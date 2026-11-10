"""Pestaña "Cómo leer esto": qué significa cada número y qué no puede hacer el sistema."""
import streamlit as st

from interfaz import componentes
from interfaz.estilo import mostrar_html
from venomscope.analisis import Motor


def mostrar(motor: Motor):
    u = motor.config["novedad"]["umbrales_puntaje"]
    conf = motor.config["clasificador"]["umbral_confianza"]

    st.markdown("#### Los tres números de la pantalla")
    st.markdown("Así se ve la escala de novedad con una secuencia que sacó 97:")
    mostrar_html(componentes.escala_novedad(97, u))

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1.container(border=True, height="stretch"):
        st.markdown("**Novedad (0 a 100)**")
        st.markdown(f"""
Qué tan lejos está de lo más parecido que tenemos. Un 97 quiere decir:
*está más lejos de lo conocido que el 97% de las toxinas del catálogo*. Desde {u['medio']} se
considera "algo distinta" y desde {u['alto']} "novedosa"; ese último corte se mueve con el control
de sensibilidad.
""")
    with c2.container(border=True, height="stretch"):
        st.markdown("**Seguridad de la familia**")
        st.markdown(f"""
Qué tan convencido está el sistema. Por debajo de {conf:.0%} avisa. Ojo: siempre elige alguna
familia conocida, aunque la secuencia no se parezca a ninguna. Por eso hay que mirarla junto con
la novedad.
""")
    with c3.container(border=True, height="stretch"):
        st.markdown("**Prioridad**")
        st.markdown("Sale de reglas fijas, no de la IA, para que siempre se pueda explicar:")
        mostrar_html(componentes.criterios([
            ("alta", "alta", "si es novedosa, o si es algo distinta y viene del NEA."),
            ("media", "media", "si es algo distinta, o si el sistema duda de la familia."),
            ("baja", "baja", "si se parece mucho a algo ya estudiado."),
        ]))

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
- En los **péptidos cortos** no pudimos comprobar qué tan confiable es: los del catálogo salen de
  solo cuatro familias, y siete de cada diez son parientes entre sí, así que no sabemos cómo se
  porta con uno de una familia distinta.
- Sirve para **ordenar y priorizar**. No reemplaza el análisis de laboratorio.
""")
