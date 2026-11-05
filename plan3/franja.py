"""
franja.py - Fijo por franja (un plan por media hora) y fijo por bloques del perfil (plan3, tarea 0.8; DECISIONES B8
y B19; prerregistro, seccion 5).

Uso (cwd = plan3/; con llegadas aleatorias o perfil, a traves de ../con_escenarios.py):
  python franja.py <esc> [--procesos 1]
  python franja.py <esc_perfil> --bloques [--procesos 1]
  Solo para pruebas (fuera de la cola): --llegadas regulares|aleatorias, --semillas, --semillas-final y
  --permitir-prueba. Las opciones van completas (sin abreviar).
Depende de barrer_fino.py (etapas gruesa, fina y desfases, con su puntaje por periodo): la franja usa el barrido con
--bloque 1800 (el de siempre) y los bloques el barrido con --bloque 600.

Franja (prerregistro 5): los 3 mejores planes de cada media hora segun el puntaje por periodo del barrido fino
(retraso total de los vehiculos con salida programada en 0-1800 s o en 1800-3600 s; semillas del barrido), sus 9
pares, cada par con un WAUT; los 9 pares con las semillas del barrido; las 3 mejores con 2001-2010 (llegadas
aleatorias: las 10 mejores, o sea las 9, con 2001-2030); gana la menor media. Instala <esc>_franja.add.xml.
Bloques (solo el perfil; B19): el mejor plan de cada bloque de 10 min segun el puntaje por bloque, una secuencia de
hasta 6 programas con un WAUT; la secuencia se verifica con 2001-2030. Instala <esc>_bloques.add.xml.

WAUT (B8; probado en plan3/referencias/waut): un <WAUT> por semaforo, sin procedure (cambio inmediato: el plan
nuevo entra alineado con su propio desfase, como si hubiera corrido desde 0 s), con su propio instante de cambio, el
primero desde el corte (y despues del cambio anterior) que cumple, en este orden:
  estricta  los dos planes muestran el mismo estado en t-1, t y t+1 (posicion en el ciclo (t - desfase) mod ciclo):
            el cambio no se ve (la regla de siempre);
  relajada  si no hay estricta en un hiperperiodo: el paso del estado del plan viejo al del nuevo es uno que un plan
            normal haria: ningun verde pasa a rojo sin ambar, ningun ambar queda mas corto que el del plan, ningun
            rojo pasa a ambar ni ningun ambar a verde (el verde que toca el cambio puede quedar corto);
  respaldo  si tampoco: el primer fin de un ambar del plan viejo en que ningun verde pasa a rojo ni queda un ambar
            corto (los enlaces que terminaron su ambar pueden seguir en ambar o pasar a verde, y uno en rojo puede
            ver un ambar: nada de eso corta un verde);
  forzado   si ni eso (no pasa con las plantillas de P1-P6, cuyos ambares no tienen verdes): el primer fin de ambar
            del plan viejo, con los problemas anotados.
franja.json y bloques.json registran por semaforo y por cambio la regla usada, el instante nominal, el instante y el
retraso (instante - nominal), mas un aviso si alguna no fue la estricta. Programas "franja1"/"franja2" o
"bloque1".."bloqueN" (los mismos verdes y fases de la plantilla); el archivo se carga ENCIMA de los adicionales del
.sumocfg (el WAUT activa su startProg desde 0 s): asi lo hacen el barrido y el brazo franja/bloques de rl_corredor y
evaluar.py. Nunca va dentro de un .sumocfg: un entrenamiento quedaria bajo el WAUT.

Cadena: lee el barrido de barrer_fino (gruesa, fina y desfases) con sus comprobaciones de la regla; bloques lee
ademas el fijo fino (fijo_fino.json, etapa fragil) y lo pone al lado con las mismas semillas. Lo que no es de la
regla se niega, salvo con --permitir-prueba (solo pruebas; la salida queda marcada).

Salidas en barridos/<esc>/: franja.csv (los 9 pares), franja_final.csv, franja_semillas.csv y franja.json
(bloques.csv, bloques_semillas.csv y bloques.json); <esc>_franja.add.xml o <esc>_bloques.add.xml con un comentario
de la regla. Todo con temporal y reemplazo; codigo 0 solo con todo escrito.
"""
import os
import sys
import math
import time
import hashlib
import argparse
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
for _ruta in (AQUI, RAIZ):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import barrer_fijo as bf  # noqa: E402
import barrer_fino as bfn  # noqa: E402

