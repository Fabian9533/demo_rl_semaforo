"""figuras_ovalo_tesis.py - Dos figuras del nudo para la tesis, redibujadas con los datos y el estilo de
nudo_ovalo_estudio2/tablas_ovalo.py (colores y formato de lima/tablas_lima.py), sin tocar esa carpeta
(19.11.2026, borrador de la tesis):

  fig_ovalo_aprendizaje.pdf|png  las curvas de aprendizaje de tablas_ovalo.figura_aprendizaje, legibles: en la de
                                 tablas_ovalo.py la primera validacion del orden libre con la demanda publicada
                                 (1210 s/veh en el episodio 20) estira el eje hasta 1200 y aplasta el rango util
                                 (75-100), y los rotulos de las referencias se pisan (las tres de la publicada;
                                 "Actuado ajustado: 147.1" y "Fijo ajustado al segundo: 125.8" con la alta). Aqui:
                                  - el eje vertical muestra el rango util: lo que toman las curvas desde el episodio
                                    100 y las tres referencias, con un margen;
                                  - cada validacion que queda por encima de ese rango se marca en el borde de arriba
                                    con un triangulo del color de su curva, y una nota da sus valores;
                                  - los rotulos de las referencias se separan si quedan a menos de un renglon;
                                  - como en las demas curvas de la tesis (fig:plan3-aprendizaje), un punto con borde
                                    negro marca la version evaluada de cada modelo citado, hueco si su entrenamiento no
                                    se estabilizo.
  fig_ovalo_ciclo.pdf|png        la de tablas_lima.figura_ciclo, con el rotulo "Modelo de orden fijo (promedio)": alli
                                 dice "Modelo completo"; en el nudo la tesis lo llama modelo de orden fijo.

No simula ni escribe en nudo_ovalo_estudio2/ (se importa sin bytecode). Lee:
  demo_rl/lima/ y demo_rl/lima/alta/: resultados_lima_ippo_vecinos_<libre|completo>_s<base>.csv (columna val_total),
  politica_lima_vecinos_<etiqueta>_s<base>.json (val_elegido y ep_elegido), salidas/val_referencias.json,
  salidas/fijo_ajustado.json y salidas/verdes_modelo.json.
Uso: python -B figuras_ovalo_tesis.py DESTINO
"""
import json
import os
import sys

sys.dont_write_bytecode = True
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # con el repositorio y los estudios
EST = os.path.join(RAIZ, "nudo_ovalo_estudio2")
sys.path.insert(0, EST)
import tablas_ovalo as to  # noqa: E402

tl, tp = to.tl, to.tp
NIVELES = {"publicada": to.LIMA, "alta": os.path.join(to.LIMA, "alta")}
DESDE = 100        # episodio desde el que se fija la escala vertical (antes, las validaciones pueden quedar arriba)
MARGEN = 0.07      # margen arriba y abajo, como fraccion del rango util
REFERENCIAS = ("actual", "fijo", "actuadoaj")


def citados():
    return {n: {e: to.citada(c, e) for e in to.MODELOS} for n, c in NIVELES.items()}


def meta(carpeta, etiqueta, base):
    with open(os.path.join(carpeta, f"politica_lima_vecinos_{etiqueta}_s{base}.json"), encoding="utf-8") as f:
        return json.load(f)


def separar(ys, minimo):
    """Posiciones de los rotulos: las mismas ys, separadas al menos `minimo` (en unidades del eje), en su orden."""
    orden = sorted(range(len(ys)), key=lambda i: ys[i])
    pos = [ys[i] for i in orden]
    for k in range(1, len(pos)):
        if pos[k] - pos[k - 1] < minimo:
            pos[k] = pos[k - 1] + minimo
    salida = [0.0] * len(ys)
    for k, i in enumerate(orden):
        salida[i] = pos[k]
    return salida


