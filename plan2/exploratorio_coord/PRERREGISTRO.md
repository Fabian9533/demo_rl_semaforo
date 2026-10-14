# Pre-registro coord2: ¿se puede mejorar la coordinación de IPPO vecinos? (tandas 1 y 2)

Fecha de fijación: 2026-09-28, ANTES de correr cualquier entrenamiento de este diseño. El sha256 de este
archivo está en `coord2/prerregistro.sha256`. Todo cambio posterior se declara como **desviación** en
`coord2/DESVIACIONES.md` (con fecha, motivo y efecto), nunca editando este archivo.

Alcance: estudio **exploratorio, fuera del protocolo de examen**. No cambia el veredicto pre-registrado del
25.09 (P1-P3 FUNCIONA, P4 MEJORA −3.6 %, P5 EMPATA, P6 PENDIENTE +2.2 %) ni toca `demo_rl/`, `plan2/`,
`veredicto.csv` ni la TESIS. Todo vive en `coord2/` (ruta completa:
`C:/Users/GAMER/AppData/Local/Temp/claude/c--Users-GAMER-Documents-demo-rl-semaforo/f9bfbde2-8203-4939-a98b-d24c9ff05662/scratchpad/coord2/`).
**Semillas 1001-1030 PROHIBIDAS** (examen): todo script de simulación lleva `assert not 1001 <= s <= 1030`.

---

## 1. Evidencia de partida (lo que motiva cada brazo)

Todas las cifras salen de archivos existentes; entre paréntesis, el archivo (rutas relativas a
`mejora_coord/` o `coord2/`).

| # | Hallazgo | Cifra | Archivo |
|---|---|---|---|
| E1 | El descuento de `gae()` es **por decisión** (γ = 0.95 cada decisión), no por segundo. Con él la política aprendida parece mejor que el trivial aunque cueste más por segundo | P4, val8: ippo_s42 frente al trivial: timeLoss +4.8 %, costo local por segundo L_loc +8.5 % (8/8 semillas prefieren el trivial), J_seg +8.4 % (8/8), pero J_dec −1.5 % (7/8 prefieren ippo). clon42_ep100: J_dec −1.7 % con timeLoss +6.6 % | `coord2/salidas/c4_alineacion.txt` |
| E2 | La exploración **independiente** rompe la sincronía del ciclo mínimo; la **común** (un sorteo por segundo) casi no | P4, trivial val8 27.08 s: 3 % de inversiones independientes → 32.96 (+21.7 %); comunes 3 % → 27.39 (+1.2 %); comunes 10 % → 29.14 (+7.6 %). P6, 15/10: independiente 3 % +14.7 %, común 3 % +2.1 % | `coord2/b2_ruido.txt` |
| E3 | Aun explorando un solo semáforo, el daño sigue | P4 +12.6 %, P6 +9.1 % (eps 0.03) | `coord2/b3_ruido_uno.txt` |
| E4 | La entropía final de IPPO vecinos es justo el régimen dañino | P4 p≈1.3-1.6 % de acción minoritaria; P6 p≈3.7-4.0 % | `coord2/b6_entropia_a_p.txt` |
| E5 | Las colas entran con escala casi nula | P4: p95 de la cola 0.026 (≈2 veh), sensibilidad de la 1.ª capa del actor: colas 2.8 %, móviles 5.0 %, mensajes 49.2 %. Con 10 veh/carril: p95 0.100 (colas) y 0.400 (móviles) | `coord2/salidas/c2_escalas_obs.txt` |
| E6 | La recompensa local cubre la mitad del timeLoss de P4; la entrada de la rotonda SR_RS pesa y depende del control | Aproximaciones 48-50 % del total; SR_RS 16 904 (trivial), 18 128 (ippo_s42), 19 755 (fijo2509) veh·s; explica +1224 de los +3373 veh·s que ippo_s42 pierde frente al trivial | `coord2/salidas/c6_edges_no_cubiertos.txt`, `c4_alineacion.txt` (f) |
| E7 | El criterio más alineado con el timeLoss es el costo de toda la red con descuento por segundo | Spearman con timeLoss (12 programas): J_red_seg 0.993, J_seg 0.944, J_dec 0.916 | `coord2/salidas/c4_alineacion.txt` |
| E8 | El crítico central de MAPPO no aporta con recompensa local | EV 0.800 (MAPPO) frente a 0.806 (IPPO) en P4; residuo no predecible (R2 ≤ 0.03) | `c4_alineacion.txt` (c), `coord2/salidas/c5_critico_residuo.txt` |
| E9 | La selección con 2 semillas es ruidosa | Spearman val2 frente a 6001-6010: 0.28 (P4), 0.34 (P6); SE de un checkpoint en P4 1.34 s con 2 semillas y 0.67 s con 8 | `mejora_coord/salidas/checkpoints_*.txt`, `coord2/b7_se_val.txt` |
| E10 | Partir del trivial sin corregir nada no basta: PPO se aleja | p4_clon_trivial: val media ep 150-200 +10.7 a +13.2 % frente al clon; cambios/ep 790-830 → 549-605 | `mejora_coord/p4_clon_trivial/salidas/deriva.txt` |
| E11 | Techo y referencias en P4 (5001-5030) | fijo_2509 30.064, actuado 29.674, IPPO vecinos s42 28.925 (−3.8 %), trivial 28.152 (−6.4 % [−8.4, −4.3]) | `mejora_coord/p4_clon_trivial/salidas/juicio.txt`, `mejora_coord/salidas/referencias_piloto_5001_5030.txt` |
| E12 | Reglas adaptativas simples y desfases no le ganan al trivial | b4b: 0/8 semillas en casi todas las reglas (la mejor +2.2 %); b5: ningún desfase mejora de forma robusta (mejor +0.3 %, 3/8) | `coord2/b4b_conjunta.txt`, `coord2/b5_desfases_red_alta.txt` |

