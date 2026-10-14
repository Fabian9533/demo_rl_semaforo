# Síntesis coord2: ¿se puede mejorar la coordinación de IPPO vecinos? (28.09.2026)

Todo está en `scratchpad/coord2/`. Las rutas de abajo son relativas a esa carpeta, salvo `mejora_coord/`, que es la carpeta hermana. No se escribió nada en `demo_rl/`.

- **Semillas.** Entrenamiento: base + k. Validación para elegir checkpoint (val8, declarada): 999, 1999, 2999, 3999, 4999, 7999, 8999, 9999. Cribado: 5001-5030. Confirmación: 6001-6030, con sensibilidad en 6011-6030. **Las semillas 1001-1030 no se simularon nunca**: cada script tiene un `assert`.
- **Pre-registro.** `PRERREGISTRO.md` (sha256 en `prerregistro.sha256`) se fijó antes de entrenar. Las desviaciones están en `DESVIACIONES.md` (D1-D11, T1-T7), escritas antes de ver los resultados que afectan.
- **Estatus.** Todo es **exploratorio y queda fuera del veredicto pre-registrado del 25.09**, que no cambia.

---

## 0. Respuesta corta

1. **La causa principal de que IPPO no mejore en P4/P6 está identificada.** No es la comunicación ni el crítico. Es el **objetivo de entrenamiento**:
   - `gae()` descuenta **por decisión** y no por segundo.
   - La exploración es **independiente** por semáforo, y eso rompe la sincronía.

   Si se corrigen las dos cosas (V2), la política cambia de régimen. Normalizar la observación (V1), la recompensa de toda la red con crítico central (V4) y validar con 8 semillas (C0) **no cambian nada** medible.
2. **P4 (red_alta).** La mejor variante (V5) **reproduce el ciclo mínimo** 10/3/10/3 y no lo supera. Lo confirman las semillas nuevas:
   - En 6001-6030 queda en +0.0 % [−0.3, 0.4] frente al trivial.
   - V2 y V4 publican exactamente el trivial (30/30 semillas idénticas).

   Frente a `fijo_2509` gana −6.2 % [−7.8, −4.5] en 6001-6030 (FUNCIONA), y frente a IPPO vecinos publicado, −3.2 % [−4.9, −1.5]. **Pero eso no es coordinación aprendida**, y frente al fijo **re-barrido** de la sección de robustez (10/10 con desfases) no gana: +1.6 % [−0.2, 3.5] (§5).
3. **P6 (malla3_alta).** Es el único resultado nuevo con contenido. V2 y V5 dan −7.3 % y −7.1 % frente al 15/10 (28/30 semillas) y −9.5 % / −9.3 % frente a IPPO vecinos publicado. La base publicada converge. **No es el trivial**, que se traba (184 s), **ni el 15/10**: es un ciclo mínimo con extensiones del verde de avenida en un 28-34 % de los ciclos (§3.1).
   - Solo hay **un** juego de 30 semillas (5001-5030) y **no hay confirmación en semillas nuevas**.
   - Una de las 3 bases no converge en cada variante, y en retraso total la ganancia baja a −3.2 %.
4. **P1.** V5 no empeora: −0.6 % [−1.5, 0.3] frente a IPPO vecinos publicado. V2 no se probó en P1, y P2, P3 y P5 no se probaron con ninguna variante.
5. **EXITO pre-registrado (a ∧ b ∧ c): NO.** Falla (b), le gana al trivial, en 5001-5030 y en 6001-6030.

---

## 1. Qué se probó y por qué

El punto de partida es el diagnóstico de `mejora_coord/SINTESIS.md`, más los chequeos b1-b7 y c1-c6 de coord2 (tabla E1-E12 del pre-registro). Las hipótesis nuevas eran tres:

