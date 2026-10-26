"""
figuras_redes.py - Figuras de las redes del plan dibujadas desde los archivos de SUMO (25.10.2026, pedido de Fabian:
"imagenes de como se ven las redes, con el sentido de cada carril y los giros").

Desde plan2/:
    python figuras_redes.py
Escribe en TESIS/images/:
  fig_redes.pdf/.png              las tres redes (corredor, red con rotonda, malla 3x3), con el sentido de cada carril y
                                  los semaforos, y un cruce ampliado con los movimientos permitidos y su tipo de verde
  fig_corredor_periodos.pdf/.png  el corredor en cada media hora: la punta de la avenida, las transversales y los
                                  cuatro giros (a la derecha en la primera, a la izquierda en la segunda)

Que sale de SUMO: la posicion de los cruces y la topologia (nodos y aristas del .net.xml, con sumolib), el numero de
carriles de cada arista y su orden (el 0 es el de la derecha), los movimientos de cada carril (conexiones r/s/l), el
tipo de verde de cada movimiento (estado G, con prioridad, o g, sin prioridad, del programa fijo del .add.xml) y los
flujos de cada media hora (corredor.rou.xml). El dibujo es esquematico: en la vista general los carriles se dibujan
mucho mas anchos que en la red (de 3.2 m en cruces a 300-400 m) para que se vean los dos sentidos; el cruce ampliado
usa la geometria real de SUMO.
"""
import os
import math
import xml.etree.ElementTree as ET

import sumolib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyArrowPatch, Circle, Wedge
from matplotlib.lines import Line2D

AQUI = os.path.dirname(os.path.abspath(__file__))
IMAGENES = os.path.join(os.path.dirname(AQUI), "TESIS", "images")

# paleta de las figuras de la tesis (curvas_demanda.py)
FONDO, TINTA, TINTA2, APAGADO = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
CALLE, BORDE = "#dcdad3", "#b7b4aa"
AZUL, NARANJA, VERDE = "#2a78d6", "#eb6834", "#1baf7a"
TRAZO_IZQ = (0, (2.4, 1.6))           # linea discontinua: giro a la izquierda, cede el paso

REDES = [("corredor", "corredor.net.xml", "corredor.add.xml", "Corredor (P1 y P2)"),
         ("red", "red.net.xml", "red.add.xml", "Red con rotonda (P3 y P4)"),
         ("malla3", "malla3.net.xml", "malla3.add.xml", "Malla 3 × 3 (P5 y P6)")]


def estados_fijo(add):
    """{tls: [estado de cada fase]} del programa fijo."""
    res = {}
    for tl in ET.parse(os.path.join(AQUI, add)).getroot().iter("tlLogic"):
        res[tl.get("id")] = [p.get("state") for p in tl.iter("phase")]
    return res


def flecha(ax, a, b, color, escala=7.0, lw=1.0, ls="-", z=4, alpha=1.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=escala, lw=lw, color=color, ls=ls,
                                 zorder=z, shrinkA=0, shrinkB=0, alpha=alpha))


def rectangulo(a, b, ancho):
    (x0, y0), (x1, y1) = a, b
    L = math.hypot(x1 - x0, y1 - y0) or 1.0
    nx, ny = -(y1 - y0) / L * ancho / 2, (x1 - x0) / L * ancho / 2
    return [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]


# ---------------- vista general esquematica ----------------

