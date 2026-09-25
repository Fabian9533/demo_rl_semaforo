"""
barrer_fijo.py - Barrido del programa de tiempo fijo de un escenario para elegir el
baseline por la metrica primaria (timeLoss promedio por vehiculo), no por espera detenida.

Uso (plan v2: desde demo_rl/plan2, con los archivos del escenario en el cwd):
  python ../barrer_fijo.py corredor|corredor_alta|red|red_alta|malla3 [--semillas 2001-2003]
         [--tmp carpeta] [--procesos N] [--instalar] [--no-extender]
         [--avenida 20,25] [--transversal 10,15] [--limite N]
  python barrer_fijo.py cruce|cruce2 [--asimetrico]

cruce y cruce2: se regenera la red con netconvert para cada verde (y cada verde de giro
protegido en cruce2), igual que hace build_net.bat.
corredor, corredor_alta, red y red_alta: se reescribe el programa fijo del <esc>.add.xml del cwd
(la plantilla) con cada verde de avenida (eje E-O), cada verde transversal (N-S) y cada desfase.
malla3 (9 semaforos): verde de avenida x verde transversal x esquema de desfases de diseno
(cero, ajedrez, onda_eo) en vez de barrer desfases libres.
Las corridas son sumo puro (sin TraCI). Salida: barrido_<esc>.csv con el promedio de cada
configuracion sobre las semillas, ordenado por timeLoss.

Cambios del plan v2 (24.09.2026):
- Semillas por defecto 2001-2003 (las de tuneo; la evaluacion usa 1001-1030).
- Escenarios nuevos red_alta y malla3; mallas nuevas por celda (MALLAS).
- La fase verde de la avenida se detecta en el .net.xml (la que da verde a mas movimientos que
  llegan por aristas E-O), ya no esta escrita a mano por escenario.
- --procesos N: configuraciones en paralelo (hilos que lanzan sumo), cada una con su tripinfo
  propio dentro de --tmp. El resultado no depende de N.
- Interioridad: si el ganador queda en el borde de un eje de verde, imprime AVISO y (con
  --extender, activo por defecto) agrega un paso mas en ese eje y barre solo lo nuevo, hasta que
  el ganador quede interior. El verde minimo del agente (10 s) es un piso valido y no cuenta como
  borde; hacia arriba el techo es el verde maximo del agente (60 s). Los desfases no se extienden.
- --instalar: escribe <esc>.add.xml en el cwd con el programa ganador (programID "fijo" en cada
  semaforo) y un comentario con la malla barrida, las semillas y el retraso del ganador.
"""
import os
import csv
import copy
import argparse
import textwrap
import statistics
import subprocess
import concurrent.futures
import xml.etree.ElementTree as ET
from xml.sax.saxutils import quoteattr

import comun

SILENCIO = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
ESCENARIOS = ("cruce", "cruce2", "corredor", "corredor_alta", "red", "red_alta", "malla3")
VERDE_MIN = 10          # verde minimo del agente: piso valido del barrido
VERDE_TECHO = 60        # verde maximo del agente: el barrido no se extiende mas alla
DISTANCIA_MALLA = 300   # m entre cruces vecinos de malla3
VEL_DISENO = 13.89      # m/s (50 km/h), velocidad de la onda verde de diseno

# Malla de verdes por celda: (verdes de avenida E-O, verdes transversales N-S), en s.
MALLAS = {"corredor": ((12, 15, 18, 20, 25, 30), (10, 15, 20)),
          "corredor_alta": ((15, 20, 25, 30, 35), (10, 15, 20, 25)),
          "red": ((15, 20, 25, 30, 35), (10, 15, 20)),
          "red_alta": ((15, 20, 25, 30, 35), (10, 15, 20)),
          "malla3": ((15, 20, 25, 30, 35), (10, 15, 20, 25))}
ESQUEMAS_MALLA3 = ("cero", "ajedrez", "onda_eo")

DESPLEGADO = {"cruce": {"verde": 25}, "cruce2": {"verde": 20, "izquierda": 6},
              "corredor": {"verde": 20, "verde_tr": 10, "off2": 15},     # asimetrico desde 06.09
              "red": {"verde": 25, "verde_tr": 15, "off2": 23},          # asimetrico desde 06.09
              "red_alta": {"verde": 25, "verde_tr": 15, "off2": 23},     # hereda el esquema de red
              "corredor_alta": {"verde": 25, "verde_tr": 15, "off2": 25}}


