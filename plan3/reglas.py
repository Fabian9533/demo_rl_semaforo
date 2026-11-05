"""
reglas.py - Regla simple y Max-Pressure para el gancho decidir de rl_ippo.correr_episodio (plan3, tarea 0.10;
DECISIONES B10; prerregistro, seccion 5). No cambia rl_ippo.py: usa la interfaz para decisores externos (mismo reloj
de 5 s desde el inicio de cada verde, misma mascara de verde minimo 10 s y maximo 60 s, mismo ambar y mismas
metricas que IPPO; con variante "local" no hay mensajes y la politica puede ser None).

Nombres (evaluar.py --regla NOMBRE; evaluar.brazo_regla):
  regla_u<U>g<G>       ciclo minimo, pero en el verde de la avenida se mantiene mientras la cola de la avenida
                       (maximo de detenidos por carril en los dos accesos E-O) sea >= U y el verde lleve menos de G s;
                       la transversal corta en su minimo. U entero o inf: regla_uinfg60 es el ciclo minimo.
  mp, mp_det           Max-Pressure por carril sin ciclo maximo (Varaiya 2013): con la mascara libre, cambia si la
                       presion de la otra fase supera a la de la actual. Presion de una fase: por cada carril de
                       entrada con algun enlace en verde, x(entrada) menos el promedio de x en sus carriles de salida
                       con verde (cada carril de entrada cuenta una vez); x = vehiculos (mp) o detenidos (mp_det).
  mp_c<C>, mp_det_c<C> lo mismo con un ciclo maximo de C s (Levin, Hu y Odell 2020, con 2 fases): la avenida corta a
                       tiempo para que entren la transversal con su minimo y los dos ambares; la transversal cierra
                       el ciclo.
Toda accion respeta la mascara (0 si no puede cambiar, 1 si el verde llego al maximo).

Barrido (cwd = plan3/; con llegadas aleatorias, a traves de ../con_escenarios.py):
  python reglas.py <esc> [--familia regla|mp|todas] [--llegadas auto|regulares|aleatorias]
  regla: U en {1, 2, 3, 4, 6} x G en {30, 60}; mp: mp, mp_det, mp_c60 y mp_c90. Cada familia con 2001-2003 y sus 3
  mejores con 2001-2010 (con llegadas aleatorias, sus 10 mejores con 2001-2030); gana la menor media. Max-Pressure es
  solo descriptivo. Salidas en barridos/<esc>/, por familia (dos trabajos --familia regla y --familia mp no se pisan):
  reglas_<familia>.csv, reglas_<familia>_final.csv, reglas_<familia>_semillas.csv, y regla.json o mp.json. Corre por
  TraCI en un solo proceso (rl_ippo usa una conexion global).
"""
import os
import re
import sys
import json
import glob
import time
import hashlib
import argparse
import statistics

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
for _ruta in (AQUI, RAIZ):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import numpy as np  # noqa: E402

AMBAR = 3                  # ambar de todos los escenarios (3 s)
VERDE_MIN = 10             # verde minimo del agente (la mascara)
PATRON = re.compile(r"^(regla_u(?P<u>\d+|inf)g(?P<g>\d+)|mp(?P<det>_det)?(_c(?P<c>\d+))?)$")
REGLAS = [f"regla_u{u}g{g}" for u in (1, 2, 3, 4, 6) for g in (30, 60)]
MAX_PRESSURE = ["mp", "mp_det", "mp_c60", "mp_c90"]
FINALES = {"regulares": 3, "aleatorias": 10}
METRICAS = ("retraso_total_prom", "timeloss_prom", "retraso_insercion_prom", "espera_prom", "paradas_prom",
            "throughput", "co2_prom", "no_insertados", "no_terminados", "vehiculos", "cambios_fase",
            "decisiones", "decisiones_libres")


def validar(regla):
    """Parametros de un nombre de regla: {"tipo": "regla"|"mp", "u", "g", "medida", "ciclo"}; error si no existe."""
    m = PATRON.match(regla)
    if not m:
        raise SystemExit(f"Regla desconocida: {regla} (regla_u<U>g<G>, mp, mp_det, mp_c<C>, mp_det_c<C>)")
    if regla.startswith("regla_"):
        return {"tipo": "regla", "u": float("inf") if m["u"] == "inf" else int(m["u"]), "g": int(m["g"])}
    return {"tipo": "mp", "medida": "det" if m["det"] else "veh", "ciclo": int(m["c"]) if m["c"] else None}


class Geometria:
    """Por semaforo: carriles de los accesos de avenida (aproximaciones 0 y 1) y, por fase, los pares (carril de
    entrada, carril de salida) con verde. Se lee con TraCI en la primera decision del episodio."""

    def __init__(self):
        self.listo = False

    def preparar(self):
        import traci
        import rl_ippo
        self.av_carriles, self.mov, self.verdes = {}, {}, {}
        for tls, aprox in rl_ippo.C["semaforos"].items():
            self.av_carriles[tls] = [f"{a}_{k}" for a in aprox[:2] for k in range(traci.edge.getLaneNumber(a))]
            links = traci.trafficlight.getControlledLinks(tls)
            activo = traci.trafficlight.getProgram(tls)
            logica = next(lg for lg in traci.trafficlight.getAllProgramLogics(tls) if lg.programID == activo)
            self.verdes[tls] = [i for i, f in enumerate(logica.phases)
                                if ("G" in f.state or "g" in f.state) and "y" not in f.state]
            self.mov[tls] = {}
            for i, fase in enumerate(logica.phases):
                pares = set()
                for k, s in enumerate(fase.state):
                    if s in "Gg" and links[k]:
                        pares.add((links[k][0][0], links[k][0][1]))
                self.mov[tls][i] = sorted(pares)
        self.listo = True


