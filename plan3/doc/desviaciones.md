# Desviaciones del plan 3

Registro de todo lo que se apartó del prerregistro (parte A, tag `plan3-prerregistro-A`, sha256
`49c898d7670c8c3bbf382a366a8038a47c2562063cc8fd8c506c8615203b6134`). El informe final las repite (§11: "toda
desviación y toda enmienda con los datos que estaban a la vista").

## 1. Semillas del examen T1 en una revisión de código (05.11.2026, 12:20-13:00)

**Qué pasó.** Una revisión automática del script de veredicto (commit `13fd132`) quiso comprobar con SUMO cómo se
cuentan los cambios de fase. Corrió `evaluar3.py` en una copia aparte del repositorio con tres semillas del examen T1
regular: 8001, 8002 y 8003. Fue un error de la instrucción: no le dijo qué semillas usar.

**Qué se corrió.** Ningún modelo del plan 3 existía todavía y el fijo fino no se corrió.

| Escenarios | Brazos | Semillas |
|---|---|---|
| Las 32 plantillas | regla simple `regla_u3g60` | 8001 |
| Corredor, red y algunas `dem_` | regla simple, Max-Pressure `mp_c60`, IPPO entregada (base 42), fijo instalado, actuado por defecto, ciclo mínimo | 8001-8003 |

**Qué se vio.**
- El agente de la revisión leyó el número de cambios de fase de cada corrida (métrica secundaria).
- En dos líneas de su salida vio también el retraso total y el timeLoss de `regla_u3g60` en el corredor.
- El coordinador vio solo cambios de fase en el corredor: los de la regla simple, el fijo, el actuado y el ciclo mínimo,
  y la diferencia k (no el conteo) de la IPPO entregada. Fabian no vio ninguna cifra.
- Según las transcripciones de la revisión, nadie vio el retraso de ninguna IPPO ni del fijo.

**Por qué no cambia ninguna regla.**
- Las reglas ya estaban fijadas y subidas antes (tag de la parte A, 11:58 del mismo día).
- Son 3 de las 30 semillas de T1 y ninguna de T2.
- Los brazos que deciden las etiquetas (los modelos nuevos frente al fijo fino) no existían.

**Qué se hizo.**
- Los 86 archivos de esas corridas (54 CSV y 32 salidas de texto) se movieron sin abrirlos a una carpeta de cuarentena
  fuera del repositorio. Antes se anotaron su ruta, sha256, filas y semillas, leyendo solo la columna de semillas.
- Desde el 05.11, `comun.iniciar_sumo` y `barrer_fijo` se niegan a simular una semilla del examen o de la prueba final
  si el proceso no viene de un trabajo ciego de la cola (commits `682b6c2` y `3a547f7`).
- Toda prueba o revisión usa solo semillas de humo (424301-424360) o la base 7.
- La evidencia del conteo de cambios de fase se rehízo con semillas de humo (`pruebas/ver/salidas/prueba_k_humo.txt`).

**Pendiente:** Fabian decide si los archivos en cuarentena se borran sin abrir (recomendado) o se guardan.

## 2. Cambios de fase: corrección de un error de conteo (05.11.2026)

**Qué pasó.** `rl_ippo.py` cuenta un cambio de más por cada semáforo que la plantilla arranca fuera de su primer verde.
`rl_corredor.py` no lo cuenta. Por eso, en el corredor, los brazos que corren por `rl_ippo` (IPPO y reglas) sumaban 1
de más por episodio. En P6 entregado sumaban 4 de más.

**Qué se hizo.** `veredicto3.py` resta ese número (k, uno por plantilla) a esos brazos. La fila de cada comparación lo
dice. Es la corrección de un error de código hecha antes de cualquier evaluación decisiva; ningún dato decisivo estaba a
la vista. No toca la métrica principal ni ninguna etiqueta.