def dibujar_red(ax, net, W, titulo, rotulo_tls=True, flechas=True):
    """Cada carril como una franja de ancho W a su lado del eje de la calle (el carril 0 es el de la derecha, el mas
    alejado del eje), con flechas de sentido; cruces como cuadrados; semaforos en verde; rotondas como anillos."""
    nodos = list(net.getNodes())
    anillo = [n for n in nodos if n.getType() == "priority"
              and any(e.getToNode().getType() == "priority" for e in n.getOutgoing())]
    ids_anillo = {n.getID() for n in anillo}
    centro_anillo, radio_anillo = None, 0.0
    if anillo:
        cx = sum(n.getCoord()[0] for n in anillo) / len(anillo)
        cy = sum(n.getCoord()[1] for n in anillo) / len(anillo)
        centro_anillo = (cx, cy)
        radio_anillo = sum(math.hypot(n.getCoord()[0] - cx, n.getCoord()[1] - cy) for n in anillo) / len(anillo)
        radio_anillo = max(radio_anillo, 1.6 * W)

    def carriles_en(nodo):
        return max([e.getLaneNumber() for e in list(nodo.getIncoming()) + list(nodo.getOutgoing())] or [1])

    def es_cruce(nodo):
        return len(nodo.getIncoming()) + len(nodo.getOutgoing()) > 2 and nodo.getID() not in ids_anillo

    for e in net.getEdges():
        if e.isSpecial():
            continue
        a, b = e.getFromNode(), e.getToNode()
        if a.getID() in ids_anillo and b.getID() in ids_anillo:
            continue                                   # el anillo se dibuja aparte
        (x0, y0), (x1, y1) = a.getCoord(), b.getCoord()
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        nx, ny = uy, -ux                               # normal hacia la derecha del sentido de la arista
        def corte(nodo, extremo):
            if nodo.getID() in ids_anillo:
                return math.hypot(extremo[0] - centro_anillo[0], extremo[1] - centro_anillo[1]) * 0 + radio_anillo + W
            return (carriles_en(nodo) * W + 0.15 * W) if es_cruce(nodo) else 0.0
        if a.getID() in ids_anillo:
            x0, y0 = centro_anillo
        if b.getID() in ids_anillo:
            x1, y1 = centro_anillo
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        nx, ny = uy, -ux
        ra, rb = corte(a, (x0, y0)), corte(b, (x1, y1))
        n = e.getLaneNumber()
        for carril in e.getLanes():
            off = (n - 1 - carril.getIndex() + 0.5) * W
            p = (x0 + ux * ra + nx * off, y0 + uy * ra + ny * off)
            q = (x1 - ux * rb + nx * off, y1 - uy * rb + ny * off)
            ax.add_patch(Polygon(rectangulo(p, q, W * 0.96), closed=True, facecolor=CALLE, edgecolor=BORDE,
                                 lw=0.35, zorder=2))
            largo = math.hypot(q[0] - p[0], q[1] - p[1])
            fracs = ([0.5] if largo < 9 * W else [0.28, 0.72]) if flechas else []
            for f in fracs:
                mx, my = p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f
                flecha(ax, (mx - ux * W * 0.9, my - uy * W * 0.9), (mx + ux * W * 0.9, my + uy * W * 0.9), TINTA2,
                       escala=5.5, lw=0.8, z=3)
    for nodo in nodos:
        if es_cruce(nodo):
            h = carriles_en(nodo) * W + 0.15 * W
            x, y = nodo.getCoord()
            ax.add_patch(Polygon([(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h)], closed=True,
                                 facecolor=CALLE, edgecolor=CALLE, lw=0.3, zorder=1.5))
    if anillo:
        cx, cy = centro_anillo
        ax.add_patch(Wedge((cx, cy), radio_anillo + W, 0, 360, width=W, facecolor=CALLE, edgecolor=BORDE, lw=0.35,
                           zorder=2))
        ax.add_patch(Circle((cx, cy), radio_anillo, facecolor=FONDO, edgecolor=BORDE, lw=0.35, zorder=2.1))
        # sentido de giro: el de una arista del anillo
        e = [e for e in net.getEdges() if e.getFromNode().getID() in ids_anillo and e.getToNode().getID() in ids_anillo][0]
        (ax0, ay0), (ax1, ay1) = e.getFromNode().getCoord(), e.getToNode().getCoord()
        giro = 1 if ((ax0 - cx) * (ay1 - cy) - (ay0 - cy) * (ax1 - cx)) > 0 else -1     # 1: antihorario
        r = radio_anillo + W / 2
        for ang in (45, 135, 225, 315):
            t = math.radians(ang)
            px, py = cx + r * math.cos(t), cy + r * math.sin(t)
            tx, ty = -math.sin(t) * giro, math.cos(t) * giro
            flecha(ax, (px - tx * W * 0.7, py - ty * W * 0.7), (px + tx * W * 0.7, py + ty * W * 0.7), TINTA2,
                   escala=5.5, lw=0.8, z=3)
    for tls in net.getTrafficLights():
        nid = tls.getID().replace("semaforo_", "")
        nodo = [n for n in nodos if n.getID() == nid]
        if not nodo:
            continue
        x, y = nodo[0].getCoord()
        ax.add_patch(Circle((x, y), W * 0.75, facecolor=VERDE, edgecolor=FONDO, lw=0.7, zorder=5))
        if rotulo_tls:
            h = carriles_en(nodo[0]) * W
            ax.text(x + h + 0.4 * W, y + h + 0.4 * W, nid, fontsize=7.0, color=TINTA, zorder=6, ha="left", va="bottom")
    bbox = net.getBBoxXY()
    m = 3.0 * W
    ax.set_xlim(bbox[0][0] - m, bbox[1][0] + m)
    ax.set_ylim(bbox[0][1] - m, bbox[1][1] + m)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(titulo, fontsize=8.6, color=TINTA, loc="left", pad=3)
    return centro_anillo, radio_anillo


