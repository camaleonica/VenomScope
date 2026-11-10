"""Los nombres de los grupos animales, escritos como se leen.

Los nombres (`nombre`) nunca llevan emoji: en las tablas y en las pantallas de
gerencia quedaban informales. Eso se mantiene.

Los íconos (`icono`) existen aparte y se usan en **un solo lugar**: la ventanita
que aparece al apoyar el mouse sobre un punto del mapa 3D. Ahí el mapa se
proyecta ante un público que no sabe biología, y ver de un vistazo si el punto
es una serpiente o una rana explica más rápido que leerlo. La ventanita la
dibuja Plotly, que no admite imágenes: por eso el ícono es un carácter y no un
dibujo del diseño.

El ícono siempre acompaña al nombre escrito, nunca lo reemplaza: si la
computadora no tiene tipografía de emojis y muestra un cuadradito, al lado
sigue diciendo "Serpiente" y no se pierde nada.
"""

NOMBRES = {
    "serpiente": "Serpiente",
    "arana": "Araña",
    "escorpion": "Escorpión",
    "anfibio": "Anfibio",
    "insecto": "Insecto",
    "laboratorio": "Del laboratorio",
}

# Solo para la ventanita del mapa 3D (venomscope/mapa.py). Ver el test
# tests/test_sin_emojis.py, que comprueba que no se escapen a ningún otro lado.
# "laboratorio" no está acá a propósito: no es un grupo animal, son las muestras
# que el propio laboratorio confirmó. En el mapa aparece solo con su nombre.
ICONOS = {
    "serpiente": "\U0001F40D",   # serpiente
    "arana": "\U0001F577",       # araña
    "escorpion": "\U0001F982",   # escorpión
    "anfibio": "\U0001F438",     # rana (el grupo son ranas del género Phyllomedusa)
    "insecto": "\U0001F41D",     # abeja (abejas y avispas son la mayoría del grupo)
}


def nombre(grupo: str) -> str:
    return NOMBRES.get(grupo, grupo)


def icono(grupo: str) -> str:
    """El pictograma del grupo, o cadena vacía si el grupo no es conocido."""
    return ICONOS.get(grupo, "")
