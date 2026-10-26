# Verde bloqueado por los giros a la izquierda en 2715 veh/h (diagnóstico del corredor, 25.10.2026)

Análisis posterior al veredicto (PRERREGISTRO.md, Enmienda 3). No cambia ningún veredicto ni ningún archivo del
plan. Pregunta: ¿qué pasa segundo a segundo en los cruces cuando hay giros a la izquierda permitidos, y por qué
le cuestan más a IPPO y al actuado que al fijo?

## Datos y método

- **Escenarios.** O = `dem_corredor_t2715` (giros del periodo 2 a la izquierda: S2->W, W->N1, E->S1 y N1->E, 90 veh/h
  cada uno, 45 vehículos por periodo). D = `dem_corredor_t2715_der` (esos cuatro giros a la derecha). La red, los
  demás flujos y el periodo 1 son iguales.
- **Controles.** Fijo 25/10 s con desfases 0/0 (copia de `dem_corredor_t2715.add.xml`, la misma en O y en D; el
  `.add.xml` de D lo reescribió el barrido de la cola a las 18:48 y no se usó), actuado, IPPO con mensajes en su
  versión evaluada (`politica_dem_corredor_t2715_vecinos_s2042.pt`) y V2 (`politica_dem_corredor_t2715_vecinos_v2_s42.pt`).
  Semillas 1001-1005: 2 × 4 × 5 = 40 corridas.
- **Medición.** `bloqueo.py` corre cada caso con las funciones de `evaluar.py` y reemplaza `traci.simulationStep`
  por una envoltura que, después de cada paso, lee con TraCI el estado de los semáforos, y en las 8 aristas de
  acceso los vehículos, los detenidos, los cruces de la línea y el vehículo de cabeza. Además lee el espacio libre
  al inicio de los enlaces C1_C2 y C2_C1 y los vehículos que esperan para entrar. Solo usa lecturas y suscripciones
  de vehículos, así que no toca las suscripciones del control.
- **Definiciones.**
  - **Cabeza:** el vehículo más avanzado entre los del carril y los del primer tramo interno de sus tres
    movimientos. El que gira a la izquierda espera el hueco **dentro del cruce**, al final de un tramo de 4.07 m,
    con 0.93 m de su cola aún sobre el carril.
  - **Detenido:** velocidad menor que 0.1 m/s.
  - **Verde de un acceso:** su movimiento recto en G (la izquierda va en g, sin prioridad).
  - **Descarga:** vehículos que cruzan la línea por segundo de verde. "Con cola" cuenta solo los segundos que
    empiezan con al menos un detenido en el carril.
  - **Derrame:** cabeza detenida en verde, que no gira a la izquierda, cuya salida es un enlace con menos de una
    plaza (7.5 m) libre al inicio.
  - **Cola hasta el cruce:** el enlace tiene menos de una plaza libre al inicio y su último vehículo va a menos
    de 2 m/s. En la versión estricta, ese vehículo está detenido.
  - **Periodos:** P1 = segundos 1-1800 y P2 = 1801-3600. En el retraso por periodo cuenta el flujo de cada
    vehículo, como en `comportamiento.py` (se usan sus funciones `leer_trip` y `leer_flujos`).
- Las tablas son medias por corrida de las 5 semillas, impresas por `python diag_corredor/bloqueo.py tablas`
  desde los CSV de esta carpeta.

## Comprobación de determinismo

Las 40 corridas dan exactamente el retraso total, el timeLoss, la espera para entrar, los cambios de fase, los no
insertados y los vehículos de la evaluación del plan con la misma semilla (`bloqueo_control.csv`, columna
`igual_al_plan`). La envoltura no cambia la simulación.

