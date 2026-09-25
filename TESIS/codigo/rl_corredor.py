"""
rl_corredor.py - Escenarios con VARIOS semaforos, un agente tabular (Q-learning o SARSA)
independiente por cruce (sin comunicacion entre ellos; es la antesala del modulo U4).

Modos:
  python rl_corredor.py baseline                 # todos los semaforos a tiempo fijo (con offsets tuneados)
  python rl_corredor.py actuado                  # todos actuados (SUMO nativo), sin coordinacion
  python rl_corredor.py train --escenario red --algoritmo qlearning --recompensa retraso --seed 42
  python rl_corredor.py demo --qtable q_table_red_ql_s42.json [--gui]

Escenarios (--escenario, por defecto "corredor"):
  corredor       prueba 3: dos cruces sobre una avenida E-O separados 300 m
  corredor_alta  el mismo corredor con toda la demanda x2 (estres)
  red            prueba 4: rotonda + tres cruces semaforizados, avenida cargada y
                 transversales ligeras (la rotonda no lleva semaforo: cede el paso)
  y los del plan v2 que registra escenarios_plan2.py (red_alta, malla3).

Cada agente ve solo su cruce: estado = cola discretizada en sus 4 aproximaciones
+ su fase verde activa. Las decisiones son cada 5 s; mientras un semaforo esta en ambar,
ese agente no decide. Un episodio es una hora simulada completa con la misma red y demanda;
entre episodios cambian solo epsilon, la semilla de SUMO y las Q-tables heredadas.

Cambios del plan de pruebas v2 (24.09.2026, plan2/ESPEC.md):
  --algoritmo qlearning|sarsa. SARSA elige a2 epsilon-greedy en s2 ANTES de actualizar,
      usa Q(s2, a2) y ejecuta a2.
  --recompensa retraso|colas (por defecto retraso). "retraso" es la de U4 (rl_ippo.recompensa_paso):
      suma por segundo, desde la decision anterior del semaforo, de
      -(W1 * sum_a n_a (1 - v_a / vmax_a) + W2 * esperas), dividida entre 5. "colas" es la de U2
      (-(W1 * detenidos + W2 * esperas) en el instante de decision).
  Epsilon: 1.0 con decaimiento geometrico 0.01 ** (1 / (0.8 * episodios)) hasta EPS_MIN 0.01; con
      --eps-decay explicito se conserva el EPS_MIN 0.05 antiguo (reproduce las corridas viejas).
  Validacion cada --eval-cada episodios (y en el ultimo) con la politica congelada en las semillas
      --val-seeds (999,1999), sobre una copia de la Q-table y sin tocar el RNG del entrenamiento.
      Cada validacion guarda checkpoints/<tag>_ep<NNN>.json; al terminar se publica
      q_table_<tag>.json = checkpoint con menor val (empate: el mas tardio) y q_table_<tag>.meta.json.
  tag = <esc>_<alg>_s<seed>, alg = ql | sarsa | ql_colas | sarsa_colas. El CSV resultados_<tag>.csv
      se reescribe desde cero en cada train. Tripinfo propio: tripinfo_<tag>_train.xml y _val.xml.
  En todos los modos correr_episodio devuelve ademas ret_retraso, ret_colas y ret_spill, medidos cada
      segundo sobre todos los semaforos con suscripciones TraCI (ESPEC seccion 5).
"""
import os
import re
import sys
import csv
import copy
import glob
import json
import time
import random
import argparse
import subprocess

# ---------------- TraCI ----------------
try:
    import traci
    import traci.constants as tc
    import sumolib
except ImportError:
    if "SUMO_HOME" in os.environ:
        sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
        import traci
        import traci.constants as tc
        import sumolib
    else:
        sys.exit("No encuentro TraCI. Define la variable SUMO_HOME o ejecuta: pip install traci sumolib")

import comun
import escenarios_plan2

