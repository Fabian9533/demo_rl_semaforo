# Informe ent-2: Etapas 3 y 4 en `rl_ippo.py` y colas en cero (PLAN3 3.1-3.4, Etapa 4 y a3)

05.11.2026. Rama `plan3-ent` (worktree `w3_ent`), después de fusionar `plan3-dev` (2adbaf8) y sobre la revisión de
robustez (`informe_ent1.md` §7, commit 24ebb66). Decisiones que aplica:
B14 (observación cercana), B16 (política por red), B24 (reloj de 2 s) y B25 (modelo completo). Primera parte:
`informe_ent1.md` (opciones de entrenamiento, estado y reanudación).

**Marcas.** [M] medido (archivo de salida de una prueba); [I] inferido; [S] supuesto.

## Respuesta corta

1. **Qué se hizo.**
   - `rl_ippo.py` tiene las opciones de la Etapa 3, con los nombres que ya usa el generador:
     - `--obs-cercana L`;
     - `--norm-valor` (con `--norm-beta B`);
     - `--sin-forzadas` y `--msg-cada-paso`;
     - `--ent-final X`, para el calendario de entropía;
     - `--paso-decision K`.
   - Tiene también las de la Etapa 4: `--escala-demanda a,b`, `--curriculo K` y `--val-escalas e1,e2,e3`.
   - Funciones nuevas:
     - `rl_ippo.configurar_colas_cero(True)`, para la sensibilidad a3, que `evaluar3.py` ya llama;
     - `rl_ippo.archivo_e2(esc, L)`, para que `p3_preparar.py` escriba antes el archivo de los E2;
     - `rl_ippo.configurar_desde_meta(meta)`, para que `evaluar.brazo_profundo` juegue cada política con las opciones
       de su meta. En `evaluar.py` el cambio son 4 líneas dentro de `brazo_profundo`.
2. **Con todo apagado no cambia nada** [M]. El CSV es igual byte a byte salvo `segundos`; los checkpoints, la
   política publicada y su meta, y el log de consola son los del tag. Vale para IPPO entregado, para V2 y para
   `--paso-decision 5`.
3. **Pruebas** [M] (secciones 3 y 5): todo OK, salvo el tope de costo en P6 en una de las dos baterías. Los E2
   no cambian la simulación; la observación cercana cuesta ×1.28 en
   2715 y en P6 ×1.34 de mediana (×1.20-1.40 según la carga de la máquina), justo en el ×1.35 del generador; la marca de giro en C2_C1 (2715) da 11.4 % de los segundos de
   verde (7.2-16.2 % por semilla) y 10.1 % de las decisiones (6.6-13.6 %): coherente con el 12 % de `bloqueo.md`
   dentro de la variación entre semillas; el reloj de 2 s da verdes de 10, 12, 14... s con la misma recompensa por segundo; y
   la reanudación sigue exacta con todas las opciones nuevas.
4. **Lo que hay que saber para usarlo** (detalle en la sección 2):
   - `--sin-forzadas` exige el descuento por segundo de V2, y `--paso-decision K` con K ≠ 5 también. Sin él, un
     intervalo de 2 o de 13 s se descontaría como uno de 5.
   - Para validar por niveles se propone **`--val-escalas e1,e2,e3`**, junto con las `--val-seeds` y el
     `--eval-cada` de siempre:
     - cada semilla corre en cada nivel, con `--scale e`;
     - `val` y `val_total` pasan a ser la media geométrica de las medias de los niveles;
     - con esa media se elige el checkpoint.
   - Todo lo nuevo queda, si está activo, en tres lugares: en `meta["opciones"]`, en la configuración que compara
     `--reanudar` y en el estado. El estado guarda además el calendario de entropía, las medias de `--norm-valor` y
     el generador de la escala, como claves nuevas: la versión sigue en 1 y un estado de antes se lee igual.
   - Las opciones nuevas se revisan en `validar_args` (revisión de robustez, `informe_ent1.md` §7): los 403 comandos
     de `rl_ippo` del generador, los 175 de la Etapa 3 incluidos, pasan sin correrlos [M, `prueba_comandos`].

## 1. Opciones

