"""
satelite_ovalo.py - Panel (a) de la Figura fig:lima-nudo-satelite de la tesis: la captura satelital de Google Maps del
Ovalo Vasco, con el norte arriba, en la misma zona, a la misma escala y en el mismo marco que el mapa de la red de SUMO
del panel (b) (images/fig_ovalo_mapa.pdf, de carriles_reducto_2026-11-18/validacion2/dibujar_mapa.py, que la tesis
recorta sin su leyenda). Asi las dos se leen lado a lado.

Como se pone la captura sobre la red (registro):
  1. La capa de trafico de Google Maps dibuja una linea de color por el eje de cada calzada. Para cada lado del ovalo
     (las dos calzadas de Reducto y las dos de 28 de Julio, entre sus esquinas) se juntan los pixeles de su color
     dentro de una ventana fija (LADOS) y se ajusta una recta (minimos cuadrados totales).
  2. Las cuatro esquinas de la captura son los cruces de esas rectas.
  3. Una semejanza (escala, giro y traslado), ajustada por minimos cuadrados, lleva esas cuatro esquinas a los nodos
     NO, NE, SO y SE de la red. El script imprime la escala, el giro y cuanto se aparta cada esquina.
  4. Con esa semejanza, la captura se remuestrea (bicubico, a su propia resolucion) sobre el cuadrado de 120 m del mapa
     de la red, centrado en el promedio de las cuatro esquinas, como el panel (b).

Lee (no escribe nada fuera de su salida; matplotlib con Agg, sin ventanas):
  capturas/ovalo_satelite_con_trafico.png   Google Maps, vista satelite con la capa de trafico, norte arriba
                                            (enviada por los autores el 20.11.2026)
  nudo_ovalo_estudio2/demo_rl/lima/lima.net.xml   la red del nudo (los nodos de las esquinas y, con --revision, los
                                            carriles)
Escribe: TESIS/images/fig_ovalo_satelite.pdf (la que usa la tesis) y, para mirarla, salida/fig_ovalo_satelite.png.
  Con --revision, ademas salida/satelite_ovalo_revision.png: la captura ya puesta, con el eje de cada carril de la red
  encima, para ver a ojo que calzan.

Uso:  python -B satelite_ovalo.py [--revision] [--captura PNG] [--red NET]
Si la captura cambia (otra toma, otro encuadre), hay que revisar las ventanas de LADOS: el script avisa si una ventana
junta pocos pixeles o si la recta queda gruesa.
"""
import hashlib
import math
import os
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))                   # demo_rl_semaforo


def opcion(nombre, defecto):
    return sys.argv[sys.argv.index(nombre) + 1] if nombre in sys.argv else defecto


CAPTURA = opcion("--captura", os.path.join(AQUI, "capturas", "ovalo_satelite_con_trafico.png"))
RED = opcion("--red", os.path.join(RAIZ, "nudo_ovalo_estudio2", "demo_rl", "lima", "lima.net.xml"))
SALIDA = os.path.join(os.path.dirname(AQUI), "TESIS", "images")
REVISION = os.path.join(AQUI, "salida")
NOMBRE = "fig_ovalo_satelite"

# ---------------- marco: el de dibujar_mapa.py (version de la tesis, sin titulo) ----------------
DPI = 300
PX_CM = DPI / 2.54
ANCHO_CM, MARGEN_CM, ALTO_LEYENDA_CM, RADIO = 16.0, 0.2, 3.5, 60.0
MARGEN_PX = round(MARGEN_CM * PX_CM) + 0.5                      # 24.5
LADO_PX = 2 * round((ANCHO_CM - 2 * MARGEN_CM) * PX_CM / 2)     # 1842: el lado del mapa
AJUSTE_PX = 0.05
LEY_PX = round(ALTO_LEYENDA_CM * PX_CM) + 0.5                   # 413.5: la leyenda de (b)
ANCHO_PX = 2 * MARGEN_PX + LADO_PX + 0.02                       # 1891.02, el ancho de fig_ovalo_mapa.pdf
ALTO_B_PX = MARGEN_PX + LADO_PX + LEY_PX + 0.02                 # 2280.02, su alto
# La tesis recorta (b) con trim={0 3.39cm 0 0}: le quita la leyenda y deja el marco del mapa entero, con 12 px de papel
# debajo. Este panel mide lo mismo que (b) ya recortado y pone el mapa en el mismo lugar.
RECORTE_CM = 3.39
ALTO_PX = ALTO_B_PX - RECORTE_CM * PX_CM                        # 1879.63
BAJO_MAPA_PX = LEY_PX + AJUSTE_PX - RECORTE_CM * PX_CM          # 13.16: del borde de abajo al mapa
PAPEL, TINTA, BLANCO = "#ffffff", "#1c1c1a", "#ffffff"
# En la tesis el panel va a 0.485 del ancho del texto (7.3 cm de los 16 cm de la figura): la letra se imprime a 0.45
# de su tamano. 15 pt quedan en 6.8 pt.
T_ROTULO = 15.0
NORTE = (52.5, 41.6, 9.0)      # pie de la flecha de norte y su largo (m del centro): los de (b)
ESCALA = (-43.0, -56.8, 20.0)  # comienzo de la escala grafica y su largo (m): los de (b)

