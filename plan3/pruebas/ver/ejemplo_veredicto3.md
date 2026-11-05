# Veredicto del bloque nuevo (plan 3) — EJEMPLO CON DATOS SINTÉTICOS (veredicto3.py --probar), no son resultados

Generado por `veredicto3.py` con las reglas de `PRERREGISTRO.md` (§7-§12). No editar a mano.

## Respuesta corta

- Número único, llegadas regulares (P1-P6, con P6): frente al plan fijo ajustado al segundo, -4.0 % [-4.0, -3.9] en la tanda 1 y -2.1 % [-2.3, -2.0] en la tanda 2 (frente al plan fijo entregado: -5.8 % [-5.9, -5.8] y -4.0 % [-4.2, -3.9]). IPPO con mensajes corregido: -3.6 % [-3.7, -3.6] y -1.7 % [-1.9, -1.6].
- Número único, llegadas aleatorias (P1-P6, con P6): frente al plan fijo ajustado al segundo, -6.0 % [-6.1, -6.0] en la tanda 1 y -6.0 % [-6.1, -6.0] en la tanda 2 (frente al plan fijo entregado: -7.8 % [-7.9, -7.8] y -7.9 % [-7.9, -7.8]). Cifra provisional en P3.
- Casos con etiqueta citable MEJORA o FUNCIONA: 22 de 32 (P1 (regulares), P2 (regulares), P6 (regulares), P6e (regulares), r1810 (regulares), r2715 (regulares), r3620 (regulares), m1810 (regulares), m2715 (regulares), m3620 (regulares), m6525 (regulares), P1 (aleatorias), P2 (aleatorias), P4 (aleatorias), P5 (aleatorias), P6 (aleatorias), mix1 (mix_corredor) (aleatorias), mix1 (mixa_corredor) (aleatorias), mix3 (mix_red) (aleatorias), mix3 (mixa_red) (aleatorias), per1 (aleatorias), per3 (aleatorias))
- Hipótesis que pasan (con su regla global o, si se juzgan caso por caso, en al menos un caso): H2, H7r, H7, H8a, H8c, H12, H14 regulares, H14 aleatorias, H15 regulares, H9 regulares, H9 aleatorias, H10 corredor, H3, H5, H6.

## Cómo leer

- Etiqueta: la regla de lo entregado frente al fijo fino (FUNCIONA: mejora de 5 % o más, significativa y sin perder contra el actuado ajustado; MEJORA: mejora significativa; FALLA: empeora; EMPATA: el resto).
- Citable: la que se repite en las dos tandas de semillas. "Se repite": cuántos entrenamientos van del lado de la etiqueta.
- Cambio: retraso total por vehículo frente al fijo fino, con su IC95; † = un extremo del IC a menos de 0.05 puntos del 0.

## Tabla del anexo: etiqueta por caso

