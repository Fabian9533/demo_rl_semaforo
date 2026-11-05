"""
prueba_k_humo.py - Evidencia de punta a punta del hallazgo 10 (cambios de fase de rl_ippo, k por plantilla), con
semillas de humo (424301-424303; nunca las de examen ni las de la prueba final). Adaptado de los guiones de la revision
del 05.11 (rev_ver/A-k-empirico/scripts: e2e.py y e2e_todas.py).

Corre evaluar3.py de verdad (por ../con_escenarios.py, como en la noche) con TraCI instrumentado solo con lecturas:
getPhase antes del primer paso y despues de cada paso, y un registro de setPhase y setProgram. No cambia la simulacion.
Cuenta aparte las entradas reales a un verde despues del arranque y las compara con cambios_fase del CSV:
CSV - real = lo que el contador agrega. Para los brazos de rl_ippo tiene que ser k (veredicto3.k_plantilla); para los
de rl_corredor, 0.
  1. --regla regla_u3g60 (rl_ippo) en las 32 plantillas del generador, semilla 424301.
  2. corredor y red, semillas 424301-424303: la regla, la politica entregada de la base 42 (rl_ippo) y el fijo
     (rl_corredor).
Un SUMO a la vez. Escribe solo en tmp_ver/k_humo/ (ignorada por git) y en pruebas/ver/salidas/prueba_k_humo.txt.

Uso (cwd = plan3/):
  python -B pruebas/ver/prueba_k_humo.py                                 todas las corridas y el resumen
  python -B pruebas/ver/prueba_k_humo.py --una LOG.json -- <args de evaluar3.py>   una corrida (la usa el anterior)
"""
import os
import sys
import csv
import json
import subprocess

sys.dont_write_bytecode = True
AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN3 = os.path.dirname(os.path.dirname(AQUI))
RAIZ = os.path.dirname(PLAN3)
TMP = os.path.join(PLAN3, "tmp_ver", "k_humo")
SALIDA = os.path.join(AQUI, "salidas", "prueba_k_humo.txt")
HUMO = (424301, 424303)                    # bloque de humo del prerregistro (§3): 424301-424360


