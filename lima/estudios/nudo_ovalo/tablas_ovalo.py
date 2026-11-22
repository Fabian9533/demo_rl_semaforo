"""
tablas_ovalo.py - Tablas y figuras del nudo en la red del Ovalo Vasco para la tesis (18.11.2026), con las dos demandas y
los dos modelos. Es lima/tablas_lima.py del estudio adaptado: los mismos formatos y colores (usa sus funciones), con el
modelo de orden libre como modelo citado y el de orden fijo al lado.

Uso (desde cualquier carpeta, cuando termine evaluar_ovalo.py; no corre ninguna simulacion):
  python tablas_ovalo.py [--destino salidas_ovalo/tesis] [--carpeta CARPETA]
Lee demo_rl/lima/ y demo_rl/lima/alta/ (o CARPETA, para probar): salidas/eval_t*_*.csv, fijo_ajustado.json,
val_referencias.json y, si estan, verdes_modelo.json (estudio.py verdes-modelo del modelo de orden fijo), los
resultados_lima_ippo_vecinos_<etiqueta>_s<base>.csv y los meta de las politicas; robustez/<variante>/salidas/.
Escribe en --destino (las tablas llevan solo el entorno tabular, como las de tablas_lima.py):
  ovalo_semaforo.tex      estados del semaforo: verde del plan actual, de los fijos ajustados y verde minimo
  ovalo_resultado.tex     retraso total de cada control y de los dos modelos, y cambio del modelo de orden libre
  ovalo_completa.tex      lo mismo con IC95 y p, y las referencias secundarias
  ovalo_orden.tex         orden libre frente a orden fijo: los citados y la media y el rango de los tres de cada uno
  ovalo_entrenamientos.tex   validacion y evaluacion de los tres entrenamientos de cada modelo y nivel
  ovalo_robustez.tex      prueba de robustez del reparto
  fig_ovalo_retraso.pdf|png       retraso total por control (tanda 1), un panel por nivel
  fig_ovalo_aprendizaje.pdf|png   validacion de los entrenamientos de los dos modelos frente a las referencias
  fig_ovalo_ciclo.pdf|png         ciclo del plan actual, del fijo ajustado y del modelo de orden fijo (si hay verdes_modelo)
La figura de la secuencia de luces del modelo de orden libre la hace figura_secuencia.py.
"""
import argparse
import os
import statistics
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
LIMA = os.path.join(AQUI, "demo_rl", "lima")
sys.path.insert(0, os.path.join(AQUI, "demo_rl"))
sys.path.insert(0, LIMA)
import estudio            # noqa: E402
import tablas_lima as tl  # noqa: E402  (formatos, colores y funciones de las tablas del estudio)
import tablas_plan3 as tp  # noqa: E402

MODELOS = {"libre": "Modelo de orden libre", "completo": "Modelo de orden fijo"}
BASES = (42, 2042, 4042)
NARANJA = "#eb6834"
NARANJA_CLARO = "#f4b08f"
VEH = {"publicada": 4271, "alta": 4271 * 1.2}


def escribir(nombre, cabecera, cuerpo):
    ruta = os.path.join(tl.DESTINO["tablas"], nombre)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("% Generado por tablas_ovalo.py (nudo_ovalo_estudio2) a partir de demo_rl/lima/ y demo_rl/lima/alta/. "
                "No editar a mano.\n" + "".join(f"% {linea}\n" for linea in cabecera) + cuerpo + "\n")
    print("Escrito", ruta)


def serie(carpeta, etiqueta, base):
    import csv
    ruta = os.path.join(carpeta, f"resultados_lima_ippo_vecinos_{etiqueta}_s{base}.csv")
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return [(int(r["episodio"]), float(r["val_total"])) for r in csv.DictReader(f) if r.get("val_total")]


def convergio(carpeta, etiqueta, base):
    import veredicto as regla
    return regla.convergencia(serie(carpeta, etiqueta, base), 400)


def citada(carpeta, etiqueta):
    import json
    import veredicto as regla
    vals = {}
    for b in BASES:
        with open(os.path.join(carpeta, f"politica_lima_vecinos_{etiqueta}_s{b}.json"), encoding="utf-8") as f:
            vals[b] = json.load(f)["val_elegido"]
    return regla.base_mediana(vals)


