# Prerregistro: diagnóstico de la curva del corredor (25.10.2026, 13:05)

Escrito antes de implementar las correcciones y de entrenar. Es un análisis posterior al veredicto, como el
diagnóstico del Anexo G: no cambia ningún veredicto del plan ni de los niveles de demanda.

## Pregunta

En el corredor, el cambio de IPPO con mensajes frente al fijo ajustado no sigue una tendencia con la demanda
(905: −5.6 % FUNCIONA; 1358: +5.4 % FALLA; 1810, P1: −6.8 %; 2715: +6.6 % FALLA; 3620, P2: −23.3 %). ¿Es un
problema del modelo, de la comparación o de SUMO, y se corrige?

## Lo que ya muestran los datos existentes (diag_corredor.py, 25.10 12:50, sin simular)

- 905: el fijo de la regla del 25.09 (malla desde 12 s) no incluye el ciclo corto; contra el fijo ajustado desde
  10 s (aquí igual al ciclo mínimo) IPPO queda en +0.1 %. Es un efecto de la referencia.
- 1358: el fijo es un ciclo corto (12/10 s) con ambas reglas; IPPO cambia de fase 373 veces por hora frente a 527 del
  fijo y queda +5.4 % frente al fijo y +1.7 % frente al ciclo mínimo.
- 2715 y 3620: la espera para entrar a la red de IPPO es 18.4 frente a 3.1 s/veh (2715) y 282 frente a 240 s/veh
  (3620). Con el retraso total, IPPO queda +32.9 % y +1.6 % frente al fijo.

## Hipótesis y predicciones

H1 (referencia). Ya mostrada; solo se reporta. En las comparaciones de este análisis la referencia principal es el
fijo ajustado desde 10 s y la métrica principal, el retraso total (timeLoss + espera para entrar).

H2 (recompensa). La recompensa de IPPO solo mide el retraso dentro de la red y no ve a los vehículos que esperan para
entrar; cerca de la saturación la política deja que la entrada se llene. Corrección INS: sumar a la recompensa de
cada agente, por segundo, el número de vehículos que esperan para entrar por las aristas de entrada de sus accesos,
con el mismo peso que un vehículo detenido. Predicciones: en 2715 y en 3620, IPPO con INS tiene (a) menos espera para
entrar que la versión evaluada actual (IC95 bootstrap pareado del cambio entero bajo cero) y (b) menos retraso total
que la versión actual (ídem).

H3 (objetivo de entrenamiento). El descuento por decisión y la exploración independiente favorecen verdes largos
(diagnóstico del Anexo G). Corrección V2 del Anexo G: descuento por segundo y exploración común. Predicciones: en
1358, IPPO con V2 tiene (a) más cambios de fase por hora que la versión actual (IC del cambio entero sobre cero) y
(b) menos timeLoss que la versión actual (IC entero bajo cero).

H4 (sin regresión). En P1, IPPO con V2+INS sigue reduciendo el retraso total frente al fijo ajustado desde 10 s
(IC entero bajo cero).

Criterio de causa raíz corregida (variante V2+INS, retraso total frente al fijo ajustado desde 10 s): ningún nivel del
corredor queda peor que el fijo con IC entero sobre cero y p de Wilcoxon < 0.05, y P1 sigue mejorando. Si no se
cumple, se reporta lo que sí se corrigió y lo que queda abierto.

## Diseño

- Variantes: V2 (descuento por segundo + exploración común), INS (recompensa con espera para entrar) y V2+INS.
  Observación, red neuronal, hiperparámetros, red, demanda y protocolo, sin cambios.
- Niveles del corredor: 905, 1358, 1810 (P1, escenario corredor), 2715 y 3620 (P2, escenario corredor_alta).
- Protocolo del plan: 3 entrenamientos (bases 42, 2042, 4042; episodio k con semilla base + k), 200 episodios,
  validación cada 10 episodios con 999 y 1999, versión evaluada = entrenamiento mediano por la validación.
- Evaluación: semillas 1001-1030 (comparables con la curva) y confirmación con 6001-6030 (nunca usadas en este
  diseño), para las variantes nuevas, la versión evaluada actual, el fijo de la regla del 25.09, el fijo ajustado desde
  10 s, el ciclo mínimo y el actuado.
- Comprobaciones de SUMO: teletransportes, sensibilidad del fijo y del ciclo mínimo al paso de 0.5 s, determinismo.

