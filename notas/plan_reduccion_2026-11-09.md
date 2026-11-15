# Plan maestro: reducir y ordenar la tesis (09.11.2026)

Fabian pidió el 09.11.2026 reducir la tesis y que se lea como una investigación, no como una bitácora de experimentos.
Aprobó estas metas de páginas y que el **resultado central sea el segundo estudio**. Este documento es la guía común
de quienes reescriben cada parte. Léelo entero antes de tocar un archivo.

## 1. Por qué

- El asesor calificó las entregas con 6.5/10 y dijo: la tesis parece experimental, sin un punto al que llegar; hay
  tantos datos que no se entiende; pidió quitar lo que hace ruido, tablas simples, empezar cada capítulo de forma
  didáctica, dar el criterio de lectura, analizar qué caso no salió y por qué, y conclusiones simples por objetivo.
- Hoy el cuerpo tiene 189 páginas y los anexos 116. Hay 96 tablas y 21 figuras. Las conclusiones ocupan 15 páginas y
  traen 277 cifras.
- La causa: el texto cuenta la historia de lo que se fue probando y corrigiendo (fechas, "después del veredicto",
  enmiendas, cola de trabajos, prueba de humo), con cuatro capas de resultados que usan métricas y referencias
  distintas. El lector no sabe cuál es el resultado.

## 2. Metas de tamaño (páginas impresas)

| Parte | Archivo | Hoy | Meta | Palabras de texto, aprox. |
|---|---|---|---|---|
| Introducción | `introduccion.tex` | 10 | 6 | 1500 |
| I. Estado del arte | `capitulo1.tex` | 10 | 10 | no se toca |
| II. Marco teórico | `capitulo2.tex` | 23 | 12 | 3200 |
| III. Método | `capitulo3.tex` | 47 | 22 | 5700 |
| IV. Implementación | `capitulo4.tex` | 33 | 12 | 3300 |
| V. Resultados | `capitulo5.tex` | 41 | 25 | 6500 |
| Conclusiones | `conclusiones.tex` | 15 | 4 | 1200 |
| Recomendaciones | `recomendaciones.tex` | 10 | 2 | 650 |
| Anexo A (tablas) y B | `anexos.tex` | 23 | 9 | |
| Anexo C (exploratoria) | `anexo_c_exploratoria.tex` | 20 | 6 | 1100 |
| Anexo F (robustez) | `anexo_f_robustez.tex` | 20 | 8 | 1900 |
| Anexo G (diagnóstico) | `anexo_g_diagnostico.tex` | 26 | 10 | 2900 |
| Anexo H (segundo estudio) | `anexo_h_segundo_estudio.tex` | 14 | 10 | |
| Anexo I (detalles de implementación, nuevo) | `anexo_i_implementacion.tex` | 0 | 5 | 1300 |

Una página impresa lleva unas 280 palabras de texto (interlineado 1.5) o una tabla mediana. Cuenta las palabras del
texto que se imprime (sin comentarios) antes de entregar. Pasarse un 10 % de la meta está bien; el doble, no.

## 3. El hilo de la tesis (lo que todo capítulo debe servir)

**Pregunta.** ¿Un control de semáforos que aprende con aprendizaje por refuerzo y recibe información de sus semáforos
vecinos reduce el retraso por vehículo frente a un plan de tiempo fijo bien ajustado, sin quedar por detrás del
control actuado?

**Tres preguntas de trabajo** (cada una tiene su evidencia y su respuesta):

1. **¿Reduce el retraso?** Se responde con el resultado central.
2. **¿De qué depende?** De la información del vecino, de lo que el agente ve, del reloj de decisión y de la demanda.
3. **¿Hasta dónde llega?** Alcance y límites: dónde funciona, dónde no y por qué.

**La evidencia se cuenta en tres pasos de exigencia creciente.** No son cuatro capas sueltas: es un solo argumento.

