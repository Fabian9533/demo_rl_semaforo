# Informe ent-1: opciones nuevas de `rl_ippo.py`, estado y reanudación (PLAN3 1.1 y 1.2)

05.11.2026. Rama `plan3-ent` (worktree `w3_ent`), nacida de `plan3-dev` en 223f908. Decisiones que aplica:
DECISIONES B13 (código en el lugar, todo apagado por defecto), B15 (estado aparte y reanudación) y B22 (caídas y
relanzamientos); prerregistro §3 (semillas), §6 (versión evaluada) y §14 (caídas).

**Marcas.** [M] medido (archivo de salida de una prueba); [I] inferido; [S] supuesto.

## Respuesta corta

1. **Qué se hizo.** `rl_ippo.py` tiene ocho opciones nuevas, todas apagadas por defecto:
   - ablación de V2: `--solo-descuento` y `--solo-exploracion`;
   - tasa: `--lr-horizonte N` y `--lr-piso F`;
   - registro: `--registro-extendido`;
   - estado y tramos: `--guardar-estado`, `--hasta-ep K` y `--reanudar ESTADO|auto`.
2. **Con todo apagado no cambia nada** [M]: el CSV es el del tag byte a byte salvo la columna `segundos` (tiempo de
   reloj), y los checkpoints, la política publicada (byte a byte) y su meta son iguales. Igual con IPPO entregado y
   con V2. Hasta el log de la consola es el mismo.
3. **La reanudación es exacta** [M]: 20 episodios seguidos dan lo mismo que 10 + 10 reanudados (CSV, tensores, estado
   de Adam, generadores, política y meta), en P1 y en P6. Matar el proceso con `taskkill /F` a mitad de un tramo y
   relanzar el mismo comando termina igual que la corrida seguida, con la misma etiqueta (`--reanudar auto`) y con
   una etiqueta nueva. Reanudar con otra etiqueta y más episodios da lo mismo que una corrida seguida con esa
   etiqueta y esa tasa.
4. **Lo demás que pedía la tarea también se cumple** [M]: la V2 del corredor (base 42) repite en el episodio 10 los
   tensores de la V2 del diagnóstico, aunque valide con otras semillas; y 400 episodios con horizonte 200 y piso 0.1
   repiten los episodios 1-181 de una corrida de 200.
5. **Lo que hay que saber para usarlo** (detalle en la sección 2):
   - los tramos de un trabajo son el mismo comando con `--reanudar auto`, cambiando solo `--hasta-ep`; relanzar una
     caída es relanzar el mismo comando;
   - `--episodios` es siempre el total: la tasa depende de él y una reanudación con otra tasa se rechaza;
   - una etiqueta nueva exige la ruta del estado de origen (`auto` solo mira su propia etiqueta). Con esa ruta, los
     tramos también son un mismo comando: el primero copia; los siguientes, y cualquier relanzamiento, siguen desde
     los estados propios que salen de ese mismo origen, sin volver a copiar ni borrar.
6. **Revisión de robustez del 05.11** (sección 7) [M]. Arregla seis fallas raras que encontró una revisión escéptica,
   sin cambiar ningún número ni los bytes de checkpoints y política:
   - un estado dañado ya no bloquea los relanzamientos: se aparta a `.roto` y `auto` sigue desde el anterior;
   - estados, checkpoints, copias y política se escriben por temporal con fsync, y la política publica primero el
     `.json` y al final el `.pt`;
   - un CSV abierto en Excel ya no tumba el tramo;
   - un episodio rehecho que no repite queda en `checkpoints/<tag>_rehechos.json` y en el meta;
   - el estado anota qué código escribió cada tramo;
   - `validar_args` revisa un comando sin correrlo.

## 1. Opciones

Todas son de `train`; `demo` no cambia. Ejemplos con `cwd = plan3/`, como la cola.

| Opción | Qué hace | Qué cambia en las salidas |
|---|---|---|
| `--solo-descuento` | Solo el descuento por segundo de V2 (GAE con γ^(dt/5)); exploración independiente | meta: `opciones.solo_descuento`, `descuento` |
| `--solo-exploracion` | Solo la exploración común de V2; descuento por decisión | meta: `opciones.solo_exploracion`, `exploracion` |
| las dos juntas | Exactamente `--v2` | nada: mismo entrenamiento y mismo meta que `--v2` |
| `--lr-horizonte N` | lr = 1e-3 × max(F, 1 − (ep − 1)/N); por defecto N = `--episodios` | meta: `opciones.lr_horizonte` si N ≠ `--episodios` |
| `--lr-piso F` | Piso de la tasa, fracción del lr inicial; por defecto 0 | meta: `opciones.lr_piso` si F > 0 |
| `--registro-extendido` | Columnas al final del CSV (sección 3) | solo el CSV |
| `--guardar-estado` | `checkpoints/<tag>_epNNN.estado.pt` en cada checkpoint, en el corte y en el último episodio | nada más: ni el CSV, ni los checkpoints, ni la política, ni el meta |
| `--hasta-ep K` | Corta después del episodio K: guarda el estado y sale con 0 sin publicar | no publica hasta llegar a `--episodios` |
| `--reanudar ESTADO` | Sigue exacto desde un estado (misma etiqueta o nueva) | etiqueta nueva: `reanudado_de` en los meta |
| `--reanudar auto` | Sigue desde el estado más avanzado de su propia etiqueta; sin estados, empieza de cero | — |

Reglas: `--v2` con una `--solo-*` es un error; `--hasta-ep` y `--reanudar auto` exigen `--guardar-estado`;
`--hasta-ep` va de 1 a `--episodios`; `--lr-horizonte` ≥ 1; `--lr-piso` en [0, 1).

**Líneas de comando** de los usos del plan, con P6 (`malla3_alta`), P4 (`red_alta`) y la base 42 de ejemplo, y las
16 semillas de validación del prerregistro §3:

