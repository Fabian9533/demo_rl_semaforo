# veredicto3.py: informe de implementación (PLAN3 5.0; DECISIONES B11, B21 y B22)

05.11.2026, con la revisión de la tarde, el ajuste de la noche al generador nuevo y el seguimiento de la revisión de
referencias. Rama `plan3-ver` (nació de `plan3-dev` en cff0d61 y trae `plan3-dev` fusionada hasta 1bcb4c9). No se
simuló nada y no se abrió ningún resultado decisivo (todavía no existen): todo se probó con lo entregado de `plan2/`
(solo lectura) y con datos sintéticos que usan las semillas de humo (424301-424360) en `plan3/tmp_ver/` (ignorada por
git).

## Respuesta corta

- **Qué hay.** `plan3/veredicto3.py` (~2500 líneas de código y ~1150 de pruebas, con el mundo sintético). Calcula, con
  las reglas del prerregistro (parte A), las etiquetas de cada celda (T1, T2 y citable), el modelo citado, el sentido
  entre entrenamientos, todas las hipótesis de §8 con sus familias y Holm, el número único, las lecturas obligadas y el
  informe de vehículos sin entrar al cierre (§4).
- **Modos.** `--probar` (160 pruebas, ~55 s), `--final` (se niega si algo sellado cambió, si un CSV de `ciego/` no es
  el de su primera mañana, si falta un trabajo, un meta o una base sin declararla caída) y `--prueba-final LISTA.json`
  (§13: valida todo, luego crea el candado en exclusiva y corre una sola vez).
- **Pruebas: 160 de 160 pasan** en `plan3-dev` fusionada (`plan3/pruebas/ver/prueba_veredicto3.txt`; el registro sale
  igual byte a byte en dos corridas).
- **Ajuste de la noche (05.11).** El mundo sintético ahora es el manifiesto del generador tal cual: no agrega lo que el
  generador ya produce (eso daba los duplicados), y se sella con `manifiesto.sello` real. veredicto3 lee las bases
  caídas por su corrida, como el generador, y coteja el brazo de las referencias nuevas.
- **Seguimiento (05.11).** `manifiesto.py` ya hace los tres cambios propuestos (d2501e5) y `comprobar_cierre` no
  necesitó más. Se agregaron la regla reactiva (al lado, con la lectura de la regla simple, y en H0), los nombres
  `mixa1` y `mixa3`, las caídas declaradas sin corrida y la corrección de los cambios de fase de los brazos que corren
  por rl_ippo (se les resta k, los semáforos que su plantilla arranca fuera del primer verde).

## Ajuste al generador nuevo y al sello real (05.11, noche)

