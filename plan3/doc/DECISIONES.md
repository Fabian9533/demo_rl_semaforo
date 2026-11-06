# Decisiones antes de implementar el plan 3

05.11.2026. Versión final, después de tres críticas (método, factibilidad e impacto). Nada está implementado.

## Respuesta corta

- **Fabian decide 8 cosas (A1-A8).** Las 25 técnicas (B1-B25) se toman por defecto como se indica.
- **Todas las decisiones A se toman el día 0.** El prerregistro lleva todas las reglas en su parte A, y esa parte se
  sube antes de la primera noche (día 4).
- **Costo del paquete recomendado:** ~1900 h-proceso en el régimen conservador, unas 160 h de reloj en 17 noches
  (~1500 h-p y 15 noches en el régimen central).
- **Calendario real: unos 26-27 días de trabajo.** El borrador decía 18-19, pero la suma de sus propias tareas daba
  más. El cuello sigue siendo el código: unos 18-19 días.
- **Qué cambió frente al borrador:**
  - el plan ahora también busca **mejorar el modelo**, no solo explicar sus resultados (A4);
  - todas las reglas estadísticas se fijan **antes de ver ninguna referencia** (A5);
  - "a ciegas" se puede comprobar: los resultados decisivos no se versionan hasta el cierre, solo su sha256 (A5);
  - la Etapa 4 vuelve a ser **una sola de las dos**, como en el programa aprobado (A6);
  - el calendario se rehízo con la suma real de las tareas y el régimen conservador (A6).

**Cómo leer.**
- **Grupo A (decide Fabian).** Cada decisión se entiende sola: qué hay que decidir, lo que ya se sabe, las opciones
  con su costo y lo que se podrá afirmar, la recomendación y para cuándo.
- **Grupo B (técnicas).** Se aplica la opción por defecto, salvo que Fabian diga otra cosa.

**Costos.**
- Salen de `costos_plan3.py`, en esta carpeta (salida en `costos_plan3_salida.txt`). Usa duraciones medidas en
  `plan2/cola/estado.json` y en las pruebas del 05.11, y simula la cola noche por noche.
- **Régimen de base: conservador + 10 %.** Es la velocidad de la noche del plan v2 (máquina cargada), más un 10 % por
  empaquetado. El central se da al lado. Así lo pidió la crítica de factibilidad: la cola corre 12 procesos en
  8 núcleos, y el central se midió con 7.2 a la vez [M `critica_codigo/salidas/concurrencia_exploratorio.txt`].
- 12 h-proceso ≈ 1 h de reloj [M: noche dem2, 11.95]. Una noche son 10 h y ~120 h-p.

**Marcas.** [M] medido, con su archivo; [I] inferido; [S] supuesto; [L] literatura. Las rutas `plan3/<área>/...`,
`critica_codigo/...` y `plan3_critico_prerregistro/...` están dentro de
`C:/Users/GAMER/Documents/demo_rl_semaforo/analisis_mejora_2026-11-04/`.

## Resumen del grupo A

| # | Qué se decide | Recomendación | Costo (conservador; central) |
|---|---|---|---|
| A1 | Contra qué se compara | Decide el fijo de un plan con barrido de 1 s; el actuado ajustado veta FUNCIONA; regla para ganadores frágiles; con llegadas aleatorias, ajuste con más semillas | 161 h-p de barridos, ~13.5 h (1.5 noches) |
| A2 | Cómo entran los autos y la métrica de P6 | Entrada corregida en todo lo nuevo; P6e como celda propia | +57 h-p (~5 h); +39 central |
| A3 | Cuántos entrenamientos y cuántas semillas | 5 bases en el modelo principal; 16 semillas de validación; 30 por tanda (regulares) y 100 (aleatorias); H1 y H2 con 120 | ~el paquete; +21 h-p por H1 con 120 |
| A4 | Cómo puede mejorar el modelo | Reloj de 2 s, mejoras también con llegadas aleatorias, modelo completo y regla de promoción | +559 h-p (~47 h) y ~1-2 días de calendario |
| A5 | Reglas para afirmar algo | El paquete: todas las reglas antes de la primera noche, a ciegas comprobable, sentido entre entrenamientos por signo | 0 h |
| A6 | Alcance de la Etapa 4 y calendario | Solo la política por red; cola de noche con hora de corte | ~26-27 días en total |
| A7 | Desorden de Lima | Perfil de 10 min y mezcla JICA sin camiones, como sensibilidad | ~72 h-p (~6 h) |
| A8 | Cómo entra en la tesis y qué se cita | Sección corta en el Cap. V sin tablas nuevas, más un anexo; las dos etiquetas juntas | 0 h; ~4 días de escritura |

**Paquete recomendado:** ~1901 h-p y 17 noches (conservador), o ~1506 h-p y 15 noches (central). Primera noche: día 4.
Última: día 20 (18 en el central). El código termina el día 19. Total: ~26-27 días.

---

## A1. Contra qué se compara (las referencias)

**Qué hay que decidir.** La etiqueta de cada caso (FUNCIONA, MEJORA, EMPATA, FALLA) se calcula frente a una referencia.
Hay que fijar qué referencia decide, cuál veta FUNCIONA y cuáles se muestran al lado. También cómo se ajustan.

**Lo que ya se sabe** (pruebas del 05.11, solo con semillas de ajuste):
- **El fijo de P6 estaba en un salto de la rejilla de 5 s.** Con pasos de 1 s gana el 12/10: frente al 15/10 baja
  −3.5 % el retraso total y −7.4 % el timeLoss [M `plan3/referencias/salidas/top10_p6_2001-2010.csv`].
- **Pero el 12/10 es frágil.** Su media en 2001-2010 es 79.53, con sd 4.76 y una semilla que casi se traba (93.05). El
  14/10 da 80.29 con sd 0.38 y gana en 10 de 10 [M, recalculado hoy del mismo CSV]. Hoy no hay regla escrita para
  elegir entre los dos.
- Eso es del tamaño de la ganancia de V2 en P6 (−3.1 % y −6.7 %, en otras semillas) [I: mezcla tandas].
- **En P1 el ajuste fino mejora el fijo solo 1.3 %.** Un plan por media hora (franja) le gana 2.2 % al fijo de un plan
  [M `plan3/referencias/salidas/franja_P1.log`].
- **IPPO decide cada 5 s**, así que sus verdes duran 10, 15, 20... s. Los verdes de 12 y 14 s del fijo fino están fuera
  de su alcance [M `rl_ippo.py` l. 671-678].
- Ajustar el actuado mueve poco con llegadas regulares. En P6 baja −13.8 %, pero sigue +18 % sobre el fijo [M
  `plan3/referencias/salidas/actuado_piloto_2001-2003.csv`].
- **Con llegadas aleatorias, 3 semillas no ordenan fijos cercanos.** La diferencia pareada entre dos fijos cercanos
  varía 4-13 % entre semillas [M `plan3/demanda/informe.md` 2.i]. Con 3 semillas, el error de esa diferencia (2.3-7.5 %)
  es mayor que el umbral de "a ≤ 2 % del mejor" que decide qué zonas se afinan.

**Opciones.**

