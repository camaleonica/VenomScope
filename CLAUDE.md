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
- Secciones 2 a 7 escritas (espacio de embeddings, líneas de base, clasificador, análisis de errores, detector de novedad, exportar). Corrido de punta a punta fuera de Colab el 2026-11-03: da los mismos artefactos y métricas que `scripts/construir_artefactos.py`. La primera celda instala scikit-learn y joblib en las versiones de `requirements.txt`: con la 1.6.1 que trae Colab el examen agrupado (4.5) daba 58 en vez de 66 y el `.joblib` no era compatible con la app.

## Regla crítica
La app **debe calcular embeddings exactamente igual que el notebook** (mismo modelo, mismo pooling con máscara, misma normalización de la secuencia: mayúsculas y sin espacios). Si difieren, el clasificador y el detector de novedad dan cualquier cosa sin dar error. Esta lógica va en un único módulo y tiene un test.

## Contrato de archivos entre notebook y app (cerrado)
Son cinco archivos en `artifacts/`, y los generan por igual la sección 7 del Notebook 2 o `scripts/construir_artefactos.py`:
- `catalogo_nea.csv` — el catálogo
- `embeddings.npy` — matriz (n_secuencias × 480), mismo orden que el CSV
- `clasificador.joblib` — regresión logística entrenada sobre los embeddings
- `proyeccion3d.joblib` — el mapa 3D precalculado (PCA guardada + coordenadas)
- `config.json` — modelo ESM, umbrales, escala de novedad, curva de sensibilidad y métricas

**La lista vive en `venomscope/contrato.py`.** Si se agrega algo que la app lea de `config.json`, va ahí: el `Motor` verifica la carpeta al arrancar y un test lo comprueba. Cualquier cambio en ese contrato hay que hacerlo en los dos lados a la vez.

## Decisiones ya tomadas
- **Umbrales de novedad**: 75 (algo distinta) y 90 (novedosa). El 90 salió de bajar el 95 original: detecta 89% de las familias nunca vistas en vez de 71%, a cambio de 10% de falsas alarmas en vez de 5%. El usuario lo mueve desde la app entre 80 y 99.
- **Reglas de prioridad**: están en `venomscope/prioridad.py`, en la sección REGLAS, y son explícitas a propósito.
- **Qué número reportar**: los dos. 93 sobre 100 en el examen estándar y 66 en el examen que agrupa las secuencias casi idénticas, que es el realista.
- **Sin emojis en la interfaz** (hay un test que lo verifica).
- **Diseño editorial** (reemplazó al tema oscuro): blanco y negro puros, un único acento `#C7DDF2` como resaltador, grilla de 1px, títulos enormes con letras en Silkscreen. Todo el aspecto vive en `interfaz/estilo.css` y las piezas en `interfaz/editorial.py`. El mapa 3D es la excepción: bloque negro con su paleta propia. Tipografías en `static/fuentes/` (anda sin internet); fotos en `assets/img/` (ver su README).

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
├── app.py                  # arma la página (título, motor, pestañas)
├── interfaz/               # Streamlit: una pestaña por archivo, solo muestra
├── venomscope/             # el motor: no importa Streamlit (lo verifica tests/test_arquitectura.py)
│   ├── embeddings.py       # ESM-2 + pooling (idéntico al notebook)
│   ├── validacion.py       # chequeo de secuencias
│   ├── clasificador.py     # carga y predicción
│   ├── novedad.py          # puntaje de novedad y vecinos
│   ├── prioridad.py        # reglas de prioridad
│   ├── plan.py             # plan de laboratorio: hallazgos y elección con presupuesto
│   ├── seguimiento.py      # muestras que el laboratorio confirmó (datos/seguimiento.csv)
│   └── cache_embeddings.py # caché de embeddings (envuelve a embeber, no lo modifica)
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
