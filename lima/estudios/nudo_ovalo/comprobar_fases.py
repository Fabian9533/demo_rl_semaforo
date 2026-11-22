"""
comprobar_fases.py - Comprueba, segundo a segundo, las luces del nudo en la red del Ovalo Vasco en una traza de
rl_ippo.py (--traza-fases): que cada cambio lleve su ambar de 3 s, que toda entrada a 28 de Julio y Balboa vaya
precedida de los 34 s de todo rojo (y ningun todo rojo en otro lado), los verdes de 10 a 60 s y el tope de rojo, y
cuenta los pasos que no siguen el orden del plan. Sirve para el modelo de orden libre y para el de orden fijo.

Es el comprobador de la prueba del orden libre (orden_libre_2026-11-17/comprobar_fases.py, sha256 465c94613bf83ef8)
adaptado al ovalo (18.11.2026). Alli las luces de cada estado eran una sola cadena; en el ovalo dependen del estado
anterior (quien quedo adentro sale primero), asi que cada verde, su ambar y el todo rojo se comparan con la cadena que
toca segun de donde se viene.

Uso (desde cualquier carpeta):
  python comprobar_fases.py --traza traza.csv [--red demo_rl/lima/lima.net.xml] [--meta politica.json]
                            [--csv resultados.csv] [--salida informe.txt]

No usa nada de rl_ippo.py: las cadenas esperadas salen de las reglas del plan sobre la red (demo_rl/lima/ovalo/
plan_ovalo.py: letras_verde, ambar, rojo; con el PLAN, TRANSICION, ROJO_TOTAL y VERDE_MAX de lima/programa.py):
  - verde del estado k viniendo del estado p: Plan.letras_verde(k, movimientos de p); tras el todo rojo, sin despeje;
  - ambar: TRANSICION s, Plan.ambar del verde que termina;
  - todo rojo: ROJO_TOTAL s, Plan.rojo del estado que termino, solo antes de 28 de Julio y Balboa;
  - verde minimo: programa.verde_minimo (10 s); maximo: programa.VERDE_MAX (60 s);
  - tope de rojo: (estados - 1) * VERDE_MAX + estados * TRANSICION + la suma de ROJO_TOTAL (163 s);
  - esperar: al menos un vehiculo detenido en los detectores E2 (columnas det_<carril> de la traza) de los carriles de
    entrada del estado. Reloj del tope: segundos seguidos en rojo con alguien esperando.
Cada fila de la traza es un segundo: las luces que hubo en ese paso de la simulacion y los detenidos al terminarlo.
--meta: compara el tope, los minimos, el rojo previo y los carriles que instalo rl_ippo.py con los de aqui.
Sale con 1 si alguna comprobacion falla (el tope se informa y tambien cuenta como falla).
"""
import argparse
import csv
import json
import os
import statistics
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "demo_rl", "lima", "ovalo"))
import plan_ovalo as po                 # noqa: E402  (y con el, lima/programa.py)
import programa                         # noqa: E402

NOMBRES = ["Reducto de frente", "giros de Reducto", "28 de Julio y Balboa"]
TRAS_EL_ROJO = po.TRAS_EL_ROJO


def plan(ruta_red):
    """Lo que dice el plan del nudo en el ovalo: cadenas de verde, ambar y todo rojo por caso, carriles de entrada de
    cada estado, minimos, rojo previo y tope."""
    p = po.Plan(ruta_red)
    n = len(p.plan)
    rojo_antes = p.rojo_antes()
    verde, ambar = {}, {}
    for k in range(n):
        for previo in p.previos(k):
            despeje = set() if previo == TRAS_EL_ROJO else p.estados[previo]
            letras = p.letras_verde(k, despeje)
            verde[(k, previo)] = letras
            ambar[(k, previo)] = p.ambar(letras)
    # todo rojo tras el estado k: solo si hay otro estado con todo rojo antes (tras 28 de Julio y Balboa nunca va)
    rojo = {k: p.rojo(k) for k in range(n) if any(rojo_antes[j] and j != k for j in range(n))}
    por_letras = {}
    for clave, letras in verde.items():
        por_letras.setdefault(letras, []).append(clave)
    entradas = {l.getID() for e in po.ENTRADA for l in p.red.net.getEdge(e).getLanes()}
    carriles = []
    for k in range(n):
        letras = verde[(k, p.previo_del_plan(k))]
        carriles.append(sorted({p.red.enlaces[i]["desde"] for i, c in enumerate(letras)
                                if c in "Gg" and p.red.enlaces[i]["desde"] in entradas}))
    minimos = [programa.verde_minimo(verde[(k, p.previo_del_plan(k))]) for k in range(n)]
    tope = (n - 1) * programa.VERDE_MAX + n * programa.TRANSICION + sum(programa.ROJO_TOTAL.values())
    return {"verde": verde, "ambar": ambar, "rojo": rojo, "por_letras": por_letras, "carriles": carriles,
            "rojo_antes": rojo_antes, "duracion_ambar": programa.TRANSICION, "minimos": minimos,
            "maximo": programa.VERDE_MAX, "tope": tope, "n": n, "avisos": sorted(set(p.avisos))}


