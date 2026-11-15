"""
tablas_lima.py - Tablas y figuras del caso Lima para la tesis, con los dos niveles de demanda.

Uso (desde demo_rl/lima):
  python tablas_lima.py --publicada <base> [--alta <base>] [--destino carpeta]
<base> es la base del entrenamiento citado en cada nivel (42, 2042 o 4042): el brazo es completo_s<base>.
Lee solo lo que ya esta escrito: salidas/ y alta/salidas/ (estudio.py), programa.py (estados del semaforo),
demanda.py (demanda) y los CSV de entrenamiento resultados_lima_ippo_vecinos_completo_s<base>.csv de cada carpeta.
No corre ninguna simulacion. Escribe (en TESIS/secciones/tablas y TESIS/images, o todo en --destino para probar):
  lima_semaforo.tex    estados del semaforo: verde del plan actual, de los fijos ajustados y verde minimo
  lima_demanda.tex     demanda publicada por entrada y destino (veh/h)
  lima_resultado.tex   retraso total de cada control y cambio del modelo frente a cada uno, tandas 1 y 2
  lima_completa.tex    lo mismo con IC95 y p, y las referencias secundarias
  lima_entrenamientos.tex   validacion de los tres entrenamientos de cada nivel
  fig_lima_retraso.pdf|png       retraso total por control (tanda 1), un panel por nivel
  fig_lima_aprendizaje.pdf|png   validacion de los entrenamientos frente a las referencias, un panel por nivel
Las tablas llevan solo el entorno tabular; el table, el caption y la etiqueta los pone el texto.
"""
import argparse
import csv
import json
import os
import statistics
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
import estudio
import tablas_plan3 as tp          # formato de numeros y colores de las figuras del segundo estudio

NOMBRE = {"actual": "Plan actual", "fijo": "Fijo ajustado al segundo", "actuadoaj": "Actuado ajustado",
          "actuado": "Actuado por defecto", "minimo": "Ciclo mínimo",
          "actuadoaj12": "Actuado ajustado, primera búsqueda",
          "actuadoajb": "Actuado ajustado, antes de la comprobación del borde"}
PRINCIPALES = ["actual", "fijo", "actuadoaj"]
ENTRADAS = {"RN": "Reducto, desde el norte", "RS": "Reducto, desde el sur", "J": "28 de Julio, desde el puente",
            "B": "Balboa"}
SALIDAS = {"L": "Larco", "J": "el puente", "RN": "Reducto norte", "RS": "Reducto sur"}
NIVELES = {"publicada": ("Publicada", AQUI, 1.0), "alta": ("Alta", os.path.join(AQUI, "alta"), 1.2)}
BASES = (42, 2042, 4042)
AZUL, AZUL_CLARO, GRIS = "#1f6fb2", "#8fb7d9", "#898781"
CEN, DER = ">{\\centering\\arraybackslash}p", ">{\\raggedleft\\arraybackslash}p"     # columnas de ancho fijo
DESTINO = {"tablas": os.path.join(RAIZ, "TESIS", "secciones", "tablas"), "imagenes": os.path.join(RAIZ, "TESIS", "images")}


def escribir(nombre, cabecera, cuerpo):
    ruta = os.path.join(DESTINO["tablas"], nombre)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("% Generado por lima/tablas_lima.py a partir de lima/salidas/ y lima/alta/salidas/. No editar a mano.\n"
                + "".join(f"% {linea}\n" for linea in cabecera) + cuerpo + "\n")
    print("Escrito", ruta)


def par(a, b, formato):
    return f"{formato(a)} y {formato(b)}"


def uno(v):
    return f"{v:.1f}"


# ---------------- Datos ----------------
def leer(carpeta, tanda, brazo):
    ruta = os.path.join(carpeta, "salidas", f"eval_t{tanda}_{brazo}.csv")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8", newline="") as f:
        return {int(r["semilla"]): float(r[estudio.METRICA]) for r in csv.DictReader(f)}


def leer_json(carpeta, nombre):
    with open(os.path.join(carpeta, "salidas", nombre), encoding="utf-8") as f:
        return json.load(f)


