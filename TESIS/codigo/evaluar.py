"""
evaluar.py - Evaluacion final de un escenario con politica congelada y varias semillas.

Uso:
  python evaluar.py --escenario cruce [--semillas 1001-1010] [--brazos baseline,actuado,demo]
  python evaluar.py --escenario red --ippo politica_red_local_s42.pt,politica_red_vecinos_s42.pt
  python evaluar.py --escenario red --brazos "" --ippo politica_red_vecinos_s42.pt --latencia 5 --perdida 0.3

Corre los controles pedidos con las MISMAS semillas, fuera del rango que uso el entrenamiento:
tiempo fijo tuneado (baseline), actuado nativo de SUMO, agente Q-learning con epsilon 0 (demo)
y las politicas IPPO de U4 (--ippo, una o varias). Escribe:
  evaluacion_<esc>.csv          una fila por (brazo, semilla); las filas de brazos que no se
                                corren en esta llamada se conservan del archivo anterior
  evaluacion_<esc>_resumen.csv  por brazo y metrica: n, media, sd, IC95 %, y frente al fijo
                                delta % con IC95 % bootstrap, p de Wilcoxon pareado, p de
                                Mann-Whitney y delta de Cliff; los brazos IPPO llevan ademas
                                el delta frente al actuado y frente al Q-learning
  vehiculos_<esc>_<brazo>.csv   una fila por vehiculo de la primera semilla (distribuciones)
  serie_<esc>_<brazo>_s<semilla>.csv y fases_<esc>_<brazo>_s<semilla>.csv, primera semilla
"""
import os
import csv
import copy
import json
import random
import argparse
import statistics

import numpy as np
from scipy import stats

import comun

METRICAS = ["timeloss_prom", "espera_prom", "cola_prom", "cola_max", "paradas_prom",
            "throughput", "co2_prom", "nox_prom", "recompensa_decision", "cambios_fase",
            "no_terminados",
            # solo en escenarios de varios cruces (corredor, red): quedan vacias en los demas
            "viaje_corredor_prom", "retraso_corredor_prom", "retraso_corredor_punta",
            "paradas_corredor", "paradas_corredor_le1",
            "spillback_tasa", "spillback_seg", "spillback_eventos", "cola_max_enlace", "veh_max_enlace"]
NOMBRE_BRAZO = {"baseline": "fijo", "actuado": "actuado", "demo": "rl"}
ORDEN_BRAZOS = ["fijo", "actuado", "rl"]
ESCENARIOS = ["cruce", "cruce2", "corredor", "red", "corredor_alta"]


def rango(texto):
    if "-" in texto:
        a, b = texto.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in texto.split(",")]


def preparar(escenario):
    """Carga el modulo que corresponde y fija sus variables globales para el escenario."""
    if escenario in ("cruce", "cruce2"):
        import rl_semaforo as mod
        mod.ESCENARIO = escenario
        mod.CFG = mod.ESCENARIOS[escenario]["cfg"]
        mod.TLS = mod.ESCENARIOS[escenario]["tls"]
        mod.APROX = mod.ESCENARIOS[escenario]["aprox"]
    else:
        import rl_corredor as mod
        mod.ESCENARIO = escenario
        mod.CFG = mod.ESCENARIOS[escenario]["cfg"]
        mod.SEMAFOROS = mod.ESCENARIOS[escenario]["semaforos"]
        mod.ENLACES = mod.ESCENARIOS[escenario]["enlaces"]
        mod.FLUJOS_CORREDOR = mod.ESCENARIOS[escenario]["flujos_corredor"]
    Q = None
    if os.path.exists(f"q_table_{escenario}.json"):
        with open(f"q_table_{escenario}.json") as f:
            Q = json.load(f)
    return mod, Q


def ic95(valores):
    n = len(valores)
    if n < 2:
        return 0.0
    return stats.t.ppf(0.975, n - 1) * statistics.stdev(valores) / n ** 0.5


def cliff(a, b):
    """Delta de Cliff: P(a > b) - P(a < b), tamano de efecto sin supuestos."""
    mas = sum(1 for x in a for y in b if x > y)
    menos = sum(1 for x in a for y in b if x < y)
    return (mas - menos) / (len(a) * len(b))


