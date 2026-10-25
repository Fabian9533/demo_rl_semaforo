"""
sumo_chequeos.py - Comprobaciones de SUMO del diagnostico del corredor (25.10.2026).

Pregunta: la falta de tendencia del corredor con la demanda, viene del simulador? Cuatro
comprobaciones (plan2/diag_corredor/PRERREGISTRO.md, "Comprobaciones de SUMO"):

  python diag_corredor/sumo_chequeos.py teletransportes [--procesos 8]
      2715 y P2, semillas 1001-1005: fijo, actuado, ciclo minimo (trivial) y la version evaluada de
      IPPO con mensajes, por el mismo camino que evaluar.py (TraCI). Tres variantes de opciones:
        base   las del .sumocfg (time-to-teleport -1), las de la evaluacion
        chk    + --collision.check-junctions true --collision.action warn (cuenta tambien choques
               dentro de los cruces; warn no cambia la dinamica)
        tt300  + --time-to-teleport 300 (el valor por defecto de SUMO: un vehiculo detenido 300 s
               seguidos se teletransporta; mide si hay bloqueos y cuanto cambiarian el retraso)
      Lee el --statistic-output de cada corrida (teletransportes, choques, frenadas de emergencia,
      vehiculos que esperan entrar al cerrar) y el tripinfo (comun.leer_tripinfo).
  python diag_corredor/sumo_chequeos.py salida [--procesos 8]
      Los mismos brazos, niveles y semillas que teletransportes con --default.departspeed max (los
      vehiculos entran a la velocidad maxima segura; el defecto de SUMO es 0): mide cuanto de la espera
      para entrar y del orden entre controles depende de como inserta SUMO, con el paso en 1 s.
  python diag_corredor/sumo_chequeos.py paso [--procesos 12]
      1358, P1 y 2715, semillas 1001-1010: fijo, actuado y ciclo minimo con sumo directo (sin
      TraCI), con --step-length 1 y 0.5. IPPO no entra: rl_ippo cuenta cada paso como 1 s.
  python diag_corredor/sumo_chequeos.py determinismo
      IPPO en 1358 (politica_dem_corredor_t1358_vecinos_s42.pt), semillas 1001-1003, dos veces;
      compara las metricas y el sha256 del tripinfo, y contra el CSV de la evaluacion.
  python diag_corredor/sumo_chequeos.py insercion
      Capacidad de insercion de una arista de entrada (un carril, 392.8 m): un solo flow de
      3600 veh/h de W_C1 a C2_E con los semaforos apagados (--tls.all-off), con departSpeed 0 (el
      de las rutas del corredor) y con departSpeed max.
  python diag_corredor/sumo_chequeos.py definiciones
      Fijo de 2715 y P2, semilla 1001: comprueba en el tripinfo que duration = arrival - depart, que
      timeLoss no incluye la espera para entrar y que el retraso total de comun.leer_tripinfo es la
      formula de la documentacion del --statistic-output; calcula el piso de espera para entrar que
      impone solo la capacidad de insercion (1202 veh/h por carril con paso de 1 s).
  python diag_corredor/sumo_chequeos.py resumen
      Lee los CSV de diag_corredor/sumo/ e imprime las tablas de sumo.md.

Se corre desde plan2/ (los .sumocfg, .add.xml y politicas estan ahi). Salidas en
plan2/diag_corredor/sumo/: teletransportes.csv, paso.csv, determinismo.csv, insercion.csv.
No cambia ningun archivo del plan; el actuado y el trivial reescriben <esc>_actuado.add.xml y
<esc>_trivial.add.xml igual que evaluar.py (mismo contenido).
"""
import os
import sys
import csv
import time
import hashlib
import argparse
import statistics
import subprocess
import concurrent.futures
import xml.etree.ElementTree as ET

# igual que plan2/cola.py: un hilo por proceso de torch
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN2 = os.path.dirname(AQUI)
RAIZ = os.path.dirname(PLAN2)
sys.path.insert(0, RAIZ)
os.chdir(PLAN2)

import comun  # noqa: E402

ARGS_ESTADISTICAS = comun.args_estadisticas     # el original; cada variante le suma sus opciones

