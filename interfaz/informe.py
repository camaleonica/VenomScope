"""El informe de la campaña: un solo archivo HTML para entregar, abrir sin la app o imprimir.

Para quién. La app es para quien opera el sistema; el informe es para quien decide: la
gerencia o la dirección del laboratorio, que no abre la app. Dice qué se analizó, cuáles
muestras conviene estudiar con el presupuesto que hay, por qué, y qué límites tiene todo eso.

Cómo está hecho. Es un archivo autocontenido: sin imágenes externas, sin scripts salvo un
botón de imprimir, sin tipografías que bajar. Se abre en cualquier navegador sin internet y,
con "Imprimir > Guardar como PDF", sale en A4. Usa colores claros (la app es oscura) porque
un informe se imprime.

Usa las mismas piezas que la pantalla (`componentes`) y los mismos números (`plan.PlanArmado`),
así pantalla e informe no pueden contradecirse.

Todo lo que viene de afuera (nombres de muestras, familias) pasa por `escape`. Este módulo
no conoce Streamlit.
"""
from datetime import datetime
from html import escape

import pandas as pd

from interfaz import componentes
from venomscope import plan as plan_mod
from venomscope import prioridad

CSS = """
:root{--tinta:#111827;--tenue:#4b5563;--ejes:#6b7280;--borde:#e5e7eb;--fondo-suave:#f9fafb}
.vs-n-alta{--c:#d95926;--ct:#a8431b;--cf:rgba(217,89,38,.12)}
.vs-n-media{--c:#b07a00;--ct:#7a5600;--cf:rgba(176,122,0,.12)}
.vs-n-baja{--c:#3987e5;--ct:#1f5fae;--cf:rgba(57,135,229,.12)}
.vs-n-nula{--c:#6b7280;--ct:#4b5563;--cf:rgba(107,114,128,.12)}
*{box-sizing:border-box}
body{margin:0;background:#fff;color:var(--tinta);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.inf{max-width:980px;margin:0 auto;padding:2.2rem 1.6rem 3rem}
h1{margin:0;font-size:2rem;letter-spacing:-.02em;line-height:1.15}
h2{margin:2.4rem 0 .6rem;padding-top:1.2rem;border-top:1px solid var(--borde);font-size:1.35rem;letter-spacing:-.01em}
.meta{margin:.4rem 0 0;color:var(--tenue)}
.titular{margin:1.6rem 0 1rem;max-width:62ch;font-size:1.25rem;line-height:1.45}
.cifras{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:.8rem;margin:1rem 0}
.cifras div{padding:.8rem 1rem;border:1px solid var(--borde);border-radius:8px;background:var(--fondo-suave)}
.cifras b{display:block;font:650 2rem/1.1 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;letter-spacing:-.03em}
.cifras span{color:var(--tenue);font-size:.9rem}
p{max-width:72ch}
.nota{color:var(--tenue);font-size:.92rem}
table{width:100%;border-collapse:collapse;margin:.8rem 0;font-size:.88rem}
th,td{padding:.45rem .55rem;border-bottom:1px solid var(--borde);text-align:left;vertical-align:top}
th{color:var(--tenue);font-weight:600;background:var(--fondo-suave);white-space:nowrap}
td.porque{width:32%;min-width:16ch}
td.id{font:.82rem ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;white-space:nowrap}
td.num{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;text-align:right;white-space:nowrap}
.chip{display:inline-block;padding:.02rem .5rem;border:1px solid var(--c);border-radius:4px;background:var(--cf);
color:var(--ct);font-weight:650;font-size:.82rem}
.limites li{margin:.35rem 0;max-width:72ch}
.pie{margin-top:2.4rem;padding-top:1rem;border-top:1px solid var(--borde);color:var(--tenue);font-size:.85rem}
.boton{margin-top:1rem;padding:.5rem 1rem;border:1px solid var(--tinta);border-radius:6px;background:#fff;
color:var(--tinta);font:inherit;cursor:pointer}

/* piezas compartidas con la pantalla, en versión clara */
.vs-dist{margin:.9rem 0 .6rem}
.vs-dist-barra{display:flex;gap:2px;height:12px}
.vs-dist-barra span{min-width:6px;background:var(--c);border-radius:2px}
.vs-dist-ley{display:flex;flex-wrap:wrap;gap:.35rem 1.5rem;margin-top:.6rem;font-size:.9rem;color:var(--tenue)}
.vs-ley i{display:inline-block;width:.7rem;height:.7rem;margin-right:.45rem;background:var(--c,#6b7280);border-radius:2px}
.vs-ley i.vs-ley-plan{background:#111827;border-radius:50%}
.vs-ley i.vs-ley-banda{background:rgba(0,0,0,.1)}
.vs-ley b{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:var(--tinta)}
.vs-leyenda-arbol{margin:.2rem 0 1rem}
.vs-arbol,.vs-curva{margin:.6rem 0;padding:.5rem;border:1px solid var(--borde);border-radius:8px;overflow-x:auto}
.vs-arbol svg,.vs-curva svg{display:block;width:100%;height:auto;min-width:520px;font-family:inherit}
.vs-curva svg{max-width:520px}
.vs-banda{fill:rgba(0,0,0,.05)}
.vs-rama{fill:none;stroke:#9ca3af;stroke-width:1.4;stroke-linejoin:round}
.vs-rama.vs-rama-hallazgo{stroke:#4b5563;stroke-width:2}
.vs-corte{stroke:#374151;stroke-width:1;stroke-dasharray:4 4;opacity:.7}
.vs-punto{fill:var(--c)}
.vs-plan-marca{fill:#111827}
.vs-plan-num{fill:#fff;font:600 12px ui-monospace,Menlo,Consolas,monospace}
.vs-arbol-nombre{fill:#374151;font-size:12.5px}
.vs-arbol-nombre.vs-arbol-sel{fill:#000;font-weight:650}
.vs-arbol-eje,.vs-arbol-n{fill:var(--ejes);font-size:11px}
.vs-grilla{stroke:var(--borde);stroke-width:1}
.vs-linea-plan{fill:none;stroke:#111827;stroke-width:2.5;stroke-linejoin:round}
.vs-linea-ranking{fill:none;stroke:#6b7280;stroke-width:2;stroke-dasharray:5 4;stroke-linejoin:round}
.vs-punto-plan{fill:#111827}
.vs-punto-ranking{fill:#6b7280}
.vs-etq-plan{fill:#111827;font-size:12px;font-weight:650}
.vs-etq-ranking{fill:#4b5563;font-size:12px}

@page{size:A4;margin:14mm}
@media print{
.inf{max-width:none;padding:0}.no-imprimir{display:none}
h2{break-after:avoid}.vs-arbol,.vs-curva,table,.cifras{break-inside:avoid}
body{font-size:11.5pt}
}
"""

