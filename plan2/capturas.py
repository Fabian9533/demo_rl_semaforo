"""
capturas.py - Capturas de pantalla de los escenarios del plan de pruebas v2 en sumo-gui.

Uso (desde demo_rl/plan2):  python capturas.py [segundo] [escenario]   (por defecto 900, en la primera
punta, y los cinco escenarios)
Salida: captura_<escenario>.png, una por caso (P1-P5), con el programa fijo tuneado y la semilla
representativa de demo.py. Abre y cierra una ventana de sumo-gui por escenario.
"""
import os
import sys

import sumolib
import traci

AQUI = os.path.dirname(os.path.abspath(__file__))
CASOS = [("corredor", 1003), ("corredor_alta", 1022), ("red", 1026), ("red_alta", 1011), ("malla3", 1006)]


def main():
    segundo = int(sys.argv[1]) if len(sys.argv) > 1 else 900
    solo = sys.argv[2] if len(sys.argv) > 2 else None
    os.chdir(AQUI)
    for esc, semilla in CASOS:
        if solo and esc != solo:
            continue
        cmd = [sumolib.checkBinary("sumo-gui"), "-c", f"{esc}.sumocfg", "--seed", str(semilla),
               "--start", "--delay", "0", "--window-size", "1600,1000"]
        if os.path.exists(f"vista_{esc}.xml"):
            cmd += ["--gui-settings-file", f"vista_{esc}.xml"]
        traci.start(cmd)
        traci.simulationStep(segundo)
        vista = traci.gui.getIDList()[0]
        # Sin ancho ni alto: con ellos sumo-gui 1.25 se cierra al tomar la captura (24.09).
        traci.gui.screenshot(vista, os.path.join(AQUI, f"captura_{esc}.png").replace(os.sep, "/"))
        traci.simulationStep(segundo + 1)   # la captura se toma al terminar el paso siguiente
        traci.simulationStep(segundo + 2)
        traci.close()
        print(f"captura_{esc}.png (segundo {segundo}, semilla {semilla})", flush=True)


if __name__ == "__main__":
    main()
