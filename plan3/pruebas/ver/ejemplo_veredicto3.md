# Veredicto del bloque nuevo (plan 3) — EJEMPLO CON DATOS SINTÉTICOS (veredicto3.py --probar), no son resultados

Generado por `veredicto3.py` con las reglas de `PRERREGISTRO.md` (§7-§12). No editar a mano.

**Enmienda 1 (06.11.2026)**, `plan3/doc/enmienda_1.md`: con llegadas regulares no se corren H8c, H12, H15 regulares ni H9 regulares; H14 regulares queda solo con D. Tampoco se corren, con llegadas regulares, la entropía en P1, la 3b ni la a3 de la observación nueva en P1, P3 y P6. Holm va sobre lo que queda. En P1, P3, P4, P5 y P6 regulares no queda variante candidata: el modelo citado es V2, sin promoción. Con llegadas aleatorias no cambia nada. La enmienda reduce el alcance (desviación declarada, §14) y se decidió antes de cualquier dato del examen.

**Enmienda 2 (07.11.2026)**, `plan3/doc/enmienda_2.md`: con llegadas regulares queda solo la V2 de cada base frente al fijo fino, con el veto del actuado ajustado, en P1, P2, P3, P4, P5, P6 y P6e (T1 y T2): da H6 y la etiqueta regular por caso (H3 y H3e). No se corren H1, H2, H4, H7r, H8a, H10 ni H14 regulares; tampoco, con llegadas regulares, la ablación, el cuadro 2x2 (C0, V2 vieja e IPPO entregado), el puente con lo entregado, la V2 aleatoria jugada con ellas, las limpiezas por separado, la entropía, el reloj de 2 s sin forzadas, la a3 ni las demás referencias. No queda ninguna promoción regular: el modelo citado es V2. Con llegadas aleatorias no cambia nada. La enmienda reduce el alcance (desviación declarada, §14) y se decidió antes de cualquier dato del examen.

## Respuesta corta

- Número único, llegadas regulares (P1-P6, con P6): frente al plan fijo ajustado al segundo, -3.6 % [-3.7, -3.6] en la tanda 1 y -2.6 % [-2.8, -2.5] en la tanda 2 (frente al plan fijo entregado: no se corre (enmienda 2)).
- Número único, llegadas aleatorias (P1-P6, con P6): frente al plan fijo ajustado al segundo, -6.4 % [-6.4, -6.3] en la tanda 1 y -6.4 % [-6.4, -6.3] en la tanda 2 (frente al plan fijo entregado: -8.2 % [-8.2, -8.1] y -8.2 % [-8.3, -8.2]). IPPO con mensajes corregido: -6.0 % [-6.1, -6.0] y -6.0 % [-6.1, -6.0]. Cifra provisional en P3.
- Casos con etiqueta citable MEJORA o FUNCIONA: 13 de 19 (P1 (regulares), P2 (regulares), P6 (regulares), P6e (regulares), P1 (aleatorias), P2 (aleatorias), P4 (aleatorias), P5 (aleatorias), P6 (aleatorias), mix1 (aleatorias), mix3 (aleatorias), per1 (aleatorias), per3 (aleatorias))
- Hipótesis que pasan (con su regla global o, si se juzgan caso por caso, en al menos un caso): H7, H14 aleatorias, H9 aleatorias, H3, H5, H6.

## Cómo leer

- Etiqueta: la regla de lo entregado frente al fijo fino (FUNCIONA: mejora de 5 % o más, significativa y sin perder contra el actuado ajustado; MEJORA: mejora significativa; FALLA: empeora; EMPATA: el resto).
- Citable: la que se repite en las dos tandas de semillas. "Se repite": cuántos entrenamientos van del lado de la etiqueta.
- Cambio: retraso total por vehículo frente al fijo fino, con su IC95; † = un extremo del IC a menos de 0.05 puntos del 0.

## Tabla del anexo: etiqueta por caso

