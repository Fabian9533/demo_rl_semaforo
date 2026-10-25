"""
generar_trabajos.py - Escribe cola/trabajos.jsonl con todos los trabajos del plan de pruebas v2.

Uso (desde demo_rl/plan2):  python generar_trabajos.py

Prioridad (menor = antes). Lo imprescindible primero, para que si la noche no alcanza lo que
quede sin correr sea lo opcional:
  0  preparar escenarios          1  barridos del fijo y todas las evaluaciones
  2  P1-P3: IPPO x3 y Q-learning  3  P4 y P5: IPPO x3 y Q-learning
  4  SARSA en P1-P5               5  DQN en P1-P4
  6  MAPPO en P1-P4
  7  Q-learning con recompensa de colas (ablacion) en P1-P4
  (DQN y MAPPO en P5 subieron a 5 el 25.09 a las 00:35)
27.09.2026: re-medicion v2.1 de P1-P5 (agregar_v21: barrido con la avenida desde 10 s, fijo, actuado,
trivial y todas las politicas re-evaluadas, prioridades 0-2) y P6 = malla3_alta (CELDAS_P6), con el
mismo protocolo, el brazo trivial y las prioridades de P5.
22.10.2026: niveles de demanda comunes a las tres redes (agregar_demanda2, ids dem2_*), con sus propias
prioridades (0-6, lo mas largo primero). Todos los trabajos anteriores ya estan hechos; regenerar este
archivo los deja con los mismos ids y comandos (el barrido de P6 se escribe con la regla del 25.09 con
que se corrio), asi que la cola solo lanza los dem2_*.
25.10.2026: diagnostico de la curva del corredor (agregar_diag_corredor, ids diag_*): correcciones V2, INS
y V2+INS de IPPO con mensajes en los cinco niveles del corredor, con sus prioridades (0-3). Enmienda 2
(16:30): variante v2inso (V2+INS con los vehiculos que esperan para entrar en la observacion), mismos ids.
"""
import os
import sys
import json

CELDAS = ["corredor", "corredor_alta", "red", "red_alta", "malla3"]
CELDAS_P6 = ["malla3_alta"]      # 27.09.2026: P6, la malla con demanda alta (calibrar_demanda.py)
# Regla del fijo del resultado principal (25.09): ganador por timeLoss sobre la malla de verdes de ese dia
# (git show 37f9680:barrer_fijo.py, MALLAS; los desfases no cambiaron). P6 se barrio el 28.09 con la
# malla de malla3. La extension automatica de barrer_fijo.py sigue activa.
MALLAS_2509 = {"corredor": ("12,15,18,20,25,30", "10,15,20"),
               "corredor_alta": ("15,20,25,30,35", "10,15,20,25"),
               "red": ("15,20,25,30,35", "10,15,20"),
               "red_alta": ("15,20,25,30,35", "10,15,20"),
               "malla3": ("15,20,25,30,35", "10,15,20,25"),
               "malla3_alta": ("15,20,25,30,35", "10,15,20,25")}
NUEVAS = {"red_alta": "listo/escenarios_red_alta.ok", "malla3": "listo/escenarios_malla3.ok",
          "malla3_alta": "listo/escenarios_malla3_alta.ok"}
BASES = [42, 2042, 4042]
SEMILLAS = "1001-1030"
EPISODIOS = 200

