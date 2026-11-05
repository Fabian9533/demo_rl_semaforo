# veredicto3.py: informe de implementación (PLAN3 5.0; DECISIONES B11, B21 y B22)

05.11.2026, con la revisión de la tarde. Rama `plan3-ver` (nació de `plan3-dev` en cff0d61 y trae `plan3-dev` fusionada
hasta fd9176a). No se simuló nada y no se abrió ningún resultado decisivo (todavía no existen): todo se probó con lo
entregado de `plan2/` (solo lectura) y con datos sintéticos que usan las semillas de humo (424301-424360) en
`plan3/tmp_ver/` (ignorada por git).

## Respuesta corta

- **Qué hay.** `plan3/veredicto3.py` (~2400 líneas de código y ~1050 de pruebas, con el mundo sintético). Calcula, con las reglas del
  prerregistro (parte A), las etiquetas de cada celda (T1, T2 y citable), el modelo citado, el sentido entre
  entrenamientos, todas las hipótesis de §8 con sus familias y Holm, el número único, las lecturas obligadas y el
  informe de vehículos sin entrar al cierre (§4).
- **Modos.** `--probar` (147 pruebas, ~25 s), `--final` (se niega si algo sellado cambió, si un CSV de `ciego/` no es
  el de su primera mañana, si falta un trabajo, un meta o una base sin declararla caída) y `--prueba-final LISTA.json`
  (§13: valida todo, luego crea el candado en exclusiva y corre una sola vez).
- **Pruebas: 147 de 147 pasan** (`plan3/pruebas/ver/prueba_veredicto3.txt`).
- **La revisión del 05.11** (43 revisores, 21 hallazgos confirmados) reprodujo la estadística al dígito. Los 12 arreglos
  que tocaban a veredicto3 están hechos (lista abajo) y las reglas que el coordinador fijó (AMB-7, 8, 9, 17, 18, 27)
  están implementadas tal cual.

## Arreglos de la revisión (05.11)

