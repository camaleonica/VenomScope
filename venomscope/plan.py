"""Plan de laboratorio: de "ordenar las muestras" a "elegir cuáles mandar".

El problema. Una campaña trae muchas secuencias, pero el laboratorio solo puede estudiar
unas pocas. Ordenarlas por novedad (lo que hace `tabla_resultados`) tiene un defecto:
si diez muestras son variantes casi idénticas de una misma proteína rara, las diez quedan
arriba y las diez cuentan como un solo hallazgo. Con cinco cupos se gastan cinco en lo mismo.

La solución. Elegir un conjunto de muestras que *represente* a todas las importantes. Es el
problema de ubicación de instalaciones (facility location): cada muestra elegida "cubre" a
las que se le parecen, y se maximiza la cobertura ponderada por importancia:

    F(S) = suma sobre j de  peso_j * max sobre i en S de similitud(i, j)

F es monótona y submodular (agregar una muestra ayuda menos cuanto más ya se eligió), así que
el algoritmo goloso, que agrega de a una la que más suma, garantiza al menos el 63% del óptimo
(1 - 1/e, Nemhauser, Wolsey y Fisher, 1978). No hace falta resolver el problema exacto.

Dos números salen de los datos y no se eligen a ojo:
- el corte que define "qué es un hallazgo distinto", que se calibra contra las familias reales
  del catálogo (`calibrar_corte`);
- la escala de la similitud, que es ese mismo corte.

Nada de este módulo conoce Streamlit.
"""
from dataclasses import dataclass

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.metrics import adjusted_rand_score

from venomscope.novedad import distancias_coseno

# Cuánto pesa la novedad al elegir (peso = (puntaje/100) ** PESO_EXPONENTE). Se eligió con
# `scripts/simular_plan.py` en campañas de ajuste, distintas de las de evaluación.
PESO_EXPONENTE = 8
CORTES_A_PROBAR = np.round(np.arange(0.01, 0.16, 0.005), 3)


def matriz_distancias(X: np.ndarray) -> np.ndarray:
    """Distancia coseno entre todas las muestras, simétrica y con ceros en la diagonal."""
    D = distancias_coseno(X, X)
    D = (D + D.T) / 2
    np.fill_diagonal(D, 0.0)
    return D


def agrupar(D: np.ndarray, corte: float) -> tuple[np.ndarray, np.ndarray]:
    """Agrupamiento jerárquico de enlace promedio.

    Devuelve (linkage, etiquetas). Las etiquetas juntan las muestras que están a menos de
    `corte` unas de otras, en promedio. Con una sola muestra no hay nada que agrupar.
    """
    n = len(D)
    if n < 2:
        return np.zeros((0, 4)), np.ones(n, dtype=int)
    Z = linkage(squareform(D, checks=False), method="average")
    return Z, fcluster(Z, corte, criterion="distance")


def calibrar_corte(X: np.ndarray, familias, cortes=CORTES_A_PROBAR) -> tuple[float, float]:
    """El corte que mejor recupera las familias reales del catálogo.

    Agrupa el catálogo con cada corte candidato y mide cuánto se parecen los grupos a las
    familias con el índice de Rand ajustado (1 = idénticos, 0 = como tirar a la suerte).
    Devuelve (corte, ari). En el catálogo del NEA da 0.025, con un ARI de 0.68.
    """
    D = matriz_distancias(X)
    Z, _ = agrupar(D, cortes[0])
    familias = np.asarray(familias)
    mejor = (float(cortes[0]), -1.0)
    for corte in cortes:
        etiquetas = fcluster(Z, corte, criterion="distance")
        ari = adjusted_rand_score(familias, etiquetas)
        if ari > mejor[1]:
            mejor = (float(corte), float(ari))
    return mejor


@dataclass
class Eleccion:
    indice: int                 # posición de la muestra elegida
    ganancia: float             # cobertura nueva que aporta, sobre el total (0-1)
    cobertura: float            # cobertura acumulada con esta y las anteriores (0-1)


def similitud(D: np.ndarray, escala: float) -> np.ndarray:
    """1 si son iguales, decae hacia 0 al alejarse. A `escala` de distancia vale 0.37."""
    return np.exp(-D / escala)