# ---------------- Escenarios ----------------
# Cada escenario define su configuracion, por semaforo los edges que llegan al cruce,
# los enlaces compartidos entre cruces (donde puede haber spillback) y los flows que
# recorren toda la avenida (para el tiempo de viaje extremo a extremo).
ESCENARIOS = {
    "corredor": {
        "cfg": "corredor.sumocfg",
        "semaforos": {
            "semaforo_C1": ["W_C1", "C2_C1", "N1_C1", "S1_C1"],
            "semaforo_C2": ["C1_C2", "E_C2", "N2_C2", "S2_C2"],
        },
        "enlaces": ["C1_C2", "C2_C1"],
        "flujos_corredor": ["p1_W_E", "p1_E_W", "p2_W_E", "p2_E_W"],
    },
    "red": {
        "cfg": "red.sumocfg",
        "semaforos": {
            "semaforo_C1": ["RE_C1", "C2_C1", "N1_C1", "S1_C1"],
            "semaforo_C2": ["C1_C2", "C3_C2", "N2_C2", "S2_C2"],
            "semaforo_C3": ["C2_C3", "E_C3", "N3_C3", "S3_C3"],
        },
        "enlaces": ["C1_C2", "C2_C1", "C2_C3", "C3_C2"],
        "flujos_corredor": ["p1_W_E", "p1_E_W", "p2_W_E", "p2_E_W"],
    },
}
# corredor_alta: el mismo corredor con toda la demanda escalada (escenario de estres para U4)
ESCENARIOS["corredor_alta"] = {**ESCENARIOS["corredor"], "cfg": "corredor_alta.sumocfg"}
# escenarios nuevos del plan v2 (red_alta, malla3)
ESCENARIOS.update(escenarios_plan2.ESCENARIOS_RC)

# Se definen en main() segun --escenario
ESCENARIO = "corredor"
CFG = ESCENARIOS["corredor"]["cfg"]
SEMAFOROS = ESCENARIOS["corredor"]["semaforos"]
ENLACES = ESCENARIOS["corredor"]["enlaces"]
FLUJOS_CORREDOR = ESCENARIOS["corredor"]["flujos_corredor"]
Q_FILE = "q_table_corredor.json"
RESULTADOS = "resultados_corredor.csv"

# ---------------- Parametros ----------------
PASO_CONTROL = 5      # segundos entre decisiones de cada agente
VERDE_MIN = 10        # verde minimo antes de permitir un cambio (fases principales)
VERDE_MIN_GIRO = 5    # verde minimo en fases de giro protegido (pocos movimientos en verde)
VERDE_MAX = 60        # verde maximo: se fuerza el cambio
W1, W2 = 1.0, 0.01    # pesos de la recompensa
W3 = 2.0              # ret_spill: peso por vehiculo detenido sobre la mitad de las plazas del enlace
ALPHA, GAMMA = 0.1, 0.9
EPS_INICIAL, EPS_DECAY, EPS_MIN = 1.0, 0.9, 0.05   # EPS_DECAY/EPS_MIN antiguos (con --eps-decay)
EPS_MIN_V2 = 0.01     # plan v2: epsilon llega a 0.01 al 80 % de los episodios
PASO_SERIE = 60       # cada cuantos segundos se guarda la cola por aproximacion

# Lecturas por suscripcion (como rl_ippo.suscribir / lecturas)
HALT, VEH = tc.LAST_STEP_VEHICLE_HALTING_NUMBER, tc.LAST_STEP_VEHICLE_NUMBER
ESP, VEL = tc.VAR_WAITING_TIME, tc.LAST_STEP_MEAN_SPEED

# Columnas del CSV de entrenamiento: las de comun.CAMPOS mas las del plan v2 (val_<semilla> segun
# --val-seeds). En este CSV la columna "recompensa" (ya en CAMPOS) es el tipo (retraso/colas); la
# suma de la recompensa de U2 a reloj fijo de 5 s, que antes iba en ella, va en "recompensa_u2".
CAMPOS_V2 = ["segundos", "val", "ret_retraso", "ret_colas", "ret_spill", "algoritmo", "base",
             "recompensa_u2", "no_terminados", "spillback_tasa", "spillback_seg", "cola_max_enlace"]
