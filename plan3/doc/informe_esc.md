# Escenarios nuevos del plan 3: llegadas aleatorias, entrada corregida, P6e, perfil y mezcla

Informe de implementación de las tareas 0.5, 0.6, la parte de rutas de 2.4 y 2.5 de `PLAN3.md` (decisiones A2 y A7;
técnicas B2, B6 y B19). 05.11.2026. Rama `plan3-esc` (worktree `w3_esc`), nacida de `plan3-dev` en 223f908. Todo
corrió con `cwd = plan3/`, semillas de humo (424301-424360; base 7 para entrenar) y como mucho 3 SUMO a la vez.
Nada se escribió en `plan2/` ni en `TESIS/`, ni se tocaron `rl_ippo.py`, `evaluar.py`, `rl_corredor.py`, `comun.py`
o `barrer_fijo.py`.

**Marcas.** [M] medido (archivo de salida); [I] inferido; [S] supuesto; [L] literatura.

## Respuesta corta

1. **Hecho.** `escenarios_plan3.py` (registro, en la raíz), `con_escenarios.py` (lanzador, en la raíz),
   `plan3/demanda_estocastica.py` (transformaciones, demanda esperada y `preparar3`) y los 13 escenarios en `plan3/`.
   **Las siete pruebas obligatorias pasan** [M `plan3/pruebas/esc/salidas/`].
2. **La entrada `best` va en los flows, y no da lo mismo que ponerla en el `.sumocfg`.** En SUMO 1.25 un vehículo que
   hereda `best` de `--default.departlane` (o de `<default.departlane>` en el `.sumocfg`) entra por
   `MSEdge::getProbableLane`, y uno con `departLane="best"` en su flow por `getFreeLane`, el "best" de la
   documentación. Las dos formas ven las mismas llegadas y bajan la espera para entrar de P6 de 45.5 a 0.3 s/veh, pero
   reparten distinto los carriles; con los flows el retraso total del fijo de P6 es 36.40 s/veh y con la opción 37.27
   (sección 5). Las cifras de A2 y del prerregistro (0.30 s/veh; timeLoss 36.91 → 36.82) se midieron con la opción.
3. **Números aleatorios comunes con `best`: se cumplen en los 13 escenarios.** Fijo, actuado, ciclo mínimo, la política
   IPPO entregada (por TraCI) y el fijo por sumo puro ven los mismos vehículos, con la misma salida pedida, el mismo
   `speedFactor` y el mismo tipo, en 424301 y 424302 [M `crn.txt`]. No hace falta el plan B (rutas por semilla).
4. **La mezcla en vehículos equivalentes es ×0.8378** (1.1936 equivalentes por vehículo): el ×0.84 del diseño está
   bien. Corrección menor de A7: con los conteos, los micros son 5.64 % y no 5.7 % (las cinco cuotas de A7 suman 100.1).
5. **P6e:** la espera para entrar del fijo queda en 0.28 y 0.27 s/veh (P6 entregado, mismas semillas: 45.7 y 44.8).
6. **Nadie traba la red** con el fijo instalado ni con el actuado: en los 13 escenarios todos los vehículos entran y
   terminan antes de 6000 s. **Ojo con P2 aleatorio** (`poi_corredor_alta`): la cola para entrar dura hasta ~5460 s y el
   último vehículo llega a los 5724 s con el fijo; con una semilla más cargada podría tocar el tope de 6000 s.
7. **Para otras tareas:** `evaluar3` y `veredicto3` deben juntar los bloques del perfil con `flujo_de`, porque en `per_`
   las métricas del corredor de `comun.leer_tripinfo` salen en 0.0 (no vacías); `plan3/.gitignore` no ignora los
   `<esc>_actuado.add.xml` y `_trivial.add.xml` que se escriben al vuelo; el prerregistro §5 debería decir "en los
   flujos" (sección 8).

---

## 1. Archivos

| Archivo | Qué es | Líneas |
|---|---|---|
| `escenarios_plan3.py` (raíz) | `RECETAS` (cómo se hace cada escenario) y `ESTOCASTICOS` (formato de `escenarios_plan2.DERIVADOS`). Importarlo no toca `escenarios_plan2` | 40 |
| `con_escenarios.py` (raíz) | Lanzador: suma `ESTOCASTICOS` a `DERIVADOS` solo en su proceso y corre el programa con `runpy` | 86 |
| `plan3/demanda_estocastica.py` | Transformaciones de la demanda, demanda esperada y el comando `preparar3` | 319 |
| `plan3/<esc>.rou.xml`, `plan3/<esc>.sumocfg` | Los 13 escenarios, escritos por `preparar3` (versionados) | — |
| `plan3/insumos/entregado/politica_*_vecinos_s*.json` | Metas de las 54 políticas entregadas, copia idéntica de `plan2/` (mismo blob; aviso del coordinador) | — |
| `plan3/pruebas/esc/` | `util_esc.py`, una prueba por tema (`prueba_archivos`, `_conteos`, `_crn`, `_lanzador`, `_cargas`, `_cierre`) y `correr_todas.py`; resúmenes en `salidas/` | — |