- **E1.** El descuento por decisión premia los verdes largos. En P4, val8, ippo_s42 frente al trivial da J_dec −1.5 % (7/8 semillas prefieren a ippo), pero J_seg +8.4 % y timeLoss +4.8 % (`salidas/c4_alineacion.txt`). En P6 pasa lo mismo: J_red_dec −1.6 % con timeLoss +4.6 % (`salidas/c4_alineacion_p6.txt`).
- **E2.** La exploración independiente rompe el ciclo sincronizado; un sorteo común casi no lo daña (`b2_ruido.txt`):

  | Caso | Programa base | 3 % de ruido independiente | 3 % de ruido común |
  |---|---|---|---|
  | P4 | trivial | +21.7 % | +1.2 % |
  | P6 | 15/10 | +14.7 % | +2.1 % |

- **E5.** Las colas entran con escala casi nula. El p95 de la cola es 0.026, y su sensibilidad en la 1.ª capa, 2.8 % (`salidas/c2_escalas_obs.txt`).

Diseño: un factorial 2×2, {observación normalizada} × {descuento por segundo + exploración común}, más dos brazos sobre V3. En todos: 3 bases, 200 episodios, val8 y la misma regla de selección, base publicada y convergencia.

| id | Cambio | Hipótesis | ¿Se cumplió? |
|---|---|---|---|
| C0 | IPPO vecinos sin cambios, con val8. Se obtuvo re-validando los 60 checkpoints del repo; la réplica salió bit a bit (D4) | Separa el efecto de validar con 8 semillas | Validar con 8 semillas **no ayuda**: +0.5 % [−0.9, 2.0] en P4 y +5.0 % [−1.4, 11.8] en P6 frente al publicado |
| V1 `norm` | Colas y móviles divididos por 10 veh × carriles, con tope 2 | H1: sola no mejora y puede romper la sincronía | **Sí**: V1 − C0 = −0.0 % [−1.7, 1.6] |
| V2 `smdp_crn` | Descuento γ^(dt/5) en GAE más un sorteo común por segundo al explorar | H2: más cambios de fase y menos timeLoss que C0 | **Sí**: 868 cambios frente a 567 de C0; −3.2 % [−4.8, −1.6], p Holm 0.0059 |
| V3 `norm_smdp_crn` | V1 + V2 | H3: interacción negativa (las colas visibles ayudan con la exploración corregida) | **No**: interacción +0.061 s/veh [−0.412, +0.558]; V3 − V2 = +0.2 % [−0.1, 0.5] |
| V4 `mappo_equipo` | V3 + MAPPO con crítico central y recompensa de toda la red (rotonda incluida) | H4: menos timeLoss y menos retraso en SR_RS | **No**: publica el trivial (30/30). SR_RS en val8 da 16 904.1 veh·s, igual al trivial y a V3 |
| V5 `norm_smdp_crn_triv` | V3 + sesgo inicial p(cambiar) ≈ 0.97, así que el ep 0 es el ciclo mínimo | H5: no deriva del trivial (E10) y está cerca de él | **Sí**: deriva +0.6 a +4.6 %, frente a +10.7 a +13.2 % del piloto de clonado. Acuerdo 0.965 |

Las fuentes son `tanda1/salidas/juicio_tanda1.txt` y `tanda1/salidas/diag/srrs_resumen.txt`.

---

## 2. P4 red_alta: cribado (5001-5030) y confirmación (6001-6030)

**Cribado, 5001-5030** (`tanda1/salidas/juicio_tanda1.txt`). Referencias: fijo_2509 30.064, actuado 29.674, trivial 28.152 e IPPO vecinos publicado s42 28.925.