# ---------------- cruce ampliado (geometria real) ----------------

def punto_desde_inicio(forma, d):
    """Punto a distancia d del inicio de una polilinea, caminando por sus tramos, y su direccion."""
    acum = 0.0
    for k in range(len(forma) - 1):
        (x0, y0), (x1, y1) = forma[k], forma[k + 1]
        s = math.hypot(x1 - x0, y1 - y0)
        if s > 0 and acum + s >= d:
            t = (d - acum) / s
            return (x0 + t * (x1 - x0), y0 + t * (y1 - y0)), ((x1 - x0) / s, (y1 - y0) / s)
        acum += s
    (x0, y0), (x1, y1) = forma[-2], forma[-1]
    s = math.hypot(x1 - x0, y1 - y0) or 1.0
    return forma[-1], ((x1 - x0) / s, (y1 - y0) / s)


def punto_desde_fin(forma, d):
    """Punto a distancia d antes del final de una polilinea, y su direccion (en el sentido de la polilinea)."""
    p, (ux, uy) = punto_desde_inicio(forma[::-1], d)
    return p, (-ux, -uy)


def poligono_carril(forma, ancho):
    """Poligono de un carril: la polilinea desplazada +-ancho/2."""
    izq, der = [], []
    for k in range(len(forma)):
        (x0, y0), (x1, y1) = (forma[k], forma[k + 1]) if k < len(forma) - 1 else (forma[k - 1], forma[k])
        s = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = -(y1 - y0) / s * ancho / 2, (x1 - x0) / s * ancho / 2
        x, y = forma[k]
        izq.append((x + nx, y + ny))
        der.append((x - nx, y - ny))
    return izq + der[::-1]