SALIDA = os.path.join("diag_corredor", "sumo")
TMP = os.path.join(SALIDA, "tmp")
FIN_SIM = 6000      # el tope de los brazos con TraCI (pasos < 6000) y de barrer_fijo.py

# nivel -> (escenario, politica IPPO de la version evaluada)
NIVELES = {
    "1358": ("dem_corredor_t1358", "politica_dem_corredor_t1358_vecinos_s42.pt"),
    "P1": ("corredor", "politica_corredor_vecinos_s4042.pt"),
    "2715": ("dem_corredor_t2715", "politica_dem_corredor_t2715_vecinos_s2042.pt"),
    "P2": ("corredor_alta", "politica_corredor_alta_vecinos_s2042.pt"),
}
# CSV de la evaluacion de cada brazo (para comprobar que la variante base reproduce los numeros)
CSV_EVAL = {
    ("1358", "fijo"): "demanda2/eval_dem_corredor_t1358_fijo.csv",
    ("1358", "actuado"): "demanda2/eval_dem_corredor_t1358_actuado.csv",
    ("1358", "trivial"): "demanda2/eval_dem_corredor_t1358_trivial.csv",
    ("1358", "ippo"): "demanda2/eval_dem_corredor_t1358_ippo_vecinos_s42.csv",
    ("P1", "fijo"): "parciales/eval_corredor_fijo.csv",
    ("P1", "actuado"): "parciales/eval_corredor_actuado.csv",
    ("P1", "trivial"): "parciales/eval_corredor_trivial.csv",
    ("2715", "fijo"): "demanda2/eval_dem_corredor_t2715_fijo.csv",
    ("2715", "actuado"): "demanda2/eval_dem_corredor_t2715_actuado.csv",
    ("2715", "trivial"): "demanda2/eval_dem_corredor_t2715_trivial.csv",
    ("2715", "ippo"): "demanda2/eval_dem_corredor_t2715_ippo_vecinos_s2042.csv",
    ("P2", "fijo"): "parciales/eval_corredor_alta_fijo.csv",
    ("P2", "actuado"): "parciales/eval_corredor_alta_actuado.csv",
    ("P2", "trivial"): "parciales/eval_corredor_alta_trivial.csv",
    ("P2", "ippo"): "parciales/eval_corredor_alta_ippo_vecinos_s2042.csv",
}
VARIANTES = {"base": [],
             "chk": ["--collision.check-junctions", "true", "--collision.action", "warn"],
             "tt300": ["--time-to-teleport", "300"]}
# Modo salida: misma corrida con los vehiculos entrando a la velocidad maxima segura en vez de
# detenidos (las rutas no fijan departSpeed: vale el defecto de SUMO, 0). Con paso de 1 s la
# insercion por carril sube de 1202 a unos 1500 veh/h; IPPO se puede probar porque el paso sigue en 1 s.
VARIANTES_SALIDA = {"vmax": ["--default.departspeed", "max"]}
METRICAS = ["timeloss_prom", "retraso_total_prom", "retraso_insercion_prom", "no_insertados",
            "no_terminados", "vehiculos", "throughput", "cambios_fase"]
ESTADISTICAS = [("vehicles", "loaded"), ("vehicles", "inserted"), ("vehicles", "running"),
                ("vehicles", "waiting"), ("teleports", "total"), ("teleports", "jam"),
                ("teleports", "yield"), ("teleports", "wrongLane"), ("safety", "collisions"),
                ("safety", "emergencyStops"), ("safety", "emergencyBraking"),
                ("vehicleTripStatistics", "departDelay"), ("vehicleTripStatistics", "departDelayWaiting"),
                ("vehicleTripStatistics", "timeLoss"), ("performance", "end")]


def campo(seccion, atributo):
    return f"{seccion[:4]}_{atributo}"


def leer_estadisticas(tripinfo):
    """Valores del --statistic-output que acompana al tripinfo (vacios si falta el atributo)."""
    raiz = ET.parse(comun.ruta_estadisticas(tripinfo)).getroot()
    fila = {}
    for seccion, atributo in ESTADISTICAS:
        nodo = raiz.find(seccion)
        fila[campo(seccion, atributo)] = nodo.get(atributo, "") if nodo is not None else ""
    return fila


