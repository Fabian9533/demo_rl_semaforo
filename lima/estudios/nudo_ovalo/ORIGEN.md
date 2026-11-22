# De dónde sale esta carpeta

`nudo_ovalo_estudio2/` es la carpeta del estudio del nudo en el Óvalo Vasco **con los carriles corregidos**. Se creó el
miércoles 18.11.2026 a las 18:14 como copia de `C:/Users/GAMER/Documents/demo_rl_semaforo/nudo_ovalo_estudio/`, la
carpeta del estudio lanzado ese día a las 11:03 y detenido a las 17:39 porque los carriles de las dos entradas de
Reducto estaban mal en la red y faltaba un giro de Balboa. La carpeta original no se tocó: queda como registro de la
corrida detenida (sus 71 huellas siguen coincidiendo después de la copia).

## Cómo se copió

Con `pruebas/correccion_carriles/copiar_estudio.py` (el inventario completo, archivo por archivo, está en
`pruebas/correccion_carriles/copia_inventario.json`). Se copiaron 117 archivos (1.3 MB), byte a byte y con su fecha;
cada copia se comprobó con sha256 contra su original. Antes de cambiar nada, las 71 huellas de `huellas.sha256` del
estudio detenido coincidían en la copia.

## Qué se dejó fuera

Todo lo que produjo la corrida detenida o las pruebas de la red anterior: 1459 archivos.

| Qué | Archivos | MB |
|---|---|---|
| `logs/` de la corrida (queda la carpeta vacía) | 20 | 0.5 |
| Políticas: `politica_*.pt` y su `.json` | 12 | 0.5 |
| `checkpoints/` (publicada y alta) | 432 | 15.4 |
| `resultados_*.csv` de los entrenamientos | 12 | 1.3 |
| `tripinfo_*` | 48 | 66.6 |
| `salidas/` de ajuste y de evaluación (`fijo_ajustado.json`, `actuado_ajustado.json`, `borde_actuado.json`, `val_referencias.json`, `eval_*.csv`) | 10 | 0.1 |
| Programas ajustados que escribió `referencias.sh`: `lima_fijo.add.xml`, `lima_minimo.add.xml`, `lima_actuado.add.xml`, `lima_actuadoaj.add.xml` | 7 | 0.0 |
| `tmp/` (no había `ver/`) | 11 | 6.7 |
| Salidas de `pruebas/` (de cada prueba queda solo su programa) | 761 | 204.9 |
| Datos de prueba de `revision/`: `prueba_parche/`, `prueba_veredicto/` y `tmp/` (políticas, resultados, salidas y programas de la red anterior) | 133 | 0.2 |
| `__pycache__/` | 13 | 0.6 |

Después de la copia no queda en la carpeta ningún `.pt`, `politica_*.json`, `resultados_*.csv`, `tripinfo_*`,
`checkpoints/`, `salidas/`, `tmp/`, `ver/` ni programa ajustado (comprobado con `find`).

## Qué se conservó

- El código y los lanzadores: `entrenar.sh`, `referencias.sh`, `evaluar_ovalo.py`, `tablas_ovalo.py`,
  `figura_secuencia.py`, `ver_ovalo.py`, `vista_ovalo.xml`, `comprobar_fases.py`, `comprobar_referencias.py` y todo
  `demo_rl/` (los `.py`, `lima/ovalo/` con sus entradas y su red, y los datos de las cuatro carpetas de trabajo).
- `LEEME.md`, `enmienda_registro.md`, `huellas.sha256` y `archivos_huellas.txt`.
- Los programas de las pruebas: `pruebas/equivalencia/equivalencia.py`, `pruebas/escritor/comparar_revision.py`,
  `pruebas/humo/{correr_plan,demos,diagnostico_actuado,modelo,referencias}.py` y
  `pruebas/lanzadores/{probar,probar_verdes}.py`. `pruebas/guardas/` no tenía programa (se hizo a mano) y no se copió.
- `revision/`: sus programas, los parches (`parche_*.diff` y `parches/`), sus salidas de texto (`*.out`) y
  `huellas_antes_de_parches.sha256`.

## Ojo: qué sigue siendo de la corrida detenida

- **`LEEME.md` y `enmienda_registro.md` son los del estudio detenido.** Describen la red anterior (4 y 5 carriles, 12
  movimientos, 53 enlaces, 224 y 512 s/veh). Hay que escribirlos de nuevo antes de lanzar.
