"""
reintentador.py - Relanza los trabajos que la cola marco como fallidos por el bloqueo del archivo
de salida de SUMO en Windows ('Could not build output file'). Hasta 2 reintentos por trabajo.
Uso (desde demo_rl/plan2):  python reintentador.py
"""
import os
import json
import time

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cola")
MARCAS = ("Could not build output file", "Connection closed by SUMO")
intentos = {}
while True:
    try:
        with open(os.path.join(DIR, "estado.json"), encoding="utf-8") as f:
            fallidos = json.load(f).get("fallidos", {})
    except Exception:
        fallidos = {}
    pedir = []
    for tid in fallidos:
        try:
            with open(os.path.join(DIR, "logs", tid + ".log"), encoding="utf-8", errors="replace") as f:
                texto = f.read()
        except Exception:
            continue
        if any(m in texto for m in MARCAS) and intentos.get(tid, 0) < 2:
            intentos[tid] = intentos.get(tid, 0) + 1
            pedir.append(tid)
    if pedir:
        with open(os.path.join(DIR, "reintentar.txt"), "a", encoding="utf-8") as f:
            f.write("\n".join(pedir) + "\n")
        print(time.strftime("%H:%M:%S"), "reintento pedido:", ", ".join(pedir), flush=True)
    time.sleep(20)
