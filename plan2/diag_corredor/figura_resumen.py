"""
figura_resumen.py - Figura de la Seccion 5.5.1 (version corta pedida el 25.10.2026 con los criterios de claridad del
profesor): dos curvas en vez de cinco y el punto de 2715 veh/h sin los giros a la izquierda.

Desde plan2/:
    python diag_corredor/figura_resumen.py
Lee plan2/diag_corredor/resultados.csv (version actual y V2 frente al fijo ajustado desde 10 s, retraso total,
1001-1030; lo escribe analisis.py) y las evaluaciones del contrafactual de la Enmienda 3 (diag_corredor/eval3/: V2
entrenado en dem_corredor_t2715_der frente al fijo ajustado de ese escenario, 1001-1030, la prueba H6b; es la misma
comparacion que la de las curvas: cada escenario con su entrenamiento y su fijo ajustado). Escribe
TESIS/images/fig_diag_resumen.pdf y .png. Mismo estilo y bandas que fig_diag_corredor (analisis.figura).
"""
import os
import sys
import csv
import math

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)
import analisis as an                                     # noqa: E402

CONTROLES = ["actual", "v2"]
NOMBRE = {"actual": "Versión evaluada", "v2": "Entrenamiento corregido"}


def puntos():
    filas = list(csv.DictReader(open(os.path.join(DIR, "resultados.csv"), encoding="utf-8")))
    res = {c: [] for c in CONTROLES}
    veh = {n: v for n, _, v, _ in an.NIVELES}
    for f in filas:
        if f["control"] in CONTROLES and f["referencia"] == "fijo10" and f["semillas"] == "1001-1030":
            res[f["control"]].append((veh[f["nivel"]], float(f["cambio_total"]),
                                      (float(f["ic_lo_total"]), float(f["ic_hi_total"])), an.vd.palabra(f["veredicto_total"])))
    for c in res:
        res[c].sort()
    return res


def contrafactual():
    """2715 sin los giros a la izquierda, con el mismo protocolo que las curvas: V2 entrenado en el contrafactual
    (base mediana, analisis3.version) frente al fijo ajustado del contrafactual (prueba H6b)."""
    import analisis3
    base = analisis3.version(analisis3.D, "v2", [])["base"]
    d = an.leer_eval(os.path.join(DIR, "eval3", f"eval_d_ippo_v2d_s{base}_1001.csv"), "1001")
    ref = an.leer_eval(os.path.join(DIR, "eval3", "eval_d_fijo_1001.csv"), "1001")
    c = an.comparar(d, ref)
    return c["cambio_total"], c["ic_total"]


