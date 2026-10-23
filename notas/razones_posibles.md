# Razones posibles de por qué el modelo cae en algunos casos

**Estas hipótesis no van a la tesis hasta confirmarse.**

Salieron en la reunión con el profesor (pedido de cambios para la entrega 3, punto 7). Él pidió primero
confirmar la tendencia y después buscar la razón, así que aquí solo se anotan, con las palabras con que
salieron, y se dice qué corrida o qué dato permitiría ponerlas a prueba. Escrito el 22.10.2026.

Lo que se quiere explicar (Tabla 5.3, `tab:resultado-principal`): en la red con rotonda, la mejora de
IPPO con mensajes frente al fijo ajustado pasa de −8.8 % (P3) a −3.6 % (P4) al subir la demanda, y en la
malla no hay mejora (P5: +1.8 %, empata; P6: +2.2 %, veredicto pendiente, empate provisional). Con dos
puntos por red todavía no hay una tendencia que explicar. Por eso casi todas las pruebas de abajo usan
las curvas de demanda nuevas (niveles fijados en `ajustes.md` de la entrega 3; sus resultados irán a
`plan2/demanda2/`, que hoy no existe).

## 1. La rotonda no se controla con semáforos, así que el modelo no puede actuar sobre esa parte de la red.

Estado: sin confirmar.

Cómo ponerla a prueba: con la curva nueva de la red con rotonda (905, 1358, 1810, 2715 y 3620 veh/h, más P3 y P4), comparar el cambio frente al fijo con el del corredor en los niveles comunes y ver si empeora con la demanda y, si empeora, si es recién cuando la rotonda se satura (desde ×1.3, unos 2795 veh/h: el nivel de 3620 veh/h, ×1.68, queda por encima, y el de 2715, ×1.26, justo por debajo) o antes; una evaluación de P3 y P4 con la salida por arista de SUMO (`--edgedata-output`, que da el `timeLoss` de cada arista) diría además cuánto retraso de cada control se pierde en las aristas de la rotonda.

## 2. En una red más compleja el control fijo también rinde peor, lo que cambia la base de comparación; aun así el modelo podría mejorarlo.

Estado: sin confirmar.

Cómo ponerla a prueba: en los niveles comunes a las tres redes (1810, 2715 y 3620 veh/h), comparar el retraso del fijo ajustado en s/veh entre las redes, junto al del actuado, el del ciclo mínimo y el de IPPO con mensajes, y no solo los porcentajes, sin olvidar que con el mismo total la carga por calle es distinta en cada red (`tab:demanda-flujos`).

## 3. Con muy poca demanda hay poco margen para que el modelo mejore.

Estado: sin confirmar.

Cómo ponerla a prueba: en los niveles nuevos que quedan por debajo de la demanda nominal de cada red (corredor 905 y 1358; red con rotonda 905, 1358 y 1810; malla 1810, 2715 y 3620 veh/h), con IPPO con mensajes reentrenado en cada nivel, mirar el retraso del fijo (el margen que hay) junto al cambio del modelo; el barrido que ya está en `plan2/demanda/` (corredor ×0.5 y ×0.75) no sirve para esto, porque evalúa las políticas de P1 y P2 sin reentrenarlas.

## 4. La coordinación de semáforos en U4 podría aportar variación.

Estado: sin confirmar.

Cómo ponerla a prueba: comparar cuánto cambia el resultado entre los 3 entrenamientos de IPPO con mensajes y de IPPO sin mensajes, que solo difieren en los mensajes (columna "rango entre bases" de `TESIS/secciones/tablas/veredicto_bases.tex`), y entrenar más bases de los dos modelos en algunos casos para que la comparación sea firme; en la evaluación los mensajes llegan al instante y sin pérdida, así que un canal imperfecto solo se probó en la fase exploratoria (Anexo C, latencia y pérdida de mensajes).

---

Cuando una hipótesis se confirme, pasa a la tesis con su dato y su fuente. Mientras tanto, la tesis solo
usa las explicaciones que ya tiene. Los rangos entre entrenamientos de IPPO con y sin mensajes de las
tablas actuales están copiados en `notas/precision.md`, punto 4.
