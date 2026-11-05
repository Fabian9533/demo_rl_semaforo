"""
costos_ref.py - Cuantas corridas y cuantas horas-proceso pide cada script de las referencias por celda (plan3, informe
de 0.7-0.11). Las cuentas usan la gruesa entregada (plan2/barrido_<esc>.csv, solo lectura) como estimacion de la
gruesa nueva (la misma rejilla con 2001-2003) para saber cuantas regiones tiene la fina, y las duraciones por corrida
de costos_plan3.py (regimen conservador + 10 %, medidas con la cola llena):
  sumo directo (barrido)  P1 2.0  P2 8.9  P3 4.8  P4 5.8  P5 10.7  P6 18.2 s;  niveles: la de su red
  actuado sumo directo     la mitad del actuado por TraCI (P1 5.4 ... P6 46.9 s; plan3/referencias/informe.md 4)
  reglas por TraCI         P1 4.8  P2 11.7  P3 7.2  P4 8.5  P5 19.7  P6 42.7 s
  llegadas aleatorias x1.07; el puntaje por periodo (write-undeparted, un tripinfo filtrado) +3 % [S].
Uso (cwd = plan3/): python pruebas/ref/costos_ref.py     Salida: pruebas/ref/salidas/costos_ref.txt
"""
import os
import sys
import csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
import barrer_fino as bfn  # noqa: E402

PLAN2 = os.path.join(up.RAIZ, "plan2")
SUMO = {"corredor": 2.0, "corredor_alta": 8.9, "red": 4.8, "red_alta": 5.8, "malla3": 10.7, "malla3_alta": 18.2}
ACT_TRACI = {"corredor": 5.4, "corredor_alta": 13.6, "red": 9.6, "red_alta": 10.7, "malla3": 27.5,
             "malla3_alta": 46.9}
REG = {"corredor": 4.8, "corredor_alta": 11.7, "red": 7.2, "red_alta": 8.5, "malla3": 19.7, "malla3_alta": 42.7}
POI, PERIODO = 1.07, 1.03
NIVEL_BASE = {"dem_corredor_t905": ("corredor", 0.6), "dem_corredor_t1358": ("corredor", 0.8),
              "dem_corredor_t2715": ("corredor_alta", 0.8), "dem_corredor_t2715_der": ("corredor_alta", 0.6),
              "dem_red_t905": ("red", 0.6), "dem_red_t1358": ("red", 0.8), "dem_red_t1810": ("red", 0.9),
              "dem_red_t2715": ("red", 1.4), "dem_red_t3620": ("red_alta", 1.8),
              "dem_malla3_t1810": ("malla3", 0.5), "dem_malla3_t2715": ("malla3", 0.6),
              "dem_malla3_t3620": ("malla3", 0.7), "dem_malla3_t6525": ("malla3_alta", 0.8)}
CASOS = {"P1": "corredor", "P2": "corredor_alta", "P3": "red", "P4": "red_alta", "P5": "malla3", "P6": "malla3_alta"}


def costo_corrida(esc):
    """s por corrida de sumo directo; los niveles escalan la de su red por la demanda (estimacion [S])."""
    if esc in SUMO:
        return SUMO[esc], esc
    base, f = NIVEL_BASE[esc]
    return SUMO[base] * f, base


def cuentas(esc, aleatorias):
    filas = list(csv.DictReader(open(os.path.join(PLAN2, f"barrido_{esc}.csv"), encoding="utf-8")))
    for f in filas:
        f["verde"], f["verde_transversal"] = int(f["verde"]), int(f["verde_transversal"])
        f["retraso_total_prom"] = float(f["retraso_total_prom"])
    malla = "esquema" in filas[0]
    n_tls = len(filas[0]["offsets"].split("/"))
    mins = bfn.minimos_locales(filas)
    regiones = [m for m in mins if m[0] <= 1.02 * mins[0][0]][:3]
    sb = 10 if aleatorias else 3
    fina = 0
    for _, a0, t0, _ in regiones:
        pares = (min(60, a0 + 4) - max(10, a0 - 4) + 1) * (min(60, t0 + 2) - max(10, t0 - 2) + 1)
        fina += pares * (4 if malla else 3)
    desf = 0 if malla else len(regiones) * (9 if n_tls == 2 else 81)
    nuevas_des = 10 * (20 if aleatorias else 7)
    fragil = 0 if aleatorias else 3 * 20
    mult5 = (3 if malla else 3 * (9 if n_tls == 2 else 81)) * sb + nuevas_des + fragil
    franja = 9 * sb + (9 * 20 if aleatorias else 3 * 7)
    return {"gruesa": len(filas) * sb, "fina": fina * sb, "desfases": desf * sb, "desempate": nuevas_des,
            "fragil": fragil, "mult5": mult5, "franja": franja, "regiones": len(regiones)}


