"""Piezas visuales en HTML: la insignia de prioridad, la escala de novedad y compañía.

Cada función devuelve un texto HTML para `st.markdown(..., unsafe_allow_html=True)`.
No importan Streamlit, así que se pueden probar solas (tests/test_componentes.py).
Las clases `vs-*` están definidas en `estilo.py`.

Tres reglas para que Streamlit no las rompa:
- Nada de líneas en blanco ni de sangría dentro del HTML: Markdown lo tomaría por código.
- Todo lo que viene de afuera (nombre de la muestra, de la proteína, especie) pasa por `escape`.
- El color nunca dice algo solo: siempre va con un texto al lado.
"""
import math
from html import escape

from venomscope import prioridad
from venomscope.novedad import NIVEL_CONOCIDA, NIVEL_MEDIA, NIVEL_NOVEDOSA, nivel_para

# Qué color lleva cada cosa. Alta/novedosa es naranja, el mismo de "tu secuencia" en el
# mapa 3D; media es ámbar; baja/conocida es azul. Las clases se definen en estilo.py.
CLASE_PRIORIDAD = {prioridad.ALTA: "alta", prioridad.MEDIA: "media", prioridad.BAJA: "baja"}
NOTA_PRIORIDAD = {
    prioridad.ALTA: "Mirarla primero",
    prioridad.MEDIA: "Mirarla después de las altas",
    prioridad.BAJA: "Puede esperar",
}
ETIQUETA_PASO = {"reglas": "Reglas fijas", "ia": "Inteligencia artificial"}


def _clase(nivel: str) -> str:
    """'alta', 'media', 'baja' o 'nula' (gris) para lo que no tiene prioridad."""
    return CLASE_PRIORIDAD.get(nivel, "nula")


def _marca_svg() -> str:
    """El logo: la propia idea del mapa 3D. Un punto naranja (tu secuencia) rodeado del
    catálogo en gris, con líneas hacia tres vecinos más parecidos."""
    cx = cy = 24
    radio = 18.5
    puntos = [(cx + radio * math.cos(math.tau * i / 12 - math.pi / 2),
               cy + radio * math.sin(math.tau * i / 12 - math.pi / 2)) for i in range(12)]
    vecinos = {1, 5, 9}
    lineas = "".join(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}"/>'
                     for i, (x, y) in enumerate(puntos) if i in vecinos)
    grises = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.3"/>'
                     for i, (x, y) in enumerate(puntos) if i not in vecinos)
    aguas = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3"/>'
                    for i, (x, y) in enumerate(puntos) if i in vecinos)
    return ('<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
            f'<g stroke="#199e70" stroke-width="1.4" opacity=".8">{lineas}</g>'
            f'<g fill="#52525b">{grises}</g><g fill="#199e70">{aguas}</g>'
            '<rect x="-5" y="-5" width="10" height="10" transform="translate(24 24) rotate(45)" '
            'fill="#d95926" stroke="#09090b" stroke-width="1.5"/></svg>')


MARCA_SVG = _marca_svg()


def encabezado(titulo: str, lema: str) -> str:
    return (f'<header class="vs-hero">{MARCA_SVG}<div>'
            f'<h1 class="vs-titulo">{escape(titulo)}</h1>'
            f'<div class="vs-lema">{escape(lema)}</div></div></header>')


def insignia(nivel: str) -> str:
    """El bloque grande con la prioridad: la respuesta a "¿la miro o no?"."""
    return (f'<div class="vs-insignia vs-n-{_clase(nivel)}">'
            f'<span class="vs-insignia-nivel">{escape(nivel)}</span>'
            f'<span class="vs-insignia-nota">{escape(NOTA_PRIORIDAD.get(nivel, ""))}</span></div>')


