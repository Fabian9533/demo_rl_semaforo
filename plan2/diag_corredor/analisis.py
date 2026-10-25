"""
analisis.py - Responde el prerregistro del diagnostico del corredor (PRERREGISTRO.md, con la Enmienda 1).

Cuando termine la cola (ids diag_*, plan2/cola/; lanzada el 25.10.2026 a las 13:38 con el commit 43596e4):
  1. Comprobar que no quedan trabajos diag_ pendientes ni fallidos (plan2/cola/estado.json o cola.log).
  2. Desde demo_rl/plan2 (o desde cualquier carpeta; las rutas salen de la ubicacion de este archivo):
       python diag_corredor/analisis.py
     Exige los 60 metas de las variantes (45 de la primera ronda y 15 de la Enmienda 2) y las evaluaciones que usa: la base mediana de cada variante en los
     dos juegos de semillas, y las referencias y la version actual en 6001-6030. Si falta algo, lo lista y sale
     con codigo 1 sin escribir nada. Si esta todo, escribe:
       plan2/diag_corredor/resultados.csv      una fila por nivel, juego de semillas, control y referencia
       plan2/diag_corredor/pruebas.txt         H1-H5 y el criterio de causa raiz (con V2+INS y con V2+INS+obs),
                                               con PASA o NO PASA y cifras
       TESIS/secciones/tablas/diag_corredor.tex   solo el tabular (retraso total frente al fijo desde 10 s)
       TESIS/secciones/tablas/diag_pruebas.tex    solo el tabular de las pruebas H2-H5 (Anexo G)
       TESIS/images/fig_diag_corredor.pdf y .png
     Tarda menos de un minuto (10 000 remuestreos por comparacion, unas 300 comparaciones).

Modo prueba (para probar el script antes de que termine la cola):
       python diag_corredor/analisis.py --prueba
  Usa lo que ya existe. Una variante cuyas tres metas o cuya evaluacion de la base mediana falten se
  reemplaza por la version evaluada actual (columna fuente = "sustituto"), y un juego de semillas sin datos se
  omite. Escribe todo en plan2/diag_corredor/prueba/ (nunca en TESIS/), con la figura marcada como prueba.
  En los dos modos el script comprueba que la version actual en 1001-1030 reproduce las cifras de
  descomposicion.txt (cambios de un decimal y medias de dos decimales) y lo informa en pruebas.txt.

Entradas (todas en plan2/):
  politica_<esc>_vecinos_<v>_s<b>.json    meta de cada entrenamiento de las variantes (v2, ins, v2ins, v2inso):
                                          val_elegido (en retraso total por la enmienda), ep_elegido,
                                          val_total_serie, ep_elegido_timeloss y ep_elegido_total
  politica_<esc>_vecinos_s<b>.json        meta de la version actual (val_elegido en timeLoss)
  resultados_<esc>_ippo_vecinos_<v>_s<b>.csv   solo en modo prueba, si falta el meta (criterio de validacion)
  diag_corredor/eval/eval_<esc>_<brazo>_<1001|6001>.csv   evaluaciones de la cola (generar_trabajos.py,
                                          agregar_diag_corredor): variantes en los dos juegos; referencias y
                                          version actual solo en 6001 (fijo10 no se repite en P1 y P2)
  1001-1030 de la version actual y de las referencias, los parciales del plan (los de descomposicion.py):
    905, 1358, 2715   demanda2/eval_dem_corredor_t<N>_<brazo>.csv; fijo desde 10 s en
                      demanda/eval_corredor_f050|f075|f150_fijo.csv
    P1, P2            parciales/eval_corredor[_alta]_<brazo>.csv; fijo del 25.09 = _fijo_2509, fijo desde
                      10 s = _fijo (el mismo programa)

Reglas (las del plan y las del prerregistro, sin cambios):
  - Version evaluada de una variante: la base mediana de 42, 2042 y 4042 por val_elegido del meta
    (veredicto.base_mediana; empate: la base menor). En las variantes val_elegido esta en retraso total; en la
    version actual, en timeLoss, y su base es la de generar_trabajos.NIVELES_DIAG (se comprueba que coincide).
  - Cambio = (media del control - media de la referencia) / media de la referencia x 100, pareado por semilla,
    con IC95 por bootstrap pareado (10 000 remuestreos) y p de Wilcoxon pareado: evaluar.comparar, tal cual.
  - Veredicto de la regla del plan sobre el retraso total frente al fijo ajustado (veredicto.veredicto: -5 %, IC
    entero bajo cero y p < 0.05, sin perder contra el actuado) y PENDIENTE con el provisional si la base
    evaluada no se estabilizo (veredicto.convergencia sobre la serie de validacion de su criterio: val_serie en
    la version actual, val_total_serie en las variantes).
  - Pruebas: H2 en 2715 y P2 (INS frente a la version actual: espera para entrar y retraso total, IC entero
    bajo cero), H3 en 1358 (V2 frente a la version actual: cambios de fase, IC entero sobre cero; timeLoss, IC
    entero bajo cero), H4 en P1 (V2+INS frente al fijo desde 10 s, retraso total, IC entero bajo cero) y el
    criterio de causa raiz (V2+INS frente al fijo desde 10 s en retraso total: ningun nivel con IC entero sobre
    cero y p < 0.05, y P1 mejora como en H4). Como pide el prerregistro, H2-H4 miran solo el IC; el p se informa.
    Se evaluan en los dos juegos de semillas por separado: 1001-1030 (comparable con la curva) y 6001-6030
    (confirmacion).
  - Enmienda 2 (segunda ronda, variante v2inso = V2+INS+obs, cola lanzada a las 16:27 con el commit 7cbcdd7): H5
    (V2+INS+obs frente a V2+INS en 2715 y P2: espera para entrar y retraso total, IC entero bajo cero), el mismo
    criterio de causa raiz con V2+INS+obs y, sin prueba, la perdida de valor media de los episodios 181-200 de
    las dos variantes en 2715 y P2 (columna perdida_valor de los CSV de entrenamiento).
"""
import os
import re
import sys
import csv
import json
import math
import argparse
import statistics
import importlib.util

DIR = os.path.dirname(os.path.abspath(__file__))          # plan2/diag_corredor
P2 = os.path.dirname(DIR)                                 # plan2
RAIZ = os.path.dirname(P2)                                # demo_rl
sys.path.insert(0, RAIZ)

import evaluar                                            # noqa: E402  (comparar: bootstrap y Wilcoxon)


def cargar(nombre, ruta):
    """Modulo de un archivo .py por su ruta (como curvas_demanda.cargar)."""
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vd = cargar("veredicto", os.path.join(RAIZ, "veredicto.py"))           # reglas del plan
gt = cargar("generar_trabajos", os.path.join(P2, "generar_trabajos.py"))  # niveles, variantes y bases de la cola

# ---------------- Diseno (de generar_trabajos.py y del prerregistro) ----------------
BASES = gt.BASES                                          # [42, 2042, 4042]
SEMILLAS = {"1001": list(range(1001, 1031)), "6001": list(range(6001, 6031))}
NOMBRE_SEMILLAS = {"1001": "1001-1030", "6001": "6001-6030"}
# clave, nombre corto, demanda total (veh/h), caso del plan
NIVELES = [("905", "905", 905, ""), ("1358", "1358", 1358, ""), ("P1", "1810 (P1)", 1810, "P1"),
           ("2715", "2715", 2715, ""), ("P2", "3620 (P2)", 3620, "P2")]
ESC = {"905": "dem_corredor_t905", "1358": "dem_corredor_t1358", "P1": "corredor",
       "2715": "dem_corredor_t2715", "P2": "corredor_alta"}