| Brazo (base publicada) | Media | Frente a fijo_2509 | Regla | Frente al trivial | Iguales al trivial | ¿Converge? |
|---|---|---|---|---|---|---|
| C0 (4042) | 29.081 | −3.3 % [−4.8, −1.8] | MEJORA | +3.3 % [1.6, 5.0] | 0/30 | sí (3/3) |
| V1 (4042) | 29.074 | −3.3 % [−4.9, −1.5] | MEJORA | +3.3 % [1.4, 5.3] | 0/30 | sí (3/3) |
| V2 (2042) | 28.152 | −6.4 % [−8.4, −4.3] | FUNCIONA | +0.0 % [0.0, 0.0] | **30/30** | sí (3/3) |
| V3 (4042) | 28.206 | −6.2 % [−8.2, −4.1] | FUNCIONA | +0.2 % [−0.1, 0.5] | 21/30 | sí (3/3) |
| V4 (42) | 28.152 | −6.4 % [−8.4, −4.3] | FUNCIONA | +0.0 % [0.0, 0.0] | **30/30** | sí (3/3) |
| **V5 (42), ganadora** | 28.068 | −6.6 % [−8.6, −4.7] | FUNCIONA | −0.3 % [−0.8, 0.2] | 0/30 | sí (3/3) |

"Iguales al trivial" cuenta las semillas con timeLoss y cambios de fase idénticos al trivial.

**Confirmación de V5, sin re-entrenar, en 6001-6030** (`tanda2/salidas/juicio_tanda2.txt`):
- (a) Frente a fijo_2509: −6.2 % [−7.8, −4.5], p=2.05e-07, FUNCIONA.
- (b) Frente al trivial: +0.0 % [−0.3, 0.4], p=0.395. **No se cumple.** V5 va por debajo del trivial en 17/30 semillas y empata en 5/30 (`conteos_tanda2.txt`).
- En 6011-6030, semillas nunca usadas antes: frente al trivial +0.3 % [0.0, 0.7] y frente a fijo_2509 −7.1 %.
- Frente a C0: −2.7 % [−4.6, −1.0]. Frente a IPPO publicado: −3.2 % [−4.9, −1.5].
- El control de determinismo en la semilla 5001 reprodujo los 6 brazos.

**Lectura.** En P4 toda la ganancia sobre C0 (−3 a −3.5 %) consiste en **pasar del plan casi fijo de ~25/10 al ciclo mínimo**. La corrección de objetivo y exploración (V2) basta para eso. Nada de lo probado supera al ciclo mínimo, y la ventaja de −0.3 % de V5 en 5001-5030 fue maldición del ganador: en 6001-6030 queda en +0.0 %.

---

## 3. P6 malla3_alta (5001-5030)

`tanda2/salidas/juicio_tanda2.txt` y `conteos_tanda2.txt`. Referencias: fijo 15/10 36.843 (sd 2.34), actuado 64.842, trivial 184.394 e IPPO vecinos publicado s42 37.745 (sd 4.55).

| Brazo (base publicada, ep) | Media (sd) | Frente al fijo 15/10 | Regla | Frente a IPPO publicado | Frente a C0-P6 | ¿Converge? (bases) |
|---|---|---|---|---|---|---|
| C0-P6 (4042, ep180) | 39.636 (5.05) | +7.6 % [2.0, 13.3] | PENDIENTE (provisional: FALLA) | +5.0 % [−1.4, 11.8] | — | no (0/3) |
| **V2** (4042, ep160) | 34.141 (1.10) | **−7.3 %** [−10.0, −5.3], p=4.7e-08 | FUNCIONA | **−9.5 %** [−13.8, −5.4] | −13.9 % [−17.7, −10.1] | sí (2/3; la 2042 no) |
| **V5** (42, ep200) | 34.218 (1.46) | **−7.1 %** [−9.8, −4.8], p=3.0e-05 | FUNCIONA | **−9.3 %** [−13.8, −5.1] | −13.7 % [−17.8, −9.5] | sí (2/3; la 2042 no) |

