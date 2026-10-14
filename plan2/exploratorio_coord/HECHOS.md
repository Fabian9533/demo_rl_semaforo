# HECHOS: cifras verificadas del análisis exploratorio (28.09.2026)

Todas las rutas son relativas al repo (`demo_rl/`). La abreviatura `EC/` equivale a `plan2/exploratorio_coord/`.

- **Métrica.** timeLoss medio (s/veh) salvo que se diga otra cosa.
- **Diferencias.** Δ % de medias con IC95 bootstrap pareado (10 000 remuestreos) y p de Wilcoxon pareado, calculados con `evaluar.comparar`. Negativo significa mejor.
- **Verificación.** Cada cifra se comprobó contra el archivo citado. Las de P4, P6 y P1 se recalcularon además desde los CSV por semilla con `EC/verificar_hechos.py`, y todas coinciden (`EC/verificar_hechos.txt`).
- **Estatus.** Todo es exploratorio y posterior al veredicto del 25.09, que no cambia. Las semillas 1001-1030 no se usaron.

## 0. Correcciones al contexto recibido

| Cifra o frase del contexto | Qué dicen los archivos | Fuente |
|---|---|---|
| "las decisiones duran 5 s o **13 s** tras un cambio" | Duran **5 s** si se mantiene la fase y **8 s** si se cambia, ámbar incluido. El descuento es γ^(dt/5), así que un cambio descuenta γ^1.6 | `EC/PRERREGISTRO.md` (V2, "dt_k = t_{k+1} − t_k (5 s si mantiene, 8 s si cambia, ámbar incluido"); `EC/codigo/rl_ippo_smdp_crn.py`, docstring de `gae()` |
| "frente al fijo re-barrido de la robustez empata (+1.6 % [−0.2, 3.5])", puesto junto a la confirmación 6001-6030 | La cifra es de **5001-5030**. El fijo re-barrido no se simuló en 6001-6030 | `EC/sintesis/extra_robustez.txt` |
| "una de 3 bases no converge por variante" (en general) | Vale **solo para P6**: V2 y V5 base 2042. En P4 las 3 bases de todas las variantes convergen. C0-P6 no converge en ninguna base (0/3) | `EC/tanda2/juicio_tanda2.txt`, `EC/tanda1/juicio_tanda1.txt` |
| "extensiones del verde de avenida en 28-34 % **de los ciclos**" | Son el 28 % (V2) y el 34 % (V5) de los **verdes E-O**: 72 % y 66 % duran 10 s. Hay un verde E-O por ciclo, así que la lectura se mantiene. Se midió **solo en la semilla 999** | `EC/sintesis/analizar_fases_p6.txt` |
| "60 semillas −7.0 % [−9.0, −5.1]" | Es V2 base 4042. V5 base 42 da −7.0 % [−9.2, −5.0] | `EC/conf_p6/salidas/juicio_conf_p6.txt` |
| Tabla del mensaje al autor: "IPPO vecinos actual P4 −3.6 %, P1 −6.8 %" | Esas dos cifras son del examen (1001-1030, tesis), no de esta carpeta. En las semillas de este análisis IPPO publicado da: P4 −3.8 % (5001-5030, 28.925 frente a 30.064) y −3.1 % [−4.8, −1.5] (6001-6030); P1 −6.7 % [−8.0, −5.4] (5001-5030). No se deben mezclar las dos fuentes en una misma frase | `EC/tanda1/juicio_tanda1.txt`, `EC/tanda2/juicio_tanda2.txt` |
| Tabla del mensaje: "Con la corrección: P4 −6.2 %, P1 −7.3 %, P6 −6.7 %" | Mezcla variantes. P4 −6.2 % es **V5** (6001-6030), P1 −7.3 % es **V5** (5001-5030) y P6 −6.7 % es **V2** (6001-6030). V2 no se corrió en P1 | `EC/tanda2/juicio_tanda2.txt`, `EC/conf_p6/salidas/juicio_conf_p6.txt` |

Todas las demás cifras del contexto cuadran exactamente con los archivos.

## 1. Diseño

