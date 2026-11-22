# El nudo en la red del Óvalo Vasco, con los carriles corregidos (18.11.2026, noche)

Para Fabian Alvarado. Esta carpeta, `nudo_ovalo_estudio2/`, es el estudio del nudo de Reducto, 28 de Julio y Vasco
Núñez de Balboa preparado otra vez, **igual en todo** al que se lanzó hoy a las 11:03 y se detuvo a las 17:39
(`nudo_ovalo_estudio/`, que queda como registro de la corrida detenida), **con la red corregida**: los carriles de las
dos entradas de Reducto y el giro de Balboa hacia Larco, que faltaba. **No se lanzó nada**: solo pruebas con semillas
de humo (424301-424360) y la base 7. No se tocó `nudo_ovalo_estudio/`, el repositorio, la tesis ni el REGISTRO.

Quién hizo qué: la red y la demanda, el constructor 1 (`pruebas/correccion_carriles/CONSTRUCTOR1.md`); el semáforo,
los detectores, el modelo, los lanzadores, las huellas y este LEEME, el constructor 2
(`pruebas/correccion_carriles/CONSTRUCTOR2.md`). Después lo revisaron cinco revisores por separado (la especificación,
las luces, el humo del plan actual, el humo de los modelos y las figuras; sus informes están en
`carriles_reducto_2026-11-18/verificacion/` y `carriles_reducto_2026-11-18/validacion/`) y el corrector escribió la
enmienda nueva y puso al día este LEEME con lo que encontraron (`pruebas/correccion_carriles/CORRECTOR.md`). De dónde
sale la carpeta: `ORIGEN.md`.

## En pocas palabras

1. **Qué cambió.** Reducto desde el norte tiene 5 carriles (los 2 de la izquierda solo giran hacia el puente);
   Reducto desde el sur, 4 (los 2 de la izquierda solo giran hacia Larco y el de la derecha va de frente y también
   gira hacia el puente); y Balboa tiene un giro más, hacia Larco, por un tramo propio. Son 13 movimientos (antes 12).
   La demanda se recalculó con la misma regla y sigue sumando 4271 veh/h.
2. **Qué no cambió.** Las cuatro esquinas y sus distancias, la isla, las velocidades, los largos de afuera, el plan
   actual (ciclo de 132 s), los tres estados, las reglas de adentro, la válvula de 10 s, los modelos con sus opciones,
   las semillas y todo el protocolo. El código del modelo es el mismo archivo, byte a byte.
3. **El semáforo.** Sus luces salen de una regla sobre la red, así que se volvieron a escribir solas: 57 enlaces (antes
   53). Comprobado movimiento por movimiento y punto por punto: cada movimiento que ya existía lleva en cada punto la
   misma luz que en el estudio detenido, en las 7 fases del plan y en las 12 del programa del orden libre.
4. **El modelo.** La observación sigue teniendo 50 entradas (orden fijo) y 56 (orden libre). Lo que el modelo lee de la
   red cambió con los carriles (capacidad de Reducto norte 680 y de Reducto sur 540; antes 544 y 675).
