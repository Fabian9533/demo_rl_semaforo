#!/bin/bash
# lanzar.sh - Estudio 2 del corredor de la Av. Benavides (enmienda del 19.11.2026 en demo_rl/lima/REGISTRO.md): red
# corregida (Casimiro Ulloa en T, 2 carriles al oeste de Larco) y verdes minimos de los peatones.
# Uso (en Git Bash):  bash lanzar.sh        NO editar este archivo ni el codigo mientras corre.
#   - los 6 entrenamientos del modelo completo (bases 42, 2042 y 4042; demanda publicada y alta), ya
#   - por nivel, en cadena: fijo ajustado, actuado ajustado, validacion y tandas de las referencias, y despues los 6
#     entrenamientos de los mensajes (IPPO con y sin mensajes corregido)
#   - por nivel, evaluar_nivel.sh: espera y evalua los modelos (tandas, canal cortado, verdes, robustez y veredicto)
# Las opciones de los modelos son las de demo_rl/lima/corredor/entrenar.sh y entrenar_nivel.sh del estudio.
# Registros en logs/; logs/lanzamiento.txt guarda la hora y las huellas comprobadas.
AQUI="$(cd "$(dirname "$0")" && pwd)"
COR="$AQUI/demo_rl/lima/corredor"
RL="$AQUI/demo_rl/rl_ippo.py"
LOG="$AQUI/logs"
VAL=21001,21002,21003,21004
COMUN="--escenario benavides --val-seeds $VAL --criterio-val total --v2 --registro-extendido"
COMPLETO="--variante vecinos --episodios 400 --eval-cada 20 --etiqueta completo --obs-cercana 75 --norm-valor \
--sin-forzadas --msg-cada-paso --lr-horizonte 200 --lr-piso 0.1 --paso-decision 2"
CORREGIDO="--variante vecinos --episodios 200 --eval-cada 10 --etiqueta corregido"
SINMSG="--variante local --episodios 200 --eval-cada 10 --etiqueta sinmsg"
if ! (cd "$AQUI" && sha256sum --quiet -c huellas.sha256); then
    echo "El codigo o los datos no son los de huellas.sha256: no se lanza"
    exit 1
fi
if ls "$COR"/politica_benavides_* "$COR"/alta/politica_benavides_* > /dev/null 2>&1; then
    echo "Ya hay politicas entrenadas en $COR: no se relanza"
    exit 1
fi
mkdir -p "$LOG"
{ echo "Lanzado el $(date '+%d.%m.%Y a las %H:%M:%S') en $AQUI"; (cd "$AQUI" && sha256sum -c huellas.sha256 | grep -c ": OK$" \
  | sed 's/$/ archivos con la huella de huellas.sha256/'); } > "$LOG/lanzamiento.txt"
carpeta() { if [ "$1" = publicada ]; then echo "$COR"; else echo "$COR/alta"; fi; }
entrenar() {      # nivel nombre opciones...
    local nivel=$1 nombre=$2
    shift 2
    (cd "$(carpeta "$nivel")" && python "$RL" train $COMUN "$@" > "$LOG/${nombre}_${nivel}.log" 2>&1)
}
cadena() {        # nivel: referencias y sus tandas; despues, los seis entrenamientos de los mensajes
    local nivel=$1 sub=""
    [ "$nivel" = alta ] && sub=alta
    if ! (cd "$COR" && export CORREDOR_CARPETA=$sub && \
          python estudio_corredor.py ajustar-fijo --procesos 5 && \
          python estudio_corredor.py ajustar-actuado --procesos 5 && \
          python estudio_corredor.py validar-referencias --procesos 4 && \
          python estudio_corredor.py evaluar --tanda 1 --procesos 5 --brazos tipico,fijo,actuado,actuadoaj,minimo && \
          python estudio_corredor.py evaluar --tanda 2 --procesos 5 --brazos tipico,fijo,actuado,actuadoaj,minimo) \
          > "$LOG/referencias_$nivel.log" 2>&1; then
        echo "FALLO en las referencias de la $nivel: $(date '+%H:%M')" >> "$LOG/lanzamiento.txt"
        return 1
    fi
    echo "Referencias de la $nivel listas: $(date '+%d.%m.%Y %H:%M')" >> "$LOG/lanzamiento.txt"
    for b in 42 2042 4042; do
        entrenar "$nivel" corregido_s$b --seed $b $CORREGIDO &
        entrenar "$nivel" sinmsg_s$b --seed $b $SINMSG &
    done
    wait
    echo "Entrenamientos de los mensajes de la $nivel listos: $(date '+%d.%m.%Y %H:%M')" >> "$LOG/lanzamiento.txt"
}
for b in 42 2042 4042; do
    for nivel in publicada alta; do
        entrenar $nivel completo_s$b --seed $b $COMPLETO &
    done
done
cadena publicada &
cadena alta &
bash "$AQUI/evaluar_nivel.sh" publicada > "$LOG/evaluar_publicada.log" 2>&1 &
bash "$AQUI/evaluar_nivel.sh" alta > "$LOG/evaluar_alta.log" 2>&1 &
wait
echo "Todo terminado: $(date '+%d.%m.%Y a las %H:%M')" >> "$LOG/lanzamiento.txt"
