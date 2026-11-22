#!/bin/bash
# continuar_publicada.sh - Estudio 2 del corredor de la Av. Benavides: sigue la evaluacion de la publicada desde el
# veredicto. evaluar_nivel.sh publicada se detuvo el 20.11.2026 a las 03:33 en ese paso porque faltaba
# demo_rl/evaluar.py en la copia (estudio.comparar lo importa para el IC por bootstrap). Se copio sin cambios del repo
# (main @53bdb48, sha256 44ed0b47...) y este script corre los pasos que faltaban, con los mismos comandos y en el mismo
# orden que evaluar_nivel.sh: veredicto, robustez, mensajes y veredicto con los mensajes.
# Uso (en Git Bash):  bash continuar_publicada.sh > logs/evaluar_publicada_continuacion.log 2>&1
AQUI="$(cd "$(dirname "$0")" && pwd)"
COR="$AQUI/demo_rl/lima/corredor"
export CORREDOR_CARPETA=""
DIR="$COR"
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
CIT=$(python "$AQUI/citado.py" "$DIR" vecinos_completo)
MODELO=$(brazo "$CIT")
echo "Continuacion de la publicada desde el veredicto ($MODELO): $(date '+%d.%m.%Y %H:%M')"
python estudio_corredor.py veredicto --modelo "$MODELO" || exit 1
SEM=$(seq -s, 24001 24100)
for v in avenida transversal; do
    cp "$COR/benavides_fijo.add.xml" "$COR/benavides_actuadoaj.add.xml" "$COR/robustez/$v/"
    CORREDOR_CARPETA=robustez/$v python estudio_corredor.py evaluar --tanda 1 --procesos $P --semillas "$SEM" \
        --brazos tipico,fijo,actuadoaj --politicas "$CIT" || exit 1
done
echo "Esperando los entrenamientos de los mensajes: $(date '+%d.%m.%Y %H:%M')"
esperar "$DIR"/politica_benavides_vecinos_corregido_s{42,2042,4042}.pt "$DIR"/politica_benavides_local_sinmsg_s{42,2042,4042}.pt
CON=$(python "$AQUI/citado.py" "$DIR" vecinos_corregido)
SIN=$(python "$AQUI/citado.py" "$DIR" local_sinmsg)
echo "Citados de los mensajes (publicada): $(brazo "$CON") y $(brazo "$SIN")"
for t in 1 2; do python estudio_corredor.py evaluar --tanda $t --procesos $P --brazos "" --politicas "$CON,$SIN" || exit 1; done
python estudio_corredor.py veredicto --modelo "$MODELO" --con-mensajes "$(brazo "$CON")" --sin-mensajes "$(brazo "$SIN")" || exit 1
echo "FIN de la evaluacion de la publicada: $(date '+%d.%m.%Y %H:%M')"