| Caso | Llegadas | Modelo citado | Tanda 1 | Tanda 2 | Citable | Cambio T1 [IC95] | Cambio T2 [IC95] | Se repite (T1; T2) | Con la mejor base |
|---|---|---|---|---|---|---|---|---|---|
| P1 | regulares | observación nueva | FUNCIONA | FUNCIONA | FUNCIONA | -9.9 % [-10.1, -9.8] | -10.2 % [-10.3, -10.0] | 3 de 3; 3 de 3 | FUNCIONA |
| P2 | regulares | IPPO con mensajes corregido | FUNCIONA | MEJORA | MEJORA | -8.2 % [-8.3, -8.1] | -2.9 % [-3.0, -2.8] | 5 de 5; 5 de 5 | MEJORA |
| P3 | regulares | IPPO con mensajes corregido | MEJORA | EMPATA | EMPATA (mejora no confirmada) | -3.0 % [-3.1, -2.9] | -0.0 % [-0.6, 0.5] | 5 de 5; 3 de 5 | EMPATA (mejora no confirmada) |
| P4 | regulares | IPPO con mensajes corregido | FALLA | EMPATA | EMPATA (falla no confirmada) | +3.9 % [3.7, 4.0] | -0.0 % [-0.7, 0.7] | 5 de 5; 2 de 5 | EMPATA (falla no confirmada) |
| P5 | regulares | IPPO con mensajes corregido | MEJORA | FALLA | CONTRADICTORIO (no se concluye) | -3.0 % [-3.1, -2.9] | +4.0 % [3.8, 4.2] | 5 de 5; 5 de 5 | CONTRADICTORIO (no se concluye) |
| P6 | regulares | IPPO con mensajes corregido | MEJORA | MEJORA | MEJORA | -3.1 % [-3.2, -3.0] | -3.0 % [-3.1, -2.9] | 4 de 5; 4 de 5 | MEJORA |
| P6e | regulares | IPPO con mensajes corregido | MEJORA | MEJORA | MEJORA | -3.0 % [-3.2, -2.9] | -3.2 % [-3.3, -3.1] | 3 de 5; 3 de 5 | MEJORA |
| D | regulares | PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE | — | — | —; — | MEJORA |
| c905 | regulares | IPPO con mensajes corregido | EMPATA | EMPATA | EMPATA | -0.0 % [-0.7, 0.6] | -0.0 % [-0.6, 0.5] | 2 de 3; 1 de 3 | EMPATA |
| c1358 | regulares | IPPO con mensajes corregido | FALLA | FALLA | FALLA | +3.9 % [3.8, 4.1] | +4.0 % [3.9, 4.1] | 3 de 3; 3 de 3 | FALLA |
| c2715 | regulares | IPPO con mensajes corregido | PENDIENTE (MEJORA) | PENDIENTE (MEJORA) | PENDIENTE (MEJORA) | -3.0 % [-3.2, -2.8] | -3.0 % [-3.1, -2.9] | 5 de 5; 5 de 5 | MEJORA |
| r905 | regulares | IPPO con mensajes corregido | PENDIENTE | PENDIENTE | PENDIENTE | — | — | —; — | PENDIENTE |
| r1358 | regulares | IPPO con mensajes corregido | PENDIENTE | PENDIENTE | PENDIENTE | -3.1 % [-3.2, -3.0] | -2.9 % [-3.0, -2.8] | 3 de 3; 3 de 3 | PENDIENTE |
| r1810 | regulares | IPPO con mensajes corregido | MEJORA | MEJORA | MEJORA | -3.0 % [-3.2, -2.9] | -3.0 % [-3.1, -2.8] | 3 de 3; 3 de 3 | MEJORA |
| r2715 | regulares | IPPO con mensajes corregido | MEJORA | MEJORA | MEJORA | -3.1 % [-3.2, -3.0] | -3.0 % [-3.1, -2.8] | 3 de 3; 3 de 3 | MEJORA |
| r3620 | regulares | IPPO con mensajes corregido | MEJORA | MEJORA | MEJORA | -3.0 % [-3.1, -2.9] | -3.1 % [-3.1, -3.0] | 3 de 3; 3 de 3 | MEJORA |
| m1810 | regulares | IPPO con mensajes corregido | MEJORA | MEJORA | MEJORA | -3.1 % [-3.2, -3.0] | -3.0 % [-3.2, -2.9] | 3 de 3; 3 de 3 | MEJORA |
| m2715 | regulares | IPPO con mensajes corregido | MEJORA | MEJORA | MEJORA | -3.0 % [-3.2, -2.9] | -3.0 % [-3.2, -2.9] | 3 de 3; 3 de 3 | MEJORA |
| m3620 | regulares | IPPO con mensajes corregido | MEJORA | MEJORA | MEJORA | -3.0 % [-3.1, -2.8] | -2.9 % [-3.0, -2.8] | 3 de 3; 3 de 3 | MEJORA |
| m6525 | regulares | IPPO con mensajes corregido | MEJORA | MEJORA | MEJORA | -3.0 % [-3.2, -2.9] | -3.0 % [-3.1, -2.8] | 3 de 3; 3 de 3 | MEJORA |
| P1 | aleatorias | IPPO con mensajes corregido (entrenado con llegadas aleatorias) | FUNCIONA | FUNCIONA | FUNCIONA | -6.1 % [-6.2, -6.0] | -6.0 % [-6.1, -5.8] | 5 de 5; 5 de 5 | FUNCIONA |
| P2 | aleatorias | IPPO con mensajes corregido (entrenado con llegadas aleatorias) | FUNCIONA | FUNCIONA | FUNCIONA | -6.0 % [-6.1, -5.9] | -6.1 % [-6.2, -6.0] | 5 de 5; 5 de 5 | FUNCIONA |
| P3 | aleatorias | IPPO con mensajes corregido (entrenado con llegadas aleatorias) | PENDIENTE (FUNCIONA) | PENDIENTE (FUNCIONA) | PENDIENTE (FUNCIONA) | -5.9 % [-6.1, -5.8] | -5.9 % [-6.0, -5.8] | 5 de 5; 5 de 5 | FUNCIONA |
| P4 | aleatorias | IPPO con mensajes corregido (entrenado con llegadas aleatorias) | FUNCIONA | FUNCIONA | FUNCIONA | -6.0 % [-6.1, -5.8] | -6.0 % [-6.2, -5.9] | 3 de 5; 3 de 5 | FUNCIONA |
| P5 | aleatorias | IPPO con mensajes corregido (entrenado con llegadas aleatorias) | FUNCIONA | FUNCIONA | FUNCIONA | -6.1 % [-6.2, -6.0] | -6.1 % [-6.2, -5.9] | 5 de 5; 5 de 5 | FUNCIONA |
| P6 | aleatorias | IPPO con mensajes corregido (entrenado con llegadas aleatorias) | FUNCIONA | FUNCIONA | FUNCIONA | -6.1 % [-6.2, -6.0] | -6.1 % [-6.2, -5.9] | 5 de 5; 5 de 5 | FUNCIONA |
| mix1 (mix_corredor) | aleatorias | IPPO con mensajes corregido (entrenado con la mezcla) | FUNCIONA | FUNCIONA | FUNCIONA | -6.0 % [-6.1, -5.9] | -6.0 % [-6.1, -5.8] | 3 de 3; 3 de 3 | FUNCIONA |
| mix1 (mixa_corredor) | aleatorias | IPPO con mensajes corregido (entrenado con la mezcla) | FUNCIONA | FUNCIONA | FUNCIONA | -6.0 % [-6.1, -5.8] | -6.0 % [-6.2, -5.8] | 3 de 3; 3 de 3 | FUNCIONA |
| mix3 (mix_red) | aleatorias | IPPO con mensajes corregido (entrenado con la mezcla) | FUNCIONA | FUNCIONA | FUNCIONA | -5.9 % [-6.0, -5.8] | -6.0 % [-6.2, -5.8] | 3 de 3; 3 de 3 | FUNCIONA |
| mix3 (mixa_red) | aleatorias | IPPO con mensajes corregido (entrenado con la mezcla) | FUNCIONA | FUNCIONA | FUNCIONA | -5.9 % [-6.0, -5.8] | -6.0 % [-6.2, -5.8] | 3 de 3; 3 de 3 | FUNCIONA |
| per1 | aleatorias | IPPO con mensajes corregido (entrenado con el perfil) | FUNCIONA | FUNCIONA | FUNCIONA | -6.1 % [-6.2, -6.0] | -6.0 % [-6.2, -5.9] | 3 de 3; 3 de 3 | FUNCIONA |
| per3 | aleatorias | IPPO con mensajes corregido (entrenado con el perfil) | FUNCIONA | FUNCIONA | FUNCIONA | -5.8 % [-5.9, -5.7] | -6.0 % [-6.2, -5.8] | 3 de 3; 3 de 3 | FUNCIONA |

