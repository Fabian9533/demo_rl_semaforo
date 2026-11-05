# Referencias del plan 3 (tareas 0.7-0.12): informe de implementación

05.11.2026. Rama `plan3-ref` (nació de `plan3-dev` en 223f908). Segunda vuelta, la tarde del 05.11: los arreglos de
la revisión de 0cea683 (32 hallazgos confirmados; aquí, los de las referencias) y la regla reactiva (4faffb7, sobre
`plan3-dev` fusionado en d2501e5); después, `plan3-dev` otra vez (a742e1b: las semillas del examen y de la final
solo desde la cola) y la misma guarda antes del sumo directo de `barrer_fino.py` (d01c2a6). Las pruebas corrieron
enteras en 4faffb7 y otra vez en d01c2a6, el código final; este informe y esas salidas van en el commit siguiente.

## Respuesta corta

- **Qué hay.** Cinco scripts nuevos en `plan3/` y cambios mínimos, apagados por defecto, en tres archivos entregados:

  | Archivo | Tarea | Qué hace |
  |---|---|---|
  | `plan3/barrer_fino.py` | 0.7 | Fijo fino (regla del prerregistro §5), fijo con verdes de 5 en 5 y el ganador de la gruesa ("fijo desde 10 s"), con puntaje por periodo |
  | `plan3/franja.py` | 0.8 | Fijo por franja (un plan por media hora) y fijo por bloques del perfil, con un WAUT por semáforo en su instante de cambio |
  | `plan3/actuado.py` | 0.9 | Actuado ajustado: descenso por coordenadas en cadena, `delay_based` y dos variantes coordinadas con el fijo fino |
  | `plan3/reglas.py` | 0.10 | Regla simple U × G, **regla reactiva** (D m) y Max-Pressure para el gancho `decidir` de `rl_ippo`, y su barrido por familia |
  | `plan3/p3_preparar.py` | 0.11 | Trabajo "preparar" de cada noche: `_actuado` y `_trivial` (y `_actuado_aj` solo si se pide) |
  | `comun.py` | 0.11 | `archivo_actuado` y `archivo_trivial` escriben en un temporal y reemplazan (mismo contenido, byte a byte); `leer_cfg` quita espacios de las rutas (la misma lista con los `.sumocfg` de siempre) |
  | `rl_corredor.py` | 0.7-0.9 | Modos `franja`, `bloques` y `actuado_aj`, y `adicional=` (fijo de otro archivo); sin ellos nada cambia |
  | `evaluar.py` | 0.7-0.10 | `--brazo franja`, `bloques` o `actuado_aj`, `--brazo fijo --programa --nombre`, `--regla`; funciones para `evaluar3` |

- **Lo que cambió con la revisión:**

  | Hallazgo | Arreglo |
  |---|---|
  | [0, 7, 19] La caché reutilizaba números viejos si cambiaba el código | La huella lleva el sha256 completo de `barrer_fino.py`, `barrer_fijo.py`, `comun.py` y `escenarios_plan2.py` (en `reglas.py`, también `reglas.py`, `rl_ippo.py` y `rl_corredor.py`) y los interruptores `ESCRIBIR_NO_INSERTADOS` y `QUITAR_BLOQUE` de `comun` |
  | [1] La regla frágil fallaba en el borde exacto del 2 % | Una sola función, `a_2pct`, en centésimas enteras, para la fina y la frágil |
  | [3] Las etapas seguían sin mirar con qué semillas y qué rejilla corrió la anterior | La gruesa registra llegadas, semillas, rejilla, `--limite` y opciones de prueba; cada etapa compara lo que lee con la regla y se niega si no lo es (salvo `--permitir-prueba`) |
  | [5] El instante limpio del WAUT a veces no existía y abortaba la franja | Ya no aborta: regla estricta (la de siempre), relajada, respaldo y forzado; `franja.json` y `bloques.json` anotan la regla y el retraso de cada cambio |
  | [6] `detector-gap` 4 queda topado | Declarado: SUMO lo deja en 43.2 m (≈ 3.1 s) |
  | [9] La no regresión se había corrido con otro código | Corrida otra vez sobre el código fusionado; la salida dice commit y sha256 |
  | [12, 13, 16] `evaluar.py` aceptaba combinaciones sin sentido | `adicional` solo con franja, bloques y actuado_aj; nada de plan3 en `cruce`/`cruce2`; `--semillas` obligatorio en sus brazos |
  | [14] `comun.leer_cfg` sin `strip` | Con `strip` |
  | [15] `escribir_atomico` dejaba su temporal | Lo borra si no llega a reemplazar |
  | [17, 22] `reinstalar` pisaba el archivo antes de comprobarlo | Temporal, sha256 y solo entonces reemplazo; si ya es igual, no lo toca; `actuado_aj` fuera de las piezas por defecto |
  | [20] Abreviaturas de opciones | `allow_abbrev=False` en los cinco scripts |
  | [24] Bloques no dependía de frágil | `bloques` exige `fijo_fino.json` (y lo pone al lado con las mismas semillas) |
  | [27] Frágil reescribía el desempate | Lo lee y comprueba que sea el de las etapas; `Celda.cargar` reintenta si Windows niega el acceso |
  | [29] Sin comprobar el cwd | Se niegan fuera de `plan3/` |
  | [31] Informe desactualizado | Este |
  | Nuevo | Familia `reactiva` en `reglas.py` |
  | Nuevo (de `plan3-dev`, 682b6c2) | `barrer_fino.correr_periodos` llama a `comun.revisar_semilla_ciega` antes de cada sumo: una semilla del examen o de la final sale con error si el proceso no es un trabajo ciego de la cola (`franja.py` y `actuado.py` corren por ahí; `reglas.py` por `rl_ippo` → `comun.iniciar_sumo`, que ya la llama) |

