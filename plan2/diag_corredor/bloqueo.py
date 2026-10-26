"""
bloqueo.py - Verde bloqueado por los giros a la izquierda en el corredor con 2715 veh/h, medido segundo a
segundo con TraCI (diagnostico del corredor, 25.10.2026).

Analisis posterior al veredicto (PRERREGISTRO.md, Enmienda 3): no cambia ningun veredicto ni ningun archivo
del plan. Mide el mecanismo de H6 en dos escenarios con la misma red (corredor.net.xml):
  O  dem_corredor_t2715      giros del periodo 2 a la izquierda (el escenario del plan)
  D  dem_corredor_t2715_der  giros del periodo 2 a la derecha (el contrafactual de la Enmienda 3)
con cuatro controles:
  fijo     25/10 s, ambar 3 s, ciclo 41 s, desfases 0/0 (copia de dem_corredor_t2715.add.xml, la misma en
           O y en D; el .add.xml de D se reescribe con el barrido de la cola, por eso no se usa)
  actuado  el actuado de SUMO de evaluar.py (comun.archivo_actuado)
  actual   IPPO con mensajes, version evaluada en 2715 (politica_dem_corredor_t2715_vecinos_s2042.pt)
  v2       la correccion V2 en 2715 (politica_dem_corredor_t2715_vecinos_v2_s42.pt)

Como se mide. Cada corrida usa las funciones de evaluar.py (brazo_referencia y brazo_profundo), sin
cambiarlas. Este script reemplaza traci.simulationStep por una envoltura que llama al original y despues
lee, con getters y suscripciones de vehiculos (no toca las suscripciones de aristas, carriles ni semaforos
del control), el estado de cada segundo:
  - el estado de los dos semaforos (getRedYellowGreenState; los links se mapean con getControlledLinks);
  - por cada una de las 8 aristas de acceso: vehiculos y detenidos (< 0.1 m/s) en el carril, vehiculos que
    cruzan la linea de detencion (estaban en el carril en t-1 y ya no), y el vehiculo de cabeza: el mas
    avanzado entre los del carril y los del primer tramo interno de sus tres movimientos (el que gira a la
    izquierda espera el hueco DENTRO del cruce, al final de ese tramo de 4.07 m, con 0.93 m de su cola
    todavia sobre el carril), con su movimiento (siguiente arista de su ruta: derecha, recta o
    izquierda), su velocidad y su distancia a la linea (negativa si ya esta dentro del cruce);
  - por cada enlace entre los cruces (C1_C2, C2_C1): vehiculos, detenidos, espacio libre al inicio (posicion
    de la cola del ultimo vehiculo) y velocidad del ultimo;
  - vehiculos que esperan para entrar por cada arista de entrada (getPendingVehicles).
Las metricas de cada corrida (comun.leer_tripinfo) se comparan con las de la evaluacion del plan con la misma
semilla (determinismo): si la envoltura cambiara algo de la simulacion, no coincidirian.

Definiciones (las de bloqueo.md):
  verde de un acceso   su movimiento recto en G (los tres links de un acceso cambian juntos; la izquierda es g)
  cabeza izq. detenida la cabeza va a girar a la izquierda y esta detenida, en un segundo de verde del acceso
  descarga             vehiculos que cruzan la linea por segundo de verde; "con cola": solo los segundos de
                       verde que empiezan con al menos un detenido en el carril
  derrame              cabeza detenida en verde que no va a la izquierda y cuya salida es un enlace con menos
                       de una plaza (7.5 m) libre al inicio
  cola hasta el cruce  el enlace tiene menos de una plaza libre al inicio y su ultimo vehiculo va a menos de
                       2 m/s (version estricta: detenido)
  periodos             P1 = segundos 1-1800, P2 = 1801-3600 en las metricas por segundo; en el retraso por
                       periodo, el del flujo de cada vehiculo (p1_ o p2_), como comportamiento.py

Uso (desde plan2/; las corridas pesadas van a una carpeta fuera del repositorio):
  python diag_corredor/bloqueo.py correr   --datos <carpeta> [--semillas 1001-1005] [--procesos 4]
  python diag_corredor/bloqueo.py analizar --datos <carpeta> [--salida diag_corredor]
  python diag_corredor/bloqueo.py tablas   [--salida diag_corredor]
correr deja en <carpeta>: seg_<esc>_<control>_s<semilla>.csv.gz (una fila por segundo), met_*.json
(metricas de la corrida y mapa de links), el tripinfo y su _stats.xml (40 corridas, unos 4 min con 4
procesos). analizar escribe en --salida: bloqueo.csv (por escenario, control, periodo y acceso: verde y su
clasificacion, cruces y descarga), bloqueo_verdes.csv (duracion de los verdes con y sin cabeza bloqueada),
bloqueo_decisiones.csv (instantes de decision de IPPO en los verdes transversales), bloqueo_derrame.csv
(enlaces llenos, acceso bloqueado por derrame, espera para entrar), bloqueo_periodos.csv (retraso por periodo y
movimiento, del tripinfo) y bloqueo_control.csv (determinismo). Cada tabla trae una fila por semilla y una fila
"media". tablas imprime las tablas de bloqueo.md desde esos CSV.
"""
import os
import sys
import csv
import gzip
import json
import time
import shutil
import random
import argparse
import statistics
import subprocess
import xml.etree.ElementTree as ET

os.environ.setdefault("OMP_NUM_THREADS", "1")       # como plan2/cola.py: un hilo de torch por proceso
os.environ.setdefault("MKL_NUM_THREADS", "1")

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN2 = os.path.dirname(AQUI)
RAIZ = os.path.dirname(PLAN2)

RED = os.path.join(PLAN2, "corredor.net.xml")
FIJO_ORIGEN = os.path.join(PLAN2, "dem_corredor_t2715.add.xml")
FIJO_COPIA = "fijo_25_10_d00.add.xml"            # en --datos
ESCENARIOS = {          # nombre -> (rutas en plan2, nombre del escenario registrado en este proceso)
    "O": ("dem_corredor_t2715.rou.xml", "bloqueo_o"),
    "D": ("dem_corredor_t2715_der.rou.xml", "bloqueo_d"),
}
CONTROLES = {
    "fijo": ("ref", "fijo"),
    "actuado": ("ref", "actuado"),
    "actual": ("pt", "politica_dem_corredor_t2715_vecinos_s2042.pt"),
    "v2": ("pt", "politica_dem_corredor_t2715_vecinos_v2_s42.pt"),
}
# evaluacion del plan con las mismas semillas (determinismo); D: Enmienda 3, con el mismo plan 25/10 en D
PLAN_CSV = {
    ("O", "fijo"): "demanda2/eval_dem_corredor_t2715_fijo.csv",
    ("O", "actuado"): "demanda2/eval_dem_corredor_t2715_actuado.csv",
    ("O", "actual"): "demanda2/eval_dem_corredor_t2715_ippo_vecinos_s2042.csv",
    ("O", "v2"): "diag_corredor/eval/eval_dem_corredor_t2715_ippo_vecinos_v2_s42_1001.csv",
    ("D", "fijo"): "diag_corredor/eval3/eval_d_fijo2715_1001.csv",
    ("D", "actuado"): "diag_corredor/eval3/eval_d_actuado_1001.csv",
    ("D", "actual"): "diag_corredor/eval3/eval_d_ippo_actual_1001.csv",
    ("D", "v2"): "diag_corredor/eval3/eval_d_ippo_v2_1001.csv",
}
METRICAS_CONTROL = ["retraso_total_prom", "timeloss_prom", "retraso_insercion_prom", "cambios_fase",
                    "no_insertados", "vehiculos"]
