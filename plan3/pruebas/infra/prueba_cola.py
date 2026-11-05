"""
prueba_cola.py - Prueba de cola.py con trabajos de mentira en plan3/tmp_cola/ (copia de cola.py y protecciones.py
con un prerregistro de prueba que permite el script ficticio.py).

Uso (desde plan3/):  python pruebas/infra/prueba_cola.py
Casos (PLAN3 0.4):
  A bien; B depende de A; C falla y D depende de C (bloqueado); E sale con 0 sin escribir su salida (fallido);
  F se mata con taskkill /F a mitad (fallido); G y su cola se matan juntos y la cola se reinicia (huerfano sin
  salidas: fallido); H falla una vez con 'WinError 32' y se reintenta (hecho); I no cabe antes del corte (no corre);
  J escribe su salida, falla al cerrar con 'WinError 32' y el reintento sale con 0 sin escribir (hecho: la salida es
  del primer intento).
Salida: pruebas/infra/prueba_cola.txt. Sale con codigo 1 si algo no da lo esperado.
"""
import os
import sys
import json
import time
import shutil
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN3 = os.path.dirname(os.path.dirname(AQUI))
TMP = os.path.join(PLAN3, "tmp_cola")
FICTICIO = r'''
import os, sys, time
modo, salida, espera = sys.argv[1], sys.argv[2], float(sys.argv[3])
time.sleep(espera)
if modo == "bien":
    os.makedirs(os.path.dirname(salida) or ".", exist_ok=True)
    open(salida, "w").write("ok")
elif modo == "falla":
    sys.exit(1)
elif modo == "sin_salida":
    pass
elif modo == "ya_hecho":
    marca = salida + ".intento"
    if not os.path.exists(marca):
        open(marca, "w").write("1")
        open(salida, "w").write("ok")
        print("PermissionError: [WinError 32] archivo tomado al cerrar")
        sys.exit(1)
    # segundo intento: ya estaba hecho (como rl_ippo --reanudar auto), sale con 0 sin escribir
elif modo == "reintento":
    marca = salida + ".intento"
    if not os.path.exists(marca):
        open(marca, "w").write("1")
        print("PermissionError: [WinError 32] El proceso no tiene acceso al archivo")
        sys.exit(1)
    open(salida, "w").write("ok")
'''


def preparar():
    if os.path.exists(TMP):
        shutil.rmtree(TMP)
    os.makedirs(os.path.join(TMP, "cola"))
    for f in ("cola.py", "protecciones.py"):
        shutil.copy(os.path.join(PLAN3, f), TMP)
    with open(os.path.join(PLAN3, "PRERREGISTRO.md"), encoding="utf-8") as f:
        texto = f.read()
    texto = texto.replace('"demanda_estocastica.py"]', '"demanda_estocastica.py", "ficticio.py"]')
    with open(os.path.join(TMP, "PRERREGISTRO.md"), "w", encoding="utf-8") as f:
        f.write(texto)
    with open(os.path.join(TMP, "ficticio.py"), "w", encoding="utf-8") as f:
        f.write(FICTICIO)


def trabajo(tid, modo, espera, requiere=(), duracion=60, prioridad=1):
    return {"id": tid, "prioridad": prioridad, "cpus": 1, "requiere": list(requiere), "uso": "sin_semillas",
            "cmd": f"python ficticio.py {modo} sal/{tid}.txt {espera}", "salidas": [f"sal/{tid}.txt"],
            "duracion": duracion}


def escribir(trabajos):
    with open(os.path.join(TMP, "cola", "trabajos.jsonl"), "w", encoding="utf-8") as f:
        for t in trabajos:
            f.write(json.dumps(t) + "\n")


def estado():
    with open(os.path.join(TMP, "cola", "estado.json"), encoding="utf-8") as f:
        return json.load(f)


def pid_de(tid):
    """PID del python que corre el trabajo tid (por su linea de comando)."""
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                        "ForEach-Object { \"$($_.ProcessId)|$($_.CommandLine)\" }"],
                       capture_output=True, text=True, timeout=60)
    for linea in r.stdout.splitlines():
        if f"sal/{tid}.txt" in linea:
            return int(linea.split("|", 1)[0])
    return None


