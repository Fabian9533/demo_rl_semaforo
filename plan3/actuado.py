"""
actuado.py - Actuado ajustado (plan3, tarea 0.9; DECISIONES A1 y B9; prerregistro, seccion 5).

Uso (cwd = plan3/; con llegadas aleatorias, a traves de ../con_escenarios.py):
  python actuado.py <esc> --paso 1|2|3|4|5|6|final|todos [--procesos 1]
  python actuado.py <esc> --instalar     (reescribe <esc>_actuado_aj.add.xml desde barridos/<esc>/actuado_aj.json;
                                          lo usa p3_preparar.py --piezas actuado_aj)
  Solo para pruebas (fuera de la cola): --llegadas regulares|aleatorias, --semillas, --semillas-final y
  --permitir-prueba. Las opciones van completas (sin abreviar).

El actuado de SUMO 1.25 con <param>, la variante delay_based y dos variantes coordinadas con el ciclo y los desfases
del fijo fino. Descenso por coordenadas en cadena (un paso por coordenada; cada paso parte del mejor de los
anteriores, por la media del retraso total en 2001-2003; en un empate se queda el punto de partida), sin TraCI: sumo
directo con el programa cargado encima de los adicionales del .sumocfg (queda activo por ser el ultimo; la prueba
sumo directo = TraCI esta en pruebas/ref). Rejillas fijas, con el defecto de SUMO (*) incluido:
  paso 1  max-gap                    1, 1.5, 2, 3*, 4 s
  paso 2  detector-gap               1, 2*, 3, 4 s (SUMO pone el detector a min(detector-gap x vmax, (minDur /
                                     passing-time + 0.5) x 7.5 m): con minDur 10 s y passing-time 1.9 (su defecto)
                                     el tope es 43.2 m, asi que en todas las celdas (13.89 m/s) el 4 queda en 43.2 m
                                     (~3.1 s), a 1.55 m del 3 (41.7 m); se deja asi, declarado)
  paso 3  jam-threshold              -1*, 10, 30 s
  paso 4  maxDur del verde de avenida      30, 45, 60* s
  paso 5  maxDur del verde transversal     20, 30, 60* s
  paso 6  familia: delay_based (detectorRange 50, 100, 200 m x minTimeLoss 1*, 3 s, con los maxDur elegidos) y dos
          variantes coordinadas del mejor actuado (prerregistro 5): coordinated=true, cycleTime y desfases del fijo
          fino, las fases de su plantilla con sus duraciones y el verde de avenida con earliestEnd en su fin del plan
          fijo (como la propuso plan3/referencias/informe.md 4), y "fin fijo": latestEnd = earliestEnd en la
          avenida y latestEnd en la transversal, cada uno en su fin del plan fijo (la avenida termina siempre donde
          el plan fijo; la transversal puede cortar antes, nunca despues). Solo latestEnd en la transversal (sin el
          de la avenida) trababa P2 (835 s/veh); solo latestEnd = earliestEnd en la avenida (sin el de la
          transversal) quedaba peor que el fijo en P1, P2, P3 y P6: ninguna de las dos se usa
  final   las 3 mejores variantes de los 6 pasos con 2001-2010 (con llegadas aleatorias, las 10 mejores con
          2001-2030); gana la menor media
minDur 10 s (5 en giros) y la fase y la duracion inicial del programa "0" de la red, como comun.archivo_actuado:
la variante por defecto es el actuado entregado con programID "actuado_aj". Los <param> se escriben solo si difieren
del defecto de SUMO (delay_based los escribe siempre). El paso 6 depende del fijo fino
(barridos/<esc>/fijo_fino.json, barrer_fino.py --etapa fragil). Cadena: cada paso parte del JSON del anterior (misma
huella) y el paso 6 lee el fijo fino; si alguno trae la marca de prueba (o no trae registro), se niega, salvo con
--permitir-prueba (solo pruebas; la salida queda marcada).

Salidas en barridos/<esc>/: actuado_paso<k>.csv, actuado_paso<k>.json (punto de partida, variantes y elegida),
actuado_paso<k>_semillas.csv, actuado_final.csv, actuado_final_semillas.csv y actuado_aj.json; y
<esc>_actuado_aj.add.xml (programID "actuado_aj": lo cargan rl_corredor modo actuado_aj y evaluar.py --brazo
actuado_aj). Todo con temporal y reemplazo; codigo 0 solo con las salidas del paso completas.
"""
import os
import sys
import json
import time
import hashlib
import argparse
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
for _ruta in (AQUI, RAIZ):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import comun  # noqa: E402
import barrer_fijo as bf  # noqa: E402
import barrer_fino as bfn  # noqa: E402

