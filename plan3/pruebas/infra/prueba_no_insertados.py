"""
prueba_no_insertados.py - comun.ESCRIBIR_NO_INSERTADOS no cambia ninguna metrica y da las filas de los no insertados.

Uso (desde plan3/):  python pruebas/infra/prueba_no_insertados.py   -> pruebas/infra/prueba_no_insertados.txt
P2 (corredor_alta) cortado a los 900 s con el fijo instalado, semilla de humo 424301: quedan vehiculos sin entrar.
  1. comun.leer_tripinfo da exactamente lo mismo con y sin las filas de los no insertados;
  2. esas filas (depart < 0) son tantas como los no insertados del archivo de estadisticas;
  3. evaluar3.por_periodo cuenta insertados + no insertados = cargados, y reparte el retraso por periodo.
"""
import os
import sys
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN3 = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.dirname(PLAN3))
sys.path.insert(0, PLAN3)
import comun            # noqa: E402
import evaluar3         # noqa: E402
import xml.etree.ElementTree as ET  # noqa: E402

TMP = os.path.join(PLAN3, "tmp_noins")


def correr(con):
    comun.ESCRIBIR_NO_INSERTADOS = con
    ti = os.path.join(TMP, f"tripinfo_{'con' if con else 'sin'}.xml")
    cmd = ["sumo", "-c", os.path.join(PLAN3, "corredor_alta.sumocfg"), "--seed", "424301", "--end", "900",
           "--tripinfo-output", ti, "--tripinfo-output.write-unfinished", "true", "--no-step-log", "true",
           "--no-warnings", "true"] + comun.args_estadisticas(ti)
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return ti


def main():
    os.makedirs(TMP, exist_ok=True)
    sin, con = correr(False), correr(True)
    comun.ESCRIBIR_NO_INSERTADOS = False
    lineas, malos = [], 0

    def revisar(desc, cond):
        nonlocal malos
        malos += not cond
        lineas.append(f"{'ok ' if cond else 'MAL'} {desc}")
    a, b = comun.leer_tripinfo(sin), comun.leer_tripinfo(con)
    revisar(f"leer_tripinfo igual con y sin las filas de los no insertados ({a['no_insertados']} no insertados, "
            f"retraso total {a['retraso_total_prom']})", a == b and a["no_insertados"] > 0)
    filas = ET.parse(con).getroot().findall("tripinfo")
    neg = sum(1 for v in filas if float(v.get("depart", 0)) < 0)
    revisar(f"filas con depart < 0 = no insertados ({neg})", neg == b["no_insertados"])
    revisar("sin la opcion no hay filas con depart < 0",
            all(float(v.get("depart", 0)) >= 0 for v in ET.parse(sin).getroot().findall("tripinfo")))
    fin = evaluar3.fin_de_simulacion(con)
    p = evaluar3.por_periodo(con, fin)
    cargados = int(ET.parse(comun.ruta_estadisticas(con)).getroot().find("vehicles").get("loaded"))
    revisar(f"por_periodo: generados {p['generados']} = cargados {cargados}; no insertados "
            f"{p['no_insertados_p1'] + p['no_insertados_p2']}", p["generados"] == cargados
            and p["no_insertados_p1"] + p["no_insertados_p2"] == b["no_insertados"])
    texto = "\n".join(lineas)
    print(texto)
    open(os.path.join(AQUI, "prueba_no_insertados.txt"), "w", encoding="utf-8").write(texto + "\n")
    sys.exit(1 if malos else 0)


if __name__ == "__main__":
    main()