Referencias en val8 (semillas declaradas abajo), P4: trivial 27.08, fijo2509 30.46, ippo_s42 28.38
(`coord2/salidas/c4_alineacion.txt`). Nota: el "val8" de `mejora_coord` (a9, a12) usaba 5999 y 6999 en lugar
de 8999 y 9999; aquí manda el conjunto de coord2.

Integridad de b2/b3 tras el incidente del `taskkill /F /IM sumo.exe` (13:38): las 5+3 filas de P4 y P6
tienen las 8 semillas con valor, y la fila eps=0.00 reproduce el trivial (27.08) y el 15/10 (36.57). Se
consideran completas. **Regla de esta tanda: nunca matar sumo por nombre de imagen, solo por PID.**

---

## 2. Diseño común (idéntico para el control y las variantes)

| Elemento | Valor fijado |
|---|---|
| Caso de la tanda 1 | P4 `red_alta` (3 semáforos, dim_obs 31) |
| Bases | 42, 2042, 4042; episodio k usa la semilla SUMO base + k (43-242, 2043-2242, 4043-4242) |
| Episodios | 200 |
| HIPER | los de `rl_ippo.HIPER` sin cambios: γ 0.95, λ 0.95, clip 0.2, 10 épocas, minilote 64, lr 1e-3 lineal a 0, entropía 0.01, valor 0.5, recorte 0.5 por red; ESCALA_R 0.02; OCULTAS 64 |
| Validación | política congelada (argmax), cada 10 episodios y en el último (20 puntos: ep 10, 20, ..., 200), con **8 semillas declaradas: 999, 1999, 2999, 3999, 4999, 7999, 8999, 9999** (`--val-seeds`). `validar()` guarda y restaura el RNG, así que el entrenamiento no depende de cuántas semillas se validen |
| Checkpoint publicado por base | el de menor val8 (empate: el más tardío), `rl_ippo.elegir_checkpoint`. **El ep 0 no es candidato** |
| Base publicada | mediana de val_elegido de las 3 bases (`veredicto.base_mediana`) |
| Convergencia | `veredicto.convergencia` sobre la serie val8 de la base publicada: último tercio, \|plateau\| ≤ 5 % y estabilidad ≤ 5 % |
| Evaluación (cribado) | semillas 5001-5030, argmax, las 3 bases de cada brazo, con `evaluar_piloto.py` (copia en coord2) → `evaluar.brazo_profundo` → `correr_episodio` del **código parchado del brazo** |
| Métrica | `timeloss_prom` (timeLoss medio por vehículo, tripinfo) |
| Referencias en 5001-5030 | ya simuladas en `mejora_coord/salidas/sim/`: `red_alta_fijo2509.csv` (fijo_2509 = git 37f96801:plan2/red_alta.add.xml), `red_alta_actuado.csv`, `red_alta_trivial.csv`, `red_alta_ippo_vecinos_s42.csv` (IPPO vecinos publicado) |
| Estadística | `evaluar.comparar`: Δ % de medias, IC95 bootstrap pareado por semilla (10 000 remuestreos), Wilcoxon pareado; regla del veredicto `veredicto.veredicto` |
| Entorno | Python 3.14, SUMO 1.25, torch CPU, `torch.set_num_threads(1)` (ya en `sembrar`), `torch.use_deterministic_algorithms(True)`, `PYTHONDONTWRITEBYTECODE=1` |
| Código | copia de `coord2/code` (= repo actual; sha256 de rl_ippo.py 31472d40988a9d65…, idéntico al del repo) en `coord2/tanda1/<id>/code`, parchada por `coord2/parchar2.py <id>`; cada reemplazo con `assert count == 1`, como `mejora_coord/parchar.py` |

