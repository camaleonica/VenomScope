import pytest

from venomscope.lectura import leer_archivo, leer_csv, leer_fasta


def test_fasta_varias_secuencias_en_varias_lineas():
    texto = ">muestra_1 yarará\nMKTLL\nLTLVV\n\n>muestra_2\nQWPRPQIPP\n"
    assert leer_fasta(texto) == [("muestra_1", "MKTLLLTLVV", None), ("muestra_2", "QWPRPQIPP", None)]


def test_fasta_aplica_nea_a_todas():
    assert all(n is True for _, _, n in leer_fasta(">a\nAAAAA\n>b\nCCCCC", es_del_nea=True))


def test_texto_sin_encabezado_es_una_sola_secuencia():
    assert leer_fasta("MKTLL\nLTLVV") == [("Muestra 1", "MKTLL\nLTLVV", None)]


def test_texto_vacio():
    assert leer_fasta("  \n ") == []


def test_encabezado_sin_nombre():
    assert leer_fasta(">\nAAAAA")[0][0] == "Muestra 1"


def test_csv_con_nombre_y_nea():
    contenido = "Nombre,Secuencia,NEA\nm1,MKTLL,sí\nm2,QWPRP,no\nm3,AAAAA,\n"
    assert leer_csv(contenido) == [("m1", "MKTLL", True), ("m2", "QWPRP", False), ("m3", "AAAAA", None)]


def test_csv_con_punto_y_coma_y_sin_nombre():
    assert leer_csv("sequence;otra\nMKTLL;x\n") == [("Muestra 1", "MKTLL", None)]


def test_csv_sin_columna_de_secuencia_da_error_claro():
    with pytest.raises(ValueError, match="secuencia"):
        leer_csv("nombre,algo\nm1,MKT\n")


def test_leer_archivo_decide_por_extension():
    assert leer_archivo("c.csv", b"secuencia\nAAAAA\n")[0][1] == "AAAAA"
    assert leer_archivo("c.fasta", b">x\nAAAAA\n")[0][0] == "x"
