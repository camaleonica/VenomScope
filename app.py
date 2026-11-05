"""VenomScope: interfaz para el laboratorio.

Correr con:  .venv/bin/streamlit run app.py

Este archivo solo arma la página. Cada pestaña está en `interfaz/` y todo el
cálculo en `venomscope/`.
"""
import streamlit as st

from interfaz import ayuda, campana, intro, una
from interfaz.comun import barra_lateral, obtener_motor

st.set_page_config(page_title="VenomScope", layout="wide")

st.title("VenomScope")
st.markdown("Qué péptidos de la fauna del noreste argentino vale la pena investigar.")

try:
    motor = obtener_motor()
except FileNotFoundError:
    st.error("Faltan los archivos del modelo en `artifacts/`. Generalos con:\n\n"
             "`.venv/bin/python scripts/construir_artefactos.py`")
    st.stop()

barra_lateral(motor)
tab_intro, tab_una, tab_campana, tab_ayuda = st.tabs(
    ["Qué es esto", "Una secuencia", "Una campaña entera", "Cómo leer esto"])
with tab_intro:
    intro.mostrar(motor)
with tab_una:
    una.mostrar(motor)
with tab_campana:
    campana.mostrar(motor)
with tab_ayuda:
    ayuda.mostrar(motor)
