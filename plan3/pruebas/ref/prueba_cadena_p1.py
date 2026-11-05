"""
prueba_cadena_p1.py - La cadena completa de las referencias en P1 (corredor), por la linea de comandos y en la
carpeta de prueba tmp_ref/fino/p1_a/ (despues de prueba_fino.py, que deja ahi la gruesa de una subrejilla con
2001-2003). Desempates y finales con semillas de humo, para no elegir nada con las de ajuste fuera de la cola:
  barrer_fino.py fina, desfases, desempate, fragil y mult5 -> corredor_r10f.add.xml y corredor_m5f.add.xml
  franja.py -> corredor_franja.add.xml;  actuado.py --paso todos -> corredor_actuado_aj.add.xml
  reglas.py -> regla.json y mp.json;  p3_preparar.py corredor (las tres piezas)
Comprueba que cada paso termina con codigo 0 y sus salidas, que el ganador de cada referencia jugado por TraCI (evaluar:
brazo_programa, brazo_referencia franja y actuado_aj, brazo_regla) reproduce su media, que p3_preparar reescribe el
actuado ajustado con el mismo sha256 y que actuado y ciclo minimo salen byte a byte iguales a los del codigo
entregado (comun.py de 223f908).
Uso (cwd = plan3/): python pruebas/ref/prueba_cadena_p1.py     Salida: pruebas/ref/salidas/prueba_cadena_p1.txt
"""
import os
import sys
import json
import types
import statistics
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
inf = up.Informe("prueba_cadena_p1")
CARPETA = os.path.join(up.TMP, "fino", "p1_a")
DES = ["--semillas-desempate", "424301-424310", "--semillas-fragil", "424301-424330"]


def correr(script, *args):
    r = subprocess.run([sys.executable, os.path.join(up.PLAN3, script), *args], cwd=CARPETA, capture_output=True,
                       text=True)
    ultima = [x for x in r.stdout.strip().split("\n") if x][-1] if r.stdout.strip() else ""
    inf.chequeo(r.returncode == 0, f"{script} {' '.join(args)}: codigo {r.returncode}; {ultima}")
    if r.returncode != 0:
        inf(r.stdout[-2000:] + r.stderr[-3000:])
    return r.returncode


def leer(rel):
    with open(os.path.join(CARPETA, rel), encoding="utf-8") as f:
        return json.load(f)


def media_traci(correr_brazo, semillas, nombre):
    vals = []
    for s in semillas:
        ti = os.path.join(CARPETA, f"ti_traci_{nombre}_{s}.xml")
        vals.append(float(correr_brazo(s, ti, None)["retraso_total_prom"]))
    return round(statistics.mean(vals), 2)


def semillas(texto):
    import barrer_fino as bfn
    return bfn.leer_semillas(texto)


