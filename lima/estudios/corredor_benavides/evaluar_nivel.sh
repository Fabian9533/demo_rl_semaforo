#!/bin/bash
# evaluar_nivel.sh - Estudio 2 del corredor de la Av. Benavides (enmienda del 19.11.2026 en demo_rl/lima/REGISTRO.md):
# evaluacion de un nivel de demanda cuando terminan sus referencias y sus entrenamientos. Lo lanza lanzar.sh y espera
# solo (revisa cada 5 minutos). NO editar este archivo mientras corre.
# Uso:  bash evaluar_nivel.sh publicada|alta
#   1. espera las tandas de las referencias (las escribe la cadena de referencias de lanzar.sh)
#   2. con los tres entrenamientos del modelo completo: sus dos tandas, el canal cortado del citado (la base con la
#      validacion mediana), los verdes del modelo, el veredicto y, con la publicada, la prueba de robustez
#   3. con los seis de los mensajes: las dos tandas de los citados con y sin mensajes y el veredicto con los mensajes
AQUI="$(cd "$(dirname "$0")" && pwd)"
COR="$AQUI/demo_rl/lima/corredor"
NIVEL=$1
case "$NIVEL" in
    publicada) export CORREDOR_CARPETA=""; DIR="$COR" ;;
    alta) export CORREDOR_CARPETA=alta; DIR="$COR/alta" ;;
    *) echo "Uso: bash evaluar_nivel.sh publicada|alta"; exit 1 ;;
esac
P=6
esperar() {
    while true; do
        falta=0
        for f in "$@"; do [ -f "$f" ] || falta=1; done
        [ $falta = 0 ] && return 0
        sleep 300
    done
}
brazo() { basename "$1" .pt | sed 's/^politica_benavides_//'; }
cd "$COR" || exit 1
echo "Esperando las referencias de la $NIVEL: $(date '+%d.%m.%Y %H:%M')"
esperar "$DIR/salidas/eval_t2_minimo.csv"
echo "Esperando los entrenamientos del modelo completo: $(date '+%d.%m.%Y %H:%M')"
esperar "$DIR"/politica_benavides_vecinos_completo_s{42,2042,4042}.pt
POLS=politica_benavides_vecinos_completo_s42.pt,politica_benavides_vecinos_completo_s2042.pt,politica_benavides_vecinos_completo_s4042.pt
CIT=$(python "$AQUI/citado.py" "$DIR" vecinos_completo)
MODELO=$(brazo "$CIT")
echo "Modelo completo citado ($NIVEL): $MODELO. Tandas desde $(date '+%d.%m.%Y %H:%M')"
for t in 1 2; do python estudio_corredor.py evaluar --tanda $t --procesos $P --brazos "" --politicas "$POLS" || exit 1; done
for t in 1 2; do python estudio_corredor.py evaluar --tanda $t --procesos $P --brazos "" --politicas "$CIT" --perdida 1 || exit 1; done
python estudio_corredor.py verdes-modelo --procesos 4 --politicas "$CIT" || exit 1
python estudio_corredor.py veredicto --modelo "$MODELO" || exit 1
if [ "$NIVEL" = publicada ]; then
    SEM=$(seq -s, 24001 24100)
    for v in avenida transversal; do
        cp "$COR/benavides_fijo.add.xml" "$COR/benavides_actuadoaj.add.xml" "$COR/robustez/$v/"
        CORREDOR_CARPETA=robustez/$v python estudio_corredor.py evaluar --tanda 1 --procesos $P --semillas "$SEM" \
            --brazos tipico,fijo,actuadoaj --politicas "$CIT" || exit 1
    done
fi
echo "Esperando los entrenamientos de los mensajes: $(date '+%d.%m.%Y %H:%M')"
esperar "$DIR"/politica_benavides_vecinos_corregido_s{42,2042,4042}.pt "$DIR"/politica_benavides_local_sinmsg_s{42,2042,4042}.pt
CON=$(python "$AQUI/citado.py" "$DIR" vecinos_corregido)
SIN=$(python "$AQUI/citado.py" "$DIR" local_sinmsg)
echo "Citados de los mensajes ($NIVEL): $(brazo "$CON") y $(brazo "$SIN")"
for t in 1 2; do python estudio_corredor.py evaluar --tanda $t --procesos $P --brazos "" --politicas "$CON,$SIN" || exit 1; done
python estudio_corredor.py veredicto --modelo "$MODELO" --con-mensajes "$(brazo "$CON")" --sin-mensajes "$(brazo "$SIN")" || exit 1
echo "FIN de la evaluacion de la $NIVEL: $(date '+%d.%m.%Y %H:%M')"
