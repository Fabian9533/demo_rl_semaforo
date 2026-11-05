# veredicto3.py: informe de implementación (PLAN3 5.0; DECISIONES B11, B21 y B22)

05.11.2026. Rama `plan3-ver`, nacida de `plan3-dev` en cff0d61. No se simuló nada y no se abrió ningún resultado
decisivo (todavía no existen): todo se probó con lo entregado de `plan2/` (solo lectura) y con datos sintéticos que usan
las semillas de humo (424301-424360) en `plan3/tmp_ver/` (ignorada por git).

## Respuesta corta

- **Qué hay.** `plan3/veredicto3.py`: ~1960 líneas de código y ~770 de pruebas. Calcula, con las reglas del
  prerregistro (parte A), las etiquetas de cada celda (T1, T2 y citable), el modelo citado, el sentido entre
  entrenamientos, todas las hipótesis de §8 con sus familias y Holm, el número único y las lecturas obligadas.
- **Modos.** `--probar` (108 pruebas, ~30 s), `--final` (se niega sin `listo/cierre.ok` o si un CSV no tiene el
  sha256 del cierre) y `--prueba-final LISTA.json` (§13, una sola vez, con candado).
- **Pruebas: 108 de 108 pasan** (`plan3/pruebas/ver/prueba_veredicto3.txt`). Entre ellas, las del prototipo, cada fila
  de la tabla de etiqueta citable de §7 con datos por semilla, el veto del actuado ajustado, el sentido 4 de 5, Holm
  con 6, las tres lecturas de la no inferioridad, H1 por intersección-unión, una semilla de más (error), la V2 de P6
  (meseta 3.19 %, estabilidad 0.00 %), y que se niega a escribir fuera de `plan3/` y a correr `--final` sin
  `cierre.ok`. Además reproduce desde los CSV por semilla las etiquetas entregadas de P1-P6 (6/6) y de los 12 niveles
  (12/12).
- **28 lecturas de reglas ambiguas**, marcadas `[AMB-n]` en el código (tabla al final). Las que pueden cambiar un
  "pasa" o una etiqueta y conviene fijar con una enmienda antes de abrir datos: AMB-4, 7, 8, 9, 13, 14, 17 y 18.
- **Un error en otra área:** el generador arma mal las rutas de IPPO entregado para su versión evaluada (doble guion
  bajo); el paso `el_p3entmed_*` fallaría. Detalle en "Hallazgos".

## Cómo se corre

Desde `plan3/`:

| Comando | Qué hace | Escribe |
|---|---|---|
| `python veredicto3.py --probar` | Todas las pruebas (sale con 1 si una falla) | `pruebas/ver/prueba_veredicto3.txt`, `pruebas/ver/ejemplo_veredicto3.md` (salida de un mundo sintético) y temporales en `tmp_ver/` |
| `python veredicto3.py --final` | El veredicto, después del cierre | `salidas/veredicto3_celdas.csv`, `_bases.csv`, `_hipotesis.csv`, `_comparaciones.csv` y `veredicto3.md` |
| `python veredicto3.py --prueba-final LISTA.json` | Prueba final reservada (§13) | `listo/holdout.candado` y `salidas/veredicto3_prueba_final.csv` |

`--final` se niega (sale con 1 y no escribe nada) si: falta `listo/cierre.ok`; falta `cola/manifiesto_cierre.json`;
un CSV del manifiesto falta o su sha256 no es el del cierre; el manifiesto de cierre lista otros CSV que el esperado;
o las semillas de un CSV no son las de su tanda en el generador y en la tabla JSON del prerregistro (§3).

## Qué lee y qué escribe

