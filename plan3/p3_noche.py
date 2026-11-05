"""
p3_noche.py - Rutina de cada noche del bloque plan3 (PLAN3 0.4 y 0.16).

Uso (desde <worktree de ejecucion>/plan3):  python p3_noche.py --hasta 07:30 [--desde 21:00] [--cpus 12]
Pasos, en orden; si el 1 encuentra problemas no corre nada:
  1. protecciones.py antes (git, prerregistro igual al de origin, insumos, checkpoints, versiones, lista de trabajos);
  2. cola.py --hasta HH:MM (no lanza lo que no alcance a terminar antes del corte);
  3. protecciones.py despues;
  4. borra los tripinfo_*.xml que queden en plan3/ (pesan y no se usan);
  5. respaldo incremental de plan3/checkpoints fuera del repositorio y cola/manifiesto_checkpoints.json;
  6. cola/manifiesto_ciego.json: ruta, sha256, filas y semillas de cada CSV de ciego/ (sin metricas);
  7. cola/resumen_<fecha>.txt: hechos, fallidos y bloqueados de la noche (sin metricas).
Por la manana se commitean el estado, los logs, los manifiestos y los resultados no decisivos (nunca ciego/).
"""
import os
import sys
import csv
import glob
import json
import time
import shutil
import argparse
import subprocess

import protecciones

PLAN3 = os.path.dirname(os.path.abspath(__file__))
COLA = os.path.join(PLAN3, "cola")
CIEGO = os.path.join(PLAN3, "ciego")
RESPALDO = os.path.join(os.path.dirname(os.path.dirname(PLAN3)), "respaldo_plan3", "checkpoints")


def paso(nombre, cmd):
    print(f"{time.strftime('%H:%M:%S')} {nombre}: {' '.join(cmd)}", flush=True)
    r = subprocess.run([sys.executable] + cmd, cwd=PLAN3)
    print(f"{time.strftime('%H:%M:%S')} {nombre}: codigo {r.returncode}", flush=True)
    return r.returncode


def borrar_tripinfo():
    n = 0
    for raiz, _, archivos in os.walk(PLAN3):
        if os.path.relpath(raiz, PLAN3).startswith(("insumos", "ciego")):
            continue
        for a in archivos:
            if a.startswith("tripinfo_") and a.endswith(".xml"):
                os.remove(os.path.join(raiz, a))
                n += 1
    return n


def borrar_temporales():
    """Temporales (*.tmp) que dejo un trabajo cortado: la cola ya termino, asi que ninguno esta en uso. Que queden es
    senal de un corte; se cuentan en el resumen (revision del 05.11)."""
    rutas = []
    for raiz, dirs, archivos in os.walk(PLAN3):
        if os.path.relpath(raiz, PLAN3).split(os.sep)[0] in ("insumos", ".git"):
            dirs[:] = []
            continue
        rutas += [os.path.join(raiz, a) for a in archivos if a.endswith(".tmp")]
    for r in rutas:
        try:
            os.remove(r)
        except OSError:
            pass
    return [os.path.relpath(r, PLAN3) for r in rutas]


