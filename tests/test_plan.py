"""El plan de laboratorio: que elija bien, que la garantía matemática se cumpla de verdad y
que el corte de "hallazgo" se calibre con los datos y no a ojo.

Son pruebas con datos inventados y chicos: no necesitan ESM-2 ni el catálogo.
"""
from itertools import combinations

import numpy as np

from venomscope import plan


def _grupos(tamanos, separacion=1.0, dispersion=0.01, dim=8, semilla=0):
    """Puntos en grupos compactos y bien separados. Devuelve (X, grupo de cada punto)."""
    rng = np.random.default_rng(semilla)
    centros = np.eye(dim)[: len(tamanos)] * separacion
    X = np.vstack([c + rng.normal(0, dispersion, (n, dim)) for c, n in zip(centros, tamanos)])
    return X + 1.0, np.repeat(np.arange(len(tamanos)), tamanos)   # +1: que no queden en el origen


def test_elige_uno_de_cada_grupo_en_vez_de_repetir():
    X, g = _grupos([6, 3, 2])
    D = plan.matriz_distancias(X)
    pesos = np.ones(len(X))
    elegidas = [e.indice for e in plan.planificar(D, pesos, 3, escala=0.05)]
    assert sorted(g[elegidas]) == [0, 1, 2]


def test_el_ranking_simple_si_repite_y_el_plan_le_gana():
    X, g = _grupos([6, 3, 2])
    D = plan.matriz_distancias(X)
    pesos = np.where(g == 0, 1.0, 0.9) + np.linspace(0, 0.05, len(X))   # el grupo 0 es apenas más novedoso
    pesos[g == 0] += 0.2
    ranking = plan.ranking_simple(pesos, 3)
    assert len(set(g[ranking])) == 1           # las tres primeras son del mismo grupo
    elegidas = [e.indice for e in plan.planificar(D, pesos, 3, escala=0.05)]
    assert plan.cobertura(D, pesos, elegidas, 0.05) > plan.cobertura(D, pesos, ranking, 0.05) + 0.2


def test_cada_cupo_extra_suma_menos_que_el_anterior():
    # Rendimientos decrecientes (submodularidad): es lo que hace válido al algoritmo goloso.
    rng = np.random.default_rng(1)
    D = plan.matriz_distancias(rng.normal(size=(25, 6)))
    ganancias = [e.ganancia for e in plan.planificar(D, rng.uniform(0.1, 1, 25), 10, escala=0.5)]
    assert all(a >= b - 1e-12 for a, b in zip(ganancias, ganancias[1:]))


def test_la_cobertura_acumulada_sube_hasta_uno():
    X, _ = _grupos([4, 4, 4])
    D = plan.matriz_distancias(X)
    elegidas = plan.planificar(D, np.ones(12), 12, escala=0.05)
    acumulada = [e.cobertura for e in elegidas]
    assert all(a <= b + 1e-12 for a, b in zip(acumulada, acumulada[1:]))
    assert acumulada[-1] <= 1.0 + 1e-9


def test_el_goloso_garantiza_al_menos_63_por_ciento_del_optimo():
    # Nemhauser-Wolsey-Fisher: 1 - 1/e = 0.632. Se comprueba contra el óptimo exacto, por
    # fuerza bruta, en muchas instancias chicas al azar.
    peor = 1.0
    for semilla in range(40):
        rng = np.random.default_rng(semilla)
        D = plan.matriz_distancias(rng.normal(size=(10, 5)))
        pesos = rng.uniform(0, 1, 10)
        goloso = plan.planificar(D, pesos, 3, escala=0.8)
        optimo = max(plan.cobertura(D, pesos, c, 0.8) for c in combinations(range(10), 3))
        peor = min(peor, goloso[-1].cobertura / optimo)
    assert peor >= 1 - 1 / np.e


