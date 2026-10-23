"""
sintesis_plan.py - Resumen del plan de pruebas fuera del veredicto.

Uso (desde demo_rl):  python sintesis_plan.py [--metrica retraso_total_prom] [--plan2 plan2] [--tesis TESIS]
                      [--fijo BRAZO] [--prefijo P] [--casos P1-P5] [--sin-trivial]
  principal:              python sintesis_plan.py --metrica timeloss_prom --fijo fijo_2509 --sin-trivial
  robustez:               python sintesis_plan.py --prefijo robustez_
  solo P1-P5 (sin tocar la tesis): primero veredicto.py y despues este script, los dos con las mismas opciones
    mas --casos P1-P5 --prefijo p1p5_ (o robustez_p1p5_) --tesis <otra carpeta>; sin el <prefijo>veredicto.csv
    el numero unico sale vacio

Lee plan2/evaluacion_<esc>.csv (consolidar.py, una fila por brazo y semilla) y plan2/veredicto.csv
(base publicada de cada modelo y caso). Calcula:
  1. Numero unico por modelo: media geometrica, sobre los casos, del cociente entre el retraso del
     modelo (base publicada) y el del fijo, expresada como cambio %:
         delta_geo = 100 * (exp(media_c ln(m_c / f_c)) - 1)
     y lo mismo frente al actuado. IC95 por bootstrap pareado: en cada remuestreo se toman semillas
     con reemplazo dentro de cada caso (las mismas para el modelo y la referencia); 10 000
     remuestreos, numpy default_rng(0). Sensibilidad: el mismo indice dejando fuera un caso a la vez.
     Resume; no reemplaza al veredicto por caso (veredicto.py).
  2. De que depende el resultado: ANOVA de dos factores con replica (caso x modelo, las tres bases
     como replicas) sobre el delta % frente al fijo de cada base; fraccion de la suma de cuadrados
     (eta cuadrado) de caso, modelo, interaccion y base. Con los seis aprendices que tienen tres bases
     en todos los casos (ql, sarsa, dqn, ippo_local, ippo_vecinos, mappo) y con solo los cuatro
     profundos. Solo entran los casos en que todas esas celdas estan completas.
  3. Figura de la mejora por caso: IPPO vecinos y MAPPO frente al fijo, el valor del veredicto
     pre-registrado (timeLoss, fijo del plan; plan2/veredicto_congelado_0355.csv)
     y el de la re-medicion.
Salidas: plan2/sintesis_numero_unico.csv, plan2/sintesis_anova.csv,
  TESIS/secciones/tablas/plan2_numero_unico.tex (tab:plan2-numero-unico),
  TESIS/secciones/tablas/plan2_anova.tex (tab:plan2-anova), TESIS/images/fig_plan2_mejora_caso.png
  y, con --fijo distinto de "fijo", el mismo dibujo en PDF vectorial (fig_plan2_mejora_caso.pdf).

Entrega 3 (23.10.2026): los .tex y las figuras usan los nombres del glosario de la tesis (veredicto.NOMBRE_TEX:
IPPO con mensajes, IPPO sin mensajes, ciclo minimo, version evaluada, medicion mas estricta) y la nota de los
casos que faltan va en palabras junto al modelo (antes, un superindice a). La figura de la mejora por caso
(figura_mejora) cambio la linea de la meta por bandas de veredicto: verde para -5 % o menos, verde muy claro de
-5 a 0 % y roja para valores positivos; cada punto lleva el color de su veredicto de veredicto.csv (hueco si es
PENDIENTE, con el borde del color del provisional), la forma dice la serie y una linea punteada marca la meta.
Los CSV no cambian.
Verificacion de la fase 2 (23.10.2026): el rotulo de la banda de FUNCIONA agrega "y no pierde contra el actuado";
la tabla del resumen en un numero da dos decimales (DEC_NUMERO), como el texto, y la del ANOVA llama
"Entrenamiento" a la semilla base y "Double DQN" a DQN. Los CSV siguen sin cambios.

Opciones del resultado principal (sin ellas, todo queda como antes; las mismas de veredicto.py):
  --fijo BRAZO   referencia del numero unico, del ANOVA y de la figura (fijo_2509: el fijo del veredicto
                 pre-registrado). Con una referencia distinta de "fijo", la figura ya no es la de dos puntos
                 (pre-registro y re-medicion) sino la mejora por caso frente a esa referencia: IPPO vecinos y
                 MAPPO con su IC95 y, bajo cada caso, semaforos, carriles por sentido y demanda.
  --prefijo P    lee plan2/<P>veredicto.csv; escribe plan2/<P>sintesis_*.csv y, en lugar de plan2_,
                 <P>numero_unico.tex, <P>anova.tex y fig_<P>mejora_caso.png (labels tab:<P sin _>-...).
  --casos        solo esos casos; --sin-trivial: sin la fila del control trivial.
  Un caso entra al numero unico solo si tiene la referencia evaluada (antes bastaba el archivo de
  evaluacion); asi un caso sin fijo todavia (P6) no entra a medias.
"""
import os
import csv
import argparse

