# Referencias del plan 3 (tareas 0.7-0.12): informe de implementación

05.11.2026. Rama `plan3-ref` (nació de `plan3-dev` en 223f908). Tres vueltas:
- la primera, las tareas 0.7-0.12 (hasta eeb82f7);
- la segunda, la tarde del 05.11: los arreglos de la revisión de 0cea683 y la regla reactiva (4faffb7, d01c2a6);
- la tercera, la noche del 05.11: la verificación adversarial de 6e8cfab (`plan3-dev` fusionado en d46cc40). Código
  en 7714544; este informe, `desviaciones.md` §3 y las salidas de las pruebas en el commit siguiente.

## Respuesta corta

- **Qué hay.** Seis scripts nuevos en `plan3/` y cambios mínimos, apagados por defecto, en tres archivos entregados:

  | Archivo | Tarea | Qué hace |
  |---|---|---|
  | `plan3/barrer_fino.py` | 0.7 | Fijo fino (regla del prerregistro §5), fijo con verdes de 5 en 5 y el ganador de la gruesa ("fijo desde 10 s"), con puntaje por periodo |
  | `plan3/franja.py` | 0.8 | Fijo por franja (un plan por media hora) y fijo por bloques del perfil, con un WAUT por semáforo en su instante de cambio |
  | `plan3/actuado.py` | 0.9 | Actuado ajustado: descenso por coordenadas en cadena, `delay_based` y dos variantes coordinadas con el fijo fino |
  | `plan3/reglas.py` | 0.10 | Regla simple U × G, regla reactiva (D m) y Max-Pressure para el gancho `decidir` de `rl_ippo`, y su barrido por familia |
  | `plan3/p3_preparar.py` | 0.11 | Trabajo "preparar" de cada noche: `_actuado` y `_trivial` (y `_actuado_aj` solo si se pide) |
  | `plan3/p3_congelar.py` | 0.17 | Parte B: escribe `referencias_congeladas.json` (archivo y sha256 de cada referencia) después de comprobar que cada una es la de su barrido |
  | `comun.py` | 0.11 | `archivo_actuado` y `archivo_trivial` escriben en un temporal y reemplazan (mismo contenido); `leer_cfg` quita espacios de las rutas |
  | `rl_corredor.py` | 0.7-0.9 | Modos `franja`, `bloques` y `actuado_aj`, y `adicional=` (fijo de otro archivo); sin ellos nada cambia |
  | `evaluar.py` | 0.7-0.10 | `--brazo franja`, `bloques` o `actuado_aj`, `--brazo fijo --programa --nombre`, `--regla`; funciones para `evaluar3` |

  Y en archivos de otros bloques, a pedido: `evaluar3.py` (un brazo por comando, `sha_ref`, referencias congeladas),
  `generar_trabajos3.py` (salidas, presupuestos, `requiere`) y `chequeos_previos.py` (cada comando con el parser de su
  script; las referencias congeladas contra el disco).

- **Lo más importante de la tercera vuelta: la variante coordinada (b) del actuado no coordinaba en red y malla.**
  SUMO cuenta su ciclo desde el desfase del programa y solo corre `earliestEnd`/`latestEnd` al ciclo siguiente si el
  verde ya empezó **y** terminó en el ciclo actual. Con la avenida en la fase 0 de la plantilla (red, malla y sus
  derivados), cuando la transversal cortaba antes el verde de la avenida empezaba antes del 0 y terminaba después:
  en el ciclo siguiente su `earliestEnd` ya había pasado y podía cortar antes. Medido con el plan 25/15 de
  `dem_red_t3620` y la semilla 424301: (b) terminaba la avenida en el fin del plan fijo en 84 de 166 salidas, con
  ciclos ~25 % más cortos, aun con `maxDur` 60. El `maxDur` heredado de la cadena era una segunda causa (en el
  corredor, la única). **Sí se puede hacer exactamente lo que dice §5**: el ciclo se cuenta desde el inicio del verde
  transversal del plan fijo (los mismos instantes del plan fijo; el desfase del programa es el del fino más ese
  inicio) y la avenida tiene `maxDur` suficiente. Ahora (b) termina la avenida en el fin fijo en 128 de 129 salidas
  (la otra es el arranque), en P2, P3 y P6 también con `maxDur` = los verdes fijos. La variante (a) tenía el mismo
  defecto y lleva el mismo arreglo. Cambia el actuado ajustado que veta FUNCIONA: se declara en `desviaciones.md` §3
  (borrador para la parte B). Detalle en 1.3 y 6.5.

- **Lo demás de la tercera vuelta** (verificación de 6e8cfab):

  | Punto | Arreglo |
  |---|---|
  | Ensayo de la cadena real | El corredor por la cola, con los comandos del generador, sin opciones de prueba y las semillas de la regla (2 CPU); después `evaluar3` con cada brazo de referencia, semilla por semilla contra el barrido: 17 trabajos, 0 fallidos, 25 min de reloj (0.93 h-p estimadas); los 9 brazos dan, semilla por semilla, lo mismo que el barrido (2.8) |
  | [21] Referencias congeladas (G1-F2) | `evaluar3` anota `sha_ref`; a ciegas se niega antes de simular si la referencia no es la de `referencias_congeladas.json`; las evaluaciones decisivas de referencias lo tienen en `requiere`; `chequeos_previos` compara el disco con el JSON; `p3_congelar.py` lo escribe |
  | Código del tag (G1-F3) y B22 de las referencias (G1-F7) | Borrador de `desviaciones.md` §3: commit y blobs del código que corre, cada diferencia de comportamiento con el tag y el procedimiento B22 de las referencias (salidas viejas a `barridos_viejos/`, ids `_r2`) |
  | Huella del fijo fino (G3-2, G1-F10) | El paso 6 del actuado y `franja --bloques` leen `fijo_fino.json` con su huella (calculada con los cortes de su propio barrido) |
  | Generador ↔ scripts (G1-F4) | `validar_args(argv)` en los cinco scripts y en `evaluar3`; `chequeos_previos` valida cada comando de la lista con el parser de su script |
  | Barridos de reglas en otras familias | `--familia reactiva` (humo) en `per_corredor`, `mix_corredor`, `malla3_alta_e`, `poi_red`, `dem_corredor_t2715_der` y `red`: 6 de 6 con código 0 y un `reactiva.json` correcto (ganadora de la rejilla, su familia y escenario, 3 finalistas con llegadas regulares y las 5 con aleatorias, la marca de prueba) |
  | WAUT (G3-1, G3-3) | La relajada solo si ningún verde que toca el cambio queda por debajo de 10 s; aviso de los cambios estrictos tardíos (más de 300 s, después del cambio siguiente o de la hora) |
  | Reglas (G1-F6, G2-4) | La huella de las reglas cubre también `escenarios_plan3.py` y `con_escenarios.py`; nombres de la reactiva solo de su rejilla (`fullmatch`) |
  | `evaluar3` (G2-1, G3-6, G3-7) | Un solo brazo por comando; `--regla-de` se niega con la marca de prueba, otra familia u otro escenario |
  | Presupuestos y salidas (G1-F5, G2-5) | Reglas por familia y llegadas (51/36/33 de 84 o 300/150/120 de 420), sin EMPAQUE doble, pasos del actuado por sus corridas; los `*_semillas.csv` declarados |
  | Escenario en la huella (G3-4) | Los XML del escenario se hashean con los fines de línea normalizados |
  | Pruebas nuevas | Oráculo independiente de la reactiva (`getNextTLS`) y su reloj (G2-2); posición de los detectores (G1-F9); identidad barrido = evaluación con WAUT no estricto; huella de las reglas; ids de los trozos; huérfanos por pid (unitaria) |
  | `trivial` en `cruce`/`cruce2` (G3-8) | Rechazado |
  | Los 32 hallazgos de 0cea683 | Punto por punto en la sección 7 |

- **Números.** Cambian, y se declara: la variante coordinada (a) en P3 y P6 (21.61 → 22.55 y 115.94 → 118.13 s/veh
  con el fijo entregado como fino; la (b) no cambia ahí porque la transversal del plan entregado está en su mínimo) y
  los programas de la franja en los pares sin instante estricto con verdes cortos (de relajada a respaldo). Nada de lo
  entregado cambia.
- **Pruebas:** pasan las 12 (245 chequeos; sección 4), todas en el código final. Los números de antes no cambian, salvo la variante (a) en P3 y P6, que el arreglo implica.
- **No regresión** (código final; la salida dice commit y sha256 de `comun.py`, `rl_ippo.py`, `evaluar.py` y
  `rl_corredor.py`): 23 de 24 brazos repiten dígito a dígito sus CSV entregados; el 24.º, IPPO en P6, difiere solo en `cambios_fase` (4 menos que el entregado en cada semilla), la diferencia ya explicada (`prueba_nr_p6`, 2 de 2). `veredicto.py --probar` pasa.
- **Lo dudoso** está en la sección 6. Lo principal: la variante coordinada cambió después del tag (declarado); el
  instante estricto del WAUT puede llegar muy tarde (se avisa; un tope sería una enmienda de B8).

---

## 1. Qué hace cada script

Todos corren con `cwd = plan3/` (o una carpeta dentro de `plan3/`, como las copias de las pruebas): desde la raíz o
desde `plan2/`, que también tienen los `.sumocfg`, se niegan antes de escribir nada. Sin preguntas, deterministas,
escriben cada CSV, JSON y `.add.xml` en un temporal con el pid que después reemplazan (y lo borran si no llegan a
hacerlo), y terminan con código 0 solo con todas sus salidas escritas. Nunca escriben en `plan2/` ni en `TESIS/`, y
nunca usan `barrer_fijo.py --instalar`. Las opciones se escriben completas (no aceptan abreviaturas). Con escenarios
de `escenarios_plan3` (`poi_*`, `per_*`, `mix_*`, P6e) se llaman a través del lanzador:
`python ../con_escenarios.py <script> <esc> ...`.

