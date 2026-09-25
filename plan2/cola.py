"""
cola.py - Cola de trabajos del plan de pruebas v2, con prioridades y dependencias.

Uso (desde demo_rl/plan2):  python cola.py [--cpus 11]

Lee cola/trabajos.jsonl (una linea JSON por trabajo; una linea posterior con el mismo id
reemplaza a la anterior) y lanza, en orden de prioridad (menor primero), los trabajos cuyas
dependencias ya se cumplen, sin pasar de --cpus procesos a la vez. Un trabajo es
  {"id": ..., "prioridad": 2, "cpus": 1, "requiere": ["listo/ippo.ok", "trabajo:prep_red"],
   "cmd": "python ../rl_ippo.py train ..."}
"listo/x.ok" exige que exista ese archivo (relativo a plan2/) y "trabajo:<id>" que ese trabajo
haya terminado bien. Cada trabajo escribe su salida en cola/logs/<id>.log. El estado (hechos,
fallidos) queda en cola/estado.json, asi que la cola se puede reiniciar sin repetir nada.
Archivos de control: cola/pausa (no lanza nada nuevo), cola/fin (sale cuando no quede nada
corriendo), cola/reintentar.txt (ids fallidos a volver a intentar, uno por linea).
"""
import os
import sys
import json
import time
import argparse
import subprocess

RAIZ = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(RAIZ, "cola")
TRABAJOS = os.path.join(DIR, "trabajos.jsonl")
ESTADO = os.path.join(DIR, "estado.json")
LOGS = os.path.join(DIR, "logs")


def leer_trabajos():
    trabajos, orden = {}, {}
    if not os.path.exists(TRABAJOS):
        return trabajos, orden
    with open(TRABAJOS, encoding="utf-8") as f:
        for n, linea in enumerate(f):
            linea = linea.strip()
            if not linea:
                continue
            try:
                t = json.loads(linea)
            except json.JSONDecodeError:
                continue
            trabajos[t["id"]] = t
            orden.setdefault(t["id"], n)
    return trabajos, orden


def leer_estado():
    if os.path.exists(ESTADO):
        with open(ESTADO, encoding="utf-8") as f:
            e = json.load(f)
        return set(e.get("hechos", [])), dict(e.get("fallidos", {})), dict(e.get("tiempos", {}))
    return set(), {}, {}


def guardar_estado(hechos, fallidos, tiempos, corriendo, huerfanos):
    """En Windows os.replace falla si otro proceso esta leyendo estado.json en ese instante
    (paso el 24.09 y tumbo la cola): se reintenta y, si no se puede, se guarda en la vuelta
    siguiente. Nunca debe tumbar la cola."""
    tmp = ESTADO + ".tmp"
    en_curso = {k: round(time.time() - v[1]) for k, v in corriendo.items()}
    en_curso.update({k: -1 for k in huerfanos})
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"hechos": sorted(hechos), "fallidos": fallidos, "tiempos": tiempos,
                       "corriendo": en_curso, "actualizado": time.strftime("%Y-%m-%d %H:%M:%S")},
                      f, indent=1)
    except OSError:
        return
    for _ in range(20):
        try:
            os.replace(tmp, ESTADO)
            return
        except OSError:
            time.sleep(0.2)


def lineas_python():
    """Lineas de comando de los python.exe vivos (para seguir a los huerfanos de una cola caida)."""
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                        "Select-Object -ExpandProperty CommandLine"],
                       capture_output=True, text=True, timeout=60)
    return r.stdout


def termino_bien(tid):
    """Un huerfano que ya no esta vivo: bien si su log no tiene un Traceback."""
    try:
        with open(os.path.join(LOGS, tid + ".log"), encoding="utf-8", errors="replace") as f:
            texto = f.read()
    except OSError:
        return False
    return bool(texto.strip()) and "Traceback" not in texto


