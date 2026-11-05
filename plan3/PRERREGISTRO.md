# Prerregistro del bloque nuevo (plan 3)

**Estado: PARTE A,** fijada antes de la primera noche de cómputo. Viene del borrador del 05.11.2026, revisado con
las críticas de método, factibilidad e impacto.

- Fabian tomó las decisiones A1-A8 de `doc/DECISIONES.md` el 05.11.2026, todas con la opción recomendada (§18); las
  técnicas B1-B25 van por defecto. Las marcas **[A#]** dicen dónde se usa cada decisión.
- **Se fija en dos partes**, cada una con su sha256, un commit de Fabian, push a origin, un tag anotado y un correo al
  asesor con el sha256 y el commit:
  - **Parte A: todo este documento** (§0-§18), antes de la primera noche (día 4). Contiene todas las reglas,
    hipótesis, familias, márgenes, semillas y la plantilla de redacción.
  - **Parte B: solo** `plan3/referencias_congeladas.json` (archivo y sha256 de cada referencia ganadora) y los detalles
    que no cambian ninguna regla (valores finales de la mezcla con sus fuentes). Va antes de la primera evaluación
    decisiva (día 14).
- Después de la parte A, todo cambio es una enmienda (§14).

**Marcas:** [M] medido, [I] inferido, [S] supuesto, [L] literatura. Las rutas `plan3/<área>/...` y `plan3/final/...`
de las evidencias son del diseño, fuera del repositorio: `C:/Users/GAMER/Documents/demo_rl_semaforo/analisis_mejora_2026-11-04/`.

---

## 0. Qué es y qué no cambia

- **Es un segundo estudio, posterior a lo entregado.** No cambia ningún veredicto entregado (§16).
- **No tiene puertas.** Se corre todo lo que este documento lista. Lo que antes era una puerta ahora es un resultado.
- **Nada se elige con las semillas decisivas** (§3): ni checkpoint, ni base, ni variante, ni referencia, ni número de
  semillas, ni qué modelo se cita.
- **A ciegas** [A5]. Los resultados de las tandas decisivas se escriben en una carpeta fuera de git y nadie los abre
  hasta el cierre (`plan3/listo/cierre.ok`). Cada mañana solo se sube su sha256. §14 dice cómo.
- **Modelo base: V2** (IPPO con mensajes, descuento por segundo y exploración común, `--v2`), elegido por retraso total
  (`--criterio-val total`) y validado con 16 semillas. Con llegadas aleatorias, la misma V2 entrenada con ellas.
  **V2 es la base de todas las variantes, pase o no H1.**
- **Modelo citado** [A4]. En cada celda se cita el modelo que gana la regla de promoción (§12): V2 o una variante
  prerregistrada que le gane en una validación nueva. La etiqueta de V2 se informa siempre.

## 1. Preguntas

1. **Llegadas regulares.** ¿Corregir el entrenamiento (V2) mejora a IPPO con mensajes frente a un plan fijo bien
   ajustado, sin empeorar donde ya funcionaba? ¿Cuánto viene de cómo se elige la versión (control C0)?
2. **Llegadas aleatorias.** ¿IPPO con mensajes, entrenado con esa demanda, le gana a un fijo re-ajustado con ella? ¿La
   ventaja es mayor que con llegadas regulares? ¿Los mensajes siguen importando?
3. **Observación nueva.** ¿Ver el giro que bloquea el carril, la espera del primer vehículo y su salida corrige las
   fallas con saturación (2715 veh/h y P2)?
4. **Más episodios.** ¿Mejoran la versión evaluada? Sin veredicto.
5. **Reloj de 2 s** [A4]. ¿Decidir cada 2 s en vez de cada 5 s mejora a IPPO con mensajes?
6. **Modelo completo** [A4]. ¿Las mejoras juntas mejoran a V2? ¿Qué modelo se cita en cada celda?
7. **Una política por red** [A6]. ¿Sostiene todos los niveles de demanda de su red?

## 2. Palabras que se usan

| Palabra | Qué es |
|---|---|
| Celda | Un caso (P1-P6, P6e, un nivel de demanda, D) con un tipo de llegadas |
| P6e | P6 con la entrada corregida: cada vehículo entra por el carril que le conviene (`departLane="best"`) |
| Brazo | Un control evaluado: una base de un modelo, una versión evaluada o una referencia |
| Base | Un entrenamiento: semilla 42, 2042 o 4042; en el modelo principal (V2 en P1-P6 y P6e, regular y aleatoria) y en H8a, también 14042 y 16042 |
| Versión evaluada | La base mediana por su validación elegida (§6) |
| Tanda | Un juego de semillas de evaluación: 30 con llegadas regulares (120 para H1 y H2), 100 con aleatorias |
| T1, T2 | Las dos tandas decisivas de cada tipo de llegadas |
| Cambio | (media del brazo − media de la referencia) / media de la referencia × 100, pareado por semilla |
| Etiqueta citable | La que se repite en T1 y T2 (§7) |
| Afirmación de método | Toda hipótesis que diga que una forma de entrenar o de decidir es mejor que otra, o que un método le gana a una referencia |

## 3. Semillas

Comprobadas libres: 0 usos en CSV o JSON del repositorio, de `demo_rl_diag`, de los datos fuera del repositorio y de
las carpetas de análisis del 04.11 y del 05.11 [M `plan3/final/semillas/t3_semillas_plan3.txt`].

| Uso | Llegadas regulares | Llegadas aleatorias |
|---|---|---|
| Entrenamiento (episodio k = base + k) | 43-242, 2043-2242, 4043-4242, 14043-14242, 16043-16242; con 400 episodios hasta 442, 2442 y 4442; con 600 (política por red) hasta 642, 2642 y 4642 | iguales; cada semilla da otras llegadas |
| Validación (16) [A3] | 999, 1999, 2999, 3999, 4999, 7999, 8999, 9999 y 15001-15008 | iguales |
| Validación de la política por red | 8 semillas (999…9999) × 3 niveles | — |
| **Promoción** [A4] (§12) | 15009-15024 | iguales |
| Ajuste de referencias | Rejilla con 2001-2003; las 10 mejores con 2001-2010; desempate de frágiles con 2001-2030 | Etapas gruesa y fina con 2001-2010; 10 finalistas con 2001-2030 |
| **T1 decisiva** | **8001-8030** (H1 y H2: 8001-8120) | **7001-7100** |
| **T2 decisiva** | **13001-13030** (H1 y H2: 13001-13120) | **10001-10100** |
| Puente con lo entregado (solo descriptivo) | 1001-1030 | — |
| No regresión (solo controles entregados) | 1001-1002 | — |
| Prueba final reservada (§13) | 11001-11030 | 12001-12100 |
| Humo y pruebas (también R0.3) | base 7 y 424301-424360 | iguales |
| Sin uso | 9001-9030 | — |
| Prohibidas para lo nuevo | 5001-5030, 6001-6030; 1001-1030 salvo puente y no regresión | iguales |

**Tabla para la máquina.** `plan3/protecciones.py` lee este bloque (y solo este) y comprueba en cada trabajo que el
sha256 de este documento coincide con el de origin. Una semilla fuera del uso declarado del trabajo lo rechaza.

```json
{
  "bases": {"principal": [42, 2042, 4042, 14042, 16042], "variantes": [42, 2042, 4042], "humo": [7]},
  "semillas": {
    "validacion": [[999, 999], [1999, 1999], [2999, 2999], [3999, 3999], [4999, 4999], [7999, 7999],
                   [8999, 8999], [9999, 9999], [15001, 15008]],
    "promocion": [[15009, 15024]],
    "ajuste": [[2001, 2030]],
    "examen_regular": [[8001, 8030], [13001, 13030]],
    "examen_h1": [[8001, 8120], [13001, 13120]],
    "examen_aleatorio": [[7001, 7100], [10001, 10100]],
    "puente": [[1001, 1030]],
    "no_regresion": [[1001, 1002]],
    "final": [[11001, 11030], [12001, 12100]],
    "humo": [[424301, 424360]]
  },
  "prohibidas": [[5001, 5030], [6001, 6030], [9001, 9030]],
  "scripts": ["../con_escenarios.py", "../rl_ippo.py", "../evaluar.py", "../barrer_fijo.py", "barrer_fino.py",
              "franja.py", "actuado.py", "reglas.py", "evaluar3.py", "revalidar_c0.py", "p3_elegir.py",
              "p3_promocion.py", "manifiesto.py", "veredicto3.py", "p3_preparar.py", "demanda_estocastica.py"],
  "etiqueta": "^p3[a-z0-9]+$"
}
```

**Por qué 1001-1030 no decide.** En el corredor (P1, P2, 905, 1358 y 2715 veh/h), V2 ya se evaluó en 1001-1030 y
6001-6030. Se eligió frente a INS, V2+INS y V2+INS+obs con esas cifras a la vista (Enmiendas 2 y 3 del diagnóstico), y
el programa del 04.11 la llevó a todos los casos también con ellas a la vista. El criterio de retraso total, en cambio,
se fijó antes de entrenar (Enmienda 1) [M `plan2/diag_corredor/PRERREGISTRO.md` l. 57-68]. Para que todas las celdas
tengan el mismo protocolo, ninguna decide con 1001-1030.

## 4. Métricas

- **Principal: retraso total por vehículo** (`retraso_total_prom`): timeLoss, más la espera para entrar, más la espera
  de los que no alcanzaron a entrar. Con ella se elige la versión y se da la etiqueta.
- **Secundarias**, con la misma estadística:
  - timeLoss, espera para entrar, vehículos no insertados y cambios de fase;
  - **en los corredores** (P1, P2, niveles del corredor, D): el retraso total por media hora, según la salida pedida
    (salida − espera para entrar); periodo 1 antes de 1800 s y periodo 2 desde 1800 s; los no insertados se asignan a
    su periodo por su salida programada y se informan aparte;
  - **en P6 y P6e con llegadas aleatorias:** la mediana del retraso total y la proporción de episodios con retraso
    mayor que 1.3 veces la mediana del fijo (colas encadenadas que dominan la media) [M
    `plan3/demanda/salidas/prueba_e_corridas.csv`];
  - **en P6 con llegadas regulares:** la mediana del fijo fino en el examen y cuántas semillas se le traban (retraso
    total mayor que 1.10 veces su mediana) [A1].
- **Entrada a la red** [A2]:
  - con llegadas aleatorias, perfil, mezcla y en los corredores nuevos (si se corren), los vehículos entran por el mejor
    carril (`departLane="best"`);
  - lo que repite casos entregados con llegadas regulares mantiene la entrada de SUMO por defecto; también la política
    por red, que se compara con la V2 de cada nivel;
  - **P6e** es P6 con la entrada corregida y llegadas regulares.
  - En P1-P4 las dos entradas dan lo mismo y en P5 difieren 0.2 s/veh [M]. En P6, con la entrada por defecto, el 55 %
    del retraso total es espera para entrar, casi igual en todos los brazos [M]. **Lectura obligada en P6:** el cambio
    relativo está diluido a la mitad; se informa también el de P6e.
- El redondeo de `exp()` al segundo agrega +0.5 s/veh de espera con llegadas aleatorias, igual en todos los brazos
  [M `plan3/demanda/salidas/prueba_e_resumen.txt`].
- **Cierre de la simulación.** Cada episodio cierra a más tardar a los 6000 s, como en lo entregado. Un vehículo que a
  esa hora todavía espera entrar cuenta con la espera que llevaba: es una cota inferior de su retraso. Con llegadas
  aleatorias en P2 la espera para entrar es larga (312 s/veh con el fijo instalado y el último vehículo llega a los
  5724 s, en semillas de humo [M `plan3/pruebas/esc/salidas/cargas.txt`]), así que alguna semilla puede tocar el
  cierre. Por celda y brazo se informan las semillas con no insertados al cerrar y cuántos vehículos. **Lectura
  obligada:** si un brazo deja vehículos sin entrar, su retraso total está subestimado y la diferencia con un brazo
  que no los deja es conservadora.

## 5. Referencias

Todas se ajustan **solo con semillas de ajuste** (§3), con la misma demanda y la misma entrada que el modelo. Con
llegadas aleatorias se re-ajustan con ellas. Los ganadores salen de estas reglas y se registran con su sha256 en
`plan3/referencias_congeladas.json` (parte B).

| Referencia | Cómo se ajusta | Papel | Lectura obligada si iguala o supera al modelo |
|---|---|---|---|
| **Fijo fino** [A1]: un plan para toda la hora | Etapa gruesa desde 10 s; etapa fina de 1 s alrededor de cada mínimo local a ≤ 2 % del mejor (con llegadas aleatorias, a ≤ 2 errores estándar de la diferencia pareada), tope 3; desfases finos ±4 s; malla con sus 3 esquemas y `onda_oe`; desempate de las 10 mejores por la media (2001-2010; 2001-2030 con llegadas aleatorias). **Ganador frágil:** si los dos primeros quedan a ≤ 2 % o el ganador tiene una semilla con retraso total > 1.10 veces su mediana, se desempata entre los 3 primeros con 2001-2030 y gana la menor media | **Decide la etiqueta** | — |
| **Actuado ajustado** [A1] | Descenso por coordenadas en cadena con rejillas fijas (DECISIONES B9), que incluyen los valores por defecto; variante coordinada con los desfases del fijo fino; 2001-2003, y los 3 mejores con 2001-2010 (con llegadas aleatorias, los 10 mejores con 2001-2030) | **Veta FUNCIONA** | — |
| **Fijo con verdes de 5 en 5** [A1] | Los 3 mejores planes de la etapa gruesa (verdes múltiplos de 5 s) con desfases finos ±4 s; desempate como el fijo fino | Al lado | "Parte de la ventaja del fijo fino viene de verdes que IPPO, al decidir cada 5 s, no puede dar" |
| Fijo por franja: un plan por media hora | Los 3 mejores de cada periodo según el puntaje por periodo; 9 pares; los 3 mejores pares con 2001-2010 (con llegadas aleatorias, los 10 mejores con 2001-2030). WAUT por semáforo en un instante limpio | Al lado | "La ventaja frente al fijo la logra también un plan por horario" |
| Fijo por bloques (solo en el perfil) | Un plan por bloque de 10 min con el puntaje por bloque; secuencia verificada con 2001-2030 | Al lado | Igual que la franja |
| Regla simple: ciclo mínimo y alargar el verde si hay cola | U ∈ {1, 2, 3, 4, 6} × G ∈ {30, 60}; 2001-2003 y las 3 mejores con 2001-2010 (con llegadas aleatorias, las 10 mejores con 2001-2030) | Al lado | Prohibido decir "aprendió algo que la regla no hace" o "coordinación aprendida" |
| Ciclo mínimo: verdes mínimos, desfases 0 | — | Al lado y como marca | "Reproduce el ciclo mínimo" si la media de retraso y la de espera coinciden hasta 0.0005 s |
| Fijo entregado (rejilla de 5 s) | El de la robustez v2.1 | Al lado, solo para comparar con lo entregado | — |
| Actuado por defecto | El de `comun.archivo_actuado` | Al lado | — |
| Max-Pressure (por carril, verde mínimo 10 s, con y sin ciclo máximo) | Igual que la regla | Solo descriptiva | — (en SUMO suele perder contra buenos fijos [L]) |
| IPPO entregado y C0 | — | Comparadores del modelo (§8) | — |

**Del fijo fino frente a IPPO.** El fijo fino puede usar verdes de 12 o 14 s. IPPO decide cada 5 s y solo da verdes de
10, 15, 20... s [M `rl_ippo.py` l. 671-678]. Se declara. El fijo de verdes de 5 en 5 mide ese límite.

**Inserción en los escenarios nuevos** [A2]: `departLane="best"` en cada flujo de los escenarios nuevos
(`plan3/demanda_estocastica.py`), no como opción por defecto de SUMO. En SUMO 1.25 las dos formas eligen el carril de
manera distinta (el atributo del flujo usa el carril libre; la opción, el carril probable): en P6 regular, la espera
para entrar del fijo es 0.28 s/veh con el atributo y 0.30 con la opción, y el retraso total 36.40 y 37.27 s/veh [M
`plan3/pruebas/esc/salidas/`, 3 semillas de humo]. Las cifras del diseño citadas en §4 y §15 se midieron con la opción.

## 6. Versión evaluada, emparejamiento y convergencia

- **Checkpoint publicado de cada base:** el de menor retraso total medio en las 16 semillas de validación; si hay
  empate, el más tardío (`rl_ippo.elegir_checkpoint`). Se valida cada 10 episodios en todas las celdas. La política por
  red usa su protocolo: 8 semillas × 3 niveles cada 20 episodios, por la media geométrica del retraso total.
- **Versión evaluada:** la base mediana por `val_elegido`: la 3.ª de 5 o la 2.ª de 3; empate, la base menor. Si cayó
  una base (§14) y quedan bases en número par, la peor de las dos centrales.
- **La mejor base por validación** se informa al lado de cada etiqueta, como secundaria prerregistrada [A3]. No decide.
- **Qué V2 va en cada comparación.**
  - Frente a las referencias (etiquetas, H3, H5, H6): la V2 evaluada entre sus 5 bases.
  - Frente a C0, al IPPO entregado y a la V2 vieja (H1, H2, el cuadro 2×2 y el puente): la V2 evaluada entre 42, 2042
    y 4042.
  - Frente a un brazo de 3 bases (sin mensajes, observación nueva, limpiezas, 400 episodios, entropía, reloj de 2 s,
    modelo completo): la V2 evaluada entre 42, 2042 y 4042.
- **Emparejamiento por base.** Dos brazos entrenados se comparan base con base (misma semilla: mismos pesos iniciales
  cuando la red es igual, y las mismas llegadas en cada episodio) [M `rl_ippo.py`, `sembrar` y episodio k = base + k].
- **V2 vieja:** el checkpoint que elegiría la regla del 25.09 (timeLoss en 999 y 1999) en las bases 42, 2042 y 4042,
  leído de los `.json`.
- **Convergencia.** Sobre la media de las 16 semillas en la métrica con que se elige (`val_total_serie`, último valor de
  cada fila). El cálculo es el del Cap. III (último tercio, meseta y estabilidad, con tope de 5 %); allí se aplicaba al
  timeLoss en 999 y 1999 (l. 1450-1464). Con 16 semillas es más fácil de cumplir, y se declara. No se usa
  `veredicto.info_base`: con más de 2 semillas toma una semilla en lugar de la media [M
  `plan3/veredicto/salidas/t1_convergencia.txt`].
- **PENDIENTE por ruido** (una política de calidad constante que sale "no convergió"):

  | | P1 | P2-P5 | P6 |
  |---|---|---|---|
  | Llegadas regulares, 16 semillas | 0-1 % [I Monte Carlo, `plan3/veredicto/salidas/t5b.txt`] | 0-1 % [I] | ~10 % [I] |
  | Llegadas aleatorias, 16 semillas | 0.0 % [M `plan3/critica_resultados/RESUMEN.txt` §3] | no medido | 2.2 % (entrada corregida) [M] |

  Lo de llegadas aleatorias se midió re-validando IPPO entregado (20 y 10 checkpoints × 16 semillas), como sustituto.
  Si una celda queda PENDIENTE, se informa su número junto a la etiqueta provisional.
- **No se agregan episodios a ninguna celda** para quitar un PENDIENTE (Cap. III, l. 1492-1495).
- **Corredor y D** se reentrenan con este protocolo; sus pesos deben coincidir con los de `demo_rl_diag` (comparando
  tensores) [M para 10 y 20 episodios: `plan3/modelo/salidas/v2val8_vs_val2.txt`]. La V2 de la Sección 5.5.1 queda
  como está; si la versión evaluada cambia, se muestran las dos.
- **Columnas descriptivas** de `recomendaciones.tex` (l. 84-92): distancia entre la validación elegida y la mediana de
  la serie; si el mínimo se repite en dos validaciones seguidas.

## 7. Comparación, etiqueta y acuerdo entre tandas

**Comparación.** La misma de lo entregado, con `consolidar.comparar`:
- cambio % pareado por semilla; **es un error si falta una semilla esperada o si sobra una**;
- IC95 por bootstrap pareado (10 000 remuestreos, `default_rng(0)`), redondeado a 2 decimales;
- p de Wilcoxon pareado de dos colas (con 100 semillas, la aproximación normal).

Se marcan las celdas con un extremo del IC a menos de 0.05 puntos del 0. En cada celda y tanda se comprueba que todos
los brazos generan los mismos vehículos por semilla.

**Etiqueta de cada celda en cada tanda.** La regla de `veredicto.py`, sin cambios, frente al fijo fino, con el veto del
actuado ajustado:

| Etiqueta | Condición |
|---|---|
| FUNCIONA | IC95 entero bajo cero, p < 0.05, cambio ≤ −5 % y no pierde contra el actuado ajustado (IC entero sobre cero con p < 0.05) |
| MEJORA | IC entero bajo cero y p < 0.05, pero cambio > −5 % o pierde contra el actuado ajustado |
| FALLA | IC entero sobre cero y p < 0.05 |
| EMPATA | El resto |
| PENDIENTE | Falta algo o la versión evaluada no convergió; se escribe la etiqueta provisional |

Las etiquetas no se corrigen por pruebas múltiples: la protección es la réplica. Si no hay efecto, una celda da MEJORA
en las dos tandas con probabilidad 0.025² ≈ 0.0006 [I].

**Etiqueta citable: solo se afirma lo que se repite** [A5].

| T1 | T2 | Etiqueta citable |
|---|---|---|
| igual | igual | esa |
| FUNCIONA | MEJORA (o al revés) | MEJORA |
| MEJORA o FUNCIONA | EMPATA | EMPATA (mejora no confirmada) |
| FALLA | EMPATA | EMPATA (falla no confirmada) |
| MEJORA o FUNCIONA | FALLA | CONTRADICTORIO (no se concluye) |
| PENDIENTE en cualquiera | | PENDIENTE |

**Sentido entre entrenamientos** [A5]. Se exige en **toda afirmación de método**, además de la prueba con las
versiones evaluadas:
- para cada base (emparejada por semilla si se comparan dos brazos entrenados; frente a la referencia si se compara con
  una referencia), el cambio estimado va del lado de la afirmación;
- **con 5 bases, en 4 de 5; con 3 bases, en las 3; en T1 y en T2**;
- en una no inferioridad, "del lado" quiere decir bajo el margen (+2 %).

La etiqueta de la versión evaluada no cambia por esto: se agrega la columna "se repite en k de n entrenamientos".

**Número único.** Media geométrica, sobre P1-P6, del cociente modelo citado / fijo fino, con P6 (no P6e). Al lado, la
misma frente al fijo entregado y, si el modelo citado no es V2 en todas las celdas, la de V2. Una cifra por tanda y por
tipo de llegadas; nunca se mezclan tandas en una cifra ni en una frase, y nunca se cita una sola tanda sin la otra. Se calcula dentro de `veredicto3` con
`sintesis_plan.indice_geo` [M l. 106]; nunca se corre `sintesis_plan.py`, que escribe en `plan2/` y `TESIS/`.

## 8. Hipótesis por etapa

**Definiciones comunes.**
- **Superioridad (a < b):** IC95 del cambio entero bajo cero **y** p de Wilcoxon, ajustado por Holm, < 0.05.
- **No inferioridad (a no es peor que b en más de 2 %)** [A5], con tres lecturas:
  - *no es peor:* límite superior del IC95 ≤ +2 % y p de una cola (Wilcoxon sobre a − 1.02·b, alternativa "menor"),
    ajustado por Holm, < 0.05;
  - *es peor:* IC95 entero sobre +2 %;
  - *no concluyente:* el resto (por ejemplo, el IC95 cruza +2 %).
- **Equivalencia ±1 %:** el IC95 del cambio queda dentro de [−1, +1] %.
- **Pasa:** en T1 y en T2, cada una con su Holm dentro de la familia, **y** con el sentido entre entrenamientos (§7)
  cuando es una afirmación de método.
- Toda hipótesis se informa, pase o no.

### Etapa 0. Referencias (sin entrenar)

| Id | Qué se mide | Papel |
|---|---|---|
| R0.1 | Fijo fino de cada celda (§5) | Define la referencia |
| R0.2 | Franja, actuado ajustado, fijo de verdes de 5 en 5, regla y MP de cada celda | Referencias al lado |
| R0.3 | En P3, P4 y red 2715 y 3620: qué parte del retraso no toca ningún semáforo (rotonda, `--edgedata-output`), con semillas de humo | Descriptiva |

### Etapa 1. V2 en todos los casos, llegadas regulares

**Control C0.** Los 60 checkpoints de IPPO entregado de cada celda, re-validados con las 16 semillas y elegidos por
retraso total, sin entrenar. Antes se comprueba que 999 y 1999 reproducen lo guardado. Como la validación no cambia el
entrenamiento [M], C0 es "IPPO entregado con la selección nueva". **C0 nunca se cita en lugar del IPPO entregado.** Con
C0, V2, IPPO entregado y la V2 vieja se arma el cuadro 2×2: entrenamiento viejo o V2, por selección vieja o nueva.

| Id | Hipótesis | Prueba | Familia (Holm) |
|---|---|---|---|
| H1 | V2 no es peor que C0 en ningún caso | **Global, por intersección-unión:** pasa si cada caso de P1-P6 da "no es peor" al 5 %, en T1 y T2, con 120 semillas por tanda. **Por caso:** tres lecturas, con Holm. V2 evaluada entre 42, 2042 y 4042 | Global: sin Holm. Por caso: 6. Frente al IPPO entregado: otra familia de 6, secundaria |
| H2 | V2 < C0 en P4 y en la malla con 6525 veh/h | Superioridad con 120 semillas por tanda; sentido: las 3 bases emparejadas (V2 de la base b frente a C0 de la base b) | 2 |
| H3 | En P6 (entrada por defecto), la etiqueta citable de V2 es MEJORA o FUNCIONA frente al fijo fino | Etiqueta citable, versión evaluada convergida y sentido 4 de 5 | Sin Holm (la réplica controla el error) |
| H3e | Lo mismo en P6e | Igual | Descriptiva |
| H4 | En P3, P5 y la malla con 1810, 2715 y 3620 veh/h, cada base queda a ±1 % del ciclo mínimo | Equivalencia por base, en T1 y T2 | Descriptiva (k de n bases) |
| H7r | Con mensajes < sin mensajes (V2) en P1, P2 y P6 | Superioridad; sentido 3 de 3 emparejadas | 3 |
| — | Ablación: solo descuento y solo exploración común, en P4 y P6 | Cambios frente a V2 y C0 | Descriptiva |
| — | Los 12 niveles | Etiqueta citable de cada nivel frente a su fijo fino. Se espera que la referencia nueva baje etiquetas entregadas: es una corrección de la referencia y lo entregado no cambia | Descriptiva |
| — | Puente | V2 (de 42, 2042 y 4042), V2 vieja y C0 en 1001-1030, frente al **fijo entregado** y al IPPO entregado | Descriptiva; nunca va al resumen |

**Lectura obligada de H1.** Si un caso sale "es peor", se dice en cuál y cuánto. Si sale "no concluyente", se escribe
que no se puede afirmar ni descartar una pérdida mayor que 2 %. V2 sigue siendo la base de las variantes en todos los
casos.

### Etapa 2. Llegadas aleatorias, con y sin mensajes

| Id | Hipótesis | Prueba | Familia (Holm) |
|---|---|---|---|
| H0 | ¿El desorden abre margen? En cuántos casos un control que reacciona da MEJORA o FUNCIONA frente al fijo fino re-ajustado con llegadas aleatorias: actuado por defecto o ajustado, regla simple, MP, IPPO entregado y V2 regular (en P6, la de P6e) | Cuenta de etiquetas citables en T1 y T2 | Descriptiva |
| H5 | V2 con mensajes, entrenada con llegadas aleatorias, da MEJORA o FUNCIONA frente al fijo fino re-ajustado en al menos 3 de los 6 casos | Cuenta de etiquetas citables, cada una con versión convergida y sentido 4 de 5 | Sin Holm |
| H6 | La ventaja frente al fijo es mayor con llegadas aleatorias que con regulares, en el mismo caso | Ver abajo; sentido: D por base (base b en los dos tipos de llegadas), 4 de 5 | 6 |
| H7 | Con mensajes < sin mensajes, con llegadas aleatorias | Superioridad; sentido 3 de 3 emparejadas | 6 (P2 y P6 son los informativos; en P3 y P5 se espera que pase) |
| — | Transferencias: la V2 aleatoria jugada con llegadas regulares (T1 y T2 regulares; P6 en P6e) y la V2 regular jugada con aleatorias (en P6, la de P6e) | Etiquetas y cambios | Descriptiva |
| — | C0 con llegadas aleatorias: la V2 regular (42, 2042 y 4042) re-elegida con validación aleatoria | Separa "entrenar con desorden" de "elegir con desorden" | Descriptiva |
| — | Perfil de 10 min (P1, P3) [A7] | Etiqueta citable frente al fijo de un plan; al lado, el fijo por bloques | Descriptiva |
| — | Mezcla de Lima (P1, P3) y arranque lento de 0.5 s (solo al evaluar) [A7] | Etiqueta citable frente al fijo re-ajustado con la mezcla | Descriptiva; sensibilidad |

**H6 en detalle.**
- D = (cambio con llegadas aleatorias) − (cambio con regulares), cada uno con V2 de ese tipo frente a su fijo fino. H6
  usa V2 y no el modelo citado, para no mezclar cambios de modelo.
- En P6, el lado regular es P6e, con la misma entrada.
- Bootstrap independiente en cada tipo de llegadas (pareado dentro de cada uno), 10 000 remuestreos; T1 aleatoria con
  T1 regular y T2 con T2.
- Pasa si el IC95 de D está entero bajo cero y el p de una cola (fracción de remuestreos con D ≥ 0), ajustado por
  Holm, es < 0.05 en los dos pares, con el sentido por base.

**Prohibido escribir "el techo se mantiene con llegadas aleatorias"** si no falla también H5.

### Etapa 3. Observación nueva, limpiezas, reloj de 2 s y modelo completo

Las variantes se entrenan sobre V2, con 3 bases (5 en 2715 y D para H8a). Se comparan con la V2 de esas mismas bases,
emparejadas.

| Id | Hipótesis | Prueba | Familia (Holm) |
|---|---|---|---|
| H8a | V2 + observación < V2 en 2715, P2 y D, con llegadas regulares | Superioridad; en 2715 y D con 5 bases (sentido 4 de 5) y en P2 con 3 (3 de 3). Se informa aparte el resultado en las bases nuevas 14042 y 16042 | 3 |
| H8b | V2 + observación < V2 con llegadas aleatorias en al menos 1 caso | Superioridad en P1-P6; sentido 3 de 3 | 6 |
| H8c | V2 + observación no es peor que V2 en P1, P3 y P6, con llegadas regulares | No inferioridad, tres lecturas | 3 |
| H12 | V2 + las tres limpiezas juntas no es peor que V2 en P2 y P6 | No inferioridad, tres lecturas | 2 |
| H14 [A4] | V2 con reloj de 2 s < V2 con reloj de 5 s | Superioridad; sentido 3 de 3. Regulares: D, P1, P2 y P6. Aleatorias: P1, P2 y P6. El reloj de 2 s va con `--sin-forzadas` (con 2 s, 4 de cada 5 decisiones del verde mínimo serían forzadas): H14 mide los dos juntos; en D se separan con el brazo de solo `--sin-forzadas` | 4 (regulares) y 3 (aleatorias) |
| H15 [A4] | Modelo completo < V2 | Superioridad; sentido 3 de 3. Regulares: P1, P2, P4 y P6. Aleatorias: P1-P6 | 4 y 6 |
| — | Limpiezas por separado (D) y brazo de entropía (P1 y D) | Cambios frente a V2 | Descriptiva |
| — | ¿La política usa lo que ve? Colas en cero y mensajes cortados (a3), en V2 y en la observación nueva; regulares en D, 2715, P1, P2, P3 y P6; aleatorias en P1-P6 [A4] | Cambio frente a la misma política sin perturbar | Descriptiva |

**Nota.** En D no hay giros a la izquierda en los semáforos, así que la marca de giro vale 0: D prueba la reacción y
2715 prueba el bloqueo [M `plan3/modelo/informe.md` §7].

### Etapa 3b. 400 episodios: estudio aparte, sin veredicto

- Se corre en P1-P6 con llegadas regulares y, [A4], también con aleatorias. No cambia ninguna etiqueta.
- La tasa de aprendizaje baja con `--episodios` [M `rl_ippo.py` l. 1074], por eso se usa horizonte 200 con piso 0.1.
  La corrida de 400 repite los episodios 1-181 de la de 200 [M `plan3/modelo/salidas/m4_identidad.txt`].
- **Se declara:** el brazo de 400 elige entre 40 checkpoints y el de 200 entre 20. Parte del efecto de "más episodios"
  es tener más candidatos. Para medirlo, se agrega sin costo "400 eligiendo entre 20" (ep. 20, 40, ..., 400).

| Id | Hipótesis | Prueba | Familia (Holm) |
|---|---|---|---|
| H9 | V2 con 400 episodios y piso < V2 con 200 sin piso | Superioridad; sentido 3 de 3 emparejadas | 6 (regulares) y 6 (aleatorias) |
| — | 200 con piso frente a 200 sin piso (efecto de la tasa) | Comparten 18 de sus 20 checkpoints, así que casi siempre dan lo mismo por construcción | Descriptiva |
| — | 400 eligiendo entre 20 checkpoints; convergencia con 400 | Cambios | Descriptiva |

### Etapa 4. Una política por red [A6]

| Id | Hipótesis | Prueba | Familia (Holm) |
|---|---|---|---|
| H10 | Una política por red no es peor que la V2 de cada nivel | No inferioridad por nivel frente a la V2 de la Etapa 1 de ese nivel (llegadas regulares). Pasa si da "no es peor" en al menos el 80 % de los niveles: corredor 4 de 5, red 6 de 7, malla 5 de 6. "No concluyente" no cuenta como "no es peor" | Por red: 5, 7 y 6 |

Si Fabian elige los corredores de 3-5 semáforos [A6], se agregan H13a (etiqueta de V2 con mensajes frente al fijo fino
en cada corredor; descriptiva) y H13b (la ventaja de los mensajes crece con los semáforos: pendiente del cambio con
frente a sin mensajes contra N = 2, 3, 4 y 5; pasa si la pendiente de las versiones evaluadas tiene IC95 entero bajo
cero y la pendiente de cada una de las 3 bases es negativa, en T1 y T2; familia 1).

### Contrastes que se informan siempre
- C0 frente al IPPO entregado (efecto de la selección nueva) y el cuadro 2×2.
- Cada referencia al lado, con su lectura obligada (§5).
- La mejor base por validación, al lado de cada etiqueta.
- Retraso por media hora en los corredores; mediana y episodios muy malos en P6 y P6e con llegadas aleatorias; mediana
  y semillas trabadas del fijo fino en P6 regular.
- Cambios de fase, espera para entrar y no insertados.

No se corren: H11 (política anclada al fijo, M6) y, si A6 no los elige, los corredores.

## 9. Corrección por pruebas múltiples

- Holm dentro de cada familia de §8, en cada tanda por separado. Una prueba pasa si pasa en T1 y en T2.
- Las etiquetas de las celdas, H3 y H5 no se corrigen (§7). H1 global usa intersección-unión.
- Las familias quedan fijadas aquí. Si una prueba no se puede correr, la familia conserva su tamaño y esa prueba cuenta
  como no pasada.

## 10. Cuántas semillas

**Llegadas regulares: 30 por tanda.** IC del cambio de ±0.2 a ±2.8 puntos en P1-P6 [M
`plan3/veredicto/salidas/t4_precision.txt`]. **H1 y H2: 120 por tanda**, porque con 30 la no inferioridad pasaría en
las dos tandas solo el 21 % (P6) o el 39 % (P4) de las veces si V2 y C0 fueran iguales; con 120, ≥ 93 % en los seis
casos [I `plan3/final/potencia/potencia_plan3_salida.txt`].

**Llegadas aleatorias: 100 por tanda [A3].**
- La diferencia pareada actuado − fijo varía 14 % (P1) y 10.6 % (P6) entre semillas: IC de ±3.9 y ±4.1 puntos con
  30, ±2.7-2.9 con 60 [M `plan3/veredicto/salidas/t6_poisson_precision.txt`] y ~±2.1-2.2 con 100 [I].
- Probabilidad de confirmar en las dos tandas un efecto real de −3 %: ~31 % con 60 y ~60 % con 100 [I].
- **Potencia de H5** (efecto igual en las 6 celdas; bases con sd 1.5 puntos; criterio de sentido de §7): 0.59 con −3 %,
  1.00 con −5 % y −8 % [I `potencia_plan3_salida.txt`].
- El número queda fijo y no depende de ningún resultado.

## 11. Qué se informa pase lo que pase

- **La tabla del anexo:** caso × tipo de llegadas, con la etiqueta de T1, la de T2 y la citable, el cambio con su IC en
  cada tanda, "se repite en k de n entrenamientos" y la etiqueta con la mejor base.
- **Todas las bases de todos los brazos:** validación elegida, episodio, si convergió, distancia a la mediana de la
  serie y si el mínimo se repite.
- **Todas las hipótesis de §8**, pasen o no, con su p ajustado y su lectura (no es peor, es peor o no concluyente).
- **Las referencias al lado** y sus lecturas obligadas.
- **C0, el cuadro 2×2 y el puente.**
- **La regla de promoción** (§12): las validaciones de promoción de cada variante y el modelo citado de cada celda.
- **La probabilidad de PENDIENTE por ruido** (§6).
- **Los entrenamientos caídos, relanzados o fallidos**, toda desviación y toda enmienda con los datos que estaban a la
  vista.
- **La predicción de §15**, para medir cuánto sorprendió el resultado.

**Lecturas obligadas** (se escriben así):

| Si pasa esto | Se escribe |
|---|---|
| El modelo da lo mismo que el ciclo mínimo | "Reproduce el ciclo mínimo", no "coordinación aprendida" |
| MEJORA frente al fijo, pero no frente al plan por franja | "La ventaja la logra también un plan por horario" |
| No le gana a la regla simple | No se dice que el modelo aprendió algo que la regla no hace |
| La versión evaluada mejora, pero no se repite entre entrenamientos | "La versión evaluada mejora; el método no se repite en k de n entrenamientos" |
| V2 mejora a C0 y C0 mejora al IPPO entregado | Parte de la ganancia viene de cómo se elige la versión |
| Gana el fijo fino y empata el de verdes de 5 en 5 | La diferencia está en verdes que IPPO, decidiendo cada 5 s, no puede dar |
| P6 con la entrada por defecto | El cambio relativo está diluido por la espera de inserción; ver P6e |
| El modelo citado no es V2 | Se nombra la variante y se da al lado la etiqueta de V2 |

## 12. Modelo citado: regla de promoción [A4]

- **Candidatos de cada celda:** V2 y las variantes prerregistradas entrenadas en esa celda con el mismo tipo de
  llegadas (observación nueva, limpiezas juntas, 400 episodios, reloj de 2 s y modelo completo, donde existan).
- **Cada candidato aporta su versión evaluada entre las bases 42, 2042 y 4042.** Se re-valida en las 16 semillas de
  promoción (15009-15024), que nunca se usaron para elegir checkpoints.
- **Gana el de menor retraso total medio, solo si le gana a V2 por al menos 1 %.** Si no, el modelo citado es V2 (con
  su versión evaluada de 5 bases).
- El resultado se guarda con su sha256 antes de `cierre.ok`. Usa solo validación: el examen sigue limpio.
- El modelo completo lleva: V2, observación nueva (75 m), las tres limpiezas, 400 episodios con piso de la tasa y, si
  se aprueba, el reloj de 2 s (DECISIONES B25).

## 13. Prueba final reservada

- **Semillas:** 11001-11030 (regulares) y 12001-12100 (aleatorias). No se simulan con el resto.
- **Para qué:** si después de ver T1 y T2 se quiere citar algo que este documento no fijó (por ejemplo, otra
  combinación de casos u otra referencia), se evalúa **una sola vez** aquí.
- **Nunca** se usa para juzgar una hipótesis o una etiqueta prerregistrada; por ejemplo, para "rescatar" una que salió
  MEJORA en T1 y EMPATA en T2.
- Lo que se cite de ella dice "elegido después de ver T1 y T2; una tanda".
- **Cómo:** una sola enmienda con la lista exacta y su sha256; Fabian crea `plan3/listo/holdout.ok`; el script guarda un
  candado con ese hash y no corre una segunda vez.

## 14. A ciegas, desviaciones, enmiendas y caídas

**A ciegas.**
- Los CSV de T1, T2, la extensión de H1 y la prueba final se escriben en `plan3/ciego/`, ignorada por git, hasta
  `cierre.ok`.
- Los logs de esos trabajos dicen solo semilla y duración. Un fallo se diagnostica con el error, nunca con métricas.
- Cada mañana se sube solo `plan3/cola/manifiesto_ciego.json` (ruta, sha256, filas y semillas de cada CSV). Los CSV
  entran en el commit de cierre y deben coincidir con esos sha256.
- Se declara el límite: nada demuestra que nadie miró. Sí se demuestra que las reglas son anteriores a los datos y que
  los archivos no cambiaron después de producirse.

**Enmiendas.**
- Llevan fecha y hora, un commit de Fabian, push, tag y correo al asesor.
- Después de la parte A, una enmienda solo puede: corregir un error de código, reemplazar un trabajo que no se puede
  correr o fijar lo ya anunciado (el β de la media móvil de la política por red, con un piloto de humo; los valores de
  la mezcla, en la parte B).
- Cada una dice qué datos estaban a la vista: referencias, validación o entrenamiento.
- **Desde la primera noche con evaluaciones decisivas (día 14), solo se corrigen errores de código.** Si el error tocó
  un análisis, se muestran las dos cifras.

**Caídas y errores** (DECISIONES B22).
- Una caída de infraestructura se relanza con el mismo id y la misma semilla, desde el último estado guardado; los
  primeros episodios deben repetir los del intento anterior (el entrenamiento es determinista [M]).
- Un error de código: se corrige y los trabajos afectados se corren con ids nuevos (`_r2`); las salidas viejas se
  conservan.
- Una falla del método en dos intentos (pérdida NaN, política que no se publica): la base cuenta como fallida y fuera
  del sentido; la versión evaluada sale de las bases que quedan (§6).

**Antes y después de cada noche:** `protecciones.py`, con `git status` de `plan2/` y `TESIS/` limpio (con los
ignorados), el manifiesto de checkpoints intacto, las versiones de Python, torch y SUMO, y el sha256 de este documento
igual al de origin.

**Declarado:** el 05.11 se usaron las semillas 1001-1003 una vez, para comprobar que el actuado sin TraCI reproduce el
CSV entregado [M `plan3/referencias/informe.md`, "Límites y desvíos"]. Fue una reproducción de lo entregado, no una
elección.

## 15. Predicción honesta (para medir la sorpresa; no cambia ningún criterio)

**Llegadas regulares.**
- Frente al fijo entregado, V2 en P1 entre −5 y −7 % y en P2 entre −9 y −11 %: el rango de las dos tandas del
  diagnóstico [M `plan2/diag_corredor/pruebas.txt`, vía críticas].
- Frente al fijo fino, menos: el fino gana 1.3 % en P1 y la franja 2.2 % [M].
- **P6:** frente al fijo fino, probablemente EMPATA: el 12/10 le gana −3.5 % al 15/10, y V2 le ganaba −3.1 % en otras
  semillas [I]. Con el reloj de 2 s, que puede dar verdes de 12 y 14 s, podría volver a MEJORA [I].
- **P3, P5 y la malla:** el ciclo mínimo.
- **Número único frente al fino:** menor que el −2.8 a −3.9 % proyectado frente al fijo entregado [I].

**Llegadas aleatorias** (medido el 05.11 con semillas de prueba, IPPO entregado entrenado con llegadas regulares y fijo
sin re-ajustar; entrada corregida) [M `plan3/critica_resultados/RESUMEN.txt` §2]:

| Caso | IPPO entregado frente al fijo instalado | Frente al actuado |
|---|---|---|
| P1 | −2.1 % [−4.0, +0.2] | +8.0 % [+5.0, +11.6]; pierde en 16 de 16 semillas |
| P2 | −12.0 % [−14.7, −9.2] | −8.3 % [−11.0, −5.5] |
| P6 | −41.1 % [−56.3, −19.2] en media; −16.7 % en mediana | −25.2 % [−30.3, −20.3]; gana en 16 de 16 |

- El actuado le gana −14 % al fijo re-ajustado en P1 [M `prueba_barrido_p1.txt`].
- **Predicción por caso** [I]: P2 y P6 son candidatos a FUNCIONA si el fijo re-ajustado no cierra la brecha. P1, con
  el reloj de 5 s, queda en MEJORA o menos por el veto del actuado; con el reloj de 2 s podría pasar a FUNCIONA.
- Las cifras del área de demanda del 05.11 (−7 % en P1 y −6 % en P6) eran con la entrada por defecto: no aplican.

**Observación nueva:** que reduzca la pérdida en 2715; que no le gane al fijo.

**400 episodios:** del orden de 1-3 % en el corredor, porque con V2 la validación sigue bajando al final (−2.5 % en el
último tercio [M RESUMEN §4]) [I].

**Reloj de 2 s:** con llegadas aleatorias, una regla que reacciona pierde +12.2 % decidiendo cada 5 s frente a cada
2 s en P1 y +20.3 % en P6 [M RESUMEN §1, la regla como sustituto de IPPO]. Para IPPO se espera menos, porque puede
anticipar [I]; con llegadas regulares, poco [I].

**Modelo completo:** sin predicción medida; riesgo de romper la coordinación (+22.3 % con el mensaje de salida en P6
sin V2 [M]).

**Política por red:** cerca del ciclo mínimo en la red y la malla.

## 16. Qué no cambia de lo entregado

- **Los veredictos entregados:** el del 25.09 (`veredicto_congelado_0355.csv`), la robustez v2.1, los niveles `dem_` de
  la entrega 3 y el diagnóstico del corredor (Anexo G), con la V2 de la Sección 5.5.1.
- **No se re-eligen** bases, checkpoints ni ensambles de lo entregado. C0 es un control y nunca se cita en su lugar.
- **Archivos:** la rama `plan3` no cambia nada en `plan2/` ni en `TESIS/` (`git diff main...HEAD -- plan2 TESIS`
  vacío). `veredicto.py` no se edita y nunca se corre sin opciones; tampoco `consolidar.py`, `sintesis_plan.py` ni la
  cola de `plan2/`.
- **El código entregado** queda marcado con el tag `entregado-2026-10-25` (81378fb). Lo que se modifica en el lugar
  lleva sus opciones apagadas por defecto y pasa la prueba de no regresión.
- **Los checkpoints entregados** se leen solo de copias, y antes se respaldan.
- **El texto de la tesis:** resumen, abstract, objetivos, Cap. I y conclusiones cambian solo con la confirmación de
  Fabian, al final [A8].

## 17. Plantilla de redacción (resumen y conclusiones)

**Reglas para todas las preguntas.**
- La etiqueta entregada y la nueva se citan juntas, cada una con su referencia [A8].
- Cada cifra lleva sus dos tandas. El puente (1001-1030) y P6e nunca van al resumen.
- Lo elegido después de ver T1 y T2 solo se cita desde la prueba final, con su rótulo (§13).

| Pregunta | Resultado | Frase del resumen y de las conclusiones |
|---|---|---|
| 1. Regulares | Alguna celda sube su etiqueta citable | "Con llegadas regulares, IPPO con mensajes corregido mejora en [casos] frente a un plan fijo ajustado al segundo: [cambio] en la tanda 1 y [cambio] en la tanda 2." |
| | Ninguna sube | "Con llegadas regulares, la corrección no cambia lo entregado frente a un plan fijo ajustado al segundo; ese plan usa verdes que IPPO, al decidir cada 5 s, no puede dar." |
| | H1 no concluyente | "En [casos] no se puede afirmar ni descartar una pérdida mayor que 2 % frente a lo entregado." |
| | PENDIENTE | "En [caso] el entrenamiento no se estabilizó; la etiqueta provisional es [X]." |
| 2. Aleatorias | H5 pasa | "Con llegadas al azar, IPPO con mensajes entrenado con ese desorden le gana a un plan fijo re-ajustado con el mismo desorden en [k] de 6 casos." |
| | H5 no pasa | "Con llegadas al azar, IPPO con mensajes no le gana de forma repetida al plan fijo re-ajustado; [lo que sí se repitió]." |
| | Un control sin aprendizaje iguala o gana | "Un control que reacciona sin aprender ([cuál]) iguala o supera a IPPO en [casos]." |
| | Tandas contradictorias | "En [casos] las dos tandas no coinciden; no se concluye." |
| 3. Observación | H8a pasa | "Ver el giro que bloquea el carril reduce la pérdida en [casos]: [cambio por tanda]." |
| | No pasa | "Ver el giro que bloquea el carril no cambia el resultado en [casos]." |
| | H8c no concluyente | "No se puede descartar que la observación nueva empeore en [casos]." |
| 4. Episodios | H9 pasa | "Entrenar 400 episodios mejora la versión evaluada en [casos]; no cambia ninguna etiqueta." |
| | No pasa | "Entrenar 400 episodios no mejora la versión evaluada." |
| 5. Reloj | H14 pasa | "Decidir cada 2 s en vez de cada 5 s mejora a IPPO con mensajes en [casos]." |
| | No pasa | "Decidir cada 2 s no cambia el resultado: el límite no es el reloj." |
| 6. Modelo citado | Se promueve una variante | "El mejor modelo prerregistrado de [caso], elegido sin mirar el examen, es [variante]: [etiqueta]; IPPO con mensajes corregido da [etiqueta]." |
| | Se queda V2 | "Ninguna variante superó a la corrección en la validación; se cita IPPO con mensajes corregido." |
| 7. Política por red | H10 pasa | "Una sola política por red sostiene [k de n] niveles sin perder más de 2 % frente a la entrenada en cada nivel." |
| | No pasa o no concluyente | "Una sola política por red no sostiene todos los niveles: pierde en [niveles] (o no se puede descartar que pierda)." |
| Número único | Siempre | "Frente al plan fijo ajustado al segundo, [cambio] en la tanda 1 y [cambio] en la tanda 2 (frente al plan fijo entregado: [cambio] y [cambio])." |

## 18. Decisiones tomadas

Fabian las tomó el 05.11.2026, todas con la opción recomendada en `doc/DECISIONES.md`.

| Decisión | Opción tomada | Dónde se usa |
|---|---|---|
| A1 Referencias | Decide el fijo afinado al segundo (barrido de 1 s, regla de ganadores frágiles, ajuste con llegadas aleatorias en dos etapas); el actuado ajustado veta FUNCIONA; al lado, franja, regla simple, ciclo mínimo, fijo de verdes de 5 en 5 y fijo entregado; Max-Pressure descriptivo | §3, §4 y §5 |
| A2 Entrada y métrica de P6 | Entrada corregida (`departLane="best"`) solo en lo nuevo, más la celda P6e; principal, el retraso total | §4 y §5 |
| A3 Bases, validación, versión evaluada y semillas | 5 bases en el modelo principal y 3 en lo demás; 16 semillas de validación; decide la base mediana y la mejor va al lado; 100 semillas por tanda con llegadas aleatorias; H1 y H2 con 120; prueba final reservada | §2, §3, §6 y §10 |
| A4 Mejoras del modelo | Reloj de 2 s, 400 episodios también con llegadas aleatorias, modelo completo y regla de promoción por celda | §0, §1, §8 (H9 aleatoria, H14, H15, a3) y §12 |
| A5 Reglas para afirmar | El paquete completo, con el criterio por signo | §0, §7, §8, §9, §13 y §14 |
| A6 Etapa 4 y calendario | Solo la política por red; la factibilidad no se corre aparte; la cola corre de noche con hora de corte | §8 (Etapa 4) |
| A7 Desorden de Lima | Perfil de 10 min con el mismo total, mezcla JICA 2013 sin camiones en vehículos equivalentes y arranque lento de 0.5 s solo al evaluar, en P1 y P3, como sensibilidad | §8 (perfil, mezcla, arranque lento) |
| A8 Tesis y qué se cita | Sección corta en el Cap. V sin tablas nuevas, más un anexo; etiquetas entregada y nueva juntas; número único frente al fijo fino con P6 y el entregado al lado; corregir en P4 la frase del ciclo mínimo con nota y confirmación | §7 (número único), §16 y §17 |
