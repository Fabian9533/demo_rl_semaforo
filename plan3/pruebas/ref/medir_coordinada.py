"""
medir_coordinada.py - Medicion de la variante coordinada (b) "fin fijo" del actuado ajustado (pedido de la verificacion
de 6e8cfab): semilla de humo 424301, sumo directo (hasta 6000 s, como el barrido) con SaveTLSStates, en
dem_red_t3620 (plan 25/15, desfases 0/23/0: la avenida es la fase 0 de la plantilla) y en el corredor (plan
22/15, 0/17: la avenida es la fase 2), con maxDur 60 y con maxDur = los verdes fijos, con el codigo de antes (6e8cfab) y el de ahora. Por semaforo: salidas del
verde de avenida (y las del plan fijo), histograma de (fin de la variante - fin del plan fijo) mod ciclo, y el segundo
del ciclo (0 = el inicio del verde de avenida en el plan fijo) en que empieza cada verde de avenida.
Uso (cwd = plan3/): python pruebas/ref/medir_coordinada.py      Salida: pruebas/ref/salidas/medir_coordinada.txt
"""
import os
import sys
import json
import types
import collections
import subprocess
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
inf = up.Informe("medir_coordinada")
CASOS = [("dem_red_t3620", (25, 15, [0, 23, 0])), ("corredor", (22, 15, [0, 17]))]
CARPETA = up.copia("medir_coordinada", [e for e, _ in CASOS])
import barrer_fino as bfn  # noqa: E402
import actuado  # noqa: E402

S = 424301
COMMIT_ANTES = "6e8cfab"
texto = subprocess.run(["git", "show", f"{COMMIT_ANTES}:plan3/actuado.py"], cwd=up.RAIZ, capture_output=True,
                       text=True, encoding="utf-8").stdout
ANTES = types.ModuleType("actuado_antes")
ANTES.__file__ = os.path.join(up.PLAN3, "actuado.py")
exec(compile(texto, "actuado_antes", "exec"), ANTES.__dict__)


def correr(c, nombre, adicionales):
    log = os.path.join(CARPETA, f"log_{c.esc}_{nombre}.add.xml")
    with open(log, "w", encoding="utf-8") as f:
        f.write("<additional>\n" + "".join(f'<timedEvent type="SaveTLSStates" source="{x}" '
                                           f'dest="tls_{c.esc}_{nombre}_{x}.xml"/>\n' for x in c.p.ids)
                + "</additional>\n")
    up.sumo_directo(c.cfg, ",".join(adicionales + [log]), S, os.path.join(CARPETA, f"ti_{c.esc}_{nombre}.xml"))
    salida = {}
    for x in c.p.ids:
        cambios, prev = [], None
        for e in ET.parse(f"tls_{c.esc}_{nombre}_{x}.xml").getroot().iter("tlsState"):
            ph = int(e.get("phase"))
            if ph != prev:
                cambios.append((int(float(e.get("time"))), ph))
            prev = ph
        salida[x] = cambios
    return salida


def medir(esc, plan):
    c = bfn.Celda(esc, prefijos=(), permitir=True)
    c.carpeta = os.path.join(CARPETA, "barridos", esc)
    os.makedirs(c.carpeta, exist_ok=True)
    pl = c.plan(*plan)
    fijo = os.path.join(CARPETA, f"{esc}_fijo.add.xml")
    c.escribir_plan(fijo, pl)
    with open(os.path.join(c.carpeta, "fijo_fino.json"), "w", encoding="utf-8") as f:
        json.dump({"ids": c.p.ids, "ciclo": pl["ciclo"], "offsets": pl["offsets"], "verde": pl["verde"],
                   "verde_transversal": pl["verde_transversal"], "sha256": "prueba", "huella": c.huella,
                   "registro": {"prueba": ["plan de la medicion (medir_coordinada)"]}}, f)
    _, _, adic = bfn.rutas_cfg(c.cfg)
    ff = correr(c, "fijo", c.p.extra(fijo)[1].split(","))
    C = pl["ciclo"]
    for maxdur in ("60", "verdes fijos"):
        base = dict(actuado.DEFECTO)
        if maxdur == "60":
            base.update(maxdur_av=60, maxdur_tr=60)
        else:
            base.update(maxdur_av=pl["verde"], maxdur_tr=pl["verde_transversal"])
        for version, mod in (("antes", ANTES), ("ahora", actuado)):
            v = mod.coordinada(c, base, fin_fijo=True)
            ruta = os.path.join(CARPETA, f"{esc}_b_{version}_{maxdur[:2]}.add.xml")
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(mod.texto_actuado(c, v))
            fv = correr(c, f"b_{version}_{maxdur[:2]}", adic + [ruta])
            inf(f"{esc}, plan {pl['clave']} (ciclo {C}), variante (b) con maxDur de la cadena {maxdur}, codigo de "
                f"{version}:")
            for i, x in enumerate(c.p.ids):
                fa = c.p.fases_av[i]
                fin_fijo = sorted({t2 % C for (t, ph), (t2, ph2) in zip(ff[x], ff[x][1:]) if ph == fa and ph2 != fa})
                ini_fijo = sorted({t % C for t, ph in ff[x][1:] if ph == fa})
                n_fijo = sum(1 for (t, ph), (t2, ph2) in zip(ff[x], ff[x][1:]) if ph == fa and ph2 != fa)
                salidas = [t2 for (t, ph), (t2, ph2) in zip(fv[x], fv[x][1:]) if ph == fa and ph2 != fa]
                inicios = [t for t, ph in fv[x][1:] if ph == fa]
                dif = collections.Counter((t - fin_fijo[0]) % C for t in salidas)
                arr = collections.Counter((t - ini_fijo[0]) % C for t in inicios)
                inf(f"  {x}: {len(salidas)} salidas de la avenida (plan fijo: {n_fijo}); en el fin fijo "
                    f"{dif.get(0, 0)}")
                inf(f"      (fin - fin fijo) mod {C}: {dict(sorted(dif.items()))}")
                inf(f"      inicio del verde de avenida (s del ciclo, 0 = inicio fijo): {dict(sorted(arr.items()))}")


def main():
    inf(f"Variante coordinada (b), semilla {S}, hasta 6000 s; antes = {COMMIT_ANTES} (copia en {CARPETA})")
    for esc, plan in CASOS:
        medir(esc, plan)
    os.chdir(up.PLAN3)
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
