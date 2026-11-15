"""
mirar_red.py - Resume y dibuja la red del caso Lima (Av. Reducto con Av. 28 de Julio) para revisarla.

Uso (desde demo_rl/lima):
  python mirar_red.py [red.net.xml] [--radio 260] [--salida borrador/red.png]
Imprime, por cada semaforo a menos de --radio metros del nudo, sus accesos (calle, lado desde donde llega, carriles
y largo) y sus fases; y escribe un dibujo de esa zona. Solo lee la red.
"""
import argparse
import collections
import math
import os
import sys

if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
import sumolib

AQUI = os.path.dirname(os.path.abspath(__file__))
NUDO = (-12.129167, -77.023778)                 # latitud y longitud del nudo (dato de Fabian)
RUMBOS = ["este", "noreste", "norte", "noroeste", "oeste", "suroeste", "sur", "sureste"]


def utm(lat, lon, zona=18):
    """Latitud y longitud WGS84 -> este y norte UTM, como los calcula la red de SUMO. Formulas estandar (serie corta)."""
    a, f = 6378137.0, 1 / 298.257223563
    k0, e2 = 0.9996, f * (2 - f)
    ep2 = e2 / (1 - e2)
    fi, la = math.radians(lat), math.radians(lon)
    la0 = math.radians(-183 + 6 * zona)
    n = a / math.sqrt(1 - e2 * math.sin(fi) ** 2)
    t, c = math.tan(fi) ** 2, ep2 * math.cos(fi) ** 2
    aa = (la - la0) * math.cos(fi)
    m = a * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * fi
             - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * math.sin(2 * fi)
             + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * math.sin(4 * fi)
             - (35 * e2 ** 3 / 3072) * math.sin(6 * fi))
    este = 500000 + k0 * n * (aa + (1 - t + c) * aa ** 3 / 6 + (5 - 18 * t + t * t + 72 * c - 58 * ep2) * aa ** 5 / 120)
    norte = k0 * (m + n * math.tan(fi) * (aa ** 2 / 2 + (5 - t + 9 * c + 4 * c * c) * aa ** 4 / 24
                                           + (61 - 58 * t + t * t + 600 * c - 330 * ep2) * aa ** 6 / 720))
    return este, norte          # sin falso norte: la red de SUMO usa "+proj=utm +zone=18" (norte negativo en el sur)