- **Números:** ningún número de lo entregado ni de las pruebas anteriores cambia. Cambian las huellas (y por eso se
  vuelve a correr todo lo guardado, con los mismos resultados) y aparecen números nuevos donde antes no había: la
  familia reactiva y los pares de franja sin instante estricto (antes abortaban).
- **Pruebas: pasan las nueve** (210 chequeos; sección 4), en el código final (d01c2a6) y antes en 4faffb7. Lo
  nuevo: la regla reactiva da el mismo tripinfo que la lógica del prototipo (P1 y P6) y respeta la máscara; la huella
  cambia si cambia `comun.py` (y entonces se vuelve a correr todo, con los mismos números) y no si solo cambian sus
  fines de línea; las etapas se niegan a leer entradas de prueba; frágil lee el desempate sin tocarlo; los pares de
  franja sin instante estricto ya no abortan y no cortan verdes; `reinstalar` no pisa nada que no sea el congelado.
- **No regresión** (código final, d01c2a6; la salida dice commit y sha256 de `comun.py`, `rl_ippo.py`, `evaluar.py` y
  `rl_corredor.py`): 23 de 24 brazos repiten dígito a dígito sus CSV entregados; el 24.º, IPPO en P6, difiere solo en
  `cambios_fase` (4 menos que el entregado en cada semilla), la diferencia ya explicada: el código entregado corrido
  hoy da lo mismo y el CSV entregado se corrió con otra plantilla (`prueba_nr_p6`, 2 de 2). `veredicto.py --probar`
  pasa.
- **Lo dudoso** está en la sección 6. Lo principal: el instante estricto del WAUT puede llegar tarde (hasta 708 s en
  3000 pares al azar; ahora queda anotado); y para que la cola rechace `--permitir-prueba` hay que sumarlo a las
  opciones de prueba de `protecciones.py`.

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
salida queda marcada como de prueba. La cola no debe pasar `--permitir-prueba` (sección 6).

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
  cambia), verificada con 2001-2030. Va después de `fragil`: exige `fijo_fino.json` y pone al lado el fijo fino con
  las mismas semillas (`fijo_fino_mismas_semillas`), así `bloques.json` no depende del orden en que corra la cola.
