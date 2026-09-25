"""
veredicto.py - Veredicto por caso y modelo del plan de pruebas v2 (plan2/ESPEC.md, seccion 7).

Uso:
  python veredicto.py                           lee plan2/ y escribe las salidas
  python veredicto.py --plan2 DIR --tesis DIR   otras carpetas (por defecto, junto a este script)
  python veredicto.py --probar                  pruebas de las reglas con numeros inventados

Lee de plan2/:
  evaluacion_<esc>_resumen.csv      (consolidar.py) media, ic95, deltas vs fijo y vs actuado, p
  q_table_<tag>.meta.json           (tabular) y politica_<esc>_<var>_s<base>.json (IPPO, DQN, MAPPO):
                                    val_elegido, val_serie, episodios
  resultados_<tag>.csv              solo si el meta no trae val_serie o val_elegido
  <esc>.sumocfg, .net.xml, .rou.xml semaforos, carriles de la avenida y demanda (de demo_rl/ si faltan)
Escribe:
  plan2/veredicto.csv               una fila por (caso, modelo)
  plan2/veredicto.md                una tabla por modelo y la matriz caso x modelo
  TESIS/secciones/tablas/veredicto_matriz.tex, veredicto_<modelo>.tex, veredicto_bases.tex
    (la matriz .tex lleva los modelos en filas y los casos en columnas para caber en 15 cm;
    un modelo sin datos deja su veredicto_<modelo>.tex solo con un comentario)

Reglas (plan v2, sin cambios respecto de la ESPEC):
  - Base publicada de (modelo, celda) = la mediana de las tres bases por val_elegido del meta
    (empate de val: gana la base menor). Nunca se elige con las semillas de evaluacion.
  - Veredicto con el retraso (timeloss_prom) de la base publicada frente al fijo (df, IC, p) y
    frente al actuado (da, IC, p): FUNCIONA, MEJORA, FALLA, EMPATA (funcion veredicto).
  - PENDIENTE si faltan bases, evaluaciones o la base publicada no convergio; en el ultimo caso
    se escribe el veredicto provisional.
  - Convergencia sobre la serie val del ultimo tercio de las validaciones (ceil(n/3), minimo 3
    puntos): plateau = pendiente * (episodios / 3) / media del tercio * 100 y
    estabilidad = (media de las 3 ultimas - minimo de la media movil de 3) / ese minimo * 100;
    convergio si |plateau| <= 5 y estabilidad <= 5.
  - Delta recompensa: el de la recompensa propia del modelo (ret_retraso, ret_colas o ret_spill)
    frente a la del fijo, tal como lo da consolidar.py (positivo = mejor recompensa).
"""
import os
import re
import csv
import sys
import math
import json
import argparse
import tempfile
import xml.etree.ElementTree as ET

DIR = os.path.dirname(os.path.abspath(__file__))

CASOS = [("P1", "corredor"), ("P2", "corredor_alta"), ("P3", "red"), ("P4", "red_alta"),
         ("P5", "malla3")]
MODELOS = ["actuado", "ql", "sarsa", "ql_colas", "dqn", "ippo_local", "ippo_vecinos", "ippo_spill",
           "mappo"]
NOMBRE = {"actuado": "Actuado", "ql": "Q-learning", "sarsa": "SARSA",
          "ql_colas": "Q-learning (colas)", "dqn": "DQN", "ippo_local": "IPPO local",
          "ippo_vecinos": "IPPO vecinos", "ippo_spill": "IPPO spill", "mappo": "MAPPO"}
RECOMPENSA = {"ql": "ret_retraso", "sarsa": "ret_retraso", "ql_colas": "ret_colas",
              "dqn": "ret_retraso", "ippo_local": "ret_retraso", "ippo_vecinos": "ret_retraso",
              "ippo_spill": "ret_spill", "mappo": "ret_retraso"}
TABULARES = ("ql", "sarsa", "ql_colas")
BASES = [42, 2042, 4042]
METRICA = "timeloss_prom"
UMBRAL_DELTA = -5.0          # % de retraso frente al fijo para FUNCIONA
ALFA = 0.05
UMBRAL_CONVERGENCIA = 5.0    # % para plateau y estabilidad
CABECERA_TEX = "% Generado por veredicto.py a partir de plan2/. No editar a mano.\n"

COLUMNAS = ["caso", "escenario", "semaforos", "carriles", "demanda_veh_h", "modelo",
            "base_publicada", "bases", "retraso", "retraso_ic95",
            "delta_fijo", "ic_fijo", "p_fijo", "delta_act", "ic_act", "p_act",
            "recompensa", "delta_recompensa", "ic_recompensa", "p_recompensa",
            "convergio", "convergen", "plateau", "estabilidad", "veredicto", "rotonda"]


# ---------------- Reglas (funciones puras) ----------------

def pierde_con_actuado(ic_a, p_a):
    """True si el IC95 del delta frente al actuado queda entero por encima de 0 con p < 0.05."""
    return ic_a is not None and p_a is not None and ic_a[0] > 0 and p_a < ALFA


def veredicto(df, ic_f, p_f, ic_a=None, p_a=None):
    """Regla de la ESPEC, seccion 7. df en %, ic_f = (lo, hi), p_f; ic_a y p_a frente al actuado."""
    mejora_sig = ic_f[1] < 0 and p_f < ALFA
    if mejora_sig and df <= UMBRAL_DELTA and not pierde_con_actuado(ic_a, p_a):
        return "FUNCIONA"
    if mejora_sig:
        return "MEJORA"
    if ic_f[0] > 0 and p_f < ALFA:
        return "FALLA"
    return "EMPATA"