| Opción | Qué hace | Dónde queda |
|---|---|---|
| `--obs-cercana L` | 16 + lados entradas al final de la observación (sección 2.1). Dimensión 31 → 49; 53 → 73 en la malla | meta `opciones.obs_cercana`, `dim_obs`, `features`; config |
| `--norm-valor` | El crítico aprende el retorno normalizado con medias móviles (ValueNorm). Los valores que entran a GAE se desnormalizan | meta `norm_valor`, `norm_beta`; config; estado (`norm_valor`: beta, m1, m2, peso); CSV `vn_media`, `vn_desv` |
| `--norm-beta B` | β de esas medias (por defecto 0.99999). Para la política por red se fija con un piloto y una enmienda (B16) | meta y config |
| `--sin-forzadas` | Las decisiones con una sola acción legal se aplican, pero no entran al lote ni cierran la decisión pendiente. Exige el descuento de V2 | meta, config; CSV `frac_forzadas` (con `--registro-extendido`) |
| `--msg-cada-paso` | Los mensajes se publican cada segundo, antes de las decisiones: al decidir, el del segundo actual | meta (evaluar lo usa), config; CSV `msg_edad` |
| `--ent-final X` | Entropía lineal de `HIPER["ent"]` a X en el horizonte de la tasa (en su último episodio vale X), constante después | meta, config; estado (`ent`, por episodio); CSV `ent_coef` |
| `--paso-decision K` | Reloj de decisión y de mensajes (sección 2.2). Si K ≠ 5, exige el descuento de V2 | meta (evaluar lo usa), config |
| `--escala-demanda a,b` | Cada episodio sortea f ~ U(a, tope) y corre sumo con `--scale f` | meta, config; estado (generador); CSV `escala` |
| `--curriculo K` | El tope sube de a a b en K episodios (0: b desde el principio) | meta, config |
| `--val-escalas e1,...` | Validación en varios niveles de demanda; elige por la media geométrica (sección 2.4) | meta, config; CSV `val_x<e>`, `val_total_x<e>`; checkpoints y series |

Las columnas nuevas del CSV salen solo con su opción y con `--registro-extendido`, que el generador pone siempre.
Las opciones de la tabla solo cambian el entrenamiento (salvo `--obs-cercana`, `--paso-decision` y
`--msg-cada-paso`, que también cambian cómo juega la política) y van todas a la configuración que compara
`--reanudar`.

**Líneas de comando** (las del generador, que agrega a cada una `--v2` y las opciones de siempre):

```
--obs-cercana 75                                              # p3obs, p3obspoi
--norm-valor | --sin-forzadas | --msg-cada-paso               # p3m7norm, p3m7forz, p3m7msg (y las tres: p3m7)
--hiper ent=0.03 --ent-final 0.003                            # p3ent
--paso-decision 2 --sin-forzadas                              # p3reloj2, p3reloj2poi
--obs-cercana 75 --norm-valor --sin-forzadas --msg-cada-paso --lr-horizonte 200 --lr-piso 0.1 --paso-decision 2
                                                              # p3completo, p3completopoi (--episodios 400)
```

Para la política por red (Etapa 4; no está en el generador) se propone, con la base de cada red y la demanda de B16:

| Red (escenario base) | Demanda base [M, suma de los flujos] | `--escala-demanda` | `--val-escalas` [S] |
|---|---|---|---|
| Corredor (`corredor`, P1) | 1810 veh/h | `0.5,2.0` (905-3620) | `0.5,1,1.5` (905, 1810, 2715) |
| Red (`red`, P3) | 2150 veh/h | `0.421,1.684` (905-3620) | `0.421,1,1.684` |
| Malla (`malla3`, P5) | 4350 veh/h | `0.416,2.0` (1810-8700) | `0.416,1,2` |

más `--curriculo 200 --episodios 600 --eval-cada 20 --val-seeds 999,1999,2999,3999,4999,7999,8999,9999` y
`--norm-valor --norm-beta <del piloto>`. Qué tres niveles validan es una decisión abierta: B16 dice "3 niveles" y no
cuáles. Aquí se propone el extremo bajo, la base y un nivel alto. En el corredor coinciden con niveles evaluados,
salvo que `--scale 1.5` difiere de `dem_corredor_t2715` en unos 8 vehículos de borde (prototipo).

## 2. Diseño

### 2.1 Observación cercana (`--obs-cercana L`)

- **Entradas**, al final de la observación (las de siempre no se mueven):
  - por acceso (o, e, n, s):
    - `cerca_det` y `cerca_mov`: detenidos y en movimiento a menos de L m de la línea, divididos por
      carriles × L/7.5, con tope 1;
    - `espera_cab`: espera del primero de cada carril, la mayor, dividida por 120 s, con tope 1;
    - `giro_izq`: 1 si hay alguien detenido en el primer tramo interno del giro a la izquierda de algún carril (el que
      gira espera el hueco dentro del cruce, como en `bloqueo.py`);
  - por lado con vecino, `salida_ocup`: detenidos del carril más cargado del enlace de **salida** i→j, sobre las
    plazas. Es una ranura nueva: la vieja `cola_mi_salida` mide en realidad el que entra (hallazgo 5 de `CLAUDE.md`)
    y no se toca.
- **Lecturas**:
  - detectores E2 suscritos (vehículos y detenidos) y el tramo interno del giro suscrito (detenidos);
  - al decidir, 2 llamadas por carril: los ids del carril y la espera del último de la lista, que es el más cercano a
    la línea;
  - la salida real se lee de `MedidorEnlaces`, que ya se lee cada paso.
- **Archivo de los E2**: `e2_<esc>_<L>.add.xml` en la carpeta actual.
  - Lo escribe `rl_ippo.archivo_e2(escenario, L, carpeta=".")`: si falta o es otro, en un temporal con el pid (varios
    procesos pueden escribirlo a la vez), lo baja a disco y lo reemplaza con reintentos. Si ya está igual, no lo toca.
  - El entrenamiento y `evaluar.py` lo generan si falta; `p3_preparar.py` puede escribirlo antes con esa función.
  - En la línea de sumo, `--additional-files` lleva los adicionales del `.sumocfg` (el programa del escenario) **y**
    los E2: esa opción reemplaza la lista del `.sumocfg`.