- **WAUT (B8):** un `<WAUT>` por semáforo, sin `procedure`; el plan nuevo entra alineado con su propio desfase. El
  instante de cambio de cada semáforo es el primero desde el corte (y después del cambio anterior) que cumple, en
  este orden:

  | Regla | Cuándo | Qué se ve en el semáforo |
  |---|---|---|
  | estricta | los dos planes muestran el mismo estado en t − 1, t y t + 1 (la de siempre) | nada: el cambio no se nota |
  | relajada | si no hay estricta en un hiperperíodo: el paso del estado viejo al nuevo es uno que haría un plan normal | ningún verde pasa a rojo sin ámbar, ningún ámbar queda corto, ningún rojo pasa a ámbar ni ningún ámbar a verde; el verde que toca el cambio puede quedar corto |
  | respaldo | si tampoco: el primer fin de un ámbar del plan viejo sin verde a rojo ni ámbar corto | los enlaces que terminaron su ámbar pueden seguir en ámbar o pasar a verde, y uno en rojo puede ver un ámbar; ninguno corta un verde |
  | forzado | si ni eso (no pasa con las plantillas de P1-P6: sus ámbares no tienen verdes) | el primer fin de ámbar del plan viejo, con los problemas anotados |

  `franja.json` y `bloques.json` traen `cambios`: por semáforo y por cambio, la regla, el instante nominal, el
  instante y el retraso (instante − nominal), la cuenta por regla, el retraso máximo y un aviso si alguno no fue
  estricto (el aviso va también en el comentario del `.add.xml`; con todos estrictos el archivo es el de siempre).
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
- **Dos variantes coordinadas** (prerregistro §5): `coordinated=true`, `cycleTime` y desfases del fijo fino, las fases
  de su plantilla con sus duraciones y los parámetros del mejor actuado; (a) el verde de avenida con `earliestEnd` en
  su fin del plan fijo, y (b) "fin fijo": `latestEnd` = `earliestEnd` en la avenida **y** `latestEnd` en la
  transversal, cada uno en su fin del plan fijo. El paso 6 corre las dos.
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
- Nombres (patrón `^(regla_u(\d+|inf)g\d+|reactiva_d\d+|mp(_det)?(_c\d+)?)$`):
  - `regla_u<U>g<G>` (U entero o `inf`; `regla_uinfg60` es el ciclo mínimo);
  - `reactiva_d<D>`: **regla reactiva**, alarga cualquier verde mientras haya un vehículo a ≤ D m de la línea de
    detención en algún carril con verde (enlace `G` o `g` en el estado del semáforo; distancia = largo del carril −
    posición del vehículo); si no hay ninguno, cambia. Es la lógica del prototipo
    `analisis_mejora_2026-11-04/plan3/critica_resultados/reloj_reactivo.py` con el reloj de 5 s (la prueba lo
    comprueba tripinfo a tripinfo);
  - `mp`, `mp_det`, `mp_c<C>`, `mp_det_c<C>` (Max-Pressure).

  Toda acción respeta la máscara (hay un `assert`).
- Barrido, una familia por trabajo (`--familia regla|reactiva|mp`; `todas` corre las tres): reglas U ∈ {1, 2, 3, 4, 6}
  × G ∈ {30, 60}; reactiva D ∈ {15, 25, 35, 50, 70} m; MP `mp`, `mp_det`, `mp_c60`, `mp_c90`. Cada familia con
  2001-2003 y sus finalistas como en la tabla de semillas. Escribe, por familia,
  `barridos/<esc>/reglas_<familia>.csv`, `reglas_<familia>_final.csv`, `reglas_<familia>_semillas.csv` y
  `<familia>.json` (`regla.json`, `reactiva.json` o `mp.json`): su campo `"regla"` es el nombre de la ganadora (p. ej.
  `reactiva_d25`), lo que lee `evaluar3 --regla-de`.
- Caché `tmp_fino/<esc>/reglas_<pid>.jsonl`: una corrida guardada vale con la misma huella, la del escenario (como
  `barrer_fino`) más el sha256 de `reglas.py`, `rl_ippo.py` y `rl_corredor.py`.

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

(frágil: cota, si se activa; si no, 0. La reactiva no está en la columna "reglas": son 5 reglas × 3 semillas y sus 3
finalistas × 10, contra 14 × 3 y 6 × 10 de regla + MP. Medido en la cadena de prueba de P1: regla + MP 322 s, las
tres familias 417 s, o sea la reactiva ≈ 0.3 de la columna, lo que le da el generador.)

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

Los brazos de plan3 (franja, bloques, actuado_aj, `brazo_programa` y `brazo_regla`) se niegan en `cruce` y `cruce2`
(`rl_semaforo` no conoce esos modos). Por debajo: `rl_corredor.correr_episodio(modo, ..., adicional=None)` con los
modos `franja`, `bloques` (sin `setProgram`: los cambia su WAUT) y `actuado_aj` (`setProgram("actuado_aj")`); en
`baseline`, `adicional` da el fijo de ese archivo. Sin modos nuevos ni `adicional`, el comando de sumo es el de antes.

