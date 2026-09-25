# demo_rl — Semáforos adaptativos con RL sobre SUMO (tesis UTEC)

## Contexto

Tesis de bachiller en Ciencia de la Computación (UTEC): "Optimización del tráfico
urbano en Lima con semáforos inteligentes mediante Aprendizaje por Refuerzo (RL) y
simulación en SUMO". Autores: Fabian Alvarado y Neftalí Calixto. Asesor: José
Antonio Fiestas Iquira. Curso actual: Tesis 2 (2026-II). El documento fuente
está en `TESIS/` (LaTeX, plantilla UTEC, se compila en Overleaf; `TESIS (12).pdf`
es solo una copia de septiembre 2026). Al 06.09.2026 el documento está escrito de
punta a punta: capítulo III (`capitulo4.tex`) cubre U1 a U4, capítulo IV
(`capitulo5.tex`) los resultados de los cinco escenarios, y conclusiones,
recomendaciones y anexos ya no son placeholders.

Arquitectura de la tesis en 4 unidades:
- U1 preprocesamiento (OSM → red SUMO con netconvert/netedit, rutas, .sumocfg)
- U2 RL de agente único (Q-learning y SARSA como base; DQN y PPO como deep RL)
- U3 simulación y medición vía SUMO + TraCI (delay, colas, throughput, paradas, emisiones)
- U4 coordinación distribuida multiagente (IPPO/MAPPO, mensajería entre vecinos,
  recompensa con penalización por spillback)

Metas cuantificables declaradas en la tesis (contra control de tiempo fijo):
25–40 % menos retraso promedio, ≥20 % menos colas, +10 % throughput, −5 % CO2.
El rigor prometido incluye semillas fijas, IC95 % y pruebas tipo Mann–Whitney:
cualquier resultado que se vaya a citar en el documento debe correrse con varias
semillas, no solo la 42.

Esta carpeta es la prueba de concepto de U2, U3 y U4 sobre cruces SINTÉTICOS. El
cruce real de Lima (importado de OSM y limpiado en netedit, capítulo III) es un
archivo aparte que aún no está aquí.

## Escenarios

| Escenario | Archivos | Descripción |
|---|---|---|
| cruce | `cruce.*` | Prueba 1: cruce N-S/E-O, 1 carril por sentido, semáforo `semaforo_C` de 2 fases verdes. Demanda invertida a mitad de hora (0–1800 s punta N-S, 1800–3600 s punta E-O). |
| cruce2 | `cruce2.*` | Prueba 2: mismo cruce con 2 carriles por sentido, carril exclusivo de giro a la izquierda y fases de giro protegido (4 fases verdes). |
| corredor | `corredor.*` | Prueba 3: dos cruces (`semaforo_C1`, `semaforo_C2`) sobre una avenida E-O separados 300 m, un agente Q-learning independiente por cruce (antesala de U4). |
| red | `red.*` | Prueba 4: rotonda sin semáforo (prioridad del anillo) + tres cruces semaforizados sobre una avenida de 2 carriles por sentido muy cargada; transversales ligeras. Tres agentes independientes. |
| corredor_alta | `corredor_alta.*` | Prueba 6 (estrés de U4, 06.09.2026): misma red de `corredor` con toda la demanda ×2 (3620 veh/h, 1200 en el sentido punta). Es el único escenario donde hay spillback y donde el throughput discrimina. Usa `corredor.net.xml`; el fijo está retuneado aparte. |

Las redes `.net.xml` se regeneran con `build_net.bat` solo si se editan los
`.nod.xml` / `.edg.xml` / `.con.xml`.

## PLAN DE PRUEBAS V2 (24.09.2026)

Qué es. Plan aprobado por el asesor el 23.09: "De los 7 casos desarrollen por lo
menos 4 para la próxima reunión. Apliquen el mismo método con cada configuración y
usen las mismas métricas de salida para compararlos y llegar a una conclusión sobre
el alcance del proyecto. Suban esto a la plantilla". Reunión: 25.09.2026, 8:00. Se
implementó y se corrió la noche del 24.09; los resultados se congelaron el 25.09 a
las 03:55 (`plan2/veredicto_congelado_0355.csv|md`). Contrato: `plan2/ESPEC.md`
(casos, modelos, protocolo, nombres de archivo, regla de veredicto, dueños).
- Casos: P1 `corredor`, P2 `corredor_alta` (×2.0), P3 `red`, P4 `red_alta` (×1.2,
  nuevo), P5 `malla3` (3×3 cruces, 2 carriles por sentido, nueva). P6 (malla alta) y
  P7 (red 4×4, 3 carriles, giro protegido) quedan como fase siguiente (tabla
  `tab:plan2-casos` de capitulo4.tex).
- Modelos: fijo (barrido en cada celda), actuado, ql, sarsa, ql_colas (ablación),
  ippo_local, ippo_vecinos, ippo_spill, dqn (`rl_dqn.py`), mappo (`rl_mappo.py`).
  Escenarios nuevos en `escenarios_plan2.py`.
- En la tesis: método en capitulo4.tex `sec:plan2`; resultados en capitulo5.tex;
  tablas completas (bases y modelos que el capítulo IV no muestra) en anexos.tex,
  Anexo A, "Plan de pruebas v2: tablas completas"; scripts en el Anexo B.

Dónde vive. Todo en `plan2/`: todas las corridas usan `plan2/` como directorio de
trabajo, así que los resultados del 06.09 en `demo_rl/` no se tocan. `tag` =
`<esc>_<alg>_s<base>`: `resultados_<tag>.csv`, `checkpoints/<tag>_ep<NNN>.*`,
`q_table_<tag>.json` + `.meta.json` o `politica_<esc>_<var>_s<base>.pt` + `.json`,
`parciales/eval_<esc>_<brazo>.csv`, `evaluacion_<esc>.csv` y `_resumen.csv`,
`barrido_<esc>.csv`, `<esc>.add.xml` (fijo ganador de la celda), `veredicto.csv|md`.

