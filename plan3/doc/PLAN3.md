# Plan 3: plan de implementación del bloque nuevo

05.11.2026. Versión final, después de las críticas de método, factibilidad e impacto. **Nada está implementado:** el
repositorio y `demo_rl_diag` no se tocaron.

- Antes de empezar, Fabian toma las 8 decisiones de `DECISIONES.md` (grupo A), **todas el día 0**: el prerregistro
  lleva todas las reglas en su parte A, y esa parte se sube antes de la primera noche.
- Este plan asume las opciones recomendadas. Donde una decisión cambia una tarea, se dice entre corchetes, por ejemplo
  [A4]. Las técnicas van por defecto (B1-B25).

**Marcas.** [M] medido (archivo y línea, o salida de una prueba); [I] inferido; [S] supuesto; [L] literatura.

**Rutas.**
- `plan3/<área>/...` (informes del diseño) está en `C:/Users/GAMER/Documents/demo_rl_semaforo/analisis_mejora_2026-11-04/`;
  `critica_codigo/...` y `plan3_critico_prerregistro/...`, en `analisis_mejora_2026-11-04/plan3/`.
- Las rutas sin prefijo son del repositorio `demo_rl` (81378fb).
- En la rama nueva, `plan3/` es la carpeta de trabajo.
- **Estado (05.11.2026):** Fabian tomó las decisiones A1-A8, todas las recomendadas. La implementación empezó ese día.

**Costos.** Salen de `costos_plan3.py`, en `analisis_mejora_2026-11-04/plan3/final/` (salida en `costos_plan3_salida.txt`). Parten de duraciones
medidas y simulan la cola noche por noche, con las dependencias y la hora de corte. **Régimen de base: conservador +
10 %**; el central va al lado. "h-p" es h-proceso; 12 h-p ≈ 1 h de reloj.

---

## Respuesta corta

1. **Qué se hace.** Se corren todas las etapas, sin puertas.

   | Etapa | Qué |
   |---|---|
   | 0 | Preparación, referencias y chequeos |
   | 1 | V2 en todos los casos, con el control C0 |
   | 2 | Llegadas aleatorias con y sin mensajes, perfil de 10 min y mezcla de Lima |
   | 3 | Observación nueva, limpiezas de PPO, **reloj de 2 s y modelo completo** [A4] |
   | 3b | 400 episodios, con llegadas regulares y aleatorias, como estudio aparte |
   | 4 | Una política por red [A6] |
   | 5 | Cierre, análisis y escritura |

   Todo va en una rama aparte (`plan3`), a ciegas hasta el cierre y con todas las reglas subidas antes de la primera
   noche.
2. **Qué cambió con las críticas del 05.11.**
   - **El plan ahora busca mejorar el modelo, no solo explicar:** reloj de 2 s, mejoras de entrenamiento también con
     llegadas aleatorias, un modelo completo y una regla para citar al mejor modelo prerregistrado [A4].
   - **Todas las reglas estadísticas se fijan antes de ver ninguna referencia** [A5].
   - **"A ciegas" se puede comprobar:** los CSV decisivos quedan fuera de git hasta el cierre y cada mañana se sube
     solo su sha256 [A5].
   - **Se corrigieron siete fallas del código previsto** (B1, B7, B11, B13, B15, B20, B21): por ejemplo, contar dos
     veces a los no insertados, publicar mal el brazo reanudado o marcar como hecho un trabajo cortado.
   - **El calendario se rehízo** con la suma real de las tareas y el régimen conservador [A6].
3. **Costo.**
   - ~**1901 h-p** (~159 h de reloj) en **17 noches**, de la del día 4 a la del día 20. En el central: ~1506 h-p y 15
     noches (última, día 18).
   - **Código: ~18-19 días.** Es el cuello. Por eso el código va en el orden que mantiene la cola llena (ver "Orden").
   - **Total: ~26-27 días de trabajo** (el borrador decía 18-19).
4. **Qué no cambia.** Ningún veredicto entregado: el del 25.09 (congelado), la robustez v2.1, los niveles `dem_` de la
   entrega 3 y el diagnóstico del corredor (Anexo G). La rama no toca `plan2/` ni `TESIS/`.
5. **Qué se espera, honestamente** [prerregistro §15]:
   - **Con llegadas regulares:** V2 mejora P1 y P2; P3, P5 y la malla quedan en el ciclo mínimo; en P6, frente al fijo
     fino, la mejora probablemente desaparece, salvo que el reloj de 2 s la recupere [I].
   - **Con llegadas aleatorias hay margen real.** Sin reentrenar, IPPO entregado ya le gana al fijo instalado −12.0 % en
     P2 y −41.1 % en P6 (−16.7 % en mediana), pero pierde con el actuado en P1 (+8.0 %) [M
     `plan3/critica_resultados/RESUMEN.txt` §2, semillas de prueba]. Lo que decide es el fijo re-ajustado.
   - Puede salir que el actuado ajustado o la regla simple ganen. Eso también es un resultado.

### Qué puede mejorar y cuánto (ordenado por el efecto que se espera)

| # | Pieza | Efecto esperado | Base |
|---|---|---|---|
| 1 | Llegadas aleatorias con la entrada corregida | El mayor margen: IPPO entregado, sin reentrenar, −12.0 % (P2) y −41.1 % (P6) frente al fijo instalado; −8.3 % y −25.2 % frente al actuado | [M RESUMEN §2]; falta el fijo re-ajustado |
| 2 | V2 con llegadas regulares | P1 −5.5 a −7.4 %, P2 −9.3 a −10.8 %, P4 de FALLA a EMPATA, P6 −3.1 % frente al 15/10. El fijo fino recorta parte: P6 −3.5 %, P1 −1.3 % | [M diagnóstico y exploratorio, vía crítica de impacto; referencias] |
| 3 | Reloj de 2 s [A4] | Con llegadas aleatorias, una regla que reacciona pierde 12 % (P1) y 20 % (P6) por decidir cada 5 s en vez de cada 2 s | [M RESUMEN §1, la regla como sustituto de IPPO] |
| 4 | 400 episodios | ~1-3 % en el corredor: con V2 la validación todavía baja −2.5 % en el último tercio | [M RESUMEN §4; I] |
| 5 | Elegir con 16 semillas y por retraso total (C0) | En P2 el criterio mueve de −8.8 a −10.8 % | [M críticas del 04.11] |
| 6 | Observación nueva y limpiezas | Sin efecto medido; riesgo medido de romper la coordinación (+22.3 %) | [M exploratorio] |

### Qué cambió frente al plan del 04.11 (`analisis_mejora_2026-11-04/salida/programa.txt`)

| Pieza | Plan del 04.11 | Ahora | Por qué |
|---|---|---|---|
| Puertas | Factibilidad Poisson como puerta; Etapas 3-4 condicionales | Sin puertas: todo se corre y lo que era puerta se informa | Pedido de Fabian |
| Fijo de referencia | Rejilla de 5 s (P6: 15/10) | Barrido de 1 s con regla única y regla para ganadores frágiles (P6: 12/10 o 14/10) | Gana −3.5 % en P6; el 12/10 es frágil [M `plan3/referencias/salidas/top10_p6_2001-2010.csv`] |
| Espera para entrar en P6 | No estaba | Entrada corregida en lo nuevo y la celda P6e [A2] | 55 % del retraso del fijo es una cola de inserción [M] |
| Fijo por franja | Solo P1 y P2 | En todas las celdas | Los seis casos invierten la punta [M] |
| Actuado | Por defecto | Ajustado; veta FUNCIONA [A1] | Crítica de impacto del 04.11, omisión 4 |
| Control de selección | No estaba | C0: los checkpoints entregados re-elegidos sin entrenar | El entrenamiento es determinista [M `plan3/modelo/salidas/v2val8_vs_val2.txt`] |
| Semillas decisivas | 1001-1030 y 8001-8030 | Regulares 8001-8030 y 13001-13030 (120 para H1/H2); aleatorias 7001-7100 y 10001-10100 | En el corredor, 1001-1030 ya se usó con V2 [M] |
| Validación | 8 semillas | 16, cada 10 en todas las celdas [A3] | PENDIENTE por ruido en P6: 25 % con 8 [I] |
| Script de veredicto | Importar `veredicto.py` | `veredicto3.py` con funciones puras y su propia convergencia | `info_base` toma x[3] y no la media [M] |
| 400 episodios | Solo P2 y P6, con veredicto | P1-P6, regulares y aleatorias, sin veredicto, reanudando desde el 180 | El Cap. III prohíbe alargar solo algunas celdas [M l. 1492-1495] |
| Acción del modelo | "No cambiar la acción (decidir cada 1-2 s)" | Reloj de 2 s como variante prerregistrada [A4] | Evidencia nueva con llegadas aleatorias: +13.3 % en P1 y +23.0 % en P6 para una regla [M RESUMEN §1] |
| Reemplazo de V2 | "Si la ablación cumple su regla, la variante reemplaza a V2" | Regla de promoción por validación con semillas nuevas [A4] | Es el equivalente sin puertas |
| Etapa 4 | Una sola de las dos | Una sola: la política por red [A6] | Programa aprobado; el código es el cuello |
| Registro de escenarios | En `DERIVADOS` | Diccionario aparte y lanzador | `DERIVADOS` crea trabajos en plan2 [M] |
| Max-Pressure | Piloto del 28.09 | Código nuevo; solo descriptivo | El piloto no tiene código [M] |