def datos_nivel(carpeta):
    """Comparaciones del modelo de orden libre citado con cada control y con el de orden fijo citado, por tanda."""
    citados = {e: citada(carpeta, e) for e in MODELOS}
    modelo = f"libre_s{citados['libre']}"
    comp, medias = tl.comparaciones(carpeta, modelo)
    for t in estudio.TANDAS:
        fijo_m = tl.leer(carpeta, t, f"completo_s{citados['completo']}")
        libre = tl.leer(carpeta, t, modelo)
        comp[t]["completo"] = estudio.comparar(libre, fijo_m)
        medias[t]["completo"] = comp[t]["completo"]["media_ref"]
    return {"citados": citados, "modelo": modelo, "comp": comp, "medias": medias}


NOMBRE = dict(tl.NOMBRE, completo="Modelo de orden fijo")
PRINCIPALES = ["actual", "fijo", "actuadoaj", "completo"]


def tabla_semaforo(niveles):
    import programa
    fijos = {n: tl.leer_json(c, "fijo_ajustado.json") for n, c in niveles.items()}
    primero = next(iter(fijos.values()))
    cab = ["Estado (quién tiene verde)", "Plan actual (s)"] + [f"Fijo ajustado, demanda {n} (s)" for n in niveles] \
        + ["Verde mínimo (s)"]
    filas = [[nombre, str(verde)] + [str(fijos[n]["ganador"][k]) for n in niveles] + [str(primero["minimos"][k])]
             for k, (nombre, verde, _) in enumerate(programa.PLAN)]
    t = programa.tiempo_fijo()
    filas += ["\\midrule", ["Ciclo, con el ámbar y el tiempo en rojo", str(sum(v for _, v, _ in programa.PLAN) + t)]
              + [str(sum(fijos[n]["ganador"]) + t) for n in niveles] + [str(sum(primero["minimos"]) + t)]]
    escribir("ovalo_semaforo.tex",
             ["Nudo en el ovalo: estados del semaforo, en el orden del plan, con el verde (s) del plan actual, del fijo",
              "ajustado al segundo de cada nivel de demanda (ajustado en el ovalo) y el verde minimo.",
              "fuente: lima/programa.py y salidas/fijo_ajustado.json de cada nivel."],
             tp.tabular(f"{tp.IZQ}{{4.3cm}}" + f"{tl.CEN}{{2.1cm}}" * (len(niveles) + 2), cab, filas))


def tabla_resultado(datos):
    filas = []
    for n, d in datos.items():
        comp, medias, modelo = d["comp"], d["medias"], d["modelo"]
        if filas:
            filas.append("\\midrule")
        primera = f"{n.capitalize()} ({VEH[n]:.0f}~veh/h)"
        for ref in PRINCIPALES:
            filas.append([primera, NOMBRE[ref], tl.par(medias[1][ref], medias[2][ref], tl.uno),
                          tl.par(comp[1][ref]["delta"], comp[2][ref]["delta"], tp.num)])
            primera = ""
        filas.append(["", MODELOS["libre"], tl.par(medias[1][modelo], medias[2][modelo], tl.uno), "---"])
    escribir("ovalo_resultado.tex",
             ["Nudo en el ovalo: retraso total por vehiculo de cada control y de los dos modelos en las dos tandas (100",
              "semillas cada una) y cambio del modelo de orden libre frente a cada uno, por nivel de demanda.",
              "fuente: salidas/eval_t1_*.csv y eval_t2_*.csv de lima/ y lima/alta/; modelos: "
              + ", ".join(f"{n}: libre_s{d['citados']['libre']} y completo_s{d['citados']['completo']}"
                          for n, d in datos.items()) + "."],
             tp.tabular(f"{tp.IZQ}{{2.5cm}}{tp.IZQ}{{3.7cm}}{tp.IZQ}{{3.4cm}}{tp.IZQ}{{4.0cm}}",
                        ["Demanda", "Control", "Retraso total, tandas 1 y 2 (s por vehículo)",
                         "Cambio del modelo de orden libre frente a este control, tandas 1 y 2 (\\%)"], filas))


def celda(c):
    p = "$p < 0.001$" if c["p"] < 0.001 else f"$p = {c['p']:.3f}$"
    return f"{tp.num(c['delta'])} [{tp.num(c['ic'][0])}, {tp.num(c['ic'][1])}], {p}"


