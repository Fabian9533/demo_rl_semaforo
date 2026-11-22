"""
estudio.py - Caso Lima: ajusta las referencias, evalua todos los controles y calcula el veredicto.

Uso (desde demo_rl/lima, con lima.net.xml, lima.rou.xml, lima.sumocfg y lima.add.xml ya escritos):
  python estudio.py ajustar-fijo      [--procesos 10]   # fijo ajustado al segundo -> lima_fijo.add.xml
  python estudio.py ajustar-actuado   [--procesos 10]   # actuado y actuado ajustado -> lima_actuado*.add.xml
  python estudio.py evaluar --tanda 1 [--politicas a.pt,b.pt] [--procesos 10]
  python estudio.py validar-referencias                 # las referencias en las semillas de validacion (figura)
  python estudio.py verdes-modelo --politicas a.pt      # verde medio que da el modelo a cada estado (figura)
  python estudio.py veredicto --modelo <brazo>          # tabla y etiqueta, tanda por tanda

Controles (todos con los mismos estados del semaforo, en el mismo orden; ver programa.py):
  actual     el plan que opera hoy en el nudo, medido en el sitio (lima.add.xml)
  fijo       fijo ajustado al segundo: los verdes que dan menos retraso total medio con la demanda del caso
  actuado    control actuado de SUMO con verdes de 10 a 60 s (5 s en los estados de solo giro)
  actuadoaj  actuado ajustado: el mejor de una rejilla de parametros del actuado
  minimo     ciclo minimo: cada verde en su minimo
  <politica> el modelo entrenado (rl_ippo.py), con la politica congelada

Semillas (ninguna se repite entre usos; no tocan los bloques ciegos del segundo estudio):
  ajuste de las referencias    2001-2010 por candidato y 2001-2030 para los diez mejores (como en el segundo estudio)
  entrenamiento                bases 42, 2042 y 4042 (episodio k = base + k)
  validacion del modelo        21001-21008
  evaluacion                   tanda 1 = 22001-22100; tanda 2 = 23001-23100

Metrica: retraso total por vehiculo (comun.leer_tripinfo, retraso_total_prom), como en el segundo estudio.
Estadistica y regla de veredicto: las de la tesis (evaluar.bootstrap_delta, Wilcoxon pareado y veredicto.veredicto).
"""
import argparse
import csv
import itertools
import json
import os
import statistics
import sys
from multiprocessing import Pool

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)

# carpeta de los datos y las salidas de un nivel de demanda: por defecto, la de los programas (demanda publicada);
# la variable de entorno LIMA_CARPETA la cambia (alta/ = demanda alta). La red y los programas son los mismos.
CARPETA = os.path.normpath(os.path.join(AQUI, os.environ.get("LIMA_CARPETA", "")))   # relativa a los programas
CFG = "lima.sumocfg"
TMP = os.path.join(CARPETA, "tmp")
SALIDAS = os.path.join(CARPETA, "salidas")
AJUSTE = list(range(2001, 2011))
DESEMPATE = list(range(2001, 2031))
VALIDACION = list(range(21001, 21009))
TANDAS = {1: list(range(22001, 22101)), 2: list(range(23001, 23101))}
VERDE_MAX = 60                 # verde maximo del actuado (y del modelo, en rl_ippo.py)
VERDE_MAX_FIJO = 120           # tope de busqueda del fijo: holgado, para que el ganador no quede en el borde
FINALISTAS = 10
ARCHIVO = {"actual": "lima.add.xml", "fijo": "lima_fijo.add.xml", "actuado": "lima_actuado.add.xml",
           "actuadoaj": "lima_actuadoaj.add.xml", "minimo": "lima_minimo.add.xml",
           # el actuado ajustado de la rejilla anterior, de 12 combinaciones (REGISTRO.md, enmienda del 14.11.2026)
           "actuadoaj12": "lima_actuadoaj12.add.xml",
           # el de antes de la comprobacion del borde, si esta lo cambia (REGISTRO.md, 14.11.2026, 15:55)
           "actuadoajb": "lima_actuadoajb.add.xml"}
METRICA = "retraso_total_prom"


# ---------------- una corrida ----------------
def _fija(tarea):
    """Una corrida de sumo puro con el programa de un archivo. tarea = (archivo .add.xml, semilla, marca)."""
    import barrer_fijo
    archivo, semilla, marca = tarea
    tripinfo = os.path.join(TMP, f"trip_{marca}_{os.getpid()}_{semilla}.xml")
    res = barrer_fijo.correr_sumo(CFG, ["--additional-files", archivo], semilla, tripinfo)
    _borrar(tripinfo)
    return res


