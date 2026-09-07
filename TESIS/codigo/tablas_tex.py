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

import comun

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


def nom(esc):
    """Nombre del escenario tal como se escribe en el texto del documento.

    El guion bajo de corredor_alta es caracter de subindice en LaTeX: sin escapar
    mete el resto del caption en modo matematico y la compilacion falla, primero al
    releer la lista de tablas (.lot) y luego en cada tabla. Solo para texto que se
    tipografia; los nombres de archivo y los \\label van con el nombre crudo.
    """
    return esc.replace("_", r"\_")


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


def desde_ultimo_reinicio(filas):
    """Solo las filas de la ultima corrida del CSV.

    Los CSV se abren en modo anadir, asi que un entrenamiento abortado y relanzado deja
    los episodios repetidos al principio (corredor tiene cinco CSV de IPPO con 204 filas
    por una corrida cortada en el episodio 4). El corte esta donde el numero de episodio
    deja de crecer.
    """
    inicio = 0
    for i in range(1, len(filas)):
        if int(filas[i]["episodio"]) <= int(filas[i - 1]["episodio"]):
            inicio = i
    return filas[inicio:]


def bloque_train(esc):
    filas = leer(f"resultados_{esc}.csv")
    train = [f for f in filas if f["modo"] == "train"]
    return desde_ultimo_reinicio(train), filas


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
        corto = f"Escenario {nom(esc)}: episodios de entrenamiento{parte}"
        largo = (f"Escenario {nom(esc)}: parámetros de entrada y métricas de salida por episodio{parte}. "
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
                 ("cambios_fase", "Cambios de fase"),
                 # solo en corredor y red
                 ("viaje_corredor_prom", "Viaje extremo a extremo (s)"),
                 ("retraso_corredor_prom", "Retraso extremo a extremo (s)"),
                 ("spillback_tasa", "Tasa de \\textit{spillback}"),
                 ("cola_max_enlace", "Cola máxima en un enlace (veh)")]


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
        if all(fila(b, m) is None for b in ("fijo", "actuado", "rl")):
            continue                     # metrica que este escenario no mide (p. ej. corredor en cruce)
        celdas = [nombre]
        for b in ("fijo", "actuado", "rl"):
            r = fila(b, m)
            celdas.append(f"{num(r['media'])} $\\pm$ {num(r['ic95'])}" if r else "--")
        rl, act = fila("rl", m), fila("actuado", m)
        if rl and rl.get("delta_pct"):
            # delta e intervalo en dos lineas para que la tabla quepa en el ancho de texto
            celdas.append("\\makecell{" + con_signo(rl["delta_pct"]) + "\\,\\%\\\\{}"
                          + intervalo(rl["delta_ic95"]) + "}")
            celdas.append(rl["p_wilcoxon"])
        else:
            celdas += ["--", "--"]
        celdas.append(f"{con_signo(act['delta_pct'])}\\,\\%" if act and act.get("delta_pct") else "--")
        lineas.append(" & ".join(celdas) + r" \\")
    cabecera = "\n".join([
        r"\setlength{\tabcolsep}{2pt}",
        r"\begin{tabular}{lrrrrrr}",
        r"\toprule",
        r"Métrica & Tiempo fijo & Actuado & Q-learning & "
        r"\makecell{$\Delta$ RL vs fijo\\{}[IC95\,\%]} & $p$ & "
        r"\makecell{$\Delta$ actuado\\vs fijo} \\",
        r"\midrule",
    ]) + "\n"
    corto = f"Escenario {nom(esc)}: evaluación con política congelada"
    largo = (f"Escenario {nom(esc)}: evaluación con política congelada sobre {n} semillas ({s0} a {s1}), "
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
            nom(esc), num(tl["fijo"]["media"]), num(tl["actuado"]["media"]), num(tl["rl"]["media"]),
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
             # el % va fuera del math: babel-spanish le antepone el espacio fino mirando
             # \lastskip, y dentro de $...$ el \, esta en mu -> "Incompatible glue units"
             "semillas de evaluación comunes a los tres controles. La meta de la tesis es $-25$\\,\\% "
             "de retraso frente al fijo.")
    return (abrir_tabla() + cabecera + "\n".join(lineas) + "\n" r"\bottomrule" "\n"
            r"\end{tabular}" "\n" + f"\\caption[Resumen por escenario]{{{largo}}}\n"
            r"\label{tab:resumen-escenarios}" "\n" r"\end{table}" "\n")


