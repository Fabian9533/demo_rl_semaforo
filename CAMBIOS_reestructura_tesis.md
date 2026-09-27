# Changelog de la reestructura de la tesis (27.09.2026)

Documento para revisar con calma lo que se eliminó, movió o reescribió en `TESIS/` y por qué. Cada afirmación se puede comprobar con `git diff 7bd8685 HEAD -- TESIS`, con `git show <commit>` o con los reportes de trabajo (auditoría, edición, verificación y corrección). Las líneas que se citan en las secciones 1 a 10 son las de `TESIS/` en el commit `2ab0d04`, salvo la lista de TODO de la sección 8, que está al día con la segunda parte (sección 11: diagramas).

## 1. Resumen

Se auditó la tesis completa y se reestructuró en el orden marco teórico, metodología, implementación y resultados. Después, una verificación adversarial contrastó cada capítulo con el original, el código y los CSV, y las correcciones se aplicaron en commits aparte. El trabajo está en la rama `reestructura-tesis`: 18 commits, de `cc2a353` al que agrega este changelog, sobre `7bd8685` (la punta de `main`, que no se tocó). El PDF pasa de 290 a 247 páginas (253 tras agregar los cinco diagramas de la sección 11). `python TESIS/compilar.py` compila sin errores ni referencias o citas sin resolver (el overfull mayor es de 5.6 pt), y `python TESIS/validar_tex.py` da 0 errores y 33 avisos, todos comentarios `TODO(reestructura)`: huecos que piden una fuente, un dato o un diagrama y que no se rellenaron con contenido propio.

Los cambios más importantes:
- El antiguo Capítulo III (`capitulo4.tex`, 1967 líneas) se partió en un Capítulo III de metodología (`capitulo3.tex`, nuevo) y un Capítulo IV de implementación (`capitulo4.tex`). El manual de OpenStreetMap pasó al Anexo D.
- La fase exploratoria salió de Resultados y quedó condensada en el Anexo C. Se eliminaron 19 tablas generadas y 14 figuras exploratorias. El Capítulo V trata solo el plan de pruebas, con dos tablas de resumen nuevas (`tab:plan2-resumen`, `tab:plan2-metas`).
- El Capítulo II se reescribió como marco teórico completo, con 13 ecuaciones numeradas y una tabla de métricas. Se eliminaron la sección de arquitectura desactualizada (con `Diagrama.png`) y la de resultados esperados.
- La notación y los términos se unificaron en todo el documento (J_i, L_i, ℓ, q_ℓ, K_ℓ; ε frente a ε_clip; Δ_f y Δ_a; checkpoint, política publicada, base publicada y celda). Se corrigieron las afirmaciones desactualizadas: SARSA, DQN y MAPPO "pendientes" y la sección "Estado de avance".
- Segunda parte (sección 11): la arquitectura modular y los flujos de U1, U2, U3 y U4 se rehicieron en TikZ a partir del código y se integraron en el Cap. III.
- Las conclusiones pasaron de 14 a 6, ordenadas por objetivo (U1 a U4, reproducibilidad y alcance), más dos párrafos finales sobre la fase exploratoria.

## 2. Autorización y alcance

El autor autorizó por escrito aplicar cambios sin pedir aprobación, incluidas las zonas protegidas. La regla que se siguió en metas y objetivos fue corregir solo lo desactualizado.

Zonas protegidas que se tocaron:
- Resumen: el párrafo 1 y las palabras clave se conservan; los párrafos 2 y 3 del original pasan a ser cuatro (2 a 5), todos reescritos.
- Abstract: los tres párrafos del original pasan a cinco, todos reescritos como traducción fiel del resumen nuevo (también el primero). El título y las keywords no cambian.
- Introducción: según el plan, en la introducción solo son zona protegida las metas y los objetivos. En las metas solo cambió el ítem de throughput, que perdió los resultados exploratorios ("escenarios cuya demanda supere" pasa a "casos cuya demanda supera"), y el guion de "25–40" pasó a `--` (en LaTeX se imprime igual). Se reescribieron las dos notas que siguen a las metas y a los objetivos. El resto de la introducción no es zona protegida; sus cambios están en la sección 4.
- Capítulo I completo (ver sección 4).
- Captions: muchos se reescribieron (ver sección 5).

Lo que no cambió:
- El objetivo general y los cinco objetivos específicos. Se comprobó con diff que el bloque de objetivos es idéntico a `7bd8685`. La edición había reescrito el objetivo U4 ("fase actual, colas/salidas previstas") con la lista de mensajes implementada; la verificación lo restauró porque el objetivo no estaba desactualizado. La diferencia con lo implementado se explica en la nota que sigue a los objetivos.
- Las metas numéricas: 25–40 % de retraso, 20 % de colas, 10 % de throughput y 5 % de CO2.
- El "Problema central", que sigue redactado como en el original.
- `tesisutec.cls`, los paquetes de `main.tex`, `referencias.bib`, las tablas generadas de `TESIS/secciones/tablas/` y los listados de `TESIS/codigo/`.

## 3. Índice antes y después

Numeración antes: I = `capitulo1.tex`, II = `capitulo2.tex`, III = `capitulo4.tex` y IV = `capitulo5.tex`; `capitulo3.tex` no existía en `7bd8685` (un `capitulo3.tex` vacío se versionó en `083aa84`, y `9fc0f8a` lo movió a `respaldo_tesis/` el 06.09). Numeración después: `capituloN.tex` es el Capítulo N (I a V), y `main.tex` solo agrega `\input{secciones/capitulo3}`.

En la columna "Antes" los capítulos llevan la numeración antigua: "Cap. III" es `capitulo4.tex` y "Cap. IV" es `capitulo5.tex`.

| Antes (7bd8685, numeración antigua) | Después (numeración nueva) | Qué pasó |
|---|---|---|
| Resumen, Abstract | mismo lugar | Al día con el plan de pruebas |
| Introducción: secciones de la presentación a las métricas | Introducción, mismas secciones | Al día; la arquitectura modular pasa antes de los objetivos |
| Introducción: Estado de avance | eliminada | Pendientes vigentes en "No incluido"; se agrega "Organización del documento" |
| Cap. I Estado del arte | Cap. I | Misma estructura, al día; implicancias condensadas |
| Cap. II: Arquitectura teórica del sistema (fig:diseno) | eliminada | U1-U4 viven en la Introducción y en el Cap. III |
| Cap. II: Definiciones y conceptos fundamentales | Cap. II, secciones 1 a 9 | Reescrito y ampliado con ecuaciones |
| Cap. II: Relación con objetivos y resultados esperados | eliminada | Narraba resultados exploratorios |
| Cap. III (`capitulo4.tex`): Alcance y unidades; Resumen de las unidades | Cap. III `sec:vision-general` + `tab:pipeline` | Fusionadas |
| Cap. III: Requisitos de hardware | Cap. IV `sec:entorno` (`tab:hw`) | Movido |
| Cap. III: Instalación de SUMO; Limpieza OSM; Importación desde OSM | Anexo D | Condensado |
| Cap. III: Diagrama de flujo del módulo U1 (fig:flow-u1) | eliminado; rehecho como Figura 3.2 (`fig:flujo-u1`) | Ver sección 11 |
| Cap. III: Generación y ejecución del escenario | Cap. IV `sec:construccion` (flujos, configuración); Anexo D (randomTrips) | Tutorial eliminado |
| Cap. III: Escenarios sintéticos de prueba | Cap. III `sec:escenarios` (P1-P5) | cruce y cruce2 y la historia del fijo pasan al Anexo C |
| Cap. III: U2, formulación | Cap. III `sec:formulacion` | Reescrita |
| Cap. III: U2, interfaz con SUMO y ciclo de entrenamiento | Cap. IV `sec:bucle` | Reescrito según `rl_corredor.py` |
| Cap. III: U2, Algoritmos recomendados | eliminada | Lo útil pasa a `sec:modelos` |
| Cap. III: U2, Actualización de los valores Q | Cap. II `sec:tabular` (`eq:q-learning`, `eq:sarsa`) | Movida |
| Cap. III: U2, Diagrama de flujo (fig:flow-u2) | eliminado; rehecho como Figura 3.3 (`fig:flujo-u2`) | Ver sección 11 |
| Cap. III: U3 (entre U2 y U4) | Cap. III `sec:u3`, después de U4 y de `sec:modelos` | Reescrito y reubicado |
| Cap. III: U4 (vecinos, observación, recompensa y variantes) | Cap. III `sec:u4`; la recompensa, a `sec:formulacion` | Reescrito |
| Cap. III: U4, IPPO con pesos compartidos | Cap. IV `sec:aprendices` | `tab:hiper-ippo` fusionada |
| Cap. III: U4, Lo que enseñó la prueba de humo | Cap. IV `sec:humo` | Movido |
| Cap. III: U4, Escenario de estrés corredor_alta | Cap. IV `sec:calibracion` | Movido |
| Cap. III: Plan de pruebas (introducción, objetivo, casos) | Cap. III `sec:plan2` | `tab:plan2-casos` fusionada con `tab:escenarios` |
| Cap. III: Plan, P4 calibración y P5 construcción de malla3 | Cap. IV `sec:calibracion` y `sec:construccion` | Movido |
| Cap. III: Plan, Modelos | Cap. III `sec:modelos` (diseño); Cap. IV `sec:aprendices` (DQN, MAPPO, hiperparámetros) | Dividido |
| Cap. III: Plan, Protocolo común | Cap. III `sec:protocolo`; el resultado del barrido, a Cap. IV `sec:referencias-fijas` | Dividido |
| Cap. III: Plan, Métricas de salida | Cap. III `sec:estadistica` (los retornos, a `sec:u3`) | Reescrito, con `eq:delta` |
| Cap. III: Plan, Regla de veredicto | Cap. III `sec:veredicto` | Reescrita |
| Cap. III: Plan, Ejecución y costo de cómputo | Cap. IV `sec:ejecucion` | Bitácora condensada |
| Cap. III: Plan, Fase exploratoria previa | Cap. III `sec:plan2` (un párrafo) y Anexo C | Condensada |
| Cap. III: Plan, Reproducibilidad | Cap. IV `sec:reproducibilidad` | Movida |
| Cap. IV Resultados (`capitulo5.tex`): plan de pruebas | Cap. V | Nuevo orden: global, caso, modelo, convergencia, alcance |
| Cap. IV: "Qué es alcanzable para P6 y P7" | Recomendaciones, "Presupuestar P6 y P7" | Movido |
| Cap. IV: fase exploratoria (resumen, E1-E4, U4, E6, niveles N0-N6, Lectura conjunta, Limitaciones) | Anexo C | Condensada; niveles y limitaciones eliminados |
| Conclusiones 1 a 14 | Conclusiones 1 a 6 + dos párrafos finales | Reordenadas por objetivo |
| Recomendaciones | Recomendaciones | Sin cambios de fondo; Lima pasa al primer lugar del trabajo siguiente |
| Anexo A: tablas completas por episodio (exploratorias) | eliminado | Protocolo reemplazado; no se citaban |
| Anexo A: "Plan de pruebas v2: tablas completas" | Anexo A, "Tablas completas del plan de pruebas" | Promovido a anexo propio |
| Anexo B: código fuente | Anexo B | Reordenado según el pipeline |
| (no existía) | Anexo C, fase exploratoria; Anexo D, importación desde OSM | Nuevos |

## 4. Cambios por capítulo

Cómo leer esta sección:
- Cada entrada describe el cambio neto frente a `7bd8685`, salvo que se indique otra cosa.
- "En la verificación" o "Corregido en la verificación" marca lo que cambió en los commits de verificación (`746a0c3` a `cb0234a`) sobre el texto de la edición. Muchas de esas correcciones deshacen algo que la edición había introducido.
- "[sin cambio neto]" marca algo que la edición introdujo y la verificación retiró, o que la edición quitó y la verificación repuso: frente a `7bd8685` no hay cambio. Se deja para que se entienda el historial de commits.
- "De la propuesta del plan" marca texto que proponía el plan maestro y que nunca llegó a la tesis.
- Cada capítulo abre con dos o tres líneas sobre lo que más importa revisar.

### Resumen y abstract (`resumen.tex`, `abstract.tex`)

Lo principal: el resumen deja la fase exploratoria y describe el plan de pruebas (casos P1-P5, modelos, protocolo, veredicto y resultados); el abstract pasa a ser su traducción. Se conservan el párrafo 1 del resumen, el título del abstract y las palabras clave.

Eliminado
- Los cinco escenarios exploratorios y las diez semillas del resumen, y SARSA, DQN y MAPPO como trabajo futuro. Por qué: describían la fase exploratoria y algoritmos que ya están implementados.
- Las cifras exploratorias (6.4 %, 35 %, 6 frente a 38 %, 21 %, "sin llegar a bloquear el enlace", +5 % frente al actuado) y, en el abstract, "37 % under double demand". Por qué: los resultados vigentes son los del plan de pruebas congelado.
- La lista de métricas secundarias. Por qué: mantener el resumen en el límite de unas 450 palabras que usó la edición (según su reporte). Las cifras de colas (−41.3 y −29.0 %) quedan en un comentario `% fuente`.

De la propuesta del plan (no llegó a la tesis; sin cambio frente a `7bd8685`)
- La frase del actuado (−19.8 % en P2, +21.8 % en P5) se omitió por el mismo límite de palabras.
- La propuesta decía "la de colas solo en P3 y P5". Sin sujeto era falsa, porque el actuado reduce las colas un 27.72 % en P4. Se escribió desde el principio con sujeto: "con IPPO con mensajes, la de colas se cumple solo en P3 y P5". La verificación la dejó en "IPPO con mensajes entre vecinos cumple la de colas solo en P3 y P5".

Reescrito
- Párrafo 2: el pipeline U1-U4 y los cinco casos P1-P5 de dificultad creciente, con el cruce de Lima importado de OSM pero sin limpiar. Por qué: estaba desactualizado.
- Párrafo 3: los modelos comparados, el protocolo en dos frases (200 episodios, tres bases, política de mejor validación en dos semillas propias, base mediana, treinta semillas de evaluación distintas de las de validación), la métrica primaria y el veredicto prefijado, incluido "pendiente". Por qué: el resumen debía describir el plan. La verificación pidió dejar claro que la selección no usa las semillas de evaluación, porque el abstract podía leerse así.
- Párrafos 4 y 5: los resultados del plan (IPPO con mensajes entre vecinos: −6.8, −23.3, −8.8 y −3.6 % en P1 a P4, empate en P5 y entre 3.6 y 16.4 % mejor que el actuado; MAPPO con el mismo veredicto donde el suyo es firme y sin convergencia en P3 y P4; Double DQN por detrás; tabulares y ablación) y, en párrafo aparte, las metas. Fuente: `plan2/veredicto_congelado_0355.md`.
- Abstract: traducción fiel del resumen nuevo. El párrafo 1 ya no habla de tiempos de viaje, emisiones ni movilidad, que el resumen no menciona, y "pre-registered" pasa a "predefined verdict rule".

Corregido en la verificación
- La enumeración de modelos se reordenó para que la glosa "un PPO independiente por semáforo" no se lea como un modelo más. Por qué: con la glosa entre comas se contaba un modelo de más.
- Se agregó "salvo una ablación de Q-learning con recompensa de colas". Por qué: "todos los aprendices usan la recompensa de retraso" contradecía `tab:plan2-modelos`.

### Introducción (`introduccion.tex`)