**Semillas** (prerregistro §3 y §5; las llegadas aleatorias se detectan solas por `period="exp(...)"` en las rutas):

| Script | Barrido | Finalistas |
|---|---|---|
| `barrer_fino.py` | 2001-2003 (aleatorias: 2001-2010) | 10 mejores con 2001-2010 (aleatorias: 2001-2030); frágiles: 3 primeros con 2001-2030 |
| `franja.py` | pares con las del barrido | 3 mejores pares con 2001-2010 (aleatorias: los 9 con 2001-2030); bloques: 2001-2030 |
| `actuado.py` | 2001-2003 (también con aleatorias) | 3 mejores con 2001-2010 (aleatorias: 10 con 2001-2030) |
| `reglas.py` | 2001-2003 (también con aleatorias) | por familia, 3 con 2001-2010 (aleatorias: 10, o las 4 de MP, con 2001-2030) |

**Opciones de prueba** (solo fuera de la cola, en copias): `--llegadas`, `--semillas`, `--semillas-desempate`,
`--semillas-fragil`, `--semillas-final`, `--avenida`, `--transversal`, `--limite` y `--permitir-prueba`. Quedan
anotadas en el `registro` del JSON de cada salida (`"prueba": [...]`; vacío = la regla).

**Cadena de etapas.** Cada etapa comprueba lo que lee antes de correr nada:
- la gruesa (en `fijo_grueso10.json`, campo `registro`): llegadas detectadas, semillas del barrido de la regla,
  rejilla inicial de `barrer_fijo` (con su par desplegado), sin `--limite` y sin opciones de prueba;
- cada `<etapa>_semillas.csv` que lee (gruesa, fina, desfases, desempate): la huella de hoy y, por plan, exactamente
  las semillas de la regla;
- donde se usa el fijo fino (paso 6 del actuado, bloques) o un paso anterior del actuado: su marca de prueba.

Si algo no es de la regla se niega y dice qué; con `--permitir-prueba` (solo pruebas) sigue con un aviso y su propia
salida queda marcada como de prueba. La cola rechaza `--permitir-prueba` como las demás opciones de prueba
(capa 1 de `protecciones.py`, desde 7192185).

### 1.1 `barrer_fino.py` (0.7)

Importa `Plantilla`, `configs_plantilla`, `desfases_malla3` y `evaluar_config` de `barrer_fijo.py` sin cambiarlos.
Etapas (cada una lee lo que dejó la anterior en `barridos/<esc>/`):

| Etapa | Qué corre | Escribe |
|---|---|---|
| `gruesa` | La rejilla de `barrer_fijo` (MALLAS desde 10 s, desfases del caso o los 3 esquemas, par desplegado, extensión si el ganador queda en el borde) | `gruesa.csv`, `gruesa_semillas.csv`, `fijo_grueso10.json` (con el registro), `<esc>_r10g.add.xml` |
| `fina` | Mínimos locales de la gruesa (pares de verdes cuyo mejor retraso no supera al de sus vecinos a un paso en un eje), a ≤ 2 % del mejor (`a_2pct`; aleatorias: diferencia pareada ≤ 2 errores estándar), tope 3; alrededor de cada uno avenida ±4 y transversal ±2 de 1 en 1 (10-60 s) con los 3 mejores patrones de desfase de la gruesa en ese par (malla: los 3 esquemas y `onda_oe`) | `fina.csv`, `fina_semillas.csv` |
| `desfases` | Corredor y red: desfases ±4 s de 1 en 1 alrededor del mejor plan de cada región (corredor 9; red 9 × 9). Malla: nada | `desfases.csv`, `desfases_semillas.csv` |
| `desempate` | Las 10 mejores de gruesa, fina y desfases con las semillas del desempate | `desempate.csv`, `desempate_semillas.csv` |
| `fragil` | Lee el desempate (sin reescribirlo: rehace en memoria las 10 finalistas y comprueba que salgan las de `desempate.csv`, en su orden). Si los dos primeros quedan a ≤ 2 % (`a_2pct`) o el ganador tiene una semilla > 1.10 × su mediana: los 3 primeros con 2001-2030; gana la menor media. Instala el fijo fino | `fragil.csv`, `fragil_semillas.csv`, `fijo_fino.json`, `<esc>_r10f.add.xml` |
| `mult5` | Fijo con verdes de 5 en 5: los 3 mejores planes de la gruesa con los dos verdes múltiplos de 5, con desfases ±4 s (malla: `onda_oe`); desempate y frágiles como el fino | `mult5.csv`, `mult5_semillas.csv`, `mult5_desempate.csv`, `mult5_desempate_semillas.csv`, `fijo_mult5.json`, `<esc>_m5f.add.xml` (y `mult5_fragil*.csv` si el ganador es frágil) |
| `fino`, `todo` | `gruesa`..`fragil` en un proceso; `todo` agrega `mult5` | lo de cada etapa |

- **`a_2pct(valor, mejor)`**: `100 × (v − m) ≤ 2 × m` con `v` y `m` en centésimas enteras (las medias llegan redondeadas
  a 0.01). Así 20.91 frente a 20.50 (2.00 %) cuenta como dentro; antes, en coma flotante, la frágil dejaba fuera 91
  de 190 bordes exactos y la fina no (las dos comparaban distinto).
- **Puntaje por periodo** (lo usa `franja.py`): cada corrida da además el retraso total de los vehículos con salida
  programada en cada periodo (`--bloque 1800`: dos medias horas; `--bloque 600`: los seis bloques del perfil). Para
  eso sumo corre con `--tripinfo-output.write-undeparted`, que **nunca** se pasa a `barrer_fijo.correr_sumo`. Las
  métricas de la hora se leen con `comun.leer_tripinfo` sobre el tripinfo sin las filas con depart < 0 (son las de
  `barrer_fijo`, comprobado); esas filas solo entran al periodo de su salida programada, fin − departDelay. Si
  `comun.ESCRIBIR_NO_INSERTADOS` (de `evaluar3`) ya agrega la opción, no se repite.
- **Columnas:** las de `barrer_fijo` en el mismo orden (verde, izquierda, verde_transversal, offsets, esquema, 7
  métricas, 2 sd, semillas) y después ciclo, etapa, región, clave, mediana, peor, trabadas, `total_p<k>` y
  `noins_p<k>`.
- **Trozos y reanudación:** `--trozo k/n` corre solo los planes de índice ≡ k (mod n) de la lista principal de la
  etapa (gruesa: la rejilla inicial; fina; desfases; mult5: sus desfases) y escribe
  `barridos/<esc>/trozos/<etapa>_t<k>de<n>.csv`. La misma etapa sin `--trozo` junta trozos, etapas anteriores y la
  caché `tmp_fino/<esc>/*.jsonl` (una línea por corrida: un trabajo cortado sigue donde quedó), corre lo que falte y
  escribe la salida.
- **Huella de la caché.** Cada resultado se guarda con la huella del escenario y con el sha256 del programa con que se
  corrió; solo se reutiliza si los dos coinciden. La huella cubre: los archivos del escenario (cfg, red, rutas,
  adicionales, plantilla), `FIN_SIM` y los cortes, el **sha256 completo** de `barrer_fino.py`, `barrer_fijo.py`,
  `comun.py` y `escenarios_plan2.py` (con los fines de línea normalizados: el mismo commit da la misma huella en
  cualquier worktree) y los valores de `comun.ESCRIBIR_NO_INSERTADOS` y `comun.QUITAR_BLOQUE`. Cualquier cambio en
  esos archivos, aunque sea un comentario, deja sin uso todo lo guardado: la etapa vuelve a correr todo y las
  siguientes se niegan a leer salidas de otra huella. Eso es lo que pide B22 tras un arreglo; el costo es repetir la
  celda entera (sección 6).
- **El `.add.xml` instalado** tiene el programa `fijo` y reemplaza a la plantilla `<esc>.add.xml` en
  `--additional-files` (como lo haría `--instalar`); para jugarlo: `evaluar.py --brazo fijo --programa
  <esc>_r10f.add.xml --nombre fino --semillas ...` o `evaluar.brazo_programa`.

### 1.2 `franja.py` (0.8)

- **Franja:** los 3 mejores planes de cada media hora según `total_p1` y `total_p2` del barrido fino (gruesa, fina y
  desfases, con las semillas del barrido), sus 9 pares (siempre dos programas, aunque sean el mismo plan), cada par
  con las semillas del barrido; finalistas como en la tabla de semillas; gana la menor media.
- **Bloques (perfil):** el mejor plan de cada bloque de 600 s según su puntaje por bloque (el barrido del perfil se
  corre con `--bloque 600`), una secuencia de hasta 6 programas (un bloque con el mismo plan que el anterior no
  cambia), verificada con 2001-2030. Va después de `fragil`: exige `fijo_fino.json`, con su huella (la de su propio
  barrido, con sus cortes), y pone al lado el fijo fino con las mismas semillas (`fijo_fino_mismas_semillas`); así
  `bloques.json` no depende del orden en que corra la cola ni de un fijo fino viejo.