SEMAFOROS = ["semaforo_C1", "semaforo_C2"]
ACCESOS = ["W_C1", "C2_C1", "N1_C1", "S1_C1", "C1_C2", "E_C2", "N2_C2", "S2_C2"]
ENTRADAS = ["W_C1", "E_C2", "N1_C1", "S1_C1", "N2_C2", "S2_C2"]
ENLACES = ["C1_C2", "C2_C1"]
TRANSVERSAL = {"semaforo_C1": ["N1_C1", "S1_C1"], "semaforo_C2": ["N2_C2", "S2_C2"]}
AVENIDA = {"semaforo_C1": ["W_C1", "C2_C1"], "semaforo_C2": ["C1_C2", "E_C2"]}
# acceso transversal cuyo giro a la izquierda del periodo 2 de O espera en cada cruce (N1->E en C1, S2->W en C2)
GIRO_TRANSVERSAL = {"semaforo_C1": "N1_C1", "semaforo_C2": "S2_C2"}
OPUESTO = {"W_C1": "C2_C1", "C2_C1": "W_C1", "N1_C1": "S1_C1", "S1_C1": "N1_C1",
           "C1_C2": "E_C2", "E_C2": "C1_C2", "N2_C2": "S2_C2", "S2_C2": "N2_C2"}
SALIDA_VECINO = {"semaforo_C1": "C1_C2", "semaforo_C2": "C2_C1"}     # enlace que sale hacia el otro cruce
# condiciones de los instantes de decision de IPPO que se tabulan en bloqueo_decisiones.csv
CONDICIONES = [("todas", lambda x: True),
               ("cabeza_izq_detenida", lambda x: x["cabeza_izq_detenida"]),
               ("cabeza_no_izq_detenida", lambda x: not x["cabeza_izq_detenida"]),
               ("transversales_sin_detenidos", lambda x: x["det_transversal"] == 0),
               ("transversales_con_detenidos", lambda x: x["det_transversal"] >= 1),
               ("enlace_salida_0-4_detenidos", lambda x: x["det_enlace"] <= 4),
               ("enlace_salida_5-9_detenidos", lambda x: 5 <= x["det_enlace"] <= 9),
               ("enlace_salida_10+_detenidos", lambda x: x["det_enlace"] >= 10)]
DETENIDO = 0.1          # m/s, el umbral de detenido de SUMO (getLastStepHaltingNumber)
LARGO = 5.0             # largo del vType auto
LIBRE_MIN = 7.5         # plaza de un vehiculo (5 m + 2.5 m de minGap, comun.LARGO_VEH + MIN_GAP)
VEL_COLA = 2.0          # m/s: el ultimo vehiculo del enlace va mas lento que esto = es parte de la cola
PERIODOS = {1: (1, 1800), 2: (1801, 3600)}      # fila t = el segundo (t-1, t]; despues de 3600, vaciado
PASO_DECISION, VERDE_MIN = 5, 10                 # reloj de decision de rl_ippo (verdes de 10, 15, 20... s)


def rango(texto):
    if "-" in texto:
        a, b = texto.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in texto.split(",")]


def nombre_base(esc, control, semilla):
    return f"{esc}_{control}_s{semilla}"


# ---------------- preparar ----------------
def leer_programa(ruta):
    """{tls: (offset, [duraciones])} de los tlLogic de un .add.xml."""
    return {tl.get("id"): (tl.get("offset"), [int(float(p.get("duration"))) for p in tl.findall("phase")])
            for tl in ET.parse(ruta).getroot().findall("tlLogic")}


def preparar_datos(datos):
    """Copia el fijo 25/10 (desfases 0/0) a --datos y escribe o.sumocfg y d.sumocfg con rutas absolutas y las
    mismas opciones que dem_corredor_t2715.sumocfg."""
    os.makedirs(datos, exist_ok=True)
    copia = os.path.join(datos, FIJO_COPIA)
    if not os.path.exists(copia):
        shutil.copyfile(FIJO_ORIGEN, copia)
    esperado = {tls: ("0", [10, 3, 25, 3]) for tls in SEMAFOROS}
    if leer_programa(copia) != esperado:
        raise SystemExit(f"{copia} no es el plan 25/10 con desfases 0/0: {leer_programa(copia)}")
    for esc, (rutas, _) in ESCENARIOS.items():
        with open(os.path.join(datos, f"{esc.lower()}.sumocfg"), "w", encoding="utf-8") as f:
            f.write(f"""<configuration>
    <input>
        <net-file value="{RED}" />
        <route-files value="{os.path.join(PLAN2, rutas)}" />
        <additional-files value="{copia}" />
    </input>
    <time>
        <begin value="0" />
        <step-length value="1" />
    </time>
    <processing>
        <time-to-teleport value="-1" />
    </processing>
    <report>
        <no-step-log value="true" />
        <no-warnings value="true" />
    </report>
</configuration>
""")


def mapa_links():
    """Links de los dos semaforos leidos de la red: {acceso: {"tls", "carril", "largo", "mov": {dir: (k,
    salida, via)}, "via": {via: dir}, "salida": {arista: dir}}}."""
    raiz = ET.parse(RED).getroot()
    largos = {l.get("id"): float(l.get("length")) for e in raiz.findall("edge") for l in e.findall("lane")}
    acc = {}
    for c in raiz.findall("connection"):
        if c.get("tl") not in SEMAFOROS:
            continue
        a = c.get("from")
        d = acc.setdefault(a, {"tls": c.get("tl"), "carril": f"{a}_0", "largo": largos[f"{a}_0"],
                               "mov": {}, "via": {}, "salida": {}})
        d["mov"][c.get("dir")] = (int(c.get("linkIndex")), c.get("to"), c.get("via"))
        d["via"][c.get("via")] = c.get("dir")
        d["salida"][c.get("to")] = c.get("dir")
    assert sorted(acc) == sorted(ACCESOS), sorted(acc)
    return acc, largos


