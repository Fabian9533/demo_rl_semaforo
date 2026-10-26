"""
figuras_redes.py - Figuras de las redes del plan dibujadas desde los archivos de SUMO (25.10.2026, pedido de Fabian:
"imagenes de como se ven las redes, con el sentido de cada carril y los giros").

Desde plan2/:
    python figuras_redes.py
Escribe en TESIS/images/:
  fig_redes.pdf/.png              las tres redes (corredor, red con rotonda, malla 3x3), con el sentido de cada carril y
                                  los semaforos, y un cruce ampliado con los movimientos permitidos y su tipo de verde
  fig_corredor_periodos.pdf/.png  los movimientos de los dos cruces del corredor en cada media hora, con la demanda
                                  de cada uno en P1 (los cuatro giros, a la derecha en la primera y a la izquierda en
                                  la segunda) y el ceda el paso de los giros a la izquierda
  fig_giro_izquierda.pdf/.png     esquema con autos de un giro a la derecha y uno a la izquierda en C1: el que gira a
                                  la izquierda espera dentro del cruce y detiene su carril (lo midio
                                  diag_corredor/bloqueo.md)

25.10.2026, 21:30: fig_corredor_periodos dejo de ser una vista del corredor a escala con los giros superpuestos
(Fabian: "no se logra entender con claridad que pasa en ese tipo de cruces"); se agrego fig_giro_izquierda.

Que sale de SUMO: la posicion de los cruces y la topologia (nodos y aristas del .net.xml, con sumolib), el numero de
carriles de cada arista y su orden (el 0 es el de la derecha), los movimientos de cada carril (conexiones r/s/l), el
tipo de verde de cada movimiento (estado G, con prioridad, o g, sin prioridad, del programa fijo del .add.xml) y los
flujos de cada media hora (corredor.rou.xml). El dibujo es esquematico: en la vista general los carriles se dibujan
mucho mas anchos que en la red (de 3.2 m en cruces a 300-400 m) para que se vean los dos sentidos; el cruce ampliado
usa la geometria real de SUMO.
"""
import os
import math
import textwrap
import xml.etree.ElementTree as ET

import sumolib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
import matplotlib.patheffects as pe
from matplotlib.patches import Polygon, FancyArrowPatch, FancyBboxPatch, Circle, Wedge, Patch
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
            # en la vista de un solo acceso, las flechas llegan mas lejos para que se lea el destino; las del acceso
            # salen juntas de cerca de la linea de detencion (comparten el carril) y el transito de frente, del borde
            b, _ = punto_desde_inicio(lout.getShape(), radio * 0.42)
            puntos = [punto_desde_fin(lin.getShape(), radio * 0.8 if de_frente else 3.0)[0]] + forma + [b]
        ax.plot([p[0] for p in puntos[:-1]], [p[1] for p in puntos[:-1]], color=color, lw=1.8, ls=ls, zorder=4,
                solid_capstyle="round")
        flecha(ax, puntos[-2], puntos[-1], color, escala=11, lw=1.8, ls=ls, z=4)
        if desde is not None and de_frente:
            # el rotulo del transito de frente, sobre su linea, entre el cruce y el borde del recuadro
            ax.text(cx + 6.0, puntos[0][1] + 1.4, "tránsito de frente", fontsize=7.0, color=color, ha="left",
                    va="bottom", zorder=6)
        elif desde is not None:
            texto = rotulos[d]
            bx, by = puntos[-1]
            ux, uy = puntos[-1][0] - puntos[-2][0], puntos[-1][1] - puntos[-2][1]
            n = math.hypot(ux, uy) or 1.0
            ux, uy = ux / n, uy / n
            ha = "left" if ux > 0.5 else ("right" if ux < -0.5 else "center")
            va = "bottom" if uy > 0.5 else ("top" if uy < -0.5 else "center")
            ax.text(bx + ux * 1.8, by + uy * 1.8, texto, fontsize=7.0, color=color, ha=ha, va=va, zorder=6)
    # el semaforo, en una esquina del cruce, para que no tape los giros
    ax.add_patch(Circle((cx - 7.0, cy - 7.0), 1.6, facecolor=VERDE, edgecolor=FONDO, lw=0.7, zorder=5))
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


