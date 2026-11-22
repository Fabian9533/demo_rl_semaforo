"""
borde_actuado.py - Comprobacion del borde del actuado ajustado (REGISTRO.md, 14.11.2026, 15:55): un paso mas alla de
cada borde de la busqueda, con las mismas semillas y el mismo desempate que estudio.buscar_actuado. Solo escribe
salidas/borde_actuado.json de la carpeta del caso; si cambia el ganador, los archivos se cambian aparte.

Uso (desde demo_rl/lima):
  python borde_actuado.py nudo [--carpeta alta] [--procesos 3]
  python borde_actuado.py corredor [--carpeta alta] [--procesos 3]
  python borde_actuado.py nudo --carpeta alta --instalar    # escribe el nuevo ganador, si cambio
  python borde_actuado.py ovalo [--carpeta alta] [--procesos 3] [--instalar]
  python borde_actuado.py --probar-reglas                    # no simula (ver abajo)

ovalo (18.11.2026, el nudo en la red del Ovalo Vasco; con LIMA_PROGRAMA=programa_ovalo): lo mismo que nudo, pero las
variantes salen de la regla escrita de forma general (variantes_bordes): un paso mas alla de cada parametro que quedo en
un extremo de los valores probados, con todo lo demas igual al mejor de su tipo (el mejor por retraso y el mejor de la
cadena); si un tipo tiene varios parametros en un extremo, ademas todos a la vez. En nudo y corredor las variantes eran
las de sus ganadores; en el ovalo el ganador puede quedar en otro borde. --probar-reglas comprueba, sin simular, que la
regla general da exactamente las variantes registradas en los cuatro casos de Lima (copias de sus actuado_ajustado.json
en ovalo/entrada/actuado_estudio/).
"""
import argparse
import ctypes
import json
import os
import sys
from multiprocessing import Pool

AQUI = os.path.dirname(os.path.abspath(__file__))
for carpeta in (os.path.dirname(AQUI), AQUI, os.path.join(AQUI, "corredor")):
    if carpeta not in sys.path:
        sys.path.insert(0, carpeta)
if os.name == "nt":            # prioridad baja: no frena la evaluacion que corre al lado (la heredan los procesos hijos)
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)


def sin_medidas(v):
    return {k: x for k, x in v.items() if not k.startswith("retraso_total") and k != "maximos"}


def mejor(candidatos, tipo):
    """El mejor de un tipo: por su retraso con 30 semillas si lo tiene, si no por el de 10."""
    lista = [c for c in candidatos if c["tipo"] == tipo and not c.get("coordinado")]
    return min(lista, key=lambda c: (c.get("retraso_total_30", float("inf")), c["retraso_total_10"]))


# Un paso mas alla de cada extremo de los valores probados en la busqueda (estudio.PASOS_ACTUADO y estudio.RETRASO). El
# umbral de atasco no entra: su extremo bajo es "sin umbral" (-1) y en los casos registrados no se trato como borde.
MAS_ALLA = {"retraso": {"detectorRange": {50: 25, 200: 400}, "minTimeLoss": {1: 0.5, 3: 5}},
            "actuado": {"max-gap": {1.0: 0.5, 4.0: 6.0}, "detector-gap": {1.0: 0.5, 4.0: 6.0}}}


def variantes_bordes(candidatos):
    """La regla de la comprobacion del borde escrita de forma general (ovalo, 18.11.2026): para el mejor de cada tipo,
    cada parametro que quedo en un extremo pasa al valor siguiente (MAS_ALLA), de a uno y, si son varios, todos a la
    vez; todo lo demas igual."""
    res = []
    for tipo, reglas in MAS_ALLA.items():
        base = sin_medidas(mejor(candidatos, tipo))
        bordes = {p: mas[base[p]] for p, mas in reglas.items() if base[p] in mas}
        res += [dict(base, **{p: v}) for p, v in bordes.items()]
        if len(bordes) > 1:
            res.append(dict(base, **bordes))
    return res


