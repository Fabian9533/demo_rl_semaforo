# Dónde y cuándo se acumula el retraso con 2715 veh/h (agente "periodos", 25.10.2026)

Análisis posterior al veredicto (PRERREGISTRO.md) y descriptivo. No es la prueba de la Enmienda 3, que usa las
semillas 1001-1030 y 6001-6030, y no cambia ningún veredicto. Mide cuánto retraso tiene cada periodo, movimiento y
arista de entrada en el escenario original **O** (`dem_corredor_t2715`) y en el contrafactual **D**
(`dem_corredor_t2715_der`, con los giros del periodo 2 a la derecha), con cuatro controles.

## Qué se corrió

- **Corridas.** 2 escenarios × 4 controles × semillas 1001-1010 = 80 corridas (25.10.2026, 18:33-18:36), con las
  funciones de `evaluar.py` (`brazo_referencia`, `brazo_profundo`) y el código de la rama diagnostico-corredor tal como
  estaba a esa hora. Este análisis tuvo como mucho 4 SUMO a la vez.
- **Controles.**
  - Fijo: 25 s de avenida y 10 s de transversal, ámbar de 3 s, ciclo de 41 s y desfases 0/0. Es una copia de
    `plan2/dem_corredor_t2715.add.xml`, la misma en O y en D, cargada por un `.sumocfg` propio con rutas absolutas.
  - Actuado: el de SUMO (`comun.archivo_actuado`); su `.add.xml` se escribió en la carpeta de datos.
  - IPPO actual: `politica_dem_corredor_t2715_vecinos_s2042.pt`.
  - V2: `politica_dem_corredor_t2715_vecinos_v2_s42.pt`.
  - Las dos políticas se entrenaron en O. En D se juegan sin reentrenar.
- **Datos.** En cada corrida quedan el tripinfo completo (con `departDelay`), las estadísticas de SUMO, la fase de cada
  semáforo por segundo y los detenidos por acceso cada segundo. Están fuera del repositorio (137 MB), en
  `C:/Users/GAMER/AppData/Local/Temp/claude/c--Users-GAMER-Documents-demo-rl-semaforo/de7717ed-cbad-4afb-8e8f-03cbdcefb7fa/scratchpad/periodos/datos`.
- **Definiciones.**
  - Periodo: por la salida pedida (`depart − departDelay`); 1 si es antes de 1800 s, 2 si es desde 1800 s. Coincide con
    el prefijo del flujo (`p1_`, `p2_`) en las 80 corridas, y cada periodo tiene 1362 vehículos en todas.
  - Movimiento, por origen y destino: avenida (W↔E recto), transversal (N↔S recto), izquierda y derecha. Cada flujo
    de giro gira una sola vez.
  - Retraso total = timeLoss + espera para entrar (`departDelay`).
  - "s por vehículo del nivel" = s·veh del grupo dividido por los 2724 vehículos de la hora, como en
    `comp_aporte.csv`. Así, los aportes suman el cambio de la hora.
- **Reproducir** (desde `plan2/`):
  `python -B diag_corredor/periodos.py correr --datos <carpeta> --semillas 1001-1010 --procesos 4` (unos 2.5 min) y
  luego `python -B diag_corredor/periodos.py analizar --datos <carpeta> --semillas 1001-1010`. `analizar` escribe
  `periodos.csv`, `periodos_extra.csv` y `<carpeta>/periodos_tablas.md`, de donde salen las tablas de este archivo.

## Lo medido

1. **El periodo 2 de O es peor que el 1 con los cuatro controles. En D, mucho menos.** El cociente P2/P1 del
   retraso total en O es 1.85 con el fijo, 4.14 con IPPO actual, 3.68 con V2 y 9.76 con el actuado. En D baja a
   1.17, 1.37, 1.41 y 0.99. Tablas 1 y 2.
2. **Toda la desventaja de 2715 está en el periodo 2 de O.** En el periodo 1 (misma demanda en O y en D; el retraso
   por semilla difiere en menos de 0.1 s/veh), los tres controles adaptativos le ganan al fijo en 10 de 10 semillas:
   IPPO actual −9.6 s/veh (IC95 −10.4 a −8.8), V2 −6.6 (−7.9 a −5.2) y actuado −9.8 (−10.6 a −9.0). En el periodo 2
   de O pierden: IPPO actual +49.6 (+26.3 a +72.8), V2 +47.1 (+21.4 a +72.8) y actuado +211.9 (+181.7 a +242.0). En
   la hora, IPPO actual queda en +20.0 (+8.2 a +31.8) y V2 en +20.3 (+7.2 a +33.3). Tabla 3.
3. **En el periodo 2 de D ningún control adaptativo queda peor que el fijo** (ningún IC95 queda entero sobre
   cero). IPPO actual: −5.4 (t: −11.1 a +0.2; bootstrap: −10.2 a −1.1; 6 de 10 semillas). V2: +0.2 (−4.4 a +4.7).
   Actuado: −16.8 (−19.1 a −14.5). En la hora: IPPO actual −7.5 (−10.4 a −4.6, 10 de 10), V2 −3.2 (−6.0 a −0.4, 7
   de 10) y actuado −13.3 (−14.6 a −12.0). Tabla 3.
4. **Dónde (O, periodo 2).** Frente al fijo, IPPO actual pierde +24.8 s por vehículo del nivel en el periodo 2 y V2
   +23.6 (1.24 y 1.16 veces el cambio de la hora). Casi todo lo pierden los vehículos que entran por **E_C2**: +27.8
   y +29.1. Tabla 4.
   - La punta recta E→O (450 vehículos por corrida) pasa de 110.1 s/veh con el fijo a 262.7 con IPPO actual y 269.8
     con V2: aporta +25.2 y +26.4, y la mitad de eso es espera para entrar (+13.4 y +14.4).
   - Los que giran a la izquierda E→S1, que entran por la misma arista, aportan +2.6 y +2.7.
   - Los movimientos transversales mejoran (−1.9 y −3.2), sobre todo S2→N2: 68.6 s/veh con el fijo, 32.6 con IPPO
     actual y 34.3 con V2. La entrada W_C1 también mejora (−1.2 y −1.7).
