#!/bin/bash
# entrenar.sh - Corredor de la Av. Benavides: lanza en paralelo los nueve entrenamientos y espera a que terminen.
# Uso (desde demo_rl/lima/corredor, en Git Bash):  bash entrenar.sh
# NO editar este archivo mientras corre.
#
# Tres modelos, tres entrenamientos cada uno (bases 42, 2042 y 4042); validacion en 21001-21004 por retraso total:
#   completo   el modelo completo del segundo estudio (con mensajes, 400 episodios, decide cada 2 s)
#   corregido  IPPO con mensajes corregido (200 episodios, decide cada 5 s)
#   sinmsg     IPPO sin mensajes corregido: lo mismo que el anterior, sin mensajes entre vecinos
cd "$(dirname "$0")" || exit 1
mkdir -p logs
VAL=21001,21002,21003,21004
COMUN="--escenario benavides --val-seeds $VAL --criterio-val total --v2 --registro-extendido"
for b in 42 2042 4042; do
    python ../../rl_ippo.py train $COMUN --variante vecinos --seed $b --episodios 400 --eval-cada 20 --etiqueta completo \
        --obs-cercana 75 --norm-valor --sin-forzadas --msg-cada-paso --lr-horizonte 200 --lr-piso 0.1 \
        --paso-decision 2 > logs/completo_s$b.log 2>&1 &
    python ../../rl_ippo.py train $COMUN --variante vecinos --seed $b --episodios 200 --eval-cada 10 --etiqueta corregido \
        > logs/corregido_s$b.log 2>&1 &
    python ../../rl_ippo.py train $COMUN --variante local --seed $b --episodios 200 --eval-cada 10 --etiqueta sinmsg \
        > logs/sinmsg_s$b.log 2>&1 &
done
wait
for f in logs/*_s*.log; do echo "== $f"; tail -1 "$f"; done