DIAG = {esc: (base, fijo10) for esc, base, fijo10 in gt.NIVELES_DIAG}
VARIANTES = list(gt.VARIANTES_DIAG)                       # ["v2", "ins", "v2ins", "v2inso"]
CONTROLES = ["actual"] + VARIANTES
NOMBRE = {"actual": "versión actual", "v2": "V2", "ins": "INS", "v2ins": "V2+INS", "v2inso": "V2+INS+obs"}
REFERENCIAS = ["fijo", "fijo10", "trivial", "actuado", "actual"]
NOMBRE_REF = {"fijo": "fijo de la regla del 25.09", "fijo10": "fijo ajustado desde 10 s",
              "trivial": "ciclo mínimo", "actuado": "actuado", "actual": "versión actual", "v2ins": "V2+INS"}
# Enmienda 2: comparaciones entre variantes (control: referencia), ademas de las REFERENCIAS
ENTRE_VARIANTES = {"v2inso": "v2ins"}
METRICAS = [("timeloss", "timeloss_prom", "timeLoss"), ("total", "retraso_total_prom", "retraso total"),
            ("espera_entrar", "retraso_insercion_prom", "espera para entrar"),
            ("cambios_fase", "cambios_fase", "cambios de fase")]
COL_METRICA = {k: c for k, c, _ in METRICAS}
NOMBRE_METRICA = {k: n for k, _, n in METRICAS}

avisos = []


def aviso(texto):
    avisos.append(texto)


# ---------------- Rutas ----------------

def ruta_1001(nivel, brazo):
    """Parcial del plan con 1001-1030 para una referencia o la version actual (brazo ippo_vecinos_s<b>)."""
    esc = ESC[nivel]
    if nivel in ("P1", "P2"):
        nombre = {"fijo": f"eval_{esc}_fijo_2509.csv", "fijo10": f"eval_{esc}_fijo.csv"}.get(
            brazo, f"eval_{esc}_{brazo}.csv")
        return os.path.join(P2, "parciales", nombre)
    if brazo == "fijo10":
        return os.path.join(P2, "demanda", f"eval_{DIAG[esc][1]}_fijo.csv")
    return os.path.join(P2, "demanda2", f"eval_{esc}_{brazo}.csv")


def ruta_diag(nivel, brazo, k):
    """Evaluacion de la cola diag_ (diag_corredor/eval/eval_<esc>_<brazo>_<k>.csv)."""
    esc = ESC[nivel]
    if brazo == "fijo10" and DIAG[esc][1] is None:
        brazo = "fijo"                    # P1 y P2: el fijo desde 10 s es el mismo programa y no se repite
    return os.path.join(DIR, "eval", f"eval_{esc}_{brazo}_{k}.csv")


def ruta_ref(nivel, brazo, k):
    return ruta_1001(nivel, brazo) if k == "1001" else ruta_diag(nivel, brazo, k)


def ruta_meta(nivel, control, base):
    var = "vecinos" if control == "actual" else f"vecinos_{control}"
    return os.path.join(P2, f"politica_{ESC[nivel]}_{var}_s{base}.json")


def ruta_entrenamiento(nivel, control, base):
    var = "vecinos" if control == "actual" else f"vecinos_{control}"
    return os.path.join(P2, f"resultados_{ESC[nivel]}_ippo_{var}_s{base}.csv")


def rel(ruta):
    return os.path.relpath(ruta, P2).replace("\\", "/")


# ---------------- Lectura ----------------

def leer_eval(ruta, k):
    """{semilla: fila} de un CSV de evaluar.py, o None si no existe. Avisa si no trae las 30 semillas."""
    if not os.path.exists(ruta):
        return None
    with open(ruta, newline="", encoding="utf-8") as f:
        filas = {int(r["semilla"]): r for r in csv.DictReader(f) if r.get("semilla", "").isdigit()}
    if sorted(filas) != SEMILLAS[k]:
        aviso(f"{rel(ruta)}: {len(filas)} semillas, se esperaban {NOMBRE_SEMILLAS[k]}")
    return filas


def media(valores):
    """statistics.mean (suma exacta), como descomposicion.py: con sum/len una media de P1 (19.845) redondea
    distinto en el segundo decimal."""
    return statistics.mean(valores)


def media_col(d, clave):
    return media(float(r[COL_METRICA[clave]]) for r in d.values())


def leer_json(ruta):
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def elegir_checkpoint(serie):
    """La fila de menor valor (empate: la mas tardia), igual que rl_ippo.elegir_checkpoint (no se importa
    rl_ippo para no cargar torch)."""
    return min(reversed(serie), key=lambda f: f[-1])


def serie_csv(ruta, columna):
    """[[ep, valor]] de las filas de validacion del CSV de entrenamiento (puede estar a medias)."""
    if not os.path.exists(ruta):
        return []
    with open(ruta, newline="", encoding="utf-8") as f:
        return [[int(r["episodio"]), float(r[columna])] for r in csv.DictReader(f) if r.get(columna)]


def entrenamiento(nivel, control, base):
    """Datos de validacion de una base: criterio, val y episodio elegidos, convergencia (con la serie del
    criterio) y el episodio que elegiria cada criterio. None si no hay meta."""
    meta = leer_json(ruta_meta(nivel, control, base))
    if meta is None:
        return None
    criterio = (meta.get("opciones") or {}).get("criterio_val", "timeloss")
    if control != "actual" and criterio != "total":
        aviso(f"{rel(ruta_meta(nivel, control, base))}: criterio_val {criterio}, la enmienda pide total")
    serie_tl = meta.get("val_serie") or []
    serie_tot = meta.get("val_total_serie") or []
    serie = serie_tot if criterio == "total" else serie_tl
    pares = sorted((int(x[0]), float(x[-1])) for x in serie)
    episodios = float(meta.get("episodios") or (pares[-1][0] if pares else 0))
    conv, plateau, estab = vd.convergencia(pares, episodios) if pares else (False, None, None)
    ep_tl = meta.get("ep_elegido_timeloss", elegir_checkpoint(serie_tl)[0] if serie_tl else None)
    ep_tot = meta.get("ep_elegido_total", elegir_checkpoint(serie_tot)[0] if serie_tot else None)
    return {"base": base, "criterio": criterio, "val": vd.flotante(meta.get("val_elegido")),
            "ep": meta.get("ep_elegido"), "convergio": conv, "plateau": plateau, "estabilidad": estab,
            "ep_timeloss": ep_tl, "ep_total": ep_tot, "fuente": "meta"}


# ---------------- Version evaluada de cada control ----------------

def version_evaluada(nivel, control, prueba, faltan):
    """{base, info, por_base}: la base mediana por val_elegido y sus datos de entrenamiento."""
    esc = ESC[nivel]
    por_base = {b: entrenamiento(nivel, control, b) for b in BASES}
    vals = {b: i["val"] for b, i in por_base.items() if i is not None and i["val"] is not None}
    base = vd.base_mediana(vals)
    if control == "actual":
        if base != DIAG[esc][0]:
            aviso(f"{nivel}: la base mediana de la version actual da {base}, generar_trabajos dice {DIAG[esc][0]}")
        base = DIAG[esc][0]
    if control != "actual" and not prueba:
        # la Enmienda 1 pide elegir por el retraso total: en el modo final un meta con otro criterio detiene el
        # analisis (en modo prueba solo queda el aviso de entrenamiento())
        for b, i in por_base.items():
            if i is not None and i["criterio"] != "total":
                faltan.append(f"{rel(ruta_meta(nivel, control, b))} (criterio_val {i['criterio']}; la enmienda pide total)")
    if base is None:
        for b, i in por_base.items():
            if i is None:
                faltan.append(rel(ruta_meta(nivel, control, b)))
            elif i["val"] is None:
                # base_mediana exige las tres bases: un meta sin val_elegido deja la variante sin version evaluada
                faltan.append(f"{rel(ruta_meta(nivel, control, b))} (meta sin val_elegido)")
        return {"base": None, "info": None, "por_base": por_base}
    return {"base": base, "info": por_base[base], "por_base": por_base}