# ---------------- registro por segundo ----------------
class Registro:
    """Lo que se lee despues de cada traci.simulationStep(). Solo getters y suscripciones de VEHICULOS: el
    control (rl_corredor, rl_ippo, comun.MedidorEnlaces) suscribe aristas, carriles y semaforos, y suscribir
    de nuevo esos objetos reemplazaria sus variables."""

    def __init__(self):
        import traci.constants as tc
        self.tc = tc
        self.vars = [tc.VAR_LANE_ID, tc.VAR_LANEPOSITION, tc.VAR_SPEED]
        self.acc, self.largos = mapa_links()
        self.ruta = {}                 # vehiculo -> aristas de su ruta
        self.origen = {}               # flujo -> arista de entrada (para los que esperan entrar)
        self.previos = {a: set() for a in ACCESOS}
        self.filas = []
        self.comprobado = False

    def comprobar_links(self):
        """El mapa leido de la red coincide con getControlledLinks."""
        import traci
        for tls in SEMAFOROS:
            for k, links in enumerate(traci.trafficlight.getControlledLinks(tls)):
                for entra, sale, via in links:
                    a, s = entra.rsplit("_", 1)[0], sale.rsplit("_", 1)[0]
                    d = self.acc[a]["salida"][s]
                    assert self.acc[a]["tls"] == tls and self.acc[a]["mov"][d] == (k, s, via), (tls, k, links)
        self.comprobado = True

    def paso(self):
        import traci
        tc = self.tc
        if not self.comprobado:
            self.comprobar_links()
        t = int(round(traci.simulation.getTime()))
        for vid in traci.simulation.getDepartedIDList():
            traci.vehicle.subscribe(vid, self.vars)
            self.ruta[vid] = traci.vehicle.getRoute(vid)
        por_carril = {}
        for vid, d in traci.vehicle.getAllSubscriptionResults().items():
            por_carril.setdefault(d[tc.VAR_LANE_ID], []).append((d[tc.VAR_LANEPOSITION], d[tc.VAR_SPEED], vid))
        estados = {tls: traci.trafficlight.getRedYellowGreenState(tls) for tls in SEMAFOROS}
        fila = [t, estados["semaforo_C1"], estados["semaforo_C2"]]
        for a in ACCESOS:
            info = self.acc[a]
            en_carril = por_carril.get(info["carril"], [])
            n_det = sum(1 for _, v, _ in en_carril if v < DETENIDO)
            cand = [(p, v, vid, None) for p, v, vid in en_carril]
            for via, d in info["via"].items():
                cand += [(info["largo"] + p, v, vid, d) for p, v, vid in por_carril.get(via, [])]
            if cand:
                avance, v, vid, d = max(cand)
                if d is None:                         # en el carril: su siguiente arista
                    r = self.ruta[vid]
                    d = info["salida"][r[r.index(a) + 1]]
                cabeza = [d, round(v, 2), round(info["largo"] - avance, 1), vid]
            else:
                cabeza = ["-", "", "", ""]
            ahora = {vid for _, _, vid in en_carril}
            cruzaron = self.previos[a] - ahora
            n_izq = 0
            for vid in cruzaron:
                r = self.ruta[vid]
                if info["salida"][r[r.index(a) + 1]] == "l":
                    n_izq += 1
            self.previos[a] = ahora
            # detenidos en el primer tramo interno del giro a la izquierda (esperando el hueco dentro del cruce)
            via_izq = info["mov"]["l"][2]
            izq_dentro = sum(1 for _, v, _ in por_carril.get(via_izq, []) if v < DETENIDO)
            fila += [len(en_carril), n_det] + cabeza + [len(cruzaron), n_izq, izq_dentro]
        for e in ENLACES:
            en = por_carril.get(f"{e}_0", [])
            if en:
                p, v, _ = min(en)
                fila += [len(en), sum(1 for _, x, _ in en if x < DETENIDO), round(p - LARGO, 1), round(v, 2)]
            else:
                fila += [0, 0, round(self.largos[f"{e}_0"], 1), ""]
        pend = {}
        for vid in traci.simulation.getPendingVehicles():
            flujo = vid.rsplit(".", 1)[0]
            pend[self.origen.get(flujo)] = pend.get(self.origen.get(flujo), 0) + 1
        fila += [pend.get(a, 0) for a in ENTRADAS]
        self.filas.append(fila)

    @staticmethod
    def cabecera():
        c = ["t", "estado_C1", "estado_C2"]
        for a in ACCESOS:
            c += [f"{a}_{x}" for x in ("veh", "det", "cab_mov", "cab_vel", "cab_dist", "cab_id", "cruces",
                                       "cruces_izq", "izq_dentro")]
        for e in ENLACES:
            c += [f"{e}_{x}" for x in ("veh", "det", "libre", "vel_ultimo")]
        c += [f"pend_{a}" for a in ENTRADAS]
        return c


def leer_origenes(rutas):
    return {f.get("id"): f.get("from") for f in ET.parse(rutas).getroot().iter("flow")}