| Lee (relativo a `plan3/`) | Para qué |
|---|---|
| `cola/manifiesto_esperado.json` | Un CSV por (celda, escenario, tanda, brazo) con `tipo`, `base` y semillas. veredicto3 trabaja **por tipo**, nunca por nombre de archivo |
| `cola/trabajos.jsonl` | La política que juega cada CSV (`--politica` de su trabajo) y, con ella, su meta |
| CSV de `evaluar3.py` (`ciego/...`, `parciales/...`) | Una fila por semilla; principal `retraso_total_prom`; secundarias y `generados` |
| `politica_*.json`, `insumos/entregado/politica_*.json` | `val_elegido`, `ep_elegido`, `val_total_serie` (o la serie con que se eligió) |
| `promocion.json` y `promocion/<escenario>.json` | Modelo citado (§12), con su sha256 |
| `insumos/puente/eval_<esc>_*.csv` | Fijo e IPPO entregados en 1001-1030 (puente, descriptivo) |
| `listo/cierre.ok`, `cola/manifiesto_cierre.json` | Solo `--final` |
| `PRERREGISTRO.md` (tabla JSON de §3, vía `protecciones.tabla_prerregistro`) | Semillas de cada uso |
| `../plan2/diag_corredor/resultados.csv` (solo lectura) | Versión evaluada de la V2 del diagnóstico, para mostrar las dos si cambia (§6) |

**Escribe solo dentro de `plan3/`.** Toda escritura pasa por `escribir()`, que resuelve la ruta real y se niega si cae
fuera (`dentro_de_plan3`). El temporal que usa `veredicto.probar()` se redirige a `tmp_ver/tempfile/`. Se pone
`sys.dont_write_bytecode = True` antes de importar, para que importar `veredicto`, `consolidar` y `sintesis_plan` no deje
`__pycache__` en la raíz. Al terminar las pruebas, `git status --porcelain --ignored -- plan2 TESIS` sale vacío (prueba
G01).

**Lo que importa de lo entregado** (al importarse, esos módulos solo definen constantes y funciones; no escriben):
`vd.veredicto`, `vd.texto_veredicto`, `vd.convergencia`, `vd.flotante`, `vd.IGUAL`, `vd.ALFA`; `consolidar.comparar`;
`sintesis_plan.indice_geo`. En las pruebas, además, `vd.probar`, `vd.info_base` y `vd.base_mediana` para comparar. De
`plan3/` importa `generar_trabajos3` (celdas, bases y tandas) y `protecciones` (tabla de semillas); importarlos tampoco
escribe.

## Qué hace cada función

**Reglas (funciones puras).**

| Función | Qué hace | Regla |
|---|---|---|
| `serie_criterio(meta)` | Serie con que se eligió el checkpoint, con el último valor de cada fila (la media de las semillas): `val_total_serie` en todo plan3 y C0 | §6 [AMB-1] |
| `entrenamiento(meta)` | Validación elegida, episodio, convergencia (`vd.convergencia` sobre esa serie), distancia a la mediana de la serie y si el mínimo se repite | §6, §11 [AMB-2, 3, 25] |
| `base_mediana_n(vals)` | Versión evaluada: 3.ª de 5, 2.ª de 3; con número par, la peor de las dos centrales; empate, la base menor | §6, B21 |
| `mejor_base(vals)` | Menor `val_elegido` (empate, la base menor) | §6, A3 |
| `comparar(a, b, esperadas)` | `consolidar.comparar` (cambio %, IC95 bootstrap pareado 10 000 con `default_rng(0)` a 2 decimales, Wilcoxon de dos colas); **ERROR si falta o sobra una semilla** | §7 [AMB-10] |
| `etiqueta(ref, act, convergio, motivo)` | `vd.veredicto` sin cambios, con el veto del actuado ajustado; PENDIENTE con motivo o con la provisional | §7 |
| `acuerdo(e1, e2)` | Etiqueta citable: la tabla de §7 (incluye "mejora/falla no confirmada", CONTRADICTORIO y PENDIENTE) | §7 [AMB-4, 5] |
| `sentido(cambios, n, lado, umbral)` | k de n bases del lado de la afirmación (signo); exige 4 de 5 o 3 de 3 | §7, A5 [AMB-7] |
| `holm(pvals)` | Holm por familia y tanda; una prueba que no se pudo correr entra con p = 1 (la familia conserva su tamaño) | §9 |
| `p_no_inferioridad(a, b)` | Wilcoxon de una cola sobre a − 1.02·b (alternativa "menor") | §8 |
| `lectura_ni(comp, p_aj)` | "no es peor", "es peor" o "no concluyente" | §8 |
| `equivalente(comp)` | IC95 dentro de [−1, +1] % (H4) | §8 |
| `interseccion_union(casos)` | H1 global: cada caso "no es peor" al 5 % (sin Holm) en T1 y T2 | §8, §9 |
| `bootstrap_cambios`, `diferencia_no_pareada` | H6: D = cambio aleatorio − cambio regular; bootstrap independiente en cada tipo de llegadas, pareado dentro; p de una cola = fracción con D ≥ 0 | §8 [AMB-11] |
| `generados`, `generados_iguales` | Mismos vehículos por semilla entre brazos (números aleatorios comunes) | §7 [AMB-14] |
| `igual_ciclo_minimo` | Medias de retraso total y de espera iguales al ciclo mínimo hasta 0.0005 s | §5, §11 [AMB-24] |
| `demanda_esperada` | veh esperados también con `period="exp(λ)"` (la de `veredicto.py` falla) | PLAN3 5.0 |
| `numero_unico(series)` | `sintesis_plan.indice_geo` con `default_rng(0)` | §7 |