| Hecho | Valor | Fuente |
|---|---|---|
| sha256 del pre-registro | 8d38fe82f9adec2c1e9318435a0ddbc01895e5af1fbab8a16b48c36006b66b33 (coincide con la copia) | `EC/prerregistro.sha256` |
| Variantes | C0 IPPO vecinos sin cambios, validado con 8 semillas. V1 `norm`: colas y móviles ÷ (10 veh × carriles), con tope 2. V2 `smdp_crn`: γ^(dt/5) y u común. V3 `norm_smdp_crn`: V1 + V2. V4 `mappo_equipo`: V3 + MAPPO con recompensa de toda la red. V5 `norm_smdp_crn_triv`: V3 + sesgo inicial p(cambiar) = 0.97, arranca en el ciclo mínimo | `EC/PRERREGISTRO.md`, `EC/SINTESIS.md` §1 |
| Entrenamiento | 3 bases (42, 2042, 4042) y 200 episodios. Val8 = 999, 1999, 2999, 3999, 4999, 7999, 8999 y 9999, cada 10 ep en P4 y P1 (20 puntos) y cada 20 ep en P6 (10 puntos) | `EC/PRERREGISTRO.md`; `EC/tanda2/seleccion_P6_V2.json` (`n_val` 10) |
| Semillas | Cribado 5001-5030; confirmación 6001-6030; sensibilidad 6011-6030. Las 6001-6010 ya se habían simulado en `mejora_coord` | `EC/PRERREGISTRO.md` (§ confirmación) |
| Exploración común | Un u = `default_rng(semilla + 104729)` por paso de decisión, compartido por todos los que deciden; a = 1 si p(cambiar) > u | `EC/codigo/smdp_crn.diff` |
| Código cambiado | Solo `rl_ippo.py` (V2 y V5). El resto del código de las variantes es idéntico al repo. Los sha256 coinciden con `tanda2/lanzamiento_p6_entrenamiento.sha256` (V2 d4ca0844…, V5 3fbde216…) | `EC/codigo/*.diff` |

## 2. Diagnóstico (antes de entrenar)

| Hecho | Valor | Fuente |
|---|---|---|
| P3 (`red`) y P5 (`malla3`): IPPO vecinos aprende el ciclo mínimo; cortar el canal (pérdida 1.0) sube el timeLoss | P3 +79.8 %, P5 +70.1 % (semillas 999 y 1999). En P4 −4.1 % y en P6 +131.8 % | `EC/diagnostico/mejora_coord/a3_obs_sensibilidad.txt` |
| P4: plan casi fijo largo | ~24-25/10 s, ciclo de 41 s | `EC/diagnostico/mejora_coord/SINTESIS.md` |
| P6: IPPO publicado s42 | Verde E-O mediano 25 s [20-30], N-S 15 s, ciclo 46 s, sincronía con vecinos 18.3 %, 161 fases/h (semilla 999) | `EC/sintesis/analizar_fases_p6.txt` |
| Descuento por decisión, P4 val8, IPPO s42 frente al trivial | timeLoss +4.8 %, J_seg +8.4 % (8/8 semillas prefieren el trivial), J_dec −1.5 % (7/8 prefieren IPPO) | `EC/diagnostico/c4_alineacion.txt` |
| Lo mismo en P6, IPPO s42 frente al 15/10 | timeLoss +4.6 %, J_red_dec −1.6 %. La columna "trivial" de ese archivo es el 15/10 (fila +0.0) | `EC/diagnostico/c4_alineacion_p6.txt` |
| Ruido de exploración sobre el ciclo base (val8) | P4 (trivial 27.08): 3 % independiente 32.96 (+21.7 %), 3 % común 27.39 (+1.2 %), 10 % común +7.6 %. P6 (15/10 36.57): 3 % independiente 41.94 (+14.7 %), 3 % común 37.36 (+2.1 %) | `EC/diagnostico/b2_ruido.txt` |
| Escala de las colas | p95 de la cola local 0.026 en P4 | `EC/diagnostico/mejora_coord/a3_obs_sensibilidad.txt` |
| Max-Pressure | La mejor versión por escenario queda entre +20 % (P4) y +60 % (P5) frente a fijo_2509; con todas las versiones, hasta +106 % (P6, `mp_cola`) | `EC/diagnostico/mejora_coord/a10_maxpresion.txt` |

## 3. P4 `red_alta`, cribado 5001-5030 (tanda 1)

Referencias: fijo_2509 30.064, actuado 29.674, trivial 28.152, IPPO vecinos publicado s42 28.925 y fijo re-barrido 27.633. Fuentes: `EC/tanda1/juicio_tanda1.txt` y `EC/sintesis/extra_robustez.txt`.

