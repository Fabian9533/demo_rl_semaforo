# Precisión de los resultados: ¿qué tan preciso es un valor como −23.3 %?

**BORRADOR PARA REVISIÓN.** No va a la tesis. Es para poder responder esa pregunta en la defensa.

Escrito el 22.10.2026 con los archivos de `plan2/`, las tablas generadas de `TESIS/secciones/tablas/`, la
documentación de SUMO y una comprobación corrida ese día (punto 3). Los nombres son los de la tesis: IPPO
con mensajes (`ippo_vecinos` en los CSV), IPPO sin mensajes (`ippo_local`), fijo ajustado (`fijo_2509`) y
ciclo mínimo (`trivial`).

## Respuesta corta

El −23.3 % de P2 es (118.66 − 154.70) / 154.70 × 100: el retraso medio de IPPO con mensajes frente al del
fijo ajustado, sobre las mismas 30 semillas de evaluación (Tabla 5.3, `tab:resultado-principal`; la Tabla
5.2 es ahora la regla de veredicto). El error de cálculo (la doble
precisión de Python y los redondeos de SUMO y del script) mueve ese valor menos de 0.02 puntos aun en el
peor caso, así que no cambia el decimal publicado. Lo que sí lo mueve es la variación entre semillas, es
decir, entre conductores: el intervalo de confianza al 95 % va de −23.9 a −22.7 %. También lo mueve el
entrenamiento: los otros dos entrenamientos de IPPO con mensajes dan −23.9 y −23.1 %. No está medido
cuánto cambiaría con un paso de simulación menor que 1 s ni con llegadas aleatorias.

## 1. Error de representación y de redondeo

**Cómo se calcula el número.** Para cada semilla, `comun.leer_tripinfo` promedia el atributo `timeLoss`
de todos los vehículos del tripinfo (3620 por semilla en P2) y redondea la media a 2 decimales (columna
`timeloss_prom`). Después, la función `comparar` de `consolidar.py` calcula

    Δ = (media del modelo − media de la referencia) / media de la referencia × 100

sobre las 30 semillas emparejadas y lo guarda con 2 decimales; la tabla lo muestra con uno (Ecuación
`eq:delta` de capitulo3.tex; ajuste A11; la función `comparar` de `evaluar.py` usa la misma fórmula). En
P2 las medias son 154.7013 y 118.6587 s/veh (`plan2/evaluacion_corredor_alta_resumen_fijo_2509.csv`) y
Δ = −23.298 %, que se publica como −23.3 %.

**Doble precisión.** Python y numpy guardan cada número en float64 (doble precisión): guardar un número o
hacer una operación tiene un error relativo de a lo más 2^-53 ≈ 1.1 × 10^-16. Medido en P2: el Δ
calculado en float64 y el calculado con fracciones exactas, a partir de los mismos 60 valores del CSV,
difieren en 8 × 10^-15 puntos. No se ve.

**Decimales que escribe SUMO.** SUMO escribe los números con los decimales que fija la opción
`--precision`, que por defecto es 2 (punto 2). El plan no la cambia: no está en el comando que arma
`rl_corredor.correr_episodio` ni en los `.sumocfg` de `plan2/`. Cada `timeLoss` llega entonces con 2
decimales, con un error de a lo más ±0.005 s por vehículo. Más decimales no hay: aunque se le pidan 6,
SUMO escribe el `timeLoss` con 3, es decir, con resolución de 1 ms (punto 3).

**Cuánto puede mover el redondeo la media y el cambio de P2.** Cada media por semilla junta dos
redondeos: el de SUMO (±0.005 s/veh en el peor caso, si todos los vehículos se redondean hacia el mismo
lado) y el `round(·, 2)` del script (±0.005 s/veh). La media de las 30 semillas hereda a lo más ±0.01
s/veh. Con la fórmula de arriba y los números de la Tabla 5.3 (R = 154.70 s/veh del fijo y M = 118.66
s/veh del modelo):

    |δΔ| ≤ (100 / R) · 0.01 + (100 · M / R²) · 0.01 = 0.0065 + 0.0050 = 0.011 puntos

