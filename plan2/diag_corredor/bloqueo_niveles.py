"""
bloqueo_niveles.py - Los giros a la izquierda del periodo 2 en los cinco niveles de demanda del corredor (905,
1358, 1810, 2715 y 3620 veh/h): cuanto verde bloquean y si la cola llega al cruce de aguas arriba, medido segundo
a segundo con el registro de bloqueo.py (diagnostico del corredor, 25.10.2026; lo usa mecanismo_2715.md).

Analisis posterior al veredicto (PRERREGISTRO.md): no cambia ningun veredicto ni ningun archivo existente. Usa,
sin modificarlos, bloqueo.py (Registro, metricas_acceso, metricas_enlace, verdes_y_decisiones, retraso_periodos,
fila_acceso, promedio_filas) y comportamiento.py (NIVELES: escenario, control y evaluacion del plan de cada nivel).

Los cinco niveles tienen la misma demanda escalada (x0.5, x0.75, x1, x1.5, x2): en el periodo 2 los cuatro giros
(S2->W, W->N1, E->S1, N1->E; 30, 45, 60, 90 y 120 veh/h cada uno) son a la izquierda, con verde sin prioridad.

Controles por nivel (las claves de comportamiento.NIVELES):
  ref      el fijo de referencia del diagnostico: fijo ajustado desde 10 s en 905 (10/10 s), 1358 (12/10 s) y
           2715 (25/10 s, desfases 0/0); el fijo vigente en 1810 (20/10 s, desfase 15) y 3620 (25/15 s, desfase 25)
  actuado  el actuado de SUMO (comun.archivo_actuado; su .add.xml se escribe en la carpeta de la corrida)
  ippo     la version evaluada de IPPO con mensajes del nivel (905 s4042, 1358 s42, 1810 s4042, 2715 s2042,
           3620 s2042)
Cada corrida usa las funciones de evaluar.py (brazo_referencia, brazo_profundo) con un .sumocfg propio en --datos:
las mismas opciones que el .sumocfg del escenario, con rutas absolutas y una copia de su .add.xml. La envoltura de
traci.simulationStep es la de bloqueo.py (solo lecturas). Las metricas de cada corrida se comparan con las de la
evaluacion del plan con la misma semilla (determinismo).

Uso (desde plan2/; los datos pesados van fuera del repositorio):
  python diag_corredor/bloqueo_niveles.py correr   --datos <carpeta> [--semillas 1001-1005] [--procesos 4]
  python diag_corredor/bloqueo_niveles.py analizar --datos <carpeta> [--salida diag_corredor]
analizar escribe en --salida bloqueo_niveles.csv (nivel, control, periodo y acceso), bloqueo_niveles_enlaces.csv,
bloqueo_niveles_verdes.csv, bloqueo_niveles_decisiones.csv, bloqueo_niveles_periodos.csv y
bloqueo_niveles_control.csv; cada uno con una fila por semilla y una fila "media".
"""
import os
import sys
import csv
import json
import gzip
import time
import shutil
import random
import hashlib
import argparse
import statistics
import subprocess
import xml.etree.ElementTree as ET

os.environ.setdefault("OMP_NUM_THREADS", "1")       # como plan2/cola.py: un hilo de torch por proceso
os.environ.setdefault("MKL_NUM_THREADS", "1")

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN2 = os.path.dirname(AQUI)
RAIZ = os.path.dirname(PLAN2)
sys.path.insert(0, AQUI)
import bloqueo as bq            # noqa: E402
import comportamiento as cp     # noqa: E402

NIVELES = ["905", "1358", "1810", "2715", "3620"]
REF = {"905": "fijo10", "1358": "fijo10", "1810": "fijo", "2715": "fijo10", "3620": "fijo"}
CONTROLES = ["ref", "actuado", "ippo"]
# opciones del .sumocfg de los escenarios del corredor (se comprueba que el original no tenga otras)
OPCIONES = {("time", "begin"): "0", ("time", "step-length"): "1", ("processing", "time-to-teleport"): "-1",
            ("report", "no-step-log"): "true", ("report", "no-warnings"): "true"}


def clave_cp(nivel, control):
    return REF[nivel] if control == "ref" else control


def escenario(nivel, control):
    return cp.NIVELES[nivel][clave_cp(nivel, control)][0]


def nombre_base(nivel, control, semilla):
    return f"{nivel}_{control}_s{semilla}"