---

## 3. Brazos de la tanda 1 (control + 5 variantes = 18 políticas; 15 procesos de entrenamiento)

Nombres de variante (`--variante`, van al meta y el código parchado ramifica por ellos, también en demo):

| id | variante | recompensa (meta) | algoritmo |
|---|---|---|---|
| C0 | `vecinos` | retraso | ippo |
| V1 | `norm` | retraso | ippo |
| V2 | `smdp_crn` | retraso | ippo |
| V3 | `norm_smdp_crn` | retraso | ippo |
| V4 | `mappo_equipo` | equipo_red | mappo |
| V5 | `norm_smdp_crn_triv` | retraso | ippo |

Diseño factorial 2×2 en {observación normalizada} × {descuento por segundo + exploración común}:
C0, V1, V2, V3. Sobre V3 se agrega un solo factor cada vez: V4 (MAPPO + recompensa de equipo) y V5
(inicio en el ciclo mínimo).

### C0 — Control: IPPO vecinos actual con validación de 8 semillas
- Código: `rl_ippo.py` **sin cambios**; solo `--val-seeds 999,1999,2999,3999,4999,7999,8999,9999`.
- **Cómo se obtiene sin gastar 3 procesos.** Como `validar()` restaura el RNG, entrenar C0 da, episodio a
  episodio, los mismos pesos que el entrenamiento original de `plan2/`. Entonces C0 = **re-validar con val8
  los 60 checkpoints existentes** (`plan2/checkpoints/red_alta_ippo_vecinos_s{42,2042,4042}_ep{010..200}.pt`,
  copiados a `coord2/tanda1/c0/plan2/checkpoints/`, solo lectura del repo) y aplicar la misma regla de
  selección. Condición: la **prueba de réplica** (§5, paso 2) tiene que dar identidad bit a bit.
- **Respaldo pre-declarado:** si la réplica falla, C0 se re-entrena completo (3 procesos) y **se elimina V2**
  para seguir en 15 procesos. En ese caso el diseño queda C0, V1, V3, V4, V5.
- Qué separa: el efecto de la validación de 8 semillas (C0 frente a IPPO vecinos publicado s42) del efecto de
  cada variante (Vi frente a C0).