def comparaciones(carpeta, modelo):
    """({tanda: {referencia: comparacion del modelo con ella}}, {tanda: {brazo: retraso total medio}})."""
    comp, medias = {}, {}
    for t in estudio.TANDAS:
        vals = leer(carpeta, t, modelo)
        if vals is None:
            raise SystemExit(f"falta {carpeta}/salidas/eval_t{t}_{modelo}.csv")
        comp[t], medias[t] = {}, {modelo: statistics.mean(vals.values())}
        for ref in NOMBRE:
            r = leer(carpeta, t, ref)
            if r is not None:
                comp[t][ref] = estudio.comparar(vals, r)
                medias[t][ref] = comp[t][ref]["media_ref"]
    return comp, medias


def etiquetas(comp):
    """Veredicto de cada tanda con la regla de la tesis (frente al fijo ajustado y al actuado ajustado)."""
    import veredicto as regla
    res = {}
    for t, c in comp.items():
        f, a = c["fijo"], c.get("actuadoaj")
        res[t] = regla.veredicto(f["delta"], f["ic"], f["p"], a["ic"] if a else None, a["p"] if a else None)
    return res


def serie_validacion(carpeta, base):
    ruta = os.path.join(carpeta, f"resultados_lima_ippo_vecinos_completo_s{base}.csv")
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return [(int(r["episodio"]), float(r["val_total"])) for r in csv.DictReader(f) if r.get("val_total")]


# ---------------- Tablas ----------------
def tabla_semaforo(niveles):
    import programa
    fijos = {n: leer_json(NIVELES[n][1], "fijo_ajustado.json") for n in niveles}
    primero = fijos[next(iter(niveles))]
    cab = ["Estado (quién tiene verde)", "Plan actual (s)"] + [f"Fijo ajustado, demanda {NIVELES[n][0].lower()} (s)"
                                                              for n in niveles] + ["Verde mínimo (s)"]
    filas = []
    for k, (nombre, verde, _) in enumerate(programa.PLAN):
        filas.append([nombre, str(verde)] + [str(fijos[n]["ganador"][k]) for n in niveles] + [str(primero["minimos"][k])])
    t = programa.tiempo_fijo()
    filas += ["\\midrule", ["Ciclo, con el ámbar y el tiempo en rojo", str(sum(v for _, v, _ in programa.PLAN) + t)]
              + [str(sum(fijos[n]["ganador"]) + t) for n in niveles] + [str(sum(primero["minimos"]) + t)]]
    escribir("lima_semaforo.tex",
             ["Caso Lima: estados del semaforo del nudo, en su orden, con el verde (s) del plan actual, del fijo ajustado",
              "al segundo de cada nivel de demanda y el verde minimo. Tras cada verde hay 3 s de ambar y, tras los giros,",
              "34 s con todo en rojo.",
              "fuente: lima/programa.py (PLAN, TRANSICION, ROJO_TOTAL) y salidas/fijo_ajustado.json de cada nivel."],
             tp.tabular(f"{tp.IZQ}{{4.3cm}}" + f"{CEN}{{2.1cm}}" * (len(niveles) + 2), cab, filas))


def tabla_demanda():
    import demanda
    tasas, fuente = demanda.tasas()
    filas, total = [], 0.0
    for e, nombre in ENTRADAS.items():
        vals = [statistics.mean(tasas[(e, s)]) if (e, s) in tasas else None for s in SALIDAS]
        suma = sum(v for v in vals if v is not None)
        total += suma
        filas.append([nombre] + [f"{v:.0f}" if v is not None else "---" for v in vals] + [f"{suma:.0f}"])
    filas += ["\\midrule", ["Todo el nudo"] + [f"{sum(statistics.mean(q) for (e, s), q in tasas.items() if s == sal):.0f}"
                                               for sal in SALIDAS] + [f"{total:.0f}"]]
    escribir("lima_demanda.tex",
             ["Caso Lima: demanda publicada (veh/h, media de la hora) por entrada y destino. La demanda alta es esta",
              f"multiplicada por 1.2. fuente: {fuente}; lima/demanda.py."],
             tp.tabular(f"{tp.IZQ}{{4.2cm}}" + f"{DER}{{1.7cm}}" * 4 + "r",
                        ["Entrada"] + [f"Hacia {s}" for s in SALIDAS.values()] + ["Total"],
                        filas))