| Opción | Qué se podrá afirmar | Costo |
|---|---|---|
| **(a) Decide el fijo de un plan con barrido de 1 s**, con la misma regla en todos los casos y niveles; con llegadas aleatorias se re-ajusta con ellas. **Veta FUNCIONA el actuado ajustado.** Al lado, con lectura obligada: franja, regla simple, ciclo mínimo y **un fijo con verdes de 5 en 5 y desfases finos** (lo que el reloj de IPPO puede imitar). El fijo entregado va al lado solo para comparar con lo entregado. Max-Pressure solo se describe | La vara de un plan más exigente. En P6 el MEJORA de V2 probablemente desaparece (H3 improbable). En P1 el FUNCIONA puede quedar en el borde. El fijo de verdes de 5 en 5 separa el límite del reloj de lo que aprende el modelo | 161 h-p de barridos, ~13.5 h (las dos sub-opciones de abajo incluidas) |
| (b) Decide el mejor entre el fijo de un plan y la franja | Más exigente, pero mezcla dos clases de control. P1 podría bajar a MEJORA | igual |
| (c) Decide el mejor control sin aprendizaje (fijo, franja, actuado ajustado o regla) | El más exigente. Con llegadas aleatorias decidiría a veces el actuado (en P1 le gana −14 % al fijo re-ajustado [M `plan3/demanda/salidas/prueba_barrido_p1.txt`]) | igual |
| (d) Como lo entregado: decide el fijo de 5 s y el fino va al lado | Se compara directo con lo entregado, pero la vara se puede mejorar 3.5 % en P6 y un jurado lo puede objetar | −30 h-p (~2.5 h) [I] |

Dos sub-opciones dentro de (a):

| Sub-opción | Recomendada | Alternativa |
|---|---|---|
| **Ganador frágil.** Si los dos primeros quedan a ≤ 2 % en la media, o el ganador tiene una semilla con retraso total mayor que 1.10 veces su mediana, se desempata entre los 3 primeros con 2001-2030 y gana la menor media. En P6 regular se informa además, como secundaria, la mediana del fijo fino y sus semillas trabadas en el examen | Sí. En P6 se activa (0.96 % de diferencia). ~3 h-p | Sin regla: alguien tendría que elegir a mano entre 12/10 y 14/10 conociendo ya la V2 de P6. Eso favorecería a un lado |
| **Llegadas aleatorias: más semillas al ajustar.** Etapas gruesa y fina con 2001-2010; pasan a la fina los mínimos a ≤ 2 errores estándar del mejor (tope 3); 10 finalistas de cada referencia (fijo, franja, actuado y regla) con 2001-2030 | Sí. +59 h-p (~5 h), en las noches de las referencias | Con 2001-2003 (borrador): el ruido elegiría qué zonas se afinan, y una referencia mal ajustada favorece al modelo justo donde se espera margen (H0, H5, H6) |

**Recomendación: (a), con las dos sub-opciones.**

**Por qué.**
- Es lo que instalaría un ingeniero con un plan por hora, ajustado con el mismo cuidado que el modelo.
- El fijo de verdes de 5 en 5 deja limpio cuánto pierde IPPO por decidir cada 5 s (crítica de impacto 7).
- Las dos sub-opciones cierran caminos para elegir la referencia con los resultados a la vista.

**A más tardar:** día 0 (va en la parte A del prerregistro).

---

## A2. Cómo entran los autos a la red, y la métrica de P6

**Qué hay que decidir.** Por defecto, SUMO hace entrar a todos los autos por el primer carril y a velocidad 0. En P6
eso crea una cola artificial para entrar. La métrica principal (retraso total) incluye esa espera.

**Lo que ya se sabe.**
- **En P6, el 55 % del retraso total del fijo es esa cola: 45.7 de 82.6 s/veh.** Con `departLane="best"` baja a
  0.3 s/veh y el timeLoss no cambia (36.91 → 36.82) [M `plan3/referencias/salidas/insercion_P6_P2_P4_P6cfg.csv`].
- En P1-P4 el resultado es idéntico dígito a dígito, y en P5 cambia 0.2 s/veh [M]. La espera de P2 (~233 s/veh) es
  una cola real de los semáforos [M].
- Con llegadas regulares, la espera de P6 es casi igual en todos los controles (45.5-45.7 s/veh): no cambia la
  etiqueta, pero divide por dos el cambio relativo, y eso pesa en el umbral de −5 % de FUNCIONA [M; I].
- Con llegadas aleatorias ya no es igual entre controles: al corregir la entrada, el actuado pasa de perder +16 % a
  ganar −6 % frente al fijo de P6 [M `plan3/demanda/salidas/prueba_insercion.txt`].

**Opciones.**

| Opción | Qué se podrá afirmar | Costo |
|---|---|---|
| (a) La entrada de siempre en todo; en P6, timeLoss co-principal | Comparable con lo entregado, pero P6 con llegadas aleatorias queda contaminado y tiene dos etiquetas | 0 |
| **(b) Entrada corregida en todo lo nuevo** (llegadas aleatorias, perfil, mezcla y corredores nuevos si se corren); lo que repite casos entregados con llegadas regulares queda igual, y también la política por red, que se compara con la V2 de cada nivel; **P6e** (P6 con entrada corregida y llegadas regulares) como celda propia | Quita el artefacto donde distorsiona y lo entregado sigue comparable. P6e permite comparar llegadas regulares y aleatorias con la misma entrada (H6) | +57 h-p (~5 h); +39 en el central |
| (c) Entrada corregida en todo, también con llegadas regulares | Más simple, pero P6 deja de compararse con lo entregado y C0 de P6 corre en otro entorno | ~+15 h-p [I] |

**Recomendación: (b).** La métrica principal sigue siendo el retraso total. El timeLoss y la espera para entrar se
informan siempre aparte.

**Por qué.** Quita el artefacto donde cambia las conclusiones sin romper la comparación con lo entregado, y no agrega
una segunda etiqueta.

**A más tardar:** día 0.

---

## A3. Cuántos entrenamientos y cuántas semillas

**Qué hay que decidir.** Cinco números que fijan la precisión y, con ella, qué se podrá afirmar:
1. bases (entrenamientos) por brazo;
2. semillas de validación para elegir la versión;
3. qué base es la versión evaluada;
4. semillas por tanda de examen;
5. si H1 y H2 llevan más semillas.

**Lo que ya se sabe.**
- En P6, las 3 bases de IPPO entregado quedan +1.1, +6.0 y +4.5 % sobre el fijo en retraso total (+2.2, +13.0 y
  +9.6 % en timeLoss) [M `plan3/veredicto/salidas/t4_precision.txt`]. Las bases difieren más que el efecto que se busca.
- **Ruido al elegir la versión.** Una política de calidad constante sale "no convergió" solo por ruido:
  - llegadas regulares: 0-1 % en P1-P5; en P6, 25 % con 8 semillas y ~10 % con 16 [I Monte Carlo,
    `plan3/veredicto/salidas/t5b.txt`];
  - llegadas aleatorias: 0.0 % en P1 y 2.2 % en P6 con 16 semillas; 0.9 % y 10.4 % con 8 [M
    `plan3/critica_resultados/RESUMEN.txt` §3, con IPPO entregado re-validado como sustituto].
- Validar no cambia el entrenamiento: los pesos son idénticos con 2 o con 8 semillas de validación [M
  `plan3/modelo/salidas/v2val8_vs_val2.txt`].
- Las bases de V2 y de C0 con la misma semilla comparten pesos iniciales y llegadas de cada episodio [M `rl_ippo.py`:
  `sembrar` antes de crear la política; episodio k con semilla base + k]. Se pueden comparar emparejadas.
- **Precisión del examen.** Con llegadas regulares, 30 semillas dan ±0.2 a ±2.8 puntos en P1-P6 [M t4]. Con
  aleatorias, ±3.9 (P1) y ±4.1 (P6) con 30 semillas, ±2.7-2.9 con 60 y ~±2.1-2.2 con 100 [M/I
  `t6_poisson_precision.txt`].
