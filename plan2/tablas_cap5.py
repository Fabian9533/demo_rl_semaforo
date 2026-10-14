"""tablas_cap5.py - Tablas tab:plan2-resumen y tab:plan2-metas del Cap. V.

Uso (desde demo_rl/plan2):  python tablas_cap5.py [--modelo ippo_vecinos]
                            [--metrica M] [--fijo BRAZO] [--prefijo P] [--casos P1-P5] [--sin-trivial]
  principal (28.09.2026): python tablas_cap5.py --metrica timeloss_prom --fijo fijo_2509 --sin-trivial
  robustez:               python tablas_cap5.py --prefijo robustez_
Escribe TESIS/secciones/tablas/plan2_resumen.tex y plan2_metas.tex (el Cap. V las incluye con \\input).

tab:plan2-resumen: retraso del fijo por caso y, por modelo y caso, retraso de la base publicada,
Delta vs fijo y veredicto abreviado. Fuente: plan2/veredicto.csv (veredicto.py; metrica primaria
veredicto.METRICA, el retraso total desde el 27.09.2026) y la fila del fijo de
plan2/evaluacion_<esc>_resumen.csv.

tab:plan2-metas: Delta (%) frente al fijo de la base publicada de un modelo (por defecto IPPO vecinos) en
las cuatro metricas con meta de la introduccion. Fuente: plan2/evaluacion_<esc>_resumen.csv (delta_pct);
base publicada de plan2/veredicto.csv.

Formato de numeros igual que veredicto.py: retraso con 2 decimales, deltas con '{:+.1f}'.
No recalcula nada: solo lee y formatea. Cambios del 27.09.2026: lee el veredicto vigente (antes el
congelado de las 03:55), metrica primaria de veredicto.py, casos P1-P6, fila del control trivial y
marca * de las politicas iguales al trivial; escribe los archivos en vez de imprimirlos.

Cambios del 28.09.2026 (sin opciones, todo queda como antes): las opciones de veredicto.py.
  --metrica, --fijo BRAZO  la fila del fijo y los deltas salen del resumen frente a BRAZO
                           (evaluacion_<esc>_resumen_<BRAZO>.csv; fijo_2509 = el fijo del 25.09).
  --prefijo P              lee plan2/<P>veredicto.csv y escribe <P>plan2_resumen.tex y <P>plan2_metas.tex,
                           con labels tab:<P sin _>-plan2-... y el prefijo al inicio de los titulos.
  --casos, --sin-trivial   solo esos casos; sin la fila del control trivial.
  Con timeLoss, los titulos son los del 25.09 (retraso = timeLoss). Una celda sin comparacion con el
  fijo todavia (P6 mientras corre su barrido) se escribe "pendiente" y el archivo lleva un comentario
  % PENDIENTE-<caso>.
"""
import os
import sys
import csv
import argparse

PLAN2 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(PLAN2))
import veredicto as vd          # noqa: E402

MODELOS = [("actuado", "Actuado"), ("trivial", "Trivial"), ("ql", "Q-learning"), ("sarsa", "SARSA"),
           ("ql_colas", r"\texttt{ql\_colas}"), ("dqn", "DQN"), ("ippo_local", "IPPO local"),
           ("ippo_vecinos", "IPPO vecinos"), ("ippo_spill", "IPPO spill"), ("mappo", "MAPPO")]
ABREV = {"FUNCIONA": "FUN", "MEJORA": "MEJ", "EMPATA": "EMP", "FALLA": "FAL"}
TABLAS = os.path.join(os.path.dirname(PLAN2), "TESIS", "secciones", "tablas")


def menos(texto):
    return texto.replace("-", "$-$")


def delta(x):
    s = f"{float(x):+.1f}"
    if s in ("+0.0", "-0.0"):
        s = "0.0"
    return menos(s)


def veredicto_corto(v):
    v = v.strip()
    marca = "*" if "(= trivial)" in v else ""
    v = v.replace(" (= trivial)", "")
    if v in ABREV:
        return ABREV[v] + marca
    if v.startswith("= vecinos"):
        return "= vecinos"
    if v.startswith("PENDIENTE (no convergi"):
        prov = v.split("provisional:")[1].strip(" )")
        return f"PEN ({ABREV[prov]})" + marca
    if v.startswith("PENDIENTE (falta"):
        return "pendiente"
    if v.startswith("PENDIENTE"):
        return "sin datos"
    raise ValueError(v)


def cabecera():
    return " & ".join(r"\makecell{" + c + r"\\" + e.replace("_", r"\_") + "}" for c, e in vd.CASOS)


