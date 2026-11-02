"""Un ícono por grupo animal, para que la pantalla se lea de un vistazo.

El ícono acompaña siempre al nombre del grupo, nunca lo reemplaza: quien no
distinga los emojis tiene que poder leer igual.
"""

ICONOS_GRUPO = {
    "serpiente": "🐍",
    "arana": "🕷️",
    "escorpion": "🦂",
    "anfibio": "🐸",
    "insecto": "🐝",
}

NOMBRES_GRUPO = {
    "serpiente": "serpiente",
    "arana": "araña",
    "escorpion": "escorpión",
    "anfibio": "anfibio",
    "insecto": "insecto",
}


def icono(grupo: str) -> str:
    return ICONOS_GRUPO.get(grupo, "•")


def con_icono(grupo: str) -> str:
    """'🐍 serpiente'. Con el nombre escrito, no solo el dibujito."""
    return f"{icono(grupo)} {NOMBRES_GRUPO.get(grupo, grupo)}"