```
VAL=999,1999,2999,3999,4999,7999,8999,9999,15001,15002,15003,15004,15005,15006,15007,15008

# 1.3 V2 regular en dos tramos: el mismo comando, el ultimo sin --hasta-ep (relanzar una caida = el mismo comando)
python ../rl_ippo.py train --escenario malla3_alta --seed 42 --episodios 200 --eval-cada 10 --val-seeds $VAL --v2 --criterio-val total --etiqueta p3v2reg --guardar-estado --registro-extendido --reanudar auto --hasta-ep 100
python ../rl_ippo.py train --escenario malla3_alta --seed 42 --episodios 200 --eval-cada 10 --val-seeds $VAL --v2 --criterio-val total --etiqueta p3v2reg --guardar-estado --registro-extendido --reanudar auto

# 1.5 ablacion de V2
python ../rl_ippo.py train --escenario red_alta --seed 42 --episodios 200 --eval-cada 10 --val-seeds $VAL --solo-descuento --criterio-val total --etiqueta p3abldesc --guardar-estado --registro-extendido --reanudar auto
python ../rl_ippo.py train --escenario red_alta --seed 42 --episodios 200 --eval-cada 10 --val-seeds $VAL --solo-exploracion --criterio-val total --etiqueta p3ablexpl --guardar-estado --registro-extendido --reanudar auto

# 3b: 400 episodios desde el ep 180 de la V2 de 200, en dos tramos con la ruta del estado de origen
python ../rl_ippo.py train --escenario malla3_alta --seed 42 --episodios 400 --lr-horizonte 200 --lr-piso 0.1 --eval-cada 10 --val-seeds $VAL --v2 --criterio-val total --etiqueta p3e400 --guardar-estado --registro-extendido --reanudar checkpoints/malla3_alta_ippo_vecinos_p3v2reg_s42_ep180.estado.pt --hasta-ep 300
python ../rl_ippo.py train --escenario malla3_alta --seed 42 --episodios 400 --lr-horizonte 200 --lr-piso 0.1 --eval-cada 10 --val-seeds $VAL --v2 --criterio-val total --etiqueta p3e400 --guardar-estado --registro-extendido --reanudar checkpoints/malla3_alta_ippo_vecinos_p3v2reg_s42_ep180.estado.pt
```

En 3b, los tramos después del primero también pueden llevar `--reanudar auto` en vez de la ruta: dan lo mismo,
porque la etiqueta nueva ya tiene estados propios. Con la ruta, el comando es uno solo para todos los tramos y
relanzamientos. Las líneas exactas de las pruebas están en cada guion de `plan3/pruebas/ent/` y en sus salidas.

## 2. Contrato de `--guardar-estado`, `--hasta-ep` y `--reanudar`

### 2.1 Nombres

Todo es relativo a la carpeta actual (`plan3/` en la cola):

- `tag = <esc>_ippo_<variante>[_<etiqueta>]_s<base>` (el de siempre);
- CSV: `resultados_<tag>.csv` (o `--csv`);
- checkpoints: `checkpoints/<tag>_epNNN.pt` y `.json`, en cada validación (como siempre);
- estado: `checkpoints/<tag>_epNNN.estado.pt`;
- temporales mientras se escribe (sección 7): `<tag>_epNNN.tmp`, `.json.tmp` y `.estado.tmp`. El de un `.pt` cambia
  la extensión en vez de agregarla: `torch.save` guarda dentro del zip el nombre del archivo sin su última extensión,
  y así el `.pt` sale con los mismos bytes que con un `torch.save` directo;
- estado apartado por dañado: `checkpoints/<tag>_epNNN.estado.pt.roto` (`.roto2`, ... si se repite). No se borra;
- `checkpoints/<tag>_rehechos.json`: solo si un episodio rehecho no repite el intento anterior (B22, sección 7);
- política publicada: `politica_<esc>_<variante>[_<etiqueta>]_s<base>.pt` y `.json` (como siempre).

### 2.2 Qué guarda el estado

Se escribe al final del episodio NNN, **después** del checkpoint y de la fila del CSV, en un temporal que se baja a
disco (fsync) y se renombra; los checkpoints también, antes de anotar su sha256. Por eso, si el estado existe, está
entero y todo lo ≤ NNN está completo. Se lee con `torch.load(weights_only=True)`: solo trae tensores y tipos simples.

| Clave | Contenido |
|---|---|
| `politica`, `opt` | pesos y estado de Adam (con su contador de pasos, `exp_avg`, `exp_avg_sq` y grupos) |
| `generadores` | `random`, numpy global, torch (CPU) y el `default_rng` de `sembrar` (el que baraja los minilotes) |
| `val_serie`, `val_total_serie` | las series de validación hasta NNN (las que elige la publicación) |
| `csv` | el texto exacto del CSV hasta NNN (cabecera y filas) |
| `lr` | la tasa usada en cada episodio 1..NNN |
| `archivos` | sha256 de cada checkpoint (`.pt` y `.json`) de la etiqueta hasta NNN |
| `config` | lo que debe coincidir para seguir (2.4) |
| `origen` | `[{"corrida": tag, "episodio": k}]` si la corrida viene de otra etiqueta |
| `codigo`, `tramos` | huella del código que escribió el estado y `[{desde, hasta, git, codigo}]`: qué código escribió cada episodio (sección 7) |
| `reanudaciones` | B22: `[{partida, episodios, filas, distintos}]`, una por relanzamiento que rehízo episodios (sección 7) |
| `fase_av`, `tag`, `etiqueta`, `episodio`, `episodios`, `eval_cada`, `ruta_csv`, `git`, `torch`, `python`, `version` | lo demás |

`codigo`, `tramos` y `reanudaciones` llegaron con la revisión del 05.11 y se leen con `.get`: un estado sin ellas sigue
valiendo (la versión sigue siendo 1).