| escenario | control | retraso total por corrida, semillas 1001-1005 (s/veh) | igual a la evaluación |
|---|---|---|---|
| O | fijo 25/10 | 45.07 / 86.63 / 45.11 / 45.94 / 49.05 | 5 de 5 (`demanda2/eval_dem_corredor_t2715_fijo.csv`) |
| O | actuado | 168.45 / 143.7 / 157.19 / 148.73 / 133.97 | 5 de 5 (`demanda2/eval_dem_corredor_t2715_actuado.csv`) |
| O | IPPO actual (s2042) | 65.87 / 77.72 / 82.08 / 68.87 / 75.93 | 5 de 5 (`demanda2/eval_dem_corredor_t2715_ippo_vecinos_s2042.csv`) |
| O | V2 (s42) | 80.29 / 71.53 / 78.18 / 69.62 / 69.75 | 5 de 5 (`diag_corredor/eval/eval_dem_corredor_t2715_ippo_vecinos_v2_s42_1001.csv`) |
| D | fijo 25/10 | 40.99 / 40.09 / 42.87 / 42.8 / 40.9 | 5 de 5 (`diag_corredor/eval3/eval_d_fijo2715_1001.csv`) |
| D | actuado | 28.24 / 28.6 / 28.81 / 28.46 / 27.77 | 5 de 5 (`diag_corredor/eval3/eval_d_actuado_1001.csv`) |
| D | IPPO actual (s2042) | 35.48 / 36.18 / 34.93 / 32.94 / 37.54 | 5 de 5 (`diag_corredor/eval3/eval_d_ippo_actual_1001.csv`) |
| D | V2 (s42) | 35.02 / 40.3 / 41.9 / 40.97 / 41.14 | 5 de 5 (`diag_corredor/eval3/eval_d_ippo_v2_1001.csv`) |

Las 5 semillas representan bien a las 30 de la evaluación. Retraso total medio con 1001-1005 y, entre paréntesis,
con 1001-1030 (mismos CSV):
- O: fijo 54.36 (57.50), actuado 150.41 (151.43), IPPO actual 74.09 (76.43), V2 73.87 (76.83).
- D: fijo 41.53 (42.54), actuado 28.38 (28.75), IPPO actual 35.41 (34.61), V2 39.87 (39.59).

## Resultados

### Retraso total por periodo (s/veh; `bloqueo_periodos.csv`, `bloqueo_control.csv`)

| control | hora O | hora D | P1 O | P2 O | P1 D | P2 D | P2 O − P2 D | E_C2 en P2: espera para entrar O / D |
|---|---|---|---|---|---|---|---|---|
| fijo 25/10 | 54.36 | 41.53 | 38.4 | 70.3 | 38.4 | 44.7 | +25.7 | 17.8 / 0.5 |
| actuado | 150.41 | 28.38 | 28.6 | 272.2 | 28.6 | 28.1 | +244.1 | 391.0 / 0.5 |
| IPPO actual (s2042) | 74.09 | 35.41 | 29.3 | 118.9 | 29.3 | 41.5 | +77.3 | 89.7 / 0.5 |
| V2 (s42) | 73.87 | 39.87 | 32.3 | 115.5 | 32.3 | 47.5 | +68.0 | 92.7 / 0.5 |

### (i)-(iii) Verde con la cabeza detenida girando a la izquierda, P2 de O (s por corrida; `bloqueo.csv`)