# ---------------- Modulo U4 (IPPO) ----------------
VARIANTES = ["local", "vecinos", "spill", "cambio"]
NOMBRE_VARIANTE = {"local": "IPPO local", "vecinos": "IPPO vecinos", "spill": "IPPO spill",
                   "cambio": "IPPO cambio"}
METRICAS_U4 = METRICAS_EVAL + [
    ("retraso_corredor_punta", "Retraso de paso, sentido punta (s)"),
    ("paradas_corredor", "Paradas de paso (/veh)"),
    ("paradas_corredor_le1", "Fracción de paso con $\\le 1$ parada"),
    ("spillback_seg", "Segundos con \\textit{spillback}"),
    ("veh_max_enlace", "Vehículos máximos en un enlace"),
    ("no_terminados", "Vehículos no terminados")]


def brazos_u4(esc):
    """Brazos principales del escenario: fijo, actuado, rl y la politica mediana de cada variante."""
    resumen = leer(f"evaluacion_{esc}_resumen.csv")
    en_csv = {x["brazo"] for x in resumen}
    politicas = comun.politicas_ippo(esc)
    ippo = [(v, comun.brazo_ippo(v, politicas, en_csv)) for v in VARIANTES]
    ippo = [(v, b) for v, b in ippo if b]
    return resumen, politicas, [b for b in ("fijo", "actuado", "rl") if b in en_csv], ippo


def celda_delta(r, sufijo=""):
    if not r or not r.get("delta_pct" + sufijo):
        return "--", "--"
    return (f"{con_signo(r['delta_pct' + sufijo])}\\,\\% {intervalo(r['delta_ic95' + sufijo])}",
            r["p_wilcoxon" + sufijo])


def dos_lineas(celda):
    """Pone el intervalo debajo del porcentaje (makecell) para que las tablas anchas quepan."""
    if "[" not in celda:
        return celda
    return "\\makecell{" + celda.replace("\\% [", "\\%\\\\{}[") + "}"


def celda_delta_apilada(r, sufijo=""):
    """El cambio, su intervalo y el p en una sola celda, en tres lineas.

    En columnas separadas la tabla de deltas mide unos 21 cm y el bloque de texto 15:
    la ultima columna se salia del papel. El {} tras \\\\ evita que el corchete de
    apertura del intervalo se lea como argumento opcional del salto de linea.
    """
    if not r or not r.get("delta_pct" + sufijo):
        return "--"
    return (r"\makecell[r]{" + f"{con_signo(r['delta_pct' + sufijo])}\\,\\%"
            + r"\\{}" + intervalo(r["delta_ic95" + sufijo])
            + r"\\$p$ = " + r["p_wilcoxon" + sufijo] + "}")