5. **Plan actual, 20 semillas de humo:** 101 s/veh con la demanda publicada (de 76 a 169) y 279 con la alta (de 228 a
   324), sin ninguna traba permanente y sin vehículos sin terminar. En la red anterior, con la demanda anterior, daba
   224 y 512; la mayor parte de esa baja viene de las fracciones nuevas, no de los carriles (ver "Humo del plan
   actual"). El revisor del humo lo corrió por su cuenta y dio lo mismo. Los dos modelos, 5 episodios con la base 7
   (como en el estudio detenido, en una copia de esta carpeta) y 2 episodios aquí: 0 fallas de luces segundo a segundo.
6. **Lanzadores listos**: los tres `--comprobar` dicen "listo para lanzar" y `huellas.sha256` lista 73 archivos.
7. **Hecho antes de lanzar (18.11.2026, 23:40)**: la enmienda que quedó en `lima/REGISTRO.md` es
   `enmienda_registro_carriles.md` (la del cierre), no `enmienda_registro.md` (borrador del corrector, reemplazado: tiene
   errores de texto que corrigió la segunda vuelta). Fabian vio lo que su visto bueno de las 20:00 no cubría y eligió
   lanzar con esta red y declarar los dos puntos como límites (camino A, 23:35). Donde este LEEME describe el límite (a)
   o dice que se pegue `enmienda_registro.md`, manda la enmienda del REGISTRO.
8. **Límites declarados** (decididos hacia las 20:00; las fracciones no cambian): (a) el giro del puente hacia Reducto
   sur pide 97.4 veh/h y la red deja pasar unos 69; en la red esperan en fila por un solo carril, no tres lado a lado
   como en tu foto; (b) Balboa hacia Reducto norte y hacia Larco atienden el 93-94 % de lo que piden; (c) 4 choques en
   40 corridas y ningún teletransporte por atasco. Detalle en "Límites declarados".

## Qué cambió y por qué

El 18.11.2026, hacia las 17:35, revisaste la red contra el lugar y encontraste mal los carriles de las dos entradas de
Reducto y la falta de un giro de Balboa. Lo confirmaste por escrito ese día, carril por carril. El carril 0 es el de la
derecha del conductor.

| Entrada | Antes (red del 13.11) | Ahora |
|---|---|---|
| Reducto desde el norte | 4 carriles: 3 de frente (el derecho también gira a Larco) y 1 de giro al puente | 5 carriles: 0 de frente y derecha (Larco); 1 y 2 de frente; 3 y 4 solo izquierda, hacia el puente |
| Reducto desde el sur | 5 carriles: 1 solo derecha (puente), 2 de frente y 2 de giro a Larco | 4 carriles: 0 de frente y derecha (puente); 1 de frente; 2 y 3 solo izquierda, hacia Larco |
| Balboa | 3 carriles: 0 al puente y a Reducto sur; 1 al puente; 2 al puente y a Reducto norte | Igual, y el carril 2 gira además a la izquierda hacia Larco (movimiento nuevo) |
| 28 de Julio desde el puente | 3 carriles: 0 a Larco y a Reducto norte; 1 a Larco; 2 solo a Reducto sur | Sin cambios |

Las salidas no cambian: hacia Larco 2 carriles, Reducto norte 2, Reducto sur 3 y el puente 3.

Lo que cambia por dentro es solo lo que piden esos carriles:

| Qué | Antes | Ahora |
|---|---|---|
| Ramal de giro del norte, antes y después de cruzar | 1 carril | 2 carriles |
| Calzada principal del sur | 3 carriles | 2 carriles |
| Ramal de giro del sur | 2 carriles | 2 carriles |
| Tramo de Balboa hacia Larco | no existía | 1 carril, 45.2 m (caben 6 autos), por el oeste, sin cruzar los lados del óvalo |
| Enlaces del semáforo | 53 | 57 |
| Detectores de 75 m (uno por carril de entrada) | 15 (4 + 5 + 3 + 3) | 15 (5 + 4 + 3 + 3) |
| Lugar libre del lado norte | 6.7 m (cabe 1 auto por carril) | 4.6 m (no cabe ninguno) |
| Lugar libre del lado este | 6.3 m (cabe 1) | 4.1 m (no cabe ninguno) |
| Lugar libre del lado sur | 4.0 m (no cabe ninguno) | 5.6 m (cabe 1) |
| Lugar libre del lado oeste | 5.3 m (cabe 1) | 5.3 m (cabe 1) |

El lugar libre de tres lados cambió **sin pedirlo**: las esquinas no se movieron, pero el borde de cada esquina depende
del ancho de lo que la cruza. El borde de la esquina NE llega hasta el cruce del ramal de giro del norte, que ahora
tiene 2 carriles: NE se lleva 8.84 de los 18.44 m del lado norte y 11.02 de los 19.92 m del este
(`carriles_reducto_2026-11-18/red/INFORME.md`, 3.5). Los cruces de los ramales quedaron donde estaban, a la misma
distancia de su esquina que en OpenStreetMap. Con eso cambió también la forma de las esquinas: NE pasa de 129.95 a
169.75 m² y SE de 92.49 a 62.03 m², y el tramo interno de 23 de las 47 conexiones que existen en las dos redes cambia
de largo (por ejemplo, 28 de Julio en NE de 12.79 a 14.93 m; Balboa en SE de 9.64 a 6.43 m). Además, los carriles de
las dos entradas de Reducto terminan 0.26 m (norte) y 0.10 m (sur) antes de donde terminaban. Detalle y medidas:
`pruebas/correccion_carriles/comparar_redes.txt` y, medido aparte por el corrector,
`pruebas/correccion_carriles/corrector/geometria_corrector.txt`. **Tu visto bueno de las 20:00 fue sobre la tabla y el
mapa, que no dan estas cifras**: ver "Problemas abiertos", 2.

## Simplificaciones declaradas

1. **Carriles de giro completos.** Los carriles de giro de Reducto son carriles enteros de la entrada (1 km), en las dos
   entradas. En el sitio el ensanche es corto: la red le da a Reducto más lugar para la cola del que tiene. Es igual
   para todos los controles.
2. **El giro a la derecha del sur sale solo del carril derecho.** Dijiste que los dos carriles de la derecha pueden
   seguir de frente o girar hacia el puente. Girar desde el segundo carril cruzaría al primero, que sigue de frente:
   se modela solo desde el carril 0.
3. **El carril del medio de Balboa va solo de frente.** Dijiste que desde el carril del medio también se gira. No se
   modela, por el mismo motivo: los giros de Balboa hacia Reducto norte y hacia Larco salen solo del carril izquierdo.
4. **Sin vuelta en U** desde Reducto norte.
5. **El giro de 28 de Julio hacia Reducto norte pasa con su verde.** Sale del carril derecho de 28 de Julio y dobla en
   la primera esquina con prioridad: no espera adentro ni tiene luz propia.
6. **Balboa hacia Larco es un ceda el paso en la unión.** Tiene verde junto con Balboa en su línea de parada, va por
   su tramo y, donde se junta con la salida hacia Larco, cede a todos los que van hacia Larco (a los dos carriles, no
   solo al que entra). Su tramo (`B_ML`, 45.24 m) va aparte solo en su parte media: en sus primeros 16.2 m se
   superpone al carril izquierdo de Balboa pasada la línea de parada (`B_SO_2`; nacen en el mismo punto), y en sus
   últimos metros al ramal de giro de Reducto sur hacia Larco (18 m con su carril izquierdo, `SO_ML_1`, y 10.2 m con el
   derecho), como en OpenStreetMap. SUMO no hace que esos vehículos se estorben hasta la unión
   (`carriles_reducto_2026-11-18/verificacion/especificacion/verificar_red.txt`, 1i, y
   `pruebas/correccion_carriles/corrector/geometria_corrector.txt`, 4).
7. Lo que ya estaba declarado y sigue igual: el que gira y cruza al otro flujo (28 de Julio hacia Reducto sur y Balboa
   hacia Reducto norte) cede en su segunda esquina y espera adentro; quien quedó adentro al cambiar la luz sale
   primero; un solo semáforo para los 10 nodos; la válvula de 10 s en todas las corridas.

## Límite conocido del programa del orden libre (no se corrigió)

Si el modelo de orden libre pasa de 28 de Julio y Balboa directamente a los giros de Reducto (el paso "2 a 1", que el
plan actual no tiene), los vehículos que quedaron adentro no salen durante ese verde ni durante el siguiente: la regla
"quien está adentro sale primero" solo recuerda el estado inmediatamente anterior. Lo demostró el diagnóstico de la
corrida detenida (`diagnostico_orden_ovalo_2026-11-18/DIAGNOSTICO.md`, secciones 5, 7 y 8): con una regla fija que
repite ese paso, el retraso sube 97 %; pero los modelos casi no lo usan (3 a 10 veces por política en dos episodios)
y no es la causa de su resultado. **No se corrige en este estudio**, para no cambiar nada del método: queda como
límite.

En la red corregida se ve igual (`carriles_reducto_2026-11-18/verificacion/luces/INFORME.md`, sección 5): con una regla
fija que recorre los seis pasos, 20 detenciones de 60 a 70 s dentro del óvalo en 4 corridas, todas tras el paso 2 a 1;
con el plan actual, ninguna. En el humo de 5 episodios, con políticas casi al azar, el modelo de orden libre usó ese
paso 199 veces con la publicada y 152 con la alta (`carriles_reducto_2026-11-18/verificacion/humo_modelos/INFORME.md`).
La enmienda lo registra como límite.

## Límites declarados (decididos el 18.11.2026 hacia las 20:00)

Las fracciones de la demanda no cambian. Se declaran estos límites, con las cifras del humo del plan actual (20
semillas; `carriles_reducto_2026-11-18/verificacion/humo_plan/INFORME.md`; el corrector las volvió a contar desde los
datos crudos: `pruebas/correccion_carriles/corrector/humo_corrector.txt`):

| | Qué pasa en la red | Cifras con la demanda publicada |
|---|---|---|
| (a) Giro del puente hacia Reducto sur | Pide más de lo que la red deja pasar y acumula cola. Los que esperan adentro van en fila, por un solo carril, casi siempre antes de la primera esquina; no tres lado a lado en el lado oeste, como en tu foto. Salen cuando Balboa deja de pasar. No se aisló la causa | Pide 97.4 veh/h y pasan 69.3 (el 74 % de los 94.1 que pedían en esa hora; 2.5 por verde, y viste unos 3). 599.5 s/veh (288.5 a 914.9; más de 300 en 19 de 20 semillas): el 13.4 % del retraso con el 2.2 % de los vehículos. Al final del verde, 2.31 detenidos adentro (hasta 4): 77 % antes de la primera esquina, 18 % en el lado norte, 3 % en el oeste (uno solo, en 5 de 75 verdes). El 96.5 % sale del óvalo con Reducto de frente ya en verde. Con la alta, 57 % y 1112.7 s/veh |
| (b) Balboa hacia Reducto norte y hacia Larco | Quedan en el límite. Comparten el carril izquierdo de Balboa, que pierde el 39 % de su verde: el que gira hacia Reducto norte espera antes de su primera esquina a que termine 28 de Julio y tapa el carril. El de Larco espera siempre en su tramo propio | Atienden 47.8 de 51.1 (94 %) y 47.1 de 50.7 veh/h (93 %); 239.5 y 246.5 s/veh. El carril izquierdo pasa 7.0 vehículos por verde y los otros dos, 14.2 y 16.3; tiene el primero detenido en la línea 13.8 de los 35 s de verde útil |
| (c) Choques | Un bus (3 veces) o una combi alcanza a un auto casi detenido en los tramos cortos de Reducto antes de su esquina (`RN_NO` 3 veces, `RS_SE` 1); SUMO retira al que choca | 4 en 40 corridas (1 con la publicada y 3 con la alta), cada uno con su teletransporte; 0 teletransportes por atasco, por ceder o por carril |

Por qué no se baja la fracción del giro del puente: lo que se le quite pasaría a los dos carriles de frente de 28 de
Julio, que con la publicada ya están al 97 % de lo que el plan deja pasar (piden 876.4 veh/h y con la alta pasan
903.3). Para comparar: un auto por ciclo son 27.3 veh/h.

Otras cosas medidas en el humo, para leer bien los resultados:
- Con la publicada, 28 de Julio de frente y Balboa quedan al 97 % de lo que el plan deja pasar: el retraso total del
  plan actual va de 76 a 169 s/veh según la semilla, y el de Balboa hacia el puente, de 64.5 a 310.4.
- Con la alta, 11 de los 13 movimientos atienden menos de lo que piden y 7 pasan de 300 s/veh.
- 7 de 280 vehículos del giro hacia Reducto sur (3 corridas) cruzan la línea de parada desde el carril del medio de 28
  de Julio y cambian de carril adentro (se detienen hasta 23 s): es una rareza del simulador; ninguno queda atrapado.
- Nadie cruza una línea de parada fuera de su verde y su ámbar (0 de 188 072 vehículos en las 40 corridas) y nadie
  queda más de un ciclo adentro (el que más, 107 s).
- En el lado oeste cabe 1 auto por carril (5.28 m). Los lados este (4.08 m), donde espera Balboa hacia Reducto norte
  antes de ceder, y norte (4.62 m) ya no tienen lugar para un auto entero. No se aisló si eso hace que los dos giros
  esperen antes de su primera esquina: no hay posiciones por segundo de la red anterior para comparar.

## Qué hay en la carpeta

| Archivo o carpeta | Qué es |
|---|---|
| `entrenar.sh` | Los seis entrenamientos de un modelo: `bash entrenar.sh libre` y `bash entrenar.sh completo` (los dos a la vez: doce) |
| `referencias.sh` | Fijo ajustado y ciclo mínimo, actuado y actuado ajustado, comprobación del borde y validación de las referencias, en las dos demandas |
| `evaluar_ovalo.py` | Las dos tandas (referencias y modelos), la robustez del reparto y los veredictos (`salidas_ovalo/veredicto_ovalo.md`) |
| `tablas_ovalo.py`, `figura_secuencia.py` | Tablas y figuras para la tesis (`salidas_ovalo/tesis/`), y la figura de la secuencia de luces |
| `ver_ovalo.py`, `vista_ovalo.xml` | Mirar la simulación en sumo-gui (con ventana no se corrió; sin ventana, en la prueba de los lanzadores) |
| `comprobar_fases.py` | Comprueba segundo a segundo las luces de una traza |
| `comprobar_referencias.py` | Lo que revisa `referencias.sh --comprobar` |
| `huellas.sha256`, `archivos_huellas.txt` | Huellas de los 73 archivos de código y datos; ningún lanzador corre si alguno cambió |
| `enmienda_registro_carriles.md` | La enmienda de la red corregida, tal como quedó en `lima/REGISTRO.md` (18.11.2026, 23:45). La de las 11:03 sigue en `nudo_ovalo_estudio/enmienda_registro.md` |
| `enmienda_registro.md` | Borrador del corrector, reemplazado por `enmienda_registro_carriles.md`; no se pegó |
| `ORIGEN.md` | De dónde se copió la carpeta y qué quedó fuera |
| `demo_rl/` | El código (el del estudio detenido) y las carpetas de trabajo |
| `demo_rl/lima/`, `demo_rl/lima/alta/` | La red corregida con la demanda publicada y con la alta: aquí se entrena, se ajusta y se evalúa |
| `demo_rl/lima/robustez/{reducto,transversal}/` | Las dos demandas de la prueba de robustez del reparto |
| `demo_rl/lima/ovalo/` | Cómo se arma la red y la demanda: `armar_ovalo.py` (la tabla de carriles, `DISPOSICION`), `regenerar_demanda.py`, `preparar_carpetas.py`, `comprobar_red.py`, sus entradas y `red/` |
| `pruebas/correccion_carriles/` | Todo lo que se comprobó en la corrección: los informes de los dos constructores y del corrector (`CORRECTOR.md`), los programas de comprobación y sus salidas (las del corrector, en `corrector/`) |
| `pruebas/humo/`, `pruebas/lanzadores/`, `pruebas/guardas/`, `pruebas/escritor/` | Las pruebas del estudio, vueltas a correr en la red corregida (ver "Pruebas hechas") |
| `logs/` | Vacía; los registros de la corrida real quedan aquí |

## La red

`demo_rl/lima/lima.net.xml` (la misma en las cuatro carpetas de trabajo) es `demo_rl/lima/ovalo/red/ovalo_estudio.net.xml`,
armada con `demo_rl/lima/ovalo/armar_ovalo.py`. Los carriles de las cuatro entradas están escritos en un solo sitio,
la tabla `DISPOSICION` de ese archivo; lo demás se deduce de ella. Con la disposición anterior el mismo constructor da
la red anterior byte a byte, salvo la cabecera del `.net.xml`, que lleva la fecha
(`pruebas/correccion_carriles/regresion/regresion.txt`).

- Lados de esquina a esquina (tus medidas): norte 18.44 m, oeste 24.43 m, este 19.92 m y sur 15.74 m. Los 10 nodos del
  semáforo están a 0.000 m de donde estaban.
- Antes de la primera esquina: 28 de Julio 13.4 m y Balboa 18.0 m (igual que antes).
- Un solo semáforo, `semaforo_S1`, en los 10 nodos (4 líneas de parada de afuera, 4 esquinas y 2 uniones): 57 enlaces.
- Los mismos cinco giros subidos a 5.56 m/s (20 km/h); ningún tramo interno por debajo.
- Todas las corridas llevan `--ignore-junction-blocker 10` (en el `.sumocfg`, que no cambió: sha256 `cbc78301…`).
- Resumen y comprobaciones, con sumolib: `demo_rl/lima/ovalo/red/resumen_estudio.txt` (`comprobar_red.py`: todas bien).

A dónde va cada carril, leído de la red armada:

| Carril | Hacia |
|---|---|
| `RN_S1_0` | Reducto sur y Larco |
| `RN_S1_1`, `RN_S1_2` | Reducto sur |
| `RN_S1_3`, `RN_S1_4` | el puente (giro a la izquierda) |
| `RS_S1_0` | Reducto norte y el puente |
| `RS_S1_1` | Reducto norte |
| `RS_S1_2`, `RS_S1_3` | Larco (giro a la izquierda) |
| `B_S1_0` | el puente y Reducto sur |
| `B_S1_1` | el puente |
| `B_S1_2` | el puente, Reducto norte y Larco (nuevo, por el tramo `B_ML`) |
| `J_S1_0` | Larco y Reducto norte |
| `J_S1_1` | Larco |
| `J_S1_2` | Reducto sur |

## El semáforo

El plan actual no cambió: Reducto de frente 37 s y 3 de ámbar; giros a la izquierda de Reducto 15 y 3; todo en rojo
34 s; 28 de Julio y Balboa 37 y 3. Ciclo de 132 s. Los tres estados tienen los mismos movimientos, más Balboa hacia
Larco, que va con 28 de Julio y Balboa. Los dos giros a la izquierda de Reducto siguen juntos.

Las luces no están escritas a mano: `demo_rl/lima/ovalo/plan_ovalo.py` las deduce de la red (qué movimientos usan cada
enlace) y `demo_rl/lima/programa_ovalo.py` escribe el plan (`lima.add.xml`), los programas de las referencias y el
programa del orden libre (`lima_libre.json`, 12 fases). Lo único escrito a mano en la regla es quién cede dentro del
óvalo, y solo se agregó el giro nuevo:

| Movimiento | Dónde cede | Desde cuándo |
|---|---|---|
| 28 de Julio hacia Reducto sur | en la esquina SO, a Balboa | estudio detenido |
| Balboa hacia Reducto norte | en la esquina NE, a 28 de Julio | estudio detenido |
| Balboa hacia Larco | en la unión de la salida hacia Larco, a todos (ceda el paso) | corrección de carriles |

Por qué un ceda el paso y no la regla general: con la regla general, cuando después de 28 de Julio y Balboa venía
Reducto de frente, el giro nuevo y el carril derecho hacia Larco quedaban cediéndose uno al otro toda la fase (medido
por el constructor 1: un bloqueo de 39 s con la demanda publicada y dos de 38 s con la alta, semilla 424301). Con el
ceda el paso no hay ninguno y las luces de todos los demás enlaces quedan como si el giro no existiera.

Comprobado (`pruebas/correccion_carriles/letras_c2.txt` y `programas_c2.txt`, sin simular):

- El plan y el programa libre de las cuatro carpetas, vueltos a escribir en una carpeta aparte, salen byte a byte
  iguales a los que están (sha256 `140a3ccb…` y `ecf94f52…`).
- Los 47 enlaces que existen en las dos redes llevan la misma luz en las 19 fases (7 del plan y 12 del orden libre).
- Los 12 movimientos que ya existían llevan en cada punto de su camino (entrada, esquinas y unión) la luz del estudio
  detenido. Donde un movimiento tiene ahora más carriles, todos llevan la luz que llevaba el que había.
- El segundo carril del giro del norte lleva en los tres puntos la luz del primero. Balboa hacia Larco tiene verde con
  Balboa en su línea de parada y en la unión nunca tiene prioridad ni queda en rojo.
- Ningún par de enlaces con prioridad se cruza en ninguna fase, y todo enlace sin prioridad cede, según la red, a los
  que la tienen.

## La demanda

La regla no cambió: el total publicado de 4271 veh/h se reparte en proporción a carriles por segundos de verde medidos
de cada grupo, y dentro de cada grupo por destino. Cambian los carriles de los grupos y las fracciones de 28 de Julio
y de Balboa, que se fijaron hoy con lo que dijiste: adentro del óvalo caben unos 3 autos esperando el giro del puente
hacia Reducto sur (`carriles_reducto_2026-11-18/capturas_fabian/28_espera_dentro_del_ovalo.png`) y de Balboa a
Reducto norte suben "muy pocos".

| Grupo | Carriles | Verde medido (s) | Destinos |
|---|---|---|---|
| Reducto norte de frente | 3 | 38 | 90 % a Reducto sur y 10 % a Larco |
| Reducto norte, giro | 2 (antes 1) | 18 | 100 % al puente |
| Reducto sur de frente | 2 (antes 3) | 40 | 80 % a Reducto norte y 20 % al puente |
| Reducto sur, giro | 2 | 18 | 100 % a Larco |
| 28 de Julio | 3 | 38 | 75 % a Larco, 15 % a Reducto norte y 10 % a Reducto sur (antes 65, 15 y 20) |
| Balboa | 3 | 40 | 70 % al puente, 20 % a Reducto sur, 5 % a Reducto norte y 5 % a Larco (antes 55, 35 y 10) |

Flujos con la demanda publicada (veh/h), leídos de los archivos (`demo_rl/lima/ovalo/entrada/rutas_estudio/flujos.txt`,
que trae también la alta y las dos de la robustez):

| Entrada | Hacia | Estudio detenido | Ahora |
|---|---|---|---|
| Reducto norte | Reducto sur | 839.5 | 876.4 |
| Reducto norte | Larco | 93.3 | 97.4 |
| Reducto norte | el puente | 147.3 | 307.5 |
| Reducto sur | Reducto norte | 785.5 | 546.7 |
| Reducto sur | el puente | 196.4 | 136.7 |
| Reducto sur | Larco | 294.6 | 307.5 |
| 28 de Julio | Larco | 606.3 | 730.3 |
| 28 de Julio | Reducto norte | 139.9 | 146.1 |
| 28 de Julio | Reducto sur | 186.5 | 97.4 |
| Balboa | el puente | 540.0 | 717.5 |
| Balboa | Reducto sur | 343.6 | 205.0 |
| Balboa | Reducto norte | 98.2 | 51.3 |
| Balboa | Larco | no existía | 51.3 |
| **Todo el nudo** | | **4271.0** | **4271.0** |

La demanda alta es la publicada por 1.2, flujo por flujo (5125.2 veh/h). Las dos de la robustez tienen el mismo total
publicado, con más carga en Reducto o en 28 de Julio y Balboa, como antes.

Las fracciones de 28 de Julio y de Balboa son dos líneas al comienzo de `demo_rl/lima/demanda.py`
(`DESTINOS_28_DE_JULIO` y `DESTINOS_BALBOA`) y todo se regenera con un comando, desde `demo_rl/lima/ovalo`:
`python -B regenerar_demanda.py`. **Ya es la definitiva: no se vuelve a regenerar.** Si alguna vez se regenera, hay
que rehacer las huellas.

## El código (qué cambió frente al estudio detenido)

No cambió nada del modelo, de la recompensa, de la observación ni de las reglas del orden libre. Estos archivos son los
del estudio detenido, byte a byte (misma huella): `demo_rl/rl_ippo.py`, `comun.py`, `rl_corredor.py`,
`escenarios_lima.py`, `escenarios_plan2.py`, `evaluar.py`, `veredicto.py`, `barrer_fijo.py`, `lima/estudio.py`,
`lima/programa.py`, `lima/programa_ovalo.py`, `lima/borde_actuado.py`, `entrenar.sh`, `referencias.sh`,
`evaluar_ovalo.py`, `comprobar_fases.py`, `figura_secuencia.py`, `ver_ovalo.py` y `vista_ovalo.xml`. Por eso la prueba
de equivalencia de la mañana (este código da en la red del estudio lo mismo que el de `orden_libre_2026-11-17/`)
sigue valiendo y no se repitió.

Ninguno de esos programas tiene escrito un carril, un número de carriles ni qué carriles tiene cada estado: todo lo leen
de la red en cada corrida (comprobado con una búsqueda en todo el código y, después, en el meta de las políticas de
prueba).

| Archivo | Qué cambió | Quién |
|---|---|---|
| `demo_rl/lima/ovalo/armar_ovalo.py` | La tabla `DISPOSICION` y lo que se deduce de ella; el tramo de Balboa hacia Larco | constructor 1 |
| `demo_rl/lima/ovalo/plan_ovalo.py` | El giro nuevo: cede en la unión y es un ceda el paso. Nada más | constructor 1; revisado por el 2 |
| `demo_rl/lima/demanda.py` | Los carriles de los grupos y las fracciones de 28 de Julio y de Balboa | constructor 1 |
| `demo_rl/lima/ovalo/regenerar_demanda.py` (nuevo) | El comando único de la demanda | constructor 1 |
| `demo_rl/lima/ovalo/preparar_carpetas.py`, `comprobar_red.py`, `armar_rutas.py` | Ya no comparan con archivos de la red anterior; los detectores son los de la red nueva | constructor 1 |
| `demo_rl/plan3/demanda_estocastica.py`, `demo_rl/escenarios_plan3.py` (nuevos) | Copias del repositorio que necesita `demanda.py` | constructor 1 |
| `comprobar_referencias.py` | Los detectores que no cuentan a nadie de los actuados se comparan con los carriles de adentro de la red (36), no con el 34 escrito a mano | constructor 2 |
| `tablas_ovalo.py` | Una palabra: el comentario de cada tabla dice `nudo_ovalo_estudio2` | constructor 2 |

Dos comentarios del código citan todavía la red anterior y no se tocaron para no cambiar la huella del modelo:
`demo_rl/lima/estudio.py`, línea 68 ("53 enlaces") y `demo_rl/rl_ippo.py`, línea 152 ("nudo_ovalo_estudio/LEEME.md").
No tienen ningún efecto.

Lo que el modelo lee de la red corregida (`pruebas/correccion_carriles/detectores_modelo_c2.txt` y `pruebas/humo/modelo.md`):

| Qué | Estudio detenido | Ahora |
|---|---|---|
| Entradas de la observación | 50 (orden fijo) y 56 (orden libre) | 50 y 56 |
| Capacidad de Reducto norte y de Reducto sur | 544 y 675 | 680 y 540 |
| Capacidad de Balboa y de 28 de Julio | 405 y 408 | 405 y 408 |
| Carriles del estado de Reducto de frente | `RN_S1_0-2`, `RS_S1_0-2` | `RN_S1_0-2`, `RS_S1_0-1` |
| Carriles del estado de los giros | `RN_S1_3`, `RS_S1_3`, `RS_S1_4` | `RN_S1_3`, `RN_S1_4`, `RS_S1_2`, `RS_S1_3` |
| Carriles del estado de 28 de Julio y Balboa | `B_S1_0-2`, `J_S1_0-2` | iguales |
| Detectores de 75 m | 15 | 15: entra `e2_RN_S1_4` y sale `e2_RS_S1_4` |

## Pruebas hechas en la red corregida

Solo la base 7 y las semillas de humo 424301-424320 y 424341-424355. Como máximo 6 simulaciones a la vez en esta
carpeta. Las seis últimas filas son las cinco revisiones y el corrector: las revisiones no escribieron en esta
carpeta (las que simularon lo hicieron en sus propias copias, con 8 a la vez como máximo) y el corrector no simuló.

| Prueba | Resultado | Dónde |
|---|---|---|
| La red frente a la anterior, la regresión del constructor y la demanda (constructor 1) | Todas bien, salvo lo dicho del lugar libre y de las líneas de parada de Reducto | `pruebas/correccion_carriles/CONSTRUCTOR1.md` |
| `comprobar_red.py` con la demanda definitiva | Todas bien: 52 flujos de 13 movimientos, 15 detectores, 57 enlaces y 23 aristas en cada carpeta | `demo_rl/lima/ovalo/red/resumen_estudio.txt` |
| El plan y el programa libre vueltos a escribir en una carpeta aparte | Byte a byte iguales a los de las cuatro carpetas | `pruebas/correccion_carriles/programas_c2.txt` |
| Las luces de cada movimiento en cada punto, frente al estudio detenido | Iguales en los 12 movimientos que ya existían; la regla cubre los enlaces nuevos | `pruebas/correccion_carriles/letras_c2.txt` |
| El escritor frente a los programas de la revisión (plan, fijo, actuado ajustado y ciclo mínimo, las dos demandas) | Mismo tipo, parámetros y duraciones; 0 letras distintas en los 47 enlaces comunes | `pruebas/escritor/comparar_revision.txt` |
| Todos los controles usan las letras del plan y solo cambian duraciones | Sin fallas; 36 detectores nulos en los actuados | `pruebas/correccion_carriles/revisar_programas_c2.txt` |
| Detectores y lo que el modelo lee de la red, sin simular | 15 detectores (5 + 4 + 3 + 3); `rl_ippo.py` no los reescribe; observación de 50 y 56 | `pruebas/correccion_carriles/detectores_modelo_c2.txt` |
| Humo del plan actual, semillas 424301-424320, publicada y alta | Ver "Humo del plan actual", abajo: 0 trabas en 20 con cada demanda | `pruebas/humo/plan_actual.md` y `plan_actual_corridas.csv` |
| Plan actual, semillas 424301 y 424302, las cuatro demandas | Ver la tabla de abajo: sin trabas | `pruebas/correccion_carriles/humo_c2_plan.txt` |
| SUMO carga y corre los cuatro tipos de programa de las referencias (semilla 424303, demanda publicada) | Sin errores; los mismos 6 avisos de siempre al cargar. Fijo [45, 15, 37] 162.5 s/veh; actuado con hueco de 1 s 87.8; por retraso 84.7; ciclo mínimo 1476.9 (607 sin terminar, todavía llegando) | `pruebas/correccion_carriles/humo_c2_referencias.txt` |
| Los dos modelos, 2 episodios con la base 7 y validación en 424303-424304: publicada (dos copias) y alta | 0 fallas de luces en las 6 trazas (24 episodios); el de orden libre usa los seis pasos; las dos copias dan lo mismo; `tope_excedido` 0 | `pruebas/humo/modelo.md` |
| `--comprobar` de los lanzadores | Los tres dicen "listo para lanzar"; `evaluar_ovalo.py` dice qué falta | `pruebas/correccion_carriles/lanzadores_comprobar_c2.txt` |
| Guardas: un verde cambiado en una copia | Los nueve intentos se niegan sin escribir nada | `pruebas/guardas/guardas.txt` |
| Lanzadores de punta a punta con semillas de humo (424341-424355) y las políticas de 2 episodios | Todos los pasos corrieron sin errores, en 22 minutos con 6 procesos: `evaluar_ovalo.py` con `--comprobar` y de verdad (referencias, modelos citados, robustez y veredicto), `tablas_ovalo.py` (6 tablas y 2 figuras), `figura_secuencia.py` correr y dibujar, `ver_ovalo.py` sin ventana con los 5 controles y `estudio.py verdes-modelo`. Las cifras de los modelos no significan nada | `pruebas/lanzadores/probar.log` |
| Revisión de la especificación, sin simular y con programas propios | Los 15 carriles de entrada van a los destinos confirmados; 13 movimientos; los 10 nodos del semáforo a 0.000 m; las 52 tasas de los 8 archivos de demanda son las de la regla (0.0018 veh/h de diferencia como máximo); ningún resultado de la corrida detenida en esta carpeta; 73 de 73 huellas. Sus dos reparos importantes (la enmienda vieja y el lugar libre) quedan resueltos con la enmienda nueva y este LEEME | `carriles_reducto_2026-11-18/verificacion/especificacion/INFORME.md` |
| Revisión de las luces: un descifrado propio, sin el código del estudio, y 8 corridas con traza (424301 y 424302) | 0 problemas en las 19 fases; las 60 relaciones de quién cede de los 12 movimientos que ya existían, sin cambios; 0 fallas en `comprobar_fases.py`; el plan reproduce exactamente el humo | `carriles_reducto_2026-11-18/verificacion/luces/INFORME.md` |
| Humo del plan actual, hecho otra vez por un revisor (20 semillas por demanda; posiciones por segundo en 3) | Los mismos 101.2 y 278.6 s/veh; 0 trabas; de ahí salen los límites (a), (b) y (c) | `carriles_reducto_2026-11-18/verificacion/humo_plan/INFORME.md` |
| Humo de los modelos como en el estudio detenido (5 episodios, base 7, validación en 424303-424304, las dos demandas, dos copias, 8 a la vez), en una copia byte a byte de esta carpeta | 0 fallas de luces en las 8 trazas (56 episodios); el de orden libre usa los seis pasos (905 de 1724 y 817 de 1658 cambios fuera del orden; `tope_excedido` 0); el de orden fijo, 0 fuera del orden; las copias dan lo mismo byte a byte. Punta a punta otra vez (16 min 48 s, 8 procesos): todos los pasos corrieron | `carriles_reducto_2026-11-18/verificacion/humo_modelos/INFORME.md` |
| Figuras para validar contigo (mapa, estados y tabla) | En todo lo que muestran, la red coincide con la especificación; sus tres reparos de la red están en este LEEME | `carriles_reducto_2026-11-18/validacion/INFORME.md` |
| Corrector: lugar libre, esquinas, superposición de `B_ML` y cifras del humo, medidos otra vez por su cuenta, sin simular | Coinciden con los revisores (diferencias de redondeo en `CORRECTOR.md`) | `pruebas/correccion_carriles/corrector/` |

### Humo del plan actual (semillas 424301-424320)

`python -B pruebas/humo/correr_plan.py correr --redes final --procesos 6` y `resumir`: las opciones de `estudio.py`,
sin TraCI, 40 corridas en 80 s. Detalle por semilla y por movimiento: `pruebas/humo/plan_actual.md` y
`plan_actual_corridas.csv`. La fila de la red anterior es la del estudio detenido, con las mismas semillas
(`nudo_ovalo_estudio/pruebas/humo/plan_actual.md`).

| Red y demanda | Retraso total medio (s/veh) | Mín. - máx. | Trabas permanentes | Sin terminar a los 6000 s | Choques | Segundos por corrida |
|---|---|---|---|---|---|---|
| **Red corregida, demanda publicada** | **101.2** | 76 - 169 | **0 de 20** | 0 | 1 | 6 |
| **Red corregida, demanda alta** | **278.6** | 228 - 324 | **0 de 20** | 0 | 3 | 15 |
| Red anterior, su demanda publicada | 224.3 | 170 - 290 | 0 de 20 | 0 | 1 | 21 |
| Red anterior, su demanda alta | 512.4 | 440 - 592 | 0 de 20 | 80 en 3 semillas | 1 | 52 |

- **Trabas.** Traba permanente: a los 6000 s quedan vehículos y nadie llegó en los últimos 300 s. Ninguna en 40
  corridas, y en ninguna queda un vehículo sin terminar.
- **Nivel de servicio.** Sigue en F con las dos demandas (E llega hasta 80 s por vehículo), pero la publicada queda
  cerca: 101 s/veh, con 5 de las 20 semillas por debajo de 90 y una en nivel E (76). El retraso simulado sigue sin
  poder compararse con el nivel E publicado. El giro de 28 de Julio hacia Reducto sur espera 600 s/veh (1093 en la
  red anterior).
- **Por movimiento, con la publicada** (media de las 20 semillas): 28 de Julio hacia Reducto sur 600 s/veh; Balboa
  hacia Larco 246 y hacia Reducto norte 239 (comparten el carril izquierdo de Balboa); Balboa hacia Reducto sur 130 y
  hacia el puente 118; los otros ocho, de 62 a 90. Con la alta: 1113, 575 y 554; los demás, de 115 a 388.
- **Choques.** Cuatro en 40 corridas (publicada 424313; alta 424311, 424313 y 424320). Son choques por alcance a
  menos de 4 m/s dentro del óvalo, justo después de la línea de parada de Reducto: tres en la calzada del norte (un
  bus contra un auto) y uno en la del sur. SUMO retira al que choca: los 4 teletransportes de las 40 corridas son esos
  choques, y no hay ninguno por atasco, por ceder ni por carril equivocado. En la red anterior hubo dos en las mismas
  40 corridas. No se corrigió nada: es un efecto del simulador y está declarado (límite (c);
  `pruebas/correccion_carriles/humo_c2/choques/`).
- **La mayor parte de la baja frente a la red anterior viene de las fracciones, no de los carriles.** El revisor del
  humo corrió aparte, sobre copias, la red corregida con las fracciones que había a las 18:55 (28 de Julio 65, 15 y
  20; Balboa 65, 20, 10 y 5; no es la demanda del estudio): el plan actual daba 210.7 s/veh con la publicada (166.9 a
  264.6) y 449.8 con la alta (397.7 a 518.2; 640 vehículos sin terminar entre 18 de las 20 semillas, sin ninguna
  traba). De los 123.1 s/veh de baja con la publicada, 13.6 son de la red con su regla de carriles y 109.5 de las
  fracciones definitivas; con la alta, 62.6 y 171.2 de 233.8
  (`carriles_reducto_2026-11-18/verificacion/humo_plan/INFORME.md`, sección 2). Esa variante reproduce exactamente la
  corrida de prueba del constructor 1 (semilla 424301: 217.74 s/veh).

### Otras corridas del plan actual

Prueba rápida con las cuatro demandas (las dos de la robustez no entran en el humo de 20):

| Demanda | Semilla 424301 (s/veh) | Semilla 424302 (s/veh) | Sin terminar a los 6000 s | Trabas | Teletransportes | Segundos por corrida |
|---|---|---|---|---|---|---|
| Publicada | 97.9 | 85.1 | 0 | 0 | 0 | 6 |
| Alta | 290.3 | 232.0 | 0 | 0 | 0 | 12-14 |
| Robustez, más carga en Reducto | 102.5 | 83.5 | 0 | 0 | 0 | 6 |
| Robustez, más carga en 28 de Julio y Balboa | 273.8 | 208.9 | 0 | 0 | 0 | 9-11 |

En la prueba de punta a punta el plan actual corrió además en otras semillas de humo: 8 con la publicada y 8 con la
alta (424341-424348) y 4 con cada demanda de la robustez (424349-424352). Publicada: de 84.9 a 134.4 s/veh (media
95.7). Alta: de 199.6 a 303.5 (media 271.3). Robustez: de 91.7 a 107.7 y de 291.6 a 302.6. En las 24 corridas, 0
vehículos sin terminar (`pruebas/lanzadores/lima/**/salidas/eval_t*_actual.csv`).

En esas dos semillas, con la demanda publicada, lo que más espera es el giro de 28 de Julio hacia Reducto sur (426 y
466 s/veh), después Balboa hacia Larco (251 y 189) y Balboa hacia Reducto norte (225 y 167).

No se repitió: la prueba de equivalencia (su código no cambió) ni el humo de las referencias de 30 minutos (solo medía
tiempos). `pruebas/humo/correr_plan.py` quedó solo con las redes de esta carpeta (`final` y `giros`): las de comparación
de la mañana tienen los carriles de antes.

## Lanzadores

Todos en Git Bash, desde `C:/Users/GAMER/Documents/demo_rl_semaforo/nudo_ovalo_estudio2`. Todos comprueban las huellas
antes de hacer nada; lo ya hecho no se repite (se pueden cortar y volver a lanzar), salvo los entrenamientos, que no se
relanzan sobre una corrida empezada.

| Paso | Comando | Qué hace |
|---|---|---|
| Entrenar, orden libre | `bash entrenar.sh libre` | 6 entrenamientos (42, 2042, 4042 × publicada y alta), etiqueta `libre`: el modelo citado |
| Entrenar, orden fijo | `bash entrenar.sh completo` | 6 entrenamientos, etiqueta `completo` |
| Referencias | `bash referencias.sh [publicada\|alta\|ambas] --procesos N` | fijo ajustado y ciclo mínimo, actuado y actuado ajustado, comprobación del borde y validación de las referencias |
| Tandas de las referencias | `python evaluar_ovalo.py referencias [--nivel ...] --procesos N` | plan actual, fijo, actuado, actuado ajustado y ciclo mínimo, en 22001-22100 y 23001-23100 |
| Tandas de los modelos | `python evaluar_ovalo.py modelos [--nivel ...] --procesos N` | primero el citado de cada modelo en las dos tandas, después los otros dos |
| Robustez del reparto | `python evaluar_ovalo.py robustez --procesos N` | plan actual, fijo, actuado ajustado y el citado de cada modelo en 24001-24100 |
| Veredicto | `python evaluar_ovalo.py veredicto [--nivel ...]` | no simula: `salidas_ovalo/veredicto_ovalo.md` y `.json` |
| Verdes del modelo de orden fijo | `LIMA_PROGRAMA=programa_ovalo LIMA_CARPETA= python demo_rl/lima/estudio.py verdes-modelo --politicas politica_lima_vecinos_completo_s<b>.pt --procesos 8` (y `LIMA_CARPETA=alta`) | verde medio por estado en 21001-21008 |
| Secuencia de luces | `python figura_secuencia.py correr --nivel publicada` y `dibujar` (y `alta`) | los dos citados juegan la semilla 21001 con traza |
| Tablas y figuras | `python tablas_ovalo.py` | `salidas_ovalo/tesis/`: 6 tablas y 3 figuras |

**No copiar a esta carpeta ninguna política ni ningún programa del estudio detenido.** Una política de orden fijo de la
red anterior tiene el mismo tamaño y `evaluar_ovalo.py` no la distingue por la red (sí rechaza una de orden libre, por
la huella de `lima_libre.json`). Para saber de qué red es una política: en su `.json`, `cap` debe decir `RN_S1` 680 y
`RS_S1` 540.

**Tampoco copiar a `demo_rl/lima/` las políticas de humo.** En `pruebas/lanzadores/lima/` y
`pruebas/lanzadores/lima/alta/` hay 12 políticas de 2 episodios (base 7, validación en 424303-424304) que la prueba de
punta a punta guardó con los nombres de las bases del estudio (`_s42`, `_s2042` y `_s4042`): no son del estudio, y lo
dice un aviso en esa carpeta (`NO_SON_DEL_ESTUDIO.txt`). Fuera del modo de prueba, `evaluar_ovalo.py` las rechaza,
porque no tienen 400 episodios ni la validación en 21001-21008 (función `procedencia`). Las de `pruebas/humo/modelo/`
llevan el nombre de la base 7.

## Orden de ejecución y horas

Antes de nada: que veas lo que tu visto bueno de las 20:00 no cubría ("Problemas abiertos", 1 y 2); pegar
`enmienda_registro.md` en `lima/REGISTRO.md` (al final, después de "Detención del estudio del óvalo... (17:40)", que la
anuncia en "Lo que sigue"), con la hora en el título en lugar de HH:MM; y correr `bash entrenar.sh libre --comprobar`,
`bash entrenar.sh completo --comprobar` y `bash referencias.sh --comprobar`. Los tres deben decir "listo para lanzar".
La PC tiene que estar sola.

| Cuándo | Qué se lanza (Git Bash, desde `nudo_ovalo_estudio2`) | Procesos |
|---|---|---|
| Al empezar | `bash entrenar.sh libre > logs/entrenar_libre.out 2>&1 &` y `bash entrenar.sh completo > logs/entrenar_completo.out 2>&1 &` (los 12 a la vez) | 12 |
| Al empezar | `bash referencias.sh ambas --procesos 4 > logs/referencias.out 2>&1 &` (primero la publicada, después la alta) | 4 |
| Cuando `logs/referencias_publicada.log` diga "terminado" | `python evaluar_ovalo.py referencias --nivel publicada --procesos 4` | 4 |
| Cuando terminen los 6 entrenamientos de la publicada | `python evaluar_ovalo.py modelos --nivel publicada --procesos 6` y después `python evaluar_ovalo.py robustez --procesos 6` | 6 |
| Cuando termine `referencias.sh` con la alta | `python evaluar_ovalo.py referencias --nivel alta --procesos 4` | 4 |
| Cuando terminen los 6 de la alta | `python evaluar_ovalo.py modelos --nivel alta --procesos 12` | 12 |
| Con todo evaluado | verdes del modelo de orden fijo (las dos demandas), `figura_secuencia.py correr` y `dibujar` (las dos), `python evaluar_ovalo.py veredicto` y `python tablas_ovalo.py` | 8 |

Horas. Lo medido es de la corrida detenida (red y demanda anteriores,
`carriles_reducto_2026-11-18/pruebas-lanzadores/INFORME.md`): los entrenamientos de la publicada tardaron 5 h 10 min
(orden fijo) y 5 h 45 min a 6 h 35 min (orden libre); los de la alta iban para 9.5 a 11 h; las referencias de la
publicada, 2 h 37 min. Con eso el estudio entero son **14 a 16 h** si cada paso se lanza en cuanto puede, y 17 a 19 h
si los pasos de la madrugada esperan. En la red corregida, el revisor del humo de los modelos midió que un episodio
tarda de 0.69 a 0.83 veces lo que tardaba en la red anterior (con las mismas políticas, semillas y carga) y con eso
estima el estudio entero en **9 a 11 h** con la PC libre, si cada paso se lanza en cuanto puede: entrenamientos de
orden fijo, 3 h 45 a 4 h 17 la publicada y 6 h 35 a 7 h 53 la alta; de orden libre, 4 h 24 a 5 h 11 y 7 h 34 a
9 h 04 (`carriles_reducto_2026-11-18/verificacion/humo_modelos/INFORME.md`, sección 6). **Es una estimación**: no se
puede medir sin correr el estudio, sus medidas son con 8 procesos y no con 16, y la corrida detenida compartió la PC
con el diagnóstico entre las 16:00 y las 17:40.

Las referencias secundarias, el actuado de SUMO por defecto y el ciclo mínimo, casi no se aceleran en la red corregida
(0.84 a 1.03 veces lo de antes, frente a 0.39 a 0.59 de los fijos y del actuado por retraso) y dejan cientos de
vehículos sin terminar. Si sus tandas de la alta corren con 4 procesos, pueden terminar después que los modelos: cuando
se libere la PC, conviene lanzar `python evaluar_ovalo.py referencias --nivel alta` con más procesos. Cada semilla
corre por separado, así que el número de procesos no cambia ningún resultado (en la prueba de punta a punta, el plan
actual dio las mismas cifras con 6 y con 8).

Si la PC tiene otra carga, todo se alarga; si algo se corta, se vuelve a lanzar el mismo paso. Los entrenamientos no:
`rl_ippo.py` reescribe su CSV y hay que mover a mano lo de esa etiqueta; un entrenamiento cortado no se puede reanudar.
Seguimiento: `tail -1 logs/libre_*.log logs/completo_*.log`; la columna `tope_excedido` del CSV de cada entrenamiento
libre debe quedar en 0. En las trazas de prueba, el reloj del tope del orden libre llega a 163 s justos y no pasa: es la
regla (tope de 163 s), no una falla.

## Ver la simulación en sumo-gui (cuando existan las políticas)

No se corrió con ventana. Desde Git Bash o PowerShell, cuando terminen los entrenamientos:

```
cd C:/Users/GAMER/Documents/demo_rl_semaforo/nudo_ovalo_estudio2
python ver_ovalo.py                                         # plan de hoy | modelo de orden libre, demanda publicada
python ver_ovalo.py --controles hoy,completo,libre          # plan de hoy | orden fijo | orden libre
python ver_ovalo.py --demanda alta --semilla 21002 --retardo 50
```

Abre una ventana por control, lado a lado, con los mismos vehículos (misma semilla; por defecto 21001, de validación) y
la vista centrada en el óvalo. De cada modelo juega el entrenamiento citado (validación mediana). `--retardo` son
milisegundos por segundo simulado (100: la hora en unos 6 minutos). Cada control corre en su propia copia de la
carpeta (`ver/`).

## Huellas

`huellas.sha256` lista 73 archivos (`archivos_huellas.txt`), con el criterio del estudio detenido: los lanzadores, el
código de `demo_rl/`, la red con sus entradas y los datos de las cuatro carpetas de trabajo. Frente a la lista de 71 del
estudio detenido:

- entran 4: `demo_rl/lima/ovalo/regenerar_demanda.py`, `demo_rl/plan3/demanda_estocastica.py`,
  `demo_rl/escenarios_plan3.py` (código nuevo de la demanda) y `demo_rl/lima/ovalo/red/e2_ovalo_estudio_75.add.xml`
  (de donde salen ahora los detectores de las cuatro carpetas);
- salen 2: `entrada/e2_lima_75_estudio.add.xml` y `entrada/plan_actual_revision.add.xml`, referencias de la red
  anterior que ya no usa ningún programa (los archivos siguen en la carpeta);
- de los 69 que están en las dos listas, 33 tienen la misma huella y 36 cambiaron (la red, la demanda, el plan, el
  programa libre, los detectores y ocho programas).

`entrenar.sh`, `referencias.sh`, `evaluar_ovalo.py`, `tablas_ovalo.py` y `figura_secuencia.py` comprueban las huellas
antes de hacer nada y no corren si algo cambió. Cada política guarda en su meta las huellas del código con que se
entrenó y `evaluar_ovalo.py` no evalúa una que no las traiga o que traiga otras.

**No volver a armar la red** (`armar_ovalo.py`, `preparar_carpetas.py`) ni regenerar la demanda después de sacar las
huellas: la cabecera de `lima.net.xml` lleva la fecha y su huella cambia aunque la red sea la misma. Si hay que
corregir un programa (regla del REGISTRO: solo errores de código, anotados con fecha):
`sha256sum $(cat archivos_huellas.txt) > huellas.sha256` desde esta carpeta, y anotar las nuevas huellas. Son huellas
de los bytes: `rl_ippo.py` va con fin de línea CRLF, como en el repositorio.

## Problemas abiertos y límites

1. **La enmienda está escrita; falta pegarla.** `enmienda_registro.md` es la de la red corregida (la de las 11:03 sigue
   en `nudo_ovalo_estudio/enmienda_registro.md`). Dice los carriles con tu confirmación y tu visto bueno, qué cambió y
   qué no, lo que cambió sin elegirlo, la demanda, las simplificaciones, los límites (a), (b) y (c), el límite del paso
   2 a 1 y que se registra después de ver los resultados parciales de la corrida detenida y el diagnóstico. Hay que
   pegarla en `lima/REGISTRO.md` con la hora antes de lanzar ("Orden de ejecución y horas").
2. **Lo que tu visto bueno de las 20:00 no cubría.** Fue sobre la tabla y el mapa, que no dan estas cifras. Conviene
   que lo veas antes de lanzar, porque cambiarlo después cuesta el estudio entero:
   - **Lugar libre.** Los lados norte (4.62 m) y este (4.08 m) ya no tienen lugar para un auto entero (antes 6.71 y
     6.33 m); el sur sube a 5.64 m y el oeste sigue en 5.28 m (1 auto por carril). En el este espera Balboa hacia
     Reducto norte antes de ceder. Con el plan actual no hubo ninguna traba (0 de 40 corridas), ni con la regla fija de
     seis pasos del revisor de las luces (4 corridas). Si no lo aceptas como límite declarado, hay que rearmar la red
     (por ejemplo, cambiando dónde cruzan los ramales de giro; el constructor tiene la opción `--ramales`, que no se
     probó con los carriles nuevos): cambia la huella de la red, tu visto bueno deja de valer y hay que repetir todas
     las pruebas y las huellas.
   - **La espera del giro del puente hacia Reducto sur.** En la red cabe un auto en el lado oeste, no tres lado a lado
     como en tu foto, y en la práctica esperan en fila antes de la primera esquina. Lo muestra la figura de los estados
     (`carriles_reducto_2026-11-18/validacion/fig_ovalo_estados_pantalla.png`: "lado oeste, 5.3 m (cabe 1)" y "lado
     este, 4.1 m (no cabe entero)"), que no estaba en tu visto bueno. Ya está declarado como límite (a).
3. **El nivel del plan actual depende de fracciones supuestas.** Con las definitivas da 101.2 s/veh con la publicada
   (20 semillas); con las de las 18:55 (20 % de 28 de Julio hacia Reducto sur y 10 % de Balboa hacia Reducto norte)
   daba 210.7. No hay conteo de esos giros.
4. **Los tres giros que esperan adentro** (28 de Julio hacia Reducto sur, y Balboa hacia Reducto norte y hacia Larco)
   son el 4.6 % de los vehículos y el 19.2 % del retraso con la publicada: ver "Límites declarados", (a) a (c), también
   los choques por alcance dentro del óvalo.
5. **El actuado de SUMO por defecto sigue dando retrasos muy altos en el óvalo**: 890 y 853 s/veh con la publicada y
   1157 y 1160 con la alta (cuatro semillas de humo cada cifra, en la prueba de punta a punta). Con hueco de 1 s y
   umbral de atasco, una variante de la búsqueda, dio 87.8 en una semilla. Es una referencia secundaria; el actuado
   ajustado sale de la búsqueda.
6. **Límites que ya estaban y siguen**: el paso 2 a 1 del programa libre (arriba); el verde máximo de 60 s de los
   modelos y del actuado; `estudio.py verdes-modelo` no sirve para el modelo de orden libre; la lectura `giro_izq` de
   la observación mira el primer tramo del giro, que está en la línea de parada de afuera (ahora de cuatro carriles:
   `RN_S1_3`, `RN_S1_4`, `RS_S1_2` y `RS_S1_3`; el giro de Balboa hacia Larco no la enciende); la comparación entre los
   dos modelos mide el efecto conjunto de elegir el orden y de lo que trae consigo.
7. **Nada de esto está en el repositorio.** La demanda del repositorio (`demo_rl/lima/demanda.py`) y la tabla de
   demanda de la tesis tienen todavía los carriles de antes.