---

## Reglas para todo el bloque

1. **Sin puertas.** Todo lo de este plan se corre. Ningún resultado decide si algo se corre o cómo se configura.
2. **A ciegas** [A5]. Las tandas decisivas se escriben en `plan3/ciego/`, fuera de git; sus logs dicen solo semilla y
   duración; cada mañana se sube solo su sha256. Nadie abre esos resultados hasta `plan3/listo/cierre.ok`.
3. **Nada se elige con semillas decisivas:** ni checkpoint, ni base, ni variante, ni referencia, ni número de semillas,
   ni qué modelo se cita.
4. **Prerregistro** [A5]:
   - **Parte A (todas las reglas):** commit, push, tag y correo al asesor antes de la primera noche (día 4).
   - **Parte B (sha256 de las referencias congeladas y valores de la mezcla):** antes de la primera noche con
     evaluaciones decisivas (día 14).
   - Enmiendas solo por error de código, trabajo imposible o algo ya anunciado; desde el día 14, solo errores de código.
5. **Aislamiento** (B1). Dos worktrees: `../demo_rl_plan3` (ejecución) y `../demo_rl_plan3_dev` (desarrollo). Nada
   escribe en `plan2/` ni en `TESIS/`. Protecciones en tres capas.
6. **Commits** solo a nombre de Fabian, sin línea de coautor (regla del proyecto). Fusión con commit de fusión.
7. **Las versiones no cambian:** Python 3.14.6, torch 2.14.0+cpu, SUMO 1.25.0, comprobadas antes de cada noche.

**Semillas** (detalle y tabla para la máquina en `PRERREGISTRO_borrador.md` §3; todas libres [M
`plan3/final/semillas/t3_semillas_plan3.txt`]):

| Uso | Llegadas regulares | Llegadas aleatorias |
|---|---|---|
| Bases | 42, 2042, 4042 (+14042 y 16042 en el modelo principal y en H8a) | iguales |
| Validación | 999…9999 (8) y 15001-15008 | iguales |
| Promoción [A4] | 15009-15024 | iguales |
| Ajuste de referencias | 2001-2003; las 10 mejores con 2001-2010; frágiles con 2001-2030 | 2001-2010; 10 finalistas con 2001-2030 |
| T1 decisiva | 8001-8030 (H1/H2: 8001-8120) | 7001-7100 |
| T2 decisiva | 13001-13030 (H1/H2: 13001-13120) | 10001-10100 |
| Puente y no regresión | 1001-1030 (puente) y 1001-1002 (no regresión) | — |
| Prueba final reservada | 11001-11030 | 12001-12100 |
| Humo | base 7 y 424301-424360 | iguales |

---

## Orden del trabajo

El código es el cuello (~18-19 días). Para que la cola no quede vacía, va primero lo que alimenta entrenamientos largos,
que no dependen de las referencias. Las referencias y las evaluaciones van después; `veredicto3` al final, porque no
decide nada hasta el cierre.

| Días | Código | Primera noche que lo usa |
|---|---|---|
| 1-2 | Infraestructura (0.1-0.5) | — |
| 3-4 | Opciones de entrenamiento, reanudación, generador (parte 1), prerregistro parte A | Día 4: V2 regular, ablación, sin mensajes |
| 5 | Escenarios nuevos (0.6) y C0 (1.4) | Día 5: llegadas aleatorias, P6e, C0, 400 episodios |
| 6-8 | Etapa 3: observación nueva, limpiezas, entropía, reloj de 2 s, completo, promoción | Día 8 |
| 9-12 | Referencias (0.7-0.12) | Día 12 (dos noches) |
| 13-14 | Evaluación: `evaluar3`, manifiesto, pasos de elección, chequeos, parte B | Día 14: evaluaciones decisivas |
| 15-16 | Perfil y mezcla | Día 16 |
| 17 | Política por red | Día 17 |
| 18-19 | `veredicto3` | — |

Según el modelo de costos, este orden termina el cómputo 2 noches antes que poner las referencias primero: día 20
frente a 22 en el conservador, y 18 frente a 20 en el central [I `orden_codigo_salida.txt`, en esta carpeta].

---

## Etapa 0. Preparación, infraestructura y referencias

### 0.1 Respaldo de los checkpoints (antes de cualquier otra cosa)
- **Qué se hace:** se copian `demo_rl/plan2/checkpoints` (6360 archivos) y `demo_rl_diag/plan2/checkpoints` (2640) fuera
  de los repositorios, con un manifiesto sha256.
- **Prueba:** el recuento y el sha256 de cada copia son iguales a los del origen.
- **Costo:** minutos. **Por qué:** no están en git y son la única copia de los 1080 checkpoints de C0 [M infra §3].

### 0.2 Worktrees y tag
- **Qué se hace:** `git tag -a entregado-2026-10-25 81378fb`; `git worktree add ../demo_rl_plan3 -b plan3 main`;
  `git worktree add ../demo_rl_plan3_dev -b plan3-dev plan3`. `plan3/.gitignore` con checkpoints, `**/tripinfo_*.xml`,
  `tmp_*/`, `cola/fin`, `cola/pausa`, `cola/reintentar.txt`, `insumos/c0_checkpoints/` y **`ciego/`**.
- **Prueba:** `git diff main...HEAD -- plan2 TESIS` vacío; `git status --ignored -- plan2 TESIS` vacío; la ruta más
  larga bajo 200 caracteres (154 en la ubicación propuesta [M]).
- **Costo:** 0.1 día.

### 0.3 Insumos con manifiesto
- **Qué se hace:** `plan3/p3_insumos.py` (~80 líneas) copia, sin escribir en el origen, los escenarios base, las
  políticas entregadas, los CSV de referencias en 1001-1030 (puente), los checkpoints de C0 y los de la V2 de
  `demo_rl_diag`.
- **Prueba:** cada sha256 igual al de su origen; 1080 `.pt` y 1080 `.json` de C0.
- **Costo:** 0.25 día.

### 0.4 Cola, protecciones y rutina de cada noche [B1]
- **Qué se hace** (a partir de los prototipos de `plan3/infra/prototipo/`):
  - `plan3/cola.py`: copia de `plan2/cola.py` con `RAIZ = plan3/` y estos cambios:
    - **antes de cada lanzamiento** comprueba que el árbol está limpio y coincide con `lanzamiento.sha256`, y guarda el
      commit y el hash en el registro del trabajo;
    - `--hasta HH:MM`: no lanza un trabajo cuya duración estimada (la da el generador) pase de esa hora;
    - un trabajo cuenta como hecho solo con código 0 **y sus salidas esperadas completas**; un huérfano sin salidas
      completas pasa a fallido;
    - reintentos, lista de bloqueados y aviso de dependencias inexistentes (como el prototipo).
  - `plan3/protecciones.py`, tres capas:
    1. comandos: desenvuelve `con_escenarios.py` y aplica las reglas del programa interno; semillas, bases, scripts y
       etiqueta salen del bloque JSON del prerregistro §3, cuyo sha256 debe coincidir con el de origin; `--salida`
       relativa bajo `plan3/` o absoluta dentro de `plan3/`; `plan2` y `TESIS` se buscan con límites de palabra;
    2. lista de trabajos: semillas por bloque de uso y nombres únicos (B5);
    3. git antes y después, con los ignorados: `git diff main...HEAD -- plan2 TESIS`, manifiesto de checkpoints, HEAD
       en origin, versiones de Python, torch y SUMO.
  - `plan3/p3_noche.py`: antes → `cola/fin` → cola → después → borrar tripinfo → respaldo de `plan3/checkpoints` →
    `cola/manifiesto_ciego.json` → resumen (solo terminados, fallidos y bloqueados).
- **Prueba:**
  - el 100 % de la lista generada pasa la capa 1, y los comandos malos se rechazan también a través del lanzador
    (hoy el prototipo rechaza 7 de 7 legítimos y deja pasar un `rl_ippo train` sin `--etiqueta` [M
    `critica_codigo/salidas/capa1_prototipo_vs_plan.txt`]);
  - una mini-cola de 4 trabajos; un trabajo corrido a propósito en `plan2/` detectado;
  - **un trabajo matado con `taskkill /F` y la cola reiniciada:** queda como fallido, no como hecho;
  - un trabajo que falla, con sus dependientes bloqueados; un reintento.
- **Costo:** ~500 líneas, 1.25 días (prototipos listos).

### 0.5 Registro de escenarios sin efectos laterales [B2]
- **Qué se hace:** `escenarios_plan3.py` (diccionarios `ESTOCASTICOS` y `NUEVOS`) y el lanzador `con_escenarios.py`,
  que los suma a `escenarios_plan2` solo dentro de su proceso. La cola llama `python ../con_escenarios.py .. <programa>`.
- **Prueba:** en una copia, `plan2/generar_trabajos.py` regenera el mismo `trabajos.jsonl` (sha256 `4EB09E8F...` [M]);
  evaluar, rl_ippo y barrer_fijo corren con un escenario de prueba [M `plan3/demanda/salidas/prueba_post.txt`]; el
  lanzador falla si un módulo ya estaba importado o si un nombre choca.
- **Costo:** 0.25 día.

### 0.6 Escenarios nuevos: llegadas aleatorias, entrada corregida y P6e [A2, B6]
- **Qué se hace:** `demanda_estocastica.py` (~150 líneas, a partir de `plan3/demanda/guiones/`): `rou_poisson`
  (`period="exp(q/3600)"`), `escalar_exp`, `demanda_esperada`, `por_periodo` y `preparar3`, que escribe `poi_P1`…`poi_P6`
  con `departLane="best"` y P6e.
