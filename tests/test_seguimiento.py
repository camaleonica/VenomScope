"""El seguimiento: el libro de confirmaciones y el motor que aprende de él.

El motor se arma con datos inventados (sin ESM-2 ni artefactos): lo que se verifica es la lógica.
"""
import tempfile
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from venomscope import novedad, seguimiento as sg
from venomscope.analisis import Motor
from venomscope.embeddings import DIM

AHORA = datetime(2026, 11, 8, 10, 30)
SEQ_A, SEQ_B = "ACDEFGHIKLMNPQRSTVWY", "KLMNPQRSTVWYACDEFGHI"
COLUMNAS_CATALOGO = ["accession", "nombre_proteina", "especie", "genero_consultado", "organism_id",
                     "familia_proteica", "familia_nivel1", "familia_valida", "grupo", "en_nea", "largo",
                     "peptido_corto", "sequence", "clase", "clase_modelable"]


def _libro(d):
    return sg.Libro(Path(d) / "datos" / "seguimiento.csv")


def _conf(nombre="M1", seq=SEQ_A, familia="Conotoxina", nea=None):
    return sg.nueva(nombre, seq, familia, nea, AHORA)


# ----------------------------------------------------------------------- el libro ----
def test_lo_que_se_guarda_se_lee_igual_incluso_con_comas_comillas_y_tildes():
    with tempfile.TemporaryDirectory() as d:
        libro = _libro(d)
        a = _conf('Muestra, "especial" ñandú', SEQ_A, "Familia α, tipo 2", True)
        b = _conf("M2", SEQ_B, "Otra", False)
        c = _conf("M3", "MKTLLLTLVVV", "Tercera", None)
        for x in (a, b, c):
            libro.agregar(x)
        assert libro.leer() == [a, b, c]


def test_una_secuencia_repetida_se_reemplaza_en_vez_de_duplicarse():
    with tempfile.TemporaryDirectory() as d:
        libro = _libro(d)
        libro.agregar(_conf("M1", SEQ_A, "Familia equivocada"))
        libro.agregar(_conf("M1", SEQ_A, "Familia corregida"))
        leidas = libro.leer()
        assert len(leidas) == 1 and leidas[0].familia == "Familia corregida"


def test_deshacer_saca_la_ultima_y_vaciar_deja_todo_en_cero():
    with tempfile.TemporaryDirectory() as d:
        libro = _libro(d)
        assert libro.deshacer() is None                # no falla si no hay nada
        libro.agregar(_conf("M1", SEQ_A))
        libro.agregar(_conf("M2", SEQ_B))
        assert libro.deshacer().nombre == "M2" and [c.nombre for c in libro.leer()] == ["M1"]
        libro.vaciar()
        assert libro.leer() == [] and libro.firma() == ""


def test_si_el_archivo_no_existe_el_libro_esta_vacio():
    with tempfile.TemporaryDirectory() as d:
        assert _libro(d).leer() == []


def test_las_filas_incompletas_del_csv_se_ignoran():
    with tempfile.TemporaryDirectory() as d:
        libro = _libro(d)
        libro.ruta.parent.mkdir(parents=True)
        libro.ruta.write_text("nombre,secuencia,familia,es_del_nea,fecha\n"
                              f"bien,{SEQ_A},Fam,sí,2026-01-01 10:00\n"
                              f",{SEQ_B},Fam,sí,\n"
                              "solo_nombre,,,,\n", encoding="utf-8")
        assert [c.nombre for c in libro.leer()] == ["bien"]


def test_no_quedan_archivos_temporales():
    with tempfile.TemporaryDirectory() as d:
        libro = _libro(d)
        libro.agregar(_conf())
        libro.vaciar()
        assert list(libro.ruta.parent.glob("*.tmp")) == []


def test_nueva_normaliza_la_secuencia_y_rechaza_lo_que_no_sirve():
    assert sg.nueva("M", " acdefghikl \n", "F", None, AHORA).secuencia == "ACDEFGHIKL"
    for nombre, seq, familia in [("", SEQ_A, "F"), ("M", SEQ_A, "  "), ("M", "XXXX1234", "F"), ("M", "", "F")]:
        try:
            sg.nueva(nombre, seq, familia, None, AHORA)
        except ValueError as e:
            assert str(e)
        else:
            raise AssertionError(f"debió rechazar {(nombre, seq, familia)}")