| acceso (giro que espera, flujo opuesto) | control | verde | cabeza izq. detenida (i) | % del verde (ii) | con detenidos detrás | episodios (de 45 que giran) | s por episodio | opuesto en marcha / cruza (fracción de esos s) | descarga (iii), veh/s de verde | descarga con cola | descarga con cola en D |
|---|---|---|---|---|---|---|---|---|---|---|---|
| W_C1 (W->N1, opuesto C2_C1 recto 990) | fijo 25/10 | 1096 | 418.6 | 38 % | 336.2 | 39.6 | 10.6 | 0.99 / 0.50 | 0.21 | 0.19 | 0.31 |
| W_C1 | actuado | 1086 | 271.2 | 25 % | 229.0 | 20.4 | 13.3 | 0.94 / 0.42 | 0.22 | 0.19 | 0.27 |
| W_C1 | IPPO actual | 1084 | 276.0 | 25 % | 203.2 | 29.8 | 9.3 | 0.98 / 0.47 | 0.22 | 0.21 | 0.31 |
| W_C1 | V2 | 1070 | 151.6 | 14 % | 89.0 | 26.6 | 5.7 | 0.99 / 0.48 | 0.22 | 0.25 | 0.32 |
| C2_C1 (E->S1, opuesto W->E 375) | fijo 25/10 | 1096 | 47.0 | 4 % | 43.0 | 5.0 | 9.4 | 0.93 / 0.32 | 0.44 | 0.44 | 0.47 |
| C2_C1 | actuado | 1086 | 403.0 | 37 % | 397.4 | 20.0 | 20.1 | 0.92 / 0.36 | 0.26 | 0.26 | 0.44 |
| C2_C1 | IPPO actual | 1084 | 136.6 | 13 % | 133.4 | 18.2 | 7.5 | 0.93 / 0.32 | 0.38 | 0.38 | 0.46 |
| C2_C1 | V2 | 1070 | 123.6 | 12 % | 121.6 | 18.0 | 6.9 | 0.97 / 0.30 | 0.38 | 0.38 | 0.46 |
| N1_C1 (N1->E, opuesto S1->N1 270) | fijo 25/10 | 440 | 1.4 | 0 % | 1.4 | 0.6 | 2.3 | 1.00 / 0.25 | 0.39 | 0.40 | 0.39 |
| N1_C1 | actuado | 600 | 100.6 | 17 % | 60.4 | 24.2 | 4.2 | 1.00 / 0.37 | 0.29 | 0.30 | 0.37 |
| N1_C1 | IPPO actual | 447 | 6.0 | 1 % | 5.4 | 1.2 | 5.0 | 1.00 / 0.34 | 0.38 | 0.38 | 0.44 |
| N1_C1 | V2 | 456 | 3.6 | 1 % | 3.0 | 0.8 | 4.5 | 1.00 / 0.27 | 0.39 | 0.38 | 0.41 |
| S2_C2 (S2->W, opuesto N2->S2 270) | fijo 25/10 | 440 | 2.8 | 1 % | 1.4 | 1.4 | 2.0 | 1.00 / 0.16 | 0.39 | 0.40 | 0.41 |
| S2_C2 | actuado | 616 | 158.8 | 26 % | 138.8 | 26.4 | 6.0 | 0.99 / 0.35 | 0.25 | 0.24 | 0.38 |
| S2_C2 | IPPO actual | 674 | 122.0 | 18 % | 87.6 | 23.2 | 5.3 | 0.98 / 0.28 | 0.26 | 0.26 | 0.37 |
| S2_C2 | V2 | 491 | 23.6 | 5 % | 15.8 | 6.4 | 3.7 | 0.99 / 0.27 | 0.36 | 0.38 | 0.42 |

- En las 40 corridas hay 10806 s de verde con un vehículo detenido dentro del cruce esperando para girar a la
  izquierda. En esos segundos cruzaron la línea **0** vehículos de los otros movimientos del mismo acceso.
- En P1 de O y en D (todos los accesos y controles) hay **0** s de verde con la cabeza detenida girando a la izquierda.
- En los demás accesos y en el P1 la clasificación completa por segundo está en `bloqueo.csv`.

### Reparto del verde y servicio de E_C2 en P2 (s por corrida; `bloqueo.csv`)

| control | E_C2 verde O / D | E_C2 cruces en verde O / D (demanda: 495) | E_C2 veh/s de verde O / D | C2 transversal verde O / D | C1 transversal verde O / D |
|---|---|---|---|---|---|
| fijo 25/10 | 1096 / 1096 | 453.0 / 475.8 | 0.413 / 0.434 | 440 / 440 | 440 / 440 |
| actuado | 1069 / 1139 | 271.0 / 488.6 | 0.254 / 0.429 | 616 / 451 | 600 / 437 |
| IPPO actual (s2042) | 928 / 1113 | 386.2 / 474.6 | 0.416 / 0.427 | 674 / 456 | 447 / 449 |
| V2 (s42) | 1014 / 1061 | 382.2 / 465.4 | 0.377 / 0.439 | 491 / 461 | 456 / 457 |