Cómo se corre:
```
cd plan2
python generar_trabajos.py        # escribe cola/trabajos.jsonl (prioridad 0 = antes)
python cola.py --cpus 11          # lanza lo que tenga sus dependencias; logs en cola/logs/
                                  # control: cola/pausa, cola/fin, cola/reintentar.txt
python ../consolidar.py --escenario red    # parciales -> evaluacion_red.csv y _resumen.csv
cd .. && python veredicto.py      # plan2/veredicto.csv|md y TESIS/secciones/tablas/veredicto_*.tex
```
La cola ya encadena barrido, entrenamiento y evaluación; consolidar y veredicto se
corren a mano cuando terminan evaluaciones. `python veredicto.py --probar` prueba
las reglas.

Protocolo (igual para todos los aprendices y celdas): bases 42/2042/4042 (episodio
k = semilla base + k), 200 episodios, validación cada 10 con la política congelada
en 999 y 1999, checkpoint en cada validación, política publicada = checkpoint de
menor validación; base publicada = mediana de las tres por esa validación (nunca
con 1001-1030). Fijo barrido en cada celda con 2001-2003. Evaluación final
1001-1030 para todos los brazos; Δ con bootstrap pareado por semilla (10 000
remuestreos) y Wilcoxon pareado. Tabular: ε 1.0 → 0.01 al 80 % de los episodios,
α 0.1, γ 0.9.

Regla de veredicto (Δf = Δ % del retraso vs fijo, Δa vs actuado):
- FUNCIONA: IC95 de Δf entero < 0, p < 0.05, Δf ≤ −5 % y no pierde de forma
  significativa contra el actuado (IC95 de Δa entero > 0 con p < 0.05).
- MEJORA: IC95 de Δf entero < 0 y p < 0.05, pero Δf > −5 % o pierde contra el actuado.
- FALLA: IC95 de Δf entero > 0 y p < 0.05. EMPATA: el resto.
- PENDIENTE: celda incompleta, o la base publicada no convergió (último tercio de
  la serie de validación: |plateau| ≤ 5 % y estabilidad ≤ 5 %); se escribe el
  veredicto provisional.

Hallazgos de la noche del 24.09 (todos deben seguir escritos en la tesis):
1. P4 `red_alta` usa 1.2 × la demanda de `red`, no 2.0. Con f ≥ 1.3 la rotonda sin
   semáforo se satura antes que los semáforos: sus ramales de un carril (NR_RN,
   SR_RS) se llenan y los vehículos de esos ramales pierden 400-700 s cada uno, que
   ningún semáforo puede evitar. Regla: el mayor f que no satura la rotonda. Tabla
   por factor (1.0 a 3.0, semillas 2001-2003) en la cabecera de `red_alta.rou.xml`.
2. En red, red_alta y malla3 el término de spillback de IPPO spill nunca se activa:
   la cola máxima de un carril de enlace en el entrenamiento de ippo_vecinos (máximo
   de las tres bases, 200 episodios) es red 9, red_alta 12 y malla3 8, frente a un
   umbral de plazas // 2 = 19 (38 plazas) en red y red_alta y 18 (37) en malla3. Con
   la misma base la política de spill es idéntica bit a bit a la de vecinos, así que
   ahí no se entrenó aparte (prioridad 9 en la cola) y el veredicto dice
   "= vecinos". Verificado directamente: dos corridas completas de spill en red
   (bases 42 y 2042) y cuatro parciales (red 4042, red_alta 42/2042/4042) son
   idénticas a vecinos episodio a episodio (timeloss, espera, cambios de fase, kl,
   pérdidas, val, ret_retraso) con `spill_activaciones` = 0, y las dos completas dan
   el mismo retraso que vecinos en las 30 semillas de evaluación (20.03 y
   21.70 s/veh). En corredor y corredor_alta sí se activa. Fuente:
   `cola_max_enlace` y `spill_activaciones` de `plan2/resultados_<esc>_ippo_*_s*.csv`,
   `plan2/evaluacion_red.csv`; regla en `veredicto.spill_inactivo` (desde el 25.09
   también cubre celdas de spill parciales o sin evaluar).
3. Con la malla de verdes ampliada hacia abajo (corredor 12/15/18/20/25/30,
   corredor_alta 15-35) el óptimo del fijo del corredor sigue en 20/10 con desfase
   15, ahora interior: la referencia ya era la mejor (cierra el A1 del 07.09). En
   corredor_alta (25/15/desfase 25) y red (25/15/0-23-0) el ganador también es el
   programa que ya estaba instalado, con óptimo interior. En los nuevos: red_alta
   30/10/0-20-0 (transversal en el piso de 10 s, válido; el 25/15 queda a 0.05 s con
   sd ~3 s, empate práctico) y malla3 25/15 con desfases en ajedrez 0/23, interior.
   Fuente: `plan2/barrido_<esc>.csv` y la cabecera de `plan2/<esc>.add.xml`.
4. El prototipo de malla del 18.09 tenía las fases EO y NS cruzadas. `malla3` se
   construyó corregida: en `malla3.add.xml` la fase 0 de cada semáforo es la EO
   (avenida) y la 2 la NS (docstring de `escenarios_plan2.py`).
5. En la observación de IPPO la ranura llamada `cola_mi_salida` mide en realidad la
   cola del enlace que ENTRA desde el vecino (heredado del 06.09). En malla3 es
   numéricamente simétrica. El código no se cambió para no invalidar políticas
   entrenadas. En la tesis ya está escrito con lo que mide: fila 22 de tab:obs-u4
   (capitulo4.tex) y la lectura de IPPO spill en capitulo5.tex. La sección U4 de
   abajo lo lista con el nombre del código.
6. Q-learning, SARSA, DQN, IPPO y MAPPO usan en el plan v2 LA MISMA recompensa de
   retraso (la de U4, `rl_ippo.recompensa_paso`; en tabular sin la escala 0.02).
   La de colas de U2 se conserva solo como ablación `ql_colas`. La sección
   "Formulación RL implementada" de abajo describe la fase anterior.
