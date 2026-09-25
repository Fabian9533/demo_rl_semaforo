"""
demo.py - Demostracion en vivo del plan de pruebas v2: abre una ventana de sumo-gui por modelo,
lado a lado, con el mismo trafico (misma semilla) para comparar a simple vista.

Uso (desde demo_rl/plan2):
  python demo.py lista                          casos y modelos disponibles
  python demo.py P3                             fijo contra IPPO vecinos en la red (dos ventanas)
  python demo.py P5 fijo actuado ippo_vecinos   tres ventanas en la malla 3x3
  python demo.py P1 ippo_local ippo_vecinos --delay 0
Opciones: --delay N  milisegundos por paso de simulacion (por defecto 50; 0 = lo mas rapido)
          --seed S   semilla de SUMO (por defecto, la semilla representativa del caso: ver abajo)
          --sin-gui  corre igual pero sin ventanas (para comprobar que todo funciona)

Semilla representativa por caso (de las 30 de la evaluacion final, la que deja a IPPO vecinos mas
cerca de su diferencia media frente al fijo y frente al actuado; calculada el 25.09 sobre
evaluacion_<esc>.csv): P1 1003, P2 1022, P3 1026, P4 1011, P5 1006. Con otra semilla el resultado
puede alejarse de la media: en P5 con la 1001 IPPO vecinos queda 11.8 % sobre el fijo, y es una de
las 6 semillas desfavorables de 30.

Cada modelo usa su politica publicada: la base mediana por validacion segun
plan2/veredicto_congelado_0355.csv (la misma que la tabla de veredicto). Al terminar cada
ventana, la consola imprime el retraso por vehiculo (timeloss_prom) de esa corrida.
En sumo-gui el control "Delay" de la barra superior acelera o frena la simulacion en vivo.
"""
import os
import sys
import csv
import subprocess
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
CASOS = {"P1": "corredor", "P2": "corredor_alta", "P3": "red", "P4": "red_alta", "P5": "malla3"}
NOMBRES = {"P1": "corredor, 2 semaforos", "P2": "corredor con demanda doble",
           "P3": "red de 3 cruces con rotonda", "P4": "red con demanda 1.2x", "P5": "malla 3x3, 9 semaforos"}
SEMILLA_REPRESENTATIVA = {"P1": 1003, "P2": 1022, "P3": 1026, "P4": 1011, "P5": 1006}
MODELOS = ["fijo", "actuado", "ql", "sarsa", "dqn", "ippo_local", "ippo_vecinos", "mappo"]


def bases_publicadas():
    ruta = os.path.join(AQUI, "veredicto_congelado_0355.csv")
    with open(ruta, encoding="utf-8") as f:
        return {(r["caso"], r["modelo"]): (r["base_publicada"], r["veredicto"]) for r in csv.DictReader(f)}


def comando(esc, modelo, base, delay, seed, gui):
    g = ["--gui", "--delay", str(delay)] if gui else []
    s = ["--seed", str(seed)]
    if modelo == "fijo":
        return ["../rl_corredor.py", "baseline", "--escenario", esc] + g + s
    if modelo == "actuado":
        return ["../rl_corredor.py", "actuado", "--escenario", esc] + g + s
    if modelo in ("ql", "sarsa"):
        return ["../rl_corredor.py", "demo", "--escenario", esc,
                "--qtable", f"q_table_{esc}_{modelo}_s{base}.json"] + g + s
    if modelo.startswith("ippo_"):
        variante = modelo[len("ippo_"):]
        return ["../rl_ippo.py", "demo", "--escenario", esc,
                "--politica", f"politica_{esc}_{variante}_s{base}.pt"] + g + s
    if modelo == "dqn":
        return ["../rl_dqn.py", "demo", "--escenario", esc, "--politica", f"politica_{esc}_dqn_s{base}.pt"] + g + s
    if modelo == "mappo":
        return ["../rl_mappo.py", "demo", "--escenario", esc,
                "--politica", f"politica_{esc}_mappo_s{base}.pt"] + g + s
    sys.exit(f"modelo desconocido: {modelo}")


def main():
    args = sys.argv[1:]
    delay, seed, gui = 50, None, True
    if "--delay" in args:
        i = args.index("--delay"); delay = int(args[i + 1]); del args[i:i + 2]
    if "--seed" in args:
        i = args.index("--seed"); seed = int(args[i + 1]); del args[i:i + 2]
    if "--sin-gui" in args:
        args.remove("--sin-gui"); gui = False
    publicadas = bases_publicadas()
    if not args or args[0] == "lista":
        print("Casos:")
        for caso, esc in CASOS.items():
            print(f"  {caso}  {esc:14s} {NOMBRES[caso]}")
            for m in MODELOS[2:]:
                base, ver = publicadas.get((caso, m), ("", ""))
                if base:
                    print(f"        {m:13s} base {base:5s} {ver}")
        print("Modelos: " + ", ".join(MODELOS))
        return
    caso = args[0].upper()
    if caso not in CASOS:
        sys.exit(f"caso desconocido: {caso} (usa P1..P5)")
    esc = CASOS[caso]
    seed = seed or SEMILLA_REPRESENTATIVA[caso]
    print(f"{caso} ({NOMBRES[caso]}), semilla {seed}")
    modelos = args[1:] or ["fijo", "ippo_vecinos"]
    procesos = []
    for m in modelos:
        base = ""
        if m not in ("fijo", "actuado"):
            base, ver = publicadas.get((caso, m), ("", ""))
            if not base:
                print(f"{m}: no tiene politica publicada en {caso}; se omite")
                continue
        cmd = [sys.executable] + comando(esc, m, base, delay, seed, gui)
        print(f"{caso} {esc}: {m}" + (f" (base {base})" if base else "") + " -> " + " ".join(cmd[1:]))
        procesos.append((m, subprocess.Popen(cmd, cwd=AQUI, stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT, text=True)))
        time.sleep(3)   # los modos de rl_corredor abren el mismo CSV de registro al arrancar
    for m, p in procesos:
        salida = p.communicate()[0]
        linea = next((l for l in reversed(salida.splitlines()) if "timeloss_prom" in l), "")
        tl = linea.split("'timeloss_prom':")[1].split(",")[0].strip() if "'timeloss_prom':" in linea else "?"
        print(f"{m:13s} retraso por vehiculo {tl} s" + ("" if p.returncode == 0 else f"  (codigo {p.returncode})"))
        if p.returncode != 0:
            print(salida[-1500:])


if __name__ == "__main__":
    main()
