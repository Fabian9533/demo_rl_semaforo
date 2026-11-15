"""
armar_red.py - Arma la red del caso Lima: el nudo de Av. Reducto, Av. 28 de Julio y Av. Vasco Nunez de Balboa,
en Miraflores (12 07 45.0 S, 77 01 25.6 O). Es un solo cruce con semaforo, semaforo_S1.

Uso (desde demo_rl/lima):  python armar_red.py
Lee borrador/lima_reducto.net.xml (la conversion cruda de OpenStreetMap; ver bajar_osm.py y borrador/union.nod.xml)
solo para tomar la GEOMETRIA real: la posicion del nudo y el trazado de cada calle. Los carriles y los movimientos
permitidos NO salen de OpenStreetMap: salen de la descripcion de campo de Fabian (lima.pdf, 13.11.2026) donde la
hay, y de OpenStreetMap donde todavia falta confirmar (marcado "OSM, por confirmar").
Escribe red/lima.nod.xml, red/lima.edg.xml y red/lima.con.xml y llama a netconvert: lima.net.xml.

Aristas "<origen>_<destino>": RN = Reducto norte, RS = Reducto sur, B = Balboa, J = 28 de Julio del lado del puente
de la Via Expresa, L = 28 de Julio hacia Larco. Los dos semaforos del puente (a 80 y 145 m) NO estan en la red: se
decidio evaluar solo el nudo (13.11.2026), asi que 28 de Julio se modela como una calle continua.
El programa del semaforo que queda dentro de lima.net.xml es el que adivina netconvert y no se usa: el programa
de cada control va en un archivo aparte (programa.py).
"""
import argparse
import math
import os
import subprocess
import sys

if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
import sumolib

AQUI = os.path.dirname(os.path.abspath(__file__))
CRUDA = os.path.join(AQUI, "borrador", "lima_reducto.net.xml")
PLANO = os.path.join(AQUI, "red")
VEL = 13.89                    # 50 km/h, limite de las avenidas de Lima
TRAZADO_ENTRADA = 300.0        # m de trazado real (OpenStreetMap) de cada entrada, pegados al nudo
LARGO_ENTRADA = 1000.0         # m totales de cada entrada: lo que pasa del trazado real es una recta, para que
                               # la cola quepa dentro de la red y el modelo la vea (piloto del 13.11.2026)
LARGO_SALIDA = 180.0           # m de calle despues del nudo

NUDO_OSM = "cluster_10092527760_10092527761_10092527765_10092527767_#5more"

# arista nueva: (arista de OSM pegada al nudo, sentido en que se recorre la calle para completar el largo,
#                nodo de origen, nodo de destino, carriles, de donde sale el numero de carriles)
ARISTAS = {
    # --- entradas ---
    "RN_S1": ("653645242#0", "arriba", "RNe", "S1", 4, "Fabian: 4; el de la izquierda solo gira a la izquierda"),
    "RS_S1": ("653650083", "arriba", "RSe", "S1", 5, "Fabian (13.11): 3 de la avenida y 2 solo para girar a la izquierda"),
    "B_S1": ("653645248", "arriba", "Be", "S1", 3, "Fabian: 3; el del medio de frente, los laterales pueden girar"),
    "J_S1": ("24315794#0", "arriba", "Je", "S1", 3, "Fabian: 3 por sentido"),
    # --- salidas ---
    "S1_L": ("291058249", "abajo", "S1", "Ls", 2, "Fabian (13.11): 2; coincide con OSM"),
    "S1_RN": ("365935498#0", "abajo", "S1", "RNs", 2, "Fabian (13.11): 2; coincide con OSM"),
    "S1_RS": ("243364007#0", "abajo", "S1", "RSs", 3, "OSM"),
    "S1_J": ("653645247", "abajo", "S1", "Js", 3, "Fabian: 3 por sentido"),
}

