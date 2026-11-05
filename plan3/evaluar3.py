"""
evaluar3.py - Evaluacion de un brazo en un escenario y una tanda de semillas, dentro de plan3 (PLAN3 0.14; B11).

Uso (desde plan3/; con escenarios nuevos, a traves de ../con_escenarios.py):
  python evaluar3.py --escenario E --semillas 8001-8030 --salida ciego/t1r/eval_E_<brazo>.csv  <BRAZO> [opciones]
  BRAZO, uno de:
    --brazo fijo|actuado|trivial            los de lo entregado (fijo = el programa instalado del escenario)
    --brazo fijo --programa RUTA --nombre X un fijo desde un archivo de programa, p. ej. el fijo fino
                                            <esc>_r10f.add.xml (brazo fijo_<X>; evaluar.brazo_programa)
    --brazo franja|bloques|actuado_aj [--programa RUTA]
                                            franja, bloques (WAUT) o actuado ajustado; por defecto <esc>_<brazo>.add.xml
    --politica politica_<...>.pt            una politica de torch (evaluar.brazo_profundo lee su meta)
    --regla R                               regla simple o Max-Pressure por su nombre (evaluar.brazo_regla)
    --regla-de barridos/<esc>/regla.json    la regla ganadora de un barrido de plan3/reglas.py (o mp.json)
  opciones: --perdida 1 (mensajes cortados, a3), --colas-cero (colas en cero en la observacion, a3)
  Un solo brazo por comando (--brazo, --politica, --regla y --regla-de son excluyentes); opciones completas.

Referencias (plan3-ref; la parte B del prerregistro):
  - la columna sha_ref lleva el sha256 del archivo de la referencia que se carga: el programa (--programa, o
    <esc>_<brazo>.add.xml de franja, bloques y actuado_aj) o el JSON de --regla-de; vacia en los demas brazos;
  - --regla-de se niega si el JSON trae la marca de prueba, si su familia no es la del nombre del archivo o si es de
    otro escenario (salvo mixa_<x>, que juega lo de mix_<x>);
  - A CIEGAS (--salida ciego/...), un brazo con archivo de referencia se niega antes de simular si
    plan3/referencias_congeladas.json (p3_congelar.py, dia 14) falta, no lo lista o tiene otro sha256.

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


BRAZOS = ("fijo", "actuado", "trivial", "franja", "bloques", "actuado_aj")
CON_PROGRAMA = ("fijo", "franja", "bloques", "actuado_aj")
CONGELADAS = os.path.join(PLAN3, "referencias_congeladas.json")


def sha256_de(ruta):
    import hashlib
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def archivo_de_referencia(a):
    """El archivo que carga el brazo (relativo a plan3/, como lo nombra el comando), o None (lo entregado, una
    politica o una regla por su nombre)."""
    if a.regla_de:
        return a.regla_de
    if a.brazo in ("franja", "bloques", "actuado_aj"):
        return a.programa or f"{a.escenario}_{a.brazo}.add.xml"
    if a.brazo == "fijo" and a.programa:
        return a.programa
    return None


def comprobar_congelada(ruta):
    """A ciegas: la referencia debe ser la congelada en la parte B (referencias_congeladas.json, mismo sha256)."""
    import json
    if not os.path.exists(CONGELADAS):
        sys.exit(f"a ciegas, la referencia {ruta} necesita {os.path.basename(CONGELADAS)} (parte B, p3_congelar.py)")
    with open(CONGELADAS, encoding="utf-8") as f:
        congeladas = json.load(f)["referencias"]
    clave = os.path.relpath(os.path.abspath(ruta), PLAN3).replace(os.sep, "/")
    if clave not in congeladas:
        sys.exit(f"a ciegas: {clave} no esta en {os.path.basename(CONGELADAS)}")
    if not os.path.exists(ruta) or sha256_de(ruta) != congeladas[clave]["sha256"]:
        sys.exit(f"a ciegas: {clave} no es la referencia congelada (sha256 distinto o falta el archivo)")


def leer_regla_de(a):
    """El nombre de la regla ganadora de un JSON de reglas.py, revisado: sin marca de prueba, su familia es la del
    nombre del archivo y es de este escenario (mixa_<x> juega lo de mix_<x>)."""
    import json
    with open(a.regla_de, encoding="utf-8") as f:
        datos = json.load(f)
    familia = os.path.splitext(os.path.basename(a.regla_de))[0]
    malos = []
    if (datos.get("registro") or {}).get("prueba"):
        malos.append(f"trae la marca de prueba {datos['registro']['prueba']}")
    if datos.get("familia") != familia:
        malos.append(f"su familia es {datos.get('familia')}, no {familia}")
    esc = a.escenario
    mismo = datos.get("escenario") == esc or (esc.startswith("mixa_") and datos.get("escenario") == "mix_" + esc[5:])
    if not mismo:
        malos.append(f"es de {datos.get('escenario')}, no de {esc}")
    if malos:
        sys.exit(f"--regla-de {a.regla_de}: " + "; ".join(malos))
    return datos["regla"]


def armar_brazo(a, evaluar):
    """(brazo, modelo, base, correr) con las funciones de evaluar.py (plan3-ref, informe_ref §3)."""
    esc = a.escenario
    if a.politica:
        return evaluar.brazo_profundo(esc, a.politica, 0, a.perdida)
    if a.brazo == "fijo" and a.programa:
        return evaluar.brazo_programa(esc, a.programa, a.nombre)
    if a.brazo:
        return evaluar.brazo_referencia(esc, a.brazo, adicional=a.programa)
    if a.regla_de:
        return evaluar.brazo_regla(esc, leer_regla_de(a))
    return evaluar.brazo_regla(esc, a.regla)


def construir_parser():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--escenario", required=True)
    ap.add_argument("--semillas", required=True)
    ap.add_argument("--salida", required=True)
    brazo = ap.add_mutually_exclusive_group(required=True)
    brazo.add_argument("--brazo", choices=BRAZOS)
    brazo.add_argument("--politica")
    brazo.add_argument("--regla")
    brazo.add_argument("--regla-de", dest="regla_de")
    ap.add_argument("--programa")
    ap.add_argument("--nombre", default=None)
    ap.add_argument("--perdida", type=float, default=0.0)
    ap.add_argument("--colas-cero", action="store_true")
    return ap


def validar_args(argv):
    """Lee y revisa los argumentos (argv sin el nombre del programa): parse_args y todos los ap.error, sin leer
    archivos. Devuelve args o sale como argparse (SystemExit(2)). La usa chequeos_previos."""
    ap = construir_parser()
    a = ap.parse_args(argv)
    if a.programa and a.brazo not in CON_PROGRAMA:
        ap.error(f"--programa solo va con --brazo {', '.join(CON_PROGRAMA)}")
    if bool(a.brazo == "fijo" and a.programa) != bool(a.nombre):
        ap.error("--brazo fijo --programa necesita --nombre, y --nombre solo va con ellos")
    try:
        if not rango(a.semillas):
            raise ValueError
    except ValueError:
        ap.error(f"--semillas ilegible: {a.semillas}")
    return a


def main():
    a = validar_args(sys.argv[1:])
    ciego = a.salida.replace("\\", "/").startswith("ciego/")
    semillas = rango(a.semillas)
    ruta_ref = archivo_de_referencia(a)
    if ruta_ref and ciego:
        comprobar_congelada(ruta_ref)              # antes de simular nada
    sha_ref = sha256_de(ruta_ref) if ruta_ref and os.path.exists(ruta_ref) else ""
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
    campos = evaluar.ID_V2 + evaluar.METRICAS_V2 + EXTRA + ["sha_ref"]
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
                            **{m: res.get(m, "") for m in evaluar.METRICAS_V2 + EXTRA}, "sha_ref": sha_ref})
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