- **Geometría**: carriles, largos y tramos internos del giro se leen de la red una vez por proceso. El prototipo la
  releía en cada episodio de evaluación, lo que es lento en la malla.

### 2.2 Reloj de decisión (`--paso-decision K`, B24)

- Con K = 5 rige el reloj de siempre, sin tocar: cada 5 s del verde propio (la primera a los 5 s, que es forzada si el
  mínimo es 10) y todos en el segundo 0.
- Con otro K se decide:
  - cada K s mientras el verde no llega al mínimo (decisiones forzadas, que `--sin-forzadas` deja fuera del lote);
  - cada K s desde el mínimo;
  - una vez al llegar al verde máximo (60 s), para que se respete aunque no caiga en la rejilla.
  - Con K = 2 y mínimo de 10 s, los verdes duran 10, 12, 14... s.
- **Se sigue la redacción de H14**: con 2 s, las decisiones de los 2, 4, 6 y 8 s del verde mínimo existen y son
  forzadas ("4 de cada 5 decisiones del verde mínimo serían forzadas"). B24 dice "decide cada 2 s una vez cumplido el
  verde mínimo"; los verdes y el lote son los mismos con `--sin-forzadas`, pero no se saltan esas decisiones: así
  el flujo de números de la exploración común de V2 queda como lo mide H14.
- **K ≠ 5 exige `--sin-forzadas`** (y el descuento de V2): `validar_args` rechaza el reloj de 2 s sin ella, porque
  esas decisiones forzadas llenarían el lote (`frac_forzadas` ~0.65). Los trabajos del generador (`p3reloj2`,
  `p3completo`) ya las llevan juntas.
- Los mensajes se publican cada K s de reloj global (cada segundo con `--msg-cada-paso`). La recompensa que se reporta
  "a reloj fijo" sigue cada 5 s.
- **La recompensa y el descuento de V2 siguen en unidades de 5 s**: r = suma por segundo / 5 y γ^(dt/5), con
  `PASO_CONTROL`. Por eso un intervalo de 2 s pesa 2/5 de uno de 5, y la recompensa por segundo no depende del
  reloj (prueba 8).
- **El arranque del episodio y la cuenta de cambios de fase no cambian en ningún modo** (con cualquier reloj y
  cualquier opción de las Etapas 3 y 4): `setPhase(verdes[0])` en cada semáforo, `fase_previa` leída después con
  `fases_actuales()` (todavía la fase de la plantilla) y, en cada segundo, la cuenta de "entró a un verde nuevo".
  Las líneas son las del tag, y los tres `setPhase` (arranque, ámbar y verde siguiente) son los mismos. Así, la
  resta de k por plantilla que hace `veredicto3` en `cambios_fase` vale igual para todos los brazos de `rl_ippo`.
  Con el decisor "mantener", los relojes de 5 y de 2 s dan los mismos 131 cambios (prueba 8).

### 2.3 Limpiezas de PPO (`--norm-valor`, `--sin-forzadas`, `--msg-cada-paso`) y entropía

- **`--norm-valor`**:
  - los valores que guarda el episodio, y el del cierre, se desnormalizan para GAE;
  - después de GAE, las medias toman los retornos del lote y el crítico aprende el retorno normalizado con ellas;
  - el actor no cambia;
  - `var_explicada` se calcula en la escala del retorno;
  - **`perdida_valor` queda en unidades normalizadas**: es el error cuadrático del crítico frente a
    (retorno − media)/desv, no en las de la recompensa. No se compara con una corrida sin la opción; `var_explicada`
    sí;
  - cada checkpoint y la política publicada guardan la escala del crítico: `vn_media`, `vn_desv` y `vn_estado`
    (β, m1, m2, peso). La publicada lleva la del checkpoint elegido.
- **Frente al ValueNorm de MAPPO** (Yu et al. 2022, código `onpolicy`; lo de MAPPO, de memoria del código [S]):
  - igual: medias móviles de los retornos con corrección de sesgo, varianza con piso 1e-2, β por defecto 0.99999,
    valores desnormalizados para GAE y objetivo del crítico normalizado;
  - distinto: MAPPO actualiza las medias en cada minilote de cada época; aquí, una vez por episodio con todo el
    lote, antes de actualizar. Con β = 0.99999 y la corrección de sesgo, las dos dan casi el promedio de todos los
    retornos vistos [I];
  - no hay PopArt: los pesos de la última capa del crítico no se reescalan cuando cambian las medias;
  - la pérdida del crítico es la de siempre (cuadrática, sin recorte de valor); MAPPO usa Huber y recorte.
