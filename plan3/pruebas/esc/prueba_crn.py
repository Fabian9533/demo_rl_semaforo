"""
prueba_crn.py - Pruebas 3 y 4 de los escenarios nuevos (B6): numeros aleatorios comunes con departLane="best".
  3. Con la misma semilla, el fijo, el actuado y el ciclo minimo (rl_corredor por TraCI, como evaluar.py) y la
     politica IPPO con mensajes entregada de su caso (base 42, jugada por TraCI con evaluar.brazo_profundo) ven los
     mismos vehiculos: mismos ids, misma salida pedida (depart - departDelay), mismo speedFactor y mismo tipo. Tambien
     el fijo por sumo puro (como barrer_fijo), que ademas debe dar el mismo tripinfo que el fijo por TraCI. En los 13
     escenarios, semillas de humo 424301 y 424302. mixa_ frente a mix_: mismos vehiculos y tipos (el arranque lento
     no toca el sorteo).
  4. Dos semillas distintas dan llegadas distintas (en P6e, con llegadas regulares, solo cambian los conductores).
Cada brazo corre en un proceso aparte (las dos semillas seguidas, para que dos procesos no escriban a la vez el
<esc>_actuado.add.xml o el _trivial), como mucho 3 a la vez. El proceso registra los escenarios con
con_escenarios.registrar() y agrega --tripinfo-output.write-undeparted a sumo (solo salida: no cambia la simulacion)
para ver tambien a los que no alcanzaron a entrar.
Uso (desde plan3/): python pruebas/esc/prueba_crn.py      Salida: salidas/crn.txt y crn.csv (tripinfo en tmp_esc/crn)
"""
import os
import sys
import csv
import json
import time
import shutil
import subprocess
import concurrent.futures as cf
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_esc as u                       # noqa: E402

SEMILLAS = (424301, 424302)
BRAZOS = ("fijo", "actuado", "trivial", "ippo", "sumo")
CARPETA = os.path.join(u.TMP, "crn")


def tripinfo(esc, brazo, semilla):
    return os.path.join(CARPETA, f"tripinfo_{esc}_{brazo}_{semilla}.xml")


def politica(esc):
    import escenarios_plan3
    caso = escenarios_plan3.RECETAS[esc][0]
    return os.path.join("insumos", "entregado", f"politica_{caso}_vecinos_s42.pt")


def trabajo(esc, brazo):
    """Un brazo en las dos semillas, en este proceso."""
    import con_escenarios
    con_escenarios.registrar()
    import comun
    original = comun.iniciar_sumo
    comun.iniciar_sumo = lambda cmd, *a, **k: original(list(cmd) + ["--tripinfo-output.write-undeparted", "true"],
                                                       *a, **k)
    import evaluar
    if brazo == "ippo":
        correr = evaluar.brazo_profundo(esc, politica(esc), 0, 0.0)[3]
    elif brazo != "sumo":
        correr = evaluar.brazo_referencia(esc, brazo)[3]
    for s in SEMILLAS:
        t0 = time.time()
        if brazo == "sumo":                      # con las opciones de barrer_fijo.correr_sumo
            u.correr_sumo(f"{esc}.sumocfg", s, tripinfo(esc, brazo, s), ["--device.emissions.probability", "1"])
        else:
            correr(u.semilla_humo(s), tripinfo(esc, brazo, s), None)
        print("RESULTADO " + json.dumps({"escenario": esc, "brazo": brazo, "semilla": s,
                                         "segundos": round(time.time() - t0, 1)}), flush=True)


def lanzar(esc, brazo):
    entorno = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "una", esc, brazo], cwd=u.PLAN3,
                       capture_output=True, text=True, env=entorno)
    if r.returncode != 0:
        raise RuntimeError(f"{esc} {brazo}: {r.stderr[-800:]}")
    return [json.loads(l[len("RESULTADO "):]) for l in r.stdout.splitlines() if l.startswith("RESULTADO ")]


