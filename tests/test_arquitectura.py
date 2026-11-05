"""Las dos capas no se mezclan: el motor (`venomscope`) no sabe que existe la web.

Así el motor se puede probar y usar sin interfaz (lo usa también
scripts/construir_artefactos.py), y la interfaz se puede cambiar sin tocar el
cálculo. Este test hace que la regla se cumpla sola en vez de depender de que
alguien se acuerde.
"""
import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def _importa(archivo: Path) -> set[str]:
    """Los paquetes que importa un archivo, solo el primer nombre (streamlit, numpy...)."""
    modulos = set()
    for nodo in ast.walk(ast.parse(archivo.read_text())):
        if isinstance(nodo, ast.Import):
            modulos |= {a.name.split(".")[0] for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            modulos.add(nodo.module.split(".")[0])
    return modulos


def test_el_motor_no_depende_de_la_interfaz():
    prohibidos = {"streamlit", "interfaz"}
    violaciones = {f.name: _importa(f) & prohibidos
                   for f in sorted((RAIZ / "venomscope").glob("*.py"))}
    violaciones = {k: v for k, v in violaciones.items() if v}
    assert not violaciones, f"El motor importa cosas de la interfaz: {violaciones}"


def test_la_interfaz_existe_y_se_revisa():
    """Si alguien renombra la carpeta, el test de arriba no puede quedar revisando nada."""
    assert len(list((RAIZ / "interfaz").glob("*.py"))) >= 5
    assert len(list((RAIZ / "venomscope").glob("*.py"))) >= 5
