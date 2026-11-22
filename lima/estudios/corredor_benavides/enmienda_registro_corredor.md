## Enmienda: estudio 2 del corredor de la Av. Benavides, con la red corregida y los verdes mínimos de los peatones (19.11.2026, 17:35)

Se registra antes de ajustar las referencias, de entrenar y de evaluar en la red corregida. Para el corredor reemplaza la
red, la demanda, los verdes mínimos, las partidas de la búsqueda del fijo y los pasos del actuado registrados el
13.11.2026 (22:40) y el 14.11.2026 (03:00, 03:25, 04:05, 05:40, 05:50 y 15:55). Los controles, los tres modelos y sus
opciones, las bases, las semillas, la métrica, las comparaciones, la regla del veredicto, la prueba del canal cortado y
la prueba de robustez siguen como quedaron registrados. Corre en una carpeta aparte, `corredor_estudio2/` (copia del
código del estudio de `demo_rl/` en el commit 53bdb48, con los cambios de abajo); `demo_rl/lima/corredor/` queda como
está. La tesis informa solo este estudio.

**Por qué.** La revisión del corredor del 19.11.2026 (`revision_corredor_2026-11-19/`, cuatro informes) comparó la red
con OpenStreetMap del corredor entero, bajado ese día, y encontró dos errores: la Av. Casimiro Ulloa (C5) llega a la
avenida solo desde el norte (el cruce es en T) y la red tenía una rama sur que no existe, por la que entraban 500 veh/h
y salían 475; y la avenida llega a Larco desde el oeste con 2 carriles por sentido, no 3. Encontró además que el
modelo daba a las transversales verdes de 10 a 12 s, que no dejan cruzar la Benavides a un peatón (16 a 19 s a 1.2
m/s). Fabian Alvarado decidió (19.11.2026, hacia las 17:00) corregir la red, poner verdes mínimos para los peatones y
volver a correr el estudio del corredor.

**Qué se sabía al registrar.** Los resultados del estudio anterior del corredor (FUNCIONA con las dos demandas: −8.8 y
−8.9 % frente al fijo ajustado al segundo con la publicada, −19.9 % con la alta) y las pruebas de la revisión en la red
anterior, todas con semillas de prueba: con verdes mínimos de peatones como cota baja y el modelo sin reentrenar, −3.1 %
(publicada) y −16.7 % (alta); con 2 carriles al oeste de Larco, −6.5 %; con la alta, un fijo de 80 s con onda verde en
los dos sentidos tenía un 8.8 % menos de retraso que el fijo ajustado de 62 s; con la publicada, un actuado con hueco
de 1.25 s y verdes máximos de 35 y 25 s, un 1 % menos que el actuado ajustado. Por eso se agregan las partidas y los
pasos de abajo. En la red corregida solo se usaron la base 7 (dos episodios, semillas 8 y 9 de SUMO) y las semillas de
prueba 424331, 424332 y 424340; ninguna semilla de ajuste (2001-2030), de validación (21001-21004), de evaluación
(22001-22100 y 23001-23100) ni de robustez (24001-24100), y ninguna de las bases 42, 2042 y 4042.

**La red** (`corredor.py`).
- C5, Av. Casimiro Ulloa: cruce en T. La transversal llega solo desde el norte, de doble sentido, con 2 carriles por
  sentido. Lo que baja gira a la derecha, hacia el oeste, por el carril derecho, o a la izquierda, hacia el este, por
  el izquierdo. Desde la avenida, yendo al oeste, se gira a la derecha hacia Casimiro Ulloa; yendo al este no hay giro
  (como en el resto, no hay giros a la izquierda desde la avenida). Al sur queda, como en las calles de un sentido, un
  tramo de un carril sin demanda, para que el modelo describa cada cruce con cuatro accesos.
- Avenida al oeste de Larco: 2 carriles por sentido. Hacia el oeste llegan 3 carriles a Larco y siguen 2: el derecho
  solo gira hacia Larco (la regla que ya se usaba en Paseo de la República).
- Lo demás no cambia. En los seis cruces ningún par de movimientos con verde está en conflicto según la red.

**La demanda.** La misma regla: en los tres cruces con volumen publicado, la transversal se elige para llegar a él; en
los otros tres, se supone por sus carriles y no cambia.
- Casimiro Ulloa: 500 veh/h, la mitad gira al oeste y la mitad al este (supuesto).
- Larco 934 veh/h (antes 1050), Paseo de la República 612 por sentido (719) y República de Panamá 898 por sentido
  (1009). Los tres cruces quedan en 3390, 3779 y 4358 veh/h (publicado: 3390, 3778 y 4358).
- Entran 7654 veh/h (antes 8706). La alta es la misma por 1.2: 9185 veh/h. La robustez, el mismo total de la publicada
  con el reparto cambiado como se registró el 14.11.2026 a las 03:25.

