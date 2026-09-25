# Propuestas para las zonas protegidas (plan de pruebas v2)

Etapa W2 (version final), 25.09.2026, para la reunion del 25.09.2026 a las 8:00. `resumen.tex`,
`abstract.tex`, `introduccion.tex` y `capitulo1.tex` son zonas protegidas: **no se editan sin la
confirmacion de Fabian Alvarado y Neftali Calixto**. Este archivo trae, para cada uno, el parrafo
actual (copiado literal del .tex; comprobado el 25.09 que sigue igual) y el parrafo nuevo
propuesto, listo para pegar en LaTeX. Nada de esto esta aplicado todavia.

Fuentes de todos los numeros: `plan2/veredicto.csv` y `plan2/veredicto.md` (generados por
`veredicto.py`, resultados congelados el 25.09.2026 a las 03:55; copia en
`plan2/veredicto_congelado_0355.csv` y `.md`), `plan2/evaluacion_<esc>_resumen.csv` (semillas
1001-1030), `plan2/barrido_<esc>.csv` y la cabecera de `plan2/red_alta.rou.xml`. Son los mismos
que citan `conclusiones.tex` (conclusiones 1 a 6) y `recomendaciones.tex`.

Estado al congelar (W2): P1-P5 evaluados para fijo, actuado, Q-learning, SARSA, DQN, IPPO (local,
vecinos, spill) y MAPPO; la ablacion `ql_colas` en P1-P4 (en P5 no se corrio). Seis de las 40
celdas de aprendices quedan PENDIENTE: `ql_colas` P5 sin datos, y Q-learning P4, `ql_colas` P2, DQN
P5 y MAPPO P3 y P4 porque la politica publicada no convergio. IPPO spill en P3, P4 y P5 figura como
"= vecinos" (el termino nunca se activa). La cola sigue corriendo confirmaciones de IPPO spill; no
cambian ninguna cifra de estas propuestas.

Retraso de la politica publicada, delta frente al fijo tuneado de cada caso (IC95 % bootstrap
pareado, 30 semillas) y veredicto:

| Caso | Fijo (s/veh) | Actuado | Q-learning | SARSA | Q-learning (colas) | DQN | IPPO local | IPPO vecinos | MAPPO |
|---|---|---|---|---|---|---|---|---|---|
| P1 corredor | 21.30 | -1.1 % EMPATA | +9.2 % FALLA | +14.0 % FALLA | +10.6 % FALLA | -3.5 % MEJORA | -0.5 % EMPATA | -6.8 % FUNCIONA | -7.1 % FUNCIONA |
| P2 corredor_alta | 154.70 | -19.8 % FUNCIONA | -8.8 % MEJORA | +6.6 % FALLA | +6.8 % pend. (prov. FALLA) | -19.4 % FUNCIONA | -22.8 % FUNCIONA | -23.3 % FUNCIONA | -21.6 % FUNCIONA |
| P3 red | 21.72 | -1.1 % MEJORA | +12.4 % FALLA | +11.2 % FALLA | +9.6 % FALLA | -1.8 % MEJORA | +2.3 % FALLA | -8.8 % FUNCIONA | -7.8 % pend. (prov. FUNCIONA) |
| P4 red_alta (1.2x) | 30.05 | -0.1 % EMPATA | +9.9 % pend. (prov. FALLA) | +10.4 % FALLA | +9.8 % FALLA | -3.4 % MEJORA | +2.9 % FALLA | -3.6 % MEJORA | -2.0 % pend. (prov. MEJORA) |
| P5 malla3 | 20.84 | +21.8 % FALLA | +42.5 % FALLA | +40.0 % FALLA | sin datos | +11.1 % pend. (prov. FALLA) | +25.9 % FALLA | +1.8 % EMPATA | -0.3 % EMPATA |

IPPO spill: P1 -5.2 %, P2 -22.7 % (FUNCIONA); en P3, P4 y P5 "= vecinos" (cola maxima de un carril de
enlace en los entrenamientos: 9, 12 y 8 vehiculos, frente a 19 de 38 y 18 de 37 plazas). IPPO
vecinos frente al actuado: -5.8 / -4.4 / -7.8 / -3.6 / -16.4 % (P1 a P5). Metas secundarias con
IPPO vecinos: colas -9.1 / -5.0 / -41.3 / -16.6 / -29.0 %; CO2 -1.6 / -12.3 / +1.9 / -0.5 / +5.2 %;
throughput -0.1 / +0.2 / +0.0 / +0.2 / -0.0 % (P1 a P5).

## 1. resumen.tex

### Parrafo 2 (pipeline, casos, modelos y regla de veredicto)

`resumen.tex`, lineas 5 (al 24.09.2026).

**Actual:**

