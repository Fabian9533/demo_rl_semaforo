# Desviaciones del plan 3

Registro de todo lo que se apartó del prerregistro (parte A, tag `plan3-prerregistro-A`, sha256
`49c898d7670c8c3bbf382a366a8038a47c2562063cc8fd8c506c8615203b6134`). El informe final las repite (§11: "toda
desviación y toda enmienda con los datos que estaban a la vista").

## 1. Semillas del examen T1 en una revisión de código (05.11.2026, 12:20-13:00)

**Qué pasó.** Una revisión automática del script de veredicto (commit `13fd132`) quiso comprobar con SUMO cómo se
cuentan los cambios de fase. Corrió `evaluar3.py` en una copia aparte del repositorio con tres semillas del examen T1
regular: 8001, 8002 y 8003. Fue un error de la instrucción: no le dijo qué semillas usar.

**Qué se corrió.** Ningún modelo del plan 3 existía todavía y el fijo fino no se corrió.

| Escenarios | Brazos | Semillas |
|---|---|---|
| Las 32 plantillas | regla simple `regla_u3g60` | 8001 |
| Corredor, red y algunas `dem_` | regla simple, Max-Pressure `mp_c60`, IPPO entregada (base 42), fijo instalado, actuado por defecto, ciclo mínimo | 8001-8003 |

**Qué se vio.**
- El agente de la revisión leyó el número de cambios de fase de cada corrida (métrica secundaria).
- En dos líneas de su salida vio también el retraso total y el timeLoss de `regla_u3g60` en el corredor.
- El coordinador vio solo cambios de fase en el corredor: los de la regla simple, el fijo, el actuado y el ciclo mínimo,
  y la diferencia k (no el conteo) de la IPPO entregada. Fabian no vio ninguna cifra.
- Según las transcripciones de la revisión, nadie vio el retraso de ninguna IPPO ni del fijo.

**Por qué no cambia ninguna regla.**
- Las reglas ya estaban fijadas y subidas antes (tag de la parte A, 11:58 del mismo día).
- Son 3 de las 30 semillas de T1 y ninguna de T2.
- Los brazos que deciden las etiquetas (los modelos nuevos frente al fijo fino) no existían.

**Qué se hizo.**
- Los 86 archivos de esas corridas (54 CSV y 32 salidas de texto) se movieron sin abrirlos a una carpeta de cuarentena
  fuera del repositorio. Antes se anotaron su ruta, sha256, filas y semillas, leyendo solo la columna de semillas.
- Desde el 05.11, `comun.iniciar_sumo` y `barrer_fijo` se niegan a simular una semilla del examen o de la prueba final
  si el proceso no viene de un trabajo ciego de la cola (commits `682b6c2` y `3a547f7`).
- Toda prueba o revisión usa solo semillas de humo (424301-424360) o la base 7.
- La evidencia del conteo de cambios de fase se rehízo con semillas de humo (`pruebas/ver/salidas/prueba_k_humo.txt`).

**Decisión de Fabian (05.11, 19:57):** se borraron sin abrir. Su manifiesto (ruta, sha256, filas y semillas, sin
ninguna métrica) queda en `plan3/doc/cuarentena_examen_20261105.json`.

## 2. Cambios de fase: corrección de un error de conteo (05.11.2026)

**Qué pasó.** `rl_ippo.py` cuenta un cambio de más por cada semáforo que la plantilla arranca fuera de su primer verde.
`rl_corredor.py` no lo cuenta. Por eso, en el corredor, los brazos que corren por `rl_ippo` (IPPO y reglas) sumaban 1
de más por episodio. En P6 entregado sumaban 4 de más.

**Qué se hizo.** `veredicto3.py` resta ese número (k, uno por plantilla) a esos brazos. La fila de cada comparación lo
dice. Es la corrección de un error de código hecha antes de cualquier evaluación decisiva; ningún dato decisivo estaba a
la vista. No toca la métrica principal ni ninguna etiqueta.

## 3. Código de las referencias después del tag (05.11.2026; borrador para incluir con la parte B)

**Qué pasó.** El prerregistro (§5, "Detalles operativos de las referencias") dice que esos detalles los fija el código
del tag de la parte A (`plan3-prerregistro-A`, commit `a9ba36b`, 05.11 a las 11:58). Después del tag, dos revisiones de
ese código (sobre `0cea683` y sobre `6e8cfab`) encontraron errores, que se corrigieron el mismo día, antes de correr
ninguna referencia (sus noches son los días 12 y 13). El código de las referencias que corre es el del commit
`7714544` (rama `plan3-ref`); sus archivos, por su blob de git:

| Archivo | Blob |
|---|---|
| `plan3/barrer_fino.py` | `a8fc4961f8193d98730634018db2d8b0a2b51fd2` |
| `plan3/franja.py` | `0ed5faf1b74a49db4657a32fa2b9bb975528df26` |
| `plan3/actuado.py` | `2da7cf5027818372bfa966a7d8e27e1fed3a787e` |
| `plan3/reglas.py` | `4c99d833b1ea4ef8e3fcbaf41401777b52f5b035` |
| `plan3/p3_preparar.py` | `1489dc76da0c615f582cc9beb3cc07083eec384e` |
| `plan3/p3_congelar.py` | `cc4fdd63b14cad4a78847fd5bdd2bf68c63db4f7` |
| `plan3/evaluar3.py` | `6f9ae718b509def74bf06d2fe90149e761c78a7c` |
| `evaluar.py` | `fb2d80e5e857d964d7f5a186eb6475f4f90f38b6` |
| `comun.py` | `55a0d8cf08bebc58ff695bdd20c6b64fdaccf10a` |
| `rl_corredor.py` | `95c73c7745c7b6cb985bad47100149ccf5598e59` |
| `barrer_fijo.py` | `ad8b7b27a18437d2ff379dd622f32209f1308971` |

(Un blob es el sha1 que git da al contenido del archivo: `git rev-parse <commit>:<archivo>`. Si la rama que corre trae
otro commit con estos mismos blobs, el código de las referencias es el mismo.)

**Qué hace distinto del código del tag.** Ninguna regla de §5 cambia: cambian detalles que el tag resolvía mal o no
resolvía.

| Punto | Código del tag | Código que corre |
|---|---|---|
| "A ≤ 2 %" (etapa fina y regla de frágiles) | Comparación en coma flotante: en el borde exacto (p. ej. 20.50 y 20.91) la frágil fallaba en 91 de 190 casos y la fina no | Una sola cuenta, en centésimas enteras (`a_2pct`), en las dos |
| Cambio de plan de la franja y de los bloques (WAUT) | Si en un hiperperíodo no había un instante con el mismo estado en t − 1, t y t + 1, la celda abortaba | Esa regla primero (los programas que la cumplían salen iguales). Si no hay, una regla relajada (el paso de un plan al otro es uno que haría un plan normal y ningún verde que lo toca dura menos de 10 s); si tampoco, un respaldo (al terminar un ámbar del plan viejo, sin cortar verdes); y si ni eso (no pasa en P1-P6), el primer fin de ámbar. `franja.json` y `bloques.json` anotan la regla y el retraso de cada cambio, con un aviso si alguno llega más de 300 s tarde o después del cambio siguiente |
| Actuado ajustado, variantes coordinadas (a) y (b) | SUMO contaba el ciclo desde el inicio de la fase 0. En red y malla, donde la avenida es la fase 0, el verde de la avenida cruzaba ese 0 y SUMO dejaba sin efecto `earliestEnd` y `latestEnd` en la mitad de los ciclos. Además, el `maxDur` de la avenida venía de la cadena y podía cortarla antes de su fin | El ciclo se cuenta desde el inicio del verde transversal del plan fijo: son los mismos instantes del plan fijo, y el desfase del programa es el del fijo fino más ese inicio. La avenida tiene `maxDur` suficiente: el ciclo en (b) y, en (a), lo que necesita si la transversal corta en su mínimo. Medido con el plan 25/15 de `dem_red_t3620`: (b) terminaba la avenida en el fin del plan fijo en 84 de 166 salidas y ahora en 128 de 129 (la otra es el arranque). En el corredor, donde la avenida es la fase 2, solo cambia el `maxDur` |
| Regla reactiva | No estaba en el código del tag | Carriles con verde: los de entrada con algún enlace G o g en el estado del semáforo. Distancia a la línea: largo del carril menos la posición del vehículo. Los vehículos que ya están dentro del cruce no cuentan. Mismo reloj de 5 s y misma máscara que IPPO |
| Cadena de etapas | Cada etapa leía la anterior mirando solo la huella del escenario | Se niega a leer salidas con opciones de prueba, con otra rejilla, con otras semillas o un fijo fino de otra huella |
| Caché | La huella no cubría el código que lee las métricas | La huella cubre el código entero que arma, corre y lee cada corrida: un arreglo nunca hereda números viejos |

**Relanzamientos de las referencias (B22).** Si un error de código toca una referencia, se corrige como dice B22: los
trabajos afectados corren otra vez con ids nuevos (`_r2`), se conservan las salidas viejas y una enmienda lo declara.
En las referencias eso exige un paso más, porque los scripts escriben siempre en las mismas rutas:
1. antes de relanzar, se mueven las salidas viejas de cada celda afectada (`barridos/<esc>/`, `tmp_fino/<esc>/` y los
   `<esc>_*.add.xml` instalados) a `barridos_viejos/<esc>_<fecha>/`;
2. el generador da a esa celda los ids `_r2` en lugar de los viejos (mismos comandos y mismas salidas declaradas);
3. como la huella cubre el código, nada de lo guardado antes del arreglo se reutiliza.

Una caída de infraestructura (proceso matado, reinicio) no es esto: se relanza el mismo id, sin mover nada, y la caché
sigue donde quedó.

**Por qué no cambia ninguna regla.** Todo se hizo antes de correr ninguna referencia y sin datos de las tandas
decisivas: las pruebas usan semillas de humo, y las de ajuste solo en copias. Los cambios corrigen lo que el código
hacía distinto de lo que §5 describe (el borde del 2 %, la coordinación del actuado), o completan lo que §5 no
detallaba (el WAUT sin instante limpio y la regla reactiva).
