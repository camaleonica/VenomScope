"""Pestaña "Qué es esto": la introducción para quien no sabe biología.

Cinco secciones que alternan blanco y negro: el problema, la biología mínima,
cómo funciona, qué tan bien anda y cómo probarlo.
"""
import streamlit as st

from interfaz.editorial import bloque, foto, marca, marcador, numero, seccion, titulo
from venomscope.analisis import Motor

TOTAL = 5

PASOS = [
    ("Revisar", "regla",
     "Chequea que la secuencia use solo las 20 letras válidas y tenga un largo razonable. "
     "Si no, avisa en vez de inventar un resultado."),
    ("Traducir a números", "IA",
     "Un modelo de lenguaje para proteínas, <b>ESM-2</b>, convierte la secuencia en un vector "
     "de {dim} números: un <i>embedding</i>."),
    ("Reconocer la familia", "IA",
     "Un clasificador entrenado con el catálogo mira ese vector y dice a qué familia se parece "
     "y con cuánta seguridad."),
    ("Medir la novedad", "IA",
     "Busca los cinco <b>vecinos</b> más cercanos del catálogo. Si están lejos, la secuencia "
     "es rara: puntaje de novedad alto."),
    ("Decidir la prioridad", "regla",
     "<b>Reglas</b> fijas y escritas, sin IA, combinan novedad, seguridad y origen. Siempre se "
     "puede explicar el porqué."),
]


def _cabeza(n: int, nombre: str, texto_titulo: str) -> str:
    return f'<div class="vs-cabeza">{titulo(texto_titulo)}{marcador(n, TOTAL, nombre)}</div>'


def _portada(motor: Motor):
    cat = motor.catalogo
    n_familias = cat.loc[cat["clase_modelable"], "clase"].nunique()
    bloque(f"""
    <div class="vs-portada">
      <div class="vs-portada-texto">
        {titulo("V[e]nom|Sc[op]e", nivel=1, clase="vs-titulo vs-titulo--portada")}
        <div class="vs-esquina" style="justify-content:flex-start">
          <div class="vs-chico">Mira un péptido de veneno y dice a qué se parece, qué tan nuevo
            es y {marca("si vale la pena investigarlo")}.</div>
          <div class="vs-chico vs-mono">{len(cat)} toxinas<br>{cat['genero_consultado'].nunique()}
            géneros del NEA<br>{n_familias} familias<br>sin internet</div>
        </div>
      </div>
      <div>
        <div class="vs-marcador" style="margin-bottom:16px"><span>00 / {TOTAL:02d}</span>
          <span>Inicio</span></div>
        {foto("portada")}
      </div>
    </div>
    """)


def _problema():
    with seccion("problema"):
        bloque(f"""
        {_cabeza(1, "El problema", "Del ve[n]eno|al reme[d]io")}
        <div class="vs-esquina">
          <div class="vs-chico">{numero(1)}Los venenos de serpientes, arañas, escorpiones, ranas e
            insectos están llenos de moléculas que la evolución afinó durante millones de años
            para actuar sobre el cuerpo con mucha precisión. Por eso son una de las fuentes de
            <b>medicamentos nuevos</b> más prometedoras que hay.</div>
          <div class="vs-chico">{numero(2)}El problema es elegir. Una campaña de muestreo en el
            noreste argentino deja decenas o cientos de secuencias, y estudiar cada una lleva
            meses. Hoy se elige a ojo, y la que no se parecía a nada, que suele ser la más
            interesante, queda olvidada en una planilla.
            {marca("VenomScope ordena la campaña en segundos y dice cuáles mirar primero.")}</div>
        </div>
        """)


def _biologia():
    with seccion("biologia", oscura=True):
        bloque(f"""
        {_cabeza(2, "Biología", "La bio[l]ogía|en un mi[n]uto")}
        <div class="vs-con-foto">
          {foto("biologia")}
          <div class="vs-columnas" style="--cols:3">
            <div>{numero(1)}<p class="vs-item-titulo">Una proteína es un texto</p>
              <div class="vs-chico">Se escribe con un alfabeto de 20 letras, los
              <b>aminoácidos</b>: por ejemplo <code>QWPRPQIPP</code>. Las toxinas son proteínas,
              y las cortas se llaman <b>péptidos</b>. Para el sistema, cada una es un
              <i>string</i>.</div></div>
            <div>{numero(2)}<p class="vs-item-titulo">Vienen en familias</p>
              <div class="vs-chico">Las que hacen cosas parecidas se parecen entre sí, como clases
              que heredan del mismo padre. Saber la <b>familia</b> de una toxina da una primera
              idea de qué hace, sin pisar el laboratorio.</div></div>
            <div>{numero(3)}<p class="vs-item-titulo">Por qué importa</p>
              <div class="vs-chico">El <b>captopril</b>, un antihipertensivo de los más vendidos de
              la historia, salió de un péptido de nueve aminoácidos del veneno de la
              {marca("yarará")}, una serpiente que está en nuestro catálogo.</div></div>
          </div>
        </div>
        """)


