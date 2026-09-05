---
name: experimento-sumo
description: Crear, tunear y correr un experimento de control semafórico con RL en SUMO para la tesis (nuevo escenario, baseline honesto, entrenamiento, comparación y registro de resultados). Usar cuando se pida agregar un cruce/escenario nuevo, re-correr pruebas, comparar contra tiempo fijo o preparar números para el documento.
---

# Experimento de control semafórico en SUMO

Procedimiento estándar de esta carpeta para que cada prueba sea comparable con
las anteriores y citable en la tesis. Leer primero CLAUDE.md (formulación RL y
convenciones); la formulación implementada no se toca sin actualizar a la vez el
código, el documento (`TESIS/secciones/capitulo4.tex`, módulo U2) y LEEME.txt.
Todo resultado que se vaya a citar termina en la tesis con el skill
`escribir-tesis`, en el mismo turno.

## 1. Definir el escenario

Un escenario `<esc>` son estos archivos con el mismo prefijo:
- `<esc>.nod.xml` — nodos; el cruce controlado lleva `type="traffic_light"` y
  `tl="semaforo_..."`.
- `<esc>.edg.xml` — vías, 13.89 m/s (50 km/h) salvo justificación; ids con el
  patrón `ORIGEN_DESTINO` (ej. `N_C`, `C1_C2`).
- `<esc>.con.xml` — solo si hace falta forzar carriles por movimiento (ej. carril
  exclusivo de giro a la izquierda).
- `<esc>.rou.xml` — demanda con `<flow>` por periodo; mantener el patrón de
  demanda que cambia a mitad de la simulación (0–1800 s / 1800–3600 s) para que
  el tiempo fijo no pueda ser óptimo en ambos periodos a la vez.
- `<esc>.sumocfg` — igual al de `cruce` (`time-to-teleport = -1`, sin warnings).

Regenerar la red con netconvert (agregar la línea al `build_net.bat`):
`--no-turnarounds` siempre; `--tls.green.time <G>` para el programa fijo;
`--tls.left-green.time <L>` si hay giros protegidos.

Antes de seguir, verificar la demanda contra la capacidad aproximada:
carril ≈ 1600 veh/h de verde efectivo con sigma 0.5; flujo por carril ≤
(verde/ciclo)·1600. Si el baseline colapsa (espera creciendo sin recuperarse),
el experimento no dice nada: bajar demanda o subir capacidad.

## 2. Baseline honesto (regla del proyecto)

El tiempo fijo NO debe ser un baseline débil. Probar varios tiempos de verde
(rebuild con netconvert + `baseline`) y quedarse con el mejor por la métrica
primaria, timeLoss promedio por vehículo (`timeloss_prom`). En `cruce` el barrido
fue 15–42 s y ganó 25 s, pero ese y los demás baselines (cruce2, corredor, red) se
eligieron por espera detenida antes de fijar esta regla: re-barrer por timeLoss
antes de citarlos en el documento. Dejar anotado en LEEME.txt qué valores se
probaron y cuál ganó.

Segundo control de referencia: el actuado nativo de SUMO (`tlLogic
type="actuated"` en `<esc>.add.xml`, con `minDur` y `maxDur` iguales al verde
mínimo y máximo del agente, 10 y 60 s). La tesis promete comparar contra fijo y
actuado, y en `cruce` el actuado gana al Q-learning; sin ese brazo la comparación
queda incompleta.

## 3. Entrenar y comparar

```
python rl_semaforo.py baseline --escenario <esc>
python rl_semaforo.py train    --escenario <esc> --episodios 40
python rl_semaforo.py demo     --escenario <esc>
python graficar.py <esc>
```
(Para escenarios de más de un semáforo: `rl_corredor.py` con los mismos modos.)

- Entrenamiento: semilla base 42; el episodio k usa la semilla 42 + k, así que un
  entrenamiento de N episodios ocupa 43..42+N.
- Evaluación (todo número que va al documento): semillas 1001–1010, fuera del
  rango de entrenamiento y las mismas para fijo, actuado y RL; reportar media,
  IC95 % y prueba pareada (Wilcoxon) o Mann–Whitney exacta, nunca una corrida
  suelta. Antes de la corrida que se va a citar, borrar `q_table_<esc>.json` y
  entrenar desde cero para que el bloque del CSV sea reproducible.
- Comparar primero timeloss_prom (primaria) y después espera_prom, cola, paradas,
  throughput y CO2 de `demo` contra `baseline` del MISMO escenario y mismas
  semillas; la mejora se reporta como porcentaje sobre el baseline tuneado.
- Si la curva no converge (espera oscilando fuerte tras ~30 episodios), revisar
  primero el tamaño del espacio de estados (bins × fases) antes de tocar α o γ.

## 4. Registrar

- Los resultados quedan en `resultados_<esc>.csv` (no borrarlo: es el historial).
- Actualizar la tabla de resultados de LEEME.txt con: configuración del baseline,
  episodios, semilla, espera y timeLoss de ambos controles y el porcentaje.
- La Q-table entrenada (`q_table_<esc>.json`) se conserva; `train` continúa desde
  ella si existe — borrar el archivo si se quiere entrenar desde cero.
- Llevar el resultado a `TESIS/secciones/` con el skill `escribir-tesis` en el
  mismo turno (tabla o figura en capitulo5, escenario en capitulo4). LEEME.txt es
  nota de trabajo, no registro: un número que solo está ahí no existe para la tesis.