## Hipótesis

| Id | Qué se prueba | Resultado |
|---|---|---|
| H1 | V2 no es peor que C0 en ningún caso (P1-P6, 120 semillas) | no pasa: P5 (contradictorio (T1x: no es peor; T2x: es peor)). P5 es peor en T2x (+6.07 % [5.95, 6.20]) |
| H2 | V2 < C0 (120 semillas por tanda) | pasa en 2 de 2 casos: P4, m6525 |
| H7r | con mensajes < sin mensajes, llegadas regulares | pasa en 2 de 3 casos: P1, P2 |
| H7 | con mensajes < sin mensajes, llegadas aleatorias | pasa en 6 de 6 casos: P1, P2, P3, P4, P5, P6 |
| H8a | V2 + observación < V2, llegadas regulares | pasa en 3 de 3 casos: c2715, P2, D |
| H8b | V2 + observación < V2, llegadas aleatorias | no pasa: 0 de 6 casos (ninguno); hace falta 1 |
| H8c | V2 + observación no es peor que V2 | pasa en 3 de 3 casos: P1, P3, P6 |
| H12 | V2 + las tres limpiezas no es peor que V2 | pasa en 1 de 2 casos: P6 |
| H14 regulares | reloj de 2 s < reloj de 5 s | pasa en 4 de 4 casos: D, P1, P2, P6 |
| H14 aleatorias | reloj de 2 s < reloj de 5 s | pasa en 3 de 3 casos: P1, P2, P6 |
| H15 regulares | modelo completo < V2 | pasa en 4 de 4 casos: P1, P2, P4, P6 |
| H15 aleatorias | modelo completo < V2 | pasa en 0 de 6 casos: ninguno |
| H9 regulares | 400 episodios con piso < 200 sin piso | pasa en 5 de 6 casos: P1, P2, P3, P5, P6 |
| H9 aleatorias | 400 episodios con piso < 200 sin piso | pasa en 6 de 6 casos: P1, P2, P3, P4, P5, P6 |
| H10 corredor | una política por red (corredor) no es peor que la V2 de cada nivel | pasa: 'no es peor' en 4 de 5 niveles; hacen falta 4 ('no concluyente' no cuenta) |
| H10 red | una política por red (red) no es peor que la V2 de cada nivel | no pasa: 'no es peor' en 0 de 7 niveles; hacen falta 6 ('no concluyente' no cuenta); no se pudo correr en 7 |
| H10 malla | una política por red (malla) no es peor que la V2 de cada nivel | no pasa: 'no es peor' en 0 de 6 niveles; hacen falta 5 ('no concluyente' no cuenta); no se pudo correr en 6 |
| H3 | V2 MEJORA o FUNCIONA frente al fijo fino en P6 | citable MEJORA; sentido 4 de 5 y 4 de 5 |
| H3e | V2 MEJORA o FUNCIONA frente al fijo fino en P6e | citable MEJORA; sentido 3 de 5 (hacen falta 4) y 3 de 5 (hacen falta 4) (descriptiva) |
| H5 | V2 aleatoria MEJORA o FUNCIONA frente al fijo fino re-ajustado en al menos 3 de 6 | pasa: 4 de 6 casos (P1, P2, P5, P6); hacen falta 3 |
| H6 | la ventaja frente al fijo es mayor con llegadas aleatorias (por caso) | pasa en 3 de 6 casos: P3, P5, P6 |
| H0 | ¿el desorden abre margen? (descriptiva) | en 6 de 6 casos algún control que reacciona da MEJORA o FUNCIONA |