- **H1 tiene poca potencia con 30 semillas.** Si V2 y C0 fueran iguales, la no inferioridad (+2 %) pasaría en las dos
  tandas solo el 39 % de las veces en P4 y el 21 % en P6 [I `plan3/final/potencia/potencia_plan3_salida.txt`, con los
  semianchos medidos por la crítica de método: 1.7-2.5 puntos]. Con 120 semillas por tanda, ≥ 93 % en los seis casos.

**Opciones.**

| Tema | Opción | Qué se podrá afirmar | Costo |
|---|---|---|---|
| Bases | **(a) 5 en el modelo principal** (V2 con mensajes, regular y aleatoria, en P1-P6 y P6e) y 3 en lo demás | Una afirmación del método se apoya en 5 entrenamientos | incluido |
| | (b) 3 en todo | Como lo entregado; en P6 se filtra poco | −101 h-p (−8 h) |
| | (c) 5 en todo | Lo más sólido | +~330 h-p (+28 h), +3 noches [I, cifra del borrador] |
| Validación | **(a) 16 semillas en todo** (999…9999 y 15001-15008) | Una sola regla; PENDIENTE por ruido ≤ 10 % en P6 | incluido |
| | (b) 8 en todo | P6 con 25 % de PENDIENTE por ruido | −349 h-p (−29 h) |
| Versión evaluada | **(a) La base mediana decide la etiqueta (como el Cap. III); la mejor base por validación se informa al lado, prerregistrada** | Se compara igual que lo entregado y se sabe cuánto cambiaría elegir la mejor | 0 h (todas las bases se evalúan igual) |
| | (b) Decide la mejor base por validación | Simétrico con las referencias, que son la mejor de su búsqueda. Mejoraría las etiquetas donde las bases varían, como P6 [I], pero cambia la convención del Cap. III | 0 h |
| Examen, regulares | **T1 = 8001-8030, T2 = 13001-13030; 1001-1030 solo como puente** | Dos tandas limpias en todas las celdas | incluido |
| Examen, aleatorias | **(a) 100 semillas por tanda** (7001-7100 y 10001-10100) | Un efecto real de −3 % se confirma en las dos tandas ~60 % de las veces; uno de −5 %, ~99 % | incluido |
| | (b) 60 por tanda | −3 %: ~31 %; −5 %: ~88 % | −116 h-p (−10 h) |
| H1 y H2 | **(a) 120 semillas por tanda** (8001-8120 y 13001-13120) solo para V2, C0 e IPPO entregado en P1-P6 y la malla con 6525 veh/h | H1 deja de fallar por falta de precisión | +21 h-p (~2 h) |
| | (b) 30, como el resto | Un "H1 no pasa" no distinguiría "V2 es peor" de "faltan semillas" | 0 |
| Prueba final | **Reservada:** 11001-11030 y 12001-12100, una sola vez y solo para lo elegido después de ver T1 y T2 | Protege contra elegir a posteriori | ~22 h-p, solo si se usa |

**Recomendación: todas las marcadas en negrita.**

**Por qué.**
- P6 necesita 5 bases y 16 semillas de validación; lo pide `recomendaciones.tex` (l. 88-92).
- 120 semillas para H1 cuestan 2 h y la vuelven informativa.
- Informar la mejor base al lado no cuesta nada y responde la pregunta "¿y si se elige la mejor?" sin cambiar la
  convención.
- Todas las semillas nuevas están libres: 0 usos en CSV o JSON de los dos repositorios, los datos fuera del repositorio
  y las carpetas de análisis [M `plan3/final/semillas/t3_semillas_plan3.txt`].

**A más tardar:** día 0.

---

## A4. Cómo puede mejorar el modelo

**Qué hay que decidir.** El borrador estaba armado para explicar los resultados, no para mejorarlos. El único modelo
citable era V2 con 200 episodios, y las mejoras de entrenamiento se probaban solo con llegadas regulares, donde el techo
ya es conocido. Como todo corre a ciegas y sin puertas, **lo que no se prerregistre ahora no existirá al final.** Hay
cuatro piezas para decidir.

**Lo que ya se sabe.**
- **Reloj de decisión.** Con llegadas aleatorias, una regla reactiva que decide cada 5 s pierde frente a la misma regla
  cada 1 s: +13.3 % [+8.9, +18.2] en P1 y +23.0 % [+20.3, +26.3] en P6. Decidir cada 2 s cuesta solo +1.0 % y +2.3 %
  (no significativo). Con 5 s la regla pierde con el actuado (+8.9 % en P1); con 1 s le gana (−3.9 %) [M
  `plan3/critica_resultados/RESUMEN.txt` §1, semillas de prueba]. En P2 (saturado) el reloj pesa poco (+4.1 %, n.s.).
- **IPPO entregado con llegadas aleatorias** (sin reentrenar, entrada corregida) le gana al actuado en P2 (−8.3 %) y en
  P6 (−25.2 %), pero pierde en P1 (+8.0 %, 0 de 16 semillas) [M RESUMEN §2]. En P1, el veto del actuado dejaría la
  etiqueta en MEJORA o menos [I].
- El programa aprobado decía "no cambiar la acción (decidir cada 1-2 s)" por falta de evidencia. Esta evidencia es
  nueva: es con llegadas aleatorias.
- **Más episodios.** Con V2, la validación sigue bajando al final: el mínimo del último tercio queda −2.49 % bajo el de
  los episodios ≤ 130 (18 bases del corredor; 11 bajan más de 1 %). Con IPPO entregado: +0.46 % (54 bases) [M RESUMEN §4].
  El Cap. III (l. 1492-1495) solo prohíbe alargar algunas celdas.
- **Observación nueva y limpiezas:** sin efecto medido todavía; un antecedente empeoró +22.3 % (mensaje de salida en P6
  sin V2) [M exploratorio].
- **El programa aprobado** decía, en la Etapa 3: "si la ablación cumple su regla, esa variante reemplaza a V2". Sin
  puertas, el equivalente es una regla de promoción escrita antes.

**Opciones.**

| Pieza | Qué es | Qué se podrá afirmar | Costo (conservador; central) |
|---|---|---|---|
| **(i) Reloj de 2 s** | Variante prerregistrada, como V2: decide cada 2 s una vez cumplido el verde mínimo. En D, P1, P2 y P6 con llegadas regulares y en P1, P2 y P6 con aleatorias; 3 bases | Si decidir más seguido mejora a IPPO con mensajes, con su propia hipótesis. Si no se corre, se declara el límite del reloj | +166 h-p (+14 h); +117 central. 0.75 día de código |
| **(ii) Mejoras con llegadas aleatorias** | 400 episodios (reanudando desde el 180) en P1-P6 y la sensibilidad a3 (¿la política usa lo que ve?), también con llegadas aleatorias | Si más episodios ayudan donde sí hay margen | +121 h-p (+10 h); +98 central. 0 días |
| **(iii) Modelo completo** | V2 + observación nueva + limpiezas de PPO + 400 episodios con piso de la tasa + reloj de 2 s (si se aprueba (i)). En P1, P2, P4 y P6 regulares y P1-P6 aleatorias (P3 y P5 regulares ya están en el ciclo mínimo); 3 bases | Si las mejoras juntas mejoran a V2. Cada pieza sigue con su prueba por separado | +338 h-p (+28 h); +250 central. ~0 días (combina opciones), pero necesita todas. Con 200 episodios: −148 h-p |
| **(iv) Regla de promoción** | En cada celda se cita el modelo prerregistrado con mejor validación en 16 semillas nuevas (15009-15024, nunca usadas para elegir checkpoints), si le gana a V2 por al menos 1 %. Si no, se cita V2 | La etiqueta citable puede ser la de un modelo mejor que V2, elegido sin mirar el examen. La de V2 se informa siempre al lado | +5 h-p; 0.25 día |
| | Alternativa a (iv): una sola variante para todas las celdas de un tipo de llegadas | Un solo método; mejora menos donde las celdas difieren | igual |
| | Sin (iv) | V2 sigue siendo el único modelo citable, aunque otra variante sea mejor | 0 |

