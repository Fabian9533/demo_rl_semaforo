"""
dibujar_red.py - Dibuja la red limpia del caso Lima (red/lima.net.xml) para compararla con el cruce real.

Uso (desde demo_rl/lima):  python dibujar_red.py
Escribe red/lima_nudo.png: el nudo, con los movimientos de cada entrada en su color. Cada linea es un carril; la flecha marca el sentido. Solo lee la red.
"""
import math
import os
import sys

if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
import sumolib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
RED = os.path.join(AQUI, "lima.net.xml")
# paleta que se distingue tambien en gris y con daltonismo (Okabe-Ito)
COLOR = {"RN_S1": "#0072B2", "RS_S1": "#D55E00", "B_S1": "#009E73", "J_S1": "#CC79A7"}
NOMBRE = {"RN_S1": "Reducto, desde el norte", "RS_S1": "Reducto, desde el sur", "B_S1": "Balboa",
          "J_S1": "28 de Julio, desde el puente", "S1_L": "28 de Julio, hacia Larco", "S1_RN": "Reducto, hacia el norte",
          "S1_RS": "Reducto, hacia el sur", "S1_J": "28 de Julio, hacia el puente",
          "AN_S2": "Auxiliar de Paseo de la República (va al sur)", "S2_AS": "Auxiliar, hacia el sur",
          "AS_S3": "Auxiliar de Paseo de la República (va al norte)", "S3_AN": "Auxiliar, hacia el norte",
          "E_S3": "28 de Julio, desde el este", "S3_E": "28 de Julio, hacia el este",
          "S2_S3": "puente", "S3_S2": "puente"}


def flecha(ax, forma, color, donde=0.6, tam=9):
    """Punta de flecha sobre la polilinea, a la fraccion `donde` de su largo."""
    tramos = [math.hypot(forma[i + 1][0] - forma[i][0], forma[i + 1][1] - forma[i][1]) for i in range(len(forma) - 1)]
    meta, acum = sum(tramos) * donde, 0.0
    for i, t in enumerate(tramos):
        if acum + t >= meta and t > 0:
            f = (meta - acum) / t
            x = forma[i][0] + f * (forma[i + 1][0] - forma[i][0])
            y = forma[i][1] + f * (forma[i + 1][1] - forma[i][1])
            ux, uy = (forma[i + 1][0] - forma[i][0]) / t, (forma[i + 1][1] - forma[i][1]) / t
            ax.annotate("", xy=(x + ux, y + uy), xytext=(x - ux, y - uy),
                        arrowprops=dict(arrowstyle="-|>", color=color, lw=0, mutation_scale=tam), zorder=6)
            return
        acum += t


def curva(entra, sale, n=24):
    """Curva de Bezier cubica del ultimo punto del carril `entra` al primero del carril `sale`, tangente a los dos."""
    (ax, ay), (bx, by) = entra[-2], entra[-1]
    (cx, cy), (dx, dy) = sale[0], sale[1]
    largo = math.hypot(cx - bx, cy - by) * 0.4
    u = math.hypot(bx - ax, by - ay) or 1.0
    v = math.hypot(dx - cx, dy - cy) or 1.0
    p1 = (bx + (bx - ax) / u * largo, by + (by - ay) / u * largo)
    p2 = (cx - (dx - cx) / v * largo, cy - (dy - cy) / v * largo)
    puntos = []
    for i in range(n + 1):
        t = i / n
        k0, k1, k2, k3 = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        puntos.append((k0 * bx + k1 * p1[0] + k2 * p2[0] + k3 * cx, k0 * by + k1 * p1[1] + k2 * p2[1] + k3 * cy))
    return puntos


