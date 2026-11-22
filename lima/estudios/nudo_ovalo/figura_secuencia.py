"""
figura_secuencia.py - Secuencia de luces del nudo en el ovalo: unos 6 minutos de la hora punta, el modelo de orden fijo
frente al de orden libre (los entrenamientos citados), con la misma semilla y la misma demanda; y, para toda la hora, que
pasos entre estados usa cada uno. Estilo de las figuras de la tesis (tablas_lima.figura_ciclo y la figura de la prueba
del orden libre, orden_libre_2026-11-17/analisis/tesis/figura.py).

Uso (desde cualquier carpeta, cuando existan las politicas entrenadas):
  python figura_secuencia.py correr  [--nivel publicada] [--semilla 21001]
  python figura_secuencia.py dibujar [--nivel publicada] [--semilla 21001] [--desde 1800] [--segundos 360]
  --carpeta CARPETA (pruebas): otra carpeta con la forma de demo_rl/lima; --salida: donde escribir la figura
correr: cada politica citada (validacion mediana) juega un episodio (rl_ippo.py demo) en su copia de la carpeta del nivel
(<salida>/corridas_secuencia/<nivel>/<modelo>/), con --traza-fases. 21001 es la primera semilla de validacion, ya vista
al elegir la version; no se usa ninguna semilla de evaluacion.
dibujar: lee las dos trazas, clasifica cada segundo con las reglas de comprobar_fases.plan (verde de cada estado, ambar,
todo rojo) y escribe fig_ovalo_secuencia_<nivel>.png y .pdf, y fig_ovalo_secuencia_<nivel>.txt con los tramos dibujados
y, para la hora con demanda (1-3600 s), cuantas veces se pasa de cada estado a cada otro y el verde medio de cada estado
(con otra semilla que la 21001, el nombre lleva tambien _s<semilla>).
"""
import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DEMO = os.path.join(AQUI, "demo_rl")
sys.path.insert(0, AQUI)
sys.path.insert(0, DEMO)
import comprobar_fases as cf            # noqa: E402

NIVELES = {"publicada": "", "alta": "alta"}
MODELOS = [("completo", "Modelo de\norden fijo"), ("libre", "Modelo de\norden libre")]
DATOS = ["lima.sumocfg", "lima.net.xml", "lima.rou.xml", "lima.add.xml", "e2_lima_75.add.xml", "lima_libre.json"]
# colores y tintas de la tesis (lima/tablas_lima.py y tablas_plan3.py)
AZUL, NARANJA, VERDE = "#1f6fb2", "#eb6834", "#1baf7a"
CLARO, GRIS = "#d9d8d0", "#898781"
FONDO, TINTA, TINTA2, EJE = "#fcfcfb", "#0b0b0b", "#52514e", "#c3c2b7"
COLOR_ESTADO = [AZUL, NARANJA, VERDE]
NOMBRE_ESTADO = ["Reducto de frente, los dos sentidos", "Giros a la izquierda de Reducto",
                 "28 de Julio desde el puente y Balboa"]
CORTO = ["Reducto de frente", "Giros de Reducto", "28 de Julio y Balboa"]
HORA = 3600


def citada(carpeta, etiqueta):
    import veredicto as regla
    vals = {}
    for b in (42, 2042, 4042):
        with open(os.path.join(carpeta, f"politica_lima_vecinos_{etiqueta}_s{b}.json"), encoding="utf-8") as f:
            vals[b] = json.load(f)["val_elegido"]
    return regla.base_mediana(vals)