def dibujar_cruce(ax, net_f, add_f, nodo_id, radio, desde=None, frente=None):
    """Los movimientos permitidos de un cruce (conexiones del .net.xml, por los carriles internos de SUMO), con su
    color por direccion; linea continua si su verde tiene prioridad (G) y discontinua si cede el paso (g). Con desde,
    solo los movimientos que salen de esa arista; con frente, ademas el recto de la arista opuesta, en gris (el
    transito de frente al que cede el giro a la izquierda)."""
    net = sumolib.net.readNet(os.path.join(AQUI, net_f), withInternal=True)
    estados = estados_fijo(add_f)
    nodo = net.getNode(nodo_id)
    cx, cy = nodo.getCoord()
    ax.add_patch(Polygon(nodo.getShape(), closed=True, facecolor=CALLE, edgecolor=CALLE, lw=0.6, zorder=1))
    for arista in list(nodo.getIncoming()) + list(nodo.getOutgoing()):
        if arista.isSpecial():
            continue
        for carril in arista.getLanes():
            forma = carril.getShape()
            ax.add_patch(Polygon(poligono_carril(forma, carril.getWidth()), closed=True, facecolor=CALLE,
                                 edgecolor=BORDE, lw=0.6, zorder=2))
            # flecha de sentido del carril, en el borde del recuadro
            if arista in nodo.getIncoming():
                m, u = punto_desde_fin(forma, radio * 0.86)
            else:
                m, u = punto_desde_inicio(forma, radio * 0.86)
            flecha(ax, (m[0] - u[0] * 2.2, m[1] - u[1] * 2.2), (m[0] + u[0] * 2.2, m[1] + u[1] * 2.2), TINTA2,
                   escala=8, lw=1.0, z=3)
    tls_id = "semaforo_" + nodo_id
    tls = [t for t in net.getTrafficLights() if t.getID() == tls_id][0]
    fases = estados[tls_id]
    rotulos = {"s": "recto", "r": "a la derecha", "l": "a la izquierda:\ncede el paso"}
    for (lin, lout, idx) in tls.getConnections():
        con = [c for c in lin.getOutgoing() if c.getToLane() == lout][0]
        d = con.getDirection()
        de_frente = frente is not None and lin.getEdge().getID() == frente
        if desde is not None and lin.getEdge().getID() != desde and not (de_frente and d == "s"):
            continue
        prioridad = "G" in set(f[idx] for f in fases)
        color = APAGADO if de_frente else {"s": TINTA, "r": AZUL, "l": NARANJA}.get(d, APAGADO)
        forma = []
        via = con.getViaLaneID()
        while via:
            carril_via = net.getLane(via)
            forma += carril_via.getShape() if not forma else carril_via.getShape()[1:]
            sig = [c for c in carril_via.getOutgoing()]
            via = sig[0].getViaLaneID() if sig and sig[0].getViaLaneID() else ""
            if sig and sig[0].getToLane().getEdge().isSpecial() and not via:
                forma += sig[0].getToLane().getShape()[1:]
        a, _ = punto_desde_fin(lin.getShape(), 7.0)
        b, _ = punto_desde_inicio(lout.getShape(), 7.0)
        puntos = [a] + forma + [b]
        ls = "-" if prioridad else TRAZO_IZQ
        if desde is not None:
            # en la vista de un solo acceso, las flechas llegan mas lejos para que se lea el destino
            b, _ = punto_desde_inicio(lout.getShape(), radio * 0.42)
            puntos = [punto_desde_fin(lin.getShape(), radio * 0.55)[0]] + forma + [b]
        ax.plot([p[0] for p in puntos[:-1]], [p[1] for p in puntos[:-1]], color=color, lw=1.8, ls=ls, zorder=4,
                solid_capstyle="round")
        flecha(ax, puntos[-2], puntos[-1], color, escala=11, lw=1.8, ls=ls, z=4)
        if desde is not None and de_frente:
            # el rotulo del transito de frente, sobre su linea y dentro del recuadro
            (sx, sy) = puntos[0]
            ax.text(sx, sy + 1.6, "tránsito de frente", fontsize=7.0, color=color, ha="right", va="bottom", zorder=6)
        elif desde is not None:
            texto = rotulos[d]
            bx, by = puntos[-1]
            ux, uy = puntos[-1][0] - puntos[-2][0], puntos[-1][1] - puntos[-2][1]
            n = math.hypot(ux, uy) or 1.0
            ux, uy = ux / n, uy / n
            ha = "left" if ux > 0.5 else ("right" if ux < -0.5 else "center")
            va = "bottom" if uy > 0.5 else ("top" if uy < -0.5 else "center")
            ax.text(bx + ux * 1.8, by + uy * 1.8, texto, fontsize=7.0, color=color, ha=ha, va=va, zorder=6)
    ax.add_patch(Circle((cx, cy), 1.6, facecolor=VERDE, edgecolor=FONDO, lw=0.7, zorder=5))
    ax.set_xlim(cx - radio, cx + radio)
    ax.set_ylim(cy - radio, cy + radio)
    ax.set_aspect("equal")
    ax.axis("off")