`demanda_estocastica.py` tiene 319 líneas y no ~150: 196 de código, 75 de comentarios y docstrings (la fuente de cada
valor de la mezcla y la explicación de la entrada `best`) y 48 en blanco. El código de más frente a la estimación es
el que no estaba en los prototipos: los controles que detienen el generador si una receta no calza, `por_bloque`,
`bloque_de`, `--revisar` y la escritura atómica. Los tres archivos que pueden ir al Anexo B tienen líneas de ≤ 110
caracteres.

## 2. Escenarios

| Escenario | Caso | Red base | Malla y desfases de | Llegadas | Perfil | Mezcla | Arranque | Vehículos esperados por periodo |
|---|---|---|---|---|---|---|---|---|
| `poi_corredor` | P1 | corredor | corredor | Poisson | — | — | — | 905 / 905 |
| `poi_corredor_alta` | P2 | corredor | corredor_alta | Poisson | — | — | — | 1810 / 1810 |
| `poi_red` | P3 | red | red | Poisson | — | — | — | 1075 / 1075 |
| `poi_red_alta` | P4 | red | red_alta | Poisson | — | — | — | 1290 / 1290 |
| `poi_malla3` | P5 | malla3 | malla3 | Poisson | — | — | — | 2175 / 2175 |
| `poi_malla3_alta` | P6 | malla3 | malla3_alta | Poisson | — | — | — | 4350 / 4350 |
| `malla3_alta_e` | P6e | malla3 | malla3_alta | regulares | — | — | — | 4350 / 4350 (exactos) |
| `per_corredor` | P1 | corredor | corredor | Poisson | 10 min | — | — | 905 / 905; por bloque 201, 302, 402, 402, 302, 201 |
| `per_red` | P3 | red | red | Poisson | 10 min | — | — | 1075 / 1075; por bloque 239, 358, 478, 478, 358, 239 |
| `mix_corredor` | P1 | corredor | corredor | Poisson | — | Lima | — | 758.2 / 758.2 (= 905 / 905 equivalentes) |
| `mixa_corredor` | P1 | corredor | corredor | Poisson | — | Lima | 0.5 s | como `mix_corredor` |
| `mix_red` | P3 | red | red | Poisson | — | Lima | — | 900.6 / 900.6 (= 1075 / 1075 equivalentes) |
| `mixa_red` | P3 | red | red | Poisson | — | Lima | 0.5 s | como `mix_red` |

- Todos entran por el mejor carril (`departLane="best"` en cada flow). "Red base" es el primer campo de
  `ESTOCASTICOS` (de ahí salen semáforos, vecinos y lados); "malla y desfases de" es el tercero (lo usa
  `barrer_fijo.como`).
- Los nombres propuestos no chocan con ningún escenario existente; el lanzador lo comprueba en cada corrida. Ojo:
  `malla3_alta_e` empieza con `malla3_alta_` (como `red_alta` con `red_`): todo glob nuevo debe validar el nombre exacto,
  como ya hacen `consolidar.leer_parciales` y `comun.politicas_ippo`. `mix_` no es prefijo de `mixa_`.
- No creé el diccionario `NUEVOS` que menciona 0.5: era para redes nuevas (corredores de 3-5 semáforos, B17) y A6 las
  dejó fuera. Una red nueva necesitaría registrar también `ESCENARIOS_RC`, `VECINOS` y `LADOS`, no solo `DERIVADOS`.

### Qué genera `preparar3` y qué hereda

- **Genera** en `plan3/`, para cada escenario de `RECETAS`: `<esc>.rou.xml` (la demanda de `<caso>.rou.xml` con la
  receta y un comentario que la describe) y `<esc>.sumocfg` (el `<caso>.sumocfg` con `route-files = <esc>.rou.xml` y un
  comentario). Escritura atómica (temporal con el pid y `os.replace`); dos corridas dan los mismos bytes.
