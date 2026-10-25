# Comprobaciones de SUMO del diagnóstico del corredor (25.10.2026)

Pregunta: ¿la falta de tendencia del corredor con la demanda viene del simulador? Corrido sobre una copia de
solo lectura del commit 5196edb (SUMO 1.25.0, Python 3.14, torch en CPU con un hilo por proceso, como
`plan2/cola.py`). Script: `plan2/diag_corredor/sumo_chequeos.py` (modos `teletransportes`, `salida`, `paso`,
`determinismo`, `insercion`, `definiciones` y `resumen`). Datos: `plan2/diag_corredor/sumo/*.csv`; salida
completa del resumen en `plan2/diag_corredor/sumo/resumen.txt`.

## Respuesta corta

SUMO no introduce errores que expliquen la curva. No hay teletransportes, choques ni vehículos perdidos.
La simulación es determinista dígito a dígito. Las definiciones de timeLoss y de espera para entrar son las
que usa la tesis. Sí hay dos rasgos del modelo de SUMO que cambian las magnitudes y conviene declarar:

1. **Inserción.** Con el paso de 1 s y los vehículos entrando detenidos (el valor por defecto, porque las
   rutas no fijan `departSpeed`), una arista de entrada de un carril admite como máximo **1202 veh/h**. La
   línea de detención descarga 1836 veh/h. En P2 las dos entradas de la avenida piden 1320 veh/h durante
   media hora. Eso deja una espera para entrar mínima de unos **34 s/veh** con cualquier control. En 2715
   no hay piso (piden 990 veh/h), pero una cola que llega a la entrada se vacía a solo 1202 − 990 = 212 veh/h.
   Aun así, el exceso de espera para entrar de IPPO en 2715 y en P2 **no es un artefacto de la
   inserción**: con los vehículos entrando a la velocidad máxima segura, la desventaja de IPPO frente al
   fijo se mantiene y crece (2715: +29.3 s/veh, IC95 [+19.7, +39.0]).
2. **Paso de simulación.** En SUMO el paso es el tiempo de reacción del conductor. Con 0.5 s la capacidad
   sube (descarga +9.5 %, inserción +12.5 %), los retrasos bajan entre 11 y 66 %, y **el orden entre el
   fijo, el actuado y el ciclo mínimo se invierte en 1358 y en P1**. Ahí las diferencias son menores que
   1 s, y la inversión es significativa. En 2715 el orden se mantiene. Diferencias del tamaño de la
   desventaja de IPPO en 1358 (+1 s, +5 %) quedan dentro de lo que este parámetro mueve.

En resumen, la curva no sale de un fallo de SUMO. Su forma en demanda baja depende de supuestos del modelo
(paso de 1 s, entrada detenida). Son los mismos para todos los brazos, así que la comparación interna es
válida. Lo que no se debe hacer es generalizar el signo de diferencias de ±5 % en 905-1810.

## 1. Opciones de SUMO de cada brazo (código)

Todos los brazos de la evaluación usan el mismo `.sumocfg` del escenario: `step-length 1`,
`time-to-teleport -1` (no hay teletransportes por bloqueo), `no-step-log` y `no-warnings`. A eso suman
`--seed`, `--tripinfo-output` con `--tripinfo-output.write-unfinished true`,
`--device.emissions.probability 1` y `--statistic-output` (`comun.args_estadisticas`).

- fijo, actuado y ciclo mínimo: `rl_corredor.correr_episodio` (rl_corredor.py:236-245). El actuado y el
  trivial agregan `--additional-files` con el `.add.xml` del escenario y `<esc>_actuado.add.xml` o
  `<esc>_trivial.add.xml`, y activan el programa con `setProgram`.
- IPPO: `rl_ippo.correr_episodio` (rl_ippo.py:453-455), con las mismas opciones.
- Fin de la corrida: no se pasa `--end`. El bucle de TraCI corta cuando la red se vacía o a los 6000 pasos
  (rl_corredor.py:291, rl_ippo.py:538). `barrer_fijo.py` y las corridas directas de este análisis usan
  `--end 6000`, el mismo tope.
- Choques: valores por defecto de SUMO 1.25 (`sumo --save-template`): `collision.action teleport`,
  `collision.check-junctions false`, `collision.mingap-factor -1`.
- Inserción: las rutas no fijan `departSpeed`, `departLane` ni `departPos`. Valen los defectos: velocidad 0,
  carril `first` y posición `base`.

