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

## Prueba adicional del nudo: el modelo elige el estado que sigue (17.11.2026, 17:25)

Se registra antes de entrenar y antes de cualquier evaluación con las semillas de las tandas. Hasta aquí solo se usaron
la base 7 y semillas de humo (424301-424306).

**Qué se prueba y por qué.** En el estudio, el modelo decide cada 2 s si mantiene el verde o pasa al estado siguiente,
siempre en el orden del plan medido: Reducto de frente, giros a la izquierda de Reducto, 34 s con todo en rojo y 28 de
Julio con Balboa. Fabian Alvarado pregunta cuánto más baja el retraso total si el modelo también puede elegir qué estado
viene después. Es una prueba adicional: no reemplaza el resultado principal del nudo ni su veredicto, y se informa tal
como salga, mejore o no.

**Diseño** (opción `--orden-libre` de una copia de `rl_ippo.py`; con la opción apagada, la copia da los mismos números
que el código del repositorio en el commit 53bdb48).
- Acción: mantener el verde o pasar a cualquiera de los otros dos estados. Verde mínimo de 10 s y máximo de 60 s, como
  en el estudio.
- Transiciones: 3 s de ámbar para los movimientos que pierden el verde. Los 34 s con todo en rojo van siempre antes del
  verde de 28 de Julio con Balboa, venga de donde venga, y antes de ese rojo todos los verdes pasan por ámbar, como en
  el plan. En el orden del plan, las luces son las de hoy. Así el modelo no puede ganar saltándose el rojo total.
- Tope de rojo: ningún estado con vehículos esperando pasa más de 163 s en rojo, lo más que permite el orden del plan
  con verdes de 60 s (2 × 60 + 3 × 3 + 34). Un estado espera cuando los detectores de 75 m de sus carriles ven al menos
  un vehículo detenido, y el tiempo cuenta solo mientras alguien espera: un estado sin nadie esperando se puede saltar.
  El cambio se fuerza a tiempo, contando el ámbar y el rojo total de la transición. Con el orden del plan el tope nunca
  obliga a nada: el modelo puede hacer todo lo que hacía antes.
- Observación: la del estudio, más dos datos por estado: los vehículos detenidos en sus carriles y el tiempo que lleva
  en rojo con alguien esperando, como fracción del tope.
- Lo demás es igual: recompensa, hiperparámetros, red neuronal (salvo el tamaño de la entrada, 56 en vez de 50, y de la
  salida, una por estado), 400 episodios, decisión cada 2 s, validación, selección de la versión, la red
  (`lima.net.xml`, sin cambios) y las dos demandas, la publicada y la alta.
- Qué mide y qué no. El modelo libre ve seis entradas más (detenidos y reloj del tope de cada estado) y su decisión a
  los 60 s tiene dos opciones y entra al lote (en el estudio era forzada). El cambio frente al modelo del estudio mide
  el efecto conjunto de elegir el orden y de esas diferencias; para separarlos se agrega un grupo de control (más
  abajo). Un resultado peor tampoco descarta el orden libre: el modelo libre empieza más lejos con los mismos 400
  episodios. En un piloto de 20 episodios con la base 7 (validación en las semillas de humo 424305-424306), con la
  demanda publicada el modelo libre daba 77 s/veh de retraso total y el del estudio, entrenado igual, 55; con la
  alta, 176 y 71. Parte de una ganancia puede venir de servir más de una vez a Reducto (de frente y giros) por cada
  rojo total de 34 s; con el rojo total en otro lugar del ciclo, la ganancia sería otra.

**Semillas y protocolo.** Los del estudio. Tres entrenamientos por nivel de demanda (bases 42, 2042 y 4042), validación
cada 20 episodios en 21001-21008 por retraso total y versión evaluada la de menor retraso medio en esa validación.
Entrenamiento citado: el de validación mediana entre los tres; los otros dos se evalúan igual y se informan al lado.
Evaluación en las dos tandas de 100 semillas (22001-22100 y 23001-23100), las mismas de todos los controles.

**Comparaciones y veredicto.** Retraso total por vehículo; cambio en %, IC95 por bootstrap pareado (10 000
remuestreos) y prueba de Wilcoxon pareada, tanda por tanda, frente a los resultados por semilla ya medidos en el
estudio, que no se vuelven a correr:
- frente al fijo ajustado al segundo, sin perder contra el actuado ajustado: veredicto con la regla de la tesis, como
  en el estudio;
- frente al modelo del estudio (el entrenamiento citado de cada nivel, base 42 en los dos): la misma regla, con ese
  modelo en el lugar del fijo. Responde la pregunta con la salvedad del diseño: mide el efecto conjunto;
- frente al plan actual: el cambio, sin etiqueta.

La etiqueta que se cita es la que se repite en las dos tandas; si no se repite, EMPATA. Si el entrenamiento citado no se
estabiliza (regla de la tesis), el veredicto es provisional. Cada nivel de demanda recibe su propio veredicto. Junto al
entrenamiento citado se informa la media de los tres entrenamientos de cada modelo, para leer las diferencias junto a
la variación entre entrenamientos; eso no cambia el veredicto.

**Grupo de control (registrado aquí, antes de lanzar ningún entrenamiento de esta prueba).** Para separar el efecto de
elegir el orden del de las seis entradas nuevas, se entrena también el modelo del estudio, con el orden del plan y la
misma observación ampliada del modelo libre (56 entradas), con la etiqueta `obsamp`. Todo lo demás es igual: bases,
demandas, 400 episodios, validación, selección de la versión, entrenamiento citado y evaluación en las dos tandas. Se
programa en una copia aparte, sin tocar la de esta prueba, y se lanza en cuanto pase sus pruebas: con la opción nueva
apagada tiene que dar lo mismo que el código del estudio, y con el orden libre, lo mismo que el código de esta prueba.
Su lanzamiento se anota debajo, con la hora y las huellas, antes de cualquier evaluación con las tandas. Agrega dos
comparaciones, con la misma regla de veredicto: el modelo libre frente a este grupo (el efecto de elegir el orden,
incluida la decisión a los 60 s) y este grupo frente al modelo del estudio (el efecto de las seis entradas). Si no se
lanza antes del 18.11.2026 a las 12:00, se informa solo la comparación conjunta, con su salvedad.

**Código y datos.** La prueba no corre en el repositorio. El código, los entrenamientos y los resultados quedan juntos
en la carpeta `orden_libre_2026-11-17/`, junto al repositorio (como `datos_diagnostico_corredor_2026-10-25/`).
Huellas sha256 de los programas:
- `demo_rl/rl_ippo.py`: 538cb134d71535efd15aface87301318ecbf90b61dd7eaa20b2795ccbf0f888e
- `entrenar_libre.sh`: c714f8b74c70cdba16607ea27514718bce1aed6d90e01cf30108afc919c777da
- `evaluar_libre.py`: 12804ece9c5ca1c92d5eba7103d0541bfde78f66b4ebb1dda1ff400ec2f53026
- `comprobar_fases.py`: 465c94613bf83ef80d5ffb12d230a787325176069dcc9eb8799525434ae5d937

El resto del código y los datos (la red, las dos demandas, el plan, los detectores, el fijo y el actuado ajustados) son
los del repositorio en el commit 53bdb48, sin cambios; `huellas.sha256` lista los 27 archivos con su huella.
`entrenar_libre.sh` y `evaluar_libre.py` no corren si alguno cambió, y cada política guarda en su meta las huellas del
código con que se entrenó.

