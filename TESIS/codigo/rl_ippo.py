"""
rl_ippo.py - Modulo U4: coordinacion distribuida entre semaforos con IPPO (PPO con pesos
compartidos: un solo actor y un solo critico para todos los semaforos del escenario, cada
agente decide con su propia observacion). Torch puro, sin Gym ni stable-baselines3.

Modos:
  python rl_ippo.py train --escenario red --variante vecinos --episodios 200 --seed 42
  python rl_ippo.py demo  --escenario red --politica politica_red_vecinos_s42.pt [--gui]

Variantes (--variante), en orden incremental:
  local    observacion local: colas y vehiculos en movimiento por aproximacion, fase activa,
           tiempo de verde, si ya puede cambiar e id del semaforo; ranuras de vecinos a cero.
  vecinos  local + estado extendido con lo que envian los cruces vecinos (mensajeria).
  spill    vecinos + penalizacion por spillback en los enlaces de salida hacia el vecino.
  cambio   vecinos + penalizacion por cambio de fase (opcional).

Lo que no cambia respecto de U2: fases, ambar de 3 s, verde minimo 10 s (5 s en giros) y
maximo 60 s, decision cada 5 s contados desde el inicio del verde propio (la primera a los
5 s), episodio = 1 h de demanda mas vaciado (tope 6000 pasos) y los pesos w1 = 1, w2 = 0.01.
Lo que cambia en la recompensa: el termino de cola detenida se sustituye por los
vehiculos-equivalentes retrasados n_a * (1 - v_media_a / v_max_a) de cada aproximacion (la
version por segundo del timeLoss, metrica primaria) y el agente recibe la suma por segundo
sobre su intervalo de decision dividida entre 5 (retraso-segundos), no el nivel en el
instante siguiente. La formula de U2 se sigue reportando a reloj fijo de 5 s para comparar.

Mensajeria: cada 5 s de reloj global cada semaforo publica a cada vecino su fase (avenida,
transversal o ambar), el tiempo en esa fase, el outflow que le va a enviar, la cola que
tiene esperando hacia el y la cola que ve en la salida del vecino. El receptor lo lee en
su propia decision; --latencia y --perdida simulan un canal imperfecto (solo evaluacion).
"""
import os
import sys
import json
import time
import random
import argparse
import subprocess

import numpy as np
import torch
import torch.nn as nn

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
import rl_corredor as rc

# ---------------- Escenarios ----------------
# Vecinos de cada semaforo: por lado (oeste, este) el vecino, el enlace que llega desde el
# vecino (j -> i, es aproximacion propia) y el enlace que sale hacia el (i -> j).
VECINOS = {
    "corredor": {
        "semaforo_C1": {"oeste": None, "este": ("semaforo_C2", "C2_C1", "C1_C2")},
        "semaforo_C2": {"oeste": ("semaforo_C1", "C1_C2", "C2_C1"), "este": None},
    },
    "red": {
        "semaforo_C1": {"oeste": None, "este": ("semaforo_C2", "C2_C1", "C1_C2")},
        "semaforo_C2": {"oeste": ("semaforo_C1", "C1_C2", "C2_C1"),
                        "este": ("semaforo_C3", "C3_C2", "C2_C3")},
        "semaforo_C3": {"oeste": ("semaforo_C2", "C2_C3", "C3_C2"), "este": None},
    },
    "cruce": {"semaforo_C": {"oeste": None, "este": None}},
}
VECINOS["corredor_alta"] = VECINOS["corredor"]

ESCENARIOS = {esc: {**rc.ESCENARIOS[esc], "vecinos": VECINOS[esc]}
              for esc in ("corredor", "red", "corredor_alta")}
ESCENARIOS["cruce"] = {"cfg": "cruce.sumocfg", "semaforos": {"semaforo_C": ["W_C", "E_C", "N_C", "S_C"]},
                       "enlaces": [], "flujos_corredor": None, "vecinos": VECINOS["cruce"]}
# Orden de las aproximaciones en SEMAFOROS: [avenida oeste, avenida este, norte, sur]

# ---------------- Parametros ----------------
PASO_CONTROL, VERDE_MAX = rc.PASO_CONTROL, rc.VERDE_MAX
W1, W2 = rc.W1, rc.W2          # recompensa base, identica a U2
W3 = 2.0                       # spill: vehiculos-equivalentes por vehiculo detenido sobre la bisagra
W4 = 2.0                       # cambio: costo de cada cambio de fase
ESCALA_R = 0.02                # lo que ve PPO es r / 50 (valores de -5 a -10 con politicas buenas)
N_ID = 3                       # posiciones fijas del id del semaforo (C1, C2, C3)
DIM_OBS = 15 + 2 * 8           # bloque local + dos ranuras de vecinos
OCULTAS = 64
# Fijados en la prueba de humo (cruce, 06.09): con lr 3e-4, minilote 256 y 8 epocas la politica
# no salia de un programa fijo en 60 episodios (KL < 0.001 por actualizacion); con lr 1e-3,
# minilote 64 y 10 epocas iguala al actuado en 15 episodios. gamma 0.9 no cambio nada.
HIPER = {"gamma": 0.95, "lam": 0.95, "clip": 0.2, "epocas": 10, "minibatch": 64,
         "lr": 1e-3, "ent": 0.01, "valor": 0.5, "grad": 0.5}
