"""
rl_mappo.py - Modulo U4, variante MAPPO: el actor de ippo_vecinos (la misma red Politica de
rl_ippo, la misma observacion con mensajes de los vecinos, la misma mascara y la misma
recompensa "retraso") entrenado con un CRITICO CENTRALIZADO. Durante el entrenamiento V ve el
estado global = concatenacion de las observaciones de todos los semaforos (orden de
C["indice"]) en el instante de la decision, mas el one-hot del semaforo que decide. En la
ejecucion solo se usa el actor: cada semaforo decide con su propia observacion, igual que IPPO
(entrenamiento centralizado, ejecucion descentralizada).

Uso (desde demo_rl/plan2, como la cola de trabajos):
  python ../rl_mappo.py train --escenario red --seed 42 --episodios 200 [--eval-cada 10]
                              [--val-seeds 999,1999] [--csv R] [--hiper k=v,...]
  python ../rl_mappo.py demo  --escenario red --politica politica_red_mappo_s42.pt [--seed S]
                              [--latencia L] [--perdida P] [--serie] [--gui]

Salidas del entrenamiento (tag = <esc>_mappo_s<base>):
  resultados_<tag>.csv                      una fila por episodio (se reescribe desde cero)
  checkpoints/<tag>_ep<NNN>.pt/.json        actor (formato Politica de rl_ippo) en cada validacion
  checkpoints/<tag>_critico_ep<NNN>.pt      critico central de ese checkpoint
  politica_<esc>_mappo_s<base>.pt/.json     politica publicada = checkpoint de menor val
  critico_<esc>_mappo_s<base>.pt            su critico central (no hace falta para evaluar)
  tripinfo_<tag>_train.xml, tripinfo_<tag>_val.xml
La politica publicada es un Politica de rl_ippo (actor entrenado; su critico local queda con la
inicializacion y no se usa) con meta "algoritmo": "mappo" y "variante": "vecinos", asi que
rl_ippo.correr_episodio("demo", politica, ..., variante="vecinos") la juega tal cual. Este
modulo expone tambien preparar, cargar(ruta) y correr_episodio con la firma de rl_ippo.

Todo lo demas es rl_ippo sin cambios, a traves de su interfaz de decisores externos
(decidir / transicion / con_estado): simulacion, reloj de decision, mensajeria, recompensa
(suma por segundo / 5 * ESCALA_R), GAE (rl_ippo.gae), validacion (rl_ippo.validar, que guarda
y restaura el RNG), checkpoints y eleccion de la politica publicada. Lo unico propio es el
critico central y la actualizacion PPO que lo usa (copia de rl_ippo.actualizar con V separado).

Hiperparametros: los HIPER de rl_ippo sin cambios (gamma 0.95, lambda 0.95, clip 0.2,
10 epocas, minilote 64, lr 1e-3 lineal a 0, entropia 0.01, valor 0.5, recorte de gradiente 0.5
por red). Un solo Adam (eps 1e-5) para actor y critico central, como IPPO. Critico central: MLP
de dos capas ocultas de 64 con tanh (como el de IPPO), entrada n_tls * dim_obs + n_tls. Con la
misma semilla base el actor arranca con los mismos pesos que el de ippo_vecinos.
Prueba de humo en cruce (24.09.2026, base 42, 30 episodios, validacion cada 5; con un solo
semaforo el critico central es el de IPPO mas un one-hot constante): val 36.30, 18.15, 15.79,
15.26, 15.37, 14.86, la misma curva que IPPO con estos HIPER (humo5: 36.43, 16.90, 15.38 ...
14.99) y al nivel del actuado (15.46): no hizo falta tocar HIPER.

Plan de pruebas v2 (24.09.2026, plan2/ESPEC.md): archivo nuevo. Protocolo de la seccion 3
(semillas base 42/2042/4042, episodio k con semilla base + k, validacion argmax cada --eval-cada
episodios y en el ultimo con las semillas 999 y 1999, checkpoint en cada validacion, publicada =
menor val con empate al mas tardio), columnas de la seccion 5 (las de rl_ippo, con
algoritmo = mappo y recompensa_tipo = retraso).
"""
import csv
import json
import time
import shutil
import argparse

import numpy as np
import torch
import torch.nn as nn

import rl_ippo as ri
from rl_ippo import C, Politica, capa, preparar

VARIANTE = "vecinos"            # observacion con mensajes; recompensa "retraso"
ALGORITMO = "mappo"
HIPER = dict(ri.HIPER)          # copia: --hiper no toca el dict de rl_ippo
OCULTAS_CRITICO = ri.OCULTAS


