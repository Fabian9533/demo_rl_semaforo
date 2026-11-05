"""
tabla_coordinadas.py - La tabla de informe_ref §6.5: las dos variantes coordinadas del actuado ajustado frente al fijo
y al actuado, con el fijo entregado (la plantilla) como "fijo fino", en P1, P2, P3 y P6, y con dos planes cuya
transversal tiene holgura (puede cortar antes que en el plan fijo): P1 con 22/15 y el nivel dem_red_t3620 con 25/15
(el ejemplo de la verificacion de 6e8cfab); semilla de humo 424301,
sumo directo (el programa encima de los adicionales, como el barrido). Para (a) y (b), el codigo de antes (el
actuado.py de 6e8cfab, sacado con git show) y el de ahora (cuenta del ciclo desde el inicio de la transversal y maxDur
de la avenida no menor que lo que necesita), con los parametros por defecto (maxDur 60). Ademas, por variante, cuantas
salidas del verde de avenida caen en el fin del plan fijo (SaveTLSStates), en el semaforo que peor sale.
Uso (cwd = plan3/): python pruebas/ref/tabla_coordinadas.py     Salida: pruebas/ref/salidas/tabla_coordinadas.txt
"""
import os
import sys
import json
import types
import subprocess
import concurrent.futures
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
inf = up.Informe("tabla_coordinadas")
CASOS = [("P1", "corredor", None), ("P2", "corredor_alta", None), ("P3", "red", None), ("P6", "malla3_alta", None),
         ("P1, plan 22/15 0/17", "corredor", (22, 15, [0, 17])),
         ("dem_red_t3620, plan 25/15 0/23/0", "dem_red_t3620", (25, 15, [0, 23, 0]))]
CARPETA = up.copia("coordinadas", sorted({e for _, e, _ in CASOS}))
import barrer_fino as bfn  # noqa: E402
import actuado  # noqa: E402
import comun  # noqa: E402

S = up.HUMO[0]
COMMIT_ANTES = "6e8cfab"


def modulo_de_antes():
    texto = subprocess.run(["git", "show", f"{COMMIT_ANTES}:plan3/actuado.py"], cwd=up.RAIZ, capture_output=True,
                           text=True, encoding="utf-8").stdout
    mod = types.ModuleType("actuado_antes")
    mod.__file__ = os.path.join(up.PLAN3, "actuado.py")
    exec(compile(texto, "actuado_antes", "exec"), mod.__dict__)
    return mod


ANTES = modulo_de_antes()


def celda(esc, plan=None):
    c = bfn.Celda(esc, prefijos=(), permitir=True)
    c.carpeta = os.path.join(CARPETA, "barridos", esc)
    os.makedirs(c.carpeta, exist_ok=True)
    i = 0
    fases = [f for f in c.p.tls[i] if f.tag == "phase"]
    av = int(fases[c.p.fases_av[i]].get("duration"))
    tr = int(next(f.get("duration") for k, f in enumerate(fases)
                  if bfn.bf.es_verde(f.get("state")) and k != c.p.fases_av[i]))
    pl = c.plan(av, tr, [int(tl.get("offset")) for tl in c.p.tls]) if plan is None else c.plan(*plan)
    av, tr = pl["verde"], pl["verde_transversal"]
    with open(os.path.join(c.carpeta, "fijo_fino.json"), "w", encoding="utf-8") as f:
        json.dump({"ids": c.p.ids, "ciclo": pl["ciclo"], "offsets": pl["offsets"], "verde": av,
                   "verde_transversal": tr, "sha256": "prueba", "huella": c.huella,
                   "registro": {"prueba": ["el fijo entregado como fijo fino (tabla_coordinadas)"]}}, f)
    return c, pl