Lo principal: sale "Estado de avance"; la arquitectura modular pasa antes de los objetivos; se agregan la pregunta de investigación y "Organización del documento". Los objetivos no cambian y en las metas solo cambia el ítem de throughput. La frase "sin GPU" de las herramientas se corrigió al final (`2ab0d04`).

Eliminado
- "Estado de avance" (Completado, En curso, Pendiente). Por qué: estaba al 06.09 y duplicaba el alcance. Sus pendientes vigentes pasaron a "No incluido en esta etapa".
- En la meta de throughput, la lectura exploratoria ("cuatro escenarios de demanda nominal", "ningún control se acerca al 10 %"). Por qué: eran resultados en una zona de metas; queda solo cuándo es evaluable.
- En el alcance, los escenarios exploratorios como casos de la etapa, y en "No incluido", SARSA, DQN y MAPPO. Por qué: ya están implementados.
- En herramientas, `stable-baselines3` ("para DQN, pendiente, se evaluará"; no se usa) y Mann–Whitney (`consolidar.py` no lo calcula).
- En métricas, la lista con definiciones y el ítem "Recompensa por decisión y curvas de convergencia". Por qué: las definiciones viven en el Cap. II (`tab:metricas`).

Movido
- La arquitectura modular pasa antes de "Objetivos de investigación", condensada en un párrafo. Por qué: las siglas U1-U4 se usaban antes de definirse. Se glosan TraCI y las acciones, y el aporte de U4 se mide con IPPO local frente a IPPO vecinos (antes: tabulares frente a IPPO, que no aísla los mensajes).

Reescrito
- Presentación: "una intersección o pequeño corredor" pasa a "una intersección, un corredor o una red pequeña". Por qué: el plan incluye una malla de nueve cruces.
- Alcance de esta etapa: los casos P1-P5; todos los algoritmos con el mismo protocolo y la ablación `ql_colas`; la glosa del fijo tuneado y de los verdes de 10 y 60 s; los casos de un cruce, solo como fase exploratoria y prueba de humo.
- No incluido: el cruce de Lima (importado de OSM el 01.12.2025, sin limpiar ni evaluar, Anexo D), P6 y P7, el canal imperfecto (evaluado solo en la fase exploratoria) y las llegadas de Poisson.
- Áreas de investigación y herramientas: `netedit` y OpenStreetMap pasan a "solo intervienen en el cruce real, importado en crudo y pendiente de limpieza (Anexo D)". Por qué: no se usaron en ningún caso evaluado. IPPO, Double DQN y MAPPO figuran en PyTorch puro, y la estadística queda en `scipy` (IC y Wilcoxon pareado) y `numpy` (bootstrap pareado).
- Métricas de evaluación: tres párrafos (métricas, retornos como diagnóstico, veredicto), con remisión a los Cap. II y III.
- La nota que sigue a las metas ("Estas metas son el objetivo del trabajo completo...") se conserva y se amplía: distingue el umbral del 5 % del veredicto de las metas, más exigentes, y dice qué metas contrasta el Cap. V. Antes decía que el Cap. V reporta cuánto las cumple "cada uno de los dos algoritmos implementados".
- La nota que sigue a los objetivos ("De estos objetivos, esta fase ejecuta los cuatro...") pasa de un párrafo a dos: lo que ejecuta cada unidad, qué modelos usan mensajes, que IPPO spill repite a vecinos en P3-P5, que seis de las cuarenta combinaciones quedan pendientes y que los mensajes no incluyen una predicción de salidas. Antes decía que faltaban SARSA, DQN y MAPPO.
- "Fase" pasa a "etapa" cuando se habla de la etapa del proyecto. "Fase exploratoria" nombra a la etapa previa y "fase" queda solo para la fase semafórica.

Agregado
- Un segundo párrafo de presentación con las dos etapas: fase exploratoria (Anexo C) y plan de siete casos, de los que se ejecutan cinco.
- Al final del primer párrafo de presentación: "Los conceptos de control semafórico y de aprendizaje por refuerzo que se mencionan en esta introducción se definen en el Capítulo II".
- En la formulación, la pregunta de investigación del plan, la definición de fijo tuneado y actuado y una frase puente hacia los casos sintéticos. Fuente: la sección del plan del Cap. III y el texto original de `sec:escenarios`.
- En herramientas: "Los entrenamientos corren con un hilo cada uno y sin usar la GPU, en el equipo de la Tabla `tab:hw`" (la edición había escrito "sin GPU", que chocaba con el Cap. IV; corregido en `2ab0d04`).
- "Organización del documento", con los Capítulos I a V y los Anexos A a D.
- Citas: `SUMO_TLS_Actuated` (actuado por detectores) y `Chavez2023`, `Chakrabarti2022` en la justificación. Las citas FHWA/HCM que la edición había puesto en la situación problemática se quitaron en la verificación, porque esas fuentes no respaldan esa afirmación; en su lugar quedó un TODO.
- Tres TODO (líneas 6, 14 y 31).

### Capítulo I, Estado del arte (`capitulo1.tex`)

Lo principal: lo que el capítulo dice de esta tesis se puso al día con el plan (algoritmos, controles de referencia, rigor, Lima); cada trabajo queda en su subsección y `tab:relacionados` suma la fila "Esta tesis". Revisar la afirmación de `sec:implicancias` que las conclusiones eliminaron (sección 8).

Eliminado
- En "Implicancias", R_global (no existe en el código), "MAPPO queda pendiente", la mensajería con latencia y pérdida, la lista de métricas de corredor y la motivación de U4 con un resultado exploratorio. Por qué: estaban desactualizados, y el detalle de U4 vive en el Cap. III.
- La lista antigua "implementa / están implementados", con SARSA y DQN como trabajo siguiente. Por qué: estaba desactualizada.
- En "Modelado de la realidad", que la tesis integra datos reales de aforos ("Esta tesis busca combinar ambas fortalezas, integrando datos reales de aforos") pasa a "se propuso combinar ambas fortalezas". Por qué: los datos observados están fuera del alcance de esta etapa.
- En "Rigor experimental", Mann–Whitney y el tamaño de efecto. Por qué: `consolidar.py` no los calcula.
- El resultado de coordinación exploratorio (corredor y red de la fase anterior). Por qué: se reemplazó por el del plan.
- Las negritas decorativas y las cajas vacías que generaban los `\\` dentro de los campos de cada trabajo.

Movido
- Revisión crítica: "Comparación algorítmica" pasa antes de "Línea base", que se renombra "Controles de referencia". Por qué: los modelos se definen antes de la frase de resultados que los nombra.

Reescrito
- Panorama: la definición de agente único (un agente controla una sola intersección) frente a multiagente (uno por intersección en la misma red). Por qué: antes se definían casi igual.
- Los tres trabajos: cada campo es un párrafo (`\noindent\textbf{Campo.}`) bajo una `\subsection` numerada con título corto. Se desarrollan las siglas (DQN, Deep RL, OD, A2C, AR, RNN, RMSE, MAE, MAPE, R², UAQ).
- Uniandes: la frase de espera frente a retraso pasa a su propio párrafo, con remisión al Cap. V. La limitación queda "no reporta intervalos de confianza ni pruebas de significancia". La edición había escrito "carece de análisis estadístico", y la verificación lo devolvió al sentido del original, que decía "análisis estadístico robusto".
- Comparación algorítmica al día: Q-learning y SARSA; IPPO en tres variantes, Double DQN y MAPPO; A2C no se implementó (TODO). Queda en tres párrafos.
- Controles de referencia: el actuado con 10 a 60 s y el fijo tuneado. Por qué: la frase de resultados se reescribió con `veredicto_congelado_0355.md` (antes usaba los cinco escenarios exploratorios).
- Rigor experimental: lo que hace el plan (bases, validación 999/1999, evaluación 1001-1030, bootstrap pareado y Wilcoxon).
- Transferencia a Lima: se separa lo hecho de lo pendiente (importación cruda del 01.12.2025, Anexo D).
- Implicancias: una lista al día y dos párrafos que conectan cada lección con una decisión. "Se atienden" pasa a "se atienden en parte", con A2C y los datos reales fuera. La lección de UAQ sobre tiempos de viaje se atiende "solo en parte", porque el Cap. V no los analiza.
- Aporte U4: un párrafo en lugar de la lista de cinco componentes.

Agregado
- Los labels `cap:estado-arte`, `sec:relacionados`, `sec:revision-critica` y `sec:implicancias`.
- Un párrafo de RL multiagente con `Yu2021_MAPPO`.
- Frases de entrada en "Revisión crítica" y en "Síntesis comparativa".
- Comentarios `% fuente`.
- Cuatro TODO (líneas 11, 70, 111 y 124).
- En `tab:relacionados`, ver la sección 5.

Restaurado
- La frase de Sistemas Distribuidos. La edición la había quitado por irrelevante; la verificación la repuso, reformulada, porque era la única mención del tópico y la propuesta del autor la conservaba.

### Capítulo II, Marco teórico (`capitulo2.tex`, de 64 a 619 líneas)

Lo principal: es el mayor cambio de contenido de la reestructura. Todo lo agregado son definiciones con cita a obras que ya estaban en el `.bib`, o con un TODO donde falta la fuente. Revisar que cada cita respalde lo que se le atribuye y los 15 TODO (sección 8).

Eliminado
- La sección "Arquitectura teórica del sistema (visión por módulos)", con `fig:diseno` (`Diagrama.png`) y los párrafos U1 a U4. Por qué: la figura dibuja componentes que no existen (Azure, Google Maps, matrices OD, estados de densidad) y omite la evaluación. U1-U4 se describen en la Introducción y en el Cap. III.
- La sección "Relación con objetivos y resultados esperados". Por qué: narraba resultados de la fase exploratoria ("cumple la meta en el cruce...") que el plan contradice.
- Frases desactualizadas: "quedan pendientes SARSA y DQN", "SARSA queda como comparación pendiente", "MAPPO queda como extensión", "el módulo U2 usa agentes tabulares en corredor y red".
- "Tamaño de efecto" (no se calcula) y la frase de versiones de software, que vive en el Cap. IV.
- La cita `SB3_Docs`, porque SB3 no se usa. Como nadie más la cita, esa entrada sale de la bibliografía impresa, pero sigue en `referencias.bib`.
- El umbral operativo de spillback (90 % de las plazas). Por qué: es metodología (Cap. III).
- "PPO es *policy-based*". Por qué: PPO es actor-crítico.

Movido
- Desde el `capitulo4.tex` original: las ecuaciones de Q-learning y SARSA ("Actualización de los valores Q y ejemplo de pseudocódigo", que no tenía pseudocódigo), ahora `eq:q-learning` y `eq:sarsa`, y el `\renewcommand{\theequation}` del inicio.
- El argumento de que los episodios no son réplicas independientes pasa a `sec:evaluacion`.
- Las definiciones de métricas pasan a `tab:metricas`.

Agregado (definiciones apoyadas en fuentes que ya estaban en el `.bib`; donde faltaba fuente quedó un TODO)
- `sec:teoria-simulacion`: SUMO (grafo dirigido, `tripinfo`, σ y factor de velocidad como fuente de aleatoriedad) y TraCI.
- `sec:teoria-control`: fase, ámbar, programa, ciclo, reparto, desfase, verdes mínimo y máximo, flujo de saturación, capacidad y grado de saturación. El fijo y el actuado van en párrafos separados (el actuado, con la regla de hueco entre vehículos); la onda verde y el spillback se definen como conceptos.
- `sec:teoria-metricas` con `tab:metricas`: el throughput se enlaza con la capacidad y se precisa control delay frente a timeLoss.
- `sec:rl`: el MDP como tupla, la propiedad de Markov, `eq:retorno` (con el horizonte 1/(1−γ)), `eq:valor`, `eq:bellman`, la regla ε-greedy con decaimiento y la política congelada generalizada a las redes.
- `sec:tabular`: `eq:td`, `eq:q-learning`, `eq:sarsa`, las condiciones de convergencia de Q-learning (distintas de la convergencia operativa) y la discretización.
- `sec:dqn`: redes como aproximadores, `eq:dqn` (red objetivo θ⁻, memoria de repetición, terminal frente a truncado) y `eq:double-dqn`.
- `sec:ppo`: `eq:gradiente-politica`, ventaja y actor-crítico, `eq:gae`, `eq:ppo-razon` (ρ_t), `eq:ppo-clip` (ε_clip) y `eq:ppo-total`; la KL como diagnóstico.
- `sec:marl`: Dec-POMDP (Yu et al.), estado frente a observación, recompensas locales, pesos compartidos, IPPO frente a MAPPO, entrenamiento centralizado con ejecución descentralizada y comunicación entre vecinos.
- `sec:evaluacion`: unidad experimental, semillas disjuntas, selección por validación, convergencia operativa, diseño pareado, IC con t, bootstrap y Wilcoxon, y por qué pueden discrepar.
- 15 TODO: 14 de fuentes o de verificación de fuentes y 1 de diagrama (línea 14) (ver sección 8).

Reescrito
- La apertura: qué conceptos se presentan, en qué orden y qué parte del método usa cada uno. La verificación la dividió en frases cortas.
- Las remisiones escritas a mano ("Capítulo III") pasan a `\ref{cap:metodologia}` o `\ref{cap:implementacion}`.

Corregido en la verificación (cada punto, con lo que se contrastó)
- La política tabular congelada no es determinista: un empate se resuelve al azar con un generador sembrado. Por qué: `mejor_accion` de `rl_corredor.py` desempata con `random.randint`.
- Los retornos y la recompensa de colas se registran con cualquier control, no solo con los aprendices. Por qué: así lo dicen `plan2/ESPEC.md` (sección 5) y `evaluar.py`.
- La recompensa local de spill incluye los enlaces de salida hacia el vecino. Por qué: `rl_ippo.termino_spill` suma sobre esos enlaces, y el texto contradecía otra frase del mismo capítulo.
- Se quitó `FHWA_Timing_Manual_Chapter3` de las citas de desfase y onda verde; queda `HCM2000_or_2010` con TODO. Por qué: ese capítulo de la FHWA no trata esos temas.
- La pérdida combinada de PPO se pide cuando actor y crítico comparten parámetros, y el código usa 1/2 del error cuadrático. Por qué: es la condición de Schulman et al. (sec. 5), y así lo calculan `rl_ippo.py` y `rl_mappo.py`.
- Se quitaron los arranques de lo que timeLoss "agrega" al control delay. Por qué: el control delay del HCM ya incluye la demora de aceleración.
- El minilote se atribuye a Mnih y a Schulman. Por qué: Sutton y Barto presentan el descenso de gradiente ejemplo a ejemplo.
- La discrepancia entre IC y Wilcoxon ocurre en dos celdas: P5 con IPPO vecinos frente al fijo y P2 con MAPPO frente al actuado. Por qué: son las dos únicas al recorrer todas las filas de `veredicto_congelado_0355.csv` (IPPO spill repite a vecinos en P5).
- "Semilla base" remite al Cap. III. Por qué: se usaba sin definir; la definición está en el protocolo.
- `tab:metricas` suma las paradas medias de corredor. Por qué: `comun.py` las calcula y el Cap. III las lista.
- El caption de `tab:metricas` dice "las del bloque inferior se refieren a la avenida y a los enlaces". Por qué: decía "solo en los escenarios de varios semáforos", y todos los casos del plan tienen varios.
- Los modelos con mensajes se nombran con sus nombres canónicos (IPPO vecinos, IPPO spill, DQN y MAPPO). Por qué: "IPPO con mensajes" no es un nombre del documento.
- La lectura de γ como horizonte: "el Cap. IV usa esa lectura para interpretar el descuento de las redes". Por qué: el Cap. IV solo la aplica al 0.95 de las redes, no al 0.9 tabular.
- La apertura ya no asigna DQN a U4. Por qué: `tab:pipeline` lo pone en U2.
- [sin cambio neto] Las épocas de PPO ya no llevan símbolo. La edición había escrito "durante $K$ épocas"; la verificación (`746a0c3`) lo cambió por "varias épocas". Por qué: K quedó reservada para las plazas K_ℓ.