- **WAUT (B8):** un `<WAUT>` por semáforo, sin `procedure`; el plan nuevo entra alineado con su propio desfase. El
  instante de cambio de cada semáforo es el primero desde el corte (y después del cambio anterior) que cumple, en
  este orden:

  | Regla | Cuándo | Qué se ve en el semáforo |
  |---|---|---|
  | estricta | los dos planes muestran el mismo estado en t − 1, t y t + 1 (la de siempre) | nada: el cambio no se nota |
  | relajada | si no hay estricta en un hiperperíodo: el paso del estado viejo al nuevo es uno que haría un plan normal y ningún verde que lo toca dura menos de 10 s | ningún verde pasa a rojo sin ámbar, ningún ámbar queda corto, ningún rojo pasa a ámbar ni ningún ámbar a verde, ningún verde de menos de 10 s |
  | respaldo | si tampoco: el primer fin de un ámbar del plan viejo sin verde a rojo ni ámbar corto | los enlaces que terminaron su ámbar pueden seguir en ámbar o pasar a verde, y uno en rojo puede ver un ámbar; ninguno corta un verde |
  | forzado | si ni eso (no pasa con las plantillas de P1-P6: sus ámbares no tienen verdes) | el primer fin de ámbar del plan viejo, con los problemas anotados |

  `franja.json` y `bloques.json` traen `cambios`: por semáforo y por cambio, la regla, el instante nominal, el
  instante y el retraso (instante − nominal), la cuenta por regla, el retraso máximo, los cambios tardíos (más de
  300 s después del nominal, después del nominal del cambio siguiente o después de la hora) y un aviso si alguno no
  fue estricto o llegó tarde (el aviso va también en el comentario del `.add.xml`; con todos estrictos y a tiempo el
  archivo es el de siempre). En 3000 pares al azar de P1, P3 y P6, la estricta llegó hasta 708 s tarde: un tope sería
  una enmienda de B8, así que solo se avisa.
  El archivo se carga **encima** de los adicionales del `.sumocfg` (el WAUT activa `franja1`/`bloque1` desde 0 s);
  nunca va dentro de un `.sumocfg`.
- **Escribe** en `barridos/<esc>/`: `franja.csv` (los 9 pares), `franja_final.csv`, `franja_semillas.csv`,
  `franja.json` (programas, instantes, cambios, registro, sha256) o `bloques.csv`, `bloques_semillas.csv`,
  `bloques.json`; y `<esc>_franja.add.xml` o `<esc>_bloques.add.xml`.

### 1.3 `actuado.py` (0.9)

- Variantes del actuado de SUMO 1.25, sin TraCI (el programa encima de los adicionales queda activo por ser el
  último). Rejillas fijas con el defecto incluido; cada paso parte del mejor de los anteriores (en un empate se queda):

  | Paso | Coordenada | Valores (defecto *) |
  |---|---|---|
  | 1 | `max-gap` | 1, 1.5, 2, 3*, 4 s |
  | 2 | `detector-gap` | 1, 2*, 3, 4 s (el 4 queda en ≈ 3.1 s: ver abajo) |
  | 3 | `jam-threshold` | −1*, 10, 30 s |
  | 4 | `maxDur` del verde de avenida | 30, 45, 60* s |
  | 5 | `maxDur` del verde transversal | 20, 30, 60* s |
  | 6 | familia | `delay_based` (detectorRange 50/100/200 m × minTimeLoss 1*/3 s, con los maxDur elegidos) y las dos variantes coordinadas del mejor actuado |
  | final | — | las 3 mejores de los 6 pasos con 2001-2010 (aleatorias: 10 con 2001-2030) |

- **`detector-gap` 4 queda topado** (hallazgo [6], declarado, sin cambiar la rejilla): SUMO pone el detector a
  min(detector-gap × vmax, (minDur / passing-time + 0.5) × 7.5 m). Con minDur 10 s y passing-time 1.9 (su defecto) el
  tope es 43.2 m; como todos los carriles con semáforo van a 13.89 m/s, el 4 queda en 43.2 m (≈ 3.1 s), a 1.55 m del
  3 (41.7 m). La rejilla del prerregistro ("rejillas fijas que incluyen los valores por defecto") se cumple; el último
  punto explora poco más que el 3.
- `minDur` 10 s (5 en giros), fases y duración inicial del programa "0" de la red, desfase 0: la variante por defecto
  es el actuado entregado (`comun.archivo_actuado`) con `programID="actuado_aj"`. Los `<param>` se escriben solo si
  difieren del defecto de SUMO (`delay_based` los escribe siempre).
- **Ojo con `minTimeLoss`:** SUMO 1.25 lee la clave `minTimeloss` (así está en `sumo.exe`); con `minTimeLoss`, como
  dice su documentación, la ignora sin aviso. `actuado.py` escribe `minTimeloss`.
- **Dos variantes coordinadas** (prerregistro §5): `coordinated=true`, `cycleTime` del fijo fino, las fases de su
  plantilla con sus duraciones y los parámetros del mejor actuado; (a) el verde de avenida con `earliestEnd` en su fin
  del plan fijo, y (b) "fin fijo": `latestEnd` = `earliestEnd` en la avenida **y** `latestEnd` en la transversal, cada
  uno en su fin del plan fijo. El paso 6 corre las dos (paso 6 con 2001-2003, como los demás).
- **Cómo cuenta SUMO el ciclo, y por qué importa** (verificación de 6e8cfab). `timeInCycle = (t − offset) mod
  cycleTime`, y un verde con `earliestEnd` y `latestEnd` solo pasa esos valores al ciclo siguiente si ya empezó **y**
  terminó en el ciclo actual. Si el verde de la avenida cruza el 0 del ciclo (empieza antes porque la transversal cortó
  antes, y termina después), en el ciclo siguiente su `earliestEnd` ya pasó: corta antes y el ciclo se acorta. Pasa
  cuando la avenida es la fase 0 de la plantilla: red, malla y todos sus derivados. Por eso el ciclo se cuenta desde el
  inicio del verde transversal del plan fijo (`referencia_coordinada`): los `earliestEnd`/`latestEnd` son los mismos
  instantes del plan fijo, contados desde ahí, y el desfase del programa es el del fino más ese inicio. Así la avenida
  empieza y termina siempre dentro del mismo ciclo. En el corredor (la avenida es la fase 2 y la transversal la 0) el
  programa no cambia.
- **`maxDur` de la avenida en las coordinadas:** no menor que lo que necesita para llegar a su fin. En (b), el ciclo
  entero (su `latestEnd` la corta igual en su fin; con menos, un arranque corto se perpetuaba). En (a), el ciclo menos
  los ámbares y los `minDur` de los otros verdes (lo que necesita si la transversal corta en su mínimo; sin `latestEnd`
  puede alargar). Los pasos 1-5 siguen con los `maxDur` de la cadena.
- **Lo medido** (`pruebas/ref/medir_coordinada.txt`, semilla 424301): con el plan 25/15 de `dem_red_t3620`, (b) antes
  terminaba la avenida en el fin fijo en 84-91 de 164-167 salidas (el plan fijo tiene 130) con `maxDur` 60, y en 24-29
  de 176-177 con `maxDur` = los verdes fijos; ahora, 128-130 de 129-130 salidas en los dos casos (lo que falta es el
  arranque). En el corredor (22/15) antes fallaba solo con `maxDur` = los verdes fijos (22-27 de 163); ahora 138-139 de
  139-140. `prueba_actuado` 6 lo comprueba en P2, P3 y P6 con un plan con holgura y `maxDur` = los verdes fijos.
- **Escribe** en `barridos/<esc>/`: `actuado_paso<k>.csv`, `actuado_paso<k>.json` (partida, variantes, elegida y
  registro), `actuado_paso<k>_semillas.csv`, `actuado_final.csv`, `actuado_final_semillas.csv`, `actuado_aj.json`; y
  `<esc>_actuado_aj.add.xml`.
- **`actuado.py <esc> --instalar`** (`reinstalar`, la pieza `actuado_aj` de `p3_preparar`): si el instalado ya tiene
  el sha256 congelado de `actuado_aj.json`, no lo toca; si no, escribe el texto de hoy en un temporal, compara su
  sha256 con el congelado y solo entonces reemplaza. Si no coincide: error, el instalado queda como estaba y el
  temporal se borra.

### 1.4 `reglas.py` (0.10)

- `hacer_decidir(regla)` da la función `decidir` para `rl_ippo.correr_episodio(..., variante="local", decidir=...)`:
  las tres familias corren por `reglas.correr` → `rl_ippo.correr_episodio` con el gancho `decidir` (mismo reloj de
  5 s, máscara, ámbar y métricas que IPPO; sin tocar `rl_ippo.py`). Crear una por episodio.
- Nombres (con `fullmatch`, sin ceros a la izquierda; la reactiva solo con D de su rejilla):
  - `regla_u<U>g<G>` (U entero o `inf`; `regla_uinfg60` es el ciclo mínimo);
  - `reactiva_d<D>`: **regla reactiva**, alarga cualquier verde mientras haya un vehículo a ≤ D m de la línea de
    detención en algún carril con verde (enlace `G` o `g` en el estado del semáforo; distancia = largo del carril −
    posición del vehículo; los vehículos que ya entraron al cruce no cuentan); si no hay ninguno, cambia; D ∈ {15,
    25, 35, 50, 70} (`reactiva_d26` o `reactiva_d025` se rechazan). Qué cubre la comparación con el prototipo
    (`analisis_mejora_2026-11-04/plan3/critica_resultados/reloj_reactivo.py`): `prueba_reglas` 5 corre una copia de
    su lógica (`hacer_decidir`) y esta regla por el mismo bucle de `rl_ippo`, con el reloj de 5 s, en el corredor y
    `malla3_alta` regulares, y da el mismo tripinfo; y `prueba_reglas` 7 la compara con un oráculo independiente
    (`traci.vehicle.getNextTLS`: distancia y estado del propio enlace de cada vehículo), sin diferencias en 856 y 5468
    decisiones libres. Las cifras del prototipo en P1 (`poi_corredor`) se reproducen; las de P6 no, porque el
    prototipo armó la entrada de P6 con la opción `departLane best` y plan3 con el atributo del flujo (prerregistro §5,
    "Inserción en los escenarios nuevos"); con la misma forma de entrada salen iguales (verificación de 6e8cfab);
  - `mp`, `mp_det`, `mp_c<C>`, `mp_det_c<C>` (Max-Pressure).

  Toda acción respeta la máscara (hay un `assert`).