**Lo que no se agrega, y por qué.**
- Brazos aparte de limpiezas con llegadas aleatorias: van dentro del modelo completo. La entropía no entra en el modelo completo (B25 y prerregistro §12); su brazo corre solo en D y P1 con llegadas regulares (nota del 05.11).
- Lote de varios episodios por actualización de PPO: sin medición propia, solo literatura [L Yu et al. 2022]. Se
  declara como trabajo futuro.
- Quitar P3 y P5 del 400 regular para ahorrar: no hace falta (el cuello es el código) y reabriría la crítica de
  alargar solo algunas celdas.

**Recomendación: las cuatro piezas, con la regla de promoción por celda.** Total: +559 h-p en el conservador (~47 h de
reloj; +416 en el central) y ~1-2 días más de calendario (~26-27 días en vez de ~25).

**Por qué.**
- Fabian pidió que los resultados mejoren. Sin (iii) y (iv), aunque cada pieza ayude, la etiqueta citable seguiría
  siendo la de V2 con 200 episodios.
- El reloj de 2 s ataca la causa más probable de que P1 con desorden no llegue a FUNCIONA (medida con una regla como
  sustituto de IPPO), y en P6 pone al alcance los verdes de 12-14 s del fijo fino.
- Todo se fija antes de ver datos, y la promoción usa solo semillas de validación: el examen sigue limpio.
- Cuesta ~1-2 días de calendario porque casi todo el cómputo extra cabe en noches que el código igual tiene que esperar.

**A más tardar:** día 0. El código va en los días 6-8.

---

## A5. Reglas para afirmar algo

**Qué hay que decidir.** Con qué reglas una cifra o una etiqueta del bloque nuevo se puede citar. Es un paquete.

**Lo que ya se sabe.**
- **Prerregistro en dos partes (borrador).** La parte B fijaba hipótesis, márgenes y familias el día 5, con todas las
  referencias ya vistas. Como el fijo varía poco entre semillas (CV 0.5-3 %, salvo P4 con 10 % [M t4]), su desempeño en
  las semillas de ajuste predice el del examen. Escribir las hipótesis después permitía elegirlas sabiendo cuáles pasan.
- **"A ciegas" no se podía comprobar.** El borrador versionaba cada mañana los CSV decisivos, y `evaluar.py` imprime
  en el log el retraso de cada semilla [M `evaluar.py` l. 307-309].
- **Potencia de H5** (al menos 3 de 6 casos con llegadas aleatorias), con 100 semillas, si el efecto es igual en
  todas las celdas y las bases varían con sd 1.5 puntos [I `plan3/final/potencia/potencia_plan3_salida.txt`]:

  | Criterio de "sentido entre entrenamientos" | Efecto −3 % | −5 % | −8 % | Falso positivo por celda (efecto medio 0) |
  |---|---|---|---|---|
  | (a) IC entero del lado, 4 de 5 bases (borrador) | 0.15 | 0.99 | 1.00 | 0.0001 |
  | **(b) Cambio del lado (signo), 4 de 5 bases; con 3 bases, 3 de 3** | 0.59 | 1.00 | 1.00 | 0.005 |
  | (c) Sin criterio: solo la versión evaluada | 0.62 | 1.00 | 1.00 | 0.023 |

  Con 3 bases y llegadas regulares, (b) "3 de 3" y (a) "2 de 3 con IC" rinden parecido (potencia 0.63 y 0.66 con −3 %;
  falso positivo 1.4 % y 1.9 %).
- El borrador exigía el sentido entre entrenamientos solo en H2, H3 y H5. Las demás hipótesis de método (mensajes,
  observación, episodios, reloj) no veían la variación entre entrenamientos.

**El paquete recomendado** (cada punto con su alternativa):

| # | Regla recomendada | Alternativa y su consecuencia |
|---|---|---|
| 1 | La regla de `veredicto.py` no cambia; se aplica frente a la referencia de A1 | — |
| 2 | **Solo se cita lo que se repite en T1 y T2.** FUNCIONA y MEJORA dan MEJORA; MEJORA y EMPATA dan EMPATA; MEJORA y FALLA dan CONTRADICTORIO | Que mande T2, o juntar tandas: más etiquetas positivas, menos protección |
| 3 | **Sentido entre entrenamientos en TODA afirmación sobre el método**, con bases emparejadas por semilla: criterio (b) de la tabla | (a): casi no se podría afirmar un −3 %. (c): un entrenamiento con suerte bastaría |
| 4 | Holm dentro de cada familia, por tanda. Las etiquetas no se corrigen (con efecto nulo, MEJORA en las dos tandas ≈ 0.0006). **H1 global ("en ningún caso es peor") se prueba por intersección-unión: cada caso al 5 %, sin Holm.** Holm solo para las afirmaciones caso por caso | Holm también en las etiquetas: más estricto que lo entregado |
| 5 | **No inferioridad (+2 %) con tres lecturas:** no es peor (límite superior ≤ +2 % en las dos tandas), es peor (IC entero sobre +2 %) o **no concluyente** (el IC cruza +2 %) | Dos lecturas: un "no pasa" se leería como pérdida aunque falten semillas |
| 6 | C0 (los checkpoints entregados re-elegidos con la selección nueva) es el control de la selección. **Nunca se cita en lugar del IPPO entregado** | Solo IPPO entregado: mezcla entrenamiento y selección |
| 7 | Convergencia sobre la media de las 16 semillas, en retraso total. Nunca se agregan episodios para quitar un PENDIENTE | La regla del Cap. III (999 y 1999): con 16 semillas no tiene sentido |
| 8 | **A ciegas comprobable.** Los CSV de las tandas decisivas van a una carpeta fuera de git hasta el cierre; cada mañana se sube solo un manifiesto con su sha256. Los logs de esos trabajos dicen semilla y duración, sin métricas. Un fallo se diagnostica con el error, nunca con resultados | Versionar los CSV cada mañana: nadie podría mostrar que no se miraron |
| 9 | **Todas las reglas en la parte A del prerregistro, antes de la primera noche (día 4).** La parte B (antes de la primera evaluación decisiva, día 14) solo agrega el archivo y el sha256 de cada referencia congelada y detalles que no cambian reglas (valores de la mezcla). Cada parte y cada enmienda: commit de Fabian, push, **tag anotado** y **correo al asesor** con el sha256. Fusión de `plan3` con commit de fusión, sin squash ni rebase | Dos partes como el borrador: hipótesis escritas con las referencias a la vista |
| 10 | **Enmiendas.** Después de la parte A solo por error de código, por un trabajo que no se puede correr o por lo ya anunciado (β de la política por red, detalles de la mezcla). Cada una dice qué datos estaban a la vista (referencias, validación, entrenamiento). Desde la primera noche decisiva, solo errores de código | Enmiendas libres: el diseño se podría ajustar con datos a la vista |
| 11 | **Prueba final.** Nunca se usa para juzgar una hipótesis o etiqueta prerregistrada (por ejemplo, para "rescatar" una que salió MEJORA en T1 y EMPATA en T2). Lo que se cite de ella dice "elegido después de ver T1 y T2, una tanda" | Usarla para desempatar: elección a posteriori |
| 12 | **Errores de análisis encontrados después de abrir los datos:** se corrigen solo errores de código y se muestran las dos cifras | Corregir cualquier cosa: forking paths |

