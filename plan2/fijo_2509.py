"""
fijo_2509.py - Brazo de referencia "fijo_2509": el fijo tuneado del veredicto del 25.09.2026.

Uso (desde demo_rl/plan2):  python fijo_2509.py [--escenario ESC ...]
Despues:                    python ../consolidar.py --escenario ESC
                            python ../consolidar.py --escenario ESC --fijo fijo_2509

Por que (28.09.2026): el resultado principal de la tesis vuelve a ser el veredicto pre-registrado del
25.09 (ESPEC.md: metrica primaria timeLoss, fijo tuneado con la malla de entonces, avenida desde 15 s y
12 s en el corredor). El re-barrido del 27.09 (v2.1) instalo otro fijo en red, red_alta y malla3 y
re-evaluo el brazo "fijo" con el; ese fijo nuevo queda para el analisis de robustez. Este script deja
el fijo del 25.09 como un brazo mas, parciales/eval_<esc>_fijo_2509.csv, con las mismas columnas que
los parciales actuales, para que veredicto.py, sintesis_plan.py y tablas_cap5.py lo usen con --fijo.

De donde sale cada escenario:
  red, red_alta, malla3   filas "fijo" de plan2/evaluacion_<esc>.csv en el commit COMMIT (25.09.2026,
                          "plan de pruebas casos p1 a p5"). Las metricas que ese dia no se median
                          (retraso_total_prom, retraso_insercion_prom, no_insertados) quedan vacias:
                          no se reconstruyen.
  corredor, corredor_alta el fijo no cambio el 27.09: copia de parciales/eval_<esc>_fijo.csv. Antes de
                          copiar se comprueba, semilla por semilla, que todas las metricas que existian
                          el 25.09 coinciden con COMMIT; si alguna difiere, no se escribe nada.
  malla3_alta (P6)        su fijo es el del barrido con la regla del 25.09 (--metrica timeloss_prom,
                          avenida 15-35, transversal 10-25): copia de parciales/eval_malla3_alta_fijo.csv
                          cuando exista (no hay dato del 25.09 con que compararlo).
"""
import os
import io
import csv
import argparse
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
COMMIT = "37f96801c75cab69734e0bce0c022162d16419b3"
BRAZO = "fijo_2509"
DE_GIT = ("red", "red_alta", "malla3")
COPIA = ("corredor", "corredor_alta", "malla3_alta")
SIN_REFERENCIA = ("malla3_alta",)
ID = ("brazo", "modelo", "base", "semilla")


def leer(ruta):
    with open(ruta, newline="") as f:
        lector = csv.DictReader(f)
        return list(lector), list(lector.fieldnames or [])


def fijo_del_commit(esc):
    """Filas del brazo fijo de evaluacion_<esc>.csv en COMMIT, o None si el archivo no esta."""
    res = subprocess.run(["git", "show", f"{COMMIT}:plan2/evaluacion_{esc}.csv"], cwd=AQUI,
                         capture_output=True, text=True)
    if res.returncode != 0:
        return None
    return [r for r in csv.DictReader(io.StringIO(res.stdout)) if r["brazo"] == "fijo"]


def diferencias(actuales, viejas):
    """Semillas y metricas del 25.09 en que el fijo actual no coincide (lista de textos)."""
    por = {r["semilla"]: r for r in actuales}
    difs = []
    for v in viejas:
        a = por.get(v["semilla"])
        if a is None:
            difs.append(f"semilla {v['semilla']} ausente")
            continue
        difs += [f"semilla {v['semilla']} {c}: {a.get(c)} != {v[c]}"
                 for c in v if c not in ID and a.get(c) != v[c]]
    return difs


def escribir(esc, filas, campos):
    ruta = os.path.join(AQUI, "parciales", f"eval_{esc}_{BRAZO}.csv")
    with open(ruta, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, restval="", extrasaction="ignore")
        w.writeheader()
        for r in sorted(filas, key=lambda r: int(r["semilla"])):
            w.writerow(dict(r, brazo=BRAZO, modelo="fijo", base=""))
    print(f"{esc}: {len(filas)} semillas -> {ruta}")


def preparar(esc):
    ruta_fijo = os.path.join(AQUI, "parciales", f"eval_{esc}_fijo.csv")
    if not os.path.exists(ruta_fijo):
        print(f"{esc}: falta {ruta_fijo}; se copia cuando exista")
        return
    actuales, campos = leer(ruta_fijo)
    viejas = None if esc in SIN_REFERENCIA else fijo_del_commit(esc)
    if esc not in SIN_REFERENCIA and not viejas:
        raise SystemExit(f"{esc}: no hay filas del fijo en {COMMIT[:7]}:plan2/evaluacion_{esc}.csv")
    if esc in DE_GIT:
        escribir(esc, viejas, campos)
        return
    difs = diferencias(actuales, viejas) if viejas else []
    if difs:
        raise SystemExit(f"{esc}: el fijo actual no es el del 25.09 ({len(difs)} diferencias, "
                         f"p. ej. {difs[0]}); no se escribe")
    escribir(esc, actuales, campos)


def main():
    ap = argparse.ArgumentParser(description="Brazo fijo_2509 (fijo tuneado del 25.09.2026).")
    ap.add_argument("--escenario", nargs="+", default=list(DE_GIT + COPIA),
                    choices=list(DE_GIT + COPIA))
    for esc in ap.parse_args().escenario:
        preparar(esc)


if __name__ == "__main__":
    main()
