"""
rl_semaforo.py - Control adaptativo de un semaforo con Q-learning sobre SUMO (TraCI).

Modos:
  python rl_semaforo.py baseline                 # semaforo de tiempo fijo (linea base), sin GUI
  python rl_semaforo.py baseline --gui           # lo mismo, pero viendolo en sumo-gui
  python rl_semaforo.py train --episodios 40     # entrena el agente Q-learning (sin GUI, rapido)
  python rl_semaforo.py demo --gui               # corre el agente ya entrenado en sumo-gui

Escenarios (--escenario, por defecto "cruce"):
  cruce   prueba 1: cruce simple, 1 carril por sentido, 2 fases verdes
  cruce2  prueba 2: 2 carriles por sentido con giro a la izquierda protegido, 4 fases verdes

Estado  : cola discretizada en cada aproximacion (N, S, E, O) + fase verde activa
Accion  : 0 = mantener la fase verde, 1 = cambiar a la otra fase verde (pasando por ambar)
Recompensa: r = -(w1 * suma de colas + w2 * suma de tiempos de espera)
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
# Cada escenario define su configuracion, el id del semaforo y las vias que llegan al cruce.
ESCENARIOS = {
    "cruce":  {"cfg": "cruce.sumocfg",  "tls": "semaforo_C", "aprox": ["N_C", "S_C", "E_C", "W_C"]},
    "cruce2": {"cfg": "cruce2.sumocfg", "tls": "semaforo_C", "aprox": ["N_C", "S_C", "E_C", "W_C"]},
}

# Se definen en main() segun --escenario
ESCENARIO = "cruce"
CFG = ESCENARIOS["cruce"]["cfg"]
TLS = ESCENARIOS["cruce"]["tls"]
APROX = ESCENARIOS["cruce"]["aprox"]
Q_FILE = "q_table_cruce.json"
RESULTADOS = "resultados_cruce.csv"

# ---------------- Parametros ----------------
PASO_CONTROL = 5      # segundos entre decisiones del agente
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


def estado(verde_idx):
    colas = tuple(bin_cola(traci.edge.getLastStepHaltingNumber(e)) for e in APROX)
    return colas + (verde_idx,)


def clave(s):
    return ",".join(str(x) for x in s)


def cola_total():
    return sum(traci.edge.getLastStepHaltingNumber(e) for e in APROX)


def espera_total():
    return sum(traci.edge.getWaitingTime(e) for e in APROX)


def recompensa():
    return -(W1 * cola_total() + W2 * espera_total())


def q_vals(Q, s):
    return Q.setdefault(clave(s), [0.0, 0.0])


def mejor_accion(Q, s):
    q = q_vals(Q, s)
    if q[0] == q[1]:
        return random.randint(0, 1)
    return 0 if q[0] > q[1] else 1


def fases_verdes():
    """Lee el programa del semaforo y devuelve las fases verdes, su ambar siguiente
    y el verde minimo de cada fase (mas corto en fases de giro protegido)."""
    logica = traci.trafficlight.getAllProgramLogics(TLS)[0]
    fases = logica.phases
    verdes = [i for i, p in enumerate(fases) if ("G" in p.state or "g" in p.state) and "y" not in p.state]
    ambar = {i: (i + 1) % len(fases) for i in verdes}
    dur_ambar = {i: max(1, int(fases[ambar[i]].duration)) for i in verdes}
    verde_min = {i: VERDE_MIN if sum(1 for c in fases[i].state if c in "Gg") > 2 else VERDE_MIN_GIRO
                 for i in verdes}
    return verdes, ambar, dur_ambar, verde_min


def poner_fase(fase, duracion):
    traci.trafficlight.setPhase(TLS, fase)
    traci.trafficlight.setPhaseDuration(TLS, duracion)


def leer_tripinfo(archivo):
    raiz = ET.parse(archivo).getroot()
    viajes = raiz.findall("tripinfo")
    n = max(1, len(viajes))
    espera = sum(float(v.get("waitingTime")) for v in viajes) / n
    perdida = sum(float(v.get("timeLoss")) for v in viajes) / n
    return len(viajes), espera, perdida


# ---------------- Episodio ----------------
def correr_episodio(modo, Q, eps, gui, delay, seed, gamma=GAMMA):
    binario = sumolib.checkBinary("sumo-gui" if gui else "sumo")
    tripinfo = f"tripinfo_{ESCENARIO}_{modo}.xml"
    cmd = [binario, "-c", CFG, "--seed", str(seed),
           "--tripinfo-output", tripinfo, "--tripinfo-output.write-unfinished", "true"]
    if gui:
        cmd += ["--start", "--quit-on-end", "--delay", str(delay)]
        vista = f"vista_{ESCENARIO}.xml" if os.path.exists(f"vista_{ESCENARIO}.xml") else "vista.xml"
        if os.path.exists(vista):
            cmd += ["--gui-settings-file", vista]
    traci.start(cmd)

    verdes, ambar, dur_ambar, verde_min = fases_verdes()
    verde = 0                     # indice dentro de la lista 'verdes'
    if modo != "baseline":
        poner_fase(verdes[verde], 100000)   # el agente decide cuando cambiar
    t_verde = 0
    pasos = 0
    cola_acum = 0.0
    r_total = 0.0
    cambios = 0
    s = estado(verde)

    def avanzar(n):
        nonlocal pasos, cola_acum
        for _ in range(n):
            traci.simulationStep()
            pasos += 1
            cola_acum += cola_total()

    while traci.simulation.getMinExpectedNumber() > 0 and pasos < 6000:
        if modo == "baseline":
            avanzar(PASO_CONTROL)
            continue

        if modo == "train" and random.random() < eps:
            a = random.randint(0, 1)
        else:
            a = mejor_accion(Q, s)

        cambiar = (a == 1 and t_verde >= verde_min[verdes[verde]]) or t_verde >= VERDE_MAX
        if cambiar:
            f_actual = verdes[verde]
            poner_fase(ambar[f_actual], dur_ambar[f_actual])
            avanzar(dur_ambar[f_actual])
            verde = (verde + 1) % len(verdes)
            poner_fase(verdes[verde], 100000)
            t_verde = 0
            cambios += 1

        avanzar(PASO_CONTROL)
        t_verde += PASO_CONTROL
        r = recompensa()
        r_total += r
        s2 = estado(verde)

        if modo == "train":
            q = q_vals(Q, s)
            q[a] += ALPHA * (r + gamma * max(q_vals(Q, s2)) - q[a])
        s = s2

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
    global ESCENARIO, CFG, TLS, APROX, Q_FILE, RESULTADOS
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["baseline", "train", "demo"])
    ap.add_argument("--escenario", choices=sorted(ESCENARIOS), default="cruce")
    ap.add_argument("--episodios", type=int, default=40)
    ap.add_argument("--eps-decay", type=float, default=EPS_DECAY,
                    help="decaimiento de epsilon por episodio (mas lento = mas exploracion)")
    ap.add_argument("--gamma", type=float, default=GAMMA,
                    help="factor de descuento (mas alto = horizonte mas largo)")
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--delay", type=int, default=30, help="ms por paso en sumo-gui")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    random.seed(args.seed)      # tambien en baseline/demo: el desempate de acciones usa random

    ESCENARIO = args.escenario
    CFG = ESCENARIOS[ESCENARIO]["cfg"]
    TLS = ESCENARIOS[ESCENARIO]["tls"]
    APROX = ESCENARIOS[ESCENARIO]["aprox"]
    Q_FILE = f"q_table_{ESCENARIO}.json"
    RESULTADOS = f"resultados_{ESCENARIO}.csv"

    Q = {}
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
        print("BASELINE (tiempo fijo):", res)
        escritor.writerow({"modo": "baseline", "episodio": 0, "epsilon": 0, **res})

    elif args.modo == "train":
        if not Q:
            print("Q-table vacia: entrenamiento desde cero.")
        eps = EPS_INICIAL
        for ep in range(1, args.episodios + 1):
            res = correr_episodio("train", Q, eps, args.gui, args.delay, args.seed + ep, args.gamma)
            print(f"Episodio {ep:3d}  eps={eps:.2f}  espera={res['espera_prom']:6.2f}s  "
                  f"timeLoss={res['timeloss_prom']:6.2f}s  cola={res['cola_prom']:5.2f}  "
                  f"R={res['recompensa']:9.1f}  estados={len(Q)}")
            escritor.writerow({"modo": "train", "episodio": ep, "epsilon": round(eps, 3), **res})
            salida.flush()
            eps = max(EPS_MIN, eps * args.eps_decay)
            with open(Q_FILE, "w") as f:
                json.dump(Q, f)
        print(f"Q-table guardada en {Q_FILE} ({len(Q)} estados)")

    else:  # demo
        if not Q:
            sys.exit("No hay Q-table entrenada. Ejecuta primero: python rl_semaforo.py train")
        res = correr_episodio("demo", Q, 0.0, args.gui, args.delay, args.seed)
        print("AGENTE RL (Q-learning):", res)
        escritor.writerow({"modo": "demo", "episodio": 0, "epsilon": 0, **res})

    salida.close()


if __name__ == "__main__":
    main()
