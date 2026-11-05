"""
prueba_franja.py - Pruebas de la tarea 0.8 (franja.py, modos franja y bloques de rl_corredor y evaluar.py --brazo):
  1. franja con plan 2 = plan 1 (el fijo entregado) da el mismo tripinfo que el fijo de un plan, por sumo directo y
     por TraCI (P1, P3 y P6);
  2. a los 1800 s el programa cambia en su instante limpio y entra alineado: desde el cambio, el estado de cada
     semaforo es el del plan 2 corriendo solo desde 0 s;
  3. 0 cortes de verde sin ambar en toda la corrida (con dos pares que, cambiando todos a los 1800 s, si cortan:
     la prueba los ve);
  4. sumo directo = TraCI (evaluar.brazo_referencia(esc, "franja", archivo)) con dos planes distintos;
  5. bloques: 6 programas con WAUT en P1 y P6: cambios en sus instantes, 0 cortes y sumo directo = TraCI (modo bloques);
  6. pares sin instante estricto (antes abortaban): la regla relajada (P1 25/10 0/0 -> 15/20 0/15, y uno de la red) y
     el respaldo (P1 en contrafase: 10/10 0/0 -> 10/10 13/13): el WAUT cambia en el instante anotado, entra alineado,
     0 verdes cortados, 0 ambares tras un verde mas cortos que 3 s; el registro dice regla y retraso por semaforo;
  7. sin sumo: en 3000 pares al azar de P1, P3 y P6 (verdes de 10 a 60 s, desfases cualesquiera), el instante de la
     regla estricta es el mismo que el del codigo de antes en todos los pares en que el de antes lo encontraba, y donde
     no lo encontraba (abortaba) ahora hay relajada, respaldo o forzado; en ninguno el cambio corta un verde ni deja un
     ambar corto tras un verde (problemas_del_cambio), y forzado no aparece.
Semillas de humo (424301-424302). Uso (cwd = plan3/): python pruebas/ref/prueba_franja.py
Salida: pruebas/ref/salidas/prueba_franja.txt
"""
import os
import sys
import math
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
import traci  # noqa: E402
import barrer_fino as bfn  # noqa: E402
import franja  # noqa: E402
import evaluar  # noqa: E402

TMP = os.path.join(up.TMP, "franja")
os.makedirs(TMP, exist_ok=True)
inf = up.Informe("prueba_franja")


def plan_plantilla(c):
    """El fijo entregado (la plantilla <esc>.add.xml) como plan."""
    i = 0
    fases = [f for f in c.p.tls[i] if f.tag == "phase"]
    verdes = [k for k, f in enumerate(fases) if franja.bf.es_verde(f.get("state"))]
    av = int(fases[c.p.fases_av[i]].get("duration"))
    tr = int(next(fases[k].get("duration") for k in verdes if k != c.p.fases_av[i]))
    offsets = [int(tl.get("offset")) for tl in c.p.tls]
    esquema = "cero" if c.malla and not any(offsets) else ""
    return c.plan(av, tr, offsets, esquema)


def escribir(c, nombre, secuencia, prefijo="franja", wid="franja", forzar=None):
    """Archivo WAUT de la secuencia; forzar = instante unico para todos (cambio ingenuo, solo para la prueba 3)."""
    texto, instantes = franja.texto_waut(c.p, secuencia, prefijo, wid)
    if forzar is not None:
        import re
        texto = re.sub(r'wautSwitch time="\d+"', f'wautSwitch time="{forzar}"', texto)
        instantes = {tls: [forzar] * len(ts) for tls, ts in instantes.items()}
    ruta = os.path.join(TMP, f"{nombre}.add.xml")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)
    return ruta, instantes


def encima(c, ruta):
    _, _, adic = bfn.rutas_cfg(c.cfg)
    return ",".join(adic + [ruta])