### (iv) Verdes transversales del P2 y cabeza bloqueada (`bloqueo_verdes.csv`, `bloqueo_decisiones.csv`)

"det." es la media de detenidos en el acceso con giro en el instante de decisión. Las decisiones son las de
rl_ippo, a los 10, 15, 20... s de verde.

| control | cruce (acceso con giro) | verdes por corrida | duración media O (s) | con cabeza izq. detenida: n, media | sin: n, media | duración media en D | IPPO: termina el verde en la decisión, cabeza detenida / no (n; det.) |
|---|---|---|---|---|---|---|---|
| IPPO actual | C1 (N1_C1) | 44.6 | 10 | 1.2, 10 | 43.4, 10 | 10 | 1.000 (1; 5.0) / 1.000 (222; 0.3); D: 1.000 (224; 0.1) |
| IPPO actual | C2 (S2_C2) | 33.2 | **20.4** | 20.4, **23.8** | 12.8, 15.0 | 11.8 | **0.099** (111; 1.8) / 0.388 (400; 0.4); D: **0.738** (263; 0.1) |
| V2 | C1 (N1_C1) | 45.6 | 10 | 0.8, 10 | 44.8, 10 | 10 | 1.000 (2; 1.5) / 1.000 (226; 0.2); D: 1.000 (229; 0.2) |
| V2 | C2 (S2_C2) | 49.2 | 10 | 6.2, 10 | 43.0, 10 | 10 | 1.000 (18; 2.1) / 1.000 (228; 0.2); D: 1.000 (231; 0.1) |
| actuado | C1 (N1_C1) | 19.0 | 31.5 | 17.2, 33.6 | 1.8, 12.3 | 13.2 | |
| actuado | C2 (S2_C2) | 19.0 | 32.4 | 18.0, 33.4 | 1.0, 14.0 | 12.8 | |
| fijo 25/10 | C1 / C2 | 44.0 | 10 | 0.6 / 1.4, 10 | 43.4 / 42.6, 10 | 10 | |

Verde de avenida de C1 en P2, con los segundos por verde en que la cabeza de C2_C1 está detenida girando a la izquierda:

| control | O | D |
|---|---|---|
| fijo | 25 s (1.1 s) | 25 s |
| actuado | 57 s (21.1 s) | 35.3 s |
| IPPO actual | 24.3 s (3.1 s) | 24.0 s |
| V2 | 23.5 s (2.7 s) | 23.4 s |

IPPO actual en C2, P2 (`bloqueo_decisiones.csv`, columna `condicion`):
- Termina el verde en el 32.5 % de las 511 decisiones de O y en el 73.8 % de las 263 de D.
- La tasa casi no cambia con la cola del enlace de salida C2_C1: 0.319, 0.325 y 0.400 con 0-4, 5-9 y 10 o más
  detenidos. No es una reacción al derrame.
- Sí cambia con los detenidos en las transversales: 0.433 sin detenidos y 0.119 con alguno, frente a 0.754 y
  0.641 en D.

### (v) Derrame (`bloqueo_derrame.csv`)