- **Hereda sin copiar** la red (`<red>.net.xml`) y el programa fijo del caso (`<caso>.add.xml`): el `.sumocfg` nuevo los
  nombra, así que el brazo `fijo` de un escenario nuevo es el fijo entregado de su caso. `barrer_fijo.py <esc>` usa esa
  plantilla y avisa "no carga `<esc>.add.xml` (el que escribe --instalar)": es esperado, el plan 3 no usa `--instalar`
  (el fijo fino escribe `plan3/<esc>_r10f.add.xml`, con nombre propio).
- **Al vuelo**, fuera de `preparar3`: `<esc>_actuado.add.xml` y `<esc>_trivial.add.xml`, que escriben
  `comun.archivo_actuado` y `archivo_trivial` en el cwd cada vez que corre ese brazo, como en los casos entregados.
- **Receta**, en este orden: `rou_perfil_poisson` si hay perfil, si no `rou_poisson` con llegadas de Poisson;
  `con_mezcla` y `escalar_exp(1 / equivalencia_media())` si hay mezcla; `entrada_best` siempre.

## 3. Uso exacto (para el generador de trabajos)

Todo con `cwd = plan3/`. La capa 1 de `protecciones.py` debe desenvolver `../con_escenarios.py` y aplicar las reglas al
programa interno (`../rl_ippo.py`, `../evaluar.py`, `../barrer_fijo.py`, `evaluar3.py`, `barrer_fino.py`).

```
# chequeo de cada tarde: los 26 archivos al dia (sale con 0); preparar3 sin --revisar solo si cambia una receta
python demanda_estocastica.py preparar3 --revisar

# 2.1 V2 con llegadas aleatorias: con mensajes, bases 42, 2042, 4042, 14042 y 16042; sin mensajes
#     (--variante local), bases 42, 2042 y 4042, con la misma etiqueta
python ../con_escenarios.py ../rl_ippo.py train --escenario poi_<caso> --variante vecinos --seed <b> \
    --episodios 200 --eval-cada 10 --v2 --criterio-val total --guardar-estado --etiqueta p3v2poi \
    --val-seeds 999,1999,2999,3999,4999,7999,8999,9999,15001,15002,15003,15004,15005,15006,15007,15008
# 1.3 P6e (V2 con llegadas regulares, 5 bases): lo mismo con --escenario malla3_alta_e --etiqueta p3v2reg
# 2.4 perfil (3 bases): --escenario per_corredor | per_red --etiqueta p3v2per
# 2.5 mezcla (3 bases): --escenario mix_corredor | mix_red --etiqueta p3v2mix

# evaluaciones (evaluar3.py corre igual por el lanzador)
python ../con_escenarios.py ../evaluar.py --escenario <esc> --brazo fijo|actuado|trivial --semillas <s> --salida <csv>
python ../con_escenarios.py ../evaluar.py --escenario <esc> --politica <politica.pt> --semillas <s> --salida <csv>
# arranque lento (2.5): la politica entrenada en mix_<caso> se juega en mixa_<caso> (evaluar avisa que se entreno en
# otro escenario; es lo buscado)
python ../con_escenarios.py evaluar3.py --escenario mixa_<caso> --politica politica_mix_<caso>_vecinos_p3v2mix_s<b>.pt ...

# barridos del fijo (barrer_fino.py es de la tarea 0.7; barrer_fijo.py nunca con --instalar)
python ../con_escenarios.py barrer_fino.py <esc> ...
python ../con_escenarios.py ../barrer_fijo.py <esc> --semillas <s> --tmp tmp_barrido_<esc> --procesos 1
```

- `--guardar-estado` lo agrega la tarea 1.1; el `rl_ippo.py` de esta rama todavía no la tiene.
- Las salidas llevan el nombre del escenario: `politica_<esc>_<variante>_<etiqueta>_s<b>.pt|.json`,
  `resultados_<esc>_ippo_<variante>_<etiqueta>_s<b>.csv`, `checkpoints/<esc>_ippo_..._epNNN.*`, `barrido_<esc>.csv`.
- Sin el lanzador, `evaluar.py --escenario poi_corredor` falla visible (`invalid choice`), no en silencio.
- Un programa de `plan3/` corre con `plan3/` al frente de `sys.path` (importa `demanda_estocastica`) y la raíz detrás
  (importa `evaluar`, `comun`). `sys.argv[0]` queda como la ruta absoluta del programa (lo pone `runpy`).
- El lanzador se niega a correr un programa de `plan2/` o `TESIS/` (de este repositorio, de un worktree hermano o de una
  copia dentro de ellos) o con el cwd ahí. No mira lo que está por encima de `demo_rl_semaforo/` (allí una carpeta
  puede llamarse "Tesis").
- Desde otro programa (pruebas): `import con_escenarios; con_escenarios.registrar()`, antes de importar `rl_corredor`,
  `rl_ippo`, `evaluar`, `barrer_fijo`, `rl_dqn` o `rl_mappo`.