| # | Qué cambió | Qué se hizo | Prueba |
|---|---|---|---|
| 1 | El generador produce referencias (`ref_fino` con clave `fino`, `ref_fino5`, `ref_fijo10`, `ref_franja`, `ref_bloques`, `ref_actuadoaj`, `ref_regla`, `ref_mp`), `v2reg3poi`, a3, perfil, mezcla y arranque lento | El mundo usa `gt.generar_con_manifiesto(gt.PARTES_PLAN)` sin tocar rutas ni claves. Solo agrega lo que falta, comparando por (celda, escenario, tanda, tipo, base) y con `gt.evaluacion` (hoy solo la política por red del corredor, que la Etapa 4 aún no genera); una segunda vez no agrega nada | M00 |
| 2 | Lo que el mundo quita | Solo el fijo fino de r905 y el actuado ajustado de r1358, para probar PENDIENTE por una referencia que falta | M06 |
| 3 | Sello real | `sellar_mundo` = `manifiesto.sello(esperado, raiz)` + `manifiesto.revisar_historia` (para `manifiesto_ciego_commit`), como `manifiesto.py cierre`. El mundo vive en `tmp_ver/mundo/plan3` con su repositorio git en `tmp_ver/mundo` (como `plan3/` en el worktree) y crea un `.pt` por cada política | M00b, M04b-M04g |
| 4 | `comprobar_cierre` frente a `manifiesto.sello` | Los CSV de uso 'final' que estén sellados no se exigen ni se rechazan; los "otros" que se exigen son `manifiesto.OTROS` que existen y `promocion/*.json` (así siguen a `manifiesto.py`); un CSV sin sellar que no existe porque su base cayó (declarada) no es problema | M32b, M04d, M04q, M04r |
| 5 | `manifiesto_ciego_commit` del sello | `comprobar_ciego` exige que ese commit esté en la historia de git | M35b |
| 6 | Bases caídas por corrida | `cola/caidas.json` es el mismo archivo que lee `generar_trabajos3.leer_caidas` (`corrida`, celda, escenario, tipo, base, intentos, fecha). veredicto3 da por caída una base por su (celda, escenario, tipo, base) o por la corrida de su política y las que salen de ella (`gt.DERIVA`): una V2 caída se lleva sus 400 episodios y sus dos derivadas, y la V2 de la mezcla cae también en el arranque lento. Da exactamente las mismas bases que el generador deja de evaluar. La fecha va en cada intento o una vez por declaración; una corrida que no es de su base es ERROR | M36, M04i, M04j-M04j3, M27 |
| 7 | Brazo de las referencias | `brazo_de_trabajo` sigue a `evaluar3.armar_brazo`: `--brazo fijo --programa P --nombre X` → `fijo_X`; `--brazo X` → X (franja, bloques, actuado_aj...); `--regla-de .../regla.json`, `reactiva.json` o `mp.json` → la forma del nombre (`regla_u<U>g<G>`; `reactiva<...>`; `mp`, `mp_det`, `mp_c<C>`), porque el nombre exacto está en un archivo que no se sella | M04k, M04m, M04o, M04p |
| 8 | Sin `ref_mpc` | Max-Pressure es una sola referencia (`ref_mp`, la mejor de la familia con y sin ciclo máximo); H0 ya no la lista dos veces. `ref_fijo10` se llama "fijo ajustado desde 10 s" y va al lado | M28 |
| 9 | Celdas de perfil, mezcla y arranque lento | veredicto3 las toma de `gt.PERFIL`, `gt.MEZCLA` y `gt.MEZCLA_A` (hoy `per1`, `per3`, `mix1`, `mix3`, `mixa1` y `mixa3`) y las distingue por (celda, escenario); en el `.md` agrega el escenario si un nombre se repite | M06b, M28e |
| 10 | H10 con datos | El resumen dice además en cuántos niveles no se pudo correr | M22, M22b |

## Seguimiento de la revisión de referencias y de `manifiesto.py` (05.11, noche)

| # | Qué cambió | Qué se hizo | Prueba |
|---|---|---|---|
| 1 | `manifiesto.py` (d2501e5): `revisar` y `sello` saltan las tandas de uso 'final', `revisar` avisa de una base caída declarada después, y `OTROS` trae `insumos/manifiesto.json` | `comprobar_cierre` ya casaba: lee la lista de `manifiesto.OTROS`, así que ahora exige sellado `insumos/manifiesto.json`, y sigue aceptando un sello con o sin los CSV de la prueba final | M00b, M32b |
| 2 | Regla reactiva al lado (`ref_reactiva`, clave `reactiva`; §5) | Se coteja la forma de su nombre; lleva la misma lectura obligada que la regla simple (§11): "No le gana a la regla simple", "a la regla reactiva" o "a la regla simple ni a la regla reactiva"; H0 la cuenta entre los controles que reaccionan | M28j |
| 3 | Celdas `mixa1` y `mixa3` | Salen de `gt.MEZCLA_A`; nada que cambiar en las reglas | M06b, M28e |
| 4 | `cola/caidas.json` sin `corrida` | Se arma como el generador (`gt.corrida_de_tipo` con el escenario, el tipo y la base) y vale igual para lo que sale de ella | M36b |
| 5 | Cambios de fase (hallazgo 10) | A los brazos que corren por rl_ippo se les resta k por semilla antes de compararlos (ver abajo) | N18, M37 |

**Cambios de fase: qué se corrige y por qué.** rl_ippo pone cada semáforo en su primera fase verde al empezar, pero su
contador de cambios de fase compara con la fase en que arrancó la plantilla (la lee antes de ponerlo en verde): por cada
semáforo que la plantilla arranca fuera de su primer verde, suma un cambio que no ocurrió. rl_corredor lee la fase
después y no lo suma. Corren por rl_ippo las políticas (V2 y sus variantes, C0, IPPO entregado, la política por red) y
las reglas (simple, reactiva y Max-Pressure); por rl_corredor, el fijo, el fijo fino, el de verdes de 5 en 5, el ajustado
desde 10 s, la franja, los bloques, el actuado, el actuado ajustado y el ciclo mínimo. veredicto3 resta k a cada semilla
de los brazos de rl_ippo al leer `cambios_fase`, de modo que todo brazo cuenta los cambios que de verdad hubo; la fila de
`veredicto3_comparaciones.csv` lo dice. k sale de la plantilla versionada del escenario (`plan3/<esc>.sumocfg`, su red
y sus `.add.xml`): la fase en que está cada semáforo a t = 0 ((−offset) mod ciclo) frente a su primer verde, como
`k_plantillas.py` de la revisión. Solo cambia una métrica secundaria; la principal no se toca.