def bootstrap_delta(base, otro, n_boot=10000):
    """IC95 % bootstrap (pareado por semilla) del cambio porcentual de la media respecto a base."""
    rng = np.random.default_rng(0)
    base, otro = np.array(base), np.array(otro)
    idx = rng.integers(0, len(base), size=(n_boot, len(base)))
    deltas = (otro[idx].mean(axis=1) - base[idx].mean(axis=1)) / base[idx].mean(axis=1) * 100
    return np.percentile(deltas, 2.5), np.percentile(deltas, 97.5)


def comparar(vals, ref, sufijo=""):
    """delta %, IC bootstrap, Wilcoxon pareado, Mann-Whitney y Cliff de vals frente a ref."""
    if len(ref) != len(vals) or statistics.mean(ref) == 0:
        return {}
    media_r = statistics.mean(ref)
    difs = [a - b for a, b in zip(vals, ref)]
    p_w = stats.wilcoxon(difs).pvalue if any(d != 0 for d in difs) else 1.0
    p_mw = stats.mannwhitneyu(vals, ref, method="auto").pvalue   # 'auto': exacta sin empates
    lo, hi = bootstrap_delta(ref, vals)
    return {"delta_pct" + sufijo: round((statistics.mean(vals) - media_r) / media_r * 100, 1),
            "delta_ic95" + sufijo: f"[{lo:.1f}, {hi:.1f}]",
            "p_wilcoxon" + sufijo: f"{p_w:.3g}",
            "p_mannwhitney" + sufijo: f"{p_mw:.3g}",
            "cliff" + sufijo: round(cliff(vals, ref), 2)}


