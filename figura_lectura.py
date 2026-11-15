"""
figura_lectura.py - Figura explicativa del Capitulo V (pedido del asesor, 13.11.2026): que son las llegadas regulares y
las aleatorias, y como se lee un veredicto (FUNCIONA, MEJORA, EMPATA, FALLA y PENDIENTE). Es una ilustracion: no
muestra resultados.

Uso (desde demo_rl/):  python figura_lectura.py [--destino carpeta]
Escribe TESIS/images/fig_lectura.pdf y .png.

(a) Dos minutos de una entrada con 600 veh/h: con llegadas regulares entra un vehiculo cada 6 s; con llegadas
    aleatorias (proceso de Poisson, la misma media) el intervalo cambia: a veces llegan seguidos y a veces pasa mas
    tiempo sin ninguno. La semilla del dibujo es fija (7).
(b) Cinco casos inventados sobre las bandas de la regla de veredicto, con su IC95 y la regla en palabras.
"""
import argparse
import os
import sys

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import tablas_plan3 as tp

MENOS = "−"


def llegadas_aleatorias(media_s, duracion_s, semilla=7):
    rng = np.random.default_rng(semilla)
    t, res = 0.0, []
    while True:
        t += rng.exponential(media_s)
        if t > duracion_s:
            return res
        res.append(t)