# alg -> (comando de entrenamiento, archivo de politica publicada, bandera de codigo)
ALGS = {
    "ql": ("python ../rl_corredor.py train --escenario {e} --algoritmo qlearning --recompensa retraso "
           "--seed {b} --episodios {n} --desde-cero", "q_table_{e}_ql_s{b}.json", "listo/tabular.ok"),
    "sarsa": ("python ../rl_corredor.py train --escenario {e} --algoritmo sarsa --recompensa retraso "
              "--seed {b} --episodios {n} --desde-cero", "q_table_{e}_sarsa_s{b}.json", "listo/tabular.ok"),
    "ql_colas": ("python ../rl_corredor.py train --escenario {e} --algoritmo qlearning --recompensa colas "
                 "--seed {b} --episodios {n} --desde-cero", "q_table_{e}_ql_colas_s{b}.json",
                 "listo/tabular.ok"),
    "ippo_local": ("python ../rl_ippo.py train --escenario {e} --variante local --seed {b} --episodios {n}",
                   "politica_{e}_local_s{b}.pt", "listo/ippo.ok"),
    "ippo_vecinos": ("python ../rl_ippo.py train --escenario {e} --variante vecinos --seed {b} "
                     "--episodios {n}",
                     "politica_{e}_vecinos_s{b}.pt", "listo/ippo.ok"),
    "ippo_spill": ("python ../rl_ippo.py train --escenario {e} --variante spill --seed {b} --episodios {n}",
                   "politica_{e}_spill_s{b}.pt", "listo/ippo.ok"),
    "dqn": ("python ../rl_dqn.py train --escenario {e} --seed {b} --episodios {n}",
            "politica_{e}_dqn_s{b}.pt", "listo/dqn.ok"),
    "mappo": ("python ../rl_mappo.py train --escenario {e} --seed {b} --episodios {n}",
              "politica_{e}_mappo_s{b}.pt", "listo/mappo.ok"),
}


def regla_2509(caso):
    """Opciones de barrer_fijo.py para la regla del 25.09 con la malla de verdes de caso."""
    avenida, transversal = MALLAS_2509[caso]
    return f" --metrica timeloss_prom --avenida {avenida} --transversal {transversal}"


def prioridad(alg, esc):
    if alg == "ippo_spill" and esc in ("red", "red_alta", "malla3"):
        # En estos escenarios la cola de los enlaces nunca pasa de la mitad de las plazas: el
        # termino de spillback no se activa y la politica es identica bit a bit a ippo_vecinos
        # (pruebas del 24.09 y fase del 06.09). Se corre al final, solo si sobra maquina.
        return 9
    if alg in ("ql", "ippo_local", "ippo_vecinos", "ippo_spill"):
        return 2 if esc in ("corredor", "corredor_alta", "red") else 3
    if alg == "sarsa":
        return 4
    if alg in ("dqn", "mappo") and esc == "malla3":
        # 25.09 00:35: adelantados (eran 8). Son los trabajos mas largos (unas 2.5 h) y la malla
        # es donde un critico centralizado tiene mas sentido; con prioridad 8 no llegaban a las 5:00.
        return 5
    return {"dqn": 5, "mappo": 6, "ql_colas": 7}[alg]


def agregar_v21(trabajos, agregar):
    """Re-medicion v2.1 (27.09.2026), sin reentrenar: barrido del fijo con la avenida desde 10 s y
    por retraso total, fijo, actuado y trivial re-evaluados, y todas las politicas ya entrenadas
    re-evaluadas para tener retraso total, espera para entrar y no insertados. Las evaluaciones
    del plan v2 que seguian pendientes (spill en red, red_alta y malla3) no se duplican: corren
    con su id original y el codigo nuevo."""
    ids = {t["id"] for t in trabajos}
    hechos = set()
    ruta_estado = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cola", "estado.json")
    if os.path.exists(ruta_estado):
        with open(ruta_estado, encoding="utf-8") as f:
            hechos = set(json.load(f).get("hechos", []))
    for esc in CELDAS:
        barrido = f"v21_barrido_{esc}"
        agregar(barrido, 0, f"python ../barrer_fijo.py {esc} --semillas 2001-2003 --tmp tmp_v21_{esc} "
                f"--procesos 3 --instalar", [])
        for brazo in ("fijo", "actuado", "trivial"):
            agregar(f"v21_eval_{esc}_{brazo}", 1,
                    f"python ../evaluar.py --escenario {esc} --brazo {brazo} --semillas {SEMILLAS} "
                    f"--salida parciales/eval_{esc}_{brazo}.csv",
                    [f"trabajo:{barrido}"] if brazo == "fijo" else [])
        for alg, (_, archivo, _) in ALGS.items():
            for b in BASES:
                viejo = f"eval_{esc}_{alg}_s{b}"
                if viejo not in ids or viejo not in hechos:
                    continue
                agregar(f"v21_{viejo}", 2,
                        f"python ../evaluar.py --escenario {esc} --politica {archivo.format(e=esc, b=b)} "
                        f"--semillas {SEMILLAS} --salida parciales/{viejo}.csv",
                        [f"trabajo:train_{esc}_{alg}_s{b}"])


