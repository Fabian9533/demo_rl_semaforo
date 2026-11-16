"""
tablas_plan3.py - Tablas y figura del segundo estudio (plan 3) para la tesis.

Uso (desde demo_rl/):  python tablas_plan3.py

Lee solo las salidas del veredicto del plan 3, que ya estan cerradas y en git:
  plan3/salidas/veredicto3_celdas.csv         etiqueta y cambio por caso y tipo de llegadas
  plan3/salidas/veredicto3_comparaciones.csv  cada control frente a cada referencia, por tanda
  plan3/salidas/veredicto3.md                 tablas de hipotesis y de referencias al lado
  plan3/promocion/<escenario>.json            validacion de la regla de promocion
Escribe:
  TESIS/secciones/tablas/plan3_*.tex   solo el entorno tabular; el table, el caption y la etiqueta los pone el anexo
  TESIS/images/fig_plan3_cambio.pdf y .png   cambio frente al fijo ajustado al segundo, con las bandas de veredicto
No corre ninguna simulacion y no escribe en plan2/ ni en plan3/.
"""
import os
import re
import csv
import json

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDAS = os.path.join(AQUI, "plan3", "salidas")
PROMOCION = os.path.join(AQUI, "plan3", "promocion")
TABLAS = os.path.join(AQUI, "TESIS", "secciones", "tablas")
IMAGENES = os.path.join(AQUI, "TESIS", "images")

# Casos del plan (Tabla tab:plan-resultados): red, demanda y veh/h
CASOS = {"P1": ("corredor", "nominal", 1810), "P2": ("corredor", "alta", 3620),
         "P3": ("red con rotonda", "nominal", 2150), "P4": ("red con rotonda", "alta", 2580),
         "P5": ("malla", "nominal", 4350), "P6": ("malla", "alta", 8700)}
SENSIBILIDAD = {"mix1": "Corredor nominal, mezcla de vehículos de Lima",
                "mixa1": "Corredor nominal, mezcla de Lima y arranque lento",
                "per1": "Corredor nominal, demanda con perfil de 10~min",
                "mix3": "Red nominal, mezcla de vehículos de Lima",
                "mixa3": "Red nominal, mezcla de Lima y arranque lento",
                "per3": "Red nominal, demanda con perfil de 10~min"}
# nombres del veredicto -> nombres de la tesis
MODELO = {"modelo completo": "Modelo completo", "IPPO con mensajes corregido": "IPPO con mensajes corregido"}
REFERENCIAS = ["actuado ajustado", "actuado por defecto", "fijo entregado", "fijo de verdes de 5 en 5",
               "fijo por franja", "regla simple", "regla reactiva", "Max-Pressure", "ciclo mínimo"]
NOMBRE_REF = {"actuado ajustado": "Actuado ajustado", "actuado por defecto": "Actuado por defecto",
              "fijo entregado": "Fijo ajustado desde 10~s", "fijo de verdes de 5 en 5": "Fijo de verdes de 5 en 5",
              "fijo por franja": "Fijo por franja", "regla simple": "Regla simple",
              "regla reactiva": "Regla reactiva", "Max-Pressure": "Max-Pressure", "ciclo mínimo": "Ciclo mínimo"}
CANDIDATOS = [("p3completopoimed", "Modelo completo"), ("p3obspoimed", "Observación nueva"),
              ("p3e400poimed", "400 episodios"), ("p3reloj2poimed", "Decisión cada 2~s")]
ESCENARIO = {"P1": "poi_corredor", "P2": "poi_corredor_alta", "P3": "poi_red", "P4": "poi_red_alta",
             "P5": "poi_malla3", "P6": "poi_malla3_alta"}


