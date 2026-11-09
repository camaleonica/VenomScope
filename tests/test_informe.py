"""El informe descargable: que sea un archivo solo, que escape lo de afuera y que no se rompa con datos raros."""
import re
from datetime import datetime

import numpy as np
import pandas as pd

from interfaz import informe
from venomscope import plan

FECHA = datetime(2026, 11, 8, 14, 5)
UMBRALES = {"medio": 75, "alto": 90}


def _grupos(tamanos, dim=8):
    rng = np.random.default_rng(0)
    return np.vstack([np.eye(dim)[i] + rng.normal(0, 0.01, (n, dim)) + 1 for i, n in enumerate(tamanos)])


def _caso(nombres=None, familia="Familia A"):
    X = _grupos([3, 2, 1])
    n = len(X)
    nombres = nombres or [f"M{i + 1}" for i in range(n)]
    niveles = ["Alta", "Alta", "Alta", "Media", "Media", "Baja"]
    tabla = pd.DataFrame({
        "Muestra": nombres, "Prioridad": niveles, "Familia probable": familia, "Confianza": 0.91,
        "Novedad (0-100)": [99, 97, 96, 80, 78, 20], "Nivel de novedad": "Novedosa",
        "Más parecida a": "Toxina X (Especie y)", "Motivo": "No se parece a nada del catálogo.", "Avisos": "",
    })
    armado = plan.armar(X, tabla["Novedad (0-100)"], corte=0.05, cupos_max=5)
    return tabla, nombres, armado, dict(zip(nombres, niveles))


def _informe(tabla, ids, armado, nivel_de, cupos=3, confirmadas=0):
    return informe.construir(tabla=tabla, ids_plan=ids, armado=armado, nivel_de=nivel_de, cupos=cupos,
                             umbrales=UMBRALES, catalogo_n=584, n_confirmadas=confirmadas, fecha=FECHA,
                             metricas={"macro_f1_esm2": 0.93, "macro_f1_esm2_agrupado": 0.66})


def test_el_informe_tiene_todas_las_secciones_y_los_numeros_de_la_campana():
    tabla, ids, armado, nivel_de = _caso()
    html = _informe(tabla, ids, armado, nivel_de)
    for texto in ("Informe de campaña", "Plan de laboratorio", "Todas las muestras",
                  "Cómo leer este informe y sus límites", "08/11/2026 14:05", "584 toxinas"):
        assert texto in html
    assert f"De 6 muestras, {armado.hallazgos} son hallazgos distintos" in html
    assert html.count("<tr><td class=\"num\">") == 3          # una fila por cupo en la tabla del plan
    assert html.startswith("<!doctype html>") and 'lang="es"' in html


def test_es_un_archivo_solo_sin_recursos_externos():
    tabla, ids, armado, nivel_de = _caso()
    html = _informe(tabla, ids, armado, nivel_de)
    for prohibido in ("src=", "href=", "<link", "@import", "url(", "<script"):
        assert prohibido not in html, prohibido
    assert "https://" not in html and html.count("http://") == html.count("http://www.w3.org/2000/svg")


def test_escapa_lo_que_viene_de_afuera_en_todas_partes():
    malo = '<script>alert(1)</script>'
    tabla, ids, armado, nivel_de = _caso(nombres=[malo] + [f"M{i}" for i in range(2, 7)], familia=malo)
    tabla["Más parecida a"] = malo
    html = _informe(tabla, ids, armado, nivel_de)
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_sin_plan_el_informe_igual_se_arma():
    tabla, ids, _, nivel_de = _caso()
    html = _informe(tabla, None, None, nivel_de)
    assert "Plan de laboratorio" not in html and "Todas las muestras" in html
    assert "Se analizaron 6 muestras" in html


def test_las_muestras_no_analizadas_no_muestran_nan():
    tabla, ids, armado, nivel_de = _caso()
    tabla.loc[5, ["Familia probable", "Confianza", "Novedad (0-100)", "Más parecida a", "Motivo"]] = np.nan
    tabla.loc[5, ["Prioridad", "Avisos"]] = ["No analizada", "La secuencia tiene letras no válidas."]
    html = _informe(tabla, ids, armado, nivel_de)
    assert not re.search(r"\bnan\b", html.lower()) and "letras no válidas" in html


def test_dos_muestras_con_el_mismo_nombre_no_rompen_el_informe():
    tabla, ids, armado, nivel_de = _caso(nombres=["IGUAL"] * 6)
    assert "Informe de campaña" in _informe(tabla, ids, armado, nivel_de)


def test_se_aclara_cuantas_muestras_confirmo_el_laboratorio():
    tabla, ids, armado, nivel_de = _caso()
    assert "entre ellas 1 confirmada por el laboratorio" in _informe(tabla, ids, armado, nivel_de, confirmadas=1)
    assert "entre ellas 3 confirmadas por el laboratorio" in _informe(tabla, ids, armado, nivel_de, confirmadas=3)
    assert "confirmada" not in _informe(tabla, ids, armado, nivel_de, confirmadas=0)


def test_pedir_mas_cupos_de_los_que_hay_no_rompe():
    tabla, ids, armado, nivel_de = _caso()
    assert "Plan de laboratorio" in _informe(tabla, ids, armado, nivel_de, cupos=99)


def test_los_limites_estan_siempre():
    tabla, ids, armado, nivel_de = _caso()
    assert "No reemplaza el análisis de laboratorio" in _informe(tabla, ids, armado, nivel_de)
