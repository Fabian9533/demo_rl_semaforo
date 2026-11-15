"""
curvas_entrenamiento.py - Curva de aprendizaje por episodio del primer estudio (plan 2) para la tesis: retraso
(timeLoss) de cada episodio de entrenamiento de IPPO con mensajes, con su media movil de 10 episodios, el fijo ajustado
y el actuado como referencia, y debajo la entropia de la politica (cuanto explora). Es el formato de la Figura 4.11 de
la Entrega Parcial 1, que pidio el asesor el 13.11.2026.

Uso (desde demo_rl/):  python curvas_entrenamiento.py [--destino carpeta]

Lee solo lo que ya esta escrito:
  plan2/veredicto.csv                                  entrenamiento del que sale la version evaluada (base_publicada)
                                                       y retraso del actuado en la evaluacion
  plan2/evaluacion_<esc>_resumen_fijo_2509.csv         retraso del fijo ajustado en la evaluacion (timeloss_prom)
  plan2/resultados_<esc>_ippo_vecinos_s<base>.csv      timeloss_prom y entropia_libre de cada episodio
Escribe TESIS/images/fig_plan2_entrenamiento.pdf y .png. No corre ninguna simulacion.
"""
import argparse
import csv
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN2 = os.path.join(AQUI, "plan2")
sys.path.insert(0, AQUI)
import tablas_plan3 as tp

ESC = {"P1": "corredor", "P2": "corredor_alta", "P3": "red", "P4": "red_alta", "P5": "malla3", "P6": "malla3_alta"}
VENTANA = 10


