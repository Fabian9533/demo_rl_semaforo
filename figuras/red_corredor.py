"""
red_corredor.py - La red de SUMO del corredor de la Av. Benavides (caso Lima, estudio 2 del corredor), para ponerla
en la tesis bajo una captura satelital del mismo tramo. Dibuja la red tal como esta en el archivo, con el norte
arriba: un panel a todo lo ancho con el corredor entero y dos recuadros ampliados, a la misma escala, donde se
distinguen los carriles (A: C1 a C3; B: C4 y C5).

Solo lee (no simula; matplotlib con Agg, sin ventanas; no escribe nada en la carpeta del caso):
  benavides.net.xml   la red (sumolib): carriles, uniones y enlaces de los semaforos
  benavides.rou.xml   la demanda (XML): que accesos no tienen vehiculos (los que el modelo agrega)
  corredor.py         CRUCES y SOLO_NORTE, leidos con ast (sin importar el modulo, que dejaria su cache al lado)

Uso:  python -B red_corredor.py                        # TESIS/images/fig_corredor_red.pdf y .png
      python -B red_corredor.py --guia                 # solo para revisar: salida/red_corredor_guia.png, con cuadricula
      python -B red_corredor.py --caso DIR             # otra carpeta del caso
Tambien imprime lo que la figura afirma (cruces, carriles de cada tramo, accesos sin vehiculos, lineas de parada,
extension y escala de cada panel, huella de la red) y avisa si un rotulo pisa una calzada, otro rotulo o el marco.

Decisiones de dibujo que no son datos de la red:
  - Color de cada carril segun su sentido de marcha; son los colores de la figura del nudo para el mismo sentido
    (hacia el sur, azul como Reducto desde el norte; hacia el norte, naranja como Reducto desde el sur; hacia el
    este, verde como Balboa; hacia el oeste, rosado como 28 de Julio desde el puente).
  - Los accesos sin vehiculos (la calle no los tiene: el modelo da cuatro accesos a cada cruce) van en gris claro,
    con su carril punteado y su linea de parada gris.
  - Extension de cada panel (PRINCIPAL, RECUADROS), donde va cada rotulo, la escala y la flecha de norte.
"""
import ast
import hashlib
import math
import os
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Polygon, Rectangle  # noqa: E402
from matplotlib.path import Path  # noqa: E402
from matplotlib.transforms import offset_copy  # noqa: E402

sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
import sumolib  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))                  # demo_rl_semaforo


def opcion(nombre, defecto):
    return sys.argv[sys.argv.index(nombre) + 1] if nombre in sys.argv else defecto


CASO = opcion("--caso", os.path.join(RAIZ, "corredor_estudio2", "demo_rl", "lima", "corredor"))
# la figura va a TESIS/images; la guia (--guia), solo para revisar, a figuras/salida
SALIDA = opcion("--salida", os.path.join(AQUI, "salida") if "--guia" in sys.argv
                else os.path.join(os.path.dirname(AQUI), "TESIS", "images"))
RED = os.path.join(CASO, "benavides.net.xml")
RUTAS = os.path.join(CASO, "benavides.rou.xml")
CODIGO = os.path.join(CASO, "corredor.py")
NOMBRE = "fig_corredor_red"

# ---------------- sistema visual (el de la figura del nudo, fig_ovalo_mapa) ----------------
COLOR = {"sur": "#0072B2", "norte": "#D55E00", "este": "#009E73", "oeste": "#CC79A7"}
SENTIDOS = ("este", "oeste", "norte", "sur")
PAPEL, FONDO = "#ffffff", "#f6f5f1"
CALZADA, BORDILLO = "#d6d5cf", "#9a9993"
FANTASMA, GRIS_F = "#ecebe6", "#8a8984"       # acceso sin vehiculos: calzada y trazos
TINTA, TINTA2 = "#1c1c1a", "#4a4946"
AVENIDA = "Av. Alfredo Benavides"

ANCHO_CM = 15.0                # ancho de la figura impresa (el del texto de la tesis)
MARGEN_CM = 0.2                # a cada lado de los paneles
# Letra, en puntos, con la figura a 15 cm: nada por debajo de 8
T_ID, T_CALLE, T_LEYENDA, T_LETRA = 8.5, 8.0, 8.0, 9.0

# Extension de cada panel, en metros: x al este del centro del cruce con Larco (C1), y al norte del eje de la avenida
PRINCIPAL = (-70.0, 1298.0, -100.0, 100.0)
RECUADROS = {"A": (-45.0, 315.0, -50.0, 50.0), "B": (520.0, 730.0, -50.0, 50.0)}
HUECO_RECUADROS_CM = 0.4       # entre los dos recuadros
# Grosores (pt) y tamanos en papel (mm) de cada panel: el principal va a ~0.11 mm por metro y los recuadros a ~0.25
ESTILO = {
    "principal": {"borde": 0.45, "carril": 0.32, "parada": 1.0, "punto_mm": 0.42, "flechas": False},
    "recuadro": {"borde": 0.9, "carril": 0.7, "parada": 1.5, "punto_mm": 0.55, "flechas": True},
}
FLECHA_MM = (1.05, 0.62)       # largo y ancho de las puntas de flecha de los carriles en los recuadros (mm)

