"""
periodos.py - Donde y cuando se acumula el retraso con 2715 veh/h en el corredor: por periodo, clase de
movimiento y arista de entrada, en el escenario original y en el contrafactual de la Enmienda 3 (diagnostico
del corredor, 25.10.2026; agente "periodos"). Analisis posterior al veredicto (PRERREGISTRO.md): no cambia
ningun veredicto ni corrige nada.

Escenarios (red corredor.net.xml: dos cruces a 300 m, todas las calles de un carril):
  O  dem_corredor_t2715      giros del periodo 2 a la izquierda (verde sin prioridad, estado g)
  D  dem_corredor_t2715_der  igual, pero con los giros del periodo 2 a la derecha (los del periodo 1)
Controles:
  fijo     25 s avenida / 10 s transversal, ambar 3 s, ciclo 41 s, desfases 0/0 en los dos escenarios: copia de
           plan2/dem_corredor_t2715.add.xml en --datos (plan2/dem_corredor_t2715_der.add.xml lo reescribe el
           barrido de la cola, por eso no se usa)
  actuado  el actuado de SUMO de evaluar.py (comun.archivo_actuado; su .add.xml se escribe en --datos)
  actual   IPPO con mensajes, version evaluada de 2715: politica_dem_corredor_t2715_vecinos_s2042.pt
  v2       IPPO con la correccion V2 (base 42): politica_dem_corredor_t2715_vecinos_v2_s42.pt
  Las dos politicas se entrenaron en O; en D se juegan sin reentrenar (Enmienda 3, prediccion a).

Uso (con plan2/ como directorio de trabajo; -B para no escribir __pycache__ en el repositorio):
  python -B diag_corredor/periodos.py correr   --datos <carpeta> [--semillas 1001-1010] [--procesos 4]
  python -B diag_corredor/periodos.py analizar --datos <carpeta> [--semillas 1001-1010] [--salida diag_corredor]

correr: escribe en --datos la copia del programa fijo y un .sumocfg por escenario (O.sumocfg, D.sumocfg: las
  opciones del .sumocfg del escenario en plan2/ con rutas absolutas a la red, a las rutas de plan2/ y a la
  copia) y corre cada escenario x control en las semillas con las funciones de evaluar.py (brazo_referencia,
  brazo_profundo), como comportamiento.correr_uno: tripinfo completo (con departDelay), estadisticas de SUMO,
  fase de cada semaforo por segundo y detenidos por acceso cada segundo (rl_corredor.PASO_SERIE = 1). Un
  proceso por escenario x control, como mucho --procesos (maximo 4) a la vez, cada uno con un SUMO. No escribe
  nada en plan2/. Las metricas de evaluar.py de cada corrida quedan en <datos>/metricas_<E>_<control>.csv.
analizar: lee esos archivos (con comportamiento.leer_trip, leer_flujos, leer_stats, leer_fases y
  analizar_fases) y escribe <salida>/periodos.csv, <salida>/periodos_extra.csv y <datos>/periodos_tablas.md (las
  tablas de periodos.md); compara cada corrida con la evaluacion del plan (O) o de la cola (D) con la misma
  semilla (determinismo).

Definiciones:
  periodo    el de la hora de salida pedida (depart - departDelay del tripinfo): 1 si < 1800 s, 2 si >= 1800 s;
             "hora" = los dos
  movimiento por origen y destino: avenida (W<->E recto), transversal (N<->S recto), izquierda, derecha (el giro
             que hace el vehiculo; cada flujo de giro gira una sola vez); "todos" = los cuatro
  arista     arista de entrada a la red (W_C1, E_C2, N1_C1, S1_C1, N2_C2, S2_C2); "todas" = las seis
  retraso total = timeLoss + departDelay (espera para entrar), como retraso_total_prom de comun.leer_tripinfo
periodos.csv: una fila por escenario, control, semilla, periodo, movimiento y arista (arista = "todas" da la
  fila por movimiento; movimiento = "todos" da la fila por arista); medias por vehiculo en s (la suma en s.veh
  es la media x vehiculos). periodos_extra.csv: los valores por corrida de las tablas (6)-(9) y del
  determinismo, en formato largo (escenario, control, semilla, medida, clave, valor).
"""
import os
import sys
import csv
import math
import time
import shutil
import random
import argparse
import statistics
import subprocess
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN2 = os.path.abspath(os.path.join(AQUI, ".."))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))      # carpeta con evaluar.py, rl_ippo.py...
sys.path.insert(0, AQUI)
import comportamiento as comp                                 # noqa: E402  (se reutiliza, sin modificarlo)

ESCENARIOS = {"O": {"esc": "dem_corredor_t2715", "rou": "dem_corredor_t2715.rou.xml"},
              "D": {"esc": "dem_corredor_t2715_der", "rou": "dem_corredor_t2715_der.rou.xml"}}
RED = "corredor.net.xml"
FIJO_ORIGEN = "dem_corredor_t2715.add.xml"
FIJO_COPIA = "fijo_25_10_desfases_0_0.add.xml"
# programa esperado en los dos semaforos: (programID, tipo, desfase, fases)
FIJO_ESPERADO = ("fijo", "static", "0", ((10, "GGgrrrGGgrrr"), (3, "yyyrrryyyrrr"),
                                         (25, "rrrGGgrrrGGg"), (3, "rrryyyrrryyy")))
