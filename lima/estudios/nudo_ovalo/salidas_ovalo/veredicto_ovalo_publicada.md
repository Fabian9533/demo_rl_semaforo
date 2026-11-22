# Nudo en la red del Ovalo Vasco: veredicto del modelo de orden libre

## Demanda publicada

- Modelo de orden libre (citado): version citada base 42 (validacion mediana; val_elegido {42: 80.767, 2042: 79.321, 4042: 82.249}); entrenamiento estabilizado: tendencia -2.47 %, estabilidad 1.91 %.
- Modelo de orden fijo: version citada base 2042 (validacion mediana; val_elegido {42: 76.169, 2042: 76.602, 4042: 76.627}); entrenamiento SIN ESTABILIZAR (provisional): tendencia -5.13 %, estabilidad 0.00 %.

### Tanda 1 (100 semillas)

| Frente a | Retraso total de la referencia (s/veh) | Del modelo de orden libre (s/veh) | Cambio (%) | IC95 | p |
|---|---|---|---|---|---|
| Fijo ajustado al segundo | 84.11 | 81.23 | -3.43 | [-4.56, -2.38] | 5.66e-08 |
| Actuado ajustado | 76.39 | 81.23 | +6.33 | [+5.45, +7.22] | 4.09e-17 |
| Modelo de orden fijo | 76.40 | 81.23 | +6.32 | [+5.41, +7.22] | 1.17e-16 |
| Plan actual | 99.46 | 81.23 | -18.33 | [-20.56, -16.22] | 3.9e-18 |
| Actuado por defecto | 870.79 | 81.23 | -90.67 | [-90.80, -90.55] | 3.9e-18 |
| Ciclo minimo | 1367.42 | 81.23 | -94.06 | [-94.14, -93.98] | 3.9e-18 |

Vehiculos sin terminar o sin entrar a los 6000 s (media por semilla; semillas con alguno; su retraso cuenta hasta el corte): actual 0.0 (0); fijo 0.0 (0); actuadoaj 0.0 (0); actuado 359.1 (100); minimo 516.3 (100); libre_s42 0.0 (0); completo_s2042 0.0 (0)

(1) Veredicto del nudo (frente al fijo ajustado, sin perder contra el actuado ajustado): **MEJORA**
(2) Frente al modelo de orden fijo (la misma regla, con el de orden fijo en el lugar del fijo): **FALLA**
(3) El modelo de orden fijo frente al fijo ajustado, sin perder contra el actuado ajustado: **FUNCIONA** (-9.17 % frente al fijo, +0.01 % frente al actuado ajustado, -23.18 % frente al plan actual)
Los tres entrenamientos de Modelo de orden libre (citado): 42 81.23, 2042 79.36, 4042 82.93 s/veh; media por semilla de los tres 81.17; rango 3.57
Los tres entrenamientos de Modelo de orden fijo: 42 75.67, 2042 76.40, 4042 76.91 s/veh; media por semilla de los tres 76.33; rango 1.24
Media de los tres libres menos media de los tres de orden fijo: +4.84 s/veh (los libres con mas retraso); rango mayor entre entrenamientos: 3.57 s/veh

### Tanda 2 (100 semillas)

| Frente a | Retraso total de la referencia (s/veh) | Del modelo de orden libre (s/veh) | Cambio (%) | IC95 | p |
|---|---|---|---|---|---|
| Fijo ajustado al segundo | 84.46 | 81.38 | -3.64 | [-4.64, -2.65] | 2.74e-10 |
| Actuado ajustado | 76.49 | 81.38 | +6.40 | [+5.46, +7.37] | 2.21e-17 |
| Modelo de orden fijo | 76.56 | 81.38 | +6.31 | [+5.41, +7.19] | 1.06e-16 |
| Plan actual | 100.64 | 81.38 | -19.14 | [-21.05, -17.26] | 3.9e-18 |
| Actuado por defecto | 866.11 | 81.38 | -90.60 | [-90.72, -90.49] | 3.9e-18 |
| Ciclo minimo | 1356.03 | 81.38 | -94.00 | [-94.07, -93.92] | 3.9e-18 |

