# Fotos de la app

Son cinco fotos. Si falta alguna, la app no se rompe: muestra un recuadro con las medidas.
Para poner la foto de verdad, reemplazá el archivo por otro **con el mismo nombre**.
No hace falta tocar código.

| Archivo | Proporción | Tamaño mínimo | Dónde aparece | Qué foto |
|---|---|---|---|---|
| `portada.jpg` | 3:4 vertical | 1200 × 1600 | Portada, a la derecha del título | Araña |
| `biologia.jpg` | 3:2 horizontal | 1500 × 1000 | "La biología en un minuto" | Anfibio |
| `ejemplos.jpg` | 3:2 horizontal | 1500 × 1000 | Entrada de "Una secuencia" | Anémona de mar |
| `anemona.jpg` | 1:1 cuadrada | 1200 × 1200 | "Qué no puede hacer" | Anémona de mar |
| `cierre.jpg` | 4:3 horizontal | 1600 × 1200 | "Probalo", al final | Serpiente |

Qué tienen que tener:

- **Un animal aislado sobre fondo oscuro o liso.** Las que mejor funcionan son las de fondo
  negro: se funden con la página en vez de quedar como un recuadro pegado.
- **Licencia libre** (dominio público, CC0 o CC BY, anotando la autoría). Buenos lugares para buscar: Wikimedia Commons, Unsplash, Pexels y la Biodiversity Heritage Library.
- **Van a color**, apenas apagadas para que no griten sobre el fondo negro. Para pasarlas
  todas a blanco y negro se cambia `--foto-color` a 0 en `interfaz/estilo.css`.
- **Hasta 500 KB cada una**: viajan dentro de la página. Si pesan más, exportalas en JPG con calidad 80.
- **La proporción importa**: lo que sobra se recorta para llenar el hueco, así que una
  foto de otra forma puede quedar con el animal cortado. Si la que tenés es de otra
  proporción, cambiá la del hueco en `FOTOS` (interfaz/editorial.py) en vez de recortarla.

Si un archivo falta, la app no se rompe: muestra el recuadro con las medidas.