def correr(carpeta, nivel, semilla, salida):
    for etiqueta, _ in MODELOS:
        base = citada(carpeta, etiqueta)
        donde = os.path.join(salida, "corridas_secuencia", nivel, etiqueta)
        os.makedirs(donde, exist_ok=True)
        for f in DATOS:
            shutil.copyfile(os.path.join(carpeta, f), os.path.join(donde, f))
        traza = os.path.join(donde, f"traza_{semilla}.csv")
        if os.path.exists(traza):
            os.remove(traza)                    # rl_ippo agrega filas: se empieza de cero
        pt = os.path.join(carpeta, f"politica_lima_vecinos_{etiqueta}_s{base}.pt")
        cmd = [sys.executable, os.path.join(DEMO, "rl_ippo.py"), "demo", "--escenario", "lima", "--politica", pt,
               "--seed", str(semilla), "--traza-fases", traza]
        r = subprocess.run(cmd, cwd=donde, capture_output=True, text=True)
        print(f"{etiqueta} (base {base}): codigo {r.returncode}; {r.stdout.strip()[-300:]}{r.stderr.strip()[-300:]}")
        if r.returncode != 0:
            raise SystemExit(f"{etiqueta}: rl_ippo.py demo fallo; la traza {traza} no sirve")


def tramos(p, filas):
    """[(tipo, estado, inicio, fin)] de un episodio: verde de un estado, ambar del estado que termina o todo rojo. La
    fila t es el paso de t - 1 a t."""
    res = []
    for _, luz, _ in filas:
        if luz in p["por_letras"]:
            tipo, estado = "verde", p["por_letras"][luz][0][0]
        elif luz in set(p["rojo"].values()):
            tipo, estado = "rojo", None
        elif "y" in luz:
            tipo, estado = "ambar", res[-1][1] if res else None
        else:
            raise SystemExit(f"luces desconocidas: {luz}")
        t = len(res) and res[-1][3]
        if res and res[-1][0] == tipo and (tipo != "verde" or res[-1][1] == estado):
            res[-1] = (tipo, res[-1][1], res[-1][2], res[-1][3] + 1)
        else:
            res.append((tipo, estado, t, t + 1))
    return res


def resumen(nombre, trs):
    """Pasos entre estados y verde medio de cada estado en la hora con demanda."""
    verdes = [(e, i, f) for tipo, e, i, f in trs if tipo == "verde" and f <= HORA]
    pasos = {}
    for (a, _, _), (b, _, _) in zip(verdes, verdes[1:]):
        pasos[(a, b)] = pasos.get((a, b), 0) + 1
    lineas = [f"{nombre}: {len(verdes)} verdes en la hora; pasos de un estado a otro: " + ", ".join(
        f"{CORTO[a]} -> {CORTO[b]} {v}" + ("" if b == (a + 1) % 3 else " (fuera del orden del plan)")
        for (a, b), v in sorted(pasos.items()))]
    for k in range(3):
        d = [f - i for e, i, f in verdes if e == k]
        lineas.append(f"   verde de {CORTO[k]}: " + (f"{len(d)} veces, medio {statistics.mean(d):.1f} s" if d else
                                                     "nunca"))
    return lineas