### Capítulo III, Marco metodológico (`capitulo3.tex`, nuevo, 863 líneas)

Lo principal: capítulo nuevo con el diseño del método, armado con texto del antiguo `capitulo4.tex` y reordenado según el plan maestro. Cambia la notación de la recompensa (sección 6) y se agregan `tab:pipeline`, la formulación en tres subsecciones y las definiciones del protocolo (validación, checkpoint, base publicada, celda).

Movido
- El commit `cc2a353` trasladó por script, sin reescribir párrafos, desde el `capitulo4.tex` original: la apertura, Alcance y unidades, Resumen de las unidades, Escenarios sintéticos, U2, Algoritmos recomendados, U3, U4, Plan de pruebas (introducción, fase exploratoria previa, objetivo y casos), Modelos, Protocolo común, Métricas de salida y Regla de veredicto.
- Dentro del capítulo:
  - U3 (medición del desempeño, `sec:u3`) pasa después de U4 y de "Modelos comparados"; en `7bd8685` iba entre U2 y U4. Por qué: es el orden del plan maestro, que presenta qué se compara antes de cómo se mide;
  - la frase del actuado pasa de escenarios a `sec:modelos`;
  - los verdes mínimo y máximo pasan de U4 a `sec:formulacion`, como máscara;
  - las definiciones de `ret_retraso`, `ret_colas` y `ret_spill` pasan de "Métricas de salida" a `sec:u3`, "Retornos por segundo";
  - la fase exploratoria previa pasa al inicio de `sec:plan2`, condensada en un párrafo;
  - la regla de PENDIENTE por falta de cómputo pasa de "Ejecución y costo" a `sec:veredicto`;
  - la convergencia se define antes de la lista de veredictos;
  - `tab:plan2-semillas` quedó después de las definiciones de validación, checkpoint y base publicada (verificación).

Eliminado
- La instalación de SUMO y la limpieza de OSM como parte de U1. Por qué: el camino OSM no produjo ningún escenario evaluado (Anexo D).
- "Algoritmos recomendados". Por qué: mencionaba `stable-baselines3` como implementación de referencia de DQN y PPO (la tesis no lo usa) y decía "se implementaron los cuatro" listando cinco. Lo útil pasó a `sec:modelos`.
- El verde mínimo de 5 s en las fases de giro protegido y "con cuatro fases, 1024 estados". Por qué: ningún caso del plan tiene giros protegidos.
- "Es la recompensa de la fase exploratoria" y las frases sobre la recompensa anterior en el Protocolo común. Por qué: repetían `sec:formulacion`.
- El párrafo "Dos precisiones importan...". Por qué: duplicaba el Cap. II y afirmaba que la espera detenida es lo que optimiza la recompensa, lo que en el plan solo vale para la ablación.
- El párrafo de hiperparámetros tabulares. Por qué: los hiperparámetros viven en el Cap. IV (`tab:plan2-hiper`).
- "De él [el fijo ganador] se genera el actuado". Por qué: contradice `comun.archivo_actuado`, que toma las fases del programa de la red con desfase cero.
- El ejemplo "El veredicto sale solo del retraso" con cifras exploratorias de corredor_alta (20.1 %, 28.1 %, −30.60 frente a −23.89). Queda una remisión a `sec:lectura-modelo`.
- La fecha de aprobación del asesor (se repuso en la conclusión 6), la enumeración N0-N6 y las etiquetas E1-E6.
- En la tabla de escenarios, las filas cruce, cruce2, P6 y P7 y las columnas "Programa fijo" y "Fases verdes". P6 y P7 quedan en una frase y la historia del fijo en el Anexo C.
- Las cifras exploratorias (15 %, 60 %, 6 %, 2 s) como motivación de U4 y la pila de implementación (PyTorch, sin Gym) dentro de U4.
- "Tres controles comparados" y "el escenario de estrés del módulo U4".
- [sin cambio neto] La regla de empate de la base mediana ("en empate, la base menor"): la agregó la edición (`7c63dbe`) y la quitó la verificación (`746a0c3`). Por qué: venía de un docstring que no coincide con `veredicto.base_mediana`, que ordena por (valor, base).

Agregado
- `cap:metodologia` y la apertura.
- `sec:vision-general` con `tab:pipeline`.
- `sec:formulacion` en tres subsecciones: agentes y restricciones, estado, recompensa. Incluye cómo tratan los tabulares las restricciones (se aplican después de elegir y la tabla se actualiza con la acción elegida).
- `sec:modelos` como sección propia: un párrafo por comparación, lo que aísla cada pareja, y citas a `SuttonBarto2018`, `Mnih2015_DQN`, `Schulman2017_PPO` y `Yu2021_MAPPO`.
- `sec:protocolo`, con las definiciones del protocolo (ver sección 6).
- `sec:estadistica` con `eq:delta`, IC con t, bootstrap pareado (10 000 remuestreos, percentiles 2.5 y 97.5) y Wilcoxon.
- `sec:veredicto`: EMPATA si el IC y Wilcoxon discrepan, y IPPO spill en P3-P5 como "= vecinos".
- Los símbolos de `eq:recompensa-u4`: v_max = 13.89 m/s, la división entre 5 (el cambio de 8 s pesa 8/5) y la escala 0.02 de las redes.
- La justificación de los dos cambios de la recompensa de retraso: las colas que reptan, y la señal acumulada en lugar del nivel instantáneo.
- "La observación supone exactamente dos fases verdes".
- Cuatro TODO (líneas 71, 604, 770 y 844).

Reescrito o corregido
- El estado `s = (c_N, c_S, c_E, c_O, f)` pasa a `s = (b_O, b_E, b_N, b_S, φ)` en el orden del código. La recompensa de retraso se presenta primero como la común, y `P_e/2` pasa a la parte entera.
- La verificación cambió la notación de conjuntos e índices a J_i, L_i, ℓ, q_ℓ y K_ℓ (ver sección 6).
- Las 38 plazas corresponden a enlaces de 285.6 m (P1-P4); malla3 tiene 279 m y 37 plazas. El texto decía "300 m".
- La observación es un bloque local de 12, un identificador de 3 (9 en malla3) y 8 por lado: 31 o 53 componentes.
- El canal: latencia y pérdida nulas en todo el plan; solo se usaron en la fase exploratoria. El texto decía "prueba de robustez del plan de pruebas", que no existe.
- "Episodios de spillback" pasa a "eventos (flancos de subida)".
- "Celda" se define como un modelo en un caso.
- La introducción de U4 describe los cuatro cambios frente a los tabulares. La edición había escrito que a los tabulares "les falta información de los vecinos", una causa que el Cap. V contradice; la verificación lo corrigió.
- En `tab:pipeline`, IPPO pasa a U2, alineado con la Introducción (verificación).
- La introducción de U3 ya no repite el Cap. II (verificación).
- [sin cambio neto] La metáfora "escalera" para las variantes la introdujo la edición (`7c63dbe`); la verificación (`746a0c3`) la cambió por "cada una añade un elemento a la anterior". Por qué: regla de lenguaje natural del plan.
- La variante `cambio`: el original decía que resta w₄ = 2 por cada cambio de fase y que "se corre aparte". Ahora dice "Una cuarta variante, que resta un costo fijo por cada cambio de fase, quedó formulada pero no se entrenó", sin w₄, en línea con `recomendaciones.tex` ("quedó formulada y sin correr"). Por qué: nunca se corrió (auditoría `cap4_u2u3u4`). La frase "los pesos se fijaron de antemano, sin barrido" se conserva.
- MAPPO "comparte la arquitectura del actor y la observación y entrena su propia política".

### Capítulo IV, Implementación (`capitulo4.tex`, de 1967 a 1094 líneas)

Lo principal: queda cómo se construyó y ejecutó el plan. El manual de uso de SUMO y OSM sale al Anexo D y el material exploratorio al Anexo C; entran extractos de los archivos reales del plan. Revisar las correcciones hechas contra el código (siembra, spill, plazas) y las cifras del prototipo de malla3, que ya no aparecen (sección 8).

Eliminado
- Del párrafo de hardware, los tiempos por episodio y por entrenamiento (incluida la errata de 17 s; el máximo real es 16.4). Por qué: el costo vive en `sec:ejecucion`.
- El ítem "Revisar semáforos importados", condensado en el Anexo D: la opción Traffic lights pasa a la descripción del asistente y la revisión de los `<tlLogic>` al cuarto paso de la limpieza prevista. Salen del todo la frase normativa sin fuente ("el ámbar suele fijarse entre 3 y 4 s...") y el consejo de mantener los semáforos generados. Por qué: es del camino OSM. En el Cap. IV solo se conservó el ámbar de 3 s.
- El tutorial "Crear el archivo de configuración" y "Ejecución de SUMO", con sus bloques verbatim. Por qué: era manual de uso. Las corridas se lanzan desde Python.
- Los ejemplos de `tlLogic` y de flujos del escenario cruce. Por qué: eran exploratorios y contradecían la convención avenida = este–oeste. Se reemplazaron por los de P1.
- El esquema de ε de la fase exploratoria (×0.9 hasta 0.05; 0.96 y 0.95), la regla de 40, 120 y 100 episodios, la evaluación cada cinco episodios con una semilla y "del orden de 600 a 800 decisiones por semáforo". Por qué: eran exploratorios o inexactos.
- El pseudocódigo de `rl_semaforo.py`, que usaba la recompensa de colas. Se reemplazó por uno de `rl_corredor.py`.
- `fig:flow-u2` (`U2.png`) y su párrafo. Por qué: la figura es genérica e inexacta, con un criterio de parada que no existe y sin validación ni checkpoints. Quedó un TODO.
- La regla vieja de "tres políticas por variante" (la base cuya última evaluación intermedia es la mediana). Por qué: contradice el protocolo del plan.
- `tab:hiper-ippo` como tabla aparte, con sus filas de protocolo exploratorio (fusionada, ver sección 5).
- La fecha 18.09.2026 y las cifras del prototipo de malla3 (programa corregido 21.6 s, cruzado 26.0 s, actuado 25.4 s). Por qué: la tarea pedía reducir el prototipo a una o dos frases. Aviso: esas cifras ya no aparecen en ninguna parte de la tesis (ver sección 8).
- La frase "Los programas fijos de los cuatro escenarios nominales se tunearon con las semillas 1001 a 1003...". Por qué: contradice el plan, que rebarrió todo con 2001-2003.
- El barrido exploratorio de corredor_alta (verde de 25 a 40 s, 80 configuraciones, 152 frente a 171 s). Por qué: no es el barrido del plan, y los 171 s no tienen fuente.
- La fecha "heredada del 06.09.2026" en la nota de `cola_mi_salida`.
- La bitácora de la cola en el cuerpo del texto (arranque a las 17:55, prioridades numeradas, adelanto nocturno, reintentos de Q-learning, PermissionError). Pasó a los comentarios `% fuente`.
- Las cifras de costo que repetían `tab:plan2-costo` y la repetición del entorno en la reproducibilidad (remite a `tab:hw`).
- `randomTrips.py`, que pasó al Anexo D.
- En P2 (`sec:calibracion`), que en ese caso se reportan también "las diferencias absolutas de retraso". Queda que se registran los vehículos no terminados y el throughput. El reporte de edición no da el motivo.

Movido
- Desde U4 y el plan: corredor_alta y la calibración de P4 a `sec:calibracion`, malla3 a `sec:construccion` y `tab:plan2-fijo` a `sec:referencias-fijas`.
- Las pruebas de humo de DQN y MAPPO, que estaban en los párrafos de cada modelo, a `sec:humo` ("DQN y MAPPO"), sin cambios de cifras.
- El determinismo y los metadatos a la subsección de IPPO. La ejecución y el costo a `sec:ejecucion`.
- La frase de hiperparámetros tabulares (que el editor del Cap. III quitó) a "Q-learning y SARSA", copiada del original.

Agregado
- `cap:implementacion`, la apertura y `sec:entorno`.
- "Red vial": extractos literales de `corredor.nod.xml` y `corredor.edg.xml` y el comando de `build_net.bat`. Por qué: el texto decía que las redes se construyen con netconvert pero no lo mostraba.
- "Configuración y ejecución": paso de 1 s, `time-to-teleport` −1 y barrido sin TraCI.
- "Programas de semáforos" con `plan2/corredor.add.xml` (P1) y "Demanda" con `plan2/corredor.rou.xml`, con los atributos del vType explicados (5 m más 2.5 m dan las plazas de 7.5 m).
- "Programa actuado", escrita a partir de `comun.archivo_actuado`: fases del programa de la red, 10/60 s y desfase cero.
- "Pasos del ciclo" (con validación y checkpoint), "Episodio" actualizado y el pseudocódigo nuevo.
- Valores Q iniciales en cero y desempate al azar; la pérdida de Huber en DQN; la entropía solo sobre las decisiones libres en IPPO; un párrafo tras `tab:plan2-hiper`.
- La definición de "prueba de humo" al abrir `sec:humo`.
- Cuatro TODO (líneas 280, 344, 575 y 827).

Corregido
- "Un computador de escritorio sin GPU" pasa a "tiene GPU pero no la usa".
- P4 comparte el umbral de P2, pero con otros candidatos y la condición del 10 % de vehículos sin terminar. Se define la saturación de la rotonda (32 de 36 plazas). "La celda emite veredictos" pasa a "el caso".
- `sec:spill-vecinos`: "cuatro parciales" pasa a "siete parciales". Las nueve corridas de spill se verificaron fila a fila el 27.09 (0 filas distintas, `spill_activaciones` = 0).
- Prueba de humo: "una compuerta de la fase exploratoria exigía", la recompensa de colas, las semillas 1001-1010 y la remisión al Anexo C.

