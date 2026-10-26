# Por qué IPPO con mensajes pierde frente al fijo con 2715 veh/h (síntesis, 25.10.2026)

Análisis posterior al veredicto (PRERREGISTRO.md): no cambia ningún veredicto ni ningún archivo existente. Junta lo
que midieron `periodos.md` (10 semillas), `bloqueo.md` (5 semillas, segundo a segundo), `comportamiento.md`, `sumo.md`,
los barridos del fijo y la Enmienda 3 (`pruebas3.txt`). Agrega dos mediciones nuevas de esta síntesis:
`bloqueo_niveles.py`, que aplica el registro de `bloqueo.py` a los cinco niveles, y `giros_liberacion.py`, que mide
cuándo sale el vehículo que espera para girar. Cada paso dice si está **MEDIDO** o es **INFERIDO**. Una
correlación se dice como correlación.

Términos:
- O = `dem_corredor_t2715`, con los giros del periodo 2 a la izquierda. D = `dem_corredor_t2715_der`, con los giros
  a la derecha.
- Periodo 1 = 0-1800 s (punta O→E). Periodo 2 = 1800-3600 s (punta E→O).
- "Fijo" = 25/10 s con desfases 0/0, el fijo ajustado de 2715, salvo que se diga otro.
- "Retraso" = timeLoss + espera para entrar, en s/veh.

## Respuesta corta

- **Causa medida.** La desventaja aparece en el periodo 2, con los cuatro giros a la izquierda. Esos giros tienen
  verde sin prioridad y van en calles de un carril, así que el que espera un hueco detiene todo su carril. Si esos
  giros se cambian a la derecha (D), V2 deja de perder contra el mismo fijo y le gana (H6a pasa).
- **Por qué solo en 2715.** Los giros existen en los cinco niveles, y desde 1358 ya bloquean parte del verde (en 1810,
  hasta el 25 % del verde de W_C1). Hasta 1810 sobra capacidad, así que el bloqueo no se propaga. 2715 es el primer
  nivel en que la avenida trabaja llena en el periodo 2. Ahí cada segundo bloqueado o quitado a la avenida se vuelve
  cola, derrame hasta C2 y espera para entrar por E_C2. En 3620 todo está saturado en los dos periodos y la diferencia
  entre controles se diluye.
- **Qué hace cada control.**
  - IPPO de 2715 alarga la transversal de C2 mientras el giro S2→W la tiene bloqueada, y le quita verde a E_C2.
  - V2 no alarga, pero sufre el bloqueo del giro E→S1 en C1, que derrama hasta C2.
  - El actuado alarga todo.
  - El fijo corta siempre a los 10 y 25 s, y el que espera para girar sale casi siempre al terminar el verde (del 77
    al 97 % según el acceso; `giros_liberacion_2715.csv`).
- **Lo que no alcanza.** Según la regla prerregistrada, los giros no bastan. Sin ellos, V2 entrenado en D no le gana
  al fijo ajustado de D (+1.3 %, H6b no pasa). Un horizonte más largo (gamma 0.99) empeora el resultado (+16.1 %, H7
  no pasa).

## La cadena causal, paso a paso

1. **MEDIDO. Punto de partida** (`pruebas.txt`, `pruebas3.txt`; semillas 1001-1030).
   - Retraso: fijo 57.50, IPPO actual 76.43 (+32.9 %), V2 76.83 (+33.6 %), actuado 151.43.
   - Con 6001-6030: IPPO actual +41.7 % y V2 +38.4 %.
   - Todas las versiones entrenadas quedan entre 76 y 91 s/veh.
2. **MEDIDO. Todo el exceso está en el periodo 2** (`periodos.csv`, 10 semillas, diferencia pareada con el fijo,
   IC95 t).
   - Periodo 1: IPPO actual −9.6 [−10.4, −8.8], V2 −6.6 [−7.9, −5.2] y actuado −9.8. Los tres ganan en 10 de 10
     semillas.
   - Periodo 2: IPPO actual +49.6 [+26.3, +72.8], V2 +47.1 [+21.4, +72.8] y actuado +211.9.
   - Hora: +20.0 y +20.3.
3. **MEDIDO. Lo pagan los que entran por E_C2, la punta E→O** (`periodos.csv`, tabla 4 de `periodos.md`).
   - Aportan +27.8 (IPPO actual) y +29.1 (V2) s por vehículo de la hora. Es más que el total del periodo 2 (+24.8 y
     +23.6), porque las transversales mejoran (−1.9 y −3.2).
   - La recta E→O pasa de 110.1 s/veh con el fijo a 262.7 y 269.8. La mitad de ese aumento es espera para entrar.
