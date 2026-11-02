# VenomScope

Ayuda a un laboratorio a decidir **qué péptidos de toxinas de la fauna del noreste argentino vale la pena investigar**. Recibe una secuencia de aminoácidos (o una campaña entera) y devuelve, para cada una, a qué familia proteica se parece, qué tan novedosa es respecto del catálogo regional y qué prioridad de investigación merece.

TPO de Inteligencia Artificial, UADE, 2do cuatrimestre 2026.

## Instalación (una sola vez)

Requiere **Python 3.12** e internet solo para este paso.

```bash
git clone https://github.com/camaleonica/VenomScope.git
cd VenomScope

# 1. Entorno virtual con las librerías
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
#   (Windows: .venv\Scripts\pip install -r requirements.txt)

# 2. Descargar el modelo ESM-2 (~150 MB) y generar los archivos del modelo (~1 minuto)
HF_HUB_OFFLINE=0 .venv/bin/python scripts/construir_artefactos.py
```

El paso 2 descarga ESM-2 la primera vez y después genera `artifacts/embeddings.npy`, `artifacts/clasificador.joblib` y `artifacts/config.json`, además de mostrar las métricas del modelo.

> ¿No tenés Python 3.12? Con [uv](https://docs.astral.sh/uv/): `uv python install 3.12` y `uv venv --python 3.12 .venv`, y después `uv pip install --python .venv/bin/python -r requirements.txt`.

## Usar la app

```bash
.venv/bin/streamlit run app.py
```

Se abre en el navegador (`http://localhost:8501`). **Funciona sin internet.**

- **Analizar una secuencia**: pegar una secuencia o elegir un ejemplo.
- **Analizar una campaña**: subir un FASTA o CSV (o usar la campaña de demostración) y descargar los resultados ordenados por prioridad.
- **Cómo leer los resultados**: explicación para quien no es especialista.

Archivos de ejemplo en `ejemplos/` (las variantes "del NEA" son secuencias del catálogo con mutaciones al azar: sirven para la demo, no son muestras reales).

## Tests

```bash
.venv/bin/python -m pytest
```

## Cómo está armado

```
secuencia → validacion → embeddings (ESM-2) → clasificador (familia + confianza)
                                            → novedad (vecinos del catálogo, puntaje 0-100)
                                            → prioridad (reglas explícitas) → pantalla
```

| Archivo | Qué hace |
|---|---|
| `app.py` | Interfaz (Streamlit) |
| `venomscope/validacion.py` | Chequeo de la secuencia (mismas reglas que el Notebook 1) |
| `venomscope/embeddings.py` | Secuencia → vector de 480 números con ESM-2 (**idéntico al Notebook 2**) |
| `venomscope/clasificador.py` | Familia proteica más probable |
| `venomscope/novedad.py` | Puntaje de novedad y vecinos más parecidos |
| `venomscope/prioridad.py` | Reglas de prioridad (todas en un solo lugar, editables) |
| `venomscope/analisis.py` | Une todas las piezas |
| `venomscope/lectura.py` | Lectura de archivos FASTA y CSV |
| `scripts/construir_artefactos.py` | Genera los archivos del modelo y mide su desempeño |

Los notebooks de Colab (catálogo y modelo) son la fuente de las decisiones; la app las reproduce. Si se cambia cómo se calculan los embeddings en uno, hay que cambiarlo en el otro.
