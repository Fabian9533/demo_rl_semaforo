"""
comportamiento.py - Que hace cada control en los cinco niveles del corredor (diagnostico del 25.10.2026).

Analisis posterior al veredicto (ver PRERREGISTRO.md): no cambia ningun veredicto. Mide, por nivel y
control, la duracion de los verdes, el ciclo, los cambios de fase por hora, el desfase y la sincronia de
los dos semaforos, las colas por acceso, la espera para entrar a la red por arista de entrada (departDelay)
y el retraso por movimiento.

Uso (con plan2/ como directorio de trabajo; conviene una copia de solo lectura del repositorio):
  python diag_corredor/comportamiento.py correr   --datos <carpeta> [--semillas 1001-1005] [--procesos 12]
  python diag_corredor/comportamiento.py analizar --datos <carpeta> [--salida diag_corredor]

correr: una evaluacion por nivel, control y semilla con el codigo de evaluar.py (mismas funciones, misma
  politica congelada), guardando el tripinfo completo (con departDelay), el archivo de estadisticas de
  SUMO (teletransportes, no insertados), las fases por segundo y las colas por acceso cada SEGUNDO
  (rl_corredor.PASO_SERIE = 1; en la evaluacion del plan es cada 60 s, que con ciclos fijos de 26-46 s
  muestrea siempre los mismos puntos del ciclo). Cambiar PASO_SERIE solo cambia cuantas filas se
  guardan; las metricas de cada corrida se escriben en metricas_<nivel>_<control>.csv y analizar las
  compara con las de la evaluacion del plan (determinismo).
analizar: lee esos archivos y escribe las tablas comp_*.csv y las figuras comp_*.png en --salida.

Niveles y controles (version evaluada de IPPO con mensajes de cada nivel; fijo = regla del 25.09;
fijo10 = fijo ajustado desde 10 s, del barrido del 27.09 con los mismos flujos; en P1 y P2 el fijo
vigente es el mismo programa que el del 25.09, por eso no se corre dos veces):
  905   dem_corredor_t905  ippo s4042, fijo, fijo10 (corredor_f050), trivial (ciclo minimo), actuado
  1358  dem_corredor_t1358 ippo s42,   fijo, fijo10 (corredor_f075), trivial, actuado
  1810  corredor (P1)      ippo s4042, fijo, trivial, actuado
  2715  dem_corredor_t2715 ippo s2042, fijo, fijo10 (corredor_f150), trivial, actuado
  3620  corredor_alta (P2) ippo s2042, fijo, trivial, actuado
"""
import os
import sys
import csv
import json
import time
import argparse
import statistics
import subprocess
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))      # carpeta con rl_ippo.py, evaluar.py...

# nivel -> control -> (escenario, "ref" o ruta .pt, CSV de la evaluacion del plan para comprobar)
NIVELES = {
    "905": {
        "ippo": ("dem_corredor_t905", "politica_dem_corredor_t905_vecinos_s4042.pt",
                 "demanda2/eval_dem_corredor_t905_ippo_vecinos_s4042.csv"),
        "fijo": ("dem_corredor_t905", "ref", "demanda2/eval_dem_corredor_t905_fijo.csv"),
        "fijo10": ("corredor_f050", "ref", "demanda/eval_corredor_f050_fijo.csv"),
        "trivial": ("dem_corredor_t905", "ref", "demanda2/eval_dem_corredor_t905_trivial.csv"),
        "actuado": ("dem_corredor_t905", "ref", "demanda2/eval_dem_corredor_t905_actuado.csv"),
    },
    "1358": {
        "ippo": ("dem_corredor_t1358", "politica_dem_corredor_t1358_vecinos_s42.pt",
                 "demanda2/eval_dem_corredor_t1358_ippo_vecinos_s42.csv"),
        "fijo": ("dem_corredor_t1358", "ref", "demanda2/eval_dem_corredor_t1358_fijo.csv"),
        "fijo10": ("corredor_f075", "ref", "demanda/eval_corredor_f075_fijo.csv"),
        "trivial": ("dem_corredor_t1358", "ref", "demanda2/eval_dem_corredor_t1358_trivial.csv"),
        "actuado": ("dem_corredor_t1358", "ref", "demanda2/eval_dem_corredor_t1358_actuado.csv"),
    },
    "1810": {
        "ippo": ("corredor", "politica_corredor_vecinos_s4042.pt", "parciales/eval_corredor_ippo_vecinos_s4042.csv"),
        "fijo": ("corredor", "ref", "parciales/eval_corredor_fijo.csv"),
        "trivial": ("corredor", "ref", "parciales/eval_corredor_trivial.csv"),
        "actuado": ("corredor", "ref", "parciales/eval_corredor_actuado.csv"),
    },
    "2715": {
        "ippo": ("dem_corredor_t2715", "politica_dem_corredor_t2715_vecinos_s2042.pt",
                 "demanda2/eval_dem_corredor_t2715_ippo_vecinos_s2042.csv"),
        "fijo": ("dem_corredor_t2715", "ref", "demanda2/eval_dem_corredor_t2715_fijo.csv"),
        "fijo10": ("corredor_f150", "ref", "demanda/eval_corredor_f150_fijo.csv"),
        "trivial": ("dem_corredor_t2715", "ref", "demanda2/eval_dem_corredor_t2715_trivial.csv"),
        "actuado": ("dem_corredor_t2715", "ref", "demanda2/eval_dem_corredor_t2715_actuado.csv"),
    },
    "3620": {
        "ippo": ("corredor_alta", "politica_corredor_alta_vecinos_s2042.pt",
                 "parciales/eval_corredor_alta_ippo_vecinos_s2042.csv"),
        "fijo": ("corredor_alta", "ref", "parciales/eval_corredor_alta_fijo.csv"),
        "trivial": ("corredor_alta", "ref", "parciales/eval_corredor_alta_trivial.csv"),
        "actuado": ("corredor_alta", "ref", "parciales/eval_corredor_alta_actuado.csv"),
    },
}
NOMBRE_NIVEL = {"905": "905", "1358": "1358", "1810": "1810 (P1)", "2715": "2715", "3620": "3620 (P2)"}
CONTROLES = ["ippo", "fijo", "fijo10", "trivial", "actuado"]
SEMAFOROS = ["semaforo_C1", "semaforo_C2"]
# En todos los programas del corredor la fase 0 es la transversal (N-S) y la 2 la avenida (E-O);
# las fases 1 y 3 son los ambares de 3 s (estado de corredor.add.xml y enlaces de corredor.net.xml).
FASE_NOMBRE = {0: "transversal", 2: "avenida"}
ENTRADAS = ["W_C1", "E_C2", "N1_C1", "S1_C1", "N2_C2", "S2_C2"]
ACCESOS = ["W_C1", "C2_C1", "N1_C1", "S1_C1", "C1_C2", "E_C2", "N2_C2", "S2_C2"]
# Viaje libre entre las lineas de detencion de C1 y C2 (300 m a 13.89 m/s): se usa para la banda verde
T_VIAJE = 22
FIN = 3600
PERIODO = 1800        # la punta va de oeste a este en 0-1800 s y de este a oeste en 1800-3600 s


