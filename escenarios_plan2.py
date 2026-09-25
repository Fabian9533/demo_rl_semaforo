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

Cambios del plan v2 (24.09.2026):
  red_alta  P4: la red de 3 cruces + rotonda (red.net.xml) con toda la demanda x 1.2. El factor
            y su criterio estan en la cabecera de red_alta.rou.xml. Semaforos, enlaces, flujos y
            vecinos son los de "red" (copiados aqui para no importar rl_corredor ni rl_ippo).
  malla3    P5: malla de 3x3 cruces semaforizados (C11..C33, fila 1 al norte, columna 1 al oeste),
            300 m entre cruces, brazos de 400 m, 2 carriles por sentido. La avenida de referencia
            es la fila 2 (E-O): sus flows de punta a punta se llaman como en el corredor.
            En malla3.add.xml la fase 0 de cada semaforo es la E-O (avenida) y la 2 la N-S.
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
