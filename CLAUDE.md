# VenomScope — contexto del proyecto

## Qué es
Trabajo Práctico Obligatorio (TPO) grupal de Inteligencia Artificial, UADE, 2do cuatrimestre 2026.

VenomScope ayuda a un laboratorio a decidir **qué péptidos de toxinas de la fauna del noreste argentino (NEA) vale la pena investigar**. Recibe una secuencia de aminoácidos y devuelve, en segundos:
1. a qué **familia proteica** conocida se parece,
2. qué tan **novedosa** es respecto del catálogo regional,
3. qué **prioridad** de investigación merece.

Problema de negocio: una campaña de muestreo deja decenas o cientos de secuencias; analizarlas a mano lleva horas, así que se estudian las que "llaman la atención" y el resto queda olvidado. El error caro es gastar meses de laboratorio en el candidato equivocado o dejar enterrado el que no se parecía a nada conocido.

## Requisitos de la cátedra que condicionan el código
- Hay que mostrar un **prototipo funcionando en vivo** en una defensa de 15 minutos. Si no abre, el grupo desaprueba.
- **Tiene que funcionar sin internet y en CPU** (notebook personal, sin GPU, sin depender del wifi del aula).
- La audiencia es "Gerencia Comercial y Técnica": la interfaz tiene que ser clara para alguien que no sabe biología ni IA. Nada de jerga sin explicar.
- Suma puntos combinar técnicas (ML + reglas) y analizar limitaciones: qué pasa cuando la IA se equivoca y cómo se protege al usuario.
- Ortografía y prolijidad cuentan: todos los textos visibles en español correcto.

## Qué ya existe (hecho en Google Colab)
**Notebook 1 — catálogo:** descarga de UniProt (Swiss-Prot, keyword KW-0800 "Toxin") toxinas de 24 géneros del NEA en 5 grupos (serpiente, escorpion, arana, anfibio, insecto). Limpia y genera `catalogo_nea.csv`: 584 secuencias.
- Filtros: solo los 20 aminoácidos estándar (`ACDEFGHIKLMNPQRSTVWY`), sin fragmentos (campo `fragment` de UniProt), largo entre 5 y 600, sin duplicados.
- La clase a predecir es la **familia proteica de primer nivel** (`familia_nivel1`), NO la especie. Decisión de producto: el laboratorio ya sabe de qué animal sacó la muestra; lo que no sabe es a qué familia funcional pertenece.
- 518 secuencias "modelables" (`clase_modelable == True`, 24 familias con ≥5 ejemplos). 66 reservadas (familias raras o sin familia) para **evaluar el detector de novedad**.
- Desbalance ~15x entre clases → se evalúa con macro-F1 y validación cruzada estratificada, no con accuracy.

Columnas conocidas de `catalogo_nea.csv`: `accession, nombre_proteina, especie, genero_consultado, organism_id, familia_proteica, familia_nivel1, familia_valida, grupo, largo, peptido_corto, sequence, clase, clase_modelable, en_nea` (verificar contra el archivo real).

**Notebook 2 — modelo (en curso):** genera embeddings con ESM-2.
- Modelo: `facebook/esm2_t12_35M_UR50D` (Hugging Face, ~150 MB, corre en CPU), dimensión 480.
- Un vector por secuencia = **promedio de los vectores por aminoácido, excluyendo tokens especiales y de relleno** (máscara con `attention_mask` y `tokenizer.all_special_ids`). `torch.no_grad()`, `model.eval()`.
- Pendiente en el notebook: visualizar el espacio (UMAP/t-SNE), línea de base, clasificador sobre embeddings, análisis de errores, detector de novedad por distancia a vecinos, exportar.

## Regla crítica
La app **debe calcular embeddings exactamente igual que el notebook** (mismo modelo, mismo pooling con máscara, misma normalización de la secuencia: mayúsculas y sin espacios). Si difieren, el clasificador y el detector de novedad dan cualquier cosa sin dar error. Esta lógica va en un único módulo y tiene un test.

## Contrato de archivos entre notebook y app (a confirmar con el grupo)
El notebook exporta a `artifacts/`:
- `catalogo_nea.csv` — el catálogo
- `embeddings.npy` — matriz (n_secuencias × 480), mismo orden que el CSV
- `clasificador.joblib` — modelo de scikit-learn entrenado sobre embeddings
- `config.json` — nombre del modelo ESM, umbrales del detector de novedad, versión

Mientras esos archivos no existan, la app debe poder generarlos por su cuenta a partir de `catalogo_nea.csv` con un script (`scripts/construir_artefactos.py`) usando un clasificador simple (k-NN o regresión logística), para no bloquear el desarrollo.

## Lo que hace la app (Streamlit)
Entrada: una secuencia pegada o un archivo FASTA/CSV con varias.

Validación: avisar claramente si hay letras no estándar, si el largo está fuera de 5–600, o si está vacía.

Salida por secuencia:
- Familia predicha + confianza, y advertencia si la confianza es baja.
- Puntaje de novedad (distancia a los vecinos más cercanos del catálogo) con una explicación en lenguaje simple.
- Los k vecinos más parecidos del catálogo (nombre, especie, familia, si es del NEA).
- Prioridad (alta / media / baja) calculada con **reglas explícitas y explicadas**, combinando novedad, confianza y si es especie del NEA. Las reglas exactas se definen con el grupo; dejarlas en un único lugar fácil de editar.
- Aviso si es un péptido corto (<20 aa): su embedding es menos confiable.

Modo lote: tabla ordenada por prioridad, descargable como CSV. Es el caso de uso real (una campaña entera).

## Stack y estructura
- Python 3.11+, entorno virtual (`venv`), `requirements.txt` con versiones fijas.
- Streamlit, transformers, torch (CPU), scikit-learn, pandas, numpy, joblib.
- Modelo ESM-2 descargado una vez y usado offline (`HF_HUB_OFFLINE=1` en la demo).

```
venomscope/
├── app.py                  # interfaz Streamlit
├── venomscope/
│   ├── embeddings.py       # ESM-2 + pooling (idéntico al notebook)
│   ├── validacion.py       # chequeo de secuencias
│   ├── clasificador.py     # carga y predicción
│   ├── novedad.py          # puntaje de novedad y vecinos
│   └── prioridad.py        # reglas de prioridad
├── scripts/construir_artefactos.py
├── artifacts/              # salidas del notebook (no versionar archivos grandes)
├── notebooks/              # copias de los notebooks de Colab
├── tests/
├── requirements.txt
└── README.md               # cómo instalar y correr, paso a paso
```

## Convenciones
- Código, comentarios y textos de la interfaz en español.
- Preguntar al grupo antes de cambiar decisiones compartidas (contrato de archivos, reglas de prioridad).