```latex
La solución consiste en un \textit{pipeline} reproducible con cuatro unidades: (U1) datos y preprocesamiento; (U2) agentes de \textbf{RL} (un agente por intersección); (U3) simulación y medición en SUMO; y (U4) \textbf{coordinación distribuida entre semáforos}. En U4, cada agente comparte mensajes ligeros con sus \textit{vecinos} (fase actual, tiempo en ella, descarga hacia el vecino y colas en el enlace compartido) para \textbf{coordinar ondas verdes} y \textbf{evitar spillback}. En esta fase se implementaron las cuatro unidades y se validaron sobre \textbf{cinco escenarios sintéticos} construidos con \texttt{netconvert}: un cruce de dos fases, un cruce con giros protegidos, un corredor de dos cruces, una red de tres cruces con rotonda y el mismo corredor con el doble de demanda. Se implementan y comparan \textbf{Q-learning} tabular, con un agente independiente por intersección, e \textbf{IPPO} multiagente con un actor y un crítico compartidos, este último con \textbf{estado extendido} y \textbf{recompensa con término de coordinación}. Todos los controles se comparan sobre las mismas diez semillas contra dos referencias: tiempo fijo tuneado por barrido y actuado nativo de SUMO. SARSA, DQN, la variante con crítico centralizado (MAPPO) y el cruce real de Lima importado de OpenStreetMap quedan como trabajo siguiente.
```

**Nuevo:**

```latex
La solución consiste en un \textit{pipeline} reproducible con cuatro unidades: (U1) datos y preprocesamiento; (U2) agentes de \textbf{RL} (un agente por intersección); (U3) simulación y medición en SUMO; y (U4) \textbf{coordinación distribuida entre semáforos}. En U4, cada agente comparte mensajes ligeros con sus \textit{vecinos} (fase actual, tiempo en ella, descarga hacia el vecino y colas en el enlace compartido) para \textbf{coordinar ondas verdes} y \textbf{evitar spillback}. En esta fase se implementaron las cuatro unidades y se evaluaron con un \textbf{plan de pruebas} de cinco casos sintéticos construidos con \texttt{netconvert}, cada uno más difícil que el anterior: un corredor de dos cruces con demanda nominal (P1) y doble (P2), una red de tres cruces con rotonda con demanda nominal (P3) y 1.2 veces la nominal (P4), y una malla de nueve cruces (P5). En cada caso se comparan los mismos modelos con el mismo método: dos referencias sin aprendizaje, el tiempo fijo tuneado por barrido en ese caso y el actuado nativo de SUMO; \textbf{Q-learning} y \textbf{SARSA} tabulares; tres variantes de \textbf{IPPO} con un actor y un crítico compartidos (sin mensajes, con mensajes entre vecinos y con penalización de \textit{spillback}); \textbf{Double DQN}; y \textbf{MAPPO}, con crítico centralizado. Todos los aprendices usan la misma recompensa, el retraso por segundo, se entrenan 200 episodios con tres semillas base, publican la política con mejor validación y se evalúan sobre las mismas treinta semillas. Un \textbf{veredicto prefijado} clasifica cada modelo en cada caso: FUNCIONA si reduce el retraso frente al fijo al menos un 5\,\%, con un intervalo de confianza al 95\,\% entero por debajo de cero y $p < 0.05$, sin perder de forma significativa contra el actuado; MEJORA si la reducción es significativa pero menor o pierde contra el actuado; FALLA si el retraso aumenta de forma significativa; y EMPATA en otro caso. El cruce real de Lima, importado de OpenStreetMap pero sin limpiar, queda como trabajo siguiente.
```

### Parrafo 3 (metricas, metas y resultados principales)

`resumen.tex`, lineas 7 (al 24.09.2026).

**Actual:**

```latex
La métrica primaria es el \textbf{retraso por vehículo} (\texttt{timeLoss} de SUMO); como secundarias se miden la espera detenida, las colas promedio y máxima, las paradas por vehículo, el \textit{throughput}, las emisiones (CO\textsubscript{2}, NOx) y la recompensa por decisión, y en los escenarios de varios cruces el retraso de extremo a extremo, la progresión de los vehículos de paso y la tasa de \textit{spillback}. Las metas del trabajo son una reducción del retraso del \textbf{25–40\%} y de las colas de al menos un \textbf{20\%} frente al control de tiempo fijo. Con Q-learning tabular no se alcanzan: el agente reduce el retraso un 6.4\% en el cruce de dos fases y lo aumenta entre un 15 y un 60\% en los otros tres escenarios de demanda nominal, mientras que el control actuado lo reduce entre un 2 y un 33\% en tres de los cuatro y empata con el fijo tuneado del corredor. Con IPPO se alcanzan en el cruce de dos fases, donde el retraso baja un 35\% y las colas promedio a la mitad. En el corredor, frente a un programa fijo con el reparto de verde tuneado, la mejora es del 6\%; la primera versión de ese fijo, con un solo verde común, hacía parecer la mejora de un 38\%, y la diferencia mide cuánto pesa la referencia. En la red de tres cruces, donde el programa fijo ya coordina una onda verde y el propio actuado solo mejora un 2\%, la coordinación aprendida iguala al fijo y queda dos puntos por detrás del actuado; en el corredor con demanda doble reduce el retraso un 21\% sin llegar a bloquear el enlace entre cruces, cosa que el actuado sí hace. La mensajería entre vecinos es lo que separa a la coordinación de la reacción local: mejora el retraso frente a la misma red sin mensajes con el mismo signo en las tres semillas base entrenadas, y en el corredor supera al control actuado en un 5\%, el primer control aprendido de esta tesis que lo consigue en un escenario de varios cruces.
```