**Decidido antes, con pruebas que no usan las semillas de evaluación.**
- Un prototipo del 17.11 por la mañana tenía el rojo total pegado a los giros y no tenía tope: dejó a los giros sin
  verde toda la hora y se ahorraba los 34 s. Por eso el rojo total va pegado a 28 de Julio y Balboa y se agregó el tope.
- Las políticas del estudio no sirven de punto de partida (la red cambia de tamaño): se entrena desde cero, como en el
  estudio.
- Con la opción apagada, la copia da lo mismo que el código del repositorio, celda por celda y bit a bit, en un
  entrenamiento de 2 episodios y en su evaluación, con las dos demandas.
- Con la opción prendida, 5 episodios por demanda (más su validación) y una comprobación segundo a segundo de las luces:
  todos los cambios llevan sus 3 s de ámbar, toda entrada a 28 de Julio y Balboa lleva antes sus 34 s con todo en rojo,
  los verdes duran de 10 a 60 s y ningún estado pasa del tope. Alrededor de la mitad de los cambios no siguen el orden
  del plan.

**Cuándo.** Antes de entrenar y antes de cualquier evaluación con las tandas.

### Lanzamiento del grupo de control (17.11.2026, 19:50)

Se anota antes de entrenarlo y antes de cualquier evaluación con las semillas de las tandas. Para prepararlo solo se
usaron la base 7 y semillas de humo del bloque 424301-424360.

**Qué se agregó.** La opción `--obs-ampliada`, en una copia aparte de `rl_ippo.py` hecha desde la de esta prueba
(carpeta `orden_libre_2026-11-17/control/`). Es el modelo del estudio con su misma forma de decidir: mantener el verde
o pasar al estado siguiente del plan, verde de 10 a 60 s y cambio forzado a los 60 s; el programa del semáforo es el
del plan. Cambia la observación: suma las seis entradas del modelo libre (56 en vez de 50), calculadas con el mismo
código. Por estado, los detenidos en sus carriles sobre sus plazas en 75 m, y el reloj del tope (el rojo con alguien
detenido) sobre 163 s. Ese código se separó de la instalación del programa libre sin cambiar ningún número del modelo
libre. Con la entrada más grande cambia la primera capa de la red y, con ella, todos los pesos iniciales. El tope no
entra a la máscara de obsamp: con el orden del plan nunca obligaría a nada. Etiqueta `obsamp`.

**Qué mide cada comparación.**
- (a) obsamp frente al fijo ajustado, sin perder contra el actuado ajustado, con la regla del estudio. No estaba en la
  enmienda: se agrega aquí, antes de evaluar, como comprobación del modelo con las seis entradas. El veredicto del nudo
  sigue siendo el del estudio.
- (b) libre frente a obsamp, con obsamp en el lugar del fijo: el efecto de elegir el orden. Trae consigo el tope de
  rojo, la decisión a los 60 s y lo que cambia al tener tres acciones en vez de dos: la capa de salida, los pesos
  iniciales del crítico, el muestreo de la exploración y la escala de la entropía.
- (c) obsamp frente al modelo del estudio (base 42 en los dos niveles), con el del estudio en el lugar del fijo: el
  efecto de las seis entradas, con pesos iniciales distintos (la primera capa pasa de 50 a 56 entradas).
- (d) cada entrenamiento de los tres modelos (libre, obsamp y el del estudio), su media y su rango, tanda por tanda.
- (e) la comparación conjunta (libre frente al modelo del estudio). `evaluar_control.py` la repite con los mismos
  datos y la misma regla; tiene que dar la misma etiqueta que `evaluar_libre.py`.

Para FUNCIONA, el modelo que se juzga tampoco debe perder contra el actuado ajustado (el libre en (b) y (e), obsamp en
(c)), como en la enmienda.

**Cómo se leen.** La etiqueta citada es la que se repite en las dos tandas; si no, EMPATA. Es provisional si no se
estabiliza el entrenamiento citado de alguno de los dos modelos comparados (en (a), el de obsamp), como "con frente a
sin mensajes" en el corredor (14.11.2026, 19:00). La misma marca se aplica al informar la comparación conjunta del
modelo libre con el del estudio; la enmienda solo miraba el libre. Con la demanda alta el entrenamiento citado del
estudio no se estabilizó, así que (c) y la conjunta salen provisionales en la alta.

(b), (c) y la conjunta comparan un solo entrenamiento de cada modelo; su IC95 mide la variación entre semillas, no
entre entrenamientos. En el estudio, dos entrenamientos del mismo modelo difieren hasta 1.0 % con la demanda alta, y la
regla da MEJORA entre ellos en las dos tandas (2042 frente a 4042: −0.96 y −0.74 %). Por eso una etiqueta de (b), (c)
o la conjunta se atribuye al diseño solo si, en las dos tandas, la diferencia entre las medias de los tres
entrenamientos de cada modelo va en el sentido de la etiqueta y es mayor que el rango entre entrenamientos (el mayor
de los dos modelos; en el estudio, 0.14 y 0.27 s/veh con la publicada y 0.66 y 0.49 con la alta). La etiqueta no
cambia. `evaluar_control.py` escribe esa lectura junto a cada etiqueta.

**Orden de la evaluación.** Primero `evaluar_libre.py`, sin `--solo-citada` ((d) y la lectura usan los tres
entrenamientos del libre); después `evaluar_control.py`, que evalúa los tres entrenamientos obsamp en las dos tandas,
el citado primero.

**Pruebas** (base 7 y semillas de humo; están en la copia de trabajo, en `pruebas/`).
- Con la opción apagada, la copia da lo mismo que el código del repositorio en el commit 53bdb48: 2 episodios con las
  opciones del estudio y la evaluación de la política con `estudio.py`, celda por celda y bit a bit, con las dos
  demandas. El estudio se entrenó el 13.11 con ese soporte de Lima todavía sin commit (sus metas dicen 2eb76ff) y no
  hay huella de aquel código; los metas de sus seis políticas coinciden con el de esos 2 episodios en entradas,
  hiperparámetros, constantes y opciones. Es el mismo límite de la prueba del orden libre.
- Con `--orden-libre`, la copia da lo mismo que el código con que corre esta prueba, también las trazas de luces,
  byte a byte. En el meta solo cambia la huella de `rl_ippo.py`.
- Con `--obs-ampliada`, 5 episodios por demanda y la comprobación segundo a segundo de las luces: 0 fallas y 0 cambios
  fuera del orden del plan; todos los cambios con 3 s de ámbar, los 34 s de rojo total solo antes de 28 de Julio y
  Balboa, verdes de 10 a 60 s. La observación tiene 56 entradas y las seis nuevas quedan entre 0 y 1. Con y sin la
  opción, la misma política del estudio juega exactamente el mismo episodio. Sin SUMO, la máscara de obsamp es la del
  estudio en 200 000 estados al azar.
- La máscara del modelo libre, jugada en el orden del plan, nunca quita ninguna de las dos acciones del plan (mantener
  o pasar al siguiente): 0 de 817 975 decisiones sintéticas. Solo quita saltos fuera del orden.
- Piloto de 20 episodios con la base 7 y validación cada 10 en 424305-424306. Retraso total en los episodios 10 y 20:
  con la publicada, obsamp 67.7 y 57.5 s/veh, el modelo del estudio 68.1 y 55.2 y el libre 131.1 y 77.1; con la alta,
  125.6 y 73.3, 79.5 y 70.9, y 558.2 y 175.6. Un revisor alargó el de la alta a 40 episodios: obsamp 76.9 y 70.6 en
  los episodios 30 y 40; el del estudio, 80.1 y 101.5.
