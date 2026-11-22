"""resultado_final_ovalo.py - La tabla y la figura del resultado central (resultado_final.tex y fig_resultado_final)
con el nudo en la red del Ovalo Vasco (19.11.2026, borrador de la tesis).

Es lima/corredor/tablas_corredor.py (tabla_final y figura_final), el de la copia del estudio 2 del corredor
(corredor_estudio2/), sin tocarlo (se importa sin bytecode), con dos cambios:
  - las filas del nudo salen del veredicto del estudio del ovalo (nudo_ovalo_estudio2/salidas_ovalo/
    veredicto_ovalo*.json). Encuadre final (19.11.2026): el modelo del nudo es el modelo completo (de orden fijo), como
    en los demas casos, comparado con el fijo ajustado al segundo y con el actuado ajustado (comparacion (3) del
    registro); la variante de orden libre, que el registro citaba, se informa en una nota del texto. Con --libre, las
    filas del nudo son las de la variante de orden libre (comparacion (1));
  - en la figura, un punto que caiga por encima del panel se dibuja en su borde, con una flecha y su valor (con el
    modelo completo no cae ninguno; con --libre, el nudo con la demanda alta, +55 %).
Lo demas (los seis casos del segundo estudio, el corredor de Benavides, colores, bandas y leyendas) es lo de
tablas_corredor.py. No simula.
  python -B resultado_final_ovalo.py DESTINO [--libre] [veredicto_ovalo.json | ..._publicada.json ..._alta.json]
"""
import json
import os
import sys

sys.dont_write_bytecode = True
# 20.11.2026: el corredor es el del estudio 2 (red corregida y verdes minimos de los peatones; enmienda del 19.11.2026,
# 17:35), en corredor_estudio2/. Los seis casos del segundo estudio siguen saliendo de plan3/salidas del repositorio,
# que la copia no tiene: se apunta tablas_plan3.SALIDAS ahi.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # el repositorio (este archivo esta en figuras/)
RAIZ = os.path.dirname(REPO)          # la carpeta que tiene el repositorio y las copias de los estudios (lima/estudios)
REPO_CORREDOR = os.path.join(RAIZ, "corredor_estudio2", "demo_rl", "lima", "corredor")
SALIDAS_PLAN3 = os.path.join(REPO, "plan3", "salidas")
sys.path.insert(0, REPO_CORREDOR)
import tablas_corredor as tc  # noqa: E402

tl, tp = tc.tl, tc.tp
tp.SALIDAS = SALIDAS_PLAN3
SALIDAS_OVALO = os.path.join(RAIZ, "nudo_ovalo_estudio2", "salidas_ovalo")
VEH = {"publicada": 4271, "alta": round(4271 * 1.2)}


def nudo_ovalo(rutas, brazo="completo"):
    """Los dos casos del nudo (publicada y alta), con la forma de tablas_corredor.casos_finales. brazo: "completo" (el
    modelo de orden fijo; su veredicto es el de la comparacion (3), "fijo_m") o "libre" (comparacion (1), "nudo")."""
    clave = {"completo": "fijo_m", "libre": "nudo"}[brazo]
    niveles = {}
    for ruta in rutas:
        with open(ruta, encoding="utf-8") as f:
            niveles.update(json.load(f))
    casos = []
    for n in ("publicada", "alta"):
        d = niveles[n]
        estable = d["modelos"][brazo]["estabilizado"]
        tandas = {}
        for t in (1, 2):
            T = d["tandas"][str(t)]
            f, a = T[brazo]["fijo"], T[brazo]["actuadoaj"]
            tandas[t] = {"fijo": f["delta"], "ic": tuple(f["ic"]), "veredicto": T["veredictos"][clave],
                         "pendiente": not estable, "actuado": a["delta"]}
        etiquetas = {t: tandas[t]["veredicto"] for t in (1, 2)}
        t1 = d["tandas"]["1"][brazo]["fijo"]
        caso = {"caso": "Lima", "red": "nudo", "lugar": f"Nudo, {n}", "veh": VEH[n], "fijo": t1["media_ref"],
                "modelo": t1["media"], "tandas": tandas, "veredicto": tc.etiqueta_citable(etiquetas, estable),
                "regulares": None, "veredicto_reg": None}
        citable = d["citable"][clave] + ("" if estable else " (sin estabilizar)")
        if caso["veredicto"] != citable:
            raise SystemExit(f"{n}: el veredicto recalculado ({caso['veredicto']}) no es el del estudio ({citable})")
        casos.append(caso)
    return casos