- Límite: un programa que lance hijos de Python con `multiprocessing` no les pasa el registro. Ninguno de los del
  plan 3 lo hace (`calibrar_demanda.py` sí, pero no está en la lista de scripts del prerregistro).

## 4. Funciones de `demanda_estocastica.py`

| Función | Qué hace |
|---|---|
| `rou_poisson(texto)` | `vehsPerHour="q"` → `period="exp(q/3600)"` (12 cifras) en cada flow; begin y end no cambian, así que cada periodo espera lo mismo y la punta se invierte a los 1800 s. Se detiene si un flow no tiene `vehsPerHour` |
| `escalar_exp(texto, f)` | Multiplica por `f` cada tasa `exp(r)`. No toca `vehsPerHour` (para eso está `barrido_demanda.rou_escalado`) |
| `entrada_best(texto)` | `departLane="best"` en cada flow; se detiene si la demanda ya trae `departLane` |
| `rou_perfil_poisson(texto, perfil=PERFIL, bloque=600)` | Cada flow en bloques de 600 s con `period="exp(q·f_k/3600)"` e id `<flow>_b<k>`, ordenados por inicio. `PERFIL` = (2/3, 1, 4/3, 4/3, 1, 2/3) = `barrido_demanda.PERFIL / 1.5` |
| `con_mezcla(texto, arranque=0)` | Cambia el `<vType id="auto">` por una `<vTypeDistribution id="auto">` con los tipos `lima_auto`, `lima_moto`, `lima_combi`, `lima_micro` y `lima_bus`; los flows no cambian. Con `arranque` agrega `startupDelay` a los cinco |
| `flujo_de(id)` | Flow de origen sin el sufijo del bloque: `p1_W_E_b2.17` → `p1_W_E` (vale para vehículos y flows) |
| `bloque_de(id)` | Bloque `k` del perfil, o `None` |
| `demanda_flow(flow)` | Vehículos esperados de un `<flow>`: `vehsPerHour`/`perHour`, `period="exp(r)"` (r·dur), `period=T`, `probability`, `number` |
| `demanda_esperada(rutas)` | Total esperado. Mismo contrato que `veredicto.demanda` (lista de `.rou.xml`): `veredicto3` puede usarla en su lugar (`vd.demanda = demanda_estocastica.demanda_esperada` si importa `veredicto`). Da 1810, 8700 y 2580 en P1, P6 y P4, con llegadas regulares y con Poisson |
| `por_flow(rutas)`, `por_bloque(rutas, 600)`, `por_periodo(rutas)` | Esperados por flow, por bloque (un flow que cruza un borde se reparte en proporción al tiempo) y por periodo de 30 min (`{1: ..., 2: ...}`) |
| `composicion()`, `equivalencia_media()` | Cuotas de la mezcla y equivalentes por vehículo (sección 6) |
| `preparar3(carpeta, revisar)` | Escribe o compara los 26 archivos y devuelve los que no estaban al día |

Uso por consola: `python demanda_estocastica.py demanda <archivo.rou.xml> ...` imprime total, periodos y bloques.

## 5. Entrada por el mejor carril: en los flows

**Decisión:** `departLane="best"` en cada flow del `.rou.xml` (función `entrada_best`), no `<default.departlane>` en el
`.sumocfg`.

