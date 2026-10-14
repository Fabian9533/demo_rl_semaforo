# Veredicto del plan de pruebas v2

Generado por veredicto.py a partir de plan2/. No editar a mano. Regla: ESPEC seccion 7.
Metrica primaria: retraso_total_prom (retraso total (timeLoss más la espera para entrar a la red)). * = la politica da lo mismo que el control trivial.
Delta de retraso en % (negativo = mejor); delta de recompensa en % (positivo = mejor).

## Matriz caso x modelo

| Caso | Escenario | Actuado | Trivial | Q-learning | SARSA | Q-learning (colas) | DQN | IPPO local | IPPO vecinos | IPPO spill | MAPPO |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | EMPATA | FALLA | FALLA | FALLA | FALLA | MEJORA | EMPATA | FUNCIONA | FUNCIONA | FUNCIONA |
| P2 | corredor_alta | FALLA | FALLA | FALLA | FALLA | PENDIENTE | FALLA | MEJORA | FALLA | FALLA | FALLA |
| P3 | red | FALLA | MEJORA | FALLA | FALLA | FALLA | FALLA | FALLA | MEJORA* | = vecinos | PENDIENTE |
| P4 | red_alta | FALLA | EMPATA | PENDIENTE | FALLA | FALLA | FALLA | FALLA | FALLA | = vecinos | PENDIENTE |
| P5 | malla3 | FALLA | EMPATA | FALLA | FALLA | PENDIENTE | PENDIENTE | FALLA | FALLA | = vecinos | EMPATA* |

## Actuado (actuado)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | - | 21.45 +- 0.15 | -1.0 % [-2.1, 0.1] p=0.0549 | - | - | - | EMPATA |
| P2 | corredor_alta | 2 | 1 | 3620 | - | 445.46 +- 4.53 | +13.0 % [11.6, 14.3] p=1.86e-09 | - | - | - | FALLA |
| P3 | red | 3 + rotonda | 2 | 2150 | - | 21.84 +- 0.12 | +7.8 % [7.0, 8.6] p=1.73e-06 | - | - | - | FALLA |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | - | 30.37 +- 0.90 | +6.3 % [4.2, 8.5] p=5.14e-06 | - | - | - | FALLA |
| P5 | malla3 | 9 | 2 | 4350 | - | 25.84 +- 0.10 | +21.6 % [21.1, 22.1] p=1.73e-06 | - | - | - | FALLA |

## Trivial (trivial)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | - | 106.26 +- 2.08 | +390.3 % [379.8, 400.7] p=1.86e-09 | - | - | - | FALLA |
| P2 | corredor_alta | 2 | 1 | 3620 | - | 1055.41 +- 11.71 | +167.7 % [163.7, 171.6] p=1.86e-09 | - | - | - | FALLA |
| P3 | red | 3 + rotonda | 2 | 2150 | - | 20.17 +- 0.11 | -0.5 % [-0.8, -0.1] p=0.0128 | - | - | - | MEJORA |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | - | 28.29 +- 0.92 | -1.0 % [-2.4, 0.5] p=0.217 | - | - | - | EMPATA |
| P5 | malla3 | 9 | 2 | 4350 | - | 21.25 +- 0.05 | +0.0 % [0.0, 0.0] p=1 | - | - | - | EMPATA |