# ---------------- correr ----------------
def uno(esc, control, semilla, datos):
    """Una corrida con las funciones de evaluar.py y la envoltura de traci.simulationStep."""
    sys.path.insert(0, RAIZ)
    os.chdir(PLAN2)
    import traci
    import evaluar
    import rl_corredor
    rutas, nombre = ESCENARIOS[esc]
    cfg = os.path.join(datos, f"{esc.lower()}.sumocfg")
    # el escenario se registra solo en este proceso: la red y los semaforos del corredor, otro .sumocfg
    rl_corredor.ESCENARIOS[nombre] = {**rl_corredor.ESCENARIOS["corredor"], "cfg": cfg}
    tipo, valor = CONTROLES[control]
    if tipo == "pt":
        import torch
        import rl_ippo
        torch.set_num_threads(1)
        rl_ippo.ESCENARIOS[nombre] = {**rl_ippo.ESCENARIOS["dem_corredor_t2715"], "cfg": cfg}
        rl_ippo.VECINOS[nombre] = rl_ippo.VECINOS["corredor"]
        rl_ippo.LADOS[nombre] = rl_ippo.LADOS["corredor"]
        _, _, _, correr = evaluar.brazo_profundo(nombre, os.path.join(PLAN2, valor), 0, 0.0)
    else:
        _, _, _, correr = evaluar.brazo_referencia(nombre, valor)
    # el actuado escribe <escenario>_actuado.add.xml en la carpeta actual: una por corrida, fuera del repo
    base = nombre_base(esc, control, semilla)
    trabajo = os.path.join(datos, "tmp_" + base)
    os.makedirs(trabajo, exist_ok=True)
    os.chdir(trabajo)
    reg = Registro()
    reg.origen = leer_origenes(os.path.join(PLAN2, rutas))
    original = traci.simulationStep

    def envoltura(*a, **k):
        r = original(*a, **k)
        reg.paso()
        return r
    traci.simulationStep = envoltura
    random.seed(semilla)                    # como evaluar.main_v2
    t0 = time.time()
    tripinfo = os.path.join(datos, base + "_trip.xml")
    try:
        res = correr(semilla, tripinfo, None)
    finally:
        traci.simulationStep = original
    with gzip.open(os.path.join(datos, f"seg_{base}.csv.gz"), "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(Registro.cabecera())
        w.writerows(reg.filas)
    meta = {"escenario": esc, "control": control, "semilla": semilla, "cfg": cfg, "control_def": valor,
            "segundos": round(time.time() - t0, 1), "pasos": len(reg.filas),
            "metricas": {m: res.get(m) for m in METRICAS_CONTROL},
            "accesos": {a: {"tls": d["tls"], "mov": d["mov"]} for a, d in reg.acc.items()}}
    with open(os.path.join(datos, f"met_{base}.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    print(f"{base}: total {res['retraso_total_prom']}  timeLoss {res['timeloss_prom']}  "
          f"cambios {res['cambios_fase']}  {meta['segundos']} s", flush=True)


def correr(args):
    preparar_datos(args.datos)
    trabajos = [(e, c, s) for e in ESCENARIOS for c in CONTROLES for s in rango(args.semillas)]
    pendientes = [t for t in trabajos
                  if not os.path.exists(os.path.join(args.datos, f"met_{nombre_base(*t)}.json"))]
    pendientes.sort(key=lambda t: (CONTROLES[t[1]][0] != "pt", t))      # IPPO primero (mas lentas)
    activos = []
    while pendientes or activos:
        while pendientes and len(activos) < args.procesos:
            e, c, s = pendientes.pop(0)
            log = open(os.path.join(args.datos, f"log_{nombre_base(e, c, s)}.txt"), "w")
            p = subprocess.Popen([sys.executable, os.path.abspath(__file__), "uno", "--datos", args.datos,
                                  "--escenario", e, "--control", c, "--semilla", str(s)],
                                 stdout=log, stderr=subprocess.STDOUT)
            activos.append((p, log, (e, c, s)))
        time.sleep(2)
        for item in activos[:]:
            if item[0].poll() is not None:
                item[1].close()
                print(f"termino {nombre_base(*item[2])} (codigo {item[0].returncode})", flush=True)
                activos.remove(item)


# ---------------- analizar ----------------
def media(v):
    return statistics.mean(v) if v else None


def r(x, d=2):
    return "" if x is None else round(x, d)


def leer_segundos(ruta):
    """Filas por segundo con los tipos ya convertidos."""
    out = []
    with gzip.open(ruta, "rt", newline="", encoding="utf-8") as f:
        for x in csv.DictReader(f):
            fila = {"t": int(x["t"]), "estado": {"semaforo_C1": x["estado_C1"], "semaforo_C2": x["estado_C2"]}}
            for a in ACCESOS:
                fila[a] = {"veh": int(x[f"{a}_veh"]), "det": int(x[f"{a}_det"]), "mov": x[f"{a}_cab_mov"],
                           "vel": float(x[f"{a}_cab_vel"]) if x[f"{a}_cab_vel"] else None,
                           "dist": float(x[f"{a}_cab_dist"]) if x[f"{a}_cab_dist"] else None,
                           "id": x[f"{a}_cab_id"], "cruces": int(x[f"{a}_cruces"]),
                           "cruces_izq": int(x[f"{a}_cruces_izq"]), "izq_dentro": int(x[f"{a}_izq_dentro"])}
            for e in ENLACES:
                fila[e + "_enl"] = {"veh": int(x[f"{e}_veh"]), "det": int(x[f"{e}_det"]),
                                    "libre": float(x[f"{e}_libre"]),
                                    "vel": float(x[f"{e}_vel_ultimo"]) if x[f"{e}_vel_ultimo"] else None}
            fila["pend"] = {a: int(x[f"pend_{a}"]) for a in ENTRADAS}
            out.append(fila)
    return out


def entrada_ocupada(enl):
    """Al inicio del enlace queda menos de una plaza (la cola del ultimo vehiculo a menos de 7.5 m, o todavia
    dentro del cruce): un vehiculo detenido en verde que va hacia el no puede entrar."""
    return enl["veh"] > 0 and enl["libre"] < LIBRE_MIN


def lleno(enl, umbral=None):
    """La cola del enlace llega al cruce de aguas arriba: entrada ocupada por un ultimo vehiculo que va a menos
    de VEL_COLA (es parte de la cola; uno que entra libre va a 8-14 m/s). Con umbral=DETENIDO, la version
    estricta (el ultimo, detenido)."""
    return entrada_ocupada(enl) and enl["vel"] is not None and enl["vel"] < (umbral or VEL_COLA)


def clasificar(fila, a, acc):
    """Estado de la cabeza del acceso a en un segundo: vacio, marcha (se mueve), izq (gira a la izquierda y
    esta detenida), derrame (otro movimiento, detenida, con su salida = enlace lleno) u otro (detenida)."""
    c = fila[a]
    if c["mov"] == "-":
        return "vacio"
    if c["vel"] >= DETENIDO:
        return "marcha"
    if c["mov"] == "l":
        return "izq"
    salida = acc[a]["mov"][c["mov"]][1]
    if salida in ENLACES and entrada_ocupada(fila[salida + "_enl"]):
        return "derrame"
    return "otro"


def verde_acceso(fila, a, acc):
    """El acceso tiene verde (su movimiento recto en G o g; en este programa sus tres links cambian juntos)."""
    k = acc[a]["mov"]["s"][0]
    return fila["estado"][acc[a]["tls"]][k] in "Gg"


def periodo_de(t):
    for p, (a, b) in PERIODOS.items():
        if a <= t <= b:
            return p
    return None


def tramos_verde(filas, tls, accesos, acc):
    """[(inicio, fin)] (fin incluido) de los verdes de un grupo de accesos de un semaforo."""
    out, inicio = [], None
    for k, f in enumerate(filas):
        v = verde_acceso(f, accesos[0], acc)
        if v and inicio is None:
            inicio = k
        if not v and inicio is not None:
            out.append((inicio, k - 1))
            inicio = None
    return out                      # un verde que sigue al cerrar no se cuenta (incompleto)


def metricas_acceso(filas, acc):
    """Por periodo y acceso: segundos de verde y su clasificacion, cruces y descarga, episodios de bloqueo (un
    mismo vehiculo de cabeza detenido girando a la izquierda en segundos de verde seguidos) y cruces de otros
    movimientos mientras un vehiculo espera detenido dentro del cruce para girar a la izquierda."""
    out = {}
    for p in PERIODOS:
        for a in ACCESOS:
            out[(p, a)] = {k: 0 for k in ("seg_verde", "seg_izq", "seg_izq_cola", "seg_izq_salida_llena",
                                          "seg_derrame", "seg_otro", "seg_vacio", "seg_marcha", "cruces_verde",
                                          "cruces_izq_verde", "seg_verde_cola", "cruces_verde_cola",
                                          "cruces_ambar_rojo", "det_suma", "seg", "seg_verde_izq_dentro",
                                          "cruces_no_izq_con_izq_dentro", "episodios_izq", "izq_opuesto_marcha",
                                          "izq_opuesto_cruza")}
            out[(p, a)]["dur_episodios"] = []
    previa = None
    racha = {a: None for a in ACCESOS}            # (vehiculo, segundos) del episodio de bloqueo en curso
    for f in filas:
        p = periodo_de(f["t"])
        if p is None:
            previa = f
            continue
        for a in ACCESOS:
            m = out[(p, a)]
            m["seg"] += 1
            m["det_suma"] += f[a]["det"]
            verde = verde_acceso(f, a, acc)
            clase = clasificar(f, a, acc) if verde else None
            if clase == "izq" and racha[a] is not None and racha[a][0] == f[a]["id"]:
                racha[a][1] += 1
            else:
                if racha[a] is not None:
                    m["dur_episodios"].append(racha[a][1])
                racha[a] = [f[a]["id"], 1] if clase == "izq" else None
            if not verde:
                m["cruces_ambar_rojo"] += f[a]["cruces"]
                continue
            m["seg_verde"] += 1
            m["cruces_verde"] += f[a]["cruces"]
            m["cruces_izq_verde"] += f[a]["cruces_izq"]
            m["seg_" + clase] += 1
            if clase == "izq":
                # detenidos detras de ella en el carril (si la cabeza esta en el carril, ella es uno)
                detras = f[a]["det"] - (1 if f[a]["dist"] >= 0 else 0)
                if detras >= 1:
                    m["seg_izq_cola"] += 1
                salida = acc[a]["mov"]["l"][1]
                if salida in ENLACES and entrada_ocupada(f[salida + "_enl"]):
                    m["seg_izq_salida_llena"] += 1
                # lo que hace el acceso opuesto mientras tanto (el giro le cede el paso)
                o = OPUESTO[a]
                m["izq_opuesto_marcha"] += clasificar(f, o, acc) == "marcha"
                m["izq_opuesto_cruza"] += f[o]["cruces"] > 0
            if f[a]["izq_dentro"] >= 1:
                m["seg_verde_izq_dentro"] += 1
                m["cruces_no_izq_con_izq_dentro"] += f[a]["cruces"] - f[a]["cruces_izq"]
            if previa is not None and previa[a]["det"] >= 1:
                m["seg_verde_cola"] += 1
                m["cruces_verde_cola"] += f[a]["cruces"]
        previa = f
    for a in ACCESOS:                               # un episodio que sigue a los 3600 s se cierra ahi
        if racha[a] is not None:
            out[(2, a)]["dur_episodios"].append(racha[a][1])
    for (p, a), m in out.items():
        m["episodios_izq"] = len(m["dur_episodios"])
    return out


def verdes_y_decisiones(filas, acc):
    """Verdes completos de cada fase de cada semaforo, con los segundos de cabeza detenida girando a la
    izquierda en cada acceso del grupo; y, en cada instante de decision de rl_ippo (10, 15, 20... s de verde),
    si la cabeza del acceso con giro estaba detenida girando y si el verde siguio o termino."""
    verdes, decis = [], []
    for tls in SEMAFOROS:
        for fase, grupo in (("transversal", TRANSVERSAL[tls]), ("avenida", AVENIDA[tls])):
            for i, j in tramos_verde(filas, tls, grupo, acc):
                if i == 0:
                    continue                          # el primer verde empieza antes del registro
                p = periodo_de(filas[i]["t"])
                dur = j - i + 1
                bloq = {a: sum(1 for k in range(i, j + 1) if clasificar(filas[k], a, acc) == "izq") for a in grupo}
                verdes.append({"semaforo": tls[-2:], "fase": fase, "periodo": p, "inicio": filas[i]["t"],
                               "duracion": dur, **{f"izq_{a}": bloq[a] for a in grupo}})
                if fase == "transversal":
                    a = GIRO_TRANSVERSAL[tls]
                    k = VERDE_MIN
                    while k <= dur:
                        f = filas[i + k - 1]           # lo que ve la politica al decidir (fin del segundo k)
                        decis.append({"semaforo": tls[-2:], "periodo": p, "k": k,
                                      "cabeza_izq_detenida": clasificar(f, a, acc) == "izq",
                                      "cambia": k == dur, "det_acceso": f[a]["det"],
                                      "det_avenida": sum(f[x]["det"] for x in AVENIDA[tls]),
                                      "det_transversal": sum(f[x]["det"] for x in TRANSVERSAL[tls]),
                                      "det_enlace": f[SALIDA_VECINO[tls] + "_enl"]["det"]})
                        k += PASO_DECISION
    return verdes, decis


def metricas_enlace(filas, acc):
    """Por periodo y enlace: segundos lleno hasta el cruce de aguas arriba, verde del acceso que descarga en
    el (E_C2 en C2_C1, W_C1 en C1_C2) con la cabeza detenida por el derrame, detenidos y espera para entrar."""
    aguas_arriba = {"C2_C1": "E_C2", "C1_C2": "W_C1"}
    out = {}
    for p in PERIODOS:
        for e in ENLACES:
            a = aguas_arriba[e]
            g = [f for f in filas if periodo_de(f["t"]) == p]
            verde = [f for f in g if verde_acceso(f, a, acc)]
            out[(p, e)] = {
                "seg": len(g), "seg_lleno": sum(1 for f in g if lleno(f[e + "_enl"])),
                "seg_lleno_ultimo_detenido": sum(1 for f in g if lleno(f[e + "_enl"], DETENIDO)),
                "det_medio": media([f[e + "_enl"]["det"] for f in g]),
                "det_max": max(f[e + "_enl"]["det"] for f in g),
                "acceso": a, "seg_verde_acceso": len(verde),
                "seg_verde_acceso_lleno": sum(1 for f in verde if lleno(f[e + "_enl"])),
                "cruces_verde_acceso_lleno": sum(f[a]["cruces"] for f in verde if lleno(f[e + "_enl"])),
                "cruces_verde_acceso_no_lleno": sum(f[a]["cruces"] for f in verde if not lleno(f[e + "_enl"])),
                "seg_verde_acceso_derrame": sum(1 for f in verde if clasificar(f, a, acc) == "derrame"),
                "pend_medio": media([f["pend"][a] for f in g]),
                "pend_max": max(f["pend"][a] for f in g)}
    return out


def retraso_periodos(tripinfo, rutas):
    """Retraso total (timeLoss + espera para entrar) por vehiculo, por periodo de su flujo y movimiento, con
    las funciones de comportamiento.py (leer_flujos, leer_trip, movimiento)."""
    import comportamiento
    viajes = comportamiento.leer_trip(tripinfo, comportamiento.leer_flujos(rutas))
    out = {}
    for p in PERIODOS:
        for mov in ("todos", "avenida", "transversal", "giros"):
            g = [x for x in viajes if x["periodo"] == p and (mov == "todos" or x["mov"] == mov)]
            out[(p, mov)] = {"vehiculos": len(g),
                             "retraso_total": media([x["timeloss"] + x["delay"] for x in g]),
                             "timeloss": media([x["timeloss"] for x in g]),
                             "espera_entrar": media([x["delay"] for x in g])}
        g = [x for x in viajes if x["periodo"] == p and x["desde"] == "E_C2"]
        out[(p, "desde_E_C2")] = {"vehiculos": len(g), "retraso_total": media([x["timeloss"] + x["delay"] for x in g]),
                                  "timeloss": media([x["timeloss"] for x in g]),
                                  "espera_entrar": media([x["delay"] for x in g])}
    return out


def guardar(ruta, filas):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print("Escrito", ruta)


def leer_plan(esc, control):
    with open(os.path.join(PLAN2, PLAN_CSV[(esc, control)]), newline="", encoding="utf-8") as f:
        return {int(x["semilla"]): x for x in csv.DictReader(f)}


def analizar(args):
    datos, salida = args.datos, args.salida
    semillas = rango(args.semillas)
    t_acc, t_verdes, t_decis, t_enl, t_control, t_verdes_lista, t_per = [], [], [], [], [], [], []
    for esc in ESCENARIOS:
        for control in CONTROLES:
            plan = leer_plan(esc, control)
            por_sem, per_sem = {}, {}
            verdes_todos, decis_todos, enl_sem = [], [], {}
            for s in semillas:
                base = nombre_base(esc, control, s)
                with open(os.path.join(datos, f"met_{base}.json"), encoding="utf-8") as f:
                    meta = json.load(f)
                acc = {a: {"tls": d["tls"], "mov": {k: tuple(v) for k, v in d["mov"].items()}}
                       for a, d in meta["accesos"].items()}
                m, pl = meta["metricas"], plan[s]
                fila_c = {"escenario": esc, "control": control, "semilla": s}
                for k in METRICAS_CONTROL:
                    fila_c[k] = m[k]
                    fila_c["plan_" + k] = pl.get(k, "")
                fila_c["igual_al_plan"] = all(float(m[k]) == float(pl[k]) for k in METRICAS_CONTROL if pl.get(k, "") != "")
                fila_c["archivo_plan"] = PLAN_CSV[(esc, control)]
                t_control.append(fila_c)
                filas = leer_segundos(os.path.join(datos, f"seg_{base}.csv.gz"))
                por_sem[s] = metricas_acceso(filas, acc)
                v, d = verdes_y_decisiones(filas, acc)
                for x in v:
                    x["semilla"] = s
                verdes_todos += v
                decis_todos += d
                enl_sem[s] = metricas_enlace(filas, acc)
                rp = retraso_periodos(os.path.join(datos, base + "_trip.xml"),
                                      os.path.join(PLAN2, ESCENARIOS[esc][0]))
                per_sem[s] = rp
                print(f"analizado {base}", flush=True)
            for p in PERIODOS:
                for mov in ("todos", "avenida", "transversal", "giros", "desde_E_C2"):
                    filas_s = [{"escenario": esc, "control": control, "periodo": p, "grupo": mov, "semilla": s,
                                **{k: r(v, 2) for k, v in per_sem[s][(p, mov)].items()}} for s in semillas]
                    t_per += filas_s
                    t_per.append(promedio_filas(filas_s))
            # (i)-(iii) por acceso y periodo, por semilla y media
            for p in PERIODOS:
                for a in ACCESOS:
                    filas_s = []
                    for s in semillas:
                        m = por_sem[s][(p, a)]
                        filas_s.append(fila_acceso(esc, control, p, a, acc[a]["tls"], s, m))
                    t_acc += filas_s
                    t_acc.append(promedio_filas(filas_s))
            # (iv) verdes y decisiones
            for x in verdes_todos:
                t_verdes_lista.append({"escenario": esc, "control": control, **x})
            for tls in SEMAFOROS:
                sem = tls[-2:]
                for fase, grupo in (("transversal", TRANSVERSAL[tls]), ("avenida", AVENIDA[tls])):
                    for p in PERIODOS:
                        g = [x for x in verdes_todos if x["semaforo"] == sem and x["fase"] == fase and x["periodo"] == p]
                        for a in grupo:
                            for clase in ("todos", "con_cabeza_izq_detenida", "sin"):
                                h = [x for x in g if clase == "todos" or (clase == "sin") == (x[f"izq_{a}"] == 0)]
                                dur = [x["duracion"] for x in h]
                                t_verdes.append({
                                    "escenario": esc, "control": control, "semaforo": sem, "fase": fase,
                                    "periodo": p, "acceso": a, "clase": clase,
                                    "verdes_por_semilla": r(len(h) / len(semillas), 1),
                                    "duracion_media": r(media(dur), 1),
                                    "duracion_mediana": r(statistics.median(dur), 1) if dur else "",
                                    "frac_ge15s": r(sum(1 for x in dur if x >= 15) / len(dur), 3) if dur else "",
                                    "seg_izq_por_verde": r(media([x[f"izq_{a}"] for x in h]), 2),
                                    "frac_verde_izq": r(sum(x[f"izq_{a}"] for x in h) / max(1, sum(dur)), 3)})
                    if fase == "transversal" and control in ("actual", "v2"):
                        for p in PERIODOS:
                            for cond, filtro in CONDICIONES:
                                g = [x for x in decis_todos if x["semaforo"] == sem and x["periodo"] == p
                                     and filtro(x)]
                                t_decis.append({"escenario": esc, "control": control, "semaforo": sem,
                                                "periodo": p, "acceso": GIRO_TRANSVERSAL[tls],
                                                "enlace_salida": SALIDA_VECINO[tls], "condicion": cond,
                                                "decisiones": len(g),
                                                "frac_cambia": r(sum(1 for x in g if x["cambia"]) / len(g), 3)
                                                if g else "",
                                                "detenidos_acceso_medio": r(media([x["det_acceso"] for x in g]), 2),
                                                "detenidos_transversales_medio":
                                                    r(media([x["det_transversal"] for x in g]), 2),
                                                "detenidos_avenida_medio": r(media([x["det_avenida"] for x in g]), 2),
                                                "detenidos_enlace_salida_medio":
                                                    r(media([x["det_enlace"] for x in g]), 2)})
            # (v) enlaces llenos
            for p in PERIODOS:
                for e in ENLACES:
                    filas_s = []
                    for s in semillas:
                        m = enl_sem[s][(p, e)]
                        filas_s.append({"escenario": esc, "control": control, "periodo": p, "enlace": e,
                                        "semilla": s, **{k: (r(v, 2) if isinstance(v, float) else v)
                                                         for k, v in m.items()}})
                    t_enl += filas_s
                    t_enl.append(promedio_filas(filas_s))
    guardar(os.path.join(salida, "bloqueo.csv"), t_acc)
    guardar(os.path.join(salida, "bloqueo_verdes.csv"), t_verdes)
    guardar(os.path.join(salida, "bloqueo_decisiones.csv"), t_decis)
    guardar(os.path.join(salida, "bloqueo_derrame.csv"), t_enl)
    guardar(os.path.join(salida, "bloqueo_control.csv"), t_control)
    guardar(os.path.join(salida, "bloqueo_periodos.csv"), t_per)
    with gzip.open(os.path.join(datos, "verdes_lista.csv.gz"), "wt", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for x in t_verdes_lista for k in x}))
        w.writeheader()
        w.writerows(t_verdes_lista)