def datos_control(nivel, control, k, version, actual, prueba, faltan):
    """(datos por semilla, fuente, version) de un control en un juego de semillas. En modo prueba, una
    variante que no tiene version evaluada o evaluacion se reemplaza por la version actual."""
    if control == "actual":
        b = version["base"]
        ruta = ruta_1001(nivel, f"ippo_vecinos_s{b}") if k == "1001" else ruta_diag(nivel, f"ippo_vecinos_s{b}", k)
        d = leer_eval(ruta, k)
        if d is None:
            faltan.append(rel(ruta))
        return d, "versión actual", version
    d = None
    if version["base"] is not None:
        ruta = ruta_diag(nivel, f"ippo_vecinos_{control}_s{version['base']}", k)
        d = leer_eval(ruta, k)
        if d is None:
            faltan.append(rel(ruta))
    if d is not None:
        return d, "variante", version
    if prueba and actual[k][0] is not None:
        return actual[k][0], "sustituto (versión actual)", actual["version"]
    return None, "", version


# ---------------- Comparaciones ----------------

def comparar(ctrl, ref):
    """Por metrica: media del control y de la referencia, cambio %, IC95 y p (evaluar.comparar sobre las
    semillas comunes, en orden)."""
    comunes = sorted(set(ctrl) & set(ref))
    res = {"n": len(comunes)}
    for clave, col, _ in METRICAS:
        a = [float(ctrl[s][col]) for s in comunes]
        b = [float(ref[s][col]) for s in comunes]
        c = evaluar.comparar(a, b)
        res[f"media_{clave}"] = media(a)
        res[f"media_ref_{clave}"] = media(b)
        if c:
            lo, hi = (float(x) for x in c["delta_ic95"].strip("[]").split(","))
            res.update({f"cambio_{clave}": c["delta_pct"], f"ic_{clave}": (lo, hi),
                        f"p_{clave}": float(c["p_wilcoxon"])})
        else:                                 # media de la referencia en 0
            res.update({f"cambio_{clave}": None, f"ic_{clave}": None, f"p_{clave}": None})
    return res


def veredicto_total(c_fijo, c_act, info):
    """Regla del plan sobre el retraso total frente a una referencia fija (c_fijo) y al actuado (c_act)."""
    if c_fijo.get("cambio_total") is None:
        return "PENDIENTE (sin datos)"
    prov = vd.veredicto(c_fijo["cambio_total"], c_fijo["ic_total"], c_fijo["p_total"],
                        c_act["ic_total"] if c_act else None, c_act["p_total"] if c_act else None)
    return vd.texto_veredicto(prov, convergio=bool(info and info["convergio"]))


def calcular(prueba):
    """Todas las filas de resultados.csv, mas lo que necesitan las pruebas, la tabla y la figura."""
    faltan, filas, medias = [], [], {}
    versiones = {}
    for nivel, _, _, _ in NIVELES:
        for control in CONTROLES:
            versiones[(nivel, control)] = version_evaluada(nivel, control, prueba, faltan)
    R = {}
    for nivel, nombre, veh, caso in NIVELES:
        for k in SEMILLAS:
            refs = {}
            for brazo in REFERENCIAS[:-1]:
                ruta = ruta_ref(nivel, brazo, k)
                refs[brazo] = leer_eval(ruta, k)
                if refs[brazo] is None:
                    faltan.append(rel(ruta))
            actual = {"version": versiones[(nivel, "actual")]}
            actual[k] = datos_control(nivel, "actual", k, actual["version"], None, prueba, faltan)
            refs["actual"] = actual[k][0]
            datos = {"actual": actual[k]}
            for v in VARIANTES:
                datos[v] = datos_control(nivel, v, k, versiones[(nivel, v)], actual, prueba, faltan)
            medias[(nivel, k)] = {b: d for b, d in refs.items() if d is not None}
            for control in CONTROLES:
                d, fuente, version = datos[control]
                if d is None:
                    continue
                medias[(nivel, k)][control] = d
                info = version["info"]
                comps = {}
                for ref in REFERENCIAS:
                    # (en modo prueba, un sustituto frente a la version actual da cambio 0 e IC [0, 0]: se deja
                    # para que H2 y H3 recorran el mismo camino que con los datos reales)
                    if ref == control or refs.get(ref) is None:
                        continue
                    comps[ref] = comparar(d, refs[ref])
                otra = ENTRE_VARIANTES.get(control)
                if otra and datos[otra][0] is not None:
                    comps[otra] = comparar(d, datos[otra][0])
                for ref, c in comps.items():
                    ver = ""
                    if ref in ("fijo", "fijo10"):
                        ver = veredicto_total(c, comps.get("actuado"), info)
                    fila = {"nivel": nivel, "veh_h": veh, "escenario": ESC[nivel], "semillas": NOMBRE_SEMILLAS[k],
                            "control": control, "fuente": fuente, "base_evaluada": version["base"],
                            "criterio_val": info["criterio"] if info else "", "val_elegido": info["val"] if info else "",
                            "ep_elegido": info["ep"] if info else "",
                            "convergio": ("si" if info["convergio"] else "no") if info else "",
                            "referencia": ref, "n_semillas": c["n"], "veredicto_total": ver}
                    for clave, _, _ in METRICAS:
                        ic = c[f"ic_{clave}"]
                        fila.update({f"media_{clave}": round(c[f"media_{clave}"], 3),
                                     f"media_ref_{clave}": round(c[f"media_ref_{clave}"], 3),
                                     f"cambio_{clave}": c[f"cambio_{clave}"],
                                     f"ic_lo_{clave}": ic[0] if ic else "", f"ic_hi_{clave}": ic[1] if ic else "",
                                     f"p_{clave}": c[f"p_{clave}"]})
                    filas.append(fila)
                    R[(nivel, k, control, ref)] = dict(c, veredicto=ver, fuente=fuente)
    return filas, R, medias, versiones, sorted(set(faltan))


COLUMNAS = (["nivel", "veh_h", "escenario", "semillas", "control", "fuente", "base_evaluada", "criterio_val",
             "val_elegido", "ep_elegido", "convergio", "referencia", "n_semillas"]
            + [f"{p}_{k}" for k, _, _ in METRICAS for p in ("media", "media_ref", "cambio", "ic_lo", "ic_hi", "p")]
            + ["veredicto_total"])


def escribir_csv(ruta, filas):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for fila in filas:
            w.writerow({c: ("" if fila.get(c) is None else fila.get(c)) for c in COLUMNAS})
    print("Escrito", ruta)


# ---------------- Comprobacion contra descomposicion.txt ----------------

def comprobar_descomposicion(R, medias, versiones):
    """La version actual en 1001-1030 debe dar los cambios y medias de descomposicion.txt."""
    ruta = os.path.join(DIR, "descomposicion.txt")
    if not os.path.exists(ruta):
        return ["descomposicion.txt no existe: comprobacion omitida"], 0, 0
    clave_nivel = {"905": "905", "1358": "1358", "1810 P1": "P1", "2715": "2715", "3620 P2": "P2"}
    ref_de = {"fijo 25.09": "fijo", "fijo desde 10 s": "fijo10", "ciclo min": "trivial", "actuado": "actuado"}
    brazo_de = {"ippo": "actual", "fijo": "fijo", "fijo10": "fijo10", "triv": "trivial", "act": "actuado"}
    metrica_de = {"timeLoss": "timeloss", "retraso total": "total"}
    lineas, ok, total, nivel = [], 0, 0, None
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            m = re.match(r"=== Corredor (.+) veh/h", linea)
            if m:
                nivel = clave_nivel[m.group(1).strip()]
                continue
            m = re.match(r"\s+IPPO vs \[(.+)\]: (.+)", linea)
            if m and nivel:
                met = metrica_de[m.group(1)]
                for parte in m.group(2).split("|"):
                    nombre, valor = parte.strip().rsplit(" ", 1)
                    esperado = float(valor.rstrip("%"))
                    c = R.get((nivel, "1001", "actual", ref_de[nombre]))
                    obtenido = c[f"cambio_{met}"] if c else None
                    total += 1
                    if obtenido is not None and abs(obtenido - esperado) < 1e-9:
                        ok += 1
                    else:
                        lineas.append(f"{nivel} {m.group(1)} frente a {nombre}: descomposicion {esperado:+.1f}, "
                                      f"aqui {obtenido}")
                continue
            m = re.match(r"\s+(ippo|fijo10|fijo|triv|act)\s+timeLoss\s+([\d.]+)\s+total\s+([\d.]+)\s+espera_entrar"
                         r"\s+([\d.]+)\s+cambios_fase\s+([\d.]+)", linea)
            if m and nivel:
                d = medias.get((nivel, "1001"), {}).get(brazo_de[m.group(1)])
                for clave, texto, dec in (("timeloss", m.group(2), 2), ("total", m.group(3), 2),
                                          ("espera_entrar", m.group(4), 2), ("cambios_fase", m.group(5), 1)):
                    total += 1
                    if d is None:
                        lineas.append(f"{nivel} {m.group(1)}: sin datos")
                        continue
                    mu = media_col(d, clave)
                    if f"{mu:.{dec}f}" == texto:
                        ok += 1
                    else:
                        lineas.append(f"{nivel} {m.group(1)} {clave}: descomposicion {texto}, aqui {mu:.{dec}f}")
    return lineas, ok, total


