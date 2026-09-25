# Veredicto del plan de pruebas v2

Generado por veredicto.py a partir de plan2/. No editar a mano. Regla: ESPEC seccion 7.
Delta de retraso en % (negativo = mejor); delta de recompensa en % (positivo = mejor).

## Matriz caso x modelo

| Caso | Escenario | Actuado | Q-learning | SARSA | Q-learning (colas) | DQN | IPPO local | IPPO vecinos | IPPO spill | MAPPO |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | EMPATA | FALLA | FALLA | FALLA | MEJORA | EMPATA | FUNCIONA | FUNCIONA | FUNCIONA |
| P2 | corredor_alta | FUNCIONA | MEJORA | FALLA | PENDIENTE | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA |
| P3 | red | MEJORA | FALLA | FALLA | FALLA | MEJORA | FALLA | FUNCIONA | = vecinos | PENDIENTE |
| P4 | red_alta | EMPATA | PENDIENTE | FALLA | FALLA | MEJORA | FALLA | MEJORA | = vecinos | PENDIENTE |
| P5 | malla3 | FALLA | FALLA | FALLA | PENDIENTE | PENDIENTE | FALLA | EMPATA | = vecinos | EMPATA |

## Actuado (actuado)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | - | 21.07 +- 0.15 | -1.1 % [-2.1, 0.1] p=0.0571 | - | - | - | EMPATA |
| P2 | corredor_alta | 2 | 1 | 3620 | - | 124.14 +- 2.48 | -19.8 % [-21.3, -18.2] p=1.86e-09 | - | - | - | FUNCIONA |
| P3 | red | 3 + rotonda | 2 | 2150 | - | 21.48 +- 0.12 | -1.1 % [-1.7, -0.5] p=0.00306 | - | - | - | MEJORA |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | - | 30.04 +- 0.90 | -0.1 % [-1.4, 1.4] p=0.869 | - | - | - | EMPATA |
| P5 | malla3 | 9 | 2 | 4350 | - | 25.37 +- 0.10 | +21.8 % [21.3, 22.3] p=1.73e-06 | - | - | - | FALLA |

## Q-learning (ql)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 42 | 23.26 +- 0.15 | +9.2 % [7.8, 10.5] p=1.92e-06 | +10.4 % [9.4, 11.3] p=1.73e-06 | -11.6 % [-13.0, -10.0] p=1.86e-09 | si (1/3) | FALLA |
| P2 | corredor_alta | 2 | 1 | 3620 | 4042 | 141.14 +- 1.80 | -8.8 % [-9.9, -7.5] p=3.73e-09 | +13.7 % [11.5, 15.9] p=1.86e-09 | +6.5 % [5.0, 7.8] p=1.64e-07 | si (1/3) | MEJORA |
| P3 | red | 3 + rotonda | 2 | 2150 | 42 | 24.41 +- 0.24 | +12.4 % [11.5, 13.6] p=1.73e-06 | +13.6 % [12.5, 14.9] p=1.73e-06 | -11.9 % [-13.3, -10.9] p=1.86e-09 | si (2/3) | FALLA |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 4042 | 33.03 +- 0.99 | +9.9 % [8.0, 11.9] p=1.86e-09 | +10.0 % [8.3, 11.7] p=1.86e-09 | -11.2 % [-12.1, -10.4] p=1.86e-09 | no (2/3) | PENDIENTE (no convergió; provisional: FALLA) |
| P5 | malla3 | 9 | 2 | 4350 | 4042 | 29.69 +- 0.09 | +42.5 % [42.0, 43.0] p=1.73e-06 | +17.0 % [16.4, 17.6] p=1.73e-06 | -34.1 % [-34.6, -33.6] p=1.86e-09 | si (3/3) | FALLA |

## SARSA (sarsa)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 42 | 24.27 +- 0.30 | +14.0 % [12.1, 15.9] p=1.73e-06 | +15.2 % [13.7, 16.8] p=1.73e-06 | -14.6 % [-16.7, -12.6] p=1.86e-09 | si (3/3) | FALLA |
| P2 | corredor_alta | 2 | 1 | 3620 | 42 | 164.91 +- 4.41 | +6.6 % [3.7, 9.4] p=0.000209 | +32.9 % [29.1, 36.6] p=1.86e-09 | -12.4 % [-15.8, -8.9] p=4.71e-07 | si (1/3) | FALLA |
| P3 | red | 3 + rotonda | 2 | 2150 | 2042 | 24.15 +- 0.11 | +11.2 % [10.6, 11.8] p=1.73e-06 | +12.4 % [11.6, 13.2] p=1.73e-06 | -10.6 % [-11.2, -9.9] p=1.86e-09 | si (3/3) | FALLA |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 42 | 33.19 +- 1.02 | +10.4 % [8.5, 12.4] p=3.73e-09 | +10.5 % [8.6, 12.5] p=1.86e-09 | -12.1 % [-13.3, -11.1] p=1.86e-09 | si (2/3) | FALLA |
| P5 | malla3 | 9 | 2 | 4350 | 42 | 29.18 +- 0.09 | +40.0 % [39.5, 40.6] p=1.73e-06 | +15.0 % [14.5, 15.5] p=1.73e-06 | -31.2 % [-31.7, -30.7] p=1.86e-09 | si (3/3) | FALLA |