5. **Cuándo (O, periodo 2).** El retraso crece durante todo el periodo. Para los que piden salir en los minutos
   30-35 y 50-55 es de 48 y 183 s/veh con IPPO actual, de 48 y 173 con V2 y de 42 y 92 con el fijo. Con el actuado
   sube de 87 (minutos 30-35) a 382 (minutos 45-50). Tabla 6.
   - La cola para entrar por E_C2 empieza en los minutos 40-45 con IPPO actual y V2 (4.0 y 7.8 vehículos esperando
     en promedio) y llega a 61 en los minutos 55-60.
   - Esa cola se forma en 10 de 10 semillas con IPPO actual, V2 y el actuado, y en 2 de 10 con el fijo (semillas 1002
     y 1010, con 86.9 y 43.4 s/veh de espera media en E_C2).
   - En D no se forma con ningún control (0 de 10). Tabla 9.
6. **Reparto del verde.** En el periodo 2 de O, C2 le da a la avenida el 0.577 del verde con IPPO actual (verde
   transversal mediano de 20 s, contra 10 s del fijo), el 0.667 con V2 (verde de avenida mediano de 20 s, contra 25 s)
   y el 0.638 con el actuado. El fijo le da el 0.714. En el periodo 2 de D, C2 da 0.712, 0.697 y 0.720. En C1, en el
   periodo 2 de O, queda en 0.709 (IPPO actual), 0.699 (V2) y 0.638 (actuado). Tabla 8.
7. **Colas por acceso (periodo 2, detenidos medios).**
   - E_C2 en O: 2.5 con el fijo, 11.7 con IPPO actual, 5.5 con V2 y 20.4 con el actuado. En D: 1.1, 1.7, 2.3 y 1.2.
   - S2_C2 en O: 4.0 con el fijo y 1.7 con IPPO actual y V2. En D: 0.8-1.1.
   - N1_C1 en O con el fijo: 3.8, frente a 0.8 en D. Tabla 7.
8. **Con el fijo, el periodo 2 también es peor en O que en D:** 71.9 frente a 45.5 s/veh de retraso total. Por
   movimiento, O frente a D:
   - S2→N2 recto: 68.6 frente a 22.3 s/veh. N1→S1: 64.4 frente a 22.2. W→E: 53.7 frente a 27.6. E→W: 110.1
     frente a 62.0.
   - Los giros a la izquierda tienen 112.6 (S2→W), 103.6 (E→S1), 59.2 (N1→E) y 35.9 s/veh (W→N1).
   - Por semilla, el periodo 2 de O con el fijo da 52-58 s/veh en 6 semillas, 66-84 en 2 y 112-135 en 2. Tablas 4,
     4b y `periodos.csv`.

## Lo inferido (no medido aquí)

- **Los accesos que empeoran con el fijo en el periodo 2 de O tienen algo en común.** En los tres, un vehículo que
  gira a la izquierda espera un hueco en un carril único: S2_C2 (S2→W cede a N2→S2), N1_C1 (N1→E cede a S1→N1) y W_C1
  (W→N1 cede a la punta E→O). Lo más probable es que ese vehículo detenga a los que siguen recto detrás. No se midió
  el bloqueo vehículo por vehículo.
- **Por qué pierden los controles adaptativos.** Con los giros a la izquierda se forma cola en S2_C2 (con el fijo,
  4.0 detenidos de media, frente a 0.8 en D). Los controles que responden a las colas le dan más verde (IPPO actual)
  o lo atienden más seguido (V2: verdes de avenida más cortos). Así, la fracción de verde de la avenida en C2 baja de
  0.714 a 0.58-0.67 justo cuando pasa la punta E→O. La demanda que cruza C2 hacia el oeste en ese periodo es de
  990 veh/h (E→W 900 + E→S1 90, `dem_corredor_t2715.rou.xml`).
  - Lo inferido es que ese verde ya no alcanza para la demanda. Por eso la cola crece durante el periodo y termina
    como espera para entrar en E_C2.
  - El fijo sostiene los 25 s de avenida, y lo pagan los accesos bloqueados.
  - En D, sin giros a la izquierda en el periodo 2, los adaptativos no recortan el verde de avenida (0.70-0.72 en
    C2) y le ganan al fijo en la hora.
  - Esto es coherente con H6, pero se basa en 10 semillas y en políticas que no se reentrenaron.
- **Por qué solo en 2715.** En `comp_movimientos.csv` (semillas 1001-1005, medido por `comportamiento.py`), el
  cociente P2/P1 de IPPO, del fijo y del actuado va de 0.95 a 1.15 en 905, 1358 y 1810 veh/h. En 2715 va de 1.83 a
  9.51 y en 3620 de 2.75 a 4.94.
  - Lo inferido es que con menos demanda la punta tiene holgura en C2, y quitarle verde a la avenida cuesta poco.
  - En 2715, el periodo 2 de O ya está al borde con el fijo (2 de 10 semillas forman cola para entrar), así que
    quitarle verde a la avenida lo hace pasar de la capacidad.
  - En 3620 todos los controles están saturados.
  - Para los otros niveles no se midió aquí el reparto del verde ni las colas.
- **Límites.**
  - Son 10 semillas, el análisis es descriptivo y no hay corrección por comparaciones múltiples.
  - D cambia qué tramo transversal lleva los giros: S1_C1 y N2_C2 en vez de S2_C2 y N1_C1. Con el fijo, las rectas
    de esos accesos en D (S1→N1 y N2→S2) tienen 47.5 y 49.4 s/veh, frente a 22.2-22.3 de las otras dos (tabla 4b).
  - Los detenidos (velocidad < 0.1 m/s) no cuentan las colas que avanzan despacio.
  - El periodo 2 de D no es igual al periodo 1 (fijo: 45.5 frente a 38.9 s/veh), aunque los flujos son su imagen
    girada. Con el fijo, el retraso ya sube dentro del periodo 1 (de 30 a 47 s/veh, tabla 6) y sigue subiendo en el
    periodo 2.