- Barrido, una familia por trabajo (`--familia regla|reactiva|mp`; `todas` corre las tres): reglas U ∈ {1, 2, 3, 4, 6}
  × G ∈ {30, 60}; reactiva D ∈ {15, 25, 35, 50, 70} m; MP `mp`, `mp_det`, `mp_c60`, `mp_c90`. Cada familia con
  2001-2003 y sus finalistas como en la tabla de semillas. Escribe, por familia,
  `barridos/<esc>/reglas_<familia>.csv`, `reglas_<familia>_final.csv`, `reglas_<familia>_semillas.csv` y
  `<familia>.json` (`regla.json`, `reactiva.json` o `mp.json`): su campo `"regla"` es el nombre de la ganadora (p. ej.
  `reactiva_d25`), lo que lee `evaluar3 --regla-de`.
- Caché `tmp_fino/<esc>/reglas_<pid>.jsonl`: una corrida guardada vale con la misma huella, la del escenario (como
  `barrer_fino`) más el sha256 de `reglas.py`, `rl_ippo.py`, `rl_corredor.py` y, si están, `escenarios_plan3.py` y
  `con_escenarios.py` (`codigo_de_reglas`; `prueba_reglas` 8 comprueba que cambia con cada uno).
- El JSON de cada familia trae `registro` (llegadas, semillas y `prueba`): `evaluar3 --regla-de` lo revisa (3).

### 1.5 `p3_preparar.py`, la escritura atómica y `leer_cfg` (0.11)

- `comun.escribir_atomico(ruta, texto)`: temporal `<ruta>.<pid>.tmp` y `os.replace` con 10 reintentos de 2 s; si no
  llega a reemplazar, borra el temporal y el destino queda como estaba. La usan `archivo_actuado` y
  `archivo_trivial`; el archivo sale igual byte a byte.
- `comun.leer_cfg` quita los espacios alrededor de cada ruta (`'det.add.xml, corredor.add.xml'` es válido en SUMO);
  con los 40 `.sumocfg` de la raíz y de `plan3/` la lista es la de antes.
- `p3_preparar.py <esc> ... [--piezas actuado,trivial]`: por defecto escribe `<esc>_actuado.add.xml` y
  `<esc>_trivial.add.xml`; `--piezas actuado_aj` agrega `<esc>_actuado_aj.add.xml` (con `reinstalar`, 1.3). Relee cada
  archivo como XML e imprime su sha256. **Punto de extensión:** el diccionario `PIEZAS`
  (`{nombre: función(esc) -> ruta}`); los E2 de la observación nueva (3.1) entran como otra pieza.

### 1.6 Referencias congeladas: `p3_congelar.py`, `evaluar3` y `chequeos_previos` (parte B; [21])

- **`p3_congelar.py [--comprobar]`** (cwd = `plan3/`, día 14, a mano): arma la lista de todas las referencias que
  evalúa la cola (`generar_trabajos3.brazos_ref` de cada celda con referencias: 154 archivos) y, para cada una,
  comprueba que el programa tenga el sha256 que anotó el JSON de su barrido (`fijo_fino.json`, `fijo_mult5.json`,
  `fijo_grueso10.json`, `franja.json`, `bloques.json`, `actuado_aj.json`), que ningún JSON traiga la marca de prueba y
  que los JSON de las reglas sean de su familia. Si todo cuadra escribe `referencias_congeladas.json`:
  `{"version": 1, "commit", "escrito", "referencias": {archivo relativo a plan3/: {"sha256", "celda", "referencia",
  "tipo", "escenario", ...}}}`. Con un solo problema no escribe nada (código 1).
- **`evaluar3`**: la columna `sha_ref` lleva el sha256 del archivo de la referencia que carga (el `--programa`, el
  `<esc>_<brazo>.add.xml` de franja, bloques y actuado_aj, o el JSON de `--regla-de`). Con `--salida ciego/...`, si
  falta el JSON congelado, no lista el archivo o el sha256 no coincide, sale antes de simular.
- **El generador**: las evaluaciones a ciegas de las referencias ajustadas tienen `referencias_congeladas.json` en
  `requiere` (la cola no las lanza antes de la parte B).
- **`chequeos_previos`**: desde que existe el JSON, cada tarde compara el disco con él (un archivo que falta o cambió
  es un problema y la noche no arranca).

### 1.7 Cada comando con el parser de su script (G1-F4)

`barrer_fino`, `franja`, `actuado`, `reglas`, `p3_preparar` y `evaluar3` tienen `validar_args(argv)`: el `parse_args` y
todos los `ap.error` del script, sin leer el escenario ni tocar archivos. `chequeos_previos` valida con ellos (y con el
de `rl_ippo`) cada comando de la lista de trabajos, en otro proceso y después de registrar los escenarios del plan 3;
así un desajuste entre el generador y un script (una familia o una opción que el script no conoce) para la noche en
la tarde. Con la lista de referencias y sus evaluaciones: 894 comandos, 0 rechazados (`prueba_comandos_ref` 1).

---

## 2. Cómo se corre cada celda

`h-p` = horas-proceso estimadas por trabajo en el régimen conservador + 10 % (`pruebas/ref/costos_ref.py`). Los
barridos que pasan de ~2 h se parten con `--trozo k/n` (los trozos en paralelo; después la misma etapa sin
`--trozo`). Todos con `--procesos 1`. La lista real de trabajos la arma `generar_trabajos3.py` (`ref_celda`); lo que
sigue es la regla que implementa.

### 2.1 Celda regular: P1-P6 y D (`dem_corredor_t2715_der`); P6e igual, por el lanzador

```
python barrer_fino.py <esc> --etapa gruesa      [--trozo k/n ... y luego sin --trozo]
python barrer_fino.py <esc> --etapa fina        [--trozo k/n ...]          # depende de gruesa
python barrer_fino.py <esc> --etapa desfases    [--trozo k/n ...]          # depende de fina
python barrer_fino.py <esc> --etapa desempate                              # depende de desfases
python barrer_fino.py <esc> --etapa fragil                                 # depende de desempate -> <esc>_r10f.add.xml
python barrer_fino.py <esc> --etapa mult5       [--trozo k/n ...]          # depende de gruesa -> <esc>_m5f.add.xml
python franja.py <esc>                                                     # depende de desfases -> <esc>_franja.add.xml
python actuado.py <esc> --paso 1   (luego 2, 3, 4, 5, en cadena)           # sin dependencias
python actuado.py <esc> --paso 6                                           # depende del paso 5 y de fragil
python actuado.py <esc> --paso final                                       # depende del paso 6 -> <esc>_actuado_aj.add.xml
python reglas.py <esc> --familia regla      # sin dependencias (las tres familias en paralelo)
python reglas.py <esc> --familia reactiva
python reglas.py <esc> --familia mp
```

| Celda | gruesa | fina | desfases | desempate | frágil | mult5 | franja | actuado (6 pasos + final) | reglas (regla + mp) |
|---|---|---|---|---|---|---|---|---|---|
| P1 corredor | 0.29 | 0.14 | 0.02 | 0.04 | 0.03 | 0.12 | 0.03 | 0.06 | 0.11 |
| P2 corredor_alta | 0.91 | 1.03 | 0.07 | 0.18 | 0.15 | 0.54 | 0.12 | 0.16 | 0.27 |
| P3 red | 1.94 | 0.19 | 0.33 | 0.10 | 0.08 | 1.18 | 0.07 | 0.11 | 0.17 |
| P4 red_alta | 2.34 | 0.22 | 0.40 | 0.12 | 0.10 | 1.43 | 0.08 | 0.12 | 0.20 |
| P5 malla3 | 0.66 | 3.20 | 0 | 0.21 | 0.18 | 0.43 | 0.15 | 0.32 | 0.46 |
| P6 malla3_alta (y P6e) | 1.12 | 1.69 | 0 | 0.36 | 0.31 | 0.72 | 0.25 | 0.55 | 1.00 |
| D | 0.64 | 0.62 | 0.04 | 0.11 | 0.09 | 0.32 | 0.07 | 0.16 | 0.27 |

(frágil: cota, si se activa; si no, 0. La columna "reglas" cuesta regla + MP; el generador la reparte por familia según
sus corridas: con llegadas regulares, regla 51, reactiva 36 y MP 33 de 84; con aleatorias, 300, 150 y 120 de 420 (la
reactiva va aparte de la columna). Franja y reglas sin el EMPAQUE que ya trae REF_H, y los pasos del actuado por sus
corridas: 5, 3, 2, 2, 2 y 8 de 22. En el ensayo del corredor (2.8): regla 205 s, reactiva 155 s y MP 150 s de reloj.)

### 2.2 Los 12 niveles `dem_*`

Fijo fino (que deja también el "fijo desde 10 s", `<esc>_r10g.add.xml`) y actuado ajustado; sin mult5, franja ni
reglas (PLAN3 1.6):

```
python barrer_fino.py <nivel> --etapa gruesa | fina | desfases | desempate | fragil     (en cadena, como 2.1)
python actuado.py <nivel> --paso 1 ... --paso 6, --paso final                            (o --paso todos)
```

Por nivel: gruesa 0.15-3.6 h-p (red 3620: 3.6), fina 0.1-2.3, desfases 0-0.9, desempate y frágil ≤ 0.3, actuado
0.07-0.6 (tabla completa en `costos_ref.txt`).

### 2.3 Llegadas aleatorias `poi_<caso>` (P1-P6)

Lo mismo que 2.1, por el lanzador: `python ../con_escenarios.py barrer_fino.py poi_<caso> --etapa ...`, etc. La regla
cambia sola (barrido con 2001-2010, umbral en errores estándar, 10 finalistas con 2001-2030; franja con los 9 pares;
actuado y reglas con 10 finalistas). No hay `fragil` que correr de más (los finalistas ya tienen 2001-2030), pero la
etapa igual se corre porque instala `<esc>_r10f.add.xml`.