def escala_novedad(puntaje: float, umbrales: dict, titulo: str | None = None) -> str:
    """La regla de 0 a 100 con sus tres zonas y una marca donde cae la secuencia.

    Las zonas miden lo que miden los cortes de verdad (escala lineal): como los cortes
    están arriba de 75, la zona "parecida a algo conocido" ocupa la mayor parte. Si el
    usuario mueve el control de sensibilidad, la zona "novedosa" se ensancha.
    """
    medio, alto = umbrales["medio"], umbrales["alto"]
    p = min(max(float(puntaje), 0.0), 100.0)
    nivel = nivel_para(p, umbrales)
    zonas = [(NIVEL_CONOCIDA, "baja", 0, medio),
             (NIVEL_MEDIA, "media", medio, alto),
             (NIVEL_NOVEDOSA, "alta", alto, 100)]

    pista = "".join(
        f'<span class="vs-zona vs-n-{c}{" vs-zona-activa" if n == nivel else ""}" '
        f'style="flex:{hasta - desde}"></span>' for n, c, desde, hasta in zonas)
    marca = f'<span class="vs-marca" style="--p:{p:.1f}%"><span class="vs-marca-etq">{p:.0f}</span></span>'
    nombres = "".join(
        f'<span class="vs-n-{c}{" vs-nombre-activo" if n == nivel else ""}" '
        f'style="flex:{hasta - desde}">{escape(n)}</span>' for n, c, desde, hasta in zonas)
    # Debajo, el número donde empieza cada zona; la última lleva también el 100 del final.
    numeros = "".join(f'<span style="flex:{hasta - desde}">{desde}</span>'
                      for _, _, desde, hasta in zonas[:-1])
    _, _, desde, hasta = zonas[-1]
    numeros += f'<span class="vs-fin" style="flex:{hasta - desde}">{desde}<em>{hasta}</em></span>'

    cabecera = f'<div class="vs-escala-tit">{escape(titulo)}</div>' if titulo else ""
    aria = (f"Novedad {p:.0f} de 100: {nivel}. Los cortes están en {medio} y {alto}.")
    return (f'<div class="vs-escala" role="img" aria-label="{escape(aria)}">{cabecera}'
            f'<div class="vs-escala-cuerpo"><div class="vs-pista">{pista}{marca}</div>'
            f'<div class="vs-nombres">{nombres}</div><div class="vs-numeros">{numeros}</div></div></div>')


def veredicto(titular: str, detalle: str, nivel_prioridad: str) -> str:
    """Una frase que dice qué hacer. `titular` y `detalle` ya vienen como HTML seguro."""
    return (f'<div class="vs-veredicto vs-n-{_clase(nivel_prioridad)}">'
            f'<strong>{titular}</strong> {detalle}</div>')


def distribucion(niveles: list[tuple[str, int]]) -> str:
    """Una barra con la proporción de cada prioridad en la campaña, más su leyenda.

    `niveles` va en el orden en que se quiere mostrar: [(nivel, cantidad), ...]. Las tres
    prioridades salen siempre en la leyenda (un "Alta 0%" también informa); "No analizada"
    solo si hay alguna.
    """
    total = sum(n for _, n in niveles) or 1
    segmentos = "".join(
        f'<span class="vs-n-{_clase(nivel)}" style="flex:{n}" title="{escape(nivel)}: {n}"></span>'
        for nivel, n in niveles if n > 0)
    leyenda = "".join(
        f'<span class="vs-ley vs-n-{_clase(nivel)}"><i></i>{escape(nivel)} <b>{n / total:.0%}</b></span>'
        for nivel, n in niveles if n > 0 or nivel in CLASE_PRIORIDAD)
    resumen = ", ".join(f"{nivel}: {n}" for nivel, n in niveles if n > 0)
    return (f'<div class="vs-dist"><div class="vs-dist-barra" role="img" '
            f'aria-label="{escape(resumen)}">{segmentos}</div>'
            f'<div class="vs-dist-ley">{leyenda}</div></div>')


