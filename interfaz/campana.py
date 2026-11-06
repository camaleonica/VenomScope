"""Pestaña "Una campaña entera": el caso real, muchas secuencias ordenadas por prioridad."""
import streamlit as st

from interfaz.comun import OPCIONES_NEA, control_umbral
from interfaz.editorial import bloque, cabeza, marca, seccion, subtitulo
from interfaz.resultado import mostrar_resultado
from venomscope import prioridad
from venomscope.analisis import ARTIFACTS, SIN_ANALIZAR, Motor, reevaluar, tabla_resultados
from venomscope.lectura import leer_archivo


TOTAL = 4   # entrada, la campaña, el detalle de una muestra y su mapa


def mostrar(motor: Motor):
    with seccion("campana_entrada"):
        if not _entrada(motor):
            return   # el archivo no se pudo leer: el error ya está a la vista

    resultados = st.session_state.get("resultados_campana")
    if not resultados:
        return

    with seccion("campana_sensibilidad"):
        reevaluar(resultados, control_umbral(motor, "umbral_campana"))
    with seccion("campana_tabla"):
        elegida = _tabla(resultados)
    por_id = {r.id: r for r in resultados}
    mostrar_resultado(por_id[elegida], motor, clave="mapa_campana", n=3, total=TOTAL)


def _entrada(motor: Motor) -> bool:
    """Los controles para cargar la campaña. Devuelve False si el archivo no sirvió."""
    bloque(f"""
    {cabeza(1, TOTAL, "Entrada", "Una cam[p]aña|en[t]era")}
    <div class="vs-esquina" style="margin-bottom:48px">
      <div class="vs-chico">El caso real: todas las secuencias de una salida de muestreo de
      una vez, ordenadas para saber {marca("cuáles mirar primero")}.</div>
      <div class="vs-chico">Subí un FASTA o un CSV, o probá con la campaña de prueba: once
      muestras con variantes de toxinas del NEA, toxinas de otras regiones y una lectura
      con errores.</div>
    </div>
    """)
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
            return False
        if not entradas:
            st.error("No se encontró ninguna secuencia en el archivo.")
            return False
        with st.spinner(f"Analizando {len(entradas)} secuencias..."):
            st.session_state["resultados_campana"] = motor.analizar(entradas)
    return True


def _tabla(resultados) -> str:
    """La campaña ordenada por prioridad. Devuelve la muestra elegida para ver en detalle."""
    bloque(cabeza(2, TOTAL, "La campaña", "Por d[o]nde|em[p]ezar"))
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

    bloque(subtitulo(1, "Ver una muestra en detalle"))
    return st.selectbox("Muestra", tabla["Muestra"], label_visibility="collapsed")
