"""
evaluar.py - Evaluacion final de un escenario con politica congelada y varias semillas.

Modo del plan de pruebas v2 (un brazo por llamada, escribe un CSV parcial; ver plan2/ESPEC.md):
  python ../evaluar.py --escenario E --brazo fijo --semillas 1001-1030 --salida parciales/eval_E_fijo.csv
  (igual con --brazo actuado y --salida parciales/eval_E_actuado.csv)
  python ../evaluar.py --escenario E --politica q_table_<tag>.json --semillas 1001-1030 --salida ...
  python ../evaluar.py --escenario E --politica politica_<esc>_<var>_s<base>.pt --semillas ... --salida ...

  El tipo de politica se decide por la extension y el meta:
    .json  Q-tables (rl_corredor, o rl_semaforo en cruce/cruce2) con epsilon 0. Si existe
           q_table_<tag>.meta.json el brazo es <alg>_s<base> (alg = ql, sarsa, ql_colas...
           segun meta["algoritmo"] y meta["recompensa"]); sin meta es una Q-table vieja del
           06.09 y el brazo se llama "rl", como en las evaluaciones anteriores.
    .pt    se lee el meta <archivo>.json: "algoritmo" ausente o "ippo" -> rl_ippo con su
           variante (brazo ippo_<variante>_s<base>); "dqn" -> rl_dqn (dqn_s<base>);
           "mappo" -> rl_mappo (mappo_s<base>). rl_dqn y rl_mappo se importan solo si hacen falta.
  Filas de salida: brazo, modelo, base, semilla, las METRICAS de siempre, los tres retornos
  medidos cada segundo (ret_retraso, ret_colas, ret_spill; vacios si el modulo del control aun
  no los devuelve) y vehiculos, recompensa y decisiones. El CSV se escribe en <salida>.tmp y se
  renombra al terminar, asi consolidar.py nunca lee un parcial a medias. Por defecto --semillas
  es 1001-1030 y --salida es parciales/eval_<esc>_<brazo>.csv.
  El tripinfo de cada corrida es unico (tripinfo_eval_<esc>_<brazo>_<pid>.xml, para que varias
  evaluaciones puedan correr en paralelo en la misma carpeta): el de la primera semilla se conserva
  y da vehiculos_<esc>_<brazo>.csv; los de las demas semillas se borran tras leerlos. De la primera
  semilla tambien quedan serie_<esc>_<brazo>_s<semilla>.csv y fases_<esc>_<brazo>_s<semilla>.csv.

Modo antiguo (06.09.2026, se conserva sin cambios; escribe evaluacion_<esc>.csv y el resumen):
  python evaluar.py --escenario cruce [--semillas 1001-1010] [--brazos baseline,actuado,demo]
  python evaluar.py --escenario red --ippo politica_red_local_s42.pt,politica_red_vecinos_s42.pt
  python evaluar.py --escenario red --brazos "" --ippo politica_red_vecinos_s42.pt --latencia 5 --perdida 0.3

Corre los controles pedidos con las MISMAS semillas, fuera del rango que uso el entrenamiento:
tiempo fijo tuneado (baseline), actuado nativo de SUMO, agente Q-learning con epsilon 0 (demo)
y las politicas IPPO de U4 (--ippo, una o varias). Escribe:
  evaluacion_<esc>.csv          una fila por (brazo, semilla); las filas de brazos que no se
                                corren en esta llamada se conservan del archivo anterior
  evaluacion_<esc>_resumen.csv  por brazo y metrica: n, media, sd, IC95 %, y frente al fijo
                                delta % con IC95 % bootstrap, p de Wilcoxon pareado, p de
                                Mann-Whitney y delta de Cliff; los brazos IPPO llevan ademas
                                el delta frente al actuado y frente al Q-learning
  vehiculos_<esc>_<brazo>.csv   una fila por vehiculo de la primera semilla (distribuciones)
  serie_<esc>_<brazo>_s<semilla>.csv y fases_<esc>_<brazo>_s<semilla>.csv, primera semilla
En el modo antiguo --semillas vale 1001-1010 por defecto, como antes.

Cambios del plan v2 (24.09.2026): modo --brazo/--politica/--salida con CSV parcial por brazo
(la estadistica pasa a consolidar.py), carga por tipo de politica y meta, nombres de brazo
<alg>_s<base>, columnas modelo/base/ret_*, tripinfo unico por proceso, escenarios del plan v2
(los de rl_corredor.ESCENARIOS, que incluye escenarios_plan2).
"""
import os
import csv
import copy
import json
import time
import random
import argparse
import statistics

