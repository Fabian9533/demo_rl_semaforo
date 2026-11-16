"""
curvas_plan3.py - Curvas de aprendizaje del segundo estudio (plan 3) para la tesis: retraso total en las semillas de
validacion a lo largo del entrenamiento del modelo citado de cada caso, con llegadas aleatorias, junto al fijo ajustado
al segundo y al actuado ajustado medidos en esas mismas semillas.

Uso (desde demo_rl/):  python curvas_plan3.py [--procesos 10]

Lee:
  plan3/salidas/veredicto3_bases.csv y veredicto3_celdas.csv   entrenamientos de cada caso, modelo citado y version
                                                               evaluada (cerrados)
  plan3/politica_<...>.json                                    serie de validacion (val_total_serie) de cada entrenamiento
Escribe:
  plan3/curvas/val_referencias3.json   fijo ajustado al segundo y actuado ajustado en las 16 semillas de validacion
                                       (se calcula una vez con sumo; si existe, se reutiliza)
  TESIS/images/fig_plan3_aprendizaje.pdf y .png
No cambia ningun resultado del estudio: las semillas de validacion no son de evaluacion.
"""
import argparse
import csv
import json
import math
import os
import statistics
import sys
from multiprocessing import Pool

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN3 = os.path.join(AQUI, "plan3")
CURVAS = os.path.join(PLAN3, "curvas")
sys.path.insert(0, AQUI)
import tablas_plan3 as tp

FAMILIA = {"modelo completo": "p3completopoi", "IPPO con mensajes corregido": "v2poi"}
NOMBRE = {"modelo completo": "Modelo completo", "IPPO con mensajes corregido": "IPPO con mensajes corregido"}
REFERENCIAS = {"fijo": ("{esc}_r10f.add.xml", "Fijo ajustado al segundo"),
               "actuadoaj": ("{esc}_actuado_aj.add.xml", "Actuado ajustado")}


