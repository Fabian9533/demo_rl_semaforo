"""
costo_escala.py - Costo de computo, costo en la calle y escala (Cap. IV, sec:ejecucion; Cap. V, sec:costo-escala).

Uso, desde demo_rl:
  python costo/costo_escala.py
Escribe costo/costo_escala.json e imprime un resumen. Solo lee archivos del repositorio; no corre SUMO.

Tres partes:
1. Computo medido. Horas de la cola del segundo estudio (plan3/cola/estado.json), horas de entrenamiento del
   modelo completo en el corredor de Benavides y en la malla con demanda alta (columna segundos de sus
   resultados_*.csv, que no incluye la validacion) y tiempo de una decision del actor de la politica citada del
   corredor de Benavides, en CPU con un hilo.
2. Estimacion de rentabilidad en el corredor de Benavides: valor del tiempo ahorrado por cruce y anio frente al
   costo anual de los sensores. Es una estimacion con los supuestos de SUPUESTOS, no una medicion.
3. Separacion entre cruces del corredor, para el criterio de agrupacion de la FHWA (Cap. V).
"""
import csv
import datetime
import glob
import json
import os
import statistics
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "costo", "costo_escala.json")
FMT = "%Y-%m-%d %H:%M:%S"

# ---------------- Supuestos de la estimacion (parte 2), cada uno con su fuente ----------------
SUPUESTOS = {
    # 2 h de punta por dia habil y 250 dias: la politica se entreno para la demanda de punta
    "horas_punta_anio": 500,
    # valor social del tiempo, S/ por pasajero-hora, Lima urbano (MEF, Anexo 11 de la Directiva 001-2019-EF/63.01,
    # secc. 2.8.2; fuente de la tabla: CIUP, 2012)
    "vst_privado": 7.83,
    "vst_publico": 6.50,
    # ocupacion del auto que usa el Banco Mundial (PAD P178842, Anexo 4, parr. 9); la moto, 1 (supuesto)
    "ocupacion_auto": 1.38,
    "ocupacion_moto": 1.0,
    # pasajeros por combi, micro y bus: valores ilustrativos, no medidos
    "ocupacion_publico": {"combi": 10, "micro": 20, "bus": 30},
    # soles por dolar (PAD P178842, nota 70, 2022)
    "soles_por_dolar": 3.857,
    # tasa social de descuento (MEF, Anexo 11; la misma del PAD) y vida util de los sensores (ODOT)
    "tasa": 0.08,
    "anios": 10,
    # costo de deteccion de un cruce en 10 anios (ODOT SPR 781, 2017, Tabla 8.7): costo inicial y valor presente
    # al 3 % de los costos anuales (mantenimiento y ajustes)
    "sensores": {"espiras": (20400, 0), "video-radar": (31520, 24880), "radar": (46520, 38949)},
    "tasa_odot": 0.03,
    # reajustar el plan fijo, USD por cruce: Boston (2010, Tabla 5) y FHWA (EDC-4, 2016)
    "reajuste_por_cruce": (1110, 4500),
}
CRUCES_BENAVIDES = 6
# demanda de cada nivel (veh/h): TESIS/secciones/tablas/resultado_final.tex
NIVELES = {"publicada": ("lima/corredor/salidas", 8706, "vecinos_completo_s42"),
           "alta": ("lima/corredor/alta/salidas", 10447, "vecinos_completo_s2042")}


def horas(segundos):
    return round(segundos / 3600, 2)


def suma_segundos(patron):
    """Horas de la columna segundos de cada CSV que cumple el patron: {archivo: horas}."""
    out = {}
    for ruta in sorted(glob.glob(os.path.join(RAIZ, patron))):
        with open(ruta, encoding="utf-8") as f:
            out[os.path.relpath(ruta, RAIZ)] = horas(sum(float(r["segundos"]) for r in csv.DictReader(f)))
    return out


def media_csv(ruta, columna="retraso_total_prom"):
    with open(os.path.join(RAIZ, ruta), encoding="utf-8") as f:
        return statistics.mean(float(r[columna]) for r in csv.DictReader(f))