**Datos (`class Datos`).** Lee el manifiesto y arma, por celda (celda, escenario), los tipos con sus bases y tandas.
Un brazo es una tupla: referencia (`ref_*`), versión publicada (C0, IPPO entregado, V2 vieja, transferencias), una base,
la versión evaluada entre n bases o la mejor base, o un CSV entregado del puente.

| Método | Qué hace |
|---|---|
| `bases_disenio` | 5 bases si el manifiesto trae 14042 o 16042 (modelo principal, H8a); si no, 3 |
| `meta_base`, `base_version` | Meta de cada base y versión evaluada o mejor base; una base sin meta cuenta como caída (§14) |
| `pub_info` | Versión publicada por `p3_elegir mediana`: **comprueba** que su base es la mediana por `val_elegido` de sus candidatas, leídas de sus propios metas (ERROR si no) |
| `entrada`, `filas_csv`, `serie` | El CSV de un brazo en una tanda; junta tandas físicas (T1x = t1r + h1t1 para H1/H2); ERROR si un CSV tiene una semilla de más o de menos, una repetida o más de un brazo |
| `comp` | Comparación con caché; si los dos brazos no generan los mismos vehículos, queda con su motivo |
| `convergencia` | Convergencia de la versión que juega un brazo [AMB-28] |
| `promocion`, `citado` | Decisión de promoción de la celda (con sha256) y modelo citado: V2 o la variante promovida, que debe ser la versión evaluada de esa variante [AMB-20] |

**Análisis.**

| Función | Qué hace |
|---|---|
| `etiqueta_brazo` | Etiqueta de una tanda frente al fijo fino; veto del actuado ajustado en lo entrenado [AMB-12, 13] |
| `sentido_brazo`, `referencias_al_lado` | Sentido de cada base frente a la referencia; etiqueta frente a cada referencia al lado |
| `fila_celda` | Una fila de `veredicto3_celdas.csv`: citado (T1, T2, citable, cambio, IC, p, borde del IC), "se repite en k de n", mejor base, V2 al lado, ciclo mínimo, probabilidad de PENDIENTE por ruido (§6) y lecturas obligadas (§5, §11) [AMB-6, 16, 22, 23] |
| `tabla_bases` | Todas las bases de todos los brazos, también las candidatas de C0, V2 vieja e IPPO entregado |
| `pruebas_definidas` | H1, H2, H7r, H7, H8a, H8b, H8c, H12, H14, H15, H9 y H10 con sus familias exactas, y las descriptivas (ablación, 2×2, C0 frente a IPPO entregado, puente, C0 aleatorio, transferencias, limpiezas, entropía, reloj sin forzadas, 3b) [AMB-8, 19, 26, 27] |
| `evaluar_pruebas` | Comparación por tanda, Holm por familia y tanda, lectura y sentido [AMB-8, 9] |
| `h_etiqueta`, `h6`, `hipotesis` | H3, H3e, H5, H6, H4, H0, H1 global, resúmenes k de n y H10 al 80 % [AMB-18] |
| `tabla_numero` | Número único por tanda y tipo de llegadas: citado / fijo fino, citado / fijo entregado y, si hay un promovido, V2 / fijo fino [AMB-17] |
| `comparaciones`, `medianas` | Cada brazo frente al fijo fino (con etiqueta), citado y V2 frente a cada referencia, secundarias del citado, retraso por media hora y no insertados por periodo en los corredores, medianas de P6 [AMB-15] |
| `revisar_generados`, `versiones_diag` | Todos los brazos de cada celda y tanda con los mismos vehículos (aviso); V2 del diagnóstico si cambia su versión evaluada |