## Tablas

### (1) Retraso total medio por periodo (s/veh, media de las 10 semillas)

Fuente: `periodos.csv` (movimiento = todos, arista = todas).

| Esc. | Control | P1 | P1 timeLoss + espera | P2 | P2 timeLoss + espera | Hora | Hora timeLoss + espera |
|---|---|---|---|---|---|---|---|
| O | fijo 25/10 | 38.9 | 38.2 + 0.6 | 71.9 | 66.6 + 5.3 | 55.4 | 52.4 + 3.0 |
| O | actuado | 29.1 | 28.5 + 0.6 | 283.8 | 133.1 + 150.6 | 156.4 | 80.8 + 75.6 |
| O | IPPO actual (s2042) | 29.3 | 28.7 + 0.6 | 121.5 | 86.7 + 34.8 | 75.4 | 57.7 + 17.7 |
| O | V2 (s42) | 32.3 | 31.7 + 0.6 | 119.0 | 82.1 + 36.9 | 75.7 | 56.9 + 18.8 |
| D | fijo 25/10 | 38.9 | 38.2 + 0.6 | 45.5 | 44.8 + 0.6 | 42.2 | 41.5 + 0.6 |
| D | actuado | 29.1 | 28.4 + 0.6 | 28.7 | 28.0 + 0.6 | 28.9 | 28.2 + 0.6 |
| D | IPPO actual (s2042) | 29.3 | 28.7 + 0.6 | 40.0 | 39.4 + 0.6 | 34.7 | 34.0 + 0.6 |
| D | V2 (s42) | 32.3 | 31.7 + 0.6 | 45.6 | 45.0 + 0.6 | 39.0 | 38.3 + 0.6 |

Vehículos por corrida (todos los controles y semillas): O P1: [1362]; O P2: [1362]; D P1: [1362]; D P2: [1362]

### (2) Cociente periodo 2 / periodo 1

Fuente: `periodos.csv`.

| Esc. | Control | P1 (s/veh) | P2 (s/veh) | P2/P1 (de las medias) | P2/P1 por semilla (mín-máx) |
|---|---|---|---|---|---|
| O | fijo 25/10 | 38.9 | 71.9 | 1.85 | 1.36-3.57 |
| O | actuado | 29.1 | 283.8 | 9.76 | 8.37-10.74 |
| O | IPPO actual (s2042) | 29.3 | 121.5 | 4.14 | 3.55-4.90 |
| O | V2 (s42) | 32.3 | 119.0 | 3.68 | 3.10-4.59 |
| D | fijo 25/10 | 38.9 | 45.5 | 1.17 | 1.05-1.29 |
| D | actuado | 29.1 | 28.7 | 0.99 | 0.94-1.06 |
| D | IPPO actual (s2042) | 29.3 | 40.0 | 1.37 | 1.07-1.58 |
| D | V2 (s42) | 32.3 | 45.6 | 1.41 | 1.21-1.57 |

### (3) Diferencia pareada por semilla frente al fijo 25/10, retraso total medio (s/veh)

Fuente: `periodos.csv`. IC95 t: t de Student sobre las 10 diferencias. Bootstrap: pareado, percentil, 10 000
remuestreos (semilla 0). Wilcoxon: rangos con signo, exacto.

| Esc. | Comparación | Periodo | Media | IC95 t | IC95 bootstrap pareado | p Wilcoxon | Semillas mejor que el fijo | Mín / máx |
|---|---|---|---|---|---|---|---|---|
| O | IPPO actual (s2042) - fijo | 1 | -9.6 | [-10.4, -8.8] | [-10.3, -9.0] | 0.00195 | 10/10 | -12.0 / -8.4 |
| O | IPPO actual (s2042) - fijo | 2 | +49.6 | [+26.3, +72.8] | [+29.4, +67.6] | 0.00586 | 1/10 | -9.4 / +88.5 |
| O | IPPO actual (s2042) - fijo | hora | +20.0 | [+8.2, +31.8] | [+10.0, +29.1] | 0.0137 | 2/10 | -8.9 / +39.7 |
| O | V2 (s42) - fijo | 1 | -6.6 | [-7.9, -5.2] | [-7.8, -5.5] | 0.00195 | 10/10 | -10.3 / -4.2 |
| O | V2 (s42) - fijo | 2 | +47.1 | [+21.4, +72.8] | [+24.6, +66.8] | 0.00977 | 1/10 | -23.8 / +90.3 |
| O | V2 (s42) - fijo | hora | +20.3 | [+7.2, +33.3] | [+8.9, +30.3] | 0.0137 | 2/10 | -15.1 / +42.6 |
| O | actuado - fijo | 1 | -9.8 | [-10.6, -9.0] | [-10.5, -9.2] | 0.00195 | 10/10 | -11.7 / -8.4 |
| O | actuado - fijo | 2 | +211.9 | [+181.7, +242.0] | [+185.0, +234.4] | 0.00195 | 0/10 | +124.2 / +255.7 |
| O | actuado - fijo | hora | +101.0 | [+85.7, +116.4] | [+87.4, +112.5] | 0.00195 | 0/10 | +57.1 / +123.4 |
| D | IPPO actual (s2042) - fijo | 1 | -9.6 | [-10.4, -8.8] | [-10.3, -9.0] | 0.00195 | 10/10 | -12.0 / -8.5 |
| D | IPPO actual (s2042) - fijo | 2 | -5.4 | [-11.1, +0.2] | [-10.2, -1.1] | 0.131 | 6/10 | -20.5 / +3.2 |
| D | IPPO actual (s2042) - fijo | hora | -7.5 | [-10.4, -4.6] | [-10.0, -5.3] | 0.00195 | 10/10 | -15.7 / -3.0 |
| D | V2 (s42) - fijo | 1 | -6.6 | [-7.9, -5.2] | [-7.8, -5.5] | 0.00195 | 10/10 | -10.3 / -4.2 |
| D | V2 (s42) - fijo | 2 | +0.2 | [-4.4, +4.7] | [-3.7, +3.8] | 0.922 | 5/10 | -11.1 / +8.9 |
| D | V2 (s42) - fijo | hora | -3.2 | [-6.0, -0.4] | [-5.6, -1.0] | 0.0488 | 7/10 | -10.7 / +1.9 |
| D | actuado - fijo | 1 | -9.8 | [-10.6, -9.0] | [-10.5, -9.1] | 0.00195 | 10/10 | -11.8 / -8.4 |
| D | actuado - fijo | 2 | -16.8 | [-19.1, -14.5] | [-18.8, -15.0] | 0.00195 | 10/10 | -23.2 / -12.8 |
| D | actuado - fijo | hora | -13.3 | [-14.6, -12.0] | [-14.5, -12.3] | 0.00195 | 10/10 | -17.5 / -11.3 |