## 2. Teletransportes, choques y bloqueos (2715 y P2, semillas 1001-1005)

Se corrieron los cuatro brazos por el mismo camino que `evaluar.py` (TraCI), en tres variantes:

- **base**: las opciones de la evaluación.
- **chk**: suma `--collision.check-junctions true --collision.action warn`. También cuenta los choques
  dentro de los cruces y no cambia la dinámica.
- **tt300**: suma `--time-to-teleport 300`, el valor por defecto de SUMO. Detecta vehículos detenidos
  300 s seguidos.

Medias por corrida:

| nivel | control | teletransp. base / tt300 | choques base / chk | frenadas de emergencia | esperan entrar al cerrar | sin terminar | espera para entrar (s/veh) | timeLoss | retraso total |
|---|---|---|---|---|---|---|---|---|---|
| 2715 | fijo | 0 / 0 | 0 / 0 | 0 | 0 | 0 | 3.77 | 50.59 | 54.36 |
| 2715 | actuado | 0 / 0 | 0 / 0 | 0 | 0 | 0 | 71.82 | 78.59 | 150.41 |
| 2715 | ciclo mín. | 0 / 0 | 0 / 1.0 | 0 | 0 | 0 | 291.34 | 196.19 | 487.53 |
| 2715 | IPPO s2042 | 0 / 0 | 0 / 0 | 0 | 0 | 0 | 16.84 | 57.25 | 74.09 |
| P2 | fijo | 0 / 0 | 0 / 0.6 | 0 | 0 | 0 | 238.61 | 153.85 | 392.46 |
| P2 | actuado | 0 / 0 | 0 / 0.2 | 0 | 0 | 0 | 317.96 | 120.81 | 438.77 |
| P2 | ciclo mín. | 0 / 0 | 0 / 2.0 | 0 | 230.4 | 131.0 | 654.90 | 281.10 | 1043.62 |
| P2 | IPPO s2042 | 0 / 0.4 | 0 / 0 | 0 | 0 | 0 | 280.47 | 118.38 | 398.85 |

- La variante base reproduce el CSV de la evaluación en 40 de 40 corridas (seis métricas iguales).
- La variante chk da registros `<tripinfo>` idénticos a la base (sha256) en 40 de 40. Los 0-5 choques por
  corrida dentro de los cruces, que solo aparecen en las referencias, no cambian ningún número.
- Con `time-to-teleport 300`, solo IPPO en P2, semilla 1005, tiene 2 teletransportes de tipo *yield* (un
  vehículo que espera más de 300 s un hueco en el tránsito con prioridad). El retraso total de IPPO en P2
  cambia en +0.07 % (timeLoss −0.03 %). Los demás brazos quedan idénticos.
- Los únicos vehículos sin terminar son los del ciclo mínimo en P2: 131 en la red y 230 fuera de ella al
  tope de 6000 s. Ya estaba registrado; `comun.leer_tripinfo` los cuenta con su espera hasta el cierre.

**Entrada a velocidad máxima (`salida`, `--default.departspeed max`, paso 1 s, mismas semillas).** Esta
variante separa lo que se debe a cómo inserta SUMO. IPPO puede probarse porque el paso sigue en 1 s. En
la tabla, "IPPO − fijo" es la diferencia pareada en s/veh, con IC95 t (4 gl):

| nivel | métrica | evaluación: fijo / IPPO | IPPO − fijo | entrada a vel. máx.: fijo / IPPO | IPPO − fijo |
|---|---|---|---|---|---|
| 2715 | espera para entrar | 3.77 / 16.84 | +13.07 [+4.34, +21.80] | 0.30 / 17.60 | +17.30 [+11.51, +23.09] |
| 2715 | retraso total | 54.36 / 74.09 | +19.73 [−1.59, +41.06] | 44.76 / 74.09 | +29.34 [+19.67, +39.01] |
| P2 | espera para entrar | 238.61 / 280.47 | +41.85 [+24.14, +59.56] | 233.01 / 280.20 | +47.19 [+34.92, +59.46] |
| P2 | timeLoss | 153.85 / 118.38 | −35.47 [−39.41, −31.53] | 151.62 / 123.70 | −27.92 [−33.09, −22.76] |
| P2 | retraso total | 392.46 / 398.85 | +6.39 [−14.24, +27.01] | 384.63 / 403.90 | +19.27 [+1.89, +36.64] |