CONTROLES = ["fijo", "actuado", "actual", "v2"]
POLITICAS = {"actual": "politica_dem_corredor_t2715_vecinos_s2042.pt",
             "v2": "politica_dem_corredor_t2715_vecinos_v2_s42.pt"}
NOMBRE = {"fijo": "fijo 25/10", "actuado": "actuado", "actual": "IPPO actual (s2042)", "v2": "V2 (s42)"}
# evaluaciones con las que se compara cada corrida (rutas desde plan2/): O, la del plan; D, la de la cola
# (diag3_eval_d_*, 18:20, con el mismo programa 25/10 en dem_corredor_t2715_der.add.xml)
REFERENCIA = {
    ("O", "fijo"): "demanda2/eval_dem_corredor_t2715_fijo.csv",
    ("O", "actuado"): "demanda2/eval_dem_corredor_t2715_actuado.csv",
    ("O", "actual"): "demanda2/eval_dem_corredor_t2715_ippo_vecinos_s2042.csv",
    ("O", "v2"): "diag_corredor/eval/eval_dem_corredor_t2715_ippo_vecinos_v2_s42_1001.csv",
    ("D", "fijo"): "diag_corredor/eval3/eval_d_fijo2715_1001.csv",
    ("D", "actuado"): "diag_corredor/eval3/eval_d_actuado_1001.csv",
    ("D", "actual"): "diag_corredor/eval3/eval_d_ippo_actual_1001.csv",
    ("D", "v2"): "diag_corredor/eval3/eval_d_ippo_v2_1001.csv",
}
FASES_REFERENCIA = {      # fase por segundo de la semilla 1001 que dejaron esas evaluaciones
    ("O", "fijo"): "fases_dem_corredor_t2715_fijo_s1001.csv",
    ("O", "actuado"): "fases_dem_corredor_t2715_actuado_s1001.csv",
    ("O", "actual"): "fases_dem_corredor_t2715_ippo_vecinos_s2042_s1001.csv",
    ("O", "v2"): "diag_corredor/eval/extras_1001/fases_dem_corredor_t2715_ippo_vecinos_v2_s42_s1001.csv",
    ("D", "fijo"): "diag_corredor/eval3/extras_1001/fases_dem_corredor_t2715_der_fijo_s1001.csv",
    ("D", "actuado"): "diag_corredor/eval3/extras_1001/fases_dem_corredor_t2715_der_actuado_s1001.csv",
    ("D", "actual"): "diag_corredor/eval3/extras_1001/fases_dem_corredor_t2715_der_ippo_vecinos_s2042_s1001.csv",
    ("D", "v2"): "diag_corredor/eval3/extras_1001/fases_dem_corredor_t2715_der_ippo_vecinos_v2_s42_s1001.csv",
}
COMPARAR = ("retraso_total_prom", "timeloss_prom", "retraso_insercion_prom", "cambios_fase", "no_insertados")
PERIODO = 1800
FIN = 3600
PERIODOS = [1, 2, "hora"]
CLASES = ["avenida", "transversal", "izquierda", "derecha"]
MOVIMIENTOS = CLASES + ["todos"]
ENTRADAS = comp.ENTRADAS                       # W_C1, E_C2, N1_C1, S1_C1, N2_C2, S2_C2
ACCESOS = comp.ACCESOS                         # los ocho accesos de los dos semaforos
# rumbo con el que se entra por cada arista de entrada y con el que se sale por cada arista de salida
RUMBO_ENTRADA = {"W_C1": "E", "E_C2": "O", "N1_C1": "S", "N2_C2": "S", "S1_C1": "N", "S2_C2": "N"}
RUMBO_SALIDA = {"C2_E": "E", "C1_W": "O", "C1_N1": "N", "C2_N2": "N", "C1_S1": "S", "C2_S2": "S"}
ANGULO = {"N": 0, "E": 90, "S": 180, "O": 270}


def clase(desde, hasta):
    """avenida, transversal, izquierda o derecha, por el rumbo de entrada y el de salida."""
    giro = (ANGULO[RUMBO_SALIDA[hasta]] - ANGULO[RUMBO_ENTRADA[desde]]) % 360
    if giro == 0:
        return "avenida" if RUMBO_ENTRADA[desde] in ("E", "O") else "transversal"
    if giro == 90:
        return "derecha"
    if giro == 270:
        return "izquierda"
    raise ValueError(f"vuelta en U: {desde} -> {hasta}")


# ---------------- correr ----------------
def leer_programa(ruta):
    raiz = ET.parse(ruta).getroot()
    return {tl.get("id"): (tl.get("programID"), tl.get("type"), tl.get("offset"),
                           tuple((int(float(p.get("duration"))), p.get("state")) for p in tl.findall("phase")))
            for tl in raiz.findall("tlLogic")}


