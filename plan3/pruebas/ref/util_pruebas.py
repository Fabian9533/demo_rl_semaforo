"""
util_pruebas.py - Utilidades de las pruebas de las referencias (plan3, tareas 0.7-0.12). Las pruebas corren con
cwd = plan3/ y escriben solo en plan3/tmp_ref/ (ignorada por git) y en plan3/pruebas/ref/salidas/.
"""
import os
import sys
import hashlib
import subprocess
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN3 = os.path.dirname(os.path.dirname(AQUI))
RAIZ = os.path.dirname(PLAN3)
for _ruta in (PLAN3, RAIZ):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)
SALIDAS = os.path.join(AQUI, "salidas")
TMP = os.path.join(PLAN3, "tmp_ref")
HUMO = list(range(424301, 424361))         # semillas de humo (prerregistro 3)


def preparar():
    """cwd = plan3/ y las carpetas de salida."""
    os.chdir(PLAN3)
    os.makedirs(SALIDAS, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)


def archivos_de_cfg(cfg):
    """El .sumocfg y los archivos que nombra (net, rutas, adicionales), relativos a su carpeta."""
    raiz = ET.parse(cfg).getroot()
    salida = [os.path.basename(cfg)]
    for etiqueta in ("net-file", "route-files", "additional-files"):
        for nodo in raiz.iter(etiqueta):
            salida += [v.strip() for v in nodo.get("value", "").split(",") if v.strip()]
    return salida


def copia(nombre, escenarios, extra=()):
    """Copia en tmp_ref/<nombre>/ los escenarios (cfg y lo que nombra) y los archivos extra de plan3/, y deja el
    cwd ahi: los brazos actuado y trivial regeneran su .add.xml en la carpeta actual y no deben tocar plan3/."""
    import shutil
    destino = os.path.join(TMP, nombre)
    os.makedirs(destino, exist_ok=True)
    for esc in escenarios:
        for rel in archivos_de_cfg(os.path.join(PLAN3, f"{esc}.sumocfg")):
            shutil.copyfile(os.path.join(PLAN3, rel), os.path.join(destino, rel))
    for rel in extra:
        shutil.copyfile(os.path.join(PLAN3, rel), os.path.join(destino, os.path.basename(rel)))
    os.chdir(destino)
    return destino


def huella_tripinfo(ruta):
    """sha256 (16 hex) de los registros <tripinfo> del archivo, sin la cabecera, y cuantos son."""
    regs = [ET.tostring(v, encoding="unicode") for v in ET.parse(ruta).getroot().findall("tripinfo")]
    return hashlib.sha256("".join(regs).encode()).hexdigest()[:16], len(regs)


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def sumo_directo(cfg, adicionales, semilla, tripinfo, extra=(), log=None):
    """sumo con las opciones de barrer_fijo.correr_sumo; adicionales = valor de --additional-files (o None)."""
    import barrer_fijo as bf
    import comun
    cmd = ["sumo", "-c", cfg, "--seed", str(semilla), "--tripinfo-output", tripinfo,
           "--tripinfo-output.write-unfinished", "true", "--device.emissions.probability", "1",
           "--no-step-log", "true", "--end", str(bf.FIN_SIM)] + comun.args_estadisticas(tripinfo)
    # con log: los avisos se escriben (los .sumocfg traen no-warnings true; la linea de comandos manda)
    cmd += ["--log", log, "--no-warnings", "false"] if log else ["--no-warnings", "true"]
    if adicionales:
        cmd += ["--additional-files", adicionales]
    subprocess.run(cmd + list(extra), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return comun.leer_tripinfo(tripinfo)


def cabecera_codigo(archivos=("comun.py", "rl_ippo.py", "evaluar.py", "rl_corredor.py")):
    """Lineas que dicen con que codigo se corre: el commit (HEAD), si esos archivos tienen cambios sin commitear y
    el sha256 de cada uno con los fines de linea de git (LF): es el de 'git show <commit>:<archivo>', el mismo en
    cualquier worktree."""
    def git(*args):
        return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    sucios = git("status", "--porcelain", "--", *archivos)
    lineas = [f"Codigo: commit {git('rev-parse', 'HEAD')} (rama {git('rev-parse', '--abbrev-ref', 'HEAD')}); "
              + ("estos archivos sin cambios frente al commit" if not sucios else f"CON CAMBIOS: {sucios}")]
    for a in archivos:
        with open(os.path.join(RAIZ, a), "rb") as f:
            crudo = f.read().replace(b"\r\n", b"\n")
        lineas.append(f"  sha256 {a}: {hashlib.sha256(crudo).hexdigest()}")
    return lineas


class Informe:
    """Acumula lineas, las imprime y al final las escribe en pruebas/ref/salidas/<nombre>.txt."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.lineas = []
        self.fallas = 0

    def __call__(self, texto=""):
        print(texto, flush=True)
        self.lineas.append(str(texto))

    def chequeo(self, ok, texto):
        self(("OK    " if ok else "FALLA ") + texto)
        if not ok:
            self.fallas += 1
        return ok

    def cerrar(self):
        self(f"\nRESULTADO: {'PASA' if self.fallas == 0 else f'{self.fallas} FALLAS'}")
        with open(os.path.join(SALIDAS, f"{self.nombre}.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(self.lineas) + "\n")
        return self.fallas