Al facilitar la inserción, el fijo casi no deja vehículos esperando en 2715 (0.30 s/veh), pero IPPO sí
(17.6 s/veh). La política llena la entrada por sí misma. Esto respalda H2, la corrección INS.

## 3. Paso de simulación (fijo, actuado y ciclo mínimo; 1358, P1 y 2715; semillas 1001-1010)

Las corridas fueron con sumo directo (sin TraCI), con los `.sumocfg` y `.add.xml` de cada brazo y
`--end 6000`. Con paso de 1 s reproducen la evaluación con TraCI en 90 de 90 corridas. Con paso de 0.5 s
no hubo teletransportes.

| nivel | control | timeLoss 1 s | timeLoss 0.5 s | cambio | total 1 s | total 0.5 s | cambio | espera entrar 1 s / 0.5 s |
|---|---|---|---|---|---|---|---|---|
| 1358 | fijo | 18.21 | 16.07 | −11.8 % | 18.79 | 16.49 | −12.3 % | 0.58 / 0.41 |
| 1358 | actuado | 18.06 | 15.79 | −12.6 % | 18.64 | 16.20 | −13.1 % | 0.58 / 0.41 |
| 1358 | ciclo mín. | 18.74 | 15.78 | −15.8 % | 19.32 | 16.18 | −16.2 % | 0.58 / 0.41 |
| P1 | fijo | 21.15 | 17.89 | −15.4 % | 21.53 | 18.20 | −15.5 % | 0.37 / 0.31 |
| P1 | actuado | 20.91 | 18.57 | −11.2 % | 21.29 | 18.88 | −11.3 % | 0.37 / 0.31 |
| P1 | ciclo mín. | 105.17 | 50.32 | −52.2 % | 108.55 | 50.63 | −53.4 % | 3.38 / 0.31 |
| 2715 | fijo | 52.40 | 37.22 | −29.0 % | 55.38 | 37.67 | −32.0 % | 2.98 / 0.45 |
| 2715 | actuado | 80.79 | 49.36 | −38.9 % | 156.42 | 53.71 | −65.7 % | 75.63 / 4.35 |
| 2715 | ciclo mín. | 195.73 | 152.81 | −21.9 % | 485.38 | 333.67 | −31.3 % | 289.65 / 180.86 |

¿Se mantiene el orden? Diferencias pareadas de retraso total, en s/veh con IC95 t (9 gl):

- **1358, no se mantiene.** Con 1 s el orden es actuado < fijo < ciclo mínimo; con 0.5 s es ciclo mínimo ≈
  actuado < fijo.
  - fijo − ciclo mín.: −0.53 [−0.90, −0.16] con 1 s y +0.30 [+0.17, +0.44] con 0.5 s.
  - fijo − actuado: +0.15 [−0.15, +0.46] con 1 s y +0.29 [+0.04, +0.54] con 0.5 s.
- **P1, no se mantiene.** Con 1 s es actuado < fijo; con 0.5 s es fijo < actuado.
  - fijo − actuado: +0.24 [−0.15, +0.63] con 1 s y −0.68 [−0.99, −0.37] con 0.5 s.
  - El ciclo mínimo queda último en los dos, pero su desventaja baja de 87 a 32 s/veh.
- **2715, se mantiene** (fijo < actuado < ciclo mínimo), pero las distancias cambian mucho.
  - fijo − actuado: −101.0 [−116.4, −85.7] con 1 s y −16.0 [−19.9, −12.2] con 0.5 s.

Mecanismo, medido en la misma red (modo `insercion`, 3 semillas):

| | paso 1 s | paso 0.5 s |
|---|---|---|
| inserción en W_C1 libre, entrada detenida (la del corredor) | 1202 veh/h | 1352 veh/h |
| inserción en W_C1 libre, entrada a vel. máx. | 1508 veh/h | 1750 veh/h |
| descarga de una cola en verde (vehículos 5 a 30) | 1836 veh/h | 2010 veh/h |

Bajar el paso hace que los conductores reaccionen antes. La red gana capacidad, el costo de cada cambio de
fase baja y el ciclo corto pasa a convenir. No es una versión "más exacta" del mismo modelo, sino otro
conductor. La tesis usa 1 s, el valor por defecto de SUMO, en todo: entrenamiento, barridos y evaluación.