# ---------------- correr ----------------
def rango(texto):
    if "-" in texto:
        a, b = texto.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in texto.split(",")]


def correr_uno(nivel, control, semillas, datos):
    """Corre un control de un nivel en las semillas dadas, con las funciones de evaluar.py."""
    sys.path.insert(0, RAIZ)
    import evaluar
    import rl_corredor
    rl_corredor.PASO_SERIE = 1          # colas por acceso cada segundo (rl_ippo lo lee de aqui tambien)
    os.makedirs(datos, exist_ok=True)
    esc, tipo, _ = NIVELES[nivel][control]
    if tipo == "ref":
        _, _, _, correr = evaluar.brazo_referencia(esc, control if control != "fijo10" else "fijo")
    else:
        _, _, _, correr = evaluar.brazo_profundo(esc, tipo, 0, 0.0)
    salida = os.path.join(datos, f"metricas_{nivel}_{control}.csv")
    filas = []
    for s in semillas:
        t0 = time.time()
        base = os.path.join(datos, f"{nivel}_{control}_s{s}")
        res = correr(s, base + "_trip.xml", os.path.join(datos, f"serie_{nivel}_{control}_s{s}.csv"))
        filas.append({"nivel": nivel, "control": control, "escenario": esc, "semilla": s,
                      **{m: res.get(m, "") for m in evaluar.METRICAS}})
        print(f"{nivel} {control} s{s}: total {res['retraso_total_prom']}  timeLoss {res['timeloss_prom']}"
              f"  {time.time() - t0:.0f}s", flush=True)
    with open(salida, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)


def correr(args):
    os.makedirs(args.datos, exist_ok=True)
    trabajos = [(n, c) for n in NIVELES for c in CONTROLES if c in NIVELES[n]]
    pendientes = [t for t in trabajos if not os.path.exists(os.path.join(args.datos, f"metricas_{t[0]}_{t[1]}.csv"))]
    # los mas largos primero (IPPO y demanda alta)
    pendientes.sort(key=lambda t: (t[1] != "ippo", -int(t[0])))
    activos = []
    while pendientes or activos:
        while pendientes and len(activos) < args.procesos:
            n, c = pendientes.pop(0)
            log = open(os.path.join(args.datos, f"log_{n}_{c}.txt"), "w")
            p = subprocess.Popen([sys.executable, os.path.abspath(__file__), "uno", "--nivel", n, "--control", c,
                                  "--semillas", args.semillas, "--datos", args.datos],
                                 stdout=log, stderr=subprocess.STDOUT)
            activos.append((p, log, n, c))
        time.sleep(2)
        for item in activos[:]:
            if item[0].poll() is not None:
                item[1].close()
                print(f"termino {item[2]} {item[3]} (codigo {item[0].returncode})", flush=True)
                activos.remove(item)


# ---------------- analizar: utilidades ----------------
def pct(valores, q):
    """Percentil q (0-100) con interpolacion lineal; None si no hay valores."""
    v = sorted(valores)
    if not v:
        return None
    k = (len(v) - 1) * q / 100
    i = int(k)
    j = min(i + 1, len(v) - 1)
    return v[i] + (v[j] - v[i]) * (k - i)


