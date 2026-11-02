"""Une todas las piezas: validar -> embeber -> clasificar -> novedad -> prioridad.

La app solo usa esto. Carga los artefactos una vez (Motor) y analiza listas
de secuencias, que es el caso real: una campaña de muestreo entera.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from venomscope import clasificador, novedad, prioridad
from venomscope.clasificador import Prediccion
from venomscope.embeddings import MODELO, embeber
from venomscope.grupos import nombre as nombre_grupo
from venomscope.novedad import ResultadoNovedad
from venomscope.prioridad import Prioridad
from venomscope.validacion import ResultadoValidacion, validar

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"


@dataclass
class Resultado:
    id: str
    validacion: ResultadoValidacion
    prediccion: Prediccion | None = None
    novedad: ResultadoNovedad | None = None
    prioridad: Prioridad | None = None
    vecinos: pd.DataFrame | None = None        # filas del catálogo, con su distancia
    advertencias: list[str] = field(default_factory=list)
    es_del_nea: bool | None = None
    punto3d: np.ndarray | None = None          # su lugar en el mapa, para el gráfico


class Motor:
    def __init__(self, carpeta: Path = ARTIFACTS):
        self.config = json.loads((carpeta / "config.json").read_text())
        if self.config["modelo_esm"] != MODELO:
            raise ValueError(f"Los artefactos se hicieron con {self.config['modelo_esm']}, "
                             f"pero la app usa {MODELO}. Hay que regenerarlos.")
        self.catalogo = pd.read_csv(carpeta / "catalogo_nea.csv")
        X_catalogo = np.load(carpeta / "embeddings.npy")
        if len(X_catalogo) != len(self.catalogo):
            raise ValueError("embeddings.npy no tiene una fila por secuencia del catálogo. Hay que regenerarlo.")
        self.modelo = clasificador.cargar(carpeta / "clasificador.joblib")
        cfg_nov = self.config["novedad"]
        self.detector = novedad.DetectorNovedad(X_catalogo, np.array(cfg_nov["escala"]),
                                                cfg_nov["umbrales_puntaje"])
        # El mapa 3D: se calcula una sola vez en construir_artefactos.py y se guarda,
        # para que el dibujo sea idéntico en todas las máquinas y en cada apertura.
        proyeccion = joblib.load(carpeta / "proyeccion3d.joblib")
        self.pca3d, self.coords3d = proyeccion["pca"], proyeccion["coords"]

    def analizar(self, entradas: list[tuple[str, str, bool | None]]) -> list[Resultado]:
        """entradas: lista de (id, secuencia, es_del_nea). es_del_nea puede ser None."""
        resultados = [Resultado(id=i, validacion=validar(s)) for i, s, _ in entradas]
        nea = [n for _, _, n in entradas]
        validas = [k for k, r in enumerate(resultados) if r.validacion.es_valida]
        if not validas:
            return resultados

        X = embeber([resultados[k].validacion.secuencia for k in validas])
        predicciones = clasificador.predecir(self.modelo, X, self.config["clasificador"]["umbral_confianza"])
        novedades = self.detector.analizar(X, k=self.config["novedad"]["k_vecinos"])
        puntos3d = self.pca3d.transform(X)   # su lugar en el mapa guardado

        for k, pred, nov, punto in zip(validas, predicciones, novedades, puntos3d):
            r = resultados[k]
            r.prediccion, r.novedad, r.punto3d = pred, nov, punto
            r.es_del_nea = nea[k]
            r.prioridad = prioridad.calcular(nov.nivel, nov.puntaje, pred.baja_confianza, nea[k])
            r.vecinos = self.catalogo.iloc[nov.vecinos][
                ["accession", "nombre_proteina", "especie", "grupo", "clase", "en_nea", "largo"]
            ].assign(
                distancia=nov.distancias,
                parecido=[self.detector.parecido(d) for d in nov.distancias],
            ).reset_index(drop=True)
            r.advertencias = list(r.validacion.advertencias)
            if pred.baja_confianza:
                r.advertencias.append(
                    f"El sistema no está seguro de la familia ({pred.confianza:.0%} de confianza). "
                    "Otras posibles: " + ", ".join(f"{f} ({p:.0%})" for f, p in pred.alternativas) + "."
                )
        return resultados


SIN_ANALIZAR = "No analizada"


def reevaluar(resultados: list[Resultado], umbrales: dict) -> None:
    """Recalcula nivel de novedad y prioridad con otros umbrales, en el lugar.

    El puntaje de novedad NO cambia: es una propiedad de la secuencia. Lo único que
    cambia es a partir de qué puntaje la llamamos "novedosa". Por eso mover el
    control en la app es instantáneo: no hay que volver a calcular ningún embedding.
    """
    for r in resultados:
        if r.novedad is None:
            continue
        r.novedad.nivel = novedad.nivel_para(r.novedad.puntaje, umbrales)
        r.prioridad = prioridad.calcular(r.novedad.nivel, r.novedad.puntaje,
                                         r.prediccion.baja_confianza, r.es_del_nea)


def tabla_resultados(resultados: list[Resultado]) -> pd.DataFrame:
    """Una fila por muestra, ordenada por prioridad (Alta primero) y después por novedad."""
    filas = []
    for r in resultados:
        if not r.validacion.es_valida:
            filas.append({"Muestra": r.id, "Prioridad": SIN_ANALIZAR,
                          "Avisos": " ".join(r.validacion.errores)})
            continue
        filas.append({
            "Muestra": r.id,
            "Prioridad": r.prioridad.nivel,
            "Familia probable": r.prediccion.familia,
            "Confianza": round(r.prediccion.confianza, 3),
            "Novedad (0-100)": round(r.novedad.puntaje),
            "Nivel de novedad": r.novedad.nivel,
            "Más parecida a": f"{r.vecinos.loc[0, 'nombre_proteina'].split(' (')[0]} "
                              f"({r.vecinos.loc[0, 'especie']})",
            "Grupo": nombre_grupo(r.vecinos.loc[0, "grupo"]),
            "Motivo": " ".join(r.prioridad.razones),
            "Avisos": " ".join(r.advertencias),
            "Largo": len(r.validacion.secuencia),
        })
    columnas = ["Muestra", "Prioridad", "Familia probable", "Confianza", "Novedad (0-100)",
                "Nivel de novedad", "Más parecida a", "Grupo", "Motivo", "Avisos", "Largo"]
    tabla = pd.DataFrame(filas).reindex(columns=columnas)
    orden = {**prioridad.ORDEN, SIN_ANALIZAR: len(prioridad.ORDEN)}
    return (tabla.assign(_orden=tabla["Prioridad"].map(orden))
                 .sort_values(["_orden", "Novedad (0-100)"], ascending=[True, False])
                 .drop(columns="_orden").reset_index(drop=True))