def figura_final(casos):
    """tablas_corredor.figura_final, con los puntos que caen fuera del panel dibujados en su borde."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FixedLocator, NullLocator
    menos = "−"
    x0, x1 = 1450, 13500
    rojo, pequena, clara = tp.mezcla(tp.ROJO, 0.09), tp.mezcla(tp.VERDE, 0.06), tp.mezcla(tp.VERDE, 0.15)
    LUGARES, ROTULO, fusion, palabra, miles = tc.LUGARES, tc.ROTULO, tc.fusion, tc.palabra, tc.miles

    def banda(y):
        return rojo if y > 0 else (pequena if y > tp.UMBRAL else clara)

    def marcador(ax, x, y, lugar, ver, pendiente):
        _, color, forma, tam = LUGARES[lugar]
        ms = tam + (1.2 if ver == "MEJORA" else 0)
        ax.plot(x, y, forma, ms=ms + 2.6, mfc=banda(y), mec=banda(y), mew=0, zorder=4.6)
        if ver == "EMPATA":
            ax.plot(x, y, forma, ms=tam, mfc=tp.FONDO, mec=color, mew=1.4, zorder=5)
        elif ver == "MEJORA":
            ax.plot(x, y, forma, ms=ms, fillstyle="bottom", mfc=color, markerfacecoloralt=tp.FONDO, mec=color,
                    mew=0.5, zorder=5)
        else:
            ax.plot(x, y, forma, ms=tam, mfc=color, mec=color, mew=1.0, zorder=5)
        if pendiente:
            ax.scatter([x], [y], s=(ms + 4.4) ** 2, marker=forma, facecolors="none", edgecolors=tp.TINTA,
                       linewidths=1.0, linestyle=(0, (1.2, 1.2)), zorder=5.5)

    def panel(ax, clave, y0, y1, titulo):
        ax.set_facecolor(tp.FONDO)
        ax.set_xscale("log")
        ax.axhspan(y0, tp.UMBRAL, color=clara, lw=0, zorder=0)
        ax.axhspan(tp.UMBRAL, 0, color=pequena, lw=0, zorder=0)
        ax.axhspan(0, y1, color=rojo, lw=0, zorder=0)
        ax.axhline(0, color=tp.APAGADO, lw=0.9, zorder=2)
        rot = dict(fontsize=6.9, color=tp.TINTA2, linespacing=1.25, zorder=2)
        tope = y1 - 3.5                                # donde se dibuja un punto que cae por encima del panel
        hay_fuera = any(fusion(c[clave])[0] > y1 for c in casos if c[clave] is not None)
        if y0 < tp.META:
            # el rotulo de la banda roja va a la izquierda (en tablas_corredor.py, a la derecha): a la derecha queda el
            # nudo con la demanda alta, sobre la banda, y su barra lo tocaria (hay_fuera: punto fuera de escala)
            ax.text(x0 * 1.03, y1 - 0.5, "Más retraso que el fijo: FALLA si es significativo", ha="left",
                    va="top", **rot)
            # 20.11.2026: arriba de la banda (va="top" bajo el cero) y no en su centro: el corredor de Benavides con la
            # demanda publicada (-3.7 %, 7654 veh/h) cae en el centro de la banda, justo debajo del rotulo
            ax.text(x1 / 1.03, -0.4, f"Mejora pequeña, entre {menos}5 y 0 %:\nMEJORA si es significativa",
                    ha="right", va="top", **rot)
            ax.axhline(tp.META, color=tp.TINTA2, lw=0.9, ls=(0, (1, 2.2)), zorder=2)
            ax.text(x0 * 1.03, tp.META + 0.5, f"meta de la tesis: {menos}25 %", ha="left", va="bottom", **rot)
            ax.text(x0 * 1.03, y0 + 0.6, f"Mejora clara, de {menos}5 % o más negativo: FUNCIONA si es significativa\n"
                    "y el modelo no tiene más retraso que el actuado ajustado", ha="left", va="bottom", **rot)
        for lugar, (_, color, _, _) in LUGARES.items():
            serie = sorted((c for c in casos if c["red"] == lugar and c[clave] is not None), key=lambda c: c["veh"])
            if not serie:
                continue
            puntos = [(c["veh"],) + fusion(c[clave]) + (c,) for c in serie]
            ax.plot([p[0] for p in puntos], [tope if p[1] > y1 else p[1] for p in puntos], color=color, lw=1.4, zorder=3,
                    solid_joinstyle="round", solid_capstyle="round")
            for x, y, (lo, hi), c in puntos:
                fuera = y > y1                          # solo lo que cae fuera del panel
                if not fuera:
                    ax.plot([x, x], [lo, min(hi, y1)], color=color, lw=1.1, zorder=4, solid_capstyle="butt")
                ver, pendiente = palabra(c["veredicto"] if clave == "tandas" else c["veredicto_reg"])
                yd = tope if fuera else y
                marcador(ax, x, yd, lugar, ver, pendiente)
                if fuera:                                    # flecha hacia arriba y el valor real
                    ax.annotate("", xy=(x, y1 - 0.1), xytext=(x, yd + 1.0), zorder=6,
                                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.1, shrinkA=0, shrinkB=0))
                if c["caso"] != "Lima":
                    dx, dy, lado = ROTULO[clave][c["caso"]]
                    ax.annotate(c["caso"], (x, y), xytext=(dx, dy), textcoords="offset points", ha=lado,
                                va="center", fontsize=7.6, color=tp.TINTA, fontweight="bold", zorder=6)
                elif clave == "tandas" and c is serie[0]:
                    ax.annotate({"nudo": "Nudo", "benavides": "Benavides"}[lugar], (x, yd), xytext=(-9, 0),
                                textcoords="offset points", ha="right", va="center", fontsize=7.6, color=tp.TINTA,
                                fontweight="bold", zorder=6)
                elif clave == "tandas":
                    if fuera:                                # a la izquierda: a la derecha esta el rotulo de la banda
                        ax.annotate(f"alta: {y:+.0f} %\n(fuera de escala)".replace("-", menos), (x, yd),
                                    xytext=(-10, 0), textcoords="offset points", ha="right", va="center",
                                    fontsize=7.2, color=tp.TINTA, linespacing=1.2, zorder=6)
                    else:
                        ax.annotate("alta", (x, yd), xytext=(9, 0), textcoords="offset points", ha="left",
                                    va="center", fontsize=7.2, color=tp.TINTA, zorder=6)
        ax.set_xlim(x0, x1)
        ax.xaxis.set_major_locator(FixedLocator([2000, 3000, 4000, 6000, 8000, 10000]))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xticklabels([miles(v, False) for v in (2000, 3000, 4000, 6000, 8000, 10000)], fontsize=7.4)
        ax.set_ylim(y0, y1)
        marcas = [m for m in range(-30, 11, 5) if y0 <= m <= y1]
        ax.set_yticks(marcas)
        ax.set_yticklabels([f"{t:+d}".replace("-", menos) if t else "0" for t in marcas], fontsize=7.4)
        ax.tick_params(length=0)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.set_title(titulo, fontsize=8.0, color=tp.TINTA, loc="left")
        ax.set_ylabel("Cambio del retraso total frente al\nfijo ajustado al segundo (%)", fontsize=7.6, linespacing=1.3)

    with plt.rc_context(tl.estilo()):
        fig, (arriba, abajo) = plt.subplots(2, 1, figsize=(7.0, 7.1), facecolor=tp.FONDO,
                                            gridspec_kw={"height_ratios": [2.1, 1.0], "hspace": 0.3})
        alto = 10.0 if any(fusion(c["tandas"])[0] > 6.0 for c in casos) else 6.0      # 6, como tablas_corredor.py
        panel(arriba, "tandas", -32.0, alto, "(a) Llegadas aleatorias: los seis casos del segundo estudio y los de Lima")
        panel(abajo, "regulares", -7.0, 5.0,
              "(b) Llegadas regulares: IPPO con mensajes corregido en los seis casos del segundo estudio")
        abajo.set_xlabel("Demanda total (veh/h, escala logarítmica)", fontsize=7.8)
        p = dict(ls="", ms=7.0)
        por_lugar = [Line2D([], [], marker=forma, mfc=color, mec=color, color=color, lw=1.4, ms=tam, label=nombre)
                     for nombre, color, forma, tam in LUGARES.values()]
        por_veredicto = [
            Line2D([], [], marker="o", mfc=tp.TINTA2, mec=tp.TINTA2, label="FUNCIONA o FALLA, según la banda", **p),
            Line2D([], [], marker="o", fillstyle="bottom", mfc=tp.TINTA2, markerfacecoloralt=tp.FONDO, mec=tp.TINTA2,
                   mew=0.5, label="MEJORA", **dict(p, ms=8.2)),
            Line2D([], [], marker="o", mfc=tp.FONDO, mec=tp.TINTA2, mew=1.4, label="EMPATA", **p),
            arriba.scatter([], [], s=9.6 ** 2, marker="o", facecolors="none", edgecolors=tp.TINTA, linewidths=1.0,
                           linestyle=(0, (1.2, 1.2)), label="Borde punteado: entrenamiento sin estabilizar"),
            Line2D([], [], marker="|", ms=10, mew=1.1, color=tp.TINTA2, ls="",
                   label="Barra: de un extremo a otro de los IC95 de las dos tandas")]
        comun = dict(fontsize=7.2, title_fontsize=7.4, handletextpad=0.5, alignment="left", labelcolor=tp.TINTA,
                     frameon=False)
        ley1 = fig.legend(handles=por_lugar, ncol=1, loc="upper left", bbox_to_anchor=(0.04, 1.0),
                          title="Lugar: color y forma\n(cada punto: promedio de las dos tandas)", handlelength=2.4,
                          labelspacing=0.3, **comun)
        ley2 = fig.legend(handles=por_veredicto, ncol=1, loc="upper left", bbox_to_anchor=(0.47, 1.0),
                          title="Veredicto que se repite en las dos tandas:\nrelleno del marcador", handlelength=1.6,
                          labelspacing=0.3, **comun)
        for ley in (ley1, ley2):
            ley.get_title().set_color(tp.TINTA2)
        fig.subplots_adjust(top=0.79)
        tl.guardar(fig, "fig_resultado_final", plt)


def main():
    destino = os.path.abspath(sys.argv[1])
    libre = "--libre" in sys.argv[2:]
    rutas = [a for a in sys.argv[2:] if a != "--libre"] or [os.path.join(SALIDAS_OVALO, "veredicto_ovalo.json")]
    os.makedirs(destino, exist_ok=True)
    tl.DESTINO.update(tablas=destino, imagenes=destino)
    # 20.11.2026: la tabla y la figura finales solo usan el modelo completo (casos_finales); con esto no esperan a los
    # entrenamientos de los mensajes, porque cargar() lee el meta de cada modelo de MODELOS
    tc.MODELOS = {"completo": tc.MODELOS["completo"]}
    datos = {n: tc.cargar(n) for n in ("publicada", "alta")}
    casos = tc.casos_finales(datos, {})            # sin el nudo de la red anterior
    lima = [c for c in casos if c["caso"] == "Lima"]
    sinteticos = [c for c in casos if c["caso"] != "Lima"]
    casos = sinteticos + nudo_ovalo(rutas, "libre" if libre else "completo") + lima   # el nudo antes que el corredor
    tc.tabla_final(casos)
    figura_final(casos)
    for c in casos:
        t = c["tandas"]
        print(f"{c['caso']:5s} {c['lugar']:32s} {c['veh']:6d} fijo {c['fijo']:7.2f} modelo {c['modelo']:7.2f} "
              f"{t[1]['fijo']:+7.2f} {t[2]['fijo']:+7.2f} | {t[1]['actuado']:+7.2f} {t[2]['actuado']:+7.2f} {c['veredicto']}")


if __name__ == "__main__":
    main()