# Rotulos dentro de los recuadros: metros al este y al norte del centro de cada cruce (van en un hueco sin calzada)
ROTULO_RECUADRO = {"C1": (26.0, 27.0), "C2": (26.0, 27.0), "C3": (26.0, 27.0), "C4": (26.0, 27.0),
                   "C5": (26.0, 27.0)}
ESCALA_PRINCIPAL = (760.0, -72.0, 200.0)     # comienzo, altura y largo (m) de la escala del panel principal
ESCALA_RECUADRO = ("A", 22.0, -40.0, 100.0)  # recuadro, comienzo, altura y largo (m)
NORTE = (1165.0, 14.0, 0.50)                 # pie de la flecha de norte (m) y su largo en papel (cm)
ROTULO_AVENIDA = (950.0, 14.0)               # centro del nombre de la avenida (m), sobre su borde norte


# ---------------- geometria ----------------
def largo(forma):
    return sum(math.dist(a, b) for a, b in zip(forma, forma[1:]))


def en(forma, s):
    """Punto y direccion (unitaria) a la distancia s del comienzo de la polilinea."""
    acum = 0.0
    for a, b in zip(forma, forma[1:]):
        t = math.dist(a, b)
        if t > 0 and acum + t >= s:
            f = max(0.0, (s - acum) / t)
            return (a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])), ((b[0] - a[0]) / t, (b[1] - a[1]) / t)
        acum += t
    a, b = forma[-2], forma[-1]
    t = math.dist(a, b) or 1.0
    return b, ((b[0] - a[0]) / t, (b[1] - a[1]) / t)


def normales(forma):
    """Normal a la izquierda de la marcha en cada punto de la polilinea."""
    res, n = [], len(forma)
    for k in range(n):
        a, b = forma[max(0, k - 1)], forma[min(n - 1, k + 1)]
        d = math.dist(a, b) or 1.0
        res.append((-(b[1] - a[1]) / d, (b[0] - a[0]) / d))
    return res


def desplazar(forma, d):
    """La polilinea corrida d metros a la izquierda de la marcha (d < 0: a la derecha)."""
    return [(p[0] + d * n[0], p[1] + d * n[1]) for p, n in zip(forma, normales(forma))]


def poligono_carril(forma, ancho):
    return desplazar(forma, ancho / 2) + desplazar(forma, -ancho / 2)[::-1]


def recorte(a, b, caja):
    """Parte visible del segmento a-b dentro de la caja (x0, x1, y0, y1): (t0, t1) o None (Liang-Barsky)."""
    x0, x1, y0, y1 = caja
    t0, t1 = 0.0, 1.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0:
            if q < 0:
                return None
            continue
        r = q / p
        if p < 0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
    return (t0, t1) if t0 < t1 else None


def sentido(forma):
    dx, dy = forma[-1][0] - forma[0][0], forma[-1][1] - forma[0][1]
    if abs(dx) >= abs(dy):
        return "este" if dx > 0 else "oeste"
    return "norte" if dy > 0 else "sur"