PROGRAMA = "actuado_aj"
VERDE_MIN, VERDE_MIN_GIRO = 10, 5          # los del agente y del actuado entregado
DEFECTO = {"tipo": "actuated", "max-gap": 3.0, "detector-gap": 2.0, "jam-threshold": -1,
           "maxdur_av": 60, "maxdur_tr": 60, "coordinado": False}
PARAMS_ACTUADO = ("max-gap", "detector-gap", "jam-threshold")
PASOS = (("max-gap", (1.0, 1.5, 2.0, 3.0, 4.0)),
         ("detector-gap", (1.0, 2.0, 3.0, 4.0)),
         ("jam-threshold", (-1, 10, 30)),
         ("maxdur_av", (30, 45, 60)),
         ("maxdur_tr", (20, 30, 60)),
         ("familia", None))
DELAY = [(r, m) for r in (50, 100, 200) for m in (1, 3)]
FINALES = {"regulares": 3, "aleatorias": 10}
SEMILLAS_PASOS = "2001-2003"               # prerregistro 5: los pasos con 2001-2003 tambien con llegadas aleatorias


def num(x):
    return f"{x:g}" if isinstance(x, float) else str(x)


def clave(v):
    """Identificador del programa de una variante."""
    if v["tipo"] == "delay_based":
        s = f"del_dr{num(v['detectorRange'])}_mt{num(v['minTimeLoss'])}"
    else:
        s = "act_" + "_".join(f"{k[0]}{k.split('-')[1][0]}{num(v[k])}" for k in PARAMS_ACTUADO)
    s += f"_av{v['maxdur_av']}_tr{v['maxdur_tr']}"
    if v["coordinado"]:
        fino = json.dumps([v["ciclo"], v["offsets"], v["verde"], v["verde_transversal"]])
        s += "_coord" + hashlib.sha256(fino.encode()).hexdigest()[:8]
        if v.get("fin_fijo"):                 # latestEnd = earliestEnd en la avenida y latestEnd en la transversal
            s += "_finfijo"
    return s


def params(v):
    """<param> de la variante: los del actuado que difieren del defecto de SUMO; delay_based, siempre los suyos;
    la coordinada, coordinated y cycleTime. OJO: SUMO 1.25 lee la clave "minTimeloss" (asi esta en sumo.exe); con
    "minTimeLoss", como dice su documentacion, la ignora sin aviso (medido: 0.01, 1 y 1000 dan el mismo tripinfo)."""
    if v["tipo"] == "delay_based":
        salida = [("detectorRange", num(v["detectorRange"])), ("minTimeloss", num(v["minTimeLoss"]))]
    else:
        salida = [(k, num(v[k])) for k in PARAMS_ACTUADO if v[k] != DEFECTO[k]]
    if v["coordinado"]:
        salida += [("coordinated", "true"), ("cycleTime", str(v["ciclo"]))]
    return salida


def fase_avenida_red(c, net_file):
    """Indice de la fase de avenida del programa "0" de la red, por semaforo (barrer_fijo.fase_avenida)."""
    salida = {}
    for tl in ET.parse(net_file).getroot().findall("tlLogic"):
        if tl.get("id") in c.p.ids and tl.get("id") not in salida:
            salida[tl.get("id")] = bf.fase_avenida(tl, c.p.geo[tl.get("id")]["horizontal"])
    return salida


