"""VenomScope: interfaz para el laboratorio.

Correr con:  .venv/bin/streamlit run app.py

Criterio de la pantalla: primero la respuesta, después el porqué. Todo lo que es
explicación larga va en un desplegable, para que quien ya sabe leer el resultado
no tenga que atravesarla.
"""
import streamlit as st

from venomscope import prioridad
from venomscope.analisis import ARTIFACTS, SIN_ANALIZAR, Motor, reevaluar, tabla_resultados
from venomscope.ejemplos import EJEMPLOS
from venomscope.grupos import nombre as nombre_grupo
from venomscope.lectura import leer_archivo, leer_fasta
from venomscope.mapa import figura_3d
from venomscope.novedad import NIVEL_MEDIA, NIVEL_NOVEDOSA

st.set_page_config(page_title="VenomScope", layout="wide")

COLOR_PRIORIDAD = {prioridad.ALTA: "red", prioridad.MEDIA: "orange", prioridad.BAJA: "green",
                   SIN_ANALIZAR: "gray"}
OPCIONES_NEA = {"Sí": True, "No": False, "No sé": None}


@st.cache_resource(show_spinner="Preparando el modelo (solo la primera vez)...")
def obtener_motor() -> Motor:
    motor = Motor()
    motor.analizar([("calentamiento", "ACDEFGHIK", None)])   # deja ESM-2 cargado en memoria
    return motor


def control_umbral(motor: Motor, clave: str) -> dict:
    """Corre el corte de 'novedosa'. No recalcula embeddings: es instantáneo."""
    curva = motor.config["novedad"]["curva_umbrales"]
    por_defecto = motor.config["novedad"]["umbrales_puntaje"]["alto"]

    c1, c2 = st.columns([2, 3], vertical_alignment="center")
    with c1:
        valor = st.slider("Sensibilidad: avisar desde", 80, 99, por_defecto, key=clave,
                          help="Más bajo, más candidatos marcados y más falsas alarmas.")
    with c2:
        encuentra = round(curva.get(str(valor), 0.0) * 100)
        st.markdown(f"De cada 100 toxinas realmente nuevas, encuentra **{encuentra}**. "
                    f"De cada 100 ya conocidas, marca **{100 - valor}** por error.")
    return {**motor.config["novedad"]["umbrales_puntaje"], "alto": valor}


# ------------------------------------------------------------- resultado ----
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


def mostrar_resultado(r, motor: Motor, clave: str = "mapa"):
    if not r.validacion.es_valida:
        st.error("**No se pudo analizar esta secuencia.**\n\n" + "\n\n".join(r.validacion.errores))
        return

    c1, c2, c3 = st.columns(3)
    c1.markdown("Prioridad")
    c1.markdown(f"# :{COLOR_PRIORIDAD[r.prioridad.nivel]}[{r.prioridad.nivel}]")
    c2.metric("Novedad", f"{r.novedad.puntaje:.0f}/100", r.novedad.nivel, delta_color="off")
    c3.metric("Seguridad de la familia", f"{r.prediccion.confianza:.0%}",
              "baja" if r.prediccion.baja_confianza else "suficiente", delta_color="off")

    st.markdown(_veredicto(r))
    st.markdown(f"**Familia probable:** {r.prediccion.familia}")

    for aviso in r.advertencias:
        st.warning(aviso)

    with st.expander("Por qué le dio esta prioridad"):
        st.markdown("\n".join(f"- {razon}" for razon in r.prioridad.razones))

    st.markdown("##### Las cinco toxinas del catálogo más parecidas")
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


# ---------------------------------------------------------- barra lateral ----
def barra_lateral(motor: Motor):
    cat = motor.catalogo
    m = motor.config.get("metricas", {})
    with st.sidebar:
        st.markdown("### VenomScope")
        st.markdown("Compara un péptido contra las toxinas del noreste argentino y dice "
                    "a qué se parece, qué tan nuevo es y si conviene investigarlo.")
        st.markdown(f"**Catálogo:** {len(cat)} toxinas de "
                    f"{cat['genero_consultado'].nunique()} géneros, "
                    f"{cat.loc[cat['clase_modelable'], 'clase'].nunique()} familias. "
                    "Fuente: UniProt.")
        if m:
            with st.expander("Qué tan bien anda"):
                st.markdown(
                    f"- Identifica la familia con un puntaje de "
                    f"**{m['macro_f1_esm2'] * 100:.0f} sobre 100**. Sin IA, el mismo método "
                    f"llega a {m['macro_f1_composicion'] * 100:.0f}.\n"
                    f"- De las toxinas de familias que nunca vio, avisa por el "
                    f"**{m['reservadas_nivel_medio_o_alto']:.0%}**.\n"
                    "- Los dos números están medidos con exámenes que el modelo no vio. "
                    "El detalle está en el Notebook 2."
                )
        st.caption("Anda sin internet. Es una ayuda para priorizar: la decisión es del laboratorio.")


# --------------------------------------------------------------- pestañas ----
def cargar_ejemplo():
    ejemplo = EJEMPLOS[st.session_state["ejemplo"]]
    st.session_state["secuencia"] = ejemplo["secuencia"]
    st.session_state["nea_una"] = ejemplo["nea"]