## Q-learning (colas) (ql_colas)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 4042 | 23.56 +- 0.33 | +10.6 % [8.9, 12.4] p=1.73e-06 | +11.8 % [10.3, 13.4] p=1.73e-06 | -10.8 % [-13.1, -8.6] p=9.31e-09 | si (1/3) | FALLA |
| P2 | corredor_alta | 2 | 1 | 3620 | 4042 | 165.25 +- 5.02 | +6.8 % [3.8, 9.8] p=0.000313 | +33.1 % [28.4, 37.8] p=1.86e-09 | +4.2 % [-1.5, 10.2] p=0.309 | no (0/3) | PENDIENTE (no convergió; provisional: FALLA) |
| P3 | red | 3 + rotonda | 2 | 2150 | 42 | 23.81 +- 0.14 | +9.6 % [8.9, 10.4] p=1.73e-06 | +10.8 % [10.0, 11.7] p=1.73e-06 | +3.0 % [2.0, 3.9] p=5.14e-06 | si (3/3) | FALLA |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 2042 | 33.00 +- 0.91 | +9.8 % [8.4, 11.3] p=1.86e-09 | +9.9 % [8.2, 11.5] p=3.73e-09 | +6.4 % [5.3, 7.5] p=5.59e-09 | si (3/3) | FALLA |
| P5 | malla3 | 9 | 2 | 4350 | - | - | - | - | - | - | PENDIENTE (sin datos) |

## DQN (dqn)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 4042 | 20.56 +- 0.16 | -3.5 % [-4.8, -2.2] p=2.35e-06 | -2.4 % [-3.3, -1.6] p=1.22e-05 | +3.0 % [1.7, 4.5] p=4.41e-05 | si (3/3) | MEJORA |
| P2 | corredor_alta | 2 | 1 | 3620 | 4042 | 124.66 +- 1.10 | -19.4 % [-20.3, -18.5] p=1.86e-09 | +0.4 % [-1.7, 2.5] p=0.44 | +17.4 % [16.4, 18.4] p=1.86e-09 | si (3/3) | FUNCIONA |
| P3 | red | 3 + rotonda | 2 | 2150 | 4042 | 21.32 +- 0.10 | -1.8 % [-2.4, -1.3] p=1.36e-05 | -0.7 % [-1.3, -0.2] p=0.00545 | +3.8 % [3.2, 4.3] p=1.86e-09 | si (3/3) | MEJORA |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 4042 | 29.04 +- 1.02 | -3.4 % [-4.7, -2.1] p=4.41e-05 | -3.3 % [-5.0, -1.5] p=0.00233 | +8.7 % [8.3, 9.1] p=1.86e-09 | si (2/3) | MEJORA |
| P5 | malla3 | 9 | 2 | 4350 | 4042 | 23.15 +- 0.09 | +11.1 % [10.7, 11.4] p=1.73e-06 | -8.8 % [-9.2, -8.4] p=1.73e-06 | -7.8 % [-8.0, -7.5] p=1.86e-09 | no (2/3) | PENDIENTE (no convergió; provisional: FALLA) |

## IPPO local (ippo_local)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 2042 | 21.19 +- 0.14 | -0.5 % [-1.7, 0.5] p=0.711 | +0.5 % [-0.4, 1.4] p=0.106 | -0.3 % [-1.4, 0.9] p=0.309 | si (3/3) | EMPATA |
| P2 | corredor_alta | 2 | 1 | 3620 | 42 | 119.43 +- 0.80 | -22.8 % [-23.3, -22.2] p=1.86e-09 | -3.8 % [-5.8, -1.9] p=0.000872 | +19.6 % [18.9, 20.2] p=1.86e-09 | si (2/3) | FUNCIONA |
| P3 | red | 3 + rotonda | 2 | 2150 | 2042 | 22.21 +- 0.16 | +2.3 % [1.5, 3.0] p=4.07e-05 | +3.4 % [2.8, 4.0] p=2.35e-06 | -1.1 % [-1.9, -0.2] p=0.0427 | si (3/3) | FALLA |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 2042 | 30.91 +- 1.02 | +2.9 % [1.4, 4.4] p=0.00124 | +2.9 % [1.2, 4.7] p=0.00538 | -1.4 % [-2.7, -0.2] p=0.0384 | si (3/3) | FALLA |
| P5 | malla3 | 9 | 2 | 4350 | 4042 | 26.23 +- 0.23 | +25.9 % [24.8, 27.0] p=1.73e-06 | +3.4 % [2.5, 4.3] p=6.34e-06 | -15.7 % [-16.8, -14.7] p=1.86e-09 | si (2/3) | FALLA |