### V1 — Observación con colas bien normalizadas (`norm`)
- Cambio (`observar`): colas y vehículos en movimiento de cada aproximación divididos por **10 veh × carriles
  de esa aproximación** en lugar de `C["cap"]` (carriles × plazas), con tope **2.0**:
  `obs[k] = min(2, h / (10·carr[a]))`, `obs[4+k] = min(2, max(0, v−h) / (10·carr[a]))`. Lo mismo en el mensaje
  para `outflow` y `cola_alimentadora` (divisor 10 × carriles de la alimentadora). `cola_mi_salida` (ocupación
  del carril del enlace) y el resto quedan igual. `C["carriles"][a] = net.getEdge(a).getLaneNumber()` en
  `preparar()`. La escala se elige en `correr_episodio` según la variante (`C["norm"] = variante in NORM`), así
  que la demo y `evaluar.py` la aplican solas. `dim_obs` no cambia (31). Meta: `"escala_obs": "10 veh/carril, tope 2"`.
- Hipótesis H1: con las colas visibles (p95 × 3.6-3.8, E5), la política puede condicionar el verde al tráfico.
  Predicción: **sin** corregir la exploración, más reactividad rompe la sincronía (E12, a8, a10). No se espera
  una mejora significativa frente a C0; puede empeorar.

### V2 — Descuento por segundo + exploración común (`smdp_crn`), observación original
- (i) **Descuento SMDP** (idea 1 de causa). En el buffer se guarda `t` (segundo de simulación) de cada decisión
  y `t_final` al cerrar el episodio; `dt_k = t_{k+1} − t_k` (5 s si mantiene, 8 s si cambia, ámbar incluido;
  para la última, `t_final − t_k`). En `gae()`: `δ_k = r_k + γ^{dt_k/5}·V_{k+1} − V_k` y
  `A_k = δ_k + (γλ)^{dt_k/5}·A_{k+1}`, con el mismo trato del bootstrap `v_final`. La recompensa de cada
  decisión no cambia (suma por segundo / 5 · ESCALA_R).
- (ii) **Exploración común** (idea 1 de literatura, números aleatorios comunes). Solo en `modo == "train"`:
  `rng_expl = np.random.default_rng(seed + 104729)` creado al empezar el episodio (flujo propio, no toca
  `random`, `np.random` ni `torch`). En cada segundo con agentes que deciden se sortea **un solo**
  `u = rng_expl.random()`, y cada agente toma `a = 1 si p_cambiar > u, si no 0`, con `p_cambiar` = softmax de
  los logits enmascarados. `logp = dist.log_prob(a)` sin cambios. La máscara fuerza los casos p = 0 y p = 1.
  Se declara la limitación: con p distintas entre agentes el estimador del gradiente con logp marginales está
  sesgado; es una heurística.
- Hipótesis H2 (E1-E4): con el objetivo por segundo y el ruido correlacionado, el ciclo corto sincronizado deja
  de parecer peor de lo que es. Predicción: la política publicada cambia de fase más (C0 s42: 559 cambios en
  5001-5030; trivial 868, `coord2/b1_alineacion.txt`) y su timeLoss baja frente a C0.

### V3 — V1 + V2 (`norm_smdp_crn`)
- Los dos cambios anteriores juntos. Es la base de V4 y V5.
- Hipótesis H3: con la exploración corregida, las colas visibles permiten correcciones adaptativas sin romper la
  sincronía. Predicción: V3 ≤ V2 en timeLoss; la interacción (V3 − V2) − (V1 − C0) es negativa.

### V4 — V3 + MAPPO con recompensa de equipo alineada con la métrica (`mappo_equipo`)
- Algoritmo: `rl_mappo.py` (crítico central, actor = `Politica`), con `VARIANTE = "mappo_equipo"` en la copia
  parchada. Así la política publicada lleva ese nombre en el meta y `evaluar.brazo_profundo` la juega con la
  observación normalizada.
- Recompensa de equipo (idea "MAPPO de verdad" de causa y E6-E8): en `correr_episodio`, si la variante es de
  equipo, se suscriben (VEH, VEL) **todos los edges no internos** de la red (`sumolib.readNet`, sin internos:
  incluye la rotonda, SR_RS, C1_RE y los ramales), y cada segundo cada agente con decisión pendiente acumula
  `r_equipo = −(1/n_tls)·Σ_e n_e·(1 − min(1, max(0, v_e)/vmax_e))`. Es el mismo proxy de `c1_sim_recompensa.py`
  que define J_red_seg (Spearman 0.993). Sin término de espera W2, igual que J_red_seg (pesa 1-4 % de L, c6).
  `ret_retraso` sigue reportando la recompensa local sin mezclar.
