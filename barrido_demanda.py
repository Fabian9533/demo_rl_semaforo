"""
barrido_demanda.py - Barrido de demanda en el corredor de P1 (analisis complementario).

Uso (desde demo_rl/plan2):
  python ../barrido_demanda.py preparar     escribe los escenarios derivados en el cwd
  python ../barrido_demanda.py resumir      junta demanda/eval_*.csv y escribe la tabla y la figura

Pregunta: como cambia el resultado con la demanda, sin cambiar la red ni los controles. Se toma la
red de P1 (dos semaforos, un carril) y toda la demanda de corredor.rou.xml x f, con f en
escenarios_plan2.FACTORES_DEMANDA (0.5 a 2.25), mas un perfil que cambia dentro de la hora
(corredor_var: bloques de 10 min con x1.0, 1.5, 2.0, 2.0, 1.5 y 1.0, en promedio x1.5). Brazos por
nivel, todos con las semillas de evaluacion 1001-1030:
  fijo      el fijo re-barrido para ese nivel (barrer_fijo.py, semillas 2001-2003, retraso total)
  fijo_p1   el programa fijo de P1 sin retunear (lo que hace un plan de ciudad que no se ajusta)
  actuado   el actuado de SUMO
  ippo_vecinos_s4042 / ippo_vecinos_s2042   las politicas publicadas de IPPO vecinos en P1 (entrenada
            con x1.0) y en P2 (x2.0), sin reentrenar
Los trabajos de la cola (generar_trabajos.py) escriben demanda/eval_<esc>_<brazo>.csv. Con x1.0 y
x2.0 los brazos deben dar, semilla a semilla, lo mismo que P1 y P2 (parciales/eval_corredor_*.csv y
eval_corredor_alta_*.csv): resumir lo comprueba. Salidas de resumir:
  demanda/resumen_demanda.csv   por nivel y brazo: media del retraso total y del timeLoss y delta %
                                frente al fijo de ese nivel (bootstrap pareado 10 000, rng 0, Wilcoxon)
  TESIS/secciones/tablas/demanda_corredor.tex y TESIS/images/fig_plan2_demanda.png
"""
import os
import re
import csv
import sys
import argparse
import xml.etree.ElementTree as ET

import numpy as np
from scipy import stats

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import escenarios_plan2 as ep            # noqa: E402

PERFIL = (1.0, 1.5, 2.0, 2.0, 1.5, 1.0)     # corredor_var: factor por bloque de 600 s
BRAZOS = [("fijo_p1", "Plan fijo de P1 sin retunear"), ("actuado", "Actuado (SUMO)"),
          ("ippo_vecinos_s4042", "IPPO vecinos entrenado con x1.0 (P1)"),
          ("ippo_vecinos_s2042", "IPPO vecinos entrenado con x2.0 (P2)")]
METRICAS = [("retraso_total_prom", "retraso total"), ("timeloss_prom", "timeLoss")]
N_BOOT = 10000


def niveles():
    """[(escenario, etiqueta, factor medio)] en orden."""
    filas = [(f"corredor_f{f:03d}", ("%.2f" % (f / 100)).rstrip("0"), f / 100)
             for f in ep.FACTORES_DEMANDA]
    filas = [(e, t + "0" if t.endswith(".") else t, f) for e, t, f in filas]
    return filas + [("corredor_var", "variable", sum(PERFIL) / len(PERFIL))]


def escribir_cfg(destino, rou, add):
    arbol = ET.parse("corredor.sumocfg")
    arbol.getroot().find(".//route-files").set("value", rou)
    arbol.getroot().find(".//additional-files").set("value", add)
    arbol.write(destino, encoding="unicode")


def rou_escalado(f):
    with open("corredor.rou.xml", encoding="utf-8") as fh:
        texto = fh.read()
    return re.sub(r'vehsPerHour="([0-9.]+)"',
                  lambda m: 'vehsPerHour="%d"' % round(float(m.group(1)) * f), texto)


def rou_perfil():
    """Cada flow de corredor.rou.xml partido en bloques de 600 s con el factor de PERFIL, ordenados
    por inicio (SUMO lee las rutas por tramos de tiempo y exige el archivo ordenado). Los ids llevan
    _b<bloque>, asi que las metricas de extremo a extremo del corredor no se miden aqui."""
    raiz = ET.parse("corredor.rou.xml").getroot()
    lineas, flujos = ["<routes>"], []
    for hijo in raiz:
        if hijo.tag != "flow":
            lineas.append("    " + ET.tostring(hijo, encoding="unicode").strip())
            continue
        ini, fin = float(hijo.get("begin")), float(hijo.get("end"))
        for k, factor in enumerate(PERFIL):
            a, b = max(ini, 600 * k), min(fin, 600 * (k + 1))
            if a >= b:
                continue
            f = dict(hijo.attrib, id=f"{hijo.get('id')}_b{k}", begin=str(int(a)), end=str(int(b)),
                     vehsPerHour=str(round(float(hijo.get("vehsPerHour")) * factor)))
            atributos = " ".join(f'{c}="{v}"' for c, v in f.items())
            flujos.append((a, len(flujos), "    <flow " + atributos + "/>"))
    lineas += [x[2] for x in sorted(flujos)]
    return "\n".join(lineas) + "\n</routes>\n"


