"""
evaluar3.py - Evaluacion de un brazo en un escenario y una tanda de semillas, dentro de plan3 (PLAN3 0.14; B11).

Uso (desde plan3/; con escenarios nuevos, a traves de ../con_escenarios.py):
  python evaluar3.py --escenario E --semillas 8001-8030 --salida ciego/t1r/eval_E_<brazo>.csv  <BRAZO> [opciones]
  BRAZO, uno de:
    --brazo fijo|actuado|trivial|...        los de evaluar.brazo_referencia (fijo = el programa instalado)
    --politica politica_<...>.pt            una politica de torch (evaluar.brazo_profundo lee su meta)
    --programa RUTA.add.xml --nombre X      un fijo desde un archivo de programa (brazo fijo_<X>)
    --franja RUTA --nombre X                fijo por franja o por bloques (WAUT)
    --actuado-aj RUTA --nombre X            actuado ajustado (archivo con sus parametros)
    --regla R                               regla simple o Max-Pressure (evaluar.brazo_regla)
  opciones: --perdida 1 (mensajes cortados, a3), --colas-cero (colas en cero en la observacion, a3)

Distinto de evaluar.py:
  - su propio ciclo por semilla y escritura atomica (temporal con el pid y reemplazo al final);
  - A CIEGAS si --salida empieza por ciego/: el log dice solo semilla y segundos; no guarda los extras (serie, fases,
    vehiculos) de ningun brazo: todo temporal va a tmp_eval3_<pid>/ y se borra;
  - por semilla agrega: vehiculos generados (insertados + no insertados), y por periodo (salida pedida antes o desde
    los 1800 s) el retraso total y los insertados; los no insertados se asignan a su periodo por su salida
    programada (fin - espera) y se informan aparte (prerregistro §4). Para eso pide a SUMO las filas de los no
    insertados (comun.ESCRIBIR_NO_INSERTADOS), que comun.leer_tripinfo excluye de las metricas de siempre.
"""
import os
import csv
import sys
import time
import shutil
import random
import argparse
import xml.etree.ElementTree as ET

PLAN3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(PLAN3))

CORTE_PERIODO = 1800.0
EXTRA = ["generados", "insertados_p1", "insertados_p2", "no_insertados_p1", "no_insertados_p2",
         "retraso_total_p1", "retraso_total_p2", "espera_no_insertados"]


def rango(texto):
    salida = []
    for parte in texto.split(","):
        if "-" in parte[1:]:
            a, b = parte.split("-", 1)
            salida += list(range(int(a), int(b) + 1))
        elif parte:
            salida.append(int(parte))
    return salida


def por_periodo(tripinfo, fin_sim):
    """Retraso total por periodo de la salida pedida, con las filas de los no insertados (depart < 0)."""
    suma = {1: 0.0, 2: 0.0}
    ins = {1: 0, 2: 0}
    noins = {1: 0, 2: 0}
    espera_fuera = 0.0
    for v in ET.parse(tripinfo).getroot().iter("tripinfo"):
        dd = float(v.get("departDelay", 0))
        dep = float(v.get("depart", -1))
        if dep >= 0:
            p = 1 if dep - dd < CORTE_PERIODO else 2
            ins[p] += 1
            suma[p] += float(v.get("timeLoss", 0)) + dd
        else:                                   # no insertado: espero dd hasta el cierre
            p = 1 if fin_sim - dd < CORTE_PERIODO else 2
            noins[p] += 1
            suma[p] += dd
            espera_fuera += dd
    res = {"insertados_p1": ins[1], "insertados_p2": ins[2], "no_insertados_p1": noins[1],
           "no_insertados_p2": noins[2], "generados": ins[1] + ins[2] + noins[1] + noins[2],
           "espera_no_insertados": round(espera_fuera, 1)}
    for p in (1, 2):
        n = ins[p] + noins[p]
        res[f"retraso_total_p{p}"] = round(suma[p] / n, 2) if n else ""
    return res


def fin_de_simulacion(tripinfo):
    """Instante del cierre: lo escribe SUMO en el archivo de estadisticas (performance end)."""
    import comun
    stats = comun.ruta_estadisticas(tripinfo)
    raiz = ET.parse(stats).getroot()
    perf = raiz.find("performance")
    return float(perf.get("end")) if perf is not None and perf.get("end") else None