| control | C2_C1 en P2: cola hasta C2 (s) | último detenido (s) | E_C2 en verde con cola hasta C2 (s) | E_C2 en verde con cabeza detenida por derrame (s) | E_C2 veh/s de verde con / sin cola hasta C2 | E_C2: esperan entrar, media / máx. | D: cola hasta C2 / E_C2 bloqueada (s) | C1_C2 en P1: cola hasta C1, O / D (s) |
|---|---|---|---|---|---|---|---|---|
| fijo 25/10 | 78.4 | 12.0 | 50.6 | 25.8 | 0.13 / 0.43 | 3.9 / 14.4 | 1.4 / 0.0 | 0.4 / 0.4 |
| actuado | 594.4 | 325.8 | 412.4 | 355.4 | 0.04 / 0.39 | 68.4 / 187.2 | 0.0 / 0.0 | 0.0 / 0.0 |
| IPPO actual | 261.6 | 16.2 | 79.0 | 16.0 | 0.15 / 0.44 | 19.1 / 71.8 | 62.2 / 0.2 | 0.0 / 0.0 |
| V2 | 262.2 | 19.8 | 136.8 | 28.4 | 0.17 / 0.41 | 20.1 / 69.8 | 58.4 / 0.0 | 0.0 / 0.0 |

**Asociaciones entre las 15 corridas de O** (fijo, IPPO actual y V2; P2; ρ de Spearman, salida de `tablas`):
- Segundos con la cabeza de C2_C1 detenida girando:
  - frente al retraso total del P2: 0.92 (p = 1.4e-06);
  - frente a la cola de C2_C1 hasta C2: 0.79 (p = 0.0005).
- Cola de C2_C1 hasta C2 frente a los que esperan entrar en E_C2: 0.64 (p = 0.011).
- Cabeza de S2_C2 detenida girando frente al retraso del P2: 0.59 (p = 0.021).
- Cabeza de W_C1 detenida girando frente al retraso del P2: −0.44 (p = 0.10).

Con el actuado (20 corridas) son 0.96, 0.90, 0.84, 0.77 y −0.22.

En el fijo, la peor semilla (1002, 86.63 s/veh) es la que tuvo más tiempo la cabeza de C2_C1 detenida girando:
158 s, frente a 2-46 s en las otras cuatro. Su cola llegó a C2 durante 307 s, frente a 0-70 s
(filas por semilla de `bloqueo.csv` y `bloqueo_derrame.csv`).

## Conclusiones

1. **MEDIDO. Un giro a la izquierda que espera detiene todo su acceso.**
   - En SUMO, el que gira a la izquierda espera el hueco dentro del cruce. Mientras está detenido ahí, no
     cruza ningún vehículo de los otros movimientos de su acceso: 0 en 10806 s de verde, en 40 corridas
     (`bloqueo.csv`).
   - Mientras espera, el acceso opuesto está en marcha en el 92-100 % de esos segundos y cruza la línea en el
     16-50 %. Es espera de hueco en un flujo con prioridad.
   - Esto pasa solo donde hay giros a la izquierda: 0 s en P1 y en D.

2. **MEDIDO. Los giros a la izquierda le cuestan muy distinto a cada control.**
   - Retraso total del P2, O menos D (mismo periodo y volúmenes, cambia solo el sentido de los cuatro giros):
     fijo +25.7, V2 +68.0, IPPO actual +77.3 y actuado +244.1 s/veh (`bloqueo_periodos.csv`).
   - Sin esos giros (D), IPPO actual le gana al fijo en la hora: 35.41 frente a 41.53 s/veh; con 30 semillas,
     34.61 frente a 42.54 (`eval3/eval_d_*_1001.csv`).
   - Con ellos (O), pierde: 74.09 frente a 54.36; con 30 semillas, 76.43 frente a 57.50.
   - En P1, que no tiene giros a la izquierda y es igual en O y en D, IPPO gana: 29.3 frente a 38.4 s/veh.

3. **MEDIDO. El bloqueo que más pesa es el giro E->S1 en C1, en el sentido de la punta.**
   - Con la cabeza de C2_C1 detenida girando (cede el paso a W->E, 375 veh/h), la punta E->W queda retenida en C1.
   - Fracción del verde de avenida de C1 bloqueada así: fijo 4 %, IPPO actual 13 %, V2 12 %, actuado 37 %.
   - Descarga de C2_C1 con cola: 0.44, 0.38, 0.38 y 0.26 veh/s; en D, 0.44-0.47.
   - Entre corridas, esos segundos siguen al retraso del P2 con ρ = 0.92, y a la cola de C2_C1 que llega a C2 con
     ρ = 0.79.
   - El giro W->N1 bloquea más segundos (14-38 % del verde de W_C1), pero no se asocia con el retraso
     (ρ = −0.44, p = 0.10).