4. **MEDIDO. Lo único que distingue el periodo 2 del 1 son esos giros, y en SUMO detienen su carril**
   (`dem_corredor_t2715.rou.xml`, `bloqueo.csv`, `bloqueo_niveles.csv`).
   - Los flujos del periodo 2 son los del 1 girados 180 grados, salvo los cuatro giros de 90 veh/h, que pasan de la
     derecha a la izquierda.
   - El que gira espera el hueco dentro del cruce, con 0.93 m de su cola sobre el carril.
   - En los segundos de verde con un vehículo así no cruzó ningún otro vehículo de su acceso: 0 en 10 806 s (40
     corridas de `bloqueo.py`) y 0 en 25 638 s (75 corridas nuevas, cinco niveles).
   - Solo pasa en el periodo 2 de O: hay 0 s en el periodo 1 y en D.
5. **MEDIDO. Sin esos giros desaparece la pérdida frente al mismo fijo** (`periodos.csv`, `bloqueo_periodos.csv`,
   `pruebas3.txt`).
   - En el periodo 2 de D: IPPO actual −5.4 [−11.1, +0.2], V2 +0.2 [−4.4, +4.7] y actuado −16.8. En la hora: −7.5,
     −3.2 y −13.3.
   - Con 30 semillas, V2 queda en 39.59 frente a 42.54 del fijo (−6.9 % [−9.9, −4.1]).
   - Costo de los giros, periodo 2 de O menos periodo 2 de D: fijo +25.7, V2 +68.0, IPPO actual +77.3 y actuado
     +244.1 s/veh.
6. **MEDIDO. Cómo sale el que espera para girar** (`giros_liberacion_2715.csv`, periodo 2 de O, por corrida).
   - W→N1, contra 990 veh/h. Con el fijo se detienen 39.2 de los 45 que giran. El 97 % sale al terminar el verde (38.0),
     y en el periodo hay 44.0 fines de verde. Es casi uno por fin de verde.
   - E→S1 en C2_C1, contra 375 veh/h. Se detienen 7.8 con el fijo, 21.4 con IPPO actual y 19.6 con V2.
   - S2→W en S2_C2. Con el fijo se detienen 5.2 y el 88 % sale al terminar el verde. Con IPPO actual se detienen 20.2, y
     el 90 % sale en un hueco del verde alargado.
7. **MEDIDO; la relación con el retraso es una correlación. Dónde pesa el bloqueo** (`bloqueo.csv`).
   - Fracción del verde con la cabeza detenida para girar (fijo / actuado / IPPO actual / V2):

     | Acceso | Fracción del verde | Dato adicional |
     |---|---|---|
     | C2_C1, giro E→S1 (retiene la punta en C1) | 4 / 37 / 13 / 12 % | Descarga con cola: 0.44 / 0.26 / 0.38 / 0.38 veh/s (en D, 0.44-0.47) |
     | S2_C2 | 1 / 26 / 18 / 5 % | |
     | W_C1 | 38 / 25 / 25 / 14 % | |

   - En las 15 corridas sin el actuado, los segundos con C2_C1 bloqueado siguen al retraso del periodo 2 con
     ρ = 0.92.
   - En W_C1 el bloqueo no se asocia con el retraso (ρ = −0.44, p = 0.10). W_C1 no está saturado: cruzan 235
     vehículos en verde para una demanda de 233.
8. **MEDIDO. IPPO actual alarga la transversal de C2 mientras S2_C2 está bloqueado, y le quita verde a E_C2**
   (`bloqueo_verdes.csv`, `bloqueo_decisiones.csv`, `bloqueo.csv`).
   - El verde transversal de C2 en el periodo 2 dura 20.4 s, frente a 11.8 s en D y 10 s con el fijo. Dura 23.8 s con
     la cabeza bloqueada y 15.0 s sin ella.
   - IPPO termina el verde en el 9.9 % de 111 decisiones con la cabeza bloqueada, en el 38.8 % de 400 sin ella y en el
     73.8 % de 263 en D.
   - E_C2 recibe 928 s de verde, frente a 1113 s en D, y cruzan 386 de sus 495 vehículos, frente a 475 en D. Unos 79
     de los 88 que faltan salen del verde perdido (185 s × 0.427 veh/s); es una cuenta sobre lo medido.
   - **INFERIDO, cota de capacidad.** E_C2 recibe 928 s de verde de cada 1800. A la descarga de saturación de SUMO
     (1836 veh/h, `sumo.md`), eso da como mucho unos 947 veh/h, menos que los 990 que piden pasar (E→O 900 + E→S1 90).
     La cola tiene que crecer. Con el fijo (1096 s), la cota es de unos 1118 veh/h (v/c ≈ 0.89).