## IPPO vecinos (ippo_vecinos)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 4042 | 19.84 +- 0.17 | -6.8 % [-8.0, -5.8] p=1.86e-09 | -5.8 % [-6.7, -4.9] p=1.92e-06 | +7.0 % [5.9, 8.3] p=1.86e-09 | si (3/3) | FUNCIONA |
| P2 | corredor_alta | 2 | 1 | 3620 | 2042 | 118.66 +- 0.67 | -23.3 % [-23.9, -22.7] p=1.86e-09 | -4.4 % [-6.3, -2.6] p=0.000137 | +19.9 % [19.1, 20.7] p=1.86e-09 | si (2/3) | FUNCIONA |
| P3 | red | 3 + rotonda | 2 | 2150 | 4042 | 19.81 +- 0.11 | -8.8 % [-9.3, -8.2] p=1.73e-06 | -7.8 % [-8.4, -7.2] p=1.73e-06 | +15.6 % [15.2, 16.0] p=1.86e-09 | si (3/3) | FUNCIONA |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 42 | 28.97 +- 0.92 | -3.6 % [-5.0, -2.3] p=3.45e-05 | -3.6 % [-4.8, -2.4] p=2.6e-05 | +9.2 % [8.5, 9.9] p=1.86e-09 | si (3/3) | MEJORA |
| P5 | malla3 | 9 | 2 | 4350 | 2042 | 21.21 +- 0.35 | +1.8 % [0.4, 3.4] p=0.523 | -16.4 % [-17.6, -15.0] p=1.73e-06 | +7.3 % [5.3, 9.0] p=4.71e-07 | si (3/3) | EMPATA |

## IPPO spill (ippo_spill)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 2042 | 20.19 +- 0.15 | -5.2 % [-6.2, -4.2] p=2.56e-06 | -4.2 % [-5.0, -3.4] p=2.35e-06 | +5.3 % [4.2, 6.3] p=1.86e-09 | si (3/3) | FUNCIONA |
| P2 | corredor_alta | 2 | 1 | 3620 | 4042 | 119.62 +- 1.23 | -22.7 % [-23.4, -21.9] p=1.86e-09 | -3.6 % [-5.8, -1.5] p=0.00501 | +17.0 % [16.0, 17.9] p=1.86e-09 | si (2/3) | FUNCIONA |
| P3 | red | 3 + rotonda | 2 | 2150 | 4042 | 19.81 +- 0.11 | -8.8 % [-9.3, -8.2] p=1.73e-06 | -7.8 % [-8.4, -7.2] p=1.73e-06 | +15.6 % [15.2, 16.0] p=1.86e-09 | si (3/3) | = vecinos (término de spill inactivo; FUNCIONA) |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 42 | 28.97 +- 0.92 | -3.6 % [-5.0, -2.3] p=3.45e-05 | -3.6 % [-4.8, -2.4] p=2.6e-05 | +9.2 % [8.5, 9.9] p=1.86e-09 | si (3/3) | = vecinos (término de spill inactivo; MEJORA) |
| P5 | malla3 | 9 | 2 | 4350 | 2042 | 21.21 +- 0.35 | +1.8 % [0.4, 3.4] p=0.523 | -16.4 % [-17.6, -15.0] p=1.73e-06 | +7.3 % [5.3, 9.0] p=4.71e-07 | si (3/3) | = vecinos (término de spill inactivo; EMPATA) |

## MAPPO (mappo)

| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | corredor | 2 | 1 | 1810 | 42 | 19.79 +- 0.18 | -7.1 % [-8.4, -5.8] p=3.73e-09 | -6.1 % [-7.0, -5.2] p=1.86e-09 | +7.2 % [5.8, 8.6] p=5.59e-09 | si (3/3) | FUNCIONA |
| P2 | corredor_alta | 2 | 1 | 3620 | 42 | 121.24 +- 1.34 | -21.6 % [-22.6, -20.7] p=1.86e-09 | -2.3 % [-4.5, -0.1] p=0.0687 | +17.7 % [16.5, 18.8] p=1.86e-09 | si (3/3) | FUNCIONA |
| P3 | red | 3 + rotonda | 2 | 2150 | 4042 | 20.01 +- 0.21 | -7.8 % [-8.8, -6.8] p=1.92e-06 | -6.8 % [-7.7, -5.8] p=2.85e-06 | +14.1 % [12.5, 15.4] p=1.86e-09 | no (2/3) | PENDIENTE (no convergió; provisional: FUNCIONA) |
| P4 | red_alta | 3 + rotonda | 2 | 2580 | 2042 | 29.45 +- 0.88 | -2.0 % [-3.1, -0.9] p=0.00225 | -2.0 % [-3.3, -0.6] p=0.0293 | +5.5 % [4.7, 6.3] p=3.73e-09 | no (1/3) | PENDIENTE (no convergió; provisional: MEJORA) |
| P5 | malla3 | 9 | 2 | 4350 | 2042 | 20.78 +- 0.05 | -0.3 % [-0.6, 0.0] p=0.0896 | -18.1 % [-18.4, -17.8] p=1.73e-06 | +9.8 % [9.6, 10.1] p=1.86e-09 | si (2/3) | EMPATA |
