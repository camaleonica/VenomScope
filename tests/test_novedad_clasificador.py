"""Tests con datos sintéticos (no cargan ESM-2): dos grupos de puntos bien separados."""
import numpy as np

from venomscope import clasificador, novedad

rng = np.random.default_rng(0)
CENTRO_A = np.r_[np.ones(10), np.zeros(10)]
CENTRO_B = np.r_[np.zeros(10), np.ones(10)]
X = np.vstack([CENTRO_A + 0.05 * rng.normal(size=(20, 20)),
               CENTRO_B + 0.05 * rng.normal(size=(20, 20))])
y = ["A"] * 20 + ["B"] * 20


def test_distancia_coseno_basica():
    D = novedad.distancias_coseno(np.array([[1.0, 0.0]]), np.array([[2.0, 0.0], [0.0, 1.0]]))
    assert np.allclose(D, [[0.0, 1.0]])


def test_calibrar_no_cuenta_la_propia_secuencia():
    escala = novedad.calibrar(X)
    assert len(escala) == len(X)
    assert (escala > 0).all()


def test_puntaje_va_de_0_a_100():
    escala = np.array([0.1, 0.2, 0.3, 0.4])
    assert novedad.puntaje(0.0, escala) == 0
    assert novedad.puntaje(0.25, escala) == 50
    assert novedad.puntaje(9.9, escala) == 100


def test_secuencia_del_catalogo_no_es_novedosa_y_una_rara_si():
    det = novedad.DetectorNovedad(X, novedad.calibrar(X))
    conocida, rara = det.analizar(np.vstack([X[0], -CENTRO_A]), k=3)
    assert conocida.nivel == novedad.NIVEL_CONOCIDA
    assert conocida.vecinos[0] == 0
    assert rara.nivel == novedad.NIVEL_NOVEDOSA
    assert len(rara.vecinos) == 3
    assert rara.distancias == sorted(rara.distancias)


def test_clasificador_predice_y_marca_confianza(tmp_path):
    modelo = clasificador.entrenar(X, y)
    ruta = tmp_path / "m.joblib"
    clasificador.guardar(modelo, ruta)
    modelo = clasificador.cargar(ruta)

    p = clasificador.predecir(modelo, CENTRO_B[None, :])[0]
    assert p.familia == "B"
    assert p.confianza > 0.9 and not p.baja_confianza
    assert p.alternativas[0][0] == "A"

    dudosa = clasificador.predecir(modelo, ((CENTRO_A + CENTRO_B) / 2)[None, :], umbral=0.99)[0]
    assert dudosa.baja_confianza
