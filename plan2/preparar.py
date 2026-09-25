"""
preparar.py - Copia a plan2/ los archivos de un escenario (el .sumocfg y lo que referencia).

Uso (desde demo_rl/plan2):  python preparar.py corredor [red ...]

Los archivos fuente viven en demo_rl/. El programa fijo (.add.xml) se copia como punto de
partida; el barrido del plan v2 lo reemplaza en plan2/ por el ganador de esa celda, sin tocar
el original de demo_rl/.
"""
import os
import sys
import shutil
import xml.etree.ElementTree as ET

PLAN2 = os.path.dirname(os.path.abspath(__file__))
FUENTE = os.path.dirname(PLAN2)


def copiar(nombre):
    origen = os.path.join(FUENTE, nombre)
    if not os.path.exists(origen):
        sys.exit(f"falta {origen}")
    shutil.copy2(origen, os.path.join(PLAN2, nombre))
    print(f"  {nombre}")


def preparar(esc):
    cfg = f"{esc}.sumocfg"
    copiar(cfg)
    raiz = ET.parse(os.path.join(FUENTE, cfg)).getroot()
    for etiqueta in ("net-file", "route-files", "additional-files"):
        nodo = raiz.find(f".//{etiqueta}")
        if nodo is None:
            continue
        for nombre in nodo.get("value", "").split(","):
            nombre = nombre.strip()
            if nombre:
                copiar(nombre)


if __name__ == "__main__":
    for esc in sys.argv[1:]:
        print(f"preparando {esc}:")
        preparar(esc)