def figura_aprendizaje(cit):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    colores = {"libre": (tl.AZUL, tl.AZUL_CLARO), "completo": (to.NARANJA, to.NARANJA_CLARO)}
    alto_panel = 2.55
    with plt.rc_context(tl.estilo()):
        fig, ejes = plt.subplots(len(NIVELES), 1, figsize=(6.4, alto_panel * len(NIVELES) + 0.75),
                                 facecolor=tp.FONDO, squeeze=False)
        for ax, (n, carpeta) in zip(ejes[:, 0], NIVELES.items()):
            referencias = tl.leer_json(carpeta, "val_referencias.json")["retraso_total"]
            series = {(e, b): to.serie(carpeta, e, b) for e in colores for b in to.BASES}
            util = [v for s in series.values() for ep, v in s if ep >= DESDE] + [referencias[r] for r in REFERENCIAS]
            lo, hi = min(util), max(util)
            y0, y1 = lo - (hi - lo) * MARGEN, hi + (hi - lo) * MARGEN
            tl.limpiar(ax)
            ultimo = max(s[-1][0] for s in series.values())
            fuera = []
            for etiqueta, (fuerte, claro) in colores.items():
                for base in sorted(to.BASES, key=lambda b: b == cit[n][etiqueta]):     # el citado, encima
                    s = series[(etiqueta, base)]
                    es = base == cit[n][etiqueta]
                    color = fuerte if es else claro
                    ax.plot([e for e, _ in s], [v for _, v in s], color=color, lw=2.0 if es else 1.0,
                            zorder=4 if es else 3, solid_joinstyle="round", clip_on=True)
                    for ep, v in s:
                        if v > y1:
                            fuera.append(v)
                            ax.plot(ep, y1 - (y1 - y0) * 0.012, marker="^", ms=6.0 if es else 4.6, mfc=color,
                                    mec=tp.FONDO, mew=0.8, zorder=6 if es else 5, clip_on=False)
                    if es:                                       # la version evaluada del modelo citado
                        m = meta(carpeta, etiqueta, base)
                        estable = to.convergio(carpeta, etiqueta, base)[0]
                        ax.plot(m["ep_elegido"], m["val_elegido"], marker="o", ms=6.6,
                                mfc=fuerte if estable else tp.FONDO, mec=tp.TINTA, mew=1.0, zorder=7)
            ys = [referencias[r] for r in REFERENCIAS]
            for r, y, yr in zip(REFERENCIAS, ys, separar(ys, (y1 - y0) * 0.085)):
                ax.axhline(y, color=tl.GRIS, lw=1.0, zorder=2)
                ax.annotate(f"{tl.NOMBRE[r]}: {y:.1f}", (ultimo, yr), xytext=(6, 0), textcoords="offset points",
                            ha="left", va="center", fontsize=7.2, color=tp.TINTA2, annotation_clip=False)
            if fuera:                                            # la nota, entre el titulo y el panel
                ax.text(0.0, 1.012, f"\u25B2 en el borde de arriba: {len(fuera)} validaciones de los primeros "
                        f"episodios, fuera de la escala (de {min(fuera):.0f} a {max(fuera):.0f} s/veh)",
                        transform=ax.transAxes, ha="left", va="bottom", fontsize=6.8, color=tp.TINTA2)
            ax.set_xlim(0, max(1, ultimo))
            ax.set_ylim(y0, y1)
            ax.set_ylabel("Retraso total en la\nvalidación (s por vehículo)", fontsize=8.0, linespacing=1.35)
            ax.set_title(f"Demanda {n}: {to.VEH[n]:.0f} veh/h", fontsize=8.4, color=tp.TINTA2, loc="left", pad=15)
        ejes[-1, 0].set_xlabel("Episodio de entrenamiento", fontsize=8.2)
        leyenda = [Line2D([], [], color=to.NARANJA, lw=2.0, label="Orden fijo, citado"),
                   Line2D([], [], color=tl.AZUL, lw=2.0, label="Orden libre, citado"),
                   Line2D([], [], color=to.NARANJA_CLARO, lw=1.0, label="Orden fijo, otras bases"),
                   Line2D([], [], color=tl.AZUL_CLARO, lw=1.0, label="Orden libre, otras bases"),
                   Line2D([], [], color=tl.GRIS, lw=1.0, label="Referencias, mismas semillas"),
                   Line2D([], [], ls="", marker="o", ms=6.6, mfc=tp.TINTA2, mec=tp.TINTA, mew=1.0,
                          label="Versión evaluada (hueco: sin estabilizar)")]
        fig.legend(handles=leyenda, ncol=3, loc="upper center", bbox_to_anchor=(0.47, 1.0), frameon=False,
                   fontsize=7.3, labelcolor=tp.TINTA, handlelength=1.6, columnspacing=1.4)
        fig.tight_layout(rect=(0, 0, 0.79, 1 - 0.55 / (alto_panel * len(NIVELES) + 0.75)), h_pad=1.6)
        tl.guardar(fig, "fig_ovalo_aprendizaje", plt)