**Nuevo:**

```latex
La métrica primaria es el \textbf{retraso por vehículo} (\texttt{timeLoss} de SUMO); como secundarias se miden la espera detenida, las colas promedio y máxima, las paradas por vehículo, el \textit{throughput}, las emisiones (CO\textsubscript{2}, NOx), los retornos de las tres recompensas y, en los escenarios de varios cruces, el retraso de extremo a extremo, la progresión de los vehículos de paso y el \textit{spillback}. Las metas del trabajo son una reducción del retraso del \textbf{25–40\%} y de las colas de al menos un \textbf{20\%} frente al control de tiempo fijo. Los cinco casos quedaron evaluados con todos los controles, salvo la ablación con la recompensa de colas en P5. \textbf{IPPO con mensajería entre vecinos} es el único modelo con veredicto firme en los cinco casos que no falla en ninguno: reduce el retraso un 6.8, un 23.3 y un 8.8\,\% frente al fijo en P1, P2 y P3 y un 3.6\,\% en P4, empata con el fijo coordinado en ajedrez de la malla (P5), y en los cinco casos queda por debajo del actuado, entre un 3.6 y un 16.4\,\%. Sin mensajes, la misma red empata o falla salvo con demanda doble, y en la malla todos los controles sin mensajes pierden entre un 21 y un 43\,\% contra ese fijo coordinado. Con la misma observación, MAPPO queda a la par de IPPO y Double DQN por detrás. Q-learning y SARSA, con la misma recompensa, fallan en todos los casos con demanda nominal, y la ablación con la recompensa de colas muestra que la causa no es la recompensa. El actuado supera con claridad al fijo tuneado solo con demanda doble ($-19.8$\,\%) y pierde un 21.8\,\% en la malla. La meta de retraso no se alcanza en ningún caso, el más cercano es P2, y la de colas solo en P3 y P5 ($-41.3$ y $-29.0$\,\%). El trabajo sostiene que, en corredores y redes de dos o tres semáforos, una coordinación aprendida con mensajes entre vecinos supera a las dos referencias clásicas por un margen medible, y que en una malla de nueve cruces iguala a un fijo coordinado; no que alcance la magnitud de las metas.
```

Las palabras clave no cambian.

## 2. abstract.tex (en ingles)

El abstract es la traduccion del resumen propuesto; los veredictos se traducen como WORKS, IMPROVES, TIES y FAILS (en la tabla del capitulo siguen en espanol). El titulo, el parrafo 1 y las keywords no cambian.

### Paragraph 2 (pipeline, cases, models and verdict rule)

`abstract.tex`, lineas 9 (al 24.09.2026).

**Actual:**

```latex
A reproducible pipeline with four units is proposed: (U1) data preprocessing and generation of the SUMO network and routes; (U2) \textbf{RL} agents, one per intersection, trained directly through TraCI; (U3) simulation and measurement in SUMO; and (U4) \textbf{distributed coordination between traffic signals}, where each intersection exchanges messages with its neighbours to build \textit{green waves} and prevent \textit{spillback}. This phase implements all four units, validated on \textbf{five synthetic scenarios} built with \texttt{netconvert}: a two-phase intersection, an intersection with protected left turns, a two-intersection corridor, a three-intersection network with a roundabout, and a version of the corridor with twice the demand. Two algorithms are implemented: tabular \textbf{Q-learning} with one independent agent per intersection (U2) and \textbf{IPPO} with a shared actor and critic (U4), the latter with \textbf{neighbour messaging}, an \textbf{extended state} and a \textbf{spillback penalty} in the reward. All controls are compared over the same ten random seeds against two references: a tuned fixed-time program and SUMO's native actuated control. SARSA, DQN, the centralised-critic variant (MAPPO) and a real intersection in Lima imported from OpenStreetMap remain as future work.
```

**Nuevo:**

