"""
grafico_convergencia.py - Curvas de validacion del plan de pruebas v2 (convergencia por caso).

Uso (desde demo_rl/plan2):  python grafico_convergencia.py
Salida: fig_plan2_convergencia.png

Un panel por caso (P1-P5). En cada uno, la curva de validacion de la politica publicada (base
mediana, veredicto_congelado_0355.csv) de IPPO vecinos, MAPPO, DQN y Q-learning: retraso medio
de las semillas 999 y 1999 cada 10 episodios, leido del val_serie de su meta. Linea gris
discontinua: el fijo tuneado de la celda en esas mismas dos semillas (fijo_validacion.json).
Banda sombreada: el ultimo tercio del entrenamiento, donde se mide si la curva se estabilizo.
"""
import csv
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
CASOS = [("P1", "corredor", "P1  corredor"), ("P2", "corredor_alta", "P2  corredor saturado"),
         ("P3", "red", "P3  red con rotonda"), ("P4", "red_alta", "P4  red, demanda alta"),
         ("P5", "malla3", "P5  malla 3x3")]
# alg -> (nombre, color categorico en orden fijo, patron del archivo de meta)
MODELOS = [("ippo_vecinos", "IPPO vecinos", "#2a78d6", "politica_{e}_vecinos_s{b}.json"),
           ("mappo", "MAPPO", "#eb6834", "politica_{e}_mappo_s{b}.json"),
           ("dqn", "DQN", "#1baf7a", "politica_{e}_dqn_s{b}.json"),
           ("ql", "Q-learning", "#eda100", "q_table_{e}_ql_s{b}.meta.json")]
TINTA, TINTA2, APAGADO = "#0b0b0b", "#52514e", "#898781"
GRILLA, EJE, FONDO = "#e1e0d9", "#c3c2b7", "#fcfcfb"


def leer():
    with open(os.path.join(AQUI, "veredicto_congelado_0355.csv"), encoding="utf-8") as f:
        ver = {(r["caso"], r["modelo"]): r for r in csv.DictReader(f)}
    with open(os.path.join(AQUI, "fijo_validacion.json"), encoding="utf-8") as f:
        fijo = json.load(f)
    return ver, fijo


def serie(esc, patron, base):
    ruta = os.path.join(AQUI, patron.format(e=esc, b=base))
    if not base or not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8") as f:
        meta = json.load(f)
    s = meta.get("val_serie") or []
    return [x[0] for x in s], [x[3] for x in s], meta.get("ep_elegido"), meta.get("val_elegido")


def separar(ys, minimo):
    """Posiciones de etiqueta sin solaparse: orden por y y separacion minima."""
    orden = sorted(range(len(ys)), key=lambda i: ys[i])
    pos = [0.0] * len(ys)
    ultimo = None
    for i in orden:
        y = ys[i] if ultimo is None else max(ys[i], ultimo + minimo)
        pos[i] = ultimo = y
    return pos


