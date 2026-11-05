"""Las piezas del diseño editorial (interfaz/editorial.py)."""
from interfaz.editorial import FOTOS, foto, ruta_foto, titulo


def test_el_titulo_mixto_se_lee_entero():
    """Las letras en píxeles parten la palabra en pedazos: el texto completo tiene
    que quedar igual para un lector de pantalla."""
    t = titulo("V[e]nom|Sc[op]e", nivel=1)
    assert 'aria-label="Venom Scope"' in t
    assert t.count('class="vs-pixel"') == 2
    assert "<br>" in t


def test_el_titulo_no_deja_pasar_html():
    assert "<script>" not in titulo("<script>")


def test_cada_hueco_de_foto_tiene_su_archivo():
    """Si alguien borra una foto, la app igual anda (muestra el recuadro), pero
    el repo tiene que traerlas todas."""
    faltan = [n for n in FOTOS if ruta_foto(n) is None]
    assert not faltan, f"Faltan en assets/img/: {faltan}"


def test_sin_archivo_la_foto_dice_que_va_ahi(monkeypatch):
    monkeypatch.setattr("interfaz.editorial.ruta_foto", lambda nombre: None)
    assert "Rana o escuerzo" in foto("portada")
