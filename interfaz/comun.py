"""Lo que usan varias pantallas: el motor, el control de sensibilidad y la barra lateral."""
import streamlit as st

from venomscope.analisis import ARTIFACTS, Motor
from venomscope.lectura import leer_archivo


OPCIONES_NEA = {"Sí": True, "No": False, "No sé": None}


@st.cache_resource(show_spinner="Preparando el modelo (solo la primera vez)...")
def obtener_motor() -> Motor:
    return Motor()


@st.cache_resource(show_spinner="Analizando la campaña de demostración...")
def campana_demo(_motor: Motor) -> list:
    """La campaña de prueba, analizada una sola vez por sesión.

    Es lo que ve el usuario al abrir la app, así que no se le pide que cargue
    nada para entender el producto. De paso deja ESM-2 cargado en memoria, así
    la primera consulta propia ya sale instantánea.
    """
    ruta = ARTIFACTS.parent / "ejemplos" / "campana_demo.csv"
    return _motor.analizar(leer_archivo(ruta.name, ruta.read_bytes(), None))


def umbrales_elegidos(motor: Motor, clave: str) -> dict:
    """Los umbrales vigentes, sin dibujar nada.

    Sirve para calcular una tabla ANTES de dibujar el deslizante que la controla:
    el valor ya está en el estado de la sesión desde la última vez que se movió.
    """
    umbrales = motor.config["novedad"]["umbrales_puntaje"]
    return {**umbrales, "alto": st.session_state.get(clave, umbrales["alto"])}


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
                    "**Identificar la familia**, en puntos sobre 100:\n\n"
                    f"| | con IA | sin IA |\n|---|---|---|\n"
                    f"| examen normal | **{m['macro_f1_esm2'] * 100:.0f}** | "
                    f"{m['macro_f1_composicion'] * 100:.0f} |\n"
                    f"| examen difícil | **{m['macro_f1_esm2_agrupado'] * 100:.0f}** | "
                    f"{m['macro_f1_composicion_agrupado'] * 100:.0f} |\n\n"
                    "El examen difícil separa las secuencias casi idénticas, así que el "
                    "sistema no puede aprobar de memoria. Es el número realista, y ahí la "
                    "ventaja de la IA se agranda.\n\n"
                    f"**Avisar de lo desconocido:** de las toxinas de familias que nunca vio, "
                    f"marca el **{m['reservadas_nivel_medio_o_alto']:.0%}**."
                )
        st.caption("Anda sin internet. Es una ayuda para priorizar: la decisión es del laboratorio.")