def agregar_demanda(agregar):
    """Barrido de demanda en el corredor de P1 (27.09.2026, barrido_demanda.py): por nivel, el fijo
    re-barrido para esa demanda, el fijo de P1 sin retunear, el actuado y las politicas publicadas
    de IPPO vecinos de P1 (base 4042) y de P2 (base 2042) segun veredicto.csv, sin reentrenar."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import escenarios_plan2
    agregar("dem_preparar", 1, "python ../barrido_demanda.py preparar", ["trabajo:v21_barrido_corredor"])
    niveles = [e for e in escenarios_plan2.DERIVADOS
               if not e.endswith("_p1") and e not in escenarios_plan2.NIVELES_DEMANDA2]
    politicas = {"ippo_vecinos_s4042": "politica_corredor_vecinos_s4042.pt",
                 "ippo_vecinos_s2042": "politica_corredor_alta_vecinos_s2042.pt"}
    for esc in niveles:
        agregar(f"dem_barrido_{esc}", 2, f"python ../barrer_fijo.py {esc} --semillas 2001-2003 "
                f"--tmp tmp_dem_{esc} --procesos 3 --instalar", ["trabajo:dem_preparar"])
        base = f"python ../evaluar.py --semillas {SEMILLAS} "
        agregar(f"dem_eval_{esc}_fijo", 2, base + f"--escenario {esc} --brazo fijo "
                f"--salida demanda/eval_{esc}_fijo.csv", [f"trabajo:dem_barrido_{esc}"])
        agregar(f"dem_eval_{esc}_fijo_p1", 2, base + f"--escenario {esc}_p1 --brazo fijo "
                f"--salida demanda/eval_{esc}_fijo_p1.csv", ["trabajo:dem_preparar"])
        agregar(f"dem_eval_{esc}_actuado", 2, base + f"--escenario {esc} --brazo actuado "
                f"--salida demanda/eval_{esc}_actuado.csv", ["trabajo:dem_preparar"])
        for brazo, archivo in politicas.items():
            agregar(f"dem_eval_{esc}_{brazo}", 2, base + f"--escenario {esc} --politica {archivo} "
                    f"--salida demanda/eval_{esc}_{brazo}.csv", ["trabajo:dem_preparar"])


def agregar_demanda2(agregar):
    """Niveles de demanda comunes a las tres redes (22.10.2026; escenarios_plan2.NIVELES_DEMANDA2): 3 en el
    corredor, 5 en la red con rotonda y 4 en la malla, con el protocolo del plan. Por nivel:
      dem2_barrido_<esc>    fijo ajustado con la regla del 25.09 (regla_2509) y la malla del caso que
                            hereda el nivel; --instalar deja el ganador en <esc>.add.xml
      dem2_train_<esc>_ippo_vecinos_s<b>   IPPO con mensajes, bases 42, 2042 y 4042, con los mismos
                            argumentos que train_<celda>_ippo_vecinos_s<b> (200 episodios, validacion
                            con 999 y 1999 cada 10, checkpoints, HIPER por defecto)
      dem2_eval_<esc>_<brazo>   fijo, actuado, trivial (ciclo minimo) e ippo_vecinos_s<b>, semillas
                            1001-1030, parcial en demanda2/eval_<esc>_<brazo>.csv
      dem2_consolidar_<esc> consolidar.py con esos parciales: evaluacion_<esc>.csv y _resumen.csv
    Todo con cpus=1, y es exacto: cada barrido corre con un proceso (--procesos 1; el resultado no
    depende de N). Con 4 procesos y cpus=1, los barridos entraban juntos al terminar los entrenamientos
    de la red y la maquina llegaba a unos 39 hilos sobre 16; con cpus=4 no encontrarian hueco frente a
    los de 1. Prioridad, lo mas largo primero: 0 preparar; 1 barridos (los 12 arrancan juntos al
    principio; el de dem_red_t3620, unas 2 h con un proceso, es el trabajo mas largo); 2 IPPO en la
    malla; 3 IPPO en la red; 4 IPPO en el corredor; 5 evaluaciones; 6 consolidar. Dentro de cada
    prioridad, el nivel con mas demanda primero.
    Las salidas llevan dem_ en el nombre (no pisan nada del plan); los temporales del barrido van a
    tmp_barrido_dem2_<esc>/, que .gitignore ya excluye."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import escenarios_plan2
    niveles = escenarios_plan2.NIVELES_DEMANDA2
    redes = ("red", "malla3", "corredor")             # orden de los barridos: la red es la mas cara
    prio_ippo = {"malla3": 2, "red": 3, "corredor": 4}
    prep = "dem2_preparar"
    agregar(prep, 0, "python ../barrido_demanda.py preparar2", [])
    orden = sorted(niveles, key=lambda e: (prio_ippo[niveles[e][0]], -niveles[e][2]))
    for esc in orden:
        for b in BASES:
            agregar(f"dem2_train_{esc}_ippo_vecinos_s{b}", prio_ippo[niveles[esc][0]],
                    ALGS["ippo_vecinos"][0].format(e=esc, b=b, n=EPISODIOS), [f"trabajo:{prep}"])
    for esc in sorted(niveles, key=lambda e: (redes.index(niveles[e][0]), -niveles[e][2])):
        agregar(f"dem2_barrido_{esc}", 1, f"python ../barrer_fijo.py {esc} --semillas 2001-2003 "
                f"--tmp tmp_barrido_dem2_{esc} --procesos 1 --instalar" + regla_2509(niveles[esc][3]),
                [f"trabajo:{prep}"])
    for esc in orden:
        evaluar = f"python ../evaluar.py --escenario {esc} --semillas {SEMILLAS} "
        evals = []
        for brazo in ("fijo", "actuado", "trivial"):
            requiere = [f"trabajo:dem2_barrido_{esc}" if brazo == "fijo" else f"trabajo:{prep}"]
            agregar(f"dem2_eval_{esc}_{brazo}", 5,
                    evaluar + f"--brazo {brazo} --salida demanda2/eval_{esc}_{brazo}.csv", requiere)
            evals.append(f"trabajo:dem2_eval_{esc}_{brazo}")
        for b in BASES:
            agregar(f"dem2_eval_{esc}_ippo_vecinos_s{b}", 5,
                    evaluar + f"--politica politica_{esc}_vecinos_s{b}.pt "
                    f"--salida demanda2/eval_{esc}_ippo_vecinos_s{b}.csv",
                    [f"trabajo:dem2_train_{esc}_ippo_vecinos_s{b}"])
            evals.append(f"trabajo:dem2_eval_{esc}_ippo_vecinos_s{b}")
        agregar(f"dem2_consolidar_{esc}", 6,
                f"python ../consolidar.py --escenario {esc} --parciales demanda2", evals)


