"""
curvas_demanda.py - Curva de demanda de IPPO con mensajes en cada red (entrega 3, tarea 5).

Uso (desde demo_rl/):
  python curvas_demanda.py                   lee plan2/ y escribe el resumen, la tabla y la figura
  python curvas_demanda.py --veredicto DIR   usa el veredicto.py de la carpeta DIR (p. ej. una copia de la
                                             version commiteada) en lugar del de esta carpeta

Junta los 12 niveles de demanda nuevos (escenarios dem_<red>_t<veh/h> de escenarios_plan2.NIVELES_DEMANDA2:
corredor 905, 1358 y 2715; red con rotonda 905, 1358, 1810, 2715 y 3620; malla 1810, 2715, 3620 y 6525 veh/h)
con los seis casos del plan, que son un punto mas de la curva de su red: P1 corredor 1810, P2 corredor 3620,
P3 red 2150, P4 red 2580, P5 malla 4350 y P6 malla 8700 veh/h.

Lee de plan2/:
  evaluacion_dem_<esc>_resumen.csv      consolidar.py: media por brazo y cambio frente al fijo y al actuado
  demanda2/eval_dem_<esc>_<brazo>.csv   parciales de evaluar.py (semillas 1001-1030): recalculo y ciclo minimo
  politica_dem_<esc>_vecinos_s<b>.json  val_elegido, val_serie y episodios de cada entrenamiento
  dem_<esc>.add.xml, barrido_dem_<esc>.csv   programa fijo instalado por barrer_fijo.py y su barrido
  veredicto.csv, veredicto.md           filas ippo_vecinos de P1-P6 (veredicto.py --metrica timeloss_prom
                                        --fijo fijo_2509 --sin-trivial)
  evaluacion_<esc>_resumen_fijo_2509.csv   retraso del fijo ajustado, del actuado y del ciclo minimo en P1-P6
  evaluacion_<esc>.csv                  por semilla: cambio frente al ciclo minimo y recalculo en P1-P6
  generar_trabajos.py (MALLAS_2509) y fijo_2509.py (COMMIT): malla inicial de verdes de cada barrido y commit
                                        con el programa fijo de P1-P5 (el de P6 es el de malla3_alta.add.xml)
Escribe:
  plan2/demanda2/resumen_demanda2.csv   una fila por red y nivel
  TESIS/secciones/tablas/demanda2.tex   solo el tabular (el table, el caption y el label van en el capitulo)
  TESIS/images/fig_demanda_bandas.pdf (vectorial) y .png

Reglas: las del plan, sin cambios (plan2/ESPEC.md seccion 7; capitulo3.tex, sec:veredicto), aplicadas con las
funciones de veredicto.py:
  - Metrica: el retraso (timeloss_prom), la del veredicto del plan.
  - Version evaluada: la mediana de las tres bases (42, 2042, 4042) por el valor de validacion elegido
    (val_elegido del meta; veredicto.info_base y base_mediana). Nunca se elige con las semillas 1001-1030.
  - Convergencia de esa base: veredicto.convergencia (meseta entre -5 y +5 % y estabilidad de hasta 5 % en el
    ultimo tercio de la validacion); entrenamientos_estables = cuantas de las tres bases convergen.
  - Cambio = (media del modelo - media de la referencia) / media de la referencia x 100 sobre las mismas
    semillas, con IC95 por bootstrap pareado (10 000 remuestreos) y p de Wilcoxon pareado (evaluar.comparar).
  - Veredicto: veredicto.celda y veredicto.veredicto (umbral del 5 %, IC y p < 0.05, condicion frente al
    actuado; PENDIENTE con el provisional si la base evaluada no converge).
  - La referencia de cada nivel nuevo es SU fijo ajustado: el brazo fijo, con el programa que barrer_fijo.py
    eligio para ese nivel con la regla del 25.09 (--metrica timeloss_prom y la malla de verdes del caso que
    hereda el nivel, con la extension automatica). En P1-P6, el fijo ajustado del plan (brazo fijo_2509).
  - Los veredictos de los niveles nuevos salen de evaluacion_dem_<esc>_resumen.csv con veredicto.celda, como en
    veredicto.py. Las cifras de un decimal (cambio, IC) y el p salen de evaluar.comparar sobre los parciales,
    es decir, de los datos crudos con un solo redondeo; el script comprueba que coinciden con el resumen
    (hasta 0.05, porque el resumen trae 2 decimales) y que dan el mismo veredicto.
    El cambio frente al ciclo minimo (brazo trivial) no esta en el resumen y sale solo de evaluar.comparar.
  - P1-P6: las cifras de veredicto.csv, que deben coincidir exactamente con evaluar.comparar sobre
    evaluacion_<esc>.csv (si no, el script avisa de un doble redondeo).
  - Igual al ciclo minimo: la version evaluada da en las 30 semillas los mismos valores que el ciclo minimo
    en todas las metricas de trafico (evaluar.METRICAS; no en los retornos ni en las decisiones).

Verificacion (23.10.2026):
  - Doble redondeo: antes, las cifras de los niveles nuevos se tomaban del resumen (2 decimales) y se
    redondeaban otra vez a uno. Tres cifras salian mal: malla 1810 frente al actuado -9.1 (es -9.0495, -9.0),
    IC de red 1358 frente al fijo [-10.3, -9.2] (es [-10.3, -9.3]) y de malla 3620 [0.5, 1.0] (es [0.4, 1.0]).
  - Figura: el rotulo de la banda de FUNCIONA dice tambien la condicion frente al actuado, como la Figura
    fig:plan2-mejora-caso; los puntos de los niveles compartidos se desplazan hacia la derecha (corredor x1.07,
    malla x1.15), porque el desplazamiento anterior hacia la izquierda (corredor x0.92) dejaba el corredor de
    2715 veh/h a la izquierda de P4 (2580); el script avisa si algun punto queda fuera de orden. MEJORA va con
    un marcador mas grande y un borde mas fino. El provisional de PENDIENTE no se ve en el marcador (el color
    dice la red): esta en la tabla, y el pie de figura debe decirlo.
  - Tabla: el comentario del .tex dice el entorno que necesita para caber en el ancho del texto.
"""
import os
import re
import csv
import math
import argparse
import subprocess
import importlib.util