def preparar(datos):
    """Copia del programa fijo 25/10 (desfases 0/0) y un .sumocfg por escenario en datos (rutas absolutas)."""
    os.makedirs(datos, exist_ok=True)
    copia = os.path.join(datos, FIJO_COPIA)
    if not os.path.exists(copia):
        shutil.copyfile(os.path.join(PLAN2, FIJO_ORIGEN), copia)
    prog = leer_programa(copia)
    for tls in comp.SEMAFOROS:
        if prog.get(tls) != FIJO_ESPERADO:
            raise SystemExit(f"{copia}: {tls} no tiene el programa 25/10 con desfase 0: {prog.get(tls)}")
    for E, e in ESCENARIOS.items():
        arbol = ET.parse(os.path.join(PLAN2, e["esc"] + ".sumocfg"))
        entrada = arbol.getroot().find("input")
        entrada.find("net-file").set("value", os.path.join(PLAN2, RED))
        entrada.find("route-files").set("value", os.path.join(PLAN2, e["rou"]))
        entrada.find("additional-files").set("value", copia)
        arbol.write(os.path.join(datos, f"{E}.sumocfg"), encoding="utf-8", xml_declaration=False)
    return copia


def correr_uno(E, control, semillas, datos):
    """Corre un escenario x control en las semillas, con las funciones de evaluar.py y el .sumocfg de datos."""
    os.chdir(PLAN2)
    sys.path.insert(0, RAIZ)
    import comun
    import evaluar
    import rl_corredor
    rl_corredor.PASO_SERIE = 1          # detenidos por acceso cada segundo (rl_ippo lo lee de aqui tambien)
    esc = ESCENARIOS[E]["esc"]
    cfg = os.path.join(datos, f"{E}.sumocfg")
    original = comun.archivo_actuado

    def actuado_en_datos(cfg_, escenario, *a, **k):
        # mismo programa actuado; solo cambia la carpeta del <esc>_actuado.add.xml (no se escribe en plan2/)
        return original(cfg_, os.path.join(datos, escenario), *a, **k)
    comun.archivo_actuado = actuado_en_datos
    if control in ("fijo", "actuado"):
        brazo, _, _, correr = evaluar.brazo_referencia(esc, control)
        rl_corredor.CFG = cfg           # correr_episodio lee el global en cada corrida
    else:
        import rl_ippo
        brazo, _, _, correr = evaluar.brazo_profundo(esc, POLITICAS[control], 0, 0.0)
        rl_ippo.C["cfg"] = cfg          # preparar() lo fijo con el .sumocfg de plan2/; las rutas son las mismas
    filas = []
    for s in semillas:
        random.seed(s)                  # como evaluar.main_v2 (estos controles no usan random)
        t0 = time.time()
        base = os.path.join(datos, f"{E}_{control}_s{s}")
        res = correr(s, base + "_trip.xml", os.path.join(datos, f"serie_{E}_{control}_s{s}.csv"))
        filas.append({"escenario": E, "escenario_sumo": esc, "control": control, "brazo": brazo, "semilla": s,
                      **{m: res.get(m, "") for m in evaluar.METRICAS}})
        print(f"{E} {control} s{s}: total {res['retraso_total_prom']}  timeLoss {res['timeloss_prom']}  "
              f"espera {res['retraso_insercion_prom']}  {time.time() - t0:.0f}s", flush=True)
    salida = os.path.join(datos, f"metricas_{E}_{control}.csv")
    with open(salida + ".tmp", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    os.replace(salida + ".tmp", salida)


def correr(args):
    copia = preparar(args.datos)
    print(f"Programa fijo: {copia}; .sumocfg: {args.datos}/O.sumocfg y D.sumocfg", flush=True)
    procesos = max(1, min(4, args.procesos))       # no mas de 4 SUMO a la vez (la cola usa 10 CPU)
    trabajos = [(E, c) for E in ESCENARIOS for c in CONTROLES]
    pendientes = [t for t in trabajos if not os.path.exists(os.path.join(args.datos, f"metricas_{t[0]}_{t[1]}.csv"))]
    pendientes.sort(key=lambda t: t[1] in ("fijo", "actuado"))      # IPPO primero (mas lento)
    activos = []
    while pendientes or activos:
        while pendientes and len(activos) < procesos:
            E, c = pendientes.pop(0)
            log = open(os.path.join(args.datos, f"log_{E}_{c}.txt"), "w")
            p = subprocess.Popen([sys.executable, "-B", os.path.abspath(__file__), "uno", "--escenario", E,
                                  "--control", c, "--semillas", args.semillas, "--datos", args.datos],
                                 stdout=log, stderr=subprocess.STDOUT, cwd=PLAN2)
            activos.append((p, log, E, c))
            print(f"inicio {E} {c}", flush=True)
        time.sleep(2)
        for item in activos[:]:
            if item[0].poll() is not None:
                item[1].close()
                print(f"termino {item[2]} {item[3]} (codigo {item[0].returncode})", flush=True)
                activos.remove(item)


# ---------------- analizar: utilidades ----------------
def media(v):
    v = [x for x in v if x is not None]
    return statistics.mean(v) if v else None


def r(x, d=2):
    return "" if x is None else round(x, d)


def f1(x, d=1):
    return "" if x is None else f"{x:.{d}f}"


def ic_t(d):
    from scipy import stats
    n = len(d)
    if n < 2:
        return (None, None)
    m, h = statistics.mean(d), stats.t.ppf(0.975, n - 1) * statistics.stdev(d) / math.sqrt(n)
    return (m - h, m + h)


def ic_boot(d, n_boot=10000):
    """IC95 bootstrap pareado (percentil) de la media de las diferencias por semilla."""
    import numpy as np
    rng = np.random.default_rng(0)
    d = np.asarray(d, dtype=float)
    idx = rng.integers(0, len(d), size=(n_boot, len(d)))
    m = d[idx].mean(axis=1)
    return (float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)))


