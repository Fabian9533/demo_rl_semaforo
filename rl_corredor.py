"""
rl_corredor.py - Escenarios con VARIOS semaforos, un agente Q-learning independiente
por cruce (sin comunicacion entre ellos; es la antesala del modulo U4).

Modos (igual que rl_semaforo.py):
  python rl_corredor.py baseline                 # todos los semaforos a tiempo fijo
  python rl_corredor.py train --episodios 40     # entrena todos los agentes a la vez
  python rl_corredor.py demo --gui               # agentes entrenados en sumo-gui

Escenarios (--escenario, por defecto "corredor"):
  corredor  prueba 3: dos cruces sobre una avenida E-O separados 300 m
  red       prueba 4: rotonda + tres cruces semaforizados, avenida cargada y
            transversales ligeras (la rotonda no lleva semaforo: cede el paso)

Cada agente ve solo su cruce: estado = cola discretizada en sus 4 aproximaciones
+ su fase verde activa. Recompensa local = -(w1*colas propias + w2*esperas propias).
Las decisiones son cada 5 s; mientras un semaforo esta en ambar, ese agente no decide.
"""
import os
import sys
import csv
import json
import random
import argparse
import xml.etree.ElementTree as ET

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

# ---------------- Escenarios ----------------
# Cada escenario define su configuracion y, por semaforo, los edges que llegan al cruce.
ESCENARIOS = {
    "corredor": {
        "cfg": "corredor.sumocfg",
        "semaforos": {
            "semaforo_C1": ["W_C1", "C2_C1", "N1_C1", "S1_C1"],
            "semaforo_C2": ["C1_C2", "E_C2", "N2_C2", "S2_C2"],
        },
    },
    "red": {
        "cfg": "red.sumocfg",
        "semaforos": {
            "semaforo_C1": ["RE_C1", "C2_C1", "N1_C1", "S1_C1"],
            "semaforo_C2": ["C1_C2", "C3_C2", "N2_C2", "S2_C2"],
            "semaforo_C3": ["C2_C3", "E_C3", "N3_C3", "S3_C3"],
        },
    },
}

# Se definen en main() segun --escenario
ESCENARIO = "corredor"
CFG = ESCENARIOS["corredor"]["cfg"]
SEMAFOROS = ESCENARIOS["corredor"]["semaforos"]
Q_FILE = "q_table_corredor.json"
RESULTADOS = "resultados_corredor.csv"

# ---------------- Parametros ----------------
PASO_CONTROL = 5      # segundos entre decisiones de cada agente
VERDE_MIN = 10        # verde minimo antes de permitir un cambio (fases principales)
VERDE_MIN_GIRO = 5    # verde minimo en fases de giro protegido (pocos movimientos en verde)
VERDE_MAX = 60        # verde maximo: se fuerza el cambio
W1, W2 = 1.0, 0.01    # pesos de la recompensa
ALPHA, GAMMA = 0.1, 0.9
EPS_INICIAL, EPS_DECAY, EPS_MIN = 1.0, 0.9, 0.05


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


def estado(tls, verde_idx):
    colas = tuple(bin_cola(traci.edge.getLastStepHaltingNumber(e)) for e in SEMAFOROS[tls])
    return colas + (verde_idx,)


def clave(s):
    return ",".join(str(x) for x in s)


def recompensa(tls):
    cola = sum(traci.edge.getLastStepHaltingNumber(e) for e in SEMAFOROS[tls])
    espera = sum(traci.edge.getWaitingTime(e) for e in SEMAFOROS[tls])
    return -(W1 * cola + W2 * espera)


def cola_total():
    return sum(traci.edge.getLastStepHaltingNumber(e) for aprox in SEMAFOROS.values() for e in aprox)


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


def leer_tripinfo(archivo):
    raiz = ET.parse(archivo).getroot()
    viajes = raiz.findall("tripinfo")
    n = max(1, len(viajes))
    espera = sum(float(v.get("waitingTime")) for v in viajes) / n
    perdida = sum(float(v.get("timeLoss")) for v in viajes) / n
    return len(viajes), espera, perdida


