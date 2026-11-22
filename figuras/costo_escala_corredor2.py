"""
costo_escala_corredor2.py - costo/costo_escala.py del repo con el corredor del estudio 2 (corredor_estudio2/).

Uso:  python -B costo_escala_corredor2.py
Hace lo mismo que el original (computo, rentabilidad y separacion entre cruces), con dos cambios:
  - el corredor de Benavides se lee de corredor_estudio2/demo_rl (red corregida y verdes minimos de los peatones,
    enmienda del 19.11.2026 en lima/REGISTRO.md), con su demanda (7654 y 9185 veh/h) y sus modelos citados (la base
    con la validacion mediana, como corredor_estudio2/citado.py);
  - escribe figuras/salida/costo_escala_corredor2.json en esta entrega, no en el repo.
La cola del segundo estudio, P6 y la mezcla de vehiculos se leen del repo, como en el original. Los supuestos de la
estimacion (SUPUESTOS) son los del original, sin cambios. Si una demanda aun no tiene sus evaluaciones, se salta.
"""
import csv
import glob
import importlib.util
import json
import os
import statistics
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # el repositorio (este archivo esta en figuras/)
RAIZ = os.path.dirname(REPO)          # la carpeta que tiene el repositorio y las copias de los estudios (lima/estudios)
ORIG = os.path.join(REPO, "costo", "costo_escala.py")
COR2 = os.path.join(RAIZ, "corredor_estudio2", "demo_rl")
AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "salida", "costo_escala_corredor2.json")
_spec = importlib.util.spec_from_file_location("costo_escala_repo", ORIG)
ce = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ce)

# demanda de cada nivel (veh/h): corredor_estudio2/demo_rl/lima/corredor/corredor.py (flujos) y el factor 1.2 de la alta
NIVELES = {"publicada": ("lima/corredor", 7654), "alta": ("lima/corredor/alta", 9185)}


def citado(carpeta, nombre="vecinos_completo"):
    """El entrenamiento citado: la base con la validacion mediana (corredor_estudio2/citado.py). None si falta."""
    vals = []
    for base in (42, 2042, 4042):
        ruta = os.path.join(COR2, carpeta, f"politica_benavides_{nombre}_s{base}.json")
        if not os.path.exists(ruta):
            return None
        with open(ruta, encoding="utf-8") as f:
            vals.append((json.load(f)["val_elegido"], base))
    vals.sort()
    return f"{nombre}_s{vals[1][1]}"


def suma_segundos(patron):
    out = {}
    for ruta in sorted(glob.glob(os.path.join(COR2, patron))):
        with open(ruta, encoding="utf-8") as f:
            out[os.path.relpath(ruta, COR2).replace("\\", "/")] = ce.horas(
                sum(float(r["segundos"]) for r in csv.DictReader(f)))
    return out


def decision():
    """Como ce.decision(), con la politica citada del corredor del estudio 2 con la demanda publicada."""
    import torch
    import torch.nn as nn
    torch.set_num_threads(1)
    ruta = os.path.join(COR2, "lima", "corredor", f"politica_benavides_{citado('lima/corredor')}.pt")
    meta = json.load(open(ruta.replace(".pt", ".json"), encoding="utf-8"))
    sd = torch.load(ruta, weights_only=True, map_location="cpu")
    d, o = meta["dim_obs"], meta["ocultas"]
    actor = nn.Sequential(nn.Linear(d, o), nn.Tanh(), nn.Linear(o, o), nn.Tanh(), nn.Linear(o, 2))
    actor.load_state_dict({k[len("actor."):]: v for k, v in sd.items() if k.startswith("actor.")})
    obs = torch.rand(1, d, generator=torch.Generator().manual_seed(0))
    tandas = []
    with torch.no_grad():
        for _ in range(1000):
            actor(obs).argmax(dim=1)
        for _ in range(10):
            t0 = time.perf_counter_ns()
            for _ in range(1000):
                actor(obs).argmax(dim=1)
            tandas.append((time.perf_counter_ns() - t0) / 1000 / 1000)
    us = statistics.median(tandas)
    paso = meta.get("opciones", {}).get("paso_decision", 5)
    n_actor = sum(v.numel() for k, v in sd.items() if k.startswith("actor."))
    return {"politica": os.path.relpath(ruta, COR2).replace("\\", "/"), "us_por_decision": round(us, 1),
            "paso_decision_s": paso, "cpu_s_por_hora_y_semaforo": round(3600 / paso * us / 1e6, 3),
            "parametros_actor": n_actor, "kb_actor_float32": round(n_actor * 4 / 1000, 1), "torch": torch.__version__}