EDAD_MAX = 30                  # edad de mensaje que satura la observacion (s)
CAMPOS_IPPO = ["variante", "base", "episodio", "semilla", "lr", "segundos", "vehiculos",
               "espera_prom", "timeloss_prom", "cola_prom", "cola_max",
               "recompensa", "recompensa_decision", "recompensa_total_decision",
               "decisiones", "decisiones_libres", "cambios_fase",
               "paradas_prom", "throughput", "co2_prom", "nox_prom", "no_terminados",
               "spillback_tasa", "spillback_seg", "spillback_eventos", "cola_max_enlace",
               "veh_max_enlace", "viaje_corredor_prom", "retraso_corredor_prom",
               "retraso_corredor_punta", "paradas_corredor", "paradas_corredor_le1",
               "spill_activaciones", "spill_suma",
               "perdida_politica", "perdida_valor", "entropia_libre", "kl_aprox", "clipfrac",
               "eval_timeloss", "eval_espera"]

# Se rellena con preparar(escenario)
C = {}


def preparar(escenario):
    """Fija el escenario y calcula la geometria (plazas por aproximacion y por carril)."""
    e = ESCENARIOS[escenario]
    net_file, _ = comun.leer_cfg(e["cfg"])
    net = sumolib.net.readNet(net_file)
    aprox = [a for lista in e["semaforos"].values() for a in lista]
    C.clear()
    C.update({
        "escenario": escenario, "cfg": e["cfg"], "net": net_file,
        "semaforos": e["semaforos"], "enlaces": e["enlaces"],
        "flujos": e["flujos_corredor"], "vecinos": e["vecinos"],
        "indice": {tls: k for k, tls in enumerate(e["semaforos"])},
        "cap": {a: net.getEdge(a).getLaneNumber() * comun.plazas_carril(net, a) for a in aprox},
        "vmax": {a: net.getEdge(a).getSpeed() for a in aprox},
        "plazas": {l: comun.plazas_carril(net, l) for l in e["enlaces"]},
        "fase_av": {},          # se calcula con TraCI en el primer episodio
    })
    assert len(e["semaforos"]) <= N_ID
    return C


def fase_avenida(tls, aprox, verdes):
    """Indice (dentro de verdes) de la fase verde que sirve a la avenida: la que pone en
    verde los links cuyo carril de entrada pertenece a las aproximaciones 0 o 1."""
    activo = traci.trafficlight.getProgram(tls)
    logicas = traci.trafficlight.getAllProgramLogics(tls)
    logica = next((l for l in logicas if l.programID == activo), logicas[0])
    links = traci.trafficlight.getControlledLinks(tls)
    de_avenida = [bool(l) and l[0][0].rsplit("_", 1)[0] in aprox[:2] for l in links]
    candidatas = []
    for k, f in enumerate(verdes):
        estado = logica.phases[f].state
        if any(c in "Gg" and av for c, av in zip(estado, de_avenida)):
            candidatas.append(k)
    assert len(candidatas) == 1, f"{tls}: fases de avenida {candidatas}"
    return candidatas[0]


# ---------------- Lecturas por suscripcion ----------------
HALT, VEH, ESP = tc.LAST_STEP_VEHICLE_HALTING_NUMBER, tc.LAST_STEP_VEHICLE_NUMBER, tc.VAR_WAITING_TIME
VEL = tc.LAST_STEP_MEAN_SPEED


def suscribir():
    for lista in C["semaforos"].values():
        for a in lista:
            traci.edge.subscribe(a, [HALT, VEH, ESP, VEL])
    for tls in C["semaforos"]:
        traci.trafficlight.subscribe(tls, [tc.TL_CURRENT_PHASE])


def lecturas():
    return traci.edge.getAllSubscriptionResults()


def leer(lect, edge, var):
    return lect.get(edge, {}).get(var, 0)


def fases_actuales():
    res = traci.trafficlight.getAllSubscriptionResults()
    return {tls: res.get(tls, {}).get(tc.TL_CURRENT_PHASE, -1) for tls in C["semaforos"]}


