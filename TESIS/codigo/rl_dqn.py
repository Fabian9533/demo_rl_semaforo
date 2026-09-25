"""
rl_dqn.py - Double DQN con pesos compartidos entre semaforos (plan de pruebas v2, 24.09.2026).

Una sola red Q para todos los semaforos del escenario; cada semaforo decide con su propia
observacion. Todo lo del entorno es el de rl_ippo.py variante vecinos: la misma observacion
(bloque local + mensajes de los vecinos), la misma mascara de acciones (verde minimo y maximo
de U2), el mismo reloj de decision (cada 5 s del verde propio) y la misma recompensa
(recompensa_paso acumulada sobre el intervalo de decision / 5, escalada por ESCALA_R = 0.02).
Este archivo solo decide y aprende; el episodio lo corre rl_ippo.correr_episodio con sus
ganchos decidir / transicion (ver su docstring), asi las metricas son las mismas en todo.

Uso (desde demo_rl/plan2):
  python ../rl_dqn.py train --escenario red --seed 42 --episodios 200 [--eval-cada 10]
                            [--val-seeds 999,1999] [--csv R] [--hiper lr=1e-3,objetivo=500]
  python ../rl_dqn.py demo  --escenario red --politica politica_red_dqn_s42.pt [--seed 1001]
                            [--latencia L] [--perdida P] [--serie] [--gui]

Algoritmo (HIPER, fijados antes de la prueba de humo):
  red Q dim_obs-64-64-2 con ReLU, inicializacion ortogonal como rl_ippo.capa (ganancia raiz de 2
  en las ocultas, 1 en la salida, sesgos a cero); red objetivo copiada cada 1000 actualizaciones;
  replay de 100 000 transiciones compartido por todos los semaforos; minilote 64; Adam lr 5e-4;
  gamma 0.95 (por decision, como IPPO); perdida de Huber; recorte de gradiente 10 (norma global);
  una actualizacion por transicion guardada (una por decision de cada semaforo) desde que el
  replay tiene 1000; epsilon lineal por episodio de 1.0 a 0.05 en el primer 50 % de los
  episodios. Double DQN: la accion del objetivo la elige la red en linea y la valora la red
  objetivo. Las acciones que la mascara prohibe valen -inf en todo argmax (decision y objetivo).
  Terminal solo si la red se vacio (si el episodio se corta en 6000 s se hace bootstrap).
  La exploracion y el muestreo del replay usan un generador propio (numpy default_rng(base)),
  asi la validacion (modo demo, argmax) no toca ninguna secuencia aleatoria del entrenamiento.
  Prueba de humo (24.09, cruce, base 42, 60 episodios, validacion 999 cada 10; humo/dqn_humo_cruce.csv):
  val 15.91 / 15.08 / 15.10 / 16.52 / 15.01 / 15.07 en los episodios 10..60, mejor 15.01 (ep 50)
  frente a 23.19 s del fijo del cruce: pasa con estos HIPER, que quedan congelados sin reintento.

Protocolo (ESPEC seccion 3): episodio k con semilla SUMO base + k; validacion con la red en
linea congelada (argmax) en --val-seeds cada --eval-cada episodios y en el ultimo
(rl_ippo.validar, que ademas guarda y restaura el RNG global); checkpoint en cada validacion
(checkpoints/<tag>_ep<NNN>.pt/.json, tag = <esc>_dqn_s<base>); politica publicada =
checkpoint de menor val (empate: el mas tardio) en politica_<esc>_dqn_s<base>.pt/.json con
ep_elegido, val_elegido, val_serie, val_seeds, algoritmo = dqn, variante = vecinos, recompensa,
base, episodios, escenario, git e hiperparametros. CSV resultados_<tag>.csv reescrito en cada
corrida, con las metricas de rl_ippo (incluidos ret_retraso, ret_colas, ret_spill), val_*,
algoritmo, recompensa_tipo (= retraso; "recompensa" ya es una metrica) y diagnosticos de DQN.

Interfaz para evaluar.py:
  preparar(escenario) -> C de rl_ippo
  cargar(ruta) -> (red, meta)
  correr_episodio("demo", red, gui, delay, seed, tripinfo=None, serie=None, latencia=0,
                  perdida=0.0) -> dict de metricas (el mismo que rl_ippo.correr_episodio)
"""
import os
import csv
import sys
import json
import time
import shutil
import argparse

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