def test_la_firma_cambia_cuando_cambia_lo_que_el_sistema_sabe():
    assert sg.firma_de([]) == ""
    a = sg.firma_de([_conf("M1", SEQ_A, "F1")])
    assert a == sg.firma_de([_conf("OTRO NOMBRE", SEQ_A, "F1")])         # el nombre no cambia lo que sabe
    assert a != sg.firma_de([_conf("M1", SEQ_A, "F2")])
    assert a != sg.firma_de([_conf("M1", SEQ_A, "F1"), _conf("M2", SEQ_B, "F1")])


def test_las_confirmadas_se_reconocen_por_su_accession():
    assert sg.es_confirmada("LAB-001") and not sg.es_confirmada("P0CC17")


def test_filas_de_catalogo_tienen_la_forma_del_catalogo():
    filas = sg.filas_catalogo([_conf("M1", SEQ_A, "F1", True), _conf("M2", SEQ_B, "F2", None)],
                              COLUMNAS_CATALOGO + ["columna_nueva_que_no_conocemos"])
    assert list(filas.columns) == COLUMNAS_CATALOGO + ["columna_nueva_que_no_conocemos"]
    assert list(filas["accession"]) == ["LAB-001", "LAB-002"]
    assert list(filas["en_nea"]) == [True, False] and not filas["clase_modelable"].any()
    assert filas.loc[0, "clase"] == "F1" and filas.loc[0, "largo"] == len(SEQ_A)
    assert filas["columna_nueva_que_no_conocemos"].isna().all()


# ------------------------------------------------------------------ el motor ampliado ----
def _motor_de_juguete():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(30, DIM)).astype(np.float32)
    m = Motor.__new__(Motor)                       # sin cargar artefactos
    m.catalogo = pd.DataFrame({
        "accession": [f"P{i:05d}" for i in range(30)], "nombre_proteina": "toxina", "especie": "Especie",
        "genero_consultado": "G", "organism_id": 1, "familia_proteica": "F", "familia_nivel1": "F",
        "familia_valida": True, "grupo": "serpiente", "en_nea": True, "largo": 50, "peptido_corto": False,
        "sequence": "A" * 50, "clase": "F", "clase_modelable": True})
    m.detector = novedad.DetectorNovedad(X, np.linspace(0.001, 0.2, 50))
    m.pca3d = PCA(n_components=3, random_state=0).fit(X)
    m.coords3d = m.pca3d.transform(X)
    return m, rng


def test_sin_confirmadas_el_motor_es_el_mismo():
    m, _ = _motor_de_juguete()
    assert m.con_confirmadas([]) is m and m.firma == ""


def test_el_motor_ampliado_conoce_lo_confirmado_y_el_original_no_cambia():
    m, rng = _motor_de_juguete()
    v = rng.normal(size=DIM).astype(np.float32)
    ampliado = m.con_confirmadas([_conf("ZIC-01", SEQ_A, "Conotoxina")], embeber_fn=lambda s, **k: np.vstack([v] * len(s)))

    assert len(ampliado.catalogo) == 31 and ampliado.detector.X_catalogo.shape == (31, DIM)
    assert ampliado.coords3d.shape == (31, 3) and ampliado.firma != ""
    assert sg.es_confirmada(ampliado.catalogo.iloc[-1]["accession"])
    # El original, intacto: lo comparte toda la app.
    assert len(m.catalogo) == 30 and m.detector.X_catalogo.shape == (30, DIM)
    assert m.coords3d.shape == (30, 3) and m.firma == ""


def test_una_variante_de_lo_confirmado_deja_de_ser_novedad():
    m, rng = _motor_de_juguete()
    v = rng.normal(size=DIM).astype(np.float32)
    variante = (v + rng.normal(scale=0.01, size=DIM)).astype(np.float32)[None]
    antes = m.detector.analizar(variante)[0].puntaje
    ampliado = m.con_confirmadas([_conf()], embeber_fn=lambda s, **k: np.vstack([v] * len(s)))
    despues = ampliado.detector.analizar(variante)[0]
    assert antes > 90 and despues.puntaje < 10
    assert sg.es_confirmada(ampliado.catalogo.iloc[despues.vecinos[0]]["accession"])   # su vecino más cercano


def test_la_escala_de_novedad_no_cambia_para_que_los_puntajes_sean_comparables():
    m, rng = _motor_de_juguete()
    v = rng.normal(size=DIM).astype(np.float32)
    ampliado = m.con_confirmadas([_conf()], embeber_fn=lambda s, **k: np.vstack([v] * len(s)))
    assert np.array_equal(ampliado.detector.escala, m.detector.escala)
    assert ampliado.detector.umbrales == m.detector.umbrales