def dibujar(net, centro, radio, salida, titulo, con_movimientos):
    cx, cy = centro
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_facecolor("#f4f3ef")
    for e in net.getEdges(withInternal=False):
        for carril in e.getLanes():
            forma = carril.getShape()
            xs, ys = [p[0] for p in forma], [p[1] for p in forma]
            ax.plot(xs, ys, color="#b9b8b2", linewidth=7 if radio < 120 else 3.2, solid_capstyle="butt", zorder=1)
            ax.plot(xs, ys, color="white", linewidth=0.6, linestyle=(0, (6, 6)), zorder=2)
            flecha(ax, forma, "#3a3a38", 0.82 if e.getToNode().getID().startswith("S") else 0.3,
                   9 if radio < 120 else 6)
    if con_movimientos:
        for e in net.getEdges(withInternal=False):
            if e.getID() not in COLOR:
                continue
            for carril in e.getLanes():
                for con in carril.getOutgoing():
                    via = con.getViaLaneID()
                    forma = []
                    while via:                                     # la conexion puede tener varios tramos internos
                        interno = net.getLane(via)
                        forma += interno.getShape()
                        siguiente = interno.getOutgoing()
                        via = siguiente[0].getViaLaneID() if siguiente and siguiente[0].getViaLaneID() else None
                    if len(forma) < 2:
                        # red sin tramos internos: se dibuja una curva suave del final del carril de entrada al
                        # comienzo del de salida (no es una trayectoria simulada, solo dice a donde se puede ir)
                        forma = curva(carril.getShape(), con.getToLane().getShape())
                    ax.plot([p[0] for p in forma], [p[1] for p in forma], color=COLOR[e.getID()], linewidth=1.6,
                            alpha=0.9, zorder=4)
                    flecha(ax, forma, COLOR[e.getID()], 0.55, 11)
        for eid, color in COLOR.items():
            ax.plot([], [], color=color, linewidth=2.5, label=NOMBRE[eid] + f" ({net.getEdge(eid).getLaneNumber()} carriles)")
        # la leyenda va debajo del dibujo, para no tapar las calles ni sus nombres
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2, fontsize=9, frameon=False,
                  title="Movimientos de cada entrada", title_fontsize=9)
    for e in net.getEdges(withInternal=False):
        forma = e.getShape()
        entra = e.getToNode().getID().startswith("S")
        # la etiqueta va a 55-70 m del cruce (o al medio si el tramo es corto)
        total = e.getLength()
        d = min(total / 2, radio * (0.52 if entra else 0.36))    # entradas y salidas a distinta altura: no se pisan
        pos = sumolib.geomhelper.positionAtShapeOffset(forma, total - d if entra else d)
        if abs(pos[0] - cx) > radio * 0.93 or abs(pos[1] - cy) > radio * 0.93:
            continue
        texto = NOMBRE.get(e.getID(), e.getID())
        if not con_movimientos or e.getID() not in COLOR:
            texto += f" ({e.getLaneNumber()})"
        ax.text(pos[0], pos[1], texto, fontsize=7.5, ha="center", va="center", zorder=7,
                color=COLOR.get(e.getID(), "#1c1c1a") if con_movimientos else "#1c1c1a",
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1.2))
    for n in net.getNodes():
        if n.getType() == "traffic_light":
            x, y = n.getCoord()
            if abs(x - cx) <= radio and abs(y - cy) <= radio:
                ax.text(x, y, n.getID(), fontsize=10, fontweight="bold", ha="center", va="center", zorder=8,
                        bbox=dict(boxstyle="circle,pad=0.25", facecolor="#ffd94a", edgecolor="black"))
    ax.set_xlim(cx - radio, cx + radio)
    ax.set_ylim(cy - radio, cy + radio)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    escala = 20 if radio < 120 else 50
    ax.plot([cx - radio * 0.92, cx - radio * 0.92 + escala], [cy - radio * 0.92] * 2, color="black", lw=2.5, zorder=9)
    ax.text(cx - radio * 0.92 + escala / 2, cy - radio * 0.92 + radio * 0.025, f"{escala} m", ha="center", fontsize=9)
    if titulo:
        ax.set_title(titulo, fontsize=10)
    fig.tight_layout()
    fig.savefig(salida, dpi=110 if titulo else 200, bbox_inches="tight")
    plt.close(fig)
    print("Escrito", salida)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    net = sumolib.net.readNet(RED, withInternal=True)
    s1 = net.getNode("S1").getCoord()
    if "--tesis" in sys.argv:          # la figura del Anexo D: sin titulo (lo lleva el pie de la figura)
        dibujar(net, s1[:2], 75, os.path.join(os.path.dirname(AQUI), "TESIS", "images", "fig_lima_nudo.png"), "", True)
        return
    dibujar(net, s1[:2], 75, os.path.join(AQUI, "red", "lima_nudo.png"),
            "Caso Lima: el nudo. Norte arriba. Cada línea gris es un carril; en color, a dónde puede ir cada entrada.",
            True)


if __name__ == "__main__":
    main()