| Paso | Llegadas | Referencia | Métrica | Qué da |
|---|---|---|---|---|
| 1. Primer estudio (el plan de pruebas) | Regulares | Fijo ajustado con barrido de 5 en 5 s | Retraso | Gana en el corredor y en la red con rotonda, empata en la malla: −6.83 % frente al fijo y −14.35 % frente al actuado |
| 2. Medición más estricta | Regulares | Fijo ajustado desde 10 s | Retraso total | La ventaja frente al fijo casi desaparece (−0.03 %); frente al actuado se mantiene (−11.45 %). Hallazgo: con llegadas regulares, un fijo bien ajustado es casi óptimo |
| 3. **Segundo estudio (resultado central)** | Aleatorias (y regulares) | Fijo ajustado al segundo, vuelto a ajustar con cada tráfico; el actuado ajustado veta | Retraso total | **Gana en 3 de 6 casos; −10.8 % y −11.1 % en las dos tandas.** Con llegadas regulares empata (−0.4 %) |

**Respuesta central (cítala igual en todas partes).** Con tráfico que llega al azar, y frente al plan fijo más
exigente que se pudo construir (ajustado al segundo para cada caso), el modelo gana en tres de los seis casos: el
corredor con sus dos demandas y la malla con demanda alta. En esos tres baja el retraso total entre un 16 y un 27 % y
supera también a todas las demás referencias, incluido el actuado ajustado. En la red con rotonda y en la malla con
demanda nominal empata o pierde por menos de un 2 %. Resumido en un número: −10.8 % en una tanda de evaluación y
−11.1 % en la otra (frente al fijo entregado, −15.8 y −14.5 %). Con llegadas regulares, un fijo bien ajustado es casi
óptimo y el modelo empata con él (−0.4 %).

**Por qué gana donde gana (lectura posterior al cierre; se dice así).** Gana donde reaccionar al tráfico sirve: en
los mismos tres casos donde el actuado ajustado también mejora al fijo. En los otros tres, ningún control probado
supera al fijo ajustado al segundo. En la red con rotonda, ese fijo es el ciclo más corto posible con uno o dos
semáforos corridos 1 s, y un modelo que decide cada 5 s (o cada 2 s) no puede dar ese desfase. La rotonda sin semáforo
se satura desde 1.3 veces la demanda nominal, así que los semáforos de esa red nunca quedan exigidos.

### Cifras canónicas del resultado central (segundo estudio, llegadas aleatorias)

Cambio del retraso total del modelo citado frente al fijo ajustado al segundo, tanda 1 y tanda 2 (100 semillas cada
una), con IC95:

| Caso | Red y demanda | Veh/h | Veredicto | Tanda 1 | Tanda 2 |
|---|---|---|---|---|---|
| P1 | corredor, nominal | 1810 | FUNCIONA | −16.3 [−17.7, −15.0] | −17.1 [−18.6, −15.8] |
| P2 | corredor, alta | 3620 | PENDIENTE (provisional: FUNCIONA) | −19.8 [−20.5, −19.0] | −20.2 [−20.9, −19.6] |
| P3 | red con rotonda, nominal | 2150 | FALLA | +1.6 [+1.4, +1.7] | +1.6 [+1.4, +1.8] |
| P4 | red con rotonda, alta | 2580 | EMPATA | −0.5 [−1.3, +0.2] | 0.0 [−0.7, +0.6] |
| P5 | malla, nominal | 4350 | EMPATA | +0.2 [−0.1, +0.5] | +0.3 [0.0, +0.7] |
| P6 | malla, alta | 8700 | FUNCIONA | −25.7 [−28.4, −23.0] | −26.9 [−30.8, −23.5] |

- Modelo citado: el modelo completo en P1, P2, P4 y P6; IPPO con mensajes corregido en P3 y P5.
- IPPO con mensajes corregido solo (sin los cambios del modelo completo): P1 MEJORA (−6.3 y −8.7), P2 FUNCIONA (−5.7 y
  −5.8), P3 FALLA (+1.6), P4 FALLA (+1.2 y +1.5), P5 EMPATA, P6 FUNCIONA (−18.4 y −20.2). Resumen: −4.8 y −5.6 %.
- Frente al actuado ajustado: P1 −3.3 y −3.8; P2 −19.0 y −19.5; P6 −11.5 y −12.9.
- Frente al fijo entregado: P1 −18.2 y −18.8; P2 −27.3 y −27.5; P6 −39.0 y −32.4.
- Con llegadas regulares (IPPO con mensajes corregido, 30 semillas por tanda): P1 MEJORA −2.8 y −2.8; P2 EMPATA; P3
  FALLA +1.7 y +1.7; P4 EMPATA; P5 PENDIENTE (EMPATA); P6 EMPATA. Resumen: −0.4 % [−1.0, +0.1] y −0.4 % [−0.8, +0.1].