Δ queda entre −23.310 y −23.287 %; con un decimal sigue siendo −23.3 %. El redondeo final a un decimal
es, por definición, de ±0.05 puntos, y es una decisión de presentación, no un error del cálculo.

La cota crece cuando el retraso es chico. En P1 (R = 21.30 y M = 19.84 s/veh) es de ±0.09 puntos sobre
−6.816 %, de modo que en el peor caso el decimal publicado podría pasar a −6.9 o a −6.7 %. Es una cota muy
pesimista: lo medido en el punto 3 es unas diez veces menor por vehículo.

**Sesgo del redondeo de SUMO.** Al escribir con 2 decimales, SUMO redondea hacia arriba las milésimas
que terminan en 5 (punto 3), y por eso cada media por semilla sale unos 0.0005 s/veh más alta. El sesgo
viene de cómo SUMO escribe los números, no del control, así que debería ser casi el mismo en todos los
controles (solo se midió en el fijo). En Δ casi se cancela: lo cambiaría en unos Δ · 0.0005 / R, es
decir, 0.0001 puntos en P2.

## 2. Lo que dice la documentación de SUMO

Consultada el 22.10.2026. La documentación en línea es la de la versión actual de SUMO; el plan corrió
con SUMO 1.25.0, que es la instalada (`C:\Program Files (x86)\Eclipse\Sumo`).

- **timeLoss** (https://sumo.dlr.de/docs/Simulation/Output/TripInfo.html, tabla de atributos de
  `tripinfo`; página editada el 12.10.2026): "The time lost due to driving below the ideal speed. (ideal
  speed includes the individual speedFactor; slowdowns due to intersections etc. will incur timeLoss,
  scheduled stops do not count)".
