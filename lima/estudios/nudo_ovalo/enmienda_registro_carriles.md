## Enmienda: el nudo en la red del Óvalo Vasco con los carriles corregidos (18.11.2026, 23:45)

Se registra antes de ajustar las referencias, de entrenar y de evaluar en la red corregida. Para el estudio del nudo
reemplaza, de la enmienda de las 11:03, la red, la demanda, las pruebas, el código, las huellas y el orden de
ejecución. Los controles, los modelos y sus opciones, las semillas, las comparaciones, la regla del veredicto y la
prueba de robustez siguen tal como quedaron registrados a las 11:03, con la corrección de las 11:33. En la red
corregida solo se usaron la base 7 (episodios con las semillas 8 a 12 de SUMO) y semillas de humo del bloque
424301-424360 (424301-424320 y 424341-424355); ninguna semilla de ajuste (2001-2030), de validación (21001-21008) ni
de evaluación (22001-22100, 23001-23100 y 24001-24100), y ninguna de las bases 42, 2042 y 4042. Además, para leer los
avisos de SUMO, se cargaron tres redes durante 1 s con la semilla por defecto de SUMO, que no es del estudio.

**Qué se sabía al registrar.** Esta enmienda se escribe después de la detención de las 17:39 y de sus resultados
parciales (anotados a las 17:40), del diagnóstico de por qué el modelo de orden libre validó peor que el de orden fijo
(`diagnostico_orden_ovalo_2026-11-18/DIAGNOSTICO.md`) y de las pruebas de humo de la red corregida (abajo). En la red
anterior ya se usaron las semillas de ajuste, de validación y de las dos tandas; las de la robustez, no. Nada de eso se
informa y nada del método cambia por ello: el modelo citado sigue siendo el de orden libre. Cambian la red, con los
carriles confirmados en el sitio, y la demanda que sale de ella con la misma regla, con las fracciones de 28 de Julio y
de Balboa fijadas el 18.11.2026 con lo que dijo Fabian Alvarado ("La demanda"). Se deja dicho: el diagnóstico había
encontrado que los dos giros que esperan adentro, con su demanda supuesta, llevaban del 30 al 44 % del retraso
(`DIAGNOSTICO.md`, sección 7), y sus fracciones bajaron después con lo que dijo Fabian (28 de Julio hacia Reducto sur,
de 20 a 10 %; Balboa hacia Reducto norte, de 10 a 5 %).

**La red: qué cambió.** Fabian Alvarado revisó la red contra el lugar (18.11.2026, entre las 17:15 y las 17:35) y
confirmó por escrito ese mismo día los carriles de cada entrada y el giro de Balboa hacia Larco. El carril 0 es el de
la derecha del conductor.

| Entrada | Antes | Ahora |
|---|---|---|
| Reducto desde el norte (`RN_S1`) | 4 carriles: 3 de frente (el derecho también hacia Larco) y 1 de giro hacia el puente | 5: el 0 de frente y hacia Larco; el 1 y el 2 de frente; el 3 y el 4 solo giran hacia el puente |
| Reducto desde el sur (`RS_S1`) | 5: 1 solo hacia el puente, 2 de frente y 2 de giro hacia Larco | 4: el 0 de frente y hacia el puente; el 1 de frente; el 2 y el 3 solo giran hacia Larco |
| Balboa (`B_S1`) | 3: el 0 hacia el puente y Reducto sur; el 1 hacia el puente; el 2 hacia el puente y Reducto norte | igual, y el 2 gira además hacia Larco (movimiento nuevo) |
| 28 de Julio desde el puente (`J_S1`) | 3: el 0 hacia Larco y Reducto norte; el 1 hacia Larco; el 2 solo hacia Reducto sur | sin cambios |

- Las salidas no cambian: hacia Larco 2 carriles, Reducto norte 2, Reducto sur 3 y el puente 3. Adentro cambia solo lo
  que piden esos carriles: el ramal de giro del norte pasa de 1 a 2 carriles antes y después de cruzar (`RN_NE`,
  `NE_MJ`), la calzada principal del sur de 3 a 2 (`RS_SE`) y el ramal de giro del sur sigue con 2 (`RS_SO`).
- Balboa hacia Larco va por un tramo propio de 1 carril y 45.24 m (`B_ML`), de la línea de parada de Balboa a la unión
  de la salida hacia Larco, por el oeste, como en OpenStreetMap (vía 366715629), sin cruzar los lados del óvalo (su eje
  pasa a 4.99 m o más de los carriles de los lados). Tiene verde junto con Balboa. Queda sin efecto la decisión del
  13.11.2026 de dejarlo fuera ("Decidido antes"): Fabian Alvarado confirmó que existe y dio su demanda.