- **`huellas.sha256` es la del estudio detenido.** Después de la corrección ya no coinciden 34 de sus 71 archivos, así
  que ningún lanzador corre hasta que se rehaga (`sha256sum $(cat archivos_huellas.txt) > huellas.sha256`). Es a
  propósito: nada se puede lanzar por descuido con la carpeta a medio preparar.
- `demo_rl/lima/ovalo/entrada/e2_lima_75_estudio.add.xml` y `entrada/plan_actual_revision.add.xml` son referencias
  de la red anterior. Ya no las usa ningún programa (antes las usaban `preparar_carpetas.py` y `comprobar_red.py`),
  pero siguen en `archivos_huellas.txt`.
- `pruebas/escritor/comparar_revision.py` compara con programas de la red anterior: ya no puede dar "igual".

## Qué cambió después de la copia

La corrección de la red y de la demanda (constructor 1) está en `pruebas/correccion_carriles/CONSTRUCTOR1.md`, con
sus comprobaciones. El programa del semáforo, los detectores, el modelo y los lanzadores son del constructor 2.

## Actualización del constructor 2 (18.11.2026, noche)

Lo que dice "Ojo: qué sigue siendo de la corrida detenida" cambió así
(`pruebas/correccion_carriles/CONSTRUCTOR2.md`):

- `LEEME.md` se escribió de nuevo para la red corregida. **`enmienda_registro.md` sigue siendo el de la corrida
  detenida** (11:03): hay que escribir la enmienda nueva antes de lanzar.
- `huellas.sha256` y `archivos_huellas.txt` se rehicieron: 73 archivos. Los lanzadores ya corren (`--comprobar`:
  "listo para lanzar"). La lista del estudio detenido quedó en
  `pruebas/correccion_carriles/huellas_estudio_detenido.sha256`.
- Las dos referencias de la red anterior (`entrada/e2_lima_75_estudio.add.xml` y `entrada/plan_actual_revision.add.xml`)
  salieron de `archivos_huellas.txt`. Los archivos siguen en la carpeta y no los usa ningún programa.
- `pruebas/escritor/comparar_revision.py` compara ahora lo que las dos redes tienen en común (los 47 enlaces que
  existen en las dos) y vuelve a servir.
- En `pruebas/` hay otra vez salidas de pruebas, todas de la red corregida y con semillas de humo: políticas de 2
  episodios en `pruebas/humo/modelo/` y sus copias en `pruebas/lanzadores/lima/`. En `demo_rl/lima` no hay ninguna
  política ni ningún programa ajustado.

## Actualización del corrector (18.11.2026, noche)

Manda sobre lo que dicen arriba "Ojo: qué sigue siendo de la corrida detenida" y la actualización del constructor 2
(`pruebas/correccion_carriles/CORRECTOR.md`):

- **`enmienda_registro.md` se escribió de nuevo para la red corregida.** La de las 11:03 (sha256 `0247e189…`) sigue en
  `nudo_ovalo_estudio/enmienda_registro.md` y en `lima/REGISTRO.md`. `LEEME.md` se puso al día con las revisiones.
- **Textos de la red anterior que quedan en la carpeta** (sin efecto en el estudio; ninguno tiene huella salvo los dos
  programas del último punto):
  - Los 4 `revision/*.out` son de las 11:16 a las 11:29, con la red anterior. Por ejemplo,
    `revision/revisar_programas.out` dice 34 detectores nulos en los actuados; en la red corregida son 36
    (`pruebas/correccion_carriles/revisar_programas_c2.txt`).
  - En `pruebas/correccion_carriles/CONSTRUCTOR1.md` (sección 8) ya no valen la huella de `demanda.py` (`f53d2858…`;
    hoy `08b06eeb…`) ni las de las cuatro demandas (`d5f409a3…`, `d689c180…`, `fce32dfe…` y `1aa230a3…`; hoy
    `db3afbf5…`, `b057c6f2…`, `49d863c8…` y `2320d7cf…`): son de antes de las fracciones definitivas. Valen las de
    `CONSTRUCTOR2.md` (sección 6) y las de la enmienda.
  - En `pruebas/lanzadores/lima/` y `alta/` hay 12 políticas de humo de 2 episodios con los nombres de las bases del
    estudio (`_s42`, `_s2042`, `_s4042`). No son del estudio; lo dice el aviso `NO_SON_DEL_ESTUDIO.txt`.
  - Dos comentarios del código citan la red anterior: `demo_rl/rl_ippo.py`, línea 152 ("nudo_ovalo_estudio/LEEME.md"),
    y `demo_rl/lima/estudio.py`, línea 68 ("53 enlaces"). No se tocan, para no cambiar la huella del modelo.