def _como_funciona(motor: Motor):
    with seccion("sistema"):
        pasos = "".join(
            f'<div>{numero(i)}<p class="vs-item-titulo">{nombre}</p>'
            f'<p class="vs-etiqueta">{marca("IA") if tipo == "IA" else "Regla"}</p>'
            f'<div class="vs-chico">{texto.format(dim=motor.config["dim"])}</div></div>'
            for i, (nombre, tipo, texto) in enumerate(PASOS, start=1))
        bloque(f"""
        {_cabeza(3, "El sistema", "Cómo fu[n]ciona")}
        <div class="vs-esquina" style="margin-bottom:40px">
          <div class="vs-chico">Cada secuencia pasa por cinco pasos. Los del medio usan
          inteligencia artificial; el primero y el último son reglas, a propósito.</div>
        </div>
        <div class="vs-columnas" style="--cols:5">{pasos}</div>
        """)
        with st.expander("La misma idea, en términos de informática"):
            st.markdown(
                "- **ESM-2** es un modelo de lenguaje como los que usan los chatbots, pero "
                "entrenado con millones de proteínas en vez de texto. Igual que los *word "
                "embeddings* ponen cerca palabras con significado parecido, ESM-2 pone cerca "
                "proteínas que funcionan parecido, aunque las letras sean distintas.\n"
                "- **El clasificador** es una regresión logística sobre esos vectores. Es simple "
                "a propósito: con pocos ejemplos por familia, un modelo grande memoriza en vez de "
                "aprender.\n"
                "- **La novedad** es detección de anomalías por vecinos más cercanos (k-NN), como "
                "detectar una compra con tarjeta que no se parece a ninguna habitual.\n"
                "- **La prioridad** es un `if / else` explícito. El clasificador siempre elige "
                "alguna familia, aunque la secuencia no se parezca a ninguna (un `switch` sin "
                "`default`): la novedad es la que avisa cuando eso pasa, y las reglas juntan las "
                "dos cosas de forma auditable.\n"
                "- Todo corre en una notebook común, **sin internet y sin placa de video**.")


def _resultados(m: dict):
    with seccion("resultados", oscura=True):
        cifras = [
            (f"{m['macro_f1_esm2'] * 100:.0f}", "/100", "Familia, examen normal",
             f"Sin IA: {m['macro_f1_composicion'] * 100:.0f}."),
            (f"{m['macro_f1_esm2_agrupado'] * 100:.0f}", "/100", "Familia, examen difícil",
             f"Sin IA: {m['macro_f1_composicion_agrupado'] * 100:.0f}. Es el número realista."),
            (f"{m['reservadas_nivel_alto'] * 100:.0f}", "%", "Avisa de familias nunca vistas",
             "Con el corte de novedad en 90."),
        ]
        columnas = "".join(
            f'<div>{numero(i)}<p class="vs-cifra">{valor}<small>{unidad}</small></p>'
            f'<p class="vs-item-titulo">{nombre}</p><div class="vs-chico">{detalle}</div></div>'
            for i, (valor, unidad, nombre, detalle) in enumerate(cifras, start=1))
        bloque(f"""
        {_cabeza(4, "Resultados", "Qué tan|bien [a]nda")}
        <div class="vs-columnas" style="--cols:3; margin-bottom:56px">{columnas}</div>
        <div class="vs-esquina">
          <div class="vs-chico">"Sin IA" es el mismo clasificador contando cuántas veces aparece
          cada letra: lo que se conseguía sin el modelo de lenguaje.</div>
          <div class="vs-chico">El examen difícil separa las secuencias casi idénticas, así el
          sistema {marca("no puede aprobar de memoria")}.</div>
          <div class="vs-chico">Para la última medición escondimos a propósito toxinas de familias
          que el sistema nunca vio y medimos cuántas marca como novedosas.</div>
        </div>
        """)


def _probalo(motor: Motor):
    cat = motor.catalogo
    n_familias = cat.loc[cat["clase_modelable"], "clase"].nunique()
    with seccion("demo"):
        bloque(f"""
        {_cabeza(5, "Demo", "Pro[b]alo")}
        <div class="vs-con-foto" style="grid-template-columns:minmax(0,7fr) minmax(0,5fr)">
          {foto("cierre")}
          <div>
            <div class="vs-chico">{numero(1)}Compara contra un <b>catálogo regional</b> de
            {len(cat)} toxinas de {cat['genero_consultado'].nunique()} géneros de animales del
            noreste argentino, agrupadas en {n_familias} familias y descargadas de UniProt, la
            base pública de proteínas más usada del mundo.</div>
            <div class="vs-chico">{numero(2)}Andá a la pestaña {marca("Una secuencia")} y elegí un
            ejemplo: una toxina que ya conocemos, una de otra parte del mundo que el sistema
            nunca vio y una secuencia con errores.</div>
            <div class="vs-chico">{numero(3)}En <b>Una campaña entera</b> está el caso real:
            muchas secuencias de golpe, ordenadas por prioridad. El sistema ayuda a priorizar;
            la decisión sigue siendo del laboratorio.</div>
          </div>
        </div>
        """)


def mostrar(motor: Motor):
    _portada(motor)
    _problema()
    _biologia()
    _como_funciona(motor)
    m = motor.config.get("metricas", {})
    if m:
        _resultados(m)
    _probalo(motor)
