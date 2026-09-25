# Plan de pruebas v2 — especificación de implementación (24.09.2026)

Aprobado por el asesor (correo del 23.09): desarrollar los casos P1–P4 como mínimo, P5 si se
puede, con el MISMO método en cada configuración y las MISMAS métricas de salida, y subir los
resultados a la plantilla. Reunión: 25.09.2026, 8:00. Este archivo es el contrato entre todos los
que tocan el código esta noche. Si algo no está aquí, se decide a favor de lo más simple que no
rompa la reproducibilidad de lo ya hecho.

## 0. Reglas de convivencia (obligatorias)

- Código en `demo_rl/*.py` (se edita en el lugar). Cada archivo tiene UN dueño (sección 9). No
  edites archivos de otro dueño; si necesitas algo de ellos, usa la interfaz de esta especificación.
- Todas las corridas del plan v2 se ejecutan con **directorio de trabajo `demo_rl/plan2/`**:
  `cd demo_rl/plan2 && python ../rl_corredor.py ...`. Los scripts usan rutas relativas al cwd, así
  que todas las salidas quedan en `plan2/` y los resultados del 06.09 en `demo_rl/` no se tocan.
- Pruebas propias: en una COPIA privada (`<scratchpad>/<tu_nombre>/`) con los .py y los archivos
  de escenario que necesites. Nunca corras pruebas dentro de `demo_rl/` ni de `demo_rl/plan2/`.
- No hagas commits. No toques `TESIS/` salvo que seas el dueño de TESIS.
- Estilo: español, sin tildes en identificadores, código simple y legible (va al anexo de la
  tesis). Líneas <= 110 caracteres. Solo caracteres Latin-1 en .py.
- Todo proceso de entrenamiento con torch: `torch.set_num_threads(1)` (ya lo hace
  `rl_ippo.sembrar`). La cola exporta `OMP_NUM_THREADS=1`.
- En modo train el CSV `resultados_<tag>.csv` se REESCRIBE desde cero (no se anexa): la cola puede
  reintentar un trabajo y no deben quedar filas duplicadas. Los checkpoints de una corrida anterior
  con el mismo tag se borran al empezar.
- Al terminar y pasar tus compuertas, crea la bandera `demo_rl/plan2/listo/<nombre>.ok` (texto:
  qué probaste). La cola de trabajos arranca sola lo que depende de tu bandera. NO crees la
  bandera si una compuerta falla.

## 1. Casos (celdas) y escenarios

| Caso | escenario (id) | Semáforos | Carriles por sentido (avenida) | Demanda |
|---|---|---|---|---|
| P1 | `corredor` | 2 | 1 | 1.0x (existe) |
| P2 | `corredor_alta` | 2 | 1 | 2.0x (existe) |
| P3 | `red` | 3 + rotonda | 2 | 1.0x (existe) |
| P4 | `red_alta` | 3 + rotonda | 2 | factor calibrado (nuevo) |
| P5 | `malla3` | 9 | 2 | 1.0x (nuevo) |

Escenarios nuevos se registran en `demo_rl/escenarios_plan2.py` (dueño: escenarios):
- `ESCENARIOS_RC`: dict con el formato de `rl_corredor.ESCENARIOS` (cfg, semaforos: tls ->
  [aprox oeste, aprox este, aprox norte, aprox sur], enlaces: lista de edges internos entre
  semáforos, flujos_corredor: ids de flows que recorren la avenida de punta a punta o None).
- `VECINOS`: dict con el formato de `rl_ippo.VECINOS`; para malla3 cada tls tiene cuatro lados
  `oeste, este, norte, sur` con `(vecino, enlace_vecino_a_mi, enlace_mi_a_vecino)` o `None`.
- `LADOS`: dict escenario -> tupla de lados (`("oeste","este")` o `("oeste","este","norte","sur")`).
`rl_corredor.py` hace `ESCENARIOS.update(escenarios_plan2.ESCENARIOS_RC)` y `rl_ippo.py` hace lo
mismo con VECINOS/LADOS. El stub vacío ya existe; el dueño de escenarios lo llena.

