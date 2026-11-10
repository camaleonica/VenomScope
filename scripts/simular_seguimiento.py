"""¿El seguimiento hace lo que dice? Se mide con los datos reales del catálogo.

Para cada familia con suficientes miembros:
  1. Se la saca de la referencia: para el sistema es una familia desconocida, y todos sus
     miembros se ven como novedad.
  2. El laboratorio "confirma" una muestra de esa familia (o dos), que pasa a la referencia.
  3. Se mide qué pasa con las demás: ¿siguen marcadas como novedosas?

Si funciona, confirmar una muestra tiene que hacer bajar a sus parientes, y no a las demás
familias. Esa segunda parte importa tanto como la primera: un seguimiento que bajara todo
sería peor que no tenerlo. Por eso se mide también el efecto sobre una segunda familia
desconocida y sin relación (el control), que no debería moverse.

Uso:  .venv/bin/python scripts/simular_seguimiento.py
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from venomscope import novedad  # noqa: E402
from venomscope.analisis import ARTIFACTS  # noqa: E402

MIN_MIEMBROS = 8
SORTEOS = 30


def puntajes(detector, X):
    return np.array([r.puntaje for r in detector.analizar(X)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=str(RAIZ / "resultados" / "seguimiento_simulacion.json"))
    args = ap.parse_args()

    cat = pd.read_csv(ARTIFACTS / "catalogo_nea.csv")
    X = np.load(ARTIFACTS / "embeddings.npy")
    ok = cat["clase_modelable"].to_numpy()
    familias = np.where(ok, cat["clase"].to_numpy(), "")
    grandes = [f for f in sorted(set(familias[ok])) if (familias == f).sum() >= MIN_MIEMBROS]
    rng = np.random.default_rng(0)

    filas = []
    for f in grandes:
        miembros = np.flatnonzero(familias == f)
        # Control: una segunda familia, sin relación, que TAMBIÉN es desconocida para el sistema.
        # Si estuviera en la referencia no sería novedad ni antes ni después y no probaría nada.
        otra = rng.choice([g for g in grandes if g != f])
        control = np.flatnonzero(familias == otra)
        ref = np.flatnonzero(ok & (familias != f) & (familias != otra))
        escala = novedad.calibrar(X[ref])
        det0 = novedad.DetectorNovedad(X[ref], escala)
        alto = det0.umbrales["alto"]
        fila = {"familia": f, "miembros": int(len(miembros)),
                "novedosas_antes": float((puntajes(det0, X[miembros]) >= alto).mean()),
                "mediana_antes": float(np.median(puntajes(det0, X[miembros]))),
                "control_novedosas_antes": float((puntajes(det0, X[control]) >= alto).mean())}
        for k in (1, 2):
            despues, mediana, ctrl = [], [], []
            for _ in range(SORTEOS):
                elegidas = rng.choice(miembros, k, replace=False)
                resto = np.setdiff1d(miembros, elegidas)
                det1 = novedad.DetectorNovedad(np.vstack([X[ref], X[elegidas]]), escala)   # la escala NO cambia
                p = puntajes(det1, X[resto])
                despues.append((p >= alto).mean())
                mediana.append(np.median(p))
                ctrl.append((puntajes(det1, X[control]) >= alto).mean())
            fila[f"novedosas_despues_{k}"] = float(np.mean(despues))
            fila[f"mediana_despues_{k}"] = float(np.mean(mediana))
            fila[f"control_novedosas_despues_{k}"] = float(np.mean(ctrl))
        filas.append(fila)

    df = pd.DataFrame(filas)
    resumen = {
        "familias": len(df), "sorteos_por_familia": SORTEOS,
        "pariente_novedosas_antes": df.novedosas_antes.mean(),
        "pariente_novedosas_tras_1": df.novedosas_despues_1.mean(),
        "pariente_novedosas_tras_2": df.novedosas_despues_2.mean(),
        "pariente_mediana_antes": df.mediana_antes.mean(),
        "pariente_mediana_tras_1": df.mediana_despues_1.mean(),
        "pariente_mediana_tras_2": df.mediana_despues_2.mean(),
        "control_novedosas_antes": df.control_novedosas_antes.mean(),
        "control_novedosas_tras_1": df.control_novedosas_despues_1.mean(),
        "familias_donde_baja": int((df.novedosas_despues_1 < df.novedosas_antes - 0.05).sum()),
    }
    resumen = {k: (round(float(v), 3) if isinstance(v, float) or hasattr(v, "dtype") else v) for k, v in resumen.items()}
    print(f"{len(df)} familias con {MIN_MIEMBROS}+ miembros\n")
    print("Parientes de lo confirmado marcados como NOVEDOSOS:")
    print(f"  antes de confirmar nada : {resumen['pariente_novedosas_antes']:.0%}   (mediana del puntaje {resumen['pariente_mediana_antes']:.0f})")
    print(f"  tras confirmar 1 muestra: {resumen['pariente_novedosas_tras_1']:.0%}   (mediana {resumen['pariente_mediana_tras_1']:.0f})")
    print(f"  tras confirmar 2        : {resumen['pariente_novedosas_tras_2']:.0%}   (mediana {resumen['pariente_mediana_tras_2']:.0f})")
    print("Control, otra familia desconocida y SIN relación con lo confirmado:")
    print(f"  antes {resumen['control_novedosas_antes']:.0%}  ->  después {resumen['control_novedosas_tras_1']:.0%}")
    print(f"Familias donde confirmar una baja la novedad de las demás (más de 5 puntos): {resumen['familias_donde_baja']} de {len(df)}")
    print("\nLas que menos bajan (confirmar una no alcanza):")
    peor = df.assign(baja=df.novedosas_antes - df.novedosas_despues_1).sort_values("baja").head(4)
    for _, r in peor.iterrows():
        print(f"  {r.familia[:50]:<50} {r.novedosas_antes:.0%} -> {r.novedosas_despues_1:.0%}")

    Path(args.salida).parent.mkdir(exist_ok=True)
    Path(args.salida).write_text(json.dumps({"resumen": resumen, "por_familia": filas}, indent=2, ensure_ascii=False))
    print("\nGuardado en", args.salida)


if __name__ == "__main__":
    main()