def figura_ciclo(cit):
    """tablas_lima.figura_ciclo con el modelo de orden fijo citado de cada nivel y su nombre en la tesis."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    import programa
    colores = [tl.AZUL, "#eb6834", "#1baf7a"]
    claro = "#d9d8d0"
    with plt.rc_context(tl.estilo()):
        fig, ejes = plt.subplots(len(NIVELES), 1, figsize=(6.6, 1.5 * len(NIVELES) + 1.0), facecolor=tp.FONDO,
                                 squeeze=False)
        largo = 0.0
        for ax, (n, carpeta) in zip(ejes[:, 0], NIVELES.items()):
            verdes = tl.leer_json(carpeta, "verdes_modelo.json")
            esperada = f"politica_lima_vecinos_completo_s{cit[n]['completo']}.pt"
            if verdes["politica"] != esperada:
                raise SystemExit(f"verdes_modelo.json de {n} es de {verdes['politica']}, no del citado {esperada}")
            filas = [("Plan actual", [v for _, v, _ in programa.PLAN]),
                     ("Fijo ajustado\nal segundo", tl.leer_json(carpeta, "fijo_ajustado.json")["ganador"]),
                     ("Modelo de orden\nfijo (promedio)", verdes["verdes"])]
            ax.set_facecolor(tp.FONDO)
            for y, (rotulo, vs) in zip((2, 1, 0), filas):
                x = 0.0
                for k, v in enumerate(vs):
                    ax.barh(y, v, left=x, height=0.42, color=colores[k], edgecolor=tp.FONDO, linewidth=1.2, zorder=3)
                    ax.text(x + v / 2, y + 0.27, f"{v:.0f}", ha="center", va="bottom", fontsize=7.4, color=tp.TINTA)
                    x += v
                    ax.barh(y, programa.TRANSICION, left=x, height=0.42, color=claro, edgecolor=tp.FONDO, linewidth=1.2,
                            zorder=3)
                    x += programa.TRANSICION
                    if programa.ROJO_TOTAL.get(k):
                        r = programa.ROJO_TOTAL[k]
                        ax.barh(y, r, left=x, height=0.42, color=tl.GRIS, edgecolor=tp.FONDO, linewidth=1.2, zorder=3)
                        ax.text(x + r / 2, y + 0.27, f"{r:.0f}", ha="center", va="bottom", fontsize=7.4,
                                color=tp.TINTA2)
                        x += r
                ax.text(x + 2.5, y, f"ciclo de {x:.0f} s", ha="left", va="center", fontsize=7.6, color=tp.TINTA2)
                largo = max(largo, x)
            ax.set_yticks((2, 1, 0))
            ax.set_yticklabels([f[0] for f in filas], fontsize=7.8, color=tp.TINTA, linespacing=1.2)
            ax.set_ylim(-0.45, 2.75)
            ax.tick_params(length=0, labelsize=7.6)
            ax.set_title(f"Demanda {n}: {to.VEH[n]:.0f} veh/h", fontsize=8.4, color=tp.TINTA2, loc="left")
            for s in ("top", "right", "left"):
                ax.spines[s].set_visible(False)
        for ax in ejes[:, 0]:
            ax.set_xlim(0, largo * 1.2)
        ejes[-1, 0].set_xlabel("Segundos desde el inicio del ciclo", fontsize=8.0)
        leyenda = [Patch(color=c, label=nombre) for c, (nombre, _, _) in zip(colores, programa.PLAN)]
        leyenda += [Patch(color=claro, label=f"Ámbar ({programa.TRANSICION} s)"), Patch(color=tl.GRIS, label="Todo en rojo")]
        fig.legend(handles=leyenda, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.0), frameon=False, fontsize=7.4,
                   labelcolor=tp.TINTA, handlelength=1.1, columnspacing=1.4)
        fig.tight_layout(rect=(0, 0, 1, 1 - 0.42 / (1.5 * len(NIVELES) + 1.0)), h_pad=1.2)
        tl.guardar(fig, "fig_ovalo_ciclo", plt)


def main():
    destino = os.path.abspath(sys.argv[1])
    os.makedirs(destino, exist_ok=True)
    tl.DESTINO.update(tablas=destino, imagenes=destino)
    cit = citados()
    print("citados", cit)
    figura_aprendizaje(cit)
    figura_ciclo(cit)


if __name__ == "__main__":
    main()
