"""Copia sin cambios del guion del revisor R2 (revision del 05.11; la usa prueba_revision_e34.py, punto e).
Revisor R2: verificacion independiente de la Etapa 3 de rl_ippo.py (reloj, forzadas, recompensa, descuento,
mensajes y observacion cercana) en un episodio de entrenamiento con politica nueva.
Uso: python verif_e3.py <raiz_rl_ippo> <config.json> <salida.json>   (cwd = carpeta con los escenarios)
"""
import sys
import json
import time

raiz, archivo_cfg, archivo_out = sys.argv[1:4]
sys.path.insert(0, raiz)
sys.dont_write_bytecode = True

import numpy as np  # noqa: E402
import torch  # noqa: E402
import rl_ippo as ri  # noqa: E402

cfg = json.load(open(archivo_cfg, encoding="utf-8"))
esc = cfg["escenario"]
K = int(cfg.get("paso", 5))
ri.preparar(esc)
ri.configurar_obs_cercana(cfg.get("obs", 0.0))
ri.C["paso_decision"] = K
ri.C["msg_paso"] = bool(cfg.get("msg", False))
ri.C["sin_forzadas"] = bool(cfg.get("sin_forzadas", False))
ri.C["vnorm"] = ri.NormValor() if cfg.get("norm") else None

reg = {"obs": [], "fases": [], "pub": [], "r": {}, "cerca": {"n": 0, "dif": {}, "ejemplos": [], "giro1": 0,
                                                             "e2_vs_pos": 0, "espera_lejos": 0}}
verdes_tls = {}

# --- envolturas (solo lecturas: no cambian la simulacion) ---
_observar = ri.observar


def observar(tls, ag, lect, canal, t, con_vecinos):
    o = _observar(tls, ag, lect, canal, t, con_vecinos)
    reg["obs"].append([t, tls, ag["t_verde"], ag["verde"], ri.minimo_verde(ag), list(ri.mascara(ag))])
    return o


ri.observar = observar
_fases = ri.fases_actuales


def fases_actuales():
    f = _fases()
    if not verdes_tls:
        for tls in ri.C["semaforos"]:
            v, amb, dur, vmin = ri.rc.fases_verdes(tls)
            verdes_tls[tls] = {"verdes": v, "ambar": amb, "dur": dur, "vmin": vmin}
    reg["fases"].append([ri.traci.simulation.getTime(), f])
    return f


ri.fases_actuales = fases_actuales
_publicar = ri.Canal.publicar


def publicar(self, emisor, receptor, t, msg):
    reg["pub"].append(t)
    return _publicar(self, emisor, receptor, t, msg)


ri.Canal.publicar = publicar
_rpaso = ri.recompensa_paso


def recompensa_paso(tls, lect):
    r = _rpaso(tls, lect)
    reg["r"].setdefault(tls, []).append([ri.traci.simulation.getTime(), r])
    return r


ri.recompensa_paso = recompensa_paso
_cerca = ri.entradas_cercanas
via_traci = {}


def entradas_cercanas(tls):
    res = _cerca(tls)
    tr = ri.traci
    c = reg["cerca"]
    c["n"] += 1
    largo = ri.C["obs_cerca"]
    indep = np.zeros_like(res)
    for k, a in enumerate(ri.C["semaforos"][tls]):
        carriles = [f"{a}_{i}" for i in range(tr.edge.getLaneNumber(a))]
        det = mov = 0
        espera = 0.0
        giro = 0.0
        for l in carriles:
            n = tr.lanearea.getLastStepVehicleNumber(f"e2_{l}")
            h = tr.lanearea.getLastStepHaltingNumber(f"e2_{l}")
            det += h
            mov += max(0, n - h)
            vs = tr.lane.getLastStepVehicleIDs(l)
            lg = tr.lane.getLength(l)
            if vs:
                pos = {v: tr.vehicle.getLanePosition(v) for v in vs}
                primero = max(vs, key=lambda v: pos[v])
                w = tr.vehicle.getWaitingTime(primero)
                cerca_n = sum(1 for v in vs if lg - pos[v] < largo + tr.vehicle.getLength(v))
                if cerca_n != n:
                    c["e2_vs_pos"] += 1
                if n == 0 and w > 0:
                    c["espera_lejos"] += 1
                espera = max(espera, w)
            if l not in via_traci:
                via_traci[l] = [lk[4] for lk in tr.lane.getLinks(l, True) if lk[6] in ("l", "L") and lk[4]]
            for via in via_traci[l]:
                if tr.lane.getLastStepHaltingNumber(via) > 0:
                    giro = 1.0
        plazas = len(carriles) * max(1.0, largo / 7.5)
        indep[4 * k: 4 * k + 4] = [min(1.0, det / plazas), min(1.0, mov / plazas), min(1.0, espera / 120.0), giro]
    for r, lado in enumerate(ri.C["lados"]):
        vec = ri.C["vecinos"][tls].get(lado)
        if vec is not None:
            e = vec[2]
            hmax = max(tr.lane.getLastStepHaltingNumber(f"{e}_{i}") for i in range(tr.edge.getLaneNumber(e)))
            indep[16 + r] = min(1.0, hmax / ri.C["plazas"][e])
    dif = np.abs(indep - res) > 1e-6
    if dif.any():
        nombres = ri.nombres_features()[-ri.C["n_cerca"]:]
        for k in np.flatnonzero(dif):
            c["dif"][nombres[k]] = c["dif"].get(nombres[k], 0) + 1
        if len(c["ejemplos"]) < 6:
            c["ejemplos"].append([tr.simulation.getTime(), tls, [float(x) for x in res], [float(x) for x in indep]])
    c["giro1"] += int(any(res[3::4][:4] > 0))
    return res


