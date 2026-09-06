"""
rl_corredor.py - Escenarios con VARIOS semaforos, un agente Q-learning independiente
por cruce (sin comunicacion entre ellos; es la antesala del modulo U4).

Modos (igual que rl_semaforo.py):
  python rl_corredor.py baseline                 # todos los semaforos a tiempo fijo (con offsets tuneados)
  python rl_corredor.py actuado                  # todos actuados (SUMO nativo), sin coordinacion
  python rl_corredor.py train --episodios 40     # entrena todos los agentes a la vez
  python rl_corredor.py demo --gui               # agentes entrenados en sumo-gui

Escenarios (--escenario, por defecto "corredor"):
  corredor  prueba 3: dos cruces sobre una avenida E-O separados 300 m
  red       prueba 4: rotonda + tres cruces semaforizados, avenida cargada y
            transversales ligeras (la rotonda no lleva semaforo: cede el paso)

Cada agente ve solo su cruce: estado = cola discretizada en sus 4 aproximaciones
+ su fase verde activa. Recompensa local = -(w1*colas propias + w2*esperas propias).
Las decisiones son cada 5 s; mientras un semaforo esta en ambar, ese agente no decide.
Un episodio es una hora simulada completa con la misma red y demanda; entre episodios
cambian solo epsilon, la semilla de SUMO y las Q-tables heredadas.
"""
import os
import sys
import copy
import json
import random
import argparse

# ---------------- TraCI ----------------
try:
    import traci
    import sumolib
except ImportError:
    if "SUMO_HOME" in os.environ:
        sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
        import traci
        import sumolib
    else:
        sys.exit("No encuentro TraCI. Define la variable SUMO_HOME o ejecuta: pip install traci sumolib")

import comun

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

# Se definen en main() segun --escenario
ESCENARIO = "corredor"
CFG = ESCENARIOS["corredor"]["cfg"]
SEMAFOROS = ESCENARIOS["corredor"]["semaforos"]
ENLACES = ESCENARIOS["corredor"]["enlaces"]
FLUJOS_CORREDOR = ESCENARIOS["corredor"]["flujos_corredor"]
Q_FILE = "q_table_corredor.json"
RESULTADOS = "resultados_corredor.csv"
UMBRAL_SPILLBACK = 0.9   # hay spillback cuando la cola detenida ocupa al menos esta fraccion del enlace

# ---------------- Parametros ----------------
PASO_CONTROL = 5      # segundos entre decisiones de cada agente
VERDE_MIN = 10        # verde minimo antes de permitir un cambio (fases principales)
VERDE_MIN_GIRO = 5    # verde minimo en fases de giro protegido (pocos movimientos en verde)
VERDE_MAX = 60        # verde maximo: se fuerza el cambio
W1, W2 = 1.0, 0.01    # pesos de la recompensa
ALPHA, GAMMA = 0.1, 0.9
EPS_INICIAL, EPS_DECAY, EPS_MIN = 1.0, 0.9, 0.05
PASO_SERIE = 60       # cada cuantos segundos se guarda la cola por aproximacion


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
    cola = sum(traci.edge.getLastStepHaltingNumber(e) for e in SEMAFOROS[tls])
    espera = sum(traci.edge.getWaitingTime(e) for e in SEMAFOROS[tls])
    return -(W1 * cola + W2 * espera)


def q_vals(Q, tls, s):
    return Q[tls].setdefault(clave(s), [0.0, 0.0])