CORTE_FRANJA = 1800
BLOQUE = 600
TOP_PERIODO = 3          # mejores planes de cada periodo
TOP_PARES = {"regulares": 3, "aleatorias": 10}


# ---------------------------------------------------------------- estados de un programa fijo
def fases_tls(p, i, verde_av, verde_tr):
    """[(duracion, estado)] del semaforo i de la plantilla con esos verdes (como barrer_fijo.escribir_programa)."""
    salida = []
    for k, fase in enumerate(f for f in p.tls[i] if f.tag == "phase"):
        estado = fase.get("state")
        if bf.es_verde(estado):
            dur = verde_av if k == p.fases_av[i] else verde_tr
        else:
            dur = int(float(fase.get("duration")))
        salida.append((int(dur), estado))
    return salida


def estado_en(fases, ciclo, desfase, t):
    """Estado del programa en el segundo t: la fase en la posicion (t - desfase) mod ciclo."""
    x = (t - desfase) % ciclo
    for dur, estado in fases:
        if x < dur:
            return estado
        x -= dur
    raise AssertionError("ciclo mal calculado")


REGLAS_CAMBIO = ("estricta", "relajada", "respaldo", "forzado")
SE_TOLERA_EN_RESPALDO = ("ambar_tras_rojo", "verde_tras_ambar")


def racha_ambar(prog, x, i, paso):
    """Segundos seguidos en que el enlace i del programa prog (fases, ciclo, desfase) muestra ambar, desde x hacia
    adelante (paso 1) o hacia atras (paso -1), contando x; 0 si en x no hay ambar."""
    n = 0
    while n < prog[1] and estado_en(*prog, x + paso * n)[i] == "y":
        n += 1
    return n


def ambar_del_plan(prog):
    """El ambar mas corto del programa (3 s en todas las plantillas)."""
    return min((d for d, e in prog[0] if "y" in e), default=0)


def problemas_del_cambio(a, b, t):
    """Lo que se veria si el semaforo pasa del programa a al b en t (se ve a hasta t-1 y b desde t; ver
    instante_limpio): [(enlace, problema)]. verde_a_rojo: un verde pasa a rojo sin ambar; ambar_corto: un ambar que
    viene de un verde dura menos que el ambar del plan; ambar_tras_rojo: un rojo pasa a ambar; verde_tras_ambar: un
    ambar pasa a verde. Lejos del cambio cada plan sigue su propia secuencia, que no tiene ninguno de los cuatro."""
    viejo, nuevo = estado_en(*a, t - 1), estado_en(*b, t)
    ambar = min(ambar_del_plan(a), ambar_del_plan(b))
    salida = []
    for i, (x, y) in enumerate(zip(viejo, nuevo)):
        if x in "Gg" and y == "r":
            salida.append((i, "verde_a_rojo"))
        elif x in "Gg" and y == "y" and racha_ambar(b, t, i, 1) < ambar:
            salida.append((i, "ambar_corto"))
        elif x == "y" and y == "r" and racha_ambar(a, t - 1, i, -1) < ambar:
            salida.append((i, "ambar_corto"))
        elif x == "y" and y == "y" and racha_ambar(a, t - 1, i, -1) + racha_ambar(b, t, i, 1) < ambar:
            salida.append((i, "ambar_corto"))
        elif x == "r" and y == "y":
            salida.append((i, "ambar_tras_rojo"))
        elif x == "y" and y in "Gg":
            salida.append((i, "verde_tras_ambar"))
    return salida


def fin_de_ambar(a, t):
    """True si en t-1 termina un ambar del programa a (en t ya esta en la fase siguiente)."""
    antes = estado_en(*a, t - 1)
    return "y" in antes and estado_en(*a, t) != antes


