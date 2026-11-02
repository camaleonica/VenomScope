"""Prueba la interfaz sin abrir el navegador, con el simulador de Streamlit (AppTest)."""
import pytest
from streamlit.testing.v1 import AppTest

from venomscope.analisis import ARTIFACTS

if not (ARTIFACTS / "embeddings.npy").exists():
    pytest.skip("Faltan artefactos: correr scripts/construir_artefactos.py", allow_module_level=True)

TIMEOUT = 120


def texto_de(at) -> str:
    return " ".join(m.value for m in at.markdown) + " ".join(m.value for m in at.info)


@pytest.fixture
def app():
    at = AppTest.from_file(str(ARTIFACTS.parent / "app.py"), default_timeout=TIMEOUT)
    at.run()
    assert not at.exception
    return at


def test_la_app_abre_con_sus_tres_pestanas(app):
    assert [t.label for t in app.tabs] == ["Analizar una secuencia", "Analizar una campaña",
                                           "Cómo leer los resultados"]
    assert not app.error


def test_ejemplo_novedoso_da_prioridad_alta(app):
    app.selectbox(key="ejemplo").select("Toxina de afuera: ziconotida (caracol marino)").run()
    app.button[0].click().run()
    assert not app.exception
    assert "Alta" in texto_de(app)
    assert "No se parece a nada que tengamos" in texto_de(app)


def test_ejemplo_del_catalogo_se_reconoce(app):
    app.selectbox(key="ejemplo").select("Toxina conocida: fosfolipasa de yarará (NEA)").run()
    app.button[0].click().run()
    assert "ya está en el catálogo" in texto_de(app)
    assert "Baja" in texto_de(app)


def test_secuencia_invalida_muestra_error(app):
    app.text_area(key="secuencia").input("MKTXXZ").run()
    app.button[0].click().run()
    assert app.error
    assert "No se pudo analizar" in app.error[0].value


def test_campana_de_demostracion(app):
    app.toggle[0].set_value(True).run()
    app.button[1].click().run()
    assert not app.exception
    metricas = {m.label: m.value for m in app.metric}
    assert metricas["Secuencias"] == "11"
    assert metricas["No analizadas"] == "1"
    assert len(app.dataframe) >= 2   # la tabla de la campaña + los vecinos del detalle
