"""Pestaña "Una campaña entera": el caso real, muchas secuencias ordenadas por prioridad."""
import streamlit as st

from interfaz.comun import OPCIONES_NEA, control_umbral
from interfaz.resultado import mostrar_resultado
from venomscope import prioridad
from venomscope.analisis import ARTIFACTS, SIN_ANALIZAR, Motor, reevaluar, tabla_resultados
from venomscope.lectura import leer_archivo


def mostrar(motor: Motor):
    c1, c2 = st.columns([3, 1])
    with c1:
        archivo = st.file_uploader(
            "Archivo con las secuencias de la campaña",
            type=["fasta", "fa", "faa", "txt", "csv", "tsv"],
            help="FASTA, o CSV con una columna 'secuencia'. Opcionales: 'nombre' y 'nea'.")
    with c2:
        nea = st.radio("¿Son de especies del NEA?", list(OPCIONES_NEA), index=2,
                       key="nea_campana", help="Salvo que el CSV traiga una columna 'nea'.")
        usar_demo = st.toggle("Usar campaña de prueba",
                              help="11 muestras: variantes de toxinas del NEA, toxinas de otras "
                                   "regiones y una lectura con errores.")

    if st.button("Analizar campaña", type="primary", disabled=not (archivo or usar_demo)):
        try:
            if usar_demo:
                ruta = ARTIFACTS.parent / "ejemplos" / "campana_demo.csv"
                entradas = leer_archivo(ruta.name, ruta.read_bytes(), OPCIONES_NEA[nea])
            else:
                entradas = leer_archivo(archivo.name, archivo.getvalue(), OPCIONES_NEA[nea])
        except ValueError as e:
            st.error(str(e))
            return
        if not entradas:
            st.error("No se encontró ninguna secuencia en el archivo.")
            return
        with st.spinner(f"Analizando {len(entradas)} secuencias..."):
            st.session_state["resultados_campana"] = motor.analizar(entradas)

    resultados = st.session_state.get("resultados_campana")
    if not resultados:
        return

    st.divider()
    reevaluar(resultados, control_umbral(motor, "umbral_campana"))
    st.divider()

    tabla = tabla_resultados(resultados)
    conteo = tabla["Prioridad"].value_counts()
    cols = st.columns(5)
    cols[0].metric("Secuencias", len(tabla))
    for col, nivel in zip(cols[1:], [prioridad.ALTA, prioridad.MEDIA, prioridad.BAJA, SIN_ANALIZAR]):
        col.metric(f"Prioridad {nivel.lower()}" if nivel != SIN_ANALIZAR else "No analizadas",
                   int(conteo.get(nivel, 0)))

    st.dataframe(
        tabla, hide_index=True, width="stretch",
        column_config={
            "Confianza": st.column_config.NumberColumn("Seguridad", format="percent"),
            "Novedad (0-100)": st.column_config.ProgressColumn("Novedad", min_value=0,
                                                               max_value=100, format="%d"),
            "Motivo": st.column_config.TextColumn(width="large"),
            "Avisos": st.column_config.TextColumn(width="large"),
        },
    )
    st.download_button("Descargar la tabla (CSV)",
                       tabla.to_csv(index=False).encode("utf-8-sig"),   # Excel lee bien las tildes
                       file_name="venomscope_resultados.csv", mime="text/csv")

    st.markdown("##### Ver una muestra en detalle")
    por_id = {r.id: r for r in resultados}
    elegida = st.selectbox("Muestra", tabla["Muestra"], label_visibility="collapsed")
    mostrar_resultado(por_id[elegida], motor, clave="mapa_campana")
