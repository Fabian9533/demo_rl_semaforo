"""
cola.py - Cola de trabajos del bloque plan3, con prioridades, dependencias y hora de corte (DECISIONES B1).

Uso (desde <worktree de ejecucion>/plan3):
  python cola.py [--cpus 12] [--hasta HH:MM] [--seco] [--sin-git]

Lee cola/trabajos.jsonl (una linea JSON por trabajo; una linea posterior con el mismo id reemplaza a la anterior):
  {"id": ..., "prioridad": 2, "cpus": 1, "requiere": ["trabajo:<id>", "listo/x.ok"], "cmd": "python ...",
   "salidas": ["ruta relativa a plan3/", ...], "duracion": <s estimados>, "uso": "<bloque de semillas>"}
y lanza, por prioridad (menor primero), los trabajos cuyas dependencias se cumplen, sin pasar de --cpus. Cada trabajo
corre con cwd = plan3/ y escribe su salida en cola/logs/<id>.log. El estado queda en cola/estado.json, asi que la cola
se puede reiniciar sin repetir nada.

Cambios frente a plan2/cola.py:
  1. Revisa la lista entera con protecciones.py (capas 1 y 2) al arrancar y cada trabajo antes de lanzarlo.
  2. Antes de cada lanzamiento comprueba que HEAD es el commit de lanzamiento.sha256 (lo escribe
     chequeos_previos.py) y que el codigo y el prerregistro no tienen cambios sin commit; guarda el commit en el
     registro del trabajo.
  3. --hasta HH:MM: no lanza un trabajo cuya duracion estimada pase de esa hora; sale cuando no queda nada
     corriendo ni nada que quepa antes del corte.
  4. Un trabajo cuenta como hecho solo con codigo 0 y todas sus salidas declaradas, escritas despues de su inicio.
     Un huerfano de una cola caida cuenta como hecho solo si sus salidas estan completas; si no, como fallido.
  5. Reintenta sola, hasta 2 veces, los fallos de Windows por archivo tomado.
  6. Al salir lista los bloqueados (dependen de algo fallido).
Archivos de control: cola/pausa (no lanza nada nuevo), cola/fin (sale cuando no quede nada corriendo),
cola/reintentar.txt (ids fallidos a volver a intentar, uno por linea).
"""
import os
import sys
import json
import time
import argparse
import datetime
import subprocess

import protecciones

RAIZ = os.path.dirname(os.path.abspath(__file__))           # plan3/
DIR = os.path.join(RAIZ, "cola")
TRABAJOS = os.path.join(DIR, "trabajos.jsonl")
ESTADO = os.path.join(DIR, "estado.json")
LOGS = os.path.join(DIR, "logs")
LANZAMIENTO = os.path.join(RAIZ, "lanzamiento.sha256")
# Fallos de Windows o de SUMO que no dicen nada del trabajo: se reintenta (los entrenamientos reanudan solos).
MARCAS = ("Could not build output file", "Connection closed by SUMO", "WinError 32", "WinError 5]",
          "Errno 13] Permission denied", "error code: 32")   # archivo tomado (antivirus, respaldo) al escribir
MAX_REINTENTOS = 2


def ahora():
    return time.strftime("%Y-%m-%d %H:%M:%S")


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
            return json.load(f)
    return {}


def guardar_estado(e, corriendo, huerfanos):
    """En Windows os.replace falla si otro proceso lee estado.json en ese instante: se reintenta y, si no se puede,
    se guarda en la vuelta siguiente. Nunca debe tumbar la cola."""
    e["corriendo"] = {k: round(time.time() - v[1]) for k, v in corriendo.items()}
    e["corriendo"].update({k: -1 for k in huerfanos})
    e["actualizado"] = ahora()
    tmp = ESTADO + f".{os.getpid()}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(e, f, indent=1, ensure_ascii=False)
    except OSError:
        return
    for _ in range(20):
        try:
            os.replace(tmp, ESTADO)
            return
        except OSError:
            time.sleep(0.2)


def salidas_completas(t, desde=None):
    """Todas las salidas declaradas existen (y, si se da `desde`, se escribieron despues de esa hora)."""
    for rel in t.get("salidas", []):
        ruta = os.path.join(RAIZ, rel)
        if not os.path.exists(ruta):
            return False
        if desde is not None and os.path.getmtime(ruta) < desde - 2:
            return False
    return True