9. **MEDIDO. V2 no alarga, pero pierde por el derrame desde C1** (`bloqueo_derrame.csv`).
   - V2 termina siempre la transversal a los 10 s.
   - La cola de C2_C1 llega a C2 durante 262 s por corrida. Con el fijo son 78 s, y en D 62 s como máximo.
   - E_C2 descarga 0.17 veh/s en los 137 s de verde con esa cola, y 0.41 en el resto. En el periodo descarga 0.377
     frente a 0.439 en D, y cruzan 382 vehículos frente a 465.
10. **MEDIDO; el porqué es INFERIDO. El actuado amplifica todo** (`bloqueo.md`).
    - El verde de avenida de C1 dura 57 s (35.3 s en D), y en 21.1 s de cada uno la cabeza de C2_C1 está bloqueada.
    - Las transversales duran 31.5 y 32.4 s (13.2 y 12.8 s en D).
    - La cola de C2_C1 llega a C2 durante 594 s, y E_C2 queda bloqueada por el derrame 355 s.
    - Los vehículos que entran por E_C2 esperan 391 s para entrar.
    - INFERIDO: el actuado no corta porque la cola detenida ocupa su detector.
11. **MEDIDO. La cola termina como espera para entrar, que no cuenta en el timeLoss** (tabla 9 de `periodos.md`,
    `comp_entrada.csv`).
    - Con IPPO actual y V2, la cola para entrar por E_C2 empieza en los minutos 40-45 y llega a unos 61 vehículos en
      los minutos 55-60.
    - Se forma en 10 de 10 semillas con IPPO actual, V2 y el actuado, en 2 de 10 con el fijo y en 0 de 10 en D.
    - Espera media para entrar por E_C2 en el periodo 2: IPPO actual 89.7 s, fijo 17.8 s, actuado 391.0 s y D 0.5 s.
    - **MEDIDO, no se arregla mirando la entrada.** V2+INS+obs ve esa espera y la paga en la recompensa, y aun así
      queda en +36.7 % [+25.2, +49.6] frente al fijo (`pruebas.txt`).
    - Tampoco es un efecto de cómo SUMO inserta los vehículos: con entrada a velocidad máxima, la desventaja de IPPO
      sigue en +29.3 [+19.7, +39.0] s/veh (`sumo.md`).
12. **MEDIDO. En O, el fijo tiene un margen muy estrecho** (`barrido_dem_corredor_t2715.csv` y
    `barrido_dem_corredor_t2715_der.csv`, semillas 2001-2003).
    - En O, solo 25/10 queda bajo 100 s/veh: 46.7 con desfases 0/0 y 49.9-64.4 con otros desfases. El mejor plan con
      ciclo de 46 s da 108.8, y el mejor de 56 s, 162.8.
    - En D, el mejor plan es 35/15 con desfases 0/30 (28.6), y los mejores ciclos son los de 56-61 s.
    - Con el mismo plan, O menos D da una mediana de +27.8 a +55.0 s/veh con ciclos de 31-46 s, y de +83.5 a +148.3
      con ciclos de 51-66 s.
    - **INFERIDO.** Con los giros bloqueando, cada fase recibe en 25/10 casi justo lo que necesita.
      - El giro W→N1 sale casi solo al terminar el verde (paso 6). Con un ciclo de 41 s hay 44 fines de verde para 45
        vehículos; con 46 s habría unos 39, y con 56 s, unos 32.
      - Con más transversal, la avenida baja de su capacidad.
      - Los controles adaptativos salen de ese margen en el periodo 2. IPPO de 2715 da en C2 verdes medianos de 30 s de
        avenida y 20 s de transversal, y el actuado llega a 60 s de avenida (tabla 8 de `periodos.md`).

## Por qué en 2715 y no en 905-1810, y qué pasa en 3620

