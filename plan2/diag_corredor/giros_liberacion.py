"""
giros_liberacion.py - Cuando sale el vehiculo que espera dentro del cruce para girar a la izquierda: en un hueco
del verde o al terminar el verde (ambar o rojo), y cuantos verdes terminan por periodo (diagnostico del corredor,
25.10.2026; lo usa mecanismo_2715.md).

Lee los registros por segundo de bloqueo.py y de bloqueo_niveles.py (seg_<base>.csv.gz y met_<base>.json) sin
correr nada. Una "liberacion" es un segundo t en que baja el numero de vehiculos detenidos en el primer tramo interno
del giro a la izquierda del acceso (columna <acceso>_izq_dentro: el que gira espera ahi el hueco); se clasifica por el
estado del link de ese giro en t: g o G (hueco en el verde) o y o r (salio al terminar el verde). "Fines de verde" son
los cambios de verde a ambar del link en el periodo.

Uso (desde plan2/):
  python diag_corredor/giros_liberacion.py --datos <carpeta> --bases O_fijo_s1001,O_actual_s1001,... --salida <csv>
  (o --patron 'O_*' para tomar todas las bases cuyo met_<base>.json calce con el patron)
"""
import os
import sys
import csv
import json
import glob
import fnmatch
import argparse
import statistics

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import bloqueo as bq     # noqa: E402

ACCESOS_GIRO = ["W_C1", "C2_C1", "N1_C1", "S2_C2"]      # los que tienen giro a la izquierda en el periodo 2 de O


def una(datos, base):
    with open(os.path.join(datos, f"met_{base}.json"), encoding="utf-8") as f:
        meta = json.load(f)
    acc = {a: {"tls": d["tls"], "mov": {k: tuple(v) for k, v in d["mov"].items()}} for a, d in meta["accesos"].items()}
    filas = bq.leer_segundos(os.path.join(datos, f"seg_{base}.csv.gz"))
    out = []
    for p, (t0, t1) in bq.PERIODOS.items():
        for a in ACCESOS_GIRO:
            k = acc[a]["mov"]["l"][0]
            tls = acc[a]["tls"]
            lib = {"verde": 0, "fin": 0}
            fines, previa = 0, None
            for f in filas:
                if previa is not None and t0 <= f["t"] <= t1:
                    est, est0 = f["estado"][tls][k], previa["estado"][tls][k]
                    baja = previa[a]["izq_dentro"] - f[a]["izq_dentro"]
                    if baja > 0:
                        lib["verde" if est in "gG" else "fin"] += baja
                    if est0 in "gG" and est == "y":
                        fines += 1
                previa = f
            total = lib["verde"] + lib["fin"]
            out.append({"base": base, "periodo": p, "acceso": a, "liberaciones": total,
                        "en_hueco_del_verde": lib["verde"], "al_terminar_el_verde": lib["fin"],
                        "frac_al_terminar": round(lib["fin"] / total, 3) if total else "",
                        "fines_de_verde": fines})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datos", required=True)
    ap.add_argument("--bases", default="")
    ap.add_argument("--patron", default="")
    ap.add_argument("--salida", required=True)
    args = ap.parse_args()
    bases = [b for b in args.bases.split(",") if b]
    if args.patron:
        todas = sorted(os.path.basename(x)[4:-5] for x in glob.glob(os.path.join(args.datos, "met_*.json")))
        bases += [b for b in todas if fnmatch.fnmatch(b, args.patron)]
    filas = []
    for b in bases:
        filas += una(args.datos, b)
        print("leido", b, flush=True)
    with open(args.salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print("Escrito", args.salida)


if __name__ == "__main__":
    main()
