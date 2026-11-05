# Referencias del plan 3 (tareas 0.7-0.12): informe de implementación

05.11.2026. Rama `plan3-ref` (nació de `plan3-dev` en 223f908); este informe va en el último commit de la rama.

## Respuesta corta

- **Qué hay.** Cinco scripts nuevos en `plan3/` y cambios mínimos, apagados por defecto, en tres archivos entregados:

  | Archivo | Tarea | Qué hace |
  |---|---|---|
  | `plan3/barrer_fino.py` | 0.7 | Fijo fino (regla del prerregistro §5), fijo con verdes de 5 en 5 y el ganador de la gruesa ("fijo desde 10 s"), con puntaje por periodo |
  | `plan3/franja.py` | 0.8 | Fijo por franja (un plan por media hora) y fijo por bloques del perfil, con un WAUT por semáforo en su instante limpio |
  | `plan3/actuado.py` | 0.9 | Actuado ajustado: descenso por coordenadas en cadena, `delay_based` y dos variantes coordinadas con el fijo fino |
  | `plan3/reglas.py` | 0.10 | Regla simple U × G y Max-Pressure por carril (con y sin ciclo máximo) para el gancho `decidir` de `rl_ippo`, y su barrido |
  | `plan3/p3_preparar.py` | 0.11 | Trabajo "preparar" de cada noche: `_actuado`, `_trivial` y `_actuado_aj` (punto de extensión para los E2) |
  | `comun.py` | 0.11 | `archivo_actuado` y `archivo_trivial` escriben en un temporal con el pid y reemplazan con reintentos (mismo contenido, byte a byte) |
  | `rl_corredor.py` | 0.7-0.9 | Modos `franja`, `bloques` y `actuado_aj`, y `adicional=` (fijo de otro archivo); sin ellos nada cambia |
  | `evaluar.py` | 0.7-0.10 | `--brazo franja`, `bloques` o `actuado_aj` (con `--programa` opcional), `--brazo fijo --programa --nombre`, `--regla`; funciones para `evaluar3` |

- **Pruebas: pasan** (sección 4). Lo más importante: reproduce filas y ganador del barrido entregado (P1 65/65
  y el ganador; P2-P6 3 de 3; P6 las tres del 15/10); dos corridas, una en trozos, dan los mismos archivos; la suma
  por periodo es el total de `leer_tripinfo` también con vehículos sin entrar; franja con el mismo plan = fijo, cambio
  alineado y 0 cortes de verde; sumo directo = TraCI en franja, bloques y actuado con `<param>` y coordinado; U = ∞ =
  ciclo mínimo; cada ganador jugado por TraCI reproduce su media.
- **No regresión:** 23 de 24 brazos repiten dígito a dígito sus CSV entregados. El que no (IPPO en P6) difiere solo en
  `cambios_fase` (+4 por episodio en el entregado) y **no es una regresión**: el código entregado corrido hoy da lo
  mismo que esta rama, y el CSV entregado se reproduce entero si se pone en P6 la plantilla 15/10 en ajedrez. O sea,
  ese CSV se corrió con otro `malla3_alta.add.xml` y el conteo de cambios de IPPO depende de la plantilla (sección 6).
- **Costo de la noche de referencias:** ~156 h-proceso estimadas (P1-P6 regulares y aleatorias, D, P6e y los 12
  niveles), más el perfil; el detalle por trabajo está en `plan3/pruebas/ref/salidas/costos_ref.txt` y en la sección 2.
- **Un hallazgo que cambia el actuado ajustado:** SUMO 1.25 lee la clave `minTimeloss` y no `minTimeLoss` (la de su
  documentación); con esta última el parámetro se ignora sin aviso. Lo vi en la cadena de prueba de P1 (minTimeLoss 1
  y 3 daban lo mismo en las tres distancias); `actuado.py` usa ahora la clave correcta, y la prueba "cada parámetro
  mueve algún número" compara cada variante con la que solo difiere en ese parámetro (antes la comparaba con el
  actuado por defecto, y una variante `delay_based` siempre difiere de él).
- **Lo dudoso** está en la sección 6. Lo principal: en P6 el 10/10 no deja vehículos sin entrar a los 6000 s (la prueba
  del lector se hizo además con P6 10/25 y P2 10/25, que sí dejan); el actuado ajustado tiene dos variantes
  coordinadas en el paso 6 (decisión del 05.11 tras la primera entrega de este informe: la del informe de
  referencias se comporta como un actuado libre y la segunda es casi el fijo; sección 6, punto 4); y `p3_preparar.py`
  falta en la lista de scripts del prerregistro §3.

---

## 1. Qué hace cada script

Todos corren con `cwd = plan3/`, sin preguntas, deterministas, y escriben cada CSV, JSON y `.add.xml` en un temporal
con el pid que después reemplazan (`barrer_fijo.reemplazar`): un trabajo cortado no deja un archivo que parezca
completo. Terminan con código 0 solo con todas sus salidas escritas. Nunca escriben en `plan2/` ni en `TESIS/`, y
nunca usan `barrer_fijo.py --instalar`. Con escenarios de `escenarios_plan3` (llegadas aleatorias `poi_*`, perfil
`per_*`, P6e) se llaman a través del lanzador: `python ../con_escenarios.py <script> <esc> ...`.

**Semillas** (prerregistro §3 y §5; las llegadas aleatorias se detectan solas por `period="exp(...)"` en las rutas, o
con `--llegadas`):

