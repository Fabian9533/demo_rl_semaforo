"""Diagnostico rapido de la curva del corredor: IPPO con mensajes frente a cuatro referencias y dos metricas.

Solo lee archivos existentes de plan2/ (sin simular). Para cada nivel compara, semilla a semilla (1001-1030),
la version evaluada de IPPO con: el fijo de la regla del 25.09, el fijo ajustado desde 10 s (regla de la
robustez, del barrido del 27.09), el ciclo minimo y el actuado; en timeLoss y en retraso total.
"""
import csv
import os
import statistics

P2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def leer(ruta):
    if not os.path.exists(ruta):
        return None
    with open(ruta, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    return {int(r["semilla"]): r for r in filas if r.get("semilla", "").isdigit()}


def media(d, m):
    return statistics.mean(float(r[m]) for r in d.values())


def delta(a, b, m):
    comunes = sorted(set(a) & set(b))
    ma = statistics.mean(float(a[s][m]) for s in comunes)
    mb = statistics.mean(float(b[s][m]) for s in comunes)
    return (ma - mb) / mb * 100, len(comunes)


NIVELES = [
    ("905", "demanda2/eval_dem_corredor_t905_ippo_vecinos_s4042.csv", "demanda2/eval_dem_corredor_t905_fijo.csv",
     "demanda/eval_corredor_f050_fijo.csv", "demanda2/eval_dem_corredor_t905_trivial.csv",
     "demanda2/eval_dem_corredor_t905_actuado.csv"),
    ("1358", "demanda2/eval_dem_corredor_t1358_ippo_vecinos_s42.csv", "demanda2/eval_dem_corredor_t1358_fijo.csv",
     "demanda/eval_corredor_f075_fijo.csv", "demanda2/eval_dem_corredor_t1358_trivial.csv",
     "demanda2/eval_dem_corredor_t1358_actuado.csv"),
    ("1810 P1", "parciales/eval_corredor_ippo_vecinos_s4042.csv", "parciales/eval_corredor_fijo_2509.csv",
     "parciales/eval_corredor_fijo.csv", "parciales/eval_corredor_trivial.csv", "parciales/eval_corredor_actuado.csv"),
    ("2715", "demanda2/eval_dem_corredor_t2715_ippo_vecinos_s2042.csv", "demanda2/eval_dem_corredor_t2715_fijo.csv",
     "demanda/eval_corredor_f150_fijo.csv", "demanda2/eval_dem_corredor_t2715_trivial.csv",
     "demanda2/eval_dem_corredor_t2715_actuado.csv"),
    ("3620 P2", "parciales/eval_corredor_alta_ippo_vecinos_s2042.csv", "parciales/eval_corredor_alta_fijo_2509.csv",
     "parciales/eval_corredor_alta_fijo.csv", "parciales/eval_corredor_alta_trivial.csv",
     "parciales/eval_corredor_alta_actuado.csv"),
]

for nombre, f_ippo, f_fijo, f_fijo10, f_triv, f_act in NIVELES:
    d = {k: leer(os.path.join(P2, v)) for k, v in
         [("ippo", f_ippo), ("fijo", f_fijo), ("fijo10", f_fijo10), ("triv", f_triv), ("act", f_act)]}
    falt = [k for k, v in d.items() if v is None]
    print(f"\n=== Corredor {nombre} veh/h" + (f"  (faltan: {falt})" if falt else ""))
    for m, etiqueta in [("timeloss_prom", "timeLoss"), ("retraso_total_prom", "retraso total")]:
        partes = []
        for k, et in [("fijo", "fijo 25.09"), ("fijo10", "fijo desde 10 s"), ("triv", "ciclo min"), ("act", "actuado")]:
            if d[k] is not None and d["ippo"] is not None:
                dl, n = delta(d["ippo"], d[k], m)
                partes.append(f"{et} {dl:+.1f}%")
        print(f"  IPPO vs [{etiqueta}]: " + " | ".join(partes))
    for k in ["ippo", "fijo", "fijo10", "triv", "act"]:
        if d[k] is not None:
            print(f"    {k:7s} timeLoss {media(d[k], 'timeloss_prom'):7.2f}  total {media(d[k], 'retraso_total_prom'):7.2f}"
                  f"  espera_entrar {media(d[k], 'retraso_insercion_prom'):6.2f}  cambios_fase {media(d[k], 'cambios_fase'):6.1f}"
                  f"  no_term {media(d[k], 'no_terminados'):5.1f}")
