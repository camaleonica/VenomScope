# VenomScope visto como un agente inteligente

Este documento describe qué tipo de sistema es VenomScope, usando el vocabulario
de la materia. No habla de código: habla de qué percibe el sistema, qué decide y
qué hace con esa decisión.

La idea que lo recorre entero es una sola: **VenomScope no decide nada en nombre
del laboratorio.** Mide, ordena y explica. La decisión de gastar meses de trabajo
en un candidato sigue siendo de las personas. Todo lo que sigue es, en el fondo,
la justificación de esa frase.

---

## 1. PEAS: las cuatro preguntas

PEAS es una forma ordenada de describir un sistema inteligente respondiendo
cuatro preguntas: qué significa que le vaya bien, dónde trabaja, qué puede hacer
y qué puede ver.

### Medida de rendimiento: ¿qué significa que le vaya bien?

Lo primero que hay que aclarar es que **el objetivo no es acertar la familia de
cada toxina.** Eso es un medio, no un fin. El objetivo es que el laboratorio
gaste sus meses de trabajo en los candidatos correctos.

De ahí salen cuatro medidas, en orden de importancia para el negocio:

1. **No perder lo valioso.** Que una toxina realmente distinta de todo lo
   conocido no quede enterrada en una planilla. Hoy el sistema avisa en el 89 de
   cada 100 casos de familias que nunca vio, y en 98 de cada 100 si se cuenta
   también el aviso intermedio.
2. **No hacer perder el tiempo.** Que las falsas alarmas sean pocas. Con la
   configuración actual, de cada 100 toxinas ya conocidas marca 10 de más.
3. **Acertar la familia.** 93 puntos sobre 100 en la evaluación estándar y 66 en
   la evaluación exigente, que separa las secuencias casi idénticas para que el
   sistema no pueda aprobar de memoria. El segundo número es el realista.
4. **Poder explicar siempre el porqué.** Una recomendación que nadie puede
   discutir no sirve en un laboratorio. Esta medida no tiene un número: se
   cumple o no se cumple, y hoy se cumple.

El orden importa. Los dos primeros errores no cuestan lo mismo: una falsa alarma
se descarta en diez minutos; una novedad perdida se pierde para siempre. Por eso
el sistema está deliberadamente configurado para marcar de más.

### Ambiente: ¿dónde trabaja?

El ambiente de VenomScope son las secuencias de aminoácidos que llegan de una
campaña de muestreo en el noreste argentino, y el catálogo de toxinas ya
publicadas contra el cual se las compara.

Ese catálogo tiene hoy **584 toxinas de 106 especies**, agrupadas en 24 familias,
descargadas de UniProt, la base pública de proteínas más usada del mundo.

No forman parte del ambiente ni el laboratorio físico, ni los ensayos, ni el
resultado de esos ensayos. El sistema nunca se entera de si el candidato que
recomendó sirvió o no.

### Actuadores: ¿qué puede hacer?

Acá está la objeción que conviene adelantar, porque alguien la va a plantear:
**VenomScope no actúa sobre el mundo.** No pide reactivos, no agenda ensayos, no
descarta muestras, no manda correos. Sus únicos actuadores son informativos:

- una familia probable, con su nivel de seguridad;
- un puntaje de novedad del 0 al 100;
- las cinco toxinas conocidas más parecidas;
- una prioridad (alta, media o baja) **acompañada de las razones que la
  produjeron**;
- la campaña entera ordenada, descargable como planilla.

¿Es eso una limitación? No: es el diseño. Y hay tres razones para defenderlo.

**Primera, el costo de equivocarse no es simétrico.** Un sistema que descartara
muestras por su cuenta podría tirar, sin que nadie se entere, el candidato que
importaba. Un sistema que solo recomienda, en el peor caso hace perder diez
minutos.

