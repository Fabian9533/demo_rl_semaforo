"""Re-calcula desde los CSV por semilla de esta carpeta las cifras de HECHOS.md (analisis exploratorio
coord2, 28.09.2026; fuera del veredicto pre-registrado del 25.09). Usa evaluar.comparar del repo
(delta % de medias, IC95 bootstrap pareado 10 000 remuestreos, Wilcoxon pareado).
Uso, desde demo_rl/:  python plan2/exploratorio_coord/verificar_hechos.py > plan2/exploratorio_coord/verificar_hechos.txt"""
import os, sys, csv, glob, statistics as st
AQ = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(AQ))
sys.path.insert(0, REPO)
import evaluar as E

S5 = list(range(5001, 5031)); S6 = list(range(6001, 6031)); S6b = list(range(6011, 6031))


def leer(*pats):
    d = {}
    for pat in pats:
        fs = sorted(glob.glob(os.path.join(AQ, pat)))
        assert fs, pat
        for f in fs:
            for r in csv.DictReader(open(f)):
                s = int(r["semilla"]); assert not 1001 <= s <= 1030
                d[s] = r
    return d


def ser(d, sem, col="timeloss_prom"):
    return [float(d[s][col]) for s in sem]


def cmp(etq, a, b, sem, col="timeloss_prom"):
    x, y = ser(a, sem, col), ser(b, sem, col)
    c = E.comparar(x, y)
    gana = sum(1 for u, v in zip(x, y) if u < v)
    igual = sum(1 for u, v in zip(x, y) if u == v)
    print(f"  {etq:44s} {col:18s} {st.mean(x):8.3f} vs {st.mean(y):8.3f}  {c['delta_pct']:+.1f} % {c['delta_ic95']}"
          f" p={c['p_wilcoxon']}  gana {gana}/{len(sem)}  iguales {igual}")


# ---- P4 red_alta ----
P4 = {"V2_s2042": leer("csv/p4_5001_5030/eval_red_alta_V2_s2042_*.csv"),
      "V5_s42": leer("csv/p4_5001_5030/eval_red_alta_V5_s42_*.csv")}
for x in ("trivial", "ippo_vecinos_s42", "fijo2509", "actuado"):
    P4[x] = leer(f"csv/p4_5001_5030/red_alta_{x}.csv")
P4["fijo_rebarrido"] = leer("csv/p4_5001_5030/red_alta_fijo.csv")
print("== P4 red_alta, cribado 5001-5030 (timeLoss)")
for x in ("fijo2509", "actuado", "trivial", "ippo_vecinos_s42", "fijo_rebarrido", "V2_s2042", "V5_s42"):
    print(f"  media {x:18s} {st.mean(ser(P4[x], S5)):.3f}")
for b in ("V2_s2042", "V5_s42"):
    cmp(f"{b} vs fijo2509", P4[b], P4["fijo2509"], S5)
    cmp(f"{b} vs trivial", P4[b], P4["trivial"], S5)
    cmp(f"{b} vs ippo_vecinos_s42", P4[b], P4["ippo_vecinos_s42"], S5)
    cmp(f"{b} vs fijo_rebarrido", P4[b], P4["fijo_rebarrido"], S5)
    it = sum(1 for s in S5 if P4[b][s]["timeloss_prom"] == P4["trivial"][s]["timeloss_prom"]
             and P4[b][s]["cambios_fase"] == P4["trivial"][s]["cambios_fase"])
    print(f"  {b} igual al trivial (timeLoss y cambios_fase): {it}/30")

P4c = {x: leer(f"csv/p4_6001_6030/red_alta_{x}_p*.csv") for x in
       ("V5_s42", "C0_s4042", "ippo_vecinos_s42", "fijo2509", "actuado", "trivial")}