def rumbo(dx, dy):
    return RUMBOS[int(((math.degrees(math.atan2(dy, dx)) % 360) + 22.5) // 45) % 8]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("red", nargs="?", default=os.path.join(AQUI, "borrador", "lima_reducto.net.xml"))
    ap.add_argument("--radio", type=float, default=260.0)
    ap.add_argument("--salida", default=os.path.join(AQUI, "borrador", "red.png"))
    args = ap.parse_args()

    net = sumolib.net.readNet(args.red, withPrograms=True, withInternal=False)
    dx, dy = net.getLocationOffset()
    este, norte = utm(*NUDO)
    px, py = este + dx, norte + dy
    print(f"Nudo en la red: x {px:.0f}, y {py:.0f}")

    cerca = []
    for tls in net.getTrafficLights():
        nodos = {c[0].getEdge().getToNode() for c in tls.getConnections()}
        cx = sum(n.getCoord()[0] for n in nodos) / len(nodos)
        cy = sum(n.getCoord()[1] for n in nodos) / len(nodos)
        d = math.hypot(cx - px, cy - py)
        if d <= args.radio:
            cerca.append((d, tls, cx, cy))
    cerca.sort(key=lambda r: r[0])
    print(f"Semaforos a menos de {args.radio:.0f} m del nudo: {len(cerca)} (de {len(net.getTrafficLights())} en la red)")
    for k, (d, tls, cx, cy) in enumerate(cerca, start=1):
        prog = next(iter(tls.getPrograms().values()))
        fases = prog.getPhases()
        verdes = [f for f in fases if ("G" in f.state or "g" in f.state) and "y" not in f.state]
        print(f"\nS{k}: {tls.getID()[:58]}  (a {d:.0f} m del nudo; x {cx:.0f}, y {cy:.0f})")
        print(f"    programa que adivina netconvert: {len(fases)} fases, {len(verdes)} verdes; duraciones "
              + ", ".join(f"{f.duration:.0f}" for f in fases) + f" (ciclo {sum(f.duration for f in fases):.0f} s)")
        entradas = collections.OrderedDict()
        for carril_in, carril_out, _ in tls.getConnections():
            e, s = carril_in.getEdge(), carril_out.getEdge()
            entradas.setdefault(e, set()).add(s)
        for e, salidas in entradas.items():
            ax, ay = e.getFromNode().getCoord()
            forma = e.getShape()
            ax, ay = forma[max(0, len(forma) - 2)]            # ultimo tramo antes de la linea de parada
            lado = rumbo(ax - cx, ay - cy)
            destinos = ", ".join(sorted({(s.getName() or "sin nombre") + " (" + rumbo(
                s.getShape()[min(1, len(s.getShape()) - 1)][0] - cx,
                s.getShape()[min(1, len(s.getShape()) - 1)][1] - cy) + ")" for s in salidas}))
            print(f"    entra {(e.getName() or 'sin nombre')[:32]:32s} desde el {lado:9s} {e.getLaneNumber()} carriles, "
                  f"{e.getLength():4.0f} m -> {destinos}")

    # ---------------- dibujo ----------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    r = args.radio
    fig, ax = plt.subplots(figsize=(11, 11))
    nombres = {}
    for e in net.getEdges():
        forma = e.getShape()
        if not any(abs(x - px) <= r * 1.15 and abs(y - py) <= r * 1.15 for x, y in forma):
            continue
        xs, ys = [p[0] for p in forma], [p[1] for p in forma]
        ax.plot(xs, ys, color="#8a8a86", linewidth=1.2 + 1.6 * e.getLaneNumber(), solid_capstyle="round", zorder=1)
        mx, my = forma[len(forma) // 2] if len(forma) > 2 else ((xs[0] + xs[-1]) / 2, (ys[0] + ys[-1]) / 2)
        # tramo que contiene la mitad del recorrido: ahi va la flecha de sentido
        tramos = [math.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]) for i in range(len(xs) - 1)]
        mitad, acum, k = sum(tramos) / 2, 0.0, 1
        for i, t in enumerate(tramos):
            if acum + t >= mitad:
                k = i + 1
                break
            acum += t
        x0, y0, x1, y1 = xs[k - 1], ys[k - 1], xs[k], ys[k]
        largo = math.hypot(x1 - x0, y1 - y0)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        if largo > 8 and e.getLength() > 25 and abs(mx - px) <= r and abs(my - py) <= r:      # flecha de sentido
            ux, uy = (x1 - x0) / largo, (y1 - y0) / largo
            cxm, cym = (x0 + x1) / 2, (y0 + y1) / 2
            ax.annotate("", xy=(cxm + 5 * ux, cym + 5 * uy), xytext=(cxm - 5 * ux, cym - 5 * uy),
                        arrowprops=dict(arrowstyle="-|>", color="#1c1c1a", lw=1.0), zorder=3)
        nombre = e.getName()
        if nombre and e.getLength() > 35 and abs(mx - px) <= r * 0.95 and abs(my - py) <= r * 0.95:
            nombres.setdefault(nombre, []).append((e.getLength(), mx, my, math.degrees(math.atan2(y1 - y0, x1 - x0)),
                                                   e.getLaneNumber()))
    for nombre, lista in nombres.items():
        lista.sort(reverse=True)
        for largo, mx, my, ang, carriles in lista[:2]:
            ang = ang if -90 <= ang <= 90 else ang - 180 if ang > 90 else ang + 180
            ax.text(mx, my, f"{nombre.replace('Avenida', 'Av.').replace('Calle', 'Ca.')} ({carriles})", fontsize=7,
                    rotation=ang, ha="center", va="center", color="#11314f", zorder=4,
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.75, pad=0.6))
    for k, (d, tls, cx, cy) in enumerate(cerca, start=1):
        ax.plot([cx], [cy], marker="o", markersize=17, color="#1baf7a", markeredgecolor="black", zorder=5)
        ax.text(cx, cy, f"S{k}", fontsize=8, fontweight="bold", ha="center", va="center", zorder=6)
    ax.plot([px], [py], marker="+", markersize=14, color="#d43d3d", zorder=7)
    ax.set_xlim(px - r, px + r)
    ax.set_ylim(py - r, py + r)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Caso Lima, borrador de la red (norte arriba). Círculos: semáforos. Flechas: sentido. "
                 "Entre paréntesis: carriles.", fontsize=10)
    ax.plot([px - r + 20, px - r + 120], [py - r + 20, py - r + 20], color="black", lw=2)
    ax.text(px - r + 70, py - r + 27, "100 m", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(args.salida, dpi=110)
    print("\nDibujo:", args.salida)


if __name__ == "__main__":
    main()