### (4) O, periodo 2: de dónde sale el cambio frente al fijo

Fuente: `periodos.csv` (el aporte de cada grupo es la media × vehículos del grupo, menos la del fijo, sobre los 2724
vehículos de la hora). En el periodo 2 de O, cada fila "<movimiento> desde <arista>" es un solo flujo: las izquierdas
son S2→W (S2_C2), W→N1 (W_C1), E→S1 (E_C2) y N1→E (N1_C1), y las rectas son el flujo recto de esa arista.

Aporte = (s.veh del grupo con el control - s.veh del grupo con el fijo) / vehículos de la hora, media de las semillas; entre paréntesis, timeLoss / espera para entrar. Fracción = aporte / cambio de la hora. Cambio de la hora frente al fijo: IPPO actual (s2042) +20.00, V2 (s42) +20.27, actuado +101.04 s/veh.

| Grupo | Veh. por corrida | Fijo (s/veh) | IPPO actual (s2042) (s/veh) | Aporte IPPO actual (s2042) | Fracción | V2 (s42) (s/veh) | Aporte V2 (s42) | Fracción | actuado (s/veh) | Aporte actuado | Fracción |
|---|---|---|---|---|---|---|---|---|---|---|---|
| periodo 2, todos | 1362 | 71.9 | 121.5 | +24.78 (+10.06 / +14.73) | 1.24 | 119.0 | +23.56 (+7.77 / +15.78) | 1.16 | 283.8 | +105.93 (+33.29 / +72.64) | 1.05 |
| avenida | 638 | 93.5 | 196.8 | +24.19 (+10.78 / +13.40) | 1.21 | 199.9 | +24.92 (+10.54 / +14.38) | 1.23 | 466.3 | +87.31 (+21.68 / +65.63) | 0.86 |
| transversal | 544 | 44.6 | 35.1 | -1.91 (-1.91 / +0.00) | -0.10 | 28.4 | -3.24 (-3.24 / +0.00) | -0.16 | 76.1 | +6.29 (+5.89 / +0.39) | 0.06 |
| izquierda | 180 | 77.8 | 115.6 | +2.50 (+1.18 / +1.32) | 0.12 | 106.3 | +1.88 (+0.48 / +1.40) | 0.09 | 264.5 | +12.34 (+5.72 / +6.62) | 0.12 |
| entra por W_C1 | 233 | 50.3 | 36.5 | -1.18 (-1.18 / +0.00) | -0.06 | 30.1 | -1.72 (-1.72 / +0.00) | -0.09 | 43.4 | -0.59 (-0.59 / +0.00) | -0.01 |
| entra por E_C2 | 495 | 109.5 | 262.4 | +27.79 (+13.06 / +14.73) | 1.39 | 269.5 | +29.08 (+13.29 / +15.78) | 1.43 | 641.6 | +96.69 (+24.58 / +72.11) | 0.96 |
| entra por N1_C1 | 181 | 63.1 | 63.9 | +0.05 (+0.05 / -0.00) | 0.00 | 34.3 | -1.91 (-1.91 / +0.00) | -0.09 | 55.0 | -0.54 (-0.54 / -0.00) | -0.01 |
| entra por S1_C1 | 136 | 22.7 | 22.8 | +0.00 (+0.00 / +0.00) | 0.00 | 22.5 | -0.01 (-0.01 / +0.00) | -0.00 | 33.3 | +0.53 (+0.53 / +0.00) | 0.01 |
| entra por N2_C2 | 136 | 22.7 | 21.0 | -0.08 (-0.08 / +0.00) | -0.00 | 21.9 | -0.04 (-0.04 / +0.00) | -0.00 | 33.6 | +0.54 (+0.54 / +0.00) | 0.01 |
| entra por S2_C2 | 181 | 79.5 | 52.5 | -1.80 (-1.80 / +0.00) | -0.09 | 52.0 | -1.83 (-1.83 / +0.00) | -0.09 | 219.6 | +9.31 (+8.77 / +0.53) | 0.09 |
| avenida desde W_C1 | 188 | 53.7 | 38.9 | -1.02 (-1.02 / +0.00) | -0.05 | 32.5 | -1.46 (-1.46 / +0.00) | -0.07 | 45.8 | -0.54 (-0.54 / +0.00) | -0.01 |
| avenida desde E_C2 | 450 | 110.1 | 262.7 | +25.21 (+11.81 / +13.40) | 1.26 | 269.8 | +26.38 (+12.00 / +14.38) | 1.30 | 641.9 | +87.85 (+22.22 / +65.63) | 0.87 |
| transversal desde N1_C1 | 136 | 64.4 | 63.9 | -0.03 (-0.03 / +0.00) | -0.00 | 34.8 | -1.48 (-1.48 / +0.00) | -0.07 | 49.9 | -0.73 (-0.73 / +0.00) | -0.01 |
| transversal desde S1_C1 | 136 | 22.7 | 22.8 | +0.00 (+0.00 / +0.00) | 0.00 | 22.5 | -0.01 (-0.01 / +0.00) | -0.00 | 33.3 | +0.53 (+0.53 / +0.00) | 0.01 |
| transversal desde N2_C2 | 136 | 22.7 | 21.0 | -0.08 (-0.08 / +0.00) | -0.00 | 21.9 | -0.04 (-0.04 / +0.00) | -0.00 | 33.6 | +0.54 (+0.54 / +0.00) | 0.01 |
| transversal desde S2_C2 | 136 | 68.6 | 32.6 | -1.80 (-1.80 / +0.00) | -0.09 | 34.3 | -1.71 (-1.71 / +0.00) | -0.08 | 187.6 | +5.94 (+5.55 / +0.39) | 0.06 |
| izquierda desde W_C1 | 45 | 35.9 | 26.5 | -0.16 (-0.16 / +0.00) | -0.01 | 20.0 | -0.26 (-0.26 / +0.00) | -0.01 | 33.1 | -0.05 (-0.05 / +0.00) | -0.00 |
| izquierda desde E_C2 | 45 | 103.6 | 259.5 | +2.58 (+1.25 / +1.32) | 0.13 | 267.1 | +2.70 (+1.30 / +1.40) | 0.13 | 638.3 | +8.83 (+2.36 / +6.48) | 0.09 |
| izquierda desde N1_C1 | 45 | 59.2 | 63.9 | +0.08 (+0.08 / -0.00) | 0.00 | 32.8 | -0.44 (-0.44 / +0.00) | -0.02 | 70.4 | +0.19 (+0.19 / +0.00) | 0.00 |
| izquierda desde S2_C2 | 45 | 112.6 | 112.6 | +0.00 (+0.00 / +0.00) | 0.00 | 105.4 | -0.12 (-0.12 / +0.00) | -0.01 | 316.3 | +3.36 (+3.22 / +0.14) | 0.03 |

