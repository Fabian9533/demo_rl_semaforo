"""
satelite_corredor.py - Panel (a) de la Figura fig:corredor-satelite de la tesis: la captura satelital de Google Maps del
corredor de la Av. Benavides, de Larco a Republica de Panama, con el norte arriba y a la misma escala que el panel
principal del panel (b) (images/fig_corredor_red.pdf, de red_corredor.py: el corredor entero). Encima, un punto donde
cae cada uno de los seis cruces de la red (C1 a C6) y su nombre.

Como se ubica la captura sobre la red (registro):
  1. Los autores enviaron dos capturas del mismo tramo (el 20.11.2026): la vista de satelite,
     que es la que se publica, y la vista de mapa, cuyas calles son de un color parejo y se pueden medir. Google dibuja
     los mismos iconos en las dos. El dibujo de cada icono calza pixel a pixel de una vista a la otra (ICONOS); con esos
     pares se ajusta un polinomio de grado 2 que pasa del mapa al satelite. No basta un traslado: la vista de satelite
     de Google es una vista 3D en perspectiva (se ven los costados de los edificios altos) y su escala cambia ~1 % de
     oeste a este. El script imprime cuanto se aparta cada icono del polinomio.
  2. En el mapa, el eje de cada calle sale de lineas de barrido: en cada fila (las transversales) o columna (la
     avenida), el tramo continuo del color de calzada de Google y su punto medio. Las lineas se eligieron donde la calle
     no tiene rotulos, flechas ni iconos encima, y el script descarta las que dan un ancho distinto del de esa calle.
     El eje es la recta de minimos cuadrados por esos puntos medios; el de la avenida se ajusta cerca de cada cruce.
  3. El centro de cada cruce es el cruce del eje de la avenida con el de la transversal. En C4 la transversal es la
     Via Expresa: su eje es la linea media de sus dos calzadas centrales (el color oscuro del mapa). C5 es un cruce en
     T: su centro es el medio de la boca por la que Casimiro Ulloa entra a la avenida, sobre el eje de esta.
  4. Una semejanza (escala, giro y traslado) lleva los centros de C1, C2, C3 y C6 a los nodos de la red. C4 y C5 no
     entran al ajuste: la red junta en un nodo los dos cruces de Paseo de la Republica (sus dos pistas laterales, a
     62 m entre si) y C5 es la boca ancha de un cruce en T; de los dos se imprime cuanto se apartan. La escala da los
     metros por pixel y el giro, el rumbo de la avenida (en la red va recta de oeste a este).
  5. La captura se pone con el norte arriba, sin girarla ni remuestrearla: se recorta y se le da la escala de (b). Los
     puntos son los nodos de la red llevados a la captura con la semejanza. Un traslado este-oeste (minimos cuadrados)
     deja esos puntos a la altura de los cruces de (b): como la avenida real baja ~9 grados, el corredor se acorta en
     el este un 1.3 % (el coseno de 9 grados).

Lee (no escribe nada fuera de su salida; matplotlib con Agg, sin ventanas):
  capturas/benavides_satelite_larco_panama.png   Google Maps, vista de satelite con rotulos, sin capa de trafico
  capturas/benavides_mapa_larco_panama.png       Google Maps, vista de mapa del mismo tramo
  corredor_estudio2/demo_rl/lima/corredor/benavides.net.xml   la red (nodos C1 a C6 y, con --revision, carriles)
Escribe: TESIS/images/fig_corredor_satelite.pdf (la que usa la tesis) y, para mirarla, salida/fig_corredor_satelite.png.
  Con --revision, ademas salida/satelite_corredor_revision.png (la captura con los carriles de la red encima, llevados
  con la semejanza, y los centros medidos) y salida/satelite_corredor_barrido.png (el mapa con los puntos medios).

Uso:  python -B satelite_corredor.py [--revision]
Si cambia una captura, hay que revisar ICONOS, las lineas de barrido y los rotulos.
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
SATELITE = os.path.join(AQUI, "capturas", "benavides_satelite_larco_panama.png")
MAPA = os.path.join(AQUI, "capturas", "benavides_mapa_larco_panama.png")
RED = os.path.join(RAIZ, "corredor_estudio2", "demo_rl", "lima", "corredor", "benavides.net.xml")
SALIDA = os.path.join(os.path.dirname(AQUI), "TESIS", "images")
REVISION = os.path.join(AQUI, "salida")
NOMBRE = "fig_corredor_satelite"
CRUCES = ["C1", "C2", "C3", "C4", "C5", "C6"]
AJUSTE = ["C1", "C2", "C3", "C6"]                               # los que entran a la semejanza

# ---------------- marco: el del panel principal de red_corredor.py ----------------
DPI = 300
ANCHO_CM, MARGEN_CM = 15.0, 0.2
PRINCIPAL_X = (-70.0, 1298.0)          # m al este de C1, como el panel principal de (b)
ALTO_N = (-290.0, 90.0)                # m al norte de C1: la avenida baja ~200 m de C1 al borde este
BORDE_CM = 0.05                        # papel arriba y abajo del mapa
PAPEL, TINTA, BLANCO = "#ffffff", "#1c1c1a", "#ffffff"
T_ID, T_TEXTO = 8.5, 8.0               # puntos, con la figura a 15 cm (como red_corredor.py)
# Nombre de cada cruce: m al este y al norte de su punto (en un hueco sin rotulos de Google)
ROTULO = {"C1": (-26.0, 30.0), "C2": (0.0, 34.0), "C3": (16.0, -36.0), "C4": (-46.0, -30.0), "C5": (0.0, -38.0),
          "C6": (-30.0, -34.0)}
ESCALA = (-40.0, -262.0, 200.0)        # comienzo, altura y largo (m) de la escala grafica
NORTE = (1276.0, 4.0, 0.40)            # pie de la flecha de norte (m) y su largo en papel (cm)

# ---------------- paso del mapa al satelite: iconos de Google ----------------
# Centro aproximado de cada icono en la captura satelital (x, y en pixeles). En el satelite se ajusta el circulo blanco
# del icono; en el mapa se busca, cerca, el lugar donde su dibujo calza (SSD en un disco de 7 px de radio).
ICONOS = {"Municipalidad de Miraflores": (194, 46), "Unaluka": (1001, 143), "Atlantic City": (257, 383),
          "TP Sede Miraflores": (498, 382), "Centro Cultural Ricardo Palma": (155, 438), "Maido": (46, 443),
          "Punto Azul": (309, 549), "Trattoria Don Vito": (983, 421), "BCP": (1144, 479), "Wong": (1430, 515),
          "Markham College": (1595, 418), "Colegio Pestalozzi": (1716, 221), "St. George's College": (1937, 255),
          "McDonald's": (1857, 585), "Colegio Medico": (507, 768), "paradero sobre la Via Expresa": (725, 390)}
DESPLAZAMIENTO = (17.0, -27.0)         # mapa - satelite, aproximado: centro de la busqueda
RADIO_ICONO, BUSQUEDA, MAX_SSD = 7, 10, 30.0

# ---------------- barrido en el mapa (pixeles del mapa) ----------------
CALZADA = (211, 219, 227)              # calzada en la vista de mapa de Google
VIA_EXPRESA = (139, 165, 193)          # calzadas centrales de la Via Expresa
TOL = {"calzada": 6, "via": 8}


def guia_avenida(x):
    """Recta guia del eje de la avenida en el mapa (solo para buscar)."""
    return 339.0 + 0.158 * (x - 230.0)


# columnas limpias a cada lado de cada cruce y ancho aceptado de la avenida (px)
AVENIDA = {
    "C1": ([(100, 184), (202, 240)], (21, 26)),
    "C2": ([(202, 240), (400, 454)], (21, 26)),
    "C3": ([(400, 454), (466, 532)], (21, 26)),
    "C4": ([(600, 712), (820, 862)], None),            # el ancho cambia en C4: 21-26 al oeste, 28-32 al este
    "C5": ([(820, 862), (910, 994)], (28, 32)),
    "C6": ([(1372, 1402), (1426, 1440)], (28, 32)),
}
ANCHO_C4 = {"oeste": (21, 26), "este": (28, 32)}
# transversales: color, filas, x guia (recta: x0 + pendiente (y - y0)), ancho aceptado; las filas evitan los rotulos
TRANSVERSAL = {
    "C1": ("calzada", list(range(225, 306, 5)), (202.5, 250.0, -0.17), (15, 17)),
    "C2": ("calzada", list(range(285, 341, 5)), (356.0, 300.0, -0.07), (7, 11)),
    "C3": ("calzada", list(range(300, 356, 5)) + [460, 465, 470, 490, 500, 510, 520], (464.0, 300.0, -0.044), (7, 11)),
    "C4": ("via", list(range(300, 396, 5)) + list(range(460, 551, 10)), (732.5, 300.0, 0.25), (35, 56)),
    "C6": ("calzada", [455, 460, 465, 470, 475] + list(range(550, 631, 10)), (1413.5, 500.0, 0.0), (17, 20)),
}
BOCA_C5 = (850, 1000, 6.0)             # columnas donde buscar la boca de Casimiro Ulloa y cuanto sube el borde (px)
# Solo para informar (no cambia la figura): las dos pistas laterales de la Via Expresa, cada una de un sentido, son los
# dos cruces con semaforo que la red junta en C4. Filas al norte de la avenida (al sur hay rampas), x guia y ancho.
LATERALES_C4 = {"oeste": (list(range(320, 396, 5)), (713.5, 340.0, 0.20), (13, 17)),
                "este": (list(range(320, 396, 5)), (766.5, 340.0, 0.29), (7, 11))}


def sha(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# ---------------- iconos y polinomio ----------------
def circulo_blanco(img, x, y, r=16):
    v = img[y - r:y + r + 1, x - r:x + r + 1]
    ys, xs = np.nonzero(np.all(v > 235, axis=2))
    X, Y = xs + x - r + 0.5, ys + y - r + 0.5
    A = np.column_stack([2 * X, 2 * Y, np.ones_like(X)])
    (cx, cy, c), *_ = np.linalg.lstsq(A, X ** 2 + Y ** 2, rcond=None)
    return cx, cy, math.sqrt(c + cx ** 2 + cy ** 2)


def pares_de_iconos(sat, mapa):
    yy, xx = np.mgrid[-RADIO_ICONO:RADIO_ICONO + 1, -RADIO_ICONO:RADIO_ICONO + 1]
    disco = xx ** 2 + yy ** 2 <= RADIO_ICONO ** 2
    pares = []
    for nombre, (x, y) in ICONOS.items():
        cx, cy, _ = circulo_blanco(sat, x, y)
        i, j = int(cy), int(cx)                                  # pixel del centro
        plantilla = sat[i - RADIO_ICONO:i + RADIO_ICONO + 1, j - RADIO_ICONO:j + RADIO_ICONO + 1]
        pi, pj = i + round(DESPLAZAMIENTO[1]), j + round(DESPLAZAMIENTO[0])
        mejor = (np.inf, 0, 0)
        for di in range(-BUSQUEDA, BUSQUEDA + 1):
            for dj in range(-BUSQUEDA, BUSQUEDA + 1):
                a, b = pi + di, pj + dj
                w = mapa[a - RADIO_ICONO:a + RADIO_ICONO + 1, b - RADIO_ICONO:b + RADIO_ICONO + 1]
                ssd = float(np.mean(((w - plantilla) ** 2).sum(axis=2)[disco]))
                mejor = min(mejor, (ssd, a - i, b - j))
        ssd, di, dj = mejor
        if ssd > MAX_SSD:
            print(f"  AVISO: el icono '{nombre}' no calza en el mapa (SSD {ssd:.0f}); queda fuera")
            continue
        pares.append((nombre, (cx, cy), (cx + dj, cy + di), ssd))
    return pares


def base_poly(x, y):
    x, y = (np.asarray(x) - 1000.0) / 1000.0, (np.asarray(y) - 450.0) / 1000.0
    return np.column_stack([np.ones_like(x), x, y, x * x, x * y, y * y])


def mapa_a_satelite(pares):
    m = np.array([p[2] for p in pares])
    s = np.array([p[1] for p in pares])
    B = base_poly(m[:, 0], m[:, 1])
    cu, *_ = np.linalg.lstsq(B, s[:, 0], rcond=None)
    cv, *_ = np.linalg.lstsq(B, s[:, 1], rcond=None)

    def f(x, y):
        b = base_poly(np.atleast_1d(x), np.atleast_1d(y))
        return np.column_stack([b @ cu, b @ cv])
    res = f(m[:, 0], m[:, 1]) - s
    return f, res


# ---------------- barrido ----------------
def tramos(mascara_linea, desde, hueco):
    idx = np.nonzero(mascara_linea)[0]
    if len(idx) == 0:
        return []
    grupos, ini, ant = [], idx[0], idx[0]
    for k in idx[1:]:
        if k - ant > hueco + 1:
            grupos.append((desde + ini, desde + ant))
            ini = k
        ant = k
    grupos.append((desde + ini, desde + ant))
    return grupos


def medio_en_fila(masc, y, x_guia, ventana, hueco, extremos=False, largo_min=1):
    """Punto medio del tramo de calzada de la fila y cerca de x_guia: el que contiene la guia (o el mas cercano) o,
    con extremos=True, del primero al ultimo de los tramos de al menos largo_min px en la ventana. Devuelve (x, ancho)."""
    x0, x1 = int(x_guia - ventana), int(x_guia + ventana)
    gs = [g for g in tramos(masc[y, x0:x1], x0, hueco) if g[1] - g[0] + 1 >= largo_min]
    if not gs:
        return None
    if extremos:
        a, b = gs[0][0], gs[-1][1]
    else:
        a, b = min(gs, key=lambda g: 0 if g[0] <= x_guia <= g[1] + 1 else min(abs(g[0] - x_guia), abs(g[1] + 1 - x_guia)))
    return (a + b + 1) / 2, b - a + 1


def borde_en_columna(masc, x, hueco=3, ventana=40):
    """Tramo de la avenida en la columna x: (arriba, abajo) en coordenadas continuas, o None."""
    yg = guia_avenida(x)
    y0, y1 = int(yg - ventana), int(yg + ventana)
    gs = tramos(masc[y0:y1, x], y0, hueco)
    if not gs:
        return None
    a, b = min(gs, key=lambda g: 0 if g[0] <= yg <= g[1] + 1 else min(abs(g[0] - yg), abs(g[1] + 1 - yg)))
    return a, b + 1


def recta(us, vs):
    """v = p u + q por minimos cuadrados; devuelve (p, q, rms)."""
    A = np.column_stack([us, np.ones(len(us))])
    (p, q), *_ = np.linalg.lstsq(A, vs, rcond=None)
    return p, q, float(np.sqrt(np.mean((A @ np.array([p, q]) - vs) ** 2)))


def eje_avenida(masc, c, puntos):
    rangos, ancho = AVENIDA[c]
    xs, ys = [], []
    for k, (a, b) in enumerate(rangos):
        acept = ancho or (ANCHO_C4["oeste"] if k == 0 else ANCHO_C4["este"])
        for x in range(a, b + 1):
            t = borde_en_columna(masc, x)
            if t and acept[0] <= t[1] - t[0] <= acept[1]:
                xs.append(x + 0.5)
                ys.append((t[0] + t[1]) / 2)
    p, q, rms = recta(np.array(xs), np.array(ys))
    puntos.extend(zip(xs, ys))
    return p, q, rms, len(xs)


def eje_transversal(mascaras, c, puntos):
    color, filas, (x0, y0, m), (amin, amax) = TRANSVERSAL[c]
    masc = mascaras[color]
    ys, xs = [], []
    for y in filas:
        r = medio_en_fila(masc, y, x0 + m * (y - y0), 35 if color == "via" else 20, hueco=5,
                          extremos=color == "via", largo_min=8 if color == "via" else 1)
        if r and amin <= r[1] <= amax:
            ys.append(y + 0.5)
            xs.append(r[0])
    p, q, rms = recta(np.array(ys), np.array(xs))              # x = p y + q
    puntos.extend(zip(xs, ys))
    return p, q, rms, len(ys)


def centros_en_mapa(mapa, puntos):
    mascaras = {k: np.all(np.abs(mapa - np.array(col)) <= TOL[k], axis=2)
                for k, col in (("calzada", CALZADA), ("via", VIA_EXPRESA))}
    centros = {}
    for c in CRUCES:
        pa, qa, rms_a, na = eje_avenida(mascaras["calzada"], c, puntos)
        if c in TRANSVERSAL:
            pt, qt, rms_t, nt = eje_transversal(mascaras, c, puntos)
            # y = pa x + qa ; x = pt y + qt
            y = (pa * qt + qa) / (1 - pa * pt)
            x = pt * y + qt
            print(f"  {c}: avenida {na:3d} columnas (rms {rms_a:.2f} px), transversal {nt:2d} filas (rms {rms_t:.2f} px) "
                  f"-> centro ({x:7.1f}, {y:6.1f}) en el mapa")
            if c == "C4":
                for lado, (filas, (gx, gy, gm), (amin, amax)) in LATERALES_C4.items():
                    ys_, xs_ = [], []
                    for yy in filas:
                        r = medio_en_fila(mascaras["calzada"], yy, gx + gm * (yy - gy), 12, hueco=3)
                        if r and amin <= r[1] <= amax:
                            ys_.append(yy + 0.5)
                            xs_.append(r[0])
                    p, q, rms = recta(np.array(ys_), np.array(xs_))
                    yl = (pa * q + qa) / (1 - pa * p)
                    centros[f"C4 lateral {lado}"] = (p * yl + q, yl)
                    print(f"      lateral {lado} de la Via Expresa: {len(ys_)} filas (rms {rms:.2f} px) -> cruza la "
                          f"avenida en ({p * yl + q:7.1f}, {yl:6.1f})")
        else:
            # C5, en T: la boca es el tramo de columnas donde el borde norte de la avenida sube mas de BOCA_C5[2] px
            a, b, sube = BOCA_C5
            bordes = []
            for xx in range(a, b + 1):
                t = borde_en_columna(mascaras["calzada"], xx)
                if t:
                    bordes.append((xx, t[0], t[1]))
            # borde norte normal: recta por los bordes de arriba de las columnas de ancho aceptado
            acept = AVENIDA[c][1]
            ok = [(xx + 0.5, t0) for xx, t0, t1 in bordes if acept[0] <= t1 - t0 <= acept[1]]
            pn, qn, _ = recta(np.array([u for u, _ in ok]), np.array([v for _, v in ok]))
            boca = [xx for xx, t0, t1 in bordes if t0 < pn * (xx + 0.5) + qn - sube]
            # el tramo continuo mas largo de columnas de boca
            grupos = tramos(np.isin(np.arange(a, b + 1), boca), a, 1)
            g = max(grupos, key=lambda g: g[1] - g[0])
            x = (g[0] + g[1] + 1) / 2
            y = pa * x + qa
            print(f"  {c}: avenida {na:3d} columnas (rms {rms_a:.2f} px); boca de Casimiro Ulloa en las columnas "
                  f"{g[0]} a {g[1]} -> centro ({x:7.1f}, {y:6.1f}) en el mapa")
        centros[c] = (x, y)
    return centros


# ---------------- red ----------------
def leer_red():
    raiz = ET.parse(RED).getroot()
    nodos = {j.get("id"): (float(j.get("x")), float(j.get("y"))) for j in raiz.iter("junction")}
    carriles = []
    for e in raiz.iter("edge"):
        for ln in e.iter("lane"):
            forma = [tuple(map(float, q.split(","))) for q in ln.get("shape").split()]
            carriles.append((e.get("function") == "internal", forma))
    return nodos, carriles


# ---------------- figura ----------------
def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "ps.fonttype": 42})
    sat = np.asarray(Image.open(SATELITE).convert("RGB"))
    mapa = np.asarray(Image.open(MAPA).convert("RGB"))
    for ruta, im in ((SATELITE, sat), (MAPA, mapa)):
        print(f"Captura: {ruta}\n  {im.shape[1]} x {im.shape[0]} px, sha256 {sha(ruta)}")
    print(f"Red: {RED}\n  sha256 {sha(RED)}")
    nodos, carriles = leer_red()

    # 1. mapa -> satelite
    pares = pares_de_iconos(sat.astype(float), mapa.astype(float))
    f, res = mapa_a_satelite(pares)
    print(f"Iconos: {len(pares)} calzan (SSD de 0 a {max(p[3] for p in pares):.1f}); mapa - satelite de "
          f"{min(p[2][0] - p[1][0] for p in pares):+.0f} a {max(p[2][0] - p[1][0] for p in pares):+.0f} px en x y de "
          f"{min(p[2][1] - p[1][1] for p in pares):+.0f} a {max(p[2][1] - p[1][1] for p in pares):+.0f} px en y")
    print(f"  polinomio de grado 2, mapa -> satelite: residuo rms {np.sqrt((res ** 2).sum(1).mean()):.2f} px, maximo "
          f"{np.sqrt((res ** 2).sum(1)).max():.2f} px")

    # 2-3. centros en el mapa y en el satelite
    puntos = []
    centros_m = centros_en_mapa(mapa.astype(int), puntos)
    centros_s = {c: tuple(f(*centros_m[c])[0]) for c in centros_m}

    # 4. semejanza Z = a z + b, z = u - i v (satelite, pixeles) y Z = x + i y (red, m)
    z = np.array([centros_s[c][0] - 1j * centros_s[c][1] for c in AJUSTE])
    Z = np.array([nodos[c][0] + 1j * nodos[c][1] for c in AJUSTE])
    (a, b), *_ = np.linalg.lstsq(np.column_stack([z, np.ones(len(z))]), Z, rcond=None)
    k = abs(a)                                                   # m por pixel
    giro = math.degrees(np.angle(a))
    print(f"Semejanza con {', '.join(AJUSTE)}: {1 / k:.4f} px por metro ({k:.4f} m por px), giro {giro:+.2f} grados "
          f"(rumbo de la avenida en la captura: {-giro:+.2f} grados desde el este)")
    for c in CRUCES:
        zc = centros_s[c][0] - 1j * centros_s[c][1]
        r = a * zc + b - (nodos[c][0] + 1j * nodos[c][1])
        nota = "" if c in AJUSTE else "  (fuera del ajuste)"
        print(f"  {c}: captura ({centros_s[c][0]:7.1f}, {centros_s[c][1]:6.1f}) px -> se aparta {abs(r):5.2f} m del nodo "
              f"({r.real:+6.2f} a lo largo, {r.imag:+6.2f} de lado){nota}")
    lat = {lado: a * (centros_s[f"C4 lateral {lado}"][0] - 1j * centros_s[f"C4 lateral {lado}"][1]) + b
           for lado in LATERALES_C4}
    print("  Via Expresa: sus laterales cruzan la avenida a "
          + " y ".join(f"{lat[lado].real - nodos['C1'][0]:.1f} m ({lado})" for lado in LATERALES_C4)
          + f" del nodo C1, a lo largo de la red: {abs(lat['este'] - lat['oeste']):.1f} m entre si; el nodo C4 esta a "
          f"{nodos['C4'][0] - nodos['C1'][0]:.1f} m")

    # 5. puesta con el norte arriba: E = (u - u1) k + delta, N = -(v - v1) k
    inv = lambda X, Y: (((X + 1j * Y) - b) / a)
    en_cap = {c: inv(*nodos[c]) for c in CRUCES}                 # nodo de la red en la captura (u - i v)
    u1, v1 = en_cap["C1"].real, -en_cap["C1"].imag
    E = {c: (en_cap[c].real - u1) * k for c in CRUCES}
    N = {c: -(-en_cap[c].imag - v1) * k for c in CRUCES}
    x_red = {c: nodos[c][0] - nodos["C1"][0] for c in CRUCES}
    delta = float(np.mean([x_red[c] - E[c] for c in CRUCES]))
    E = {c: E[c] + delta for c in CRUCES}
    print(f"Norte arriba: traslado este-oeste de {delta:+.1f} m; cada cruce respecto de (b): "
          + ", ".join(f"{c} {E[c] - x_red[c]:+.1f} m" for c in CRUCES))
    a_px = lambda e: u1 + (e - delta) / k
    b_px = lambda n: v1 - n / k
    x0, x1 = PRINCIPAL_X
    n0, n1 = ALTO_N
    u_a, u_b, v_a, v_b = a_px(x0), a_px(x1), b_px(n1), b_px(n0)
    print(f"Panel: x de {x0:.0f} a {x1:.0f} m y de {n0:.0f} a {n1:.0f} m; en la captura, u de {u_a:.1f} a {u_b:.1f} y v de "
          f"{v_a:.1f} a {v_b:.1f} px")
    assert 0 <= u_a and u_b <= sat.shape[1] and 0 <= v_a and v_b <= sat.shape[0], "el panel se sale de la captura"
    # recorte entero, un pixel mas por lado, con su extension exacta en metros
    ia, ib, ja, jb = int(math.floor(v_a)) - 1, int(math.ceil(v_b)) + 1, int(math.floor(u_a)) - 1, int(math.ceil(u_b)) + 1
    ia, ja = max(ia, 0), max(ja, 0)
    recorte = sat[ia:ib, ja:jb]
    ext = ((ja - u1) * k + delta, (jb - u1) * k + delta, -(ib - v1) * k, -(ia - v1) * k)

    cm_m = (ANCHO_CM - 2 * MARGEN_CM) / (x1 - x0)
    alto_mapa = (n1 - n0) * cm_m
    alto = alto_mapa + 2 * BORDE_CM
    fig = plt.figure(figsize=(ANCHO_CM / 2.54, alto / 2.54), facecolor=PAPEL)
    ax = fig.add_axes([MARGEN_CM / ANCHO_CM, BORDE_CM / alto, (ANCHO_CM - 2 * MARGEN_CM) / ANCHO_CM, alto_mapa / alto])
    im = ax.imshow(recorte, extent=ext, interpolation="none", zorder=1)
    ax.set_xlim(x0, x1)
    ax.set_ylim(n0, n1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(TINTA)
        s.set_linewidth(0.6)
    halo = [pe.withStroke(linewidth=2.2, foreground=TINTA)]
    # cruces de la red: punto blanco con borde oscuro y su nombre
    r_punto = 0.06 / cm_m                                        # 0.6 mm de radio
    for c in CRUCES:
        ax.add_patch(plt.Circle((E[c], N[c]), r_punto, fc=BLANCO, ec=TINTA, lw=0.8, zorder=6))
        dx, dy = ROTULO[c]
        ax.text(E[c] + dx, N[c] + dy, c, fontsize=T_ID, weight="bold", color=BLANCO, ha="center", va="center",
                zorder=7, path_effects=halo)
    # escala grafica: 200 m con la marca de 100 m, como el panel principal de (b)
    ex, ey, metros = ESCALA
    sube = 0.09 / cm_m
    trazo = dict(color=BLANCO, zorder=7, solid_capstyle="butt", path_effects=[pe.withStroke(linewidth=2.6,
                                                                                            foreground=TINTA)])
    ax.plot([ex, ex + metros], [ey, ey], lw=1.2, **trazo)
    for v in (0.0, metros / 2, metros):
        ax.plot([ex + v, ex + v], [ey, ey + sube], lw=0.8, **trazo)
        ax.text(ex + v, ey + 1.6 * sube, f"{v:.0f}" + (" m" if v == metros else ""), fontsize=T_TEXTO, color=BLANCO,
                ha="center", va="bottom", zorder=7, path_effects=halo)
    # norte
    nx, ny, largo_cm = NORTE
    flecha = ax.annotate("", xy=(nx, ny + largo_cm / cm_m), xytext=(nx, ny), zorder=7,
                         arrowprops=dict(arrowstyle="-|>", color=BLANCO, lw=1.0, mutation_scale=8, shrinkA=0,
                                         shrinkB=0))
    flecha.arrow_patch.set_path_effects([pe.withStroke(linewidth=2.6, foreground=TINTA)])
    ax.text(nx, ny + largo_cm / cm_m + 0.04 / cm_m, "N", fontsize=T_TEXTO, color=BLANCO, ha="center", va="bottom",
            zorder=7, path_effects=halo)

    os.makedirs(SALIDA, exist_ok=True)
    os.makedirs(REVISION, exist_ok=True)
    pdf, png = os.path.join(SALIDA, NOMBRE + ".pdf"), os.path.join(REVISION, NOMBRE + ".png")
    fig.savefig(pdf, dpi=DPI, facecolor=PAPEL)
    im.set_interpolation("bicubic")
    fig.savefig(png, dpi=DPI, facecolor=PAPEL)
    print(f"Figura: {ANCHO_CM:.1f} x {alto:.2f} cm; mapa de {alto_mapa:.2f} cm de alto; escala 1:{100 / cm_m:.0f}; "
          f"recorte de {recorte.shape[1]} x {recorte.shape[0]} px ({recorte.shape[1] / ((ANCHO_CM - 2 * MARGEN_CM) / 2.54):.0f}"
          f" pixeles por pulgada impresa)")
    print("Escrito", pdf, f"({os.path.getsize(pdf) / 1e6:.2f} MB)")
    print("Escrito", png)
    plt.close(fig)

    if "--revision" in sys.argv:
        revision(sat, mapa, a, b, centros_s, nodos, carriles, puntos)


def revision(sat, mapa, a, b, centros_s, nodos, carriles, puntos):
    """Para mirar a ojo: la captura con los carriles de la red encima (llevados con la semejanza), y el mapa con los
    puntos medios del barrido."""
    inv = lambda X, Y: ((X + 1j * Y) - b) / a
    fig = plt.figure(figsize=(sat.shape[1] / 150, sat.shape[0] / 150), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(sat, interpolation="none")
    for interno, forma in carriles:
        q = [inv(X, Y) for X, Y in forma]
        ax.plot([w.real for w in q], [-w.imag for w in q], color="#ff00ff" if interno else "#00e5ff",
                lw=0.4 if interno else 0.7)
    for c in CRUCES:
        w = inv(*nodos[c])
        ax.plot(w.real, -w.imag, "o", ms=7, mfc="none", mec="#ff3030", mew=1.2)
        ax.plot(*centros_s[c], "+", ms=10, color="#ffff00", mew=1.2)
        ax.text(w.real + 8, -w.imag - 8, c, color="#ffff00", fontsize=9)
    ax.set_xlim(0, sat.shape[1])
    ax.set_ylim(sat.shape[0], 0)
    ax.axis("off")
    rev = os.path.join(REVISION, "satelite_corredor_revision.png")
    fig.savefig(rev, dpi=150)
    plt.close(fig)
    print("Escrito", rev, "(cian: carriles de la red; magenta: sus tramos internos; circulo rojo: nodo de cada cruce; "
          "cruz amarilla: el centro medido)")
    fig = plt.figure(figsize=(mapa.shape[1] / 150, mapa.shape[0] / 150), dpi=150)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(mapa, interpolation="none")
    ax.plot([p[0] for p in puntos], [p[1] for p in puntos], ".", ms=1.5, color="#ff00ff")
    ax.set_xlim(0, mapa.shape[1])
    ax.set_ylim(mapa.shape[0], 0)
    ax.axis("off")
    bar = os.path.join(REVISION, "satelite_corredor_barrido.png")
    fig.savefig(bar, dpi=150)
    plt.close(fig)
    print("Escrito", bar, "(magenta: puntos medios del barrido)")


if __name__ == "__main__":
    main()