import numpy as np

import veredicto as vd

N_BOOT = 10000
APRENDICES = ["ql", "sarsa", "dqn", "ippo_local", "ippo_vecinos", "mappo"]
PROFUNDOS = ["dqn", "ippo_local", "ippo_vecinos", "mappo"]
MODELOS = ["ippo_vecinos", "mappo", "dqn", "ippo_local", "ql", "sarsa", "actuado", "trivial"]
FIJO = "fijo"        # brazo de referencia (--fijo)
PREFIJO = ""         # --prefijo


def leer_csv(ruta):
    if not os.path.exists(ruta):
        return []
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def por_semilla(plan2, esc, metrica):
    """{brazo: {semilla: valor}} de evaluacion_<esc>.csv."""
    datos = {}
    for r in leer_csv(os.path.join(plan2, f"evaluacion_{esc}.csv")):
        if r.get(metrica) not in ("", None):
            datos.setdefault(r["brazo"], {})[int(r["semilla"])] = float(r[metrica])
    return datos


def publicadas(plan2):
    """{(modelo, escenario): brazo evaluado} con la base publicada de veredicto.csv."""
    brazos = {}
    for r in leer_csv(os.path.join(plan2, PREFIJO + "veredicto.csv")):
        if r["modelo"] in ("actuado", "trivial"):
            brazos[(r["modelo"], r["escenario"])] = r["modelo"]
        elif r.get("base_publicada"):
            brazos[(r["modelo"], r["escenario"])] = f"{r['modelo']}_s{r['base_publicada']}"
    return brazos


def pares(datos, brazo, ref):
    """Arreglos (x, y) del brazo y la referencia en las semillas comunes."""
    x, y = datos.get(brazo, {}), datos.get(ref, {})
    s = sorted(set(x) & set(y))
    return np.array([x[k] for k in s]), np.array([y[k] for k in s])


def indice_geo(series, rng):
    """Media geometrica del cociente sobre casos, con IC bootstrap pareado por caso.
    series: lista de (x, y) por caso. Devuelve (delta %, lo, hi)."""
    logs = [np.log(x.mean() / y.mean()) for x, y in series]
    acum = np.zeros(N_BOOT)
    for x, y in series:
        idx = rng.integers(0, len(x), size=(N_BOOT, len(x)))
        acum += np.log(x[idx].mean(1) / y[idx].mean(1))
    boot = (np.exp(acum / len(series)) - 1) * 100
    return (np.exp(np.mean(logs)) - 1) * 100, np.percentile(boot, 2.5), np.percentile(boot, 97.5)


def numero_unico(plan2, metrica):
    datos = {e: por_semilla(plan2, e, metrica) for _, e in vd.CASOS}
    casos = [(c, e) for c, e in vd.CASOS if FIJO in datos[e]]
    brazos = publicadas(plan2)
    filas = []
    for m in MODELOS:
        for ref in (FIJO, "actuado"):
            if m == ref or (ref == "actuado" and m == "trivial"):
                continue
            series, usados = [], []
            for c, e in casos:
                b = brazos.get((m, e))
                if b and b in datos[e] and ref in datos[e]:
                    x, y = pares(datos[e], b, ref)
                    if len(x):
                        series.append((x, y))
                        usados.append(c)
            if not series:
                continue
            d, lo, hi = indice_geo(series, np.random.default_rng(0))
            fila = {"modelo": m, "referencia": ref, "casos": "/".join(usados), "delta_geo": round(d, 2),
                    "ic_lo": round(lo, 2), "ic_hi": round(hi, 2)}
            for k, c in enumerate(usados):           # sensibilidad: sin un caso
                resto = series[:k] + series[k + 1:]
                if resto:
                    fila[f"sin_{c}"] = round(indice_geo(resto, np.random.default_rng(0))[0], 2)
            filas.append(fila)
    return filas, [c for c, _ in casos]