**MEDIDO** (`bloqueo_niveles*.csv`, periodo 2, 5 semillas, 75 corridas nuevas). Cada nivel tiene su fijo de
referencia y su versión evaluada de IPPO. La demanda es la misma escalada (×0.5 a ×2), y los cuatro giros a la
izquierda del periodo 2 están en todos los niveles.

Columnas (los pares son fijo / IPPO):
- Verde bloqueado por un giro: fracción del verde de cada acceso con la cabeza detenida para girar, en W_C1, C2_C1 y
  S2_C2.
- Verde de C2_C1 con cola: segundos de verde de C2_C1 que empiezan con un vehículo detenido.
- Cola de C2_C1 hasta C2: segundos por corrida.
- Esperan entrar por E_C2: vehículos en promedio.
- Decisiones de IPPO que cortan la transversal de C2: entre paréntesis, el número de decisiones.
- Retraso P2/P1: cociente entre el periodo 2 y el 1.

| Nivel | Verde bloqueado, fijo | Verde bloqueado, IPPO | Verde de C2_C1 con cola | Cola de C2_C1 hasta C2 (s) | Esperan entrar por E_C2 | Decisiones de IPPO que cortan | Retraso P2/P1 |
|---|---|---|---|---|---|---|---|
| 905 | 2 / 0.5 / 0.3 % | 1 / 0.2 / 0.2 % | 3 / 6 % | 0 / 0 | 0.03 / 0.03 | 100 % (228) | 0.98 / 0.97 |
| 1358 | 8 / 1.0 / 3.5 % | 4 / 0.8 / 5.6 % | 9 / 3 % | 0 / 0 | 0.04 / 0.04 | 100 % (231) | 1.07 / 1.02 |
| 1810 | 25 / 4.5 / 2.4 % | 19 / 4.1 / 5.1 % | 16 / 13 % | 0 / 0 | 0.05 / 0.05 | 100 % (241) | 1.08 / 1.15 |
| 2715 | 38 / 4.3 / 0.6 % | 25 / 12.6 / 18.1 % | 85 / 91 % | 78 / 262 | 3.9 / 19.1 | 32.5 % (511); 9.9 % con la cabeza bloqueada | 1.83 / 4.05 |
| 3620 | 21 / 2.8 / 21.5 % | 25 / 20.4 / 21.6 % | 94 / 94 % | 51 / 416 | 86.8 / 159.7 | 15.4 % (771) | 2.75 / 4.17 |

- **Hasta 1810 hay bloqueo, pero no se propaga.** En 1810, W→N1 ya bloquea del 15 al 25 % del verde de W_C1, según
  el control, pero:
  - la cola de C2_C1 nunca llega a C2;
  - casi nadie espera para entrar;
  - solo empiezan con cola del 3 al 22 % de los segundos de verde de C2_C1 (85-93 % en 2715);
  - las políticas de IPPO de 905, 1358 y 1810 cortan la transversal de C2 en la primera decisión, también con la
    cabeza bloqueada (n = 1, 4 y 4).

  En el periodo 2, IPPO le da a la avenida de C2 el 0.699, 0.696 y 0.681 del verde, casi lo mismo que en el periodo 1
  (`comp_ciclo.csv`). El cociente P2/P1 queda entre 0.96 y 1.15 con los tres controles (`bloqueo_niveles_periodos.csv`)
  y entre 0.95 y 1.15 en `comp_movimientos.csv`.
- **En 2715 la avenida trabaja llena.** Ahí, el verde bloqueado (por el giro E→S1 en C1) y el verde quitado (por la
  transversal alargada en C2) se vuelven derrame y espera para entrar (pasos 7-11). Solo las políticas de 2715 y 3620
  alargan la transversal.
- **INFERIDO, cuenta aproximada de capacidad.**
  - Supuestos: descarga de saturación de 1836 veh/h (`sumo.md`) y la fracción del ciclo que cada fijo de referencia da
    a la avenida.
  - El acceso crítico del periodo 2 es C2_C1 en C1, hacia el oeste. Pide 360, 540, 720, 1080 y 1440 veh/h, con fijos
    de 10/10, 12/10, 20/10, 25/10 y 25/15. Eso da un v/c de unos 0.51, 0.69, 0.71, 0.96 y 1.44.
  - 2715 es el primer nivel en que hasta el mejor fijo trabaja cerca de 1.
  - La cuenta ignora el uso del ámbar y la pérdida al arrancar.