def tarjetas_muestras(filas: list[dict]) -> str:
    """Una tarjeta por muestra, para ver de un vistazo las de mayor novedad.

    Cada fila es una fila de `tabla_resultados`.
    """
    tarjetas = []
    for f in filas:
        nivel = f.get("Prioridad", "")
        novedad = min(max(float(f.get("Novedad (0-100)", 0)), 0.0), 100.0)
        tarjetas.append(
            f'<div class="vs-tarjeta vs-n-{_clase(nivel)}">'
            f'<div class="vs-tarjeta-cab"><span class="vs-tarjeta-id" title="{escape(str(f.get("Muestra", "")))}">'
            f'{escape(str(f.get("Muestra", "")))}</span><span class="vs-nivel">{escape(nivel)}</span></div>'
            f'<div class="vs-tarjeta-fam">{escape(str(f.get("Familia probable", "")))}</div>'
            f'<div class="vs-tarjeta-sub">Más parecida a {escape(str(f.get("Más parecida a", "")))}</div>'
            f'<div class="vs-mini"><span>Novedad</span><span class="vs-mini-barra">'
            f'<i style="width:{novedad:.0f}%"></i></span><b>{novedad:.0f}</b></div></div>')
    return f'<div class="vs-tarjetas">{"".join(tarjetas)}</div>'


def pasos(items: list[dict]) -> str:
    """Los pasos del sistema, en orden. Cada uno dice si lo hace una regla o la IA.

    Cada item: {"titulo", "texto", "tipo"}, con tipo "reglas" o "ia". El texto es HTML
    propio del proyecto (lleva <strong>), no viene de afuera.
    """
    tarjetas = "".join(
        f'<div class="vs-paso vs-paso-{p["tipo"]}" role="listitem">'
        f'<span class="vs-paso-n">{i}</span><span class="vs-paso-tit">{p["titulo"]}</span>'
        f'<span class="vs-paso-txt">{p["texto"]}</span>'
        f'<span class="vs-paso-tipo">{ETIQUETA_PASO[p["tipo"]]}</span></div>'
        for i, p in enumerate(items, start=1))
    return f'<div class="vs-pasos" role="list">{tarjetas}</div>'


def cifras(pares: list[tuple[int | str, str]]) -> str:
    """Números grandes con su rótulo, para la barra lateral."""
    celdas = "".join(f'<div><b>{escape(str(n))}</b><span>{escape(r)}</span></div>' for n, r in pares)
    return f'<div class="vs-cifras">{celdas}</div>'


def criterios(items: list[tuple[str, str, str]]) -> str:
    """Lista de "etiqueta de color + explicación". Cada item: (clase, etiqueta, texto).

    La etiqueta va en minúscula y el estilo la muestra con la primera en mayúscula; así
    no se confunde con el resultado real de una secuencia cuando se lee el texto de la página.
    """
    filas = "".join(
        f'<div class="vs-criterio"><span class="vs-chip vs-n-{clase}">{escape(etiqueta)}</span>'
        f'<span>{texto}</span></div>' for clase, etiqueta, texto in items)
    return f'<div class="vs-criterios">{filas}</div>'


def etiqueta(texto: str) -> str:
    """Un rótulo chico, con el mismo aspecto que el de las métricas."""
    return f'<span class="vs-etiqueta">{escape(texto)}</span>'


def cifra(texto: str | int) -> str:
    """Un número dentro de una frase, en la tipografía de los números."""
    return f'<span class="vs-cifra">{escape(str(texto))}</span>'


# ---------------------------------------------------------------- plan de laboratorio ----
def _recortar(texto: str, largo: int) -> str:
    return texto if len(texto) <= largo else texto[: largo - 1] + "…"