| Script | Barrido | Finalistas |
|---|---|---|
| `barrer_fino.py` | 2001-2003 (aleatorias: 2001-2010) | 10 mejores con 2001-2010 (aleatorias: 2001-2030); frágiles: 3 primeros con 2001-2030 |
| `franja.py` | pares con las del barrido | 3 mejores pares con 2001-2010 (aleatorias: los 9 con 2001-2030); bloques: 2001-2030 |
| `actuado.py` | 2001-2003 (también con aleatorias) | 3 mejores con 2001-2010 (aleatorias: 10 con 2001-2030) |
| `reglas.py` | 2001-2003 (también con aleatorias) | por familia, 3 con 2001-2010 (aleatorias: 10, o las 4 de MP, con 2001-2030) |

### 1.1 `barrer_fino.py` (0.7)

Importa `Plantilla`, `configs_plantilla`, `desfases_malla3` y `evaluar_config` de `barrer_fijo.py` sin cambiarlos.
Etapas (cada una lee lo que dejó la anterior en `barridos/<esc>/`):

| Etapa | Qué corre | Escribe |
|---|---|---|
| `gruesa` | La rejilla de `barrer_fijo` (MALLAS desde 10 s, desfases del caso o los 3 esquemas, par desplegado, extensión si el ganador queda en el borde) | `gruesa.csv`, `gruesa_semillas.csv`, `fijo_grueso10.json`, `<esc>_r10g.add.xml` |
| `fina` | Mínimos locales de la gruesa (pares de verdes cuyo mejor retraso no supera al de sus vecinos a un paso en un eje), a ≤ 2 % del mejor (aleatorias: diferencia pareada ≤ 2 errores estándar), tope 3; alrededor de cada uno avenida ±4 y transversal ±2 de 1 en 1 (10-60 s) con los 3 mejores patrones de desfase de la gruesa en ese par (malla: los 3 esquemas y `onda_oe`) | `fina.csv`, `fina_semillas.csv` |
| `desfases` | Corredor y red: desfases ±4 s de 1 en 1 alrededor del mejor plan de cada región (corredor 9; red 9 × 9). Malla: nada (sin desfases libres, como `barrer_fijo`) | `desfases.csv`, `desfases_semillas.csv` |
| `desempate` | Las 10 mejores de gruesa, fina y desfases con las semillas del desempate | `desempate.csv`, `desempate_semillas.csv` |
| `fragil` | Si los dos primeros quedan a ≤ 2 % o el ganador tiene una semilla > 1.10 × su mediana: los 3 primeros con 2001-2030; gana la menor media. Instala el fijo fino | `fragil.csv`, `fijo_fino.json`, `<esc>_r10f.add.xml` |
| `mult5` | Fijo con verdes de 5 en 5: los 3 mejores planes de la gruesa con los dos verdes múltiplos de 5, con desfases ±4 s (malla: `onda_oe` para sus verdes); desempate y frágiles como el fino | `mult5.csv`, `mult5_semillas.csv`, `mult5_desempate.csv`, `fijo_mult5.json`, `<esc>_m5f.add.xml` |
| `fino`, `todo` | `gruesa`..`fragil` en un proceso; `todo` agrega `mult5` | lo de cada etapa |

- **Puntaje por periodo** (lo usa `franja.py`): cada corrida da además el retraso total de los vehículos con salida
  programada en cada periodo (`--bloque 1800`: dos medias horas; `--bloque 600`: los seis bloques del perfil). Para
  eso sumo corre con `--tripinfo-output.write-undeparted`, que **nunca** se pasa a `barrer_fijo.correr_sumo`. Las
  métricas de la hora se leen con `comun.leer_tripinfo` sobre el tripinfo sin las filas con depart < 0 (son las de
  `barrer_fijo`, comprobado); las filas con depart < 0 solo entran al periodo de su salida programada,
  fin − departDelay (fin = `end` de las estadísticas). Desde la fusión con `plan3-dev`, `comun.leer_tripinfo` también
  ignora esas filas y `comun.ESCRIBIR_NO_INSERTADOS` (de `evaluar3`) agrega la misma opción en
  `args_estadisticas`; `correr_periodos` no la repite si ya viene.
- **Columnas:** las de `barrer_fijo` en el mismo orden (verde, izquierda, verde_transversal, offsets, esquema, 7
  métricas, 2 sd, semillas) y después ciclo, etapa, región, clave, mediana, peor, trabadas, `total_p<k>` y
  `noins_p<k>`.
- **Trozos y reanudación:** `--trozo k/n` corre solo los planes de índice ≡ k (mod n) de la lista principal de la etapa
  (gruesa: la rejilla inicial; fina; desfases; mult5: sus desfases) y escribe `barridos/<esc>/trozos/<etapa>_t<k>de<n>.csv`.
  La misma etapa sin `--trozo` junta trozos, etapas anteriores y la caché `tmp_fino/<esc>/*.jsonl` (una línea por
  corrida: un trabajo cortado sigue donde quedó), corre lo que falte (en la gruesa, también la extensión) y escribe la
  salida. Cada resultado se guarda con la huella del escenario (sha256 de cfg, red, rutas, adicionales, cortes y del
  código que corre y lee cada corrida) y con el sha256 del programa con que se corrió: solo se reutiliza si los dos
  coinciden. Así, si se arregla el código que genera un programa (B22: "se corren de nuevo los trabajos afectados"),
  no se heredan números viejos; y si cambia el escenario, la etapa siguiente se niega a seguir.