| # | Hallazgo | Qué se hizo | Prueba |
|---|---|---|---|
| 1 | Faltaba el informe de no insertados al cierre (§4 nuevo) | Por celda, tanda y **cada** brazo: semillas con no insertados y vehículos (`veredicto3_no_insertados.csv` y sección del `.md`); la lectura obligada va en la celda si un brazo deja vehículos sin entrar | M11c, M11d, M28 |
| 2 | Lectura conjunta de la no inferioridad | `lectura_ni_conjunta` (AMB-9 fijada): pasa solo con "no es peor" en T1 y T2 y, si lleva sentido, con sentido en las dos; si solo falla el sentido, "la versión evaluada no es peor; el método no se repite en k de n"; si no pasa: es peor, pérdida no confirmada, contradictorio o no concluyente, con la lectura de cada tanda. En H1 se nombra cada tanda que da "es peor" con su caso y su cifra. Una superioridad que pasa en las dos tandas sin sentido dice la lectura de §11 | N15, M12, M13, M19, M21 |
| 3 | Bases caídas | n sale del **diseño** (5 para V2 regular en P1-P6, P6e, c2715 y D; 5 para V2 aleatoria en los 6 casos; 5 para la observación nueva en c2715 y D; 3 en lo demás). La caída se declara en `cola/caidas.json` (celda, escenario, tipo, base y los dos intentos con id, error y fecha): fuera de la mediana y fuera del lado. Sin CSV y sin declarar: ERROR en `--final`. Con CSV y sin meta: ERROR siempre | M04h, M04i, M04j, M11b, M17, M18, M27 |
| 4 | Prueba final | Cada CSV en una tanda de uso 'final' (`gt.TANDAS`) con el bloque completo de su tipo de llegadas (11001-11030 o 12001-12100); métrica, semillas y vehículos (`generados_iguales`) validados y la comparación calculada **antes** del candado; candado con `open('x')` y con el sha256 de la lista, de `holdout.ok`, de cada CSV leído y de la salida. `comprobar_cierre` no exige sellar lo de uso 'final' | M32-M34b |
| 5 | C0 aleatorio frente a la V2 de 5 bases | El contraste "elegir con desorden" usa `v2reg3poi` (V2 regular de 42/2042/4042 jugada con llegadas aleatorias; en P6, la mediana de 3 de P6e). `v2regmed` queda para H0 y las transferencias | M28f |
| 6 | Regla simple, `acuerdo()`, criterio de las bases | La lectura de la regla simple prohíbe las dos frases de §5; `acuerdo` ya no lanza StopIteration; ERROR si una base de plan3 o de C0 no se eligió con criterio total y las 16 semillas (salvo lo entregado, `p3_elegir regla` y la política por red) | N16, N17 |
| 7 | Tipos de perfil, mezcla, arranque lento y a3; celda sin modelo principal | Modelo principal `v2reg`, `v2poi`, `v2per`, `v2mix`; filas descriptivas de perfil (con el fijo por bloques al lado), mezcla y arranque lento por escenario (`per_`, `mix_`, `mixa_`), y de a3 (`a3colas0_<t>`, `a3msg0_<t>` frente a la misma versión sin perturbar); lo que no está, "no se pudo correr". Una celda sin modelo principal da fila PENDIENTE con aviso y, en `--final`, ERROR | M06, M28d, M28e, M28h, M28i |
| 8 | Tanda promo | Una sola línea de aviso por tanda que no entra al veredicto; el mundo sintético usa las partes base del generador (sin los alias de etapa3b), fabrica los 58 CSV de promoción y decide con `p3_promocion.decidir` y `juntar` reales | M08, M28b |
| 9 | Brazo de cada CSV | Se exige la columna brazo y que sea el que escribe su trabajo (`--politica`: `ippo_<variante>[_<etiqueta>]_s<base>` del meta, con `_L0p<k>_p<k>` y `_colas0`; `--brazo X`: X), con su base; cada CSV una sola vez en el manifiesto; brazos distintos dentro de cada celda y tanda | M04k, M04l, M04m |
| 10 | Segunda barrera del a ciegas | `comprobar_ciego`: cada CSV sellado de `ciego/` aparece en alguna versión commiteada de `cola/manifiesto_ciego.json`, su sha256 no cambió de una mañana a otra y el del cierre es el de la primera mañana | M04f, M04g, M35 |
| 11 | Sello completo | `cola/manifiesto_cierre.json` con `csv`, `metas` y `otros` (manifiesto esperado, trabajos, caídas, `promocion.json` y `promocion/*.json`); en `--final` todo meta y todo archivo de control que se lee debe estar sellado con el mismo sha256 (los insumos, contra `insumos/manifiesto.json`) | M04b-M04e, M04n |
| 12 | Escrituras de borde | G01 exige `rc == 0` y usa `git --no-optional-locks`; N13b ya no llama a `tempfile.gettempdir()`; `dentro_de_plan3` rechaza la carpeta `plan3` misma; `carpeta_limpia` solo borra `plan3/tmp_*` (y quita el atributo de solo lectura que deja git en Windows) | G01, N13b-N13d |

## Cómo se corre

Desde `plan3/`:

| Comando | Qué hace | Escribe |
|---|---|---|
| `python veredicto3.py --probar` | Todas las pruebas (sale con 1 si una falla) | `pruebas/ver/prueba_veredicto3.txt`, `pruebas/ver/ejemplo_veredicto3.md` (salida de un mundo sintético) y temporales en `tmp_ver/` |
| `python veredicto3.py --final` | El veredicto, después del cierre | `salidas/veredicto3_celdas.csv`, `_bases.csv`, `_hipotesis.csv`, `_comparaciones.csv`, `_no_insertados.csv` y `veredicto3.md` |
| `python veredicto3.py --prueba-final LISTA.json` | Prueba final reservada (§13) | `listo/holdout.candado` y `salidas/veredicto3_prueba_final.csv` |

`--final` revisa, en este orden, y se niega (sale con 1 sin escribir nada) en cuanto algo falla:
1. `listo/cierre.ok` existe.
2. El sello `cola/manifiesto_cierre.json` tiene `csv`, `metas` y `otros`; los CSV sellados son los del manifiesto
   (menos los de uso 'final' y los de bases caídas declaradas) y nada sellado cambió; los archivos de control están
   sellados.