def respaldar_checkpoints():
    """Copia a RESPALDO lo nuevo o cambiado de plan3/checkpoints y escribe cola/manifiesto_checkpoints.json."""
    man = protecciones.manifiesto_checkpoints()
    copiados = 0
    for rel, h in man.items():
        destino = os.path.join(RESPALDO, rel)
        if os.path.exists(destino) and protecciones.sha(destino) == h:
            continue
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        shutil.copy2(os.path.join(PLAN3, "checkpoints", rel), destino)
        copiados += 1
    os.makedirs(COLA, exist_ok=True)
    with open(os.path.join(COLA, "manifiesto_checkpoints.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, indent=0, sort_keys=True)
    return len(man), copiados


def manifiesto_ciego():
    """Ruta, sha256, filas y semillas de cada CSV de ciego/. Solo cuenta filas y lee la columna de semillas."""
    salida = {}
    for raiz, _, archivos in os.walk(CIEGO):
        for a in sorted(archivos):
            p = os.path.join(raiz, a)
            rel = os.path.relpath(p, PLAN3).replace(os.sep, "/")
            info = {"sha256": protecciones.sha(p), "bytes": os.path.getsize(p)}
            if a.endswith(".csv"):
                with open(p, encoding="utf-8", newline="") as f:
                    filas = list(csv.DictReader(f))
                info["filas"] = len(filas)
                col = next((c for c in ("semilla", "seed") if filas and c in filas[0]), None)
                if col:
                    semillas = sorted({int(float(r[col])) for r in filas if r.get(col)})
                    info["semillas"] = [semillas[0], semillas[-1], len(semillas)] if semillas else []
            salida[rel] = info
    os.makedirs(COLA, exist_ok=True)
    with open(os.path.join(COLA, "manifiesto_ciego.json"), "w", encoding="utf-8") as f:
        json.dump(salida, f, indent=1, sort_keys=True)
    return len(salida)


def resumen(inicio):
    ruta = os.path.join(COLA, "estado.json")
    if not os.path.exists(ruta):
        return "sin estado"
    e = json.load(open(ruta, encoding="utf-8"))
    de_hoy = [t for t, r in e.get("registro", {}).items() if r.get("inicio_epoch", 0) >= inicio]
    hechos = [t for t in de_hoy if t in set(e.get("hechos", []))]
    fallidos = {t: v for t, v in e.get("fallidos", {}).items() if t in de_hoy or str(v).startswith("rechazado")}
    lineas = [f"noche del {time.strftime('%Y-%m-%d', time.localtime(inicio))}: {len(de_hoy)} trabajos lanzados, "
              f"{len(hechos)} hechos, {len(fallidos)} fallidos"]
    lineas += [f"  FALLO {t}: {v}" for t, v in sorted(fallidos.items())]
    sal = e.get("salida", {})
    if sal.get("bloqueados"):
        lineas.append(f"  bloqueados: {len(sal['bloqueados'])}: " + ", ".join(sal["bloqueados"][:20]))
    if sal.get("pendientes"):
        lineas.append(f"  pendientes para otra noche: {len(sal['pendientes'])}")
    reintentos = {t: n for t, n in e.get("reintentos", {}).items() if t in de_hoy}
    if reintentos:
        lineas.append(f"  reintentados por archivo tomado: {len(reintentos)}: " + ", ".join(sorted(reintentos)[:20]))
    # Prerregistro §14 (B22): un tramo relanzado debe repetir los episodios del intento anterior. rl_ippo deja las
    # diferencias en checkpoints/<tag>_rehechos.json; aqui solo se avisa (sin metricas).
    rehechos = [os.path.basename(p) for p in glob.glob(os.path.join(PLAN3, "checkpoints", "*_rehechos.json"))
                if os.path.getmtime(p) >= inicio]
    if rehechos:
        lineas.append(f"  PROBLEMA (B22): episodios rehechos que no repiten el intento anterior: {', '.join(rehechos)}")
    avisos = []
    for t in de_hoy:
        ruta_log = os.path.join(COLA, "logs", t + ".log")
        if os.path.exists(ruta_log):
            with open(ruta_log, encoding="utf-8", errors="replace") as f:
                avisos += [f"{t}: {l.strip()[:160]}" for l in f if l.startswith("AVISO")]
    if avisos:
        lineas.append(f"  avisos en los logs ({len(avisos)}):")
        lineas += [f"    {a}" for a in avisos[:30]]
    return "\n".join(lineas)


def esperar_hasta(hhmm):
    """Duerme hasta la proxima vez que el reloj marque HH:MM (para dejar la noche lanzada de dia)."""
    import datetime
    h, m = (int(x) for x in hhmm.split(":"))
    ahora = datetime.datetime.now()
    objetivo = ahora.replace(hour=h, minute=m, second=0, microsecond=0)
    if objetivo <= ahora:
        objetivo += datetime.timedelta(days=1)
    print(f"{time.strftime('%H:%M:%S')} esperando hasta {objetivo:%Y-%m-%d %H:%M}", flush=True)
    while datetime.datetime.now() < objetivo:
        time.sleep(30)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hasta", required=True, help="HH:MM de corte")
    ap.add_argument("--desde", default=None, help="HH:MM: espera hasta esa hora para empezar")
    ap.add_argument("--cpus", type=int, default=12)
    args = ap.parse_args()
    if args.desde:
        esperar_hasta(args.desde)
    inicio = time.time()
    os.makedirs(COLA, exist_ok=True)
    if paso("protecciones antes", ["protecciones.py", "antes"]) != 0:
        sys.exit("p3_noche: las protecciones encontraron problemas; no se corre nada")
    paso("cola", ["cola.py", "--hasta", args.hasta, "--cpus", str(args.cpus)])
    paso("protecciones despues", ["protecciones.py", "despues"])
    print(f"tripinfo borrados: {borrar_tripinfo()}", flush=True)
    temporales = borrar_temporales()
    print(f"temporales de trabajos cortados: {len(temporales)} {temporales[:10]}", flush=True)
    total, copiados = respaldar_checkpoints()
    print(f"checkpoints: {total} registrados, {copiados} copiados al respaldo", flush=True)
    print(f"manifiesto ciego: {manifiesto_ciego()} archivos", flush=True)
    texto = resumen(inicio)
    with open(os.path.join(COLA, f"resumen_{time.strftime('%Y%m%d', time.localtime(inicio))}.txt"), "w",
              encoding="utf-8") as f:
        f.write(texto + "\n")
    print(texto, flush=True)


if __name__ == "__main__":
    main()
