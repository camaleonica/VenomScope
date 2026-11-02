"""Secuencias de ejemplo para la demo en vivo, cada una cuenta una parte de la historia."""

EJEMPLOS = {
    "Toxina conocida: fosfolipasa de yarará (NEA)": {
        "secuencia": "SLFELGKMILQETGKNPAKSYGAYYCYCGWGGQGQPKDATDRCCYVHKCCYKKLTGCNPKKDRYSYSWKDKTIVCGENNSCLKELCECDKAVAICLRENLNTYNKKYRYYLKPLCKKADAC",
        "nea": "Sí",
        "nota": "Ya está en el catálogo (Bothrops alternatus): el sistema la reconoce y le da prioridad baja.",
    },
    "Péptido corto: de la familia que originó el captopril": {
        "secuencia": "QWPRPQIPP",
        "nea": "Sí",
        "nota": "Péptido potenciador de bradiquinina de 9 aminoácidos, como el que dio origen al captopril.",
    },
    "Toxina de afuera: ziconotida (caracol marino)": {
        "secuencia": "CKGKGAKCSRLMYDCCTGSCRSGKC",
        "nea": "No",
        "nota": "Hoy es un analgésico aprobado. No se parece a nada del catálogo regional: el sistema la marca como novedosa.",
    },
    "Secuencia con errores de lectura": {
        "secuencia": "MKTLLXTLVVVTIVCLDLGBTLKC",
        "nea": "No sé",
        "nota": "Tiene letras que no son aminoácidos: el sistema avisa en vez de inventar un resultado.",
    },
}