import evaluar
import escenarios_plan2 as ep

DIR = os.path.dirname(os.path.abspath(__file__))
vd = None                       # modulo veredicto, cargado en main() (--veredicto)

METRICA = "timeloss_prom"       # metrica del veredicto del plan (retraso = timeLoss)
SEMILLAS = list(range(1001, 1031))
REDES = ["corredor", "red", "malla3"]                       # orden de las filas y de las series
NOMBRE_RED = {"corredor": "corredor", "red": "red con rotonda", "malla3": "malla 3x3"}
RED_TEX = {"corredor": ("Corredor", ""), "red": ("Red con", "rotonda"), "malla3": ("Malla", r"$3 \times 3$")}
RED_FIG = {"corredor": "Corredor", "red": "Red con rotonda", "malla3": "Malla 3 × 3"}
MARCA_TRIVIAL = " (= trivial)"  # sufijo que veredicto.py agrega sin --sin-trivial; aqui va en su columna
COLUMNAS = ["red", "escenario", "vehiculos_hora", "factor", "caso_plan", "programa_fijo", "malla_extendida",
            "retraso_fijo", "retraso_actuado", "retraso_trivial", "retraso_ippo", "base_evaluada",
            "entrenamientos_estables", "convergio", "cambio_fijo", "ic_fijo", "p_fijo", "cambio_actuado",
            "ic_actuado", "p_actuado", "cambio_ciclo_minimo", "ic_ciclo_minimo", "p_ciclo_minimo",
            "igual_ciclo_minimo", "veredicto"]
avisos = []                     # comprobaciones que no cuadran (se imprimen al final)


def aviso(texto):
    avisos.append(texto)


def cargar(nombre, ruta):
    """Modulo de un archivo .py por su ruta (sin tocar sys.path)."""
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def leer_csv(ruta):
    if not os.path.exists(ruta):
        return []
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------- Programa fijo instalado por barrer_fijo.py ----------------

PATRON_MALLA = re.compile(r"verde de avenida \(E-O\) ([\d/]+) s x verde transversal \(N-S\) ([\d/]+) s")
PATRON_GANADOR = re.compile(r"Ganador: avenida (\d+) s, transversal (\d+) s, ciclo (\d+) s, desfases "
                            r"([\d/]+)(?: \((\w+)\))?")
ESQUEMA = {"ajedrez": "en ajedrez", "cero": "todos en 0", "onda_eo": "en onda hacia el este"}


def comentario(texto):
    """Primer comentario de un .add.xml, en una sola linea."""
    m = re.search(r"<!--(.*?)-->", texto, re.S)
    return " ".join(m.group(1).split()) if m else ""


def programa(texto, malla_inicial):
    """Ganador del barrido y verdes agregados por la extension automatica, del comentario que barrer_fijo.py
    escribe en el .add.xml; malla_inicial = (avenida, transversal) como en MALLAS_2509 ("15,20,25", ...)."""
    t = comentario(texto)
    m, g = PATRON_MALLA.search(t), PATRON_GANADOR.search(t)
    if not m or not g:
        return None
    barrida = [[int(v) for v in eje.split("/")] for eje in m.groups()]
    inicial = [[int(v) for v in eje.split(",")] for eje in malla_inicial]
    agregados = [f"{nombre} {v} s" for nombre, b, i in zip(("avenida", "transversal"), barrida, inicial)
                 for v in b if v not in i]
    return {"verde": int(g.group(1)), "transversal": int(g.group(2)), "ciclo": int(g.group(3)),
            "desfases": g.group(4), "esquema": g.group(5), "agregados": agregados}


def texto_programa(p):
    """'20/10 s, ciclo 36 s, desfases 0/15 s; malla sin extender' (verdes de avenida / transversal)."""
    if p["esquema"] == "cero":
        desfases = "desfases todos en 0"
    elif p["esquema"]:
        valores = sorted({int(v) for v in p["desfases"].split("/")})
        desfases = f"desfases {ESQUEMA.get(p['esquema'], p['esquema'])}, " + \
            " y ".join(str(v) for v in valores) + " s"
    else:
        desfases = f"desfases {p['desfases']} s"
    malla = f"malla extendida ({', '.join(p['agregados'])})" if p["agregados"] else "malla sin extender"
    return f"{p['verde']}/{p['transversal']} s, ciclo {p['ciclo']} s, {desfases}; {malla}"


def programa_nivel(plan2, esc, mallas):
    """Programa fijo de un nivel nuevo, comprobado contra la fila ganadora de su barrido."""
    with open(os.path.join(plan2, f"{esc}.add.xml"), encoding="utf-8") as f:
        p = programa(f.read(), mallas[ep.NIVELES_DEMANDA2[esc][3]])
    if p is None:
        aviso(f"{esc}: no se pudo leer el programa fijo del comentario de {esc}.add.xml")
        return None
    barrido = leer_csv(os.path.join(plan2, f"barrido_{esc}.csv"))
    if barrido:
        ganador = min(barrido, key=lambda r: float(r[METRICA]))
        if (int(ganador["verde"]), int(ganador["verde_transversal"]), ganador["offsets"]) != \
                (p["verde"], p["transversal"], p["desfases"]):
            aviso(f"{esc}: el ganador de barrido_{esc}.csv no es el programa de {esc}.add.xml")
    else:
        aviso(f"{esc}: falta barrido_{esc}.csv")
    return p