**Salidas y modos.** `escribir_salidas` (los 4 archivos pedidos más `veredicto3_comparaciones.csv`, el detalle para el
anexo: secundarias, referencias al lado y medianas que no caben en los otros); `texto_md` (respuesta corta con la frase
del número único de §17, tabla del anexo, hipótesis, lecturas obligadas, referencias al lado, promoción, PENDIENTE,
entrenamientos caídos, avisos); `comprobar_cierre`, `comprobar_semillas`, `correr_final`, `correr_prueba_final`.

**Pruebas.** `fabricar` (datos por semilla con números aleatorios comunes), `mundo_sintetico` (una carpeta plan3
completa con el manifiesto y los trabajos reales del generador, semillas de humo, CSV con efectos conocidos, metas,
promoción, puente y cierre) y `probar`.

## Pruebas y resultados (108 de 108 pasan)

**1. Las del prototipo, con lo entregado de `plan2/` (solo lectura).**

| Prueba | Resultado |
|---|---|
| P01 `veredicto.probar()` (la regla no cambió) | pasa |
| P02 V2 de P6, s4042, 8 semillas (serie del diagnóstico): meseta 3.19 %, estabilidad 0.00 %, convergió | pasa |
| P03 con x[3] (lo que hace `info_base`): 9.43 % y "no convergió" | pasa |
| P04 V5 de P6, s42: meseta −4.61 % | pasa |
| P05 metas entregados de IPPO con mensajes: igual a `info_base` | 18/18 |
| P06 V2 del corredor (criterio total): convergencia igual a `analisis.py` | 5/5 |
| P07 `comparar` = resumen de `consolidar` (P1, s4042: −6.7 % [−7.85, −5.67], p = 1.86e-09) | pasa |
| P08 etiqueta de IPPO con mensajes P1-P6 desde los CSV por semilla = robustez entregada | 6/6 |
| P08b etiquetas de los 12 niveles de la entrega 3 (timeLoss) desde los CSV por semilla (PLAN3 5.0) | 12/12 |
| P09 Holm; P10 tabla de acuerdo (textos de §7) | pasan |
| P11-P13 sentido: con 3 bases, 2 de 3 ya no alcanza (A5 pide 3 de 3); 3 de 3 y 4 de 5 cumplen | pasan |
| P14 margen +2 %; P15 demanda con `exp()`; P16 mismos vehículos en P1 (30 semillas) | pasan |
| P17 H6 con datos reales (D −1.85 [−3.16, −0.53]); P18 p de no inferioridad 9.31e-10 | pasan |

P11 cambió frente al prototipo: el prototipo exigía "todas menos una con IC entero del lado"; el prerregistro (A5)
fijó el criterio por signo, 4 de 5 o 3 de 3.

**2. Reglas nuevas con datos por semilla fabricados.**

| Prueba | Resultado |
|---|---|
| N01 `base_mediana_n`: = `vd.base_mediana` con 3 bases (200 casos con empates); 3.ª de 5; peor central con 4; empate | pasan |
| N02 `serie_criterio` toma x[−1] de `val_total_serie` (la media de 16), no x[3] | pasa |
| N03 una semilla de más y una de menos: ERROR | pasan |
| N04 cada fila de la tabla citable de §7 (14 combinaciones, también al revés), PENDIENTE por convergencia y por referencia faltante | 16/16 |
| N05 veto: −8 % frente al fino y pierde contra el actuado ajustado → MEJORA; empata o le gana → FUNCIONA | pasa |
| N06 sentido 4 de 5 con una base en contra pasa, con dos no; una base caída cuenta como fuera del lado | pasan |
| N07 Holm con una familia de 6 (una prueba sin correr cuenta con p = 1) | pasa |
| N08 las tres lecturas de la no inferioridad | pasa |
| N09 H1 por intersección-unión: 6 "no es peor" pasa; uno que no lo es en T2, no | pasa |
| N10 H6 con datos fabricados (D −3.07 [−3.24, −2.89]) | pasa |
| N11 `generados_iguales` y `igual_ciclo_minimo` (0.0004 sí, 0.0011 no) | pasan |
| N12 número único = media geométrica directa | pasa |
| N13 se niega a escribir en la raíz del repositorio y en el temporal del sistema | pasan |
| N14 `--final` exige las semillas del prerregistro | pasa |