def p_wilcoxon(d):
    from scipy import stats
    return stats.wilcoxon(d).pvalue if any(x != 0 for x in d) else 1.0


def ic_txt(ic, d=1):
    return f"[{ic[0]:+.{d}f}, {ic[1]:+.{d}f}]" if ic[0] is not None else ""


def tabla_md(cabecera, filas):
    out = ["| " + " | ".join(cabecera) + " |", "|" + "|".join("---" for _ in cabecera) + "|"]
    out += ["| " + " | ".join(str(c) for c in fila) + " |" for fila in filas]
    return "\n".join(out)


def cargar_viajes(ruta, flujos):
    """comportamiento.leer_trip mas destino, clase de movimiento y periodo por la salida pedida."""
    viajes = comp.leer_trip(ruta, flujos)
    for x in viajes:
        desde, hasta = flujos[x["flujo"]]
        x["hasta"] = hasta
        x["clase"] = clase(desde, hasta)
        x["pedida"] = round(x["depart"] - x["delay"], 2)
        x["per"] = 1 if x["pedida"] < PERIODO else 2
        x["total"] = x["timeloss"] + x["delay"]
    return viajes


def agregar(viajes):
    """{(periodo, movimiento, arista): (n, s.veh total, s.veh timeLoss, s.veh espera)} de una corrida."""
    acum = {}
    for x in viajes:
        for p in (x["per"], "hora"):
            for m in (x["clase"], "todos"):
                for a in (x["desde"], "todas"):
                    n, t, tl, e = acum.get((p, m, a), (0, 0.0, 0.0, 0.0))
                    acum[(p, m, a)] = (n + 1, t + x["total"], tl + x["timeloss"], e + x["delay"])
    return acum


def leer_serie(ruta):
    """Detenidos medios por acceso en el periodo 1 (t < 1800) y en el 2 (1800 <= t <= 3600), segundo final
    de la corrida y segundos del periodo 2 con algun enlace interno con >= 34 detenidos (90 % de 38 plazas)."""
    filas = comp.leer_csv(ruta)
    suma = {(a, p): 0 for a in ACCESOS for p in (1, 2)}
    cuenta = {1: 0, 2: 0}
    lleno = {1: 0, 2: 0}
    for x in filas:
        t = int(x["t"])
        if t > FIN:
            continue
        p = 1 if t < PERIODO else 2
        cuenta[p] += 1
        for a in ACCESOS:
            suma[(a, p)] += int(x[a])
        if int(x["C1_C2"]) >= 34 or int(x["C2_C1"]) >= 34:
            lleno[p] += 1
    out = {(a, p): suma[(a, p)] / max(1, cuenta[p]) for a in ACCESOS for p in (1, 2)}
    out["fin"] = int(filas[-1]["t"])
    out["lleno"] = lleno
    return out


TRAMOS_EC2 = list(range(1800, 4200, 300))      # tramos de 5 min desde el minuto 30 hasta el 70


def esperando_ec2(viajes):
    """Vehiculos que esperan para entrar por E_C2 (salida pedida <= t < salida real), media de cada tramo de
    5 min muestreada cada 10 s, y espera media para entrar por E_C2 en el periodo 2."""
    v = [(x["pedida"], x["depart"]) for x in viajes if x["desde"] == "E_C2"]
    out = {}
    for t0 in TRAMOS_EC2:
        ts = range(t0, t0 + 300, 10)
        out[t0] = sum(sum(1 for a, b in v if a <= t < b) for t in ts) / len(ts)
    p2 = [x["delay"] for x in viajes if x["desde"] == "E_C2" and x["per"] == 2]
    out["espera_p2"] = sum(p2) / max(1, len(p2))
    return out