def cola_avenida(geo, tls):
    import traci
    return max(traci.lane.getLastStepHaltingNumber(c) for c in geo.av_carriles[tls])


def presion(geo, tls, fase, medida):
    """Presion por carril de una fase (indice del programa activo)."""
    import traci
    leer = traci.lane.getLastStepVehicleNumber if medida == "veh" else traci.lane.getLastStepHaltingNumber
    salidas = {}
    for entrada, salida in geo.mov[tls][fase]:
        salidas.setdefault(entrada, []).append(salida)
    return sum(leer(e) - sum(leer(s) for s in ss) / len(ss) for e, ss in salidas.items())


def hacer_decidir(regla, registro=None):
    """Funcion decidir(deciden, obs, mascara, modo, info) para rl_ippo.correr_episodio. Crear una por episodio
    (guarda el inicio del ciclo de cada semaforo). registro: lista opcional donde se anota (t, tls, mascara,
    accion, presiones) de cada decision (pruebas)."""
    import rl_ippo
    par = validar(regla)
    geo = Geometria()
    inicio_ciclo = {}

    def decidir(deciden, obs, masc, modo, info):
        if not geo.listo:
            geo.preparar()
        t = info["t"]
        acciones = []
        for k, tls in enumerate(deciden):
            m = masc[k]
            verde = int(np.argmax(obs[k][8:10]))               # indice dentro de las fases verdes
            t_verde = int(round(float(obs[k][10]) * 60))
            fase_av = rl_ippo.C["fase_av"][tls]
            if verde == fase_av:                                # el ciclo empieza con el verde de avenida
                inicio_ciclo[tls] = t - t_verde
            presiones = None
            if m[1] == 0:                                       # todavia no puede cambiar
                a = 0
            elif m[0] == 0:                                     # verde maximo: cambio forzado
                a = 1
            elif par["tipo"] == "regla":
                a = 0 if (verde == fase_av and cola_avenida(geo, tls) >= par["u"] and t_verde < par["g"]) else 1
            else:
                fv = geo.verdes[tls]
                actual, otra = fv[verde], fv[1 - verde]
                presiones = (presion(geo, tls, actual, par["medida"]), presion(geo, tls, otra, par["medida"]))
                a = 1 if presiones[1] > presiones[0] else 0
                if par["ciclo"] is not None:
                    transcurrido = t - inicio_ciclo.get(tls, t - t_verde)
                    if verde == fase_av and transcurrido + 5 > par["ciclo"] - 2 * AMBAR - VERDE_MIN:
                        a = 1                                   # deja lugar a la transversal en este ciclo
                    if verde != fase_av and transcurrido + 5 > par["ciclo"] - AMBAR:
                        a = 1                                   # cierra el ciclo
            assert m[a] > 0, f"{regla}: accion {a} fuera de la mascara {m} en {tls}, t={t}"
            acciones.append(a)
            if registro is not None:
                registro.append((t, tls, (float(m[0]), float(m[1])), a, presiones))
        return acciones, [None] * len(deciden)
    return decidir


def correr(esc, regla, semilla, tripinfo, serie=None, registro=None):
    """Un episodio de la regla por rl_ippo (llamar antes rl_ippo.preparar(esc))."""
    import rl_ippo
    return rl_ippo.correr_episodio("demo", None, False, 0, semilla, tripinfo=tripinfo, serie=serie,
                                   variante="local", decidir=hacer_decidir(regla, registro))


