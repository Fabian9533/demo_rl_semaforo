"""ic95_lima.py - Cambio del retraso total del modelo frente al fijo ajustado al segundo y frente al actuado ajustado,
con su IC95, en las dos tandas y con las dos demandas, para un caso de Lima (20.11.2026; Fabian pidio "graficas que
indiquen el error de IC95, mostrando la comparativa").

  python -B ic95_lima.py nudo DESTINO      -> DESTINO/fig_ovalo_ic95.pdf|png: el modelo de orden fijo citado, con las
                                              comparaciones de tablas_nudo_fijo.datos (las de la Tabla D.4) y el
                                              veredicto de nudo_ovalo_estudio2/salidas_ovalo/veredicto_ovalo.json
  python -B ic95_lima.py corredor DESTINO  -> DESTINO/fig_corredor_ic95.pdf|png: el modelo completo citado, con las
                                              comparaciones de tablas_corredor.cargar (las de tab:corredor-completa)

Un caso por proceso: los dos estudios tienen modulos con el mismo nombre (estudio, tablas_lima, tablas_plan3).
Mismas funciones que las tablas (estudio.comparar: cambio %, IC95 por bootstrap pareado). No simula ni escribe en las
carpetas de los estudios; imprime cada cifra que dibuja.
"""
import json
import os
import sys

sys.dont_write_bytecode = True
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))      # la carpeta que tiene el repositorio y las copias de los estudios
CORREDOR = os.path.join(RAIZ, "corredor_estudio2", "demo_rl", "lima", "corredor")
VEREDICTO_OVALO = os.path.join(RAIZ, "nudo_ovalo_estudio2", "salidas_ovalo", "veredicto_ovalo.json")
REFS = [("fijo", "Frente al fijo\najustado al segundo"), ("actuadoaj", "Frente al actuado\najustado")]
NIVELES = [("publicada", "Demanda publicada"), ("alta", "Demanda alta")]
MENOS = "\u2212"


def datos_nudo():
    """{nivel: {"veh", "veredicto", "comp": {tanda: {ref: comparar}}}} del modelo de orden fijo citado."""
    sys.path.insert(0, AQUI)
    import tablas_nudo_fijo as tnf
    with open(VEREDICTO_OVALO, encoding="utf-8") as f:
        ver = json.load(f)
    todo = {}
    for n, _ in NIVELES:
        d = tnf.datos(tnf.NIVELES[n])
        v = ver[n]
        assert v["modelos"]["completo"]["brazo"] == d["modelo"], (v["modelos"]["completo"]["brazo"], d["modelo"])
        etiqueta = v["citable"]["fijo_m"] + ("" if v["modelos"]["completo"]["estabilizado"] else " (sin estabilizar)")
        todo[n] = {"veh": tnf.to.VEH[n], "veredicto": etiqueta, "comp": d["comp"], "modelo": d["modelo"]}
    return todo, tnf.tl, tnf.tp, "fig_ovalo_ic95"


def datos_corredor():
    sys.path.insert(0, CORREDOR)
    import tablas_corredor as tc
    todo = {}
    for n, _ in NIVELES:
        d = tc.cargar(n)
        e1, e2 = d["etiquetas"][1], d["etiquetas"][2]
        assert e1 == e2, (n, e1, e2)
        ok, _, _ = tc.convergio(d["carpeta"], "completo", d["citado"]["completo"])
        todo[n] = {"veh": d["veh"], "veredicto": e1 + ("" if ok else " (sin estabilizar)"), "comp": d["comp"],
                   "modelo": d["modelo"]}
    return todo, tc.tl, tc.tp, "fig_corredor_ic95"


def numero(v):
    return f"{v:+.1f}".replace("-", MENOS) if abs(v) >= 0.05 else "0.0"