Convención de ejes: la "avenida" es el eje este-oeste (EO) en todos los escenarios; norte-sur (NS)
es la transversal. En malla3 las dos direcciones tienen 2 carriles, pero la convención se mantiene.

## 2. Modelos

| Etiqueta `alg` | Qué es | Script | Recompensa de entrenamiento |
|---|---|---|---|
| `fijo` | tiempo fijo tuneado por barrido en ESA celda | rl_corredor baseline | — |
| `actuado` | actuado nativo SUMO (minDur 10 / maxDur 60) | rl_corredor actuado | — |
| `ql` | Q-learning tabular, un agente por semáforo | rl_corredor train --algoritmo qlearning --recompensa retraso | retraso |
| `sarsa` | SARSA tabular | rl_corredor train --algoritmo sarsa --recompensa retraso | retraso |
| `ql_colas` | Q-learning con la recompensa original de U2 (ablación) | rl_corredor ... --recompensa colas | colas |
| `ippo_local` | IPPO sin mensajes | rl_ippo --variante local | retraso |
| `ippo_vecinos` | IPPO con mensajes | rl_ippo --variante vecinos | retraso |
| `ippo_spill` | IPPO con mensajes + término de spillback | rl_ippo --variante spill | retraso + spill |
| `dqn` | Double DQN con pesos compartidos, misma observación que ippo_vecinos | rl_dqn.py | retraso |
| `mappo` | actor como ippo_vecinos + crítico centralizado | rl_mappo.py | retraso |

**Recompensa "retraso"** (la misma para todos los aprendices, igual a la de U4 hoy): cada segundo
se acumula por semáforo `r_paso = -(W1 * retraso_base + W2 * espera)`, con
`retraso_base = sum_a n_a * (1 - v_media_a / vmax_a)` sobre sus aproximaciones y `espera` la
suma de `getWaitingTime` de sus aproximaciones (W1=1.0, W2=0.01). La recompensa de una decisión
es la suma de `r_paso` desde la decisión anterior dividida entre 5. Es exactamente
`rl_ippo.recompensa_paso`; en tabular NO se multiplica por ESCALA_R. **"colas"** = recompensa
actual de U2 (`rl_corredor.recompensa`, en el instante de decisión). **"retraso + spill"** = la de
`rl_ippo` variante spill (W3 = 2.0 por vehículo detenido sobre la mitad de las plazas del enlace
que sale hacia un vecino).

## 3. Protocolo común (igual para todos los aprendices, en todas las celdas)

- Semillas base 42, 2042, 4042; episodio k usa la semilla SUMO `base + k`.
- 200 episodios. Validación cada 10 episodios (y en el último) con la política congelada (greedy /
  argmax) en las semillas **999 y 1999**; `val = media(val_999, val_1999)` del timeLoss medio.
  La validación NO debe alterar el RNG del entrenamiento (guardar y restaurar random / numpy /
  torch) — el entrenamiento tiene que reproducir el mismo CSV dígito a dígito con o sin validación.
- **Checkpoint** en cada validación: `plan2/checkpoints/<tag>_ep<NNN>.json|.pt`.
- **Política publicada** = checkpoint con el menor `val` (empate: el más tardío). Se escribe con
  el nombre de política de la sección 4 y su meta registra `ep_elegido`, `val_elegido`,
  `val_serie` = lista de `[ep, val_999, val_1999, val]`, `val_seeds`, `algoritmo`, `recompensa`,
  `base`, `episodios`, `escenario`, `git` y los hiperparámetros.
- Tabular: `EPS_INICIAL 1.0`, decaimiento geométrico por episodio `0.01 ** (1 / (0.8 * episodios))`
  (llega a 0.01 al 80 % de los episodios), `EPS_MIN 0.01`, `ALPHA 0.1`, `GAMMA 0.9`. Se puede
  seguir pasando `--eps-decay` explícito para reproducir corridas viejas.
- IPPO: hiperparámetros congelados de siempre (HIPER). DQN y MAPPO: los que fije su dueño tras la
  prueba de humo en `cruce`, registrados en el meta y en el docstring.
