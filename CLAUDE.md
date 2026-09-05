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

## Comandos

```
python rl_semaforo.py baseline [--escenario cruce|cruce2] [--gui]
python rl_semaforo.py train    [--escenario cruce|cruce2] --episodios 40
python rl_semaforo.py demo     [--escenario cruce|cruce2] --gui
python rl_corredor.py baseline|train|demo [--escenario corredor|red] [--gui]
python graficar.py [cruce|cruce2|corredor|red]           # curva_aprendizaje_<esc>.png
```

Salidas por escenario: `q_table_<esc>.json`, `resultados_<esc>.csv`,
`tripinfo_<esc>_<modo>.xml`, `curva_aprendizaje_<esc>.png`.

## Resultados validados (semilla 42; detalles y notas en LEEME.txt)

| Escenario | Tiempo fijo (tuneado) | Q-learning (demo greedy) | Δ espera |
|---|---|---|---|
| cruce (40 ep) | 9.3 s/veh | 6.4 s/veh | −31 % |
| cruce2 (120 ep, eps-decay 0.96) | 16.0 s/veh | 18.0 s/veh | +13 % (peor) |
| corredor (40 ep, 2 agentes) | 14.0 s/veh | 10.3 s/veh | −27 % |
| red (60 ep, eps-decay 0.95, 3 agentes) | 7.4 s/veh (onda verde) | 8.3 s/veh | +13 % (peor) |

Advertencia (verificado el 04.09.2026 con 5 y 10 semillas): estos Δ son de espera
detenida (waitingTime) y de una sola semilla. En timeLoss, que es el "retraso" de
las metas, cruce no mejora (23.0 vs 23.0 s/veh), el agente sube las paradas por
vehículo +36 % y el actuado nativo de SUMO con las mismas restricciones gana al
Q-learning por ~50 %. No citar el −31 % como retraso. Los números de esta
advertencia se midieron en corridas fuera del proyecto (scratchpad de la sesión
del 04.09.2026) y todavía no se regeneran con ningún script del proyecto: son
provisionales hasta que exista la evaluación por semillas del plan de pruebas
(skill escribir-tesis, sección 6), y no van al documento antes de eso.

Reglas y lecciones que salieron de estas corridas:
- Los baselines NO son débiles a propósito: verde barrido por escenario, y en el
  corredor también el offset entre semáforos (0→25 s bajó la espera de 22.4 a
  14.0). Tunear igual antes de comparar cualquier escenario nuevo.
- cruce2 es el hallazgo: el Q-learning tabular toca techo con 4 fases (1024
  estados; la política greedy cae en estados poco visitados). Es el argumento
  empírico para DQN/PPO en U2. No insistir con: γ=0.95 (sobreestimación,
  inestable entre semillas), desempate "mantener fase" (retiene 60 s y es peor),
  ni más episodios sin cambiar la representación.
- red es el otro hallazgo: agentes independientes ganan −59 % contra un fijo sin
  coordinar, pero pierden +13 % contra la onda verde tuneada de 3 cruces — la
  coordinación anticipada vale más que la reacción local cuando hay varios
  semáforos consecutivos. Es la evidencia empírica que motiva U4.
- El RNG se siembra en TODOS los modos (el desempate de acciones usa random);
  los demos son deterministas por semilla. La corrida original de cruce
  (9.4→5.9, −38 %) no era reproducible con el código actual; su q_table quedó
  respaldada en q_table_cruce_original.json.

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

Antes de editar `TESIS/`: confirmar que la copia local está al día con Overleaf,
respaldar `main.tex`, `referencias.bib` y `secciones/` en
`respaldo_tesis/<fecha_hora>/`, y que ninguna otra sesión esté editando. Al
terminar: diff contra el respaldo y lista de archivos a resubir. Resumen,
abstract, metas y objetivos, capítulo 1 y los captions del autor solo se cambian
de contenido con confirmación previa; `tesisutec.cls` y los paquetes de
`main.tex` no se tocan.

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
No hay repositorio git. Sin LaTeX local: la tesis se compila en Overleaf y los
.tex se revisan con `python TESIS/validar_tex.py`.

## Pendientes conocidos de la tesis

- Traer el cruce real de Lima (OSM limpio) a este pipeline y repetir las pruebas.
- SARSA, DQN y PPO (stable-baselines3) para la comparación algorítmica del cap. I.
- Métricas U3 faltantes: throughput, paradas/veh, emisiones (CO2, NOx).
- Análisis estadístico: varias semillas, IC95 %, Mann–Whitney.
- U4 real: estado extendido con vecinos, mensajería y penalización por spillback
  (rl_corredor.py usa agentes independientes, todavía sin comunicación).
- Alinear `capitulo4.tex` (U2) con el código: decisión cada 5 s, traci.start y
  close por episodio, estado con índice de fase, schedule de ε, verde mín/máx,
  definición de episodio y por qué 40 (lista completa en el skill escribir-tesis).
- Escribir el plan de pruebas (capitulo4.tex) y los resultados (capitulo5.tex,
  hoy vacío) con evaluación por semillas, IC95 % y actuado como tercer brazo;
  agregar el script de evaluación por semillas y las columnas de semilla,
  paradas, throughput y CO2 al CSV.
- Re-barrer los baselines fijos por timeLoss (se tunearon por espera detenida).
- Decidir el ámbar: el documento fija 4 s como mínimo y los escenarios usan 3 s.
- Unificar la lista de algoritmos en el documento (capítulo 1 dice PPO, A2C y
  DQN; el resto Q-learning, SARSA, DQN y PPO; capítulo 4 menciona DDPG).
- Alcance: el documento promete un cruce real de Lima y hora punta/valle; hoy
  todo es sintético con demanda invertida. Corregir alcance o traer el cruce.
- Herramientas declaradas vs. reales: el documento nombra pandas, PyTorch, Docker
  y Gym; el código usa csv y TraCI directo, sin GPU.
