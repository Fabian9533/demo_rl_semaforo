# Casos de Lima: código, datos y salidas de cada estudio

Los dos casos de Lima de la tesis (Sección 5.3 y Anexo D) corrieron cada uno en una copia de trabajo propia del
repositorio, con los programas del caso. Esta carpeta guarda esas copias tal como quedaron, sin los checkpoints
intermedios, los `tripinfo_*.xml`, los registros (`logs/`) ni las pruebas previas: pesan cientos de MB y no hacen
falta para repetir el estudio.

| Carpeta | Caso | Copia de trabajo original | Veredictos |
|---|---|---|---|
| `nudo_ovalo/` | nudo del Óvalo Vasco, un semáforo | `nudo_ovalo_estudio2/` | `salidas_ovalo/veredicto_ovalo.md` |
| `corredor_benavides/` | corredor de la Av. Benavides, seis cruces | `corredor_estudio2/` | `demo_rl/lima/corredor/salidas/veredicto_vecinos_completo_s42.md` (demanda publicada) y `demo_rl/lima/corredor/alta/salidas/veredicto_vecinos_completo_s4042.md` (alta) |

## Qué hay en cada carpeta

- `huellas.sha256`: sha256 de los archivos de los que dependen las cifras (73 en el nudo y 63 en el corredor),
  tomadas al lanzar el estudio. Los lanzadores no arrancan si alguna no coincide.
- `demo_rl/`: los archivos del repositorio que usa el estudio, en la versión con que corrió (los que tienen huella,
  byte a byte), y sus salidas: referencias ajustadas, políticas evaluadas (`politica_*.pt`, con su `.json`, que guarda
  las huellas del código con que se entrenó), CSV de entrenamiento y carpetas `salidas/`.
- En la raíz: los lanzadores, los programas propios del estudio y las notas del registro (`enmienda_*.md`, ya
  copiadas en `lima/REGISTRO.md`, y `cierre_*.md`, que quedan aquí). En el nudo, además, su nota de trabajo
  (`LEEME.md`), con el orden de ejecución, los tiempos y los límites.
- `salidas_del_estudio.txt`: los archivos que produjo la corrida. Lo demás es código y datos de entrada.

Cada caso tiene su propio `demo_rl/rl_ippo.py`, el del repositorio con una extensión: el del nudo agrega la variante
de orden libre (`--orden-libre`) y la traza de luces (`--traza-fases`); el del corredor, un verde mínimo por semáforo
y estado (el de los peatones), que declara su `demo_rl/escenarios_lima.py`.

Una excepción en el corredor: `demo_rl/lima/corredor/tablas_corredor.py` se editó después del lanzamiento, solo en
rótulos y comentarios de las tablas (`cierre_registro_corredor.md`, punto 2), así que su huella no coincide. La
versión del lanzamiento está en `tablas_corredor_lanzamiento.py`, con la huella registrada.

## Cómo armar la copia de trabajo

Requisitos: SUMO 1.25.0 (con `SUMO_HOME`), Python 3.14 con PyTorch 2.14 (CPU), `traci`, `sumolib`, `numpy`, `scipy`
y `matplotlib`, y bash (en Windows, Git Bash). Son las versiones que guarda el `.json` de cada política.

Cada copia es el repositorio en el commit `53bdb48`, la base de los dos estudios, dentro de `demo_rl/`, con la
carpeta del caso encima. Se arman junto al repositorio y con los nombres de las copias originales, que son los que
buscan los programas de `figuras/`:

    git clone https://github.com/Fabian9533/demo_rl_semaforo.git demo_rl
    mkdir -p nudo_ovalo_estudio2/demo_rl corredor_estudio2/demo_rl
    git -C demo_rl archive 53bdb48 | tar -x -C nudo_ovalo_estudio2/demo_rl
    git -C demo_rl archive 53bdb48 | tar -x -C corredor_estudio2/demo_rl
    cp -r demo_rl/lima/estudios/nudo_ovalo/. nudo_ovalo_estudio2/
    cp -r demo_rl/lima/estudios/corredor_benavides/. corredor_estudio2/
    (cd nudo_ovalo_estudio2 && sha256sum -c huellas.sha256)     # las 73 coinciden
    (cd corredor_estudio2 && sha256sum -c huellas.sha256)       # 62 de 63: falla solo tablas_corredor.py

Git no convierte los fines de línea de esta carpeta (`.gitattributes` de la raíz), así que las huellas coinciden en
cualquier sistema.

## Comprobar las cifras sin simular (minutos)

Git no guarda las fechas de los archivos, y `evaluar_ovalo.py` rechaza una evaluación más vieja que el programa o la
política que evaluó (función `al_dia`). Por eso, en el nudo, primero se pone al día la fecha de las salidas:

    cd nudo_ovalo_estudio2
    find demo_rl/lima -path '*/salidas/*' -type f -exec touch {} +
    python evaluar_ovalo.py veredicto      # salidas_ovalo/veredicto_ovalo.md y .json
    python tablas_ovalo.py                 # salidas_ovalo/tesis/: tablas y figuras del estudio

    cd corredor_estudio2/demo_rl/lima/corredor
    python tablas_corredor.py --niveles publicada,alta --destino prueba

Comprobado en copias armadas así: el veredicto y las tablas y figuras del nudo salen iguales, byte a byte, a las
guardadas, y las siete tablas del corredor que usa la tesis salen iguales salvo las líneas entre filas, que se
agregaron a mano en la tesis. `tablas_corredor.py` escribe además dos tablas y una figura que juntan los casos con el
nudo de la red anterior (`lima_resumen.tex`, `resultado_final.tex` y `fig_resultado_final`) y que la tesis no usa:
su resultado final sale de `figuras/resultado_final_ovalo.py`. Sin `--destino`, escribe en el `TESIS/` de la copia.

## Repetir el estudio desde cero

Los lanzadores no rehacen lo que ya está (un entrenamiento con la misma etiqueta, una evaluación ya escrita): desde
la raíz de la copia, primero se borran las salidas.

    xargs -d '\n' rm -f < salidas_del_estudio.txt

- Nudo: los pasos de "Orden de ejecución y horas" de `nudo_ovalo/LEEME.md`, desde la raíz de la copia. A la vez,
  `bash entrenar.sh libre`, `bash entrenar.sh completo` y `bash referencias.sh ambas --procesos 4`; al terminar
  cada parte, `python evaluar_ovalo.py referencias`, `modelos` y `robustez`, y al final `veredicto` y
  `python tablas_ovalo.py`. Con `--comprobar`, los lanzadores solo revisan las huellas y los argumentos.
- Corredor: `cp tablas_corredor_lanzamiento.py demo_rl/lima/corredor/tablas_corredor.py` (el lanzador comprueba
  las huellas) y `bash lanzar.sh`. Lanza los seis entrenamientos del modelo, ajusta y valida las referencias, entrena
  IPPO con y sin mensajes y deja corriendo `evaluar_nivel.sh` en cada demanda, que evalúa y da el veredicto.

En la PC de los estudios (8 núcleos, 16 hilos) el nudo tardó unas 9.5 h y el corredor unas 15 h. Cada semilla corre
por separado: el número de procesos no cambia ningún resultado.