def instante_limpio(a, b, desde):
    """(t, regla, problemas) del cambio del programa a al b (fases, ciclo, desfase) desde t >= desde. Con el WAUT en
    t, el semaforo muestra a hasta la posicion t-1 y b desde t (estado_en; SUMO lo ve un segundo despues). Reglas, en
    orden (docstring del modulo): estricta (el mismo estado en t-1, t y t+1), relajada (problemas_del_cambio vacio),
    respaldo (fin de un ambar de a sin verde_a_rojo ni ambar_corto) y forzado (el primer fin de ambar de a). Las tres
    primeras se buscan en un hiperperiodo; nunca termina el proceso."""
    hasta = desde + math.lcm(a[1], b[1]) + max(a[1], b[1])
    for t in range(desde, hasta + 1):
        if all(estado_en(*a, x) == estado_en(*b, x) for x in (t - 1, t, t + 1)):
            return t, "estricta", []
    for t in range(desde, hasta + 1):
        if not problemas_del_cambio(a, b, t):
            return t, "relajada", []
    for t in range(desde, hasta + 1):
        if fin_de_ambar(a, t):
            problemas = problemas_del_cambio(a, b, t)
            if all(p in SE_TOLERA_EN_RESPALDO for _, p in problemas):
                return t, "respaldo", problemas
    t = next((x for x in range(desde, desde + a[1] + 1) if fin_de_ambar(a, x)), desde)
    return t, "forzado", problemas_del_cambio(a, b, t)


def programa_tls(p, pl, i):
    return (fases_tls(p, i, pl["verde"], pl["verde_transversal"]), pl["ciclo"], pl["offsets"][i])


def detalle_cambios(p, secuencia, i):
    """Cambios del semaforo i para una secuencia [(t nominal, plan)] (el primero desde 0 s): por cada plan nuevo,
    {"nominal", "instante", "retraso", "regla", "problemas"}; cada instante se busca desde su t nominal y despues del
    cambio anterior."""
    salida, anterior, t_prev = [], secuencia[0][1], 0
    for t_nom, pl in secuencia[1:]:
        t, regla, problemas = instante_limpio(programa_tls(p, anterior, i), programa_tls(p, pl, i),
                                              max(t_nom, t_prev + 1))
        salida.append({"nominal": t_nom, "instante": t, "retraso": t - t_nom, "regla": regla,
                       "problemas": [f"enlace {k}: {q}" for k, q in problemas]})
        anterior, t_prev = pl, t
    return salida


def cambios_tls(p, secuencia, i):
    """Instantes de cambio del semaforo i para una secuencia [(t nominal, plan)] (detalle_cambios)."""
    return [d["instante"] for d in detalle_cambios(p, secuencia, i)]


def resumen_cambios(p, secuencia):
    """{"por_semaforo": {tls: [detalle]}, "reglas": {regla: cuantos}, "aviso": texto o None} de una secuencia."""
    por_tls = {tls: detalle_cambios(p, secuencia, i) for i, tls in enumerate(p.ids)} if len(secuencia) > 1 else \
        {tls: [] for tls in p.ids}
    cuenta = {r: sum(1 for lista in por_tls.values() for d in lista if d["regla"] == r) for r in REGLAS_CAMBIO}
    otras = {r: n for r, n in cuenta.items() if n and r != "estricta"}
    aviso = None
    if otras:
        aviso = (f"cambios sin instante estricto: {otras} (ver por_semaforo; la regla relajada no corta verdes ni "
                 f"ambares; el respaldo puede dejar un ambar tras un rojo o un verde tras un ambar)")
    return {"por_semaforo": por_tls, "reglas": cuenta, "retraso_maximo": max(
        (d["retraso"] for lista in por_tls.values() for d in lista), default=0), "aviso": aviso}