## Lecturas obligadas (§5 y §11)

- P1 (regulares): El modelo citado no es IPPO con mensajes corregido: es observación nueva; la etiqueta de IPPO con mensajes corregido es FUNCIONA. | V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión.
- P2 (regulares): V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión.
- P3 (regulares): V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión.
- P6 (regulares): P6 con la entrada por defecto: el cambio relativo está diluido por la espera de inserción; ver P6e. | V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión.
- P6e (regulares): La versión evaluada mejora; el método no se repite en 3 de 5 entrenamientos (T1).
- c905 (regulares): V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión.
- c1358 (regulares): V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión.
- c2715 (regulares): V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión. | PENDIENTE por no convergencia; probabilidad de que una política estable salga así por ruido: no medido (§6).
- r905 (regulares): V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión.
- r1358 (regulares): V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión.
- r1810 (regulares): V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión.
- r2715 (regulares): V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión.
- r3620 (regulares): V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión.
- m1810 (regulares): V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión.
- m2715 (regulares): V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión.
- m3620 (regulares): Reproduce el ciclo mínimo (no se dice "coordinación aprendida"). | V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige la versión.
- P2 (aleatorias): Deja vehículos sin entrar al cierre (fijo fino en t1a: 3 de 10 semillas, 120 vehículos): su retraso total está subestimado y la diferencia con un brazo que no los deja es conservadora.
- P3 (aleatorias): PENDIENTE por no convergencia; probabilidad de que una política estable salga así por ruido: no medido (§6).
- P4 (aleatorias): La versión evaluada mejora; el método no se repite en 3 de 5 entrenamientos (T1).

## Referencias al lado (etiqueta citable del modelo citado frente a cada una)