def rango(texto):
    """'1001-1003' -> [1001, 1002, 1003]; '42' -> [42]"""
    if "-" in texto:
        a, b = texto.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(texto)]


def lista_enteros(texto):
    """'20,25' -> [20, 25]"""
    return [int(x) for x in texto.split(",") if x.strip()]


def correr_sumo(cfg, extra, seed, tripinfo):
    cmd = ["sumo", "-c", cfg, "--seed", str(seed), "--tripinfo-output", tripinfo,
           "--tripinfo-output.write-unfinished", "true", "--device.emissions.probability", "1",
           "--no-step-log", "true", "--no-warnings", "true"] + extra
    subprocess.run(cmd, check=True, **SILENCIO)
    return comun.leer_tripinfo(tripinfo)


def evaluar_config(cfg, nombre, extra, semillas, tmp):
    """Promedio de las metricas de una configuracion sobre las semillas (tripinfo propio)."""
    tripinfo = os.path.join(tmp, f"tripinfo_{nombre}.xml")
    res = [correr_sumo(cfg, extra, s, tripinfo) for s in semillas]
    os.remove(tripinfo)
    fila = {}
    for m in ("timeloss_prom", "espera_prom", "paradas_prom", "throughput", "co2_prom"):
        fila[m] = round(statistics.mean(float(r[m]) for r in res), 2)
    retrasos = [float(r["timeloss_prom"]) for r in res]
    fila["timeloss_sd"] = round(statistics.stdev(retrasos), 2) if len(res) > 1 else 0
    return fila


# ---------------------------------------------------------------- cruce y cruce2 (sin cambios)

def configs_cruce(esc, tmp):
    """Un net por verde (y por verde de giro en cruce2). La malla incluye la configuracion desplegada."""
    for verde in sorted(set(range(15, 43, 3)) | {DESPLEGADO[esc]["verde"]}):
        for izq in ([None] if esc == "cruce" else [6, 8, 10, 12]):
            nombre = f"{esc}_v{verde}" + (f"_l{izq}" if izq else "")
            net = os.path.join(tmp, nombre + ".net.xml")
            if not os.path.exists(net):
                cmd = ["netconvert", "--node-files", f"{esc}.nod.xml", "--edge-files", f"{esc}.edg.xml",
                       "--output-file", net, "--no-turnarounds", "--tls.green.time", str(verde)]
                if esc == "cruce2":
                    cmd += ["--connection-files", "cruce2.con.xml", "--tls.left-green.time", str(izq)]
                subprocess.run(cmd, check=True, **SILENCIO)
            params = {"verde": verde, "izquierda": izq if izq else "", "offsets": ""}
            yield nombre, params, ["--net-file", net]


def configs_cruce_asimetrico(esc, tmp):
    """Solo cruce: reparto asimetrico N-S x E-O escrito como programa 'fijo' en un .add.xml,
    porque netconvert solo admite un verde comun. 'verde' es el N-S y 'verde_transversal' el
    E-O (los dos ejes son principales, cada uno en una mitad de la hora). Incluye el 25/25."""
    verdes = (15, 20, 25, 30, 35, 40)
    for v_ns in verdes:
        for v_eo in verdes:
            nombre = f"{esc}_ns{v_ns}_eo{v_eo}"
            ruta = os.path.join(tmp, nombre + ".add.xml")
            if not os.path.exists(ruta):
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write('<additional>\n  <tlLogic id="semaforo_C" type="static" programID="fijo"'
                            ' offset="0">\n'
                            f'    <phase duration="{v_ns}" state="GGgrrrGGgrrr"/>\n'
                            '    <phase duration="3"  state="yyyrrryyyrrr"/>\n'
                            f'    <phase duration="{v_eo}" state="rrrGGgrrrGGg"/>\n'
                            '    <phase duration="3"  state="rrryyyrrryyy"/>\n'
                            '  </tlLogic>\n</additional>\n')
            yield (nombre, {"verde": v_ns, "izquierda": "", "verde_transversal": v_eo, "offsets": ""},
                   ["--additional-files", ruta])


# ---------------------------------------------------------------- escenarios con plantilla .add.xml