Para `veredicto3`: los nombres de la reactiva siguen `reactiva_d<D>` (regex `reactiva_d\d+`); su ganadora queda en
`barridos/<esc>/reactiva.json`, clave `"regla"`; el generador la evalúa con el tipo `ref_reactiva`
(`brazos_ref` de `generar_trabajos3.py`).

---

## 4. Pruebas

Todas corren con `cwd = plan3/` y escriben solo en `plan3/tmp_ref/` (ignorada) y en `plan3/pruebas/ref/salidas/`.
Semillas: de humo (424301-424360) salvo (1) la reproducción del barrido entregado (2001-2003, las suyas), (2) la no
regresión (1001-1002, solo controles entregados) y (3) `prueba_cadena_p1`, que corre en su copia la fina, los
desfases, el barrido de mult5 y los 9 pares de la franja de P1 con 2001-2003 (las del barrido de P1; sus desempates y
finales van con humo, y nada de esa copia se instala ni se usa después). A lo sumo 3 sumo a la vez (2 de 21:00 a
07:30).

| Prueba (tarea) | Qué comprueba | Resultado |
|---|---|---|
| `prueba_fino.py` (0.7) | A. La regla con datos inventados: mínimos locales de la gruesa entregada de malla3 (10/10, 25/15 y 30/10 a ≤ 2 %), umbral de 2 errores estándar, regla de frágiles (dos casos) y el borde del 2 %: `a_2pct` en 9500 casos, los ejemplos de la revisión y la frágil con 20.50 y 20.91 | PASA |
| | B. Reproduce `plan2/barrido_<esc>.csv` con 2001-2003: P1, subrejilla completa por la línea de comandos, y su ganador; P2-P6, 3 filas cada uno; el lector frente a `barrer_fijo.evaluar_config` | PASA (P1 65 de 65 filas y el ganador; P2-P6 3 de 3) |
| | C. Dos corridas (una en 2 trozos y la unión, con otros `--procesos`) dan los mismos archivos | PASA (4 de 4) |
| | D. Puntaje por periodo en P6 10/10, P6 10/25 y P2 10/25: la suma por periodo es el total de `leer_tripinfo`, los no insertados cuadran y su salida programada es la de su flujo | PASA (3 de 3) |
| | E. Huella, en una copia del código: repetir no corre nada; cambiar solo los fines de línea de `comun.py` tampoco; un comentario en `comun.py` cambia la huella y se vuelve a correr todo, con el mismo `gruesa.csv`; los dos interruptores de `comun` la cambian | PASA (4 de 4) |
| | F. Cadena: la fina se niega a leer una gruesa con opciones de prueba; con `--permitir-prueba` la lee y marca su salida; una gruesa con el registro de la regla pero otras semillas también se niega; frágil lee el desempate sin tocarlo (mismo sha256 y fecha) y se niega si `desempate.csv` cambió de orden o le falta una semilla; desde la raíz se niega; `--sem` no se acepta; las semillas del examen y de la final se niegan antes de lanzar sumo (con sumo reemplazado: no se simula ninguna) | PASA (9 de 9) |
| | Total | **33 de 33** |
| `prueba_cadena_p1.py` (0.7-0.11) | La cadena completa en P1 por la línea de comandos sobre la gruesa de la subrejilla de B: sin `--permitir-prueba` la fina se niega; con él, cada paso termina con código 0 (fina, desfases, desempate, frágil, mult5, franja, actuado, reglas con las tres familias, preparar); frágil no reescribe el desempate; las 29 salidas existen y todas quedan marcadas como de prueba; cada ganador jugado por TraCI reproduce su media (fijo fino, verdes de 5 en 5, franja, actuado ajustado, regla, reactiva y MP); `evaluar.py --brazo fijo --programa ... --nombre fino`; `p3_preparar` no toca el actuado ajustado igual al congelado y lo recrea igual si falta; actuado y ciclo mínimo iguales byte a byte a los del `comun.py` entregado | PASA (27 de 27). Los mismos números que antes: fijo fino 22/10 desfase 17 (20.90), franja 20/10-0/25 → 22/10-0/13 (20.59; los dos cambios, estrictos), actuado ajustado con el mismo sha256 (817e3add…); la reactiva gana `reactiva_d25` (22.71) |
| `prueba_franja.py` (0.8) | 1. Franja con plan 2 = plan 1 = el fijo entregado (P1, P3, P6): mismo tripinfo por sumo directo y por TraCI. 2. Cambio en su instante y alineado con el plan 2 solo. 3. 0 cortes de verde (con el cambio de todos a los 1800 s habría 6, 6, 8 y 24). 4. Sumo directo = TraCI. 5. Bloques de 6 programas en P1 y P6. 6. Cuatro pares que antes abortaban (P1 con la relajada en un semáforo, P1 en contrafase con el respaldo, P3 relajada, P6 con 1 relajada y 2 respaldos): cambian en el instante anotado, entran alineados, 0 verdes cortados y 0 ámbares cortos tras un verde. 7. Sin sumo, 3000 pares al azar de P1, P3 y P6: el instante estricto es el de antes en todos los pares donde existía; 13993 cambios estrictos, 1 relajado, 6 de respaldo, 0 forzados; ninguno corta un verde ni deja un ámbar corto | PASA (46 de 46); 1-5 con los mismos números que antes |
| `prueba_actuado.py` (0.9) | 1. La variante por defecto = el actuado entregado (P1-P6). 2. Cada parámetro mueve algún número frente a la variante que solo difiere en él. 3. Sin avisos de SUMO en el log. 4. Sumo directo = TraCI con `<param>`, `delay_based` y las dos coordinadas. 5. `reinstalar`: igual al congelado → no lo toca; cambiado o borrado → lo reescribe con el sha256 congelado; sha256 que el texto de hoy no da → error, el instalado queda igual y sin temporales; `p3_preparar` sin `--piezas` hace solo actuado y trivial | PASA (28 de 28); 1-4 con los mismos números que antes |
| `prueba_reglas.py` (0.10) | 1. U = ∞ da el mismo tripinfo que el ciclo mínimo (P1, P5). 2. Ninguna acción fuera de la máscara. 3. Presión 0 con la red vacía y no 0 con tráfico. 4. `evaluar.py --regla` escribe su CSV; una regla desconocida se rechaza. 5. Reactiva: sus 5 nombres y los inválidos; el barrido `--familia reactiva` (las 5 reglas, 3 finalistas, `reactiva.json` con la ganadora y la marca de prueba); `evaluar.py --regla reactiva_d25`; en P1 (D 25) y P6 (D 50) respeta la máscara y con la máscara libre alarga si y solo si hay un vehículo a ≤ D m en un carril con verde; y da el mismo tripinfo que la lógica del prototipo por el mismo bucle. 6. `evaluar.py`: `adicional` con fijo, actuado o trivial, y los brazos de plan3 en `cruce`/`cruce2`, se rechazan; sin `--semillas` sus brazos no arrancan | PASA (25 de 25) |
| `prueba_atomica.py` (0.11) | 3 evaluaciones simultáneas de actuado y de ciclo mínimo (P1) y de actuado (P6): código 0, CSV iguales, sin temporales y el `.add.xml` del `comun.py` entregado; si el reemplazo falla siempre, `escribir_atomico` (de `comun` y de `barrer_fino`) borra su temporal y el destino queda igual; `leer_cfg` con espacios, y la misma lista que antes en los 40 `.sumocfg` | PASA (5 de 5) |
| `prueba_aleatorias.py` (0.7-0.10) | Por el lanzador: `poi_corredor` y `per_corredor`; barrido fino aleatorio (umbral en errores estándar, 10 finalistas), franja con los 9 pares, perfil con 6 puntajes por bloque y su fijo por bloques jugado por TraCI, actuado con 10 finalistas y MP con sus 4 (las etapas con `--permitir-prueba`: las gruesas son subrejillas) | PASA (19 de 19), con los mismos números (bloques 230.88) |
| `prueba_no_regresion.py` (0.12) | Fijo, actuado, ciclo mínimo e IPPO con mensajes (base 42) en P1-P6 con 1001-1002 por `evaluar.py`: todas las columnas iguales, como texto, a `insumos/puente/eval_<esc>_<brazo>.csv`; `veredicto.py --probar`. La salida empieza con el commit y el sha256 de `comun.py`, `rl_ippo.py`, `evaluar.py` y `rl_corredor.py` | PASA (25 de 25): 23 brazos iguales en las 34 columnas; IPPO en P6 con la diferencia conocida (`cambios_fase` 1650 y 1592 frente a 1654 y 1596), que se informa aparte y fallaría si fuera otra |
| `prueba_nr_p6.py` (0.12) | Por qué difiere IPPO en P6: el código entregado (223f908) corrido hoy da lo mismo que el de esta rama, y con la plantilla de P6 cambiada al 15/10 en ajedrez sale igual al CSV entregado | PASA (2 de 2): no es una regresión |