**Verdes mínimos de los peatones.** Cada verde dura al menos lo que necesita un peatón que empieza a cruzar con el verde
para llegar al otro lado antes de que termine el ámbar: 3.2 s para empezar más el ancho a 1.2 m/s (Highway Capacity
Manual 2000), menos los 3 s del ámbar, redondeado hacia arriba y nunca menos de 10 s. Con el verde de la transversal se
cruza la avenida; con el de la avenida, la transversal. Anchos de OSM: 3.3 m por carril más el separador central de la
avenida; en Larco, el lado este; en Paseo de la República, el cruce oeste del puente.

| Cruce | Ancho que se cruza con el verde de la avenida / de la transversal (m) | Verde mínimo de la avenida / de la transversal (s) |
|---|---|---|
| C1 Larco | 9.9 / 19.8 | 10 / 17 |
| C2 Alcanfores | 6.6 / 20.9 | 10 / 18 |
| C3 La Paz | 6.6 / 22.8 | 10 / 20 |
| C4 Paseo de la República | 13.2 / 22.0 | 12 / 19 |
| C5 Casimiro Ulloa | 13.2 / 20.7 | 12 / 18 |
| C6 República de Panamá | 13.2 / 19.7 | 12 / 17 |

Valen para todos los controles: el plan típico (ya los cumple), el fijo ajustado, el actuado, el actuado ajustado y sus
variantes coordinadas (verde mínimo de cada estado), el ciclo mínimo (ciclo común de 37 s, cada transversal en su
mínimo) y el modelo, que no puede cambiar de estado antes del mínimo del suyo (`escenarios_lima.py`, `verde_min_tls`, y
`rl_ippo.py`). Sin todo rojo, como antes. Comprobado en la red corregida (base 7, semilla 424332): el modelo no baja de
esos mínimos en ningún cruce.

**Referencias** (`estudio_corredor.py`).
- Fijo ajustado: la misma búsqueda (descenso por coordenadas con pasos de 8, 4, 2 y 1 s; 10 semillas por candidato,
  2001-2010; los diez mejores con 30, 2001-2030), con otras partidas: el plan típico y, en ciclos de 40, 44, 48, 52,
  56, 60, 66, 72, 80, 90 y 100 s, el reparto de Webster con los mínimos de los peatones, sin desfases y con onda verde
  hacia el este, hacia el oeste y en los dos sentidos. Se afinan las tres mejores partidas de ciclos distintos, y al
  mover el ciclo se prueba también con los desfases movidos junto con él.
- Actuado ajustado: los mismos pasos, con los huecos de 0.75 y 1.25 s y tres esquemas más de verdes máximos (avenida /
  transversal: 30/20, 35/25 y 45/35 s).

**Modelos, semillas, evaluación y veredicto.** Sin cambios: el modelo completo (400 episodios, decide cada 2 s) e IPPO
con y sin mensajes corregido (200 episodios), tres entrenamientos de cada uno (bases 42, 2042 y 4042); validación en
21001-21004 por retraso total; se cita la base con la validación mediana; tandas 22001-22100 y 23001-23100; canal
cortado del modelo citado; robustez en 24001-24100 con el plan típico, el fijo y el actuado ajustados de la publicada y
el modelo citado; la misma regla del veredicto para cada nivel.

**Código y huellas.** `corredor_estudio2/huellas.sha256` (sha256 17405a9ff54921b2af672f9401d425ee4bacef52432231246ceb1d27c1228010)
lista los 63 archivos de código y datos; `lanzar.sh` no corre si alguno cambió. Huellas de los datos (16 primeros
caracteres): red `benavides.net.xml` 29713c5f7a161b22; plan típico `benavides.add.xml` 9fd252f33b567ba1; demanda
publicada ccfb40f845572017 y alta d88fbd3f8ff10bf4; robustez, más carga en la avenida 38bc1bcdaacd1188 y más carga en
las transversales 93aed5c043fe1f91.

**Cuándo y en qué orden.** Se lanza a continuación desde `corredor_estudio2/` (`bash lanzar.sh`; la hora queda en
`logs/lanzamiento.txt`): los 6 entrenamientos del modelo completo y, al lado, las referencias de las dos demandas con
sus tandas; cuando terminan las referencias de una demanda, sus 6 entrenamientos de los mensajes; cuando terminan los
entrenamientos, las tandas de los modelos, el canal cortado, los verdes del modelo, la robustez y el veredicto
(`evaluar_nivel.sh`). Estimado, sin medirlo: el modelo completo de la publicada hacia la medianoche y el de la alta el
viernes 20.11 en la mañana.

**Nota sobre la hora (19.11.2026, 17:25).** El título de esta enmienda dice 17:35, que era la hora estimada de
lanzamiento. La enmienda se escribió a las 17:22 y el estudio se lanzó a las 17:23:13 (`logs/lanzamiento.txt`).