def texto_waut(p, secuencia, prefijo_pid, wid, comentario=None):
    """Texto del .add.xml: un programa por plan de la secuencia (programID <prefijo><k>, k desde 1) y un WAUT por
    semaforo con sus instantes limpios. Devuelve (texto, {tls: [instantes]})."""
    lineas = ["<additional>"]
    if comentario:
        import textwrap
        texto = comentario.replace("--", "- -")              # un comentario XML no puede llevar "--"
        lineas.append("    <!-- " + "\n         ".join(textwrap.wrap(texto, 96)) + " -->")
    for k, (_, pl) in enumerate(secuencia, start=1):
        for i, tl in enumerate(p.tls):        # como barrer_fijo.escribir_programa, con otro programID
            a = dict(tl.attrib)
            a.update(type="static", programID=f"{prefijo_pid}{k}", offset=pl["offsets"][i])
            lineas.append(f"    <tlLogic {bf.atributos(a)}>")
            fases = iter(fases_tls(p, i, pl["verde"], pl["verde_transversal"]))
            for hijo in tl:
                if hijo.tag != "phase":
                    lineas.append("        " + ET.tostring(hijo, encoding="unicode").strip())
                    continue
                f = dict(hijo.attrib)
                f["duration"] = next(fases)[0]
                lineas.append(f"        <phase {bf.atributos(f)}/>")
            lineas.append("    </tlLogic>")
    instantes = {}
    if len(secuencia) == 1:             # un solo plan: sin WAUT (el ultimo programa cargado queda activo)
        lineas.append("</additional>")
        return "\n".join(lineas) + "\n", {tls: [] for tls in p.ids}
    for i, tls in enumerate(p.ids):
        instantes[tls] = cambios_tls(p, secuencia, i)
        lineas.append(f'    <WAUT refTime="0" id="{wid}_{tls}" startProg="{prefijo_pid}1">')
        for k, t in enumerate(instantes[tls], start=2):
            lineas.append(f'        <wautSwitch time="{t}" to="{prefijo_pid}{k}"/>')
        lineas.append("    </WAUT>")
        lineas.append(f'    <wautJunction wautID="{wid}_{tls}" junctionID="{tls}"/>')
    lineas.append("</additional>")
    return "\n".join(lineas) + "\n", instantes


def secuencia_sin_repetir(planes, cortes):
    """[(t nominal, plan)] con el plan de cada periodo; un periodo con el mismo plan que el anterior no cambia."""
    secuencia = [(0, planes[0])]
    for t, pl in zip(cortes, planes[1:]):
        if pl["clave"] != secuencia[-1][1]["clave"]:
            secuencia.append((t, pl))
    return secuencia


def plan_waut(c, secuencia, prefijo_pid, wid, clave):
    """Plan (para Celda.asegurar) que escribe el WAUT de la secuencia y se carga encima de los adicionales."""
    def escribir(ruta):
        texto, _ = texto_waut(c.p, secuencia, prefijo_pid, wid)
        bfn.escribir_atomico(ruta, texto, encoding="utf-8")
    return {"clave": clave, "escribir": escribir, "secuencia": secuencia}


def fila_secuencia(c, pl, semillas, etapa):
    fila = {"etapa": etapa, "clave": pl["clave"],
            "programas": " | ".join(f"{t}:{q['clave']}{'_' + q['esquema'] if q['esquema'] else ''}"
                                    for t, q in pl["secuencia"])}
    fila.update(c.metricas(pl["clave"], semillas))
    return fila


def campos_secuencia(c):
    return ["etapa", "clave", "programas"] + c.campos_metricas()


def ordenar(filas):
    return sorted(range(len(filas)), key=lambda i: filas[i]["retraso_total_prom"])