def mejor_accion(Q, tls, s):
    q = q_vals(Q, tls, s)
    if q[0] == q[1]:
        return random.randint(0, 1)
    return 0 if q[0] > q[1] else 1


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
def correr_episodio(modo, Q, eps, gui, delay, seed, tripinfo=None, serie=None):
    """Corre una hora simulada. modo: baseline (fijo con offsets), actuado (SUMO), train o demo."""
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
    traci.start(cmd)

    controla = modo in ("train", "demo")
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
                        "fase_previa": None}
        if controla:
            traci.trafficlight.setPhase(tls, verdes[0])
            traci.trafficlight.setPhaseDuration(tls, 100000)   # el agente decide cuando cambiar
        agentes[tls]["fase_previa"] = traci.trafficlight.getPhase(tls)

    aprox = todas_las_aprox()
    net_file, _ = comun.leer_cfg(CFG)
    capacidad = {e: comun.capacidad_enlace(net_file, e) for e in ENLACES}
    pasos = 0
    cola_acum = 0.0
    cola_max = 0
    r_total = 0.0        # recompensa que ven los agentes (para aprender)
    decisiones = 0
    r_reporte = 0.0      # recompensa medida cada 5 s de reloj fijo, igual en los cuatro modos (para comparar)
    n_reporte = 0
    cambios = 0
    dq_max = 0.0
    pasos_spillback = 0  # pasos en que algun enlace entre cruces esta lleno de vehiculos detenidos
    cola_max_enlace = 0
    filas_serie = []

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
                if ag["s"] is not None:
                    r = recompensa(tls)
                    r_total += r
                    decisiones += 1
                    if modo == "train":
                        q = q_vals(Q, tls, ag["s"])
                        delta = ALPHA * (r + GAMMA * max(q_vals(Q, tls, s2)) - q[ag["a"]])
                        q[ag["a"]] += delta
                        dq_max = max(dq_max, abs(delta))

                if modo == "train" and random.random() < eps:
                    a = random.randint(0, 1)
                else:
                    a = mejor_accion(Q, tls, s2)
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
        colas = [traci.edge.getLastStepHaltingNumber(e) for e in aprox]
        cola_acum += sum(colas)
        cola_max = max(cola_max, sum(colas))
        detenidos_enlace = {e: traci.edge.getLastStepHaltingNumber(e) for e in ENLACES}
        cola_max_enlace = max(cola_max_enlace, max(detenidos_enlace.values()))
        if any(detenidos_enlace[e] >= UMBRAL_SPILLBACK * capacidad[e] for e in ENLACES):
            pasos_spillback += 1
        if serie is not None and pasos % PASO_SERIE == 0:
            filas_serie.append([pasos] + colas)

        for tls, ag in agentes.items():
            fase = traci.trafficlight.getPhase(tls)
            if fase != ag["fase_previa"] and fase in ag["verdes"]:   # entro un verde nuevo
                cambios += 1
            ag["fase_previa"] = fase
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
    res = comun.leer_tripinfo(tripinfo, FLUJOS_CORREDOR)
    res.update({
        "cola_prom": round(cola_acum / max(1, pasos), 2),   # detenidos en todas las aproximaciones
        "cola_max": cola_max,
        "recompensa": round(r_reporte, 1),                    # medida cada 5 s en los cuatro modos
        "recompensa_decision": round(r_reporte / max(1, n_reporte), 3),
        "decisiones": decisiones if controla else n_reporte,
        "cambios_fase": cambios,                             # sumados sobre todos los semaforos
        "dq_max": round(dq_max, 4),
        "spillback_tasa": round(pasos_spillback / max(1, pasos), 4),  # fraccion de la hora con un enlace lleno
        "cola_max_enlace": cola_max_enlace,                   # mayor cola detenida en un enlace entre cruces
    })
    return res


def estados_totales(Q):
    return sum(len(Q[tls]) for tls in Q)


def evaluar_greedy(Q, seed):
    """Politica congelada (epsilon 0) sobre una copia de las Q-tables, sin alterar el RNG."""
    estado_rng = random.getstate()
    random.seed(seed)
    res = correr_episodio("demo", copy.deepcopy(Q), 0.0, False, 0, seed,
                          tripinfo=f"tripinfo_{ESCENARIO}_eval.xml")
    random.setstate(estado_rng)
    return res["timeloss_prom"], res["espera_prom"]