def tabla_u4(esc):
    """Medias con IC95 por brazo, con las variantes IPPO junto a los tres controles de referencia."""
    resumen, _, ref, ippo = brazos_u4(esc)
    if not ippo:
        return ""
    s0, s1, n = rango_semillas(esc)
    columnas = ref + [b for _, b in ippo]

    def fila(b, m):
        return next((x for x in resumen if x["brazo"] == b and x["metrica"] == m), None)

    lineas = []
    de_corredor = [m for m, _ in METRICAS_U4[len(METRICAS_EVAL) - 4:]]   # solo con enlaces entre cruces
    for m, nombre in METRICAS_U4:
        if all(fila(b, m) is None for b in columnas):
            continue
        if m in de_corredor and esc in ("cruce", "cruce2"):
            continue
        celdas = [nombre]
        for b in columnas:
            r = fila(b, m)
            dec = 0 if m in ("throughput", "no_terminados", "spillback_seg") else 2
            celdas.append(f"{num(r['media'], dec)} $\\pm$ {num(r['ic95'], dec)}" if r else "--")
        lineas.append(" & ".join(celdas) + r" \\")
    nombres = {"fijo": "Fijo", "actuado": "Actuado", "rl": "Q-learning"}
    nombres.update({b: NOMBRE_VARIANTE[v] for v, b in ippo})
    ancha = len(columnas) >= 6                      # con 6 brazos hay que apretar para que quepa
    cabecera = "\n".join([
        (r"\setlength{\tabcolsep}{2pt}" if ancha else "")
        + r"\begin{tabular}{" + ("p{2.8cm}" if ancha else "p{3.3cm}") + "r" * len(columnas) + "}",
        r"\toprule",
        "Métrica & " + " & ".join(r"\makecell{" + nombres[b].replace(" ", r"\\") + "}" for b in columnas)
        + r" \\",
        r"\midrule"]) + "\n"
    corto = f"Escenario {nom(esc)}: evaluación de las variantes IPPO"
    largo = (f"Escenario {nom(esc)}: evaluación con política congelada sobre {n} semillas ({s0} a {s1}), "
             "las mismas para todos los brazos; media $\\pm$ IC95\\,\\%. Cada variante IPPO es la "
             "política mediana de sus semillas base por la evaluación intermedia final; los cambios "
             f"porcentuales están en la Tabla~\\ref{{tab:{esc}-u4-deltas}}.")
    return (abrir_tabla() + cabecera + "\n".join(lineas) + "\n" r"\bottomrule" "\n"
            r"\end{tabular}" "\n" + f"\\caption[{corto}]{{{largo}}}\n"
            + f"\\label{{tab:{esc}-u4}}\n" r"\end{table}" "\n")


def tabla_u4_deltas(esc):
    """Cambio del retraso de cada variante IPPO frente al fijo, al actuado y a Q-learning."""
    resumen, _, _, ippo = brazos_u4(esc)
    if not ippo:
        return ""
    lineas = []
    for v, b in ippo:
        r = next((x for x in resumen if x["brazo"] == b and x["metrica"] == "timeloss_prom"), None)
        celdas = [NOMBRE_VARIANTE[v], num(r["media"]) if r else "--"]
        for suf in ("", "_act", "_rl"):
            celdas.append(celda_delta_apilada(r, suf))
        for m in ("espera_prom", "paradas_prom", "cambios_fase"):
            rm = next((x for x in resumen if x["brazo"] == b and x["metrica"] == m), None)
            celdas.append(f"{con_signo(rm['delta_pct'])}\\,\\%" if rm and rm.get("delta_pct") else "--")
        lineas.append(" & ".join(celdas) + r" \\")
    # cada comparacion ocupa una sola columna (cambio, intervalo y p apilados): con las
    # tres en columnas separadas la tabla se salia del bloque de texto por unos 6 cm
    cabecera = "\n".join([
        r"\begin{tabular}{lrrrrrrr}",
        r"\toprule",
        r" & Retraso & \multicolumn{3}{c}{Cambio del retraso [IC95\,\%]} & "
        r"\multicolumn{3}{c}{vs fijo, secundarias} \\",
        r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}",
        r"Variante & (s/veh) & vs fijo & vs actuado & vs Q-learning & "
        r"Espera & Paradas & Cambios \\",
        r"\midrule"]) + "\n"
    corto = f"Escenario {nom(esc)}: cambio del retraso de las variantes IPPO"
    largo = (f"Escenario {nom(esc)}: cambio porcentual del retraso de cada variante IPPO (política mediana) "
             "frente al fijo, al actuado y a Q-learning, con intervalo bootstrap pareado por semilla y "
             "$p$ de Wilcoxon pareado; a la derecha, cambio frente al fijo de tres secundarias.")
    return (abrir_tabla() + cabecera + "\n".join(lineas) + "\n" r"\bottomrule" "\n"
            r"\end{tabular}" "\n" + f"\\caption[{corto}]{{{largo}}}\n"
            + f"\\label{{tab:{esc}-u4-deltas}}\n" r"\end{table}" "\n")


