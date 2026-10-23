"""
grafico_convergencia.py - Curvas de validacion del plan de pruebas (convergencia por caso).

Uso (desde demo_rl/plan2):  python grafico_convergencia.py [--medir-fijo]
Salida: fig_plan2_convergencia.png

Un panel por caso (P1-P6). En cada uno, la curva de validacion de la politica publicada (base
mediana, veredicto.csv) de IPPO vecinos, MAPPO, DQN y Q-learning: timeLoss medio de las semillas
999 y 1999 cada 10 episodios, leido del val_serie de su meta (la validacion sigue en timeLoss).
Linea gris discontinua: el fijo tuneado vigente de la celda en esas mismas dos semillas y con la misma
metrica (fijo_validacion.json). Banda sombreada: el ultimo tercio del entrenamiento, donde se mide si
la curva se estabilizo.
--medir-fijo vuelve a medir fijo_validacion.json con el programa fijo instalado en plan2/ (27.09.2026:
el re-barrido cambio el fijo de P3-P5 y P6 es nuevo). No escribe en resultados_<esc>.csv.

Opciones del 28.09.2026 (sin ellas, todo queda como antes):
  --fijo-json RUTA   json de la linea del fijo (por defecto fijo_validacion.json). Para el resultado
                     principal, fijo_validacion_2509.json: los valores del fijo del 25.09 (P1-P5, del
                     commit de ese dia). Un caso que no esta en el json queda sin la linea del fijo.
  --medir-fijo --solo ESC   mide solo ese escenario y lo agrega al json (conserva los demas valores):
                     python grafico_convergencia.py --fijo-json fijo_validacion_2509.json --medir-fijo
                         --solo malla3_alta   (cuando el barrido de P6 con la regla del 25.09 instale su fijo)

Diseno de la figura (verificacion de la fase 2 de la entrega 3, 23.10.2026): en la tesis el texto salia a 4-5 pt,
porque la figura de 7.6 x 11 pulgadas se reducia a 0.56. Ahora: 3 x 2 paneles de 6.3 x 7.0 pulgadas (en la pagina
queda a casi 0.9), letra de 9 a 10 pt, leyenda en una franja abajo y sin titulo propio (lo da el caption). Las
etiquetas al final de cada curva se amontonaban en P4 y P6: la identidad va ahora en la leyenda y en la forma del
marcador de cada modelo, y el entrenamiento que no se estabilizo lleva marcadores huecos (como el PENDIENTE de la
figura de cambio por caso). Los datos y su lectura (val_serie de los metas, fijo del json, ultimo tercio) no
cambian.
"""
import os
import sys
import csv
import json
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

AQUI = os.path.dirname(os.path.abspath(__file__))
# Entrega 3 (23.10.2026): nombres del glosario de la tesis en titulos y leyenda (antes "corredor saturado",
# "red, demanda alta", "IPPO vecinos", "fijo tuneado", "checkpoint publicado" y "politica publicada").
# Verificacion de la fase 2 (23.10.2026): "DQN" pasa a "Double DQN" y cada titulo dice la red y la demanda del caso
# como la columna "Red y demanda" de la Tabla 5.3 (tab:resultado-principal).
CASOS = [("P1", "corredor", "P1  Corredor, nominal"), ("P2", "corredor_alta", "P2  Corredor, alta"),
         ("P3", "red", "P3  Red con rotonda, nominal"), ("P4", "red_alta", "P4  Red con rotonda, alta"),
         ("P5", "malla3", "P5  Malla 3×3, nominal"), ("P6", "malla3_alta", "P6  Malla 3×3, alta")]
# alg -> (nombre, color categorico en orden fijo, marcador, patron del archivo de meta). Colores: los cuatro primeros
# de la paleta categorica de referencia de la skill dataviz, validados con su script (modo claro: CVD 9.1, normal
# 22.9; contraste bajo 3:1 en aqua y amarillo, por eso la forma del marcador repite la identidad).
MODELOS = [("ippo_vecinos", "IPPO con mensajes", "#2a78d6", "o", "politica_{e}_vecinos_s{b}.json"),
           ("mappo", "MAPPO", "#eb6834", "s", "politica_{e}_mappo_s{b}.json"),
           ("dqn", "Double DQN", "#1baf7a", "^", "politica_{e}_dqn_s{b}.json"),
           ("ql", "Q-learning", "#eda100", "D", "q_table_{e}_ql_s{b}.meta.json")]
TINTA, TINTA2, APAGADO = "#0b0b0b", "#52514e", "#898781"
GRILLA, EJE, FONDO = "#e1e0d9", "#c3c2b7", "#fcfcfb"
TERCIO = "#efeee9"


def medir_fijo(ruta_json=None, solo=None):
    """timeLoss del fijo instalado en las semillas de validacion, como lo mide la validacion.
    Con solo=ESC mide ese escenario y conserva en el json los valores de los demas."""
    sys.path.insert(0, os.path.dirname(AQUI))
    import comun
    import evaluar
    ruta_json = ruta_json or os.path.join(AQUI, "fijo_validacion.json")
    valores = {}
    if solo and os.path.exists(ruta_json):
        with open(ruta_json, encoding="utf-8") as f:
            valores = json.load(f)
    for _, esc, _ in CASOS:
        if solo and esc != solo:
            continue
        mod = evaluar.configurar(esc)
        for semilla in (999, 1999):
            tripinfo = f"tripinfo_validacion_fijo_{esc}_{semilla}.xml"
            res = mod.correr_episodio("baseline", {}, 0.0, False, 0, semilla, tripinfo=tripinfo)
            comun.borrar_tripinfo(tripinfo)
            valores[f"{esc}_{semilla}"] = res["timeloss_prom"]
            print(esc, semilla, res["timeloss_prom"], flush=True)
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(valores, f, indent=1)
    print("escrito", ruta_json)