def correr(c, nombre, adicionales):
    """sumo directo con SaveTLSStates: (retraso total, {tls: [(t, fase)]})."""
    log = os.path.join(CARPETA, f"log_{c.esc}_{nombre}.add.xml")
    with open(log, "w", encoding="utf-8") as f:
        f.write("<additional>\n" + "".join(f'<timedEvent type="SaveTLSStates" source="{x}" '
                                           f'dest="tls_{c.esc}_{nombre}_{x}.xml"/>\n' for x in c.p.ids)
                + "</additional>\n")
    res = up.sumo_directo(c.cfg, ",".join(adicionales + [log]), S, os.path.join(CARPETA, f"ti_{c.esc}_{nombre}.xml"))
    fases = {}
    for x in c.p.ids:
        cambios, prev = [], None
        for e in ET.parse(f"tls_{c.esc}_{nombre}_{x}.xml").getroot().iter("tlsState"):
            ph = int(e.get("phase"))
            if ph != prev:
                cambios.append((int(float(e.get("time"))), ph))
            prev = ph
        fases[x] = cambios
    return res["retraso_total_prom"], fases


def fines(c, fases, k_tls):
    fa = c.p.fases_av[k_tls]
    return [t2 for (t, ph), (t2, ph2) in zip(fases, fases[1:]) if ph == fa and ph2 != fa]


def caso(nombre_caso, esc, plan):
    c, pl = celda(esc, plan)
    _, _, adic = bfn.rutas_cfg(c.cfg)
    if plan is None:
        fijo = list(adic)
    else:                                  # el plan fijo reemplaza a la plantilla, como en el barrido
        ruta = os.path.join(CARPETA, f"{esc}_fijo_{pl['clave']}.add.xml")
        c.escribir_plan(ruta, pl)
        fijo = c.p.extra(ruta)[1].split(",")
    base = dict(actuado.DEFECTO)
    programas = {}
    for etiqueta, mod, fin in (("a_antes", ANTES, False), ("a", actuado, False), ("b_antes", ANTES, True),
                               ("b", actuado, True)):
        v = mod.coordinada(c, base, fin_fijo=fin)
        ruta = os.path.join(CARPETA, f"{esc}_{etiqueta}.add.xml")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(mod.texto_actuado(c, v))
        programas[etiqueta] = ruta
    ruta = os.path.join(CARPETA, f"{esc}_actuado_defecto.add.xml")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(actuado.texto_actuado(c, dict(base)))
    programas["actuado"] = ruta
    trabajos = {"fijo": fijo}
    trabajos.update({k: adic + [r] for k, r in programas.items()})
    with concurrent.futures.ThreadPoolExecutor(3) as ex:
        res = dict(zip(trabajos, ex.map(lambda kv: correr(c, kv[0], kv[1]), trabajos.items())))
    C = pl["ciclo"]
    alineado = {}
    for k in ("a_antes", "a", "b_antes", "b"):
        peor = None
        for i, x in enumerate(c.p.ids):
            fijos = {t % C for t in fines(c, res["fijo"][1][x], i)}
            mios = fines(c, res[k][1][x], i)
            en_fin = sum(1 for t in mios if t % C in fijos)
            if peor is None or en_fin / max(1, len(mios)) < peor[0] / max(1, peor[1]):
                peor = (en_fin, len(mios))
        alineado[k] = peor
    n_fijo = min(len(fines(c, res["fijo"][1][x], i)) for i, x in enumerate(c.p.ids))
    return {k: v[0] for k, v in res.items()}, alineado, n_fijo


def main():
    inf(f"Variantes coordinadas del actuado con el fijo entregado como fino (semilla {S}; antes = {COMMIT_ANTES}; "
        f"copia en {CARPETA})")
    inf("retraso total (s/veh); entre parentesis, salidas del verde de avenida en el fin del plan fijo / salidas, en el "
        "semaforo que peor sale")
    inf("| | fijo | actuado | coordinada (a) antes | (a) ahora | coordinada (b) antes | (b) ahora |")
    inf("|---|---|---|---|---|---|---|")
    for nombre, esc, plan in CASOS:
        r, al, n_fijo = caso(nombre, esc, plan)
        celda_txt = {k: f"{r[k]} ({al[k][0]}/{al[k][1]})" for k in al}
        inf(f"| {nombre} | {r['fijo']} ({n_fijo} salidas) | {r['actuado']} | {celda_txt['a_antes']} | {celda_txt['a']} | "
            f"{celda_txt['b_antes']} | {celda_txt['b']} |")
    os.chdir(up.PLAN3)
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