# ---------------- esquema de cruces con un carril por sentido ----------------
# Unidades: el ancho de un carril. Cada brazo tiene un carril que llega al cruce y otro que sale; se circula por la
# derecha. c es el centro del cruce, d el vector unitario del centro hacia el extremo del brazo y s la distancia al
# centro; el borde del cruce, con la linea de detencion, esta en s = h (h = 1: el cuadrado donde se cortan las dos
# calles; h > 1: un cruce mas amplio con las esquinas redondeadas, como el de SUMO, que llega a 7.2 m del centro).

def brazo(nodo, vecino):
    """Vector del cruce hacia un nodo vecino, redondeado a los ejes (el corredor esta alineado con ellos)."""
    (x0, y0), (x1, y1) = nodo.getCoord(), vecino.getCoord()
    L = math.hypot(x1 - x0, y1 - y0)
    return (round((x1 - x0) / L), round((y1 - y0) / L))


def p_entrada(c, d, s):
    """Punto del carril que llega al cruce c por el brazo d."""
    return (c[0] + d[0] * s - d[1] * 0.5, c[1] + d[1] * s + d[0] * 0.5)


def p_salida(c, d, s):
    """Punto del carril que sale del cruce c por el brazo d."""
    return (c[0] + d[0] * s + d[1] * 0.5, c[1] + d[1] * s - d[0] * 0.5)


def bezier(a, c, b, n=40):
    return [((1 - t) ** 2 * a[0] + 2 * t * (1 - t) * c[0] + t * t * b[0],
             (1 - t) ** 2 * a[1] + 2 * t * (1 - t) * c[1] + t * t * b[1]) for t in (k / n for k in range(n + 1))]


def trayecto(c, d1, d2, s_ini, s_fin, h=1.0):
    """Puntos del movimiento que entra al cruce c por el brazo d1 y sale por el d2: por el carril que llega desde
    s_ini hasta la linea de detencion, recto o en curva hasta el carril que sale, y por este hasta s_fin."""
    a, b = p_entrada(c, d1, h), p_salida(c, d2, h)
    if d1[0] + d2[0] == 0 and d1[1] + d2[1] == 0:
        medio = [a, b]
    else:
        esquina = (b[0], a[1]) if d1[1] == 0 else (a[0], b[1])
        medio = bezier(a, esquina, b)
    return [p_entrada(c, d1, s_ini)] + medio + [p_salida(c, d2, s_fin)]


def arcos_esquinas(c, h, n=10):
    """Las cuatro esquinas redondeadas de un cruce de semilado h, en orden antihorario desde la inferior derecha."""
    r = h - 1.0
    res = []
    for (ox, oy), a0, a1 in (((h, -h), 180, 90), ((h, h), 270, 180), ((-h, h), 360, 270), ((-h, -h), 90, 0)):
        res.append([(c[0] + ox + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                     c[1] + oy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)])
    return res


def calle_esquema(ax, c, brazos, rotulos=None, fs=7.2, h=1.0):
    """El cruce c y sus brazos ({d: largo}): calzada, bordes, linea central, linea de detencion de cada carril que
    llega y los rotulos de los extremos ({d: texto})."""
    x, y = c
    if h > 1.0:
        arcos = arcos_esquinas(c, h)
        ax.add_patch(Polygon([p for arco in arcos for p in arco], closed=True, facecolor=CALLE, edgecolor="none",
                             zorder=1))
        for arco in arcos:
            ax.plot([p[0] for p in arco], [p[1] for p in arco], color=BORDE, lw=0.8, zorder=1.1)
    else:
        ax.add_patch(Polygon([(x - 1, y - 1), (x + 1, y - 1), (x + 1, y + 1), (x - 1, y + 1)], closed=True,
                             facecolor=CALLE, edgecolor="none", zorder=1))
    for d, L in brazos.items():
        p, q = (x + d[0] * h, y + d[1] * h), (x + d[0] * L, y + d[1] * L)
        ax.add_patch(Polygon(rectangulo(p, q, 2.0), closed=True, facecolor=CALLE, edgecolor="none", zorder=1))
        for lado in (-1, 1):
            ax.plot([p[0] - d[1] * lado, q[0] - d[1] * lado], [p[1] + d[0] * lado, q[1] + d[0] * lado], color=BORDE,
                    lw=0.8, zorder=1.1, solid_capstyle="butt")
        ax.plot([p[0], q[0]], [p[1], q[1]], color=BORDE, lw=0.7, ls=(0, (3, 2.5)), zorder=1.1)
        ax.plot([p[0], p[0] - d[1]], [p[1], p[1] + d[0]], color=TINTA2, lw=1.5, zorder=1.2, solid_capstyle="butt")
        if rotulos and d in rotulos:
            ha = "left" if d[0] > 0 else ("right" if d[0] < 0 else "center")
            va = "bottom" if d[1] > 0 else ("top" if d[1] < 0 else "center")
            ax.text(x + d[0] * (L + 0.3), y + d[1] * (L + 0.3), rotulos[d], fontsize=fs, color=TINTA, ha=ha, va=va,
                    zorder=6)


