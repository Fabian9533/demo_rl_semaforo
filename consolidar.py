"""
consolidar.py - Junta las evaluaciones parciales de un escenario y hace la estadistica pareada.

Uso (desde demo_rl/plan2):  python ../consolidar.py --escenario red [--parciales parciales]

Lee parciales/eval_<esc>_<brazo>.csv (uno por brazo, los escribe evaluar.py). Un archivo se usa
solo si su nombre coincide con el brazo de sus filas: asi, al consolidar "red", se ignoran los
de "red_alta" (eval_red_alta_fijo.csv tiene brazo fijo, no alta_fijo). Escribe:
  evaluacion_<esc>.csv          todas las filas (brazo, modelo, base, semilla, metricas...)
  evaluacion_<esc>_resumen.csv  por brazo y metrica:
      n, media, sd, ic95        sobre todas las semillas del brazo (IC95 con t de Student)
      n_par, delta_pct, delta_ic95, p_wilcoxon                  frente al fijo
      n_par_act, delta_pct_act, delta_ic95_act, p_wilcoxon_act  frente al actuado
  El fijo no lleva comparaciones; el actuado lleva solo la del fijo (el veredicto lo usa como
  fila de referencia); todos los demas brazos llevan las dos.

Como se compara (plan de pruebas v2, ESPEC seccion 6):
  - Emparejamiento POR SEMILLA: se toman solo las semillas que tienen los dos brazos (n_par) y
    se comparan valor con valor de la misma semilla, nunca por la posicion en el archivo.
  - delta_pct = (media_brazo - media_ref) / media_ref * 100 sobre las semillas comunes; en el
    retraso, negativo = mejor que la referencia.
  - Para los retornos ret_retraso, ret_colas y ret_spill (negativos: son penalizaciones) el
    denominador es |media_ref|, de modo que delta positivo = mas recompensa = mejor.
  - delta_ic95: bootstrap pareado (se remuestrean semillas y se usan los dos valores de cada
    una), 10 000 remuestreos, numpy default_rng(0), percentiles 2.5 y 97.5.
  - p_wilcoxon: Wilcoxon de rangos con signo sobre las diferencias pareadas (1 si son todas 0).
  - Si la media de la referencia es 0 (p. ej. spillback en un escenario sin spillback) no hay
    delta y solo se escribe n_par.

Nuevo en el plan v2 (24.09.2026); la estadistica es la misma que tenia evaluar.py, pero pareada
por semilla y separada de la simulacion.
"""
import os
import csv
import glob
import argparse
import statistics

import numpy as np
from scipy import stats

ID = ["brazo", "modelo", "base", "semilla"]
N_BOOT = 10000
CAMPOS_RESUMEN = ["brazo", "modelo", "base", "metrica", "n", "media", "sd", "ic95",
                  "n_par", "delta_pct", "delta_ic95", "p_wilcoxon",
                  "n_par_act", "delta_pct_act", "delta_ic95_act", "p_wilcoxon_act"]


def leer_parciales(esc, carpeta):
    """Filas de todos los parciales del escenario y la lista de metricas (en orden de aparicion)."""
    filas, metricas = [], []
    for ruta in sorted(glob.glob(os.path.join(carpeta, f"eval_{esc}_*.csv"))):
        with open(ruta, newline="") as f:
            lector = csv.DictReader(f)
            propias = list(lector)
            campos = lector.fieldnames or []
        brazos = {r["brazo"] for r in propias}
        if len(brazos) != 1 or os.path.basename(ruta) != f"eval_{esc}_{next(iter(brazos))}.csv":
            print(f"  se ignora {ruta} (vacio, de otro escenario o con varios brazos)")
            continue
        filas += propias
        metricas += [c for c in campos if c not in ID and c not in metricas]
    return filas, metricas


def ordenar_brazos(filas):
    brazos = sorted({r["brazo"] for r in filas})
    referencias = [b for b in ("fijo", "actuado") if b in brazos]
    return referencias + [b for b in brazos if b not in referencias]


def por_semilla(filas, brazo, metrica):
    """{semilla: valor} de un brazo; se omiten las semillas sin valor en esa metrica."""
    return {int(r["semilla"]): float(r[metrica]) for r in filas
            if r["brazo"] == brazo and r.get(metrica, "") not in ("", None)}


