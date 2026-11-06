"""Pestaña "Cómo leer esto": qué significa cada número y qué no puede hacer el sistema."""
from interfaz.editorial import bloque, cabeza, marca, numero, seccion
from venomscope.analisis import Motor

TOTAL = 3


def _columnas(items, cols: int) -> str:
    """Ítems numerados en columnas angostas: [(título, texto html), ...]."""
    celdas = "".join(
        f'<div>{numero(i)}<p class="vs-item-titulo">{nombre}</p><div class="vs-chico">{texto}</div></div>'
        for i, (nombre, texto) in enumerate(items, start=1))
    return f'<div class="vs-columnas" style="--cols:{cols}">{celdas}</div>'


def _numeros(motor: Motor):
    u = motor.config["novedad"]["umbrales_puntaje"]
    conf = motor.config["clasificador"]["umbral_confianza"]
    items = [
        ("Novedad (0 a 100)",
         "Qué tan lejos está de lo más parecido que tenemos. Un 97 quiere decir: <i>está más "
         "lejos de lo conocido que el 97% de las toxinas del catálogo</i>. Desde "
         f"{u['medio']} se considera \"algo distinta\" y desde {u['alto']} \"novedosa\"; ese "
         "último corte se mueve con el control de sensibilidad."),
        ("Seguridad de la familia",
         f"Qué tan convencido está el sistema. Por debajo de {conf:.0%} avisa. Ojo: siempre "
         "elige alguna familia conocida, aunque la secuencia no se parezca a ninguna. Por eso "
         "hay que mirarla junto con la novedad."),
        ("Prioridad",
         "Sale de <b>reglas fijas</b>, no de la IA, para que siempre se pueda explicar: alta si "
         "es novedosa o si es algo distinta y viene del NEA; media si es algo distinta o si el "
         "sistema duda de la familia; baja si se parece mucho a algo ya estudiado."),
    ]
    with seccion("ayuda_numeros"):
        bloque(f"""
        {cabeza(1, TOTAL, "Los números", "Los tres|nú[m]eros")}
        <div class="vs-esquina" style="margin-bottom:40px">
          <div class="vs-chico">Cada resultado trae tres datos. Los dos primeros salen de la IA;
          el tercero, {marca("de reglas escritas a mano")}.</div>
        </div>
        {_columnas(items, 3)}
        """)


def _marcar_de_mas():
    errores = [
        ("Falsa alarma", "Alguien mira una secuencia y en diez minutos la descarta."),
        ("Novedad perdida",
         "El candidato que no se parecía a nada queda enterrado en una planilla."),
    ]
    with seccion("ayuda_errores", oscura=True):
        bloque(f"""
        {cabeza(2, TOTAL, "Los errores", "Por qué con[v]iene|marcar de más")}
        <div class="vs-con-foto" style="grid-template-columns:minmax(0,5fr) minmax(0,7fr)">
          <div>
            <div class="vs-chico">La sensibilidad no tiene una posición correcta. Bajarla
            encuentra más candidatos y genera más falsas alarmas; subirla hace lo contrario. Lo
            que decide no es la técnica, es <b>cuánto cuesta cada error</b>, y acá no cuestan lo
            mismo.</div>
          </div>
          {_columnas(errores, 2)}
        </div>
        <div class="vs-esquina" style="margin-top:72px">
          <div class="vs-chico">Hay un caso que lo muestra mejor que cualquier argumento. El
          <b>captopril</b>, uno de los antihipertensivos más vendidos de la historia, salió de un
          péptido de <b>nueve aminoácidos</b> del veneno de <i>Bothrops jararaca</i>, una yarará
          que está en nuestro propio catálogo.</div>
          <div class="vs-chico">Un filtro que descartara las secuencias cortas por considerarlas
          basura, que es exactamente lo que íbamos a hacer al principio de este trabajo,
          {marca("habría tirado esa molécula")} sin que nadie se enterara.</div>
        </div>
        """)


def _limites(motor: Motor):
    items = [
        ("Solo lo publicado",
         "El catálogo tiene lo que <b>ya se publicó</b>. Una especie poco estudiada va a parecer "
         "más novedosa de lo que es, simplemente porque hay menos con qué compararla."),
        ("El mapa es aproximado",
         f"El <b>mapa</b> conserva el {motor.config['mapa3d']['varianza_conservada']:.0%} de la "
         "información, así que la posición de un punto es orientativa. El puntaje y las líneas "
         "sí salen del cálculo completo."),
        ("Péptidos cortos",
         "En los <b>péptidos cortos</b> no pudimos comprobar qué tan confiable es: los que "
         "tenemos son casi todos de una misma familia fácil, así que no sabemos cómo se porta "
         "con uno de otra."),
        ("Ayuda, no reemplaza",
         "Sirve para <b>ordenar y priorizar</b>. No reemplaza el análisis de laboratorio."),
    ]
    with seccion("ayuda_limites"):
        bloque(f"""
        {cabeza(3, TOTAL, "Los límites", "Qué no p[u]ede|hacer")}
        {_columnas(items, 4)}
        """)


def mostrar(motor: Motor):
    _numeros(motor)
    _marcar_de_mas()
    _limites(motor)