**Recomendación: el paquete completo, con el criterio (b).**

**Por qué.**
- Atiende las dos críticas altas de método y la mayoría de las medias, sin cambiar la regla de lo entregado.
- El criterio (b) conserva casi toda la potencia de mirar solo la versión evaluada y baja su falso positivo de 2.3 % a
  0.5 %.
- Lo único que no se puede demostrar es que nadie miró. Sí se puede demostrar que las reglas son anteriores a los
  datos y que los archivos no cambiaron después de producirse.

**A más tardar:** día 0. Fabian sube la parte A el día 4.

---

## A6. Alcance de la Etapa 4 y calendario

**Qué hay que decidir.** Tres cosas:
1. qué se corre en la Etapa 4;
2. si la prueba de factibilidad que se aprobó como Etapa 0 se corre aparte;
3. si la cola corre solo de noche.

Con eso queda fijada la fecha real.

**Lo que ya se sabe.**
- **El programa aprobado decía "una sola de las dos"** para la Etapa 4: corredores de 3-5 semáforos o una política por
  red [M `analisis_mejora_2026-11-04/salida/programa.txt`, Etapa 4]. El borrador corría las dos.
- **El código es el cuello.** Las tareas del propio borrador sumaban 12.9-14.4 días, sin el generador de trabajos ni los
  pasos que eligen la versión evaluada [M, suma de PLAN3]. Con las correcciones y A4 son ~18-19 días.
- La política por red es una mejora del modelo con un problema medido detrás: la política de P2 con la demanda de P1
  queda +70 % [M `plan2/demanda/resumen_demanda.csv`, vía programa]. Sus comparadores (V2 en los 12 niveles) ya están
  en la Etapa 1. Cuesta 1 día de código.
- Los corredores prueban si los mensajes valen más con más cruces (la pregunta central de la tesis), pero son
  escenarios sintéticos; RESCO advierte que se relacionan poco con redes reales [L]. Cuestan 1.75 días de código.
- **Factibilidad aparte.** El 05.11 ya se midió, con semillas de prueba, lo que esa prueba quería saber: hay margen con
  llegadas aleatorias. IPPO entregado le gana al fijo instalado en P2 (−12.0 %) y en P6 (−41.1 % en media, −16.7 % en
  mediana) y al actuado en esos dos casos; el actuado le gana −14 % al fijo re-ajustado en P1 [M RESUMEN §2;
  `prueba_barrido_p1.txt`]. No es un veredicto: semillas de prueba, fijo sin re-ajustar en P2 y P6.

**Opciones.**

| Tema | Opción | Qué se podrá afirmar | Costo |
|---|---|---|---|
| Etapa 4 | **(a) Solo la política por red** (corredor, red y malla; llegadas regulares; comparada con la V2 de cada nivel) | Si una política sostiene todos los niveles de su red (H10) | 73 h-p (~6 h); 1 día de código |
| | (b) Solo los corredores de 3-5 semáforos | Si la ventaja de los mensajes crece con más cruces (H13) | ~55 h-p; 1.75 días: +1 día de calendario |
| | (c) Las dos | Las dos preguntas | +55 h-p; +1-2 días de calendario |
| | (d) Ninguna | Ninguna de las dos | −73 h-p; −1 día |
| Factibilidad | **(a) No se corre aparte.** Su pregunta (H0) se responde con las tandas decisivas de la Etapa 2; las cifras exploratorias de arriba se informan ya | La respuesta llega con 100 semillas y dos tandas | 0 |
| | (b) Correrla en 9001-9030 como exploratoria | Una respuesta temprana que no decide nada | ~13 h-p (~1 h) |
| Cola | **(a) Solo de noche, con hora de corte:** no se lanza un trabajo que no alcance a terminar; los entrenamientos largos se parten en tramos de ≤ 5 h | La PC queda libre de día | incluido |
| | (b) También de día cuando la PC esté libre | Se gana ~1 día (el código sigue mandando) [I] | 0 |

**Calendario con la recomendación** (detalle en `CRONOGRAMA.md`):

| | Conservador + 10 % (base) | Central |
|---|---|---|
| Cómputo | ~1901 h-p, ~159 h de reloj | ~1506 h-p, ~126 h |
| Noches con trabajo | 17 (días 4-20) | 15 (días 4-18) |
| Código | ~18-19 días (termina el día 19) | igual |
| Fin del análisis | día 22 | día 21 |
| **Total** | **~27 días** | **~26 días** |

Lo que más mueve la fecha es el código: cada día de código es un día más al final.

| Variante | Total |
|---|---|
| Recomendada | ~26-27 días |
| Sin las piezas de A4 | ~25 días |
| Sin A4 y sin Etapa 4 | ~24 días |
| Etapa 4 solo con corredores | ~27 días |
| Etapa 4 con las dos | ~28 días |
| Cola también de día cuando la PC está libre | ~26 días |

**Recomendación: (a) en los tres temas.**

**Por qué.**
- Respeta el programa aprobado ("una sola de las dos").
- La política por red es la que ataca un problema medido del modelo, y su código es el más corto.
- La factibilidad ya no decide nada: sin puertas, correrla aparte solo agrega datos.

**A más tardar:** día 0.

---

## A7. El desorden de Lima: perfil, mezcla y conductores

**Qué hay que decidir.** Cómo se agrega el "desorden real" que pidieron Fabian y el asesor (28.09), más allá de las
llegadas aleatorias.

**Lo que ya se sabe.**
- **Perfil dentro de la hora.** En bloques de 10 min con el mismo total (0.67, 1.0, 1.33, 1.33, 1.0, 0.67), el fijo de
  P1 pasa de 32.1 a 51.5 s/veh y el actuado le gana −15.9 % [M `plan3/demanda/salidas/prueba_post.txt`, fijo sin
  re-ajustar].
- **Composición.** La única composición de tránsito de Lima que se pudo abrir es la línea cortina del Rímac (JICA 2013,
  Tabla 2.16) [L]: autos y taxis 68.9 %, transporte público 14.6 %, camiones 12.7 %, motos 3.8 %. Los camiones vienen
  sobre todo de vías de carga [L].
- **Carga.** Con los mismos veh/h, la mezcla sube el retraso del fijo de P1 +36 a +61 %. Con los mismos vehículos
  equivalentes (INVERMET), queda a −0.5/−3.9 % de la base con llegadas regulares [M `prueba_mezcla.txt`].
- **Conductores.** No hay parámetros de conducción medidos en Lima en fuentes abiertas [L]. `startupDelay` es muy
  sensible: 0.5 s sube el retraso +13 %, 1 s +151 % y 2 s traba la red [M].

**Opciones.**

