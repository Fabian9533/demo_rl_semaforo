# Caso Lima: reglas del estudio

Registradas el viernes 13.11.2026 a las 19:30, antes de ajustar las referencias, de entrenar y de evaluar con estos
datos. Lo que sigue no se cambia después de ver los resultados.

## Pregunta

¿El modelo completo reduce el retraso total por vehículo en el nudo de la Av. Reducto, la Av. 28 de Julio y la
Av. Vasco Núñez de Balboa (Miraflores), frente al plan que opera hoy y frente al fijo ajustado al segundo?

## Escenario

- **Red** (`armar_red.py`): un solo cruce con semáforo. Geometría de OpenStreetMap; carriles y movimientos de la
  descripción de campo de Fabian Alvarado (lima.pdf y mensajes del 13.11.2026). Entradas de 1 km: 300 m de trazado
  real y el resto en recta, para que la cola quepa dentro de la red. Reducto desde el norte, 4 carriles (el
  izquierdo solo gira a la izquierda); Reducto desde el sur, 5 (el derecho solo gira a la derecha, dos de frente y
  dos solo para girar a la izquierda); 28 de Julio desde el puente, 3; Balboa, 3. Salidas: hacia Larco 2, Reducto
  norte 2, Reducto sur 3, hacia el puente 3. Dentro del nudo no se simulan las trayectorias (red sin tramos internos).
- **Semáforo** (`programa.py`): el plan medido en el sitio el 13.11.2026 en la punta de la tarde, ciclo de 132 s:
  Reducto de frente 40 s, giros a la izquierda de Reducto 18 s, todo en rojo 34 s, 28 de Julio y Balboa juntas 40 s.
  Los últimos 3 s de cada verde medido son ámbar. Los 34 s con todo en rojo son iguales en todos los controles.
- **Demanda** (`demanda.py`): no hay conteo por movimiento. Total publicado de 4271 veh/h en la punta de la tarde
  (Plan de Movilidad Urbana de Miraflores 2017-2020), repartido en proporción a los carriles y al verde que el plan
  actual le da a cada grupo de movimientos; destinos dentro de cada grupo, estimados o supuestos. Llegadas
  aleatorias (Poisson) y mezcla de vehículos de Lima del segundo estudio.
- Huellas sha256 (16 primeros caracteres): `lima.net.xml` fc02a737fd3024d2, `lima.add.xml` 5a19a0c80baca53f,
  `lima.rou.xml` c4268af6add50553.

## Controles que se comparan

Todos usan los mismos estados, en el mismo orden, y solo cambian cuánto dura cada verde.

| Control | Qué es |
|---|---|
| Plan actual | el plan medido en el sitio |
| Fijo ajustado al segundo | los verdes que dan menos retraso total medio: descenso por coordenadas hasta 1 s, 10 semillas por candidato (2001-2010) y los diez mejores con 30 (2001-2030); verdes de 10 a 120 s |
| Actuado | control actuado de SUMO con verdes de 10 a 60 s |
| Actuado ajustado | el mejor de una rejilla de 12 combinaciones de parámetros, con las mismas semillas de ajuste |
| Ciclo mínimo | cada verde en su mínimo (10 s) |
| Modelo completo | el del segundo estudio, sin cambios |

## Modelo

El modelo completo del segundo estudio: observación de los vehículos cercanos (75 m), valor normalizado, sin
decisiones forzadas en el lote, tasa de aprendizaje con piso, decisión cada 2 s, 400 episodios. Un solo agente; no
hay vecinos ni mensajes. Verde de 10 a 60 s.

- Tres entrenamientos: bases 42, 2042 y 4042 (`entrenar.sh`).
- Validación cada 20 episodios en las semillas 21001-21008, por retraso total.
- Versión evaluada de cada entrenamiento: la de menor retraso total en la validación.
- Entrenamiento citado: el de validación mediana entre los tres. Los otros dos se informan al lado.

## Evaluación y veredicto

