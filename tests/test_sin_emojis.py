"""La interfaz no lleva emojis: decisión de producto, la audiencia es gerencia.

Este test existe porque es la clase de cosa que se vuelve a colar sin querer.
"""
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ARCHIVOS = [RAIZ / "app.py", *sorted((RAIZ / "venomscope").glob("*.py"))]


def _emojis(texto: str) -> list[str]:
    """Pictogramas de verdad. Las tildes y la eñe no cuentan, obviamente."""
    return [c for c in texto
            if unicodedata.category(c) == "So" or 0x1F000 <= ord(c) <= 0x1FAFF]


def test_ningun_archivo_de_la_interfaz_tiene_emojis():
    con_emojis = {f.name: set(_emojis(f.read_text())) for f in ARCHIVOS}
    con_emojis = {k: v for k, v in con_emojis.items() if v}
    assert not con_emojis, f"Quedaron emojis: {con_emojis}"


def test_los_ejemplos_y_sus_notas_tampoco():
    from venomscope.ejemplos import EJEMPLOS
    texto = " ".join(k + v["nota"] for k, v in EJEMPLOS.items())
    assert not _emojis(texto)