| Tema | Recomendada | Alternativas | Costo de la recomendada |
|---|---|---|---|
| Perfil | Bloques de 10 min con el mismo total, llegadas aleatorias, en P1 y P3. Decide el fijo de un plan; al lado, un fijo por bloques | El perfil de `corredor_var` (×1.5: mezcla más demanda con punta); no correrlo | ~33 h-p |
| Composición | JICA 2013 sin camiones; transporte público repartido con la flota ATU 2021: autos 78.9 %, motos 4.4 %, combis 4.8 %, micros 5.64 % (errata corregida el 05.11 al implementar: el diseño decía 5.7 %), buses 6.3 % [I: aritmética sobre [L]] | JICA con camiones; el aforo de La Bolichera (una intersección) | ~39 h-p (todo el bloque de mezcla) |
| Parámetros | Los de SUMO por clase; combi (6 m, 2.0 m/s²) y micro (8 m, 1.5 m/s²) son supuestos escritos [S] | — | — |
| Demanda | Mismos vehículos equivalentes (×0.84 los veh/h) [I] | Mismos veh/h (mezcla carga con composición) | — |
| Conductores | No se tocan al entrenar; arranque lento de 0.5 s solo al evaluar, como sensibilidad | Entrenar con 0.5 s (un valor sin fuente decidiría el resultado) | incluido |

**Recomendación:** la columna recomendada. Todo se presenta como **sensibilidad**, no como "Lima calibrada".

**Por qué.** Usa la única fuente de tránsito de Lima que se pudo abrir, no confunde mezcla con carga y no deja que un
valor sin fuente decida el resultado.

**A más tardar:** día 0 la decisión; los valores finales con sus fuentes van en la parte B (día 14), antes de que corra
la mezcla.

---

## A8. Cómo entra en la tesis y qué se cita

**Qué hay que decidir.** Dónde va el bloque nuevo, qué se escribe en el resumen y las conclusiones para cada resultado
posible, y cómo conviven las cifras nuevas con las entregadas.

**Lo que ya se sabe.**
- El asesor pidió (09.10) poco dato, tablas simples y respuesta primero [M memoria del proyecto].
- **El programa aprobado dice "No agregar tablas al Cap. V: lo nuevo va en un anexo con una tabla simple".** El
  borrador ponía una tabla en el Cap. V.
- El Cap. III (l. 1425-1432) dice que las llegadas aleatorias quedan fuera del plan. La Sección 5.5.1 trae la V2
  validada con 2 semillas.
- Una frase entregada no vale en P4: "en P3-P5 el fijo es el ciclo mínimo"; ahí el ciclo mínimo queda −1.0 %
  [−2.4, 0.5] frente al fijo desde 10 s [M `plan2/robustez_veredicto.md`, vía críticas].
- `sintesis_plan.py` escribe por defecto en `plan2/` y `TESIS/` [M l. 30-31 y 503-504]: no sirve para el número único
  nuevo.

**Opciones.**

| Tema | Opción | Consecuencia |
|---|---|---|
| Dónde | **(a) Sección corta en el Cap. V, sin tablas nuevas** (pregunta, respuesta, criterio de lectura y una figura con bandas), **más un anexo nuevo** con la tabla simple y el detalle | Si algo mejora, el jurado lo ve en el cuerpo, y se respeta el programa aprobado |
| | (b) Solo el anexo, con una línea en el Cap. V | Cambia lo mínimo; una mejora quedaría escondida |
| | (c) Cifras nuevas en las tablas del Cap. V | Mezcla estudios y recarga el capítulo. No conviene |
| Etiqueta entregada y nueva | **(a) Se citan juntas, cada una con su referencia** (ejemplo de forma: "P1: FUNCIONA frente al fijo del 25.09; MEJORA frente al fijo ajustado al segundo") | Nada entregado se borra y se ve qué cambió y por qué |
| | (b) La nueva reemplaza a la entregada en resumen y conclusiones | Más simple, pero cambia un veredicto congelado |
| | (c) La entregada sola; la nueva solo en el anexo | No se ve la mejora |
| Número único | **Media geométrica frente a la referencia que decide (fijo fino), con P6 (no P6e), una cifra por tanda; al lado, la misma frente al fijo entregado.** Se calcula dentro de `veredicto3` (nunca con `sintesis_plan.py`) | Comparable con el número entregado y sin mezclar tandas |
| Modelo citado | **El de la regla de promoción (A4); si no es V2, se nombra, y la etiqueta de V2 va al lado** | La mejora queda a la vista y no se esconde que es otro modelo |
| Corrección de P4 | **(a) Corregir la frase entregada, con una nota** | El texto queda exacto; toca texto entregado, por eso lo confirma Fabian |
| | (b) Dejarla y anotar la diferencia solo en el anexo nuevo | No toca lo entregado, pero el Cap. V queda con una frase inexacta |

**Plantilla de redacción.** El prerregistro (§17) trae, para cada pregunta, la frase del resumen y de las conclusiones
según el resultado: pasa, no pasa, no concluyente o PENDIENTE. El puente con 1001-1030 y P6e nunca van al resumen. Cada
cifra del cuerpo lleva sus dos tandas.

**Recomendación:** las marcadas en negrita. La V2 de la 5.5.1 no se toca; si la re-elegida difiere, se muestran las
dos. Resumen, abstract, objetivos, Cap. I y conclusiones cambian solo con la confirmación de Fabian, cambio por cambio.

**Por qué.** Sigue el programa aprobado, los criterios de claridad del asesor y la regla de no cambiar veredictos
entregados.

**A más tardar:** día 0 la plantilla (va en la parte A); el texto, al final.

---

## Grupo B. Decisiones técnicas (se aplican por defecto)