ALG_CORTO = {"qlearning": "ql", "sarsa": "sarsa"}


# ---------------- Utilidades ----------------
def bin_cola(n):
    """Discretiza el numero de vehiculos detenidos de una aproximacion."""
    if n == 0:
        return 0
    if n <= 3:
        return 1
    if n <= 8:
        return 2
    return 3


def todas_las_aprox():
    return [e for aprox in SEMAFOROS.values() for e in aprox]


def estado(tls, verde_idx):
    colas = tuple(bin_cola(traci.edge.getLastStepHaltingNumber(e)) for e in SEMAFOROS[tls])
    return colas + (verde_idx,)


def clave(s):
    return ",".join(str(x) for x in s)


def recompensa(tls):
    """Recompensa "colas" (U2): detenidos y esperas de sus aproximaciones en este instante."""
    cola = sum(traci.edge.getLastStepHaltingNumber(e) for e in SEMAFOROS[tls])
    espera = sum(traci.edge.getWaitingTime(e) for e in SEMAFOROS[tls])
    return -(W1 * cola + W2 * espera)


def leer(lect, edge, var):
    return lect.get(edge, {}).get(var, 0)


_VMAX = {}   # net_file -> {edge: velocidad maxima}; se lee una vez por red


def velocidades_max(net_file):
    if net_file not in _VMAX:
        net = sumolib.net.readNet(net_file)
        _VMAX[net_file] = {e.getID(): e.getSpeed() for e in net.getEdges()}
    return _VMAX[net_file]


def recompensa_paso(tls, lect, vmax):
    """Recompensa "retraso" de un segundo (copia de rl_ippo.recompensa_paso): vehiculos-equivalentes
    retrasados n_a * (1 - v_media_a / vmax_a) mas W2 * esperas, sobre las aproximaciones de tls."""
    retraso = 0.0
    for a in SEMAFOROS[tls]:
        n = leer(lect, a, VEH)
        if n:
            retraso += n * (1.0 - min(1.0, max(0.0, leer(lect, a, VEL)) / vmax[a]))
    return -(W1 * retraso + W2 * sum(leer(lect, a, ESP) for a in SEMAFOROS[tls]))


def q_vals(Q, tls, s):
    return Q[tls].setdefault(clave(s), [0.0, 0.0])


def mejor_accion(Q, tls, s):
    q = q_vals(Q, tls, s)
    if q[0] == q[1]:
        return random.randint(0, 1)
    return 0 if q[0] > q[1] else 1


def elegir(Q, tls, s, eps, explora):
    """epsilon-greedy si explora (train), greedy si no. Sin explorar no consume el RNG salvo
    en el desempate de mejor_accion, igual que antes."""
    if explora and random.random() < eps:
        return random.randint(0, 1)
    return mejor_accion(Q, tls, s)


def fases_verdes(tls):
    """Lee el programa ACTIVO del semaforo y devuelve las fases verdes y su ambar siguiente."""
    activo = traci.trafficlight.getProgram(tls)
    logicas = traci.trafficlight.getAllProgramLogics(tls)
    logica = next((l for l in logicas if l.programID == activo), logicas[0])
    fases = logica.phases
    verdes = [i for i, p in enumerate(fases) if ("G" in p.state or "g" in p.state) and "y" not in p.state]
    ambar = {i: (i + 1) % len(fases) for i in verdes}
    dur_ambar = {i: max(1, int(fases[ambar[i]].duration)) for i in verdes}
    verde_min = {i: VERDE_MIN if sum(1 for c in fases[i].state if c in "Gg") > 2 else VERDE_MIN_GIRO
                 for i in verdes}
    return verdes, ambar, dur_ambar, verde_min