- **El `.add.xml` instalado** tiene el programa `fijo` y reemplaza a la plantilla `<esc>.add.xml` en
  `--additional-files` (como lo haría `--instalar`); para jugarlo: `evaluar.py --brazo fijo --programa <esc>_r10f.add.xml
  --nombre fino` o `evaluar.brazo_programa`.

### 1.2 `franja.py` (0.8)

- **Franja:** los 3 mejores planes de cada media hora según `total_p1` y `total_p2` del barrido fino (gruesa, fina y
  desfases, con las semillas del barrido), sus 9 pares (siempre dos programas, aunque sean el mismo plan), cada par
  con las semillas del barrido; finalistas como en la tabla de semillas; gana la menor media.
- **Bloques (perfil):** el mejor plan de cada bloque de 600 s según su puntaje por bloque (el barrido del perfil se
  corre con `--bloque 600`), una secuencia de hasta 6 programas (un bloque con el mismo plan que el anterior no
  cambia), verificada con 2001-2030. `bloques.json` trae al lado el fijo fino con las mismas semillas, si las tiene.
- **WAUT (B8):** un `<WAUT>` por semáforo, sin `procedure`, con su instante limpio: el primer t ≥ el corte en que
  los dos planes muestran el mismo estado en t − 1, t y t + 1 (posición en el ciclo (t − desfase) mod ciclo). El plan
  nuevo entra alineado con su propio desfase. El archivo se carga **encima** de los adicionales del `.sumocfg` (el
  WAUT activa `franja1`/`bloque1` desde 0 s); nunca va dentro de un `.sumocfg`.
- **Escribe** en `barridos/<esc>/`: `franja.csv` (los 9 pares), `franja_final.csv`, `franja_semillas.csv`,
  `franja.json` (programas, instantes de cambio por semáforo, sha256) o `bloques.csv`, `bloques_semillas.csv`,
  `bloques.json`; y `<esc>_franja.add.xml` o `<esc>_bloques.add.xml`.

### 1.3 `actuado.py` (0.9)

- Variantes del actuado de SUMO 1.25, sin TraCI (el programa encima de los adicionales queda activo por ser el
  último). Rejillas fijas con el defecto incluido; cada paso parte del mejor de los anteriores (en un empate se queda):

  | Paso | Coordenada | Valores (defecto *) |
  |---|---|---|
  | 1 | `max-gap` | 1, 1.5, 2, 3*, 4 s |
  | 2 | `detector-gap` | 1, 2*, 3, 4 s |
  | 3 | `jam-threshold` | −1*, 10, 30 s |
  | 4 | `maxDur` del verde de avenida | 30, 45, 60* s |
  | 5 | `maxDur` del verde transversal | 20, 30, 60* s |
  | 6 | familia | `delay_based` (detectorRange 50/100/200 m × minTimeLoss 1*/3 s, con los maxDur elegidos) y las dos variantes coordinadas del mejor actuado |
  | final | — | las 3 mejores de los 6 pasos con 2001-2010 (aleatorias: 10 con 2001-2030) |

- `minDur` 10 s (5 en giros), fases y duración inicial del programa "0" de la red, desfase 0: la variante por defecto
  es el actuado entregado (`comun.archivo_actuado`) con `programID="actuado_aj"`. Los `<param>` se escriben solo si
  difieren del defecto de SUMO (`delay_based` los escribe siempre).
- **Ojo con `minTimeLoss`:** SUMO 1.25 lee la clave `minTimeloss` (así está en `sumo.exe`); con `minTimeLoss`, como
  dice su documentación, la ignora sin aviso (medido en P1: 0.01, 1, 3 y 1000 dan el mismo tripinfo; con
  `minTimeloss` dan 25.02, 22.37, 23.61 y 111.71 s/veh). `actuado.py` escribe `minTimeloss`.
- **Dos variantes coordinadas** (prerregistro §5): `coordinated=true`, `cycleTime` y desfases del fijo fino
  (`barridos/<esc>/fijo_fino.json`), las fases de su plantilla con sus duraciones y los parámetros del mejor actuado;
  (a) el verde de avenida con `earliestEnd` en su fin del plan fijo (la propuesta de `plan3/referencias/informe.md`
  §4), y (b) "fin fijo": `latestEnd` = `earliestEnd` en la avenida **y** `latestEnd` en la transversal, cada uno en su
  fin del plan fijo: la avenida termina siempre donde el plan fijo y la transversal puede cortar antes, nunca después
  (clave `..._coord<hash>_finfijo`, columna `fin_fijo` de los CSV). El paso 6 las corre a las dos con las mismas
  semillas y la misma regla; la elegida pasa al final como cualquier otra variante.
- **Escribe** en `barridos/<esc>/`: `actuado_paso<k>.csv`, `actuado_paso<k>.json` (partida, variantes y elegida),
  `actuado_paso<k>_semillas.csv`, `actuado_final.csv`, `actuado_final_semillas.csv`, `actuado_aj.json`; y
  `<esc>_actuado_aj.add.xml`. `actuado.py <esc> --instalar` lo reescribe desde el JSON (lo usa `p3_preparar.py`).

### 1.4 `reglas.py` (0.10)