| Brazo (base publicada) | Media | Frente a fijo_2509 | Regla | Frente al trivial | Iguales al trivial |
|---|---|---|---|---|---|
| C0 (4042) | 29.081 | −3.3 % [−4.8, −1.8] | MEJORA | +3.3 % [1.6, 5.0] | 0/30 |
| V1 (4042) | 29.074 | −3.3 % [−4.9, −1.5] | MEJORA | +3.3 % [1.4, 5.3] | 0/30 |
| V2 (2042) | 28.152 | −6.4 % [−8.4, −4.3], p=9.22e-06 | FUNCIONA | +0.0 % [0.0, 0.0] | 30/30 |
| V3 (4042) | 28.206 | −6.2 % [−8.2, −4.1] | FUNCIONA | +0.2 % [−0.1, 0.5] | 21/30 |
| V4 (42) | 28.152 | −6.4 % [−8.4, −4.3] | FUNCIONA | +0.0 % [0.0, 0.0] | 30/30 |
| **V5 (42), ganadora** | 28.068 | −6.6 % [−8.6, −4.7], p=2.26e-05 | FUNCIONA | −0.3 % [−0.8, 0.2], p=0.00819 | 0/30 |

- **Contrastes frente a C0.** V1 −0.0 % [−1.7, 1.6] (p Holm 0.903). V2 −3.2 % [−4.8, −1.6] (p Holm 0.00592). V5 −3.5 % [−5.0, −2.0].
- **Efecto de validar con 8 semillas.** C0 frente a IPPO publicado: +0.5 % [−0.9, 2.0], p=0.666.
- **Interacción** (V3 − V2) − (V1 − C0): +0.061 s/veh [−0.412, +0.558].
- **Cambios de fase por episodio.** C0 567.0 y V2 868.4.
- **Frente a IPPO publicado.** V2 −2.7 % [−4.4, −1.0] y V5 −3.0 % [−4.7, −1.3].
- **Frente al fijo re-barrido** (10/10, desfases 0/25/24). V5 +1.6 % [−0.2, 3.5], p=0.118, gana en 13/30. V2 +1.9 % [−0.0, 3.8], igual que el trivial. C0 +5.2 % [3.9, 6.7] e IPPO publicado +4.7 % [2.6, 6.8]. Fuente: `EC/sintesis/extra_robustez.txt`.
- **Retraso total.** V5 frente a fijo_2509 −6.6 % [−8.5, −4.6]. El retraso de inserción es 0.336 s/veh en todos los brazos. Fuente: `EC/sintesis/extra_robustez.txt`.
- **Convergencia.** Las 3 bases convergen en las 5 variantes. Fuentes: `EC/tanda1/seleccion_V*.json`.
- **V4 con recompensa de toda la red.** SR_RS en val8 da 16 904.1 veh·s, igual al trivial y a V3. Fuente: `EC/SINTESIS.md` §1, que cita `tanda1/salidas/diag/srrs_resumen.txt` (copiado como `EC/tanda1/srrs_resumen.txt`).

## 4. P4, confirmación de V5 en 6001-6030 (tanda 2)

Fuentes: `EC/tanda2/juicio_tanda2.txt` §1 y `EC/tanda2/conteos_tanda2.txt`. Medias: V5 27.829, trivial 27.816, C0 28.610, IPPO publicado 28.739, fijo_2509 29.658 y actuado 29.759.

- **Frente a fijo_2509:** −6.2 % [−7.8, −4.5], p=2.05e-07, FUNCIONA. Gana en 27/30.
- **Frente al trivial:** +0.0 % [−0.3, 0.4], p=0.395. Gana en 17/30 y empata en 5/30. El criterio (b) no se cumple, así que **no hay ÉXITO**.
- **Frente a IPPO publicado:** −3.2 % [−4.9, −1.5], p=0.00158. Frente a C0: −2.7 % [−4.6, −1.0].
- **En 6011-6030:** frente a fijo_2509 −7.1 % [−8.9, −5.3], y frente al trivial +0.3 % [0.0, 0.7].
- **IPPO publicado frente a fijo_2509 en 6001-6030:** −3.1 % [−4.8, −1.5]. El trivial da −6.2 % [−7.9, −4.5].
- **Determinismo.** La semilla 5001 se reprodujo en los 6 brazos.

## 5. P6 `malla3_alta`

### 5.1 Cribado 5001-5030 (tanda 2)

Referencias: fijo 15/10 36.843 (sd 2.34), actuado 64.842, trivial 184.394 e IPPO publicado s42 37.745 (sd 4.55). Fuentes: `EC/tanda2/juicio_tanda2.txt` §2 y `EC/tanda2/conteos_tanda2.txt`.

