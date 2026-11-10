"""La interfaz no lleva emojis: decisión de producto, la audiencia es gerencia.

Hay una sola excepción, y está acotada acá: los cinco íconos de grupo animal
que aparecen en la ventanita del mapa 3D (venomscope/grupos.py -> ICONOS). El
mapa se proyecta ante gente que no sabe biología y el ícono ubica más rápido
que el nombre en latín. Estos tests comprueban que la excepción no se escape
a ningún otro archivo.

Este test existe porque es la clase de cosa que se vuelve a colar sin querer.
"""
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ICONOS_DEL_MAPA = RAIZ / "venomscope" / "grupos.py"
ARCHIVOS = [RAIZ / "app.py", *sorted((RAIZ / "venomscope").glob("*.py")),
            *sorted((RAIZ / "interfaz").glob("*.py"))]


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


def test_los_iconos_del_mapa_estan_escritos_con_su_codigo():
    """En grupos.py van como \\U0001F40D y no pegados como carácter.

    Así el archivo se puede abrir en cualquier editor sin que se rompa, y el
    test de arriba sigue cubriendo venomscope/grupos.py entero.
    """
    assert not _emojis(ICONOS_DEL_MAPA.read_text())


def test_los_iconos_solo_se_usan_en_el_mapa():
    """La excepción vale para la ventanita del mapa y nada más.

    Si algún día aparecen en una tabla o en un título, este test avisa.
    """
    # Busca quién define el diccionario y quién lo importa de grupos.py. No
    # alcanza con buscar "icono" suelto: "ziconotida" lo contiene, y el ícono de
    # la pestaña del navegador (interfaz/icono.png) es otra cosa.
    busca = re.compile(r"^ICONOS\b|^from venomscope\.grupos import .*\bicono\b", re.M)
    usan = [f.name for f in ARCHIVOS if busca.search(f.read_text())]
    assert usan == ["grupos.py", "mapa.py"], f"Los íconos se usan en: {usan}"


def test_cada_grupo_animal_tiene_su_icono():
    """Los cinco grupos de animales llevan ícono. "laboratorio" no, a propósito:
    son las muestras que el laboratorio confirmó, no un animal."""
    from venomscope.grupos import ICONOS, NOMBRES, icono
    assert set(ICONOS) == set(NOMBRES) - {"laboratorio"}
    assert all(icono(g) for g in ICONOS)


def test_un_grupo_sin_icono_no_rompe_nada():
    """Sin ícono la ventanita del mapa muestra solo el nombre, que es lo que importa."""
    from venomscope.grupos import icono, nombre
    assert icono("laboratorio") == "" and nombre("laboratorio") == "Del laboratorio"
    assert icono("desconocido") == ""