- Descuento SMDP en MAPPO: `decidir` guarda `info["t"]` en el extra; `transicion` calcula
  `dt = info["t"] − t_decisión` y lo agrega al buffer, y `ri.gae` (parchado) lo usa. Exploración común en
  `Recolector.decidir`, con la misma regla y el mismo flujo `seed + 104729`.
- Hipótesis H4: con un objetivo común que ve la rotonda, el crítico central tiene algo que aprender (E8) y
  los agentes internalizan el costo sobre SR_RS. Predicción: menor timeLoss que V3 y menor retraso en SR_RS
  (diagnóstico §6.3).

### V5 — V3 + inicio en el ciclo mínimo (`norm_smdp_crn_triv`)
- Cambio: sesgo de la capa final del actor inicializado en `[0, +3.476]` (= ln(0.97/0.03)): en toda decisión
  libre p(cambiar) ≈ 0.97, porque los pesos de esa capa (ganancia ortogonal 0.01) apenas mueven el logit. En
  argmax el ep 0 es "cambiar en cuanto la máscara lo permite", que en red_alta es el trivial 10/10. Con la
  exploración común, el 3 % de desvío cuesta +1.2 % (E2). Es la versión residual de "anclar al trivial" (idea 2
  de literatura) sin clonado ni término KL: la política parte **exactamente** del ciclo mínimo y PPO aprende
  desviaciones. **El ep 0 no es candidato a checkpoint**, así que la regla de selección no cambia.
- Hipótesis H5: con el objetivo corregido (V3), partir del trivial ya no produce la deriva de E10, y las colas
  visibles permiten desviaciones útiles. Predicción: acuerdo ≥ 0.9 con el trivial en decisiones libres y un
  timeLoss cercano al trivial. Superar al trivial (criterio b) es **improbable** (E12).

### Familias consideradas y no incluidas (motivo)
- Recompensa de vecindario con α (MA2C): en P4, con 3 cruces, la de equipo (α = 1, V4) la cubre y agrega la
  rotonda. Queda para P6 si V4 funciona.
- Ancla KL/CE al clon: V5 logra el mismo punto de partida sin cambiar la pérdida ni admitir el ep 0.
- Estrategias evolutivas: es otro algoritmo y usa ~10× los episodios del protocolo.
- Ventaja optimista (OptiMAPPO) y huella de política en el mensaje: efectos de segundo orden después de la
  exploración común; cambiar el mensaje además rompe la compatibilidad de dim_obs.
- K = 4 episodios por actualización: multiplica ×4 la CPU y no entra en 15 procesos.

---

## 4. Criterios de decisión (fijados ahora)

### 4.1 Tanda 1 (P4, 5001-5030)
1. Para cada variante Vi (V1-V5): base publicada b*_i = mediana de val_elegido (val8). Se registra si converge
   (`convergencia` sobre la serie val8 de b*_i).
2. **Ganadora** = la Vi de **menor timeLoss medio de su base publicada en 5001-5030**, entre las Vi cuya base
   publicada converge. Si hay empate a 0.001 s, gana la de menor val_elegido y, si sigue el empate, la de menor
   número. C0 no compite: es el control.
3. Si ninguna variante converge, no hay ganadora y el EXITO es imposible. Se reporta "ninguna variante
   converge".

### 4.2 EXITO (se necesitan las tres condiciones)
- **(a)** En 5001-5030, la base publicada de la ganadora frente a fijo_2509: Δ ≤ −5 %, IC95 entero < 0 y
  Wilcoxon p < 0.05. Se informa también la etiqueta completa de `veredicto.veredicto`, que agrega "no pierde con
  el actuado".
- **(b)** En 5001-5030, frente al **trivial**: IC95 de Δ entero < 0. Se informa el p.
- **(c)** Confirmación en **6001-6030** con la **misma política** (sin re-entrenar), con fijo_2509, actuado y
  trivial simulados en esas semillas: se cumplen (a) y (b) otra vez.

