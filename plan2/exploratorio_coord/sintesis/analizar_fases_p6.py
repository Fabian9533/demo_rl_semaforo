"""Duraciones de verde, ciclo y sincronia en malla3_alta, semilla 999 (fase 0 = verde E-O, 2 = verde N-S).
Fuentes: sintesis/run/<tag>/fases_*.csv (fases_p6.py) y mejora_coord/datos/fases_malla3_alta_{fijo2509,trivial}.csv."""
import os, csv, glob, statistics as st, collections
A = os.path.dirname(os.path.abspath(__file__))
F = {"fijo2509 (15/10)": os.path.join(A, "..", "..", "mejora_coord", "datos", "fases_malla3_alta_fijo2509.csv"),
     "trivial": os.path.join(A, "..", "..", "mejora_coord", "datos", "fases_malla3_alta_trivial.csv")}
for t in ("ippo_s42", "V2_s4042", "V5_s42"):
    F[t] = glob.glob(os.path.join(A, "run", t, "fases_*.csv"))[0]
def corr(s, f):
    out, ini = [], None
    for t, v in enumerate(s):
        if v == f and ini is None: ini = t
        if v != f and ini is not None: out.append((ini, t - ini)); ini = None
    return out
def pares():
    p = []
    for i in (1, 2, 3):
        for j in (1, 2):
            p.append((f"semaforo_C{i}{j}", f"semaforo_C{i}{j+1}")); p.append((f"semaforo_C{j}{i}", f"semaforo_C{j+1}{i}"))
    return p
print(f"{'brazo':18s} {'vEO med [p10-p90]':>18s} {'vNS med [p10-p90]':>18s} {'%vEO=10':>7s} {'%vNS=10':>7s} {'ciclo med':>9s} {'sd vEO entre cruces':>19s} {'sinc%':>6s} {'fases/h':>7s}")
for b, ruta in F.items():
    r = list(csv.reader(open(ruta))); cab = r[0][1:]
    S = {c: [int(f[i + 1]) for f in r[1:]][:3600] for i, c in enumerate(cab)}
    veo, vns, cic, porc = [], [], [], []
    for c in cab:
        e = [(i, d) for i, d in corr(S[c], 0) if 0 < i and i + d < 3600]
        n = [(i, d) for i, d in corr(S[c], 2) if 0 < i and i + d < 3600]
        veo += [d for _, d in e]; vns += [d for _, d in n]
        ini = [i for i, _ in e]; cic += [b2 - a for a, b2 in zip(ini, ini[1:])]
        porc.append(st.mean(d for _, d in e) if e else float("nan"))
    q = lambda x: st.quantiles(x, n=10)
    sinc = st.mean(sum(1 for t in range(3600) if S[u][t] == S[d][t]) / 3600 for u, d in pares())
    print(f"{b:18s} {st.median(veo):5.0f} [{q(veo)[0]:4.0f}-{q(veo)[-1]:4.0f}]   {st.median(vns):5.0f} [{q(vns)[0]:4.0f}-{q(vns)[-1]:4.0f}]  "
          f"{100*sum(d==10 for d in veo)/len(veo):6.0f}  {100*sum(d==10 for d in vns)/len(vns):6.0f}  {st.median(cic):8.0f}  "
          f"{st.pstdev(porc):18.1f}  {100*sinc:5.1f}  {(len(veo)+len(vns))/len(cab):7.0f}")
    hist = collections.Counter(veo)
    print(f"{'':18s} verdes E-O mas frecuentes: {hist.most_common(6)}")