def procesos_vivos():
    """[(pid, pid del padre, linea de comando)] de los procesos vivos (para seguir a los huerfanos de una cola caida)."""
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process | ForEach-Object { \"$($_.ProcessId)|$($_.ParentProcessId)|"
                        "$($_.CommandLine)\" }"], capture_output=True, text=True, timeout=60)
    salida = []
    for linea in r.stdout.splitlines():
        partes = linea.split("|", 2)
        if len(partes) == 3 and partes[0].isdigit() and partes[1].isdigit():
            salida.append((int(partes[0]), int(partes[1]), partes[2]))
    return salida


def huerfano_vivo(cmd, pid, vivos):
    """¿Sigue vivo el trabajo? Por el pid del cmd.exe que lo lanzo (el proceso o un hijo suyo con su comando). Sin pid
    (estados viejos), por el comando entero entre los python vivos. Comparar solo texto confundia trabajos cuyo comando
    esta dentro del de otro (revision del 05.11)."""
    if pid:
        return any((p == pid or padre == pid) and cmd in linea for p, padre, linea in vivos)
    return any(cmd in linea for _, _, linea in vivos if "python" in linea.lower())


def cumple(req, hechos):
    if req.startswith("trabajo:"):
        return req[len("trabajo:"):] in hechos
    return os.path.exists(os.path.join(RAIZ, req))


def bloqueados(trabajos, hechos, fallidos):
    """Pendientes que nunca van a correr porque algo de lo que dependen fallo."""
    malos = set(fallidos)
    cambio = True
    while cambio:
        cambio = False
        for tid, t in trabajos.items():
            if tid in malos or tid in hechos:
                continue
            if any(r.startswith("trabajo:") and r[8:] in malos for r in t.get("requiere", [])):
                malos.add(tid)
                cambio = True
    return sorted(malos - set(fallidos))


def corte(hhmm):
    """Instante (epoch) de la proxima vez que el reloj marque HH:MM."""
    if not hhmm:
        return None
    h, m = (int(x) for x in hhmm.split(":"))
    hoy = datetime.datetime.now()
    c = hoy.replace(hour=h, minute=m, second=0, microsecond=0)
    if c <= hoy:
        c += datetime.timedelta(days=1)
    return c.timestamp()


def commit_aprobado():
    """Commit que aprobo chequeos_previos.py (primera palabra de lanzamiento.sha256), o None."""
    if not os.path.exists(LANZAMIENTO):
        return None
    with open(LANZAMIENTO, encoding="utf-8") as f:
        partes = f.read().split()
    return partes[0] if partes else None


