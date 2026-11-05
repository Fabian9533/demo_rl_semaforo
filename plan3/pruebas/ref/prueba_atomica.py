"""
prueba_atomica.py - Prueba de la tarea 0.11: escritura atomica de comun.archivo_actuado y archivo_trivial.
  3 evaluaciones simultaneas del mismo escenario (evaluar.py --brazo actuado, y despues --brazo trivial; cada una
  regenera el .add.xml al empezar cada semilla mientras los sumo de las otras lo leen) terminan sin error, dan los
  mismos numeros, no dejan temporales y el .add.xml queda igual byte a byte al que escribe el comun.py entregado
  (223f908). En P1 (5 semillas cada una) y en P6 (2 semillas).
Corre en una copia (tmp_ref/atomica/). Semillas de humo. Uso (cwd = plan3/): python pruebas/ref/prueba_atomica.py
Salida: pruebas/ref/salidas/prueba_atomica.txt
"""
import os
import sys
import glob
import types
import shutil
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
inf = up.Informe("prueba_atomica")
CARPETA = up.copia("atomica", ["corredor", "malla3_alta"])


def esperado(esc, brazo):
    """El .add.xml que escribe el comun.py entregado, en una subcarpeta con su propia copia del escenario."""
    import rl_corredor as rc
    viejo = subprocess.run(["git", "show", "223f908:comun.py"], capture_output=True, text=True, cwd=up.RAIZ,
                           encoding="utf-8").stdout
    mod = types.ModuleType("comun_entregado")
    exec(compile(viejo, "comun_entregado", "exec"), mod.__dict__)
    sub = os.path.join(CARPETA, "entregado")
    os.makedirs(sub, exist_ok=True)
    for f in up.archivos_de_cfg(os.path.join(CARPETA, f"{esc}.sumocfg")):
        shutil.copyfile(os.path.join(CARPETA, f), os.path.join(sub, f))
    os.chdir(sub)
    tls = list(rc.ESCENARIOS[esc]["semaforos"])
    if brazo == "actuado":
        mod.archivo_actuado(f"{esc}.sumocfg", esc, tls, rc.VERDE_MIN, rc.VERDE_MIN_GIRO, rc.VERDE_MAX)
    else:
        mod.archivo_trivial(f"{esc}.sumocfg", esc, tls, rc.VERDE_MIN, rc.VERDE_MIN_GIRO)
    os.chdir(CARPETA)
    return os.path.join(sub, f"{esc}_{brazo}.add.xml")


def simultaneas(esc, brazo, semillas):
    destino = f"{esc}_{brazo}.add.xml"
    if os.path.exists(destino):
        os.remove(destino)
    procs = []
    for k in range(3):
        procs.append(subprocess.Popen(
            [sys.executable, os.path.join(up.RAIZ, "evaluar.py"), "--escenario", esc, "--brazo", brazo,
             "--semillas", semillas, "--salida", f"eval_{esc}_{brazo}_{k}.csv", "--extras", f"extras_{brazo}_{k}"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True))
    codigos, textos = [], []
    for p in procs:
        out, _ = p.communicate()
        codigos.append(p.returncode)
        textos.append(out)
    csvs = [open(f"eval_{esc}_{brazo}_{k}.csv", encoding="utf-8").read() if os.path.exists(
        f"eval_{esc}_{brazo}_{k}.csv") else "" for k in range(3)]
    temporales = glob.glob(f"{destino}.*.tmp")
    igual = up.sha256(destino) == up.sha256(esperado(esc, brazo))
    inf.chequeo(codigos == [0, 0, 0] and len(set(csvs)) == 1 and csvs[0] and not temporales and igual,
                f"{esc} {brazo}: 3 evaluaciones simultaneas ({semillas}): codigos {codigos}, CSV iguales "
                f"{len(set(csvs)) == 1}, temporales {temporales}, {destino} igual al del comun.py entregado: {igual}")
    for c, t in zip(codigos, textos):
        if c != 0:
            inf(t[-2000:])


def main():
    inf(f"Prueba de 0.11: escritura atomica (copia en {CARPETA})")
    simultaneas("corredor", "actuado", f"{up.HUMO[0]}-{up.HUMO[4]}")
    simultaneas("corredor", "trivial", f"{up.HUMO[0]}-{up.HUMO[4]}")
    simultaneas("malla3_alta", "actuado", f"{up.HUMO[0]}-{up.HUMO[1]}")
    os.chdir(up.PLAN3)
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