- Dos tandas de 100 semillas, las mismas para todos los controles: 22001-22100 y 23001-23100.
- Métrica: retraso total por vehículo (tiempo perdido dentro de la red más espera para entrar).
- Cambio en %, IC95 por bootstrap pareado (10 000 remuestreos) y prueba de Wilcoxon pareada.
- Veredicto con la regla de la tesis, frente al fijo ajustado al segundo y, para llegar a FUNCIONA, sin perder contra
  el actuado ajustado. La etiqueta que se cita es la que se repite en las dos tandas; si no se repite, EMPATA.
- Además se informa el cambio frente al plan actual, sin etiqueta.

## Decidido antes, con pruebas que no usan las semillas de evaluación

Con datos provisionales (piloto, carpeta `piloto/`; base 7 y semillas 424301-424302):

- Entradas de 1 km. Con 300 m la cola quedaba fuera de la red, el modelo no la veía y dejaba sin servir un estado.
- Modelo completo sin cambios, y un solo modelo. Decidir cada 5 s o descontar más despacio no dio mejor resultado.

Con el plan actual y los datos reales (semillas 424301-424303), antes de ajustar referencias o entrenar:

- Red sin tramos internos. Con ellos, los movimientos de Balboa y de 28 de Julio que se cruzan en su verde
  compartido quedaban detenidos más de 15 minutos y un vehículo dentro del nudo bloqueaba a Reducto todo un verde,
  cosa que no se observa en el sitio.
- Sin el giro de Balboa hacia Larco: entra al mismo carril que 28 de Julio durante el mismo verde, no hay conteo y
  en el simulador no encuentra hueco.
- Con estas reglas el plan actual da entre 56 y 61 s por vehículo, compatible con el nivel de servicio E publicado.

## Límites conocidos de antemano

- La demanda es un supuesto, no un aforo; el reparto elegido es el más favorable para el plan actual.
- Un solo cruce: un agente, sin coordinación con otros semáforos.
- Los dos semáforos del puente sobre la Vía Expresa no están en la red. En el sitio, la cola hacia el puente
  bloquea a veces el paso de frente de Reducto; la simulación no lo reproduce.
- Los dos carriles de giro a la izquierda desde el sur son en el sitio un ensanche corto; aquí son carriles completos.
- Reducto norte a sur y 28 de Julio tienen 38 s de verde en el sitio; aquí van con los 40 s de su pareja.
- No se simulan peatones. El tiempo con todo en rojo se conserva tal cual.

## Segundo nivel de demanda (añadido el 13.11.2026 a las 19:40, antes de ajustar, entrenar o evaluar con él)

El plan de movilidad califica el cruce con su nivel de saturación más alto (más de un 20 % por encima de la
capacidad). Con los 4271 veh/h la simulación queda cerca de la capacidad, pero no por encima. Por eso se añade un
segundo nivel, como la demanda nominal y la alta de los demás casos de la tesis:

- **Demanda alta**: toda la demanda multiplicada por 1.2 (5125 veh/h), en la carpeta `alta/`. La red, el semáforo,
  los controles, el modelo, las semillas y la regla de veredicto son los mismos; el fijo y el actuado se vuelven a
  ajustar y el modelo se vuelve a entrenar con esa demanda (`entrenar_nivel.sh alta`).
- Con el plan actual y las semillas 424301-424302 da entre 76 y 83 s por vehículo, y los dos giros a la izquierda
  de Reducto quedan por encima de su capacidad (entre 118 y 253 s por vehículo).
- Cada nivel recibe su propio veredicto. No se promedian.

## Prueba de robustez del reparto (añadida el 13.11.2026 a las 22:10, antes de correrla)

El reparto de la demanda entre las calles es un supuesto. Esta prueba pregunta qué pasa si el reparto real es otro.
No interviene en el veredicto.

- Demanda: el mismo total publicado (4271 veh/h), con el reparto entre entradas cambiado. Dos variantes:
  **más carga en Reducto** (las dos entradas de Reducto por 1.2 y las de 28 de Julio y Balboa por 0.8, y todo
  reescalado al mismo total) y **más carga en 28 de Julio y Balboa** (lo contrario). Carpetas `robustez/reducto/` y
  `robustez/transversal/`.
- Controles, sin volver a ajustar ni a entrenar: el plan actual, el fijo ajustado al segundo y el actuado ajustado
  de la demanda publicada, y el entrenamiento citado del modelo (base 42).