Corregido en la verificación (cada punto, con lo que se contrastó)
- La siembra del generador: con la semilla base al entrenar y con la semilla de cada episodio al validar o evaluar. La edición había escrito "la semilla base en todos los modos", lo que es falso. Por qué: `rl_corredor.py` siembra con la base al entrenar, `evaluar_greedy` con 999 y 1999, y `evaluar.py` con cada semilla de 1001 a 1030.
- Las siete evaluaciones de spill nunca se lanzaron. El texto decía que "siguieron en la cola". Por qué: `estado.json` de la cola tiene 247 trabajos hechos, y los siete que faltan son justo esas evaluaciones.
- "16 y 20 de 38 plazas" pasa a "7.9 de 38 (máximo 10)" con el fijo tuneado de P1. Por qué: 16 y 20 coinciden con la cola total de la red, no con la del enlace (`plan2/evaluacion_corredor_resumen.csv`). Las cifras viejas quedaron en un comentario.
- Con el fijo tuneado de P2 no queda ningún vehículo sin terminar. Por qué: `plan2/evaluacion_corredor_alta_resumen.csv` da 0 no terminados con el fijo y el actuado; los 80 a 94 del texto no son de ese programa.
- En el paso 3, el orden de SARSA: elige antes de actualizar. Por qué: el texto decía "actualiza y luego elige", que solo vale para Q-learning (`rl_corredor.py`).
- IPPO también usa un solo Adam para actor y crítico. Por qué: `rl_ippo.py` crea un Adam sobre todos los parámetros; la tabla solo lo decía de MAPPO.
- La pérdida del valor sin recorte vale solo para IPPO y MAPPO. Por qué: el párrafo parecía general, y DQN usa pérdida de Huber y recorte global (`rl_dqn.py`).
- La remisión apunta a `sec:protocolo` y a `sec:veredicto`. Por qué: el papel de cada referencia en el veredicto está en la segunda.
- El párrafo inicial de la calibración anuncia la regla de la rotonda. Por qué: en P4 el factor lo fija esa regla (1.2), no el criterio general (2.5).
- Vuelve al texto que la cola no registró la duración de nueve entrenamientos de Q-learning. Por qué: la salvedad había quedado solo en comentarios; se comprobó en `estado.json`.
- La primera decisión de cada verde es a los 5 s, salvo en el primer verde del episodio, donde se decide ya en el paso 0. Por qué: `rl_corredor.py` solo salta el instante 0 cuando `pasos > 0`.
- El actuado tiene "los mismos estados de verde y ámbar que el fijo (en malla3, en otro orden)". Por qué: "mismos verdes y ámbares" era ambiguo; se compararon los `.add.xml` del fijo y del actuado.
- Las llegadas equiespaciadas se explican una vez, en `sec:construccion`. Por qué: estaban dos veces en el capítulo.
- Cada configuración del barrido son tres corridas, una por semilla. Por qué: lo dicen `barrer_fijo.py` y `plan2/barrido_<esc>.csv` (semillas 2001-2003).
- La prueba de humo con −35 % se marca como resultado exploratorio, fuera de las metas. Por qué: es una de las decisiones transversales de la verificación (sección 7); el resultado viene de la fase exploratoria, en un escenario que no es un caso del plan.
- La columna "Espera máx. para entrar" de `tab:red-alta-factor` se define en el caption. Por qué: no estaba definida; el texto original de resultados la describe como la espera máxima para entrar a la red.

### Capítulo V, Resultados (`capitulo5.tex`, de 1290 a 546 líneas)

Lo principal: queda solo el plan de pruebas, de lo global al detalle, con dos tablas nuevas (`tab:plan2-resumen`, `tab:plan2-metas`); la fase exploratoria pasa al Anexo C. Revisar la frase sobre las métricas de corredor, que no se analizan (TODO), y los valores p, que conservan el redondeo del original.

Eliminado
- Todo lo que seguía a "Fase exploratoria: resumen de los cuatro casos" pasó al Anexo C (commit `cc2a353`). La apertura ya no anuncia E1-E6.
- La sección "Resultados del plan de pruebas por casos": los dos párrafos que repetían casos y protocolo. Por qué: duplicaban `tab:plan2-casos` y `sec:protocolo`.
- En la lectura por caso:
  - los resultados de los barridos (20/10/15, 25/15/25, 25/15 con 0/23/0), que viven en el Cap. IV (`tab:plan2-fijo`), y la lista de medias ± IC de nueve modelos, que viven en las tablas `veredicto_*` (Cap. V y Anexo A; `tab:plan2-resumen` solo da la media);
  - en P2, los rangos entre bases de Q-learning y SARSA, que están en el Anexo A;
  - en P4, la calibración de la rotonda (1.3, 400-700 s, colas, espera de 4 s);
  - en P5, la historia del prototipo, las 60 configuraciones y "29.0 s sin desfases".
- "Qué es alcanzable para P6 y P7", que pasó a las recomendaciones.
- En "Qué lo limita", los tiempos por episodio, las duraciones y el equipo (AMD Ryzen, 16 GB, sin GPU). Por qué: viven en el Cap. IV.
- Del párrafo de spillback, la cola máxima de los enlaces (9, 12 y 8), la comprobación episodio a episodio de spill y la nota de `cola_mi_salida`. Por qué: viven en el Cap. IV.
- La frase "el crítico centralizado no cambia el veredicto del actor". Por qué: era redundante (verificación).

Movido
- Las tablas por modelo `veredicto_actuado`, `veredicto_ql` y `veredicto_ippo_vecinos` pasan al inicio de la lectura por caso. Por qué: se citaban sus intervalos antes de que aparecieran.
- "Curvas de aprendizaje y convergencia" deja de estar entre la matriz y la lectura por caso y pasa a `sec:convergencia`, después de la lectura por modelo. Reúne los checkpoints de P3 y P5, que antes se contaban tres veces.

Agregado
- `sec:resultados-global` (se conserva `sec:resultados-plan2`), con "Veredicto por caso y modelo" y "Metas cuantitativas".
- `tab:plan2-resumen` y `tab:plan2-metas` (ver sección 5).
- Un párrafo de notación: fijo tuneado, actuado, Δ_f, Δ_a, IC bootstrap y p de Wilcoxon.
- El encabezado "Término de spillback".
- MAPPO frente a DQN en P4 (29.45 frente a 29.04 s).
- En la verificación, una frase: las métricas de corredor se registraron pero no se analizan (con TODO, ver sección 8).

Reescrito
- Las salvedades van después de la matriz y distinguen seis celdas PENDIENTE: cinco por no convergencia con veredicto provisional y una sin datos (`ql_colas` en P5).
- La lectura de la matriz, celda por celda, pasa a patrones en dos párrafos.
- Cada caso P1-P5 queda en unas pocas frases con `\ref` a las tablas.
- La lectura por modelo ya no repite pares de retrasos. Los párrafos "Tabular frente a aproximación de funciones" y "Efecto de la recompensa" se dividen, y se recuerda que en Δ recompensa un valor positivo es mejor.
- "Crítico local frente a centralizado" se acota a "no cambia el veredicto donde los dos son firmes", con los matices de P2 y P5.
- Las curvas se describen caso por caso (antes: "descienden y oscilan en una banda estrecha"), y el salto de Q-learning en P4 se explica.
- El alcance se condensa, con remisiones a las tablas del Cap. IV.

Corregido
- "Casi cualquier control que reaccione a las colas gana" (P2) pasa a "el actuado y los aprendices con red neuronal".
- "No el doble previsto" (P4) pasa a "no el 2.5 que daba el criterio usado en corredor_alta".
- "Una red sin eje principal" pasa a "una malla con vecinos en los dos ejes".
- Términos: "fijo tuneado" en lugar de "fijo coordinado", "fijo en ajedrez" o "de la celda"; "base publicada no converge".
- En la verificación (cada punto, con lo que se contrastó):
  - los valores p vuelven al redondeo del original (0.057, 0.07, 0.003, 0.87, 0.09 y 0.52). La edición los había llevado a la precisión de las tablas. Por qué: decisión transversal de conservar el redondeo del documento;
  - "las cinco celdas pendientes" pasa a "cinco de las seis". Por qué: `veredicto_congelado_0355.csv` tiene seis PENDIENTE, una sin datos (`ql_colas` en P5);
  - se repuso "La ablación `ql_colas` no se corrió en P5". Por qué: la salvedad estaba en el original y se había perdido;
  - la ablación explica el techo tabular solo donde tiene veredicto firme. Por qué: `ql_colas` es firme solo en P1, P3 y P4;
  - "ningún modelo lo mejora un 5 %" (P4) pasa a "con su base publicada". Por qué: una base no publicada de MAPPO (s4042) da −5.8 %;
  - la fragilidad en P3 vuelve a "dos de las tres bases". Por qué: así lo decía el original, y las series de validación de s42 y s4042 lo confirman;
  - se repuso que Q-learning, SARSA e IPPO local quedan detrás del actuado en P5. Por qué: estaba en el original y lo confirma el CSV congelado;
  - se quitaron tres inferencias nuevas: "uno por cada familia" (ni el original ni `grafico_convergencia.py` dan ese criterio), "descansa en diez episodios" (imprecisa) y el reencuadre de que las diferencias solo aparecen en throughput y spillback (también las hay de retraso: IPPO vecinos tiene Δ_a −4.4 % en P2);
  - las remisiones apuntan a `sec:spill-vecinos` y `sec:calibracion` en lugar de secciones más amplias, y el Anexo C sustituye a `sec:plan2` para la ventaja exploratoria de IPPO sobre Q-learning. Por qué: `sec:plan2` no trae esa comparación;
  - "Qué funciona, dónde y cuánto" recupera sus magnitudes. Por qué: hallazgo de severidad alta; las cifras estaban en el original.
- MAPPO y spill "usan la política de IPPO con mensajes" pasa a "comparten la arquitectura del actor y la observación; cada uno entrena su propia política".

### Conclusiones (`conclusiones.tex`, de 372 a 249 líneas)

Lo principal: pasan de 14 a 6, ordenadas por objetivo, más dos párrafos finales sobre la fase exploratoria. Revisar `conclusiones.tex:221`: la verificación reintrodujo una frase que contradice la conclusión 2 (ver "Reescrito o corregido" y la sección 8).

Correspondencia: la antigua 1 y la 2 pasan a la 4 (U4). La 3 se reparte: MAPPO a la 4 y DQN a la 2. La 4 pasa a la 2 (U2). La 5 pasa a la 3 (U3), y la rotonda, a la 1. La 6 sigue en la 6. De la 8 queda una frase en la 2, de la 11 una frase en la 3, la 12 pasa a la 5 y la 14 al segundo párrafo final. La 7, la 9, la 10 y la 13 se eliminan. La conclusión 1 (U1) es nueva.

Eliminado
- La 7 (tabular con recompensa de colas): duplica la corrección del 60 %, que está en la 5.
- La 9 (techo tabular con cuatro fases): se apoya en un fijo de cruce2 tuneado con semillas de evaluación, y el plan no tiene casos de cuatro fases.
- La 10 (agentes sin comunicación en la red): la cubre la 4.
- La 13 ("cumple la meta en el cruce"): contradice la 6, y el cruce no es un caso del plan.
- Del párrafo de transición "Las conclusiones 7 a 14 corresponden a la fase exploratoria...", la remisión a las conclusiones 7 a 14 y "se conservan como registro de lo que motivó el plan". El resto (diez semillas, Q-learning con recompensa de colas, política del último episodio) pasa al primer párrafo final.
- "Aprender el valor coordina peor que aprender la política" y "los mensajes también le sirven [a DQN]". Por qué: la inferencia causal no se sostiene, porque no hay un DQN sin mensajes ni ajuste por caso.
- "La peor de las tres bases de vecinos tiene menos retraso que la mejor de local". Por qué: es una comparación de medias sin prueba pareada, y en P2 cae en el ruido. Aviso: el Cap. I conserva esta afirmación (ver sección 8).
- "Ningún modelo supera a un fijo coordinado bien tuneado en una malla regular". Por qué: generalizaba desde una sola malla.
- En la antigua 5: el programa 20/10/15 ("en el interior de la malla", errata), los datos sobrantes de la rotonda y los márgenes de P4.
- De la antigua 1: el tiempo medio de vecinos en P5, la convergencia por bases, las cifras de local en P3-P5 y la cola máxima de los enlaces (queda en un comentario).
- De la antigua 12: "revisión adversarial del documento" y "cambió el signo de varias conclusiones".
- Del párrafo inicial: el recuento del protocolo y la lista de los ocho aprendices.
- De la antigua 14: el título "primer control aprendido que supera al actuado" (el plan lo desmiente), las cifras exploratorias de spillback (0-3 frente a 79 s) y de servicio (2-3 %) y la repetición de la red (−8.8/−7.8).

Agregado
- La conclusión 1 (U1), escrita con texto existente: redes con netconvert, demanda por flujos, P2 y P4, la rotonda y Lima sin limpiar (Anexo D).
- En la 3, un párrafo de metas secundarias con remisión a `tab:plan2-metas`.

Reescrito o corregido
- "Con la misma información, IPPO y MAPPO quedan por delante de DQN" pasa a "IPPO vecinos por delante en los cinco casos; MAPPO en cuatro". Por qué: en P4 MAPPO tiene 29.45 s y DQN 29.04 s.
- "Solo los que reciben mensajes evitan perder..." pasa a "todos los controles sin mensajes pierden entre un 21.8 y un 42.5 %". Por qué: DQN también recibe mensajes. La verificación corrigió además el redondeo de 21 y 43.
- "Solo supera a un fijo coordinado cuando la demanda excede la capacidad" pasa a "en un 5 % o más... como en P2". Por qué: el actuado mejora un 1.1 % en P3. La verificación quitó el paréntesis "(FUNCIONA)".
- La 4 dice que spill reproduce a vecinos en P3-P5, sin dar el recuento de corridas, que estaba desactualizado.
- La 5 usa la evidencia del plan: el 60 % exploratorio pasa a 10.6 y 9.2 % con el protocolo del plan, más el checkpoint y la fragilidad de P3.
- La 6 pierde las cifras que repetía de la 1.
- La 6, frase de DQN: el original decía "con los mensajes, IPPO y MAPPO quedan a la par y DQN detrás". La edición (`ad26402`) la cambió por "IPPO vecinos y MAPPO quedan a la par y DQN queda por detrás de IPPO vecinos". Esa corrección se perdió en la verificación: al dividir el párrafo, `024e23e` escribió "Entre los que reciben mensajes, IPPO vecinos y MAPPO quedan a la par y DQN por detrás" (`conclusiones.tex:221`), que contradice la conclusión 2 (en P4, MAPPO 29.45 s y DQN 29.04 s). Queda pendiente (sección 8).
- Los dos párrafos finales. El primero dice qué protocolo usaba la fase exploratoria (viene del párrafo de transición) y que, donde el plan repitió una medición, las conclusiones usan la del plan. En el segundo, la progresión y la robustez al canal quedan como dos observaciones de esa fase "sin confirmar en el plan", con TODO. El canal imperfecto "mantenía el retraso cerca del actuado" pasa a "perdió la progresión y, en el corredor, dejó de superar al actuado".
- En la verificación (cada punto, con lo que se contrastó):
  - se repuso la salvedad de P5 (el IC bootstrap de +0.4 a +3.4 % no incluye el cero; p = 0.52). Por qué: estaba en el original y coincide con el CSV congelado y el Cap. V;
  - el título de la 4 recupera "ni el término de spillback ni el crítico centralizado añaden algo medible". Por qué: el título editado tenía un salto lógico (IPPO vecinos no tiene crítico centralizado); se vuelve al sentido de los títulos originales 2 y 3;
  - se avisa la convención de signo de Δ recompensa. Por qué: +3.0 y +6.4 % se leían como empeoramiento;
  - "la política publicada no convergió" pasa a "la base publicada no convergió". Por qué: la convergencia se mide sobre la serie de validación de la base publicada (`sec:veredicto`);
  - se quitó la comparación con la semiamplitud de los IC (0.92 y 1.02 s). Por qué: era una inferencia nueva; el original solo daba la diferencia de 0.07 s en P4;
  - el throughput es evaluable solo en P2. Por qué: lo dicen la introducción y el Cap. V;
  - las prácticas del quinto objetivo ya no incluyen "las mismas semillas para todos los controles". Por qué: el objetivo 5 no la menciona;
  - se repuso "plan aprobado por el asesor el 23.09.2026". Por qué: estaba en el original y consta en `plan2/ESPEC.md`;
  - "funciona" pasa a "mejora" en el título de la 6. Por qué: en P4 el veredicto de IPPO vecinos es MEJORA;
  - se quitó la frase del prototipo de malla3 en la 1. Por qué: no responde a U1, y el plan ubica el prototipo en el Cap. IV;
  - "Pesa más la información que el algoritmo" se apoya ahora en DQN frente a IPPO local (P1, P3, P4 y P5). Por qué: el argumento anterior tenía un salto lógico. En esta misma reescritura se perdió la corrección de la frase de DQN (ver arriba);
  - "Esta fase" pasa a "Esta etapa". Por qué: convención de términos (sección 6).