| Plantilla | k |
|---|---|
| corredor, corredor_alta, dem_corredor_t905, dem_corredor_t2715_der (y poi_, per_, mix_ y mixa_ del corredor) | 1 |
| dem_red_t905, dem_red_t1358, dem_red_t1810 | 1 |
| dem_corredor_t1358, dem_corredor_t2715, red, red_alta, dem_red_t2715, dem_red_t3620 (y poi_, per_, mix_ y mixa_ de la red) | 0 |
| malla3, malla3_alta, malla3_alta_e, dem_malla3_* (y poi_ de la malla) | 0 |

`pruebas/ref/prueba_nr_p6.py` muestra este mismo efecto: el CSV entregado de IPPO en P6 (el del puente) se corrió con la
plantilla 15/10 en ajedrez (k = 4) y cuenta 4 cambios más que con la de plan3 (k = 0), con las otras 33 columnas
iguales. El puente solo usa la métrica principal, así que no hace falta corregirlo.

## Cómo se corre

Desde `plan3/`:

| Comando | Qué hace | Escribe |
|---|---|---|
| `python veredicto3.py --probar` | Todas las pruebas (sale con 1 si una falla) | `pruebas/ver/prueba_veredicto3.txt`, `pruebas/ver/ejemplo_veredicto3.md` (salida de un mundo sintético) y temporales en `tmp_ver/` |
| `python veredicto3.py --final` | El veredicto, después del cierre | `salidas/veredicto3_celdas.csv`, `_bases.csv`, `_hipotesis.csv`, `_comparaciones.csv`, `_no_insertados.csv` y `veredicto3.md` |
| `python veredicto3.py --prueba-final LISTA.json` | Prueba final reservada (§13) | `listo/holdout.candado` y `salidas/veredicto3_prueba_final.csv` |

`--final` revisa, en este orden, y se niega (sale con 1 sin escribir nada) en cuanto algo falla:
1. `listo/cierre.ok` existe.
2. El sello `cola/manifiesto_cierre.json` (el de `manifiesto.py cierre`) tiene `csv`, `metas` y `otros`; cada CSV del
   manifiesto está sellado (salvo los de uso 'final' y los que no existen porque su base cayó) y no hay sellados de
   más; nada sellado cambió (CSV, cada `politica_*.pt` y `.json`, otros); los archivos de control están sellados.
3. La historia de `cola/manifiesto_ciego.json` en git cubre cada CSV sellado de `ciego/` con su primer sha256, y
   contiene la última mañana que vio el cierre.
4. Los datos se leen en modo estricto: hace falta `cola/trabajos.jsonl`, el trabajo de cada CSV, el meta de cada
   política (sellado), y cada base del diseño evaluada o declarada caída; cada meta de plan3 o C0 elegido con criterio
   total y 16 semillas.
5. Las semillas de cada CSV son las de su tanda en el generador y caen en el bloque de su uso en la tabla JSON de §3.
6. Durante el análisis: cada CSV con exactamente sus semillas y el brazo de su trabajo; brazos distintos por celda y
   tanda; ninguna celda sin modelo principal.

## Qué lee y qué escribe