- Qué explica la mejora (hipótesis registradas, llegadas aleatorias): los mensajes mejoran solo en P6 (−5.2 y −5.3);
  ver los vehículos cercanos mejora en P1, P2 y P6 (entre −5.9 y −9.7); entrenar 400 episodios, solo en P6 (−5.3 y
  −5.4); decidir cada 2 s no mejora en ninguno de 3 casos; el modelo completo mejora a IPPO con mensajes corregido en
  4 de 6 (P1, P2, P4 y P6).
- Sensibilidad (corredor y red, demanda nominal): con la mezcla de vehículos de Lima, MEJORA en el corredor (−3 a −4 %)
  y FALLA en la red (+1 a +2 %); con perfil de demanda de 10 min, FUNCIONA provisional en el corredor (−12.1 y −9.8) y
  FALLA en la red (+1.0 y +1.1).
- Rigor: reglas publicadas antes de entrenar, evaluación a ciegas, 201 entrenamientos (44 160 episodios), 740
  evaluaciones, dos tandas independientes que dan el mismo veredicto en los 19 casos evaluados.
- Meta de la tesis (reducir el retraso entre un 25 y un 40 %): con el resultado central se alcanza en un caso (P6,
  −25.7 y −26.9 %); el resumen en un número queda en −11 %.

Fuentes: `plan3/salidas/veredicto3.md` y sus CSV; `TESIS/secciones/anexo_h_segundo_estudio.tex` (ya escrito; es el
texto de referencia del segundo estudio); `plan2/veredicto.csv` y las tablas existentes para el primer estudio. **No
inventes ni recalcules cifras: copia las que ya están en la tesis o en esos archivos, con su comentario
`% fuente:`.**

## 4. Reglas de escritura

1. **Respuesta primero.** Cada capítulo y cada sección empieza diciendo qué responde y cuál es la respuesta. Después,
   cómo se lee lo que sigue.
2. **Poco dato.** En el cuerpo va la respuesta y la evidencia clave. Una idea por tabla. Si una cifra no cambia lo
   que el lector concluye, sale. El detalle va al anexo o queda en el repositorio.
3. **Investigación, no bitácora.** Se describe el diseño final y lo que mide, no la historia de cómo se llegó.
   Fuera: fechas de trabajo ("25.09", "el 28 de septiembre"), "se congeló", "cola de trabajos", "prueba de humo"
   como relato, commits, nombres de archivos y de programas, "antes decía". Una decisión tomada después de ver
   resultados se declara una vez, en una frase ("este análisis se decidió después del veredicto"), no en cada
   párrafo.
4. **Un nombre por cosa** (glosario de la sección 5). Sin nombres de código en `\texttt{}` dentro del texto, salvo
   en el Capítulo IV cuando sea indispensable y en el Anexo B.
5. **Frases cortas**, impersonales ("se midió", "se observa"), sin lenguaje de relleno. Párrafos de 3 a 6 líneas.
   Listas solo cuando ayudan a leer.
6. **Los resultados negativos se dicen igual que los positivos**, con su causa medida. No se suaviza ni se exagera.
7. **Nada de afirmaciones nuevas.** Solo se reorganiza y se sintetiza lo que ya está medido. Si falta un dato, se
   deja fuera y se anota en el informe final.
8. **Lo que sale no se pierde:** la versión anterior completa queda en el tag `entregado-2026-10-25`, en el respaldo
   `respaldo_tesis_2026-11-09_antes_de_reducir/` y en los CSV del repositorio. No hace falta conservar texto "por si
   acaso".

## 5. Glosario (úsalo tal cual)

