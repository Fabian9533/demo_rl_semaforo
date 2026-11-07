# Enmienda 1 del plan 3: el plan se centra en el tráfico aleatorio

**Fecha:** 06.11.2026. **Decide:** Fabian Alvarado. **Se avisa por correo al asesor**, con el commit y el tag
`plan3-enmienda-1`.

**Datos a la vista al decidir:** solo entrenamiento, validación y referencias con semillas de ajuste. **Ninguna
evaluación del examen** había corrido: no existía ningún CSV de `plan3/ciego/`.

## Qué cambia

**Con llegadas regulares, se mantiene:**
- la Etapa 1 completa (V2, la ablación y V2 sin mensajes), C0, las referencias y todas sus evaluaciones: son el control
  y el puente con lo entregado;
- la Etapa 3 donde hay una pregunta abierta: la observación nueva en 2715, D y P2 (H8a), y las piezas sueltas en D
  (limpiezas, entropía y reloj de 2 s).

**Con llegadas regulares, se quita:**

| Hipótesis o análisis | Qué deja de correr |
|---|---|
| H8c | La observación nueva en P1, P3 y P6 |
| H12 | Las limpiezas juntas en P2 y P6 |
| H14, parte regular | El reloj de 2 s en P1, P2 y P6 (queda en D) |
| H15, parte regular | El modelo completo en P1, P2, P4 y P6 |
| H9, parte regular | Los 400 episodios (3b) en P1-P6 |
| Descriptiva | La entropía en P1 (queda en D) |
| a3 | La observación nueva perturbada en P1, P3 y P6 (V2 perturbada sigue en todos los casos) |

Con ellas se van sus evaluaciones del examen y su promoción. En P1, P3, P4, P5 y P6 regulares no queda ninguna
variante candidata, así que **el modelo citado es V2**. La promoción sigue en P2, 2715, D y en los seis casos con
llegadas aleatorias.

**Con llegadas aleatorias no cambia nada.** Tampoco cambian las semillas, las métricas, los márgenes ni las reglas de
lectura.

**Familias de Holm:** H14 regular queda con D solo y H15 regular sin casos. H9 queda solo con la familia de llegadas
aleatorias. H8c y H12 no se corren.

## Por qué

- El tráfico regular ya está estudiado en las entregas anteriores. Con él, un fijo bien afinado es casi imbatible
  (§15), y las preguntas que importan las responde mejor el tráfico aleatorio, que es el realista.
- Se conserva lo regular que sirve de control: con tráfico parejo el RL debería empatar, y con tráfico variable debería
  ganar. También se conserva la pregunta abierta del caso 2715.
- Ahorra unas 340 horas de proceso estimadas (~250 reales, un día de cómputo): 72 entrenamientos de la Etapa 3,
  57 trabajos de la 3b y 244 evaluaciones, medianas y pasos de promoción.

## Desviación que se declara

La §14 dice que, después de la parte A, una enmienda solo puede corregir un error de código, reemplazar un trabajo que
no se puede correr o fijar lo ya anunciado. **Esta enmienda va más allá: reduce el alcance.** Se declara como tal.

Lo que la justifica es el momento: se decide antes de cualquier dato del examen. Lo que se quita, se quita sin saber si
le iba a ir bien o mal. El informe final la repite (§11).

## Dónde está en el código

`plan3/generar_trabajos3.py`: `QUITADOS_ENMIENDA1`, `TIPOS_3B` y `queda()`. `plan3/veredicto3.py` marca esas hipótesis
como "no se corre (enmienda 1)".
