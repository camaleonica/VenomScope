"""Pantalla de inicio: una campaña entera, ordenada y con el plan de laboratorio.

Es el caso de uso real del laboratorio, así que es lo primero que se ve. Abre con
la campaña de demostración ya analizada: nadie tiene que cargar nada para entender
qué hace el producto. Desde una fila se entra al detalle de esa muestra.

Cuatro secciones: la campaña, el plan (qué mandar a estudiar y qué volvió del
laboratorio), el detalle de una muestra y su mapa.
"""
from datetime import datetime

import streamlit as st

from interfaz import componentes, informe
from interfaz.comun import (CAMPANAS_DE_PRUEBA, OPCIONES_NEA, campana_demo, control_umbral,
                            umbrales_elegidos)
from interfaz.editorial import bloque, cabeza, marca, numero, seccion, subtitulo
from interfaz.plan_lab import mostrar_plan
from interfaz.resultado import mostrar_resultado
from interfaz.seguimiento_lab import altas, mostrar_seguimiento
from venomscope import prioridad, seguimiento
from venomscope.analisis import SIN_ANALIZAR, Motor, reevaluar, tabla_resultados
from venomscope.lectura import leer_archivo
from venomscope.novedad import NIVEL_NOVEDOSA

TOTAL = 4   # la campaña, el plan, el detalle de una muestra y su mapa


def mostrar(motor: Motor):
    resultados, es_demo = _resultados_vigentes(motor)

    # Los umbrales se leen antes de dibujar nada, porque la tabla depende de ellos;
    # el deslizante se dibuja después, debajo de lo que controla.
    umbrales = umbrales_elegidos(motor, "umbral_campana")
    reevaluar(resultados, umbrales)
    tabla = tabla_resultados(resultados)

    with seccion("campana_tabla"):
        elegida = _portada_campana(motor, resultados, tabla, es_demo)
    with seccion("campana_plan"):
        _plan_y_seguimiento(motor, resultados, tabla, umbrales)

    por_id = {r.id: r for r in resultados}
    mostrar_resultado(por_id[elegida], motor, clave="mapa_campana", n=3, total=TOTAL,
                      umbrales=umbrales)


# ------------------------------------------------------ de dónde salen los datos --
def _resultados_vigentes(motor: Motor) -> tuple[list, bool]:
    """La campaña que hay que mostrar, rehecha si el laboratorio confirmó algo.

    Rehacerla es barato: los embeddings ya están en la caché de disco.
    """
    propias = st.session_state.get("entradas_campana")
    if propias is None:
        archivo = CAMPANAS_DE_PRUEBA[st.session_state.get("demo_campana", "General")]
        return campana_demo(motor, archivo, motor.firma), True

    if st.session_state.get("firma_campana") != motor.firma:
        with st.spinner("Actualizando con lo que confirmó el laboratorio..."):
            st.session_state["resultados_campana"] = motor.analizar(propias)
        st.session_state["firma_campana"] = motor.firma
    return st.session_state["resultados_campana"], False


# ----------------------------------------------------------------- 01 la campaña --
def _resumen(tabla, resultados) -> str:
    """Las cifras de arriba: en qué estado quedó la campaña de un vistazo."""
    conteo = tabla["Prioridad"].value_counts()
    validos = [r for r in resultados if r.validacion.es_valida]
    familias = len({r.prediccion.familia for r in validos})
    sin_par = sum(1 for r in validos if r.novedad.nivel == NIVEL_NOVEDOSA)

    cifras = [
        (conteo.get(prioridad.ALTA, 0), "Prioridad alta", "Empezar por acá."),
        (conteo.get(prioridad.MEDIA, 0), "Prioridad media", "Vale una mirada."),
        (conteo.get(prioridad.BAJA, 0), "Prioridad baja", "Parecidas a algo ya estudiado."),
        (familias, "Familias distintas", "Cuántos tipos de toxina distintos hay en la campaña."),
        (sin_par, "Sin correspondencia", "No se parecen a nada del catálogo."),
    ]
    columnas = "".join(
        f'<div>{numero(i)}<p class="vs-cifra">{valor}</p>'
        f'<p class="vs-item-titulo">{nombre}</p><div class="vs-chico">{detalle}</div></div>'
        for i, (valor, nombre, detalle) in enumerate(cifras, start=1))
    return f'<div class="vs-columnas" style="--cols:5; margin-bottom:40px">{columnas}</div>'