| Nombre en la tesis | Qué es | Nombre de código (no usar en el texto) |
|---|---|---|
| IPPO con mensajes | Un agente PPO por semáforo, misma red neuronal, con información de los vecinos | ippo_vecinos |
| IPPO sin mensajes | Lo mismo, sin información de los vecinos | ippo_local |
| IPPO con mensajes corregido | IPPO con mensajes con las dos correcciones del entrenamiento (el descuento cuenta los segundos entre decisiones; los semáforos exploran a la vez) | V2 |
| Modelo completo | IPPO con mensajes corregido que además ve los vehículos cercanos, usa tres ajustes del entrenamiento, entrena 400 episodios y decide cada 2 s | p3completo |
| Modelo citado | El que representa a cada caso del segundo estudio (regla de promoción) | — |
| Fijo ajustado | El plan fijo del primer estudio (barrido de 5 en 5 s) | fijo_2509 |
| Fijo ajustado desde 10 s | El de la medición más estricta | fijo re-barrido |
| Fijo ajustado al segundo | El del segundo estudio, vuelto a ajustar por caso y tipo de llegadas | fijo fino |
| Actuado / actuado ajustado | Control actuado de SUMO, por defecto o con sus parámetros ajustados | — |
| Ciclo mínimo | Plan fijo con los verdes mínimos y sin desfases | trivial |
| Versión evaluada | El entrenamiento y la versión guardada que representan a un modelo | política publicada |
| Retraso / retraso total | timeLoss por vehículo / timeLoss más la espera para entrar a la red | timeloss_prom / retraso_total_prom |
| Veredicto | FUNCIONA, MEJORA, EMPATA, FALLA o PENDIENTE (en el registro del segundo estudio se llama "etiqueta") | — |
| Tanda | Un juego de semillas de evaluación independiente | T1, T2 |
| Primer estudio / segundo estudio | El plan de pruebas / el estudio con llegadas aleatorias registrado antes de entrenar | plan2 / plan3 |
| Llegadas regulares / aleatorias | A intervalos iguales / al azar (proceso de Poisson), con la misma demanda media | — |

Casos: P1 corredor nominal (1810 veh/h), P2 corredor alta (3620), P3 red con rotonda nominal (2150), P4 red con
rotonda alta (2580), P5 malla nominal (4350), P6 malla alta (8700).

## 6. Estructura nueva y etiquetas

**Regla de etiquetas.** Otros archivos citan etiquetas del tuyo. Conserva **todas** las etiquetas de tu archivo que
figuran en la lista "garantizadas", puestas en la sección, tabla, figura o ecuación que corresponda. Si quitas una
tabla o figura garantizada, no dejes la etiqueta en otro objeto: dilo en tu informe. Desde tu texto, cita de otros
archivos **solo** etiquetas garantizadas (o `cap:`). Las etiquetas nuevas llevan el prefijo de su tipo (`sec:`,
`tab:`, `fig:`, `eq:`).

### Capítulo II (`capitulo2.tex`, 12 p.)
Mismas nueve secciones, más cortas: solo la teoría que la tesis usa. Garantizadas: `cap:teoria`,
`sec:teoria-simulacion`, `sec:teoria-control`, `sec:teoria-metricas`, `sec:rl`, `sec:tabular`, `sec:dqn`, `sec:ppo`,
`sec:marl`, `sec:evaluacion`, `eq:retraso-total`, `eq:gae`, `eq:ppo-clip`, `eq:q-learning`, `eq:sarsa`,
`eq:double-dqn`. Conserva al inicio el `\renewcommand{\theequation}`.

### Capítulo III (`capitulo3.tex`, 22 p.)
1. Visión general del método (2 p.): `sec:vision-general`, `fig:arquitectura`, `tab:pipeline`. Los cuatro diagramas
   de flujo de U1 a U4 salen (queda la figura de arquitectura).
2. Escenarios y casos (3 p.): `sec:escenarios`, la figura de las tres redes, `tab:plan2-casos`, `tab:demanda-flujos`,
   `fig:corredor-periodos`, `fig:giro-izquierda`. Aquí se dice qué son las llegadas regulares y las aleatorias.
3. Formulación como problema de aprendizaje por refuerzo (4 p.): `sec:formulacion`, `eq:recompensa-u4`,
   `eq:recompensa`.
4. Coordinación entre semáforos (3 p.): `sec:u4`, `tab:obs-u4`.
5. Modelos comparados (2.5 p.): `sec:modelos`, `tab:plan2-modelos`. Incluye, en breve, IPPO con mensajes corregido y
   el modelo completo (detalle en los Anexos G y H).