Vehiculos sin terminar o sin entrar a los 6000 s (media por semilla; semillas con alguno; su retraso cuenta hasta el corte): actual 0.0 (0); fijo 0.0 (0); actuadoaj 0.0 (0); actuado 352.4 (100); minimo 501.1 (100); libre_s42 0.0 (0); completo_s2042 0.0 (0)

(1) Veredicto del nudo (frente al fijo ajustado, sin perder contra el actuado ajustado): **MEJORA**
(2) Frente al modelo de orden fijo (la misma regla, con el de orden fijo en el lugar del fijo): **FALLA**
(3) El modelo de orden fijo frente al fijo ajustado, sin perder contra el actuado ajustado: **FUNCIONA** (-9.36 % frente al fijo, +0.09 % frente al actuado ajustado, -23.93 % frente al plan actual)
Los tres entrenamientos de Modelo de orden libre (citado): 42 81.38, 2042 79.25, 4042 83.77 s/veh; media por semilla de los tres 81.47; rango 4.52
Los tres entrenamientos de Modelo de orden fijo: 42 75.94, 2042 76.56, 4042 77.17 s/veh; media por semilla de los tres 76.55; rango 1.23
Media de los tres libres menos media de los tres de orden fijo: +4.91 s/veh (los libres con mas retraso); rango mayor entre entrenamientos: 4.52 s/veh

Veredicto citable del nudo, demanda publicada: **MEJORA**
Orden libre frente a orden fijo, demanda publicada: **FALLA** (provisional: algun entrenamiento citado sin estabilizar); frente a la variacion entre entrenamientos: se distingue de la variacion entre entrenamientos
Modelo de orden fijo frente al fijo ajustado, demanda publicada: **FUNCIONA** (provisional)

## Prueba de robustez del reparto (demanda publicada, sin reajustar ni reentrenar; no interviene en el veredicto)

- reducto: modelo de orden libre 72.05 s/veh; Plan actual 91.85 (-21.56 % [-23.24, -19.87], p = 3.9e-18); Fijo ajustado al segundo 97.21 (-25.88 % [-27.81, -23.97], p = 3.9e-18); Actuado ajustado 69.28 (+4.00 % [+3.06, +4.98], p = 2.17e-11); Modelo de orden fijo 68.06 (+5.86 % [+5.00, +6.73], p = 1.9e-16)
- transversal: modelo de orden libre 102.82 s/veh; Plan actual 263.24 (-60.94 % [-61.93, -59.92], p = 3.9e-18); Fijo ajustado al segundo 158.79 (-35.25 % [-37.07, -33.40], p = 3.9e-18); Actuado ajustado 90.73 (+13.32 % [+11.67, +15.06], p = 5.77e-18); Modelo de orden fijo 91.13 (+12.83 % [+11.12, +14.64], p = 4.14e-18)

## Codigo

Huellas sha256 de los programas; las del resto del codigo y de los datos, en huellas.sha256. Las politicas se entrenaron con este codigo (sha256_codigo de su meta).

- `demo_rl/rl_ippo.py` c61b706c7a96baa07ca9737564a5124c50bea7da911e5c77805dd62b784e4bc7
- `demo_rl/lima/estudio.py` 5f08daaa8c1005962b70ef10d2fabe28a924f76cdb9790c4b54aa8c70b67bbf4
- `demo_rl/lima/programa_ovalo.py` 5d5f03cca511b296762be38e930150a5bd2975c1ee88579a65985b02dd2d34c2
- `demo_rl/lima/ovalo/plan_ovalo.py` 0829e80c105cc1bd46f71bef4d84ccd55f89de9356449006039b48378e31c940
- `entrenar.sh` a9a95791138ded3ba283199c382a5fdf16bd422cffb7c3251961e8c7ec8d311e
- `referencias.sh` 474472c8a4ee8c7fa88f7dbfb343e9b9f5448c60ffacb80e28be3da651ac8f79
- `evaluar_ovalo.py` 4621671b9d0a38df20baac5c1da31d104d79f164aa46c11e9caf07489aebc836
- `comprobar_fases.py` 6e10f4c157622ced5058e48fcf424bf641b5b6b917c2319ac88a6fa2cd8ea20e
