"""VenomScope: interfaz para el laboratorio.

Correr con:  .venv/bin/streamlit run app.py
"""
import pandas as pd
import streamlit as st

from venomscope import prioridad
from venomscope.analisis import ARTIFACTS, SIN_ANALIZAR, Motor, reevaluar, tabla_resultados
from venomscope.ejemplos import EJEMPLOS
from venomscope.iconos import con_icono, icono
from venomscope.lectura import leer_archivo, leer_fasta
from venomscope.mapa import figura_3d
from venomscope.novedad import NIVEL_MEDIA, NIVEL_NOVEDOSA

st.set_page_config(page_title="VenomScope", page_icon="🧪", layout="wide")

COLOR_PRIORIDAD = {prioridad.ALTA: "red", prioridad.MEDIA: "orange", prioridad.BAJA: "green",
                   SIN_ANALIZAR: "gray"}
OPCIONES_NEA = {"Sí": True, "No": False, "No sé": None}


@st.cache_resource(show_spinner="Cargando el modelo (solo la primera vez)...")
def obtener_motor() -> Motor:
    motor = Motor()
    motor.analizar([("calentamiento", "ACDEFGHIK", None)])   # deja ESM-2 cargado en memoria
    return motor


def etiqueta(nivel: str) -> str:
    return f":{COLOR_PRIORIDAD[nivel]}-background[**{nivel}**]"


def control_umbral(motor: Motor, clave: str) -> dict:
    """El control para mover el corte de 'novedosa', con su consecuencia explicada.

    Mover esto NO recalcula los embeddings: solo cambia a partir de qué puntaje
    llamamos novedosa a una secuencia, así que es instantáneo.
    """
    curva = motor.config["novedad"]["curva_umbrales"]
    por_defecto = motor.config["novedad"]["umbrales_puntaje"]["alto"]
    n_res = motor.config.get("n_reservadas", 66)

    c1, c2 = st.columns([2, 3])
    with c1:
        valor = st.slider("Marcar como novedosa a partir de", 80, 99, por_defecto, key=clave,
                          help="Más bajo = marca más candidatos, pero también más falsas alarmas.")
    with c2:
        detecta = curva.get(str(valor), 0.0)
        st.markdown(f"**Con el corte en {valor}:**")
        st.markdown(
            f"- Encuentra **{detecta:.0%}** de las toxinas de familias que el sistema nunca vio "
            f"(probado con las {n_res} que reservamos).\n"
            f"- A cambio, marca como novedosas **{100 - valor}%** de las toxinas que en realidad "
            "ya son conocidas: falsas alarmas."
        )
    return {**motor.config["novedad"]["umbrales_puntaje"], "alto": valor}