def programa_plan(plan2, esc, mallas, commit):
    """Programa del fijo ajustado de un caso del plan: el de plan2/<esc>.add.xml en el commit del veredicto
    pre-registrado (fijo_2509.COMMIT, barridos del 24.09: P1-P5) o, si alli no existe, el actual (P6)."""
    res = subprocess.run(["git", "show", f"{commit}:plan2/{esc}.add.xml"], cwd=DIR, capture_output=True,
                         text=True, encoding="utf-8")
    texto = res.stdout if res.returncode == 0 else None
    if texto is None:
        with open(os.path.join(plan2, f"{esc}.add.xml"), encoding="utf-8") as f:
            texto = f.read()
    p = programa(texto, mallas[esc])
    if p is None:
        aviso(f"{esc}: no se pudo leer el programa fijo de {esc}.add.xml")
    return p


# ---------------- Estadistica ----------------

def por_semilla(filas, brazo, metrica=METRICA):
    """{semilla: valor} de un brazo; se omiten las semillas sin valor."""
    return {int(r["semilla"]): float(r[metrica]) for r in filas
            if r["brazo"] == brazo and r.get(metrica, "") not in ("", None)}


def comparar(otro, ref):
    """evaluar.comparar pareado por semilla (las semillas comunes, en orden): (cambio %, IC, p, n)."""
    comunes = sorted(set(otro) & set(ref))
    r = evaluar.comparar([otro[s] for s in comunes], [ref[s] for s in comunes]) if comunes else {}
    return vd.flotante(r.get("delta_pct")), vd.intervalo(r), vd.flotante(r.get("p_wilcoxon")), len(comunes)


def iguales(filas, brazo_a, brazo_b):
    """True si los dos brazos dan los mismos valores en las 30 semillas en todas las metricas de trafico."""
    a = {int(r["semilla"]): r for r in filas if r["brazo"] == brazo_a}
    b = {int(r["semilla"]): r for r in filas if r["brazo"] == brazo_b}
    if sorted(set(a) & set(b)) != SEMILLAS:
        return False
    for s in SEMILLAS:
        for m in evaluar.METRICAS:
            if vd.flotante(a[s].get(m)) != vd.flotante(b[s].get(m)):
                return False
    return True


def media(valores):
    return sum(valores) / len(valores) if valores else None


def cuadra(nombre, a, b, tol):
    """Avisa si dos numeros (o dos IC) no coinciden hasta tol."""
    if isinstance(a, tuple) or isinstance(b, tuple):
        ok = a is not None and b is not None and all(abs(x - y) <= tol for x, y in zip(a, b))
    else:
        ok = a is not None and b is not None and abs(a - b) <= tol
    if not ok:
        aviso(f"{nombre}: {a} frente a {b} del recalculo")


def cuadra_p(nombre, p_tabla, p_recalculo):
    """Los dos p salen de scipy.stats.wilcoxon con 3 cifras significativas."""
    if p_tabla is None or p_recalculo is None or abs(p_tabla - p_recalculo) > 1e-3 * max(p_tabla, 1e-12):
        aviso(f"{nombre}: p {p_tabla} frente a {p_recalculo} del recalculo")


# ---------------- Filas ----------------

def palabra(texto):
    """(veredicto, provisional o None) de un texto de veredicto.csv o de veredicto.celda."""
    texto = (texto or "").replace(MARCA_TRIVIAL, "")
    if texto.startswith("PENDIENTE"):
        prov = texto.split("provisional:")[1].strip(" )") if "provisional:" in texto else None
        return "PENDIENTE", prov
    return texto.split(" ")[0], None


def fila_nivel(plan2, esc, mallas):
    """Fila de un nivel nuevo: version evaluada, convergencia y veredicto con veredicto.celda, como en el plan."""
    base_red, factor, total, _ = ep.NIVELES_DEMANDA2[esc]
    resumen = vd.leer_resumen(plan2, esc)              # evaluacion_<esc>_resumen.csv (deltas frente a su fijo)
    desc = vd.describir(esc, plan2)
    if desc["demanda"] != total:
        aviso(f"{esc}: el .rou.xml suma {desc['demanda']} veh/h y no {total}")
    celda, _, _ = vd.celda(plan2, "", esc, "ippo_vecinos", resumen, desc)
    base = celda["base_publicada"]
    brazo = f"ippo_vecinos_s{base}"
    p = programa_nivel(plan2, esc, mallas)
    fila = {"red": base_red, "escenario": esc, "vehiculos_hora": total, "factor": factor, "caso_plan": "",
            "programa_fijo": texto_programa(p) if p else "", "malla_extendida": bool(p and p["agregados"]),
            "base_evaluada": base, "entrenamientos_estables": celda["convergen"], "convergio": celda["convergio"],
            "cambio_fijo": celda["delta_fijo"], "ic_fijo": celda["ic_fijo"], "p_fijo": celda["p_fijo"],
            "cambio_actuado": celda["delta_act"], "ic_actuado": celda["ic_act"], "p_actuado": celda["p_act"],
            "veredicto": celda["veredicto"]}
    for col, br in (("retraso_fijo", "fijo"), ("retraso_actuado", "actuado"), ("retraso_trivial", "trivial"),
                    ("retraso_ippo", brazo)):
        r = resumen.get((br, METRICA))
        fila[col] = vd.flotante(r["media"]) if r else None
    # recalculo con evaluar.comparar sobre los parciales de demanda2/
    parciales = []
    for br in ("fijo", "actuado", "trivial", brazo):
        filas = leer_csv(os.path.join(plan2, "demanda2", f"eval_{esc}_{br}.csv"))
        if not filas:
            aviso(f"{esc}: falta el parcial demanda2/eval_{esc}_{br}.csv")
        parciales += filas
    vals = {br: por_semilla(parciales, br) for br in ("fijo", "actuado", "trivial", brazo)}
    for col, br in (("retraso_fijo", "fijo"), ("retraso_actuado", "actuado"), ("retraso_trivial", "trivial"),
                    ("retraso_ippo", brazo)):
        cuadra(f"{esc} {col}", fila[col], media(list(vals[br].values())), 5e-5)
        if sorted(vals[br]) != SEMILLAS:
            aviso(f"{esc} {br}: las semillas no son 1001-1030")
    d_f, ic_f, p_f, _ = comparar(vals[brazo], vals["fijo"])
    d_a, ic_a, p_a, _ = comparar(vals[brazo], vals["actuado"])
    # el resumen trae 2 decimales y evaluar.comparar 1, desde los datos crudos: coinciden hasta 0.05 (las dos
    # cifras son multiplos de 0.01 y cada una esta a 0.005 o 0.05 del valor sin redondear)
    cuadra(f"{esc} cambio frente al fijo", fila["cambio_fijo"], d_f, 0.05 + 1e-9)
    cuadra(f"{esc} IC frente al fijo", fila["ic_fijo"], ic_f, 0.05 + 1e-9)
    cuadra_p(f"{esc} frente al fijo", fila["p_fijo"], p_f)
    cuadra(f"{esc} cambio frente al actuado", fila["cambio_actuado"], d_a, 0.05 + 1e-9)
    cuadra(f"{esc} IC frente al actuado", fila["ic_actuado"], ic_a, 0.05 + 1e-9)
    cuadra_p(f"{esc} frente al actuado", fila["p_actuado"], p_a)
    ver, prov = palabra(fila["veredicto"])
    if None not in (d_f, ic_f, p_f, ic_a, p_a) and vd.veredicto(d_f, ic_f, p_f, ic_a, p_a) != (prov or ver):
        aviso(f"{esc}: el veredicto cambia con los valores de evaluar.comparar (un decimal)")
    # verificacion del 23.10.2026: las cifras que se publican son las de evaluar.comparar (un solo redondeo,
    # desde los datos crudos). Redondear otra vez a un decimal el resumen de 2 decimales cambiaba tres cifras.
    fila.update({"cambio_fijo": d_f, "ic_fijo": ic_f, "p_fijo": p_f,
                 "cambio_actuado": d_a, "ic_actuado": ic_a, "p_actuado": p_a})
    fila["cambio_ciclo_minimo"], fila["ic_ciclo_minimo"], fila["p_ciclo_minimo"], _ = \
        comparar(vals[brazo], vals["trivial"])
    fila["igual_ciclo_minimo"] = iguales(parciales, brazo, "trivial")
    if fila["igual_ciclo_minimo"] != vd.igual_a(resumen, brazo, "trivial"):
        aviso(f"{esc}: la igualdad con el ciclo minimo por semilla no coincide con veredicto.igual_a")
    return fila