import numpy as np
from scipy import stats

import comun
import rl_corredor

METRICAS = ["timeloss_prom", "espera_prom", "cola_prom", "cola_max", "paradas_prom",
            "throughput", "co2_prom", "nox_prom", "recompensa_decision", "cambios_fase",
            "no_terminados",
            # solo en escenarios de varios cruces (corredor, red): quedan vacias en los demas
            "viaje_corredor_prom", "retraso_corredor_prom", "retraso_corredor_punta",
            "paradas_corredor", "paradas_corredor_le1",
            "spillback_tasa", "spillback_seg", "spillback_eventos", "cola_max_enlace", "veh_max_enlace"]
NOMBRE_BRAZO = {"baseline": "fijo", "actuado": "actuado", "demo": "rl"}
ORDEN_BRAZOS = ["fijo", "actuado", "rl"]
ESCENARIOS = ["cruce", "cruce2"] + list(rl_corredor.ESCENARIOS)

# Plan v2: columnas del CSV parcial
ID_V2 = ["brazo", "modelo", "base", "semilla"]
METRICAS_V2 = METRICAS + ["ret_retraso", "ret_colas", "ret_spill", "vehiculos", "recompensa", "decisiones"]
MODO_REFERENCIA = {"fijo": "baseline", "actuado": "actuado"}
# meta["algoritmo"] de rl_corredor -> etiqueta del modelo (ESPEC seccion 2)
ALG_TABULAR = {"qlearning": "ql", "q-learning": "ql", "ql": "ql", "sarsa": "sarsa"}


def rango(texto):
    if "-" in texto:
        a, b = texto.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in texto.split(",")]


def configurar(escenario):
    """Carga el modulo que corresponde y fija sus variables globales para el escenario."""
    if escenario in ("cruce", "cruce2"):
        import rl_semaforo as mod
        mod.ESCENARIO = escenario
        mod.CFG = mod.ESCENARIOS[escenario]["cfg"]
        mod.TLS = mod.ESCENARIOS[escenario]["tls"]
        mod.APROX = mod.ESCENARIOS[escenario]["aprox"]
    else:
        mod = rl_corredor
        mod.ESCENARIO = escenario
        mod.CFG = mod.ESCENARIOS[escenario]["cfg"]
        mod.SEMAFOROS = mod.ESCENARIOS[escenario]["semaforos"]
        mod.ENLACES = mod.ESCENARIOS[escenario]["enlaces"]
        mod.FLUJOS_CORREDOR = mod.ESCENARIOS[escenario]["flujos_corredor"]
    return mod


def preparar(escenario):
    """Modo antiguo: modulo del escenario y la Q-table q_table_<esc>.json si existe."""
    mod = configurar(escenario)
    Q = None
    if os.path.exists(f"q_table_{escenario}.json"):
        with open(f"q_table_{escenario}.json") as f:
            Q = json.load(f)
    return mod, Q


def ic95(valores):
    n = len(valores)
    if n < 2:
        return 0.0
    return stats.t.ppf(0.975, n - 1) * statistics.stdev(valores) / n ** 0.5


def cliff(a, b):
    """Delta de Cliff: P(a > b) - P(a < b), tamano de efecto sin supuestos."""
    mas = sum(1 for x in a for y in b if x > y)
    menos = sum(1 for x in a for y in b if x < y)
    return (mas - menos) / (len(a) * len(b))