- **`--sin-forzadas`**: una decisión forzada no cierra la pendiente; su recompensa sigue sumando a la decisión libre
  anterior. Con el reloj de 5 s, un cambio dura 13 s (ámbar más verde mínimo) y un cambio forzado a los 60 s, 18 s.
  - **Al truncar** (6000 s sin que la red se vacíe), la decisión libre pendiente se cierra con V(observación final)
    descontado por su intervalo real. Ese instante puede caer dentro del verde mínimo, un estado que el crítico no
    ve en el lote con `--sin-forzadas`: el valor es una extrapolación. Afecta a una transición por semáforo y solo en
    los episodios truncados; si la red se vacía, el valor final es 0, como siempre [I].
  - Si un episodio no deja ninguna transición en el lote, no se actualiza la política: las columnas de la
    actualización quedan vacías y el log lo avisa (revisión del 05.11).
- **`--msg-cada-paso`**: los mensajes se publican cada segundo antes de las decisiones: edad 0 al decidir (con
  `--latencia L` al jugar, L).
- **`--ent-final`**: el coeficiente de cada episodio se guarda en el estado y se compara al reanudar, como la tasa.

### 2.4 Política por red: escala por episodio y validación por niveles (B16)

- **Escala por episodio** (`--escala-demanda a,b`):
  - f ~ U(a, tope) con un generador propio (`default_rng(base + 15485863)`), un sorteo por episodio;
  - tope = b, o a + (b − a)·min(1, ep/K) con `--curriculo K`;
  - f se redondea a 4 decimales y va a sumo como `--scale f`; la columna `escala` lo registra;
  - el estado guarda el generador.
- **Validación por niveles** (`--val-escalas e1,e2,...`): cada semilla de `--val-seeds` corre en cada nivel con
  `--scale e`. Claves, en la fila del CSV y en el `.json` de cada checkpoint:
  - `val_<s>_x<e>` y `val_total_<s>_x<e>`, por semilla y nivel (solo en el `.json`);
  - `val_x<e>` y `val_total_x<e>`: media de las semillas de ese nivel, con 3 decimales;
  - `val` y `val_total`: media geométrica de los niveles, con 3 decimales. No depende de la escala de cada nivel: un
    nivel alto con retrasos de 500 s no tapa a uno bajo con 25 s.
- **Series**: `val_serie` y `val_total_serie` tienen por fila `[ep, nivel 1, ..., nivel n, geométrica]`. El último
  valor sigue siendo el criterio (`elegir_checkpoint`, `veredicto3`).
- **`eval_timeloss`, `eval_espera` y `eval_999_final`** (revisión del 05.11): con niveles, son los de la primera
  semilla en el nivel 1 (la demanda del escenario), o vacíos si no se valida en el nivel 1. El meta publicado lo
  dice en `eval_nivel` (1.0 o null). Antes eran los del primer nivel, una demanda distinta en cada red.
- **Reglas** (`validar_args`): factores entre 0.1 y 4; niveles sin repetir (tampoco `1` y `1.0`); `--val-escalas`
  solo con validación (`--eval-cada` > 0 y `--val-seeds`). De la Etapa 3, solo `--norm-valor` va con la escala (B16).
- **Costo**: niveles × semillas episodios por validación (3 × 8 = 24 cada 20 episodios).

### 2.5 Colas en cero (a3)

- `configurar_colas_cero(True)` deja en cero, al jugar, **todas las entradas que cuentan vehículos detenidos**: las
  de `nombres_features()` que empiezan con `cola_`, `cerca_det_` o `salida_ocup_`, o terminan en
  `_cola_alimentadora` o `_cola_mi_salida`. La lista exacta [M, `nombres_features()`]:
  - corredor y red (dos lados), 8 de 31: `cola_o`, `cola_e`, `cola_n`, `cola_s`, `oeste_cola_alimentadora`,
    `oeste_cola_mi_salida`, `este_cola_alimentadora`, `este_cola_mi_salida`;
  - con `--obs-cercana`, 14 de 49: las 8 y `cerca_det_o`, `cerca_det_e`, `cerca_det_n`, `cerca_det_s`,
    `salida_ocup_oeste`, `salida_ocup_este`;
  - malla (cuatro lados), 12 de 53: las 8 y `norte_cola_alimentadora`, `norte_cola_mi_salida`,
    `sur_cola_alimentadora`, `sur_cola_mi_salida`;
  - malla con `--obs-cercana`, 20 de 73: las 12, `cerca_det_o..s` y `salida_ocup_oeste`, `_este`, `_norte`, `_sur`.
- No toca lo que se mueve (`movil_*`, `cerca_mov_*`), la espera del primero, la marca del giro, las fases, los
  tiempos ni la espera para entrar (`pend_*`).
- La lista sale de los nombres de `nombres_features()`, así que sirve para cualquier dimensión.
- El interruptor vive fuera de `C`, porque `preparar()` vacía `C` y `evaluar3.py` lo activa antes de armar el brazo.
- No encontré el guion del a3 original. Su cuadro de magnitudes agrupaba `cola_local(0-3)`, `vec_cola_alimentadora` y
  `vec_cola_mi_salida`, que aquí van las tres. Si el a3 de 2026-09 anulaba solo las locales, las cifras no son
  comparables una a una [I].

### 2.6 Reanudación con las opciones nuevas

- La configuración que compara `--reanudar` suma las opciones activas de las Etapas 3 y 4 (`opciones_etapas`, el
  mismo diccionario que va al meta). Un estado sin esas claves vale para una corrida con ellas apagadas.