- Quedan 13 movimientos (antes 12), sin vuelta en U. `semaforo_S1` maneja 57 enlaces en los mismos 10 nodos (antes
  53). Hay 15 detectores E2 de 75 m, uno por carril de entrada (5 + 4 + 3 + 3). La matriz de las esquinas lleva 74
  cesiones (antes 66).
- No cambian: la posición de los 10 nodos del semáforo (0.000 m), las distancias de esquina a esquina (norte 18.44 m,
  oeste 24.43 m, este 19.92 m y sur 15.74 m), la isla (107.79 m²), el ancho de carril (3.2 m), las velocidades que se
  fijan (13.89 m/s y los mismos cinco giros de adentro a 5.56 m/s), los largos de las entradas (1026.52, 1014.75,
  1019.89 y 1021.64 m) y de las salidas, las reglas de adentro y el `.sumocfg`, con la válvula de 10 s.
- Con los carriles de antes, el constructor nuevo vuelve a dar la red de las 11:03, byte a byte salvo la cabecera.
- El 18.11.2026, hacia las 20:00, Fabian Alvarado dio su visto bueno a la tabla de carriles y demanda y al mapa de la
  red (`carriles_reducto_2026-11-18/validacion/tabla_carriles_demanda.png` y `fig_ovalo_mapa_pantalla.png`), hechos
  con la red, el plan actual y la demanda publicada de esta enmienda (`d41d816a…`, `140a3ccb…` y `db3afbf5…`).
- Lo que ese visto bueno no cubría (el párrafo que sigue, la causa del límite (a) y el defecto del paso 2 a 1) se le
  explicó antes de lanzar, entre las 22:35 y las 23:35, con cuatro figuras hechas para eso
  (`carriles_reducto_2026-11-18/explicacion_fabian/`: el lado norte en las dos redes, qué es el lado norte, la fila de
  ese giro estirada a escala y el paso 2 a 1; las dibuja `figuras_explicacion.py` con las dos trazas del humo). Él
  aportó cuatro capturas de Street View del óvalo (`carriles_reducto_2026-11-18/capturas_fabian/streetview_*.png`). Se
  le ofrecieron dos caminos: A, lanzar con la red de su visto bueno y declarar los dos puntos como límites; B,
  corregirlos (que los giros que esperan adentro puedan detenerse encima de un cruce y que en el paso 2 a 1 salgan
  primero los de adentro), repetir las pruebas y lanzar de madrugada. El asistente de IA que arma el estudio le dijo
  que B daría resultados más fieles al sitio, que no se puede saber de antemano cuál favorece al modelo y que no debe
  elegirse por eso. Fabian Alvarado eligió A el 18.11.2026, hacia las 23:35, por tiempo y riesgo, sin ningún resultado
  de la red corregida a la vista.

**La red: lo que cambió sin elegirlo.** Se declara:
- El lugar libre de los lados (el largo entre los bordes de dos esquinas; caben autos de 5 m con 2.5 m de hueco): el
  norte baja de 6.71 a 4.62 m (de 1 auto por carril a ninguno) y el este de 6.33 a 4.08 m (de 1 a ninguno); el sur sube
  de 4.04 a 5.64 m (de ninguno a 1); el oeste sigue en 5.28 m (1). Viene de que el borde de la esquina NE llega hasta el
  cruce del ramal del norte, que ahora tiene 2 carriles (NE se lleva 8.84 de los 18.44 m del lado norte, antes 6.74, y
  11.02 de los 19.92 m del este, antes 8.77), y de que la calzada del sur es más angosta (SE se lleva 3.21 m del lado
  sur, antes 4.81). Los cruces de los ramales quedaron donde estaban, a la misma distancia de su esquina que en
  OpenStreetMap. El lado norte más corto es lo que más pesa en el giro del puente hacia Reducto sur (límite (a)).
- La forma de las esquinas: NE pasa de 129.95 a 169.75 m² y SE de 92.49 a 62.03 m². Cambia el largo del tramo interno
  de 23 de las 47 conexiones que existen en las dos redes (por ejemplo, 28 de Julio hacia Reducto sur en NE, de 9.27 a
  11.43 m, y Balboa hacia Reducto norte en SE, de 4.36 a 2.96 m) y el de `RN_NO` (de 12.46 a 12.38 m), `RS_SO` (de
  21.00 a 21.42 m) y `SE_MJ` (de 4.61 a 6.22 m).
