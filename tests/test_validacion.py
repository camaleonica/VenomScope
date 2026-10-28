from venomscope.validacion import normalizar, validar


def test_normalizar_pasa_a_mayusculas_y_saca_espacios():
    assert normalizar("  mkt llt\nlvv\t") == "MKTLLTLVV"


def test_secuencia_valida_sin_avisos():
    r = validar("MKTLLLTLVVVTIVCLDLGYTLKCHNTQ")
    assert r.es_valida
    assert r.errores == []
    assert r.advertencias == []
    assert r.secuencia == "MKTLLLTLVVVTIVCLDLGYTLKCHNTQ"


def test_secuencia_vacia():
    r = validar("   ")
    assert not r.es_valida
    assert "vacía" in r.errores[0]


def test_letras_no_estandar_se_informan_con_su_posicion():
    r = validar("MKTXLLB")
    assert not r.es_valida
    assert "X (posición 4)" in r.errores[0]
    assert "B (posición 7)" in r.errores[0]


def test_demasiado_corta():
    r = validar("MKTL")
    assert not r.es_valida
    assert "4 aminoácidos" in r.errores[0]


def test_demasiado_larga():
    r = validar("A" * 601)
    assert not r.es_valida
    assert "601 aminoácidos" in r.errores[0]


def test_limites_exactos_son_validos():
    assert validar("A" * 5).es_valida
    assert validar("A" * 600).es_valida


def test_peptido_corto_es_valido_pero_avisa():
    # Un BPP de 9 aminoácidos (como el que dio origen al captopril)
    r = validar("QWPRPQIPP")
    assert r.es_valida
    assert r.es_peptido_corto
    assert len(r.advertencias) == 1


def test_secuencia_de_20_no_es_corta():
    assert not validar("A" * 20).es_peptido_corto
