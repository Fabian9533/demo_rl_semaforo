"""
escenarios_plan3.py - Escenarios nuevos del plan 3 (segundo estudio): llegadas aleatorias, entrada por el mejor
carril, P6e, perfil de 10 min y mezcla de Lima (plan3/doc/PLAN3.md, tareas 0.5, 0.6, 2.4 y 2.5).

No se suman a escenarios_plan2.DERIVADOS en disco: solo dentro del proceso que lanza con_escenarios.py
(DECISIONES.md, B2). Si se sumaran en disco, plan2/generar_trabajos.agregar_demanda crearia seis trabajos por
escenario en la cola de plan2. Importar este modulo no cambia nada de escenarios_plan2.

ESTOCASTICOS[esc] = (red base, .sumocfg, caso cuya malla de barrido y desfases hereda): el formato de DERIVADOS.
RECETAS[esc] = (caso, llegadas, perfil, mezcla, arranque): como escribe plan3/demanda_estocastica.py preparar3 los
archivos del escenario.
  caso      escenario entregado del que salen la demanda, la red y el programa fijo (su <caso>.add.xml)
  llegadas  "poisson": period="exp(q/3600)" en cada flow; "regulares": vehsPerHour, como lo entregado
  perfil    True: bloques de 10 min con los factores 2/3, 1, 4/3, 4/3, 1, 2/3 (la misma demanda en cada media hora)
  mezcla    True: mezcla de Lima (JICA 2013 sin camiones) con los mismos vehiculos equivalentes
  arranque  startupDelay (s) de todos los tipos; 0 = el de SUMO. Solo para evaluar (A7)
Todos entran por el mejor carril: departLane="best" en cada flow (A2).

Escenarios (P1-P6 = corredor, corredor_alta, red, red_alta, malla3, malla3_alta):
  poi_<caso>     P1-P6 con llegadas de Poisson
  malla3_alta_e  P6e: P6 con llegadas regulares y la entrada corregida
  per_<caso>     P1 y P3 con llegadas de Poisson y el perfil de 10 min
  mix_<caso>     P1 y P3 con llegadas de Poisson y la mezcla de Lima
  mixa_<caso>    lo mismo que mix_ con arranque lento de 0.5 s (sensibilidad al evaluar)
"""

# Caso entregado -> red base (la de sus semaforos, vecinos y lados en rl_corredor y rl_ippo)
RED_BASE = {"corredor": "corredor", "corredor_alta": "corredor", "red": "red", "red_alta": "red",
            "malla3": "malla3", "malla3_alta": "malla3"}

RECETAS = {}
for _caso in RED_BASE:
    RECETAS[f"poi_{_caso}"] = (_caso, "poisson", False, False, 0)
RECETAS["malla3_alta_e"] = ("malla3_alta", "regulares", False, False, 0)
for _caso in ("corredor", "red"):
    RECETAS[f"per_{_caso}"] = (_caso, "poisson", True, False, 0)
    RECETAS[f"mix_{_caso}"] = (_caso, "poisson", False, True, 0)
    RECETAS[f"mixa_{_caso}"] = (_caso, "poisson", False, True, 0.5)

ESTOCASTICOS = {esc: (RED_BASE[caso], f"{esc}.sumocfg", caso) for esc, (caso, *_) in RECETAS.items()}