# ---------------------------------------------------------------- franja
def franja(c):
    planes = bfn.planes_barrido(c)
    semillas = c.semillas["barrido"]
    c.asegurar(planes, semillas, "franja")              # normalmente ya estan todas (barrer_fino)
    filas = [c.fila(pl, semillas, "barrido") for pl in planes]
    mejores = []
    for k in (1, 2):
        orden = sorted(range(len(planes)), key=lambda i: filas[i][f"total_p{k}"])
        mejores.append([planes[i] for i in orden[:TOP_PERIODO]])
        print(f"{c.esc} periodo {k}: " + "; ".join(f"{planes[i]['clave']} {filas[i][f'total_p{k}']}"
                                                   for i in orden[:TOP_PERIODO]), flush=True)
    pares = []
    for p1 in mejores[0]:
        for p2 in mejores[1]:            # siempre dos programas y un cambio, aunque el plan sea el mismo
            secuencia = [(0, p1), (CORTE_FRANJA, p2)]
            pares.append(plan_waut(c, secuencia, "franja", "franja", f"fr_{p1['clave']}__{p2['clave']}"))
    c.asegurar(pares, semillas, "franja", c.encima())
    filas_p = [fila_secuencia(c, pl, semillas, "pares") for pl in pares]
    orden = ordenar(filas_p)
    finalistas = [pares[i] for i in orden[:TOP_PARES[c.llegadas]]]
    final = c.semillas["desempate"]
    c.asegurar(finalistas, final, "franja", c.encima())
    filas_f = [fila_secuencia(c, pl, final, "final") for pl in finalistas]
    orden_f = ordenar(filas_f)
    ganador, fila_g = finalistas[orden_f[0]], filas_f[orden_f[0]]
    bfn.escribir_csv(os.path.join(c.carpeta, "franja.csv"), campos_secuencia(c), [filas_p[i] for i in orden])
    bfn.escribir_csv(os.path.join(c.carpeta, "franja_final.csv"), campos_secuencia(c),
                     [filas_f[i] for i in orden_f])
    bfn.escribir_csv(os.path.join(c.carpeta, "franja_semillas.csv"), c.campos_corrida(),
                     [c.fila_corrida(pl["clave"], s) for pl in pares for s in semillas] +
                     [c.fila_corrida(pl["clave"], s) for pl in finalistas for s in final if s not in semillas])
    texto = (f"Fijo por franja (franja.py, plan3; prerregistro, seccion 5) para {c.esc}, llegadas {c.llegadas}: "
             f"los 3 mejores planes de cada media hora segun el puntaje por periodo de barrer_fino "
             f"({bfn.texto_semillas(semillas)}), 9 pares con WAUT por semaforo en su instante limpio; las "
             f"{TOP_PARES[c.llegadas]} mejores con {bfn.texto_semillas(final)}. Ganador: {fila_g['programas']}; "
             f"retraso total {fila_g['retraso_total_prom']} s (sd {fila_g['retraso_total_sd']}), timeLoss "
             f"{fila_g['timeloss_prom']} s sobre {fila_g['semillas']}.")
    return instalar(c, ganador, fila_g, "franja", "franja", texto)


# ---------------------------------------------------------------- bloques del perfil
def bloques(c):
    planes = bfn.planes_barrido(c)
    semillas = c.semillas["barrido"]
    c.asegurar(planes, semillas, "bloques")
    filas = [c.fila(pl, semillas, "barrido") for pl in planes]
    elegidos = []
    for k in range(1, c.k + 1):
        i = min(range(len(planes)), key=lambda j: (filas[j][f"total_p{k}"], j))
        elegidos.append(planes[i])
        print(f"{c.esc} bloque {k}: {planes[i]['clave']} {planes[i]['esquema']} {filas[i][f'total_p{k}']}",
              flush=True)
    secuencia = secuencia_sin_repetir(elegidos, c.cortes)
    clave = "bl_" + hashlib.sha256("|".join(f"{t}:{q['clave']}" for t, q in secuencia).encode()).hexdigest()[:12]
    pl = plan_waut(c, secuencia, "bloque", "bloques", clave)
    final = c.semillas["fragil"]
    c.asegurar([pl], final, "bloques", c.encima())
    fila = fila_secuencia(c, pl, final, "verificacion")
    bfn.escribir_csv(os.path.join(c.carpeta, "bloques.csv"), campos_secuencia(c), [fila])
    bfn.escribir_csv(os.path.join(c.carpeta, "bloques_semillas.csv"), c.campos_corrida(),
                     [c.fila_corrida(pl["clave"], s) for s in final])
    texto = (f"Fijo por bloques de {BLOQUE} s (franja.py --bloques, plan3; prerregistro, seccion 5) para {c.esc}, "
             f"llegadas {c.llegadas}: el mejor plan de cada bloque segun el puntaje por bloque de barrer_fino "
             f"({bfn.texto_semillas(semillas)}), WAUT por semaforo en su instante limpio; secuencia verificada "
             f"con {bfn.texto_semillas(final)}: {fila['programas']}; retraso total {fila['retraso_total_prom']} s "
             f"(sd {fila['retraso_total_sd']}), timeLoss {fila['timeloss_prom']} s.")
    extra = {}
    ruta_fino = os.path.join(c.carpeta, "fijo_fino.json")
    if os.path.exists(ruta_fino):              # al lado: el fijo fino con las mismas semillas de la verificacion
        fino = c.comprobar_marca(ruta_fino)
        pl_fino = c.plan(fino["verde"], fino["verde_transversal"], fino["offsets"], fino["esquema"])
        if pl_fino["clave"] != fino["clave"]:
            raise SystemExit(f"{ruta_fino}: la clave {fino['clave']} no sale de sus verdes y desfases")
        c.asegurar([pl_fino], final, "bloques")         # normalmente ya estan (desempate o fragil)
        extra["fijo_fino_mismas_semillas"] = c.metricas(fino["clave"], final)["retraso_total_prom"]
    else:
        c.fuera_de_regla(ruta_fino, ["falta: bloques va despues de la etapa fragil (pone al lado el fijo fino)"])
    return instalar(c, pl, fila, "bloques", "bloques", texto, extra)