def anova(plan2, metrica, modelos):
    """eta cuadrado de caso, modelo, interaccion y base sobre el delta % frente al fijo por base."""
    celdas, casos_ok = {}, []
    for c, e in vd.CASOS:
        datos = por_semilla(plan2, e, metrica)
        if FIJO not in datos:
            continue
        valores = {}
        for m in modelos:
            deltas = []
            for b in vd.BASES:
                x, y = pares(datos, f"{m}_s{b}", FIJO)
                if len(x):
                    deltas.append((x.mean() / y.mean() - 1) * 100)
            valores[m] = deltas
        if all(len(v) == len(vd.BASES) for v in valores.values()):
            casos_ok.append(c)
            for m, v in valores.items():
                celdas[(c, m)] = v
    if len(casos_ok) < 2:
        return None
    y = np.array([[celdas[(c, m)] for m in modelos] for c in casos_ok])    # caso x modelo x base
    media = y.mean()
    ss_total = ((y - media) ** 2).sum()
    n_b = y.shape[2]
    ss_caso = n_b * len(modelos) * ((y.mean(axis=(1, 2)) - media) ** 2).sum()
    ss_modelo = n_b * len(casos_ok) * ((y.mean(axis=(0, 2)) - media) ** 2).sum()
    celda = y.mean(axis=2)
    efecto_caso, efecto_modelo = y.mean(axis=(1, 2))[:, None], y.mean(axis=(0, 2))[None, :]
    ss_inter = n_b * ((celda - efecto_caso - efecto_modelo + media) ** 2).sum()
    ss_base = ss_total - ss_caso - ss_modelo - ss_inter
    return {"casos": "/".join(casos_ok), "modelos": "/".join(modelos),
            "caso": round(float(100 * ss_caso / ss_total), 1),
            "modelo": round(float(100 * ss_modelo / ss_total), 1),
            "interaccion": round(float(100 * ss_inter / ss_total), 1),
            "base": round(float(100 * ss_base / ss_total), 1)}


def escribir_csv(ruta, filas):
    campos = []
    for f in filas:
        campos += [k for k in f if k not in campos]
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, restval="")
        w.writeheader()
        w.writerows(filas)
    print("Escrito", ruta)


def num(x, dec=1):
    return f"{x:+.{dec}f}".replace("-", "$-$")


# Decimales del resumen en un numero en la tabla (verificacion de la fase 2 de la entrega 3, 23.10.2026): dos, como
# fija la regla 2 del plan del 14.10 y como lo cita el texto (-6.83, -14.35, -0.03 [-0.56, +0.53]); con uno, la tabla
# de robustez imprimia "-0.0 [-0.6, +0.5]" junto a un texto que dice -0.03.
DEC_NUMERO = 2


def etiqueta(nombre):
    """tab:plan2-<nombre>, o tab:<prefijo sin _>-<nombre> con --prefijo."""
    return "tab:" + (PREFIJO.strip("_").replace("_", "-") or "plan2") + "-" + nombre


def titulo(corto, largo):
    """Titulos con el prefijo al inicio (p. ej. Robustez: ...), como en veredicto.py."""
    t = PREFIJO.strip("_").replace("_", " ").capitalize()
    if not t:
        return corto, largo
    return f"{t}: {corto[0].lower()}{corto[1:]}", f"{t}. {largo}"


