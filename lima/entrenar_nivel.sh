#!/bin/bash
# entrenar_nivel.sh - Caso Lima: lo mismo que entrenar.sh, para otro nivel de demanda, en su carpeta.
# Uso (en Git Bash):  bash entrenar_nivel.sh alta      # corre en lima/alta/ (la prepara preparar_nivel.sh)
# Mismo modelo, mismas bases y mismas semillas de validacion que entrenar.sh; solo cambia la demanda de la carpeta.
AQUI="$(cd "$(dirname "$0")" && pwd)"
cd "$AQUI/$1" || exit 1
mkdir -p logs
VAL=21001,21002,21003,21004,21005,21006,21007,21008
for b in 42 2042 4042; do
    python "$AQUI/../rl_ippo.py" train --escenario lima --variante vecinos --seed $b --episodios 400 --eval-cada 20 \
        --val-seeds $VAL --criterio-val total --v2 --registro-extendido --etiqueta completo \
        --obs-cercana 75 --norm-valor --sin-forzadas --msg-cada-paso --lr-horizonte 200 --lr-piso 0.1 \
        --paso-decision 2 > logs/completo_s$b.log 2>&1 &
done
wait
for f in logs/completo_s*.log; do echo "== $f"; tail -1 "$f"; done