for sem, et in ((S6, "6001-6030"), (S6b, "6011-6030")):
    print(f"== P4 red_alta, confirmacion {et} (timeLoss)")
    for x in P4c:
        print(f"  media {x:18s} {st.mean(ser(P4c[x], sem)):.3f}")
    for r in ("fijo2509", "trivial", "ippo_vecinos_s42", "C0_s4042"):
        cmp(f"V5_s42 vs {r}", P4c["V5_s42"], P4c[r], sem)

# ---- P6 malla3_alta ----
BR6 = ["V2_s42", "V2_s2042", "V2_s4042", "V5_s42", "V5_s2042", "V5_s4042", "ippo_vecinos_s42", "fijo", "actuado", "trivial"]
P6 = {b: leer(f"conf_p6/salidas/malla3_alta_{b}_p*.csv") for b in BR6}
P6_5 = {b: leer(f"csv/p6_5001_5030/eval_malla3_alta_{b}_p*.csv") for b in BR6[:6]}
P6_5["C0_s4042"] = leer("csv/p6_5001_5030/eval_malla3_alta_C0_s4042_p*.csv")
P6_5["fijo"] = leer("csv/p6_5001_5030/malla3_alta_fijo2509.csv")
for x in ("ippo_vecinos_s42", "actuado", "trivial"):
    P6_5[x] = leer(f"csv/p6_5001_5030/malla3_alta_{x}.csv")
P60 = {b: {**P6_5[b], **{s: P6[b][s] for s in S6}} for b in BR6}
S60 = S5 + S6
sin28 = [s for s in S6 if s != 6028]
print("== P6 malla3_alta (timeLoss; fijo = 15/10 de fijo_2509)")
print("  fijo 15/10, 5 mayores timeLoss en 6001-6030:",
      sorted(((s, float(P6["fijo"][s]["timeloss_prom"])) for s in S6), key=lambda z: -z[1])[:3])
for D, sem, et in ((P6_5, S5, "5001-5030"), (P6, S6, "6001-6030"), (P6, S6b, "6011-6030"),
                   (P6, sin28, "6001-6030 sin 6028"), (P60, S60, "60 semillas")):
    print(f"-- {et}")
    for b in ("V2_s4042", "V5_s42"):
        cmp(f"{b} vs fijo 15/10", D[b], D["fijo"], sem)
        cmp(f"{b} vs ippo_vecinos_s42", D[b], D["ippo_vecinos_s42"], sem)
        cmp(f"{b} vs fijo 15/10", D[b], D["fijo"], sem, "retraso_total_prom")
    cmp("ippo_vecinos_s42 vs fijo 15/10", D["ippo_vecinos_s42"], D["fijo"], sem)
    if et == "5001-5030":
        cmp("V2_s4042 vs C0_s4042", D["V2_s4042"], D["C0_s4042"], sem)
        cmp("C0_s4042 vs ippo_vecinos_s42", D["C0_s4042"], D["ippo_vecinos_s42"], sem)
    ri = {b: round(st.mean(ser(D[b], sem, "retraso_insercion_prom")), 2) for b in BR6 if b != "trivial"}
    print(f"  retraso de insercion medio (s/veh), todos salvo trivial: min {min(ri.values())} max {max(ri.values())}")

# ---- P1 corredor ----
P1 = {"V5_s4042": leer("csv/p1_5001_5030/eval_corredor_V5_s4042.csv"),
      "ippo_vecinos_s4042": leer("csv/p1_5001_5030/corredor_ippo_vecinos_s4042.csv"),
      "fijo2509": leer("csv/p1_5001_5030/corredor_fijo2509.csv")}
print("== P1 corredor, 5001-5030 (timeLoss)")
cmp("V5_s4042 vs ippo_vecinos_s4042", P1["V5_s4042"], P1["ippo_vecinos_s4042"], S5)
cmp("V5_s4042 vs fijo2509", P1["V5_s4042"], P1["fijo2509"], S5)
cmp("ippo_vecinos_s4042 vs fijo2509", P1["ippo_vecinos_s4042"], P1["fijo2509"], S5)