- **Decimales** (https://sumo.dlr.de/docs/sumo.html, opciones de salida; editada el 13.10.2026):
  "--precision <INT> Defines the number of digits after the comma for floating point output; default:
  2". La ayuda del binario instalado (`sumo --save-template`) da el mismo valor por defecto, 2.
- **Misma semilla, mismo resultado** (https://sumo.dlr.de/docs/Simulation/Randomness.html; editada el
  08.10.2026). En "Random number generation (RNG)": "This random number generator (RNG) is initialized
  with a seed value which defaults to the (arbitrary) value 23423. This setup makes all applications
  deterministic by default as the sequence of random numbers is fixed for a given seed." En
  "Reproducibility": "Generally, all SUMO applications and tools are expected to produce the same results
  when running the same version repeatedly with the same arguments and inputs. This also includes running
  on different platforms (Windows/Linux/Mac)." Las excepciones que lista la página son la opción
  `--random`, la conversión de coordenadas geográficas con la biblioteca Proj y la función log en el
  modelo EIDM y en el dispositivo DriverState. Ninguna aplica al plan: se pasa `--seed`, las tres redes
  no tienen proyección geográfica (`projParameter="!"` en `corredor.net.xml`, `red.net.xml` y
  `malla3.net.xml`, que usan también los casos con demanda alta) y el tipo de vehículo usa el modelo de
  seguimiento por defecto, Krauss.
- **"Suma cerca de 1 s por segundo detenido y cerca de 0.5 s a media velocidad"** (lo que se dijo en la
  reunión). La documentación no da esa regla; solo da la definición de arriba. La regla sale de esa
  definición si el tiempo perdido se entiende como el tiempo real menos el que tardaría el vehículo en
  hacer el mismo recorrido a su velocidad ideal: en cada segundo se suma 1 − v / v_ideal, que vale 1 con
  el vehículo detenido y 0.5 a la mitad de la velocidad ideal. Se comprobó con la corrida de más
  decimales del punto 3: en los 1570 vehículos que siguen recto en cada semilla, el `timeLoss` coincide
  con duración − largo del recorrido / v_ideal dentro de un paso de simulación (diferencias entre −0.98 y
  +0.01 s), tomando v_ideal = mín(13.89, factor de velocidad × 13.89) m/s. En los 240 que giran la
  diferencia es mayor (entre −0.4 y −2.1 s), porque en la curva del cruce la velocidad permitida baja a
  6.51 u 8.00 m/s y la ideal baja con ella. La regla es coherente con la definición y con los datos;
  para darla como un hecho habría que verla en el código de SUMO, y eso no se hizo. La recompensa de la
  tesis usa la misma idea (capitulo3.tex: "un vehículo detenido cuenta 1 y uno que avanza a media
  velocidad cuenta 0.5").

## 3. Comprobación empírica: el fijo de P1, dos veces y con más decimales

**Qué se corrió.** El brazo fijo de P1 con las semillas 1001 a 1003 y la misma llamada que usa el plan,
`evaluar.py --escenario corredor --brazo fijo --semillas 1001-1003`, desde carpetas temporales fuera del
repositorio, con copias de `plan2/corredor.sumocfg`, `corredor.net.xml`, `corredor.rou.xml` y
`corredor.add.xml` (el mismo SHA-1 que los originales). Las corridas A y B son iguales entre sí; la C es
igual pero con `--precision 6`. Un script pequeño que llama a evaluar.py solo cambió dos cosas: que no se
borrara el tripinfo de las semillas 1002 y 1003 (evaluar.py borra todos menos el de la primera semilla)
y, en C, que se agregara esa opción. El comando de SUMO para la semilla 1001 fue:

```text
sumo.exe -c corredor.sumocfg --seed 1001 --tripinfo-output tripinfo_eval_corredor_fijo_<pid>.xml
  --tripinfo-output.write-unfinished true --device.emissions.probability 1
  --statistic-output tripinfo_eval_corredor_fijo_<pid>_stats.xml          (en C, más --precision 6)
```

SUMO 1.25.0, Windows 10, 22.10.2026. No se escribió ningún archivo del repositorio.

**Resultados.**

| | Semilla 1001 | 1002 | 1003 |
|---|---|---|---|
| `timeloss_prom` del CSV (igual en A, B, C y `plan2/evaluacion_corredor.csv`) | 21.05 | 21.50 | 20.69 |
| Media sin redondear, `timeLoss` con 2 decimales (A) | 21.049475 | 21.497022 | 20.693155 |
| Media sin redondear, `timeLoss` con 3 decimales (C) | 21.049052 | 21.496575 | 20.692549 |
| Efecto de los 2 decimales de SUMO (A − C), s/veh | +0.00042 | +0.00045 | +0.00061 |
| Efecto del `round(·, 2)` del script (CSV − A), s/veh | +0.00053 | +0.00298 | −0.00316 |
| Los dos redondeos juntos (CSV − C), s/veh | +0.00095 | +0.00343 | −0.00255 |

- **A y B son idénticas**: el CSV byte a byte, los tres tripinfo (5433 líneas cada uno, sin contar el
  comentario de cabecera, que lleva la fecha y el nombre del archivo) y los archivos de vehículos, de
  serie y de fases. Los archivos de estadísticas solo difieren en los nombres de archivo, el puerto de
  TraCI y el tiempo de reloj.
- **A coincide con lo guardado**: las 30 columnas de `plan2/evaluacion_corredor.csv` (brazo `fijo`,
  semillas 1001 a 1003) sin ninguna diferencia. En P1 y P2 el brazo `fijo` es el mismo programa que el
  fijo ajustado: `fijo_2509` coincide con él semilla a semilla.
- **Con más decimales**, el valor por semilla del CSV no cambia. Por vehículo, la diferencia llega como
  máximo a 0.005 s. La media de las tres semillas pasa de 21.0799 a 21.0794 s/veh (−0.0005).
- Con `--precision 6`, SUMO escribe el `timeLoss`, la duración y la espera para entrar con 3 decimales,
  y el largo del recorrido o el factor de velocidad con 6: los tiempos salen con resolución de 1 ms. Al
  escribir con 2 decimales, las 513 milésimas terminadas en 5 se redondearon hacia arriba y las demás al
  valor más cercano; de ahí el +0.0005 s/veh.
- El propio SUMO escribe en el archivo de estadísticas la media de `timeLoss` de cada semilla (21.049,
  21.496 y 20.692 en C): coincide con la de Python truncada al milisegundo.

**Otras pruebas de que el cálculo se repite igual, que ya estaban en el repositorio.**

- `prueba_det_a.csv` y `prueba_det_b.csv` (06.09): dos entrenamientos de IPPO con mensajes de 3
  episodios, idénticos salvo la columna `segundos`, que es tiempo de reloj (CLAUDE.md: "Determinismo
  verificado").
- En P3, P4 y P5, las 9 políticas de IPPO con penalización de spillback dan en la evaluación, semilla a
  semilla, lo mismo que las de IPPO con mensajes con la misma base en las 30 columnas de métricas,
  incluidas `ret_spill` y `recompensa`, porque la penalización nunca se activa
  (`plan2/evaluacion_{red,red_alta,malla3}.csv`, brazos `ippo_spill_s<base>` frente a
  `ippo_vecinos_s<base>`; comprobado otra vez el 23.10; Anexo A: "Las nueve políticas dan, semilla a
  semilla, el mismo timeLoss"). Son entrenamientos corridos por separado que llegan al mismo resultado.
- El fijo de P1 y de P2 evaluado el 25.09 (commit 37f9680) y vuelto a evaluar después (el CSV actual ya
  tiene `retraso_total_prom`, que el 25.09 no existía) coincide en las 27 métricas comunes y en las 30
  semillas (comprobado otra vez el 22.10).

## 4. Fuentes de variación por unidad

Las cifras son de P2 salvo que se diga otra cosa. Las unidades son las de la introducción de la tesis:
U1 preprocesamiento (red y demanda), U2 aprendizaje por refuerzo, U3 simulación y medición, U4
coordinación distribuida.

**U1, preprocesamiento.**

- Demanda: las llegadas son a intervalos regulares, y la semilla no cambia cuántos vehículos llegan ni
  cuándo (capitulo3.tex, `sec:escenarios` y `sec:estadistica`). La demanda no agrega variación entre
  corridas, pero los intervalos de confianza son condicionales a ella y subestiman la variación de un
  tráfico real. Con llegadas aleatorias no se midió: pregunta abierta.
- Ajuste del fijo (barrido con las semillas 2001 a 2003): no es ruido, es la elección de la referencia.
  En P1 y P2 la medición más estricta usa el mismo fijo; en P3 y P4, un barrido que parte de 10 s da un
  fijo con 8.35 y 6.06 % menos retraso (`plan2/evaluacion_red_resumen_fijo_2509.csv` y
  `plan2/evaluacion_red_alta_resumen_fijo_2509.csv`, brazo `fijo` frente a `fijo_2509`).

**U2, aprendizaje.**

- Semilla del entrenamiento (3 entrenamientos por modelo, `TESIS/secciones/tablas/veredicto_bases.tex`).
  IPPO con mensajes en P2: −23.9, −23.3 (la versión evaluada, del entrenamiento mediano por validación) y
  −23.1 %. En otros casos la diferencia es mayor: en P3, de −8.8 a −0.1 %; en P6, de 37.54 a 41.51 s/veh,
  es decir, de +2.2 a +13.0 %.
- La política congelada no agrega variación en la evaluación: fuera del entrenamiento elige siempre la
  acción más probable (`acciones = logits.argmax(dim=1)` en `rl_ippo.correr_episodio`), así que con la
  misma semilla da lo mismo.

**U3, simulación y medición.**

- Semillas de evaluación (cambian a los conductores: su factor de velocidad y la imperfección σ del
  modelo de seguimiento). Fijo ajustado: 154.70 ± 1.06 s/veh (Tabla A.1, semiamplitud del IC95). IPPO con
  mensajes: 118.66 ± 0.67 s/veh (`plan2/veredicto.csv`). Δ: IC95 de −23.9 a −22.7 % (bootstrap pareado por
  semilla, 10 000 remuestreos).
- El remuestreo del bootstrap usa una semilla fija (0), así que el intervalo se repite igual.
  Recalculado con 50 semillas de remuestreo distintas, sus extremos van de −23.93 a −23.90 % y de −22.69
  a −22.65 %: se mueven unas centésimas.
- Redondeos y doble precisión: puntos 1 y 3.
- Paso de simulación de 1 s (`step-length 1` en los `.sumocfg`): no se midió qué pasa con un paso menor;
  es una pregunta abierta. Probarlo no es solo cambiar `--step-length`: `rl_corredor.py` y `rl_ippo.py`
  cuentan los pasos como segundos (5 pasos entre decisiones, el verde de 10 a 60 pasos, el tope de 6000
  pasos y `comun.FIN_HORA` = 3600), y habría que adaptarlos.

**U4, coordinación distribuida.**

- En la evaluación del plan los mensajes son instantáneos y sin pérdida (clase `Canal` de `rl_ippo.py`
  con latencia 0 y pérdida 0): no agregan variación.
- Un canal imperfecto solo se probó en la fase exploratoria (Anexo C; corredor, 10 semillas, otra
  versión de la política y el fijo de esa fase). Frente a ese fijo, la política pasó de −6.2 % sin
  latencia a +0.6 % con 5 s de latencia, +4.2 % con 5 s y 30 % de pérdida y +5.8 % con 10 s
  (`evaluacion_corredor_resumen.csv` de la raíz del repositorio). Eso dice cuánto sirve el modelo con un
  canal real, no qué tan preciso es el −23.3 %.
- **Opinión del equipo, a revisar: "U4 aporta más error que U2".** El dato que la pone a prueba es
  cuánto cambia el resultado entre los 3 entrenamientos de IPPO con mensajes y de IPPO sin mensajes, que
  tienen la misma red neuronal y la misma recompensa y solo difieren en los mensajes. Columna "rango
  entre bases" de `veredicto_bases.tex`, en s/veh:

  | | P1 | P2 | P3 | P4 | P5 | P6 |
  |---|---|---|---|---|---|---|
  | IPPO con mensajes | 0.23 | 1.28 | 1.88 | 0.80 | 0.39 | 3.97 |
  | IPPO sin mensajes | 0.33 | 2.69 | 1.40 | 1.20 | 1.97 | 1.02 |

  Con mensajes el rango es menor en P1, P2, P4 y P5 y mayor en P3 y P6. Con tres entrenamientos por
  modelo eso no alcanza para sostener ni para descartar la opinión (la tesis ya dice que tres bases
  detectan la fragilidad pero no la caracterizan). Para decidirlo habría que entrenar más bases de los
  dos modelos en algunos casos, por ejemplo P3 y P6, y comparar la dispersión.

## 5. "Si una red neuronal tiene precisión 0.9, equivale a 10 % de error"

La idea de la reunión era sumar de forma aproximada el error de cada etapa y tomar la precisión de una
red neuronal (por ejemplo 0.9) como cerca de 10 % de error en esa etapa.

En esta tesis no aplica (ajuste A9). Las redes de la tesis son políticas de aprendizaje por refuerzo: en
cada decisión eligen mantener la fase o pasar a la siguiente, y no hay una respuesta correcta con la que
compararlas, así que no tienen una métrica de precisión. Además, en un clasificador hay que distinguir dos
medidas: si 0.9 es la exactitud (accuracy), se equivoca en 1 de cada 10 casos; si es la precisión
(verdaderos positivos entre todos los positivos predichos), se equivoca en 1 de cada 10 predicciones
positivas. En ninguno de los dos casos quiere decir que el resultado final tenga un error de ±10 %. Lo
comparable que sí se mide es la variación entre los 3 entrenamientos (punto 4, U2).

## 6. Conclusión en orden de magnitud

Para P2:

| Fuente | Cuánto mueve el −23.3 % | Orden de magnitud (puntos) |
|---|---|---|
| Doble precisión (float64) | 8 × 10^-15 puntos (medido) | 10^-14 |
| Sesgo del redondeo de SUMO (debería ser casi igual en todos los controles) | unos 0.0001 puntos | 10^-4 |
| Redondeos de SUMO y del script, en el peor caso | hasta 0.011 puntos | 10^-2 |
| Remuestreo del bootstrap (solo los extremos del intervalo) | unas centésimas | 10^-2 |
| Semillas de evaluación (IC95) | de −23.9 a −22.7 % (±0.6) | 10^-1 a 10^0 |
| Entrenamiento (los otros dos entrenamientos) | −23.9 y −23.1 % | 10^0 |
| Paso de 1 s y llegadas aleatorias | no medido | ? |

En los seis casos (IPPO con mensajes frente al fijo ajustado):

| Caso | Δ (%) | Cota del redondeo, peor caso (puntos) | IC95 de Δ (semiamplitud) | Los 3 entrenamientos (rango en puntos) |
|---|---|---|---|---|
| P1 | −6.8 | 0.09 | −8.0 a −5.8 (1.1) | −6.8, −5.8, −5.7 (1.1) |
| P2 | −23.3 | 0.01 | −23.9 a −22.7 (0.6) | −23.9, −23.3, −23.1 (0.8) |
| P3 | −8.8 | 0.09 | −9.3 a −8.2 (0.5) | −8.8, −7.8, −0.1 (8.7) |
| P4 | −3.6 | 0.07 | −5.0 a −2.3 (1.4) | −4.6, −3.6, −1.9 (2.7) |
| P5 | +1.8 | 0.10 | +0.4 a +3.4 (1.5) | −0.1, +1.1, +1.8 (1.9) |
| P6 | +2.2 | 0.06 | −1.4 a +6.2 (3.8) | +2.2, +9.6, +13.0 (10.8) |

Fuente: medias de `plan2/evaluacion_<escenario>_resumen_fijo_2509.csv` (brazo `fijo_2509` y las tres
bases de `ippo_vecinos`, columnas `media` y `delta_pct`) y `plan2/veredicto.csv` (columna `ic_fijo`). La
cota sale de la fórmula del punto 1 con ±0.01 s/veh en cada media. En P6 el veredicto es pendiente
(empate provisional).

**Conclusión.** El error numérico es mínimo. Aun en el peor caso, en P2 es unas 50 veces menor que la
mitad del intervalo de confianza (0.011 frente a 0.6 puntos), y en ningún caso pasa de una quinta parte
de esa mitad (el margen más chico es el de P3: 0.09 frente a 0.5); el de la doble precisión ni se ve. La
precisión del −23.3 % la ponen las semillas de evaluación (±0.6 puntos) y el entrenamiento (−23.9 y −23.1
% con los otros dos). En P3 y P6 el entrenamiento pesa mucho más que las semillas. Quedan abiertos el
paso de 1 s y las llegadas aleatorias.

Una salvedad que no es de precisión: la cifra depende de qué se mide. Con la medición más estricta del
análisis de robustez (el retraso total, que suma la espera para entrar a la red), P2 pasa a +1.6 % frente
al fijo, con intervalo de +0.6 a +2.6 % (`plan2/robustez_veredicto.csv`). No es un error de cálculo: es
otra métrica.

## Preguntas abiertas

1. Sensibilidad al paso de simulación de 1 s: no medida. Antes de correrla hay que adaptar los
   contadores de pasos de `rl_corredor.py` y `rl_ippo.py`.
2. Llegadas aleatorias: los intervalos son condicionales a la demanda declarada; con llegadas aleatorias
   no se midió.
3. Cuántos entrenamientos harían falta para caracterizar la variación entre entrenamientos (con 3 solo
   se detecta) y, con eso, poner a prueba la opinión sobre U4.
4. Cómo acumula SUMO el `timeLoss` por dentro: solo se vio que lo escribe con resolución de 1 ms.
5. La regla de 1 − v / v_ideal por segundo: es coherente con la definición y con la prueba del punto 2,
   pero no está verificada en el código de SUMO.

## Cómo repetir la comprobación del punto 3

1. Crear una carpeta fuera del repositorio y copiar en ella `plan2/corredor.sumocfg`,
   `corredor.net.xml`, `corredor.rou.xml` y `corredor.add.xml`.
2. Desde esa carpeta, correr una semilla por llamada, porque evaluar.py conserva solo el tripinfo de la
   primera semilla de cada llamada:
   `python -B <repositorio>/evaluar.py --escenario corredor --brazo fijo --semillas 1001 --salida eval_1001.csv`,
   y lo mismo con 1002 y 1003. La opción `-B` evita que Python escriba `__pycache__` en el repositorio.
3. Repetir en una segunda carpeta y comparar los CSV y los tripinfo sin el comentario de cabecera.
4. Para más decimales, agregar `<output><precision value="6"/></output>` a la copia del `.sumocfg`. Da lo
   mismo que pasar `--precision 6`: se comprobó con la semilla 1001 (tripinfo idéntico al de la corrida C).