4. **MEDIDO. IPPO actual alarga la transversal de C2 mientras la cabeza de S2_C2 espera para girar (S2->W).**
   - Sus verdes transversales de C2 en P2 duran 20.4 s de media, frente a 11.8 s en D y 10 s del fijo.
   - Los verdes con la cabeza bloqueada duran 23.8 s (20.4 por corrida); los que no, 15.0 s (12.8 por corrida).
   - En las decisiones, termina el verde en el 9.9 % de las 111 con la cabeza bloqueada, en el 38.8 % de las
     400 sin ella y en el 73.8 % de las 263 de D.
   - En C1 no lo hace: el 100 % de sus verdes transversales duran 10 s.

5. **MEDIDO; la cuenta del reparto es aritmética sobre lo medido. El costo de IPPO actual sale sobre todo del
   verde que le quita a E_C2.**
   - En P2, la transversal de C2 recibe 674 s de verde, frente a 456 s en D (+218 s), y E_C2 recibe 928 s,
     frente a 1113 s (−185 s).
   - E_C2 descarga casi igual por segundo de verde (0.416 frente a 0.427 veh/s), así que cruza 386 de sus 495
     vehículos del P2, frente a 475 en D.
   - De ese déficit de 88 vehículos, unos 79 salen del verde que falta (185 s × 0.427).
   - E_C2 tiene 19.1 vehículos esperando para entrar de media (máx. 71.8; fijo 3.9 y 14.4; D 0.15 y 1). Los
     vehículos del P2 que entran por E_C2 esperan 89.7 s (D 0.5 s, fijo 17.8 s).

6. **MEDIDO. V2 pierde lo mismo que IPPO actual, pero por el derrame desde C1.**
   - No alarga ninguna transversal: termina el verde en el 100 % de sus decisiones, con o sin bloqueo.
   - La cola de C2_C1 llega a C2 durante 262 s por corrida (fijo 78 s; D 58 s).
   - E_C2 pasa 136.8 s de su verde con esa cola en la entrada. En esos segundos descarga 0.17 veh/s, y 0.41 en
     el resto.
   - En la hora, E_C2 descarga 0.377 veh/s frente a 0.439 en D y cruza 382 vehículos frente a 465.
   - De ese déficit de 83 vehículos, unos 63 salen de la descarga más lenta y 21 del verde que falta (−48 s).

7. **MEDIDO; INFERIDO en el porqué. El actuado colapsa por el mismo mecanismo, amplificado.**
   - Mientras hay bloqueo, sus verdes llegan al máximo.
   - El verde de avenida de C1 dura 57 s, frente a 35.3 s en D, y en 21.1 s de cada uno la cabeza de C2_C1 está
     detenida girando. Las transversales duran 31.5 y 32.4 s, frente a 13.2 y 12.8 s en D.
   - La cola de C2_C1 llega a C2 durante 594 s por corrida, y la cabeza de E_C2 queda detenida por derrame en
     355 s de su verde.
   - E_C2 descarga 0.254 veh/s y los vehículos del P2 que entran por E_C2 esperan 391 s.
   - INFERIDO: el actuado no corta el verde porque la cola detenida queda sobre su detector, así que nunca ve un
     hueco.

8. **MEDIDO; INFERIDO en la propagación. El fijo es el menos afectado.**
   - Su bloqueo está sobre todo en W_C1 (38 % del verde). En los accesos que alimentan o retienen la punta es
     de 1-4 %, y sus transversales quedan en 10 s.
   - W_C1 no está saturado en P2: en los cuatro controles cruza unos 235 vehículos en verde, frente a una
     demanda de 233. INFERIDO: por eso ese bloqueo no se propaga.
   - No está medido por qué el giro E->S1 se bloquea tres veces menos con el fijo que con IPPO o V2. El
     volumen opuesto servido es el mismo en todos. Una hipótesis sin probar es el momento en que llega el
     pelotón E->W a C1 respecto de la descarga de W_C1: desfases 0/0 en el fijo, progresión en IPPO.