| Lee (relativo a `plan3/`) | Para qué |
|---|---|
| `cola/manifiesto_esperado.json` | Un CSV por (celda, escenario, tanda, brazo) con `tipo`, `base` y semillas. veredicto3 trabaja **por tipo**, nunca por nombre de archivo |
| `cola/trabajos.jsonl` | El comando de cada CSV: la política que juega (y su meta) y el brazo que debe decir |
| `cola/caidas.json` | Bases caídas declaradas (§14, B22), con su corrida |
| CSV de `evaluar3.py` (`ciego/...`, `parciales/...`) | Una fila por semilla; principal `retraso_total_prom`; secundarias, `generados` y `no_insertados` |
| `politica_*.json`, `insumos/entregado/politica_*.json` | `val_elegido`, `ep_elegido`, `val_total_serie` (o la serie con que se eligió), criterio y semillas de validación |
| `promocion.json` y `promocion/<escenario>.json` | Modelo citado (§12), con su sha256 |
| `insumos/puente/eval_<esc>_*.csv` e `insumos/manifiesto.json` | Fijo e IPPO entregados en 1001-1030 (puente) y sus sha256 |
| `<esc>.sumocfg` con su red y sus `.add.xml` (la plantilla versionada) | k de cada plantilla, para corregir los cambios de fase |
| `listo/cierre.ok`, `cola/manifiesto_cierre.json`, historia git de `cola/manifiesto_ciego.json` | Solo `--final` |
| `listo/holdout.ok`, `listo/holdout.candado` | Solo `--prueba-final` |
| `PRERREGISTRO.md` (tabla JSON de §3, vía `protecciones.tabla_prerregistro`) | Semillas de cada uso |
| `../plan2/diag_corredor/resultados.csv` (solo lectura) | Versión evaluada de la V2 del diagnóstico, para mostrar las dos si cambia (§6) |

**Escribe solo dentro de `plan3/`** (y nunca la carpeta `plan3` misma): toda escritura pasa por `escribir()`, que
resuelve la ruta real y se niega si cae fuera. El temporal de `veredicto.probar()` se redirige a `tmp_ver/tempfile/`.
`sys.dont_write_bytecode = True` antes de importar: importar `veredicto`, `consolidar`, `sintesis_plan`,
`generar_trabajos3`, `protecciones`, `manifiesto` y `p3_promocion` no deja `__pycache__`. Al terminar las pruebas,
`git --no-optional-locks status --porcelain --ignored -- plan2 TESIS` sale vacío con rc 0 (G01). Las pruebas crean un
repositorio git anidado y temporal en `tmp_ver/mundo` para tener mañanas commiteadas del manifiesto ciego; no toca el
repositorio de la rama.

**Lo que importa de lo entregado** (al importarse solo definen constantes y funciones): `vd.veredicto`,
`vd.texto_veredicto`, `vd.convergencia`, `vd.flotante`, `vd.IGUAL`, `vd.ALFA`; `consolidar.comparar`;
`sintesis_plan.indice_geo`. En las pruebas, además, `vd.probar`, `vd.info_base` y `vd.base_mediana` para comparar. De
`plan3/`: `generar_trabajos3` (celdas, tandas, `nombre_corrida`, `DERIVA`), `protecciones`, `manifiesto` (`OTROS`; en
las pruebas, `sello`, `revisar_historia` y `politicas_evaluadas`) y, en las pruebas, `p3_promocion`.

## Qué hace cada función

**Reglas (funciones puras).**

| Función | Qué hace | Regla |
|---|---|---|
| `serie_criterio(meta)` | Serie con que se eligió el checkpoint, con el último valor de cada fila (la media): `val_total_serie` en todo plan3 y C0 | §6 [AMB-1] |
| `validar_meta(meta, ruta)` | ERROR si una base de plan3 o C0 no se eligió con criterio total y las 16 semillas | §6 |
| `entrenamiento(meta)` | Validación elegida, episodio, convergencia, distancia a la mediana de la serie y si el mínimo se repite | §6, §11 [AMB-2, 3, 25] |
| `base_mediana_n`, `mejor_base` | Versión evaluada (3.ª de 5, 2.ª de 3; par: la peor central; empate: la base menor) y mejor base | §6, B21, A3 |
| `comparar(a, b, esperadas)` | `consolidar.comparar`; **ERROR si falta o sobra una semilla** | §7 [AMB-10] |
| `etiqueta`, `acuerdo` | Regla de `veredicto.py` con el veto del actuado ajustado; etiqueta citable (tabla de §7) | §7 [AMB-4, 5] |
| `sentido` | k de n bases del lado (signo); 4 de 5 o 3 de 3; una base caída cuenta fuera | §7, A5 [AMB-7] |
| `holm` | Holm por familia y tanda; una prueba sin correr entra con p = 1 | §9 |
| `p_no_inferioridad`, `lectura_ni`, `lectura_ni_conjunta` | Wilcoxon de una cola sobre a − 1.02·b; las tres lecturas por tanda; la lectura de las dos tandas | §8 [AMB-9] |
| `equivalente`, `interseccion_union` | ±1 % (H4); H1 global | §8 |
| `bootstrap_cambios`, `diferencia_no_pareada` | H6 | §8 [AMB-11] |
| `generados_iguales`, `igual_ciclo_minimo` | Mismos vehículos por semilla; igual al ciclo mínimo | §7, §5 [AMB-14, 24] |
| `demanda_esperada`, `numero_unico` | Demanda con `exp(λ)`; `sintesis_plan.indice_geo` con `default_rng(0)` | §7 |
| `brazo_de_trabajo` | El brazo que escribe `evaluar3.py` para un trabajo (política, fijo desde un programa, referencia, regla) | — |
| `caidas_de_texto`, `declaracion_caida`, `corrida_de` | Lee y valida `cola/caidas.json` (sin corrida, la arma como el generador); la declaración que hace caer una base, por su clave o por su corrida y lo que sale de ella | §14 [AMB-7] |
| `corre_por_rl_ippo`, `k_plantilla` | Si un brazo corre por rl_ippo; k de la plantilla de un escenario | Hallazgo 10 |