def fila_acceso(esc, control, p, a, tls, s, m):
    sv = m["seg_verde"]
    return {"escenario": esc, "control": control, "periodo": p, "acceso": a, "semaforo": tls[-2:],
            "semilla": s, "seg_verde": sv,
            "seg_cab_izq_detenida": m["seg_izq"],
            "frac_verde_cab_izq_detenida": r(m["seg_izq"] / sv, 3) if sv else "",
            "seg_cab_izq_detenida_con_cola": m["seg_izq_cola"],
            "seg_cab_izq_detenida_salida_llena": m["seg_izq_salida_llena"],
            "episodios_izq": m["episodios_izq"],
            "dur_media_episodio_izq": r(media(m["dur_episodios"]), 2),
            "seg_verde_izq_esperando_dentro": m["seg_verde_izq_dentro"],
            "cruces_no_izq_con_izq_dentro": m["cruces_no_izq_con_izq_dentro"],
            "frac_izq_opuesto_en_marcha": r(m["izq_opuesto_marcha"] / m["seg_izq"], 3) if m["seg_izq"] else "",
            "frac_izq_opuesto_cruza": r(m["izq_opuesto_cruza"] / m["seg_izq"], 3) if m["seg_izq"] else "",
            "seg_cab_derrame": m["seg_derrame"], "seg_cab_otro_detenida": m["seg_otro"],
            "seg_cab_marcha": m["seg_marcha"], "seg_vacio": m["seg_vacio"],
            "cruces_verde": m["cruces_verde"], "cruces_izq_verde": m["cruces_izq_verde"],
            "descarga_por_seg_verde": r(m["cruces_verde"] / sv, 3) if sv else "",
            "seg_verde_con_cola": m["seg_verde_cola"],
            "descarga_con_cola": r(m["cruces_verde_cola"] / m["seg_verde_cola"], 3) if m["seg_verde_cola"] else "",
            "cruces_ambar_rojo": m["cruces_ambar_rojo"],
            "detenidos_medio": r(m["det_suma"] / m["seg"], 2) if m["seg"] else ""}