| Caso | Llegadas | actuado por defecto | actuado ajustado | fijo por bloques | fijo entregado | fijo ajustado desde 10 s | fijo de verdes de 5 en 5 | fijo por franja | Max-Pressure | regla simple | ciclo mínimo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | regulares | FUNCIONA | FUNCIONA | — | FUNCIONA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA |
| P2 | regulares | FUNCIONA | FUNCIONA | — | MEJORA | — | MEJORA | MEJORA | FUNCIONA | FUNCIONA | FUNCIONA |
| P3 | regulares | MEJORA | MEJORA | — | MEJORA | — | MEJORA | CONTRADICTORIO (no se concluye) | FUNCIONA | FUNCIONA | FUNCIONA |
| P4 | regulares | MEJORA | CONTRADICTORIO (no se concluye) | — | CONTRADICTORIO (no se concluye) | — | CONTRADICTORIO (no se concluye) | EMPATA (falla no confirmada) | FUNCIONA | FUNCIONA | FUNCIONA |
| P5 | regulares | MEJORA | CONTRADICTORIO (no se concluye) | — | CONTRADICTORIO (no se concluye) | — | CONTRADICTORIO (no se concluye) | CONTRADICTORIO (no se concluye) | FUNCIONA | FUNCIONA | FUNCIONA |
| P6 | regulares | FUNCIONA | FUNCIONA | — | MEJORA | — | MEJORA | MEJORA | FUNCIONA | FUNCIONA | FUNCIONA |
| P6e | regulares | FUNCIONA | FUNCIONA | — | MEJORA | — | MEJORA | MEJORA | FUNCIONA | FUNCIONA | FUNCIONA |
| D | regulares | — | — | — | — | — | — | — | — | — | — |
| c905 | regulares | MEJORA | MEJORA | — | MEJORA | EMPATA (mejora no confirmada) | — | — | — | — | FUNCIONA |
| c1358 | regulares | MEJORA | FALLA | — | FALLA | FALLA | — | — | — | — | FUNCIONA |
| c2715 | regulares | FUNCIONA | FUNCIONA | — | MEJORA | MEJORA | — | — | — | — | FUNCIONA |
| r905 | regulares | FUNCIONA | FUNCIONA | — | MEJORA | MEJORA | — | — | — | — | FUNCIONA |
| r1358 | regulares | FUNCIONA | — | — | MEJORA | MEJORA | — | — | — | — | FUNCIONA |
| r1810 | regulares | FUNCIONA | FUNCIONA | — | MEJORA | MEJORA | — | — | — | — | FUNCIONA |
| r2715 | regulares | FUNCIONA | FUNCIONA | — | MEJORA | MEJORA | — | — | — | — | FUNCIONA |
| r3620 | regulares | FUNCIONA | FUNCIONA | — | MEJORA | MEJORA | — | — | — | — | FUNCIONA |
| m1810 | regulares | FUNCIONA | FUNCIONA | — | MEJORA | MEJORA | — | — | — | — | FUNCIONA |
| m2715 | regulares | FUNCIONA | FUNCIONA | — | MEJORA | PENDIENTE | — | — | — | — | FUNCIONA |
| m3620 | regulares | FUNCIONA | FUNCIONA | — | MEJORA | MEJORA | — | — | — | — | EMPATA |
| m6525 | regulares | FUNCIONA | FUNCIONA | — | MEJORA | MEJORA | — | — | — | — | FUNCIONA |
| P1 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA |
| P2 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA |
| P3 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA |
| P4 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA |
| P5 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA |
| P6 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA |
| mix1 (mix_corredor) | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | — | — | — | — | FUNCIONA | FUNCIONA |
| mix1 (mixa_corredor) | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | — | — | — | — | FUNCIONA | FUNCIONA |
| mix3 (mix_red) | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | — | — | — | — | FUNCIONA | FUNCIONA |
| mix3 (mixa_red) | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | — | — | — | — | FUNCIONA | FUNCIONA |
| per1 | aleatorias | FUNCIONA | FUNCIONA | MEJORA | FUNCIONA | — | — | — | FUNCIONA | FUNCIONA | FUNCIONA |
| per3 | aleatorias | FUNCIONA | FUNCIONA | MEJORA | FUNCIONA | — | — | — | FUNCIONA | FUNCIONA | FUNCIONA |

## PENDIENTE

- D (regulares): PENDIENTE (falta la decisión de promoción de dem_corredor_t2715_der).
- c2715 (regulares): PENDIENTE (no convergió; provisional: MEJORA); probabilidad de que una política estable no converja por ruido (§6): no medido.
- r905 (regulares): PENDIENTE (falta fijo fino en t1r).
- r1358 (regulares): PENDIENTE (falta actuado ajustado en t1r).
- P3 (aleatorias): PENDIENTE (no convergió; provisional: FUNCIONA); probabilidad de que una política estable no converja por ruido (§6): no medido.

## Regla de promoción (§12): validación en 15009-15024 frente a V2

