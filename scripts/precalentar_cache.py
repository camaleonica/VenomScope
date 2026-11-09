"""Calcula una vez los embeddings de los ejemplos y las campañas de prueba y los guarda en la caché.

Para qué. Calcular un embedding con ESM-2 es lo único lento del sistema. Con la caché llena, la
primera vez que se abre la demo ya no espera al modelo: elegir un ejemplo y analizar la campaña
de prueba responden al instante. Correrlo una vez en la notebook de la defensa, con el modelo
descargado, y antes de ensayar.

Uso:  .venv/bin/python scripts/precalentar_cache.py
"""
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from venomscope import cache_embeddings  # noqa: E402
from venomscope.ejemplos import EJEMPLOS  # noqa: E402
from venomscope.lectura import leer_archivo  # noqa: E402
from venomscope.validacion import validar  # noqa: E402


def secuencias_de_demo() -> list[str]:
    """Todas las secuencias válidas de los ejemplos y de las campañas de prueba, sin repetir."""
    crudas = [e["secuencia"] for e in EJEMPLOS.values()]
    for ruta in sorted((RAIZ / "ejemplos").glob("campana_*.csv")):
        crudas += [s for _, s, _ in leer_archivo(ruta.name, ruta.read_bytes(), None)]
    validas = (validar(s) for s in crudas)
    return list(dict.fromkeys(v.secuencia for v in validas if v.es_valida))


def main():
    from venomscope.embeddings import embeber

    secuencias = secuencias_de_demo()
    antes = cache_embeddings.tamano()
    print(f"{len(secuencias)} secuencias de demo; ya había {antes} en la caché ({cache_embeddings.CARPETA}).")
    inicio = time.time()
    cache_embeddings.embeber_con_cache(secuencias, embeber)
    print(f"Listo en {time.time() - inicio:.0f} s. Ahora hay {cache_embeddings.tamano()} secuencias guardadas.")


if __name__ == "__main__":
    main()