7. Máquina real: AMD Ryzen 7 3700X, 8 núcleos y 16 hilos, 16 GB de RAM, sin usar
   GPU. Tiempo por episodio (mediana de la columna `segundos` de
   `plan2/resultados_<tag>.csv` por escenario y modelo, con la cola corriendo hasta
   11 procesos a la vez): corredor 5-8 s (DQN 8.4), corredor_alta 13-16 s, red
   9-11 s, red_alta 10-12 s, malla3 24-25 s (DQN 30.6). Un entrenamiento de 200
   episodios (suma de `segundos`): 17 a 57 min fuera de malla3; en malla3, 82 a
   85 min (DQN unos 102).

Estado final (W2; `plan2/veredicto.md` congelado el 25.09 a las 03:55; la tesis
manda, esto es nota). Matriz caso × modelo:
| Caso | Actuado | QL | SARSA | QL colas | DQN | IPPO local | IPPO vecinos | IPPO spill | MAPPO |
|---|---|---|---|---|---|---|---|---|---|
| P1 | EMPATA | FALLA | FALLA | FALLA | MEJORA | EMPATA | FUNCIONA | FUNCIONA | FUNCIONA |
| P2 | FUNCIONA | MEJORA | FALLA | pend. (FALLA) | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA |
| P3 | MEJORA | FALLA | FALLA | FALLA | MEJORA | FALLA | FUNCIONA | = vecinos | pend. (FUNCIONA) |
| P4 | EMPATA | pend. (FALLA) | FALLA | FALLA | MEJORA | FALLA | MEJORA | = vecinos | pend. (MEJORA) |
| P5 | FALLA | FALLA | FALLA | sin datos | pend. (FALLA) | FALLA | EMPATA | = vecinos | EMPATA |
"pend. (X)": la base publicada no convergió, X es el provisional. Lectura:
- Resultado central: IPPO vecinos funciona en P1-P3, mejora en P4, empata con la onda
  verde en P5 y supera al actuado en los cinco casos (P5: −16.4 %).
- SARSA falla en P1-P5 como Q-learning: techo tabular con la misma recompensa. La
  ablación ql_colas (mismo QL, recompensa de colas) falla en P1, P3 y P4 con deltas
  del mismo orden (+9.6 a +10.6 % frente a +9.2 a +12.4 % de ql): el techo no es la
  recompensa. En P2 ql mejora (−8.8 %) y ql_colas no convergió; P5 no se corrió.
- DQN mejora en P1, P3 y P4, funciona en P2; P5 no convergió (provisional falla,
  +11.1 % vs fijo, −8.8 % vs actuado). MAPPO funciona en P1 y P2, empata en P5
  (−0.3 %, p = 0.0896); P3 y P4 no convergieron (provisionales funciona y mejora).
- En P5 todo control sin mensajes pierde contra la onda verde: actuado +21.8 %,
  IPPO local +25.9 %, SARSA +40.0 %, Q-learning +42.5 %.
Fuente: `plan2/veredicto.csv`. En la tesis: matriz y modelos principales en
capitulo5.tex; bases y tablas de sarsa, ql_colas, dqn, mappo, ippo_local e
ippo_spill en anexos.tex (Anexo A, "Plan de pruebas v2: tablas completas").

Pendiente al cierre de W2 (25.09, 04:00):
- La cola sigue corriendo confirmaciones de IPPO spill (red 4042, red_alta y
  malla3). NO correr `consolidar.py` ni `veredicto.py` antes de la reunión: cambiarían
  los archivos congelados. Si se corren después, comparar contra
  `plan2/veredicto_congelado_0355.*` y revisar el texto de capitulo5 y anexos.
- Celdas sin veredicto firme (base publicada sin converger): QL P4, ql_colas P2,
  DQN P5, MAPPO P3 y P4. ql_colas P5 no se corrió. Opciones: más episodios con el
  mismo protocolo o declararlas como límite.
- P6 (malla alta) y P7 (red 4×4, 3 carriles, giro protegido) no se empezaron.
- `plan2/generar_trabajos.py` (l. 35, 112 caracteres) y `plan2/cola.py` (l. 141,
  113) pasan de 110 caracteres: no están en el Anexo B (se dice ahí). `tablas_tex.py`
  (l. 499 y 536, 111 caracteres) sí está en el Anexo B desde antes: acortar esas dos
  líneas y recopiarlo.
- `TESIS/codigo/` quedó al día el 25.09 04:00 (consolidar.py y veredicto.py
  recopiados); recopiar si cambia algún script.

## Formulación RL implementada (no cambiarla sin actualizar código y documento a la vez)

Ojo: `capitulo4.tex` (módulo U2) todavía trae una formulación genérica distinta a
esta (estado crudo por carril, tres acciones, recompensa sin pesos, decisión cada
segundo); la lista de divergencias está en el skill `escribir-tesis`, sección 4.

- Estado: cola discretizada por aproximación (bins 0, 1–3, 4–8, >8) + índice de fase verde activa.
- Acción: 0 = mantener fase verde, 1 = pasar a la siguiente fase verde (ámbar automático).
- Recompensa: r = −(w1·Σcolas + w2·Σesperas), con w1=1.0, w2=0.01.
- Restricciones: verde mínimo 10 s (5 s en fases de giro protegido, detectadas por
  tener ≤2 movimientos en verde), verde máximo 60 s, decisión cada 5 s.
- Q-learning: α=0.1, γ=0.9, ε-greedy con decaimiento 0.9 hasta 0.05 (cruce2
  necesitó decaimiento 0.96 y 120 episodios; hay flags --eps-decay y --gamma).