- Las entradas de Reducto siguen centradas en su nodo con otro número de carriles, así que en la línea de parada sus
  carriles se corren 1.6 m de lado (los nodos no se mueven): los tres de frente del norte pasan de −4.8, −1.6 y 1.6 m a
  −6.4, −3.2 y 0.0 m del eje (positivo a la izquierda) y `RN_NO` arranca 1.60 m más a la derecha; en el sur, el carril
  derecho de `RS_SE` pasa de −6.52 a −4.92 m y el ramal `RS_SO`, de 2.65 y 5.84 m a 1.01 y 4.21 m. De ahí salen los
  largos nuevos de `RN_NO` y `RS_SO` y la forma de las líneas de parada: `P_RN` pasa de 22.30 a 32.06 m² y `P_RS` de
  32.22 a 26.87 m².
- Los carriles de Reducto norte terminan 0.26 m antes y los de Reducto sur 0.10 m antes (los corta así netconvert;
  miden lo mismo y sus nodos no se movieron). Los de Balboa y de 28 de Julio terminan donde terminaban.
- Velocidades que calcula netconvert y que no se fijan: cambian 4 de las 47 conexiones comunes (el primer carril del
  giro del norte en su línea de parada, de 12.40 a 13.89 m/s; 28 de Julio hacia Reducto sur en NE, de 13.39 a 13.89;
  las dos de `SE_MJ` hacia el puente, de 11.59 a 11.57 y de 13.29 a 13.27). En las conexiones nuevas: el giro del sur
  en su línea de parada queda en 8.87 m/s (`RS_S1_3`, tramo de 1.52 m; su equivalente de antes, `RS_S1_4`, 12.54) y en
  11.73 (`RS_S1_2`; antes `RS_S1_3`, 13.89); el segundo carril del giro del norte, en 11.54 (`RN_S1_4`); Balboa hacia
  Larco entra a la unión a 10.70. Los tramos internos por debajo de 13.89 m/s pasan de 12 a 14; ninguno queda por
  debajo de 5.56.
- Los enlaces del semáforo se renumeran (3 de los 57 conservan su número): ningún programa ni ninguna política de la red
  anterior sirve en esta.

**Simplificaciones declaradas.**
1. Los carriles de giro de Reducto son carriles completos de la entrada (1 km), ahora en las dos entradas. En el sitio,
   la del norte es una avenida de 3 carriles con un ensanche de 2, y la del sur, una calzada de 2 que se abre a 4 poco
   antes del semáforo. La red le da a Reducto más lugar para la cola del que tiene. Es igual para todos los controles.
2. Reducto sur gira a la derecha, hacia el puente, solo desde el carril 0. Fabian dijo que los dos carriles de la
   derecha pueden seguir de frente o girar; el giro desde el carril 1 cruzaría al carril 0, que sigue de frente.
3. El carril del medio de Balboa va solo de frente: los giros hacia Reducto norte y hacia Larco salen solo del carril
   izquierdo. Fabian dijo que desde el carril del medio también se gira; no se modela, por el mismo motivo.
4. Sin vuelta en U desde Reducto norte.
5. Balboa hacia Larco es un ceda el paso en la unión: en su línea de parada tiene el verde de Balboa y en la unión
   nunca tiene prioridad. Cede a los cuatro enlaces que llegan a la salida hacia Larco (28 de Julio de frente y los
   giros de Reducto norte y de Reducto sur hacia Larco), no solo a 28 de Julio de frente. Con la regla general, ese
   giro y el carril derecho hacia Larco quedaban cediéndose uno al otro toda una fase (39 s con la demanda publicada y
   dos veces 38 s con la alta, semilla 424301). El tramo `B_ML` se superpone al carril izquierdo de Balboa en sus
   primeros 16.2 m (nacen en el mismo punto) y a los dos carriles del ramal de giro de Reducto sur en sus últimos metros
   (18.1 m el izquierdo y 10.2 m el derecho); SUMO no hace que esos vehículos se estorben hasta la unión.
6. Lo que ya estaba declarado: el que gira y cruza al otro flujo (28 de Julio hacia Reducto sur, en la esquina SO, y
   Balboa hacia Reducto norte, en la NE) cede en su segunda esquina y espera adentro; quien quedó adentro al cambiar la
   luz sale primero; un solo semáforo para los 10 nodos; la válvula de 10 s. Es lo que describió Fabian el 18.11.2026:
   los que vienen del puente y giran hacia Reducto sur no esperan ningún semáforo, ceden el paso a Balboa y avanzan
   cuando Balboa deja de pasar; los de 28 de Julio que siguen hacia Larco tienen preferencia.

