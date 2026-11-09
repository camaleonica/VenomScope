"""Pestaña "Qué es esto": la introducción para quien no sabe biología."""
import streamlit as st

from interfaz import componentes
from interfaz.estilo import mostrar_html
from venomscope.analisis import Motor


PASOS = [
    {"titulo": "Revisar", "tipo": "reglas",
     "texto": "Chequea que la secuencia use solo las 20 letras válidas y tenga un largo "
              "razonable. Si no, avisa en vez de inventar un resultado."},
    {"titulo": "Traducir a números", "tipo": "ia",
     "texto": "Un modelo de lenguaje para proteínas, <strong>ESM-2</strong>, convierte la "
              "secuencia en un vector de {dim} números (un <em>embedding</em>)."},
    {"titulo": "Reconocer la familia", "tipo": "ia",
     "texto": "Un clasificador entrenado con el catálogo mira ese vector y dice "
              "a qué familia se parece y con cuánta seguridad."},
    {"titulo": "Medir la novedad", "tipo": "ia",
     "texto": "Busca los cinco <strong>vecinos</strong> más cercanos del catálogo. Si están "
              "lejos, la secuencia es rara: puntaje de novedad alto."},
    {"titulo": "Decidir la prioridad", "tipo": "reglas",
     "texto": "<strong>Reglas</strong> fijas y escritas, sin IA, combinan novedad, "
              "seguridad y origen. Siempre se puede explicar el porqué."},
]


def mostrar(motor: Motor):
    cat = motor.catalogo
    m = motor.config.get("metricas", {})
    n_familias = cat.loc[cat["clase_modelable"], "clase"].nunique()

    st.markdown("### Del veneno al remedio: a cuál le apostamos")
    st.markdown(
        "Los venenos de serpientes, arañas, escorpiones, ranas e insectos están llenos de "
        "moléculas que la evolución afinó durante millones de años para actuar sobre el "
        "cuerpo con mucha precisión. Por eso son una de las fuentes de **medicamentos nuevos** "
        "más prometedoras que hay.\n\n"
        "El problema es elegir. Una campaña de muestreo en el noreste argentino deja decenas o "
        "cientos de secuencias, y estudiar cada una en el laboratorio lleva meses. Hoy se elige "
        "a ojo, y la que no se parecía a nada conocido, que suele ser la más interesante, queda "
        "olvidada en una planilla. **VenomScope ordena la campaña en segundos y dice cuáles "
        "mirar primero.**")

    st.divider()
    st.markdown("### La biología en un minuto")
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.markdown(
            "**Una proteína es un texto.** Se escribe con un alfabeto de 20 letras, los "
            "**aminoácidos**: por ejemplo `QWPRPQIPP`. Las toxinas son proteínas, y las "
            "cortas se llaman **péptidos**. Para el sistema, cada una es un *string*.")
    with c2:
        st.markdown(
            "**Las proteínas vienen en familias.** Las que hacen cosas parecidas se parecen "
            "entre sí, como clases que heredan del mismo padre. Saber la **familia** de una "
            "toxina da una primera idea de qué hace, sin pisar el laboratorio.")
    with c3:
        st.markdown(
            "**Por qué importa.** El **captopril**, un antihipertensivo de los más vendidos de "
            "la historia, salió de un péptido de nueve aminoácidos del veneno de la yarará, "
            "una serpiente que está en nuestro catálogo.")

    st.divider()
    st.markdown("### Cómo funciona")
    st.markdown("Cada secuencia pasa por cinco pasos. Los del medio usan inteligencia "
                "artificial; el primero y el último son reglas, a propósito.")
    mostrar_html(componentes.pasos(
        [{**paso, "texto": paso["texto"].format(dim=motor.config["dim"])} for paso in PASOS]))

    with st.expander("La misma idea, en términos de informática"):
        st.markdown(
            "- **ESM-2** es un modelo de lenguaje como los que usan los chatbots, pero entrenado "
            "con millones de proteínas en vez de texto. Igual que los *word embeddings* ponen "
            "cerca palabras con significado parecido, ESM-2 pone cerca proteínas que funcionan "
            "parecido, aunque las letras sean distintas.\n"
            "- **El clasificador** es una regresión logística sobre esos vectores. Es simple a "
            "propósito: con pocos ejemplos por familia, un modelo grande memoriza en vez de "
            "aprender.\n"
            "- **La novedad** es detección de anomalías por vecinos más cercanos (k-NN), como "
            "detectar una compra con tarjeta que no se parece a ninguna habitual.\n"
            "- **La prioridad** es un `if / else` explícito. El clasificador siempre elige "
            "alguna familia, aunque la secuencia no se parezca a ninguna (un `switch` sin "
            "`default`): la novedad es la que avisa cuando eso pasa, y las reglas juntan las "
            "dos cosas de forma auditable.\n"
            "- Todo corre en una notebook común, **sin internet y sin placa de video**.")

    st.divider()
    st.markdown("### Con qué compara")
    st.markdown(
        f"Con un **catálogo regional** de {len(cat)} toxinas de {cat['genero_consultado'].nunique()} "
        f"géneros de animales del noreste argentino, agrupadas en {n_familias} familias, "
        "descargadas de UniProt, la base pública de proteínas más usada del mundo.")

    if m:
        st.markdown("### Qué tan bien anda")
        c1, c2, c3 = st.columns(3)
        c1.metric("Familia, examen normal", f"{m['macro_f1_esm2'] * 100:.0f}/100",
                  f"sin IA: {m['macro_f1_composicion'] * 100:.0f}", delta_color="off", delta_arrow="off")
        c2.metric("Familia, examen difícil", f"{m['macro_f1_esm2_agrupado'] * 100:.0f}/100",
                  f"sin IA: {m['macro_f1_composicion_agrupado'] * 100:.0f}", delta_color="off", delta_arrow="off")
        c3.metric("Avisa de familias nunca vistas", f"{m['reservadas_nivel_alto']:.0%}",
                  "con el corte en 90", delta_color="off", delta_arrow="off")
        st.caption(
            "\"Sin IA\" es el mismo clasificador contando cuántas veces aparece cada letra: lo "
            "que se conseguía sin el modelo de lenguaje. El examen difícil separa las "
            "secuencias casi idénticas, así el sistema no puede aprobar de memoria; es el "
            "número realista. Para la última medición escondimos a propósito toxinas de "
            "familias que el sistema nunca vio y medimos cuántas marca como novedosas.")

    st.divider()
    st.markdown("### Probalo")
    st.markdown(
        "Andá a la pestaña **Una secuencia** y elegí un ejemplo de la lista: hay una toxina "
        "que ya conocemos, una de otra parte del mundo que el sistema no vio nunca y una "
        "secuencia con errores. En **Una campaña entera** está el caso real: muchas "
        "secuencias de golpe, ordenadas por prioridad. El sistema **ayuda a priorizar**; "
        "la decisión sigue siendo del laboratorio.")