- `hacer_decidir(regla)` da la función `decidir` para `rl_ippo.correr_episodio(..., variante="local", decidir=...)`
  (mismo reloj de 5 s, máscara, ámbar y métricas que IPPO; sin tocar `rl_ippo.py`). Crear una por episodio.
- Nombres: `regla_u<U>g<G>` (U entero o `inf`; `regla_uinfg60` es el ciclo mínimo), `mp`, `mp_det`, `mp_c<C>`,
  `mp_det_c<C>`. Toda acción respeta la máscara (hay un `assert`).
- Barrido: reglas U ∈ {1, 2, 3, 4, 6} × G ∈ {30, 60}; MP `mp`, `mp_det`, `mp_c60`, `mp_c90`. Corre por TraCI en un
  solo proceso; `--familia regla` y `--familia mp` lo parten en dos trabajos que no se pisan. Escribe, por familia,
  `barridos/<esc>/reglas_<familia>.csv`, `reglas_<familia>_final.csv` y `reglas_<familia>_semillas.csv`, y
  `regla.json` o `mp.json` (el ganador: lo que va a `evaluar.py --regla`).

### 1.5 `p3_preparar.py` y la escritura atómica (0.11)

- `comun.escribir_atomico(ruta, texto)`: temporal `<ruta>.<pid>.tmp` y `os.replace` con 10 reintentos de 2 s (como
  `barrer_fijo.reemplazar`). La usan `archivo_actuado` y `archivo_trivial`; el archivo sale igual byte a byte.
- `p3_preparar.py <esc> ... [--piezas actuado,trivial,actuado_aj]`: escribe `<esc>_actuado.add.xml`,
  `<esc>_trivial.add.xml` y `<esc>_actuado_aj.add.xml` (este desde `actuado_aj.json`, y falla si el sha256 no es el
  congelado), los relee como XML e imprime su sha256. **Punto de extensión:** el diccionario `PIEZAS`
  (`{nombre: función(esc) -> ruta}`); los E2 de la observación nueva (3.1) entran como otra pieza.

---

## 2. Cómo se corre cada celda