- **Prueba:**
  1. cada periodo suma lo mismo que el caso regular;
  2. SUMO carga los 7 escenarios;
  3. la media de vehículos en 20 semillas de humo queda dentro de ±3 errores estándar (hecho en P1 [M]);
  4. **números comunes con `best`:** ids, salida deseada y `speedFactor` iguales entre fijo, actuado e IPPO por TraCI,
     2 semillas, **en `poi_P3`-`poi_P6` y P6e** (hoy medido solo en P1 y P6 con la entrada por defecto [M
     `plan3/demanda/salidas/prueba_ab.txt`]);
  5. dos semillas distintas dan llegadas distintas; el sha256 de los `.rou.xml` de `plan2/` no cambia;
  6. en P6e la espera para entrar del fijo queda bajo 1 s/veh (medido 0.30 [M]).
- **Costo:** 0.6 día; pruebas ~2 h-p.

### 0.7 Barrido fino del fijo, con puntaje por periodo [A1, B7]
- **Qué se hace:** `plan3/barrer_fino.py` (~200 líneas). Importa `Plantilla`, `configs_plantilla`, `desfases_malla3` y
  `evaluar_config` de `barrer_fijo.py`, sin cambiarlos.
  - **Lector propio por periodo:** no pasa `--tripinfo-output.write-undeparted` a `correr_sumo`. Asigna cada no
    insertado a su periodo por su salida programada (fin − departDelay) y excluye del total las filas con depart < 0.
    Así evita el doble conteo medido: 905 vehículos en vez de 827 y retraso 82.38 en vez de 80.08 [M
    `critica_codigo/salidas/write_undeparted_doble_conteo.txt`].
  - Regla de A1: gruesa desde 10 s, fina de 1 s alrededor de cada mínimo local (tope 3), desfases finos ±4 s, malla con
    sus 3 esquemas y `onda_oe`, desempate de las 10 mejores, **regla para ganadores frágiles** y, con llegadas
    aleatorias, 2001-2010 en gruesa y fina, umbral en errores estándar y 10 finalistas con 2001-2030.
  - **Fijo con verdes de 5 en 5:** los 3 mejores de la gruesa con desfases finos ±4 s.
  - Escribe con nombres nuevos (`plan3/barridos/...`, `plan3/<esc>_r10f.add.xml`); nunca `--instalar`.
- **Se aplica a:** P1-P6, los 12 niveles, D, P6e y `poi_P1`…`poi_P6`.
- **Prueba:** reproduce las filas y el ganador de `plan2/barrido_<esc>.csv` (P6: 3 de 3 [M]); dos corridas dan el mismo
  CSV; **en P6 10/10, que se traba, la suma por periodo es igual al total de `leer_tripinfo` sin write-undeparted**; el
  ganador jugado por TraCI reproduce su media; `plan2/` queda limpio.
- **Costo:** 1.1 días.

### 0.8 Fijo por franja (un plan por media hora) [B8]
- **Qué se hace:** `plan3/franja.py` (~50 líneas): dos programas y un WAUT por semáforo, sin `procedure`, con su
  instante limpio. `rl_corredor`: modo `franja` (~6 líneas); `evaluar.py`: `--brazo franja` (~3).
- **Prueba:** franja con plan 2 = plan 1 da el mismo tripinfo que el fijo de un plan; a los 1800 s el programa cambia
  alineado [M `waut_prueba.py`]; 0 cortes de verde sin ámbar; sumo directo = TraCI.
- **Costo:** 0.5 día.

### 0.9 Actuado ajustado [A1, B9]
- **Qué se hace:** `plan3/actuado.py` (~100 líneas): actuado con `<param>`, variante `delay_based` y variante
  coordinada con los desfases del fijo fino. **Descenso por coordenadas en cadena**, sin TraCI. `rl_corredor`: modo
  `actuado_aj` (~8 líneas).
- **Prueba:** la variante por defecto reproduce el actuado entregado (hecho: 9/9 y 6/6 [M]); cada parámetro mueve algún
  número; el log de SUMO no trae avisos; **sumo directo = TraCI también con `<param>` y con la variante coordinada**.
- **Costo:** 0.6 día.

### 0.10 Regla simple y Max-Pressure [B10]
- **Qué se hace:** `plan3/reglas.py` (~110 líneas, del prototipo): fábricas de `decidir` para el gancho de
  `rl_ippo.correr_episodio`. `evaluar.py`: `--regla` (~25 líneas).
- **Prueba:** con U = ∞ da el mismo tripinfo que el ciclo mínimo (sha256; hecho en P1 y P5 [M]); cada acción respeta la
  máscara; la presión es 0 con la red vacía.
- **Costo:** 0.75 día.

### 0.11 Trabajo "preparar" y escritura atómica [B13]
- **Qué se hace:** al inicio de cada noche, un trabajo "preparar" genera los `_actuado`, `_trivial`, `_actuado_aj` y los
  E2; las evaluaciones dependen de él. `comun.archivo_actuado` y `archivo_trivial` escriben a un temporal con el pid y
  reemplazan con reintentos (`barrer_fijo.reemplazar`).
- **Prueba:** 3 evaluaciones simultáneas del mismo escenario terminan sin error y el `.add.xml` queda igual byte a byte.
- **Costo:** 0.1 día.

### 0.12 Chequeos de reproducción y no regresión [B13]
- `veredicto.py --probar` pasa; la reproducción con `--plan2` y `--tesis` en copias da 45/45, 54/54 y 60/60 (hecho [M
  `plan3/veredicto/salidas/`]); `--v2` es igual a `smdp_crn` en P4 y P6 (hecho [M]).
- **No regresión de lo entregado** (después de tocar `evaluar.py`, `rl_corredor.py` y `comun.py`): fijo, actuado,
  ciclo mínimo y una política IPPO publicada, en 1001-1002, repiten dígito a dígito los parciales de `plan2/` en P1-P6.
- Semillas de las pruebas de esta tarea: humo (424301-424360) o las de no regresión.
- **Costo:** 0.25 día; ~3 h-p.

### 0.13 Prerregistro, parte A (día 4)
- **Qué se escribe:** `plan3/PRERREGISTRO.md`, parte A: el borrador de esta carpeta con las decisiones A1-A8. Contiene
  **todas** las reglas: referencias, hipótesis, familias, márgenes, semillas (con el bloque JSON), promoción y plantilla.
- **Quién y cuándo:** Fabian hace commit, push, tag anotado y correo al asesor con el sha256 **antes de la primera
  noche** (día 4).
- **Costo:** 0.25 día (el borrador ya está escrito).

### 0.14 Evaluación dentro de plan3 [B11]
- **Qué se cambia:** `plan3/evaluar3.py` (~150 líneas). Importa `evaluar` y `comun` sin cambiarlos y **tiene su propio
  ciclo por semilla** (usa las funciones de brazo de `evaluar`):
  - en las tandas decisivas escribe en `plan3/ciego/` y su log dice solo semilla y duración;
  - `--programa ARCHIVO --nombre X` da el brazo `fijo_<X>`;
  - guarda el retraso por media hora y los vehículos generados y no insertados por semilla;
  - **opción "colas en cero"** para la sensibilidad a3 (cortar mensajes ya se puede con `--perdida 1`).
- **Prueba:** un brazo de cada tipo en 2 semillas de humo; el CSV cae en `plan3/`; el nombre es el esperado; los dos
  periodos dan el total; con "colas en cero" apagada, el CSV sale igual; el log no trae métricas en modo ciego.
- **Costo:** 0.5 día.

### 0.15 Manifiesto
- **Qué se cambia:** `plan3/manifiesto.py` (100-150 líneas): para cada celda, tanda y brazo, la ruta del CSV y las
  semillas esperadas; los metas por base; los hashes de red y rutas. Prueba en seco con CSV sintéticos.
- **Costo:** 0.5 día. (`veredicto3` pasa a 5.0: no bloquea ninguna noche.)

### 0.16 Chequeos de cada noche y `lanzamiento.sha256`
- **Qué se cambia:** `plan3/chequeos_previos.py` (80-120 líneas). Cada tarde corre: identidad de `rl_ippo` con todo
  apagado (P1, 10 episodios), `nombres.py`, la búsqueda de semillas, la prueba en seco del generador y del manifiesto.
  Escribe `plan3/lanzamiento.sha256` del commit que va a correr.
- **Prueba:** si falta o no coincide, la cola no arranca.
- **Costo:** 0.25 día.

### 0.17 Prerregistro, parte B (día 14)
- **Qué se escribe:** `plan3/referencias_congeladas.json` (archivo y sha256 de cada referencia) y los valores finales de
  la mezcla con sus fuentes. Ninguna regla cambia.
- **Quién y cuándo:** commit, push, tag y correo antes de la noche del día 14.

### 0.18 Generador de trabajos [B20]
- **Qué se cambia:** `plan3/generar_trabajos3.py` (~450 líneas, por partes: entrenamientos el día 4, Etapa 3 el día 8,
  referencias el día 12 y evaluaciones el día 14). Por trabajo declara salidas esperadas, duración estimada,
  dependencias y prioridad (referencias primero). Los pasos que eligen la versión evaluada son trabajos; los pasos
  secuenciales van en cadena; toda evaluación de una versión elegida depende de todas las bases de su regla.