**Por qué.**
1. **Es la entrada que nombran A2 y el plan** (`departLane="best"`), con el significado de la documentación de SUMO.
2. **Las dos formas no son iguales en SUMO 1.25**: la diferencia está medida (punto 3) [M] y el mecanismo sale de leer
   el código [I, `src/microsim/MSEdge.cpp` en el tag v1_25_0,
   https://github.com/eclipse-sumo/sumo/blob/v1_25_0/src/microsim/MSEdge.cpp]. `MSEdge::getDepartLane` resuelve el
   valor por defecto (`dld = myDefaultDepartLaneDefinition`), pero dentro del caso `BEST_FREE`/`BEST_PROB` elige entre
   `getFreeLane` y `getProbableLane` con `veh.getParameter().departLaneProcedure == DepartLaneDefinition::BEST_FREE`, es
   decir, mirando el valor propio del vehículo, que con la opción es `DEFAULT`. Con la opción el vehículo entra por
   `getProbableLane` (el carril con más hueco, como `best_prob`); con el atributo, por `getFreeLane`. También
   `MSEdge::insertVehicle` con `checkOnly` trata distinto a los dos.
3. **Medido en P6 regular, fijo instalado, semillas 424301-424303, sumo puro** [M `archivos.txt`, parte e]:

   | Entrada | Espera para entrar (s/veh) | timeLoss (s/veh) | Retraso total | Entra por el carril 0 |
   |---|---|---|---|---|
   | Por defecto (primer carril) | 45.45 | 36.51 | 81.96 | 100 % |
   | `--default.departlane best` (opción o `.sumocfg`) | 0.30 | 36.97 | 37.27 | 53.6 % |
   | `departLane="best"` en los flows (lo elegido) | 0.28 | 36.12 | 36.40 | 40.1 % |

   Las dos formas de `best` ven los mismos vehículos con la misma salida pedida y el mismo `speedFactor`; cambia el
   carril de entrada y con él el tráfico. Con las dos, fijo y actuado ven las mismas llegadas.
4. **Va con la demanda**: viaja con el `.rou.xml`, se ve al leerlo y no depende de cómo se lance sumo (todos los
   programas usan `-c <esc>.sumocfg`, pero un programa nuevo que armara su línea de comandos sin el `.sumocfg` la
   perdería).

**Qué cambia frente a lo escrito.** El prerregistro (borrador, §5) dice "`departLane="best"` en los flujos o en el
`.sumocfg`": no son equivalentes y debería decir "en los flujos". Las cifras descriptivas de A2 y del prerregistro (0.30
s/veh; timeLoss 36.91 → 36.82) son de la opción; con los flows, en semillas de humo: 0.28 s/veh y timeLoss 36.51 →
36.12. Ninguna conclusión de A2 cambia. Si se prefiriera la opción (para repetir exacto lo medido por el área de
referencias), basta cambiar `entrada_best` por la opción en el `.sumocfg` y correr `preparar3`.

## 6. Mezcla de Lima (valores para la parte B del prerregistro)

| Clase | Cuota | De dónde sale la cuota | Equivalentes (INVERMET) | Clase de SUMO | Largo (m) | Acel. (m/s²) | Decel. (m/s²) |
|---|---|---|---|---|---|---|---|
| Auto y taxi | 78.928 % | 541 088 de 685 544 veh/día [L] | 1.00 [L] | passenger (el vType entregado) | 5 | 2.6 | 4.5 |
| Moto | 4.364 % | 29 919 de 685 544 [L] | 1.0 [S] (sin factor) | motorcycle | 2.2 [M] | 6 [M] | 10 [M] |
| Combi | 4.808 % | transporte público 114 537 × 6 420 / 22 310 [L; I] | 1.25 [L] | bus | 6 [S] | 2.0 [S] | 4.5 [S] |
| Micro | 5.641 % | 114 537 × 7 533 / 22 310 [L; I] | 2.00 [L] | bus | 8 [S] | 1.5 [S] | 4.0 [S] |
| Bus | 6.258 % | 114 537 × 8 357 / 22 310 [L; I] | 3.00 [L] | bus | 12 [M] | 1.2 [M] | 4.0 [M] |

- **Composición** [L]: línea cortina del río Rímac, JICA y Nippon Koei (2013), *Encuesta de recolección de información
  básica del transporte urbano en el área metropolitana de Lima y Callao*, Tabla 2.16 (15 puentes, 24 h,
  8-9.05.2012), https://openjicareport.jica.go.jp/pdf/12087532_01.pdf. Sumé las 15 filas: la fila "Total" publicada
  omite el puente Huachipa en cada tipo (motos 27 574 publicado frente a 29 919 sumado, etc.; el total general de
  785 614 sí lo incluye). Sin camiones (100 070 veh/día, que vienen sobre todo de vías de carga): 685 544 veh/día.
- **Reparto del transporte público** [L; I]: flota regular de la ATU en 2021 (Lima Cómo Vamos, *Reporte urbano de
  indicadores de calidad de vida 2021*, p. 16, suma de su tabla por antigüedad: combis 6 420, micros 7 533, buses
  8 357, total 22 310), https://www.limacomovamos.org/wp-content/uploads/2022/11/ReporteIndicadoresLCV2021.pdf. Es
  flota, no tránsito.
- **Equivalentes** [L]: factores del INVERMET citados en el estudio de impacto vial del predio Oquendo (UNFV, Tabla
  N.° 2: auto 1.00, camioneta rural 1.25, microbús 2.00, ómnibus 3.00),
  https://web.unfv.edu.pe/facultades/fopca/images/2022/Proyecto_de_Facultad_en_Oquendo/3.Estudio_de_Impacto_Vial.pdf.
  La moto no tiene factor: 1.0 [S].