- **3620: todo saturado, y la diferencia se compensa.**
  - Saturación (MEDIDO):
    - Con el fijo, el periodo 1 ya da 209.6 s/veh, y en ese periodo la espera para entrar por W_C1 es de 352 s (IPPO:
      154.2 y 216 s; `comp_movimientos.csv`, `comp_entrada.csv`).
    - Las dos entradas de la avenida piden 1320 veh/h, y SUMO inserta como mucho 1202 por carril (`sumo.md`).
  - Mismo patrón que en 2715 (MEDIDO, `comp_ciclo.csv`, `comp_entrada.csv` y la tabla de arriba):
    - IPPO baja la fracción de verde de la avenida en el periodo 2 a 0.499 en C1 y 0.461 en C2.
    - E_C2 espera 964 s, frente a 395 s con el fijo.
    - La cola de C2_C1 llega a C2 durante 416 s.
  - IPPO pierde +79.9 s por vehículo del nivel en la avenida del periodo 2. Gana −27.7 en el periodo 1 y −38.7 en las
    transversales del periodo 2, donde el fijo las deja en 242.5 s/veh. En la hora queda en +6.4 (+1.6 %;
    `comp_aporte.csv`, `pruebas.txt`).
  - V2+INS+obs, que ve la espera para entrar, le gana al fijo en 3620 (−8.9 % [−10.3, −7.5]), pero no en 2715
    (+36.7 %; `pruebas.txt`).
  - INFERIDO: en 3620 pesa sobre todo la entrada, y en 2715 pesa el bloqueo con la avenida al límite.
  - En 3620 no hay contrafactual sin giros, así que no está medido cuánto de su resultado se debe a los giros.

## Lo que contradice o no cierra

1. **H6b no pasa, así que la explicación está incompleta según la regla prerregistrada.** Sin los giros, V2
   entrenado en D queda +1.3 % [+0.5, +2.0] frente al fijo ajustado de D (35/15, 0/30). Las otras dos bases también
   quedan peor (+2.2 % y +1.5 %, recalculado desde `eval3/`).
   - Descriptivo, no es una prueba: cada escenario tiene su fijo ajustado y su V2 entrenado. Con eso, la desventaja
     pasa de +33.6 % en O a +1.3 % en D.
   - Los giros explican la anomalía de 2715. Sin ellos, IPPO empata con un fijo bien ajustado, como en 905 (+0.1 %) y
     en 3620 (+1.6 %), pero no gana.
2. **INFERIDO. La ganancia de IPPO en el periodo 1 es frente a un fijo que los giros obligan a ser corto.** En O, el
   25/10 con desfases 0/0 tiene una banda verde de 0.36 (`comportamiento.md`), y en D el 25/10 es un plan malo (42.54
   frente a 29.22 del ajustado; `pruebas3.txt`). El retraso por periodo del fijo ajustado de D no está medido.
3. **Por qué el fijo sufre tres veces menos el bloqueo E→S1 (4 % frente a 12-13 %).** No está medido. Lo nuevo: con el
   fijo se detienen 7.8 de los 45 que giran, frente a 21.4 con IPPO actual y 19.6 con V2. Hay dos hipótesis sin
   probar:
   - El momento en que llega el pelotón E→O con desfases 0/0.
   - El propio bloqueo de W_C1 (38 % del verde con el fijo), que corta el flujo W→E y le abre huecos a E→S1. Entre las
     15 corridas, los dos bloqueos se relacionan con ρ = −0.41, una correlación débil.
4. **No se sabe qué dispara a IPPO.**
   - La política no observa si la cabeza va a girar.
   - En O también corta menos sin detenidos en las transversales (0.433, frente a 0.754 en D).
   - Solo las políticas de 2715 y 3620 alargan la transversal; las de 905 a 1810 nunca lo hacen.
   - No está medido por qué la política de 2715 lo aprendió.
5. **El periodo 2 de D no es igual al periodo 1.** Fijo 45.5 frente a 38.9, IPPO actual 40.0 frente a 29.3 y V2 45.6
   frente a 32.3 s/veh; solo el actuado es igual (28.7 frente a 29.1; `periodos.csv`). Esa asimetría no está
   explicada, y por eso el efecto de los giros se mide como periodo 2 de O menos periodo 2 de D.