- 100 semillas nuevas, las mismas para todos: 24001-24100. Misma métrica y misma estadística.
- Se informa el retraso de cada control y el cambio del modelo frente a cada uno, tal como salga.

## Segundo caso: corredor de la Av. Benavides (añadido el 13.11.2026 a las 22:40, antes de ajustar, entrenar o evaluar)

El nudo es un solo cruce y no pone a prueba los mensajes entre semáforos vecinos. Por eso se añade un corredor real
con varios cruces (`corredor/`, escenario `benavides`).

- **Red**: la Av. Alfredo Benavides entre la Av. José Larco y la Av. República de Panamá (Miraflores): seis cruces
  con semáforo en 1.2 km (Larco, Alcanfores, La Paz, Paseo de la República, Casimiro Ulloa y República de Panamá).
  Distancias, carriles y sentidos de OpenStreetMap; la avenida se dibuja recta. Entradas de 600 m.
- **Semáforos**: no se midieron. Cada cruce tiene dos estados (avenida y transversal). El plan típico es un
  supuesto: ciclo de 140 s, transversal con 43 s de verde y 97 s de rojo, sin coordinación entre cruces.
- **Demanda**: supuesta, ajustada a los volúmenes publicados de tres de los cruces (Larco 3390, Paseo de la
  República 3778 y República de Panamá 4358 veh/h; quedan a menos de un 2 %). Entran 8706 veh/h. Llegadas
  aleatorias y mezcla de vehículos de Lima.
- **Controles**: plan típico; fijo ajustado al segundo (ciclo común, verde de la transversal de cada cruce y
  desfase de cada cruce, por descenso de coordenadas; 10 semillas por candidato, 2001-2010, y los diez mejores con
  30, 2001-2030); actuado de SUMO y actuado ajustado (rejilla de parámetros); ciclo mínimo.
- **Modelos**, tres entrenamientos cada uno (bases 42, 2042 y 4042), validación en 21001-21004 por retraso total:
  el modelo completo (con mensajes, 400 episodios), IPPO con mensajes corregido (200 episodios) e IPPO sin mensajes
  corregido (lo mismo, sin mensajes). Se cita el modelo completo; los otros dos responden qué aportan los mensajes.
- **Evaluación y veredicto**: como en el nudo (tandas 22001-22100 y 23001-23100, retraso total, misma estadística
  y misma regla). La comparación con y sin mensajes se informa con su cambio y su IC95.
- **Límite conocido**: geometría y volumen total son reales; los semáforos y el reparto de la demanda, supuestos.
- Huellas sha256 (16 primeros caracteres): `benavides.net.xml` 943a52d994f1a668, `benavides.rou.xml`
  8069232367324a28, `benavides.add.xml` (plan típico) adbcad5f2e2e7959.

## Corredor: segundo nivel de demanda y prueba del canal cortado (añadidos el 14.11.2026 a las 03:00)

Se registran cuando del corredor solo se conocen el ajuste de las referencias y la validación de los
entrenamientos; ninguna evaluación con las semillas de las tandas ha terminado.

- **Demanda alta**: toda la demanda del corredor multiplicada por 1.2 (10 447 veh/h), el mismo factor del nudo,
  en la carpeta `corredor/alta/` (`corredor.py nivel --factor 1.2 --carpeta alta`). La red, los estados de cada
  cruce, los controles, los tres modelos, las semillas y la regla de veredicto son los mismos; el fijo y el actuado
  se vuelven a ajustar y los modelos se vuelven a entrenar con esa demanda (`entrenar_nivel.sh alta`). El plan
  típico no cambia. Cada nivel recibe su propio veredicto. No se promedian.
- Con las semillas 424301-424302, antes de ajustar o entrenar: el plan típico da entre 140 y 171 s por vehículo y
  el fijo ajustado de la demanda publicada, sin volver a ajustar, entre 52 y 57. El nivel carga la red y se puede
  servir. Huella de `alta/benavides.rou.xml`: a3cc0929e75c94af (la red y el plan típico son los mismos archivos).
