"""La caché de embeddings: que no recalcule, que no cambie los números y que se banque archivos rotos.

Usa un `embeber` de mentira que cuenta cuántas veces lo llaman: no hace falta cargar ESM-2.
"""
import tempfile
import zlib
from pathlib import Path

import numpy as np

from venomscope import cache_embeddings as ce
from venomscope.embeddings import DIM


class EmbeberFalso:
    """Devuelve un vector que depende solo de la secuencia, y anota qué le pidieron."""

    def __init__(self):
        self.llamadas: list[list[str]] = []

    def __call__(self, secuencias, **kwargs):
        self.llamadas.append(list(secuencias))
        return np.vstack([np.random.default_rng(zlib.crc32(s.encode())).normal(size=DIM).astype(np.float32)
                          for s in secuencias])


def _con_carpeta(prueba):
    with tempfile.TemporaryDirectory() as d:
        prueba(Path(d))


def test_solo_calcula_lo_que_falta():
    def prueba(c):
        f = EmbeberFalso()
        ce.embeber_con_cache(["ACDEF", "GHIKL"], f, c)
        ce.embeber_con_cache(["GHIKL", "MNPQR", "ACDEF"], f, c)
        assert f.llamadas == [["ACDEF", "GHIKL"], ["MNPQR"]]
    _con_carpeta(prueba)


def test_un_acierto_devuelve_exactamente_lo_que_se_calculo():
    def prueba(c):
        f = EmbeberFalso()
        primera = ce.embeber_con_cache(["ACDEF", "GHIKL"], f, c)
        segunda = ce.embeber_con_cache(["ACDEF", "GHIKL"], f, c)
        assert len(f.llamadas) == 1
        assert np.array_equal(primera, segunda) and segunda.dtype == np.float32
    _con_carpeta(prueba)


def test_respeta_el_orden_y_calcula_una_vez_las_repetidas():
    def prueba(c):
        f = EmbeberFalso()
        X = ce.embeber_con_cache(["ACDEF", "ACDEF", "GHIKL"], f, c)
        assert f.llamadas == [["ACDEF", "GHIKL"]]
        assert X.shape == (3, DIM) and np.array_equal(X[0], X[1]) and not np.array_equal(X[0], X[2])
    _con_carpeta(prueba)


def test_la_misma_secuencia_escrita_distinto_usa_la_misma_entrada():
    def prueba(c):
        f = EmbeberFalso()
        ce.embeber_con_cache(["acdef"], f, c)
        ce.embeber_con_cache([" ACDEF \n"], f, c)
        assert len(f.llamadas) == 1
    _con_carpeta(prueba)


def test_una_entrada_rota_se_ignora_y_se_recalcula():
    def prueba(c):
        f = EmbeberFalso()
        bueno = ce.embeber_con_cache(["ACDEF"], f, c)
        archivo = next(c.glob("*.npy"))
        archivo.write_bytes(b"esto no es un npy")
        de_nuevo = ce.embeber_con_cache(["ACDEF"], f, c)
        assert len(f.llamadas) == 2 and np.array_equal(bueno, de_nuevo)
        assert ce._leer(archivo) is not None            # y quedó arreglada
    _con_carpeta(prueba)


def test_una_entrada_con_la_forma_equivocada_se_ignora():
    def prueba(c):
        f = EmbeberFalso()
        ce.embeber_con_cache(["ACDEF"], f, c)
        np.save(next(c.glob("*.npy")), np.zeros(7, dtype=np.float32))
        ce.embeber_con_cache(["ACDEF"], f, c)
        assert len(f.llamadas) == 2
    _con_carpeta(prueba)


def test_no_quedan_archivos_temporales():
    def prueba(c):
        ce.embeber_con_cache(["ACDEF", "GHIKL"], EmbeberFalso(), c)
        assert list(c.glob("*.tmp")) == [] and len(list(c.glob("*.npy"))) == 2
    _con_carpeta(prueba)


def test_cambiar_la_version_invalida_la_cache_vieja():
    def prueba(c):
        f = EmbeberFalso()
        version = ce.VERSION
        try:
            ce.embeber_con_cache(["ACDEF"], f, c)
            ce.VERSION = version + 1                    # cambió la lógica de embeber
            ce.embeber_con_cache(["ACDEF"], f, c)
        finally:
            ce.VERSION = version
        assert len(f.llamadas) == 2
    _con_carpeta(prueba)


def test_sin_secuencias_devuelve_una_matriz_vacia_de_la_forma_correcta():
    def prueba(c):
        f = EmbeberFalso()
        X = ce.embeber_con_cache([], f, c)
        assert X.shape == (0, DIM) and f.llamadas == []
    _con_carpeta(prueba)


def test_tamano_cuenta_lo_guardado_y_no_falla_si_no_hay_carpeta():
    def prueba(c):
        assert ce.tamano(c / "no_existe") == 0
        ce.embeber_con_cache(["ACDEF", "GHIKL", "ACDEF"], EmbeberFalso(), c)
        assert ce.tamano(c) == 2
    _con_carpeta(prueba)


def test_el_precalentado_junta_las_secuencias_de_los_ejemplos_y_las_campanas():
    import importlib.util
    ruta = Path(__file__).resolve().parent.parent / "scripts" / "precalentar_cache.py"
    spec = importlib.util.spec_from_file_location("precalentar_cache", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    secuencias = modulo.secuencias_de_demo()
    assert len(secuencias) == len(set(secuencias)) and len(secuencias) >= 20
    assert "CKGKGAKCSRLMYDCCTGSCRSGKC" in secuencias              # ziconotida, de los ejemplos y de la campaña