6. **H7 no pasa, pero el entrenamiento con gamma 0.99 no se estabilizó.** La base elegida tiene una meseta de +33.0 % y
   una estabilidad de 22.9 % (`pruebas3.txt`), y las tres bases quedan peor que V2 (+16.1 % a +26.4 %). La prueba no
   separa "el horizonte no importa" de "con gamma 0.99 no se aprendió en 200 episodios".
7. **Pocas semillas y correlaciones entre controles.**
   - El mecanismo usa 5-10 semillas, sin corrección por comparaciones múltiples.
   - El ρ = 0.92 mezcla tres controles. Dentro del fijo, la peor semilla (1002, 86.63 s/veh) es la de más bloqueo
     E→S1: 158 s, frente a 2-46 s en las otras.
8. **Depende del modelo de SUMO.**
   - Con paso de 0.5 s, la distancia entre el fijo y el actuado en 2715 baja de −101.0 a −16.0 s/veh (`sumo.md`), e
     IPPO no se puede probar con ese paso.
   - Que el que gira espere dentro del cruce, y que salga uno por fin de verde, es el modelo de cruce de SUMO.
   - El mecanismo vale dentro del modelo.
9. **El contrafactual cambia más que el sentido del giro.** También cambia qué tramo transversal lleva los 90 veh/h:
   S1_C1 y N2_C2 en vez de S2_C2 y N1_C1. Además, las políticas que H6a juega en D no se reentrenaron.

## Enmienda 3: H6a, H6b y H7 (ya terminaron)

La cola terminó a las 18:52:18 (`eval3/cola.log`, "cola: fin"), y `analisis3.py` escribió `pruebas3.txt` a las
18:54:41. Las medias, los cambios y los IC los recalculé desde los CSV de `eval3/` y `eval/`, y coinciden.

| Prueba | Comparación | 1001-1030 | 6001-6030 | Resultado |
|---|---|---|---|---|
| H6a | En D, V2 de 2715 sin reentrenar frente al fijo 25/10 | 42.54 → 39.59 (−6.9 % [−9.9, −4.1], p = 0.00011) | 43.11 → 39.22 (−9.0 % [−11.5, −6.5]) | PASA |
| H6b | En D, V2 entrenado en D (base 42) frente al fijo ajustado de D (35/15, 0/30) | 29.22 → 29.59 (+1.3 % [+0.5, +2.0], p = 0.0042) | 28.89 → 29.32 (+1.5 % [+0.4, +2.6]) | NO PASA |
| H7 | En O, V2 con gamma 0.99 (base 4042) frente a V2 (base 42) | 76.83 → 89.23 (+16.1 % [+9.0, +23.6], p = 0.00015) | 75.94 → 85.24 (+12.3 % [+6.2, +18.8]) | NO PASA |

- **Lectura prerregistrada.** (a) pasa y (b) no pasa, así que "los giros no bastan para explicar 2715". H7 no suma.
- **Lo que deciden.**
  - Que los giros causan la gran desventaja frente al fijo de 2715 (H6a).
  - Que sin ellos IPPO no supera a un fijo bien ajustado (H6b).
  - Que alargar el horizonte del descuento no la corrige (H7).
- **Regla del plan para V2 entrenado en D.** FALLA: +1.3 % frente al fijo y +2.9 % frente al actuado (`pruebas3.txt`).
- **Sin prueba** (1001-1030, retraso frente al 25/10 en D): IPPO actual −18.6 %, actuado −32.4 % y fijo ajustado de D
  −31.3 %.

## Comprobaciones

- **Determinismo (obligatorio).** Las 75 corridas nuevas dan el mismo retraso total, timeLoss, espera para entrar,
  cambios de fase, no insertados y vehículos que la evaluación del plan con la misma semilla
  (`bloqueo_niveles_control.csv`).
  - O con 1001-1005, fijo: 45.07 / 86.63 / 45.11 / 45.94 / 49.05, igual que `demanda/eval_corredor_f150_fijo.csv`,
    que es igual a `demanda2/eval_dem_corredor_t2715_fijo.csv` en las 30 semillas. Semilla 1001: 45.07 = 45.07.
  - Actuado: 168.45 / 143.7 / 157.19 / 148.73 / 133.97 (`demanda2/eval_dem_corredor_t2715_actuado.csv`).
  - IPPO actual: 65.87 / 77.72 / 82.08 / 68.87 / 75.93 (`demanda2/eval_dem_corredor_t2715_ippo_vecinos_s2042.csv`).
  - V2 se corrió aparte, con el mismo código (`bloqueo_niveles.uno`): 80.29 / 71.53 / 78.18 / 69.62 / 69.75, 5 de 5
    iguales a `eval/eval_dem_corredor_t2715_ippo_vecinos_v2_s42_1001.csv`.