def tabla_completa(datos):
    filas = []
    for n, d in datos.items():
        comp, medias, modelo = d["comp"], d["medias"], d["modelo"]
        if filas:
            filas.append("\\midrule")
        primera = n.capitalize()
        for ref in list(NOMBRE):
            if ref in comp[1] and ref in comp[2]:
                filas.append([primera, NOMBRE[ref], tl.par(medias[1][ref], medias[2][ref], tl.uno),
                              celda(comp[1][ref]), celda(comp[2][ref])])
                primera = ""
        filas.append(["", MODELOS["libre"], tl.par(medias[1][modelo], medias[2][modelo], tl.uno), "---", "---"])
    escribir("ovalo_completa.tex",
             ["Nudo en el ovalo: todos los controles, por nivel de demanda. Retraso total por vehiculo en las dos tandas",
              "y cambio del modelo de orden libre frente a cada uno, con IC95 (bootstrap pareado, 10 000 remuestreos) y",
              "p de Wilcoxon pareado. fuente: salidas/eval_t1_*.csv y eval_t2_*.csv de lima/ y lima/alta/."],
             tp.tabular(f"{tp.IZQ}{{1.5cm}}{tp.IZQ}{{2.6cm}}{tp.IZQ}{{2.0cm}}{tp.IZQ}{{4.0cm}}{tp.IZQ}{{4.0cm}}",
                        ["Demanda", "Control", "Retraso total, tandas 1 y 2 (s/veh)",
                         "Cambio del modelo de orden libre, tanda 1 (\\%)", "Cambio, tanda 2 (\\%)"], filas))


def tres(carpeta, etiqueta, t):
    vals = {b: tl.leer(carpeta, t, f"{etiqueta}_s{b}") for b in BASES}
    medias = {b: statistics.mean(v.values()) for b, v in vals.items()}
    semillas = sorted(set.intersection(*(set(v) for v in vals.values())))
    return statistics.mean(statistics.mean(vals[b][s] for b in BASES) for s in semillas), \
        max(medias.values()) - min(medias.values())


def tabla_orden(datos, niveles):
    filas = []
    for n, d in datos.items():
        if filas:
            filas.append("\\midrule")
        c = d["comp"]
        medias = {e: [tres(niveles[n], e, t) for t in estudio.TANDAS] for e in MODELOS}
        filas.append([n.capitalize(), tl.par(c[1]["completo"]["media"], c[2]["completo"]["media"], tl.uno),
                      tl.par(c[1]["completo"]["media_ref"], c[2]["completo"]["media_ref"], tl.uno),
                      f"{celda(c[1]['completo'])}; {celda(c[2]['completo'])}",
                      tl.par(medias["libre"][0][0], medias["libre"][1][0], tl.uno) + " ("
                      + tl.par(medias["libre"][0][1], medias["libre"][1][1], tl.uno) + ")",
                      tl.par(medias["completo"][0][0], medias["completo"][1][0], tl.uno) + " ("
                      + tl.par(medias["completo"][0][1], medias["completo"][1][1], tl.uno) + ")"])
    escribir("ovalo_orden.tex",
             ["Nudo en el ovalo: el modelo de orden libre frente al de orden fijo en la misma red. Retraso total de los",
              "entrenamientos citados en las tandas 1 y 2, cambio del libre frente al de orden fijo (IC95 y p), y media",
              "por semilla de los tres entrenamientos de cada modelo con su rango entre entrenamientos (entre parentesis).",
              "fuente: salidas/eval_t*_libre_s*.csv y eval_t*_completo_s*.csv de lima/ y lima/alta/."],
             tp.tabular(f"{tp.IZQ}{{1.5cm}}{tp.IZQ}{{2.2cm}}{tp.IZQ}{{2.2cm}}{tp.IZQ}{{4.6cm}}{tp.IZQ}{{2.6cm}}"
                        f"{tp.IZQ}{{2.6cm}}",
                        ["Demanda", "Orden libre, citado (s/veh)", "Orden fijo, citado (s/veh)",
                         "Cambio del libre frente al de orden fijo, tandas 1 y 2 (\\%)",
                         "Tres libres: media (rango)", "Tres de orden fijo: media (rango)"], filas))