IC95 t del aporte en O, periodo 2 (s por vehículo del nivel):

| Grupo | Aporte IPPO actual (s2042) | Aporte V2 (s42) |
|---|---|---|
| periodo 2, todos | +24.78 [+13.17, +36.39] | +23.56 [+10.71, +36.41] |
| avenida | +24.19 [+15.02, +33.36] | +24.92 [+14.64, +35.19] |
| transversal | -1.91 [-3.03, -0.78] | -3.24 [-4.35, -2.14] |
| izquierda | +2.50 [+1.08, +3.92] | +1.88 [+0.33, +3.44] |
| entra por W_C1 | -1.18 [-1.84, -0.52] | -1.72 [-2.21, -1.24] |
| entra por E_C2 | +27.79 [+17.30, +38.28] | +29.08 [+17.44, +40.72] |
| entra por N1_C1 | +0.05 [-0.63, +0.73] | -1.91 [-2.54, -1.28] |
| entra por S1_C1 | +0.00 [-0.03, +0.03] | -0.01 [-0.04, +0.01] |
| entra por N2_C2 | -0.08 [-0.13, -0.04] | -0.04 [-0.09, +0.00] |
| entra por S2_C2 | -1.80 [-2.88, -0.71] | -1.83 [-2.93, -0.73] |
| avenida desde W_C1 | -1.02 [-1.55, -0.49] | -1.46 [-1.85, -1.07] |

### (4b) D, periodo 2: lo mismo en el contrafactual

Fuente: `periodos.csv`, como la tabla 4. En D, las derechas del periodo 2 son S1→E (S1_C1), E→N1 (E_C2), W→S2 (W_C1) y
N2→W (N2_C2).

Aporte = (s.veh del grupo con el control - s.veh del grupo con el fijo) / vehículos de la hora, media de las semillas; entre paréntesis, timeLoss / espera para entrar. Fracción = aporte / cambio de la hora. Cambio de la hora frente al fijo: IPPO actual (s2042) -7.50, V2 (s42) -3.20, actuado -13.28 s/veh.