import rl_ippo as ri

HIPER = {"gamma": 0.95, "lr": 5e-4, "minibatch": 64, "replay": 100000, "inicio": 1000,
         "objetivo": 1000, "grad": 10.0, "eps_ini": 1.0, "eps_fin": 0.05, "eps_frac": 0.5}
OCULTAS = 64
VARIANTE = "vecinos"            # observacion con mensajes, recompensa de retraso
RECOMPENSA = "retraso"
DIAG = ["epsilon", "perdida_q", "q_medio", "actualizaciones", "transiciones"]
CAMPOS = (["variante", "base", "episodio", "semilla", "lr", "segundos", "vehiculos",
           "espera_prom", "timeloss_prom", "cola_prom", "cola_max",
           "recompensa", "recompensa_decision", "recompensa_total_decision",
           "decisiones", "decisiones_libres", "cambios_fase",
           "paradas_prom", "throughput", "co2_prom", "nox_prom", "no_terminados",
           "spillback_tasa", "spillback_seg", "spillback_eventos", "cola_max_enlace",
           "veh_max_enlace", "viaje_corredor_prom", "retraso_corredor_prom",
           "retraso_corredor_punta", "paradas_corredor", "paradas_corredor_le1",
           "spill_activaciones", "spill_suma"] + DIAG
          + ["eval_timeloss", "eval_espera", "ret_retraso", "ret_colas", "ret_spill"])

C = ri.C


def preparar(escenario):
    return ri.preparar(escenario)


# ---------------- Red Q ----------------
class RedQ(nn.Module):
    """MLP dim_obs-64-64-2 con ReLU; una salida por accion (0 mantener, 1 cambiar)."""

    def __init__(self, dim_obs, ocultas=OCULTAS):
        super().__init__()
        self.q = nn.Sequential(ri.capa(dim_obs, ocultas, 2 ** 0.5), nn.ReLU(),
                               ri.capa(ocultas, ocultas, 2 ** 0.5), nn.ReLU(),
                               ri.capa(ocultas, 2, 1.0))

    def forward(self, obs):
        return self.q(obs)


def enmascarar(q, mascara):
    """Acciones prohibidas a -inf (la mascara siempre deja al menos una legal)."""
    return q.masked_fill(mascara == 0, float("-inf"))


