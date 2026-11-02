"""Lectura de campañas: texto/archivo FASTA o CSV -> lista de (id, secuencia, es_del_nea).

FASTA es el formato estándar de secuencias:
    >nombre_de_la_muestra
    MKTLLLTLVVVTIVCLDLGYT...
CSV: una columna con la secuencia y, opcionalmente, una con el nombre y otra
que diga si la especie es del NEA (sí/no).
"""
import io

import pandas as pd

COLUMNAS_SECUENCIA = ("secuencia", "sequence", "seq")
COLUMNAS_ID = ("id", "nombre", "muestra", "accession")
COLUMNAS_NEA = ("nea", "en_nea", "es_del_nea", "del_nea")
VALORES_SI = {"si", "sí", "s", "true", "verdadero", "1", "yes", "y", "x"}
VALORES_NO = {"no", "n", "false", "falso", "0"}


def leer_fasta(texto: str, es_del_nea: bool | None = None) -> list[tuple[str, str, bool | None]]:
    """Si el texto no tiene ningún '>', se toma entero como una sola secuencia."""
    if ">" not in texto:
        return [("Muestra 1", texto, es_del_nea)] if texto.strip() else []

    entradas, nombre, partes = [], None, []
    for linea in texto.splitlines():
        linea = linea.strip()
        if linea.startswith(">"):
            if nombre is not None:
                entradas.append((nombre, "".join(partes), es_del_nea))
            nombre = linea[1:].split()[0] if linea[1:].strip() else f"Muestra {len(entradas) + 1}"
            partes = []
        elif linea and nombre is not None:
            partes.append(linea)
    if nombre is not None:
        entradas.append((nombre, "".join(partes), es_del_nea))
    return entradas


def _a_bool(valor) -> bool | None:
    texto = str(valor).strip().lower()
    if texto in VALORES_SI:
        return True
    if texto in VALORES_NO:
        return False
    return None


def _separador(contenido: str) -> str:
    """Coma, punto y coma (Excel en español) o tabulación: el que más aparezca en el encabezado."""
    encabezado = contenido.lstrip().split("\n", 1)[0]
    return max([",", ";", "\t"], key=encabezado.count)


def leer_csv(contenido: str, es_del_nea: bool | None = None) -> list[tuple[str, str, bool | None]]:
    df = pd.read_csv(io.StringIO(contenido), sep=_separador(contenido), dtype=str).fillna("")
    columnas = {c.strip().lower(): c for c in df.columns}

    col_seq = next((columnas[c] for c in COLUMNAS_SECUENCIA if c in columnas), None)
    if col_seq is None:
        raise ValueError(
            "El CSV no tiene una columna con las secuencias. Tiene que llamarse "
            f"'secuencia' (o {', '.join(repr(c) for c in COLUMNAS_SECUENCIA[1:])}). "
            f"Columnas encontradas: {', '.join(df.columns)}."
        )
    col_id = next((columnas[c] for c in COLUMNAS_ID if c in columnas), None)
    col_nea = next((columnas[c] for c in COLUMNAS_NEA if c in columnas), None)

    entradas = []
    for i, fila in df.iterrows():
        nombre = fila[col_id].strip() if col_id and fila[col_id].strip() else f"Muestra {i + 1}"
        nea = _a_bool(fila[col_nea]) if col_nea else es_del_nea
        entradas.append((nombre, fila[col_seq], nea))
    return entradas


def leer_archivo(nombre_archivo: str, contenido: bytes, es_del_nea: bool | None = None):
    texto = contenido.decode("utf-8-sig", errors="replace")
    if nombre_archivo.lower().endswith((".csv", ".tsv")):
        return leer_csv(texto, es_del_nea)
    return leer_fasta(texto, es_del_nea)
