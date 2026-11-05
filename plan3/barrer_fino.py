"""
barrer_fino.py - Barrido fino del programa fijo, con puntaje por periodo (plan3, tarea 0.7; DECISIONES A1 y B7;
prerregistro, seccion 5: "Fijo fino" y "Fijo con verdes de 5 en 5").

Uso (cwd = plan3/). Con llegadas aleatorias, perfil o P6e, a traves del lanzador, que registra el escenario:
  python barrer_fino.py <esc> --etapa gruesa|fina|desfases|desempate|fragil|mult5|fino|todo
         [--trozo k/n] [--procesos 1] [--llegadas auto|regulares|aleatorias] [--bloque 1800]
  python ../con_escenarios.py barrer_fino.py poi_corredor --etapa gruesa ...

Importa Plantilla, configs_plantilla, desfases_malla3 y evaluar_config de barrer_fijo.py sin cambiarlos y nunca
instala: escribe con nombres nuevos (barridos/<esc>/..., <esc>_r10f.add.xml, <esc>_r10g.add.xml, <esc>_m5f.add.xml).

Regla (prerregistro 5, la misma en todos los casos y niveles; "semillas del barrido" = 2001-2003 con llegadas
regulares y 2001-2010 con aleatorias, que se detectan por period="exp(...)" en las rutas):
  gruesa     la rejilla de barrer_fijo: MALLAS desde 10 s, desfases del caso (corredor y red) o los 3 esquemas
             (malla), el par desplegado y la extension si el ganador queda en el borde. Las filas son las de
             barrer_fijo (mismas columnas y numeros) mas el puntaje por periodo. Su ganador queda en
             <esc>_r10g.add.xml ("fijo desde 10 s" de los niveles).
  fina       minimos locales de la gruesa: pares de verdes cuyo mejor retraso total (sobre sus desfases o
             esquemas) no supera al de sus vecinos inmediatos en la rejilla (un paso en un eje). Pasan los que
             quedan a <= 2 % del mejor (con llegadas aleatorias: diferencia pareada con el mejor plan <= 2 errores
             estandar), tope 3. Alrededor de cada uno: avenida a-4..a+4 y transversal t-2..t+2 de 1 en 1 (10-60 s),
             con los 3 mejores patrones de desfase de la gruesa en ese par (corredor y red; los desfases se toman
             modulo el ciclo) o los 3 esquemas mas onda_oe (malla).
  desfases   corredor y red: alrededor del mejor plan de cada region de la fina, los desfases a +-4 s de 1 en 1
             (corredor 9 valores; red 9 x 9). En la malla no hay desfases libres (como en barrer_fijo).
  desempate  las 10 mejores de gruesa, fina y desfases con 2001-2010 (2001-2030 con llegadas aleatorias); gana la
             menor media. Se informan sd, mediana, peor semilla y semillas trabadas.
  fragil     si los dos primeros quedan a <= 2 % o el ganador tiene una semilla con retraso total > 1.10 veces su
             mediana, se desempata entre los 3 primeros con 2001-2030 y gana la menor media (con llegadas
             aleatorias ya tienen 2001-2030: no cambia nada). Instala <esc>_r10f.add.xml (el fijo fino).
  mult5      fijo con verdes de 5 en 5: los 3 mejores planes de la gruesa con los dos verdes multiplos de 5 s, con
             desfases finos +-4 s (malla: onda_oe para sus verdes); desempate y regla de fragiles como el fijo
             fino. Instala <esc>_m5f.add.xml. Depende solo de la gruesa.
  fino       gruesa, fina, desfases, desempate y fragil en un solo proceso; todo = fino + mult5.

Puntaje por periodo (lo usa franja.py): cada corrida se puntua tambien por periodo (--bloque s; 1800 da los dos
periodos de 30 min y 600 los seis bloques del perfil). El retraso de cada vehiculo (timeLoss + espera para entrar)
va al periodo de su salida programada: depart - departDelay; los no insertados, fin - departDelay. Para eso sumo
corre con --tripinfo-output.write-undeparted, que NUNCA se pasa a barrer_fijo.correr_sumo: su lector
(comun.leer_tripinfo) contaria dos veces a los no insertados (fila del tripinfo y espera de las estadisticas). Aqui
las metricas de la hora se leen con comun.leer_tripinfo sobre el tripinfo sin las filas con depart < 0, asi que son
las mismas de barrer_fijo; las filas con depart < 0 solo entran al puntaje por periodo.

Trozos y reanudacion: --trozo k/n corre solo los planes de indice = k (mod n) de la lista principal de la etapa
(gruesa: la rejilla inicial; fina; desfases; mult5: los desfases finos) y escribe
barridos/<esc>/trozos/<etapa>_t<k>de<n>.csv.
La etapa sin --trozo junta lo ya corrido (trozos, etapas anteriores y la cache tmp_fino/<esc>/*.jsonl, que se
escribe corrida a corrida y sirve para reanudar), corre lo que falte y escribe la salida. Los resultados se guardan
por (plan, semilla) con la huella del escenario (sha256 de cfg, red, rutas, adicionales, cortes y del codigo que corre
y lee) y el sha256 del programa con que se corrieron: un resultado solo se reutiliza si los dos coinciden, asi un
arreglo del codigo no hereda numeros viejos. El CSV no depende de --procesos ni de los trozos. Todo CSV, JSON y
.add.xml se escribe en un temporal con el pid y se reemplaza.

Salidas en barridos/<esc>/: <etapa>.csv (una fila por plan, ordenada por retraso total), <etapa>_semillas.csv (una
fila por plan y semilla), fijo_grueso10.json, fijo_fino.json y fijo_mult5.json (el ganador, la traza de la regla y
el sha256 del .add.xml). Codigo 0 solo con las salidas de la etapa completas.
"""
import os
import sys
import csv
import json
import glob
import time
import bisect
import hashlib
import argparse
import itertools
import statistics
import threading
import subprocess
import concurrent.futures
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
for _ruta in (AQUI, RAIZ):                 # plan3/ (este bloque) y la raiz (barrer_fijo, comun, escenarios)
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import comun  # noqa: E402
import barrer_fijo as bf  # noqa: E402
from barrer_fijo import Plantilla, configs_plantilla, desfases_malla3, evaluar_config  # noqa: E402

FIN_HORA = comun.FIN_HORA
# Semillas de ajuste (prerregistro 3): las del barrido, las del desempate y las de los fragiles
SEMILLAS = {"regulares": {"barrido": "2001-2003", "desempate": "2001-2010", "fragil": "2001-2030"},
            "aleatorias": {"barrido": "2001-2010", "desempate": "2001-2030", "fragil": "2001-2030"}}