| Caso | Llegadas | Modelo citado | Tanda 1 | Tanda 2 | Citable | Cambio T1 [IC95] | Cambio T2 [IC95] | Se repite (T1; T2) | Con la mejor base |
|---|---|---|---|---|---|---|---|---|---|
| P1 | regulares | IPPO con mensajes corregido | FUNCIONA | FUNCIONA | FUNCIONA | -7.9 % [-8.1, -7.8] | -8.1 % [-8.2, -7.9] | 5 de 5; 5 de 5 | FUNCIONA |
| P2 | regulares | IPPO con mensajes corregido | MEJORA | MEJORA | MEJORA | -8.2 % [-8.3, -8.1] | -7.9 % [-8.0, -7.8] | 5 de 5; 5 de 5 | MEJORA |
| P3 | regulares | IPPO con mensajes corregido | MEJORA | EMPATA | EMPATA (mejora no confirmada) | -3.0 % [-3.1, -2.9] | -0.0 % [-0.6, 0.5] | 5 de 5; 3 de 5 | EMPATA (mejora no confirmada) |
| P4 | regulares | IPPO con mensajes corregido | FALLA | EMPATA | EMPATA (falla no confirmada) | +3.9 % [3.7, 4.0] | -0.0 % [-0.7, 0.7] | 5 de 5; 2 de 5 | EMPATA (falla no confirmada) |
| P5 | regulares | IPPO con mensajes corregido | MEJORA | FALLA | CONTRADICTORIO (no se concluye) | -3.0 % [-3.1, -2.9] | +4.0 % [3.8, 4.2] | 5 de 5; 5 de 5 | CONTRADICTORIO (no se concluye) |
| P6 | regulares | IPPO con mensajes corregido | MEJORA | MEJORA | MEJORA | -3.1 % [-3.2, -3.0] | -3.0 % [-3.1, -2.9] | 4 de 5; 4 de 5 | MEJORA |
| P6e | regulares | IPPO con mensajes corregido | MEJORA | MEJORA | MEJORA | -3.0 % [-3.2, -2.9] | -3.2 % [-3.3, -3.1] | 3 de 5; 3 de 5 | MEJORA |
| P1 | aleatorias | reloj de 2 s | FUNCIONA | FUNCIONA | FUNCIONA | -8.1 % [-8.3, -8.0] | -8.1 % [-8.2, -8.0] | 3 de 3; 3 de 3 | FUNCIONA |
| P2 | aleatorias | IPPO con mensajes corregido (entrenado con llegadas aleatorias) | FUNCIONA | FUNCIONA | FUNCIONA | -6.0 % [-6.1, -5.9] | -6.1 % [-6.2, -6.0] | 5 de 5; 5 de 5 | FUNCIONA |
| P3 | aleatorias | IPPO con mensajes corregido (entrenado con llegadas aleatorias) | PENDIENTE (FUNCIONA) | PENDIENTE (FUNCIONA) | PENDIENTE (FUNCIONA) | -5.9 % [-6.1, -5.8] | -5.9 % [-6.0, -5.8] | 5 de 5; 5 de 5 | FUNCIONA |
| P4 | aleatorias | IPPO con mensajes corregido (entrenado con llegadas aleatorias) | FUNCIONA | FUNCIONA | FUNCIONA | -6.0 % [-6.1, -5.8] | -6.0 % [-6.2, -5.9] | 3 de 5; 3 de 5 | FUNCIONA |
| P5 | aleatorias | IPPO con mensajes corregido (entrenado con llegadas aleatorias) | FUNCIONA | FUNCIONA | FUNCIONA | -6.1 % [-6.2, -6.0] | -6.1 % [-6.2, -5.9] | 5 de 5; 5 de 5 | FUNCIONA |
| P6 | aleatorias | IPPO con mensajes corregido (entrenado con llegadas aleatorias) | FUNCIONA | FUNCIONA | FUNCIONA | -6.1 % [-6.2, -6.0] | -6.1 % [-6.2, -5.9] | 5 de 5; 5 de 5 | FUNCIONA |
| mix1 | aleatorias | IPPO con mensajes corregido (entrenado con la mezcla) | FUNCIONA | FUNCIONA | FUNCIONA | -6.0 % [-6.1, -5.9] | -6.0 % [-6.1, -5.8] | 3 de 3; 3 de 3 | FUNCIONA |
| mix3 | aleatorias | IPPO con mensajes corregido (entrenado con la mezcla) | MEJORA | MEJORA | MEJORA | -2.9 % [-3.0, -2.8] | -3.1 % [-3.2, -3.0] | 3 de 3; 3 de 3 | MEJORA |
| mixa1 | aleatorias | IPPO con mensajes corregido (entrenado con la mezcla) | PENDIENTE | PENDIENTE | PENDIENTE | — | — | —; — | PENDIENTE |
| mixa3 | aleatorias | IPPO con mensajes corregido (entrenado con la mezcla) | PENDIENTE | PENDIENTE | PENDIENTE | -5.9 % [-6.0, -5.8] | -6.0 % [-6.2, -5.8] | 3 de 3; 3 de 3 | PENDIENTE |
| per1 | aleatorias | IPPO con mensajes corregido (entrenado con el perfil) | FUNCIONA | FUNCIONA | FUNCIONA | -6.1 % [-6.2, -6.0] | -6.0 % [-6.2, -5.9] | 3 de 3; 3 de 3 | FUNCIONA |
| per3 | aleatorias | IPPO con mensajes corregido (entrenado con el perfil) | FUNCIONA | FUNCIONA | FUNCIONA | -5.8 % [-5.9, -5.7] | -6.0 % [-6.2, -5.8] | 3 de 3; 3 de 3 | FUNCIONA |