# ---------------- analizar ----------------
def analizar(args):
    datos, salida = args.datos, args.salida
    semillas = comp.rango(args.semillas)
    flujos = {E: comp.leer_flujos(os.path.join(PLAN2, e["rou"])) for E, e in ESCENARIOS.items()}
    A = {}                      # (E, c, s) -> agregar(...)
    perfil = {}                 # (E, c, s) -> {bin de 300 s: (n, s.veh)}
    series = {}                 # (E, c, s) -> leer_serie(...)
    verdes = {}                 # (E, c, s) -> comportamiento.analizar_fases(...)
    cola_ec2 = {}               # (E, c, s) -> esperando_ec2(...)
    control_filas = []          # determinismo
    avisos = []
    filas_csv = []
    for E in ESCENARIOS:
        for c in CONTROLES:
            met = {int(x["semilla"]): x for x in comp.leer_csv(os.path.join(datos, f"metricas_{E}_{c}.csv"))}
            ruta_ref = os.path.join(PLAN2, REFERENCIA[(E, c)])
            ref = {int(x["semilla"]): x for x in comp.leer_csv(ruta_ref)} if os.path.exists(ruta_ref) else {}
            for s in semillas:
                trip = os.path.join(datos, f"{E}_{c}_s{s}_trip.xml")
                viajes = cargar_viajes(trip, flujos[E])
                st = comp.leer_stats(trip[:-4] + "_stats.xml")
                distintos = sum(1 for x in viajes if x["per"] != x["periodo"])
                if distintos:
                    avisos.append(f"{E} {c} s{s}: {distintos} vehiculos con periodo por salida pedida distinto del "
                                  f"prefijo del flujo")
                A[(E, c, s)] = agregar(viajes)
                pf = {}
                for x in viajes:
                    b = min(11, int(x["pedida"] // 300))
                    n, t = pf.get(b, (0, 0.0))
                    pf[b] = (n + 1, t + x["total"])
                perfil[(E, c, s)] = pf
                series[(E, c, s)] = leer_serie(os.path.join(datos, f"serie_{E}_{c}_s{s}.csv"))
                verdes[(E, c, s)] = comp.analizar_fases(comp.leer_fases(os.path.join(datos, f"fases_{E}_{c}_s{s}.csv")))
                cola_ec2[(E, c, s)] = esperando_ec2(viajes)
                for clave in [(p, m, a) for p in PERIODOS for m in MOVIMIENTOS for a in ["todas"] + ENTRADAS]:
                    if clave not in A[(E, c, s)]:
                        continue
                    n, t, tl, e = A[(E, c, s)][clave]
                    filas_csv.append({"escenario": E, "control": c, "semilla": s, "periodo": clave[0],
                                      "movimiento": clave[1], "arista": clave[2], "vehiculos": n,
                                      "retraso_total_medio": r(t / n, 3), "timeloss_medio": r(tl / n, 3),
                                      "espera_entrar_media": r(e / n, 3)})
                # determinismo: la corrida contra la evaluacion de referencia con la misma semilla
                m_, rf = met[s], ref.get(s)
                n_h, t_h = A[(E, c, s)][("hora", "todos", "todas")][:2]
                fila = {"escenario": E, "control": c, "semilla": s,
                        "retraso_total": m_["retraso_total_prom"],
                        "ref_retraso_total": rf["retraso_total_prom"] if rf else "",
                        "igual": (all(float(m_[k]) == float(rf[k]) for k in COMPARAR) if rf else ""),
                        "tripinfo_igual_metrica": round(t_h / n_h, 2) == float(m_["retraso_total_prom"]),
                        "no_insertados": st["no_insertados"], "teleports": st["teleports"], "vehiculos": n_h}
                if s == 1001:
                    ruta_f = os.path.join(PLAN2, FASES_REFERENCIA[(E, c)])
                    if os.path.exists(ruta_f):
                        with open(ruta_f, encoding="utf-8") as fa, \
                                open(os.path.join(datos, f"fases_{E}_{c}_s{s}.csv"), encoding="utf-8") as fb:
                            fila["fases_s1001_igual"] = fa.read() == fb.read()
                control_filas.append(fila)
            print(f"analizado {E} {c}", flush=True)
    ruta_csv = os.path.join(salida, "periodos.csv")
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas_csv[0].keys()))
        w.writeheader()
        w.writerows(filas_csv)
    print("Escrito", ruta_csv)
    # valores por corrida de las tablas (6)-(9) y del determinismo: periodos_extra.csv (formato largo)
    extra = []
    for (E, c, s) in sorted(A):
        def fila(medida, clave, valor):
            extra.append({"escenario": E, "control": c, "semilla": s, "medida": medida, "clave": clave,
                          "valor": r(valor, 3) if isinstance(valor, float) else valor})
        for b in range(12):
            if b in perfil[(E, c, s)]:
                n, t = perfil[(E, c, s)][b]
                fila("retraso_total_por_tramo_5min", f"{5 * b}-{5 * b + 5}", t / n)
        for p in (1, 2):
            for a in ACCESOS:
                fila("detenidos_medios", f"P{p}_{a}", series[(E, c, s)][(a, p)])
            fila("seg_enlace_interno_ge34", f"P{p}", series[(E, c, s)]["lleno"][p])
            for tls in comp.SEMAFOROS:
                af = verdes[(E, c, s)][tls]
                sv = af["seg_verde_p"]
                fila("frac_verde_avenida", f"P{p}_{tls[-2:]}", sv[(2, p)] / max(1, sv[(0, p)] + sv[(2, p)]))
                fila("verde_avenida_mediana", f"P{p}_{tls[-2:]}", comp.pct(af["verdes_p"][(2, p)], 50))
                fila("verde_transversal_mediana", f"P{p}_{tls[-2:]}", comp.pct(af["verdes_p"][(0, p)], 50))
        fila("fin_corrida_s", "", series[(E, c, s)]["fin"])
        for t0 in TRAMOS_EC2:
            fila("esperando_entrar_E_C2", f"{t0 // 60}-{t0 // 60 + 5}", cola_ec2[(E, c, s)][t0])
        fila("espera_media_E_C2", "P2", cola_ec2[(E, c, s)]["espera_p2"])
    for x in control_filas:
        for k in ("retraso_total", "ref_retraso_total", "igual", "tripinfo_igual_metrica", "no_insertados",
                  "teleports", "fases_s1001_igual"):
            if k in x:
                extra.append({"escenario": x["escenario"], "control": x["control"], "semilla": x["semilla"],
                              "medida": "determinismo", "clave": k, "valor": x[k]})
    ruta_extra = os.path.join(salida, "periodos_extra.csv")
    with open(ruta_extra, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["escenario", "control", "semilla", "medida", "clave", "valor"])
        w.writeheader()
        w.writerows(extra)
    print("Escrito", ruta_extra)
    texto = tablas(A, perfil, series, verdes, cola_ec2, control_filas, avisos, semillas)
    ruta_md = args.tablas or os.path.join(datos, "periodos_tablas.md")
    with open(ruta_md, "w", encoding="utf-8") as f:
        f.write(texto)
    print("Escrito", ruta_md)


