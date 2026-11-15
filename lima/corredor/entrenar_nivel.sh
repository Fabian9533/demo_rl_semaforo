#!/bin/bash
# entrenar_nivel.sh - Corredor de la Av. Benavides: lo mismo que entrenar.sh, para otro nivel de demanda, en su carpeta.
# Uso (en Git Bash):  bash entrenar_nivel.sh alta
# La carpeta se prepara antes con:  python corredor.py nivel --factor 1.2 --carpeta alta
# Mismos modelos, mismas bases y mismas semillas de validacion que entrenar.sh; solo cambia la demanda de la carpeta.
# NO editar este archivo mientras corre.
AQUI="$(cd "$(dirname "$0")" && pwd)"
cd "$AQUI/$1" || exit 1
mkdir -p logs
VAL=21001,21002,21003,21004
COMUN="--escenario benavides --val-seeds $VAL --criterio-val total --v2 --registro-extendido"
for b in 42 2042 4042; do
    python "$AQUI/../../rl_ippo.py" train $COMUN --variante vecinos --seed $b --episodios 400 --eval-cada 20 \
        --etiqueta completo --obs-cercana 75 --norm-valor --sin-forzadas --msg-cada-paso --lr-horizonte 200 \
        --lr-piso 0.1 --paso-decision 2 > logs/completo_s$b.log 2>&1 &
    python "$AQUI/../../rl_ippo.py" train $COMUN --variante vecinos --seed $b --episodios 200 --eval-cada 10 \
        --etiqueta corregido > logs/corregido_s$b.log 2>&1 &
    python "$AQUI/../../rl_ippo.py" train $COMUN --variante local --seed $b --episodios 200 --eval-cada 10 \
        --etiqueta sinmsg > logs/sinmsg_s$b.log 2>&1 &
done
wait
for f in logs/*_s*.log; do echo "== $f"; tail -1 "$f"; done
