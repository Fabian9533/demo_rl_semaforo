"""
escenarios_plan2.py - Escenarios nuevos del plan de pruebas v2 (P4 red_alta, P5 malla3).

Lo importan rl_corredor.py (ESCENARIOS_RC) y rl_ippo.py (VECINOS, LADOS). El formato de cada
entrada esta en plan2/ESPEC.md, seccion 1:
  ESCENARIOS_RC[esc] = {"cfg", "semaforos": tls -> [aprox oeste, aprox este, aprox norte, aprox sur]
                        (edges que LLEGAN al cruce), "enlaces": edges internos entre semaforos,
                        "flujos_corredor": flows que recorren la avenida de punta a punta o None}
  VECINOS[esc][tls][lado] = (vecino, enlace vecino -> mi, enlace mi -> vecino) o None en el borde
  LADOS[esc] = lados que se miran en VECINOS
Mientras un escenario no este listo, no aparece aqui.

Cambios del plan v2:
  red_alta  P4: la red de 3 cruces + rotonda (red.net.xml) con toda la demanda x 1.2. El factor
            y su criterio estan en la cabecera de red_alta.rou.xml. Semaforos, enlaces, flujos y
            vecinos son los de "red" (copiados aqui para no importar rl_corredor ni rl_ippo).
  malla3    P5: malla de 3x3 cruces semaforizados (C11..C33, fila 1 al norte, columna 1 al oeste),
            300 m entre cruces, brazos de 400 m, 2 carriles por sentido. La avenida de referencia
            es la fila 2 (E-O): sus flows de punta a punta se llaman como en el corredor.
            En malla3.add.xml la fase 0 de cada semaforo es la E-O (avenida) y la 2 la N-S.
Cambios posteriores al plan v2:
  malla3_alta  P6: la misma malla con toda la demanda x f (calibrar_demanda.py).
  dem_<base>_t<veh/h>  22.10.2026: niveles de demanda comunes a las tres redes (NIVELES_DEMANDA2, al
            final); se registran como DERIVADOS, con los semaforos, vecinos y lados de su base.
"""

# ---------------- P4: red_alta ----------------
ESCENARIOS_RC = {
    "red_alta": {
        "cfg": "red_alta.sumocfg",
        "semaforos": {
            "semaforo_C1": ["RE_C1", "C2_C1", "N1_C1", "S1_C1"],
            "semaforo_C2": ["C1_C2", "C3_C2", "N2_C2", "S2_C2"],
            "semaforo_C3": ["C2_C3", "E_C3", "N3_C3", "S3_C3"],
        },
        "enlaces": ["C1_C2", "C2_C1", "C2_C3", "C3_C2"],
        "flujos_corredor": ["p1_W_E", "p1_E_W", "p2_W_E", "p2_E_W"],
    },
}
VECINOS = {
    "red_alta": {
        "semaforo_C1": {"oeste": None, "este": ("semaforo_C2", "C2_C1", "C1_C2")},
        "semaforo_C2": {"oeste": ("semaforo_C1", "C1_C2", "C2_C1"),
                        "este": ("semaforo_C3", "C3_C2", "C2_C3")},
        "semaforo_C3": {"oeste": ("semaforo_C2", "C2_C3", "C3_C2"), "este": None},
    },
}
LADOS = {"red_alta": ("oeste", "este")}


# ---------------- P5: malla3 ----------------
# Nodo C<fila><columna>; los brazos exteriores terminan en W<fila>, E<fila>, N<columna>, S<columna>.
# Los ids de los edges son ORIGEN_DESTINO (p. ej. C21_C22 va de C21 a C22).
FILAS = COLUMNAS = 3


def nodo_vecino(fila, col, lado):
    """Nodo al otro lado de la via que sale del cruce (fila, col) hacia 'lado', y si es un cruce."""
    if lado == "oeste":
        return (f"C{fila}{col - 1}", True) if col > 1 else (f"W{fila}", False)
    if lado == "este":
        return (f"C{fila}{col + 1}", True) if col < COLUMNAS else (f"E{fila}", False)
    if lado == "norte":
        return (f"C{fila - 1}{col}", True) if fila > 1 else (f"N{col}", False)
    return (f"C{fila + 1}{col}", True) if fila < FILAS else (f"S{col}", False)


def malla3():
    lados = ("oeste", "este", "norte", "sur")
    semaforos, vecinos, enlaces = {}, {}, []
    for fila in range(1, FILAS + 1):
        for col in range(1, COLUMNAS + 1):
            yo = f"C{fila}{col}"
            tls = f"semaforo_{yo}"
            semaforos[tls] = []
            vecinos[tls] = {}
            for lado in lados:
                otro, es_cruce = nodo_vecino(fila, col, lado)
                semaforos[tls].append(f"{otro}_{yo}")          # aproximacion: llega desde ese lado
                if es_cruce:
                    vecinos[tls][lado] = (f"semaforo_{otro}", f"{otro}_{yo}", f"{yo}_{otro}")
                    enlaces.append(f"{otro}_{yo}")               # cada enlace interno una vez
                else:
                    vecinos[tls][lado] = None
    rc = {"cfg": "malla3.sumocfg", "semaforos": semaforos, "enlaces": sorted(enlaces),
          "flujos_corredor": ["p1_W_E", "p1_E_W", "p2_W_E", "p2_E_W"]}
    return rc, vecinos


