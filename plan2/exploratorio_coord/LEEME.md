# Análisis exploratorio posterior: corrección del entrenamiento de IPPO vecinos (28.09.2026)

## Qué es

Material del análisis exploratorio hecho **después** del veredicto pre-registrado del 25.09. Pregunta: ¿por qué IPPO vecinos no mejora la coordinación en P4 (`red_alta`) y P6 (`malla3_alta`), y se arregla corrigiendo el entrenamiento?

- **Diagnóstico.** `gae()` descuenta por decisión y no por segundo. Además, la exploración es independiente por semáforo y rompe el ciclo común.
- **Variante V2 (`smdp_crn`).** Descuento γ^(dt/5) en GAE y exploración con un número aleatorio común para todos los semáforos que deciden en el mismo segundo.
- **Diseño.** Pre-registro propio (`PRERREGISTRO.md`, sha256 en `prerregistro.sha256`) con 5 variantes (V1-V5) y un control C0. Hay 3 bases, 200 episodios y validación con 8 semillas.
- **Semillas.** Cribado en 5001-5030 y confirmación en 6001-6030. Las semillas del examen (1001-1030) **no se simularon**: cada script tiene un `assert`.

**No forma parte del veredicto pre-registrado del 25.09 ni lo cambia.** Las cifras verificadas y su archivo fuente están en `HECHOS.md`.

## Contenido

| Carpeta o archivo | Qué contiene |
|---|---|
| `PRERREGISTRO.md`, `prerregistro.sha256` | Diseño fijado antes de entrenar (sha256 `8d38fe82…6b33`) |
| `DESVIACIONES.md` | Desviaciones D1-D11 (tanda 1) y T1-T7 (tanda 2), escritas antes de ver los resultados que afectan |
| `SINTESIS.md` | Síntesis del análisis. Se escribió antes de la confirmación de P6: la §3 y la §7 dicen "sin confirmación en semillas nuevas", y eso ya no vale (ver `conf_p6/`) |
| `diagnostico/` | Chequeos previos: `b1`-`b7` (ruido, desfases, reglas), `c2`-`c6` (escalas, alineación del objetivo, crítico). En `mejora_coord/` está el diagnóstico anterior: sensibilidad al canal y Max-Pressure |
| `tanda1/` | P4, cribado 5001-5030 de C0 y V1-V5: `juicio_tanda1.{txt,json}`, `seleccion_V*.json`, réplica de C0 e identidad V5/V3 |
| `tanda2/` | P4, confirmación 6001-6030 de V5; P6, cribado 5001-5030 de V2, V5 y C0; P1, no regresión de V5. Incluye `juicio_tanda2.{txt,json}`, `conteos_tanda2.txt` y `seleccion_*.json` |
| `conf_p6/` | P6, confirmación 6001-6030 de las 3 bases de V2 y V5 más las referencias: `juicio_conf_p6.{txt,json}`, scripts y CSV por semilla |
| `sintesis/` | `extra_robustez` (fijo re-barrido y retraso total) y `analizar_fases_p6` (qué programa aprendió cada política en P6, semilla 999) |
| `csv/` | CSV por semilla usados por `verificar_hechos.py` (P4 5001-5030 y 6001-6030, P6 5001-5030 y P1 5001-5030) |
| `codigo/` | `rl_ippo_smdp_crn.py` (V2) y `rl_ippo_norm_smdp_crn_triv.py` (V5), con sus diffs contra `rl_ippo.py` del repo. Ningún otro archivo de código cambia |
| `politicas/` | Las 4 políticas publicadas (`.pt` y `.json`): V2 P4 base 2042, V5 P4 base 42, V2 P6 base 4042 y V5 P6 base 42 |
| `verificar_hechos.py`, `verificar_hechos.txt` | Recalculan desde `csv/` y `conf_p6/salidas/` las cifras de `HECHOS.md` |

## Cómo se reproduce

1. **Cifras, sin simular.** Desde `demo_rl/`:
   `python plan2/exploratorio_coord/verificar_hechos.py > plan2/exploratorio_coord/verificar_hechos.txt`
   El script usa `evaluar.comparar` del repo: bootstrap pareado de 10 000 remuestreos y Wilcoxon.
2. **Entrenamiento de V2.** Hay que sustituir `rl_ippo.py` por `codigo/rl_ippo_smdp_crn.py` en una copia del repo, o aplicar `codigo/smdp_crn.diff`. Después, para cada base B en {42, 2042, 4042}:
   `python rl_ippo.py train --escenario red_alta --variante smdp_crn --episodios 200 --seed B --val-seeds 999,1999,2999,3999,4999,7999,8999,9999 --eval-cada 10`
   Para P6 se usa `--escenario malla3_alta --eval-cada 20`. La política publicada de cada base es el checkpoint con menor val8, y la base publicada sale de la misma regla de selección y convergencia del plan v2 (`tanda*/seleccion_*.json`).
3. **V5.** Es igual, con `codigo/rl_ippo_norm_smdp_crn_triv.py` y `--variante norm_smdp_crn_triv`.
4. **Evaluación.** Se usa `evaluar.brazo_profundo` con la política congelada (argmax) en 5001-5030 o 6001-6030. En `conf_p6/lanzador_conf_p6.py` está el ejemplo.

Versiones: SUMO 1.25.0, torch 2.14.0+cpu y Python 3.14.6. La demanda es determinista (`vehsPerHour`), así que las semillas solo cambian `sigma`.
