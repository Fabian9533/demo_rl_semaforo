"""
prueba_fino.py - Pruebas de la tarea 0.7 (barrer_fino.py):
  A. la regla con datos inventados: minimos locales (con la gruesa de plan2/barrido_malla3.csv deben salir 10/10,
     25/15 y 30/10, los tres a <= 2 %), el umbral de 2 errores estandar con llegadas aleatorias y la regla de
     ganadores fragiles;
  B. reproduce las filas y el ganador de plan2/barrido_<esc>.csv con 2001-2003: en P1 una subrejilla completa por la
     linea de comandos (avenida 15/18/20/25 x transversal 10/15, todos sus desfases) y en P2-P6 tres filas cada uno
     (en P6 las tres del 15/10: 3 de 3); ademas, una configuracion frente a barrer_fijo.evaluar_config;
  C. dos corridas dan el mismo CSV: la misma subrejilla en otra carpeta, en dos trozos y la union, con otros
     --procesos (sha256 de gruesa.csv, gruesa_semillas.csv y del .add.xml instalado);
  D. puntaje por periodo: en P6 10/10 (que se traba) y en dos planes que dejan vehiculos sin entrar a los 6000 s
     (P6 10/25 y P2 10/25), la suma por periodo es igual al total de comun.leer_tripinfo sin write-undeparted, las
     metricas de la hora son las mismas, los no insertados por periodo suman los de las estadisticas y su salida
     programada (fin - departDelay) es la de su flujo.
Uso (cwd = plan3/): python pruebas/ref/prueba_fino.py      Salida: pruebas/ref/salidas/prueba_fino.txt
Semillas: 2001-2003 en B y C (las del barrido entregado, para reproducirlo); humo en D.
"""
import os
import sys
import csv
import shutil
import statistics
import subprocess
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
import barrer_fijo as bf  # noqa: E402
import barrer_fino as bfn  # noqa: E402

inf = up.Informe("prueba_fino")
PLAN2 = os.path.join(up.RAIZ, "plan2")
COLUMNAS = ["verde", "izquierda", "verde_transversal", "offsets", "retraso_total_prom", "timeloss_prom",
            "retraso_insercion_prom", "espera_prom", "paradas_prom", "throughput", "co2_prom", "retraso_total_sd",
            "timeloss_sd", "semillas"]
SUBREJILLA = ["--avenida", "15,18,20,25", "--transversal", "10,15"]


