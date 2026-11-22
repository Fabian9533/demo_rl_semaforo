### Cierre del estudio del nudo en la red del Óvalo Vasco con los carriles corregidos (19.11.2026, 09:10)

Lo que se corrió, en el orden y con los comandos de la enmienda del 18.11.2026 (23:45) y de
`nudo_ovalo_estudio2/pruebas/correccion_carriles/CIERRE.md`, sección 6.

**Horas.** Lanzamiento el 18.11 a las 23:45. Referencias ajustadas: demanda publicada a las 01:34 del 19.11, alta a
las 06:06. Entrenamientos: los 6 de orden fijo a las 06:01 y los 6 de orden libre a las 07:25 (400 episodios cada
uno). Evaluación completa a las 08:48. A las 08:50 los 73 archivos de `huellas.sha256` daban el mismo sha256 que al
lanzar. En los 6 entrenamientos de orden libre, `tope_excedido` quedó en 0.

**Incidentes de operación.** Ninguno cambia un número: cada semilla se simula igual en cualquier proceso, y lo ya
evaluado no se repite.

1. A las 05:41 se cortó `evaluar_ovalo.py modelos --nivel publicada`. Dos simulaciones tomaron el mismo puerto de
   TraCI: una se conectó al SUMO de la otra y, al terminar, no encontró su archivo de viajes. Se detuvo con error y
   sin escribir resultado. A las 05:43 se volvió a lanzar el mismo paso, y después la robustez. Durante la tanda 2 de
   los modelos citados de la alta hubo otro choque de puertos, que SUMO resolvió solo, sin corte. En los registros de
   los 12 entrenamientos no hay ninguno.
2. El paso `evaluar_ovalo.py referencias --nivel alta` empezó a las 06:07 con 4 procesos. Antes, a las 06:09, la
   tanda 2 del ciclo mínimo se lanzó en paralelo con el mismo comando que usa ese paso
   (`estudio.py evaluar --tanda T --brazos B`), en núcleos libres. Ya evaluadas las tres referencias principales, el
   paso se cortó a las 07:24. Las secundarias que faltaban se corrieron con ese mismo comando en procesos paralelos
   (actuado por defecto, ciclo mínimo y actuado ajustado de antes de la comprobación del borde, en las dos tandas). A
   las 08:49 se volvió a correr el paso completo, que encontró todo evaluado.
3. Los verdes del modelo de orden fijo (`estudio.py verdes-modelo`, bases citadas 2042 y 4042) y la figura de la
   secuencia (`figura_secuencia.py`) se corrieron en cuanto existían sus políticas, antes de terminar la
   evaluación: no dependen de otros resultados.

**Resultado** (`salidas_ovalo/veredicto_ovalo.md` y `.json`; tablas y figuras de `tablas_ovalo.py` en
`salidas_ovalo/tesis/`):

| | Demanda publicada | Demanda alta |
|---|---|---|
| Modelo de orden libre (citado) frente al fijo ajustado | MEJORA: −3.43 y −3.64 % (base 42) | FALLA: +55.02 y +55.11 % (base 2042, sin estabilizar) |
| Libre frente al modelo de orden fijo | FALLA: +6.32 y +6.31 %, se distingue de la variación entre entrenamientos (provisional) | FALLA: +51.31 y +50.27 %, se distingue (provisional) |
| Modelo de orden fijo frente al fijo ajustado | FUNCIONA: −9.17 y −9.36 %, empata con el actuado ajustado (base 2042, provisional) | FALLA: +2.45 y +3.22 %; −4.50 y −7.75 % frente al actuado ajustado (base 4042) |
| Libre frente al plan actual | −18.33 y −19.14 % | −23.60 y −25.49 % |

Límites que la regla manda decir con la demanda alta: el fijo ajustado [60, 25, 77] da verdes de más de 60 s, que
el actuado ajustado y los modelos no pueden dar; el actuado ajustado (por retraso, alcance de 100 m, retraso mínimo
de 5 s) quedó otra vez en el borde tras la comprobación del borde. Robustez del reparto, demanda publicada: el modelo
libre tiene 25.9 y 35.3 % menos retraso que el fijo ajustado, y 4.0 y 13.3 % más que el actuado ajustado.

En la hora de la figura de la secuencia (semilla de validación 21001), el modelo libre usó el paso de 28 de Julio y
Balboa a los giros (el defecto declarado en la enmienda) 1 vez con la demanda publicada y ninguna con la alta.