```latex
A reproducible pipeline with four units is proposed: (U1) data preprocessing and generation of the SUMO network and routes; (U2) \textbf{RL} agents, one per intersection, trained directly through TraCI; (U3) simulation and measurement in SUMO; and (U4) \textbf{distributed coordination between traffic signals}, where each intersection exchanges messages with its neighbours to build \textit{green waves} and prevent \textit{spillback}. This phase implements all four units and evaluates them with a \textbf{test plan} of five synthetic cases built with \texttt{netconvert}, each harder than the previous one: a two-intersection corridor under nominal (P1) and double demand (P2), a three-intersection network with a roundabout under nominal demand (P3) and 1.2 times the nominal demand (P4), and a nine-intersection grid (P5). Every case compares the same models with the same method: two non-learning references, a fixed-time program tuned by grid search for that case and SUMO's native actuated control; tabular \textbf{Q-learning} and \textbf{SARSA}; three variants of \textbf{IPPO} with a shared actor and critic (without messages, with neighbour messages, and with a spillback penalty); \textbf{Double DQN}; and \textbf{MAPPO}, with a centralised critic. All learners use the same reward, the per-second delay, are trained for 200 episodes with three base seeds, publish the checkpoint with the best validation score and are evaluated on the same thirty seeds. A \textbf{pre-registered verdict} classifies each model in each case: WORKS if it cuts delay against fixed time by at least 5\%, with a 95\% confidence interval entirely below zero and $p < 0.05$, without losing significantly to actuated control; IMPROVES if the reduction is significant but smaller, or it loses to actuated control; FAILS if delay increases significantly; and TIES otherwise. The real intersection in Lima, imported from OpenStreetMap but not yet cleaned, remains as future work.
```

### Paragraph 3 (metrics, targets and main results)

`abstract.tex`, lineas 11 (al 24.09.2026).

**Actual:**

```latex
The primary metric is the delay per vehicle (SUMO's \texttt{timeLoss}); secondary metrics are stopped waiting time, average and maximum queue length, stops per vehicle, \textit{throughput}, emissions (CO\textsubscript{2}, NOx) and reward per decision. The targets for the complete work are a \textbf{25--40\%} reduction in delay and at least \textbf{20\%} in queues with respect to fixed-time control. Tabular Q-learning does not reach them: the agent reduces delay by 6.4\% in the two-phase intersection and increases it by 15 to 60\% in the other three nominal-demand scenarios, and by 37\% under double demand, while actuated control reduces it by 2 to 33\% in three of the four and ties with the tuned fixed-time program in the corridor. IPPO reaches them in the two-phase intersection, where delay drops by 35\% and average queues are halved. In the corridor, against a fixed-time program with a tuned green split, the improvement is 6\%; the first version of that baseline, with a single common green, made it look like 38\%, and the gap measures how much the reference matters. In the three-intersection network, where the fixed-time program already coordinates a green wave and actuated control itself only improves by 2\%, the learned coordination matches fixed time and stays two points behind actuated control; in the corridor with twice the demand it cuts delay by 21\% without ever blocking the link between intersections, which actuated control does block. Neighbour messaging is what separates coordination from local reaction: it improves delay over the same network without messages with a consistent sign across the three training seeds, and in the corridor it beats actuated control by 5\%, the first learned control in this thesis to do so in a multi-intersection scenario.
```

**Nuevo:**

```latex
The primary metric is the delay per vehicle (SUMO's \texttt{timeLoss}); secondary metrics are stopped waiting time, average and maximum queue length, stops per vehicle, \textit{throughput}, emissions (CO\textsubscript{2}, NOx) and the returns of the three rewards. The targets for the complete work are a \textbf{25--40\%} reduction in delay and at least \textbf{20\%} in queues with respect to fixed-time control. All five cases were evaluated with every control, except the queue-reward ablation in P5. \textbf{IPPO with neighbour messaging} is the only model with a firm verdict in all five cases that fails in none: it cuts delay by 6.8, 23.3 and 8.8\% against fixed time in P1, P2 and P3 and by 3.6\% in P4, ties with the checkerboard-coordinated fixed plan of the grid (P5), and in all five cases it also beats actuated control, by 3.6 to 16.4\%. Without messages the same network ties or fails except under double demand, and in the grid every control without messages loses to that coordinated fixed plan by 21 to 43\%. With the same observation, MAPPO matches IPPO and Double DQN falls behind. Q-learning and SARSA, with the same reward, fail in every nominal-demand case, and the queue-reward ablation shows that the reward is not the cause. Actuated control clearly beats the tuned fixed-time program only under double demand ($-19.8$\%) and loses by 21.8\% in the grid. The delay target is not reached in any case, the closest being P2, and the queue target only in P3 and P5 ($-41.3$ and $-29.0$\%). The work supports the claim that, in corridors and networks of two or three signals, a learned coordination with neighbour messages beats both classical references by a measurable margin, and that in a nine-intersection grid it matches a coordinated fixed-time program; not that it reaches the size of the targets.
```