### Recomendaciones (`recomendaciones.tex`)

Lo principal: sin cambios de fondo. Salen cifras repetidas y fechas internas; Lima pasa al primer lugar del trabajo siguiente y "Presupuestar P6 y P7" absorbe el párrafo del antiguo capítulo de resultados. Revisar las estimaciones de viabilidad de P6 y P7 que la verificación repuso (sección 8).

Eliminado
- Las cifras que repetían las conclusiones o el Cap. IV: 38 frente a 6 % y 20/10/15 (en "Barrer siempre la referencia"), −19.8 y +21.8 % (en "Mantener las dos referencias"), la lista de celdas y los episodios 40/50 (en "Juzgar la convergencia") y 1.3 y 400-700 s (en "Calibrar la demanda de estrés").
- Del presupuesto de P6 y P7: la descripción del equipo, los rangos por escenario, 21-63 y 95-115 min, el factor 2.3, 3.6-4.4 h, 11-13 h y la mención a E2. Por qué: había contradicciones con el capítulo de resultados (2.3 frente a 2.4; 3.6-4.4 frente a 3.8 h).
- Las fechas internas 18.09 y 06.09.

Movido
- "Llevar el protocolo al cruce real de Lima" pasa al primer lugar del trabajo siguiente, con remisión al Anexo D.
- "Presupuestar P6 y P7" absorbe el párrafo "Qué es alcanzable para P6 y P7" del antiguo capítulo de resultados, con un único factor (2.4).
- "Priorizar P6 sobre P7" recibe de ese párrafo la frase de que la malla no tiene elementos sin semáforo que se saturen antes.

Reescrito o corregido
- "Cerrar las celdas pendientes" reúne la lista completa (seis) y la acción. Los hiperparámetros de DQN y MAPPO se fijaron antes de su prueba de humo; el texto decía "en".
- "Ningún control mueve el throughput" pasó primero a "no puede aumentarlo". Tras la verificación dice "ningún control del plan aumentó el throughput más de un 0.6 %".
- "Entrenar con canal imperfecto": el retraso sí subía (1.4 a 2.5 s en el corredor). "Basta" pasa a "conviene".
- `cola_mi_salida` se identifica como la componente 22 de `tab:obs-u4`. En la verificación se corrigió que "en la malla las dos magnitudes coinciden" (falso: lo que coincide es la longitud, en todos los escenarios) y se aclaró que IPPO local no la usa.
- En la verificación (cada punto, con lo que se contrastó):
  - la remisión de la entrada pasa a `cap:resultados`. Por qué: apuntaba a `sec:plan2`, que es el método;
  - la transferencia a Lima se justifica como "trabajo siguiente de la introducción". Por qué: la edición la justificaba con U1, algo que el original no decía;
  - "llena el enlace" pasa a "alcanza el umbral de spillback". Por qué: el criterio de calibración es el umbral de 34 de 38 plazas (`sec:calibracion`);
  - P6 y P7 quedan en dos párrafos, declarados como estimaciones, y recuperan las lecturas de viabilidad del original (ver sección 8). Por qué: el párrafo estaba sobrecargado; las cifras se contrastaron con `tab:plan2-costo` y `sec:ejecucion`;
  - "los que usan la política IPPO con mensajes" pasa a "IPPO vecinos y MAPPO". Por qué: MAPPO no usa la política de IPPO; comparte la arquitectura del actor y entrena la suya (sección 6).
- El encabezado manual del capítulo (`\chapter*`) se mantuvo por pedido de la tarea (ver sección 8).

### Anexos A a D (`anexos.tex`, `anexo_c_exploratoria.tex`, `anexo_d_osm.tex`)

Lo principal: el Anexo A queda con las tablas del plan y el B se reordena según el pipeline. El C (nuevo) condensa la fase exploratoria y avisa dónde el plan cambió la lectura. El D (nuevo) recoge el procedimiento OSM con el estado real de la importación. Revisar los avisos de cambio de lectura del Anexo C (E3, E6 y P3).

Estructura común
- `anexos.tex` usa `\customchapter{ANEXOS}` en lugar del encabezado copiado a mano. Por qué: le faltaba el `\vspace{-4.5cm}`.
- Cada anexo tiene `\phantomsection` y una entrada en el índice.
- Las tablas y figuras se numeran A.x, C.x y D.x. Por qué: antes seguían la numeración del último capítulo (4.28 a 4.72) y parecían resultados.

Anexo A, Tablas completas del plan de pruebas
- Eliminado: el antiguo Anexo A exploratorio, con las tablas por episodio (ver sección 5), que llegó al Anexo C en el commit de estructura y se eliminó en la edición. En el texto del plan se quitaron "v2" y "brazos"; el protocolo queda en una frase.
- Reescrito: los párrafos de SARSA/`ql_colas`, DQN/MAPPO y local/spill quedan en pocas frases, sin las cifras que están en las tablas.
- En la verificación se repusieron la excepción de P2 de `ql_colas` (no convergió, +6.8 %, mientras Q-learning mejora un 8.8 %), que no se corrió en P5, y la explicación de por qué la tabla de bases de spill tiene dos filas en P3 y ninguna en P4 y P5.

Anexo B, Código fuente
- Movido: los listados siguen el pipeline (escenarios_plan2, barrer_fijo, comun, rl_corredor, rl_ippo, rl_dqn, rl_mappo, evaluar, consolidar, veredicto). `rl_semaforo.py` y `tablas_tex.py` quedan al final como scripts de la fase exploratoria.
- Reescrito: los títulos ya no dicen "plan v2". El de `tablas_tex.py` dice "tablas de la fase exploratoria" (antes decía "del capítulo de resultados", que quedó desactualizado al salir la fase exploratoria del Cap. V). Las omisiones se justifican por función y no por largo de línea, y se nombran `grafico_convergencia.py`, `preparar.py` y `build_net.bat`. La apertura cubre el Cap. V y el Anexo C.

Anexo C, Fase exploratoria (nuevo)
- Movido: el contenido exploratorio del antiguo capítulo de resultados, la historia del fijo en dos rondas (del `capitulo4.tex` original) y la descripción de cruce y cruce2 (antes, filas de `tab:escenarios`).
- Eliminado:
  - las tablas por episodio, los resúmenes por episodio, tres tablas `*_evaluacion` y tres `*_fragilidad` (ver sección 5);
  - 14 figuras, con el texto que solo las describía (serie por minuto, ECDF, curva de E1);
  - "Nivel alcanzado según el criterio prefijado" (N0-N6, criterios nunca definidos);
  - "Limitaciones de esta fase";
  - los párrafos "Techo", "Reacción local" y "Metas" de la lectura conjunta;
  - en la prueba de humo, las corridas de ajuste con las bases 43 y 45 y la tercera corrida;
  - en E4-U4, la comparación con el fijo 20/20 (−1.5 %) y los porcentajes de cambios y paradas;
  - en E3-U4, "la mensajería añade los seis puntos" (errata) y "el término nunca se activa" (contradecía el Cap. IV);
  - en E6, la mención a N4 y el rango 181-194 s;
  - la "revisión adversarial" y el detalle de cruce (0.2 s);
  - los labels `sec:resultados-u4` y `sec:lectura`, porque las secciones numeradas pasan a `\subsection*`.
- Agregado:
  - una apertura en cuatro párrafos: qué fue la fase, las cuatro diferencias de protocolo, IPPO y la numeración E con su equivalencia en P1-P3;
  - la subsección "Escenarios cruce y cruce2";
  - las definiciones de las variantes, de "control de no daño" y de "vehículos de paso";
  - los párrafos que marcan dónde el plan cambió la lectura: IPPO en P1, P2 y P3 y, en la verificación, el agente tabular en E3 (+60 % pasa a +10.6 y +9.2 % en P1) y en E6 (+37 % pasa a −8.8 %, MEJORA, en P2);
  - la fragilidad del checkpoint de P3;
  - un TODO en la línea 441.
- Conservado (restituido en la verificación) [sin cambio neto]: la identidad bit a bit de los tensores de spill y vecinos en la red exploratoria (E4-U4). Estaba en el `capitulo5.tex` original; `cc2a353` la llevó al Anexo C, la edición (`3cf37fb`) la reemplazó por una remisión a `sec:spill-vecinos` y la verificación (`cb0234a`) la repuso, condensada.
- Corregido:
  - E2 era "peor en todas las métricas", lo que es falso para el throughput;
  - E6 atribuía los no terminados a todos los controles; eran solo de Q-learning;
  - el canal imperfecto en el corredor "sigue muy por debajo del fijo" pasa a +0.6, +4.2 y +5.8 % frente al fijo y +1.7, +5.4 y +7.0 % frente al actuado;
  - en la verificación: el rango −20 a −23 % era de las siete políticas, no de las medianas; la cola de 31 a 33 es una media; se remite a `tab:resumen-escenarios`; cruce también se usa en la prueba de humo; se define la notación 25/25 y la frase de la primera ronda.
- Los captions de las cuatro figuras que quedan se reescribieron (ver sección 5). "Lectura conjunta" pasa a "Lectura del agente tabular". El canal de la red y el del corredor quedan en una sola subsección.

Anexo D, Importación de un cruce desde OSM (nuevo)
- Movido desde el `capitulo4.tex` original: la instalación de SUMO (un párrafo), las herramientas (en prosa), la importación con osmWebWizard, la limpieza (en condicional, como pasos previstos) y randomTrips.
- Eliminado:
  - `conexiones.PNG`, subfigura (b) de `fig:netedit-before-after`. Por qué: muestra otra intersección y su caption afirmaba una limpieza que no ocurrió;
  - `fig:import-osm-sumo` (`OSM.PNG` y `SUMO.PNG`). Por qué: una es una captura de navegador con marcadores personales y la otra repite la red cruda;
  - la sección "Diagrama de flujo del módulo U1" con `fig:flow-u1` (`U1.png`). Por qué: dibuja Azure y Google Maps, y tiene la errata "sumogui";
  - la frase normativa de 3 a 4 s de ámbar;
  - "Actualizar los archivos de configuración";
  - el label `sec:osm-limpieza`.
- Reescrito o corregido:
  - la apertura dice el estado real: importación cruda del 01.12.2025, fuera del repositorio, con la demanda aleatoria del asistente, sin limpiar ni evaluar;
  - "Seleccione Lima, Peru en el buscador" pasa a "se ajusta el bounding box";
  - `NETEDIT.PNG` queda como figura única, con el label `fig:osm-lima-cruda`;
  - en la verificación, la carpeta de la importación en el comentario de fuente y la versión de SUMO de la importación (v1_24_0+1720).

## 5. Figuras y tablas

En la columna "Antes" los capítulos llevan la numeración antigua: "Cap. III" es `capitulo4.tex` y "Cap. IV" es `capitulo5.tex`. En "Después" y "Dónde queda", la nueva.

### Figuras

| Figura (label, archivo) | Antes (numeración antigua) | Después | Qué debería mostrar en su lugar |
|---|---|---|---|
| `fig:diseno` (`Diagrama.png`) | Cap. II | Eliminada; rehecha como `fig:arquitectura` (Figura 3.1) | Ver sección 11 |
| `fig:flow-u1` (`U1.png`) | Cap. III (capitulo4), sección propia | Eliminada; rehecha como `fig:flujo-u1` (Figura 3.2) | Ver sección 11 |
| `fig:flow-u2` (`U2.png`) | Cap. III, U2 | Eliminada; rehecha como `fig:flujo-u2` (Figura 3.3) | Ver sección 11 |
| `fig:netedit-before-after` (`NETEDIT.PNG` + `conexiones.PNG`) | Cap. III, limpieza OSM | `NETEDIT.PNG` sola, como `fig:osm-lima-cruda` (Anexo D); `conexiones.PNG` eliminada | -- |
| `fig:import-osm-sumo` (`OSM.PNG`, `SUMO.PNG`) | Cap. III, importación OSM | Eliminada | -- |
| `fig:cruce-curva`, `fig:cruce-qtable`, `fig:cruce-comparacion`, `fig:cruce-serie`, `fig:cruce-ecdf`, `fig:cruce2-curva`, `fig:cruce2-comparacion`, `fig:corredor-curva`, `fig:corredor-comparacion`, `fig:red-curva`, `fig:red-comparacion`, `fig:cruce-curva-ippo`, `fig:red-curva-ippo`, `fig:corredor-curva-ippo` | Cap. IV (fase exploratoria) | Eliminadas (14) | Ninguna. Las curvas quedan superadas por `fig:plan2-convergencia`; las comparaciones repetían tablas; la serie y la ECDF usan una sola semilla; la Q-table de cruce ilustraba dos cifras |
| `fig:cruce2-qtable`, `fig:red-fases`, `fig:corredor-fases`, `fig:corredor-alta-spillback` | Cap. IV | Anexo C (C.1 a C.4), captions reescritos (ventana de 10 a 15 min, colores, semilla 1001, política del último episodio de la fase exploratoria, 120 episodios, puntos, IC y umbral 34/38), con caption corto | -- |
| `fig:plan2-convergencia` | Cap. IV, entre la matriz y la lectura por caso | Cap. V, `sec:convergencia`. PNG regenerado solo para quitar "v2" del título (`plan2/grafico_convergencia.py`, 2 líneas). Caption: "serie de validación de la base publicada", la banda es el último tercio (episodios 140 a 200), sin "v2" | -- |

### Tablas