# ---------------- Episodio ----------------
def correr_episodio(modo, Q, eps, gui, delay, seed):
    binario = sumolib.checkBinary("sumo-gui" if gui else "sumo")
    tripinfo = f"tripinfo_{ESCENARIO}_{modo}.xml"
    cmd = [binario, "-c", CFG, "--seed", str(seed),
           "--tripinfo-output", tripinfo, "--tripinfo-output.write-unfinished", "true"]
    if gui:
        cmd += ["--start", "--quit-on-end", "--delay", str(delay)]
        if os.path.exists(f"vista_{ESCENARIO}.xml"):
            cmd += ["--gui-settings-file", f"vista_{ESCENARIO}.xml"]
    traci.start(cmd)

    # Un estado de control por semaforo
    agentes = {}
    for tls in SEMAFOROS:
        verdes, ambar, dur_ambar, verde_min = fases_verdes(tls)
        agentes[tls] = {"verdes": verdes, "ambar": ambar, "dur_ambar": dur_ambar,
                        "verde_min": verde_min, "verde": 0, "t_verde": 0,
                        "ambar_restante": 0, "s": None, "a": None}
        if modo != "baseline":
            traci.trafficlight.setPhase(tls, verdes[0])
            traci.trafficlight.setPhaseDuration(tls, 100000)   # el agente decide cuando cambiar

    pasos = 0
    cola_acum = 0.0
    r_total = 0.0
    cambios = 0

    while traci.simulation.getMinExpectedNumber() > 0 and pasos < 6000:
        if modo != "baseline" and pasos % PASO_CONTROL == 0:
            for tls, ag in agentes.items():
                if ag["ambar_restante"] > 0:
                    continue                      # en ambar no se decide
                s2 = estado(tls, ag["verde"])
                if ag["s"] is not None:
                    r = recompensa(tls)
                    r_total += r
                    if modo == "train":
                        q = q_vals(Q, tls, ag["s"])
                        q[ag["a"]] += ALPHA * (r + GAMMA * max(q_vals(Q, tls, s2)) - q[ag["a"]])

                if modo == "train" and random.random() < eps:
                    a = random.randint(0, 1)
                else:
                    a = mejor_accion(Q, tls, s2)
                ag["s"], ag["a"] = s2, a

                cambiar = (a == 1 and ag["t_verde"] >= ag["verde_min"][ag["verdes"][ag["verde"]]]) or ag["t_verde"] >= VERDE_MAX
                if cambiar:
                    f_actual = ag["verdes"][ag["verde"]]
                    traci.trafficlight.setPhase(tls, ag["ambar"][f_actual])
                    traci.trafficlight.setPhaseDuration(tls, ag["dur_ambar"][f_actual])
                    ag["ambar_restante"] = ag["dur_ambar"][f_actual]
                    cambios += 1

        traci.simulationStep()
        pasos += 1
        cola_acum += cola_total()

        if modo != "baseline":
            for tls, ag in agentes.items():
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
    n_veh, espera, perdida = leer_tripinfo(tripinfo)
    return {
        "vehiculos": n_veh,
        "espera_prom": round(espera, 2),        # s de espera por vehiculo (detenido)
        "timeloss_prom": round(perdida, 2),     # s de retraso por vehiculo vs. flujo libre
        "cola_prom": round(cola_acum / max(1, pasos), 2),
        "recompensa": round(r_total, 1),
        "cambios_fase": cambios,
    }


# ---------------- Main ----------------
def main():
    global ESCENARIO, CFG, SEMAFOROS, Q_FILE, RESULTADOS
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["baseline", "train", "demo"])
    ap.add_argument("--escenario", choices=sorted(ESCENARIOS), default="corredor")
    ap.add_argument("--episodios", type=int, default=40)
    ap.add_argument("--eps-decay", type=float, default=EPS_DECAY,
                    help="decaimiento de epsilon por episodio (mas lento = mas exploracion)")
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--delay", type=int, default=30, help="ms por paso en sumo-gui")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    random.seed(args.seed)      # tambien en baseline/demo: el desempate de acciones usa random

    ESCENARIO = args.escenario
    CFG = ESCENARIOS[ESCENARIO]["cfg"]
    SEMAFOROS = ESCENARIOS[ESCENARIO]["semaforos"]
    Q_FILE = f"q_table_{ESCENARIO}.json"
    RESULTADOS = f"resultados_{ESCENARIO}.csv"

    Q = {tls: {} for tls in SEMAFOROS}
    if os.path.exists(Q_FILE):
        with open(Q_FILE) as f:
            Q = json.load(f)

    nuevo = not os.path.exists(RESULTADOS)
    salida = open(RESULTADOS, "a", newline="")
    campos = ["modo", "episodio", "epsilon", "vehiculos", "espera_prom", "timeloss_prom",
              "cola_prom", "recompensa", "cambios_fase"]
    escritor = csv.DictWriter(salida, fieldnames=campos)
    if nuevo:
        escritor.writeheader()

    if args.modo == "baseline":
        res = correr_episodio("baseline", Q, 0.0, args.gui, args.delay, args.seed)
        print(f"BASELINE (tiempo fijo, {len(SEMAFOROS)} semaforos):", res)
        escritor.writerow({"modo": "baseline", "episodio": 0, "epsilon": 0, **res})

    elif args.modo == "train":
        if not any(Q[tls] for tls in Q):
            print(f"Q-tables vacias: entrenamiento desde cero ({len(SEMAFOROS)} agentes independientes).")
        eps = EPS_INICIAL
        for ep in range(1, args.episodios + 1):
            res = correr_episodio("train", Q, eps, args.gui, args.delay, args.seed + ep)
            estados = sum(len(Q[tls]) for tls in Q)
            print(f"Episodio {ep:3d}  eps={eps:.2f}  espera={res['espera_prom']:6.2f}s  "
                  f"timeLoss={res['timeloss_prom']:6.2f}s  cola={res['cola_prom']:5.2f}  "
                  f"R={res['recompensa']:9.1f}  estados={estados}")
            escritor.writerow({"modo": "train", "episodio": ep, "epsilon": round(eps, 3), **res})
            salida.flush()
            eps = max(EPS_MIN, eps * args.eps_decay)
            with open(Q_FILE, "w") as f:
                json.dump(Q, f)
        print(f"Q-tables guardadas en {Q_FILE}")

    else:  # demo
        if not any(Q[tls] for tls in Q):
            sys.exit("No hay Q-tables entrenadas. Ejecuta primero: python rl_corredor.py train")
        res = correr_episodio("demo", Q, 0.0, args.gui, args.delay, args.seed)
        print("AGENTES RL (Q-learning independiente):", res)
        escritor.writerow({"modo": "demo", "episodio": 0, "epsilon": 0, **res})

    salida.close()


if __name__ == "__main__":
    main()