- **Prueba en seco:** el 100 % pasa la capa 1; las dependencias existen; la lista coincide con `costos_plan3.py`.
- **Costo:** 1.25 días en total (el borrador no lo contaba).

### 0.19 Pasos de elección [B21]
- **Qué se cambia:** `plan3/p3_elegir.py` (~120 líneas): publica la versión evaluada de cada brazo (mediana de 5, de 3,
  V2 vieja, C0, la mejor base al lado) con su etiqueta propia en el meta (B5).
- **Prueba:** con 5 bases elige la 3.ª; con 4 (una caída), la peor de las dos centrales; la política publicada es
  idéntica al checkpoint elegido.
- **Costo:** 0.25 día.

**Noches de las referencias (días 12 y 13):** 0.7-0.10 en todas las celdas, **161 h-p** (~13.5 h de reloj; no
dependen del régimen). Con prioridad 0 en la cola. Producen `plan3/referencias_congeladas.json`.

---

## Etapa 1. V2 en todos los casos, con el control C0 (código días 3-5; noches desde el día 4)

V2 queda fijada como base de todas las variantes, pase o no H1 (prerregistro §0).

### 1.1 Opciones nuevas de `rl_ippo.py` [B13]
- **Qué se cambia** (todas apagadas por defecto):
  - `--solo-descuento` y `--solo-exploracion` (ablación de V2; ~10 líneas);
  - `--guardar-estado`: **archivo aparte** `checkpoints/<tag>_epNNN.estado.pt` con Adam (y su contador de pasos),
    `random`, numpy global, torch y el `default_rng` de `sembrar` (~25 líneas). La política `.pt` no cambia, porque
    `Politica.cargar` usa `weights_only=True` [M `rl_ippo.py` l. 388-393];
  - al final del CSV, `val_<s>` y `val_total_<s>` de todas las semillas, `var_explicada`, `frac_forzadas`, `msg_edad` y
    `ent_coef` (~20 líneas).
- **Prueba:** con todo apagado, IPPO entregado y V2 en P1 dan 0 diferencias en el CSV y 12/12 tensores iguales [M
  `plan3/modelo/salidas/prototipo_aceptacion.txt`]; `--solo-descuento` más `--solo-exploracion` = `--v2`;
  `--guardar-estado` no cambia ningún número; **`evaluar.py` juega igual una política entrenada con la opción.**
- **Costo:** 0.5 día.

### 1.2 Reanudación y tasa con piso [B15] (antes de la primera noche)
- **Qué se cambia:** `--lr-horizonte N --lr-piso F` (~15 líneas, ya en el prototipo) y `--reanudar ESTADO` (~40
  líneas): carga el estado completo, **copia a la etiqueta nueva los checkpoints ≤ el episodio de partida y precarga
  `val_serie` y `val_total_serie`**.
- **Prueba (antes de la noche del día 4):**
  - en P1 y en P6, 20 episodios seguidos dan lo mismo que 10 + 10 reanudados (CSV, `torch.equal` en tensores y estado
    de Adam);
  - con validación cada 5, reanudar en el 10 publica la misma política y el mismo meta que la corrida seguida;
  - 400 episodios con N = 200 y F = 0.1 repiten los episodios 1-181 de la corrida de 200 (hecho en 10 [M
    `plan3/modelo/salidas/m4_identidad.txt`]).
- **Produce:** 3b sin repetir episodios, tramos de ≤ 5 h para los entrenamientos largos y reintentos desde el último
  estado.
- **Costo:** 0.75 día.

### 1.3 V2 en las 18 celdas, en P6e y en D
- **Qué se corre:** `rl_ippo.py train --v2 --criterio-val total --val-seeds <16> --eval-cada 10 --episodios 200
  --guardar-estado --etiqueta p3v2reg`.
  - P1-P6 y P6e con 5 bases [A3]; los 12 niveles con 3; **2715 y D con 5** (B23).
  - El corredor (P1, P2, 905, 1358 y 2715) y D **se reentrenan** [B12].
- **Prueba:** en el corredor, los tensores coinciden con los de `demo_rl_diag/plan2/checkpoints` (`torch.equal`; el
  sha256 del archivo no sirve porque `torch.save` guarda el nombre [M `critica_codigo/salidas/torch_save_nombre_y_estado.txt`]).
- **Costo (conservador):** ~180 h-p de entrenamiento con los niveles. El más largo, V2 en P6, 7.3 h (4.0 central), en
  2 tramos.

### 1.4 C0: IPPO entregado re-elegido sin entrenar [B12]
- **Qué se cambia:** `plan3/revalidar_c0.py` (120-160 líneas, del prototipo `plan3/modelo/scripts/revalidar.py`):
  valida con las 16 semillas los checkpoints entregados de las 18 celdas, elige por retraso total y publica con la
  etiqueta `p3c0` en el meta. Trabajos de ≤ 1 h.
- **Prueba:** 999 y 1999 dan dígito a dígito lo guardado (hecho en 4 checkpoints [M]); la política publicada es idéntica
  al checkpoint elegido.
- **Costo:** 0.5 día de código; ~65 h-p.

### 1.5 Ablación de V2 (P4 y P6) y V2 sin mensajes (P1, P2 y P6)
- `--solo-descuento` y `--solo-exploracion`, 3 bases, en P4 y P6 (~58 h-p); `--variante local --v2`, 3 bases (~34 h-p).

### 1.6 Evaluaciones
- **Qué se corre:** `evaluar3`, T1 (8001-8030) y T2 (13001-13030). Brazos: todas las bases de V2; la versión evaluada
  de C0, de la V2 vieja y del IPPO entregado; las referencias (fijo fino, fijo de verdes de 5 en 5, fijo entregado,
  franja, actuado, actuado ajustado, ciclo mínimo, regla simple y MP; en los niveles: fijo fino, fijo desde 10 s, fijo
  entregado, ciclo mínimo, actuado y actuado ajustado); ablaciones y V2 sin mensajes.
- **H1 y H2:** V2 (de 42, 2042 y 4042), C0 e IPPO entregado también en 8031-8120 y 13031-13120, en P1-P6 y la malla con
  6525 veh/h (~21 h-p).
- **Puente:** V2 (de 42, 2042 y 4042), V2 vieja y C0 en 1001-1030, frente al fijo entregado y al IPPO entregado (sus
  CSV se reutilizan).
- **R0.3:** la rotonda con `--edgedata-output`, semillas de humo.
- **Costo:** ~110 h-p (conservador). Desde la noche del día 14.

---

## Etapa 2. Llegadas aleatorias, con y sin mensajes; perfil; mezcla

### 2.1 V2 con llegadas aleatorias, con y sin mensajes
- **Qué se corre:** en `poi_P1`…`poi_P6`, `--v2 --criterio-val total`, 16 semillas, 200 episodios,
  **`--guardar-estado`** y `--etiqueta p3v2poi`. Con mensajes, 5 bases; sin mensajes (`--variante local`), 3.
- **Prueba:** humo de 2 episodios por caso; números comunes entre dos brazos; costo por episodio ≤ ×1.15 del regular
  (medido +3 a +13 % [M]).
- **Costo:** ~140 h-p (conservador). El más largo, P6, 7.8 h en 2 tramos (4.2 central). Desde la noche del día 5.

### 2.2 C0 con llegadas aleatorias
- Los checkpoints de la V2 regular (42, 2042 y 4042) re-validados con llegadas aleatorias. **En P6 se usan los de P6e**,
  para no mezclar el cambio de entrada. Descriptivo. ~30 h-p.

### 2.3 Evaluaciones con llegadas aleatorias y transferencias
- **Qué se corre:** T1 (7001-7100) y T2 (10001-10100). Brazos: todas las bases de V2 con y sin mensajes; la versión
  evaluada de la V2 regular (en P6, la de P6e), de C0 con llegadas aleatorias y del IPPO entregado; las referencias
  re-ajustadas (fijo fino, franja, actuado ajustado y regla) y además fijo entregado, actuado por defecto, ciclo mínimo
  y MP.
- **Transferencia de vuelta:** la V2 aleatoria jugada con llegadas regulares (P6 en P6e).
- **Secundarias:** retraso por media hora; en P6, mediana y proporción de episodios muy malos.
- **Prueba:** números comunes en cada celda y tanda.
- **Costo:** ~156 h-p de evaluación (conservador; incluye perfil y mezcla). **H0** (la antigua puerta) se responde aquí.

### 2.4 Perfil dentro de la hora (P1 y P3) [A7, B19]
- `rou_perfil_poisson` (bloques de 600 s, mismo total); fijo de un plan (decide), fijo por bloques (WAUT de 6
  programas), actuado ajustado, regla, ciclo mínimo, V2 con perfil (3 bases) y la V2 aleatoria sin perfil.
- **Prueba:** conteos por bloque como se esperaba en 20 semillas de humo (hecho en P1 [M]); nadie traba la red en el
  bloque punta.
- **Costo:** 0.5 día; ~33 h-p.

### 2.5 Mezcla de Lima y arranque lento (P1 y P3) [A7]
- `con_mezcla`: una `vTypeDistribution` con id `auto` reemplaza al vType (los flujos no cambian); JICA 2013 sin camiones
  con el transporte público repartido por la flota ATU 2021; parámetros de SUMO por clase (combi y micro supuestos
  [S]); demanda en vehículos equivalentes (×0.84 [I]); variante de evaluación con `startupDelay` 0.5 s.
