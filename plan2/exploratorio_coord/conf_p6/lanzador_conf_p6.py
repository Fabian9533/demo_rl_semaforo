"""Confirmacion de P6 (malla3_alta) en semillas NUEVAS 6001-6030 (exploratorio, fuera del veredicto del 25.09).
Brazos: V2 (smdp_crn) bases 42/2042/4042, V5 (norm_smdp_crn_triv) bases 42/2042/4042 (politicas ya entrenadas,
sin re-entrenar), IPPO vecinos publicado s42 (politica del repo, solo lectura), fijo 15/10 instalado
(plan2/malla3_alta.add.xml, identico md5 a mejora_coord/plan2/malla3_alta.add.xml), actuado y trivial.
Mismo camino que la tanda 2: V3/evaluar_v3.py (brazo_profundo) y tanda2/sim_ref.py (brazo_referencia).
Cada brazo corre ademas la semilla 5001 como control de determinismo frente a tanda2 / mejora_coord.
A lo sumo MAX_PROC procesos; torch 1 hilo; PYTHONDONTWRITEBYTECODE=1. Nunca escribe en el repo.
Salida por semilla: conf_p6/salidas/malla3_alta_<brazo>_p<i>.csv; tiempos en conf_p6/salidas/tiempos.csv."""
import os, sys, time, csv, subprocess, datetime
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
AQ = os.path.dirname(os.path.abspath(__file__))
C2 = os.path.dirname(AQ)
MC = os.path.join(os.path.dirname(C2), "mejora_coord")
REPO = r"C:\Users\GAMER\Documents\demo_rl_semaforo\demo_rl"
PY = sys.executable
MAX_PROC = 15
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
EVAL = os.path.join(C2, "V3", "evaluar_v3.py")
SIMREF = os.path.join(C2, "tanda2", "sim_ref.py")
PARTES = ["5001,6001-6010", "6011-6020", "6021-6030"]
for p in PARTES:
    for t in p.split(","):
        a, b = (t.split("-") + [t])[:2]
        assert not (int(a) <= 1030 and int(b) >= 1001), "semillas de examen prohibidas"
SAL = os.path.join(AQ, "salidas"); LOGS = os.path.join(AQ, "logs"); RUN = os.path.join(AQ, "run")
for d in (SAL, LOGS, RUN):
    os.makedirs(d, exist_ok=True)

JOBS = []
POL = {}
for br, var in (("V2", "smdp_crn"), ("V5", "norm_smdp_crn_triv")):
    for b in (42, 2042, 4042):
        POL[f"{br}_s{b}"] = (os.path.join(C2, br, "plan2", f"politica_malla3_alta_{var}_s{b}.pt"),
                             os.path.join(C2, br, "code"), os.path.join(C2, br, "plan2"))
POL["ippo_vecinos_s42"] = (os.path.join(REPO, "plan2", "politica_malla3_alta_vecinos_s42.pt"),
                           os.path.join(C2, "code"), os.path.join(MC, "plan2"))
# referencias primero (el trivial es el mas lento)
for ref in ("trivial", "fijo", "actuado"):
    for i, sem in enumerate(PARTES):
        JOBS.append((f"{ref}_p{i+1}", [PY, SIMREF, "malla3_alta", ref, sem, os.path.join(SAL, f"malla3_alta_{ref}_p{i+1}.csv"),
                                       "--plan2", os.path.join(MC, "plan2"), "--run", os.path.join(RUN, "ref")]))
for nom, (pt, code, plan2) in POL.items():
    assert os.path.exists(pt), pt
    for i, sem in enumerate(PARTES):
        JOBS.append((f"{nom}_p{i+1}", [PY, EVAL, pt, "malla3_alta", sem, os.path.join(SAL, f"malla3_alta_{nom}_p{i+1}.csv"),
                                       "--code", code, "--plan2", plan2, "--run", os.path.join(RUN, nom)]))


def ahora():
    return datetime.datetime.now().strftime("%H:%M:%S")


pend = list(JOBS); corr = {}; hecho = []
t0 = time.time()
while pend or corr:
    for jid, (p, fh, ti) in list(corr.items()):
        rc = p.poll()
        if rc is None:
            continue
        fh.close(); del corr[jid]
        hecho.append((jid, rc, ti, time.time()))
        print(f"[{ahora()}] termina {jid} rc={rc} en {time.time()-ti:.0f} s", flush=True)
    while pend and len(corr) < MAX_PROC:
        jid, cmd = pend.pop(0)
        fh = open(os.path.join(LOGS, jid + ".log"), "w", encoding="utf-8")
        fh.write(" ".join(cmd) + "\n"); fh.flush()
        corr[jid] = (subprocess.Popen(cmd, cwd=AQ, env=ENV, stdout=fh, stderr=subprocess.STDOUT), fh, time.time())
        print(f"[{ahora()}] lanza {jid}", flush=True)
    time.sleep(3)
with open(os.path.join(SAL, "tiempos.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["job", "rc", "segundos"])
    for jid, rc, ti, tf in hecho:
        w.writerow([jid, rc, round(tf - ti, 1)])
malos = [j for j, rc, _, _ in hecho if rc != 0]
print(f"FIN en {(time.time()-t0)/60:.1f} min; fallidos: {malos}", flush=True)
open(os.path.join(AQ, "FIN"), "w").write(f"{datetime.datetime.now()} {time.time()-t0:.0f} s fallidos {malos}\n")