# ------------------------------------------------------------- detalle ----
def mostrar_detalle(r, motor: Motor = None, mapa: bool = True):
    if not r.validacion.es_valida:
        st.error("**No se pudo analizar esta secuencia.**\n\n" + "\n\n".join(r.validacion.errores))
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Prioridad de investigación**")
        st.markdown(f"## {etiqueta(r.prioridad.nivel)}")
    with c2:
        st.markdown("**Familia probable**")
        st.markdown(f"#### {r.prediccion.familia}")
        st.caption(f"Confianza del sistema: {r.prediccion.confianza:.0%}")
    with c3:
        st.markdown("**Novedad respecto del catálogo**")
        st.markdown(f"## {r.novedad.puntaje:.0f}/100")
        st.caption(r.novedad.nivel)

    st.markdown("**Por qué esta prioridad**")
    st.markdown("\n".join(f"- {razon}" for razon in r.prioridad.razones))

    for aviso in r.advertencias:
        st.warning(aviso, icon="⚠️")

    vecino = r.vecinos.iloc[0]
    st.markdown(f"**Se parece sobre todo a una toxina de {con_icono(vecino['grupo'])}**, "
                f"{vecino['nombre_proteina'].split(' (')[0]} de *{vecino['especie']}*.")
    if vecino["distancia"] < 1e-4:
        explicacion = (f"Esta secuencia **ya está en el catálogo**: es {vecino['nombre_proteina'].split(' (')[0]} "
                       f"de *{vecino['especie']}* ({vecino['accession']}).")
    elif r.novedad.nivel == NIVEL_NOVEDOSA:
        explicacion = (f"Está más lejos de lo conocido que el {r.novedad.puntaje:.0f}% de las toxinas del "
                       "catálogo respecto de su pariente más cercano. **No se parece a nada que tengamos**: "
                       "la familia sugerida es solo la menos lejana, tomarla con cuidado.")
    elif r.novedad.nivel == NIVEL_MEDIA:
        explicacion = (f"Está más lejos de lo conocido que el {r.novedad.puntaje:.0f}% de las toxinas del "
                       "catálogo. Se parece a familias conocidas, pero con diferencias notables.")
    else:
        explicacion = ("Se parece mucho a toxinas que ya están en el catálogo: probablemente sea una "
                       "variante de algo ya estudiado.")
    st.info(explicacion, icon="🧭")

    st.markdown("**Las 5 toxinas del catálogo más parecidas**")
    vecinos = r.vecinos.assign(
        grupo=[con_icono(g) for g in r.vecinos["grupo"]],
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
            "en_nea": st.column_config.TextColumn("Especie del NEA", width="small"),
            "parecido": st.column_config.ProgressColumn("Parecido", min_value=0, max_value=100,
                                                        format="%.0f"),
            "enlace": st.column_config.LinkColumn("UniProt", display_text="ver ficha"),
        },
    )

    if mapa and r.punto3d is not None:
        st.markdown("**Dónde cae en el mapa del catálogo**")
        st.plotly_chart(figura_3d(motor, r), width="stretch",
                        config={"displayModeBar": False})
        st.caption(
            f"Se puede girar con el mouse y acercar con la rueda. Cada punto es una toxina del "
            f"catálogo; pasá el mouse para ver cuál es. El mapa aplasta los "
            f"{motor.config['dim']} números de cada secuencia a 3 para poder dibujarlos, y en el "
            f"camino conserva el {motor.config['mapa3d']['varianza_conservada']:.0%} de la "
            "información: **la posición es orientativa**. El puntaje escrito al lado del rombo y "
            "las líneas hacia las toxinas más parecidas sí salen del cálculo completo."
        )


# ---------------------------------------------------------- barra lateral ----
def barra_lateral(motor: Motor):
    with st.sidebar:
        st.markdown("### Cómo funciona")
        st.markdown(
            "1. **Revisa** que la secuencia sea válida.\n"
            "2. **La traduce a números** con ESM-2, un modelo entrenado con millones de proteínas.\n"
            "3. **La compara** con el catálogo regional: familia más probable y qué tan novedosa es.\n"
            "4. **Asigna una prioridad** con reglas explícitas, siempre explicadas."
        )
        cat = motor.catalogo
        st.markdown("### El catálogo")
        st.markdown(f"- **{len(cat)}** toxinas de **{cat['genero_consultado'].nunique()}** géneros\n"
                    f"- **{cat.loc[cat['clase_modelable'], 'clase'].nunique()}** familias proteicas\n"
                    f"- Fuente: UniProt / Swiss-Prot (revisadas a mano)")
        m = motor.config.get("metricas", {})
        if m:
            st.markdown("### Qué tan bien anda")
            st.markdown(
                f"- Puntaje al identificar la familia: **{m['macro_f1_esm2'] * 100:.0f}/100** "
                f"(sin IA: {m['macro_f1_composicion'] * 100:.0f}/100).\n"
                f"- Marca como al menos *algo distinta* el **{m['reservadas_nivel_medio_o_alto']:.0%}** "
                "de las toxinas de familias que nunca vio."
            )
        st.caption("Funciona sin internet. Es una herramienta de apoyo: la decisión final es del laboratorio.")