def _modelo(tarea):
    """Una corrida con una politica entrenada (argmax). tarea = (ruta .pt, semilla, marca)."""
    import torch
    import rl_ippo
    torch.set_num_threads(1)
    ruta, semilla, marca = tarea
    if _modelo.cargada != ruta:
        rl_ippo.preparar("lima")
        politica, meta = rl_ippo.Politica.cargar(ruta)
        rl_ippo.configurar_desde_meta(meta)
        _modelo.cargada, _modelo.politica, _modelo.meta = ruta, politica, meta
    tripinfo = os.path.join(TMP, f"trip_{marca}_{os.getpid()}_{semilla}.xml")
    res = rl_ippo.correr_episodio("demo", _modelo.politica, False, 0, semilla, tripinfo=tripinfo,
                                  variante=_modelo.meta.get("variante", "vecinos"))
    _borrar(tripinfo)
    return res


_modelo.cargada = None


def _borrar(tripinfo):
    import comun
    for ruta in (tripinfo, comun.ruta_estadisticas(tripinfo)):
        try:
            os.remove(ruta)
        except OSError:
            pass


def media(resultados):
    return statistics.mean(r[METRICA] for r in resultados)


# ---------------- fijo ajustado al segundo ----------------
def ajustar_fijo(args):
    import programa
    minimos = programa.minimos()
    actual = [v for _, v, _ in programa.PLAN]
    n = len(actual)
    cache = {}

    def puntaje(verdes, pool, semillas=AJUSTE):
        clave = (tuple(verdes), len(semillas))
        if clave not in cache:
            archivo = os.path.join(TMP, "fijo_" + "_".join(str(v) for v in verdes) + ".add.xml")
            programa.escribir(archivo, list(verdes))
            res = pool.map(_fija, [(archivo, s, "aj") for s in semillas])
            cache[clave] = (media(res), [r[METRICA] for r in res])
            os.remove(archivo)
            print(f"  verdes {list(verdes)} ciclo {sum(verdes) + programa.tiempo_fijo():3d} s, {len(semillas)} semillas: "
                  f"{cache[clave][0]:8.2f} s/veh", flush=True)
        return cache[clave][0]

    def limitar(k, v):
        return max(minimos[k], min(VERDE_MAX_FIJO, v))

    with Pool(args.procesos) as pool:
        # puntos de partida: el plan actual (recortado a los limites), todo en minimos y repartos parejos
        partidas = [[limitar(k, v) for k, v in enumerate(actual)], list(minimos)]
        partidas += [[limitar(k, g) for k in range(n)] for g in (20, 30, 45)]
        mejor = min(partidas, key=lambda v: puntaje(v, pool))
        for paso in (8, 4, 2, 1):                       # descenso por coordenadas, afinando hasta 1 s
            mejoro = True
            while mejoro:
                mejoro = False
                for k in range(n):
                    for signo in (-1, 1):
                        candidato = list(mejor)
                        candidato[k] = limitar(k, candidato[k] + signo * paso)
                        if candidato != mejor and puntaje(candidato, pool) < puntaje(mejor, pool):
                            mejor, mejoro = candidato, True
            print(f"paso {paso} s: mejor {mejor} = {puntaje(mejor, pool):.2f}", flush=True)
        # desempate: los diez mejores con 30 semillas
        orden = sorted((v for (v, k) in cache if k == len(AJUSTE)), key=lambda v: cache[(v, len(AJUSTE))][0])
        finalistas = orden[:FINALISTAS]
        ganador = min(finalistas, key=lambda v: puntaje(list(v), pool, DESEMPATE))
    programa.escribir(os.path.join(CARPETA, ARCHIVO["fijo"]), list(ganador), programa="fijo_ajustado",
                      comentario=f"Fijo ajustado al segundo del caso Lima (estudio.py ajustar-fijo): verdes {list(ganador)}")
    programa.escribir(os.path.join(CARPETA, ARCHIVO["minimo"]), list(minimos), programa="minimo",
                      comentario="Ciclo minimo del caso Lima: cada verde en su minimo")
    registro = {"ganador": list(ganador), "retraso_total_30": cache[(ganador, len(DESEMPATE))][0],
                "minimos": minimos, "plan_actual": actual, "transicion": programa.TRANSICION,
                "rojo_total": programa.ROJO_TOTAL, "tiempo_fijo": programa.tiempo_fijo(),
                "semillas_ajuste": [AJUSTE[0], AJUSTE[-1]], "semillas_desempate": [DESEMPATE[0], DESEMPATE[-1]],
                "candidatos": [{"verdes": list(v), "semillas": k, "retraso_total": round(m, 4)}
                               for (v, k), (m, _) in sorted(cache.items(), key=lambda kv: kv[1][0])]}
    os.makedirs(SALIDAS, exist_ok=True)
    with open(os.path.join(SALIDAS, "fijo_ajustado.json"), "w", encoding="utf-8") as f:
        json.dump(registro, f, indent=1)
    print(f"Fijo ajustado: verdes {list(ganador)} (ciclo {sum(ganador) + programa.tiempo_fijo()} s), "
          f"{registro['retraso_total_30']:.2f} s/veh con 30 semillas; {len(cache)} evaluaciones")
    en_tope = [programa.PLAN[k][0] for k, v in enumerate(ganador) if v >= VERDE_MAX_FIJO]
    if en_tope:
        print(f"AVISO: el ganador toca el tope de {VERDE_MAX_FIJO} s en {en_tope}: subir VERDE_MAX_FIJO y repetir")


