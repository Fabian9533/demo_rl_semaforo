"""
prueba_cargas.py - Pruebas 7 y 5 de los escenarios nuevos:
  7. Nadie traba la red con el fijo instalado ni con el actuado: en los 13 escenarios, semillas de humo 424301 y
     424302, con evaluar.py por el lanzador (como correra la cola), todos los vehiculos entran y terminan antes del
     tope de 6000 s (no_insertados = no_terminados = 0); los teletransportes estan apagados en todos los .sumocfg
     (time-to-teleport -1), asi que una red trabada se veria como vehiculos sin terminar. Se informa el retraso total
     medio de cada brazo (descriptivo: semillas de humo y referencias sin re-ajustar). En per_, ademas, el retraso
     por bloque de 10 min de la primera semilla (el bloque punta no se traba).
  5. En malla3_alta_e (P6e) la espera para entrar del fijo queda bajo 1 s/veh; al lado, P6 entregado (entrada por
     defecto) con las mismas semillas.
Uso (desde plan3/): python pruebas/esc/prueba_cargas.py
Salida: salidas/cargas.txt, cargas.csv y salidas/cargas/eval_<esc>_<brazo>.csv (los CSV de evaluar.py)
"""
import os
import re
import sys
import csv
import glob
import shutil
import subprocess
import statistics as st
import concurrent.futures as cf
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_esc as u                       # noqa: E402
import demanda_estocastica as de           # noqa: E402

SEMILLAS = "424301-424302"
CARPETA = os.path.join(u.TMP, "cargas")
ENTORNO = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")


def evaluar(esc, brazo):
    """evaluar.py por el lanzador; un proceso por (escenario, brazo): nunca dos escriben el mismo _actuado.add.xml."""
    rel = os.path.relpath(CARPETA, u.PLAN3)
    r = subprocess.run([sys.executable, "../con_escenarios.py", "../evaluar.py", "--escenario", esc, "--brazo", brazo,
                        "--semillas", SEMILLAS, "--salida", f"{rel}/eval_{esc}_{brazo}.csv",
                        "--extras", f"{rel}/extras_{esc}_{brazo}"], cwd=u.PLAN3, capture_output=True, text=True,
                       env=ENTORNO)
    if r.returncode != 0:
        raise RuntimeError(f"{esc} {brazo}: {r.stderr[-600:]}")
    segundos = [float(x) for x in re.findall(r"(\d+\.\d)s\s*$", r.stdout, flags=re.M)]
    with open(os.path.join(CARPETA, f"eval_{esc}_{brazo}.csv"), newline="") as f:
        return list(csv.DictReader(f)), segundos


def tripinfo_primera(esc, brazo):
    """Tripinfo de la primera semilla, que evaluar.py deja en la carpeta de --extras."""
    return glob.glob(os.path.join(CARPETA, f"extras_{esc}_{brazo}", f"tripinfo_eval_{esc}_{brazo}_*.xml"))[0]


def ultima_llegada(esc, brazo):
    """Instante en que termina el ultimo vehiculo en la primera semilla (margen hasta el tope de 6000 s)."""
    return max(float(v.get("arrival")) for v in ET.parse(tripinfo_primera(esc, brazo)).getroot().iter("tripinfo"))


