"""Chequeo de una secuencia antes de analizarla.

Usa las mismas reglas que la limpieza del Notebook 1: si la app aceptara algo
que el catálogo descartó, el modelo estaría trabajando fuera de lo que conoce.
Los mensajes están pensados para alguien que no sabe biología.
"""
import re
from dataclasses import dataclass, field

AMINOACIDOS_VALIDOS = set("ACDEFGHIKLMNPQRSTVWY")   # los 20 estándar
LARGO_MIN, LARGO_MAX = 5, 600                       # igual que el Notebook 1
UMBRAL_PEPTIDO_CORTO = 20                           # igual que el Notebook 1


@dataclass
class ResultadoValidacion:
    secuencia: str                     # ya normalizada
    errores: list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)

    @property
    def es_valida(self) -> bool:
        return not self.errores

    @property
    def es_peptido_corto(self) -> bool:
        return len(self.secuencia) < UMBRAL_PEPTIDO_CORTO


def normalizar(secuencia: str) -> str:
    """Mayúsculas y sin espacios ni saltos de línea.

    El notebook solo saca espacios en los bordes, pero las secuencias del
    catálogo no tienen espacios internos, así que para ellas el resultado es
    idéntico. Sacar los internos permite pegar secuencias partidas en líneas.
    """
    return re.sub(r"\s+", "", secuencia).upper()


def validar(secuencia: str) -> ResultadoValidacion:
    r = ResultadoValidacion(secuencia=normalizar(secuencia))
    s = r.secuencia

    if not s:
        r.errores.append("La secuencia está vacía.")
        return r

    invalidas = [(i + 1, letra) for i, letra in enumerate(s) if letra not in AMINOACIDOS_VALIDOS]
    if invalidas:
        detalle = ", ".join(f"{letra} (posición {pos})" for pos, letra in invalidas[:10])
        if len(invalidas) > 10:
            detalle += f" y {len(invalidas) - 10} más"
        r.errores.append(
            "La secuencia tiene letras que no corresponden a ninguno de los 20 "
            f"aminoácidos estándar: {detalle}. Suelen indicar posiciones que el "
            "laboratorio no pudo leer con certeza."
        )

    if not LARGO_MIN <= len(s) <= LARGO_MAX:
        r.errores.append(
            f"La secuencia tiene {len(s)} aminoácidos; el sistema trabaja con "
            f"secuencias de entre {LARGO_MIN} y {LARGO_MAX}, que es el rango del catálogo."
        )

    if r.es_valida and r.es_peptido_corto:
        r.advertencias.append(
            f"Es un péptido corto ({len(s)} aminoácidos). Puede ser muy valioso, pero "
            "con tan poca información los resultados son menos confiables."
        )

    return r
