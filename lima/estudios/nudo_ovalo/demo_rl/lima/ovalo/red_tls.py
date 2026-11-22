"""
red_tls.py - Lectura del semaforo unico del ovalo en una red ya armada: enlaces, esquina de cada enlace, conflictos y
quien cede a quien segun la matriz de cada esquina (elementos <request> de la red). Lo usan programa_ovalo.py y
comprobar.py.

Uso suelto (para mirar):  python -B programas/red_tls.py red/ovalo.net.xml
"""
import os
import sys
import xml.etree.ElementTree as ET

sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
import sumolib  # noqa: E402

TLS = "semaforo_S1"


class RedTLS:
    """enlaces[i] = {"nodo", "desde" (carril), "hacia" (carril), "via", "local" (indice en la matriz de su nodo)}.
    choca(i, j): los dos enlaces estan en el mismo nodo y SUMO los marca como conflicto (cruce o union).
    cede(i, j): segun la matriz de su nodo, i debe ceder el paso a j cuando i no tiene prioridad (letra g u o)."""

    def __init__(self, ruta, tls=TLS):
        self.ruta = ruta
        self.net = sumolib.net.readNet(ruta, withInternal=True, withPrograms=True)
        self.tls = tls
        raiz = ET.parse(ruta).getroot()
        self.matriz = {}
        for j in raiz.findall("junction"):
            if j.get("type") == "internal":
                continue
            filas = {int(r.get("index")): (r.get("foes"), r.get("response")) for r in j.findall("request")}
            if filas:
                self.matriz[j.get("id")] = filas
        self.enlaces = {}
        for entrada, salida, i in self.net.getTLS(tls).getConnections():
            nodo = entrada.getEdge().getToNode()
            con = [c for c in entrada.getOutgoing() if c.getToLane() == salida][0]
            self.enlaces[i] = {"nodo": nodo.getID(), "desde": entrada.getID(), "hacia": salida.getID(),
                               "via": con.getViaLaneID(), "local": nodo.getLinkIndex(con), "con": con}
        self.n = len(self.enlaces)

    def _bit(self, cadena, k):
        return cadena[len(cadena) - 1 - k] == "1"

    def choca(self, i, j):
        a, b = self.enlaces[i], self.enlaces[j]
        if a["nodo"] != b["nodo"] or i == j:
            return False
        foes = self.matriz[a["nodo"]][a["local"]][0]
        return self._bit(foes, b["local"])

    def cede(self, i, j):
        a, b = self.enlaces[i], self.enlaces[j]
        if a["nodo"] != b["nodo"] or i == j:
            return False
        respuesta = self.matriz[a["nodo"]][a["local"]][1]
        return self._bit(respuesta, b["local"])

    def nodo(self, i):
        return self.enlaces[i]["nodo"]

    def arista_desde(self, i):
        return self.enlaces[i]["desde"].rsplit("_", 1)[0]

    def arista_hacia(self, i):
        return self.enlaces[i]["hacia"].rsplit("_", 1)[0]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    r = RedTLS(sys.argv[1])
    print(f"{r.n} enlaces en {r.tls}")
    for i, e in sorted(r.enlaces.items()):
        choques = [j for j in r.enlaces if r.choca(i, j)]
        cede_a = [j for j in choques if r.cede(i, j)]
        print(f"{i:3d} {e['nodo']:5s} {e['desde']:9s} -> {e['hacia']:9s} local {e['local']:2d}  choca con {choques}  "
              f"cede a {cede_a}")


if __name__ == "__main__":
    main()