- Episodio = 1 hora simulada (con margen hasta 6000 pasos para vaciar la red).
- Reloj de decisión: cada agente decide a los 5, 10, 15... s de su verde (la
  primera vez a los 5 s de entrar el verde), en ámbar no decide; así el verde
  mínimo real es 10 s y el máximo 60 s también en rl_corredor.py (antes del
  05.09 el reloj global lo dejaba en 12/62 s). La recompensa que se reporta en el
  CSV se mide cada 5 s de reloj fijo en los cuatro modos; la que ve el agente
  para aprender sigue su propio reloj.
- Evaluación intermedia (política congelada) cada 5 episodios con semilla 999,
  sobre una copia de la Q-table y restaurando el RNG; evaluación final con
  semillas 1001–1010.

### U4 (rl_ippo.py, 06.09.2026): IPPO con pesos compartidos

- Un actor y un crítico (31-64-64, tanh, ortogonal) compartidos por todos los
  semáforos; observación de 31: 15 locales (4 colas/cap, 4 móviles/cap, fase
  one-hot, t_verde/60, puede_cambiar, id one-hot de 3) + 2 ranuras de vecino
  (oeste, este) × 8 (presente, verde_avenida, ámbar, t_fase/60, outflow/cap,
  cola_alimentadora/cap, cola_mi_salida/plazas, edad/30). Variantes: local
  (ranuras a cero), vecinos, spill (w3=2, bisagra en plazas/2=19), cambio (w4=2).
- Mensajes cada 5 s de reloj global por `Canal` (latencia/pérdida solo en
  evaluación, RNG propio). Máscara de acciones = verde mín/máx de U2; mismo reloj
  de decisión que rl_corredor.py.
- Recompensa del agente: NO es la de U2. Suma por segundo sobre el intervalo de
  decisión, dividida entre 5, de −(1.0·Σ n_a(1−v̄_a/vmax_a) + 0.01·Σ esperas)
  (vehículos-equivalentes retrasados = timeLoss por segundo). La de U2 (colas
  detenidas) se sigue reportando a reloj fijo como `recompensa_decision`. Escala
  0.02. Por qué: la prueba de humo en cruce mostró que con el conteo de
  detenidos PPO colapsa a cambiar de fase cada 10 s (las colas reptan y no
  cuentan como detenidas); ver capitulo4.tex "Lo que enseñó la prueba de humo".
- HIPER congelados tras la prueba de humo: γ 0.95, λ 0.95, clip 0.2, 10 épocas,
  minilote 64, lr 1e-3 lineal a 0, entropía 0.01, valor 0.5, recorte de
  gradiente 0.5 POR RED (actor y crítico por separado; el global anulaba al
  actor). 200 episodios, eval argmax cada 10 con semilla 999, bases 42/2042/4042;
  la política que representa a cada variante es la de la base con eval-999
  final mediana (`comun.politicas_ippo`). `--hiper lr=...,minibatch=...` permite
  cambios registrados. Registros de la prueba de humo en `humo/`.
- Determinismo verificado (dos corridas de 3 episodios idénticas dígito a dígito).
- corredor_alta = corredor con toda la demanda × 2.0 (elegido con el actuado,
  semillas 2001–2003, criterio: cola por carril ≥ 34 en ≥ 2 de 3 semillas; 1.3
  → 0/3, 1.5 → 1/3, 2.0 → 3/3). Fijo retuneado con `barrer_fijo.py corredor_alta
  --semillas 2001-2003` (verde avenida × transversal × offset). Todo tuneo nuevo
  usa 2001–2003.

## Comandos

```
python rl_semaforo.py baseline|actuado|train|demo [--escenario cruce|cruce2] [--gui]
python rl_semaforo.py train --escenario cruce --episodios 40 --desde-cero   # eval greedy cada 5 ep
python rl_corredor.py baseline|actuado|train|demo [--escenario corredor|red] [--gui]
python evaluar.py --escenario <esc>        # fijo, actuado y RL con semillas 1001-1010 + estadistica
python barrer_fijo.py <esc>                # barrido del programa fijo por retraso
python graficar.py <esc>                   # fig_<esc>_curva|comparacion|serie|ecdf|qtable.png
python tablas_tex.py                       # tablas LaTeX en TESIS/secciones/tablas/
python rl_ippo.py train --escenario red --variante vecinos --seed 2042     # U4, 200 episodios
python evaluar.py --escenario red --ippo politica_red_local_s42.pt,politica_red_vecinos_s42.pt
python evaluar.py --escenario red --brazos "" --ippo politica_red_vecinos_s42.pt --latencia 5 --perdida 0.3
```
Salidas de U4: `resultados_<esc>_ippo_<variante>_s<base>.csv`,
`politica_<esc>_<variante>_s<base>.pt/.json`, brazos `ippo_<variante>[_s<base>][_L<lat>p<perd>]`
en `evaluacion_<esc>.csv` (deltas también vs actuado y vs rl), tablas
`<esc>_u4|fragilidad|s1|ippo_episodios.tex`, `resumen_u4.tex`, figuras
`fig_<esc>_curva_ippo|fases|spillback.png`. Varios entrenamientos pueden correr en
paralelo (nombres de archivo por corrida); `evaluar.py` no (comparte evaluacion_<esc>.csv).
Episodios y decaimiento por escenario: cruce 40 (0.9), cruce2 120 (0.96),
corredor 40 (0.9), red 100 (0.95). `comun.py` tiene lo compartido (métricas del
tripinfo, programa actuado, CSV, series).

Salidas por escenario: `q_table_<esc>.json`, `resultados_<esc>.csv` (por episodio,
con semilla, U3 y eval greedy; el formato viejo quedó en `resultados_<esc>_v1.csv`),
`evaluacion_<esc>.csv` y `_resumen.csv`, `vehiculos_<esc>_<control>.csv`,
`serie_<esc>_<control>_s<semilla>.csv`, `barrido_<esc>.csv`, `fig_<esc>_*.png`,
`tripinfo_<esc>_<modo>.xml`. Las figuras se copian a `TESIS/images/` y los scripts
a `TESIS/codigo/` (los incluye el anexo) cada vez que cambian.

## Resultados validados (protocolo del plan de pruebas, 05.09.2026)