## Enmienda 1 (25.10.2026, 13:35, antes de lanzar los entrenamientos)

Criterio de validación de las variantes nuevas. El protocolo del plan elige el checkpoint publicado y la base mediana
por el timeLoss medio en 999 y 1999. Ese es justo el criterio que no ve a los vehículos que esperan para entrar: con
él, la selección de INS favorecería al checkpoint que menos atiende las entradas, en contra de H2 y de la métrica
principal de este análisis. Por eso:

- V2, INS y V2+INS eligen el checkpoint publicado y la base mediana por el retraso total medio en 999 y 1999
  (rl_ippo.py --criterio-val total; val_elegido queda en esa métrica). Las tres usan el mismo criterio, para que entre
  ellas solo cambie el entrenamiento.
- La validación registra las dos métricas en todos los casos (val y val_total en el CSV; val_serie y val_total_serie
  en el meta) y el meta guarda el episodio que habría elegido cada criterio (ep_elegido_timeloss y ep_elegido_total).
- La versión evaluada actual se eligió por timeLoss y no se vuelve a elegir. En las comparaciones con ella, el cambio
  incluye el del criterio. En 905, 1358 y P1 la espera para entrar es de 0.4-0.6 s y casi igual en todos los
  controles, así que ahí el efecto es pequeño. En 2715 y P2 se informa, por variante y base, si los dos criterios
  eligen el mismo episodio.

## Enmienda 2 (25.10.2026, 16:30): segunda ronda, escrita con los resultados de la primera a la vista

Esta es una prueba nueva, no una repetición de H2. Se escribe y se registra en git antes de entrenar la variante
nueva. Se informa pase o no pase.

**Resultado de la primera ronda** (`pruebas.txt`, semillas 1001-1030 y 6001-6030): H3 y H4 pasan; H2 y el criterio
no pasan. En 2715 y P2, INS y V2+INS dejan más espera para entrar que la versión actual. V2 sola no corrige 2715.

**Por qué falló INS** (registros de entrenamiento, sin simular de nuevo):

- Lo que INS cobra no está en la observación. La cola de cada acceso entra como detenidos/plazas recortado a 1, así
  que un acceso lleno se ve igual con 0 que con 50 vehículos esperando afuera.
- El crítico no puede predecirlo. En los episodios 181-200, la pérdida de valor es 3.5-4.6 (INS) y 2.8-4.4
  (V2+INS) frente a 0.17-0.21 (V2) en 2715, unas 20 veces más. En P2 es 64-75 y 31-87 frente a 0.27-0.28, unas 250
  veces más.
- El término pesa más que el resto de la recompensa: por decisión, −35 a −43 con INS frente a −22 con V2 en 2715,
  y −183 a −209 frente a −51 a −54 en P2.

**H5 (observabilidad).** INS falló porque el agente no ve lo que se le cobra. Corrección V2+INS+obs: V2+INS más
cuatro entradas al final de la observación, una por acceso. Cada una vale n/(n + plazas del acceso), donde n es el
número de vehículos que esperan para entrar por esa arista (`rl_ippo.py --obs-insercion`). Lo demás no cambia
respecto de V2+INS: recompensa y pesos, red, hiperparámetros, criterio de validación por retraso total, bases 42,
2042 y 4042, 200 episodios, cinco niveles, evaluación en 1001-1030 y confirmación en 6001-6030.

**Predicciones** (mismas pruebas que antes: cambio pareado, IC95 bootstrap pareado, p de Wilcoxon):

- (a) En 2715 y en P2, V2+INS+obs tiene menos espera para entrar y menos retraso total que V2+INS (IC entero bajo
  cero en las cuatro comparaciones).
- (b) Criterio de causa raíz corregida, el mismo de arriba, aplicado a V2+INS+obs: ningún nivel queda peor que el
  fijo ajustado desde 10 s en retraso total (IC entero sobre cero y p < 0.05), y P1 sigue mejorando (IC entero bajo
  cero).
- Comprobación descriptiva, sin prueba: la pérdida de valor media de los episodios 181-200 de V2+INS+obs es menor
  que la de V2+INS en 2715 y P2.

**Lectura.**

- Si (a) y (b) se cumplen, la causa de 2715 es la recompensa que no ve la entrada más la falta de esa información
  en la observación.
- Si (a) se cumple y (b) no, la observabilidad explica la falla de INS pero no basta para 2715.
- Si (a) no se cumple, H5 no se sostiene y la causa de 2715 sigue abierta.
