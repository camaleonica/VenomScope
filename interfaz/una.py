"""Pestaña "Una secuencia": pegar una o elegir un ejemplo."""
import streamlit as st

from interfaz.comun import OPCIONES_NEA, control_umbral
from interfaz.resultado import mostrar_resultado
from venomscope.analisis import Motor, reevaluar
from venomscope.ejemplos import EJEMPLOS
from venomscope.lectura import leer_fasta


def cargar_ejemplo():
    """Copia el ejemplo elegido al cuadro de texto.

    El desplegable se puede vaciar con su cruz, y entonces llega None: no hay nada que
    cargar y se deja la secuencia que esté escrita, en vez de borrarle lo suyo al usuario.
    """
    nombre = st.session_state["ejemplo"]
    if nombre is None:
        return
    ejemplo = EJEMPLOS[nombre]
    st.session_state["secuencia"] = ejemplo["secuencia"]
    st.session_state["nea_una"] = ejemplo["nea"]


def mostrar(motor: Motor):
    # El valor inicial se fija acá y no con index= en el radio: al elegir un ejemplo
    # lo pisamos desde session_state, y Streamlit se queja si se hacen las dos cosas.
    st.session_state.setdefault("nea_una", "No sé")

    c1, c2 = st.columns([3, 1])
    with c1:
        texto = st.text_area("Secuencia", height=150, key="secuencia",
                             placeholder="Pegá una secuencia de aminoácidos: MKTLLLTLVVVTIVCLDLGYT...")
    with c2:
        st.selectbox("O probá con un ejemplo", list(EJEMPLOS), index=None, key="ejemplo",
                     placeholder="Elegí uno", on_change=cargar_ejemplo)
        st.radio("¿Es de una especie del NEA?", list(OPCIONES_NEA),
                 key="nea_una", horizontal=True)
    if st.session_state.get("ejemplo"):
        st.caption(EJEMPLOS[st.session_state["ejemplo"]]["nota"])

    if st.button("Analizar", type="primary", disabled=not texto.strip()):
        entradas = leer_fasta(texto, OPCIONES_NEA[st.session_state["nea_una"]])
        if len(entradas) > 1:
            st.info(f"Hay {len(entradas)} secuencias y se analiza la primera. "
                    "Para varias, usá la otra pestaña.")
        with st.spinner("Analizando..."):
            st.session_state["entrada_una"] = entradas[:1]
            st.session_state["resultado_una"] = motor.analizar(entradas[:1])[0]
            st.session_state["firma_una"] = motor.firma

    # Si el laboratorio confirmó algo después de analizar, el resultado quedó viejo: se rehace.
    if "entrada_una" in st.session_state and st.session_state.get("firma_una", motor.firma) != motor.firma:
        st.session_state["resultado_una"] = motor.analizar(st.session_state["entrada_una"])[0]
        st.session_state["firma_una"] = motor.firma

    if "resultado_una" in st.session_state:
        st.divider()
        resultado = st.session_state["resultado_una"]
        umbrales = None
        if resultado.validacion.es_valida:
            umbrales = control_umbral(motor, "umbral_una")
            reevaluar([resultado], umbrales)
            st.divider()
        mostrar_resultado(resultado, motor, clave="mapa_una", umbrales=umbrales)
