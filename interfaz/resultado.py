"""La tarjeta con el resultado de una secuencia: primero la respuesta, después el porqué.

De arriba para abajo: la prioridad y los dos números que la explican, la escala de
novedad (dónde cae y dónde están los cortes), una frase que dice qué hacer, la familia,
los avisos, las vecinas más parecidas y el mapa.
"""
from html import escape

import streamlit as st

from interfaz import componentes
from interfaz.estilo import mostrar_html
from venomscope.analisis import Motor
from venomscope.seguimiento import es_confirmada
from venomscope.grupos import nombre as nombre_grupo
from venomscope.mapa import figura_3d
from venomscope.novedad import NIVEL_MEDIA, NIVEL_NOVEDOSA


def _veredicto(r) -> tuple[str, str]:
    """Una frase corta que diga qué hacer con esta secuencia: (titular, detalle) en HTML.

    Lo que viene de la base de datos pasa por `escape` antes de entrar al HTML.
    """
    if r.vecinos.iloc[0]["distancia"] < 1e-4:
        v = r.vecinos.iloc[0]
        if es_confirmada(v["accession"]):
            return ("Esta muestra ya fue estudiada por el laboratorio.",
                    f"Es {escape(v['nombre_proteina'])}, confirmada como {escape(v['clase'])}.")
        return ("Esta secuencia ya está en el catálogo.",
                f"Es {escape(v['nombre_proteina'].split(' (')[0])} de <em>{escape(v['especie'])}</em>.")
    if r.novedad.nivel == NIVEL_NOVEDOSA:
        return ("No se parece a nada que tengamos.",
                "Puede ser una familia nueva. La familia de abajo es solo la menos lejana: "
                "tomala con pinzas.")
    if r.novedad.nivel == NIVEL_MEDIA:
        return ("Es pariente lejano de algo conocido.", "Puede tener una variante interesante.")
    return ("Se parece mucho a toxinas ya estudiadas.", "Probablemente sea una variante.")


def mostrar_resultado(r, motor: Motor, clave: str = "mapa", umbrales: dict | None = None):
    """`umbrales` son los cortes de novedad que está usando el control de sensibilidad;
    si no se pasan, se usan los de la configuración."""
    if not r.validacion.es_valida:
        st.error("**No se pudo analizar esta secuencia.**\n\n" + "\n\n".join(r.validacion.errores))
        return
    umbrales = umbrales or motor.config["novedad"]["umbrales_puntaje"]

    # La clave le pone nombre al contenedor para que la hoja de estilos pueda sacarle
    # el recuadro a estas dos métricas: acá van sueltas, al lado de la insignia.
    with st.container(key=f"resumen_{clave}"):
        c1, c2, c3 = st.columns(3)
        c1.markdown(componentes.etiqueta("Prioridad"), unsafe_allow_html=True,
                    help="Qué tan urgente es estudiarla en el laboratorio. Sale de "
                         "reglas fijas, no de la IA: abajo dice por qué.")
        with c1:
            mostrar_html(componentes.insignia(r.prioridad.nivel))
        c2.metric("Novedad", f"{r.novedad.puntaje:.0f}/100", r.novedad.nivel, delta_color="off", delta_arrow="off",
                  help="Qué tan distinta es de todo lo que hay en el catálogo. Un 97 quiere decir "
                       "que está más lejos de lo conocido que el 97% de las toxinas del catálogo.")
        c3.metric("Seguridad de la familia", f"{r.prediccion.confianza:.0%}",
                  "baja" if r.prediccion.baja_confianza else "suficiente", delta_color="off", delta_arrow="off",
                  help="Qué tan convencido está el sistema de la familia que eligió. Ojo: siempre "
                       "elige alguna, así que hay que mirarla junto con la novedad.")

    mostrar_html(componentes.escala_novedad(r.novedad.puntaje, umbrales, "Escala de novedad"))
    titular, detalle = _veredicto(r)
    mostrar_html(componentes.veredicto(titular, detalle, r.prioridad.nivel))
    st.markdown(f"**Familia probable:** {r.prediccion.familia}",
                help="El grupo de toxinas conocidas al que más se parece. Toxinas de la misma "
                     "familia suelen actuar de forma parecida.")

    for aviso in r.advertencias:
        st.warning(aviso)

    with st.expander("Por qué le dio esta prioridad"):
        st.markdown("\n".join(f"- {razon}" for razon in r.prioridad.razones))

    st.markdown("##### Las cinco toxinas del catálogo más parecidas")
    vecinos = r.vecinos.assign(
        grupo=[nombre_grupo(g) for g in r.vecinos["grupo"]],
        en_nea=r.vecinos["en_nea"].map({True: "Sí", False: "No"}),
        # Las muestras del laboratorio no tienen ficha en UniProt.
        enlace=[None if es_confirmada(a) else "https://www.uniprot.org/uniprotkb/" + a
                for a in r.vecinos["accession"]])
    st.dataframe(
        vecinos[["nombre_proteina", "especie", "grupo", "clase", "en_nea", "parecido", "enlace"]],
        hide_index=True, width="stretch",
        column_config={
            "nombre_proteina": st.column_config.TextColumn("Proteína", width="large"),
            "especie": "Especie",
            "grupo": st.column_config.TextColumn("Grupo", width="small"),
            "clase": "Familia",
            "en_nea": st.column_config.TextColumn("Del NEA", width="small"),
            "parecido": st.column_config.ProgressColumn("Parecido", min_value=0, max_value=100,
                                                        format="%.0f"),
            "enlace": st.column_config.LinkColumn("Ficha", display_text="UniProt"),
        },
    )

    if r.punto3d is not None:
        st.markdown("##### Dónde cae en el mapa del catálogo")
        # key fija + uirevision en la figura: si el usuario giró el mapa y después
        # mueve el deslizante del umbral, no se le resetea la vista.
        st.plotly_chart(figura_3d(motor, r), width="stretch", key=clave,
                        config={"displayModeBar": False})
        st.caption(
            "Girá con el mouse, acercá con la rueda, pasá por un punto para ver cuál es. "
            f"El mapa achata {motor.config['dim']} números a 3 y conserva el "
            f"{motor.config['mapa3d']['varianza_conservada']:.0%} de la información, así que "
            "**la posición es orientativa**. El puntaje del recuadro y las líneas a las toxinas "
            "más parecidas salen del cálculo completo."
        )