| Tabla | Estado | Dónde queda | Fuente o motivo |
|---|---|---|---|
| `tab:pipeline` | Nueva | Cap. III, `sec:vision-general` | Unidad, qué hace, entradas, salidas y programas. Fuente: `capitulo4.tex` original (Alcance y unidades, Resumen de las unidades, P5, párrafo de DQN, Reproducibilidad) y Anexo B original. La verificación movió IPPO a U2 |
| `tab:metricas` | Nueva | Cap. II, `sec:teoria-metricas` | 11 métricas (7 generales y 4 de corredor) con definición y salida de SUMO. Fuente: Cap. II y módulo U3 originales; `comun.py`. TODO para citar la documentación de tripinfo |
| `tab:plan2-resumen` | Nueva | Cap. V, 5.1.1 | Retraso del fijo (media ± IC95) y, por modelo y caso, retraso, Δ_f y veredicto abreviado con el provisional. Fuente: `plan2/veredicto_congelado_0355.csv` (retraso, delta_fijo, veredicto) y la fila fijo de `plan2/evaluacion_<esc>_resumen.csv`. La imprimió un script que solo lee y formatea (`tablas_cap5.py`, en el scratchpad de la sesión, fuera del repositorio) |
| `tab:plan2-metas` | Nueva | Cap. V, 5.1.2 | Las cuatro metas frente al Δ de la política publicada de IPPO vecinos (bases publicadas: P1 4042, P2 2042, P3 4042, P4 42, P5 2042). Fuente: columna `delta_pct` de `plan2/evaluacion_<esc>_resumen.csv`. Se agregó porque las conclusiones citaban metas secundarias que no aparecían en Resultados |
| `tab:escenarios` = `tab:plan2-casos` | Fusionadas (dos labels en una tabla) | Cap. III, `sec:escenarios` | Estaban duplicadas y daban cifras distintas (2152 frente a 2150). Filas P1-P5; salen cruce y cruce2 (al Anexo C, en texto) y P6-P7 (una frase); salen las columnas del programa fijo (vive en `tab:plan2-fijo`) y de fases verdes; se completan los giros que faltaban en P1, P3 y P4 (60, 60 y 72; verificados en los `.rou.xml`). Fuente: flujos de los `.rou.xml`, `demanda_veh_h` del CSV congelado y `vehiculos` de `evaluacion_<esc>_resumen.csv` |
| `tab:plan2-hiper` = `tab:hiper-ippo` | Fusionadas (dos labels en una tabla) | Cap. IV, "Hiperparámetros" | Había dos tablas, y `tab:hiper-ippo` traía el protocolo exploratorio. Se agregan las filas de pérdida y de valores iniciales en cero; la tasa de IPPO "decae linealmente por episodio" (antes "lineal a 0"); en la verificación, "un solo Adam" también en IPPO. Fuente: `rl_corredor.py`, `rl_dqn.py` (HIPER), `rl_ippo.py` (HIPER), `rl_mappo.py` |
| `tab:relacionados` | Modificada | Cap. I | Nueva columna "Referencia" y fila "Esta tesis" (fuente: `veredicto_congelado_0355.md`). En Uniandes, cada cifra lleva su algoritmo (el orden asignaba 63.40 a DQN y 63.49 a PPO, al revés que el texto). Sin negritas en las celdas (el encabezado las conserva). El caption advierte que las métricas no son comparables entre filas |
| `tab:hw` | Movida | Cap. IV, `sec:entorno` | La fila GPU ya no repite la versión de PyTorch |
| `tab:obs-u4` | Movida y modificada | Cap. III, `sec:u4` | Bloque "Identificador" propio (filas 13-15); "verde hacia mí" en las filas 17 y 20; caption con la disposición de 31 y 53 componentes; `\setstretch{1}` |
| `tab:plan2-modelos` | Movida y modificada | Cap. III, `sec:modelos` | Nombres canónicos, orden por familia; "recompensa de colas"; fila MAPPO "misma arquitectura de actor y observación"; caption con spill = vecinos y `ql_colas` sin P5 |
| `tab:plan2-semillas` | Movida | Cap. III, `sec:protocolo`, tras las definiciones | "Todos los controles" en lugar de "brazos"; la calibración de P2 en la fila de tuneo |
| `tab:red-alta-factor` | Movida | Cap. IV, `sec:calibracion` | En la verificación, el caption define "Espera máx. para entrar" (queda un TODO sobre cómo se agrega) |
| `tab:plan2-fijo` | Movida | Cap. IV, `sec:referencias-fijas` | Caption "por caso" en lugar de "por celda" |
| `tab:plan2-costo` | Movida | Cap. IV, `sec:ejecucion` | Caption: "= vecinos: la celda repite a IPPO vecinos; sus entrenamientos de confirmación no se incluyen" (antes "no se entrenó aparte", falso) |
| `veredicto_actuado`, `veredicto_ql`, `veredicto_ippo_vecinos` (generadas) | Movidas dentro del Cap. V | Inicio de `sec:lectura-caso` | Se citaban antes de aparecer |
| Tablas generadas del Anexo A y la matriz | Sin cambios | Anexo A y Cap. V | No se regeneraron (ver sección 8) |
| 19 tablas generadas exploratorias: `cruce_episodios`, `cruce2_episodios`, `corredor_episodios`, `red_episodios`, `corredor_alta_episodios`, `cruce_ippo_episodios`, `red_ippo_episodios`, `corredor_ippo_episodios`, `corredor_alta_ippo_episodios`, `cruce_episodios_resumen`, `cruce2_episodios_resumen`, `corredor_episodios_resumen`, `red_episodios_resumen`, `cruce_evaluacion`, `corredor_evaluacion`, `red_evaluacion`, `red_fragilidad`, `corredor_fragilidad`, `corredor_alta_fragilidad` | Eliminadas del documento (los archivos siguen en `TESIS/secciones/tablas/`) | -- | Por episodio (unas 950 filas): protocolo reemplazado y no se citaban; su texto afirmaba en falso que eran reproducibles "con los comandos del plan". Resúmenes por episodio: subconjuntos (dos con 26 y 27 filas). `*_evaluacion`: repetían columnas de las `*_u4` (se conserva `cruce2_evaluacion`, porque cruce2 no tiene `*_u4`). `*_fragilidad`: las supera `veredicto_bases` del Anexo A. No hace falta nada en su lugar |
| 13 tablas generadas del Anexo C (`resumen_escenarios`, `cruce2_evaluacion`, `resumen_u4`, `cruce_u4`, `red_u4`, `corredor_u4` y `corredor_alta_u4`, las cuatro con su tabla de deltas, `red_s1`, `corredor_s1`) | Conservadas, sin tocar | Anexo C | No se regeneraron |

## 6. Variables, notación y terminología

| Símbolo o término | Decisión | Antes | Dónde se define |
|---|---|---|---|
| i, j | i = semáforo (agente); j = aproximación, en el orden del código O, E, N, S | c_i con dos sentidos; `a` como índice de aproximación (a es la acción); orden N, S, E, O de `rl_semaforo.py` | Cap. III, `sec:formulacion` |
| J_i | Conjunto de aproximaciones del semáforo i | `\mathcal{A}_i` y ∑_a, que chocaban con el conjunto de acciones del MDP | Cap. III, `eq:recompensa-u4` |
| L_i, ℓ (`\ell`) | Enlaces que salen de i hacia sus vecinos; ℓ, índice de enlace | "salidas_i", luego `\mathcal{S}_i` (chocaba con el espacio de estados) y `e` (chocaba con la espera e_j en la misma ecuación) | Cap. III, `eq:recompensa-u4`; también en `ret_spill` (`sec:u3`) y en el Anexo C. En GAE, `l` es solo el índice de la suma |
| q_ℓ(t) | Máximo por carril de vehículos detenidos en el enlace ℓ | q_e | Cap. III, `eq:recompensa-u4` |
| K_ℓ, ⌊K_ℓ/2⌋ | Plazas por carril (38; 37 en malla3) y umbral del término de spillback | P_e y P_e/2 (P es la transición del MDP; el código usa división entera: en malla3 el umbral es 18, no 18.5). El plan maestro proponía q_e y P_e; la verificación lo cambió. Las épocas de PPO no llevan símbolo, para no chocar con K_ℓ | Cap. III, `eq:recompensa-u4` |
| h_j, b_j = b(h_j), φ, s | Detenidos; nivel 0 a 3 (0; 1-3; 4-8; >8); fase verde activa; s = (b_O, b_E, b_N, b_S, φ), 512 estados | s = (c_N, c_S, c_E, c_O, f), con f en conflicto con el factor de demanda | Cap. III, `sec:formulacion` |
| n_j, v̄_j, v_max,j, e_j, T_i, w_1, w_2, w_3 | Presentes, velocidad media, 13.89 m/s, suma de esperas, segundos desde la decisión anterior; w_1 = 1, w_2 = 0.01, w_3 = 2 solo en spill | Sin v_max ni el intervalo definidos | Cap. III, `sec:formulacion` |
| ε y ε_clip | ε = exploración; ε_clip = recorte de PPO (0.2), nunca ε | -- | Cap. II, `sec:rl` y `eq:ppo-clip`; valores en `tab:plan2-hiper` |
| α, γ, λ, ρ_t, θ, θ⁻ | α solo como tasa tabular (en redes se dice "tasa de aprendizaje"); γ descuento; λ de GAE; ρ_t razón de probabilidades (para no confundirla con r); θ⁻ red objetivo | γ con valores pero sin definir | Cap. II (`eq:td`, `eq:retorno`, `eq:gae`, `eq:ppo-razon`, `eq:dqn`) |
| N, f, d, n | N = 200 episodios; f = factor de demanda (2.0 en P2, 1.2 en P4); d = dimensión de la observación (31 o 53); n = número de semáforos | -- | Cap. III (`sec:protocolo`, `sec:escenarios`); Cap. IV (`tab:plan2-hiper`) |
| Δ, Δ_f, Δ_a | (x̄_m − x̄_ref)/x̄_ref × 100 sobre las semillas comunes, pareado por semilla; negativo = menos retraso | Δ sin definir; Δ recompensa aparecía antes que Δ | Cap. III, `eq:delta` (`sec:estadistica`); el Cap. V remite |
| Δ recompensa | Dividido entre el valor absoluto de la media de la referencia; positivo = más recompensa | Normalización explicada tres veces | Cap. III, `sec:estadistica`; aviso de signo en el Cap. V y en la conclusión 2 |
| Semilla base (base) | 42, 2042 y 4042; el episodio k usa base+k | -- | Cap. III, `sec:protocolo` |
| Validación | Semillas 999 y 1999, cada 10 episodios y en el último; media del retraso | -- | Cap. III, `sec:protocolo` |
| Checkpoint | Copia de la tabla Q o de los pesos en cada validación | Sin definir | Cap. III, `sec:protocolo` |
| Política publicada | El checkpoint con menor validación de un entrenamiento (en empate, el más tardío) | Usada también para la base mediana | Cap. III, `sec:protocolo` |
| Base publicada | La mediana de las tres bases por ese valor. La regla de empate "la base menor" se quitó en la verificación porque el código ordena por (valor, base) | -- | Cap. III, `sec:protocolo` |
| Celda | Un modelo en un caso | Usada también como "caso" | Cap. III, `sec:plan2` ("Pregunta de cada prueba") |
| Fragilidad | Rango (máximo menos mínimo) del retraso de evaluación entre bases, comparado con el IC de una política | Sin definición operativa | Cap. III, `sec:protocolo` |
| Convergencia | Meseta y estabilidad de a lo sumo 5 % en el último tercio de las validaciones de la base publicada; mide el entrenamiento, no el checkpoint | Usada antes de definirse | Cap. III, `sec:veredicto`; concepto en Cap. II, `sec:evaluacion` |
| Fijo tuneado / actuado | El programa fijo ajustado por barrido en cada caso / el actuado nativo de SUMO | "fijo coordinado", "fijo en ajedrez", "de la celda" | Introducción (Formulación), Cap. III (`sec:modelos`), Cap. V (apertura) |
| Plan de pruebas / fase exploratoria / etapa / fase | "Plan de pruebas" sin "v2" en el texto, en los captions, en los títulos del Anexo B y en el título del PNG; "fase exploratoria" para lo anterior; "etapa" para la etapa del proyecto; "fase" solo para la fase semafórica | "plan v2"; "fase" con dos sentidos | Introducción; Cap. III, `sec:plan2` |
| P1-P5 y E1-E6 | Los casos se nombran con su escenario ("P3, red"); E1-E6 solo en el Anexo C (E6 no se renumeró a E5) | E1-E6 en el Cap. III, el Cap. V y las conclusiones | Anexo C, apertura |
| "Brazo" | Eliminado del texto; solo queda en la opción `--brazo` de un comando | Usado en el texto | -- |
| Modelos | fijo, actuado, Q-learning, SARSA, `ql_colas`, DQN (un Double DQN, dicho al definirlo), IPPO local, vecinos y spill, MAPPO | Nombres variables | Cap. III, `tab:plan2-modelos` |
| MAPPO y spill frente a IPPO vecinos | "Comparten la arquitectura (o la red) del actor y la observación con mensajes; cada uno entrena su propia política" | "usa el actor de IPPO vecinos", "usan la política de IPPO con mensajes" | Cap. III, `sec:modelos`; Cap. IV, MAPPO |
| Valores p | El redondeo del documento original | La edición los pasó a la precisión de las tablas; la verificación lo revirtió | Cap. V |
| PENDIENTE | Seis celdas: cinco por no convergencia (con veredicto provisional) y una sin datos | "Cinco" | Cap. V, 5.1.1; Introducción; Conclusiones |

Restos que no se unificaron (ver sección 8):
- Las tablas generadas por `veredicto.py` todavía dicen "Política publicada = mediana de las tres semillas base" y "Conv.: si convergió la política publicada", nombran `ql_colas` como "Q-learning (colas)" y remiten a "la regla de la sección de métodos" sin `\ref`.
- `anexos.tex:24` dice "La publicada es la mediana de las tres por la validación"; debería decir "la base publicada".
- `anexos.tex:54` dice "cuya política publicada no convergió"; debería decir "base publicada".
- "Fijo coordinado" sigue en `conclusiones.tex` (líneas 88, 100, 125, 198 y 214), en `recomendaciones.tex` (127, "fijo coordinado en ajedrez", y 131), en `resumen.tex:13` ("iguala a un fijo coordinado") y en `abstract.tex:15` ("a coordinated fixed-time program"), pese a la decisión de la fila "Fijo tuneado / actuado". En alguna frase puede ser intencional (en `conclusiones.tex:88` se refiere al fijo con desfases, frente al mejor sin desfases); lo decide el autor.

## 7. Verificación adversarial

Qué se revisó. Siete verificadores de grupo contrastaron cada capítulo con el original (`7bd8685`), el código (`rl_*.py`, `comun.py`, `consolidar.py`, `veredicto.py`), `plan2/ESPEC.md` y los CSV congelados:
- teoría: Cap. II;
- metodología: Cap. III;
- implementación: Cap. IV;
- resultados: Cap. V;
- preliminares: resumen, abstract, introducción y Cap. I;
- cierre: conclusiones y recomendaciones;
- anexos: A a D.

Además, un lector global leyó el documento completo. Buscaron errores, invenciones (afirmaciones sin respaldo en el original ni en las fuentes), pérdidas (salvedades o datos que desaparecieron) y problemas de legibilidad.

Cuántos hallazgos. Hubo 141: 5 de severidad alta, 49 media y 87 baja. Por tipo: 53 errores, 48 de legibilidad, 22 pérdidas y 18 invenciones. Los correctores registraron 140 decisiones: 75 aplicadas tal cual, 59 aplicadas con cambios y 6 rechazadas. El recuento no es uno a uno, porque los hallazgos del lector global se repartieron entre los grupos y algunos se atendieron junto con el equivalente del grupo. Seis decisiones transversales se aplicaron en todos los archivos:
- la notación J_i, L_i, ℓ, q_ℓ y K_ℓ;
- el redondeo original de los valores p;
- las métricas de corredor: no se analizan en el Cap. V, se dice que no se analizan y queda un TODO;
- la redacción sobre MAPPO y spill;
- las seis celdas pendientes;
- marcar como exploratorio el −35 % de la prueba de humo.

La comprobación final de compilación no cambió ningún archivo.