def main():
    inf = up.Informe("costos_ref")
    inf("Corridas y h-proceso por celda (estimacion; regiones de la fina segun la gruesa entregada)")
    inf("celda                   llegadas   regiones gruesa  fina desfases desempate fragil mult5 franja actuado "
        "reglas | h-p fino  mult5 franja actuado reglas  total")
    total = 0.0
    etapas = []
    # P1-P6, D y P6e (P6e con la rejilla y los costos de P6) llevan todas las referencias; los 12 niveles, el fijo
    # fino, el grueso y el actuado ajustado (90 corridas, como costos_plan3.py)
    celdas = [(c, False) for c in list(CASOS.values()) + ["dem_corredor_t2715_der", "P6e"] +
              [n for n in NIVEL_BASE if n != "dem_corredor_t2715_der"]] + [(c, True) for c in CASOS.values()]
    for esc, aleatorias in celdas:
        k = cuentas("malla3_alta" if esc == "P6e" else esc, aleatorias)
        seg, base = costo_corrida("malla3_alta" if esc == "P6e" else esc)
        seg *= (POI if aleatorias else 1.0) * PERIODO
        nivel = esc not in SUMO and esc not in ("dem_corredor_t2715_der", "P6e")
        act = (63 + (270 if aleatorias else 21)) if not nivel else 90
        reg = 0 if nivel else (42 + (378 if aleatorias else 42))
        act_s = ACT_TRACI[base] / 2 * (POI if aleatorias else 1.0)
        reg_s = REG[base] * (POI if aleatorias else 1.0)
        h_fino = (k["gruesa"] + k["fina"] + k["desfases"] + k["desempate"] + k["fragil"]) * seg / 3600
        h_m5 = 0 if nivel else k["mult5"] * seg / 3600
        h_fr = 0 if nivel else k["franja"] * seg / 3600
        h_act = act * act_s / 3600
        h_reg = reg * reg_s / 3600
        h = h_fino + h_m5 + h_fr + h_act + h_reg
        total += h
        inf(f"{esc:23s} {'aleatorias' if aleatorias else 'regulares ':10s} {k['regiones']:4d} {k['gruesa']:7d} "
            f"{k['fina']:5d} {k['desfases']:6d} {k['desempate']:7d} {k['fragil']:6d} {0 if nivel else k['mult5']:5d} "
            f"{0 if nivel else k['franja']:5d} {act:6d} {reg:6d} | {h_fino:7.2f} {h_m5:5.2f} {h_fr:5.2f} "
            f"{h_act:6.2f} {h_reg:6.2f} {h:6.2f}")
        etapas.append((esc, aleatorias, {e: k[e] * seg / 3600 for e in ("gruesa", "fina", "desfases", "desempate",
                                                                         "fragil")}, h_m5, h_fr, h_act, h_reg))
    inf(f"\nTotal (P1-P6 regulares y aleatorias, 13 niveles con D): {total:.0f} h-proceso "
        f"(~{total / 12:.1f} h de reloj con 12 procesos)")
    inf("No incluye: el perfil (barrido con --bloque 600 en P1 y P3: como la celda aleatoria; bloques 30 corridas),"
        " ni las evaluaciones en T1/T2.")
    inf("\nh-proceso por trabajo (un proceso; los barridos largos se parten con --trozo; el paso del actuado es "
        "1/6 de su columna y su final el resto):")
    inf("celda                   llegadas    gruesa  fina  desf  desemp fragil mult5 franja actuado reglas")
    for esc, aleatorias, h, h_m5, h_fr, h_act, h_reg in etapas:
        inf(f"{esc:23s} {'aleatorias' if aleatorias else 'regulares ':10s} {h['gruesa']:6.2f} {h['fina']:5.2f} "
            f"{h['desfases']:5.2f} {h['desempate']:6.2f} {h['fragil']:6.2f} {h_m5:5.2f} {h_fr:6.2f} {h_act:7.2f} "
            f"{h_reg:6.2f}")
    inf.cerrar()


if __name__ == "__main__":
    main()