def probar_reglas():
    """Sin simular: la regla general da las variantes registradas en los cuatro casos de Lima (REGISTRO.md, 14.11.2026,
    15:55; borde_actuado.json de cada carpeta). Los actuado_ajustado.json son los de antes de la comprobacion (en la
    alta del nudo, el ganador registrado antes del borde)."""
    carpeta = os.path.join(AQUI, "ovalo", "entrada", "actuado_estudio")
    clave = lambda v: tuple(sorted((k, x) for k, x in v.items() if k in ("tipo", "detectorRange", "minTimeLoss",  # noqa: E731
                                                                      "max-gap", "detector-gap")))
    ok = True
    for caso in ("nudo_publicada", "nudo_alta", "corredor_publicada", "corredor_alta"):
        with open(os.path.join(carpeta, f"{caso}_actuado_ajustado.json"), encoding="utf-8") as f:
            candidatos = json.load(f)["candidatos"]
        with open(os.path.join(carpeta, f"{caso}_borde_actuado.json"), encoding="utf-8") as f:
            registradas = json.load(f)["variantes"]
        general = sorted(clave(v) for v in variantes_bordes(candidatos))
        iguales = general == sorted(clave(v) for v in registradas)
        ok &= iguales
        print(f"{caso}: {'iguales' if iguales else 'DISTINTAS'}; regla general {general}")
    print("La regla general reproduce las variantes registradas" if ok else "NO reproduce las variantes registradas")
    return ok


def variantes(caso, candidatos):
    """Las variantes un paso mas alla de cada borde, con todo lo demas igual al mejor de su tipo."""
    if caso == "ovalo":
        return variantes_bordes(candidatos)
    retraso = sin_medidas(mejor(candidatos, "retraso"))
    if caso == "nudo":
        return [dict(retraso, detectorRange=a, minTimeLoss=m) for a, m in ((400, 3), (200, 5), (400, 5))]
    return [dict(retraso, detectorRange=100, minTimeLoss=0.5), dict(sin_medidas(mejor(candidatos, "actuado")),
                                                                     **{"max-gap": 0.5})]


def preparar(caso):
    """(estudio del caso, funcion de una corrida, escribir_variante(archivo, v)), como en su ajustar-actuado."""
    import estudio
    if caso in ("nudo", "ovalo"):
        programa = estudio.cargar_programa()
        with open(os.path.join(estudio.SALIDAS, "fijo_ajustado.json"), encoding="utf-8") as f:
            fijo = json.load(f)["ganador"]
        n = len(programa.PLAN)
        maximos = {"60": [estudio.VERDE_MAX] * n,
                   "doble del fijo": [min(estudio.VERDE_MAX, max(m, 2 * g)) for m, g in zip(programa.minimos(), fijo)]}

        def escribir(archivo, v, **extra):
            programa.escribir(archivo, maximos[v["esquema"]], tipo=v["tipo"], parametros=estudio.parametros_sumo(v),
                              **extra)
        escribir.maximos = maximos
        return estudio, estudio._fija, escribir
    import corredor
    import estudio_corredor as ec
    with open(os.path.join(ec.SALIDAS, "fijo_ajustado.json"), encoding="utf-8") as f:
        fijo = json.load(f)
    maximos = {"60": [(ec.VERDE_MAX, ec.VERDE_MAX)] * ec.N,
               "doble del fijo": [(min(ec.VERDE_MAX, max(ec.MIN, 2 * (fijo["ciclo"] - 2 * corredor.AMBAR - t))),
                                   min(ec.VERDE_MAX, max(ec.MIN, 2 * t))) for t in fijo["transversal"]]}

    def escribir(archivo, v, **extra):
        corredor.escribir_programa(archivo, None, None, None, tipo=v["tipo"], maximos=maximos[v["esquema"]],
                                   parametros=estudio.parametros_sumo(v), **extra)
    escribir.maximos = maximos
    return ec, ec._fija, escribir