Pesa ~185 KB (P1) más ~0.4 KB por fila del CSV [M]: unos 4.5 MB por corrida de 200 episodios con validación cada 10 y
~11 MB por una de 400 [I]. La política `.pt` no cambia.

### 2.3 Qué lee, borra y escribe cada caso

| Caso | Lee | Borra | Escribe | Sale con |
|---|---|---|---|---|
| Sin `--reanudar` (o `auto` sin estados) | escenario | `checkpoints/<tag>_ep*` (`.pt`, `.json`, `.estado.pt` y temporales; no los `.roto`) | CSV desde cero; checkpoints y estados; al final, la política | 0 |
| `--hasta-ep K` (K < `--episodios`) | — | — | lo mismo hasta K y el estado de K; **no** publica | 0 |
| `--reanudar RUTA`, misma etiqueta | el estado; los checkpoints ≤ k que anota (verifica su sha256); el CSV actual (filas > k) | `checkpoints/<tag>_ep*` con NNN > k | CSV = filas ≤ k del estado + las nuevas; checkpoints y estados > k; al final, la política | 0 |
| `--reanudar RUTA`, etiqueta nueva (primera vez) | el estado; los checkpoints ≤ k y los estados ≤ k de la etiqueta de origen, en la carpeta del estado (verifica sha256) | todo `checkpoints/<nuevo>_ep*` | copia los `.pt` ≤ k byte a byte, reescribe sus `.json` con el meta nuevo, copia los estados ≤ k; CSV con las filas ≤ k del estado y la etiqueta nueva; sigue | 0 |
| `--reanudar RUTA`, etiqueta nueva que ya tiene estados propios que salen de ese mismo estado (un intento o tramo anterior) | el estado propio de mayor NNN | como `auto` | como `auto` | 0 |
| `--reanudar auto` con estados | el de mayor NNN de **su** etiqueta que sirva (2.4); uno que no sirve se renombra a `.roto` con un AVISO y se prueba el anterior | como misma etiqueta | como misma etiqueta | 0 |
| `--reanudar RUTA` con un estado que no sirve (2.4) | el estado | nada | nada | 1, con el motivo (no se aparta: lo eligió quien lanza) |
| El CSV está tomado por otro programa al empezar el tramo | lo de su caso | lo de su caso | lo de su caso, con el CSV en memoria; al final lo escribe entero (el último tramo espera hasta 30 min antes de publicar) | 0 (1 con "Permission denied" si al final sigue tomado: la cola lo reintenta) |
| Misma etiqueta (o `auto`), k = `--hasta-ep` | el estado | nada | nada ("Nada que hacer") | 0 |
| `auto` (o etiqueta nueva ya empezada), k > `--hasta-ep`: un tramo posterior ya corrió | el estado | nada | nada ("Nada que hacer") | 0 |
| RUTA de la misma etiqueta, k > `--hasta-ep` | el estado | nada | nada | 1 (se pidió seguir desde más allá del corte) |
| Misma etiqueta (o `auto`), k = `--episodios` y ya publicada | el estado, el CSV y la política | nada | nada ("Nada que hacer") | 0 |
| k = `--episodios` sin publicar (se cayó al publicar) | el estado | como misma etiqueta | el CSV (igual) y la política | 0 |
| Algo no coincide (2.4) | el estado | nada | nada | 1, con el motivo |
| Opciones incompatibles | — | nada | nada | 2 (argparse) |

"Ya publicada" quiere decir: el CSV en disco es el del estado final, el `.json` publicado trae las mismas series y el
`.pt` publicado es, byte a byte, el checkpoint que elige el `--criterio-val` de esta llamada.

Detalles:

- **Misma etiqueta** = el `tag` guardado en el estado es el de esta corrida. Si la ruta apunta a otra carpeta (un
  respaldo), copia de ahí los checkpoints y estados ≤ k.
- **Etiqueta nueva**: el meta de los checkpoints > k y el de la política publicada llevan
  `"reanudado_de": [{"corrida": "<tag de origen>", "episodio": k}]`. Los `.json` de los checkpoints copiados se
  reescriben como los habría escrito una corrida seguida con la etiqueta nueva (meta nuevo más la validación de ese
  checkpoint, sacada de las series). Las filas ≤ k del CSV pasan con la columna `etiqueta` nueva; las demás columnas,
  tal cual. Los estados copiados guardan dentro el `tag` de origen.
- **Comprobación de B22**: al reanudar, las filas > k que haya en el CSV de esta corrida (las de un intento caído) se
  comparan con las que se rehacen, salvo `segundos`, en cuanto sale cada una. El log dice "Reanudacion: los episodios
  a-b repiten el intento anterior" o "AVISO: el episodio n no repite...". Si alguno no repite, además queda en
  `checkpoints/<tag>_rehechos.json` (lo muestra el resumen de `p3_noche`). Cada relanzamiento que rehízo episodios
  queda en `reanudaciones` del estado y del meta publicado (sección 7). El código de salida no cambia.
- La política se publica solo al llegar a `--episodios`, como siempre: el checkpoint de menor validación de toda la
  serie (la copiada y la nueva).

### 2.4 Qué se comprueba antes de tocar ningún archivo

1. **Que el estado sirva** (`estado_valido`): el zip está sano (`testzip` revisa el CRC de cada pieza; `torch.load`
   no lo hace), carga, es de la versión 1, el NNN del nombre es el episodio guardado y cada checkpoint que anota (en
   su carpeta) tiene su sha256. Con `auto`, uno que no sirve se aparta a `.roto` y se prueba el anterior; con una
   ruta, sale con 1. Las copias de un origen dentro de una etiqueta nueva no se juzgan por sus checkpoints (llevan el
   nombre del origen y pueden estar en su carpeta); si se usan, el punto 5 los verifica.