`h-p` = horas-proceso estimadas por trabajo en el régimen conservador + 10 % (`pruebas/ref/costos_ref.py`; cuentas con
la gruesa entregada como estimación del número de regiones de la fina). Los barridos que pasan de ~2 h se parten con
`--trozo k/n` (los trozos en paralelo; después la misma etapa sin `--trozo`). Todos con `--procesos 1`.

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
python reglas.py <esc> --familia regla ; python reglas.py <esc> --familia mp   # sin dependencias
```

| Celda | gruesa | fina | desfases | desempate | frágil | mult5 | franja | actuado (6 pasos + final) | reglas |
|---|---|---|---|---|---|---|---|---|---|
| P1 corredor | 0.29 | 0.14 | 0.02 | 0.04 | 0.03 | 0.12 | 0.03 | 0.06 | 0.11 |
| P2 corredor_alta | 0.91 | 1.03 | 0.07 | 0.18 | 0.15 | 0.54 | 0.12 | 0.16 | 0.27 |
| P3 red | 1.94 | 0.19 | 0.33 | 0.10 | 0.08 | 1.18 | 0.07 | 0.11 | 0.17 |
| P4 red_alta | 2.34 | 0.22 | 0.40 | 0.12 | 0.10 | 1.43 | 0.08 | 0.12 | 0.20 |
| P5 malla3 | 0.66 | 3.20 | 0 | 0.21 | 0.18 | 0.43 | 0.15 | 0.32 | 0.46 |
| P6 malla3_alta (y P6e) | 1.12 | 1.69 | 0 | 0.36 | 0.31 | 0.72 | 0.25 | 0.55 | 1.00 |
| D | 0.64 | 0.62 | 0.04 | 0.11 | 0.09 | 0.32 | 0.07 | 0.16 | 0.27 |

(frágil: cota, si se activa; si no, 0.)

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

Con trozos de ≤ 2 h: poi P3/P4 gruesa en 4-5 trozos, poi P5 fina en 6, poi P6 fina en 3; reglas de poi P6 en dos
trabajos (`--familia regla` 3.8 h-p y `--familia mp` 1.5 h-p).

### 2.4 Perfil `per_<caso>` (P1 y P3)

Por el lanzador y con `--bloque 600` en **todas** las etapas del barrido (la huella incluye los cortes; mezclar
`--bloque` hace que la etapa siguiente se niegue a seguir):

```
python ../con_escenarios.py barrer_fino.py per_<caso> --bloque 600 --etapa gruesa | fina | desfases | desempate | fragil
python ../con_escenarios.py franja.py per_<caso> --bloques                     # depende de desfases -> per_<caso>_bloques.add.xml
python ../con_escenarios.py actuado.py per_<caso> --paso ...                    # como 2.1
python ../con_escenarios.py reglas.py per_<caso> [--familia ...]
```

Costo como la celda aleatoria de su caso (poi P1 y poi P3) más 30 corridas de la verificación de bloques; sin mult5
ni franja de media hora.

### 2.5 Salidas esperadas por trabajo (para el generador y la cola)

Todas bajo `plan3/`; `B` = `barridos/<esc>/`.

| Trabajo | Salidas que deben existir al terminar |
|---|---|
| `barrer_fino.py <esc> --etapa E --trozo k/n` | `B/trozos/E_t<k>de<n>.csv` |
| `barrer_fino.py <esc> --etapa gruesa` | `B/gruesa.csv`, `B/gruesa_semillas.csv`, `B/fijo_grueso10.json`, `<esc>_r10g.add.xml` |
| `... --etapa fina` / `desfases` / `desempate` | `B/<etapa>.csv`, `B/<etapa>_semillas.csv` |
| `... --etapa fragil` | `B/fragil.csv`, `B/fijo_fino.json`, `<esc>_r10f.add.xml` |
| `... --etapa mult5` | `B/mult5.csv`, `B/mult5_desempate.csv`, `B/fijo_mult5.json`, `<esc>_m5f.add.xml` |
| `franja.py <esc>` | `B/franja.csv`, `B/franja_final.csv`, `B/franja.json`, `<esc>_franja.add.xml` |
| `franja.py <esc> --bloques` | `B/bloques.csv`, `B/bloques.json`, `<esc>_bloques.add.xml` |
| `actuado.py <esc> --paso k` (1-6) | `B/actuado_paso<k>.csv`, `B/actuado_paso<k>.json` |
| `actuado.py <esc> --paso final` | `B/actuado_final.csv`, `B/actuado_aj.json`, `<esc>_actuado_aj.add.xml` |
| `reglas.py <esc> --familia regla` (o `mp`) | `B/reglas_regla.csv`, `B/reglas_regla_final.csv`, `B/regla.json` (o `reglas_mp*.csv`, `B/mp.json`) |
| `p3_preparar.py <esc> ...` | `<esc>_actuado.add.xml`, `<esc>_trivial.add.xml` (y `<esc>_actuado_aj.add.xml` con esa pieza) |

Ejemplo, P6 con llegadas aleatorias (trozos de ~2 h según la tabla 2.3):

```
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa gruesa --trozo 0/2
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa gruesa --trozo 1/2
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa gruesa
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa fina --trozo 0/3   (1/3, 2/3 y luego sin --trozo)
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa desfases
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa desempate
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa fragil
python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa mult5
python ../con_escenarios.py franja.py poi_malla3_alta
python ../con_escenarios.py actuado.py poi_malla3_alta --paso 1      (2, 3, 4, 5, 6 y final, en cadena)
python ../con_escenarios.py reglas.py poi_malla3_alta --familia regla
python ../con_escenarios.py reglas.py poi_malla3_alta --familia mp
```

### 2.6 Cada noche y la evaluación

- Al empezar la noche: `python p3_preparar.py <esc> ... [--piezas actuado,trivial]` (con `actuado_aj` solo después de
  `actuado.py --paso final` de esa celda). Las evaluaciones de actuado, ciclo mínimo y actuado ajustado dependen de él.
- Brazos (`evaluar.py`, cwd = `plan3/`): `--brazo fijo --programa <esc>_r10f.add.xml --nombre fino` (fijo fino),
  `--programa <esc>_m5f.add.xml --nombre mult5`, `--programa <esc>_r10g.add.xml --nombre grueso10`; `--brazo franja`,
  `--brazo bloques`, `--brazo actuado_aj` (archivo por defecto `<esc>_<brazo>.add.xml`, o `--programa`); `--regla
  <nombre de regla.json o mp.json>`.

---

## 3. Contrato para `evaluar3.py`

Cada función devuelve `(brazo, modelo, base, correr)`; `correr(semilla, tripinfo, serie)` devuelve el dict de
métricas de siempre (`retraso_total_prom`, `timeloss_prom`, `no_insertados`, `ret_retraso`...) y no imprime ni
escribe nada fuera del tripinfo y la serie que pide el llamador (los nuevos brazos no regeneran archivos: leen el
suyo; los brazos entregados `actuado` y `trivial` siguen regenerando su `.add.xml`, ahora de forma atómica).

```python
evaluar.brazo_referencia(esc, brazo, adicional=None)
    # brazo en "fijo", "actuado", "trivial", "franja", "bloques", "actuado_aj"; adicional = ruta del .add.xml
    # (franja, bloques, actuado_aj; por defecto <esc>_<brazo>.add.xml). Brazo y modelo = brazo.
evaluar.brazo_programa(esc, ruta, nombre)
    # fijo con el programa de ruta (reemplaza a los adicionales del .sumocfg que traen <tlLogic>). Brazo "fijo_<nombre>".
evaluar.brazo_regla(esc, regla)
    # regla de plan3/reglas.py (regla_u3g60, regla_uinfg60, mp, mp_det, mp_c60, mp_det_c90...). Brazo = regla.
