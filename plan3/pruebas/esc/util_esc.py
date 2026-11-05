"""
util_esc.py - Utilidades de las pruebas de los escenarios nuevos del plan 3 (tareas 0.5, 0.6, 2.4 y 2.5).

Las pruebas corren con cwd = plan3/ (donde estan los escenarios); lo pesado (tripinfo, CSV de evaluar) va a
plan3/tmp_esc/, que git ignora, y los resumenes a plan3/pruebas/esc/salidas/. Semillas solo de humo
(424301-424360; base 7 para entrenar). Como mucho 3 procesos de SUMO a la vez (MAX_SUMO).
"""
import os
import sys
import hashlib
import subprocess
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN3 = os.path.dirname(os.path.dirname(AQUI))
RAIZ = os.path.dirname(PLAN3)
TMP = os.path.join(PLAN3, "tmp_esc")
SALIDAS = os.path.join(AQUI, "salidas")
for _r in (RAIZ, PLAN3):
    if _r not in sys.path:
        sys.path.append(_r)
MAX_SUMO = 3
HUMO = range(424301, 424361)


def semilla_humo(s):
    assert s in HUMO, f"semilla {s} fuera del rango de humo 424301-424360"
    return s


def escenarios():
    import escenarios_plan3
    return list(escenarios_plan3.RECETAS)


def correr_sumo(cfg, semilla, tripinfo, extra=(), fin=6000):
    """sumo puro con cwd = plan3/, tripinfo completo (sin terminar y no insertados) y estadisticas al lado.
    Devuelve (ruta del tripinfo, ruta de las estadisticas, stderr)."""
    stats = tripinfo[:-4] + "_stats.xml"
    cmd = ["sumo", "-c", cfg, "--seed", str(semilla_humo(semilla)), "--tripinfo-output", tripinfo,
           "--tripinfo-output.write-unfinished", "true", "--tripinfo-output.write-undeparted", "true",
           "--no-step-log", "true", "--end", str(fin), "--statistic-output", stats] + list(extra)
    r = subprocess.run(cmd, cwd=PLAN3, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"sumo fallo ({cfg}, {semilla}): {r.stderr[-500:]}")
    return tripinfo, stats, r.stderr


def leer_viajes(ruta):
    """{id: {deseada, depart, dd, vtype, sf}} de un tripinfo; deseada = depart - departDelay (salida pedida). Los no
    insertados (write-undeparted) traen depart = -1: su deseada queda en None."""
    res = {}
    for v in ET.parse(ruta).getroot().iter("tripinfo"):
        dep, dd = float(v.get("depart")), float(v.get("departDelay", 0))
        res[v.get("id")] = {"deseada": round(dep - dd, 2) if dep >= 0 else None, "depart": dep, "dd": dd,
                            "vtype": v.get("vType"), "sf": v.get("speedFactor")}
    return res


def estadisticas(ruta):
    raiz = ET.parse(ruta).getroot()
    veh, tel = raiz.find("vehicles"), raiz.find("teleports")
    res = {k: int(veh.get(k)) for k in ("loaded", "inserted", "running", "waiting")}
    res["teleports"] = int(tel.get("total")) if tel is not None else 0
    return res


def comparar_llegadas(a, b):
    """Compara vehiculo por vehiculo dos {id: viaje}: ids, salida deseada, speedFactor y tipo."""
    comunes = set(a) & set(b)
    dif_t = sum(1 for k in comunes if a[k]["deseada"] != b[k]["deseada"])
    orden = sorted(a, key=lambda k: (a[k]["deseada"] is None, a[k]["deseada"] or 0, k)) == \
        sorted(b, key=lambda k: (b[k]["deseada"] is None, b[k]["deseada"] or 0, k))
    return {"n_a": len(a), "n_b": len(b), "solo_uno": len(set(a) ^ set(b)), "deseada_distinta": dif_t,
            "sf_distinto": sum(1 for k in comunes if a[k]["sf"] != b[k]["sf"]),
            "tipo_distinto": sum(1 for k in comunes if a[k]["vtype"] != b[k]["vtype"]), "mismo_orden": orden}


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def sha_plan2_rou():
    """{archivo: sha256} de los .rou.xml de plan2/ (solo lectura)."""
    plan2 = os.path.join(RAIZ, "plan2")
    return {n: sha256(os.path.join(plan2, n)) for n in sorted(os.listdir(plan2)) if n.endswith(".rou.xml")}


class Salida:
    """Lineas de un resumen que se imprimen y se guardan en salidas/<nombre>."""

    def __init__(self, nombre):
        self.ruta, self.lineas = os.path.join(SALIDAS, nombre), []

    def __call__(self, *partes):
        texto = " ".join(str(p) for p in partes)
        print(texto, flush=True)
        self.lineas.append(texto)

    def guardar(self):
        os.makedirs(SALIDAS, exist_ok=True)
        with open(self.ruta, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(self.lineas) + "\n")
