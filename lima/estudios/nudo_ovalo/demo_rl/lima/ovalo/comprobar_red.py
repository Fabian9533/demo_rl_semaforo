"""
comprobar_red.py - Resumen y comprobaciones de la red del estudio del nudo en el Ovalo Vasco (18.11.2026), con sumolib.

Uso (desde lima/ovalo, despues de armar_ovalo.py y preparar_carpetas.py):  python -B comprobar_red.py
Escribe red/resumen_estudio.txt. Sale con 1 si alguna comprobacion falla. No simula nada.

Correccion de carriles (18.11.2026, tarde; nudo_ovalo_estudio2). Tres comprobaciones comparaban con archivos de la red
anterior y con la red nueva fallaban por diseno: los carriles de las entradas contra la red del estudio (el nudo como
un punto), los detectores E2 contra la copia del estudio y las letras del plan contra las de la revision. Ahora cada
una se hace contra lo que debe ser: la tabla DISPOSICION del constructor, la red de la carpeta y la regla de las luces
(plan_ovalo.py) sobre esa red. El numero de enlaces (antes 53, escrito a mano) sale de las conexiones del constructor.

Comprueba, en las cuatro carpetas de trabajo (lima/, lima/alta/, lima/robustez/reducto/ y lima/robustez/transversal/):
  - afuera: las mismas 8 aristas del estudio, con su velocidad y el largo de cada carril (0.02 m de tolerancia) como en
    lima/lima.net.xml del repositorio (copia en entrada/red_estudio/). Carriles: los de DISPOSICION; en Balboa, 28 de
    Julio y las cuatro salidas, ademas, los mismos de la red del estudio (no cambiaron);
  - adentro: las aristas de CARRILES_INTERNOS, con sus carriles, y ninguna otra;
  - carril a carril: cada carril de cada entrada llega, siguiendo las conexiones de la red armada, exactamente a las
    salidas de DISPOSICION; los movimientos son los de CAMINOS y no hay vuelta en U;
  - los detectores E2 de 75 m son los de esta red: uno por carril de entrada (15), con el id, el carril, el inicio y
    el fin que escribe rl_ippo.archivo_e2 (los 75 m antes de la linea de parada);
  - la demanda es la de entrada/rutas_estudio/, flujo por flujo, con el camino por el ovalo en "via" como unica
    diferencia; ademas, lo que comprueba regenerar_demanda.py: los carriles de la regla (demanda.GRUPOS) son los de la
    red, los totales (4271 veh/h; la alta, 1.2 veces) y un flujo por movimiento y cuarto de hora;
  - el .sumocfg es el del estudio con <ignore-junction-blocker value="10"/> y sin teletransportes (time-to-teleport -1);
  - el semaforo semaforo_S1 maneja los 10 nodos del ovalo: un enlace por conexion del constructor y ninguna conexion
    sin semaforo; todo enlace lo usa al menos un movimiento (uno que no usara nadie quedaria en rojo siempre); cada
    carril de entrada tiene verde en un solo estado del plan y los carriles de cada estado, leidos de las letras, son
    los de DISPOSICION; lo que la red marca como giro a la izquierda en las lineas de parada (lo que lee giro_izq en
    rl_ippo.py) sale exactamente de los carriles de Reducto que solo giran a la izquierda;
  - el plan actual (lima.add.xml) tiene las duraciones del plan (37, 3, 15, 3, 34, 37 y 3 s) y las letras que da la
    regla sobre la red de la carpeta, sin enlaces que choquen con prioridad; lima_libre.json tiene las fases que da
    la regla del orden libre;
  - ningun tramo interno queda por debajo de 5.56 m/s.
Y resume la red: lados (de esquina a esquina), lugar libre en cada lado y autos que caben, velocidades de giro antes y
despues, la tabla carril a carril y los enlaces del semaforo con la letra de cada uno en cada fase del plan.
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
LIMA = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import armar_ovalo as ao  # noqa: E402
import plan_ovalo as po   # noqa: E402
import regenerar_demanda  # noqa: E402

sumolib = ao.sumolib
ESTUDIO = os.path.join(AQUI, "entrada", "red_estudio", "lima.net.xml")
RUTAS_ESTUDIO = os.path.join(AQUI, "entrada", "rutas_estudio")
CARPETAS = {"": "publicada", "alta": "alta", os.path.join("robustez", "reducto"): os.path.join("robustez", "reducto"),
            os.path.join("robustez", "transversal"): os.path.join("robustez", "transversal")}
LADOS = {"norte (28 de Julio hacia Larco)": ("NO", "NE", "NE_NO"), "oeste (Reducto hacia el sur)": ("NO", "SO", "NO_SO"),
         "sur (Balboa hacia el puente)": ("SO", "SE", "SO_SE"), "este (Reducto hacia el norte)": ("NE", "SE", "SE_NE")}
SIN_CAMBIOS = ("B_S1", "J_S1", "S1_L", "S1_RN", "S1_RS", "S1_J")      # con los carriles de la red del estudio
E2_LARGO = 75.0


def caben(largo):
    """Autos de 5 m detenidos uno tras otro con 2.5 m entre ellos (como medido/LEEME.md)."""
    return 0 if largo < 5.0 else 1 + int((largo - 5.0) // 7.5)


def detectores(ruta):
    raiz = ET.parse(ruta).getroot()
    return {d.get("id"): (d.get("lane"), round(float(d.get("pos")), 2), round(float(d.get("endPos")), 2))
            for d in raiz.findall("laneAreaDetector")}


def flujos(ruta):
    with open(ruta, encoding="utf-8") as f:
        return [l.strip() for l in f if "<flow " in l]


def salidas_de(net, carril):
    """{salida: [camino]} siguiendo las conexiones carril a carril de la red desde un carril de entrada."""
    arista_salida = {arista: d for d, arista in ao.ARISTA_SALIDA.items()}
    res, pila = {}, [[carril]]
    while pila:
        camino = pila.pop()
        lane = net.getLane(camino[-1])
        arista = lane.getEdge().getID()
        if arista in arista_salida:
            res.setdefault(arista_salida[arista], []).append(camino)
            continue
        siguientes = [c.getToLane().getID() for c in lane.getOutgoing()]
        if not siguientes or len(camino) > 12:
            res.setdefault("(sin salida)", []).append(camino)
            continue
        pila += [camino + [s] for s in siguientes]
    return res


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    fallas, lineas = [], []
    estudio = sumolib.net.readNet(ESTUDIO, withInternal=False)
    numero = {**{e: v[2] for e, v in ao.AFUERA.items()}, **{e: v[2] for e, v in ao.CARRILES_INTERNOS.items()}}
    for sub, fuente in CARPETAS.items():
        donde = os.path.join(LIMA, sub)
        nombre = sub or "lima (publicada)"
        ruta_red = os.path.join(donde, "lima.net.xml")
        net = sumolib.net.readNet(ruta_red, withInternal=True, withPrograms=True)
        # afuera y adentro: aristas, carriles, velocidad y largo
        for eid in ao.AFUERA:
            a, b = net.getEdge(eid), estudio.getEdge(eid)
            if a.getLaneNumber() != numero[eid] or abs(a.getSpeed() - b.getSpeed()) > 1e-6:
                fallas.append(f"{nombre}: {eid} no tiene los carriles de DISPOSICION o la velocidad del estudio")
            if eid in SIN_CAMBIOS and a.getLaneNumber() != b.getLaneNumber():
                fallas.append(f"{nombre}: {eid} no tiene los carriles de la red del estudio")
            difs = [abs(la.getLength() - b.getLanes()[0].getLength()) for la in a.getLanes()]
            if max(difs) > 0.02:
                fallas.append(f"{nombre}: {eid} difiere {max(difs):.3f} m del estudio")
        aristas = {e.getID(): e.getLaneNumber() for e in net.getEdges() if not e.isSpecial()}
        if aristas != numero:
            fallas.append(f"{nombre}: las aristas o sus carriles no son los del constructor: "
                          f"{sorted(set(aristas.items()) ^ set(numero.items()))}")
        # carril a carril: cada carril de entrada llega exactamente a las salidas de DISPOSICION
        movimientos = set()
        for o, arista in ao.ARISTA_ENTRADA.items():
            for lane in net.getEdge(arista).getLanes():
                llegadas = salidas_de(net, lane.getID())
                pedidas = set(ao.DISPOSICION[o][lane.getIndex()]) if lane.getIndex() < len(ao.DISPOSICION[o]) else set()
                if set(llegadas) != pedidas:
                    fallas.append(f"{nombre}: {lane.getID()} llega a {sorted(llegadas)} y DISPOSICION dice {sorted(pedidas)}")
                for d, caminos in llegadas.items():
                    movimientos.add((o, d))
                    for camino in caminos:
                        if [c.rsplit("_", 1)[0] for c in camino] != ao.CAMINOS.get((o, d)):
                            fallas.append(f"{nombre}: {' > '.join(camino)} no es el camino de {o}>{d}")
        if movimientos != set(ao.CAMINOS) or any(o == d for o, d in movimientos):
            fallas.append(f"{nombre}: los movimientos de la red no son los {len(ao.CAMINOS)} del constructor")
        # detectores E2: los de esta red
        e2 = detectores(os.path.join(donde, "e2_lima_75.add.xml"))
        entradas = [l for e in po.ENTRADA for l in net.getEdge(e).getLanes()]
        esperados = {f"e2_{l.getID()}": (l.getID(), round(max(0.0, l.getLength() - E2_LARGO), 2), round(l.getLength(), 2))
                     for l in entradas}
        if e2 != esperados or len(entradas) != 15:
            fallas.append(f"{nombre}: los detectores E2 no son los 15 de esta red (75 m antes de cada linea de parada)")
        # demanda
        f_ovalo = flujos(os.path.join(donde, "lima.rou.xml"))
        f_estudio = flujos(os.path.join(RUTAS_ESTUDIO, fuente, "lima.rou.xml"))
        sin_via = [re.sub(r' via="[^"]*"', "", f) for f in f_ovalo]
        if sin_via != f_estudio or not all(' via="' in f for f in f_ovalo):
            fallas.append(f"{nombre}: la demanda no es la de entrada/rutas_estudio con su camino en via")
        with open(os.path.join(donde, "lima.sumocfg"), encoding="utf-8") as f:
            cfg = f.read()
        if '<ignore-junction-blocker value="10"/>' not in cfg or '<time-to-teleport value="-1"/>' not in cfg:
            fallas.append(f"{nombre}: el .sumocfg no lleva la valvula de 10 s o tiene teletransportes")
        # semaforo: nodos, enlaces, conexiones sin semaforo
        tls = net.getTLS(po.TLS)
        nodos = sorted({c[0].getEdge().getToNode().getID() for c in tls.getConnections()})
        de_la_red = sorted((l.getEdge().getID(), c.getToLane().getEdge().getID(), l.getIndex(), c.getToLane().getIndex())
                           for e in net.getEdges() if not e.isSpecial() for l in e.getLanes() for c in l.getOutgoing())
        del_semaforo = sorted((a.getEdge().getID(), b.getEdge().getID(), a.getIndex(), b.getIndex())
                              for a, b, _ in tls.getConnections())
        if nodos != sorted(ao.NODOS_SEMAFORO) or del_semaforo != sorted(ao.CONEXIONES) or de_la_red != del_semaforo:
            fallas.append(f"{nombre}: semaforo_S1 no maneja los 10 nodos del ovalo con un enlace por conexion del "
                          f"constructor ({len(ao.CONEXIONES)})")
        lentos = [l.getID() for e in net.getEdges(withInternal=True) if e.isSpecial() for l in e.getLanes()
                  if l.getSpeed() < ao.VEL_GIRO_MIN - 1e-6]
        if lentos:
            fallas.append(f"{nombre}: tramos internos por debajo de {ao.VEL_GIRO_MIN} m/s: {lentos}")
        # el plan actual y el programa libre: los que da la regla sobre la red de la carpeta
        plan = po.Plan(ruta_red)
        regla = [(str(dur), estado) for dur, estado, _ in plan.fases([v for _, v, _ in po.pe.PLAN])]
        with open(os.path.join(donde, "lima.add.xml"), encoding="utf-8") as f:
            aqui = re.findall(r'duration="(\d+)" state="([^"]+)"', f.read())
        if aqui != regla or [d for d, _ in aqui] != ["37", "3", "15", "3", "34", "37", "3"]:
            fallas.append(f"{nombre}: el plan actual no tiene las duraciones del plan o las letras de la regla")
        fases_l, verde, ambar, rojo = plan.fases_libres()
        with open(os.path.join(donde, "lima_libre.json"), encoding="utf-8") as f:
            libre = json.load(f)
        if (libre["fases"] != [[n, l] for n, l in fases_l] or libre["verde"] != [list(x) for x in verde]
                or libre["ambar"] != [list(x) for x in ambar] or libre["rojo"] != [list(x) for x in rojo]):
            fallas.append(f"{nombre}: lima_libre.json no tiene las fases de la regla del orden libre")
        if plan.avisos:
            fallas.append(f"{nombre}: enlaces que chocan con prioridad: {sorted(set(plan.avisos))}")
        sin_uso = [plan.texto_enlace(i) for i in range(plan.red.n) if not plan.usos[i]]
        if sin_uso:
            fallas.append(f"{nombre}: enlaces que no usa ningun movimiento (rojo para siempre): {sin_uso}")
        verdes = [estado for _, estado, nombre_fase in plan.fases([v for _, v, _ in po.pe.PLAN])
                  if nombre_fase not in po.pe.NO_VERDES]
        for lane in entradas:
            estados = {k for k, estado in enumerate(verdes) for i, e in plan.red.enlaces.items()
                       if e["desde"] == lane.getID() and estado[i] == "G"}
            if len(estados) != 1:
                fallas.append(f"{nombre}: {lane.getID()} tiene verde en {len(estados)} estados del plan")
        # los carriles de entrada de cada estado, leidos de las letras, son los de la tabla (asi los deduce rl_ippo.py)
        for k, estado in enumerate(verdes):
            de_las_letras = {e["desde"] for i, e in plan.red.enlaces.items() if plan.afuera(i) and estado[i] == "G"}
            de_la_tabla = {f"{ao.ARISTA_ENTRADA[o]}_{c}" for (o, d) in plan.estados[k] for c in ao.CARRILES_ENTRADA[(o, d)]}
            if de_las_letras != de_la_tabla:
                fallas.append(f"{nombre}: los carriles con verde en el estado {k + 1} no son los de DISPOSICION")
        # lo que la red marca como giro a la izquierda en las lineas de parada (la lectura giro_izq de rl_ippo.py) sale
        # exactamente de los carriles de Reducto que solo giran a la izquierda
        giran = {l.getID() for l in entradas for c in l.getOutgoing() if c.getDirection() in ("l", "L")}
        solo_giro = {f"{ao.ARISTA_ENTRADA[o]}_{c}" for o, p in ao.REDUCTO.items()
                     for c, destinos in enumerate(ao.DISPOSICION[o]) if set(destinos) == {p["giro"][0]}}
        if giran != solo_giro:
            fallas.append(f"{nombre}: los carriles con giro a la izquierda en su linea de parada son {sorted(giran)} y "
                          f"debian ser {sorted(solo_giro)}")
        lineas.append(f"{nombre}: {len(f_ovalo)} flujos de {len(movimientos)} movimientos, {len(e2)} detectores E2, "
                      f"{len(tls.getConnections())} enlaces, {len(aristas)} aristas")
    # la demanda: la regla, los carriles de GRUPOS frente a la red y los totales (regenerar_demanda.py)
    problemas, tablas, total = regenerar_demanda.comprobar()
    fallas += [f"demanda: {p}" for p in problemas]
    lineas.append("demanda (veh/h): " + ", ".join(f"{caso} {t:.2f}" for caso, t in total.items())
                  + f"; carriles de la regla = carriles de la red: {'si' if not problemas else 'ver fallas'}")
    # resumen de la red
    red = os.path.join(LIMA, "lima.net.xml")
    net = sumolib.net.readNet(red, withInternal=True)
    with open(os.path.join(AQUI, "red", "ovalo_estudio.alargues.json"), encoding="utf-8") as f:
        puntos = json.load(f)["puntos"]
    res = ["Red del estudio del nudo en el Ovalo Vasco (lima/lima.net.xml = lima/ovalo/red/ovalo_estudio.net.xml)", "",
           "1. Lados del ovalo: de esquina a esquina (medidas de Fabian en Google Maps) y lugar libre para esperar "
           "(largo de carril entre los bordes de sus esquinas; autos de 5 m con 2.5 m entre ellos)"]
    for nombre, (a, b, arista) in LADOS.items():
        d = ao.dist(puntos[a], puntos[b])
        largo = net.getEdge(arista).getLanes()[0].getLength()
        res.append(f"   {nombre:34s} {a}-{b} {d:5.2f} m; libre {largo:4.1f} m; {net.getEdge(arista).getLaneNumber()} "
                   f"carriles; caben {caben(largo)} por carril")
    res.append("   Antes de la primera esquina: 28 de Julio (J_NE) "
               f"{net.getEdge('J_NE').getLanes()[0].getLength():.1f} m, Balboa (B_SO) "
               f"{net.getEdge('B_SO').getLanes()[0].getLength():.1f} m")
    res.append("   Ramales de giro: " + ", ".join(
        f"{e} {net.getEdge(e).getLaneNumber()} x {net.getEdge(e).getLanes()[0].getLength():.1f} m"
        for e in ("RN_NE", "NE_MJ", "RS_SO", "SO_ML", "B_ML") if e in ao.CARRILES_INTERNOS))
    res += ["", "2. Velocidad de los giros: red/ovalo_estudio.giros.txt (antes y despues, con su largo). Subidos a "
            f"{ao.VEL_GIRO_MIN} m/s:"]
    with open(os.path.join(AQUI, "red", "ovalo_estudio.giros.txt"), encoding="utf-8") as f:
        res += ["   " + l.rstrip() for l in f if "<- subido" in l or l.startswith("Tramos internos:")]
    plan = po.Plan(red)
    fases = plan.fases([v for _, v, _ in po.pe.PLAN])
    fases_l = plan.fases_libres()[0]
    res += ["", f"3. Semaforo semaforo_S1: {plan.red.n} enlaces en {len(ao.NODOS_SEMAFORO)} nodos (4 lineas de parada "
            "de afuera, 4 esquinas y 2 uniones). Letras en las 7 fases del plan (verde, ambar y todo rojo) y "
            f"{len(fases_l)} fases del programa del orden libre (lima/lima_libre.json).",
            "   G/g verde con o sin prioridad, y ambar, r rojo, O/o apagada con o sin prioridad",
            "   " + " ".join(f"{k + 1}" for k in range(len(fases))) + "  <- fases del plan: " + ", ".join(
                f"{k + 1} {nombre}" for k, (_, _, nombre) in enumerate(fases))]
    for i in range(plan.red.n):
        e = plan.red.enlaces[i]
        letras = " ".join(estado[i] for _, estado, _ in fases)
        movs = ", ".join(sorted(f"{o}>{d}" for o, d in plan.usos[i]))
        res.append(f"   {letras}  {i:2d} {e['nodo']:4s} {e['desde']:8s} -> {e['hacia']:8s} {movs}")
    res += ["", f"4. Carriles de cada entrada (DISPOSICION, armar_ovalo.py) y su camino carril a carril en la red armada: "
            f"{len(ao.CAMINOS)} movimientos"]
    nombres = {"L": "Larco", "J": "el puente", "RN": "Reducto norte", "RS": "Reducto sur"}
    for o, arista in ao.ARISTA_ENTRADA.items():
        res.append(f"   {arista} ({net.getEdge(arista).getLaneNumber()} carriles; el 0 es el de la derecha)")
        for lane in net.getEdge(arista).getLanes():
            for d, caminos in sorted(salidas_de(net, lane.getID()).items()):
                for camino in caminos:
                    res.append(f"      {lane.getID()} -> {nombres.get(d, d):14s} {' -> '.join(camino[1:])}")
    res += ["", "5. Comprobaciones (aristas y carriles, carril a carril, detectores, demanda, .sumocfg, semaforo, giros, "
            "plan actual y programa libre):"]
    res += ["   " + l for l in lineas]
    res.append("   " + ("todas bien" if not fallas else "FALLAS: " + "; ".join(fallas)))
    texto = "\n".join(res) + "\n"
    with open(os.path.join(AQUI, "red", "resumen_estudio.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    print(texto)
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