- **Cuenta**: 0.78928·1 + 0.04364·1 + 0.04808·1.25 + 0.05641·2 + 0.06258·3 = **1.1936 equivalentes por vehículo**, así que
  la demanda se multiplica por **1/1.1936 = 0.8378** (con la moto en 0.5: 0.8534). P1 pasa de 1810 a 1516.4 veh/h y P3
  de 2150 a 1801.3, con los mismos equivalentes que el caso. El ×0.84 del diseño está bien.
- **Parámetros de SUMO por clase** [M `archivos.txt`, parte g, leídos con TraCI en SUMO 1.25]: passenger 5 m, 2.6, 4.5;
  motorcycle 2.2 m, 6, 10; bus 12 m, 1.2, 4. Todos los tipos guardan del vType entregado sigma 0.5, minGap 2.5 y
  maxSpeed 13.89 (50 km/h). Lo demás lo pone la clase: desvío de la velocidad deseada 0.1 (passenger y motorcycle) y
  0.0 (bus: combis, micros y buses no varían su velocidad deseada), deceleración de emergencia 9, 10 y 7, y la clase de
  emisión HBEFA4 de cada una. Combi y micro no tienen clase en SUMO: clase bus con largo, aceleración y deceleración
  supuestos [S] (los mismos del prototipo de factibilidad que midió A7).
- **Arranque lento** (`mixa_`): `startupDelay` 0.5 s en los cinco tipos [S], solo para evaluar (A7). Con la misma
  semilla, `mixa_` tiene los mismos vehículos y los mismos tipos que `mix_` [M `crn.txt`].
- **Corrección a A7**: la tabla de A7 dice micros 5.7 %; con los conteos es 5.64 % (las cinco cuotas de A7 suman
  100.1 %). Las demás coinciden al redondear.

## 7. Pruebas

Todas en `plan3/pruebas/esc/` (resúmenes en `salidas/`, lo pesado en `plan3/tmp_esc/`, ignorada).
`python pruebas/esc/correr_todas.py` las corre en orden (~40 min).

| # | Prueba | Resultado | Salida |
|---|---|---|---|
| 1 | Cada periodo suma lo del caso; SUMO carga los 13 | **Pasa.** Diferencia máxima 2.3e-9 vehículos por periodo y 1.1e-9 por flow (en `mix_`, después de multiplicar por 1.1936 equivalentes por vehículo); en `per_` cada flow del caso conserva su total al juntar sus bloques. Los 13 cargan sin errores ni avisos (300 s, avisos visibles). `preparar3` es determinista (26 de 26 iguales en una copia) | `archivos.txt` (a-d, g) |
| 2 | Generados en 20 semillas de humo dentro de ±3 ee; bloques del perfil; composición dentro de ±2 ee | **Pasa.** Totales con z de −0.58 a +0.65, periodos \|z\| ≤ 1.25, bloques de `per_` \|z\| ≤ 1.64; dispersión de Poisson (sd/√esperado 0.76-1.32). Cuotas de la mezcla \|z\| ≤ 1.46; chi cuadrado p = 0.33 (P1) y 0.40 (P3). Todo vehículo de `per_` pide salir dentro de su bloque. P6e genera 8700 exactos | `conteos.txt`, `conteos.csv` |
| 3 | Números comunes con `best`: fijo, actuado, ciclo mínimo, IPPO entregado (TraCI) y fijo por sumo puro | **Pasa** en los 13 escenarios × 2 semillas: 0 diferencias en ids, salida pedida, `speedFactor`, tipo y orden. El fijo por sumo puro (opciones de `barrer_fijo`) da el mismo tripinfo que por TraCI, con emisiones. `mixa_` = `mix_` | `crn.txt`, `crn.csv` |
| 4 | Dos semillas, llegadas distintas; sha256 de los `.rou.xml` de `plan2/` | **Pasa.** En todos los aleatorios el 100 % de los ids comunes cambia de salida pedida; en P6e (regulares) mismas salidas y otros conductores (8503 de 8700 `speedFactor` distintos), como debe ser. Los 28 `.rou.xml` de `plan2/` con el mismo sha256 | `crn.txt` (4), `cierre.txt` |
| 5 | P6e: espera para entrar del fijo < 1 s/veh | **Pasa.** 0.28 y 0.27 s/veh (P6 entregado: 45.66 y 44.80) | `cargas.txt` (5) |
| 6 | Lanzador con `evaluar.py`, `rl_ippo.py train`, `barrer_fijo.py`; generador de plan2 en copia; rechazos | **Pasa** (detalle abajo) | `lanzador.txt`, `salidas/lanzador/` |
| 7 | Nadie traba la red (fijo y actuado, 2 semillas) | **Pasa.** 0 no insertados y 0 sin terminar en los 13; `time-to-teleport -1` en los 13 `.sumocfg` (sin teletransportes). Retrasos abajo | `cargas.txt`, `cargas.csv`, `salidas/cargas/` |
| — | Cierre | `git status --porcelain --ignored -- plan2 TESIS` y `git diff 223f908 -- plan2 TESIS` vacíos; `preparar3 --revisar` al día; sin restos en `plan3/` | `cierre.txt` |