**Segunda, el sistema sabe menos que el usuario.** VenomScope ve una secuencia de
letras. El laboratorio sabe de dónde salió la muestra, qué línea de
investigación tiene abierta, qué equipamiento hay disponible y qué se publicó la
semana pasada. Un sistema que decidiera solo estaría decidiendo con menos
información que la persona a la que reemplaza.

**Tercera, una recomendación que no se puede discutir no se adopta.** En un
laboratorio, quien firma el gasto tiene que poder explicar por qué lo firmó. Por
eso cada prioridad viene con sus razones escritas, y por eso el usuario puede
mover el umbral de sensibilidad desde la pantalla y ver cómo cambia todo: el
sistema entrega un argumento, no un veredicto.

Dicho en una línea: **el actuador de VenomScope es una recomendación, y esa
elección es deliberada.**

### Sensores: ¿qué puede ver?

- La secuencia de aminoácidos, pegada a mano o en un archivo FASTA o CSV.
- Un dato opcional que aporta la persona: si la muestra viene o no de una especie
  del noreste argentino.
- El catálogo de referencia y los umbrales de configuración.

Y nada más. **No ve** el animal, ni el lugar de la captura, ni la fecha, ni la
estructura tridimensional de la proteína, ni ningún resultado de laboratorio.
Opina sobre un texto de letras.

---

## 2. Cómo es el ambiente

| Propiedad | Cómo es acá | Qué consecuencia tiene |
|---|---|---|
| **Parcialmente observable** | El catálogo tiene solo lo que ya se publicó | Es la limitación central. Se desarrolla abajo |
| **Determinista** | La misma secuencia da siempre el mismo resultado | Se puede reproducir y auditar una recomendación de hace seis meses |
| **Episódico** | Cada secuencia se analiza sola, sin memoria de las anteriores | Simplifica todo, pero significa que el sistema no aprende del uso |
| **Estático** | El catálogo no cambia mientras se analiza una campaña | No hay apuro: el usuario puede pensar sin que la respuesta se desactualice |
| **Discreto** | Un alfabeto cerrado de 20 letras | Permite validar la entrada de forma estricta antes de gastar cómputo |
| **De un solo agente** | No hay nadie compitiendo ni colaborando | — |
| **Conocido** | Las reglas del juego están escritas y a la vista | El usuario puede entender el mecanismo completo |

### La observabilidad parcial es el sesgo de publicación

Esta es la propiedad que más conviene entender, porque **no es un detalle
técnico: es el sesgo principal del producto, dicho en el vocabulario de la
materia.**

El sistema mide qué tan novedosa es una secuencia comparándola contra el
catálogo. Pero el catálogo no contiene "las toxinas que existen": contiene **las
toxinas que alguien ya estudió, publicó y cargó en una base de datos
internacional**.

Esas dos cosas no son lo mismo, y la diferencia no es azarosa. Se publica más
sobre las especies peligrosas para las personas, sobre las fáciles de capturar y
sobre las que ya tienen financiamiento detrás. En nuestro propio catálogo se ve
sin esfuerzo: **285 secuencias de serpientes y 22 de anfibios.** Nadie cree que
los anfibios del NEA tengan trece veces menos toxinas que las serpientes; lo que
hay son trece veces menos publicaciones.

La consecuencia práctica, dicha para el laboratorio:

> Una toxina de una especie poco estudiada va a parecer **más novedosa de lo que
> realmente es**, simplemente porque hay menos con qué compararla. El sistema no
> mide qué tan rara es una molécula: mide **qué tan lejos está de lo que la
> ciencia ya miró**. En parte está midiendo nuestra propia ignorancia.

Que esto se pueda nombrar con precisión no lo arregla, pero cambia cómo se usa la
herramienta. Un puntaje de novedad alto en un anfibio merece más desconfianza que
el mismo puntaje en una serpiente, y quien lo lea tiene que saberlo. Por eso
figura en la pantalla "Cómo leer esto" y no escondido en un apéndice.

---

## 3. Por qué es un agente basado en utilidad

