"""
escenarios_lima.py - Escenario del caso Lima (13.11.2026): el nudo de Av. Reducto, Av. 28 de Julio y Av. Vasco
Nunez de Balboa, en Miraflores. Lo importa rl_ippo.py, igual que escenarios_plan2.py.

Es UN solo cruce con semaforo (semaforo_S1) y sin vecinos: no hay mensajes. Sus cuatro entradas ocupan las cuatro
posiciones de la observacion [oeste, este, norte, sur]: Balboa (llega desde el suroeste), 28 de Julio desde el
puente de la Via Expresa (este), Reducto desde el norte y Reducto desde el sur.
"fases" es el numero de estados con verde del programa del semaforo (lima/programa.py, PLAN): la observacion lleva
una posicion por fase. Los archivos del escenario se generan en lima/ (armar_red.py, programa.py y demanda.py) y las
corridas usan lima/ como carpeta de trabajo.
"""
FASES_LIMA = 3          # debe coincidir con len(PLAN) de lima/programa.py; rl_ippo lo comprueba al empezar

ESCENARIOS = {
    "lima": {
        "cfg": "lima.sumocfg",
        "semaforos": {"semaforo_S1": ["B_S1", "J_S1", "RN_S1", "RS_S1"]},
        "enlaces": [],
        "flujos_corredor": None,
        "vecinos": {"semaforo_S1": {"oeste": None, "este": None}},
        "fases": FASES_LIMA,
    },
}

# Segundo caso de Lima (13.11.2026): el corredor de la Av. Alfredo Benavides entre la Av. Jose Larco y la Av.
# Republica de Panama (lima/corredor/corredor.py). Seis cruces de dos fases sobre una avenida de doble sentido, como
# los corredores de los casos P1 a P4: un agente por cruce y mensajes entre vecinos. Accesos en el orden [oeste,
# este, norte, sur]; una transversal de un solo sentido tiene el acceso contrario como un tramo sin demanda.
_CRUCES = ["C1", "C2", "C3", "C4", "C5", "C6"]


def _lado(k, paso):
    j = k + paso
    return "W" if j < 0 else "E" if j >= len(_CRUCES) else _CRUCES[j]


import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "lima", "corredor"))
import corredor as _corredor       # estudio 2 del corredor (19.11.2026): verdes minimos de los peatones por cruce

ESCENARIOS["benavides"] = {
    "cfg": "benavides.sumocfg",
    # verde minimo de cada estado con verde (0 = avenida, 2 = transversal), en s: el de los peatones del cruce
    "verde_min_tls": {f"semaforo_{c}": {0: _corredor.minimos(c)[0], 2: _corredor.minimos(c)[1]} for c in _CRUCES},
    "semaforos": {f"semaforo_{c}": [f"{_lado(k, -1)}_{c}", f"{_lado(k, 1)}_{c}", f"N{k + 1}_{c}", f"S{k + 1}_{c}"]
                  for k, c in enumerate(_CRUCES)},
    "enlaces": [e for a, b in zip(_CRUCES, _CRUCES[1:]) for e in (f"{a}_{b}", f"{b}_{a}")],
    "flujos_corredor": [f"p{p}_{f}" for p in (1, 2, 3, 4) for f in ("W_E", "E_W")],
    "vecinos": {f"semaforo_{c}": {
        "oeste": (f"semaforo_{_CRUCES[k - 1]}", f"{_CRUCES[k - 1]}_{c}", f"{c}_{_CRUCES[k - 1]}") if k > 0 else None,
        "este": (f"semaforo_{_CRUCES[k + 1]}", f"{_CRUCES[k + 1]}_{c}", f"{c}_{_CRUCES[k + 1]}")
        if k < len(_CRUCES) - 1 else None} for k, c in enumerate(_CRUCES)},
}