| Grupo | Veh. por corrida | Fijo (s/veh) | IPPO actual (s2042) (s/veh) | Aporte IPPO actual (s2042) | Fracción | V2 (s42) (s/veh) | Aporte V2 (s42) | Fracción | actuado (s/veh) | Aporte actuado | Fracción |
|---|---|---|---|---|---|---|---|---|---|---|---|
| periodo 2, todos | 1362 | 45.5 | 40.0 | -2.72 (-2.72 / +0.00) | 0.36 | 45.6 | +0.08 (+0.08 / +0.00) | -0.02 | 28.7 | -8.39 (-8.39 / +0.00) | 0.63 |
| avenida | 638 | 51.8 | 49.6 | -0.52 (-0.52 / +0.00) | 0.07 | 60.7 | +2.08 (+2.08 / +0.00) | -0.65 | 28.1 | -5.57 (-5.57 / +0.00) | 0.42 |
| transversal | 544 | 35.3 | 26.7 | -1.72 (-1.72 / +0.00) | 0.23 | 25.9 | -1.89 (-1.89 / +0.00) | 0.59 | 28.0 | -1.46 (-1.46 / +0.00) | 0.11 |
| derecha | 180 | 53.5 | 46.2 | -0.48 (-0.48 / +0.00) | 0.06 | 51.7 | -0.12 (-0.12 / -0.00) | 0.04 | 32.8 | -1.36 (-1.36 / +0.00) | 0.10 |
| entra por W_C1 | 233 | 27.7 | 21.9 | -0.50 (-0.50 / +0.00) | 0.07 | 22.1 | -0.48 (-0.48 / +0.00) | 0.15 | 20.1 | -0.66 (-0.66 / +0.00) | 0.05 |
| entra por E_C2 | 495 | 61.3 | 61.1 | -0.03 (-0.03 / +0.00) | 0.00 | 77.0 | +2.86 (+2.86 / +0.00) | -0.89 | 31.4 | -5.42 (-5.42 / +0.00) | 0.41 |
| entra por N1_C1 | 136 | 22.2 | 20.7 | -0.07 (-0.07 / +0.00) | 0.01 | 21.8 | -0.02 (-0.02 / +0.00) | 0.01 | 28.2 | +0.30 (+0.30 / +0.00) | -0.02 |
| entra por S1_C1 | 181 | 47.4 | 29.0 | -1.22 (-1.22 / +0.00) | 0.16 | 24.4 | -1.53 (-1.53 / -0.00) | 0.48 | 32.2 | -1.01 (-1.01 / -0.00) | 0.08 |
| entra por N2_C2 | 181 | 58.1 | 43.6 | -0.96 (-0.96 / +0.00) | 0.13 | 47.4 | -0.71 (-0.71 / -0.00) | 0.22 | 31.0 | -1.80 (-1.80 / -0.00) | 0.14 |
| entra por S2_C2 | 136 | 22.3 | 23.6 | +0.07 (+0.07 / +0.00) | -0.01 | 21.3 | -0.05 (-0.05 / +0.00) | 0.01 | 26.1 | +0.19 (+0.19 / +0.00) | -0.01 |
| avenida desde W_C1 | 188 | 27.6 | 22.3 | -0.37 (-0.37 / +0.00) | 0.05 | 21.9 | -0.40 (-0.40 / +0.00) | 0.12 | 20.1 | -0.52 (-0.52 / +0.00) | 0.04 |
| avenida desde E_C2 | 450 | 62.0 | 61.0 | -0.15 (-0.15 / +0.00) | 0.02 | 77.0 | +2.48 (+2.48 / +0.00) | -0.78 | 31.4 | -5.05 (-5.05 / +0.00) | 0.38 |
| transversal desde N1_C1 | 136 | 22.2 | 20.7 | -0.07 (-0.07 / +0.00) | 0.01 | 21.8 | -0.02 (-0.02 / +0.00) | 0.01 | 28.2 | +0.30 (+0.30 / +0.00) | -0.02 |
| transversal desde S1_C1 | 136 | 47.5 | 29.2 | -0.91 (-0.91 / +0.00) | 0.12 | 23.2 | -1.21 (-1.21 / +0.00) | 0.38 | 30.0 | -0.87 (-0.87 / +0.00) | 0.07 |
| transversal desde N2_C2 | 136 | 49.4 | 33.4 | -0.80 (-0.80 / +0.00) | 0.11 | 37.1 | -0.61 (-0.61 / +0.00) | 0.19 | 27.8 | -1.08 (-1.08 / +0.00) | 0.08 |
| transversal desde S2_C2 | 136 | 22.3 | 23.6 | +0.07 (+0.07 / +0.00) | -0.01 | 21.3 | -0.05 (-0.05 / +0.00) | 0.01 | 26.1 | +0.19 (+0.19 / +0.00) | -0.01 |
| derecha desde W_C1 | 45 | 28.1 | 20.3 | -0.13 (-0.13 / +0.00) | 0.02 | 23.3 | -0.08 (-0.08 / +0.00) | 0.02 | 20.1 | -0.13 (-0.13 / +0.00) | 0.01 |
| derecha desde E_C2 | 45 | 54.1 | 61.5 | +0.12 (+0.12 / +0.00) | -0.02 | 77.1 | +0.38 (+0.38 / +0.00) | -0.12 | 31.5 | -0.37 (-0.37 / +0.00) | 0.03 |
| derecha desde S1_C1 | 45 | 47.1 | 28.5 | -0.31 (-0.31 / +0.00) | 0.04 | 27.9 | -0.32 (-0.32 / -0.00) | 0.10 | 38.9 | -0.13 (-0.13 / -0.00) | 0.01 |
| derecha desde N2_C2 | 45 | 84.6 | 74.6 | -0.16 (-0.16 / +0.00) | 0.02 | 78.3 | -0.10 (-0.10 / -0.00) | 0.03 | 40.8 | -0.72 (-0.72 / -0.00) | 0.05 |

### (6) Cuándo: retraso total medio según el tramo de 5 min de la salida pedida (s/veh)

Fuente: `periodos_extra.csv` (medida = retraso_total_por_tramo_5min).

| Esc. | Control | 0-5 | 5-10 | 10-15 | 15-20 | 20-25 | 25-30 | 30-35 | 35-40 | 40-45 | 45-50 | 50-55 | 55-60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| O | fijo 25/10 | 30 | 34 | 39 | 40 | 44 | 47 | 42 | 52 | 67 | 78 | 92 | 101 |
| O | actuado | 27 | 29 | 30 | 29 | 30 | 30 | 87 | 211 | 339 | 382 | 360 | 327 |
| O | IPPO actual (s2042) | 27 | 29 | 30 | 29 | 29 | 31 | 48 | 76 | 109 | 152 | 183 | 162 |
| O | V2 (s42) | 29 | 31 | 32 | 33 | 34 | 35 | 48 | 84 | 115 | 146 | 173 | 150 |
| D | fijo 25/10 | 30 | 34 | 39 | 40 | 44 | 46 | 38 | 40 | 44 | 47 | 50 | 54 |
| D | actuado | 27 | 29 | 30 | 29 | 30 | 30 | 29 | 29 | 30 | 28 | 28 | 28 |
| D | IPPO actual (s2042) | 27 | 29 | 30 | 29 | 29 | 30 | 31 | 34 | 38 | 42 | 46 | 49 |
| D | V2 (s42) | 29 | 31 | 32 | 33 | 34 | 35 | 34 | 39 | 45 | 48 | 54 | 54 |

### (7) Dónde: detenidos medios por acceso

Fuente: `periodos_extra.csv` (medida = detenidos_medios, seg_enlace_interno_ge34, fin_corrida_s). Se cuentan cada
segundo; el periodo 1 va hasta t < 1800 s y el 2 de 1800 a 3600 s. Los enlaces internos C1_C2 y C2_C1 tienen 38
plazas, y 34 es el 90 %.