# ---------------- Pruebas del prerregistro ----------------

def txt_pct(x):
    return "   --" if x is None else f"{x:+.1f} %"


def txt_ic(ic):
    return "--" if not ic else f"[{ic[0]:+.1f}, {ic[1]:+.1f}]"


def txt_p(p):
    return "--" if p is None else f"{p:.2g}"


def condicion(R, nivel, k, control, ref, clave, sentido):
    """(cumple, linea): IC95 del cambio entero bajo cero (sentido "bajo") o sobre cero ("sobre")."""
    c = R.get((nivel, k, control, ref))
    if c is None or c.get(f"ic_{clave}") is None:
        return None, f"    {nivel:5s} {NOMBRE_METRICA[clave]:19s} sin datos"
    lo, hi = c[f"ic_{clave}"]
    cumple = hi < 0 if sentido == "bajo" else lo > 0
    unidad = "" if clave == "cambios_fase" else " s/veh"
    dec = 1 if clave == "cambios_fase" else 2
    sust = "  [sustituto]" if c["fuente"].startswith("sustituto") else ""
    if (hi if sentido == "bajo" else lo) == 0:
        sust += "  [extremo del IC en 0.0 por el redondeo]"
    return cumple, (f"    {nivel:5s} {NOMBRE_METRICA[clave]:19s} {c[f'media_ref_{clave}']:8.{dec}f} -> "
                    f"{c[f'media_{clave}']:8.{dec}f}{unidad}  {txt_pct(c[f'cambio_{clave}']):>9s} "
                    f"{txt_ic(c[f'ic_{clave}']):>16s}  p={txt_p(c[f'p_{clave}']):7s} "
                    f"{'cumple' if cumple else 'no cumple'}{sust}")


def resultado(lista):
    if any(x is None for x in lista):
        return "SIN DATOS"
    return "PASA" if all(lista) else "NO PASA"


def prueba_juego(R, k, conds):
    """conds = [(nivel, control, ref, clave, sentido)]: lineas y PASA / NO PASA en el juego k."""
    lineas, cumple = [], []
    for nivel, control, ref, clave, sentido in conds:
        c, linea = condicion(R, nivel, k, control, ref, clave, sentido)
        cumple.append(c)
        lineas.append(linea)
    return lineas, resultado(cumple)


def bloque_hipotesis(R, titulo, enunciado, conds, juegos):
    lineas = [titulo, f"  {enunciado}"]
    res = {}
    for k in juegos:
        l, r = prueba_juego(R, k, conds)
        res[k] = r
        lineas += [f"  Semillas {NOMBRE_SEMILLAS[k]} (referencia -> control, cambio, IC95 bootstrap pareado, "
                   f"p de Wilcoxon):"] + l + [f"    => {r}"]
    lineas.append(f"  Resultado: " + "; ".join(f"{res[k]} en {NOMBRE_SEMILLAS[k]}" for k in juegos))
    return lineas, res


def bloque_criterio(R, juegos, control="v2ins", titulo="CRITERIO DE CAUSA RAÍZ CORREGIDA"):
    lineas = [titulo,
              f"  {NOMBRE[control]} frente al fijo ajustado desde 10 s, retraso total: ningún nivel peor con IC entero",
              "  sobre cero y p < 0.05, y P1 sigue mejorando (IC entero bajo cero, como H4)."]
    res = {}
    for k in juegos:
        lineas.append(f"  Semillas {NOMBRE_SEMILLAS[k]}:")
        peores, sin = [], False
        for nivel, _, _, _ in NIVELES:
            c = R.get((nivel, k, control, "fijo10"))
            if c is None or c.get("ic_total") is None:
                lineas.append(f"    {nivel:5s} sin datos")
                sin = True
                continue
            peor = c["ic_total"][0] > 0 and c["p_total"] < vd.ALFA
            if peor:
                peores.append(nivel)
            sust = "  [sustituto]" if c["fuente"].startswith("sustituto") else ""
            if c["ic_total"][0] == 0:
                sust += "  [extremo del IC en 0.0 por el redondeo]"
            lineas.append(f"    {nivel:5s} {c['media_ref_total']:8.2f} -> {c['media_total']:8.2f} s/veh  "
                          f"{txt_pct(c['cambio_total']):>9s} {txt_ic(c['ic_total']):>16s}  p={txt_p(c['p_total']):7s} "
                          f"{'PEOR que el fijo' if peor else 'no peor'}  ({vd.palabra(c['veredicto'])}){sust}")
        p1, _ = condicion(R, "P1", k, control, "fijo10", "total", "bajo")
        if sin or p1 is None:
            res[k] = "SIN DATOS"
        else:
            res[k] = "PASA" if not peores and p1 else "NO PASA"
        detalle = []
        if peores:
            detalle.append("peor en " + ", ".join(peores))
        if p1 is False:
            detalle.append("P1 no mejora con IC entero bajo cero")
        lineas.append(f"    => {res[k]}" + (f" ({'; '.join(detalle)})" if detalle else ""))
    lineas.append(f"  Resultado: " + "; ".join(f"{res[k]} en {NOMBRE_SEMILLAS[k]}" for k in juegos))
    return lineas, res


def bloque_h1(R, juegos):
    lineas = ["H1 (referencia). Se reporta; no tiene prueba. Versión actual frente a las dos reglas del fijo:"]
    for k in juegos:
        lineas.append(f"  Semillas {NOMBRE_SEMILLAS[k]}:")
        for nivel, _, _, _ in NIVELES:
            partes = []
            for ref in ("fijo", "fijo10", "trivial"):
                c = R.get((nivel, k, "actual", ref))
                if c:
                    partes.append(f"{NOMBRE_REF[ref]} {txt_pct(c['cambio_timeloss']).strip()} (timeLoss), "
                                  f"{txt_pct(c['cambio_total']).strip()} (total)")
            lineas.append(f"    {nivel:5s} " + ("; ".join(partes) if partes else "sin datos"))
    return lineas