| Celda | gruesa | fina | desfases | desempate | mult5 | franja | actuado | reglas (regla + mp) |
|---|---|---|---|---|---|---|---|---|
| poi P1 | 1.04 | 0.50 | 0.06 | 0.12 | 0.29 | 0.17 | 0.27 | 0.60 |
| poi P2 | 3.24 | 3.68 | 0.25 | 0.54 | 1.28 | 0.74 | 0.67 | 1.46 |
| poi P3 | 6.92 | 0.66 | 1.19 | 0.29 | 3.86 | 0.40 | 0.48 | 0.90 |
| poi P4 | 8.36 | 0.80 | 1.44 | 0.36 | 4.67 | 0.48 | 0.53 | 1.06 |
| poi P5 | 2.36 | 11.40 | 0 | 0.66 | 0.75 | 0.88 | 1.36 | 2.46 |
| poi P6 | 4.01 | 6.02 | 0 | 1.11 | 1.28 | 1.50 | 2.32 | 5.33 (3.8 + 1.5) |

Con trozos de ≤ 2 h: poi P3/P4 gruesa en 4-5 trozos, poi P5 fina en 6, poi P6 fina en 3; las reglas, un trabajo por
familia.

### 2.4 Perfil `per_<caso>` (P1 y P3)

Por el lanzador y con `--bloque 600` en **todas** las etapas del barrido (la huella incluye los cortes; mezclar
`--bloque` hace que la etapa siguiente se niegue a seguir):

```
python ../con_escenarios.py barrer_fino.py per_<caso> --bloque 600 --etapa gruesa | fina | desfases | desempate | fragil
python ../con_escenarios.py franja.py per_<caso> --bloques     # depende de desfases y de fragil -> per_<caso>_bloques.add.xml
python ../con_escenarios.py actuado.py per_<caso> --paso ...    # como 2.1
python ../con_escenarios.py reglas.py per_<caso> --familia regla | reactiva | mp
```

Costo como la celda aleatoria de su caso (poi P1 y poi P3) más 30 corridas de la verificación de bloques; sin mult5
ni franja de media hora.

### 2.5 Mezcla `mix_<caso>` (P1 y P3; `mixa_` juega lo de `mix_`)

El "fijo re-ajustado con la mezcla" del prerregistro §8: por el lanzador, la misma cadena que 2.3 en `mix_corredor` y
`mix_red` (gruesa, fina, desfases, desempate y frágil; actuado; reglas `regla` y `reactiva`), sin mult5, franja ni
MP. Costo: el de la celda aleatoria de su caso × 1.10. Las celdas `mixa_<caso>` (arranque lento) no se ajustan:
juegan los archivos de `mix_<caso>` (`--programa mix_<caso>_r10f.add.xml`, `--programa mix_<caso>_actuado_aj.add.xml`,
`--regla-de barridos/mix_<caso>/regla.json`).

### 2.6 Salidas por trabajo (para el generador y la cola)

Todas bajo `plan3/`; `B` = `barridos/<esc>/`. "Siempre" son las que deben existir al terminar con código 0; "a veces"
dependen de lo que salga.

| Trabajo | Siempre | A veces |
|---|---|---|
| `barrer_fino.py <esc> --etapa E --trozo k/n` | `B/trozos/E_t<k>de<n>.csv` | |
| `... --etapa gruesa` | `B/gruesa.csv`, `B/gruesa_semillas.csv`, `B/fijo_grueso10.json`, `<esc>_r10g.add.xml` | |
| `... --etapa fina` / `desfases` / `desempate` | `B/<etapa>.csv`, `B/<etapa>_semillas.csv` | |
| `... --etapa fragil` | `B/fragil.csv`, `B/fragil_semillas.csv`, `B/fijo_fino.json`, `<esc>_r10f.add.xml` | |
| `... --etapa mult5` | `B/mult5.csv`, `B/mult5_semillas.csv`, `B/mult5_desempate.csv`, `B/mult5_desempate_semillas.csv`, `B/fijo_mult5.json`, `<esc>_m5f.add.xml` | `B/mult5_fragil.csv`, `B/mult5_fragil_semillas.csv` (si es frágil) |
| `franja.py <esc>` | `B/franja.csv`, `B/franja_final.csv`, `B/franja_semillas.csv`, `B/franja.json`, `<esc>_franja.add.xml` | |
| `franja.py <esc> --bloques` | `B/bloques.csv`, `B/bloques_semillas.csv`, `B/bloques.json`, `<esc>_bloques.add.xml` | |
| `actuado.py <esc> --paso k` (1-6) | `B/actuado_paso<k>.csv`, `B/actuado_paso<k>_semillas.csv`, `B/actuado_paso<k>.json` | |
| `actuado.py <esc> --paso final` | `B/actuado_final.csv`, `B/actuado_final_semillas.csv`, `B/actuado_aj.json`, `<esc>_actuado_aj.add.xml` | |
| `reglas.py <esc> --familia F` | `B/reglas_F.csv`, `B/reglas_F_final.csv`, `B/reglas_F_semillas.csv`, `B/F.json` (`regla.json`, `reactiva.json`, `mp.json`) | |
| `p3_preparar.py <esc> ...` | `<esc>_actuado.add.xml`, `<esc>_trivial.add.xml` (y `<esc>_actuado_aj.add.xml` con `--piezas actuado_aj`) | |

Además todos escriben su caché en `tmp_fino/<esc>/` (ignorada por git). Ejemplo, P6 con llegadas aleatorias
(trozos de ~2 h según la tabla 2.3; el generador calcula n con `TROZO_MAX_H`):

```
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa gruesa --trozo 0/3   (1/3 y 2/3)
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa gruesa
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa fina --trozo 0/4     (1/4, 2/4, 3/4 y luego sin --trozo)
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa desfases
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa desempate
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa fragil
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa mult5
python ../con_escenarios.py franja.py poi_malla3_alta
python ../con_escenarios.py actuado.py poi_malla3_alta --paso 1      (2, 3, 4, 5, 6 y final, en cadena)
python ../con_escenarios.py reglas.py poi_malla3_alta --familia regla   (y --familia reactiva, --familia mp)
```

### 2.7 Cada noche y la evaluación

- Al empezar la noche: `python p3_preparar.py <esc> ...` (actuado y ciclo mínimo). El actuado ajustado lo instala
  `actuado.py --paso final`; `--piezas actuado_aj` solo para reponer un archivo que falte (no toca uno igual al
  congelado). Las evaluaciones de actuado y ciclo mínimo dependen de "preparar".
- Brazos (`evaluar.py`, cwd = `plan3/`; con estos brazos `--semillas` es obligatorio): `--brazo fijo --programa
  <esc>_r10f.add.xml --nombre fino --semillas S` (fijo fino), `--programa <esc>_m5f.add.xml --nombre mult5`,
  `--programa <esc>_r10g.add.xml --nombre grueso10`; `--brazo franja`, `--brazo bloques`, `--brazo actuado_aj`
  (archivo por defecto `<esc>_<brazo>.add.xml`, o `--programa`); `--regla <"regla" de regla.json, reactiva.json o
  mp.json>`. Las tandas decisivas van por `evaluar3.py` (a ciegas; `--regla-de barridos/<esc>/<familia>.json`).

### 2.8 Ensayo de la cadena real (corredor, 05.11, verificación de 6e8cfab)

En un worktree aparte (`w3_ensayo_ref`, commit 1884c93, cuyo código de las referencias es el de 7714544 salvo
`evaluar3` y `p3_congelar`, que solo cambiaron de dónde leen el JSON congelado), con `cwd = plan3/`: los trabajos de
referencias del corredor tal como los arma `generar_trabajos3.generar(["referencias"])`, sin opciones de prueba y con
las semillas de la regla, por `cola.py --cpus 2 --sin-git`.

- **La cola:** 17 trabajos (gruesa, fina, desfases, desempate, frágil, mult5, franja, actuado 1-6 y final, regla,
  reactiva y MP; el corredor no tiene trozos), 0 fallidos, todos con sus salidas declaradas, de 17:13 a 17:38 (25 min de
  reloj con 2 CPU; el generador estima 0.93 h-p). Todos los JSON salen sin marca de prueba.
- **Los ganadores** (semillas de ajuste; no deciden nada): fijo fino 22/10, desfases 0/17 (los dos primeros quedaron a
  ≤ 2 %: desempate de los 3 primeros con 2001-2030, 20.87 s/veh); verdes de 5 en 5 25/10, 0/24 (21.13); fijo desde 10 s
  20/10, 0/15 (20.88, el de `plan2`); franja 20/10 0/25 → 22/10 0/13 (20.48 en 2001-2010; los dos cambios estrictos,
  14 s tarde a lo sumo); actuado ajustado, la coordinada (a) con `detector-gap` 3 (19.66 en 2001-2010); `regla_u1g60`
  (35.68), `reactiva_d25` (22.87), `mp_c60` (25.43).
- **`evaluar3` frente al barrido:** cada brazo de `brazos_ref("corredor")` (fino, fino5, franja, actuado_aj, regla,
  reactiva, MP), más el fijo desde 10 s y el actuado ajustado con `--programa` (como en `mixa_`), con 2001-2003: el
  retraso total de cada semilla es el de la fila del ganador en `barridos/corredor/*_semillas.csv`, en los 9 brazos.
  `sha_ref` sale en cada CSV. (Bloques no entra: es del perfil.)
- **Las reglas en las otras familias** (humo, `--familia reactiva --semillas 424301 --semillas-final
  424301-424302`): `per_corredor`, `mix_corredor`, `malla3_alta_e` y `poi_red` por el lanzador, y
  `dem_corredor_t2715_der` y `red` directo: 6 de 6 con código 0 y un `reactiva.json` correcto.

---

## 3. Contrato para `evaluar3.py`