def figura(todo, tl, tp, nombre):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import MultipleLocator

    rojo, pequena, clara = tp.mezcla(tp.ROJO, 0.09), tp.mezcla(tp.VERDE, 0.06), tp.mezcla(tp.VERDE, 0.15)
    bajos = [todo[n]["comp"][t][r]["ic"][0] for n in todo for t in (1, 2) for r, _ in REFS]
    altos = [todo[n]["comp"][t][r]["ic"][1] for n in todo for t in (1, 2) for r, _ in REFS]
    x0 = min(min(bajos) - 2.0, tp.UMBRAL - 1.5)
    x1 = max(max(altos) + 2.6, 2.0)
    with plt.rc_context(tl.estilo()):
        fig, ejes = plt.subplots(1, 2, figsize=(7.2, 2.75), facecolor=tp.FONDO, sharey=True)
        for ax, (n, titulo) in zip(ejes, NIVELES):
            d = todo[n]
            ax.set_facecolor(tp.FONDO)
            ax.axvspan(x0, tp.UMBRAL, color=clara, lw=0, zorder=0)
            ax.axvspan(tp.UMBRAL, 0, color=pequena, lw=0, zorder=0)
            ax.axvspan(0, x1, color=rojo, lw=0, zorder=0)
            ax.axvline(0, color=tp.APAGADO, lw=0.9, zorder=1)
            ax.axvline(tp.UMBRAL, color=tp.TINTA2, lw=0.8, ls=(0, (1, 2.2)), zorder=1)
            for fila, (ref, _) in enumerate(REFS):
                for t, dy, relleno in ((1, 0.16, tp.TINTA), (2, -0.16, tp.FONDO)):
                    c = d["comp"][t][ref]
                    y = len(REFS) - 1 - fila + dy
                    ax.plot(c["ic"], [y, y], color=tp.TINTA, lw=1.6, solid_capstyle="butt", zorder=3)
                    ax.plot([c["delta"]], [y], "o", ms=6.5, mfc=relleno, mec=tp.TINTA, mew=1.3, zorder=4)
                    ax.annotate(f"{numero(c['delta'])} %", (c["ic"][1], y), xytext=(5, 0), textcoords="offset points",
                                ha="left", va="center", fontsize=7.2, color=tp.TINTA, zorder=5)
                    print(f"{nombre} {n} tanda {t} frente a {ref}: {c['delta']:+.2f} [{c['ic'][0]:+.2f}, {c['ic'][1]:+.2f}]")
            ax.set_xlim(x0, x1)
            ax.xaxis.set_major_locator(MultipleLocator(5 if x1 - x0 > 15 else 2))   # sin rotulos encimados
            ax.set_ylim(-0.6, len(REFS) - 0.4)
            ax.set_yticks(range(len(REFS)))
            ax.set_yticklabels([etq for _, etq in reversed(REFS)], fontsize=7.8, color=tp.TINTA, linespacing=1.2)
            ax.tick_params(length=0, labelsize=7.6)
            for s in ("top", "right", "left"):
                ax.spines[s].set_visible(False)
            ax.set_xlabel(f"Cambio del retraso total del modelo (%)", fontsize=7.8)
            ax.set_title(f"{titulo}: {d['veh']:,.0f} veh/h".replace(",", " ") + f"\nVeredicto: {d['veredicto']}",
                         fontsize=8.2, color=tp.TINTA2, loc="left", linespacing=1.3)
        marcas = [Line2D([], [], color=tp.TINTA, lw=1.6, marker="o", ms=6.5, mfc=tp.TINTA, mec=tp.TINTA,
                         label="Tanda 1 (100 semillas): cambio medio e IC95"),
                  Line2D([], [], color=tp.TINTA, lw=1.6, marker="o", ms=6.5, mfc=tp.FONDO, mec=tp.TINTA, mew=1.3,
                         label="Tanda 2 (otras 100 semillas)"),
                  Line2D([], [], color=tp.TINTA2, lw=0.8, ls=(0, (1, 2.2)), label=f"{MENOS}5 %: umbral de la regla")]
        fig.legend(handles=marcas, loc="upper center", ncol=3, frameon=False, fontsize=7.4,
                   bbox_to_anchor=(0.5, 1.07), handlelength=2.6, columnspacing=1.6)
        fig.tight_layout(w_pad=1.6)
        tl.guardar(fig, nombre, plt)


def main():
    caso, destino = sys.argv[1], os.path.abspath(sys.argv[2])
    os.makedirs(destino, exist_ok=True)
    todo, tl, tp, nombre = datos_nudo() if caso == "nudo" else datos_corredor()
    tl.DESTINO.update(tablas=destino, imagenes=destino)
    for n in todo:
        print(n, todo[n]["modelo"], todo[n]["veredicto"])
    figura(todo, tl, tp, nombre)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