**El semáforo.** El plan actual no cambia: Reducto de frente 37 s y 3 de ámbar, giros a la izquierda de Reducto 15 y 3,
todo en rojo 34 s, 28 de Julio y Balboa 37 y 3; ciclo de 132 s. Los tres estados tienen los mismos movimientos, más
Balboa hacia Larco, que va con 28 de Julio y Balboa; los dos giros a la izquierda de Reducto siguen juntos. Las luces
salen de la regla de siempre sobre la red; lo único agregado a mano es el ceda el paso de Balboa hacia Larco. Se
comprobó sin simular, con el programa del estudio y con un descifrado independiente: los 47 enlaces que existen en las
dos redes y los 12 movimientos que ya existían llevan, en cada punto de su camino, la misma luz que en la red anterior,
en las 7 fases del plan y en las 12 del programa del orden libre; las 60 relaciones de quién cede a quién entre esos
movimientos no cambian; ninguna fase da prioridad a la vez a dos enlaces que se cruzan.

**El modelo.** El código no cambia. Lo que lee de la red cambia con los carriles: la capacidad con que divide las colas
(Reducto norte 680 y Reducto sur 540, antes 544 y 675; Balboa 405 y 28 de Julio 408, como antes); los carriles de cada
estado (Reducto de frente `RN_S1_0-2` y `RS_S1_0-1`; giros `RN_S1_3`, `RN_S1_4`, `RS_S1_2` y `RS_S1_3`; 28 de Julio y
Balboa `B_S1_0-2` y `J_S1_0-2`); y los de la lectura `giro_izq`, que son los cuatro carriles de giro de Reducto (la red
marca de frente el giro de Balboa hacia Larco, así que no la enciende). La observación sigue con 50 entradas (orden
fijo) y 56 (orden libre).

**La demanda.** La misma regla: el total publicado de 4271 veh/h se reparte en proporción a carriles por segundos de
verde medidos de cada grupo y, dentro de cada grupo, por destino. Grupos: Reducto norte de frente 3 × 38 s, su giro
2 × 18, Reducto sur de frente 2 × 40, su giro 2 × 18, 28 de Julio 3 × 38 y Balboa 3 × 40 (suma 500; antes 522).
Destinos: Reducto norte de frente, 90 % a Reducto sur y 10 % a Larco; Reducto sur de frente, 80 % a Reducto norte y
20 % al puente; los giros, 100 %; 28 de Julio, 75 % a Larco, 15 % a Reducto norte y 10 % a Reducto sur (antes 65, 15 y
20); Balboa, 70 % al puente, 20 % a Reducto sur, 5 % a Reducto norte y 5 % a Larco (antes 55, 35 y 10, sin Larco). Las
fracciones de 28 de Julio y de Balboa se fijaron el 18.11.2026 con lo que dijo Fabian Alvarado: adentro del óvalo
caben unos 3 autos esperando el giro del puente hacia Reducto sur (foto
`carriles_reducto_2026-11-18/capturas_fabian/28_espera_dentro_del_ovalo.png`) y de Balboa a Reducto norte suben "muy
pocos". Flujos de la demanda publicada (veh/h):

| Entrada | Hacia | Antes | Ahora |
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

Por entrada: Reducto norte 1281.3, Reducto sur 990.9, 28 de Julio 973.8 y Balboa 1025.0 veh/h (antes 1080.0, 1276.4,
932.7 y 981.8). La alta es la publicada por 1.2, flujo por flujo (5125.2 veh/h). Las dos de la prueba de robustez se
derivan como en esa prueba (13.11.2026, 22:10), con el mismo total publicado (4271.0 veh/h cada una). La mezcla de
vehículos y las llegadas aleatorias son las de antes. Las fracciones están en un solo sitio (`demo_rl/lima/demanda.py`,
líneas 52 y 53) y no se vuelven a cambiar.

**El plan actual en la red corregida** (humo: 20 semillas por demanda, 424301-424320; lo corrieron por separado el
constructor y un revisor, este dos veces, con la misma simulación vehículo por vehículo):
- 101.2 s por vehículo con la demanda publicada (76.0 a 168.7; nivel F en 19 de 20 semillas) y 278.6 con la alta
  (228.0 a 324.1). Ninguna traba en las 40 corridas y ningún vehículo sin entrar ni sin terminar a los 6000 s. En la
  red anterior, con su demanda y las mismas semillas, daba 224.3 y 512.4.