3. La historia de `cola/manifiesto_ciego.json` en git cubre cada CSV sellado de `ciego/` con su primer sha256.
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
| `cola/caidas.json` | Bases caídas declaradas (§14, B22) |
| CSV de `evaluar3.py` (`ciego/...`, `parciales/...`) | Una fila por semilla; principal `retraso_total_prom`; secundarias, `generados` y `no_insertados` |
| `politica_*.json`, `insumos/entregado/politica_*.json` | `val_elegido`, `ep_elegido`, `val_total_serie` (o la serie con que se eligió), criterio y semillas de validación |
| `promocion.json` y `promocion/<escenario>.json` | Modelo citado (§12), con su sha256 |
| `insumos/puente/eval_<esc>_*.csv` e `insumos/manifiesto.json` | Fijo e IPPO entregados en 1001-1030 (puente) y sus sha256 |
| `listo/cierre.ok`, `cola/manifiesto_cierre.json`, historia git de `cola/manifiesto_ciego.json` | Solo `--final` |
| `listo/holdout.ok`, `listo/holdout.candado` | Solo `--prueba-final` |
| `PRERREGISTRO.md` (tabla JSON de §3, vía `protecciones.tabla_prerregistro`) | Semillas de cada uso |
| `../plan2/diag_corredor/resultados.csv` (solo lectura) | Versión evaluada de la V2 del diagnóstico, para mostrar las dos si cambia (§6) |

**Escribe solo dentro de `plan3/`** (y nunca la carpeta `plan3` misma): toda escritura pasa por `escribir()`, que
resuelve la ruta real y se niega si cae fuera. El temporal de `veredicto.probar()` se redirige a `tmp_ver/tempfile/`.
`sys.dont_write_bytecode = True` antes de importar: importar `veredicto`, `consolidar`, `sintesis_plan`,
`generar_trabajos3`, `protecciones` y `p3_promocion` no deja `__pycache__`. Al terminar las pruebas,
`git --no-optional-locks status --porcelain --ignored -- plan2 TESIS` sale vacío con rc 0 (G01). Las pruebas crean un
repositorio git anidado y temporal dentro de `tmp_ver/mundo` para tener mañanas commiteadas del manifiesto ciego; no
toca el repositorio de la rama.

**Lo que importa de lo entregado** (al importarse solo definen constantes y funciones): `vd.veredicto`,
`vd.texto_veredicto`, `vd.convergencia`, `vd.flotante`, `vd.IGUAL`, `vd.ALFA`; `consolidar.comparar`;
`sintesis_plan.indice_geo`. En las pruebas, además, `vd.probar`, `vd.info_base` y `vd.base_mediana` para comparar.

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
| `brazo_de_trabajo` | El brazo que escribe `evaluar3.py` para un trabajo | — |

**Datos (`class Datos`).** Lee el manifiesto y arma, por celda (celda, escenario), los tipos con sus bases y tandas;
con `estricto` y `sello` (modo `--final`) exige todo lo de arriba.

| Método | Qué hace |
|---|---|
| `verificar`, `leer_otro`, `sha_insumo` | El sello: un meta o archivo de control que se lee debe estar sellado con el mismo sha256 |
| `leer_caidas`, `es_caida` | `cola/caidas.json` |
| `bases_disenio`, `meta_base`, `base_version` | Bases del diseño; meta y estado de cada base (caída, publicada, sin meta); versión evaluada o mejor base |
| `pub_info` | Versión publicada por `p3_elegir mediana`: **comprueba** que su base es la mediana de sus candidatas |
| `entrada`, `filas_csv`, `serie`, `serie_insumo` | El CSV de un brazo en una tanda; T1x = t1r + h1t1; cotejo de semillas, brazo y base |
| `comp`, `convergencia` | Comparación con caché (motivo si faltan datos o cambian los vehículos); convergencia de la versión [AMB-28] |
| `promocion`, `citado` | Decisión de promoción por escenario (con sha256) y modelo citado [AMB-20] |

**Análisis y salidas.** `etiqueta_brazo`, `sentido_brazo`, `referencias_al_lado`, `filas_no_insertados`,
`fila_celda` (fila de `veredicto3_celdas.csv` con las lecturas obligadas), `tabla_bases`, `pruebas_definidas` (todas las
pruebas de §8 con sus familias exactas y las descriptivas, a3 incluido), `evaluar_pruebas`, `h_etiqueta`, `h6`,
`hipotesis` (H0-H15, perfil, mezcla y arranque lento), `tabla_numero`, `comparaciones`, `medianas`,
`revisar_generados`, `versiones_diag`, `analizar`, `texto_md`, `escribir_salidas`.