Lectura obligada:
- Si (a) se cumple y en (b) el IC95 contiene 0: **"reproduce el ciclo mínimo"**, no es coordinación aprendida.
- Si en (b) el IC95 es entero > 0: "no alcanza al trivial".
- Si (a) falla: "no supera al fijo_2509 por ≥ 5 %".
- Como la ganadora se elige en 5001-5030, (a) y (b) en esas semillas son optimistas (maldición del ganador).
  Por eso solo (c) confirma.

### 4.3 Contrastes secundarios (descriptivos; no deciden la ganadora)
En 5001-5030, entre bases publicadas: Δ, IC95 y Wilcoxon de:
- cada Vi frente a C0, con corrección de Holm sobre los 5 p;
- C0 frente a IPPO vecinos publicado s42 (efecto de la validación de 8 semillas);
- los contrastes de mecanismo V1 − C0 (normalización), V2 − C0 (SMDP + exploración común), V3 − V2, V4 − V3 y
  V5 − V3;
- la dispersión entre bases: media en 5001-5030 de cada una de las 3 bases de cada brazo (mínimo y máximo).

### 4.4 Diagnósticos pre-declarados (descriptivos)
- `cambios_fase` y `ret_retraso` medios en 5001-5030 (del CSV de evaluación) de cada base publicada.
- Acuerdo con el trivial: fracción de decisiones libres en que el argmax es "cambiar", semilla 999, base
  publicada de cada brazo.
- Entropía libre media de los últimos 20 episodios (CSV de entrenamiento).
- Retraso en SR_RS y en las aproximaciones (veh·s, edgedata, las 8 semillas de val8) para las bases publicadas
  de C0, V3, V4 y el trivial, con el método de `c6_edges_no_cubiertos.py`.
- Deriva, solo en V5: val media de ep 150-200 frente a la val8 del ep 0 (trivial).

---

## 5. Procedimiento, procesos y tiempos (tanda 1)

Estructura: `coord2/tanda1/<id>/{code,plan2,logs,salidas,run}` con id en {c0, v1, v2, v3, v4, v5}. `plan2/` es
una copia de `mejora_coord/p4_clon_trivial/plan2/*.xml|*.sumocfg` (red, red_alta, fijo2509, actuado, trivial).

0. **Parches y hashes.** `python coord2/parchar2.py <id>` para v1-v5. Luego se escribe
   `coord2/tanda1/lanzamiento.sha256` con el sha256 de: este pre-registro, `parchar2.py`, cada
   `code/rl_ippo.py` y `code/rl_mappo.py` parchado, `evaluar_piloto2.py`, `juzgar_tanda1.py` y los scripts de
   lanzamiento. Se hace antes del paso 3.
1. **Humo** (descartable; a lo sumo 6 procesos, ~5 min). Cada brazo parchado corre 2 episodios de
   entrenamiento con base 7 (semillas 8 y 9) y valida en 999. V5: se valida el ep 0 en 999 y 1999 y tiene que
   dar 25.40 y 28.49, los valores del trivial (`p4_clon_trivial/logs/train_s42.log`: val_clon_999 25.4,
   val_clon_1999 28.49). V1: para cada aproximación, el factor de escala nuevo/viejo = cap/(10 · carriles)
   tiene que dar lo de `c2_escalas_obs.txt` (3.6-3.8 en P4), y con un mismo estado observado la observación de
   V1 tiene que ser la de C0 por ese factor (con el tope aplicado). V4: el meta dice `"algoritmo": "mappo", "variante": "mappo_equipo"`, y `evaluar_piloto` en 999 reproduce
   la val_999 del checkpoint de humo. Si algo falla, se corrige el parche y se declara en DESVIACIONES.md antes
   del lanzamiento.
