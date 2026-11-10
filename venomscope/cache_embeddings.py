"""Caché de embeddings en disco: una secuencia que ya se calculó no se vuelve a calcular.

Por qué. Calcular el embedding con ESM-2 es lo único lento del sistema (segundos por lote en
una notebook sin placa de video). Todo lo demás es instantáneo. Con la caché, volver a
analizar una campaña, mover un control o confirmar una muestra en el seguimiento no espera
al modelo, y la demo abre rápido aunque el modelo todavía no esté cargado.

Cómo. Envuelve a `embeber` desde afuera y NO lo modifica: la lógica de `embeddings.py` tiene
que ser idéntica a la del notebook. La caché guarda tal cual los números que `embeber`
devolvió, de modo que un acierto devuelve exactamente lo mismo que habría calculado.

La clave de cada secuencia incluye el modelo y `VERSION`. Si alguna vez cambia la lógica de
`embeber` (y por lo tanto hay que replicarla en el notebook), se sube `VERSION` y las
entradas viejas dejan de usarse solas, sin riesgo de mezclar números de dos lógicas.

Una entrada por archivo `.npy`, escrita en un archivo temporal y renombrada: si se corta la
luz a la mitad, queda un archivo completo o ninguno. Una entrada rota o con la forma
equivocada se ignora y se recalcula.

Nada de este módulo conoce Streamlit.
"""
import hashlib
import os
import tempfile
from pathlib import Path

import numpy as np

from venomscope.embeddings import DIM, MODELO
from venomscope.validacion import normalizar

VERSION = 1
CARPETA = Path(os.environ.get("VENOMSCOPE_CACHE")
               or Path(__file__).resolve().parents[1] / "cache" / "embeddings")


def _ruta(carpeta: Path, secuencia: str) -> Path:
    clave = hashlib.sha256(f"{MODELO}|v{VERSION}|{secuencia}".encode()).hexdigest()
    return carpeta / f"{clave}.npy"


def _leer(ruta: Path) -> np.ndarray | None:
    """El vector guardado, o None si no está o no sirve."""
    try:
        v = np.load(ruta, allow_pickle=False)
    except (OSError, ValueError):
        return None
    if v.shape != (DIM,) or v.dtype != np.float32 or not np.isfinite(v).all():
        return None
    return v


def _guardar(ruta: Path, vector: np.ndarray) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=ruta.parent, suffix=".tmp", delete=False) as f:
        np.save(f, vector.astype(np.float32), allow_pickle=False)
    os.replace(f.name, ruta)


def embeber_con_cache(secuencias: list[str], embeber_fn, carpeta: Path | None = None, **kwargs) -> np.ndarray:
    """Igual que `embeber`: una matriz (n_secuencias x 480), pero solo calcula lo que falta.

    `embeber_fn` es la función que calcula de verdad (se pasa de afuera para poder probar la
    caché sin cargar el modelo). Las secuencias repetidas se calculan una sola vez.
    """
    carpeta = Path(carpeta) if carpeta else CARPETA
    normalizadas = [normalizar(s) for s in secuencias]
    if not normalizadas:
        return np.zeros((0, DIM), dtype=np.float32)

    vectores: dict[str, np.ndarray] = {}
    for s in dict.fromkeys(normalizadas):                 # únicas, en orden
        v = _leer(_ruta(carpeta, s))
        if v is not None:
            vectores[s] = v
    faltan = [s for s in dict.fromkeys(normalizadas) if s not in vectores]
    if faltan:
        nuevos = embeber_fn(faltan, **kwargs)
        for s, v in zip(faltan, nuevos):
            vectores[s] = np.asarray(v, dtype=np.float32)
            _guardar(_ruta(carpeta, s), vectores[s])
    return np.vstack([vectores[s] for s in normalizadas])


def tamano(carpeta: Path | None = None) -> int:
    """Cuántas secuencias hay guardadas."""
    carpeta = Path(carpeta) if carpeta else CARPETA
    return len(list(carpeta.glob("*.npy"))) if carpeta.exists() else 0