- `evaluar_control.py`, sin simular: con el modelo del estudio en el lugar de obsamp y del libre, reproduce el
  veredicto publicado (−4.39 y −4.51 % frente al fijo con la publicada, −5.73 y −6.57 % con la alta: MEJORA) y empata
  consigo mismo en (b), (c) y (e). Con los entrenamientos del estudio cambiados de nombre (obsamp = el 2042, el del
  estudio = el 4042), (c) da MEJORA en la alta y la lectura dice que no se atribuye al diseño. Con las semillas de humo,
  evalúa bien las políticas de humo de obsamp y del libre.

**Código y datos.** Carpeta `orden_libre_2026-11-17/control/`, dentro de la de esta prueba; no pisa nada de ella.
Huellas sha256 de los programas:
- `demo_rl/rl_ippo.py`: 8ce8e77f8d11d97327a2719e2d42907984332d56fc9dc01ce72496ec74ef95ca (trae las dos opciones)
- `entrenar_control.sh`: b48034d23feefdd0054eea67632b48bcdc3075d4aaee1c65ff9367b8b987380c
- `evaluar_control.py`: fff8714e738162128379488b8d0c27e025bce4946f9a810e67e511e6f510b8b5
- `comprobar_fases.py`: 465c94613bf83ef80d5ffb12d230a787325176069dcc9eb8799525434ae5d937 (el de esta prueba)

El resto del código y los datos son los del repositorio en el commit 53bdb48 y los de esta prueba, sin cambios;
`huellas.sha256` lista los 27 archivos con su huella. `entrenar_control.sh` y `evaluar_control.py` no corren si alguno
cambió, y `evaluar_control.py` no evalúa una política obsamp que no traiga en su meta las huellas de este código.

**Cuándo.** Se lanza a las 19:50, antes de cualquier evaluación con las tandas: los seis entrenamientos a la vez (bases
42, 2042 y 4042, con la demanda publicada y con la alta), con las mismas opciones que el modelo libre salvo
`--obs-ampliada` y la etiqueta. `logs/lanzamiento.txt` guarda la hora y las huellas comprobadas.

### Comprobación: por qué funciona el orden libre (17.11.2026, 23:25)

Se anota antes de correr ninguna semilla de las tandas con este control. Para prepararla solo se usaron las semillas de validación (21001-21008) y de humo (424301-424310).

**Qué se vio antes y cómo.** Después de evaluar el modelo libre, un diagnóstico sin registrar miró sus luces. En las semillas de validación 21001-21004, el modelo libre citado repite casi siempre el mismo ciclo: Reducto de frente, giros, Reducto de frente otra vez, 34 s con todo en rojo y 28 de Julio con Balboa. Lo hace en 112 de 115 ciclos con la demanda publicada y en 94 de 97 con la alta. Después, en las semillas de humo 424301-424310, el diagnóstico puso ese orden en controles sin aprendizaje:
- Primero, en dos planes fijos, sin detectores: con los verdes del fijo ajustado (el de Reducto de frente, partido en dos) y con los verdes medios del modelo libre en las semillas de validación. No bajaron el retraso frente al fijo ajustado: 57.47 y 63.72 s/veh frente a 57.42 con la publicada (+0.1 y +11.0 %), y 75.14 y 75.82 frente a 69.91 con la alta (+7.5 y +8.4 %). Con verdes fijos, el orden solo no basta. Por eso se usa el actuado ajustado, cuyos verdes se adaptan a la cola.
- Después, en el actuado ajustado del estudio, sin reajustarlo. Dio 50.62 s/veh con la publicada y 59.81 con la alta: −4.7 y −6.0 % frente al actuado ajustado (53.14 y 63.63; menos retraso en 10 de 10 semillas) y −2.2 y −2.5 % frente al modelo libre (51.76 y 61.31). En la dirección de (2), el modelo libre tiene +2.2 y +2.5 % frente al actuado con el orden, con más retraso en 9 y 10 de 10 semillas.

Son 10 semillas y no son las de evaluación: por eso se mide con las tandas.

**Qué se prueba y por qué.** La tesis es de RL; esto solo explica la mejora del modelo libre. Hasta la prueba del orden libre, todos los controles tenían el mismo orden. En esa prueba solo el modelo puede cambiarlo, así que su mejora frente al actuado ajustado mezcla dos cosas: el orden que encontró y cómo decide cada verde. Aquí se separan en lo principal, con el actuado ajustado usando el orden del modelo libre (las demás diferencias, en «Qué mide y qué no»). No es un control nuevo del estudio: no tiene veredicto y no cambia ningún veredicto registrado. El modelo libre sigue con FUNCIONA en las dos demandas. Fabian Alvarado aprobó correrla el 17.11.2026 hacia las 22:15, después de ver el diagnóstico, solo para explicar la mejora del modelo libre.

**El programa** (`lima_actuadoaj_orden.add.xml`, uno por demanda). Es el actuado ajustado del estudio, sin reajustar:
- el mismo control por retraso de SUMO;
- los mismos parámetros: alcance de 200 m y retraso mínimo de 3 s con la publicada y de 5 s con la alta;
- el mismo mínimo y máximo de cada verde: 10 a 60 s, y los giros de 10 a 38 s con la alta.

Cambia solo el orden: Reducto de frente, giros, Reducto de frente otra vez, 34 s con todo en rojo y 28 de Julio con Balboa. Los dos verdes de Reducto de frente tienen los límites de Reducto de frente. Cada cambio lleva 3 s de ámbar. Antes del rojo total, todos los verdes pasan por ámbar, con la regla del plan. El rojo total va solo antes de 28 de Julio y Balboa, como en el plan. Empieza en Reducto de frente, como el actuado ajustado. Las fases y los parámetros son los del diagnóstico.

**Comparaciones.** Retraso total por vehículo, tanda por tanda, con la estadística del estudio: cambio %, IC95 por bootstrap pareado con 10 000 remuestreos y p de Wilcoxon pareado. De cada una se informa también en cuántas de las 100 semillas el control tiene menos retraso.
- (1) El actuado con el orden frente al actuado ajustado: el efecto del orden, sin aprendizaje.
- (2) El modelo libre citado (base 4042 con la publicada, base 42 con la alta) frente al actuado con el orden: lo que aporta el aprendizaje además del orden. Al lado, la media por semilla de los tres entrenamientos libres, cada entrenamiento y el rango entre sus medias.
- (3) El actuado con el orden frente al fijo ajustado: solo como referencia.

Para leer junto a (1) se repite el modelo libre citado frente al actuado ajustado, que ya está en `veredicto_libre.md`. Los resultados por semilla del fijo, del actuado ajustado y del modelo libre ya existen: se leen y no se vuelven a correr.

**Cómo se leen.** Un sentido cuenta si el IC95 queda entero de un lado del cero y p < 0.05. Se lee solo si se repite en las dos tandas; si no, no se lee un sentido.
- (1) Con menos retraso: el orden, sin aprendizaje, baja el retraso del actuado ajustado. Con más retraso: el orden solo no basta. Sin diferencia: el retraso no cambia de forma distinguible.
- (2) El modelo libre con menos retraso: el aprendizaje aporta además del orden.
- (2) El actuado con el orden con menos retraso, o sin diferencia: la mejora del modelo libre frente al actuado ajustado se explica por el orden que encontró, no por decidir cada verde mejor que el actuado. El aporte del modelo es entonces haber encontrado ese orden. Para usarlo sin aprendizaje, el diagnóstico apunta a un control actuado con detectores: con los dos planes fijos que probó, el mismo orden no bajó el retraso.