Los cuatro tipos de agente que vimos en la cursada, aplicados a este caso:

**No es un agente reactivo.** Un agente reactivo responde a lo que percibe con
reglas de estímulo y respuesta, sin ningún modelo de su mundo. VenomScope tiene
un modelo del mundo bien concreto: el catálogo de 584 toxinas y la representación
numérica que ESM-2 construye de cada secuencia. Sin ese modelo no podría decir
"esto está lejos de todo lo conocido", porque no tendría contra qué medir.

**No es solamente un agente basado en modelos.** Tener un modelo del mundo
alcanza para describir, no para recomendar. VenomScope no se queda en "esta
secuencia se parece a tal familia": dice qué conviene hacer con ella.

**No es un agente por objetivos.** Un agente por objetivos distingue entre
estados que cumplen la meta y estados que no: un resultado es aceptable o no lo
es. Acá eso no alcanza, porque **no hay una respuesta correcta única**. Treinta
candidatos de una campaña no se parten en "sirven" y "no sirven": se ordenan de
mejor a peor, y el laboratorio baja por esa lista hasta donde le alcance el
presupuesto. El producto necesita **grados**, no un sí o un no.

**Es un agente basado en utilidad.** Y en un sentido más fuerte que el habitual,
porque **en VenomScope la función de utilidad no está escondida adentro de un
modelo: está escrita en un archivo que cualquiera puede abrir y leer.**

El archivo es `venomscope/prioridad.py`, y dice esto:

| | Condición | Prioridad |
|---|---|---|
| 1 | No se parece a nada del catálogo (novedad 90 o más) | **Alta** |
| 2 | Es pariente lejano de algo conocido (novedad 75 a 89) | **Media** |
| 3 | El sistema no está seguro de la familia (menos del 50%) | sube a **Media** |
| 4 | Es del NEA y ya tenía prioridad media | sube a **Alta** |
| 5 | Todo lo demás | **Baja** |

Esas cinco líneas son la función de utilidad del agente. Combinan tres cosas que
no se pueden sumar directamente —cuán nueva es, cuán seguro está el sistema y si
es del foco regional— y producen un orden de preferencia.

Hay tres propiedades de esta decisión que vale la pena defender en voz alta:

**Es explícita.** No hay que interrogar a un modelo para saber por qué
recomendó algo. La respuesta se lee.

**Es auditable.** Cada resultado viene con las razones que lo produjeron, en
castellano. Si el laboratorio no está de acuerdo con la regla 4 —que las especies
del NEA desempaten hacia arriba—, puede discutirla, porque puede verla. Un modelo
entrenado que devolviera "prioridad: alta" sin más no permitiría esa
conversación.

**Es parcialmente ajustable por el usuario.** El corte entre "algo distinta" y
"novedosa" no está clavado: se mueve desde la pantalla entre 80 y 99, y la app
muestra en el momento cuántas novedades reales se encontrarían y cuántas falsas
alarmas aparecerían con cada valor. Es decir: **el usuario puede correr la
función de utilidad hacia donde le convenga, viendo el precio de hacerlo.**

### La decisión de fondo

Podríamos haber entrenado un modelo para predecir la prioridad directamente.
Habría quedado más impresionante y habría sido peor producto.

La razón es que **la prioridad no es un hecho sobre la molécula: es una decisión
de negocio.** Depende de cuánto cuesta un ensayo en este laboratorio, de cuánto
se tolera una falsa alarma y de qué tan fuerte es la apuesta regional. Eso no
está en los datos de UniProt y no se puede aprender de ellos. Es una política, y
las políticas se escriben, se discuten y se cambian; no se entrenan.

De ahí la división que organiza todo el sistema: **la IA mide, las reglas
deciden.** Las dos partes que requieren aprender de miles de ejemplos —entender
la secuencia y reconocer la familia— usan aprendizaje automático. La parte que
expresa qué le importa a esta organización usa reglas que cualquiera puede leer
en treinta segundos.
