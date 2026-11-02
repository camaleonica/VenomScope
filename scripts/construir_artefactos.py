"""Genera los artefactos que usa la app a partir de artifacts/catalogo_nea.csv.

Es el plan B mientras el Notebook 2 no exporte los suyos: produce los mismos
archivos del contrato (embeddings.npy, clasificador.joblib, config.json) y, de
paso, mide qué tan bien anda todo con las 66 secuencias reservadas.

Uso:  .venv/bin/python scripts/construir_artefactos.py
"""
import json
import sys
import time
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.dummy import DummyClassifier
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from venomscope import clasificador, novedad  # noqa: E402
from venomscope.embeddings import DIM, MODELO, embeber  # noqa: E402
from venomscope.validacion import AMINOACIDOS_VALIDOS  # noqa: E402

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
VERSION = "0.1-provisorio"


def composicion(secuencias) -> np.ndarray:
    """Línea de base sin IA: proporción de cada uno de los 20 aminoácidos."""
    letras = sorted(AMINOACIDOS_VALIDOS)
    return np.array([[s.count(a) / len(s) for a in letras] for s in secuencias])


def macro_f1_cv(modelo, X, y, cv) -> float:
    pred = cross_val_predict(modelo, X, y, cv=cv)
    return f1_score(y, pred, average="macro")


def main():
    cat = pd.read_csv(ARTIFACTS / "catalogo_nea.csv")
    modelable = cat["clase_modelable"].to_numpy()
    print(f"Catálogo: {len(cat)} secuencias ({modelable.sum()} modelables, {(~modelable).sum()} reservadas)")

    # 1. Embeddings de todo el catálogo, en el mismo orden que el CSV
    t0 = time.time()
    X = embeber(cat["sequence"].tolist(),
                progreso=lambda h, t: print(f"\r  embeddings {h}/{t}", end="", flush=True))
    print(f"\n  listo en {time.time() - t0:.0f} s -> matriz {X.shape}")
    np.save(ARTIFACTS / "embeddings.npy", X)

    # 2. Clasificador: evaluación honesta con validación cruzada, después entrenamos con todo
    Xm, ym = X[modelable], cat.loc[modelable, "clase"].to_numpy()
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    metricas = {
        "macro_f1_mayoritaria": macro_f1_cv(DummyClassifier(strategy="most_frequent"), Xm, ym, cv),
        "macro_f1_composicion": macro_f1_cv(clasificador.nuevo_modelo(),
                                            composicion(cat.loc[modelable, "sequence"]), ym, cv),
        "macro_f1_esm2": macro_f1_cv(clasificador.nuevo_modelo(), Xm, ym, cv),
    }
    print("\nClasificador (macro-F1, validación cruzada 5 partes):")
    print(f"  siempre la familia más común : {metricas['macro_f1_mayoritaria']:.3f}")
    print(f"  composición de aminoácidos   : {metricas['macro_f1_composicion']:.3f}")
    print(f"  embeddings ESM-2             : {metricas['macro_f1_esm2']:.3f}")

    modelo = clasificador.entrenar(Xm, ym)
    clasificador.guardar(modelo, ARTIFACTS / "clasificador.joblib")

    # 3. Novedad: escala calibrada con las modelables; examen con las reservadas
    escala = novedad.calibrar(Xm)
    d_reservadas = novedad.distancias_coseno(X[~modelable], Xm).min(axis=1)
    umbrales = novedad.UMBRALES_POR_DEFECTO
    p_reservadas = np.array([novedad.puntaje(d, escala) for d in d_reservadas])
    auc = roc_auc_score(np.r_[np.zeros(len(escala)), np.ones(len(d_reservadas))],
                        np.r_[escala, d_reservadas])
    metricas.update({
        "novedad_auc": auc,
        "reservadas_nivel_alto": float((p_reservadas >= umbrales["alto"]).mean()),
        "reservadas_nivel_medio_o_alto": float((p_reservadas >= umbrales["medio"]).mean()),
    })
    print("\nDetector de novedad (66 reservadas = familias que el modelo no vio):")
    print(f"  AUC (0.5 = azar, 1 = perfecto)           : {auc:.3f}")
    print(f"  reservadas marcadas 'Novedosa' (>= {umbrales['alto']})   : {metricas['reservadas_nivel_alto']:.0%}")
    print(f"  reservadas al menos 'Algo distinta' (>= {umbrales['medio']}): {metricas['reservadas_nivel_medio_o_alto']:.0%}")
    print(f"  (por construcción, ~{100 - umbrales['alto']}% de las conocidas también superan {umbrales['alto']})")

    # 4. El mapa 3D, calculado UNA sola vez y guardado.
    #    Si la app lo recalculara en cada apertura, el dibujo podría salir espejado
    #    (el signo de cada eje de PCA es arbitrario). Guardándolo, el mapa es siempre
    #    el mismo en todas las máquinas.
    pca3d = PCA(n_components=3, random_state=0).fit(X)
    coords3d = pca3d.transform(X)
    joblib.dump({"pca": pca3d, "coords": coords3d}, ARTIFACTS / "proyeccion3d.joblib")
    conservado = pca3d.explained_variance_ratio_.sum()
    print(f"\nMapa 3D: conserva el {conservado:.1%} de la información de los {DIM} números.")
    print("  (por eso el mapa es orientativo; el veredicto sale del cálculo completo)")

    # 5. Configuración que lee la app
    # Qué pasa con cada valor posible del control deslizante de la app: cuántas
    # novedades detecta. Las falsas alarmas son 100 - umbral, por cómo está armada
    # la escala. Lo guardamos para que la app lo muestre sin recalcular nada.
    curva = {str(u): round(float((p_reservadas >= u).mean()), 4) for u in range(80, 100)}

    config = {
        "version": VERSION,
        "generado_por": "scripts/construir_artefactos.py",
        "fecha": date.today().isoformat(),
        "modelo_esm": MODELO,
        "dim": DIM,
        "n_catalogo": len(cat),
        "n_reservadas": int((~modelable).sum()),
        "clasificador": {"umbral_confianza": clasificador.UMBRAL_CONFIANZA_POR_DEFECTO},
        "novedad": {
            "k_vecinos": 5,
            "umbrales_puntaje": umbrales,
            "escala": escala.round(6).tolist(),
            "curva_umbrales": curva,
        },
        "mapa3d": {"varianza_conservada": round(float(conservado), 4)},
        "metricas": {k: round(float(v), 4) for k, v in metricas.items()},
    }
    (ARTIFACTS / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False))
    print(f"\nGuardado en {ARTIFACTS}: embeddings.npy, clasificador.joblib, config.json")


if __name__ == "__main__":
    main()