## 3. introduccion.tex

Lo central es el estado de avance (3.7). Los demas cambios corrigen frases que el plan v2 deja falsas (cinco escenarios, dos algoritmos, SARSA/DQN/MAPPO pendientes, stable-baselines3). Las metas cuantificables (lineas 15-21) no se tocan.

### 3.1 Presentacion del tema, parrafo 1

`introduccion.tex`, lineas 5 (al 24.09.2026).

**Actual:**

```latex
La congestión vehicular en Lima Metropolitana afecta de manera crítica la movilidad urbana, el tiempo de viaje y la calidad del aire. Este trabajo propone \textbf{optimizar el control semafórico} de una intersección o pequeño corredor de alto tráfico mediante \textbf{Aprendizaje por Refuerzo (RL)} y validación en el simulador \textbf{SUMO}, con un agente por intersección y una evaluación rigurosa frente a los esquemas tradicionales de tiempo fijo y actuado. El estudio se centra en el desarrollo de un \textit{pipeline} reproducible de datos \textrightarrow\ preprocesamiento \textrightarrow\ SUMO \textrightarrow\ RL \textrightarrow\ evaluación. La fase que reporta este documento valida ese \textit{pipeline} sobre cinco escenarios sintéticos, con control por agente aislado y con coordinación entre semáforos vecinos; la transferencia a un cruce real de Lima queda como trabajo siguiente.
```

**Nuevo:**

```latex
La congestión vehicular en Lima Metropolitana afecta de manera crítica la movilidad urbana, el tiempo de viaje y la calidad del aire. Este trabajo propone \textbf{optimizar el control semafórico} de una intersección o pequeño corredor de alto tráfico mediante \textbf{Aprendizaje por Refuerzo (RL)} y validación en el simulador \textbf{SUMO}, con un agente por intersección y una evaluación rigurosa frente a los esquemas tradicionales de tiempo fijo y actuado. El estudio se centra en el desarrollo de un \textit{pipeline} reproducible de datos \textrightarrow\ preprocesamiento \textrightarrow\ SUMO \textrightarrow\ RL \textrightarrow\ evaluación. La fase que reporta este documento valida ese \textit{pipeline} con un plan de pruebas de cinco casos sintéticos (un corredor, una red con rotonda y una malla de nueve cruces, con distintas demandas), con control por agente aislado y con coordinación entre semáforos vecinos; la transferencia a un cruce real de Lima queda como trabajo siguiente.
```

### 3.2 Parrafo que sigue a las metas

`introduccion.tex`, lineas 23 (al 24.09.2026).

**Actual:**

```latex
Estas metas son el objetivo del trabajo completo, no el resultado alcanzado en esta fase. El Capítulo~\ref{cap:resultados} reporta en qué medida las cumple cada uno de los dos algoritmos implementados.
```

**Nuevo:**

```latex
Estas metas son el objetivo del trabajo completo, no el resultado alcanzado en esta fase. El Capítulo~\ref{cap:resultados} reporta en qué medida las cumple cada modelo del plan de pruebas.
```

### 3.3 Parrafo que sigue a los objetivos especificos

`introduccion.tex`, lineas 38 (al 24.09.2026).

**Actual:**

```latex
\noindent De estos objetivos, esta fase ejecuta los cuatro: U1, U2 (con Q-learning tabular), U3 y U4 (con IPPO, mensajería entre vecinos y penalización por \textit{spillback}). De U2 restan SARSA y DQN; PPO se implementó dentro de U4. Del propio U4 queda pendiente la variante con crítico centralizado (MAPPO).
```

**Nuevo:**

```latex
\noindent De estos objetivos, esta fase ejecuta los cuatro. En U2 están implementados Q-learning y SARSA tabulares; PPO, en su versión multiagente independiente (IPPO), y Double DQN, con pesos compartidos, usan la observación con mensajes de U4; y MAPPO completa U4 con un crítico centralizado. Todos se comparan con el plan de pruebas de la Sección~\ref{sec:plan2}, que tiene resultados de todos ellos en los cinco casos.
```

### 3.4 Alcance de esta fase

`introduccion.tex`, lineas 46-51 (al 24.09.2026).

**Actual:**

