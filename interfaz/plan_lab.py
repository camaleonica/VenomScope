"""La sección "Plan de laboratorio" de la pestaña de campaña.

El usuario dice cuántas muestras puede estudiar el laboratorio y el sistema elige cuáles
mandar. Muestra el árbol de parentesco de la campaña con la elección marcada, y cuánto se
gana contra la alternativa de siempre: ordenar por novedad y tomar las primeras.

El cálculo está en `venomscope/plan.py`; acá solo se arma lo que se ve.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
import streamlit as st

from interfaz import componentes
from interfaz.estilo import mostrar_html
from venomscope import plan
from venomscope.analisis import Motor

MAXIMO_CUPOS = 15


@st.cache_resource(show_spinner=False)
def _corte_del_catalogo(_motor: Motor) -> tuple[float, float]:
    """Corte de "hallazgo distinto", calibrado con las familias reales del catálogo.
    Se calcula una vez (el guion bajo evita que Streamlit intente hashear el motor)."""
    cat = _motor.catalogo
    ok = cat["clase_modelable"].to_numpy()
    return plan.calibrar_corte(_motor.detector.X_catalogo[ok], cat.loc[ok, "clase"].to_numpy())


def _plural(n: int, uno: str, varios: str) -> str:
    return uno if n == 1 else varios.format(n=n)


@dataclass
class PlanMostrado:
    """Lo que quedó en pantalla, para que el informe descargable use exactamente lo mismo."""
    armado: plan.PlanArmado
    ids: list[str]              # id de cada muestra analizada, en el orden del plan
    cupos: int


def mostrar_plan(motor: Motor, resultados: list) -> PlanMostrado | None:
    analizadas = [r for r in resultados if r.embedding is not None]
    st.markdown("##### Plan de laboratorio")
    if len(analizadas) < 3:
        st.caption("Hacen falta al menos 3 muestras analizadas para armar un plan.")
        return None

    corte, _ = _corte_del_catalogo(motor)

    st.markdown(
        "Ordenar por novedad no alcanza: si varias muestras son variantes de lo mismo, todas quedan "
        "arriba y gastan cupos en un solo hallazgo. El plan elige las que **representan** a toda la campaña.")
    maximo = min(MAXIMO_CUPOS, len(analizadas))
    # Si antes se analizó una campaña más grande, el valor guardado podría pasarse del nuevo máximo.
    if st.session_state.get("cupos_plan", 1) > maximo:
        st.session_state["cupos_plan"] = maximo
    cupos = st.slider("¿Cuántas muestras puede estudiar el laboratorio?", 1, maximo, min(3, maximo),
                      key="cupos_plan",
                      help="Cada cupo es una muestra que se manda a estudiar. El plan se arma para ese número.")

    armado = plan.armar(np.vstack([r.embedding for r in analizadas]),
                        [r.novedad.puntaje for r in analizadas], corte, maximo)
    elegidas, orden, etiquetas = armado.elegidas, armado.orden, armado.etiquetas
    c_plan, c_ranking = armado.curva_plan, armado.curva_ranking
    cupos = min(cupos, len(elegidas))

    cuando = _plural(cupos, "Con 1 cupo", "Con {n} cupos")
    top = _plural(cupos, "mandando la de mayor novedad", "mandando las {n} de mayor novedad")
    mostrar_html(componentes.veredicto(
        f"{len(analizadas)} muestras, {armado.hallazgos} hallazgos distintos.",
        f"{cuando}, el plan cubre el {c_plan[cupos - 1]:.0%} de lo importante; "
        f"{top} se cubriría el {c_ranking[cupos - 1]:.0%}.", ""))

    # El punto donde seguir gastando cupos casi no rinde: lo más útil para decidir presupuesto.
    suficiente = armado.cupos_suficientes()
    if suficiente is not None and suficiente < cupos:
        st.caption(f"Con {_plural(suficiente, '1 cupo', '{n} cupos')} ya se cubre el 95% de lo importante: "
                   "los cupos que siguen casi no suman.")

    nombres = [r.id for r in analizadas]
    niveles = [r.prioridad.nivel for r in analizadas]
    mostrar_html(componentes.arbol_hallazgos(
        nombres, niveles, armado.Z, etiquetas, corte, {i: k + 1 for k, i in enumerate(orden[:cupos])}))
    mostrar_html(componentes.leyenda_arbol())

    izquierda, derecha = st.columns([3, 2], gap="large")
    with izquierda:
        filas = []
        for lugar, e in enumerate(elegidas[:cupos], start=1):
            r = analizadas[e.indice]
            filas.append({
                "Orden": lugar, "Muestra": r.id, "Prioridad": r.prioridad.nivel,
                "Familia probable": r.prediccion.familia, "Novedad": round(r.novedad.puntaje),
                "Aporta": e.ganancia,
                "Equivale a": armado.equivale_a(e.indice),
            })
        st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch", column_config={
            "Aporta": st.column_config.NumberColumn(
                "Aporta", format="percent", help="Cobertura nueva que suma esta muestra a las anteriores."),
            "Equivale a": st.column_config.NumberColumn(
                "Equivale a", help="Otras muestras del mismo hallazgo: estudiar esta alcanza para todas."),
            "Familia probable": st.column_config.TextColumn(width="large"),
        })
    with derecha:
        mostrar_html(componentes.curva_plan(c_plan, c_ranking, cupos))

    with st.expander("Cómo se arma el plan"):
        st.markdown(
            "- **Hallazgo:** dos muestras cuentan como lo mismo si están más cerca que "
            f"{corte:.2f} (distancia coseno entre embeddings). Ese corte no se eligió a ojo: es el que mejor "
            "reconstruye las familias reales del catálogo.\n"
            "- **Cobertura:** qué parte de lo importante de la campaña queda representada por las muestras "
            "elegidas. Cada muestra pesa según su novedad, así que una variante común casi no cuenta.\n"
            "- **Elección:** algoritmo goloso. Primero la que más cubre sola, después la que más suma a "
            "las anteriores, y así hasta llenar los cupos. Para este tipo de problema el goloso garantiza al "
            "menos el 63% del plan óptimo.\n"
            "- **Evidencia:** en campañas simuladas con datos reales, a igual cantidad de cupos descubre "
            "más familias nuevas que ordenar por novedad. Los números están en `resultados/plan_simulacion.json`.")
    return PlanMostrado(armado, nombres, cupos)