def arbol_hallazgos(nombres: list[str], niveles: list[str], Z, etiquetas, corte: float,
                    orden_plan: dict[int, int]) -> str:
    """El árbol de parentesco de la campaña, con el plan marcado encima.

    Cada fila es una muestra. Las ramas unen las que se parecen: cuanto más a la izquierda se
    juntan, más parecidas son. La línea punteada es el corte que define un "hallazgo": lo que
    se junta antes de la línea cuenta como lo mismo, y cada banda gris/oscura es un hallazgo.
    El círculo con número marca las muestras que el plan elige, en orden.

    - `Z`: matriz de enlace de scipy; `etiquetas`: grupo de cada muestra al corte.
    - `orden_plan`: {posición de la muestra: lugar en el plan (1, 2, 3...)}.
    El color del punto es la prioridad; el nombre y la leyenda dicen lo mismo con texto.
    """
    from scipy.cluster.hierarchy import dendrogram

    n = len(nombres)
    if n < 2:
        return ""
    arbol = dendrogram(Z, no_plot=True)
    hojas = arbol["leaves"]                         # índices de muestra, de arriba a abajo
    fila_de = {m: f for f, m in enumerate(hojas)}
    con_nombres = n <= 40
    alto_fila = 22 if con_nombres else max(6.0, 880.0 / n)
    top, ancho, x_arbol, x_fin = 30, 900, 300, 780
    alto = top + n * alto_fila + 34
    d_max = max(float(Z[:, 2].max()), corte * 1.5)

    def x(d):
        return x_arbol + d / d_max * (x_fin - x_arbol)

    def y(fila):
        return top + (fila + 0.5) * alto_fila

    partes = []
    # Bandas: una por hallazgo, alternando para que se distingan.
    grupos: dict[int, list[int]] = {}
    for m in hojas:
        grupos.setdefault(int(etiquetas[m]), []).append(fila_de[m])
    for k, filas in enumerate(grupos.values()):
        a, b = min(filas), max(filas)
        if k % 2 == 0:
            partes.append(f'<rect class="vs-banda" x="0" y="{top + a * alto_fila:.1f}" width="{ancho}" '
                          f'height="{(b - a + 1) * alto_fila:.1f}"/>')
        if len(filas) > 1:
            partes.append(f'<text class="vs-arbol-n" x="{ancho - 8}" y="{y((a + b) / 2) + 4:.1f}" '
                          f'text-anchor="end">{len(filas)} muestras</text>')
    # Ramas (en horizontal: la distancia va hacia la derecha).
    for ic, dc in zip(arbol["icoord"], arbol["dcoord"]):
        puntos = " ".join(f"{x(d):.1f},{y((i - 5) / 10):.1f}" for i, d in zip(ic, dc))
        clase = "vs-rama vs-rama-hallazgo" if max(dc) <= corte else "vs-rama"
        partes.append(f'<polyline class="{clase}" points="{puntos}"/>')
    # Corte y eje.
    partes.append(f'<line class="vs-corte" x1="{x(corte):.1f}" x2="{x(corte):.1f}" y1="{top - 8}" '
                  f'y2="{top + n * alto_fila:.1f}"/>')
    partes.append(f'<text class="vs-arbol-eje" x="{x(corte) + 6:.1f}" y="{top - 12}">corte: mismo hallazgo</text>')
    base = top + n * alto_fila + 20
    partes.append(f'<text class="vs-arbol-eje" x="{x_arbol}" y="{base}">más parecidas</text>')
    partes.append(f'<text class="vs-arbol-eje" x="{x_fin}" y="{base}" text-anchor="end">más distintas</text>')
    # Filas: plan, prioridad y nombre.
    for m in hojas:
        yy = y(fila_de[m])
        clase = _clase(niveles[m])
        if m in orden_plan:
            partes.append(f'<circle class="vs-plan-marca" cx="18" cy="{yy:.1f}" r="{min(10, alto_fila / 2 + 1):.1f}"/>'
                          f'<text class="vs-plan-num" x="18" y="{yy + 4:.1f}" text-anchor="middle">{orden_plan[m]}</text>')
        partes.append(f'<circle class="vs-n-{clase} vs-punto" cx="44" cy="{yy:.1f}" r="{min(5, alto_fila / 3):.1f}"/>')
        if con_nombres or m in orden_plan:
            peso = " vs-arbol-sel" if m in orden_plan else ""
            partes.append(f'<text class="vs-arbol-nombre{peso}" x="58" y="{yy + 4:.1f}">{escape(_recortar(nombres[m], 30))}</text>')
    resumen = f"{n} muestras en {len(grupos)} hallazgos; el plan elige {len(orden_plan)}."
    return (f'<div class="vs-arbol"><svg viewBox="0 0 {ancho} {alto:.0f}" role="img" aria-label="{escape(resumen)}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(partes)}</svg></div>')


