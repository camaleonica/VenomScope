"""Seguimiento: lo que el laboratorio ya estudió vuelve a alimentar al sistema.

El circuito se cortaba en el análisis: el sistema decía "mirá esta", el laboratorio la
estudiaba y el sistema no se enteraba. Si después llegaba otra variante de la misma
proteína, volvía a aparecer como novedad, aunque ya estuviera resuelta.

Acá el laboratorio marca una muestra como estudiada y dice a qué familia pertenece. Esa
muestra pasa a ser parte de lo que el sistema conoce: sus parientes dejan de ser novedad y
el plan se rearma sin ella. La novedad siempre es relativa a lo conocido, y esto hace que
lo conocido crezca con el uso.

Qué NO hace, a propósito: no reentrena el clasificador. Una familia con una sola muestra no
alcanza para aprenderla, y cambiar el modelo en caliente sin que nadie lo revise sería
justo lo que este proyecto evita. Lo que cambia es la memoria con la que se mide la
novedad, que es simple de explicar y de deshacer.

El libro es un CSV chico y legible (datos/seguimiento.csv): se puede abrir en Excel, copiar a
otra máquina o borrar. Se escribe entero en un archivo temporal y se renombra, así que un
corte a la mitad no lo deja roto.

Nada de este módulo conoce Streamlit.
"""
import csv
import hashlib
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from venomscope.validacion import validar

PREFIJO = "LAB-"                          # accession de las muestras confirmadas
GRUPO = "laboratorio"
ESPECIE = "muestra confirmada por el laboratorio"
RUTA = (Path(os.environ.get("VENOMSCOPE_DATOS") or Path(__file__).resolve().parents[1] / "datos")
        / "seguimiento.csv")
CAMPOS = ["nombre", "secuencia", "familia", "es_del_nea", "fecha"]


@dataclass(frozen=True)
class Confirmada:
    nombre: str
    secuencia: str                        # ya normalizada y validada
    familia: str
    es_del_nea: bool | None
    fecha: str                            # ISO, hasta el minuto


def es_confirmada(accession) -> bool:
    return str(accession).startswith(PREFIJO)


def nueva(nombre: str, secuencia: str, familia: str, es_del_nea: bool | None, ahora: datetime | None = None) -> Confirmada:
    """Arma una confirmación revisando que tenga sentido. Si no, ValueError con el motivo."""
    nombre, familia = nombre.strip(), familia.strip()
    if not nombre:
        raise ValueError("Falta el nombre de la muestra.")
    if not familia:
        raise ValueError("Falta la familia confirmada.")
    v = validar(secuencia)
    if not v.es_valida:
        raise ValueError("La secuencia no es válida: " + " ".join(v.errores))
    ahora = ahora or datetime.now()
    return Confirmada(nombre, v.secuencia, familia, es_del_nea, ahora.strftime("%Y-%m-%d %H:%M"))


def firma_de(confirmadas: list[Confirmada]) -> str:
    """Una huella corta del contenido: cambia cuando cambia lo que el sistema sabe. Vacío si
    no hay nada. Sirve para saber cuándo hay que rehacer el motor y los análisis."""
    if not confirmadas:
        return ""
    texto = "\n".join(f"{c.secuencia}|{c.familia}|{c.es_del_nea}" for c in confirmadas)
    return hashlib.sha256(texto.encode()).hexdigest()[:12]


def _a_texto(valor: bool | None) -> str:
    return {True: "sí", False: "no", None: ""}[valor]


def _de_texto(texto: str) -> bool | None:
    return {"sí": True, "no": False}.get(texto.strip().lower())


class Libro:
    """Las muestras confirmadas, guardadas en un CSV."""

    def __init__(self, ruta: Path | str | None = None):
        self.ruta = Path(ruta) if ruta else RUTA

    def leer(self) -> list[Confirmada]:
        if not self.ruta.exists():
            return []
        with open(self.ruta, newline="", encoding="utf-8") as f:
            filas = list(csv.DictReader(f))
        return [Confirmada(r["nombre"], r["secuencia"], r["familia"], _de_texto(r.get("es_del_nea") or ""),
                           r.get("fecha") or "")
                for r in filas if r.get("nombre") and r.get("secuencia") and r.get("familia")]

    def _escribir(self, confirmadas: list[Confirmada]) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", dir=self.ruta.parent, suffix=".tmp", delete=False,
                                         newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(CAMPOS)
            for c in confirmadas:
                w.writerow([c.nombre, c.secuencia, c.familia, _a_texto(c.es_del_nea), c.fecha])
        os.replace(f.name, self.ruta)

    def agregar(self, c: Confirmada) -> None:
        """Suma una confirmación. Si esa secuencia ya estaba, se reemplaza (por ejemplo, para
        corregir la familia) en vez de duplicarla."""
        self._escribir([x for x in self.leer() if x.secuencia != c.secuencia] + [c])

    def deshacer(self) -> Confirmada | None:
        """Saca la última confirmación y la devuelve (None si no había)."""
        actuales = self.leer()
        if not actuales:
            return None
        self._escribir(actuales[:-1])
        return actuales[-1]

    def vaciar(self) -> None:
        if self.ruta.exists():
            self._escribir([])

    def firma(self) -> str:
        return firma_de(self.leer())


def filas_catalogo(confirmadas: list[Confirmada], columnas) -> pd.DataFrame:
    """Las confirmadas con la forma de filas del catálogo, para sumarlas a la referencia.

    Llevan accession LAB-001, LAB-002... y `clase_modelable` en falso: el clasificador ya está
    entrenado y no las usa. Cualquier columna del catálogo que no se conozca queda vacía.
    """
    filas = []
    for i, c in enumerate(confirmadas, start=1):
        sabido = {
            "accession": f"{PREFIJO}{i:03d}", "nombre_proteina": c.nombre, "especie": ESPECIE,
            "genero_consultado": "", "organism_id": 0, "familia_proteica": c.familia,
            "familia_nivel1": c.familia, "familia_valida": True, "grupo": GRUPO,
            "en_nea": bool(c.es_del_nea), "largo": len(c.secuencia), "peptido_corto": False,
            "sequence": c.secuencia, "clase": c.familia, "clase_modelable": False,
        }
        filas.append({col: sabido.get(col) for col in columnas})
    return pd.DataFrame(filas, columns=list(columnas))