def ceda(ax, centro, r=0.27, z=7):
    """Senal de ceda el paso: triangulo invertido."""
    x, y = centro
    ax.add_patch(Polygon([(x - r, y + 0.58 * r), (x + r, y + 0.58 * r), (x, y - 1.15 * r)], closed=True,
                         facecolor=FONDO, edgecolor=NARANJA, lw=1.3, zorder=z, joinstyle="round"))


# ---------------- el corredor en cada media hora: los movimientos de cada cruce ----------------

def flujos_corredor(rou):
    """[(periodo, desde, hasta, veh/h)] de corredor.rou.xml."""
    res = []
    for fl in ET.parse(os.path.join(AQUI, rou)).getroot().iter("flow"):
        periodo = 1 if float(fl.get("begin")) < 1800 else 2
        res.append((periodo, fl.get("from"), fl.get("to"), float(fl.get("vehsPerHour"))))
    return res


def movimientos_por_cruce(net, flujos):
    """{(periodo, cruce): {(arista que llega, arista que sale): [direccion, veh/h]}}: cada flujo suma su tasa en cada
    cruce de su camino (el mas corto, que en el corredor es el unico)."""
    res = {}
    for (p, desde, hasta, v) in flujos:
        camino = net.getShortestPath(net.getEdge(desde), net.getEdge(hasta))[0]
        for a, b in zip(camino[:-1], camino[1:]):
            cons = a.getOutgoing().get(b, [])
            mov = res.setdefault((p, a.getToNode().getID()), {}).setdefault(
                (a, b), [cons[0].getDirection() if cons else "s", 0.0])
            mov[1] += v
    return res


