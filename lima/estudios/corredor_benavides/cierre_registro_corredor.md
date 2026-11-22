## Cierre del estudio 2 del corredor (20.11.2026) — BORRADOR, se agrega a lima/REGISTRO.md con el OK de Fabian

Notas de lo que pasó durante la corrida lanzada el 19.11.2026 a las 17:23:13 desde `corredor_estudio2/` (enmienda del
19.11.2026, 17:35). Ninguna cambia el código que corrió ni los datos de huellas.sha256.

**1. Faltaba `demo_rl/evaluar.py` en la copia (20.11.2026, 03:33).** `evaluar_nivel.sh publicada` se detuvo en el
veredicto: `estudio.comparar` importa `evaluar` (para el IC por bootstrap, `bootstrap_delta`) y ese archivo no se había
copiado a `corredor_estudio2/demo_rl/` (tampoco estaba en huellas.sha256). Lo anterior al veredicto ya había terminado
(las dos tandas de los tres entrenamientos del modelo completo, el canal cortado del citado y sus verdes). A las 03:35
se copió `demo_rl/evaluar.py` sin cambios desde el repo (main @53bdb48, sin cambios locales; sha256
44ed0b4742decb093344bc83e7f9462b729c72ca6062e688b19a65b865f01512) y `continuar_publicada.sh` corrió los pasos que
faltaban de la publicada con los mismos comandos y en el mismo orden que `evaluar_nivel.sh`: veredicto, robustez,
espera de los entrenamientos de los mensajes, sus tandas y el veredicto con los mensajes (registro en
`logs/evaluar_publicada_continuacion.log`; nota en `logs/lanzamiento.txt`). `evaluar_nivel.sh alta` no se tocó: llega
al veredicto con el archivo ya copiado.

**2. `tablas_corredor.py` se editó después del lanzamiento (20.11.2026, madrugada).** Solo el posproceso: el rótulo de
Casimiro Ulloa en la tabla de cruces (cruce en T), la cabecera de los archivos generados y un comentario de fuente. La
cadena del estudio no lo usa, así que su huella difiere de la de huellas.sha256 sin efecto en los resultados.

**3. Resultados.** Publicada: MEJORA. Alta: FUNCIONA.
- Publicada: modelo citado vecinos_completo_s42 (validación mediana: 39.105; las otras, 38.938 y 39.242). Frente al
  fijo ajustado -3.67 % [-4.00, -3.36] y -3.78 % [-4.27, -3.35]; frente al actuado ajustado -3.20 y -3.33 %: MEJORA en
  las dos tandas, veredicto citable MEJORA (`demo_rl/lima/corredor/salidas/veredicto_vecinos_completo_s42.md`).
- Publicada, robustez del reparto (100 semillas, 24001-24100; controles de la publicada sin reajustar ni reentrenar):
  más carga en la avenida, modelo frente al fijo -4.22 % [-4.76, -3.71] y frente al actuado ajustado -2.89 %; más
  carga en las transversales, -14.34 % [-15.53, -13.23] y -13.85 %.
- Publicada, mensajes: IPPO con mensajes corregido (vecinos_corregido_s42) frente a IPPO sin mensajes corregido
  (local_sinmsg_s4042), -4.76 % [-5.05, -4.47] y -4.77 % [-5.08, -4.47]; modelo completo frente a su canal cortado,
  -4.43 y -4.24 %; con el canal cortado, el modelo queda +0.79 y +0.47 % frente al fijo. Los nueve entrenamientos de la
  publicada se estabilizaron. FIN de la evaluación de la publicada: 20.11.2026, 05:03.
- Alta: referencias listas a las 06:39 (fijo de ciclo 84 s, 60.63 s/veh con 30 semillas; actuado de SUMO coordinado
  "fin fijo", hueco 1.25 s, verdes máximos de 60 s, 61.04; sin coordinar, 68.81). Modelo citado vecinos_completo_s4042
  (validación mediana: 53.125; las otras, 52.962 y 54.002). Frente al fijo ajustado -7.71 % [-8.31, -7.14] y -7.59 %
  [-8.16, -6.99]; frente al actuado ajustado -8.01 y -7.61 %: FUNCIONA en las dos tandas, veredicto citable FUNCIONA
  (`demo_rl/lima/corredor/alta/salidas/veredicto_vecinos_completo_s4042.md`, 20.11.2026, 08:41). El actuado ajustado
  frente al fijo: +0.32 y +0.02 %. Canal cortado: el modelo frente a su canal cortado -8.45 y -7.89 %; con el canal
  cortado, +0.80 y +0.32 % frente al fijo. Los tres entrenamientos del modelo completo se estabilizaron.
- Alta, mensajes: IPPO con mensajes corregido (vecinos_corregido_s42) frente a IPPO sin mensajes corregido
  (local_sinmsg_s2042), -12.44 % [-13.16, -11.71] y -13.18 % [-14.25, -12.03]; los tres entrenamientos de IPPO con
  mensajes corregido sin estabilizar (seguían bajando), dos de los tres de IPPO sin mensajes corregido estables.
  IPPO con mensajes corregido frente al fijo: +11.59 y +11.67 %. FIN de la evaluación de la alta y de todo el estudio:
  20.11.2026, 09:58 (`logs/lanzamiento.txt`, "Todo terminado").