def registrar(c, adicionales, semilla, nombre):
    """Por TraCI, sin tocar los semaforos: programa y estado de cada semaforo en cada segundo (antes del paso)."""
    ti = os.path.join(TMP, f"ti_reg_{nombre}.xml")
    traci.start(["sumo", "-c", c.cfg, "--additional-files", adicionales, "--seed", str(semilla),
                 "--no-step-log", "true", "--no-warnings", "true", "--end", "6000", "--tripinfo-output", ti])
    serie = {tls: [] for tls in c.p.ids}
    while traci.simulation.getMinExpectedNumber() > 0 and traci.simulation.getTime() < 6000:
        for tls in c.p.ids:
            serie[tls].append((traci.trafficlight.getProgram(tls),
                               traci.trafficlight.getRedYellowGreenState(tls)))
        traci.simulationStep()
    traci.close()
    return serie


def cortes(serie):
    """Enlaces que pasan de verde (G/g) a rojo sin ambar entre dos segundos seguidos."""
    total = 0
    for estados in serie.values():
        for (_, a), (_, b) in zip(estados, estados[1:]):
            total += sum(1 for x, y in zip(a, b) if x in "Gg" and y in "rR")
    return total


def ambares(serie, ambar=3):
    """(ambares tras un verde mas cortos que ambar s, ambares tras un rojo, verdes tras un ambar) en la serie."""
    cortos = tras_rojo = verde_tras = 0
    for estados in serie.values():
        e = [s for _, s in estados]
        for i in range(len(e[0])):
            t = 1
            while t < len(e):
                if e[t][i] == "y" and e[t - 1][i] != "y":
                    fin = t
                    while fin < len(e) and e[fin][i] == "y":
                        fin += 1
                    if e[t - 1][i] in "Gg" and fin < len(e) and fin - t < ambar:
                        cortos += 1
                    tras_rojo += e[t - 1][i] in "rR"
                    verde_tras += fin < len(e) and e[fin][i] in "Gg"
                    t = fin
                t += 1
    return cortos, tras_rojo, verde_tras


def prueba_igual_al_fijo(esc):
    c = bfn.Celda(esc, prefijos=())
    pl = plan_plantilla(c)
    ruta, _ = escribir(c, f"igual_{esc}", [(0, pl), (franja.CORTE_FRANJA, pl)])
    s = up.HUMO[0]
    a = up.sumo_directo(c.cfg, None, s, os.path.join(TMP, f"ti_fijo_{esc}.xml"))
    b = up.sumo_directo(c.cfg, encima(c, ruta), s, os.path.join(TMP, f"ti_franja_{esc}.xml"))
    ha, hb = up.huella_tripinfo(os.path.join(TMP, f"ti_fijo_{esc}.xml")), \
        up.huella_tripinfo(os.path.join(TMP, f"ti_franja_{esc}.xml"))
    inf.chequeo(ha == hb and a == b, f"1 {esc}: franja {pl['clave']} -> el mismo, sumo directo: tripinfo {hb} = fijo "
                                     f"{ha}; retraso total {b['retraso_total_prom']} = {a['retraso_total_prom']}")
    _, _, _, correr_f = evaluar.brazo_referencia(esc, "fijo")
    _, _, _, correr_w = evaluar.brazo_referencia(esc, "franja", ruta)
    ra = correr_f(s, os.path.join(TMP, f"ti_tfijo_{esc}.xml"), None)
    rb = correr_w(s, os.path.join(TMP, f"ti_tfranja_{esc}.xml"), None)
    ha2, hb2 = up.huella_tripinfo(os.path.join(TMP, f"ti_tfijo_{esc}.xml")), \
        up.huella_tripinfo(os.path.join(TMP, f"ti_tfranja_{esc}.xml"))
    inf.chequeo(ha2 == hb2 == ha and ra == rb,
                f"1 {esc}: por TraCI (evaluar fijo y franja): {hb2} = {ha2}; mismas metricas: {ra == rb}")


