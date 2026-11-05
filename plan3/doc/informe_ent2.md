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
3. **Pruebas: todo OK** [M] (sección 3). Los E2 no cambian la simulación; la observación cercana cuesta ×1.28 en
   2715 y ×1.34 en P6, dentro del ×1.35 del generador; la marca de giro se activa en el 11.4 % del verde de C2_C1
   en 2715 (`bloqueo.md`: 12 %); el reloj de 2 s da verdes de 10, 12, 14... s con la misma recompensa por segundo; y
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
  - `var_explicada` se calcula en la escala del retorno.
- **`--sin-forzadas`**: una decisión forzada no cierra la pendiente; su recompensa sigue sumando a la decisión libre
  anterior. Con el reloj de 5 s, un cambio dura 13 s (ámbar más verde mínimo) y un cambio forzado a los 60 s, 18 s.
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
  valor sigue siendo el criterio (`elegir_checkpoint`, `veredicto3`); `eval_999_final` pasa a ser la media del primer
  nivel.
- **Costo**: niveles × semillas episodios por validación (3 × 8 = 24 cada 20 episodios).

### 2.5 Colas en cero (a3)

- `configurar_colas_cero(True)` deja en cero, al jugar, **todas las entradas que cuentan vehículos detenidos**:
  - `cola_o..cola_s`;
  - las colas que mandan los vecinos (`<lado>_cola_alimentadora`, `<lado>_cola_mi_salida`);
  - con `--obs-cercana`, también `cerca_det_*` y `salida_ocup_*`.
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
**todo OK** [M].

| # | Prueba | Resultado [M] | Salida |
|---|---|---|---|
| 1 | Todo apagado = tag: IPPO y V2; con estado y registro; ablación; y `--paso-decision 5` puesto a mano | OK, 56 comprobaciones: CSV igual byte a byte salvo `segundos`, checkpoints y política (byte a byte) y meta iguales, log de consola igual; `--paso-decision 5` da la V2 del tag | `prueba_identidad.txt` |
| 2 | `--obs-cercana 75` no cambia la simulación: la misma política juega igual con y sin los E2, en 2715 (V2 del diagnóstico) y en P6 (IPPO entregado) | OK: todas las métricas y los 2724 y 8700 viajes iguales; dimensión 31 → 49 y 53 → 73 | `prueba_etapa3.txt` |
| 3 | La espera del primero leída solo con alguien en la zona = leída en todos los carriles | OK: 0 distintas en 133 872 lecturas (2715 y P6) | `prueba_etapa3.txt` |
| 4 | Costo por episodio ≤ ×1.35 (mediana de 3 parejas sin/con alternadas en un proceso) | OK: 2715 ×1.28 (1.26-1.31); P6 ×1.34 (1.30-1.34) | `prueba_etapa3.txt` |
| 5 | Marca `giro_izq` en 2715 (V2 del diagnóstico, base 42), periodo 2, 20 semillas: % de los segundos de verde del acceso, la medida de `bloqueo.md` | OK: C2_C1 11.4 % (`bloqueo.md` 12 %; por semilla 7.2-16.2 %); W_C1 17.4 % (14 %); S2_C2 3.8 % (5 %); 0 en el periodo 1. Contada por decisiones, C2_C1 da 10.1 % | `prueba_etapa3.txt` |
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
   marca, en el periodo 2. El prototipo la comparó con la fracción de decisiones (2 semillas). Con 20 semillas, por
   segundos da 11.4 % en C2_C1, dentro del 11-13 % pedido; por decisiones daría 10.1 %, fuera. La variación entre
   semillas es grande (7.2-16.2 %).

**Límites y pendientes:**

7. **Costo de la observación cercana:** en la batería final, ×1.26-1.31 en 2715 y ×1.30-1.34 en P6 (medianas ×1.28
   y ×1.34), con la medición alternada en un proceso. Una corrida anterior del mismo código dio ×1.11-1.39 en P6
   (mediana ×1.20): la razón depende de la carga de la máquina. En dos procesos que compiten, una con y otra sin,
   llega a ×1.47 por puro ruido.
   - El factor del generador (`OBS = 1.35`) alcanza en las medianas, pero en P6 sin margen.
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
    Sin `--sin-forzadas`, las decisiones forzadas de los 2, 4, 6 y 8 s entran al lote (`frac_forzadas` ~0.65).
12. **`ent_coef`** se escribe con todos sus decimales (p. ej. `0.002999999999999999`, que es 0.003 en coma flotante).