ri.entradas_cercanas = entradas_cercanas

torch.manual_seed(7)
torch.set_num_threads(1)
pol = ri.Politica(ri.C["dim_obs"])
buffer = {}
t0 = time.perf_counter()
res = ri.correr_episodio("train", pol, False, 0, cfg.get("semilla", 424301), tripinfo="tripinfo_r2.xml",
                         buffer=buffer, v2=True)
seg_ep = time.perf_counter() - t0
lote = ri.gae(buffer, ri.HIPER["gamma"], ri.HIPER["lam"], smdp=True)

out = {"config": cfg, "dim_obs": ri.C["dim_obs"], "segundos_episodio": round(seg_ep, 2),
       "res": {k: res.get(k) for k in ("timeloss_prom", "cambios_fase", "decisiones", "decisiones_libres",
                                      "frac_forzadas", "msg_edad", "ret_retraso")},
       "vmin": {t: sorted(set(v["vmin"].values())) for t, v in verdes_tls.items()},
       "dur_ambar_cfg": {t: sorted(set(v["dur"].values())) for t, v in verdes_tls.items()}}
problemas = []

# 1) reloj: t_verde de cada decision y mascara
t_final = max(b["t_final"] for b in buffer.values())
dec = [d for d in reg["obs"] if d[0] != t_final]
malas_reloj, malas_masc = [], []
for t, tls, tv, verde, m, masc in dec:
    if tv == 0:
        ok = t == 0
    elif K == 5:
        ok = tv % 5 == 0
    else:
        ok = (tv % K == 0) if tv < m else ((tv - m) % K == 0 or tv == ri.VERDE_MAX)
    if not ok:
        malas_reloj.append([t, tls, tv])
    esperada = [1.0, 0.0] if tv < m else ([0.0, 1.0] if tv >= ri.VERDE_MAX else [1.0, 1.0])
    if masc != esperada:
        malas_masc.append([t, tls, tv, masc])
out["decisiones_t_verde"] = sorted({d[2] for d in dec})
out["reloj_mal"] = malas_reloj[:5]
out["mascara_mal"] = malas_masc[:5]
if malas_reloj or malas_masc:
    problemas.append("reloj o mascara")

# 2) fases: duracion de verdes y ambares (y que en cada verde se decidio en todos los t_verde esperados)
dur_verdes, dur_ambar = {}, {}
dec_por = {}
for t, tls, tv, verde, m, masc in dec:
    dec_por.setdefault(tls, []).append((t, tv))
faltan = []
for tls in ri.C["semaforos"]:
    v = verdes_tls[tls]
    seq = [(t, f[tls]) for t, f in reg["fases"]]
    # tramos de fase constante
    tramos = []
    ini, fase = seq[0][0], seq[0][1]
    for t, f in seq[1:]:
        if f != fase:
            tramos.append((fase, ini, t))
            ini, fase = t, f
    tramos.append((fase, ini, None))
    for fase, a, b in tramos[1:-1]:          # sin el primero (arranque) ni el ultimo (sin terminar)
        d = int(b - a)
        if fase in v["verdes"]:
            dur_verdes[d] = dur_verdes.get(d, 0) + 1
        else:
            dur_ambar[d] = dur_ambar.get(d, 0) + 1
    # en cada verde completo, las decisiones (t_verde) deben ser exactamente las del reloj hasta su fin
    tv_de_t = {t: tv for t, tv in dec_por.get(tls, [])}
    for fase, a, b in tramos[1:-1]:
        if fase not in v["verdes"]:
            continue
        G = int(b - a)
        m = v["vmin"][fase]
        if K == 5:
            esperadas = [x for x in range(5, G + 1) if x % 5 == 0]
        else:
            esperadas = [x for x in range(1, G + 1) if (x < m and x % K == 0) or
                         (x >= m and ((x - m) % K == 0 or x == ri.VERDE_MAX))]
        # el verde se pone al final del paso a - 1 (t_verde = 0 en pasos = a - 1) y se registra desde a: la
        # decision con t_verde = x ocurre con pasos = a - 1 + x
        vistas = [tv_de_t.get(int(a) - 1 + x) for x in esperadas]
        if vistas != esperadas:
            faltan.append([tls, a, G, esperadas[:8], vistas[:8]])