# 25.10.2026: diagnostico de la curva del corredor (diag_corredor/PRERREGISTRO.md). Por nivel: escenario,
# base de la version evaluada actual de IPPO con mensajes y escenario del fijo ajustado desde 10 s (barrido
# del 27.09 con los mismos flujos; None = el fijo vigente del escenario, igual al del 25.09).
NIVELES_DIAG = [("corredor_alta", 2042, None), ("dem_corredor_t2715", 2042, "corredor_f150"),
                ("corredor", 4042, None), ("dem_corredor_t1358", 42, "corredor_f075"),
                ("dem_corredor_t905", 4042, "corredor_f050")]          # lo mas largo primero
VARIANTES_DIAG = {"v2": "--v2", "ins": "--recompensa-insercion", "v2ins": "--v2 --recompensa-insercion",
                  # Enmienda 2 (25.10.2026, 16:30): INS observable, segunda ronda
                  "v2inso": "--v2 --recompensa-insercion --obs-insercion"}
# Enmienda del 25.10.2026 (PRERREGISTRO.md): las tres variantes eligen el checkpoint por el retraso total
CRITERIO_DIAG = "--criterio-val total"
SEMILLAS_DIAG = {"1001": "1001-1030", "6001": "6001-6030"}     # comparables con la curva y confirmacion