# ---------------- actuado y actuado ajustado ----------------
# El actuado ajustado se busca con los pasos del segundo estudio (plan3/actuado.py), sin sus dos variantes
# coordinadas (REGISTRO.md, enmienda del 14.11.2026). Lo usa tambien corredor/estudio_corredor.py.
DEFECTO_ACTUADO = {"tipo": "actuado", "max-gap": 3.0, "detector-gap": 2.0, "jam-threshold": -1}    # los de SUMO
# estudio 2 del corredor (19.11.2026): se agregan los huecos de 0.75 y 1.25 s (revision del corredor)
PASOS_ACTUADO = (("max-gap", (0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0)), ("detector-gap", (1.0, 2.0, 3.0, 4.0)),
                 ("jam-threshold", (-1, 10, 30)))
RETRASO = [(alcance, minimo) for alcance in (50, 100, 200) for minimo in (1, 3)]     # detectorRange (m), minTimeloss (s)
FINALISTAS_ACTUADO = 3
PROCEDIMIENTO_ACTUADO = ("pasos del segundo estudio en cadena (hueco, detector, umbral de atasco y verde maximo), "
                         "variante por retraso y los tres mejores con 30 semillas")


def parametros_sumo(v):
    """{clave: valor} de los <param> de una variante: del actuado, los que difieren del defecto de SUMO; de la
    variante por retraso, los suyos (SUMO 1.25 lee la clave "minTimeloss", no "minTimeLoss")."""
    if v["tipo"] == "retraso":
        return {"detectorRange": v["detectorRange"], "minTimeloss": v["minTimeLoss"]}
    return {k: v[k] for k in ("max-gap", "detector-gap", "jam-threshold") if v[k] != DEFECTO_ACTUADO[k]}


def texto_variante(v):
    if v["tipo"] == "retraso":
        return f"por retraso, alcance {v['detectorRange']} m, retraso minimo {v['minTimeLoss']} s, maximos {v['esquema']}"
    coordinado = {None: "", "avenida": ", coordinado con el fijo", "fin fijo": ", coordinado con el fijo y fin fijo"}
    return (f"hueco {v['max-gap']} s, detector {v['detector-gap']} s, umbral de atasco {v['jam-threshold']}, "
            f"maximos {v['esquema']}{coordinado[v.get('coordinado')]}")