# ---------------- Main ----------------
def main():
    global ESCENARIO, CFG, SEMAFOROS, ENLACES, FLUJOS_CORREDOR, Q_FILE, RESULTADOS
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["baseline", "actuado", "train", "demo"])
    ap.add_argument("--escenario", choices=sorted(ESCENARIOS), default="corredor")
    ap.add_argument("--episodios", type=int, default=40)
    ap.add_argument("--eps-decay", type=float, default=EPS_DECAY,
                    help="decaimiento de epsilon por episodio (mas lento = mas exploracion)")
    ap.add_argument("--eval-cada", type=int, default=5,
                    help="cada cuantos episodios de train se evalua la politica congelada (0 = nunca)")
    ap.add_argument("--eval-seed", type=int, default=999,
                    help="semilla fija de esa evaluacion, fuera del entrenamiento y de la evaluacion final")
    ap.add_argument("--desde-cero", action="store_true", help="borra las Q-tables antes de entrenar")
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
    if args.modo == "train" and args.desde_cero and os.path.exists(Q_FILE):
        os.remove(Q_FILE)
    if os.path.exists(Q_FILE):
        with open(Q_FILE) as f:
            Q = json.load(f)

    salida, escritor = comun.abrir_csv(RESULTADOS)
    serie = (f"serie_{ESCENARIO}_{args.modo}_s{args.seed}.csv" if args.serie else None)

    if args.modo in ("baseline", "actuado"):
        res = correr_episodio(args.modo, Q, 0.0, args.gui, args.delay, args.seed, serie=serie)
        nombre = "TIEMPO FIJO" if args.modo == "baseline" else "ACTUADO (SUMO)"
        print(f"{nombre} ({len(SEMAFOROS)} semaforos):", res)
        escritor.writerow({"modo": args.modo, "episodio": 0, "semilla": args.seed, "epsilon": 0, **res})

    elif args.modo == "train":
        if not any(Q[tls] for tls in Q):
            print(f"Q-tables vacias: entrenamiento desde cero ({len(SEMAFOROS)} agentes independientes).")
        eps = EPS_INICIAL
        for ep in range(1, args.episodios + 1):
            res = correr_episodio("train", Q, eps, args.gui, args.delay, args.seed + ep)
            fila = {"modo": "train", "episodio": ep, "semilla": args.seed + ep,
                    "epsilon": round(eps, 3), "estados_q": estados_totales(Q), **res}
            if args.eval_cada and (ep % args.eval_cada == 0 or ep == args.episodios):
                fila["eval_timeloss"], fila["eval_espera"] = evaluar_greedy(Q, args.eval_seed)
            print(f"Episodio {ep:3d}  eps={eps:.2f}  timeLoss={res['timeloss_prom']:6.2f}s  "
                  f"espera={res['espera_prom']:6.2f}s  cola={res['cola_prom']:5.2f}  "
                  f"R/dec={res['recompensa_decision']:7.2f}  estados={estados_totales(Q)}"
                  + (f"  eval timeLoss={fila['eval_timeloss']:6.2f}s" if "eval_timeloss" in fila else ""))
            escritor.writerow(fila)
            salida.flush()
            eps = max(EPS_MIN, eps * args.eps_decay)
            with open(Q_FILE, "w") as f:
                json.dump(Q, f)
        print(f"Q-tables guardadas en {Q_FILE}")

    else:  # demo
        if not any(Q[tls] for tls in Q):
            sys.exit("No hay Q-tables entrenadas. Ejecuta primero: python rl_corredor.py train")
        res = correr_episodio("demo", Q, 0.0, args.gui, args.delay, args.seed, serie=serie)
        print("AGENTES RL (Q-learning independiente):", res)
        escritor.writerow({"modo": "demo", "episodio": 0, "semilla": args.seed, "epsilon": 0,
                           "estados_q": estados_totales(Q), **res})

    salida.close()


if __name__ == "__main__":
    main()