- **Prueba del canal cortado** (no interviene en el veredicto): el entrenamiento citado del modelo completo de cada
  nivel se evalúa otra vez en las dos tandas sin que le llegue ningún mensaje de sus vecinos
  (`estudio_corredor.py evaluar --perdida 1`). Se informa el cambio frente al mismo modelo con mensajes, tal como
  salga. Dice cuánto se apoya en los mensajes un modelo entrenado con ellos; no reemplaza la comparación entre
  entrenar con mensajes y entrenar sin ellos.

## Corredor: prueba de robustez del reparto (añadida el 14.11.2026 a las 03:25, antes de correrla)

Se registra cuando todavía no ha terminado ninguna evaluación de los modelos del corredor. Como en el nudo, pregunta
qué pasa si el reparto real de la demanda es otro. No interviene en el veredicto.

- Demanda: el mismo total de la demanda publicada (8706 veh/h), con el reparto cambiado. Dos variantes: **más carga
  en la avenida** (lo que entra por los dos extremos de la avenida por 1.2 y lo de las transversales por 0.8, y todo
  reescalado al mismo total) y **más carga en las transversales** (lo contrario). Carpetas `corredor/robustez/avenida/`
  y `corredor/robustez/transversal/` (`corredor.py nivel --reparto ...`).
- Controles, sin volver a ajustar ni a entrenar: el plan típico, el fijo ajustado al segundo y el actuado ajustado de
  la demanda publicada, y el entrenamiento citado del modelo completo.
- 100 semillas, las mismas para todos: 24001-24100. Misma métrica y misma estadística.
- Se informa el retraso de cada control y el cambio del modelo frente a cada uno, tal como salga.

## Enmienda del actuado ajustado (14.11.2026, 04:05)

**Qué se vio.** En los tres ajustes hechos hasta ahora (nudo con la demanda publicada, nudo con la alta y corredor
con la publicada), el ganador de la rejilla de 12 combinaciones quedó en su borde: hueco de 2 s, el menor de los
probados, y detector a 2 s, el mayor. El retraso baja de forma sostenida al acortar el hueco (nudo: 63.4, 60.1 y
55.7 s por vehículo con 4, 3 y 2 s). En el segundo estudio de la tesis, que probó huecos desde 1 s, con llegadas
aleatorias ganó casi siempre un hueco de 1 o 1.5 s. La rejilla de este caso era más corta y deja una referencia
más débil de lo que la tesis llama actuado ajustado.

**Qué se cambia.** El actuado ajustado de los dos casos de Lima se vuelve a buscar con los pasos del segundo estudio
(`plan3/actuado.py`), sin sus dos variantes coordinadas: en cadena, hueco máximo (1, 1.5, 2, 3 y 4 s), distancia del
detector (1, 2, 3 y 4 s), umbral de atasco (sin umbral, 10 y 30 s) y verde máximo (60 s en todos los estados, o el
doble del verde del fijo ajustado); después, la variante de SUMO que decide por el retraso de los vehículos (alcance
del detector de 50, 100 y 200 m, y retraso mínimo de 1 y 3 s). Cada candidato con las semillas 2001-2010; los tres
mejores, con 2001-2030; gana el de menor retraso total medio. Las semillas son las mismas de antes.

**Qué se repite.** Con el actuado ajustado nuevo se vuelven a evaluar las dos tandas, la validación y las pruebas de
robustez de cada caso y nivel. El veredicto se calcula con él. El cambio solo puede hacer más exigente la
referencia. Los resultados con la rejilla anterior se conservan con el sufijo `12` (`eval_t*_actuadoaj12.csv`,
`*_actuadoaj12.add.xml`, `actuado_ajustado_rejilla12.json`) y se informan al lado.

**Cuándo.** Antes de que termine la evaluación del modelo completo del corredor. Del nudo ya se conocían los
resultados con la rejilla anterior: frente a ese actuado ajustado el modelo empataba (+0.2 y +0.3 % con la demanda
publicada; -0.5 y -1.1 % con la alta).

## Enmienda del fijo ajustado del corredor (14.11.2026, 05:50)