def sin_fijo(res):
    """Casos sin la fila del fijo de referencia (su columna queda pendiente)."""
    return [(c, e) for c, e in vd.CASOS if not res[e].get((vd.FIJO, vd.METRICA))]


def comentario_pendiente(res):
    return "".join(f"% PENDIENTE-{c}: falta evaluar el fijo de referencia ({vd.FIJO}) de {e}; al "
                   f"terminar, regenerar con plan2/tablas_cap5.py\n" for c, e in sin_fijo(res))


def titulo(corto, largo):
    """Titulos con el prefijo al inicio (p. ej. Robustez: ...), como en veredicto.py."""
    t = vd.titulo_prefijo()
    if not t:
        return corto, largo
    return f"{t}: {corto[0].lower()}{corto[1:]}", f"{t}. {largo}"


def escribir(nombre, texto):
    ruta = os.path.join(TABLAS, vd.PREFIJO + nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("% Generado por plan2/tablas_cap5.py. No editar a mano.\n" + texto + "\n")
    print("Escrito", ruta)


def lista_casos(casos):
    """"P5", "P5 ni en P6", "P4, P5 ni en P6"."""
    if len(casos) < 2:
        return "".join(casos)
    return ", ".join(casos[:-1]) + " ni en " + casos[-1]


def tabla_resumen(ver, res):
    lin = [r"Modelo & " + cabecera() + r" \\", r"\midrule"]
    fijo = []
    for _, esc in vd.CASOS:
        r = res[esc].get((vd.FIJO, vd.METRICA))
        fijo.append("--" if not r else
                    r"\makecell{" + f"{float(r['media']):.2f}" + r"\\$\pm$ " + f"{float(r['ic95']):.2f}"
                    + "}")
    lin += [r"\makecell[l]{Fijo tuneado\\(s/veh)} & " + " & ".join(fijo) + r" \\", r"\midrule"]
    usados = set()
    for m, nombre in MODELOS:
        celdas = []
        for caso, _ in vd.CASOS:
            r = ver.get((caso, m))
            v = veredicto_corto(r["veredicto"]) if r else "sin datos"
            usados.add(v)
            if not r or not r["retraso"] or v in ("= vecinos", "pendiente") or not r["delta_fijo"]:
                celdas.append(v)
                continue
            celdas.append(r"\makecell{" + f"{float(r['retraso']):.2f}" + r"\\" + delta(r["delta_fijo"])
                          + " " + v + "}")
        lin.append(nombre + " & " + " & ".join(celdas) + r" \\")
    sin_ql_colas = [c for c, _ in vd.CASOS
                    if (ver.get((c, "ql_colas")) or {}).get("veredicto", "") == "PENDIENTE (sin datos)"]
    if vd.METRICA == "timeloss_prom":
        inicio = (r"Resumen del plan de pruebas por "
                  r"caso y modelo, sobre las semillas de evaluación 1001 a 1030. Primera fila: retraso del "
                  r"fijo tuneado (s/veh), media $\pm$ semiamplitud del IC95\,\%. Demás filas: retraso medio "
                  r"del modelo (s/veh), es decir, de la política publicada de su base publicada, ")
        ql_colas = r"\texttt{ql\_colas} (``Q-learning (colas)'' en las tablas de veredicto)"
    else:
        que = "retraso total" if vd.METRICA == "retraso_total_prom" else "retraso (timeLoss)"
        inicio = (r"Resumen del plan de pruebas por "
                  r"caso y modelo, sobre las semillas de evaluación 1001 a 1030, con el " + que + r" "
                  r"(Ecuación~\ref{eq:retraso-total}). Primera fila: el del fijo tuneado (s/veh), "
                  r"media $\pm$ "
                  r"semiamplitud del IC95\,\%. Demás filas: el del modelo (s/veh), es decir, de la política "
                  r"publicada "
                  r"de su base publicada, ")
        ql_colas = r"\texttt{ql\_colas}"
    largo = (inicio +
             r"y debajo $\Delta_f$ (\%) con el veredicto abreviado: FUN, funciona; MEJ, "
             r"mejora; EMP, empata; FAL, falla. PEN (x): pendiente porque la base publicada no converge, "
             r"con el "
             r"veredicto provisional x. "
             + ("" if vd.SIN_TRIVIAL else
                r"*: la política da el mismo retraso total y la misma espera que el control trivial. ")
             + r"= vecinos: el término de \textit{spillback} no se activa y la política es la de "
             r"IPPO vecinos. "
             + ("" if "pendiente" not in usados else
                r"Pendiente: el caso aún no tiene la comparación con el fijo tuneado. ")
             + ("" if not sin_ql_colas else
                r"Sin datos: la ablación " + ql_colas + " no se corrió en "
                + lista_casos(sin_ql_colas) + ". ")
             + r"Los intervalos, los valores $p$ y $\Delta_a$ están en las tablas por modelo.")
    corto, largo = titulo("Retraso y cambio frente al fijo por caso y modelo", largo)
    return comentario_pendiente(res) + "\n".join([
        r"\begin{table}[H]", r"\setstretch{1}", r"\centering", r"\scriptsize",
        r"\setlength{\tabcolsep}{2.5pt}",
        r"\begin{tabular}{l" + "c" * len(vd.CASOS) + "}", r"\toprule"] + lin + [
        r"\bottomrule", r"\end{tabular}",
        r"\caption[" + corto + "]{" + largo + "}",
        r"\label{" + vd.etiqueta("plan2-resumen") + "}", r"\end{table}"])


def tabla_metas(ver, res, modelo):
    retraso = "Retraso por vehículo" if vd.METRICA == "timeloss_prom" else "Retraso total por vehículo"
    metas = [(vd.METRICA, retraso, r"$-25$ a $-40$"),
             ("cola_prom", r"Cola promedio", r"$\leq -20$"),
             ("co2_prom", r"Emisiones de CO$_2$", r"$\leq -5$"),
             ("throughput", r"\textit{Throughput}", r"$\geq +10$")]
    bases = [(ver.get((caso, modelo)) or {}).get("base_publicada", "") for caso, _ in vd.CASOS]
    lin = [r"Métrica & \makecell{Meta\\$\Delta$ (\%)} & " + cabecera() + r" \\", r"\midrule"]
    for met, nombre, meta in metas:
        celdas = []
        for (caso, esc), b in zip(vd.CASOS, bases):
            r = res[esc].get((f"{modelo}_s{b}", met))
            celdas.append(delta(r["delta_pct"]) if r and r.get("delta_pct") not in ("", None) else "--")
        lin.append(nombre + " & " + meta + " & " + " & ".join(celdas) + r" \\")
    comentario = "% bases publicadas de " + modelo + ": " + ", ".join(
        f"{c} {b}" for (c, _), b in zip(vd.CASOS, bases))
    corto, largo = titulo("Metas cuantitativas frente al fijo tuneado", (
        r"Metas cuantitativas de la tesis y "
        r"política publicada de " + vd.NOMBRE[modelo] + r". Cambio porcentual de la media "
        r"frente al "
        r"fijo tuneado ($\Delta$, \%) en cada caso, sobre las semillas de evaluación 1001 a 1030 y "
        r"pareado por semilla. Meta: la de la introducción, expresada como cambio frente al fijo; "
        r"un valor negativo es una reducción."))
    return comentario_pendiente(res) + "\n".join([
        comentario, r"\begin{table}[H]", r"\setstretch{1}", r"\centering", r"\footnotesize",
        r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{lc" + "r" * len(vd.CASOS) + "}", r"\toprule"]
        + lin + [r"\bottomrule", r"\end{tabular}",
                 r"\caption[" + corto + "]{" + largo + "}",
                 r"\label{" + vd.etiqueta("plan2-metas") + "}", r"\end{table}"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="ippo_vecinos", help="modelo de la tabla de metas")
    ap.add_argument("--metrica", choices=["retraso_total_prom", "timeloss_prom"], default=vd.METRICA)
    ap.add_argument("--fijo", default="fijo", help="brazo de referencia (fijo_2509: el del 25.09)")
    ap.add_argument("--prefijo", default="", help="prefijo de veredicto.csv, de las salidas y de los labels")
    ap.add_argument("--casos", default=None, help='solo esos casos, p. ej. "P1-P5"')
    ap.add_argument("--sin-trivial", action="store_true", help="sin la fila del control trivial")
    args = ap.parse_args()
    vd.configurar(args.metrica, args.fijo, args.sin_trivial, args.casos, args.prefijo)
    if args.sin_trivial:
        MODELOS[:] = [mn for mn in MODELOS if mn[0] != "trivial"]
    with open(os.path.join(PLAN2, vd.PREFIJO + "veredicto.csv"), encoding="utf-8") as f:
        ver = {(r["caso"], r["modelo"]): r for r in csv.DictReader(f)}
    res = {esc: vd.leer_resumen(PLAN2, esc) for _, esc in vd.CASOS}
    escribir("plan2_resumen.tex", tabla_resumen(ver, res))
    escribir("plan2_metas.tex", tabla_metas(ver, res, args.modelo))


if __name__ == "__main__":
    main()