def tablas(A, perfil, series, verdes, cola_ec2, control_filas, avisos, semillas):
    """Las tablas de periodos.md, en Markdown."""
    S = semillas
    out = [f"<!-- generado por periodos.py analizar, semillas {S[0]}-{S[-1]} -->"]

    def m(E, c, s, p, mov="todos", a="todas", campo=1):
        v = A[(E, c, s)].get((p, mov, a))
        return None if v is None else v[campo] / v[0]

    def n_veh(E, c, s, p, mov="todos", a="todas"):
        v = A[(E, c, s)].get((p, mov, a))
        return 0 if v is None else v[0]

    # (1) retraso total medio por periodo (media de las semillas de la media por vehiculo)
    filas = []
    for E in ESCENARIOS:
        for c in CONTROLES:
            celdas = [E, NOMBRE[c]]
            for p in PERIODOS:
                tot = media([m(E, c, s, p) for s in S])
                tl = media([m(E, c, s, p, campo=2) for s in S])
                e = media([m(E, c, s, p, campo=3) for s in S])
                celdas += [f1(tot), f"{f1(tl)} + {f1(e)}"]
            filas.append(celdas)
    out.append("### (1) Retraso total medio por periodo (s/veh, media de las semillas)\n")
    out.append(tabla_md(["Esc.", "Control", "P1", "P1 timeLoss + espera", "P2", "P2 timeLoss + espera", "Hora",
                         "Hora timeLoss + espera"], filas))
    veh = {(E, p): sorted({n_veh(E, c, s, p) for c in CONTROLES for s in S}) for E in ESCENARIOS for p in PERIODOS}
    out.append("\nVehiculos por corrida (todos los controles y semillas): " +
               "; ".join(f"{E} P{p}: {veh[(E, p)]}" for E in ESCENARIOS for p in (1, 2)))

    # (2) cociente P2 / P1
    filas = []
    for E in ESCENARIOS:
        for c in CONTROLES:
            m1 = media([m(E, c, s, 1) for s in S])
            m2 = media([m(E, c, s, 2) for s in S])
            cs = [m(E, c, s, 2) / m(E, c, s, 1) for s in S]
            filas.append([E, NOMBRE[c], f1(m1), f1(m2), f"{m2 / m1:.2f}", f"{min(cs):.2f}-{max(cs):.2f}"])
    out.append("\n### (2) Cociente periodo 2 / periodo 1 del retraso total medio\n")
    out.append(tabla_md(["Esc.", "Control", "P1 (s/veh)", "P2 (s/veh)", "P2/P1 (de las medias)",
                         "P2/P1 por semilla (min-max)"], filas))

    # (3) diferencias pareadas frente al fijo
    filas = []
    for E in ESCENARIOS:
        for c in ("actual", "v2", "actuado"):
            for p in PERIODOS:
                d = [m(E, c, s, p) - m(E, "fijo", s, p) for s in S]
                filas.append([E, f"{NOMBRE[c]} - fijo", p, f"{statistics.mean(d):+.1f}", ic_txt(ic_t(d)),
                              ic_txt(ic_boot(d)), f"{p_wilcoxon(d):.3g}", f"{sum(1 for x in d if x < 0)}/{len(d)}",
                              f"{min(d):+.1f} / {max(d):+.1f}"])
    out.append("\n### (3) Diferencia pareada por semilla frente al fijo 25/10, retraso total medio (s/veh)\n")
    out.append(tabla_md(["Esc.", "Comparacion", "Periodo", "Media", "IC95 t", "IC95 bootstrap pareado",
                         "p Wilcoxon", "Semillas mejor que el fijo", "Min / max"], filas))

    # (4) de donde sale el exceso en el periodo 2 (s por vehiculo del nivel, como comp_aporte.csv)
    def aporte(E, c, p, mov, a, campo=1):
        """Cambio de s.veh del grupo frente al fijo / vehiculos de la hora del fijo, por semilla."""
        out_ = []
        for s in S:
            v, f = A[(E, c, s)].get((p, mov, a)), A[(E, "fijo", s)].get((p, mov, a))
            vv = v[campo] if v else 0.0
            ff = f[campo] if f else 0.0
            out_.append((vv - ff) / A[(E, "fijo", s)][("hora", "todos", "todas")][0])
        return out_

    for E in ("O", "D"):
        filas = []
        grupos = ([("todos", "todas", "periodo 2, todos")] +
                  [(mov, "todas", mov) for mov in CLASES] +
                  [("todos", a, f"entra por {a}") for a in ENTRADAS] +
                  [(mov, a, f"{mov} desde {a}") for mov in CLASES for a in ENTRADAS])
        grupos = [g for g in grupos if any(A[(E, "fijo", s)].get((2, g[0], g[1])) for s in S)]
        delta_hora = {c: media(aporte(E, c, "hora", "todos", "todas")) for c in ("actual", "v2", "actuado")}
        for mov, a, nombre in grupos:
            nv = media([n_veh(E, "fijo", s, 2, mov, a) for s in S])
            celdas = [nombre, f1(nv, 0), f1(media([m(E, "fijo", s, 2, mov, a) for s in S]))]
            for c in ("actual", "v2", "actuado"):
                tot = aporte(E, c, 2, mov, a)
                celdas += [f1(media([m(E, c, s, 2, mov, a) for s in S])),
                           f"{media(tot):+.2f} ({media(aporte(E, c, 2, mov, a, 2)):+.2f} / "
                           f"{media(aporte(E, c, 2, mov, a, 3)):+.2f})",
                           f"{media(tot) / delta_hora[c]:.2f}" if delta_hora[c] else ""]
            filas.append(celdas)
        out.append(f"\n### (4{'' if E == 'O' else 'b'}) {E}, periodo 2: de donde sale el cambio frente al fijo "
                   f"(s por vehiculo del nivel)\n")
        out.append("Aporte = (s.veh del grupo con el control - s.veh del grupo con el fijo) / vehiculos de la hora, "
                   "media de las semillas; entre parentesis, timeLoss / espera para entrar. Fraccion = aporte / "
                   "cambio de la hora. Cambio de la hora frente al fijo: " +
                   ", ".join(f"{NOMBRE[c]} {delta_hora[c]:+.2f}" for c in ("actual", "v2", "actuado")) + " s/veh.\n")
        cab = ["Grupo", "Veh. por corrida", "Fijo (s/veh)"]
        for c in ("actual", "v2", "actuado"):
            cab += [f"{NOMBRE[c]} (s/veh)", f"Aporte {NOMBRE[c]}", "Fraccion"]
        out.append(tabla_md(cab, filas))
        # IC del aporte de los grupos principales (solo O)
        if E == "O":
            filas = []
            for mov, a, nombre in grupos[:11]:
                celdas = [nombre]
                for c in ("actual", "v2"):
                    tot = aporte(E, c, 2, mov, a)
                    celdas += [f"{media(tot):+.2f} {ic_txt(ic_t(tot), 2)}"]
                filas.append(celdas)
            out.append("\nIC95 t del aporte en O, periodo 2 (s por vehiculo del nivel):\n")
            out.append(tabla_md(["Grupo", f"Aporte {NOMBRE['actual']}", f"Aporte {NOMBRE['v2']}"], filas))

    # (extra) cuando: retraso total medio por tramo de 5 min de la salida pedida
    filas = []
    for E in ESCENARIOS:
        for c in CONTROLES:
            celdas = [E, NOMBRE[c]]
            for b in range(12):
                vals = [perfil[(E, c, s)][b][1] / perfil[(E, c, s)][b][0] for s in S if b in perfil[(E, c, s)]]
                celdas.append(f1(media(vals), 0))
            filas.append(celdas)
    out.append("\n### (6) Cuando: retraso total medio segun el tramo de 5 min de la salida pedida (s/veh)\n")
    out.append(tabla_md(["Esc.", "Control"] + [f"{5 * b}-{5 * b + 5}" for b in range(12)], filas))

    # (extra) donde: detenidos medios por acceso (serie por segundo)
    filas = []
    for E in ESCENARIOS:
        for c in CONTROLES:
            for p in (1, 2):
                celdas = [E, NOMBRE[c], p] + [f1(media([series[(E, c, s)][(a, p)] for s in S])) for a in ACCESOS]
                celdas.append(f1(media([series[(E, c, s)]["lleno"][p] for s in S]), 0))
                if p == 2:
                    celdas.append(f"{min(series[(E, c, s)]['fin'] for s in S)}-"
                                  f"{max(series[(E, c, s)]['fin'] for s in S)}")
                else:
                    celdas.append("")
                filas.append(celdas)
    out.append("\n### (7) Donde: detenidos medios por acceso (cada segundo; P1 t < 1800 s, P2 1800-3600 s)\n")
    out.append(tabla_md(["Esc.", "Control", "Periodo"] + ACCESOS +
                        ["s con un enlace interno >= 34 detenidos", "Fin de la corrida (s)"], filas))

    # (extra) reparto del verde por cruce y periodo (fase por segundo; comportamiento.analizar_fases)
    filas = []
    for E in ESCENARIOS:
        for c in CONTROLES:
            for p in (1, 2):
                celdas = [E, NOMBRE[c], p]
                for tls in comp.SEMAFOROS:
                    av = [g for s in S for g in verdes[(E, c, s)][tls]["verdes_p"][(2, p)]]
                    tr = [g for s in S for g in verdes[(E, c, s)][tls]["verdes_p"][(0, p)]]
                    sv = [verdes[(E, c, s)][tls]["seg_verde_p"] for s in S]
                    frac = media([x[(2, p)] / max(1, x[(0, p)] + x[(2, p)]) for x in sv])
                    celdas += [f"{f1(comp.pct(av, 50), 0)} ({f1(comp.pct(av, 10), 0)}-{f1(comp.pct(av, 90), 0)})",
                               f"{f1(comp.pct(tr, 50), 0)} ({f1(comp.pct(tr, 10), 0)}-{f1(comp.pct(tr, 90), 0)})",
                               f"{frac:.3f}"]
                filas.append(celdas)
    out.append("\n### (8) Reparto del verde: mediana (p10-p90) de los verdes completos que empiezan en el periodo (s) "
               "y fraccion del verde para la avenida\n")
    out.append(tabla_md(["Esc.", "Control", "Periodo", "C1 avenida", "C1 transversal", "C1 frac. avenida",
                         "C2 avenida", "C2 transversal", "C2 frac. avenida"], filas))

    # (extra) cola para entrar por E_C2 (la entrada de la punta E->O del periodo 2)
    filas = []
    for E in ESCENARIOS:
        for c in CONTROLES:
            celdas = [E, NOMBRE[c]] + [f1(media([cola_ec2[(E, c, s)][t0] for s in S])) for t0 in TRAMOS_EC2]
            esp = [cola_ec2[(E, c, s)]["espera_p2"] for s in S]
            celdas += [f"{sum(1 for x in esp if x > 5)}/{len(esp)}", f"{min(esp):.1f}-{max(esp):.1f}"]
            filas.append(celdas)
    out.append("\n### (9) Vehiculos esperando para entrar por E_C2 (media de cada tramo de 5 min, muestreo cada 10 s; "
               "media de las semillas)\n")
    out.append(tabla_md(["Esc.", "Control"] + [f"{t0 // 60}-{t0 // 60 + 5}" for t0 in TRAMOS_EC2] +
                        ["Semillas con espera media en E_C2 (P2) > 5 s", "Espera media en E_C2, P2 (min-max de las "
                                                                         "semillas, s)"], filas))

    # (5) determinismo
    filas = []
    for E in ESCENARIOS:
        for c in CONTROLES:
            g = [x for x in control_filas if x["escenario"] == E and x["control"] == c]
            iguales = sum(1 for x in g if x["igual"] is True)
            dif = max(abs(float(x["retraso_total"]) - float(x["ref_retraso_total"])) for x in g
                      if x["ref_retraso_total"] != "")
            fases = next((x.get("fases_s1001_igual", "") for x in g if x["semilla"] == 1001), "")
            g5 = [x for x in g if x["semilla"] <= 1005]
            filas.append([E, NOMBRE[c], REFERENCIA[(E, c)], f"{sum(1 for x in g5 if x['igual'] is True)}/{len(g5)}",
                          f"{iguales}/{len(g)}", f"{dif:.2f}", fases,
                          f"{sum(1 for x in g if x['tripinfo_igual_metrica'])}/{len(g)}",
                          sorted({x["no_insertados"] for x in g}), sorted({x["vehiculos"] for x in g})])
    out.append("\n### (5) Determinismo: cada corrida contra la evaluacion de referencia con la misma semilla\n")
    out.append("Igual = retraso_total_prom, timeloss_prom, retraso_insercion_prom, cambios_fase y no_insertados "
               "iguales. Tripinfo = la media de timeLoss + departDelay del tripinfo guardado, redondeada a 2, es el "
               "retraso_total_prom de la corrida.\n")
    out.append(tabla_md(["Esc.", "Control", "Referencia (plan2/)", "Iguales 1001-1005", f"Iguales {S[0]}-{S[-1]}",
                         "Dif. max. retraso total", "Fases s1001 iguales", "Tripinfo = metrica",
                         "No insertados", "Vehiculos"], filas))
    s1001 = {(x["escenario"], x["control"]): x for x in control_filas if x["semilla"] == 1001}
    out.append("\nSemilla 1001, retraso total (esta corrida / referencia): " +
               "; ".join(f"{E} {c} {s1001[(E, c)]['retraso_total']} / {s1001[(E, c)]['ref_retraso_total']}"
                         for E in ESCENARIOS for c in CONTROLES if (E, c) in s1001))
    if avisos:
        out.append("\nAvisos:\n" + "\n".join("- " + a for a in avisos))
    else:
        out.append("\nEn todas las corridas el periodo por la salida pedida coincide con el prefijo del flujo (p1_/p2_).")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["correr", "uno", "analizar"])
    ap.add_argument("--datos", required=True, help="carpeta de las corridas (tripinfo, fases, series)")
    ap.add_argument("--salida", default="diag_corredor", help="carpeta de periodos.csv")
    ap.add_argument("--tablas", default=None, help="archivo de las tablas (por defecto <datos>/periodos_tablas.md)")
    ap.add_argument("--semillas", default="1001-1010")
    ap.add_argument("--procesos", type=int, default=4)
    ap.add_argument("--escenario", choices=list(ESCENARIOS))
    ap.add_argument("--control", choices=CONTROLES)
    args = ap.parse_args()
    args.datos = os.path.abspath(args.datos)
    if args.accion == "correr":
        correr(args)
    elif args.accion == "uno":
        correr_uno(args.escenario, args.control, comp.rango(args.semillas), args.datos)
    else:
        analizar(args)


if __name__ == "__main__":
    main()