2. **Misma configuración**: escenario, variante, base, `dim_obs`, `HIPER` (con `--hiper`), descuento y exploración
   de V2, `--recompensa-insercion`, `--obs-insercion` y `--val-seeds`. No cuentan los que solo cambian nombres,
   cortes, validaciones o la elección final: `--episodios`, `--eval-cada`, `--etiqueta`, `--criterio-val`, `--csv`,
   `--hasta-ep`, `--guardar-estado` y `--registro-extendido`.
3. **Misma tasa, bit a bit, en cada episodio 1..k** (la del estado frente a la que daría esta corrida). Así se
   rechaza un tramo con otro `--episodios` (cambiaría la tasa desde el episodio 2) y se acepta el 400 con horizonte
   200 y piso 0.1 desde el 180 de una de 200.
4. k ≤ `--episodios`.
5. El sha256 de cada checkpoint ≤ k que anota el estado.
6. Que las columnas del CSV del estado quepan en las de esta corrida (mismas `--val-seeds` y mismo
   `--registro-extendido`). Si esta corrida agrega columnas, quedan vacías en las filas copiadas, con un aviso.

### 2.5 Para el generador de trabajos

- **Tramos de ≤ 5 h**: el mismo comando con `--guardar-estado --reanudar auto`, cambiando solo `--hasta-ep`
  (el último, sin `--hasta-ep`). Cada tramo depende del anterior.
- **Relanzar una caída** (B22): el mismo comando. Sigue desde el último estado escrito; si el tramo ya estaba hecho,
  sale con 0 sin tocar nada.
- **Salidas esperadas** (para marcar un trabajo como hecho):
  - tramo con `--hasta-ep K`: `checkpoints/<tag>_epKKK.estado.pt` y el CSV con las filas 1..K;
  - último tramo: la política (`.pt` y `.json`), `checkpoints/<tag>_epNNN.estado.pt` con NNN = `--episodios` y el
    CSV con las filas 1..NNN.
- **Etiqueta nueva** (3b, "400 desde el 180"): todos los tramos con la misma ruta del estado de origen, cambiando
  solo `--hasta-ep`. El primero copia; los demás, y cualquier relanzamiento, siguen desde el estado propio más
  avanzado **que salga de ese mismo origen** (lo dice su `origen`). `auto` también sirve desde el segundo tramo, pero
  no en el primero: `auto` solo mira la etiqueta propia y, sin estados, empezaría de cero.
- **Interacción de `auto` con `--hasta-ep`**: si el estado más avanzado ya llega a `--hasta-ep` (o lo pasa, porque un
  tramo posterior ya corrió), sale con 0 sin tocar nada; si no, sigue hasta `--hasta-ep` y corta. Como `auto` parte
  siempre del estado más avanzado, lo único que borra es lo que un intento caído escribió después de su último
  estado (checkpoints sin estado). Sin `--hasta-ep`, sigue hasta `--episodios` y publica.
- **"200 con piso"** (`p3piso200`): no hace falta otra corrida. Los checkpoints ≤ 200 del 400 con horizonte 200 y piso
  0.1 son los de una corrida de 200 con piso (la tasa es la misma hasta el 200); el paso aparte elige entre ellos con
  `val_total_serie` del meta del 400 y publica con su etiqueta. "400 eligiendo entre 20" (ep. 20, 40, ..., 400) sale de
  la misma serie.
- **Un error de código** (B22: trabajos nuevos `_r2`): el trabajo nuevo debe usar otra etiqueta o borrar los estados
  viejos; si no, `auto` seguiría desde los estados del código con error. El estado guarda la huella del código y la
  reanudación avisa si es otra (no el commit: el HEAD cambia cada mañana al commitear estado y logs), pero no lo
  rechaza: los tramos de un trabajo pueden correr con código distinto, de una noche a la siguiente. El meta publicado
  lleva entonces `tramos` con las huellas (sección 7).
- **Revisar los comandos antes de la noche**: `rl_ippo.validar_args(argv)` (sección 7) o `--validar-args` en la
  línea de comando.
- **Publicación**: primero el `.json` y al final el `.pt`; si el `.pt` publicado existe, su `.json` está completo.

### 2.6 Límites

- **Dos procesos con la misma etiqueta a la vez no están protegidos.** Lo evitan las dependencias de la cola.
- La columna `segundos` de las filas copiadas es la de la corrida que las hizo.
- Un `.pt` copiado a una etiqueta nueva guarda dentro el nombre del archivo de origen (lo escribe `torch.save`): sus
  tensores son los mismos, su sha256 no (B12).
- Si el estado más avanzado de una etiqueta nueva es una copia (el trabajo se cayó antes de su primer estado propio,
  o los propios no sirven), `auto` repite la copia desde el origen: es lo mismo que relanzar el primer tramo. Si
  tampoco sirve ninguna copia, `auto` empezaría de cero con la etiqueta nueva; con el origen en la misma carpeta
  `checkpoints/`, como en el plan, las copias solo dejan de servir si se dañan todas a la vez.
- Con la ruta de otra etiqueta, si la etiqueta nueva tiene estados propios que salen de **otro** estado de partida, la
  ruta manda: se borra la etiqueta nueva y se copia de nuevo.
- Una corrida reanudada no borra una política publicada antes con la misma etiqueta: la reescribe al llegar a
  `--episodios`, como hace hoy una corrida nueva.

## 3. Registro extendido

`--registro-extendido` agrega al final del CSV, en este orden:

1. `val_<s>` de las semillas de validación que no tienen columna fija y luego sus `val_total_<s>` (con 999 y 1999,
   que ya tienen columna, no se repiten);
2. `var_explicada`: 1 − Var(retorno − V)/Var(retorno) en el lote del episodio, con V el valor que dio el crítico al
   decidir (antes de actualizar);
