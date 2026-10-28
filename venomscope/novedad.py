"""Qué tan novedosa es una secuencia respecto del catálogo, y sus vecinos más parecidos.

Idea: en el espacio de embeddings, "parecerse" es "estar cerca". Medimos la
distancia (coseno) a la secuencia más cercana del catálogo y la traducimos a un
puntaje 0-100 comparándola con una escala de referencia: las distancias que
tienen las secuencias conocidas a su pariente más cercano.

Puntaje 97 = "está más lejos de lo conocido que el 97% de las toxinas del
catálogo respecto de su pariente más cercano".
"""
from dataclasses import dataclass

import numpy as np

# Cortes del puntaje para el nivel que se muestra. Editables en config.json.
UMBRALES_POR_DEFECTO = {"medio": 75, "alto": 95}

NIVEL_CONOCIDA = "Parecida a algo conocido"
NIVEL_MEDIA = "Algo distinta"
NIVEL_NOVEDOSA = "Novedosa"


def _a_unitarios(X: np.ndarray) -> np.ndarray:
    normas = np.linalg.norm(X, axis=1, keepdims=True)
    return X / np.clip(normas, 1e-12, None)


def distancias_coseno(Q: np.ndarray, R: np.ndarray) -> np.ndarray:
    """Matriz (len(Q) x len(R)): 0 = misma dirección, cuanto más grande más distinta."""
    # clip: el redondeo puede dar -0.000001 cuando son idénticas
    return np.clip(1.0 - _a_unitarios(Q) @ _a_unitarios(R).T, 0.0, None)


def calibrar(X_referencia: np.ndarray) -> np.ndarray:
    """Distancia de cada secuencia a su vecina más cercana (sin contarse a sí misma).

    Devuelve las distancias ordenadas: es la escala con la que se mide la novedad.
    """
    D = distancias_coseno(X_referencia, X_referencia)
    np.fill_diagonal(D, np.inf)
    return np.sort(D.min(axis=1))


def puntaje(distancia_min: float, escala: np.ndarray) -> float:
    """Porcentaje de la escala que queda por debajo de esta distancia (0-100)."""
    return 100.0 * np.searchsorted(escala, distancia_min, side="left") / len(escala)


@dataclass
class ResultadoNovedad:
    distancia_min: float
    puntaje: float
    nivel: str
    vecinos: list[int]          # índices en el catálogo, del más parecido al menos
    distancias: list[float]


class DetectorNovedad:
    def __init__(self, X_catalogo: np.ndarray, escala: np.ndarray, umbrales: dict | None = None):
        self.X_catalogo = X_catalogo
        self.escala = np.sort(np.asarray(escala))
        self.umbrales = umbrales or UMBRALES_POR_DEFECTO

    def nivel(self, p: float) -> str:
        if p >= self.umbrales["alto"]:
            return NIVEL_NOVEDOSA
        if p >= self.umbrales["medio"]:
            return NIVEL_MEDIA
        return NIVEL_CONOCIDA

    def analizar(self, X: np.ndarray, k: int = 5) -> list[ResultadoNovedad]:
        D = distancias_coseno(X, self.X_catalogo)
        resultados = []
        for fila in D:
            orden = np.argsort(fila)[:k]
            d_min = float(fila[orden[0]])
            p = puntaje(d_min, self.escala)
            resultados.append(ResultadoNovedad(
                distancia_min=d_min,
                puntaje=p,
                nivel=self.nivel(p),
                vecinos=orden.tolist(),
                distancias=fila[orden].tolist(),
            ))
        return resultados
