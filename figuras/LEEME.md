# Programas de las tablas y figuras de los casos de Lima en la tesis

Arman las tablas y figuras de los casos de Lima que usa la tesis, a partir de lo que ya escribieron los dos estudios.
No corren ninguna simulación. Buscan las copias de trabajo de los estudios junto al repositorio, con los nombres
`nudo_ovalo_estudio2/` y `corredor_estudio2/` (cómo armarlas: `lima/estudios/LEEME.md`).

| Programa | Qué escribe |
|---|---|
| `tablas_nudo_fijo.py DESTINO` | tablas del nudo con el modelo de orden fijo (el del resultado central): resultado, todos los controles, entrenamientos y robustez |
| `entrenamientos_nudo.py DESTINO` | cambio de cada entrenamiento del nudo frente a las referencias, por tanda, en texto |
| `figuras_ovalo_tesis.py DESTINO` | figuras del nudo: curvas de aprendizaje (`fig_ovalo_aprendizaje`) y ciclo (`fig_ovalo_ciclo`) |
| `secuencia_ovalo_tesis.py DESTINO` | secuencia de luces de los dos modelos del nudo |
| `ic95_lima.py nudo\|corredor DESTINO` | cambio del modelo citado frente a cada referencia, con su IC95, en las dos tandas y las dos demandas |
| `resultado_final_ovalo.py DESTINO` | tabla y figura del resultado central: los casos del segundo estudio con los dos de Lima |
| `costo_escala_corredor2.py` | `costo/costo_escala.py` con el corredor de Lima: cómputo, rentabilidad y separación entre cruces (`salida/costo_escala_corredor2.json`) |
| `red_corredor.py` | la red de SUMO del corredor (`TESIS/images/fig_corredor_red`) |
| `satelite_ovalo.py`, `satelite_corredor.py` | vista satelital junto a la red de SUMO (`TESIS/images/fig_*_satelite`) |

`satelite_ovalo.py` y `satelite_corredor.py` necesitan las capturas de Google Maps de `figuras/capturas/`, que no se
suben al repositorio: son de Google y se usan en la tesis con su atribución. Las figuras que resultan están en
`TESIS/images/`.

Las tablas de la tesis llevan, además, líneas entre filas agregadas a mano en `TESIS/secciones/tablas/`: al volver a
generarlas se pierden. Por eso los programas que aceptan `DESTINO` conviene correrlos con una carpeta aparte.