# ---------------- Lectura ----------------
def leer_csv(nombre):
    with open(os.path.join(SALIDAS, nombre), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def tabla_md(titulo):
    """Filas (dict) de la tabla que sigue al titulo '## <titulo>' de veredicto3.md."""
    with open(os.path.join(SALIDAS, "veredicto3.md"), encoding="utf-8") as f:
        lineas = f.read().split("\n")
    i = next(k for k, linea in enumerate(lineas) if linea.startswith("## " + titulo))
    filas = [linea for linea in lineas[i + 1:] if linea.startswith("|")]
    fin = next((k for k, linea in enumerate(lineas[i + 1:]) if linea.startswith("## ")), len(lineas))
    filas = [linea for linea in lineas[i + 1:i + 1 + fin] if linea.startswith("|")]
    celdas = [[c.strip() for c in linea.strip("|").split("|")] for linea in filas]
    cab = celdas[0]
    return [dict(zip(cab, c)) for c in celdas[2:]]


# ---------------- Formato LaTeX ----------------
def num(x, dec=1):
    """Numero con signo en modo matematico: -16.28 -> $-16.3$; lo que redondea a cero va sin signo."""
    texto = f"{float(x):+.{dec}f}"
    return f"${texto.lstrip('+-') if float(texto) == 0 else texto}$"


def intervalo(texto, dec=1):
    """'[-17.74, -15.00]' -> [$-17.7$, $-15.0$]."""
    a, b = (float(v) for v in texto.strip("[]").split(","))
    return f"[{num(a, dec)}, {num(b, dec)}]"


def etiqueta(texto):
    """Etiqueta del veredicto con la marca sin estabilizar: X (sin estabilizar)."""
    m = re.match(r"PENDIENTE \(no convergió; provisional: (\w+)\)", texto)
    return f"{m.group(1)} (sin estabilizar)" if m else texto


def repite(fila):
    return f"{fila['repite_T1']} y {fila['repite_T2']}"


def nombre_caso(c):
    red, demanda, veh = CASOS[c]
    return f"{c}, {red}, demanda {demanda} ({veh}~veh/h)"


def escribir(nombre, cabecera, cuerpo):
    ruta = os.path.join(TABLAS, nombre)
    texto = ("% Generado por tablas_plan3.py a partir de plan3/salidas/. No editar a mano.\n"
             + "".join(f"% {linea}\n" for linea in cabecera) + cuerpo + "\n")
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    print("Escrito", os.path.relpath(ruta, AQUI))


def tabular(columnas, cabecera, filas):
    lineas = [f"\\begin{{tabular}}{{{columnas}}}", "\\toprule", " & ".join(cabecera) + " \\\\", "\\midrule"]
    lineas += [" & ".join(f) + " \\\\" if f != "\\midrule" else f for f in filas]
    return "\n".join(lineas + ["\\bottomrule", "\\end{tabular}"])


IZQ = ">{\\raggedright\\arraybackslash}p"


# ---------------- Tablas de etiquetas por caso ----------------
def tabla_aleatorias(celdas):
    filas = []
    for c in CASOS:
        r = celdas[(c, "aleatorias")]
        modelo = "Modelo completo" if r["modelo_citado"] == "modelo completo" else "IPPO con mensajes corregido"
        filas.append([nombre_caso(c), modelo, etiqueta(r["etiqueta_citable"]),
                      f"{num(r['cambio_T1'])} {intervalo(r['ic_T1'])}", f"{num(r['cambio_T2'])} {intervalo(r['ic_T2'])}",
                      repite(r)])
    escribir("plan3_aleatorias.tex",
             ["Segundo estudio, llegadas aleatorias: etiqueta citable del modelo citado frente al fijo ajustado al",
              "segundo, con el cambio del retraso total y su IC95 en cada tanda (100 semillas por tanda).",
              "fuente: plan3/salidas/veredicto3_celdas.csv (filas P1-P6 con llegadas aleatorias: modelo_citado,",
              "etiqueta_citable, cambio_T1, ic_T1, cambio_T2, ic_T2, repite_T1 y repite_T2).",
              "Entorno: \\setstretch{1}, \\footnotesize y \\setlength{\\tabcolsep}{3pt}."],
             tabular(f"{IZQ}{{2.9cm}}{IZQ}{{2.2cm}}{IZQ}{{2.2cm}}{IZQ}{{2.4cm}}{IZQ}{{2.4cm}}{IZQ}{{1.3cm}}",
                     ["Caso", "Modelo citado", "Veredicto", "Cambio, tanda 1 (\\%)", "Cambio, tanda 2 (\\%)",
                      "Se repite"], filas))


def tabla_regulares(celdas):
    filas = []
    for c in list(CASOS) + ["P6e"]:
        r = celdas[(c, "regulares")]
        nombre = nombre_caso(c) if c in CASOS else "P6 con la entrada corregida"
        filas.append([nombre, etiqueta(r["etiqueta_citable"]),
                      f"{num(r['cambio_T1'])} {intervalo(r['ic_T1'])}", f"{num(r['cambio_T2'])} {intervalo(r['ic_T2'])}",
                      repite(r)])
    escribir("plan3_regulares.tex",
             ["Segundo estudio, llegadas regulares: etiqueta citable de IPPO con mensajes corregido frente al fijo",
              "ajustado al segundo (30 semillas por tanda).",
              "fuente: plan3/salidas/veredicto3_celdas.csv (filas P1-P6 y P6e con llegadas regulares).",
              "Entorno: \\setstretch{1}, \\footnotesize y \\setlength{\\tabcolsep}{3pt}."],
             tabular(f"{IZQ}{{4.0cm}}{IZQ}{{3.0cm}}{IZQ}{{2.5cm}}{IZQ}{{2.5cm}}{IZQ}{{1.4cm}}",
                     ["Caso", "Veredicto", "Cambio, tanda 1 (\\%)", "Cambio, tanda 2 (\\%)", "Se repite"],
                     filas))


def tabla_sensibilidad(celdas):
    filas = []
    for c, nombre in SENSIBILIDAD.items():
        r = celdas[(c, "aleatorias")]
        filas.append([nombre, etiqueta(r["etiqueta_citable"]),
                      f"{num(r['cambio_T1'])} {intervalo(r['ic_T1'])}", f"{num(r['cambio_T2'])} {intervalo(r['ic_T2'])}",
                      repite(r)])
        if c == "per1":
            filas.append("\\midrule")
    escribir("plan3_sensibilidad.tex",
             ["Segundo estudio, sensibilidad con llegadas aleatorias: mezcla de vehiculos de Lima, arranque lento y",
              "perfil de 10 min, en el corredor y en la red con demanda nominal.",
              "fuente: plan3/salidas/veredicto3_celdas.csv (filas mix1, mixa1, per1, mix3, mixa3 y per3).",
              "Entorno: \\setstretch{1}, \\footnotesize y \\setlength{\\tabcolsep}{3pt}."],
             tabular(f"{IZQ}{{4.4cm}}{IZQ}{{2.8cm}}{IZQ}{{2.4cm}}{IZQ}{{2.4cm}}{IZQ}{{1.4cm}}",
                     ["Caso", "Veredicto", "Cambio, tanda 1 (\\%)", "Cambio, tanda 2 (\\%)", "Se repite"],
                     filas))


# ---------------- Referencias al lado ----------------
def lista_casos(casos):
    """'P1, P2, P6'; 'P1 a P6' si estan los seis; raya si no hay ninguno."""
    if not casos:
        return "---"
    if len(casos) == len(CASOS):
        return f"{casos[0]} a {casos[-1]}"
    return ", ".join(casos)


def tabla_referencias():
    """Casos en que el modelo citado recibe cada etiqueta frente a cada referencia ('Referencias al lado')."""
    nota = {"EMPATA (mejora no confirmada)": ("EMPATA", "a"), "EMPATA (falla no confirmada)": ("EMPATA", "b")}
    por_caso = {r["Caso"]: r for r in tabla_md("Referencias al lado")
                if r["Caso"] in CASOS and r["Llegadas"] == "aleatorias"}
    etiquetas = ["FUNCIONA", "MEJORA", "EMPATA", "FALLA"]
    # una fila por referencia y una columna por etiqueta, con los casos dentro: cabe en el ancho del texto
    filas = []
    for ref in REFERENCIAS:
        grupos = {e: [] for e in etiquetas}
        for c in CASOS:
            e, marca = nota.get(por_caso[c][ref], (por_caso[c][ref], ""))
            grupos[e].append(c + (f"\\textsuperscript{{{marca}}}" if marca else ""))
        filas.append([NOMBRE_REF[ref]] + [lista_casos(grupos[e]) for e in etiquetas])
    escribir("plan3_referencias.tex",
             ["Segundo estudio, llegadas aleatorias: casos en que el modelo citado recibe cada etiqueta citable frente",
              "a cada una de las otras referencias (la misma regla, con esa referencia en el lugar del fijo ajustado al",
              "segundo).",
              "fuente: plan3/salidas/veredicto3.md, tabla 'Referencias al lado' (filas P1-P6 con llegadas aleatorias).",
              "a: mejora en una sola tanda. Entorno: \\setstretch{1}, \\footnotesize y \\setlength{\\tabcolsep}{3pt}."],
             tabular(f"{IZQ}{{4.2cm}}{IZQ}{{3.0cm}}{IZQ}{{1.8cm}}{IZQ}{{3.0cm}}{IZQ}{{1.8cm}}",
                     ["Frente a"] + etiquetas, filas))


def tabla_referencias_cifras(celdas, comp):
    """Cambio del modelo citado frente al actuado ajustado y frente al fijo entregado, en las dos tandas."""
    filas = []
    for c in CASOS:
        clave = celdas[(c, "aleatorias")]["clave_citado"]
        fila = [nombre_caso(c)]
        for ref in ("actuado ajustado", "fijo entregado"):
            v = {r["tanda"]: r for r in comp if r["celda"] == c and r["llegadas"] == "aleatorias"
                 and r["clave"] == clave and r["referencia"] == ref and r["metrica"] == "retraso_total_prom"}
            fila.append(f"{num(v['T1']['cambio'])} y {num(v['T2']['cambio'])}")
        filas.append(fila)
    escribir("plan3_referencias_cifras.tex",
             ["Segundo estudio, llegadas aleatorias: cambio del retraso total del modelo citado frente al actuado",
              "ajustado y frente al fijo entregado, en la tanda 1 y en la tanda 2 (%).",
              "fuente: plan3/salidas/veredicto3_comparaciones.csv (clave del modelo citado de cada caso, referencias",
              "'actuado ajustado' y 'fijo entregado', metrica retraso_total_prom, columna cambio).",
              "Entorno: \\setstretch{1}, \\footnotesize y \\setlength{\\tabcolsep}{3pt}."],
             tabular(f"{IZQ}{{5.6cm}}{IZQ}{{3.6cm}}{IZQ}{{3.6cm}}",
                     ["Caso", "Frente al actuado ajustado (\\%)", "Frente al fijo ajustado desde 10~s (\\%)"], filas))


def tabla_margen(celdas, comp):
    """Por caso: retraso con el fijo ajustado al segundo, la mejor de las otras referencias y el modelo citado."""
    filas = []
    for c in CASOS:
        r = celdas[(c, "aleatorias")]
        refs = [x for x in comp if x["celda"] == c and x["llegadas"] == "aleatorias" and x["tanda"] == "T1"
                and x["referencia"] == "fijo fino" and x["metrica"] == "retraso_total_prom"
                and x["clave"].startswith("ref_")]
        mejor = min(refs, key=lambda x: float(x["cambio"]))
        iguales = [x["brazo"] for x in refs if abs(float(x["cambio"]) - float(mejor["cambio"])) < 0.005]
        nombres = iguales[0] if len(iguales) == 1 else f"{iguales[0]} y {len(iguales) - 1} más"
        filas.append([nombre_caso(c), f"{float(refs[0]['media_ref']):.1f}",
                      f"{num(mejor['cambio'])} ({nombres})", num(r["cambio_T1"])])
    escribir("plan3_margen.tex",
             ["Segundo estudio, llegadas aleatorias, tanda 1: retraso total con el fijo ajustado al segundo, la mejor",
              "de las otras referencias frente a el y el modelo citado. Lectura posterior al cierre (descriptiva).",
              "fuente: plan3/salidas/veredicto3_comparaciones.csv (tanda T1, referencia 'fijo fino', claves ref_*:",
              "media_ref y el menor cambio) y veredicto3_celdas.csv (cambio_T1 del modelo citado).",
              "Entorno: \\setstretch{1}, \\footnotesize y \\setlength{\\tabcolsep}{3pt}."],
             tabular(f"{IZQ}{{4.6cm}}{IZQ}{{2.2cm}}{IZQ}{{4.2cm}}{IZQ}{{2.0cm}}",
                     ["Caso", "Retraso con el fijo ajustado al segundo (s/veh)",
                      "La mejor de las otras referencias (\\%)", "Modelo citado (\\%)"], filas))


# ---------------- Promocion ----------------
def tabla_promocion(celdas):
    filas = []
    for c in CASOS:
        with open(os.path.join(PROMOCION, ESCENARIO[c] + ".json"), encoding="utf-8") as f:
            d = json.load(f)
        cambios = {}
        for cand in d["candidatos"]:
            for clave, _ in CANDIDATOS:
                if f"_{clave}_" in cand["brazo"]:
                    cambios[clave] = cand["cambio_vs_v2_pct"]
        citado = celdas[(c, "aleatorias")]["modelo_citado"]
        filas.append([c] + [num(cambios[k], 2) if k in cambios else "---" for k, _ in CANDIDATOS]
                     + ["Modelo completo" if citado == "modelo completo" else "IPPO con mensajes corregido"])
    escribir("plan3_promocion.tex",
             ["Segundo estudio, regla de promocion con llegadas aleatorias: cambio del retraso total de cada variante",
              "frente a IPPO con mensajes corregido en las 16 semillas de promocion (15009-15024), y modelo citado.",
              "fuente: plan3/promocion/poi_<caso>.json (candidatos: cambio_vs_v2_pct) y",
              "plan3/salidas/veredicto3_celdas.csv (modelo_citado). Se promueve la variante de menor retraso si le",
              "gana a IPPO con mensajes corregido por al menos 1 %.",
              "Entorno: \\setstretch{1}, \\footnotesize y \\setlength{\\tabcolsep}{3pt}."],
             tabular(f"l{IZQ}{{2.0cm}}{IZQ}{{2.0cm}}{IZQ}{{2.0cm}}{IZQ}{{2.0cm}}{IZQ}{{3.6cm}}",
                     ["Caso"] + [f"{n} (\\%)" for _, n in CANDIDATOS] + ["Modelo citado"], filas))


# ---------------- Figura ----------------
FONDO, TINTA, TINTA2, APAGADO, EJE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#c3c2b7"
VERDE, VERDE_OSCURO, ROJO = "#0ca30c", "#006300", "#d03b3b"
COLOR = {"FUNCIONA": VERDE_OSCURO, "MEJORA": VERDE, "EMPATA": EJE, "FALLA": ROJO}
BORDE = {"FUNCIONA": VERDE_OSCURO, "MEJORA": VERDE, "EMPATA": APAGADO, "FALLA": ROJO}
UMBRAL, META = -5.0, -25.0          # los de la Figura fig:plan2-mejora-caso (sintesis_plan.py)


def mezcla(color, alfa, fondo=FONDO):
    from matplotlib.colors import to_rgb, to_hex
    return to_hex([alfa * c + (1 - alfa) * f for c, f in zip(to_rgb(color), to_rgb(fondo))])


def punto_etiqueta(texto):
    """(etiqueta que da el color, es pendiente)."""
    m = re.match(r"PENDIENTE \(no convergió; provisional: (\w+)\)", texto)
    return (m.group(1), True) if m else (texto.split(" ")[0], False)


def figura(celdas):
    """Cambio del retraso total frente al fijo ajustado al segundo, por caso, con llegadas regulares y aleatorias y
    las dos tandas de cada una, sobre las bandas de veredicto de la Figura fig:plan2-mejora-caso."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    menos = "−"
    series = (("regulares", "s", 6.2, -0.27), ("aleatorias", "o", 7.2, 0.15))
    puntos, textos = [], []
    for i, c in enumerate(CASOS):
        for llegadas, marca, tam, dx in series:
            r = celdas[(c, llegadas)]
            ys = []
            for k, t in enumerate(("T1", "T2")):
                y = float(r[f"cambio_{t}"])
                a, b = (float(v) for v in r[f"ic_{t}"].strip("[]").split(","))
                ver, pendiente = punto_etiqueta(r[f"etiqueta_{t}"])
                puntos.append((i + dx + 0.12 * k, y, (a, b), ver, pendiente, marca, tam))
                ys.append((y, a, b))
            rotulo = " y ".join(num(y).strip("$").replace("-", menos) for y, _, _ in ys)
            textos.append((i + dx + 0.06, min(a for _, a, _ in ys), max(b for _, _, b in ys), rotulo, llegadas))
    y0, y1 = -34.0, 9.5
    with plt.rc_context({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.edgecolor": EJE,
                         "axes.labelcolor": TINTA2, "xtick.color": TINTA2, "ytick.color": TINTA2}):
        fig, ax = plt.subplots(figsize=(7.2, 4.9), facecolor=FONDO)
        ax.set_facecolor(FONDO)
        x0, x1 = -0.68, len(CASOS) - 0.32
        ax.axhspan(y0, UMBRAL, color=mezcla(VERDE, 0.15), lw=0, zorder=0)
        ax.axhspan(UMBRAL, 0, color=mezcla(VERDE, 0.06), lw=0, zorder=0)
        ax.axhspan(0, y1, color=mezcla(ROJO, 0.09), lw=0, zorder=0)
        ax.grid(axis="y", color=FONDO, lw=0.8, zorder=1)
        ax.set_axisbelow(True)
        ax.axhline(0, color=APAGADO, lw=0.9, zorder=2)
        ax.axhline(META, color=TINTA2, lw=0.9, ls=(0, (1, 2.2)), zorder=2)
        rot = dict(fontsize=7.4, color=TINTA2, linespacing=1.25, zorder=2)
        ax.text(x0 + 0.1, y1 - 0.8, "Más retraso que el fijo: FALLA si es significativo", ha="left", va="top", **rot)
        ax.text(x0 + 0.1, UMBRAL - 0.9, f"Mejora clara, de {menos}5 % o más negativo:\nFUNCIONA si es significativa\n"
                "y no pierde contra el actuado ajustado", ha="left", va="top", **rot)
        ax.text(x0 + 0.1, META + 0.6, f"meta de la tesis: {menos}25 %", ha="left", va="bottom", fontsize=7.4,
                color=TINTA2, zorder=2)
        for x, y, ic, ver, pendiente, marca, tam in puntos:
            ax.plot([x, x], list(ic), color=TINTA2, lw=1.1, zorder=3, solid_capstyle="butt")
            if pendiente:
                estilo = dict(mfc=FONDO, mec=BORDE.get(ver, TINTA2), mew=1.8)
            else:
                estilo = dict(mfc=COLOR.get(ver, EJE), mec=APAGADO if ver == "EMPATA" else FONDO,
                              mew=1.0 if ver == "EMPATA" else 1.1)
            ax.plot(x, y, marca, ms=tam, zorder=5, **estilo)
        for x, bajo, alto, rotulo, llegadas in textos:
            # el rotulo va debajo del par si la mejora es grande y encima si esta cerca de cero
            if bajo < -8:
                ax.annotate(rotulo, (x, bajo), xytext=(0, -4), textcoords="offset points", ha="center", va="top",
                            fontsize=7.0, color=TINTA, zorder=6)
            else:
                arriba = llegadas == "regulares"
                ax.annotate(rotulo, (x, alto if arriba else bajo), xytext=(0, 4 if arriba else -4),
                            textcoords="offset points", ha="center", va="bottom" if arriba else "top",
                            fontsize=7.0, color=TINTA, zorder=6)
        ax.set_ylim(y0, y1)
        marcas = list(range(-30, 6, 5))
        ax.set_yticks(marcas)
        ax.set_yticklabels([f"{t:+d}".replace("-", menos) if t else "0" for t in marcas], fontsize=7.8)
        ax.set_xticks(range(len(CASOS)))
        redes = {c: red.replace("red con ", "red con\n") for c, (red, _, _) in CASOS.items()}
        ax.set_xticklabels([f"{c}\n{redes[c]}\n{veh} veh/h" for c, (_, _, veh) in CASOS.items()], fontsize=7.6,
                           color=TINTA2, linespacing=1.3)
        ax.set_xlim(x0, x1)
        ax.tick_params(length=0)
        ax.set_ylabel("Cambio del retraso total frente al fijo ajustado al segundo (%)\n"
                      "negativo = menos retraso = mejora", fontsize=8.0, linespacing=1.4)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        p = dict(ls="", ms=7.0)
        por_etiqueta = [Line2D([], [], marker="o", mfc=COLOR[v], mec=APAGADO if v == "EMPATA" else FONDO, label=v, **p)
                        for v in ("FUNCIONA", "MEJORA", "EMPATA", "FALLA")]
        por_etiqueta.append(Line2D([], [], marker="o", mfc=FONDO, mec=TINTA2, mew=1.6, **p,
                                   label="Hueco: entrenamiento sin estabilizar\n(borde del color de su veredicto)"))
        por_llegadas = [Line2D([], [], marker="s", mfc=TINTA2, mec=FONDO, label="Llegadas regulares", **p),
                        Line2D([], [], marker="o", mfc=TINTA2, mec=FONDO, label="Llegadas aleatorias", **p),
                        Line2D([], [], marker="|", ms=11, mew=1.3, color=TINTA2, ls="", label="IC95 %")]
        comun = dict(fontsize=7.4, title_fontsize=7.4, frameon=False, handletextpad=0.4, borderaxespad=0.2,
                     alignment="left", labelcolor=TINTA)
        ley1 = ax.legend(handles=por_etiqueta, ncol=3, loc="lower left", bbox_to_anchor=(-0.01, 1.01),
                         title="Color: veredicto de cada tanda", columnspacing=1.2, **comun)
        ax.add_artist(ley1)
        ax.legend(handles=por_llegadas, ncol=1, loc="lower center", bbox_to_anchor=(0.5, 0.015),
                  title="Forma: llegadas (cada par: tandas 1 y 2)", **comun)
        for ley in ax.get_legend(), ley1:
            ley.get_title().set_color(TINTA2)
        ruta = os.path.join(IMAGENES, "fig_plan3_cambio.png")
        # la leyenda de colores va fuera de los ejes: se pasa aparte para que el recorte la incluya
        fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=FONDO, bbox_extra_artists=[ley1])
        fig.savefig(os.path.splitext(ruta)[0] + ".pdf", bbox_inches="tight", facecolor=FONDO,
                    bbox_extra_artists=[ley1], metadata={"CreationDate": None})
        plt.close(fig)
    print("Escrito", os.path.relpath(ruta, AQUI), "y su .pdf")


# ---------------- Resultado central: tabla y figura de retrasos ----------------
def retrasos(celdas, comp, c, tanda="T1"):
    """(fijo ajustado al segundo, actuado ajustado, modelo citado): retraso total medio (s/veh) de un caso con llegadas
    aleatorias en una tanda. La fila del modelo citado es la que da el cambio de veredicto3_celdas.csv."""
    cambio = float(celdas[(c, "aleatorias")][f"cambio_{tanda}"])
    nombre = celdas[(c, "aleatorias")]["modelo_citado"]
    filas = [r for r in comp if r["celda"] == c and r["llegadas"] == "aleatorias" and r["tanda"] == tanda
             and r["referencia"] == "fijo fino" and r["metrica"] == "retraso_total_prom"]
    modelo = [r for r in filas if r["brazo"].startswith(nombre) and abs(float(r["cambio"]) - cambio) < 0.006]
    actuado = [r for r in filas if r["clave"] == "ref_actuadoaj"]
    if not modelo or len(actuado) != 1:
        raise SystemExit(f"{c} {tanda}: no encuentro la fila del modelo citado o la del actuado ajustado")
    return float(modelo[0]["media_ref"]), float(actuado[0]["media_brazo"]), float(modelo[0]["media_brazo"])


def tabla_central(celdas, comp):
    filas = []
    for c, (red, demanda, veh) in CASOS.items():
        r = celdas[(c, "aleatorias")]
        fijo, _, modelo = retrasos(celdas, comp, c)
        filas.append([c, f"{red.capitalize()}, {demanda}", str(veh), f"{fijo:.1f}", f"{modelo:.1f}",
                      f"{num(r['cambio_T1'])} y {num(r['cambio_T2'])}", etiqueta(r["etiqueta_citable"])])
    escribir("plan3_central.tex",
             ["Resultado central (segundo estudio, llegadas aleatorias): retraso total por vehiculo con el fijo ajustado",
              "al segundo y con el modelo citado en la tanda 1, cambio del modelo frente al fijo en las dos tandas",
              "(100 semillas cada una) y veredicto que se repite en las dos.",
              "fuente: plan3/salidas/veredicto3_comparaciones.csv (tanda T1, referencia 'fijo fino', fila del modelo",
              "citado: media_ref y media_brazo) y veredicto3_celdas.csv (cambio_T1, cambio_T2 y etiqueta_citable).",
              "Entorno: \\setstretch{1}, \\footnotesize y \\setlength{\\tabcolsep}{3pt}."],
             tabular(f"l{IZQ}{{2.8cm}}r{IZQ}{{2.2cm}}{IZQ}{{1.9cm}}{IZQ}{{2.4cm}}{IZQ}{{2.4cm}}",
                     ["Caso", "Red y demanda", "Veh/h", "Retraso con el fijo ajustado al segundo (s/veh)",
                      "Retraso con el modelo (s/veh)", "Cambio, tandas 1 y 2 (\\%)", "Veredicto"], filas))


def figura_retraso(celdas, comp):
    """Retraso total por vehiculo con el fijo ajustado al segundo, el actuado ajustado y el modelo citado, por caso
    (llegadas aleatorias, tanda 1). Un panel por caso, cada uno con su escala: P2 tiene diez veces el retraso de P1."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    menos = "−"
    gris, claro, azul = "#898781", "#c3c2b7", "#1f6fb2"
    with plt.rc_context({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.edgecolor": EJE,
                         "axes.labelcolor": TINTA2, "xtick.color": TINTA2, "ytick.color": TINTA2}):
        fig, ejes = plt.subplots(2, 3, figsize=(7.2, 4.9), facecolor=FONDO)
        orden = ["P1", "P3", "P5", "P2", "P4", "P6"]          # arriba la demanda nominal, abajo la alta
        for ax, c in zip(ejes.flat, orden):
            red, demanda, veh = CASOS[c]
            valores = retrasos(celdas, comp, c)
            cambio = celdas[(c, "aleatorias")]["cambio_T1"]
            ax.set_facecolor(FONDO)
            barras = ax.bar(range(3), valores, width=0.62, color=[gris, claro, azul], zorder=3)
            for b, v in zip(barras, valores):
                ax.annotate(f"{v:.1f}", (b.get_x() + b.get_width() / 2, v), xytext=(0, 2.5), textcoords="offset points",
                            ha="center", va="bottom", fontsize=7.4, color=TINTA)
            ax.set_ylim(0, max(valores) * 1.2)
            ax.set_xticks([])
            ax.tick_params(length=0, labelsize=7.2)
            ax.grid(axis="y", color=EJE, lw=0.4, alpha=0.5, zorder=1)
            ax.set_axisbelow(True)
            for s in ("top", "right"):
                ax.spines[s].set_visible(False)
            ax.set_title(f"{c}: {red}, demanda {demanda}\n{veh} veh/h; cambio: "
                         f"{num(cambio).strip('$').replace('-', menos)} %", fontsize=7.6, color=TINTA2, loc="left",
                         linespacing=1.35)
        for ax in ejes[:, 0]:
            ax.set_ylabel("Retraso total (s por vehículo)", fontsize=7.6)
        leyenda = [Patch(color=gris, label="Fijo ajustado al segundo"), Patch(color=claro, label="Actuado ajustado"),
                   Patch(color=azul, label="Modelo citado")]
        fig.legend(handles=leyenda, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.03), frameon=False,
                   fontsize=7.8, labelcolor=TINTA, handlelength=1.2, columnspacing=2.0)
        fig.tight_layout(rect=(0, 0, 1, 0.96), h_pad=1.6, w_pad=1.2)
        ruta = os.path.join(IMAGENES, "fig_plan3_retraso.png")
        fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=FONDO)
        fig.savefig(os.path.splitext(ruta)[0] + ".pdf", bbox_inches="tight", facecolor=FONDO,
                    metadata={"CreationDate": None})
        plt.close(fig)
    print("Escrito", os.path.relpath(ruta, AQUI), "y su .pdf")


def main():
    celdas = {(r["celda"], r["llegadas"]): r for r in leer_csv("veredicto3_celdas.csv")}
    comp = leer_csv("veredicto3_comparaciones.csv")
    tabla_central(celdas, comp)
    figura_retraso(celdas, comp)
    tabla_aleatorias(celdas)
    tabla_regulares(celdas)
    tabla_sensibilidad(celdas)
    tabla_referencias()
    tabla_referencias_cifras(celdas, comp)
    tabla_margen(celdas, comp)
    tabla_promocion(celdas)
    figura(celdas)


if __name__ == "__main__":
    main()