- El estado suma tres claves; la versión sigue en 1, como pidió la revisión de robustez:
  - `ent`, el coeficiente por episodio, que se compara bit a bit;
  - `norm_valor`;
  - `generadores.escala`.
- Un estado de antes, sin esas claves, se lee igual (con `.get`): vale para una corrida con esas opciones apagadas.
- Con etiqueta nueva, los `.json` de los checkpoints copiados llevan el meta nuevo más todo lo que va desde
  `ep_checkpoint` en el `.json` de origen, y los `tramos` de esta corrida (`informe_ent1.md` §7). Antes se rearmaban
  desde las series, y eso no alcanzaba con niveles.
- Lo de la revisión de robustez vale igual con las opciones nuevas: escrituras por temporal con fsync, estados
  dañados a `.roto`, CSV tomado, B22 en `rehechos.json` y procedencia por tramos.

## 3. Pruebas

Guiones nuevos en `plan3/pruebas/ent/`: `prueba_etapa3.py`, `prueba_etapa4.py` y `trabajo_e3.py`. Este último corre
cada medición en un proceso aparte e importa `rl_ippo.py`. Los de la primera parte se ampliaron:
`prueba_identidad.py` suma `--paso-decision 5` y `prueba_reanudar.py` suma los modos `e3` y `e4`. Salidas en
`plan3/pruebas/ent/salidas/` y corridas en `plan3/tmp_ent/`. Semillas: base 7 y 424301-424320 (humo).

**La batería corrió sobre el commit 5824084** (las Etapas 3 y 4 encima de la revisión de robustez). Resultado:
**todo OK** [M]. **Se volvió a correr entera sobre 201ec69** (los arreglos de la sección 5): todo OK salvo una
comprobación, el costo de la observación cercana en P6, que esa vez dio ×1.40 de mediana (punto 7 de la sección 4).

| # | Prueba | Resultado [M] | Salida |
|---|---|---|---|
| 1 | Todo apagado = tag: IPPO y V2; con estado y registro; ablación; y `--paso-decision 5` puesto a mano | OK, 56 comprobaciones: CSV igual byte a byte salvo `segundos`, checkpoints y política (byte a byte) y meta iguales, log de consola igual; `--paso-decision 5` da la V2 del tag | `prueba_identidad.txt` |
| 2 | `--obs-cercana 75` no cambia la simulación: la misma política juega igual con y sin los E2, en 2715 (V2 del diagnóstico) y en P6 (IPPO entregado) | OK: todas las métricas y los 2724 y 8700 viajes iguales; dimensión 31 → 49 y 53 → 73 | `prueba_etapa3.txt` |
| 3 | La espera del primero leída solo con alguien en la zona = leída en todos los carriles | OK: 0 distintas en 133 872 lecturas (2715 y P6) | `prueba_etapa3.txt` |
| 4 | Costo por episodio ≤ ×1.35 (mediana de 3 parejas sin/con alternadas en un proceso) | 2715: OK, ×1.28 y ×1.26 en las dos baterías. P6: OK en 5824084 (×1.34; 1.30-1.34), **FALLA en 201ec69** (×1.40; 1.37-1.47). Una medición aparte con 5 parejas dio ×1.34 (1.30-1.44) | `prueba_etapa3.txt`, `costo_p6.txt` |
| 5 | Marca `giro_izq` en 2715 (V2 del diagnóstico, base 42), periodo 2, 20 semillas: % de los segundos de verde del acceso, la medida de `bloqueo.md` | OK, coherente con `bloqueo.md` dentro de la variación entre semillas. Segundos de verde (por semilla) y decisiones (por semilla) frente a `bloqueo.md`: C2_C1 11.4 % (7.2-16.2) y 10.1 % (6.6-13.6) frente a 12 %; W_C1 17.4 % (10.2-32.6) y 18.0 % (13.2-29.5) frente a 14 %; S2_C2 3.8 % (0.4-6.2) y 5.0 % (1.9-9.6) frente a 5 %. En el periodo 1, 0 |  `prueba_etapa3.txt` |
| 6 | `--sin-forzadas`: intervalos del lote | OK: 5 y 13 s con el reloj de 5; 2 y 13 s con el de 2 (salvo el cierre) | `prueba_etapa3.txt` |
| 7 | `--paso-decision 2`: duración de los verdes | OK: 10, 12, 14... s (con 5: 10, 15, 20... s) | `prueba_etapa3.txt` |
| 8 | Recompensa por segundo con los dos relojes (decisor "mantener", misma simulación) | OK: −180 441.503 con los dos (1578 y 3946 decisiones) = `ret_retraso` | `prueba_etapa3.txt` |
| 9 | Colas en cero, con las mismas decisiones | OK: 14 entradas en cero y las demás iguales | `prueba_etapa3.txt` |
| 10 | Entrenamiento corto con todas las opciones de la Etapa 3 | OK: `msg_edad` 0.0 (sin `--msg-cada-paso`, 1.95-2.06 s); `ent_coef` de 0.03 a 0.003; columnas `vn_*`; `frac_forzadas` 0.61-0.67; `evaluar.py` juega la política de dimensión 49 igual que su validación, semilla por semilla; `evaluar3.py --colas-cero` la juega | `prueba_etapa3.txt` |
| 11 | Etapa 4: `--scale` frente a los escenarios de demanda; escala por episodio con currículo; validación por niveles | OK: `--scale 0.5` = `dem_corredor_t905` (mismas métricas y los 906 viajes); `--scale 1.5` da ×1.501 vehículos; la columna `escala` sigue el sorteo con el tope del currículo (0.79, 0.99, 1.18, 1.89) y los vehículos la siguen (±2 %); en el CSV y en cada checkpoint, cada nivel es la media de sus semillas y `val_total` la media geométrica de los niveles; la serie elige el ep 2 por esa media; `vn_*` presentes | `prueba_etapa4.txt` |
| 12 | Reanudación exacta, 20 = 10 + 10, con las opciones de la Etapa 3 juntas (`e3`: `--obs-cercana 75 --norm-valor --paso-decision 2 --sin-forzadas --msg-cada-paso --hiper ent=0.03 --ent-final 0.003`) y con las de la Etapa 4 (`e4`) | OK con los dos: el corte no publica; reanudado, CSV igual, checkpoints con tensores y `.json` iguales, política igual byte a byte, meta igual, y estados iguales (pesos, Adam, los generadores —también el de la escala—, `ent`, `norm_valor`, series y CSV); los `tramos` son 1-20 frente a 1-10 y 11-20, con la misma huella | `prueba_reanudar_corredor_e3_e4.txt` |
| 13 | No regresión de la primera parte y de la robustez | OK: reanudación en P1 (IPPO y V2, etiqueta nueva y 10 rechazos; 57 comprobaciones), caídas con `taskkill`, robustez R1-R7, prueba 5 (base 42 frente al diagnóstico: 12/12 tensores) e identidad de `chequeos_previos` (`[]`) | `prueba_reanudar_corredor.txt`, `prueba_caida.txt`, `prueba_robustez.txt`, `prueba_diag.txt`, `chequeos_identidad.txt` |
| 14 | Los 403 comandos de `rl_ippo` del generador frente a `validar_args` | OK: pasan todos, los 175 de la Etapa 3 incluidos | `prueba_comandos.txt` |

