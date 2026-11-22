"""
programa.py - Escribe programas de semaforo para el nudo del caso Lima (semaforo_S1) a partir de una lista de
ESTADOS: cada estado dice que movimientos tienen verde y cuantos segundos dura.

Uso (desde demo_rl/lima):
  python programa.py                     # escribe lima.add.xml (plan vigente en PLAN) y lo imprime
  python programa.py --verdes 40,12,35,30 --salida prueba.add.xml [--tipo actuado]
Como modulo: escribir(ruta, verdes, ...) y enlaces_de_estado(...) los usan ajustar_fijo.py y evaluar_lima.py.

Reglas (iguales para todos los controles, para que la comparacion sea justa):
- Los estados van siempre en el mismo orden; cada control solo cambia cuanto dura cada verde.
- Tras cada verde va una transicion de TRANSICION segundos en ambar para los movimientos que pierden el verde (los
  que siguen en verde en el estado siguiente no pasan por ambar). Si en la calle hay despues un tiempo con todo en
  rojo (ROJO_TOTAL), va tras el ambar y dura lo mismo en todos los controles: ninguno lo acorta ni lo salta.
- Dentro de un estado, un movimiento va con "G" (pasa con prioridad) salvo que entre al mismo carril de salida que
  otro movimiento que tambien esta en verde y deba cederle el paso: entonces va con "g" (pasa si hay hueco). Quien
  cede a quien lo decide la red de SUMO. Si dos movimientos en verde se juntan y ninguno cede, el programa avisa.
- Los cruces de trayectorias dentro del nudo no se simulan (13.11.2026): en el sitio, 28 de Julio y Balboa tienen
  verde a la vez aunque algunos de sus movimientos se cruzan; con las reglas de ceder el paso de SUMO esos
  movimientos quedaban detenidos mas de 15 minutos y un solo vehiculo dentro del nudo bloqueaba a Reducto.

PLAN es el plan que opera hoy en el nudo, medido en el sitio por Fabian Alvarado el viernes 13.11.2026 en la punta de
la tarde. Ciclo de 132 s: Reducto de frente 40 s (sur a norte; norte a sur tiene 38 s), los dos giros a la izquierda de
Reducto 18 s (se prenden cuando el semaforo principal pasa a rojo), 34 s con todo en rojo, y 28 de Julio desde el
puente (38 s) con Balboa (40 s), que se prenden a la vez, 40 s antes de que Reducto vuelva al verde. Decisiones:
- En el sitio no se vio ambar. Aqui los ultimos 3 s de cada verde medido son ambar (el simulador lo necesita para
  que los vehiculos frenen): los verdes del plan son 37, 15 y 37 s y el ciclo sigue en 132 s.
- Reducto norte a sur y 28 de Julio van con el verde de su pareja (40 s y no 38 s).
- Los 34 s con todo en rojo se conservan iguales en todos los controles.
"""
import argparse
import os
import sys

if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
import sumolib

AQUI = os.path.dirname(os.path.abspath(__file__))
RED = os.path.join(AQUI, "lima.net.xml")
TLS = "semaforo_S1"
TRANSICION = 3                 # s de ambar despues de cada verde
ROJO_TOTAL = {1: 34}           # {indice del estado: s con todo en rojo despues de su ambar}; igual en todos los controles
NO_VERDES = ("transicion", "todo en rojo")
VERDE_MIN, VERDE_MAX = 10, 60  # limites del agente; un estado de solo giro (1 o 2 enlaces) baja a 5 s

# Estados del plan: (nombre, verde en s, [(entrada, salidas con verde o "*" para todas, salidas excluidas)])
PLAN = [
    ("Reducto de frente, los dos sentidos", 37, [("RN_S1", "*", ("S1_J",)), ("RS_S1", "*", ("S1_L",))]),
    ("Giros a la izquierda de Reducto", 15, [("RN_S1", ("S1_J",), ()), ("RS_S1", ("S1_L",), ())]),
    ("28 de Julio desde el puente y Balboa", 37, [("J_S1", "*", ()), ("B_S1", "*", ())]),
]

_CACHE = {}


def red():
    if "net" not in _CACHE:
        net = sumolib.net.readNet(RED, withPrograms=True, withInternal=False)
        tls = net.getTLS(TLS)
        con = {}                                  # indice del semaforo -> conexion
        for c in net.getNode("S1").getConnections():
            if c.getTLSID() == TLS:
                con[c.getTLLinkIndex()] = c
        _CACHE.update(net=net, tls=tls, con=con, nodo=net.getNode("S1"))
    return _CACHE


def enlaces_de_estado(movimientos):
    """Indices de los enlaces del semaforo que tienen verde en un estado."""
    r = red()
    res = set()
    for entrada, salidas, excluidas in movimientos:
        for i, c in r["con"].items():
            if c.getFrom().getID() != entrada:
                continue
            hacia = c.getTo().getID()
            if (salidas == "*" or hacia in salidas) and hacia not in excluidas:
                res.add(i)
        assert any(r["con"][i].getFrom().getID() == entrada for i in res), f"sin enlaces para {entrada}"
    return res


def letras(verdes):
    """Cadena de estado de un verde: G con prioridad, g si entra al mismo carril de salida que otro enlace en verde y
    le cede el paso, r el resto. Devuelve tambien los pares en verde que se juntan sin que ninguno ceda. Los cruces
    de trayectorias dentro del nudo no se simulan (la red no tiene tramos internos: armar_red.py)."""
    r = red()
    n = len(r["con"])
    estado, inseguros = [], []
    for i in range(n):
        if i not in verdes:
            estado.append("r")
            continue
        cede = any(j != i and mismo_destino(i, j) and r["nodo"].forbids(r["con"][j], r["con"][i]) for j in verdes)
        estado.append("g" if cede else "G")
    lista = sorted(verdes)
    for a in lista:
        for b in lista:
            if a < b and mismo_destino(a, b):
                if not r["nodo"].forbids(r["con"][a], r["con"][b]) and not r["nodo"].forbids(r["con"][b], r["con"][a]):
                    inseguros.append((a, b))
    return "".join(estado), inseguros


