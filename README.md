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

# 2. Descargar ESM-2 (~150 MB) y generar los archivos del modelo (~1 minuto)
HF_HUB_OFFLINE=0 .venv/bin/python scripts/construir_artefactos.py
```

El paso 2 descarga el modelo la primera vez y después genera los cinco archivos de `artifacts/`, además de mostrar las métricas.

> ¿No tenés Python 3.12? Con [uv](https://docs.astral.sh/uv/): `uv python install 3.12`, `uv venv --python 3.12 .venv` y `uv pip install --python .venv/bin/python -r requirements.txt`.

## Usar la app

```bash
.venv/bin/streamlit run app.py
```

Se abre en `http://localhost:8501`. **Funciona sin internet.**

- **Qué es esto**: la introducción para quien no sabe biología: el problema, la biología mínima, cómo funciona y qué tan bien anda.
- **Una secuencia**: pegar una secuencia o elegir un ejemplo.
- **Una campaña entera**: subir un FASTA o CSV (o usar la campaña de prueba) y descargar los resultados ordenados por prioridad.
- **Cómo leer esto**: qué significa cada número y qué no puede hacer el sistema.

Archivos de ejemplo en `ejemplos/`. Las muestras "del NEA" de la campaña de prueba son secuencias del catálogo con mutaciones al azar: sirven para la demo, no son muestras reales.

## Tests

```bash
.venv/bin/python -m pytest
```

## Cómo está armado

```
secuencia → validación → embeddings (ESM-2) → clasificador (familia + confianza)
                                            → novedad (vecinos del catálogo, 0-100)
                                            → prioridad (reglas explícitas) → pantalla
```

Dos capas, como un backend y un frontend:

- **`venomscope/`, el motor.** Todo el cálculo. No sabe que existe una web: se puede probar solo y lo usa también el script que genera los artefactos.
- **`interfaz/`, la web.** Solo muestra. Le pide todo al motor a través de `venomscope/analisis.py`.

`tests/test_arquitectura.py` falla si el motor llega a importar algo de la interfaz, así la separación se mantiene sola.

| Archivo | Qué hace |
|---|---|
| `app.py` | Arma la página: encabezado, motor y pestañas |
| `interfaz/estilo.py` | La hoja de estilos, el encabezado y el ícono de la pestaña |
| `interfaz/componentes.py` | Las piezas visuales en HTML (insignia, escala de novedad, tarjetas); se prueban solas |
| `interfaz/comun.py` | Carga del motor, control de sensibilidad y barra lateral |
| `interfaz/resultado.py` | La tarjeta de resultado de una secuencia |
| `interfaz/intro.py`, `una.py`, `campana.py`, `ayuda.py` | Una pestaña cada uno |
| `venomscope/validacion.py` | Chequeo de la secuencia (mismas reglas que el Notebook 1) |
| `venomscope/embeddings.py` | Secuencia → 480 números con ESM-2 (**idéntico al Notebook 2**) |
| `venomscope/clasificador.py` | Familia proteica más probable y confianza |
| `venomscope/novedad.py` | Puntaje de novedad y vecinos más parecidos |
| `venomscope/plan.py` | Plan de laboratorio: agrupa la campaña en hallazgos y elige qué muestras mandar con un presupuesto |
| `interfaz/plan_lab.py` | La sección del plan en la pestaña de campaña |
| `scripts/simular_plan.py` | Simula campañas con datos reales y mide el plan contra el ranking por novedad |
| `venomscope/seguimiento.py` | El libro de muestras que el laboratorio confirmó (`datos/seguimiento.csv`) |
| `interfaz/seguimiento_lab.py` | La sección de seguimiento en la pestaña de campaña |
| `scripts/simular_seguimiento.py` | Mide con datos reales cuánto baja la novedad de los parientes al confirmar una muestra |
| `venomscope/cache_embeddings.py` | Caché en disco de embeddings: no se recalcula lo ya calculado |
| `scripts/precalentar_cache.py` | Llena la caché con los ejemplos y las campañas de prueba antes de la demo |
| `interfaz/informe.py` | El informe descargable de la campaña (HTML, se imprime a PDF) |
| `venomscope/prioridad.py` | Reglas de prioridad (todas en un solo lugar, editables) |
| `venomscope/mapa.py` | El mapa 3D del catálogo |
| `venomscope/analisis.py` | Une todas las piezas; la app solo usa esto |
| `venomscope/lectura.py` | Lectura de FASTA y CSV |
| `venomscope/contrato.py` | Qué tiene que haber en `artifacts/` para que la app arranque |
| `scripts/construir_artefactos.py` | Genera los artefactos y mide el desempeño |
| `.streamlit/config.toml` | Tema claro y tipografías locales |
| `interfaz/estilo.css`, `interfaz/editorial.py` | El diseño editorial: todo el aspecto y sus piezas |
| `static/fuentes/` | Space Grotesk, Silkscreen y JetBrains Mono (licencia OFL), para no depender de internet |
| `assets/img/` | Las fotos de la introducción (ver su README) |

## El plan de laboratorio

