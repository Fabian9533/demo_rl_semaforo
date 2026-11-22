# Nudo en la red del Ovalo Vasco: veredicto del modelo de orden libre

## Demanda alta

- Modelo de orden libre (citado): version citada base 2042 (validacion mediana; val_elegido {42: 185.951, 2042: 189.221, 4042: 202.954}); entrenamiento SIN ESTABILIZAR (provisional): tendencia +7.07 %, estabilidad 1.54 %.
- Modelo de orden fijo: version citada base 4042 (validacion mediana; val_elegido {42: 128.734, 2042: 126.641, 4042: 128.048}); entrenamiento estabilizado: tendencia +2.20 %, estabilidad 3.69 %.

### Tanda 1 (100 semillas)

| Frente a | Retraso total de la referencia (s/veh) | Del modelo de orden libre (s/veh) | Cambio (%) | IC95 | p |
|---|---|---|---|---|---|
| Fijo ajustado al segundo | 133.50 | 206.94 | +55.02 | [+51.81, +58.18] | 3.9e-18 |
| Actuado ajustado | 143.22 | 206.94 | +44.49 | [+41.65, +47.33] | 3.9e-18 |
| Modelo de orden fijo | 136.77 | 206.94 | +51.31 | [+48.68, +54.05] | 3.9e-18 |
| Plan actual | 270.88 | 206.94 | -23.60 | [-25.17, -22.11] | 3.9e-18 |

Vehiculos sin terminar o sin entrar a los 6000 s (media por semilla; semillas con alguno; su retraso cuenta hasta el corte): actual 0.0 (0); fijo 0.0 (0); actuadoaj 0.0 (0); libre_s2042 0.0 (0); completo_s4042 0.0 (0)

(1) Veredicto del nudo (frente al fijo ajustado, sin perder contra el actuado ajustado): **FALLA**
(2) Frente al modelo de orden fijo (la misma regla, con el de orden fijo en el lugar del fijo): **FALLA**
(3) El modelo de orden fijo frente al fijo ajustado, sin perder contra el actuado ajustado: **FALLA** (+2.45 % frente al fijo, -4.50 % frente al actuado ajustado, -49.51 % frente al plan actual)
Los tres entrenamientos de Modelo de orden libre (citado): sin evaluar
Los tres entrenamientos de Modelo de orden fijo: sin evaluar

### Tanda 2 (100 semillas)

| Frente a | Retraso total de la referencia (s/veh) | Del modelo de orden libre (s/veh) | Cambio (%) | IC95 | p |
|---|---|---|---|---|---|
| Fijo ajustado al segundo | 127.53 | 197.82 | +55.11 | [+52.17, +57.98] | 3.9e-18 |
| Actuado ajustado | 142.70 | 197.82 | +38.62 | [+33.63, +43.16] | 1.43e-16 |
| Modelo de orden fijo | 131.64 | 197.82 | +50.27 | [+47.63, +52.91] | 3.9e-18 |
| Plan actual | 265.50 | 197.82 | -25.49 | [-26.80, -24.10] | 3.9e-18 |
| Actuado por defecto | 1150.53 | 197.82 | -82.81 | [-83.19, -82.42] | 3.9e-18 |
| Ciclo minimo | 1747.77 | 197.82 | -88.68 | [-88.94, -88.42] | 3.9e-18 |

Vehiculos sin terminar o sin entrar a los 6000 s (media por semilla; semillas con alguno; su retraso cuenta hasta el corte): actual 0.0 (0); fijo 0.0 (0); actuadoaj 0.0 (0); actuado 759.1 (100); minimo 1208.8 (100); libre_s2042 0.0 (0); completo_s4042 0.0 (0)

(1) Veredicto del nudo (frente al fijo ajustado, sin perder contra el actuado ajustado): **FALLA**
(2) Frente al modelo de orden fijo (la misma regla, con el de orden fijo en el lugar del fijo): **FALLA**
(3) El modelo de orden fijo frente al fijo ajustado, sin perder contra el actuado ajustado: **FALLA** (+3.22 % frente al fijo, -7.75 % frente al actuado ajustado, -50.42 % frente al plan actual)
Los tres entrenamientos de Modelo de orden libre (citado): sin evaluar
Los tres entrenamientos de Modelo de orden fijo: sin evaluar

Veredicto citable del nudo, demanda alta: **FALLA** (provisional: entrenamiento citado sin estabilizar)
Orden libre frente a orden fijo, demanda alta: **FALLA** (provisional: algun entrenamiento citado sin estabilizar); frente a la variacion entre entrenamientos: no se puede decir (faltan entrenamientos sin evaluar)
Modelo de orden fijo frente al fijo ajustado, demanda alta: **FALLA**

Limite, demanda alta: el fijo ajustado [60, 25, 77] da verdes de mas de 60 s, que el actuado ajustado y los modelos no pueden dar (su verde maximo es 60 s)
Limite, demanda alta: el actuado ajustado (por retraso, alcance 100 m, retraso minimo 5 s, maximos 60) queda otra vez en el borde (['minTimeLoss']); no se sigue: se dice como limite

## Prueba de robustez del reparto (demanda publicada, sin reajustar ni reentrenar; no interviene en el veredicto)

- reducto: sin evaluar
- transversal: sin evaluar

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
