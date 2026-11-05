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


def test_la_app_abre_con_sus_cuatro_pestanas(app):
    assert [t.label for t in app.tabs] == ["Qué es esto", "Una secuencia",
                                           "Una campaña entera", "Cómo leer esto"]
    assert not app.error


def test_la_introduccion_explica_sin_suponer_biologia(app):
    intro = " ".join(m.value for m in app.tabs[0].markdown)
    for idea in ["aminoácidos", "familia", "captopril", "ESM-2", "vecinos", "reglas"]:
        assert idea in intro, f"La introducción no menciona: {idea}"


def test_los_numeros_del_resultado_tienen_ayuda(app):
    app.selectbox(key="ejemplo").select("Toxina de afuera: ziconotida (caracol marino)").run()
    app.button[0].click().run()
    ayudas = {m.label: m.help for m in app.metric}
    assert ayudas["Novedad"] and ayudas["Seguridad de la familia"]


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


def test_el_deslizante_arranca_en_90(app):
    app.selectbox(key="ejemplo").select("El caso difícil: ShK (anémona de mar)").run()
    app.button[0].click().run()
    assert app.slider(key="umbral_una").value == 90


def test_mover_el_deslizante_cambia_el_veredicto(app):
    app.selectbox(key="ejemplo").select("Toxina de afuera: ziconotida (caracol marino)").run()
    app.button[0].click().run()
    assert "Alta" in texto_de(app)

    app.slider(key="umbral_una").set_value(99).run()   # ziconotida saca 98: ya no llega
    assert not app.exception
    assert "Media" in texto_de(app)


def test_el_deslizante_explica_sus_consecuencias(app):
    app.selectbox(key="ejemplo").select("El caso difícil: ShK (anémona de mar)").run()
    app.button[0].click().run()
    assert "falsas alarmas" in texto_de(app)


def test_el_caso_shk_dibuja_el_mapa(app):
    app.selectbox(key="ejemplo").select("El caso difícil: ShK (anémona de mar)").run()
    app.button[0].click().run()
    assert not app.exception
    assert "99/100" in texto_de(app)
    assert "la posición es orientativa" in " ".join(c.value for c in app.caption)


def test_la_ayuda_cuenta_el_caso_del_captopril(app):
    assert "captopril" in texto_de(app)
    assert "Bothrops jararaca" in texto_de(app)