- **Prueba:** composición dentro de ±2 errores estándar en 20 semillas; números comunes; nadie traba la red.
- **Costo:** 1 día; ~39 h-p. **Riesgos:** no hay conducción medida en Lima [L]; `comun.plazas_carril` supone 7.5 m por
  vehículo [I, se declara].

---

## Etapa 3b. 400 episodios: estudio aparte, sin veredicto

- **Qué se corre:** P1-P6, bases 42, 2042 y 4042, **reanudando desde el episodio 180** hasta el 400, validación cada 10,
  `--etiqueta p3e400`; **también con llegadas aleatorias** (`p3e400poi`, desde la V2 aleatoria) [A4].
- Un paso aparte publica el **"200 con piso"** (`p3piso200`): el mejor checkpoint ≤ 200 de la corrida reanudada, con
  los ≤ 180 copiados. Otro publica, sin costo, **"400 eligiendo entre 20"** (ep. 20, 40, ..., 400).
- **Produce:** H9 y los descriptivos de la tasa; no cambia ninguna etiqueta.
- **Costo:** ~172 h-p (conservador; 67 regulares y 105 aleatorias). P6 dura 8.0 h en el conservador, en 2 tramos (4.4
  central); sin reanudar serían 13.2 h. Desde la noche del día 5.

---

## Etapa 3. Observación nueva, limpiezas, reloj de 2 s y modelo completo (código días 6-8)

"Primero en D" significa que D entra primero a la cola y que las ablaciones se hacen en D (~20 min por base). No es una
puerta.

### 3.1 Observación cercana (M3) [B14]
- `--obs-cercana 75`, del prototipo `plan3/modelo/code_m/` (~85 líneas): E2 de 75 m por carril de acceso y el tramo del
  giro a la izquierda (archivo generado por "preparar"); por acceso, vehículos cerca detenidos y en movimiento, espera
  del primero y marca de giro bloqueado; por lado, la salida real del enlace en una ranura nueva. Dimensión 31 → 49
  (53 → 73 en la malla). `evaluar.brazo_profundo` lee `opciones.obs_cercana`.
- **Prueba:** apagada, 0 diferencias; los E2 no cambian la simulación; en 2715 la marca está activa el 11-13 % del verde
  de C2_C1 (frente al 12 % de `bloqueo.md`) [M]; costo ≤ ×1.35; `evaluar.py` juega la política de dimensión 49.
- **Costo:** 0.75 día.

### 3.2 Limpiezas de PPO (M7) y 3.3 brazo de entropía
- `--norm-valor` (~35 líneas), `--sin-forzadas` (exige `--v2`, ~15) y `--msg-cada-paso` (~10); entropía con
  `--hiper ent=0.03 --ent-final 0.003`.
- **Prueba:** apagado, 0 diferencias; con `--sin-forzadas`, intervalos de 5, 13 o 18 s o el cierre; con
  `--msg-cada-paso`, edad del mensaje 0.0 s (hoy 1.9-2.0 [M]); la columna `ent_coef` sigue el calendario.
- **Costo:** 0.6 día.

### 3.4 Reloj de 2 s [A4, B24]
- **Qué se cambia:** `--paso-decision K` (~25 líneas): decide y publica mensajes cada K s una vez cumplido el verde
  mínimo. **La unidad del descuento de V2 y la normalización de la recompensa siguen en 5 s** (hoy las dos usan
  `PASO_CONTROL` [M `rl_ippo.py` l. 624 y 854]). Va con `--sin-forzadas`.
- **Prueba:** con `--paso-decision 5`, 0 diferencias en CSV y tensores; con 2, los verdes pueden durar 10, 12, 14...
  s; la recompensa por segundo es la misma con los dos relojes en un episodio de humo.
- **Costo:** 0.75 día. Por episodio, ×1.4 al entrenar y ×1.15 al jugar [S: la regla reactiva midió ×1.1-1.2].

### 3.5 Modelo completo y promoción [A4, B25]
- **Modelo completo:** `--v2 --obs-cercana 75 --norm-valor --sin-forzadas --msg-cada-paso --episodios 400
  --lr-horizonte 200 --lr-piso 0.1 --paso-decision 2`, etiqueta `p3completo` (`p3completopoi`). Sin código nuevo.
- **Promoción:** `plan3/p3_promocion.py` (~60 líneas): re-valida la versión evaluada de cada candidato de la celda en
  15009-15024 y aplica la regla del prerregistro §12. Escribe `plan3/promocion.json` con su sha256 antes del cierre.
- **Costo:** 0.3 día.

### 3.6 Trabajos (3 bases cada uno, salvo donde se dice; D entra primero)

| Brazo | Casos | Llegadas | Para qué |
|---|---|---|---|
| M3 | D y 2715 (5 bases), P1, P2, P3, P6 | regulares | H8a (2715, P2, D) y H8c (P1, P3, P6) |
| M3 | P1-P6 | aleatorias | H8b |
| M7 por separado | D | regulares | Descriptivo |
| M7 junto | D, P2, P6 | regulares | H12 (P2, P6) |
| Entropía | P1, D | regulares | Descriptivo |
| Reloj de 2 s [A4] | D, P1, P2, P6 | regulares | H14 |
| Reloj de 2 s [A4] | P1, P2, P6 | aleatorias | H14 |
| Modelo completo [A4] | P1, P2, P4, P6 | regulares | H15 y promoción |
| Modelo completo [A4] | P1-P6 | aleatorias | H15 y promoción |
| a3: colas en cero, mensajes cortados | V2 y M3; regulares en D, 2715, P1, P2, P3, P6; aleatorias en P1-P6 [A4] | las dos | Descriptivo |

- **Evaluaciones:** regulares en T1 y T2 regulares; aleatorias en T1 y T2 aleatorias.
- **Costo (conservador):** ~669 h-p. Los más largos: el modelo completo con llegadas aleatorias en P6, 26.3 h por base
  en 6 tramos (14.4 central), y M3 aleatoria en P6, 10.5 h en 3 tramos. Desde la noche del día 8.

---

## Etapa 4. Una política por red (código día 17) [A6, B16]

- **Qué se cambia:** en `rl_ippo.py`, `--escala-demanda a,b --curriculo K` (~15 líneas en el prototipo): cada episodio
  sortea `--scale f` con f ~ U(a, b); validación en 3 niveles (8 semillas cada uno, cada 20 episodios) por la media
  geométrica (~35 líneas); `--norm-valor` con media móvil rápida, cuyo β se fija con un piloto de humo (base 7, 20
  episodios) y una enmienda anunciada.
- **Qué se corre:** corredor, red y malla, 3 bases, 600 episodios, llegadas regulares, entrada de siempre, en tramos de
  ≤ 5 h. Se evalúa en cada nivel de su red en T1 y T2 regulares, frente a la V2 de cada nivel (Etapa 1).
- **Prueba:** `--scale 0.5` reproduce `dem_corredor_t905` [M]; la columna `escala` sigue el sorteo; la validación
  devuelve la media geométrica; apagado, 0 diferencias.
- **Costo:** 1 día; ~73 h-p (conservador). La malla, ~13.7 h por base en el conservador [I], en 3 tramos.
- **Corredores de 3-5 semáforos:** fuera, salvo que Fabian los elija en A6 (1.75 días de código, ~55 h-p; B17).

---

## Etapa 5. Cierre, análisis y escritura

### 5.0 `veredicto3.py` (días 18-19) [B11]
- 550-750 líneas, a partir de `plan3/veredicto/guiones/prototipo_veredicto3.py` (sus 20 pruebas pasan hoy [M]). Importa
  solo funciones puras de `veredicto.py` y `consolidar.comparar`, e inyecta `demanda_esperada`.
- Propias: `serie_criterio` (`x[-1]` de `val_total_serie`), `base_mediana_n` (con la regla de número par),
  `comparar` (**rechaza semillas que faltan y que sobran**), `acuerdo`, `sentido` (criterio de A5, emparejado por base),
  `holm`, `no_inferior` con tres lecturas, intersección-unión para H1, `diferencia_no_pareada` (H6),
  `generados_iguales`, `igual_ciclo_minimo`, número único con `sintesis_plan.indice_geo` [M l. 106].
- Modos: `--probar` (datos sintéticos) y `--final` (exige `listo/cierre.ok`; la prueba final con candado de hash).
- **Prueba:** las 20 del prototipo; la V2 de P6 da meseta 3.19 % y estabilidad 0.00 %; reproduce las etiquetas de la
  robustez en P1-P6 y en los 12 niveles; rechaza un CSV con una semilla de más; se niega a escribir fuera de `plan3/`.

### Amenaza y defensas del cierre y de la prueba final
**Repositorio.** El `origin` de la rama `plan3` es `https://github.com/Fabian9533/demo_rl_semaforo.git` (veredicto3
lo compara con `git remote get-url origin`; https o ssh, con o sin `.git`).