def figura(destino):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    azul, gris = "#1f6fb2", "#898781"
    duracion, media = 120, 6.0
    regulares = np.arange(3, duracion, media)
    aleatorias = llegadas_aleatorias(media, duracion)
    with plt.rc_context({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.edgecolor": tp.EJE,
                         "axes.labelcolor": tp.TINTA2, "xtick.color": tp.TINTA2, "ytick.color": tp.TINTA2}):
        # el panel (b) deja a su derecha el espacio de la regla en palabras: asi el ancho total es el de la pagina
        fig = plt.figure(figsize=(7.0, 6.6), facecolor=tp.FONDO)
        a = fig.add_axes([0.17, 0.70, 0.80, 0.22])
        b = fig.add_axes([0.17, 0.08, 0.47, 0.48])
        # (a) llegadas
        a.set_facecolor(tp.FONDO)
        for y, tiempos, nombre in ((1, regulares, "Regulares"), (0, aleatorias, "Aleatorias")):
            a.plot([0, duracion], [y, y], color=tp.EJE, lw=0.8, zorder=1)
            a.plot(tiempos, [y] * len(tiempos), "s", ms=5.2, mfc=azul, mec=azul, zorder=3)
            a.text(-3, y, f"{nombre}\n({len(tiempos)} vehículos)", ha="right", va="center", fontsize=7.4,
                   color=tp.TINTA, linespacing=1.2)
        a.text(duracion / 2, 1.42, "Un vehículo cada 6 s, siempre", ha="center", va="bottom", fontsize=7.2,
               color=tp.TINTA2)
        a.text(duracion / 2, -0.42, "En promedio, uno cada 6 s: a veces llegan seguidos y a veces pasa más tiempo "
               "sin ninguno", ha="center", va="top", fontsize=7.2, color=tp.TINTA2)
        a.set_xlim(-1, duracion + 1)
        a.set_ylim(-0.9, 1.9)
        a.set_yticks([])
        a.set_xticks(range(0, duracion + 1, 20))
        a.tick_params(length=0, labelsize=7.2)
        a.set_xlabel("Tiempo (s): dos minutos de una entrada con 600 veh/h", fontsize=7.6)
        for s in ("top", "right", "left"):
            a.spines[s].set_visible(False)
        a.set_title("(a) Llegadas regulares y aleatorias, con la misma demanda", fontsize=8.2, color=tp.TINTA,
                    loc="left", pad=14)
        # (b) veredictos
        b.set_facecolor(tp.FONDO)
        y0, y1 = -14.0, 6.0
        b.axvspan(y0, tp.UMBRAL, color=tp.mezcla(tp.VERDE, 0.15), lw=0, zorder=0)
        b.axvspan(tp.UMBRAL, 0, color=tp.mezcla(tp.VERDE, 0.06), lw=0, zorder=0)
        b.axvspan(0, y1, color=tp.mezcla(tp.ROJO, 0.09), lw=0, zorder=0)
        b.axvline(0, color=tp.APAGADO, lw=0.9, zorder=2)
        b.axvline(tp.UMBRAL, color=tp.APAGADO, lw=0.6, ls=(0, (3, 2)), zorder=2)
        casos = [  # (veredicto, cambio, IC95, regla en palabras)
            ("FUNCIONA", -9.0, (-10.4, -7.6), "baja el retraso un 5 % o más, con el\nIC95 entero bajo cero, y no "
             "pierde\ncontra el actuado"),
            ("MEJORA", -2.8, (-3.9, -1.7), "IC95 entero bajo cero, pero la baja\nes menor del 5 % o el modelo "
             "pierde\ncontra el actuado"),
            ("EMPATA", 0.4, (-1.1, 1.9), "el IC95 cruza el cero: no se\ndistingue del fijo"),
            ("FALLA", 2.9, (1.9, 3.9), "IC95 entero sobre cero: más\nretraso que el fijo"),
            ("PENDIENTE", -7.0, (-8.6, -5.4), "el entrenamiento no se estabilizó:\nel veredicto (aquí, FUNCIONA) "
             "es\nprovisional"),
        ]
        for k, (ver, x, ic, regla) in enumerate(casos):
            y = len(casos) - 1 - k
            b.plot(list(ic), [y, y], color=tp.TINTA2, lw=1.4, zorder=3, solid_capstyle="butt")
            if ver == "PENDIENTE":
                b.plot(x, y, "o", ms=8, mfc=tp.FONDO, mec=tp.VERDE_OSCURO, mew=1.8, zorder=5)
            else:
                b.plot(x, y, "o", ms=8, mfc=tp.COLOR[ver], mec=tp.APAGADO if ver == "EMPATA" else tp.FONDO,
                       mew=1.0, zorder=5)
            b.text(y1 + 0.4, y, regla, ha="left", va="center", fontsize=7.0, color=tp.TINTA2, linespacing=1.2,
                   clip_on=False)
        b.set_yticks(range(len(casos)))
        b.set_yticklabels([v for v, _, _, _ in reversed(casos)], fontsize=7.6, color=tp.TINTA)
        b.set_xlim(y0, y1)
        b.set_ylim(-0.7, len(casos) - 0.3)
        marcas = list(range(-12, 7, 3))
        b.set_xticks(marcas)
        b.set_xticklabels([f"{t:+d}".replace("-", MENOS) if t else "0" for t in marcas], fontsize=7.2)
        b.tick_params(length=0)
        for s in ("top", "right", "left"):
            b.spines[s].set_visible(False)
        b.set_xlabel(f"Cambio del retraso del modelo frente al fijo (%): negativo = menos retraso = mejora",
                     fontsize=7.6)
        b.text(tp.UMBRAL, len(casos) - 0.35, f"{MENOS}5 %", ha="center", va="bottom", fontsize=6.9, color=tp.TINTA2)
        b.set_title("(b) Cómo se lee un veredicto: el punto es el cambio medio y la barra, su IC95", fontsize=8.2,
                    color=tp.TINTA, loc="left", pad=14)
        ruta = os.path.join(destino, "fig_lectura.png")
        fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=tp.FONDO)
        fig.savefig(os.path.splitext(ruta)[0] + ".pdf", bbox_inches="tight", facecolor=tp.FONDO,
                    metadata={"CreationDate": None})
        plt.close(fig)
    print("Escrito", ruta, "y su .pdf;", len(regulares), "llegadas regulares y", len(aleatorias), "aleatorias")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino", default=tp.IMAGENES)
    figura(ap.parse_args().destino)


if __name__ == "__main__":
    main()