3. `frac_forzadas`: fracción de decisiones con una sola acción legal (verde mínimo o máximo);
4. `msg_edad`: edad media (s) del mensaje de cada vecino en el momento de decidir (vacía sin mensajes);
5. `ent_coef`: coeficiente de entropía de la actualización.

En P1 dan, por ejemplo, `var_explicada` −0.003 en el episodio 1 y 0.84-0.90 después, `frac_forzadas` 0.34-0.39 y
`msg_edad` 1.96-1.99 s [M, humo de 3 episodios], como el prototipo (−0.02 y 0.80-0.94; 18-42 %; 1.9-2.0 s).

**Por qué detrás de una opción, y en qué se aparta del prototipo** (`plan3/modelo/code_m/rl_ippo.py`):

- El prototipo agregaba las columnas siempre: con todo apagado su CSV tenía 7 columnas más (y las de cada semilla), y
  su prueba comparaba "las columnas comunes". Aquí, con todo apagado, el CSV es el entregado byte a byte salvo
  `segundos`: es lo que piden B13 y la regla 2 del bloque.
- **Una columna nueva entra solo con la opción que la produce.** Las del prototipo para otras etapas (`escala`,
  `vn_media`, `vn_desv`) no están: llegarán con `--escala-demanda` y `--norm-valor`. Así el CSV de una corrida no
  cambia de columnas entre versiones del código, y un tramo que se reanuda con el código de otra noche escribe las
  mismas columnas que el primero.
- `var_explicada` usa el valor guardado al decidir (convención de stable-baselines3) en vez de una pasada más del
  crítico dentro de `actualizar`: es la misma cantidad (mismos pesos) y `actualizar` queda como estaba.
- `frac_forzadas`: el prototipo la dejaba vacía salvo con `--sin-forzadas`. Aquí siempre es la fracción de decisiones
  con una sola acción legal; con `--sin-forzadas` (Etapa 3) será la fracción que queda fuera del lote, con la misma
  fórmula.
- Las columnas por semilla van agrupadas (todas las `val_<s>` y después las `val_total_<s>`), como `val_999`,
  `val_1999` y `val_total_999`, `val_total_1999`; el prototipo las intercalaba.

## 4. Pruebas

Guiones en `plan3/pruebas/ent/` (utilidades comunes en `util_ent.py`); salidas en `plan3/pruebas/ent/salidas/`;
corridas en `plan3/tmp_ent/` (ignorada por git). Todas con `OMP_NUM_THREADS=1` y `MKL_NUM_THREADS=1`, una carpeta
por corrida con copias de los escenarios de `plan3/`, y como mucho 3 procesos a la vez. Semillas: base 7 y
validación en 424301-424302 (evaluación en 424303-424304), salvo la prueba 5 (base 42). El código del tag se extrae
con `git show entregado-2026-10-25:` a `tmp_ent/codigo_tag/` junto con los módulos que importa (`comun`,
`rl_corredor`, `escenarios_plan2`): el script importa esas copias, no las de la raíz. "CSV igual" quiere decir
**byte a byte salvo la columna `segundos`** (tiempo de reloj; el guion comprueba antes que leer y reescribir el CSV
da el archivo exacto).

**Toda la batería corrió sobre el commit 1557e91**, que tiene el `rl_ippo.py` final (después solo cambiaron guiones
de prueba). El meta guarda el commit, así que las corridas que se comparan deben compartirlo: todas dicen
`"git": "1557e91"`. Resultado: **todas las comprobaciones OK**. Dos salidas se rehicieron con el mismo commit:
`prueba_caida.txt` (la prueba se corrió otra vez entera, porque el guion contaba mal los procesos que mata
`taskkill`) y `prueba_piso.txt` (con `--sin-correr`: compara las mismas dos corridas de 181 episodios, con una línea
más precisa sobre el estado del 181).

**Revisión de robustez (sección 7): se volvió a correr sobre el commit 24ebb66** lo que toca el código cambiado:
identidad (pruebas 1 y 2 y ablación), reanudación en P1 (pruebas 3 y 4 y rechazos), caídas, la prueba 5 (base 42
frente al diagnóstico), las pruebas nuevas `prueba_robustez` y `prueba_comandos`, y la identidad de
`chequeos_previos`. Resultado: **todo OK**. Las pruebas comparan ahora los estados sin `tramos` (lo único que distingue
20 seguidos de 10 + 10) y comprueban aparte que sean 1-20 frente a 1-10 y 11-20 con la misma huella; `prueba_caida`
compara el meta sin `reanudaciones` y comprueba aparte un registro por relanzamiento, todos repetidos, y que no haya
`rehechos.json`. No se repitieron P6 ni la del piso: la revisión no toca el entrenamiento ni la tasa, y P1 cubre los
mismos caminos de la reanudación.

