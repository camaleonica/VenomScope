"""Pestaña "Una campaña entera": el caso real, muchas secuencias ordenadas por prioridad."""
from datetime import datetime

import streamlit as st

from interfaz import componentes, informe
from interfaz.comun import OPCIONES_NEA, control_umbral
from interfaz.estilo import mostrar_html
from interfaz.plan_lab import mostrar_plan
from interfaz.resultado import mostrar_resultado
from interfaz.seguimiento_lab import altas, mostrar_seguimiento
from venomscope import prioridad, seguimiento
from venomscope.analisis import ARTIFACTS, SIN_ANALIZAR, Motor, reevaluar, tabla_resultados
from venomscope.lectura import leer_archivo

CAMPANAS_DE_PRUEBA = {"General": "campana_demo.csv",
                      "Con variantes repetidas": "campana_redundante.csv"}


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
        if usar_demo:
            demo = st.radio("¿Cuál?", list(CAMPANAS_DE_PRUEBA), key="demo_campana",
                            help="General: 11 muestras variadas y una lectura con errores. Con variantes "
                                 "repetidas: 13 muestras, dos péptidos novedosos con varias variantes cada "
                                 "uno y algunas toxinas conocidas. Sirve para ver el plan de laboratorio.")

    if st.button("Analizar campaña", type="primary", disabled=not (archivo or usar_demo)):
        try:
            if usar_demo:
                ruta = ARTIFACTS.parent / "ejemplos" / CAMPANAS_DE_PRUEBA[demo]
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
            st.session_state["entradas_campana"] = entradas
            st.session_state["resultados_campana"] = motor.analizar(entradas)
            st.session_state["firma_campana"] = motor.firma
            st.session_state.pop("efecto_seguimiento", None)      # era de la campaña anterior

    resultados = st.session_state.get("resultados_campana")
    if not resultados:
        return
    # Si el laboratorio confirmó algo después de analizar, el resultado quedó viejo: se rehace.
    # Es rápido porque los embeddings ya están en la caché.
    if "entradas_campana" in st.session_state and st.session_state.get("firma_campana", motor.firma) != motor.firma:
        with st.spinner("Actualizando con lo que confirmó el laboratorio..."):
            resultados = motor.analizar(st.session_state["entradas_campana"])
        st.session_state["resultados_campana"] = resultados
        st.session_state["firma_campana"] = motor.firma

    st.divider()
    umbrales = control_umbral(motor, "umbral_campana")
    reevaluar(resultados, umbrales)
    st.divider()

    tabla = tabla_resultados(resultados)
    conteo = tabla["Prioridad"].value_counts()
    niveles = [prioridad.ALTA, prioridad.MEDIA, prioridad.BAJA, SIN_ANALIZAR]
    cols = st.columns(5)
    cols[0].metric("Secuencias", len(tabla))
    for col, nivel in zip(cols[1:], niveles):
        col.metric(f"Prioridad {nivel.lower()}" if nivel != SIN_ANALIZAR else "No analizadas",
                   int(conteo.get(nivel, 0)))
    mostrar_html(componentes.distribucion([(nivel, int(conteo.get(nivel, 0))) for nivel in niveles]))

    # La tabla ya viene ordenada: las primeras son las que hay que mirar antes.
    primeras = tabla[tabla["Prioridad"] != SIN_ANALIZAR].head(3)
    if len(primeras):
        st.markdown("##### Las de mayor novedad")
        mostrar_html(componentes.tarjetas_muestras(primeras.to_dict("records")))

    mostrado = mostrar_plan(motor, resultados)
    mostrar_seguimiento(motor, resultados, altas(tabla))

    st.markdown("##### Todas las muestras, ordenadas por prioridad")
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

    n_lab = int(motor.catalogo["accession"].map(seguimiento.es_confirmada).sum())
    ahora = datetime.now()
    st.download_button(
        "Descargar el informe de la campaña (HTML)",
        informe.construir(
            tabla=tabla, ids_plan=mostrado.ids if mostrado else None, armado=mostrado.armado if mostrado else None,
            nivel_de={r.id: r.prioridad.nivel for r in resultados if r.prioridad}, cupos=mostrado.cupos if mostrado else 0,
            umbrales=umbrales, catalogo_n=len(motor.catalogo), n_confirmadas=n_lab, fecha=ahora,
            metricas=motor.config.get("metricas")).encode("utf-8"),
        file_name=f"venomscope_informe_{ahora:%Y%m%d}.html", mime="text/html",
        help="Un solo archivo para entregar o imprimir: resumen, plan de laboratorio, todas las muestras y límites.")

    st.markdown("##### Ver una muestra en detalle")
    por_id = {r.id: r for r in resultados}
    elegida = st.selectbox("Muestra", tabla["Muestra"], label_visibility="collapsed")
    mostrar_resultado(por_id[elegida], motor, clave="mapa_campana", umbrales=umbrales)