**3. Mundo sintético de punta a punta** (`tmp_ver/mundo`, 26 celdas, 1508 CSV: los 1148 del manifiesto real del generador más 360
de las referencias que todavía no genera).

| Prueba | Resultado |
|---|---|
| M01-M04 `--final` se niega sin `cierre.ok`, con un CSV cambiado después del cierre, sin manifiesto de cierre y con semillas que no son las del prerregistro | pasan |
| M05 escribe las 5 salidas | pasa |
| M06 etiqueta citable de V2 en 16 celdas: FUNCIONA, MEJORA, EMPATA (mejora no confirmada), EMPATA (falla no confirmada), CONTRADICTORIO, EMPATA, FALLA, PENDIENTE por convergencia, PENDIENTE por fijo fino faltante y por actuado ajustado faltante | 16/16 |
| M07 D: veto del actuado ajustado y, sin decisión de promoción, el citado queda PENDIENTE con su motivo | pasa |
| M08 P1: variante promovida citada con la etiqueta de V2 al lado | pasa |
| M09-M11 "se repite en 4 de 5", lectura de P6, "Reproduce el ciclo mínimo", probabilidad de PENDIENTE por ruido | pasan |
| M12-M14 H1: global no pasa (P5), P5 "no es peor" en T1 y "es peor" en T2 → no concluyente; T1 = t1r + h1t1 (20 semillas sintéticas) | pasan |
| M15-M23 H2, H3 (4 de 5 pasa), H3e (3 de 5 no), H5 (5 de 6), H6 por caso, H7r (sentido 2 de 3 no pasa), H8a, H8b, H12, H10 sin datos (no se pudo correr, la familia conserva su tamaño), H15 | pasan |
| M24 número único = cálculo directo; con un promovido se agrega el de V2 | pasa |
| M25, M28b números aleatorios comunes rotos en una referencia: la comparación queda con su motivo y hay un aviso | pasan |
| M26-M28c tabla de bases (convergencia de la versión evaluada, candidatas de C0 e IPPO entregado) y `.md` (tabla, lecturas, promoción, frase de §17) | pasan |
| M29 versión publicada que no es la mediana: ERROR; M30 CSV con una semilla de más: ERROR; M31 promoción con otro sha256: ERROR | pasan |
| M32-M35 prueba final: sin `holdout.ok` o con otro sha256 se niega; corre una vez y no dos; solo semillas reservadas, y una lista mal armada no cierra el candado | pasan |
| G01 `git status --porcelain --ignored -- plan2 TESIS` vacío después de las pruebas | pasa |

## Ambigüedades del prerregistro y lectura implementada

Ninguna se eligió en silencio: cada una lleva `[AMB-n]` en el código. "¿Cambia algo?" dice si la lectura puede
mover una etiqueta, un "pasa" o una cifra citable.