En total, 210 chequeos. Salidas en `plan3/pruebas/ref/salidas/<prueba>.txt`; `costos_ref.txt` es la estimación de la
sección 2. Las nueve pruebas corrieron enteras dos veces: en 4faffb7 y en d01c2a6 (el código final, con `plan3-dev`
fusionado); las salidas versionadas son las de d01c2a6.

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

## 6. Pendiente o dudoso

1. **`--permitir-prueba` en las protecciones.** La capa 1 de `protecciones.py` rechaza `--avenida`, `--transversal`,
   `--limite`, `--semilla*` y `--llegadas` en los barridos; falta `--permitir-prueba`, que en la cola dejaría seguir
   una cadena con entradas de prueba. Es de `protecciones.py` (no lo toqué): sumarlo a `OPCIONES_PRUEBA`.
2. **Un cambio de código repite la celda entera.** Con la huella nueva, tocar `comun.py`, `barrer_fijo.py`,
   `escenarios_plan2.py` o `barrer_fino.py` (o, en las reglas, `rl_ippo.py`, `rl_corredor.py` o `reglas.py`) invalida
   todo lo guardado de todas las celdas; las etapas siguientes se niegan a leer salidas de la huella vieja, así que la
   cadena hay que relanzarla desde la gruesa. Para B22 en las referencias: si hay que conservar las salidas viejas,
   mover antes `barridos/<esc>/` y `tmp_fino/<esc>/` a una carpeta de archivo (los scripts no tienen opción de carpeta
   ni sufijo, así que un id `_r2` declararía las mismas salidas); si no, relanzar los mismos ids. Conviene no tocar esos
   archivos desde la primera noche de referencias.
