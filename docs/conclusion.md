# Conclusión: límites, sesgos y privacidad

Este documento reúne lo que VenomScope **no** puede hacer. Está acá porque una
herramienta que ordena en qué gastar meses de trabajo tiene que venir con sus
límites escritos: si el usuario no sabe cuándo desconfiar, la herramienta deja de
ayudar y empieza a estorbar.

---

## 1. Sesgos

Un sesgo no es un error de programación. Es una inclinación sistemática: el
sistema se equivoca **siempre para el mismo lado**, y por eso no se arregla
corriéndolo de nuevo. VenomScope tiene dos, y los dos vienen de los datos, no del
código.

### 1.1. Sesgo de publicación: el catálogo no es el mundo

El sistema mide qué tan novedosa es una secuencia por su distancia a las toxinas
del catálogo. Pero el catálogo no contiene las toxinas que existen en el noreste
argentino: contiene **las que alguien ya estudió, publicó y cargó en UniProt**.

Esa diferencia no es azarosa. Se investiga más lo peligroso para las personas, lo
fácil de capturar y lo que ya tiene financiamiento. Nuestros propios números lo
muestran:

| Grupo de animales | Secuencias en el catálogo | Porcentaje |
|---|---|---|
| Serpientes | 285 | 48,8% |
| Escorpiones | 136 | 23,3% |
| Arañas | 91 | 15,6% |
| Insectos | 50 | 8,6% |
| Anfibios | 22 | **3,8%** |

Nadie sostendría que los anfibios del NEA producen trece veces menos toxinas que
las serpientes. Lo que hay son trece veces menos publicaciones.

Hay un segundo indicio en el mismo sentido: de los **24 géneros** del NEA que
consultamos en UniProt, solo **16** devolvieron al menos una toxina. Ocho géneros
de la región no tienen una sola secuencia publicada con la que trabajar. El
catálogo final cubre 106 especies.

**Qué consecuencia tiene, dicho para el laboratorio:**

> Una toxina de una especie poco estudiada va a parecer más novedosa de lo que
> realmente es, porque hay menos con qué compararla. El sistema no mide qué tan
> rara es una molécula; mide **qué tan lejos está de lo que la ciencia ya
> miró**. En parte, está midiendo nuestra propia ignorancia.

**Cómo convivimos con esto:**

- Está dicho en la aplicación, en la pantalla "Cómo leer esto", no escondido en
  un anexo.
- Cada resultado muestra **las cinco toxinas más parecidas con su especie y su
  grupo**, así el usuario ve contra qué se lo está comparando. Si las cinco son
  de serpiente y la muestra es de un anfibio, la comparación habla por sí sola.
- Regla de uso que recomendamos: un puntaje de novedad alto en un grupo poco
  representado merece más desconfianza que el mismo puntaje en una serpiente.

**Lo que no hicimos y se podría hacer:** corregir el puntaje según cuántas
secuencias hay del grupo de la muestra. No lo hicimos porque no sabríamos
justificar la fórmula, y preferimos un número honesto con una advertencia clara
antes que un número corregido que nadie pueda explicar.

### 1.2. Desbalance entre familias: unas pocas se llevan casi todo

De las 584 toxinas, 518 quedaron en 24 familias con al menos cinco ejemplos cada
una. Pero el reparto es muy desparejo:

- la familia más numerosa tiene **73** secuencias (toxinas largas de escorpión);
- la más chica tiene **5**;
- la diferencia es de **casi 15 veces**;
- las 6 familias más grandes concentran **297 de las 518 secuencias**, es decir el
  **57%**.

**Qué consecuencia tiene:** el sistema reconoce mucho mejor las familias
frecuentes que las raras. Y las raras son, justamente, las que más interesan a
quien busca algo nuevo. El riesgo es el peor posible: ser menos confiable
exactamente donde más se lo necesita.

**Cómo lo tratamos:**

1. **No medimos con el promedio general.** Usamos una métrica que le da el mismo
   peso a cada familia, grande o chica (macro-F1), con validación cruzada
   estratificada. Si hubiéramos usado el porcentaje de aciertos a secas, el
   desbalance habría quedado tapado: un sistema que contestara siempre la familia
   más común acertaría bastante y no serviría para nada. Medido con la métrica
   correcta, ese sistema tonto saca **1 punto sobre 100**.
2. **El clasificador compensa el desbalance** durante el entrenamiento, dándole
   más peso a los ejemplos de familias chicas.
3. **Reportamos el número incómodo.** Hicimos una segunda evaluación que agrupa
   las secuencias casi idénticas, para que el sistema no pueda aprobar
   reconociendo copias de lo que ya vio. El resultado baja de **93 a 66 puntos**.
   Los dos números están publicados, y el que usamos para hablar del desempeño
   real es el segundo.