- La mayor parte de la baja viene de las fracciones, no de los carriles. Con la red corregida y las fracciones que
  había a las 18:55 (28 de Julio 65, 15 y 20; Balboa 65, 20, 10 y 5), el plan actual daba 210.7 y 449.8 s por
  vehículo. De la baja, 13.6 y 62.6 s son de la red con su regla de carriles, y 109.5 y 171.2 s de las fracciones
  definitivas.
- Como en la red anterior, el retraso simulado del nudo no se compara con el nivel de servicio publicado: los
  resultados comparan controles en esta red.

**Límites declarados.** El 18.11.2026 a las 19:51, al informar el humo, el asistente de IA que arma el estudio propuso
no cambiar las fracciones y declarar estos límites con sus cifras del humo (demanda publicada y 20 semillas, salvo que
se diga otra cosa); Fabian Alvarado dio su visto bueno a la tabla de carriles y demanda a las 20:00 y, con la causa
del límite (a) ya explicada, eligió mantenerlos a las 23:35 (camino A, arriba). La causa del límite (a) se midió entre
las 21:30 y las 21:54, en una comparación aparte sobre copias.
- (a) El giro del puente hacia Reducto sur pide 97.4 veh/h (3.6 por ciclo) y la red deja pasar unos 70 (2.5 por
  verde en los verdes con cola; Fabian vio unos 3 esperando adentro): atiende 69.3, el 74 %. Con el plan actual
  acumula cola: 599.5 s por vehículo (288.5 a 914.9 según la semilla), el 13.4 % del retraso con el 2.2 % de los
  vehículos; con la alta atiende el 57 % de lo que pide y espera 1112.7 s. El 96.5 % sale del óvalo con Reducto de
  frente ya en verde, es decir, cuando Balboa dejó de pasar, como en el sitio. Al final del verde quedan 2.3 detenidos
  adentro (hasta 4): el 79 % antes de la primera esquina, el 18 % en el lado norte y el 3 % en el oeste; en el oeste,
  donde la foto muestra tres lado a lado, nunca hubo más de uno. Causa: la comparación aparte (no es la red ni la
  demanda del estudio) corrió la red anterior con la demanda definitiva sin Balboa hacia Larco, con el mismo plan y las
  mismas semillas. Ahí ese giro dejaba pasar unos 95 veh/h (3.5 por verde con cola), atendía 91.0 (el 93 %) y esperaba
  271.0 s por vehículo, y el primero de la fila esperaba en el lado oeste en el 71 % de los verdes que dejaron a
  alguien adentro (en la red corregida, en el 7 %). En su camino solo cambian la esquina NE y el lado norte, que bajó
  de 6.71 a 4.62 m al crecer la esquina con el ramal de 2 carriles; las luces y las cesiones son las mismas. La
  diferencia se atribuye al lado norte; no se probó una red que cambie solo eso. Bajar la fracción del giro pasaría la
  carga a los dos carriles de frente de 28 de Julio, que ya están al 97 % de lo que el plan deja pasar. En el sitio, el
  interior del óvalo es una explanada sin carriles pintados donde los autos esperan donde caben, uno al lado del otro o
  encima de un cruce mientras el otro flujo tiene rojo (la foto `28_espera_dentro_del_ovalo.png` y las capturas de
  Street View de Fabian Alvarado, en `carriles_reducto_2026-11-18/capturas_fabian/`). En el simulador nadie espera
  encima de un cruce: la red le da a este giro menos lugar de espera que el sitio y lo atiende menos de lo que pasaría
  allí. Pesa igual para todos los controles.
- (b) Balboa hacia Reducto norte y Balboa hacia Larco atienden el 94 y el 93 % de lo que piden (47.8 de 51.1 y 47.1 de
  50.7 veh/h; 239.5 y 246.5 s por vehículo). Comparten el carril izquierdo de Balboa, que pierde el 39 % de su verde:
  el que gira hacia Reducto norte espera casi siempre antes de su primera esquina (el 77 % de los detenidos al final del
  verde; el 19 % en el lado sur y el 3 % en el este) y detrás de él no pasa nadie. En la red anterior, con la misma
  demanda, esperaba en los mismos sitios (74 % antes de la primera esquina y 4 % en el este) y pasaba casi lo mismo
  (56 veh/h en los verdes con cola, frente a 52; más en la anterior solo en 11 de 20 semillas): el lado este más corto
  no lo cambia. Balboa hacia Larco espera siempre en su tramo propio.
