# Síntesis: ¿se puede mejorar la coordinación de IPPO vecinos? (28.09.2026)

Todo lo de abajo está en `scratchpad/mejora_coord/` (scripts `a*.py`, `analisis_*.py`, `juzgar.py`, `evaluar_piloto.py`; salidas en `salidas/` y en cada `p*/salidas/`). No se escribió nada en el repo. Semillas simuladas: validación 999/1999 (y 2999-7999 declaradas para val8), re-selección 6001-6010 y piloto 5001-5030. **No se usaron las semillas 1001-1030** (de ellas solo se leyeron los CSV existentes). Referencia: fijo del 25.09 (`fijo_2509`, git 37f96801; en P6, el fijo instalado).

## 0. Respuesta corta

- **¿Mejora la coordinación?** No, con evidencia de piloto. Ninguna variante probada saca a P4, P5 o P6 de su veredicto con la regla pre-registrada. En P4 una variante llega a −6.4 % frente a `fijo_2509`, pero lo hace **copiando el trivial** (ciclo mínimo sincronizado): es idéntica a él en las 30 semillas. No es coordinación aprendida.
- **¿Conviene incluirlo HOY como variante declarada?** No. Mi recomendación es dejarlo en **Recomendaciones / trabajo futuro**, con 3-4 frases de hallazgos. Los detalles están en la sección 4.
- **¿Está el gráfico de mejora?** Sí, en la tesis. Es `TESIS/images/fig_plan2_mejora_caso.png` (Cap. 5, `fig:plan2-mejora-caso`): Δ frente al fijo por caso, IPPO vecinos y MAPPO, 1001-1030, con IC95 y círculo hueco si no converge. Existe también `fig_robustez_mejora_caso.png` (`fig:robustez-mejora-caso`). Las dos se regeneraron con P6 el 28.09 (09:14-09:15). Las variantes de esta síntesis **no** aparecen en esas figuras, y no deberían aparecer.

## 1. Qué hace hoy IPPO vecinos (diagnóstico)

| Caso | Qué aprendió la política publicada | Evidencia |
|---|---|---|
| P3 red, P5 malla3 | **Es el trivial**: cambia el 100 % de las decisiones libres, siempre a los 10 s. Usa los mensajes como reloj de sincronía: si se corta el canal, el timeLoss sube +79.8 % (red) y +70.1 % (malla3). Si se anulan las colas, la decisión no cambia (acuerdo 1.000). | `a3_obs_sensibilidad.txt` |
| P4 red_alta | Un plan casi fijo de ~24-25/10 s, ciclo de 41 s, con una onda verde de doble sentido algo mejor que la del fijo del 25.09 (banda 0.95 frente a 0.90). Pierde en el reparto: la transversal espera 16.9-17.5 s/veh, frente a ~11 s con el trivial. | `a7_verde_por_cruce.txt`, `salidas/fases.txt`, `salidas/sim_red_alta.txt` |
| P6 malla3_alta | Un plan casi fijo (~20-29 / 12-16 s) con colapsos parciales en algunas semillas (sd 3.6-7.2 s frente a 0.43 del fijo). | `a7`, `a9_maldicion.txt` |

Causas estructurales medidas:
1. **Las colas son casi invisibles**: se normalizan con la capacidad de todo el edge, así que la media queda en 0.002-0.01 (`a3`, bloque de magnitudes). La red solo ve bien el tiempo y la fase, y por eso aprende planes de tiempos.
2. **La recompensa es local**. En P4 cubre solo el 49-52 % del timeLoss, y la rotonda aporta el 21-26 % (`a4_cobertura.txt`, `a5_rotonda.txt`).
3. **La selección con 2 semillas está sesgada**. La concordancia entre la val 999/1999 y las semillas 6001-6010 sobre 60 checkpoints tiene Spearman 0.28 en P4 y 0.34 en P6 (`salidas/checkpoints_*.txt`). En P6 el checkpoint publicado pasa de −4.4 % (val2) a +1.3 % (val8) (`a9`).
4. **En este simulador coordinar es sobre todo mantener un ciclo común sincronizado**. Todo lo que rompe esa sincronía empeora: Max-Pressure queda entre +20 % y +60 % (`a10_maxpresion.txt`) y saltar fases vacías entre +6 % y +63 % (`a8_heuristicas.txt`). Tampoco hay desfases que mejoren de forma robusta (`a11_desfases.txt`).