def agregar_diag_corredor(agregar):
    """Diagnostico del corredor (25.10.2026), ids diag_*, todo con cpus=1:
      diag_train_<esc>_ippo_vecinos_<v>_s<b>   IPPO con mensajes con la correccion v (v2, ins, v2ins), bases
                            42, 2042 y 4042, con los argumentos de train_<celda>_ippo_vecinos_s<b> mas las
                            opciones de la variante, --etiqueta v (salidas con _<v> en el nombre) y
                            --criterio-val total (checkpoint por retraso total; enmienda del prerregistro)
      diag_eval_<esc>_ippo_vecinos_<v>_s<b>_<1001|6001>   esas politicas en 1001-1030 y en 6001-6030
      diag_eval_<esc>_<brazo>_6001   confirmacion de las referencias y de la version evaluada actual en
                            6001-6030: fijo (regla del 25.09), fijo10 (fijo ajustado desde 10 s; en P1 y P2 es
                            el mismo fijo y no se repite), trivial (ciclo minimo), actuado e ippo_vecinos_s<b>
                            de las tres bases actuales. En 1001-1030 ya estan en demanda/, demanda2/ y parciales/.
    Salidas en diag_corredor/eval/eval_<esc>_<brazo>_<1001|6001>.csv; el tripinfo, vehiculos_, serie_ y fases_
    de la primera semilla en diag_corredor/eval/extras_<1001|6001>/ (evaluar.py --extras), sin pisar nada.
    Prioridad: 0 entrenamientos de corredor_alta (los mas largos), 1 los demas (de mas a menos largo),
    2 evaluaciones 1001-1030 de las variantes, 3 confirmacion 6001-6030."""
    evaluar = "python ../evaluar.py --escenario {e} --semillas {s} --salida diag_corredor/eval/{n}.csv " \
              "--extras diag_corredor/eval/extras_{k} "
    for esc, _, _ in NIVELES_DIAG:
        for v, opciones in VARIANTES_DIAG.items():
            for b in BASES:
                agregar(f"diag_train_{esc}_ippo_vecinos_{v}_s{b}", 0 if esc == "corredor_alta" else 1,
                        ALGS["ippo_vecinos"][0].format(e=esc, b=b, n=EPISODIOS)
                        + f" {opciones} --etiqueta {v} {CRITERIO_DIAG}",
                        [])
    for k, prio in (("1001", 2), ("6001", 3)):
        for esc, _, _ in NIVELES_DIAG:
            for v in VARIANTES_DIAG:
                for b in BASES:
                    brazo = f"ippo_vecinos_{v}_s{b}"
                    agregar(f"diag_eval_{esc}_{brazo}_{k}", prio,
                            evaluar.format(e=esc, s=SEMILLAS_DIAG[k], n=f"eval_{esc}_{brazo}_{k}", k=k)
                            + f"--politica politica_{esc}_vecinos_{v}_s{b}.pt",
                            [f"trabajo:diag_train_{esc}_ippo_vecinos_{v}_s{b}"])
    k = "6001"
    for esc, _, fijo10 in NIVELES_DIAG:
        refs = [("fijo", esc, "--brazo fijo")]
        if fijo10:
            refs.append(("fijo10", fijo10, "--brazo fijo"))
        refs += [("trivial", esc, "--brazo trivial"), ("actuado", esc, "--brazo actuado")]
        refs += [(f"ippo_vecinos_s{b}", esc, f"--politica politica_{esc}_vecinos_s{b}.pt") for b in BASES]
        for brazo, esc_eval, opcion in refs:
            agregar(f"diag_eval_{esc}_{brazo}_{k}", 3,
                    evaluar.format(e=esc_eval, s=SEMILLAS_DIAG[k], n=f"eval_{esc}_{brazo}_{k}", k=k) + opcion, [])