- (c) 4 choques en las 40 corridas del humo (1 con la publicada y 3 con la alta): un bus (3 veces) o una combi alcanza,
  a velocidades de 1.90 a 4.03 m/s, a un auto casi detenido en los tramos cortos de Reducto antes de su esquina
  (`RN_NO` 3 veces, `RS_SE` 1), y SUMO retira al que choca (un teletransporte por choque). Ningún teletransporte por
  atasco, por ceder ni por carril equivocado. En la red anterior hubo 2 en las mismas 40 corridas.
- Además: con la publicada, 28 de Julio de frente y Balboa quedan al 97 % de lo que el plan deja pasar, así que el
  resultado de cada control puede depender bastante de la semilla. Con la alta, 11 de los 13 movimientos atienden menos
  de lo que piden y 7 pasan de 300 s por vehículo.

**Límite conocido del programa del orden libre, que no se corrige.** El diagnóstico demostró un defecto del programa
libre (`DIAGNOSTICO.md`, secciones 5, 7 y 8): si el modelo pasa de 28 de Julio y Balboa directamente a los giros de
Reducto (el paso "2 a 1", que el plan actual no tiene), los que quedaron adentro no salen durante ese verde ni durante
el siguiente, hasta el todo rojo, porque la regla "quien está adentro sale primero" solo recuerda el estado anterior.
Con una regla fija que repite ese paso, el retraso sube 97 %; los modelos de la corrida detenida lo usaron de 3 a 10
veces por política en dos episodios y no es la causa de su resultado. En la red corregida, con una regla fija que
recorre los seis pasos, hubo 20 detenciones de 60 a 70 s dentro del óvalo en 4 corridas, y todas empiezan tras ese
paso; con el plan actual, ninguna. La entrada de las 17:40 ("Lo que sigue") preveía anotar aquí su corrección si el
diagnóstico demostraba un defecto del programa libre. No corregirlo lo decidió el asistente de IA que arma el estudio
al escribir el encargo de la red corregida (hacia las 18:10), para no cambiar nada del método y sin consultarlo: a las
17:58 se le había dicho a Fabian Alvarado que el diagnóstico no encontró ningún defecto, lo que no era exacto. Se le
corrigió antes de lanzar, con la figura del paso 2 a 1. Él propuso la corrección natural (que en ese salto salgan
primero los de adentro y después pasen los giros), que es la del camino B, y eligió el camino A: el defecto queda como
límite declarado, con su prueba, y su corrección como trabajo futuro.

**Pruebas en la red corregida** (base 7 y semillas de humo; en `nudo_ovalo_estudio2/pruebas/` y en
`carriles_reducto_2026-11-18/verificacion/`, `verificacion2/`, `validacion/` y `validacion2/`).
- La red frente a la especificación de Fabian, carril por carril, y frente a la red anterior (sumolib; el constructor
  y un revisor, dos veces, con programas propios): los 15 carriles de entrada llegan exactamente a sus salidas; 13
  movimientos, cada uno con un solo camino; salidas, largos, nodos e isla como antes. Con copias del código, la red
  (salvo su cabecera, que lleva la fecha), el plan, el programa libre y las 8 demandas se rehacen byte a byte.
- El semáforo, sin simular (arriba), y 8 corridas con traza (el plan actual y una regla fija de seis pasos, semillas
  424301 y 424302): 0 fallas en la comprobación segundo a segundo de las luces y 0 cruces en rojo.
- La demanda, con una cuenta propia de la regla: las 52 tasas de cada uno de los 8 archivos, con 0.0018 veh/h de
  diferencia como máximo.
- El plan actual, 20 semillas por demanda: arriba y en los límites. La comparación aparte de la causa de (a), sobre
  copias de la red anterior: 20 semillas, las mismas.
- Los dos modelos, 5 episodios con la base 7 y su validación en 424303-424304, con las dos demandas y dos copias: 0
  fallas de luces en las 8 trazas (56 episodios); el de orden libre usa los seis pasos (905 de 1724 y 817 de 1658
  cambios fuera del orden del plan, `tope_excedido` 0); el de orden fijo, ninguno fuera del orden; las copias dan lo
  mismo byte a byte, también entre dos sesiones; observación de 50 y 56 entradas; `rl_ippo.py` no reescribe ningún dato.
  Políticas ya entrenadas (de la corrida detenida y de la red del estudio) jugando en la red corregida, solo para medir
  tiempos y sin citarse: 0 fallas de luces en 16 trazas.