def planificar(D: np.ndarray, pesos, cupos: int, escala: float) -> list[Eleccion]:
    """Elige hasta `cupos` muestras que cubran lo más importante (algoritmo goloso).

    `pesos`: importancia de cada muestra (por ejemplo, su novedad). Las de peso 0 no cuentan.
    El resultado viene en orden: la primera es la mejor sola, la segunda la que más suma a la
    primera, y así. Cortar la lista en cualquier punto da el mejor plan para ese presupuesto
    (hasta la garantía del goloso), así que sirve para todos los valores del control.
    """
    pesos = np.clip(np.asarray(pesos, dtype=float), 0.0, None)
    total = pesos.sum()
    n = len(pesos)
    if n == 0 or total <= 0 or cupos <= 0:
        return []

    S = similitud(D, escala)
    cubierto = np.zeros(n)          # mejor similitud de cada muestra con lo ya elegido
    elegidas: list[int] = []
    plan: list[Eleccion] = []
    for _ in range(min(cupos, n)):
        # Fila i: cuánto sumaría elegir i. Solo cuenta lo que mejora lo ya cubierto.
        ganancias = (np.maximum(S - cubierto[None, :], 0.0) * pesos[None, :]).sum(axis=1)
        ganancias[elegidas] = -1.0
        i = int(np.argmax(ganancias))
        if ganancias[i] <= 1e-12:
            break                    # todo lo importante ya está cubierto
        cubierto = np.maximum(cubierto, S[i])
        elegidas.append(i)
        plan.append(Eleccion(i, float(ganancias[i] / total), float((pesos * cubierto).sum() / total)))
    return plan


def ranking_simple(pesos, cupos: int) -> list[int]:
    """La alternativa de siempre: las `cupos` de más peso, sin mirar si se repiten."""
    return [int(i) for i in np.argsort(-np.asarray(pesos, dtype=float), kind="stable")[:cupos]]


def cobertura(D: np.ndarray, pesos, indices, escala: float) -> float:
    """Qué parte de lo importante queda cubierta por estas muestras (0-1), con la misma
    vara para cualquier selección. Sirve para comparar el plan contra el ranking simple."""
    pesos = np.clip(np.asarray(pesos, dtype=float), 0.0, None)
    if len(indices) == 0 or pesos.sum() <= 0:
        return 0.0
    mejor = similitud(D[list(indices)], escala).max(axis=0)
    return float((pesos * mejor).sum() / pesos.sum())


def curva_cobertura(D: np.ndarray, pesos, orden, escala: float) -> list[float]:
    """Cobertura con 1, 2, 3... muestras tomadas en este orden."""
    return [cobertura(D, pesos, orden[:k], escala) for k in range(1, len(orden) + 1)]


@dataclass
class PlanArmado:
    """Todo lo que hace falta para mostrar un plan, calculado una sola vez.

    La pantalla y el informe descargable usan exactamente estos números, así no pueden
    contradecirse."""
    D: np.ndarray                # distancias entre las muestras
    pesos: np.ndarray            # importancia de cada una
    Z: np.ndarray                # árbol de parentesco (matriz de enlace de scipy)
    etiquetas: np.ndarray        # hallazgo al que pertenece cada muestra
    corte: float
    elegidas: list[Eleccion]     # el plan, en orden
    orden: list[int]             # posiciones de las elegidas, en orden
    curva_plan: list[float]      # cobertura con 1, 2, 3... cupos siguiendo el plan
    curva_ranking: list[float]   # lo mismo ordenando por novedad

    @property
    def hallazgos(self) -> int:
        return len(set(self.etiquetas))

    def equivale_a(self, indice: int) -> int:
        """Cuántas otras muestras son el mismo hallazgo que ésta."""
        return int((self.etiquetas == self.etiquetas[indice]).sum()) - 1

    def cupos_suficientes(self, cobertura_minima: float = 0.95) -> int | None:
        """Con cuántos cupos ya se cubre casi todo; seguir gastando casi no rinde."""
        return next((k for k, v in enumerate(self.curva_plan, start=1) if v >= cobertura_minima), None)


def armar(X: np.ndarray, puntajes, corte: float, cupos_max: int) -> PlanArmado:
    """El plan completo de una campaña: X son los embeddings y `puntajes` la novedad (0-100)."""
    D = matriz_distancias(X)
    pesos = (np.asarray(puntajes, dtype=float) / 100.0) ** PESO_EXPONENTE
    Z, etiquetas = agrupar(D, corte)
    elegidas = planificar(D, pesos, cupos_max, corte)
    orden = [e.indice for e in elegidas]
    ranking = ranking_simple(pesos, len(elegidas))
    return PlanArmado(D, pesos, Z, etiquetas, corte, elegidas, orden,
                      curva_cobertura(D, pesos, orden, corte), curva_cobertura(D, pesos, ranking, corte))