# Movimientos (lima.pdf y respuestas de Fabian del 13.11.2026): (desde, hacia): [(carril de origen, carril de
# destino)]; el carril 0 es el de la derecha. Cada carril de destino recibe un solo carril de cada entrada: asi dos
# carriles de la misma entrada no se disputan el mismo carril dentro del nudo.
MOVIMIENTOS = {
    # Reducto desde el norte: el carril izquierdo (3) solo gira a la izquierda, hacia el puente, con su semaforo;
    # los otros tres van de frente y el derecho tambien gira hacia Larco
    ("RN_S1", "S1_J"): [(3, 2)],
    ("RN_S1", "S1_RS"): [(0, 0), (1, 1), (2, 2)],
    ("RN_S1", "S1_L"): [(0, 0)],
    # Reducto desde el sur: el carril derecho (0) solo gira a la derecha, hacia el puente; dos carriles de frente
    # (Reducto sigue hacia el norte con dos carriles) y dos carriles (3 y 4) solo para girar a la izquierda, hacia
    # Larco, con su semaforo. En el sitio esos dos carriles son un ensanche corto antes del cruce; aqui son carriles
    # completos (simplificacion declarada).
    ("RS_S1", "S1_J"): [(0, 0)],
    ("RS_S1", "S1_RN"): [(1, 0), (2, 1)],
    ("RS_S1", "S1_L"): [(3, 0), (4, 1)],
    # Balboa: los tres carriles siguen hacia el puente; el derecho tambien gira hacia Reducto sur y el izquierdo
    # tambien sube hacia Reducto norte. El giro de Balboa hacia Larco NO esta en el modelo: entra al mismo carril que
    # 28 de Julio durante el mismo verde, no hay conteo de cuantos lo hacen y en el simulador no encuentra hueco.
    ("B_S1", "S1_RS"): [(0, 0)],
    ("B_S1", "S1_J"): [(0, 0), (1, 1), (2, 2)],
    ("B_S1", "S1_RN"): [(2, 1)],
    # 28 de Julio desde el puente: dos carriles siguen hacia Larco (la salida tiene dos) y el derecho tambien gira
    # hacia Reducto norte; el izquierdo solo gira hacia Reducto sur, cediendo el paso a Balboa
    ("J_S1", "S1_RN"): [(0, 0)],
    ("J_S1", "S1_L"): [(0, 0), (1, 1)],
    ("J_S1", "S1_RS"): [(2, 2)],
}


def largo(forma):
    return sum(math.hypot(forma[i + 1][0] - forma[i][0], forma[i + 1][1] - forma[i][1]) for i in range(len(forma) - 1))