Política congelada, 10 semillas de evaluación 1001–1010 comunes a los tres
controles; retraso = timeLoss por vehículo; Δ con IC95 % bootstrap pareado y p de
Wilcoxon. Fuente: `evaluacion_<esc>_resumen.csv` (se regenera con `evaluar.py`).

| Escenario | Fijo tuneado | Actuado SUMO | Q-learning | RL vs fijo | Actuado vs fijo |
|---|---|---|---|---|---|
| cruce (40 ep) | 23.2 s | 15.5 s | 21.7 s | −6.4 % [−9.3, −2.7], p=0.014 | −33 % |
| cruce2 (120 ep, decay 0.96) | 27.5 s | 23.2 s | 32.2 s | +16.7 % [+9.9, +25.4], p=0.002 | −16 % |
| corredor (40 ep, 2 agentes); fijo RETUNEADO 20/10/off15 el 06.09 | 21.2 s (era 31.9 con el 25/25) | 20.9 s | 33.9 s | +60 % [+53, +67], p=0.002 (era +6.3 % vs el fijo viejo) | −1.1 % n.s. (empate) |
| red (100 ep, decay 0.95, 3 agentes); fijo RETUNEADO 25/15/off 0-23-0 el 06.09 | 21.8 s (era 22.2 con el 20/20) | 21.4 s | 25.1 s | +15.3 % [+13.9, +16.8], p=0.002 (era +13.1 %) | −1.7 % [−2.6, −0.6] p=0.020 |

Resultados U4 (06.09.2026, IPPO, política mediana de 3 bases, mismas 10 semillas;
fuente `evaluacion_<esc>_resumen.csv`, brazos `ippo_*`):

| Escenario | IPPO local | IPPO vecinos | vecinos vs fijo | vecinos vs actuado | local vs QL |
|---|---|---|---|---|---|
| cruce (humo, 60 ep, 1 base) | 15.05 s (−35 %) | — | — | −2.6 % (local) | −31 % |
| red (fijo 25/15/off 0-23-0 = 21.78 s) | 22.17 s (+1.8 % [0.7, 2.9] p=0.02; bases 22.09/22.17/24.20) | 21.89 s (bases 21.68/21.74/21.89 = −0.5/−0.2/+0.5 %, ninguna signif.) | +0.5 % [−0.3, +1.3] p=0.41 EMPATE (era −1.5 % vs el 20/20) | +2.2 % [0.8, 3.5] | −12 % |
| corredor (fijo 20/10/off15 = 21.15 s) | 21.27 s (+0.6 % n.s.; bases +0.1/+0.6/−2.4 %) | 19.84 s (bases 19.84/19.90/20.37) | −6.2 % [−8.0, −4.6] p=0.002 (era −37.7 % vs el fijo simétrico) | −5.1 % [−6.4, −3.9] p=0.002 | −37 % |
| corredor_alta (fijo 153.9, actuado 123.0, QL 211) | 122.0 s (1 base) | 121.3 s (bases 120.9/121.3/119.3); spill 122.8 (120.4/118.5/122.8) | −21.2 % [−22.2, −20.0] | −1.3 % [−3.8, 1.4] n.s. | −42 % |

Lecturas: N1 estabilidad se cumple SOLO en su mitad del signo (vecinos queda del
mismo lado del fijo en 3 de 3 en corredor y corredor_alta; en red las tres bases
empatan con el fijo retuneado, signos mixtos y ninguno significativo); la mitad del rango NO se
cumple en ninguno: rango entre bases vs IC de una política = red vecinos 0.20 vs
0.13–0.28, corredor vecinos 0.54 vs 0.36–0.40, corredor_alta vecinos 2.01 vs
1.53–1.80, spill 4.29 vs 1.61–2.09, y local-red 2.11 vs 0.20–0.37 (el peor).
Verificado el 06.09; una redacción previa lo daba por cumplido y se corrigió.
N2 local < QL en todo; N3 vecinos < local 3 de 3 y ≤ onda verde en red; N5
iguala al actuado en cruce/corredor (local) y lo supera en corredor (vecinos);
N6 meta −25 % cumplida SOLO en cruce (en corredor era −38 % contra el fijo
simétrico débil y es −6 % contra el fijo 20/10/off15; en red nadie baja de −4 %).
Secundarias de vecinos en corredor vs fijo nuevo: colas −5.6 %, CO2 −1.6 %, paradas
−16 %, cambios −9.5 %, punta −17 % (24.4→20.3), le1 0.91→0.95, cola enlace 7.9→5.5.
Progresión: paradas_corredor_le1 0.95–0.985 con vecinos (fijo 0.60/0.98,
actuado 0.72–0.73, QL 0.32–0.53). Canal imperfecto (S1) sobre la mediana de
vecinos: red L5p30 +0.8 s, L10 +2.2 s; corredor L5 +1.4, L5p30 +2.2, L10 +2.5 s;
en todos la progresión se deshace (le1 baja a 0.54–0.85): el agente no descuenta
mensajes viejos porque nunca los vio en entrenamiento. spill nominal (base 42) =
control de no daño OK (red 21.68, corredor 20.21). corredor_alta: ver LEEME/tesis.

Secundarias del RL vs fijo (cruce / cruce2 / corredor / red), contra los fijos
VIGENTES (corredor y red retuneados): espera −26 / +18 / +76 / +4 %; paradas
+27 / +23 / +94 / +76 %; CO2 −1.5 / +4 / +11 / +6 %; cambios de fase
+77 / +22 / +13 / +56 %.
Throughput no discrimina (demanda subsaturada). Metas cumplidas por el RL:
retraso −25 % en ninguno; colas −20 % solo en cruce y solo en la media; CO2 −5 %
en ninguno. Los números viejos de una semilla (−31 % de espera en cruce, etc.)
quedaron en `resultados_<esc>_v1.csv`; los de la corrida con el reloj de decisión
desfasado (corredor −19 %, red +23 %) en `resultados_<esc>_v2.csv`. Ninguno se cita.