- Barrido del fijo en CADA celda con semillas **2001–2003**, malla abierta hasta que el óptimo sea
  interior (el verde mínimo 10 s es un piso válido), y el ganador se instala en `plan2/<esc>.add.xml`.
- Evaluación final: política congelada, semillas **1001–1030**, las mismas para todos los brazos.
  Se evalúan TODAS las bases (para la tabla de fragilidad).
- **Base publicada de cada (modelo, celda)** = la mediana de las tres bases por `val_elegido`.
  NUNCA se elige con las semillas 1001–1030.

## 4. Nombres de archivos (en `plan2/`)

`tag` = `<esc>_<alg>_s<base>` (p. ej. `red_ql_s42`, `malla3_ippo_vecinos_s2042`, `red_alta_dqn_s42`).

| Qué | Nombre |
|---|---|
| CSV de entrenamiento | `resultados_<tag>.csv` |
| checkpoints | `checkpoints/<tag>_ep<NNN>.json` (tabular) o `.pt` |
| política publicada tabular | `q_table_<tag>.json` + `q_table_<tag>.meta.json` |
| política publicada IPPO | `politica_<esc>_<var>_s<base>.pt` + `.json` (como hoy) |
| política publicada DQN / MAPPO | `politica_<esc>_dqn_s<base>.pt` / `politica_<esc>_mappo_s<base>.pt` + `.json` |
| tripinfo | SIEMPRE único por corrida: `tripinfo_<tag>_train.xml`, `tripinfo_<tag>_val.xml`, y en evaluar `tripinfo_eval_<esc>_<brazo>_<pid>.xml` |
| evaluación parcial | `parciales/eval_<esc>_<brazo>.csv` |
| evaluación consolidada | `evaluacion_<esc>.csv`, `evaluacion_<esc>_resumen.csv` |
| veredicto | `veredicto.csv`, `veredicto.md`, y `TESIS/secciones/tablas/veredicto_*.tex` |

Nombre de brazo en evaluación: `fijo`, `actuado`, `<alg>_s<base>` (p. ej. `ql_s42`,
`ippo_spill_s4042`, `dqn_s2042`).

## 5. Columnas que TODA corrida devuelve (entrenamiento y evaluación, todos los modos)

Las de hoy (`comun.leer_tripinfo` + cola_prom, cola_max, recompensa, recompensa_decision,
decisiones, cambios_fase, spillback y enlaces del MedidorEnlaces) **más tres retornos medidos cada
segundo durante todo el episodio y sobre todos los semáforos**, igual en fijo, actuado y cualquier
aprendiz:
- `ret_retraso` = suma de `r_paso` (recompensa "retraso").
- `ret_colas` = suma por segundo de `-(W1 * detenidos + W2 * espera)` (la de U2 a reloj de 1 s).
- `ret_spill` = `ret_retraso - W3 * suma_t suma_enlaces max(0, max_halting(enlace) - plazas(enlace) // 2)`.
Leer VEH, VEL, ESP y HALT con suscripciones TraCI (como `rl_ippo.suscribir/lecturas`) para no
multiplicar las llamadas.

CSV de entrenamiento: además `segundos` (reloj del episodio), `val_999`, `val_1999`, `val`
(solo en filas de validación), `algoritmo`, `recompensa`, `base`. En IPPO se conserva
`eval_timeloss` (= val_999) por compatibilidad.

## 6. evaluar.py y consolidar.py (interfaz)

```
python ../evaluar.py --escenario E --brazo fijo|actuado --semillas 1001-1030 --salida parciales/eval_E_fijo.csv
python ../evaluar.py --escenario E --politica q_table_<tag>.json --semillas 1001-1030 --salida parciales/eval_E_<brazo>.csv
python ../evaluar.py --escenario E --politica politica_<esc>_<var>_s<base>.pt --semillas ... --salida ...
python ../consolidar.py --escenario E
```
- evaluar.py decide el tipo por la extensión y el meta: `.json` tabular -> `rl_corredor` modo demo;
  `.pt` con meta `algoritmo` ausente o `ippo` -> `rl_ippo` demo con su `variante`; `dqn` -> `rl_dqn`;
  `mappo` -> `rl_mappo`. Conserva el modo antiguo (`--brazos`, `--ippo`) si no estorba.