**Datos (`class Datos`).** Lee el manifiesto y arma, por celda (celda, escenario), los tipos con sus bases y tandas;
con `estricto` y `sello` (modo `--final`) exige todo lo de arriba.

| Método | Qué hace |
|---|---|
| `verificar`, `leer_otro`, `sha_insumo` | El sello: un meta o archivo de control que se lee debe estar sellado con el mismo sha256 |
| `leer_caidas`, `ruta_base`, `es_caida` | `cola/caidas.json` (sellado); la ruta de la política de una base; si cayó |
| `bases_disenio`, `meta_base`, `base_version` | Bases del diseño; meta y estado de cada base (caída, publicada, sin meta); versión evaluada o mejor base |
| `pub_info` | Versión publicada por `p3_elegir mediana`: **comprueba** que su base es la mediana de sus candidatas |
| `entrada`, `filas_csv`, `serie`, `serie_insumo`, `k_cambios` | El CSV de un brazo en una tanda; T1x = t1r + h1t1; cotejo de semillas, brazo y base; los cambios de fase de rl_ippo menos k |
| `comp`, `convergencia` | Comparación con caché (motivo si faltan datos o cambian los vehículos); convergencia de la versión [AMB-28] |
| `promocion`, `citado` | Decisión de promoción por escenario (con sha256) y modelo citado [AMB-20] |

**Análisis y salidas.** `etiqueta_brazo`, `sentido_brazo`, `referencias_al_lado`, `filas_no_insertados`,
`fila_celda` (fila de `veredicto3_celdas.csv` con las lecturas obligadas), `tabla_bases`, `pruebas_definidas` (todas las
pruebas de §8 con sus familias exactas y las descriptivas, a3 incluido), `evaluar_pruebas`, `h_etiqueta`, `h6`,
`hipotesis` (H0-H15, perfil, mezcla y arranque lento), `tabla_numero`, `comparaciones`, `medianas`,
`revisar_generados`, `versiones_diag`, `analizar`, `texto_md`, `escribir_salidas`.

**Modos.** `otros_que_se_sellan`, `comprobar_cierre`, `historia_ciego`, `comprobar_ciego`, `comprobar_semillas`,
`correr_final`, `correr_prueba_final`.

**Pruebas.** `fabricar`, `mundo_sintetico` (una carpeta plan3 completa: el manifiesto y los trabajos del generador tal
cual, con dos bases caídas que el generador ya no evalúa; `agregar_si_falta` con `extras_mundo`; promoción decidida
con `p3_promocion`; dos mañanas commiteadas; el sello de `manifiesto.py`), `sellar_mundo`, `manifiesto_ciego_de` y
`probar`.

## Pruebas y resultados (160 de 160 pasan)

**1. Las del prototipo, con lo entregado de `plan2/` (solo lectura).** P01-P18 y P08b: la regla no cambió
(`veredicto.probar()`); la V2 de P6 da meseta 3.19 % y estabilidad 0.00 % (P02; con x[3], 9.43 % y "no convergió");
18/18 metas iguales a `info_base`; 5/5 niveles del corredor iguales a `analisis.py`; `comparar` = resumen de
`consolidar` (−6.7 % [−7.85, −5.67], p = 1.86e-09); etiquetas de IPPO con mensajes P1-P6 = robustez entregada (6/6)
y de los 12 niveles = entrega 3 (12/12); Holm, tabla de acuerdo, sentido (P11 cambió: con 3 bases se pide 3 de 3,
A5), margen +2 %, demanda con `exp()`, mismos vehículos en P1, H6 y no inferioridad con datos reales.