**IPPO no se prueba con 0.5 s.** `rl_ippo.py` y `rl_corredor.py` cuentan cada paso como 1 s: decisión
cada `PASO_CONTROL = 5` pasos, verde mínimo de 10 y máximo de 60 pasos, `t_verde += 1` y
`ambar_restante -= 1` por paso, y tope de 6000 pasos (rl_ippo.py:538-642, rl_corredor.py:114-117). Con
0.5 s, la política decidiría cada 2.5 s, con verdes de 5-30 s, y la corrida se cortaría a los 3000 s. Sería
otro controlador, entrenado para otro reloj.

## 4. Determinismo (IPPO en 1358, politica_dem_corredor_t1358_vecinos_s42.pt, semillas 1001-1003)

Dos repeticiones con `evaluar.brazo_profundo` y `random.seed(semilla)`, como `evaluar.main_v2`:

| semilla | retraso total rep. 1 / rep. 2 | sha256 de los registros `<tripinfo>` | igual al CSV de la evaluación |
|---|---|---|---|
| 1001 | 19.51 / 19.51 | 1678c1e02c8d3515 / 1678c1e02c8d3515 | sí |
| 1002 | 19.53 / 19.53 | 8fc6a0e5d809b221 / 8fc6a0e5d809b221 | sí |
| 1003 | 19.68 / 19.68 | 55ad662ca2dcc2bb / 55ad662ca2dcc2bb | sí |

Las dos repeticiones son idénticas vehículo a vehículo. El hash excluye la cabecera del archivo, que trae
la fecha y el nombre del archivo. Además coinciden con la evaluación de la tesis. Como dato adicional, las
120 corridas de la sección 2 reprodujeron la evaluación salvo la de tt300 con teletransportes, que cambia
por diseño.

## 5. Definiciones, en la documentación oficial y en el código de SUMO 1.25

Documentación de la versión instalada: fuente en `eclipse-sumo/sumo`, etiqueta `v1_25_0`, `docs/web/docs/`;
publicada en sumo.dlr.de/docs.