**Qué se vio.** El modelo completo trabaja con ciclos medios de 30 a 39 s en los seis cruces
(`corredor/salidas/verdes_modelo.json`) y el fijo ajustado quedó con un ciclo de 55 s. La búsqueda del fijo partió
de ciclos de 50, 60, 70, 90 y 140 s y bajó paso a paso hasta 55 s; con 54 s y los mismos verdes de las transversales
salió peor y ahí se detuvo. Nunca probó un ciclo de menos de 50 s con los verdes repartidos de nuevo. Con el reparto
del método de Webster, el ciclo que conviene a los cruces más cargados sale entre 30 y 40 s. Si un fijo de ciclo
corto es mejor, la referencia es débil y la ventaja del modelo está inflada. Es el mismo error que la tesis ya
corrigió dos veces en los casos sintéticos (06.09 y 27.09.2026).

**Qué se cambia.** A la misma búsqueda se le añaden partidas de ciclo corto: ciclos de 32, 36, 40, 44 y 48 s, con el
verde de cada cruce repartido según los vehículos por carril del acceso más cargado de la avenida y de la
transversal (reparto de Webster, sin bajar de 10 s), cada uno con desfases cero y con onda verde a 12 m/s hacia cada
lado: 15 partidas. Las dos mejores de ciclos distintos se afinan con el mismo descenso por coordenadas (pasos de 8,
4, 2 y 1 s). Los candidatos nuevos se juntan con los de la búsqueda anterior: los diez mejores con las semillas
2001-2010 se miden con 2001-2030 y gana el de menor retraso total medio (`estudio_corredor.py ajustar-fijo
--ampliar`). Mismas semillas y misma métrica. Se aplica igual a la demanda alta.

**Qué se repite si cambia el ganador.** El fijo en las dos tandas, la validación y la prueba de robustez; el
actuado ajustado, porque uno de sus dos esquemas de verde máximo depende del fijo, y sus evaluaciones si cambia. El
veredicto se calcula con el fijo nuevo. Los resultados con el fijo anterior se conservan con el sufijo `55`
(`eval_t*_fijo55.csv`, `benavides_fijo55.add.xml`, `fijo_ajustado_primera.json`) y se informan al lado.

**Cuándo.** Después de conocer la evaluación del modelo completo en las dos tandas: frente al fijo de 55 s, −10.9
y −11.0 %. El cambio solo puede hacer más exigente la referencia.

## Enmienda del actuado ajustado del corredor: variantes coordinadas (14.11.2026, 05:40)

**Qué se vio.** La enmienda de las 04:05 dejó fuera las dos variantes coordinadas del actuado del segundo estudio.
En el nudo no aplican: es un solo cruce. En el corredor sí: son seis cruces sobre una avenida. En el segundo estudio
una variante coordinada fue la ganadora del actuado ajustado en 20 de sus 30 celdas (`plan3/barridos/*/
actuado_aj.json`), entre ellas las dos redes y el corredor con demanda alta con llegadas aleatorias. Sin esas
variantes, el actuado ajustado del corredor es más débil que el que la tesis usó en el segundo estudio.

**Qué se cambia.** La búsqueda del actuado ajustado del corredor añade las dos variantes coordinadas de
`plan3/actuado.py`, construidas sobre el mejor actuado de la cadena y sobre el fijo ajustado (su ciclo, sus verdes y
sus desfases): (a) el verde de la avenida no termina antes de su fin en el plan fijo; (b) fin fijo: además termina
exactamente ahí, y el verde de la transversal no pasa de su fin en el plan fijo. Como allí, el ciclo se cuenta desde
el inicio del verde de la transversal y el verde máximo de la avenida no baja de lo que necesita. Entran al mismo
desempate: las tres mejores variantes con las semillas 2001-2010 se miden con 2001-2030 y gana la de menor retraso
total medio. Se corre después de la enmienda del fijo, porque dependen de él. Se aplica igual a la demanda alta.

**Qué se repite.** Con el actuado ajustado que resulte: las dos tandas, la validación, la prueba de robustez y el
veredicto. Si gana una variante coordinada, los resultados del actuado sin coordinar se conservan con el sufijo
`sc` (`eval_t*_actuadoajsc.csv`, `benavides_actuadoajsc.add.xml`) y se informan al lado.