Cada función devuelve `(brazo, modelo, base, correr)`; `correr(semilla, tripinfo, serie)` devuelve el dict de
métricas de siempre (`retraso_total_prom`, `timeloss_prom`, `no_insertados`, `cambios_fase`...) y no imprime ni
escribe nada fuera del tripinfo y la serie que pide el llamador (los brazos nuevos no regeneran archivos: leen el
suyo; los entregados `actuado` y `trivial` siguen regenerando su `.add.xml`, de forma atómica).

```python
evaluar.brazo_referencia(esc, brazo, adicional=None)
    # brazo en "fijo", "actuado", "trivial", "franja", "bloques", "actuado_aj". adicional = ruta del .add.xml, solo con
    # franja, bloques y actuado_aj (por defecto <esc>_<brazo>.add.xml); con fijo, actuado o trivial es un error (el fijo
    # de otro archivo es brazo_programa). Brazo y modelo = brazo.
evaluar.brazo_programa(esc, ruta, nombre)
    # fijo con el programa de ruta (reemplaza a los adicionales del .sumocfg que traen <tlLogic>). Brazo "fijo_<nombre>".
evaluar.brazo_regla(esc, regla)
    # regla de plan3/reglas.py: regla_u<U>g<G>, reactiva_d<D> (D en 15, 25, 35, 50, 70), mp, mp_det, mp_c<C>,
    # mp_det_c<C>. Brazo = regla. Corre por rl_ippo (gancho decidir): cambios_fase con el +k de la plantilla (6.10).
```

Los brazos de plan3 (franja, bloques, actuado_aj, `brazo_programa` y `brazo_regla`), y también `trivial`, se niegan en
`cruce` y `cruce2` (`rl_semaforo` no conoce esos modos). Por debajo: `rl_corredor.correr_episodio(modo, ..., adicional=None)` con los
modos `franja`, `bloques` (sin `setProgram`: los cambia su WAUT) y `actuado_aj` (`setProgram("actuado_aj")`); en
`baseline`, `adicional` da el fijo de ese archivo. Sin modos nuevos ni `adicional`, el comando de sumo es el de antes.

Para `veredicto3`: los nombres de la reactiva siguen `reactiva_d<D>` con D en 15, 25, 35, 50 o 70 (`reglas.validar`
usa `fullmatch` y rechaza los que no son de la rejilla); su ganadora queda en `barridos/<esc>/reactiva.json`, clave
`"regla"`; el generador la evalúa con el tipo `ref_reactiva` (`brazos_ref` de `generar_trabajos3.py`).

`evaluar3.py` (tercera vuelta): un solo brazo por comando (`--brazo`, `--politica`, `--regla` y `--regla-de` son
excluyentes; `--programa` solo con fijo, franja, bloques o actuado_aj; `--nombre` solo con `--brazo fijo
--programa`; opciones completas); `--regla-de` se niega si el JSON trae la marca de prueba, si su familia no es la del
nombre del archivo o si es de otro escenario (`mixa_<x>` juega el de `mix_<x>`); la columna `sha_ref` y la negativa a
ciegas de 1.6; y `validar_args(argv)` para `chequeos_previos`.

---

## 4. Pruebas

Todas corren con `cwd = plan3/` y escriben solo en `plan3/tmp_ref/` (ignorada) y en `plan3/pruebas/ref/salidas/`.
Semillas: de humo (424301-424360) salvo (1) la reproducción del barrido entregado (2001-2003, las suyas), (2) la no
regresión (1001-1002, solo controles entregados) y (3) `prueba_cadena_p1`, que corre en su copia la fina, los
desfases, el barrido de mult5 y los 9 pares de la franja de P1 con 2001-2003 (las del barrido de P1; sus desempates y
finales van con humo, y nada de esa copia se instala ni se usa después), y (4) el ensayo de 2.8, en un worktree
aparte, con las semillas de ajuste de la regla (2001-2030). Las semillas del examen y de la final (7001, 8001 y 13120)
solo aparecen en la prueba de la guarda de `prueba_fino` F, con `subprocess.run` reemplazado: no se simula ninguna. A
lo sumo 3 sumo a la vez, y las corridas pesadas solo de 07:30 a 20:30.

| Prueba (tarea) | Qué comprueba | Resultado |
|---|---|---|
| `prueba_fino.py` (0.7) | A. La regla con datos inventados (mínimos locales, umbral de 2 errores estándar, frágiles) y el borde del 2 % (`a_2pct` en 9500 casos, los ejemplos de la revisión, la frágil con 20.50 y 20.91). B. Reproduce `plan2/barrido_<esc>.csv` con 2001-2003 (P1 65 de 65 filas y el ganador; P2-P6 3 de 3) y el lector = `evaluar_config`. C. Dos corridas (una en 2 trozos y la unión) dan los mismos archivos. D. Puntaje por periodo en tres casos con vehículos sin entrar. E. Huella: repetir no corre nada; los fines de línea de `comun.py` no la cambian; un comentario en `comun.py` sí, y se vuelve a correr todo con el mismo `gruesa.csv`; los interruptores de `comun`. F. Cadena: entradas de prueba, otras semillas, frágil sin reescribir el desempate y con sus negativas, el paso 6 del actuado con la huella de `fijo_fino.json`, cwd, abreviaturas y las semillas del examen negadas antes de lanzar sumo | PASA (34 de 34) |
| `prueba_cadena_p1.py` (0.7-0.11) | La cadena completa en P1 por la línea de comandos sobre la gruesa de una subrejilla (con `--permitir-prueba`; sin él la fina se niega); cada ganador jugado por TraCI reproduce su media (fijo fino, verdes de 5 en 5, franja, actuado ajustado, regla, reactiva y MP); `p3_preparar` no toca el actuado ajustado congelado y lo recrea igual; actuado y ciclo mínimo = el `comun.py` entregado | PASA (27 de 27), con los mismos números que en d01c2a6 (fijo fino 22/10 0/17, 20.90; franja 20.59; el mismo sha256 del actuado ajustado; `reactiva_d25` 22.71) |
| `prueba_franja.py` (0.8) | 1-5 como antes (franja = fijo con el mismo plan; cambio alineado; 0 cortes; sumo directo = TraCI; bloques). 6. Cuatro pares que antes abortaban: cambian en su instante, entran alineados, 0 verdes cortados, 0 ámbares cortos tras un verde, ningún verde relajado de menos de 10 s, y sumo directo (el barrido) = TraCI (el brazo franja) también con estos programas no estrictos. 7. 3000 pares al azar: el instante estricto es el de antes donde existía; 13993 estrictos, 0 relajados, 7 respaldos, 0 forzados; ninguno corta un verde ni deja un ámbar corto; los 5 estrictos de más de 300 s se avisan | PASA (50 de 50) |
| `prueba_actuado.py` (0.9) | 1-4 como antes (defecto = actuado entregado; cada parámetro mueve; sin avisos de SUMO; sumo directo = TraCI, también con las dos coordinadas). 5. `reinstalar` y `p3_preparar`. 6. La coordinada (b) con un plan con holgura y `maxDur` = los verdes fijos termina la avenida en el fin fijo (P2, P3 y P6: tantas salidas como el plan fijo y a lo sumo 2 fuera, el arranque). 7. Los detectores: 27.8 m con `detector-gap` 2 y 43.2 m con 4 (P1 y P6) | PASA (33 de 33); en 4, la (a) de P3 y P6 cambió (22.55 y 118.13, antes 21.61 y 115.94) por el arreglo de la coordinación |
| `prueba_reglas.py` (0.10) | 1-4 como antes (U = ∞ = ciclo mínimo; máscara; presión; `evaluar.py --regla`). 5. La reactiva: nombres (y los de fuera de la rejilla, con ceros o con un salto de línea, rechazados), barrido `--familia reactiva`, `evaluar.py --regla reactiva_d25`, máscara y lógica, mismo tripinfo que la lógica del prototipo (P1 y P6). 6. Protecciones de `evaluar.py` (también `trivial` en `cruce`). 7. Oráculo independiente (`getNextTLS`): 0 diferencias en 856 y 5468 decisiones libres; reloj: separaciones de 5 s tras alargar y 8 s tras cambiar, verdes de 10-60 s en pasos de 5. 8. La huella de las reglas cambia con cada uno de sus archivos | PASA (28 de 28) |
| `prueba_atomica.py` (0.11) | 3 evaluaciones simultáneas; temporal borrado si el reemplazo falla; `leer_cfg` con espacios | PASA (5 de 5) |
| `prueba_aleatorias.py` (0.7-0.10) | Las referencias con llegadas aleatorias y con el perfil, por el lanzador | PASA (19 de 19), con los mismos números (bloques 230.88) |
| `prueba_comandos_ref.py` (G1-F4 y otros) | 894 comandos del generador pasan el parser de su script; 8 errados se rechazan con su motivo; ids, `--trozo k/n`, salidas y uniones de los 51 trozos; presupuestos y salidas declaradas; `referencias_congeladas.json` en las evaluaciones a ciegas de referencias; huérfanos por pid (unitaria) | PASA (6 de 6) |
| `prueba_congeladas.py` ([21]) | `sha_ref`; a ciegas, las tres negativas antes de simular y la corrida con la referencia congelada; `--regla-de` y sus negativas (y `mixa_`); `p3_congelar` y `chequeos_previos` | PASA (6 de 6) |
| `prueba_no_regresion.py` (0.12) | Fijo, actuado, ciclo mínimo e IPPO (base 42) en P1-P6 con 1001-1002, todas las columnas, en el código final (la cabecera dice commit y sha256 de `comun.py`, `rl_ippo.py`, `evaluar.py` y `rl_corredor.py`); `veredicto.py --probar` | PASA (25 de 25): 23 brazos iguales en las 34 columnas y P6 IPPO con la diferencia conocida (`cambios_fase` −4) |
| `prueba_nr_p6.py` (0.12) | La diferencia de P6 IPPO no es una regresión | PASA (2 de 2) |
| `ensayo_comparar.py` (ensayo, 2.8) | Los JSON del barrido del ensayo sin marca de prueba; cada brazo de referencia del corredor por `evaluar3` = la fila del ganador, semilla por semilla | PASA (10 de 10) |
| `tabla_coordinadas.py`, `medir_coordinada.py` | Mediciones (sin chequeos): la tabla de 6.5 y los histogramas de 1.3 | `salidas/tabla_coordinadas.txt`, `salidas/medir_coordinada.txt` |

