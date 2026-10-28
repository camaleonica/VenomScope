from venomscope.novedad import NIVEL_CONOCIDA, NIVEL_MEDIA, NIVEL_NOVEDOSA
from venomscope.prioridad import ALTA, BAJA, MEDIA, calcular


def test_novedosa_es_alta():
    assert calcular(NIVEL_NOVEDOSA, 98, baja_confianza=False).nivel == ALTA


def test_algo_distinta_es_media():
    assert calcular(NIVEL_MEDIA, 80, baja_confianza=False).nivel == MEDIA


def test_conocida_y_segura_es_baja():
    p = calcular(NIVEL_CONOCIDA, 10, baja_confianza=False)
    assert p.nivel == BAJA
    assert len(p.razones) == 1


def test_confianza_baja_sube_a_media():
    p = calcular(NIVEL_CONOCIDA, 10, baja_confianza=True)
    assert p.nivel == MEDIA
    assert len(p.razones) == 2


def test_nea_desempata_media_a_alta():
    assert calcular(NIVEL_MEDIA, 80, baja_confianza=False, es_del_nea=True).nivel == ALTA


def test_nea_no_rescata_lo_conocido():
    assert calcular(NIVEL_CONOCIDA, 10, baja_confianza=False, es_del_nea=True).nivel == BAJA


def test_siempre_hay_razones():
    for nivel in (NIVEL_CONOCIDA, NIVEL_MEDIA, NIVEL_NOVEDOSA):
        assert calcular(nivel, 50, baja_confianza=False).razones