def leer_cfg(cfg):
    """(net-file, lista de additional-files) del .sumocfg."""
    raiz = ET.parse(cfg).getroot()
    net = raiz.find(".//net-file").get("value")
    nodo = raiz.find(".//additional-files")
    adicionales = [] if nodo is None else [a.strip() for a in nodo.get("value").split(",") if a.strip()]
    return net, adicionales


def geometria(net):
    """Por semaforo: posicion (x, y) del cruce y, por linkIndex, si el movimiento llega por una
    arista E-O (horizontal). Se lee de los nodos de las aristas no internas del .net.xml."""
    raiz = ET.parse(net).getroot()
    nodos = {j.get("id"): (float(j.get("x")), float(j.get("y"))) for j in raiz.findall("junction")}
    aristas = {e.get("id"): (e.get("from"), e.get("to")) for e in raiz.findall("edge")
               if e.get("function") != "internal"}
    geo = {}
    for c in raiz.findall("connection"):
        tls = c.get("tl")
        if not tls or c.get("from") not in aristas:
            continue
        desde, hasta = aristas[c.get("from")]
        (x0, y0), (x1, y1) = nodos[desde], nodos[hasta]
        g = geo.setdefault(tls, {"pos": (x1, y1), "horizontal": {}})
        g["horizontal"][int(c.get("linkIndex"))] = abs(x1 - x0) >= abs(y1 - y0)
    return geo


def es_verde(estado):
    return ("G" in estado or "g" in estado) and "y" not in estado


def fase_avenida(tl, horizontal):
    """Indice de la fase verde que sirve a la avenida: la que da verde a mas movimientos E-O
    (y menos N-S). Verificado: corredor fase 2, red fase 0."""
    mejor, puntaje = None, None
    for k, fase in enumerate(tl.findall("phase")):
        estado = fase.get("state")
        if not es_verde(estado):
            continue
        p = sum(1 if horizontal.get(i, False) else -1 for i, s in enumerate(estado) if s in "Gg")
        if puntaje is None or p > puntaje:
            mejor, puntaje = k, p
    return mejor


def cargar_plantilla(esc, net, adicionales):
    """Plantilla del programa fijo: el <esc>.add.xml del cwd o, si no existe, el primer additional
    del .sumocfg que tenga programas; si ninguno, los programas por defecto del .net.xml.
    Devuelve (arbol, ruta del archivo que reemplaza o None)."""
    for ruta in [f"{esc}.add.xml"] + adicionales:
        if os.path.exists(ruta) and ET.parse(ruta).getroot().findall("tlLogic"):
            return ET.parse(ruta), ruta
    raiz = ET.Element("additional")
    for tl in ET.parse(net).getroot().findall("tlLogic"):
        raiz.append(copy.deepcopy(tl))
    print(f"AVISO: no hay {esc}.add.xml con programas; se usa como plantilla el programa de {net}")
    return ET.ElementTree(raiz), None


def ciclo_de(tl, fase_av, verde_av, verde_tr):
    return sum(verde_av if k == fase_av else verde_tr if es_verde(f.get("state")) else int(f.get("duration"))
               for k, f in enumerate(tl.findall("phase")))


def atributos(d):
    return " ".join(f"{k}={quoteattr(str(v))}" for k, v in d.items())


def escribir_programa(plantilla, ruta, verde_av, verde_tr, offsets, fases_av, comentario=None):
    """Copia la plantilla con el verde de la avenida, el de las transversales y el offset de cada
    semaforo (en orden de aparicion). fases_av = indice de la fase de avenida de cada semaforo.
    Formato de corredor.add.xml / red.add.xml; programID "fijo" y type "static" en todos."""
    lineas = ["<additional>"]
    if comentario:
        texto = textwrap.wrap(comentario, 96)
        lineas.append("    <!-- " + "\n         ".join(texto) + " -->")
    i = 0
    for hijo in plantilla.getroot():
        if hijo.tag != "tlLogic":
            lineas.append("    " + ET.tostring(hijo, encoding="unicode").strip())
            continue
        a = dict(hijo.attrib)
        a.update(type="static", programID="fijo", offset=offsets[i])
        lineas.append(f"    <tlLogic {atributos(a)}>")
        for k, fase in enumerate(hijo):
            if fase.tag != "phase":
                lineas.append("        " + ET.tostring(fase, encoding="unicode").strip())
                continue
            f = dict(fase.attrib)
            if es_verde(f["state"]):
                f["duration"] = verde_av if k == fases_av[i] else verde_tr
            lineas.append(f"        <phase {atributos(f)}/>")
        lineas.append("    </tlLogic>")
        i += 1
    lineas.append("</additional>")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")


