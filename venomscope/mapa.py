"""El mapa 3D del catálogo, para ver dónde cae una secuencia.

Qué muestra y qué NO muestra
----------------------------
Aplastar 480 números a 3 conserva alrededor de la mitad de la información. Eso
significa que **la posición en el mapa puede mentir**: una secuencia puede estar
lejísimos de todo en el espacio real y aparecer en el medio del montón acá.

Nos pasó de verdad con ShK, una toxina de anémona de mar: novedad 99 sobre 100 y
sin embargo cae en el centro del dibujo.

Por eso el mapa nunca deja que la posición cuente el veredicto sola:

- el punto de la secuencia lleva **escrito al lado** su puntaje de novedad;
- se dibujan **líneas hacia sus vecinos de verdad**, los que calculamos con los
  480 números, no con los 3 del dibujo;
- se resalta la familia que el clasificador eligió, para poder comparar.

Colores
-------
Son tres y están validados para que se distingan con daltonismo (la guía de
visualización del proyecto limita los gráficos de dispersión a tres colores).
El catálogo va en gris y las familias se identifican con texto, no con color.
"""
import numpy as np
import plotly.graph_objects as go

from venomscope.iconos import con_icono

# Paleta validada contra el fondo oscuro (ver dataviz/references/palette.md).
# Son los pasos "dark" de la misma paleta, no los claros bajados de brillo: el modo
# oscuro se verifica aparte. Tres colores, porque más no pasa la verificación de
# daltonismo en un gráfico de dispersión.
AZUL = "#3987e5"      # la familia que predijo el clasificador
NARANJA = "#d95926"   # la secuencia del usuario
AQUA = "#199e70"      # sus vecinos más parecidos

# El color saturado se reserva para lo que cambia en cada consulta. El catálogo,
# que es el telón de fondo, va apagado para no competir.
GRIS_PUNTOS = "#52525b"
SUPERFICIE = "#09090b"
GRILLA = "#27272a"
EJES = "#3f3f46"
TINTA = "#a1a1aa"
TINTA_CLARA = "#e4e4e7"
FONDO_TOOLTIP = "#18181b"

# Monoespaciada para números y etiquetas. La lista es una cadena de respaldo: si
# JetBrains Mono no está instalada, el navegador baja a la siguiente.
MONO = "JetBrains Mono, SFMono-Regular, Menlo, Consolas, monospace"

N_FAMILIAS_ETIQUETADAS = 6

# Ángulo inicial fijo: el mapa se ve siempre igual al abrir la app.
CAMARA_INICIAL = dict(eye=dict(x=1.15, y=1.15, z=0.75))


def _hover(cat) -> list[str]:
    return [
        f"<b>{f.nombre_proteina.split(' (')[0][:55]}</b><br>"
        f"{f.especie}  ·  {con_icono(f.grupo)}<br>"
        f"{f.clase}<extra></extra>"
        for f in cat.itertuples()
    ]


def figura_3d(motor, resultado=None, altura: int = 620) -> go.Figure:
    """El mapa. Si se pasa un resultado, marca esa secuencia y sus vecinos."""
    cat, coords = motor.catalogo, motor.coords3d
    fig = go.Figure()

    # --- 1. El catálogo entero, en gris y chiquito: es el telón de fondo ---
    fig.add_trace(go.Scatter3d(
        x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
        mode="markers", name=f"Catálogo ({len(cat)} toxinas)",
        marker=dict(size=2.8, color=GRIS_PUNTOS, opacity=0.7),
        hovertemplate=_hover(cat), hoverlabel=dict(align="left"),
    ))

    # --- 2. Las familias se identifican con TEXTO, no con color ---
    # (así el gráfico se lee igual sin distinguir colores)
    _etiquetas_de_familia(fig, cat, coords)

    if resultado is None or resultado.punto3d is None:
        _ejes(fig, altura, coords)
        return fig

    # --- 3. La familia que eligió el clasificador ---
    de_la_familia = (cat["clase"] == resultado.prediccion.familia).to_numpy()
    if de_la_familia.any():
        fig.add_trace(go.Scatter3d(
            x=coords[de_la_familia, 0], y=coords[de_la_familia, 1], z=coords[de_la_familia, 2],
            mode="markers", name=f"Familia sugerida ({de_la_familia.sum()})",
            marker=dict(size=4, color=AZUL, opacity=0.85),
            hovertemplate=_hover(cat[de_la_familia]), hoverlabel=dict(align="left"),
        ))

    # --- 4. Los vecinos DE VERDAD, los de los 480 números ---
    idx = resultado.novedad.vecinos
    p = resultado.punto3d
    for i, (j, parecido) in enumerate(zip(idx, resultado.vecinos["parecido"])):
        fig.add_trace(go.Scatter3d(
            x=[p[0], coords[j, 0]], y=[p[1], coords[j, 1]], z=[p[2], coords[j, 2]],
            mode="lines", line=dict(color=AQUA, width=2), opacity=0.7,
            showlegend=False, hoverinfo="skip",
        ))
    fig.add_trace(go.Scatter3d(
        x=coords[idx, 0], y=coords[idx, 1], z=coords[idx, 2],
        mode="markers", name=f"Las {len(idx)} más parecidas",
        marker=dict(size=6, color=AQUA, line=dict(color=SUPERFICIE, width=1)),
        hovertemplate=_hover(cat.iloc[idx]), hoverlabel=dict(align="left"),
    ))

    # --- 5. La secuencia del usuario: grande y con el puntaje ESCRITO al lado ---
    # El texto es lo que impide que el dibujo contradiga al veredicto cuando la
    # posición no alcanza para mostrar que está aislada. Va como anotación de la
    # escena y no como texto suelto para que tenga fondo propio: así se lee aunque
    # le caiga encima la etiqueta de una familia.
    fig.add_trace(go.Scatter3d(
        x=[p[0]], y=[p[1]], z=[p[2]],
        mode="markers", name="Tu secuencia",
        marker=dict(size=13, color=NARANJA, symbol="diamond",
                    line=dict(color=SUPERFICIE, width=2)),
        hovertemplate=f"<b>Tu secuencia</b><br>{resultado.novedad.nivel}<br>"
                      f"Novedad {resultado.novedad.puntaje:.0f}/100<extra></extra>",
    ))

    _ejes(fig, altura, np.vstack([coords, p]), anotacion=dict(
        x=p[0], y=p[1], z=p[2],
        text=f"<b>novedad {resultado.novedad.puntaje:.0f}/100</b><br>{resultado.novedad.nivel}",
        showarrow=True, arrowhead=0, arrowwidth=1.5, arrowcolor=NARANJA,
        ax=70, ay=-55, font=dict(size=11, color=TINTA_CLARA, family=MONO),
        bgcolor="rgba(24,24,27,0.92)", bordercolor=NARANJA, borderwidth=1, borderpad=5,
    ))
    return fig