```

Por debajo: `rl_corredor.correr_episodio(modo, ..., adicional=None)` con los modos `franja`, `bloques` (sin
`setProgram`: los cambia su WAUT) y `actuado_aj` (`setProgram("actuado_aj")`); en `baseline`, `adicional` da el fijo de
ese archivo. Sin modos nuevos ni `adicional`, el comando de sumo es el de antes.

---

## 4. Pruebas

Todas corren con `cwd = plan3/` y escriben solo en `plan3/tmp_ref/` (ignorada) y en `plan3/pruebas/ref/salidas/`.
Semillas de humo (424301-424360), salvo la reproducción del barrido entregado (2001-2003, las suyas) y la no regresión
(1001-1002, solo controles entregados). A lo sumo 3 sumo a la vez.

| Prueba (tarea) | Qué comprueba | Resultado |
|---|---|---|
| `prueba_fino.py` (0.7) | A. La regla con datos inventados: mínimos locales de la gruesa entregada de malla3 (10/10, 25/15 y 30/10 a ≤ 2 %), umbral de 2 errores estándar con llegadas aleatorias, regla de frágiles (dos casos) | PASA (5 de 5) |
| | B. Reproduce `plan2/barrido_<esc>.csv` con 2001-2003: P1, subrejilla completa por la línea de comandos (avenida 15/18/20/25 × transversal 10/15, todos sus desfases) y su ganador; P2-P6, 3 filas cada uno (P6: las tres del 15/10); el lector frente a `barrer_fijo.evaluar_config` | PASA (P1 65 de 65 filas y el ganador; P2-P6 3 de 3; lector = evaluar_config) |
| | C. Dos corridas dan el mismo CSV: la subrejilla otra vez, en 2 trozos y la unión, con otros `--procesos` (sha256 de `gruesa.csv`, `gruesa_semillas.csv`, `fijo_grueso10.json` y `corredor_r10g.add.xml`) | PASA (4 de 4 archivos iguales) |
| | D. Puntaje por periodo: P6 10/10 (se traba: 261 s/veh), P6 10/25 (541 sin entrar) y P2 10/25 (792 sin entrar): la suma por periodo es el total de `leer_tripinfo` sin write-undeparted, la hora es la misma, los no insertados por periodo suman los de las estadísticas y su salida programada es la de su flujo (error 0.000 s) | PASA (3 de 3) |
| `prueba_cadena_p1.py` (0.7-0.11) | La cadena completa en P1 por la línea de comandos (fina, desfases, desempate, frágil, mult5, franja, actuado, reglas, preparar), con desempates y finales en semillas de humo; cada ganador jugado por TraCI reproduce su media (fijo fino, verdes de 5 en 5, franja, actuado ajustado, regla y MP); `evaluar.py --brazo fijo --programa ... --nombre fino` por la línea de comandos; `p3_preparar.py` reescribe el actuado ajustado con el mismo sha256 y deja actuado y ciclo mínimo iguales byte a byte a los del `comun.py` entregado | PASA (21 de 21, después de fusionar `plan3-dev`): el paso 6 del actuado corre 9 variantes, entre ellas las dos coordinadas; fijo fino 22/10 desfase 17 (20.90, frágil: desempate con 30 semillas), franja 20/10-0/25 → 22/10-0/13 (20.59), actuado ajustado coordinado (a) (19.69), todos iguales por TraCI |
| `prueba_franja.py` (0.8) | 1. Franja con plan 2 = plan 1 = el fijo entregado, en P1, P3 y P6, por sumo directo y por TraCI: mismo tripinfo. 2. Cambio en el instante limpio y alineado con el plan 2 solo (P1 con tres pares, P3, P6). 3. 0 cortes de verde sin ámbar (con el cambio de todos a los 1800 s habría 6, 6, 8 y 24). 4. Sumo directo = TraCI. 5. Bloques de 6 programas en P1 y P6: cambios en sus instantes, 0 cortes, sumo directo = TraCI | PASA (41 de 41) |
| `prueba_actuado.py` (0.9) | 1. La variante por defecto = el actuado entregado (mismo programa salvo `programID` y mismo tripinfo, P1-P6). 2. Cada parámetro mueve algún número frente a la variante que solo difiere en él (P2 o P6; la coordinada (b) frente a la (a)). 3. Sin avisos de SUMO en el log (defecto, `<param>`, `delay_based` y las dos coordinadas; P1-P6). 4. Sumo directo = TraCI con `<param>`, con `delay_based` y con las dos coordinadas (P1, P3, P6) | PASA (25 de 25). La (b) mueve frente a la (a) (P2 394.4 frente a 446.8; P6 82.6 frente a 115.9) y, con el fijo entregado como "fino", da el mismo tripinfo que ese fijo en P1, P3 y P6 (su transversal ya está en el mínimo y no puede cortar antes) |
| `prueba_reglas.py` (0.10) | 1. U = ∞ da el mismo tripinfo que el ciclo mínimo (sha256) en P1 y P5. 2. Ninguna acción fuera de la máscara (6 reglas en P1, 2 en P6). 3. Presión 0 con la red vacía (P1 y P6) y no 0 con tráfico. 4. `evaluar.py --regla` escribe su CSV; una regla desconocida se rechaza | PASA (16 de 16) |
| `prueba_atomica.py` (0.11) | 3 evaluaciones simultáneas de actuado y de ciclo mínimo (P1, 5 semillas) y de actuado (P6): código 0, CSV iguales, sin temporales y el `.add.xml` igual byte a byte al del `comun.py` entregado | PASA (3 de 3) |
| `prueba_no_regresion.py` (0.12) | Fijo, actuado, ciclo mínimo e IPPO con mensajes (base 42) en P1-P6 con 1001-1002 por `evaluar.py`: todas las columnas iguales, como texto, a `insumos/puente/eval_<esc>_<brazo>.csv`; `veredicto.py --probar` pasa | 23 de 24 brazos iguales en las 34 columnas; `veredicto.py --probar` pasa. **IPPO en P6: 33 de 34**; `cambios_fase` da 1650 y 1592 y el CSV entregado 1654 y 1596 (ver la fila siguiente) |
| `prueba_nr_p6.py` (0.12) | Por qué difiere IPPO en P6: (1) el código entregado (223f908, sacado con `git show`) corrido hoy da lo mismo que esta rama en las 34 columnas; (2) con la plantilla de P6 cambiada al 15/10 en ajedrez sale igual al CSV entregado en las 34 columnas | PASA (2 de 2): **no es una regresión**. El CSV entregado se corrió cuando `malla3_alta.add.xml` era otro plan (4 semáforos arrancan fuera del primer verde); IPPO no lo usa para el tráfico, pero su conteo de cambios de fase compara con la fase inicial de la plantilla y suma 1 por cada uno (sección 6) |
| `prueba_aleatorias.py` (0.7-0.10) | Por el lanzador (copias de los prototipos en `tmp_ref`): `poi_corredor` y `per_corredor` registrados solo en el proceso; barrido fino aleatorio (umbral en errores estándar, 10 finalistas), franja con los 9 pares finalistas, perfil con 6 puntajes por bloque y su fijo por bloques jugado por TraCI con la misma media, actuado con 10 finalistas y MP con sus 4 | PASA (19 de 19) |

Salidas en `plan3/pruebas/ref/salidas/<prueba>.txt`; `costos_ref.txt` es la estimación de la sección 2. Después de
fusionar `plan3-dev` (17bd53a: protecciones, `rl_ippo.py` y `comun.py` de los otros bloques) y de agregar la segunda
variante coordinada, volví a correr `prueba_actuado`, `prueba_reglas`, `prueba_fino` y `prueba_cadena_p1`: pasan.
Las demás salidas son de antes de la fusión (la no regresión corrió con el `rl_ippo.py` de 223f908).

---

## 5. Decisiones de implementación (lo que el plan no fijaba)

| Punto | Decisión | Por qué |
|---|---|---|
| Mínimo local de la gruesa | Par de verdes cuyo mejor retraso (sobre sus desfases o esquemas) no supera al de sus vecinos a un paso en un eje (vecindad de 4) | Reproduce lo que medía el informe de referencias: malla3 con 3 mínimos a ≤ 2 % (10/10, 25/15 y 30/10) y "7 niveles con 2-3 modos" (con la vecindad de 8, malla3 daba 2) |
| Patrones de desfase en la fina | Los 3 mejores de la gruesa en el par del mínimo, tomados módulo el ciclo de cada par fino | Un desfase es un corrimiento en segundos; módulo el ciclo es el mismo programa |
| Desfases finos | Alrededor del mejor plan de **cada** región (tope 3); el primer semáforo queda en 0 | "Alrededor de cada mínimo local"; en la red con una sola región cuesta lo mismo |
| Malla | Sin desfases libres: la fina usa los 3 esquemas y `onda_oe`; el fijo de verdes de 5 en 5 agrega `onda_oe` a los verdes de sus 3 mejores | Como `barrer_fijo` y el prerregistro ("malla con sus 3 esquemas y `onda_oe`") |
| Empates | Primero el de menor media redondeada a 0.01 (como `barrer_fijo`); en empate, el que se generó antes | Reproduce el ganador de `barrer_fijo` |
| Frágiles con llegadas aleatorias | La regla se evalúa y se informa, pero no corre nada: los finalistas ya tienen 2001-2030 | Es lo que dice la regla |
| Puntaje por periodo | Media de los retrasos medios por semilla de cada periodo (como la hora); los no insertados cuentan con su espera hasta el cierre | Igual que la métrica de la hora |
| Franja | Siempre dos programas y un cambio, aunque los dos periodos elijan el mismo plan | Así "franja con plan 2 = plan 1" prueba el mecanismo y no un caso aparte |
| Instante limpio | Mismo estado en t − 1, t y t + 1 (no solo en t) | Cubre el segundo de diferencia entre cuándo SUMO aplica el cambio (t + 1) y la convención del desfase; la prueba dio 0 cortes |
| Bloques | Si dos bloques seguidos eligen el mismo plan, no hay cambio; si todos eligen uno, no hay WAUT | Menos cambios; mismo resultado |
| Actuado: dependencias | Pasos 1-5 sin dependencias; el 6 depende del fijo fino | Solo la variante coordinada usa el fino; la cadena puede empezar antes |
| Actuado coordinado | Dos candidatas en el paso 6: (a) solo `earliestEnd` en el verde de avenida (fin del plan fijo), como lo proponía el informe de referencias, y (b) `earliestEnd` = `latestEnd` en la avenida y `latestEnd` en la transversal, en sus fines del plan fijo | Decisión del 05.11 (lo conservador: una candidata más solo hace más fuerte la referencia que veta FUNCIONA). La (b) es la que se midió "casi el fijo"; sus dos mitades por separado son peores (sección 6, punto 4) |
| Actuado y reglas con llegadas aleatorias | Barrido con 2001-2003 (como la tabla del prerregistro §5), finalistas 10 con 2001-2030 | La tabla de §5 lo dice así para el actuado y la regla |
| Max-Pressure | 4 variantes (`mp`, `mp_det`, `mp_c60`, `mp_c90`), elegidas como la regla, aparte | Solo descriptivo; así se informa la mejor de cada familia |
| Nombres de reglas | `regla_u<U>g<G>`, `mp`, `mp_det`, `mp_c<C>` | Contrato con `evaluar3` (nombre con los parámetros) |
| Programa del fijo fino | `programID="fijo"`; reemplaza a la plantilla en `--additional-files` | Es lo que habría instalado `barrer_fijo --instalar`; cargarlo encima chocaría con el `fijo` de la plantilla |

## 6. Pendiente o dudoso

1. **P6 10/10 no deja vehículos sin entrar a los 6000 s.** Con 2001-2003 y 424301 se traba mucho (retraso total
   128-480 s/veh), pero a los 6000 s todos entraron. La prueba pedida se hizo igual (la suma por periodo = el total
   de `leer_tripinfo`) y, para ejercitar de verdad la rama de los no insertados, también en P6 10/25 (541 sin entrar) y
   P2 10/25 (792): mismo total, y la salida programada de cada no insertado (fin − departDelay) es la de su flujo
   con error 0.000 s.
2. **`p3_preparar.py` no está en la lista de scripts del bloque JSON del prerregistro §3** (sí `barrer_fino.py`,
   `franja.py`, `actuado.py` y `reglas.py`). Hay que agregarlo antes de la parte A, o la capa 1 de las protecciones
   rechazará el trabajo "preparar".
3. **Opciones de prueba.** `--semillas`, `--semillas-desempate`, `--semillas-fragil`, `--semillas-final`,
   `--avenida`, `--transversal` y `--limite` existen para las pruebas (semillas de humo, subrejillas). La cola no las
   debe usar; la capa 1 podría rechazarlas en los trabajos de referencias.
4. **Variantes coordinadas del actuado.** Quedaron dos candidatas en el paso 6 (decisión del 05.11): la del informe
   de referencias, (a) solo `earliestEnd` en la avenida, y (b) `earliestEnd` = `latestEnd` en la avenida **y**
   `latestEnd` en la transversal, cada uno en su fin del plan fijo. Con el fijo entregado como "fino" y la semilla
   424301 (retraso total, s/veh; `tmp_ref/exp/coord` y `coord2`, no versionados):

   | | fijo | actuado | coordinada (a) | solo `latestEnd` en la transversal | solo `earliestEnd` = `latestEnd` en la avenida | coordinada (b), las dos cosas |
   |---|---|---|---|---|---|---|
   | P1 | 21.91 | 21.49 | 21.19 | 21.35 | 22.28 | 21.91 |
   | P2 | 392.73 | 437.26 | 446.78 | **834.97** | 501.39 | 394.40 |
   | P3 | 20.14 | 21.46 | 21.61 | — | 24.22 | 20.14 |
   | P6 | 82.57 | 114.64 | 115.94 | 112.19 | 85.30 | 82.57 |

   La (a) se comporta como un actuado libre en P2 y P6 (no sostiene la onda verde); la (b) es casi el fijo (la
   transversal solo puede cortar antes si su verde pasa del mínimo). Las dos corren en el paso 6 y el descenso elige
   con las mismas semillas y la misma regla; con eso el actuado ajustado (la referencia que veta FUNCIONA) queda al
   menos tan fuerte como la mejor de las dos. **Corrección:** en la primera entrega de este informe la (b) se describió
   como "`earliestEnd` = `latestEnd` en la avenida", pero los números que se mostraron (los de la última columna)
   eran con `latestEnd` también en la transversal. La línea del prerregistro §5 (commit 17bd53a) debe decir "y
   `latestEnd` en la transversal": las dos mitades por separado (columnas 4 y 5) son peores que el fijo.
5. **Trabajos largos.** Con llegadas aleatorias, el barrido de P3 y P4 (gruesa ~7-8 h-p), la fina de P5 (~11 h-p) y
   las reglas de P6 (~5.3 h-p) hay que partirlos: los barridos con `--trozo`, las reglas por `--familia`. El actuado
   y la verificación de franja/bloques no se parten (≤ 2.3 h-p).
6. **El perfil** necesita `--bloque 600` en todas las etapas de `barrer_fino.py`; si una etapa se corre con otro
   `--bloque`, la siguiente se niega a seguir (huella distinta). Su "fijo de un plan" (el que decide) es el fijo fino de
   ese barrido.
7. **Nombres de los archivos** (`_r10f`, `_r10g`, `_m5f`, `_franja`, `_bloques`, `_actuado_aj`) y de las reglas
   quedan por confirmar con el generador (0.18) y con `evaluar3` (0.14).
8. **La prueba de escritura atómica** corre 3 evaluaciones a la vez y no fuerza la carrera: muestra que no hay
   errores ni temporales sueltos y que el archivo es el del código entregado, no que la carrera vieja se dé.
9. Las duraciones son estimaciones (costos medidos con la cola llena, más 3 % por el tripinfo filtrado [S]); el
   número de regiones de la fina sale de la gruesa entregada y puede cambiar con la nueva (en P5 son 3).
10. **`cambios_fase` de IPPO depende de la plantilla del fijo** (hallazgo de la no regresión, no de este código).
    `rl_ippo.correr_episodio` pone cada semáforo en su primera fase verde, pero toma la fase "anterior" de la
    suscripción leída antes de ese `setPhase`: cada semáforo que la plantilla `<esc>.add.xml` arranca fuera de esa fase
    suma un cambio. El tráfico no cambia. El CSV entregado de IPPO en P6 se corrió con otra plantilla (con el 15/10 en
    ajedrez se reproduce entero), así que su `cambios_fase` tiene +4 por episodio frente a hoy (0.25 %). Afecta a
    cualquier comparación de cambios de fase de IPPO entre corridas con plantillas distintas (por ejemplo, IPPO
    entregado frente a V2 en plan3); el retraso y las demás métricas no. No toqué `rl_ippo.py`.
