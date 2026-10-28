"""Secuencia -> vector de 480 números con ESM-2.

REGLA CRÍTICA: esta lógica tiene que ser idéntica a la del Notebook 2
(mismo modelo, mismo promedio con máscara, misma normalización). Si difiere,
el clasificador y el detector de novedad reciben números distintos a los que
vieron al entrenarse y se equivocan sin dar ningún error.
Cualquier cambio acá hay que replicarlo en el notebook, y viceversa.
"""
import os
from functools import lru_cache

import numpy as np

from venomscope.validacion import normalizar

MODELO = "facebook/esm2_t12_35M_UR50D"   # ~150 MB, anda en CPU
DIM = 480

# Para la demo: nunca salir a internet. El modelo tiene que estar descargado.
os.environ.setdefault("HF_HUB_OFFLINE", "1")


@lru_cache(maxsize=1)
def cargar_modelo():
    """Carga tokenizer y modelo una sola vez (tarda unos segundos)."""
    import torch
    from transformers import AutoModel, AutoTokenizer
    from transformers.utils import logging

    logging.set_verbosity_error()   # oculta el aviso de pesos 'lm_head' que no usamos
    tokenizer = AutoTokenizer.from_pretrained(MODELO)
    modelo = AutoModel.from_pretrained(MODELO)
    modelo.eval()                   # modo evaluación: no lo entrenamos, solo lo usamos
    ids_especiales = torch.tensor(tokenizer.all_special_ids)
    return tokenizer, modelo, ids_especiales


def embeber(secuencias: list[str], batch: int = 16, progreso=None) -> np.ndarray:
    """Convierte una lista de secuencias en una matriz (n_secuencias x 480).

    `progreso`, si se pasa, se llama con (hechas, total) después de cada lote.
    """
    import torch

    tokenizer, modelo, ids_especiales = cargar_modelo()
    secuencias = [normalizar(s) for s in secuencias]
    salida = []

    with torch.no_grad():           # no calculamos gradientes: no estamos entrenando
        for i in range(0, len(secuencias), batch):
            lote = secuencias[i:i + batch]
            enc = tokenizer(lote, return_tensors="pt", padding=True, truncation=True)
            h = modelo(**enc).last_hidden_state              # (lote, largo, 480)

            # Máscara: 1 en los aminoácidos de verdad, 0 en relleno y tokens especiales
            es_especial = torch.isin(enc["input_ids"], ids_especiales)
            mascara = (~es_especial).float() * enc["attention_mask"].float()
            mascara = mascara.unsqueeze(-1)                  # (lote, largo, 1)

            # Promedio sobre los aminoácidos reales
            vec = (h * mascara).sum(1) / mascara.sum(1).clamp(min=1)
            salida.append(vec.numpy())

            if progreso:
                progreso(min(i + batch, len(secuencias)), len(secuencias))

    return np.vstack(salida).astype(np.float32)