def bootstrap_delta(base, otro, n_boot=10000):
    """IC95 % bootstrap (pareado por semilla) del cambio porcentual de la media respecto a base."""
    rng = np.random.default_rng(0)
    base, otro = np.array(base), np.array(otro)
    idx = rng.integers(0, len(base), size=(n_boot, len(base)))
    deltas = (otro[idx].mean(axis=1) - base[idx].mean(axis=1)) / base[idx].mean(axis=1) * 100
    return np.percentile(deltas, 2.5), np.percentile(deltas, 97.5)


def comparar(vals, ref, sufijo=""):
    """delta %, IC bootstrap, Wilcoxon pareado, Mann-Whitney y Cliff de vals frente a ref."""
    if len(ref) != len(vals) or statistics.mean(ref) == 0:
        return {}
    media_r = statistics.mean(ref)
    difs = [a - b for a, b in zip(vals, ref)]
    p_w = stats.wilcoxon(difs).pvalue if any(d != 0 for d in difs) else 1.0
    p_mw = stats.mannwhitneyu(vals, ref, method="auto").pvalue   # 'auto': exacta sin empates
    lo, hi = bootstrap_delta(ref, vals)
    return {"delta_pct" + sufijo: round((statistics.mean(vals) - media_r) / media_r * 100, 1),
            "delta_ic95" + sufijo: f"[{lo:.1f}, {hi:.1f}]",
            "p_wilcoxon" + sufijo: f"{p_w:.3g}",
            "p_mannwhitney" + sufijo: f"{p_mw:.3g}",
            "cliff" + sufijo: round(cliff(vals, ref), 2)}