- V5 frente a V2: +0.2 % [−1.4, 2.1], p=0.902. En P6 **el ingrediente activo es el mismo que en P4** (SMDP + exploración común). El arranque en el ciclo mínimo y la observación normalizada no suman.
- Las dos le ganan al 15/10 en 28/30 semillas. Es la **primera vez** que algo le gana de forma consistente al 15/10 en P6: en `mejora_coord` nada lo había hecho.
- Frente al IPPO publicado, V2 gana en 25/30 semillas y V5 en 22/30. Los máximos por semilla son 37.86 (V2) y 40.21 (V5), frente a 50.56 del publicado y 54.27 de C0-P6.
- El criterio pre-registrado "mejora en P6" (§6.1: converge, IC frente a IPPO publicado < 0 y etiqueta distinta de FALLA) **se cumple en las dos**.
- La réplica de C0-P6 difirió solo en `cambios_fase` (4 menos por episodio). Los pesos fueron idénticos bit a bit y queda declarado como T7. No afecta al timeLoss.

### 3.1 Qué aprendió la política en P6 (diagnóstico nuevo, semilla 999)

Fuentes: `sintesis/fases_p6.py` y `sintesis/analizar_fases_p6.py` → `sintesis/analizar_fases_p6.txt`. Las corridas reproducen la val_999 de cada checkpoint; por ejemplo, V2 s4042 da 34.05.

| Programa | Verde E-O: mediana [p10-p90] | Verdes E-O de 10 s | Verde N-S | Ciclo (mediana) | Sincronía con vecinos | Fases/h |
|---|---|---|---|---|---|---|
| fijo 15/10 | 15 [15-15] | 0 % | 10 | 31 | 100 % | 231 |
| trivial | 10 [10-10] | 100 % | 10 | 26 | 100 % | 276 |
| IPPO vecinos publicado s42 | 25 [20-30] | 6 % | 15 [10-20] | 46 | 18.3 % | 161 |
| V2 s4042 | 10 [10-20] | 72 % | 10 | 26 | 63.6 % | 247 |
| V5 s42 | 10 [10-20] | 66 % | 10 | 26 | 60.5 % | 245 |

**Lectura.** IPPO publicado aprendió un plan largo y desincronizado. V2 y V5 aprendieron el **ciclo mínimo como base, con extensiones del verde de avenida (15-35 s) en un 28-34 % de los ciclos** y verde transversal siempre mínimo. No es un plan fijo: los verdes varían dentro de un mismo cruce. Tampoco es el trivial, que en P6 se traba.

**Lo que NO se sabe:** a qué reacciona la extensión (colas, mensajes o reloj). V2 la hace con la observación sin normalizar, así que no depende de ver bien las colas. Tampoco se probó una regla simple de "ciclo mínimo + extender si hay cola", que podría igualarla. Por eso **no hay base para llamarlo "coordinación aprendida"**. La descripción que se sostiene es: "política adaptativa que supera a todas las referencias simples medidas".

---

## 4. P1 corredor: no regresión (solo V5)

Fuente: `tanda2/salidas/juicio_tanda2.txt` §3.
- La base publicada (4042) converge en las 3 bases y da FUNCIONA: −7.3 % [−8.7, −6.0] frente al fijo.
- Frente a IPPO vecinos publicado P1: −0.6 % [−1.5, 0.3]. El límite superior (+0.3 %) cumple el umbral de ≤ +2 %: **NO REGRESIÓN: sí**.
- El ep 0 de V5 (trivial) valida 101.2. El trivial en P1 es malo (102.6 en 5001-5030) y V5 sale de él.

**V2 no se corrió en P1**, y P2, P3 y P5 no se corrieron con ninguna variante.

---

## 5. Chequeos extra de robustez (hechos para esta síntesis; solo leen CSV existentes)

`sintesis/extra_robustez.py` → `sintesis/extra_robustez.txt`, con `evaluar.comparar` (bootstrap pareado 10 000 y Wilcoxon).

**(i) P4 frente al fijo RE-BARRIDO.** Es el programa instalado hoy en `plan2/red_alta.add.xml`: 10/10 con desfases 0/25/24, el que usa la sección de robustez v2.1. Resultados en 5001-5030 (media 27.633):

