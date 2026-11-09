# Veredicto del bloque nuevo (plan 3)

Generado por `veredicto3.py` con las reglas de `PRERREGISTRO.md` (§7-§12). No editar a mano.

**Enmienda 1 (06.11.2026)**, `plan3/doc/enmienda_1.md`: con llegadas regulares no se corren H8c, H12, H15 regulares ni H9 regulares; H14 regulares queda solo con D. Tampoco se corren, con llegadas regulares, la entropía en P1, la 3b ni la a3 de la observación nueva en P1, P3 y P6. Holm va sobre lo que queda. En P1, P3, P4, P5 y P6 regulares no queda variante candidata: el modelo citado es V2, sin promoción. Con llegadas aleatorias no cambia nada. La enmienda reduce el alcance (desviación declarada, §14) y se decidió antes de cualquier dato del examen.

**Enmienda 2 (07.11.2026)**, `plan3/doc/enmienda_2.md`: con llegadas regulares queda solo la V2 de cada base frente al fijo fino, con el veto del actuado ajustado, en P1, P2, P3, P4, P5, P6 y P6e (T1 y T2): da H6 y la etiqueta regular por caso (H3 y H3e). No se corren H1, H2, H4, H7r, H8a, H10 ni H14 regulares; tampoco, con llegadas regulares, la ablación, el cuadro 2x2 (C0, V2 vieja e IPPO entregado), el puente con lo entregado, la V2 aleatoria jugada con ellas, las limpiezas por separado, la entropía, el reloj de 2 s sin forzadas, la a3 ni las demás referencias. No queda ninguna promoción regular: el modelo citado es V2. Con llegadas aleatorias no cambia nada. La enmienda reduce el alcance (desviación declarada, §14) y se decidió antes de cualquier dato del examen.

## Respuesta corta

- Número único, llegadas regulares (P1-P6, con P6): frente al plan fijo ajustado al segundo, -0.4 % [-1.0, 0.1] en la tanda 1 y -0.4 % [-0.8, 0.1] en la tanda 2 (frente al plan fijo entregado: no se corre (enmienda 2)). Cifra provisional en P5.
- Número único, llegadas aleatorias (P1-P6, con P6): frente al plan fijo ajustado al segundo, -10.8 % [-11.4, -10.2] en la tanda 1 y -11.1 % [-12.0, -10.4] en la tanda 2 (frente al plan fijo entregado: -15.8 % [-17.4, -14.2] y -14.5 % [-15.9, -13.1]). IPPO con mensajes corregido: -4.8 % [-5.6, -3.9] y -5.6 % [-6.5, -4.8]. Cifra provisional en P2.
- Casos con etiqueta citable MEJORA o FUNCIONA: 5 de 19 (P1 (regulares), P1 (aleatorias), P6 (aleatorias), mix1 (aleatorias), mixa1 (aleatorias))
- Hipótesis que pasan (con su regla global o, si se juzgan caso por caso, en al menos un caso): H7, H8b, H15 aleatorias, H9 aleatorias, H5, H6.

## Cómo leer

- Etiqueta: la regla de lo entregado frente al fijo fino (FUNCIONA: mejora de 5 % o más, significativa y sin perder contra el actuado ajustado; MEJORA: mejora significativa; FALLA: empeora; EMPATA: el resto).
- Citable: la que se repite en las dos tandas de semillas. "Se repite": cuántos entrenamientos van del lado de la etiqueta.
- Cambio: retraso total por vehículo frente al fijo fino, con su IC95; † = un extremo del IC a menos de 0.05 puntos del 0.

## Tabla del anexo: etiqueta por caso