Lo que se cuida, en este orden:
- **(a) Que se pueda recuperar.** Ningún error honesto deja el cierre o la prueba final imposibles para siempre. Los
  dos pasos que no se deshacen son el push del commit del cierre y el push de `listo/holdout.ok`: cada uno tiene un
  preflight (`python veredicto3.py --preflight cierre|holdout`) que corre, con HEAD como si ya estuviera empujado, las
  mismas comprobaciones que después, y nombra el error antes del push. Un merge de código en `plan3` en cualquier
  momento (`plan3-dev` → `plan3`, o `plan3` → otra rama y de vuelta) no rompe nada: solo cuentan los commits que
  cambian lo protegido (el sello, `cierre.ok`, las mañanas, `holdout.ok`, los reemplazos y las enmiendas), y un merge
  que trae lo mismo que uno de sus padres no cuenta. Si `cierre.ok` se barre por error a un commit de la mañana sin
  el sello, el cierre es el commit siguiente que traiga el sello con `cierre.ok`.
- **(b) Que una manipulación se vea desde afuera.** El testigo de afuera es el correo al asesor con los hashes que
  imprimen las herramientas en cada paso clave: el commit del cierre y el sha256 del sello (`--preflight cierre` antes
  del push y `--final` después), el commit de `holdout.ok` y el sha256 de la lista (`--preflight holdout`), y el
  commit del candado con el sha256 del candado y de la salida (`--verificar-prueba-final`, después del push). Quien
  tenga esos correos y el repositorio de GitHub ve si la historia empujada es la de los hashes.
- **Límite declarado.** Fabian es el único que trabaja en el repositorio y no protege la rama ni los tags en GitHub.
  Sin esa protección, un push forzado (o borrar y volver a crear `plan3`) que se mire desde un repositorio que nunca
  vio la rama de antes (un clon nuevo, o el de ejecución después de borrar su reflog y `refs/veredicto3/visto`) no se
  distingue de la historia honesta: entre dos correos (por ejemplo, las mañanas antes del cierre) solo el reflog del
  repositorio de ejecución lo delata, y quien lo borra lo borra. También quedan fuera del código: correr un CSV a mano
  con `P3_USO` puesto a mano y regenerar un CSV antes de su primera mañana (§14: "nada demuestra que nadie miró").
- **Opcional (no se hace).** Proteger `plan3` en GitHub (sin push forzado ni borrado) y prohibir un tag `plan3`
  agregaría que esa reescritura no se pueda hacer en el remoto: el testigo dejaría de depender del reflog local entre
  dos correos. veredicto3 ya se niega, sin protección, si el remoto tiene `refs/tags/plan3`, `refs/plan3` o
  `refs/remotes/plan3`.

Lo que el código hace de verdad (con la prueba que lo muestra: `--probar`, `pruebas/ver/prueba_protocolo.py`):
- `--final` y `--prueba-final` leen todo desde `origin/plan3` traída con un fetch explícito de `refs/heads/plan3` (no
  desde HEAD): el commit del cierre, las mañanas, `holdout.ok` y el candado. Lo protegido del disco tiene que ser lo
  de `origin/plan3` (commiteado y empujado), y HEAD tiene que estar en su línea.
- Se niegan con: un `origin` que no es el de arriba; un remoto con una referencia ambigua `plan3`; un tag del
  prerregistro distinto del remoto; un repositorio superficial; una rama empujada reescrita después de tener datos
  decisivos, si este repositorio la vio antes (el reflog de `origin/plan3` y `refs/veredicto3/visto`, que
  `protecciones.py antes` y `despues` guardan cada noche); un sello, una mañana, un reemplazo o `holdout.ok` en una
  rama lateral; un CSV del manifiesto fuera de su ruta canónica o listas que no son las del generador; un CSV que
  cambió después de su mañana; un reemplazo que no es una corrida rehecha declarada antes de correrla; una decisión de
  promoción que no es la que da `p3_promocion` con sus CSV, o que cambió sin una enmienda; la tabla de semillas
  distinta de la del tag; código del análisis sin commitear; y, en la prueba final, CSV que no escribió la cola
  después de `holdout.ok`, otra lista, un `holdout.ok` cambiado o un candado que ya existió (en disco, en la historia,
  en otra rama o en el reflog).
- Sin red (o sin credenciales), `--final` y `--prueba-final` se niegan con un mensaje claro y no se quedan colgados
  (tiempo máximo); `protecciones.py antes` solo avisa: la noche corre igual.

### 5.1 Cierre (día 20 en el central, 21 en el conservador)
En el worktree de ejecución (`demo_rl_plan3`, rama `plan3`, desde `plan3/`), en este orden:
1. Después del commit y el push de la última mañana: `protecciones.py despues` sobre la última noche. Una corrida
   rehecha por un error de código (§14) ya tiene su enmienda: el generador le da id y CSV nuevos (`_r2`) y
   `cola/reemplazos.json` la declara (`viejo`, `nuevo`, `motivo`, `fecha`) en un commit empujado **antes** de la noche
   que la corre; la salida vieja ya estaba en una mañana anterior y se conserva.
2. `python manifiesto.py cierre`: revisa los CSV, las rutas, que la lista y el manifiesto sean los del generador, la
   historia de las mañanas y los reemplazos, y escribe el sello `cola/manifiesto_cierre.json`. Si se niega, se corrige
   la causa y se corre otra vez; nada se sella a mano.
3. Fabian crea `plan3/listo/cierre.ok`.
4. **Un solo commit** con el sello, `listo/cierre.ok`, `cola/` y los CSV de `ciego/` (`git add -f plan3/ciego`).
5. `python veredicto3.py --preflight cierre` (antes del push): las comprobaciones de `--final` con HEAD como ancla.
   Si dice algo, se corrige con otro commit (sin `--amend`) y se repite.
6. `git push origin plan3` (sin forzar). Enseguida, `python veredicto3.py --final` y el correo al asesor con el texto
   que imprime (el commit del cierre, `origin/plan3` y el sha256 del sello): es el testigo de afuera del cierre.
- **Nunca** se commitea el sello en un commit de la mañana (un `manifiesto.py cierre` corrido antes de tiempo deja
  `cola/manifiesto_cierre.json` en disco: queda fuera del commit). Desde la parte A, nada de `--amend`, `rebase`,
  `reset` ni push forzado sobre `plan3` después de un push. Después de `cierre.ok`, `protecciones` no lanza trabajos
  ciegos (salvo los de la prueba final), y nunca relanza uno cuyo CSV ya está en una mañana.
- Ensayo de punta a punta, con estos programas y un `origin` de prueba: `plan3/pruebas/ver/prueba_protocolo.py`.

### 5.2 Veredicto y tablas
- `veredicto3` escribe en `plan3/salidas/`: `veredicto3_celdas.csv` (T1, T2 y citable por celda, con el modelo citado),
  `veredicto3_bases.csv`, `veredicto3_hipotesis.csv` (con Holm y lecturas) y `veredicto3.md` (la tabla simple).

### 5.3 Prueba final reservada (solo si hace falta) [A3]
Una sola vez (~22 h-p, ~2 h), en este orden; la noche final no corre antes del paso 4:
1. **Enmienda como código y lista**, en un commit con push: las tandas de uso `final` en `generar_trabajos3.TANDAS`
   (11001-11030 regulares, 12001-12100 aleatorias), una parte nueva en `PARTES` (fuera de `PARTES_PLAN`) con los
   brazos exactos, y la lista `plan3/listo/lista_final.json` (`{"comparaciones": [{celda, escenario, tanda, a, b}]}`;
   `a` y `b` = `{"tipo": ..., "base": 42}`, `base` como número y solo si es una base); antes,
   `python generar_trabajos3.py --partes <las de cola/partes.txt>,<la parte nueva>` (lo de antes queda igual: solo se
   agregan los trabajos y los CSV de la prueba final).
2. **Resello:** `python manifiesto.py cierre` (los CSV de la prueba final no se sellan), commit del sello y push.
3. `python veredicto3.py --holdout listo/lista_final.json`: valida la lista (cada brazo en el manifiesto, en su tanda
   final, con el bloque completo de semillas) y escribe `listo/holdout.ok` en UTF-8 con una sola línea. **Nunca** con
   `>` de PowerShell (escribe UTF-16). Commit de `holdout.ok`.
4. `python veredicto3.py --preflight holdout` (antes del push) y, si no dice nada, `git push origin plan3` **antes de
   la noche final**, y el correo al asesor con el texto que imprime. La cola no lanza un trabajo `final` si
   `holdout.ok` no está commiteado, igual al de HEAD, empujado y con el hash de la lista; si ya los rechazó, sus ids
   van en `cola/reintentar.txt`.
5. La noche final (por la cola: veredicto3 exige que cada CSV final lo haya escrito un trabajo lanzado después de
   `holdout.ok`, según `cola/estado.json`); a la mañana, su commit (el manifiesto de la mañana y `cola/estado.json`,
   sin el sello) y push.
6. `python veredicto3.py --prueba-final listo/lista_final.json`: escribe primero `salidas/veredicto3_prueba_final.csv`
   y después `listo/holdout.candado` (con las filas, los sha256 y el código). Un corte antes del candado deja volver a
   correrla; después, no.
7. Enseguida, un commit del candado, de esa salida y de los CSV de la prueba final (`git add -f`) y push; después
   `python veredicto3.py --verificar-prueba-final` (vuelve a calcular la prueba final commiteada, se niega si no da lo
   mismo) y el correo al asesor con el texto que imprime (el commit del candado y sus sha256). `--final` hace la misma
   verificación. Nunca se borran ni se editan `holdout.ok`, la lista ni el candado.
- Lo que se cite de ella dice "elegido después de ver T1 y T2; una tanda". Nunca juzga lo prerregistrado.