def pestana_una(motor: Motor):
    c1, c2 = st.columns([3, 1])
    with c1:
        texto = st.text_area("Secuencia", height=150, key="secuencia",
                             placeholder="Pegá una secuencia de aminoácidos: MKTLLLTLVVVTIVCLDLGYT...")
    with c2:
        st.selectbox("O probá con un ejemplo", list(EJEMPLOS), index=None, key="ejemplo",
                     placeholder="Elegí uno", on_change=cargar_ejemplo)
        st.radio("¿Es de una especie del NEA?", list(OPCIONES_NEA), index=2,
                 key="nea_una", horizontal=True)
    if st.session_state.get("ejemplo"):
        st.caption(EJEMPLOS[st.session_state["ejemplo"]]["nota"])

    if st.button("Analizar", type="primary", disabled=not texto.strip()):
        entradas = leer_fasta(texto, OPCIONES_NEA[st.session_state["nea_una"]])
        if len(entradas) > 1:
            st.info(f"Hay {len(entradas)} secuencias y se analiza la primera. "
                    "Para varias, usá la otra pestaña.")
        with st.spinner("Analizando..."):
            st.session_state["resultado_una"] = motor.analizar(entradas[:1])[0]

    if "resultado_una" in st.session_state:
        st.divider()
        resultado = st.session_state["resultado_una"]
        if resultado.validacion.es_valida:
            reevaluar([resultado], control_umbral(motor, "umbral_una"))
            st.divider()
        mostrar_resultado(resultado, motor, clave="mapa_una")


def pestana_campana(motor: Motor):
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


def pestana_ayuda(motor: Motor):
    u = motor.config["novedad"]["umbrales_puntaje"]
    conf = motor.config["clasificador"]["umbral_confianza"]

    st.markdown("#### Los tres números de la pantalla")
    st.markdown(f"""
**Novedad (0 a 100).** Qué tan lejos está de lo más parecido que tenemos. Un 97 quiere decir:
*está más lejos de lo conocido que el 97% de las toxinas del catálogo*.

**Seguridad de la familia.** Qué tan convencido está el sistema. Por debajo de {conf:.0%} avisa.
Ojo: siempre elige alguna familia conocida, aunque la secuencia no se parezca a ninguna. Por eso
hay que mirarla junto con la novedad.

**Prioridad.** Sale de reglas fijas, no de la IA, para que siempre se pueda explicar: alta si es
novedosa o si es algo distinta y viene del NEA; media si es algo distinta o si el sistema duda de
la familia; baja si se parece mucho a algo ya estudiado.
""")

    with st.expander("Por qué conviene marcar de más"):
        st.markdown("""
La sensibilidad no tiene una posición correcta. Bajarla encuentra más candidatos y genera más
falsas alarmas; subirla hace lo contrario. Lo que decide no es la técnica, es **cuánto cuesta
cada error**, y acá no cuestan lo mismo:

- **Falsa alarma:** alguien mira una secuencia y en diez minutos la descarta.
- **Novedad perdida:** el candidato que no se parecía a nada queda enterrado en una planilla.

Hay un caso que lo muestra mejor que cualquier argumento. El **captopril**, uno de los
antihipertensivos más vendidos de la historia, salió de un péptido de **nueve aminoácidos** del
veneno de *Bothrops jararaca*, una yarará que está en nuestro propio catálogo.

Un filtro que descartara las secuencias cortas por considerarlas basura, que es exactamente lo
que íbamos a hacer al principio de este trabajo, habría tirado esa molécula sin que nadie se
enterara.
""")

    with st.expander("Qué no puede hacer"):
        st.markdown(f"""
- El catálogo tiene lo que **ya se publicó**. Una especie poco estudiada va a parecer más
  novedosa de lo que es, simplemente porque hay menos con qué compararla.
- El **mapa** conserva el {motor.config['mapa3d']['varianza_conservada']:.0%} de la información,
  así que la posición de un punto es orientativa. El puntaje y las líneas sí salen del cálculo
  completo.
- En los **péptidos cortos** no pudimos comprobar qué tan confiable es: los que tenemos son casi
  todos de una misma familia fácil, así que no sabemos cómo se porta con uno de otra.
- Sirve para **ordenar y priorizar**. No reemplaza el análisis de laboratorio.
""")

    with st.expander("Cómo funciona por dentro"):
        st.markdown(f"""
1. Revisa que la secuencia sea válida: los 20 aminoácidos estándar, entre 5 y 600 de largo.
2. La traduce a {motor.config['dim']} números con ESM-2, un modelo entrenado con millones de
   proteínas. Secuencias que hacen cosas parecidas quedan cerca, aunque se escriban distinto.
3. La compara con las {motor.config['n_catalogo']} toxinas del catálogo: de ahí salen la familia
   probable y el puntaje de novedad.
4. Aplica las reglas de prioridad, que están escritas y se pueden discutir.

Los cortes de novedad están en {u['medio']} y {u['alto']}, y el de arriba se mueve con el control
de sensibilidad.
""")


# ------------------------------------------------------------------ main ----
st.title("VenomScope")
st.markdown("Qué péptidos de la fauna del noreste argentino vale la pena investigar.")

try:
    motor = obtener_motor()
except FileNotFoundError:
    st.error("Faltan los archivos del modelo en `artifacts/`. Generalos con:\n\n"
             "`.venv/bin/python scripts/construir_artefactos.py`")
    st.stop()

barra_lateral(motor)
una, campana, ayuda = st.tabs(["Una secuencia", "Una campaña entera", "Cómo leer esto"])
with una:
    pestana_una(motor)
with campana:
    pestana_campana(motor)
with ayuda:
    pestana_ayuda(motor)