def sha(ruta):
    """sha256 de los registros <tripinfo> (atributos y emisiones), sin la cabecera del archivo, que
    lleva la fecha, el nombre del archivo y las opciones de la corrida."""
    h = hashlib.sha256()
    for v in ET.parse(ruta).getroot().findall("tripinfo"):
        h.update(ET.tostring(v))
    return h.hexdigest()[:16]


def leer_csv_eval(ruta):
    if not os.path.exists(ruta):
        return {}
    with open(ruta, newline="", encoding="utf-8") as f:
        return {int(r["semilla"]): r for r in csv.DictReader(f)}


def escribir(ruta, filas):
    campos = []
    for fila in filas:
        campos += [k for k in fila if k not in campos]
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    print(f"Escrito {ruta} ({len(filas)} filas)")


def comparar_eval(fila, nivel, control):
    """Agrega 'igual_eval': 1 si las metricas coinciden con el CSV de la evaluacion en esa semilla."""
    ref = leer_csv_eval(CSV_EVAL.get((nivel, control), "")).get(int(fila["semilla"]))
    if ref is None:
        fila["igual_eval"] = ""
        return
    iguales = all(abs(float(fila[m]) - float(ref[m])) < 1e-9 for m in
                  ("timeloss_prom", "retraso_total_prom", "retraso_insercion_prom", "no_insertados",
                   "no_terminados", "vehiculos"))
    fila["igual_eval"] = int(iguales)


# ---------------- 1. Teletransportes y bloqueos (TraCI, mismo camino que evaluar.py) ----------------
def tarea_variantes(nivel, control, semillas):
    """Las tres variantes de un brazo en un mismo proceso (el actuado y el trivial reescriben su
    .add.xml al arrancar: dos procesos a la vez chocarian en Windows)."""
    filas = []
    for variante in VARIANTES:
        filas += tarea_traci(nivel, control, variante, semillas)
    return filas


def tarea_traci(nivel, control, variante, semillas, sufijo="", guardar_tripinfo=False):
    """Corre un brazo con evaluar.py (brazo_referencia o brazo_profundo) y las opciones extra de la
    variante; devuelve una fila por semilla."""
    import random
    import evaluar
    extra = {**VARIANTES, **VARIANTES_SALIDA}[variante]
    comun.args_estadisticas = lambda tripinfo: ARGS_ESTADISTICAS(tripinfo) + extra
    esc, politica = NIVELES[nivel]
    if control == "ippo":
        _, _, _, correr = evaluar.brazo_profundo(esc, politica, 0, 0.0)
    else:
        _, _, _, correr = evaluar.brazo_referencia(esc, control)
    filas = []
    for s in semillas:
        random.seed(s)          # como evaluar.main_v2
        tripinfo = os.path.join(TMP, f"ti_{nivel}_{control}_{variante}{sufijo}_s{s}.xml")
        t0 = time.time()
        res = correr(s, tripinfo, None)
        fila = {"nivel": nivel, "escenario": esc, "control": control, "variante": variante,
                "semilla": s, **{m: res.get(m, "") for m in METRICAS}, **leer_estadisticas(tripinfo),
                "sha_tripinfo": sha(tripinfo), "segundos": round(time.time() - t0, 1)}
        comparar_eval(fila, nivel, control)
        if not guardar_tripinfo:
            comun.borrar_tripinfo(tripinfo)
        filas.append(fila)
        print(f"{nivel:5s} {control:8s} {variante:6s} s{s}: total={fila['retraso_total_prom']} "
              f"tele={fila['tele_total']} choques={fila['safe_collisions']} igual_eval={fila['igual_eval']} "
              f"({fila['segundos']} s)", flush=True)
    return filas


def correr_paralelo(tareas, procesos, funcion):
    filas = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=procesos) as ex:
        futuros = [ex.submit(funcion, *t) for t in tareas]
        for fut in concurrent.futures.as_completed(futuros):
            filas += fut.result()
    return filas


def teletransportes(args):
    semillas = list(range(1001, 1006))
    tareas = [(nivel, control, semillas)
              for nivel in ("2715", "P2") for control in ("ippo", "fijo", "actuado", "trivial")]
    filas = correr_paralelo(tareas, args.procesos, tarea_variantes)
    filas.sort(key=lambda f: (f["nivel"], f["control"], f["variante"], f["semilla"]))
    escribir(os.path.join(SALIDA, "teletransportes.csv"), filas)