def tabla_resultado(datos):
    filas = []
    for n, d in datos.items():
        comp, medias, modelo = d["comp"], d["medias"], d["modelo"]
        if filas:
            filas.append("\\midrule")
        primera = f"{NIVELES[n][0]} ({d['veh']:.0f}~veh/h)"
        for ref in PRINCIPALES:
            if ref in comp[1] and ref in comp[2]:
                filas.append([primera, NOMBRE[ref], par(medias[1][ref], medias[2][ref], uno),
                              par(comp[1][ref]["delta"], comp[2][ref]["delta"], tp.num)])
                primera = ""
        filas.append(["", "Modelo completo", par(medias[1][modelo], medias[2][modelo], uno), "---"])
    escribir("lima_resultado.tex",
             ["Caso Lima: retraso total por vehiculo de cada control en las dos tandas de evaluacion (100 semillas cada",
              "una) y cambio del modelo frente a cada control, por nivel de demanda.",
              "fuente: salidas/eval_t1_*.csv y eval_t2_*.csv de lima/ y lima/alta/ (retraso_total_prom); modelo: "
              + ", ".join(f"{n} = {d['modelo']}" for n, d in datos.items()) + "."],
             tp.tabular(f"{tp.IZQ}{{2.5cm}}{tp.IZQ}{{3.7cm}}{tp.IZQ}{{3.4cm}}{tp.IZQ}{{4.0cm}}",
                        ["Demanda", "Control", "Retraso total, tandas 1 y 2 (s por vehículo)",
                         "Cambio del modelo frente a este control, tandas 1 y 2 (\\%)"], filas))


def tabla_completa(datos):
    def celda(c):
        p = "$p < 0.001$" if c["p"] < 0.001 else f"$p = {c['p']:.3f}$"
        return f"{tp.num(c['delta'])} [{tp.num(c['ic'][0])}, {tp.num(c['ic'][1])}], {p}"

    filas = []
    for n, d in datos.items():
        comp, medias, modelo = d["comp"], d["medias"], d["modelo"]
        if filas:
            filas.append("\\midrule")
        primera = NIVELES[n][0]
        for ref in NOMBRE:
            if ref in comp[1] and ref in comp[2]:
                filas.append([primera, NOMBRE[ref], par(medias[1][ref], medias[2][ref], uno),
                              celda(comp[1][ref]), celda(comp[2][ref])])
                primera = ""
        filas.append(["", "Modelo completo", par(medias[1][modelo], medias[2][modelo], uno), "---", "---"])
    escribir("lima_completa.tex",
             ["Caso Lima: todos los controles, por nivel de demanda. Retraso total por vehiculo en las dos tandas y",
              "cambio del modelo frente a cada control, con IC95 (bootstrap pareado, 10 000 remuestreos) y p de Wilcoxon",
              "pareado. fuente: salidas/eval_t1_*.csv y eval_t2_*.csv de lima/ y lima/alta/."],
             tp.tabular(f"{tp.IZQ}{{1.5cm}}{tp.IZQ}{{2.6cm}}{tp.IZQ}{{2.0cm}}{tp.IZQ}{{4.0cm}}{tp.IZQ}{{4.0cm}}",
                        ["Demanda", "Control", "Retraso total, tandas 1 y 2 (s/veh)", "Cambio del modelo, tanda 1 (\\%)",
                         "Cambio del modelo, tanda 2 (\\%)"], filas))


def convergio(carpeta, base):
    """(se estabilizo, plateau %, estabilidad %) con la regla de la tesis (veredicto.convergencia) sobre la validacion."""
    import veredicto as regla
    return regla.convergencia(serie_validacion(carpeta, base), 400)