| AMB | Regla | Lectura implementada (la más literal) | Alternativa | ¿Cambia algo? |
|---|---|---|---|---|
| 1 | §6: convergencia sobre `val_total_serie`, x[−1] | Así en todo plan3 y C0. Lo que se eligió con otra serie usa la suya: `p3_elegir regla` → `serie_eleccion`; lo entregado y el exploratorio (criterio timeLoss) → `val_serie` | Exigir `val_total_serie` siempre | Solo la convergencia de V2 vieja, 200 con piso, 400 entre 20 e IPPO entregado (descriptivos y H0) |
| 2 | §6, §11: "distancia entre la validación elegida y la mediana de la serie" | En s y en % de la mediana de **toda** la serie | Solo el último tercio; solo % | No (descriptiva) |
| 3 | "si el mínimo se repite en dos validaciones seguidas" | Literal: el valor mínimo aparece en dos validaciones seguidas (con la precisión del meta). Al lado: "las dos mejores validaciones son seguidas" | Con una tolerancia (p. ej. 0.5 %) | No (descriptiva). Con valores continuos la literal casi siempre dice "no" |
| 4 | §7, tabla citable | Simétrica: T1 y T2 son réplicas (solo la fila FUNCIONA/MEJORA dice "o al revés") | Solo el orden escrito | Sí: sin simetría, T1 EMPATA y T2 MEJORA no tendría fila |
| 5 | PENDIENTE en la citable | "PENDIENTE (no convergió; provisional: acuerdo de las provisionales)" | Solo "PENDIENTE" | No |
| 6 | "se repite en k de n" | Lado de la etiqueta de cada tanda: sobre cero si es FALLA; si no, bajo cero | Siempre bajo cero | Solo la columna y la lectura "el método no se repite" |
| 7 | §14: base caída "fuera del sentido" | Cuenta como fuera del lado y el mínimo no baja (4 de 5; 3 de 3) | Excluirla y pedir n − 1 de las que quedan | Sí, si cae una base |
| 8 | ¿Una no inferioridad es "afirmación de método"? | H8c, H12 y H10 llevan sentido (cambio por base bajo +2 %); H1 no (su fila no lo pide y no hay C0 por base fuera de P4 y m6525) | Ninguna no inferioridad con sentido, o todas | Sí, en H8c, H12 y H10 |
| 9 | Lectura de una no inferioridad en las dos tandas | "no es peor" si las dos; "es peor" si las dos; si no, "no concluyente" | Informar solo por tanda | La frase de H1, H8c, H12 y H10 |
| 10 | §7-§8: p de Wilcoxon | El de `consolidar.comparar` (3 cifras significativas, como lo entregado), también para Holm; los p de una cola, sin redondear | Sin redondear en todo | Solo en el borde de 0.05 |
| 11 | H6: generadores del bootstrap | `default_rng(1)` (aleatorias) y `default_rng(2)` (regulares), los del prototipo | Otros | El IC de D en el segundo decimal |
| 12 | Etiqueta de una referencia (H0) | Solo frente al fijo fino, sin veto, como las filas de referencia de lo entregado | Con veto | Solo H0 (descriptiva) |
| 13 | Falta el actuado ajustado | PENDIENTE ("falta actuado ajustado"), como lo entregado sin el actuado | Etiqueta sin veto | Sí, si esa referencia no llega a una celda |
| 14 | §7: "se comprueba" que todos los brazos generan los mismos vehículos | La comparación que falla queda PENDIENTE con su motivo y se avisa | Solo avisar | Sí, si ocurre (`manifiesto.py cierre` ya lo impide) |
| 15 | §4: "P6 y P6e con llegadas aleatorias" | P6e es regular por definición: se calcula en P6 con llegadas aleatorias (que ya tiene la entrada corregida) | — | No |
| 16 | Lectura del fijo de verdes de 5 en 5: §5 ("iguala o supera") y §11 ("gana el fino y empata el de 5 en 5") | La frase de §11 si se cumple su condición; si no, la de §5 cuando el de 5 en 5 iguala o supera. Franja, bloques y regla con la condición de §11 | Una sola de las dos | El texto obligado |
| 17 | Número único | Exige los seis casos (si falta uno, PENDIENTE); usa los datos aunque la etiqueta sea PENDIENTE por convergencia; "la de V2" = V2 frente al fijo fino | Omitir casos PENDIENTE | Sí, la cifra citable |
| 18 | Hipótesis por caso sin regla global (H2, H7r, H7, H8a, H8c, H9, H12, H14, H15) | Caso por caso y "pasa en k de n"; regla global solo donde §8 la da (H1, H5, H8b, H10) | "Pasa" si pasan todos | La frase resumen |
| 19 | H10: nombre del brazo y niveles | Tipo `p3red` (B5); corredor = P1, P2, c905, c1358, c2715; red = P3, P4 y r*; malla = P5, P6 y m* | — | Hoy H10 sale "no se pudo correr" |
| 20 | §12: cómo se lee la promoción | Clave de `promocion.json` = escenario de la celda; `modelo_citado` = `ippo_<variante>_<etiqueta>med_s<base>`, y esa base debe ser la versión evaluada de la variante | — | Interfaz a fijar con quien escriba los trabajos de promoción |
| 21 | H1 y H2 con 120 semillas | V2 = el CSV de la base mediana (entre 42, 2042 y 4042) en t1r + `v2reg3med` en h1t1 (mismo checkpoint; se comprueba la base) | — | No |
| 22 | "La etiqueta con la mejor base" | Con la convergencia de esa base; con una variante citada, su mejor base (y la de V2 al lado) | Sin convergencia | Solo esa columna |
| 23 | Cuadro 2×2 y su lectura obligada | Con las tandas de 30 semillas | Con las de 120 donde existen | Solo la lectura |
| 24 | "Igual al ciclo mínimo" hasta 0.0005 s | Medias redondeadas a 4 decimales, como el resumen de `consolidar` que usaba lo entregado | Sin redondear | Solo en el borde |
| 25 | Convergencia de las metas de `p3_elegir regla` | Episodios = el último de la serie con que eligió (200 con piso: 200) | El del entrenamiento (400) | No (descriptiva) |
| 26 | Puente: "IPPO entregado" | Su versión evaluada (mediana del 25.09) de `insumos/puente` | Las tres bases | No (descriptivo) |
| 27 | C0 con llegadas aleatorias | Frente a la V2 regular de 5 bases (la única V2 regular jugada con llegadas aleatorias) | Frente a la de 3 bases | No (descriptivo) |
| 28 | PENDIENTE de una versión jugada en otra celda | Lleva la convergencia de su propio entrenamiento (la V2 regular jugada con llegadas aleatorias, IPPO entregado) | Sin convergencia | Solo H0 y las transferencias (descriptivas) |