def figura_redes():
    fig = plt.figure(figsize=(6.6, 6.7), facecolor=FONDO)
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.15], hspace=0.12, wspace=0.05)
    ejes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])]
    for ax, (esc, net_f, add_f, titulo) in zip(ejes[:3], REDES):
        net = sumolib.net.readNet(os.path.join(AQUI, net_f))
        bbox = net.getBBoxXY()
        lado = max(bbox[1][0] - bbox[0][0], bbox[1][1] - bbox[0][1])
        W = lado * (0.019 if esc != "malla3" else 0.017)
        centro, radio = dibujar_red(ax, net, W, titulo)
        if centro:
            ax.annotate("rotonda,\nsin semáforo", xy=(centro[0], centro[1] + radio + W), xytext=(centro[0], centro[1] + 7.5 * W),
                        fontsize=7.0, color=TINTA2, ha="center", va="bottom",
                        arrowprops=dict(arrowstyle="-", color=APAGADO, lw=0.7), zorder=6)
    dibujar_cruce(ejes[3], "corredor.net.xml", "corredor.add.xml", "C1", 26, desde="W_C1", frente="C2_C1")
    ejes[3].set_title("Un cruce ampliado: los movimientos desde un acceso", fontsize=8.6, color=TINTA, loc="left", pad=3)
    leyenda = [Line2D([], [], color=TINTA, lw=1.6, label="Recto: verde con prioridad"),
               Line2D([], [], color=AZUL, lw=1.6, label="A la derecha: verde con prioridad"),
               Line2D([], [], color=NARANJA, lw=1.6, ls=TRAZO_IZQ, label="A la izquierda: cede el paso"),
               Line2D([], [], marker="o", ls="", ms=6, mfc=VERDE, mec=FONDO, label="Semáforo"),
               Line2D([], [], marker=r"$\rightarrow$", ls="", ms=9, color=TINTA2, label="Sentido del carril")]
    fig.legend(handles=leyenda, loc="lower center", ncol=2, fontsize=7.2, frameon=False, bbox_to_anchor=(0.5, -0.03),
               handlelength=2.4, columnspacing=1.6, labelcolor=TINTA)
    salida = os.path.join(IMAGENES, "fig_redes.png")
    fig.savefig(salida, dpi=220, bbox_inches="tight", facecolor=FONDO)
    fig.savefig(os.path.splitext(salida)[0] + ".pdf", bbox_inches="tight", facecolor=FONDO, metadata={"CreationDate": None})
    plt.close(fig)
    print("Escrito", salida)


# ---------------- corredor por media hora (esquema) ----------------

def flujos_corredor(rou):
    """[(periodo, desde, hasta, veh/h)] de corredor.rou.xml."""
    res = []
    for fl in ET.parse(os.path.join(AQUI, rou)).getroot().iter("flow"):
        periodo = 1 if float(fl.get("begin")) < 1800 else 2
        res.append((periodo, fl.get("from"), fl.get("to"), float(fl.get("vehsPerHour"))))
    return res