def fila_caso(plan2, caso, esc, por_caso, mallas, commit):
    """Fila de un caso del plan: veredicto.csv (ippo_vecinos, fijo_2509) y el resumen frente a fijo_2509."""
    v = por_caso.get(caso)
    base_red = esc.replace("_alta", "")
    fila = {"red": base_red, "escenario": esc, "caso_plan": caso}
    if not v:
        aviso(f"{caso}: falta la fila ippo_vecinos en veredicto.csv")
        return None
    total = int(v["demanda_veh_h"])
    base = int(v["base_publicada"])
    brazo = f"ippo_vecinos_s{base}"
    resumen = {(r["brazo"], r["metrica"]): r
               for r in leer_csv(os.path.join(plan2, f"evaluacion_{esc}_resumen_fijo_2509.csv"))}
    p = programa_plan(plan2, esc, mallas, commit)
    fila.update({"vehiculos_hora": total, "factor": total / ep.TOTAL_BASE[base_red],
                 "programa_fijo": texto_programa(p) if p else "", "malla_extendida": bool(p and p["agregados"]),
                 "base_evaluada": base, "entrenamientos_estables": v["convergen"], "convergio": v["convergio"],
                 "cambio_fijo": vd.flotante(v["delta_fijo"]), "ic_fijo": vd.intervalo({"delta_ic95": v["ic_fijo"]}),
                 "p_fijo": vd.flotante(v["p_fijo"]), "cambio_actuado": vd.flotante(v["delta_act"]),
                 "ic_actuado": vd.intervalo({"delta_ic95": v["ic_act"]}), "p_actuado": vd.flotante(v["p_act"]),
                 "veredicto": (v["veredicto"] or "").replace(MARCA_TRIVIAL, "")})
    for col, br in (("retraso_fijo", "fijo_2509"), ("retraso_actuado", "actuado"), ("retraso_trivial", "trivial"),
                    ("retraso_ippo", brazo)):
        r = resumen.get((br, METRICA))
        fila[col] = vd.flotante(r["media"]) if r else None
        if fila[col] is None:
            aviso(f"{caso}: falta el brazo {br} en evaluacion_{esc}_resumen_fijo_2509.csv")
    cuadra(f"{caso} retraso de IPPO (veredicto.csv)", vd.flotante(v["retraso"]), fila["retraso_ippo"], 5e-4)
    # recalculo con evaluar.comparar sobre evaluacion_<esc>.csv (todas las semillas de todos los brazos)
    filas = leer_csv(os.path.join(plan2, f"evaluacion_{esc}.csv"))
    vals = {br: por_semilla(filas, br) for br in ("fijo_2509", "actuado", "trivial", brazo)}
    d_f, ic_f, p_f, _ = comparar(vals[brazo], vals["fijo_2509"])
    d_a, ic_a, p_a, _ = comparar(vals[brazo], vals["actuado"])
    # veredicto.csv redondea a un decimal el cambio que el resumen trae con dos; evaluar.comparar lo redondea una
    # sola vez desde los datos crudos. Deben coincidir exactamente: si no, hay un doble redondeo en veredicto.csv
    # (que es la fuente de la tabla principal de la tesis) y se avisa
    cuadra(f"{caso} cambio frente al fijo (doble redondeo)", fila["cambio_fijo"], d_f, 1e-9)
    cuadra(f"{caso} IC frente al fijo (doble redondeo)", fila["ic_fijo"], ic_f, 1e-9)
    cuadra_p(f"{caso} frente al fijo", fila["p_fijo"], p_f)
    cuadra(f"{caso} cambio frente al actuado (doble redondeo)", fila["cambio_actuado"], d_a, 1e-9)
    cuadra(f"{caso} IC frente al actuado (doble redondeo)", fila["ic_actuado"], ic_a, 1e-9)
    cuadra_p(f"{caso} frente al actuado", fila["p_actuado"], p_a)
    fila["cambio_ciclo_minimo"], fila["ic_ciclo_minimo"], fila["p_ciclo_minimo"], _ = \
        comparar(vals[brazo], vals["trivial"])
    fila["igual_ciclo_minimo"] = iguales(filas, brazo, "trivial")
    return fila