Reglas y lecciones que salieron de estas corridas:
- Los baselines se barren en reparto asimétrico (avenida × transversal × desfase,
  `barrer_fijo.py`, semillas 2001–2003): la primera ronda solo barría un verde
  común y dejó el fijo del corredor 10 s peor de lo posible (ver HALLAZGO más
  abajo). Tunear igual antes de comparar cualquier escenario nuevo, y comparar
  siempre también contra el actuado, que gana al Q-learning en los cinco casos.
- El agente mejora la espera detenida mucho más que el retraso porque eso es lo
  que penaliza la recompensa; cambia de fase ~77 % más que el fijo y sube las
  paradas. Alinear la recompensa con el retraso (penalizar cambios de fase o
  incluir timeLoss) es un cambio de formulación pendiente, que exige actualizar
  código y capitulo4.tex a la vez.
- cruce2 es el hallazgo del techo tabular: 1024 estados, el agente visita 390 y la
  política greedy cae en estados poco visitados; la evaluación intermedia se
  estanca, más episodios no ayudan. Argumento empírico para DQN/PPO. No insistir
  con γ=0.95 (inestable) ni con desempate "mantener fase".
- red es el hallazgo de coordinación: tres agentes independientes pierden +15 %
  contra la onda verde tuneada 25/15 (y ganarían por mucho al mismo fijo sin
  desfases: 36.4 s sobre 1001–1010, `barrido_red_sin_desfases_1001-1010.csv`) y la
  evaluación intermedia se estanca en 24–25 s desde el episodio 5.
  Evidencia empírica que motiva U4.
- corredor es el hallazgo de fragilidad: con verde mínimo efectivo de 12 s los
  dos agentes ganaban −19 %; con el reloj corregido a 10 s cambian de fase 463
  veces por hora y pierden +6 %. La política tabular multiagente es sensible al
  verde mínimo y una sola corrida de entrenamiento no la caracteriza.
- El RNG de Python se siembra en TODOS los modos (el desempate usa random). La
  evaluación greedy intercalada copia la Q-table y restaura el RNG: el
  entrenamiento reproduce el CSV dígito a dígito. Activar el dispositivo de
  emisiones tampoco cambia la secuencia aleatoria de SUMO. La corrida original de
  cruce (9.4→5.9) no era reproducible; su q_table quedó en q_table_cruce_original.json.

## Tesis: regla de trabajo

Todo hallazgo, resultado citable, cambio de método, métrica o escenario nuevo y
toda decisión de diseño se escribe en `TESIS/secciones/*.tex` en el mismo turno
en que se produce (pedido del asesor el 28.08.2026: nada en documentos sueltos).
Si el hallazgo contradice algo ya escrito, se corrige el texto existente y se
revisa en cascada: introducción, resumen y abstract, capítulo 2, capítulo 4,
capítulo 5, conclusiones. Cómo y dónde va cada cosa: skill `escribir-tesis`.
Validar siempre con `python TESIS/validar_tex.py` y compilar con
`python TESIS/compilar.py` (MiKTeX local desde el 06.09; Overleaf sigue siendo la
copia oficial). Numeración: `capitulo4.tex` es el Capítulo III y
`capitulo5.tex` (Resultados) el IV; `capitulo3.tex` está vacío.

Jerarquía de registros: el CSV es el dato crudo; el .tex es el registro oficial;
LEEME.txt y este archivo son notas y nunca el único lugar de un número. Al .tex
entra solo lo evaluado con el protocolo de semillas (evaluación con semillas
1001–1010, las mismas para fijo, actuado y RL; media, IC95 % y prueba); una
corrida de una semilla es provisional y se queda en el CSV. Métrica primaria:
timeLoss por vehículo (el "retraso" de las metas); espera detenida, colas,
paradas, throughput y CO2 son secundarias.

Sincronización con Overleaf: `TESIS/` es una copia de lo que hay en Overleaf.
Se edita aquí y Fabian resube los archivos cambiados; si alguien edita en
Overleaf directamente, descarga a `TESIS/` antes de la siguiente sesión. Antes
de editar `TESIS/`: `git status` limpio (o commit de lo pendiente) y ninguna otra
sesión editando. Al terminar: `git diff -- TESIS/` en el reporte y la lista de
archivos a resubir. Resumen, abstract, metas y objetivos, capítulo 1 y los
captions del autor solo se cambian de contenido con confirmación previa;
`tesisutec.cls` y los paquetes de `main.tex` no se tocan.

## Convenciones (importan para el documento de tesis)

- Todo el código, comentarios, nombres de variables y salidas en español, sin
  tildes en identificadores. Mantener el estilo simple y legible del código
  existente: es material que se cita en la tesis.
- Texto de entregables: natural, en español, sin lenguaje de IA ni formato
  decorativo. Solo lo que realmente se va a usar.
- Trato de trabajo: directo y crítico, sin suavizar errores; corregir con
  explicación breve y el siguiente paso más útil.
- Reproducibilidad: semilla por defecto 42 (en entrenamiento cada episodio usa
  semilla base + número de episodio). Registrar todo resultado en el CSV del
  escenario.

## Entorno

Windows 10 Pro, AMD Ryzen 7 3700X (8 núcleos, 16 hilos), 16 GB de RAM; no se usa
GPU (torch en CPU, `torch.set_num_threads(1)` por proceso; la cola del plan v2 corre
11 procesos a la vez). SUMO 1.25 (SUMO_HOME definido, binarios en PATH), Python 3.14
con traci, sumolib, matplotlib, numpy, scipy, torch, pypdf (sin pandas). Tiempos por
episodio medidos: sección PLAN DE PRUEBAS V2, hallazgo 7.
Repositorio git local (rama `main`, desde el 05.09.2026); los commits los hace
Fabian salvo que pida lo contrario. `respaldo_tesis/` fue el respaldo manual
previo al git y se puede borrar cuando Overleaf compile bien. Desde el
06.09.2026 hay MiKTeX local: `python TESIS/compilar.py` hace el ciclo completo
(pdflatex, bibtex, pdflatex ×2) en ~27 s y resume errores, citas sin resolver y
cajas que se salen; `--rapido` una sola pasada. Overleaf sigue siendo la copia
oficial, pero ya se puede comprobar aquí que compila (198 páginas al 06.09).
`python TESIS/validar_tex.py` sigue siendo el chequeo rápido previo. Antes de
editar TESIS/ comprobar que los .tex conservan las ediciones anteriores (el
06.09 resumen.tex volvió a HEAD sin aviso y hubo que rehacerlo).