def leer(ruta_json=None):
    with open(os.path.join(AQUI, "veredicto.csv"), encoding="utf-8") as f:
        ver = {(r["caso"], r["modelo"]): r for r in csv.DictReader(f)}
    with open(ruta_json or os.path.join(AQUI, "fijo_validacion.json"), encoding="utf-8") as f:
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


def main(ruta_json=None):
    ver, fijo = leer(ruta_json)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": EJE,
                         "axes.labelcolor": TINTA2, "xtick.color": TINTA2, "ytick.color": TINTA2,
                         "xtick.labelsize": 9, "ytick.labelsize": 9})
    fig, ejes = plt.subplots(3, 2, figsize=(6.3, 7.0), dpi=200, facecolor=FONDO)
    ejes = ejes.ravel()
    for k, (caso, esc, titulo) in enumerate(CASOS):
        ax = ejes[k]
        ax.set_facecolor(FONDO)
        ax.axvspan(200 * 2 / 3, 200, color=TERCIO, zorder=0, lw=0)
        todos = []
        if f"{esc}_999" in fijo and f"{esc}_1999" in fijo:
            ref = (fijo[f"{esc}_999"] + fijo[f"{esc}_1999"]) / 2
            ax.axhline(ref, color=APAGADO, lw=1.2, ls=(0, (4, 3)), zorder=1)
            todos = [ref]
        for alg, nombre, color, marca, patron in MODELOS:
            fila = ver.get((caso, alg))
            s = serie(esc, patron, fila["base_publicada"] if fila else "")
            if not s:
                continue
            xs, ys, ep_pub, val_pub = s
            todos += ys
            # marcador hueco: el entrenamiento de la version evaluada no se estabilizo (como el PENDIENTE de la
            # figura de cambio por caso); relleno: se estabilizo
            estable = fila["convergio"] == "si"
            ax.plot(xs, ys, color=color, lw=1.6, zorder=3, solid_capstyle="round", solid_joinstyle="round")
            if estable:
                ax.plot(xs, ys, marca, ms=3.8, color=color, mec=FONDO, mew=0.5, zorder=4)
            else:
                ax.plot(xs, ys, marca, ms=3.8, mfc=FONDO, mec=color, mew=1.0, ls="", zorder=4)
            if ep_pub is not None and val_pub is not None:
                ax.plot([ep_pub], [val_pub], marca, ms=8.5, mfc=color if estable else FONDO, mec=TINTA, mew=1.2,
                        zorder=5)
        bajo, alto = min(todos), max(todos)
        margen = (alto - bajo) * 0.08 or 1
        ax.set_ylim(bajo - margen, alto + margen)
        ax.set_title(titulo, loc="left", fontsize=10, color=TINTA, fontweight="bold", pad=6)
        ax.set_xlim(0, 200)
        ax.set_xticks([0, 50, 100, 150, 200])
        ax.grid(axis="y", color=GRILLA, lw=0.6)
        ax.tick_params(length=0)
        for lado in ("top", "right", "left"):
            ax.spines[lado].set_visible(False)
        if k >= len(CASOS) - 2:
            ax.set_xlabel("episodio de entrenamiento", fontsize=9.5)
    # leyenda en una franja bajo los paneles: el color y la forma dicen el modelo
    manijas = [Line2D([], [], color=c, lw=1.6, marker=m, ms=6, mec=FONDO, mew=0.5, label=n)
               for _, n, c, m, _ in MODELOS]
    manijas += [Line2D([], [], color=APAGADO, lw=1.2, ls=(0, (4, 3)), label="fijo ajustado, mismas semillas"),
                Line2D([], [], color=TINTA2, lw=0, marker="o", ms=8.5, mfc=TINTA2, mec=TINTA, mew=1.2,
                       label="versión evaluada: marcador grande"),
                Line2D([], [], color=TINTA2, lw=0, marker="o", ms=6, mfc=FONDO, mec=TINTA2, mew=1.0,
                       label="hueco: el entrenamiento no se estabilizó"),
                Patch(facecolor=TERCIO, edgecolor="none", label="último tercio: se mide si se estabiliza")]
    fig.legend(handles=manijas, loc="lower center", ncol=2, frameon=False, fontsize=9, handlelength=2.6,
               columnspacing=1.4, labelcolor=TINTA, bbox_to_anchor=(0.5, 0.0))
    # un solo rotulo vertical para los seis paneles: repetido en cada fila no cabia en el alto de un panel
    fig.supylabel("retraso medio en validación, semillas 999 y 1999 (s/veh)", fontsize=9.5, color=TINTA2, x=0.012,
                  y=0.575)
    fig.tight_layout(rect=(0.025, 0.15, 1, 1), h_pad=1.4, w_pad=1.6)
    salida = os.path.join(AQUI, "fig_plan2_convergencia.png")
    fig.savefig(salida, facecolor=FONDO)
    print("escrito", salida)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--medir-fijo", action="store_true", help="vuelve a medir fijo_validacion.json")
    ap.add_argument("--fijo-json", default=None, help="json del fijo (por defecto fijo_validacion.json)")
    ap.add_argument("--solo", default=None, choices=[e for _, e, _ in CASOS],
                    help="con --medir-fijo: mide solo ese escenario y lo agrega al json")
    args = ap.parse_args()
    ruta = os.path.abspath(args.fijo_json) if args.fijo_json else None
    if args.medir_fijo:
        medir_fijo(ruta, args.solo)
    main(ruta)