def tabla_entrenamientos(datos, niveles):
    import json
    filas, notas = [], []
    for n, d in datos.items():
        if filas:
            filas.append("\\midrule")
        primera = n.capitalize()
        for etiqueta, nombre in MODELOS.items():
            for base in BASES:
                carpeta = niveles[n]
                with open(os.path.join(carpeta, f"politica_lima_vecinos_{etiqueta}_s{base}.json"), encoding="utf-8") as f:
                    meta = json.load(f)
                tandas = [tl.leer(carpeta, t, f"{etiqueta}_s{base}") for t in estudio.TANDAS]
                fijos = [tl.leer(carpeta, t, "fijo") for t in estudio.TANDAS]
                ok, plateau, estab = convergio(carpeta, etiqueta, base)
                notas.append(f"{n} {etiqueta} {base}: " + ("menos de 3 validaciones" if plateau is None else
                                                           f"plateau {plateau:+.2f} %, estabilidad {estab:.2f} %"))
                filas.append([primera, nombre, str(base) + (" (citado)" if base == d["citados"][etiqueta] else ""),
                              str(meta["ep_elegido"]), tl.uno(meta["val_elegido"]),
                              tl.par(*[statistics.mean(v.values()) for v in tandas], tl.uno),
                              tl.par(*[estudio.comparar(v, f)["delta"] for v, f in zip(tandas, fijos)], tp.num),
                              "sí" if ok else "no"])
                primera = ""
    escribir("ovalo_entrenamientos.tex",
             ["Nudo en el ovalo: los tres entrenamientos de cada modelo en cada nivel de demanda. Episodio de la version",
              "evaluada (menor retraso total en la validacion, 21001-21008), ese retraso, retraso total en las dos tandas,",
              "cambio frente al fijo ajustado y si el entrenamiento se estabilizo (regla de la tesis). El citado es el",
              "de validacion mediana. fuente: politica_lima_vecinos_<etiqueta>_s<base>.json, salidas/eval_t*_*.csv y la",
              "columna val_total de resultados_lima_ippo_vecinos_<etiqueta>_s<base>.csv; " + "; ".join(notas)],
             tp.tabular(f"{tp.IZQ}{{1.4cm}}{tp.IZQ}{{2.0cm}}{tp.IZQ}{{1.5cm}}{tp.IZQ}{{1.5cm}}{tp.IZQ}{{1.7cm}}"
                        f"{tp.IZQ}{{2.0cm}}{tp.IZQ}{{1.9cm}}{tp.IZQ}{{1.5cm}}",
                        ["Demanda", "Modelo", "Base", "Episodio de la versión evaluada",
                         "Retraso en la validación (s/veh)", "Retraso en la evaluación, tandas 1 y 2 (s/veh)",
                         "Cambio frente al fijo ajustado (\\%)", "¿Se estabilizó?"], filas))


def tabla_robustez(datos, raiz):
    d = datos["publicada"]
    libre, completo = d["modelo"], f"completo_s{d['citados']['completo']}"
    filas, detalle = [], []
    brazos = ["actual", "fijo", "actuadoaj", completo, libre]
    for variante, nombre in [("", "El supuesto (tanda 1)")] + list(tl.ROBUSTEZ.items()):
        carpeta = raiz if not variante else os.path.join(raiz, "robustez", variante)
        vals = {b: tl.leer(carpeta, 1, b) for b in brazos}
        if any(v is None for v in vals.values()):
            print("robustez: falta", variante or "la tanda 1")
            return
        m = {b: statistics.mean(v.values()) for b, v in vals.items()}
        cambios = [estudio.comparar(vals[libre], vals[ref]) for ref in brazos[:4]]
        filas.append([nombre] + [tl.uno(m[b]) for b in brazos] + [tp.num(c["delta"]) for c in cambios])
        detalle.append(f"{variante or 'tanda 1'}: " + "; ".join(
            f"{r} {c['delta']:+.2f} [{c['ic'][0]:+.2f}, {c['ic'][1]:+.2f}] p={c['p']:.2g}" for r, c in zip(brazos, cambios)))
    escribir("ovalo_robustez.tex",
             ["Nudo en el ovalo, prueba de robustez del reparto: retraso total (s/veh) de cada control con el mismo total",
              "(4271 veh/h) repartido de otra forma entre las entradas, sin reajustar ni reentrenar, y cambio del modelo",
              "de orden libre frente a cada control (%). 100 semillas (24001-24100); la primera fila es la tanda 1.",
              "fuente: lima/robustez/<variante>/salidas/eval_t1_*.csv; IC95 y p: " + " | ".join(detalle)],
             tp.tabular(f"{tp.IZQ}{{2.4cm}}" + f"{tl.DER}{{1.25cm}}" * 5 + f"{tl.DER}{{1.25cm}}" * 4,
                        ["Reparto de la demanda", "Plan actual", "Fijo ajustado", "Actuado ajustado", "Orden fijo",
                         "Orden libre", "Frente al plan actual (\\%)", "Frente al fijo (\\%)",
                         "Frente al actuado (\\%)", "Frente al orden fijo (\\%)"], filas))


