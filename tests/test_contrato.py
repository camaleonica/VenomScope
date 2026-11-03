"""El contrato entre el Notebook 2 y la app.

Estos tests existen porque el notebook y el script se editan por separado y es
fácil que uno agregue algo que el otro no genera. Cuando pasa, la app revienta
en la demo y no antes.
"""
import json

import pytest

from venomscope import contrato
from venomscope.analisis import ARTIFACTS, Motor

if not (ARTIFACTS / "config.json").exists():
    pytest.skip("Faltan artefactos: correr scripts/construir_artefactos.py", allow_module_level=True)


def test_los_artefactos_cumplen_el_contrato():
    assert contrato.problemas(ARTIFACTS) == []


def test_la_app_lee_todas_las_claves_que_el_contrato_promete():
    """Si la app usa algo que no está en el contrato, el notebook no lo va a generar."""
    config = json.loads((ARTIFACTS / "config.json").read_text())
    usadas = [
        config["modelo_esm"], config["dim"], config["n_catalogo"], config["n_reservadas"],
        config["clasificador"]["umbral_confianza"],
        config["novedad"]["k_vecinos"], config["novedad"]["escala"],
        config["novedad"]["umbrales_puntaje"], config["novedad"]["curva_umbrales"],
        config["mapa3d"]["varianza_conservada"],
        config["metricas"]["macro_f1_esm2"], config["metricas"]["macro_f1_esm2_agrupado"],
        config["metricas"]["macro_f1_composicion"],
        config["metricas"]["macro_f1_composicion_agrupado"],
        config["metricas"]["reservadas_nivel_medio_o_alto"],
    ]
    assert all(v is not None for v in usadas)


def test_falta_un_archivo_y_el_mensaje_dice_cual(tmp_path):
    (tmp_path / "config.json").write_text("{}")
    fallas = contrato.problemas(tmp_path)
    assert any("embeddings.npy" in f for f in fallas)
    assert any("proyeccion3d.joblib" in f for f in fallas)
    with pytest.raises(FileNotFoundError, match="construir_artefactos"):
        contrato.verificar(tmp_path)


def test_config_viejo_sin_las_claves_nuevas_se_detecta(tmp_path):
    """El caso real: artefactos generados antes de agregar el mapa y la curva."""
    for nombre in contrato.ARCHIVOS:
        (tmp_path / nombre).write_bytes(b"")
    viejo = json.loads((ARTIFACTS / "config.json").read_text())
    del viejo["novedad"]["curva_umbrales"], viejo["mapa3d"]
    (tmp_path / "config.json").write_text(json.dumps(viejo))

    fallas = contrato.problemas(tmp_path)
    assert len(fallas) == 1
    assert "curva_umbrales" in fallas[0] and "mapa3d.varianza_conservada" in fallas[0]


def test_el_motor_rechaza_artefactos_de_otro_modelo(tmp_path):
    for nombre in contrato.ARCHIVOS:
        (tmp_path / nombre).write_bytes((ARTIFACTS / nombre).read_bytes())
    config = json.loads((tmp_path / "config.json").read_text())
    config["modelo_esm"] = "facebook/esm2_t33_650M_UR50D"
    (tmp_path / "config.json").write_text(json.dumps(config))

    with pytest.raises(ValueError, match="regenerarlos"):
        Motor(tmp_path)


def test_el_umbral_por_defecto_es_90():
    config = json.loads((ARTIFACTS / "config.json").read_text())
    assert config["novedad"]["umbrales_puntaje"] == {"medio": 75, "alto": 90}


def test_la_medicion_honesta_esta_y_es_menor_que_la_normal():
    m = json.loads((ARTIFACTS / "config.json").read_text())["metricas"]
    assert m["macro_f1_esm2_agrupado"] < m["macro_f1_esm2"]
    # lo interesante: en el examen difícil la ventaja de la IA se agranda
    ventaja_normal = m["macro_f1_esm2"] / m["macro_f1_composicion"]
    ventaja_dificil = m["macro_f1_esm2_agrupado"] / m["macro_f1_composicion_agrupado"]
    assert ventaja_dificil > ventaja_normal