def calcular(plan2):
    """Filas de los niveles nuevos y de P1-P6, ordenadas por red y demanda."""
    mallas = cargar("generar_trabajos", os.path.join(plan2, "generar_trabajos.py")).MALLAS_2509
    commit = cargar("fijo_2509", os.path.join(plan2, "fijo_2509.py")).COMMIT
    with open(os.path.join(plan2, "veredicto.md"), encoding="utf-8") as f:
        cabeza = f.read(2000)
    if "timeloss_prom" not in cabeza or "fijo_2509" not in cabeza:
        aviso("veredicto.md no dice timeloss_prom y fijo_2509: veredicto.csv no es el del resultado principal")
    por_caso = {r["caso"]: r for r in leer_csv(os.path.join(plan2, "veredicto.csv"))
                if r["modelo"] == "ippo_vecinos"}
    filas = [fila_nivel(plan2, esc, mallas) for esc in ep.NIVELES_DEMANDA2]
    filas += [fila_caso(plan2, caso, esc, por_caso, mallas, commit) for caso, esc in vd.CASOS]
    filas = [f for f in filas if f]
    filas.sort(key=lambda f: (REDES.index(f["red"]), f["vehiculos_hora"]))
    return filas


# ---------------- Salidas ----------------

def txt(x, dec):
    return "" if x is None else f"{x:.{dec}f}"


def txt_factor(f):
    return f"{f:.3f}".rstrip("0").rstrip(".")


def escribir_csv(ruta, filas):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for fila in filas:
            salida = dict(fila)
            salida["red"] = NOMBRE_RED[fila["red"]]
            salida["factor"] = txt_factor(fila["factor"])
            for c in ("retraso_fijo", "retraso_actuado", "retraso_trivial", "retraso_ippo"):
                salida[c] = txt(fila[c], 3)
            for c in ("cambio_fijo", "cambio_actuado", "cambio_ciclo_minimo"):
                salida[c] = txt(fila[c], 1)
            for c in ("ic_fijo", "ic_actuado", "ic_ciclo_minimo"):
                salida[c] = vd.txt_ic(fila[c])
            for c in ("p_fijo", "p_actuado", "p_ciclo_minimo"):
                salida[c] = vd.txt_p(fila[c])
            for c in ("malla_extendida", "igual_ciclo_minimo"):
                salida[c] = "si" if fila[c] else "no"
            w.writerow(salida)
    print("Escrito", ruta)


def tex_signo(x):
    """Cambio con signo y un decimal en modo matematico, como en la tabla de resultados: $-6.8$, $+1.8$."""
    return "--" if x is None else f"${x:+.1f}$"


def apilar(lineas):
    """Varias lineas en una celda, la primera a la altura de la fila (el {} evita que un [ se lea como argumento)."""
    return lineas[0] if len(lineas) == 1 else r"\makecell[tl]{" + r"\\{}".join(lineas) + "}"


def tex_veredicto(fila):
    """Veredicto y, debajo, el provisional si es PENDIENTE y la nota "igual al ciclo minimo" (en palabras, como
    las tablas de veredicto.py), en lineas cortas para que la tabla quepa en 15 cm."""
    ver, prov = palabra(fila["veredicto"])
    igual = fila["igual_ciclo_minimo"]
    if prov and igual:
        return apilar([ver, "(provisional:", f"{prov}; igual al", "ciclo mínimo)"])
    if prov:
        return apilar([ver, "(provisional:", f"{prov})"])
    if igual:
        return apilar([ver, "(igual al", "ciclo mínimo)"])
    return ver


def tabla_tex(filas):
    """Solo el tabular: una fila por red y nivel, por red y demanda; los casos del plan con su codigo (Caso)."""
    lineas = [
        "% Generado por curvas_demanda.py a partir de plan2/. No editar a mano.",
        "% Niveles de demanda (entrega 3, tarea 5): solo el entorno tabular; el table, el caption y la etiqueta los",
        "% pone el capitulo que la incluye con \\input{secciones/tablas/demanda2}.",
        "% fuente: plan2/demanda2/resumen_demanda2.csv (columnas red, vehiculos_hora, caso_plan, retraso_fijo,",
        "% retraso_actuado, retraso_ippo, cambio_fijo, cambio_actuado, veredicto e igual_ciclo_minimo). Niveles",
        "% nuevos: plan2/evaluacion_dem_<esc>_resumen.csv (timeloss_prom; el fijo es el fijo ajustado del barrido de",
        "% cada nivel) con la regla de veredicto.py; P1-P6: filas ippo_vecinos de plan2/veredicto.csv (referencia",
        "% fijo_2509) y plan2/evaluacion_<esc>_resumen_fijo_2509.csv. Igual al ciclo minimo: la version evaluada da",
        "% los mismos valores que el ciclo minimo en las 30 semillas (curvas_demanda.iguales). Cambios de los niveles",
        "% nuevos: evaluar.comparar sobre plan2/demanda2/eval_dem_<esc>_*.csv (un solo redondeo, desde los datos crudos).",
        "% Entorno que necesita (medido con tesisutec.cls, \\textwidth = 427.4 pt): el table lleva \\setstretch{1},",
        "% \\footnotesize y \\setlength{\\tabcolsep}{3pt}; asi mide 405.8 pt (14.3 cm) de ancho y 463.1 pt (16.3 cm) de",
        "% alto, y va en [!tbp]. Con \\small (439.2 pt) o con el tabcolsep por defecto (459.8 pt) se sale del margen.",
        r"\begin{tabular}{lrlrrrrrl}",
        r"\toprule",
        r" & & & \multicolumn{3}{c}{Retraso (s/veh)} & \multicolumn{2}{c}{\makecell{Cambio (\%)\\frente al}} & \\",
        r"\cmidrule(lr){4-6}\cmidrule(lr){7-8}",
        r"Red & Veh/h & Caso & \makecell{Fijo\\ajustado} & Actuado & \makecell{IPPO con\\mensajes} & "
        r"\makecell{fijo\\ajustado} & actuado & Veredicto \\",
    ]
    for red in REDES:
        lineas.append(r"\midrule")
        nombre = apilar([x for x in RED_TEX[red] if x])
        for i, f in enumerate(x for x in filas if x["red"] == red):
            celdas = [nombre if i == 0 else "", str(f["vehiculos_hora"]), f["caso_plan"],
                      txt(f["retraso_fijo"], 2), txt(f["retraso_actuado"], 2), txt(f["retraso_ippo"], 2),
                      tex_signo(f["cambio_fijo"]), tex_signo(f["cambio_actuado"]), tex_veredicto(f)]
            lineas.append(" & ".join(celdas) + r" \\")
    lineas += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lineas) + "\n"


def escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)
    print("Escrito", ruta)


# ---------------- Figura ----------------
# Paleta de la skill dataviz, la misma de la figura de cambio por caso (sintesis_plan.figura_mejora): superficie,
# tintas y verde y rojo de estado para las bandas. Las tres redes usan los tres primeros colores categoricos
# (azul, naranja, aguamarina, validados con validate_palette.js en todos los pares) y una forma cada una.
FONDO, TINTA, TINTA2, APAGADO = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
VERDE, ROJO = "#0ca30c", "#d03b3b"
COLOR_RED = {"corredor": "#2a78d6", "red": "#eb6834", "malla3": "#1baf7a"}
FORMA_RED = {"corredor": "o", "red": "s", "malla3": "^"}
TAM_RED = {"corredor": 7.6, "red": 6.9, "malla3": 8.2}            # puntos; el cuadrado se ve mas grande
# Con una demanda que tienen dos o tres redes (905, 1358, 1810, 2715 y 3620 veh/h) los puntos se separan un poco
# en x (factor) para que no se tapen; la red con rotonda y los demas niveles quedan en su demanda exacta.
# Verificacion del 23.10.2026: los dos desplazamientos van hacia la derecha. Con el corredor hacia la izquierda
# (x0.92) su punto de 2715 veh/h quedaba en 2498, a la izquierda de P4 (2580); hacia la izquierda caben como
# mucho un 5 % (2715/2580 = 1.052), menos de lo que hace falta para que no se tapen. Asi el orden se conserva:
# 1810 < 1937 < 2082 < 2150 (P3) < 2580 (P4) < 2715 < 2905 < 3122 < 3620 < 3873 < 4163 < 4350 (P5).
# x1.07 separa P1 del cuadrado de red 1810 (casi a la misma altura) y x1.15 aleja la linea del corredor, que baja
# de 2715 a P2, del triangulo de malla 2715
SEPARA = {"corredor": 1.07, "red": 1.0, "malla3": 1.15}
MAS_MEJORA, BORDE_MEJORA = 1.2, 0.5     # MEJORA (medio relleno): puntos de mas y grosor del borde
UMBRAL = -5.0                  # % (veredicto.UMBRAL_DELTA): FUNCIONA pide un cambio de -5 % o menos
META = -25.0                   # meta de retraso de la tesis
MENOS = "\u2212"
# Donde va el rotulo de cada caso del plan (desplazamiento en puntos y alineacion)
# (P1 va a la derecha: a la izquierda queda el cuadrado de red 1810, casi a la misma altura)
ROTULO = {"P1": (7, -1, "left"), "P2": (8, 0, "left"), "P3": (0, -11, "center"), "P4": (-7, 6, "right"),
          "P5": (0, 13, "center"), "P6": (-7, 8, "right")}


def mezcla(color, alfa, fondo=FONDO):
    """Color solido equivalente a `color` con opacidad `alfa` sobre el fondo (sin transparencias en el PDF)."""
    from matplotlib.colors import to_rgb, to_hex
    return to_hex([alfa * c + (1 - alfa) * f for c, f in zip(to_rgb(color), to_rgb(fondo))])


BANDA_CLARA, BANDA_PEQUENA, BANDA_ROJA = mezcla(VERDE, 0.15), mezcla(VERDE, 0.06), mezcla(ROJO, 0.09)


def banda(y):
    """Color de la banda en la que cae y (para que un marcador hueco tape la linea sin verse blanco)."""
    return BANDA_ROJA if y > 0 else (BANDA_PEQUENA if y > UMBRAL else BANDA_CLARA)


def con_signo(v):
    return f"{v:+d}".replace("-", MENOS) if v else "0"