def texto_actuado(c, v, comentario=None):
    """El .add.xml de una variante (un tlLogic por semaforo, programID actuado_aj)."""
    import sumolib
    net_file, _ = comun.leer_cfg(c.cfg)
    lineas = ["<additional>"]
    if comentario:
        import textwrap
        texto = comentario.replace("--", "- -")              # un comentario XML no puede llevar "--"
        lineas.append("    <!-- " + "\n         ".join(textwrap.wrap(texto, 96)) + " -->")
    if not v["coordinado"]:                # fases del programa "0" de la red, como comun.archivo_actuado
        net = sumolib.net.readNet(net_file, withPrograms=True)
        av = fase_avenida_red(c, net_file)
    for i, tls in enumerate(c.p.ids):
        if v["coordinado"]:                # fases de la plantilla con las duraciones del fijo fino
            fases = [(d, e) for d, e in fases_plantilla(c, i, v)]
            fase_av, offset = c.p.fases_av[i], v["offsets"][i]
        else:
            programas = net.getTLS(tls).getPrograms()
            programa = programas.get("0", next(iter(programas.values())))
            fases = [(int(f.duration), f.state) for f in programa.getPhases()]
            fase_av, offset = av[tls], 0
        lineas.append(f'    <tlLogic id="{tls}" type="{v["tipo"]}" programID="{PROGRAMA}" offset="{offset}">')
        for k, valor in params(v):
            lineas.append(f'        <param key="{k}" value="{valor}"/>')
        inicio = 0
        for k, (dur, estado) in enumerate(fases):
            if bf.es_verde(estado):
                minimo = VERDE_MIN if sum(1 for x in estado if x in "Gg") > 2 else VERDE_MIN_GIRO
                maximo = v["maxdur_av"] if k == fase_av else v["maxdur_tr"]
                extra = ""
                if v["coordinado"]:
                    dur = min(max(dur, minimo), maximo)
                    fin = (inicio + fases[k][0]) % v["ciclo"]          # fin de ese verde en el plan fijo
                    if k == fase_av:           # la avenida no termina antes de su fin en el plan fijo
                        extra = f' earliestEnd="{fin}"'
                        if v.get("fin_fijo"):  # ni despues: termina en su fin del plan fijo
                            extra += f' latestEnd="{fin}"'
                    elif v.get("fin_fijo"):    # y la transversal no pasa del suyo (puede cortar antes)
                        extra = f' latestEnd="{fin}"'
                lineas.append(f'        <phase duration="{dur}" minDur="{minimo}" maxDur="{maximo}" '
                              f'state="{estado}"{extra}/>')
            else:
                lineas.append(f'        <phase duration="{dur}" state="{estado}"/>')
            inicio += fases[k][0]
        lineas.append("    </tlLogic>")
    lineas.append("</additional>")
    return "\n".join(lineas) + "\n"


def fases_plantilla(c, i, v):
    """[(duracion, estado)] del semaforo i de la plantilla con los verdes del fijo fino (barrer_fijo)."""
    salida = []
    for k, fase in enumerate(f for f in c.p.tls[i] if f.tag == "phase"):
        estado = fase.get("state")
        if bf.es_verde(estado):
            dur = v["verde"] if k == c.p.fases_av[i] else v["verde_transversal"]
        else:
            dur = int(float(fase.get("duration")))
        salida.append((int(dur), estado))
    assert sum(d for d, _ in salida) == v["ciclo"], "el ciclo del fijo fino no coincide con su plantilla"
    return salida


def plan_variante(c, v):
    def escribir(ruta):
        bfn.escribir_atomico(ruta, texto_actuado(c, v), encoding="utf-8")
    return {"clave": clave(v), "escribir": escribir, "var": v}