out["verdes"] = dict(sorted(dur_verdes.items()))
out["ambares"] = dict(sorted(dur_ambar.items()))
out["verdes_con_decisiones_faltantes"] = faltan[:4]
out["n_verdes_mal"] = len(faltan)
if faltan or set(dur_ambar) - {3}:
    problemas.append("verdes/ambares")

# 3) mensajes
pubs = sorted(set(reg["pub"]))
if ri.C["msg_paso"]:
    ok = pubs == list(range(1, pubs[-1] + 1))
else:
    ok = all(t % K == 0 for t in pubs) and pubs == list(range(K, pubs[-1] + 1, K))
out["mensajes"] = {"primeros": pubs[:6], "ultimo": pubs[-1] if pubs else None, "ok": ok}
if not ok:
    problemas.append("mensajes")

# 4) recompensa por intervalo, lote y descuento
dif_r, n_r, malas_lote, intervalos = 0.0, 0, 0, {}
for tls, b in buffer.items():
    n = len(b["recompensa"])
    rs = reg["r"][tls]
    ts = b["t"][:n] + [b["t_final"]]
    for i in range(n):
        s = sum(r for t, r in rs if ts[i] < t <= ts[i + 1])
        esperado = s / 5 * ri.ESCALA_R
        dif_r = max(dif_r, abs(esperado - b["recompensa"][i]))
        n_r += 1
        dt = ts[i + 1] - ts[i]
        intervalos[dt] = intervalos.get(dt, 0) + 1
    if ri.C["sin_forzadas"]:
        malas_lote += sum(1 for mk in b["mascara"] if float(np.sum(mk)) != 2.0)
out["recompensa_max_dif"] = dif_r
out["recompensas"] = n_r
out["intervalos_lote"] = dict(sorted(intervalos.items()))
out["forzadas_en_lote"] = malas_lote
if dif_r > 1e-9 or malas_lote:
    problemas.append("recompensa o lote")
# GAE con gamma^(dt/5)
g, lam = ri.HIPER["gamma"], ri.HIPER["lam"]
ret_mio = []
for tls, b in buffer.items():
    n = len(b["recompensa"])
    if n == 0:
        continue
    vals = b["valor"] + [b["v_final"]]
    ts = b["t"][:n] + [b["t_final"]]
    A = np.zeros(n)
    ult = 0.0
    for i in reversed(range(n)):
        e = (ts[i + 1] - ts[i]) / 5.0
        delta = b["recompensa"][i] + g ** e * vals[i + 1] - vals[i]
        ult = delta + (g * lam) ** e * ult
        A[i] = ult
    ret_mio.extend(list(A + np.array(b["valor"][:n])))
out["gae_max_dif_retorno"] = float(np.max(np.abs(np.array(ret_mio, dtype=np.float32) - lote[5].numpy())))
if out["gae_max_dif_retorno"] > 1e-4:
    problemas.append("gae")

# 5) observacion cercana
if ri.C["obs_cerca"]:
    out["cerca"] = reg["cerca"]
    out["via_izq_rl_ippo"] = ri.C["via_izq"]
    out["via_izq_traci"] = {l: v for l, v in via_traci.items() if v}
    if reg["cerca"]["dif"]:
        problemas.append("observacion cercana")
    out["features"] = ri.nombres_features()[-ri.C["n_cerca"]:]
out["problemas"] = problemas
json.dump(out, open(archivo_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ("dim_obs", "segundos_episodio", "decisiones_t_verde", "verdes", "ambares",
                                      "mensajes", "recompensa_max_dif", "intervalos_lote", "forzadas_en_lote",
                                      "gae_max_dif_retorno", "problemas", "res", "vmin", "n_verdes_mal")},
                 ensure_ascii=False))
if ri.C["obs_cerca"]:
    print("cerca:", json.dumps({k: v for k, v in reg["cerca"].items() if k != "ejemplos"}),
          "ejemplos:", reg["cerca"]["ejemplos"][:2])