def figura_periodos():
    net = sumolib.net.readNet(os.path.join(AQUI, "corredor.net.xml"))
    flujos = flujos_corredor("corredor.rou.xml")
    coord = {n.getID(): n.getCoord() for n in net.getNodes()}
    vmax = max(v for _, _, _, v in flujos)
    W = 22.0                                           # ancho de carril dibujado (m)
    titulos = {1: "Primera media hora: punta de oeste a este;\nlos cuatro giros, a la derecha",
               2: "Segunda media hora: punta de este a oeste;\nlos cuatro giros, a la izquierda (ceden el paso)"}
    fig, ejes = plt.subplots(2, 1, figsize=(6.4, 6.0), facecolor=FONDO, gridspec_kw={"hspace": 0.16})

    def tramo(arista, desde_m, hasta_m):
        """Segmento de una arista entre dos distancias desde su nodo de origen, en su carril (lado derecho)."""
        (x0, y0), (x1, y1) = coord[arista.getFromNode().getID()], coord[arista.getToNode().getID()]
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        nx, ny = uy, -ux
        off = 0.5 * W
        a = (x0 + ux * desde_m + nx * off, y0 + uy * desde_m + ny * off)
        b = (x0 + ux * hasta_m + nx * off, y0 + uy * hasta_m + ny * off)
        return a, b, L

    for ax, periodo in zip(ejes, (1, 2)):
        dibujar_red(ax, net, W, "", rotulo_tls=True, flechas=False)
        ax.set_title(titulos[periodo].replace(chr(10), " "), fontsize=8.2, color=TINTA, loc="left", pad=3)
        rectos, giros = [], []
        for (p, desde, hasta, v) in flujos:
            if p != periodo:
                continue
            camino = net.getShortestPath(net.getEdge(desde), net.getEdge(hasta))[0]
            dirs = []
            for a, b in zip(camino[:-1], camino[1:]):
                cons = a.getOutgoing().get(b, [])
                dirs.append(cons[0].getDirection() if cons else "s")
            k_giro = [k for k, d in enumerate(dirs) if d in ("l", "r")]
            if not k_giro:
                rectos.append((camino, v))
            else:
                giros.append((camino, k_giro[0], dirs[k_giro[0]], v))
        # rectos: gris, a lo largo de todo el recorrido, con el grosor segun la demanda
        for camino, v in rectos:
            puntos = []
            for k, arista in enumerate(camino):
                _, _, L = tramo(arista, 0, 0)
                ini = 0.62 * L if k == 0 else 1.2 * W
                fin = 0.38 * L if k == len(camino) - 1 else L - 1.2 * W
                a, b, _ = tramo(arista, ini, fin)
                puntos += [a, b]
            ancho = 0.8 + 3.0 * v / vmax
            ax.plot([q[0] for q in puntos[:-1]], [q[1] for q in puntos[:-1]], color=APAGADO, lw=ancho, zorder=3.5,
                    solid_capstyle="butt", alpha=0.8)
            flecha(ax, puntos[-2], puntos[-1], APAGADO, escala=4 + 2.4 * ancho, lw=ancho, z=3.5, alpha=0.8)
        # giros: solo en el cruce donde giran, en color
        for camino, k, d, v in giros:
            e1, e2 = camino[k], camino[k + 1]
            _, _, L1 = tramo(e1, 0, 0)
            a, b, _ = tramo(e1, L1 - 4.2 * W, L1 - 1.2 * W)
            c, e, _ = tramo(e2, 1.2 * W, 4.2 * W)
            color, ls = (NARANJA, TRAZO_IZQ) if d == "l" else (AZUL, "-")
            ax.plot([a[0], b[0], c[0]], [a[1], b[1], c[1]], color=color, lw=1.9, ls=ls, zorder=5,
                    solid_capstyle="round")
            flecha(ax, c, e, color, escala=10, lw=1.9, ls=ls, z=5)
        ax.set_xlim(130, 970)
        ax.set_ylim(215, 585)
    leyenda = [Line2D([], [], color=APAGADO, lw=3.4, label="Recto (más grueso, más demanda)"),
               Line2D([], [], color=AZUL, lw=1.6, label="Giro a la derecha"),
               Line2D([], [], color=NARANJA, lw=1.6, ls=TRAZO_IZQ, label="Giro a la izquierda: cede el paso"),
               Line2D([], [], marker="o", ls="", ms=6, mfc=VERDE, mec=FONDO, label="Semáforo")]
    fig.legend(handles=leyenda, loc="lower center", ncol=2, fontsize=7.2, frameon=False, bbox_to_anchor=(0.5, -0.02),
               handlelength=2.4, columnspacing=1.6, labelcolor=TINTA)
    salida = os.path.join(IMAGENES, "fig_corredor_periodos.png")
    fig.savefig(salida, dpi=220, bbox_inches="tight", facecolor=FONDO)
    fig.savefig(os.path.splitext(salida)[0] + ".pdf", bbox_inches="tight", facecolor=FONDO, metadata={"CreationDate": None})
    plt.close(fig)
    print("Escrito", salida)


if __name__ == "__main__":
    figura_redes()
    figura_periodos()