| Caso | Llegadas | Modelo citado | Tanda 1 | Tanda 2 | Citable | Cambio T1 [IC95] | Cambio T2 [IC95] | Se repite (T1; T2) | Con la mejor base |
|---|---|---|---|---|---|---|---|---|---|
| P1 | regulares | IPPO con mensajes corregido | MEJORA | MEJORA | MEJORA | -2.8 % [-3.7, -2.0] | -2.8 % [-3.6, -1.9] | 5 de 5; 5 de 5 | MEJORA |
| P2 | regulares | IPPO con mensajes corregido | EMPATA | EMPATA | EMPATA | -1.7 % [-3.3, -0.0] † | -1.3 % [-3.0, 0.4] | 4 de 5; 5 de 5 | PENDIENTE (MEJORA) |
| P3 | regulares | IPPO con mensajes corregido | FALLA | FALLA | FALLA | +1.7 % [1.3, 2.1] | +1.7 % [1.3, 2.1] | 5 de 5; 5 de 5 | FALLA |
| P4 | regulares | IPPO con mensajes corregido | EMPATA | EMPATA | EMPATA | +0.5 % [-1.5, 2.5] | +0.4 % [-1.1, 1.8] | 0 de 5; 0 de 5 | EMPATA |
| P5 | regulares | IPPO con mensajes corregido | PENDIENTE (EMPATA) | PENDIENTE (EMPATA) | PENDIENTE (EMPATA) | +0.1 % [-0.1, 0.5] | +0.1 % [-0.2, 0.4] | 0 de 5; 1 de 5 | EMPATA |
| P6 | regulares | IPPO con mensajes corregido | EMPATA | EMPATA | EMPATA | -0.3 % [-2.0, 1.8] | -0.2 % [-1.4, 1.3] | 4 de 5; 2 de 5 | EMPATA |
| P6e | regulares | IPPO con mensajes corregido | FALLA | FALLA | FALLA | +9.8 % [9.2, 10.5] | +10.5 % [9.6, 11.5] | 5 de 5; 5 de 5 | PENDIENTE (FALLA) |
| P1 | aleatorias | modelo completo | FUNCIONA | FUNCIONA | FUNCIONA | -16.3 % [-17.7, -15.0] | -17.1 % [-18.6, -15.8] | 3 de 3; 3 de 3 | FUNCIONA |
| P2 | aleatorias | modelo completo | PENDIENTE (FUNCIONA) | PENDIENTE (FUNCIONA) | PENDIENTE (FUNCIONA) | -19.8 % [-20.5, -19.0] | -20.2 % [-20.9, -19.6] | 3 de 3; 3 de 3 | FUNCIONA |
| P3 | aleatorias | IPPO con mensajes corregido (entrenado con llegadas aleatorias) | FALLA | FALLA | FALLA | +1.6 % [1.4, 1.7] | +1.6 % [1.4, 1.8] | 5 de 5; 5 de 5 | FALLA |
| P4 | aleatorias | modelo completo | EMPATA | EMPATA | EMPATA | -0.5 % [-1.3, 0.2] | -0.0 % [-0.7, 0.6] | 3 de 3; 3 de 3 | MEJORA |
| P5 | aleatorias | IPPO con mensajes corregido (entrenado con llegadas aleatorias) | EMPATA | EMPATA | EMPATA | +0.2 % [-0.1, 0.5] | +0.3 % [0.0, 0.7] † | 0 de 5; 0 de 5 | EMPATA (falla no confirmada) |
| P6 | aleatorias | modelo completo | FUNCIONA | FUNCIONA | FUNCIONA | -25.7 % [-28.4, -23.0] | -26.9 % [-30.8, -23.5] | 3 de 3; 3 de 3 | FUNCIONA |
| mix1 | aleatorias | IPPO con mensajes corregido (entrenado con la mezcla) | MEJORA | MEJORA | MEJORA | -3.8 % [-4.7, -2.9] | -3.2 % [-4.1, -2.4] | 3 de 3; 3 de 3 | MEJORA |
| mix3 | aleatorias | IPPO con mensajes corregido (entrenado con la mezcla) | FALLA | FALLA | FALLA | +1.7 % [1.5, 1.9] | +1.8 % [1.7, 2.0] | 3 de 3; 3 de 3 | FALLA |
| mixa1 | aleatorias | IPPO con mensajes corregido (entrenado con la mezcla) | MEJORA | MEJORA | MEJORA | -3.4 % [-4.3, -2.5] | -3.2 % [-4.0, -2.3] | 3 de 3; 3 de 3 | MEJORA |
| mixa3 | aleatorias | IPPO con mensajes corregido (entrenado con la mezcla) | FALLA | FALLA | FALLA | +1.3 % [1.1, 1.4] | +1.2 % [1.0, 1.3] | 3 de 3; 3 de 3 | FALLA |
| per1 | aleatorias | IPPO con mensajes corregido (entrenado con el perfil) | PENDIENTE (FUNCIONA) | PENDIENTE (FUNCIONA) | PENDIENTE (FUNCIONA) | -12.1 % [-14.5, -9.7] | -9.8 % [-11.8, -7.8] | 3 de 3; 3 de 3 | FUNCIONA |
| per3 | aleatorias | IPPO con mensajes corregido (entrenado con el perfil) | FALLA | FALLA | FALLA | +1.0 % [0.5, 1.5] | +1.1 % [0.6, 1.7] | 3 de 3; 3 de 3 | FALLA |

## Hipótesis