La lectura de (2) es firme solo si los tres entrenamientos libres, cada uno frente al actuado con el orden, van en el mismo sentido en las dos tandas; si no, se informa como no firme. El rango entre entrenamientos se da solo como dato.

**Qué mide y qué no.**
- El actuado con el orden sigue siempre el ciclo que más usa el modelo libre. El modelo lo elige en cada cambio: del 3 al 5 % de sus ciclos son otros, casi todos sin giros.
- No tiene el tope de rojo del modelo libre (163 s con alguien esperando). En las diez semillas de humo (424301-424310), con la alta, los giros pasaron más de 163 s sin verde en 15 de 224 esperas (en 9 de las 10 semillas; hasta 187 s). El modelo libre, medido igual (con o sin alguien esperando), en 6 de 224 (hasta 170 s): su tope solo cuenta mientras alguien espera. Con la publicada, el actuado nunca (0 de 274) y el modelo libre 2 de 265 (hasta 188 s).
- Decide con sus propios detectores (200 m) y alarga cada verde según el retraso que ven. El modelo libre mira detectores de 75 m y decide cada 2 s. Con la alta, el verde máximo de giros del actuado es 38 s; el del modelo libre, 60 s.
- No se busca otro orden ni otro ajuste.

**Semillas.** Las dos tandas del estudio (22001-22100 y 23001-23100), las mismas de todos los controles.

**Pruebas** (sin las semillas de las tandas; en `pruebas/`).
- Con el actuado ajustado sin cambios, el corredor da en 21001-21008 exactamente lo del estudio (`val_referencias.json`): 52.96875 s/veh con la publicada y 63.49625 con la alta. Sus columnas son las de `eval_t1_actuadoaj.csv`.
- Luces segundo a segundo en las diez semillas de humo, en cada demanda: 0 fallas con `comprobar_fases.py`. Hay 3 s de ámbar en cada cambio y 34 s de rojo total solo antes de 28 de Julio y Balboa. El ciclo del orden se cumple en todo el episodio, y cada verde queda dentro del mínimo y el máximo del actuado. Son las mismas luces del diagnóstico, y guardarlas no cambia el retraso.
- En 424301-424310 da lo del diagnóstico, semilla a semilla: 50.62 y 59.81 s/veh (el actuado ajustado, 53.14 y 63.63).
- `comparar_orden.py`, sin las tandas: con las semillas de humo da las cifras del diagnóstico, y con datos inventados, la respuesta esperada, también una lectura que no se repite y una no firme.
- `correr_tandas.sh`, con un corredor falso que no simula: va una demanda después de la otra con 3 procesos, se detiene y sale con código 1 si una evaluación falla, y solo sale con 0 si están las cuatro.

**Código y datos.** Carpeta `orden_libre_2026-11-17/actuado_orden/`. `correr_orden.py` importa `estudio.py` y corre cada semilla con `estudio._fija`, la misma función de los brazos de sumo puro del estudio. Usa la carpeta de cada demanda (`LIMA_CARPETA`), con las mismas opciones de SUMO. El resto del código y de los datos son copias del repositorio en el commit 53bdb48, sin cambios. Huellas sha256:
- `demo_rl/lima/lima_actuadoaj_orden.add.xml`: 539b67cb88347cfd3b24b2fa376c64d6a93a8451f5b847a9b92867c41f5d9c9b
- `demo_rl/lima/alta/lima_actuadoaj_orden.add.xml`: b5f52cc0fc93636403c86b5fe9aceebfb4b1934e62c299f6381438ed7c569fcb
- `escribir_orden.py`: 138d01ecc83765c198c3d03240e8753de0f92f21994fa5746f31932cf3b209d1
- `correr_orden.py`: 4d507b65f9b92ed558a20a4b8b1a4bb26e668d758563ba3bd5f58ffb4e033b76
- `correr_tandas.sh`: 21e291f68b2e5c9e7f0a54488a07020c848c4b87e0b513912b9f74de35815dfc
- `comparar_orden.py`: 44133bf9ab07d4fe4092ae199c7be692d624e31881f831ac4c51e426856625b7
- `pruebas.py`: 8da6aff31b0a590fd09808b18d84a01bb0724772dd987068caebda962daf684d
- `comprobar_fases.py`: 465c94613bf83ef80d5ffb12d230a787325176069dcc9eb8799525434ae5d937 (el de la prueba del orden libre)

`huellas.sha256` lista los 43 archivos que usan las tandas y la comparación: 23 de la carpeta y los 20 resultados por semilla del repositorio y del modelo libre que se comparan. `correr_tandas.sh`, `correr_orden.py` y `comparar_orden.py` no corren si alguno cambió.

**Cuándo.** Se anota antes de correr las tandas. Se lanza con `bash correr_tandas.sh`: una demanda después de la otra, 3 simulaciones a la vez, unos 15 a 20 minutos. Se compara con `python comparar_orden.py`. `logs/lanzamiento.txt` guarda la hora y las huellas comprobadas.

## Enmienda: el nudo en la red del Óvalo Vasco, con el modelo de orden libre (18.11.2026, 11:03)

Se registra antes de ajustar las referencias, de entrenar y de evaluar en esta red. En la red del óvalo solo se usaron
la base 7 y semillas de humo del bloque 424301-424360; ninguna semilla de ajuste (2001-2030), de validación
(21001-21008) ni de evaluación (22001-22100, 23001-23100 y 24001-24100).

**Qué se vio.** El 17.11.2026, con Google Maps y Street View, Fabian Alvarado confirmó que el nudo es un óvalo, el Óvalo
Vasco: las calzadas de Reducto y de 28 de Julio rodean una isla, se cruzan en cuatro esquinas que maneja el mismo
semáforo, y en la hora punta hay vehículos que esperan dentro. La red del estudio reduce el nudo a un solo cruce sin
tramos internos ("Escenario" y "Decidido antes"). Así nadie queda dentro, y los giros de 28 de Julio hacia Reducto sur y
de Balboa hacia Reducto norte pasan con verde sin cruzarse con Balboa ni con 28 de Julio, que tienen verde a la vez.

**Qué se decidió.** La revisión del 17.11 (`revision_ovalo_2026-11-17/`, memo de la compuerta) fijó una regla: la red
del óvalo reemplaza a la del estudio solo si, con el plan actual y la demanda publicada, el retraso total queda en el
nivel E (55 a 80 s por vehículo), no se traba y los dos giros esperan donde esperan en el sitio. Ninguna versión la
cumplió y el memo recomendó no cambiar la red. El 18.11.2026, hacia las 09:00, Fabian Alvarado decidió estudiar el nudo
en la red del óvalo armada con sus medidas de Google Maps, para que la simulación muestre cómo pasan los autos por el
óvalo, y con el modelo que elige el orden de los verdes. Todos los resultados del nudo se rehacen en esa red.

**La red** (carpeta `nudo_ovalo_estudio/`, `demo_rl/lima/ovalo/armar_ovalo.py`):
- La del óvalo con las medidas de Fabian: de esquina a esquina, norte 18.44 m, oeste 24.43 m, este 19.92 m y sur
  15.74 m. Lugar libre para esperar: 6.7, 5.3, 4.0 y 6.3 m.
