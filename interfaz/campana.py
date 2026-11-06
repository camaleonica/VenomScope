"""Pantalla de inicio: una campaña entera, ordenada por prioridad.

Es el caso de uso real del laboratorio, así que es lo primero que se ve. Abre
con la campaña de demostración ya analizada: nadie tiene que cargar nada para
entender qué hace el producto. Desde una fila se entra al detalle de esa muestra.
"""
import streamlit as st

from interfaz.comun import OPCIONES_NEA, campana_demo, control_umbral, umbrales_elegidos
from interfaz.editorial import bloque, cabeza, marca, numero, seccion, subtitulo
from interfaz.resultado import mostrar_resultado
from venomscope import prioridad
from venomscope.analisis import SIN_ANALIZAR, Motor, reevaluar, tabla_resultados
from venomscope.lectura import leer_archivo
from venomscope.novedad import NIVEL_NOVEDOSA

TOTAL = 3   # la campaña, el detalle de una muestra y su mapa


def mostrar(motor: Motor):
    resultados = st.session_state.get("resultados_campana") or campana_demo(motor)
    es_demo = "resultados_campana" not in st.session_state

    # Los umbrales se leen antes de dibujar nada, porque la tabla depende de
    # ellos; el deslizante se dibuja después, debajo de lo que controla.
    reevaluar(resultados, umbrales_elegidos(motor, "umbral_campana"))
    with seccion("campana_tabla"):
        elegida = _portada_campana(motor, resultados, es_demo)
    por_id = {r.id: r for r in resultados}
    mostrar_resultado(por_id[elegida], motor, clave="mapa_campana", n=2, total=TOTAL)


# ------------------------------------------------------------------ resumen --
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
    return f'<div class="vs-columnas" style="--cols:5; margin-bottom:56px">{columnas}</div>'


def _portada_campana(motor: Motor, resultados, es_demo: bool) -> str:
    tabla = tabla_resultados(resultados)
    sin_leer = int((tabla["Prioridad"] == SIN_ANALIZAR).sum())
    aviso = (f" {sin_leer} no se pudo leer y queda marcada." if sin_leer == 1 else
             f" {sin_leer} no se pudieron leer y quedan marcadas." if sin_leer else "")
    origen = ("Estas son las <b>muestras de demostración</b>: variantes de toxinas del NEA, "
              "toxinas de otras regiones del mundo y una lectura con errores."
              if es_demo else "Estas son las muestras del archivo que subiste.")

    bloque(f"""
    {cabeza(1, TOTAL, "La campaña", "La campa[ñ]a|ent[e]ra")}
    <div class="vs-esquina" style="margin-bottom:64px">
      <div class="vs-chico">{len(tabla)} muestras analizadas y ordenadas para saber
      {marca("cuáles mirar primero")}.{aviso}</div>
      <div class="vs-chico">{origen} Para ver una en detalle,
      <b>marcá la casilla</b> que está
      al principio de su fila.</div>
    </div>
    {_resumen(tabla, resultados)}
    """)
    elegida = _lista(tabla)
    with st.container(key="franja_umbral_campana"):
        bloque(subtitulo(2, "Ajustar la sensibilidad"))
        control_umbral(motor, "umbral_campana")
    _cargar_otra(motor)
    return elegida


# -------------------------------------------------------------------- lista --
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

    # La fila clickeada. Si no hay ninguna, se muestra la primera: la pantalla
    # nunca arranca a medias. AppTest no simula la selección, de ahí el getattr.
    filas = getattr(getattr(seleccion, "selection", None), "rows", []) or []
    return tabla.loc[filas[0] if filas else 0, "Muestra"]


# ------------------------------------------------------------ cargar la tuya --
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
            if st.session_state.get("resultados_campana"):
                if st.button("Volver a la campaña de prueba"):
                    del st.session_state["resultados_campana"]
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
                st.session_state["resultados_campana"] = motor.analizar(entradas)
            st.rerun()