def media(valores):
    return statistics.mean(valores) if valores else None


def r(x, d=2):
    return "" if x is None else round(x, d)


def leer_csv(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def tramos(fases):
    """fases: lista de (t, fase) por segundo. Devuelve [(fase, inicio, fin)] con fin exclusivo; el
    primero y el ultimo pueden estar cortados por el borde de la hora (se marcan con completo=False)."""
    out = []
    inicio, actual = fases[0][0], fases[0][1]
    for t, f in fases[1:]:
        if f != actual:
            out.append((actual, inicio, t))
            inicio, actual = t, f
    out.append((actual, inicio, fases[-1][0] + 1))
    return [(f, a, b, k not in (0, len(out) - 1)) for k, (f, a, b) in enumerate(out)]


def leer_fases(ruta):
    filas = leer_csv(ruta)
    return {tls: [(int(x["t"]), int(x[tls])) for x in filas if int(x["t"]) <= FIN] for tls in SEMAFOROS}


def leer_flujos(rou):
    """id del flow -> (desde, hasta)."""
    raiz = ET.parse(rou).getroot()
    return {f.get("id"): (f.get("from"), f.get("to")) for f in raiz.iter("flow")}


def movimiento(desde, hasta):
    if (desde, hasta) in (("W_C1", "C2_E"), ("E_C2", "C1_W")):
        return "avenida"
    if desde[:2] in ("N1", "S1", "N2", "S2") and hasta[-2:] in ("N1", "S1", "N2", "S2") and desde[1] == hasta[-1]:
        return "transversal"
    return "giros"


def cfg_rutas(esc):
    raiz = ET.parse(f"{esc}.sumocfg").getroot()
    return raiz.find("input/route-files").get("value")


# ---------------- analizar ----------------
def analizar_fases(fases):
    """Por semaforo: duraciones de los verdes completos por fase, inicios de cada fase y verde por
    periodo. fases: {tls: [(t, fase)]}"""
    out = {}
    for tls, serie in fases.items():
        tr = tramos(serie)
        d = {"verdes": {0: [], 2: []}, "verdes_p": {(0, 1): [], (0, 2): [], (2, 1): [], (2, 2): []},
             "inicios": {0: [], 2: []}, "seg_verde": {0: 0, 2: 0},
             "seg_verde_p": {(0, 1): 0, (0, 2): 0, (2, 1): 0, (2, 2): 0}, "tramos": tr}
        for f, a, b, completo in tr:
            if f in (0, 2):
                d["seg_verde"][f] += b - a
                d["seg_verde_p"][(f, 1)] += max(0, min(b, PERIODO) - a)
                d["seg_verde_p"][(f, 2)] += max(0, b - max(a, PERIODO))
                if a > serie[0][0]:
                    d["inicios"][f].append(a)
                if completo:
                    d["verdes"][f].append(b - a)
                    d["verdes_p"][(f, 1 if a < PERIODO else 2)].append(b - a)
        out[tls] = d
    return out


def banda(fases, t_viaje):
    """Fraccion de los segundos de verde de avenida aguas arriba cuyo vehiculo libre (t + t_viaje)
    encuentra verde de avenida en el cruce siguiente: W->E (C1 -> C2) y E->W (C2 -> C1)."""
    f1 = dict(fases["semaforo_C1"])
    f2 = dict(fases["semaforo_C2"])
    out = {}
    for nombre, arriba, abajo in (("WE", f1, f2), ("EW", f2, f1)):
        for p in (1, 2):
            seg = [t for t, f in arriba.items() if f == 2 and (p == 1) == (t < PERIODO) and t + t_viaje <= FIN]
            ok = sum(1 for t in seg if abajo.get(t + t_viaje) == 2)
            out[(nombre, p)] = ok / len(seg) if seg else None
    simult = sum(1 for t in f1 if f1[t] == 2 and f2.get(t) == 2)
    out["simult"] = simult / max(1, sum(1 for t in f1 if f1[t] == 2))
    return out


def desfases(ini1, ini2, ciclo_med):
    """Por cada inicio de verde de avenida en C1, segundos hasta el siguiente inicio en C2 (W->E) y al
    reves (E->W), limitados a un ciclo."""
    def sig(a, lista):
        cand = [b - a for b in lista if b >= a]
        return min(cand) if cand else None
    we = [(a, x) for a, x in ((a, sig(a, ini2)) for a in ini1) if x is not None and x <= ciclo_med * 1.5]
    ew = [(a, x) for a, x in ((a, sig(a, ini1)) for a in ini2) if x is not None and x <= ciclo_med * 1.5]
    return we, ew


APROX_TLS = {"semaforo_C1": {"avenida": ["W_C1", "C2_C1"], "transversal": ["N1_C1", "S1_C1"]},
             "semaforo_C2": {"avenida": ["C1_C2", "E_C2"], "transversal": ["N2_C2", "S2_C2"]}}
BINS = [(0, 0, "0"), (1, 1, "1"), (2, 2, "2"), (3, 4, "3-4"), (5, 9999, "5+")]


def decisiones(af, serie, paso=5, minimo=10):
    """Huella de la politica IPPO: en cada instante de decision de un verde (a los 10, 15, 20... s de
    empezar; reloj de rl_corredor), si cambia o extiende, segun los detenidos en la fase en rojo y en
    la propia un segundo antes. Devuelve [(semaforo, fase en verde, cola roja, cola propia, cambia)]."""
    cola = {int(x["t"]): x for x in serie}
    out = []
    for tls, d in af.items():
        for f, a, b, completo in d["tramos"]:
            if f not in (0, 2) or not completo:
                continue
            verde = FASE_NOMBRE[f]
            rojo = "transversal" if verde == "avenida" else "avenida"
            k = minimo
            while a + k <= b:
                fila = cola.get(a + k - 1)
                if fila is None:
                    break
                c_rojo = sum(int(fila[e]) for e in APROX_TLS[tls][rojo])
                c_propia = sum(int(fila[e]) for e in APROX_TLS[tls][verde])
                out.append((tls[-2:], verde, c_rojo, c_propia, a + k == b, 1 if a < PERIODO else 2))
                k += paso
    return out


def leer_trip(ruta, flujos):
    filas = []
    for v in ET.parse(ruta).getroot().findall("tripinfo"):
        flujo = v.get("id").rsplit(".", 1)[0]
        desde, hasta = flujos[flujo]
        filas.append({"flujo": flujo, "desde": desde, "mov": movimiento(desde, hasta),
                      "periodo": 1 if flujo.startswith("p1_") else 2,
                      "depart": float(v.get("depart")), "delay": float(v.get("departDelay", 0)),
                      "timeloss": float(v.get("timeLoss")), "paradas": int(v.get("waitingCount", 0)),
                      "terminado": float(v.get("arrival", -1)) >= 0})
    return filas


def leer_stats(ruta):
    raiz = ET.parse(ruta).getroot()
    veh = raiz.find("vehicles")
    tp = raiz.find("teleports")
    return {"no_insertados": int(veh.get("waiting", 0)) if veh is not None else "",
            "teleports": int(tp.get("total", 0)) if tp is not None else 0}


def esperando(viajes, desde, paso=60):
    """Vehiculos esperando entrar por la arista 'desde' cada 'paso' s (planeado <= t < salida real)."""
    v = [(x["depart"] - x["delay"], x["depart"]) for x in viajes if x["desde"] == desde]
    fin = max([FIN] + [int(x["depart"]) for x in viajes])      # tambien despues de la hora
    return [(t, sum(1 for a, b in v if a <= t < b)) for t in range(0, fin + paso, paso)]


def guardar(ruta, filas):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print("Escrito", ruta)


def analizar(args):
    datos, salida = args.datos, args.salida
    os.makedirs(salida, exist_ok=True)
    semillas = rango(args.semillas)
    t_fases, t_ciclo, t_sinc, t_colas, t_entrada, t_mov, t_control, t_espera_serie = [], [], [], [], [], [], [], []
    t_decis, t_entrada_sem = [], []
    for nivel, controles in NIVELES.items():
        for control in CONTROLES:
            if control not in controles:
                continue
            esc, _, eval_plan = controles[control]
            flujos = leer_flujos(cfg_rutas(esc))
            met = {int(x["semilla"]): x for x in leer_csv(os.path.join(datos, f"metricas_{nivel}_{control}.csv"))}
            plan = {int(x["semilla"]): x for x in leer_csv(eval_plan)} if os.path.exists(eval_plan) else {}
            verdes = {(tls, f): [] for tls in SEMAFOROS for f in (0, 2)}
            verdes_p = {(tls, f, p): [] for tls in SEMAFOROS for f in (0, 2) for p in (1, 2)}
            ciclos = {tls: [] for tls in SEMAFOROS}
            cambios = {tls: [] for tls in SEMAFOROS}
            reparto = {tls: [] for tls in SEMAFOROS}
            reparto_p = {(tls, p): [] for tls in SEMAFOROS for p in (1, 2)}
            bandas, des_we, des_ew, decis = [], [], [], []
            colas = {a: {1: [], 2: []} for a in ACCESOS}
            colas_max = {a: [] for a in ACCESOS}
            viajes_todos = []
            for s in semillas:
                fases = leer_fases(os.path.join(datos, f"fases_{nivel}_{control}_s{s}.csv"))
                af = analizar_fases(fases)
                for tls in SEMAFOROS:
                    for f in (0, 2):
                        verdes[(tls, f)] += af[tls]["verdes"][f]
                        for p in (1, 2):
                            verdes_p[(tls, f, p)] += af[tls]["verdes_p"][(f, p)]
                    ini = af[tls]["inicios"][0]
                    ciclos[tls] += [b - a for a, b in zip(ini, ini[1:])]
                    cambios[tls].append(len(af[tls]["inicios"][0]) + len(af[tls]["inicios"][2]))
                    sv = af[tls]["seg_verde"]
                    reparto[tls].append(sv[2] / max(1, sv[0] + sv[2]))
                    for p in (1, 2):
                        svp = af[tls]["seg_verde_p"]
                        reparto_p[(tls, p)].append(svp[(2, p)] / max(1, svp[(0, p)] + svp[(2, p)]))
                bandas.append(banda(fases, T_VIAJE))
                ciclo_med = pct(ciclos["semaforo_C1"], 50) or 60
                we, ew = desfases(af["semaforo_C1"]["inicios"][2], af["semaforo_C2"]["inicios"][2], ciclo_med)
                des_we += we
                des_ew += ew
                serie = leer_csv(os.path.join(datos, f"serie_{nivel}_{control}_s{s}.csv"))
                if control == "ippo":
                    decis += decisiones(af, serie)
                fases_igual = ""
                if s == 1001:
                    # el archivo de fases que dejo la evaluacion del plan (primera semilla) para este brazo
                    brazo_plan = os.path.basename(eval_plan)[len(f"eval_{esc}_"):-len(".csv")]
                    ruta_plan = f"fases_{esc}_{brazo_plan}_s1001.csv"
                    if os.path.exists(ruta_plan):
                        with open(ruta_plan, encoding="utf-8") as fa:
                            texto_plan = fa.read()
                        with open(os.path.join(datos, f"fases_{nivel}_{control}_s{s}.csv"), encoding="utf-8") as fb:
                            fases_igual = texto_plan == fb.read()
                for a in ACCESOS:
                    vals = [(int(x["t"]), int(x[a])) for x in serie if int(x["t"]) <= FIN]
                    colas[a][1].append(media([v for t, v in vals if t < PERIODO]))
                    colas[a][2].append(media([v for t, v in vals if t >= PERIODO]))
                    colas_max[a].append(max(v for t, v in vals))
                viajes = leer_trip(os.path.join(datos, f"{nivel}_{control}_s{s}_trip.xml"), flujos)
                for x in viajes:
                    x["semilla"] = s
                viajes_todos += viajes
                for a in ENTRADAS:
                    for p in (1, 2):
                        d = [x["delay"] for x in viajes if x["desde"] == a and x["periodo"] == p]
                        t_entrada_sem.append({"nivel": nivel, "control": control, "semilla": s, "arista": a,
                                              "periodo": p, "vehiculos": len(d), "espera_media": r(media(d), 2)})
                st = leer_stats(os.path.join(datos, f"{nivel}_{control}_s{s}_trip_stats.xml"))
                m, pl = met[s], plan.get(s)
                t_control.append({
                    "nivel": nivel, "control": control, "semilla": s,
                    "retraso_total": m["retraso_total_prom"], "timeloss": m["timeloss_prom"],
                    "espera_entrar": m["retraso_insercion_prom"], "cambios_fase": m["cambios_fase"],
                    "plan_retraso_total": pl["retraso_total_prom"] if pl else "",
                    "plan_timeloss": pl["timeloss_prom"] if pl else "",
                    "plan_cambios_fase": pl["cambios_fase"] if pl else "",
                    "igual_al_plan": (pl is not None and all(float(m[k]) == float(pl[k]) for k in
                                      ("retraso_total_prom", "timeloss_prom", "retraso_insercion_prom",
                                       "cambios_fase"))) if pl else "",
                    "fases_s1001_igual_al_plan": fases_igual,
                    "no_insertados": st["no_insertados"], "teleports": st["teleports"]})
                if control in ("ippo", "fijo", "fijo10"):
                    for a in ENTRADAS:
                        for t, n in esperando(viajes, a):
                            t_espera_serie.append({"nivel": nivel, "control": control, "semilla": s, "arista": a,
                                                   "t": t, "esperando": n})
            n_s = len(semillas)
            # verdes
            for (tls, f), v in verdes.items():
                fila = {"nivel": nivel, "control": control, "semaforo": tls[-2:], "fase": FASE_NOMBRE[f],
                        "n_verdes": len(v), "media": r(media(v), 1), "p10": r(pct(v, 10), 1),
                        "p25": r(pct(v, 25), 1), "mediana": r(pct(v, 50), 1), "p75": r(pct(v, 75), 1),
                        "p90": r(pct(v, 90), 1), "max": max(v) if v else "",
                        "frac_10s": r(sum(1 for x in v if x <= 10) / len(v), 3) if v else "",
                        "frac_ge20s": r(sum(1 for x in v if x >= 20) / len(v), 3) if v else ""}
                for p in (1, 2):
                    vp = verdes_p[(tls, f, p)]
                    fila[f"media_p{p}"] = r(media(vp), 1)
                    fila[f"mediana_p{p}"] = r(pct(vp, 50), 1)
                t_fases.append(fila)
            # ciclo, cambios y reparto
            for tls in SEMAFOROS:
                c = ciclos[tls]
                t_ciclo.append({"nivel": nivel, "control": control, "semaforo": tls[-2:],
                                "ciclo_media": r(media(c), 1), "ciclo_p25": r(pct(c, 25), 1),
                                "ciclo_mediana": r(pct(c, 50), 1), "ciclo_p75": r(pct(c, 75), 1),
                                "cambios_hora": r(media(cambios[tls]), 1),
                                "frac_verde_avenida": r(media(reparto[tls]), 3),
                                "frac_verde_avenida_p1": r(media(reparto_p[(tls, 1)]), 3),
                                "frac_verde_avenida_p2": r(media(reparto_p[(tls, 2)]), 3)})
            # huella de decision de IPPO
            for tls in ("C1", "C2"):
                for verde in ("avenida", "transversal"):
                    for p in (1, 2, "hora"):
                        for lo, hi, etiqueta in BINS:
                            g = [x for x in decis if x[0] == tls and x[1] == verde and lo <= x[2] <= hi
                                 and (p == "hora" or x[5] == p)]
                            if not g:
                                continue
                            t_decis.append({"nivel": nivel, "control": control, "semaforo": tls, "fase_en_verde": verde,
                                            "periodo": p, "detenidos_en_rojo": etiqueta, "decisiones": len(g),
                                            "frac_cambia": r(sum(1 for x in g if x[4]) / len(g), 3),
                                            "detenidos_propios_media": r(media([x[3] for x in g]), 2)})
            # sincronia
            def mb(clave):
                vals = [b[clave] for b in bandas if b.get(clave) is not None]
                return r(media(vals), 3)
            av = [x for x in viajes_todos if x["mov"] == "avenida"]
            dwe = [x for _, x in des_we]
            dew = [x for _, x in des_ew]
            fila = {"nivel": nivel, "control": control,
                    "desfase_WE_mediana": r(pct(dwe, 50), 1), "desfase_WE_p25": r(pct(dwe, 25), 1),
                    "desfase_WE_p75": r(pct(dwe, 75), 1),
                    "desfase_EW_mediana": r(pct(dew, 50), 1), "desfase_EW_p25": r(pct(dew, 25), 1),
                    "desfase_EW_p75": r(pct(dew, 75), 1),
                    "banda_WE_p1": mb(("WE", 1)), "banda_WE_p2": mb(("WE", 2)),
                    "banda_EW_p1": mb(("EW", 1)), "banda_EW_p2": mb(("EW", 2)),
                    "simultaneo_avenida": mb("simult")}
            for p in (1, 2):
                # desfase W->E segun el inicio en C1 y E->W segun el inicio en C2, dentro del periodo
                vwe = [x for a, x in des_we if (a < PERIODO) == (p == 1)]
                vew = [x for a, x in des_ew if (a < PERIODO) == (p == 1)]
                fila[f"desfase_WE_mediana_p{p}"] = r(pct(vwe, 50), 1)
                fila[f"desfase_EW_mediana_p{p}"] = r(pct(vew, 50), 1)
            for nombre, flujo in (("punta_p1_WE", "p1_W_E"), ("punta_p2_EW", "p2_E_W")):
                g = [x for x in av if x["flujo"] == flujo]
                fila[f"paradas_{nombre}"] = r(media([x["paradas"] for x in g]), 2)
                fila[f"frac_sin_parar_{nombre}"] = r(sum(1 for x in g if x["paradas"] == 0) / max(1, len(g)), 3)
                fila[f"timeloss_{nombre}"] = r(media([x["timeloss"] for x in g]), 2)
            t_sinc.append(fila)
            # colas por acceso
            for a in ACCESOS:
                t_colas.append({"nivel": nivel, "control": control, "acceso": a,
                                "semaforo": "C1" if a.endswith("C1") else "C2",
                                "cola_media_p1": r(media(colas[a][1]), 2), "cola_media_p2": r(media(colas[a][2]), 2),
                                "cola_media_hora": r(media([(x + y) / 2 for x, y in zip(colas[a][1], colas[a][2])]), 2),
                                "cola_max": r(media(colas_max[a]), 1)})
            # espera para entrar por arista de entrada
            tot = sum(x["delay"] for x in viajes_todos)
            for a in ENTRADAS:
                g = [x for x in viajes_todos if x["desde"] == a]
                d = [x["delay"] for x in g]
                fila = {"nivel": nivel, "control": control, "arista": a, "vehiculos_por_semilla": len(g) / n_s,
                        "espera_media": r(media(d), 2), "espera_p90": r(pct(d, 90), 1), "espera_max": r(max(d), 1),
                        "frac_espera_gt5s": r(sum(1 for x in d if x > 5) / max(1, len(d)), 3),
                        "veh_s_por_semilla": r(sum(d) / n_s, 0), "frac_del_total": r(sum(d) / tot, 3) if tot else ""}
                for p in (1, 2):
                    dp = [x["delay"] for x in g if x["periodo"] == p]
                    fila[f"espera_media_p{p}"] = r(media(dp), 2)
                t_entrada.append(fila)
            # retraso por movimiento
            for mov in ("avenida", "transversal", "giros", "todos"):
                for p in (1, 2, "hora"):
                    g = [x for x in viajes_todos if (mov == "todos" or x["mov"] == mov) and (p == "hora" or x["periodo"] == p)]
                    if not g:
                        continue
                    t_mov.append({"nivel": nivel, "control": control, "movimiento": mov, "periodo": p,
                                  "vehiculos_por_semilla": r(len(g) / n_s, 1),
                                  "timeloss": r(media([x["timeloss"] for x in g]), 2),
                                  "espera_entrar": r(media([x["delay"] for x in g]), 2),
                                  "retraso_total": r(media([x["timeloss"] + x["delay"] for x in g]), 2),
                                  "paradas": r(media([x["paradas"] for x in g]), 2)})
            print(f"analizado {nivel} {control}", flush=True)
    guardar(os.path.join(salida, "comp_verdes.csv"), t_fases)
    guardar(os.path.join(salida, "comp_ciclo.csv"), t_ciclo)
    guardar(os.path.join(salida, "comp_sincronia.csv"), t_sinc)
    guardar(os.path.join(salida, "comp_colas.csv"), t_colas)
    guardar(os.path.join(salida, "comp_entrada.csv"), t_entrada)
    guardar(os.path.join(salida, "comp_movimientos.csv"), t_mov)
    guardar(os.path.join(salida, "comp_control.csv"), t_control)
    guardar(os.path.join(salida, "comp_espera_serie.csv"), t_espera_serie)
    guardar(os.path.join(salida, "comp_decisiones.csv"), t_decis)
    guardar(os.path.join(salida, "comp_entrada_semilla.csv"), t_entrada_sem)
    guardar(os.path.join(salida, "comp_aporte.csv"), aportes(t_mov))


def aportes(t_mov):
    """Cambio del retraso total de IPPO frente al fijo ajustado desde 10 s (fijo10; en P1 y P2 el fijo
    vigente), repartido por movimiento y periodo: s.veh por semilla y s por vehiculo del nivel."""
    out = []
    idx = {(x["nivel"], x["control"], x["movimiento"], str(x["periodo"])): x for x in t_mov}
    for nivel in NIVELES:
        ref = "fijo10" if "fijo10" in NIVELES[nivel] else "fijo"
        n_tot = idx[(nivel, ref, "todos", "hora")]["vehiculos_por_semilla"]
        delta_tot = None
        for mov in ("avenida", "transversal", "giros", "todos"):
            for p in ("1", "2", "hora"):
                a, b = idx.get((nivel, "ippo", mov, p)), idx.get((nivel, ref, mov, p))
                if a is None or b is None:
                    continue
                d_tl = a["vehiculos_por_semilla"] * a["timeloss"] - b["vehiculos_por_semilla"] * b["timeloss"]
                d_ins = a["vehiculos_por_semilla"] * a["espera_entrar"] - b["vehiculos_por_semilla"] * b["espera_entrar"]
                if mov == "todos" and p == "hora":
                    delta_tot = d_tl + d_ins
                out.append({"nivel": nivel, "referencia": ref, "movimiento": mov, "periodo": p,
                            "vehiculos_por_semilla": b["vehiculos_por_semilla"],
                            "ippo_retraso_total": a["retraso_total"], "ref_retraso_total": b["retraso_total"],
                            "ippo_timeloss": a["timeloss"], "ref_timeloss": b["timeloss"],
                            "ippo_espera_entrar": a["espera_entrar"], "ref_espera_entrar": b["espera_entrar"],
                            "delta_timeloss_vehs": r(d_tl, 0), "delta_espera_entrar_vehs": r(d_ins, 0),
                            "delta_total_s_por_veh_del_nivel": r((d_tl + d_ins) / n_tot, 2),
                            "frac_del_cambio_total": ""})
        for fila in out:
            if fila["nivel"] == nivel and delta_tot:
                fila["frac_del_cambio_total"] = r((fila["delta_timeloss_vehs"] + fila["delta_espera_entrar_vehs"])
                                                  / delta_tot, 3)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["correr", "uno", "analizar", "figuras"])
    ap.add_argument("--datos", required=True, help="carpeta de las corridas (tripinfo, fases, series)")
    ap.add_argument("--salida", default="diag_corredor", help="carpeta de las tablas y figuras")
    ap.add_argument("--semillas", default="1001-1005")
    ap.add_argument("--procesos", type=int, default=12)
    ap.add_argument("--nivel")
    ap.add_argument("--control")
    args = ap.parse_args()
    args.datos = os.path.abspath(args.datos)
    if args.accion == "correr":
        correr(args)
    elif args.accion == "uno":
        os.chdir(os.path.join(RAIZ, "plan2"))
        correr_uno(args.nivel, args.control, rango(args.semillas), args.datos)
    elif args.accion == "analizar":
        analizar(args)
    else:
        figuras(args)