## Hipótesis

| Id | Qué se prueba | Resultado |
|---|---|---|
| H1 | V2 no es peor que C0 en ningún caso (P1-P6, 120 semillas) | no se corre (enmienda 2) |
| H2 | V2 < C0 (120 semillas por tanda) | no se corre (enmienda 2) |
| H7r | con mensajes < sin mensajes, llegadas regulares | no se corre (enmienda 2) |
| H7 | con mensajes < sin mensajes, llegadas aleatorias | pasa en 6 de 6 casos: P1, P2, P3, P4, P5, P6 |
| H8a | V2 + observación < V2, llegadas regulares | no se corre (enmienda 2) |
| H8b | V2 + observación < V2, llegadas aleatorias | no pasa: 0 de 6 casos (ninguno); hace falta 1 |
| H8c | V2 + observación no es peor que V2 | no se corre (enmienda 1) |
| H12 | V2 + las tres limpiezas no es peor que V2 | no se corre (enmienda 1) |
| H14 regulares | reloj de 2 s < reloj de 5 s | no se corre (enmienda 2) |
| H14 aleatorias | reloj de 2 s < reloj de 5 s | pasa en 3 de 3 casos: P1, P2, P6 |
| H15 regulares | modelo completo < V2 | no se corre (enmienda 1) |
| H15 aleatorias | modelo completo < V2 | pasa en 0 de 6 casos: ninguno |
| H9 regulares | 400 episodios con piso < 200 sin piso | no se corre (enmienda 1) |
| H9 aleatorias | 400 episodios con piso < 200 sin piso | pasa en 6 de 6 casos: P1, P2, P3, P4, P5, P6 |
| H10 corredor | una política por red (corredor) no es peor que la V2 de cada nivel | no se corre (enmienda 2) |
| H10 red | una política por red (red) no es peor que la V2 de cada nivel | no se corre (enmienda 2) |
| H10 malla | una política por red (malla) no es peor que la V2 de cada nivel | no se corre (enmienda 2) |
| H3 | V2 MEJORA o FUNCIONA frente al fijo fino en P6 | citable MEJORA; sentido 4 de 5 y 4 de 5 |
| H3e | V2 MEJORA o FUNCIONA frente al fijo fino en P6e | citable MEJORA; sentido 3 de 5 (hacen falta 4) y 3 de 5 (hacen falta 4) (descriptiva) |
| H5 | V2 aleatoria MEJORA o FUNCIONA frente al fijo fino re-ajustado en al menos 3 de 6 | pasa: 4 de 6 casos (P1, P2, P5, P6); hacen falta 3 |
| H6 | la ventaja frente al fijo es mayor con llegadas aleatorias (por caso) | pasa en 3 de 6 casos: P3, P5, P6 |
| H4 | cada base de V2 a ±1 % del ciclo mínimo en T1 y T2 (descriptiva) | no se corre (enmienda 2) |
| H0 | ¿el desorden abre margen? (descriptiva) | en 6 de 6 casos algún control que reacciona da MEJORA o FUNCIONA |

## Lecturas obligadas (§5 y §11)