def leer(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def datos():
    veredicto = leer(os.path.join(PLAN2, "veredicto.csv"))
    res = {}
    for c, esc in ESC.items():
        fila = next(r for r in veredicto if r["caso"] == c and r["modelo"] == "ippo_vecinos")
        actuado = next(r for r in veredicto if r["caso"] == c and r["modelo"] == "actuado")
        base = fila["base_publicada"]
        episodios = leer(os.path.join(PLAN2, f"resultados_{esc}_ippo_vecinos_s{base}.csv"))
        # el fijo del primer estudio es el brazo fijo_2509; donde no hay fila aparte (P1, P2 y P6) es el brazo fijo
        resumen = [r for r in leer(os.path.join(PLAN2, f"evaluacion_{esc}_resumen_fijo_2509.csv"))
                   if r["metrica"] == "timeloss_prom"]
        fijo = next((r for r in resumen if r["brazo"] == "fijo_2509"), None) or next(r for r in resumen
                                                                                     if r["brazo"] == "fijo")
        res[c] = {"base": base, "estable": fila["convergio"] == "si",
                  "ep": [int(r["episodio"]) for r in episodios],
                  "retraso": [float(r["timeloss_prom"]) for r in episodios],
                  "entropia": [float(r["entropia_libre"]) for r in episodios],
                  "fijo": float(fijo["media"]), "actuado": float(actuado["retraso"]),
                  "evaluado": float(fila["retraso"])}
    return res


def media_movil(ys, n=VENTANA):
    """Media de los ultimos n episodios (los primeros, con los que haya)."""
    return [sum(ys[max(0, i - n + 1):i + 1]) / (i + 1 - max(0, i - n + 1)) for i in range(len(ys))]


def figura(d, destino):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    azul, claro, gris, naranja = "#1f6fb2", "#a9c6e4", "#898781", "#eb6834"
    nombre = {c: f"{c}: {red}, demanda {dem} ({veh} veh/h)" for c, (red, dem, veh) in tp.CASOS.items()}
    with plt.rc_context({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.edgecolor": tp.EJE,
                         "axes.labelcolor": tp.TINTA2, "xtick.color": tp.TINTA2, "ytick.color": tp.TINTA2}):
        fig = plt.figure(figsize=(7.2, 9.0), facecolor=tp.FONDO)
        # una fila vacia entre cada caso para que el titulo no pise los numeros del eje de arriba
        rejilla = fig.add_gridspec(8, 2, height_ratios=[3, 1, 0.45, 3, 1, 0.45, 3, 1], hspace=0.12, wspace=0.28)
        for k, c in enumerate(ESC):
            fila, col = 3 * (k // 2), k % 2
            ax = fig.add_subplot(rejilla[fila, col])
            ax_e = fig.add_subplot(rejilla[fila + 1, col], sharex=ax)
            v = d[c]
            for a in (ax, ax_e):
                a.set_facecolor(tp.FONDO)
                a.tick_params(length=0, labelsize=7.0)
                a.grid(axis="y", color=tp.EJE, lw=0.4, alpha=0.6, zorder=1)
                a.set_axisbelow(True)
                for s in ("top", "right"):
                    a.spines[s].set_visible(False)
            ax.plot(v["ep"], v["retraso"], color=claro, lw=0.7, zorder=3)
            ax.plot(v["ep"], media_movil(v["retraso"]), color=azul, lw=1.8, zorder=4)
            ax.axhline(v["fijo"], color=gris, lw=1.0, zorder=2)
            ax.axhline(v["actuado"], color=gris, lw=1.0, ls=(0, (4, 2.5)), zorder=2)
            # escala: de lo mas bajo a un poco por encima de la referencia mas alta; los primeros episodios, que
            # pueden quedar muy arriba, se cortan
            refs = [v["fijo"], v["actuado"]]
            bajo = min(min(media_movil(v["retraso"])), min(refs))
            alto = max(max(refs), sorted(v["retraso"])[int(len(v["retraso"]) * 0.9)])
            margen = (alto - bajo) * 0.12
            ax.set_ylim(bajo - margen, alto + margen)
            ax.set_title(nombre[c], fontsize=7.4, color=tp.TINTA2, loc="left")
            ax_e.plot(v["ep"], v["entropia"], color=naranja, lw=1.0, zorder=3)
            ax_e.set_ylim(0, max(v["entropia"]) * 1.1)
            plt.setp(ax.get_xticklabels(), visible=False)
            if col == 0:
                ax.set_ylabel("Retraso (s/veh)", fontsize=7.2)
                ax_e.set_ylabel("Entropía", fontsize=7.2)
            if k >= 4:
                ax_e.set_xlabel("Episodio de entrenamiento", fontsize=7.4)
            ax_e.set_xlim(1, max(v["ep"]))
        leyenda = [Line2D([], [], color=claro, lw=0.9, label="Retraso de cada episodio de entrenamiento"),
                   Line2D([], [], color=azul, lw=1.8, label=f"Media móvil de {VENTANA} episodios"),
                   Line2D([], [], color=gris, lw=1.0, label="Fijo ajustado (evaluación)"),
                   Line2D([], [], color=gris, lw=1.0, ls=(0, (4, 2.5)), label="Actuado (evaluación)"),
                   Line2D([], [], color=naranja, lw=1.0, label="Entropía de la política: cuánto explora")]
        fig.legend(handles=leyenda, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 0.995), frameon=False,
                   fontsize=7.2, labelcolor=tp.TINTA, handlelength=2.0, columnspacing=1.6)
        ruta = os.path.join(destino, "fig_plan2_entrenamiento.png")
        fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=tp.FONDO)
        fig.savefig(os.path.splitext(ruta)[0] + ".pdf", bbox_inches="tight", facecolor=tp.FONDO,
                    metadata={"CreationDate": None})
        plt.close(fig)
    print("Escrito", ruta, "y su .pdf")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino", default=tp.IMAGENES)
    args = ap.parse_args()
    d = datos()
    for c, v in d.items():
        ini, fin = sum(v["retraso"][:10]) / 10, sum(v["retraso"][-10:]) / 10
        print(f"{c}: base {v['base']}, estable {v['estable']}; retraso medio de los episodios 1-10 {ini:.2f} y de los "
              f"ultimos 10 {fin:.2f}; fijo {v['fijo']:.2f}, actuado {v['actuado']:.2f}, version evaluada "
              f"{v['evaluado']:.2f}; entropia {v['entropia'][0]:.3f} -> {v['entropia'][-1]:.3f}")
    figura(d, args.destino)


if __name__ == "__main__":
    main()