FINALISTAS = 10          # desempate: las 10 mejores
TOPE_MINIMOS = 3         # regiones de la etapa fina
UMBRAL_REL = 0.02        # minimos a <= 2 % del mejor; fragil: dos primeros a <= 2 %
UMBRAL_EE = 2.0          # llegadas aleatorias: minimos a <= 2 errores estandar de la diferencia pareada
TRABADA = 1.10           # semilla trabada: retraso total > 1.10 veces la mediana del plan
TOP_FRAGIL = 3           # fragil: se desempata entre los 3 primeros
TOP_MULT5 = 3            # verdes de 5 en 5: los 3 mejores planes de la gruesa
RADIO_AV, RADIO_TR, RADIO_DESFASE = 4, 2, 4
ESQUEMAS_FINA = tuple(bf.ESQUEMAS_MALLA3) + ("onda_oe",)
# las 7 metricas de barrer_fijo.evaluar_config, en su orden
METRICAS = ("retraso_total_prom", "timeloss_prom", "retraso_insercion_prom", "espera_prom", "paradas_prom",
            "throughput", "co2_prom")
EXTRA_CORRIDA = ("vehiculos", "no_insertados", "no_terminados")
CARPETA_TMP = "tmp_fino"
ETAPAS = ("gruesa", "fina", "desfases", "desempate", "fragil", "mult5")


# ---------------------------------------------------------------- utilidades
def texto_semillas(semillas):
    """[2001, 2002, 2003] -> '2001-2003' (como --semillas de barrer_fijo); si no son contiguas, con comas."""
    s = list(semillas)
    if len(s) > 1 and s == list(range(s[0], s[-1] + 1)):
        return f"{s[0]}-{s[-1]}"
    return ",".join(map(str, s))


def leer_semillas(texto):
    """'2001-2003' o '2001,2005' -> lista."""
    salida = []
    for parte in str(texto).split(","):
        salida += bf.rango(parte.strip())
    return salida


