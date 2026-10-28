"""Estos tests cargan ESM-2 (unos segundos). Necesitan el modelo descargado."""
import numpy as np

from venomscope.embeddings import DIM, embeber

CORTA = "QWPRPQIPP"   # BPP de 9 aa
LARGA = (
    "MVLIRVIANLLILQVSYAQKSSELVIGGDECDINEHPFLAFMYYSPRYFCGMTLINQEWVLTAAHCNRRFMRI"
    "HLGKHAGSVANYDEVVRYPKEKFICPNKKKNVITDKDIMLIRLDRPVKNSEHIAPLSLPSNPPSVGSVCRIMGW"
)


def test_dimension():
    X = embeber([CORTA, LARGA])
    assert X.shape == (2, DIM)


def test_el_relleno_no_afecta_el_resultado():
    # Mismo chequeo que el Notebook 2: la corta sola vs. acompañada de una larga
    # (que la obliga a rellenarse). Si la máscara está mal, difieren.
    sola = embeber([CORTA])[0]
    en_lote = embeber([CORTA, LARGA])[0]
    assert np.abs(sola - en_lote).max() < 1e-3


def test_normaliza_antes_de_embeber():
    a = embeber([CORTA])[0]
    b = embeber(["  qwprp\nqipp "])[0]
    assert np.allclose(a, b)


def test_es_determinista():
    assert np.array_equal(embeber([LARGA]), embeber([LARGA]))
