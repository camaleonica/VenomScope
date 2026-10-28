"""Test de punta a punta con los artefactos reales (generados por scripts/construir_artefactos.py)."""
import pytest

from venomscope.analisis import ARTIFACTS, Motor
from venomscope.prioridad import BAJA

if not (ARTIFACTS / "embeddings.npy").exists():
    pytest.skip("Faltan artefactos: correr scripts/construir_artefactos.py", allow_module_level=True)


@pytest.fixture(scope="module")
def motor():
    return Motor()


def test_secuencia_del_catalogo_se_reconoce(motor):
    fila = motor.catalogo[motor.catalogo["clase_modelable"]].iloc[0]
    r = motor.analizar([("x", fila["sequence"], None)])[0]
    assert r.prediccion.familia == fila["clase"]
    assert r.novedad.puntaje == 0
    assert r.vecinos.loc[0, "accession"] == fila["accession"]
    assert r.vecinos.loc[0, "distancia"] == pytest.approx(0, abs=1e-5)
    assert r.prioridad.nivel == BAJA


def test_invalidas_no_rompen_el_lote(motor):
    resultados = motor.analizar([("mala", "MKTX", None), ("buena", "QWPRPQIPP", True)])
    assert not resultados[0].validacion.es_valida
    assert resultados[0].prediccion is None
    assert resultados[1].prioridad is not None
    assert resultados[1].advertencias   # péptido corto
