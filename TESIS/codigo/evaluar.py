"""
evaluar.py - Evaluacion final de un escenario con politica congelada y varias semillas.

Uso:
  python evaluar.py --escenario cruce [--semillas 1001-1010] [--brazos baseline,actuado,demo]

Corre los tres controles (tiempo fijo tuneado, actuado nativo de SUMO y agente RL con
epsilon 0) con las MISMAS semillas, fuera del rango que uso el entrenamiento, y escribe:
  evaluacion_<esc>.csv          una fila por (brazo, semilla) con todas las metricas
  evaluacion_<esc>_resumen.csv  por brazo y metrica: n, media, sd, IC95 %, delta % respecto
                                al fijo con IC95 % bootstrap, p de Wilcoxon pareado,
                                p de Mann-Whitney exacta y delta de Cliff
  vehiculos_<esc>_<brazo>.csv   una fila por vehiculo de la primera semilla (distribuciones)
  serie_<esc>_<brazo>_s<semilla>.csv  cola por aproximacion cada 60 s, primera semilla
"""
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
            "throughput", "co2_prom", "nox_prom", "recompensa_decision", "cambios_fase"]
NOMBRE_BRAZO = {"baseline": "fijo", "actuado": "actuado", "demo": "rl"}


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
    """IC95 % bootstrap (pareado por semilla) del cambio porcentual de la media respecto al fijo."""
    rng = np.random.default_rng(0)
    base, otro = np.array(base), np.array(otro)
    idx = rng.integers(0, len(base), size=(n_boot, len(base)))
    deltas = (otro[idx].mean(axis=1) - base[idx].mean(axis=1)) / base[idx].mean(axis=1) * 100
    return np.percentile(deltas, 2.5), np.percentile(deltas, 97.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escenario", choices=["cruce", "cruce2", "corredor", "red"], default="cruce")
    ap.add_argument("--semillas", default="1001-1010")
    ap.add_argument("--brazos", default="baseline,actuado,demo")
    args = ap.parse_args()
    esc = args.escenario
    semillas = rango(args.semillas)
    brazos = args.brazos.split(",")
    mod, Q = preparar(esc)

    filas = []
    for brazo in brazos:
        for i, semilla in enumerate(semillas):
            random.seed(semilla)
            primera = (i == 0)
            nombre = NOMBRE_BRAZO[brazo]
            tripinfo = f"tripinfo_{esc}_eval.xml"
            serie = f"serie_{esc}_{nombre}_s{semilla}.csv" if primera else None
            res = mod.correr_episodio(brazo, copy.deepcopy(Q), 0.0, False, 0, semilla,
                                      tripinfo=tripinfo, serie=serie)
            if primera:
                vehiculos = comun.vehiculos_tripinfo(tripinfo)
                with open(f"vehiculos_{esc}_{nombre}.csv", "w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=list(vehiculos[0].keys()))
                    w.writeheader()
                    w.writerows(vehiculos)
            fila = {"brazo": nombre, "semilla": semilla, **{m: res[m] for m in METRICAS}}
            filas.append(fila)
            print(f"{nombre:8s} semilla {semilla}: timeLoss={res['timeloss_prom']:6.2f}  "
                  f"espera={res['espera_prom']:6.2f}  paradas={res['paradas_prom']:.2f}  "
                  f"CO2={res['co2_prom']} g", flush=True)

    with open(f"evaluacion_{esc}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["brazo", "semilla"] + METRICAS)
        w.writeheader()
        w.writerows(filas)

    # Resumen estadistico por brazo y metrica, comparado contra el fijo
    resumen = []
    por_brazo = {b: [fl for fl in filas if fl["brazo"] == b] for b in ("fijo", "actuado", "rl")
                 if any(fl["brazo"] == b for fl in filas)}
    base = por_brazo.get("fijo")
    for brazo, lista in por_brazo.items():
        for m in METRICAS:
            vals = [float(fl[m]) for fl in lista if fl[m] != ""]
            if not vals:
                continue
            fila = {"brazo": brazo, "metrica": m, "n": len(vals),
                    "media": round(statistics.mean(vals), 3),
                    "sd": round(statistics.stdev(vals), 3) if len(vals) > 1 else 0,
                    "ic95": round(ic95(vals), 3)}
            if base is not None and brazo != "fijo":
                vb = [float(fl[m]) for fl in base if fl[m] != ""]
                if len(vb) == len(vals) and statistics.mean(vb) != 0:
                    media_b = statistics.mean(vb)
                    fila["delta_pct"] = round((statistics.mean(vals) - media_b) / media_b * 100, 1)
                    lo, hi = bootstrap_delta(vb, vals)
                    fila["delta_ic95"] = f"[{lo:.1f}, {hi:.1f}]"
                    difs = [a - b for a, b in zip(vals, vb)]
                    p_w = stats.wilcoxon(difs).pvalue if any(d != 0 for d in difs) else 1.0
                    p_mw = stats.mannwhitneyu(vals, vb, method="auto").pvalue   # 'auto': exacta sin empates
                    fila["p_wilcoxon"] = f"{p_w:.3g}"
                    fila["p_mannwhitney"] = f"{p_mw:.3g}"
                    fila["cliff"] = round(cliff(vals, vb), 2)
            resumen.append(fila)

    campos = ["brazo", "metrica", "n", "media", "sd", "ic95", "delta_pct", "delta_ic95",
              "p_wilcoxon", "p_mannwhitney", "cliff"]
    with open(f"evaluacion_{esc}_resumen.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(resumen)

    print(f"\nResumen ({esc}, {len(semillas)} semillas {semillas[0]}-{semillas[-1]}):")
    print(f"{'metrica':20s} {'fijo':>16s} {'actuado':>16s} {'rl':>16s}   delta rl vs fijo   p Wilcoxon")
    for m in METRICAS:
        celdas = []
        for b in ("fijo", "actuado", "rl"):
            r = next((x for x in resumen if x["brazo"] == b and x["metrica"] == m), None)
            celdas.append(f"{r['media']:8.2f} ±{r['ic95']:5.2f}" if r else " " * 16)
        rl = next((x for x in resumen if x["brazo"] == "rl" and x["metrica"] == m), {})
        print(f"{m:20s} {celdas[0]} {celdas[1]} {celdas[2]}   {rl.get('delta_pct', ''):>6} % "
              f"{rl.get('delta_ic95', ''):>16}   {rl.get('p_wilcoxon', '')}")


if __name__ == "__main__":
    main()
