"""
estudio_corredor.py - Corredor de la Av. Benavides: ajusta las referencias, evalua todos los controles y calcula el
veredicto. Mismas reglas que el nudo (lima/estudio.py y lima/REGISTRO.md).

Uso (desde demo_rl/lima/corredor, con la red, el plan tipico y la demanda ya escritos por corredor.py):
  python estudio_corredor.py ajustar-fijo      [--procesos 8]   # -> benavides_fijo.add.xml y benavides_minimo.add.xml
  python estudio_corredor.py ajustar-actuado   [--procesos 8]   # -> benavides_actuado.add.xml y benavides_actuadoaj.add.xml
  python estudio_corredor.py validar-referencias                # las referencias en las semillas de validacion
  python estudio_corredor.py evaluar --tanda 1 [--politicas a.pt,b.pt] [--perdida 1]
  python estudio_corredor.py verdes-modelo --politicas a.pt     # verde medio que da el modelo en cada cruce (figura)
  python estudio_corredor.py veredicto --modelo <brazo> [--sin-mensajes <brazo> --con-mensajes <brazo>]

Otro nivel de demanda: la variable de entorno CORREDOR_CARPETA (alta = demanda alta) cambia la carpeta de los datos
y de las salidas; la red y los programas son los mismos (corredor.py nivel la prepara).

Controles (todos con los mismos dos estados por cruce: avenida y transversal):
  tipico     el plan tipico supuesto (benavides.add.xml): ciclo de 140 s, transversal 43 s, sin desfases
  fijo       fijo ajustado al segundo: ciclo comun, verde de la transversal de cada cruce y desfase de cada cruce
  actuado    control actuado de SUMO en cada cruce, con verdes de 10 a 60 s
  actuadoaj  actuado ajustado: el mejor de una rejilla de parametros
  minimo     ciclo minimo: avenida y transversal en 10 s
  <politica> un modelo entrenado (rl_ippo.py), con la politica congelada
  <politica>_cortado   el mismo modelo sin que le llegue ningun mensaje de sus vecinos (evaluar --perdida 1)
Semillas: ajuste 2001-2010 y 2001-2030; validacion 21001-21004; evaluacion 22001-22100 y 23001-23100.
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
LIMA = os.path.dirname(AQUI)
RAIZ = os.path.dirname(LIMA)
for carpeta in (RAIZ, LIMA, AQUI):
    sys.path.insert(0, carpeta)
import estudio                     # comparar(), media() y las semillas del caso Lima
import corredor

ESC = corredor.ESC
CFG = f"{ESC}.sumocfg"
CARPETA = os.path.normpath(os.path.join(AQUI, os.environ.get("CORREDOR_CARPETA", "")))   # relativa a los programas
TMP = os.path.join(CARPETA, "tmp")
SALIDAS = os.path.join(CARPETA, "salidas")
VALIDACION = list(range(21001, 21005))
ARCHIVO = {"tipico": f"{ESC}.add.xml", "fijo": f"{ESC}_fijo.add.xml", "actuado": f"{ESC}_actuado.add.xml",
           "actuadoaj": f"{ESC}_actuadoaj.add.xml", "minimo": f"{ESC}_minimo.add.xml",
           # el actuado ajustado de la rejilla anterior, de 12 combinaciones (REGISTRO.md, enmienda del 14.11.2026)
           "actuadoaj12": f"{ESC}_actuadoaj12.add.xml",
           # lo que dejan atras las enmiendas del fijo (05:50) y de las variantes coordinadas (05:40), si cambian el
           # ganador: el fijo de la primera busqueda (ciclo de 55 s) y el actuado ajustado sin variantes coordinadas
           "fijo55": f"{ESC}_fijo55.add.xml", "actuadoajsc": f"{ESC}_actuadoajsc.add.xml"}
CICLO_MAX, VERDE_MAX, MIN = 200, 60, corredor.VERDE_MIN
N = len(corredor.IDS)
POSICION = [x for _, _, x, _, _ in corredor.CRUCES]
# estudio 2 (19.11.2026): verdes minimos de los peatones de cada cruce, para la avenida y para la transversal
MIN_AV = [corredor.minimos(c)[0] for c in corredor.IDS]
MIN_TR = [corredor.minimos(c)[1] for c in corredor.IDS]


def _fija(tarea):
    import barrer_fijo
    archivo, semilla, marca = tarea
    tripinfo = os.path.join(TMP, f"trip_{marca}_{os.getpid()}_{semilla}.xml")
    res = barrer_fijo.correr_sumo(CFG, ["--additional-files", archivo], semilla, tripinfo)
    estudio._borrar(tripinfo)
    return res


def _cargar(ruta):
    import torch
    import rl_ippo
    torch.set_num_threads(1)
    if _cargar.ruta != ruta:
        rl_ippo.preparar(ESC)
        politica, meta = rl_ippo.Politica.cargar(ruta)
        rl_ippo.configurar_desde_meta(meta)
        _cargar.ruta, _cargar.politica, _cargar.meta = ruta, politica, meta
    return _cargar.politica, _cargar.meta


_cargar.ruta = None


def _modelo(tarea):
    """Una corrida con una politica entrenada (argmax). tarea = (ruta .pt, semilla, marca[, perdida del canal])."""
    import rl_ippo
    ruta, semilla, marca = tarea[:3]
    perdida = tarea[3] if len(tarea) > 3 else 0.0
    politica, meta = _cargar(ruta)
    tripinfo = os.path.join(TMP, f"trip_{marca}_{os.getpid()}_{semilla}.xml")
    res = rl_ippo.correr_episodio("demo", politica, False, 0, semilla, tripinfo=tripinfo, perdida=perdida,
                                  variante=meta.get("variante", "vecinos"))
    estudio._borrar(tripinfo)
    return res


# ---------------- fijo ajustado al segundo ----------------
def valido(plan):
    ciclo, trans = plan[0], plan[1:1 + N]
    return ciclo <= CICLO_MAX and all(t >= MIN_TR[k] and ciclo - 2 * corredor.AMBAR - t >= MIN_AV[k]
                                      for k, t in enumerate(trans))


def onda(ciclo, velocidad):
    """Desfases de una onda verde a `velocidad` m/s hacia el este (positiva) o hacia el oeste (negativa)."""
    return [int(round(x / velocidad)) % ciclo for x in POSICION]


def anchos(ciclo, verdes_av, desf, v):
    """Ancho de banda (s por ciclo) hacia el este y hacia el oeste de un plan fijo: el verde de la avenida del cruce k
    empieza en desf[k] (mas un segundo de verde util, como en revision_corredor_2026-11-19/referencias/scripts/rev.py)."""
    import numpy as np
    tau = np.arange(0, ciclo, 0.5)
    ok_e = np.ones_like(tau, dtype=bool)
    ok_w = np.ones_like(tau, dtype=bool)
    for k in range(N):
        g = verdes_av[k] + 1.0
        ok_e &= (tau + POSICION[k] / v - desf[k]) % ciclo < g
        ok_w &= (tau + (POSICION[-1] - POSICION[k]) / v - desf[k]) % ciclo < g
    return ok_e.mean() * ciclo, ok_w.mean() * ciclo


def onda_doble(ciclo, trans, v=12.0, reinicios=40, semilla=0):
    """Desfases de una onda verde en los dos sentidos a v m/s: los que maximizan min(este, oeste) + (este + oeste) / 2
    (anchos de banda), por coordenadas con reinicios al azar (la partida que encontro el mejor fijo de la demanda alta
    en la revision del 19.11.2026: referencias/scripts/rev.py, ondas_dos_sentidos)."""
    import random
    rng = random.Random(semilla)
    verdes = [ciclo - 2 * corredor.AMBAR - t for t in trans]

    def obj(d):
        e, w = anchos(ciclo, verdes, d, v)
        return min(e, w) + 0.5 * (e + w)

    mejor_d, mejor_o = None, None
    for _ in range(reinicios):
        d = [0] + [rng.randrange(ciclo) for _ in range(1, N)]
        o = obj(d)
        cambio = True
        while cambio:
            cambio = False
            for k in range(1, N):
                for x in range(ciclo):
                    if x != d[k]:
                        c = list(d)
                        c[k] = x
                        oc = obj(c)
                        if oc > o + 1e-9:
                            d, o, cambio = c, oc, True
        if mejor_o is None or o > mejor_o:
            mejor_d, mejor_o = d, o
    return mejor_d


CICLOS_CORTOS = (32, 36, 40, 44, 48)       # partidas añadidas por la enmienda del 14.11.2026 (REGISTRO.md)
# estudio 2 (19.11.2026): ciclos de partida, todos con el reparto de Webster y los minimos de los peatones; el menor
# ciclo posible es el de Paseo de la Republica, 12 + 19 + 6 = 37 s
CICLOS_ESTUDIO2 = (40, 44, 48, 52, 56, 60, 66, 72, 80, 90, 100)


def reparto_por_carga(ciclo):
    """Verde de la transversal de cada cruce para un ciclo dado: el verde util se reparte segun los vehiculos por
    carril del acceso mas cargado de la avenida y de la transversal (el reparto del metodo de Webster), sin bajar
    del verde minimo en ninguna de las dos."""
    este, oeste, por_acceso = [0.0] * N, [0.0] * N, {}
    for (_, desde, hacia), q in corredor.flujos().items():
        if desde in ("W_C1", "E_C6"):                    # entra por un extremo de la avenida
            a = 0 if desde == "W_C1" else N - 1
            b = N - 1 if hacia == "C6_E" else 0 if hacia == "C1_W" else corredor.IDS.index(hacia.split("_")[0])
            for k in range(min(a, b), max(a, b) + 1):
                (este if desde == "W_C1" else oeste)[k] += q
        else:                                            # entra por una transversal y, si gira, sigue por la avenida
            a = corredor.IDS.index(desde.split("_")[1])
            por_acceso[(a, desde[0])] = por_acceso.get((a, desde[0]), 0.0) + q
            for k in (range(a + 1, N) if hacia == "C6_E" else range(0, a) if hacia == "C1_W" else ()):
                (este if hacia == "C6_E" else oeste)[k] += q
    verde, res = ciclo - 2 * corredor.AMBAR, []
    for k in range(N):
        avenida = max(este[k] / corredor.CARRILES_AV["W" if k == 0 else corredor.IDS[k - 1]],
                      oeste[k] / corredor.CARRILES_AV[corredor.IDS[k]])
        transversal = max(q / corredor.CRUCES[k][3 if lado == "N" else 4] for (a, lado), q in por_acceso.items() if a == k)
        res.append(max(MIN_TR[k], min(verde - MIN_AV[k], int(round(verde * transversal / (avenida + transversal))))))
    return tuple(res)


def ajustar_fijo(args):
    cache = {}

    def puntaje(plan, pool, semillas=estudio.AJUSTE):
        plan = tuple(plan)
        clave = (plan, len(semillas))
        if clave not in cache:
            ciclo, trans, desf = plan[0], plan[1:1 + N], (0,) + plan[1 + N:]
            archivo = os.path.join(TMP, f"fijo_{abs(hash(plan))}.add.xml")
            corredor.escribir_programa(archivo, ciclo, trans, desf)
            res = pool.map(_fija, [(archivo, s, "aj") for s in semillas])
            cache[clave] = estudio.media(res)
            os.remove(archivo)
            print(f"  ciclo {ciclo:3d}, transversales {list(trans)}, desfases {list(desf)}, {len(semillas)} semillas: "
                  f"{cache[clave]:7.2f} s/veh", flush=True)
        return cache[clave]

    def normal(plan):
        """Desfases dentro del ciclo."""
        ciclo = plan[0]
        return tuple(plan[:1 + N]) + tuple(d % ciclo for d in plan[1 + N:])

    with Pool(args.procesos) as pool:
        if args.ampliar:
            # enmienda del 14.11.2026 (REGISTRO.md): partidas de ciclo corto sobre la busqueda ya hecha, cuyos
            # candidatos se conservan; se afinan las dos mejores partidas nuevas de ciclos distintos
            with open(os.path.join(SALIDAS, "fijo_ajustado.json"), encoding="utf-8") as f:
                for c in json.load(f)["candidatos"]:
                    cache[(tuple(c["plan"]), c["semillas"])] = c["retraso_total"]
            partidas = []
            for ciclo in CICLOS_CORTOS:
                t = reparto_por_carga(ciclo)
                partidas.append((ciclo,) + t + (0,) * (N - 1))
                for v in (12.0, -12.0):
                    partidas.append((ciclo,) + t + tuple(onda(ciclo, v)[1:]))
            por_ciclo = [min((p for p in partidas if p[0] == c), key=lambda p: puntaje(p, pool)) for c in CICLOS_CORTOS]
            salidas = sorted(por_ciclo, key=lambda p: puntaje(p, pool))[:2]
        else:
            # estudio 2 (enmienda del 19.11.2026): el plan tipico y, en cada ciclo de CICLOS_ESTUDIO2, el reparto de
            # Webster con los minimos de los peatones, sin desfases, con onda verde hacia el este, hacia el oeste y en
            # los dos sentidos; se afinan las tres mejores partidas de ciclos distintos
            partidas = [(corredor.PLAN_TIPICO["ciclo"],) + (corredor.PLAN_TIPICO["transversal"],) * N + (0,) * (N - 1)]
            for ciclo in CICLOS_ESTUDIO2:
                t = reparto_por_carga(ciclo)
                partidas.append((ciclo,) + t + (0,) * (N - 1))
                for v in (12.0, -12.0):
                    partidas.append((ciclo,) + t + tuple(onda(ciclo, v)[1:]))
                partidas.append((ciclo,) + t + tuple(onda_doble(ciclo, t)[1:]))
            partidas = [normal(p) for p in partidas if valido(p)]
            mejores = {}
            for p in sorted(partidas, key=lambda p: puntaje(p, pool)):
                mejores.setdefault(p[0], p)
            salidas = sorted(mejores.values(), key=lambda p: puntaje(p, pool))[:3]
        for mejor in salidas:
            for paso in (8, 4, 2, 1):                   # descenso por coordenadas, afinando hasta 1 s
                mejoro = True
                while mejoro:
                    mejoro = False
                    for k in range(len(mejor)):
                        for signo in (-1, 1):
                            cand = list(mejor)
                            cand[k] += signo * paso
                            cands = [normal(cand)]
                            if k == 0 and not args.ampliar:
                                # estudio 2: al cambiar el ciclo, tambien con los desfases movidos junto con el (la
                                # misma fraccion del ciclo; revision del 19.11.2026, referencias/INFORME.md)
                                cands.append(normal(list(cand[:1 + N]) + [int(round(d * cand[0] / mejor[0]))
                                                                          for d in mejor[1 + N:]]))
                            for cand in cands:
                                if cand != tuple(mejor) and valido(cand) and puntaje(cand, pool) < puntaje(mejor, pool):
                                    mejor, mejoro = cand, True
                print(f"paso {paso} s: mejor {list(mejor)} = {puntaje(mejor, pool):.2f}", flush=True)
        orden = sorted((p for (p, k) in cache if k == len(estudio.AJUSTE)), key=lambda p: cache[(p, len(estudio.AJUSTE))])
        ganador = min(orden[:estudio.FINALISTAS], key=lambda p: puntaje(p, pool, estudio.DESEMPATE))
    ciclo, trans, desf = ganador[0], list(ganador[1:1 + N]), [0] + list(ganador[1 + N:])
    corredor.escribir_programa(os.path.join(CARPETA, ARCHIVO["fijo"]), ciclo, trans, desf, programa="fijo_ajustado",
                               comentario=f"Fijo ajustado al segundo del corredor (estudio_corredor.py): ciclo {ciclo} s, "
                               f"transversales {trans}, desfases {desf}")
    ciclo_min = max(a + t for a, t in zip(MIN_AV, MIN_TR)) + 2 * corredor.AMBAR
    corredor.escribir_programa(os.path.join(CARPETA, ARCHIVO["minimo"]), ciclo_min, MIN_TR, programa="minimo",
                               comentario=f"Ciclo minimo del corredor: ciclo comun de {ciclo_min} s, transversales en su "
                               "verde minimo de peatones y la avenida con el resto")
    os.makedirs(SALIDAS, exist_ok=True)
    with open(os.path.join(SALIDAS, "fijo_ajustado.json"), "w", encoding="utf-8") as f:
        json.dump({"ciclo": ciclo, "transversal": trans, "desfases": desf,
                   "retraso_total_30": cache[(ganador, len(estudio.DESEMPATE))],
                   "tipico": corredor.PLAN_TIPICO, "evaluaciones": len(cache),
                   "ciclos_cortos_de_la_ampliacion": list(CICLOS_CORTOS) if args.ampliar else None,
                   "candidatos": [{"plan": list(p), "semillas": k, "retraso_total": round(m, 4)}
                                  for (p, k), m in sorted(cache.items(), key=lambda kv: kv[1])]}, f, indent=1)
    print(f"Fijo ajustado: ciclo {ciclo} s, transversales {trans}, desfases {desf}: "
          f"{cache[(ganador, len(estudio.DESEMPATE))]:.2f} s/veh con 30 semillas; {len(cache)} evaluaciones")
    if ciclo >= CICLO_MAX:
        print(f"AVISO: el ganador toca el tope de ciclo de {CICLO_MAX} s")


# ---------------- actuado y actuado ajustado ----------------
def ajustar_actuado(args):
    with open(os.path.join(SALIDAS, "fijo_ajustado.json"), encoding="utf-8") as f:
        fijo = json.load(f)
    corredor.escribir_programa(os.path.join(CARPETA, ARCHIVO["actuado"]), None, None, tipo="actuado",
                               maximos=[(VERDE_MAX, VERDE_MAX)] * N,
                               comentario="Actuado del corredor: control actuado de SUMO, verdes desde el minimo de "
                               "los peatones hasta 60 s")
    # el actuado ajustado se busca como en el nudo: los pasos del segundo estudio (estudio.buscar_actuado); estudio 2:
    # con los minimos de los peatones y un esquema mas de verdes maximos, 35 s la avenida y 25 la transversal (el
    # mejor actuado de la revision del 19.11.2026 con la demanda publicada)
    maximos = {"60": [(VERDE_MAX, VERDE_MAX)] * N,
               "doble del fijo": [(min(VERDE_MAX, max(MIN_AV[k], 2 * (fijo["ciclo"] - 2 * corredor.AMBAR - t))),
                                   min(VERDE_MAX, max(MIN_TR[k], 2 * t))) for k, t in enumerate(fijo["transversal"])],
               "30/20": [(max(MIN_AV[k], 30), max(MIN_TR[k], 20)) for k in range(N)],
               "35/25": [(max(MIN_AV[k], 35), max(MIN_TR[k], 25)) for k in range(N)],
               "45/35": [(max(MIN_AV[k], 45), max(MIN_TR[k], 35)) for k in range(N)]}

    def escribir_variante(archivo, v, **extra):
        # las dos variantes coordinadas van sobre el plan del fijo ajustado: su ciclo, sus verdes y sus desfases
        plan = (fijo["ciclo"], fijo["transversal"], fijo["desfases"]) if v.get("coordinado") else (None, None, None)
        corredor.escribir_programa(archivo, *plan, tipo=v["tipo"], maximos=maximos[v["esquema"]],
                                   parametros=estudio.parametros_sumo(v), coordinado=v.get("coordinado"), **extra)

    with Pool(args.procesos) as pool:
        gan, orden, por_defecto = estudio.buscar_actuado(escribir_variante, list(maximos), pool, _fija, TMP,
                                                         coordinadas=True)
    escribir_variante(os.path.join(CARPETA, ARCHIVO["actuadoaj"]), gan, programa="actuado_ajustado",
                      comentario="Actuado ajustado del corredor (estudio_corredor.py): " + estudio.texto_variante(gan))
    with open(os.path.join(SALIDAS, "actuado_ajustado.json"), "w", encoding="utf-8") as f:
        json.dump({"ganador": dict(gan, maximos=maximos[gan["esquema"]]), "actuado_por_defecto_30": por_defecto,
                   "procedimiento": estudio.PROCEDIMIENTO_ACTUADO + "; con las dos variantes coordinadas del segundo "
                   "estudio sobre el fijo ajustado", "fijo": {k: fijo[k] for k in ("ciclo", "transversal", "desfases")},
                   "candidatos": orden}, f, indent=1)
    print(f"Actuado ajustado: {estudio.texto_variante(gan)}, {gan['retraso_total_30']:.2f} s/veh con 30 semillas; "
          f"actuado por defecto {por_defecto:.2f}; {len(orden)} variantes")


def validar_referencias(args):
    res = {}
    with Pool(args.procesos) as pool:
        for brazo, archivo in ARCHIVO.items():
            ruta = os.path.join(CARPETA, archivo)
            if os.path.exists(ruta):
                res[brazo] = estudio.media(pool.map(_fija, [(ruta, s, f"val{brazo}") for s in VALIDACION]))
                print(f"{brazo}: {res[brazo]:8.2f} s/veh en las semillas de validacion", flush=True)
    os.makedirs(SALIDAS, exist_ok=True)
    with open(os.path.join(SALIDAS, "val_referencias.json"), "w", encoding="utf-8") as f:
        json.dump({"semillas": [VALIDACION[0], VALIDACION[-1]], "retraso_total": res}, f, indent=1)


# ---------------- que hace el modelo ----------------
def _verdes(tarea):
    """Una corrida de la politica con registro de fases. Por cruce: verde medio de la avenida, verde medio de la
    transversal y ciclo medio (s), sin el primer tramo ni el ultimo, que quedan cortados por el borde de la hora."""
    import rl_ippo
    ruta, semilla = tarea
    politica, meta = _cargar(ruta)
    serie = os.path.join(TMP, f"serie_{os.getpid()}_{semilla}.csv")
    tripinfo = os.path.join(TMP, f"trip_verdes_{os.getpid()}_{semilla}.xml")
    rl_ippo.correr_episodio("demo", politica, False, 0, semilla, tripinfo=tripinfo, serie=serie,
                            variante=meta.get("variante", "vecinos"))
    estudio._borrar(tripinfo)
    fases_csv = serie.replace("serie_", "fases_", 1)
    with open(fases_csv, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.reader(f))
    for sobra in (serie, fases_csv):
        os.remove(sobra)
    res = {}
    for col, tls in enumerate(filas[0][1:], start=1):
        fases = [int(float(r[col])) for r in filas[1:]]
        tramos, ini = [], 0
        for i in range(1, len(fases) + 1):
            if i == len(fases) or fases[i] != fases[ini]:
                tramos.append((fases[ini], ini, i - ini))
                ini = i
        tramos = tramos[1:-1]
        inicios = [t for f, t, _ in tramos if f == 0]
        res[tls.replace("semaforo_", "")] = {
            "avenida": statistics.mean(n for f, _, n in tramos if f == 0),
            "transversal": statistics.mean(n for f, _, n in tramos if f == 2),
            "ciclo": (inicios[-1] - inicios[0]) / (len(inicios) - 1)}
    return res


def verdes_modelo(args):
    """Verde medio que da el modelo en cada cruce, en las semillas de validacion (para la figura de los ciclos)."""
    ruta = os.path.abspath((args.politicas or "").split(",")[0])
    with Pool(args.procesos) as pool:
        res = pool.map(_verdes, [(ruta, s) for s in VALIDACION])
    cruces = {c: {k: statistics.mean(r[c][k] for r in res) for k in ("avenida", "transversal", "ciclo")}
              for c in corredor.IDS}
    os.makedirs(SALIDAS, exist_ok=True)
    with open(os.path.join(SALIDAS, "verdes_modelo.json"), "w", encoding="utf-8") as f:
        json.dump({"politica": os.path.basename(ruta), "semillas": [VALIDACION[0], VALIDACION[-1]], "cruces": cruces},
                  f, indent=1)
    for c, v in cruces.items():
        print(f"{c}: avenida {v['avenida']:.1f} s, transversal {v['transversal']:.1f} s, ciclo {v['ciclo']:.1f} s")


# ---------------- evaluacion y veredicto ----------------
def nombre_politica(ruta):
    return os.path.splitext(os.path.basename(ruta))[0].replace(f"politica_{ESC}_", "")


def evaluar(args):
    semillas = estudio.TANDAS[args.tanda] if not args.semillas else [int(s) for s in args.semillas.split(",")]
    brazos = [(b, os.path.join(CARPETA, a), _fija, ()) for b, a in ARCHIVO.items()
              if os.path.exists(os.path.join(CARPETA, a)) and (args.brazos is None or b in args.brazos.split(","))]
    for ruta in [p for p in (args.politicas or "").split(",") if p]:
        # --perdida 1: el canal cortado (ningun mensaje llega); el brazo se llama <politica>_cortado
        sufijo = "" if not args.perdida else "_cortado" if args.perdida >= 1 else f"_p{args.perdida:g}"
        brazos.append((nombre_politica(ruta) + sufijo, os.path.abspath(ruta), _modelo, (args.perdida,)))
    os.makedirs(SALIDAS, exist_ok=True)
    with Pool(args.procesos) as pool:
        for nombre, ruta, funcion, extra in brazos:
            destino = os.path.join(SALIDAS, f"eval_t{args.tanda}_{nombre}.csv")
            if os.path.exists(destino) and not args.rehacer:
                print(f"{nombre}: ya esta ({destino})")
                continue
            res = pool.map(funcion, [(ruta, s, nombre) + extra for s in semillas], chunksize=1)
            campos = ["brazo", "semilla"] + [k for k in res[0] if k not in ("brazo", "semilla")]
            with open(destino + ".tmp", "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
                w.writeheader()
                for s, r in zip(semillas, res):
                    w.writerow({"brazo": nombre, "semilla": s, **r})
            os.replace(destino + ".tmp", destino)
            print(f"{nombre}: {estudio.media(res):8.2f} s/veh de retraso total en {len(res)} semillas", flush=True)


def leer(tanda, brazo):
    ruta = os.path.join(SALIDAS, f"eval_t{tanda}_{brazo}.csv")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8", newline="") as f:
        return {int(r["semilla"]): float(r[estudio.METRICA]) for r in csv.DictReader(f)}


def veredicto(args):
    import veredicto as regla
    lineas = [f"# Corredor de la Av. Benavides: veredicto de {args.modelo}", ""]
    etiquetas = []
    for tanda in estudio.TANDAS:
        vals = leer(tanda, args.modelo)
        if vals is None:
            lineas.append(f"Tanda {tanda}: sin evaluar")
            continue
        lineas += [f"## Tanda {tanda} ({len(vals)} semillas)", "",
                   "| Frente a | Retraso total de la referencia (s/veh) | Del modelo (s/veh) | Cambio (%) | IC95 | p |",
                   "|---|---|---|---|---|---|"]
        comp = {}
        for ref in ("fijo", "actuadoaj", "tipico", "actuado", "minimo"):
            r = leer(tanda, ref)
            if r is None:
                continue
            c = comp[ref] = estudio.comparar(vals, r)
            lineas.append(f"| {ref} | {c['media_ref']:.2f} | {c['media']:.2f} | {c['delta']:+.2f} | "
                          f"[{c['ic'][0]:+.2f}, {c['ic'][1]:+.2f}] | {c['p']:.3g} |")
        if "fijo" in comp:
            f, a = comp["fijo"], comp.get("actuadoaj")
            etiqueta = regla.veredicto(f["delta"], f["ic"], f["p"], a["ic"] if a else None, a["p"] if a else None)
            etiquetas.append(etiqueta)
            lineas += ["", f"Veredicto de la tanda {tanda}: **{etiqueta}**", ""]
        if args.con_mensajes and args.sin_mensajes:
            con, sin = leer(tanda, args.con_mensajes), leer(tanda, args.sin_mensajes)
            if con and sin:
                c = estudio.comparar(con, sin)
                lineas += [f"Con mensajes ({args.con_mensajes}) frente a sin mensajes ({args.sin_mensajes}): "
                           f"{c['media']:.2f} frente a {c['media_ref']:.2f} s/veh, {c['delta']:+.2f} % "
                           f"[{c['ic'][0]:+.2f}, {c['ic'][1]:+.2f}], p = {c['p']:.3g}", ""]
    if len(etiquetas) == 2:
        lineas.append(f"Veredicto citable: **{etiquetas[0] if etiquetas[0] == etiquetas[1] else 'EMPATA (no se repite)'}**")
    texto = "\n".join(lineas) + "\n"
    with open(os.path.join(SALIDAS, f"veredicto_{args.modelo}.md"), "w", encoding="utf-8") as f:
        f.write(texto)
    print(texto)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["ajustar-fijo", "ajustar-actuado", "validar-referencias", "evaluar",
                                       "verdes-modelo", "veredicto"])
    ap.add_argument("--procesos", type=int, default=8)
    ap.add_argument("--tanda", type=int, choices=[1, 2], default=1)
    ap.add_argument("--semillas", default=None, help="(pruebas) lista de semillas en vez de la tanda")
    ap.add_argument("--brazos", default=None, help="solo estas referencias, separadas por coma ('' = ninguna)")
    ap.add_argument("--politicas", default=None, help="archivos .pt separados por coma")
    ap.add_argument("--perdida", type=float, default=0.0,
                    help="probabilidad de que se pierda cada mensaje al evaluar las politicas (1 = canal cortado)")
    ap.add_argument("--modelo", default=None, help="brazo del modelo para el veredicto")
    ap.add_argument("--con-mensajes", default=None)
    ap.add_argument("--sin-mensajes", default=None)
    ap.add_argument("--rehacer", action="store_true")
    ap.add_argument("--ampliar", action="store_true",
                    help="ajustar-fijo: añade partidas de ciclo corto a la busqueda ya hecha (REGISTRO.md, 14.11.2026)")
    args = ap.parse_args()
    os.chdir(CARPETA)
    os.makedirs(TMP, exist_ok=True)
    {"ajustar-fijo": ajustar_fijo, "ajustar-actuado": ajustar_actuado, "validar-referencias": validar_referencias,
     "evaluar": evaluar, "verdes-modelo": verdes_modelo, "veredicto": veredicto}[args.accion](args)


if __name__ == "__main__":
    main()