def pendiente_regresion(xs, ys):
    """Pendiente de la recta de minimos cuadrados de ys sobre xs."""
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def tercio_final(serie):
    """Ultimo tercio de las validaciones (redondeado hacia arriba, minimo 3 puntos)."""
    k = max(3, math.ceil(len(serie) / 3))
    return serie[-k:]


def convergencia(serie, episodios):
    """(convergio, plateau %, estabilidad %) de una serie [(ep, val), ...] ordenada por episodio."""
    if len(serie) < 3:
        return False, None, None
    tramo = tercio_final(serie)
    eps = [float(e) for e, _ in tramo]
    vals = [float(v) for _, v in tramo]
    media = sum(vals) / len(vals)
    plateau = pendiente_regresion(eps, vals) * (episodios / 3) / media * 100
    moviles = [sum(vals[i:i + 3]) / 3 for i in range(len(vals) - 2)]
    minimo = min(moviles)
    estabilidad = (sum(vals[-3:]) / 3 - minimo) / minimo * 100
    ok = abs(plateau) <= UMBRAL_CONVERGENCIA and estabilidad <= UMBRAL_CONVERGENCIA
    return ok, plateau, estabilidad


def base_mediana(vals_por_base):
    """Base publicada: la mediana por val_elegido de {base: val}. Exige las tres bases."""
    if len(vals_por_base) != len(BASES):
        return None
    orden = sorted(vals_por_base.items(), key=lambda bv: (bv[1], bv[0]))
    return orden[len(orden) // 2][0]


def texto_veredicto(provisional, motivo=None, convergio=True):
    """Veredicto final: PENDIENTE con motivo si falta algo, provisional si no convergio."""
    if motivo:
        return f"PENDIENTE ({motivo})"
    if not convergio:
        return f"PENDIENTE (no convergió; provisional: {provisional})"
    return provisional


def palabra(texto):
    """Solo la palabra del veredicto (para las matrices)."""
    if texto and texto.startswith("= vecinos"):
        return "= vecinos"
    return texto.split(" ")[0] if texto else "PENDIENTE"


# ---------------- Lectura ----------------

def flotante(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


def intervalo(fila, sufijo=""):
    """(lo, hi) del delta_ic95 de una fila: texto "[lo, hi]" o columnas _lo / _hi."""
    if not fila:
        return None
    lo = flotante(fila.get("delta_ic95_lo" + sufijo))
    hi = flotante(fila.get("delta_ic95_hi" + sufijo))
    if lo is not None and hi is not None:
        return (lo, hi)
    numeros = re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", fila.get("delta_ic95" + sufijo) or "")
    if len(numeros) != 2:
        return None
    return (float(numeros[0]), float(numeros[1]))


def leer_csv(ruta):
    if not os.path.exists(ruta):
        return []
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def leer_json(ruta):
    if not os.path.exists(ruta):
        return None
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def leer_resumen(plan2, esc):
    """{(brazo, metrica): fila} de evaluacion_<esc>_resumen.csv."""
    return {(f["brazo"], f["metrica"]): f
            for f in leer_csv(os.path.join(plan2, f"evaluacion_{esc}_resumen.csv"))}


def tag(esc, modelo, base):
    return f"{esc}_{modelo}_s{base}"


def ruta_meta(plan2, esc, modelo, base):
    if modelo in TABULARES:
        return os.path.join(plan2, f"q_table_{tag(esc, modelo, base)}.meta.json")
    var = modelo[len("ippo_"):] if modelo.startswith("ippo_") else modelo
    return os.path.join(plan2, f"politica_{esc}_{var}_s{base}.json")


def serie_de_csv(plan2, esc, modelo, base):
    """[(ep, val)] de las filas de validacion del CSV de entrenamiento."""
    serie = []
    for f in leer_csv(os.path.join(plan2, f"resultados_{tag(esc, modelo, base)}.csv")):
        v, ep = flotante(f.get("val")), flotante(f.get("episodio"))
        if v is not None and ep is not None:
            serie.append((int(ep), v))
    return sorted(serie)


def info_base(plan2, esc, modelo, base):
    """Datos de entrenamiento de una base, o None si su politica no esta publicada."""
    meta = leer_json(ruta_meta(plan2, esc, modelo, base))
    if meta is None:
        return None
    serie = [(int(x[0]), float(x[3])) for x in meta.get("val_serie") or []
             if len(x) >= 4 and flotante(x[3]) is not None]
    if not serie:
        serie = serie_de_csv(plan2, esc, modelo, base)
    serie.sort()
    val = flotante(meta.get("val_elegido"))
    ep = meta.get("ep_elegido")
    if val is None and serie:
        # menor val; en empate, el mas tardio (ESPEC seccion 3)
        ep, val = min(reversed(serie), key=lambda ev: ev[1])
    episodios = flotante(meta.get("episodios")) or (serie[-1][0] if serie else 0)
    conv, plateau, estab = convergencia(serie, episodios) if serie else (False, None, None)
    return {"base": base, "val": val, "ep": ep, "serie": serie, "episodios": episodios,
            "convergio": conv, "plateau": plateau, "estabilidad": estab}


# ---------------- Descripcion del escenario (calculada de los archivos) ----------------

def buscar(nombre, carpetas):
    for c in carpetas:
        ruta = os.path.join(c, nombre)
        if os.path.exists(ruta):
            return ruta
    return None


def archivos_escenario(esc, carpetas):
    """(ruta del .net.xml, [rutas de .rou.xml]) segun el .sumocfg; sin cfg, por nombre."""
    cfg = buscar(f"{esc}.sumocfg", carpetas)
    red, rutas = f"{esc}.net.xml", [f"{esc}.rou.xml"]
    if cfg:
        try:
            raiz = ET.parse(cfg).getroot()
            nodo = raiz.find(".//net-file")
            if nodo is not None:
                red = nodo.get("value", red).strip()
            nodo = raiz.find(".//route-files")
            if nodo is not None:
                rutas = [r.strip() for r in nodo.get("value", "").split(",") if r.strip()]
        except ET.ParseError:
            pass
    return buscar(red, carpetas), [r for r in (buscar(n, carpetas) for n in rutas) if r]


def demanda(rutas):
    """veh/h: suma de vehsPerHour * duracion / 3600 de los flows (y number/period si los hay)."""
    total = 0.0
    for ruta in rutas:
        for flow in ET.parse(ruta).getroot().iter("flow"):
            ini, fin = float(flow.get("begin", 0)), float(flow.get("end", 3600))
            dur = fin - ini
            if flow.get("vehsPerHour") or flow.get("perHour"):
                total += float(flow.get("vehsPerHour") or flow.get("perHour")) * dur / 3600
            elif flow.get("number"):
                total += float(flow.get("number"))
            elif flow.get("period"):
                total += dur / float(flow.get("period"))
    return total


def carriles_avenida(raiz):
    """Carriles de las aproximaciones este-oeste de los cruces semaforizados (la moda).

    La avenida es el eje este-oeste en todos los escenarios (ESPEC seccion 1): se toman las
    aristas que llegan a un cruce semaforizado con mas desplazamiento en x que en y.
    """
    nodos = {j.get("id"): j for j in raiz.iter("junction")}
    conteo = {}
    for e in raiz.iter("edge"):
        if e.get("function") or e.get("to") not in nodos or e.get("from") not in nodos:
            continue
        destino, origen = nodos[e.get("to")], nodos[e.get("from")]
        if not destino.get("type", "").startswith("traffic_light"):
            continue
        dx = float(destino.get("x")) - float(origen.get("x"))
        dy = float(destino.get("y")) - float(origen.get("y"))
        if abs(dx) < abs(dy):
            continue
        n = sum(1 for c in e.iter("lane") if c.get("allow") not in ("pedestrian", "bicycle"))
        conteo[n] = conteo.get(n, 0) + 1
    if not conteo:
        return None
    return max(conteo.items(), key=lambda nc: (nc[1], nc[0]))[0]


def describir(esc, plan2):
    """{semaforos, carriles, demanda, rotonda} del escenario; None en lo que no se pueda leer."""
    carpetas = [plan2, DIR]
    red, rutas = archivos_escenario(esc, carpetas)
    d = {"semaforos": None, "carriles": None, "demanda": None, "rotonda": None}
    if red:
        try:
            raiz = ET.parse(red).getroot()
            d["semaforos"] = len({t.get("id") for t in raiz.iter("tlLogic")})
            d["carriles"] = carriles_avenida(raiz)
            d["rotonda"] = any(True for _ in raiz.iter("roundabout"))
        except (ET.ParseError, TypeError, ValueError):
            pass
    if rutas:
        try:
            d["demanda"] = round(demanda(rutas))
        except (ET.ParseError, ValueError):
            pass
    return d


# ---------------- Calculo del veredicto ----------------

def fila_brazo(resumen, brazo):
    """Retraso y deltas de un brazo: dict con los numeros o None si el brazo no esta evaluado."""
    r = resumen.get((brazo, METRICA))
    if not r or flotante(r.get("media")) is None:
        return None
    return {"retraso": flotante(r.get("media")), "retraso_ic95": flotante(r.get("ic95")),
            "delta_fijo": flotante(r.get("delta_pct")), "ic_fijo": intervalo(r),
            "p_fijo": flotante(r.get("p_wilcoxon")),
            "delta_act": flotante(r.get("delta_pct_act")), "ic_act": intervalo(r, "_act"),
            "p_act": flotante(r.get("p_wilcoxon_act"))}


def delta_recompensa(resumen, brazo, modelo):
    r = resumen.get((brazo, RECOMPENSA.get(modelo, "")))
    if not r:
        return None, None, None
    return flotante(r.get("delta_pct")), intervalo(r), flotante(r.get("p_wilcoxon"))


def provisional(ev, con_actuado=True):
    """Veredicto numerico, o (None, motivo) si faltan comparaciones."""
    if ev["delta_fijo"] is None or ev["ic_fijo"] is None or ev["p_fijo"] is None:
        return None, "falta la comparación con el fijo"
    if con_actuado and (ev["delta_act"] is None or ev["ic_act"] is None or ev["p_act"] is None):
        return None, "falta la comparación con el actuado"
    return veredicto(ev["delta_fijo"], ev["ic_fijo"], ev["p_fijo"], ev["ic_act"], ev["p_act"]), None


def celda(plan2, caso, esc, modelo, resumen, desc):
    """Una fila de veredicto.csv (dict) mas las bases de la celda para la tabla de fragilidad."""
    fila = {c: None for c in COLUMNAS}
    fila.update({"caso": caso, "escenario": esc, "modelo": modelo,
                 "semaforos": desc["semaforos"], "carriles": desc["carriles"],
                 "demanda_veh_h": desc["demanda"],
                 "rotonda": "" if desc["rotonda"] is None else ("si" if desc["rotonda"] else "no")})
    bases = []
    if modelo == "actuado":
        ev = fila_brazo(resumen, "actuado")
        if ev is None:
            fila["veredicto"] = texto_veredicto(None, "sin evaluación")
            return fila, bases, False
        fila.update(ev)
        prov, motivo = provisional(ev, con_actuado=False)
        fila["delta_act"] = fila["ic_act"] = fila["p_act"] = None
        fila["veredicto"] = texto_veredicto(prov, motivo)
        return fila, bases, True

    fila["recompensa"] = RECOMPENSA[modelo]
    infos = {}
    for b in BASES:
        info = info_base(plan2, esc, modelo, b)
        ev = fila_brazo(resumen, f"{modelo}_s{b}")
        if info is not None:
            infos[b] = info
        if info is not None or ev is not None:
            bases.append({"base": b, "info": info, "eval": ev})
    hay_datos = bool(bases)
    fila["bases"] = f"{len(infos)}/{len(BASES)}"
    con_val = {b: i["val"] for b, i in infos.items() if i["val"] is not None}
    publicada = base_mediana(con_val)
    convergen = sum(1 for i in infos.values() if i["convergio"])
    fila["convergen"] = f"{convergen}/{len(BASES)}"
    if publicada is None:
        motivo = (f"bases entrenadas {len(infos)}/{len(BASES)}" if len(infos) < len(BASES)
                  else "falta val_elegido en alguna base")
        fila["veredicto"] = texto_veredicto(None, "sin datos" if not hay_datos else motivo)
        return fila, bases, hay_datos
    for x in bases:
        x["publicada"] = x["base"] == publicada
    info = infos[publicada]
    fila.update({"base_publicada": publicada, "convergio": "si" if info["convergio"] else "no",
                 "plateau": info["plateau"], "estabilidad": info["estabilidad"]})
    brazo = f"{modelo}_s{publicada}"
    ev = fila_brazo(resumen, brazo)
    if ev is None:
        fila["veredicto"] = texto_veredicto(None, f"falta evaluar la base {publicada}")
        return fila, bases, hay_datos
    fila.update(ev)
    dr, icr, pr = delta_recompensa(resumen, brazo, modelo)
    fila.update({"delta_recompensa": dr, "ic_recompensa": icr, "p_recompensa": pr})
    prov, motivo = provisional(ev)
    if not motivo and not info["serie"]:
        motivo = "sin serie de validación"
    fila["veredicto"] = texto_veredicto(prov, motivo, info["convergio"])
    return fila, bases, hay_datos


def spill_inactivo(plan2, esc):
    """True si en ningun episodio de entrenamiento de las tres bases de ippo_vecinos la cola
    maxima de un carril de enlace paso de la mitad de sus plazas. Entonces el termino de spill
    no se habria activado nunca, y con la misma semilla base la politica de ippo_spill es la de
    vecinos bit a bit (24.09.2026: red, red_alta y malla3; en corredor y corredor_alta si se activa)."""
    umbral, maximo = None, None
    for b in BASES:
        meta = leer_json(os.path.join(plan2, f"politica_{esc}_vecinos_s{b}.json"))
        filas = leer_csv(os.path.join(plan2, f"resultados_{esc}_ippo_vecinos_s{b}.csv"))
        plazas = (meta or {}).get("plazas") or {}
        if not filas or not plazas:
            return False
        u = min(int(v) // 2 for v in plazas.values())
        umbral = u if umbral is None else min(umbral, u)
        for f in filas:
            v = flotante(f.get("cola_max_enlace"))
            if v is not None:
                maximo = v if maximo is None else max(maximo, v)
    return maximo is not None and maximo <= umbral


def calcular(plan2):
    """Filas del veredicto, bases por (modelo, caso) y modelos con algun dato."""
    filas, bases, con_datos = [], {}, set()
    for caso, esc in CASOS:
        resumen = leer_resumen(plan2, esc)
        desc = describir(esc, plan2)
        por_modelo = {}
        for modelo in MODELOS:
            fila, bs, hay = celda(plan2, caso, esc, modelo, resumen, desc)
            filas.append(fila)
            por_modelo[modelo] = fila
            bases[(modelo, caso)] = bs
            if hay:
                con_datos.add(modelo)
        fs, fv = por_modelo.get("ippo_spill"), por_modelo.get("ippo_vecinos")
        # Tambien si hay corridas de spill parciales o sin evaluar: el 25.09 las que alcanzaron a
        # correr en red y red_alta (2 completas y 4 parciales) salieron identicas a vecinos
        # episodio a episodio, con cero activaciones del termino.
        if (fs and fv and (fs.get("veredicto") or "").startswith("PENDIENTE")
                and spill_inactivo(plan2, esc)):
            for c in COLUMNAS:
                if c not in ("modelo", "recompensa"):
                    fs[c] = fv[c]
            fs["veredicto"] = f"= vecinos (término de spill inactivo; {palabra(fv['veredicto'])})"
            con_datos.add("ippo_spill")
    return filas, bases, [m for m in MODELOS if m in con_datos]


# ---------------- Formato ----------------

def txt(x, dec=2):
    v = flotante(x)
    return "" if v is None else f"{v:.{dec}f}"


def txt_ic(ic):
    return "" if not ic else f"[{ic[0]:.1f}, {ic[1]:.1f}]"


def txt_p(p):
    return "" if p is None else f"{p:.3g}"


def escribir_csv(ruta, filas):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        for fila in filas:
            salida = dict(fila)
            for c in ("retraso", "retraso_ic95"):
                salida[c] = txt(fila[c], 3)
            for c in ("delta_fijo", "delta_act", "delta_recompensa", "plateau", "estabilidad"):
                salida[c] = txt(fila[c], 1)
            for c in ("ic_fijo", "ic_act", "ic_recompensa"):
                salida[c] = txt_ic(fila[c])
            for c in ("p_fijo", "p_act", "p_recompensa"):
                salida[c] = txt_p(fila[c])
            for c in COLUMNAS:
                if salida[c] is None:
                    salida[c] = ""
            w.writerow(salida)
    print("Escrito", ruta)


def md_delta(d, ic, p):
    if d is None:
        return "-"
    return f"{d:+.1f} % {txt_ic(ic)} p={txt_p(p)}"


def texto_md(filas, modelos):
    por = {(f["modelo"], f["caso"]): f for f in filas}
    lineas = ["# Veredicto del plan de pruebas v2", "",
              "Generado por veredicto.py a partir de plan2/. No editar a mano. Regla: ESPEC seccion 7.",
              "Delta de retraso en % (negativo = mejor); delta de recompensa en % (positivo = mejor).", ""]
    lineas += ["## Matriz caso x modelo", "",
               "| Caso | Escenario | " + " | ".join(NOMBRE[m] for m in MODELOS) + " |",
               "|---|---|" + "---|" * len(MODELOS)]
    for caso, esc in CASOS:
        lineas.append(f"| {caso} | {esc} | "
                      + " | ".join(palabra(por[(m, caso)]["veredicto"]) for m in MODELOS) + " |")
    for m in modelos:
        lineas += ["", f"## {NOMBRE[m]} ({m})", "",
                   "| Caso | Escenario | Sem. | Carriles | Demanda (veh/h) | Base | Retraso (s/veh) | "
                   "Delta vs fijo | Delta vs actuado | Delta recompensa | Convergio | Veredicto |",
                   "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for caso, _ in CASOS:
            f = por[(m, caso)]
            ret = f"{txt(f['retraso'])} +- {txt(f['retraso_ic95'])}" if f["retraso"] is not None else "-"
            conv = f"{f['convergio']} ({f['convergen']})" if f["convergio"] else "-"
            sem = "" if f["semaforos"] is None else str(f["semaforos"])
            if f["rotonda"] == "si":
                sem += " + rotonda"
            lineas.append(" | ".join([
                f"| {caso}", f["escenario"], sem or "?", str(f["carriles"] or "?"),
                str(f["demanda_veh_h"] or "?"), str(f["base_publicada"] or "-"), ret,
                md_delta(f["delta_fijo"], f["ic_fijo"], f["p_fijo"]),
                md_delta(f["delta_act"], f["ic_act"], f["p_act"]),
                md_delta(f["delta_recompensa"], f["ic_recompensa"], f["p_recompensa"]),
                conv, f["veredicto"]]) + " |")
    return "\n".join(lineas) + "\n"


def tex_esc(texto):
    """Escapa el guion bajo y el porcentaje para texto que se tipografia."""
    return str(texto).replace("_", r"\_").replace("%", r"\%")


def tex_num(x, dec=2):
    v = flotante(x)
    return "--" if v is None else f"{v:.{dec}f}".replace("-", "$-$")


def tex_ic(ic):
    if not ic:
        return ""
    return f"[{ic[0]:.1f},\\,{ic[1]:.1f}]".replace("-", "$-$")


def tex_delta(d, ic, p):
    """Cambio, intervalo y p apilados en una celda (como tablas_tex.celda_delta_apilada)."""
    if d is None:
        return "--"
    return (r"\makecell[r]{" + f"{d:+.1f}".replace("-", "$-$") + r"\,\%" + r"\\{}" + tex_ic(ic)
            + r"\\$p$ " + tex_p(p) + "}")


def tex_p(p):
    """p para las tablas: con n = 30 Wilcoxon da valores muy chicos; debajo de 0.001 basta el tope."""
    if p is None:
        return "--"
    return "$<$\\,0.001" if p < 0.001 else f"= {p:.3g}"


def apilar(lineas, alinear="c"):
    """Varias lineas en una celda (makecell); el {} evita que un [ se lea como argumento."""
    return r"\makecell[" + alinear + "]{" + r"\\{}".join(lineas) + "}"


def partir(texto, ancho=14):
    """Parte un texto en lineas de a lo mas `ancho` caracteres, sin cortar palabras."""
    lineas = [""]
    for trozo in texto.split(" "):
        if lineas[-1] and len(lineas[-1]) + 1 + len(trozo) > ancho:
            lineas.append(trozo)
        else:
            lineas[-1] = (lineas[-1] + " " + trozo).strip()
    return lineas


def tex_veredicto(texto):
    """Veredicto con el motivo del PENDIENTE (o de "= vecinos") partido en lineas cortas."""
    if texto.startswith("= vecinos ("):
        return apilar(["= vecinos"] + [tex_esc(x) for x in partir(texto[len("= vecinos "):])], "l")
    if not texto.startswith("PENDIENTE ("):
        return texto
    return apilar(["PENDIENTE"] + [tex_esc(x) for x in partir(texto[len("PENDIENTE "):])], "l")


def abrir_tabla(sep="3pt"):
    return (r"\begin{table}[H]" "\n" r"\setstretch{1}" "\n" r"\centering" "\n" r"\scriptsize" "\n"
            r"\setlength{\tabcolsep}{" + sep + "}\n")


def cerrar_tabla(corto, largo, etiqueta):
    return (r"\bottomrule" "\n" r"\end{tabular}" "\n" f"\\caption[{corto}]{{{largo}}}\n"
            f"\\label{{{etiqueta}}}\n" r"\end{table}" "\n")


def celda_semaforos(f):
    sem = "?" if f["semaforos"] is None else str(f["semaforos"])
    return apilar([sem, "+ rot."]) if f["rotonda"] == "si" else sem


def tex_matriz(filas):
    por = {(f["modelo"], f["caso"]): f for f in filas}
    cab = " & ".join(r"\makecell{" + caso + r"\\" + tex_esc(esc) + "}" for caso, esc in CASOS)
    lineas = [" & ".join([NOMBRE[m]] + [palabra(por[(m, caso)]["veredicto"]) for caso, _ in CASOS])
              + r" \\" for m in MODELOS]
    largo = ("Veredicto de cada modelo en cada caso del plan de pruebas (regla de la sección de "
             "métodos): retraso de la política publicada frente al fijo tuneado y al actuado, "
             "semillas de evaluación 1001 a 1030. PENDIENTE: faltan datos o la política no convergió. "
             "El actuado se juzga frente al fijo.")
    return (abrir_tabla() + r"\begin{tabular}{l" + "c" * len(CASOS) + "}\n" r"\toprule" "\n"
            + "Modelo & " + cab + r" \\" "\n" r"\midrule" "\n" + "\n".join(lineas) + "\n"
            + cerrar_tabla("Veredicto por caso y modelo", largo, "tab:veredicto-matriz"))


def tex_modelo(filas, modelo):
    lineas = []
    for f in (x for x in filas if x["modelo"] == modelo):
        ret = ("--" if f["retraso"] is None
               else apilar([tex_num(f["retraso"]), f"$\\pm$ {tex_num(f['retraso_ic95'])}"], "r"))
        conv = "--" if not f["convergio"] else \
            apilar(["sí" if f["convergio"] == "si" else "no", f"({f['convergen']})"])
        lineas.append(" & ".join([
            f["caso"], tex_esc(f["escenario"]), celda_semaforos(f),
            "?" if f["carriles"] is None else str(f["carriles"]),
            "?" if f["demanda_veh_h"] is None else str(f["demanda_veh_h"]), ret,
            tex_delta(f["delta_fijo"], f["ic_fijo"], f["p_fijo"]),
            tex_delta(f["delta_act"], f["ic_act"], f["p_act"]),
            tex_delta(f["delta_recompensa"], f["ic_recompensa"], f["p_recompensa"]),
            conv, tex_veredicto(f["veredicto"])]) + r" \\")
    cab = "\n".join([
        r"\begin{tabular}{llcrrrrrrcl}",
        r"\toprule",
        r"Caso & Escenario & Sem. & Carr. & \makecell{Dem.\\(veh/h)} & \makecell{Retraso\\(s/veh)} & "
        r"\makecell{$\Delta$\\retraso\\vs fijo} & \makecell{$\Delta$\\retraso\\vs actuado} & "
        r"\makecell{$\Delta$\\recompensa} & Conv. & Veredicto \\",
        r"\midrule"]) + "\n"
    if modelo == "actuado":
        detalle = "Controlador actuado de SUMO, fila de referencia juzgada frente al fijo tuneado."
    else:
        detalle = (f"Política publicada = mediana de las tres semillas base por la validación "
                   f"(semillas 999 y 1999). $\\Delta$ recompensa: cambio de la recompensa propia del "
                   f"modelo ({tex_esc(RECOMPENSA[modelo])}) frente a la del fijo, positivo = mejor. "
                   f"Conv.: si convergió la política publicada; entre paréntesis, cuántas de las "
                   f"tres bases convergen.")
    largo = (f"{NOMBRE[modelo]}: veredicto por caso. Sem.: semáforos (rot.: más una rotonda); Carr.: "
             f"carriles por sentido de la avenida; Dem.: demanda total. Retraso: media $\\pm$ "
             f"IC95\\,\\% sobre las semillas de evaluación 1001 a 1030; $\\Delta$ con IC95\\,\\% "
             f"bootstrap pareado y $p$ de Wilcoxon pareado. {detalle}")
    etiqueta = "tab:veredicto-" + modelo.replace("_", "-")
    return (abrir_tabla("1.5pt") + cab + "\n".join(lineas) + "\n"
            + cerrar_tabla(f"Veredicto de {NOMBRE[modelo]}", largo, etiqueta))


def tex_bases(bases, modelos):
    """Una tabla por modelo con todas sus bases en cada caso (fragilidad del entrenamiento)."""
    texto = ""
    for m in modelos:
        if m == "actuado":
            continue
        lineas = []
        for caso, esc in CASOS:
            retrasos = []
            for x in bases.get((m, caso), []):
                info, ev = x["info"], x["eval"]
                semilla = str(x["base"])
                if x.get("publicada"):
                    semilla = apilar([semilla, "(publicada)"], "l")
                val = "--" if not info or info["val"] is None else tex_num(info["val"])
                if info and info["ep"] is not None:
                    val = apilar([val, f"(ep {info['ep']})"], "r")
                conv = "--" if not info or not info["serie"] else ("sí" if info["convergio"] else "no")
                if ev:
                    retrasos.append(ev["retraso"])
                ret = "--" if not ev else \
                    apilar([tex_num(ev["retraso"]), f"$\\pm$ {tex_num(ev['retraso_ic95'])}"], "r")
                delta = "--" if not ev or ev["delta_fijo"] is None else apilar(
                    [f"{ev['delta_fijo']:+.1f}".replace("-", "$-$") + r"\,\%", tex_ic(ev["ic_fijo"])], "r")
                p = "--" if not ev or ev["p_fijo"] is None else tex_p(ev["p_fijo"]).lstrip("= ")
                lineas.append(" & ".join([caso, tex_esc(esc), semilla, val, conv, ret, delta, p]) + r" \\")
            if len(retrasos) > 1:
                lineas.append(" & & " + apilar(["rango entre", "bases"], "l") + " & & & "
                              + tex_num(max(retrasos) - min(retrasos)) + r" & & \\")
        if not lineas:
            continue
        cab = "\n".join([
            r"\begin{tabular}{lllrlrrr}",
            r"\toprule",
            r"Caso & Escenario & \makecell{Semilla\\base} & \makecell{Validación\\elegida\\(s/veh)} & "
            r"\makecell{Conver-\\gió} & \makecell{Retraso\\evaluación\\(s/veh)} & "
            r"\makecell{$\Delta$ vs fijo\\{}[IC95\,\%]} & $p$ \\",
            r"\midrule"]) + "\n"
        largo = (f"{NOMBRE[m]}: las tres políticas entrenadas (semillas base) de cada caso. La "
                 f"validación elegida es la media de las semillas 999 y 1999 del checkpoint "
                 f"publicado; el retraso y el $\\Delta$ frente al fijo, sobre las semillas 1001 a 1030. "
                 f"La base publicada es la mediana por validación. El rango entre bases se compara "
                 f"con el IC95\\,\\% de una sola política.")
        texto += (abrir_tabla() + cab + "\n".join(lineas) + "\n"
                  + cerrar_tabla(f"Bases de {NOMBRE[m]}", largo,
                                 "tab:veredicto-bases-" + m.replace("_", "-")) + "\n")
    return texto or "% Sin bases entrenadas todavia.\n"


def escribir(ruta, texto, cabecera=""):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(cabecera + texto)
    print("Escrito", ruta)


def generar(plan2, tesis):
    filas, bases, modelos = calcular(plan2)
    escribir_csv(os.path.join(plan2, "veredicto.csv"), filas)
    escribir(os.path.join(plan2, "veredicto.md"), texto_md(filas, modelos))
    tablas = os.path.join(tesis, "secciones", "tablas")
    escribir(os.path.join(tablas, "veredicto_matriz.tex"), tex_matriz(filas), CABECERA_TEX)
    for m in MODELOS:
        # sin datos se escribe un archivo vacio para que un \input del capitulo no rompa la compilacion
        texto = tex_modelo(filas, m) if m in modelos else "% Sin datos todavia.\n"
        escribir(os.path.join(tablas, f"veredicto_{m}.tex"), texto, CABECERA_TEX)
    escribir(os.path.join(tablas, "veredicto_bases.tex"), tex_bases(bases, modelos), CABECERA_TEX)
    for f in filas:
        if f["modelo"] in modelos:
            print(f"  {f['caso']} {f['modelo']:<13} {f['veredicto']}")


# ---------------- Pruebas (--probar) ----------------

def probar():
    # veredicto: cada rama
    assert veredicto(-10, (-12, -8), 0.001, (-3, -1), 0.01) == "FUNCIONA"
    assert veredicto(-5, (-6, -4), 0.01, (1, 3), 0.2) == "FUNCIONA"          # pierde n.s. con actuado
    assert veredicto(-5, (-6, -4), 0.01) == "FUNCIONA"                       # actuado: sin comparacion
    assert veredicto(-3, (-4, -2), 0.01, (-1, 1), 0.5) == "MEJORA"           # delta > -5 %
    assert veredicto(-10, (-12, -8), 0.001, (2, 4), 0.01) == "MEJORA"        # pierde con el actuado
    assert veredicto(-10, (-12, -8), 0.001, (2, 4), 0.06) == "FUNCIONA"      # pierde, pero p >= 0.05
    assert veredicto(-10, (-12, -8), 0.001, (0, 4), 0.01) == "FUNCIONA"      # IC toca 0: no entero > 0
    assert veredicto(-10, (-12, -8), 0.06) == "EMPATA"                       # IC < 0 pero p >= 0.05
    assert veredicto(-2, (-4, 0), 0.01) == "EMPATA"                          # IC toca 0
    assert veredicto(8, (5, 11), 0.002) == "FALLA"
    assert veredicto(8, (5, 11), 0.2) == "EMPATA"                            # peor pero p >= 0.05
    assert veredicto(1, (-1, 3), 0.4) == "EMPATA"
    assert pierde_con_actuado((0.5, 2), 0.04) and not pierde_con_actuado(None, None)
    # texto final y PENDIENTE
    assert texto_veredicto("MEJORA") == "MEJORA"
    assert texto_veredicto("MEJORA", convergio=False) == "PENDIENTE (no convergió; provisional: MEJORA)"
    assert texto_veredicto(None, "bases entrenadas 2/3") == "PENDIENTE (bases entrenadas 2/3)"
    assert palabra("PENDIENTE (no convergió; provisional: MEJORA)") == "PENDIENTE"
    # convergencia: 20 validaciones (ep 10..200), ultimo tercio = 7 puntos
    eps = list(range(10, 201, 10))
    plana = [(e, 30 - 10 * math.exp(-e / 20) + (0.1 if e % 20 else -0.1)) for e in eps]
    ok, pl, es = convergencia(plana, 200)
    assert ok and abs(pl) <= 5 and es <= 5, (pl, es)
    assert tercio_final(plana) == plana[-7:]
    bajando = [(e, 60 - 0.15 * e) for e in eps]       # sigue bajando: plateau ~ -26 %
    ok, pl, es = convergencia(bajando, 200)
    assert not ok and pl < -5, pl
    salto = [(e, 30.0) for e in eps[:-3]] + [(e, 33.0) for e in eps[-3:]]   # empeora al final
    ok, pl, es = convergencia(salto, 200)
    assert not ok and abs(es - 10) < 1e-9, es
    ok, pl, es = convergencia([(10, 30.0), (20, 29.0)], 200)
    assert not ok and pl is None
    assert abs(pendiente_regresion([0, 1, 2], [1, 3, 5]) - 2) < 1e-12
    # base publicada: mediana por val_elegido, empate por base
    assert base_mediana({42: 21.0, 2042: 19.0, 4042: 20.0}) == 4042
    assert base_mediana({42: 20.0, 2042: 20.0, 4042: 25.0}) == 2042
    assert base_mediana({42: 21.0, 2042: 19.0}) is None
    # intervalos del resumen
    assert intervalo({"delta_ic95": "[-2.6, -0.6]"}) == (-2.6, -0.6)
    assert intervalo({"delta_ic95_act": "[1e-1, 2]"}, "_act") == (0.1, 2.0)
    assert intervalo({"delta_ic95_lo": "-1", "delta_ic95_hi": "2"}) == (-1.0, 2.0)
    assert intervalo({"delta_ic95": ""}) is None
    # formato de las tablas
    assert tex_p(1.9e-9) == "$<$\\,0.001" and tex_p(0.0421) == "= 0.0421" and tex_p(None) == "--"
    assert partir("(no convergió; provisional: MEJORA)") == ["(no convergió;", "provisional:", "MEJORA)"]
    assert tex_esc("corredor_alta 5%") == "corredor\\_alta 5\\%"
    # demanda: 600 veh/h durante media hora + number 100 + period 36 s en una hora
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "x.rou.xml")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write('<routes><flow id="a" begin="0" end="1800" vehsPerHour="600"/>'
                    '<flow id="b" begin="0" end="3600" number="100"/>'
                    '<flow id="c" begin="0" end="3600" period="36"/></routes>')
        assert abs(demanda([ruta]) - 500) < 1e-9
    # celda completa con numeros inventados: la regla, la base mediana y la convergencia juntas
    with tempfile.TemporaryDirectory() as tmp:
        for b, v in ((42, 22.0), (2042, 20.0), (4042, 21.0)):
            serie = [[e, v, v, v] for e in eps]
            with open(ruta_meta(tmp, "red", "ql", b), "w", encoding="utf-8") as f:
                json.dump({"val_elegido": v, "ep_elegido": 200, "episodios": 200, "val_serie": serie}, f)
        resumen = {("ql_s4042", METRICA): {"media": "20.5", "ic95": "0.2", "delta_pct": "-8.0",
                                           "delta_ic95": "[-9.0, -7.0]", "p_wilcoxon": "0.001",
                                           "delta_pct_act": "-1.0", "delta_ic95_act": "[-2.0, 0.5]",
                                           "p_wilcoxon_act": "0.3"},
                   ("ql_s4042", "ret_retraso"): {"delta_pct": "4.0", "delta_ic95": "[3, 5]",
                                                 "p_wilcoxon": "0.002"}}
        desc = {"semaforos": 3, "carriles": 2, "demanda": 3000, "rotonda": True}
        fila, bases, hay = celda(tmp, "P3", "red", "ql", resumen, desc)
        assert hay and fila["base_publicada"] == 4042 and fila["veredicto"] == "FUNCIONA", fila
        assert fila["convergen"] == "3/3" and fila["delta_recompensa"] == 4.0
        fila, _, hay = celda(tmp, "P3", "red", "sarsa", resumen, desc)
        assert not hay and fila["veredicto"] == "PENDIENTE (sin datos)"
        os.remove(ruta_meta(tmp, "red", "ql", 42))
        fila, _, _ = celda(tmp, "P3", "red", "ql", resumen, desc)
        assert fila["veredicto"] == "PENDIENTE (bases entrenadas 2/3)", fila["veredicto"]
        fila, _, _ = celda(tmp, "P3", "red", "actuado", {}, desc)
        assert fila["veredicto"] == "PENDIENTE (sin evaluación)"
    print("veredicto.py --probar: todas las pruebas pasan")


def main():
    ap = argparse.ArgumentParser(description="Veredicto del plan de pruebas v2 (ESPEC seccion 7).")
    ap.add_argument("--plan2", default=os.path.join(DIR, "plan2"))
    ap.add_argument("--tesis", default=os.path.join(DIR, "TESIS"))
    ap.add_argument("--probar", action="store_true", help="solo corre las pruebas de las reglas")
    args = ap.parse_args()
    if args.probar:
        probar()
        return
    generar(os.path.abspath(args.plan2), os.path.abspath(args.tesis))


if __name__ == "__main__":
    sys.exit(main())