| Esc. | Control | Periodo | W_C1 | C2_C1 | N1_C1 | S1_C1 | C1_C2 | E_C2 | N2_C2 | S2_C2 | s con un enlace interno >= 34 detenidos | Fin de la corrida (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| O | fijo 25/10 | 1 | 1.1 | 0.7 | 0.8 | 1.5 | 3.2 | 0.4 | 1.5 | 0.8 | 0 |  |
| O | fijo 25/10 | 2 | 2.0 | 3.6 | 3.8 | 0.9 | 1.1 | 2.5 | 0.9 | 4.0 | 0 | 3759-4084 |
| O | actuado | 1 | 1.2 | 0.3 | 1.1 | 1.6 | 0.9 | 0.5 | 1.7 | 1.2 | 0 |  |
| O | actuado | 2 | 2.0 | 14.2 | 3.0 | 1.6 | 1.2 | 20.4 | 1.6 | 11.6 | 4 | 4331-4490 |
| O | IPPO actual (s2042) | 1 | 1.3 | 0.4 | 0.8 | 1.2 | 1.3 | 0.4 | 2.1 | 1.0 | 0 |  |
| O | IPPO actual (s2042) | 2 | 1.3 | 4.6 | 3.7 | 0.8 | 0.9 | 11.7 | 0.8 | 1.7 | 0 | 3958-4083 |
| O | V2 (s42) | 1 | 1.3 | 0.4 | 0.8 | 1.1 | 1.4 | 0.4 | 3.4 | 0.9 | 0 |  |
| O | V2 (s42) | 2 | 0.9 | 4.7 | 1.7 | 0.8 | 0.7 | 5.5 | 0.9 | 1.7 | 0 | 3942-4049 |
| D | fijo 25/10 | 1 | 1.1 | 0.7 | 0.8 | 1.5 | 3.2 | 0.4 | 1.5 | 0.8 | 0 |  |
| D | fijo 25/10 | 2 | 0.4 | 3.4 | 0.8 | 2.9 | 1.0 | 1.1 | 3.0 | 0.8 | 0 | 3757-3767 |
| D | actuado | 1 | 1.2 | 0.3 | 1.1 | 1.6 | 0.9 | 0.5 | 1.7 | 1.2 | 0 |  |
| D | actuado | 2 | 0.5 | 0.8 | 1.3 | 1.8 | 0.4 | 1.2 | 1.6 | 1.1 | 0 | 3702-3723 |
| D | IPPO actual (s2042) | 1 | 1.3 | 0.4 | 0.8 | 1.2 | 1.3 | 0.4 | 2.1 | 1.0 | 0 |  |
| D | IPPO actual (s2042) | 2 | 0.4 | 3.0 | 0.8 | 1.4 | 0.5 | 1.7 | 1.9 | 0.9 | 0 | 3725-3775 |
| D | V2 (s42) | 1 | 1.3 | 0.4 | 0.8 | 1.1 | 1.4 | 0.4 | 3.4 | 0.9 | 0 |  |
| D | V2 (s42) | 2 | 0.5 | 3.3 | 0.8 | 1.1 | 0.5 | 2.3 | 2.1 | 0.8 | 0 | 3734-3785 |

### (8) Reparto del verde por cruce y periodo

Fuente: `periodos_extra.csv` (medida = frac_verde_avenida, verde_avenida_mediana, verde_transversal_mediana).
Calculado con `comportamiento.analizar_fases` sobre la fase por segundo.

| Esc. | Control | Periodo | C1 avenida | C1 transversal | C1 frac. avenida | C2 avenida | C2 transversal | C2 frac. avenida |
|---|---|---|---|---|---|---|---|---|
| O | fijo 25/10 | 1 | 25 (25-25) | 10 (10-10) | 0.714 | 25 (25-25) | 10 (10-10) | 0.714 |
| O | fijo 25/10 | 2 | 25 (25-25) | 10 (10-10) | 0.714 | 25 (25-25) | 10 (10-10) | 0.714 |
| O | actuado | 1 | 32 (21-48) | 13 (10-18) | 0.712 | 35 (20-52) | 13 (10-18) | 0.720 |
| O | actuado | 2 | 60 (46-60) | 33 (20-43) | 0.638 | 60 (43-60) | 29 (14-60) | 0.638 |
| O | IPPO actual (s2042) | 1 | 25 (20-25) | 10 (10-10) | 0.705 | 30 (26-35) | 10 (10-15) | 0.731 |
| O | IPPO actual (s2042) | 2 | 25 (20-30) | 10 (10-10) | 0.709 | 30 (25-35) | 20 (15-30) | 0.577 |
| O | V2 (s42) | 1 | 25 (20-25) | 10 (10-10) | 0.705 | 25 (20-30) | 10 (10-10) | 0.725 |
| O | V2 (s42) | 2 | 25 (20-25) | 10 (10-10) | 0.699 | 20 (10-25) | 10 (10-10) | 0.667 |
| D | fijo 25/10 | 1 | 25 (25-25) | 10 (10-10) | 0.714 | 25 (25-25) | 10 (10-10) | 0.714 |
| D | fijo 25/10 | 2 | 25 (25-25) | 10 (10-10) | 0.714 | 25 (25-25) | 10 (10-10) | 0.714 |
| D | actuado | 1 | 32 (21-48) | 13 (10-18) | 0.712 | 35 (20-52) | 13 (10-18) | 0.720 |
| D | actuado | 2 | 35 (23-54) | 13 (10-18) | 0.727 | 32 (23-46) | 12 (10-17) | 0.720 |
| D | IPPO actual (s2042) | 1 | 25 (20-25) | 10 (10-10) | 0.705 | 30 (26-35) | 10 (10-15) | 0.731 |
| D | IPPO actual (s2042) | 2 | 25 (20-25) | 10 (10-10) | 0.707 | 30 (25-35) | 10 (10-15) | 0.712 |
| D | V2 (s42) | 1 | 25 (20-25) | 10 (10-10) | 0.705 | 25 (20-30) | 10 (10-10) | 0.725 |
| D | V2 (s42) | 2 | 25 (20-25) | 10 (10-10) | 0.700 | 25 (15-30) | 10 (10-10) | 0.697 |

### (9) Cola para entrar por E_C2 (la entrada de la punta E→O del periodo 2)

Fuente: `periodos_extra.csv` (medida = esperando_entrar_E_C2, espera_media_E_C2). Cuenta los vehículos con
salida pedida ≤ t < salida real.

| Esc. | Control | 30-35 | 35-40 | 40-45 | 45-50 | 50-55 | 55-60 | 60-65 | 65-70 | Semillas con espera media en E_C2 (P2) > 5 s | Espera media en E_C2, P2 (mín-máx de las semillas, s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| O | fijo 25/10 | 0.3 | 0.2 | 0.6 | 2.8 | 5.4 | 9.3 | 4.3 | 0.0 | 2/10 | 0.5-86.9 |
| O | actuado | 0.3 | 5.2 | 40.8 | 83.2 | 125.7 | 167.9 | 165.2 | 82.8 | 10/10 | 323.7-468.3 |
| O | IPPO actual (s2042) | 0.3 | 0.2 | 4.0 | 16.7 | 38.3 | 61.1 | 36.2 | 0.2 | 10/10 | 58.1-132.5 |
| O | V2 (s42) | 0.3 | 0.4 | 7.8 | 21.8 | 41.1 | 60.6 | 34.7 | 0.0 | 10/10 | 65.4-150.3 |
| D | fijo 25/10 | 0.3 | 0.2 | 0.3 | 0.2 | 0.3 | 0.2 | 0.0 | 0.0 | 0/10 | 0.5-0.6 |
| D | actuado | 0.3 | 0.2 | 0.3 | 0.2 | 0.3 | 0.2 | 0.0 | 0.0 | 0/10 | 0.5-0.6 |
| D | IPPO actual (s2042) | 0.3 | 0.2 | 0.3 | 0.2 | 0.3 | 0.2 | 0.0 | 0.0 | 0/10 | 0.5-0.6 |
| D | V2 (s42) | 0.3 | 0.2 | 0.3 | 0.2 | 0.3 | 0.2 | 0.0 | 0.0 | 0/10 | 0.5-0.5 |

## (5) Comprobación de determinismo

Fuente: `periodos_extra.csv` (medida = determinismo), `<datos>/metricas_<E>_<control>.csv` y las evaluaciones de
referencia que nombra la tabla.

- **Obligatoria (O, semillas 1001-1005).** Las 20 corridas dan el mismo `retraso_total_prom` que la evaluación del
  plan, y también los mismos timeLoss, espera para entrar, cambios de fase y no insertados. Fijo, semilla 1001: 45.07
  s/veh, igual que `demanda2/eval_dem_corredor_t2715_fijo.csv`.
- **Resto.** Las 80 corridas (O y D, 1001-1010) son iguales a su referencia: la del plan en O y la de la cola
  (`diag_corredor/eval3/eval_d_*_1001.csv`, 18:20, mismo programa 25/10) en D. Las fases de la semilla 1001 son
  idénticas en los 8 casos.
- **Otras comprobaciones.**
  - La media de timeLoss + departDelay del tripinfo guardado es el `retraso_total_prom` de cada corrida (80/80).
  - No quedan vehículos sin insertar.
  - Hay 0 teletransportes, pero porque la configuración los desactiva (`time-to-teleport -1`).
  - Con 1001-1005, los retrasos por movimiento y periodo de O (fijo, actuado e IPPO actual) son los 36 de
    `comp_movimientos.csv` (nivel 2715), con "giros" = izquierda + derecha.

Igual = retraso_total_prom, timeloss_prom, retraso_insercion_prom, cambios_fase y no_insertados iguales. Tripinfo = la media de timeLoss + departDelay del tripinfo guardado, redondeada a 2, es el retraso_total_prom de la corrida.

| Esc. | Control | Referencia (plan2/) | Iguales 1001-1005 | Iguales 1001-1010 | Dif. máx. retraso total | Fases s1001 iguales | Tripinfo = métrica | No insertados | Vehículos |
|---|---|---|---|---|---|---|---|---|---|
| O | fijo 25/10 | demanda2/eval_dem_corredor_t2715_fijo.csv | 5/5 | 10/10 | 0.00 | True | 10/10 | [0] | [2724] |
| O | actuado | demanda2/eval_dem_corredor_t2715_actuado.csv | 5/5 | 10/10 | 0.00 | True | 10/10 | [0] | [2724] |
| O | IPPO actual (s2042) | demanda2/eval_dem_corredor_t2715_ippo_vecinos_s2042.csv | 5/5 | 10/10 | 0.00 | True | 10/10 | [0] | [2724] |
| O | V2 (s42) | diag_corredor/eval/eval_dem_corredor_t2715_ippo_vecinos_v2_s42_1001.csv | 5/5 | 10/10 | 0.00 | True | 10/10 | [0] | [2724] |
| D | fijo 25/10 | diag_corredor/eval3/eval_d_fijo2715_1001.csv | 5/5 | 10/10 | 0.00 | True | 10/10 | [0] | [2724] |
| D | actuado | diag_corredor/eval3/eval_d_actuado_1001.csv | 5/5 | 10/10 | 0.00 | True | 10/10 | [0] | [2724] |
| D | IPPO actual (s2042) | diag_corredor/eval3/eval_d_ippo_actual_1001.csv | 5/5 | 10/10 | 0.00 | True | 10/10 | [0] | [2724] |
| D | V2 (s42) | diag_corredor/eval3/eval_d_ippo_v2_1001.csv | 5/5 | 10/10 | 0.00 | True | 10/10 | [0] | [2724] |

Semilla 1001, retraso total (esta corrida / referencia): O fijo 45.07 / 45.07; O actuado 168.45 / 168.45; O actual 65.87 / 65.87; O v2 80.29 / 80.29; D fijo 40.99 / 40.99; D actuado 28.24 / 28.24; D actual 35.48 / 35.48; D v2 35.02 / 35.02

En todas las corridas el periodo por la salida pedida coincide con el prefijo del flujo (p1_/p2_).
