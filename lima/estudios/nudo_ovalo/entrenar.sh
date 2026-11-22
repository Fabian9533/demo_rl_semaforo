#!/bin/bash
# entrenar.sh - Estudio del nudo en la red del Ovalo Vasco (enmienda del 18.11.2026 en lima/REGISTRO.md): lanza en
# paralelo los seis entrenamientos de un modelo (bases 42, 2042 y 4042, con la demanda publicada y con la alta) y espera
# a que terminen.
# Uso (en Git Bash, desde cualquier carpeta):
#   bash entrenar.sh libre [--comprobar]      modelo de orden libre (--orden-libre), etiqueta libre: el modelo citado
#   bash entrenar.sh completo [--comprobar]   modelo de orden fijo del estudio, etiqueta completo, en la misma red
# Los dos se lanzan a la vez, doce entrenamientos (LEEME.md, "Orden de ejecucion"). --comprobar solo revisa las huellas
# y los argumentos de los seis; no entrena.
#
# Antes de nada comprueba que el codigo y los datos son los de la enmienda (huellas.sha256, junto a este archivo); si
# algo cambio, no lanza. Las opciones son las de lima/entrenar.sh y lima/entrenar_nivel.sh del estudio (el modelo
# completo: 400 episodios, validacion cada 20 en 21001-21008 por retraso total, se guarda la version de menor retraso
# medio); el orden libre agrega --orden-libre, como orden_libre_2026-11-17/entrenar_libre.sh. Carpetas de trabajo:
#   demanda publicada: demo_rl/lima/       demanda alta: demo_rl/lima/alta/      (la red del ovalo)
#   salidas: resultados_lima_ippo_vecinos_<etiqueta>_s<base>.csv, politica_lima_vecinos_<etiqueta>_s<base>.pt/.json y
#            checkpoints/lima_ippo_vecinos_<etiqueta>_s<base>_ep*.pt; registros en logs/<etiqueta>_<nivel>_s<base>.log y
#            logs/lanzamiento_<etiqueta>.txt (cuando, donde y las huellas comprobadas)
AQUI="$(cd "$(dirname "$0")" && pwd)"
LIMA="$AQUI/demo_rl/lima"
MODELO="$1"
VAL=21001,21002,21003,21004,21005,21006,21007,21008
OPC="--escenario lima --variante vecinos --episodios 400 --eval-cada 20 --val-seeds $VAL --criterio-val total --v2 \
--registro-extendido --obs-cercana 75 --norm-valor --sin-forzadas --msg-cada-paso --lr-horizonte 200 --lr-piso 0.1 \
--paso-decision 2"
case "$MODELO" in
    libre) OPC="$OPC --etiqueta libre --orden-libre" ;;
    completo) OPC="$OPC --etiqueta completo" ;;
    *) echo "Uso: bash entrenar.sh libre|completo [--comprobar]"; exit 1 ;;
esac
# el codigo y los datos tienen que ser los de la enmienda
if ! (cd "$AQUI" && sha256sum --quiet -c huellas.sha256); then
    echo "El codigo o los datos no son los de huellas.sha256 (enmienda del 18.11.2026): no se lanza"
    exit 1
fi
if [ "$2" = "--comprobar" ]; then
    for b in 42 2042 4042; do
        python "$AQUI/demo_rl/rl_ippo.py" train $OPC --seed $b --validar-args || exit 1
    done
    for carpeta in "$LIMA" "$LIMA/alta"; do
        for f in lima.sumocfg lima.net.xml lima.rou.xml lima.add.xml e2_lima_75.add.xml lima_libre.json; do
            [ -f "$carpeta/$f" ] || { echo "Falta $carpeta/$f"; exit 1; }
        done
        if ls "$carpeta"/resultados_lima_ippo_vecinos_${MODELO}_s*.csv > /dev/null 2>&1; then
            echo "Ya hay entrenamientos con la etiqueta $MODELO en $carpeta"
            exit 1
        fi
    done
    echo "Huellas, datos y argumentos de los seis entrenamientos $MODELO correctos en $AQUI: listo para lanzar"
    exit 0
fi
# rl_ippo reescribe el CSV y borra los checkpoints de su etiqueta: no se relanza sobre una corrida ya empezada
for carpeta in "$LIMA" "$LIMA/alta"; do
    if ls "$carpeta"/resultados_lima_ippo_vecinos_${MODELO}_s*.csv > /dev/null 2>&1; then
        echo "Ya hay entrenamientos con la etiqueta $MODELO en $carpeta: no se relanza (moverlos a mano si hace falta)"
        exit 1
    fi
done
mkdir -p "$AQUI/logs"
{ echo "Lanzado $MODELO el $(date '+%d.%m.%Y a las %H:%M') en $AQUI"; (cd "$AQUI" && sha256sum -c huellas.sha256); } \
    > "$AQUI/logs/lanzamiento_$MODELO.txt"
for nivel in publicada alta; do
    if [ "$nivel" = alta ]; then carpeta="$LIMA/alta"; else carpeta="$LIMA"; fi
    for b in 42 2042 4042; do
        (cd "$carpeta" && python "$AQUI/demo_rl/rl_ippo.py" train $OPC --seed $b \
            > "$AQUI/logs/${MODELO}_${nivel}_s$b.log" 2>&1) &
    done
done
wait
for f in "$AQUI"/logs/${MODELO}_*_s*.log; do echo "== $f"; tail -1 "$f"; done