## 4. Pendiente o dudoso

**Decisiones mías para revisar:**

1. **`--sin-forzadas` y `--paso-decision K ≠ 5` exigen el descuento por segundo de V2** (`--v2` o
   `--solo-descuento`). Si no, salen con error. El generador siempre los usa con `--v2`.
2. **La espera del primero se lee solo si hay alguien a menos de L m** (si no, vale 0). Así se ahorra un tercio de
   las llamadas en P6.
   - Medido: 0 diferencias en 133 872 lecturas frente a leer todos los carriles.
   - Gatillar con "el E2 ve detenidos" ahorraría más (70 % de las lecturas en P6), pero cambia el valor en el 0.2 % de
     ellas (hasta 23 s de espera que el E2 no ve). No lo hice.
3. **Colas en cero = todas las entradas de vehículos detenidos**, también las que mandan los vecinos (sección 2.5).
   El guion del a3 original no está.
4. **Validación por niveles:** el nombre `--val-escalas` y la media geométrica de las medias de cada nivel, redondeadas
   a 3 decimales.
5. **Columnas nuevas** (`escala`, `vn_media`, `vn_desv`, `val_x<e>`, `val_total_x<e>`): solo con su opción y con
   `--registro-extendido`. Es la regla de la primera parte.
6. **La marca de giro se valida con la medida de `bloqueo.md`**: el % de los segundos de verde del acceso con la
   marca, en el periodo 2. El prototipo la comparó con la fracción de decisiones (2 semillas). Con 20 semillas, en
   C2_C1, por segundos da 11.4 % (7.2-16.2 % por semilla) y por decisiones 10.1 % (6.6-13.6 %); `bloqueo.md` da 12 %.
   Las dos medidas son coherentes con `bloqueo.md` dentro de la variación entre semillas; por segundos cae además en
   el 11-13 % pedido.

**Límites y pendientes:**

7. **Costo de la observación cercana:** en 2715, ×1.26-1.31 (medianas ×1.28 y ×1.26). En P6 depende de la carga
   de la máquina: cuatro mediciones alternadas en un proceso dieron medianas ×1.20, ×1.34, ×1.40 y ×1.34, con
   parejas de ×1.11 a ×1.47 [M, `prueba_etapa3.txt` y `costo_p6.txt`]. En dos procesos que compiten, una con y otra
   sin, llega a ×1.47 por puro ruido.
   - **El factor del generador (`OBS = 1.35`) queda justo en P6**: la mediana de las cuatro es ×1.34. Si se quiere
     margen para los tramos de 5 h, ×1.45 cubre todas las parejas medidas. No lo cambié: es del generador.
   - Al entrenar, la razón es menor: la actualización de PPO no cambia (el prototipo midió +22-29 % en D).
8. **Los tres niveles de validación y β de la política por red no están fijados.** B16 pide "3 niveles" y un β fijado
   con un piloto; aquí hay una propuesta de niveles por red (sección 1). El piloto de β (base 7, 20 episodios) no se
   corrió.