## Q-learning (ql)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 42 | 23.64 +- 0.15 | +9.1 % [7.7, 10.3] p=3.73e-09 | +10.2 % [9.3, 11.1] p=1.73e-06 | -11.6 % [-13.0, -10.0] p=1.86e-09 | si (1/3) | FALLA |
| P2 | corredor_alta | 2 | 1 | 3620 | 4042 | 498.53 +- 11.50 | +26.4 % [23.8, 29.6] p=1.86e-09 | +11.9 % [9.6, 14.9] p=1.86e-09 | +6.5 % [5.0, 7.8] p=1.64e-07 | si (1/3) | FALLA |
| P3 | red | 3 + rotonda | 2 | 2150 | 42 | 24.76 +- 0.24 | +22.2 % [21.3, 23.4] p=1.73e-06 | +13.4 % [12.3, 14.7] p=1.73e-06 | -31.7 % [-33.2, -30.6] p=1.86e-09 | si (2/3) | FALLA |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 4042 | 33.36 +- 0.99 | +16.8 % [15.0, 18.6] p=1.86e-09 | +9.8 % [8.2, 11.6] p=1.73e-06 | -32.5 % [-33.6, -31.6] p=1.86e-09 | no (2/3) | PENDIENTE (no convergió; provisional: FALLA) |
| P5 | malla3 | 9 | 2 | 4350 | 4042 | 30.16 +- 0.09 | +41.9 % [41.5, 42.5] p=1.73e-06 | +16.7 % [16.1, 17.3] p=1.73e-06 | -48.8 % [-49.4, -48.2] p=1.86e-09 | si (3/3) | FALLA |

## SARSA (sarsa)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 42 | 24.64 +- 0.30 | +13.7 % [11.9, 15.6] p=1.73e-06 | +14.9 % [13.4, 16.4] p=1.86e-09 | -14.6 % [-16.7, -12.6] p=1.86e-09 | si (3/3) | FALLA |
| P2 | corredor_alta | 2 | 1 | 3620 | 42 | 474.14 +- 6.95 | +20.3 % [18.4, 22.0] p=1.86e-09 | +6.4 % [4.8, 8.1] p=1.3e-07 | -12.4 % [-15.8, -8.9] p=4.71e-07 | si (1/3) | FALLA |
| P3 | red | 3 + rotonda | 2 | 2150 | 2042 | 24.51 +- 0.11 | +21.0 % [20.4, 21.4] p=1.73e-06 | +12.2 % [11.4, 13.0] p=1.73e-06 | -30.1 % [-30.8, -29.6] p=1.86e-09 | si (3/3) | FALLA |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 42 | 33.52 +- 1.02 | +17.4 % [15.1, 19.8] p=1.73e-06 | +10.4 % [8.5, 12.3] p=1.86e-09 | -33.6 % [-35.3, -32.2] p=1.86e-09 | si (2/3) | FALLA |
| P5 | malla3 | 9 | 2 | 4350 | 42 | 29.65 +- 0.09 | +39.5 % [39.0, 40.1] p=1.73e-06 | +14.8 % [14.3, 15.2] p=1.73e-06 | -45.5 % [-46.1, -45.0] p=1.86e-09 | si (3/3) | FALLA |

## Q-learning (colas) (ql_colas)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 4042 | 23.93 +- 0.33 | +10.4 % [8.7, 12.2] p=1.73e-06 | +11.6 % [10.1, 13.2] p=1.73e-06 | -10.8 % [-13.1, -8.6] p=9.31e-09 | si (1/3) | FALLA |
| P2 | corredor_alta | 2 | 1 | 3620 | 4042 | 559.94 +- 9.00 | +42.0 % [39.6, 44.4] p=1.86e-09 | +25.7 % [23.4, 27.9] p=1.86e-09 | +4.2 % [-1.5, 10.2] p=0.309 | no (0/3) | PENDIENTE (no convergió; provisional: FALLA) |
| P3 | red | 3 + rotonda | 2 | 2150 | 42 | 24.16 +- 0.14 | +19.3 % [18.6, 19.9] p=1.86e-09 | +10.7 % [9.8, 11.5] p=1.73e-06 | -68.4 % [-70.0, -66.9] p=1.86e-09 | si (3/3) | FALLA |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 2042 | 33.34 +- 0.91 | +16.7 % [14.8, 18.8] p=1.73e-06 | +9.8 % [8.1, 11.4] p=3.73e-09 | -73.7 % [-75.7, -71.7] p=1.86e-09 | si (3/3) | FALLA |
| P5 | malla3 | 9 | 2 | 4350 | - | - | - | - | - | - | PENDIENTE (sin datos) |