# --------------------------------------------------------------- pestañas ----
def cargar_ejemplo():
    ejemplo = EJEMPLOS[st.session_state["ejemplo"]]
    st.session_state["secuencia"] = ejemplo["secuencia"]
    st.session_state["nea_una"] = ejemplo["nea"]


def pestana_una(motor: Motor):
    st.markdown("Pegá una secuencia de aminoácidos (por ejemplo `MKTLLLTLVVV...`). "
                "También se acepta en formato FASTA.")
    c1, c2 = st.columns([3, 1])
    with c2:
        st.selectbox("Probar con un ejemplo", list(EJEMPLOS), index=None, key="ejemplo",
                     placeholder="Elegí un ejemplo", on_change=cargar_ejemplo)
        st.radio("¿La muestra es de una especie del NEA?", list(OPCIONES_NEA), index=2,
                 key="nea_una", horizontal=True)
        if st.session_state.get("ejemplo"):
            st.caption(EJEMPLOS[st.session_state["ejemplo"]]["nota"])
    with c1:
        texto = st.text_area("Secuencia", height=140, key="secuencia", label_visibility="collapsed",
                             placeholder="MKTLLLTLVVVTIVCLDLGYT...")

    if st.button("Analizar", type="primary", disabled=not texto.strip()):
        entradas = leer_fasta(texto, OPCIONES_NEA[st.session_state["nea_una"]])
        if len(entradas) > 1:
            st.info(f"Se encontraron {len(entradas)} secuencias: se analiza la primera. "
                    "Para varias, usá la pestaña *Analizar una campaña*.")
        with st.spinner("Analizando..."):
            st.session_state["resultado_una"] = motor.analizar(entradas[:1])[0]

    if "resultado_una" in st.session_state:
        st.divider()
        resultado = st.session_state["resultado_una"]
        if resultado.validacion.es_valida:
            reevaluar([resultado], control_umbral(motor, "umbral_una"))
            st.divider()
        mostrar_detalle(resultado, motor)


def pestana_campana(motor: Motor):
    st.markdown(
        "Subí todas las secuencias de una campaña de muestreo y el sistema las ordena por prioridad. "
        "Formatos: **FASTA** (`.fasta`, `.fa`, `.txt`) o **CSV** con una columna `secuencia` "
        "(opcionales: `nombre` y `nea` con sí/no)."
    )
    c1, c2 = st.columns([3, 1])
    with c1:
        archivo = st.file_uploader("Archivo de la campaña", type=["fasta", "fa", "faa", "txt", "csv", "tsv"])
    with c2:
        nea = st.radio("¿Las muestras son de especies del NEA?", list(OPCIONES_NEA), index=2,
                       key="nea_campana",
                       help="Se aplica a todas, salvo que el CSV traiga una columna 'nea'.")
        usar_demo = st.toggle("Usar la campaña de demostración",
                              help="11 muestras simuladas: variantes de toxinas del NEA, "
                                   "toxinas de otras regiones y una lectura con errores.")

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
            resultados = motor.analizar(entradas)
        st.session_state["resultados_campana"] = resultados

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
            "Confianza": st.column_config.NumberColumn(format="percent"),
            "Novedad (0-100)": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
            "Motivo": st.column_config.TextColumn(width="large"),
            "Avisos": st.column_config.TextColumn(width="large"),
        },
    )
    st.download_button("Descargar resultados (CSV)",
                       tabla.to_csv(index=False).encode("utf-8-sig"),   # utf-8-sig: Excel lee bien las tildes
                       file_name="venomscope_resultados.csv", mime="text/csv")

    st.markdown("#### Ver el detalle de una muestra")
    por_id = {r.id: r for r in resultados}
    elegida = st.selectbox("Muestra", tabla["Muestra"], label_visibility="collapsed")
    mostrar_detalle(por_id[elegida], motor)