| # | Decisión | Por defecto | Por qué |
|---|---|---|---|
| B1 | Aislamiento y cola | **Dos worktrees:** `../demo_rl_plan3` (rama `plan3`, ejecución; solo avanza entre noches, con commit subido) y `../demo_rl_plan3_dev` (rama `plan3-dev`, desarrollo); se fusionan con commit de fusión. `plan3/cola.py` (copia de la de plan2) con: verificación **antes de cada lanzamiento** de que el árbol está limpio y coincide con `lanzamiento.sha256`; commit y hash guardados por trabajo; `--hasta HH:MM` con la duración estimada de cada trabajo; éxito solo con código 0 **y las salidas esperadas completas**; un huérfano sin salidas completas pasa a fallido. Protecciones en 3 capas: la capa 1 desenvuelve el lanzador y aplica las reglas del programa interno, con bloques de semillas, bases y scripts leídos de la tabla del prerregistro §3 (una sola fuente, sha256 comprobado contra origin); `--salida` relativa bajo `plan3/` o absoluta dentro de `plan3/`; TESIS con límites de palabra; la capa 3 usa `git diff main...HEAD -- plan2 TESIS`. "Protecciones antes" comprueba Python 3.14.6, torch 2.14.0+cpu y SUMO 1.25.0. Respaldo de `plan3/checkpoints` cada mañana. Fabian pausa Windows Update y la suspensión durante el bloque. `cpus=1`, barridos con `--procesos 1`, 12 procesos | La cola corría desde el árbol que se edita de día y no tenía hora de corte [M `plan2/cola.py` l. 192-220]; un huérfano sin traceback se marcaba como hecho [M l. 88-95]; el prototipo de la capa 1 rechazó 7 de 7 comandos legítimos y aceptó un `rl_ippo train` sin `--etiqueta` a través del lanzador [M `critica_codigo/salidas/capa1_prototipo_vs_plan.txt`]; el prototipo guarda el commit solo al arrancar [M `plan3/infra/prototipo/cola.py` l. 123-126] y trae bloques de semillas viejos [M `protecciones.py` l. 38-46] |
| B2 | Registro de escenarios | `escenarios_plan3.py` aparte y el lanzador `con_escenarios.py`, que los suma solo dentro de su proceso. Nunca en `DERIVADOS` | `DERIVADOS` crea 6 trabajos por escenario en la cola de plan2 [M demanda e infra] |
| B3 | Insumos y respaldo | Antes de todo, respaldo con manifiesto sha256 de los checkpoints de `demo_rl` (6360) y `demo_rl_diag` (2640) fuera de los repositorios; insumos copiados a `plan3/insumos/` con manifiesto; las referencias de 1001-1030 se reutilizan (copias) | No están en git; son la única copia de C0 [M infra] |
| B4 | Qué se versiona | Código, escenarios, prerregistro, estado de la cola, políticas y resultados no decisivos. **Los CSV decisivos (T1, T2, extensión de H1, prueba final) quedan en `plan3/ciego/`, ignorada por git, hasta `cierre.ok`; cada mañana se sube solo `plan3/cola/manifiesto_ciego.json` (ruta, sha256, filas y semillas de cada CSV).** Los tripinfo se borran cada mañana; los extras solo si van en una figura | A ciegas comprobable (A5 #8); ~40-65 MB versionados [I infra] |
| B5 | Nombres (los nombres finales de las etiquetas están en `plan3/generar_trabajos3.py`) | Etiqueta propia con prefijo `p3` en todo brazo publicado, escrita en el meta: `p3v2reg`, `p3v2poi`, `p3c0`, `p3c0poi`, `p3v2vieja`, `p3piso200`, `p3e400`, `p3e400poi`, `p3abldesc`, `p3ablexpl`, `p3obsreg`, `p3obspoi`, `p3m7norm`, `p3m7forz`, `p3m7msg`, `p3m7`, `p3ent`, `p3reloj2`, `p3reloj2poi`, `p3completo`, `p3completopoi`, `p3red`, `p3per`, `p3mix`. Sin mensajes: `--variante local` con la misma etiqueta. `nombres.py` exige que cada (escenario, brazo, tanda, carpeta) sea único en **toda la lista de trabajos**, no solo frente a archivos que ya existen | `evaluar` arma el nombre con la etiqueta y la base del meta [M `evaluar.py` l. 220-222 y 260]: sin etiqueta propia, C0 se llamaría como el IPPO entregado y la V2 vieja como una base de V2 |
| B6 | Llegadas aleatorias | Poisson de SUMO (`period="exp(q/3600)"`), sin rutas por semilla; redondeo al segundo declarado (+0.5 s/veh, igual en todos los brazos). **Prueba de números comunes con `departLane="best"` en `poi_P3`-`poi_P6` y P6e, IPPO por TraCI incluido, antes de la noche de las referencias.** Plan B costeado (rutas por semilla, ~50 líneas) solo si falla | Hoy está medido en P1 y P6 con la entrada por defecto [M `plan3/demanda/salidas/prueba_ab.txt`]; en P3-P6, con varios carriles, falta medirlo con `best` |
| B7 | Barrido fino | Regla única de A1. **Puntaje por periodo con un lector propio**: no se pasa `--tripinfo-output.write-undeparted` a `correr_sumo`; cada vehículo no insertado se asigna a su periodo por su salida programada (fin − departDelay) y se excluyen del total las filas con depart < 0. Prueba: en una configuración que se traba (P6 10/10), la suma por periodo es igual al total de `leer_tripinfo`. Con llegadas aleatorias, 2001-2010 en las etapas gruesa y fina y 10 finalistas con 2001-2030 [A1]. Archivos con nombre nuevo; nunca `--instalar` | Con write-undeparted, `leer_tripinfo` cuenta dos veces a los no insertados: 905 vehículos en vez de 827 y retraso 82.38 frente a 80.08 [M `critica_codigo/salidas/write_undeparted_doble_conteo.txt`; `comun.py` l. 81-96] |
| B8 | Fijo por franja | Un WAUT por semáforo, sin `procedure`, con su instante limpio (primer t ≥ 1800 s con el mismo estado en los dos planes); lo carga solo su brazo | Igual a `setProgram` y no corta verdes [M `plan3/referencias/waut/`] |
| B9 | Actuado ajustado | Descenso por coordenadas **en cadena** (un paso por coordenada, cada uno espera al anterior) con las rejillas fijas de A1; depende del fijo fino y de su desempate (la variante coordinada usa sus desfases); sin TraCI. **Prueba: sumo directo = TraCI también con `<param>` y con la variante coordinada** | La prueba del borrador cubría solo la variante por defecto; el costo de la cadena entra en el calendario |
| B10 | Regla simple y Max-Pressure | Reloj de 5 s por el gancho `decidir`; U ∈ {1, 2, 3, 4, 6} × G ∈ {30, 60}; MP por carril, con y sin ciclo máximo | Con U = ∞ reproduce el ciclo mínimo (sha256) [M] |
| B11 | Evaluación y veredicto | `evaluar3.py` con su propio ciclo por semilla (usa las funciones de brazo de `evaluar`): en las tandas decisivas escribe en `plan3/ciego/` y su log solo dice semilla y duración; guarda vehículos generados y no insertados por semilla y el retraso por media hora; opción "colas en cero" para a3 (apagada da el mismo CSV). `veredicto3.py` importa solo funciones puras; `comparar` rechaza semillas **que faltan y que sobran**; calcula el número único importando `sintesis_plan.indice_geo` (sin correr `sintesis_plan.py`); modo final bloqueado hasta `cierre.ok`. **`veredicto3` sale de la ruta crítica: se escribe en los días 18-19** | `evaluar.py` imprime métricas por semilla [M l. 307-309]; en el exploratorio, los CSV de 6001-6030 traen 31 semillas, con la 5001 [M `potencia_h1_salida.txt`]; `indice_geo` existe [M `sintesis_plan.py` l. 106] |
| B12 | C0 y la V2 del corredor y de D | C0 re-valida los 60 checkpoints entregados de cada una de las 18 celdas (antes, 999 y 1999 reproducen lo guardado). La V2 del corredor y la de D se reentrenan; **la identidad con `demo_rl_diag` se comprueba con `torch.equal` sobre los `state_dict`**, no con el sha256 del archivo | `torch.save` escribe el nombre del archivo dentro del zip: los mismos tensores con otra etiqueta dan otro sha256 [M `critica_codigo/salidas/torch_save_nombre_y_estado.txt`] |
| B13 | Código nuevo | **Se modifica en el lugar** (`rl_ippo.py`, `evaluar.py`, `comun.py`, `rl_corredor.py`), con toda opción apagada por defecto, y se pone el tag `entregado-2026-10-25` en 81378fb. **Prueba de no regresión:** con todo apagado, `rl_ippo` da el mismo CSV y 12/12 tensores; y fijo, actuado, ciclo mínimo y una política IPPO publicada, en 1001-1002, repiten dígito a dígito los parciales de `plan2/` en P1-P6. Escritura atómica con temporal por pid y `reemplazar` con reintentos; un trabajo "preparar" al inicio de cada noche genera los `_actuado`, `_trivial`, `_actuado_aj` y E2, y las evaluaciones dependen de él | Copias como `rl_ippo3.py` duplicarían ~3000 líneas y `evaluar` igual importa `rl_ippo` [M l. 213]; el tag deja el código entregado a un comando; `os.replace` falla en Windows si un SUMO tiene abierto el destino [M `barrer_fijo.py` l. 121-133] |
| B14 | Observación nueva | L = 75 m; E2 suscritos y 2 llamadas por carril al decidir; la salida real del enlace en una ranura nueva; archivo E2 generado por el trabajo "preparar"; prueba de costo ≤ ×1.35 | La marca de giro reproduce `bloqueo.md` (12 %); cuesta +27-34 % [M modelo] |
| B15 | Reanudación y 400 episodios | **`--guardar-estado` escribe un archivo aparte** (`<tag>_epNNN.estado.pt`: Adam con su contador, `random`, numpy global, torch y el `default_rng` de `sembrar`); la política `.pt` no cambia. `--reanudar` copia a la etiqueta nueva los checkpoints ≤ el episodio de partida y precarga `val_serie` y `val_total_serie`. **Se programa y se prueba antes de la primera noche:** en P1 y P6, 20 episodios seguidos = 10 + 10 reanudados (CSV, tensores y Adam); `evaluar` juega igual una política entrenada con la opción; con validación cada 5, reanudar en 10 publica la misma política y el mismo meta. `--lr-horizonte 200 --lr-piso 0.1`; el "200 con piso" se publica en un paso aparte (`p3piso200`). Todo entrenamiento de más de 5 h se parte en tramos encadenados; un reintento sigue desde el último estado. **H9b pasa a descriptiva**; se agrega, sin costo, "400 eligiendo entre 20 checkpoints (ep. 20, 40, ..., 400)" | `Politica.cargar` usa `weights_only=True` y no carga el estado de numpy [M `rl_ippo.py` l. 388-393; prueba en `torch_save_nombre_y_estado.txt`]; `val_serie` empieza vacía y la política se publica desde la propia etiqueta [M l. 1072 y 1112-1117]; "200 con piso" y "200 sin piso" comparten 18 de sus 20 checkpoints y en 13 de 20 metas de V2 el elegido es ≤ 180 [M RESUMEN §4] |
| B16 | Política por red (si A6 la elige) | `--scale` por episodio; rangos: corredor ×0.5-2.0 de P1, red 905-3620 veh/h, malla 1810-8700; currículo de 200 episodios; 600 episodios; validación 8 semillas × 3 niveles cada 20, por media geométrica; `--norm-valor` con β fijado por un piloto de humo y una enmienda anunciada; tramos de ≤ 5 h. H10 al 80 %: corredor 4 de 5 niveles, red 6 de 7, malla 5 de 6 | `--scale 0.5` reproduce `dem_corredor_t905` [M]; la malla dura ~13.7 h por base en el régimen conservador [I] |
| B17 | Corredores (solo si A6 los elige) | 3, 4 y 5 semáforos a 300 m, 1 carril, demanda por cruce como P1; uno de 3 semáforos y 2 carriles. H13b: pendiente por base, con signo en 3 de 3 y la de las versiones evaluadas con IC entero bajo 0 | Diseño supuesto [S] |
| B18 | Semillas auxiliares | Bases extra 14042 y 16042; validación 999…9999 y 15001-15008; **promoción 15009-15024**; ajuste 2001-2003, 2001-2010 y 2001-2030; **extensión de H1/H2: 8031-8120 y 13031-13120**; humo: base 7 y 424301-424360 (también R0.3 y las pruebas de 0.12); no regresión: 1001-1002, solo con controles entregados; 9001-9030 sin uso | Todas libres: 0 usos en CSV o JSON [M `plan3/final/semillas/t3_semillas_plan3.txt`, búsqueda extendida hoy a todos los rangos, también en las carpetas de análisis] |
| B19 | Perfil | `rou_perfil_poisson`; el lector de plan3 quita `_b<k>`; fijo por bloques con un WAUT de 6 programas | Conteos por bloque medidos como se esperaba [M demanda 2.d] |
| B20 | Generador de trabajos | `plan3/generar_trabajos3.py`, tarea propia (~1 día con sus pruebas): declara por trabajo las salidas esperadas, la duración estimada y las dependencias; los pasos que eligen la versión evaluada son trabajos (`p3_elegir.py`); los pasos secuenciales van en cadena; toda evaluación de una versión elegida depende de **todas** las bases de su regla y de su paso de elección. Prueba en seco: el 100 % de la lista pasa la capa 1 y las dependencias existen | En el modelo de costos del borrador, a3 no dependía de su entrenamiento, la V2 regular jugada con llegadas aleatorias dependía de 3 de sus 5 bases y las transferencias solo de la base 42 [M `critica_codigo/salidas/dependencias_costos_plan3.txt`] |
| B21 | Versión evaluada y emparejamiento | Mediana por `val_elegido` (la 3.ª de 5, la 2.ª de 3; empate: la base menor). **H1, H2, el cuadro 2×2 y el puente usan la V2 evaluada entre 42, 2042 y 4042; la mediana de 5 se usa frente a las referencias.** Las comparaciones entre brazos entrenados se emparejan por base (misma semilla). La "V2 vieja" sigue la regla del 25.09 con las bases 42, 2042 y 4042. Con un número par de bases (una cayó), la peor de las dos centrales. La mejor base por validación se informa al lado [A3] | Sin esta regla se podría elegir después cuál V2 va en cada comparación (crítica de método 5); `consistencia_bases` del prototipo depende de cuántas bases se le pasen [M `prototipo_veredicto3.py` l. 157-166] |
| B22 | Caídas, errores y relanzamientos | Caída de infraestructura (reinicio, corte, proceso matado): se relanza con el mismo id y la misma semilla, desde el último estado; sin límite, se anota, y los primeros episodios deben repetir los del intento anterior. Error de código: se corrige y se corren de nuevo los trabajos afectados con ids nuevos (`_r2`), se conservan las salidas viejas y una enmienda lo declara. Falla del método (pérdida NaN, política sin publicar) en dos intentos: la base cuenta como fallida y "fuera del sentido" | El borrador tenía dos reglas que chocaban (§9 y §13) y la regla "los ids hechos no cambian de comando" impedía que un arreglo llegara a trabajos ya corridos |
| B23 | Bases nuevas en 2715 y D (H8a) | V2 y observación nueva también con las bases 14042 y 16042 en 2715 y D; H8a se juzga con 5 bases (4 de 5) y se informa aparte el resultado en las 2 bases nuevas | 2715 y D se eligieron porque V2 falló ahí con 42, 2042 y 4042: sin bases nuevas, parte de una mejora podría ser regresión a la media. ~10 h-p |
| B24 | Reloj de 2 s (si A4) | `--paso-decision 2`: decide y publica mensajes cada 2 s una vez cumplido el verde mínimo; **la unidad del descuento de V2 y la normalización de la recompensa siguen en 5 s**; va con `--sin-forzadas` (se declara que H14 mide los dos juntos; en D se separan con el brazo de solo `--sin-forzadas`); con `--paso-decision 5`, 0 diferencias | Hoy las dos usan `PASO_CONTROL` [M `rl_ippo.py` l. 624 y 854]: sin separarlas, el reloj cambiaría también el descuento. Con 2 s, las decisiones dentro del verde mínimo (10 s) pasan de 1 a 4 por verde y llenarían el lote de decisiones forzadas [I, de la máscara] |
| B25 | Modelo completo y promoción (si A4) | Completo = `--v2 --obs-cercana 75 --norm-valor --sin-forzadas --msg-cada-paso --episodios 400 --lr-horizonte 200 --lr-piso 0.1` (+ `--paso-decision 2`). Promoción: cada variante prerregistrada de la celda aporta su versión evaluada (mediana de 42, 2042 y 4042); se re-valida en 15009-15024; gana la de menor media si le gana a V2 por ≥ 1 %. El resultado se registra con su sha256 antes de `cierre.ok` | Elegir entre ~6 variantes con la misma validación que eligió los checkpoints favorecería al que tuvo suerte; el margen de 1 % evita promover ruido |