## DQN (dqn)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 4042 | 20.94 +- 0.16 | -3.4 % [-4.8, -2.2] p=2.15e-05 | -2.4 % [-3.2, -1.5] p=6.31e-05 | +3.0 % [1.7, 4.5] p=4.41e-05 | si (3/3) | MEJORA |
| P2 | corredor_alta | 2 | 1 | 3620 | 4042 | 461.12 +- 5.70 | +17.0 % [15.4, 18.5] p=1.73e-06 | +3.5 % [1.9, 5.2] p=0.000418 | +17.4 % [16.4, 18.4] p=1.86e-09 | si (3/3) | FALLA |
| P3 | red | 3 + rotonda | 2 | 2150 | 4042 | 21.68 +- 0.10 | +7.0 % [6.4, 7.6] p=1.73e-06 | -0.7 % [-1.3, -0.2] p=0.00515 | -13.3 % [-13.9, -12.6] p=1.86e-09 | si (3/3) | FALLA |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 4042 | 29.37 +- 1.02 | +2.8 % [1.1, 4.6] p=0.0019 | -3.3 % [-5.0, -1.5] p=0.00158 | -8.8 % [-9.5, -8.1] p=1.86e-09 | si (2/3) | FALLA |
| P5 | malla3 | 9 | 2 | 4350 | 4042 | 23.62 +- 0.09 | +11.2 % [10.7, 11.6] p=1.73e-06 | -8.6 % [-9.0, -8.2] p=1.73e-06 | -19.5 % [-20.0, -19.1] p=1.86e-09 | no (2/3) | PENDIENTE (no convergió; provisional: FALLA) |

## IPPO local (ippo_local)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 2042 | 21.56 +- 0.14 | -0.5 % [-1.6, 0.5] p=0.688 | +0.5 % [-0.4, 1.4] p=0.109 | -0.3 % [-1.4, 0.9] p=0.309 | si (3/3) | EMPATA |
| P2 | corredor_alta | 2 | 1 | 3620 | 42 | 387.46 +- 3.69 | -1.7 % [-2.6, -0.9] p=0.00123 | -13.0 % [-14.2, -11.8] p=1.86e-09 | +19.6 % [18.9, 20.2] p=1.86e-09 | si (2/3) | MEJORA |
| P3 | red | 3 + rotonda | 2 | 2150 | 2042 | 22.57 +- 0.16 | +11.4 % [10.6, 12.2] p=1.73e-06 | +3.4 % [2.8, 3.9] p=2.35e-06 | -18.9 % [-19.9, -17.9] p=1.86e-09 | si (3/3) | FALLA |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 2042 | 31.25 +- 1.02 | +9.4 % [7.8, 11.0] p=1.73e-06 | +2.9 % [1.2, 4.6] p=0.00538 | -20.9 % [-22.7, -19.2] p=1.86e-09 | si (3/3) | FALLA |
| P5 | malla3 | 9 | 2 | 4350 | 4042 | 26.70 +- 0.23 | +25.6 % [24.6, 26.7] p=1.73e-06 | +3.3 % [2.4, 4.3] p=6.34e-06 | -28.4 % [-29.6, -27.3] p=1.86e-09 | si (2/3) | FALLA |

## IPPO vecinos (ippo_vecinos)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 4042 | 20.22 +- 0.17 | -6.7 % [-7.8, -5.7] p=1.86e-09 | -5.7 % [-6.6, -4.8] p=1.92e-06 | +7.0 % [5.9, 8.3] p=1.86e-09 | si (3/3) | FUNCIONA |
| P2 | corredor_alta | 2 | 1 | 3620 | 2042 | 400.68 +- 3.64 | +1.6 % [0.6, 2.6] p=0.00219 | -10.1 % [-11.2, -8.8] p=1.86e-09 | +19.9 % [19.1, 20.7] p=1.86e-09 | si (2/3) | FALLA |
| P3 | red | 3 + rotonda | 2 | 2150 | 4042 | 20.17 +- 0.11 | -0.5 % [-0.8, -0.1] p=0.0128 | -7.6 % [-8.2, -7.0] p=1.73e-06 | +0.6 % [0.3, 0.9] p=0.000313 | si (3/3) | MEJORA (= trivial) |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 42 | 29.30 +- 0.92 | +2.6 % [0.8, 4.4] p=0.00984 | -3.5 % [-4.7, -2.3] p=2.76e-06 | -8.2 % [-9.0, -7.4] p=1.86e-09 | si (3/3) | FALLA |
| P5 | malla3 | 9 | 2 | 4350 | 2042 | 21.68 +- 0.35 | +2.0 % [0.7, 3.6] p=0.0277 | -16.1 % [-17.3, -14.7] p=1.73e-06 | -2.8 % [-5.0, -0.9] p=0.0252 | si (3/3) | FALLA |