- Afuera, lo del estudio: las mismas entradas y salidas, con sus largos y carriles, y los mismos detectores E2 de 75 m.
- Un solo semáforo, `semaforo_S1`, en los 10 nodos. La segunda esquina no tiene semáforo propio: el que cruza otro
  flujo cede el paso. Quien quedó adentro al cambiar la luz sale primero. Los ramales de giro de Reducto cruzan los
  lados donde están en la red medida, a 3.5-9 m de su esquina, como en OpenStreetMap.
- Esquinas: ningún giro dentro del óvalo queda por debajo de 5.56 m/s (20 km/h, una esquina urbana de unos 5.6 m de
  radio). Con las esquinas cortadas en el borde de la calzada que cruzan, cinco giros quedaban con radios de 1.5 a
  4.3 m (de 2.9 a 4.9 m/s), un defecto de construcción. Se sube la velocidad de esos cinco tramos; no cambia ninguna
  forma ni ningún largo.
- Trabas: todas las corridas usan la opción de SUMO que deja de respetar a un vehículo que lleva más de 10 s detenido
  bloqueando un cruce (`--ignore-junction-blocker 10`, en el `.sumocfg`). Sin teletransportes por atasco, como antes.
- Lo demás, como el estudio: fin a los 6000 s, la misma demanda (los mismos flujos, con su camino por el óvalo), la
  publicada y la alta, el plan actual medido, la métrica (retraso total por vehículo).

**Lo que no cumple.** Con esta red, el plan actual da 224 s por vehículo con la demanda publicada (170 a 290) y 512 con
la alta (440 a 592), con las semillas de humo 424301-424320: nivel F. En la red del estudio, con las mismas semillas, da
59 y 87. No cumple el criterio con que se aceptó la red del estudio (nivel E). Por eso el retraso simulado del nudo ya
no se compara con el nivel de servicio publicado: los resultados comparan controles en la red del óvalo. Lo que más
pesa es el giro de 28 de Julio hacia Reducto sur (1093 s por vehículo con la publicada): en su verde casi no encuentra
hueco en el flujo de Balboa y adentro caben unos 4 autos. Ese giro no se contó en el sitio; su demanda (187 veh/h) es la
supuesta del estudio.

**Controles.** Los del estudio, ajustados en esta red con su procedimiento y sus semillas: plan actual; fijo ajustado al
segundo (2001-2010 y los diez mejores con 2001-2030; verdes de 10 a 120 s) y ciclo mínimo; actuado de SUMO y actuado
ajustado (los pasos del segundo estudio, enmienda del 14.11.2026, 04:05), con la comprobación del borde (14.11.2026,
15:55). La comprobación del borde se aplica con su regla escrita de forma general: un paso más allá de cada parámetro
que quedó en un extremo de los valores probados, con todo lo demás igual al mejor de su tipo, y todos a la vez si son
varios. Esa regla da exactamente las variantes registradas en los cuatro casos de Lima; en el óvalo el ganador puede
quedar en otro borde. Si el ganador cambia, el anterior se conserva con el sufijo `b` y se informa al lado.

**Modelos.** Dos, con las bases 42, 2042 y 4042, 400 episodios, validación cada 20 en 21001-21008 por retraso total y,
como versión evaluada, la de menor retraso en la validación. De cada modelo y nivel, el entrenamiento citado es el de
validación mediana; los otros dos se evalúan igual y se informan al lado.
- **Modelo de orden libre** (`--orden-libre`, etiqueta `libre`): **es el modelo citado del nudo.** Las mismas reglas de la
  prueba del 17.11.2026, 17:25: mantener el verde o pasar a cualquiera de los otros dos estados, verdes de 10 a 60 s,
  3 s de ámbar, los 34 s con todo en rojo siempre antes de 28 de Julio y Balboa, tope de 163 s en rojo mientras alguien
  espera, y observación de 56 entradas. En el óvalo las luces de adentro dependen del estado anterior: el programa libre
  tiene un verde por cada estado y estado anterior, con la regla "quien está adentro sale primero". Lo que sale conserva
  la letra de su propio verde y lo que entra le cede el paso. En el orden del plan, las luces son las del plan actual.
- **Modelo de orden fijo** (el modelo completo del estudio, etiqueta `completo`, las opciones de `lima/entrenar.sh`), en
  la misma red: sirve para medir cuánto aporta elegir el orden.
- Los 12 entrenamientos (6 de cada modelo) se lanzan a la vez.

**Comparaciones y veredicto.** Retraso total por vehículo, tanda por tanda (22001-22100 y 23001-23100, las mismas para
todos), con la estadística del estudio: cambio %, IC95 por bootstrap pareado (10 000 remuestreos) y p de Wilcoxon
pareado.
- (1) El modelo de orden libre frente al fijo ajustado al segundo, sin perder contra el actuado ajustado: el veredicto
  del nudo, con la regla de la tesis.
- (2) El modelo de orden libre frente al de orden fijo en la misma red: la misma regla, con el de orden fijo en el lugar
  del fijo ajustado. Al lado, la media por semilla de los tres entrenamientos de cada modelo y el rango entre sus
  medias. Si la diferencia entre esas medias no supera el rango mayor en las dos tandas, se dice que la etiqueta no se
  distingue de la variación entre entrenamientos; la etiqueta no cambia.
- (3) El modelo de orden fijo frente al fijo ajustado, sin perder contra el actuado ajustado: se informa al lado.
- (4) Frente al plan actual: el cambio, sin etiqueta. El actuado de SUMO sin ajustar y el ciclo mínimo, como
  referencias secundarias.
- La etiqueta citada es la que se repite en las dos tandas; si no, EMPATA. Es provisional si el entrenamiento citado de
  un modelo comparado no se estabiliza (regla de la tesis). Cada nivel de demanda tiene su propio veredicto.

**Prueba de robustez del reparto.** Como la del 13.11.2026, 22:10: las dos variantes del reparto con el mismo total
publicado, con su camino por el óvalo; el plan actual, el fijo ajustado y el actuado ajustado de la demanda publicada y
el entrenamiento citado de cada modelo, sin reajustar ni reentrenar; 100 semillas, 24001-24100. Se informa el retraso
de cada control y el cambio del modelo de orden libre frente a cada uno, tal como salga. No interviene en el veredicto.

**Qué queda de la red anterior.** Los resultados del nudo en la red del estudio (MEJORA con las dos demandas frente al
fijo ajustado, con más retraso que el actuado ajustado) y la prueba del orden libre en esa red (FUNCIONA en las dos
demandas) no se borran ni se vuelven a correr: quedan en este registro y en sus carpetas. Por decisión de Fabian
Alvarado, la tesis informa solo los resultados en la red del óvalo, que pasa a ser la red del nudo.

**Pruebas** (base 7 y semillas de humo; en `nudo_ovalo_estudio/pruebas/`).
- Con las opciones apagadas, y también con `--orden-libre`, el código da en la red del estudio lo mismo que el de
  `orden_libre_2026-11-17/`: 2 episodios con la base 7 y su evaluación, con las dos demandas; CSV, tensores, trazas de
  luces y evaluación, iguales bit a bit.
- La red: entradas, salidas, detectores, demanda y plan actual son los del estudio y de la revisión (comprobado con
  sumolib); el escritor de programas da los mismos programas que la revisión. Frente a la red medida de la revisión
  solo cambia la velocidad de los cinco giros (de 2.9-4.9 a 5.56 m/s); las formas, los largos y la matriz son los mismos.
- Plan actual, 20 semillas de humo por demanda (424301-424320): ninguna traba permanente en la red final (a los 6000 s
  no quedan vehículos detenidos sin que nadie llegue). La red medida sin arreglos se traba en 2 de 20 con la publicada.
  Con los dos arreglos, el plan actual tiene 140 y 133 s por vehículo menos que en la red medida (en 20 de 20 semillas).