def prueba_cambio(esc, pl1, pl2, nombre, semilla):
    c = bfn.Celda(esc, prefijos=())
    p1, p2 = c.plan(*pl1), c.plan(*pl2)
    ruta, instantes = escribir(c, f"cambio_{nombre}", [(0, p1), (franja.CORTE_FRANJA, p2)])
    solo, _ = escribir(c, f"solo_{nombre}", [(0, p2)])
    serie = registrar(c, encima(c, ruta), semilla, nombre)
    ref = registrar(c, encima(c, solo), semilla, nombre + "_solo")
    for tls in c.p.ids:
        t_cambio = instantes[tls][0]
        primero = next(t for t, (prog, _) in enumerate(serie[tls]) if prog == "franja2")
        antes = all(prog == "franja1" for prog, _ in serie[tls][:primero])
        alineado = all(serie[tls][t][1] == ref[tls][t][1] for t in range(primero, min(len(serie[tls]), len(ref[tls]))))
        inf.chequeo(primero == t_cambio + 1 and antes and alineado and t_cambio >= franja.CORTE_FRANJA,
                    f"2 {nombre} {tls}: instante limpio {t_cambio} s (WAUT), franja2 desde {primero} s, alineado con "
                    f"el plan 2 solo en los {len(serie[tls]) - primero} s siguientes: {alineado}")
    n = cortes(serie)
    inf.chequeo(n == 0, f"3 {nombre}: cortes de verde sin ambar con los instantes limpios: {n}")
    ingenuo, _ = escribir(c, f"ingenuo_{nombre}", [(0, p1), (franja.CORTE_FRANJA, p2)], forzar=1800)
    m = cortes(registrar(c, encima(c, ingenuo), semilla, nombre + "_ingenuo"))
    inf(f"  3 {nombre}: con el cambio de todos a los 1800 s habria {m} cortes")
    # 4. sumo directo = TraCI
    ti_d, ti_t = os.path.join(TMP, f"ti_d_{nombre}.xml"), os.path.join(TMP, f"ti_t_{nombre}.xml")
    a = up.sumo_directo(c.cfg, encima(c, ruta), semilla, ti_d)
    _, _, _, correr = evaluar.brazo_referencia(esc, "franja", ruta)
    b = correr(semilla, ti_t, None)
    ha, hb = up.huella_tripinfo(ti_d), up.huella_tripinfo(ti_t)
    inf.chequeo(ha == hb and all(a[k] == b[k] for k in a),
                f"4 {nombre}: sumo directo {ha} = TraCI {hb}; retraso total {a['retraso_total_prom']} = "
                f"{b['retraso_total_prom']}")
    return m


def prueba_bloques(esc, planes, nombre, semilla):
    c = bfn.Celda(esc, bloque=franja.BLOQUE, prefijos=())
    pls = [c.plan(*x) for x in planes]
    secuencia = franja.secuencia_sin_repetir(pls, c.cortes)
    ruta, instantes = escribir(c, f"bloques_{nombre}", secuencia, "bloque", "bloques")
    serie = registrar(c, encima(c, ruta), semilla, f"bl_{nombre}")
    ok = True
    for tls in c.p.ids:
        progs = [prog for prog, _ in serie[tls]]
        entradas = [t for t in range(1, len(progs)) if progs[t] != progs[t - 1]]
        esperado = [t + 1 for t in instantes[tls]]
        ok &= entradas == esperado and all(t >= t_nom for t, (t_nom, _) in zip(instantes[tls], secuencia[1:]))
    inf.chequeo(ok, f"5 {nombre}: {len(secuencia)} programas; cada semaforo cambia en sus instantes limpios "
                    f"(p. ej. {c.p.ids[0]}: {instantes[c.p.ids[0]]})")
    n = cortes(serie)
    inf.chequeo(n == 0, f"5 {nombre}: cortes de verde sin ambar: {n}")
    ti_d, ti_t = os.path.join(TMP, f"ti_bd_{nombre}.xml"), os.path.join(TMP, f"ti_bt_{nombre}.xml")
    a = up.sumo_directo(c.cfg, encima(c, ruta), semilla, ti_d)
    _, _, _, correr = evaluar.brazo_referencia(esc, "bloques", ruta)
    b = correr(semilla, ti_t, None)
    ha, hb = up.huella_tripinfo(ti_d), up.huella_tripinfo(ti_t)
    inf.chequeo(ha == hb and all(a[k] == b[k] for k in a),
                f"5 {nombre}: sumo directo {ha} = TraCI modo bloques {hb}")