Techo por celda (`a12_trivial8.txt`, val8):
- **P4**: el trivial le gana a `fijo_2509` por −9.7 % (8/8 semillas). Hay margen, pero ese margen es el trivial.
- **P5**: el trivial queda en −0.4 % (5/8). No hay margen con estas restricciones.
- **P6**: el trivial se traba (val 233 s) y nada de lo probado le gana de forma robusta al 15/10.

## 2. Pilotos (semillas 5001-5030, regla del veredicto sin cambios)

El criterio de cada piloto se fijó antes de correr (`p*/piloto.json`, sha256 en `pilotos_sha256.txt`). El juicio sale de `juzgar.py`, que usa la misma regla que `veredicto.py`.

Referencias en 5001-5030, timeLoss medio en s (`salidas/referencias_piloto_5001_5030.txt`, `p*/salidas/juicio.txt`):
- **P4**: fijo_2509 30.06, actuado 29.67, IPPO vecinos s42 publicado 28.93 (−3.8 % [−5.7, −1.9], coherente con el −3.6 % del examen), trivial 28.15 (−6.4 %).
- **P6**: fijo_2509 36.84, IPPO vecinos s42 37.75 (+2.4 %), actuado 64.84, trivial 184.39.

| Piloto | Qué cambia | Base publicada: Δ frente a fijo_2509 [IC95] | Frente a IPPO vecinos publicado | Veredicto de la variante | Criterio fijado |
|---|---|---|---|---|---|
| `p4_clon_trivial` (P4, 200 ep) | Clonar el trivial antes de PPO | s2042: **−6.4 %** [−8.4, −4.3], p=9e-6 | −2.7 % [−4.4, −1.0], p=0.014 | **PENDIENTE** (no converge: plateau +7.0 %, estabilidad 5.6 %; provisional FUNCIONA) | Fracaso |
| `p6_clon_fijo` (P6, 150 ep) | Clonar el 15/10 antes de PPO | s42: **+8.0 %** [3.3, 12.9] | +5.4 % [−1.3, 12.3], p=0.07 | **PENDIENTE** (provisional FALLA) | Fracaso |
| `p6_salida` (P6, 150 ep) | El mensaje lleva la cola del enlace de salida i→j | s2042: **+22.3 %** [18.0, 25.9] | +19.4 % [12.7, 25.4] | **PENDIENTE** (ninguna base converge; provisional FALLA) | Fracaso |

Detalles:
- **P4, clon del trivial.** Las 3 bases eligen el clon (ep 10) o casi el clon (ep 40). El triple empate en val (26.945) lo rompe la regla por número de base y sale la 2042, que no converge; la 42 y la 4042 darían FUNCIONA, pero la regla no permite elegirlas. **Frente al trivial: +0.0 %, p=1 (idéntico en las 30 semillas)**; la base 42 da +0.3 % [0.0, 0.8]. Después del clon, PPO se aleja del ciclo corto: la val empeora +10.7 a +13.2 % (ep 150-200) y los cambios de fase bajan ~30 % (`p4_clon_trivial/salidas/deriva.txt`). Lo que recupera el trivial es la selección de checkpoint, no el aprendizaje.
- **P6, clon del 15/10.** El clon es exacto (val 36.42, igual al fijo), pero en el ep 10 las 3 bases ya validan 41.4-41.9 (+14 %). Las políticas elegidas coinciden con el 15/10 solo en el 47-52 % de las decisiones libres, y casi todo el desacuerdo es alargar el verde (`p6_clon_fijo/salidas/acuerdo_s*_999.json`). El RL **empeora** el programa clonado.
- **P6, mensaje de salida.** La dispersión entre bases es enorme (−1.3 / +11.3 / +22.3 %). La mejor base (42) empata con el fijo, pero no es la publicada. En la base publicada, la cola máxima de enlace **sube** (27.5 frente a 16.6 de vecinos; `p6_salida/salidas/diag_cola.txt`), en contra de la hipótesis.

## 3. Qué mejora, cuánto y con qué confianza