def tabla_entrenamientos(datos):
    """Los tres entrenamientos de cada nivel: validacion de la version evaluada, retraso en las dos tandas, cambio
    frente al fijo ajustado y si el entrenamiento se estabilizo (regla de la tesis)."""
    filas, notas = [], []
    for n, d in datos.items():
        if filas:
            filas.append("\\midrule")
        primera = NIVELES[n][0]
        for base in BASES:
            carpeta = NIVELES[n][1]
            with open(os.path.join(carpeta, f"politica_lima_vecinos_completo_s{base}.json"), encoding="utf-8") as f:
                meta = json.load(f)
            tandas = [leer(carpeta, t, f"completo_s{base}") for t in estudio.TANDAS]
            fijos = [leer(carpeta, t, "fijo") for t in estudio.TANDAS]
            ok, plateau, estab = convergio(carpeta, base)
            notas.append(f"{n} {base}: plateau {plateau:+.2f} %, estabilidad {estab:.2f} %")
            filas.append([primera, str(base) + (" (citado)" if base == d["elegido"] else ""), str(meta["ep_elegido"]),
                          uno(meta["val_elegido"]), par(*[statistics.mean(v.values()) for v in tandas], uno),
                          par(*[estudio.comparar(v, f)["delta"] for v, f in zip(tandas, fijos)], tp.num),
                          "sí" if ok else "no"])
            primera = ""
    escribir("lima_entrenamientos.tex",
             ["Caso Lima: los tres entrenamientos del modelo completo en cada nivel de demanda. Episodio de la version",
              "evaluada (menor retraso total en la validacion, semillas 21001-21008), ese retraso, retraso total en las",
              "dos tandas de evaluacion, cambio frente al fijo ajustado al segundo y si el entrenamiento se estabilizo",
              "(regla de la tesis: en el ultimo tercio de las validaciones, tendencia y estabilidad dentro del 5 %).",
              "El citado es el de validacion mediana.",
              "fuente: politica_lima_vecinos_completo_s<base>.json (ep_elegido, val_elegido), salidas/eval_t*_*.csv y la",
              "columna val_total de resultados_lima_ippo_vecinos_completo_s<base>.csv; " + "; ".join(notas)],
             tp.tabular(f"{tp.IZQ}{{1.5cm}}{tp.IZQ}{{1.8cm}}{tp.IZQ}{{1.7cm}}{tp.IZQ}{{1.9cm}}{tp.IZQ}{{2.2cm}}"
                        f"{tp.IZQ}{{2.0cm}}{tp.IZQ}{{1.7cm}}",
                        ["Demanda", "Base", "Episodio de la versión evaluada",
                         "Retraso en la validación (s/veh)", "Retraso en la evaluación, tandas 1 y 2 (s/veh)",
                         "Cambio frente al fijo ajustado (\\%)", "¿Se estabilizó?"], filas))


ROBUSTEZ = {"reducto": "Más carga en Reducto", "transversal": "Más carga en 28 de Julio y Balboa"}


def tabla_robustez(base):
    """Prueba de robustez del reparto: los controles de la demanda publicada, sin reajustar ni reentrenar, con el
    mismo total repartido de otra forma entre las entradas (100 semillas, 24001-24100)."""
    modelo = f"completo_s{base}"
    filas = []

    def fila(nombre, lectura):
        vals = {b: lectura(b) for b in PRINCIPALES + [modelo]}
        if any(v is None for v in vals.values()):
            return None
        m = {b: statistics.mean(v.values()) for b, v in vals.items()}
        cambios = [estudio.comparar(vals[modelo], vals[ref]) for ref in ("actual", "fijo", "actuadoaj")]
        return [nombre] + [uno(m[b]) for b in PRINCIPALES + [modelo]] + [tp.num(c["delta"]) for c in cambios], cambios

    r = fila("El supuesto (tanda 1)", lambda b: leer(AQUI, 1, b))
    filas.append(r[0])
    detalle = []
    for carpeta, nombre in ROBUSTEZ.items():
        r = fila(nombre, lambda b, c=carpeta: leer(os.path.join(AQUI, "robustez", c), 1, b))
        if r is None:
            print("robustez: falta", carpeta)
            return
        filas.append(r[0])
        detalle.append(f"{carpeta}: " + "; ".join(f"{ref} {c['delta']:+.2f} [{c['ic'][0]:+.2f}, {c['ic'][1]:+.2f}] p={c['p']:.2g}"
                                                for ref, c in zip(("actual", "fijo", "actuadoaj"), r[1])))
    escribir("lima_robustez.tex",
             ["Caso Lima, prueba de robustez del reparto: retraso total (s/veh) de cada control con el mismo total",
              "(4271 veh/h) repartido de otra forma entre las entradas, sin reajustar ni reentrenar, y cambio del modelo",
              "frente a cada control (%). 100 semillas (24001-24100); la primera fila es la tanda 1 del caso.",
              "fuente: lima/robustez/<variante>/salidas/eval_t1_*.csv; IC95 y p: " + " | ".join(detalle)],
             tp.tabular(f"{tp.IZQ}{{2.6cm}}" + f"{DER}{{1.45cm}}" * 4 + f"{DER}{{1.45cm}}" * 3,
                        ["Reparto de la demanda", "Plan actual", "Fijo ajustado", "Actuado ajustado", "Modelo completo",
                         "Frente al plan actual (\\%)", "Frente al fijo (\\%)", "Frente al actuado (\\%)"], filas))