def instalar(c, pl, fila, sufijo, nombre_json, comentario, extra=None):
    destino = f"{c.esc}_{sufijo}.add.xml"
    prefijo, wid = ("franja", "franja") if sufijo == "franja" else ("bloque", "bloques")
    cambios = resumen_cambios(c.p, pl["secuencia"])
    if cambios["aviso"]:                       # (con todos los cambios estrictos el comentario es el de siempre)
        comentario += f" Aviso: {cambios['aviso']}."
    texto, instantes = texto_waut(c.p, pl["secuencia"], prefijo, wid, comentario)
    bfn.escribir_atomico(destino, texto, encoding="utf-8")
    datos = {"escenario": c.esc, "llegadas": c.llegadas, "archivo": destino, "sha256": bfn.sha256_archivo(destino),
             "huella": c.huella, "clave": pl["clave"],
             "programas": [{"desde": t, "programID": f"{prefijo}{k}", "verde": q["verde"],
                            "verde_transversal": q["verde_transversal"], "offsets": q["offsets"],
                            "esquema": q["esquema"], "ciclo": q["ciclo"], "clave": q["clave"]}
                           for k, (t, q) in enumerate(pl["secuencia"], start=1)],
             "instantes": instantes, "cambios": cambios,
             **{k: fila[k] for k in ("retraso_total_prom", "retraso_total_sd", "timeloss_prom", "mediana", "peor",
                                      "trabadas", "semillas")}, **(extra or {}), "registro": c.registro()}
    bfn.escribir_json(os.path.join(c.carpeta, f"{nombre_json}.json"), datos)
    print(f"Instalado {destino}: {fila['programas']}; retraso total {fila['retraso_total_prom']} "
          f"({fila['semillas']}); cambios {instantes}; reglas {cambios['reglas']}", flush=True)
    if cambios["aviso"]:
        print(f"AVISO: {cambios['aviso']}", flush=True)
    return datos


def main():
    ap = argparse.ArgumentParser(description="Fijo por franja y por bloques con WAUT (plan3, 0.8)", allow_abbrev=False)
    ap.add_argument("escenario")
    ap.add_argument("--bloques", action="store_true", help="perfil: un plan por bloque de 600 s")
    ap.add_argument("--procesos", type=int, default=1)
    ap.add_argument("--llegadas", choices=["auto", "regulares", "aleatorias"], default="auto",
                    help="(pruebas) auto: aleatorias si las rutas tienen period=\"exp(...)\"")
    ap.add_argument("--semillas", help="(pruebas) semillas del barrido")
    ap.add_argument("--semillas-final", help="(pruebas) en vez de 2001-2010 / 2001-2030")
    ap.add_argument("--permitir-prueba", action="store_true",
                    help="(pruebas) acepta entradas que no son de la regla y marca la salida como de prueba")
    args = ap.parse_args()
    t0 = time.time()
    bloque = BLOQUE if args.bloques else CORTE_FRANJA
    semillas = {"barrido": args.semillas,
                ("fragil" if args.bloques else "desempate"): args.semillas_final}
    c = bfn.Celda(args.escenario, args.llegadas, bloque, args.procesos, semillas,
                  prefijos=bfn.ETAPAS + ("franja", "bloques"),
                  prueba=bfn.opciones_de_prueba(args, ("semillas", "semillas_final")), permitir=args.permitir_prueba)
    print(f"franja {c.esc}: {'bloques de 600 s' if args.bloques else 'dos medias horas'}, llegadas {c.llegadas}, "
          f"huella {c.huella}, {len(c.conocidas)} corridas guardadas"
          + (f"; PRUEBA: {c.prueba}" if c.prueba else ""), flush=True)
    if args.bloques:
        bloques(c)
    else:
        franja(c)
    print(f"franja {c.esc}: listo en {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