def leer_csv(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def celda(esc, sub):
    c = bfn.Celda(esc, prefijos=())
    c.tmp = os.path.join(up.TMP, "fino", sub, "tmp_fino")
    c.carpeta = os.path.join(up.TMP, "fino", sub, "barridos")
    return c


# ---------------------------------------------------------------- A
def prueba_regla():
    filas = leer_csv(os.path.join(PLAN2, "barrido_malla3.csv"))
    for f in filas:
        for k in ("verde", "verde_transversal"):
            f[k] = int(f[k])
        f["retraso_total_prom"] = float(f["retraso_total_prom"])
    mins = bfn.minimos_locales(filas)
    mejor = mins[0][0]
    dentro = [(a, t) for v, a, t, _ in mins if v <= 1.02 * mejor][:3]
    inf.chequeo(dentro == [(10, 10), (25, 15), (30, 10)],
                f"A malla3 (plan2): minimos locales {[(a, t, v) for v, a, t, _ in mins]}; a <= 2 %: {dentro}")
    # umbral de 2 errores estandar (llegadas aleatorias) con resultados inventados
    c = celda("corredor", "regla")
    c.aleatorias, c.llegadas = True, "aleatorias"
    c.semillas["barrido"] = list(range(1, 11))
    mejor_pl, otro, lejos = {"clave": "a"}, {"clave": "b"}, {"clave": "c"}
    ruido = [0.5, -0.4, 0.9, -1.1, 0.2, 0.0, 1.3, -0.8, 0.6, -0.2]
    for s, e in zip(range(1, 11), ruido):
        c.conocidas[("a", s)] = {"retraso_total_prom": 30.0}
        c.conocidas[("b", s)] = {"retraso_total_prom": 30.3 + e}        # diferencia media 0.4, ee ~0.24
        c.conocidas[("c", s)] = {"retraso_total_prom": 31.5 + e / 4}    # diferencia media 1.5, ee ~0.06
    d_b = [30.3 + e - 30.0 for e in ruido]
    ee_b = statistics.stdev(d_b) / 10 ** 0.5
    ok = (bfn.dentro_del_umbral(c, otro, mejor_pl, 30.4, 30.0)
          and not bfn.dentro_del_umbral(c, lejos, mejor_pl, 31.5, 30.0)
          and bfn.dentro_del_umbral(c, mejor_pl, mejor_pl, 30, 30))
    inf.chequeo(ok, f"A llegadas aleatorias: +0.4 s con ee {ee_b:.2f} pasa a la fina; +1.5 s con ee 0.06 no (aunque "
                    f"a 2 % pasaria); el mejor siempre")
    c.aleatorias = False
    ok = bfn.dentro_del_umbral(c, otro, mejor_pl, 30.6, 30.0) and not bfn.dentro_del_umbral(c, lejos, mejor_pl,
                                                                                           30.61, 30.0)
    inf.chequeo(ok, "A llegadas regulares: 30.6 frente a 30.0 pasa (2 %), 30.61 no")
    # regla de fragiles (sin correr nada: dos primeros lejos y sin semillas trabadas)
    filas = [{"retraso_total_prom": 30.0, "trabadas": 0, "semillas": "x"}, {"retraso_total_prom": 31.0,
                                                                          "trabadas": 0, "semillas": "x"}]
    _, _, traza = bfn.regla_fragil(c, filas, [{"clave": "a"}, {"clave": "b"}], "x")
    inf.chequeo(not traza["fragil"], f"A fragil: dos primeros a 3.3 % y sin semillas trabadas -> no fragil {traza}")


def fragil_con_datos():
    """La regla de fragiles corre de verdad (dos casos) con resultados inventados y semillas de humo."""
    c = celda("corredor", "fragil")
    c.semillas.update(desempate=[1, 2, 3, 4], fragil=[1, 2, 3, 4, 5, 6])
    # desempate (1-4): a 30.0 con una semilla trabada (33 > 1.10 x 29), b 31.0 (a 3.3 %), x 31.5;
    # con 1-6: a 30.33, b 30.0, x 31.5 -> gana b
    for clave, vals in (("a", [29, 29, 29, 33, 31, 31]), ("b", [31, 31, 31, 31, 28, 28]), ("x", [31.5] * 6)):
        for s, v in zip(range(1, 7), vals):
            c.conocidas[(clave, s)] = {m: v for m in bfn.METRICAS} | {
                **{f"total_p{k}": v for k in (1, 2)}, **{f"noins_p{k}": 0 for k in (1, 2)}}
    pls = [c.plan(20, 10, [0, 15]) | {"clave": k} for k in ("a", "b", "x")]
    os.makedirs(c.tmp, exist_ok=True)              # los resultados inventados valen para el programa de esos planes
    ruta = os.path.join(c.tmp, "inventado.add.xml")
    c.escribir_plan(ruta, pls[0])
    for clave, s in list(c.conocidas):
        c.programa[(clave, s)] = up.sha256(ruta)[:12]
    filas, planes = c.escribir_etapa("desempate", pls, c.semillas["desempate"], "desempate")
    fila, pl, traza = bfn.regla_fragil(c, filas, planes, "fragil")
    inf.chequeo(traza["fragil"] and traza["semillas_trabadas_ganador"] == 1 and pl["clave"] == "b",
                f"A fragil: el ganador del desempate ({filas[0]['clave']} {filas[0]['retraso_total_prom']}) tiene una "
                f"semilla trabada -> 3 primeros con 6 semillas: gana {pl['clave']} {fila['retraso_total_prom']}")


# ---------------------------------------------------------------- B y C
def cli(carpeta, *args):
    r = subprocess.run([sys.executable, os.path.join(up.PLAN3, "barrer_fino.py"), "corredor", *args],
                       cwd=carpeta, capture_output=True, text=True)
    if r.returncode != 0:
        inf(r.stdout[-2000:] + r.stderr[-3000:])
    return r.returncode


def reproducir_p1():
    a = os.path.join(up.TMP, "fino", "p1_a")
    shutil.rmtree(a, ignore_errors=True)
    os.chdir(up.PLAN3)
    destino = up.copia(os.path.join("fino", "p1_a"), ["corredor"])
    os.chdir(up.PLAN3)
    cod = cli(destino, "--etapa", "gruesa", "--procesos", "3", *SUBREJILLA)
    mias = leer_csv(os.path.join(destino, "barridos", "corredor", "gruesa.csv"))
    plan2 = {(f["verde"], f["verde_transversal"], f["offsets"]): f
             for f in leer_csv(os.path.join(PLAN2, "barrido_corredor.csv"))}
    iguales = sum(1 for f in mias if all(f[k] == plan2[(f["verde"], f["verde_transversal"], f["offsets"])][k]
                                          for k in COLUMNAS))
    inf.chequeo(cod == 0 and iguales == len(mias) and len(mias) > 50,
                f"B P1: subrejilla de {len(mias)} planes por la linea de comandos: {iguales}/{len(mias)} filas iguales "
                f"a plan2/barrido_corredor.csv (14 columnas)")
    g2 = leer_csv(os.path.join(PLAN2, "barrido_corredor.csv"))[0]
    inf.chequeo(all(mias[0][k] == g2[k] for k in COLUMNAS),
                f"B P1: ganador {mias[0]['verde']}/{mias[0]['verde_transversal']} {mias[0]['offsets']} "
                f"{mias[0]['retraso_total_prom']} = ganador de plan2 {g2['verde']}/{g2['verde_transversal']} "
                f"{g2['offsets']} {g2['retraso_total_prom']}")
    return destino


def mismo_csv(destino_a):
    b = os.path.join(up.TMP, "fino", "p1_b")
    shutil.rmtree(b, ignore_errors=True)
    destino = up.copia(os.path.join("fino", "p1_b"), ["corredor"])
    os.chdir(up.PLAN3)
    cods = [cli(destino, "--etapa", "gruesa", "--trozo", "0/2", "--procesos", "2", *SUBREJILLA),
            cli(destino, "--etapa", "gruesa", "--trozo", "1/2", "--procesos", "1", *SUBREJILLA),
            cli(destino, "--etapa", "gruesa", "--procesos", "1", *SUBREJILLA)]
    salida = []
    for rel in ("barridos/corredor/gruesa.csv", "barridos/corredor/gruesa_semillas.csv", "corredor_r10g.add.xml",
                "barridos/corredor/fijo_grueso10.json"):
        ha, hb = up.sha256(os.path.join(destino_a, rel)), up.sha256(os.path.join(destino, rel))
        salida.append(ha == hb)
        inf(f"  C {rel}: {ha[:16]} / {hb[:16]}")
    inf.chequeo(cods == [0, 0, 0] and all(salida),
                f"C dos corridas (una con 3 hilos; otra en 2 trozos y la union) dan los mismos archivos: {salida}")


def filas_p2_p6():
    casos = {"P2": "corredor_alta", "P3": "red", "P4": "red_alta", "P5": "malla3", "P6": "malla3_alta"}
    for caso, esc in casos.items():
        c = celda(esc, "filas")
        filas = leer_csv(os.path.join(PLAN2, f"barrido_{esc}.csv"))
        elegidas = [f for f in filas if (f["verde"], f["verde_transversal"]) == ("15", "10")] if esc == "malla3_alta" \
            else filas[:3]
        planes = []
        for f in elegidas:
            pl = c.plan(int(f["verde"]), int(f["verde_transversal"]), [int(o) for o in f["offsets"].split("/")],
                        f.get("esquema", ""))
            planes.append(pl)
        c.procesos = 3
        c.asegurar(planes, [2001, 2002, 2003], "filas")
        n = 0
        for pl, f in zip(planes, elegidas):
            mia = c.fila(pl, [2001, 2002, 2003], "x")
            cols = COLUMNAS + (["esquema"] if c.malla else [])
            n += all(str(mia[k]) == f[k] for k in cols)
        nombres = ", ".join(f"{f['verde']}/{f['verde_transversal']} {f.get('esquema', f['offsets'])}" for f in elegidas)
        inf.chequeo(n == len(elegidas), f"B {caso}: {n} de {len(elegidas)} filas de plan2/barrido_{esc}.csv "
                                        f"reproducidas ({nombres})")
    c = celda("corredor_alta", "evaluar_config")
    ref, mia = bfn.comprobar_lector(c, c.plan(25, 15, [0, 25]), [2001, 2002, 2003])
    inf.chequeo(ref == mia, f"B P2 25/15 0/25: barrer_fijo.evaluar_config {ref['retraso_total_prom']} = barrer_fino "
                            f"{mia['retraso_total_prom']} en las 9 columnas: {ref == mia}")


# ---------------------------------------------------------------- D
def programadas_de_flujos(cfg):
    """{flujo: (begin, periodo)} de los <flow> con vehsPerHour."""
    _, rutas, _ = bfn.rutas_cfg(cfg)
    salida = {}
    for r in rutas:
        for el in ET.parse(r).getroot().iter("flow"):
            if el.get("vehsPerHour"):
                salida[el.get("id")] = (float(el.get("begin")), 3600.0 / float(el.get("vehsPerHour")))
    return salida


def periodos(esc, a, t, esquema, semilla):
    c = celda(esc, "periodos")
    os.makedirs(c.tmp, exist_ok=True)
    offs = c.desfases_esquema(c.p.ciclo(a, t), esquema) if esquema else [0] * len(c.p.ids)
    pl = c.plan(a, t, offs, esquema)
    ruta = os.path.join(c.tmp, f"{esc}_{a}_{t}.add.xml")
    c.escribir_plan(ruta, pl)
    ref = bf.correr_sumo(c.cfg, c.p.extra(ruta), semilla, os.path.join(c.tmp, f"ti_ref_{esc}_{a}_{t}.xml"))
    mia = bfn.correr_periodos(c.cfg, c.p.extra(ruta), semilla, os.path.join(c.tmp, f"ti_mia_{esc}_{a}_{t}.xml"),
                              c.cortes)
    iguales = all(ref[m] == mia[m] for m in bfn.METRICAS + bfn.EXTRA_CORRIDA)
    suma = round(mia["total_periodos"], 2) == ref["retraso_total_prom"]
    cuenta = mia["n_p1"] + mia["n_p2"] == ref["vehiculos"] + ref["no_insertados"]
    noins = mia["noins_p1"] + mia["noins_p2"] == ref["no_insertados"]
    # salida programada de los no insertados frente a su flujo (una corrida con write-undeparted aparte)
    todo = os.path.join(c.tmp, f"ti_todo_{esc}_{a}_{t}.xml")
    subprocess.run(["sumo", "-c", c.cfg, "--seed", str(semilla), "--tripinfo-output", todo,
                    "--tripinfo-output.write-unfinished", "true", "--tripinfo-output.write-undeparted", "true",
                    "--no-step-log", "true", "--no-warnings", "true", "--end", str(bf.FIN_SIM)] + c.p.extra(ruta),
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    flujos = programadas_de_flujos(c.cfg)
    errores = []
    for v in ET.parse(todo).getroot().findall("tripinfo"):
        if float(v.get("depart")) < 0:
            flujo, k = v.get("id").rsplit(".", 1)
            if flujo in flujos:
                b, per = flujos[flujo]
                errores.append(abs((mia["fin"] - float(v.get("departDelay"))) - (b + int(k) * per)))
    os.remove(todo)
    inf.chequeo(iguales and suma and cuenta and noins and (not errores or max(errores) <= 0.01),
                f"D {esc} {a}/{t} {esquema} s{semilla}: total sin write-undeparted {ref['retraso_total_prom']} = suma "
                f"por periodo {mia['total_periodos']} ({mia['total_p1']} y {mia['total_p2']}); hora igual: {iguales}; "
                f"no insertados {ref['no_insertados']} = {mia['noins_p1']} + {mia['noins_p2']}; su salida programada "
                f"(fin - departDelay) frente al flujo: error maximo "
                f"{max(errores) if errores else 0:.3f} s en {len(errores)}")


def main():
    inf("Pruebas de 0.7: barrido fino con puntaje por periodo")
    prueba_regla()
    fragil_con_datos()
    destino_a = reproducir_p1()
    mismo_csv(destino_a)
    os.chdir(up.PLAN3)
    filas_p2_p6()
    periodos("malla3_alta", 10, 10, "cero", up.HUMO[0])
    periodos("malla3_alta", 10, 25, "cero", up.HUMO[0])
    periodos("corredor_alta", 10, 25, "", up.HUMO[0])
    os.chdir(up.PLAN3)
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