def main():
    ver, fijo = leer()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": EJE,
                         "axes.labelcolor": TINTA2, "xtick.color": APAGADO, "ytick.color": APAGADO})
    fig, ejes = plt.subplots(3, 2, figsize=(7.6, 8.4), dpi=200, facecolor=FONDO)
    ejes = ejes.ravel()
    for k, (caso, esc, titulo) in enumerate(CASOS):
        ax = ejes[k]
        ax.set_facecolor(FONDO)
        ax.axvspan(200 * 2 / 3, 200, color="#efeee9", zorder=0, lw=0)
        ref = (fijo[f"{esc}_999"] + fijo[f"{esc}_1999"]) / 2
        ax.axhline(ref, color=APAGADO, lw=1.1, ls=(0, (4, 3)), zorder=1)
        finales, etiquetas, colores = [], [], []
        todos = [ref]
        for alg, nombre, color, patron in MODELOS:
            fila = ver.get((caso, alg))
            s = serie(esc, patron, fila["base_publicada"] if fila else "")
            if not s:
                continue
            xs, ys, ep_pub, val_pub = s
            todos += ys
            ax.plot(xs, ys, color=color, lw=1.6, zorder=3, solid_capstyle="round")
            ax.plot(xs, ys, "o", ms=2.6, color=color, mec=FONDO, mew=0.6, zorder=4)
            if ep_pub is not None and val_pub is not None:
                ax.plot([ep_pub], [val_pub], "o", ms=7, color=color, mec=TINTA, mew=1.0, zorder=5)
            conv = "" if fila["convergio"] == "si" else " (no conv.)"
            finales.append(ys[-1]); etiquetas.append(nombre + conv); colores.append(color)
        bajo, alto = min(todos), max(todos)
        margen = (alto - bajo) * 0.08 or 1
        ax.set_ylim(bajo - margen, alto + margen)
        pos = separar(finales, (alto - bajo + 2 * margen) * 0.075)
        for y0, y, txt, c in zip(finales, pos, etiquetas, colores):
            ax.plot([200, 204], [y0, y], color=c, lw=0.8, zorder=2, clip_on=False)
            ax.text(206, y, txt, color=TINTA2, fontsize=7.2, va="center", clip_on=False)
        ax.set_title(titulo, loc="left", fontsize=9.5, color=TINTA, fontweight="bold", pad=6)
        ax.set_xlim(0, 200)
        ax.set_xticks([0, 50, 100, 150, 200])
        ax.grid(axis="y", color=GRILLA, lw=0.6)
        ax.tick_params(length=0)
        for lado in ("top", "right", "left"):
            ax.spines[lado].set_visible(False)
        if k % 2 == 0:
            ax.set_ylabel("retraso en validación (s/veh)")
        if k >= 3:
            ax.set_xlabel("episodio de entrenamiento")
    leyenda = ejes[5]
    leyenda.axis("off")
    for i, (alg, nombre, color, _) in enumerate(MODELOS):
        leyenda.plot([0.02, 0.14], [0.86 - i * 0.1] * 2, color=color, lw=1.8, transform=leyenda.transAxes)
        leyenda.text(0.18, 0.86 - i * 0.1, nombre, color=TINTA2, va="center", transform=leyenda.transAxes)
    leyenda.plot([0.02, 0.14], [0.46] * 2, color=APAGADO, lw=1.1, ls=(0, (4, 3)), transform=leyenda.transAxes)
    leyenda.text(0.18, 0.46, "fijo tuneado, mismas semillas", color=TINTA2, va="center",
                 transform=leyenda.transAxes)
    leyenda.plot([0.08], [0.37], "o", ms=7, color="#ffffff", mec=TINTA, mew=1.0, transform=leyenda.transAxes)
    leyenda.text(0.18, 0.37, "checkpoint publicado (el que se evalúa)", color=TINTA2, va="center",
                 transform=leyenda.transAxes)
    leyenda.add_patch(plt.Rectangle((0.02, 0.20), 0.12, 0.06, color="#efeee9", transform=leyenda.transAxes))
    leyenda.text(0.18, 0.23, "último tercio: se mide" + chr(10) + "si la curva se estabilizó", color=TINTA2,
                 va="center", transform=leyenda.transAxes)
    leyenda.text(0.02, 0.03, "Política publicada de cada modelo (base mediana).\n"
                 "Validación: semillas 999 y 1999, cada 10 episodios.\n"
                 "Cada panel tiene su propia escala vertical.", color=APAGADO, fontsize=7,
                 va="center", transform=leyenda.transAxes)
    fig.suptitle("Curvas de aprendizaje del plan de pruebas v2", x=0.02, ha="left",
                 fontsize=11, color=TINTA, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 0.9, 0.97), h_pad=2.2, w_pad=5.5)
    salida = os.path.join(AQUI, "fig_plan2_convergencia.png")
    fig.savefig(salida, facecolor=FONDO)
    print("escrito", salida)


if __name__ == "__main__":
    main()
