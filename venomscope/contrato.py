"""Qué tiene que haber en artifacts/ para que la app arranque.

Esto es el contrato entre el Notebook 2 y la app. Está acá, en un solo lugar,
porque los artefactos se pueden generar de dos maneras (el notebook en Colab o
scripts/construir_artefactos.py acá) y las dos tienen que producir lo mismo.

Si alguien agrega algo que la app lee de config.json, va en esta lista. Así el
test falla enseguida en vez de reventar en la demo.
"""
import json
from pathlib import Path

ARCHIVOS = {
    "catalogo_nea.csv":     "el catálogo (sale del Notebook 1)",
    "embeddings.npy":       "los números de cada secuencia, en el mismo orden que el CSV",
    "clasificador.joblib":  "el clasificador entrenado",
    "proyeccion3d.joblib":  "el mapa 3D ya calculado",
    "config.json":          "umbrales, escala de novedad y métricas",
}

# Claves de config.json que la app lee. El punto separa niveles.
CLAVES = [
    "modelo_esm",
    "dim",
    "n_catalogo",
    "n_reservadas",
    "clasificador.umbral_confianza",
    "novedad.k_vecinos",
    "novedad.umbrales_puntaje",
    "novedad.escala",
    "novedad.curva_umbrales",
    "mapa3d.varianza_conservada",
    "metricas.macro_f1_esm2",
    "metricas.macro_f1_composicion",
    "metricas.macro_f1_esm2_agrupado",
    "metricas.reservadas_nivel_medio_o_alto",
]


def _buscar(config: dict, clave: str):
    actual = config
    for parte in clave.split("."):
        if not isinstance(actual, dict) or parte not in actual:
            return None
        actual = actual[parte]
    return actual


def problemas(carpeta: Path) -> list[str]:
    """Lista vacía si la carpeta sirve; si no, qué le falta, en castellano."""
    fallas = [f"Falta {nombre} ({para_que})."
              for nombre, para_que in ARCHIVOS.items()
              if not (carpeta / nombre).exists()]
    if any("config.json" in f for f in fallas):
        return fallas

    try:
        config = json.loads((carpeta / "config.json").read_text())
    except json.JSONDecodeError as e:
        return fallas + [f"config.json está roto: {e}"]

    faltantes = [c for c in CLAVES if _buscar(config, c) is None]
    if faltantes:
        fallas.append("A config.json le faltan estas claves: " + ", ".join(faltantes) + ".")
    return fallas


def verificar(carpeta: Path) -> None:
    """Revienta con un mensaje que dice qué hacer, en vez de un error críptico."""
    fallas = problemas(carpeta)
    if fallas:
        raise FileNotFoundError(
            "Los archivos del modelo están incompletos o son de una versión vieja:\n  - "
            + "\n  - ".join(fallas)
            + "\n\nRegeneralos con:  .venv/bin/python scripts/construir_artefactos.py"
        )
