"""Test de punta a punta con los artefactos reales (generados por scripts/construir_artefactos.py)."""
import numpy as np
import pytest

from venomscope.analisis import ARTIFACTS, SIN_ANALIZAR, Motor, reevaluar, tabla_resultados
from venomscope.novedad import NIVEL_MEDIA, NIVEL_NOVEDOSA
from venomscope.prioridad import ALTA, BAJA, MEDIA

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


def test_tabla_ordena_por_prioridad_y_deja_invalidas_al_final(motor):
    conocida = motor.catalogo["sequence"].iloc[0]
    ziconotida = "CKGKGAKCSRLMYDCCTGSCRSGKC"   # toxina de caracol marino, fuera del catálogo
    resultados = motor.analizar([("mala", "MKTX", None), ("conocida", conocida, None),
                                 ("novedosa", ziconotida, None)])
    tabla = tabla_resultados(resultados)
    assert list(tabla["Muestra"]) == ["novedosa", "conocida", "mala"]
    assert list(tabla["Prioridad"]) == [ALTA, BAJA, SIN_ANALIZAR]
    assert tabla.loc[1, "Novedad (0-100)"] == 0


def test_parecido_es_100_para_una_identica(motor):
    fila = motor.catalogo.iloc[3]
    r = motor.analizar([("x", fila["sequence"], None)])[0]
    assert r.vecinos.loc[0, "parecido"] == 100


def test_reevaluar_cambia_el_veredicto_sin_tocar_el_puntaje(motor):
    ziconotida = "CKGKGAKCSRLMYDCCTGSCRSGKC"
    r = motor.analizar([("x", ziconotida, None)])[0]
    puntaje = r.novedad.puntaje
    assert r.novedad.nivel == NIVEL_NOVEDOSA and r.prioridad.nivel == ALTA

    reevaluar([r], {"medio": 75, "alto": 99})
    assert r.novedad.puntaje == puntaje          # el puntaje es de la secuencia, no cambia
    assert r.novedad.nivel == NIVEL_MEDIA        # lo que cambia es a partir de cuándo se llama novedosa
    assert r.prioridad.nivel == MEDIA

    reevaluar([r], {"medio": 75, "alto": 90})
    assert r.prioridad.nivel == ALTA             # y vuelve


def test_reevaluar_no_rompe_con_invalidas(motor):
    resultados = motor.analizar([("mala", "MKTX", None)])
    reevaluar(resultados, {"medio": 75, "alto": 90})
    assert resultados[0].prioridad is None


def test_el_punto_del_catalogo_cae_donde_dice_el_mapa(motor):
    fila = motor.catalogo.iloc[7]
    r = motor.analizar([("x", fila["sequence"], None)])[0]
    assert np.allclose(r.punto3d, motor.coords3d[7], atol=1e-4)
