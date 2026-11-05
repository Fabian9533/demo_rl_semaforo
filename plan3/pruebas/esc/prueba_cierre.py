"""
prueba_cierre.py - Chequeos al terminar todas las pruebas de los escenarios nuevos (correr al final):
  - el sha256 de cada .rou.xml de plan2/ es el que guardo prueba_archivos.py al empezar (prueba 4);
  - git status --porcelain --ignored -- plan2 TESIS y git diff 223f908 -- plan2 TESIS estan vacios (nada escribio
    ahi, ni siquiera archivos ignorados);
  - preparar3 --revisar: los escenarios de plan3/ son los que escribe preparar3;
  - no quedan en plan3/ restos de las pruebas (actuado y ciclo minimo de los escenarios nuevos, barrido_*.csv,
    politicas y resultados de humo p3humo, tmp_esc_*).
Uso (desde plan3/): python pruebas/esc/prueba_cierre.py      Salida: salidas/cierre.txt
"""
import os
import sys
import glob
import json
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_esc as u                       # noqa: E402

BASE = "223f908"           # commit de plan3-dev del que nace la rama plan3-esc


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=u.RAIZ, capture_output=True, text=True).stdout


def main():
    os.chdir(u.PLAN3)
    p = u.Salida("cierre.txt")
    fallas = []

    def ok(cond, texto):
        p(("  ok    " if cond else "  FALLA ") + texto)
        if not cond:
            fallas.append(texto)

    antes = json.load(open(os.path.join(u.SALIDAS, "sha_plan2_rou.txt"), encoding="utf-8"))
    ahora = u.sha_plan2_rou()
    ok(antes == ahora, f"sha256 de los {len(ahora)} .rou.xml de plan2/ iguales a los del comienzo")
    estado = git("status", "--porcelain", "--ignored", "--", "plan2", "TESIS")
    ok(estado.strip() == "",
       f"git status --porcelain --ignored -- plan2 TESIS vacio{': ' + estado[:200] if estado else ''}")
    dif = git("diff", BASE, "--", "plan2", "TESIS")
    ok(dif.strip() == "", f"git diff {BASE} -- plan2 TESIS vacio")
    r = subprocess.run([sys.executable, "demanda_estocastica.py", "preparar3", "--revisar"], capture_output=True,
                       text=True)
    ok(r.returncode == 0, f"preparar3 --revisar: {r.stdout.strip()}")
    restos = [n for n in u.escenarios() for s in ("_actuado.add.xml", "_trivial.add.xml") if os.path.exists(n + s)]
    restos += glob.glob("barrido_*.csv") + glob.glob("*p3humo*") + glob.glob("tmp_esc_*") + glob.glob("eco_*.py")
    ok(not restos, f"sin restos de las pruebas en plan3/{': ' + ', '.join(restos) if restos else ''}")
    p(f"\nResultado: {'TODO OK' if not fallas else f'{len(fallas)} FALLAS'}")
    p.guardar()
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