def armar_brazo(a, evaluar):
    esc = a.escenario
    if a.politica:
        return evaluar.brazo_profundo(esc, a.politica, 0, a.perdida)
    if a.brazo:
        return evaluar.brazo_referencia(esc, a.brazo)
    for opcion, funcion in (("programa", "brazo_programa"), ("franja", "brazo_franja"),
                            ("actuado_aj", "brazo_actuado_aj")):
        ruta = getattr(a, opcion)
        if ruta:
            if not hasattr(evaluar, funcion):
                sys.exit(f"evaluar.py no tiene {funcion} todavia")
            return getattr(evaluar, funcion)(esc, ruta, a.nombre)
    if a.regla:
        if not hasattr(evaluar, "brazo_regla"):
            sys.exit("evaluar.py no tiene brazo_regla todavia")
        return evaluar.brazo_regla(esc, a.regla)
    sys.exit("falta el brazo (--brazo, --politica, --programa, --franja, --actuado-aj o --regla)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escenario", required=True)
    ap.add_argument("--semillas", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--brazo")
    ap.add_argument("--politica")
    ap.add_argument("--programa")
    ap.add_argument("--franja")
    ap.add_argument("--actuado-aj", dest="actuado_aj")
    ap.add_argument("--regla")
    ap.add_argument("--nombre", default=None)
    ap.add_argument("--perdida", type=float, default=0.0)
    ap.add_argument("--colas-cero", action="store_true")
    a = ap.parse_args()
    ciego = a.salida.replace("\\", "/").startswith("ciego/")
    semillas = rango(a.semillas)
    import comun
    import evaluar
    comun.ESCRIBIR_NO_INSERTADOS = True          # filas de los no insertados, excluidas de las metricas de siempre
    if a.colas_cero:
        import rl_ippo
        if not hasattr(rl_ippo, "configurar_colas_cero"):
            sys.exit("rl_ippo.py no tiene configurar_colas_cero todavia")
        rl_ippo.configurar_colas_cero(True)
    brazo, modelo, base, correr = armar_brazo(a, evaluar)
    if a.perdida:
        brazo += f"_p{int(round(a.perdida * 100))}"
    if a.colas_cero:
        brazo += "_colas0"
    tmp_dir = os.path.join(PLAN3, f"tmp_eval3_{os.getpid()}")
    os.makedirs(tmp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(a.salida) or ".", exist_ok=True)
    temporal = f"{a.salida}.{os.getpid()}.tmp"
    campos = evaluar.ID_V2 + evaluar.METRICAS_V2 + EXTRA
    print(f"evaluar3: {brazo} en {a.escenario}, {len(semillas)} semillas{' (a ciegas)' if ciego else ''}",
          flush=True)
    try:
        with open(temporal, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
            w.writeheader()
            for semilla in semillas:
                random.seed(semilla)
                tripinfo = os.path.join(tmp_dir, f"tripinfo_{semilla}.xml")
                t0 = time.time()
                res = correr(semilla, tripinfo, None)
                fin = fin_de_simulacion(tripinfo) or float(res.get("fin_sim", 0) or 0)
                res.update(por_periodo(tripinfo, fin))
                comun.borrar_tripinfo(tripinfo)
                w.writerow({"brazo": brazo, "modelo": modelo, "base": base, "semilla": semilla,
                            **{m: res.get(m, "") for m in evaluar.METRICAS_V2 + EXTRA}})
                f.flush()
                if ciego:
                    print(f"semilla {semilla}: {time.time() - t0:.1f} s", flush=True)
                else:
                    print(f"{brazo} semilla {semilla}: total={res['retraso_total_prom']}  "
                          f"timeLoss={res['timeloss_prom']}  {time.time() - t0:.1f} s", flush=True)
        os.replace(temporal, a.salida)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        if os.path.exists(temporal):
            os.remove(temporal)
    print(f"evaluar3: escrito {a.salida}", flush=True)


if __name__ == "__main__":
    main()
