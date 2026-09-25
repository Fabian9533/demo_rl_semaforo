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
"""
import os
import json

CELDAS = ["corredor", "corredor_alta", "red", "red_alta", "malla3"]
NUEVAS = {"red_alta": "listo/escenarios_red_alta.ok", "malla3": "listo/escenarios_malla3.ok"}
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
    "ippo_vecinos": ("python ../rl_ippo.py train --escenario {e} --variante vecinos --seed {b} --episodios {n}",
                     "politica_{e}_vecinos_s{b}.pt", "listo/ippo.ok"),
    "ippo_spill": ("python ../rl_ippo.py train --escenario {e} --variante spill --seed {b} --episodios {n}",
                   "politica_{e}_spill_s{b}.pt", "listo/ippo.ok"),
    "dqn": ("python ../rl_dqn.py train --escenario {e} --seed {b} --episodios {n}",
            "politica_{e}_dqn_s{b}.pt", "listo/dqn.ok"),
    "mappo": ("python ../rl_mappo.py train --escenario {e} --seed {b} --episodios {n}",
              "politica_{e}_mappo_s{b}.pt", "listo/mappo.ok"),
}


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


def main():
    trabajos = []

    def agregar(tid, prio, cmd, requiere, cpus=1):
        trabajos.append({"id": tid, "prioridad": prio, "cpus": cpus, "requiere": requiere, "cmd": cmd})

    for esc in CELDAS:
        prep = f"prep_{esc}"
        agregar(prep, 0, f"python preparar.py {esc}", [NUEVAS[esc]] if esc in NUEVAS else [])
        bandera_barrido = "listo/barrer_malla.ok" if esc == "malla3" else "listo/barrer.ok"
        agregar(f"barrido_{esc}", 1,
                f"python ../barrer_fijo.py {esc} --semillas 2001-2003 --tmp tmp_barrido_{esc} "
                f"--procesos 4 --instalar", [bandera_barrido, f"trabajo:{prep}"], cpus=1)
        # cpus=1 aunque use 4 procesos: con la cola llena, un trabajo de 4 cpus nunca encontraria
        # hueco frente a los de 1; se acepta sobrecargar la maquina unos minutos.
        for brazo, extra in (("fijo", [f"trabajo:barrido_{esc}"]), ("actuado", [f"trabajo:{prep}"])):
            agregar(f"eval_{esc}_{brazo}", 1,
                    f"python ../evaluar.py --escenario {esc} --brazo {brazo} --semillas {SEMILLAS} "
                    f"--salida parciales/eval_{esc}_{brazo}.csv", ["listo/evaluar.ok"] + extra)
        for alg, (cmd, archivo, bandera) in ALGS.items():
            if esc == "malla3" and alg == "ql_colas":
                continue
            requiere = [bandera, f"trabajo:{prep}"]
            if esc == "malla3" and alg not in ("ql", "sarsa"):
                requiere.append("listo/ippo_malla.ok")
            for b in BASES:
                tid = f"train_{esc}_{alg}_s{b}"
                agregar(tid, prioridad(alg, esc), cmd.format(e=esc, b=b, n=EPISODIOS), requiere)
                agregar(f"eval_{esc}_{alg}_s{b}", 1,
                        f"python ../evaluar.py --escenario {esc} --politica {archivo.format(e=esc, b=b)} "
                        f"--semillas {SEMILLAS} --salida parciales/eval_{esc}_{alg}_s{b}.csv",
                        ["listo/evaluar.ok", f"trabajo:{tid}"])

    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cola", "trabajos.jsonl")
    with open(ruta, "w", encoding="utf-8") as f:
        for t in trabajos:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"{len(trabajos)} trabajos en {ruta}")


if __name__ == "__main__":
    main()