def recortar(forma, maximo, desde_el_final):
    """Deja a lo sumo `maximo` metros de la polilinea, contados desde el final (entradas) o desde el inicio."""
    if desde_el_final:
        return list(reversed(recortar(list(reversed(forma)), maximo, False)))
    salida, acum = [forma[0]], 0.0
    for a, b in zip(forma, forma[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        if acum + d >= maximo:
            t = (maximo - acum) / d if d else 0.0
            salida.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
            return salida
        salida.append(b)
        acum += d
    return salida


def prolongar(forma, metros):
    """Punto que alarga la polilinea `metros` hacia atras, en linea recta con su primer tramo (de 20 m o mas)."""
    x0, y0 = forma[0]
    x1, y1 = next((p for p in forma[1:] if math.hypot(p[0] - x0, p[1] - y0) >= 20.0), forma[-1])
    d = math.hypot(x1 - x0, y1 - y0)
    return (x0 - metros * (x1 - x0) / d, y0 - metros * (y1 - y0) / d)


def cadena(net, eid, sentido, maximo):
    """Trazado de la calle a partir de la arista eid, siguiendo la misma calle hacia arriba (entradas) o hacia abajo
    (salidas) hasta completar `maximo` metros o hasta que la calle se bifurque o termine."""
    e = net.getEdge(eid)
    partes, total, act = [e], e.getLength(), e
    while total < maximo:
        if sentido == "arriba":          # se descarta el sentido contrario de la misma calle (vuelta en U)
            vecinas = [v for v in act.getFromNode().getIncoming() if v.getFromNode() != act.getToNode()]
        else:
            vecinas = [v for v in act.getToNode().getOutgoing() if v.getToNode() != act.getFromNode()]
        mismas = [v for v in vecinas if v.getName() == act.getName() and v.getName()]
        if len(mismas) != 1:
            break
        act = mismas[0]
        partes.append(act)
        total += act.getLength()
    if sentido == "arriba":
        partes.reverse()
    forma = []
    for p in partes:
        for punto in p.getShape():
            if not forma or math.hypot(punto[0] - forma[-1][0], punto[1] - forma[-1][1]) > 0.5:
                forma.append(punto)
    return forma, [p.getID() for p in partes]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", type=float, default=LARGO_ENTRADA,
                    help="m totales de cada entrada: el trazado real y, antes, una recta donde quepa la cola")
    args = ap.parse_args()
    net = sumolib.net.readNet(CRUDA, withInternal=False)
    os.makedirs(PLANO, exist_ok=True)
    centro = net.getNode(NUDO_OSM).getCoord()[:2]
    nodos = {"S1": (centro[0], centro[1], "traffic_light")}
    lineas_e = []
    for nombre, (eid, sentido, desde, hacia, carriles, fuente) in ARISTAS.items():
        maximo = TRAZADO_ENTRADA if sentido == "arriba" else LARGO_SALIDA
        forma, usadas = cadena(net, eid, sentido, maximo)
        forma = recortar(forma, maximo, sentido == "arriba")
        if sentido == "arriba" and args.entrada > largo(forma) + 1.0:
            forma = [prolongar(forma, args.entrada - largo(forma))] + forma
        if desde == "S1":                 # la arista va de nodo a nodo: el centro del nudo va en la punta que lo toca
            forma = [centro] + forma
            nodos[hacia] = (forma[-1][0], forma[-1][1], "priority")
        else:
            forma = forma + [centro]
            nodos[desde] = (forma[0][0], forma[0][1], "priority")
        puntos = " ".join(f"{x:.2f},{y:.2f}" for x, y in forma)
        lineas_e.append(f'    <edge id="{nombre}" from="{desde}" to="{hacia}" numLanes="{carriles}" speed="{VEL}" '
                        f'spreadType="center" shape="{puntos}"/>  <!-- {largo(forma):.0f} m; OSM {", ".join(usadas)}; '
                        f'carriles: {fuente} -->')
        print(f"{nombre:6s} {desde:>3s} -> {hacia:<3s} {carriles} carriles, {largo(forma):4.0f} m  ({fuente})")

    cabeza = '<?xml version="1.0" encoding="UTF-8"?>\n<!-- Generado por armar_red.py. No editar a mano. -->\n'
    with open(os.path.join(PLANO, "lima.nod.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(cabeza + "<nodes>\n")
        for nid, (x, y, tipo) in nodos.items():
            extra = f' tl="semaforo_{nid}"' if tipo == "traffic_light" else ""
            f.write(f'    <node id="{nid}" x="{x:.2f}" y="{y:.2f}" type="{tipo}"{extra}/>\n')
        f.write("</nodes>\n")
    with open(os.path.join(PLANO, "lima.edg.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(cabeza + "<edges>\n" + "\n".join(lineas_e) + "\n</edges>\n")
    with open(os.path.join(PLANO, "lima.con.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(cabeza + "<connections>\n")
        for (desde, hacia), pares in MOVIMIENTOS.items():
            for c_de, c_a in pares:
                f.write(f'    <connection from="{desde}" to="{hacia}" fromLane="{c_de}" toLane="{c_a}"/>\n')
        f.write("</connections>\n")

    orden = ["netconvert", "--node-files", os.path.join(PLANO, "lima.nod.xml"),
             "--edge-files", os.path.join(PLANO, "lima.edg.xml"),
             "--connection-files", os.path.join(PLANO, "lima.con.xml"),
             "--output-file", os.path.join(AQUI, "lima.net.xml"),
             "--no-turnarounds", "--junctions.corner-detail", "5", "--tls.default-type", "static",
             # sin tramos internos: dentro del nudo no se simulan las trayectorias (un vehiculo que cruza la linea
             # aparece en su carril de salida). Con ellos, los movimientos de Balboa y de 28 de Julio que se cruzan
             # en su verde compartido quedaban detenidos mas de 15 minutos y bloqueaban a Reducto (13.11.2026).
             "--no-internal-links"]
    r = subprocess.run(orden, capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-1500:])
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