| Brazo (base, ep) | Media (sd) | Frente al fijo 15/10 | Frente a IPPO publicado | Converge (bases) |
|---|---|---|---|---|
| C0-P6 (4042, ep180) | 39.636 (5.05) | +7.6 % [2.0, 13.3]; provisional FALLA | +5.0 % [−1.4, 11.8] | 0/3 |
| V2 (4042, ep160) | 34.141 (1.10) | −7.3 % [−10.0, −5.3], p=4.66e-08; gana en 28/30 | −9.5 % [−13.8, −5.4]; gana en 25/30 | 2/3 (no la 2042) |
| V5 (42, ep200) | 34.218 (1.46) | −7.1 % [−9.8, −4.8], p=2.97e-05; gana en 28/30 | −9.3 % [−13.8, −5.1]; gana en 22/30 | 2/3 (no la 2042) |

- V2 frente a C0-P6: −13.9 % [−17.7, −10.1]. V5 frente a V2: +0.2 % [−1.4, 2.1].
- IPPO publicado frente al fijo: +2.4 % [−1.7, 7.1], empata.
- Retraso total frente al fijo: V2 −3.2 % [−4.4, −2.3] y V5 −3.2 % [−4.4, −2.0]. Fuente: `EC/sintesis/extra_robustez.txt`.
- La V5 publicada se eligió en el ep 200, el último. La base 2042 no converge en ninguna de las dos (plateau: V2 −6.7 % y V5 −21.6 %). Fuentes: `EC/tanda2/seleccion_P6_V2.json` y `seleccion_P6_V5.json`.

### 5.2 Confirmación 6001-6030, sin re-entrenar (conf_p6)

Fuente: `EC/conf_p6/salidas/juicio_conf_p6.txt`. Medias: V2 4042 34.649, V5 42 34.546, IPPO publicado 37.586, fijo 15/10 37.118, actuado 62.890 y trivial 184.529.

| Brazo | Frente al fijo 15/10 | Frente a IPPO publicado | Retraso total frente al fijo |
|---|---|---|---|
| **V2 4042 (publicada)** | −6.7 % [−9.8, −3.7], p=3.24e-06, FUNCIONA; gana en 29/30 | −7.8 % [−11.7, −3.8]; gana en 23/30 | −3.1 % [−4.7, −1.7] |
| **V5 42 (publicada)** | −6.9 % [−10.3, −3.7], p=0.000306, FUNCIONA; gana en 28/30 | −8.1 % [−11.8, −4.4]; gana en 26/30 | −3.2 % [−5.0, −1.6] |
| V2 42 / V2 2042 | −6.0 % / −7.2 % | −7.2 % / −8.3 % | −2.7 % / −3.3 % |
| V5 2042 / V5 4042 | −7.6 % (FUNCIONA) / −4.8 % (MEJORA) | −8.8 % / −5.9 % | −3.5 % / −2.1 % |
| IPPO publicado s42 | +1.3 % [−2.7, 5.5], EMPATA | — | +0.7 % [−1.3, 2.6] |

- **Criterio de confirmación.** Pide IC95 < 0 frente al fijo y frente a IPPO publicado en las dos publicadas, y se cumple: CONFIRMA SÍ.
- **Retraso de inserción.** Está entre 45.49 y 45.65 s/veh en todos los brazos salvo el trivial (95.51). No hay vehículos sin insertar ni sin terminar, salvo en el trivial.
- **Determinismo.** La semilla 5001 se reprodujo en los 10 brazos.
- **Sensibilidad** (recalculada en `EC/verificar_hechos.txt`, que usa el mismo método):
  - **6011-6030.** V2 −6.5 % [−11.2, −2.1] frente al fijo (19/20) y −8.9 % [−13.8, −3.5] frente a IPPO publicado. V5 −6.8 % [−11.6, −1.8].
  - **6001-6030 sin la semilla 6028.** El fijo da 50.48 en esa semilla, la mayor de las 30; la siguiente es 38.01. V2 queda en −5.4 % [−7.1, −3.1] (28/29) y V5 en −5.7 % [−7.9, −3.0]. En retraso total, V2 da −2.5 % [−3.2, −1.4].
  - **60 semillas** (5001-5030 + 6001-6030). V2 −7.0 % [−9.0, −5.1] (57/60) y V5 −7.0 % [−9.2, −5.0] (56/60) frente al fijo. Frente a IPPO publicado, las dos −8.7 %. En retraso total, las dos −3.2 %. IPPO publicado frente al fijo: +1.9 % [−1.1, 5.0]. Fuente: `EC/conf_p6/salidas/juicio_conf_p6.txt`.

### 5.3 Qué aprendió la política en P6 (semilla 999)