def _acortar(nombre: str, maximo: int = 26) -> str:
    """Corta en el espacio anterior, no a mitad de palabra."""
    if len(nombre) <= maximo:
        return nombre
    recortado = nombre[:maximo].rsplit(" ", 1)[0]
    return (recortado or nombre[:maximo]) + "…"


def _etiquetas_de_familia(fig: go.Figure, cat, coords) -> None:
    """El nombre de cada familia grande, en el centro de su nube.

    Pocas y cortas a propósito: con más se pisan entre sí y el mapa deja de leerse.
    """
    grandes = cat.loc[cat["clase_modelable"], "clase"].value_counts().head(N_FAMILIAS_ETIQUETADAS)
    centros = np.array([coords[(cat["clase"] == fam).to_numpy()].mean(axis=0) for fam in grandes.index])
    nombres = [_acortar(f.replace(" family", "").replace(" superfamily", ""))
               for f in grandes.index]
    fig.add_trace(go.Scatter3d(
        x=centros[:, 0], y=centros[:, 1], z=centros[:, 2],
        mode="text", showlegend=False, text=nombres,
        textfont=dict(size=10, color=TINTA, family=MONO), hoverinfo="skip",
    ))


def _ejes(fig: go.Figure, altura: int, puntos, anotacion: dict | None = None) -> None:
    """Sin números en los ejes: no significan nada para el usuario y distraen.

    Los rangos se fijan al tamaño real de la nube con un margen chico. Si se dejan
    automáticos, Plotly deja muchísimo aire alrededor y los puntos quedan diminutos.
    """
    bajo, alto = puntos.min(axis=0), puntos.max(axis=0)
    margen = (alto - bajo) * 0.05
    eje = dict(showticklabels=False, title="", showbackground=True,
               backgroundcolor=SUPERFICIE, gridcolor=GRILLA, zerolinecolor=EJES,
               linecolor=EJES, zeroline=False)
    fig.update_layout(
        height=altura, margin=dict(l=24, r=24, t=0, b=0),
        paper_bgcolor=SUPERFICIE, plot_bgcolor=SUPERFICIE,
        font=dict(family=MONO, size=10, color=TINTA),
        scene=dict(
            xaxis={**eje, "range": [bajo[0] - margen[0], alto[0] + margen[0]]},
            yaxis={**eje, "range": [bajo[1] - margen[1], alto[1] + margen[1]]},
            zaxis={**eje, "range": [bajo[2] - margen[2], alto[2] + margen[2]]},
            aspectmode="data",
            camera=CAMARA_INICIAL,
            annotations=[anotacion] if anotacion else [],
        ),
        legend=dict(orientation="h", yanchor="top", y=1.0, x=0,
                    bgcolor="rgba(9,9,11,0.85)", bordercolor=EJES, borderwidth=1,
                    font=dict(size=10, color=TINTA, family=MONO)),
        hoverlabel=dict(bgcolor=FONDO_TOOLTIP, bordercolor=EJES,
                        font=dict(family=MONO, size=11, color=TINTA_CLARA)),
        hovermode="closest",
        # Si el usuario giró el mapa y después mueve el deslizante del umbral, la
        # vista se mantiene. Plotly solo resetea la cámara cuando este valor cambia.
        uirevision="mapa-venomscope",
    )