def buscar_actuado(escribir_variante, esquemas, pool, correr, tmp, coordinadas=False):
    """Busca el actuado ajustado. Descenso por coordenadas en cadena: un paso por parametro, cada paso parte del
    mejor de los anteriores y en un empate se queda el punto de partida; despues, la variante por retraso con el
    esquema de verde maximo elegido. Cada variante se mide con las semillas de ajuste y las tres mejores, con las
    de desempate. escribir_variante(archivo, variante) escribe su .add.xml; esquemas: nombres de los esquemas de
    verde maximo (el primero es el de partida); correr: la funcion de una corrida. coordinadas (solo donde hay varios
    cruces sobre una avenida): se prueban ademas las dos variantes coordinadas del segundo estudio sobre el mejor
    actuado de la cadena (REGISTRO.md, 14.11.2026, 05:40). Devuelve (ganador, variantes probadas en orden de
    retraso, retraso del actuado por defecto con las semillas de desempate)."""
    probadas = {}

    def medir(v, semillas=AJUSTE, campo="retraso_total_10"):
        reg = probadas.setdefault(json.dumps(v, sort_keys=True), dict(v))
        if campo not in reg:
            archivo = os.path.join(tmp, f"actuado_{os.getpid()}_{len(probadas)}.add.xml")
            escribir_variante(archivo, v)
            reg[campo] = media(pool.map(correr, [(archivo, s, "ac") for s in semillas]))
            os.remove(archivo)
            print(f"  {texto_variante(v)}, {len(semillas)} semillas: {reg[campo]:8.2f} s/veh", flush=True)
        return reg[campo]

    partida = dict(DEFECTO_ACTUADO, esquema=esquemas[0])
    actual = partida
    for parametro, valores in list(PASOS_ACTUADO) + [("esquema", tuple(esquemas))]:
        for valor in valores:
            candidato = dict(actual, **{parametro: valor})
            if medir(candidato) < medir(actual):
                actual = candidato
        print(f"paso {parametro}: {texto_variante(actual)} = {medir(actual):.2f}", flush=True)
    for alcance, minimo in RETRASO:
        medir({"tipo": "retraso", "detectorRange": alcance, "minTimeLoss": minimo, "esquema": actual["esquema"]})
    if coordinadas:
        for modo in ("avenida", "fin fijo"):
            medir(dict(actual, coordinado=modo))
    orden = sorted(probadas.values(), key=lambda r: r["retraso_total_10"])
    finalistas = orden[:FINALISTAS_ACTUADO]
    for r in finalistas:
        medir({k: x for k, x in r.items() if not k.startswith("retraso_total")}, DESEMPATE, "retraso_total_30")
    por_defecto = medir(partida, DESEMPATE, "retraso_total_30")
    return min(finalistas, key=lambda r: r["retraso_total_30"]), orden, por_defecto


def ajustar_actuado(args):
    import programa
    n = len(programa.PLAN)
    with open(os.path.join(SALIDAS, "fijo_ajustado.json"), encoding="utf-8") as f:
        fijo = json.load(f)["ganador"]
    # actuado: los parametros por defecto de SUMO y verdes de 10 a 60 s
    programa.escribir(os.path.join(CARPETA, ARCHIVO["actuado"]), [VERDE_MAX] * n, tipo="actuado",
                      comentario="Actuado del caso Lima: control actuado de SUMO, verde maximo 60 s en cada estado")
    maximos = {"60": [VERDE_MAX] * n,
               "doble del fijo": [min(VERDE_MAX, max(m, 2 * g)) for m, g in zip(programa.minimos(), fijo)]}

    def escribir_variante(archivo, v, **extra):
        programa.escribir(archivo, maximos[v["esquema"]], tipo=v["tipo"], parametros=parametros_sumo(v), **extra)

    with Pool(args.procesos) as pool:
        gan, orden, por_defecto = buscar_actuado(escribir_variante, list(maximos), pool, _fija, TMP)
    escribir_variante(os.path.join(CARPETA, ARCHIVO["actuadoaj"]), gan, programa="actuado_ajustado",
                      comentario=f"Actuado ajustado del caso Lima (estudio.py ajustar-actuado): {texto_variante(gan)}")
    with open(os.path.join(SALIDAS, "actuado_ajustado.json"), "w", encoding="utf-8") as f:
        json.dump({"ganador": dict(gan, maximos=maximos[gan["esquema"]]), "actuado_por_defecto_30": por_defecto,
                   "procedimiento": PROCEDIMIENTO_ACTUADO, "candidatos": orden}, f, indent=1)
    print(f"Actuado ajustado: {texto_variante(gan)}, {gan['retraso_total_30']:.2f} s/veh con 30 semillas; "
          f"actuado por defecto {por_defecto:.2f}; {len(orden)} variantes")


