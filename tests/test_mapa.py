import pytest

from venomscope.analisis import ARTIFACTS, Motor
from venomscope.iconos import ICONOS_GRUPO, con_icono
from venomscope.mapa import figura_3d

if not (ARTIFACTS / "proyeccion3d.joblib").exists():
    pytest.skip("Faltan artefactos: correr scripts/construir_artefactos.py", allow_module_level=True)

SHK = "RSCIDTIPKSRCTAFQCKHSMKYRLSFCRKTCGTC"


@pytest.fixture(scope="module")
def motor():
    return Motor()


def test_todos_los_grupos_del_catalogo_tienen_icono(motor):
    assert set(motor.catalogo["grupo"]) <= set(ICONOS_GRUPO)


def test_el_icono_viene_con_el_nombre_escrito():
    assert con_icono("arana") == "🕷️ araña"
    assert "serpiente" in con_icono("serpiente")


def test_el_mapa_solo_muestra_el_catalogo_si_no_hay_secuencia(motor):
    fig = figura_3d(motor)
    assert len(fig.data) == 2            # los puntos y las etiquetas de familia
    assert fig.data[0].x.shape[0] == len(motor.catalogo)


def test_el_mapa_marca_la_secuencia_y_sus_vecinos(motor):
    r = motor.analizar([("ShK", SHK, None)])[0]
    fig = figura_3d(motor, r)
    nombres = [t.name for t in fig.data if t.name]
    assert "Tu secuencia" in nombres
    assert any("más parecidas" in n for n in nombres)


def test_el_puntaje_va_escrito_al_lado_del_punto(motor):
    """Lo que impide que el dibujo contradiga al veredicto cuando la posición engaña.

    ShK es justamente ese caso: novedad 99 pero cae en el medio del montón.
    """
    r = motor.analizar([("ShK", SHK, None)])[0]
    anotaciones = figura_3d(motor, r).layout.scene.annotations
    assert len(anotaciones) == 1
    assert f"{r.novedad.puntaje:.0f}/100" in anotaciones[0].text
    assert r.novedad.nivel in anotaciones[0].text
    assert anotaciones[0].bgcolor                      # fondo propio: se lee aunque algo le caiga encima


def test_el_mapa_es_identico_entre_ejecuciones(motor):
    """Si no, el gráfico cambiaría de forma cada vez que se abre la app."""
    a, b = figura_3d(motor), figura_3d(Motor())
    assert (a.data[0].x == b.data[0].x).all()
    assert (a.data[0].z == b.data[0].z).all()