def por_bloque(esc, brazo):
    """Retraso total medio (timeLoss + espera para entrar) por bloque de 10 min de la salida pedida, primera
    semilla."""
    bloques = {}
    for v in ET.parse(tripinfo_primera(esc, brazo)).getroot().iter("tripinfo"):
        pedida = float(v.get("depart")) - float(v.get("departDelay"))
        bloques.setdefault(int(pedida // 600), []).append(float(v.get("timeLoss")) + float(v.get("departDelay")))
    return {k: (len(x), st.mean(x)) for k, x in sorted(bloques.items())}


def main():
    os.chdir(u.PLAN3)
    shutil.rmtree(CARPETA, ignore_errors=True)
    os.makedirs(CARPETA)
    p = u.Salida("cargas.txt")
    fallas = []

    def ok(cond, texto):
        p(("  ok    " if cond else "  FALLA ") + texto)
        if not cond:
            fallas.append(texto)

    nombres = u.escenarios()
    trabajos = [(e, b) for e in nombres for b in ("fijo", "actuado")] + [("malla3_alta", "fijo")]
    res = {}
    with cf.ThreadPoolExecutor(u.MAX_SUMO) as pool:
        fut = {pool.submit(evaluar, e, b): (e, b) for e, b in trabajos}
        for f in cf.as_completed(fut):
            res[fut[f]] = f.result()
    p(f"7. Fijo instalado y actuado en los escenarios nuevos, semillas {SEMILLAS}, evaluar.py por el lanzador "
      f"(retraso total, timeLoss y espera para entrar en s/veh; media de las 2 semillas)")
    teleport = {e: ET.parse(f"{e}.sumocfg").getroot().find(".//time-to-teleport").get("value") for e in nombres}
    ok(set(teleport.values()) == {"-1"}, f"time-to-teleport -1 en los {len(teleport)} .sumocfg (sin teletransportes)")
    filas = []
    for e, b in trabajos:
        rs, segundos = res[(e, b)]
        m = {k: st.mean(float(r[k]) for r in rs) for k in ("retraso_total_prom", "timeloss_prom",
                                                          "retraso_insercion_prom", "vehiculos")}
        no_ins = max(int(r["no_insertados"]) for r in rs)
        no_ter = max(int(r["no_terminados"]) for r in rs)
        ultima = ultima_llegada(e, b)
        filas.append({"escenario": e, "brazo": b, **{k: round(v, 2) for k, v in m.items()},
                      "no_insertados_max": no_ins, "no_terminados_max": no_ter,
                      "retraso_total_por_semilla": "/".join(r["retraso_total_prom"] for r in rs),
                      "ultima_llegada_s1": ultima, "segundos_por_episodio": "/".join(f"{s:.1f}" for s in segundos)})
        texto = (f"{e:16s} {b:8s} total {m['retraso_total_prom']:7.2f} (por semilla "
                 f"{'/'.join(r['retraso_total_prom'] for r in rs)}), timeLoss {m['timeloss_prom']:6.2f}, entrar "
                 f"{m['retraso_insercion_prom']:6.2f}; vehiculos {m['vehiculos']:.0f}; no insertados {no_ins}, "
                 f"no terminados {no_ter}; ultima llegada {ultima:.0f} s")
        if e in nombres:
            ok(no_ins == 0 and no_ter == 0, texto)
        else:
            p("  (P6 entregado, entrada por defecto) " + texto)
    for e in [x for x in nombres if x.startswith("per_")]:
        esperado = de.por_bloque(os.path.join(u.PLAN3, f"{e}.rou.xml"))
        for b in ("fijo", "actuado"):
            bl = por_bloque(e, b)
            p(f"  {e} {b}, semilla 424301, retraso total por bloque de 10 min (vehiculos / s por vehiculo): "
              + ", ".join(f"b{k} {n} / {x:.1f}" for k, (n, x) in bl.items())
              + f"  (esperados por bloque: {', '.join(f'{v:.0f}' for v in esperado.values())})")
    corredor = ("viaje_corredor_prom", "retraso_corredor_punta", "paradas_corredor_le1")
    for e in ("poi_corredor", "per_corredor", "poi_red", "per_red"):
        rs = res[(e, "fijo")][0]
        p(f"  (informativo) {e:12s} fijo, metricas del corredor por semilla ({', '.join(corredor)}): "
          + "; ".join("/".join(r[m] for m in corredor) for r in rs)
          + ("  <- en per_ salen en 0: comun.leer_tripinfo no reconoce los flows <flow>_b<k>"
             if e.startswith("per_") else ""))
    p("5. Espera para entrar del fijo en P6e (malla3_alta_e) frente a P6 entregado, mismas semillas")
    p6e = [float(r["retraso_insercion_prom"]) for r in res[("malla3_alta_e", "fijo")][0]]
    p6 = [float(r["retraso_insercion_prom"]) for r in res[("malla3_alta", "fijo")][0]]
    ok(max(p6e) < 1.0, f"P6e: {p6e} s/veh (bajo 1 s/veh); P6 entregado: {p6} s/veh")
    with open(os.path.join(u.SALIDAS, "cargas.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    destino = os.path.join(u.SALIDAS, "cargas")        # los CSV de evaluar.py (2 filas cada uno)
    shutil.rmtree(destino, ignore_errors=True)
    os.makedirs(destino)
    for e, b in trabajos:
        shutil.copyfile(os.path.join(CARPETA, f"eval_{e}_{b}.csv"), os.path.join(destino, f"eval_{e}_{b}.csv"))
    u.limpiar_generados()
    p(f"\nResultado: {'TODO OK' if not fallas else f'{len(fallas)} FALLAS'}")
    p.guardar()
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