def cumple(req, hechos):
    if req.startswith("trabajo:"):
        return req[len("trabajo:"):] in hechos
    return os.path.exists(os.path.join(RAIZ, req))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cpus", type=int, default=11)
    args = ap.parse_args()
    os.makedirs(LOGS, exist_ok=True)
    hechos, fallidos, tiempos = leer_estado()
    corriendo = {}          # id -> (proceso, inicio, cpus, archivo_log)
    # Trabajos que corrian cuando la cola anterior se cayo: siguen vivos sin nadie que los espere.
    # Se reconocen por su linea de comando y no se relanzan.
    huerfanos = {}
    if os.path.exists(ESTADO):
        with open(ESTADO, encoding="utf-8") as f:
            previos = json.load(f).get("corriendo", {})
        trabajos, _ = leer_trabajos()
        for tid in previos:
            if tid in trabajos and tid not in hechos:
                huerfanos[tid] = trabajos[tid]["cmd"].split(" ", 1)[1]
    revisado = 0.0
    if huerfanos:
        print(f"cola: {len(huerfanos)} huerfanos de la cola anterior: {sorted(huerfanos)}", flush=True)
    entorno = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONUNBUFFERED="1")
    print(f"cola: {len(hechos)} hechos, {len(fallidos)} fallidos al arrancar; cpus={args.cpus}", flush=True)
    while True:
        # 1. terminados
        for tid in list(corriendo):
            proc, inicio, cpus, log = corriendo[tid]
            if proc.poll() is None:
                continue
            log.close()
            dur = round(time.time() - inicio)
            tiempos[tid] = dur
            if proc.returncode == 0:
                hechos.add(tid)
                fallidos.pop(tid, None)
                print(f"{time.strftime('%H:%M:%S')} OK    {tid} ({dur} s)", flush=True)
            else:
                fallidos[tid] = proc.returncode
                print(f"{time.strftime('%H:%M:%S')} FALLO {tid} (codigo {proc.returncode}, {dur} s)", flush=True)
            del corriendo[tid]
        # 1b. huerfanos que terminaron
        if huerfanos and time.time() - revisado > 30:
            revisado = time.time()
            try:
                vivas = lineas_python()
            except Exception:
                vivas = None
            if vivas is not None:
                for tid in list(huerfanos):
                    if huerfanos[tid] in vivas:
                        continue
                    if termino_bien(tid):
                        hechos.add(tid)
                        print(f"{time.strftime('%H:%M:%S')} OK    {tid} (huerfano)", flush=True)
                    else:
                        fallidos[tid] = "huerfano"
                        print(f"{time.strftime('%H:%M:%S')} FALLO {tid} (huerfano)", flush=True)
                    del huerfanos[tid]
        # 2. reintentos pedidos a mano
        ruta_r = os.path.join(DIR, "reintentar.txt")
        if os.path.exists(ruta_r):
            with open(ruta_r, encoding="utf-8") as f:
                for tid in f.read().split():
                    fallidos.pop(tid, None)
                    hechos.discard(tid)
            os.remove(ruta_r)
        # 3. lanzar lo que se pueda
        trabajos, orden = leer_trabajos()
        usados = sum(c[2] for c in corriendo.values()) + len(huerfanos)
        if not os.path.exists(os.path.join(DIR, "pausa")):
            listos = [t for tid, t in trabajos.items()
                      if tid not in hechos and tid not in fallidos and tid not in corriendo
                      and tid not in huerfanos
                      and all(cumple(r, hechos) for r in t.get("requiere", []))]
            listos.sort(key=lambda t: (t.get("prioridad", 5), orden[t["id"]]))
            for t in listos:
                cpus = t.get("cpus", 1)
                if usados + cpus > args.cpus:
                    if usados == 0:          # un trabajo mas grande que la maquina: lanzarlo solo
                        pass
                    else:
                        continue
                log = open(os.path.join(LOGS, t["id"] + ".log"), "w", encoding="utf-8")
                cmd = t["cmd"].replace("python ", f'"{sys.executable}" ', 1) \
                    if t["cmd"].startswith("python ") else t["cmd"]
                proc = subprocess.Popen(cmd, cwd=RAIZ, shell=True, stdout=log,
                                        stderr=subprocess.STDOUT, env=entorno)
                corriendo[t["id"]] = (proc, time.time(), cpus, log)
                usados += cpus
                print(f"{time.strftime('%H:%M:%S')} INICIO {t['id']} (prio {t.get('prioridad', 5)}, "
                      f"{usados}/{args.cpus} cpus)", flush=True)
        guardar_estado(hechos, fallidos, tiempos, corriendo, huerfanos)
        if os.path.exists(os.path.join(DIR, "fin")) and not corriendo and not huerfanos:
            print("cola: fin", flush=True)
            return
        time.sleep(5)


if __name__ == "__main__":
    main()