def guardar(red, ruta, meta):
    torch.save(red.state_dict(), ruta)
    with open(ruta.replace(".pt", ".json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)


def cargar(ruta):
    with open(ruta.replace(".pt", ".json"), encoding="utf-8") as f:
        meta = json.load(f)
    red = RedQ(meta["dim_obs"], meta["ocultas"])
    red.load_state_dict(torch.load(ruta, weights_only=True))
    red.eval()
    return red, meta


def voraz(red):
    """decidir de rl_ippo con la red congelada: argmax de Q entre las acciones legales."""
    def decidir(deciden, obs, mascara, modo, info):
        with torch.no_grad():
            q = enmascarar(red(torch.from_numpy(obs)), torch.from_numpy(mascara))
        return q.argmax(dim=1).tolist(), [None] * len(deciden)
    return decidir


# ---------------- Agente ----------------
class AgenteDQN:
    """Red en linea, red objetivo, replay circular y optimizador. decidir y transicion son los
    ganchos de rl_ippo.correr_episodio en modo train."""

    def __init__(self, dim_obs, hiper, rng):
        self.h, self.rng = hiper, rng
        self.red = RedQ(dim_obs)
        self.objetivo = RedQ(dim_obs)
        self.objetivo.load_state_dict(self.red.state_dict())
        self.opt = torch.optim.Adam(self.red.parameters(), lr=hiper["lr"])
        n = int(hiper["replay"])
        self.obs = np.zeros((n, dim_obs), dtype=np.float32)
        self.acc = np.zeros(n, dtype=np.int64)
        self.rec = np.zeros(n, dtype=np.float32)
        self.obs_sig = np.zeros((n, dim_obs), dtype=np.float32)
        self.masc_sig = np.zeros((n, 2), dtype=np.float32)
        self.fin = np.zeros(n, dtype=np.float32)
        self.pos, self.lleno = 0, 0
        self.actualizaciones, self.transiciones = 0, 0
        self.epsilon = hiper["eps_ini"]
        self.perdidas, self.q_medios = [], []

    def decidir(self, deciden, obs, mascara, modo, info):
        """epsilon-greedy: con probabilidad epsilon una accion legal al azar, si no el argmax."""
        with torch.no_grad():
            q = enmascarar(self.red(torch.from_numpy(obs)), torch.from_numpy(mascara))
        voraces = q.argmax(dim=1).tolist()
        acciones = []
        for k in range(len(deciden)):
            if self.rng.random() < self.epsilon:
                legales = np.flatnonzero(mascara[k])
                acciones.append(int(legales[self.rng.integers(len(legales))]))
            else:
                acciones.append(voraces[k])
        return acciones, [None] * len(deciden)

    def transicion(self, tls, obs, accion, recompensa, obs_sig, mascara_sig, info):
        """Guarda la transicion (terminal solo si la red se vacio) y hace una actualizacion."""
        i = self.pos
        self.obs[i], self.acc[i], self.rec[i] = obs, accion, recompensa
        self.obs_sig[i], self.masc_sig[i] = obs_sig, mascara_sig
        self.fin[i] = 1.0 if (info["ultima"] and info["vaciada"]) else 0.0
        self.pos = (i + 1) % len(self.obs)
        self.lleno = min(self.lleno + 1, len(self.obs))
        self.transiciones += 1
        if self.lleno >= self.h["inicio"]:
            self.actualizar()

    def actualizar(self):
        idx = self.rng.integers(0, self.lleno, size=int(self.h["minibatch"]))
        obs = torch.from_numpy(self.obs[idx])
        acc = torch.from_numpy(self.acc[idx])
        rec = torch.from_numpy(self.rec[idx])
        obs_sig = torch.from_numpy(self.obs_sig[idx])
        masc_sig = torch.from_numpy(self.masc_sig[idx])
        fin = torch.from_numpy(self.fin[idx])
        with torch.no_grad():
            # Double DQN: elige la red en linea (solo acciones legales), valora la objetivo
            a_sig = enmascarar(self.red(obs_sig), masc_sig).argmax(dim=1, keepdim=True)
            q_sig = self.objetivo(obs_sig).gather(1, a_sig).squeeze(1)
            y = rec + self.h["gamma"] * (1.0 - fin) * q_sig
        q = self.red(obs).gather(1, acc.unsqueeze(1)).squeeze(1)
        perdida = F.smooth_l1_loss(q, y)
        self.opt.zero_grad()
        perdida.backward()
        nn.utils.clip_grad_norm_(self.red.parameters(), self.h["grad"])
        self.opt.step()
        self.actualizaciones += 1
        if self.actualizaciones % int(self.h["objetivo"]) == 0:
            self.objetivo.load_state_dict(self.red.state_dict())
        self.perdidas.append(perdida.item())
        self.q_medios.append(float(q.detach().mean()))

    def diagnostico(self):
        """Resumen del episodio y reinicio de los acumuladores."""
        d = {"epsilon": round(self.epsilon, 4),
             "perdida_q": round(float(np.mean(self.perdidas)), 5) if self.perdidas else "",
             "q_medio": round(float(np.mean(self.q_medios)), 4) if self.q_medios else "",
             "actualizaciones": self.actualizaciones, "transiciones": self.transiciones}
        self.perdidas, self.q_medios = [], []
        return d


def epsilon_de(ep, episodios, h):
    """Lineal de eps_ini (episodio 1) a eps_fin al terminar la fraccion eps_frac de los episodios."""
    tramo = max(1.0, h["eps_frac"] * episodios)
    return max(h["eps_fin"], h["eps_ini"] - (h["eps_ini"] - h["eps_fin"]) * (ep - 1) / tramo)


# ---------------- Episodio ----------------
def correr_episodio(modo, red, gui, delay, seed, tripinfo=None, serie=None, latencia=0,
                    perdida=0.0, agente=None):
    """modo demo: argmax de red. modo train: decide y aprende el agente (red se ignora).
    Devuelve el dict de metricas de rl_ippo.correr_episodio."""
    if modo == "train":
        decidir, transicion = agente.decidir, agente.transicion
    else:
        decidir, transicion = voraz(red), None
    if tripinfo is None:
        tripinfo = f"tripinfo_{C['escenario']}_dqn_{modo}.xml"
    return ri.correr_episodio(modo, None, gui, delay, seed, tripinfo=tripinfo, serie=serie,
                              latencia=latencia, perdida=perdida, variante=VARIANTE,
                              decidir=decidir, transicion=transicion)


def meta_base(args, val_seeds):
    return {"escenario": C["escenario"], "variante": VARIANTE, "algoritmo": "dqn",
            "recompensa": RECOMPENSA, "base": args.seed, "episodios": args.episodios,
            "dim_obs": C["dim_obs"], "n_id": C["n_id"], "lados": list(C["lados"]),
            "ocultas": OCULTAS, "hiper": HIPER, "w1": ri.W1, "w2": ri.W2, "escala_r": ri.ESCALA_R,
            "fase_av": C["fase_av"], "vecinos": C["vecinos"], "cap": C["cap"], "plazas": C["plazas"],
            "latencia_entrenamiento": 0, "perdida_entrenamiento": 0.0, "val_seeds": val_seeds,
            "torch": torch.__version__, "python": sys.version.split()[0], "sumo": "1.25.0",
            "git": ri.hash_git(), "features": ri.nombres_features()}


# ---------------- Main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["train", "demo"])
    ap.add_argument("--escenario", choices=sorted(ri.ESCENARIOS), default="corredor")
    ap.add_argument("--episodios", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42, help="semilla base (entrenamiento: base + episodio)")
    ap.add_argument("--eval-cada", type=int, default=10, help="validar cada N episodios (0 = nunca)")
    ap.add_argument("--val-seeds", default="999,1999", help="semillas de validacion separadas por coma")
    ap.add_argument("--csv", default=None, help="CSV de salida (defecto resultados_<esc>_dqn_s<seed>.csv)")
    ap.add_argument("--hiper", default="", help="cambios a HIPER, p. ej. lr=1e-3,objetivo=500")
    ap.add_argument("--politica", default=None, help="archivo .pt para demo")
    ap.add_argument("--latencia", type=int, default=0, help="segundos de retardo del canal (demo)")
    ap.add_argument("--perdida", type=float, default=0.0, help="probabilidad de perder un mensaje (demo)")
    ap.add_argument("--serie", action="store_true")
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--delay", type=int, default=30)
    args = ap.parse_args()
    for cambio in [c for c in args.hiper.split(",") if c]:
        clave, valor = cambio.split("=")
        HIPER[clave] = float(valor)

    preparar(args.escenario)
    esc = args.escenario
    rng = ri.sembrar(args.seed)          # siembra random/numpy/torch, 1 hilo, determinista

    if args.modo == "demo":
        red, meta = cargar(args.politica)
        assert meta["dim_obs"] == C["dim_obs"], \
            f"la politica espera {meta['dim_obs']} entradas y {esc} da {C['dim_obs']}"
        serie = f"serie_{esc}_dqn_s{args.seed}.csv" if args.serie else None
        res = correr_episodio("demo", red, args.gui, args.delay, args.seed, serie=serie,
                              latencia=args.latencia, perdida=args.perdida)
        print(f"DQN ({esc}):", res)
        return

    val_seeds = [int(s) for s in args.val_seeds.split(",") if s.strip()]
    agente = AgenteDQN(C["dim_obs"], HIPER, rng)
    etiqueta = f"{esc}_dqn_s{args.seed}"
    ri.limpiar_checkpoints(etiqueta)
    campos = CAMPOS + [f"val_{s}" for s in val_seeds] + ["val", "algoritmo", "recompensa_tipo"]
    ruta_csv = args.csv or f"resultados_{etiqueta}.csv"
    salida = open(ruta_csv, "w", newline="")          # se reescribe: la cola puede reintentar
    escritor = csv.DictWriter(salida, fieldnames=campos, extrasaction="ignore")
    escritor.writeheader()
    print(f"DQN en {esc}: {args.episodios} episodios, semilla base {args.seed}, dim_obs {C['dim_obs']}, "
          f"{sum(p.numel() for p in agente.red.parameters())} parametros, hiper {HIPER}")
    meta = meta_base(args, val_seeds)
    val_serie = []
    for ep in range(1, args.episodios + 1):
        agente.epsilon = epsilon_de(ep, args.episodios, HIPER)
        t0 = time.time()
        res = correr_episodio("train", None, args.gui, args.delay, args.seed + ep,
                              tripinfo=f"tripinfo_{etiqueta}_train.xml", agente=agente)
        fila = {"variante": VARIANTE, "base": args.seed, "episodio": ep, "semilla": args.seed + ep,
                "lr": f"{HIPER['lr']:.2e}", "segundos": round(time.time() - t0, 1), **res,
                **agente.diagnostico(), "algoritmo": "dqn", "recompensa_tipo": RECOMPENSA}
        if val_seeds and args.eval_cada and (ep % args.eval_cada == 0 or ep == args.episodios):
            agente.red.eval()
            fila.update(ri.validar(None, val_seeds, VARIANTE, f"tripinfo_{etiqueta}_val.xml",
                                   decidir=voraz(agente.red)))
            agente.red.train()
            val_serie.append([ep] + [fila[f"val_{s}"] for s in val_seeds] + [fila["val"]])
            guardar(agente.red, ri.ruta_checkpoint(etiqueta, ep),
                    {**meta, "ep_checkpoint": ep, "val_checkpoint": fila["val"],
                     **{f"val_{s}": fila[f"val_{s}"] for s in val_seeds}})
        escritor.writerow(fila)
        salida.flush()
        print(f"Ep {ep:3d}  timeLoss={res['timeloss_prom']:6.2f}  espera={res['espera_prom']:5.2f}  "
              f"cambios={res['cambios_fase']:4d}  eps={fila['epsilon']:.3f}  perdida={fila['perdida_q']}  "
              f"q={fila['q_medio']}  {fila['segundos']}s"
              + (f"  val={fila['val']:.2f}" if "val" in fila else ""), flush=True)
    salida.close()

    ruta = f"politica_{esc}_dqn_s{args.seed}.pt"
    if val_serie:
        elegida = ri.elegir_checkpoint(val_serie)
        meta.update({"ep_elegido": elegida[0], "val_elegido": elegida[-1], "val_serie": val_serie})
        shutil.copyfile(ri.ruta_checkpoint(etiqueta, elegida[0]), ruta)
        with open(ruta.replace(".pt", ".json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=1, ensure_ascii=False)
    else:
        meta.update({"ep_elegido": args.episodios, "val_elegido": None, "val_serie": []})
        guardar(agente.red, ruta, meta)
    print(f"Politica guardada en {ruta} (episodio {meta['ep_elegido']}, val {meta['val_elegido']})")


if __name__ == "__main__":
    main()