def main():
    preparar()
    lineas, errores = [], 0

    def revisar(desc, cond):
        nonlocal errores
        errores += not cond
        lineas.append(f"{'ok ' if cond else 'MAL'} {desc}")

    # Ronda 1: A, B, C, D, E, F (F se mata), H (reintento), I (no cabe antes del corte)
    hasta = time.strftime("%H:%M", time.localtime(time.time() + 600))
    escribir([trabajo("A", "bien", 1), trabajo("B", "bien", 1, ["trabajo:A"]), trabajo("C", "falla", 1),
              trabajo("D", "bien", 1, ["trabajo:C"]), trabajo("E", "sin_salida", 1), trabajo("F", "bien", 40),
              trabajo("H", "reintento", 1), trabajo("I", "bien", 1, duracion=7200), trabajo("J", "ya_hecho", 1)])
    cola = subprocess.Popen([sys.executable, "cola.py", "--sin-git", "--cpus", "4", "--hasta", hasta], cwd=TMP,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    pid = None
    for _ in range(60):
        time.sleep(1)
        pid = pid_de("F")
        if pid:
            break
    time.sleep(3)
    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
    salida1 = cola.communicate(timeout=300)[0]
    e = estado()
    revisar("A y B hechos", {"A", "B"} <= set(e["hechos"]))
    revisar("C fallido", "C" in e["fallidos"])
    revisar("D bloqueado (no corrio)", "D" not in e["hechos"] and "D" in e.get("salida", {}).get("bloqueados", []))
    revisar("E fallido por salidas incompletas", e["fallidos"].get("E") == "salidas incompletas")
    revisar("F matado con taskkill: fallido, no hecho", "F" in e["fallidos"] and "F" not in e["hechos"])
    revisar("H hecho tras un reintento", "H" in e["hechos"] and e["reintentos"].get("H") == 1)
    revisar("J hecho: el reintento no reescribe y la salida del primer intento cuenta",
            "J" in e["hechos"] and e["reintentos"].get("J") == 1)
    revisar("I no corrio (no cabe antes del corte)", "I" not in e["hechos"] and "I" not in e["fallidos"]
            and "I" in e.get("salida", {}).get("pendientes", []))
    # Ronda 2: G y la cola se matan juntos; la cola se reinicia y G queda como huerfano sin salidas
    escribir([trabajo("G", "bien", 60)])
    os.remove(os.path.join(TMP, "cola", "estado.json"))
    cola = subprocess.Popen([sys.executable, "cola.py", "--sin-git", "--cpus", "4", "--hasta", hasta], cwd=TMP,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    pid = None
    for _ in range(60):
        time.sleep(1)
        pid = pid_de("G")
        if pid:
            break
    time.sleep(6)                                   # la cola guarda "corriendo" cada 5 s
    subprocess.run(["taskkill", "/F", "/PID", str(cola.pid)], capture_output=True)
    subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
    cola.communicate(timeout=60)
    revisar("G figura corriendo en el estado guardado", "G" in estado().get("corriendo", {}))
    cola = subprocess.run([sys.executable, "cola.py", "--sin-git", "--cpus", "4", "--hasta", hasta], cwd=TMP,
                          capture_output=True, text=True, timeout=300)
    e = estado()
    revisar("G huerfano sin salidas: fallido, no hecho", "G" not in e["hechos"]
            and "huerfano" in str(e["fallidos"].get("G", "")))
    # Ronda 3: la capa 1 rechaza un trabajo malo al arrancar (no se lanza nada)
    malo = trabajo("M", "bien", 1)
    malo["cmd"] = "python ../rl_ippo.py train --escenario corredor --seed 42 --val-seeds 999"
    escribir([trabajo("A2", "bien", 1), malo])
    r = subprocess.run([sys.executable, "cola.py", "--sin-git", "--cpus", "4"], cwd=TMP, capture_output=True,
                       text=True, timeout=120)
    revisar("un trabajo malo en la lista: la cola no lanza nada", r.returncode != 0 and "problemas" in r.stdout + r.stderr
            and not os.path.exists(os.path.join(TMP, "sal", "A2.txt")))
    lineas.append(f"{sum(l.startswith('ok') for l in lineas)} de {len(lineas)} comprobaciones bien")
    lineas.append("--- salida de la ronda 1 ---")
    lineas.append(salida1.strip())
    texto = "\n".join(lineas)
    print(texto)
    with open(os.path.join(AQUI, "prueba_cola.txt"), "w", encoding="utf-8") as f:
        f.write(texto + "\n")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
