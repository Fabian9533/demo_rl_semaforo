"""
correr_todas.py - Corre en orden las pruebas de los escenarios nuevos del plan 3 y resume el resultado:
prueba_archivos (1 y parte de la 4), prueba_conteos (2), prueba_crn (3 y 4), prueba_lanzador (6),
prueba_cargas (7 y 5) y prueba_cierre (4 y reglas de plan2/TESIS). Cada una escribe su resumen en salidas/.
Uso (desde plan3/): python pruebas/esc/correr_todas.py      (~35 min; como mucho 3 sumo a la vez)
"""
import os
import sys
import time
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
PRUEBAS = ["prueba_archivos", "prueba_conteos", "prueba_crn", "prueba_lanzador", "prueba_cargas", "prueba_cierre"]


def main():
    plan3 = os.path.dirname(os.path.dirname(AQUI))
    resumen = []
    for nombre in PRUEBAS:
        t0 = time.time()
        r = subprocess.run([sys.executable, os.path.join(AQUI, f"{nombre}.py")], cwd=plan3,
                           capture_output=True, text=True)
        ultima = [l for l in r.stdout.strip().splitlines() if l.startswith("Resultado")]
        resumen.append(f"{nombre:16s} codigo {r.returncode}  {ultima[-1] if ultima else r.stderr[-300:]}  "
                       f"({(time.time() - t0) / 60:.1f} min)")
        print(resumen[-1], flush=True)
    sys.exit(0 if all(" codigo 0 " in l for l in resumen) else 1)


if __name__ == "__main__":
    main()