**2. Reglas nuevas con datos fabricados.**

| Prueba | Resultado |
|---|---|
| N01 `base_mediana_n` (= `vd.base_mediana` con 3; 5; 4 con una caída; empates) | pasan |
| N02 x[−1] de `val_total_serie`; N03 una semilla de más o de menos: ERROR | pasan |
| N04 cada fila de la tabla citable de §7 (14 combinaciones, también al revés), PENDIENTE por convergencia y por referencia faltante | 16/16 |
| N05 veto del actuado ajustado; N06 sentido 4 de 5 (una base en contra pasa, dos no; una caída cuenta fuera) | pasan |
| N07 Holm con 6; N08 tres lecturas de la no inferioridad; N09 H1 por intersección-unión; N10 H6; N11 vehículos y ciclo mínimo; N12 número único | pasan |
| N13-N13d no escribe fuera de `plan3/` ni la carpeta `plan3`; `carpeta_limpia` solo `tmp_*` | pasan |
| N14 semillas del prerregistro; N15 lectura conjunta de la no inferioridad (8 casos); N16 `acuerdo` sin StopIteration; N17 criterio y semillas de las bases; N18 k de las plantillas de plan3 y qué brazos corren por rl_ippo | pasan |

**3. Mundo sintético de punta a punta** (`tmp_ver/mundo/plan3`: 32 celdas, 1696 CSV = 1670 del generador + 30 de la
política por red − 4 referencias quitadas).

| Prueba | Resultado |
|---|---|
| M00-M00b: el manifiesto es el del generador, sin duplicados; solo se agrega lo que falta (y una segunda vez nada); el generador no evalúa las bases caídas; el sello es el de `manifiesto.py` (CSV, cada `.pt` y `.json`, otros, último commit de la mañana) | pasan |
| M01-M04r: `--final` se niega sin `cierre.ok`, con un CSV o un meta cambiado después del cierre, sin sello, con semillas de humo, con `promocion.json` cambiado o `caidas.json` sin sellar; ERROR con un meta que se lee sin sellar, un CSV de `ciego/` que no está en ninguna mañana o que cambió después de su mañana (aunque se vuelva a sellar), una base con CSV sin meta, una base sin CSV sin declarar, `caidas.json` sin los dos intentos o con una corrida que no es de su base (y se acepta la fecha una vez por declaración), un CSV con otro brazo que el de su trabajo (política, fijo fino con el nombre del de 5 en 5, regla simple con nombre de Max-Pressure), un CSV dos veces en el manifiesto, dos CSV con el mismo brazo y sin `trabajos.jsonl`; el cierre no pide sellar el CSV que no existe de una base caída declarada, y sí el de una base sin declarar | pasan |
| M05 las 6 salidas; M06 etiqueta citable de V2 en 17 celdas (todas las filas de la tabla de §7, PENDIENTE por convergencia y por referencia faltante); M06b las 6 celdas de perfil, mezcla y arranque lento | 18/18 |
| M07-M11d: veto en D y citado PENDIENTE sin decisión de promoción; P1 promovida por `p3_promocion` (−3.2 % en la validación) con V2 al lado; "se repite 4 de 5" y la lectura de P6; ciclo mínimo; probabilidad por ruido; P4 aleatoria con dos bases caídas: 3 de 5; vehículos sin entrar en P2 aleatoria con su lectura | pasan |
| M12-M24b: H1 (global no pasa y nombra "P5 es peor en T2x (+6.07 %)"; P5 contradictorio), H2, H3/H3e, H5 (4 de 6: P4 cae por las bases caídas), H6, H7r (lectura de §11), H8a/H8b, H12, H10 (red sin datos: "no se pudo correr en 7"; corredor con la política por red: 4 de 5 niveles, pasa), H15 (AMB-18), número único = cálculo directo y "provisional en P3" | pasan |
| M25-M28j: vehículos distintos en una referencia (m2715, fijo ajustado desde 10 s), tabla de bases (convergencia, candidatas, caídas con sus intentos), `.md` (tabla, lecturas, no insertados, promoción, frase de §17), avisos (una línea para promo), a3 (48 filas, todas "mayor"), perfil y mezcla (6 celdas, bloques al lado en el perfil), C0 aleatorio con `v2reg3poi`, celda sin modelo principal, regla reactiva (lectura en P3 regular, no en P1; en H0) | pasan |
| M29-M31: versión publicada que no es la mediana, CSV con una semilla de más y promoción alterada: ERROR | pasan |
| M32-M37: prueba final (tanda de uso 'final' simulada con humo): no entra al veredicto; `manifiesto.sello` no sella sus CSV y el cierre pasa con o sin ellos; sin `holdout.ok` o con otro sha256 se niega; sin el bloque completo, con una métrica vacía o con otros vehículos se niega sin cerrar el candado; corre una vez y no dos. Un sello cuya última mañana no está en la historia y una mañana posterior con otro sha256: se niega. Caídas por corrida, con o sin la corrida en la declaración: las mismas 9 bases que deja de evaluar el generador. Cambios de fase: a V2 y a la regla de P1 se les resta 1 y al fijo fino nada; en P3, 0 | pasan |
| G01 `git status --porcelain --ignored -- plan2 TESIS` vacío, rc 0 | pasa |