def coordinada(c, v, fin_fijo=False):
    """La variante coordinada de v con el fijo fino de la celda (fin_fijo: ademas latestEnd = earliestEnd en el verde
    de la avenida y latestEnd en el transversal, cada uno en su fin del plan fijo)."""
    ruta = os.path.join(c.carpeta, "fijo_fino.json")
    if not os.path.exists(ruta):
        raise SystemExit(f"Falta {ruta}: la variante coordinada usa el fijo fino (barrer_fino --etapa fragil)")
    fino = c.comprobar_marca(ruta)
    if fino["ids"] != c.p.ids:
        raise SystemExit(f"{ruta}: semaforos en otro orden que la plantilla")
    salida = dict(v, coordinado=True, ciclo=fino["ciclo"], offsets=fino["offsets"], verde=fino["verde"],
                  verde_transversal=fino["verde_transversal"], fino_sha256=fino["sha256"])
    if fin_fijo:
        salida["fin_fijo"] = True
    return salida


def fila_variante(c, pl, semillas, etapa):
    v = pl["var"]
    fila = {"etapa": etapa, "clave": pl["clave"], "tipo": v["tipo"],
            **{k: v.get(k, "") for k in PARAMS_ACTUADO + ("maxdur_av", "maxdur_tr")},
            "detectorRange": v.get("detectorRange", ""), "minTimeLoss": v.get("minTimeLoss", ""),
            "coordinado": int(v["coordinado"]), "fin_fijo": int(bool(v.get("fin_fijo")))}
    fila.update(c.metricas(pl["clave"], semillas))
    return fila


def campos_variante(c):
    return (["etapa", "clave", "tipo"] + list(PARAMS_ACTUADO) + ["maxdur_av", "maxdur_tr", "detectorRange",
                                                                "minTimeLoss", "coordinado", "fin_fijo"]
            + c.campos_metricas())


def leer_json(ruta):
    return bfn.leer_json(ruta)


def paso_anterior(c, ruta):
    """El JSON de un paso ya corrido: de esta huella y de la regla (sin marca de prueba, salvo --permitir-prueba)."""
    datos = leer_json(ruta)
    if datos["huella"] != c.huella:
        raise SystemExit(f"{ruta} es de otra huella del escenario ({datos['huella']}, hoy {c.huella}): repita los "
                         f"pasos")
    return c.comprobar_marca(ruta)


def punto_de_partida(c, k):
    if k == 1:
        return dict(DEFECTO)
    ruta = os.path.join(c.carpeta, f"actuado_paso{k - 1}.json")
    if not os.path.exists(ruta):
        raise SystemExit(f"Falta {ruta}: los pasos van en cadena (corra antes el paso {k - 1})")
    return paso_anterior(c, ruta)["elegida"]


def paso(c, k):
    actual = punto_de_partida(c, k)
    nombre, valores = PASOS[k - 1]
    if valores is not None:
        variantes = [dict(actual, **{nombre: x}) for x in valores]
    else:
        base = {kk: actual[kk] for kk in ("maxdur_av", "maxdur_tr")}
        variantes = [actual] + [dict(base, tipo="delay_based", detectorRange=r, minTimeLoss=m, coordinado=False)
                                for r, m in DELAY]
        variantes += [coordinada(c, actual), coordinada(c, actual, fin_fijo=True)]   # prerregistro 5: las dos
    planes = bfn.unicos([plan_variante(c, v) for v in variantes])
    semillas = c.semillas["barrido"]
    c.asegurar(planes, semillas, f"actuado_paso{k}", c.encima())
    filas = [fila_variante(c, pl, semillas, f"paso{k}") for pl in planes]
    clave_actual = clave(actual)
    orden = sorted(range(len(planes)), key=lambda i: (filas[i]["retraso_total_prom"],
                                                      0 if planes[i]["clave"] == clave_actual else 1, i))
    elegida = planes[orden[0]]["var"]
    bfn.escribir_csv(os.path.join(c.carpeta, f"actuado_paso{k}_semillas.csv"), c.campos_corrida(),
                     [c.fila_corrida(pl["clave"], s) for pl in planes for s in semillas])
    bfn.escribir_csv(os.path.join(c.carpeta, f"actuado_paso{k}.csv"), campos_variante(c),
                     [filas[i] for i in orden])
    bfn.escribir_json(os.path.join(c.carpeta, f"actuado_paso{k}.json"),
                      {"escenario": c.esc, "huella": c.huella, "paso": k, "coordenada": nombre,
                       "semillas": bfn.texto_semillas(semillas), "partida": actual,
                       "variantes": [pl["var"] for pl in planes], "elegida": elegida, "registro": c.registro()})
    print(f"{c.esc} actuado paso {k} ({nombre}): {clave_actual} -> {clave(elegida)} "
          f"{filas[orden[0]]['retraso_total_prom']}", flush=True)
    return elegida