def tabla_numero(filas, casos, ruta, metrica):
    por = {(f["modelo"], f["referencia"]): f for f in filas}
    lineas = []
    faltan_casos = False
    for m in MODELOS:
        f, a = por.get((m, FIJO)), por.get((m, "actuado"))
        if not f:
            continue
        # con dos decimales la tabla no cabe en el ancho del texto con el intervalo al lado: va debajo del valor
        d = DEC_NUMERO
        celda_f = vd.apilar([num(f["delta_geo"], d), f"[{num(f['ic_lo'], d)}, {num(f['ic_hi'], d)}]"])
        celda_a = "--" if not a else vd.apilar([num(a["delta_geo"], d),
                                                f"[{num(a['ic_lo'], d)}, {num(a['ic_hi'], d)}]"])
        sens = [num(f[f"sin_{c}"], d) if f"sin_{c}" in f else "--" for c in casos]
        # entrega 3: la nota va en palabras junto al modelo (antes, un superindice a explicado en el titulo)
        faltan = [c for c in casos if c not in f["casos"].split("/")]
        faltan_casos = faltan_casos or bool(faltan)
        nombre = vd.NOMBRE_TEX[m] + (f" (sin {', '.join(faltan)})" if faltan else "")
        lineas.append(" & ".join([nombre, celda_f, celda_a] + sens) + r" \\")
    que = "retraso total" if metrica == "retraso_total_prom" else "timeLoss"
    corto, largo = titulo("Resumen en un número", (
        r"Resumen en un número: media geométrica, sobre los casos, del "
        r"cociente entre el " + que + r" del modelo (versión evaluada) y el de la referencia, "
        r"expresada como cambio \%; negativo es mejor. IC95\,\% bootstrap pareado por semilla dentro de "
        r"cada caso (semillas 1001 a 1030). Las últimas columnas repiten el índice frente al fijo "
        r"dejando fuera un caso."
        + (r" Entre paréntesis junto al modelo, los casos que le faltan; el índice usa los demás."
           if faltan_casos else "")))
    texto = "\n".join([
        "% Generado por sintesis_plan.py. No editar a mano.",
        r"\begin{table}[H]", r"\setstretch{1}", r"\centering", r"\scriptsize", r"\setlength{\tabcolsep}{3pt}",
        r"\begin{tabular}{lcc" + "r" * len(casos) + "}", r"\toprule",
        r" & \makecell{Frente al fijo\\(\%) [IC95]} & \makecell{Frente al actuado\\(\%) [IC95]} & "
        + r"\multicolumn{" + str(len(casos)) + r"}{c}{Frente al fijo, sin el caso} \\",
        r"\cmidrule(lr){4-" + str(3 + len(casos)) + "}",
        "Modelo & & & " + " & ".join(casos) + r" \\", r"\midrule"] + lineas + [
        r"\bottomrule", r"\end{tabular}",
        r"\caption[" + corto + "]{" + largo + "}",
        r"\label{" + etiqueta("numero-unico") + "}", r"\end{table}"])
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write(texto + "\n")
    print("Escrito", ruta)


def tabla_anova(filas, ruta):
    lineas = []
    for nombre, f in filas:
        if f is None:
            continue
        lineas.append(" & ".join([nombre, f["casos"].replace("/", ", "), f"{f['caso']:.1f}",
                                  f"{f['modelo']:.1f}", f"{f['interaccion']:.1f}", f"{f['base']:.1f}"])
                      + r" \\")
    corto, largo = titulo("De qué depende el resultado", (
        r"Fracción de la variación del cambio del "
        r"retraso frente al fijo (\%) que explica cada factor: análisis de varianza de dos "
        r"factores (caso y modelo) con los tres entrenamientos de cada modelo y caso como réplicas. Todos: "
        r"Q-learning, SARSA, Double DQN, IPPO "
        r"sin mensajes, IPPO con mensajes y MAPPO; profundos: los cuatro últimos. Solo entran los casos con "
        r"los tres entrenamientos evaluados en todos esos modelos."))
    texto = "\n".join([
        "% Generado por sintesis_plan.py. No editar a mano.",
        r"\begin{table}[H]", r"\setstretch{1}", r"\centering", r"\small",
        r"\begin{tabular}{llrrrr}", r"\toprule",
        r"Aprendices & Casos & Caso & Modelo & Interacción & Entrenamiento \\", r"\midrule"]
        + lineas + [r"\bottomrule", r"\end{tabular}",
                    r"\caption[" + corto + "]{" + largo + "}",
                    r"\label{" + etiqueta("anova") + "}", r"\end{table}"])
    with open(ruta, "w", encoding="utf-8") as fh:
        fh.write(texto + "\n")
    print("Escrito", ruta)