- Los lanzadores de punta a punta con semillas de humo (424341-424355): todos los pasos corrieron, dos veces. Con un
  verde del plan cambiado en una copia, los nueve intentos de lanzar se niegan. Con `--comprobar`: "listo para lanzar".

**Código y datos.** Carpeta `nudo_ovalo_estudio2/`, copia de `nudo_ovalo_estudio/` sin ningún resultado de la corrida
detenida (`ORIGEN.md`). Son los del estudio detenido, byte a byte: `rl_ippo.py` y los módulos que usa, `estudio.py`,
`programa.py`, `programa_ovalo.py`, `borde_actuado.py`, `entrenar.sh`, `referencias.sh` y `comprobar_fases.py`; y
`evaluar_ovalo.py`, `figura_secuencia.py` y `ver_ovalo.py`, con la corrección de las 11:33. Cambian solo los programas
que arman la red y la demanda, dos módulos que se copian del repositorio y dos auxiliares:
- `demo_rl/lima/ovalo/armar_ovalo.py`: los carriles de las cuatro entradas en una sola tabla y el tramo `B_ML`;
- `demo_rl/lima/ovalo/plan_ovalo.py`: el ceda el paso de Balboa hacia Larco;
- `demo_rl/lima/demanda.py`: los carriles de los grupos y las fracciones; `demo_rl/lima/ovalo/regenerar_demanda.py`
  (nuevo), `preparar_carpetas.py`, `comprobar_red.py` y `armar_rutas.py`: se comprueban contra la tabla de carriles y
  la red, no contra la red anterior;
- `demo_rl/escenarios_plan3.py` y `demo_rl/plan3/demanda_estocastica.py` (nuevos en la carpeta): copias sin cambios del
  repositorio, que usa `demanda.py`;
- `comprobar_referencias.py` cuenta en la red los carriles de adentro, que en los actuados llevan un detector que no
  cuenta a nadie (36; antes un 34 escrito a mano); `tablas_ovalo.py`, una palabra de un comentario.

Huellas sha256:
- `demo_rl/rl_ippo.py`: c61b706c7a96baa07ca9737564a5124c50bea7da911e5c77805dd62b784e4bc7 (sin cambios)
- `demo_rl/lima/estudio.py`: 5f08daaa8c1005962b70ef10d2fabe28a924f76cdb9790c4b54aa8c70b67bbf4 (sin cambios)
- `demo_rl/lima/borde_actuado.py`: 77ff0c9d21409db8964f8e9e21c49cfb91c7246a121c1d51ac07eb9b512ffb3e (sin cambios)
- `demo_rl/lima/programa_ovalo.py`: 5d5f03cca511b296762be38e930150a5bd2975c1ee88579a65985b02dd2d34c2 (sin cambios)
- `demo_rl/lima/ovalo/plan_ovalo.py`: 0829e80c105cc1bd46f71bef4d84ccd55f89de9356449006039b48378e31c940
- `demo_rl/lima/ovalo/armar_ovalo.py`: bfc3190099c5cc980a9e0a83ba5dff5abceaaba5f2b205856fc585172e436653
- `demo_rl/lima/demanda.py`: 08b06eebfbd50e04cdb17c303eb1d9f49ae720246e992d50e514d4a8c0028103
- `demo_rl/lima/ovalo/regenerar_demanda.py`: 9d1fea8024048806d3b0bfc6795fd54b68b79157965aa3d82993f3424e82cf0b
- `demo_rl/escenarios_plan3.py`: a50c1568c7afe8ca59c808cd08c1c5edf745ee4e3c66cc632d321126d5bf4c89
- `demo_rl/plan3/demanda_estocastica.py`: 8f2995f449e898968be2591e09aa4cf993bdaf2d46018cb777e92f6449696f8e
- `entrenar.sh`: a9a95791138ded3ba283199c382a5fdf16bd422cffb7c3251961e8c7ec8d311e (sin cambios)
- `referencias.sh`: 474472c8a4ee8c7fa88f7dbfb343e9b9f5448c60ffacb80e28be3da651ac8f79 (sin cambios)
- `evaluar_ovalo.py`: 4621671b9d0a38df20baac5c1da31d104d79f164aa46c11e9caf07489aebc836 (la de las 11:33)
- `comprobar_fases.py`: 6e10f4c157622ced5058e48fcf424bf641b5b6b917c2319ac88a6fa2cd8ea20e (sin cambios)
- `comprobar_referencias.py`: d428cf86c8d80d0e6b68274037a7ababb5251706b9647cc824338e586b638975
- `tablas_ovalo.py`: 6d47a8127e46eb3b3f2a96f4239aac29f98466435794b9b161166226bebcc76e
- `figura_secuencia.py`: d62bc5a056cbd9301b6948c9b5f7d1d0c39d65652f8dd36ba7f2eb6046da1143 (la de las 11:33)
- `ver_ovalo.py`: 9b4f8036a1cdcffa686478444067c057c5f73aa97611a2dc30f5e37081c2b221 (la de las 11:33)
- La red (`lima.net.xml`, la misma en las cuatro carpetas): d41d816ae02020e2f5046432cfb37faca6cc3ed83a5f7a91e7d3e866da30538c
- El `.sumocfg` (con la válvula; sin cambios): cbc78301ccee0f9d70fc2febd58f3e5c7beb51d2062ad80bf8fa84bbe6815355
- El plan actual (`lima.add.xml`): 140a3ccb8acc130380cc08e9d8c1ca0b9d60a64e1d3f0d9aedb74e397caf4577
- El programa del orden libre (`lima_libre.json`): ecf94f522a6755641da4dcd325cf3c52e77a0bc9d63b5e017ca677cf55e763aa
- Los detectores (`e2_lima_75.add.xml`): f0abce398211d3427259d033772a33c445b94a3c282a7f5dd579d5bd5f8af1c8
- La demanda publicada y la alta (`lima.rou.xml`): db3afbf59c038ce144bd75bf739932f60fec4cf8e3fd7733eddfab1e41dae929 y
  b057c6f27ee4b38e964ddda606f50dea939965a3e8648820b7ec9ac0d82fe946