# ---------------- registro ----------------
# Color de la capa de trafico de cada lado del ovalo (RGB) y ventana de la captura (x0, x1, y0, y1, en pixeles) donde
# solo esta la linea de ese lado: cada ventana deja fuera las esquinas, las otras lineas y los rotulos de Google.
AMARILLO, VERDE, ROJO = (255, 207, 67), (22, 224, 152), (169, 39, 39)
TOLERANCIA = 30
LADOS = {
    "oeste": (AMARILLO, (690, 722, 396, 524)),   # Reducto hacia el sur, de NO a SO
    "este": (VERDE, (806, 830, 414, 522)),       # Reducto hacia el norte, de SE a NE
    "norte": (AMARILLO, (712, 804, 376, 412)),   # 28 de Julio hacia Larco, de NE a NO
    "sur": (ROJO, (724, 806, 524, 550)),         # 28 de Julio hacia el puente, de SO a SE
}
ESQUINAS = {"NO": ("oeste", "norte"), "NE": ("este", "norte"), "SO": ("oeste", "sur"), "SE": ("este", "sur")}
MIN_PIXELES, MAX_GROSOR = 150, 4.0             # avisos: pocos pixeles o recta gruesa (rms perpendicular, px)


def sha(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def recta(img, color, ventana):
    """Recta por los pixeles del color dado dentro de la ventana: punto medio, direccion unitaria, cuantos pixeles y
    rms de su distancia a la recta. Coordenadas continuas: el pixel (i, j) ocupa [i, i+1) x [j, j+1)."""
    x0, x1, y0, y1 = ventana
    trozo = img[y0:y1, x0:x1].astype(int)
    marca = np.all(np.abs(trozo - np.array(color)) <= TOLERANCIA, axis=2)
    ys, xs = np.nonzero(marca)
    p = np.column_stack([xs + x0 + 0.5, ys + y0 + 0.5])
    c = p.mean(axis=0)
    val, vec = np.linalg.eigh(np.cov((p - c).T))
    d = vec[:, np.argmax(val)]
    perp = (p - c) @ np.array([-d[1], d[0]])
    return c, d, len(p), float(np.sqrt(np.mean(perp ** 2)))


def cruce(r1, r2):
    (c1, d1), (c2, d2) = r1, r2
    t = np.linalg.solve(np.column_stack([d1, -d2]), c2 - c1)
    return c1 + t[0] * d1


def nodos(red):
    raiz = ET.parse(red).getroot()
    esq = {j.get("id"): (float(j.get("x")), float(j.get("y"))) for j in raiz.iter("junction") if j.get("id") in ESQUINAS}
    carriles = []
    for e in raiz.iter("edge"):
        for ln in e.iter("lane"):
            forma = [tuple(map(float, q.split(","))) for q in ln.get("shape").split()]
            carriles.append((e.get("function") == "internal", forma))
    return esq, carriles


def main():
    img = np.asarray(Image.open(CAPTURA).convert("RGB"))
    print(f"Captura: {CAPTURA}\n  {img.shape[1]} x {img.shape[0]} px, sha256 {sha(CAPTURA)}")
    print(f"Red: {RED}\n  sha256 {sha(RED)}")
    esq_red, carriles = nodos(RED)

    rectas = {}
    for lado, (color, ventana) in LADOS.items():
        c, d, n, rms = recta(img, color, ventana)
        rectas[lado] = (c, d)
        ang = math.degrees(math.atan2(-d[1], d[0])) % 180
        aviso = "  <- AVISO" if n < MIN_PIXELES or rms > MAX_GROSOR else ""
        print(f"  lado {lado:5s}: {n:5d} pixeles, rms {rms:.2f} px, rumbo {ang:6.1f} grados{aviso}")
    esq_cap = {k: cruce(rectas[a], rectas[b]) for k, (a, b) in ESQUINAS.items()}

    # semejanza Z = a z + b, con z = u - i v (pixeles, y hacia abajo) y Z = E + i N (m de la red)
    ks = list(ESQUINAS)
    z = np.array([esq_cap[k][0] - 1j * esq_cap[k][1] for k in ks])
    Z = np.array([esq_red[k][0] + 1j * esq_red[k][1] for k in ks])
    (a, b), *_ = np.linalg.lstsq(np.column_stack([z, np.ones(len(z))]), Z, rcond=None)
    print(f"Semejanza: {1 / abs(a):.3f} px por metro ({abs(a):.4f} m por px), giro {math.degrees(np.angle(a)):+.2f} grados")
    for k, zk, Zk in zip(ks, z, Z):
        r = a * zk + b - Zk
        print(f"  {k}: captura ({zk.real:7.1f}, {-zk.imag:7.1f}) px -> se aparta {abs(r):.2f} m del nodo "
              f"({r.real:+.2f} E, {r.imag:+.2f} N)")
    lados_cap = {n: abs(a) * math.dist(esq_cap[p], esq_cap[q])
                 for n, (p, q) in {"norte": ("NO", "NE"), "oeste": ("NO", "SO"), "este": ("NE", "SE"),
                                   "sur": ("SO", "SE")}.items()}
    lados_red = {n: math.dist(esq_red[p], esq_red[q])
                 for n, (p, q) in {"norte": ("NO", "NE"), "oeste": ("NO", "SO"), "este": ("NE", "SE"),
                                   "sur": ("SO", "SE")}.items()}
    print("  Lados del ovalo, captura con esa escala / red (m): "
          + ", ".join(f"{n} {lados_cap[n]:.2f} / {lados_red[n]:.2f}" for n in lados_red))

    # remuestreo sobre el cuadrado del mapa, a la resolucion de la captura
    cx = sum(p[0] for p in esq_red.values()) / 4
    cy = sum(p[1] for p in esq_red.values()) / 4
    n_out = round(2 * RADIO / abs(a))
    k = 2 * RADIO / n_out
    z0 = complex(cx - RADIO, cy + RADIO) - b
    z0, zx, zy = z0 / a, k / a, -1j * k / a
    datos = (zx.real, zy.real, z0.real, -zx.imag, -zy.imag, -z0.imag)
    puesta = Image.fromarray(img).transform((n_out, n_out), Image.AFFINE, datos, resample=Image.BICUBIC)
    lim = (0, 0, img.shape[1], img.shape[0])
    for X, Y in ((0, 0), (n_out, 0), (0, n_out), (n_out, n_out)):
        u, v = datos[0] * X + datos[1] * Y + datos[2], datos[3] * X + datos[4] * Y + datos[5]
        if not (lim[0] <= u <= lim[2] and lim[1] <= v <= lim[3]):
            print(f"  AVISO: la esquina ({X}, {Y}) del mapa cae fuera de la captura ({u:.0f}, {v:.0f})")
    print(f"Mapa: {n_out} x {n_out} px para {2 * RADIO:.0f} m ({n_out / (2 * RADIO):.2f} px por metro), centro "
          f"({cx:.2f}, {cy:.2f})")

    fig = plt.figure(figsize=(ANCHO_PX / DPI, ALTO_PX / DPI), facecolor=PAPEL)
    ax = fig.add_axes([(MARGEN_PX - AJUSTE_PX) / ANCHO_PX, BAJO_MAPA_PX / ALTO_PX, LADO_PX / ANCHO_PX,
                       LADO_PX / ALTO_PX])
    ext = (cx - RADIO, cx + RADIO, cy - RADIO, cy + RADIO)
    im = ax.imshow(np.asarray(puesta), extent=ext, interpolation="none", zorder=1)
    ax.set_xlim(ext[0], ext[1])
    ax.set_ylim(ext[2], ext[3])
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(TINTA)
        s.set_linewidth(0.6)
    halo = [pe.withStroke(linewidth=3.2, foreground=TINTA)]
    # norte
    x, y, alto = cx + NORTE[0], cy + NORTE[1], NORTE[2]
    flecha = ax.annotate("", xy=(x, y + alto), xytext=(x, y), zorder=5,
                         arrowprops=dict(arrowstyle="-|>", color=BLANCO, lw=2.0, mutation_scale=20,
                                         shrinkA=0, shrinkB=0))
    flecha.arrow_patch.set_path_effects([pe.withStroke(linewidth=4.4, foreground=TINTA)])
    ax.text(x, y + alto + 0.9, "N", fontsize=T_ROTULO, color=BLANCO, ha="center", va="bottom", zorder=5,
            path_effects=halo)
    # escala grafica: 20 m con la marca de 10 m, como (b)
    x, y, metros = cx + ESCALA[0], cy + ESCALA[1], ESCALA[2]
    trazo = dict(color=BLANCO, zorder=5, solid_capstyle="butt",
                 path_effects=[pe.withStroke(linewidth=4.6, foreground=TINTA)])
    ax.plot([x, x + metros], [y, y], lw=2.2, **trazo)
    # cada numero centrado en su marca y la "m" aparte, a la derecha del ultimo (a esta letra, "20 m" centrado
    # quedaba pegado al "10")
    rend = fig.canvas.get_renderer()
    for v in (0.0, metros / 2, metros):
        ax.plot([x + v, x + v], [y, y + 1.6], lw=1.4, **trazo)
        t = ax.text(x + v, y + 2.4, f"{v:.0f}", fontsize=T_ROTULO, color=BLANCO, ha="center", va="bottom",
                    zorder=5, path_effects=halo)
    borde = ax.transData.inverted().transform(t.get_window_extent(rend))[1][0]
    ax.text(borde + 0.9, y + 2.4, "m", fontsize=T_ROTULO, color=BLANCO, ha="left", va="bottom", zorder=5,
            path_effects=halo)

    # la tesis usa el PDF; el PNG (4 MB de foto) es solo para mirarlo y va a salida/, fuera del repositorio
    os.makedirs(SALIDA, exist_ok=True)
    os.makedirs(REVISION, exist_ok=True)
    pdf, png = os.path.join(SALIDA, NOMBRE + ".pdf"), os.path.join(REVISION, NOMBRE + ".png")
    fig.savefig(pdf, dpi=DPI, facecolor=PAPEL)
    im.set_interpolation("bicubic")
    fig.savefig(png, dpi=DPI, facecolor=PAPEL)
    print("Escrito", pdf, f"({os.path.getsize(pdf) / 1e6:.2f} MB)")
    print("Escrito", png)

    if "--revision" in sys.argv:
        for interno, forma in carriles:
            xs, ys = zip(*forma)
            ax.plot(xs, ys, color="#ff00ff" if interno else "#00e5ff", lw=0.5 if interno else 0.8, zorder=6)
        for kk, (ex, ey) in esq_red.items():
            ax.plot(ex, ey, "o", ms=5, mfc="none", mec="#ff3030", mew=1.2, zorder=7)
            Zc = a * (esq_cap[kk][0] - 1j * esq_cap[kk][1]) + b
            ax.plot(Zc.real, Zc.imag, "+", ms=8, color="#ffff00", mew=1.2, zorder=7)
        os.makedirs(REVISION, exist_ok=True)
        rev = os.path.join(REVISION, "satelite_ovalo_revision.png")
        fig.savefig(rev, dpi=DPI, facecolor=PAPEL)
        print("Escrito", rev, "(cian: carriles de la red; magenta: sus tramos internos; circulo rojo: nodo de cada "
              "esquina; cruz amarilla: la esquina de la captura)")
    plt.close(fig)


if __name__ == "__main__":
    main()