6. Medición del desempeño (2 p.): `sec:u3`. Retraso y retraso total.
7. Diseño de la evaluación (5.5 p.): `sec:plan2` y `sec:plan` en el título de la sección.
   - Casos: `sec:plan-casos`.
   - Los dos estudios: etiqueta nueva `sec:diseno-segundo`, con la tabla `tab:plan3-cambia` (qué cambia del primer
     estudio al segundo; está hoy en el Anexo H y pasa aquí).
   - Protocolo y semillas: `sec:protocolo`, `tab:plan2-semillas`.
   - Estadística: `sec:estadistica`, `eq:delta`, `eq:media-geometrica`.
   - Regla de veredicto y convergencia: `sec:veredicto`.
   - Análisis complementarios (1 p.): `sec:analisis-complementarios`, `sec:diseno-robustez`, `sec:plan-demanda`,
     `tab:plan-demanda-niveles`, `tab:plan-comparaciones`. Solo qué son y dónde está su detalle (Anexos F y G).
Garantizadas además: `cap:metodologia`.

### Capítulo IV (`capitulo4.tex`, 12 p.) y Anexo I nuevo (`anexo_i_implementacion.tex`, 5 p.)
1. Entorno (0.5 p.): `sec:entorno`, `tab:hw`.
2. Construcción de los escenarios (2 p.): `sec:construccion`, `sec:calibracion` (un párrafo; las tablas van al Anexo I).
3. Programas de referencia (2.5 p.): `sec:referencias-fijas`, `tab:plan2-fijo`, `sec:programa-trivial`; en breve, cómo
   se ajustan el fijo al segundo y el actuado del segundo estudio.
4. Bucle de entrenamiento (1.5 p.): `sec:bucle`.
5. Implementación de los aprendices (2.5 p.): `sec:aprendices`, `tab:plan2-hiper`.
6. Ejecución y costo (1.5 p.): `sec:ejecucion`, `tab:plan2-costo`; incluye el tamaño del segundo estudio.
7. Reproducibilidad (1 p.).
Anexo I recibe, resumido: calibración de la demanda (`tab:red-alta-factor`, `tab:malla3-alta-factor`), lo que enseñó
la prueba de humo (`sec:humo`), el término de spillback que no se activa (`sec:spill-vecinos`), la medición más
estricta en la implementación (`sec:remedicion`) y P6 y el barrido de demanda (`sec:p6-demanda`). Sigue el formato de
los Anexos F y G (título `\section*{Anexo I. ...}`, contadores `I.n`). Garantizadas además: `cap:implementacion`.
No cites `fig:flujo-u1` a `fig:flujo-u4`: desaparecen.

### Capítulo V (`capitulo5.tex`, 25 p.)
1. Qué se pregunta y cómo se lee (2.5 p.): `sec:plan-resultados`, `tab:plan-resultados`, `tab:veredictos`. La
   pregunta, los seis casos, las referencias, la regla de veredicto y los tres pasos.
2. **Resultado central: tráfico aleatorio y un fijo ajustado al segundo (6 p.):** `sec:segundo-estudio` y
   `sec:resultado-central`. Tabla `tab:plan3-central` (`\input{secciones/tablas/plan3_central}`), figura
   `fig:plan3-cambio` (`fig_plan3_cambio.pdf`) y figura `fig:plan3-retraso` (`fig_plan3_retraso.pdf`: retraso total
   por vehículo con el fijo ajustado al segundo, el actuado ajustado y el modelo, por caso). Respuesta, lectura por
   caso, frente a las otras referencias, por qué no gana en tres casos, sensibilidad. Detalle en el Anexo H.
3. El camino previo: llegadas regulares (5 p.): `sec:resultado-principal` (`tab:resultado-principal`,
   `fig:plan2-mejora-caso`, `tab:metas`), `sec:esperado-obtenido`, `sec:robustez` (`tab:robustez-ippo`).
4. Qué explica el resultado (5 p.): `sec:piezas` (`tab:piezas`), `sec:efecto-demanda` (`fig:efecto-demanda`,
   `tab:efecto-demanda`), `sec:diag-corredor` (un párrafo; detalle en el Anexo G), `sec:ejecucion-indicadores`
   (`fig:plan2-convergencia`).