def preparar():
    for esc, _, f in niveles():
        texto = rou_perfil() if esc == "corredor_var" else rou_escalado(f)
        with open(f"{esc}.rou.xml", "w", encoding="utf-8") as fh:
            fh.write(texto)
        if not os.path.exists(f"{esc}.add.xml"):          # plantilla; el barrido la reemplaza
            with open("corredor.add.xml", encoding="utf-8") as fh, \
                    open(f"{esc}.add.xml", "w", encoding="utf-8") as g:
                g.write(fh.read())
        escribir_cfg(f"{esc}.sumocfg", f"{esc}.rou.xml", f"{esc}.add.xml")
        escribir_cfg(f"{esc}_p1.sumocfg", f"{esc}.rou.xml", "corredor.add.xml")
        print(f"  {esc}: {esc}.rou.xml, {esc}.sumocfg, {esc}_p1.sumocfg")


def leer(ruta, metrica):
    if not os.path.exists(ruta):
        return {}
    with open(ruta, newline="") as fh:
        return {int(r["semilla"]): float(r[metrica]) for r in csv.DictReader(fh) if r.get(metrica)}


def delta(x, y):
    """Delta % de x frente a y pareado por semilla, IC95 bootstrap y p de Wilcoxon."""
    s = sorted(set(x) & set(y))
    a, b = np.array([x[k] for k in s]), np.array([y[k] for k in s])
    rng = np.random.default_rng(0)
    idx = rng.integers(0, len(s), size=(N_BOOT, len(s)))
    bs = (a[idx].mean(1) / b[idx].mean(1) - 1) * 100
    p = stats.wilcoxon(a, b).pvalue if np.any(a != b) else 1.0
    return (a.mean() / b.mean() - 1) * 100, np.percentile(bs, 2.5), np.percentile(bs, 97.5), p, len(s)


def comprobar():
    """x1.0 y x2.0 deben reproducir P1 y P2 semilla a semilla (mismo timeLoss)."""
    pares = [("corredor_f100", "corredor", ["fijo", "actuado", "ippo_vecinos_s4042"]),
             ("corredor_f200", "corredor_alta", ["fijo", "actuado", "ippo_vecinos_s2042"])]
    ok = True
    for esc, caso, brazos in pares:
        for brazo in brazos:
            a = leer(os.path.join("demanda", f"eval_{esc}_{brazo}.csv"), "timeloss_prom")
            b = leer(os.path.join("parciales", f"eval_{caso}_{brazo}.csv"), "timeloss_prom")
            iguales = bool(a) and a == {k: b.get(k) for k in a}
            ok &= iguales
            estado = "OK" if iguales else "DISTINTO"
            print(f"  compuerta {esc} {brazo} = {caso}: {estado} ({len(a)} semillas)")
    return ok


