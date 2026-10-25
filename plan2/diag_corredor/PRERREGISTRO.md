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