# ---------------- Figuras ----------------
def guardar(fig, nombre, plt):
    ruta = os.path.join(DESTINO["imagenes"], nombre + ".png")
    fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=tp.FONDO)
    fig.savefig(os.path.splitext(ruta)[0] + ".pdf", bbox_inches="tight", facecolor=tp.FONDO,
                metadata={"CreationDate": None})
    plt.close(fig)
    print("Escrito", ruta, "y su .pdf")


def estilo():
    return {"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.edgecolor": tp.EJE, "axes.labelcolor": tp.TINTA2,
            "xtick.color": tp.TINTA2, "ytick.color": tp.TINTA2}


def limpiar(ax):
    ax.set_facecolor(tp.FONDO)
    ax.tick_params(length=0, labelsize=7.8)
    ax.grid(axis="y", color=tp.EJE, lw=0.4, alpha=0.6, zorder=1)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def figura_retraso(datos):
    """Retraso total por vehiculo de cada control (tanda 1), un panel por nivel de demanda. Una sola serie: las
    referencias en gris y el modelo en azul; el nombre de cada barra va en el eje y el valor, sobre la barra."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    with plt.rc_context(estilo()):
        fig, ejes = plt.subplots(1, len(datos), figsize=(3.6 * len(datos), 3.4), facecolor=tp.FONDO, squeeze=False)
        for ax, (n, d) in zip(ejes[0], datos.items()):
            brazos = [b for b in PRINCIPALES if b in d["medias"][1]] + [d["modelo"]]
            nombres = [{"actual": "Plan\nactual", "fijo": "Fijo\najustado", "actuadoaj": "Actuado\najustado"}.get(b, "Modelo\ncompleto")
                       for b in brazos]
            valores = [d["medias"][1][b] for b in brazos]
            limpiar(ax)
            barras = ax.bar(range(len(brazos)), valores, width=0.5, color=[GRIS] * (len(brazos) - 1) + [AZUL], zorder=3)
            for b, v in zip(barras, valores):
                ax.annotate(uno(v), (b.get_x() + b.get_width() / 2, v), xytext=(0, 3), textcoords="offset points",
                            ha="center", va="bottom", fontsize=8.2, color=tp.TINTA)
            ax.set_ylim(0, max(valores) * 1.16)
            ax.set_xticks(range(len(brazos)))
            ax.set_xticklabels(nombres, fontsize=7.8, color=tp.TINTA, linespacing=1.25)
            ax.set_title(f"Demanda {NIVELES[n][0].lower()}: {d['veh']:.0f} veh/h", fontsize=8.4, color=tp.TINTA2, loc="left")
        ejes[0][0].set_ylabel("Retraso total (s por vehículo)", fontsize=8.2)
        fig.tight_layout(w_pad=2.0)
        guardar(fig, "fig_lima_retraso", plt)


def figura_aprendizaje(datos):
    """Retraso total en las semillas de validacion a lo largo de cada entrenamiento, con el plan actual y el fijo
    ajustado en las mismas semillas como referencia. Un panel por nivel de demanda."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    with plt.rc_context(estilo()):
        fig, ejes = plt.subplots(len(datos), 1, figsize=(6.2, 2.6 * len(datos) + 0.5), facecolor=tp.FONDO, squeeze=False)
        for ax, (n, d) in zip(ejes[:, 0], datos.items()):
            carpeta = NIVELES[n][1]
            ruta_ref = os.path.join(carpeta, "salidas", "val_referencias.json")
            referencias = leer_json(carpeta, "val_referencias.json")["retraso_total"] if os.path.exists(ruta_ref) else {}
            limpiar(ax)
            ultimo, todos = 0, []
            for base in sorted(BASES, key=lambda b: b == d["elegido"]):          # el citado se dibuja encima
                serie = serie_validacion(carpeta, base)
                xs, ys = [e for e, _ in serie], [v for _, v in serie]
                ultimo = max(ultimo, xs[-1])
                todos += ys
                if base == d["elegido"]:
                    ax.plot(xs, ys, color=AZUL, lw=2.0, zorder=4, solid_joinstyle="round")
                    k = ys.index(min(ys))                   # la version evaluada: la de menor retraso en la validacion
                    ax.plot(xs[k], ys[k], "o", ms=6.5, mfc=AZUL, mec=tp.FONDO, mew=1.4, zorder=5)
                    ax.annotate("versión evaluada", (xs[k], ys[k]), xytext=(0, -7), textcoords="offset points",
                                ha="center", va="top", fontsize=7.0, color=tp.TINTA2)
                else:
                    ax.plot(xs, ys, color=AZUL_CLARO, lw=1.2, zorder=3, solid_joinstyle="round")
            for brazo in ("actual", "fijo", "actuadoaj"):
                if brazo in referencias:
                    todos.append(referencias[brazo])
                    ax.axhline(referencias[brazo], color=GRIS, lw=1.0, zorder=2)
                    ax.annotate(f"{NOMBRE[brazo].replace(' al segundo', '')}: {referencias[brazo]:.1f}",
                                (ultimo, referencias[brazo]), xytext=(5, 0), textcoords="offset points", ha="left",
                                va="center", fontsize=7.2, color=tp.TINTA2, annotation_clip=False)
            ax.set_xlim(0, ultimo)
            # eje vertical acercado: las diferencias son de pocos segundos y con el eje desde cero no se verian
            margen = (max(todos) - min(todos)) * 0.12
            ax.set_ylim(min(todos) - margen, max(todos) + margen)
            ax.set_ylabel("Retraso total en la\nvalidación (s por vehículo)", fontsize=8.0, linespacing=1.35)
            ax.set_title(f"Demanda {NIVELES[n][0].lower()}: {d['veh']:.0f} veh/h", fontsize=8.4, color=tp.TINTA2, loc="left")
        ejes[-1, 0].set_xlabel("Episodio de entrenamiento", fontsize=8.2)
        leyenda = [Line2D([], [], color=AZUL, lw=2.0, label="Entrenamiento citado"),
                   Line2D([], [], color=AZUL_CLARO, lw=1.2, label="Los otros dos entrenamientos"),
                   Line2D([], [], color=GRIS, lw=1.0, label="Referencias, en las mismas semillas")]
        fig.legend(handles=leyenda, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.0), frameon=False, fontsize=7.6,
                   labelcolor=tp.TINTA, handlelength=1.6, columnspacing=1.6)
        fig.tight_layout(rect=(0, 0, 0.84, 1 - 0.32 / (2.6 * len(datos) + 0.5)), h_pad=1.4)
        guardar(fig, "fig_lima_aprendizaje", plt)