def leer_traza(ruta):
    """{(modo, semilla): [(t, luces, {carril: detenidos})]} en el orden del archivo."""
    episodios = {}
    with open(ruta, newline="") as f:
        lector = csv.reader(f)
        cab = next(lector)
        luces = [c for c in cab if c.startswith("luces_")]
        assert len(luces) == 1, f"la traza tiene {len(luces)} semaforos; aqui se comprueba solo el nudo"
        k_luces = cab.index(luces[0])
        dets = [(i, c[len("det_"):]) for i, c in enumerate(cab) if c.startswith("det_")]
        for fila in lector:
            clave = (fila[0], int(fila[1]))
            episodios.setdefault(clave, []).append((int(fila[2]), fila[k_luces], {l: int(fila[i]) for i, l in dets}))
    return episodios


def comprobar_episodio(p, filas):
    """Recorre un episodio; devuelve las cuentas y la lista de fallas (texto)."""
    n, fallas = p["n"], []
    ts = [t for t, _, _ in filas]
    if ts != list(range(ts[0], ts[0] + len(ts))):
        fallas.append("faltan segundos en la traza")
    tramos = []                                 # [cadena, primera fila, filas]
    for k, (_, luz, _) in enumerate(filas):
        if tramos and tramos[-1][0] == luz:
            tramos[-1][2] += 1
        else:
            tramos.append([luz, k, 1])
    rojos = set(p["rojo"].values())
    tipo = []
    for luz, primera, _ in tramos:
        if luz in p["por_letras"]:
            tipo.append(("verde", p["por_letras"][luz]))
        elif luz in rojos:
            tipo.append(("rojo", None))
        elif "y" in luz:
            tipo.append(("ambar", None))
        else:
            tipo.append(("otra", None))
            fallas.append(f"luces desconocidas en t={filas[primera][0]}: {luz}")
    # el episodio empieza en el verde de Reducto de frente, con las luces del plan (como si viniera de su anterior)
    inicio = (0, (0 - 1) % n if not p["rojo_antes"][0] else TRAS_EL_ROJO)
    if tipo[0][0] != "verde" or inicio not in tipo[0][1]:
        fallas.append("el episodio no empieza en el verde de Reducto de frente del plan")
    actual = inicio                             # (estado, estado anterior) del verde que se recorre
    pasos, verdes_dur = {}, {k: [] for k in range(n)}
    k = 0
    while k < len(tramos):
        clase = tipo[k][0]
        if clase != "verde":
            fallas.append(f"t={filas[tramos[k][1]][0]}: {clase} sin un verde antes")
            k += 1
            continue
        estado = actual[0]
        ultimo = k == len(tramos) - 1
        dur = tramos[k][2]
        if not ultimo:                          # el ultimo verde lo corta el fin del episodio
            verdes_dur[estado].append(dur)
        elif dur > p["maximo"]:
            fallas.append(f"verde final de {NOMBRES[estado]} de {dur} s")
        if ultimo:
            break
        j = k + 1                               # transicion: ambar, quiza todo rojo, y el verde siguiente
        if tipo[j][0] != "ambar":
            fallas.append(f"t={filas[tramos[j][1]][0]}: tras el verde de {NOMBRES[estado]} no va ambar ({tipo[j][0]})")
            k = j
            continue
        ambar = tramos[j]
        rojo = tramos[j + 1] if j + 1 < len(tramos) and tipo[j + 1][0] == "rojo" else None
        sig = j + (2 if rojo else 1)
        t_ambar = filas[ambar[1]][0]
        if ambar[0] != p["ambar"][actual]:
            fallas.append(f"t={t_ambar}: ambar distinto del que toca tras {NOMBRES[estado]}")
        if sig >= len(tramos):                  # el episodio termino en la transicion
            break
        if tipo[sig][0] != "verde":
            fallas.append(f"t={filas[tramos[sig][1]][0]}: tras la transicion no va un verde ({tipo[sig][0]})")
            k = sig
            continue
        destinos = {d for d, _ in tipo[sig][1]}
        if len(destinos) != 1:
            fallas.append(f"t={t_ambar}: verde que no se sabe de que estado es")
        destino = min(destinos)
        if destino == estado:
            fallas.append(f"t={t_ambar}: de {NOMBRES[estado]} a si mismo")
        if ambar[2] != p["duracion_ambar"]:
            fallas.append(f"t={t_ambar}: ambar de {ambar[2]} s ({NOMBRES[estado]} -> {NOMBRES[destino]})")
        esperado_rojo = p["rojo_antes"][destino]
        if (rojo[2] if rojo else 0) != esperado_rojo:
            fallas.append(f"t={t_ambar}: {rojo[2] if rojo else 0} s todo en rojo antes de {NOMBRES[destino]} "
                          f"(se esperaban {esperado_rojo})")
        if rojo and rojo[0] != p["rojo"][estado]:
            fallas.append(f"t={t_ambar}: todo rojo distinto del que toca tras {NOMBRES[estado]}")
        previo = TRAS_EL_ROJO if esperado_rojo else estado
        if tramos[sig][0] != p["verde"].get((destino, previo)):
            fallas.append(f"t={filas[tramos[sig][1]][0]}: el verde de {NOMBRES[destino]} no es el que toca viniendo "
                          f"de {'el todo rojo' if previo == TRAS_EL_ROJO else NOMBRES[previo]}")
        pasos[(estado, destino)] = pasos.get((estado, destino), 0) + 1
        actual = (destino, previo)
        k = sig
    for estado, durs in verdes_dur.items():
        for d in durs:
            if not p["minimos"][estado] <= d <= p["maximo"]:
                fallas.append(f"verde de {NOMBRES[estado]} de {d} s (limites {p['minimos'][estado]}-{p['maximo']})")
    # tope de rojo: reloj de cada estado, fila por fila
    reloj, rojo = [0] * n, [0] * n
    max_reloj, max_rojo, tarde, filas_pasadas = [0] * n, [0] * n, [0] * n, [0] * n
    verde_previo = None
    for t, luz, det in filas:
        claves = p["por_letras"].get(luz)
        en_verde = claves[0][0] if claves else None
        if en_verde is not None and en_verde != verde_previo and reloj[en_verde] > p["tope"]:
            tarde[en_verde] += 1
        for e in range(n):
            espera = sum(det[l] for l in p["carriles"][e]) > 0
            rojo[e] = 0 if e == en_verde else rojo[e] + 1
            reloj[e] = reloj[e] + 1 if (e != en_verde and espera) else 0
            max_reloj[e], max_rojo[e] = max(max_reloj[e], reloj[e]), max(max_rojo[e], rojo[e])
            filas_pasadas[e] += reloj[e] > p["tope"]
        verde_previo = en_verde
    for e in range(n):
        if filas_pasadas[e]:
            fallas.append(f"tope: {NOMBRES[e]} paso {filas_pasadas[e]} s del tope (reloj maximo {max_reloj[e]} s; "
                          f"{tarde[e]} verdes empezaron tarde)")
    return {"segundos": len(filas), "pasos": pasos, "verdes": verdes_dur, "max_reloj": max_reloj,
            "max_rojo": max_rojo, "tarde": tarde,
            "fuera": sum(v for (a, b), v in pasos.items() if b != (a + 1) % n)}, fallas


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--traza", required=True)
    ap.add_argument("--red", default=os.path.join(AQUI, "demo_rl", "lima", "lima.net.xml"))
    ap.add_argument("--meta", default=None, help="politica o checkpoint .json de un entrenamiento con --orden-libre")
    ap.add_argument("--csv", default=None, help="resultados_*.csv del entrenamiento: segundos por episodio")
    ap.add_argument("--salida", default=None, help="ademas de imprimirlo, escribe el informe aqui")
    args = ap.parse_args()
    p = plan(args.red)
    lineas = [f"Traza: {args.traza}", f"Red: {args.red}",
              f"Plan (lima/programa.py y ovalo/plan_ovalo.py): ambar {p['duracion_ambar']} s; todo en rojo antes de "
              + ", ".join(f"{NOMBRES[k]} {s} s" for k, s in enumerate(p["rojo_antes"]) if s)
              + f"; verdes minimos {p['minimos']} s y maximo {p['maximo']} s; tope de rojo {p['tope']} s; "
              f"{len(p['verde'])} verdes posibles (uno por estado y estado anterior)",
              "Carriles de entrada de cada estado (red): " + "; ".join(f"{NOMBRES[k]}: {', '.join(c)}"
                                                                     for k, c in enumerate(p["carriles"]))]
    total_fallas = len(p["avisos"])
    lineas += [f"AVISO de las reglas: {a}" for a in p["avisos"]]
    if args.meta:
        with open(args.meta, encoding="utf-8") as f:
            meta = json.load(f)
        instalado = meta["orden_libre"]["semaforo_S1"]
        iguales = instalado["tope_rojo"] == p["tope"] and instalado["carriles"] == p["carriles"] \
            and instalado["rojo_antes"] == p["rojo_antes"] and instalado["verde_min"] == p["minimos"]
        lineas.append(f"Lo que instalo rl_ippo.py (meta): tope {instalado['tope_rojo']} s, rojo antes "
                      f"{instalado['rojo_antes']}, minimos {instalado['verde_min']}, programa "
                      f"{instalado.get('programa')}; igual que el plan: {'si' if iguales else 'NO'}")
        total_fallas += not iguales
    resumen = {"pasos": {}, "verdes": {k: [] for k in range(p["n"])}, "max_reloj": [0] * p["n"],
               "max_rojo": [0] * p["n"], "tarde": [0] * p["n"], "fuera": 0, "episodios": 0, "segundos": 0}
    for (modo, semilla), filas in leer_traza(args.traza).items():
        cuenta, fallas = comprobar_episodio(p, filas)
        total_fallas += len(fallas)
        resumen["episodios"] += 1
        resumen["segundos"] += cuenta["segundos"]
        resumen["fuera"] += cuenta["fuera"]
        for par, v in cuenta["pasos"].items():
            resumen["pasos"][par] = resumen["pasos"].get(par, 0) + v
        for e in range(p["n"]):
            resumen["verdes"][e] += cuenta["verdes"][e]
            resumen["max_reloj"][e] = max(resumen["max_reloj"][e], cuenta["max_reloj"][e])
            resumen["max_rojo"][e] = max(resumen["max_rojo"][e], cuenta["max_rojo"][e])
            resumen["tarde"][e] += cuenta["tarde"][e]
        cambios = sum(cuenta["pasos"].values())
        lineas.append(f"{modo} semilla {semilla}: {cuenta['segundos']} s, {cambios} cambios, {cuenta['fuera']} fuera "
                      f"del orden del plan; reloj del tope maximo {cuenta['max_reloj']} s; "
                      + (f"{len(fallas)} FALLAS: " + " | ".join(fallas[:6]) if fallas else "sin fallas"))
    lineas.append("")
    lineas.append(f"Total: {resumen['episodios']} episodios, {resumen['segundos']} s")
    lineas.append("Pasos de un estado al siguiente (desde -> hacia: veces):")
    for (a, b), v in sorted(resumen["pasos"].items()):
        lineas.append(f"  {NOMBRES[a]} -> {NOMBRES[b]}: {v}" + ("" if b == (a + 1) % p["n"] else "   (fuera del orden)"))
    lineas.append(f"Pasos fuera del orden del plan: {resumen['fuera']} de {sum(resumen['pasos'].values())}")
    for e in range(p["n"]):
        d = resumen["verdes"][e]
        texto = f"{len(d)} verdes de {min(d)} a {max(d)} s (medio {statistics.mean(d):.1f})" if d else "ningun verde"
        lineas.append(f"  {NOMBRES[e]}: {texto}; mayor rojo {resumen['max_rojo'][e]} s; mayor reloj del tope "
                      f"{resumen['max_reloj'][e]} s (tope {p['tope']}); verdes que empezaron tarde: {resumen['tarde'][e]}")
    if args.csv:
        with open(args.csv, encoding="utf-8-sig", newline="") as f:
            filas = list(csv.DictReader(f))
        segundos = [float(r["segundos"]) for r in filas]
        lineas.append(f"Segundos por episodio de entrenamiento ({args.csv}): "
                      + ", ".join(f"{s:.1f}" for s in segundos) + f" (mediana {statistics.median(segundos):.1f})")
        libres = [c for c in ("cambios_fuera_orden", "decisiones_tope", "tope_excedido", "rojo_max") if c in filas[0]]
        for c in libres:
            lineas.append(f"  {c} por episodio: " + ", ".join(r[c] for r in filas))
    lineas.append(f"Comprobaciones con falla: {total_fallas}")
    texto = "\n".join(lineas)
    print(texto)
    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as f:
            f.write(texto + "\n")
    return 1 if total_fallas else 0


if __name__ == "__main__":
    sys.exit(main())