# ---------------- evaluacion ----------------
def evaluar(args):
    semillas = TANDAS[args.tanda] if not args.semillas else [int(s) for s in args.semillas.split(",")]
    brazos = [(b, os.path.join(CARPETA, a), _fija) for b, a in ARCHIVO.items() if os.path.exists(os.path.join(CARPETA, a))
              and (not args.brazos or b in args.brazos.split(","))]
    for ruta in [p for p in (args.politicas or "").split(",") if p]:
        nombre = os.path.splitext(os.path.basename(ruta))[0].replace("politica_lima_vecinos_", "")
        brazos.append((nombre, ruta, _modelo))
    os.makedirs(SALIDAS, exist_ok=True)
    with Pool(args.procesos) as pool:
        for nombre, ruta, funcion in brazos:
            destino = os.path.join(SALIDAS, f"eval_t{args.tanda}_{nombre}.csv")
            if os.path.exists(destino) and not args.rehacer:
                print(f"{nombre}: ya esta ({destino})")
                continue
            res = pool.map(funcion, [(ruta, s, nombre) for s in semillas], chunksize=1)
            campos = ["brazo", "semilla"] + [k for k in res[0] if k not in ("brazo", "semilla")]
            with open(destino + ".tmp", "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
                w.writeheader()
                for s, r in zip(semillas, res):
                    w.writerow({"brazo": nombre, "semilla": s, **r})
            os.replace(destino + ".tmp", destino)
            print(f"{nombre}: {media(res):8.2f} s/veh de retraso total en {len(res)} semillas -> {destino}", flush=True)


def validar_referencias(args):
    """Retraso total de las referencias en las semillas de validacion del modelo: las lineas de la figura de
    aprendizaje. No interviene en el veredicto."""
    res = {}
    with Pool(args.procesos) as pool:
        for brazo, archivo in ARCHIVO.items():
            ruta = os.path.join(CARPETA, archivo)
            if os.path.exists(ruta):
                res[brazo] = media(pool.map(_fija, [(ruta, s, f"val{brazo}") for s in VALIDACION]))
                print(f"{brazo}: {res[brazo]:8.2f} s/veh en las semillas de validacion", flush=True)
    os.makedirs(SALIDAS, exist_ok=True)
    with open(os.path.join(SALIDAS, "val_referencias.json"), "w", encoding="utf-8") as f:
        json.dump({"semillas": [VALIDACION[0], VALIDACION[-1]], "retraso_total": res}, f, indent=1)


def _verdes(tarea):
    """Una corrida de la politica con registro de fases: verde medio (s) de cada estado y ciclos en la hora."""
    import torch
    import programa
    import rl_ippo
    torch.set_num_threads(1)
    ruta, semilla = tarea
    rl_ippo.preparar("lima")
    politica, meta = rl_ippo.Politica.cargar(ruta)
    rl_ippo.configurar_desde_meta(meta)
    serie = os.path.join(TMP, f"serie_{os.getpid()}_{semilla}.csv")
    tripinfo = os.path.join(TMP, f"trip_verdes_{os.getpid()}_{semilla}.xml")
    rl_ippo.correr_episodio("demo", politica, False, 0, semilla, tripinfo=tripinfo, serie=serie,
                            variante=meta.get("variante", "vecinos"))
    _borrar(tripinfo)
    fases_csv = serie.replace("serie_", "fases_", 1)
    with open(fases_csv, encoding="utf-8-sig", newline="") as f:
        fases = [int(float(r[1])) for r in list(csv.reader(f))[1:]]
    for sobra in (serie, fases_csv):
        os.remove(sobra)
    lista, _ = programa.fases([v for _, v, _ in programa.PLAN])
    indices = [k for k, (_, _, nombre) in enumerate(lista) if nombre not in programa.NO_VERDES]
    tramos, ini = [], 0
    for i in range(1, len(fases) + 1):
        if i == len(fases) or fases[i] != fases[ini]:
            tramos.append((fases[ini], i - ini))
            ini = i
    tramos = tramos[1:-1]                      # el primero y el ultimo quedan cortados por el borde de la hora
    return [statistics.mean(n for f, n in tramos if f == k) for k in indices], \
        sum(1 for f, _ in tramos if f == indices[0])


def verdes_modelo(args):
    """Verde medio que da el modelo a cada estado en las semillas de validacion (para la figura del ciclo)."""
    ruta = os.path.abspath((args.politicas or "").split(",")[0])
    with Pool(args.procesos) as pool:
        res = pool.map(_verdes, [(ruta, s) for s in VALIDACION])
    n = len(res[0][0])
    verdes = [statistics.mean(r[0][k] for r in res) for k in range(n)]
    os.makedirs(SALIDAS, exist_ok=True)
    with open(os.path.join(SALIDAS, "verdes_modelo.json"), "w", encoding="utf-8") as f:
        json.dump({"politica": os.path.basename(ruta), "semillas": [VALIDACION[0], VALIDACION[-1]],
                   "verdes": verdes, "ciclos_por_hora": statistics.mean(r[1] for r in res)}, f, indent=1)
    print("Verde medio por estado (s):", ", ".join(f"{v:.1f}" for v in verdes),
          f"| ciclos por hora {statistics.mean(r[1] for r in res):.1f}")


# ---------------- veredicto ----------------
def leer(tanda, brazo):
    ruta = os.path.join(SALIDAS, f"eval_t{tanda}_{brazo}.csv")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8", newline="") as f:
        return {int(r["semilla"]): float(r[METRICA]) for r in csv.DictReader(f)}


def comparar(vals, ref):
    """Cambio % de la media, IC95 por bootstrap pareado y p de Wilcoxon pareado (las funciones de la tesis)."""
    import evaluar as ev
    from scipy import stats
    semillas = sorted(set(vals) & set(ref))
    a, b = [vals[s] for s in semillas], [ref[s] for s in semillas]
    delta = (statistics.mean(a) - statistics.mean(b)) / statistics.mean(b) * 100
    lo, hi = ev.bootstrap_delta(b, a)
    difs = [x - y for x, y in zip(a, b)]
    p = stats.wilcoxon(difs).pvalue if any(d != 0 for d in difs) else 1.0
    return {"n": len(semillas), "media": statistics.mean(a), "media_ref": statistics.mean(b), "delta": delta,
            "ic": (float(lo), float(hi)), "p": float(p)}


def veredicto(args):
    import veredicto as regla
    lineas = [f"# Caso Lima: veredicto de {args.modelo}", ""]
    etiquetas = []
    for tanda in TANDAS:
        vals = leer(tanda, args.modelo)
        if vals is None:
            lineas.append(f"Tanda {tanda}: sin evaluar")
            continue
        lineas += [f"## Tanda {tanda} ({len(vals)} semillas)", "",
                   "| Frente a | Retraso total de la referencia (s/veh) | Del modelo (s/veh) | Cambio (%) | IC95 | p |",
                   "|---|---|---|---|---|---|"]
        comp = {}
        for ref in ("fijo", "actuadoaj", "actual", "actuado", "minimo"):
            r = leer(tanda, ref)
            if r is None:
                continue
            c = comp[ref] = comparar(vals, r)
            lineas.append(f"| {ref} | {c['media_ref']:.2f} | {c['media']:.2f} | {c['delta']:+.2f} | "
                          f"[{c['ic'][0]:+.2f}, {c['ic'][1]:+.2f}] | {c['p']:.3g} |")
        if "fijo" in comp:
            f, a = comp["fijo"], comp.get("actuadoaj")
            etiqueta = regla.veredicto(f["delta"], f["ic"], f["p"], a["ic"] if a else None, a["p"] if a else None)
            etiquetas.append(etiqueta)
            lineas += ["", f"Veredicto de la tanda {tanda}: **{etiqueta}**", ""]
    if len(etiquetas) == 2:
        lineas.append(f"Veredicto citable: **{etiquetas[0] if etiquetas[0] == etiquetas[1] else 'EMPATA (no se repite)'}**")
    texto = "\n".join(lineas) + "\n"
    with open(os.path.join(SALIDAS, f"veredicto_{args.modelo}.md"), "w", encoding="utf-8") as f:
        f.write(texto)
    print(texto)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["ajustar-fijo", "ajustar-actuado", "evaluar", "validar-referencias",
                                       "verdes-modelo", "veredicto"])
    ap.add_argument("--procesos", type=int, default=10)
    ap.add_argument("--tanda", type=int, choices=[1, 2], default=1)
    ap.add_argument("--semillas", default=None, help="(pruebas) lista de semillas en vez de la tanda")
    ap.add_argument("--brazos", default=None, help="solo estas referencias, separadas por coma")
    ap.add_argument("--politicas", default=None, help="archivos .pt separados por coma")
    ap.add_argument("--modelo", default=None, help="brazo del modelo para el veredicto")
    ap.add_argument("--rehacer", action="store_true")
    args = ap.parse_args()
    os.chdir(CARPETA)
    os.makedirs(TMP, exist_ok=True)
    {"ajustar-fijo": ajustar_fijo, "ajustar-actuado": ajustar_actuado, "evaluar": evaluar,
     "validar-referencias": validar_referencias, "verdes-modelo": verdes_modelo,
     "veredicto": veredicto}[args.accion](args)


if __name__ == "__main__":
    main()