def main():
    if not os.path.exists(os.path.join(CARPETA, "barridos", "corredor", "gruesa.csv")):
        raise SystemExit("Corra antes pruebas/ref/prueba_fino.py (deja la gruesa de P1 en tmp_ref/fino/p1_a)")
    inf(f"Cadena de las referencias en P1 (carpeta {CARPETA})")
    for etapa in ("fina", "desfases"):
        correr("barrer_fino.py", "corredor", "--etapa", etapa, "--procesos", "3")
    correr("barrer_fino.py", "corredor", "--etapa", "desempate", "--procesos", "3", *DES)
    correr("barrer_fino.py", "corredor", "--etapa", "fragil", "--procesos", "3", *DES)
    correr("barrer_fino.py", "corredor", "--etapa", "mult5", "--procesos", "3", *DES)
    correr("franja.py", "corredor", "--procesos", "3", "--semillas-final", "424301-424310")
    correr("actuado.py", "corredor", "--paso", "todos", "--procesos", "3", "--semillas", "424301-424303",
           "--semillas-final", "424301-424310")
    correr("reglas.py", "corredor", "--semillas", "424301-424303", "--semillas-final", "424301-424310")
    salidas = ["barridos/corredor/" + x for x in
               ("gruesa.csv", "fina.csv", "desfases.csv", "desempate.csv", "fragil.csv", "mult5.csv",
                "mult5_desempate.csv", "fijo_fino.json", "fijo_mult5.json", "fijo_grueso10.json", "franja.csv",
                "franja_final.csv", "franja.json", "actuado_final.csv", "actuado_aj.json", "reglas_regla.csv",
                "reglas_regla_final.csv", "reglas_mp.csv", "reglas_mp_final.csv", "regla.json", "mp.json")] + \
        [f"corredor_{x}.add.xml" for x in ("r10g", "r10f", "m5f", "franja", "actuado_aj")]
    faltan = [x for x in salidas if not os.path.exists(os.path.join(CARPETA, x))]
    inf.chequeo(not faltan, f"salidas de la cadena: {len(salidas) - len(faltan)}/{len(salidas)} (faltan {faltan})")
    p6 = leer("barridos/corredor/actuado_paso6.json")
    coord = sorted((bool(v.get("fin_fijo")), v["tipo"]) for v in p6["variantes"] if v.get("coordinado"))
    inf.chequeo(coord == [(False, "actuated"), (True, "actuated")],
                f"actuado paso 6: {len(p6['variantes'])} variantes, entre ellas las dos coordinadas (solo earliestEnd "
                f"y earliestEnd = latestEnd en la avenida): {coord}; elegida {p6['elegida'].get('tipo')} "
                f"coordinada={p6['elegida'].get('coordinado')} fin_fijo={p6['elegida'].get('fin_fijo', False)}")

    os.chdir(CARPETA)                      # los brazos leen el escenario de la carpeta actual
    import evaluar
    fino, m5 = leer("barridos/corredor/fijo_fino.json"), leer("barridos/corredor/fijo_mult5.json")
    inf(f"  fijo fino: {fino['clave']} ciclo {fino['ciclo']}, {fino['retraso_total_prom']} en {fino['semillas']}; "
        f"traza {fino['traza']}")
    for nombre, datos, archivo in (("fino", fino, "corredor_r10f.add.xml"), ("mult5", m5, "corredor_m5f.add.xml")):
        _, _, _, cb = evaluar.brazo_programa("corredor", archivo, nombre)
        m = media_traci(cb, semillas(datos["semillas"]), nombre)
        inf.chequeo(m == datos["retraso_total_prom"], f"TraCI fijo_{nombre} ({archivo}): media {m} en "
                                                      f"{datos['semillas']} = {datos['retraso_total_prom']}")
    # la misma evaluacion por la linea de comandos de evaluar.py (brazo fijo_<nombre>)
    salida = os.path.join(CARPETA, "eval_cli_fijo_fino.csv")
    r = subprocess.run([sys.executable, os.path.join(up.RAIZ, "evaluar.py"), "--escenario", "corredor", "--brazo",
                        "fijo", "--programa", "corredor_r10f.add.xml", "--nombre", "fino", "--semillas",
                        "424301-424302", "--salida", salida, "--extras", os.path.join(CARPETA, "extras_cli")],
                       cwd=CARPETA, capture_output=True, text=True)
    import csv
    filas = list(csv.DictReader(open(salida, encoding="utf-8"))) if os.path.exists(salida) else []
    _, _, _, cb = evaluar.brazo_programa("corredor", "corredor_r10f.add.xml", "fino")
    ref = [str(cb(s, os.path.join(CARPETA, f"ti_cli_{s}.xml"), None)["retraso_total_prom"]) for s in (424301, 424302)]
    inf.chequeo(r.returncode == 0 and [f["brazo"] for f in filas] == ["fijo_fino"] * 2
                and [f["retraso_total_prom"] for f in filas] == ref,
                f"evaluar.py --brazo fijo --programa corredor_r10f.add.xml --nombre fino: codigo {r.returncode}, "
                f"brazo {[f['brazo'] for f in filas]}, retraso total "
                f"{[f['retraso_total_prom'] for f in filas]} = {ref}")
    fr = leer("barridos/corredor/franja.json")
    _, _, _, cb = evaluar.brazo_referencia("corredor", "franja", "corredor_franja.add.xml")
    m = media_traci(cb, semillas(fr["semillas"]), "franja")
    inf.chequeo(m == fr["retraso_total_prom"], f"TraCI franja ({[p['clave'] for p in fr['programas']]}, cambios "
                                               f"{fr['instantes']}): media {m} = {fr['retraso_total_prom']}")
    aj = leer("barridos/corredor/actuado_aj.json")
    _, _, _, cb = evaluar.brazo_referencia("corredor", "actuado_aj", "corredor_actuado_aj.add.xml")
    m = media_traci(cb, semillas(aj["semillas"]), "actuado_aj")
    inf.chequeo(m == aj["retraso_total_prom"], f"TraCI actuado_aj ({aj['clave']}): media {m} = "
                                               f"{aj['retraso_total_prom']}")
    for archivo in ("regla.json", "mp.json"):
        rg = leer(f"barridos/corredor/{archivo}")
        _, _, _, cb = evaluar.brazo_regla("corredor", rg["regla"])
        m = media_traci(cb, semillas(rg["semillas"]), rg["regla"])
        inf.chequeo(m == rg["retraso_total_prom"], f"evaluar --regla {rg['regla']}: media {m} = "
                                                   f"{rg['retraso_total_prom']} (el barrido de reglas ya era TraCI)")

    # p3_preparar: reescribe el actuado ajustado igual y deja actuado y ciclo minimo como el codigo entregado
    sha_aj = up.sha256("corredor_actuado_aj.add.xml")
    for f in ("corredor_actuado.add.xml", "corredor_trivial.add.xml"):
        if os.path.exists(f):
            os.remove(f)
    correr("p3_preparar.py", "corredor")
    inf.chequeo(up.sha256("corredor_actuado_aj.add.xml") == sha_aj == aj["sha256"],
                f"p3_preparar reescribe corredor_actuado_aj.add.xml con el mismo sha256 ({sha_aj[:16]})")
    viejo = subprocess.run(["git", "show", "223f908:comun.py"], capture_output=True, text=True,
                           cwd=up.RAIZ, encoding="utf-8").stdout
    mod = types.ModuleType("comun_entregado")
    exec(compile(viejo, "comun_entregado", "exec"), mod.__dict__)
    import shutil
    import rl_corredor as rc
    os.makedirs("entregado", exist_ok=True)
    for f in up.archivos_de_cfg("corredor.sumocfg"):          # el codigo entregado lee la red desde la carpeta actual
        shutil.copyfile(f, os.path.join("entregado", f))
    os.chdir("entregado")
    tls = list(rc.ESCENARIOS["corredor"]["semaforos"])
    mod.archivo_actuado("corredor.sumocfg", "corredor", tls, rc.VERDE_MIN, rc.VERDE_MIN_GIRO, rc.VERDE_MAX)
    mod.archivo_trivial("corredor.sumocfg", "corredor", tls, rc.VERDE_MIN, rc.VERDE_MIN_GIRO)
    os.chdir(CARPETA)
    for f in ("corredor_actuado.add.xml", "corredor_trivial.add.xml"):
        a, b = up.sha256(f), up.sha256(os.path.join("entregado", f))
        inf.chequeo(a == b, f"p3_preparar {f} = el del comun.py entregado, byte a byte ({a[:16]})")
    os.chdir(up.PLAN3)
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
