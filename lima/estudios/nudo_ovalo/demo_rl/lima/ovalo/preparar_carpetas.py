"""
preparar_carpetas.py - Arma las carpetas de trabajo del estudio del nudo en el Ovalo Vasco (18.11.2026), con la misma
forma que lima/ y lima/alta/ en el repositorio, para que estudio.py, borde_actuado.py y rl_ippo.py corran sin cambios:

  lima/                    demanda publicada
  lima/alta/               demanda alta (x1.2)
  lima/robustez/reducto/   prueba de robustez del reparto: mas carga en Reducto (el mismo total publicado)
  lima/robustez/transversal/   lo mismo, mas carga en 28 de Julio y Balboa

En cada una escribe (entre parentesis, el nombre de cada parte para --solo):
  lima.net.xml        (red) la red del ovalo (ovalo/red/ovalo_estudio.net.xml, de armar_ovalo.py)
  lima.rou.xml        (rutas) la demanda de ovalo/entrada/rutas_estudio/ (la escribe lima/demanda.py) con el camino de
                      cada movimiento dentro del ovalo en el atributo via (armar_rutas.convertir); nada mas cambia
  lima.sumocfg        (cfg) el del estudio (lima/lima.sumocfg) con una linea mas: <ignore-junction-blocker value="10"/>
  e2_lima_75.add.xml  (e2) los detectores E2 de 75 m de ESTA red (ovalo/red/e2_ovalo_estudio_75.add.xml, que escribe
                      armar_ovalo.py: uno por carril de entrada, con el formato de rl_ippo.archivo_e2)
  lima.add.xml        (programas) el plan actual en el ovalo (programa_ovalo.py)
  lima_libre.json     (programas) el programa del orden libre (programa_ovalo.escribir_libre)
Los fijos y actuados ajustados no se escriben aqui: los escribe estudio.py (ajustar-fijo, ajustar-actuado) en lima/ y
lima/alta/; las carpetas de robustez reciben los de lima/ con el lanzador de la robustez.

Uso (desde lima/ovalo):  python -B preparar_carpetas.py                 # todo
                         python -B preparar_carpetas.py --solo rutas    # solo la demanda (la usa regenerar_demanda.py)

Correccion de carriles (18.11.2026, nudo_ovalo_estudio2), dos cambios frente a nudo_ovalo_estudio/:
  - La demanda ya no es la de la revision del 17.11 (cambiaron los carriles de Reducto y entro Balboa hacia Larco): se
    quita la guarda de sus md5. Lo que se exige es lo de siempre: cada flujo de la carpeta es el de
    entrada/rutas_estudio/ mas su camino (lo comprueban armar_rutas.convertir y comprobar_red.py).
  - Los detectores E2 ya no son la copia de la red del estudio (traia e2_RS_S1_4, un carril que ya no existe, y le
    faltaba e2_RN_S1_4): son los de la red nueva.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))           # lima/ovalo
LIMA = os.path.dirname(AQUI)
ENTRADA = os.path.join(AQUI, "entrada")
RED = os.path.join(AQUI, "red", "ovalo_estudio.net.xml")
E2 = os.path.join(AQUI, "red", "e2_ovalo_estudio_75.add.xml")
sys.path.insert(0, AQUI)
import armar_rutas  # noqa: E402

CARPETAS = {"": "publicada", "alta": "alta", os.path.join("robustez", "reducto"): os.path.join("robustez", "reducto"),
            os.path.join("robustez", "transversal"): os.path.join("robustez", "transversal")}
VALVULA = '        <ignore-junction-blocker value="10"/>'
PARTES = ("red", "rutas", "cfg", "e2", "programas")


def sumocfg():
    """El .sumocfg del estudio con la valvula de SUMO para las trabas en una esquina (supuesto 3 de la tarea): un
    vehiculo que lleva 10 s detenido bloqueando un cruce deja de bloquear a los demas."""
    with open(os.path.join(ENTRADA, "red_estudio", "lima.sumocfg"), encoding="utf-8") as f:
        texto = f.read()
    linea = '        <time-to-teleport value="-1"/>\n'
    assert texto.count(linea) == 1
    nuevo = texto.replace(linea, linea + VALVULA + "\n")
    assert nuevo.replace(VALVULA + "\n", "") == texto
    return nuevo


def main(partes=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if partes is None:
        ap = argparse.ArgumentParser()
        ap.add_argument("--solo", default=",".join(PARTES), help="partes a escribir, separadas por coma: " + ", ".join(PARTES))
        partes = [p.strip() for p in ap.parse_args().solo.split(",") if p.strip()]
    assert set(partes) <= set(PARTES), partes
    cfg = sumocfg()
    for sub, fuente in CARPETAS.items():
        destino = os.path.join(LIMA, sub)
        os.makedirs(destino, exist_ok=True)
        escritos = []
        if "red" in partes:
            shutil.copyfile(RED, os.path.join(destino, "lima.net.xml"))
            escritos.append("lima.net.xml")
        if "e2" in partes:
            shutil.copyfile(E2, os.path.join(destino, "e2_lima_75.add.xml"))
            escritos.append("e2_lima_75.add.xml")
        if "cfg" in partes:
            with open(os.path.join(destino, "lima.sumocfg"), "w", encoding="utf-8", newline="\n") as f:
                f.write(cfg)
            escritos.append("lima.sumocfg")
        if "rutas" in partes:
            with open(os.path.join(ENTRADA, "rutas_estudio", fuente, "lima.rou.xml"), encoding="utf-8") as f:
                texto = f.read()
            nuevo, n = armar_rutas.convertir(texto)
            assert n == len(re.findall(r"<flow ", texto)), "no todos los flujos tienen camino"
            with open(os.path.join(destino, "lima.rou.xml"), "w", encoding="utf-8", newline="\n") as f:
                f.write(nuevo)
            escritos.append(f"lima.rou.xml ({n} flujos con camino)")
        if "programas" in partes:
            # el plan actual y el programa del orden libre, con el escritor del ovalo sobre la red de la carpeta
            r = subprocess.run([sys.executable, "-B", os.path.join(LIMA, "programa_ovalo.py")],
                               env={**os.environ, "LIMA_CARPETA": sub}, capture_output=True, text=True)
            if r.returncode:
                raise SystemExit(f"programa_ovalo.py en {sub or 'lima'}:\n{r.stdout}{r.stderr}")
            escritos += ["lima.add.xml", "lima_libre.json"]
        print(f"{sub or '.'}: " + ", ".join(escritos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