9. **MEDIDO. El P1 no tiene derrame ni bloqueo por giros.**
   - La cola de C1_C2 llega a C1 durante 0.4 s por corrida como máximo, en todos los controles y escenarios.
   - Advertencia: el P2 de D no es una copia exacta del P1 para el fijo, IPPO y V2 (44.7 frente a 38.4,
     41.5 frente a 29.3 y 47.5 frente a 32.3 s/veh). Para el actuado sí lo es (28.1 frente a 28.6).
   - Por eso el efecto de los giros se mide como P2 de O menos P2 de D, no como P2 menos P1. Esa asimetría
     residual no se explica aquí.

10. **INFERIDO. Respuesta a "¿por qué 2715?" desde esta medición.**
    - La desventaja de IPPO en 2715 aparece con los giros a la izquierda permitidos del P2, en accesos de un
      carril. Sin ellos, IPPO gana.
    - Los controles que responden a las colas convierten esos bloqueos en verde mal usado: IPPO alarga una
      transversal bloqueada y el actuado alarga todo.
    - Además, todos los adaptativos sufren más el bloqueo E->S1 en C1, que retiene la punta y la derrama hasta
      la entrada E_C2. Esa espera para entrar no entra en el timeLoss.
    - No se midió aquí por qué no pasa en 905-1810 veh/h. Una posibilidad es que, con flujos opuestos más
      ligeros, el hueco aparece antes. Queda como hipótesis.

## Límites

- Son 5 semillas por caso, sin intervalos de confianza. Las cifras describen el mecanismo; los veredictos siguen
  siendo los de 30 semillas.
- La cabeza y el bloqueo se clasifican con umbrales fijos: detenido por debajo de 0.1 m/s, plaza de 7.5 m y
  cola a menos de 2 m/s. La cola hasta el cruce cambia con el umbral: la versión estricta da 12, 326, 16 y 20 s
  frente a 78, 594, 262 y 262 s. En cambio, el bloqueo de E_C2 por derrame (cabeza detenida en verde) no depende
  de la velocidad.
- La política observa colas y vehículos en movimiento, no si la cabeza gira. Que IPPO alargue el verde por el
  bloqueo es una asociación (conclusión 4). Además, sin detenidos en las transversales IPPO también corta menos
  en O que en D: 0.433 frente a 0.754 (`bloqueo_decisiones.csv`). Responde también a otras entradas que aquí no
  se identifican.

## Archivos y cómo reproducir

- `bloqueo.py`: acciones `correr`, `analizar` y `tablas`. Desde `plan2/`:
  - `python diag_corredor/bloqueo.py correr --datos <carpeta> --procesos 4`: 40 corridas, unos 4 min.
  - `python diag_corredor/bloqueo.py analizar --datos <carpeta>`.
  - `python diag_corredor/bloqueo.py tablas`.
- CSV de esta carpeta:
  - `bloqueo.csv`: por escenario, control, periodo, acceso y semilla, más la media.
  - `bloqueo_verdes.csv` y `bloqueo_decisiones.csv`.
  - `bloqueo_derrame.csv`, `bloqueo_periodos.csv` y `bloqueo_control.csv`.
- Datos por segundo (`seg_*.csv.gz`), métricas (`met_*.json`) y tripinfo de las 40 corridas, 73 MB:
  `C:/Users/GAMER/AppData/Local/Temp/claude/c--Users-GAMER-Documents-demo-rl-semaforo/de7717ed-cbad-4afb-8e8f-03cbdcefb7fa/scratchpad/bloqueo/datos/`.
  Es una carpeta temporal de la sesión: si hace falta conservarla, hay que copiarla.