2. **Prueba de réplica de C0** (1 proceso, ~3 min). Se re-entrena C0, base 42, 10 episodios, con val 999,1999.
   Tiene que ser idéntico a `plan2/resultados_red_alta_ippo_vecinos_s42.csv` (ep 1-10: timeloss_prom, kl_aprox,
   perdida_politica, entropia_libre, cambios_fase), y el `state_dict` de ep 10 idéntico al de
   `plan2/checkpoints/red_alta_ippo_vecinos_s42_ep010.pt` (`torch.equal` en todos los tensores). Resultado en
   `tanda1/c0/salidas/replica.txt`. Si pasa, C0 se hace por re-validación; si no, se aplica el respaldo de §3.
3. **Entrenamiento**: 15 procesos a la vez (V1-V5 × 3 bases), cada uno con 1 hilo de torch, sin parada
   temprana. Si un proceso cae, se relanza esa base con la misma semilla (el resultado es determinista) y se
   anota.
4. **Re-validación de C0** (cuando termina el entrenamiento): 60 checkpoints × 8 semillas repartidos en
   ≤ 15 procesos. Las val_999 y val_1999 re-calculadas tienen que coincidir con las del json de cada checkpoint
   (otra prueba de determinismo). Con eso se arma el meta de C0 (ep_elegido, val_elegido, val_serie) con
   `elegir_checkpoint`.
5. **Evaluación**: 18 políticas (6 brazos × 3 bases) en 5001-5030, ≤ 15 procesos a la vez.
6. **Juicio**: `juzgar_tanda1.py` (adaptado de `mejora_coord/juzgar.py`, con la misma regla) →
   `tanda1/salidas/juicio_tanda1.txt|json`, con la ganadora, (a), (b), los contrastes y los diagnósticos.

Tiempo estimado de reloj (8 núcleos, 16 hilos). En el piloto P4, con 9 procesos a la vez, el episodio de
entrenamiento tardó 8.4-9.1 s y el de evaluación 6-7 s (`p4_clon_trivial/logs`). Por proceso:
200 × ~9-12 s + 160 validaciones × ~6.5-8 s ≈ 50-70 min con 15 procesos. A eso se suman ~5 min de humo y
réplica y ~10 min de re-validación, evaluación y juicio. **Total ≈ 65-85 min.** No hay decisiones
intermedias: nada del diseño depende de mirar resultados parciales.

---

## 6. Tanda 2 (se lanza cuando termina el juicio de la tanda 1)

### 6.1 P6 `malla3_alta`: las 2 mejores variantes + control
- Variantes: las 2 primeras del orden de §4.1 (primero las que convergen, por timeLoss en 5001-5030). Si
  convergen menos de 2, se completa con las mejores que no convergieron, marcadas "no convergió en P4". Las
  variantes van **tal cual**. En particular, si V5 entra, empieza en el ciclo mínimo aunque en P6 el trivial se
  trabe (184.4 s en 5001-5030); adaptarlo al 15/10 sería post hoc.
- Protocolo: 3 bases, **200 episodios** (el mismo largo del protocolo, para que el control sea exacto y el
  plan de lr, lineal a 0 en 200, sea el mismo), validación val8 **cada 20 episodios** (ep 20, 40, ..., 200: 10
  puntos) y la misma regla de selección, base publicada y convergencia.
- Control C0-P6: re-validación con val8 de los checkpoints existentes
  `plan2/checkpoints/malla3_alta_ippo_vecinos_s{42,2042,4042}_ep{020,040,...,200}.pt`. Antes se hace una prueba
  de réplica como la del paso 2 (malla3_alta, base 42, 10 episodios, frente a
  `plan2/resultados_malla3_alta_ippo_vecinos_s42.csv` y el checkpoint ep010). Si falla, C0-P6 se re-entrena
  (3 procesos).
- Evaluación en 5001-5030 (2 partes por base). Referencias ya simuladas: `malla3_alta_fijo2509.csv` (el fijo
  instalado en plan2), `malla3_alta_actuado.csv`, `malla3_alta_trivial.csv` y `malla3_alta_ippo_vecinos_s42.csv`
  (IPPO vecinos publicado, +2.2 % en el examen, +2.4 % en 5001-5030).
