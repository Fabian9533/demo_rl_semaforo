"""
figura_mejora_caso.py - Figura del primer estudio: cambio del retraso de IPPO con mensajes y MAPPO frente
al fijo ajustado en cada caso (P1 a P6), sobre las bandas de la regla de veredicto (fig:plan2-mejora-caso,
Cap. V).

Uso (desde demo_rl/):  python figura_mejora_caso.py [--destino carpeta] [--original]

Redibuja la figura que escribia sintesis_plan.py (figura_mejora, con --metrica timeloss_prom --fijo
fijo_2509 --sin-trivial) sin correr sintesis_plan.py ni veredicto.py: solo lee plan2/veredicto.csv, filas
de ippo_vecinos y mappo, columnas caso, modelo, delta_fijo, ic_fijo, veredicto, semaforos, carriles y
demanda_veh_h. Son los mismos valores que dibujaba sintesis_plan.py: no recalcula nada.

Cambios frente a la version del 23.10.2026 (pedido del asesor, 13.11.2026: "aca tendria que haber un
limite"):
  - lineas verticales entre los casos, para que cada caso se lea como una columna, y el nombre del caso en
    negrita bajo el eje, con sus semaforos, carriles y demanda debajo, en gris; los rotulos y los valores
    llevan el fondo de su banda, para que esas lineas no los crucen;
  - un entrenamiento que no se estabilizo ya no se dibuja como un quinto veredicto (antes, PENDIENTE: punto
    hueco): el punto lleva el color de su veredicto y un borde punteado, "entrenamiento sin estabilizar"
    (convencion de la tesis del 15.11.2026; la misma marca de las figuras del resultado central y de los
    niveles de demanda);
  - el rotulo de la banda de FUNCIONA dice "no tiene mas retraso que el actuado" (antes, "no pierde
    contra").
Con --original dibuja la version anterior, sin esos cambios (comprobacion: da el mismo PDF y el mismo PNG
que sintesis_plan.py). Escribe fig_plan2_mejora_caso.pdf (el que incluye la tesis) y .png en TESIS/images,
o en --destino.
"""
import argparse
import csv
import math
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN2 = os.path.join(AQUI, "plan2")
IMAGENES = os.path.join(AQUI, "TESIS", "images")

CASOS = ["P1", "P2", "P3", "P4", "P5", "P6"]           # veredicto.CASOS
MARCA_TRIVIAL = " (= trivial)"                         # veredicto.MARCA_TRIVIAL
FONDO, TINTA, TINTA2, APAGADO, EJE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#c3c2b7"
VERDE, VERDE_OSCURO, ROJO = "#0ca30c", "#006300", "#d03b3b"
COLOR_VEREDICTO = {"FUNCIONA": VERDE_OSCURO, "MEJORA": VERDE, "EMPATA": EJE, "FALLA": ROJO}
BORDE_VEREDICTO = {"FUNCIONA": VERDE_OSCURO, "MEJORA": VERDE, "EMPATA": APAGADO, "FALLA": ROJO}
UMBRAL = -5.0                  # veredicto.UMBRAL_DELTA
META = -25.0                   # meta de retraso de la tesis
SEPARADOR = "#a9a89f"          # lineas entre casos: mas oscuras que el eje, mas claras que el texto


