#!/bin/bash
# entrenar.sh - Caso Lima: lanza en paralelo los tres entrenamientos del modelo y espera a que terminen.
# Uso (desde demo_rl/lima, en Git Bash):  bash entrenar.sh
#
# Modelo: el modelo completo del segundo estudio, sin cambios (ve los vehiculos cercanos, tres ajustes del
# entrenamiento, 400 episodios y decide cada 2 s). En el nudo no hay vecinos, asi que no hay mensajes.
# Tres entrenamientos (bases 42, 2042 y 4042). La version que se guarda de cada uno es la de menor retraso total
# medio en las ocho semillas de validacion (21001-21008), que no se usan para nada mas.
# Registros en logs/completo_s<base>.log; salidas: resultados_lima_ippo_vecinos_completo_s<base>.csv y
# politica_lima_vecinos_completo_s<base>.pt.
cd "$(dirname "$0")" || exit 1
mkdir -p logs
VAL=21001,21002,21003,21004,21005,21006,21007,21008
for b in 42 2042 4042; do
    python ../rl_ippo.py train --escenario lima --variante vecinos --seed $b --episodios 400 --eval-cada 20 \
        --val-seeds $VAL --criterio-val total --v2 --registro-extendido --etiqueta completo \
        --obs-cercana 75 --norm-valor --sin-forzadas --msg-cada-paso --lr-horizonte 200 --lr-piso 0.1 \
        --paso-decision 2 > logs/completo_s$b.log 2>&1 &
done
wait
for f in logs/completo_s*.log; do echo "== $f"; tail -1 "$f"; done