### 5.4 Escritura [A8]
- **Anexo nuevo** con la tabla simple y todo el detalle.
- **Sección corta en el Cap. V, sin tablas nuevas:** la pregunta, la respuesta, el criterio de lectura y una figura con
  las bandas de la Figura 5.3. Sigue el programa aprobado ("no agregar tablas al Cap. V").
- Frases del resumen y las conclusiones: la plantilla del prerregistro §17. La etiqueta entregada y la nueva van juntas.
- Reglas de claridad: sin etiquetas de código en el capítulo (V2 se escribe "IPPO con mensajes, corregido"); cada cifra
  con su archivo y sus dos tandas.
- **Revisión en cascada:** Cap. III, l. 1425-1432 (llegadas aleatorias fuera del plan) y l. 260 (cada 5 s), con un
  párrafo que remite al segundo estudio; `recomendaciones.tex` l. 84-92 y 270-279; la Sección 5.5.1 queda como está
  (si la V2 re-elegida difiere, se muestran las dos); **la frase "en P3-P5 el fijo es el ciclo mínimo" se corrige en
  P4, con confirmación de Fabian** [A8].
- La V2 no va en la misma tabla que DQN y MAPPO, que no recibieron la corrección.
- Resumen, abstract, objetivos, Cap. I y conclusiones cambian solo con la confirmación de Fabian, cambio por cambio.
- La tesis se compila en `demo_rl`. **Costo:** ~4 días más 1 de revisión.

### 5.5 Fusión
- Fabian fusiona `plan3` en `main` con **commit de fusión** (sin squash ni rebase), para que los tags del prerregistro
  sigan en la historia. Antes, `git diff main...HEAD -- plan2 TESIS` debe estar vacío.

---

## Costo total

| Etapa | h-p conservador + 10 % | Central | Tramo más largo (conservador) |
|---|---|---|---|
| 0 Referencias | 161 | 161 | 4.3 h (reglas aleatorias de P6) |
| 1 V2 regular, C0, ablación, sin mensajes, niveles | 451 | 354 | 4.2 h (tramos de V2 en P6) |
| 2 Llegadas aleatorias, perfil, mezcla | 374 | 310 | 3.9 h |
| 3b 400 episodios (reanudado) | 172 | 136 | 4.3 h |
| 3 Observación, limpiezas, reloj, completo, promoción | 669 | 495 | 5.0 h (tramos del completo) |
| 4 Política por red | 73 | 49 | 4.6 h |
| **Total sin la prueba final** | **1901 (~159 h de reloj)** | **1506 (~126 h)** | 17 noches (15 en el central) |
| Prueba final (si se usa) | 22 | 19 | 1.4 h |

| Variante (conservador) | h-p | Última noche |
|---|---|---|
| Recomendada | 1901 | día 20 |
| Sin las piezas de A4 | 1342 | día 17 |
| Sin reloj de 2 s | 1735 | día 18 |
| Sin modelo completo ni promoción | 1563 | día 18 |
| Modelo completo con 200 episodios | 1753 | día 18 |
| 3 bases en el modelo principal | 1800 | día 19 |
| Validación con 8 semillas | 1552 | día 18 |
| 60 semillas por tanda con llegadas aleatorias | 1785 | día 19 |
| Etapa 4 con las dos | 1956 | día 20 (y +2 días de código) |

**Código:** ~18-19 días (detalle en `CRONOGRAMA.md`).

---

## Riesgos principales (y qué se hace)

| Riesgo | Qué se hace |
|---|---|
| Con el fijo fino, la mejora de V2 en P6 desaparece (H3 improbable [I]) | Se prerregistra. El fijo de verdes de 5 en 5 separa el límite del reloj; el reloj de 2 s puede recuperarla [A4] |
| Con llegadas aleatorias, un −3 % no se confirma en las dos tandas | 100 semillas por tanda y el criterio de sentido por signo: H5 tiene potencia 0.59 con −3 % y 1.00 con −5 % [I] |
| En P6, con llegadas aleatorias, colas encadenadas dominan la media | Secundarias prerregistradas: mediana y proporción de episodios muy malos |
| PENDIENTE por ruido (P6 regular ~10 %) | Se informa ese número junto a la etiqueta provisional; no se agregan episodios |
| El actuado ajustado o la regla le ganan al modelo | Es un resultado, con sus lecturas obligadas |
| La observación nueva o el modelo completo rompen la coordinación (+22.3 % de un antecedente [M]) | Ablaciones, no inferioridad y la regla de promoción (solo se cita si gana en validación por ≥ 1 %) |
| El reloj de 2 s cambia la escala del aprendizaje | Descuento y recompensa siguen en 5 s; prueba de 0 diferencias con reloj de 5 s |
| Se promueve una variante que ganó por ruido | Validación de promoción en semillas nuevas y margen de 1 %; el examen es independiente |
| Un trabajo escribe en `plan2/` (18 caminos encontrados [M infra]) | 3 capas de protección y respaldo previo |
| La cola corre código editado a medias | Dos worktrees y verificación del árbol antes de cada lanzamiento |
| Un reinicio de Windows corta trabajos sin dejar error | Éxito solo con salidas completas; Windows Update pausado; reintento desde el último estado |
| El determinismo depende de las versiones | No se actualiza nada; se comprueban antes de cada noche |
| Se atrasa el código (el cuello) | El orden mantiene la cola llena; cada día de atraso corre el final un día |
| La mezcla no tiene conducción medida en Lima | Se presenta como sensibilidad |
| Exceso de datos en la tesis (crítica del asesor) | Sin tablas nuevas en el Cap. V; el detalle al anexo [A8] |
| La política por red converge al ciclo mínimo o no converge | Es un resultado; β se fija antes de lanzar |
| Rutas largas en Windows | El generador rechaza rutas de más de 200 caracteres |

---

## Lo que no se hace (y por qué)

- **M6, la política anclada al fijo:** cambia la identidad del método y no está en las etapas aprobadas.
- **Corredores de 3-5 semáforos:** el programa aprobado pedía una sola de las dos piezas de la Etapa 4 [A6].
- **Paso de simulación de 0.5 s:** reabre toda la comparación sin atacar ninguna causa de falla [M
  `plan2/diag_corredor/sumo.md`, vía programa].
- **Más niveles deterministas u otra red del mismo tipo:** repiten el techo.
- **Ganarle al ciclo mínimo en P3 y P5 con llegadas regulares:** es el óptimo medido (por eso el modelo completo no va
  en P3 y P5 regulares).
- **Repetir lo que ya falló, solo:** normalizar colas (V1), MAPPO con la recompensa de toda la red (V4), cobrar la
  espera para entrar sin mostrarla (INS), γ 0.99, validar con más semillas como única mejora.
- **Recompensa de presión** (PressLight, MPLight): en 2715 el carril bloqueado mantiene la presión alta [I]; en P3 y P5
  el techo es el ciclo mínimo. Se escribe en la tesis porque el jurado lo puede preguntar.
- **Lote de varios episodios por actualización de PPO:** sin medición propia, solo literatura [L Yu et al. 2022]; queda
  como trabajo futuro.
- **Un brazo aparte para el efecto de la tasa** (`--lr-horizonte 100`): la pregunta no es central y H9b queda
  descriptiva.
- **Quitar P3 y P5 del 400 regular para ahorrar:** no hace falta y reabriría la crítica de alargar solo algunas celdas.
- **Bahía o fase protegida en 2715, cruce real de Lima o corredor de Colonia:** fuera de plazo o ya aislado por D.
- **Más episodios solo donde no convergió:** el Cap. III lo prohíbe.
- **Rutas pre-generadas por semilla:** no hacen falta [M]; quedan como plan B costeado (B6).

---

## Cómo se atiende cada crítica

### Críticas del 05.11 (sobre el borrador de este plan)

**Lente de método**

