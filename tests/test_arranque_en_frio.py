"""El ensayo del día de la entrega: la app tiene que abrir sin internet.

Es la condición para aprobar, así que está como test y no como algo que
alguien se acuerda de probar a mano.
"""
import socket

import pytest
from streamlit.testing.v1 import AppTest

from venomscope.analisis import ARTIFACTS

if not (ARTIFACTS / "config.json").exists():
    pytest.skip("Faltan artefactos: correr scripts/construir_artefactos.py", allow_module_level=True)


@pytest.fixture
def sin_internet(monkeypatch):
    """Cualquier intento de abrir una conexión falla, como en el aula sin wifi."""
    def prohibido(*a, **k):
        raise OSError("Sin internet (simulado por el test)")
    monkeypatch.setattr(socket.socket, "connect", prohibido)
    monkeypatch.setattr(socket, "create_connection", prohibido)


def test_la_app_abre_y_analiza_sin_internet(sin_internet):
    at = AppTest.from_file(str(ARTIFACTS.parent / "app.py"), default_timeout=300)
    at.run()
    assert not at.exception
    assert not at.error

    at.selectbox(key="ejemplo").select("El caso difícil: ShK (anémona de mar)").run()
    at.button(key="analizar_una").click().run()
    assert not at.exception
    assert "99/100" in " ".join(m.value for m in at.markdown)


def test_no_quedan_avisos_de_streamlit_al_abrir(sin_internet, caplog):
    at = AppTest.from_file(str(ARTIFACTS.parent / "app.py"), default_timeout=300)
    at.run()
    at.selectbox(key="ejemplo").select("Toxina conocida: fosfolipasa de yarará (NEA)").run()
    avisos = [r.message for r in caplog.records
              if r.levelname == "WARNING" and "Session State API" in r.message]
    assert not avisos, avisos