Fuente: `EC/sintesis/analizar_fases_p6.txt`.

| Programa | Verde E-O mediano [p10-p90] | Verdes E-O de 10 s | Verde N-S | Ciclo mediano | Sincronía | Fases/h |
|---|---|---|---|---|---|---|
| fijo 15/10 | 15 [15-15] | 0 % | 10 | 31 | 100 % | 231 |
| trivial | 10 [10-10] | 100 % | 10 | 26 | 100 % | 276 |
| IPPO publicado s42 | 25 [20-30] | 6 % | 15 [10-20] | 46 | 18.3 % | 161 |
| V2 s4042 | 10 [10-20] | 72 % | 10 | 26 | 63.6 % | 247 |
| V5 s42 | 10 [10-20] | 66 % | 10 | 26 | 60.5 % | 245 |

- **Cola máxima de enlace media** (5001-5030): V5 9.8, V2 11.6, fijo 10.2, IPPO publicado 16.6 y C0 19.8. Fuente: `EC/sintesis/extra_robustez.txt`.
- **Lo que no se sabe.** No se sabe a qué reacciona la extensión del verde. Tampoco se comparó con una regla "ciclo mínimo + extender si hay cola". Fuente: `EC/SINTESIS.md` §3.1.

## 6. P1 corredor, no regresión de V5 (5001-5030)

Fuente: `EC/tanda2/juicio_tanda2.txt` §3.

- **V5 (base 4042) frente a IPPO publicado P1 (s4042):** −0.6 % [−1.5, 0.3], p=0.289, gana en 16/30. El límite superior (+0.3 %) cumple el umbral de +2 %, así que NO REGRESIÓN: SÍ.
- **V5 frente a fijo_2509:** −7.3 % [−8.7, −6.0], FUNCIONA. IPPO publicado da −6.7 % [−8.0, −5.4].
- **Convergencia.** Las 3 bases convergen. El ep 0 (trivial) valida 101.213 y el trivial da 102.582 en 5001-5030.
- **Alcance.** V2 no se probó en P1. P2, P3 y P5 no se probaron con ninguna variante.

## 7. Lo que no ayudó

| Cambio | Resultado | Fuente |
|---|---|---|
| V1, colas normalizadas | V1 − C0 = −0.0 % [−1.7, 1.6] en P4 | `EC/tanda1/juicio_tanda1.txt` |
| V4, MAPPO con recompensa de toda la red | Publica el trivial: idéntico en 30/30 en P4 | `EC/tanda1/juicio_tanda1.txt` |
| Validar con 8 semillas (C0 frente a IPPO publicado) | P4 +0.5 % [−0.9, 2.0]; P6 +5.0 % [−1.4, 11.8] | `EC/tanda1/juicio_tanda1.txt`, `EC/tanda2/juicio_tanda2.txt` |
| V5 frente a V2 en P6 (arranque en el ciclo mínimo y observación normalizada) | +0.2 % [−1.4, 2.1] en 5001-5030; −0.3 % [−3.3, 2.9] en 6001-6030 | `EC/tanda2/juicio_tanda2.txt`, `EC/conf_p6/salidas/juicio_conf_p6.txt` |

## 8. Limitaciones que deben acompañar cualquier uso

1. **Análisis post hoc.** Se decidió después del veredicto del 25.09 y no lo modifica.
2. **Demanda determinista.** Los `.rou.xml` usan `vehsPerHour`, así que las semillas solo varían `sigma`.
3. **3 bases por brazo.** En P6 una de las 3 bases no converge, tanto en V2 como en V5.
4. **Exploración común.** Usa logp marginales, un estimador sesgado cuando las p difieren entre agentes. Es una heurística declarada (`EC/SINTESIS.md` §6).
5. **Los dos cambios de V2 van juntos.** No se separa cuál de los dos pesa más.
6. **P4.** V5 reproduce el ciclo mínimo y no lo supera. Frente al fijo re-barrido empata (+1.6 % [−0.2, 3.5], 5001-5030).
7. **P6.** En retraso total la ganancia baja a −3.1 % (V2, 6001-6030), porque la espera para entrar a la red, ~45.5 s/veh, es igual en todos los brazos.
8. **Réplica de C0-P6.** Solo difirió en `cambios_fase`, con 4 cambios menos por episodio. Los pesos son idénticos bit a bit (T7). Fuente: `EC/DESVIACIONES.md`.
9. **`SINTESIS.md` está desactualizada en P6.** Se escribió antes de conf_p6: donde dice "sin confirmación en 6001-6030" hay que leer "confirmado" (§5.2).