def tabla_fragilidad(esc):
    """Por variante y semilla base: evaluacion intermedia final, media de las semillas de
    evaluacion y cambio frente al fijo; la fila de rango mide la fragilidad del entrenamiento."""
    resumen, politicas, _, ippo = brazos_u4(esc)
    if not politicas:
        return ""

    def fila_res(b):
        return next((x for x in resumen if x["brazo"] == b and x["metrica"] == "timeloss_prom"), None)

    lineas = []
    for v in VARIANTES:
        if v not in politicas:
            continue
        medias = []
        for base, ev in sorted(politicas[v]["bases"].items()):
            r = fila_res(f"ippo_{v}_s{base}")
            if r is None and len(politicas[v]["bases"]) == 1:
                r = fila_res(f"ippo_{v}")
            mediana = " (mediana)" if base == politicas[v]["mediana"] else ""
            celdas = [NOMBRE_VARIANTE[v], f"{base}{mediana}", num(ev)]
            if r:
                medias.append(float(r["media"]))
                celdas += [f"{num(r['media'])} $\\pm$ {num(r['ic95'])}", *celda_delta(r)]
            else:
                celdas += ["--", "--", "--"]
            lineas.append(" & ".join(celdas) + r" \\")
        if len(medias) > 1:
            lineas.append(f" & rango entre bases & & {num(max(medias) - min(medias))} & & \\\\")
    cabecera = "\n".join([
        r"\begin{tabular}{llrrrr}",
        r"\toprule",
        r"Variante & Semilla base & \makecell{Eval. intermedia\\final (s/veh)} & "
        r"\makecell{Retraso, semillas\\de evaluación (s/veh)} & $\Delta$ vs fijo [IC95\,\%] & $p$ \\",
        r"\midrule"]) + "\n"
    corto = f"Escenario {nom(esc)}: fragilidad del entrenamiento IPPO"
    largo = (f"Escenario {nom(esc)}: las tres políticas de cada variante IPPO. La evaluación intermedia "
             "final usa la semilla 999; la media, las semillas de evaluación. El rango entre bases se "
             "compara con el IC95\\,\\% de una sola política.")
    return (abrir_tabla() + cabecera + "\n".join(lineas) + "\n" r"\bottomrule" "\n"
            r"\end{tabular}" "\n" + f"\\caption[{corto}]{{{largo}}}\n"
            + f"\\label{{tab:{esc}-fragilidad}}\n" r"\end{table}" "\n")