def problema_de_arbol(sin_git):
    """Motivo para no lanzar nada (HEAD distinto del aprobado o codigo sin commit), o None."""
    if sin_git:
        return None
    aprobado = commit_aprobado()
    if not aprobado:
        return "falta lanzamiento.sha256 (corre chequeos_previos.py)"
    head = protecciones.git("rev-parse", "HEAD")[1].strip()
    if head != aprobado:
        return f"HEAD {head[:10]} no es el commit aprobado {aprobado[:10]}"
    _, cambios = protecciones.git("status", "--porcelain", "--untracked-files=no", "--", *protecciones.SIN_CAMBIOS)
    if cambios.strip():
        return "hay codigo, prerregistro o escenarios sin commit:\n" + cambios
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cpus", type=int, default=12)
    ap.add_argument("--hasta", default=None, help="HH:MM: no lanza trabajos que no alcancen a terminar antes")
    ap.add_argument("--seco", action="store_true", help="revisa la lista y muestra lo pendiente, sin lanzar")
    ap.add_argument("--sin-git", action="store_true", help="solo para pruebas: no exige el commit aprobado")
    args = ap.parse_args()
    trabajos, orden = leer_trabajos()
    problemas = protecciones.revisar_trabajos([trabajos[k] for k in sorted(trabajos, key=orden.get)])
    if problemas:
        for p in problemas:
            print("PROBLEMA:", p)
        sys.exit(f"cola: {len(problemas)} problemas en trabajos.jsonl; no se lanza nada")
    e = leer_estado()
    hechos, fallidos = set(e.get("hechos", [])), dict(e.get("fallidos", {}))
    if args.seco:
        pend = [t for tid, t in trabajos.items() if tid not in hechos and tid not in fallidos]
        pend.sort(key=lambda t: (t.get("prioridad", 5), orden[t["id"]]))
        b = set(bloqueados(trabajos, hechos, fallidos))
        h_p = sum(t.get("duracion", 0) * t.get("cpus", 1) for t in pend if t["id"] not in b) / 3600
        print(f"{len(trabajos)} trabajos: {len(hechos & set(trabajos))} hechos, {len(fallidos)} fallidos, "
              f"{len(b)} bloqueados, {len(pend) - len(b)} pendientes (~{h_p:.1f} h-proceso)")
        for t in pend:
            estado = "bloq  " if t["id"] in b else ("listo " if all(cumple(r, hechos) for r in t.get("requiere", []))
                                                     else "espera")
            print(f"  prio {t.get('prioridad', 5)}  {estado}  ~{t.get('duracion', 0) / 3600:.2f} h  {t['id']}")
        return
    motivo = problema_de_arbol(args.sin_git)
    if motivo:
        sys.exit(f"cola: no se lanza nada: {motivo}")
    os.makedirs(LOGS, exist_ok=True)
    fin_corte = corte(args.hasta)
    e.setdefault("tiempos", {})
    e.setdefault("registro", {})
    intentos = e.setdefault("reintentos", {})
    commit = protecciones.git("rev-parse", "HEAD")[1].strip()
    e.setdefault("arranques", []).append({"hora": ahora(), "commit": commit, "hasta": args.hasta,
                                          "sha_trabajos": protecciones.sha(TRABAJOS),
                                          "sha_prerregistro": protecciones.sha(os.path.join(RAIZ, "PRERREGISTRO.md"))})
    corriendo = {}          # id -> (proceso, inicio, cpus, archivo_log)
    # Trabajos que corrian cuando la cola anterior se cayo: siguen vivos sin nadie que los espere.
    huerfanos = {}
    for tid in e.get("corriendo", {}):
        if tid in trabajos and tid not in hechos:
            huerfanos[tid] = (trabajos[tid]["cmd"].split(" ", 1)[1], e.get("registro", {}).get(tid, {}).get("pid"))
    revisado = 0.0
    if huerfanos:
        print(f"cola: {len(huerfanos)} huerfanos de la cola anterior: {sorted(huerfanos)}", flush=True)
    entorno = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONUNBUFFERED="1",
                   PYTHONIOENCODING="utf-8")
    print(f"cola: {len(hechos)} hechos, {len(fallidos)} fallidos al arrancar; cpus={args.cpus}; "
          f"commit {commit[:10]}; corte {args.hasta or 'ninguno'}", flush=True)
    while True:
        # 1. terminados
        for tid in list(corriendo):
            proc, inicio, cpus, log = corriendo[tid]
            if proc.poll() is None:
                continue
            log.close()
            dur = round(time.time() - inicio)
            e["tiempos"][tid] = dur
            reg = e["registro"].setdefault(tid, {})
            reg.update({"fin": ahora(), "codigo": proc.returncode})
            t = trabajos.get(tid, {})
            # salidas escritas desde el PRIMER intento: un tramo relanzado que ya habia dejado su estado sale con 0
            # sin escribir nada nuevo, y eso es correcto (--reanudar auto)
            if proc.returncode == 0 and salidas_completas(t, desde=reg.get("primer_inicio_epoch", inicio)):
                hechos.add(tid)
                fallidos.pop(tid, None)
                print(f"{time.strftime('%H:%M:%S')} OK    {tid} ({dur} s)", flush=True)
            else:
                with open(os.path.join(LOGS, tid + ".log"), encoding="utf-8", errors="replace") as f:
                    texto = f.read()
                if proc.returncode != 0 and any(m in texto for m in MARCAS) and intentos.get(tid, 0) < MAX_REINTENTOS:
                    intentos[tid] = intentos.get(tid, 0) + 1
                    print(f"{time.strftime('%H:%M:%S')} REINTENTO {tid} ({intentos[tid]}/{MAX_REINTENTOS})", flush=True)
                else:
                    motivo = proc.returncode if proc.returncode != 0 else "salidas incompletas"
                    fallidos[tid] = motivo
                    print(f"{time.strftime('%H:%M:%S')} FALLO {tid} ({motivo}, {dur} s)", flush=True)
            del corriendo[tid]
        # 1b. huerfanos que terminaron: hechos solo con sus salidas completas
        if huerfanos and time.time() - revisado > 30:
            revisado = time.time()
            try:
                vivas = procesos_vivos()
            except Exception:
                vivas = None
            if vivas is not None:
                for tid in list(huerfanos):
                    if huerfano_vivo(*huerfanos[tid], vivas):
                        continue
                    reg = e["registro"].get(tid, {})
                    ini = reg.get("primer_inicio_epoch", reg.get("inicio_epoch"))
                    if salidas_completas(trabajos[tid], desde=ini):
                        hechos.add(tid)
                        print(f"{time.strftime('%H:%M:%S')} OK    {tid} (huerfano, salidas completas)", flush=True)
                    else:
                        fallidos[tid] = "huerfano sin salidas completas"
                        print(f"{time.strftime('%H:%M:%S')} FALLO {tid} (huerfano sin salidas completas)", flush=True)
                    del huerfanos[tid]
        # 2. reintentos pedidos a mano
        ruta_r = os.path.join(DIR, "reintentar.txt")
        if os.path.exists(ruta_r):
            with open(ruta_r, encoding="utf-8") as f:
                for tid in f.read().split():
                    fallidos.pop(tid, None)
                    hechos.discard(tid)
                    intentos.pop(tid, None)
            os.remove(ruta_r)
        # 3. lanzar lo que se pueda
        trabajos, orden = leer_trabajos()
        usados = sum(c[2] for c in corriendo.values()) + len(huerfanos)
        quedan_que_caben = False
        if not os.path.exists(os.path.join(DIR, "pausa")):
            listos = [t for tid, t in trabajos.items()
                      if tid not in hechos and tid not in fallidos and tid not in corriendo
                      and tid not in huerfanos and all(cumple(r, hechos) for r in t.get("requiere", []))]
            listos.sort(key=lambda t: (t.get("prioridad", 5), orden[t["id"]]))
            for t in listos:
                if fin_corte is not None and time.time() + t.get("duracion", 0) > fin_corte:
                    continue
                quedan_que_caben = True
                cpus = t.get("cpus", 1)
                if usados + cpus > args.cpus and usados > 0:
                    continue
                malos = protecciones.revisar_comando(t)
                if malos:
                    fallidos[t["id"]] = "rechazado: " + "; ".join(malos)
                    print(f"{time.strftime('%H:%M:%S')} RECHAZADO {t['id']}: {malos}", flush=True)
                    continue
                motivo = problema_de_arbol(args.sin_git)
                if motivo:
                    print(f"{time.strftime('%H:%M:%S')} cola: se detiene el lanzamiento: {motivo}", flush=True)
                    open(os.path.join(DIR, "pausa"), "w").close()
                    break
                ruta_log = os.path.join(LOGS, t["id"] + ".log")
                if os.path.exists(ruta_log):            # se guarda el log del intento anterior (su error)
                    k = 1
                    while os.path.exists(os.path.join(LOGS, f"{t['id']}.intento{k}.log")):
                        k += 1
                    try:
                        os.replace(ruta_log, os.path.join(LOGS, f"{t['id']}.intento{k}.log"))
                    except OSError:
                        pass
                log = open(ruta_log, "w", encoding="utf-8")
                cmd = t["cmd"].replace("python ", f'"{sys.executable}" ', 1)
                inicio = time.time()
                proc = subprocess.Popen(cmd, cwd=RAIZ, shell=True, stdout=log, stderr=subprocess.STDOUT,
                                        env=entorno)
                corriendo[t["id"]] = (proc, inicio, cpus, log)
                previo = e["registro"].get(t["id"], {})
                e["registro"][t["id"]] = {"inicio": ahora(), "inicio_epoch": inicio,
                                          "primer_inicio_epoch": previo.get("primer_inicio_epoch", inicio),
                                          "commit": protecciones.git("rev-parse", "HEAD")[1].strip(), "pid": proc.pid,
                                          "intento": intentos.get(t["id"], 0)}
                usados += cpus
                print(f"{time.strftime('%H:%M:%S')} INICIO {t['id']} (prio {t.get('prioridad', 5)}, "
                      f"{usados}/{args.cpus} cpus)", flush=True)
        e["hechos"], e["fallidos"] = sorted(hechos), fallidos
        guardar_estado(e, corriendo, huerfanos)
        termina = os.path.exists(os.path.join(DIR, "fin")) or (fin_corte is not None and not quedan_que_caben)
        if termina and not corriendo and not huerfanos:
            b = bloqueados(trabajos, hechos, fallidos)
            pend = [tid for tid in trabajos if tid not in hechos and tid not in fallidos and tid not in b]
            print(f"cola: fin; {len(hechos & set(trabajos))} hechos, {len(fallidos)} fallidos, {len(b)} bloqueados, "
                  f"{len(pend)} pendientes", flush=True)
            for tid in b:
                print("  bloqueado:", tid, flush=True)
            e["salida"] = {"hora": ahora(), "bloqueados": b, "pendientes": pend}
            guardar_estado(e, corriendo, huerfanos)
            return
        time.sleep(5)


if __name__ == "__main__":
    main()
