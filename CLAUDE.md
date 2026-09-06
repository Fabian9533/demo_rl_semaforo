# demo_rl — Semáforos adaptativos con RL sobre SUMO (tesis UTEC)

## Contexto

Tesis de bachiller en Ciencia de la Computación (UTEC): "Optimización del tráfico
urbano en Lima con semáforos inteligentes mediante Aprendizaje por Refuerzo (RL) y
simulación en SUMO". Autores: Fabian Alvarado y Neftalí Calixto. Asesor: José
Antonio Fiestas Iquira. Curso actual: Tesis 2 (2026-II). El documento fuente
está en `TESIS/` (LaTeX, plantilla UTEC, se compila en Overleaf; `TESIS (12).pdf`
es solo una copia de septiembre 2026). Conclusiones, Recomendaciones y Anexos
siguen siendo placeholders; lo escrito de verdad llega hasta el módulo U2 del
capítulo III (archivo `capitulo4.tex`).

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

Esta carpeta es la prueba de concepto de U2+U3 sobre cruces SINTÉTICOS. El cruce
real de Lima (importado de OSM y limpiado en netedit, capítulo III) es un archivo
aparte que aún no está aquí.

## Escenarios

| Escenario | Archivos | Descripción |
|---|---|---|
| cruce | `cruce.*` | Prueba 1: cruce N-S/E-O, 1 carril por sentido, semáforo `semaforo_C` de 2 fases verdes. Demanda invertida a mitad de hora (0–1800 s punta N-S, 1800–3600 s punta E-O). |
| cruce2 | `cruce2.*` | Prueba 2: mismo cruce con 2 carriles por sentido, carril exclusivo de giro a la izquierda y fases de giro protegido (4 fases verdes). |
| corredor | `corredor.*` | Prueba 3: dos cruces (`semaforo_C1`, `semaforo_C2`) sobre una avenida E-O separados 300 m, un agente Q-learning independiente por cruce (antesala de U4). |
| red | `red.*` | Prueba 4: rotonda sin semáforo (prioridad del anillo) + tres cruces semaforizados sobre una avenida de 2 carriles por sentido muy cargada; transversales ligeras. Tres agentes independientes. |

Las redes `.net.xml` se regeneran con `build_net.bat` solo si se editan los
`.nod.xml` / `.edg.xml` / `.con.xml`.

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

## Comandos

```
python rl_semaforo.py baseline|actuado|train|demo [--escenario cruce|cruce2] [--gui]
python rl_semaforo.py train --escenario cruce --episodios 40 --desde-cero   # eval greedy cada 5 ep
python rl_corredor.py baseline|actuado|train|demo [--escenario corredor|red] [--gui]
python evaluar.py --escenario <esc>        # fijo, actuado y RL con semillas 1001-1010 + estadistica
python barrer_fijo.py <esc>                # barrido del programa fijo por retraso
python graficar.py <esc>                   # fig_<esc>_curva|comparacion|serie|ecdf|qtable.png
python tablas_tex.py                       # tablas LaTeX en TESIS/secciones/tablas/
```
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
| corredor (40 ep, 2 agentes) | 31.9 s | 20.9 s | 33.9 s | +6.3 % [+1.3, +11.0], p=0.037 | −34 % |
| red (100 ep, decay 0.95, 3 agentes) | 22.2 s | 21.4 s | 25.1 s | +13.1 % [+12.0, +14.1], p=0.002 | −4 % |

Secundarias del RL vs fijo (cruce / cruce2 / corredor / red): espera −26 / +18 /
−13 / +4 %; paradas +27 / +23 / +49 / +74 %; CO2 −1.5 / +4 / +1 / +5 %.
Throughput no discrimina (demanda subsaturada). Metas cumplidas por el RL:
retraso −25 % en ninguno; colas −20 % solo en cruce y solo en la media; CO2 −5 %
en ninguno. Los números viejos de una semilla (−31 % de espera en cruce, etc.)
quedaron en `resultados_<esc>_v1.csv`; los de la corrida con el reloj de decisión
desfasado (corredor −19 %, red +23 %) en `resultados_<esc>_v2.csv`. Ninguno se cita.

Reglas y lecciones que salieron de estas corridas:
- Los baselines NO son débiles: verde y offsets barridos por escenario, y el
  barrido por retraso (`barrer_fijo.py`, `barrido_<esc>.csv`) confirmó los
  valores actuales. Tunear igual antes de comparar cualquier escenario nuevo, y
  comparar siempre también contra el actuado, que gana al RL en los cuatro casos.
- El agente mejora la espera detenida mucho más que el retraso porque eso es lo
  que penaliza la recompensa; cambia de fase ~77 % más que el fijo y sube las
  paradas. Alinear la recompensa con el retraso (penalizar cambios de fase o
  incluir timeLoss) es un cambio de formulación pendiente, que exige actualizar
  código y capitulo4.tex a la vez.
- cruce2 es el hallazgo del techo tabular: 1024 estados, el agente visita 390 y la
  política greedy cae en estados poco visitados; la evaluación intermedia se
  estanca, más episodios no ayudan. Argumento empírico para DQN/PPO. No insistir
  con γ=0.95 (inestable) ni con desempate "mantener fase".
- red es el hallazgo de coordinación: tres agentes independientes pierden +13 %
  contra la onda verde tuneada (y ganarían por mucho al mismo fijo sin desfases,
  41.6 s) y la evaluación intermedia se estanca en 24–25 s desde el episodio 5.
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
Validar siempre con `python TESIS/validar_tex.py` (no hay LaTeX local; el
usuario compila en Overleaf). Numeración: `capitulo4.tex` es el Capítulo III y
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

Windows 10, SUMO 1.25 (SUMO_HOME definido, binarios en PATH), Python 3.14 con
traci, sumolib, matplotlib, numpy, scipy, pypdf (sin pandas). Sin GPU asumida.
Repositorio git local (rama `main`, desde el 05.09.2026); los commits los hace
Fabian salvo que pida lo contrario. `respaldo_tesis/` fue el respaldo manual
previo al git y se puede borrar cuando Overleaf compile bien. Sin LaTeX local: la
tesis se compila en Overleaf y los .tex se revisan con
`python TESIS/validar_tex.py`.

## Pendientes conocidos de la tesis

- Traer el cruce real de Lima (OSM limpio) a este pipeline y repetir las pruebas.
- SARSA, DQN y PPO (stable-baselines3) para la comparación algorítmica del cap. I.
- U4 real: estado extendido con vecinos, mensajería y penalización por spillback
  (rl_corredor.py usa agentes independientes, todavía sin comunicación).
- Alinear la recompensa con la métrica primaria (penalizar cambios de fase o
  incluir timeLoss): cambio de formulación, actualizar código y capitulo4.tex.
- Varias semillas base de entrenamiento por escenario (hoy una sola corrida).
- Conclusiones y recomendaciones de la tesis siguen vacías; el capítulo IV
  (capitulo5.tex) ya tiene resultados de los cuatro casos.
- Decidir el ámbar: el documento fija 4 s como mínimo y los escenarios usan 3 s.
- Unificar la lista de algoritmos en el documento (capítulo 1 dice PPO, A2C y
  DQN; el resto Q-learning, SARSA, DQN y PPO; capítulo 4 menciona DDPG).
- Alcance: el documento promete un cruce real de Lima y hora punta/valle; hoy
  todo es sintético con demanda invertida. Corregir alcance o traer el cruce.
- Herramientas declaradas vs. reales: el documento nombra pandas, PyTorch, Docker
  y Gym; el código usa csv y TraCI directo, sin GPU.