- Criterio "**mejora en P6**" por variante: la base publicada converge, el IC95 de Δ frente a IPPO vecinos
  publicado s42 es entero < 0 y la etiqueta de la regla frente a fijo_2509 no es FALLA. Se reportan la
  etiqueta, Δ frente a C0-P6 y la sd entre semillas (colapsos: IPPO 3.6-7.2 s frente a 0.43 del fijo, a9).
- Tiempo: el piloto P6 (150 ep, val2 cada 10) tardó 1 h 41 min con 9 procesos. Aquí son 200 ep + 80
  episodios de validación ≈ **2.5-3 h**.

### 6.2 P1 `corredor`: no regresión de la ganadora
- Solo si hay ganadora en la tanda 1. 3 bases, 200 episodios, val8 cada 10, misma regla.
- Referencias a simular en 5001-5030 (no existen): fijo = git 37f96801:plan2/corredor.add.xml, actuado =
  git 37f96801:plan2/corredor_actuado.add.xml, trivial (programa 10/10 construido como `red_alta_trivial.add.xml`;
  se verifica en 999 contra el trivial jugado como decisor de reglas) e IPPO vecinos publicado P1 (base 4042,
  `plan2/politica_corredor_vecinos_s4042.pt`).
- **NO REGRESIÓN** si la base publicada de la ganadora en P1 da FUNCIONA con la regla (convergencia incluida)
  **y** el límite superior del IC95 de Δ frente a IPPO vecinos publicado P1 es ≤ +2 %.

### 6.3 P4: confirmación en 6001-6030 (condición c)
- La política publicada de la ganadora, sin re-entrenar, se evalúa en 6001-6030. Junto con ella, C0 publicado,
  IPPO vecinos publicado s42, fijo_2509, actuado y trivial, todos simulados en 6001-6030.
- Se aplican (a) y (b) de §4.2. **Sensibilidad pre-declarada:** 6001-6010 ya se simularon en `mejora_coord`,
  solo para diagnóstico de checkpoints viejos (`analisis_checkpoints.py`): nunca para entrenar ni elegir estas
  variantes. Por eso se reporta además el resultado en **6011-6030**, que nunca se usaron. La decisión (c) se
  toma con 6001-6030.

### 6.4 Presupuesto de procesos de la tanda 2
Al inicio: P6 6 entrenamientos + P1 3 entrenamientos + réplica P6 1 + (confirmación P4 y referencias P1: 4) =
14. Después, re-validación de C0-P6 y evaluaciones, siempre ≤ 15 a la vez.

---

## 7. Semillas (sin solapamientos)

| Uso | Semillas |
|---|---|
| Entrenamiento | base + k, k = 1..200: 43-242, 2043-2242, 4043-4242 |
| Humo | 8, 9 (base 7); validación de humo 999 (y 1999 para V5) |
| Validación (selección de checkpoint) | 999, 1999, 2999, 3999, 4999, 7999, 8999, 9999 |
| Exploración común | flujo propio `default_rng(semilla_episodio + 104729)`; no es semilla de SUMO |
| Cribado (tanda 1 y P6, P1) | 5001-5030 |
| Confirmación de la ganadora | 6001-6030 (sensibilidad: 6011-6030) |
| **Prohibidas** | **1001-1030** |

---

## 8. Resultados esperados (predicción honesta, para contrastar después)

- La probabilidad de EXITO (a ∧ b ∧ c) es **baja**: ninguna regla adaptativa ni desfase medido le gana al
  trivial en P4 (E12), y el oráculo de re-selección llega solo a −2.6 % (SINTESIS §3).
- Lo más probable: V5 y, quizá, V3 se acercan al trivial (Δ frente a fijo_2509 ≈ −5 a −7 %, cumplen (a)) y
  empatan con él en (b): "reproduce el ciclo mínimo", ahora aprendido de forma estable (sin la deriva de E10).
- V1 sola no mejora a C0. V2 cambia de fase más que C0.
- C0 frente a IPPO vecinos publicado: diferencia chica (el oráculo de re-selección era −2.6 %).
- En P6, lo que se busca es la convergencia y ≥ EMPATA. Ganarle al 15/10 no se espera.

Estas predicciones no cambian los criterios de §4: se escriben solo para poder medir después cuánto sorprendió
el resultado.