def constantes(ruta, nombres):
    """Valores literales de las asignaciones de nivel superior de un .py, sin ejecutarlo."""
    with open(ruta, encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    res = {}
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and len(nodo.targets) == 1 and isinstance(nodo.targets[0], ast.Name) \
                and nodo.targets[0].id in nombres:
            res[nodo.targets[0].id] = ast.literal_eval(nodo.value)
    assert set(res) == set(nombres), f"faltan {set(nombres) - set(res)} en {ruta}"
    return res


def huella(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# ---------------- lectura de la red ----------------
class Red:
    def __init__(self):
        cod = constantes(CODIGO, ("CRUCES", "SOLO_NORTE"))
        self.cruces = [(c, calle, x) for c, calle, x, _, _ in cod["CRUCES"]]
        self.ids = [c for c, _, _ in self.cruces]
        self.nombre = {c: calle for c, calle, _ in self.cruces}
        net = self.net = sumolib.net.readNet(RED, withInternal=True)
        self.origen = net.getNode(self.ids[0]).getCoord()[:2]
        # un semaforo por cruce, en el nodo del cruce, y en el lugar que da corredor.py
        con_semaforo = sorted(n.getID() for n in net.getNodes() if n.getType() == "traffic_light")
        assert con_semaforo == sorted(self.ids), con_semaforo
        self.pos = {c: self.p(net.getNode(c).getCoord()) for c in self.ids}
        for c, _, x in self.cruces:
            assert abs(self.pos[c][0] - x) < 0.05 and abs(self.pos[c][1]) < 0.05, (c, self.pos[c], x)
        self.normales = list(net.getEdges(withInternal=False))
        self.sentido = {e.getID(): sentido(self.forma(e.getLanes()[0])) for e in self.normales}
        # todos los carriles que llegan a un cruce tienen enlace con su semaforo
        self.enlaces = {t.getID(): len(t.getConnections()) for t in net.getTrafficLights()}
        enlazados = {a.getID() for t in net.getTrafficLights() for a, _, _ in t.getConnections()}
        self.accesos = [e for e in self.normales if e.getToNode().getID() in self.ids]
        sueltos = [l.getID() for e in self.accesos for l in e.getLanes() if l.getID() not in enlazados]
        assert not sueltos, f"carriles que llegan a un cruce sin semaforo: {sueltos}"
        self._fantasmas(cod)
        self._calzada()
        self._paradas()

    def p(self, q):
        return (q[0] - self.origen[0], q[1] - self.origen[1])

    def forma(self, carril):
        return [self.p(q) for q in carril.getShape()]

    def _fantasmas(self, cod):
        """Accesos sin vehiculos: entradas a la red por las que no entra ningun flujo. Deben ser los que corredor.py
        agrega para que cada cruce tenga cuatro accesos: el sentido que falta en una calle de un solo sentido y la
        rama sur de un cruce en T."""
        raiz = ET.parse(RUTAS).getroot()
        assert not list(raiz.iter("vehicle")) and not list(raiz.iter("route")), "la demanda no es solo de flujos"
        desde = {f.get("from") for f in raiz.iter("flow")} | {f.get("from") for f in raiz.iter("trip")}
        entradas = [e for e in self.normales if e.getFromNode().getID() not in self.ids]   # nacen en un borde
        self.fantasmas = sorted(e.getID() for e in entradas if e.getID() not in desde)
        esperado = set()
        for k, (c, _, _, n, s) in enumerate(cod["CRUCES"], start=1):
            if n is None:
                esperado.add(f"N{k}_{c}")
            if s is None or c in cod["SOLO_NORTE"]:
                esperado.add(f"S{k}_{c}")
        assert set(self.fantasmas) == esperado, (self.fantasmas, esperado)
        assert all(self.net.getEdge(e).getLaneNumber() == 1 for e in self.fantasmas)
        self.cruce_fantasma = {e: self.net.getEdge(e).getToNode().getID() for e in self.fantasmas}

    def _calzada(self):
        """Lo pavimentado: el poligono de cada carril (los internos de los cruces tambien) y la forma de cada union.
        Los carriles de los accesos sin vehiculos van aparte."""
        self.calzada, self.calzada_fantasma, self.lineas = [], [], []
        for e in self.net.getEdges(withInternal=True):
            fantasma = e.getID() in self.fantasmas
            for carril in e.getLanes():
                forma = self.forma(carril)
                if len(forma) < 2:
                    continue
                (self.calzada_fantasma if fantasma else self.calzada).append(
                    poligono_carril(forma, carril.getWidth()))
                if e.getFunction() != "internal":
                    self.lineas.append((forma, self.sentido[e.getID()], fantasma))
        for nodo in self.net.getNodes():
            forma = [self.p(q) for q in nodo.getShape()]
            if len(forma) > 2:
                self.calzada.append(forma)

    def _paradas(self):
        """Una linea de parada por acceso a un cruce: de borde a borde de su calzada, en el final de sus carriles."""
        self.paradas = []
        for e in self.accesos:
            extremos = []
            for carril in e.getLanes():
                forma, medio = self.forma(carril), carril.getWidth() / 2
                q, u = en(forma, largo(forma))
                extremos.append(((q[0] + u[1] * medio, q[1] - u[0] * medio),      # borde derecho del carril
                                 (q[0] - u[1] * medio, q[1] + u[0] * medio)))     # borde izquierdo
            self.paradas.append({"tramo": e.getID(), "cruce": e.getToNode().getID(), "a": extremos[0][0],
                                 "b": extremos[-1][1], "fantasma": e.getID() in self.fantasmas})

    def carriles_entre(self, a, b):
        """Carriles del tramo de avenida que va de a hacia b (nombres de nodo)."""
        for e in self.normales:
            if e.getFromNode().getID() == a and e.getToNode().getID() == b:
                return e.getLaneNumber()
        return None


# ---------------- dibujo de un panel ----------------
def punta(ax, p, u, largo_m, ancho_m, color, z):
    n = (-u[1], u[0])
    a = (p[0] + u[0] * largo_m / 2, p[1] + u[1] * largo_m / 2)
    b = (p[0] - u[0] * largo_m / 2, p[1] - u[1] * largo_m / 2)
    ax.add_patch(Polygon([a, (b[0] + n[0] * ancho_m / 2, b[1] + n[1] * ancho_m / 2),
                          (b[0] - n[0] * ancho_m / 2, b[1] - n[1] * ancho_m / 2)], closed=True, fc=color, ec="none",
                         zorder=z))


def dibujar_red(ax, red, caja, cm_m, estilo):
    """La red dentro de la caja (x0, x1, y0, y1), con cm_m cm de papel por metro."""
    mm_m = cm_m * 10
    x0, x1, y0, y1 = caja
    ax.set_facecolor(FONDO)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(TINTA)
        s.set_linewidth(0.6)
    # calzada: primero todo con el color del bordillo y borde grueso; encima, con el de la calzada (del borde solo
    # queda el contorno de afuera). Los accesos sin vehiculos, aparte y mas claros, con borde punteado.
    for forma in red.calzada:
        ax.add_patch(Polygon(forma, closed=True, fc=BORDILLO, ec=BORDILLO, lw=estilo["borde"], joinstyle="round",
                             zorder=2.0))
    for forma in red.calzada:
        ax.add_patch(Polygon(forma, closed=True, fc=CALZADA, ec=CALZADA, lw=0.2, joinstyle="round", zorder=2.1))
    for forma in red.calzada_fantasma:
        ax.add_patch(Polygon(forma, closed=True, fc=FANTASMA, ec=GRIS_F, lw=estilo["borde"] * 0.75,
                             ls=(0, (1.6, 1.4)), joinstyle="miter", zorder=2.2))
    # un trazo fino por carril, en el color de su sentido
    for forma, sent, fantasma in red.lineas:
        if fantasma:
            ax.plot(*zip(*forma), color=GRIS_F, lw=estilo["carril"], ls=(0, (1.0, 1.8)), zorder=4,
                    dash_capstyle="butt")
        else:
            ax.plot(*zip(*forma), color=COLOR[sent], lw=estilo["carril"], zorder=4, solid_capstyle="butt")
    if estilo["flechas"]:
        flechas_de_carril(ax, red, caja, mm_m)
    for linea in red.paradas:
        (ax0, ay0), (bx0, by0) = linea["a"], linea["b"]
        ax.plot([ax0, bx0], [ay0, by0], color=GRIS_F if linea["fantasma"] else TINTA, lw=estilo["parada"],
                solid_capstyle="butt", zorder=6)
    r = estilo["punto_mm"] / mm_m
    for c in red.ids:
        ax.add_patch(Circle(red.pos[c], r, fc=TINTA, ec="none", zorder=7))


def flechas_de_carril(ax, red, caja, mm_m):
    """Una punta de flecha por carril (no en los accesos sin vehiculos), en la mitad de su parte visible."""
    x0, x1, y0, y1 = caja
    hueco = 3.0 / mm_m                                   # 3 mm del marco
    adentro = (x0 + hueco, x1 - hueco, y0 + hueco, y1 - hueco)
    largo_m, ancho_m = FLECHA_MM[0] / mm_m, FLECHA_MM[1] / mm_m
    for forma, sent, fantasma in red.lineas:
        if fantasma:
            continue
        a, b = forma[0], forma[-1]
        assert len(forma) == 2, "carril que no es recto"
        tramo = recorte(a, b, adentro)
        if tramo is None or (tramo[1] - tramo[0]) * math.dist(a, b) < 4.0 / mm_m:
            continue
        t = (tramo[0] + tramo[1]) / 2
        p = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        d = math.dist(a, b)
        punta(ax, p, ((b[0] - a[0]) / d, (b[1] - a[1]) / d), largo_m, ancho_m, COLOR[sent], 5)


def texto(ax, x, y, s, **kw):
    kw.setdefault("color", TINTA)
    kw.setdefault("zorder", 10)
    kw.setdefault("clip_on", False)
    return ax.text(x, y, s, **kw)


def escala(ax, x, y, metros, cm_m, marcas):
    """Escala grafica: barra con marcas y numeros encima."""
    sube = 0.09 / cm_m                                   # alto de las marcas: 0.9 mm
    textos = []
    ax.plot([x, x + metros], [y, y], color=TINTA, lw=1.1, zorder=9, solid_capstyle="butt")
    for v in marcas:
        ax.plot([x + v, x + v], [y, y + sube], color=TINTA, lw=0.6, zorder=9, solid_capstyle="butt")
        textos.append(texto(ax, x + v, y + 1.6 * sube, f"{v:.0f}" + (" m" if v == metros else ""),
                            fontsize=T_LEYENDA, ha="center", va="bottom"))
    return textos


def panel_principal(fig, ax, red, cm_m):
    caja = PRINCIPAL
    dibujar_red(ax, red, caja, cm_m, ESTILO["principal"])
    x0, x1, y0, y1 = caja
    textos, de_fuera = [], []
    # cruces: C1, C3 y C5 arriba del marco; C2, C4 y C6 abajo. El codigo del cruce queda sobre su calle y el nombre,
    # mas afuera, centrado sobre ella si cabe dentro del ancho del marco
    rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    for k, c in enumerate(red.ids):
        x = red.pos[c][0]
        arriba = k % 2 == 0
        signo, y, va = (1, y1, "bottom") if arriba else (-1, y0, "top")
        t_id = texto(ax, x, y, c, fontsize=T_ID, weight="bold", ha="center", va=va,
                     transform=offset_copy(ax.transData, fig=fig, y=signo * 2.0, units="points"))
        t_nom = texto(ax, x, y, red.nombre[c], fontsize=T_CALLE, ha="center", va=va,
                      transform=offset_copy(ax.transData, fig=fig, y=signo * (2.0 + 10.5), units="points"))
        caja_nom = t_nom.get_window_extent(rend)
        izq, der = inv.transform((caja_nom.x0, 0))[0], inv.transform((caja_nom.x1, 0))[0]
        if izq < x0:
            t_nom.set_x(x0)
            t_nom.set_ha("left")
        elif der > x1:
            t_nom.set_x(x1)
            t_nom.set_ha("right")
        de_fuera += [t_id, t_nom]
    # nombre de la avenida, escala, norte y zonas ampliadas
    textos.append(texto(ax, *ROTULO_AVENIDA, AVENIDA, fontsize=T_CALLE, ha="center", va="bottom"))
    ex, ey, metros = ESCALA_PRINCIPAL
    textos += escala(ax, ex, ey, metros, cm_m, (0.0, metros / 2, metros))
    nx, ny, alto_cm = NORTE
    alto = alto_cm / cm_m
    cabeza_l, cabeza_a = 0.20 / cm_m, 0.15 / cm_m
    ax.plot([nx, nx], [ny, ny + alto - cabeza_l], color=TINTA2, lw=0.9, zorder=9, solid_capstyle="butt")
    punta(ax, (nx, ny + alto - cabeza_l / 2), (0.0, 1.0), cabeza_l, cabeza_a, TINTA2, 9)
    textos.append(texto(ax, nx, ny + alto + 0.04 / cm_m, "N", fontsize=T_CALLE, ha="center", va="bottom",
                        color=TINTA2))
    for letra, (rx0, rx1, ry0, ry1) in RECUADROS.items():
        ax.add_patch(Rectangle((rx0, ry0), rx1 - rx0, ry1 - ry0, fill=False, ec=TINTA2, lw=0.6, zorder=8))
        textos.append(texto(ax, rx0, ry1 + 0.04 / cm_m, letra, fontsize=T_LETRA, weight="bold", ha="left",
                            va="bottom", color=TINTA2))
    return textos, de_fuera


def panel_recuadro(fig, ax, red, letra, cm_m):
    caja = RECUADROS[letra]
    dibujar_red(ax, red, caja, cm_m, ESTILO["recuadro"])
    x0, x1, y0, y1 = caja
    textos = [texto(ax, x0 + 0.12 / cm_m, y1 - 0.08 / cm_m, letra, fontsize=T_LETRA, weight="bold", ha="left",
                    va="top", color=TINTA2)]
    llamar = []
    for c in red.ids:
        cx, cy = red.pos[c]
        if not (x0 < cx < x1):
            continue
        dx, dy = ROTULO_RECUADRO[c]
        t = texto(ax, cx + dx, cy + dy, c, fontsize=T_ID, weight="bold", ha="center", va="center")
        textos.append(t)
        llamar.append((t, red.pos[c]))
    if ESCALA_RECUADRO[0] == letra:
        _, ex, ey, metros = ESCALA_RECUADRO
        textos += escala(ax, ex, ey, metros, cm_m, (0.0, metros / 2, metros))
    # linea de llamada de cada rotulo al centro de su cruce: sale del borde del rotulo, punteada y gris
    rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    r = ESTILO["recuadro"]["punto_mm"] / (cm_m * 10)
    for t, centro in llamar:
        caja_t = t.get_window_extent(rend)
        (a0, b0), (a1, b1) = inv.transform((caja_t.x0, caja_t.y0)), inv.transform((caja_t.x1, caja_t.y1))
        c, mx, my = ((a0 + a1) / 2, (b0 + b1) / 2), (a1 - a0) / 2 + 0.6, (b1 - b0) / 2 + 0.6
        m = math.dist(c, centro)
        u = ((centro[0] - c[0]) / m, (centro[1] - c[1]) / m)
        sale = min(mx / abs(u[0]) if u[0] else float("inf"), my / abs(u[1]) if u[1] else float("inf"))
        a = (c[0] + u[0] * sale, c[1] + u[1] * sale)
        b = (centro[0] - u[0] * (r + 0.8), centro[1] - u[1] * (r + 0.8))
        ax.plot([a[0], b[0]], [a[1], b[1]], color=TINTA2, lw=0.6, ls=(0, (1.0, 1.6)), zorder=6.5,
                dash_capstyle="butt")
    return textos


# ---------------- leyenda ----------------
LEYENDA_FILA_CM = 0.42         # distancia entre renglones de la leyenda
LEYENDA_DERECHA_CM = 6.9       # comienzo del bloque de la derecha (lineas y marcas)


def leyenda(fig, ax, ancho_cm, alto_cm, cm_m_recuadro):
    """Franja bajo los recuadros, en centimetros. A la izquierda, el color de cada sentido (cada muestra apunta hacia
    su sentido); a la derecha, la linea de parada, el centro de cada cruce y el acceso sin vehiculos."""
    ax.set_xlim(0, ancho_cm)
    ax.set_ylim(0, alto_cm)
    ax.axis("off")
    x0, paso = MARGEN_CM, LEYENDA_FILA_CM
    y = alto_cm - 0.24

    def fila(xx, yy, s, **kw):
        kw.setdefault("color", TINTA)
        return ax.text(xx, yy, s, fontsize=T_LEYENDA, ha="left", va="center", **kw)

    fila(x0, y, "Un trazo por carril, del color de su sentido:")
    largo_m, cab_l, cab_a = 0.55, 0.16, 0.12             # muestra de sentido: largo, y largo y ancho de la punta (cm)
    direccion = {"este": (1.0, 0.0), "oeste": (-1.0, 0.0), "norte": (0.0, 1.0), "sur": (0.0, -1.0)}
    for k, sent in enumerate(SENTIDOS):
        xx, yy = x0 + 3.05 * (k % 2), y - paso * (1 + k // 2)
        u = direccion[sent]
        medio = (xx + largo_m / 2, yy)
        mitad = largo_m / 2 if u[1] == 0 else 0.17      # las verticales caben en el renglon
        a = (medio[0] - u[0] * mitad, medio[1] - u[1] * mitad)
        b = (medio[0] + u[0] * mitad, medio[1] + u[1] * mitad)
        ax.plot([a[0], b[0] - u[0] * cab_l * 0.6], [a[1], b[1] - u[1] * cab_l * 0.6], color=COLOR[sent], lw=1.2,
                solid_capstyle="butt")
        punta(ax, (b[0] - u[0] * cab_l / 2, b[1] - u[1] * cab_l / 2), u, cab_l, cab_a, COLOR[sent], 3)
        fila(xx + largo_m + 0.2, yy, f"hacia el {sent}")
    xd, muestra = LEYENDA_DERECHA_CM, 0.8
    ax.plot([xd, xd + muestra], [y, y], color=TINTA, lw=1.5, solid_capstyle="butt")
    fila(xd + muestra + 0.2, y, "línea de parada de un acceso con semáforo")
    yy = y - paso
    ax.add_patch(Circle((xd + muestra / 2, yy), 0.055, fc=TINTA, ec="none"))
    fila(xd + muestra + 0.2, yy, "centro de cada cruce con semáforo")
    # acceso sin vehiculos: una franja del ancho de un carril de los recuadros, con su trazo punteado y su linea de
    # parada gris; el texto en dos renglones
    yy = y - paso * 2.5
    ancho = 3.2 * cm_m_recuadro
    ax.add_patch(Rectangle((xd, yy - ancho / 2), muestra, ancho, fc=FANTASMA, ec=GRIS_F, lw=0.7,
                           ls=(0, (1.6, 1.4))))
    ax.plot([xd, xd + muestra], [yy, yy], color=GRIS_F, lw=0.7, ls=(0, (1.0, 1.8)), dash_capstyle="butt")
    ax.plot([xd + muestra, xd + muestra], [yy - ancho / 2, yy + ancho / 2], color=GRIS_F, lw=1.5,
            solid_capstyle="butt")
    fila(xd + muestra + 0.2, yy + paso / 2, "acceso sin vehículos, que la calle no tiene")
    fila(xd + muestra + 0.2, yy - paso / 2, "(el modelo da cuatro accesos a cada cruce)", color=TINTA2)
    return ax


# ---------------- comprobaciones ----------------
def revisar(fig, red, mapas, de_fuera):
    """Avisa si un rotulo de un mapa pisa la calzada (o queda a menos de 0.3 mm), si dos textos se pisan, si un
    rotulo de un mapa toca su marco o si un texto se sale de la figura."""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    avisos = []
    caminos = [Path(f) for f in red.calzada + red.calzada_fantasma]
    for ax, textos in mapas:
        inv = ax.transData.inverted()
        marco = ax.get_window_extent(rend)
        cm_m = (ax.get_window_extent(rend).width / fig.dpi * 2.54) / (ax.get_xlim()[1] - ax.get_xlim()[0])
        holgura = 0.03 / cm_m
        for t in textos:
            c = t.get_window_extent(rend)
            if c.x0 < marco.x0 + 1 or c.x1 > marco.x1 - 1 or c.y0 < marco.y0 + 1 or c.y1 > marco.y1 - 1:
                avisos.append(f"'{t.get_text()}' toca el marco")
            (x0, y0), (x1, y1) = inv.transform((c.x0, c.y0)), inv.transform((c.x1, c.y1))
            x0, y0, x1, y1 = x0 - holgura, y0 - holgura, x1 + holgura, y1 + holgura
            nx, ny = max(2, int((x1 - x0) / (holgura / 2))), max(2, int((y1 - y0) / (holgura / 2)))
            pts = [(x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny) for i in range(nx + 1) for j in range(ny + 1)]
            if any(cam.contains_points(pts).any() for cam in caminos):
                avisos.append(f"'{t.get_text()}' pisa una calzada o queda a menos de 0.3 mm")
    todos = [t for a in fig.axes for t in a.texts] + list(fig.texts)
    ancho, alto = fig.canvas.get_width_height()
    cajas = [(t.get_text(), t.get_window_extent(rend)) for t in todos if t.get_text()]
    for i, (s, c) in enumerate(cajas):
        if c.x0 < 1 or c.x1 > ancho - 1 or c.y0 < 1 or c.y1 > alto - 1:
            avisos.append(f"'{s}' se sale de la figura")
        for s2, c2 in cajas[i + 1:]:
            if c.x0 < c2.x1 and c2.x0 < c.x1 and c.y0 < c2.y1 and c2.y0 < c.y1:
                avisos.append(f"'{s}' y '{s2}' se pisan")
    # los rotulos de afuera no deben entrar al marco del panel principal
    marco = mapas[0][0].get_window_extent(rend)
    for t in de_fuera:
        c = t.get_window_extent(rend)
        if c.y0 < marco.y1 and c.y1 > marco.y0:
            avisos.append(f"'{t.get_text()}' entra al panel principal")
    return avisos


# ---------------- la figura ----------------
def figura(red, destinos, guia=False, dpi=300):
    ancho_util = ANCHO_CM - 2 * MARGEN_CM
    px0, px1, py0, py1 = PRINCIPAL
    cm_p = ancho_util / (px1 - px0)                             # cm de papel por metro, panel principal
    anchos = {k: v[1] - v[0] for k, v in RECUADROS.items()}
    cm_r = (ancho_util - HUECO_RECUADROS_CM * (len(RECUADROS) - 1)) / sum(anchos.values())
    altos_r = {k: (v[3] - v[2]) * cm_r for k, v in RECUADROS.items()}
    assert len(set(round(a, 6) for a in altos_r.values())) == 1, "los recuadros deben tener el mismo alto"
    alto_r = next(iter(altos_r.values()))
    alto_p = (py1 - py0) * cm_p
    rotulos = 0.80                                              # franja de rotulos arriba y abajo del principal
    alto_ley = 0.24 + 3 * LEYENDA_FILA_CM + 0.24
    arriba, hueco1, hueco2, abajo = 0.05, 0.30, 0.30, 0.05
    alto = arriba + rotulos + alto_p + rotulos + hueco1 + alto_r + hueco2 + alto_ley + abajo
    fig = plt.figure(figsize=(ANCHO_CM / 2.54, alto / 2.54), facecolor=PAPEL)

    def ejes(x, y, w, h):                                       # en cm desde la esquina inferior izquierda
        return fig.add_axes([x / ANCHO_CM, y / alto, w / ANCHO_CM, h / alto])

    y_r = abajo + alto_ley + hueco2
    y_p = y_r + alto_r + hueco1 + rotulos
    ax_p = ejes(MARGEN_CM, y_p, ancho_util, alto_p)
    textos_p, de_fuera = panel_principal(fig, ax_p, red, cm_p)
    mapas = [(ax_p, textos_p)]
    x = MARGEN_CM
    for letra in RECUADROS:
        ax_r = ejes(x, y_r, anchos[letra] * cm_r, alto_r)
        mapas.append((ax_r, panel_recuadro(fig, ax_r, red, letra, cm_r)))
        x += anchos[letra] * cm_r + HUECO_RECUADROS_CM
    ax_l = ejes(0, abajo, ANCHO_CM, alto_ley)
    leyenda(fig, ax_l, ANCHO_CM, alto_ley, cm_r)
    if guia:
        for ax, _ in mapas:
            xa, xb = ax.get_xlim()
            ya, yb = ax.get_ylim()
            paso = 100 if xb - xa > 500 else 10
            for v in range(int(xa // paso * paso), int(xb) + 1, paso):
                ax.axvline(v, color="#ff00ff", lw=0.15, zorder=20)
                ax.text(v, ya + 1, str(v), fontsize=3.5, color="#ff00ff", zorder=20)
            for v in range(int(ya // paso * paso), int(yb) + 1, paso):
                ax.axhline(v, color="#ff00ff", lw=0.15, zorder=20)
                ax.text(xa + 1, v, str(v), fontsize=3.5, color="#ff00ff", zorder=20)
    avisos = [] if guia else revisar(fig, red, mapas, de_fuera)
    for destino in destinos:
        fig.savefig(destino, dpi=dpi, facecolor=PAPEL)
        print("Escrito", destino)
    plt.close(fig)
    return avisos, {"cm_p": cm_p, "cm_r": cm_r, "alto": alto, "alto_p": alto_p, "alto_r": alto_r}


def datos(red, medidas):
    """Lo que la figura afirma, leido de la red."""
    net = red.net
    print("Red:", RED)
    print("sha256 de la red:", huella(RED))
    print("Semaforos (enlaces):", red.enlaces)
    print("Cruces (m al este de Larco, por la red) y transversal:")
    for c in red.ids:
        print(f"  {c} {red.pos[c][0]:7.1f} m  {red.nombre[c]}")
    print("Carriles de la avenida por tramo (hacia el este / hacia el oeste):")
    puntos = ["W"] + red.ids + ["E"]
    for a, b in zip(puntos, puntos[1:]):
        print(f"  {a}-{b}: {red.carriles_entre(a, b)} / {red.carriles_entre(b, a)}")
    print("Transversales (carriles por rama y sentido; * = acceso sin vehiculos):")
    for c in red.ids:
        ramas = []
        for e in red.normales:
            otro = e.getToNode().getID() if e.getFromNode().getID() == c else (
                e.getFromNode().getID() if e.getToNode().getID() == c else None)
            if otro is None or otro in red.ids or otro in ("W", "E"):
                continue
            rama = "norte" if red.p(net.getNode(otro).getCoord())[1] > 0 else "sur"
            ramas.append(f"rama {rama}: {e.getLaneNumber()} hacia el {red.sentido[e.getID()]}"
                         + ("*" if e.getID() in red.fantasmas else ""))
        print(f"  {c}: " + "; ".join(sorted(ramas)))
    print("Accesos sin vehiculos:", {e: red.cruce_fantasma[e] for e in red.fantasmas})
    print("Lineas de parada:", len(red.paradas), "| de accesos con vehiculos:",
          sum(not l["fantasma"] for l in red.paradas), "| sin vehiculos:", sum(l["fantasma"] for l in red.paradas))
    print("Anchos de carril (m):", sorted({l.getWidth() for e in red.normales for l in e.getLanes()}))
    avenida = [e for e in red.normales if e.getFromNode().getID() in puntos and e.getToNode().getID() in puntos]
    hueco = min(abs(red.forma(l)[0][1]) - l.getWidth() / 2 for e in avenida for l in e.getLanes())
    print(f"Separador central de la avenida: del eje al borde del carril mas cercano hay {hueco:.2f} m "
          "(0 = las dos calzadas se tocan, sin separador)")
    x0, x1, y0, y1 = PRINCIPAL
    print(f"Panel principal: x de {x0:.0f} a {x1:.0f} m del centro de C1 (de {-x0:.0f} m al oeste de Larco a "
          f"{x1 - red.pos[red.ids[-1]][0]:.0f} m al este de Republica de Panama), y de {y0:.0f} a {y1:.0f} m del eje; "
          f"escala 1:{1 / (medidas['cm_p'] / 100):.0f} ({medidas['cm_p'] * 10:.4f} mm por m); "
          f"alto del mapa {medidas['alto_p']:.2f} cm")
    for k, (a, b, c, d) in RECUADROS.items():
        print(f"Recuadro {k}: x de {a:.0f} a {b:.0f} m, y de {c:.0f} a {d:.0f} m; escala 1:{1 / (medidas['cm_r'] / 100):.0f}"
              f" ({medidas['cm_r'] * 10:.4f} mm por m); un carril de 3.2 m mide {3.2 * medidas['cm_r'] * 10:.2f} mm")
    print(f"Figura: {ANCHO_CM:.1f} x {medidas['alto']:.2f} cm")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "ps.fonttype": 42})
    red = Red()
    if "--guia" in sys.argv:
        figura(red, [os.path.join(SALIDA, "red_corredor_guia.png")], guia=True, dpi=300)
        return
    os.makedirs(SALIDA, exist_ok=True)
    avisos, medidas = figura(red, [os.path.join(SALIDA, f"{NOMBRE}.pdf"), os.path.join(SALIDA, f"{NOMBRE}.png")])
    datos(red, medidas)
    for a in sorted(set(avisos)):
        print("AVISO:", a)
    if not avisos:
        print("Rotulos: ninguno pisa una calzada, otro texto ni el marco; nada se sale de la figura")


if __name__ == "__main__":
    main()