def final(c):
    variantes = []
    for k in range(1, len(PASOS) + 1):
        ruta = os.path.join(c.carpeta, f"actuado_paso{k}.json")
        if not os.path.exists(ruta):
            raise SystemExit(f"Falta {ruta}: corra antes los 6 pasos")
        variantes += paso_anterior(c, ruta)["variantes"]
    planes = bfn.unicos([plan_variante(c, v) for v in variantes])
    semillas = c.semillas["barrido"]
    c.asegurar(planes, semillas, "actuado_final", c.encima())
    filas = [fila_variante(c, pl, semillas, "pasos") for pl in planes]
    orden = sorted(range(len(planes)), key=lambda i: (filas[i]["retraso_total_prom"], i))
    finalistas = [planes[i] for i in orden[:FINALES[c.llegadas]]]
    semillas_f = c.semillas["desempate"]
    c.asegurar(finalistas, semillas_f, "actuado_final", c.encima())
    filas_f = [fila_variante(c, pl, semillas_f, "final") for pl in finalistas]
    orden_f = sorted(range(len(finalistas)), key=lambda i: (filas_f[i]["retraso_total_prom"], i))
    bfn.escribir_csv(os.path.join(c.carpeta, "actuado_final_semillas.csv"), c.campos_corrida(),
                     [c.fila_corrida(pl["clave"], s) for pl in finalistas for s in semillas_f])
    bfn.escribir_csv(os.path.join(c.carpeta, "actuado_final.csv"), campos_variante(c),
                     [filas_f[i] for i in orden_f] + [filas[i] for i in orden])
    g, fila = finalistas[orden_f[0]], filas_f[orden_f[0]]
    datos = {"escenario": c.esc, "llegadas": c.llegadas, "huella": c.huella, "clave": g["clave"],
             "variante": g["var"], "variantes_probadas": len(planes),
             "semillas_pasos": bfn.texto_semillas(semillas), "finalistas": [pl["clave"] for pl in finalistas],
             **{k: fila[k] for k in ("retraso_total_prom", "retraso_total_sd", "timeloss_prom", "mediana", "peor",
                                      "trabadas", "semillas")}, "registro": c.registro()}
    return instalar(c, datos)


def comentario(datos):
    return (f"Actuado ajustado (actuado.py, plan3; prerregistro, seccion 5) para {datos['escenario']}, llegadas "
            f"{datos['llegadas']}: descenso por coordenadas en cadena con {datos['semillas_pasos']} "
            f"({datos['variantes_probadas']} variantes) y las finalistas con {datos['semillas']}. Ganadora "
            f"{datos['clave']}: retraso total {datos['retraso_total_prom']} s (sd {datos['retraso_total_sd']}), "
            f"timeLoss {datos['timeloss_prom']} s.")


def instalar(c, datos):
    """<esc>_actuado_aj.add.xml desde los datos de la ganadora (y actuado_aj.json con su sha256)."""
    destino = f"{c.esc}_{PROGRAMA}.add.xml"
    bfn.escribir_atomico(destino, texto_actuado(c, datos["variante"], comentario(datos)), encoding="utf-8")
    datos = dict(datos, archivo=destino, sha256=bfn.sha256_archivo(destino))
    bfn.escribir_json(os.path.join(c.carpeta, "actuado_aj.json"), datos)
    print(f"Instalado {destino}: {datos['clave']}, retraso total {datos['retraso_total_prom']} "
          f"({datos['semillas']})", flush=True)
    return datos