```latex
\textbf{Alcance de esta fase:}
\begin{itemize}
    \item Cinco escenarios sintéticos construidos con \texttt{netconvert} (un cruce de dos fases, un cruce con giros protegidos, un corredor de dos cruces, una red de tres cruces con rotonda y el mismo corredor con el doble de demanda como caso de estrés), cada uno con una hora de demanda y la punta invertida a la mitad, de modo que ningún programa fijo pueda ser óptimo en los dos periodos.
    \item Entrenamiento de agentes de Q-learning tabular, uno por intersección y sin comunicación entre ellos, y de agentes IPPO con mensajería entre semáforos vecinos, sobre SUMO mediante TraCI.
    \item Comparación con semaforización de tiempo fijo tuneada por barrido y con el control actuado nativo de SUMO, bajo las mismas restricciones de verde mínimo y máximo.
\end{itemize}
```

**Nuevo:**

```latex
\textbf{Alcance de esta fase:}
\begin{itemize}
    \item Cinco casos sintéticos construidos con \texttt{netconvert}, cada uno con una hora de demanda y la punta invertida a la mitad: un corredor de dos cruces con demanda nominal (P1) y doble (P2), una red de tres cruces con rotonda con demanda nominal (P3) y 1.2 veces la nominal (P4), y una malla de nueve cruces (P5). Los casos con una sola intersección (el cruce de dos fases y el de giros protegidos) se usaron en la fase exploratoria y como prueba de humo.
    \item Entrenamiento, con el mismo protocolo y la misma recompensa de retraso, de Q-learning y SARSA tabulares, uno por intersección y sin comunicación, y de IPPO (sin mensajes, con mensajes entre vecinos y con penalización de \textit{spillback}), Double DQN y MAPPO, sobre SUMO mediante TraCI.
    \item Comparación con semaforización de tiempo fijo tuneada por barrido en cada caso y con el control actuado nativo de SUMO, bajo las mismas restricciones de verde mínimo y máximo.
\end{itemize}
```

### 3.5 No incluido en esta fase: los dos ultimos items

`introduccion.tex`, lineas 59-60 (al 24.09.2026).

**Actual:**

```latex
    \item Los algoritmos SARSA y DQN, y con ellos la comparación algorítmica completa.
    \item La variante de U4 con crítico centralizado (MAPPO) y el entrenamiento con un canal de mensajes imperfecto: las políticas de coordinación se entrenaron con mensajes instantáneos, aunque sí se evaluaron con latencia y pérdida.
```

**Nuevo:**

```latex
    \item Los casos P6 (la malla de nueve cruces con demanda alta) y P7 (una red de cuatro por cuatro cruces con tres carriles y giro protegido), que repiten el mismo protocolo sobre escenarios de mayor tamaño.
    \item El entrenamiento con un canal de mensajes imperfecto: las políticas de coordinación se entrenaron con mensajes instantáneos, aunque en la fase exploratoria sí se evaluaron con latencia y pérdida.
```

### 3.6 Areas de investigacion y herramientas: item de Inteligencia Artificial

`introduccion.tex`, lineas 67 (al 24.09.2026).

Maquina: dato de la especificacion del plan v2; los tiempos por episodio estan en la columna `segundos` de `plan2/resultados_*.csv` y el costo se discute en recomendaciones.tex.

**Actual:**

```latex
    \item \textbf{Inteligencia Artificial:} Python 3.14. El agente tabular usa la biblioteca estándar; IPPO se implementa en PyTorch puro sobre CPU, sin Gym ni bibliotecas de RL de terceros. Para DQN, pendiente, se evaluará \texttt{stable-baselines3}.
```

**Nuevo:**

```latex
    \item \textbf{Inteligencia Artificial:} Python 3.14. Los agentes tabulares usan la biblioteca estándar; IPPO, Double DQN y MAPPO se implementan en PyTorch puro sobre CPU, sin Gym ni bibliotecas de RL de terceros. Los entrenamientos corren en un AMD Ryzen 7 3700X (8 núcleos, 16 hilos, 16~GB), con un hilo por entrenamiento y sin GPU.
```

### 3.7 Estado de avance

`introduccion.tex`, lineas 97-101 (al 24.09.2026).

Actualizado en W2 con los resultados congelados a las 03:55 del 25.09.

**Actual:**

```latex
\begin{enumerate}
    \item \textbf{Completado:} construcción de los cinco escenarios sintéticos y su demanda (U1); formulación e implementación del agente de Q-learning tabular (U2); instrumentación de las métricas y de los dos controles de referencia (U3); módulo de coordinación distribuida con IPPO, mensajería entre vecinos y penalización por \textit{spillback}, en variantes incrementales y con tres semillas base por variante (U4); protocolo de evaluación con semillas separadas, intervalos de confianza y pruebas de significancia, aplicado a todos los escenarios y controles.
    \item \textbf{En curso:} análisis conjunto de los resultados. La recompensa de U2 penaliza colas y espera detenida pero no el retraso; la de U4 ya usa el retraso por segundo, de modo que la comparación entre ambos módulos mezcla el efecto del algoritmo con el de la señal y conviene separarlos.
    \item \textbf{Pendiente:} importación y limpieza del cruce real de Lima; implementación de SARSA y DQN para completar la comparación algorítmica; entrenamiento de las políticas de coordinación con un canal de mensajes imperfecto y variante con crítico centralizado (MAPPO).
\end{enumerate}
```