| Id | Qué se prueba | Resultado |
|---|---|---|
| H1 | V2 no es peor que C0 en ningún caso (P1-P6, 120 semillas) | no se corre (enmienda 2) |
| H2 | V2 < C0 (120 semillas por tanda) | no se corre (enmienda 2) |
| H7r | con mensajes < sin mensajes, llegadas regulares | no se corre (enmienda 2) |
| H7 | con mensajes < sin mensajes, llegadas aleatorias | pasa en 1 de 6 casos: P6 |
| H8a | V2 + observación < V2, llegadas regulares | no se corre (enmienda 2) |
| H8b | V2 + observación < V2, llegadas aleatorias | pasa: 3 de 6 casos (P1, P2, P6); hace falta 1 |
| H8c | V2 + observación no es peor que V2 | no se corre (enmienda 1) |
| H12 | V2 + las tres limpiezas no es peor que V2 | no se corre (enmienda 1) |
| H14 regulares | reloj de 2 s < reloj de 5 s | no se corre (enmienda 2) |
| H14 aleatorias | reloj de 2 s < reloj de 5 s | pasa en 0 de 3 casos: ninguno |
| H15 regulares | modelo completo < V2 | no se corre (enmienda 1) |
| H15 aleatorias | modelo completo < V2 | pasa en 4 de 6 casos: P1, P2, P4, P6 |
| H9 regulares | 400 episodios con piso < 200 sin piso | no se corre (enmienda 1) |
| H9 aleatorias | 400 episodios con piso < 200 sin piso | pasa en 1 de 6 casos: P6 |
| H10 corredor | una política por red (corredor) no es peor que la V2 de cada nivel | no se corre (enmienda 2) |
| H10 red | una política por red (red) no es peor que la V2 de cada nivel | no se corre (enmienda 2) |
| H10 malla | una política por red (malla) no es peor que la V2 de cada nivel | no se corre (enmienda 2) |
| H3 | V2 MEJORA o FUNCIONA frente al fijo fino en P6 | citable EMPATA; sentido 4 de 5 y 2 de 5 (hacen falta 4) |
| H3e | V2 MEJORA o FUNCIONA frente al fijo fino en P6e | citable FALLA; sentido 0 de 5 (hacen falta 4) y 0 de 5 (hacen falta 4) (descriptiva) |
| H5 | V2 aleatoria MEJORA o FUNCIONA frente al fijo fino re-ajustado en al menos 3 de 6 | pasa: 3 de 6 casos (P1, P2, P6); hacen falta 3 |
| H6 | la ventaja frente al fijo es mayor con llegadas aleatorias (por caso) | pasa en 2 de 6 casos: P2, P6 |
| H4 | cada base de V2 a ±1 % del ciclo mínimo en T1 y T2 (descriptiva) | no se corre (enmienda 2) |
| H0 | ¿el desorden abre margen? (descriptiva) | en 3 de 6 casos algún control que reacciona da MEJORA o FUNCIONA |

## Lecturas obligadas (§5 y §11)

