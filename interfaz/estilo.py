"""El aspecto de la app: la hoja de estilos, el encabezado y el ícono de la pestaña.

Los colores son los del mapa 3D y de `.streamlit/config.toml`, para que todo se vea igual.
Tres tonos tienen significado y se usan siempre igual, acompañados de texto:

    naranja  prioridad alta  / novedosa            (el naranja de "tu secuencia" en el mapa)
    ámbar    prioridad media / algo distinta
    azul     prioridad baja  / parecida a algo conocido

Tipografía: la del sistema, porque la app tiene que andar sin internet y no se puede
bajar ninguna. Los números y las secuencias van en monoespaciada.

Qué toca esta hoja de Streamlit y qué no: solo los `data-testid` que Streamlit mantiene
hace años (métricas, pestañas, contenedor principal). Lo demás son clases propias `vs-*`,
que no dependen de cómo Streamlit arme su página por dentro.
"""
from pathlib import Path

import streamlit as st

from interfaz import componentes

ICONO = Path(__file__).with_name("icono.png")

CSS = """
:root{--vs-fondo:#09090b;--vs-sup:#18181b;--vs-borde:#27272a;--vs-borde-2:#3f3f46;
--vs-texto:#e4e4e7;--vs-tenue:#a1a1aa;--vs-suave:#c4c4cc;
--vs-mono:"JetBrains Mono",SFMono-Regular,Menlo,Consolas,monospace}
.vs-n-alta{--c:#d95926;--ct:#f2906a;--cf:rgba(217,89,38,.14)}
.vs-n-media{--c:#d9a21c;--ct:#ecc462;--cf:rgba(217,162,28,.14)}
.vs-n-baja{--c:#3987e5;--ct:#82b3f1;--cf:rgba(57,135,229,.14)}
.vs-n-nula{--c:#71717a;--ct:#a1a1aa;--cf:rgba(113,113,122,.14)}

[data-testid="stMainBlockContainer"]{max-width:1200px;padding-top:3.5rem;overflow:visible}
header[data-testid="stHeader"]{background-color:transparent;z-index:1}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li{max-width:74ch}

/* Texto justificado. Va por contenedor con nombre (st.container(key=...)) y no suelto en el
   HTML, para que el texto siga siendo markdown normal. Solo en párrafos anchos: justificar
   una columna angosta abre huecos feos entre las palabras. */
[class*="st-key-texto_justificado"] [data-testid="stMarkdownContainer"] p{text-align:justify}

button[data-baseweb="tab"]{padding:.75rem 1.15rem}
button[data-baseweb="tab"] p{font-size:1rem;font-weight:500}

[data-testid="stMetric"]{background:var(--vs-sup);border:1px solid var(--vs-borde);
border-radius:6px;padding:.8rem 1rem}
[data-testid="stMetricValue"]{font-family:var(--vs-mono);font-size:2rem;font-weight:600;letter-spacing:-.03em}
[class*="st-key-resumen_"] [data-testid="stMetric"]{background:none;border:0;padding:0}

.vs-hero{display:flex;align-items:center;gap:1rem;margin-bottom:.6rem;padding-bottom:1.1rem;
border-bottom:1px solid var(--vs-borde)}
.vs-hero svg{flex:none;width:48px;height:48px}
.vs-hero h1.vs-titulo{margin:0;padding:0;font-size:1.9rem;font-weight:650;letter-spacing:-.025em;line-height:1.1}
.vs-lema{margin-top:.3rem;color:var(--vs-tenue);font-size:1.02rem}

.vs-etiqueta{font-size:.875rem;color:var(--vs-tenue)}
.vs-cifra{font-family:var(--vs-mono);font-weight:600;color:var(--vs-texto)}

.vs-insignia{display:flex;flex-direction:column;justify-content:center;gap:.2rem;min-height:5.4rem;
margin-top:.3rem;padding:.7rem 1rem;background:var(--cf);border:1px solid var(--c);
border-left-width:6px;border-radius:6px}
.vs-insignia-nivel{font-size:2.1rem;font-weight:650;line-height:1.05;letter-spacing:-.02em;color:var(--ct)}
.vs-insignia-nota{font-size:.9rem;color:var(--vs-suave)}

.vs-escala{margin:.8rem 0 1.1rem;padding:.9rem 0 .8rem;background:var(--vs-sup);
border:1px solid var(--vs-borde);border-radius:6px}
.vs-escala-tit{padding:0 1.2rem;font-size:.875rem;color:var(--vs-tenue)}
.vs-escala-cuerpo{padding:2.2rem 1.2rem 0}
.vs-pista{position:relative;display:flex;gap:2px;height:14px}
.vs-zona{background:var(--c);opacity:.38;border-radius:2px}
.vs-zona.vs-zona-activa{opacity:1}
.vs-marca{position:absolute;left:var(--p);top:-7px;bottom:-7px;width:3px;margin-left:-1.5px;
background:var(--vs-texto);border-radius:2px;animation:vs-llegar .7s cubic-bezier(.2,.8,.2,1)}
.vs-marca-etq{position:absolute;bottom:100%;left:50%;transform:translateX(-50%);margin-bottom:5px;
padding:.05rem .45rem;background:var(--vs-texto);color:var(--vs-fondo);border-radius:3px;
font:600 .85rem var(--vs-mono)}
@keyframes vs-llegar{from{left:0}}
.vs-nombres,.vs-numeros{display:flex;gap:2px}
.vs-nombres span{padding-top:.55rem;font-size:.85rem;color:var(--vs-tenue);white-space:nowrap}
.vs-nombres span.vs-nombre-activo{font-weight:650;color:var(--ct)}
.vs-numeros span{padding-top:.15rem;font:.75rem var(--vs-mono);color:#8b8b94}
.vs-numeros span.vs-fin{display:flex;justify-content:space-between;gap:.5rem}
.vs-fin em{font-style:normal}

.vs-veredicto{max-width:74ch;margin:.2rem 0 .9rem;padding:.15rem 0 .15rem .95rem;
border-left:3px solid var(--c);font-size:1.08rem;line-height:1.5}
.vs-veredicto strong{font-weight:650}

.vs-dist{margin:.9rem 0 .6rem}
.vs-dist-barra{display:flex;gap:2px;height:12px}
.vs-dist-barra span{min-width:6px;background:var(--c);border-radius:2px}
.vs-dist-ley{display:flex;flex-wrap:wrap;gap:.35rem 1.5rem;margin-top:.6rem;font-size:.9rem;color:var(--vs-tenue)}
.vs-ley i{display:inline-block;width:.7rem;height:.7rem;margin-right:.45rem;background:var(--c,#71717a);border-radius:2px}
.vs-ley i.vs-ley-plan{background:#e4e4e7;border-radius:50%}
.vs-ley i.vs-ley-banda{background:rgba(255,255,255,.14)}
.vs-ley b{font-family:var(--vs-mono);font-weight:600;color:var(--vs-texto)}

.vs-tarjetas{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:.8rem;margin:.4rem 0 1.2rem}
.vs-tarjeta{display:flex;flex-direction:column;gap:.35rem;min-width:0;padding:.8rem .95rem;
background:var(--vs-sup);border:1px solid var(--vs-borde);border-top:3px solid var(--c);border-radius:6px}
.vs-tarjeta-cab{display:flex;justify-content:space-between;align-items:baseline;gap:.6rem}
.vs-tarjeta-id{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font:600 .95rem var(--vs-mono)}
.vs-nivel{flex:none;font-size:.85rem;font-weight:650;color:var(--ct)}
.vs-tarjeta-fam{font-size:.95rem;line-height:1.35}
.vs-tarjeta-sub{font-size:.85rem;line-height:1.35;color:var(--vs-tenue)}
.vs-mini{display:flex;align-items:center;gap:.6rem;margin-top:.25rem;font-size:.8rem;color:var(--vs-tenue)}
.vs-mini-barra{flex:1;height:6px;overflow:hidden;background:var(--vs-borde);border-radius:3px}
.vs-mini-barra i{display:block;height:100%;background:var(--c)}
.vs-mini b{font:600 .85rem var(--vs-mono);color:var(--vs-texto)}

.vs-pasos{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:.7rem;margin:.6rem 0 1rem}
.vs-paso{--c:#71717a;--ct:#a1a1aa;display:flex;flex-direction:column;gap:.45rem;padding:.9rem 1rem;
background:var(--vs-sup);border:1px solid var(--vs-borde);border-top:3px solid var(--c);border-radius:6px}
.vs-paso.vs-paso-ia{--c:#3987e5;--ct:#82b3f1}
.vs-paso-n{font:600 .85rem var(--vs-mono);color:var(--vs-tenue)}
.vs-paso-tit{font-size:1.08rem;font-weight:650}
.vs-paso-txt{flex:1;font-size:.92rem;line-height:1.45;color:var(--vs-suave)}
.vs-paso-tipo{font-size:.82rem;font-weight:650;color:var(--ct)}

.vs-cifras{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem;margin:.7rem 0 .4rem}
.vs-cifras div{padding:.55rem .65rem;background:var(--vs-fondo);border:1px solid var(--vs-borde);border-radius:6px}
.vs-cifras b{display:block;font:600 1.4rem var(--vs-mono);letter-spacing:-.03em}
.vs-cifras span{font-size:.8rem;color:var(--vs-tenue)}

.vs-criterios{display:flex;flex-direction:column;gap:.6rem;margin-top:.6rem}
.vs-criterio{display:flex;gap:.7rem;align-items:baseline;font-size:.95rem;line-height:1.45}
.vs-chip{flex:none;min-width:3.8rem;padding:.05rem .5rem;text-align:center;font-size:.85rem;font-weight:650;
text-transform:capitalize;color:var(--ct);background:var(--cf);border:1px solid var(--c);border-radius:4px}

.vs-arbol,.vs-curva{margin:.4rem 0 .5rem;padding:.6rem .5rem;overflow-x:auto;background:var(--vs-sup);
border:1px solid var(--vs-borde);border-radius:6px}
.vs-arbol svg,.vs-curva svg{display:block;width:100%;height:auto;min-width:560px;font-family:inherit}
.vs-curva svg{max-width:520px;min-width:420px}
.vs-banda{fill:rgba(255,255,255,.045)}
.vs-rama{fill:none;stroke:#52525b;stroke-width:1.4;stroke-linejoin:round}
.vs-rama.vs-rama-hallazgo{stroke:#a1a1aa;stroke-width:2}
.vs-corte{stroke:#e4e4e7;stroke-width:1;stroke-dasharray:4 4;opacity:.55}
.vs-punto{fill:var(--c)}
.vs-plan-marca{fill:#e4e4e7}
.vs-plan-num{fill:#09090b;font:600 12px var(--vs-mono)}
.vs-arbol-nombre{fill:#c4c4cc;font-size:12.5px}
.vs-arbol-nombre.vs-arbol-sel{fill:#fff;font-weight:650}
.vs-arbol-eje,.vs-arbol-n{fill:#8b8b94;font-size:11px}
.vs-leyenda-arbol{margin:.2rem 0 1rem}
.vs-grilla{stroke:#27272a;stroke-width:1}
.vs-linea-plan{fill:none;stroke:#e4e4e7;stroke-width:2.5;stroke-linejoin:round}
.vs-linea-ranking{fill:none;stroke:#8b8b94;stroke-width:2;stroke-dasharray:5 4;stroke-linejoin:round}
.vs-punto-plan{fill:#e4e4e7}
.vs-punto-ranking{fill:#8b8b94}
.vs-etq-plan{fill:#e4e4e7;font-size:12px;font-weight:650}
.vs-etq-ranking{fill:#a1a1aa;font-size:12px}

@media (max-width:640px){
.vs-hero svg{width:38px;height:38px}
.vs-hero h1.vs-titulo{font-size:1.5rem}
.vs-escala-cuerpo{padding-inline:.8rem}
.vs-nombres span{font-size:.72rem}
}
@media (prefers-reduced-motion:reduce){.vs-marca{animation:none}}
"""


def mostrar_html(codigo: str) -> None:
    """Muestra un fragmento de HTML (los de `componentes`)."""
    st.markdown(codigo, unsafe_allow_html=True)


def encabezado() -> None:
    """La hoja de estilos y el título. Va todo en una sola llamada para que la hoja de
    estilos no deje un hueco en blanco arriba de la página."""
    st.markdown(
        f"<style>{CSS}</style>\n\n"
        + componentes.encabezado("VenomScope",
                                 "Qué péptidos de la fauna del noreste argentino vale la pena investigar."),
        unsafe_allow_html=True)


def icono():
    """El ícono de la pestaña del navegador, o None si falta el archivo (no vale la pena
    que la app no abra por eso)."""
    try:
        from PIL import Image
        return Image.open(ICONO)
    except Exception:
        return None