def reinstalar(esc, carpeta=None):
    """Reescribe <esc>_actuado_aj.add.xml desde barridos/<esc>/actuado_aj.json (p3_preparar.py --piezas actuado_aj).
    Si el instalado ya tiene el sha256 congelado, no lo toca. Si no, escribe el texto en un temporal, compara su
    sha256 con el congelado y solo entonces reemplaza; si no coincide, error y el instalado queda como estaba (y el
    temporal se borra). Devuelve la ruta."""
    ruta = os.path.join(carpeta or os.path.join("barridos", esc), "actuado_aj.json")
    if not os.path.exists(ruta):
        raise SystemExit(f"Falta {ruta}: corra antes actuado.py {esc} --paso final")
    datos = leer_json(ruta)
    destino = f"{esc}_{PROGRAMA}.add.xml"
    if os.path.exists(destino) and bfn.sha256_archivo(destino) == datos["sha256"]:
        return destino
    c = bfn.Celda(esc, datos["llegadas"], prefijos=())
    tmp = f"{destino}.{os.getpid()}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:          # como bfn.escribir_atomico: mismos bytes
            f.write(texto_actuado(c, datos["variante"], comentario(datos)))
        if bfn.sha256_archivo(tmp) != datos["sha256"]:
            raise SystemExit(f"{destino}: el programa de hoy no coincide con el sha256 de {ruta} "
                             f"({datos['sha256'][:16]}); el archivo instalado no se toca")
        bfn.reemplazar(tmp, destino)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return destino


def main():
    ap = argparse.ArgumentParser(description="Actuado ajustado por descenso por coordenadas (plan3, 0.9)",
                                 allow_abbrev=False)
    ap.add_argument("escenario")
    ap.add_argument("--paso", choices=[str(k) for k in range(1, len(PASOS) + 1)] + ["final", "todos"])
    ap.add_argument("--instalar", action="store_true", help="reescribe el .add.xml desde actuado_aj.json")
    ap.add_argument("--procesos", type=int, default=1)
    ap.add_argument("--llegadas", choices=["auto", "regulares", "aleatorias"], default="auto",
                    help="(pruebas) auto: aleatorias si las rutas tienen period=\"exp(...)\"")
    ap.add_argument("--semillas", help="(pruebas) en vez de 2001-2003")
    ap.add_argument("--semillas-final", help="(pruebas) en vez de 2001-2010 / 2001-2030")
    ap.add_argument("--permitir-prueba", action="store_true",
                    help="(pruebas) acepta entradas que no son de la regla y marca la salida como de prueba")
    args = ap.parse_args()
    if args.instalar:
        bfn.exigir_cwd()
        print(f"Reescrito {reinstalar(args.escenario)}")
        return
    if not args.paso:
        ap.error("falta --paso (o --instalar)")
    t0 = time.time()
    c = bfn.Celda(args.escenario, args.llegadas, procesos=args.procesos,
                  semillas={"barrido": args.semillas or SEMILLAS_PASOS, "desempate": args.semillas_final},
                  prefijos=("actuado",), prueba=bfn.opciones_de_prueba(args, ("semillas", "semillas_final")),
                  permitir=args.permitir_prueba)
    print(f"actuado {c.esc}: paso {args.paso}, llegadas {c.llegadas}, semillas "
          f"{bfn.texto_semillas(c.semillas['barrido'])} y {bfn.texto_semillas(c.semillas['desempate'])}, huella "
          f"{c.huella}", flush=True)
    pasos = range(1, len(PASOS) + 1) if args.paso == "todos" else \
        ([] if args.paso == "final" else [int(args.paso)])
    for k in pasos:
        paso(c, k)
    if args.paso in ("final", "todos"):
        final(c)
    print(f"actuado {c.esc}: listo en {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