def instante_viejo(a, b, desde):
    """La regla de antes (solo la estricta): el t, o None donde abortaba."""
    hasta = desde + math.lcm(a[1], b[1]) + max(a[1], b[1])
    for t in range(desde, hasta + 1):
        if all(franja.estado_en(*a, x) == franja.estado_en(*b, x) for x in (t - 1, t, t + 1)):
            return t
    return None


def prueba_sin_estricto(esc, pl1, pl2, nombre, semilla, regla):
    c = bfn.Celda(esc, prefijos=())
    p1, p2 = c.plan(*pl1), c.plan(*pl2)
    secuencia = [(0, p1), (franja.CORTE_FRANJA, p2)]
    abortaba = [tls for i, tls in enumerate(c.p.ids)
                if instante_viejo(franja.programa_tls(c.p, p1, i), franja.programa_tls(c.p, p2, i), 1800) is None]
    r = franja.resumen_cambios(c.p, secuencia)
    ruta, instantes = escribir(c, f"sin_estricto_{nombre}", secuencia)
    solo, _ = escribir(c, f"solo_{nombre}", [(0, p2)])
    serie = registrar(c, encima(c, ruta), semilla, nombre)
    ref = registrar(c, encima(c, solo), semilla, nombre + "_solo")
    ok_cambio = True
    for tls in c.p.ids:
        t_cambio = instantes[tls][0]
        primero = next(t for t, (prog, _) in enumerate(serie[tls]) if prog == "franja2")
        alineado = all(serie[tls][t][1] == ref[tls][t][1] for t in range(primero, min(len(serie[tls]), len(ref[tls]))))
        ok_cambio &= primero == t_cambio + 1 and alineado
    n = cortes(serie)
    cortos, tras_rojo, verde_tras = ambares(serie)
    detalle = {tls[-2:]: [(d["regla"], d["instante"], d["retraso"]) for d in lista]
               for tls, lista in r["por_semaforo"].items()}
    inf.chequeo(abortaba and r["reglas"][regla] > 0 and r["reglas"]["forzado"] == 0 and ok_cambio and n == 0
                and cortos == 0,
                f"6 {nombre}: antes abortaba en {len(abortaba)} semaforos; ahora reglas {r['reglas']}, por semaforo "
                f"(regla, instante, retraso) {detalle}; cambia en su instante y entra alineado: {ok_cambio}; verdes "
                f"cortados {n}, ambares cortos tras un verde {cortos} (ambares tras un rojo {tras_rojo}, verdes tras "
                f"un ambar {verde_tras})")
    return r


def prueba_regla_de_antes(n_pares=3000):
    """Sin sumo: el instante estricto no cambia donde el codigo de antes lo encontraba."""
    rng = random.Random(424301)
    celdas = [bfn.Celda(esc, prefijos=()) for esc in ("corredor", "red", "malla3_alta")]
    verdes = list(range(10, 61))
    cuenta = {r: 0 for r in franja.REGLAS_CAMBIO}
    distintos, malos, retraso_max = [], [], {r: 0 for r in franja.REGLAS_CAMBIO}
    for k in range(n_pares):
        c = celdas[k % 3]
        a1, t1, a2, t2 = (rng.choice(verdes) for _ in range(4))
        ci1, ci2 = c.p.ciclo(a1, t1), c.p.ciclo(a2, t2)
        if c.malla:
            e1, e2 = rng.choice(franja.bfn.ESQUEMAS_FINA), rng.choice(franja.bfn.ESQUEMAS_FINA)
            p1 = c.plan(a1, t1, c.desfases_esquema(ci1, e1), e1)
            p2 = c.plan(a2, t2, c.desfases_esquema(ci2, e2), e2)
        else:
            p1 = c.plan(a1, t1, [rng.randrange(ci1) for _ in c.p.ids])
            p2 = c.plan(a2, t2, [rng.randrange(ci2) for _ in c.p.ids])
        for i in range(len(c.p.ids)):
            a, b = franja.programa_tls(c.p, p1, i), franja.programa_tls(c.p, p2, i)
            viejo = instante_viejo(a, b, 1800)
            t, regla, problemas = franja.instante_limpio(a, b, 1800)
            cuenta[regla] += 1
            retraso_max[regla] = max(retraso_max[regla], t - 1800)
            if (viejo is not None and (t, regla) != (viejo, "estricta")) or (viejo is None and regla == "estricta"):
                distintos.append((c.esc, p1["clave"], p2["clave"], i, viejo, t, regla))
            if any(p in ("verde_a_rojo", "ambar_corto") for _, p in franja.problemas_del_cambio(a, b, t)):
                malos.append((c.esc, p1["clave"], p2["clave"], i, t, regla))
    inf.chequeo(not distintos and not malos and cuenta["forzado"] == 0,
                f"7 {n_pares} pares al azar en P1, P3 y P6 ({sum(cuenta.values())} cambios de semaforo): reglas "
                f"{cuenta}, retraso maximo por regla {retraso_max}; instante estricto distinto del de antes: "
                f"{len(distintos)} {distintos[:2]}; cambios que cortan un verde o dejan un ambar corto: {len(malos)}")