ESCENARIOS_RC["malla3"], VECINOS["malla3"] = malla3()
LADOS["malla3"] = ("oeste", "este", "norte", "sur")


# ---------------- P6: malla3_alta ----------------
# La malla de P5 (malla3.net.xml) con toda la demanda multiplicada por el factor que eligio
# calibrar_demanda.py (criterio y tabla en la cabecera de malla3_alta.rou.xml). Semaforos,
# enlaces, flujos y vecinos son los de malla3.
ESCENARIOS_RC["malla3_alta"] = {**ESCENARIOS_RC["malla3"], "cfg": "malla3_alta.sumocfg"}
VECINOS["malla3_alta"] = VECINOS["malla3"]
LADOS["malla3_alta"] = LADOS["malla3"]


# ---------------- Barrido de demanda en el corredor ----------------
# Analisis complementario, fuera del veredicto: la red de P1 con toda la demanda x f y con un perfil
# que cambia dentro de la hora (barrido_demanda.py escribe los archivos en plan2/). Cada derivado
# usa la red, los semaforos y los vecinos de su base.
# DERIVADOS[esc] = (escenario base, .sumocfg, caso cuya malla de barrido y desfases hereda).
# Los <esc>_p1 cargan el programa fijo de P1 sin retunear (corredor.add.xml).
FACTORES_DEMANDA = (50, 75, 100, 125, 150, 175, 200, 225)       # f x 100
DERIVADOS = {}
for _f in FACTORES_DEMANDA:
    DERIVADOS[f"corredor_f{_f:03d}"] = ("corredor", f"corredor_f{_f:03d}.sumocfg",
                                        "corredor" if _f <= 125 else "corredor_alta")
    DERIVADOS[f"corredor_f{_f:03d}_p1"] = ("corredor", f"corredor_f{_f:03d}_p1.sumocfg", "corredor")
DERIVADOS["corredor_var"] = ("corredor", "corredor_var.sumocfg", "corredor_alta")
DERIVADOS["corredor_var_p1"] = ("corredor", "corredor_var_p1.sumocfg", "corredor")


# ---------------- Niveles de demanda comunes a las tres redes (22.10.2026) ----------------
# Cada red base (corredor, red, malla3) con toda la demanda x f, para comparar las redes con la misma
# demanda total (1810, 2715 y 3620 veh/h) y completar la curva de cada una. Mismo protocolo del plan:
# fijo ajustado con la regla del 25.09, actuado, ciclo minimo (trivial) e IPPO con mensajes x 3 bases.
# barrido_demanda.py preparar2 escribe los archivos en plan2/; las evaluaciones van a plan2/demanda2/.
# TOTAL_BASE: veh/h de cada periodo de 30 min en la red base (la suma de vehsPerHour de cada periodo).
# NIVELES_DEMANDA2[esc] = (escenario base, f, veh/h de cada periodo, caso cuya malla de barrido y
#                          desfases hereda: el caso alto de la red por encima de la demanda nominal).
# En la red y en la malla f = veh/h del nivel / TOTAL_BASE (red 1358: 1358/2150 = 0.632, el factor
# efectivo; con 1357.5/2150 los flows salen iguales). En el corredor f = 0.5, 0.75 y 1.5, como en
# corredor_f050, f075 y f150 (1810 x 0.75 = 1357.5, que se redondea a 1358 veh/h).
TOTAL_BASE = {"corredor": 1810, "red": 2150, "malla3": 4350}
_NIVELES2 = [("corredor", 905, 0.5, "corredor"), ("corredor", 1358, 0.75, "corredor"),
             ("corredor", 2715, 1.5, "corredor_alta"),
             ("red", 905, 905 / 2150, "red"), ("red", 1358, 1358 / 2150, "red"),
             ("red", 1810, 1810 / 2150, "red"), ("red", 2715, 2715 / 2150, "red_alta"),
             ("red", 3620, 3620 / 2150, "red_alta"),
             ("malla3", 1810, 1810 / 4350, "malla3"), ("malla3", 2715, 2715 / 4350, "malla3"),
             ("malla3", 3620, 3620 / 4350, "malla3"), ("malla3", 6525, 1.5, "malla3_alta")]
NIVELES_DEMANDA2 = {f"dem_{b}_t{n}": (b, f, n, caso) for b, n, f, caso in _NIVELES2}
for _esc, (_base, _, _, _caso) in NIVELES_DEMANDA2.items():
    DERIVADOS[_esc] = (_base, f"{_esc}.sumocfg", _caso)
