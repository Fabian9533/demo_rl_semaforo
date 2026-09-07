"""
rl_semaforo.py - Control adaptativo de un semaforo con Q-learning sobre SUMO (TraCI).

Modos:
  python rl_semaforo.py baseline                 # semaforo de tiempo fijo (linea base), sin GUI
  python rl_semaforo.py actuado                  # semaforo actuado nativo de SUMO (segunda referencia)
  python rl_semaforo.py baseline --gui           # lo mismo, pero viendolo en sumo-gui
  python rl_semaforo.py train --episodios 40     # entrena el agente Q-learning (sin GUI, rapido)
  python rl_semaforo.py demo --gui               # corre el agente ya entrenado en sumo-gui

Escenarios (--escenario, por defecto "cruce"):
  cruce   prueba 1: cruce simple, 1 carril por sentido, 2 fases verdes
  cruce2  prueba 2: 2 carriles por sentido con giro a la izquierda protegido, 4 fases verdes

Estado  : cola discretizada en cada aproximacion (N, S, E, O) + fase verde activa
Accion  : 0 = mantener la fase verde, 1 = pasar a la siguiente fase verde (pasando por ambar)
Recompensa: r = -(w1 * suma de colas + w2 * suma de tiempos de espera)

Un episodio es una hora simulada completa (0-3600 s de demanda mas el vaciado de la
red, tope 6000 pasos) sobre la misma red y la misma demanda. Entre episodios cambian
solo epsilon, la semilla de SUMO (semilla base + numero de episodio) y la Q-table que
el agente hereda del episodio anterior. Cada --eval-cada episodios se evalua la
politica congelada (epsilon 0) con una semilla fija, sin tocar la Q-table.
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


def colas():
    return [traci.edge.getLastStepHaltingNumber(e) for e in APROX]


def estado(verde_idx):
    return tuple(bin_cola(c) for c in colas()) + (verde_idx,)


def clave(s):
    return ",".join(str(x) for x in s)


def cola_total():
    return sum(colas())


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
    """Lee el programa estatico del semaforo y devuelve las fases verdes, su ambar siguiente
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


# ---------------- Episodio ----------------
def correr_episodio(modo, Q, eps, gui, delay, seed, gamma=GAMMA, tripinfo=None, serie=None):
    """Corre una hora simulada. modo: baseline (tiempo fijo), actuado (SUMO), train o demo.
    Devuelve las metricas del episodio. Si serie es una ruta, guarda la cola por
    aproximacion cada PASO_SERIE segundos."""
    binario = sumolib.checkBinary("sumo-gui" if gui else "sumo")
    if tripinfo is None:
        tripinfo = f"tripinfo_{ESCENARIO}_{modo}.xml"
    cmd = [binario, "-c", CFG, "--seed", str(seed),
           "--tripinfo-output", tripinfo, "--tripinfo-output.write-unfinished", "true",
           "--device.emissions.probability", "1"]
    if modo == "actuado":
        cmd += ["--additional-files",
                comun.archivo_actuado(CFG, ESCENARIO, [TLS], VERDE_MIN, VERDE_MIN_GIRO, VERDE_MAX)]
    if gui:
        cmd += ["--start", "--quit-on-end", "--delay", str(delay)]
        vista = f"vista_{ESCENARIO}.xml" if os.path.exists(f"vista_{ESCENARIO}.xml") else "vista.xml"
        if os.path.exists(vista):
            cmd += ["--gui-settings-file", vista]
    traci.start(cmd)

    controla = modo in ("train", "demo")     # en baseline y actuado el semaforo corre su programa
    if modo == "actuado":
        traci.trafficlight.setProgram(TLS, "actuado")
    verdes, ambar, dur_ambar, verde_min = fases_verdes()
    verde = 0                     # indice dentro de la lista 'verdes'
    if controla:
        poner_fase(verdes[verde], 100000)   # el agente decide cuando cambiar
    t_verde = 0
    pasos = 0
    cola_acum = 0.0
    cola_max = 0
    r_total = 0.0        # recompensa que ve el agente (para aprender)
    decisiones = 0
    r_reporte = 0.0      # recompensa medida cada 5 s de reloj fijo, igual en los cuatro modos
    n_reporte = 0
    cambios = 0
    dq_max = 0.0
    fase_previa = traci.trafficlight.getPhase(TLS)
    filas_serie = []
    s = estado(verde)

    def avanzar(n):
        nonlocal pasos, cola_acum, cola_max, cambios, fase_previa, r_reporte, n_reporte
        for _ in range(n):
            traci.simulationStep()
            pasos += 1
            c = colas()
            cola_acum += sum(c)
            cola_max = max(cola_max, sum(c))
            fase = traci.trafficlight.getPhase(TLS)
            if fase != fase_previa and fase in verdes:   # entro un verde nuevo: un cambio de fase
                cambios += 1
            fase_previa = fase
            if pasos % PASO_CONTROL == 0:
                r_reporte += recompensa()
                n_reporte += 1
            if serie is not None and pasos % PASO_SERIE == 0:
                filas_serie.append([pasos] + c)

    while traci.simulation.getMinExpectedNumber() > 0 and pasos < 6000:
        if not controla:
            avanzar(PASO_CONTROL)            # el semaforo corre su programa; solo se mide
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

        avanzar(PASO_CONTROL)
        t_verde += PASO_CONTROL
        r = recompensa()
        r_total += r
        decisiones += 1
        s2 = estado(verde)

        if modo == "train":
            q = q_vals(Q, s)
            delta = ALPHA * (r + gamma * max(q_vals(Q, s2)) - q[a])
            q[a] += delta
            dq_max = max(dq_max, abs(delta))
        s = s2

    traci.close()
    if serie is not None:
        comun.guardar_serie(serie, ["t"] + APROX, filas_serie)
    res = comun.leer_tripinfo(tripinfo)
    res.update({
        "cola_prom": round(cola_acum / max(1, pasos), 2),   # vehiculos detenidos, promedio por segundo
        "cola_max": cola_max,                                 # maximo instantaneo en las 4 aproximaciones
        "recompensa": round(r_reporte, 1),                    # medida cada 5 s en los cuatro modos
        "recompensa_decision": round(r_reporte / max(1, n_reporte), 3),
        "decisiones": decisiones if controla else n_reporte,
        "cambios_fase": cambios,
        "dq_max": round(dq_max, 4),
    })
    return res