def pestana_ayuda(motor: Motor):
    u = motor.config["novedad"]["umbrales_puntaje"]
    st.markdown(f"""
#### Familia probable
A qué grupo de toxinas conocidas se parece más, según su función. La **confianza** es qué tan
seguro está el sistema; por debajo de {motor.config['clasificador']['umbral_confianza']:.0%} se avisa.
El sistema siempre elige alguna familia conocida, aunque la secuencia no se parezca a ninguna:
por eso hay que mirarla junto con la novedad.

#### Novedad (0 a 100)
Qué tan lejos está de la toxina más parecida del catálogo, comparado con lo que es normal entre
toxinas conocidas. Un 97 significa: *está más lejos de lo conocido que el 97% de las toxinas del
catálogo respecto de su pariente más cercano*.
- **Parecida a algo conocido** (menos de {u['medio']}): probablemente una variante de algo ya estudiado.
- **Algo distinta** ({u['medio']} a {u['alto']}): pariente lejano de familias conocidas.
- **Novedosa** ({u['alto']} o más): no se parece a nada del catálogo.

#### Prioridad
Se calcula con reglas fijas, no con IA, para que siempre se pueda explicar:
- **Alta**: es novedosa, o algo distinta y de una especie del NEA.
- **Media**: es algo distinta, o el sistema no está seguro de la familia.
- **Baja**: se parece mucho a toxinas ya estudiadas.

#### Por qué preferimos marcar de más

El control para mover el corte de "novedosa" no tiene una posición correcta. Bajarlo encuentra
más candidatos pero genera más falsas alarmas; subirlo hace lo contrario. Lo que decide no es
la técnica, es **cuánto cuesta cada error**, y acá no cuestan lo mismo:

- **Falsa alarma:** un investigador mira una secuencia y en diez minutos la descarta.
- **Novedad perdida:** el candidato que no se parecía a nada queda enterrado en una planilla
  que nadie vuelve a abrir.

Hay un caso que lo muestra mejor que cualquier argumento. El **captopril**, uno de los
antihipertensivos más vendidos de la historia, salió de un péptido de **nueve aminoácidos**
del veneno de *Bothrops jararaca*, una yarará que está en nuestro propio catálogo.

Un filtro que descartara las secuencias cortas por considerarlas basura —que es exactamente lo
que íbamos a hacer al principio de este trabajo— habría tirado esa molécula sin que nadie se
enterara. Por eso el corte viene en **{u['alto']}** y no más arriba: preferimos que el
laboratorio descarte diez candidatos de más antes que perder uno.

#### Limitaciones
- El catálogo refleja lo que **ya se publicó**: las especies poco estudiadas tienen pocas secuencias,
  así que sus toxinas pueden parecer más novedosas de lo que son.
- El **mapa 3D** conserva el {motor.config['mapa3d']['varianza_conservada']:.0%} de la información,
  así que la posición de un punto es orientativa. El puntaje y las líneas a las toxinas más
  parecidas sí salen del cálculo completo.
- En los **péptidos cortos** (menos de 20 aminoácidos) no pudimos verificar qué tan confiable es
  el resultado: los que tenemos en el catálogo son casi todos de una misma familia fácil de
  reconocer, así que no sabemos cómo se comporta con uno de una familia desconocida.
- Es una herramienta para **ordenar y priorizar**, no reemplaza el análisis de laboratorio.
""")


# ------------------------------------------------------------------ main ----
st.title("🧪 VenomScope")
st.markdown("**Qué péptidos de la fauna del noreste argentino vale la pena investigar.** "
            "Cargá una secuencia y en segundos ves a qué familia se parece, qué tan novedosa es "
            "y qué prioridad merece.")

try:
    motor = obtener_motor()
except FileNotFoundError:
    st.error("Faltan los archivos del modelo en `artifacts/`. Generarlos con:\n\n"
             "`.venv/bin/python scripts/construir_artefactos.py`")
    st.stop()

barra_lateral(motor)
una, campana, ayuda = st.tabs(["Analizar una secuencia", "Analizar una campaña", "Cómo leer los resultados"])
with una:
    pestana_una(motor)
with campana:
    pestana_campana(motor)
with ayuda:
    pestana_ayuda(motor)