| Crítica | Gravedad | Dónde se atiende |
|---|---|---|
| La parte B fijaba hipótesis y márgenes con las referencias a la vista | alta | Todas las reglas en la parte A, antes de la primera noche; la parte B solo agrega hashes y valores de la mezcla (A5 #9; prerregistro, encabezado) |
| "A ciegas" no se podía demostrar | alta | CSV decisivos en `plan3/ciego/` fuera de git, logs sin métricas, solo sha256 cada mañana; enmiendas restringidas (A5 #8 y #10; B4; prerregistro §14) |
| Referencias aleatorias ajustadas con 3 semillas | media | 2001-2010 en gruesa y fina, umbral en errores estándar, 10 finalistas con 2001-2030 (A1; B7; +59 h-p) |
| Poca potencia de H1; Holm en una afirmación conjunta | media | 120 semillas por tanda para H1 y H2; tres lecturas; intersección-unión para H1 global (A3; A5 #4-5; prerregistro §8) |
| V2 de 5 bases frente a C0 de 3 | media | H1, H2, 2×2 y puente con la V2 de 42, 2042 y 4042; H2 emparejada por base (B21; prerregistro §6) |
| Afirmaciones de método sin variación entre entrenamientos | media | Sentido en toda afirmación de método, emparejado por base; criterio por signo elegido con su potencia (A5 #3; prerregistro §7) |
| Qué se cita y cómo conviven las cifras | media | Plantilla de redacción, número único frente al fijo fino con P6 y al lado el entregado, etiquetas juntas, sin `sintesis_plan.py` (A8; prerregistro §7 y §17) |
| Convergencia con llegadas aleatorias no medida | media | Medida por la crítica de impacto: 0.0 % (P1) y 2.2 % (P6) con 16 semillas (prerregistro §6) |
| Ganador frágil del fijo fino (12/10 frente a 14/10) | media | Regla de desempate con 2001-2030 y secundaria en P6 (A1; prerregistro §4-§5) |
| Potencia conjunta de H5 no mostrada | media | Tabla de potencia por criterio y por número de semillas (A3; A5) |
| La prueba final podía "rescatar" hipótesis | baja | Prohibido; rótulo de una tanda (A5 #11; prerregistro §13) |
| Demostrabilidad: tags, correo, fusión, bloques viejos del prototipo | baja | Tags y correo al asesor; fusión sin squash; tabla JSON única con sha256 contra origin (A5 #9; B1; prerregistro §3) |
| Regresión a la media en H8a | baja | Bases 14042 y 16042 de V2 y M3 en 2715 y D (B23) |
| Error en "Por qué 1001-1030 no decide" | baja | Corregido: el criterio total fue de la Enmienda 1, antes de entrenar (prerregistro §3) |
| Omisiones (bases caídas, errores tras abrir datos, 40 frente a 20 checkpoints, redondeo de H10, referencia del puente, semillas de R0.3, semillas libres, semillas de más, P6e en la transferencia, C0 nunca en lugar del entregado) | — | B21-B22; A5 #12; "400 eligiendo entre 20"; H10 4 de 5, 6 de 7, 5 de 6; puente frente al fijo entregado; R0.3 con humo; búsqueda extendida [M]; `comparar` rechaza semillas de más; P6 desde P6e; prerregistro §8 y §16 |

**Lente de factibilidad**

| Crítica | Gravedad | Dónde se atiende |
|---|---|---|
| El calendario subestimaba el código (12.9-14.4 días de tareas frente a ~11) | alta | Calendario rehecho con la suma de tareas, generador como tarea propia, `veredicto3` fuera de la ruta crítica: ~18-19 días de código y ~26-27 en total (A6; CRONOGRAMA) |
| La cola corría en el árbol que se edita y sin hora de corte | alta | Dos worktrees, verificación antes de cada lanzamiento, `--hasta` (B1; 0.2 y 0.4) |
| `--guardar-estado` antes de probar `--reanudar` | alta | Reanudación y sus pruebas antes de la primera noche; estado completo declarado (1.2; B15) |
| Estado dentro del `.pt` rompería `evaluar.py` | media | Archivo aparte; prueba de que `evaluar` juega igual (1.1) |
| Elección de los brazos reanudados | media | Copia de checkpoints ≤ 180 y precarga de las series; paso aparte para "200 con piso" (1.2; 3b) |
| Huérfanos marcados como hechos | media | Éxito solo con salidas completas; prueba con `taskkill /F` (0.4) |
| La capa 1 rechazaba los comandos legítimos | media | Desenvuelve el lanzador; tabla única del prerregistro; `--salida` dentro de `plan3/` (0.4; B1) |
| Doble conteo con write-undeparted | media | Lector propio por periodo y su prueba (0.7; B7) |
| Faltaban dependencias en el modelo de costos | media | Corregidas y simuladas noche por noche (`costos_plan3.py`; B20) |
| Régimen de carga y empaquetado | media | Conservador + 10 % como base; tramos de ≤ 5 h; M5 con el factor del régimen (costos) |
| Nombres de V2 vieja, "200 con piso" y C0 | media | Etiquetas propias en el meta; unicidad en toda la lista (B5) |
| Identidad bit a bit imposible por el nombre en el zip | baja | `torch.equal` sobre los `state_dict` (B12; 1.3) |
| Escritura atómica con temporal fijo | baja | Temporal con pid, reintentos y trabajo "preparar" (0.11) |
| `git diff main` falla si main avanza | baja | `git diff main...HEAD` (0.2; B1) |
| Números comunes no medidos con `best` en P3-P6 | baja | Prueba antes de las referencias (0.6) |
| Orden de 0.12, 0.14 y 0.16 | baja | R0.3 pasa a la noche del día 14 con `evaluar3`; chequeos de cada noche definidos (0.16) |
| Faltaba el código de "colas en cero" | baja | En `evaluar3` con su prueba (0.14) |
| Omisiones (no regresión, pasos de elección, versiones, respaldo nocturno, reintentos, Windows Update, sumo/TraCI con el actuado ajustado, 1001-1003 del 05.11) | — | 0.12; 0.19; 0.4; B22; 0.9; prerregistro §14 |

**Lente de impacto**

| Crítica | Gravedad | Dónde se atiende |
|---|---|---|
| Reloj de 5 s fijo frente a un fijo de 1 s y un actuado de 1 s | alta | Reloj de 2 s como variante prerregistrada, con H14 (A4 (i); 3.4; B24). **Se agrega P6**, que la crítica dejaba fuera: la misma medición da +23.0 % ahí y el 12/10 usa verdes que el reloj de 5 s no da |
| Mejoras de entrenamiento solo con llegadas regulares | alta | 3b y a3 también con llegadas aleatorias; `--guardar-estado` en 2.1; limpiezas aleatorias dentro del modelo completo (A4 (ii); la entropía no entra, B25 y prerregistro §12). **No se acepta** sacar P3 y P5 del 3b regular |
| Modelo citable fijo en V2 con 200 episodios | alta | Modelo completo y regla de promoción con semillas nuevas y margen de 1 % (A4 (iii)-(iv); prerregistro §12). **Celdas cambiadas:** P1, P2, P4 y P6 regulares en vez de P6e, porque las etiquetas regulares se citan en P6 y H6 usa V2 |
| H9b casi idéntica por construcción | media | H9b descriptiva; H9 = "400 con piso < 200 sin piso". **No se agrega** el brazo con `--lr-horizonte 100` |
| Etapa 4 con las dos piezas | media | Una sola: la política por red (A6) |
| Predicción de §14 con la entrada por defecto | baja | Actualizada con las cifras medidas (prerregistro §15) |
| El fijo entregado no separa reloj y aprendizaje | baja | Fijo con verdes de 5 en 5 y desfases finos (A1; prerregistro §5) |
| Faltaba el código de a3 | baja | En `evaluar3` (0.14) |
| Omisiones (orden por efecto, ruido de validación aleatoria, lote de PPO) | — | Tabla "Qué puede mejorar y cuánto"; prerregistro §6; el lote de PPO queda fuera y se declara |

### Críticas del 04.11 (sobre el programa)

| Crítica | Dónde se atiende |
|---|---|
| Método P0: `info_base` calcula mal la convergencia | `veredicto3.serie_criterio` con `x[-1]` de `val_total_serie` (5.0; prerregistro §6) |
| Método P1: 1001-1030 ya se usó con V2 | T1 = 8001-8030 y T2 = 13001-13030; 1001-1030 solo como puente (A3) |
| Método P2: las etapas decidían con semillas de examen | Sin puertas; V2 fijada; todo en la parte A; a ciegas; prueba final reservada (A5) |
| Método P3: M4 alargaba solo P2 y P6 | 400 episodios en P1-P6, sin veredicto, con piso (3b) |
| Método P4: M1 cambiaba entrenamiento y selección a la vez | C0 sin entrenar; cuadro 2×2; ablación de V2 (1.4-1.5) |
| Método P5: caminos para pisar lo entregado | Worktrees, etiquetas `p3`, registro aparte, protecciones (0.2-0.5; B1-B5) |
| Método P6: H1 no era de no inferioridad | Margen +2 %, tres lecturas, 120 semillas (prerregistro §8) |
| Método P7: ajuste desigual entre política y referencias | Fijo fino, franja, actuado ajustado, regla, con más semillas aleatorias (0.7-0.10) |
| Método P8: expectativa de la tanda favorable | Predicción por rangos; solo se cita lo que se repite (prerregistro §7 y §15) |
| Método P9: la versión evaluada no ve la variación entre entrenamientos | Sentido entre entrenamientos en toda afirmación de método; 5 bases en el modelo principal (A3; A5) |
| Método P10: protocolos distintos entre celdas | 16 semillas cada 10 en todas; corredor reentrenado (1.3) |
| Método P11: H2 y H11 mal planteadas | H2 en P4 y la malla con 6525, frente a C0; H11 no se corre |
| Método P12: puerta Poisson incoherente | Sin puerta; H0 descriptiva; H5 en los 6 casos; M5 con su comparador |
| Método P13: editar `veredicto.py`; reproducir escribe en plan2 | No se edita; reproducción con copias (0.12; 5.0) |
| Método P14: prerregistro no demostrable | Commit, push, tag y correo al asesor (0.13; A5) |
| Método O0-O11 | Holm por familia; tabla de acuerdo; `--v2` = smdp_crn medido; H6 no pareada con P6e; H7 en 6 casos y H7r; columnas de `recomendaciones.tex`; revisión en cascada; V2 fuera de la tabla de DQN y MAPPO; H4 con equivalencia; rutas por semilla como plan B; `onda_oe` y franja en P6; corrección de P4 (prerregistro; 5.4) |
| Impacto P0-P11 y O0-O4 | Fijo fino como referencia; P6e y entrada corregida; niveles descriptivos; no inferioridad por caso; candidatos fuertes en H0; pruebas baratas ya corridas el 05.11; validación cada 10; M5 con `--scale`; MP con código conocido; entropía y 400 episodios; regla de la cola; D como banco barato; recompensa de presión discutida; transferencia a llegadas regulares; retraso por media hora; actuado ajustado (prerregistro; DECISIONES) |