## IPPO spill (ippo_spill)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 2042 | 20.57 +- 0.15 | -5.1 % [-6.1, -4.2] p=2.56e-06 | -4.1 % [-4.9, -3.3] p=9.31e-09 | +5.3 % [4.2, 6.3] p=1.86e-09 | si (3/3) | FUNCIONA |
| P2 | corredor_alta | 2 | 1 | 3620 | 4042 | 421.45 +- 4.40 | +6.9 % [5.8, 8.0] p=1.86e-09 | -5.4 % [-6.6, -4.1] p=4.28e-06 | +17.0 % [16.0, 17.9] p=1.86e-09 | si (2/3) | FALLA |
| P3 | red | 3 + rotonda | 2 | 2150 | 4042 | 20.17 +- 0.11 | -0.5 % [-0.8, -0.1] p=0.0128 | -7.6 % [-8.2, -7.0] p=1.73e-06 | +0.6 % [0.3, 0.9] p=0.000313 | si (3/3) | = vecinos (término de spill inactivo; MEJORA*) |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 42 | 29.30 +- 0.92 | +2.6 % [0.8, 4.4] p=0.00984 | -3.5 % [-4.7, -2.3] p=2.76e-06 | -8.2 % [-9.0, -7.4] p=1.86e-09 | si (3/3) | = vecinos (término de spill inactivo; FALLA) |
| P5 | malla3 | 9 | 2 | 4350 | 2042 | 21.68 +- 0.35 | +2.0 % [0.7, 3.6] p=0.0277 | -16.1 % [-17.3, -14.7] p=1.73e-06 | -2.8 % [-5.0, -0.9] p=0.0252 | si (3/3) | = vecinos (término de spill inactivo; FALLA) |

## MAPPO (mappo)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 42 | 20.16 +- 0.18 | -7.0 % [-8.3, -5.7] p=1.92e-06 | -6.0 % [-6.9, -5.1] p=1.73e-06 | +7.2 % [5.8, 8.6] p=5.59e-09 | si (3/3) | FUNCIONA |
| P2 | corredor_alta | 2 | 1 | 3620 | 42 | 402.56 +- 5.01 | +2.1 % [0.7, 3.6] p=0.00501 | -9.6 % [-11.0, -8.1] p=1.86e-09 | +17.7 % [16.5, 18.8] p=1.86e-09 | si (3/3) | FALLA |
| P3 | red | 3 + rotonda | 2 | 2150 | 4042 | 20.37 +- 0.21 | +0.5 % [-0.3, 1.6] p=0.544 | -6.7 % [-7.6, -5.7] p=3.79e-06 | -1.1 % [-2.9, 0.3] p=0.191 | no (2/3) | PENDIENTE (no convergió; provisional: EMPATA) |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 2042 | 29.78 +- 0.88 | +4.3 % [2.5, 6.1] p=0.000241 | -1.9 % [-3.3, -0.6] p=0.031 | -12.6 % [-13.6, -11.7] p=1.86e-09 | no (1/3) | PENDIENTE (no convergió; provisional: FALLA) |
| P5 | malla3 | 9 | 2 | 4350 | 2042 | 21.25 +- 0.05 | +0.0 % [0.0, 0.0] p=1 | -17.8 % [-18.1, -17.4] p=1.73e-06 | -0.0 % [-0.0, 0.0] p=0.47 | si (2/3) | EMPATA (= trivial) |