def leer_csv(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def flotante(x):
    """veredicto.flotante"""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


def intervalo(texto):
    """veredicto.intervalo sobre el texto "[lo, hi]" de la columna ic_fijo."""
    numeros = re.findall(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", texto or "")
    if len(numeros) != 2:
        return None
    return (float(numeros[0]), float(numeros[1]))


def mezcla(color, alfa, fondo=FONDO):
    from matplotlib.colors import to_rgb, to_hex
    return to_hex([alfa * c + (1 - alfa) * f for c, f in zip(to_rgb(color), to_rgb(fondo))])


def color_banda(y):
    """Color de fondo de la banda de veredicto a la altura y (FUNCIONA, MEJORA o FALLA)."""
    if y < UMBRAL:
        return mezcla(VERDE, 0.15)
    return mezcla(VERDE, 0.06) if y < 0 else mezcla(ROJO, 0.09)


def veredicto_punto(texto):
    """(veredicto que da el color, sin_estabilizar). En veredicto.csv un entrenamiento sin estabilizar se
    escribe 'PENDIENTE (no convergio; provisional: X)': el color es el de X y el punto lleva el borde
    punteado."""
    texto = (texto or "").replace(MARCA_TRIVIAL, "")
    if texto.startswith("PENDIENTE"):
        prov = texto.split("provisional:")[1].strip(" )") if "provisional:" in texto else None
        return prov, True
    return texto.split(" ")[0], False


def etiquetas_casos_lineas(filas):
    etiquetas = []
    for c in CASOS:
        r = filas.get(("ippo_vecinos", c)) or {}
        sem, carr = r.get("semaforos", "?"), r.get("carriles", "?")
        etiquetas.append(f"{c}\n{sem} semáforo{'s' if sem != '1' else ''}"
                         f"\n{carr} carril{'es' if carr != '1' else ''}"
                         f"\n{r.get('demanda_veh_h', '?')} veh/h")
    return etiquetas


def figura(destino, original=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import patheffects
    from matplotlib.lines import Line2D
    filas = {(r["modelo"], r["caso"]): r for r in leer_csv(os.path.join(PLAN2, "veredicto.csv"))}
    series = (("ippo_vecinos", "o", 7.6, -0.15, "right"), ("mappo", "s", 6.6, 0.15, "left"))
    puntos, bajo, alto = [], META, 0.0
    for i, c in enumerate(CASOS):
        for m, marca, tam, dx, lado in series:
            r = filas.get((m, c))
            y = flotante(r["delta_fijo"]) if r else None
            if y is None:
                continue
            ic = intervalo(r["ic_fijo"])
            ver, pendiente = veredicto_punto(r["veredicto"])
            puntos.append((i + dx, y, ic, ver, pendiente, marca, tam, lado))
            bajo, alto = min(bajo, y, ic[0] if ic else y), max(alto, y, ic[1] if ic else y)
    y0, y1 = 5 * (bajo // 5) - 3, 5 * (alto // 5 + 1) + 3
    menos = "−"
    with plt.rc_context({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.edgecolor": EJE,
                         "axes.labelcolor": TINTA2, "xtick.color": TINTA2, "ytick.color": TINTA2}):
        fig, ax = plt.subplots(figsize=(7.2, 4.6), facecolor=FONDO)
        ax.set_facecolor(FONDO)
        x0, x1 = -0.68, len(CASOS) - 0.32
        ax.axhspan(y0, UMBRAL, color=mezcla(VERDE, 0.15), lw=0, zorder=0)
        ax.axhspan(UMBRAL, 0, color=mezcla(VERDE, 0.06), lw=0, zorder=0)
        ax.axhspan(0, y1, color=mezcla(ROJO, 0.09), lw=0, zorder=0)
        ax.grid(axis="y", color=FONDO, lw=0.8, zorder=1)
        ax.set_axisbelow(True)
        ax.axhline(0, color=APAGADO, lw=0.9, zorder=2)
        ax.axhline(META, color=TINTA2, lw=0.9, ls=(0, (1, 2.2)), zorder=2)
        if not original:
            # una linea vertical entre cada par de casos: cada caso es una columna, con sus dos modelos
            for k in range(1, len(CASOS)):
                ax.axvline(k - 0.5, color=SEPARADOR, lw=0.9, zorder=1.5)
        rotulo = dict(fontsize=7.6, color=TINTA2, linespacing=1.25, zorder=2)

        def fondo(color):
            """En la version nueva cada rotulo tapa las lineas verticales que pasan por detras."""
            return {} if original else {"bbox": dict(boxstyle="square,pad=0.2", fc=color, lw=0)}

        def halo(y):
            """En la version nueva cada valor lleva un borde del color de su banda: tapa las lineas
            verticales que lo cruzan sin tapar la banda vecina."""
            if original:
                return {}
            return {"path_effects": [patheffects.withStroke(linewidth=4.6, foreground=color_banda(y))]}

        ax.text(x0 + 0.1, y1 - 1.2, "Más retraso que el fijo (cambio positivo):\nFALLA si es significativo",
                ha="left", va="top", **rotulo, **fondo(mezcla(ROJO, 0.09)))
        ax.text(x0 + 0.1, UMBRAL / 2, f"Mejora pequeña, entre {menos}5 y 0 %:\nMEJORA si es significativa",
                ha="left", va="center", **rotulo, **fondo(mezcla(VERDE, 0.06)))
        condicion = "y no pierde contra el actuado" if original else "y no tiene más retraso\nque el actuado"
        ax.text(x1 - 0.1, (UMBRAL + META) / 2 + 2,
                f"Mejora clara, de {menos}5 % o más negativo:\nFUNCIONA si es significativa\n" + condicion,
                ha="right", va="center", **rotulo, **fondo(mezcla(VERDE, 0.15)))
        ax.text(x1 - 0.1, META + 0.6, f"meta de la tesis: {menos}25 %", ha="right", va="bottom",
                fontsize=7.6, color=TINTA2, zorder=2, **fondo(mezcla(VERDE, 0.15)))
        for x, y, ic, ver, pendiente, marca, tam, lado in puntos:
            if ic:
                ax.plot([x, x], list(ic), color=TINTA2, lw=1.3, zorder=3, solid_capstyle="butt")
            if pendiente and original:
                estilo = dict(mfc=FONDO, mec=BORDE_VEREDICTO.get(ver, TINTA2), mew=1.9)
            else:
                estilo = dict(mfc=COLOR_VEREDICTO.get(ver, EJE), mec=APAGADO if ver == "EMPATA" else FONDO,
                              mew=1.0 if ver == "EMPATA" else 1.2)
            ax.plot(x, y, marca, ms=tam, zorder=5, **estilo)
            if pendiente and not original:
                # entrenamiento sin estabilizar: el punto lleva el color de su veredicto y, alrededor, un
                # borde punteado (la misma marca que en las figuras del resultado central y de los niveles
                # de demanda)
                ax.scatter([x], [y], s=(tam + 4.4) ** 2, marker=marca, facecolors="none", edgecolors=TINTA,
                           linewidths=1.0, linestyle=(0, (1.2, 1.2)), zorder=5.5)
            izq = lado == "right"
            dx = 9.5 if (pendiente and not original) else 7     # el valor no toca el borde punteado
            ax.annotate(f"{y:+.1f}".replace("-", menos), (x, y), xytext=(-dx if izq else dx, 0),
                        textcoords="offset points", ha=lado, va="center", fontsize=7.6, color=TINTA,
                        zorder=6, **halo(y))
        ax.set_ylim(y0, y1)
        marcas = list(range(int(5 * -(-y0 // 5)), int(y1) + 1, 5))
        ax.set_yticks(marcas)
        ax.set_yticklabels([f"{t:+d}".replace("-", menos) if t else "0" for t in marcas], fontsize=7.8)
        ax.set_xticks(range(len(CASOS)))
        etiquetas = etiquetas_casos_lineas(filas)
        if original:
            ax.set_xticklabels(etiquetas, fontsize=7.6, color=TINTA2, linespacing=1.3)
        else:
            # el nombre del caso va en negrita y en tinta; debajo, en gris, semaforos, carriles y demanda
            ax.set_xticklabels([e.split("\n", 1)[1] for e in etiquetas], fontsize=7.6, color=TINTA2,
                               linespacing=1.3)
            ax.tick_params(axis="x", pad=15)
            for i, c in enumerate(CASOS):
                ax.annotate(c, (i, 0), xycoords=("data", "axes fraction"), xytext=(0, -4),
                            textcoords="offset points", ha="center", va="top", fontsize=8.4,
                            fontweight="bold", color=TINTA)
        ax.set_xlim(x0, x1)
        ax.tick_params(length=0)
        ax.set_ylabel("Cambio del retraso frente al fijo ajustado (%)\nnegativo = menos retraso = mejora",
                      fontsize=8.2, linespacing=1.4)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        punto = dict(ls="", ms=7.2)
        por_veredicto = [Line2D([], [], marker="o", mfc=COLOR_VEREDICTO[v],
                                mec=APAGADO if v == "EMPATA" else FONDO, label=v, **punto)
                         for v in ("FUNCIONA", "MEJORA", "EMPATA", "FALLA")]
        if original:
            antes = "PENDIENTE: hueco, con el borde\ndel color de su veredicto provisional"
            por_veredicto.append(Line2D([], [], marker="o", mfc=FONDO, mec=TINTA2, mew=1.6, **punto,
                                        label=antes))
        else:
            por_veredicto.append(ax.scatter([], [], s=9.6 ** 2, marker="o", facecolors="none",
                                            edgecolors=TINTA, linewidths=1.0, linestyle=(0, (1.2, 1.2)),
                                            label="Borde punteado: entrenamiento\nsin estabilizar"))
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
        ruta = os.path.join(destino, "fig_plan2_mejora_caso.png")
        fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=FONDO)
        pdf = os.path.splitext(ruta)[0] + ".pdf"
        fig.savefig(pdf, bbox_inches="tight", facecolor=FONDO, metadata={"CreationDate": None})
        plt.close(fig)
    print("Escrito", ruta)
    print("Escrito", pdf)


def main():
    global PLAN2
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino", default=IMAGENES)
    ap.add_argument("--plan2", default=PLAN2, help="carpeta de veredicto.csv (por defecto, demo_rl/plan2)")
    ap.add_argument("--original", action="store_true", help="la version del 23.10.2026, sin los cambios")
    args = ap.parse_args()
    PLAN2 = args.plan2
    figura(args.destino, args.original)


if __name__ == "__main__":
    main()