**Prueba 6, detalle** [M `lanzador.txt`]:
- Por el lanzador, con `poi_corredor`: `evaluar.py --brazo fijo` y `--brazo trivial` (424303-424304, salida en
  `tmp_esc/`); `rl_ippo.py train` (2 episodios, base 7, semillas 8 y 9, `--v2 --criterio-val total`, validación con
  424359 y 424360 en el episodio 2, `--etiqueta p3humo`; meta con el escenario, la etiqueta y las semillas); `evaluar.py`
  juega esa política (brazo `ippo_vecinos_p3humo_s7`); `barrer_fijo.py --limite 3 --tmp tmp_esc_barrido` (3
  configuraciones, sin `--instalar`). El barrido en 10/10 con desfases 0 da 105.41 s/veh y el ciclo mínimo por
  `evaluar.py` también 105.41: sumo puro y TraCI ven las mismas llegadas.
- Sin el lanzador `evaluar.py` rechaza `poi_corredor` (`invalid choice`). Un programa de `plan3/` corre con sus
  argumentos, importa `demanda_estocastica` y ve los escenarios nuevos y los de plan2.
- `plan2/generar_trabajos.py` sobre una copia de `plan2/` (en `tmp_esc/copia_gen`, con `escenarios_plan3.py` y
  `con_escenarios.py` al lado): 868 trabajos y `cola/trabajos.jsonl` con el sha256 de `plan2/` (4eb09e8f…, el
  `4EB09E8F...` del plan); igual si el proceso importa antes `escenarios_plan3`. Medido en la copia: si alguien
  registrara los escenarios en ese proceso, la cola de plan2 pasaría a 946 trabajos (+78, seis por escenario), que es
  lo que el registro aparte evita (B2).
- El lanzador se niega (código 1, mensaje `con_escenarios: ...`): con `rl_corredor` o `evaluar` ya importados; con un
  nombre que ya está en `DERIVADOS`, que es de un escenario fijo (`corredor_alta`) o de un nivel (`dem_red_t905`); al
  registrar dos veces; con el programa en `plan2/` o `TESIS/`, o con el cwd en `plan2/`. El mismo programa con
  `cwd = plan3/` corre (control).

**Prueba 7, retraso total por vehículo** (media de 424301 y 424302; en paréntesis, la espera para entrar). Es
descriptivo: semillas de humo y referencias sin re-ajustar; nada de esto decide algo [M `cargas.txt`].

| Escenario | Fijo instalado | Actuado | Última llegada en 424301 (fijo / actuado) |
|---|---|---|---|
| `poi_corredor` | 27.18 (1.30) | 24.38 (1.29) | 3710 / 3703 s |
| `poi_corredor_alta` | 487.12 (311.65) | 438.43 (302.03) | **5724 / 5585 s** |
| `poi_red` | 23.03 (1.60) | 24.87 (1.59) | 3768 / 3777 s |
| `poi_red_alta` | 32.91 (2.02) | 33.16 (2.02) | 3769 / 3770 s |
| `poi_malla3` | 22.76 (0.61) | 26.29 (0.61) | 3775 / 3770 s |
| `poi_malla3_alta` | 47.27 (0.94) | 56.18 (0.96) | 3870 / 3852 s |
| `malla3_alta_e` | 36.42 (0.28) | 55.70 (0.28) | 3785 / 3970 s |
| `per_corredor` | 47.93 (1.73) | 28.73 (1.71) | 3720 / 3707 s |
| `per_red` | 25.71 (1.47) | 27.11 (1.48) | 3754 / 3750 s |
| `mix_corredor` | 27.98 (1.19) | 23.91 (1.18) | 3706 / 3714 s |
| `mixa_corredor` | 29.23 (1.19) | 25.33 (1.18) | 3707 / 3721 s |
| `mix_red` | 22.32 (1.13) | 23.78 (1.14) | 3760 / 3765 s |
| `mixa_red` | 22.51 (1.14) | 24.02 (1.14) | 3759 / 3763 s |
| P6 entregado (`malla3_alta`, entrada por defecto) | 81.87 (45.23) | — | 3929 s |