**Cuándo.** Después de conocer la evaluación del modelo completo frente al actuado ajustado sin coordinar: −8.1 y
−7.9 %. El cambio solo puede hacer más exigente la referencia.

## Qué salió de las tres enmiendas (anotado el 14.11.2026 a las 09:10)

- **Actuado ajustado del nudo (enmienda de las 04:05).** Con las dos demandas gana la variante que decide por el
  retraso (alcance de 200 m, retraso mínimo de 3 s): 53.50 y 63.26 s por vehículo con 30 semillas. El modelo deja de
  empatar y pierde: +3.4 y +3.6 % con la demanda publicada, +4.4 y +3.3 % con la alta. El veredicto de la demanda
  alta pasa de FUNCIONA (provisional) a MEJORA (provisional); el de la publicada sigue en MEJORA.
- **Fijo ajustado del corredor (05:50).** Gana un plan de ciclo corto: ciclo de 46 s, transversales
  [15, 11, 18, 18, 13, 18], desfases [0, 22, 26, 3, 43, 44], 34.92 s por vehículo con 30 semillas, frente a 35.74 del
  plan de 55 s. En las tandas, 35.02 y 35.02 frente a 35.85 y 35.85. La mejora del modelo frente al fijo baja de
  −10.9 y −11.0 % a −8.8 y −8.9 %. Lo anterior se conserva como `fijo55`.
- **Actuado ajustado del corredor (04:05 y 05:40).** Gana el actuado sin coordinar con hueco de 1 s (34.82 con 30
  semillas). Las dos variantes coordinadas dan 37.10 y 36.37 con 10 semillas. Con el fijo nuevo el ganador es el
  mismo programa de la búsqueda de las 04:05, así que sus evaluaciones no se repiten (34.73 y 34.64 en las tandas).
  La rejilla anterior se conserva como `actuadoaj12`.
- **Veredicto del corredor con las referencias definitivas:** FUNCIONA en las dos tandas (−8.8 y −8.9 % frente al
  fijo; −8.1 y −7.9 % frente al actuado ajustado).
- **Prueba de robustez del corredor.** Se detuvo a las 05:30, cuando solo había medido el plan típico y el fijo de
  55 s con un reparto, y se volvió a correr con las referencias definitivas. Nada de lo medido antes se usa, salvo
  el plan típico.
- **Demanda alta del corredor.** Sus referencias se volvieron a lanzar a las 06:25 con el procedimiento enmendado
  (fijo con partidas de ciclo corto y actuado con variantes coordinadas), antes de que terminara ningún
  entrenamiento ni evaluación de ese nivel.

## Referencias de la demanda alta del corredor (anotado el 14.11.2026 a las 15:55)

- **Fijo ajustado.** Ciclo de 62 s, transversales [25, 21, 25, 25, 18, 25], desfases [0, 48, 44, 15, 13, 30]: 52.45 s
  por vehículo con 30 semillas. Las partidas de ciclo corto (32-48 s) quedan muy por detrás (78 a 104 s por vehículo
  con 10 semillas).
- **Actuado ajustado.** Gana la variante por retraso (alcance de 100 m, retraso mínimo de 1 s, verdes máximos de
  60 s): 47.89 con 30 semillas. El mejor actuado de la cadena da 48.87 (48.46 con los máximos del doble del fijo); las
  coordinadas, 52.50 y 55.94 con 10 semillas; el actuado por defecto, 66.11.
- **Validación (21001-21004).** Plan típico 154.33, fijo ajustado 53.73, actuado 58.39, actuado ajustado 45.30, ciclo
  mínimo 295.20.

## Comprobación del borde del actuado ajustado (anotado el 14.11.2026 a las 15:55, antes de correrla)

**Qué se vio.** En los cuatro actuados ajustados de Lima el ganador, o un parámetro de la cadena, queda en el borde de
los valores probados. El nudo, con las dos demandas, gana con la variante por retraso de 200 m y 3 s: los dos valores
son los más altos de la rejilla (50, 100 y 200 m; 1 y 3 s). En el corredor con la demanda publicada gana un actuado
con hueco de 1 s, el más bajo de la cadena (1 a 4 s). En el corredor con la demanda alta gana la variante por retraso
con 1 s, el retraso mínimo más bajo, y la cadena también termina en el hueco de 1 s. Es el mismo defecto que llevó a la
enmienda de las 04:05.

