"""
tablas_tex.py - Genera las tablas LaTeX del capitulo de resultados a partir de los CSV,
para que ningun numero del documento se copie a mano.

Uso: python tablas_tex.py [cruce cruce2 corredor red]   (por defecto, los que tengan evaluacion)

Escribe en TESIS/secciones/tablas/:
  <esc>_episodios.tex          tabla completa por episodio (entradas y salidas), en bloques
  <esc>_episodios_resumen.tex  filas escogidas (1, 2, 3, 5, 10, ... y las de evaluacion greedy)
  <esc>_evaluacion.tex         evaluacion final por control: media, IC95 %, delta vs fijo, p
  resumen_escenarios.tex       una fila por escenario con retraso y deltas del agente y del actuado
Cada archivo se incluye desde capitulo5.tex o anexos.tex con \\input{secciones/tablas/...}.
"""
import os
import csv
import sys

SALIDA = os.path.join("TESIS", "secciones", "tablas")
FILAS_POR_BLOQUE = 40


def leer(nombre):
    if not os.path.exists(nombre):
        return []
    with open(nombre, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x, dec=2):
    """Numero con signo menos matematico (el guion de texto no es un signo menos)."""
    try:
        return f"{float(x):.{dec}f}".replace("-", "$-$")
    except (TypeError, ValueError):
        return "--"


def con_signo(x, dec=1):
    try:
        return f"{float(x):+.{dec}f}".replace("-", "$-$")
    except (TypeError, ValueError):
        return "--"


def intervalo(texto):
    return texto.replace("-", "$-$") if texto else ""