| Brazo | Frente al fijo re-barrido | Semillas en que gana |
|---|---|---|
| V5 | +1.6 % [−0.2, 3.5], p=0.118 | 13/30 |
| V2 | +1.9 % [−0.0, 3.8], p=0.084 | 12/30 |
| trivial | +1.9 % [−0.0, 3.8], p=0.084 | 12/30 |
| C0 | +5.2 % [3.9, 6.7] | — |
| IPPO publicado | +4.7 % [2.6, 6.8] | — |

→ **En el marco de robustez, la mejora de P4 desaparece**: V5 y V2 empatan (o pierden por poco) con un fijo bien barrido. Esto encaja con b5: los desfases no le ganan de forma robusta al trivial en val8, aunque este programa concreto rinde mejor en 5001-5030.

**(ii) Retraso total (timeLoss + retraso de inserción).** Sirve para ver si la ganancia es cola desplazada fuera de la red.
- En P4, el retraso de inserción es 0.336 s/veh en todos los brazos. V5 frente a fijo_2509 da −6.6 % [−8.5, −4.6], la misma lectura.
- En P6, el retraso de inserción es ~45.5 s/veh **igual en todos los brazos** (45.41-45.53), con 0 vehículos no insertados y 0 no terminados. No es cola desplazada, pero ese término común diluye la ganancia:

  | Brazo | Frente al fijo 15/10 | Frente a IPPO publicado |
  |---|---|---|
  | V5 | −3.2 % [−4.4, −2.0] (28/30) | −4.1 % [−6.3, −2.1] |
  | V2 | −3.2 % [−4.4, −2.3] (28/30) | −4.2 % [−6.3, −2.3] |

  En retraso total P6 **no llega al −5 %**. La cola máxima de enlace media también baja: 9.8 (V5) y 11.6 (V2), frente a 16.6 de IPPO publicado y 19.8 de C0.
- En P1, V5 frente al fijo da −7.1 % [−8.5, −5.9], y frente a IPPO publicado, −0.6 % [−1.5, 0.3].

---

## 6. ¿Le gana al trivial? ¿Converge? ¿Con qué confianza?

| Pregunta | Respuesta | Confianza |
|---|---|---|
| ¿Le gana al TRIVIAL en P4? | **No.** Lo reproduce: V2 y V4 idénticos en 30/30; V5 +0.0 % [−0.3, 0.4] en 6001-6030 | Alta (confirmado en semillas nuevas) |
| ¿Mejora sobre IPPO vecinos actual en P4? | Sí, −2.7 % a −3.5 %, porque pasa al ciclo mínimo | Alta en timeLoss frente a fijo_2509; **nula** frente al fijo re-barrido |
| ¿Mejora en P6? | Sí: −7 % frente al 15/10 y −9 % frente a IPPO publicado; política adaptativa, no trivial | **Moderada**: un solo juego de 30 semillas, sin 6001-6030; 1 de 3 bases no converge; −3.2 % en retraso total |
| ¿Converge en P6? | La base publicada sí, según la regla (V5 plateau −4.6 %, V2 +3.2 %), en 2/3 bases por variante. La 2042 no converge (V5 −21.6 %, V2 −6.7 %). La V5 publicada se elige en el ep 200 (el último), así que la curva seguía bajando. En val hay colapsos puntuales de checkpoints intermedios (p. ej. 55.22 en una semilla del ep 120 de V2 s4042) | Moderada |
| ¿No empeora P1? | V5: no empeora (−0.6 % [−1.5, 0.3]). V2: sin medir | Alta para V5 |
| ¿Cuál es el ingrediente activo? | SMDP + exploración común (V2 − C0 −3.2 %; V5 ≈ V2 en P6) | Moderada-alta: factorial con Holm en P4 y concordancia en P6. Los dos cambios van juntos en V2, así que no se separa cuál de los dos pesa más |

