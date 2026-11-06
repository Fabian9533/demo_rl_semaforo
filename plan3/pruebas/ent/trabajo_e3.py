"""
trabajo_e3.py - Una medicion de las pruebas de las Etapas 3 y 4 (prueba_etapa3.py y prueba_etapa4.py), en un
proceso aparte: importa rl_ippo.py de la raiz, corre lo pedido en la carpeta actual (con copias de los escenarios)
y escribe un JSON. Informe: plan3/doc/informe_ent2.md.

Uso:  python trabajo_e3.py <tarea> <parametros.json> <salida.json>
Tareas:
  episodio    un episodio "demo" con un decisor externo (una politica de dimension igual o menor, ciclo minimo,
              mantener o al azar) y las opciones pedidas; devuelve las metricas, los segundos, los viajes del
              tripinfo y, si se piden, las marcas de giro por acceso, la duracion de cada verde y la recompensa de
              las transiciones.
  intervalos  un episodio de entrenamiento (politica nueva, --v2) con --sin-forzadas y el reloj pedido: los
              intervalos entre decisiones del lote.
  recompensa  el mismo episodio (decisor "mantener") con el reloj de 5 s y con el de 2 s.
  colas       el mismo episodio (ciclo minimo, --obs-cercana 75) sin y con configurar_colas_cero.
  escala      corredor con --scale 0.5 frente a dem_corredor_t905 (ciclo minimo), y corredor con 1 y 1.5.
"""
import sys
import json
import time
import random
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))

import numpy as np  # noqa: E402
import torch  # noqa: E402
import rl_ippo as ri  # noqa: E402


def configurar(p):
    ri.preparar(p["escenario"])
    ri.configurar_obs_cercana(p.get("obs_cercana", 0.0))
    ri.C["paso_decision"] = int(p.get("paso", ri.PASO_CONTROL))
    ri.C["msg_paso"] = bool(p.get("msg_paso", False))
    ri.configurar_colas_cero(p.get("colas_cero", False))


def decisor(p, registro):
    """decidir(deciden, obs, mascara, modo, info) segun p["decisor"]; anota en registro lo que se pide."""
    d = p["decisor"]
    if d["tipo"] == "politica":
        pol, meta = ri.Politica.cargar(d["ruta"])
        dim = meta["dim_obs"]
    azar = random.Random(d.get("semilla", 0))
    marcas = p.get("marcas", [])

    def espera_completa(tls, k):
        """La espera del primero del acceso k leida en todos los carriles (como el prototipo, sin saltar los de zona
        vacia), normalizada como en rl_ippo.entradas_cercanas."""
        espera = 0.0
        for l in ri.C["carriles_aprox"][ri.C["semaforos"][tls][k]]:
            ids = ri.traci.lane.getLastStepVehicleIDs(l)
            if ids:
                espera = max(espera, ri.traci.vehicle.getWaitingTime(ids[-1]))
        return np.float32(min(1.0, espera / ri.CERCA_MAX_ESPERA))

    def decidir(deciden, obs, masc, modo, info):
        t = info["t"]
        if p.get("verificar_espera"):       # la lectura corta (zona vacia: 0, sin leer) frente a la completa
            base = ri.C["dim_obs"] - ri.C["n_cerca"]
            for j, tls in enumerate(deciden):
                for k in range(4):
                    registro["espera_lecturas"] = registro.get("espera_lecturas", 0) + 1
                    if obs[j, base + 4 * k + 2] != espera_completa(tls, k):
                        registro["espera_distintas"] = registro.get("espera_distintas", 0) + 1
        for tls, acceso in marcas:          # marca giro_izq del acceso, en las decisiones con verde para el
            if tls in deciden:
                k = deciden.index(tls)
                ia = ri.C["semaforos"][tls].index(acceso)
                verde = int(np.argmax(obs[k, 8:10]))
                if (verde == ri.C["fase_av"][tls]) == (ia < 2):            # avenida: accesos oeste y este
                    giro = float(obs[k, ri.C["dim_obs"] - ri.C["n_cerca"] + 4 * ia + 3])
                    registro.setdefault(f"{tls}|{acceso}", []).append([t, giro])
        if p.get("guardar_obs"):
            for k, tls in enumerate(deciden):
                registro.setdefault("obs", []).append([t, tls] + [float(x) for x in obs[k]])
        if d["tipo"] == "politica":
            with torch.no_grad():
                logits, _ = pol(torch.from_numpy(np.ascontiguousarray(obs[:, :dim])))
                logits = ri.Politica.enmascarar(logits, torch.from_numpy(masc))
                acciones = [int(a) for a in logits.argmax(dim=1)]
        elif d["tipo"] == "ciclo":          # ciclo minimo: cambia en cuanto puede
            acciones = [1 if m[1] > 0 else 0 for m in masc]
        elif d["tipo"] == "mantener":       # no cambia nunca por gusto (solo al verde maximo)
            acciones = [0 if m[0] > 0 else 1 for m in masc]
        else:                               # al azar entre las acciones legales
            acciones = [(1 if azar.random() < d["p"] else 0) if m.sum() > 1 else int(m[1] > 0) for m in masc]
        if p.get("registrar_verdes"):       # duracion del verde que termina: t_verde al decidir cambiar
            for k, a in enumerate(acciones):
                if a == 1:
                    registro.setdefault("verdes", []).append(int(round(float(obs[k, 10]) * ri.VERDE_MAX)))
        return acciones, [None] * len(deciden)
    return decidir