- **timeLoss se cuenta desde la inserción.**
  - TripInfo (https://sumo.dlr.de/docs/Simulation/Output/TripInfo.html) define `timeLoss` como "The time
    lost due to driving below the ideal speed. (ideal speed includes the individual speedFactor; slowdowns
    due to intersections etc. will incur timeLoss, scheduled stops do not count)", y `depart` como "The
    real departure time (the time the vehicle was inserted into the network)". La página no lo dice con
    todas las letras.
  - El código sí lo dice. `MSVehicle::updateTimeLoss` (src/microsim/MSVehicle.cpp:4209-4216, llamada desde
    `executeMove`, línea 4682) suma `TS * (vmax - vNext) / vmax` con la velocidad máxima del carril en el
    que está el vehículo. Solo corre para un vehículo que ya está en la red. MSDevice_Tripinfo.cpp:303
    escribe ese valor.
  - Comprobado en un tripinfo (modo `definiciones`, fijo de P2, semilla 1001): 1560 vehículos esperaron
    ≥ 60 s para entrar, en promedio 543.1 s, y su timeLoss medio es 253.9 s. Su duración − timeLoss vale
    79.8 s (frente a 64.3 s del resto), es decir, el tiempo a flujo libre de la ruta. Si timeLoss incluyera
    la espera, esa resta sería negativa. Además, `duration = arrival − depart` en todos los vehículos.
- **departDelay es la espera para entrar.**
  - TripInfo: "The time the vehicle had to wait before it could start his journey".
  - Código: `MSBaseVehicle::getDepartDelay` (src/microsim/MSBaseVehicle.cpp:940-945) devuelve
    `getDeparture() - dep` si salió y `SIMSTEP - dep` si sigue esperando. MSDevice_Tripinfo.cpp:341-346
    usa lo mismo para los que no salieron.
  - StatisticOutput (https://sumo.dlr.de/docs/Simulation/Output/StatisticOutput.html): `departDelayWaiting`
    es "The average waiting time of vehicles which could not be inserted due to lack of road space".
  - La misma página, en "Fair Traveltime comparison between simulations", recomienda sumar "the travel
    time (duration) and the time that was spent waiting for departure (departDelay) for all vehicles that
    were defined in the input" e incluir a los que no entraron con
    `vehicles.waiting * vehicleTripStatistics.departDelayWaiting`. Es la construcción del retraso total de
    `comun.leer_tripinfo`, con timeLoss en vez de duration. Recalculado con los promedios del
    `--statistic-output`, da lo mismo: 388.62 s/veh en P2 y 45.07 en 2715, semilla 1001.
- **Inserción con la arista de entrada llena.** Fuente:
  https://sumo.dlr.de/docs/Simulation/VehicleInsertion.html.
  - Condiciones: "The vehicle (from its rear to its front position + *minGap*) must not intersect with
    other vehicles", y además distancia segura al líder y al seguidor. "If a vehicle cannot be inserted due
    to any of the above reasons its insertion is delayed".
  - "If there is insufficient space for inserting the vehicle at its designated departure time, that
    vehicle is put into an insertion queue and insertion is repeatedly attempted in subsequent simulation
    steps." Con `max-depart-delay -1`, el valor por defecto, nunca se descarta.
  - Por defecto, cuando un vehículo no entra, se dejan de intentar los siguientes de esa arista en ese paso
    (variante 2, `--eager-insert` la cambia).
  - La posición por defecto es `departPos="base"`: "the vehicle is tried to be inserted at the position
    which lets its back be at the beginning of the lane". El vehículo espera hasta que haya hueco al inicio
    de la arista, es decir, hasta que la cola de la entrada se aleje del borde.
  - Definition_of_Vehicles, Vehicle Types, and Routes
    (https://sumo.dlr.de/docs/Definition_of_Vehicles,_Vehicle_Types,_and_Routes.html) da los defectos:
    `departSpeed` "*default: 0*" y `departLane` "*default: "first"*".
- **Efecto del paso en la inserción.** VehicleInsertion, "Effect of simulation step-length": "Insertion
  attempts can only happen in every simulation step. This may cause artifacts in insertion spacing because
  at the default step-length of 1s is (usually) too short for vehicles to be inserted in successive steps
  on the same depart location. By default, the next attempt happens 2 seconds after the first vehicle has
  departed and this gap may be much larger then mandated by the carFollowModel." Medido aquí: 3.0 s entre
  inserciones, 1202 veh/h.
- **Paso y reacción.** Car-Following-Models (https://sumo.dlr.de/docs/Car-Following-Models.html): "By
  default, drivers may react to their surroundings in every simulation step ... Thus, their time to react,
  is equal to the value set by sumo-option **--step-length** (default 1s)."
- **Teletransportes.** Why Vehicles are teleporting
  (https://sumo.dlr.de/docs/Simulation/Why_Vehicles_are_teleporting.html) dice "Setting
  **--time-to-teleport** to a negative value disables teleporting due to gridlock". El tipo *yield* es "The
  vehicle is stuck on a low-priority road and did not find a gap in the prioritized traffic".
- **Choques.** Safety (https://sumo.dlr.de/docs/Simulation/Safety.html): por defecto se registra un choque
  cuando el hueco baja de *minGap* en una misma arista. "When setting the option
  **--collision.check-junctions**, collisions between vehicles on the same intersection are also checked by
  detecting overlap of the vehicles shapes". La acción por defecto es **teleport**.

## Qué significa para el diagnóstico

- H1-H4 no cambian. Los cuatro brazos comparten opciones y defectos de SUMO, y la comparación de la tesis es
  interna al mismo modelo.
- **2715 y P2 (H2):** la espera para entrar de IPPO es real. Aparece igual o mayor cuando la inserción deja
  de ser un cuello de botella. El piso de unos 34 s/veh en P2 viene de la inserción y lo comparten todos los
  controles. Achica las diferencias relativas en retraso total, pero no las crea.
- **1358 y P1 (H3):** el resultado vale para el conductor de SUMO con reacción de 1 s. Con reacción de
  0.5 s, el orden entre las referencias se invierte, con diferencias del orden de 0.3-0.8 s/veh. Conviene
  decirlo en la tesis como límite del alcance: en demanda baja, diferencias de ±5 % entre controles
  dependen de este parámetro.
- No propongo cambiar el paso ni la inserción de la evaluación. Todo lo entrenado y barrido es con 1 s y
  entrada detenida, y cambiarlo exigiría re-entrenar y re-barrer.

## Cómo reproducir

Desde `plan2/`, con `python diag_corredor/sumo_chequeos.py <modo>`, en este orden: `paso --procesos 12`,
`teletransportes --procesos 8`, `salida --procesos 8`, `determinismo`, `insercion`, `definiciones` y
`resumen`. No corras `paso` a la vez que `teletransportes` o `salida`, porque esos dos reescriben
`<esc>_actuado.add.xml` y `<esc>_trivial.add.xml` (con el mismo contenido) y en Windows chocan. En total
son unos 30 min con 8 a 12 procesos.