**Modos.** `comprobar_cierre`, `historia_ciego`, `comprobar_ciego`, `comprobar_semillas`, `correr_final`,
`correr_prueba_final`.

**Pruebas.** `fabricar`, `mundo_sintetico` (una carpeta plan3 completa: el manifiesto y los trabajos reales del generador
con sus partes base, más lo que todavía no produce: referencias nuevas, `v2reg3poi`, a3, perfil, mezcla y arranque
lento; dos bases caídas declaradas; promoción decidida con `p3_promocion`; sello; dos mañanas commiteadas),
`sellar_mundo`, `manifiesto_ciego_de` y `probar`.

## Pruebas y resultados (147 de 147 pasan)

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
| N14 semillas del prerregistro; N15 lectura conjunta de la no inferioridad (8 casos); N16 `acuerdo` sin StopIteration; N17 criterio y semillas de las bases | pasan |

**3. Mundo sintético de punta a punta** (`tmp_ver/mundo`, 29 celdas, 1650 CSV).

| Prueba | Resultado |
|---|---|
| M01-M04n: `--final` se niega sin `cierre.ok`, con un CSV o un meta cambiado después del cierre, sin sello, con semillas de humo, con `promocion.json` cambiado o `caidas.json` sin sellar; ERROR con un meta que se lee sin sellar, un CSV de `ciego/` que no está en ninguna mañana o que cambió después de su mañana (aunque se vuelva a sellar), una base con CSV sin meta, una base sin CSV sin declarar, `caidas.json` sin los dos intentos, un CSV con otro brazo que el de su trabajo, un CSV dos veces en el manifiesto, dos CSV con el mismo brazo y sin `trabajos.jsonl` | pasan |
| M05 las 6 salidas; M06 etiqueta citable de V2 en 20 celdas (todas las filas de la tabla de §7, PENDIENTE por convergencia y por referencia faltante, perfil, mezcla y arranque lento) | 20/20 |
| M07-M11d: veto en D y citado PENDIENTE sin decisión de promoción; P1 promovida por `p3_promocion` (−3.2 % en la validación) con V2 al lado; "se repite 4 de 5" y la lectura de P6; ciclo mínimo; probabilidad por ruido; P4 aleatoria con dos bases caídas: 3 de 5; vehículos sin entrar en P2 aleatoria con su lectura | pasan |
| M12-M24b: H1 (global no pasa y nombra "P5 es peor en T2x (+6.07 %)"; P5 contradictorio), H2, H3/H3e, H5 (4 de 6: P4 cae por las bases caídas), H6, H7r (lectura de §11), H8a/H8b, H12, H10 sin datos, H15 (AMB-18), número único = cálculo directo y "provisional en P3" | pasan |
| M25-M28i: vehículos distintos en una referencia, tabla de bases (convergencia, candidatas, caídas con sus intentos), `.md` (tabla, lecturas, no insertados, promoción, frase de §17), avisos (una línea para promo), a3 (48 filas), perfil y mezcla, C0 aleatorio con `v2reg3poi`, celda sin modelo principal | pasan |
| M29-M31: versión publicada que no es la mediana, CSV con una semilla de más y promoción alterada: ERROR | pasan |
| M32-M35: prueba final (tanda de uso 'final' simulada con humo): no entra al veredicto ni al sello; sin `holdout.ok` o con otro sha256 se niega; sin el bloque completo, con una métrica vacía o con otros vehículos se niega sin cerrar el candado; corre una vez con el sha256 de cada CSV y de la salida en el candado; no corre dos veces. Una mañana posterior con otro sha256 para un CSV: se niega | pasan |
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
| 7 | Base caída "fuera del sentido" | **Fijada:** fuera del lado y el mínimo no baja; n del diseño; declarada en `cola/caidas.json` | Sí, si cae una base |
| 8 | ¿Una no inferioridad es afirmación de método? | **Fijada:** H8c, H12 y H10 llevan sentido (bajo +2 % por base en T1 y T2); H1 no (su potencia ≥ 93 % con 120 semillas se calculó sin él y C0 por base solo se evalúa en P4 y m6525) | Sí |
| 9 | Lectura de una no inferioridad en las dos tandas | **Fijada:** ver arreglo 2 | La frase |
| 10 | p de Wilcoxon | El de `consolidar` (3 cifras, como lo entregado), también para Holm; los de una cola sin redondear | En el borde |
| 11 | Generadores del bootstrap de H6 | `default_rng(1)` y `default_rng(2)` (prototipo) | 2.º decimal del IC |
| 12 | Etiqueta de una referencia (H0) | Solo frente al fijo fino, sin veto (como lo entregado) | H0 |
| 13 | Falta el actuado ajustado | **Fijada:** PENDIENTE con motivo (regla de `veredicto.py`) | Si falta |
| 14 | Vehículos distintos | **Fijada:** la comparación queda PENDIENTE con su motivo y hay aviso | Si ocurre |
| 15 | "P6 y P6e con llegadas aleatorias" | Solo existe P6 aleatoria (ya con la entrada corregida) | No |
| 16 | Lectura del fijo de verdes de 5 en 5 (§5 y §11) | La de §11 si gana el fino y empata el de 5 en 5; si no, la de §5 | El texto |
| 17 | Número único | **Fijada:** los seis casos; con datos aunque haya PENDIENTE por convergencia, y entonces "provisional en [casos]" | La cifra |
| 18 | Hipótesis por caso sin regla global | **Fijada:** "pasa en k de n casos: [casos]"; en §17, "pasa" = al menos un caso | La frase |
| 19 | H10 | Tipo `p3red`; niveles por red como en el informe | Hoy "no se pudo correr" |
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