## Ambigüedades del prerregistro y lectura implementada

Cada una lleva `[AMB-n]` en el código. **Fijada (05.11)** = el coordinador la decidió y va al prerregistro tal cual.

| AMB | Regla | Lectura implementada | ¿Cambia algo? |
|---|---|---|---|
| 1 | §6: convergencia sobre `val_total_serie`, x[−1] | Así en plan3 y C0; lo elegido con otra serie usa la suya (`serie_eleccion` de `p3_elegir regla`; `val_serie` en lo entregado) | Solo descriptivos y H0 |
| 2 | "Distancia entre la validación elegida y la mediana de la serie" | En s y en % de la mediana de toda la serie | No (descriptiva) |
| 3 | "Si el mínimo se repite en dos validaciones seguidas" | Literal (el mismo valor mínimo en dos seguidas) y, al lado, "las dos mejores son seguidas" | No (descriptiva) |
| 4 | Tabla citable de §7 | **Fijada:** simétrica entre T1 y T2 | Sí |
| 5 | PENDIENTE citable | Con la provisional del acuerdo de las provisionales | No |
| 6 | "Se repite en k de n" | Lado de la etiqueta de cada tanda (FALLA: sobre cero) | Solo la columna |
| 7 | Base caída "fuera del sentido" | **Fijada:** fuera del lado y el mínimo no baja; n del diseño; declarada en `cola/caidas.json`. El prerregistro no nombra la corrida ni dice si la fecha va por intento: se acepta la fecha en cada intento o una vez por declaración, y la corrida (la que usa el generador) hace caer también lo que sale de ella | Sí, si cae una base |
| 8 | ¿Una no inferioridad es afirmación de método? | **Fijada:** H8c, H12 y H10 llevan sentido (bajo +2 % por base en T1 y T2); H1 no (su potencia ≥ 93 % con 120 semillas se calculó sin él y C0 por base solo se evalúa en P4 y m6525) | Sí |
| 9 | Lectura de una no inferioridad en las dos tandas | **Fijada:** pasa solo con "no es peor" en T1 y T2 (y con sentido en las dos si lo lleva); si no, es peor, pérdida no confirmada, contradictorio o no concluyente | La frase |
| 10 | p de Wilcoxon | El de `consolidar` (3 cifras, como lo entregado), también para Holm; los de una cola sin redondear | En el borde |
| 11 | Generadores del bootstrap de H6 | `default_rng(1)` y `default_rng(2)` (prototipo) | 2.º decimal del IC |
| 12 | Etiqueta de una referencia (H0) | Solo frente al fijo fino, sin veto (como lo entregado) | H0 |
| 13 | Falta el actuado ajustado | **Fijada:** PENDIENTE con motivo (regla de `veredicto.py`) | Si falta |
| 14 | Vehículos distintos | **Fijada:** la comparación queda PENDIENTE con su motivo y hay aviso | Si ocurre |
| 15 | "P6 y P6e con llegadas aleatorias" | Solo existe P6 aleatoria (ya con la entrada corregida) | No |
| 16 | Lectura del fijo de verdes de 5 en 5 (§5 y §11) | La de §11 si gana el fino y empata el de 5 en 5; si no, la de §5 | El texto |
| 17 | Número único | **Fijada:** los seis casos; con datos aunque haya PENDIENTE por convergencia, y entonces "provisional en [casos]" | La cifra |
| 18 | Hipótesis por caso sin regla global | **Fijada:** "pasa en k de n casos: [casos]"; en §17, "pasa" = al menos un caso | La frase |
| 19 | H10 | Tipo `p3red`, 3 bases, en cada nivel de su red. La Etapa 4 aún no está en el generador: el mundo la agrega en el corredor con un nombre supuesto (`politica_corredor_niveles_vecinos_p3red_s<b>.pt`) | Hoy, sin datos reales |
| 20 | Clave de la promoción | El escenario (el generador llama a `p3_promocion` con `--celda <escenario>`) | Interfaz |
| 21 | H1 y H2 con 120 semillas | V2 = CSV de la base mediana en t1r + `v2reg3med` en h1t1 (misma base, comprobada) | No |
| 22 | Etiqueta con la mejor base | Con su convergencia; con una variante citada, su mejor base (y la de V2 al lado) | Esa columna |
| 23 | Cuadro 2×2 y su lectura | Con las tandas de 30 semillas | La lectura |
| 24 | Igual al ciclo mínimo | Medias redondeadas a 4 decimales, como `consolidar` | En el borde |
| 25 | Episodios de las metas de `p3_elegir regla` | El último de la serie con que eligió | No |
| 26 | IPPO entregado en el puente | Su versión evaluada (regla del 25.09) | No |
| 27 | C0 aleatorio | **Fijada:** frente a la V2 regular de 42/2042/4042 jugada con llegadas aleatorias (`v2reg3poi`) | No (descriptiva) |
| 28 | Convergencia de una versión jugada en otra celda | La de su propio entrenamiento | H0 y transferencias |

