"""Reglas de prioridad de investigación: alta, media o baja, siempre con sus razones.

Son reglas explícitas (no ML) a propósito: un laboratorio tiene que poder ver
por qué el sistema le recomienda algo y discutirlo.

PROVISORIO: las reglas definitivas las decide el grupo. Todo lo editable está
en este archivo, en la sección REGLAS.
"""
from dataclasses import dataclass, field

from venomscope.novedad import NIVEL_MEDIA, NIVEL_NOVEDOSA

# ---------------------------------------------------------------- REGLAS ----
# 1. "Novedosa" (puntaje >= umbral alto de config.json)      -> ALTA
#    No se parece a nada conocido: puede ser una familia nueva.
# 2. "Algo distinta"                                          -> MEDIA
#    Pariente lejano de algo conocido: puede tener una variante interesante.
# 3. El modelo no está seguro de la familia                   -> al menos MEDIA
#    Conviene que la mire una persona.
# 4. Especie del NEA y prioridad MEDIA                        -> sube a ALTA
#    Es el foco regional del producto; solo desempata, no rescata lo conocido.
# 5. Todo lo demás (parecida a algo conocido, familia segura) -> BAJA
# El péptido corto no cambia la prioridad: solo agrega una advertencia.
SUBIR_SI_NEA = True
# ------------------------------------------------------------------------------

ALTA, MEDIA, BAJA = "Alta", "Media", "Baja"
ORDEN = {ALTA: 0, MEDIA: 1, BAJA: 2}   # para ordenar tablas: Alta primero


@dataclass
class Prioridad:
    nivel: str
    razones: list[str] = field(default_factory=list)


def calcular(nivel_novedad: str, puntaje_novedad: float, baja_confianza: bool,
             es_del_nea: bool | None = None) -> Prioridad:
    razones = []

    if nivel_novedad == NIVEL_NOVEDOSA:
        nivel = ALTA
        razones.append(f"No se parece a nada del catálogo (novedad {puntaje_novedad:.0f}/100): "
                       "podría ser una familia nueva.")
    elif nivel_novedad == NIVEL_MEDIA:
        nivel = MEDIA
        razones.append(f"Es un pariente lejano de toxinas conocidas (novedad {puntaje_novedad:.0f}/100).")
    else:
        nivel = BAJA
        razones.append(f"Se parece mucho a toxinas ya estudiadas (novedad {puntaje_novedad:.0f}/100).")

    if baja_confianza:
        if nivel == BAJA:
            nivel = MEDIA
        razones.append("El sistema no está seguro de a qué familia pertenece: conviene revisarla.")

    if SUBIR_SI_NEA and es_del_nea and nivel == MEDIA:
        nivel = ALTA
        razones.append("Proviene de una especie del NEA, el foco regional del producto.")

    return Prioridad(nivel=nivel, razones=razones)