**Nuevo:**

```latex
\begin{enumerate}
    \item \textbf{Completado:} construcción de los escenarios sintéticos y su demanda, incluida la calibración de la red con demanda alta y la malla de nueve cruces (U1); Q-learning y SARSA tabulares con la recompensa de retraso (U2); instrumentación de las métricas, con las mismas columnas de salida en toda corrida, y de los dos controles de referencia (U3); IPPO en tres variantes, Double DQN y MAPPO (U4 y comparación algorítmica); plan de pruebas con protocolo común, barrido del fijo en cada caso y regla de veredicto; casos P1 a P5 evaluados para el fijo, el actuado y los ocho aprendices, salvo la ablación con la recompensa de colas en P5.
    \item \textbf{En curso:} cierre de las cinco celdas cuya política publicada no convergió (Q-learning en P4, la ablación de colas en P2, DQN en P5 y MAPPO en P3 y P4) y corridas de confirmación de que la variante con penalización de \textit{spillback} coincide con la de mensajes en las redes.
    \item \textbf{Pendiente:} casos P6 y P7; la ablación de colas en P5; limpieza en \texttt{netedit} y demanda del cruce real de Lima, cuya importación cruda desde OpenStreetMap se hizo el 01.12.2025; entrenamiento de las políticas de coordinación con un canal de mensajes imperfecto.
\end{enumerate}
```

## 4. capitulo1.tex (lista de algoritmos implementados)

### 4.1 Revision critica: Linea base de comparacion

`capitulo1.tex`, lineas 34 (al 24.09.2026).

**Actual:**

```latex
\textbf{Línea base de comparación.} Los tres trabajos miden únicamente frente a control de tiempo fijo (Trinity añade un agente aleatorio). Ninguno compara contra semaforización \textit{actuada}, que es el control adaptativo estándar y está disponible de fábrica en SUMO. Esta tesis lo incorpora como segundo control de referencia, con las mismas restricciones de verde que el agente, y el Capítulo~\ref{cap:resultados} muestra que la omisión no es menor: el actuado supera al agente tabular en los cinco escenarios evaluados, y solo el agente con aproximación de funciones y mensajería entre vecinos llega a igualarlo o superarlo. \\
```

**Nuevo:**

```latex
\textbf{Línea base de comparación.} Los tres trabajos miden únicamente frente a control de tiempo fijo (Trinity añade un agente aleatorio). Ninguno compara contra semaforización \textit{actuada}, que es el control adaptativo estándar y está disponible de fábrica en SUMO. Esta tesis lo incorpora como segundo control de referencia, con las mismas restricciones de verde que el agente, y el Capítulo~\ref{cap:resultados} muestra que la omisión no es menor: el actuado supera al Q-learning tabular en los cinco casos del plan de pruebas, y solo IPPO con mensajería entre vecinos lo supera en todos ellos. A la vez, en la malla de nueve cruces el actuado pierde un 21.8\,\% frente al fijo coordinado, de modo que ninguna de las dos referencias basta sola. \\
```

### 4.2 Revision critica: Comparacion algoritmica

`capitulo1.tex`, lineas 35 (al 24.09.2026).

**Actual:**

```latex
\textbf{Comparación algorítmica.} Trinity muestra ventajas de PPO y A2C; Uniandes añade DQN con buen rendimiento. Esta tesis implementa \textbf{Q-learning} tabular como línea base y \textbf{PPO}, en su versión multiagente independiente, como algoritmo profundo; SARSA y DQN quedan pendientes para completar la comparación. \\
```

**Nuevo:**

```latex
\textbf{Comparación algorítmica.} Trinity muestra ventajas de PPO y A2C; Uniandes añade DQN con buen rendimiento. Esta tesis implementa \textbf{Q-learning} y \textbf{SARSA} tabulares como líneas base y, con aproximación de funciones, \textbf{PPO} en su versión multiagente independiente (IPPO), \textbf{Double DQN} con pesos compartidos y \textbf{MAPPO} con crítico centralizado. Los tres últimos usan la misma observación, con mensajes entre vecinos, y todos los aprendices la misma recompensa, de modo que la comparación entre algoritmos no se mezcla con la de observaciones ni con la de recompensas. \\
```

### 4.3 Implicancias para el diseno

`capitulo1.tex`, lineas 73 (al 24.09.2026).

**Actual:**