- **Coordinación aprendida: ninguna mejora demostrada.** En P3/P5 la política ya es el trivial, que es el techo medido. En P4 la única ganancia (−6.4 % frente a −3.8 % de IPPO publicado en 5001-5030, es decir, −2.7 % entre ellos) sale de **reproducir una regla sin aprendizaje**. En P6 las dos variantes empeoran.
- **Re-seleccionar checkpoints (V1 'sel8') no alcanza el umbral**, ni siquiera con un oráculo optimista: el mejor checkpoint existente elegido *con* las semillas 6001-6010 da −2.6 % en P4 y −2.1 % en P6 frente a `fijo_2509` (`salidas/checkpoints_*.txt`). Ninguno llega a −5 %. No hace falta correr V1 para saber que no cambia el veredicto.
- **Confianza:** es evidencia de piloto (30 semillas 5001-5030, 3 bases, 1 corrida por variante). Los IC95 son pareados por bootstrap. En P6 la dispersión entre bases (hasta 23 puntos) es mayor que cualquier efecto buscado, así que un resultado de P6 con 3 bases no es estable.
- **No probado** (lo que queda abierto, con costo de reloj estimado):
  - V2, recompensa de vecindario al estilo MA2C con la rotonda (piloto en P4, ~1.5 h).
  - V3, MAPPO con recompensa de equipo (P4, ~1.5 h).
  - V4, observación re-escalada con conteo cercano (P4, ~1.5 h; P6, ~4 h).
  - Anclar PPO al clon con un término KL/BC y admitir el ep 0 como candidato (P6, ~2 h).

  Lo más que se espera de V2-V4 en P4 es acercarse al trivial, y en P6, empatar con el fijo. La evidencia (`a8`, `a10`) predice que las políticas más adaptativas rompen la sincronía.

## 4. Qué haría falta para incluirlo HOY y por qué no lo recomiendo

Si aun así se quisiera incluir **P4 vecinos_clon** como variante declarada:
1. Copiar las 3 políticas a `plan2/` y evaluarlas en 1001-1030 con `evaluar.py`, con la misma regla. Los modelos ya están entrenados, así que son **~5 min de reloj** (3 procesos, ~7 s por semilla). Hay que tocar `plan2/` y `veredicto.csv`, lo que hoy choca con la otra tarea que edita la TESIS.
2. Texto: la variante, la declaración post hoc (se decidió después de ver el examen de la política original) y la lectura obligada. Son ~1-2 h de redacción más la revisión de números.
3. **Resultado previsible:** PENDIENTE (la base publicada no converge) e idéntico al trivial, que la tesis **ya reporta** como referencia de robustez. No aporta una cifra nueva y en cambio suma una variante post hoc que un jurado puede leer como ajuste a posteriori.

Para P5 y P6 no hay nada que incluir: no se probó ninguna variante en P5 (el techo medido es −0.4 %) y en P6 las dos fracasaron.

**Recomendación:** dejar el veredicto pre-registrado como está y agregar en *Recomendaciones / trabajo futuro* un párrafo con esta evidencia (sin cifras de 1001-1030 nuevas):
- (a) La coordinación que aprende IPPO en P3/P5 es un ciclo mínimo sincronizado por mensajes, y en P4/P6 un plan casi fijo, porque las colas entran con una escala casi nula.
- (b) Con recompensa local, PPO se aleja del ciclo corto aunque arranque en él (piloto P4) y del 15/10 en P6.
- (c) La selección con 2 semillas de validación es ruidosa (Spearman 0.28-0.34 con semillas nuevas).
- (d) Líneas futuras: recompensa de vecindario o de equipo, observación re-escalada, anclaje KL al clon y validación con ≥ 8 semillas.

Si el autor quiere, esas cifras pueden citarse como "piloto en semillas 5001-5030, fuera del protocolo de examen", nunca como veredicto.

## 5. Archivos clave

- Diagnósticos: `a3_obs_sensibilidad.txt`, `a4_cobertura.txt`, `a5_rotonda.txt`, `a7_verde_por_cruce.txt`, `a8_heuristicas.txt`, `a9_maldicion.txt`, `a10_maxpresion.txt`, `a11_desfases.txt`, `a12_trivial8.txt`, `salidas/fases.txt`, `salidas/checkpoints_{red_alta,malla3_alta}.txt`, `salidas/referencias_piloto_5001_5030.txt`.
- Pilotos: `p4_clon_trivial/salidas/{juicio.txt,deriva.txt}`, `p6_clon_fijo/salidas/{juicio.txt,acuerdo_s*_999.json}`, `p6_salida/salidas/{juicio.txt,diag_cola.txt}`.
- Horas de reloj consumidas por los pilotos: P4 38.5 min, P6 clon 1 h 41 min, P6 salida 1 h 40 min (los dos de P6 corrieron en paralelo).