def tarea_salida(nivel, control, semillas):
    return tarea_traci(nivel, control, "vmax", semillas)


def salida(args):
    semillas = list(range(1001, 1006))
    tareas = [(nivel, control, semillas)
              for nivel in ("2715", "P2") for control in ("ippo", "fijo", "actuado", "trivial")]
    filas = correr_paralelo(tareas, args.procesos, tarea_salida)
    filas.sort(key=lambda f: (f["nivel"], f["control"], f["semilla"]))
    escribir(os.path.join(SALIDA, "salida_vmax.csv"), filas)


# ---------------- 2. Paso de simulacion (sumo directo) ----------------
def adicionales(esc, control):
    cfg = f"{esc}.sumocfg"
    _, base = comun.leer_cfg(cfg)
    if control == "fijo":
        return cfg, base
    return cfg, base + [f"{esc}_{control}.add.xml"]     # el ultimo programa cargado queda activo


def tarea_sumo(nivel, control, paso, semillas):
    esc, _ = NIVELES[nivel]
    cfg, adic = adicionales(esc, control)
    filas = []
    for s in semillas:
        tripinfo = os.path.join(TMP, f"ti_paso_{nivel}_{control}_{paso}_s{s}.xml")
        cmd = ["sumo", "-c", cfg, "--seed", str(s), "--tripinfo-output", tripinfo,
               "--tripinfo-output.write-unfinished", "true", "--device.emissions.probability", "1",
               "--no-step-log", "true", "--no-warnings", "true", "--end", str(FIN_SIM),
               "--step-length", str(paso), "--additional-files", ",".join(adic)] + \
            comun.args_estadisticas(tripinfo)
        t0 = time.time()
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        res = comun.leer_tripinfo(tripinfo)
        fila = {"nivel": nivel, "escenario": esc, "control": control, "paso": paso, "semilla": s,
                **{m: res.get(m, "") for m in METRICAS if m != "cambios_fase"},
                **leer_estadisticas(tripinfo), "segundos": round(time.time() - t0, 1)}
        if paso == 1:
            comparar_eval(fila, nivel, control)
        comun.borrar_tripinfo(tripinfo)
        filas.append(fila)
        print(f"{nivel:5s} {control:8s} paso {paso}: s{s} total={fila['retraso_total_prom']} "
              f"timeLoss={fila['timeloss_prom']} ({fila['segundos']} s)", flush=True)
    return filas


def paso(args):
    semillas = list(range(1001, 1011))
    tareas = [(nivel, control, p, semillas) for nivel in ("1358", "P1", "2715")
              for control in ("fijo", "actuado", "trivial") for p in (1, 0.5)]
    filas = correr_paralelo(tareas, args.procesos, tarea_sumo)
    filas.sort(key=lambda f: (f["nivel"], f["control"], -f["paso"], f["semilla"]))
    escribir(os.path.join(SALIDA, "paso.csv"), filas)


# ---------------- 3. Determinismo ----------------
def determinismo(args):
    semillas = [1001, 1002, 1003]
    filas = []
    for rep in (1, 2):
        for fila in tarea_traci("1358", "ippo", "base", semillas, sufijo=f"_rep{rep}", guardar_tripinfo=True):
            fila["repeticion"] = rep
            filas.append(fila)
    escribir(os.path.join(SALIDA, "determinismo.csv"), filas)


# ---------------- 4. Capacidad de insercion ----------------
RUTA_INSERCION = """<routes>
    <vType id="auto" accel="2.6" decel="4.5" sigma="0.5" length="5" minGap="2.5" maxSpeed="13.89"/>
    <flow id="f" type="auto" from="W_C1" to="C2_E" begin="0" end="600" vehsPerHour="3600"{extra}/>
</routes>
"""