def viajes(esc, brazo, s):
    est = u.estadisticas(tripinfo(esc, brazo, s)[:-4] + "_stats.xml")
    return u.leer_viajes(tripinfo(esc, brazo, s), est["fin"]), est


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "una":
        trabajo(sys.argv[2], sys.argv[3])
        return
    os.chdir(u.PLAN3)
    shutil.rmtree(CARPETA, ignore_errors=True)
    os.makedirs(CARPETA)
    nombres = u.escenarios()
    p = u.Salida("crn.txt")
    fallas = []

    def ok(cond, texto):
        p(("  ok    " if cond else "  FALLA ") + texto)
        if not cond:
            fallas.append(texto)

    tiempos = []
    with cf.ThreadPoolExecutor(u.MAX_SUMO) as pool:
        for res in pool.map(lambda t: lanzar(*t), [(e, b) for e in nombres for b in BRAZOS]):
            tiempos += res
    p(f"3. Numeros aleatorios comunes con departLane=best, semillas {SEMILLAS[0]} y {SEMILLAS[1]} (frente al fijo "
      f"por TraCI): ids, salida pedida, speedFactor y tipo")
    filas = []
    for esc in nombres:
        for s in SEMILLAS:
            fijo, est_f = viajes(esc, "fijo", s)
            partes = []
            todo = True
            for b in BRAZOS[1:]:
                otro, est = viajes(esc, b, s)
                c = u.comparar_llegadas(fijo, otro)
                bien = c["solo_uno"] == 0 and c["deseada_distinta"] == 0 and c["sf_distinto"] == 0 and \
                    c["tipo_distinto"] == 0 and c["mismo_orden"]
                todo &= bien
                partes.append(f"{b} {'=' if bien else 'DISTINTO ' + str(c)}")
                filas.append({"escenario": esc, "semilla": s, "brazo": b, **c,
                              "espera_entrar_fijo": round(sum(v["dd"] for v in fijo.values()) / len(fijo), 2),
                              "espera_entrar_brazo": round(sum(v["dd"] for v in otro.values()) / len(otro), 2),
                              "no_insertados_fijo": est_f["waiting"], "no_insertados_brazo": est["waiting"]})
            ok(todo, f"{esc:16s} {s}: {len(fijo)} vehiculos; " + ", ".join(partes))
            igual = [ET.tostring(v) for v in ET.parse(tripinfo(esc, "fijo", s)).getroot().iter("tripinfo")] == \
                [ET.tostring(v) for v in ET.parse(tripinfo(esc, "sumo", s)).getroot().iter("tripinfo")]
            ok(igual, f"{esc:16s} {s}: el fijo por sumo puro (como barrer_fijo) da el mismo tripinfo que por "
                      f"TraCI, vehiculo por vehiculo y con sus emisiones")
    p("   mixa_ frente a mix_ (fijo, misma semilla): el arranque lento no cambia vehiculos ni tipos")
    for caso in ("corredor", "red"):
        for s in SEMILLAS:
            c = u.comparar_llegadas(viajes(f"mix_{caso}", "fijo", s)[0], viajes(f"mixa_{caso}", "fijo", s)[0])
            ok(c["solo_uno"] == 0 and c["deseada_distinta"] == 0 and c["sf_distinto"] == 0 and c["tipo_distinto"] == 0,
               f"mixa_{caso} = mix_{caso} en {s}: {c}")

    p("4. Dos semillas distintas dan llegadas distintas (fijo, 424301 frente a 424302)")
    for esc in nombres:
        a, b = viajes(esc, "fijo", SEMILLAS[0])[0], viajes(esc, "fijo", SEMILLAS[1])[0]
        c = u.comparar_llegadas(a, b)
        comunes = len(set(a) & set(b))
        texto = (f"{esc:16s} vehiculos {c['n_a']} y {c['n_b']}; de {comunes} ids comunes, salida pedida distinta en "
                 f"{c['deseada_distinta']} y speedFactor distinto en {c['sf_distinto']}")
        if esc == "malla3_alta_e":
            ok(c["n_a"] == c["n_b"] and c["deseada_distinta"] == 0 and c["sf_distinto"] > 0,
               texto + " (llegadas regulares: mismas salidas, otros conductores)")
        else:
            ok(c["deseada_distinta"] > 0.9 * comunes, texto)
    with open(os.path.join(u.SALIDAS, "crn.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    p(f"(tiempo por episodio: mediana {sorted(t['segundos'] for t in tiempos)[len(tiempos) // 2]} s, "
      f"maximo {max(t['segundos'] for t in tiempos)} s; {len(tiempos)} episodios)")
    u.limpiar_generados()
    p(f"\nResultado: {'TODO OK' if not fallas else f'{len(fallas)} FALLAS'}")
    p.guardar()
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