## HALLAZGO ABIERTO 06.09.2026 (noche): la referencia fija de corredor y red era débil

Un agente "jurado hostil" del workflow de verificación comprobó que `barrer_fijo.py`
solo barría UN verde común para avenida y transversales (más desfases), aunque la
avenida lleva 600–850 veh/h y las transversales 150–240. Con reparto asimétrico
25 s avenida / 10 s transversal / desfase 22 s, el fijo de corredor da 20.99 s en
las semillas 1001–1010 (contra 31.86 del 25/25 desplegado; reproducido). Frente a
ese fijo: IPPO vecinos −5.5 % (p=0.002), local +1.4 % n.s., actuado −0.4 %,
Q-learning +61 %. En red, con reparto tuneado, vecinos queda +1.0 a +1.9 % peor
que el fijo y local +3 %. En cruce, un plan por franja horaria (30/10 y 10/30
cambiando a los 30 min) deja a IPPO local en −1.8 % (pero eso es otra clase de
control, no un "tiempo fijo": decidir con Fabian/asesor si se añade como brazo).
CONSECUENCIA: la meta −25 % NO se cumple en corredor frente a un fijo bien
tuneado; la afirmación fuerte que sobrevive es "iguala/supera al actuado".
HECHO (06.09 noche): barridos asimétricos con semillas 2001–2003 (`--tmp
tmp_barrido_asim`; los simétricos viejos en `barrido_<esc>_simetrico_1001-1003.csv`).
- cruce `--asimetrico` (36 configs): el 25/25 desplegado ES el mejor → referencia
  del cruce intacta (barrido_cruce_asimetrico.csv).