def viajes(tripinfo):
    """id -> [depart, arrival, timeLoss] de cada vehiculo del tripinfo (para comparar dos corridas)."""
    raiz = ET.parse(tripinfo).getroot()
    return {v.get("id"): [v.get("depart"), v.get("arrival"), v.get("timeLoss")] for v in raiz.iter("tripinfo")}


def marca_por_segundo(p, registro):
    """La marca giro_izq medida como bloqueo.md: en cada segundo con el verde del acceso, si hay alguien detenido en
    el primer tramo interno de su giro a la izquierda. Envuelve rl_ippo.lecturas (se llama despues de cada paso) y
    suma por acceso [segundos de verde, con marca] en el periodo 1 (t <= 1800) y en el 2 (1800 < t <= 3600)."""
    leer_original = ri.lecturas
    verdes = {}

    def lecturas():
        lect = leer_original()
        if not verdes:
            verdes.update({tls: ri.rc.fases_verdes(tls)[0] for tls in ri.C["semaforos"]})
        t = ri.traci.simulation.getTime()
        if t > 3600:
            return lect
        vias = ri.traci.lane.getAllSubscriptionResults()
        for tls, acceso in p.get("marcas", []):
            ia = ri.C["semaforos"][tls].index(acceso)
            av = ri.C["fase_av"][tls]
            if ri.traci.trafficlight.getPhase(tls) == verdes[tls][av if ia < 2 else 1 - av]:
                giro = any(vias.get(ri.C["via_izq"][l], {}).get(ri.HALT, 0) > 0
                           for l in ri.C["carriles_aprox"][acceso] if l in ri.C["via_izq"])
                c = registro.setdefault(f"seg|{tls}|{acceso}", [0, 0, 0, 0])
                c[0 if t <= 1800 else 2] += 1
                c[1 if t <= 1800 else 3] += int(giro)
        return lect
    ri.lecturas = lecturas


def episodio(p):
    configurar(p)
    registro, rec = {}, {"r": 0.0, "n": 0}
    if p.get("marca_por_segundo"):
        marca_por_segundo(p, registro)

    def transicion(tls, obs, a, r, obs_sig, masc_sig, info):
        rec["r"] += r / ri.ESCALA_R * ri.PASO_CONTROL       # recompensa del intervalo, en retraso-segundos
        rec["n"] += 1
    t0 = time.perf_counter()
    res = ri.correr_episodio("demo", None, False, 0, p["semilla"], tripinfo="tripinfo_e3.xml",
                             variante=p.get("variante", "vecinos"), decidir=decisor(p, registro),
                             transicion=transicion if p.get("transiciones") else None, escala=p.get("escala"))
    return {"res": res, "segundos": round(time.perf_counter() - t0, 3), "registro": registro,
            "recompensa_segundos": rec["r"], "transiciones": rec["n"], "dim_obs": ri.C["dim_obs"],
            "features": ri.nombres_features(), "viajes": viajes("tripinfo_e3.xml")}