3. **El instante estricto puede llegar tarde.** La regla estricta busca en un hiperperíodo: con ciclos que difieren
   en pocos segundos el primer instante limpio puede caer minutos después del corte (en 3000 pares al azar de P1, P3 y
   P6, hasta 708 s; la relajada hasta 49 s y el respaldo hasta 3 s). No lo cambié (cambiaría programas que hoy existen):
   ahora queda anotado (`cambios` en `franja.json` y `bloques.json`). Si se quiere un tope (por ejemplo, preferir la
   relajada si la estricta llega más de un ciclo tarde), es una enmienda de B8.
4. **P6 10/10 no deja vehículos sin entrar a los 6000 s.** La prueba del lector se hizo además con P6 10/25 (541 sin
   entrar) y P2 10/25 (792): mismo total, y la salida programada de cada no insertado es la de su flujo.
5. **Variantes coordinadas del actuado.** Quedaron dos candidatas en el paso 6 (decisión del 05.11): (a) solo
   `earliestEnd` en la avenida, y (b) `earliestEnd` = `latestEnd` en la avenida **y** `latestEnd` en la transversal.
   Con el fijo entregado como "fino" y la semilla 424301 (retraso total, s/veh):

   | | fijo | actuado | coordinada (a) | solo `latestEnd` en la transversal | solo `earliestEnd` = `latestEnd` en la avenida | coordinada (b) |
   |---|---|---|---|---|---|---|
   | P1 | 21.91 | 21.49 | 21.19 | 21.35 | 22.28 | 21.91 |
   | P2 | 392.73 | 437.26 | 446.78 | **834.97** | 501.39 | 394.40 |
   | P3 | 20.14 | 21.46 | 21.61 | — | 24.22 | 20.14 |
   | P6 | 82.57 | 114.64 | 115.94 | 112.19 | 85.30 | 82.57 |

   La (a) se comporta como un actuado libre en P2 y P6; la (b) es casi el fijo. Las dos corren en el paso 6.
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