def test_lo_que_pesa_cero_no_se_elige_ni_cuenta():
    X, g = _grupos([3, 3])
    D = plan.matriz_distancias(X)
    pesos = np.where(g == 0, 1.0, 0.0)
    elegidas = plan.planificar(D, pesos, 2, escala=0.05)
    assert all(g[e.indice] == 0 for e in elegidas)       # nada del grupo que no importa
    assert elegidas[0].cobertura > 0.9                   # con una sola ya queda casi todo cubierto
    assert elegidas[1].ganancia < 0.02                   # la segunda casi no suma


def test_casos_vacios_no_rompen():
    D = plan.matriz_distancias(np.ones((3, 4)))
    assert plan.planificar(D, [0, 0, 0], 2, 0.05) == []
    assert plan.planificar(D, [1, 1, 1], 0, 0.05) == []
    assert plan.planificar(np.zeros((0, 0)), [], 2, 0.05) == []
    assert plan.cobertura(D, [1, 1, 1], [], 0.05) == 0.0


def test_el_plan_es_determinista():
    rng = np.random.default_rng(5)
    D = plan.matriz_distancias(rng.normal(size=(15, 4)))
    pesos = rng.uniform(0.1, 1, 15)
    uno = [e.indice for e in plan.planificar(D, pesos, 5, 0.5)]
    dos = [e.indice for e in plan.planificar(D, pesos, 5, 0.5)]
    assert uno == dos


def test_cortar_el_plan_da_el_plan_mas_chico():
    # El de 3 cupos es el comienzo del de 5: por eso el control de la app es instantáneo.
    rng = np.random.default_rng(7)
    D = plan.matriz_distancias(rng.normal(size=(20, 4)))
    pesos = rng.uniform(0.1, 1, 20)
    cinco = [e.indice for e in plan.planificar(D, pesos, 5, 0.5)]
    tres = [e.indice for e in plan.planificar(D, pesos, 3, 0.5)]
    assert cinco[:3] == tres


def test_el_corte_calibrado_recupera_los_grupos_reales():
    X, g = _grupos([8, 8, 8, 8], separacion=1.0, dispersion=0.02)
    corte, ari = plan.calibrar_corte(X, g)
    assert ari > 0.99
    D = plan.matriz_distancias(X)
    dentro = D[np.equal.outer(g, g) & ~np.eye(len(g), dtype=bool)].max()
    fuera = D[~np.equal.outer(g, g)].min()
    assert dentro < corte < fuera or corte >= dentro      # no parte grupos y no junta grupos distintos


def test_agrupar_con_una_sola_muestra():
    Z, etiquetas = plan.agrupar(np.zeros((1, 1)), 0.05)
    assert len(Z) == 0 and list(etiquetas) == [1]


def test_agrupar_separa_lo_que_esta_lejos_y_junta_lo_que_esta_cerca():
    X, g = _grupos([4, 4])
    _, etiquetas = plan.agrupar(plan.matriz_distancias(X), 0.05)
    assert len(set(etiquetas)) == 2
    assert all(len(set(etiquetas[g == k])) == 1 for k in (0, 1))


def test_armar_junta_todo_lo_que_la_pantalla_y_el_informe_necesitan():
    X, g = _grupos([6, 3, 2])
    puntajes = np.full(len(X), 95.0)
    a = plan.armar(X, puntajes, corte=0.05, cupos_max=5)
    assert a.hallazgos == 3
    assert sorted(g[a.orden[:3]]) == [0, 1, 2]
    assert len(a.curva_plan) == len(a.curva_ranking) == len(a.elegidas)
    assert all(p >= r - 1e-9 for p, r in zip(a.curva_plan, a.curva_ranking))      # el plan nunca pierde contra el ranking
    assert a.cupos_suficientes(0.95) == 3                                           # con uno de cada grupo alcanza
    i = a.orden[0]
    assert a.equivale_a(i) == (g == g[i]).sum() - 1


def test_armar_sin_nada_que_planificar_no_rompe():
    a = plan.armar(np.ones((3, 4)), [0, 0, 0], corte=0.05, cupos_max=3)
    assert a.elegidas == [] and a.curva_plan == [] and a.cupos_suficientes() is None