def instalar(caso, escribir):
    """Si la comprobacion cambio el ganador: escribe el nuevo actuado ajustado y lo pone como ganador en
    actuado_ajustado.json (lo anterior ya se guardo con el sufijo b: REGISTRO.md, 14.11.2026, 15:55)."""
    import estudio
    with open(os.path.join(caso.SALIDAS, "borde_actuado.json"), encoding="utf-8") as f:
        borde = json.load(f)
    if not borde["cambia"]:
        print("No cambia el ganador: nada que instalar")
        return
    gan = borde["ganador"]
    escribir(os.path.join(caso.CARPETA, caso.ARCHIVO["actuadoaj"]), gan, programa="actuado_ajustado",
             comentario="Actuado ajustado (borde_actuado.py, comprobacion del borde): " + estudio.texto_variante(gan))
    ruta = os.path.join(caso.SALIDAS, "actuado_ajustado.json")
    with open(ruta, encoding="utf-8") as f:
        registro = json.load(f)
    registro["ganador"] = dict(gan, maximos=escribir.maximos[gan["esquema"]])
    registro["procedimiento"] += "; despues, un paso mas alla de cada borde (borde_actuado.py)"
    registro["ganador_antes_del_borde"] = borde["ganador_anterior"]
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(registro, f, indent=1)
    print("Instalado: " + estudio.texto_variante(gan))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("caso", nargs="?", choices=("nudo", "corredor", "ovalo"))
    ap.add_argument("--carpeta", default="")
    ap.add_argument("--procesos", type=int, default=3)
    ap.add_argument("--instalar", action="store_true", help="escribir el nuevo ganador, si lo hay")
    ap.add_argument("--probar-reglas", action="store_true", help="no simula: la regla general frente a lo registrado")
    args = ap.parse_args()
    if args.probar_reglas:
        sys.exit(0 if probar_reglas() else 1)
    if not args.caso:
        ap.error("falta el caso (nudo, corredor u ovalo)")
    # la carpeta del nivel de demanda se fija antes de importar los estudios (la leen al importarse)
    os.environ["LIMA_CARPETA" if args.caso in ("nudo", "ovalo") else "CORREDOR_CARPETA"] = args.carpeta
    import estudio
    caso, correr, escribir = preparar(args.caso)
    os.chdir(caso.CARPETA)
    if args.instalar:
        instalar(caso, escribir)
        return
    with open(os.path.join(caso.SALIDAS, "actuado_ajustado.json"), encoding="utf-8") as f:
        busqueda = json.load(f)
    ganador = busqueda["ganador"]
    print(f"{args.caso} {args.carpeta or 'publicada'}: ganador {estudio.texto_variante(ganador)}, "
          f"{ganador['retraso_total_10']:.2f} con 10 semillas y {ganador['retraso_total_30']:.2f} con 30", flush=True)
    medidas = []
    with Pool(args.procesos) as pool:
        def medir(v, semillas):
            archivo = os.path.join(caso.TMP, f"borde_{os.getpid()}_{len(medidas)}.add.xml")
            escribir(archivo, v)
            r = estudio.media(pool.map(correr, [(archivo, s, "bo") for s in semillas]))
            os.remove(archivo)
            print(f"  {estudio.texto_variante(v)}, {len(semillas)} semillas: {r:8.2f} s/veh", flush=True)
            return r
        for v in variantes(args.caso, busqueda["candidatos"]):
            v = dict(v, retraso_total_10=medir(v, estudio.AJUSTE))
            if v["retraso_total_10"] < ganador["retraso_total_10"]:
                v["retraso_total_30"] = medir(sin_medidas(v), estudio.DESEMPATE)
            medidas.append(v)
    nuevo = min([ganador] + [v for v in medidas if "retraso_total_30" in v], key=lambda v: v["retraso_total_30"])
    cambia = nuevo is not ganador
    with open(os.path.join(caso.SALIDAS, "borde_actuado.json"), "w", encoding="utf-8") as f:
        json.dump({"ganador_anterior": ganador, "variantes": medidas, "cambia": cambia,
                   "ganador": nuevo}, f, indent=1)
    print(("CAMBIA el ganador: " if cambia else "No cambia el ganador: ") + estudio.texto_variante(nuevo)
          + f", {nuevo['retraso_total_30']:.2f} s/veh con 30 semillas", flush=True)


if __name__ == "__main__":
    main()