En total, 245 chequeos en 12 scripts, todos sobre el código final (7714544; `ensayo_comparar` sobre la cola del
ensayo, 1884c93). Salidas en `plan3/pruebas/ref/salidas/<prueba>.txt`.

---

## 5. Decisiones de implementación (lo que el plan no fijaba)

| Punto | Decisión | Por qué |
|---|---|---|
| Mínimo local de la gruesa | Par de verdes cuyo mejor retraso (sobre sus desfases o esquemas) no supera al de sus vecinos a un paso en un eje (vecindad de 4) | Reproduce lo que medía el informe de referencias: malla3 con 3 mínimos a ≤ 2 % (10/10, 25/15 y 30/10) |
| "A ≤ 2 %" | `a_2pct`: en centésimas enteras, la misma en la fina y en la frágil | Las medias llegan redondeadas a 0.01; en coma flotante el borde exacto salía distinto en una y otra |
| Patrones de desfase en la fina | Los 3 mejores de la gruesa en el par del mínimo, tomados módulo el ciclo de cada par fino | Un desfase es un corrimiento en segundos; módulo el ciclo es el mismo programa |
| Desfases finos | Alrededor del mejor plan de **cada** región (tope 3); el primer semáforo queda en 0 | "Alrededor de cada mínimo local" |
| Malla | Sin desfases libres: la fina usa los 3 esquemas y `onda_oe`; el fijo de verdes de 5 en 5 agrega `onda_oe` | Como `barrer_fijo` y el prerregistro |
| Empates | Primero el de menor media redondeada a 0.01 (como `barrer_fijo`); en empate, el que se generó antes | Reproduce el ganador de `barrer_fijo` |
| Frágiles con llegadas aleatorias | La regla se evalúa y se informa, pero no corre nada: los finalistas ya tienen 2001-2030 | Es lo que dice la regla |
| Puntaje por periodo | Media de los retrasos medios por semilla de cada periodo (como la hora); los no insertados cuentan con su espera hasta el cierre | Igual que la métrica de la hora |
| Huella de la caché | sha256 completo de los archivos de código, no solo de las funciones que corren | Un arreglo en el lector (`comun.leer_tripinfo`) o en la forma de cargar el programa no heredaba números viejos; con el archivo entero no se escapa nada (a costa de repetir la celda ante cualquier cambio) |
| Cadena de etapas | Registro en el JSON de la gruesa (y de cada salida con JSON) y semillas por plan en cada `_semillas.csv`; sin archivos nuevos | La regla se comprueba con lo que ya se escribe; la cola no cambia sus salidas declaradas |
| Franja | Siempre dos programas y un cambio, aunque los dos periodos elijan el mismo plan | Así "franja con plan 2 = plan 1" prueba el mecanismo |
| Instante de cambio | Estricta (mismo estado en t − 1, t y t + 1), y solo si no hay en un hiperperíodo, relajada, respaldo y forzado | La estricta es la de B8 y no cambia ningún programa donde existe; las otras evitan abortar sin cortar verdes |
| Bloques | Si dos bloques seguidos eligen el mismo plan, no hay cambio; si todos eligen uno, no hay WAUT; exige el fijo fino | Menos cambios; `bloques.json` no depende del orden de la cola |
| Actuado: dependencias | Pasos 1-5 sin dependencias; el 6 depende del fijo fino | Solo las coordinadas usan el fino |
| Actuado coordinado | Dos candidatas en el paso 6: (a) solo `earliestEnd` en la avenida y (b) `earliestEnd` = `latestEnd` en la avenida y `latestEnd` en la transversal | Una candidata más solo hace más fuerte la referencia que veta FUNCIONA |
| Actuado y reglas con llegadas aleatorias | Barrido con 2001-2003, finalistas 10 con 2001-2030 | La tabla de §5 lo dice así |
| Regla reactiva | Carriles con verde = carriles de entrada con algún enlace `G` o `g` en el estado actual; distancia a la línea = largo del carril − posición; los vehículos ya en el cruce (carriles internos) no cuentan | Es la lógica del prototipo, que se reproduce tripinfo a tripinfo |
| Max-Pressure y reactiva | Familias aparte, elegidas como la regla | Solo descriptivas o al lado; así se informa la mejor de cada una |
| Nombres de reglas | `regla_u<U>g<G>`, `reactiva_d<D>`, `mp`, `mp_det`, `mp_c<C>` | Contrato con `evaluar3` (nombre con los parámetros) |
| Programa del fijo fino | `programID="fijo"`; reemplaza a la plantilla en `--additional-files` | Es lo que habría instalado `barrer_fijo --instalar` |
| Ciclo de las variantes coordinadas | Contado desde el inicio del verde transversal del plan fijo (`offset` = el del fino + ese inicio) | Con la avenida en la fase 0, SUMO dejaba sin efecto `earliestEnd`/`latestEnd` en la mitad de los ciclos (1.3); son los mismos instantes del plan fijo |
| `maxDur` de la avenida en las coordinadas | (b): el ciclo; (a): el ciclo menos los ámbares y los `minDur` de los otros verdes | (b) no puede pasar de su fin (`latestEnd`) y con menos un arranque corto se perpetuaba; (a) puede alargar, así que solo se le da lo que necesita para llegar a su fin |
| WAUT relajada | Solo si ningún verde que toca el cambio dura menos de 10 s; si no, respaldo | Pedido de la verificación (G3-1); la estricta no cambia |
| WAUT tardío | Se avisa (JSON, comentario y consola), no se topa | Un tope cambiaría la regla de B8: enmienda |
| Huella del fijo fino al leerlo | La de su propio barrido (sus cortes, anotados en el JSON) | El actuado corre siempre con cortes de 1800 s y el perfil barre con 600: compararla con la del lector la negaría siempre |
| `referencias_congeladas.json` | Clave: la ruta, relativa a `plan3/`, del archivo que carga cada brazo; lo escribe `p3_congelar.py` solo si todo cuadra | Es lo que `evaluar3` puede resolver sin leer el generador; un solo problema impide escribirlo |
| `validar_args` | El parser y sus `ap.error`, sin leer el escenario ni tocar archivos | `chequeos_previos` lo corre para cada comando de la lista, como ya hacía con `rl_ippo` |

## 6. Pendiente o dudoso

1. **La variante coordinada cambió después del tag** (1.3): el actuado ajustado veta FUNCIONA, así que el cambio se
   declara (`desviaciones.md` §3, borrador para la parte B, con el commit y los blobs del código que corre). Es lo que
   §5 describe; lo que el tag hacía no lo era.
2. **Un cambio de código repite la celda entera.** Con la huella, tocar `comun.py`, `barrer_fijo.py`,
   `escenarios_plan2.py` o `barrer_fino.py` (o, en las reglas, `rl_ippo.py`, `rl_corredor.py`, `reglas.py`,
   `escenarios_plan3.py` o `con_escenarios.py`) invalida todo lo guardado; las etapas siguientes se niegan a leer
   salidas de la huella vieja (también `fijo_fino.json`), así que la cadena se relanza desde la gruesa. El procedimiento
   B22 de las referencias (salidas viejas a `barridos_viejos/<esc>_<fecha>/` y ids `_r2`, que el generador tendría que
   dar a esa celda en lugar de los viejos) está en `desviaciones.md` §3. Conviene no tocar esos archivos desde la
   primera noche de referencias. La versión de SUMO no está en la huella: la vigila la capa 3 de `protecciones.py`.
3. **El instante estricto puede llegar tarde.** La regla estricta busca en un hiperperíodo: con ciclos que difieren en
   pocos segundos el primer instante limpio puede caer minutos después del corte (en 3000 pares al azar de P1, P3 y
   P6, hasta 708 s; el respaldo hasta 33 s; con ciclos más largos o más parecidos puede pasar de 1300 s). No lo cambié
   (cambiaría programas que hoy existen): ahora se anota y se avisa (más de 300 s, después del cambio siguiente o de
   la hora). Un tope (por ejemplo, preferir la relajada si la estricta llega más de un ciclo tarde) es una enmienda de
   B8.
4. **P6 10/10 no deja vehículos sin entrar a los 6000 s.** La prueba del lector se hizo además con P6 10/25 (541 sin
   entrar) y P2 10/25 (792): mismo total, y la salida programada de cada no insertado es la de su flujo.
5. **Variantes coordinadas del actuado.** Dos candidatas en el paso 6 (decisión del 05.11): (a) solo `earliestEnd` en
   la avenida, y (b) `earliestEnd` = `latestEnd` en la avenida **y** `latestEnd` en la transversal. Retraso total
   (s/veh) con la semilla 424301; entre paréntesis, salidas del verde de avenida en el fin del plan fijo / salidas, en
   el semáforo que peor sale (`pruebas/ref/tabla_coordinadas.py`; antes = el código de 6e8cfab):

   | | fijo | actuado | (a) antes | (a) ahora | (b) antes | (b) ahora |
   |---|---|---|---|---|---|---|
   | P1, fijo entregado | 21.91 | 21.49 | 21.19 (75/164) | 21.19 (75/164) | 21.91 (166/166) | 21.91 (166/166) |
   | P2, fijo entregado | 392.73 | 437.26 | 446.78 (12/73) | 446.78 (12/73) | 394.4 (128/129) | 394.4 (128/129) |
   | P3, fijo entregado | 20.14 | 21.46 | 21.61 (2/216) | 22.55 (11/209) | 20.14 (231/231) | 20.14 (230/230) |
   | P6, fijo entregado | 82.57 | 114.64 | 115.94 (60/143) | 118.13 (69/144) | 82.57 (194/194) | 82.57 (193/193) |
   | P1, plan 22/15 0/17 | 26.4 | 21.49 | 21.29 (71/139) | 21.29 (71/139) | 21.6 (139/139) | 21.6 (139/139) |
   | `dem_red_t3620`, plan 25/15 0/23/0 | 104.19 | 106.9 | 107.8 (39/146) | 103.64 (51/121) | 106.17 (84/166) | 103.32 (128/129) |

   Con el fijo entregado la (b) ya salía bien: su transversal está en el mínimo y no puede cortar antes, así que la
   avenida nunca empezaba antes. El defecto aparece cuando la transversal tiene holgura (lo normal en un fijo fino), y
   en red y malla: última fila. La (a) se comporta como un actuado libre (alarga después del fin fijo: lo dejan sus
   `earliestEnd` sin `latestEnd`); ahora su `earliestEnd` vale en todos los ciclos. Las columnas "solo `latestEnd` en
   la transversal" y "solo `earliestEnd` = `latestEnd` en la avenida" de la primera entrega (las dos mitades de la (b)
   por separado, peores que el fijo) se midieron con el código de antes.