AZUL, NARANJA, TINTA, TINTA2, REJILLA, FONDO = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def estilo(ax):
    ax.set_facecolor(FONDO)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(TINTA2)
    ax.tick_params(colors=TINTA2, labelsize=8)
    ax.grid(axis="y", color=REJILLA, linewidth=0.8)
    ax.set_axisbelow(True)


def figuras(args):
    """comp_verdes.png (verdes y ciclo de IPPO frente al fijo ajustado) y comp_espera_entrar.png
    (vehiculos esperando entrar por E_C2 y W_C1, semilla 1001), desde las tablas de --salida."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    salida = args.salida
    verdes = leer_csv(os.path.join(salida, "comp_verdes.csv"))
    ciclo = leer_csv(os.path.join(salida, "comp_ciclo.csv"))
    niveles = list(NIVELES)
    ref = {n: ("fijo10" if "fijo10" in NIVELES[n] else "fijo") for n in niveles}

    fig, ejes = plt.subplots(1, 3, figsize=(11, 3.6), facecolor=FONDO)
    paneles = [("Verde de avenida (s)", verdes, "avenida"), ("Verde transversal (s)", verdes, "transversal"),
               ("Ciclo (s)", ciclo, None)]
    for ax, (titulo, tabla, fase) in zip(ejes, paneles):
        estilo(ax)
        for i, n in enumerate(niveles):
            for k, sem in enumerate(("C1", "C2")):
                def fila(control):
                    return next(x for x in tabla if x["nivel"] == n and x["control"] == control and x["semaforo"] == sem
                                and (fase is None or x["fase"] == fase))
                a = fila("ippo")
                if fase is None:
                    med, lo, hi = float(a["ciclo_mediana"]), float(a["ciclo_p25"]), float(a["ciclo_p75"])
                    val_ref = float(fila(ref[n])["ciclo_mediana"])
                else:
                    med, lo, hi = float(a["mediana"]), float(a["p10"]), float(a["p90"])
                    val_ref = float(fila(ref[n])["mediana"])
                x = i + (k - 0.5) * 0.28
                ax.plot([x, x], [lo, hi], color=AZUL, linewidth=2, solid_capstyle="round")
                ax.plot(x, med, "o", color=AZUL, markersize=7, markerfacecolor=AZUL if sem == "C1" else FONDO,
                        markeredgewidth=2, label=f"IPPO {sem}" if i == 0 else None, zorder=3)
                ax.plot(x, val_ref, "s", color=NARANJA, markersize=6, label="Fijo ajustado" if i == 0 and k == 0 else None,
                        zorder=4, markeredgecolor=FONDO, markeredgewidth=1)
        ax.set_xticks(range(len(niveles)))
        ax.set_xticklabels([NOMBRE_NIVEL[n] for n in niveles], color=TINTA2)
        ax.set_xlabel("Demanda (veh/h)", color=TINTA2, fontsize=8)
        ax.set_title(titulo, color=TINTA, fontsize=10, loc="left")
        ax.set_ylim(bottom=0)
    manijas, etiquetas = ejes[0].get_legend_handles_labels()
    orden = [etiquetas.index(e) for e in ("IPPO C1", "IPPO C2", "Fijo ajustado")]
    ejes[0].legend([manijas[k] for k in orden], [etiquetas[k] for k in orden], frameon=False, fontsize=8,
                   labelcolor=TINTA2, loc="upper left")
    fig.text(0.01, 0.01, "IPPO: mediana y p10-p90 de los verdes (ciclo: p25-p75), semillas 1001-1005. Fijo ajustado: "
             "desde 10 s (905, 1358, 2715) o vigente (P1, P2).", fontsize=7, color=TINTA2)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    ruta = os.path.join(salida, "comp_verdes.png")
    fig.savefig(ruta, dpi=160, facecolor=FONDO)
    print("Escrito", ruta)

    serie = leer_csv(os.path.join(salida, "comp_espera_serie.csv"))
    fig, ejes = plt.subplots(1, 3, figsize=(11, 3.4), facecolor=FONDO, sharey=False)
    for ax, (n, arista) in zip(ejes, (("2715", "E_C2"), ("3620", "E_C2"), ("3620", "W_C1"))):
        estilo(ax)
        for control, color, nombre in (("ippo", AZUL, "IPPO"), (ref[n], NARANJA, "Fijo ajustado")):
            # promedio sobre las semillas (una semilla sin dato en un minuto cuenta 0: ya entraron todos)
            suma, sems = {}, set()
            for x in serie:
                if x["nivel"] == n and x["control"] == control and x["arista"] == arista:
                    t = int(x["t"])
                    suma[t] = suma.get(t, 0) + int(x["esperando"])
                    sems.add(x["semilla"])
            ts = sorted(suma)
            ax.plot([t / 60 for t in ts], [suma[t] / len(sems) for t in ts], color=color, linewidth=2, label=nombre)
        ax.axvline(30, color=TINTA2, linewidth=0.8, linestyle=":")
        ax.set_title(f"{NOMBRE_NIVEL[n]} veh/h, entrada {arista}", color=TINTA, fontsize=10, loc="left")
        ax.set_xlabel("Minuto de la hora (punta O-E hasta el 30, luego E-O)", color=TINTA2, fontsize=8)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
    ejes[0].set_ylabel("Vehiculos esperando entrar", color=TINTA2, fontsize=8)
    ejes[0].legend(frameon=False, fontsize=8, labelcolor=TINTA2, loc="upper left")
    fig.text(0.01, 0.01, "Promedio de las semillas 1001-1005; cada 60 s, vehiculos con salida programada ya cumplida "
             "que aun no entran (depart - departDelay <= t < depart).", fontsize=7, color=TINTA2)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    ruta = os.path.join(salida, "comp_espera_entrar.png")
    fig.savefig(ruta, dpi=160, facecolor=FONDO)
    print("Escrito", ruta)


if __name__ == "__main__":
    main()