LIMITES = [
    "El catálogo contiene lo que ya se publicó en UniProt. Una especie poco estudiada va a parecer más "
    "novedosa de lo que es, simplemente porque hay menos con qué compararla.",
    "La novedad y la familia son estimaciones de un modelo, no resultados de laboratorio. El sistema siempre "
    "elige alguna familia, aunque la secuencia no se parezca a ninguna: por eso se lee junto con la novedad.",
    "Los péptidos cortos no se pudieron validar: los del catálogo salen de solo cuatro familias, y siete de cada "
    "diez son parientes entre sí, así que no se sabe qué tan confiable es el sistema con uno de una familia distinta.",
    "El plan se calculó en simulaciones con campañas armadas con datos reales; en una campaña poco redundante la "
    "ventaja sobre ordenar por novedad es menor.",
    "Sirve para ordenar y priorizar. No reemplaza el análisis de laboratorio: la decisión es de quien lo hace.",
]


def _txt(valor) -> str:
    """Texto seguro para HTML; vacío si el dato falta."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    return escape(str(valor))


def _corto(texto: str, largo: int = 32) -> str:
    """Un nombre largo se recorta (el nombre completo queda en el tooltip)."""
    return texto if len(texto) <= largo else texto[: largo - 1] + "…"


def _chip(nivel: str) -> str:
    return f'<span class="chip vs-n-{componentes.CLASE_PRIORIDAD.get(nivel, "nula")}">{escape(nivel)}</span>'


def _tabla_plan(tabla: pd.DataFrame, ids: list[str], armado: plan_mod.PlanArmado, cupos: int) -> str:
    por_id = tabla.set_index("Muestra")
    por_id = por_id[~por_id.index.duplicated()]          # dos muestras con el mismo nombre: se usa la primera
    filas = []
    for lugar, e in enumerate(armado.elegidas[:cupos], start=1):
        id_ = ids[e.indice]
        r = por_id.loc[id_]
        filas.append(
            f'<tr><td class="num">{lugar}</td><td class="id" title="{escape(id_)}">{escape(_corto(id_))}</td><td>{_chip(r["Prioridad"])}</td>'
            f'<td>{_txt(r["Familia probable"])}</td><td class="num">{_txt(r["Novedad (0-100)"])}</td>'
            f'<td class="num">{e.ganancia:.0%}</td><td class="num">{armado.equivale_a(e.indice)}</td>'
            f'<td class="porque">{_txt(r["Motivo"])}</td></tr>')
    cabeza = ("<tr><th>Orden</th><th>Muestra</th><th>Prioridad</th><th>Familia probable</th><th>Novedad</th>"
              "<th>Aporta</th><th>Equivale a</th><th>Por qué</th></tr>")
    return f"<table>{cabeza}{''.join(filas)}</table>"


def _tabla_todas(tabla: pd.DataFrame) -> str:
    filas = []
    for _, r in tabla.iterrows():
        confianza = "" if pd.isna(r["Confianza"]) else f'{r["Confianza"]:.0%}'
        parecida = _txt(r["Más parecida a"]) or _txt(r["Avisos"])
        filas.append(
            f'<tr><td class="id" title="{_txt(r["Muestra"])}">{escape(_corto(str(r["Muestra"])))}</td><td>{_chip(r["Prioridad"])}</td><td>{_txt(r["Familia probable"])}</td>'
            f'<td class="num">{confianza}</td><td class="num">{_txt(r["Novedad (0-100)"])}</td><td>{parecida}</td></tr>')
    cabeza = ("<tr><th>Muestra</th><th>Prioridad</th><th>Familia probable</th><th>Seguridad</th>"
              "<th>Novedad</th><th>Más parecida a</th></tr>")
    return f"<table>{cabeza}{''.join(filas)}</table>"


def construir(*, tabla: pd.DataFrame, ids_plan: list[str] | None, armado: plan_mod.PlanArmado | None,
              nivel_de: dict[str, str], cupos: int, umbrales: dict, catalogo_n: int, n_confirmadas: int,
              fecha: datetime, metricas: dict | None = None) -> str:
    """El informe completo, como texto HTML.

    - `tabla`: la de `tabla_resultados`. `ids_plan`: ids de las muestras analizadas, en el mismo
      orden que las filas del plan (`armado`). Si no hay plan, `armado` es None.
    - `nivel_de`: {id de muestra: prioridad} para colorear el árbol.
    """
    n = len(tabla)
    conteo = tabla["Prioridad"].value_counts()
    niveles = [prioridad.ALTA, prioridad.MEDIA, prioridad.BAJA, "No analizada"]
    altas = int(conteo.get(prioridad.ALTA, 0))

    base = f"{catalogo_n} toxinas"
    if n_confirmadas:
        base += f", entre ellas {n_confirmadas} confirmada{'s' if n_confirmadas != 1 else ''} por el laboratorio"
    cifras = [(n, "muestras"), (altas, "de prioridad alta")]
    if armado:
        cifras.insert(1, (armado.hallazgos, "hallazgos distintos"))
        if armado.elegidas:
            k = min(cupos, len(armado.elegidas))
            cifras.append((f"{armado.curva_plan[k - 1]:.0%}", f"de lo importante cubierto con {k} "
                           f"{'cupo' if k == 1 else 'cupos'}"))
    html_cifras = "".join(f"<div><b>{escape(str(v))}</b><span>{escape(t)}</span></div>" for v, t in cifras)

    if armado and armado.elegidas:
        k = min(cupos, len(armado.elegidas))
        titular = (f"De {n} muestras, {armado.hallazgos} son hallazgos distintos. Con {k} "
                   f"{'cupo' if k == 1 else 'cupos'} de laboratorio, el plan cubre el {armado.curva_plan[k - 1]:.0%} "
                   f"de lo importante; ordenando solo por novedad se cubriría el {armado.curva_ranking[k - 1]:.0%}.")
    else:
        titular = f"Se analizaron {n} muestras; {altas} resultaron de prioridad alta."

    plan_html = ""
    if armado and armado.elegidas and ids_plan:
        k = min(cupos, len(armado.elegidas))
        suficiente = armado.cupos_suficientes()
        extra = (f" Con {suficiente} {'cupo' if suficiente == 1 else 'cupos'} ya se cubre el 95%: los que siguen "
                 "casi no suman." if suficiente is not None and suficiente < k else "")
        niveles_arbol = [nivel_de.get(i, "No analizada") for i in ids_plan]
        plan_html = (
            "<h2>Plan de laboratorio</h2>"
            f"<p>Ordenar por novedad no alcanza: si varias muestras son variantes de lo mismo, todas quedan arriba y "
            f"gastan cupos en un solo hallazgo. Para {k} {'cupo' if k == 1 else 'cupos'}, el plan elige las muestras "
            f"que representan a toda la campaña.{extra}</p>"
            + componentes.arbol_hallazgos(ids_plan, niveles_arbol, armado.Z, armado.etiquetas, armado.corte,
                                          {i: j + 1 for j, i in enumerate(armado.orden[:k])})
            + componentes.leyenda_arbol()
            + _tabla_plan(tabla, ids_plan, armado, k)
            + componentes.curva_plan(armado.curva_plan, armado.curva_ranking, k)
            + f'<p class="nota">Dos muestras cuentan como el mismo hallazgo si están a menos de {armado.corte:.3f} de '
              "distancia (calibrado con las familias reales del catálogo). «Aporta» es la cobertura nueva que suma cada "
              "muestra a las anteriores; «Equivale a» son las otras muestras del mismo hallazgo.</p>")

    cuerpo = (
        '<main class="inf">'
        "<h1>Informe de campaña</h1>"
        f'<p class="meta">VenomScope · {fecha.strftime("%d/%m/%Y %H:%M")} · referencia: {escape(base)} · '
        f'«novedosa» desde el puntaje {escape(str(umbrales["alto"]))}</p>'
        f'<p class="titular">{escape(titular)}</p>'
        f'<div class="cifras">{html_cifras}</div>'
        + componentes.distribucion([(nivel, int(conteo.get(nivel, 0))) for nivel in niveles])
        + plan_html
        + "<h2>Todas las muestras</h2>" + _tabla_todas(tabla)
        + "<h2>Cómo leer este informe y sus límites</h2>"
        + '<ul class="limites">' + "".join(f"<li>{escape(t)}</li>" for t in LIMITES) + "</ul>"
        + (f'<p class="nota">Medido con datos reales del catálogo: acierto de familia {metricas["macro_f1_esm2"]:.0%} '
           f'en el examen normal y {metricas["macro_f1_esm2_agrupado"]:.0%} en el difícil.</p>' if metricas else "")
        + f'<div class="pie">Generado por VenomScope el {fecha.strftime("%d/%m/%Y a las %H:%M")}. '
          "Es una ayuda para priorizar: la decisión es del laboratorio.</div>"
        + '<button class="boton no-imprimir" onclick="window.print()">Imprimir o guardar como PDF</button>'
        "</main>")
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>Informe de campaña · VenomScope</title><style>{CSS}</style></head><body>{cuerpo}</body></html>")
