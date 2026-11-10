"""La sección "Seguimiento del laboratorio": cerrar el circuito.

El laboratorio estudia una muestra y la confirma acá. Desde ese momento forma parte de lo
que el sistema conoce: sus parientes dejan de verse como novedad y el plan se rearma sin ella.
Para que se vea el efecto, la pantalla dice cuánto cambió la prioridad alta tras confirmar.

La lógica (guardar, reconocer, sumar a la referencia) está en `venomscope/seguimiento.py` y en
`Motor.con_confirmadas`; acá solo se arma lo que se ve.
"""
import pandas as pd
import streamlit as st

from interfaz.editorial import bloque, subtitulo
from venomscope import prioridad, seguimiento
from venomscope.analisis import Motor

OTRA = "Otra familia (escribir el nombre)"


def _familias_posibles(motor: Motor, probable: str) -> list[str]:
    """La que dice el sistema primero (casi siempre es la correcta), después el resto."""
    cat = motor.catalogo
    conocidas = set(cat.loc[cat["clase_modelable"], "clase"]) | set(
        cat.loc[cat["accession"].map(seguimiento.es_confirmada), "clase"])
    return [probable] + sorted(conocidas - {probable}) + [OTRA]


def mostrar_seguimiento(motor: Motor, resultados: list, altas_ahora: int) -> None:
    analizadas = [r for r in resultados if r.validacion.es_valida and r.prediccion is not None]
    libro = seguimiento.Libro()
    confirmadas = libro.leer()

    bloque(subtitulo(2, "Seguimiento del laboratorio"))
    st.markdown(
        "Cuando el laboratorio estudia una muestra, confirmala acá. Se suma a lo que el sistema conoce: "
        "sus parientes dejan de aparecer como novedad y el plan se rearma sin ella.")

    efecto = st.session_state.get("efecto_seguimiento")
    if efecto:
        st.info(f"Efecto de confirmar «{efecto['muestra']}»: las muestras de prioridad alta pasaron de "
                f"{efecto['altas_antes']} a {altas_ahora}.")

    if analizadas:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            elegida = st.selectbox("Muestra que se estudió", [r.id for r in analizadas], key="seg_muestra")
        r = next(x for x in analizadas if x.id == elegida)
        with c2:
            familia = st.selectbox("Familia confirmada", _familias_posibles(motor, r.prediccion.familia),
                                   key=f"seg_familia_{elegida}",
                                   help="Lo que el laboratorio comprobó, no lo que dijo el sistema.")
        if familia == OTRA:
            familia = st.text_input("Nombre de la familia", key=f"seg_nueva_{elegida}")

        if st.button("Confirmar y sumar a lo que el sistema conoce", key="seg_confirmar"):
            try:
                c = seguimiento.nueva(r.id, r.validacion.secuencia, familia, r.es_del_nea)
            except ValueError as e:
                st.error(str(e))
            else:
                libro.agregar(c)
                st.session_state["efecto_seguimiento"] = {"muestra": r.id, "altas_antes": altas_ahora}
                st.rerun()

    if confirmadas:
        with st.expander(f"Lo que el laboratorio ya confirmó ({len(confirmadas)})"):
            st.dataframe(pd.DataFrame([{"Muestra": c.nombre, "Familia": c.familia, "Confirmada": c.fecha}
                                       for c in confirmadas]), hide_index=True, width="stretch")
            a, b = st.columns(2)
            if a.button("Deshacer la última", key="seg_deshacer"):
                libro.deshacer()
                st.session_state.pop("efecto_seguimiento", None)
                st.rerun()
            if b.button("Vaciar todo", key="seg_vaciar", help="Borra todas las confirmaciones."):
                libro.vaciar()
                st.session_state.pop("efecto_seguimiento", None)
                st.rerun()
    elif not analizadas:
        st.caption("Todavía no hay muestras confirmadas.")


def altas(tabla: pd.DataFrame) -> int:
    """Cuántas muestras de prioridad alta hay en la tabla de resultados."""
    return int((tabla["Prioridad"] == prioridad.ALTA).sum())