def computo():
    c = ce.computo()          # cola del segundo estudio y P6, del repo; el corredor y la decision se reemplazan
    c["benavides_publicada_h"] = suma_segundos("lima/corredor/resultados_benavides_ippo_vecinos_completo_s*.csv")
    c["benavides_alta_h"] = suma_segundos("lima/corredor/alta/resultados_benavides_ippo_vecinos_completo_s*.csv")
    c["decision"] = decision()
    return c


def media_csv(ruta, columna="retraso_total_prom"):
    with open(ruta, encoding="utf-8") as f:
        return statistics.mean(float(r[columna]) for r in csv.DictReader(f))


def rentabilidad():
    """Como ce.rentabilidad(), con el corredor del estudio 2 y su demanda."""
    s = ce.SUPUESTOS
    p = ce.composicion()
    privado = (p["auto"] * s["ocupacion_auto"] + p["moto"] * s["ocupacion_moto"]) * s["vst_privado"]
    publico = sum(p[k] * n for k, n in s["ocupacion_publico"].items()) * s["vst_publico"]
    valor = {"solo_autos_y_motos": privado, "con_transporte_publico": privado + publico}   # S/ por vehiculo-hora
    fra = s["tasa"] / (1 - (1 + s["tasa"]) ** -s["anios"])
    fva = (1 - (1 + s["tasa_odot"]) ** -s["anios"]) / s["tasa_odot"]
    sensores = {k: round(ini * fra + vp / fva) for k, (ini, vp) in s["sensores"].items()}
    filas, modelos = [], {}
    for nivel, (carpeta, veh) in NIVELES.items():
        modelo = citado(carpeta)
        rutas = {b: os.path.join(COR2, carpeta, "salidas", f"eval_t1_{b}.csv")
                 for b in ("tipico", "fijo", "actuadoaj", modelo or "")}
        if modelo is None or not all(os.path.exists(r) for r in rutas.values()):
            print(f"{nivel}: faltan evaluaciones, se salta")
            continue
        modelos[nivel] = modelo
        r = {b: media_csv(ruta) for b, ruta in rutas.items()}
        for a, b in ((modelo, "fijo"), (modelo, "actuadoaj"), ("fijo", "tipico")):
            ahorro_s = r[b] - r[a]
            veh_h = ahorro_s * veh / 3600 * s["horas_punta_anio"]
            usd = {k: round(veh_h * v / s["soles_por_dolar"] / ce.CRUCES_BENAVIDES) for k, v in valor.items()}
            filas.append({"nivel": nivel, "control": a, "frente_a": b, "retraso_a": round(r[a], 2),
                          "retraso_b": round(r[b], 2), "ahorro_s_por_veh": round(ahorro_s, 2),
                          "veh_hora_anio": round(veh_h), "usd_por_cruce_anio": usd})
    return {"modelos_citados": modelos, "composicion_pct": {k: round(v * 100, 2) for k, v in p.items()},
            "soles_por_veh_hora": {k: round(v, 2) for k, v in valor.items()},
            "sensores_usd_por_cruce_anio": sensores, "comparaciones": filas,
            "supuestos": {k: v for k, v in s.items() if k != "sensores"}}


def separacion():
    sys.path.insert(0, os.path.join(COR2, "lima", "corredor"))
    import corredor
    x = [c[2] for c in corredor.CRUCES]
    return [round(b - a) for a, b in zip(x, x[1:])]


if __name__ == "__main__":
    res = {"computo": computo(), "rentabilidad": rentabilidad(), "separacion_benavides_m": separacion()}
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))
    print("escrito", SALIDA)