def evaluar_greedy(Q, seed):
    """Corre la politica actual con epsilon 0 sobre una copia de la Q-table y sin alterar
    el generador aleatorio del entrenamiento. Devuelve (timeLoss, espera)."""
    estado_rng = random.getstate()
    random.seed(seed)
    res = correr_episodio("demo", copy.deepcopy(Q), 0.0, False, 0, seed,
                          tripinfo=f"tripinfo_{ESCENARIO}_eval.xml")
    random.setstate(estado_rng)
    return res["timeloss_prom"], res["espera_prom"]


# ---------------- Main ----------------
def main():
    global ESCENARIO, CFG, TLS, APROX, Q_FILE, RESULTADOS
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["baseline", "actuado", "train", "demo"])
    ap.add_argument("--escenario", choices=sorted(ESCENARIOS), default="cruce")
    ap.add_argument("--episodios", type=int, default=40)
    ap.add_argument("--eps-decay", type=float, default=EPS_DECAY,
                    help="decaimiento de epsilon por episodio (mas lento = mas exploracion)")
    ap.add_argument("--gamma", type=float, default=GAMMA,
                    help="factor de descuento (mas alto = horizonte mas largo)")
    ap.add_argument("--eval-cada", type=int, default=5,
                    help="cada cuantos episodios de train se evalua la politica congelada (0 = nunca)")
    ap.add_argument("--eval-seed", type=int, default=999,
                    help="semilla fija de esa evaluacion, fuera del entrenamiento y de la evaluacion final")
    ap.add_argument("--desde-cero", action="store_true", help="borra la Q-table antes de entrenar")
    ap.add_argument("--serie", action="store_true",
                    help="guarda la cola por aproximacion cada 60 s (serie_<esc>_<modo>_s<semilla>.csv)")
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
    if args.modo == "train" and args.desde_cero and os.path.exists(Q_FILE):
        os.remove(Q_FILE)
    if os.path.exists(Q_FILE):
        with open(Q_FILE) as f:
            Q = json.load(f)

    salida, escritor = comun.abrir_csv(RESULTADOS)
    serie = (f"serie_{ESCENARIO}_{args.modo}_s{args.seed}.csv" if args.serie else None)

    if args.modo in ("baseline", "actuado"):
        res = correr_episodio(args.modo, Q, 0.0, args.gui, args.delay, args.seed, serie=serie)
        print("TIEMPO FIJO:" if args.modo == "baseline" else "ACTUADO (SUMO):", res)
        escritor.writerow({"modo": args.modo, "episodio": 0, "semilla": args.seed, "epsilon": 0, **res})

    elif args.modo == "train":
        if not Q:
            print("Q-table vacia: entrenamiento desde cero.")
        eps = EPS_INICIAL
        for ep in range(1, args.episodios + 1):
            res = correr_episodio("train", Q, eps, args.gui, args.delay, args.seed + ep, args.gamma)
            fila = {"modo": "train", "episodio": ep, "semilla": args.seed + ep,
                    "epsilon": round(eps, 3), "estados_q": len(Q), **res}
            if args.eval_cada and (ep % args.eval_cada == 0 or ep == args.episodios):
                fila["eval_timeloss"], fila["eval_espera"] = evaluar_greedy(Q, args.eval_seed)
            print(f"Episodio {ep:3d}  eps={eps:.2f}  timeLoss={res['timeloss_prom']:6.2f}s  "
                  f"espera={res['espera_prom']:6.2f}s  cola={res['cola_prom']:5.2f}  "
                  f"R/dec={res['recompensa_decision']:7.2f}  estados={len(Q)}"
                  + (f"  eval timeLoss={fila['eval_timeloss']:6.2f}s" if "eval_timeloss" in fila else ""))
            escritor.writerow(fila)
            salida.flush()
            eps = max(EPS_MIN, eps * args.eps_decay)
            with open(Q_FILE, "w") as f:
                json.dump(Q, f)
        print(f"Q-table guardada en {Q_FILE} ({len(Q)} estados)")

    else:  # demo
        if not Q:
            sys.exit("No hay Q-table entrenada. Ejecuta primero: python rl_semaforo.py train")
        res = correr_episodio("demo", Q, 0.0, args.gui, args.delay, args.seed, serie=serie)
        print("AGENTE RL (Q-learning):", res)
        escritor.writerow({"modo": "demo", "episodio": 0, "semilla": args.seed, "epsilon": 0,
                           "estados_q": len(Q), **res})

    salida.close()


if __name__ == "__main__":
    main()
