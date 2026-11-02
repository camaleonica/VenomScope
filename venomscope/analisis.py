"""Une todas las piezas: validar -> embeber -> clasificar -> novedad -> prioridad.

La app solo usa esto. Carga los artefactos una vez (Motor) y analiza listas
de secuencias, que es el caso real: una campaña de muestreo entera.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from venomscope import clasificador, novedad, prioridad
from venomscope.clasificador import Prediccion
from venomscope.embeddings import MODELO, embeber
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

        for k, pred, nov in zip(validas, predicciones, novedades):
            r = resultados[k]
            r.prediccion, r.novedad = pred, nov
            r.prioridad = prioridad.calcular(nov.nivel, nov.puntaje, pred.baja_confianza, nea[k])
            r.vecinos = self.catalogo.iloc[nov.vecinos][
                ["accession", "nombre_proteina", "especie", "clase", "en_nea", "largo"]
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
            "Motivo": " ".join(r.prioridad.razones),
            "Avisos": " ".join(r.advertencias),
            "Largo": len(r.validacion.secuencia),
        })
    columnas = ["Muestra", "Prioridad", "Familia probable", "Confianza", "Novedad (0-100)",
                "Nivel de novedad", "Más parecida a", "Motivo", "Avisos", "Largo"]
    tabla = pd.DataFrame(filas).reindex(columns=columnas)
    orden = {**prioridad.ORDEN, SIN_ANALIZAR: len(prioridad.ORDEN)}
    return (tabla.assign(_orden=tabla["Prioridad"].map(orden))
                 .sort_values(["_orden", "Novedad (0-100)"], ascending=[True, False])
                 .drop(columns="_orden").reset_index(drop=True))