def mismo_destino(a, b):
    """Dos enlaces del semaforo que entran al mismo carril de salida (se juntan)."""
    r = red()
    return r["con"][a].getToLane().getID() == r["con"][b].getToLane().getID()


def fases(verdes_seg, plan=None, transicion=TRANSICION):
    """[(duracion, estado, nombre)]: verde y transicion de cada estado del plan, con las duraciones verdes_seg."""
    plan = plan or PLAN
    assert len(verdes_seg) == len(plan)
    conjuntos = [enlaces_de_estado(mov) for _, _, mov in plan]
    res, avisos = [], []
    for k, (nombre, _, _) in enumerate(plan):
        verde, inseguros = letras(conjuntos[k])
        if inseguros:
            avisos.append((nombre, inseguros))
        # si despues viene un rojo total, todos los verdes pasan por ambar; si no, solo los que pierden el verde
        siguiente = set() if ROJO_TOTAL.get(k) else conjuntos[(k + 1) % len(plan)]
        ambar = "".join("y" if (c in "Gg" and i not in siguiente) else c for i, c in enumerate(verde))
        res.append((verdes_seg[k], verde, nombre))
        res.append((transicion, ambar, "transicion"))
        if ROJO_TOTAL.get(k):
            res.append((ROJO_TOTAL[k], "r" * len(verde), "todo en rojo"))
    return res, avisos


def tiempo_fijo(plan=None, transicion=TRANSICION):
    """Segundos del ciclo que no son verde y que ningun control puede cambiar: las transiciones y el rojo total."""
    return len(plan or PLAN) * transicion + sum(ROJO_TOTAL.values())


def verde_minimo(estado):
    """Verde minimo de un estado: 10 s, o 5 s si es un giro solo (1 o 2 enlaces en verde), como en rl_corredor."""
    return 5 if sum(c in "Gg" for c in estado) <= 2 else VERDE_MIN


def minimos(plan=None):
    """Verde minimo de cada estado del plan."""
    plan = plan or PLAN
    lista, _ = fases([v for _, v, _ in plan], plan)
    return [verde_minimo(estado) for _, estado, nombre in lista if nombre not in NO_VERDES]


def escribir(ruta, verdes_seg, plan=None, tipo="fijo", programa=None, comentario="", transicion=TRANSICION,
             parametros=None):
    """Escribe el .add.xml de un control. tipo: "fijo" (duraciones verdes_seg), "actuado" (control actuado de SUMO
    con los mismos estados; verdes_seg da el verde maximo de cada estado y el minimo es el del agente) o "retraso"
    (la variante de SUMO que decide por el retraso de los vehiculos, delay_based, con los mismos limites).
    parametros: {clave: valor} del control de SUMO (max-gap, detector-gap...)."""
    plan = plan or PLAN
    lista, avisos = fases(verdes_seg, plan, transicion)
    lineas = ["<additional>"]
    if comentario:
        lineas.append(f"    <!-- {comentario} -->")
    if tipo == "fijo":
        lineas.append(f'    <tlLogic id="{TLS}" type="static" programID="{programa or "fijo"}" offset="0">')
        for dur, estado, nombre in lista:
            lineas.append(f'        <phase duration="{dur}" state="{estado}"/>  <!-- {nombre} -->')
    else:
        clase = "delay_based" if tipo == "retraso" else "actuated"
        lineas.append(f'    <tlLogic id="{TLS}" type="{clase}" programID="{programa or "actuado"}" offset="0">')
        for clave, valor in (parametros or {}).items():
            lineas.append(f'        <param key="{clave}" value="{valor}"/>')
        for dur, estado, nombre in lista:
            if nombre in NO_VERDES:
                lineas.append(f'        <phase duration="{dur}" state="{estado}"/>  <!-- {nombre} -->')
            else:
                minimo = verde_minimo(estado)
                lineas.append(f'        <phase duration="{minimo}" minDur="{minimo}" maxDur="{max(minimo, dur)}" '
                              f'state="{estado}"/>  <!-- {nombre} -->')
    lineas += ["    </tlLogic>", "</additional>"]
    tmp = f"{ruta}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas) + "\n")
    os.replace(tmp, ruta)
    return lista, avisos


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--verdes", default=None, help="verde de cada estado, en s, separados por coma")
    ap.add_argument("--salida", default=os.path.join(AQUI, "lima.add.xml"))
    ap.add_argument("--tipo", choices=["fijo", "actuado"], default="fijo")
    args = ap.parse_args()
    verdes = [int(v) for v in args.verdes.split(",")] if args.verdes else [v for _, v, _ in PLAN]
    lista, avisos = escribir(args.salida, verdes, tipo=args.tipo,
                             comentario="Plan actual del nudo, medido en el sitio el 13.11.2026 (programa.py)")
    r = red()
    print(f"Escrito {args.salida}: {len(PLAN)} estados, ciclo {sum(d for d, _, _ in lista)} s")
    for dur, estado, nombre in lista:
        print(f"  {dur:3d} s  {estado}  {nombre}")
    for nombre, pares in avisos:
        for a, b in pares:
            ca, cb = r["con"][a], r["con"][b]
            print(f"AVISO, estado '{nombre}': se cruzan sin ceder {ca.getFrom().getID()}>{ca.getTo().getID()} "
                  f"y {cb.getFrom().getID()}>{cb.getTo().getID()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