- Los dos modelos, 5 episodios con la base 7 y su validación en 424303-424304, con las dos demandas: 0 fallas en la
  comprobación segundo a segundo de las luces (3 s de ámbar en cada cambio, con el ámbar que toca según el estado
  anterior; 34 s de todo rojo solo antes de 28 de Julio y Balboa; verdes de 10 a 60 s; ningún estado pasa del tope).
  El de orden libre usa los seis pasos posibles (cerca de la mitad de los cambios no siguen el orden del plan); el de
  orden fijo, ninguno fuera del orden. Repetidos, dan lo mismo byte a byte.
- Las políticas citadas que ya existen, entrenadas en la red del estudio, jugando en el óvalo con semillas de humo:
  0 fallas de luces; sirvieron para medir el tiempo de un episodio y no se citan.
- Un paso corto de la búsqueda de las referencias con semillas de humo (424321-424328), solo para medir tiempos: el
  actuado de SUMO por huecos deja cientos de vehículos sin terminar en el óvalo (sin traba: la red se llena porque
  sirve menos de lo que entra); el actuado por retraso, no. La búsqueda no cambia: empieza por la cadena de huecos, como
  en el estudio, y gana la variante que dé menos retraso.
- Los lanzadores no corren si cambia un archivo de `huellas.sha256` (probado con un verde del plan cambiado).

**Código y datos.** Carpeta `nudo_ovalo_estudio/`, junto al repositorio (como `orden_libre_2026-11-17/`). El código es el
de la prueba del orden libre más los cambios del óvalo; con las opciones apagadas da los mismos números que el
repositorio en 53bdb48. Los cambios:
- `rl_ippo.py`: con `--orden-libre`, si junto al `.sumocfg` está `lima_libre.json`, el programa libre se arma con sus
  fases (en el óvalo, 12: un verde y un ámbar por estado y estado anterior, y un todo rojo por estado que termina); los
  carriles de cada estado son solo los de las entradas; la geometría cercana se guarda por red; la huella del código va
  en el meta de toda política.
- `estudio.py` y `borde_actuado.py`: con `LIMA_PROGRAMA=programa_ovalo`, los programas se escriben con el escritor del
  óvalo (`programa_ovalo.py`, nuevo). `borde_actuado.py ovalo`: la regla del borde escrita de forma general.
Huellas sha256:
- `demo_rl/rl_ippo.py`: c61b706c7a96baa07ca9737564a5124c50bea7da911e5c77805dd62b784e4bc7
- `demo_rl/lima/estudio.py`: 5f08daaa8c1005962b70ef10d2fabe28a924f76cdb9790c4b54aa8c70b67bbf4
- `demo_rl/lima/borde_actuado.py`: 77ff0c9d21409db8964f8e9e21c49cfb91c7246a121c1d51ac07eb9b512ffb3e
- `demo_rl/lima/programa_ovalo.py`: 5d5f03cca511b296762be38e930150a5bd2975c1ee88579a65985b02dd2d34c2
- `demo_rl/lima/ovalo/plan_ovalo.py`: 486b70246157d250fd260118cfa1f14d07eecb5fd8d11919cc570220d63a7d29
- `demo_rl/lima/ovalo/armar_ovalo.py`: 90a8f59819c4392c39c5f63405156cf3d14f6c80a43af500cfc51ad567f43f0f
- `entrenar.sh`: a9a95791138ded3ba283199c382a5fdf16bd422cffb7c3251961e8c7ec8d311e
- `referencias.sh`: 474472c8a4ee8c7fa88f7dbfb343e9b9f5448c60ffacb80e28be3da651ac8f79
- `evaluar_ovalo.py`: 0914114c381be71f94947568320d37b68b891498f59d93b03e15c2f9de46d3a2
- `comprobar_fases.py`: 6e10f4c157622ced5058e48fcf424bf641b5b6b917c2319ac88a6fa2cd8ea20e
- La red (`lima.net.xml`, la misma en las cuatro carpetas): 7e6ee64cf7705d403c68b9d906a16665a32874b84f6e774e0e10fc16da665cb6
- El `.sumocfg` (con la válvula): cbc78301ccee0f9d70fc2febd58f3e5c7beb51d2062ad80bf8fa84bbe6815355
- El plan actual (`lima.add.xml`): 85f8492737547e5e7fecb6af00f4636b2607b9dd8831b4f5939f8743246f799f
- El programa del orden libre (`lima_libre.json`): d25dd1eceac3c976e68775d7681316243c5efa8cbc4be5231fac4ad39b10ba67
- La demanda publicada y la alta (`lima.rou.xml`): d80502be4340cea6ebaa05e74d13f7903accb251d44f3fd5cc5c605b345b161d y
  d27a1598c30f1e3b5e39db42c265907726b69a6a2faa34b73aa0e9ff1b53ec58 (las de la revisión del óvalo)

`huellas.sha256` lista los 71 archivos de código y datos. `entrenar.sh`, `referencias.sh`, `evaluar_ovalo.py`,
`tablas_ovalo.py` y `figura_secuencia.py` no corren si alguno cambió, y `evaluar_ovalo.py` no evalúa una política que no
traiga en su meta las huellas de este código.

**Cuándo.** Después de conocer todos los resultados del nudo en la red del estudio, y antes de ajustar, entrenar o
evaluar en la red del óvalo. Primero se lanzan los 12 entrenamientos y, al lado, las referencias. `logs/lanzamiento_*.txt`
guarda la hora y las huellas comprobadas.

## Si aparece un error

Solo se corrigen errores de código. Se repite todo lo afectado y se anota aquí qué se cambió y cuándo.

### Corrección de los programas de evaluación del óvalo (18.11.2026, 11:33, antes de evaluar)

Un revisor encontró, antes de cualquier evaluación en la red del óvalo, cuatro errores en los programas que se usan
después de entrenar. Los entrenamientos y la búsqueda de las referencias no cambian y siguen corriendo.
- `evaluar_ovalo.py` podía evaluar el actuado ajustado antes de la comprobación del borde y no volvía a evaluarlo. Ahora
  exige que `referencias.sh` haya terminado el nivel (con el ganador del borde instalado) y se detiene si un programa o
  una política es más nuevo que su evaluación.
- La lectura de la comparación (2) no miraba el sentido de la diferencia. Queda fijada con la regla del grupo de control
  (17.11.2026, 19:50): la etiqueta de (2) se distingue de la variación entre entrenamientos solo si, en las dos tandas,
  la diferencia entre las medias de los tres entrenamientos de cada modelo va en el sentido de la etiqueta y supera el
  mayor rango entre entrenamientos. Con EMPATA no aplica.
- `figura_secuencia.py` escribía la figura de las dos demandas con el mismo nombre. Ahora lleva el nivel en el nombre y
  se detiene si la corrida falla.
- El veredicto informa, por tanda y por control, los vehículos sin terminar o sin entrar a los 6000 s: su retraso cuenta
  solo hasta el corte.

Menores: la procedencia de las políticas revisa también sus opciones; el veredicto se escribe por nivel; la robustez
exige las semillas 24001-24100; las tablas exigen que la figura del ciclo sea del modelo de orden fijo citado;
`ver_ovalo.py` solo acepta semillas de validación o de humo.