def figura_ciclo(datos):
    """El ciclo de cada control en barras de tiempo, un panel por nivel de demanda: verde de cada estado, ambar y
    tiempo con todo en rojo. Del modelo, el verde medio de cada estado en las semillas de validacion
    (salidas/verdes_modelo.json, que escribe estudio.py verdes-modelo)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    import programa
    colores = [AZUL, "#eb6834", "#1baf7a"]          # un color por estado con verde (validados con el fondo claro)
    claro = "#d9d8d0"
    with plt.rc_context(estilo()):
        fig, ejes = plt.subplots(len(datos), 1, figsize=(6.6, 1.5 * len(datos) + 1.0), facecolor=tp.FONDO, squeeze=False)
        largo = 0.0
        for ax, (n, d) in zip(ejes[:, 0], datos.items()):
            carpeta = NIVELES[n][1]
            filas = [("Plan actual", [v for _, v, _ in programa.PLAN]),
                     ("Fijo ajustado", leer_json(carpeta, "fijo_ajustado.json")["ganador"]),
                     ("Modelo completo\n(promedio)", leer_json(carpeta, "verdes_modelo.json")["verdes"])]
            ax.set_facecolor(tp.FONDO)
            for y, (rotulo, verdes) in zip((2, 1, 0), filas):
                x = 0.0
                for k, v in enumerate(verdes):
                    ax.barh(y, v, left=x, height=0.42, color=colores[k], edgecolor=tp.FONDO, linewidth=1.2, zorder=3)
                    ax.text(x + v / 2, y + 0.27, f"{v:.0f}", ha="center", va="bottom", fontsize=7.4, color=tp.TINTA)
                    x += v
                    ax.barh(y, programa.TRANSICION, left=x, height=0.42, color=claro, edgecolor=tp.FONDO, linewidth=1.2,
                            zorder=3)
                    x += programa.TRANSICION
                    if programa.ROJO_TOTAL.get(k):
                        r = programa.ROJO_TOTAL[k]
                        ax.barh(y, r, left=x, height=0.42, color=GRIS, edgecolor=tp.FONDO, linewidth=1.2, zorder=3)
                        ax.text(x + r / 2, y + 0.27, f"{r:.0f}", ha="center", va="bottom", fontsize=7.4, color=tp.TINTA2)
                        x += r
                ax.text(x + 2.5, y, f"ciclo de {x:.0f} s", ha="left", va="center", fontsize=7.6, color=tp.TINTA2)
                largo = max(largo, x)
            ax.set_yticks((2, 1, 0))
            ax.set_yticklabels([f[0] for f in filas], fontsize=7.8, color=tp.TINTA, linespacing=1.2)
            ax.set_ylim(-0.45, 2.75)
            ax.tick_params(length=0, labelsize=7.6)
            ax.set_title(f"Demanda {NIVELES[n][0].lower()}: {d['veh']:.0f} veh/h", fontsize=8.4, color=tp.TINTA2, loc="left")
            for s in ("top", "right", "left"):
                ax.spines[s].set_visible(False)
        for ax in ejes[:, 0]:
            ax.set_xlim(0, largo * 1.2)
        ejes[-1, 0].set_xlabel("Segundos desde el inicio del ciclo", fontsize=8.0)
        leyenda = [Patch(color=c, label=nombre) for c, (nombre, _, _) in zip(colores, programa.PLAN)]
        leyenda += [Patch(color=claro, label=f"Ámbar ({programa.TRANSICION} s)"), Patch(color=GRIS, label="Todo en rojo")]
        fig.legend(handles=leyenda, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.0), frameon=False, fontsize=7.4,
                   labelcolor=tp.TINTA, handlelength=1.1, columnspacing=1.4)
        fig.tight_layout(rect=(0, 0, 1, 1 - 0.42 / (1.5 * len(datos) + 1.0)), h_pad=1.2)
        guardar(fig, "fig_lima_ciclo", plt)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--publicada", type=int, required=True, help="base del entrenamiento citado con la demanda publicada")
    ap.add_argument("--alta", type=int, default=None, help="base del entrenamiento citado con la demanda alta")
    ap.add_argument("--destino", default=None, help="(pruebas) carpeta donde escribir todo, en vez de TESIS/")
    args = ap.parse_args()
    if args.destino:
        os.makedirs(args.destino, exist_ok=True)
        DESTINO.update(tablas=args.destino, imagenes=args.destino)
    datos = {}
    for n, base in (("publicada", args.publicada), ("alta", args.alta)):
        if base is None:
            continue
        modelo = f"completo_s{base}"
        comp, medias = comparaciones(NIVELES[n][1], modelo)
        datos[n] = {"modelo": modelo, "elegido": base, "comp": comp, "medias": medias, "veh": 4271 * NIVELES[n][2]}
    tabla_semaforo(list(datos))
    tabla_demanda()
    tabla_resultado(datos)
    tabla_completa(datos)
    tabla_entrenamientos(datos)
    tabla_robustez(args.publicada)
    figura_retraso(datos)
    figura_aprendizaje(datos)
    if all(os.path.exists(os.path.join(NIVELES[n][1], "salidas", "verdes_modelo.json")) for n in datos):
        figura_ciclo(datos)
    for n, d in datos.items():
        ok, plateau, estab = convergio(NIVELES[n][1], d["elegido"])
        for t, e in etiquetas(d["comp"]).items():
            print(f"Demanda {n}, veredicto de la tanda {t}: {e}" + ("" if ok else " (PENDIENTE: el entrenamiento citado "
                  f"no se estabilizo, plateau {plateau:+.2f} %, estabilidad {estab:.2f} %; provisional)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