6. **Trabajos largos.** Con llegadas aleatorias, el barrido de P3 y P4 (gruesa ~7-8 h-p), la fina de P5 (~11 h-p) y
   las reglas de P6 hay que partirlos: los barridos con `--trozo`, las reglas por `--familia`.
7. **El perfil** necesita `--bloque 600` en todas las etapas de `barrer_fino.py`; si una etapa se corre con otro
   `--bloque`, la siguiente se niega a seguir (huella distinta).
8. **La prueba de escritura atómica** corre 3 evaluaciones a la vez y no fuerza la carrera: muestra que no hay
   errores ni temporales sueltos y que el archivo es el del código entregado. El borrado del temporal cuando el
   reemplazo falla sí se fuerza (sin sumo).
9. Las duraciones son estimaciones (costos medidos con la cola llena, más 3 % por el tripinfo filtrado [S]); el
   número de regiones de la fina sale de la gruesa entregada y puede cambiar con la nueva.
10. **`cambios_fase` de los brazos de `rl_ippo` suma +k por la plantilla** (hallazgo [10]; no es de este código y no
    toqué `rl_ippo.py`). `rl_ippo.correr_episodio` pone cada semáforo en su primera fase verde, pero toma la fase
    "anterior" de la suscripción leída antes de ese `setPhase`: cada semáforo que la plantilla `<esc>.add.xml` arranca
    fuera de esa fase suma un cambio por episodio; el tráfico no cambia. Lo corren por `rl_ippo` IPPO, V2 y las tres
    familias de `reglas.py`; los brazos de `rl_corredor` (fijos, actuados, franja, bloques, ciclo mínimo) no lo suman.
    Por eso el CSV entregado de IPPO en P6 (otra plantilla) tiene +4 frente a hoy (`prueba_nr_p6`). `veredicto3`
    corrige k en los brazos de `rl_ippo`.

## 7. Los 32 hallazgos de la revisión de 0cea683, punto por punto

Con el texto completo de cada arreglo pedido (`result.confirmados[*].arreglo` de la revisión; los extractos que se
cortaban eran los de la verificación). Estado en el código final de esta rama. ✓ hecho; ◐ hecho en parte; — no se hizo
(con el motivo); "otro" = lo hizo otro bloque.

| # | Qué pedía | Estado |
|---|---|---|
| 0 | Huella con el lector: sha256 de `comun.py` y `barrer_fijo.py`; `sumo --version`; opcional, cómo se carga el programa | ✓ sha256 completo de `barrer_fino`, `barrer_fijo`, `comun`, `escenarios_plan2` (fines de línea normalizados) y de los XML del escenario. — `sumo --version` no entra en la huella: lo comprueba la capa 3 de `protecciones.py` (versión de SUMO). La forma de cargar el programa es código de `barrer_fino.py`, que ya está en la huella |
| 1 | Frágil en el borde del 2 %: misma forma que la fina o centésimas enteras | ✓ `a_2pct` para las dos; prueba en 9500 casos |
| 2 | Escribir en §5 radios, vecindad, patrones y desfases | otro ✓ (prerregistro §5, "Detalles operativos") |
| 3 | Cada etapa registra semillas, rejilla y opciones de prueba; la siguiente se niega; o rechazarlas en la cola | ✓ registro en `fijo_grueso10.json` y en cada JSON; semillas por plan en cada `_semillas.csv`; `--permitir-prueba`; la cola rechaza las opciones de prueba (otro, 7192185) |
| 4 | Variante F (`earliestEnd` = `latestEnd` en la avenida); `maxDur` no menor que los verdes del fino; escribir en §5 qué es "coordinada" | ✓ (b) con `latestEnd` también en la transversal (decisión del 05.11); `maxDur` de la avenida: el ciclo en (b), lo que necesita en (a); y el ciclo de SUMO contado desde la transversal (sin eso (b) no coordinaba en red y malla). §5 lo dice (otro) |
| 5 | WAUT sin abortar: relajada y respaldo con aviso; opcional verde ≥ 10 s | ✓ estricta, relajada (sin verdes de menos de 10 s), respaldo, forzado; aviso y registro por semáforo; aviso de tardíos |
| 6 | Declarar el tope de `detector-gap` o subir `passing-time` | ✓ declarado (docstring, informe, prerregistro) y medido: 27.8 y 43.2 m (`prueba_actuado` 7) |
| 7 | Huella de las reglas con `rl_ippo`, `rl_corredor`, `comun` | ✓ y además `reglas`, `escenarios_plan3`, `con_escenarios` (`prueba_reglas` 8) |
| 8 | Regla simple débil: opcional, contar vehículos o alargar la transversal | otro: prerregistrada tal cual; la reactiva va al lado ✓ |
| 9 | No regresión en el código fusionado | ✓ en el código final (cabecera con commit y sha256) |
| 10 | Declarar el +k de `cambios_fase` y restarlo en `veredicto3`, o leer la fase después de `setPhase` | otro ✓ (`veredicto3` resta k; desviaciones §2) |
| 11 | La noche usa el `evaluar3` de `plan3-dev` | otro ✓ |
| 12 | `brazo_referencia`: `adicional` solo con franja, bloques y actuado_aj | ✓ |
| 13 | Rechazar los brazos de plan3 en `cruce`/`cruce2` | ✓ y también `trivial` (G3-8) |
| 14 | `strip` en `comun.leer_cfg`; E2 en su propio archivo | ✓ `strip` (la misma lista en los 40 `.sumocfg`); los E2 van como pieza propia de `p3_preparar` |
| 15 | `escribir_atomico` borra su temporal si no reemplaza | ✓ (`comun` y `barrer_fino`) |
| 16 | `--semillas` obligatorio con los brazos nuevos de `evaluar.py` (o en los ejemplos) | ✓ las dos cosas |
| 17 | `reinstalar`: comprobar el sha256 antes de escribir | ✓ temporal, sha256 y luego reemplazo; si ya es igual no lo toca |
| 18 | Segunda variante coordinada en el paso 6 | ✓ (desde eeb82f7) |
| 19 | Huella con `comun`, `barrer_fijo`, `rl_corredor` (y `rl_ippo` en reglas), `sumo --version`; procedimiento B22 de las referencias | ✓ huella; procedimiento escrito en `desviaciones.md` §3 (borrador para la parte B): mover las salidas viejas a `barridos_viejos/<esc>_<fecha>/` y correr con ids `_r2` (no "los mismos ids", que chocaría con B22). — `sumo --version`: ver 0 |
| 20 | Capa 1 con lista blanca de opciones en los barridos; `uso` "ajuste"; humos fuera de la cola | otro ◐: rechaza `--avenida`, `--transversal`, `--limite`, `--semilla*`, `--llegadas` y `--permitir-prueba` y exige "ajuste" (lista negra, no blanca); los scripts no aceptan abreviaturas; `--bloque` solo se valida como divisor de la hora (no "600 y solo en per_") |
| 21 | `evaluar3` y `chequeos_previos` comparan con `referencias_congeladas.json`; el JSON en `requiere` | ✓ `sha_ref`, negativa a ciegas, `requiere`, comparación diaria y `p3_congelar.py` (formato del JSON) |
| 22 | `reinstalar` con temporal; `actuado_aj` fuera de las piezas por defecto | ✓ |
| 23 | Duraciones con las fórmulas del resumen | otro ✓ (05e8feb) y ✓ aquí el reparto de las reglas por familia y llegadas, sin EMPAQUE doble, y los pasos del actuado por sus corridas (G1-F5) |
| 24 | `r_bloques` requiere `r_fragil` | otro ✓ (generador) y ✓ `bloques` exige `fijo_fino.json` con su huella |
| 25 | Huérfanos por pid en la cola | otro ✓ (05e8feb); ✓ prueba unitaria con comandos prefijo y pid reusado (`prueba_comandos_ref` 6). — La prueba de integración (matar la cola con dos trabajos así y relanzarla) no se hizo |
| 26 | Ids de los trozos con n | otro ✓; ✓ chequeo estático de ids, `--trozo k/n`, salidas y uniones (`prueba_comandos_ref` 3) |
| 27 | Frágil lee el desempate; declarar los `*_semillas.csv` | ✓ las dos |
| 28 | `*.tmp` en `.gitignore` y limpieza en `p3_noche` | otro ✓ |
| 29 | Abortar fuera de `plan3/` | ✓ |
| 30 | Capa 1 exige `--semillas` en `../evaluar.py` y `evaluar3.py`; ejemplos con `--semillas` | otro ✓ en `../evaluar.py` (capa 1); `evaluar3` lo exige su parser y ahora `chequeos_previos` valida cada comando con ese parser (G1-F4); ✓ ejemplos |
| 31 | Informe al día | ✓ |