def escribir(nombre, texto):
    os.makedirs(SALIDA, exist_ok=True)
    ruta = os.path.join(SALIDA, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("% Generado por tablas_tex.py a partir de los CSV del proyecto. No editar a mano.\n")
        f.write(texto)
    print("Escrito", ruta)


def abrir_tabla(tamano=r"\scriptsize"):
    """Cabecera comun: interlineado sencillo dentro del flotante y columnas mas juntas."""
    return (r"\begin{table}[H]" "\n" r"\setstretch{1}" "\n" r"\centering" "\n"
            + tamano + "\n" r"\setlength{\tabcolsep}{3pt}" "\n")


def bloque_train(esc):
    filas = leer(f"resultados_{esc}.csv")
    train = [f for f in filas if f["modo"] == "train"]
    inicio = 0
    for i in range(1, len(train)):
        if int(train[i]["episodio"]) <= int(train[i - 1]["episodio"]):
            inicio = i
    return train[inicio:], filas


def fila_episodio(f, estados_inicio):
    celdas = [f["episodio"], num(f["epsilon"], 3), f["semilla"], str(estados_inicio),
              num(f["timeloss_prom"]), num(f["espera_prom"]), num(f["cola_prom"]),
              num(f["recompensa_decision"]), f["cambios_fase"], num(f["paradas_prom"]),
              num(f.get("eval_timeloss")), num(f.get("eval_espera"))]
    return " & ".join(celdas) + r" \\"


ENCABEZADO_EPISODIOS = "\n".join([
    r"\begin{tabular}{rrrrrrrrrrrr}",
    r"\toprule",
    r"\multicolumn{4}{c}{Entradas del episodio} & "
    r"\multicolumn{6}{c}{Salidas del episodio (entrenamiento, $\varepsilon>0$)} & "
    r"\multicolumn{2}{c}{Política congelada} \\",
    r"\cmidrule(lr){1-4}\cmidrule(lr){5-10}\cmidrule(lr){11-12}",
    r"Ep. & $\varepsilon$ & Semilla & Q ini. & Retraso & Espera & Cola & $r$/dec. & "
    r"Cambios & Paradas & Retraso & Espera \\",
    r" &  &  & (estados) & (s/veh) & (s/veh) & (veh) &  & de fase & (/veh) & (s/veh) & (s/veh) \\",
    r"\midrule",
]) + "\n"


def datos_entrenamiento(train):
    """Semilla base y paso de la evaluacion intermedia, leidos del propio CSV."""
    base = int(train[0]["semilla"]) - int(train[0]["episodio"]) if train else 42
    evals = [int(f["episodio"]) for f in train if f.get("eval_timeloss")]
    paso = evals[1] - evals[0] if len(evals) > 1 else (evals[0] if evals else 0)
    return base, paso


def tabla_episodios(esc, train, filas, escogidas=None, sufijo="", nota=""):
    if not train:
        return ""
    base_semilla, paso_eval = datos_entrenamiento(train)
    referencia = ""
    base = [f for f in filas if f["modo"] == "baseline"]
    if base:
        b = base[-1]
        referencia = (f"fijo & 0 & {b['semilla']} & -- & {num(b['timeloss_prom'])} & "
                      f"{num(b['espera_prom'])} & {num(b['cola_prom'])} & "
                      f"{num(b['recompensa_decision'])} & {b['cambios_fase']} & "
                      f"{num(b['paradas_prom'])} & -- & -- \\\\\n\\midrule\n")
    cuerpo = []
    estados_prev = 0
    for f in train:
        if escogidas is None or int(f["episodio"]) in escogidas or f.get("eval_timeloss"):
            cuerpo.append(fila_episodio(f, estados_prev))
        try:
            estados_prev = int(f["estados_q"])
        except (TypeError, ValueError):
            pass
    bloques = [cuerpo[i:i + FILAS_POR_BLOQUE] for i in range(0, len(cuerpo), FILAS_POR_BLOQUE)]
    n = len(train)
    texto = ""
    for k, bloque in enumerate(bloques, 1):
        parte = f" (parte {k} de {len(bloques)})" if len(bloques) > 1 else ""
        etiqueta = f"tab:{esc}-episodios{sufijo}" + (f"-{k}" if k > 1 else "")
        corto = f"Escenario {esc}: episodios de entrenamiento{parte}"
        largo = (f"Escenario {esc}: parámetros de entrada y métricas de salida por episodio{parte}. "
                 f"{n} episodios de entrenamiento con semilla base {base_semilla}"
                 + ("; la fila fijo es el tiempo fijo con la misma semilla base" if referencia else "")
                 + (f". La política congelada se evalúa cada {paso_eval} episodios con una semilla "
                    f"fija ajena al entrenamiento y a la evaluación final" if paso_eval else "")
                 + f".{nota}")
        texto += (abrir_tabla() + ENCABEZADO_EPISODIOS + (referencia if k == 1 else "")
                  + "\n".join(bloque) + "\n" r"\bottomrule" "\n" r"\end{tabular}" "\n"
                  + f"\\caption[{corto}]{{{largo}}}\n"
                  + f"\\label{{{etiqueta}}}\n" r"\end{table}" "\n\n")
    return texto


METRICAS_EVAL = [("timeloss_prom", "Retraso (s/veh)"), ("espera_prom", "Espera detenida (s/veh)"),
                 ("cola_prom", "Cola promedio (veh)"), ("cola_max", "Cola máxima (veh)"),
                 ("paradas_prom", "Paradas por vehículo"), ("throughput", "Throughput (veh)"),
                 ("co2_prom", "CO$_2$ (g/veh)"), ("nox_prom", "NO$_x$ (mg/veh)"),
                 ("recompensa_decision", "Recompensa por decisión"),
                 ("cambios_fase", "Cambios de fase")]


def rango_semillas(esc):
    filas = leer(f"evaluacion_{esc}.csv")
    semillas = sorted({int(f["semilla"]) for f in filas}) if filas else []
    return (semillas[0], semillas[-1], len(semillas)) if semillas else (0, 0, 0)


def tabla_evaluacion(esc):
    resumen = leer(f"evaluacion_{esc}_resumen.csv")
    if not resumen:
        return ""
    s0, s1, n = rango_semillas(esc)

    def fila(b, m):
        return next((x for x in resumen if x["brazo"] == b and x["metrica"] == m), None)

    lineas = []
    for m, nombre in METRICAS_EVAL:
        celdas = [nombre]
        for b in ("fijo", "actuado", "rl"):
            r = fila(b, m)
            celdas.append(f"{num(r['media'])} $\\pm$ {num(r['ic95'])}" if r else "--")
        rl, act = fila("rl", m), fila("actuado", m)
        if rl and rl.get("delta_pct"):
            celdas.append(f"{con_signo(rl['delta_pct'])}\\,\\% {intervalo(rl['delta_ic95'])}")
            celdas.append(rl["p_wilcoxon"])
        else:
            celdas += ["--", "--"]
        celdas.append(f"{con_signo(act['delta_pct'])}\\,\\%" if act and act.get("delta_pct") else "--")
        lineas.append(" & ".join(celdas) + r" \\")
    cabecera = "\n".join([
        r"\begin{tabular}{lrrrrrr}",
        r"\toprule",
        r"Métrica & Tiempo fijo & Actuado & Q-learning & "
        r"\makecell{$\Delta$ RL vs fijo\\{}[IC95\,\%]} & $p$ & "
        r"\makecell{$\Delta$ actuado\\vs fijo} \\",
        r"\midrule",
    ]) + "\n"
    corto = f"Escenario {esc}: evaluación con política congelada"
    largo = (f"Escenario {esc}: evaluación con política congelada sobre {n} semillas ({s0} a {s1}), "
             "las mismas para los tres controles. Media $\\pm$ IC95\\,\\%; el cambio porcentual lleva "
             "su intervalo bootstrap pareado y $p$ es el de la prueba de Wilcoxon pareada frente al fijo.")
    return (abrir_tabla() + cabecera + "\n".join(lineas) + "\n" r"\bottomrule" "\n"
            r"\end{tabular}" "\n" + f"\\caption[{corto}]{{{largo}}}\n"
            + f"\\label{{tab:{esc}-evaluacion}}\n" r"\end{table}" "\n")


def tabla_resumen(escenarios):
    lineas = []
    n_sem = 0
    for esc in escenarios:
        resumen = leer(f"evaluacion_{esc}_resumen.csv")
        if not resumen:
            continue
        n_sem = rango_semillas(esc)[2]

        def r(b, m):
            return next((x for x in resumen if x["brazo"] == b and x["metrica"] == m), None)

        tl = {b: r(b, "timeloss_prom") for b in ("fijo", "actuado", "rl")}
        lineas.append(" & ".join([
            esc, num(tl["fijo"]["media"]), num(tl["actuado"]["media"]), num(tl["rl"]["media"]),
            f"{con_signo(tl['rl']['delta_pct'])}\\,\\% {intervalo(tl['rl']['delta_ic95'])}",
            tl["rl"]["p_wilcoxon"],
            f"{con_signo(tl['actuado']['delta_pct'])}\\,\\%",
            f"{con_signo(r('rl', 'espera_prom')['delta_pct'])}\\,\\%",
            f"{con_signo(r('rl', 'paradas_prom')['delta_pct'])}\\,\\%",
            f"{con_signo(r('rl', 'co2_prom')['delta_pct'])}\\,\\%",
        ]) + r" \\")
    if not lineas:
        return ""
    cabecera = "\n".join([
        r"\begin{tabular}{lrrrrrrrrr}",
        r"\toprule",
        r" & \multicolumn{3}{c}{Retraso (s/veh)} & \multicolumn{2}{c}{RL vs fijo} & Actuado & "
        r"\multicolumn{3}{c}{RL vs fijo, secundarias} \\",
        r"\cmidrule(lr){2-4}\cmidrule(lr){5-6}\cmidrule(lr){7-7}\cmidrule(lr){8-10}",
        r"Escenario & Fijo & Actuado & RL & $\Delta$ [IC95\,\%] & $p$ & $\Delta$ vs fijo & "
        r"Espera & Paradas & CO$_2$ \\",
        r"\midrule",
    ]) + "\n"
    largo = (f"Resumen por escenario: retraso promedio por vehículo con política congelada, {n_sem} "
             "semillas de evaluación comunes a los tres controles. La meta de la tesis es $-25\\,\\%$ "
             "de retraso frente al fijo.")
    return (abrir_tabla() + cabecera + "\n".join(lineas) + "\n" r"\bottomrule" "\n"
            r"\end{tabular}" "\n" + f"\\caption[Resumen por escenario]{{{largo}}}\n"
            r"\label{tab:resumen-escenarios}" "\n" r"\end{table}" "\n")


def main():
    todos = ["cruce", "cruce2", "corredor", "red"]
    escenarios = sys.argv[1:] or [e for e in todos if os.path.exists(f"evaluacion_{e}_resumen.csv")]
    for esc in escenarios:
        train, filas = bloque_train(esc)
        n = len(train)
        escogidas = {1, 2, 3, 5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 80, 90, 100, 120, n}
        escribir(f"{esc}_episodios.tex", tabla_episodios(esc, train, filas))
        escribir(f"{esc}_episodios_resumen.tex",
                 tabla_episodios(esc, train, filas, escogidas=escogidas, sufijo="-resumen",
                                 nota=" Se muestran episodios escogidos; la tabla completa está en el Anexo~A."))
        escribir(f"{esc}_evaluacion.tex", tabla_evaluacion(esc))
    escribir("resumen_escenarios.tex", tabla_resumen(escenarios))


if __name__ == "__main__":
    main()