Aclaraciones, sin cambio de código: la regla general del borde (`borde_actuado.py ovalo`) no extiende el umbral de
atasco ni el esquema de verde máximo, como las variantes registradas, que reproduce. El fijo ajustado puede dar verdes
de hasta 120 s; el actuado y los modelos tienen un máximo de 60 s, como en el estudio. Si el fijo pasa de 60 s, se dirá
como límite.

Huellas nuevas: `evaluar_ovalo.py` 4621671b9d0a38df20baac5c1da31d104d79f164aa46c11e9caf07489aebc836,
`figura_secuencia.py` d62bc5a056cbd9301b6948c9b5f7d1d0c39d65652f8dd36ba7f2eb6046da1143, `tablas_ovalo.py`
e845004001cb2e4b499ca78d8266ab1ff564d3e132273d4a89e36d3d79a63a84 y `ver_ovalo.py`
9b4f8036a1cdcffa686478444067c057c5f73aa97611a2dc30f5e37081c2b221. Parches y pruebas en `nudo_ovalo_estudio/revision/`.

### Detención del estudio del óvalo: los carriles de Reducto están mal en la red (18.11.2026, 17:40)

**Qué se detectó.** Fabian Alvarado revisó la red contra el lugar (18.11.2026, entre las 17:15 y las 17:35) y encontró
que las dos entradas de la Av. Reducto tienen los carriles mal desde la primera red del nudo (13.11.2026):

| Entrada | En la red (la del 13.11 y la del óvalo, iguales carril por carril) | En el sitio, según Fabian Alvarado |
|---|---|---|
| Reducto, de norte a sur | 4 carriles: el izquierdo solo gira a la izquierda (al puente); tres de frente, el derecho también hacia Larco | 5 carriles: la avenida de 3 y un ensanche de 2, los dos de la izquierda solo para girar a la izquierda |
| Reducto, de sur a norte | 5 carriles: dos izquierdos solo giran a la izquierda (a Larco), dos de frente, el derecho solo gira al puente | La calzada trae 2 carriles y se abre a 4 poco antes del semáforo: los dos de la izquierda giran a la izquierda; los otros dos van de frente o giran hacia 28 de Julio |
| Balboa | Sin el giro a la izquierda hacia Larco (quedó fuera el 13.11) | Puede girar a la izquierda hacia Larco, subir a Reducto norte o seguir de frente hacia el puente |

**Causa.** El 13.11.2026 Fabian Alvarado escribió "Hay 5 carriles, bueno es una avenida que forma 3 carriles y llegando
al paso peatonal se abre un cachito para dos carriles más que son específicamente para el giro a la izquierda". El
mensaje no decía el sentido; respondía a una pregunta sobre Reducto desde el sur y se asignó a esa entrada sin
confirmarlo. OpenStreetMap coincide con lo que dice ahora: la calzada de norte a sur tiene 3 carriles
(`turn:lanes = through|through|through;right`, vía 653645242) y la de sur a norte, 2.

**Alcance.** Tienen esos carriles todos los resultados del nudo obtenidos hasta hoy: el estudio del 13.11.2026, la
prueba del orden libre y su grupo de control (17.11.2026) y el estudio en la red del óvalo (enmienda del 18.11.2026,
11:03). La demanda supuesta también depende de ellos, porque se repartió según los carriles y el verde de cada
movimiento. El corredor de Benavides no se ve afectado.

**Decisión** (Fabian Alvarado, 18.11.2026, hacia las 17:35): corregir la red y repetir todo el estudio del nudo, y
detener la corrida en curso.

**Qué se detuvo** (18.11.2026, 17:39):
- Los seis entrenamientos de la demanda alta: orden libre en los episodios 237 a 239 de 400; orden fijo en 266 a 278.
- El ajuste de las referencias de la demanda alta (iba en el actuado; el fijo ajustado había quedado en verdes
  [71, 23, 76], 280.69 s/veh con 30 semillas).
- Las tandas de las referencias de la demanda publicada, lanzadas a las 16:37: quedaron el plan actual (223.07 y
  222.48 s/veh), el fijo ajustado (155.75 y 158.06) y el actuado ajustado de la tanda 1 (139.26); la tanda 2 del
  actuado ajustado, el actuado de SUMO y el ciclo mínimo no se corrieron.

**Qué había terminado.** Los seis entrenamientos de la demanda publicada (el de orden libre con la base 42 terminó
solo a las 17:39) y las referencias de la publicada. Mejor validación de cada entrenamiento (21001-21008, s/veh): orden
fijo 142.31, 146.59 y 138.18 (bases 42, 2042 y 4042); orden libre 191.79, 152.64 y 202.08. Referencias en esas
semillas: plan actual 225.10, fijo ajustado 157.28, actuado ajustado 138.78. **Ningún modelo se evaluó en las tandas.**

**Qué se hace con lo corrido.** Nada de este estudio se informa como resultado. La carpeta `nudo_ovalo_estudio/` queda
como está. Desde las 16:55 corre aparte, con semillas de humo y sin tocar esa carpeta, un diagnóstico de por qué el
modelo de orden libre validó peor que el de orden fijo (`diagnostico_orden_ovalo_2026-11-18/`); no es parte del estudio
registrado.

**Lo que sigue.** Antes de lanzar nada se anotará aquí la enmienda con la red corregida (carriles de Reducto y giro
de Balboa hacia Larco, confirmados por Fabian Alvarado), la demanda recalculada con la misma regla y las comprobaciones.
Las reglas del estudio no cambian; si el diagnóstico demuestra un defecto del programa del orden libre, su corrección se
anotará en esa misma enmienda, con la prueba del defecto.

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

## Enmienda: estudio 2 del corredor de la Av. Benavides, con la red corregida y los verdes mínimos de los peatones (19.11.2026, 17:35)

Se registra antes de ajustar las referencias, de entrenar y de evaluar en la red corregida. Para el corredor reemplaza la
red, la demanda, los verdes mínimos, las partidas de la búsqueda del fijo y los pasos del actuado registrados el
13.11.2026 (22:40) y el 14.11.2026 (03:00, 03:25, 04:05, 05:40, 05:50 y 15:55). Los controles, los tres modelos y sus
opciones, las bases, las semillas, la métrica, las comparaciones, la regla del veredicto, la prueba del canal cortado y
la prueba de robustez siguen como quedaron registrados. Corre en una carpeta aparte, `corredor_estudio2/` (copia del
código del estudio de `demo_rl/` en el commit 53bdb48, con los cambios de abajo); `demo_rl/lima/corredor/` queda como
está. La tesis informa solo este estudio.

**Por qué.** La revisión del corredor del 19.11.2026 (`revision_corredor_2026-11-19/`, cuatro informes) comparó la red
con OpenStreetMap del corredor entero, bajado ese día, y encontró dos errores: la Av. Casimiro Ulloa (C5) llega a la
avenida solo desde el norte (el cruce es en T) y la red tenía una rama sur que no existe, por la que entraban 500 veh/h
y salían 475; y la avenida llega a Larco desde el oeste con 2 carriles por sentido, no 3. Encontró además que el
modelo daba a las transversales verdes de 10 a 12 s, que no dejan cruzar la Benavides a un peatón (16 a 19 s a 1.2
m/s). Fabian Alvarado decidió (19.11.2026, hacia las 17:00) corregir la red, poner verdes mínimos para los peatones y
volver a correr el estudio del corredor.