9. **La política por red no está en el generador:** los nombres y las líneas de comando de la sección 1 son la
   propuesta.
10. **Evaluación de la política por red:** se evalúa con los escenarios `dem_*`, no con `--scale`. En el corredor,
   `--scale 0.5` es exactamente `dem_corredor_t905` [M]; `--scale 1.5` y `dem_corredor_t2715` difieren en ~8
   vehículos (prototipo).
11. **El reloj de 2 s con verde mínimo de 5 s** (fases de giro, que el corredor no tiene) decide a los 5, 7, 9... s.
    Desde la revisión del 05.11, el reloj de 2 s sin `--sin-forzadas` se rechaza: las decisiones forzadas de los 2,
    4, 6 y 8 s ya no pueden entrar al lote.
12. **`ent_coef`** se escribe con todos sus decimales (p. ej. `0.002999999999999999`, que es 0.003 en coma flotante).

## 5. Revisión del 05.11 (segunda): arreglos y comprobaciones

Una revisión adversarial de 786c5fe confirmó 29 hallazgos, ninguno alto. Los arreglos están en el commit 201ec69,
encima de `plan3-dev` 5b2a32d. Con todo apagado nada cambia: la identidad con el tag sigue exacta [M].

**Código** (en `rl_ippo.py`, `evaluar.py` y `plan3/revalidar_c0.py`):

| # | Hallazgo | Qué hace ahora |
|---|---|---|
| 1 | `evaluar.py` en su modo antiguo (`--ippo`) y `revalidar_c0.py validar` jugaban las políticas sin sus opciones de la Etapa 3 | Las dos llaman a `configurar_desde_meta(meta)` antes y a `configurar_desde_meta({})` después, como `brazo_profundo`; también el MAPPO guardado como `Politica`. El brazo DQN, que juega con su propia observación, sale con error si el meta trae una opción que actúa (`opciones_que_actuan`). En `revalidar_c0` la dimensión se compara después de configurar |
| 2 | El reloj de 2 s sin `--sin-forzadas` llenaba el lote de decisiones forzadas | `validar_args` lo rechaza. Las decisiones de antes del mínimo siguen existiendo (H14 y el flujo de V2 no cambian) |
| 3 | Combinaciones sin sentido o que ningún trabajo usa | `validar_args` rechaza: niveles repetidos (también `1` y `1.0`); `--val-escalas` sin validación; factores fuera de 0.1-4; `--obs-cercana` con `--obs-insercion`; opciones de la Etapa 3 con `--variante local`; opciones de la Etapa 3 con la escala de la Etapa 4, salvo `--norm-valor` (B16 la pide). El generador no usa ninguna de esas combinaciones: sus 403 comandos pasan |
| 4 | `demo` jugaba con las opciones del meta sin decir nada | Avisa si la línea de comandos pedía otra observación, otro reloj u otros mensajes |
| 5 | Con niveles, `eval_*` venían del primer nivel | Vienen del nivel 1 (la demanda del escenario), o quedan vacíos; el meta lo dice en `eval_nivel` |
| 6 | La escala del crítico con `--norm-valor` no quedaba en los meta | `vn_media`, `vn_desv` y `vn_estado` en cada checkpoint y, del elegido, en la política publicada |
| 7 | Un episodio sin transiciones rompía la actualización | No se actualiza: columnas vacías y AVISO; `NormValor.actualizar` se niega con un lote vacío |
| 8 | `prueba_identidad.py` leía el CSV de evaluar aunque evaluar hubiera fallado, y una excepción dejaba la prueba sin salida | Salta la lectura si evaluar falla; `util_ent.proteger` anota cualquier excepción como FALLA y escribe la salida igual |

En las reglas de entrenamiento (puntos 2 y 3, y las de antes que exigen el descuento de V2), `demo` no se rechaza:
ahí mandan las opciones del meta y se avisa.

**Comprobaciones** (todas sobre 201ec69, con semillas de humo: base 7 y 424301-424304, y 999 y 1999 en la corrida
larga):

