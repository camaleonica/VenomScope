"""Los nombres de los grupos animales, escritos como se leen.

Antes esto tenía un emoji por grupo. Se sacaron: en una pantalla para gerencia
quedaban informales, y en algunas computadoras se ven como cuadraditos.
"""

NOMBRES = {
    "serpiente": "Serpiente",
    "arana": "Araña",
    "escorpion": "Escorpión",
    "anfibio": "Anfibio",
    "insecto": "Insecto",
    "laboratorio": "Del laboratorio",
}


def nombre(grupo: str) -> str:
    return NOMBRES.get(grupo, grupo)
