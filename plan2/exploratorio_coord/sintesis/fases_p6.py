"""Diagnostico descriptivo: corre UNA politica en malla3_alta, semilla de validacion (999 u otra fuera de
1001-1030), y deja fases_<esc>_<brazo>_s<semilla>.csv (fase por segundo y semaforo) en coord2/sintesis/run/<tag>.
Uso: python fases_p6.py POLITICA.pt CODE_DIR TAG SEMILLA"""
import os, sys, shutil, json
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
pt, code, tag, sem = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), sys.argv[3], int(sys.argv[4])
assert not 1001 <= sem <= 1030
sys.path.insert(0, code)
import torch; torch.set_num_threads(1)
AQUI = os.path.dirname(os.path.abspath(__file__))
plan2 = os.path.join(AQUI, "..", "V2", "plan2")
run = os.path.join(AQUI, "run", tag); os.makedirs(run, exist_ok=True)
for f in os.listdir(plan2):
    if f.startswith(("malla3", "red")) and f.endswith((".xml", ".sumocfg")):
        shutil.copy(os.path.join(plan2, f), run)
os.chdir(run)
import comun, evaluar
brazo, _, _, correr = evaluar.brazo_profundo("malla3_alta", pt, 0, 0.0)
res = correr(sem, f"trip_{tag}.xml", f"serie_malla3_alta_{tag}_s{sem}.csv")
print(tag, brazo, sem, res["timeloss_prom"], res["cambios_fase"], sorted(os.listdir(".")))