def sha256_archivo(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def escribir_atomico(ruta, texto, modo="w", **kw):
    """Escribe en <ruta>.<pid>.tmp y reemplaza con reintentos (barrer_fijo.reemplazar): un trabajo cortado no
    deja un archivo que parezca completo y dos procesos no se pisan el temporal."""
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    tmp = f"{ruta}.{os.getpid()}.tmp"
    with open(tmp, modo, **kw) as f:
        f.write(texto)
    bf.reemplazar(tmp, ruta)


def escribir_csv(ruta, campos, filas):
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    tmp = f"{ruta}.{os.getpid()}.tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    bf.reemplazar(tmp, ruta)


def escribir_json(ruta, datos):
    escribir_atomico(ruta, json.dumps(datos, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def rutas_cfg(cfg):
    """(net, [rutas], [adicionales]) del .sumocfg, relativos a la carpeta actual."""
    raiz = ET.parse(cfg).getroot()
    net = raiz.find(".//net-file").get("value")
    nodo = raiz.find(".//route-files")
    rutas = [] if nodo is None else [r.strip() for r in nodo.get("value").split(",") if r.strip()]
    nodo = raiz.find(".//additional-files")
    adic = [] if nodo is None else [a.strip() for a in nodo.get("value").split(",") if a.strip()]
    return net, rutas, adic


def llegadas_aleatorias(cfg):
    """True si alguna ruta del escenario tiene llegadas de Poisson (period="exp(...)")."""
    _, rutas, _ = rutas_cfg(cfg)
    for r in rutas:
        with open(r, encoding="utf-8") as f:
            if 'period="exp(' in f.read():
                return True
    return False


def huella_escenario(cfg, extras=(), cortes=()):
    """sha256 (12 hex) de los archivos que definen la simulacion de un barrido, de los cortes de periodo y del codigo
    que corre y lee cada corrida (leer_periodos y correr_periodos). Una corrida guardada solo se reutiliza con la
    misma huella (y con el mismo programa: Celda.asegurar)."""
    net, rutas, adic = rutas_cfg(cfg)
    h = hashlib.sha256()
    for ruta in [cfg, net] + rutas + adic + [e for e in extras if e not in adic]:
        h.update(ruta.encode())
        with open(ruta, "rb") as f:
            h.update(f.read())
    h.update(f"fin={bf.FIN_SIM};cortes={list(cortes)}".encode())
    import inspect
    h.update((inspect.getsource(leer_periodos) + inspect.getsource(correr_periodos)).encode())
    return h.hexdigest()[:12]


# ---------------------------------------------------------------- corrida con puntaje por periodo
def leer_periodos(todo, filtrado, cortes):
    """Lee el tripinfo escrito con write-undeparted (todo) y devuelve las metricas de la hora de
    comun.leer_tripinfo sobre el mismo tripinfo SIN las filas de los no insertados (escrito en filtrado, junto a
    su archivo de estadisticas), mas el puntaje por periodo: total_p<k> (retraso total medio de los vehiculos cuya
    salida programada cae en el periodo k), n_p<k> y noins_p<k> (de ellos, cuantos no alcanzaron a entrar)."""
    arbol = ET.parse(todo)
    raiz = arbol.getroot()
    fin = float(ET.parse(comun.ruta_estadisticas(filtrado)).getroot().find("performance").get("end"))
    k_total = len(cortes) + 1
    suma, n, noins = [0.0] * k_total, [0] * k_total, [0] * k_total
    for v in list(raiz):
        if v.tag != "tripinfo":
            continue
        salida = float(v.get("depart"))
        espera = float(v.get("departDelay"))
        if salida >= 0:
            programada, retraso = salida - espera, float(v.get("timeLoss")) + espera
        else:                                  # no insertado: su espera llega hasta el cierre
            programada, retraso = fin - espera, espera
            raiz.remove(v)
        k = bisect.bisect_right(cortes, programada)
        suma[k] += retraso
        n[k] += 1
        if salida < 0:
            noins[k] += 1
    arbol.write(filtrado, encoding="utf-8")
    res = comun.leer_tripinfo(filtrado)
    salida = {m: res[m] for m in METRICAS + EXTRA_CORRIDA}
    salida["fin"] = fin
    for k in range(k_total):
        salida[f"total_p{k + 1}"] = round(suma[k] / n[k], 4) if n[k] else 0.0
        salida[f"n_p{k + 1}"] = n[k]
        salida[f"noins_p{k + 1}"] = noins[k]
    salida["total_periodos"] = round(sum(suma) / max(1, sum(n)), 4)
    return salida


def correr_periodos(cfg, extra, semilla, tripinfo, cortes, intentos=5):
    """Una corrida de sumo puro con las opciones de barrer_fijo.correr_sumo (mismo tope, mismas salidas) mas
    write-undeparted, solo para el puntaje por periodo (leer_periodos). Reintenta como correr_sumo si Windows
    tiene tomado un archivo un instante; no cambia ningun numero."""
    todo = tripinfo[:-len(".xml")] + "_todo.xml"
    cmd = ["sumo", "-c", cfg, "--seed", str(semilla), "--tripinfo-output", todo,
           "--tripinfo-output.write-unfinished", "true", "--tripinfo-output.write-undeparted", "true",
           "--device.emissions.probability", "1",
           "--no-step-log", "true", "--no-warnings", "true", "--end", str(bf.FIN_SIM)] + \
        comun.args_estadisticas(tripinfo) + extra
    for k in range(intentos):
        try:
            subprocess.run(cmd, check=True, **bf.SILENCIO)
            res = leer_periodos(todo, tripinfo, cortes)
            break
        except (subprocess.CalledProcessError, PermissionError, ET.ParseError, AttributeError):
            if k == intentos - 1:
                raise
            time.sleep(3.0)
    comun.borrar_tripinfo(tripinfo)
    comun.borrar_tripinfo(todo)
    return res


# ---------------------------------------------------------------- celda: escenario, semillas y resultados
class Celda:
    """Un escenario con su plantilla, sus semillas de ajuste y los resultados ya corridos."""

    def __init__(self, esc, llegadas="auto", bloque=1800, procesos=1, semillas=None, prefijos=ETAPAS):
        self.esc = esc
        self.cfg = f"{esc}.sumocfg"
        if not os.path.exists(self.cfg):
            raise SystemExit(f"No existe {self.cfg} en {os.getcwd()} (el escenario se corre con cwd = plan3/)")
        if bf.como(esc) not in bf.MALLAS:
            raise SystemExit(f"{esc}: no hay rejilla de barrido para '{bf.como(esc)}' (barrer_fijo.MALLAS); "
                             "registre el escenario con el caso cuya rejilla hereda")
        self.p = Plantilla(esc, self.cfg)
        self.malla = bf.es_malla(esc)
        self.aleatorias = llegadas_aleatorias(self.cfg) if llegadas == "auto" else llegadas == "aleatorias"
        self.llegadas = "aleatorias" if self.aleatorias else "regulares"
        self.cortes = list(range(bloque, FIN_HORA, bloque))
        self.k = len(self.cortes) + 1
        self.carpeta = os.path.join("barridos", esc)
        self.tmp = os.path.join(CARPETA_TMP, esc)
        self.semillas = {k: leer_semillas(v) for k, v in SEMILLAS[self.llegadas].items()}
        for k, v in (semillas or {}).items():
            if v:
                self.semillas[k] = leer_semillas(v)
        extras = [self.p.ruta] if self.p.ruta else []
        self.huella = huella_escenario(self.cfg, extras, self.cortes)
        self.procesos = max(1, procesos)
        self.prefijos = prefijos
        self.lock = threading.Lock()
        self.contador = itertools.count()
        self.conocidas = {}
        self.programa = {}          # (clave, semilla) -> sha256 (12 hex) del programa con que se corrio
        self.cargar()

    # ---------------- resultados guardados
    def campos_corrida(self):
        return (["clave", "semilla", "huella", "programa"] + list(METRICAS) + list(EXTRA_CORRIDA)
                + ["fin", "total_periodos"]
                + [f"{c}_p{k}" for k in range(1, self.k + 1) for c in ("total", "n", "noins")])

    def cargar(self):
        """Resultados ya corridos con esta huella: <prefijo>*_semillas.csv y trozos/ de barridos/<esc>/ y la
        cache tmp_fino/<esc>/<prefijo>*.jsonl (una linea por corrida; una linea cortada se ignora)."""
        enteros = set(EXTRA_CORRIDA) | {f"n_p{k}" for k in range(1, self.k + 1)} | \
            {f"noins_p{k}" for k in range(1, self.k + 1)} | {"throughput"}
        rutas = []
        for pre in self.prefijos:
            rutas += sorted(glob.glob(os.path.join(self.carpeta, f"{pre}*_semillas.csv")))
            rutas += sorted(glob.glob(os.path.join(self.carpeta, "trozos", f"{pre}_t*.csv")))
        for ruta in rutas:
            with open(ruta, newline="", encoding="utf-8") as f:
                for fila in csv.DictReader(f):
                    if fila.get("huella") != self.huella or not fila.get("programa"):
                        continue
                    r = {}
                    for c in self.campos_corrida()[4:]:
                        v = fila[c]
                        r[c] = int(v) if c in enteros else float(v)
                    self.conocidas[(fila["clave"], int(fila["semilla"]))] = r
                    self.programa[(fila["clave"], int(fila["semilla"]))] = fila["programa"]
        for pre in self.prefijos:
            for ruta in sorted(glob.glob(os.path.join(self.tmp, f"{pre}*.jsonl"))):
                with open(ruta, encoding="utf-8") as f:
                    for linea in f:
                        try:
                            d = json.loads(linea)
                        except ValueError:
                            continue
                        if d.get("h") == self.huella and "r" in d and d.get("p"):
                            self.conocidas[(d["clave"], int(d["s"]))] = d["r"]
                            self.programa[(d["clave"], int(d["s"]))] = d["p"]

    def fila_corrida(self, clave, semilla):
        return {"clave": clave, "semilla": semilla, "huella": self.huella,
                "programa": self.programa[(clave, semilla)], **self.conocidas[(clave, semilla)]}

    # ---------------- planes
    def plan(self, verde_av, verde_tr, offsets, esquema=""):
        offsets = [int(o) for o in offsets]
        return {"verde": int(verde_av), "verde_transversal": int(verde_tr), "offsets": offsets,
                "esquema": esquema, "ciclo": self.p.ciclo(verde_av, verde_tr),
                "clave": f"v{verde_av}_t{verde_tr}_o{'_'.join(map(str, offsets))}"}

    def desfases_esquema(self, ciclo, esquema):
        """Desfases de un esquema de la malla: los 3 de barrer_fijo y onda_oe (onda verde hacia el oeste: la
        columna mas al este en 0, como en el prototipo top10_p6.py)."""
        if esquema != "onda_oe":
            return desfases_malla3(self.p.ids, self.p.geo, ciclo, esquema)
        xs = sorted({round(self.p.geo[t]["pos"][0]) for t in self.p.ids})
        return [round((len(xs) - 1 - xs.index(round(self.p.geo[t]["pos"][0]))) * bf.DISTANCIA_MALLA
                      / bf.VEL_DISENO) % ciclo for t in self.p.ids]

    def escribir_plan(self, ruta, pl, comentario=None):
        self.p.escribir(ruta, pl["verde"], pl["verde_transversal"], pl["offsets"], comentario)

    def encima(self):
        """extra_de de asegurar para programas que se cargan ENCIMA de los adicionales del .sumocfg (el ultimo
        programa cargado queda activo y un WAUT activa su startProg): franja, bloques y actuado ajustado."""
        _, _, adic = rutas_cfg(self.cfg)
        return lambda pl, ruta: ["--additional-files", ",".join(adic + [ruta])]

    # ---------------- corridas
    def asegurar(self, planes, semillas, nombre_cache, extra_de=None):
        """Corre las (plan, semilla) que faltan, con --procesos hilos; cada resultado va a la cache al terminar.
        Un resultado guardado vale solo si se corrio con el mismo programa (sha256 del .add.xml del plan): un arreglo
        del codigo que cambie un programa sin cambiar su clave no reutiliza nada viejo.
        extra_de(plan, ruta) -> argumentos de sumo; por defecto el programa reemplaza a la plantilla."""
        os.makedirs(self.tmp, exist_ok=True)
        rutas, huellas = {}, {}
        for pl in planes:
            if pl["clave"] not in rutas:         # nombre corto con el pid: otro proceso puede correr el mismo plan
                ruta = os.path.join(self.tmp, f"p{os.getpid()}_{next(self.contador)}.add.xml")
                if "escribir" in pl:
                    pl["escribir"](ruta)
                else:
                    self.escribir_plan(ruta, pl)
                rutas[pl["clave"]] = ruta
                huellas[pl["clave"]] = sha256_archivo(ruta)[:12]
        faltan, vistos = [], set()
        for pl in planes:
            for s in semillas:
                clave = (pl["clave"], s)
                if self.programa.get(clave) != huellas[pl["clave"]] and clave not in vistos:
                    vistos.add(clave)
                    faltan.append((pl, s))
        if not faltan:
            self.borrar(rutas)
            return 0
        cache = os.path.join(self.tmp, f"{nombre_cache}.jsonl")
        extra_de = extra_de or (lambda pl, ruta: self.p.extra(ruta))

        def una(pl, s):
            with self.lock:
                n = next(self.contador)
            ti = os.path.join(self.tmp, f"ti_{os.getpid()}_{n}.xml")
            r = correr_periodos(self.cfg, extra_de(pl, rutas[pl["clave"]]), s, ti, self.cortes)
            p = huellas[pl["clave"]]
            with self.lock:
                self.conocidas[(pl["clave"], s)] = r
                self.programa[(pl["clave"], s)] = p
                with open(cache, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"h": self.huella, "p": p, "clave": pl["clave"], "s": s, "r": r}) + "\n")
            return r

        t0 = time.time()
        with concurrent.futures.ThreadPoolExecutor(self.procesos) as pool:
            futuros = [(pl, s, pool.submit(una, pl, s)) for pl, s in faltan]
            for pl, s, fut in futuros:
                r = fut.result()
                print(f"  {pl.get('nombre', pl['clave']):40s} s{s}: total={r['retraso_total_prom']:7.2f} "
                      f"timeLoss={r['timeloss_prom']:7.2f} no_insertados={r['no_insertados']}", flush=True)
        self.borrar(rutas)
        print(f"  {len(faltan)} corridas en {time.time() - t0:.0f} s", flush=True)
        return len(faltan)

    @staticmethod
    def borrar(rutas):
        for ruta in rutas.values():
            try:
                os.remove(ruta)
            except OSError:
                pass

    # ---------------- filas
    def metricas(self, clave, semillas):
        """Medias de un programa sobre unas semillas con los redondeos de barrer_fijo.evaluar_config (las 7
        metricas y las sd), mas mediana, peor semilla, semillas trabadas y el puntaje por periodo."""
        res = [self.conocidas[(clave, s)] for s in semillas]
        fila = {}
        for m in METRICAS:
            fila[m] = round(statistics.mean(float(r[m]) for r in res), 2)
        for m, nombre in (("retraso_total_prom", "retraso_total_sd"), ("timeloss_prom", "timeloss_sd")):
            valores = [float(r[m]) for r in res]
            fila[nombre] = round(statistics.stdev(valores), 2) if len(res) > 1 else 0
        fila["semillas"] = texto_semillas(semillas)
        totales = [float(r["retraso_total_prom"]) for r in res]
        mediana = statistics.median(totales)
        fila.update({"mediana": round(mediana, 2), "peor": max(totales),
                     "trabadas": sum(1 for x in totales if x > TRABADA * mediana)})
        for k in range(1, self.k + 1):
            fila[f"total_p{k}"] = round(statistics.mean(float(r[f"total_p{k}"]) for r in res), 2)
            fila[f"noins_p{k}"] = round(statistics.mean(float(r[f"noins_p{k}"]) for r in res), 2)
        return fila

    def campos_metricas(self):
        return (list(METRICAS) + ["retraso_total_sd", "timeloss_sd", "semillas", "mediana", "peor", "trabadas"]
                + [f"{c}_p{k}" for k in range(1, self.k + 1) for c in ("total", "noins")])

    def fila(self, pl, semillas, etapa, region=""):
        """Fila de un plan: las columnas de barrer_fijo (verde, izquierda, verde_transversal, offsets, esquema en
        la malla, 7 metricas, 2 sd, semillas) y despues ciclo, etapa, region, clave y lo de metricas()."""
        fila = {"verde": pl["verde"], "izquierda": "", "verde_transversal": pl["verde_transversal"],
                "offsets": "/".join(map(str, pl["offsets"]))}
        if self.malla:
            fila["esquema"] = pl["esquema"]
        fila.update(self.metricas(pl["clave"], semillas))
        fila.update({"ciclo": pl["ciclo"], "etapa": etapa, "region": region, "clave": pl["clave"]})
        return fila

    def campos_fila(self):
        campos = self.campos_metricas()
        return (["verde", "izquierda", "verde_transversal", "offsets"] + (["esquema"] if self.malla else [])
                + campos[:campos.index("semillas") + 1] + ["ciclo", "etapa", "region", "clave"]
                + campos[campos.index("semillas") + 1:])

    def escribir_etapa(self, nombre, planes, semillas, etapa, regiones=None):
        """<nombre>.csv (ordenado por retraso total, estable) y <nombre>_semillas.csv (orden de los planes)."""
        regiones = regiones or {}
        filas = [self.fila(pl, semillas, etapa, regiones.get(pl["clave"], "")) for pl in planes]
        orden = sorted(range(len(filas)), key=lambda i: filas[i]["retraso_total_prom"])
        escribir_csv(os.path.join(self.carpeta, f"{nombre}_semillas.csv"), self.campos_corrida(),
                     [self.fila_corrida(pl["clave"], s) for pl in planes for s in semillas])
        escribir_csv(os.path.join(self.carpeta, f"{nombre}.csv"), self.campos_fila(), [filas[i] for i in orden])
        return [filas[i] for i in orden], [planes[i] for i in orden]

    def escribir_trozo(self, etapa, trozo, planes, semillas):
        k, n = trozo
        mios = [pl for i, pl in enumerate(planes) if i % n == k]
        self.asegurar(mios, semillas, f"{etapa}_t{k}de{n}")
        escribir_csv(os.path.join(self.carpeta, "trozos", f"{etapa}_t{k}de{n}.csv"), self.campos_corrida(),
                     [self.fila_corrida(pl["clave"], s) for pl in mios for s in semillas])
        print(f"{self.esc} {etapa}: trozo {k}/{n} con {len(mios)} de {len(planes)} planes", flush=True)


def unicos(planes):
    """Planes sin repetir programa (el primero manda)."""
    vistos, salida = set(), []
    for pl in planes:
        if pl["clave"] not in vistos:
            vistos.add(pl["clave"])
            salida.append(pl)
    return salida


# ---------------------------------------------------------------- etapa gruesa
def pares_gruesa(c, avenida=None, transversal=None):
    """Ejes y par desplegado de la rejilla de barrer_fijo (main, l. 483-492)."""
    avenidas, transversales = bf.MALLAS[bf.como(c.esc)]
    ejes = [list(avenida or avenidas), list(transversal or transversales)]
    d = bf.DESPLEGADO.get(bf.como(c.esc))
    extra = {(d["verde"], d["verde_tr"])} if d and not (avenida or transversal) else set()
    return ejes, extra


def planes_de_pares(c, pares, limite=None):
    salida = []
    for nombre, params, offsets in list(configs_plantilla(c.p, pares))[:limite]:
        pl = c.plan(params["verde"], params["verde_transversal"], offsets, params.get("esquema", ""))
        pl["nombre"] = nombre
        salida.append(pl)
    return salida


def etapa_gruesa(c, trozo=None, avenida=None, transversal=None, limite=None):
    """La rejilla de barrer_fijo con su extension. Devuelve (filas ordenadas, planes en el orden de barrer_fijo)."""
    ejes, extra = pares_gruesa(c, avenida, transversal)
    semillas = c.semillas["barrido"]
    pares = sorted({(a, t) for a in ejes[0] for t in ejes[1]} | extra)
    if trozo:
        c.escribir_trozo("gruesa", trozo, planes_de_pares(c, pares, limite), semillas)
        return None, None
    hechos, planes = set(), []
    while True:
        pares = [par for par in sorted({(a, t) for a in ejes[0] for t in ejes[1]} | extra) if par not in hechos]
        nuevos = planes_de_pares(c, pares, limite)
        c.asegurar(nuevos, semillas, "gruesa")
        planes += nuevos
        hechos |= set(pares)
        filas = [c.fila(pl, semillas, "gruesa") for pl in planes]
        ganador = min(filas, key=lambda f: f["retraso_total_prom"])
        bordes = bf.en_borde(ejes, (ganador["verde"], ganador["verde_transversal"]))
        if not bordes:
            break
        print(f"AVISO: el ganador (avenida {ganador['verde']}, transversal {ganador['verde_transversal']}) "
              f"queda en el borde de: {', '.join(bordes)}", flush=True)
        if limite or not bf.extender(ejes, (ganador["verde"], ganador["verde_transversal"])):
            break
        print(f"  se extiende la malla: avenida {ejes[0]} x transversal {ejes[1]}", flush=True)
    filas, ordenados = c.escribir_etapa("gruesa", planes, semillas, "gruesa")
    g, pl = filas[0], ordenados[0]
    texto = (f"Fijo desde 10 s (ganador de la etapa gruesa de barrer_fino.py, plan3) para {c.esc}: rejilla de "
             f"barrer_fijo (avenida {'/'.join(map(str, ejes[0]))} s x transversal {'/'.join(map(str, ejes[1]))} s"
             f" x {bf.DESFASES_TEXTO[bf.como(c.esc)]}); {len(planes)} planes con las semillas {g['semillas']} "
             f"({c.llegadas}). Ganador: avenida {g['verde']} s, transversal {g['verde_transversal']} s, ciclo "
             f"{g['ciclo']} s, desfases {g['offsets']}{' (' + g['esquema'] + ')' if c.malla else ''}; retraso "
             f"total {g['retraso_total_prom']} s (sd {g['retraso_total_sd']}), timeLoss {g['timeloss_prom']} s.")
    instalar(c, pl, g, "r10g", "fijo_grueso10", texto, {"ejes": ejes, "planes": len(planes)})
    return filas, planes


def planes_gruesa(c):
    """Planes de la gruesa ya escrita (en su orden de barrer_fijo), para las etapas siguientes."""
    ruta = os.path.join(c.carpeta, "gruesa_semillas.csv")
    if not os.path.exists(ruta):
        raise SystemExit(f"Falta {ruta}: corra antes la etapa gruesa")
    return planes_desde_semillas(c, ruta)


def planes_desde_semillas(c, ruta):
    """Planes en el orden de un <etapa>_semillas.csv (la clave dice verdes y desfases); el esquema sale del CSV
    de la etapa."""
    claves = []
    with open(ruta, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            if fila["huella"] != c.huella:
                raise SystemExit(f"{ruta} se corrio con otra huella del escenario ({fila['huella']}, hoy "
                                 f"{c.huella}): cambiaron los archivos del escenario o --bloque; repita la etapa")
            if fila["clave"] not in claves:
                claves.append(fila["clave"])
    esquemas = {}
    ruta_etapa = ruta.replace("_semillas.csv", ".csv")
    if os.path.exists(ruta_etapa):
        with open(ruta_etapa, newline="", encoding="utf-8") as f:
            esquemas = {fila["clave"]: fila.get("esquema", "") for fila in csv.DictReader(f)}
    planes = []
    for clave in claves:
        v, t, o = clave.split("_", 2)
        pl = c.plan(int(v[1:]), int(t[1:]), [int(x) for x in o[1:].split("_")], esquemas.get(clave, ""))
        planes.append(pl)
    return planes


# ---------------------------------------------------------------- etapa fina
def minimos_locales(filas):
    """[(valor, verde, transversal, indice de la mejor fila)] de los pares de verdes que son minimo local: su
    mejor retraso total no supera al de sus vecinos inmediatos (un paso en un eje), ordenados de mejor a peor."""
    mejor = {}
    for i, f in enumerate(filas):
        par = (f["verde"], f["verde_transversal"])
        if par not in mejor or f["retraso_total_prom"] < filas[mejor[par]]["retraso_total_prom"]:
            mejor[par] = i
    av = sorted({a for a, _ in mejor})
    tr = sorted({t for _, t in mejor})
    salida = []
    for (a, t), i in mejor.items():
        valor = filas[i]["retraso_total_prom"]
        ia, it = av.index(a), tr.index(t)
        vecinos = [(av[x], tr[y]) for x, y in ((ia - 1, it), (ia + 1, it), (ia, it - 1), (ia, it + 1))
                   if 0 <= x < len(av) and 0 <= y < len(tr)]
        if all(valor <= filas[mejor[v]]["retraso_total_prom"] for v in vecinos if v in mejor):
            salida.append((valor, a, t, i))
    salida.sort(key=lambda m: (m[0], m[3]))
    return salida


def dentro_del_umbral(c, pl, pl_mejor, valor, valor_mejor):
    """Llegadas regulares: a <= 2 % del mejor. Aleatorias: la media de la diferencia pareada por semilla con el
    mejor plan no supera 2 errores estandar."""
    if not c.aleatorias:
        return valor <= (1 + UMBRAL_REL) * valor_mejor
    d = [float(c.conocidas[(pl["clave"], s)]["retraso_total_prom"]) -
         float(c.conocidas[(pl_mejor["clave"], s)]["retraso_total_prom"]) for s in c.semillas["barrido"]]
    if len(d) < 2:
        return valor <= valor_mejor
    ee = statistics.stdev(d) / len(d) ** 0.5
    return statistics.mean(d) <= UMBRAL_EE * ee


def regiones_fina(c, planes_g, filas_g):
    """Regiones de la etapa fina: [(etiqueta, plan del minimo, planes de la region)], tope 3."""
    minimos = minimos_locales(filas_g)
    valor_mejor, _, _, i_mejor = minimos[0]
    elegidos = [m for m in minimos if dentro_del_umbral(c, planes_g[m[3]], planes_g[i_mejor], m[0], valor_mejor)]
    regiones = []
    for valor, a0, t0, i in elegidos[:TOPE_MINIMOS]:
        etiqueta = f"min{len(regiones) + 1}_v{a0}_t{t0}"
        patrones = []
        for j in sorted(range(len(planes_g)), key=lambda j: filas_g[j]["retraso_total_prom"]):
            pl = planes_g[j]
            if (pl["verde"], pl["verde_transversal"]) == (a0, t0) and pl["offsets"] not in patrones:
                patrones.append(pl["offsets"])
        patrones = patrones[:3]
        planes = []
        for a in range(max(bf.VERDE_MIN, a0 - RADIO_AV), min(bf.VERDE_TECHO, a0 + RADIO_AV) + 1):
            for t in range(max(bf.VERDE_MIN, t0 - RADIO_TR), min(bf.VERDE_TECHO, t0 + RADIO_TR) + 1):
                ciclo = c.p.ciclo(a, t)
                if c.malla:
                    for esquema in ESQUEMAS_FINA:
                        planes.append(c.plan(a, t, c.desfases_esquema(ciclo, esquema), esquema))
                else:
                    for patron in patrones:
                        planes.append(c.plan(a, t, [o % ciclo for o in patron]))
        regiones.append((etiqueta, planes_g[i], unicos(planes)))
        print(f"{c.esc} fina: region {etiqueta} (retraso total {valor}), {len(unicos(planes))} planes"
              + ("" if c.malla else f", patrones de desfase {patrones}"), flush=True)
    return regiones


def contexto_fina(c):
    """Planes y filas de la gruesa (semillas del barrido) y las regiones de la fina."""
    planes_g = planes_gruesa(c)
    c.asegurar(planes_g, c.semillas["barrido"], "gruesa")      # normalmente ya estan todos
    filas_g = [c.fila(pl, c.semillas["barrido"], "gruesa") for pl in planes_g]
    return planes_g, filas_g, regiones_fina(c, planes_g, filas_g)


def planes_fina(regiones):
    """Planes de la fina en orden (sin repetir) y su region (la primera en que aparece)."""
    planes, region = [], {}
    for etiqueta, _, lista in regiones:
        for pl in lista:
            if pl["clave"] not in region:
                region[pl["clave"]] = etiqueta
                planes.append(pl)
    return planes, region


def etapa_fina(c, trozo=None):
    _, _, regiones = contexto_fina(c)
    planes, region = planes_fina(regiones)
    if trozo:
        c.escribir_trozo("fina", trozo, planes, c.semillas["barrido"])
        return
    c.asegurar(planes, c.semillas["barrido"], "fina")
    c.escribir_etapa("fina", planes, c.semillas["barrido"], "fina", region)
    print(f"{c.esc} fina: {len(planes)} planes en {len(regiones)} regiones", flush=True)


# ---------------------------------------------------------------- etapa desfases
def planes_desfases_de(c, pl):
    """Desfases finos +-4 s de 1 en 1 alrededor de un plan (corredor: el segundo cruce; red: el segundo y el
    tercero), modulo el ciclo; en la malla no hay desfases libres."""
    if c.malla or len(pl["offsets"]) not in (2, 3):
        return []
    ciclo, o = pl["ciclo"], pl["offsets"]
    rango_d = range(-RADIO_DESFASE, RADIO_DESFASE + 1)
    if len(o) == 2:
        combos = [[o[0], (o[1] + d) % ciclo] for d in rango_d]
    else:
        combos = [[o[0], (o[1] + d2) % ciclo, (o[2] + d3) % ciclo] for d2 in rango_d for d3 in rango_d]
    return unicos([c.plan(pl["verde"], pl["verde_transversal"], combo) for combo in combos])


def contexto_desfases(c):
    """Regiones de la fina con su mejor plan (semillas del barrido) y los planes de desfases finos."""
    _, _, regiones = contexto_fina(c)
    planes_f, _ = planes_fina(regiones)
    ruta = os.path.join(c.carpeta, "fina_semillas.csv")
    if not os.path.exists(ruta):
        raise SystemExit(f"Falta {ruta}: corra antes la etapa fina")
    c.asegurar(planes_f, c.semillas["barrido"], "fina")
    planes, region = [], {}
    for etiqueta, _, lista in regiones:
        filas = [c.fila(pl, c.semillas["barrido"], "fina") for pl in lista]
        mejor = lista[min(range(len(lista)), key=lambda i: filas[i]["retraso_total_prom"])]
        for pl in planes_desfases_de(c, mejor):
            if pl["clave"] not in region:
                region[pl["clave"]] = etiqueta
                planes.append(pl)
    return planes, region


def etapa_desfases(c, trozo=None):
    planes, region = contexto_desfases(c)
    if trozo:
        c.escribir_trozo("desfases", trozo, planes, c.semillas["barrido"])
        return
    c.asegurar(planes, c.semillas["barrido"], "desfases")
    c.escribir_etapa("desfases", planes, c.semillas["barrido"], "desfases", region)
    print(f"{c.esc} desfases: {len(planes)} planes" + (" (malla: sin desfases libres)" if c.malla else ""),
          flush=True)


# ---------------------------------------------------------------- desempate, fragiles e instalacion
def planes_barrido(c):
    """Planes de gruesa, fina y desfases (sin repetir, en ese orden) con las semillas del barrido."""
    planes = planes_gruesa(c)
    for etapa in ("fina", "desfases"):
        ruta = os.path.join(c.carpeta, f"{etapa}_semillas.csv")
        if not os.path.exists(ruta):
            raise SystemExit(f"Falta {ruta}: corra antes la etapa {etapa}")
        planes += planes_desde_semillas(c, ruta)
    return unicos(planes)


def desempatar(c, candidatos, nombre, etapa):
    """Las 10 mejores por la media en las semillas del barrido, con las del desempate: (filas, planes)
    ordenados por la media del desempate."""
    c.asegurar(candidatos, c.semillas["barrido"], nombre)
    filas = [c.fila(pl, c.semillas["barrido"], etapa) for pl in candidatos]
    orden = sorted(range(len(filas)), key=lambda i: filas[i]["retraso_total_prom"])
    finalistas = [candidatos[i] for i in orden[:FINALISTAS]]
    c.asegurar(finalistas, c.semillas["desempate"], nombre)
    return c.escribir_etapa(nombre, finalistas, c.semillas["desempate"], "desempate")


def regla_fragil(c, filas_d, planes_d, nombre):
    """Regla de ganadores fragiles sobre el desempate. Devuelve (fila ganadora, plan, traza)."""
    g = filas_d[0]
    segundo = filas_d[1] if len(filas_d) > 1 else None
    cerca = segundo is not None and \
        segundo["retraso_total_prom"] - g["retraso_total_prom"] <= UMBRAL_REL * g["retraso_total_prom"]
    traza = {"dos_primeros_a_2pct": bool(cerca), "semillas_trabadas_ganador": g["trabadas"],
             "fragil": bool(cerca or g["trabadas"] > 0), "semillas_desempate": g["semillas"]}
    if not traza["fragil"]:
        return g, planes_d[0], traza
    top = planes_d[:TOP_FRAGIL]
    c.asegurar(top, c.semillas["fragil"], nombre)
    filas_f, planes_f = c.escribir_etapa(nombre, top, c.semillas["fragil"], "fragil")
    traza.update({"desempate_fragil": [f["clave"] for f in filas_f], "semillas_fragil": filas_f[0]["semillas"]})
    return filas_f[0], planes_f[0], traza


def instalar(c, pl, fila, sufijo, nombre_json, comentario, traza):
    """Escribe <esc>_<sufijo>.add.xml (programa "fijo", reemplaza a la plantilla <esc>.add.xml en
    --additional-files, como lo haria barrer_fijo --instalar) y barridos/<esc>/<nombre_json>.json."""
    destino = f"{c.esc}_{sufijo}.add.xml"
    tmp = f"{destino}.{os.getpid()}.tmp"
    c.escribir_plan(tmp, pl, comentario.replace("--", "- -"))     # un comentario XML no puede llevar "--"
    bf.reemplazar(tmp, destino)
    datos = {"escenario": c.esc, "llegadas": c.llegadas, "archivo": destino, "sha256": sha256_archivo(destino),
             "huella": c.huella, "verde": pl["verde"], "verde_transversal": pl["verde_transversal"],
             "offsets": pl["offsets"], "esquema": pl["esquema"], "ciclo": pl["ciclo"], "clave": pl["clave"],
             "ids": c.p.ids, "fases_avenida": c.p.fases_av,
             **{k: fila[k] for k in ("retraso_total_prom", "retraso_total_sd", "timeloss_prom", "mediana", "peor",
                                      "trabadas", "semillas")},
             "semillas_regla": {k: texto_semillas(v) for k, v in c.semillas.items()}, "traza": traza}
    escribir_json(os.path.join(c.carpeta, f"{nombre_json}.json"), datos)
    print(f"Instalado {destino}: avenida {pl['verde']} s, transversal {pl['verde_transversal']} s, desfases "
          f"{'/'.join(map(str, pl['offsets']))} {pl['esquema']}, retraso total {fila['retraso_total_prom']} "
          f"({fila['semillas']})", flush=True)
    return datos


def comentario_ganador(c, que, fila, traza, n):
    return (f"{que} (barrer_fino.py, plan3; regla del prerregistro, seccion 5) para {c.esc}, llegadas {c.llegadas}: "
            f"{n} planes con las semillas {texto_semillas(c.semillas['barrido'])}; las 10 mejores con "
            f"{texto_semillas(c.semillas['desempate'])}"
            + (f"; ganador fragil, desempate de los 3 primeros con {traza.get('semillas_fragil')}"
               if traza.get("fragil") else "")
            + f". Ganador: avenida {fila['verde']} s, transversal {fila['verde_transversal']} s, ciclo "
            f"{fila['ciclo']} s, desfases {fila['offsets']}{' (' + fila['esquema'] + ')' if c.malla else ''}; "
            f"retraso total {fila['retraso_total_prom']} s (sd {fila['retraso_total_sd']}, peor "
            f"{fila['peor']}), timeLoss {fila['timeloss_prom']} s sobre {fila['semillas']}.")


def etapa_desempate(c):
    candidatos = planes_barrido(c)
    filas, _ = desempatar(c, candidatos, "desempate", "desempate")
    print(f"{c.esc} desempate: {len(filas)} finalistas de {len(candidatos)} planes; mejor "
          f"{filas[0]['clave']} {filas[0]['retraso_total_prom']} ({filas[0]['semillas']})", flush=True)


def etapa_fragil(c):
    candidatos = planes_barrido(c)
    ruta = os.path.join(c.carpeta, "desempate_semillas.csv")
    if not os.path.exists(ruta):
        raise SystemExit(f"Falta {ruta}: corra antes la etapa desempate")
    filas_d, planes_d = desempatar(c, candidatos, "desempate", "desempate")
    fila, pl, traza = regla_fragil(c, filas_d, planes_d, "fragil")
    if not traza["fragil"]:          # sin fragil: fragil.csv igual queda escrito (el ganador del desempate)
        c.escribir_etapa("fragil", planes_d[:1], c.semillas["desempate"], "fragil")
    texto = comentario_ganador(c, "Fijo fino", fila, traza, len(candidatos))
    instalar(c, pl, fila, "r10f", "fijo_fino", texto, traza)


# ---------------------------------------------------------------- fijo con verdes de 5 en 5
def contexto_mult5(c):
    planes_g = planes_gruesa(c)
    c.asegurar(planes_g, c.semillas["barrido"], "gruesa")
    filas_g = [c.fila(pl, c.semillas["barrido"], "gruesa") for pl in planes_g]
    orden = sorted(range(len(planes_g)), key=lambda i: filas_g[i]["retraso_total_prom"])
    m5 = [planes_g[i] for i in orden
          if planes_g[i]["verde"] % 5 == 0 and planes_g[i]["verde_transversal"] % 5 == 0]
    nuevos = []
    for pl in m5[:TOP_MULT5]:
        if c.malla:
            nuevos.append(c.plan(pl["verde"], pl["verde_transversal"],
                                 c.desfases_esquema(pl["ciclo"], "onda_oe"), "onda_oe"))
        else:
            nuevos += planes_desfases_de(c, pl)
    return m5, unicos(nuevos)


def etapa_mult5(c, trozo=None):
    m5, nuevos = contexto_mult5(c)
    if trozo:
        c.escribir_trozo("mult5", trozo, nuevos, c.semillas["barrido"])
        return
    c.asegurar(nuevos, c.semillas["barrido"], "mult5")
    candidatos = unicos(m5 + nuevos)
    c.escribir_etapa("mult5", candidatos, c.semillas["barrido"], "mult5")
    filas_d, planes_d = desempatar(c, candidatos, "mult5_desempate", "mult5")
    fila, pl, traza = regla_fragil(c, filas_d, planes_d, "mult5_fragil")
    texto = comentario_ganador(c, "Fijo con verdes de 5 en 5 y desfases finos", fila, traza, len(candidatos))
    instalar(c, pl, fila, "m5f", "fijo_mult5", texto, traza)


# ---------------------------------------------------------------- comprobacion del lector
def comprobar_lector(c, pl, semillas, tmp=None):
    """Hora de leer_periodos frente a barrer_fijo.evaluar_config (sin write-undeparted) en un plan: devuelve
    (fila de evaluar_config, fila de este lector) con las mismas claves."""
    tmp = tmp or c.tmp
    os.makedirs(tmp, exist_ok=True)
    ruta = os.path.join(tmp, f"comprobar_{pl['clave']}_{os.getpid()}.add.xml")
    c.escribir_plan(ruta, pl)
    ref = evaluar_config(c.cfg, f"comprobar_{os.getpid()}", c.p.extra(ruta), semillas, tmp)
    c.asegurar([pl], semillas, "comprobar")
    propia = c.fila(pl, semillas, "comprobar")
    os.remove(ruta)
    return ref, {k: propia[k] for k in ref}


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Barrido fino del fijo con puntaje por periodo (plan3, 0.7)")
    ap.add_argument("escenario")
    ap.add_argument("--etapa", choices=list(ETAPAS) + ["fino", "todo"], default="fino")
    ap.add_argument("--trozo", help="k/n: solo los planes de indice k (mod n) de la lista principal de la etapa")
    ap.add_argument("--procesos", type=int, default=1, help="sumo en paralelo (hilos); la cola usa 1")
    ap.add_argument("--llegadas", choices=["auto", "regulares", "aleatorias"], default="auto",
                    help="auto: aleatorias si las rutas tienen period=\"exp(...)\"")
    ap.add_argument("--bloque", type=int, default=1800,
                    help="largo de cada periodo del puntaje (1800: dos medias horas; 600: bloques del perfil)")
    ap.add_argument("--semillas", help="(pruebas) semillas del barrido en vez de las de la regla")
    ap.add_argument("--semillas-desempate", help="(pruebas) en vez de 2001-2010 / 2001-2030")
    ap.add_argument("--semillas-fragil", help="(pruebas) en vez de 2001-2030")
    ap.add_argument("--avenida", help="(pruebas) verdes de avenida de la gruesa, p. ej. 15,20")
    ap.add_argument("--transversal", help="(pruebas) verdes transversales de la gruesa")
    ap.add_argument("--limite", type=int, help="(pruebas) solo los primeros N planes de la gruesa, sin extension")
    args = ap.parse_args()
    if args.etapa in ("desempate", "fragil", "fino", "todo") and args.trozo:
        ap.error("--trozo solo en gruesa, fina, desfases y mult5")
    trozo = None
    if args.trozo:
        k, n = (int(x) for x in args.trozo.split("/"))
        if not 0 <= k < n:
            ap.error("--trozo k/n con 0 <= k < n")
        trozo = (k, n)
    c = Celda(args.escenario, args.llegadas, args.bloque, args.procesos,
              {"barrido": args.semillas, "desempate": args.semillas_desempate, "fragil": args.semillas_fragil})
    print(f"barrer_fino {c.esc}: etapa {args.etapa}, llegadas {c.llegadas}, semillas "
          f"{ {k: texto_semillas(v) for k, v in c.semillas.items()} }, periodos de {args.bloque} s, huella "
          f"{c.huella}, {len(c.conocidas)} corridas ya guardadas", flush=True)
    t0 = time.time()
    av = bf.lista_enteros(args.avenida) if args.avenida else None
    tr = bf.lista_enteros(args.transversal) if args.transversal else None
    etapas = {"fino": ETAPAS[:5], "todo": ETAPAS}.get(args.etapa, (args.etapa,))
    for etapa in etapas:
        print(f"== {c.esc}: etapa {etapa}", flush=True)
        if etapa == "gruesa":
            etapa_gruesa(c, trozo, av, tr, args.limite)
        elif etapa == "fina":
            etapa_fina(c, trozo)
        elif etapa == "desfases":
            etapa_desfases(c, trozo)
        elif etapa == "desempate":
            etapa_desempate(c)
        elif etapa == "fragil":
            etapa_fragil(c)
        elif etapa == "mult5":
            etapa_mult5(c, trozo)
    print(f"barrer_fino {c.esc} {args.etapa}: listo en {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