def computo():
    """Parte 1: horas de la cola del segundo estudio, de los entrenamientos citados y de una decision."""
    est = json.load(open(os.path.join(RAIZ, "plan3", "cola", "estado.json"), encoding="utf-8"))
    tramos = sorted((datetime.datetime.strptime(r["inicio"], FMT), datetime.datetime.strptime(r["fin"], FMT))
                    for r in est["registro"].values() if r.get("inicio") and r.get("fin"))
    ocupado, (ini, fin) = datetime.timedelta(0), tramos[0]
    for a, b in tramos[1:]:
        if a > fin:
            ocupado += fin - ini
            ini, fin = a, b
        else:
            fin = max(fin, b)
    ocupado += fin - ini
    eventos = sorted([(a, 1) for a, _ in tramos] + [(b, -1) for _, b in tramos])
    n = maximo = 0
    for _, d in eventos:
        n += d
        maximo = max(maximo, n)
    # P6, modelo completo: cada entrenamiento esta partido en tramos t1, t2... de la cola (con la validacion)
    p6_cola = {}
    for clave, seg in est["tiempos"].items():
        if clave.startswith("e3_p3completopoi_poi_malla3_alta_s"):
            base = clave.split("_s")[-1].split("_t")[0]
            p6_cola[base] = p6_cola.get(base, 0) + seg
    return {
        "segundo_estudio": {"horas_proceso": horas(sum(est["tiempos"].values())),
                            "horas_reloj_cola_ocupada": horas(ocupado.total_seconds()),
                            "trabajos_a_la_vez_max": maximo},
        "benavides_publicada_h": suma_segundos("lima/corredor/resultados_benavides_ippo_vecinos_completo_s*.csv"),
        "benavides_alta_h": suma_segundos("lima/corredor/alta/resultados_benavides_ippo_vecinos_completo_s*.csv"),
        "p6_episodios_h": suma_segundos("plan3/resultados_poi_malla3_alta_ippo_vecinos_p3completopoi_s*.csv"),
        "p6_con_validacion_h": {b: horas(s) for b, s in sorted(p6_cola.items())},
        "decision": decision(),
    }


def decision():
    """Microsegundos de una decision del actor (lote 1, CPU, un hilo): mediana de 10 tandas de 1000 llamadas."""
    import torch
    import torch.nn as nn
    torch.set_num_threads(1)
    ruta = os.path.join(RAIZ, "lima", "corredor", "politica_benavides_vecinos_completo_s42.pt")
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
    return {"politica": os.path.relpath(ruta, RAIZ), "us_por_decision": round(us, 1), "paso_decision_s": paso,
            "cpu_s_por_hora_y_semaforo": round(3600 / paso * us / 1e6, 3), "parametros_actor": n_actor,
            "kb_actor_float32": round(n_actor * 4 / 1000, 1), "torch": torch.__version__}


def composicion():
    """Mezcla de vehiculos del escenario (plan3/demanda_estocastica.py)."""
    sys.path.insert(0, os.path.join(RAIZ, "plan3"))
    import demanda_estocastica as de
    return de.composicion()


def rentabilidad():
    """Parte 2: valor del tiempo ahorrado por cruce y anio en Benavides, frente al costo anual de los sensores."""
    s = SUPUESTOS
    p = composicion()
    privado = (p["auto"] * s["ocupacion_auto"] + p["moto"] * s["ocupacion_moto"]) * s["vst_privado"]
    publico = sum(p[k] * n for k, n in s["ocupacion_publico"].items()) * s["vst_publico"]
    valor = {"solo_autos_y_motos": privado, "con_transporte_publico": privado + publico}   # S/ por vehiculo-hora
    fra = s["tasa"] / (1 - (1 + s["tasa"]) ** -s["anios"])                        # recuperacion del capital
    fva = (1 - (1 + s["tasa_odot"]) ** -s["anios"]) / s["tasa_odot"]               # deshace el valor presente
    sensores = {k: round(ini * fra + vp / fva) for k, (ini, vp) in s["sensores"].items()}
    filas = []
    for nivel, (carpeta, veh, modelo) in NIVELES.items():
        r = {b: media_csv(f"{carpeta}/eval_t1_{b}.csv") for b in ("tipico", "fijo", "actuadoaj", modelo)}
        for a, b in ((modelo, "fijo"), (modelo, "actuadoaj"), ("fijo", "tipico")):
            ahorro_s = r[b] - r[a]
            veh_h = ahorro_s * veh / 3600 * s["horas_punta_anio"]
            usd = {k: round(veh_h * v / s["soles_por_dolar"] / CRUCES_BENAVIDES) for k, v in valor.items()}
            filas.append({"nivel": nivel, "control": a, "frente_a": b, "retraso_a": round(r[a], 2),
                          "retraso_b": round(r[b], 2), "ahorro_s_por_veh": round(ahorro_s, 2),
                          "veh_hora_anio": round(veh_h), "usd_por_cruce_anio": usd})
    return {"composicion_pct": {k: round(v * 100, 2) for k, v in p.items()},
            "soles_por_veh_hora": {k: round(v, 2) for k, v in valor.items()},
            "sensores_usd_por_cruce_anio": sensores, "comparaciones": filas,
            "supuestos": {k: v for k, v in s.items() if k != "sensores"}}


def separacion():
    """Parte 3: distancia entre cruces vecinos del corredor de Benavides (m)."""
    sys.path.insert(0, os.path.join(RAIZ, "lima", "corredor"))
    import corredor
    x = [c[2] for c in corredor.CRUCES]
    return [round(b - a) for a, b in zip(x, x[1:])]


if __name__ == "__main__":
    res = {"computo": computo(), "rentabilidad": rentabilidad(), "separacion_benavides_m": separacion()}
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))
    print("escrito", os.path.relpath(SALIDA, RAIZ))