- En `per_corredor` el fijo pierde en la punta (bloque 3, 30-40 min: 71.9 s/veh frente a 39.0 del actuado, semilla
  424301) pero no se traba.
- La espera para entrar de 0.6-2.0 s/veh en los aleatorios (0.28 en P6e) incluye los +0.5 s/veh del redondeo de
  `exp()` al segundo (B6), igual en todos los brazos.
- `poi_corredor_alta` (P2 aleatorio) tiene una cola real en sus accesos de un carril (312 s/veh de espera para entrar
  con el fijo; ~230 con llegadas regulares): el último vehículo entra a los ~5460 s y llega a los 5724 s.

## 8. Pendiente o dudoso

1. **Prerregistro §5 (entrada):** cambiar "en los flujos o en el `.sumocfg`" por "en los flujos" y, si se citan, poner
   al lado las cifras con los flows (sección 5). La parte A todavía no está subida.
2. **Perfil y métricas del corredor:** en `per_` los ids llevan `_b<k>` y `comun.leer_tripinfo` no los reconoce como
   flows del corredor: `viaje_corredor_prom`, `retraso_corredor_prom`, `retraso_corredor_punta`, `paradas_corredor` y
   `paradas_corredor_le1` salen en **0.0** (no vacías) en `evaluar.py` y en el CSV de `rl_ippo` [M `cargas.txt`,
   líneas "(informativo)", y `salidas/cargas/eval_per_corredor_fijo.csv`]. `evaluar3`/`veredicto3` deben ignorarlas o
   recalcularlas con `flujo_de` (B19 lo preveía en "el lector de plan3").
3. **P2 aleatorio cerca del tope:** con una semilla de examen más cargada que las de humo, la cola de `poi_corredor_alta`
   puede no vaciarse antes de 6000 s; entonces hay no insertados y el retraso total de esa semilla es una cota inferior
   (`comun.leer_tripinfo` cuenta su espera hasta el cierre). Conviene que `evaluar3` informe los no insertados por
   semilla (ya está en 0.14).
4. **`plan3/.gitignore`** no ignora `<esc>_actuado.add.xml` ni `<esc>_trivial.add.xml`, que `comun` escribe en el cwd
   en cada corrida de esos brazos; las pruebas los borran al terminar. No toqué `.gitignore` (lo editan otras tareas):
   agregar los dos patrones o dejar que el trabajo "preparar" (0.11) los genere y se versionen como en `plan2/`.
5. **Mezcla:** combis y micros como clase bus heredan desvío de velocidad 0.0 y la clase de emisión de un bus urbano
   de más de 15 t (sobrestima su CO2; el CO2 es secundario); `comun.plazas_carril` supone 7.5 m por vehículo (riesgo ya
   declarado en 2.5); el factor de la moto (1.0) es un supuesto.
6. **Insumos:** `plan3/insumos/entregado/` traía solo los `.pt`. El coordinador lo corrigió en `plan3-dev`; aquí
   commiteé los 54 `.json` idénticos a `plan2/` (mismo blob, la fusión no choca). `p3_insumos.py` no se tocó.
7. **`--guardar-estado`**: las líneas de entrenamiento de la sección 3 la llevan; la agrega la tarea 1.1.
8. **Avisos esperados:** `barrer_fijo.py` dirá en cada escenario nuevo que el `.sumocfg` no carga `<esc>.add.xml`, y
   `evaluar.py` que una política se entrenó en otro escenario cuando se juega entregada o en `mixa_`.

## 9. Commits

En `plan3-esc`, a nombre de Fabian y sin coautor: a22974c (metas `.json` de insumos), 9c9a6c9 (registro, lanzador,
generador, escenarios y prueba de archivos), fea637a (las demás pruebas, sus salidas y el formato a ≤ 110
caracteres) y el último (este informe, y la prueba 7 con la copia de sus CSV en `salidas/cargas/`). No toqué archivos
de otras tareas; `plan3/insumos/entregado/*.json` es idéntico a lo que agregó el coordinador en `plan3-dev`.


## Nota de la integración (05.11.2026)

Las etiquetas del perfil y de la mezcla quedaron `p3v2per` y `p3v2mix` (las que usa `generar_trabajos3.py`); en el
manifiesto de evaluaciones sus tipos son `v2per` y `v2mix`. Las evaluaciones van con `evaluar3.py`. La revisión
del 05.11 corrigió además: las cifras de la entrada `best` (ver prerregistro §5), el cierre a los 6000 s en P2 (el
ciclo mínimo siempre llega; prerregistro §4) y las métricas del corredor en `per_` (`comun.QUITAR_BLOQUE`, que
activa `con_escenarios.registrar`).