```latex
A partir del estado del arte, esta tesis implementa: (i) un entorno \textbf{SUMO+TraCI} con un agente por intersección, (ii) \textbf{Q-learning y SARSA} como líneas base tabulares y \textbf{DQN y PPO} como algoritmos de \textit{Deep RL}, y (iii) evaluación rigurosa (retraso, colas, \textit{throughput}, paradas y emisiones) frente a control fijo y actuado, con pruebas estadísticas. En la fase reportada en este documento están implementados Q-learning tabular y PPO, este último en su versión multiagente independiente dentro del módulo U4; SARSA y DQN quedan como trabajo siguiente.
```

**Nuevo:**

```latex
A partir del estado del arte, esta tesis implementa: (i) un entorno \textbf{SUMO+TraCI} con un agente por intersección, (ii) \textbf{Q-learning y SARSA} como líneas base tabulares y \textbf{DQN y PPO} como algoritmos de \textit{Deep RL}, y (iii) evaluación rigurosa (retraso, colas, \textit{throughput}, paradas y emisiones) frente a control fijo y actuado, con pruebas estadísticas. En la fase reportada en este documento están implementados los cuatro: PPO en su versión multiagente independiente (IPPO) dentro del módulo U4 y DQN como Double DQN con pesos compartidos, además de MAPPO. Todos tienen resultados en los cinco casos del plan de pruebas.
```

### 4.4 Aporte U4: item Algoritmos

`capitulo1.tex`, lineas 80 (al 24.09.2026).

**Actual:**

```latex
    \item \textit{Algoritmos}: \textbf{IPPO} (PPO independiente con pesos compartidos), con un actor y un crítico compartidos por todos los semáforos. La extensión a \textbf{MAPPO} (crítico centralizado) queda pendiente.
```

**Nuevo:**

```latex
    \item \textit{Algoritmos}: \textbf{IPPO} (PPO independiente con pesos compartidos), con un actor y un crítico compartidos por todos los semáforos, y \textbf{MAPPO}, con el mismo actor y un crítico centralizado que durante el entrenamiento ve las observaciones de todos los semáforos; la ejecución sigue descentralizada.
```

### 4.5 Aporte U4: parrafo de cierre

`capitulo1.tex`, lineas 84 (al 24.09.2026).

Verificado en plan2/evaluacion_<esc>_resumen.csv: en los cinco casos (P1 a P5) la peor base de vecinos tiene menos retraso que la mejor base de local (en P2 por poco: 119.02 frente a 119.27 s).

**Actual:**

```latex
Este módulo añade el tópico de \textbf{Sistemas Distribuidos} al marco de RL, incrementa el esfuerzo computacional (entrenamiento multiagente con estado ampliado) y permite medir el beneficio de la \textbf{coordinación} frente a agentes aislados. La medida es directa, porque el módulo se evalúa en variantes incrementales: una sin mensajería, con las mismas redes y la misma recompensa, y otra con ella. La diferencia entre ambas es el aporte de la comunicación, y resulta favorable a la coordinación en el corredor de dos cruces y en la red de tres, con el mismo signo en las tres semillas base entrenadas por variante (Capítulo~\ref{cap:resultados}).
```

**Nuevo:**

```latex
Este módulo añade el tópico de \textbf{Sistemas Distribuidos} al marco de RL, incrementa el esfuerzo computacional (entrenamiento multiagente con estado ampliado) y permite medir el beneficio de la \textbf{coordinación} frente a agentes aislados. La medida es directa, porque el módulo se evalúa en variantes incrementales: una sin mensajería, con las mismas redes y la misma recompensa, y otra con ella. La diferencia entre ambas es el aporte de la comunicación, y resulta favorable a la coordinación en los cinco casos del plan de pruebas: en cada uno, las tres políticas entrenadas con mensajes quedan por debajo, en retraso, de las tres entrenadas sin ellos (Capítulo~\ref{cap:resultados}).
```

## 5. Fuera de las zonas protegidas

`capitulo2.tex` repite la lista de algoritmos y el diseno de U4 (el skill escribir-tesis pide mantener los cuatro archivos iguales); no es zona protegida pero tiene otro dueno esta noche. Al aplicar estas propuestas conviene revisar que diga lo mismo. La frase de `capitulo5.tex` que hablaba de "veinte veces" el intervalo para la diferencia de 8 s entre dos entrenamientos del corredor ya no esta; con `evaluacion_corredor_resumen.csv` de demo_rl (ic95 = 1.661 s) son unas cinco veces, como dice `conclusiones.tex` (conclusion 12, antes 11). En W2 las conclusiones del plan pasaron de cinco a seis (se agrego la comparacion DQN/MAPPO y la de los tabulares con la ablacion), y las de la fase exploratoria quedaron numeradas de 7 a 14.
