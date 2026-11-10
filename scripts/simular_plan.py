"""¿El plan de laboratorio sirve de verdad? Se mide, no se afirma.

Simula campañas con los datos reales del catálogo y cuenta cuántas FAMILIAS NUEVAS descubre
cada estrategia con el mismo número de cupos. Una familia "nueva" es una que el sistema no
vio: se la saca del catálogo de referencia, igual que pasaría con una familia desconocida.

Cada campaña simulada:
  1. Se eligen 4 familias "nuevas" y 4 "conocidas" al azar.
  2. Se arma una campaña de 40 muestras con miembros de esas 8 familias (al menos 2 de cada
     nueva). Las familias grandes aportan muchas muestras casi iguales: justo la redundancia
     que el plan debería evitar.
  3. La referencia es el catálogo SIN las familias nuevas y SIN las muestras de la campaña.
  4. Con esa referencia se calibra todo (escala de novedad y corte del plan), igual que en la app.

Estrategias, con K cupos:
  ranking   las K de mayor novedad (lo que hace la tabla hoy)
  diverso   entre las novedosas, las K más alejadas entre sí (k-center goloso): una alternativa razonable
  plan      el plan de laboratorio (cobertura ponderada, goloso)
  azar      K al azar, como piso

Se calibra el peso con las semillas de ajuste y se evalúa en otras semillas distintas, para
no medir sobre lo mismo con lo que se eligió.

Uso:  .venv/bin/python scripts/simular_plan.py
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from venomscope import novedad, plan  # noqa: E402
from venomscope.analisis import ARTIFACTS  # noqa: E402

CUPOS = list(range(1, 9))
ESTRATEGIAS = ["ranking", "diverso", "plan", "azar"]


def armar_campana(rng, familias: np.ndarray, validas: np.ndarray, n=40, n_nuevas=4, n_conocidas=4):
    elegibles = [f for f in validas if (familias == f).sum() >= 6]
    nuevas = list(rng.choice(elegibles, n_nuevas, replace=False))
    conocidas = list(rng.choice([f for f in elegibles if f not in nuevas], n_conocidas, replace=False))
    campana = []
    for f in nuevas:                                   # garantiza algo que descubrir
        campana += list(rng.choice(np.flatnonzero(familias == f), 2, replace=False))
    pool = np.flatnonzero(np.isin(familias, nuevas + conocidas))
    pool = np.setdiff1d(pool, campana)
    campana += list(rng.choice(pool, n - len(campana), replace=False))
    return np.array(campana), nuevas


def elegir_diverso(D, puntajes, cupos, corte_alto):
    """Entre las novedosas, empieza por la más novedosa y va sumando la más alejada de lo elegido."""
    candidatas = [i for i in np.argsort(-puntajes) if puntajes[i] >= corte_alto] or list(np.argsort(-puntajes))
    elegidas = [candidatas[0]]
    while len(elegidas) < min(cupos, len(candidatas)):
        resto = [i for i in candidatas if i not in elegidas]
        elegidas.append(max(resto, key=lambda i: D[i, elegidas].min()))
    relleno = [i for i in np.argsort(-puntajes) if i not in elegidas]
    return (elegidas + relleno)[:cupos]


def una_simulacion(X, familias, validas, semilla, peso, n=40):
    rng = np.random.default_rng(semilla)
    campana, nuevas = armar_campana(rng, familias, validas, n=n)
    ref = np.flatnonzero(~np.isin(familias, nuevas))
    ref = np.setdiff1d(ref, campana)
    ref = ref[np.isin(familias[ref], validas)]
    escala_nov = novedad.calibrar(X[ref])
    detector = novedad.DetectorNovedad(X[ref], escala_nov)
    puntajes = np.array([r.puntaje for r in detector.analizar(X[campana])])
    corte, _ = plan.calibrar_corte(X[ref], familias[ref])
    D = plan.matriz_distancias(X[campana])
    pesos = (puntajes / 100.0) ** peso
    elegido = plan.planificar(D, pesos, max(CUPOS), corte)
    orden_plan = [e.indice for e in elegido]

    fam_c = familias[campana]
    descubiertas = {e: [] for e in ESTRATEGIAS}
    for k in CUPOS:
        listas = {
            "ranking": plan.ranking_simple(puntajes, k),
            "diverso": elegir_diverso(D, puntajes, k, detector.umbrales["alto"]),
            "plan": orden_plan[:k],
            "azar": list(rng.choice(len(campana), k, replace=False)),
        }
        for e, idx in listas.items():
            descubiertas[e].append(len(set(fam_c[idx]) & set(nuevas)))
    return descubiertas


def correr(X, familias, validas, semillas, peso):
    filas = [una_simulacion(X, familias, validas, s, peso) for s in semillas]
    return {e: np.array([f[e] for f in filas]) for e in ESTRATEGIAS}   # (campañas, cupos)


def ic_bootstrap(diferencias, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    medias = [rng.choice(diferencias, len(diferencias)).mean() for _ in range(n)]
    return float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campanas", type=int, default=300)
    ap.add_argument("--ajuste", type=int, default=60, help="campañas para elegir el exponente del peso")
    ap.add_argument("--salida", default=str(RAIZ / "resultados" / "plan_simulacion.json"))
    args = ap.parse_args()

    cat = pd.read_csv(ARTIFACTS / "catalogo_nea.csv")
    X = np.load(ARTIFACTS / "embeddings.npy")
    ok = cat["clase_modelable"].to_numpy()
    familias = np.where(ok, cat["clase"].to_numpy(), "").astype(object)
    validas = np.array(sorted(set(familias[ok])))

    print("Ajuste del peso (semillas 0..%d), familias nuevas descubiertas con 3 y 5 cupos:" % (args.ajuste - 1))
    mejor = None
    for peso in (1, 2, 4, 8):
        r = correr(X, familias, validas, range(args.ajuste), peso)["plan"].mean(axis=0)
        print(f"  peso = (novedad/100)^{peso}:  K=3 -> {r[2]:.2f}   K=5 -> {r[4]:.2f}")
        if mejor is None or r[2] + r[4] > mejor[1]:
            mejor = (peso, r[2] + r[4])
    peso = mejor[0]
    print(f"Se usa el exponente {peso}. Evaluación en {args.campanas} campañas distintas (semillas 1000+):\n")

    r = correr(X, familias, validas, range(1000, 1000 + args.campanas), peso)
    print("Familias nuevas descubiertas (de 4 posibles), promedio:")
    print("cupos " + "".join(f"{k:>8}" for k in CUPOS))
    for e in ESTRATEGIAS:
        print(f"{e:<8}" + "".join(f"{v:8.2f}" for v in r[e].mean(axis=0)))
    print("\nDiferencia plan - ranking (IC 95% por bootstrap):")
    resumen = {}
    for e in ("ranking", "diverso", "azar"):
        print(f"  plan - {e}:")
        for k in (2, 3, 4, 5):
            d = r["plan"][:, k - 1] - r[e][:, k - 1]
            lo, hi = ic_bootstrap(d)
            print(f"    K={k}: {d.mean():+.2f}  [{lo:+.2f}, {hi:+.2f}]")
            resumen[f"plan-{e}@{k}"] = {"media": float(d.mean()), "ic95": [lo, hi]}

    Path(args.salida).parent.mkdir(exist_ok=True)
    Path(args.salida).write_text(json.dumps({
        "campanas": args.campanas, "peso_exponente": peso, "cupos": CUPOS,
        "promedios": {e: r[e].mean(axis=0).round(3).tolist() for e in ESTRATEGIAS},
        "diferencias": resumen}, indent=2))
    print("\nGuardado en", args.salida)


if __name__ == "__main__":
    main()