def figura_retraso(datos):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rotulo = {"actual": "Plan\nactual", "fijo": "Fijo\najustado", "actuadoaj": "Actuado\najustado",
              "completo": "Orden\nfijo", "libre": "Orden\nlibre"}
    with plt.rc_context(tl.estilo()):
        fig, ejes = plt.subplots(1, len(datos), figsize=(3.9 * len(datos), 3.4), facecolor=tp.FONDO, squeeze=False)
        for ax, (n, d) in zip(ejes[0], datos.items()):
            brazos = ["actual", "fijo", "actuadoaj", "completo", "libre"]
            valores = [d["medias"][1][b if b != "libre" else d["modelo"]] for b in brazos]
            tl.limpiar(ax)
            barras = ax.bar(range(len(brazos)), valores, width=0.5, color=[tl.GRIS] * 3 + [NARANJA, tl.AZUL], zorder=3)
            for b, v in zip(barras, valores):
                ax.annotate(tl.uno(v), (b.get_x() + b.get_width() / 2, v), xytext=(0, 3), textcoords="offset points",
                            ha="center", va="bottom", fontsize=8.2, color=tp.TINTA)
            ax.set_ylim(0, max(valores) * 1.16)
            ax.set_xticks(range(len(brazos)))
            ax.set_xticklabels([rotulo[b] for b in brazos], fontsize=7.8, color=tp.TINTA, linespacing=1.25)
            ax.set_title(f"Demanda {n}: {VEH[n]:.0f} veh/h", fontsize=8.4, color=tp.TINTA2, loc="left")
        ejes[0][0].set_ylabel("Retraso total (s por vehículo)", fontsize=8.2)
        fig.tight_layout(w_pad=2.0)
        tl.guardar(fig, "fig_ovalo_retraso", plt)