- Filas de salida: `brazo, modelo, base, semilla` + todas las métricas de la sección 5.
- consolidar.py lee `parciales/eval_E_*.csv`, escribe `evaluacion_E.csv` y
  `evaluacion_E_resumen.csv`: por brazo y métrica `n, media, sd, ic95`; frente a `fijo` y frente
  a `actuado` (para TODOS los brazos salvo esos dos): `delta_pct, delta_ic95` (bootstrap pareado por
  semilla, 10 000 remuestreos, rng 0) y `p_wilcoxon` (pareado), sufijo `_act` para el actuado.
  **El emparejamiento es por semilla** (solo semillas comunes; registrar `n_par`), no por posición.
  Para las métricas `ret_*` (negativas) el delta se calcula sobre `|media_ref|`, de modo que
  delta positivo = mejor recompensa; documentarlo en el docstring.

## 7. Regla de veredicto (la que aprobó el asesor; veredicto.py la aplica)

Con Δf = delta % del retraso (`timeloss_prom`) frente al fijo, su IC95 y p; Δa lo mismo frente al actuado:
- **FUNCIONA**: IC95 de Δf entero < 0, p < 0.05, Δf <= −5 % y NO (IC95 de Δa entero > 0 y p_act < 0.05).
- **MEJORA**: IC95 de Δf entero < 0 y p < 0.05, pero Δf > −5 % o pierde contra el actuado de forma significativa.
- **FALLA**: IC95 de Δf entero > 0 y p < 0.05.
- **EMPATA**: en otro caso.
- **PENDIENTE**: la celda no está completa, o la base publicada no convergió → se escribe
  `pendiente (no convergió; provisional: X)`.
Convergencia sobre la serie `val` de la base publicada, último tercio de las validaciones:
`plateau` = pendiente de la regresión lineal * (episodios / 3) / media del tercio * 100;
`estabilidad` = (media de las 3 últimas − mínimo de la media móvil de 3) / ese mínimo * 100;
convergió si |plateau| <= 5 y estabilidad <= 5. Se reporta también k/3 bases que convergen.
Columna Δ recompensa: delta de la recompensa PROPIA del modelo (`ret_retraso`, `ret_colas` o
`ret_spill` según la tabla de la sección 2) frente a esa misma recompensa medida en el fijo.
El actuado aparece como fila de referencia con su veredicto frente al fijo.

## 8. Cola de trabajos

`plan2/cola.py` corre `plan2/cola/trabajos.jsonl` con prioridades y dependencias (banderas en
`plan2/listo/` y trabajos terminados). Logs en `plan2/cola/logs/<id>.log`, estado en
`plan2/cola/estado.json`. Los comandos exactos que va a lanzar están en `plan2/generar_trabajos.py`:
tu CLI tiene que aceptar exactamente esos argumentos.

## 9. Dueños

| Dueño | Archivos | Bandera |
|---|---|---|
| escenarios | escenarios_plan2.py, red_alta.*, malla3.*, build_net.bat | escenarios_red_alta.ok y escenarios_malla3.ok (una por escenario, en cuanto cada uno este listo) |
| tabular | rl_corredor.py | tabular.ok |
| ippo | rl_ippo.py | ippo.ok (escenarios de dos lados: corredor, corredor_alta, red, red_alta) y ippo_malla.ok (malla3) |
| evaluacion | evaluar.py, consolidar.py, comun.py (solo funciones nuevas al final del archivo) | evaluar.ok |
| barrido | barrer_fijo.py | barrer.ok (corredor, corredor_alta, red, red_alta) y barrer_malla.ok (malla3) |
| dqn | rl_dqn.py (nuevo) | dqn.ok |
| mappo | rl_mappo.py (nuevo) | mappo.ok |
| veredicto | veredicto.py (nuevo) | veredicto.ok |
| tesis | TESIS/ (solo lo que se le pida) | — |
| orquestador | plan2/cola.py, plan2/generar_trabajos.py, plan2/ESPEC.md | — |

Si necesitas una función compartida en comun.py y no eres su dueño, ponla en tu propio archivo.