**Qué se sabía al registrar.** Los resultados del estudio anterior del corredor (FUNCIONA con las dos demandas: −8.8 y
−8.9 % frente al fijo ajustado al segundo con la publicada, −19.9 % con la alta) y las pruebas de la revisión en la red
anterior, todas con semillas de prueba: con verdes mínimos de peatones como cota baja y el modelo sin reentrenar, −3.1 %
(publicada) y −16.7 % (alta); con 2 carriles al oeste de Larco, −6.5 %; con la alta, un fijo de 80 s con onda verde en
los dos sentidos tenía un 8.8 % menos de retraso que el fijo ajustado de 62 s; con la publicada, un actuado con hueco
de 1.25 s y verdes máximos de 35 y 25 s, un 1 % menos que el actuado ajustado. Por eso se agregan las partidas y los
pasos de abajo. En la red corregida solo se usaron la base 7 (dos episodios, semillas 8 y 9 de SUMO) y las semillas de
prueba 424331, 424332 y 424340; ninguna semilla de ajuste (2001-2030), de validación (21001-21004), de evaluación
(22001-22100 y 23001-23100) ni de robustez (24001-24100), y ninguna de las bases 42, 2042 y 4042.

**La red** (`corredor.py`).
- C5, Av. Casimiro Ulloa: cruce en T. La transversal llega solo desde el norte, de doble sentido, con 2 carriles por
  sentido. Lo que baja gira a la derecha, hacia el oeste, por el carril derecho, o a la izquierda, hacia el este, por
  el izquierdo. Desde la avenida, yendo al oeste, se gira a la derecha hacia Casimiro Ulloa; yendo al este no hay giro
  (como en el resto, no hay giros a la izquierda desde la avenida). Al sur queda, como en las calles de un sentido, un
  tramo de un carril sin demanda, para que el modelo describa cada cruce con cuatro accesos.
- Avenida al oeste de Larco: 2 carriles por sentido. Hacia el oeste llegan 3 carriles a Larco y siguen 2: el derecho
  solo gira hacia Larco (la regla que ya se usaba en Paseo de la República).
- Lo demás no cambia. En los seis cruces ningún par de movimientos con verde está en conflicto según la red.

**La demanda.** La misma regla: en los tres cruces con volumen publicado, la transversal se elige para llegar a él; en
los otros tres, se supone por sus carriles y no cambia.
- Casimiro Ulloa: 500 veh/h, la mitad gira al oeste y la mitad al este (supuesto).
- Larco 934 veh/h (antes 1050), Paseo de la República 612 por sentido (719) y República de Panamá 898 por sentido
  (1009). Los tres cruces quedan en 3390, 3779 y 4358 veh/h (publicado: 3390, 3778 y 4358).
- Entran 7654 veh/h (antes 8706). La alta es la misma por 1.2: 9185 veh/h. La robustez, el mismo total de la publicada
  con el reparto cambiado como se registró el 14.11.2026 a las 03:25.

**Verdes mínimos de los peatones.** Cada verde dura al menos lo que necesita un peatón que empieza a cruzar con el verde
para llegar al otro lado antes de que termine el ámbar: 3.2 s para empezar más el ancho a 1.2 m/s (Highway Capacity
Manual 2000), menos los 3 s del ámbar, redondeado hacia arriba y nunca menos de 10 s. Con el verde de la transversal se
cruza la avenida; con el de la avenida, la transversal. Anchos de OSM: 3.3 m por carril más el separador central de la
avenida; en Larco, el lado este; en Paseo de la República, el cruce oeste del puente.

| Cruce | Ancho que se cruza con el verde de la avenida / de la transversal (m) | Verde mínimo de la avenida / de la transversal (s) |
|---|---|---|
| C1 Larco | 9.9 / 19.8 | 10 / 17 |
| C2 Alcanfores | 6.6 / 20.9 | 10 / 18 |
| C3 La Paz | 6.6 / 22.8 | 10 / 20 |
| C4 Paseo de la República | 13.2 / 22.0 | 12 / 19 |
| C5 Casimiro Ulloa | 13.2 / 20.7 | 12 / 18 |
| C6 República de Panamá | 13.2 / 19.7 | 12 / 17 |

Valen para todos los controles: el plan típico (ya los cumple), el fijo ajustado, el actuado, el actuado ajustado y sus
variantes coordinadas (verde mínimo de cada estado), el ciclo mínimo (ciclo común de 37 s, cada transversal en su
mínimo) y el modelo, que no puede cambiar de estado antes del mínimo del suyo (`escenarios_lima.py`, `verde_min_tls`, y
`rl_ippo.py`). Sin todo rojo, como antes. Comprobado en la red corregida (base 7, semilla 424332): el modelo no baja de
esos mínimos en ningún cruce.

**Referencias** (`estudio_corredor.py`).
- Fijo ajustado: la misma búsqueda (descenso por coordenadas con pasos de 8, 4, 2 y 1 s; 10 semillas por candidato,
  2001-2010; los diez mejores con 30, 2001-2030), con otras partidas: el plan típico y, en ciclos de 40, 44, 48, 52,
  56, 60, 66, 72, 80, 90 y 100 s, el reparto de Webster con los mínimos de los peatones, sin desfases y con onda verde
  hacia el este, hacia el oeste y en los dos sentidos. Se afinan las tres mejores partidas de ciclos distintos, y al
  mover el ciclo se prueba también con los desfases movidos junto con él.
- Actuado ajustado: los mismos pasos, con los huecos de 0.75 y 1.25 s y tres esquemas más de verdes máximos (avenida /
  transversal: 30/20, 35/25 y 45/35 s).

**Modelos, semillas, evaluación y veredicto.** Sin cambios: el modelo completo (400 episodios, decide cada 2 s) e IPPO
con y sin mensajes corregido (200 episodios), tres entrenamientos de cada uno (bases 42, 2042 y 4042); validación en
21001-21004 por retraso total; se cita la base con la validación mediana; tandas 22001-22100 y 23001-23100; canal
cortado del modelo citado; robustez en 24001-24100 con el plan típico, el fijo y el actuado ajustados de la publicada y
el modelo citado; la misma regla del veredicto para cada nivel.

**Código y huellas.** `corredor_estudio2/huellas.sha256` (sha256 17405a9ff54921b2af672f9401d425ee4bacef52432231246ceb1d27c1228010)
lista los 63 archivos de código y datos; `lanzar.sh` no corre si alguno cambió. Huellas de los datos (16 primeros
caracteres): red `benavides.net.xml` 29713c5f7a161b22; plan típico `benavides.add.xml` 9fd252f33b567ba1; demanda
publicada ccfb40f845572017 y alta d88fbd3f8ff10bf4; robustez, más carga en la avenida 38bc1bcdaacd1188 y más carga en
las transversales 93aed5c043fe1f91.

**Cuándo y en qué orden.** Se lanza a continuación desde `corredor_estudio2/` (`bash lanzar.sh`; la hora queda en
`logs/lanzamiento.txt`): los 6 entrenamientos del modelo completo y, al lado, las referencias de las dos demandas con
sus tandas; cuando terminan las referencias de una demanda, sus 6 entrenamientos de los mensajes; cuando terminan los
entrenamientos, las tandas de los modelos, el canal cortado, los verdes del modelo, la robustez y el veredicto
(`evaluar_nivel.sh`). Estimado, sin medirlo: el modelo completo de la publicada hacia la medianoche y el de la alta el
viernes 20.11 en la mañana.

**Nota sobre la hora (19.11.2026, 17:25).** El título de esta enmienda dice 17:35, que era la hora estimada de
lanzamiento. La enmienda se escribió a las 17:22 y el estudio se lanzó a las 17:23:13 (`logs/lanzamiento.txt`).