def bloque_criterios_validacion(prueba):
    """(5) 2715 y P2: si los criterios timeLoss y total eligen el mismo episodio en cada base."""
    lineas = ["CRITERIO DE VALIDACIÓN (Enmienda 1): episodio elegido por timeLoss y por retraso total, 2715 y P2"]
    for nivel in ("2715", "P2"):
        for v in VARIANTES:
            partes = []
            for b in BASES:
                info = entrenamiento(nivel, v, b)
                if info is not None and info["ep_timeloss"] is not None and info["ep_total"] is not None:
                    fuente = ""
                else:
                    info = None
                    if prueba:
                        tl = serie_csv(ruta_entrenamiento(nivel, v, b), "val")
                        tot = serie_csv(ruta_entrenamiento(nivel, v, b), "val_total")
                        if tl and tot:
                            info = {"ep_timeloss": elegir_checkpoint(tl)[0], "ep_total": elegir_checkpoint(tot)[0]}
                            fuente = f", parcial: {max(e for e, _ in tl)} episodios del CSV"
                if info is None:
                    partes.append(f"s{b} sin datos")
                    continue
                igual = "mismo" if info["ep_timeloss"] == info["ep_total"] else "distinto"
                partes.append(f"s{b} {info['ep_timeloss']}/{info['ep_total']} ({igual}{fuente})")
            lineas.append(f"  {nivel:5s} {NOMBRE[v]:7s} timeLoss/total: " + "; ".join(partes))
    lineas.append("  La versión actual se eligió por timeLoss y su meta no trae val_total_serie: en las comparaciones")
    lineas.append("  con ella el cambio incluye el del criterio.")
    return lineas


def bloque_perdida_valor():
    """Enmienda 2, sin prueba: perdida de valor (critico) media de los episodios 181-200 por base, V2+INS y
    V2+INS+obs en 2715 y P2, de los CSV de entrenamiento (con V2 como referencia de escala)."""
    lineas = ["COMPROBACIÓN DESCRIPTIVA (Enmienda 2): pérdida de valor media de los episodios 181-200, por base"]
    for nivel in ("2715", "P2"):
        for control in ("v2", "v2ins", "v2inso"):
            partes = []
            for b in BASES:
                ruta = ruta_entrenamiento(nivel, control, b)
                if not os.path.exists(ruta):
                    partes.append(f"s{b} --")
                    continue
                with open(ruta, newline="", encoding="utf-8") as f:
                    filas = [r for r in csv.DictReader(f) if 181 <= int(r["episodio"]) <= 200]
                partes.append(f"s{b} {media(float(r['perdida_valor']) for r in filas):.2f}" if len(filas) == 20
                              else f"s{b} -- ({len(filas)} de 20 episodios)")
            lineas.append(f"  {nivel:5s} {NOMBRE[control]:11s} " + ", ".join(partes))
    return lineas


def bloque_versiones(versiones):
    lineas = ["VERSIÓN EVALUADA DE CADA CONTROL (base mediana por val_elegido)"]
    for nivel, _, _, _ in NIVELES:
        for control in CONTROLES:
            v = versiones[(nivel, control)]
            vals = ", ".join(f"s{b} {i['val']:.2f}" if i and i["val"] is not None else f"s{b} --"
                             for b, i in v["por_base"].items())
            info = v["info"]
            if info:
                conv = (f"se estabilizó" if info["convergio"] else "NO se estabilizó") + (
                    f" (meseta {info['plateau']:+.1f} %, estabilidad {info['estabilidad']:.1f} %)"
                    if info["plateau"] is not None else "")
                lineas.append(f"  {nivel:5s} {NOMBRE[control]:15s} base {v['base']:>5}  criterio {info['criterio']:8s} "
                              f"val {vals}; episodio {info['ep']}; {conv}")
            else:
                lineas.append(f"  {nivel:5s} {NOMBRE[control]:15s} sin entrenamientos completos (val: {vals})")
    return lineas


def bloque_medias(medias, juegos):
    lineas = ["MEDIAS POR CONTROL (s/veh; cambios de fase por corrida, suma de los dos semáforos)"]
    orden = CONTROLES + ["fijo", "fijo10", "trivial", "actuado"]
    for k in juegos:
        lineas.append(f"  Semillas {NOMBRE_SEMILLAS[k]}:")
        for nivel, _, _, _ in NIVELES:
            for b in orden:
                d = medias.get((nivel, k), {}).get(b)
                if d is None:
                    continue
                m = {c: media_col(d, c) for c in COL_METRICA}
                nombre = NOMBRE.get(b, NOMBRE_REF.get(b))
                lineas.append(f"    {nivel:5s} {nombre:27s} timeLoss {m['timeloss']:7.2f}  total {m['total']:7.2f}  "
                              f"espera para entrar {m['espera_entrar']:6.2f}  cambios de fase {m['cambios_fase']:6.1f}")
    return lineas


def texto_pruebas(R, medias, versiones, prueba, sustituidos, comprob):
    juegos = [k for k in SEMILLAS if any(key[1] == k for key in R)]
    lineas = ["Diagnóstico de la curva del corredor: respuesta al prerregistro (PRERREGISTRO.md, Enmiendas 1 y 2)",
              "Generado por plan2/diag_corredor/analisis.py. No editar a mano.", ""]
    if prueba:
        lineas += ["*** MODO PRUEBA: no son los resultados del diagnóstico. ***"]
        if sustituidos:
            lineas += ["Controles sustituidos por la versión actual (faltan sus entrenamientos o evaluaciones):",
                       "  " + ", ".join(sustituidos)]
        omitidos = [NOMBRE_SEMILLAS[k] for k in SEMILLAS if k not in juegos]
        if omitidos:
            lineas.append("Juegos de semillas sin datos, omitidos: " + ", ".join(omitidos))
        lineas.append("")
    lineas += ["Referencia principal: fijo ajustado desde 10 s. Métrica principal: retraso total (timeLoss + espera",
               "para entrar). Cambio pareado por semilla, IC95 por bootstrap pareado (10 000 remuestreos) y p de",
               "Wilcoxon pareado (evaluar.comparar). H2-H5 miran solo el IC, como dice el prerregistro.",
               "El IC llega redondeado a 0.1 (evaluar.comparar), y 'IC entero bajo/sobre cero' se lee sobre ese valor,",
               "como en veredicto.py: un extremo real entre -0.05 y +0.05 queda en 0.0 y no cuenta. Esas líneas",
               "llevan la marca [extremo del IC en 0.0 por el redondeo].", ""]
    lineas += bloque_h1(R, juegos) + [""]
    resumen = {}
    l, resumen["H2"] = bloque_hipotesis(
        R, "H2 (recompensa)", "INS frente a la versión actual en 2715 y P2: (a) espera para entrar y (b) retraso "
        "total, IC entero bajo cero.",
        [(n, "ins", "actual", c, "bajo") for n in ("2715", "P2") for c in ("espera_entrar", "total")], juegos)
    lineas += l + [""]
    l, resumen["H3"] = bloque_hipotesis(
        R, "H3 (objetivo de entrenamiento)", "V2 frente a la versión actual en 1358: (a) cambios de fase, IC entero "
        "sobre cero; (b) timeLoss, IC entero bajo cero.",
        [("1358", "v2", "actual", "cambios_fase", "sobre"), ("1358", "v2", "actual", "timeloss", "bajo")], juegos)
    lineas += l + [""]
    l, resumen["H4"] = bloque_hipotesis(
        R, "H4 (sin regresión)", "V2+INS frente al fijo ajustado desde 10 s en P1, retraso total, IC entero bajo cero.",
        [("P1", "v2ins", "fijo10", "total", "bajo")], juegos)
    lineas += l + [""]
    l, resumen["Criterio"] = bloque_criterio(R, juegos)
    lineas += l + [""]
    lineas += ["ENMIENDA 2 (segunda ronda, escrita con la primera a la vista y antes de entrenar V2+INS+obs)", ""]
    l, resumen["H5"] = bloque_hipotesis(
        R, "H5 (observabilidad)", "V2+INS+obs frente a V2+INS en 2715 y P2: (a) espera para entrar y (b) retraso "
        "total, IC entero bajo cero.",
        [(n, "v2inso", "v2ins", c, "bajo") for n in ("2715", "P2") for c in ("espera_entrar", "total")], juegos)
    lineas += l + [""]
    l, resumen["Criterio 2"] = bloque_criterio(R, juegos, "v2inso",
                                               "CRITERIO DE CAUSA RAÍZ CORREGIDA CON V2+INS+obs (Enmienda 2)")
    lineas += l + [""]
    lineas += bloque_perdida_valor() + [""]
    lineas += ["RESUMEN"] + [f"  {h:10s} " + "; ".join(f"{r[k]} en {NOMBRE_SEMILLAS[k]}" for k in juegos)
                             for h, r in resumen.items()] + [""]
    lineas += bloque_criterios_validacion(prueba) + [""]
    lineas += bloque_versiones(versiones) + [""]
    lineas += bloque_medias(medias, juegos) + [""]
    diferencias, ok, total = comprob
    lineas.append(f"COMPROBACIÓN: la versión actual en 1001-1030 frente a descomposicion.txt: {ok} de {total} cifras "
                  "iguales" + ("" if not diferencias else ", diferencias:"))
    lineas += [f"  {d}" for d in diferencias]
    if avisos:
        lineas += ["", "AVISOS"] + [f"  {a}" for a in avisos]
    return "\n".join(lineas) + "\n", resumen