def una(log_path, args3):
    """Una corrida de evaluar3 con TraCI instrumentado; escribe el log y devuelve los resultados por semilla."""
    sys.path.insert(0, RAIZ)
    import traci
    episodios = []
    real_start, real_step = traci.start, traci.simulationStep
    real_set, real_setprog = traci.trafficlight.setPhase, traci.trafficlight.setProgram

    def verdes_activas(tls):
        activo = traci.trafficlight.getProgram(tls)
        logica = next(lg for lg in traci.trafficlight.getAllProgramLogics(tls) if lg.programID == activo)
        return activo, [i for i, p in enumerate(logica.phases)
                        if ("G" in p.state or "g" in p.state) and "y" not in p.state]

    def start(cmd, *a, **k):
        r = real_start(cmd, *a, **k)
        ep = {"pasos": 0, "t0": {}, "pre1": None, "serie": [], "sets": [], "setprog": []}
        for tls in traci.trafficlight.getIDList():
            ep["t0"][tls] = traci.trafficlight.getPhase(tls)      # fase de la plantilla a t = 0
        episodios.append(ep)
        return r

    def step(*a, **k):
        ep = episodios[-1]
        if ep["pre1"] is None:                                     # despues del arranque (setPhase inicial)
            ep["pre1"] = {tls: traci.trafficlight.getPhase(tls) for tls in traci.trafficlight.getIDList()}
            ep["verdes"], ep["programa"] = {}, {}
            for tls in traci.trafficlight.getIDList():
                ep["programa"][tls], ep["verdes"][tls] = verdes_activas(tls)
        r = real_step(*a, **k)
        ep["pasos"] += 1
        ep["serie"].append([traci.trafficlight.getPhase(tls) for tls in sorted(ep["pre1"])])
        return r

    def set_phase(tls, idx):
        episodios[-1]["sets"].append((episodios[-1]["pasos"], tls, int(idx)))
        return real_set(tls, idx)

    def set_prog(tls, prog):
        episodios[-1]["setprog"].append((episodios[-1]["pasos"], tls, prog))
        return real_setprog(tls, prog)

    traci.start, traci.simulationStep = start, step
    traci.trafficlight.setPhase, traci.trafficlight.setProgram = set_phase, set_prog
    import con_escenarios
    sys.argv = ["con_escenarios.py", "evaluar3.py"] + args3
    con_escenarios.main()
    salida = args3[args3.index("--salida") + 1]
    with open(salida, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    res = []
    for ep, fila in zip(episodios, filas):
        tl = sorted(ep["pre1"])

        def contar(inicio):
            n, prev = 0, [inicio[t] for t in tl]
            for fila_f in ep["serie"]:
                for j, t in enumerate(tl):
                    if fila_f[j] != prev[j] and fila_f[j] in ep["verdes"][t]:
                        n += 1
                prev = list(fila_f)
            return n
        res.append({"semilla": int(fila["semilla"]), "brazo": fila["brazo"],
                    "cambios_fase_csv": float(fila["cambios_fase"]), "real": contar(ep["pre1"]),
                    "fuera_t0": sum(1 for t in tl if ep["t0"][t] not in ep["verdes"][t][:1]),
                    "pasos": ep["pasos"]})
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    return res


def corridas():
    """(escenario, args de evaluar3, que) de todas las corridas."""
    sys.path.insert(0, PLAN3)
    sys.path.insert(0, RAIZ)
    import generar_trabajos3 as gt
    escs = sorted(set(list(gt.CASOS.values()) + list(gt.NIVELES.values()) + list(gt.D.values())
                      + list(gt.P6E.values()) + list(gt.POI.values()) + list(gt.PERFIL.values())
                      + list(gt.MEZCLA.values()) + list(gt.MEZCLA_A.values())))
    lista = [(e, f"{HUMO[0]}", ["--regla", "regla_u3g60"], "regla") for e in escs]
    for e in ("corredor", "red"):
        semillas = f"{HUMO[0]}-{HUMO[1]}"
        lista += [(e, semillas, ["--regla", "regla_u3g60"], "regla"),
                  (e, semillas, ["--politica", f"insumos/entregado/politica_{e}_vecinos_s42.pt"], "entregado"),
                  (e, semillas, ["--brazo", "fijo"], "fijo")]
    return lista


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--una":
        assert sys.argv[3] == "--"
        una(sys.argv[2], sys.argv[4:])
        return
    if os.path.abspath(os.getcwd()) != PLAN3:
        raise SystemExit(f"correr desde {PLAN3}")
    sys.path.insert(0, PLAN3)
    sys.path.insert(0, RAIZ)
    import veredicto3 as v3
    os.makedirs(TMP, exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    lineas, malas, buenas = [], 0, 0
    lineas.append("Hallazgo 10: cambios_fase del CSV de evaluar3 menos las entradas reales a un verde (TraCI), "
                  "semillas de humo")
    lineas.append(f"{'escenario':26s} {'que':9s} {'brazo':34s} {'semilla':>7s} {'csv':>6s} {'real':>6s} "
                  f"{'csv-real':>8s} {'k esperado':>10s} {'fuera t0':>8s}  resultado")
    for esc, semillas, brazo, que in corridas():
        nombre = f"{esc}_{que}_{semillas.replace('-', '_')}"
        log = os.path.join(TMP, f"{nombre}.json")
        salida = os.path.join("tmp_ver", "k_humo", f"eval_{nombre}.csv")
        with open(os.path.join(TMP, f"{nombre}.log"), "w", encoding="utf-8") as f:
            rc = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--una", log, "--",
                                 "--escenario", esc, "--semillas", semillas, "--salida", salida] + brazo,
                                cwd=PLAN3, env=env, stdout=f, stderr=subprocess.STDOUT).returncode
        try:
            res = json.load(open(log, encoding="utf-8"))
        except (OSError, ValueError):
            res = []
        if rc != 0 or not res:
            malas += 1
            lineas.append(f"{esc:26s} {que:9s} ERROR rc={rc} (ver tmp_ver/k_humo/{nombre}.log)")
            continue
        esperado = v3.k_plantilla(esc) if que != "fijo" else 0
        for r in res:
            dif = r["cambios_fase_csv"] - r["real"]
            bien = dif == esperado
            malas += not bien
            buenas += bien
            lineas.append(f"{esc:26s} {que:9s} {r['brazo'][:34]:34s} {r['semilla']:7d} {r['cambios_fase_csv']:6.0f} "
                          f"{r['real']:6d} {dif:8.0f} {esperado:10d} {r['fuera_t0']:8d}  {'OK' if bien else 'MAL'}")
        print(lineas[-1], flush=True)
    lineas.append(f"=== {buenas} OK, {malas} MAL")
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas) + "\n")
    print(lineas[-1])
    sys.exit(1 if malas else 0)


if __name__ == "__main__":
    main()