Limitaciones comunes:
- La demanda es determinista (`vehsPerHour` en los `.rou.xml`, sin `probability`), así que las semillas solo varían `sigma`.
- La exploración común usa logp marginales, un estimador sesgado cuando las p difieren entre agentes. Es una heurística declarada.
- 3 bases por brazo.
- El pre-registro predijo "EXITO improbable; V5 cerca del trivial" en P4, y así fue. En P6 predijo "buscar ≥ EMPATA; ganarle al 15/10 no se espera": ahí el resultado **sorprendió**, y justamente por eso necesita confirmación.

---

## 7. Qué hacer con esto en la tesis

### (a) Hallazgos que ya valen para la tesis (explican por qué el método actual no mejora en P4-P6)

Son diagnósticos sobre las políticas y el código existentes. No cambian ningún veredicto ni usan 1001-1030. Pueden ir en la discusión del Cap. V o en Limitaciones, citados como "análisis de diagnóstico en semillas fuera del examen".

1. **Qué aprende IPPO vecinos.**
   - En P3/P5: el ciclo mínimo sincronizado por mensajes. Si se corta el canal, el timeLoss sube +70 a +80 % (`mejora_coord/a3`).
   - En P4/P6: un plan casi fijo largo y poco sincronizado. En P4 es ~25/10 con ciclo de 41 s. En P6 es 25/15 con ciclo de 46 s y 18 % de sincronía (§3.1).
2. **Por qué.**
   - El descuento por decisión (γ por decisión y no por segundo) hace que el criterio de entrenamiento prefiera los verdes largos, aunque cuesten más por segundo (E1).
   - La exploración independiente rompe la sincronía y así penaliza al ciclo corto durante el entrenamiento (E2): +21.7 % en P4 y +14.7 % en P6 con 3 % de ruido.
   - Corregir las dos cosas lleva a IPPO al ciclo mínimo en P4 (idéntico en 30/30 semillas) y lo baja un 14 % frente a C0 en P6.
3. **Lo que NO es la causa.**
   - La escala de las colas: normalizarlas no cambia nada, V1 − C0 = −0.0 %.
   - La recompensa local o la falta de crítico central: la recompensa de toda la red con MAPPO no cambia la política ni el retraso en la rotonda.
   - El ruido de selección de checkpoint: validar con 8 semillas no mejora, +0.5 % en P4 y +5.0 % en P6.
4. **El techo en P4 es el ciclo mínimo, y un fijo bien barrido lo alcanza.** Ninguna variante, regla adaptativa ni desfase medido lo supera de forma robusta. Frente al fijo re-barrido, el ciclo mínimo empata (+1.9 % [−0.0, 3.8]).
5. **La coordinación en esta red es sobre todo mantener un ciclo común.** Max-Pressure, saltar fases vacías y la exploración independiente la rompen y empeoran.

### (b) Variantes que podrían entrar como EXPLORATORIAS declaradas

**Candidata:** "IPPO vecinos con descuento por segundo y exploración común" (V2; V5 es equivalente en P6). Si entra, que sea en una subsección aparte ("Análisis exploratorio: corrección del objetivo de entrenamiento"), **fuera del veredicto y de las figuras de mejora**, solo con semillas 5001-5030 y 6001-6030.

Texto mínimo sugerido:

> *Análisis exploratorio (fuera del protocolo pre-registrado).* Después del veredicto se diagnosticaron dos desajustes del entrenamiento de IPPO: el descuento de la ventaja se aplicaba por decisión y no por segundo, y la exploración era independiente entre semáforos, lo que rompe la sincronía del ciclo. Se probaron cinco variantes con un pre-registro propio (3 bases, 200 episodios, validación con 8 semillas y la misma regla de selección), evaluadas en semillas distintas de las del examen (5001-5030; confirmación en 6001-6030). Corregir ambos puntos lleva la política de P4 exactamente al ciclo mínimo 10/3/10/3 (−6.2 % frente al fijo del 25.09 en 6001-6030, sin diferencia con el ciclo mínimo, +0.0 % [−0.3, 0.4]), y no supera al fijo re-barrido. En P6 produce una política de ciclo mínimo con extensiones del verde de avenida que mejora al fijo 15/10 en −7.3 % [−10.0, −5.3] y a IPPO vecinos en −9.5 % [−13.8, −5.4] (5001-5030; −3.2 % en retraso total), aunque sin confirmación en semillas nuevas y con una de tres bases sin converger. Normalizar la observación, usar una recompensa de toda la red con crítico central o validar con más semillas no cambió los resultados. Estos números no modifican el veredicto pre-registrado.

Lo que habría que declarar junto al texto:
- (1) Se decidió después de ver el veredicto (post hoc).
- (2) La ganadora de P4 se eligió en 5001-5030 y solo 6001-6030 la confirma.
- (3) P6 no tiene confirmación.
- (4) Frente al fijo re-barrido, P4 empata.
- (5) Solo se verificó la no regresión en P1 y con V5, no con V2.
- (6) Las desviaciones D1-D11 y T1-T7.

**Mi recomendación.** Incluir los hallazgos (a) sí; valen por sí solos. Incluir la variante (b) solo si antes se confirma P6 en 6001-6030. Si no, dejarla en Recomendaciones / trabajo futuro con 2-3 frases. Sin esa confirmación, el único resultado nuevo con contenido (P6) queda en una sola muestra de 30 semillas, y su efecto se reduce a la mitad en retraso total.

### Trabajo futuro (por orden de valor por costo)

Los tiempos son estimaciones a partir de `tanda2/salidas/tiempos.csv`.
1. **Confirmar P6 en 6001-6030**: V2 s4042 y V5 s42 congeladas, más fijo 15/10, actuado, trivial e IPPO publicado simulados ahí. Las políticas ya están entrenadas; cada evaluación de 15 semillas tardó 305-380 s, así que es menos de 1 h de reloj con procesos en paralelo.
2. **No regresión de V2 en P1, y de V2 en P3/P5.** Allí IPPO ya es el trivial, así que se espera un empate, pero no está medido.
3. **Caracterizar a qué reacciona la extensión del verde en P6**: sensibilidad de la entrada, como `mejora_coord/a3`. Probar además una regla "ciclo mínimo + extender si cola > x" como referencia.
4. **Separar SMDP y exploración común** (V2 los junta) y repetir con demanda aleatoria (Poisson). Todo lo anterior es con demanda determinista.

---

## 8. Archivos

- **Diseño:** `PRERREGISTRO.md`, `prerregistro.sha256`, `DESVIACIONES.md`, `b*_*.txt`, `salidas/c*_*.txt`.
- **Tanda 1 (P4):** `tanda1/salidas/juicio_tanda1.{txt,json}`, `seleccion_V*.json`, `identidad_v5_v3.txt`, `diag/srrs_resumen.txt`, `diag/acuerdo_*.json`, `tiempos.csv`; `tanda1/c0/salidas/replica.txt`.
- **Tanda 2 (P4 conf., P6, P1):** `tanda2/salidas/juicio_tanda2.{txt,json}`, `conteos_tanda2.txt`, `seleccion_P6_V{2,5}.json`, `seleccion_P1_V5.json`, `tiempos*.csv`; `tanda2/c0p6/salidas/replica.txt`.
- **Código de las variantes:** `V1..V5/code` (parches `V*/parchar_v*.py`) y políticas en `V*/plan2/politica_*.pt|json`.
- **Esta síntesis (nuevo):** `sintesis/extra_robustez.{py,txt}` (fijo re-barrido y retraso total); `sintesis/fases_p6.py` y `sintesis/analizar_fases_p6.{py,txt}` (fases en P6, semilla 999; corridas en `sintesis/run/`).