5. Comparación con otros trabajos (2 p.): `sec:comparacion-literatura`, `tab:comparacion-referencia`.
6. Alcance y límites (3 p.): `sec:plan-conclusion`, `sec:alcance`, `sec:limites`. Con una tabla nueva
   `tab:afirmaciones`: qué se afirma, con qué evidencia y dónde está.
Garantizadas además: `cap:resultados`.

### Conclusiones (`conclusiones.tex`, 4 p.) y recomendaciones (`recomendaciones.tex`, 2 p.)
Conclusiones, cuatro bloques:
1. **Respuesta** (media página, tres cifras).
2. **Por objetivo** (una tabla o lista: objetivo, cumplido / en parte / no, y la medida que lo sostiene). Los
   objetivos son los de `introduccion.tex`: general, U1, U2, U3, U4 y reproducibilidad.
3. **¿Los modelos están bien construidos?** Lo que lo sostiene (resultados reproducibles; dos tandas independientes
   que coinciden en los 19 casos; cuántos entrenamientos se estabilizaron; controles que delatan falsos positivos,
   como el ciclo mínimo; defectos del entrenamiento encontrados y corregidos, con su efecto medido) y lo que no
   (decide cada 5 s y no puede dar desfases de 1 s; entrenamientos que no se estabilizan; el canal de mensajes es
   perfecto).
4. **Alcance y límites:** dónde funciona, dónde no y por qué, con cifras; qué no se puede afirmar (Lima, datos
   reales, canal imperfecto, otra demanda).
Recomendaciones: cinco o seis, cada una en tres o cuatro líneas, ordenadas por utilidad.

### Anexos
- A (`anexos.tex`): de 20 tablas a unas 5 (retraso y cambio por caso y modelo; resumen en un número; veredicto y
  entrenamientos de IPPO con mensajes; una tabla compacta con los veredictos de los demás modelos, si no repite la
  matriz del Cap. V). Las demás tablas quedan en el repositorio. B se conserva y suma los programas del segundo
  estudio.
- C, F y G: mismos contenidos, resumidos; conservar las tablas y figuras que el cuerpo cita.

### Etiquetas garantizadas de los anexos (las únicas de anexos que el cuerpo puede citar)
- Anexo A: `tab:plan2-resumen`, `tab:plan2-numero-unico`, `tab:plan2-anova`.
- Anexo F: `tab:robustez-fijo`, `fig:plan2-demanda`, `tab:plan2-demanda`.
- Anexo H: `tab:plan3-aleatorias`, `tab:plan3-regulares`, `tab:plan3-referencias`, `tab:plan3-referencias-cifras`,
  `tab:plan3-promocion`, `tab:plan3-hipotesis`, `tab:plan3-sensibilidad`, `tab:plan3-margen`, `tab:plan3-esperado`.
- Los demás anexos se citan por su nombre: "Anexo~C", "Anexo~G", "Anexo~I".

## 7. Reglas de trabajo

- Trabajas en `c:\Users\GAMER\Documents\demo_rl_semaforo\demo_rl` (rama `tesis-plan3`). Edita **solo** tus archivos.
- Lee antes las convenciones de LaTeX de `demo_rl/.claude/skills/escribir-tesis/SKILL.md` (secciones 0, 3 y 5).
- Escribe con las herramientas de edición de archivos, no con `sed` ni con heredocs de la consola (se comen las
  barras invertidas).
- Conserva junto a cada cifra su comentario `% fuente:` (el que ya tiene o uno equivalente). Los comentarios que
  cuentan la historia de ediciones anteriores pueden salir.
- **No compiles** (`compilar.py` lo corre quien integra: varias compilaciones a la vez se pisan). Puedes correr
  `python TESIS/validar_tex.py`; mira solo los errores de tus archivos.
- No corras simulaciones, ni `veredicto.py`, `consolidar.py`, `sintesis_plan.py` ni nada de `plan2/` o `plan3/`. No
  hagas commits ni toques git.
- Al terminar, informa: palabras de cada archivo antes y después, etiquetas garantizadas que quitaste o cambiaste,
  tablas y figuras que salieron, y cualquier dato que te faltó o duda.