# ---------------- Tabla .tex ----------------

def tex_signo(x):
    """Cambio con signo en modo matematico ($-6.8$, $+1.8$), como las demas tablas de resultados."""
    return "--" if x is None else f"${x:+.1f}$"


def apilar(lineas):
    return lineas[0] if len(lineas) == 1 else r"\makecell[tl]{" + r"\\{}".join(lineas) + "}"


def tex_veredicto(texto):
    """Lineas del veredicto: la palabra y, si es PENDIENTE por no estabilizarse, el provisional debajo."""
    if not texto:
        return ["--"]
    if texto.startswith("PENDIENTE"):
        prov = texto.split("provisional:")[1].strip(" )") if "provisional:" in texto else None
        # en tres lineas: "(prov.: FUNCIONA)" en una sola ensancha la tabla a 18 cm con cuatro celdas asi
        return ["PENDIENTE", "(provisional:", f"{prov})"] if prov else ["PENDIENTE"]
    return [texto.split(" ")[0]]


def tex_ic(ic):
    return "--" if not ic else f"[${ic[0]:+.1f}$, ${ic[1]:+.1f}$]"


def tabla_tex(R, prueba):
    lineas = [
        "% Generado por plan2/diag_corredor/analisis.py. No editar a mano.",
        "% Diagnóstico del corredor (PRERREGISTRO.md): solo el tabular; el table, el caption y la etiqueta van en el",
        "% capítulo. Fuente: plan2/diag_corredor/resultados.csv, semillas 1001-1030, referencia fijo10 (fijo ajustado",
        "% desde 10 s), columnas media_ref_total, cambio_total y veredicto_total. Veredicto: la regla del plan",
        "% (veredicto.veredicto: -5 %, IC entero bajo cero y p < 0.05, sin perder contra el actuado) sobre el retraso",
        "% total, con PENDIENTE (provisional) si la versión evaluada no se estabilizó en su criterio de validación.",
        "% Cada celda: cambio (%) y veredicto; el IC95 y el p están en resultados.csv y pruebas.txt (con cinco",
        "% controles, el IC en la celda no cabe en 15 cm). Necesita booktabs y makecell; el table lleva",
        "% \\footnotesize y \\setlength{\\tabcolsep}{3pt} (ancho medido por analisis.py en su salida de consola).",
    ]
    if prueba:
        lineas.append("% MODO PRUEBA: las variantes que faltan son la versión actual. No usar en la tesis.")
    cabecera = {"actual": r"\makecell{Versión\\actual}", "v2inso": r"\makecell{V2+INS\\+obs}"}
    lineas += [
        r"\begin{tabular}{lr" + "c" * len(CONTROLES) + "}",
        r"\toprule",
        r" & & \multicolumn{" + str(len(CONTROLES)) + r"}{c}{Cambio del retraso total frente al fijo desde 10 s (\%)} \\",
        rf"\cmidrule(lr){{3-{2 + len(CONTROLES)}}}",
        r"\makecell[tl]{Demanda\\(veh/h)} & \makecell[tr]{Fijo\\desde 10 s\\(s/veh)} & "
        + " & ".join(cabecera.get(c, NOMBRE[c]) for c in CONTROLES) + r" \\",
        r"\midrule",
    ]
    for i, (nivel, nombre, _, _) in enumerate(NIVELES):
        ref, partes = None, []
        for control in CONTROLES:
            c = R.get((nivel, "1001", control, "fijo10"))
            if c is None:
                partes.append("--")
                continue
            ref = c["media_ref_total"]
            # \\{} y no \\ solo: una linea que empiece con [ se leeria como el espacio opcional de \\
            partes.append(r"\makecell[t]{" + r"\\{}".join([tex_signo(c["cambio_total"])]
                                                          + tex_veredicto(c["veredicto"])) + "}")
        celdas = [nombre, "--" if ref is None else f"{ref:.2f}"] + partes
        lineas.append(" & ".join(celdas) + r" \\" + (r"[3pt]" if i < len(NIVELES) - 1 else ""))
    lineas += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lineas) + "\n"


# (hipotesis, nivel, control, referencia, metrica, sentido) de las pruebas del prerregistro, en orden
PRUEBAS_TEX = ([("H2", n, "ins", "actual", c, "bajo") for n in ("2715", "P2") for c in ("espera_entrar", "total")]
               + [("H3", "1358", "v2", "actual", "cambios_fase", "sobre"), ("H3", "1358", "v2", "actual", "timeloss", "bajo"),
                  ("H4", "P1", "v2ins", "fijo10", "total", "bajo")]
               + [("H5", n, "v2inso", "v2ins", c, "bajo") for n in ("2715", "P2") for c in ("espera_entrar", "total")])


def tabla_pruebas_tex(R, prueba):
    """Tabular de las pruebas H2-H5 (Anexo G): cambio e IC95 en 1001-1030 y si cumple en los dos juegos."""
    lineas = [
        "% Generado por plan2/diag_corredor/analisis.py. No editar a mano.",
        "% Pruebas H2-H5 del prerregistro (PRERREGISTRO.md, Enmiendas 1 y 2): cambio pareado e IC95 bootstrap pareado",
        "% en 1001-1030 y si cumple la prediccion (IC entero bajo o sobre cero) en 1001-1030 y en 6001-6030.",
        "% Fuente: plan2/diag_corredor/resultados.csv. Necesita booktabs y makecell; el table lleva \\footnotesize",
        "% y \\setlength{\\tabcolsep}{3pt}.",
    ]
    if prueba:
        lineas.append("% MODO PRUEBA: las variantes que faltan son la versión actual. No usar en la tesis.")
    lineas += [r"\begin{tabular}{llcrccc}", r"\toprule",
               r" & & & & & \multicolumn{2}{c}{¿Cumple?} \\", r"\cmidrule(lr){6-7}",
               r"Nivel & Métrica & \makecell{IC que\\se espera} & \makecell[tr]{Cambio\\(\%)} & IC95 (\%) & "
               r"1001-1030 & 6001-6030 \\", r"\midrule"]
    anterior = None
    for h, nivel, control, ref, clave, sentido in PRUEBAS_TEX:
        c = R.get((nivel, "1001", control, ref))
        cumple = []
        for k in SEMILLAS:
            ck, _ = condicion(R, nivel, k, control, ref, clave, sentido)
            cumple.append("--" if ck is None else ("sí" if ck else "no"))
        nombre = [n for k_, n, _, _ in NIVELES if k_ == nivel][0]
        if h != anterior:
            if anterior is not None:
                lineas.append(r"\addlinespace")
            ref_txt = {"actual": "a la", "fijo10": "al"}.get(ref, "a") + " " + NOMBRE_REF[ref]
            lineas.append(rf"\multicolumn{{7}}{{l}}{{\textbf{{{h}.}} {NOMBRE[control]} frente {ref_txt}}} \\")
        anterior = h
        lineas.append(" & ".join([nombre, NOMBRE_METRICA[clave], "bajo 0" if sentido == "bajo" else "sobre 0",
                                  tex_signo(c[f"cambio_{clave}"]) if c else "--",
                                  tex_ic(c[f"ic_{clave}"]) if c else "--"] + cumple) + r" \\")
    # Enmienda 3 (por que 2715): las filas salen de resultados3.csv (analisis3.py), si ya existe
    ruta3 = os.path.join(DIR, "resultados3.csv")
    if os.path.exists(ruta3):
        with open(ruta3, newline="", encoding="utf-8") as f:
            filas3 = [r for r in csv.DictReader(f) if r["prueba"] in ("H6a", "H6b", "H7")]
        titulos = {"H6a": r"Sin giros a la izquierda: V2 de 2715 (sin reentrenar) frente al fijo",
                   "H6b": r"Sin giros a la izquierda: V2 entrenado ahí frente a su fijo ajustado",
                   "H7": r"V2 con $\gamma = 0.99$ frente a V2"}
        for h in ("H6a", "H6b", "H7"):
            r = {x["semillas"]: x for x in filas3 if x["prueba"] == h}
            if "1001-1030" not in r:
                continue
            a = r["1001-1030"]
            cumple = [("sí" if r[s]["cumple"] == "si" else "no") if s in r else "--" for s in ("1001-1030", "6001-6030")]
            lineas += [r"\addlinespace", rf"\multicolumn{{7}}{{l}}{{\textbf{{{h}.}} {titulos[h]}}} \\",
                       " & ".join(["2715", "retraso total", "bajo 0", tex_signo(float(a["cambio"])),
                                   tex_ic((float(a["ic_lo"]), float(a["ic_hi"])))] + cumple) + r" \\"]
    lineas += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(lineas) + "\n"