def intervalos(p):
    """Un episodio de entrenamiento con --v2 y --sin-forzadas (y el reloj pedido) con una politica nueva."""
    configurar(p)
    ri.C["sin_forzadas"] = bool(p.get("sin_forzadas", True))
    torch.manual_seed(7)
    torch.set_num_threads(1)
    pol = ri.Politica(ri.C["dim_obs"])
    buffer = {}
    res = ri.correr_episodio("train", pol, False, 0, p["semilla"], tripinfo="tripinfo_e3.xml", buffer=buffer,
                             v2=True)
    dts, cierres = {}, {}
    for tls, b in buffer.items():
        if b["recompensa"]:
            dt = [int(x) for x in ri.intervalos(b)]
            for x in dt[:-1]:
                dts[x] = dts.get(x, 0) + 1
            cierres[tls] = dt[-1]
    return {"res": res, "intervalos": {str(k): v for k, v in sorted(dts.items())}, "cierres": cierres}


def recompensa(p):
    """El mismo episodio (decisor mantener) con el reloj de 5 s y con el de 2 s."""
    salida = {}
    for k in (ri.PASO_CONTROL, 2):
        r = episodio({**p, "paso": k, "transiciones": True, "decisor": {"tipo": "mantener"}})
        salida[str(k)] = {"recompensa_segundos": r["recompensa_segundos"], "transiciones": r["transiciones"],
                          "ret_retraso": r["res"]["ret_retraso"], "timeloss": r["res"]["timeloss_prom"],
                          "cambios": r["res"]["cambios_fase"], "viajes": r["viajes"]}
    return salida


def colas(p):
    """Ciclo minimo con --obs-cercana 75, sin y con colas en cero: observaciones en cada decision."""
    salida = {}
    for cero in (False, True):
        r = episodio({**p, "colas_cero": cero, "guardar_obs": True, "decisor": {"tipo": "ciclo"}})
        salida["con" if cero else "sin"] = {"obs": r["registro"]["obs"], "res": r["res"]}
        salida["features"] = r["features"]
    ri.configurar_colas_cero(False)
    return salida


def costo(p):
    """Costo de --obs-cercana con menos ruido: el mismo episodio sin y con, alternados en este proceso (sin, con, con,
    sin, ...), p["repeticiones"] veces cada uno; devuelve los segundos y la mediana de las razones por pareja."""
    sin, con = [], []
    for k in range(p.get("repeticiones", 3)):
        orden = (0.0, p["obs_cercana"]) if k % 2 == 0 else (p["obs_cercana"], 0.0)
        for largo in orden:
            r = episodio({**p, "obs_cercana": largo})
            (con if largo else sin).append(r["segundos"])
    razones = [c / s for c, s in zip(con, sin)]
    return {"sin": sin, "con": con, "razones": razones, "mediana": float(np.median(razones))}


def escala(p):
    """corredor con --scale 0.5 frente a dem_corredor_t905 (ciclo minimo, misma semilla); corredor con 1 y 1.5."""
    salida = {}
    for nombre, esc, f in (("corredor_x0.5", "corredor", 0.5), ("t905", "dem_corredor_t905", None),
                           ("corredor_x1", "corredor", 1.0), ("corredor_x1.5", "corredor", 1.5),
                           ("corredor", "corredor", None)):
        r = episodio({**p, "escenario": esc, "escala": f, "decisor": {"tipo": "ciclo"}})
        salida[nombre] = {"res": r["res"], "viajes": r["viajes"]}
    return salida


if __name__ == "__main__":
    tarea, entrada, archivo = sys.argv[1:4]
    with open(entrada, encoding="utf-8") as f:
        parametros = json.load(f)
    resultado = {"episodio": episodio, "intervalos": intervalos, "recompensa": recompensa, "colas": colas,
                 "escala": escala, "costo": costo}[tarea](parametros)
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False)