def _portada_campana(motor: Motor, resultados, tabla, es_demo: bool) -> str:
    sin_leer = int((tabla["Prioridad"] == SIN_ANALIZAR).sum())
    aviso = (f" {sin_leer} no se pudo leer y queda marcada." if sin_leer == 1 else
             f" {sin_leer} no se pudieron leer y quedan marcadas." if sin_leer else "")
    origen = ("Estas son las <b>muestras de demostración</b>: variantes de toxinas del NEA, "
              "toxinas de otras regiones del mundo y una lectura con errores."
              if es_demo else "Estas son las muestras del archivo que subiste.")
    niveles = [prioridad.ALTA, prioridad.MEDIA, prioridad.BAJA, SIN_ANALIZAR]
    conteo = tabla["Prioridad"].value_counts()

    bloque(f"""
    {cabeza(1, TOTAL, "La campaña", "La campa[ñ]a|ent[e]ra")}
    <div class="vs-esquina" style="margin-bottom:64px">
      <div class="vs-chico">{len(tabla)} muestras analizadas y ordenadas para saber
      {marca("cuáles mirar primero")}.{aviso}</div>
      <div class="vs-chico">{origen} Para ver una en detalle, <b>marcá la casilla</b> que está
      al principio de su fila.</div>
    </div>
    {_resumen(tabla, resultados)}
    {componentes.distribucion([(n, int(conteo.get(n, 0))) for n in niveles])}
    """)

    # Las primeras de la tabla ya son las que hay que mirar antes.
    primeras = tabla[tabla["Prioridad"] != SIN_ANALIZAR].head(3)
    if len(primeras):
        bloque(subtitulo(1, "Las de mayor novedad")
               + componentes.tarjetas_muestras(primeras.to_dict("records")))

    bloque(subtitulo(2, "Todas las muestras, ordenadas por prioridad"))
    elegida = _lista(tabla)
    with st.container(key="franja_umbral_campana"):
        bloque(subtitulo(3, "Ajustar la sensibilidad"))
        control_umbral(motor, "umbral_campana")
    _cargar_otra(motor)
    return elegida


def _lista(tabla) -> str:
    """La campaña ordenada. Devuelve la muestra elegida; por defecto, la primera."""
    seleccion = st.dataframe(
        tabla, hide_index=True, width="stretch", key="filas_campana",
        on_select="rerun", selection_mode="single-row",
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

    # La fila marcada. Si no hay ninguna, se muestra la primera: la pantalla
    # nunca arranca a medias. AppTest no simula la selección, de ahí el getattr.
    filas = getattr(getattr(seleccion, "selection", None), "rows", []) or []
    return tabla.loc[filas[0] if filas else 0, "Muestra"]


def _cargar_otra(motor: Motor):
    with st.expander("Analizar otra campaña"):
        c1, c2 = st.columns([3, 1])
        with c1:
            archivo = st.file_uploader(
                "Archivo con las secuencias",
                type=["fasta", "fa", "faa", "txt", "csv", "tsv"],
                help="FASTA, o CSV con una columna 'secuencia'. Opcionales: 'nombre' y 'nea'.")
        with c2:
            nea = st.radio("¿Son de especies del NEA?", list(OPCIONES_NEA), index=2,
                           key="nea_campana", help="Salvo que el CSV traiga una columna 'nea'.")
            st.radio("O probá otra campaña de prueba", list(CAMPANAS_DE_PRUEBA),
                     key="demo_campana",
                     help="General: 11 muestras variadas y una lectura con errores. Con "
                          "variantes repetidas: 13 muestras, dos péptidos novedosos con "
                          "varias variantes cada uno. Sirve para ver qué aporta el plan.")
            if st.session_state.get("entradas_campana") and st.button("Volver a la de prueba"):
                for clave in ("entradas_campana", "resultados_campana", "firma_campana"):
                    st.session_state.pop(clave, None)
                st.rerun()

        if st.button("Analizar campaña", type="primary", key="analizar_campana",
                     disabled=not archivo):
            try:
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
                st.session_state.pop("efecto_seguimiento", None)   # era de la campaña anterior
            st.rerun()


# -------------------------------------------- 02 el plan y lo que vuelve del lab --
def _plan_y_seguimiento(motor: Motor, resultados, tabla, umbrales: dict):
    bloque(f"""
    {cabeza(2, TOTAL, "El plan", "Qué man[d]ar|a est[u]diar")}
    <div class="vs-esquina" style="margin-bottom:48px">
      <div class="vs-chico">Ordenar por novedad dice <b>cuál mirar primero</b>, pero no
      {marca("cuáles elegir")}. Si varias muestras son variantes de lo mismo, todas quedan
      arriba y gastan cupos en un solo hallazgo.</div>
      <div class="vs-chico">El plan elige las que <b>representan</b> a toda la campaña. Y
      cuando el laboratorio estudia una, lo que aprendió vuelve al sistema.</div>
    </div>
    """)
    mostrado = mostrar_plan(motor, resultados)
    mostrar_seguimiento(motor, resultados, altas(tabla))
    _descargar_informe(motor, tabla, resultados, mostrado, umbrales)


def _descargar_informe(motor: Motor, tabla, resultados, mostrado, umbrales: dict):
    """Un solo archivo HTML para entregar o imprimir, con los mismos números de pantalla."""
    confirmadas = int(motor.catalogo["accession"].map(seguimiento.es_confirmada).sum())
    ahora = datetime.now()
    bloque(subtitulo(3, "Llevarse la campaña"))
    st.download_button(
        "Descargar el informe de la campaña (HTML)",
        informe.construir(
            tabla=tabla,
            ids_plan=mostrado.ids if mostrado else None,
            armado=mostrado.armado if mostrado else None,
            nivel_de={r.id: r.prioridad.nivel for r in resultados if r.prioridad},
            cupos=mostrado.cupos if mostrado else 0,
            umbrales=umbrales, catalogo_n=len(motor.catalogo), n_confirmadas=confirmadas,
            fecha=ahora, metricas=motor.config.get("metricas")).encode("utf-8"),
        file_name=f"venomscope_informe_{ahora:%Y%m%d}.html", mime="text/html",
        help="Para entregar o imprimir: resumen, plan de laboratorio, todas las muestras "
             "y los límites del sistema.")