def figura_aprendizaje(datos, niveles):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    colores = {"libre": (tl.AZUL, tl.AZUL_CLARO), "completo": (NARANJA, NARANJA_CLARO)}
    with plt.rc_context(tl.estilo()):
        fig, ejes = plt.subplots(len(datos), 1, figsize=(6.2, 2.6 * len(datos) + 0.5), facecolor=tp.FONDO, squeeze=False)
        for ax, (n, d) in zip(ejes[:, 0], datos.items()):
            carpeta = niveles[n]
            ruta_ref = os.path.join(carpeta, "salidas", "val_referencias.json")
            referencias = tl.leer_json(carpeta, "val_referencias.json")["retraso_total"] if os.path.exists(ruta_ref) else {}
            tl.limpiar(ax)
            ultimo, todos = 0, []
            for etiqueta, (fuerte, claro) in colores.items():
                for base in sorted(BASES, key=lambda b: b == d["citados"][etiqueta]):
                    s = serie(carpeta, etiqueta, base)
                    xs, ys = [e for e, _ in s], [v for _, v in s]
                    ultimo, todos = max(ultimo, xs[-1]), todos + ys
                    citado = base == d["citados"][etiqueta]
                    ax.plot(xs, ys, color=fuerte if citado else claro, lw=2.0 if citado else 1.0, zorder=4 if citado
                            else 3, solid_joinstyle="round")
            for brazo in ("actual", "fijo", "actuadoaj"):
                if brazo in referencias:
                    todos.append(referencias[brazo])
                    ax.axhline(referencias[brazo], color=tl.GRIS, lw=1.0, zorder=2)
                    ax.annotate(f"{tl.NOMBRE[brazo]}: {referencias[brazo]:.1f}", (ultimo, referencias[brazo]),
                                xytext=(5, 0), textcoords="offset points", ha="left", va="center", fontsize=7.2,
                                color=tp.TINTA2, annotation_clip=False)
            ax.set_xlim(0, max(1, ultimo))
            margen = (max(todos) - min(todos)) * 0.12 or 1.0
            ax.set_ylim(min(todos) - margen, max(todos) + margen)
            ax.set_ylabel("Retraso total en la\nvalidación (s por vehículo)", fontsize=8.0, linespacing=1.35)
            ax.set_title(f"Demanda {n}: {VEH[n]:.0f} veh/h", fontsize=8.4, color=tp.TINTA2, loc="left")
        ejes[-1, 0].set_xlabel("Episodio de entrenamiento", fontsize=8.2)
        leyenda = [Line2D([], [], color=tl.AZUL, lw=2.0, label="Orden libre, citado"),
                   Line2D([], [], color=NARANJA, lw=2.0, label="Orden fijo, citado"),
                   Line2D([], [], color=tl.GRIS, lw=1.0, label="Referencias, mismas semillas")]
        fig.legend(handles=leyenda, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.0), frameon=False, fontsize=7.6,
                   labelcolor=tp.TINTA, handlelength=1.6, columnspacing=1.6)
        fig.tight_layout(rect=(0, 0, 0.84, 1 - 0.32 / (2.6 * len(datos) + 0.5)), h_pad=1.4)
        tl.guardar(fig, "fig_ovalo_aprendizaje", plt)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino", default=os.path.join(AQUI, "salidas_ovalo", "tesis"))
    ap.add_argument("--carpeta", default=None, help="(pruebas) otra carpeta con la forma de demo_rl/lima")
    args = ap.parse_args()
    from evaluar_ovalo import huellas
    huellas()                       # el codigo y los datos son los de la enmienda; si no, se detiene
    os.makedirs(args.destino, exist_ok=True)
    tl.DESTINO.update(tablas=args.destino, imagenes=args.destino)
    raiz = os.path.abspath(args.carpeta) if args.carpeta else LIMA
    niveles = {"publicada": raiz, "alta": os.path.join(raiz, "alta")}
    datos = {n: datos_nivel(c) for n, c in niveles.items()}
    tabla_semaforo(niveles)
    tabla_resultado(datos)
    tabla_completa(datos)
    tabla_orden(datos, niveles)
    tabla_entrenamientos(datos, niveles)
    tabla_robustez(datos, raiz)
    figura_retraso(datos)
    figura_aprendizaje(datos, niveles)
    if all(os.path.exists(os.path.join(c, "salidas", "verdes_modelo.json")) for c in niveles.values()):
        # la figura del ciclo es del modelo de orden fijo CITADO de cada nivel (estudio.py verdes-modelo se lanza a mano)
        jugadas = {n: tl.leer_json(c, "verdes_modelo.json")["politica"] for n, c in niveles.items()}
        citadas = {n: f"politica_lima_vecinos_completo_s{d['citados']['completo']}.pt" for n, d in datos.items()}
        if jugadas != citadas:
            raise SystemExit(f"verdes_modelo.json no es del modelo de orden fijo citado: {jugadas}; deben ser {citadas}")
        tl.NIVELES.update({"publicada": ("Publicada", niveles["publicada"], 1.0),
                           "alta": ("Alta", niveles["alta"], 1.2)})
        ciclo = {n: {"veh": VEH[n]} for n in niveles}
        tl.figura_ciclo(ciclo)          # escribe fig_lima_ciclo: el de orden fijo frente al plan y al fijo ajustado
        os.replace(os.path.join(args.destino, "fig_lima_ciclo.png"), os.path.join(args.destino, "fig_ovalo_ciclo.png"))
        os.replace(os.path.join(args.destino, "fig_lima_ciclo.pdf"), os.path.join(args.destino, "fig_ovalo_ciclo.pdf"))
    for n, d in datos.items():
        for etiqueta in MODELOS:
            ok, plateau, estab = convergio(niveles[n], etiqueta, d["citados"][etiqueta])
            print(f"Demanda {n}, {MODELOS[etiqueta]} citado (base {d['citados'][etiqueta]}): "
                  + ("estabilizado" if ok else "SIN ESTABILIZAR (provisional)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