def figura(filas, ruta):
    """Demanda total contra el cambio de IPPO con mensajes frente al fijo ajustado, una serie por red, sobre
    bandas por rango de veredicto. Escribe el PNG de `ruta` y el PDF vectorial al lado."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FixedLocator, NullLocator

    bajo = min([META] + [f["ic_fijo"][0] for f in filas if f["ic_fijo"]])
    alto = max([0.0] + [f["ic_fijo"][1] for f in filas if f["ic_fijo"]])
    y0, y1 = math.floor(bajo) - 3, math.ceil(alto) + 2
    x0, x1 = 760, 10200
    redes_por_nivel = {}
    for f in filas:
        redes_por_nivel.setdefault(f["vehiculos_hora"], set()).add(f["red"])

    def x_de(f):
        compartido = len(redes_por_nivel[f["vehiculos_hora"]]) > 1
        return f["vehiculos_hora"] * (SEPARA[f["red"]] if compartido else 1.0)

    # el desplazamiento no puede cambiar el orden de dos puntos de demandas distintas (verificacion del 23.10.2026)
    for a in filas:
        for b in filas:
            if a["vehiculos_hora"] < b["vehiculos_hora"] and x_de(a) >= x_de(b):
                aviso(f"figura: {NOMBRE_RED[a['red']]} {a['vehiculos_hora']} queda dibujado en {x_de(a):.0f}, "
                      f"a la derecha de {NOMBRE_RED[b['red']]} {b['vehiculos_hora']} ({x_de(b):.0f})")

    with plt.rc_context({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.edgecolor": APAGADO,
                         "axes.labelcolor": TINTA2, "xtick.color": TINTA2, "ytick.color": TINTA2}):
        fig, ax = plt.subplots(figsize=(6.4, 4.5), facecolor=FONDO)
        ax.set_facecolor(FONDO)
        ax.set_xscale("log")
        ax.axhspan(y0, UMBRAL, color=BANDA_CLARA, lw=0, zorder=0)
        ax.axhspan(UMBRAL, 0, color=BANDA_PEQUENA, lw=0, zorder=0)
        ax.axhspan(0, y1, color=BANDA_ROJA, lw=0, zorder=0)
        ax.axhline(0, color=APAGADO, lw=0.9, zorder=2)
        ax.axhline(META, color=TINTA2, lw=0.9, ls=(0, (1, 2.2)), zorder=2)
        rotulo = dict(fontsize=7.4, color=TINTA2, linespacing=1.25, zorder=2)
        xr = 8000                                          # rotulos de las bandas, a la izquierda de P6
        # la misma lectura de la Figura fig:plan2-mejora-caso (sintesis_plan.figura_mejora), que el Cap. V
        # promete; verificacion del 23.10.2026: el rotulo de FUNCIONA lleva el texto de esa figura, con la
        # condicion frente al actuado (red 1810 cae en esa banda y es MEJORA porque pierde contra el actuado).
        # Va en cuatro lineas, a la derecha de P2, para no cruzarse con la linea del corredor
        ax.text(xr, y1 - 1.0, "Más retraso que el fijo ajustado:\nFALLA si es significativo", ha="right",
                va="top", **rotulo)
        # (medio punto por debajo del centro de la banda, para no tocar el cuadrado de red 3620, en -0.1)
        ax.text(xr, UMBRAL / 2 - 0.5, f"Mejora pequeña, entre {MENOS}5 y 0 %:\nMEJORA si es significativa",
                ha="right", va="center", **rotulo)
        ax.text(x1 / 1.04, (UMBRAL + META) / 2 - 2.5,
                f"Mejora clara, de {MENOS}5 %\no más negativo:\nFUNCIONA si es significativa\n"
                "y no pierde contra el actuado", ha="right", va="center", **rotulo)
        ax.text(x1 / 1.04, META + 0.5, f"meta de la tesis: {MENOS}25 %", ha="right", va="bottom",
                fontsize=7.4, color=TINTA2, zorder=2)
        for red in REDES:
            serie = [f for f in filas if f["red"] == red and f["cambio_fijo"] is not None]
            color, forma, tam = COLOR_RED[red], FORMA_RED[red], TAM_RED[red]
            xs = [x_de(f) for f in serie]
            ax.plot(xs, [f["cambio_fijo"] for f in serie], color=color, lw=1.4, zorder=3,
                    solid_joinstyle="round", solid_capstyle="round")
            for x, f in zip(xs, serie):
                y = f["cambio_fijo"]
                if f["ic_fijo"]:
                    ax.plot([x, x], list(f["ic_fijo"]), color=color, lw=1.1, zorder=4, solid_capstyle="butt")
                ver, _ = palabra(f["veredicto"])
                # MEJORA, medio relleno: mas grande y con un borde mas fino para que la mitad blanca se vea al
                # tamano de impresion (verificacion del 23.10.2026: con el borde de 0.9 quedaba en un tercio)
                ms = tam + (MAS_MEJORA if ver == "MEJORA" else 0)
                # anillo del color de la banda: separa el marcador de las lineas que pasan cerca
                ax.plot(x, y, forma, ms=ms + 2.6, mfc=banda(y), mec=banda(y), mew=0, zorder=4.6)
                if ver == "PENDIENTE":
                    ax.scatter([x], [y], s=(tam + 0.6) ** 2, marker=forma, facecolors=banda(y), edgecolors=color,
                               linewidths=1.6, linestyle=(0, (1.3, 1.1)), zorder=5)
                elif ver == "EMPATA":
                    ax.plot(x, y, forma, ms=tam, mfc=FONDO, mec=color, mew=1.4, zorder=5)
                elif ver == "MEJORA":
                    ax.plot(x, y, forma, ms=ms, fillstyle="bottom", mfc=color, markerfacecoloralt=FONDO,
                            mec=color, mew=BORDE_MEJORA, zorder=5)
                else:                                      # FUNCIONA o FALLA: la banda dice cual
                    ax.plot(x, y, forma, ms=tam, mfc=color, mec=color, mew=1.0, zorder=5)
                if f["caso_plan"]:
                    dx, dy, lado = ROTULO.get(f["caso_plan"], (0, 9, "center"))
                    ax.annotate(f["caso_plan"], (x, y), xytext=(dx, dy), textcoords="offset points", ha=lado,
                                va="center", fontsize=7.8, color=TINTA, fontweight="bold", zorder=6)
        niveles = sorted({f["vehiculos_hora"] for f in filas if not f["caso_plan"]} |
                         {f["vehiculos_hora"] for f in filas if f["caso_plan"] in ("P5", "P6")})
        ax.set_xlim(x0, x1)
        ax.xaxis.set_major_locator(FixedLocator(niveles))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xticklabels([str(n) for n in niveles], fontsize=7.6)
        ax.set_ylim(y0, y1)
        marcas = list(range(5 * math.ceil(y0 / 5), y1 + 1, 5))
        ax.set_yticks(marcas)
        ax.set_yticklabels([con_signo(t) for t in marcas], fontsize=7.8)
        ax.grid(axis="both", color=FONDO, lw=0.8, zorder=1)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.set_xlabel("Demanda total (veh/h, escala logarítmica)", fontsize=8.2)
        ax.set_ylabel("Cambio del retraso de IPPO con mensajes\nfrente al fijo ajustado (%)\n"
                      "negativo = menos retraso = mejora", fontsize=8.2, linespacing=1.4)
        # dos leyendas con titulo: la red (color y forma), arriba, y el veredicto (relleno del marcador), en el
        # hueco de abajo a la izquierda, sobre la linea de la meta
        punto = dict(ls="", ms=7.0)
        por_red = [Line2D([], [], marker=FORMA_RED[r], mfc=COLOR_RED[r], mec=COLOR_RED[r], color=COLOR_RED[r],
                          lw=1.4, ms=TAM_RED[r], label=RED_FIG[r]) for r in REDES]
        por_veredicto = [
            Line2D([], [], marker="o", mfc=TINTA2, mec=TINTA2, label="FUNCIONA o FALLA, según la banda", **punto),
            Line2D([], [], marker="o", fillstyle="bottom", mfc=TINTA2, markerfacecoloralt=FONDO, mec=TINTA2,
                   mew=BORDE_MEJORA, label="MEJORA", **dict(punto, ms=punto["ms"] + MAS_MEJORA)),
            Line2D([], [], marker="o", mfc=FONDO, mec=TINTA2, mew=1.4, label="EMPATA", **punto),
            # el provisional no se ve en el marcador (el color dice la red): esta en la tabla, y el pie de figura lo
            # dice (en la leyenda, una segunda linea la haria crecer hasta el cuadrado de red 1358)
            ax.scatter([], [], s=7.6 ** 2, marker="o", facecolors=FONDO, edgecolors=TINTA2, linewidths=1.5,
                       linestyle=(0, (1.3, 1.1)), label="PENDIENTE (no se estabilizó)"),
            Line2D([], [], marker="|", ms=10, mew=1.1, color=TINTA2, ls="", label="IC95 %")]
        comun = dict(fontsize=7.4, title_fontsize=7.6, handletextpad=0.5, alignment="left", labelcolor=TINTA)
        # la de dentro va con add_artist (queda recortada a los ejes, y no cuenta para bbox_inches="tight") y la
        # de arriba es la leyenda principal de los ejes, para que el recorte del PNG y del PDF la incluya
        sobre_meta = (META + 1.2 - y0) / (y1 - y0)
        ley1 = ax.legend(handles=por_veredicto, ncol=1, loc="lower left", bbox_to_anchor=(0.008, sobre_meta),
                         title="Veredicto: relleno del marcador", handlelength=1.4, labelspacing=0.35,
                         frameon=True, facecolor=FONDO, edgecolor="#e1e0d9", framealpha=1.0, fancybox=False,
                         borderaxespad=0.0, **comun)
        ley1.get_frame().set_linewidth(0.6)
        ax.add_artist(ley1)
        ax.legend(handles=por_red, ncol=3, loc="lower left", bbox_to_anchor=(-0.01, 1.0),
                  title="Red: color y forma", handlelength=2.4, columnspacing=1.6, frameon=False,
                  borderaxespad=0.2, **comun)
        for ley in ax.get_legend(), ley1:
            ley.get_title().set_color(TINTA2)
        fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=FONDO)
        pdf = os.path.splitext(ruta)[0] + ".pdf"
        fig.savefig(pdf, bbox_inches="tight", facecolor=FONDO, metadata={"CreationDate": None})
        plt.close(fig)
    print("Escrito", ruta)
    print("Escrito", pdf)


# ---------------- Principal ----------------

def resumen_consola(filas):
    print(f"\n{'red':16s} {'veh/h':>5s} {'caso':4s} {'fijo':>7s} {'act':>7s} {'ippo':>7s} {'base':>5s} "
          f"{'conv':4s} {'cambio fijo':>24s} {'c. ciclo min':>12s} {'=cm':3s} veredicto")
    for f in filas:
        cf = f"{txt(f['cambio_fijo'], 1)} {vd.txt_ic(f['ic_fijo'])} p={vd.txt_p(f['p_fijo'])}"
        ver, prov = palabra(f["veredicto"])
        print(f"{NOMBRE_RED[f['red']]:16s} {f['vehiculos_hora']:5d} {f['caso_plan']:4s} {txt(f['retraso_fijo'], 2):>7s} "
              f"{txt(f['retraso_actuado'], 2):>7s} {txt(f['retraso_ippo'], 2):>7s} {f['base_evaluada']:>5} "
              f"{f['entrenamientos_estables']:4s} {cf:>24s} {txt(f['cambio_ciclo_minimo'], 1):>12s} "
              f"{'si' if f['igual_ciclo_minimo'] else 'no':3s} {ver}" + (f" (provisional {prov})" if prov else ""))


def main():
    global vd
    ap = argparse.ArgumentParser(description="Curva de demanda de IPPO con mensajes en cada red (entrega 3).")
    ap.add_argument("--plan2", default=os.path.join(DIR, "plan2"))
    ap.add_argument("--tesis", default=os.path.join(DIR, "TESIS"))
    ap.add_argument("--veredicto", default=DIR, help="carpeta del veredicto.py que se usa (por defecto, esta)")
    args = ap.parse_args()
    vd = cargar("veredicto", os.path.join(os.path.abspath(args.veredicto), "veredicto.py"))
    vd.configurar(metrica=METRICA)     # la referencia queda en el brazo "fijo": el fijo ajustado de cada nivel
    plan2 = os.path.abspath(args.plan2)
    filas = calcular(plan2)
    escribir_csv(os.path.join(plan2, "demanda2", "resumen_demanda2.csv"), filas)
    escribir(os.path.join(args.tesis, "secciones", "tablas", "demanda2.tex"), tabla_tex(filas))
    figura(filas, os.path.join(args.tesis, "images", "fig_demanda_bandas.png"))
    resumen_consola(filas)
    print("\nComprobaciones:", "todas cuadran" if not avisos else f"{len(avisos)} avisos")
    for a in avisos:
        print("  AVISO:", a)


if __name__ == "__main__":
    main()