## Hallazgos y pendientes de otras áreas

1. **Error en `generar_trabajos3.py`** (función `mediana`, IPPO entregado): con etiqueta vacía arma
   `insumos/entregado/politica_<esc>_vecinos__s42.pt` (doble guion bajo); el archivo real es
   `politica_<esc>_vecinos_s42.pt`. `p3_elegir.py mediana` no encontraría el meta y el paso `el_p3entmed_<esc>` fallaría
   en las 18 celdas. El mundo sintético lo corrige para probar veredicto3; el generador no se tocó.
2. **Tipos que veredicto3 espera y el generador aún no produce:** `ref_fino` (decide), `ref_actuadoaj` (veto),
   `ref_fino5`, `ref_franja`, `ref_bloques`, `ref_regla`, `ref_mp`, `ref_mpc`; `p3red` (H10). Mientras falten, cada celda
   queda PENDIENTE con su motivo y H10 "no se pudo correr". Un `ref_*` nuevo (p. ej. "fijo desde 10 s" de los niveles)
   entra solo como referencia al lado.
3. **Sin tipo definido todavía:** la sensibilidad a3 (colas en cero, mensajes cortados), el perfil y la mezcla. Hoy
   saldrían como brazos descriptivos frente al fijo fino; la celda de perfil o mezcla toma como modelo principal
   `p3per` o `p3mix` si existen. Falta fijar sus tipos en el generador.
4. **Promoción:** veredicto3 busca la decisión por el escenario de la celda (`corredor`, `poi_corredor`, ...). Los
   trabajos que llamen a `p3_promocion.py decidir` deberían usar `--celda <escenario>`.
5. **Prueba final:** el formato de la lista de §13 que acepta `--prueba-final` es
   `{"comparaciones": [{"celda", "escenario", "tanda", "a": {"tipo", "base"}, "b": {"tipo", "base"}}]}`; sus CSV deben
   estar en el manifiesto con semillas del bloque `final`. Es una propuesta: la fija la enmienda que la active.

## Límites

- Nada de esto vio datos reales: las etiquetas del mundo sintético salen de efectos fabricados. Lo que sí está probado
  con datos reales es que las reglas reproducen lo entregado (P01-P18).
- Duración: ~30 s con 10 semillas sintéticas por tanda. Con datos reales (30-120 semillas, ~7000 comparaciones con
  10 000 remuestreos cada una) se estiman unos pocos minutos [I].
- veredicto3 no calcula relanzamientos ni desvíos (están en `cola/estado.json` y en las enmiendas); el `.md` lo dice.