def tabla_s1(esc):
    """Canal imperfecto: la politica mediana de vecinos con latencia y perdida, sin reentrenar."""
    resumen, _, _, ippo = brazos_u4(esc)
    perfecto = next((b for v, b in ippo if v == "vecinos"), None)
    evaluacion = leer(f"evaluacion_{esc}.csv")
    def canal(b):                       # 'ippo_vecinos_L5p30' -> (5, 30): orden por latencia y perdida
        lat, perd = b.split("_L")[1].split("p")
        return int(lat), int(perd)

    brazos_s1 = sorted({x["brazo"] for x in evaluacion
                        if x["brazo"].startswith("ippo_vecinos") and "_L" in x["brazo"]}, key=canal)
    if not perfecto or not brazos_s1:
        return ""

    def valores(b, m):
        return {x["semilla"]: float(x[m]) for x in evaluacion if x["brazo"] == b and x.get(m)}

    def r(b, m):
        return next((x for x in resumen if x["brazo"] == b and x["metrica"] == m), None)

    lineas = []
    for b in [perfecto] + brazos_s1:
        etiqueta = "canal perfecto"
        if "_L" in b:
            lat, perd = b.split("_L")[1].split("p")
            etiqueta = f"latencia {lat}~s" + (f", pérdida {perd}\\,\\%" if int(perd) else "")
        celdas = [etiqueta]
        rt = r(b, "timeloss_prom")
        celdas.append(f"{num(rt['media'])} $\\pm$ {num(rt['ic95'])}" if rt else "--")
        base, otro = valores(perfecto, "timeloss_prom"), valores(b, "timeloss_prom")
        difs = [otro[s] - base[s] for s in base if s in otro]
        if b != perfecto and len(difs) > 1:
            import statistics
            from scipy import stats
            h = stats.t.ppf(0.975, len(difs) - 1) * statistics.stdev(difs) / len(difs) ** 0.5
            celdas.append(f"{con_signo(statistics.mean(difs), 2)} $\\pm$ {num(h)}")
        else:
            celdas.append("--")
        for m in ("paradas_corredor_le1", "retraso_corredor_punta", "cambios_fase"):
            rm = r(b, m)
            celdas.append(num(rm["media"], 3 if m == "paradas_corredor_le1" else 1) if rm else "--")
        lineas.append(" & ".join(celdas) + r" \\")
    cabecera = "\n".join([
        r"\begin{tabular}{lrrrrr}",
        r"\toprule",
        r"Canal & Retraso (s/veh) & \makecell{Diferencia vs\\perfecto (s)} & "
        r"\makecell{Paso con\\$\le 1$ parada} & \makecell{Retraso de paso\\punta (s)} & Cambios \\",
        r"\midrule"]) + "\n"
    corto = f"Escenario {nom(esc)}: IPPO vecinos con canal imperfecto"
    largo = (f"Escenario {nom(esc)}: la política mediana de IPPO vecinos evaluada con latencia y pérdida de "
             "mensajes, sin reentrenar, sobre las mismas semillas. La diferencia frente al canal "
             "perfecto es la media pareada por semilla $\\pm$ IC95\\,\\%.")
    return (abrir_tabla() + cabecera + "\n".join(lineas) + "\n" r"\bottomrule" "\n"
            r"\end{tabular}" "\n" + f"\\caption[{corto}]{{{largo}}}\n"
            + f"\\label{{tab:{esc}-s1}}\n" r"\end{table}" "\n")


ENCABEZADO_IPPO = "\n".join([
    r"\setlength{\tabcolsep}{2pt}",
    r"\begin{tabular}{rrrrrrrrrr}",
    r"\toprule",
    r"Ep. & lr & Retraso & Espera & $r$/dec. & $r$ agente & Cambios & "
    r"Entropía & KL & \makecell{Eval.\\retraso} \\",
    r" & ($\times 10^{-4}$) & (s/veh) & (s/veh) & (U2) & (U4) & de fase &  &  & (s/veh) \\",
    r"\midrule"]) + "\n"


def tabla_ippo_episodios(esc):
    """Registro condensado por episodio de cada entrenamiento IPPO (episodios 1-5 y cada 10)."""
    politicas = comun.politicas_ippo(esc)
    texto = ""
    for v in VARIANTES:
        for base in sorted(politicas.get(v, {"bases": {}})["bases"]):
            filas = desde_ultimo_reinicio(leer(f"resultados_{esc}_ippo_{v}_s{base}.csv"))
            n = len(filas)
            cuerpo = []
            for f in filas:
                ep = int(f["episodio"])
                if ep <= 5 or ep % 10 == 0 or ep == n:
                    cuerpo.append(" & ".join([
                        str(ep), num(float(f["lr"]) * 1e4, 1), num(f["timeloss_prom"]),
                        num(f["espera_prom"]), num(f["recompensa_decision"]),
                        num(f["recompensa_total_decision"]), f["cambios_fase"],
                        num(f["entropia_libre"], 3), num(f["kl_aprox"], 4),
                        num(f.get("eval_timeloss"))]) + r" \\")
            corto = f"Escenario {nom(esc)}: entrenamiento IPPO {v}, semilla base {base}"
            largo = (f"Escenario {nom(esc)}: entrenamiento de IPPO {v} con semilla base {base}, {n} episodios "
                     "(se muestran los cinco primeros y uno de cada diez; la semilla de SUMO de cada "
                     "episodio es la base más su número). $r$/dec.\\ es la recompensa de U2 a reloj "
                     "fijo; $r$ agente, la que vio el agente por decisión; la entropía se promedia "
                     "sobre las decisiones libres.")
            texto += (abrir_tabla() + ENCABEZADO_IPPO + "\n".join(cuerpo) + "\n" r"\bottomrule" "\n"
                      r"\end{tabular}" "\n" + f"\\caption[{corto}]{{{largo}}}\n"
                      + f"\\label{{tab:{esc}-ippo-{v}-{base}}}\n" r"\end{table}" "\n\n")
    return texto


