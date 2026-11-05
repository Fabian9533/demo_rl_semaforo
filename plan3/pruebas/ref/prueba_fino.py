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
     programada (fin - departDelay) es la de su flujo;
  E. la huella de la cache: en una copia del codigo (comun, barrer_fijo, escenarios_plan2 y barrer_fino), repetir no
     corre nada; cambiar solo los fines de linea de comun.py tampoco; un cambio en comun.py (un comentario) cambia la
     huella y se vuelve a correr todo, con los mismos numeros; ESCRIBIR_NO_INSERTADOS y QUITAR_BLOQUE la cambian;
  F. la cadena de etapas (sin sumo, con resultados inventados): la fina se niega a leer una gruesa con opciones de
     prueba y la acepta con --permitir-prueba (y su salida queda marcada); una gruesa con el registro de la regla pero
     otras semillas tambien se niega; la etapa fragil lee el desempate sin reescribirlo (mismo sha256 y misma fecha) y
     se niega si desempate.csv no es el de las etapas o si sus semillas no son las de la regla; desde la raiz se niega
     (cwd) y una opcion abreviada no se acepta; correr_periodos niega las semillas del examen y de la final antes de
     lanzar sumo (con sumo reemplazado: no se simula ninguna).
Uso (cwd = plan3/): python pruebas/ref/prueba_fino.py      Salida: pruebas/ref/salidas/prueba_fino.txt
Semillas: 2001-2003 en B y C (las del barrido entregado, para reproducirlo); humo en D y E; en F nada corre (los
numeros son inventados, con los nombres de las semillas de la regla).
"""
import os
import re
import sys
import csv
import json
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
    # el borde exacto del 2 %, en centesimas enteras (a_2pct: la fina y la regla de fragiles usan la misma)
    malos, viejos, bordes = [], 0, 0
    for p in range(500, 10000):                       # el mejor, de 5.00 a 99.99 s, en centesimas
        tope = p + (2 * p) // 100                     # el mayor valor a <= 2 % (aritmetica entera)
        mejor, dentro, fuera = round(p / 100, 2), round(tope / 100, 2), round((tope + 1) / 100, 2)
        if not bfn.a_2pct(dentro, mejor) or bfn.a_2pct(fuera, mejor):
            malos.append((mejor, dentro, fuera))
        if (2 * p) % 100 == 0:                        # borde exacto: el segundo queda justo a 2.00 %
            bordes += 1
            viejos += not (dentro - mejor <= 0.02 * mejor)
    inf.chequeo(not malos, f"A a_2pct en el borde: con el mejor de 5.00 a 99.99 s (9500 casos), el mayor valor a "
                           f"<= 2 % entra y el centesimo siguiente no: fallas {malos[:3]}; la comparacion de antes "
                           f"(segundo - primero <= 0.02 x primero) dejaba fuera {viejos} de los {bordes} bordes "
                           f"exactos")
    ejemplos = [(20.50, 20.91, True), (20.50, 20.92, False), (30.00, 30.60, True), (30.00, 30.61, False)]
    inf.chequeo(all(bfn.a_2pct(v, m) == e for m, v, e in ejemplos),
                f"A ejemplos de la revision (mejor, valor, a <= 2 %): "
                f"{[(m, v, bfn.a_2pct(v, m)) for m, v, _ in ejemplos]}; la fina: "
                f"{[bfn.dentro_del_umbral(c, otro, mejor_pl, v, m) for m, v, _ in ejemplos]}")
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
    # el borde exacto: a 20.50 y b 20.91 (2.00 %), sin semillas trabadas -> fragil; con b 20.92 -> no
    c2 = celda("corredor", "fragil_borde")
    c2.semillas.update(desempate=[1, 2], fragil=[1, 2, 3])
    for clave, vals in (("a", [20.5, 20.5, 21.1]), ("b", [20.91, 20.91, 20.2]), ("x", [22.0] * 3)):
        for s, v in zip((1, 2, 3), vals):
            c2.conocidas[(clave, s)] = {m: v for m in bfn.METRICAS} | {
                **{f"total_p{k}": v for k in (1, 2)}, **{f"noins_p{k}": 0 for k in (1, 2)}}
            c2.programa[(clave, s)] = up.sha256(ruta)[:12]
    os.makedirs(c2.tmp, exist_ok=True)
    filas, planes = c2.escribir_etapa("desempate", pls, [1, 2], "desempate")
    fila, pl, traza = bfn.regla_fragil(c2, filas, planes, "fragil")
    lejos = [dict(filas[0]), dict(filas[1], retraso_total_prom=20.92)]
    _, _, traza2 = bfn.regla_fragil(c2, lejos, planes, "fragil_lejos")
    inf.chequeo(traza["dos_primeros_a_2pct"] and traza["fragil"] and pl["clave"] == "b"
                and not traza2["dos_primeros_a_2pct"] and not traza2["fragil"],
                f"A fragil en el borde: 20.50 y 20.91 (2.00 %) -> fragil, 3 primeros con 3 semillas, gana "
                f"{pl['clave']} {fila['retraso_total_prom']}; 20.50 y 20.92 -> no fragil")


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


# ---------------------------------------------------------------- E. huella de la cache
def copia_de_codigo():
    """tmp_ref/fino/huella/: una raiz con comun.py, barrer_fijo.py y escenarios_plan2.py, y su plan3/ con
    barrer_fino.py y el corredor. barrer_fino de la copia importa el codigo de la copia."""
    base = os.path.join(up.TMP, "fino", "huella")
    shutil.rmtree(base, ignore_errors=True)
    p3 = os.path.join(base, "plan3")
    os.makedirs(p3)
    for f in ("comun.py", "barrer_fijo.py", "escenarios_plan2.py"):
        shutil.copyfile(os.path.join(up.RAIZ, f), os.path.join(base, f))
    shutil.copyfile(os.path.join(up.PLAN3, "barrer_fino.py"), os.path.join(p3, "barrer_fino.py"))
    for rel in up.archivos_de_cfg(os.path.join(up.PLAN3, "corredor.sumocfg")):
        shutil.copyfile(os.path.join(up.PLAN3, rel), os.path.join(p3, rel))
    return base, p3


def gruesa_en(p3, *extra):
    """La gruesa chica de la copia (2 planes, 1 semilla de humo): (codigo, huella, corridas, sha256 de gruesa.csv,
    salida)."""
    args = ["corredor", "--etapa", "gruesa", "--avenida", "20", "--transversal", "10", "--limite", "2",
            "--semillas", str(up.HUMO[0]), *extra]
    r = subprocess.run([sys.executable, os.path.join(p3, "barrer_fino.py"), *args], cwd=p3, capture_output=True,
                       text=True)
    if r.returncode != 0:
        inf(r.stdout[-1500:] + r.stderr[-1500:])
        return r.returncode, None, None, None, r.stdout
    with open(os.path.join(p3, "barridos", "corredor", "fijo_grueso10.json"), encoding="utf-8") as f:
        huella = json.load(f)["huella"]
    corridas = sum(int(m.group(1)) for m in re.finditer(r"(\d+) corridas en", r.stdout))
    return r.returncode, huella, corridas, up.sha256(os.path.join(p3, "barridos", "corredor", "gruesa.csv")), r.stdout


def huella_de_la_cache():
    base, p3 = copia_de_codigo()
    cod1, h1, n1, csv1, _ = gruesa_en(p3)
    cod2, h2, n2, csv2, _ = gruesa_en(p3)
    inf.chequeo(cod1 == cod2 == 0 and n1 == 2 and n2 == 0 and h1 == h2 and csv1 == csv2,
                f"E copia del codigo: la gruesa chica corre {n1} corridas (huella {h1}); repetirla corre {n2} "
                f"(huella {h2}), mismo gruesa.csv")
    comun_copia = os.path.join(base, "comun.py")
    with open(comun_copia, "rb") as f:
        crudo = f.read()
    otro_fin = crudo.replace(b"\r\n", b"\n") if b"\r\n" in crudo else crudo.replace(b"\n", b"\r\n")
    with open(comun_copia, "wb") as f:
        f.write(otro_fin)
    cod3, h3, n3, csv3, _ = gruesa_en(p3)
    fines = "LF" if b"\r\n" in crudo else "CRLF"
    inf.chequeo(cod3 == 0 and h3 == h1 and n3 == 0,
                f"E comun.py de la copia con los otros fines de linea ({fines}): misma huella {h3}, {n3} corridas")
    with open(comun_copia, "ab") as f:
        f.write(b"# cambio de prueba (prueba_fino E): un comentario basta para cambiar la huella\n")
    cod4, h4, n4, csv4, salida = gruesa_en(p3)
    inf.chequeo(cod4 == 0 and h4 != h1 and n4 == 2 and csv4 == csv1,
                f"E comun.py de la copia cambiado: huella {h1} -> {h4}, vuelve a correr {n4} corridas, gruesa.csv "
                f"igual byte a byte (los numeros no cambian)")
    import comun
    h0 = bfn.huella_escenario("corredor.sumocfg")
    comun.ESCRIBIR_NO_INSERTADOS = True
    h_ni = bfn.huella_escenario("corredor.sumocfg")
    comun.ESCRIBIR_NO_INSERTADOS = False
    comun.QUITAR_BLOQUE = True
    h_qb = bfn.huella_escenario("corredor.sumocfg")
    comun.QUITAR_BLOQUE = False
    inf.chequeo(len({h0, h_ni, h_qb}) == 3 and bfn.huella_escenario("corredor.sumocfg") == h0,
                f"E interruptores de comun: huella {h0}; con ESCRIBIR_NO_INSERTADOS {h_ni}; con QUITAR_BLOQUE {h_qb}")


# ---------------------------------------------------------------- F. cadena de etapas
def cadena_con_la_gruesa_de_prueba():
    """La gruesa chica de E (opciones de prueba) en una copia nueva del codigo de hoy (la de E quedo con comun.py
    cambiado): la fina se niega sin --permitir-prueba; con permitir la lee y marca su salida; con el registro de la
    regla pero otras semillas tambien se niega."""
    _, p3 = copia_de_codigo()
    gruesa_en(p3)
    r = subprocess.run([sys.executable, os.path.join(p3, "barrer_fino.py"), "corredor", "--etapa", "fina"],
                       cwd=p3, capture_output=True, text=True)
    texto = r.stdout + r.stderr
    inf.chequeo(r.returncode != 0 and "no es de la regla" in texto and "opciones de prueba" in texto,
                f"F la fina se niega a leer una gruesa con opciones de prueba: codigo {r.returncode}; "
                f"{texto.strip().splitlines()[-1][:220] if texto.strip() else ''}")
    os.chdir(p3)
    c = bfn.Celda("corredor", permitir=True)
    planes = bfn.planes_gruesa(c)
    inf.chequeo(len(planes) == 2 and any(p.startswith("entrada de prueba") for p in c.prueba),
                f"F con --permitir-prueba la lee ({len(planes)} planes) y su salida queda marcada: {c.prueba}")
    ruta = os.path.join("barridos", "corredor", "fijo_grueso10.json")
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    ejes, extra = bfn.pares_gruesa(c)
    datos["registro"] = {"llegadas": "regulares", "semillas": {"barrido": "2001-2003"}, "ejes_iniciales": ejes,
                         "desplegado": sorted(list(p) for p in extra), "limite": None, "prueba": []}
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f)
    try:
        bfn.planes_gruesa(bfn.Celda("corredor"))
        mensaje = "no se nego"
    except SystemExit as e:
        mensaje = str(e)
    inf.chequeo("otras semillas" in mensaje and "2001-2003" in mensaje,
                f"F una gruesa con el registro de la regla pero corrida con {up.HUMO[0]} tambien se niega: "
                f"{mensaje[:200]}")
    os.chdir(up.PLAN3)


def invento(c, planes, semillas, base):
    """Resultados inventados (sin sumo) para cada plan y semilla, validos para el programa de cada plan."""
    os.makedirs(c.tmp, exist_ok=True)
    for i, pl in enumerate(planes):
        ruta = os.path.join(c.tmp, f"inventado_{i}.add.xml")
        c.escribir_plan(ruta, pl)
        sha = up.sha256(ruta)[:12]
        for s in semillas:
            v = base + 0.37 * i + 0.11 * ((s * 7 + i * 3) % 5)
            c.conocidas[(pl["clave"], s)] = {**{m: round(v, 4) for m in bfn.METRICAS}, "throughput": 1000,
                                            **{m: 0 for m in bfn.EXTRA_CORRIDA}, "fin": 3700.0,
                                            "total_periodos": round(v, 4),
                                            **{f"total_p{k}": round(v, 4) for k in (1, 2)},
                                            **{f"n_p{k}": 100 for k in (1, 2)}, **{f"noins_p{k}": 0 for k in (1, 2)}}
            c.programa[(pl["clave"], s)] = sha


def fragil_lee_el_desempate():
    carpeta = os.path.join(up.TMP, "fino", "cadena_inventada")
    shutil.rmtree(carpeta, ignore_errors=True)
    os.chdir(up.PLAN3)
    up.copia(os.path.join("fino", "cadena_inventada"), ["corredor"])
    c = bfn.Celda("corredor")
    todas = list(range(2001, 2031))
    gruesa = [c.plan(a, 10, [0, o]) for a in (20, 25) for o in (0, 5, 10, 15)]
    fina = [c.plan(a, 11, [0, o]) for a in (21, 22) for o in (5, 10)]
    desfases = [c.plan(21, 11, [0, o]) for o in (3, 4, 6, 7)]
    invento(c, gruesa, todas, 20.0)
    invento(c, fina, todas, 20.1)
    invento(c, desfases, todas, 20.2)
    barrido = c.semillas["barrido"]
    filas_g, planes_g = c.escribir_etapa("gruesa", gruesa, barrido, "gruesa")
    ejes, extra = bfn.pares_gruesa(c)
    bfn.instalar(c, planes_g[0], filas_g[0], "r10g", "fijo_grueso10", "gruesa inventada (prueba_fino F)", {},
                 c.registro(ejes_iniciales=ejes, desplegado=sorted(list(p) for p in extra), limite=None))
    c.escribir_etapa("fina", fina, barrido, "fina")
    c.escribir_etapa("desfases", desfases, barrido, "desfases")
    bfn.etapa_desempate(c)
    des = [os.path.join(c.carpeta, f) for f in ("desempate.csv", "desempate_semillas.csv")]
    antes = [(up.sha256(r), os.stat(r).st_mtime_ns) for r in des]
    bfn.etapa_fragil(c)
    despues = [(up.sha256(r), os.stat(r).st_mtime_ns) for r in des]
    fino = bfn.leer_json(os.path.join(c.carpeta, "fijo_fino.json"))
    inf.chequeo(antes == despues and os.path.exists("corredor_r10f.add.xml") and fino["registro"]["prueba"] == [],
                f"F fragil lee el desempate sin reescribirlo: desempate.csv y desempate_semillas.csv con el mismo "
                f"sha256 y la misma fecha; fijo fino {fino['clave']} {fino['retraso_total_prom']} "
                f"({fino['semillas']}), registro sin marca de prueba")
    filas = bfn.leer_csv(des[0])
    filas[0], filas[1] = filas[1], filas[0]
    bfn.escribir_csv(des[0], list(filas[0]), filas)
    try:
        bfn.etapa_fragil(bfn.Celda("corredor"))
        mensaje = "no se nego"
    except SystemExit as e:
        mensaje = str(e)
    inf.chequeo("no es el desempate" in mensaje, f"F desempate.csv en otro orden: fragil se niega: {mensaje[:160]}")
    filas[0], filas[1] = filas[1], filas[0]
    bfn.escribir_csv(des[0], list(filas[0]), filas)
    semillas = [f for f in bfn.leer_csv(des[1]) if f["semilla"] != "2010"]
    bfn.escribir_csv(des[1], list(semillas[0]), semillas)
    try:
        bfn.etapa_fragil(bfn.Celda("corredor"))
        mensaje = "no se nego"
    except SystemExit as e:
        mensaje = str(e)
    inf.chequeo("otras semillas" in mensaje, f"F desempate sin la semilla 2010: fragil se niega: {mensaje[:200]}")
    os.chdir(up.PLAN3)


def fuera_de_plan3():
    """exigir_cwd: desde la raiz del repositorio se niega antes de escribir nada."""
    r = subprocess.run([sys.executable, os.path.join(up.PLAN3, "barrer_fino.py"), "corredor", "--etapa", "gruesa"],
                       cwd=up.RAIZ, capture_output=True, text=True)
    inf.chequeo(r.returncode != 0 and "cwd = plan3/" in (r.stdout + r.stderr)
                and not os.path.exists(os.path.join(up.RAIZ, "barridos")),
                f"F desde la raiz (donde tambien hay corredor.sumocfg) se niega: codigo {r.returncode}")
    r = subprocess.run([sys.executable, os.path.join(up.PLAN3, "barrer_fino.py"), "corredor", "--etapa", "gruesa",
                        "--sem", "2001"], cwd=up.PLAN3, capture_output=True, text=True)
    inf.chequeo(r.returncode == 2 and "unrecognized arguments: --sem" in r.stderr,
                f"F una opcion abreviada (--sem) no se acepta: codigo {r.returncode}")


def semillas_ciegas():
    """comun.revisar_semilla_ciega antes del sumo de barrer_fino.correr_periodos. Sin sumo: subprocess.run se
    reemplaza por uno que solo anota la semilla, asi ninguna semilla del examen o de la final llega a simularse."""
    llamadas, resultados = [], []

    class Lanzado(Exception):
        pass

    def falso(cmd, *a, **k):
        llamadas.append(cmd[cmd.index("--seed") + 1])
        raise Lanzado()
    real, uso = bfn.subprocess.run, os.environ.pop("P3_USO", None)
    bfn.subprocess.run = falso
    try:
        for semilla in (7001, 8001, 13120, up.HUMO[0]):
            try:
                bfn.correr_periodos("corredor.sumocfg", [], semilla, os.path.join(up.TMP, "ti_ciega.xml"), [1800],
                                    intentos=1)
                resultados.append((semilla, "corrio"))
            except SystemExit:
                resultados.append((semilla, "negada"))
            except Lanzado:
                resultados.append((semilla, "llega a sumo"))
    finally:
        bfn.subprocess.run = real
        if uso is not None:
            os.environ["P3_USO"] = uso
    inf.chequeo(resultados == [(7001, "negada"), (8001, "negada"), (13120, "negada"), (up.HUMO[0], "llega a sumo")]
                and llamadas == [str(up.HUMO[0])],
                f"F semillas del examen y de la final: correr_periodos las niega antes de lanzar sumo (sumo "
                f"reemplazado: "
                f"nada se simula): {resultados}")


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
    huella_de_la_cache()
    os.chdir(up.PLAN3)
    cadena_con_la_gruesa_de_prueba()
    fragil_lee_el_desempate()
    fuera_de_plan3()
    os.chdir(up.PLAN3)
    semillas_ciegas()
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
