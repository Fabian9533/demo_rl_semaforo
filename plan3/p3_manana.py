"""
p3_manana.py - La manana del protocolo a ciegas sin detener la cola (la PC corre de corrido, 07.11.2026).

Uso (desde <worktree de ejecucion>/plan3, con la cola corriendo):  python p3_manana.py
  1. protecciones.py antes (git, prerregistro igual al de origin, insumos, checkpoints, versiones);
  2. cola/manifiesto_ciego.json: ruta, sha256, filas y semillas de cada CSV de ciego/ (sin metricas);
  3. respaldo de plan3/checkpoints y de plan3/ciego fuera del repositorio, y cola/manifiesto_checkpoints.json;
  4. cola/resumen_<fecha>.txt: lo que se lanzo desde la manana anterior (sin metricas).
Despues, a mano: commit de cola/manifiesto_ciego.json, cola/manifiesto_checkpoints.json y el resumen (nunca ciego/
ni el sello), push, `python chequeos_previos.py --solo-datos` y borrar cola/pausa: la cola deja de lanzar mientras
HEAD no es el aprobado y retoma sola al borrar la pausa. Los trabajos que estan corriendo no se tocan.
"""
import os
import sys
import time
import subprocess

import p3_noche as pn

ULTIMA = os.path.join(pn.COLA, "ultima_manana.txt")


def main():
    r = subprocess.run([sys.executable, "protecciones.py", "antes"], cwd=pn.PLAN3)
    if r.returncode != 0:
        sys.exit("p3_manana: las protecciones encontraron problemas")
    print(f"manifiesto ciego: {pn.manifiesto_ciego()} archivos", flush=True)
    total, copiados = pn.respaldar_checkpoints()
    print(f"checkpoints: {total} registrados, {copiados} copiados al respaldo", flush=True)
    print(f"ciego: {pn.respaldar_ciego()} archivos copiados al respaldo", flush=True)
    desde = float(open(ULTIMA).read().strip()) if os.path.exists(ULTIMA) else time.time() - 24 * 3600
    texto = pn.resumen(desde)
    with open(os.path.join(pn.COLA, f"resumen_{time.strftime('%Y%m%d_%H%M')}.txt"), "w", encoding="utf-8") as f:
        f.write(texto + "\n")
    with open(ULTIMA, "w") as f:
        f.write(str(time.time()))
    print(texto, flush=True)


if __name__ == "__main__":
    main()
