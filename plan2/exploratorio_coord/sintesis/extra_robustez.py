"""Chequeos extra para la SINTESIS (solo lee CSV existentes; no simula nada).
1) P4 5001-5030: brazos frente al fijo RE-BARRIDO instalado (10/10, desfases 0/25/24; mejora_coord/salidas/sim/red_alta_fijo.csv).
2) P4, P6, P1: los mismos contrastes en retraso_total_prom (timeLoss + departDelay) y retraso de insercion,
   para ver si la ganancia en timeLoss es cola desplazada fuera de la red.
Estadistica: evaluar.comparar (bootstrap pareado 10 000, Wilcoxon)."""
import os, sys, csv, glob, statistics as st
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
C2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MC = os.path.join(C2, "..", "mejora_coord")
sys.path.insert(0, os.path.join(C2, "code"))
import evaluar

def leer(*rutas, sem=range(5001, 5031)):
    d = {}
    for pat in rutas:
        for r in glob.glob(pat):
            for f in csv.DictReader(open(r)):
                s = int(f["semilla"])
                if s in sem:
                    d[s] = f
    assert not any(1001 <= s <= 1030 for s in d)
    return d

def cmp(nombre, A, R, col="timeloss_prom"):
    ss = sorted(set(A) & set(R)); assert len(ss) == 30, (nombre, len(ss))
    a = [float(A[s][col]) for s in ss]; r = [float(R[s][col]) for s in ss]
    c = evaluar.comparar(a, r)
    gana = sum(x < y for x, y in zip(a, r))
    print(f"  {nombre:44s} {col:22s} {st.mean(a):8.3f} vs {st.mean(r):8.3f}  {c['delta_pct']:+5.1f} % {c['delta_ic95']:>14s} p={c['p_wilcoxon']:>9s}  gana {gana}/30")

sim = os.path.join(MC, "salidas", "sim")
P4 = {
  "V5_s42": leer(os.path.join(C2, "V5", "salidas", "eval_red_alta_s42_*.csv")),
  "V2_s2042": leer(os.path.join(C2, "V2", "salidas", "eval_red_alta_s2042_*.csv")),
  "C0_s4042": leer(os.path.join(C2, "tanda1", "c0", "salidas", "eval_red_alta_s4042_*.csv")),
  "trivial": leer(os.path.join(sim, "red_alta_trivial.csv")),
  "ippo_vecinos_s42": leer(os.path.join(sim, "red_alta_ippo_vecinos_s42.csv")),
  "fijo2509": leer(os.path.join(sim, "red_alta_fijo2509.csv")),
  "fijo_rebarrido": leer(os.path.join(sim, "red_alta_fijo.csv")),
}
print("== P4 red_alta, 5001-5030, frente al fijo RE-BARRIDO instalado (10/10, desfases 0/25/24)")
for b in ("V5_s42", "V2_s2042", "trivial", "C0_s4042", "ippo_vecinos_s42", "fijo2509"):
    cmp(f"{b} vs fijo_rebarrido", P4[b], P4["fijo_rebarrido"])
print("== P4 red_alta, 5001-5030, retraso total (timeLoss + insercion) frente a fijo2509")
for b in ("V5_s42", "V2_s2042", "trivial", "C0_s4042", "fijo_rebarrido"):
    cmp(f"{b} vs fijo2509", P4[b], P4["fijo2509"], "retraso_total_prom")
for b in ("V5_s42", "trivial", "fijo2509", "fijo_rebarrido", "C0_s4042"):
    ins = st.mean(float(P4[b][s]["retraso_insercion_prom"]) for s in P4[b])
    ni = sum(int(float(P4[b][s]["no_insertados"])) for s in P4[b])
    print(f"  {b:18s} retraso_insercion medio {ins:7.3f} s  no_insertados total {ni}")

T2 = os.path.join(C2, "tanda2")
P6 = {
  "V5_s42": leer(os.path.join(T2, "p6", "salidas", "eval_malla3_alta_V5_s42_p*.csv")),
  "V2_s4042": leer(os.path.join(T2, "p6", "salidas", "eval_malla3_alta_V2_s4042_p*.csv")),
  "C0_s4042": leer(os.path.join(T2, "p6", "salidas", "eval_malla3_alta_C0_s4042_p*.csv")),
  "ippo_vecinos_s42": leer(os.path.join(sim, "malla3_alta_ippo_vecinos_s42.csv")),
  "fijo2509": leer(os.path.join(sim, "malla3_alta_fijo2509.csv")),
}
print("== P6 malla3_alta, 5001-5030, retraso total frente a fijo2509 (15/10) y a IPPO publicado")
for b in ("V5_s42", "V2_s4042", "C0_s4042", "ippo_vecinos_s42"):
    cmp(f"{b} vs fijo2509", P6[b], P6["fijo2509"], "retraso_total_prom")
for b in ("V5_s42", "V2_s4042"):
    cmp(f"{b} vs ippo_vecinos_s42", P6[b], P6["ippo_vecinos_s42"], "retraso_total_prom")
for b in P6:
    ins = st.mean(float(P6[b][s]["retraso_insercion_prom"]) for s in P6[b])
    ni = sum(int(float(P6[b][s]["no_insertados"])) for s in P6[b])
    nt = sum(int(float(P6[b][s]["no_terminados"])) for s in P6[b])
    cm = st.mean(float(P6[b][s]["cola_max_enlace"]) for s in P6[b])
    print(f"  {b:18s} retraso_insercion medio {ins:7.3f} s  no_insertados total {ni}  no_terminados total {nt}  cola_max_enlace media {cm:.1f}")

P1d = os.path.join(T2, "p1", "salidas")
P1 = {
  "V5_s4042": leer(os.path.join(P1d, "eval_corredor_V5_s4042.csv")),
  "ippo_vecinos_s4042": leer(os.path.join(P1d, "corredor_ippo_vecinos_s4042.csv")),
  "fijo2509": leer(os.path.join(P1d, "corredor_fijo2509.csv")),
  "actuado": leer(os.path.join(P1d, "corredor_actuado.csv")),
}
print("== P1 corredor, 5001-5030, retraso total")
for b in ("V5_s4042", "ippo_vecinos_s4042", "actuado"):
    cmp(f"{b} vs fijo2509", P1[b], P1["fijo2509"], "retraso_total_prom")
cmp("V5_s4042 vs ippo_vecinos_s4042", P1["V5_s4042"], P1["ippo_vecinos_s4042"], "retraso_total_prom")