def ic95(valores):
    n = len(valores)
    if n < 2:
        return 0.0
    return stats.t.ppf(0.975, n - 1) * statistics.stdev(valores) / n ** 0.5


def comparar(otro, ref, es_retorno, sufijo=""):
    """Delta % pareado por semilla de otro frente a ref (dos dict semilla -> valor)."""
    comunes = sorted(set(otro) & set(ref))
    if not comunes:
        return {}
    res = {"n_par" + sufijo: len(comunes)}
    a = np.array([otro[s] for s in comunes])
    b = np.array([ref[s] for s in comunes])
    if b.mean() == 0:
        return res
    den = abs(b.mean()) if es_retorno else b.mean()
    res["delta_pct" + sufijo] = round(float((a.mean() - b.mean()) / den * 100), 2)
    # bootstrap pareado: los mismos indices de semilla para los dos brazos
    rng = np.random.default_rng(0)
    idx = rng.integers(0, len(comunes), size=(N_BOOT, len(comunes)))
    media_a, media_b = a[idx].mean(axis=1), b[idx].mean(axis=1)
    den_b = np.abs(media_b) if es_retorno else media_b
    if np.all(den_b != 0):
        deltas = (media_a - media_b) / den_b * 100
        res["delta_ic95" + sufijo] = f"[{np.percentile(deltas, 2.5):.2f}, {np.percentile(deltas, 97.5):.2f}]"
    difs = a - b
    if np.any(difs != 0):
        try:
            res["p_wilcoxon" + sufijo] = f"{stats.wilcoxon(difs).pvalue:.3g}"
        except ValueError:
            pass
    else:
        res["p_wilcoxon" + sufijo] = "1"
    return res


def resumir(filas, metricas):
    resumen = []
    for brazo in ordenar_brazos(filas):
        primera = next(r for r in filas if r["brazo"] == brazo)
        for m in metricas:
            vals = por_semilla(filas, brazo, m)
            if not vals:
                continue
            v = list(vals.values())
            fila = {"brazo": brazo, "modelo": primera.get("modelo", ""), "base": primera.get("base", ""),
                    "metrica": m, "n": len(v), "media": round(statistics.mean(v), 4),
                    "sd": round(statistics.stdev(v), 4) if len(v) > 1 else 0, "ic95": round(ic95(v), 4)}
            es_retorno = m.startswith("ret_")
            if brazo != "fijo":
                fila.update(comparar(vals, por_semilla(filas, "fijo", m), es_retorno))
            if brazo not in ("fijo", "actuado"):
                fila.update(comparar(vals, por_semilla(filas, "actuado", m), es_retorno, "_act"))
            resumen.append(fila)
    return resumen


def imprimir(esc, resumen):
    print(f"\n{esc}: retraso (timeloss_prom, s/veh), media +- IC95; delta % pareado por semilla [IC95] "
          f"y p de Wilcoxon")
    for r in resumen:
        if r["metrica"] != "timeloss_prom":
            continue
        texto = f"  {r['brazo']:20s} n={r['n']:2d}  {r['media']:7.2f} +- {r['ic95']:5.2f}"
        for suf, ref in (("", "fijo"), ("_act", "actuado")):
            if "delta_pct" + suf in r:
                texto += (f" | vs {ref} {r['delta_pct' + suf]:+6.1f}% {r.get('delta_ic95' + suf, '')} "
                          f"p={r.get('p_wilcoxon' + suf, '')} (n_par {r['n_par' + suf]})")
        print(texto)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escenario", required=True)
    ap.add_argument("--parciales", default="parciales", help="carpeta de los CSV parciales")
    args = ap.parse_args()
    esc = args.escenario
    filas, metricas = leer_parciales(esc, args.parciales)
    if not filas:
        raise SystemExit(f"No hay parciales de {esc} en {args.parciales}/")
    orden = {b: k for k, b in enumerate(ordenar_brazos(filas))}
    filas.sort(key=lambda r: (orden[r["brazo"]], int(r["semilla"])))
    with open(f"evaluacion_{esc}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ID + metricas, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    resumen = resumir(filas, metricas)
    with open(f"evaluacion_{esc}_resumen.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS_RESUMEN)
        w.writeheader()
        w.writerows(resumen)
    print(f"{len(filas)} filas de {len(orden)} brazos -> evaluacion_{esc}.csv y evaluacion_{esc}_resumen.csv")
    imprimir(esc, resumen)


if __name__ == "__main__":
    main()