def resumir(tesis):
    filas = []
    for esc, etq, f in niveles():
        ref = {m: leer(os.path.join("demanda", f"eval_{esc}_fijo.csv"), m) for m, _ in METRICAS}
        for brazo, _ in [("fijo", "")] + BRAZOS:
            fila = {"escenario": esc, "nivel": etq, "factor": round(f, 3), "brazo": brazo}
            for m, _ in METRICAS:
                x = leer(os.path.join("demanda", f"eval_{esc}_{brazo}.csv"), m)
                fila[m] = round(float(np.mean(list(x.values()))), 2) if x else ""
                if brazo != "fijo" and x and ref[m]:
                    d, lo, hi, p, n = delta(x, ref[m])
                    fila.update({f"delta_{m}": round(d, 2), f"ic_lo_{m}": round(lo, 2),
                                 f"ic_hi_{m}": round(hi, 2), f"p_{m}": float(f"{p:.3g}"), "n": n})
            filas.append(fila)
    campos = ["escenario", "nivel", "factor", "brazo", "retraso_total_prom", "timeloss_prom", "n"]
    for m, _ in METRICAS:
        campos += [f"delta_{m}", f"ic_lo_{m}", f"ic_hi_{m}", f"p_{m}"]
    os.makedirs("demanda", exist_ok=True)
    with open(os.path.join("demanda", "resumen_demanda.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, restval="")
        w.writeheader()
        w.writerows(filas)
    print("Escrito demanda/resumen_demanda.csv")
    ok = comprobar()
    tabla_tex(filas, os.path.join(tesis, "secciones", "tablas", "demanda_corredor.tex"))
    figura(filas, os.path.join(tesis, "images", "fig_plan2_demanda.png"))
    return ok


def celda(fila, m):
    d = fila.get(f"delta_{m}")
    if d in (None, ""):
        return "--"
    txt = f"{d:+.1f}".replace("-", "$-$")
    return txt + ("" if fila[f"p_{m}"] < 0.05 else r"$^{\mathrm{ns}}$")


def tabla_tex(filas, ruta):
    por = {(f["escenario"], f["brazo"]): f for f in filas}
    lineas = []
    for esc, etq, _ in niveles():
        fijo = por[(esc, "fijo")]
        celdas = [celda(por[(esc, b)], m) for m, _ in METRICAS for b, _ in BRAZOS]
        ref = fijo["retraso_total_prom"]
        nivel = etq if etq == "variable" else r"$\times$" + etq
        lineas.append(" & ".join([nivel, "--" if ref == "" else f"{ref:.1f}"] + celdas) + r" \\")
    cab = " & ".join(r"\makecell{" + x + "}" for x in
                     [r"Plan\\de P1", "Actuado", r"IPPO\\P1", r"IPPO\\P2"])
    texto = "\n".join([
        "% Generado por barrido_demanda.py resumir. No editar a mano.",
        r"\begin{table}[H]", r"\setstretch{1}", r"\centering", r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{lr" + "r" * 8 + "}", r"\toprule",
        r" & & \multicolumn{4}{c}{$\Delta$ retraso total (\%)} & "
        r"\multicolumn{4}{c}{$\Delta$ timeLoss (\%)} \\",
        r"\cmidrule(lr){3-6}\cmidrule(lr){7-10}",
        r"Demanda & \makecell{Fijo\\(s/veh)} & " + cab + " & " + cab + r" \\", r"\midrule"]
        + lineas + [r"\bottomrule", r"\end{tabular}",
                    r"\caption[Barrido de demanda en el corredor]{Barrido de demanda en la red de P1: cambio "
                    r"del retraso de cada control frente al fijo re-barrido para ese nivel (semillas de "
                    r"evaluación 1001 a 1030, IC95\,\% bootstrap pareado; ns: Wilcoxon $p \geq 0.05$). "
                    r"Fijo: "
                    r"retraso total del fijo re-barrido. Plan de P1: el programa fijo de P1 sin retunear. "
                    r"IPPO P1 y P2: las políticas publicadas de IPPO vecinos entrenadas con $\times$1.0 y "
                    r"$\times$2.0, sin reentrenar. Variable: bloques de 10~min con $\times$1.0, 1.5, "
                    r"2.0, 2.0, "
                    r"1.5 y 1.0.}", r"\label{tab:plan2-demanda}", r"\end{table}"])
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write(texto + "\n")
    print("Escrito", ruta)


def figura(filas, ruta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    por = {(f["escenario"], f["brazo"]): f for f in filas}
    esc_niveles = niveles()
    cmap = LinearSegmentedColormap.from_list("div", ["#2a78d6", "#f0efec", "#e34948"])
    fig, ejes = plt.subplots(2, 1, figsize=(8.4, 5.4), facecolor="#fcfcfb")
    for ax, (m, nombre) in zip(ejes, METRICAS):
        valores = [[por[(esc, b)].get(f"delta_{m}", 0.0) or 0.0 for esc, _, _ in esc_niveles]
                   for b, _ in BRAZOS]
        ax.imshow([[max(-50, min(50, v)) for v in fila] for fila in valores], cmap=cmap,
                  norm=TwoSlopeNorm(vmin=-50, vcenter=0, vmax=50), aspect="auto")
        for i, fila in enumerate(valores):
            for j, v in enumerate(fila):
                txt = ("%+.0f" if abs(v) >= 100 else "%+.1f") % v
                ax.text(j, i, txt.replace("-", "\u2212"), ha="center", va="center", fontsize=7.5,
                        color="white" if abs(v) > 30 else "#0b0b0b", fontweight="bold")
        ax.set_xticks(range(len(esc_niveles)))
        ax.set_xticklabels([e if e == "variable" else "×" + e for _, e, _ in esc_niveles], fontsize=7.8,
                           color="#52514e")
        ax.set_yticks(range(len(BRAZOS)))
        ax.set_yticklabels([n.replace(" entrenado", "\nentrenado") for _, n in BRAZOS], fontsize=7.5,
                           color="#52514e")
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(f"Cambio del {nombre} frente al fijo re-barrido para cada demanda (%)", fontsize=8.6,
                     loc="left")
    fig.tight_layout()
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor="#fcfcfb")
    plt.close(fig)
    print("Escrito", ruta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["preparar", "resumir"])
    ap.add_argument("--tesis", default=os.path.join(AQUI, "TESIS"))
    args = ap.parse_args()
    if args.modo == "preparar":
        preparar()
    else:
        sys.exit(0 if resumir(args.tesis) else 1)


if __name__ == "__main__":
    main()
