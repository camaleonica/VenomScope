"""La tarjeta con el resultado de una secuencia: primero la respuesta, después el porqué.

Son dos secciones: la blanca con la respuesta y la tabla, y la negra con el mapa 3D,
que conserva su propia paleta oscura (venomscope/mapa.py).
"""
import streamlit as st

from interfaz.editorial import bloque, cabeza, marca, seccion, subtitulo
from venomscope import prioridad
from venomscope.analisis import Motor
from venomscope.grupos import nombre as nombre_grupo
from venomscope.mapa import figura_3d
from venomscope.novedad import NIVEL_MEDIA, NIVEL_NOVEDOSA


def _veredicto(r) -> str:
    """Una sola frase que diga qué hacer con esta secuencia."""
    if r.vecinos.iloc[0]["distancia"] < 1e-4:
        v = r.vecinos.iloc[0]
        return (f"Esta secuencia **ya está en el catálogo**: es {v['nombre_proteina'].split(' (')[0]} "
                f"de *{v['especie']}*.")
    if r.novedad.nivel == NIVEL_NOVEDOSA:
        return ("**No se parece a nada que tengamos.** Puede ser una familia nueva. "
                "La familia de abajo es solo la menos lejana: tomala con pinzas.")
    if r.novedad.nivel == NIVEL_MEDIA:
        return "**Es pariente lejano de algo conocido.** Puede tener una variante interesante."
    return "**Se parece mucho a toxinas ya estudiadas.** Probablemente sea una variante."


def _palabra_prioridad(nivel: str) -> str:
    """La prioridad en letras grandes. Solo la alta lleva resaltador: es la que hay que ver."""
    texto = marca(nivel) if nivel == prioridad.ALTA else nivel
    clase = "vs-prioridad" + ("" if nivel in (prioridad.ALTA, prioridad.MEDIA) else " vs-prioridad--baja")
    return f'<p class="{clase}">{texto}</p>'


def mostrar_resultado(r, motor: Motor, clave: str = "mapa", n: int = 2, total: int = 3):
    """`n` y `total` numeran las secciones: el resultado es la n y el mapa la n + 1."""
    with seccion(f"resultado_{clave}"):
        if not r.validacion.es_valida:
            bloque(cabeza(n, total, "Resultado", "No se pu[d]o|analizar"))
            st.error("**No se pudo analizar esta secuencia.**\n\n" + "\n\n".join(r.validacion.errores))
            return
        bloque(cabeza(n, total, "Resultado", "Re[s]ultado"))
        _respuesta(r, clave)

    if r.punto3d is not None:
        _mapa(r, motor, clave, n + 1, total)


def _respuesta(r, clave: str):
    c1, c2, c3 = st.columns(3)
    c1.markdown("Prioridad", help="Qué tan urgente es estudiarla en el laboratorio. Sale de "
                                  "reglas fijas, no de la IA: abajo dice por qué.")
    with c1:
        bloque(_palabra_prioridad(r.prioridad.nivel))
    c2.metric("Novedad", f"{r.novedad.puntaje:.0f}/100", r.novedad.nivel, delta_color="off", delta_arrow="off",
              help="Qué tan distinta es de todo lo que hay en el catálogo. Un 97 quiere decir "
                   "que está más lejos de lo conocido que el 97% de las toxinas del catálogo.")
    c3.metric("Seguridad de la familia", f"{r.prediccion.confianza:.0%}",
              "baja" if r.prediccion.baja_confianza else "suficiente", delta_color="off", delta_arrow="off",
              help="Qué tan convencido está el sistema de la familia que eligió. Ojo: siempre "
                   "elige alguna, así que hay que mirarla junto con la novedad.")

    with st.container(key=f"veredicto_{clave}"):
        st.markdown(_veredicto(r))
    st.markdown(f"**Familia probable:** {r.prediccion.familia}",
                help="El grupo de toxinas conocidas al que más se parece. Toxinas de la misma "
                     "familia suelen actuar de forma parecida.")

    for aviso in r.advertencias:
        st.warning(aviso)

    with st.expander("Por qué le dio esta prioridad"):
        st.markdown("\n".join(f"- {razon}" for razon in r.prioridad.razones))

    bloque(subtitulo(1, "Las cinco toxinas del catálogo más parecidas"))
    vecinos = r.vecinos.assign(
        grupo=[nombre_grupo(g) for g in r.vecinos["grupo"]],
        en_nea=r.vecinos["en_nea"].map({True: "Sí", False: "No"}),
        enlace="https://www.uniprot.org/uniprotkb/" + r.vecinos["accession"])
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


def _mapa(r, motor: Motor, clave: str, n: int, total: int):
    with seccion(f"mapa_{clave}", oscura=True):
        bloque(cabeza(n, total, "Mapa", "Dónde c[a]e|en el m[a]pa"))
        # key fija + uirevision en la figura: si el usuario giró el mapa y después
        # mueve el deslizante del umbral, no se le resetea la vista.
        st.plotly_chart(figura_3d(motor, r), width="stretch", key=clave, theme=None,
                        config={"displayModeBar": False})
        st.caption(
            "Girá con el mouse, acercá con la rueda, pasá por un punto para ver cuál es. "
            f"El mapa achata {motor.config['dim']} números a 3 y conserva el "
            f"{motor.config['mapa3d']['varianza_conservada']:.0%} de la información, así que "
            "**la posición es orientativa**. El puntaje del recuadro y las líneas a las toxinas "
            "más parecidas salen del cálculo completo."
        )