def dibujar(carpeta, nivel, semilla, desde, segundos, salida):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    p = cf.plan(os.path.join(carpeta, "lima.net.xml"))
    hasta = desde + segundos
    texto = [f"Demanda {nivel}, semilla {semilla}, segundos {desde} a {hasta} del episodio"]
    estilo = {"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.edgecolor": EJE, "axes.labelcolor": TINTA2,
              "xtick.color": TINTA2, "ytick.color": TINTA2}
    with plt.rc_context(estilo):
        alto = 2.35
        fig, ax = plt.subplots(figsize=(6.6, alto), facecolor=FONDO)
        ax.set_facecolor(FONDO)
        for y, (etiqueta, rotulo) in zip((1, 0), MODELOS):
            traza = os.path.join(salida, "corridas_secuencia", nivel, etiqueta, f"traza_{semilla}.csv")
            (_, filas), = cf.leer_traza(traza).items()
            trs = tramos(p, filas)
            texto += resumen(rotulo.replace("\n", " "), trs)
            for tipo, estado, ini, fin in trs:
                if fin <= desde or ini >= hasta:
                    continue
                x0, x1 = max(ini, desde), min(fin, hasta)
                color = COLOR_ESTADO[estado] if tipo == "verde" else GRIS if tipo == "rojo" else CLARO
                ax.barh(y, x1 - x0, left=x0, height=0.46, color=color, edgecolor=FONDO, linewidth=1.2, zorder=3)
                cortado = ini < desde or fin > hasta
                if tipo in ("verde", "rojo") and not cortado:
                    ax.text((x0 + x1) / 2, y + 0.29, f"{fin - ini}", ha="center", va="bottom", fontsize=7.0,
                            color=TINTA if tipo == "verde" else TINTA2)
                nombre = CORTO[estado] if tipo == "verde" else "todo en rojo" if tipo == "rojo" else "ambar"
                texto.append(f"   {etiqueta:8s} {ini:5d}-{fin:5d} ({fin - ini:3d} s) {nombre}"
                             + (" [cortado por la ventana]" if cortado else ""))
        ax.set_yticks((1, 0))
        ax.set_yticklabels([r for _, r in MODELOS], fontsize=7.8, color=TINTA, linespacing=1.2)
        ax.set_ylim(-0.4, 1.55)
        ax.set_xlim(desde, hasta)
        marcas = list(range(desde, hasta + 1, 60))
        ax.set_xticks(marcas)
        ax.set_xticklabels([f"{m // 60}:00" for m in marcas], fontsize=7.6)
        ax.set_xlabel("Minuto de la hora punta (mm:ss)", fontsize=8.0)
        ax.tick_params(length=0)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        leyenda = [Patch(color=c, label=n) for c, n in zip(COLOR_ESTADO, NOMBRE_ESTADO)]
        leyenda += [Patch(color=CLARO, label="Ámbar (3 s)"), Patch(color=GRIS, label="Todo en rojo (34 s)")]
        fig.legend(handles=leyenda, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.0), frameon=False,
                   fontsize=7.4, labelcolor=TINTA, handlelength=1.1, columnspacing=1.4)
        fig.tight_layout(rect=(0, 0, 1, 1 - 0.42 / alto))
        os.makedirs(salida, exist_ok=True)
        # un archivo por demanda (y por semilla, si no es la de siempre): la de la alta no pisa a la de la publicada
        base = os.path.join(salida, f"fig_ovalo_secuencia_{nivel}" + ("" if semilla == 21001 else f"_s{semilla}"))
        fig.savefig(base + ".png", dpi=200, bbox_inches="tight", facecolor=FONDO)
        fig.savefig(base + ".pdf", bbox_inches="tight", facecolor=FONDO, metadata={"CreationDate": None})
        plt.close(fig)
    with open(base + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(texto) + "\n")
    print("\n".join(texto))
    print("Escrito", base + ".png y .pdf")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["correr", "dibujar"])
    ap.add_argument("--nivel", choices=list(NIVELES), default="publicada")
    ap.add_argument("--semilla", type=int, default=21001)
    ap.add_argument("--desde", type=int, default=1800)
    ap.add_argument("--segundos", type=int, default=360)
    ap.add_argument("--carpeta", default=None, help="(pruebas) otra carpeta con la forma de demo_rl/lima")
    ap.add_argument("--salida", default=os.path.join(AQUI, "salidas_ovalo"))
    args = ap.parse_args()
    assert 21001 <= args.semilla <= 21008 or 424301 <= args.semilla <= 424360, "solo validacion o humo"
    from evaluar_ovalo import huellas
    huellas()                       # el codigo y los datos son los de la enmienda; si no, se detiene
    carpeta = os.path.join(os.path.abspath(args.carpeta) if args.carpeta else os.path.join(DEMO, "lima"),
                           NIVELES[args.nivel])
    if args.accion == "correr":
        correr(carpeta, args.nivel, args.semilla, args.salida)
    else:
        dibujar(carpeta, args.nivel, args.semilla, args.desde, args.segundos, args.salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