# Descarga de una cola en la linea de detencion: C1 en rojo 200 s (se forma la cola en W_C1), luego
# verde 400 s; C2 siempre en verde. Un detector instantaneo a 5 m de la salida de C1 (en C1_C2) anota
# cada vehiculo; el intervalo entre el 5.o y el 30.o da el flujo de saturacion.
ADD_DESCARGA = """<additional>
    <tlLogic id="semaforo_C1" type="static" programID="descarga" offset="0">
        <phase duration="200" state="rrrrrrrrrrrr"/>
        <phase duration="400" state="GGGGGGGGGGGG"/>
    </tlLogic>
    <tlLogic id="semaforo_C2" type="static" programID="descarga" offset="0">
        <phase duration="600" state="GGGGGGGGGGGG"/>
    </tlLogic>
    <instantInductionLoop id="salida_C1" lane="C1_C2_0" pos="5" file="{salida}"/>
</additional>
"""


def correr_insercion(ruta, s, paso, extra_cmd, etiqueta):
    tripinfo = os.path.join(TMP, f"ti_insercion_{etiqueta}.xml")
    cmd = ["sumo", "-n", "corredor.net.xml", "-r", ruta, "--seed", str(s), "--step-length", str(paso),
           "--tripinfo-output", tripinfo, "--no-step-log", "true", "--no-warnings", "true",
           "--end", "600"] + comun.args_estadisticas(tripinfo) + extra_cmd
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    est = leer_estadisticas(tripinfo)
    comun.borrar_tripinfo(tripinfo)
    return est


def insercion(args):
    filas = []
    for paso in (1, 0.5):
        # 1) insercion en una arista de entrada libre (semaforos apagados)
        for nombre, extra in (("insercion departSpeed 0 (corredor)", ""),
                              ("insercion departSpeed max", ' departSpeed="max"')):
            ruta = os.path.join(TMP, f"insercion_{len(extra)}.rou.xml")
            with open(ruta, "w") as f:
                f.write(RUTA_INSERCION.format(extra=extra))
            for s in (1001, 1002, 1003):
                est = correr_insercion(ruta, s, paso, ["--tls.all-off", "true"], f"{paso}_{s}")
                insertados = int(est["vehi_inserted"])
                filas.append({"caso": nombre, "paso": paso, "semilla": s, "veh": insertados,
                              "veh_h": round(insertados * 3600 / 600)})
                print(filas[-1], flush=True)
        # 2) descarga de una cola detenida en la linea de C1
        ruta = os.path.join(TMP, "insercion_0.rou.xml")
        for s in (1001, 1002, 1003):
            salida = os.path.join(TMP, f"descarga_{paso}_{s}.xml")
            add = os.path.join(TMP, f"descarga_{paso}_{s}.add.xml")
            with open(add, "w") as f:
                f.write(ADD_DESCARGA.format(salida=os.path.basename(salida)))
            correr_insercion(ruta, s, paso, ["--additional-files", add], f"d{paso}_{s}")
            pasos = sorted(float(e.get("time")) for e in ET.parse(salida).getroot().findall("instantOut")
                           if e.get("state") == "enter")
            h = (pasos[29] - pasos[4]) / 25 if len(pasos) >= 30 else float("nan")
            filas.append({"caso": "descarga de cola en verde (veh 5 a 30)", "paso": paso, "semilla": s,
                          "veh": len(pasos), "veh_h": round(3600 / h), "intervalo_s": round(h, 3),
                          "perdida_arranque_s": round(pasos[0] - 200, 1) if pasos else ""})
            print(filas[-1], flush=True)
    escribir(os.path.join(SALIDA, "insercion.csv"), filas)


# ---------------- 5. Definiciones, comprobadas en un tripinfo ----------------
def piso_insercion(rou, capacidad):
    """Espera media para entrar (s/veh) que impone solo la capacidad de insercion de cada arista de
    entrada (modelo de fluido: llegadas uniformes de cada flow, servicio a 'capacidad' veh/h, red sin
    bloqueos aguas abajo). Es una cota inferior de departDelay con cualquier control."""
    flows = ET.parse(rou).getroot().findall("flow")
    total = sum(float(f.get("vehsPerHour")) * (float(f.get("end")) - float(f.get("begin"))) / 3600 for f in flows)
    espera, detalle = 0.0, {}
    for arista in sorted({f.get("from") for f in flows}):
        cola, area, t = 0.0, 0.0, 0
        while t < FIN_SIM:
            llegada = sum(float(f.get("vehsPerHour")) for f in flows
                          if f.get("from") == arista and float(f.get("begin")) <= t < float(f.get("end"))) / 3600
            cola = max(0.0, cola + llegada - capacidad / 3600)
            area += cola
            t += 1
        if area > 0:
            detalle[arista] = round(area / 3600, 1)      # veh-h de espera en esa entrada
        espera += area
    return espera / total, detalle