Los cinco hallazgos de severidad alta y qué se hizo:
- Anexo C, E3: el +60 % del tabular quedaba como lectura vigente. Se agregó que el plan lo redujo a +10.6 % (recompensa de colas) y +9.2 % (retraso) en P1, sobre todo por el protocolo.
- Anexo C, E6: el tabular aparecía un 37 % por encima del fijo sin aviso. Se agregó que en P2 Q-learning mejora un 8.8 % (MEJORA), sin dejar vehículos sin terminar.
- Conclusiones: el indicio exploratorio de progresión se presentaba como vigente, aunque el CSV del plan lo contradice en P3. Quedó como "observación sin confirmar en el plan", con TODO y las cifras solo en el comentario.
- Cap. V: no reporta las métricas de corredor que prometen la Introducción, el Cap. I y el Cap. III. Se atendió solo en parte: una frase dice que se registraron y no se analizan, y queda un TODO. No se agregó la tabla que se proponía.
- Cap. V: "Qué funciona, dónde y cuánto" había perdido el "cuánto". Se restituyeron las magnitudes (6.8, 23.3, 8.8 y 3.6 %; +1.8 % con p = 0.52; 3.6 a 16.4 % frente al actuado).

Otras correcciones importantes:
- Cap. IV: la siembra del generador (la edición había agregado una afirmación falsa).
- Cap. IV: las siete evaluaciones de spill nunca se lanzaron.
- Cap. IV: 16 y 20 de 38 plazas eran la cola total de la red. Se reemplazaron por 7.9 de 38 (máximo 10) con el fijo tuneado de P1.
- Cap. IV: el −35 % de la prueba de humo, marcado como fase exploratoria.
- Cap. III: la notación de la recompensa (J_i, L_i, ℓ, K_ℓ) y el reparto U2/U4 en `tab:pipeline`.
- Cap. III: se quitaron la regla de empate de la base mediana (no coincide con el código) y la paráfrasis causal de la introducción de U4.
- Cap. II: la política tabular congelada desempata al azar; los retornos se miden con todos los controles; la recompensa de spill cubre los enlaces de salida; FHWA cap. 3 se retiró de desfase y onda verde; la condición de la pérdida combinada de PPO.
- Introducción: se quitaron las citas FHWA/HCM que la edición había agregado sin respaldo; el objetivo U4 se restauró; "plan de siete casos, cinco ejecutados".
- Resumen y abstract: la selección por validación en semillas propias y la base mediana; que MAPPO no convergió en P3 y P4; el párrafo de resultados, dividido.
- Cap. I: la limitación de Uniandes vuelve al sentido original; "se atienden en parte"; la frase de Sistemas Distribuidos se repuso.
- Cap. V: los valores p vuelven al redondeo original; seis celdas pendientes (5 + 1); se repusieron salvedades (`ql_colas` sin P5, fragilidad en dos de tres bases, IPPO local detrás del actuado en P5).
- Conclusiones: la salvedad del IC bootstrap de P5; MAPPO frente a DQN en P4; la convención de signo de Δ recompensa; el acuerdo con el asesor del 23.09.2026.
- Recomendaciones: `cola_mi_salida` (qué coincide y quién la usa), la cota del throughput (+0.6 %) y P6/P7 declarados como estimaciones.
- Anexos: la excepción de P2 en `ql_colas`, las dos filas de spill en P3, la fragilidad de P3 en el Anexo C y la versión de SUMO de la importación de Lima.

Una corrección de la edición se perdió en la verificación: en la conclusión 6, `ad26402` había dejado a DQN "por detrás de IPPO vecinos", y `024e23e`, al dividir el párrafo, volvió a "IPPO vecinos y MAPPO quedan a la par y DQN por detrás" (`conclusiones.tex:221`). Ver la sección 8.

Algunas correcciones de la verificación no dejan cambio neto frente a `7bd8685`, porque deshacen algo que la propia edición había introducido o quitado. En la sección 4 van marcadas "[sin cambio neto]": la regla de empate "la base menor" y la metáfora "escalera" (Cap. III), el símbolo K de las épocas de PPO (Cap. II) y la identidad bit a bit de spill (Anexo C).

Rechazados, y por qué:
- Cap. IV, frase de 16/20 plazas "bajo el fijo con que se calibró ese factor" (lector global): la propuesta era falsa, porque el factor se calibró con el actuado. El problema de fondo se resolvió de otra forma (7.9 de 38).
- Cap. IV, detalle de 0.1 m/s duplicado con el Cap. III (lector global): el editor del Cap. IV no cambió nada. El duplicado se quitó del lado del Cap. III.
- Recomendaciones, viabilidad de P6/P7 (grupo de resultados): no era su archivo. El grupo de cierre sí lo aplicó.
- Cap. IV, cifras del prototipo de malla3 (21.6, 26.0 y 25.4 s) (grupo de resultados): no era su archivo, y nadie las repuso. Quedan fuera de la tesis (ver sección 8).
- Notación del Cap. III y citas de la introducción (dos rechazos del grupo de teoría): no eran sus archivos. Las aplicaron los grupos de metodología y de preliminares.

Además, dentro de las decisiones "aplicado con cambios" se descartaron varias redacciones propuestas por inventar o generalizar:
- "cae dentro de los intervalos" (DQN en P4);
- "ninguna política publicada" (P4);
- "ningún control del plan aumentó el throughput" (falso: IPPO local sube un 0.58 %);
- "no se contrasta con las metas" (sin fuente);
- "todas las políticas IPPO usan `cola_mi_salida`" (falso para local).

## 8. Pendientes para el autor

### TODO en el texto (30, líneas al día tras la sección 11)

Referencias que faltan en el `.bib`, con la obra identificada (10):
- `capitulo2.tex:346`: optimizador Adam (Kingma y Ba, 2015) y una fuente para el recorte de la norma del gradiente.
- `capitulo2.tex:373`: pérdida de Huber (Huber, 1964) o la documentación de `smooth_l1_loss` de PyTorch.
- `capitulo2.tex:390`: Double DQN (van Hasselt, Guez y Silver, 2016).
- `capitulo2.tex:437`: GAE (Schulman, Moritz, Levine, Jordan y Abbeel, 2016).
- `capitulo2.tex:537`: IPPO (de Witt et al., 2020).
- `capitulo2.tex:613`: bootstrap (Efron y Tibshirani, 1993), prueba de Wilcoxon (Wilcoxon, 1945) e intervalo con t de Student.
- `capitulo3.tex:905`: las mismas del bootstrap percentil pareado y de Wilcoxon (una misma entrada del `.bib` resuelve este TODO y el anterior).
- `capitulo1.tex:11`: trabajos de RL multiagente aplicados a semáforos (CoLight, PressLight, MPLight, banco RESCO) como comparación natural de U4. Además de la entrada, hay que leer las fuentes.
- `capitulo2.tex:35`: documentación de SUMO del modelo de seguimiento por defecto (Krauss, σ, speedFactor).
- `capitulo2.tex:154`: documentación de la salida `tripinfo` de SUMO (timeLoss, waitingTime, waitingCount).

Referencias que faltan, sin obra identificada (7):
- `introduccion.tex:6`: estudio o informe de movilidad de Lima Metropolitana para la afirmación sobre la congestión.
- `introduccion.tex:14`: fuente de ingeniería de tránsito para la pérdida de vigencia del fijo cuando cambia el sentido dominante y para la falta de anticipación del actuado aislado.
- `capitulo2.tex:102`: progresión en los dos sentidos y desfases alternados de medio ciclo ("en ajedrez"), del capítulo de coordinación del manual de la FHWA o del HCM.
- `capitulo2.tex:513`: formalización del caso con recompensas individuales por agente (juego estocástico parcialmente observable).
- `capitulo2.tex:553`: RL multiagente con comunicación entre agentes (Yu2021_MAPPO no la trata).
- `capitulo2.tex:583`: selección de modelo por validación o parada temprana y, opcional, variabilidad entre semillas en RL profundo.
- `capitulo3.tex:979`: fuente de diseño experimental para el umbral del 5 % (veredicto y convergencia) y la exigencia conjunta de IC bootstrap y p de Wilcoxon (hoy solo consta en `plan2/ESPEC.md`, sección 7).

Verificaciones de fuentes ya citadas (4):
- `capitulo1.tex:111`: que Chavez2023 usa SUMO (el texto solo dice "escenario simulado").
- `capitulo1.tex:124`: que UAQ2024 usa SUMO (el texto solo dice "microsimulador").
- `capitulo2.tex:67`: la sección del HCM 2010 que define fase, ciclo, reparto, desfase, verdes, control prefijado y actuado y progresión. El capítulo 3 de la FHWA citado no los define.
- `capitulo2.tex:202`: que SuttonBarto2018 (sec. 17.2) trate los procesos semi-markovianos; si no, citar Sutton, Precup y Singh (1999).

Diagramas por dibujar: resueltos en la segunda parte (sección 11); sus tres TODO (`capitulo2.tex:14`, `capitulo3.tex:71` y `capitulo4.tex:575` de `2ab0d04`) se borraron.

Análisis pendiente de las métricas de corredor del plan (2):
- `capitulo5.tex:539` y `conclusiones.tex:246`: analizar `paradas_corredor_le1` y `retraso_corredor_punta` de `plan2/evaluacion_<esc>_resumen.csv`. La lectura preliminar del TODO: en P3 la política publicada de IPPO vecinos tiene menos progresión que el fijo (0.93 frente a 0.99).
  - En los reportes de corrección figura además, verificado contra el CSV: P3, fijo 0.9864 frente a IPPO vecinos base 4042 0.9293; P1, fijo 0.903, vecinos 0.930 y actuado 0.727.
  - El lector global reportó, sin que se reverificara, P5 0.91 frente a 0.99 y un retraso de corredor en punta de 26.9 frente a 24.4 s en P3.
  - Afecta al objetivo U4 ("impacto a nivel de corredor"), al Cap. I (lección de UAQ), al Cap. III (`sec:u3`) y al segundo párrafo final de las conclusiones.

Datos faltantes o por confirmar (5):
- `capitulo3.tex:738`: el número de vehículos de extremo a extremo en corredor_alta, red_alta y malla3. Se obtendría contando en los `.rou.xml` los flujos de `flujos_corredor`.
- `capitulo4.tex:281`: a qué programa fijo de corredor corresponden los 80 a 94 vehículos sin terminar en P2 y qué archivo lo respalda.
- `capitulo4.tex:345`: la columna "Espera máx. para entrar" de `tab:red-alta-factor` trae un solo valor por factor. Confirmar si es el máximo de las tres semillas (ningún script la calcula).
- `capitulo4.tex:831`: el gradiente del crítico, "130 veces" en el texto y en LEEME.txt y "~100" en el comentario de `rl_ippo.actualizar`. Confirmar con `humo/humo1_s42_recorte_global.csv` y unificar el código y su copia en `TESIS/codigo/`.
- `anexo_c_exploratoria.tex:441`: el "límite de 2 s del criterio de robustez" del texto original no se define en ninguna parte. Definirlo con su fuente o dejar solo las diferencias en segundos.

Justificaciones que solo puede dar el autor (2):
- `capitulo1.tex:70`: por qué no se implementó A2C, que Trinity recomienda junto a PPO.
- `introduccion.tex:31`: de dónde salen las metas (25-40 %, 20 %, 10 %, 5 %). Como contexto, el Cap. I cita reducciones de 35.79 a 63.49 % del tiempo de espera (Chavez2023) y de hasta 36.34 % del tiempo de viaje (UAQ2024).

### Decisiones que quedan al autor

Resueltas al final, en `2ab0d04` (las detectó el crítico del changelog):
- `conclusiones.tex` (conclusión 6): "IPPO vecinos y MAPPO quedan a la par y DQN por detrás" contradecía P4 (DQN 29.04 s, MAPPO 29.45 s); la edición lo había corregido y `024e23e` lo reintrodujo. Ahora: IPPO vecinos tiene menos retraso que DQN en los cinco casos y MAPPO en cuatro.
- `introduccion.tex:86`: "sin GPU" pasa a "sin usar la GPU".
- `anexos.tex:24` y `anexos.tex:54`: "base publicada" donde decía "publicada" y "política publicada no convergió".
- Nota de `cola_mi_salida` del Cap. IV: excluye a IPPO local, que tiene a cero las ranuras de los vecinos (coincide con las recomendaciones).
- El script que imprimió `tab:plan2-resumen` y `tab:plan2-metas` está ahora en `plan2/tablas_cap5.py` (salida idéntica a la usada) y los comentarios `% fuente` del Cap. V lo nombran.
- El skill `escribir-tesis` ya dice que `anexos.tex` usa `\customchapter`.

Siguen abiertas:
- Regenerar las tablas con `veredicto.py` para corregir sus captions (base publicada, "Q-learning (colas)", la remisión sin `\ref`, PENDIENTE sin provisional, columnas vacías en `veredicto_actuado`). No se hizo porque la cola siguió corriendo después del cierre y las tablas regeneradas podrían no coincidir con las congeladas. Lo mismo vale para las tablas exploratorias de `tablas_tex.py` (columna "RL", caption de `cruce_u4` con "mediana de sus semillas base" pese a tener una sola base, filas en cero).
- Las cifras del prototipo de malla3 (corregido 21.6 s, cruzado 26.0 s, actuado 25.4 s, con las semillas 2001-2003) ya no están en la tesis. Si se quieren, van en el Cap. IV, `sec:construccion`.
- Cap. I, `sec:implicancias`: se mantiene "los tres entrenamientos con mensajes tienen menos retraso que los tres sin ellos", que en las conclusiones se eliminó por ser una comparación de medias sin prueba pareada (en P2, 119.02 frente a 119.27 s). Decidir si se califica, se quita o se respalda con la prueba pareada (`plan2/evaluacion_<esc>.csv`).
- Recomendaciones, P6 y P7: la edición había quitado "P6 cabría en una noche" y "P7 alcanzable [para IPPO] en una noche"; la verificación los restituyó del original, declarados como estimaciones. Confirmar si se quieren.
- El objetivo U4 dice "colas/salidas previstas", pero los mensajes implementados no incluyen una predicción. Hoy lo explica la nota que sigue a los objetivos; decidir si se ajusta el objetivo.
- El "Problema central" sigue redactado como tarea ("Crear un modelo...") y el objetivo U1 sigue diciendo "Recopilar y preprocesar datos de tráfico". La nota que sigue a los objetivos aclara que esta etapa usa escenarios sintéticos.
- "Fijo coordinado" en las conclusiones, las recomendaciones, el resumen y el abstract (lista en la sección 6): decidir si pasa a "fijo tuneado" o se conserva donde el matiz importa.
- En `sec:calibracion`, la frase heredada "así el término de spillback no se activaría" (bajo el fijo) convive con `sec:spill-vecinos`, que dice que en el corredor el término sí se activa durante el entrenamiento. Se refieren a controles distintos, pero puede leerse como contradicción.
- Formato:
  - `recomendaciones.tex` conserva el encabezado manual (`\chapter*`), mientras `anexos.tex` pasó a `\customchapter`;
  - el Anexo C ocupa unas 20 páginas (215 a 234 según `main.toc`), tanto como el Cap. II y más que el Cap. V (16);
  - E6 no se renumeró a E5.
- `plan2/captura_corredor.png` (sin versionar) se propuso como figura de P1 en `sec:escenarios`; no se usó.
- `build_net.bat` no tiene listado en el Anexo B, solo se nombra. El Cap. IV muestra el comando del corredor.
- `SB3_Docs` dejó de citarse y ya no sale en la bibliografía; la entrada sigue en `referencias.bib`.

## 9. Archivos para Overleaf e imágenes sin uso