def etiquetas_casos(filas):
    """Texto bajo cada caso: semaforos, carriles por sentido y demanda (de veredicto.csv)."""
    etiquetas = []
    for c, e in vd.CASOS:
        r = filas.get(("ippo_vecinos", c)) or {}
        carr = r.get("carriles", "?")
        etiquetas.append(f"{c}\n{r.get('semaforos', '?')} sem. · {carr} carril{'es' if carr != '1' else ''}"
                         f"\n{r.get('demanda_veh_h', '?')} veh/h")
    return etiquetas


# Figura de cambio por caso con bandas de veredicto (entrega 3, tarea 4b del pedido del profesor, 23.10.2026).
# Antes: una linea discontinua en la meta y los puntos con el color de la serie. Ahora las bandas marcan los rangos
# de la regla de veredicto (Tabla tab:veredictos: el 5 % separa una mejora clara de una pequena; el signo, mejora de
# mas retraso) y cada punto lleva el color de su veredicto real de plan2/veredicto.csv; la serie va en la forma
# (circulo, IPPO con mensajes; cuadrado, MAPPO). Paleta de la skill dataviz: tinta, ejes y verde y rojo de estado.
# El verde y el rojo no se separan bien con daltonismo, asi que el rango lo dicen tambien la banda rotulada, el eje
# y el valor escrito junto a cada punto; y los rellenos difieren en luminosidad (verde oscuro, verde medio, gris
# claro y rojo), para que la figura se lea tambien impresa en gris.
FONDO, TINTA, TINTA2, APAGADO, EJE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#c3c2b7"
VERDE, VERDE_OSCURO, ROJO = "#0ca30c", "#006300", "#d03b3b"
COLOR_VEREDICTO = {"FUNCIONA": VERDE_OSCURO, "MEJORA": VERDE, "EMPATA": EJE, "FALLA": ROJO}
BORDE_VEREDICTO = {"FUNCIONA": VERDE_OSCURO, "MEJORA": VERDE, "EMPATA": APAGADO, "FALLA": ROJO}
UMBRAL = vd.UMBRAL_DELTA       # -5 %: el umbral de FUNCIONA de la regla de veredicto
META = -25.0                   # meta de retraso de la tesis (de -25 a -40 %)


def mezcla(color, alfa, fondo=FONDO):
    """Color solido equivalente a `color` con opacidad `alfa` sobre el fondo (sin transparencias en el PDF)."""
    from matplotlib.colors import to_rgb, to_hex
    return to_hex([alfa * c + (1 - alfa) * f for c, f in zip(to_rgb(color), to_rgb(fondo))])


def veredicto_punto(texto):
    """(veredicto que da el color, es_pendiente) a partir del texto de veredicto.csv. Un PENDIENTE toma el
    color de su veredicto provisional, que solo se dibuja en el borde del marcador hueco."""
    texto = (texto or "").replace(vd.MARCA_TRIVIAL, "")
    if texto.startswith("PENDIENTE"):
        prov = texto.split("provisional:")[1].strip(" )") if "provisional:" in texto else None
        return prov, True
    return texto.split(" ")[0], False


def etiquetas_casos_lineas(filas):
    """Como etiquetas_casos, pero sin abreviar y una cosa por linea, para el ancho de la figura con bandas."""
    etiquetas = []
    for c, e in vd.CASOS:
        r = filas.get(("ippo_vecinos", c)) or {}
        sem, carr = r.get("semaforos", "?"), r.get("carriles", "?")
        etiquetas.append(f"{c}\n{sem} semáforo{'s' if sem != '1' else ''}\n{carr} carril{'es' if carr != '1' else ''}"
                         f"\n{r.get('demanda_veh_h', '?')} veh/h")
    return etiquetas