def figura_periodos():
    net = sumolib.net.readNet(os.path.join(AQUI, "corredor.net.xml"))
    movs = movimientos_por_cruce(net, flujos_corredor("corredor.rou.xml"))
    vref = max(v for m in movs.values() for (dr, v) in m.values() if dr == "s")
    H = 1.7                                          # semilado del cruce dibujado
    SEP, LARGO_AV, LARGO_TR = 9.4, 4.4, 3.7          # C1-C2 dibujado (en la red, 300 m) y brazos de los extremos
    centros = {"C1": (0.0, 0.0), "C2": (SEP, 0.0)}
    nombres = {"W": "Oeste", "E": "Este"}
    titulos = {1: "Primera media hora: la punta va de oeste a este y los cuatro giros son a la derecha",
               2: "Segunda media hora: la punta va de este a oeste y los cuatro giros son a la izquierda"}
    orden = {"s": 0, "r": 1, "l": 2}
    fig, ejes = plt.subplots(2, 1, figsize=(6.4, 5.5), facecolor=FONDO, gridspec_kw={"hspace": 0.10})
    for ax, periodo in zip(ejes, (1, 2)):
        for nid, c in centros.items():
            nodo = net.getNode(nid)
            brazos, rotulos = {}, {}
            for e in list(nodo.getIncoming()) + list(nodo.getOutgoing()):
                otro = e.getFromNode() if e.getToNode() == nodo else e.getToNode()
                d = brazo(nodo, otro)
                if otro.getID() in centros:
                    brazos[d] = SEP / 2                  # cada cruce dibuja la mitad del tramo entre los dos
                else:
                    brazos[d] = LARGO_AV if d[1] == 0 else LARGO_TR
                    rotulos[d] = nombres.get(otro.getID(), otro.getID())
            calle_esquema(ax, c, brazos, rotulos, fs=7.8, h=H)
            ax.text(c[0] + (-H - 1.1 if nid == "C1" else H + 1.1), c[1] + H + 1.1, nid, fontsize=8.6, color=TINTA,
                    ha="center", va="center", fontweight="bold", zorder=6)
            for (a, b), (dr, v) in sorted(movs[(periodo, nid)].items(), key=lambda kv: orden.get(kv[1][0], 3)):
                d1, d2 = brazo(nodo, a.getFromNode()), brazo(nodo, b.getToNode())
                # los rectos vienen por su carril; los giros salen de la linea de detencion de ese mismo carril
                if dr == "s":
                    s_ini, s_fin = H + 0.7, min(H + 2.0, brazos[d2] - 0.35)
                    lw, color, ls = 0.9 + 3.4 * v / vref, APAGADO, "-"
                else:
                    s_ini, s_fin = H, min(H + 0.9, brazos[d2] - 0.35)
                    lw, color, ls = 1.9, (AZUL if dr == "r" else NARANJA), ("-" if dr == "r" else TRAZO_IZQ)
                pts = trayecto(c, d1, d2, s_ini, s_fin, h=H)
                z = 3 + orden.get(dr, 0)
                halo = [] if dr == "s" else [pe.Stroke(linewidth=lw + 2.2, foreground=CALLE), pe.Normal()]
                ax.plot([p[0] for p in pts[:-1]], [p[1] for p in pts[:-1]], color=color, lw=lw, ls=ls, zorder=z,
                        solid_capstyle="butt", solid_joinstyle="round", path_effects=halo)
                flecha(ax, pts[-2], pts[-1], color, escala=5 + 2.0 * lw, lw=lw, ls=ls, z=z)
                # la cifra, al costado de la punta y fuera de la calzada
                x, y = pts[-1]
                ax.text(x + d2[1] * 0.95, y - d2[0] * 0.95, f"{v:.0f}", fontsize=7.6, ha="center", va="center",
                        color=TINTA2 if dr == "s" else color, zorder=6)
                if dr == "l":
                    # ceda el paso al costado del carril donde empieza el giro, junto a la linea de detencion
                    x, y = p_entrada(c, d1, H + 0.35)
                    ceda(ax, (x - d1[1] * 0.95, y + d1[0] * 0.95))
        ax.set_xlim(-LARGO_AV - 1.5, SEP + LARGO_AV + 1.5)
        ax.set_ylim(-LARGO_TR - 0.75, LARGO_TR + 0.75)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(titulos[periodo], fontsize=8.8, color=TINTA, loc="left", pad=2)
    leyenda = [Line2D([], [], color=APAGADO, lw=3.4, label="Recto: el grosor crece con la demanda"),
               Line2D([], [], color=AZUL, lw=1.9, label="Giro a la derecha: verde con prioridad"),
               Line2D([], [], color=NARANJA, lw=1.9, ls=TRAZO_IZQ, label="Giro a la izquierda: verde sin prioridad"),
               Line2D([], [], marker="v", ls="", ms=7.5, mfc=FONDO, mec=NARANJA, mew=1.3,
                      label="Ceda el paso: espera un hueco en el tránsito de frente")]
    fig.legend(handles=leyenda, loc="lower center", ncol=2, fontsize=7.8, frameon=False, bbox_to_anchor=(0.5, -0.03),
               handlelength=2.4, columnspacing=1.6, labelcolor=TINTA)
    fig.text(0.5, -0.06, "Cifras: vehículos por hora de cada movimiento en P1. Todas las calles tienen un carril por "
             "sentido.", fontsize=7.6, color=TINTA2, ha="center", va="top")
    salida = os.path.join(IMAGENES, "fig_corredor_periodos.png")
    fig.savefig(salida, dpi=220, bbox_inches="tight", facecolor=FONDO)
    fig.savefig(os.path.splitext(salida)[0] + ".pdf", bbox_inches="tight", facecolor=FONDO, metadata={"CreationDate": None})
    plt.close(fig)
    print("Escrito", salida)


# ---------------- que pasa en un giro a la izquierda (esquema con autos) ----------------

def auto(ax, centro, angulo, color, largo=1.45, ancho=0.64, z=6):
    """Un auto visto desde arriba, con el parabrisas adelante (angulo en grados; 0 = hacia el este). Devuelve el
    punto del frente y la direccion."""
    tr = mtransforms.Affine2D().rotate_deg(angulo).translate(centro[0], centro[1]) + ax.transData
    cuerpo = FancyBboxPatch((-largo / 2, -ancho / 2), largo, ancho, boxstyle="round,pad=0,rounding_size=0.16",
                            facecolor=color, edgecolor="none", zorder=z)
    vidrio = FancyBboxPatch((largo * 0.1, -ancho * 0.33), largo * 0.17, ancho * 0.66,
                            boxstyle="round,pad=0,rounding_size=0.05", facecolor=FONDO, edgecolor="none", alpha=0.8,
                            zorder=z + 0.1)
    for parche in (cuerpo, vidrio):
        parche.set_transform(tr)
        ax.add_patch(parche)
    u = (math.cos(math.radians(angulo)), math.sin(math.radians(angulo)))
    return (centro[0] + u[0] * largo / 2, centro[1] + u[1] * largo / 2), u