def guardar_vehiculos(esc, nombre, tripinfo):
    vehiculos = comun.vehiculos_tripinfo(tripinfo)
    with open(f"vehiculos_{esc}_{nombre}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(vehiculos[0].keys()))
        w.writeheader()
        w.writerows(vehiculos)


# ---------------- Plan v2: un brazo por llamada ----------------
def leer_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def brazo_referencia(esc, brazo):
    """fijo o actuado: (brazo, modelo, base, correr)."""
    mod = configurar(esc)

    def correr(semilla, tripinfo, serie):
        return mod.correr_episodio(MODO_REFERENCIA[brazo], {}, 0.0, False, 0, semilla,
                                   tripinfo=tripinfo, serie=serie)
    return brazo, brazo, "", correr


def brazo_tabular(esc, ruta):
    """Q-tables de rl_corredor (o rl_semaforo) jugadas con epsilon 0, como el brazo rl de antes."""
    Q = leer_json(ruta)
    ruta_meta = ruta[:-len(".json")] + ".meta.json"
    if os.path.exists(ruta_meta):
        meta = leer_json(ruta_meta)
        modelo = ALG_TABULAR.get(meta.get("algoritmo", "qlearning"), meta.get("algoritmo"))
        if meta.get("recompensa", "retraso") != "retraso":
            modelo += "_" + meta["recompensa"]
        base = meta["base"]
        brazo = f"{modelo}_s{base}"
        if meta.get("escenario", esc) != esc:
            print(f"AVISO: {ruta} se entreno en {meta['escenario']} y se evalua en {esc}")
    else:
        brazo = modelo = "rl"      # Q-table vieja (06.09), sin meta
        base = ""
    mod = configurar(esc)

    def correr(semilla, tripinfo, serie):
        # copia por corrida: en demo setdefault agrega estados nuevos a la Q-table
        return mod.correr_episodio("demo", copy.deepcopy(Q), 0.0, False, 0, semilla,
                                   tripinfo=tripinfo, serie=serie)
    return brazo, modelo, base, correr


def brazo_profundo(esc, ruta, latencia, perdida):
    """Politicas de torch (.pt) de rl_ippo, rl_dqn o rl_mappo segun meta["algoritmo"]."""
    import rl_ippo
    meta = leer_json(ruta[:-len(".pt")] + ".json")
    alg = meta.get("algoritmo", "ippo")
    rl_ippo.preparar(esc)       # geometria del escenario (la usan tambien rl_dqn y rl_mappo)
    canal = {"latencia": latencia, "perdida": perdida} if latencia or perdida else {}
    if alg == "ippo":
        politica, meta = rl_ippo.Politica.cargar(ruta)
        modelo = "ippo_" + meta["variante"]

        def correr(semilla, tripinfo, serie):
            return rl_ippo.correr_episodio("demo", politica, False, 0, semilla, tripinfo=tripinfo,
                                           serie=serie, latencia=latencia, perdida=perdida,
                                           variante=meta["variante"])
    elif alg in ("dqn", "mappo"):
        import importlib
        mod = importlib.import_module("rl_" + alg)
        if hasattr(mod, "preparar"):
            mod.preparar(esc)
        modelo = alg
        if hasattr(mod, "cargar"):
            politica, meta = mod.cargar(ruta)

            def correr(semilla, tripinfo, serie):
                return mod.correr_episodio("demo", politica, False, 0, semilla, tripinfo=tripinfo,
                                           serie=serie, **canal)
        else:
            # MAPPO guardado como Politica de rl_ippo: se juega su actor con la variante del meta
            politica, meta = rl_ippo.Politica.cargar(ruta)
            variante = meta.get("variante", "vecinos")

            def correr(semilla, tripinfo, serie):
                return rl_ippo.correr_episodio("demo", politica, False, 0, semilla, tripinfo=tripinfo,
                                               serie=serie, latencia=latencia, perdida=perdida,
                                               variante=variante)
    else:
        raise SystemExit(f"{ruta}: algoritmo desconocido en el meta: {alg}")
    if meta.get("escenario", esc) != esc:
        print(f"AVISO: {ruta} se entreno en {meta['escenario']} y se evalua en {esc}")
    base = meta.get("base", "")
    brazo = f"{modelo}_s{base}" if base != "" else modelo
    if latencia or perdida:
        brazo += f"_L{latencia}p{int(round(perdida * 100))}"
    return brazo, modelo, base, correr


def main_v2(args):
    esc = args.escenario
    semillas = rango(args.semillas or "1001-1030")
    if args.brazo:
        brazo, modelo, base, correr = brazo_referencia(esc, args.brazo)
    elif args.politica.endswith(".json"):
        brazo, modelo, base, correr = brazo_tabular(esc, args.politica)
    elif args.politica.endswith(".pt"):
        brazo, modelo, base, correr = brazo_profundo(esc, args.politica, args.latencia, args.perdida)
    else:
        raise SystemExit(f"--politica debe ser .json (tabular) o .pt: {args.politica}")
    salida = args.salida or os.path.join("parciales", f"eval_{esc}_{brazo}.csv")
    if os.path.dirname(salida):
        os.makedirs(os.path.dirname(salida), exist_ok=True)
    print(f"Evaluando {brazo} (modelo {modelo}) en {esc}, {len(semillas)} semillas "
          f"{semillas[0]}-{semillas[-1]} -> {salida}", flush=True)

    tripinfo_primera = f"tripinfo_eval_{esc}_{brazo}_{os.getpid()}.xml"
    temporal = salida + ".tmp"
    with open(temporal, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ID_V2 + METRICAS_V2, extrasaction="ignore")
        w.writeheader()
        for i, semilla in enumerate(semillas):
            random.seed(semilla)      # el desempate de acciones de las Q-tables usa random
            primera = i == 0
            tripinfo = tripinfo_primera if primera else tripinfo_primera.replace(".xml", f"_s{semilla}.xml")
            serie = f"serie_{esc}_{brazo}_s{semilla}.csv" if primera else None
            t0 = time.time()
            res = correr(semilla, tripinfo, serie)
            if primera:
                guardar_vehiculos(esc, brazo, tripinfo)
            elif os.path.exists(tripinfo):
                os.remove(tripinfo)
            w.writerow({"brazo": brazo, "modelo": modelo, "base": base, "semilla": semilla,
                        **{m: res.get(m, "") for m in METRICAS_V2}})
            f.flush()
            print(f"{brazo:18s} semilla {semilla}: timeLoss={res['timeloss_prom']:6.2f}  "
                  f"espera={res['espera_prom']:6.2f}  ret_retraso={res.get('ret_retraso', '')}  "
                  f"{time.time() - t0:.1f}s", flush=True)
    os.replace(temporal, salida)
    print(f"Escrito {salida}")


# ---------------- Modo antiguo (06.09.2026) ----------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escenario", choices=ESCENARIOS, default="cruce")
    ap.add_argument("--semillas", default=None,
                    help="p. ej. 1001-1030 o 1001,1005 (por defecto 1001-1030; 1001-1010 en el modo antiguo)")
    ap.add_argument("--brazo", choices=["fijo", "actuado"], default=None, help="plan v2: brazo de referencia")
    ap.add_argument("--politica", default=None, help="plan v2: q_table_<tag>.json o politica_*.pt")
    ap.add_argument("--salida", default=None, help="plan v2: CSV parcial (parciales/eval_<esc>_<brazo>.csv)")
    ap.add_argument("--brazos", default="baseline,actuado,demo",
                    help="modo antiguo: controles de rl_semaforo/rl_corredor a correr (vacio para ninguno)")
    ap.add_argument("--ippo", default="", help="modo antiguo: politicas IPPO (.pt) separadas por coma")
    ap.add_argument("--latencia", type=int, default=0, help="latencia del canal para los brazos IPPO")
    ap.add_argument("--perdida", type=float, default=0.0, help="perdida de mensajes para los brazos IPPO")
    args = ap.parse_args()
    if args.brazo and args.politica:
        ap.error("--brazo y --politica son excluyentes")
    if args.brazo or args.politica:
        if args.ippo:
            ap.error("--ippo es del modo antiguo; en el plan v2 use --politica")
        main_v2(args)
        return
    esc = args.escenario
    semillas = rango(args.semillas or "1001-1010")
    brazos = [b for b in args.brazos.split(",") if b]
    politicas = [p for p in args.ippo.split(",") if p]
    mod, Q = preparar(esc)

    # Brazos IPPO: nombre = ippo_<variante> (+ _s<base> si la variante se repite, + _L<lat>p<perd>)
    ippo = []
    if politicas:
        import rl_ippo
        rl_ippo.preparar(esc)
        cargadas = [(ruta, *rl_ippo.Politica.cargar(ruta)) for ruta in politicas]
        variantes = [meta["variante"] for _, _, meta in cargadas]
        for ruta, politica, meta in cargadas:
            nombre = "ippo_" + meta["variante"]
            if variantes.count(meta["variante"]) > 1:
                nombre += f"_s{meta['base']}"
            if args.latencia or args.perdida:
                nombre += f"_L{args.latencia}p{int(round(args.perdida * 100))}"
            ippo.append((nombre, politica, meta))

    filas = []
    for brazo in brazos:
        nombre = NOMBRE_BRAZO[brazo]
        if brazo == "demo" and Q is None:
            print(f"No hay q_table_{esc}.json: se omite el brazo Q-learning")
            continue
        for i, semilla in enumerate(semillas):
            random.seed(semilla)
            tripinfo = f"tripinfo_{esc}_eval.xml"
            serie = f"serie_{esc}_{nombre}_s{semilla}.csv" if i == 0 else None
            res = mod.correr_episodio(brazo, copy.deepcopy(Q) if Q else {}, 0.0, False, 0, semilla,
                                      tripinfo=tripinfo, serie=serie)
            if i == 0:
                guardar_vehiculos(esc, nombre, tripinfo)
            filas.append({"brazo": nombre, "semilla": semilla, **{m: res.get(m, "") for m in METRICAS}})
            print(f"{nombre:16s} semilla {semilla}: timeLoss={res['timeloss_prom']:6.2f}  "
                  f"espera={res['espera_prom']:6.2f}  paradas={res['paradas_prom']:.2f}", flush=True)
    for nombre, politica, meta in ippo:
        import rl_ippo
        for i, semilla in enumerate(semillas):
            random.seed(semilla)
            tripinfo = f"tripinfo_{esc}_eval_ippo.xml"
            serie = f"serie_{esc}_{nombre}_s{semilla}.csv" if i == 0 else None
            res = rl_ippo.correr_episodio("demo", politica, False, 0, semilla, tripinfo=tripinfo,
                                          serie=serie, latencia=args.latencia, perdida=args.perdida,
                                          variante=meta["variante"])
            if i == 0:
                guardar_vehiculos(esc, nombre, tripinfo)
            filas.append({"brazo": nombre, "semilla": semilla, **{m: res.get(m, "") for m in METRICAS}})
            print(f"{nombre:16s} semilla {semilla}: timeLoss={res['timeloss_prom']:6.2f}  "
                  f"espera={res['espera_prom']:6.2f}  paradas={res['paradas_prom']:.2f}", flush=True)

    # Conservar del archivo anterior los brazos que no se corrieron ahora
    ruta = f"evaluacion_{esc}.csv"
    corridos = {f["brazo"] for f in filas}
    if os.path.exists(ruta):
        with open(ruta, newline="") as f:
            previas = [r for r in csv.DictReader(f) if r["brazo"] not in corridos]
        filas = previas + filas
    with open(ruta, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["brazo", "semilla"] + METRICAS, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)

    # Resumen estadistico por brazo y metrica
    nombres = [b for b in ORDEN_BRAZOS if any(fl["brazo"] == b for fl in filas)]
    nombres += sorted({fl["brazo"] for fl in filas} - set(nombres))
    por_brazo = {b: [fl for fl in filas if fl["brazo"] == b] for b in nombres}

    def valores(brazo, m):
        return [float(fl[m]) for fl in por_brazo.get(brazo, []) if fl.get(m, "") != ""]

    resumen = []
    for brazo in nombres:
        for m in METRICAS:
            vals = valores(brazo, m)
            if not vals:
                continue
            fila = {"brazo": brazo, "metrica": m, "n": len(vals),
                    "media": round(statistics.mean(vals), 3),
                    "sd": round(statistics.stdev(vals), 3) if len(vals) > 1 else 0,
                    "ic95": round(ic95(vals), 3)}
            if brazo != "fijo":
                fila.update(comparar(vals, valores("fijo", m)))
            if brazo.startswith("ippo"):
                fila.update(comparar(vals, valores("actuado", m), "_act"))
                fila.update(comparar(vals, valores("rl", m), "_rl"))
            resumen.append(fila)

    campos = ["brazo", "metrica", "n", "media", "sd", "ic95",
              "delta_pct", "delta_ic95", "p_wilcoxon", "p_mannwhitney", "cliff",
              "delta_pct_act", "delta_ic95_act", "p_wilcoxon_act", "p_mannwhitney_act", "cliff_act",
              "delta_pct_rl", "delta_ic95_rl", "p_wilcoxon_rl", "p_mannwhitney_rl", "cliff_rl"]
    with open(f"evaluacion_{esc}_resumen.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(resumen)

    print(f"\nResumen ({esc}, {len(semillas)} semillas {semillas[0]}-{semillas[-1]}); media +- IC95, "
          f"delta % vs fijo [IC95] y p de Wilcoxon:")
    for m in METRICAS:
        celdas = []
        for b in nombres:
            r = next((x for x in resumen if x["brazo"] == b and x["metrica"] == m), None)
            if r is None:
                continue
            delta = ""
            if "delta_pct" in r:
                delta = f" {r['delta_pct']:+.1f}% {r['delta_ic95']} p={r['p_wilcoxon']}"
            celdas.append(f"{b}={r['media']:.2f}+-{r['ic95']:.2f}{delta}")
        if celdas:
            print(f"{m:22s} " + " | ".join(celdas))


if __name__ == "__main__":
    main()