def figura_mejora(plan2, ruta, metrica):
    """Cambio frente a la referencia por caso: IPPO con mensajes y MAPPO con su IC95, sobre bandas de veredicto.
    Escribe el PNG de `ruta` y el mismo dibujo en PDF vectorial al lado (la misma ruta con .pdf)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    filas = {(r["modelo"], r["caso"]): r for r in leer_csv(os.path.join(plan2, PREFIJO + "veredicto.csv"))}
    casos = [c for c, _ in vd.CASOS]
    series = (("ippo_vecinos", "o", 7.6, -0.15, "right"), ("mappo", "s", 6.6, 0.15, "left"))
    puntos, bajo, alto = [], META, 0.0
    for i, c in enumerate(casos):
        for m, marca, tam, dx, lado in series:
            r = filas.get((m, c))
            y = vd.flotante(r["delta_fijo"]) if r else None
            if y is None:
                continue
            ic = vd.intervalo({"delta_ic95": r["ic_fijo"]})
            ver, pendiente = veredicto_punto(r["veredicto"])
            puntos.append((i + dx, y, ic, ver, pendiente, marca, tam, lado))
            bajo, alto = min(bajo, y, ic[0] if ic else y), max(alto, y, ic[1] if ic else y)
    y0, y1 = 5 * (bajo // 5) - 3, 5 * (alto // 5 + 1) + 3
    menos = "−"
    with plt.rc_context({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.edgecolor": EJE,
                         "axes.labelcolor": TINTA2, "xtick.color": TINTA2, "ytick.color": TINTA2}):
        fig, ax = plt.subplots(figsize=(7.2, 4.6), facecolor=FONDO)
        ax.set_facecolor(FONDO)
        x0, x1 = -0.68, len(casos) - 0.32
        # bandas por rango del cambio frente al fijo (regla de la Tabla tab:veredictos)
        ax.axhspan(y0, UMBRAL, color=mezcla(VERDE, 0.15), lw=0, zorder=0)
        ax.axhspan(UMBRAL, 0, color=mezcla(VERDE, 0.06), lw=0, zorder=0)
        ax.axhspan(0, y1, color=mezcla(ROJO, 0.09), lw=0, zorder=0)
        ax.grid(axis="y", color=FONDO, lw=0.8, zorder=1)
        ax.set_axisbelow(True)
        ax.axhline(0, color=APAGADO, lw=0.9, zorder=2)
        ax.axhline(META, color=TINTA2, lw=0.9, ls=(0, (1, 2.2)), zorder=2)
        rotulo = dict(fontsize=7.6, color=TINTA2, linespacing=1.25, zorder=2)
        ax.text(x0 + 0.1, y1 - 1.2, "Más retraso que el fijo (cambio positivo):\nFALLA si es significativo",
                ha="left", va="top", **rotulo)
        ax.text(x0 + 0.1, UMBRAL / 2, f"Mejora pequeña, entre {menos}5 y 0 %:\nMEJORA si es significativa",
                ha="left", va="center", **rotulo)
        # verificacion de la fase 2 (23.10.2026): el rotulo dice tambien la condicion frente al actuado de la Tabla
        # tab:veredictos (antes solo "FUNCIONA si es significativa")
        ax.text(x1 - 0.1, (UMBRAL + META) / 2 + 2,
                f"Mejora clara, de {menos}5 % o más negativo:\nFUNCIONA si es significativa\n"
                "y no pierde contra el actuado", ha="right", va="center", **rotulo)
        ax.text(x1 - 0.1, META + 0.6, f"meta de la tesis: {menos}25 %", ha="right", va="bottom",
                fontsize=7.6, color=TINTA2, zorder=2)
        for x, y, ic, ver, pendiente, marca, tam, lado in puntos:
            if ic:
                ax.plot([x, x], list(ic), color=TINTA2, lw=1.3, zorder=3, solid_capstyle="butt")
            if pendiente:
                estilo = dict(mfc=FONDO, mec=BORDE_VEREDICTO.get(ver, TINTA2), mew=1.9)
            else:
                estilo = dict(mfc=COLOR_VEREDICTO.get(ver, EJE), mec=APAGADO if ver == "EMPATA" else FONDO,
                              mew=1.0 if ver == "EMPATA" else 1.2)
            ax.plot(x, y, marca, ms=tam, zorder=5, **estilo)
            izq = lado == "right"
            ax.annotate(f"{y:+.1f}".replace("-", menos), (x, y), xytext=(-7 if izq else 7, 0),
                        textcoords="offset points", ha=lado, va="center", fontsize=7.6, color=TINTA,
                        zorder=6)
        ax.set_ylim(y0, y1)
        marcas = list(range(int(5 * -(-y0 // 5)), int(y1) + 1, 5))
        ax.set_yticks(marcas)
        ax.set_yticklabels([f"{t:+d}".replace("-", menos) if t else "0" for t in marcas], fontsize=7.8)
        ax.set_xticks(range(len(casos)))
        ax.set_xticklabels(etiquetas_casos_lineas(filas), fontsize=7.6, color=TINTA2, linespacing=1.3)
        ax.set_xlim(x0, x1)
        ax.tick_params(length=0)
        que = "del retraso" if metrica == "timeloss_prom" else "del retraso total"
        nombre = "fijo ajustado" if FIJO == "fijo_2509" else "fijo ajustado desde 10 s"
        ax.set_ylabel(f"Cambio {que} frente al {nombre} (%)\nnegativo = menos retraso = mejora",
                      fontsize=8.2, linespacing=1.4)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        # dos leyendas con titulo: el color dice el veredicto y la forma, el modelo
        punto = dict(ls="", ms=7.2)
        por_veredicto = [Line2D([], [], marker="o", mfc=COLOR_VEREDICTO[v], mec=APAGADO if v == "EMPATA" else FONDO,
                                label=v, **punto) for v in ("FUNCIONA", "MEJORA", "EMPATA", "FALLA")]
        por_veredicto.append(Line2D([], [], marker="o", mfc=FONDO, mec=TINTA2, mew=1.6, **punto,
                                    label="PENDIENTE: hueco, con el borde\ndel color de su veredicto provisional"))
        por_modelo = [Line2D([], [], marker="o", mfc=TINTA2, mec=FONDO, label="IPPO con mensajes", **punto),
                      Line2D([], [], marker="s", mfc=TINTA2, mec=FONDO, label="MAPPO", **punto),
                      Line2D([], [], marker="|", ms=11, mew=1.3, color=TINTA2, ls="", label="IC95 %")]
        comun = dict(fontsize=7.6, title_fontsize=7.6, frameon=False, handletextpad=0.4, borderaxespad=0.2,
                     alignment="left", labelcolor=TINTA)
        ley1 = ax.legend(handles=por_veredicto, ncol=3, loc="lower left", bbox_to_anchor=(-0.01, 1.01),
                         title="Color del punto: veredicto", columnspacing=1.2, **comun)
        ax.add_artist(ley1)
        ax.legend(handles=por_modelo, ncol=1, loc="lower right", bbox_to_anchor=(1.01, 1.01),
                  title="Forma: modelo", **comun)
        for ley in ax.get_legend(), ley1:
            ley.get_title().set_color(TINTA2)
        fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=FONDO)
        pdf = os.path.splitext(ruta)[0] + ".pdf"
        fig.savefig(pdf, bbox_inches="tight", facecolor=FONDO, metadata={"CreationDate": None})
        plt.close(fig)
    print("Escrito", ruta)
    print("Escrito", pdf)


def figura(plan2, ruta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    congelado = os.path.join(plan2, "veredicto_congelado_0355.csv")
    viejo = {(r["modelo"], r["caso"]): r for r in leer_csv(congelado)}
    nuevo = {(r["modelo"], r["caso"]): r for r in leer_csv(os.path.join(plan2, PREFIJO + "veredicto.csv"))}
    casos = [c for c, _ in vd.CASOS]
    fondo, eje, rojo = "#fcfcfb", "#c3c2b7", "#d03b3b"
    fig, ax = plt.subplots(figsize=(8.2, 4.0), facecolor=fondo)
    ax.set_facecolor(fondo)
    for i, c in enumerate(casos):
        for m, color, dx in (("ippo_vecinos", "#2a78d6", -0.12), ("mappo", "#eb6834", 0.12)):
            n, v = nuevo.get((m, c)), viejo.get((m, c))
            x = i + dx
            yn = vd.flotante(n["delta_fijo"]) if n else None
            yv = vd.flotante(v["delta_fijo"]) if v else None
            if yn is not None and yv is not None:
                ax.plot([x, x], [yv, yn], color=color, lw=1.6, alpha=0.45, zorder=2)
            if yv is not None:
                ax.plot(x, yv, "o", ms=7, mfc=fondo, mec=color, mew=1.8, zorder=4)
            if yn is not None:
                ic = vd.intervalo({"delta_ic95": n["ic_fijo"]})
                if ic:
                    ax.plot([x, x], list(ic), color=color, lw=1.8, zorder=3)
                ax.plot(x, yn, "o", ms=7, color=color, mec=fondo, mew=1.2, zorder=5)
    ax.axhline(0, color=eje, lw=1.2)
    ax.axhline(-25, color=rojo, lw=1.2, ls=(0, (5, 4)))
    ax.text(len(casos) - 0.55, -24.3, "meta de la tesis: \u221225 %", color=rojo, fontsize=8, ha="right",
            va="bottom")
    ax.set_xticks(range(len(casos)))
    ax.set_xticklabels(etiquetas_casos(nuevo), fontsize=7.6, color="#52514e")
    ax.set_xlim(-0.5, len(casos) - 0.5)
    ax.set_ylabel("Cambio del retraso frente al fijo (%)")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e1e0d9", lw=0.6)
    # nombres del glosario de la tesis (entrega 3): IPPO con mensajes; medicion mas estricta (antes "re-medicion")
    ley = [Line2D([], [], marker="o", ls="", color="#2a78d6", label="IPPO con mensajes"),
           Line2D([], [], marker="o", ls="", color="#eb6834", label="MAPPO"),
           Line2D([], [], marker="o", ls="", mfc=fondo, mec="#898781", mew=1.5,
                  label="veredicto pre-registrado (timeLoss)"),
           Line2D([], [], marker="o", ls="", color="#898781",
                  label="medición más estricta (retraso total), IC95")]
    ax.legend(handles=ley, ncol=4, loc="upper left", bbox_to_anchor=(0, 1.13), fontsize=7.6, frameon=False)
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=fondo)
    plt.close(fig)
    print("Escrito", ruta)


def main():
    global FIJO, PREFIJO
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrica", default="retraso_total_prom",
                    choices=["retraso_total_prom", "timeloss_prom"])
    ap.add_argument("--plan2", default=os.path.join(vd.DIR, "plan2"))
    ap.add_argument("--tesis", default=os.path.join(vd.DIR, "TESIS"))
    ap.add_argument("--fijo", default="fijo", help="brazo de referencia (fijo_2509: el del pre-registro)")
    ap.add_argument("--prefijo", default="", help="prefijo de veredicto.csv y de las salidas")
    ap.add_argument("--casos", default=None, help='solo esos casos, p. ej. "P1-P5"')
    ap.add_argument("--sin-trivial", action="store_true", help="sin la fila del control trivial")
    args = ap.parse_args()
    FIJO, PREFIJO = args.fijo, args.prefijo
    vd.configurar(args.metrica, args.fijo, args.sin_trivial, args.casos, args.prefijo)
    if args.sin_trivial and "trivial" in MODELOS:
        MODELOS.remove("trivial")
    base = PREFIJO or "plan2_"
    filas, casos = numero_unico(args.plan2, args.metrica)
    escribir_csv(os.path.join(args.plan2, PREFIJO + "sintesis_numero_unico.csv"), filas)
    anovas = [("Todos", anova(args.plan2, args.metrica, APRENDICES)),
              ("Profundos", anova(args.plan2, args.metrica, PROFUNDOS))]
    escribir_csv(os.path.join(args.plan2, PREFIJO + "sintesis_anova.csv"),
                 [dict(f, aprendices=n) for n, f in anovas if f])
    tablas = os.path.join(args.tesis, "secciones", "tablas")
    tabla_numero(filas, casos, os.path.join(tablas, base + "numero_unico.tex"), args.metrica)
    tabla_anova(anovas, os.path.join(tablas, base + "anova.tex"))
    ruta_fig = os.path.join(args.tesis, "images", f"fig_{base}mejora_caso.png")
    if FIJO == "fijo":
        figura(args.plan2, ruta_fig)
    else:
        figura_mejora(args.plan2, ruta_fig, args.metrica)
    for f in filas:
        print(f"  {f['modelo']:13s} vs {f['referencia']:7s} {f['delta_geo']:+6.2f} [{f['ic_lo']:+.2f}, "
              f"{f['ic_hi']:+.2f}]  casos {f['casos']}")
    for n, f in anovas:
        print(f"  ANOVA {n}: {f}")


if __name__ == "__main__":
    main()