def leer(nombre):
    with open(os.path.join(PLAN3, "salidas", nombre), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def entrenamientos():
    """{caso: (modelo citado, [fila de veredicto3_bases.csv de cada entrenamiento de ese modelo])}."""
    celdas = {(r["celda"], r["llegadas"]): r for r in leer("veredicto3_celdas.csv")}
    bases = leer("veredicto3_bases.csv")
    res = {}
    for c in tp.CASOS:
        citado = celdas[(c, "aleatorias")]["modelo_citado"].split(" (")[0]
        filas =[b for b in bases if b["celda"] == c and b["llegadas"] == "aleatorias" and b["familia"] == FAMILIA[citado]]
        res[c] = (citado, sorted(filas, key=lambda b: int(b["base"])))
    return res


def serie(fila):
    with open(os.path.join(PLAN3, fila["politica"].replace(".pt", ".json")), encoding="utf-8") as f:
        meta = json.load(f)
    return [(int(v[0]), float(v[-1])) for v in meta["val_total_serie"]], meta["val_seeds"]


def _referencia(tarea):
    import barrer_fijo
    cfg, archivo, semilla = tarea
    tripinfo = os.path.join(CURVAS, "tmp", f"trip_{os.getpid()}_{semilla}.xml")
    res = barrer_fijo.correr_sumo(cfg, ["--additional-files", archivo], semilla, tripinfo)
    import comun
    for sobra in (tripinfo, comun.ruta_estadisticas(tripinfo)):
        if os.path.exists(sobra):
            os.remove(sobra)
    return res["retraso_total_prom"]


def referencias(datos, procesos):
    ruta = os.path.join(CURVAS, "val_referencias3.json")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    os.makedirs(os.path.join(CURVAS, "tmp"), exist_ok=True)
    os.chdir(PLAN3)
    tareas, claves = [], []
    for c, (_, filas) in datos.items():
        esc = tp.ESCENARIO[c]
        semillas = serie(filas[0])[1]
        for ref, (archivo, _) in REFERENCIAS.items():
            for s in semillas:
                tareas.append((f"{esc}.sumocfg", archivo.format(esc=esc), s))
                claves.append((c, ref))
    with Pool(procesos) as pool:
        valores = pool.map(_referencia, tareas)
    res = {}
    for (c, ref), v in zip(claves, valores):
        res.setdefault(c, {}).setdefault(ref, []).append(v)
    res = {c: {ref: statistics.mean(v) for ref, v in d.items()} for c, d in res.items()}
    res["semillas"] = serie(next(iter(datos.values()))[1][0])[1]
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    os.chdir(AQUI)
    return res


def figura(datos, refs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    azul, gris = "#1f6fb2", "#898781"
    orden = [["P1", "P2"], ["P3", "P4"], ["P5", "P6"]]
    with plt.rc_context({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.edgecolor": tp.EJE,
                         "axes.labelcolor": tp.TINTA2, "xtick.color": tp.TINTA2, "ytick.color": tp.TINTA2}):
        fig, ejes = plt.subplots(3, 2, figsize=(7.2, 7.6), facecolor=tp.FONDO)
        for fila_ejes, fila_casos in zip(ejes, orden):
            for ax, c in zip(fila_ejes, fila_casos):
                citado, filas = datos[c]
                red, demanda, veh = tp.CASOS[c]
                ax.set_facecolor(tp.FONDO)
                todos, ultimo, inicio_tercio = [], 0, None
                for f in sorted(filas, key=lambda f: f["version_evaluada"] == "sí"):
                    s, _ = serie(f)
                    xs, ys = [e for e, _ in s], [v for _, v in s]
                    evaluada = f["version_evaluada"] == "sí"
                    ax.plot(xs, ys, color=azul, lw=1.8 if evaluada else 0.7, alpha=1.0 if evaluada else 0.45,
                            zorder=4 if evaluada else 3, solid_joinstyle="round")
                    todos += ys[1:]                    # la primera validacion puede quedar fuera de la escala
                    ultimo = max(ultimo, xs[-1])
                    k = max(3, math.ceil(len(s) / 3))  # ultimo tercio de las validaciones (veredicto.tercio_final)
                    inicio_tercio = s[-k][0]
                    if evaluada:
                        estable = f["convergio"] == "sí"
                        ax.plot(int(f["ep_elegido"]), float(f["val_elegido"]), "o", ms=7.5, zorder=6,
                                mfc=azul if estable else tp.FONDO, mec=tp.TINTA, mew=1.2, clip_on=False)
                ax.axvspan(inicio_tercio, ultimo, color=tp.EJE, alpha=0.25, lw=0, zorder=0)
                for ref, estilo in (("fijo", "-"), ("actuadoaj", (0, (4, 2.5)))):
                    v = refs[c][ref]
                    todos.append(v)
                    ax.axhline(v, color=gris, lw=1.0, ls=estilo, zorder=2)
                margen = (max(todos) - min(todos)) * 0.10
                ax.set_ylim(min(todos) - margen, max(todos) + margen)
                ax.set_xlim(0, ultimo)
                ax.tick_params(length=0, labelsize=7.2)
                ax.grid(axis="y", color=tp.EJE, lw=0.4, alpha=0.6, zorder=1)
                ax.set_axisbelow(True)
                for s_ in ("top", "right"):
                    ax.spines[s_].set_visible(False)
                ax.set_title(f"{c}: {red}, {demanda} ({veh} veh/h)\n{NOMBRE[citado]}, {len(filas)} entrenamientos",
                             fontsize=7.6, color=tp.TINTA2, loc="left", linespacing=1.3)
        for ax in ejes[:, 0]:
            ax.set_ylabel("Retraso total en la\nvalidación (s/veh)", fontsize=7.6, linespacing=1.3)
        for ax in ejes[-1, :]:
            ax.set_xlabel("Episodio de entrenamiento", fontsize=7.6)
        leyenda = [Line2D([], [], color=azul, lw=1.8, label="Entrenamiento de la versión evaluada"),
                   Line2D([], [], color=azul, lw=0.7, alpha=0.6, label="Los otros entrenamientos"),
                   Line2D([], [], marker="o", ls="", ms=7, mfc=azul, mec=tp.TINTA, label="Versión evaluada"),
                   Line2D([], [], marker="o", ls="", ms=7, mfc=tp.FONDO, mec=tp.TINTA,
                          label="Hueco: entrenamiento sin estabilizar"),
                   Line2D([], [], color=gris, lw=1.0, label="Fijo ajustado al segundo, mismas semillas"),
                   Line2D([], [], color=gris, lw=1.0, ls=(0, (4, 2.5)), label="Actuado ajustado, mismas semillas")]
        fig.legend(handles=leyenda, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.0), frameon=False,
                   fontsize=7.4, labelcolor=tp.TINTA, handlelength=2.0, columnspacing=1.6)
        fig.tight_layout(rect=(0, 0, 1, 0.92), h_pad=1.3, w_pad=1.4)
        ruta = os.path.join(tp.IMAGENES, "fig_plan3_aprendizaje.png")
        fig.savefig(ruta, dpi=200, bbox_inches="tight", facecolor=tp.FONDO)
        fig.savefig(os.path.splitext(ruta)[0] + ".pdf", bbox_inches="tight", facecolor=tp.FONDO,
                    metadata={"CreationDate": None})
        plt.close(fig)
    print("Escrito", os.path.relpath(ruta, AQUI), "y su .pdf")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--procesos", type=int, default=10)
    ap.add_argument("--destino", default=None, help="(pruebas) carpeta de la figura, en vez de TESIS/images")
    args = ap.parse_args()
    if args.destino:
        tp.IMAGENES = args.destino
    datos = entrenamientos()
    refs = referencias(datos, args.procesos)
    for c, (citado, filas) in datos.items():
        ev = [f for f in filas if f["version_evaluada"] == "sí"]
        print(f"{c}: {citado}, {len(filas)} entrenamientos; evaluada base {ev[0]['base']} (episodio {ev[0]['ep_elegido']},"
              f" {ev[0]['val_elegido']} s/veh, estable: {ev[0]['convergio']}); fijo {refs[c]['fijo']:.2f}, "
              f"actuado ajustado {refs[c]['actuadoaj']:.2f}")
    figura(datos, refs)


if __name__ == "__main__":
    main()
