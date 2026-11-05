"""
prueba_c0_paralelo.py - Dos grupos de checkpoints de una misma corrida validados a la vez dan lo mismo que en serie
(revision del 05.11: con un tripinfo comun el XML se corrompia).

Uso (desde plan3/):  python pruebas/infra/prueba_c0_paralelo.py   -> pruebas/infra/prueba_c0_paralelo.txt
P1, IPPO entregado base 42, checkpoints 10-20 y 30-40, validacion en 2 semillas de humo.
"""
import os
import sys
import json
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN3 = os.path.dirname(os.path.dirname(AQUI))
TMP = os.path.join(PLAN3, "tmp_c0b")


def correr(eps, salida, esperar=True):
    cmd = [sys.executable, "revalidar_c0.py", "validar", "--escenario", "corredor", "--origen",
           "insumos/c0_checkpoints", "--corrida", "corredor_ippo_vecinos_s42", "--eps", eps,
           "--val-seeds", "999,424301", "--salida", salida]
    entorno = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    p = subprocess.Popen(cmd, cwd=PLAN3, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=entorno)
    return p.communicate()[0] if esperar else p


def main():
    os.makedirs(TMP, exist_ok=True)
    for f in os.listdir(TMP):
        os.remove(os.path.join(TMP, f))
    a = correr("10,20", "tmp_c0b/serie_g1.json")
    b = correr("30,40", "tmp_c0b/serie_g2.json")
    p1 = correr("10,20", "tmp_c0b/par_g1.json", esperar=False)
    p2 = correr("30,40", "tmp_c0b/par_g2.json", esperar=False)
    s1, s2 = p1.communicate()[0], p2.communicate()[0]
    lineas, malos = [], 0
    ok_codigos = p1.returncode == 0 and p2.returncode == 0
    lineas.append(f"{'ok ' if ok_codigos else 'MAL'} los dos grupos a la vez terminan con codigo 0")
    malos += not ok_codigos
    for g in ("g1", "g2"):
        serie = json.load(open(os.path.join(TMP, f"serie_{g}.json"), encoding="utf-8"))["checkpoints"]
        par = json.load(open(os.path.join(TMP, f"par_{g}.json"), encoding="utf-8"))["checkpoints"]
        quitar = lambda cs: [{k: v for k, v in c.items() if k != "segundos"} for c in cs]
        igual = quitar(serie) == quitar(par)
        malos += not igual
        lineas.append(f"{'ok ' if igual else 'MAL'} {g}: a la vez = en serie")
    sobras = [d for d in os.listdir(PLAN3) if d.startswith("tmp_c0_")]
    lineas.append(f"{'ok ' if not sobras else 'MAL'} no quedan carpetas temporales: {sobras}")
    malos += bool(sobras)
    texto = "\n".join(lineas)
    print(texto)
    if malos:
        print(a, b, s1, s2)
    open(os.path.join(AQUI, "prueba_c0_paralelo.txt"), "w", encoding="utf-8").write(texto + "\n")
    sys.exit(1 if malos else 0)


if __name__ == "__main__":
    main()