- P5 (regulares): PENDIENTE por no convergencia; probabilidad de que una política estable salga así por ruido: 0-1 % (§6).
- P6 (regulares): P6 con la entrada por defecto: el cambio relativo está diluido por la espera de inserción; ver P6e.
- P1 (aleatorias): El modelo citado no es IPPO con mensajes corregido: es modelo completo; la etiqueta de IPPO con mensajes corregido es MEJORA.
- P2 (aleatorias): El modelo citado no es IPPO con mensajes corregido: es modelo completo; la etiqueta de IPPO con mensajes corregido es FUNCIONA. | PENDIENTE por no convergencia; probabilidad de que una política estable salga así por ruido: no medido (§6). | Deja vehículos sin entrar al cierre (regla reactiva en t1a: 1 de 100 semillas, 28 vehículos; ciclo mínimo en t1a: 100 de 100 semillas, 20877 vehículos; ciclo mínimo en t2a: 100 de 100 semillas, 20606 vehículos): su retraso total está subestimado y la diferencia con un brazo que no los deja es conservadora.
- P3 (aleatorias): Reproduce el ciclo mínimo (no se dice "coordinación aprendida"). | No le gana a la regla simple: no se dice que el modelo aprendió algo que la regla no hace ni "coordinación aprendida" (§5). | El fijo de verdes de 5 en 5 iguala o supera al modelo: parte de la ventaja del fijo fino viene de verdes que IPPO, al decidir cada 5 s, no puede dar.
- P4 (aleatorias): No le gana a la regla simple: no se dice que el modelo aprendió algo que la regla no hace ni "coordinación aprendida" (§5). | El fijo de verdes de 5 en 5 iguala o supera al modelo: parte de la ventaja del fijo fino viene de verdes que IPPO, al decidir cada 5 s, no puede dar. | El modelo citado no es IPPO con mensajes corregido: es modelo completo; la etiqueta de IPPO con mensajes corregido es FALLA.
- P5 (aleatorias): No le gana a la regla simple: no se dice que el modelo aprendió algo que la regla no hace ni "coordinación aprendida" (§5). | El fijo de verdes de 5 en 5 iguala o supera al modelo: parte de la ventaja del fijo fino viene de verdes que IPPO, al decidir cada 5 s, no puede dar.
- P6 (aleatorias): El modelo citado no es IPPO con mensajes corregido: es modelo completo; la etiqueta de IPPO con mensajes corregido es FUNCIONA. | Deja vehículos sin entrar al cierre (ciclo mínimo en t1a: 13 de 100 semillas, 2855 vehículos; ciclo mínimo en t2a: 14 de 100 semillas, 6323 vehículos): su retraso total está subestimado y la diferencia con un brazo que no los deja es conservadora.
- mix1 (aleatorias): No le gana a la regla reactiva: no se dice que el modelo aprendió algo que la regla no hace ni "coordinación aprendida" (§5).
- mix3 (aleatorias): Reproduce el ciclo mínimo (no se dice "coordinación aprendida"). | No le gana a la regla simple: no se dice que el modelo aprendió algo que la regla no hace ni "coordinación aprendida" (§5).
- mixa1 (aleatorias): No le gana a la regla reactiva: no se dice que el modelo aprendió algo que la regla no hace ni "coordinación aprendida" (§5).
- mixa3 (aleatorias): Reproduce el ciclo mínimo (no se dice "coordinación aprendida"). | No le gana a la regla simple: no se dice que el modelo aprendió algo que la regla no hace ni "coordinación aprendida" (§5).
- per1 (aleatorias): PENDIENTE por no convergencia; probabilidad de que una política estable salga así por ruido: no medido (§6).
- per3 (aleatorias): No le gana a la regla simple: no se dice que el modelo aprendió algo que la regla no hace ni "coordinación aprendida" (§5).

## Referencias al lado (etiqueta citable del modelo citado frente a cada una)

| Caso | Llegadas | actuado por defecto | actuado ajustado | fijo por bloques | fijo entregado | fijo de verdes de 5 en 5 | fijo por franja | Max-Pressure | regla reactiva | regla simple | ciclo mínimo |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | regulares | — | FALLA | — | — | — | — | — | — | — | — |
| P2 | regulares | — | MEJORA | — | — | — | — | — | — | — | — |
| P3 | regulares | — | FALLA | — | — | — | — | — | — | — | — |
| P4 | regulares | — | EMPATA | — | — | — | — | — | — | — | — |
| P5 | regulares | — | FALLA | — | — | — | — | — | — | — | — |
| P6 | regulares | — | EMPATA | — | — | — | — | — | — | — | — |
| P6e | regulares | — | EMPATA (falla no confirmada) | — | — | — | — | — | — | — | — |
| P1 | aleatorias | FUNCIONA | MEJORA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA |
| P2 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA |
| P3 | aleatorias | FUNCIONA | FALLA | — | EMPATA (mejora no confirmada) | FALLA | FALLA | FUNCIONA | FUNCIONA | EMPATA | EMPATA |
| P4 | aleatorias | FUNCIONA | EMPATA | — | MEJORA | EMPATA | EMPATA | FUNCIONA | FUNCIONA | EMPATA (mejora no confirmada) | EMPATA (mejora no confirmada) |
| P5 | aleatorias | FUNCIONA | EMPATA | — | EMPATA | EMPATA | EMPATA | FUNCIONA | FUNCIONA | EMPATA | EMPATA |
| P6 | aleatorias | FUNCIONA | FUNCIONA | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA |
| mix1 | aleatorias | FALLA | FALLA | — | MEJORA | — | — | — | EMPATA (falla no confirmada) | FUNCIONA | FUNCIONA |
| mix3 | aleatorias | FUNCIONA | FALLA | — | EMPATA | — | — | — | FUNCIONA | EMPATA | EMPATA |
| mixa1 | aleatorias | FALLA | FALLA | — | FUNCIONA | — | — | — | EMPATA (falla no confirmada) | FUNCIONA | FUNCIONA |
| mixa3 | aleatorias | FUNCIONA | FALLA | — | MEJORA | — | — | — | FUNCIONA | EMPATA | EMPATA |
| per1 | aleatorias | EMPATA | EMPATA | FUNCIONA | FUNCIONA | — | — | FUNCIONA | FUNCIONA | FUNCIONA | FUNCIONA |
| per3 | aleatorias | MEJORA | FALLA | EMPATA | EMPATA (mejora no confirmada) | — | — | FUNCIONA | FUNCIONA | EMPATA | EMPATA |