def definiciones(args):
    filas = []
    for nivel in ("2715", "P2"):
        esc, _ = NIVELES[nivel]
        tripinfo = os.path.join(TMP, f"ti_def_{nivel}.xml")
        cmd = ["sumo", "-c", f"{esc}.sumocfg", "--seed", "1001", "--tripinfo-output", tripinfo,
               "--tripinfo-output.write-unfinished", "true", "--no-step-log", "true", "--no-warnings", "true",
               "--end", str(FIN_SIM), "--duration-log.statistics", "true"] + comun.args_estadisticas(tripinfo)
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        viajes = ET.parse(tripinfo).getroot().findall("tripinfo")
        est = ET.parse(comun.ruta_estadisticas(tripinfo)).getroot()
        tripstat = est.find("vehicleTripStatistics")
        g = lambda v, a: float(v.get(a))
        retrasados = [v for v in viajes if g(v, "departDelay") >= 60]
        # tiempo a flujo libre: duracion - timeLoss; si timeLoss contara la espera para entrar,
        # duracion - timeLoss seria mucho menor (o negativo) en los vehiculos retrasados
        libre = lambda vs: statistics.mean(g(v, "duration") - g(v, "timeLoss") for v in vs) if vs else float("nan")
        res = comun.leer_tripinfo(tripinfo)
        n_ins = int(est.find("vehicles").get("inserted"))
        n_esp = int(est.find("vehicles").get("waiting"))
        # retraso total de comun.leer_tripinfo frente a la formula de la documentacion
        total_doc = (float(tripstat.get("timeLoss")) * n_ins + float(tripstat.get("totalDepartDelay")) +
                     n_esp * float(tripstat.get("departDelayWaiting"))) / max(1, n_ins + n_esp)
        piso, detalle = piso_insercion(f"{esc}.rou.xml" if nivel == "2715" else "corredor_alta.rou.xml", 1202)
        filas.append({
            "nivel": nivel, "control": "fijo", "semilla": 1001, "vehiculos": len(viajes),
            "duracion_igual_llegada_menos_salida": int(all(abs(g(v, "duration") - (g(v, "arrival") - g(v, "depart"))) < 1e-6
                                                         for v in viajes if g(v, "arrival") >= 0)),
            "timeloss_menor_que_duracion": int(all(g(v, "timeLoss") <= g(v, "duration") + 1e-6 for v in viajes)),
            "veh_espera_entrar_ge60s": len(retrasados),
            "espera_entrar_media_ge60s": round(statistics.mean(g(v, "departDelay") for v in retrasados), 1) if retrasados else "",
            "timeloss_media_ge60s": round(statistics.mean(g(v, "timeLoss") for v in retrasados), 1) if retrasados else "",
            "libre_ge60s": round(libre(retrasados), 1),
            "libre_resto": round(libre([v for v in viajes if g(v, "departDelay") < 1]), 1),
            "retraso_total_comun": res["retraso_total_prom"], "retraso_total_doc": round(total_doc, 2),
            "piso_insercion_s_veh": round(piso, 1), "piso_por_entrada_veh_h": str(detalle),
            "espera_entrar_fijo": res["retraso_insercion_prom"]})
        comun.borrar_tripinfo(tripinfo)
        print(filas[-1], flush=True)
    escribir(os.path.join(SALIDA, "definiciones.csv"), filas)


# ---------------- Resumen ----------------
def leer(nombre):
    ruta = os.path.join(SALIDA, nombre)
    if not os.path.exists(ruta):
        return []
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def media(filas, m):
    return statistics.mean(float(f[m]) for f in filas)


