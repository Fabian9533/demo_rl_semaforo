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
     error y el instalado queda igual, sin temporales; p3_preparar sin --piezas hace solo actuado y trivial.
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
    os.chdir(up.PLAN3)
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