- Las dos de la robustez: 49d863c8ec919094b691a4f5715eed9366a3a21367f5ac02730a46533bd363c4 (más carga en Reducto) y
  2320d7cfbb15dd99e0c23b1087861ec4739015a4f4f64944c5722f6241f2bedc (más carga en 28 de Julio y Balboa)

`huellas.sha256` (sha256 b482251efa955a14514dfdb5d01dab0afcff8394e93138934ba18b2728efcf88) lista los 73 archivos de
código y datos (antes 71: entran el código nuevo de la demanda, los dos módulos copiados y el archivo de donde salen
los detectores; salen dos referencias de la red anterior que ya no usa ningún programa). `entrenar.sh`,
`referencias.sh`, `evaluar_ovalo.py`, `tablas_ovalo.py` y `figura_secuencia.py` no corren si alguno cambió, y
`evaluar_ovalo.py` no evalúa una política que no traiga en su meta las huellas de este código.

**Qué queda de la corrida detenida.** Lo anotado a las 17:40: nada de esa corrida se informa y `nudo_ovalo_estudio/`
queda como está.

**Cuándo y en qué orden.** Después de la detención de las 17:39 y del diagnóstico, y antes de ajustar, entrenar o
evaluar en la red corregida. Se lanza a las 23:45, desde `nudo_ovalo_estudio2/`, con la PC sola (8 núcleos y 16
hilos); `logs/lanzamiento_*.txt` guarda la hora y las huellas comprobadas. El orden es el de las 11:03 (primero los
12 entrenamientos y, al lado, las referencias); las horas,
contadas desde el lanzamiento, son una estimación: lo medido en la corrida detenida por la razón de tiempo por episodio
medida en las dos redes (la corregida tarda de 0.69 a 0.83 veces lo de la anterior), sin correr el estudio.

| Desde el lanzamiento | Qué se lanza | Procesos |
|---|---|---|
| 0 h | Los 12 entrenamientos (`entrenar.sh libre` y `entrenar.sh completo`) y `referencias.sh ambas --procesos 4` | 16 |
| 1 h 10 a 1 h 45 | Referencias de la publicada listas: sus tandas (`evaluar_ovalo.py referencias --nivel publicada`) | 4 |
| 4 h 15 a 5 h 55 | Referencias de la alta listas: sus tandas (las del actuado de SUMO y del ciclo mínimo tardan 2.5 a 3.5 h más) | 4 |
| 4 h 24 a 5 h 11 | Terminan los 6 entrenamientos de la publicada: tandas de sus modelos y después la robustez | 6 |
| 7 h 34 a 9 h 04 | Terminan los 6 de la alta: tandas de sus modelos | 12 |
| 9 a 11 h | Verdes del modelo de orden fijo, figura de la secuencia, veredicto y tablas: fin | 8 |
