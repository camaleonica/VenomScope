"""Piezas del diseño editorial: títulos mixtos, marcadores, resaltador y fotos.

Las pantallas no escriben estilos: arman la página con estas piezas, y todo el
aspecto vive en `estilo.css`. Para cambiar un color o un tamaño se toca ese
archivo y nada más.

Las fotos van en `assets/img/` con el nombre exacto de FOTOS. Para poner una
foto de verdad alcanza con reemplazar el archivo de muestra por otro con el
mismo nombre: no hay que tocar código. Se muestran siempre en blanco y negro
(filtro en el CSS), aunque el archivo sea a color.
"""
import base64
import html
import re
from pathlib import Path

import streamlit as st

CARPETA_FOTOS = Path(__file__).resolve().parents[1] / "assets" / "img"
_CSS = Path(__file__).with_name("estilo.css")

# nombre -> (proporción, tamaño recomendado en píxeles, qué foto va)
FOTOS = {
    "portada": ("3:4", (1200, 1600), "Rana o escuerzo sobre fondo liso"),
    "biologia": ("1:1", (1200, 1200), "Escorpión sobre fondo liso"),
    "cierre": ("16:9", (1920, 1080), "Muda de piel de serpiente sobre fondo liso"),
}


def aplicar_estilo():
    """Carga el CSS en la página. Va una vez, al principio de app.py."""
    st.html(f"<style>{_CSS.read_text()}</style>")


def titulo(texto: str, nivel: int = 2, clase: str = "vs-titulo") -> str:
    """Título grande con algunas letras en tipografía de píxeles.

    Las letras entre corchetes van en píxeles y `|` corta la línea:
    titulo("Ven[o]m|Sc[o]pe") -> "Venom" / "Scope", con las dos "o" pixeladas.
    El texto completo queda en aria-label, así un lector de pantalla lo lee
    entero aunque esté partido en pedazos.
    """
    plano = html.escape(texto.replace("[", "").replace("]", "").replace("|", " "))
    cuerpo = re.sub(r"\[([^\]]+)\]", r'<span class="vs-pixel">\1</span>', html.escape(texto))
    cuerpo = cuerpo.replace("|", "<br>")
    return (f'<div class="{clase}" role="heading" aria-level="{nivel}" aria-label="{plano}">'
            f'<span aria-hidden="true">{cuerpo}</span></div>')


def marcador(numero: int, total: int, nombre: str) -> str:
    """El marcador de sección de arriba a la derecha: 02 / 05 — BIOLOGÍA."""
    return (f'<div class="vs-marcador"><span>{numero:02d} / {total:02d}</span>'
            f'<span>{html.escape(nombre)}</span></div>')


def marca(frase: str) -> str:
    """Una frase corta pasada con resaltador."""
    return f'<mark class="vs-marca">{frase}</mark>'


def numero(n: int) -> str:
    """La numeración chica 01, 02, 03 al lado de cada ítem."""
    return f'<span class="vs-n">{n:02d}</span>'


@st.cache_data(show_spinner=False)
def _como_data_uri(ruta: str, modificado: float) -> str:
    """La foto embebida en la página. `modificado` está para que, si alguien
    reemplaza el archivo, se vuelva a leer en vez de usar la versión guardada."""
    tipo = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}[ruta.rsplit(".", 1)[1]]
    return f"data:image/{tipo};base64," + base64.b64encode(Path(ruta).read_bytes()).decode()


def ruta_foto(nombre: str) -> Path | None:
    for extension in ("jpg", "jpeg", "png", "webp"):
        ruta = CARPETA_FOTOS / f"{nombre}.{extension}"
        if ruta.exists():
            return ruta
    return None


def foto(nombre: str) -> str:
    """Una foto en blanco y negro con su proporción. Si falta el archivo, un recuadro
    que dice qué foto va ahí, así el hueco se ve y la app no se rompe."""
    proporcion, (ancho, alto), descripcion = FOTOS[nombre]
    abre = f'<figure class="vs-foto" style="aspect-ratio: {proporcion.replace(":", " / ")}">'
    ruta = ruta_foto(nombre)
    if ruta is None:
        return (f'{abre}<div class="vs-foto-falta">Foto B/N {proporcion} · {ancho}×{alto}'
                f"<br>{html.escape(descripcion)}</div></figure>")
    src = _como_data_uri(str(ruta), ruta.stat().st_mtime)
    return f'{abre}<img src="{src}" alt="{html.escape(descripcion)}"></figure>'


def bloque(contenido: str):
    """Escribe un pedazo de HTML del diseño. Sin líneas en blanco adentro: si no,
    Streamlit lo interpreta como Markdown y rompe el maquetado."""
    st.markdown(re.sub(r"\n\s*", " ", contenido.strip()), unsafe_allow_html=True)


def seccion(nombre: str, oscura: bool = False):
    """Una sección a todo el ancho, blanca o negra. Se usa con `with`."""
    return st.container(key=f"{'negra' if oscura else 'blanca'}_{nombre}")