| # | Prueba | Resultado [M] | Salida |
|---|---|---|---|
| 1 | Todo apagado = tag: IPPO entregado y V2 (`--v2 --criterio-val total`), P1, 10 episodios, validación cada 5 | OK: CSV igual; checkpoints 5 y 10 con 12/12 tensores y `.json` iguales; política publicada igual byte a byte y meta igual; hasta el log de consola es el mismo (salvo los segundos) | `prueba_identidad.txt` |
| 2 | `--guardar-estado` y `--registro-extendido` no cambian ningún número; `evaluar.py` juega igual | OK: 57 columnas comunes con 0 diferencias, la cabecera es la del tag más 8 columnas al final; checkpoints, política (bytes) y meta iguales; un estado por checkpoint; el CSV de `evaluar.py` en 424303-424304 es el mismo byte a byte, con IPPO y con V2 | `prueba_identidad.txt` |
| — | Ablación: las dos `--solo-*` = `--v2`; cada una sola hace su mitad | OK: las dos juntas dan el CSV, los checkpoints, la política y el meta de `--v2`. `--solo-descuento` juega el episodio 1 como IPPO entregado y `--solo-exploracion` como V2 (mismo timeLoss y cambios), y las dos actualizan distinto | `prueba_identidad.txt` |
| 3 | P1: 20 seguidos = 10 (corte) + 10 reanudados, con IPPO entregado y con V2 | OK con los dos: el corte sale con 0, no publica y deja CSV de 10 filas y estados 5 y 10; reanudado, CSV igual, checkpoints 5-20 con 12/12 tensores y `.json` iguales, política igual byte a byte, meta igual y estados 5-20 iguales (Adam, generadores, series, CSV). Con IPPO entregado esto prueba además el generador de torch, que muestrea las acciones | `prueba_reanudar_corredor.txt` |
| 3 | P6: lo mismo con V2 | OK: el corte no publica y deja el estado del 10; reanudado, CSV igual (20 filas), checkpoints 5-20 con 12/12 tensores y `.json` iguales, política igual byte a byte, meta igual, y estados 5, 10, 15 y 20 iguales (pesos, Adam con 5960 a 19 900 pasos, los cuatro generadores, series y CSV). P6 tardó 26 s por episodio (mediana; 22-61 s) | `prueba_reanudar_malla3_alta.txt` |
| 4 | Etiqueta nueva desde el ep 10, 30 episodios con horizonte 20 y piso 0.1 | OK: checkpoints y estados ≤ 10 copiados byte a byte; `reanudado_de` y las opciones de la tasa en el meta; frente a una corrida seguida de 30 con esa etiqueta y esa tasa, CSV igual (30 filas), checkpoints 5-30 con tensores y `.json` iguales (salvo `reanudado_de`), política y meta iguales, estados 15-30 iguales; filas 1-10 iguales a las de la V2 de origen salvo `etiqueta` | `prueba_reanudar_corredor.txt` |
| — | Rechazos (otra tasa, configuración, semillas, base o registro; checkpoint alterado; opciones incompatibles) | OK, 10 de 10: salen con 1 (o 2, argparse) y el motivo, sin escribir ni borrar nada | `prueba_reanudar_corredor.txt` |
| — | `--reanudar auto` con `taskkill /F /T` a mitad de cada tramo; y la ruta de una etiqueta nueva relanzada | OK. Misma etiqueta (dos tramos, 10 y 20): cada intento muerto (en el ep 8 y en el 18; python y su sumo) sale distinto de 0 y deja los estados hasta el 5 y el 15; relanzado con el mismo comando, sigue desde ahí, los episodios rehechos repiten los del intento muerto, y el resultado es la corrida seguida (CSV, checkpoints, política byte a byte, meta y estados). Relanzar un tramo ya hecho, o la corrida publicada, sale con 0 sin tocar ningún archivo. Etiqueta nueva (desde el ep 10, 30 episodios, horizonte 20, piso 0.1, la ruta de origen en los dos tramos): muerto en el ep 18 y relanzado, sigue desde su estado del 15 sin volver a copiar, y termina igual que la corrida seguida de 30 con esa etiqueta. Desde la revisión de robustez, el meta publicado anota cada relanzamiento (partidas 5 y 15; 15 en la etiqueta nueva), todos repetidos, y no hay `rehechos.json` | `prueba_caida.txt` |
| 5 | V2 del corredor, base 42, ep 10, frente a la V2 del diagnóstico | OK: 12/12 tensores iguales (`torch.equal`; el sha256 difiere por el nombre); filas 1-10 iguales en las 48 columnas comparables. Validar en otras semillas, y una vez más (en el 5), no cambió el entrenamiento | `prueba_diag.txt` |
| r | Robustez (sección 7): estados dañados, etiqueta nueva con estados propios dañados, CSV tomado, B22, procedencia, `validar_args` y escrituras atómicas | OK, R1-R7 (detalle en la sección 7) | `prueba_robustez.txt` |
| c | Los 403 comandos de `rl_ippo` del generador frente a `validar_args` | OK: pasan todos menos los 175 de la Etapa 3, que esperan sus opciones | `prueba_comandos.txt` |
| d | 400 con horizonte 200 y piso 0.1 repite los episodios 1-181 de una de 200 | OK: la tasa es la misma bit a bit en 1-180 (en el 181 difiere en el último bit: 0.1 frente a 0.0999...98); CSV 1-181 igual; checkpoints 10-180 iguales; estados 10-180 iguales. En el 181 hasta los pesos y los momentos de Adam coinciden: la diferencia se pierde al pasar a float32. Desde el 182 la tasa cambia de verdad (9.5e-05 frente a 1e-04) | `prueba_piso.txt` |

## 5. Para la Etapa 3 y la política por red (dónde enganchar)

No se implementó nada de la Etapa 3 ni de la Etapa 4. Lo que cada opción nueva tendrá que sumar, para que la
reanudación siga exacta:

| Pieza | Dónde | Qué |
|---|---|---|
| Opción que cambia el entrenamiento (`--obs-cercana`, `--norm-valor`, `--sin-forzadas`, `--msg-cada-paso`, `--paso-decision`, `--escala-demanda`) | `config_reanudacion` | su valor, **solo si está activa** (como `opciones` en `meta_base`) |
| Calendario por episodio (`--ent-final`) | bucle (`hiper_ep`, ya existe) y `comprobar_estado` | el coeficiente de cada episodio, como `lr`: se guarda en el estado y se compara bit a bit |
| Estado que pasa de un episodio a otro (`NormValor`: m1, m2, peso; generador de `--escala-demanda`) | `guardar_estado` y `reanudar` | guardarlo y restaurarlo; si falta, la reanudación deja de ser exacta |
| Columnas nuevas (`escala`, `vn_media`, `vn_desv`) | `campos_csv` | solo con su opción y solo con `--registro-extendido` |
| `frac_forzadas` con `--sin-forzadas` | `correr_episodio` | misma fórmula: forzadas / (libres + forzadas) |