Hay que subir:
- `TESIS/main.tex` (una línea nueva: `\input{secciones/capitulo3}`).
- `TESIS/secciones/`: `resumen.tex`, `abstract.tex`, `introduccion.tex`, `capitulo1.tex`, `capitulo2.tex`, `capitulo3.tex` (nuevo; si en Overleaf existe uno vacío, se reemplaza), `capitulo4.tex`, `capitulo5.tex`, `conclusiones.tex`, `recomendaciones.tex`, `anexos.tex`, `anexo_c_exploratoria.tex` (nuevo) y `anexo_d_osm.tex` (nuevo).
- `TESIS/images/fig_plan2_convergencia.png` (regenerada solo para quitar "v2" del título).
- `TESIS/images/diag_arquitectura.pdf`, `diag_u1.pdf`, `diag_u2.pdf`, `diag_u3.pdf` y `diag_u4.pdf` (sección 11). La carpeta `TESIS/diagramas/` (fuentes TikZ) no hace falta en Overleaf: las figuras se compilan aparte.

No cambiaron: `TESIS/secciones/tablas/`, `TESIS/codigo/`, `referencias.bib`, `tesisutec.cls` ni las demás imágenes.

Fuera de `TESIS/` cambiaron `CLAUDE.md` (mapa de capítulos al día y remisión a este archivo), `.claude/skills/escribir-tesis/SKILL.md` (mapa de capítulos nuevo) `plan2/grafico_convergencia.py` (título sin "v2") con su salida `plan2/fig_plan2_convergencia.png`, y `plan2/tablas_cap5.py` (nuevo). En el árbol de trabajo hay además `plan2/resultados_malla3.csv` modificado y `plan2/captura_corredor.png` y `plan2/capturas.py` sin versionar. No forman parte de la reestructura.

Este changelog (`CAMBIOS_reestructura_tesis.md`) está versionado en la rama, en el último commit.

Imágenes de `TESIS/images/` que ningún `.tex` incluye (comprobado con grep de `\includegraphics`). Se pueden borrar de Overleaf:
- Liberadas por esta reestructura (20):
  - `Diagrama.png`, `U1.png`, `U2.png` (reemplazadas por los `diag_*.pdf` de la sección 11);
  - `OSM.PNG`, `SUMO.PNG`, `conexiones.PNG`;
  - `fig_cruce_curva.png`, `fig_cruce_qtable.png`, `fig_cruce_comparacion.png`, `fig_cruce_serie.png`, `fig_cruce_ecdf.png`, `fig_cruce_curva_ippo.png`;
  - `fig_cruce2_curva.png`, `fig_cruce2_comparacion.png`;
  - `fig_corredor_curva.png`, `fig_corredor_comparacion.png`, `fig_corredor_curva_ippo.png`;
  - `fig_red_curva.png`, `fig_red_comparacion.png`, `fig_red_curva_ippo.png`.
- Ya sin uso en `7bd8685` (15):
  - `fig_cruce2_ecdf.png`, `fig_cruce2_serie.png`;
  - `fig_corredor_ecdf.png`, `fig_corredor_qtable.png`, `fig_corredor_serie.png`;
  - `fig_red_ecdf.png`, `fig_red_qtable.png`, `fig_red_serie.png`;
  - `fig_corredor_alta_comparacion.png`, `fig_corredor_alta_curva.png`, `fig_corredor_alta_curva_ippo.png`, `fig_corredor_alta_ecdf.png`, `fig_corredor_alta_fases.png`, `fig_corredor_alta_qtable.png`, `fig_corredor_alta_serie.png`.

Siguen en uso: `NETEDIT.PNG`, `fig_cruce2_qtable.png`, `fig_red_fases.png`, `fig_corredor_fases.png`, `fig_corredor_alta_spillback.png` y `fig_plan2_convergencia.png`. `ORCID128px.png` y `logo_utec.png` no aparecen en ningún `.tex`, pero las usa `tesisutec.cls`: no se deben borrar.

Opcional: las 19 tablas generadas que ya no se incluyen siguen en `TESIS/secciones/tablas/` (lista en la sección 5). Otras 5 ya no se incluían en `7bd8685`: `corredor_alta_episodios_resumen`, `corredor_alta_evaluacion`, `corredor_alta_s1`, `cruce_fragilidad` y `cruce_s1`.

## 10. Cómo revertir

| Commit | Contenido |
|---|---|
| `cc2a353` | Estructura. Traslado de bloques por script, sin reescribir párrafos: `capitulo4.tex` se reparte en `capitulo3.tex` (nuevo), `capitulo4.tex`, `capitulo2.tex` (ecuaciones Q-learning/SARSA y `\theequation`), `anexo_d_osm.tex` (nuevo) y `anexo_c_exploratoria.tex` (nuevo, con la fase exploratoria del antiguo Cap. IV, `capitulo5.tex`, la historia del fijo en dos rondas y las tablas por episodio del Anexo A). Sí cambia encabezados: `\chapter{IMPLEMENTACIÓN}` en `capitulo4.tex`, `\section*{Anexo C...}` y `\section*{Anexo D...}`, y "Plan de pruebas v2: tablas completas" pasa a `\section*{Anexo A. Tablas completas del plan de pruebas}`. Quita el `\graphicspath` duplicado de `capitulo4.tex` (queda el de `main.tex`). Cambian además `anexos.tex` y `main.tex` |
| `8378f19` | Marco teórico: Cap. II reescrito con ecuaciones |
| `7c63dbe` | Metodología: Cap. III reescrito |
| `1eefa58` | Implementación: Cap. IV reescrito |
| `432c397` | Resultados: Cap. V solo con el plan; `fig_plan2_convergencia.png` (TESIS y plan2) y `plan2/grafico_convergencia.py` |
| `d650f3f` | Introducción, resumen y abstract (zonas protegidas) |
| `8836a27` | Estado del arte: Cap. I |
| `ad26402` | Conclusiones y recomendaciones |
| `3cf37fb` | Anexos A, B, C y D |
| `746a0c3` | Verificación: Cap. II y Cap. III (notación de la recompensa y precisiones) |
| `5576363` | Verificación: Cap. IV |
| `094740a` | Verificación: Cap. V |
| `e242aac` | Verificación: introducción, resumen, abstract y Cap. I |
| `024e23e` | Verificación: conclusiones y recomendaciones |
| `cb0234a` | Verificación: anexos |
| `5bde6b3` | Documentación: `CLAUDE.md` y el skill `escribir-tesis` (no toca `TESIS/`) |
| `2ab0d04` | Cierre: correcciones precisas detectadas al contrastar este changelog con el diff (conclusión 6, "sin GPU", "base publicada" en el Anexo A, nota de `cola_mi_salida`, `plan2/tablas_cap5.py`, skill) |
| `b82354c` | Este changelog (primera parte) |
| `014f86a` | Diagramas: fuentes TikZ, estilo común, `construir.py`, especificación y los cinco `diag_*.pdf` |
| `63109a4` | Integración de los diagramas en el Cap. III, citas desde el Cap. IV y la introducción, `tab:pipeline` renombrada y correcciones D4 y D11 |
| `7e61432` | `CLAUDE.md`: el cruce de Lima no se limpió en netedit |
| (último) | Este changelog con la sección 11 |

Aviso: los commits por capítulo no son independientes.
- Los capítulos se citan entre sí por label. El Cap. IV remite a 13 labels del Cap. III y el Cap. V a 12; el Cap. III remite a 11 del Cap. IV y a 9 del Cap. II; la introducción, las conclusiones, las recomendaciones y los anexos remiten a labels nuevos (`cap:*`, `sec:protocolo`, `sec:veredicto`, `eq:delta`, `tab:plan2-resumen`, etc.).
- Revertir un solo commit de capítulo puede dejar `\ref` sin resolver o duplicar contenido. Por ejemplo, restaurar solo el `capitulo4.tex` original repetiría lo que ya está en `capitulo3.tex` y en los anexos.
- Los commits de verificación modifican el texto de los de edición y pueden dar conflictos si se revierte uno sin el otro.

El estado previo completo es `7bd8685`, que sigue siendo la punta de `main`. Para volver a él basta con quedarse en `main` o cambiar a esa rama. Para recuperar un párrafo concreto se puede usar `git show 7bd8685:TESIS/secciones/<archivo>.tex` y copiarlo a mano. Hay que tener en cuenta que en `7bd8685` la metodología está en `capitulo4.tex` y los resultados en `capitulo5.tex`.

## 11. Segunda parte: diagramas de arquitectura y de U1 a U4

Pedido del autor, tras la primera parte: devolver los diagramas que se habían quitado (arquitectura, U1 y U2), pero rehechos por completo y coherentes con la implementación actual, y agregar los de U3 y U4, que nunca existieron. Commits `014f86a` (diagramas), `63109a4` (integración en la tesis) y `7e61432` (`CLAUDE.md`).

### Cómo se hicieron

1. Análisis: cinco fichas, una por diagrama, sacadas del código (`rl_corredor.py`, `rl_ippo.py`, `rl_dqn.py`, `rl_mappo.py`, `comun.py`, `evaluar.py`, `consolidar.py`, `veredicto.py`, `barrer_fijo.py`, `escenarios_plan2.py`, `build_net.bat`, `plan2/generar_trabajos.py`) y del texto actual, con evidencia `archivo:línea` para cada nodo y cada flecha.
2. Especificación única: qué muestra cada figura, con qué nivel de detalle y cómo se relacionan. Dos críticos la revisaron, uno de fidelidad al código y otro de claridad. Está en `TESIS/diagramas/especificacion.md`.
3. Dibujo en TikZ, compilado aparte con `standalone` (la plantilla no carga TikZ y sus paquetes no se tocan). Cada figura pasó por su dibujante, un revisor independiente (visual y de fidelidad) y una corrección, y después por una revisión cruzada de las cinco.
4. Integración en el Cap. III y verificación de los textos nuevos contra el dibujo y el código.

### Qué muestra cada figura

| Figura | Dónde | Qué responde |
|---|---|---|
| 3.1 `fig:arquitectura` (`diag_arquitectura.pdf`) | `sec:vision-general` | Cómo se conectan U1 a U4, qué información intercambian (I1 a I8) y por dónde entra cada conjunto de semillas. U3 contiene SUMO + TraCI y la cadena de evaluación; U2 y U4 comparten una barra de "aprendices" porque intercambian lo mismo con U3; el cruce de Lima aparece en punteado, previsto y no usado |
| 3.2 `fig:flujo-u1` | `sec:escenarios` | Cómo se construye cada caso: red (`netconvert`), demanda (flujos, factor $f$ calibrado con el actuado en P2 y P4), barrido del fijo (con ampliación de la malla) y actuado, configuración y tabla de aproximaciones, enlaces y vecinos |
| 3.3 `fig:flujo-u2` | `sec:formulacion` | El entrenamiento de un aprendiz con una base: bucle por segundo, decisión cada 5 s de verde, cierre con la recompensa acumulada, actualización según el algoritmo (marcas T, D, P), validación cada 10 episodios en 999 y 1999, *checkpoint* y publicación |
| 3.4 `fig:flujo-u4` | `sec:u4` | Un episodio con coordinación: los dos relojes (mensajes cada 5 s globales y decisión cada 5 s del verde propio), el mensaje y su canal, la observación extendida, el término *spill*, los críticos local (IPPO) y central (MAPPO), GAE y PPO |
| 3.5 `fig:flujo-u3` | `sec:u3` | Qué se mide en cada corrida (`tripinfo`, lecturas TraCI por segundo, retornos) y cómo se llega al veredicto: `evaluar.py` en 1001–1030, `consolidar.py` (IC95, Δ pareado, *bootstrap*, Wilcoxon), `veredicto.py` (base publicada, convergencia, regla) |

Lenguaje común: un color por unidad (U1 azul, U2 naranja, U3 verde, U4 violeta, que se distinguen también en gris por los títulos), una forma por tipo de nodo (proceso, archivo o dato, decisión, inicio o fin, simulador, semillas, puerto), un trazo por tipo de flecha (flujo, interfaz, repetición, previsto no usado) y la misma leyenda al pie de las cinco. Ocho interfaces con nombre fijo: I1 escenario del caso, I2 aproximaciones, enlaces y vecinos, I3 observación y recompensa, I4 acción, I5 mensajes entre vecinos, I6 métricas por corrida, I7 política publicada, I8 veredicto. La arquitectura las dibuja como flechas y cada figura de unidad como puertos o citas, con el mismo texto. Todas miden 15 cm de ancho y se incluyen a escala 1, con letra de 8 pt como mínimo. La arquitectura va con `[H]`; las cuatro de unidad, de casi una página, con `[p]` para no dejar medias páginas vacías.

### Cambios de texto que trajo la segunda parte

- Se borraron los tres TODO de diagramas (`capitulo2.tex`, `capitulo3.tex` y `capitulo4.tex`). Quedan 30 TODO.
- `capitulo3.tex`: pie y párrafo "En la figura..." para cada figura; un párrafo que define I1 a I8 antes de `tab:pipeline`; `tab:pipeline` renombra U2 como "Aprendizaje por refuerzo" y U3 como "Simulación y medición", como la introducción (antes "Entrenamiento" y "Medición"), y su fila U3 dice que colas y retornos los mide `correr_episodio` (hasta ahora se atribuía todo a `comun.py`). `tab:plan2-modelos` bajó un párrafo para no dejar un tercio de página vacío.
- `capitulo4.tex`: citas a las Figuras 3.2 a 3.5; corregida la frase que decía que el entrenamiento depende del barrido de su caso (en `plan2/generar_trabajos.py` solo depende de preparar el caso; el barrido solo lo espera la evaluación del fijo); agregado que en el plan ningún barrido tuvo que ampliar su malla (ningún `plan2/cola/logs/barrido_*.log` tiene "AVISO").
- `introduccion.tex`: la arquitectura modular remite a la Figura 3.1.
- `CLAUDE.md`: el cruce de Lima se importó de OSM pero no se limpió en netedit.
- La verificación de los textos nuevos corrigió, antes del commit: que la validación y el *checkpoint* van cada 10 episodios y en el último (no tras cada episodio); que la actualización PPO es solo de IPPO y MAPPO; las excepciones de SARSA (elige antes de actualizar) y `ql_colas` (recompensa leída al decidir); que la configuración de SUMO trae el fijo y el actuado se agrega al evaluarlo; y que los puertos grises son los de varias unidades o de los resultados.

### Notas que quedan para el autor (no cambian los dibujos)

- "Las mismas fases que el fijo" (actuado; `sec:modelos` y otros lugares) es aproximado: `comun.archivo_actuado` toma las fases del programa estático por omisión de la red, que tiene los mismos estados, pero en malla3 en otro orden. La figura de U1 lo dice con precisión.
- Ningún script calcula el factor $f$: la calibración consta en el texto y en las cabeceras de `corredor_alta.rou.xml` y `plan2/red_alta.rou.xml`.
- Los tabulares no cierran la última decisión al terminar el episodio y las redes sí (lo muestra la Figura 3.3; el texto no lo dice).
- `rl_corredor.py` observa y luego calcula la recompensa, y `rl_ippo.py` cierra y luego observa. Ocurre en el mismo instante y las figuras siguen el orden de `rl_ippo.py`.

### Cómo regenerar las figuras

`cd TESIS/diagramas && python construir.py` compila las cinco (o `python construir.py u2` una sola), copia cada PDF a `TESIS/images/diag_<nombre>.pdf`, deja una vista previa en `previa/` e informa el tamaño. Cualquier cambio de contenido debe seguir la especificación, que tiene la evidencia de cada elemento; el estilo común está en `estilo_diagramas.tex`.