def main():
    inf("Pruebas de 0.8: fijo por franja y por bloques con WAUT (semillas de humo)")
    for esc in ("corredor", "red", "malla3_alta"):
        prueba_igual_al_fijo(esc)
    s = up.HUMO[0]
    # P1: el par del prototipo waut_prueba (20/10 0/15 -> 25/15 0/30) y dos desfases que cortaban (5 y 40)
    m = [prueba_cambio("corredor", (20, 10, [0, 15]), (25, 15, [0, 30]), "P1_off30", s),
         prueba_cambio("corredor", (20, 10, [0, 15]), (25, 15, [0, 5]), "P1_off5", s),
         prueba_cambio("corredor", (20, 10, [0, 15]), (25, 15, [0, 40]), "P1_off40", up.HUMO[1])]
    m.append(prueba_cambio("red", (10, 10, [0, 25, 24]), (20, 10, [0, 7, 30]), "P3", s))
    m.append(prueba_cambio("malla3_alta", (15, 10, [0] * 9, "cero"), (12, 10, [0, 11, 22] * 3), "P6", s))
    inf.chequeo(any(x > 0 for x in m), f"3 la prueba ve cortes cuando los hay (cambio ingenuo): {m}")
    prueba_bloques("corredor", [(20, 10, [0, 15]), (25, 15, [0, 30]), (25, 15, [0, 5]), (30, 15, [0, 40]),
                                (20, 10, [0, 10]), (15, 10, [0, 20])], "P1", s)
    prueba_bloques("malla3_alta", [(15, 10, [0] * 9, "cero"), (12, 10, [0, 11, 22] * 3),
                                   (14, 10, [0] * 9, "cero"), (14, 10, [0] * 9, "cero"),
                                   (20, 15, [0, 19, 0, 19, 0, 19, 0, 19, 0]), (15, 10, [0] * 9, "cero")],
                   "P6", s)
    prueba_sin_estricto("corredor", (25, 10, [0, 0]), (15, 20, [0, 15]), "P1_relajada", s, "relajada")
    prueba_sin_estricto("corredor", (10, 10, [0, 0]), (10, 10, [13, 13]), "P1_contrafase", s, "respaldo")
    prueba_sin_estricto("red", (20, 15, [0, 22, 8]), (20, 15, [0, 26, 26]), "P3_relajada", s, "relajada")
    c6 = bfn.Celda("malla3_alta", prefijos=())
    prueba_sin_estricto("malla3_alta", (18, 25, c6.desfases_esquema(c6.p.ciclo(18, 25), "ajedrez"), "ajedrez"),
                        (25, 18, c6.desfases_esquema(c6.p.ciclo(25, 18), "onda"), "onda"), "P6_respaldo", s,
                        "respaldo")
    prueba_regla_de_antes()
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