Ordenar por novedad no alcanza: si diez muestras son variantes de una misma proteína rara, las diez
quedan arriba y cuentan como un solo hallazgo. El plan elige las muestras que representan a toda la
campaña (cobertura ponderada por novedad, algoritmo goloso, garantía de al menos el 63% del óptimo).

El corte que define "hallazgo" no se eligió a ojo: se calibra contra las familias reales del catálogo.
La mejora se mide con `scripts/simular_plan.py` y queda en `resultados/plan_simulacion.json`:

    .venv/bin/python scripts/simular_plan.py

En 300 campañas simuladas con datos reales, con 3 cupos descubre 2.76 de 4 familias nuevas contra 1.48
de ordenar por novedad (la mejora tiene intervalo de confianza del 95% de +1.20 a +1.36). Con muchos
cupos la ventaja se achica: está en los presupuestos chicos.

## Seguimiento del laboratorio

El circuito se cortaba en el análisis: el sistema decía "mirá esta", el laboratorio la estudiaba y el
sistema no se enteraba. Ahora el laboratorio confirma la muestra y su familia, y esa muestra pasa a ser
parte de lo que el sistema conoce: sus parientes dejan de aparecer como novedad y el plan se rearma.

- Se guarda en `datos/seguimiento.csv` (se abre en Excel, se copia o se borra). El motor original no se
  modifica: se usa una copia ampliada, y "Deshacer" y "Vaciar" lo revierten.
- **No reentrena el clasificador**, a propósito: una familia con una sola muestra no alcanza para
  aprenderla. Lo que cambia es la memoria con la que se mide la novedad.
- Medido en datos reales (`scripts/simular_seguimiento.py`, 17 familias): tras confirmar **una** muestra,
  los parientes marcados como novedosos bajan de **88% a 65%**, y con dos a 51%. Una segunda familia
  desconocida y sin relación no se mueve (**86% a 86%**). El efecto es parcial: una familia diversa
  necesita más de una muestra.

## Informe de la campaña

El botón "Descargar el informe de la campaña" genera un único archivo HTML: resumen, plan de
laboratorio con el árbol de hallazgos, todas las muestras y los límites. No usa nada externo, se abre sin
internet y, con "Imprimir > Guardar como PDF", sale en A4. Usa exactamente los mismos números que la
pantalla.

## Caché de embeddings

Calcular el embedding con ESM-2 es lo único lento. La caché (`cache/embeddings/`, una entrada por
secuencia) guarda lo ya calculado: volver a analizar una campaña o confirmar una muestra no espera al
modelo. No modifica `embeddings.py`; si algún día cambia esa lógica, se sube `VERSION` en
`cache_embeddings.py` y las entradas viejas dejan de usarse. Antes de la defensa:

    .venv/bin/python scripts/precalentar_cache.py

## El contrato con el notebook

Los artefactos se pueden generar de dos maneras y las dos tienen que producir lo mismo: la sección 7 del `Notebook2_Modelo.ipynb` (en Colab, guarda en Drive) o `scripts/construir_artefactos.py` (acá). Son cinco archivos en `artifacts/`:

| Archivo | Qué es |
|---|---|
| `catalogo_nea.csv` | El catálogo, 584 secuencias (sale del Notebook 1) |
| `embeddings.npy` | 480 números por secuencia, en el mismo orden que el CSV |
| `clasificador.joblib` | El clasificador entrenado |
| `proyeccion3d.joblib` | El mapa 3D precalculado, para que se dibuje siempre igual |
| `config.json` | Umbrales, escala de novedad, curva de sensibilidad y métricas |

La lista y las claves que necesita `config.json` están en `venomscope/contrato.py`. Si falta algo, la app dice qué falta al arrancar en vez de romperse después.

**La regla crítica:** la app calcula los embeddings exactamente igual que el notebook (mismo modelo, mismo promedio con máscara, misma normalización). Si difirieran, el clasificador recibiría números distintos a los que vio al entrenarse y se equivocaría sin dar ningún error. Hay un test que lo verifica, y `config.json` guarda el nombre del modelo para que la app se niegue a arrancar con artefactos de otro.

Los notebooks (`Notebook1_Catalogo_regional.ipynb` y `Notebook2_Modelo.ipynb`) están en la raíz del repo y se sincronizan desde Colab con *Archivo → Guardar una copia en GitHub*, eligiendo el mismo repo y la misma ruta. Va en un solo sentido: después de que alguien pushee desde acá, hay que volver a abrir el notebook desde GitHub antes de seguir editándolo en Colab.

## Qué tan bien anda

| | con IA | sin IA |
|---|---|---|
| Identificar la familia, examen normal | 93 | 81 |
| Identificar la familia, examen difícil | 66 | 48 |

En puntos sobre 100 (macro-F1, validación cruzada). El examen difícil agrupa las secuencias casi idénticas y las reparte por grupo entero, así el modelo no puede aprobar de memoria: es el número realista, y ahí la ventaja de la IA se agranda.

El detector de novedad avisa sobre el 98% de las toxinas de familias que nunca vio (las 66 que el Notebook 1 reservó justamente para eso).