def figura(ruta):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from matplotlib.ticker import FixedLocator, NullLocator

    FONDO, TINTA, TINTA2, APAGADO = an.FONDO, an.TINTA, an.TINTA2, an.APAGADO
    banda_clara, banda_pequena, banda_roja = an.mezcla(an.VERDE, 0.15), an.mezcla(an.VERDE, 0.06), an.mezcla(an.ROJO, 0.09)

    def banda(y):
        return banda_roja if y > 0 else (banda_pequena if y > an.UMBRAL else banda_clara)

    pts = puntos()
    cf, cf_ic = contrafactual()
    separa = {"actual": 0.975, "v2": 1.025}
    todos = [p for s in pts.values() for p in s]
    y0 = math.floor(min([an.UMBRAL * 2, cf_ic[0]] + [p[2][0] for p in todos]) / 5) * 5 - 2
    y1 = math.ceil(max([5.0] + [p[2][1] for p in todos]) / 5) * 5 + 3
    with plt.rc_context({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.edgecolor": APAGADO,
                         "axes.labelcolor": TINTA2, "xtick.color": TINTA2, "ytick.color": TINTA2}):
        fig, ax = plt.subplots(figsize=(6.4, 4.0), facecolor=FONDO)
        ax.set_facecolor(FONDO)
        ax.set_xscale("log")
        ax.axhspan(y0, an.UMBRAL, color=banda_clara, lw=0, zorder=0)
        ax.axhspan(an.UMBRAL, 0, color=banda_pequena, lw=0, zorder=0)
        ax.axhspan(0, y1, color=banda_roja, lw=0, zorder=0)
        ax.axhline(0, color=APAGADO, lw=0.9, zorder=2)
        for control in CONTROLES:
            s = pts[control]
            color, forma, tam = an.COLOR[control], an.FORMA[control], an.TAM[control] + 0.6
            xs = [p[0] * separa[control] for p in s]
            ax.plot(xs, [p[1] for p in s], color=color, lw=1.5, ls=an.LINEA[control], zorder=3)
            for x, (_, y, ic, ver) in zip(xs, s):
                ax.plot([x, x], list(ic), color=color, lw=1.0, zorder=4, solid_capstyle="butt")
                ax.plot(x, y, forma, ms=tam + 2.4, mfc=banda(y), mec=banda(y), mew=0, zorder=4.6)
                if ver.startswith("EMPATA"):
                    ax.plot(x, y, forma, ms=tam, mfc=FONDO, mec=color, mew=1.4, zorder=5)
                elif ver.startswith("MEJORA"):
                    ax.plot(x, y, forma, ms=tam + 1.2, fillstyle="bottom", mfc=color, markerfacecoloralt=FONDO,
                            mec=color, mew=0.6, zorder=5)
                else:
                    ax.plot(x, y, forma, ms=tam, mfc=color, mec=color, mew=1.0, zorder=5)
        # 2715 sin los giros a la izquierda (entrenado y comparado en el contrafactual): estrella y flecha desde el punto real
        x_v2 = 2715 * separa["v2"]
        y_v2 = next(p[1] for p in pts["v2"] if p[0] == 2715)
        x_cf = 2715 * 1.12
        ax.annotate("", xy=(x_cf, cf), xytext=(x_v2, y_v2),
                    arrowprops=dict(arrowstyle="-|>", color=an.COLOR["v2"], lw=1.1, ls=(0, (3, 2)), shrinkA=6, shrinkB=7),
                    zorder=4)
        ax.plot([x_cf, x_cf], list(cf_ic), color=an.COLOR["v2"], lw=1.0, zorder=4)
        ax.plot(x_cf, cf, "*", ms=13, mfc=an.COLOR["v2"], mec=FONDO, mew=0.8, zorder=6)
        ax.text(x_cf / 1.045, cf - 2.2, "sin los giros a la\nizquierda", fontsize=7.2, color=an.COLOR["v2"],
                va="top", ha="right", zorder=6)
        niveles = [veh for _, _, veh, _ in an.NIVELES]
        ax.set_xlim(800, 4300)
        ax.xaxis.set_major_locator(FixedLocator(niveles))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xticklabels([n.replace(" (", "\n(") for _, n, _, _ in an.NIVELES], fontsize=7.6)
        ax.set_ylim(y0, y1)
        paso = 5 if y1 - y0 <= 60 else 10
        marcas = list(range(paso * math.ceil(y0 / paso), int(y1) + 1, paso))
        ax.set_yticks(marcas)
        ax.set_yticklabels([f"{t:+d}".replace("-", an.MENOS) if t else "0" for t in marcas], fontsize=7.8)
        ax.grid(axis="both", color=FONDO, lw=0.8, zorder=1)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        ax.set_xlabel("Demanda total del corredor (veh/h, escala logarítmica)", fontsize=8.2)
        ax.set_ylabel("Cambio del retraso total frente al\nfijo ajustado desde 10 s (%)\n"
                      "negativo = menos retraso = mejora", fontsize=8.2, linespacing=1.4)
        comun = dict(fontsize=7.3, title_fontsize=7.5, handletextpad=0.5, alignment="left", labelcolor=TINTA)
        por_control = [Line2D([], [], marker=an.FORMA[c], mfc=an.COLOR[c], mec=an.COLOR[c], color=an.COLOR[c], lw=1.5,
                              ls=an.LINEA[c], ms=an.TAM[c], label=NOMBRE[c]) for c in CONTROLES]
        por_control.append(Line2D([], [], marker="*", ms=11, mfc=an.COLOR["v2"], mec=FONDO, ls="",
                                  label="Entrenamiento corregido, 2715\nsin giros a la izquierda"))
        punto = dict(ls="", ms=6.6)
        por_veredicto = [
            Line2D([], [], marker="o", mfc=TINTA2, mec=TINTA2, label="FUNCIONA o FALLA, según la banda", **punto),
            Line2D([], [], marker="o", fillstyle="bottom", mfc=TINTA2, markerfacecoloralt=FONDO, mec=TINTA2,
                   mew=0.6, label="MEJORA", **dict(punto, ms=7.8)),
            Line2D([], [], marker="o", mfc=FONDO, mec=TINTA2, mew=1.4, label="EMPATA", **punto),
            Line2D([], [], marker="|", ms=10, mew=1.0, color=TINTA2, ls="", label="IC95 %")]
        por_banda = [
            Patch(facecolor=banda_roja, edgecolor="#e1e0d9", lw=0.6, label="Más retraso que el fijo:\nFALLA si es significativo"),
            Patch(facecolor=banda_pequena, edgecolor="#e1e0d9", lw=0.6,
                  label=f"Entre {an.MENOS}5 y 0 %:\nMEJORA si es significativa"),
            Patch(facecolor=banda_clara, edgecolor="#e1e0d9", lw=0.6,
                  label=f"{an.MENOS}5 % o menos: FUNCIONA si\nes significativa y no pierde\ncontra el actuado")]
        ley1 = ax.legend(handles=por_veredicto, loc="upper left", bbox_to_anchor=(1.01, 1.0), title="Veredicto: relleno",
                         handlelength=1.4, labelspacing=0.4, frameon=False, borderaxespad=0.0, **comun)
        ax.add_artist(ley1)
        ley2 = ax.legend(handles=por_banda, loc="upper left", bbox_to_anchor=(1.01, 0.56), title="Banda: rango del cambio",
                         handlelength=1.4, handleheight=1.6, labelspacing=0.6, frameon=False, borderaxespad=0.0, **comun)
        ax.add_artist(ley2)
        ley3 = ax.legend(handles=por_control, ncol=3, loc="lower left", bbox_to_anchor=(-0.01, 1.0),
                         title="IPPO con mensajes", handlelength=2.4, columnspacing=1.4, frameon=False,
                         borderaxespad=0.2, **comun)
        leyendas = [ley1, ley2, ley3]
        for ley in leyendas:
            ley.get_title().set_color(TINTA2)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=FONDO, bbox_extra_artists=leyendas)
        pdf = os.path.splitext(ruta)[0] + ".pdf"
        fig.savefig(pdf, bbox_inches="tight", facecolor=FONDO, bbox_extra_artists=leyendas, metadata={"CreationDate": None})
        plt.close(fig)
    print("Escrito", ruta)
    print("Escrito", pdf)
    print(f"Contrafactual 2715 (V2 entrenado sin los giros frente al fijo ajustado sin los giros, H6b): "
          f"{cf:+.1f} % IC {cf_ic}")


if __name__ == "__main__":
    figura(os.path.join(an.RAIZ, "TESIS", "images", "fig_diag_resumen.png"))