def en_marcha(ax, frente, u, color, z=6):
    """Flecha corta delante de un auto que avanza."""
    flecha(ax, (frente[0] + u[0] * 0.12, frente[1] + u[1] * 0.12), (frente[0] + u[0] * 0.7, frente[1] + u[1] * 0.7),
           color, escala=6.5, lw=1.0, z=z)


def semaforo_verde(ax, x, y, z=6):
    """Cabeza de semaforo con la luz verde encendida."""
    ax.add_patch(FancyBboxPatch((x - 0.17, y - 0.44), 0.34, 0.88, boxstyle="round,pad=0,rounding_size=0.07",
                                facecolor=TINTA2, edgecolor="none", zorder=z))
    for k in range(3):
        ax.add_patch(Circle((x, y + 0.27 - 0.27 * k), 0.09, facecolor=VERDE if k == 2 else "#7d7b75",
                            edgecolor="none", zorder=z + 0.1))


def marca(ax, x, y, n, z=9, fs=7.6):
    """Numero de un paso, en un circulo."""
    ax.text(x, y, str(n), fontsize=fs, color=FONDO, ha="center", va="center", fontweight="bold", zorder=z,
            bbox=dict(boxstyle="circle,pad=0.22", facecolor=TINTA, edgecolor="none"))


def guia(ax, a, b, z=8):
    ax.plot([a[0], b[0]], [a[1], b[1]], color=TINTA2, lw=0.7, zorder=z)


