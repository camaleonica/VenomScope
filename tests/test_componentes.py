"""Las piezas HTML de la interfaz: se prueban solas, sin abrir Streamlit.

Lo que importa: que el HTML sobreviva a Markdown (sin líneas en blanco ni sangría), que
lo que viene de afuera se escape y que el color nunca vaya sin texto.
"""
from interfaz import componentes as c

UMBRALES = {"medio": 75, "alto": 90}


def _todas_las_piezas() -> list[str]:
    fila = {"Muestra": "M1", "Prioridad": "Alta", "Familia probable": "X", "Novedad (0-100)": 97,
            "Más parecida a": "Y (Z)"}
    return [
        c.encabezado("VenomScope", "lema"), c.insignia("Alta"), c.insignia("No analizada"),
        c.escala_novedad(97, UMBRALES, "Escala"), c.veredicto("a", "b", "Media"),
        c.distribucion([("Alta", 1), ("Media", 0), ("Baja", 2), ("No analizada", 0)]),
        c.tarjetas_muestras([fila]), c.pasos([{"titulo": "t", "texto": "x", "tipo": "ia"}]),
        c.cifras([(584, "toxinas")]), c.criterios([("alta", "alta", "texto")]),
        c.etiqueta("Prioridad"), c.cifra(89),
    ]


def test_el_html_no_tiene_lineas_en_blanco_ni_sangria():
    # Markdown toma un bloque con línea en blanco o 4 espacios al inicio por código.
    for pieza in _todas_las_piezas():
        assert "\n" not in pieza and not pieza.startswith("    "), pieza[:60]


def test_lo_que_viene_de_afuera_se_escapa():
    malo = '<script>alert(1)</script>"'
    fila = {"Muestra": malo, "Prioridad": "Alta", "Familia probable": malo,
            "Novedad (0-100)": 50, "Más parecida a": malo}
    for pieza in (c.tarjetas_muestras([fila]), c.insignia(malo), c.cifra(malo), c.etiqueta(malo),
                  c.cifras([(malo, malo)])):
        assert "<script>" not in pieza


def test_la_marca_cae_donde_dice_el_puntaje():
    assert "--p:97.0%" in c.escala_novedad(97, UMBRALES)
    assert "--p:100.0%" in c.escala_novedad(250, UMBRALES)   # no se sale de la escala
    assert "--p:0.0%" in c.escala_novedad(-3, UMBRALES)


def test_las_zonas_miden_lo_que_miden_los_cortes():
    html = c.escala_novedad(50, {"medio": 75, "alto": 85})
    assert "flex:75" in html and "flex:10" in html and "flex:15" in html


def test_se_resalta_solo_la_zona_donde_cae():
    assert c.escala_novedad(97, UMBRALES).count("vs-zona-activa") == 1
    assert c.escala_novedad(80, UMBRALES).count("vs-nombre-activo") == 1


def test_el_color_siempre_va_con_texto():
    assert "Alta" in c.insignia("Alta") and "Mirarla primero" in c.insignia("Alta")
    assert "Novedosa" in c.escala_novedad(97, UMBRALES)
    assert "Novedad 97 de 100" in c.escala_novedad(97, UMBRALES)   # lectores de pantalla


def test_la_leyenda_muestra_las_tres_prioridades_aunque_una_sea_cero():
    html = c.distribucion([("Alta", 3), ("Media", 0), ("Baja", 7), ("No analizada", 0)])
    assert "Media <b>0%</b>" in html and "No analizada" not in html
    assert "No analizada" in c.distribucion([("Alta", 1), ("No analizada", 1)])


def _arbol_de_juguete():
    import numpy as np
    from venomscope import plan
    X = np.array([[1, 0, 0], [1, 0.01, 0], [0, 1, 0], [0, 1, 0.01], [0, 0, 1]], dtype=float) + 1
    Z, etiquetas = plan.agrupar(plan.matriz_distancias(X), 0.05)
    nombres = ["a", "b", "c", "d", "<img src=x onerror=alert(1)>"]
    niveles = ["Alta", "Alta", "Media", "Baja", "No analizada"]
    return nombres, niveles, Z, etiquetas


def test_el_arbol_marca_el_plan_con_numeros_y_no_tiene_saltos_de_linea():
    nombres, niveles, Z, etiquetas = _arbol_de_juguete()
    html = c.arbol_hallazgos(nombres, niveles, Z, etiquetas, 0.05, {0: 1, 2: 2})
    assert "\n" not in html and html.startswith("<div") and "<svg" in html
    assert html.count("vs-plan-marca") == 2
    assert ">1</text>" in html and ">2</text>" in html
    assert "3 hallazgos" in html                       # el resumen para lectores de pantalla


def test_el_arbol_escapa_los_nombres_de_las_muestras():
    nombres, niveles, Z, etiquetas = _arbol_de_juguete()
    assert "<img" not in c.arbol_hallazgos(nombres, niveles, Z, etiquetas, 0.05, {})


def test_el_arbol_con_una_sola_muestra_no_dibuja_nada():
    import numpy as np
    assert c.arbol_hallazgos(["a"], ["Alta"], np.zeros((0, 4)), [1], 0.05, {}) == ""


def test_la_curva_dice_cuanto_cubre_cada_estrategia_con_texto():
    html = c.curva_plan([0.5, 0.8, 1.0], [0.3, 0.4, 0.9], 2)
    assert "\n" not in html
    assert "Plan" in html and "Ranking por novedad" in html
    assert "cubre 80%" in html and "ranking por novedad 40%" in html
    assert c.curva_plan([0.5], [0.5], 1) == ""


def test_la_leyenda_del_arbol_explica_cada_marca():
    html = c.leyenda_arbol()
    assert "\n" not in html
    for texto in ("lugar en el plan", "prioridad alta", "prioridad media", "prioridad baja", "hallazgo"):
        assert texto in html