4. **Hay una salida de emergencia.** Cuando el sistema no está seguro de la
   familia, lo dice, y esa duda sube la prioridad para que lo mire una persona.
5. **66 toxinas quedaron deliberadamente afuera** del entrenamiento —las de
   familias raras o sin familia asignada— y se usaron para medir el detector de
   novedad contra familias que el sistema nunca vio.

### 1.3. Un sesgo que agregamos a propósito

La regla 4 de prioridad sube a "alta" las muestras del NEA que ya tenían
prioridad media. **Eso es un sesgo regional, y es intencional**: el producto
existe para potenciar la fauna del noreste argentino. Lo dejamos escrito porque un
sesgo elegido y declarado es una decisión de producto; el mismo sesgo sin
declarar sería un defecto oculto.

### 1.4. Un sesgo que estuvimos a punto de introducir

Al principio pensamos descartar los péptidos más cortos, por considerarlos ruido
de la base de datos. Habría sido un error grave. El **captopril**, uno de los
antihipertensivos más vendidos de la historia, salió de un péptido de **nueve
aminoácidos** del veneno de la yarará, una serpiente que está en nuestro propio
catálogo. Ese filtro habría tirado esa molécula sin que nadie se enterara.

Hoy los péptidos cortos se analizan igual que el resto y se marcan con una
advertencia, porque su representación numérica es menos confiable. Lo decimos con
todas las letras: **no pudimos comprobar qué tan bien funciona con péptidos
cortos**, porque los que tenemos son casi todos de una misma familia fácil.

---

## 2. Privacidad y manejo de los datos

### 2.1. Qué dato sensible hay acá

No hay datos personales: VenomScope no trata con personas, ni con pacientes, ni
con identificadores de nadie.

Lo que sí hay es **propiedad intelectual del laboratorio**. Las secuencias de una
campaña de muestreo todavía no publicada son el activo más valioso de un grupo de
investigación. Una secuencia filtrada antes de tiempo puede significar que otro
grupo publique primero y que años de trabajo de campo queden sin crédito. En este
dominio, la confidencialidad no es un trámite legal: es la carrera profesional de
las personas que recolectaron las muestras.

### 2.2. La decisión: todo se procesa en la máquina del laboratorio

Lo normal, hoy, sería resolver esto con un servicio en la nube: se manda la
secuencia a un servidor, se recibe el análisis. Eso implica que cada secuencia sin
publicar sale de la institución y queda en la infraestructura de un tercero.

**VenomScope no manda nada a ninguna parte.** Corre entero en la computadora de
quien lo usa:

| | Dónde ocurre |
|---|---|
| La secuencia que se pega o el archivo que se sube | Queda en la memoria de la computadora |
| El modelo ESM-2 que la traduce a números | Instalado localmente, se descarga una sola vez |
| El catálogo y el clasificador | Archivos en el disco |
| La planilla de resultados | Se descarga a la carpeta del usuario |

Durante la demostración, la aplicación corre con la conexión a internet
deshabilitada de forma explícita, y el programa no recolecta estadísticas de uso.

### 2.3. Un beneficio que no buscábamos

La decisión de funcionar sin internet la tomamos por una razón práctica y bastante
prosaica: no queríamos que la defensa dependiera del wifi del aula.

Resultó ser también la decisión correcta de privacidad. Es el caso poco frecuente
en que la restricción más molesta de un proyecto termina siendo una de sus
mejores propiedades, y conviene decirlo sin fingir que fue un plan maestro.

Tiene un costo real, eso sí: el sistema usa un modelo chico, de unos 150 MB, que
funciona en una notebook común sin placa de video. Un modelo mayor en la nube
probablemente reconocería mejor las familias. Elegimos la versión que el
laboratorio puede correr sin entregarle sus muestras a nadie.

### 2.4. Los datos de origen

El catálogo se construyó con UniProt, una base de datos pública y gratuita de
proteínas. La aplicación enlaza cada toxina a su ficha original, de modo que el
usuario siempre puede ir a la fuente y verificar. La fuente está citada en la
interfaz y en el informe.

### 2.5. Qué quedaría por hacer en un uso real

Somos conscientes de que un despliegue verdadero necesitaría más de lo que un
trabajo práctico puede cubrir:

- **Registro de auditoría**: hoy no se guarda qué se consultó ni cuándo. Para
  defender una decisión meses después, habría que registrarlo, y eso abre su
  propia discusión sobre quién puede leer ese registro.
- **Borrado**: los resultados viven mientras la aplicación está abierta y
  desaparecen al cerrarla. Es privado por simple, no por diseño cuidadoso.
- **Varios usuarios**: no hay cuentas ni permisos. Cualquiera que abra la
  aplicación ve lo que hay.