**Qué se hace.** Un paso más allá de cada borde, con todo lo demás igual al mejor de su tipo:
- nudo, las dos demandas: variante por retraso con 400 m y 3 s, 200 m y 5 s, y 400 m y 5 s;
- corredor, las dos demandas: variante por retraso con 100 m y 0.5 s, y la cadena con hueco de 0.5 s.

Cada variante se mide con las semillas de ajuste (2001-2010). Las que bajen del ganador con esas semillas se miden con
2001-2030 y gana la de menor retraso total medio con 30 semillas, como en la búsqueda. Si el nuevo ganador vuelve a
quedar en el borde, no se sigue: se dice como límite. Si cambia el ganador, lo anterior se conserva con el sufijo `b`
(`eval_t*_actuadoajb.csv`, `*_actuadoajb.add.xml`) y se repiten con el nuevo las dos tandas, la validación, la prueba
de robustez y el veredicto. Programa: `lima/borde_actuado.py`.

**Cuándo.** Antes de conocer ninguna evaluación de la demanda alta del corredor. Con las otras tres celdas ya se
conocen sus veredictos. La comprobación solo puede hacer más exigente la referencia.

**Qué salió (16:07; `lima/logs/borde_actuado.log` y `salidas/borde_actuado.json` de cada carpeta).** Con 10 semillas,
frente al ganador:
- corredor, demanda alta (46.77): 100 m y 0.5 s, 49.23; hueco de 0.5 s, 57.11. No cambia.
- corredor, demanda publicada (34.87): 100 m y 0.5 s, 34.92; hueco de 0.5 s, 36.33. No cambia.
- nudo, demanda publicada (53.88): 400 m y 3 s, 55.67; 200 m y 5 s, 54.14; 400 m y 5 s, 54.46. No cambia.
- nudo, demanda alta (63.41): 400 m y 3 s, 65.41; 200 m y 5 s, 63.24 (63.18 con 30 semillas, frente a 63.26 del
  ganador); 400 m y 5 s, 63.96. **Cambia:** gana 200 m y 5 s, por 0.08 s por vehículo. Queda otra vez en el borde (5 s),
  y la regla dice no seguir: se dice como límite. Lo anterior se guardó con el sufijo `b`
  (`alta/lima_actuadoajb.add.xml`, `alta/salidas/eval_t*_actuadoajb.csv`, `val_referencias_b.json`,
  `veredicto_completo_s42_b.md`, `actuado_ajustado_b.json`); el nuevo se instaló con
  `python borde_actuado.py nudo --carpeta alta --instalar` y se evalúa en las dos tandas (log
  `alta/logs/borde_reevaluar.log`).
- Reevaluación (16:40): el actuado nuevo da 63.29 y 62.95 en las tandas (el anterior, 63.23 y 62.94). El modelo queda
  +4.34 y +3.29 % por detrás (antes +4.43 y +3.31). El veredicto no cambia: MEJORA, provisional.

## Resultado de la demanda alta del corredor (anotado el 14.11.2026 a las 19:00)

Entrenamientos citados (mediana de la validación): completo 2042 (los tres estables), corregido 4042 y sin mensajes
2042 (los dos sin estabilizar). Tandas 1 y 2: plan típico 152.05 y 153.03, fijo ajustado 53.01 y 52.83, actuado
ajustado 47.40 y 47.36, modelo 42.48 y 42.32. Frente al fijo, −19.86 y −19.90 %; frente al actuado ajustado, −10.39 y
−10.63 %: **FUNCIONA** en las dos tandas, firme. Mensajes: con frente a sin, −0.94 y −0.98 % (provisional); canal
cortado, 43.58 y 43.44 (+2.6 %). Veredicto en `corredor/alta/salidas/veredicto_vecinos_completo_s2042.md`.

## Si aparece un error

Solo se corrigen errores de código. Se repite todo lo afectado y se anota aquí qué se cambió y cuándo.
