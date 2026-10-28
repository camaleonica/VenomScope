"""Predicción de la familia proteica a partir del embedding.

Regresión logística: simple, rápida en CPU y devuelve probabilidades, que usamos
como "confianza". class_weight="balanced" hace que las familias chicas pesen
lo mismo que las grandes (hay un desbalance de ~15x en el catálogo).
"""
from dataclasses import dataclass

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

UMBRAL_CONFIANZA_POR_DEFECTO = 0.5   # por debajo, se avisa "confianza baja"


def nuevo_modelo():
    # StandardScaler: pone los 480 números en la misma escala antes de clasificar
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=5000, class_weight="balanced"),
    )


def entrenar(X: np.ndarray, y) -> object:
    modelo = nuevo_modelo()
    modelo.fit(X, y)
    return modelo


def guardar(modelo, ruta) -> None:
    joblib.dump(modelo, ruta)


def cargar(ruta):
    return joblib.load(ruta)


@dataclass
class Prediccion:
    familia: str
    confianza: float                      # probabilidad de la familia elegida (0-1)
    alternativas: list[tuple[str, float]] # las siguientes más probables
    baja_confianza: bool


def predecir(modelo, X: np.ndarray, umbral=UMBRAL_CONFIANZA_POR_DEFECTO, n_alternativas=2) -> list[Prediccion]:
    probas = modelo.predict_proba(X)
    clases = modelo.classes_
    predicciones = []
    for fila in probas:
        orden = np.argsort(fila)[::-1]
        predicciones.append(Prediccion(
            familia=str(clases[orden[0]]),
            confianza=float(fila[orden[0]]),
            alternativas=[(str(clases[i]), float(fila[i])) for i in orden[1:1 + n_alternativas]],
            baja_confianza=bool(fila[orden[0]] < umbral),
        ))
    return predicciones