# ---------------- Critico central ----------------
class CriticoCentral(nn.Module):
    """V(estado global, one-hot del semaforo que decide): MLP de dos capas ocultas con tanh."""

    def __init__(self, n_tls, dim_obs, ocultas=OCULTAS_CRITICO):
        super().__init__()
        self.n_tls, self.dim_obs = n_tls, dim_obs
        self.red = nn.Sequential(capa(n_tls * dim_obs + n_tls, ocultas, 2 ** 0.5), nn.Tanh(),
                                 capa(ocultas, ocultas, 2 ** 0.5), nn.Tanh(),
                                 capa(ocultas, 1, 1.0))

    def forward(self, entrada):
        return self.red(entrada).squeeze(-1)


def entrada_critico(estado, tls):
    """Estado global (n_tls * dim_obs) seguido del one-hot del semaforo tls."""
    uno = np.zeros(len(C["indice"]), dtype=np.float32)
    uno[C["indice"][tls]] = 1.0
    return np.concatenate([estado, uno]).astype(np.float32)


# ---------------- Recoleccion de un episodio (ganchos de rl_ippo) ----------------
class Recolector:
    """decidir muestrea del actor y anota el valor del critico central; transicion arma, por
    semaforo, el mismo buffer que rl_ippo.gae espera (mas la entrada del critico)."""

    def __init__(self, politica, critico):
        self.politica, self.critico = politica, critico
        self.buffer = {tls: {"obs": [], "mascara": [], "accion": [], "logp": [], "valor": [],
                             "entrada": [], "recompensa": [], "v_final": 0.0}
                       for tls in C["indice"]}

    def decidir(self, deciden, obs, masc, modo, info):
        with torch.no_grad():
            logits = Politica.enmascarar(self.politica.actor(torch.from_numpy(obs)), torch.from_numpy(masc))
            if modo == "train":
                dist = torch.distributions.Categorical(logits=logits)
                acciones = dist.sample()
                logp = dist.log_prob(acciones)
            else:
                acciones = logits.argmax(dim=1)
                logp = torch.zeros(len(deciden))
            entradas = np.stack([entrada_critico(info["estado"], tls) for tls in deciden])
            valores = self.critico(torch.from_numpy(entradas))
        extras = [{"logp": float(logp[k]), "valor": float(valores[k]), "mascara": masc[k],
                   "entrada": entradas[k]} for k in range(len(deciden))]
        return acciones, extras

    def transicion(self, tls, obs, accion, recompensa, obs_sig, mascara_sig, info):
        b, e = self.buffer[tls], info["extra"]
        b["obs"].append(obs)
        b["mascara"].append(e["mascara"])
        b["accion"].append(int(accion))
        b["logp"].append(e["logp"])
        b["valor"].append(e["valor"])
        b["entrada"].append(e["entrada"])
        b["recompensa"].append(recompensa)
        if info["ultima"]:
            if info["vaciada"]:
                b["v_final"] = 0.0                 # terminal real
            else:                                  # truncado a 6000 s: se estima con el critico
                with torch.no_grad():
                    x = torch.from_numpy(entrada_critico(info["estado_sig"], tls)).unsqueeze(0)
                    b["v_final"] = float(self.critico(x)[0])

    def lote(self):
        """El lote de rl_ippo.gae (mismo orden de agentes) mas las entradas del critico."""
        obs, masc, acc, logp, adv, ret = ri.gae(self.buffer, HIPER["gamma"], HIPER["lam"])
        entradas = [x for b in self.buffer.values() if b["recompensa"]
                    for x in b["entrada"][:len(b["recompensa"])]]
        return obs, masc, acc, logp, adv, ret, torch.from_numpy(np.stack(entradas))


def actualizar(politica, critico, opt, lote, hiper, rng):
    """rl_ippo.actualizar con el valor del critico central en vez del critico local."""
    obs, masc, acc, logp_viejo, adv, ret, entradas = lote
    n = len(obs)
    idx = np.arange(n)
    libres = masc.sum(dim=1) > 1
    diag = {"perdida_politica": [], "perdida_valor": [], "entropia_libre": [], "kl_aprox": [],
            "clipfrac": []}
    for _ in range(hiper["epocas"]):
        rng.shuffle(idx)
        for ini in range(0, n, hiper["minibatch"]):
            b = torch.from_numpy(idx[ini:ini + hiper["minibatch"]])
            logits = politica.actor(obs[b])
            valor = critico(entradas[b])
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
            nn.utils.clip_grad_norm_(politica.actor.parameters(), hiper["grad"])     # recorte por red
            nn.utils.clip_grad_norm_(critico.parameters(), hiper["grad"])
            opt.step()
            with torch.no_grad():
                diag["perdida_politica"].append(float(perdida_pol))
                diag["perdida_valor"].append(float(perdida_val))
                diag["entropia_libre"].append(float(entropia))
                diag["kl_aprox"].append(float(((ratio - 1) - (logp - logp_viejo[b])).mean()))
                diag["clipfrac"].append(float(((ratio - 1).abs() > hiper["clip"]).float().mean()))
    return {k: round(float(np.mean(v)), 4) for k, v in diag.items()}