# ---------------------------------------------------------------- barrido
def main():
    ap = argparse.ArgumentParser(description="Barrido de la regla simple y de Max-Pressure (plan3, 0.10)")
    ap.add_argument("escenario")
    ap.add_argument("--familia", choices=["regla", "mp", "todas"], default="todas")
    ap.add_argument("--llegadas", choices=["auto", "regulares", "aleatorias"], default="auto")
    ap.add_argument("--semillas", default="2001-2003", help="(pruebas) en vez de 2001-2003")
    ap.add_argument("--semillas-final", help="(pruebas) en vez de 2001-2010 / 2001-2030")
    args = ap.parse_args()
    import comun
    import rl_ippo
    import barrer_fino as bfn
    esc = args.escenario
    cfg = rl_ippo.ESCENARIOS[esc]["cfg"] if esc in rl_ippo.ESCENARIOS else None
    if cfg is None or not os.path.exists(cfg):
        raise SystemExit(f"{esc}: escenario sin registrar en rl_ippo o sin {cfg} en {os.getcwd()}")
    aleatorias = bfn.llegadas_aleatorias(cfg) if args.llegadas == "auto" else args.llegadas == "aleatorias"
    llegadas = "aleatorias" if aleatorias else "regulares"
    semillas = bfn.leer_semillas(args.semillas)
    semillas_f = bfn.leer_semillas(args.semillas_final or bfn.SEMILLAS[llegadas]["desempate"])
    familias = {"regla": REGLAS, "mp": MAX_PRESSURE}
    if args.familia != "todas":
        familias = {args.familia: familias[args.familia]}
    with open(os.path.abspath(__file__), "rb") as f:      # una corrida guardada vale con el mismo codigo de reglas
        huella = bfn.huella_escenario(cfg) + "_" + hashlib.sha256(f.read()).hexdigest()[:8]
    carpeta = os.path.join("barridos", esc)
    tmp = os.path.join(bfn.CARPETA_TMP, esc)
    os.makedirs(tmp, exist_ok=True)
    cache = os.path.join(tmp, f"reglas_{os.getpid()}.jsonl")
    conocidas = {}
    for ruta in sorted(glob.glob(os.path.join(tmp, "reglas*.jsonl"))):
        with open(ruta, encoding="utf-8") as f:
            for linea in f:
                try:
                    d = json.loads(linea)
                except ValueError:
                    continue
                if d.get("h") == huella:
                    conocidas[(d["regla"], int(d["s"]))] = d["r"]
    rl_ippo.preparar(esc)
    print(f"reglas {esc}: llegadas {llegadas}, {bfn.texto_semillas(semillas)} y finalistas con "
          f"{bfn.texto_semillas(semillas_f)}, huella {huella}, {len(conocidas)} corridas guardadas", flush=True)
    t0 = time.time()

    def asegurar(lista, sems):
        for regla in lista:
            for s in sems:
                if (regla, s) in conocidas:
                    continue
                ti = os.path.join(tmp, f"ti_regla_{os.getpid()}.xml")
                t1 = time.time()
                res = correr(esc, regla, s, ti)
                comun.borrar_tripinfo(ti)
                conocidas[(regla, s)] = {m: res.get(m, "") for m in METRICAS}
                with open(cache, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"h": huella, "regla": regla, "s": s, "r": conocidas[(regla, s)]}) + "\n")
                print(f"  {regla:12s} s{s}: total={res['retraso_total_prom']:7.2f} "
                      f"timeLoss={res['timeloss_prom']:7.2f} cambios={res['cambios_fase']} "
                      f"{time.time() - t1:.1f}s", flush=True)

    def fila(regla, sems, etapa):
        res = [conocidas[(regla, s)] for s in sems]
        f = {"etapa": etapa, "regla": regla, "semillas": bfn.texto_semillas(sems)}
        for m in METRICAS:
            f[m] = round(statistics.mean(float(r[m]) for r in res), 2)
        tot = [float(r["retraso_total_prom"]) for r in res]
        f.update({"retraso_total_sd": round(statistics.stdev(tot), 2) if len(tot) > 1 else 0,
                  "mediana": round(statistics.median(tot), 2), "peor": max(tot)})
        return f

    campos = ["etapa", "regla", "semillas"] + list(METRICAS) + ["retraso_total_sd", "mediana", "peor"]
    sems_todas = list(dict.fromkeys(semillas + semillas_f))
    for familia, lista in familias.items():          # salidas por familia: dos trabajos no se pisan
        asegurar(lista, semillas)
        filas = sorted((fila(r, semillas, familia) for r in lista), key=lambda f: f["retraso_total_prom"])
        finalistas = [f["regla"] for f in filas[:FINALES[llegadas]]]
        asegurar(finalistas, semillas_f)
        filas_f = sorted((fila(r, semillas_f, f"final_{familia}") for r in finalistas),
                         key=lambda f: f["retraso_total_prom"])
        g = filas_f[0]
        filas_s = [{"regla": r, "semilla": s, "huella": huella, **conocidas[(r, s)]}
                   for r in lista for s in sems_todas if (r, s) in conocidas]
        bfn.escribir_csv(os.path.join(carpeta, f"reglas_{familia}_semillas.csv"),
                         ["regla", "semilla", "huella"] + list(METRICAS), filas_s)
        bfn.escribir_csv(os.path.join(carpeta, f"reglas_{familia}.csv"), campos, filas)
        bfn.escribir_csv(os.path.join(carpeta, f"reglas_{familia}_final.csv"), campos, filas_f)
        bfn.escribir_json(os.path.join(carpeta, "regla.json" if familia == "regla" else "mp.json"),
                          {"escenario": esc, "llegadas": llegadas, "huella": huella, "familia": familia,
                           "regla": g["regla"], "finalistas": finalistas,
                           "semillas_barrido": bfn.texto_semillas(semillas),
                           **{k: g[k] for k in ("retraso_total_prom", "retraso_total_sd", "timeloss_prom",
                                                "mediana", "peor", "semillas")}})
        print(f"{esc} {familia}: gana {g['regla']} con {g['retraso_total_prom']} ({g['semillas']})", flush=True)
    print(f"reglas {esc}: listo en {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