| Pedido | Qué se corrió | Resultado [M] | Salida |
|---|---|---|---|
| a | Modelo completo en su forma real, 20 = 10 + 10 (las opciones de e3 sin `--hiper ent` ni `--ent-final`, con `--lr-horizonte 10 --lr-piso 0.1`), en P6 (`malla3_alta`) y P4 (`red_alta`) | OK en los dos (16 comprobaciones cada uno): CSV igual, checkpoints, política byte a byte, meta y estados (Adam con 14 010 pasos en P6); `tramos` 1-10 y 11-20 | `prueba_reanudar_malla3_alta_e3c.txt`, `prueba_reanudar_red_alta_e3c.txt` |
| b | Reanudar con cada opción de las Etapas 3 y 4 quitada o cambiada (10 de e3 y 8 de e4) | OK, 18 de 18: salen con 1 ("el estado es de otra configuracion", con la clave que cambia) o, sin `--sin-forzadas` con el reloj de 2 s, con 2 (argparse), y ningún archivo de la corrida cambia (lo único que se escribe son las entradas `e2_corredor_75.add.xml` y `e2_corredor_50.add.xml`, los detectores que `configurar_obs_cercana` crea si faltan, antes de comparar el estado). La reanudación 20 = 10 + 10 con e3 y e4 sigue exacta (50 comprobaciones en total) | `prueba_reanudar_corredor_e3_e4.txt` |
| c | `evaluar3.py --regla regla_u2g60` (corredor) y `--regla mp_c90` (malla3_alta), 424301-424302, con el árbol de a9ba36b y el de hoy | OK: los dos CSV iguales byte a byte en los dos casos | `prueba_revision_e34.txt` (D) |
| d | Variantes entregadas frente al tag: `--obs-insercion`, `--recompensa-insercion`, `--variante spill` y `cambio`; un episodio de `rl_mappo`; `evaluar.py --latencia 5` | OK: CSV igual salvo `segundos`, checkpoints, política byte a byte y meta en las cuatro; MAPPO con actor y crítico iguales; el CSV de evaluar igual byte a byte | `prueba_revision_e34.txt` (E) |
| e | Observación cercana recalculada aparte con `verif_e3.py` (el guion del revisor R2), red_alta, K = 5 y K = 2 | OK: 0 diferencias en 1887 y 4551 lecturas; sin problemas de reloj, máscara, recompensa ni GAE. La marca de giro no se activó en red_alta con esta política nueva (0 en los dos relojes; el cálculo aparte también da 0) | `prueba_revision_e34.txt` (F) |
| f | Política de forma p3obspoi (2 episodios en poi_corredor) por `../con_escenarios.py evaluar3.py`: sola, con `--colas-cero` y con `--perdida 1` | OK: las tres salen con 0; sola da su validación (69.14 y 102.07 s) | `prueba_revision_e34.txt` (G) |
| g | Ocho procesos crean a la vez `e2_corredor_75.add.xml` | OK: los ocho salen con 0, el archivo es igual al de un proceso solo y no quedan temporales | `prueba_revision_e34.txt` (H) |
| h | Corrida larga del modelo completo en D (`dem_corredor_t2715_der`), base 7, 400 episodios, validación cada 10 en 999 y 1999, con las opciones de `OP_COMPLETO` (código de 5b2a32d, congelado aparte al empezar) | OK: ni NaN ni inf en el CSV, en los 40 checkpoints ni en el estado final; ningún lote vacío. `var_explicada` estable, 0.77-0.79 por bloque de 50 episodios; `vn_media` −5.4 → −3.9 y `vn_desv` 3.6 → 1.5, cada vez más quietas; entropía 0.26 → 0.08 y KL ~0.001 desde el episodio 150; `perdida_valor` (normalizada) 0.005 → 0.017, porque `vn_desv` baja. Validación (retraso total) 222 s en el ep 10 y 25-27 s desde el 20; publica el 170 (25.38 s). 8.4 s por episodio de entrenamiento (p90 10.3 s); 67 min en total | `largo_completo_d.txt` |
| 1-8 | Los arreglos de código | OK: evaluar en modo antiguo, `revalidar_c0` y `demo` dan la validación de una política de la Etapa 3 semilla por semilla; el lote vacío no actualiza; las reglas nuevas de `validar_args`; `eval_nivel` y la escala del crítico en los meta (`prueba_etapa4`) | `prueba_revision_e34.txt` (A, B, C), `prueba_etapa4.txt` |
| — | No regresión | OK: identidad con el tag (56 comprobaciones, también `--paso-decision 5`), reanudación en P1 (IPPO y V2, etiqueta nueva y 10 rechazos; 57), caídas con `taskkill` (40), robustez R1-R7 (79), prueba 5 frente al diagnóstico (4), Etapa 4 (17), comandos del generador (los 403) e identidad de `chequeos_previos` (`[]`). Etapa 3: 26 OK y 1 FALLA, el tope de costo en P6 (×1.40; sección 4, punto 7) | las de `plan3/pruebas/ent/salidas/` |

**Decisiones mías en esta revisión** (ninguna cambia lo entregado):

1. La corrida larga (h) empezó antes de los arreglos, con el código de 5b2a32d copiado aparte. Los arreglos no
   cambian un episodio que deja transiciones, así que sus números valen para 201ec69; su meta no trae `vn_*`.
2. `--norm-valor` sí va con la escala de la Etapa 4: B16 la pide para la política por red. Las demás opciones de la
   Etapa 3 se rechazan con la escala.
3. Con `--variante local` se rechazan todas las opciones de la Etapa 3, también `--norm-valor` y `--ent-final`.
4. Con niveles, `eval_999_final` es la primera semilla en el nivel 1 del último checkpoint, como `val_999` sin
   niveles; no la media del nivel.
5. Las reglas de entrenamiento no rechazan `demo` (sección 5, arriba): ahí se avisa.
6. En (b), "ningún archivo cambia" excluye los detectores `e2_*.add.xml`, que son entradas y se crean al configurar.
7. El costo de P6 falló el tope de ×1.35 en una batería (×1.40). No cambié el tope ni el factor del generador: queda
   anotado en la sección 4, punto 7, con la propuesta de ×1.45.