Las pruebas de `plan3/pruebas/ent/` sirven de no regresión para esas opciones: con ellas apagadas, `prueba_identidad`
debe seguir dando todo OK.

## 6. Pendiente o dudoso

**Decisiones mías que conviene revisar** (ninguna cambia lo entregado):

1. **Etiqueta nueva: las filas copiadas del CSV y los `.json` copiados pasan a la etiqueta nueva.** El plan dice
   "copia". Copiar tal cual dejaría, dentro de `resultados_<nuevo>.csv`, filas con la columna `etiqueta` vieja, y
   checkpoints de la etiqueta nueva cuyo meta dice otra etiqueta, otros `--episodios` y otras opciones de la tasa.
   Así, en cambio, la corrida reanudada es igual a una corrida seguida con la etiqueta nueva (lo comprueba la prueba
   4) y la procedencia queda en `reanudado_de` (meta) y en los estados copiados, que conservan su `tag`. Volver a la
   copia literal es cambiar una línea (`lineas_csv_estado(..., None)`) y copiar el `.json` en vez de reescribirlo.
2. **La ruta de una etiqueta nueva sigue desde los estados propios** si un intento anterior ya avanzó desde ese
   mismo estado de origen. El pedido decía que la etiqueta nueva exige ruta (se cumple) y no decía qué hacer al
   relanzarla. Sin esto, relanzar el primer tramo repetía todo el tramo y, peor, relanzarlo después de que corrieron
   tramos posteriores **borraba** su avance. Con esto, el comando de un trabajo de etiqueta nueva es uno solo para
   todos sus tramos y relanzamientos (lo prueba `prueba_caida`).
3. **`--hasta-ep` y `--reanudar auto` exigen `--guardar-estado`**: un corte sin estado perdería el trabajo, y `auto`
   sin estados repetiría siempre desde cero.
4. **`--registro-extendido` es una opción aparte de `--guardar-estado`** (sección 3).

**Límites conocidos:**

5. "Igual byte a byte" excluye siempre la columna `segundos`: es tiempo de reloj y cambia entre dos corridas del
   mismo código, también con el código del tag.
6. **Espacio**: ~4.5 MB de estados por corrida de 200 episodios y ~11 MB por una de 400 [I]; para todo el plan, del
   orden de 1-2 GB en `plan3/checkpoints/` [S, con ~300 corridas], que el respaldo de cada mañana copia. Si molesta,
   se podría guardar el estado solo cada 20 episodios más el del corte y el del 180 (no está hecho: la tarea pedía
   uno por checkpoint).
7. **No hay candado**: dos procesos con la misma etiqueta a la vez se pisan. Las dependencias de la cola lo evitan.
8. **Error de código y `auto`**: un trabajo `_r2` con la misma etiqueta seguiría desde los estados del código con
   error. El generador debe darle otra etiqueta (o borrar los estados viejos); el log avisa si la huella del código
   del estado es otra, y el meta publicado guarda los `tramos` (sección 7).
9. **El commit va en el meta** (`git`, como siempre): dos corridas solo dan el mismo meta si corren con el mismo
   commit. Por eso toda la batería final corrió sobre un solo commit (abajo).
10. Determinismo entre máquinas o versiones: no probado (como antes); las pruebas corren con Python 3.14.6,
    torch 2.14.0+cpu y SUMO 1.25.0.

**No está hecho (no era de esta tarea):** el paso que publica "200 con piso" y "400 eligiendo entre 20"
(`p3_elegir.py`), el generador de trabajos y la cola (que deben usar el contrato de la sección 2), y las opciones de
la Etapa 3 y de la política por red (sección 5).

## 7. Robustez (revisión del 05.11.2026)

Una revisión escéptica del contrato encontró seis fallas posibles. Todas son de gravedad baja: casos raros (un corte
de luz en el segundo justo, un CSV abierto en Excel, un código que cambia entre noches) y ninguna cambia un número.
Quedaron arregladas en el commit 24ebb66, sin opciones nuevas salvo `--validar-args`. Con todo apagado, los números
y los bytes de checkpoints y política siguen siendo los del tag (prueba 1).

| # | Qué podía pasar | Qué hace ahora | Prueba [M] |
|---|---|---|---|
| 1 | Un estado truncado o dañado (corte de luz, `taskkill` a mitad de una copia) hacía fallar todos los relanzamientos: `auto` tomaba el de mayor NNN sin probarlo, y `torch.load` no revisa el CRC | Estados, checkpoints y copias se escriben en un temporal que se baja a disco (fsync) y se renombra. `estado_valido` revisa el zip (`testzip`), la carga, la versión, el episodio y el sha256 de los checkpoints que anota. `auto` va de mayor a menor: uno que no sirve se renombra a `.roto` (no se borra), con un AVISO, y prueba el anterior. Con etiqueta nueva, si ningún estado propio sirve, copia otra vez del origen | R1, R2 |
| 2 | La publicación no era atómica | Primero el `.json` y al final el `.pt`, cada uno por temporal | R7 |
| 3 | Un CSV abierto en Excel (o tomado por el antivirus) hacía fallar el tramo sin reintento | Tramo intermedio: AVISO y sigue con el CSV en memoria (el estado lo guarda). Último tramo: al final reintenta cada 30 s, hasta 30 min, antes de publicar; si no puede, sale con "Permission denied" y la cola lo reintenta. Las escrituras reintentan si el archivo está tomado | R3, R7 |
| 4 | B22: un episodio rehecho que no repetía solo dejaba un AVISO en el log | Además, `checkpoints/<tag>_rehechos.json` (lo muestra el resumen de `p3_noche`) y `reanudaciones` en el estado y en el meta publicado. El código de salida no cambia | R4 y `prueba_caida` |
| 5 | Procedencia: el meta solo guardaba el commit del último tramo, y el aviso de commit saltaba cada mañana | El estado guarda `codigo` (sha256 de `rl_ippo.py`, `comun.py`, `rl_corredor.py` y `escenarios_plan2.py`, con fin de línea normalizado) y `tramos` (`{desde, hasta, git, codigo}`). El aviso compara `codigo`. El meta lleva `tramos` solo si hubo más de un código | R5 y `prueba_reanudar` |
| 6 | Nada comprobaba que `rl_ippo` aceptara los comandos del generador | `validar_args(argv)`: `parse_args` y todos los `ap.error`, sin leer el escenario, sin tocar archivos y sin cambiar `HIPER`. `--validar-args` hace lo mismo desde la línea de comando | R6 |