def medir_tabla(tex):
    """Ancho del tabular con pdflatex (12 pt, footnotesize, tabcolsep 3pt), en cm; None si no hay LaTeX."""
    import shutil
    import subprocess
    import tempfile
    if not shutil.which("pdflatex"):
        return None
    doc = (r"\documentclass[12pt]{report}\usepackage[utf8]{inputenc}\usepackage[T1]{fontenc}"
           r"\usepackage{booktabs,makecell}\newsavebox\caja\begin{document}"
           r"\begin{lrbox}{\caja}\footnotesize\setlength{\tabcolsep}{3pt}" + tex +
           r"\end{lrbox}\typeout{ANCHO=\the\wd\caja}\end{document}")
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "t.tex"), "w", encoding="utf-8") as f:
            f.write(doc)
        try:
            out = subprocess.run(["pdflatex", "-interaction=nonstopmode", "t.tex"], cwd=tmp, capture_output=True,
                                 text=True, timeout=120, encoding="utf-8", errors="replace").stdout
        except (OSError, subprocess.SubprocessError):
            return None
    m = re.search(r"ANCHO=([\d.]+)pt", out)
    return float(m.group(1)) * 2.54 / 72.27 if m else None


# ---------------- Figura ----------------
# Paleta de curvas_demanda.py (skill dataviz): superficie, tintas, verde y rojo de estado para las bandas. La
# version actual va en la tinta secundaria con linea discontinua (es la referencia de las variantes) y las tres
# variantes en los tres primeros colores categoricos (validados con validate_palette.js), con una forma cada una.
FONDO, TINTA, TINTA2, APAGADO = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
VERDE, ROJO = "#0ca30c", "#d03b3b"
COLOR = {"actual": TINTA2, "v2": "#2a78d6", "ins": "#eb6834", "v2ins": "#1baf7a", "v2inso": "#8f4fd6"}
FORMA = {"actual": "o", "v2": "s", "ins": "^", "v2ins": "D", "v2inso": "v"}
TAM = {"actual": 6.6, "v2": 6.0, "ins": 7.0, "v2ins": 5.6, "v2inso": 7.0}
LINEA = {"actual": (0, (4, 2)), "v2": "-", "ins": "-", "v2ins": "-", "v2inso": "-"}
SEPARA = {"actual": 0.95, "v2": 0.975, "ins": 1.0, "v2ins": 1.025, "v2inso": 1.05}   # en x (escala log)
UMBRAL = vd.UMBRAL_DELTA                                                 # -5 %
MENOS = "−"


def mezcla(color, alfa, fondo=FONDO):
    from matplotlib.colors import to_rgb, to_hex
    return to_hex([alfa * c + (1 - alfa) * f for c, f in zip(to_rgb(color), to_rgb(fondo))])