# ---------------- Episodio ----------------
def correr_episodio(modo, Q, eps, gui, delay, seed, tripinfo=None, serie=None,
                    algoritmo="qlearning", tipo_recompensa="colas"):
    """Corre una hora simulada. modo: baseline (fijo con offsets), actuado (SUMO), train o demo.
    algoritmo (qlearning/sarsa) y tipo_recompensa (colas/retraso) solo importan en train; por
    defecto se comporta como antes del plan v2."""
    binario = sumolib.checkBinary("sumo-gui" if gui else "sumo")
    if tripinfo is None:
        tripinfo = f"tripinfo_{ESCENARIO}_{modo}.xml"
    cmd = [binario, "-c", CFG, "--seed", str(seed),
           "--tripinfo-output", tripinfo, "--tripinfo-output.write-unfinished", "true",
           "--device.emissions.probability", "1"]
    if modo == "actuado":
        cmd += ["--additional-files",
                comun.archivo_actuado(CFG, ESCENARIO, list(SEMAFOROS), VERDE_MIN, VERDE_MIN_GIRO, VERDE_MAX)]
    if gui:
        cmd += ["--start", "--quit-on-end", "--delay", str(delay)]
        if os.path.exists(f"vista_{ESCENARIO}.xml"):
            cmd += ["--gui-settings-file", f"vista_{ESCENARIO}.xml"]
    comun.iniciar_sumo(cmd)

    controla = modo in ("train", "demo")
    aprende = modo == "train"
    sarsa = algoritmo == "sarsa"
    con_retraso = tipo_recompensa == "retraso"
    if modo == "actuado":
        for tls in SEMAFOROS:
            traci.trafficlight.setProgram(tls, "actuado")

    # Un estado de control por semaforo
    agentes = {}
    for tls in SEMAFOROS:
        verdes, ambar, dur_ambar, verde_min = fases_verdes(tls)
        agentes[tls] = {"verdes": verdes, "ambar": ambar, "dur_ambar": dur_ambar,
                        "verde_min": verde_min, "verde": 0, "t_verde": 0,
                        "ambar_restante": 0, "s": None, "a": None,
                        "fase_previa": None, "r_acum": 0.0}
        if controla:
            traci.trafficlight.setPhase(tls, verdes[0])
            traci.trafficlight.setPhaseDuration(tls, 100000)   # el agente decide cuando cambiar
        agentes[tls]["fase_previa"] = traci.trafficlight.getPhase(tls)

    aprox = todas_las_aprox()
    for a in aprox:
        traci.edge.subscribe(a, [HALT, VEH, ESP, VEL])
    net_file, _ = comun.leer_cfg(CFG)
    vmax = velocidades_max(net_file)
    medidor = comun.MedidorEnlaces(net_file, ENLACES)   # spillback y colas por carril en los enlaces
    filas_fases = []
    pasos = 0
    cola_acum = 0.0
    cola_max = 0
    r_total = 0.0        # recompensa que ven los agentes (para aprender)
    decisiones = 0
    r_reporte = 0.0      # recompensa medida cada 5 s de reloj fijo, igual en los cuatro modos
    n_reporte = 0
    cambios = 0
    dq_max = 0.0
    filas_serie = []
    ret_retraso, ret_colas, spill_total = 0.0, 0.0, 0.0   # medidos cada segundo (ESPEC seccion 5)

    while traci.simulation.getMinExpectedNumber() > 0 and pasos < 6000:
        if pasos > 0 and pasos % PASO_CONTROL == 0:
            for tls in SEMAFOROS:
                r_reporte += recompensa(tls)
                n_reporte += 1
        if controla:
            for tls, ag in agentes.items():
                # Cada agente decide cada 5 s contados desde el inicio de su verde (la primera vez
                # a los 5 s de entrar el verde), igual que rl_semaforo.py: asi el verde minimo real
                # es 10 s y el maximo 60 s. En ambar no se decide.
                if ag["ambar_restante"] > 0 or ag["t_verde"] % PASO_CONTROL != 0:
                    continue
                if ag["t_verde"] == 0 and pasos > 0:
                    continue
                s2 = estado(tls, ag["verde"])
                a = None
                if ag["s"] is not None:
                    if con_retraso:     # retraso-segundos desde la decision anterior, entre 5
                        r = ag["r_acum"] / PASO_CONTROL
                    else:
                        r = recompensa(tls)
                    ag["r_acum"] = 0.0
                    r_total += r
                    decisiones += 1
                    if aprende:
                        q = q_vals(Q, tls, ag["s"])
                        if sarsa:       # a2 se elige antes de actualizar y es la que se ejecuta
                            a = elegir(Q, tls, s2, eps, True)
                            objetivo = q_vals(Q, tls, s2)[a]
                        else:
                            objetivo = max(q_vals(Q, tls, s2))
                        delta = ALPHA * (r + GAMMA * objetivo - q[ag["a"]])
                        q[ag["a"]] += delta
                        dq_max = max(dq_max, abs(delta))

                if a is None:
                    a = elegir(Q, tls, s2, eps, aprende)
                ag["s"], ag["a"] = s2, a

                minimo = ag["verde_min"][ag["verdes"][ag["verde"]]]
                cambiar = (a == 1 and ag["t_verde"] >= minimo) or ag["t_verde"] >= VERDE_MAX
                if cambiar:
                    f_actual = ag["verdes"][ag["verde"]]
                    traci.trafficlight.setPhase(tls, ag["ambar"][f_actual])
                    traci.trafficlight.setPhaseDuration(tls, ag["dur_ambar"][f_actual])
                    ag["ambar_restante"] = ag["dur_ambar"][f_actual]

        traci.simulationStep()
        pasos += 1
        lect = traci.edge.getAllSubscriptionResults()
        colas = [leer(lect, e, HALT) for e in aprox]
        cola_acum += sum(colas)
        cola_max = max(cola_max, sum(colas))
        medidor.paso(pasos)
        # retornos por segundo sobre todos los semaforos, iguales en los cuatro modos
        for tls, ag in agentes.items():
            r_paso = recompensa_paso(tls, lect, vmax)
            ret_retraso += r_paso
            if ag["s"] is not None:
                ag["r_acum"] += r_paso
        ret_colas -= W1 * sum(colas) + W2 * sum(leer(lect, e, ESP) for e in aprox)
        for e in ENLACES:
            spill_total += max(0, medidor.max_halting(e) - medidor.plazas[e] // 2)
        if serie is not None and pasos % PASO_SERIE == 0:
            filas_serie.append([pasos] + colas)

        fases_ahora = []
        for tls, ag in agentes.items():
            fase = traci.trafficlight.getPhase(tls)
            fases_ahora.append(fase)
            if fase != ag["fase_previa"] and fase in ag["verdes"]:   # entro un verde nuevo
                cambios += 1
            ag["fase_previa"] = fase
        if serie is not None and pasos <= comun.FIN_HORA:
            filas_fases.append([pasos] + fases_ahora)
        for tls, ag in agentes.items():
            if not controla:
                continue
            if ag["ambar_restante"] > 0:
                ag["ambar_restante"] -= 1
                if ag["ambar_restante"] == 0:      # termino el ambar: entra el siguiente verde
                    ag["verde"] = (ag["verde"] + 1) % len(ag["verdes"])
                    traci.trafficlight.setPhase(tls, ag["verdes"][ag["verde"]])
                    traci.trafficlight.setPhaseDuration(tls, 100000)
                    ag["t_verde"] = 0
            else:
                ag["t_verde"] += 1

    traci.close()
    if serie is not None:
        comun.guardar_serie(serie, ["t"] + aprox, filas_serie)
        comun.guardar_fases(serie.replace("serie_", "fases_", 1), list(SEMAFOROS), filas_fases)
    res = comun.leer_tripinfo(tripinfo, FLUJOS_CORREDOR)
    res.update({
        "cola_prom": round(cola_acum / max(1, pasos), 2),   # detenidos en todas las aproximaciones
        "cola_max": cola_max,
        "recompensa": round(r_reporte, 1),                    # medida cada 5 s en los cuatro modos
        "recompensa_decision": round(r_reporte / max(1, n_reporte), 3),
        "decisiones": decisiones if controla else n_reporte,
        "cambios_fase": cambios,                             # sumados sobre todos los semaforos
        "dq_max": round(dq_max, 4),
        "ret_retraso": round(ret_retraso, 1),
        "ret_colas": round(ret_colas, 1),
        "ret_spill": round(ret_retraso - W3 * spill_total, 1),
    })
    res.update(medidor.resumen())                             # spillback y colas por carril en los enlaces
    return res


def estados_totales(Q):
    return sum(len(Q[tls]) for tls in Q)


def evaluar_greedy(Q, seed, tripinfo=None):
    """Politica congelada (epsilon 0) sobre una copia de las Q-tables, sin alterar el RNG."""
    estado_rng = random.getstate()
    random.seed(seed)
    res = correr_episodio("demo", copy.deepcopy(Q), 0.0, False, 0, seed,
                          tripinfo=tripinfo or f"tripinfo_{ESCENARIO}_eval.xml")
    random.setstate(estado_rng)
    return res["timeloss_prom"], res["espera_prom"]


def hash_git():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              timeout=5, cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip()
    except Exception:
        return ""


def guardar_json(ruta, datos, indent=None):
    with open(ruta, "w") as f:
        json.dump(datos, f, indent=indent)


# ---------------- Entrenamiento (plan v2) ----------------
def entrenar(args, Q):
    """Entrena, valida, guarda checkpoints y publica la mejor Q-table (ESPEC secciones 3 y 4)."""
    alg = ALG_CORTO[args.algoritmo] + ("_colas" if args.recompensa == "colas" else "")
    tag = f"{ESCENARIO}_{alg}_s{args.seed}"
    val_seeds = [int(x) for x in args.val_seeds.split(",") if x.strip()]
    if args.eps_decay is None:      # plan v2: llega a 0.01 al 80 % de los episodios
        eps_decay, eps_min = EPS_MIN_V2 ** (1 / (0.8 * args.episodios)), EPS_MIN_V2
    else:                           # explicito: reproduce las corridas anteriores al plan v2
        eps_decay, eps_min = args.eps_decay, EPS_MIN

    os.makedirs("checkpoints", exist_ok=True)
    for viejo in glob.glob(os.path.join("checkpoints", f"{tag}_ep*.json")):
        if re.fullmatch(rf"{re.escape(tag)}_ep\d+\.json", os.path.basename(viejo)):
            os.remove(viejo)

    ruta_csv = f"resultados_{tag}.csv"
    campos = comun.CAMPOS + [f"val_{s}" for s in val_seeds] + CAMPOS_V2
    salida = open(ruta_csv, "w", newline="")      # se reescribe: la cola puede reintentar
    escritor = csv.DictWriter(salida, fieldnames=campos, extrasaction="ignore")
    escritor.writeheader()

    if not any(Q[tls] for tls in Q):
        print(f"Q-tables vacias: entrenamiento desde cero ({len(SEMAFOROS)} agentes independientes).")
    print(f"{args.algoritmo} / recompensa {args.recompensa} en {ESCENARIO}: {args.episodios} episodios, "
          f"base {args.seed}, eps_decay {eps_decay:.5f}, eps_min {eps_min}", flush=True)
    val_serie = []      # [ep, val_<s1>, val_<s2>, ..., val]
    eps = EPS_INICIAL
    for ep in range(1, args.episodios + 1):
        t0 = time.time()
        res = correr_episodio("train", Q, eps, args.gui, args.delay, args.seed + ep,
                              tripinfo=f"tripinfo_{tag}_train.xml",
                              algoritmo=args.algoritmo, tipo_recompensa=args.recompensa)
        fila = {"modo": "train", "episodio": ep, "semilla": args.seed + ep,
                "epsilon": round(eps, 3), "estados_q": estados_totales(Q), **res,
                "segundos": round(time.time() - t0, 1), "algoritmo": args.algoritmo,
                "recompensa": args.recompensa, "base": args.seed, "recompensa_u2": res["recompensa"]}
        texto_val = ""
        if args.eval_cada and val_seeds and (ep % args.eval_cada == 0 or ep == args.episodios):
            valores = []
            for s in val_seeds:
                tl, esp = evaluar_greedy(Q, s, tripinfo=f"tripinfo_{tag}_val.xml")
                fila[f"val_{s}"] = tl
                valores.append(tl)
                if s == val_seeds[0]:       # compatibilidad con graficar.py (eval intermedia)
                    fila["eval_timeloss"], fila["eval_espera"] = tl, esp
            fila["val"] = round(sum(valores) / len(valores), 3)
            val_serie.append([ep] + valores + [fila["val"]])
            guardar_json(os.path.join("checkpoints", f"{tag}_ep{ep:03d}.json"), Q)
            texto_val = f"  val={fila['val']:6.2f}s"
        print(f"Episodio {ep:3d}  eps={eps:.3f}  timeLoss={res['timeloss_prom']:6.2f}s  "
              f"espera={res['espera_prom']:6.2f}s  cola={res['cola_prom']:5.2f}  "
              f"R/dec={res['recompensa_decision']:7.2f}  estados={estados_totales(Q)}  "
              f"{fila['segundos']}s" + texto_val, flush=True)
        escritor.writerow(fila)
        salida.flush()
        eps = max(eps_min, eps * eps_decay)
    salida.close()

    # Politica publicada: checkpoint de menor val (empate: el mas tardio). Sin validacion, la final.
    if val_serie:
        mejor = min(val_serie, key=lambda v: (v[-1], -v[0]))
        ep_elegido, val_elegido = mejor[0], mejor[-1]
        with open(os.path.join("checkpoints", f"{tag}_ep{ep_elegido:03d}.json")) as f:
            Q_publicada = json.load(f)
    else:
        ep_elegido, val_elegido, Q_publicada = args.episodios, None, Q
    ruta_q = f"q_table_{tag}.json"
    guardar_json(ruta_q, Q_publicada)
    meta = {"escenario": ESCENARIO, "algoritmo": args.algoritmo, "recompensa": args.recompensa,
            "alg": alg, "tag": tag, "base": args.seed, "episodios": args.episodios,
            "ep_elegido": ep_elegido, "val_elegido": val_elegido, "val_serie": val_serie,
            "val_seeds": val_seeds, "eval_cada": args.eval_cada,
            "hiper": {"alpha": ALPHA, "gamma": GAMMA, "eps_inicial": EPS_INICIAL, "eps_decay": eps_decay,
                      "eps_min": eps_min, "w1": W1, "w2": W2, "w3": W3, "paso_control": PASO_CONTROL,
                      "verde_min": VERDE_MIN, "verde_min_giro": VERDE_MIN_GIRO, "verde_max": VERDE_MAX,
                      "bins_cola": [0, 3, 8]},
            "estados_q": estados_totales(Q_publicada), "python": sys.version.split()[0],
            "sumo": "1.25.0", "git": hash_git()}
    guardar_json(ruta_q.replace(".json", ".meta.json"), meta, indent=1)
    print(f"Q-tables publicadas en {ruta_q} (episodio {ep_elegido}, val {val_elegido})")


# ---------------- Main ----------------
def main():
    global ESCENARIO, CFG, SEMAFOROS, ENLACES, FLUJOS_CORREDOR, Q_FILE, RESULTADOS
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["baseline", "actuado", "train", "demo"])
    ap.add_argument("--escenario", choices=sorted(ESCENARIOS), default="corredor")
    ap.add_argument("--algoritmo", choices=["qlearning", "sarsa"], default="qlearning")
    ap.add_argument("--recompensa", choices=["retraso", "colas"], default="retraso",
                    help="recompensa de entrenamiento (ESPEC seccion 2)")
    ap.add_argument("--episodios", type=int, default=200)
    ap.add_argument("--eps-decay", type=float, default=None,
                    help="decaimiento de epsilon por episodio; si se da, EPS_MIN 0.05 como antes del plan v2")
    ap.add_argument("--eval-cada", type=int, default=10,
                    help="cada cuantos episodios de train se valida la politica congelada (0 = nunca)")
    ap.add_argument("--val-seeds", default="999,1999",
                    help="semillas de validacion, fuera del entrenamiento y de la evaluacion final")
    ap.add_argument("--desde-cero", action="store_true", help="empieza con las Q-tables vacias")
    ap.add_argument("--qtable", default=None, help="Q-table para demo (por defecto q_table_<esc>.json)")
    ap.add_argument("--serie", action="store_true",
                    help="guarda la cola por aproximacion cada 60 s (serie_<esc>_<modo>_s<semilla>.csv)")
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--delay", type=int, default=30, help="ms por paso en sumo-gui")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    random.seed(args.seed)      # tambien en baseline/demo: el desempate de acciones usa random

    ESCENARIO = args.escenario
    CFG = ESCENARIOS[ESCENARIO]["cfg"]
    SEMAFOROS = ESCENARIOS[ESCENARIO]["semaforos"]
    ENLACES = ESCENARIOS[ESCENARIO]["enlaces"]
    FLUJOS_CORREDOR = ESCENARIOS[ESCENARIO]["flujos_corredor"]
    Q_FILE = f"q_table_{ESCENARIO}.json"
    RESULTADOS = f"resultados_{ESCENARIO}.csv"

    Q = {tls: {} for tls in SEMAFOROS}
    if args.modo == "train":
        alg = ALG_CORTO[args.algoritmo] + ("_colas" if args.recompensa == "colas" else "")
        previa = f"q_table_{ESCENARIO}_{alg}_s{args.seed}.json"
        if not args.desde_cero and os.path.exists(previa):     # continua la corrida publicada
            with open(previa) as f:
                Q = json.load(f)
        entrenar(args, Q)
        return

    if args.modo == "demo":
        Q_FILE = args.qtable or Q_FILE
        if os.path.exists(Q_FILE):
            with open(Q_FILE) as f:
                Q = json.load(f)
        if not any(Q[tls] for tls in Q):
            sys.exit(f"No hay Q-tables entrenadas en {Q_FILE}. Ejecuta primero: python rl_corredor.py train")

    salida, escritor = comun.abrir_csv(RESULTADOS)
    serie = (f"serie_{ESCENARIO}_{args.modo}_s{args.seed}.csv" if args.serie else None)

    if args.modo in ("baseline", "actuado"):
        res = correr_episodio(args.modo, Q, 0.0, args.gui, args.delay, args.seed, serie=serie)
        nombre = "TIEMPO FIJO" if args.modo == "baseline" else "ACTUADO (SUMO)"
        print(f"{nombre} ({len(SEMAFOROS)} semaforos):", res)
        escritor.writerow({"modo": args.modo, "episodio": 0, "semilla": args.seed, "epsilon": 0, **res})
    else:  # demo
        res = correr_episodio("demo", Q, 0.0, args.gui, args.delay, args.seed, serie=serie)
        print("AGENTES RL (tabular independiente):", res)
        escritor.writerow({"modo": "demo", "episodio": 0, "semilla": args.seed, "epsilon": 0,
                           "estados_q": estados_totales(Q), **res})

    salida.close()


if __name__ == "__main__":
    main()