def leyenda_arbol() -> str:
    """Qué significa cada marca del árbol, con texto: el color nunca va solo."""
    return ('<div class="vs-dist-ley vs-leyenda-arbol">'
            '<span class="vs-ley"><i class="vs-ley-plan"></i>lugar en el plan</span>'
            '<span class="vs-ley vs-n-alta"><i></i>prioridad alta</span>'
            '<span class="vs-ley vs-n-media"><i></i>prioridad media</span>'
            '<span class="vs-ley vs-n-baja"><i></i>prioridad baja</span>'
            '<span class="vs-ley"><i class="vs-ley-banda"></i>cada banda es un hallazgo</span></div>')


def curva_plan(plan: list[float], ranking: list[float], cupos: int) -> str:
    """Cobertura con 1, 2, 3... cupos: el plan contra ordenar por novedad.

    Los dos recorren la misma vara (`plan.cobertura`). Ver cuánto separa las dos líneas es ver
    cuánto se ahorra: con el ranking hace falta más presupuesto para cubrir lo mismo.
    """
    n = len(plan)
    if n < 2:
        return ""
    ancho, alto, izq, der, arriba, abajo = 460, 240, 44, 16, 40, 40

    def x(k):
        return izq + (k - 1) / (n - 1) * (ancho - izq - der)

    def y(v):
        return arriba + (1 - v) * (alto - arriba - abajo)

    def linea(valores):
        return " ".join(f"{x(k + 1):.1f},{y(v):.1f}" for k, v in enumerate(valores))

    partes = []
    for g in (0, 0.25, 0.5, 0.75, 1.0):
        partes.append(f'<line class="vs-grilla" x1="{izq}" x2="{ancho - der}" y1="{y(g):.1f}" y2="{y(g):.1f}"/>'
                      f'<text class="vs-arbol-eje" x="{izq - 6}" y="{y(g) + 4:.1f}" text-anchor="end">{g:.0%}</text>')
    paso = 1 if n <= 10 else 2
    for k in range(1, n + 1, paso):
        partes.append(f'<text class="vs-arbol-eje" x="{x(k):.1f}" y="{alto - abajo + 18}" text-anchor="middle">{k}</text>')
    partes.append(f'<text class="vs-arbol-eje" x="{(izq + ancho - der) / 2:.1f}" y="{alto - 4}" text-anchor="middle">cupos del laboratorio</text>')
    partes.append(f'<polyline class="vs-linea-ranking" points="{linea(ranking)}"/>')
    partes.append(f'<polyline class="vs-linea-plan" points="{linea(plan)}"/>')
    k = min(max(cupos, 1), n)
    partes.append(f'<line class="vs-corte" x1="{x(k):.1f}" x2="{x(k):.1f}" y1="{arriba}" y2="{alto - abajo}"/>'
                  f'<circle class="vs-punto-plan" cx="{x(k):.1f}" cy="{y(plan[k - 1]):.1f}" r="5"/>'
                  f'<circle class="vs-punto-ranking" cx="{x(k):.1f}" cy="{y(ranking[k - 1]):.1f}" r="4"/>')
    # Leyenda adentro del gráfico: una muestra de cada trazo con su nombre.
    partes.append(f'<line class="vs-linea-plan" x1="{izq}" x2="{izq + 26}" y1="14" y2="14"/>'
                  f'<text class="vs-etq-plan" x="{izq + 32}" y="18">Plan</text>'
                  f'<line class="vs-linea-ranking" x1="{izq + 90}" x2="{izq + 116}" y1="14" y2="14"/>'
                  f'<text class="vs-etq-ranking" x="{izq + 122}" y="18">Ranking por novedad</text>')
    aria = (f"Con {k} cupos el plan cubre {plan[k - 1]:.0%} y el ranking por novedad {ranking[k - 1]:.0%}.")
    return (f'<div class="vs-curva"><svg viewBox="0 0 {ancho} {alto}" role="img" aria-label="{escape(aria)}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(partes)}</svg></div>')