def guardar_vehiculos(esc, nombre, tripinfo):
    vehiculos = comun.vehiculos_tripinfo(tripinfo)
    with open(f"vehiculos_{esc}_{nombre}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(vehiculos[0].keys()))
        w.writeheader()
        w.writerows(vehiculos)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escenario", choices=ESCENARIOS, default="cruce")
    ap.add_argument("--semillas", default="1001-1010")
    ap.add_argument("--brazos", default="baseline,actuado,demo",
                    help="controles de rl_semaforo/rl_corredor a correr (vacio para ninguno)")
    ap.add_argument("--ippo", default="", help="politicas IPPO (.pt) separadas por coma")
    ap.add_argument("--latencia", type=int, default=0, help="latencia del canal para los brazos IPPO")
    ap.add_argument("--perdida", type=float, default=0.0, help="perdida de mensajes para los brazos IPPO")
    args = ap.parse_args()
    esc = args.escenario
    semillas = rango(args.semillas)
    brazos = [b for b in args.brazos.split(",") if b]
    politicas = [p for p in args.ippo.split(",") if p]
    mod, Q = preparar(esc)

    # Brazos IPPO: nombre = ippo_<variante> (+ _s<base> si la variante se repite, + _L<lat>p<perd>)
    ippo = []
    if politicas:
        import rl_ippo
        rl_ippo.preparar(esc)
        cargadas = [(ruta, *rl_ippo.Politica.cargar(ruta)) for ruta in politicas]
        variantes = [meta["variante"] for _, _, meta in cargadas]
        for ruta, politica, meta in cargadas:
            nombre = "ippo_" + meta["variante"]
            if variantes.count(meta["variante"]) > 1:
                nombre += f"_s{meta['base']}"
            if args.latencia or args.perdida:
                nombre += f"_L{args.latencia}p{int(round(args.perdida * 100))}"
            ippo.append((nombre, politica, meta))

    filas = []
    for brazo in brazos:
        nombre = NOMBRE_BRAZO[brazo]
        if brazo == "demo" and Q is None:
            print(f"No hay q_table_{esc}.json: se omite el brazo Q-learning")
            continue
        for i, semilla in enumerate(semillas):
            random.seed(semilla)
            tripinfo = f"tripinfo_{esc}_eval.xml"
            serie = f"serie_{esc}_{nombre}_s{semilla}.csv" if i == 0 else None
            res = mod.correr_episodio(brazo, copy.deepcopy(Q) if Q else {}, 0.0, False, 0, semilla,
                                      tripinfo=tripinfo, serie=serie)
            if i == 0:
                guardar_vehiculos(esc, nombre, tripinfo)
            filas.append({"brazo": nombre, "semilla": semilla, **{m: res.get(m, "") for m in METRICAS}})
            print(f"{nombre:16s} semilla {semilla}: timeLoss={res['timeloss_prom']:6.2f}  "
                  f"espera={res['espera_prom']:6.2f}  paradas={res['paradas_prom']:.2f}", flush=True)
    for nombre, politica, meta in ippo:
        import rl_ippo
        for i, semilla in enumerate(semillas):
            random.seed(semilla)
            tripinfo = f"tripinfo_{esc}_eval_ippo.xml"
            serie = f"serie_{esc}_{nombre}_s{semilla}.csv" if i == 0 else None
            res = rl_ippo.correr_episodio("demo", politica, False, 0, semilla, tripinfo=tripinfo,
                                          serie=serie, latencia=args.latencia, perdida=args.perdida,
                                          variante=meta["variante"])
            if i == 0:
                guardar_vehiculos(esc, nombre, tripinfo)
            filas.append({"brazo": nombre, "semilla": semilla, **{m: res.get(m, "") for m in METRICAS}})
            print(f"{nombre:16s} semilla {semilla}: timeLoss={res['timeloss_prom']:6.2f}  "
                  f"espera={res['espera_prom']:6.2f}  paradas={res['paradas_prom']:.2f}", flush=True)

    # Conservar del archivo anterior los brazos que no se corrieron ahora
    ruta = f"evaluacion_{esc}.csv"
    corridos = {f["brazo"] for f in filas}
    if os.path.exists(ruta):
        with open(ruta, newline="") as f:
            previas = [r for r in csv.DictReader(f) if r["brazo"] not in corridos]
        filas = previas + filas
    with open(ruta, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["brazo", "semilla"] + METRICAS, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)

    # Resumen estadistico por brazo y metrica
    nombres = [b for b in ORDEN_BRAZOS if any(fl["brazo"] == b for fl in filas)]
    nombres += sorted({fl["brazo"] for fl in filas} - set(nombres))
    por_brazo = {b: [fl for fl in filas if fl["brazo"] == b] for b in nombres}

    def valores(brazo, m):
        return [float(fl[m]) for fl in por_brazo.get(brazo, []) if fl.get(m, "") != ""]

    resumen = []
    for brazo in nombres:
        for m in METRICAS:
            vals = valores(brazo, m)
            if not vals:
                continue
            fila = {"brazo": brazo, "metrica": m, "n": len(vals),
                    "media": round(statistics.mean(vals), 3),
                    "sd": round(statistics.stdev(vals), 3) if len(vals) > 1 else 0,
                    "ic95": round(ic95(vals), 3)}
            if brazo != "fijo":
                fila.update(comparar(vals, valores("fijo", m)))
            if brazo.startswith("ippo"):
                fila.update(comparar(vals, valores("actuado", m), "_act"))
                fila.update(comparar(vals, valores("rl", m), "_rl"))
            resumen.append(fila)

    campos = ["brazo", "metrica", "n", "media", "sd", "ic95",
              "delta_pct", "delta_ic95", "p_wilcoxon", "p_mannwhitney", "cliff",
              "delta_pct_act", "delta_ic95_act", "p_wilcoxon_act", "p_mannwhitney_act", "cliff_act",
              "delta_pct_rl", "delta_ic95_rl", "p_wilcoxon_rl", "p_mannwhitney_rl", "cliff_rl"]
    with open(f"evaluacion_{esc}_resumen.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(resumen)

    print(f"\nResumen ({esc}, {len(semillas)} semillas {semillas[0]}-{semillas[-1]}); media +- IC95, "
          f"delta % vs fijo [IC95] y p de Wilcoxon:")
    for m in METRICAS:
        celdas = []
        for b in nombres:
            r = next((x for x in resumen if x["brazo"] == b and x["metrica"] == m), None)
            if r is None:
                continue
            delta = ""
            if "delta_pct" in r:
                delta = f" {r['delta_pct']:+.1f}% {r['delta_ic95']} p={r['p_wilcoxon']}"
            celdas.append(f"{b}={r['media']:.2f}+-{r['ic95']:.2f}{delta}")
        if celdas:
            print(f"{m:22s} " + " | ".join(celdas))


if __name__ == "__main__":
    main()
