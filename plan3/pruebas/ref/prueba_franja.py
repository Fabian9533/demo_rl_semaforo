"""
prueba_franja.py - Pruebas de la tarea 0.8 (franja.py, modos franja y bloques de rl_corredor y evaluar.py --brazo):
  1. franja con plan 2 = plan 1 (el fijo entregado) da el mismo tripinfo que el fijo de un plan, por sumo directo y
     por TraCI (P1, P3 y P6);
  2. a los 1800 s el programa cambia en su instante limpio y entra alineado: desde el cambio, el estado de cada
     semaforo es el del plan 2 corriendo solo desde 0 s;
  3. 0 cortes de verde sin ambar en toda la corrida (con dos pares que, cambiando todos a los 1800 s, si cortan:
     la prueba los ve);
  4. sumo directo = TraCI (evaluar.brazo_referencia(esc, "franja", archivo)) con dos planes distintos;
  5. bloques: 6 programas con WAUT en P1 y P6: cambios en sus instantes, 0 cortes y sumo directo = TraCI (modo bloques).
Semillas de humo (424301-424302). Uso (cwd = plan3/): python pruebas/ref/prueba_franja.py
Salida: pruebas/ref/salidas/prueba_franja.txt
"""
import os
import sys

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
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
