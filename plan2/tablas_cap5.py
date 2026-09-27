"""tablas_cap5.py - Tablas tab:plan2-resumen y tab:plan2-metas del Cap. V.

Se generan a partir de los resultados congelados (25.09.2026, 03:55).

tab:plan2-resumen: retraso del fijo por caso y, por modelo y caso, retraso de la base publicada,
Delta vs fijo y veredicto abreviado. Fuente: plan2/veredicto_congelado_0355.csv (modelos) y fila
'fijo' (timeloss_prom) de plan2/evaluacion_<esc>_resumen.csv.

tab:plan2-metas: Delta (%) frente al fijo de la base publicada de IPPO vecinos en las cuatro metricas
con meta de la introduccion. Fuente: plan2/evaluacion_<esc>_resumen.csv (delta_pct); base publicada
de plan2/veredicto_congelado_0355.csv (columna base_publicada).

Formato de numeros igual que veredicto.py: retraso con 2 decimales, deltas con '{:+.1f}'.
No recalcula nada: solo lee y formatea.
Uso (desde demo_rl/plan2):  python tablas_cap5.py   (imprime las dos tablas en la salida estandar)
"""
import csv
import os

PLAN2 = os.path.dirname(os.path.abspath(__file__))
CASOS = [("P1", "corredor"), ("P2", "corredor_alta"), ("P3", "red"), ("P4", "red_alta"),
         ("P5", "malla3")]
MODELOS = [("actuado", "Actuado"), ("ql", "Q-learning"), ("sarsa", "SARSA"),
           ("ql_colas", r"\texttt{ql\_colas}"), ("dqn", "DQN"), ("ippo_local", "IPPO local"),
           ("ippo_vecinos", "IPPO vecinos"), ("ippo_spill", "IPPO spill"), ("mappo", "MAPPO")]
ABREV = {"FUNCIONA": "FUN", "MEJORA": "MEJ", "EMPATA": "EMP", "FALLA": "FAL"}


def menos(texto):
    return texto.replace("-", "$-$")


def delta(x):
    s = f"{float(x):+.1f}"
    if s in ("+0.0", "-0.0"):
        s = "0.0"
    return menos(s)


def veredicto_corto(v):
    v = v.strip()
    if v in ABREV:
        return ABREV[v]
    if v.startswith("= vecinos"):
        return "= vecinos"
    if v.startswith("PENDIENTE (no convergi"):
        prov = v.split("provisional:")[1].strip(" )")
        return f"PEN ({ABREV[prov]})"
    if v.startswith("PENDIENTE (sin datos"):
        return "sin datos"
    raise ValueError(v)


def leer_resumen(esc):
    ruta = os.path.join(PLAN2, f"evaluacion_{esc}_resumen.csv")
    with open(ruta, encoding="utf-8") as f:
        return {(r["brazo"], r["metrica"]): r for r in csv.DictReader(f)}


with open(os.path.join(PLAN2, "veredicto_congelado_0355.csv"), encoding="utf-8") as f:
    ver = {(r["caso"], r["modelo"]): r for r in csv.DictReader(f)}
res = {esc: leer_resumen(esc) for _, esc in CASOS}

# ---------------- tab:plan2-resumen ----------------
lin = []
cab = " & ".join(r"\makecell{" + c + r"\\" + e.replace("_", r"\_") + "}" for c, e in CASOS)
lin.append(r"Modelo & " + cab + r" \\")
lin.append(r"\midrule")
fijo = []
for _, esc in CASOS:
    r = res[esc][("fijo", "timeloss_prom")]
    fijo.append(r"\makecell{" + f"{float(r['media']):.2f}" + r"\\" + f"$\\pm$ {float(r['ic95']):.2f}" + "}")
lin.append(r"\makecell[l]{Fijo tuneado\\(s/veh)} & " + " & ".join(fijo) + r" \\")
lin.append(r"\midrule")
for m, nombre in MODELOS:
    celdas = []
    for caso, _ in CASOS:
        r = ver[(caso, m)]
        v = veredicto_corto(r["veredicto"])
        if not r["retraso"]:
            celdas.append(v)
            continue
        if v == "= vecinos":
            celdas.append(v)
            continue
        celdas.append(r"\makecell{" + f"{float(r['retraso']):.2f}" + r"\\" + delta(r["delta_fijo"])
                      + " " + v + "}")
    lin.append(nombre + " & " + " & ".join(celdas) + r" \\")
print("% ---- tab:plan2-resumen ----")
print("\n".join(lin))

# ---------------- tab:plan2-metas ----------------
METAS = [("timeloss_prom", r"Retraso por vehículo", r"$-25$ a $-40$"),
         ("cola_prom", r"Cola promedio", r"$\leq -20$"),
         ("co2_prom", r"Emisiones de CO$_2$", r"$\leq -5$"),
         ("throughput", r"\textit{Throughput}", r"$\geq +10$")]
print("% ---- tab:plan2-metas ----")
bases = []
for caso, esc in CASOS:
    b = ver[(caso, "ippo_vecinos")]["base_publicada"]
    bases.append(b)
print("% bases publicadas de ippo_vecinos: " + ", ".join(f"{c} {b}" for (c, _), b in zip(CASOS, bases)))
for met, nombre, meta in METAS:
    celdas = []
    for (caso, esc), b in zip(CASOS, bases):
        r = res[esc][(f"ippo_vecinos_s{b}", met)]
        celdas.append(delta(r["delta_pct"]))
    print(nombre + " & " + meta + " & " + " & ".join(celdas) + r" \\")

# comprobacion: el retraso de la base publicada coincide con el CSV congelado
print("% ---- comprobaciones ----")
for (caso, esc), b in zip(CASOS, bases):
    r = res[esc][(f"ippo_vecinos_s{b}", "timeloss_prom")]
    v = ver[(caso, "ippo_vecinos")]
    print(f"% {caso}: resumen media={r['media']} delta={r['delta_pct']} | congelado retraso={v['retraso']}"
          f" delta_fijo={v['delta_fijo']}")
    for met in ("cola_prom", "co2_prom", "throughput"):
        r = res[esc][(f"ippo_vecinos_s{b}", met)]
        print(f"%    {met}: delta_pct={r['delta_pct']} ic={r['delta_ic95']} p={r['p_wilcoxon']}"
              f" media={r['media']} fijo={res[esc][('fijo', met)]['media']}")