def figura(R, ruta, prueba):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from matplotlib.ticker import FixedLocator, NullLocator

    banda_clara, banda_pequena, banda_roja = mezcla(VERDE, 0.15), mezcla(VERDE, 0.06), mezcla(ROJO, 0.09)

    def banda(y):
        return banda_roja if y > 0 else (banda_pequena if y > UMBRAL else banda_clara)

    puntos = {c: [] for c in CONTROLES}
    for nivel, _, veh, _ in NIVELES:
        for control in CONTROLES:
            c = R.get((nivel, "1001", control, "fijo10"))
            if c and c["cambio_total"] is not None:
                puntos[control].append((veh * SEPARA[control], c["cambio_total"], c["ic_total"],
                                        vd.palabra(c["veredicto"])))
    todos = [p for s in puntos.values() for p in s]
    y0 = math.floor(min([UMBRAL * 2] + [p[2][0] for p in todos]) / 5) * 5 - 2
    y1 = math.ceil(max([5.0] + [p[2][1] for p in todos]) / 5) * 5 + 3
    with plt.rc_context({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.edgecolor": APAGADO,
                         "axes.labelcolor": TINTA2, "xtick.color": TINTA2, "ytick.color": TINTA2}):
        fig, ax = plt.subplots(figsize=(6.4, 4.3), facecolor=FONDO)
        ax.set_facecolor(FONDO)
        ax.set_xscale("log")
        ax.axhspan(y0, UMBRAL, color=banda_clara, lw=0, zorder=0)
        ax.axhspan(UMBRAL, 0, color=banda_pequena, lw=0, zorder=0)
        ax.axhspan(0, y1, color=banda_roja, lw=0, zorder=0)
        ax.axhline(0, color=APAGADO, lw=0.9, zorder=2)
        # las bandas se explican en una leyenda fuera de los ejes: con datos que aun no existen, un rotulo dentro
        # puede caer sobre cualquier punto
        x0, x1 = 800, 4300
        for control in CONTROLES:
            s = puntos[control]
            if not s:
                continue
            color, forma, tam = COLOR[control], FORMA[control], TAM[control]
            ax.plot([p[0] for p in s], [p[1] for p in s], color=color, lw=1.3, ls=LINEA[control], zorder=3)
            for x, y, ic, ver in s:
                ax.plot([x, x], list(ic), color=color, lw=1.0, zorder=4, solid_capstyle="butt")
                ax.plot(x, y, forma, ms=tam + 2.4, mfc=banda(y), mec=banda(y), mew=0, zorder=4.6)
                if ver.startswith("PENDIENTE"):
                    ax.scatter([x], [y], s=(tam + 0.6) ** 2, marker=forma, facecolors=banda(y), edgecolors=color,
                               linewidths=1.5, linestyle=(0, (1.3, 1.1)), zorder=5)
                elif ver.startswith("EMPATA"):
                    ax.plot(x, y, forma, ms=tam, mfc=FONDO, mec=color, mew=1.4, zorder=5)
                elif ver.startswith("MEJORA"):
                    ax.plot(x, y, forma, ms=tam + 1.2, fillstyle="bottom", mfc=color, markerfacecoloralt=FONDO,
                            mec=color, mew=0.6, zorder=5)
                else:
                    ax.plot(x, y, forma, ms=tam, mfc=color, mec=color, mew=1.0, zorder=5)
        niveles = [veh for _, _, veh, _ in NIVELES]
        ax.set_xlim(x0, x1)
        ax.xaxis.set_major_locator(FixedLocator(niveles))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xticklabels([n.replace(" (", "\n(") for _, n, _, _ in NIVELES], fontsize=7.6)
        ax.set_ylim(y0, y1)
        paso = 5 if y1 - y0 <= 60 else 10
        marcas = list(range(paso * math.ceil(y0 / paso), int(y1) + 1, paso))
        ax.set_yticks(marcas)
        ax.set_yticklabels([f"{t:+d}".replace("-", MENOS) if t else "0" for t in marcas], fontsize=7.8)
        ax.grid(axis="both", color=FONDO, lw=0.8, zorder=1)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        ax.set_xlabel("Demanda total del corredor (veh/h, escala logarítmica)", fontsize=8.2)
        ax.set_ylabel("Cambio del retraso total frente al\nfijo ajustado desde 10 s (%)\n"
                      "negativo = menos retraso = mejora", fontsize=8.2, linespacing=1.4)
        if prueba:
            ax.text(0.5, 0.5, "PRUEBA: las variantes que faltan\nson la versión actual", transform=ax.transAxes,
                    ha="center", va="center", fontsize=13, color=ROJO, alpha=0.35, zorder=7, fontweight="bold")
        comun = dict(fontsize=7.3, title_fontsize=7.5, handletextpad=0.5, alignment="left", labelcolor=TINTA)
        por_control = [Line2D([], [], marker=FORMA[c], mfc=COLOR[c], mec=COLOR[c], color=COLOR[c], lw=1.3,
                              ls=LINEA[c], ms=TAM[c], label=NOMBRE[c][0].upper() + NOMBRE[c][1:]) for c in CONTROLES]
        punto = dict(ls="", ms=6.6)
        por_veredicto = [
            Line2D([], [], marker="o", mfc=TINTA2, mec=TINTA2, label="FUNCIONA o FALLA, según la banda", **punto),
            Line2D([], [], marker="o", fillstyle="bottom", mfc=TINTA2, markerfacecoloralt=FONDO, mec=TINTA2,
                   mew=0.6, label="MEJORA", **dict(punto, ms=7.8)),
            Line2D([], [], marker="o", mfc=FONDO, mec=TINTA2, mew=1.4, label="EMPATA", **punto),
            ax.scatter([], [], s=7.2 ** 2, marker="o", facecolors=FONDO, edgecolors=TINTA2, linewidths=1.5,
                       linestyle=(0, (1.3, 1.1)), label="PENDIENTE (no se estabilizó)"),
            Line2D([], [], marker="|", ms=10, mew=1.0, color=TINTA2, ls="", label="IC95 %")]
        por_banda = [
            Patch(facecolor=banda_roja, edgecolor="#e1e0d9", lw=0.6,
                  label="Más retraso que el fijo:\nFALLA si es significativo"),
            Patch(facecolor=banda_pequena, edgecolor="#e1e0d9", lw=0.6,
                  label=f"Entre {MENOS}5 y 0 %:\nMEJORA si es significativa"),
            Patch(facecolor=banda_clara, edgecolor="#e1e0d9", lw=0.6,
                  label=f"{MENOS}5 % o menos: FUNCIONA si\nes significativa y no pierde\ncontra el actuado")]
        ley1 = ax.legend(handles=por_veredicto, loc="upper left", bbox_to_anchor=(1.01, 1.0),
                         title="Veredicto: relleno", handlelength=1.4, labelspacing=0.4, frameon=False,
                         borderaxespad=0.0, **comun)
        ax.add_artist(ley1)
        ley2 = ax.legend(handles=por_banda, loc="upper left", bbox_to_anchor=(1.01, 0.5),
                         title="Banda: rango del cambio", handlelength=1.4, handleheight=1.6, labelspacing=0.6,
                         frameon=False, borderaxespad=0.0, **comun)
        ax.add_artist(ley2)
        ley3 = ax.legend(handles=por_control, ncol=min(5, len(por_control)), loc="lower left", bbox_to_anchor=(-0.01, 1.0),
                         title="IPPO con mensajes: color y forma", handlelength=2.4, columnspacing=1.4,
                         frameon=False, borderaxespad=0.2, **comun)
        leyendas = [ley1, ley2, ley3]
        for ley in leyendas:
            ley.get_title().set_color(TINTA2)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=FONDO, bbox_extra_artists=leyendas)
        pdf = os.path.splitext(ruta)[0] + ".pdf"
        fig.savefig(pdf, bbox_inches="tight", facecolor=FONDO, bbox_extra_artists=leyendas,
                    metadata={"CreationDate": None})
        plt.close(fig)
    print("Escrito", ruta)
    print("Escrito", pdf)


# ---------------- Principal ----------------

def escribir(ruta, texto):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)
    print("Escrito", ruta)


def main():
    ap = argparse.ArgumentParser(description="Responde el prerregistro del diagnostico del corredor.")
    ap.add_argument("--prueba", action="store_true",
                    help="con los datos que haya; las variantes que faltan son la version actual; salidas en "
                         "diag_corredor/prueba/")
    args = ap.parse_args()
    filas, R, medias, versiones, faltan = calcular(args.prueba)
    if faltan and not args.prueba:
        print(f"Faltan o no sirven {len(faltan)} archivos (la cola no termino o algun trabajo fallo); "
              "no se escribe nada:")
        for f in faltan:
            print("  ", f)
        return 1
    sustituidos = sorted({f"{f['nivel']} {NOMBRE[f['control']]} ({f['semillas']})" for f in filas
                          if f["fuente"].startswith("sustituto")})
    comprob = comprobar_descomposicion(R, medias, versiones)
    texto, resumen = texto_pruebas(R, medias, versiones, args.prueba, sustituidos, comprob)
    tex = tabla_tex(R, args.prueba)
    tex_pruebas = tabla_pruebas_tex(R, args.prueba)
    if args.prueba:
        salida = os.path.join(DIR, "prueba")
        rutas = {"csv": os.path.join(salida, "resultados.csv"), "txt": os.path.join(salida, "pruebas.txt"),
                 "tex": os.path.join(salida, "diag_corredor.tex"), "tex_pruebas": os.path.join(salida, "diag_pruebas.tex"),
                 "fig": os.path.join(salida, "fig_diag_corredor.png")}
    else:
        tablas = os.path.join(RAIZ, "TESIS", "secciones", "tablas")
        rutas = {"csv": os.path.join(DIR, "resultados.csv"), "txt": os.path.join(DIR, "pruebas.txt"),
                 "tex": os.path.join(tablas, "diag_corredor.tex"), "tex_pruebas": os.path.join(tablas, "diag_pruebas.tex"),
                 "fig": os.path.join(RAIZ, "TESIS", "images", "fig_diag_corredor.png")}
    escribir_csv(rutas["csv"], filas)
    escribir(rutas["txt"], texto)
    escribir(rutas["tex"], tex)
    escribir(rutas["tex_pruebas"], tex_pruebas)
    figura(R, rutas["fig"], args.prueba)
    ancho = medir_tabla(tex)
    ancho_pruebas = medir_tabla(tex_pruebas)
    print()
    if args.prueba:
        print(f"MODO PRUEBA: {len(faltan)} archivos faltan; sustituidos: {len(sustituidos)} controles")
    for h, r in resumen.items():
        print(f"{h:9s} " + "; ".join(f"{v} en {NOMBRE_SEMILLAS[k]}" for k, v in r.items()))
    diferencias, ok, total = comprob
    print(f"Comprobacion con descomposicion.txt: {ok} de {total} cifras iguales")
    for d in diferencias:
        print("  DIFERENCIA:", d)
    for nombre, a in (("Ancho del tabular", ancho), ("Ancho del tabular de pruebas", ancho_pruebas)):
        print(f"{nombre}:", "sin LaTeX para medirlo" if a is None else
              f"{a:.1f} cm ({'cabe' if a <= 15 else 'NO cabe'} en 15 cm)")
    for a in avisos:
        print("  AVISO:", a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