**Lo que no cambia.** La versión del estado sigue en 1: las claves nuevas se leen con `.get`, y un estado anterior
sigue valiendo (su tramo cuenta como "sin huella"). El `.pt` de checkpoints y política tiene los mismos bytes que con
un `torch.save` directo: el temporal se llama `<tag>_epNNN.tmp` y `torch.save` guarda dentro del zip el nombre del
archivo sin su última extensión. Con todo apagado, el log de consola es el de siempre.

**`validar_args` para `chequeos_previos`** (en su proceso; `argv` es el comando sin `python ../rl_ippo.py`, y sin
`../con_escenarios.py` cuando va con el lanzador):

```python
sys.path.insert(0, RAIZ)                      # la carpeta de rl_ippo.py y con_escenarios.py
import con_escenarios
con_escenarios.registrar()                    # antes de importar rl_ippo: suma los escenarios del plan 3
import rl_ippo
err = io.StringIO()
try:
    with contextlib.redirect_stderr(err):
        args = rl_ippo.validar_args(argv)     # bien: devuelve args (no toca archivos, ni HIPER, ni C)
except SystemExit as e:                       # mal: e.code == 2; el motivo es la ultima linea de err
    motivo = err.getvalue().strip().splitlines()[-1]
```

**Prueba nueva** (`prueba_robustez.py`; P1, V2 con estado y registro, base 7, 6 episodios con validación cada 2 en
424301-424302; la referencia es el mismo comando sin cortes ni daños). Resultado: todo OK [M].

| | Caso | Resultado [M] |
|---|---|---|
| R1 | Estado del 4 con un byte cambiado en una pieza de tensores: `torch.load` lo carga sin error, `testzip` no | Relanzado con `auto`: AVISO, queda como `.roto` y sigue desde el 2; los episodios 3-4 rehechos repiten. Luego, el checkpoint del 4 alterado: el estado del 4 va a `.roto2` y sigue desde el 2. `auto` con otra configuración sale con error sin apartar ni tocar nada. Final igual que la referencia: CSV, checkpoints, política byte a byte, meta y estados |
| R2 | Etiqueta nueva (8 episodios, horizonte 6, piso 0.1) desde el estado del 2 | Estado propio del 6 truncado: sigue desde el propio del 4, sin copiar. Propios del 4 y del 6 dañados: los aparta y copia otra vez del origen. Final igual que la corrida seguida de 8 con esa etiqueta |
| R3 | CSV tomado | Tramo intermedio con el CSV sin compartir: avisa, sigue en memoria, sale con 0 y el estado guarda las filas. Último tramo con el CSV en solo lectura (como Excel): espera, lo escribe al soltarlo (segundo intento) y publica. Final igual que la referencia |
| R4 | Fila del episodio 3 alterada en el CSV y estado del 4 borrado | AVISO del episodio 3, sale con 0, `rehechos.json` con `{partida 2, episodios 3-4, filas 2, distintos [[3, timeloss_prom]]}`, lo mismo en el estado final y en el meta publicado; el CSV final es el de la referencia |
| R5 | Último tramo con una copia del código con un comentario de más | AVISO de otro código; meta `tramos` 1-2 y 3-6 con dos huellas; el checkpoint del 2 sin `tramos` y el del 4 con 1-2 y 3-4; mismos números y política byte a byte |
| R6 | `validar_args`: 2 comandos buenos (uno con `poi_corredor`, tras `registrar()`) y 10 malos | Acepta los buenos y rechaza los malos con código 2 y su motivo; `HIPER` y `C` quedan iguales; `--validar-args` sale con 0 (bueno) o 2 (malo) sin escribir nada |
| R7 | Escrituras atómicas, en el proceso | `.pt` con los bytes de un `torch.save` directo; `Politica.guardar` escribe el `.json` y después el `.pt`; con el destino tomado 2 s, reintenta y escribe; si el escritor falla, el archivo anterior queda entero |

**Los comandos del generador** (`prueba_comandos.py`, sin simular): arma en el proceso la lista completa de
`generar_trabajos3` (3037 trabajos) y pasa por `validar_args` los 403 que corren `rl_ippo`, como hará
`chequeos_previos`. En este commit pasan los de las etapas 1, 2 y 3b, y fallan los 175 de la Etapa 3
("unrecognized arguments: --obs-cercana 75"), como se esperaba: sus opciones llegan con la Etapa 3. Con
`--esperar-rechazo etapa3`, la prueba da todo OK [M].

**Límites:**

- Si una etiqueta nueva no tiene ningún estado que sirva, ni propio ni copia, `auto` empieza de cero (como cualquier
  `auto` sin estados). Con el origen en la misma `checkpoints/`, como en el plan, eso solo pasa si se dañan todas las
  copias a la vez.
- Los `.roto` quedan en `checkpoints/`: se borran a mano después de mirarlos. `rehechos.json` tampoco se borra al
  empezar de cero.
- El CSV no se baja a disco en cada fila; el estado lo guarda entero.
- El código de salida no cambia con B22: el aviso llega por `rehechos.json`, el meta y el log.