# ---------------- Interfaz para evaluar.py ----------------
def cargar(ruta):
    """(Politica, meta) de una politica publicada o un checkpoint (formato de rl_ippo)."""
    politica, meta = Politica.cargar(ruta)
    if C and meta["dim_obs"] != C["dim_obs"]:
        raise SystemExit(f"{ruta} espera {meta['dim_obs']} entradas y {C['escenario']} da {C['dim_obs']}")
    return politica, meta


def correr_episodio(modo, politica, gui, delay, seed, tripinfo=None, serie=None, latencia=0,
                    perdida=0.0, variante=VARIANTE, buffer=None, decidir=None, transicion=None,
                    con_estado=False):
    """rl_ippo.correr_episodio con variante vecinos por defecto (el actor de MAPPO es el de
    ippo_vecinos) y tripinfo por defecto propio."""
    if tripinfo is None:
        tripinfo = f"tripinfo_{C['escenario']}_mappo_{modo}.xml"
    return ri.correr_episodio(modo, politica, gui, delay, seed, tripinfo=tripinfo, serie=serie,
                              latencia=latencia, perdida=perdida, variante=variante, buffer=buffer,
                              decidir=decidir, transicion=transicion, con_estado=con_estado)


# ---------------- Entrenamiento ----------------
def meta_mappo(args, val_seeds, n_param_critico):
    meta = ri.meta_base(argparse.Namespace(variante=VARIANTE, seed=args.seed, episodios=args.episodios),
                        val_seeds)
    meta.update({"algoritmo": ALGORITMO, "variante": VARIANTE, "recompensa": ri.RECOMPENSA[VARIANTE],
                 "hiper": HIPER,
                 "critico_central": {"entrada": len(C["indice"]) * C["dim_obs"] + len(C["indice"]),
                                     "ocultas": OCULTAS_CRITICO, "parametros": n_param_critico,
                                     "archivo": f"critico_{C['escenario']}_mappo_s{args.seed}.pt"},
                 "critico_local": "sin entrenar, no se usa (solo cuenta el actor)"})
    return meta