## PENDIENTE

- P5 (regulares): PENDIENTE (no convergió; provisional: EMPATA); probabilidad de que una política estable no converja por ruido (§6): 0-1 %.
- P2 (aleatorias): PENDIENTE (no convergió; provisional: FUNCIONA); probabilidad de que una política estable no converja por ruido (§6): no medido.
- per1 (aleatorias): PENDIENTE (no convergió; provisional: FUNCIONA); probabilidad de que una política estable no converja por ruido (§6): no medido.

## Regla de promoción (§12): validación en 15009-15024 frente a V2

- P1 (aleatorias): modelo completo -9.04 %, observación nueva -8.06 %, 400 episodios -1.27 %, reloj de 2 s +0.15 %; se cita modelo completo (promovido: le gana a V2 por al menos 1 %).
- P2 (aleatorias): modelo completo -13.61 %, observación nueva -9.83 %, 400 episodios -1.48 %, reloj de 2 s +1.71 %; se cita modelo completo (promovido: le gana a V2 por al menos 1 %).
- P3 (aleatorias): modelo completo -0.36 %, 400 episodios +0.00 %, observación nueva +0.30 %; se cita IPPO con mensajes corregido (entrenado con llegadas aleatorias).
- P4 (aleatorias): modelo completo -1.24 %, 400 episodios +0.00 %, observación nueva +0.08 %; se cita modelo completo (promovido: le gana a V2 por al menos 1 %).
- P5 (aleatorias): 400 episodios +0.00 %, modelo completo +1.87 %, observación nueva +5.90 %; se cita IPPO con mensajes corregido (entrenado con llegadas aleatorias).
- P6 (aleatorias): modelo completo -8.79 %, observación nueva -6.89 %, 400 episodios -5.24 %, reloj de 2 s +3.67 %; se cita modelo completo (promovido: le gana a V2 por al menos 1 %).

## Vehículos sin entrar al cierre (§4)

- P2 (aleatorias, t1a): regla reactiva: 1 de 100 semillas, 28 vehículos
- P2 (aleatorias, t1a): ciclo mínimo: 100 de 100 semillas, 20877 vehículos
- P2 (aleatorias, t2a): ciclo mínimo: 100 de 100 semillas, 20606 vehículos
- P6 (aleatorias, t1a): ciclo mínimo: 13 de 100 semillas, 2855 vehículos
- P6 (aleatorias, t2a): ciclo mínimo: 14 de 100 semillas, 6323 vehículos
- Lectura obligada: el retraso total de esos brazos está subestimado y la diferencia con un brazo que no los deja es conservadora. Detalle por brazo en veredicto3_no_insertados.csv.

## Entrenamientos caídos o sin publicar

- Ninguno.
- Relanzamientos, desvíos y enmiendas: en cola/estado.json y en las enmiendas del prerregistro (§11, §14); veredicto3 no los calcula.

## V2 del diagnóstico del corredor (§6)

- P1: la versión evaluada de la V2 del diagnóstico (Sección 5.5.1) es la base 42; la de ahora es la base 16042 (se muestran las dos).

## Procedencia

- Código: commit fc7433534bd58f6c1cd83eeeb3513468488f885a; rama empujada fc7433534bd58f6c1cd83eeeb3513468488f885a; sello sha256 f7e4f611cb0087ebbf68a176b4f8a17f631acb7a82172bdaeca3317b498a31fd.
- Blobs de git del código del análisis: veredicto3.py 2072772fae00; manifiesto.py 6d08ee4b7b22; generar_trabajos3.py 8bacab782de0; protecciones.py fa10a6f1fcc6; anclaje.py 8ef0d643a6a1; p3_promocion.py 70c021f2e658; PRERREGISTRO.md d38d9c04a86d; doc/enmienda_2_quitados.txt 74eea802262d; ../veredicto.py d9fe64cd8632; ../consolidar.py 083b9cd1c335; ../sintesis_plan.py 942019b4a463.
- El sha256 de cada salida está en veredicto3_procedencia.json.

## Avisos

- 27 CSV de la tanda promo no entran al veredicto (regla de promoción: se leen en promocion/<esc>.json)

La predicción de §15 del prerregistro va al lado de estos resultados para medir la sorpresa. El detalle está en veredicto3_celdas.csv, veredicto3_bases.csv, veredicto3_hipotesis.csv, veredicto3_comparaciones.csv y veredicto3_no_insertados.csv.