- **Coincidencia con `bloqueo.py`.** Las filas de 2715 de `bloqueo_niveles.csv` reproducen las de `bloqueo.csv`: por
  ejemplo, C2_C1 4.3 / 37.1 / 12.6 % y E_C2 con 928 s y 386.2 cruces con IPPO.
- **Umbrales.** Son los de `bloqueo.md`: detenido por debajo de 0.1 m/s, plaza de 7.5 m y cola a menos de 2 m/s.

## Archivos y cómo reproducir

- Nuevos en esta carpeta:
  - `mecanismo_2715.md`.
  - `bloqueo_niveles.py` y sus CSV `bloqueo_niveles.csv`, `_enlaces.csv`, `_verdes.csv`, `_decisiones.csv`,
    `_periodos.csv` y `_control.csv`.
  - `giros_liberacion.py`, con `giros_liberacion_niveles.csv` y `giros_liberacion_2715.csv` (este último viene de los
    datos de `bloqueo.py`).
- Reproducir, desde `plan2/`:
  - `python -B diag_corredor/bloqueo_niveles.py correr --datos <carpeta> --procesos 4` (75 corridas, unos 5 min).
  - `python -B diag_corredor/bloqueo_niveles.py analizar --datos <carpeta>`.
  - `python -B diag_corredor/giros_liberacion.py --datos <carpeta> --patron "*" --salida <csv>`.
- Datos por segundo (fuera del repositorio):
  `C:/Users/GAMER/AppData/Local/Temp/claude/c--Users-GAMER-Documents-demo-rl-semaforo/de7717ed-cbad-4afb-8e8f-03cbdcefb7fa/scratchpad/mecanismo/datos/`.
  La comprobación de V2 está en `.../mecanismo/datos_v2/`. Es una carpeta temporal de la sesión.
- Aviso, fuera del análisis: por un error de ruta, al preparar las corridas se creó la carpeta
  `C:\c\Users\GAMER\AppData\Local\Temp\claude\...\scratchpad\mecanismo\datos`. Tiene 17 archivos pequeños: copias de
  `.sumocfg` y `.add.xml`, y `escenarios.json`. No la usa nada y se puede borrar entera, desde `C:\c`. No la borré
  porque el control de seguridad bloqueó el borrado.

## Nota de verificacion (25.10.2026, 20:20; dos verificadores independientes, cifras y causalidad)

Las mediciones de periodos.md y bloqueo.md se reprodujeron (determinismo 20 de 20 y mas). Correcciones a este documento:

- "Sin ellos, IPPO empata con un fijo bien ajustado": no es empate. V2 entrenado sin los giros queda +1.3 % [+0.5, +2.0]
  (+1.5 % en 6001-6030), FALLA con la regla del plan (pruebas3.txt, H6b).
- "Los giros explican la anomalia de 2715": la lectura prerregistrada (Enmienda 3) es que no bastan, porque H6b no paso.
- La distincion "IPPO quita verde a E_C2, V2 sufre el giro E->S1" no se sostiene: con IPPO y con V2 el cuello es el
  mismo, el giro E->S1 en C1 (12-13 % del verde frente a 4 % con el fijo); C1 sirve unos 418 veh hacia el oeste por
  1800 s con los dos, y dar mas verde a E_C2 no lo cambia. Que IPPO alargue la transversal bloqueada es una asociacion
  ("mientras"), no una causa medida.
- Por que el fijo sufre tres veces menos el bloqueo E->S1 no esta medido; con desfases de 10-30 s el fijo lo resiste
  igual, y que bloquear mas W_C1 le abra huecos es solo una correlacion (rho -0.76, 45 corridas).
- "E_C2 descarga 0.377 frente a 0.439 veh/s" es del periodo 2, no de la hora; los costos por periodo de 5 semillas
  (+25.7, +68.0, +77.3, +244.1) con 10 semillas son +26.4, +73.4, +81.5 y +255.1, y el del fijo lo decide la semilla
  1002.
- El horizonte (H7) sigue abierto como alternativa: el entrenamiento con gamma 0.99 no se estabilizo.

La tesis (Seccion 5.5.1 y Anexo G) cita solo lo verificado.
