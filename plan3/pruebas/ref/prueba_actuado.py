"""
prueba_actuado.py - Pruebas de la tarea 0.9 (actuado.py, modo actuado_aj de rl_corredor y evaluar.py):
  1. la variante por defecto reproduce el actuado entregado: el mismo programa que comun.archivo_actuado (salvo el
     programID) y el mismo tripinfo, sumo directo frente al brazo actuado de evaluar (TraCI), en P1-P6;
  2. cada parametro mueve algun numero (tripinfo distinto del de la variante que solo difiere en ese parametro) en
     P2 o P6;
  3. el log de SUMO no trae avisos con cada tipo de variante (defecto, <param>, delay_based y las dos coordinadas) en
     P1-P6;
  4. sumo directo = TraCI (evaluar.brazo_referencia(esc, "actuado_aj", archivo)) tambien con <param>, con
     delay_based y con las dos variantes coordinadas (solo earliestEnd en la avenida, y earliestEnd = latestEnd), en
     P1, P3 y P6;
  5. reinstalar (p3_preparar --piezas actuado_aj): con el instalado igual al congelado no lo toca (misma fecha); si
     el instalado cambio o falta, lo reescribe con el sha256 congelado; si el texto de hoy no da el sha256 congelado,
     error y el instalado queda igual, sin temporales; p3_preparar sin --piezas hace solo actuado y trivial;
  6. la variante coordinada (b) "fin fijo" termina el verde de avenida en el fin del plan fijo, con un plan cuya
     transversal puede cortar antes (holgura) y con maxDur de la cadena = los verdes fijos (el caso dificil), en P2
     (la avenida es la fase 2), P3 y P6 (la avenida es la fase 0): tantas salidas como el plan fijo (+-1) y a lo sumo
     2 por semaforo fuera del fin fijo (el arranque); la transversal nunca termina despues de su fin fijo;
  7. donde pone SUMO los detectores del actuado (TraCI, inductionloop): a min(detector-gap x vmax, (minDur /
     passing-time + 0.5) x 7.5 m, largo del carril) de la linea, con passing-time 1.9 y minDur 10: con detector-gap 2,
     27.8 m; con 4, el tope de 43.2 m (informe_ref 1.3), en P1 y P6.
La variante coordinada usa un fijo fino de prueba (el fijo entregado, escrito como fijo_fino.json en tmp_ref, con la
marca de prueba: la celda corre con permitir).
Semillas de humo. Corre en una copia de los escenarios (tmp_ref/actuado/). Uso (cwd = plan3/):
  python pruebas/ref/prueba_actuado.py        Salida: pruebas/ref/salidas/prueba_actuado.txt
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
inf = up.Informe("prueba_actuado")
CASOS = {"P1": "corredor", "P2": "corredor_alta", "P3": "red", "P4": "red_alta", "P5": "malla3",
         "P6": "malla3_alta"}
CARPETA = up.copia("actuado", list(CASOS.values()))
import barrer_fino as bfn  # noqa: E402
import actuado  # noqa: E402
import evaluar  # noqa: E402
import concurrent.futures  # noqa: E402

S = up.HUMO[0]


def celda(esc):
    c = bfn.Celda(esc, prefijos=())
    c.carpeta = os.path.join(CARPETA, "barridos", esc)
    os.makedirs(c.carpeta, exist_ok=True)
    # fijo fino de prueba: el fijo entregado (plantilla) como si fuera el ganador de barrer_fino
    i = 0
    fases = [f for f in c.p.tls[i] if f.tag == "phase"]
    av = int(fases[c.p.fases_av[i]].get("duration"))
    tr = int(next(f.get("duration") for k, f in enumerate(fases)
                  if bfn.bf.es_verde(f.get("state")) and k != c.p.fases_av[i]))
    pl = c.plan(av, tr, [int(tl.get("offset")) for tl in c.p.tls])
    with open(os.path.join(c.carpeta, "fijo_fino.json"), "w", encoding="utf-8") as f:
        json.dump({"ids": c.p.ids, "ciclo": pl["ciclo"], "offsets": pl["offsets"], "verde": av,
                   "verde_transversal": tr, "sha256": "prueba",
                   "registro": {"prueba": ["fijo fino de prueba: la plantilla (prueba_actuado)"]}}, f)
    c.permitir = True                     # el fijo fino de prueba lleva la marca de prueba
    return c


def archivo(c, v, nombre):
    ruta = os.path.join(CARPETA, f"{c.esc}_{nombre}.add.xml")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(actuado.texto_actuado(c, v))
    return ruta


def encima(c, ruta):
    _, _, adic = bfn.rutas_cfg(c.cfg)
    return ",".join(adic + [ruta])


def defecto(caso, esc):
    c = celda(esc)
    ruta = archivo(c, dict(actuado.DEFECTO), "defecto")
    _, _, _, correr = evaluar.brazo_referencia(esc, "actuado")
    ref = correr(S, f"ti_act_{esc}.xml", None)            # escribe <esc>_actuado.add.xml (comun) en la copia
    entregado = open(f"{esc}_actuado.add.xml", encoding="utf-8").read()
    mio = open(ruta, encoding="utf-8").read()
    bloques = lambda t: sorted(b.split("</tlLogic>")[0] for b in t.split("<tlLogic")[1:])   # noqa: E731
    mismo_programa = bloques(entregado) == bloques(mio.replace('programID="actuado_aj"', 'programID="actuado"'))
    r = up.sumo_directo(c.cfg, encima(c, ruta), S, f"ti_def_{esc}.xml")
    h1, h2 = up.huella_tripinfo(f"ti_act_{esc}.xml"), up.huella_tripinfo(f"ti_def_{esc}.xml")
    inf.chequeo(mismo_programa and h1 == h2 and r["retraso_total_prom"] == ref["retraso_total_prom"],
                f"1 {caso}: defecto = actuado entregado: programa igual {mismo_programa}; tripinfo {h2} = {h1}; "
                f"retraso total {r['retraso_total_prom']} = {ref['retraso_total_prom']}")


def variantes(c):
    base = dict(actuado.DEFECTO)
    salida = {"max-gap 1": dict(base, **{"max-gap": 1.0}), "detector-gap 4": dict(base, **{"detector-gap": 4.0}),
              "jam-threshold 30": dict(base, **{"jam-threshold": 30}), "maxDur avenida 30": dict(base, maxdur_av=30),
              "maxDur transversal 20": dict(base, maxdur_tr=20),
              "delay_based 50 m": dict(maxdur_av=60, maxdur_tr=60, tipo="delay_based", detectorRange=50,
                                       minTimeLoss=1, coordinado=False),
              "delay_based minTimeLoss 3": dict(maxdur_av=60, maxdur_tr=60, tipo="delay_based", detectorRange=100,
                                                minTimeLoss=3, coordinado=False),
              "coordinada": actuado.coordinada(c, base),
              "coordinada fin fijo": actuado.coordinada(c, base, fin_fijo=True)}
    return salida


# cada variante frente a la que solo difiere en ese parametro (no frente al actuado por defecto: una variante
# delay_based siempre difiere del actuado aunque su parametro se ignore, y eso escondio que SUMO 1.25 lee
# "minTimeloss" y no "minTimeLoss")
PAREJAS = {"max-gap 1": "defecto", "detector-gap 4": "defecto", "jam-threshold 30": "defecto",
           "maxDur avenida 30": "defecto", "maxDur transversal 20": "defecto", "coordinada": "defecto",
           "coordinada fin fijo": "coordinada",
           "delay_based 50 m": "delay_based 100 m", "delay_based minTimeLoss 3": "delay_based 100 m"}


def mueve(caso, esc):
    c = celda(esc)
    vs = {"defecto": dict(actuado.DEFECTO),
          "delay_based 100 m": dict(maxdur_av=60, maxdur_tr=60, tipo="delay_based", detectorRange=100,
                                    minTimeLoss=1, coordinado=False), **variantes(c)}

    def una(item):
        nombre, v = item
        r = archivo(c, v, "m_" + nombre.replace(" ", "_"))
        ti = f"ti_m_{esc}_{nombre.replace(' ', '_')}.xml"
        res = up.sumo_directo(c.cfg, encima(c, r), S, ti)
        return nombre, up.huella_tripinfo(ti), res["retraso_total_prom"]
    with concurrent.futures.ThreadPoolExecutor(3) as ex:
        res = {n: (h, t) for n, h, t in ex.map(una, vs.items())}
    return {n: (res[n][0] != res[ref][0], f"{res[n][1]} frente a {res[ref][1]} de {ref}")
            for n, ref in PAREJAS.items()}


def avisos(caso, esc):
    c = celda(esc)
    vs = {"defecto": dict(actuado.DEFECTO), **variantes(c)}
    vs = {k: vs[k] for k in ("defecto", "max-gap 1", "jam-threshold 30", "delay_based 50 m", "coordinada",
                             "coordinada fin fijo")}

    def una(item):
        nombre, v = item
        r = archivo(c, v, "a_" + nombre.replace(" ", "_"))
        log = f"log_{esc}_{nombre.replace(' ', '_')}.txt"
        up.sumo_directo(c.cfg, encima(c, r), S, f"ti_a_{esc}_{nombre.replace(' ', '_')}.xml", log=log)
        texto = open(log, encoding="utf-8", errors="replace").read()
        return nombre, texto.count("Warning"), texto.count("Error")
    with concurrent.futures.ThreadPoolExecutor(3) as ex:
        res = list(ex.map(una, vs.items()))
    inf.chequeo(all(w == 0 and e == 0 for _, w, e in res),
                f"3 {caso}: avisos y errores en el log de SUMO: " + ", ".join(f"{n} {w}/{e}" for n, w, e in res))


def directo_traci(caso, esc):
    c = celda(esc)
    vs = variantes(c)
    for nombre in ("max-gap 1", "delay_based minTimeLoss 3", "coordinada", "coordinada fin fijo"):
        ruta = archivo(c, vs[nombre], "t_" + nombre.replace(" ", "_"))
        a = up.sumo_directo(c.cfg, encima(c, ruta), S, f"ti_d_{esc}.xml")
        _, _, _, correr = evaluar.brazo_referencia(esc, "actuado_aj", ruta)
        b = correr(S, f"ti_t_{esc}.xml", None)
        ha, hb = up.huella_tripinfo(f"ti_d_{esc}.xml"), up.huella_tripinfo(f"ti_t_{esc}.xml")
        inf.chequeo(ha == hb and all(a[k] == b[k] for k in a),
                    f"4 {caso} {nombre}: sumo directo {ha} = TraCI {hb}; retraso total {a['retraso_total_prom']} = "
                    f"{b['retraso_total_prom']}")


def reinstalar():
    import glob
    import shutil
    import subprocess
    c = celda("corredor")
    v = dict(actuado.DEFECTO, **{"max-gap": 2.0})
    datos = {"escenario": "corredor", "llegadas": c.llegadas, "huella": c.huella, "clave": actuado.clave(v),
             "variante": v, "variantes_probadas": 1, "semillas_pasos": "prueba", "finalistas": [actuado.clave(v)],
             "retraso_total_prom": 0, "retraso_total_sd": 0, "timeloss_prom": 0, "mediana": 0, "peor": 0,
             "trabadas": 0, "semillas": "prueba"}
    datos = actuado.instalar(c, datos)
    destino = "corredor_actuado_aj.add.xml"
    f0 = os.stat(destino).st_mtime_ns
    actuado.reinstalar("corredor", c.carpeta)
    igual_sin_tocar = os.stat(destino).st_mtime_ns == f0 and up.sha256(destino) == datos["sha256"]
    with open(destino, "a", encoding="utf-8") as f:
        f.write("<!-- cambiado a mano -->" + os.linesep)
    actuado.reinstalar("corredor", c.carpeta)
    reescrito = up.sha256(destino) == datos["sha256"]
    os.remove(destino)
    actuado.reinstalar("corredor", c.carpeta)
    recreado = up.sha256(destino) == datos["sha256"]
    inf.chequeo(igual_sin_tocar and reescrito and recreado,
                f"5 reinstalar: igual al congelado -> no lo toca (misma fecha): {igual_sin_tocar}; cambiado a mano -> "
                f"reescrito con el sha256 congelado: {reescrito}; borrado -> recreado: {recreado}")
    otra = os.path.join(CARPETA, "barridos", "corredor_sha_malo")
    os.makedirs(otra, exist_ok=True)
    with open(os.path.join(otra, "actuado_aj.json"), "w", encoding="utf-8") as f:
        json.dump(dict(datos, sha256="0" * 64), f)
    antes = up.sha256(destino)
    try:
        actuado.reinstalar("corredor", otra)
        mensaje = "no se nego"
    except SystemExit as e:
        mensaje = str(e)
    temporales = glob.glob(f"{destino}.*.tmp")
    inf.chequeo("no se toca" in mensaje and up.sha256(destino) == antes and not temporales,
                f"5 reinstalar con un sha256 congelado que el texto de hoy no da: error ({mensaje[:90]}...), el "
                f"instalado queda igual: {up.sha256(destino) == antes}, temporales {temporales}")
    f1 = os.stat(destino).st_mtime_ns
    r = subprocess.run([sys.executable, os.path.join(up.PLAN3, "p3_preparar.py"), "corredor"], cwd=CARPETA,
                       capture_output=True, text=True)
    piezas = [x.split()[1].rstrip(":") for x in r.stdout.splitlines() if x.startswith("corredor ")]
    inf.chequeo(r.returncode == 0 and piezas == ["actuado", "trivial"] and os.stat(destino).st_mtime_ns == f1,
                f"5 p3_preparar corredor (sin --piezas): codigo {r.returncode}, piezas {piezas}; el actuado ajustado "
                f"no se toca")
    shutil.rmtree(otra, ignore_errors=True)


def fases_por_segundo(c, nombre, adicionales):
    """sumo directo con SaveTLSStates: {tls: [(t, fase)]} con los cambios de fase."""
    import xml.etree.ElementTree as ET
    log = os.path.join(CARPETA, f"log_alin_{c.esc}_{nombre}.add.xml")
    with open(log, "w", encoding="utf-8") as f:
        f.write("<additional>\n" + "".join(f'<timedEvent type="SaveTLSStates" source="{x}" '
                                           f'dest="tls_alin_{c.esc}_{nombre}_{x}.xml"/>\n' for x in c.p.ids)
                + "</additional>\n")
    up.sumo_directo(c.cfg, ",".join(adicionales + [log]), S, os.path.join(CARPETA, f"ti_alin_{c.esc}_{nombre}.xml"))
    salida = {}
    for x in c.p.ids:
        cambios, prev = [], None
        for e in ET.parse(os.path.join(CARPETA, f"tls_alin_{c.esc}_{nombre}_{x}.xml")).getroot().iter("tlsState"):
            ph = int(e.get("phase"))
            if ph != prev:
                cambios.append((int(float(e.get("time"))), ph))
            prev = ph
        salida[x] = cambios
    return salida


def alineada(caso, esc, plan):
    """La variante (b) con maxDur de la cadena = los verdes fijos termina la avenida en el fin del plan fijo."""
    c = celda(esc)
    pl = c.plan(*plan)
    with open(os.path.join(c.carpeta, "fijo_fino.json"), "w", encoding="utf-8") as f:
        json.dump({"ids": c.p.ids, "ciclo": pl["ciclo"], "offsets": pl["offsets"], "verde": pl["verde"],
                   "verde_transversal": pl["verde_transversal"], "sha256": "prueba", "huella": c.huella,
                   "registro": {"prueba": ["plan con holgura (prueba_actuado 6)"]}}, f)
    fijo = os.path.join(CARPETA, f"{esc}_alin_fijo.add.xml")
    c.escribir_plan(fijo, pl)
    v = actuado.coordinada(c, dict(actuado.DEFECTO, maxdur_av=pl["verde"], maxdur_tr=pl["verde_transversal"]),
                           fin_fijo=True)
    ruta = archivo(c, v, "alin_b")
    _, _, adic = bfn.rutas_cfg(c.cfg)
    ff = fases_por_segundo(c, "fijo", c.p.extra(fijo)[1].split(","))
    fv = fases_por_segundo(c, "b", adic + [ruta])
    C, malos, detalle = pl["ciclo"], [], []
    for i, x in enumerate(c.p.ids):
        fa = c.p.fases_av[i]
        ft = next(k for k, f in enumerate(f for f in c.p.tls[i] if f.tag == "phase")
                  if bfn.bf.es_verde(f.get("state")) and k != fa)

        def fines(cambios, fase):
            return [t2 for (t, ph), (t2, ph2) in zip(cambios, cambios[1:]) if ph == fase and ph2 != fase]
        fijos_av = {t % C for t in fines(ff[x], fa)}
        fijos_tr = sorted({t % C for t in fines(ff[x], ft)})
        mios = fines(fv[x], fa)
        fuera = sum(1 for t in mios if t % C not in fijos_av)
        # la transversal termina en su fin fijo o antes: a lo sumo (verde fijo - minDur) s antes
        holgura = pl["verde_transversal"] - actuado.VERDE_MIN
        tarde = sum(1 for t in fines(fv[x], ft) if not 0 <= (fijos_tr[0] - t) % C <= holgura)
        n_fijo = len(fines(ff[x], fa))
        detalle.append(f"{x[-2:]}: {len(mios)}/{n_fijo} salidas, {fuera} fuera del fin fijo, transversal tarde {tarde}")
        if abs(len(mios) - n_fijo) > 1 or fuera > 2 or tarde > 2:
            malos.append(x)
    inf.chequeo(not malos, f"6 {caso} plan {pl['clave']} (ciclo {C}), (b) con maxDur = verdes fijos: "
                           + "; ".join(detalle))


def posicion_detectores(caso, esc):
    """Los detectores que crea SUMO para el actuado, con detector-gap 2 y 4: a que distancia de la linea quedan."""
    import traci
    c = celda(esc)
    detalle, malos = [], []
    for dg in (2.0, 4.0):
        ruta = archivo(c, dict(actuado.DEFECTO, **{"detector-gap": dg}), f"det_{int(dg)}")
        traci.start(["sumo", "-c", c.cfg, "--additional-files", encima(c, ruta), "--seed", str(S), "--no-step-log",
                     "true", "--no-warnings", "true", "--end", "5",
                     "--tripinfo-output", os.path.join(CARPETA, f"ti_det_{esc}_{int(dg)}.xml")])
        traci.simulationStep()
        distancias = []
        for d in traci.inductionloop.getIDList():
            carril = traci.inductionloop.getLaneID(d)
            largo, vmax = traci.lane.getLength(carril), traci.lane.getMaxSpeed(carril)
            dist = largo - traci.inductionloop.getPosition(d)
            esperado = min(dg * vmax, (actuado.VERDE_MIN / 1.9 + 0.5) * 7.5, largo)
            distancias.append(round(dist, 2))
            if abs(dist - esperado) > 0.05:
                malos.append((dg, d, round(dist, 2), round(esperado, 2)))
        traci.close()
        detalle.append(f"detector-gap {dg:g}: {len(distancias)} detectores a {sorted(set(distancias))} m")
    inf.chequeo(not malos and len(detalle) == 2,
                f"7 {caso}: " + "; ".join(detalle) + (f"; fuera de lo esperado: {malos[:3]}" if malos else ""))


def main():
    inf(f"Pruebas de 0.9: actuado ajustado (copia en {CARPETA}; semilla {S})")
    reinstalar()
    for caso, esc in CASOS.items():
        defecto(caso, esc)
    movidos = {}
    for caso in ("P2", "P6"):
        res = mueve(caso, CASOS[caso])
        inf(f"  2 {caso}: " + "; ".join(f"{n}: {'mueve' if m else 'igual'} ({t})" for n, (m, t) in res.items()))
        for n, (m, _) in res.items():
            movidos[n] = movidos.get(n, False) or m
    inf.chequeo(all(movidos.values()), f"2 cada parametro mueve algun numero en P2 o P6: {movidos}")
    for caso, esc in CASOS.items():
        avisos(caso, esc)
    for caso in ("P1", "P3", "P6"):
        directo_traci(caso, CASOS[caso])
    alineada("P2", "corredor_alta", (25, 15, [0, 25]))
    alineada("P3", "red", (20, 15, [0, 10, 20]))
    alineada("P6", "malla3_alta", (15, 15, [0] * 9, "cero"))
    posicion_detectores("P1", "corredor")
    posicion_detectores("P6", "malla3_alta")
    os.chdir(up.PLAN3)
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