## Interfaces con otras áreas

1. **Sello del cierre.** Los tres cambios de `manifiesto.py` ya están (d2501e5) y casan con `comprobar_cierre` (M00b,
   M04b-M04g, M32b). Después de la enmienda de la prueba final hay que volver a correr `manifiesto.py cierre`: sella el
   manifiesto nuevo sin los CSV de uso 'final', y la historia de las mañanas comprueba que los de T1 y T2 no cambiaron.
   Dos detalles menores de `manifiesto.caida_declarada` (solo cambian el texto del aviso): lee el `cola/caidas.json`
   real (`gt.leer_caidas`) y no el de la carpeta que se revisa, y busca la corrida por el escenario del CSV, así que en
   `mixa_` (que juega la política de `mix_`) no avisa.
2. **`cola/caidas.json`.** El generador y veredicto3 aceptan la declaración con o sin corrida. Para la mezcla y el
   arranque lento conviene declarar con el escenario de la política (`mix_corredor`, `mix_red`): así cae en las dos
   celdas, en el generador y en veredicto3.
3. **Regla reactiva.** `reglas.py` todavía no tiene la familia `reactiva` (el generador ya la pide). veredicto3 acepta
   cualquier nombre que empiece con "reactiva"; cuando se fije (p. ej. `reactiva_d<D>`), conviene ajustar `FORMA_REGLA`.
4. **Política por red (Etapa 4).** veredicto3 espera el tipo `p3red` con 3 bases en cada nivel de su red. Cuando el
   generador la produzca con ese tipo, el mundo usará sus entradas (compara por clave); con otro tipo, hay que avisarme.
5. **evaluar3 con `--perdida`:** el brazo sale con doble sufijo (`..._L0p100_p100`: uno de `evaluar.brazo_profundo` y otro
   de `evaluar3`). veredicto3 lo reproduce tal cual; si se cambia uno, hay que cambiar `brazo_de_trabajo`.
6. **Cambios de fase.** Si se corrige el contador de rl_ippo (leer la fase después del setPhase), k pasa a 0 para los
   CSV nuevos y hay que quitar la resta en `Datos.k_cambios` (o hacerla depender del código con que se corrió cada CSV).
7. **Prueba final:** la lista que acepta `--prueba-final` es
   `{"comparaciones": [{"celda", "escenario", "tanda", "a": {"tipo", "base"}, "b": {"tipo", "base"}}]}`.

## Límites

- Nada de esto vio datos reales; con datos reales está probado que las reglas reproducen lo entregado (P01-P18).
- Duración: ~55 s con 10 semillas sintéticas por tanda. Con datos reales (30-120 semillas, unas 7000 comparaciones
  con 10 000 remuestreos cada una) se estiman unos pocos minutos [I].
- veredicto3 no calcula relanzamientos ni desvíos (están en `cola/estado.json` y en las enmiendas); el `.md` lo dice.