- P6 (regulares): P6 con la entrada por defecto: el cambio relativo está diluido por la espera de inserción; ver P6e.
- P6e (regulares): La versión evaluada mejora; el método no se repite en 3 de 5 entrenamientos (T1).
- P1 (aleatorias): El modelo citado no es IPPO con mensajes corregido: es reloj de 2 s; la etiqueta de IPPO con mensajes corregido es FUNCIONA.
- P2 (aleatorias): Deja vehículos sin entrar al cierre (fijo fino en t1a: 3 de 10 semillas, 120 vehículos): su retraso total está subestimado y la diferencia con un brazo que no los deja es conservadora.
- P3 (aleatorias): PENDIENTE por no convergencia; probabilidad de que una política estable salga así por ruido: no medido (§6).
- P4 (aleatorias): La versión evaluada mejora; el método no se repite en 3 de 5 entrenamientos (T1).
- mix3 (aleatorias): Reproduce el ciclo mínimo (no se dice "coordinación aprendida"). | No le gana a la regla reactiva: no se dice que el modelo aprendió algo que la regla no hace ni "coordinación aprendida" (§5).

## Referencias al lado (etiqueta citable del modelo citado frente a cada una)

| Caso | Llegadas | actuado por defecto | actuado ajustado | fijo por bloques | fijo entregado | fijo de verdes de 5 en 5 | fijo por franja | Max-Pressure | regla reactiva | regla simple | ciclo mínimo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | regulares | — | FUNCIONA | — | — | — | — | — | — | — | — |
| P2 | regulares | — | FALLA | — | — | — | — | — | — | — | — |
| P3 | regulares | — | MEJORA | — | — | — | — | — | — | — | — |
| P4 | regulares | — | CONTRADICTORIO (no se concluye) | — | — | — | — | — | — | — | — |
| P5 | regulares | — | CONTRADICTORIO (no se concluye) | — | — | — | — | — | — | — | — |
| P6 | regulares | — | FUNCIONA | — | — | — | — | — | — | — | — |
| P6e | regulares | — | FUNCIONA | — | — | — | — | — | — | — | — |
| P1 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | MEJORA | FUNCIONA | FUNCIONA |
| P2 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | MEJORA | FUNCIONA | FUNCIONA |
| P3 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | MEJORA | FUNCIONA | FUNCIONA |
| P4 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | MEJORA | FUNCIONA | FUNCIONA |
| P5 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | FUNCIONA | PENDIENTE | FUNCIONA | MEJORA | FUNCIONA | FUNCIONA |
| P6 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | MEJORA | FUNCIONA | FUNCIONA |
| mix1 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | — | — | — | MEJORA | FUNCIONA | FUNCIONA |
| mix3 | aleatorias | FUNCIONA | FUNCIONA | — | MEJORA | — | — | — | FALLA | FUNCIONA | EMPATA |
| mixa1 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | — | — | — | MEJORA | FUNCIONA | FUNCIONA |
| mixa3 | aleatorias | FUNCIONA | — | — | FUNCIONA | — | — | — | MEJORA | FUNCIONA | FUNCIONA |
| per1 | aleatorias | FUNCIONA | FUNCIONA | MEJORA | FUNCIONA | — | — | FUNCIONA | MEJORA | FUNCIONA | FUNCIONA |
| per3 | aleatorias | FUNCIONA | FUNCIONA | MEJORA | FUNCIONA | — | — | FUNCIONA | MEJORA | FUNCIONA | FUNCIONA |

## PENDIENTE

- P3 (aleatorias): PENDIENTE (no convergió; provisional: FUNCIONA); probabilidad de que una política estable no converja por ruido (§6): no medido.
- mixa1 (aleatorias): PENDIENTE (falta fijo fino en t1a).
- mixa3 (aleatorias): PENDIENTE (falta actuado ajustado en t1a).

## Regla de promoción (§12): validación en 15009-15024 frente a V2

- P1 (aleatorias): reloj de 2 s -3.25 %, modelo completo +0.23 %, observación nueva +0.26 %, 400 episodios +0.26 %; se cita reloj de 2 s (promovido: le gana a V2 por al menos 1 %).
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

## Avisos

- 27 CSV de la tanda promo no entran al veredicto (regla de promoción: se leen en promocion/<esc>.json)
- P5 (poi_malla3, t1a): los brazos no generan los mismos vehículos en 1 semilla (la primera, 424344; distinto: ciego/t1a/eval_poi_malla3__franja.csv)

La predicción de §15 del prerregistro va al lado de estos resultados para medir la sorpresa. El detalle está en veredicto3_celdas.csv, veredicto3_bases.csv, veredicto3_hipotesis.csv, veredicto3_comparaciones.csv y veredicto3_no_insertados.csv.