def resumen(args):
    tele = leer("teletransportes.csv")
    if tele:
        print("\n== 1. Teletransportes y bloqueos (semillas 1001-1005; medias por corrida)")
        print("nivel control  variante  tele  jam  choques  fren_emerg  paradas_emerg  esperan_al_cerrar  "
              "no_term  espera_entrar  timeLoss  total  igual_eval")
        claves = sorted({(f["nivel"], f["control"], f["variante"]) for f in tele})
        for nivel, control, variante in claves:
            g = [f for f in tele if (f["nivel"], f["control"], f["variante"]) == (nivel, control, variante)]
            print(f"{nivel:5s} {control:8s} {variante:6s} {media(g, 'tele_total'):5.1f} {media(g, 'tele_jam'):5.1f} "
                  f"{media(g, 'safe_collisions'):7.1f} {media(g, 'safe_emergencyBraking'):10.1f} "
                  f"{media(g, 'safe_emergencyStops'):13.1f} {media(g, 'vehi_waiting'):17.1f} "
                  f"{media(g, 'no_terminados'):8.1f} {media(g, 'retraso_insercion_prom'):13.2f} "
                  f"{media(g, 'timeloss_prom'):9.2f} {media(g, 'retraso_total_prom'):6.2f}  "
                  f"{sum(int(f['igual_eval'] or 0) for f in g)}/{len(g)}")
        print("\nCambio del retraso total con time-to-teleport 300 frente a la evaluacion (base), %:")
        for nivel, control, _ in [c for c in claves if c[2] == "base"]:
            b = [f for f in tele if (f["nivel"], f["control"], f["variante"]) == (nivel, control, "base")]
            t = [f for f in tele if (f["nivel"], f["control"], f["variante"]) == (nivel, control, "tt300")]
            c = [f for f in tele if (f["nivel"], f["control"], f["variante"]) == (nivel, control, "chk")]
            if t:
                db = media(b, "retraso_total_prom")
                print(f"  {nivel:5s} {control:8s} tt300 {(media(t, 'retraso_total_prom') - db) / db * 100:+.2f} % "
                      f"(timeLoss {(media(t, 'timeloss_prom') - media(b, 'timeloss_prom')) / media(b, 'timeloss_prom') * 100:+.2f} %)"
                      f"  chk identico a base: {all(x['sha_tripinfo'] == y['sha_tripinfo'] for x, y in zip(b, c))}")
    vmax = leer("salida_vmax.csv")
    if vmax and tele:
        print("\n== 1b. Entrada a velocidad maxima (--default.departspeed max) frente a la evaluacion (semillas 1001-1005)")
        for nivel in ("2715", "P2"):
            print(f"-- {nivel}")
            for m in ("retraso_insercion_prom", "timeloss_prom", "retraso_total_prom"):
                ref = {c: {f["semilla"]: float(f[m]) for f in tele if f["nivel"] == nivel and f["control"] == c
                           and f["variante"] == "base"} for c in ("fijo", "ippo", "actuado", "trivial")}
                alt = {c: {f["semilla"]: float(f[m]) for f in vmax if f["nivel"] == nivel and f["control"] == c}
                       for c in ("fijo", "ippo", "actuado", "trivial")}
                txt = []
                for nombre, d in (("evaluacion", ref), ("vmax", alt)):
                    medias = {c: statistics.mean(v.values()) for c, v in d.items()}
                    dif = [d["ippo"][s] - d["fijo"][s] for s in sorted(d["fijo"])]
                    ic = 2.776 * statistics.stdev(dif) / len(dif) ** 0.5      # t 0.975 con 4 gl
                    txt.append(f"{nombre}: " + " ".join(f"{c} {v:7.2f}" for c, v in medias.items()) +
                               f" | IPPO-fijo {statistics.mean(dif):+.2f} [{statistics.mean(dif) - ic:+.2f}, "
                               f"{statistics.mean(dif) + ic:+.2f}] ({statistics.mean(dif) / medias['fijo'] * 100:+.1f} %)")
                print(f"   {m:22s} " + "\n   " + " " * 22 + " ".join(txt[:1]) + "\n   " + " " * 22 + txt[1])
    pasos = leer("paso.csv")
    if pasos:
        print("\n== 2. Paso de simulacion (sumo directo, semillas 1001-1010)")
        for nivel in ("1358", "P1", "2715"):
            print(f"-- {nivel}")
            for m in ("timeloss_prom", "retraso_total_prom"):
                orden = {}
                for p in ("1", "0.5"):
                    vals = {}
                    for control in ("fijo", "actuado", "trivial"):
                        g = [f for f in pasos if f["nivel"] == nivel and f["control"] == control and f["paso"] == p]
                        vals[control] = media(g, m)
                    orden[p] = sorted(vals, key=vals.get)
                    print(f"   {m:20s} paso {p:3s}: " + "  ".join(f"{c} {v:7.2f}" for c, v in vals.items())
                          + f"   orden: {' < '.join(orden[p])}")
                for control in ("fijo", "actuado", "trivial"):
                    a = [f for f in pasos if f["nivel"] == nivel and f["control"] == control and f["paso"] == "1"]
                    b = [f for f in pasos if f["nivel"] == nivel and f["control"] == control and f["paso"] == "0.5"]
                    print(f"      {control:8s} cambio 0.5 s vs 1 s: {(media(b, m) - media(a, m)) / media(a, m) * 100:+.1f} %")
                print(f"      orden igual: {orden['1'] == orden['0.5']}")
                for a, b in (("fijo", "actuado"), ("fijo", "trivial"), ("actuado", "trivial")):
                    partes = []
                    for p in ("1", "0.5"):
                        xa = {f["semilla"]: float(f[m]) for f in pasos if f["nivel"] == nivel and f["control"] == a and f["paso"] == p}
                        xb = {f["semilla"]: float(f[m]) for f in pasos if f["nivel"] == nivel and f["control"] == b and f["paso"] == p}
                        d = [xa[s] - xb[s] for s in sorted(xa)]
                        ic = 2.262 * statistics.stdev(d) / len(d) ** 0.5     # t 0.975 con 9 gl
                        partes.append(f"paso {p}: {statistics.mean(d):+7.2f} s [{statistics.mean(d) - ic:+.2f}, {statistics.mean(d) + ic:+.2f}]")
                    print(f"      {a} - {b:8s} (pareado, IC95 t): " + "   ".join(partes))
            g1 = [f for f in pasos if f["nivel"] == nivel and f["paso"] == "1"]
            print(f"   paso 1 igual a la evaluacion con TraCI: {sum(int(f['igual_eval'] or 0) for f in g1)}/{len(g1)}"
                  f"   teletransportes paso 0.5: {sum(int(f['tele_total']) for f in pasos if f['nivel'] == nivel)}")
    det = leer("determinismo.csv")
    if det:
        print("\n== 3. Determinismo (IPPO 1358, s42)")
        for s in sorted({f["semilla"] for f in det}):
            g = [f for f in det if f["semilla"] == s]
            iguales = all(g[0][m] == g[1][m] for m in METRICAS) and g[0]["sha_tripinfo"] == g[1]["sha_tripinfo"]
            print(f"  semilla {s}: rep1 total={g[0]['retraso_total_prom']} rep2 total={g[1]['retraso_total_prom']} "
                  f"sha {g[0]['sha_tripinfo']} / {g[1]['sha_tripinfo']}  identicas: {iguales}  "
                  f"igual al CSV de la evaluacion: {g[0]['igual_eval']}/{g[1]['igual_eval']}")
    ins = leer("insercion.csv")
    if ins:
        print("\n== 4. Capacidad de insercion de W_C1 y flujo de saturacion de la linea de C1 (3 semillas)")
        for caso in dict.fromkeys(f["caso"] for f in ins):
            for p in ("1", "0.5"):
                g = [f for f in ins if f["caso"] == caso and f["paso"] == p]
                print(f"  {caso:40s} paso {p:3s}: {media(g, 'veh_h'):6.0f} veh/h")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", choices=["teletransportes", "salida", "paso", "determinismo", "insercion", "definiciones", "resumen"])
    ap.add_argument("--procesos", type=int, default=8)
    args = ap.parse_args()
    os.makedirs(TMP, exist_ok=True)
    {"teletransportes": teletransportes, "salida": salida, "paso": paso, "determinismo": determinismo,
     "insercion": insercion, "definiciones": definiciones, "resumen": resumen}[args.modo](args)


if __name__ == "__main__":
    main()