def tabla_resumen_u4(escenarios):
    lineas = []
    for esc in escenarios:
        resumen, _, ref, ippo = brazos_u4(esc)
        if not ippo:
            continue

        def r(b, m="timeloss_prom"):
            return next((x for x in resumen if x["brazo"] == b and x["metrica"] == m), None)

        por_v = dict(ippo)
        celdas = [nom(esc)]
        for b in ("fijo", "actuado", "rl"):
            celdas.append(num(r(b)["media"]) if r(b) else "--")
        for v in ("local", "vecinos", "spill"):
            celdas.append(num(r(por_v[v])["media"]) if v in por_v and r(por_v[v]) else "--")
        mejor = por_v.get("vecinos") or por_v.get("local")
        delta, p = celda_delta(r(mejor))
        celdas += [dos_lineas(delta), p, dos_lineas(celda_delta(r(mejor), "_act")[0])]
        lineas.append(" & ".join(celdas) + r" \\")
    if not lineas:
        return ""
    cabecera = "\n".join([
        r"\begin{tabular}{lrrrrrrrrr}",
        r"\toprule",
        r" & \multicolumn{6}{c}{Retraso (s/veh)} & \multicolumn{2}{c}{IPPO vecinos vs fijo} & "
        r"\makecell{IPPO vecinos\\vs actuado} \\",
        r"\cmidrule(lr){2-7}\cmidrule(lr){8-9}",
        r"Escenario & Fijo & Actuado & Q-learning & \makecell{IPPO\\local} & \makecell{IPPO\\vecinos} & "
        r"\makecell{IPPO\\spill} & $\Delta$ [IC95\,\%] & $p$ & $\Delta$ [IC95\,\%] \\",
        r"\midrule"]) + "\n"
    largo = ("Resumen del módulo U4: retraso promedio por vehículo con política congelada sobre las "
             "semillas de evaluación, comunes a todos los brazos. Cada variante IPPO es su política "
             "mediana.")
    return (abrir_tabla() + cabecera + "\n".join(lineas) + "\n" r"\bottomrule" "\n"
            r"\end{tabular}" "\n" + f"\\caption[Resumen del módulo U4]{{{largo}}}\n"
            r"\label{tab:resumen-u4}" "\n" r"\end{table}" "\n")


def main():
    todos = ["cruce", "cruce2", "corredor", "red", "corredor_alta"]
    escenarios = sys.argv[1:] or [e for e in todos if os.path.exists(f"evaluacion_{e}_resumen.csv")]
    for esc in escenarios:
        train, filas = bloque_train(esc)
        n = len(train)
        escogidas = {1, 2, 3, 5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 80, 90, 100, 120, n}
        escribir(f"{esc}_episodios.tex", tabla_episodios(esc, train, filas))
        nota = " Se muestran episodios escogidos; la tabla completa está en el Anexo~A."
        escribir(f"{esc}_episodios_resumen.tex",
                 tabla_episodios(esc, train, filas, escogidas=escogidas, sufijo="-resumen", nota=nota))
        escribir(f"{esc}_evaluacion.tex", tabla_evaluacion(esc))
        if comun.politicas_ippo(esc):
            escribir(f"{esc}_u4.tex", tabla_u4(esc) + tabla_u4_deltas(esc))
            escribir(f"{esc}_fragilidad.tex", tabla_fragilidad(esc))
            escribir(f"{esc}_s1.tex", tabla_s1(esc))
            escribir(f"{esc}_ippo_episodios.tex", tabla_ippo_episodios(esc))
    escribir("resumen_escenarios.tex", tabla_resumen([e for e in escenarios if e != "corredor_alta"]))
    escribir("resumen_u4.tex", tabla_resumen_u4([e for e in escenarios if e not in ("cruce", "cruce2")]))


if __name__ == "__main__":
    main()