# ---------------- Politica ----------------
def capa(entrada, salida, ganancia):
    lin = nn.Linear(entrada, salida)
    nn.init.orthogonal_(lin.weight, ganancia)
    nn.init.zeros_(lin.bias)
    return lin


class Politica(nn.Module):
    """Actor y critico separados, MLP de dos capas ocultas con tanh."""

    def __init__(self, dim_obs=DIM_OBS, ocultas=OCULTAS):
        super().__init__()
        self.actor = nn.Sequential(capa(dim_obs, ocultas, 2 ** 0.5), nn.Tanh(),
                                   capa(ocultas, ocultas, 2 ** 0.5), nn.Tanh(),
                                   capa(ocultas, 2, 0.01))
        self.critico = nn.Sequential(capa(dim_obs, ocultas, 2 ** 0.5), nn.Tanh(),
                                     capa(ocultas, ocultas, 2 ** 0.5), nn.Tanh(),
                                     capa(ocultas, 1, 1.0))

    def forward(self, obs):
        return self.actor(obs), self.critico(obs).squeeze(-1)

    @staticmethod
    def enmascarar(logits, mascara):
        return logits.masked_fill(mascara == 0, -1e8)

    def guardar(self, ruta, meta):
        torch.save(self.state_dict(), ruta)
        with open(ruta.replace(".pt", ".json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=1, ensure_ascii=False)

    @staticmethod
    def cargar(ruta):
        with open(ruta.replace(".pt", ".json"), encoding="utf-8") as f:
            meta = json.load(f)
        politica = Politica(meta["dim_obs"], meta["ocultas"])
        politica.load_state_dict(torch.load(ruta, weights_only=True))
        politica.eval()
        return politica, meta


# ---------------- Mensajeria ----------------
class Canal:
    """Buzon entre semaforos vecinos. Cada mensaje se entrega t_emision + latencia segundos
    despues y se pierde con probabilidad perdida (RNG propio: no toca ninguna otra
    secuencia aleatoria). El receptor lee el mas reciente ya entregado; si no hay ninguno
    nuevo conserva el ultimo y la edad crece."""

    def __init__(self, latencia=0, perdida=0.0, semilla=0):
        self.latencia, self.perdida = int(latencia), float(perdida)
        self.rng = random.Random(semilla + 7919)
        self.buzon = {}
        self.ultimo = {}

    def publicar(self, emisor, receptor, t, msg):
        if self.perdida > 0 and self.rng.random() < self.perdida:
            return
        self.buzon.setdefault((emisor, receptor), []).append((t + self.latencia, t, msg))

    def leer(self, emisor, receptor, t):
        clave = (emisor, receptor)
        cola = self.buzon.get(clave, [])
        entregados = [x for x in cola if x[0] <= t]
        if entregados:
            self.ultimo[clave] = (entregados[-1][1], entregados[-1][2])
            self.buzon[clave] = [x for x in cola if x[0] > t]
        if clave in self.ultimo:
            t_em, msg = self.ultimo[clave]
            return msg, t - t_em
        return None, EDAD_MAX


def alimentadora(j, lado_de_i):
    """Aproximacion del vecino j que descarga sobre el enlace hacia i: la de la avenida por el
    lado contrario a i (si i esta al este de j, la aproximacion oeste de j, y viceversa)."""
    return C["semaforos"][j][0] if lado_de_i == "este" else C["semaforos"][j][1]


def mensaje(j, ag_j, lect, medidor, lado_de_i, enlace_i_a_j, t):
    """Lo que j le envia a su vecino i (i esta al lado_de_i de j)."""
    if ag_j["ambar_restante"] > 0:
        fase = "ambar"
    elif ag_j["verde"] == C["fase_av"][j]:
        fase = "avenida"
    else:
        fase = "transversal"
    alim = alimentadora(j, lado_de_i)
    total = leer(lect, alim, VEH)
    return {"fase": fase, "t_fase": 0 if fase == "ambar" else ag_j["t_verde"],
            "outflow": total if fase == "avenida" else 0,
            "cola_alimentadora": leer(lect, alim, HALT),
            "cola_salida": medidor.max_halting(enlace_i_a_j), "t": t}


# ---------------- Observacion, mascara y recompensa ----------------
def minimo_verde(ag):
    return ag["verde_min"][ag["verdes"][ag["verde"]]]


def observar(tls, ag, lect, canal, t, con_vecinos):
    obs = np.zeros(DIM_OBS, dtype=np.float32)
    aprox = C["semaforos"][tls]
    for k, a in enumerate(aprox):
        h, v = leer(lect, a, HALT), leer(lect, a, VEH)
        obs[k] = min(1.0, h / C["cap"][a])
        obs[4 + k] = min(1.0, max(0, v - h) / C["cap"][a])
    obs[8 + ag["verde"]] = 1.0
    obs[10] = min(1.0, ag["t_verde"] / VERDE_MAX)
    obs[11] = 1.0 if ag["t_verde"] >= minimo_verde(ag) else 0.0
    obs[12 + C["indice"][tls]] = 1.0
    if not con_vecinos:
        return obs
    for r, lado in enumerate(("oeste", "este")):
        vec = C["vecinos"][tls][lado]
        if vec is None:
            continue
        j, enlace_j_a_i, enlace_i_a_j = vec
        base = 15 + 8 * r
        obs[base] = 1.0
        msg, edad = canal.leer(j, tls, t)
        if msg is None:
            obs[base + 7] = 1.0
            continue
        lado_de_i = "oeste" if lado == "este" else "este"   # i visto desde j
        cap_alim = C["cap"][alimentadora(j, lado_de_i)]
        obs[base + 1] = 1.0 if msg["fase"] == "avenida" else 0.0
        obs[base + 2] = 1.0 if msg["fase"] == "ambar" else 0.0
        obs[base + 3] = min(1.0, msg["t_fase"] / VERDE_MAX)
        obs[base + 4] = min(1.0, msg["outflow"] / cap_alim)
        obs[base + 5] = min(1.0, msg["cola_alimentadora"] / cap_alim)
        obs[base + 6] = min(1.0, msg["cola_salida"] / C["plazas"][enlace_i_a_j])
        obs[base + 7] = min(1.0, edad / EDAD_MAX)
    return obs


def mascara(ag):
    """[puede mantener, puede cambiar]: verde minimo y maximo, igual que en U2."""
    if ag["t_verde"] < minimo_verde(ag):
        return [1.0, 0.0]
    if ag["t_verde"] >= VERDE_MAX:
        return [0.0, 1.0]
    return [1.0, 1.0]


def recompensa_base(tls, lect):
    """Formula de U2 (colas detenidas y esperas): se reporta a reloj fijo de 5 s en todos los brazos."""
    aprox = C["semaforos"][tls]
    return -(W1 * sum(leer(lect, a, HALT) for a in aprox) + W2 * sum(leer(lect, a, ESP) for a in aprox))


def retraso_base(tls, lect):
    """Vehiculos-equivalentes retrasados en las aproximaciones: n_a * (1 - v_media_a / v_max_a).
    Es la version por segundo del timeLoss de SUMO (metrica primaria): un vehiculo detenido
    cuenta 1 y uno que avanza a media velocidad cuenta 0.5. El conteo de detenidos de U2 no ve
    a los que avanzan a paso lento, y por eso cambiar de fase muy seguido (colas que reptan en
    vez de pararse) le parecia bueno al optimizador (prueba de humo en cruce, 06.09)."""
    total = 0.0
    for a in C["semaforos"][tls]:
        n = leer(lect, a, VEH)
        if n:
            total += n * (1.0 - min(1.0, max(0.0, leer(lect, a, VEL)) / C["vmax"][a]))
    return total


def recompensa_paso(tls, lect):
    """Lo que acumula el agente de U4 cada segundo: retraso en vez de cola detenida, misma espera."""
    return -(W1 * retraso_base(tls, lect) + W2 * sum(leer(lect, a, ESP) for a in C["semaforos"][tls]))


def termino_spill(tls, medidor):
    """Vehiculos detenidos por encima de la mitad de las plazas en el carril mas cargado de
    cada enlace que sale de tls hacia un vecino (lectura directa, no del mensaje)."""
    total = 0.0
    for lado in ("oeste", "este"):
        vec = C["vecinos"][tls][lado]
        if vec is None:
            continue
        enlace = vec[2]
        total += max(0, medidor.max_halting(enlace) - C["plazas"][enlace] // 2)
    return total


# ---------------- Episodio ----------------
def correr_episodio(modo, politica, gui, delay, seed, tripinfo=None, serie=None,
                    latencia=0, perdida=0.0, variante="vecinos", buffer=None):
    """Una hora simulada con los agentes IPPO. modo train (muestrea acciones y llena buffer)
    o demo (argmax). Devuelve las mismas metricas que rl_corredor.correr_episodio mas las
    de U4. El reloj de decision es el de rl_corredor.py."""
    esc = C["escenario"]
    con_vecinos = variante != "local"
    binario = sumolib.checkBinary("sumo-gui" if gui else "sumo")
    if tripinfo is None:
        tripinfo = f"tripinfo_{esc}_ippo_{modo}.xml"
    cmd = [binario, "-c", C["cfg"], "--seed", str(seed),
           "--tripinfo-output", tripinfo, "--tripinfo-output.write-unfinished", "true",
           "--device.emissions.probability", "1"]
    if gui:
        cmd += ["--start", "--quit-on-end", "--delay", str(delay)]
        if os.path.exists(f"vista_{esc}.xml"):
            cmd += ["--gui-settings-file", f"vista_{esc}.xml"]
    traci.start(cmd)
    suscribir()
    medidor = comun.MedidorEnlaces(C["net"], C["enlaces"])
    canal = Canal(latencia, perdida, seed)

    rc.SEMAFOROS = C["semaforos"]          # fases_verdes usa el programa activo del semaforo
    agentes = {}
    for tls, aprox in C["semaforos"].items():
        verdes, ambar, dur_ambar, verde_min = rc.fases_verdes(tls)
        assert len(verdes) == 2, f"{tls}: {len(verdes)} fases verdes; la observacion asume 2"
        if tls not in C["fase_av"]:
            C["fase_av"][tls] = fase_avenida(tls, aprox, verdes)
        agentes[tls] = {"verdes": verdes, "ambar": ambar, "dur_ambar": dur_ambar,
                        "verde_min": verde_min, "verde": 0, "t_verde": 0, "ambar_restante": 0,
                        "pendiente": None, "cambio": 0.0, "fase_previa": None,
                        "r_acum": 0.0, "s_acum": 0.0}
        traci.trafficlight.setPhase(tls, verdes[0])
        traci.trafficlight.setPhaseDuration(tls, 100000)
    fases = fases_actuales()
    for tls in agentes:
        agentes[tls]["fase_previa"] = fases[tls]
    orden = list(C["semaforos"])
    if buffer is not None:
        for tls in orden:
            buffer[tls] = {"obs": [], "mascara": [], "accion": [], "logp": [], "valor": [],
                           "recompensa": [], "v_final": 0.0}

    pasos = 0
    cola_acum = 0.0
    cola_max = 0
    r_reporte, n_reporte = 0.0, 0      # recompensa base a reloj fijo de 5 s (comparable con U2)
    r_agente, n_agente = 0.0, 0        # lo que ven los agentes (con terminos), sin escalar
    decisiones_libres = 0
    spill_activaciones, spill_suma = 0, 0.0
    cambios = 0
    filas_serie, filas_fases = [], []
    lect = {}
    aprox_todas = [a for lista in C["semaforos"].values() for a in lista]

    def recompensa_agente(tls, ag):
        # Suma por segundo de recompensa_paso sobre el intervalo de decision, dividida entre
        # 5 s: en un intervalo de mantener es el nivel medio y en uno de cambiar (8 s) pesa
        # 8/5 (retraso-segundos, el objetivo real). El nivel en el instante siguiente, como en
        # U2, subestimaba la cola al inicio de un verde y tambien sesgaba hacia cambiar.
        r = ag["r_acum"] / PASO_CONTROL
        if variante == "spill":
            s = ag["s_acum"] / PASO_CONTROL
            r -= W3 * s
            nonlocal spill_activaciones, spill_suma
            if s > 0:
                spill_activaciones += 1
                spill_suma += s
        if variante == "cambio":
            r -= W4 * ag["cambio"]
        ag["r_acum"], ag["s_acum"] = 0.0, 0.0
        return r

    def cerrar_pendiente(tls, ag):
        nonlocal r_agente, n_agente
        if ag["pendiente"] is None:
            return
        r = recompensa_agente(tls, ag)
        r_agente += r
        n_agente += 1
        ag["cambio"] = 0.0
        if buffer is not None:
            buffer[tls]["recompensa"].append(r * ESCALA_R)
        ag["pendiente"] = None

    while traci.simulation.getMinExpectedNumber() > 0 and pasos < 6000:
        if pasos > 0 and pasos % PASO_CONTROL == 0:
            for tls in orden:
                r_reporte += recompensa_base(tls, lect)
                n_reporte += 1
            if con_vecinos:
                for j, ag_j in agentes.items():
                    for lado, vec in C["vecinos"][j].items():
                        if vec is None:
                            continue
                        i, _, enlace_i_a_j = vec
                        msg = mensaje(j, ag_j, lect, medidor, lado, enlace_i_a_j, pasos)
                        canal.publicar(j, i, pasos, msg)

        deciden = []
        for tls in orden:
            ag = agentes[tls]
            if ag["ambar_restante"] > 0 or ag["t_verde"] % PASO_CONTROL != 0:
                continue
            if ag["t_verde"] == 0 and pasos > 0:
                continue
            deciden.append(tls)
        if deciden:
            for tls in deciden:
                cerrar_pendiente(tls, agentes[tls])
            obs = np.stack([observar(tls, agentes[tls], lect, canal, pasos, con_vecinos) for tls in deciden])
            masc = np.array([mascara(agentes[tls]) for tls in deciden], dtype=np.float32)
            with torch.no_grad():
                logits, valores = politica(torch.from_numpy(obs))
                logits = Politica.enmascarar(logits, torch.from_numpy(masc))
                if modo == "train":
                    dist = torch.distributions.Categorical(logits=logits)
                    acciones = dist.sample()
                    logp = dist.log_prob(acciones)
                else:
                    acciones = logits.argmax(dim=1)
                    logp = torch.zeros(len(deciden))
            for k, tls in enumerate(deciden):
                ag = agentes[tls]
                a = int(acciones[k])
                if masc[k].sum() > 1:
                    decisiones_libres += 1
                if buffer is not None:
                    b = buffer[tls]
                    b["obs"].append(obs[k])
                    b["mascara"].append(masc[k])
                    b["accion"].append(a)
                    b["logp"].append(float(logp[k]))
                    b["valor"].append(float(valores[k]))
                ag["pendiente"] = True
                if a == 1:                                  # la mascara garantiza que es legal
                    f_actual = ag["verdes"][ag["verde"]]
                    traci.trafficlight.setPhase(tls, ag["ambar"][f_actual])
                    traci.trafficlight.setPhaseDuration(tls, ag["dur_ambar"][f_actual])
                    ag["ambar_restante"] = ag["dur_ambar"][f_actual]
                    ag["cambio"] = 1.0

        traci.simulationStep()
        pasos += 1
        lect = lecturas()
        colas = [leer(lect, a, HALT) for a in aprox_todas]
        cola_acum += sum(colas)
        cola_max = max(cola_max, sum(colas))
        medidor.paso(pasos)
        for tls, ag in agentes.items():
            if ag["pendiente"] is not None:
                ag["r_acum"] += recompensa_paso(tls, lect)
                if variante == "spill":
                    ag["s_acum"] += termino_spill(tls, medidor)
        if serie is not None and pasos % rc.PASO_SERIE == 0:
            filas_serie.append([pasos] + colas)
        fases = fases_actuales()
        if serie is not None and pasos <= comun.FIN_HORA:
            filas_fases.append([pasos] + [fases[t] for t in orden])
        for tls, ag in agentes.items():
            if fases[tls] != ag["fase_previa"] and fases[tls] in ag["verdes"]:
                cambios += 1
            ag["fase_previa"] = fases[tls]
            if ag["ambar_restante"] > 0:
                ag["ambar_restante"] -= 1
                if ag["ambar_restante"] == 0:
                    ag["verde"] = (ag["verde"] + 1) % len(ag["verdes"])
                    traci.trafficlight.setPhase(tls, ag["verdes"][ag["verde"]])
                    traci.trafficlight.setPhaseDuration(tls, 100000)
                    ag["t_verde"] = 0
            else:
                ag["t_verde"] += 1

    vaciada = traci.simulation.getMinExpectedNumber() == 0
    # transiciones pendientes: recompensa con el estado de cierre y valor final segun vaciado
    for tls in orden:
        ag = agentes[tls]
        cerrar_pendiente(tls, ag)
        if buffer is not None:
            if vaciada:
                buffer[tls]["v_final"] = 0.0
            else:
                with torch.no_grad():
                    o = torch.from_numpy(observar(tls, ag, lect, canal, pasos, con_vecinos)).unsqueeze(0)
                    buffer[tls]["v_final"] = float(politica(o)[1][0])
    traci.close()

    if serie is not None:
        comun.guardar_serie(serie, ["t"] + aprox_todas, filas_serie)
        comun.guardar_fases(serie.replace("serie_", "fases_", 1), orden, filas_fases)
    res = comun.leer_tripinfo(tripinfo, C["flujos"])
    res.update({
        "cola_prom": round(cola_acum / max(1, pasos), 2),
        "cola_max": cola_max,
        "recompensa": round(r_reporte, 1),
        "recompensa_decision": round(r_reporte / max(1, n_reporte), 3),
        "recompensa_total_decision": round(r_agente / max(1, n_agente), 3),
        "decisiones": n_agente,
        "decisiones_libres": decisiones_libres,
        "cambios_fase": cambios,
        "spill_activaciones": spill_activaciones,
        "spill_suma": round(spill_suma, 1),
    })
    res.update(medidor.resumen())
    return res


# ---------------- PPO ----------------
def gae(buffer, gamma, lam):
    """Ventajas y retornos por agente; devuelve el lote concatenado."""
    obs, masc, acc, logp, adv, ret = [], [], [], [], [], []
    for tls, b in buffer.items():
        n = len(b["recompensa"])
        if n == 0:
            continue
        valores = b["valor"] + [b["v_final"]]
        ventaja = np.zeros(n, dtype=np.float32)
        ultimo = 0.0
        for t in reversed(range(n)):
            delta = b["recompensa"][t] + gamma * valores[t + 1] - valores[t]
            ultimo = delta + gamma * lam * ultimo
            ventaja[t] = ultimo
        obs.extend(b["obs"][:n])
        masc.extend(b["mascara"][:n])
        acc.extend(b["accion"][:n])
        logp.extend(b["logp"][:n])
        adv.extend(ventaja)
        ret.extend(ventaja + np.array(b["valor"][:n], dtype=np.float32))
    adv = np.array(adv, dtype=np.float32)
    adv = (adv - adv.mean()) / (adv.std() + 1e-8)
    return (torch.from_numpy(np.stack(obs)), torch.from_numpy(np.stack(masc)),
            torch.tensor(acc), torch.tensor(logp, dtype=torch.float32),
            torch.from_numpy(adv), torch.tensor(ret, dtype=torch.float32))


def actualizar(politica, opt, lote, hiper, rng):
    obs, masc, acc, logp_viejo, adv, ret = lote
    n = len(obs)
    idx = np.arange(n)
    libres = masc.sum(dim=1) > 1
    diag = {"perdida_politica": [], "perdida_valor": [], "entropia_libre": [], "kl_aprox": [],
            "clipfrac": []}
    for _ in range(hiper["epocas"]):
        rng.shuffle(idx)
        for ini in range(0, n, hiper["minibatch"]):
            b = torch.from_numpy(idx[ini:ini + hiper["minibatch"]])
            logits, valor = politica(obs[b])
            dist = torch.distributions.Categorical(logits=Politica.enmascarar(logits, masc[b]))
            logp = dist.log_prob(acc[b])
            ratio = torch.exp(logp - logp_viejo[b])
            recortado = torch.clamp(ratio, 1 - hiper["clip"], 1 + hiper["clip"])
            perdida_pol = -torch.min(ratio * adv[b], recortado * adv[b]).mean()
            perdida_val = 0.5 * ((valor - ret[b]) ** 2).mean()
            ent_libre = dist.entropy()[libres[b]]
            entropia = ent_libre.mean() if len(ent_libre) else torch.tensor(0.0)
            perdida = perdida_pol + hiper["valor"] * perdida_val - hiper["ent"] * entropia
            opt.zero_grad()
            perdida.backward()
            # Recorte por red y no global: el error inicial del critico (retornos de -20 a -30
            # frente a un valor inicial 0) hace su gradiente ~100 veces mayor que el del actor y
            # un recorte conjunto reducia el paso del actor 50 veces (prueba de humo, 06.09).
            nn.utils.clip_grad_norm_(politica.actor.parameters(), hiper["grad"])
            nn.utils.clip_grad_norm_(politica.critico.parameters(), hiper["grad"])
            opt.step()
            with torch.no_grad():
                diag["perdida_politica"].append(float(perdida_pol))
                diag["perdida_valor"].append(float(perdida_val))
                diag["entropia_libre"].append(float(entropia))
                # estimador k3 de KL(vieja || nueva): (ratio - 1) - log(ratio), siempre >= 0
                diag["kl_aprox"].append(float(((ratio - 1) - (logp - logp_viejo[b])).mean()))
                diag["clipfrac"].append(float(((ratio - 1).abs() > hiper["clip"]).float().mean()))
    return {k: round(float(np.mean(v)), 4) for k, v in diag.items()}


def evaluar_argmax(politica, seed, variante, tripinfo):
    """Politica congelada (argmax) con una semilla fija; no consume el RNG del entrenamiento."""
    estado_torch = torch.get_rng_state()
    res = correr_episodio("demo", politica, False, 0, seed, tripinfo=tripinfo, variante=variante)
    torch.set_rng_state(estado_torch)
    return res["timeloss_prom"], res["espera_prom"]


def sembrar(base):
    random.seed(base)
    np.random.seed(base)
    torch.manual_seed(base)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    return np.random.default_rng(base)


def hash_git():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                              text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


# ---------------- Main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["train", "demo"])
    ap.add_argument("--escenario", choices=sorted(ESCENARIOS), default="corredor")
    ap.add_argument("--variante", choices=["local", "vecinos", "spill", "cambio"], default="vecinos")
    ap.add_argument("--episodios", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42, help="semilla base (entrenamiento: base + episodio)")
    ap.add_argument("--eval-cada", type=int, default=10)
    ap.add_argument("--eval-seed", type=int, default=999)
    ap.add_argument("--latencia", type=int, default=0, help="segundos de retardo del canal (demo)")
    ap.add_argument("--perdida", type=float, default=0.0, help="probabilidad de perder un mensaje (demo)")
    ap.add_argument("--csv", default=None,
                    help="CSV de salida (por defecto resultados_<esc>_ippo_<variante>_s<seed>.csv)")
    ap.add_argument("--politica", default=None, help="archivo .pt para demo")
    ap.add_argument("--hiper", default="", help="cambios a HIPER, p. ej. lr=1e-3,minibatch=64")
    ap.add_argument("--serie", action="store_true")
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--delay", type=int, default=30)
    args = ap.parse_args()
    for cambio in [c for c in args.hiper.split(",") if c]:
        clave, valor = cambio.split("=")
        HIPER[clave] = type(HIPER[clave])(float(valor)) if clave in ("epocas", "minibatch") else float(valor)

    preparar(args.escenario)
    esc = args.escenario
    rng = sembrar(args.seed)

    if args.modo == "demo":
        politica, meta = Politica.cargar(args.politica)
        variante = meta["variante"]
        serie = f"serie_{esc}_ippo_{variante}_s{args.seed}.csv" if args.serie else None
        res = correr_episodio("demo", politica, args.gui, args.delay, args.seed, serie=serie,
                              latencia=args.latencia, perdida=args.perdida, variante=variante)
        print(f"IPPO {variante} ({esc}):", res)
        return

    politica = Politica()
    opt = torch.optim.Adam(politica.parameters(), lr=HIPER["lr"], eps=1e-5)
    etiqueta = f"{esc}_ippo_{args.variante}_s{args.seed}"
    ruta_csv = args.csv or f"resultados_{etiqueta}.csv"
    salida, escritor = comun.abrir_csv(ruta_csv, CAMPOS_IPPO)
    print(f"IPPO {args.variante} en {esc}: {args.episodios} episodios, semilla base {args.seed}, "
          f"{sum(p.numel() for p in politica.parameters())} parametros")
    eval_final = None
    for ep in range(1, args.episodios + 1):
        lr = HIPER["lr"] * (1 - (ep - 1) / args.episodios)
        for g in opt.param_groups:
            g["lr"] = lr
        buffer = {}
        t0 = time.time()
        res = correr_episodio("train", politica, args.gui, args.delay, args.seed + ep,
                              tripinfo=f"tripinfo_{etiqueta}.xml", variante=args.variante, buffer=buffer)
        lote = gae(buffer, HIPER["gamma"], HIPER["lam"])
        diag = actualizar(politica, opt, lote, HIPER, rng)
        fila = {"variante": args.variante, "base": args.seed, "episodio": ep, "semilla": args.seed + ep,
                "lr": f"{lr:.2e}", "segundos": round(time.time() - t0, 1), **res, **diag}
        if args.eval_cada and (ep % args.eval_cada == 0 or ep == args.episodios):
            fila["eval_timeloss"], fila["eval_espera"] = evaluar_argmax(
                politica, args.eval_seed, args.variante, f"tripinfo_{etiqueta}_eval.xml")
            eval_final = fila["eval_timeloss"]
        escritor.writerow(fila)
        salida.flush()
        print(f"Ep {ep:3d}  timeLoss={res['timeloss_prom']:6.2f}  espera={res['espera_prom']:5.2f}  "
              f"r/dec={res['recompensa_decision']:6.2f}  cambios={res['cambios_fase']:4d}  "
              f"kl={diag['kl_aprox']:.4f} ent={diag['entropia_libre']:.3f}  {fila['segundos']}s"
              + (f"  eval={fila['eval_timeloss']:.2f}" if "eval_timeloss" in fila else ""), flush=True)
    salida.close()

    meta = {"escenario": esc, "variante": args.variante, "base": args.seed, "episodios": args.episodios,
            "dim_obs": DIM_OBS, "ocultas": OCULTAS, "hiper": HIPER, "w1": W1, "w2": W2, "w3": W3, "w4": W4,
            "escala_r": ESCALA_R, "fase_av": C["fase_av"], "vecinos": C["vecinos"], "cap": C["cap"],
            "plazas": C["plazas"], "umbral_spillback": comun.UMBRAL_SPILLBACK,
            "latencia_entrenamiento": 0, "perdida_entrenamiento": 0.0, "eval_seed": args.eval_seed,
            "eval_999_final": eval_final, "torch": torch.__version__, "python": sys.version.split()[0],
            "sumo": "1.25.0", "git": hash_git(),
            "features": ["cola_o", "cola_e", "cola_n", "cola_s", "movil_o", "movil_e", "movil_n", "movil_s",
                         "fase_0", "fase_1", "t_verde", "puede_cambiar", "id_C1", "id_C2", "id_C3"]
                        + [f"{lado}_{f}" for lado in ("oeste", "este")
                           for f in ("presente", "verde_hacia_mi", "ambar", "t_fase", "outflow",
                                     "cola_alimentadora", "cola_mi_salida", "edad")]}
    ruta = f"politica_{etiqueta}.pt".replace("_ippo", "")
    politica.guardar(ruta, meta)
    print(f"Politica guardada en {ruta} (eval final {eval_final})")


if __name__ == "__main__":
    main()
