"""
prueba_atomica.py - Prueba de la tarea 0.11: escritura atomica de comun.archivo_actuado y archivo_trivial.
  3 evaluaciones simultaneas del mismo escenario (evaluar.py --brazo actuado, y despues --brazo trivial; cada una
  regenera el .add.xml al empezar cada semilla mientras los sumo de las otras lo leen) terminan sin error, dan los
  mismos numeros, no dejan temporales y el .add.xml queda igual byte a byte al que escribe el comun.py entregado
  (223f908). En P1 (5 semillas cada una) y en P6 (2 semillas).
  Y sin sumo: si el reemplazo no llega a hacerse (Windows niega el acceso en todos los intentos), escribir_atomico
  borra su temporal y el destino queda como estaba (comun y barrer_fino); comun.leer_cfg quita los espacios de las
  rutas ('a.add.xml, b.add.xml') y con todos los .sumocfg del repositorio da la misma lista que antes.
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


def sin_reemplazo():
    """os.replace niega el acceso siempre: escribir_atomico agota sus reintentos, borra su temporal y el destino
    queda igual (comun.escribir_atomico y barrer_fino.escribir_atomico)."""
    import comun
    import barrer_fino as bfn
    destino = os.path.join(CARPETA, "destino_atomico.txt")
    with open(destino, "w", encoding="utf-8") as f:
        f.write("original")
    real = os.replace

    def niega(a, b):
        raise PermissionError(13, "acceso denegado (prueba)")
    resultados = []
    for nombre, escribir in (("comun.escribir_atomico", lambda: comun.escribir_atomico(destino, "nuevo", 2, 0.01)),
                             ("barrer_fino.escribir_atomico", lambda: bfn.escribir_atomico(destino, "nuevo"))):
        os.replace = niega
        try:
            escribir()
            fallo = False
        except PermissionError:
            fallo = True
        finally:
            os.replace = real
        temporales = glob.glob(destino + ".*.tmp")
        igual = open(destino, encoding="utf-8").read() == "original"
        resultados.append((nombre, fallo, temporales, igual))
    inf.chequeo(all(f and not tm and ig for _, f, tm, ig in resultados),
                f"sin reemplazo: (funcion, levanta PermissionError, temporales que quedan, destino intacto) "
                f"{resultados}")


def leer_cfg_con_espacios():
    import comun
    import xml.etree.ElementTree as ET
    cfg = os.path.join(CARPETA, "con_espacios.sumocfg")
    with open(cfg, "w", encoding="utf-8") as f:
        f.write('<configuration><input><net-file value="corredor.net.xml"/>'
                '<additional-files value="det.add.xml, corredor.add.xml"/></input></configuration>')
    _, adic = comun.leer_cfg(cfg)
    cambian = []
    todos = sorted(glob.glob(os.path.join(up.RAIZ, "*.sumocfg")) + glob.glob(os.path.join(up.PLAN3, "*.sumocfg")))
    for c in todos:
        nodo = ET.parse(c).getroot().find("input/additional-files")
        antes = nodo.get("value").split(",") if nodo is not None else []
        if comun.leer_cfg(c)[1] != antes:
            cambian.append(os.path.basename(c))
    inf.chequeo(adic == ["det.add.xml", "corredor.add.xml"] and not cambian,
                f"leer_cfg: 'det.add.xml, corredor.add.xml' -> {adic}; con los {len(todos)} .sumocfg de la raiz y de "
                f"plan3 la lista es la de antes (distintas: {cambian})")


def main():
    inf(f"Prueba de 0.11: escritura atomica (copia en {CARPETA})")
    sin_reemplazo()
    leer_cfg_con_espacios()
    simultaneas("corredor", "actuado", f"{up.HUMO[0]}-{up.HUMO[4]}")
    simultaneas("corredor", "trivial", f"{up.HUMO[0]}-{up.HUMO[4]}")
    simultaneas("malla3_alta", "actuado", f"{up.HUMO[0]}-{up.HUMO[1]}")
    os.chdir(up.PLAN3)
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