def promedio_filas(filas_s):
    """Fila 'media' de varias semillas: media de cada columna numerica; las demas se copian."""
    out = dict(filas_s[0])
    out["semilla"] = "media"
    for k, v in filas_s[0].items():
        if k in ("semilla",) or isinstance(v, str) and v != "":
            continue
        vals = [x[k] for x in filas_s if x[k] != "" and x[k] is not None]
        if vals and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in vals):
            out[k] = round(statistics.mean(vals), 3)
    return out


# ---------------- tablas de bloqueo.md ----------------
NOMBRE = {"fijo": "fijo 25/10", "actuado": "actuado", "actual": "IPPO actual (s2042)", "v2": "V2 (s42)"}


def f1(x, d=1):
    return "" if x in ("", None) else f"{float(x):.{d}f}"


def tablas(args):
    """Imprime las tablas de bloqueo.md a partir de los CSV de --salida (medias de las semillas)."""
    def leer(nombre):
        with open(os.path.join(args.salida, nombre), newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    ctrl = leer("bloqueo_control.csv")
    per = [x for x in leer("bloqueo_periodos.csv") if x["semilla"] == "media"]
    acc_todas = leer("bloqueo.csv")
    acc = [x for x in acc_todas if x["semilla"] == "media"]
    ver = leer("bloqueo_verdes.csv")
    dec = leer("bloqueo_decisiones.csv")
    der = [x for x in leer("bloqueo_derrame.csv") if x["semilla"] == "media"]

    def uno(tabla, **k):
        g = [x for x in tabla if all(str(x[c]) == str(v) for c, v in k.items())]
        assert len(g) == 1, (k, len(g))
        return g[0]

    print("### Determinismo\n")
    print("| escenario | control | retraso total por corrida, semillas 1001-1005 (s/veh) | igual a la evaluacion |")
    print("|---|---|---|---|")
    for esc in ESCENARIOS:
        for c in CONTROLES:
            g = [x for x in ctrl if x["escenario"] == esc and x["control"] == c]
            iguales = sum(1 for x in g if x["igual_al_plan"] == "True")
            print(f"| {esc} | {NOMBRE[c]} | {' / '.join(x['retraso_total_prom'] for x in g)} | {iguales} de {len(g)} "
                  f"(`{g[0]['archivo_plan']}`) |")

    print("\n### Retraso total por periodo (s/veh, media de 5 semillas)\n")
    print("| control | hora O | hora D | P1 O | P2 O | P1 D | P2 D | P2 O - P2 D | E_C2 en P2: espera para entrar O / D |")
    print("|---|---|---|---|---|---|---|---|---|")
    for c in CONTROLES:
        hora = {esc: statistics.mean(float(x["retraso_total_prom"]) for x in ctrl
                                     if x["escenario"] == esc and x["control"] == c) for esc in ESCENARIOS}
        v = {(esc, p): float(uno(per, escenario=esc, control=c, periodo=p, grupo="todos")["retraso_total"])
             for esc in ESCENARIOS for p in PERIODOS}
        e = {esc: uno(per, escenario=esc, control=c, periodo=2, grupo="desde_E_C2")["espera_entrar"] for esc in ESCENARIOS}
        print(f"| {NOMBRE[c]} | {hora['O']:.2f} | {hora['D']:.2f} | {v[('O', 1)]:.1f} | {v[('O', 2)]:.1f} | "
              f"{v[('D', 1)]:.1f} | {v[('D', 2)]:.1f} | {v[('O', 2)] - v[('D', 2)]:+.1f} | {f1(e['O'])} / {f1(e['D'])} |")

    print("\n### (i)-(iii) Verde con la cabeza detenida girando a la izquierda, periodo 2 de O (s por corrida)\n")
    print("| acceso (giro que espera, flujo opuesto) | control | verde | cabeza izq. detenida | % del verde | "
          "con detenidos detras | episodios | s por episodio | opuesto en marcha / cruza (fraccion de esos s) | "
          "descarga (veh/s de verde) | descarga con cola | descarga con cola en D |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    giros = {"W_C1": "W->N1, opuesto C2_C1 recto 990", "C2_C1": "E->S1, opuesto W->E 375",
             "N1_C1": "N1->E, opuesto S1->N1 270", "S2_C2": "S2->W, opuesto N2->S2 270"}
    for a, texto in giros.items():
        for c in CONTROLES:
            x = uno(acc, escenario="O", control=c, periodo=2, acceso=a)
            xd = uno(acc, escenario="D", control=c, periodo=2, acceso=a)
            sv, si, ep = float(x["seg_verde"]), float(x["seg_cab_izq_detenida"]), float(x["episodios_izq"])
            print(f"| {a} ({texto}) | {NOMBRE[c]} | {sv:.0f} | {si:.1f} | {100 * si / sv:.0f} % | "
                  f"{float(x['seg_cab_izq_detenida_con_cola']):.1f} | {ep:.1f} | {f1(si / ep if ep else '')} | "
                  f"{f1(x['frac_izq_opuesto_en_marcha'], 2)} / {f1(x['frac_izq_opuesto_cruza'], 2)} | "
                  f"{f1(x['descarga_por_seg_verde'], 2)} | {f1(x['descarga_con_cola'], 2)} | {f1(xd['descarga_con_cola'], 2)} |")
    por_sem = [x for x in acc_todas if x["semilla"] != "media"]
    otros = sum(int(x["cruces_no_izq_con_izq_dentro"]) for x in por_sem)
    dentro = sum(int(x["seg_verde_izq_esperando_dentro"]) for x in por_sem)
    print(f"\nCruces de otros movimientos del mismo acceso mientras uno espera detenido dentro del cruce para girar: "
          f"{otros} en {dentro} s de verde (40 corridas, P1 y P2).")
    print(f"Segundos de verde con cabeza izq. detenida en D (todos los accesos y controles, P1 y P2) y en P1 de O, "
          f"40 corridas: {sum(int(x['seg_cab_izq_detenida']) for x in por_sem if x['escenario'] == 'D' or x['periodo'] == '1')}")

    print("\n### Reparto del verde en el periodo 2 (s por corrida)\n")
    print("| control | E_C2 verde O / D | E_C2 cruces en verde O / D | E_C2 veh/s de verde O / D | "
          "C2 transversal verde O / D | C1 transversal verde O / D |")
    print("|---|---|---|---|---|---|")
    for c in CONTROLES:
        x = {esc: uno(acc, escenario=esc, control=c, periodo=2, acceso="E_C2") for esc in ESCENARIOS}
        t2 = {esc: uno(acc, escenario=esc, control=c, periodo=2, acceso="S2_C2")["seg_verde"] for esc in ESCENARIOS}
        t1 = {esc: uno(acc, escenario=esc, control=c, periodo=2, acceso="N1_C1")["seg_verde"] for esc in ESCENARIOS}
        print(f"| {NOMBRE[c]} | {f1(x['O']['seg_verde'], 0)} / {f1(x['D']['seg_verde'], 0)} | "
              f"{f1(x['O']['cruces_verde'])} / {f1(x['D']['cruces_verde'])} | "
              f"{f1(x['O']['descarga_por_seg_verde'], 3)} / {f1(x['D']['descarga_por_seg_verde'], 3)} | "
              f"{f1(t2['O'], 0)} / {f1(t2['D'], 0)} | {f1(t1['O'], 0)} / {f1(t1['D'], 0)} |")

    print("\n### (iv) Verdes transversales del periodo 2: duracion y cabeza bloqueada\n")
    print("| control | cruce (acceso con giro) | verdes por corrida | duracion media O | con cabeza izq. detenida "
          "(n, media) | sin (n, media) | duracion media en D | IPPO: cambia en la decision, cabeza detenida / no "
          "(n decisiones) |")
    print("|---|---|---|---|---|---|---|---|")
    for c in ("actual", "v2", "actuado", "fijo"):
        for sem, a in (("C1", "N1_C1"), ("C2", "S2_C2")):
            def v(esc, clase):
                return uno(ver, escenario=esc, control=c, semaforo=sem, fase="transversal", periodo=2, acceso=a,
                           clase=clase)
            t, con, sin, d = v("O", "todos"), v("O", "con_cabeza_izq_detenida"), v("O", "sin"), v("D", "todos")
            texto_dec = ""
            if c in ("actual", "v2"):
                si = uno(dec, escenario="O", control=c, semaforo=sem, periodo=2, condicion="cabeza_izq_detenida")
                no = uno(dec, escenario="O", control=c, semaforo=sem, periodo=2, condicion="cabeza_no_izq_detenida")
                dd = uno(dec, escenario="D", control=c, semaforo=sem, periodo=2, condicion="cabeza_no_izq_detenida")
                texto_dec = (f"{f1(si['frac_cambia'], 3) or '-'} ({si['decisiones']}; {f1(si['detenidos_acceso_medio'])} det.) / "
                             f"{f1(no['frac_cambia'], 3)} ({no['decisiones']}; {f1(no['detenidos_acceso_medio'])} det.); "
                             f"D: {f1(dd['frac_cambia'], 3)} ({dd['decisiones']}; {f1(dd['detenidos_acceso_medio'])} det.)")
            print(f"| {NOMBRE[c]} | {sem} ({a}) | {t['verdes_por_semilla']} | {t['duracion_media']} | "
                  f"{con['verdes_por_semilla']}, {con['duracion_media'] or '-'} | {sin['verdes_por_semilla']}, "
                  f"{sin['duracion_media'] or '-'} | {d['duracion_media']} | {texto_dec} |")
    print("\nIPPO actual, decisiones en los verdes transversales de C2 en P2: fraccion que termina el verde "
          "(n decisiones), por condicion:")
    for cond, _ in CONDICIONES:
        o = uno(dec, escenario="O", control="actual", semaforo="C2", periodo=2, condicion=cond)
        d = uno(dec, escenario="D", control="actual", semaforo="C2", periodo=2, condicion=cond)
        print(f"- {cond}: O {f1(o['frac_cambia'], 3) or '-'} ({o['decisiones']}), "
              f"D {f1(d['frac_cambia'], 3) or '-'} ({d['decisiones']})")
    print("\nVerdes de avenida de C1 en P2 (acceso C2_C1): ")
    for c in CONTROLES:
        t = uno(ver, escenario="O", control=c, semaforo="C1", fase="avenida", periodo=2, acceso="C2_C1", clase="todos")
        d = uno(ver, escenario="D", control=c, semaforo="C1", fase="avenida", periodo=2, acceso="C2_C1", clase="todos")
        print(f"- {NOMBRE[c]}: O {t['duracion_media']} s ({t['seg_izq_por_verde']} s con cabeza izq. detenida por "
              f"verde), D {d['duracion_media']} s")

    print("\n### (v) Derrame\n")
    print("| control | C2_C1 en P2: cola hasta C2 (s) | ultimo detenido (s) | E_C2 en verde: con cola hasta C2 (s) | "
          "E_C2 en verde con cabeza detenida por derrame (s) | E_C2 veh/s de verde, con / sin cola hasta C2 | "
          "E_C2: esperan entrar, media / max | igual en D: cola hasta C2 / E_C2 bloqueada | "
          "C1_C2 en P1: cola hasta C1, O / D (s) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for c in CONTROLES:
        o = uno(der, escenario="O", control=c, periodo=2, enlace="C2_C1")
        d = uno(der, escenario="D", control=c, periodo=2, enlace="C2_C1")
        o1 = uno(der, escenario="O", control=c, periodo=1, enlace="C1_C2")
        d1 = uno(der, escenario="D", control=c, periodo=1, enlace="C1_C2")
        sl, sv = float(o["seg_verde_acceso_lleno"]), float(o["seg_verde_acceso"])
        con = float(o["cruces_verde_acceso_lleno"]) / sl if sl else None
        sin = float(o["cruces_verde_acceso_no_lleno"]) / (sv - sl)
        print(f"| {NOMBRE[c]} | {f1(o['seg_lleno'])} | {f1(o['seg_lleno_ultimo_detenido'])} | {f1(sl)} | "
              f"{f1(o['seg_verde_acceso_derrame'])} | {f1(con, 2)} / {f1(sin, 2)} | "
              f"{f1(o['pend_medio'])} / {f1(o['pend_max'])} | "
              f"{f1(d['seg_lleno'])} / {f1(d['seg_verde_acceso_derrame'])} | {f1(o1['seg_lleno'])} / "
              f"{f1(d1['seg_lleno'])} |")

    # asociaciones entre corridas en el periodo 2 de O (una fila por control y semilla)
    from scipy import stats
    todas_der = leer("bloqueo_derrame.csv")
    todas_per = leer("bloqueo_periodos.csv")
    for grupo in (("fijo", "actual", "v2"), tuple(CONTROLES)):
        claves = [(x["control"], x["semilla"]) for x in ctrl if x["escenario"] == "O" and x["control"] in grupo]

        def col(tabla, k, **filtro):
            idx = {(x["control"], x["semilla"]): x for x in tabla
                   if x["escenario"] == "O" and all(str(x[c]) == str(v) for c, v in filtro.items())}
            return [float(idx[cl][k]) for cl in claves]
        izq_c2c1 = col(acc_todas, "seg_cab_izq_detenida", periodo=2, acceso="C2_C1")
        izq_w = col(acc_todas, "seg_cab_izq_detenida", periodo=2, acceso="W_C1")
        izq_s2 = col(acc_todas, "seg_cab_izq_detenida", periodo=2, acceso="S2_C2")
        cola_c2 = col(todas_der, "seg_lleno", periodo=2, enlace="C2_C1")
        pend = col(todas_der, "pend_medio", periodo=2, enlace="C2_C1")
        p2 = col(todas_per, "retraso_total", periodo=2, grupo="todos")
        print(f"\nAsociaciones entre las {len(claves)} corridas de O ({', '.join(grupo)}), periodo 2, rho de Spearman (p):")
        for nombre, a_, b_ in (("C2_C1 cabeza izq. detenida vs retraso total del P2", izq_c2c1, p2),
                               ("S2_C2 cabeza izq. detenida vs retraso total del P2", izq_s2, p2),
                               ("W_C1 cabeza izq. detenida vs retraso total del P2", izq_w, p2),
                               ("C2_C1 cabeza izq. detenida vs cola de C2_C1 hasta C2", izq_c2c1, cola_c2),
                               ("cola de C2_C1 hasta C2 vs esperan entrar en E_C2", cola_c2, pend),
                               ("W_C1 cabeza izq. detenida vs C2_C1 cabeza izq. detenida", izq_w, izq_c2c1)):
            rho, p = stats.spearmanr(a_, b_)
            print(f"- {nombre}: {rho:.2f} (p = {p:.2g})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["correr", "uno", "analizar", "tablas"])
    ap.add_argument("--datos", default="", help="carpeta de las corridas (fuera del repositorio)")
    ap.add_argument("--salida", default=AQUI, help="carpeta de los CSV de resultados")
    ap.add_argument("--semillas", default="1001-1005")
    ap.add_argument("--procesos", type=int, default=4)
    ap.add_argument("--escenario", choices=list(ESCENARIOS))
    ap.add_argument("--control", choices=list(CONTROLES))
    ap.add_argument("--semilla", type=int)
    args = ap.parse_args()
    args.datos = os.path.abspath(args.datos)
    args.salida = os.path.abspath(args.salida)
    if args.accion == "correr":
        correr(args)
    elif args.accion == "uno":
        uno(args.escenario, args.control, args.semilla, args.datos)
    elif args.accion == "analizar":
        analizar(args)
    else:
        tablas(args)


if __name__ == "__main__":
    main()
