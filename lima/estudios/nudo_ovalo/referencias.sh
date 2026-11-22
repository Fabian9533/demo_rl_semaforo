#!/bin/bash
# referencias.sh - Estudio del nudo en la red del Ovalo Vasco (enmienda del 18.11.2026 en lima/REGISTRO.md): ajusta las
# referencias de cada demanda en la red del ovalo, con el procedimiento del estudio y sus semillas de ajuste.
# Uso (en Git Bash, desde cualquier carpeta):
#   bash referencias.sh [publicada|alta|ambas] [--procesos N] [--comprobar]      (por defecto: ambas, 4 procesos)
# Pasos de cada demanda (lo ya hecho no se repite; si se corta, se vuelve a lanzar igual):
#   1. fijo ajustado al segundo y ciclo minimo   estudio.py ajustar-fijo     (2001-2010 y los diez mejores con 2001-2030)
#   2. actuado y actuado ajustado               estudio.py ajustar-actuado  (cadena del segundo estudio y variante por
#                                                                            retraso; los tres mejores con 2001-2030)
#   3. comprobacion del borde del actuado        borde_actuado.py ovalo      (un paso mas alla de cada borde del mejor de
#                                                                            cada tipo, la regla del 14.11 escrita de forma
#                                                                            general; si cambia el ganador, el anterior queda
#                                                                            en lima_actuadoajb.add.xml y se instala el nuevo)
#   4. validacion de las referencias             estudio.py validar-referencias (21001-21008; la figura de aprendizaje)
# Todo con LIMA_PROGRAMA=programa_ovalo (el escritor de programas del ovalo) en demo_rl/lima/ y demo_rl/lima/alta/.
# --comprobar: revisa huellas y el escritor del ovalo en las dos carpetas sin simular (comprobar_referencias.py).
AQUI="$(cd "$(dirname "$0")" && pwd)"
LIMA="$AQUI/demo_rl/lima"
NIVELES="publicada alta"
PROCESOS=4
COMPROBAR=0
while [ $# -gt 0 ]; do
    case "$1" in
        publicada|alta) NIVELES="$1" ;;
        ambas) NIVELES="publicada alta" ;;
        --procesos) PROCESOS="$2"; shift ;;
        --comprobar) COMPROBAR=1 ;;
        *) echo "Uso: bash referencias.sh [publicada|alta|ambas] [--procesos N] [--comprobar]"; exit 1 ;;
    esac
    shift
done
if ! (cd "$AQUI" && sha256sum --quiet -c huellas.sha256); then
    echo "El codigo o los datos no son los de huellas.sha256 (enmienda del 18.11.2026): no se lanza"
    exit 1
fi
if [ "$COMPROBAR" = 1 ]; then
    python "$AQUI/comprobar_referencias.py" || exit 1
    echo "Huellas y escritor del ovalo correctos: listo para lanzar referencias.sh ($NIVELES, $PROCESOS procesos)"
    exit 0
fi
mkdir -p "$AQUI/logs"
export LIMA_PROGRAMA=programa_ovalo
for nivel in $NIVELES; do
    if [ "$nivel" = alta ]; then sub=alta; else sub=""; fi
    S="$LIMA/$sub/salidas"
    LOG="$AQUI/logs/referencias_$nivel.log"
    { echo "== $nivel: $(date '+%d.%m.%Y %H:%M')"; (cd "$AQUI" && sha256sum -c huellas.sha256); } >> "$LOG"
    if [ ! -f "$S/fijo_ajustado.json" ]; then
        LIMA_CARPETA=$sub python "$LIMA/estudio.py" ajustar-fijo --procesos $PROCESOS >> "$LOG" 2>&1 || exit 1
    fi
    if [ ! -f "$S/actuado_ajustado.json" ]; then
        LIMA_CARPETA=$sub python "$LIMA/estudio.py" ajustar-actuado --procesos $PROCESOS >> "$LOG" 2>&1 || exit 1
    fi
    if [ ! -f "$S/borde_actuado.json" ]; then
        python "$LIMA/borde_actuado.py" ovalo --carpeta "$sub" --procesos $PROCESOS >> "$LOG" 2>&1 || exit 1
        if grep -q '"cambia": true' "$S/borde_actuado.json"; then
            cp -p "$LIMA/$sub/lima_actuadoaj.add.xml" "$LIMA/$sub/lima_actuadoajb.add.xml"
            python "$LIMA/borde_actuado.py" ovalo --carpeta "$sub" --instalar >> "$LOG" 2>&1 || exit 1
        fi
    fi
    if [ ! -f "$S/val_referencias.json" ]; then
        LIMA_CARPETA=$sub python "$LIMA/estudio.py" validar-referencias --procesos $PROCESOS >> "$LOG" 2>&1 || exit 1
    fi
    echo "== $nivel: terminado $(date '+%d.%m.%Y %H:%M')" >> "$LOG"
    tail -3 "$LOG"
done