def main():
    trabajos = []

    def agregar(tid, prio, cmd, requiere, cpus=1):
        trabajos.append({"id": tid, "prioridad": prio, "cpus": cpus, "requiere": requiere, "cmd": cmd})

    for esc in CELDAS + CELDAS_P6:
        prep = f"prep_{esc}"
        agregar(prep, 0, f"python preparar.py {esc}", [NUEVAS[esc]] if esc in NUEVAS else [])
        bandera_barrido = "listo/barrer_malla.ok" if esc.startswith("malla3") else "listo/barrer.ok"
        agregar(f"barrido_{esc}", 1,
                f"python ../barrer_fijo.py {esc} --semillas 2001-2003 --tmp tmp_barrido_{esc} "
                f"--procesos 4 --instalar" + (regla_2509(esc) if esc in CELDAS_P6 else ""),
                [bandera_barrido, f"trabajo:{prep}"], cpus=1)
        # cpus=1 aunque use 4 procesos: con la cola llena, un trabajo de 4 cpus nunca encontraria
        # hueco frente a los de 1; se acepta sobrecargar la maquina unos minutos.
        referencias = [("fijo", [f"trabajo:barrido_{esc}"]), ("actuado", [f"trabajo:{prep}"])]
        if esc in CELDAS_P6:
            # en P1-P5 el trivial entra con la re-medicion v2.1 (agregar_v21)
            referencias.append(("trivial", [f"trabajo:{prep}"]))
        for brazo, extra in referencias:
            agregar(f"eval_{esc}_{brazo}", 1,
                    f"python ../evaluar.py --escenario {esc} --brazo {brazo} --semillas {SEMILLAS} "
                    f"--salida parciales/eval_{esc}_{brazo}.csv", ["listo/evaluar.ok"] + extra)
        for alg, (cmd, archivo, bandera) in ALGS.items():
            if esc.startswith("malla3") and alg == "ql_colas":
                continue
            requiere = [bandera, f"trabajo:{prep}"]
            if esc.startswith("malla3") and alg not in ("ql", "sarsa"):
                requiere.append("listo/ippo_malla.ok")
            for b in BASES:
                tid = f"train_{esc}_{alg}_s{b}"
                agregar(tid, prioridad(alg, esc), cmd.format(e=esc, b=b, n=EPISODIOS), requiere)
                agregar(f"eval_{esc}_{alg}_s{b}", 1,
                        f"python ../evaluar.py --escenario {esc} --politica {archivo.format(e=esc, b=b)} "
                        f"--semillas {SEMILLAS} --salida parciales/eval_{esc}_{alg}_s{b}.csv",
                        ["listo/evaluar.ok", f"trabajo:{tid}"])

    agregar_v21(trabajos, agregar)
    agregar_demanda(agregar)
    agregar_demanda2(agregar)
    agregar_diag_corredor(agregar)
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cola", "trabajos.jsonl")
    with open(ruta, "w", encoding="utf-8") as f:
        for t in trabajos:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"{len(trabajos)} trabajos en {ruta}")


if __name__ == "__main__":
    main()