1. **Sello del cierre** (`manifiesto.py cierre`, lo hace el coordinador): `{"csv": {...}, "metas": {...}, "otros": {...}}`
   con rutas relativas a `plan3/`. `otros` debe traer `cola/manifiesto_esperado.json`, `cola/trabajos.jsonl`,
   `cola/caidas.json` (si existe), `promocion.json` y `promocion/*.json`; `metas`, los `politica_*.json` de todo lo
   evaluado (los de `insumos/` se cotejan con `insumos/manifiesto.json`). Los CSV de uso 'final' y los de bases caídas
   no se sellan.
2. **Tipos que el generador todavía no produce:** `ref_fino`, `ref_actuadoaj`, `ref_fino5`, `ref_franja`, `ref_bloques`,
   `ref_regla`, `ref_mp`, `ref_mpc`, `v2reg3poi`, los de perfil y mezcla (`v2per`, `v2mix`, en `per_`, `mix_` y `mixa_`),
   a3 (`a3colas0_<t>`, `a3msg0_<t>`) y `p3red`. Mientras falten: PENDIENTE con su motivo o "no se pudo correr".
3. **evaluar3 con `--perdida`:** el brazo sale con doble sufijo (`..._L0p100_p100`: uno de `evaluar.brazo_profundo` y otro
   de `evaluar3`). veredicto3 lo reproduce tal cual para el cotejo; si se cambia uno, hay que cambiar `brazo_de_trabajo`.
4. **Prueba final:** la enmienda que la active declara su tanda en `generar_trabajos3.TANDAS` con uso 'final' y sus CSV
   en el manifiesto; la lista que acepta `--prueba-final` es
   `{"comparaciones": [{"celda", "escenario", "tanda", "a": {"tipo", "base"}, "b": {"tipo", "base"}}]}`.
5. El error del generador del informe anterior (rutas de IPPO entregado con doble guion bajo) ya está corregido en
   `plan3-dev` (`mediana` sin etiqueta).

## Límites

- Nada de esto vio datos reales; con datos reales está probado que las reglas reproducen lo entregado (P01-P18).
- Duración: ~25 s con 10 semillas sintéticas por tanda. Con datos reales (30-120 semillas, unas 7000 comparaciones
  con 10 000 remuestreos cada una) se estiman unos pocos minutos [I].
- veredicto3 no calcula relanzamientos ni desvíos (están en `cola/estado.json` y en las enmiendas); el `.md` lo dice.