def entrenar(args):
    esc = C["escenario"]
    rng = ri.sembrar(args.seed)
    val_seeds = [int(s) for s in args.val_seeds.split(",") if s.strip()]
    politica = Politica(C["dim_obs"])                 # mismo actor inicial que ippo con esa base
    # el critico se inicializa con un RNG aparte: el torch RNG queda como en IPPO y el primer
    # episodio (antes de la primera actualizacion) es identico al de ippo_vecinos con esa base
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(args.seed + 1)
        critico = CriticoCentral(len(C["indice"]), C["dim_obs"])
    opt = torch.optim.Adam(list(politica.actor.parameters()) + list(critico.parameters()),
                           lr=HIPER["lr"], eps=1e-5)
    etiqueta = f"{esc}_{ALGORITMO}_s{args.seed}"
    ri.limpiar_checkpoints(etiqueta)
    ri.limpiar_checkpoints(etiqueta + "_critico")
    ruta_csv = args.csv or f"resultados_{etiqueta}.csv"
    salida = open(ruta_csv, "w", newline="")          # se reescribe: la cola puede reintentar
    escritor = csv.DictWriter(salida, fieldnames=ri.CAMPOS_IPPO, extrasaction="ignore")
    escritor.writeheader()
    n_critico = sum(p.numel() for p in critico.parameters())
    print(f"MAPPO en {esc}: {args.episodios} episodios, semilla base {args.seed}, dim_obs {C['dim_obs']}, "
          f"actor {sum(p.numel() for p in politica.actor.parameters())} y critico central {n_critico} "
          f"parametros", flush=True)
    meta = meta_mappo(args, val_seeds, n_critico)
    val_serie = []
    for ep in range(1, args.episodios + 1):
        lr = HIPER["lr"] * (1 - (ep - 1) / args.episodios)
        for g in opt.param_groups:
            g["lr"] = lr
        rec = Recolector(politica, critico)
        t0 = time.time()
        res = correr_episodio("train", None, args.gui, args.delay, args.seed + ep,
                              tripinfo=f"tripinfo_{etiqueta}_train.xml", decidir=rec.decidir,
                              transicion=rec.transicion, con_estado=True)
        diag = actualizar(politica, critico, opt, rec.lote(), HIPER, rng)
        fila = {"variante": VARIANTE, "base": args.seed, "episodio": ep, "semilla": args.seed + ep,
                "lr": f"{lr:.2e}", "segundos": round(time.time() - t0, 1), **res, **diag,
                "algoritmo": ALGORITMO, "recompensa_tipo": ri.RECOMPENSA[VARIANTE]}
        if val_seeds and args.eval_cada and (ep % args.eval_cada == 0 or ep == args.episodios):
            fila.update(ri.validar(politica, val_seeds, VARIANTE, f"tripinfo_{etiqueta}_val.xml"))
            val_serie.append([ep] + [fila[f"val_{s}"] for s in val_seeds] + [fila["val"]])
            politica.guardar(ri.ruta_checkpoint(etiqueta, ep),
                             {**meta, "ep_checkpoint": ep, "val_checkpoint": fila["val"],
                              **{f"val_{s}": fila[f"val_{s}"] for s in val_seeds}})
            torch.save(critico.state_dict(), ri.ruta_checkpoint(etiqueta + "_critico", ep))
        escritor.writerow(fila)
        salida.flush()
        print(f"Ep {ep:3d}  timeLoss={res['timeloss_prom']:6.2f}  espera={res['espera_prom']:5.2f}  "
              f"r/dec={res['recompensa_decision']:6.2f}  cambios={res['cambios_fase']:4d}  "
              f"kl={diag['kl_aprox']:.4f} ent={diag['entropia_libre']:.3f}  {fila['segundos']}s"
              + (f"  val={fila['val']:.2f}" if "val" in fila else ""), flush=True)
    salida.close()

    ruta = f"politica_{esc}_{ALGORITMO}_s{args.seed}.pt"
    ruta_critico = meta["critico_central"]["archivo"]
    if val_serie:
        elegida = ri.elegir_checkpoint(val_serie)
        meta.update({"ep_elegido": elegida[0], "val_elegido": elegida[-1], "val_serie": val_serie,
                     "eval_999_final": val_serie[-1][1]})
        shutil.copyfile(ri.ruta_checkpoint(etiqueta, elegida[0]), ruta)
        shutil.copyfile(ri.ruta_checkpoint(etiqueta + "_critico", elegida[0]), ruta_critico)
        with open(ruta.replace(".pt", ".json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=1, ensure_ascii=False)
    else:
        meta.update({"ep_elegido": args.episodios, "val_elegido": None, "val_serie": [],
                     "eval_999_final": None})
        politica.guardar(ruta, meta)
        torch.save(critico.state_dict(), ruta_critico)
    print(f"Politica guardada en {ruta} (episodio {meta['ep_elegido']}, val {meta['val_elegido']}); "
          f"critico central en {ruta_critico}")


# ---------------- Main ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["train", "demo"])
    ap.add_argument("--escenario", choices=sorted(ri.ESCENARIOS), default="corredor")
    ap.add_argument("--episodios", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42, help="semilla base (entrenamiento: base + episodio)")
    ap.add_argument("--eval-cada", type=int, default=10, help="validar cada N episodios (0 = nunca)")
    ap.add_argument("--val-seeds", default="999,1999", help="semillas de validacion separadas por coma")
    ap.add_argument("--latencia", type=int, default=0, help="segundos de retardo del canal (demo)")
    ap.add_argument("--perdida", type=float, default=0.0, help="probabilidad de perder un mensaje (demo)")
    ap.add_argument("--csv", default=None,
                    help="CSV de salida (por defecto resultados_<esc>_mappo_s<seed>.csv)")
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
    if args.modo == "train":
        entrenar(args)
        return
    ri.sembrar(args.seed)
    politica, meta = cargar(args.politica)
    esc = args.escenario
    serie = f"serie_{esc}_mappo_s{args.seed}.csv" if args.serie else None
    res = correr_episodio("demo", politica, args.gui, args.delay, args.seed, serie=serie,
                          latencia=args.latencia, perdida=args.perdida,
                          variante=meta.get("variante", VARIANTE))
    print(f"MAPPO ({esc}):", res)


if __name__ == "__main__":
    main()