def sha(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def entradas_cfg(esc):
    """(red, rutas, adicional) del .sumocfg del escenario en plan2/, como rutas absolutas; comprueba que el resto
    de las opciones sean las de OPCIONES."""
    raiz = ET.parse(os.path.join(PLAN2, f"{esc}.sumocfg")).getroot()
    inp = raiz.find("input")
    rutas = {t: os.path.join(PLAN2, inp.find(t).get("value")) for t in ("net-file", "route-files", "additional-files")}
    otras = {(g.tag, o.tag): o.get("value") for g in raiz if g.tag != "input" for o in g}
    if otras != OPCIONES:
        raise SystemExit(f"{esc}.sumocfg tiene otras opciones: {otras}")
    for r in rutas.values():
        if not os.path.exists(r):
            raise SystemExit(f"falta {r}")
    return rutas["net-file"], rutas["route-files"], rutas["additional-files"]


def preparar(datos):
    """.sumocfg de rutas absolutas por escenario y copia de su .add.xml (con su sha256) en --datos."""
    os.makedirs(datos, exist_ok=True)
    registro = {}
    for n in NIVELES:
        for c in CONTROLES:
            esc = escenario(n, c)
            if esc in registro:
                continue
            red, rutas, adic = entradas_cfg(esc)
            copia = os.path.join(datos, f"{esc}.add.xml")
            if not os.path.exists(copia):
                shutil.copyfile(adic, copia)
            if sha(copia) != sha(adic):
                raise SystemExit(f"{copia} ya no es igual a {adic}")
            with open(os.path.join(datos, f"{esc}.sumocfg"), "w", encoding="utf-8") as f:
                f.write(f"""<configuration>
    <input>
        <net-file value="{red}" />
        <route-files value="{rutas}" />
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
            registro[esc] = {"red": red, "rutas": rutas, "adicional": adic, "sha_adicional": sha(adic),
                             "programa": bq.leer_programa(copia)}
    with open(os.path.join(datos, "escenarios.json"), "w", encoding="utf-8") as f:
        json.dump(registro, f, indent=1)
    return registro


# ---------------- correr ----------------
def uno(nivel, control, semilla, datos):
    """Una corrida con las funciones de evaluar.py y la envoltura de traci.simulationStep de bloqueo.py."""
    sys.path.insert(0, RAIZ)
    os.chdir(PLAN2)
    import traci
    import evaluar
    import rl_corredor
    esc = escenario(nivel, control)
    clave = clave_cp(nivel, control)
    tipo = cp.NIVELES[nivel][clave][1]
    nombre = "niv_" + esc                       # registrado solo en este proceso, con el .sumocfg de --datos
    cfg = os.path.join(datos, f"{esc}.sumocfg")
    rl_corredor.ESCENARIOS[nombre] = {**rl_corredor.ESCENARIOS[esc], "cfg": cfg}
    if tipo == "ref":
        _, _, _, correr = evaluar.brazo_referencia(nombre, "fijo" if clave == "fijo10" else clave)
    else:
        import torch
        import rl_ippo
        torch.set_num_threads(1)
        rl_ippo.ESCENARIOS[nombre] = {**rl_ippo.ESCENARIOS[esc], "cfg": cfg}
        rl_ippo.VECINOS[nombre] = rl_ippo.VECINOS[esc]
        rl_ippo.LADOS[nombre] = rl_ippo.LADOS[esc]
        _, _, _, correr = evaluar.brazo_profundo(nombre, os.path.join(PLAN2, tipo), 0, 0.0)
    base = nombre_base(nivel, control, semilla)
    trabajo = os.path.join(datos, "tmp_" + base)       # aqui escribe el actuado su .add.xml
    os.makedirs(trabajo, exist_ok=True)
    os.chdir(trabajo)
    reg = bq.Registro()
    reg.origen = bq.leer_origenes(entradas_cfg(esc)[1])
    original = traci.simulationStep

    def envoltura(*a, **k):
        r = original(*a, **k)
        reg.paso()
        return r
    traci.simulationStep = envoltura
    random.seed(semilla)                                # como evaluar.main_v2
    t0 = time.time()
    tripinfo = os.path.join(datos, base + "_trip.xml")
    try:
        res = correr(semilla, tripinfo, None)
    finally:
        traci.simulationStep = original
    with gzip.open(os.path.join(datos, f"seg_{base}.csv.gz"), "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(bq.Registro.cabecera())
        w.writerows(reg.filas)
    meta = {"nivel": nivel, "control": control, "clave": clave, "escenario": esc, "semilla": semilla,
            "cfg": cfg, "control_def": tipo, "segundos": round(time.time() - t0, 1), "pasos": len(reg.filas),
            "metricas": {m: res.get(m) for m in bq.METRICAS_CONTROL},
            "accesos": {a: {"tls": d["tls"], "mov": d["mov"]} for a, d in reg.acc.items()}}
    with open(os.path.join(datos, f"met_{base}.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    print(f"{base}: total {res['retraso_total_prom']}  timeLoss {res['timeloss_prom']}  "
          f"cambios {res['cambios_fase']}  {meta['segundos']} s", flush=True)


def correr(args):
    preparar(args.datos)
    trabajos = [(n, c, s) for n in NIVELES for c in CONTROLES for s in bq.rango(args.semillas)]
    pendientes = [t for t in trabajos
                  if not os.path.exists(os.path.join(args.datos, f"met_{nombre_base(*t)}.json"))]
    pendientes.sort(key=lambda t: (t[1] != "ippo", -int(t[0]), t[2]))      # las mas largas primero
    activos = []
    while pendientes or activos:
        while pendientes and len(activos) < args.procesos:
            n, c, s = pendientes.pop(0)
            log = open(os.path.join(args.datos, f"log_{nombre_base(n, c, s)}.txt"), "w")
            p = subprocess.Popen([sys.executable, os.path.abspath(__file__), "uno", "--datos", args.datos,
                                  "--nivel", n, "--control", c, "--semilla", str(s)],
                                 stdout=log, stderr=subprocess.STDOUT)
            activos.append((p, log, (n, c, s)))
        time.sleep(2)
        for item in activos[:]:
            if item[0].poll() is not None:
                item[1].close()
                print(f"termino {nombre_base(*item[2])} (codigo {item[0].returncode})", flush=True)
                activos.remove(item)


# ---------------- analizar ----------------
def leer_plan(rel):
    with open(os.path.join(PLAN2, rel), newline="", encoding="utf-8") as f:
        return {int(x["semilla"]): x for x in csv.DictReader(f) if x.get("semilla", "").isdigit()}


def analizar(args):
    datos, salida = args.datos, args.salida
    semillas = bq.rango(args.semillas)
    with open(os.path.join(datos, "escenarios.json"), encoding="utf-8") as f:
        registro = json.load(f)
    t_acc, t_enl, t_ver, t_dec, t_per, t_ctl = [], [], [], [], [], []
    for n in NIVELES:
        for c in CONTROLES:
            clave = clave_cp(n, c)
            esc, _, plan_rel = cp.NIVELES[n][clave]
            if sha(registro[esc]["adicional"]) != registro[esc]["sha_adicional"]:
                print(f"AVISO: {registro[esc]['adicional']} cambio despues de las corridas", flush=True)
            plan = leer_plan(plan_rel)
            por_sem, enl_sem, per_sem, verdes, decis = {}, {}, {}, [], []
            for s in semillas:
                base = nombre_base(n, c, s)
                with open(os.path.join(datos, f"met_{base}.json"), encoding="utf-8") as f:
                    meta = json.load(f)
                acc = {a: {"tls": d["tls"], "mov": {k: tuple(v) for k, v in d["mov"].items()}}
                       for a, d in meta["accesos"].items()}
                m, pl = meta["metricas"], plan[s]
                fila_c = {"nivel": n, "control": c, "clave": clave, "escenario": esc, "semilla": s}
                for k in bq.METRICAS_CONTROL:
                    fila_c[k] = m[k]
                    fila_c["plan_" + k] = pl.get(k, "")
                fila_c["igual_al_plan"] = all(float(m[k]) == float(pl[k]) for k in bq.METRICAS_CONTROL
                                              if pl.get(k, "") != "")
                fila_c["archivo_plan"] = plan_rel
                t_ctl.append(fila_c)
                filas = bq.leer_segundos(os.path.join(datos, f"seg_{base}.csv.gz"))
                por_sem[s] = bq.metricas_acceso(filas, acc)
                enl_sem[s] = bq.metricas_enlace(filas, acc)
                v, d = bq.verdes_y_decisiones(filas, acc)
                for x in v:
                    x["semilla"] = s
                verdes += v
                decis += d
                per_sem[s] = bq.retraso_periodos(os.path.join(datos, base + "_trip.xml"), registro[esc]["rutas"])
                print(f"analizado {base}", flush=True)
            for p in bq.PERIODOS:
                for a in bq.ACCESOS:
                    filas_s = []
                    for s in semillas:
                        fila = bq.fila_acceso(esc, c, p, a, acc[a]["tls"], s, por_sem[s][(p, a)])
                        filas_s.append({"nivel": n, **fila})
                    t_acc += filas_s
                    t_acc.append(bq.promedio_filas(filas_s))
                for e in bq.ENLACES:
                    filas_s = [{"nivel": n, "escenario": esc, "control": c, "periodo": p, "enlace": e, "semilla": s,
                                **{k: (bq.r(v, 2) if isinstance(v, float) else v) for k, v in enl_sem[s][(p, e)].items()}}
                               for s in semillas]
                    t_enl += filas_s
                    t_enl.append(bq.promedio_filas(filas_s))
                for mov in ("todos", "avenida", "transversal", "giros", "desde_E_C2"):
                    filas_s = [{"nivel": n, "escenario": esc, "control": c, "periodo": p, "grupo": mov, "semilla": s,
                                **{k: bq.r(v, 2) for k, v in per_sem[s][(p, mov)].items()}} for s in semillas]
                    t_per += filas_s
                    t_per.append(bq.promedio_filas(filas_s))
            # verdes por fase, semaforo y periodo, con y sin la cabeza del acceso con giro detenida girando
            for tls in bq.SEMAFOROS:
                sem = tls[-2:]
                for fase, grupo in (("transversal", bq.TRANSVERSAL[tls]), ("avenida", bq.AVENIDA[tls])):
                    for p in bq.PERIODOS:
                        g = [x for x in verdes if x["semaforo"] == sem and x["fase"] == fase and x["periodo"] == p]
                        for a in grupo:
                            for clase in ("todos", "con_cabeza_izq_detenida", "sin"):
                                h = [x for x in g if clase == "todos" or (clase == "sin") == (x[f"izq_{a}"] == 0)]
                                dur = [x["duracion"] for x in h]
                                t_ver.append({"nivel": n, "escenario": esc, "control": c, "semaforo": sem, "fase": fase,
                                              "periodo": p, "acceso": a, "clase": clase,
                                              "verdes_por_semilla": bq.r(len(h) / len(semillas), 1),
                                              "duracion_media": bq.r(bq.media(dur), 1),
                                              "duracion_mediana": bq.r(statistics.median(dur), 1) if dur else "",
                                              "seg_izq_por_verde": bq.r(bq.media([x[f"izq_{a}"] for x in h]), 2),
                                              "frac_verde_izq": bq.r(sum(x[f"izq_{a}"] for x in h) / max(1, sum(dur)), 3)})
                    if fase == "transversal" and c == "ippo":
                        for p in bq.PERIODOS:
                            for cond, filtro in bq.CONDICIONES:
                                g = [x for x in decis if x["semaforo"] == sem and x["periodo"] == p and filtro(x)]
                                t_dec.append({"nivel": n, "escenario": esc, "control": c, "semaforo": sem,
                                              "periodo": p, "acceso": bq.GIRO_TRANSVERSAL[tls], "condicion": cond,
                                              "decisiones": len(g),
                                              "frac_cambia": bq.r(sum(1 for x in g if x["cambia"]) / len(g), 3)
                                              if g else "",
                                              "detenidos_acceso_medio": bq.r(bq.media([x["det_acceso"] for x in g]), 2)})
    bq.guardar(os.path.join(salida, "bloqueo_niveles.csv"), t_acc)
    bq.guardar(os.path.join(salida, "bloqueo_niveles_enlaces.csv"), t_enl)
    bq.guardar(os.path.join(salida, "bloqueo_niveles_verdes.csv"), t_ver)
    bq.guardar(os.path.join(salida, "bloqueo_niveles_decisiones.csv"), t_dec)
    bq.guardar(os.path.join(salida, "bloqueo_niveles_periodos.csv"), t_per)
    bq.guardar(os.path.join(salida, "bloqueo_niveles_control.csv"), t_ctl)
    iguales = sum(1 for x in t_ctl if x["igual_al_plan"])
    print(f"determinismo: {iguales} de {len(t_ctl)} corridas iguales a la evaluacion del plan", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["correr", "uno", "analizar"])
    ap.add_argument("--datos", required=True, help="carpeta de las corridas (fuera del repositorio)")
    ap.add_argument("--salida", default=AQUI, help="carpeta de los CSV de resultados")
    ap.add_argument("--semillas", default="1001-1005")
    ap.add_argument("--procesos", type=int, default=4)
    ap.add_argument("--nivel", choices=NIVELES)
    ap.add_argument("--control", choices=CONTROLES)
    ap.add_argument("--semilla", type=int)
    args = ap.parse_args()
    args.datos = os.path.abspath(args.datos)
    if args.accion == "correr":
        correr(args)
    elif args.accion == "uno":
        uno(args.nivel, args.control, args.semilla, args.datos)
    else:
        analizar(args)


if __name__ == "__main__":
    main()