def desfases_malla3(ids, geo, ciclo, esquema):
    """Offsets de diseno de malla3 por semaforo (en orden de ids). Fila y columna se cuentan desde
    0 por la posicion del cruce (columna 0 = la mas al oeste).
    cero: todos 0; ajedrez: medio ciclo donde fila + columna es impar;
    onda_eo: columna * 300 m / 13.89 m/s (onda verde hacia el este) modulo el ciclo."""
    xs = sorted({round(geo[t]["pos"][0]) for t in ids})
    ys = sorted({round(geo[t]["pos"][1]) for t in ids})
    offsets = []
    for t in ids:
        col = xs.index(round(geo[t]["pos"][0]))
        fila = ys.index(round(geo[t]["pos"][1]))
        if esquema == "cero":
            offsets.append(0)
        elif esquema == "ajedrez":
            offsets.append(ciclo // 2 if (fila + col) % 2 else 0)
        else:
            offsets.append(round(col * DISTANCIA_MALLA / VEL_DISENO) % ciclo)
    return offsets


class Plantilla:
    """Lo que hace falta para escribir programas de un escenario con .add.xml."""

    def __init__(self, esc, cfg):
        self.esc = esc
        net, self.adicionales = leer_cfg(cfg)
        self.arbol, self.ruta = cargar_plantilla(esc, net, self.adicionales)
        self.geo = geometria(net)
        self.tls = self.arbol.getroot().findall("tlLogic")
        self.ids = [tl.get("id") for tl in self.tls]
        self.fases_av = [fase_avenida(tl, self.geo[tl.get("id")]["horizontal"]) for tl in self.tls]
        if f"{esc}.add.xml" not in self.adicionales:
            print(f"AVISO: {cfg} no carga {esc}.add.xml (el que escribe --instalar)")
        if esc == "malla3":
            xs = sorted({round(self.geo[t]["pos"][0]) for t in self.ids})
            pasos = {b - a for a, b in zip(xs, xs[1:])}
            if any(abs(p - DISTANCIA_MALLA) > 1 for p in pasos):
                print(f"AVISO: columnas de malla3 separadas {sorted(pasos)} m, no {DISTANCIA_MALLA}")

    def ciclo(self, verde_av, verde_tr):
        return ciclo_de(self.tls[0], self.fases_av[0], verde_av, verde_tr)

    def escribir(self, ruta, verde_av, verde_tr, offsets, comentario=None):
        escribir_programa(self.arbol, ruta, verde_av, verde_tr, offsets, self.fases_av, comentario)

    def extra(self, ruta):
        """Argumentos de sumo: los additional del cfg con la plantilla cambiada por ruta."""
        otros = [a for a in self.adicionales if a != self.ruta]
        return ["--additional-files", ",".join(otros + [ruta])]


def configs_plantilla(p, pares):
    """Verde de avenida x verde transversal x desfases. corredor / corredor_alta: desfase del
    segundo cruce; red / red_alta: del segundo y del tercero (0, el del segundo o el doble);
    malla3: esquema de diseno (ESQUEMAS_MALLA3)."""
    esc = p.esc
    d = DESPLEGADO.get(esc, {})
    if esc == "corredor_alta":
        offsets2 = [0, 10, 20, 25, 30]
    else:
        offsets2 = sorted(set(range(0, 45, 5)) | ({d["off2"]} if d else set()))
    for verde_av, verde_tr in pares:
        ciclo = p.ciclo(verde_av, verde_tr)
        base = {"verde": verde_av, "izquierda": "", "verde_transversal": verde_tr}
        if esc == "malla3":
            for esquema in ESQUEMAS_MALLA3:
                offsets = desfases_malla3(p.ids, p.geo, ciclo, esquema)
                nombre = f"{esc}_v{verde_av}_t{verde_tr}_{esquema}"
                params = dict(base, offsets="/".join(map(str, offsets)), esquema=esquema)
                yield nombre, params, offsets
            continue
        for off2 in offsets2:
            if off2 >= ciclo:
                continue
            terceros = [None] if len(p.ids) < 3 else sorted({0, off2, (2 * off2) % ciclo})
            for off3 in terceros:
                offsets = [0, off2] + ([off3] if off3 is not None else [])
                nombre = f"{esc}_v{verde_av}_t{verde_tr}_o{'_'.join(map(str, offsets))}"
                yield nombre, dict(base, offsets="/".join(map(str, offsets))), offsets


def en_borde(ejes, ganador):
    """Ejes en cuyo borde quedo el ganador; el piso de 10 s no cuenta como borde."""
    return [nombre for nombre, eje, valor in zip(("avenida", "transversal"), ejes, ganador)
            if valor == eje[-1] or (valor == eje[0] and valor > VERDE_MIN)]


def extender(ejes, ganador):
    """Agrega un paso a cada eje de verde en cuyo borde quedo el ganador (el paso del extremo;
    5 s si el eje tiene un solo valor). Devuelve True si agrego algo. Abajo no pasa de 10 s
    (piso valido) y arriba no pasa de 60 s (techo)."""
    cambio = False
    for nombre, eje, valor in zip(("avenida", "transversal"), ejes, ganador):
        if valor == eje[-1]:
            nuevo = valor + (eje[-1] - eje[-2] if len(eje) > 1 else 5)
            if nuevo <= VERDE_TECHO:
                eje.append(nuevo)
                cambio = True
            else:
                print(f"AVISO: {nombre} llega al techo de {VERDE_TECHO} s; no se extiende")
        if valor == eje[0] and valor > VERDE_MIN:
            eje.insert(0, max(VERDE_MIN, valor - (eje[1] - eje[0] if len(eje) > 1 else 5)))
            cambio = True
    return cambio


_DESFASES_RED = ("desfase del segundo cruce de 0 a 40 s cada 5 s y 23 s; "
                 "tercero en 0, el del segundo o el doble")
DESFASES_TEXTO = {
    "corredor": "desfase del segundo cruce de 0 a 40 s cada 5 s y el desplegado (15 s)",
    "corredor_alta": "desfase del segundo cruce en 0, 10, 20, 25 y 30 s",
    "red": _DESFASES_RED,
    "red_alta": _DESFASES_RED,
    "malla3": "esquemas de desfase " + ", ".join(ESQUEMAS_MALLA3)}


def comentario_instalado(esc, ejes, semillas, ganador, n, p):
    """Texto del comentario del .add.xml instalado: malla barrida, semillas y ganador."""
    ejes_txt = ["/".join(map(str, eje)) for eje in ejes]
    esquema = f" ({ganador['esquema']})" if esc == "malla3" else ""
    return (f"Programa fijo del plan v2 para {esc}, instalado por barrer_fijo.py. Malla barrida: "
            f"verde de avenida (E-O) {ejes_txt[0]} s x verde transversal (N-S) {ejes_txt[1]} s x "
            f"{DESFASES_TEXTO[esc]}; {n} configuraciones con las semillas {semillas}. Ganador: "
            f"avenida {ganador['verde']} s, transversal {ganador['verde_transversal']} s, ciclo "
            f"{p.ciclo(ganador['verde'], ganador['verde_transversal'])} s, desfases "
            f"{ganador['offsets']}{esquema}; retraso {ganador['timeloss_prom']} s "
            f"(sd {ganador['timeloss_sd']}) sobre esas semillas.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("escenario", choices=ESCENARIOS)
    ap.add_argument("--semillas", default="2001-2003")
    ap.add_argument("--tmp", default="tmp_barrido")
    ap.add_argument("--procesos", type=int, default=1, help="configuraciones en paralelo")
    ap.add_argument("--instalar", action="store_true",
                    help="escribe <esc>.add.xml en el cwd con el programa ganador")
    ap.add_argument("--extender", action=argparse.BooleanOptionalAction, default=True,
                    help="extiende el eje de verde en cuyo borde quedo el ganador (por defecto si)")
    ap.add_argument("--avenida", help="verdes de avenida a barrer, p. ej. 20,25 (reemplaza la malla)")
    ap.add_argument("--transversal", help="verdes transversales a barrer (reemplaza la malla)")
    ap.add_argument("--limite", type=int, help="solo las primeras N configuraciones (pruebas; no extiende)")
    ap.add_argument("--asimetrico", action="store_true",
                    help="cruce: reparto N-S x E-O por .add.xml (salida barrido_cruce_asimetrico.csv)")
    args = ap.parse_args()
    esc = args.escenario
    semillas = rango(args.semillas)
    os.makedirs(args.tmp, exist_ok=True)
    cfg = f"{esc}.sumocfg"

    def barrer(configs):
        """[(nombre, params, extra)] -> filas, en el mismo orden (el resultado no depende de N)."""
        with concurrent.futures.ThreadPoolExecutor(max(1, args.procesos)) as pool:
            futuros = [pool.submit(evaluar_config, cfg, nombre, extra, semillas, args.tmp)
                       for nombre, _, extra in configs]
            filas = []
            for (_, params, _), fut in zip(configs, futuros):
                fila = dict(params, **fut.result(), semillas=args.semillas)
                filas.append(fila)
                print(f"verde={fila['verde']:>2} tr={fila.get('verde_transversal', '')!s:>2} "
                      f"izq={fila['izquierda']!s:>2} offsets={fila['offsets']:<10} "
                      f"{fila.get('esquema', '')} timeLoss={fila['timeloss_prom']:6.2f} "
                      f"espera={fila['espera_prom']:6.2f}", flush=True)
        return filas

    if esc in ("cruce", "cruce2"):
        if args.instalar:
            ap.error("--instalar no aplica a cruce/cruce2 (el programa va en el .net.xml)")
        gen = configs_cruce_asimetrico(esc, args.tmp) if args.asimetrico else configs_cruce(esc, args.tmp)
        filas = barrer(list(gen)[:args.limite])
    else:
        p = Plantilla(esc, cfg)
        avenidas, transversales = MALLAS[esc]
        ejes = [lista_enteros(args.avenida) if args.avenida else list(avenidas),
                lista_enteros(args.transversal) if args.transversal else list(transversales)]
        d = DESPLEGADO.get(esc)
        a_mano = args.avenida or args.transversal
        extra_desplegado = {(d["verde"], d["verde_tr"])} if d and not a_mano else set()
        hechos = set()
        filas = []
        while True:
            pares = sorted({(a, t) for a in ejes[0] for t in ejes[1]} | extra_desplegado)
            pares = [par for par in pares if par not in hechos]
            configs = []
            for nombre, params, offsets in list(configs_plantilla(p, pares))[:args.limite]:
                ruta = os.path.join(args.tmp, nombre + ".add.xml")
                p.escribir(ruta, params["verde"], params["verde_transversal"], offsets)
                configs.append((nombre, params, p.extra(ruta)))
            filas += barrer(configs)
            hechos |= set(pares)
            ganador = min(filas, key=lambda f: f["timeloss_prom"])
            bordes = en_borde(ejes, (ganador["verde"], ganador["verde_transversal"]))
            if not bordes:
                break
            print(f"AVISO: el ganador (avenida {ganador['verde']}, transversal "
                  f"{ganador['verde_transversal']}) queda en el borde de: {', '.join(bordes)}", flush=True)
            if not args.extender or args.limite:
                break
            if not extender(ejes, (ganador["verde"], ganador["verde_transversal"])):
                break
            print(f"  se extiende la malla: avenida {ejes[0]} x transversal {ejes[1]}", flush=True)

    filas.sort(key=lambda f: f["timeloss_prom"])
    salida = f"barrido_{esc}{'_asimetrico' if args.asimetrico else ''}.csv"
    with open(salida, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print(f"\nMejores 5 por timeLoss ({salida}):")
    for fila in filas[:5]:
        print(f"  verde={fila['verde']} tr={fila.get('verde_transversal', '')} izq={fila['izquierda']} "
              f"offsets={fila['offsets']} {fila.get('esquema', '')} timeLoss={fila['timeloss_prom']} "
              f"(sd {fila['timeloss_sd']}) espera={fila['espera_prom']}")

    if args.instalar:
        g = filas[0]
        offsets = [int(o) for o in g["offsets"].split("/")]
        destino = f"{esc}.add.xml"
        texto = comentario_instalado(esc, ejes, args.semillas, g, len(filas), p)
        p.escribir(destino + ".nuevo", g["verde"], g["verde_transversal"], offsets, texto)
        os.replace(destino + ".nuevo", destino)
        print(f"\nInstalado en {destino}: avenida {g['verde']} s, transversal {g['verde_transversal']} s, "
              f"desfases {g['offsets']}, retraso {g['timeloss_prom']} s")


if __name__ == "__main__":
    main()