- corredor (143 configs): mejor 20/10/off15 (20.5 s en tuneo; las 10 mejores
  llevan la transversal al mínimo de 10 s). Instalado en corredor.add.xml (el
  viejo en corredor_fijo_simetrico_25_25_off25.add.xml); fijo reevaluado con
  1001–1010 = 21.15 ± 0.41 s; el actuado reprodujo 20.911 dígito a dígito.
  Tablas/figuras regeneradas y TEXTO REESCRITO en capitulo4 (párrafo del baseline
  en 2 rondas, tab:escenarios, N6 del plan), capitulo5 (resumen de casos, P3,
  P3-U4, Nivel alcanzado N6, lectura conjunta, limitaciones), resumen, abstract,
  capitulo2, conclusiones 1/2/5/6/7/8 y una recomendación nueva ("barrer siempre el
  reparto de verde").
- red (321 configs): mejor 25/15 con los mismos desfases 0/23/0 = 21.51 s en tuneo
  (el 20/20 daba 22.18); instalado en red.add.xml (el viejo en
  red_fijo_simetrico_20_20_off23.add.xml); fijo reevaluado con 1001–1010 =
  21.78 ± 0.22 s (era 22.22); actuado reprodujo 21.422. Con el fijo nuevo: actuado
  −1.7 %, QL +15.3 %, IPPO local +1.8 % (p=0.02), IPPO vecinos +0.5 % n.s. (bases
  −0.5/−0.2/+0.5 %: EMPATE, antes −1.5 % significativo), spill −0.5 % n.s.; S1
  L5p30 +4.2 % y L10 +10.4 % frente al fijo. Texto de red reescrito en capitulo4
  (baseline, tab:escenarios, N6 del plan, motivación de U4), capitulo5 (resumen de
  casos, P4, P4-U4, canal imperfecto, N1/N3/N6, lectura conjunta), resumen,
  abstract, capitulo2, conclusiones 1/2/4/5/7/8, LEEME.

## DIAGNOSTICO DE ETAPA 07.09.2026: brechas verificadas antes de cerrar la tesis

Auditoria con 7 agentes (inventario de objetivos + completitud + ejecucion +
pendientes + coherencia, y dos analistas). Lo que sigue esta VERIFICADO abriendo
archivos, no es sospecha.

### A. Agujeros de evidencia en lo que el documento YA afirma (baratos y urgentes)

1. BASELINE EN EL BORDE DE LA MALLA. En `barrido_corredor.csv` el optimo es
   avenida 20 s y la malla barrida fue {20,25,30,35}: el ganador es el valor MAS
   BAJO. En `barrido_corredor_alta.csv` el optimo es 25 s con malla {25,30,35,40}:
   igual. Nunca se probaron verdes de avenida menores. red esta bien (gana 25 con
   malla {15,20,25,30}, interior). Es el MISMO error que se corrigio el 06.09.
   Accion: ampliar `malla` en barrer_fijo.py hacia abajo (corredor 12/15/18,
   corredor_alta 15/20) y re-barrer con 2001-2003. Si el optimo se mueve, hay que
   reinstalar el .add.xml, reevaluar con 1001-1010 y rehacer los deltas y el texto.
2. U2 NO TIENE CRITERIO DE PARADA NI SELECCION DE MODELO. Se reporta la Q-table
   del ULTIMO episodio. Evaluacion intermedia (semilla 999) ultima vs mejor:
   cruce ep40=21.4 / ep30=19.6; cruce2 ep120=179.0 / ep95=25.3; corredor
   ep40=30.1 / ep20=23.9; red ep100=24.8 / ep80=23.8; corredor_alta ep40=178.3 /
   ep5=155.5. El +60 % del corredor y el +17 % de cruce2 pueden ser artefacto del
   punto de corte. La semilla 999 es independiente de 1001-1010, asi que
   seleccionar el checkpoint por ella es seleccion de modelo legitima.
   Accion: guardar la Q-table en cada evaluacion intermedia, elegir por 999,
   reevaluar con 1001-1010 y declarar el criterio en capitulo4.
3. LA META SOLO SE CUMPLE CON UNA SEMILLA BASE. El -35 % de IPPO local en cruce
   sale de politica_cruce_local_s42.pt (60 ep, prueba de humo) y el propio plan
   dice "ningun resultado se cita con una sola semilla base". Esta en resumen,
   abstract, N6 y conclusion 7. Accion: entrenar bases 2042 y 4042 en cruce.
4. PRERREGISTRO NO DEMOSTRABLE. `git show 9fc0f8a:...capitulo4.tex` (06.09 00:07)
   NO contiene los niveles N; aparecen en 6e31e26 (06.09 19:08), despues de las
   politicas (10:59) y de evaluacion_corredor.csv (18:29) y evaluacion_red.csv
   (18:48). El documento dice "fijo siete niveles de exito antes de entrenar".
   Accion: suavizar la redaccion o separar lo que si tiene respaldo con fecha
   (los hiperparametros de la prueba de humo, en humo/).
5. TABLAS HUERFANAS: corredor_alta_evaluacion, corredor_alta_episodios_resumen,
   corredor_alta_s1, cruce_fragilidad, cruce_s1 se generan y NO tienen \input.
   Los numeros de corredor_alta (153.9/123.0/211.1) se citan en resumen, abstract
   y conclusion 1 sin tabla de respaldo. Accion: 10 minutos.
6. cruce2 es el unico fijo NO rebarrido en asimetrico, y su barrido uso 1001-1003,
   que son semillas de EVALUACION. Ya declarado en capitulo4 el 07.09.
7. spill en red = vecinos_s42 bit a bit (12 tensores y 10 filas identicos). Ya
   corregido en capitulo5 el 07.09.
8. PRECISION: `comun.archivo_actuado` lee el programa "0" del .net.xml y escribe
   offset=0, no el .add.xml tuneado. La estructura de fases coincide; las
   duraciones base y el desfase no. El texto dice "las mismas fases del programa
   fijo": conviene precisar "la misma estructura de fases de la red".

### B. Objetivos declarados que hoy NO se entregan (decidir con el asesor)

- Cruce real de Lima: no existe (.osm, red importada, aforos). Afecta al titulo,
  al objetivo general ("en Lima Metropolitana") y a la mitad de U1 ("Recopilar y
  preprocesar datos"), que introduccion.tex declara ejecutado.
- SARSA y DQN: cero lineas de codigo. El objetivo especifico U2 dice
  "implementar y comparar Q-learning, SARSA, DQN y PPO".
- MAPPO: cero lineas. U4 dice "variantes multiagente (IPPO/MAPPO)".
Para los tres: o se ejecutan o se corrige el alcance. Es decision de Fabian y el
asesor, no del codigo.

### C. Lo que le falta al documento como tesis (no como experimento)

- NO HAY HIPOTESIS ni pregunta de investigacion (grep sobre TESIS/*.tex: cero).
  Se aplican Wilcoxon, Mann-Whitney y Cliff sin enunciar que se contrasta.
- capitulo2.tex tiene CERO ecuaciones y el aporte central es IPPO: falta el MDP,
  el Dec-POMDP, el objetivo recortado de PPO y GAE.
- Estado del arte: 17 entradas en referencias.bib, 3 trabajos relacionados y
  NINGUNO de RL multiagente para semaforos (faltan CoLight, PressLight, MPLight,
  RESCO/Ault&Sharon, sumo-rl). El capitulo IV no cita ni una referencia.
- Diagrama.png y U1.png dibujan Azure/Google Maps/OD/SARSA/DQN/MAPPO y el flujo
  OSM->netedit, que no es lo construido.

### Orden recomendado
A1 y A2 primero (pueden cambiar numeros); luego A3, A5, A4, A6; despues la
decision de alcance (B); en paralelo C, que es el grueso de escritura que queda.
NO hacer antes de defender: llegadas aleatorias (rehace todos los numeros).

## Pendientes conocidos de la tesis

- Traer el cruce real de Lima (OSM limpio) a este pipeline y repetir las pruebas.
- SARSA, DQN y PPO (stable-baselines3) para la comparación algorítmica del cap. I.
- U4 (06.09.2026): etapas E0–E5 corridas y escritas en todo el documento. La
  cascada a zonas protegidas (resumen, abstract, introducción, capítulo 1) se
  hizo el 06.09 con autorización de Fabian: ya no queda texto que diga que U4
  está sin implementar, y el documento habla de CINCO escenarios (se sumó
  corredor_alta) y de dos algoritmos (Q-learning tabular e IPPO). Faltan: E6
  opcional (variante `cambio`, local en cruce2), entrenar con latencia/pérdida
  aleatorias (el agente no descuenta mensajes viejos), y MAPPO.
- La recompensa de U4 ya usa el retraso (timeLoss por segundo); U2 sigue con
  colas detenidas. Queda pendiente reentrenar Q-learning con la recompensa de
  retraso para aislar el efecto del algoritmo del de la recompensa.
- Varias semillas base de entrenamiento por escenario: U4 usa 3; U2 sigue con una.
- Decidir el ámbar: el documento fija 4 s como mínimo y los escenarios usan 3 s.
- Unificar la lista de algoritmos en el documento (capítulo 1 dice PPO, A2C y
  DQN; el resto Q-learning, SARSA, DQN y PPO; capítulo 4 menciona DDPG).
- Alcance: el documento promete un cruce real de Lima y hora punta/valle; hoy
  todo es sintético con demanda invertida. Corregir alcance o traer el cruce.
- Herramientas declaradas vs. reales: el documento nombra pandas, PyTorch, Docker
  y Gym; el código usa csv y TraCI directo, sin GPU.