def figura_giro_izquierda():
    """El giro de este a norte en C1 (primera media hora) frente al de este a sur (segunda), con autos."""
    C = (0.0, 0.0)
    brazos = {(-1, 0): 3.2, (1, 0): 9.4, (0, 1): 2.8, (0, -1): 2.8}
    rotulos = {(-1, 0): "Oeste", (1, 0): "C2", (0, 1): "N1", (0, -1): "S1"}
    FRENTE, FILA = TINTA2, "#a9a69e"
    escenas = [
        ("Primera media hora: giro a la derecha, de este a norte en C1",
         ["Gira a la derecha: no cruza el tránsito de frente y tiene verde con prioridad, así que no espera.",
          "Los de atrás siguen."]),
        ("Segunda media hora: giro a la izquierda, de este a sur en C1",
         ["El primero de la fila va a girar a la izquierda. Entra al cruce y espera un hueco.",
          "El tránsito de frente tiene prioridad y sigue pasando.",
          "Los de atrás van recto, pero no pueden pasarlo: la calle tiene un solo carril. Quedan detenidos con el "
          "semáforo en verde.",
          "Gira cuando hay un hueco o cuando termina el verde. Si gira al terminar el verde, los de atrás esperan el "
          "verde siguiente."]),
    ]
    fig = plt.figure(figsize=(6.4, 5.1), facecolor=FONDO)
    gs = fig.add_gridspec(2, 2, width_ratios=[1.95, 1.1], height_ratios=[1.0, 1.3], hspace=0.22,
                          wspace=0.04)
    for fila, (titulo, textos) in enumerate(escenas):
        ax = fig.add_subplot(gs[fila, 0])
        calle_esquema(ax, C, brazos, rotulos, fs=7.8)
        semaforo_verde(ax, -1.95, 1.75)
        if fila == 0:
            # el que gira a la derecha: no cruza a nadie y sigue
            frente, u = auto(ax, (0.78, 0.86), 128, AZUL)
            camino = bezier((frente[0] + u[0] * 0.1, frente[1] + u[1] * 0.1), (0.5, 1.75), (0.5, 2.05)) + [(0.5, 2.5)]
            ax.plot([p[0] for p in camino[:-1]], [p[1] for p in camino[:-1]], color=AZUL, lw=1.5, zorder=5)
            flecha(ax, camino[-2], camino[-1], AZUL, escala=9, lw=1.5, z=5)
            for x in (-2.4, 0.3, 3.4):                          # transito de frente, en marcha
                f, v = auto(ax, (x, -0.5), 0, FRENTE)
                en_marcha(ax, f, v, FRENTE)
            for x in (2.6, 4.5, 6.4):                           # los de atras, tambien en marcha
                f, v = auto(ax, (x, 0.5), 180, FILA)
                en_marcha(ax, f, v, APAGADO)
            marca(ax, 1.85, 1.75, 1)
            guia(ax, (1.6, 1.62), (1.12, 1.15))
            marca(ax, 4.5, 1.5, 2)
            guia(ax, (4.5, 1.22), (4.5, 0.86))
        else:
            # el que gira a la izquierda: detenido dentro del cruce, con la cola todavia sobre su carril
            frente, u = auto(ax, (0.55, 0.36), 192, NARANJA)
            camino = bezier((frente[0] + u[0] * 0.1, frente[1] + u[1] * 0.1), (-0.5, 0.05), (-0.5, -1.0)) + [(-0.5, -2.2)]
            ax.plot([p[0] for p in camino[:-1]], [p[1] for p in camino[:-1]], color=NARANJA, lw=1.5, ls=TRAZO_IZQ,
                    zorder=5)
            flecha(ax, camino[-2], camino[-1], NARANJA, escala=9, lw=1.5, ls=TRAZO_IZQ, z=5)
            ceda(ax, (-1.45, 1.8))                              # junto al semaforo: con verde, el giro cede el paso
            for x in (-1.75, 0.45, 3.1):                        # transito de frente, en marcha: no deja hueco
                f, v = auto(ax, (x, -0.5), 0, FRENTE)
                en_marcha(ax, f, v, FRENTE)
            for x in (2.15, 3.9, 5.65, 7.4):                     # los de atras, detenidos
                auto(ax, (x, 0.5), 180, FILA)
            # llave sobre la fila detenida
            ax.plot([1.45, 1.45, 8.1, 8.1], [1.13, 1.3, 1.3, 1.13], color=TINTA2, lw=0.8, zorder=8)
            marca(ax, 0.45, 1.55, 1)
            guia(ax, (0.45, 1.27), (0.5, 0.72))
            marca(ax, 3.1, -1.55, 2)
            guia(ax, (3.1, -1.27), (3.1, -0.86))
            marca(ax, 4.78, 1.62, 3)
            marca(ax, -1.65, -2.2, 4)
            guia(ax, (-1.37, -2.2), (-0.62, -2.2))
        ax.set_xlim(-4.85, 10.45)
        ax.set_ylim(-3.45, 3.75)
        ax.set_aspect("equal")
        ax.set_anchor("N")                                  # arriba de su celda, a la altura de los pasos
        ax.axis("off")
        ax.set_title(titulo, fontsize=8.8, color=TINTA, loc="left", pad=2)
        # los pasos, a la derecha del dibujo y desde su borde superior; el paso de linea va en pulgadas para que sea
        # el mismo en las dos filas, que tienen distinta altura
        ax_t = fig.add_subplot(gs[fila, 1])
        ax_t.set_xlim(0, 1)
        ax_t.set_ylim(0, 1)
        ax_t.axis("off")
        alto = ax_t.get_position().height * fig.get_figheight()
        linea = 7.9 / 72 * 1.25 / alto
        y = 1.0 - 0.06 / alto
        for k, texto in enumerate(textos, 1):
            lineas = textwrap.wrap(texto, 37)
            marca(ax_t, 0.05, y - 0.45 * linea, k, fs=7.6)
            ax_t.text(0.13, y, "\n".join(lineas), fontsize=7.9, color=TINTA, ha="left", va="top", linespacing=1.25)
            y -= linea * len(lineas) + 0.09 / alto
    leyenda = [Patch(facecolor=NARANJA, label="Gira a la izquierda"), Patch(facecolor=AZUL, label="Gira a la derecha"),
               Patch(facecolor=FRENTE, label="Tránsito de frente"), Patch(facecolor=FILA, label="Detrás del que gira: van recto")]
    fig.legend(handles=leyenda, loc="lower center", ncol=4, fontsize=7.6, frameon=False, bbox_to_anchor=(0.5, -0.03),
               handlelength=1.6, handleheight=0.9, columnspacing=1.6, labelcolor=TINTA)
    salida = os.path.join(IMAGENES, "fig_giro_izquierda.png")
    fig.savefig(salida, dpi=220, bbox_inches="tight", facecolor=FONDO)
    fig.savefig(os.path.splitext(salida)[0] + ".pdf", bbox_inches="tight", facecolor=FONDO, metadata={"CreationDate": None})
    plt.close(fig)
    print("Escrito", salida)


if __name__ == "__main__":
    figura_redes()
    figura_periodos()
    figura_giro_izquierda()