- P1 (regulares): observación nueva -3.21 %, reloj de 2 s +0.34 %, modelo completo +0.38 %, 400 episodios +0.39 %; se cita observación nueva (promovido: le gana a V2 por al menos 1 %).
- P2 (regulares): reloj de 2 s +0.21 %, 400 episodios +0.29 %, limpiezas de PPO juntas +0.30 %, modelo completo +0.31 %, observación nueva +0.32 %; se cita IPPO con mensajes corregido.
- P3 (regulares): observación nueva +0.24 %, 400 episodios +0.25 %; se cita IPPO con mensajes corregido.
- P4 (regulares): modelo completo +0.21 %, 400 episodios +0.37 %; se cita IPPO con mensajes corregido.
- P5 (regulares): 400 episodios +0.34 %; se cita IPPO con mensajes corregido.
- P6 (regulares): reloj de 2 s +0.30 %, modelo completo +0.30 %, limpiezas de PPO juntas +0.32 %, observación nueva +0.32 %, 400 episodios +0.34 %; se cita IPPO con mensajes corregido.
- c2715 (regulares): observación nueva +0.21 %; se cita IPPO con mensajes corregido.
- P1 (aleatorias): modelo completo +0.23 %, reloj de 2 s +0.26 %, observación nueva +0.26 %, 400 episodios +0.26 %; se cita IPPO con mensajes corregido (entrenado con llegadas aleatorias).
- P2 (aleatorias): 400 episodios +0.22 %, modelo completo +0.26 %, reloj de 2 s +0.34 %, observación nueva +0.38 %; se cita IPPO con mensajes corregido (entrenado con llegadas aleatorias).
- P3 (aleatorias): modelo completo +0.23 %, observación nueva +0.33 %, 400 episodios +0.36 %; se cita IPPO con mensajes corregido (entrenado con llegadas aleatorias).
- P4 (aleatorias): observación nueva +0.39 %, 400 episodios +0.40 %, modelo completo +0.48 %; se cita IPPO con mensajes corregido (entrenado con llegadas aleatorias).
- P5 (aleatorias): modelo completo +0.28 %, observación nueva +0.30 %, 400 episodios +0.33 %; se cita IPPO con mensajes corregido (entrenado con llegadas aleatorias).
- P6 (aleatorias): reloj de 2 s +0.27 %, observación nueva +0.28 %, 400 episodios +0.33 %, modelo completo +0.34 %; se cita IPPO con mensajes corregido (entrenado con llegadas aleatorias).

## Vehículos sin entrar al cierre (§4)

- P2 (aleatorias, t1a): fijo fino: 3 de 10 semillas, 120 vehículos
- Lectura obligada: el retraso total de esos brazos está subestimado y la diferencia con un brazo que no los deja es conservadora. Detalle por brazo en veredicto3_no_insertados.csv.

## Entrenamientos caídos o sin publicar

- poi_red_alta: IPPO con mensajes corregido (entrenado con llegadas aleatorias), base 14042: caída declarada en cola/caidas.json (e2_v2poi_poi_red_alta_s14042: pérdida NaN (2026-11-15 03:10), e2_v2poi_poi_red_alta_s14042_r2: pérdida NaN (2026-11-16 02:55))
- poi_red_alta: IPPO con mensajes corregido (entrenado con llegadas aleatorias), base 16042: caída declarada en cola/caidas.json (e2_v2poi_poi_red_alta_s16042: pérdida NaN (2026-11-15 03:10), e2_v2poi_poi_red_alta_s16042_r2: pérdida NaN (2026-11-16 02:55))
- Relanzamientos, desvíos y enmiendas: en cola/estado.json y en las enmiendas del prerregistro (§11, §14); veredicto3 no los calcula.

## V2 del diagnóstico del corredor (§6)

- c905: la versión evaluada de la V2 del diagnóstico (Sección 5.5.1) es la base 2042; la de ahora es la base 42 (se muestran las dos).

## Avisos

- 58 CSV de la tanda promo no entran al veredicto (regla de promoción: se leen en promocion.json)
- m2715 (dem_malla3_t2715, t1r): los brazos no generan los mismos vehículos en 1 semilla (la primera, 424304; distinto: ciego/t1r/eval_dem_malla3_t2715__fijo10.csv)

La predicción de §15 del prerregistro va al lado de estos resultados para medir la sorpresa. El detalle está en veredicto3_celdas.csv, veredicto3_bases.csv, veredicto3_hipotesis.csv, veredicto3_comparaciones.csv y veredicto3_no_insertados.csv.
