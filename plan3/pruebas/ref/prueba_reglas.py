"""
prueba_reglas.py - Pruebas de la tarea 0.10 (reglas.py y evaluar.py --regla):
  1. con U = inf (regla_uinfg60) el mismo tripinfo que el ciclo minimo (brazo trivial), registro por registro
     (sha256), en P1 y P5;
  2. cada accion respeta la mascara (registro de todas las decisiones de un episodio de cada familia en P1 y P6);
  3. la presion es 0 con la red vacia (todas las fases de todos los semaforos, antes del primer paso) y no es 0 con
     trafico;
  4. evaluar.py --regla por la linea de comandos escribe su CSV con el brazo esperado.
Semillas de humo. Corre en una copia de los escenarios (tmp_ref/reglas/): el brazo trivial regenera su .add.xml en la
carpeta actual. Uso (cwd = plan3/): python pruebas/ref/prueba_reglas.py
Salida: pruebas/ref/salidas/prueba_reglas.txt
"""
import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
inf = up.Informe("prueba_reglas")
CARPETA = up.copia("reglas", ["corredor", "malla3", "malla3_alta"])
import traci  # noqa: E402
import rl_ippo  # noqa: E402
import evaluar  # noqa: E402
import reglas  # noqa: E402


def igual_ciclo_minimo(esc, semilla):
    _, _, _, trivial = evaluar.brazo_referencia(esc, "trivial")
    a = trivial(semilla, f"ti_trivial_{esc}.xml", None)
    brazo, _, _, regla = evaluar.brazo_regla(esc, "regla_uinfg60")
    b = regla(semilla, f"ti_regla_{esc}.xml", None)
    ha, hb = up.huella_tripinfo(f"ti_trivial_{esc}.xml"), up.huella_tripinfo(f"ti_regla_{esc}.xml")
    inf.chequeo(ha == hb and a["retraso_total_prom"] == b["retraso_total_prom"],
                f"1 {esc} s{semilla}: {brazo} tripinfo {hb} = ciclo minimo {ha}; retraso total "
                f"{b['retraso_total_prom']} = {a['retraso_total_prom']}, timeLoss {b['timeloss_prom']} = "
                f"{a['timeloss_prom']}")


def mascara(esc, regla, semilla):
    rl_ippo.preparar(esc)
    registro = []
    res = reglas.correr(esc, regla, semilla, f"ti_masc_{esc}_{regla}.xml", registro=registro)
    malas = [r for r in registro if (r[2][r[3]] == 0)]
    libres = sum(1 for r in registro if r[2] == (1.0, 1.0))
    forzadas = sum(1 for r in registro if r[2] == (0.0, 1.0))
    cambios = sum(r[3] for r in registro)
    inf.chequeo(not malas and registro, f"2 {esc} {regla}: {len(registro)} decisiones ({libres} libres, {forzadas} "
                                        f"forzadas por el verde maximo, {cambios} cambios), fuera de la mascara: "
                                        f"{len(malas)}; retraso total {res['retraso_total_prom']}")


def presion_vacia(esc, semilla):
    rl_ippo.preparar(esc)
    cfg = rl_ippo.C["cfg"]
    traci.start(["sumo", "-c", cfg, "--seed", str(semilla), "--no-step-log", "true", "--no-warnings", "true",
                 "--tripinfo-output", f"ti_pres_{esc}.xml"])
    geo = reglas.Geometria()
    geo.preparar()
    vacias = {(tls, f, m): reglas.presion(geo, tls, f, m) for tls in geo.verdes for f in geo.verdes[tls]
              for m in ("veh", "det")}
    n0 = traci.vehicle.getIDCount()
    for _ in range(900):
        traci.simulationStep()
    llenas = {(tls, f, m): reglas.presion(geo, tls, f, m) for tls in geo.verdes for f in geo.verdes[tls]
              for m in ("veh", "det")}
    n1 = traci.vehicle.getIDCount()
    traci.close()
    inf.chequeo(n0 == 0 and all(v == 0 for v in vacias.values()),
                f"3 {esc}: red vacia ({n0} vehiculos): presion 0 en las {len(vacias)} (semaforo, fase, medida)")
    inf.chequeo(any(v != 0 for v in llenas.values()),
                f"3 {esc}: a los 900 s ({n1} vehiculos) la presion no es 0 en "
                f"{sum(1 for v in llenas.values() if v != 0)} de {len(llenas)}")


def linea_de_comandos():
    salida = os.path.join(CARPETA, "eval_corredor_regla.csv")
    r = subprocess.run([sys.executable, os.path.join(up.RAIZ, "evaluar.py"), "--escenario", "corredor", "--regla",
                        "regla_u2g30", "--semillas", f"{up.HUMO[0]}-{up.HUMO[1]}", "--salida", salida,
                        "--extras", os.path.join(CARPETA, "extras")], capture_output=True, text=True)
    import csv
    filas = list(csv.DictReader(open(salida, encoding="utf-8"))) if os.path.exists(salida) else []
    resumen = [(f["brazo"], f["semilla"], f["retraso_total_prom"]) for f in filas]
    inf.chequeo(r.returncode == 0 and [f["brazo"] for f in filas] == ["regla_u2g30"] * 2,
                f"4 evaluar.py --regla regla_u2g30: codigo {r.returncode}, filas {resumen}")
    r = subprocess.run([sys.executable, os.path.join(up.RAIZ, "evaluar.py"), "--escenario", "corredor", "--regla",
                        "regla_x"], capture_output=True, text=True)
    inf.chequeo(r.returncode != 0, f"4 una regla desconocida se rechaza (codigo {r.returncode})")


def main():
    inf(f"Pruebas de 0.10: regla simple y Max-Pressure por el gancho decidir (copia en {CARPETA})")
    for esc in ("corredor", "malla3"):
        igual_ciclo_minimo(esc, up.HUMO[0])
    for regla in ("regla_u2g30", "regla_u6g60", "mp", "mp_det", "mp_c60", "mp_det_c90"):
        mascara("corredor", regla, up.HUMO[0])
    for regla in ("regla_u1g30", "mp_c90"):
        mascara("malla3_alta", regla, up.HUMO[0])
    presion_vacia("corredor", up.HUMO[0])
    presion_vacia("malla3_alta", up.HUMO[0])
    linea_de_comandos()
    os.chdir(up.PLAN3)
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
