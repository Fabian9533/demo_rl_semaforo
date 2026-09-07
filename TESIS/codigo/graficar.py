"""
graficar.py - Figuras de un escenario para la tesis (matplotlib, PNG a 200 dpi).

Uso: python graficar.py [cruce|cruce2|corredor|red]   (por defecto: cruce)

Lee resultados_<esc>.csv (ultimo bloque de entrenamiento), evaluacion_<esc>.csv y
evaluacion_<esc>_resumen.csv (si existen), serie_<esc>_<brazo>_s<semilla>.csv y
vehiculos_<esc>_<brazo>.csv (si existen), y guarda:

  fig_<esc>_curva.png        curva de aprendizaje: retraso y espera por episodio de
                             entrenamiento (puntos grises, media movil), evaluacion greedy
                             cada 5 episodios, banda del fijo y linea del actuado con las
                             semillas de evaluacion, y epsilon debajo
  fig_<esc>_comparacion.png  fijo vs actuado vs RL por metrica: un punto por semilla,
                             lineas que unen la misma semilla, media con IC95 %, delta y p
  fig_<esc>_serie.png        vehiculos detenidos a lo largo de la hora (misma semilla)
  fig_<esc>_ecdf.png         distribucion por vehiculo del retraso y la espera
  fig_<esc>_qtable.png       estados visitados y cambio maximo de Q por episodio
Con politicas IPPO (resultados_<esc>_ippo_<variante>_s<base>.csv) anade ademas:
  fig_<esc>_curva_ippo.png   evaluacion intermedia (semilla 999) por variante y semilla base
  fig_<esc>_fases.png        verde de la avenida por semaforo en una ventana de 5 min (desfase)
  fig_<esc>_spillback.png    spillback, cola maxima en enlace y no terminados por brazo
Los brazos IPPO que entran en las figuras son la politica mediana de cada variante.
"""
import os
import csv
import sys
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

escenario = sys.argv[1] if len(sys.argv) > 1 else "cruce"

# Colores: un tono fijo por control (fijo azul, actuado naranja, RL verde-agua);
# el entrenamiento y las referencias van en gris. Texto siempre en tinta, no en color de serie.
COLOR = {"fijo": "#2a78d6", "actuado": "#eb6834", "rl": "#1baf7a",
         "ippo_local": "#7b4fc4", "ippo_vecinos": "#d63a6a", "ippo_spill": "#a67c00", "ippo_cambio": "#4a4a4a"}
GRIS = "#9b9a95"
GRIS_CLARO = "#e6e6e3"
TINTA = "#0b0b0b"
TINTA2 = "#52514e"
NOMBRE = {"fijo": "Tiempo fijo", "actuado": "Actuado (SUMO)", "rl": "Q-learning",
          "ippo_local": "IPPO local", "ippo_vecinos": "IPPO vecinos", "ippo_spill": "IPPO spill",
          "ippo_cambio": "IPPO cambio"}
FASE_AVENIDA = {"corredor": 2, "corredor_alta": 2, "red": 0}   # indice de la fase verde de la avenida


def variante_de(brazo):
    """'ippo_vecinos_s2042_L5p30' -> 'ippo_vecinos'; 'fijo' -> 'fijo'."""
    partes = brazo.split("_")
    return "_".join(partes[:2]) if brazo.startswith("ippo") else brazo


def color_de(brazo):
    return COLOR.get(variante_de(brazo), TINTA2)


def nombre_de(brazo):
    return NOMBRE.get(variante_de(brazo), brazo)
METRICA = {
    "timeloss_prom": ("Retraso por vehículo (timeLoss)", "s/veh"),
    "espera_prom": ("Espera detenida por vehículo", "s/veh"),
    "cola_prom": ("Cola promedio", "veh detenidos"),
    "cola_max": ("Cola máxima instantánea", "veh detenidos"),
    "paradas_prom": ("Paradas por vehículo", "paradas/veh"),
    "co2_prom": ("CO$_2$ por vehículo", "g/veh"),
    "throughput": ("Vehículos que llegan antes de 3600 s", "veh"),
}
META = {"timeloss_prom": -25, "cola_prom": -20, "co2_prom": -5}   # metas de la tesis (% vs fijo)

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "legend.fontsize": 8,
    "axes.edgecolor": TINTA2, "axes.labelcolor": TINTA2, "xtick.color": TINTA2, "ytick.color": TINTA2,
    "text.color": TINTA, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRIS_CLARO, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "figure.facecolor": "white", "axes.facecolor": "white", "legend.frameon": False,
})


def leer_csv(nombre):
    if not os.path.exists(nombre):
        return []
    with open(nombre, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def numero(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def ic95(vals):
    from scipy import stats
    n = len(vals)
    return stats.t.ppf(0.975, n - 1) * statistics.stdev(vals) / n ** 0.5 if n > 1 else 0.0


def media_movil(vals, k=5):
    return [statistics.mean(vals[max(0, i - k + 1):i + 1]) for i in range(len(vals))]


def guardar(fig, nombre):
    fig.savefig(nombre, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("Guardado", nombre)


# ---------------- Datos ----------------
def desde_ultimo_reinicio(filas):
    """Solo las filas de la ultima corrida: los CSV se abren en modo anadir, asi que un
    entrenamiento abortado y relanzado deja los primeros episodios repetidos al principio."""
    inicio = 0
    for i in range(1, len(filas)):
        if int(filas[i]["episodio"]) <= int(filas[i - 1]["episodio"]):
            inicio = i
    return filas[inicio:]


filas = leer_csv(f"resultados_{escenario}.csv")
train = desde_ultimo_reinicio([f for f in filas if f["modo"] == "train"])
evaluacion = leer_csv(f"evaluacion_{escenario}.csv")
resumen = leer_csv(f"evaluacion_{escenario}_resumen.csv")
en_csv = {f["brazo"] for f in evaluacion}
brazos = [b for b in ("fijo", "actuado", "rl") if b in en_csv]
# Brazos IPPO principales: la politica mediana de cada variante (comun.politicas_ippo)
import comun
politicas = comun.politicas_ippo(escenario)
brazos_ippo = [b for b in (comun.brazo_ippo(v, politicas, en_csv) for v in ("local", "vecinos", "spill", "cambio")) if b]
brazos += brazos_ippo


def valores_eval(brazo, metrica):
    return [numero(f[metrica]) for f in evaluacion if f["brazo"] == brazo and numero(f[metrica]) is not None]


def fila_resumen(brazo, metrica):
    return next((r for r in resumen if r["brazo"] == brazo and r["metrica"] == metrica), None)


# ---------------- Figura 1: curva de aprendizaje ----------------
if train:
    ep = [int(f["episodio"]) for f in train]
    eps = [float(f["epsilon"]) for f in train]
    fig, ejes = plt.subplots(2, 2, figsize=(11, 5.6), sharex=True,
                             gridspec_kw={"height_ratios": [4, 1], "hspace": 0.08, "wspace": 0.25})
    for j, (m, col_eval) in enumerate((("timeloss_prom", "eval_timeloss"), ("espera_prom", "eval_espera"))):
        ax = ejes[0][j]
        y = [float(f[m]) for f in train]
        ax.plot(ep, y, "o", color=GRIS, ms=3.5, alpha=0.7, label="episodio de entrenamiento (ε > 0)")
        ax.plot(ep, media_movil(y), "-", color=TINTA2, lw=1.4, label="media móvil de 5 episodios")
        ev = [(int(f["episodio"]), numero(f[col_eval])) for f in train if numero(f[col_eval]) is not None]
        if ev:
            ax.plot([e for e, _ in ev], [v for _, v in ev], "-s", color=COLOR["rl"], lw=1.8, ms=5,
                    label="política congelada (ε = 0), semilla fija")
        for brazo in ("fijo", "actuado"):
            vals = valores_eval(brazo, m)
            if vals:
                mu, h = statistics.mean(vals), ic95(vals)
                ax.axhspan(mu - h, mu + h, color=COLOR[brazo], alpha=0.18, lw=0)
                ax.axhline(mu, color=COLOR[brazo], lw=1.4,
                           label=f"{NOMBRE[brazo]}, media ± IC95 % ({len(vals)} semillas)")
        if not valores_eval("fijo", m):
            base = [f for f in filas if f["modo"] == "baseline"]
            if base:
                ax.axhline(float(base[-1][m]), color=COLOR["fijo"], lw=1.4, label="Tiempo fijo (una semilla)")
        titulo, unidad = METRICA[m]
        ax.set_title(titulo, loc="left")
        ax.set_ylabel(unidad)
        ax.set_ylim(bottom=0)
        axe = ejes[1][j]
        axe.plot(ep, eps, "-", color=TINTA2, lw=1.4)
        axe.set_ylabel("ε")
        axe.set_ylim(0, 1.05)
        axe.set_yticks([0, 0.5, 1])
        axe.set_xlabel("Episodio (una hora simulada de entrenamiento)")
        piso = next((e for e, v in zip(ep, eps) if v <= min(eps) + 1e-9), None)
        if piso and piso < ep[-1]:
            axe.axvline(piso, color=GRIS, lw=1)
            a_la_izquierda = piso > ep[-1] * 0.5
            axe.text(piso - 0.6 if a_la_izquierda else piso + 0.6, 0.6,
                     f"ε llega al piso ({min(eps):.2f}) en el episodio {piso}",
                     fontsize=7.5, color=TINTA2, va="center", ha="right" if a_la_izquierda else "left")
    manijas, etiquetas = ejes[0][0].get_legend_handles_labels()
    fig.legend(manijas, etiquetas, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.0))
    fig.subplots_adjust(top=0.84, bottom=0.2, left=0.07, right=0.98)
    fig.suptitle(f"Escenario {escenario}: aprendizaje del agente", x=0.02, y=0.97, ha="left", fontsize=11)
    fig.text(0.02, 0.905, "Cada punto es una hora completa de tráfico con la misma red y la misma demanda; "
             "entre episodios cambian ε, la semilla de SUMO y la Q-table heredada.", fontsize=8, color=TINTA2)
    guardar(fig, f"fig_{escenario}_curva.png")

# ---------------- Figura 2: comparacion final por semilla ----------------
if evaluacion and len(brazos) >= 2:
    metricas = [m for m in ("timeloss_prom", "espera_prom", "cola_prom",
                            "cola_max", "paradas_prom", "co2_prom") if valores_eval(brazos[0], m)]
    columnas = 3
    filas_fig = (len(metricas) + columnas - 1) // columnas
    ancho = max(10, 1.8 * len(brazos) + 4)
    fig, ejes = plt.subplots(filas_fig, columnas, figsize=(ancho, 4.3 * filas_fig), squeeze=False)
    ejes = [ax for fila in ejes for ax in fila]
    for ax in ejes[len(metricas):]:
        ax.axis("off")
    semillas = sorted({f["semilla"] for f in evaluacion})
    for ax, m in zip(ejes, metricas):
        x = {b: i for i, b in enumerate(brazos)}
        for s in semillas:                                   # la misma semilla unida entre controles
            pts = [(x[b], numero(next((f[m] for f in evaluacion if f["brazo"] == b and f["semilla"] == s), None)))
                   for b in brazos]
            pts = [(xi, v) for xi, v in pts if v is not None]
            ax.plot([p[0] for p in pts], [p[1] for p in pts], "-", color=GRIS_CLARO, lw=0.9, zorder=1)
            ax.plot([p[0] for p in pts], [p[1] for p in pts], "o", color=GRIS, ms=3.5, zorder=2)
        for b in brazos:
            vals = valores_eval(b, m)
            ax.errorbar(x[b], statistics.mean(vals), yerr=ic95(vals), fmt="o", color=color_de(b), ms=8,
                        capsize=4, lw=1.8, zorder=3)
        todos = [v for b in brazos for v in valores_eval(b, m)]
        recortado = (max(todos) - min(todos)) < 0.3 * max(todos)   # diferencias pequenas: no partir de cero
        if m in META and valores_eval("fijo", m):
            meta = statistics.mean(valores_eval("fijo", m)) * (1 + META[m] / 100)
            ax.axhline(meta, color=TINTA2, lw=0.9)
            ax.text(-0.45, meta, f"meta {META[m]:+d} %", fontsize=7, color=TINTA2, ha="left", va="bottom")
            todos.append(meta)
        titulo, unidad = METRICA[m]
        r = fila_resumen("rl", m)
        sub = ""
        if r and r.get("delta_pct"):
            sub = f"\nRL vs fijo: {float(r['delta_pct']):+.1f} %  (p = {r['p_wilcoxon']})"
        for b in brazos_ippo[:2]:
            ri = fila_resumen(b, m)
            if ri and ri.get("delta_pct"):
                sub += f"\n{nombre_de(b)} vs fijo: {float(ri['delta_pct']):+.1f} %  (p = {ri['p_wilcoxon']})"
        ax.set_title(titulo + sub, loc="left", fontsize=8.5)
        ax.set_ylabel(unidad + (" (eje recortado)" if recortado else ""))
        ax.set_xticks(range(len(brazos)))
        ax.set_xticklabels([nombre_de(b).replace(" (SUMO)", "").replace("IPPO ", "IPPO\n") for b in brazos],
                           fontsize=8)
        ax.set_xlim(-0.5, len(brazos) - 0.5)
        if recortado:
            margen = (max(todos) - min(todos)) * 0.25
            ax.set_ylim(min(todos) - margen, max(todos) + margen)
        else:
            ax.set_ylim(bottom=0)
        ax.grid(axis="x", visible=False)
    fig.suptitle(f"Escenario {escenario}: evaluación con política congelada, {len(semillas)} semillas "
                 f"({semillas[0]}–{semillas[-1]}); puntos = una semilla, marcador grande = media ± IC95 %",
                 x=0.02, ha="left", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    guardar(fig, f"fig_{escenario}_comparacion.png")

# ---------------- Figura 3: dentro de la hora ----------------
series = {}
for b in brazos:
    for nombre in sorted(os.listdir(".")):
        if nombre.startswith(f"serie_{escenario}_{b}_s") and nombre.endswith(".csv"):
            series[b] = leer_csv(nombre)
            break
if series:
    ejemplo = next(iter(series.values()))
    columnas = [c for c in ejemplo[0].keys() if c != "t"]
    if escenario in ("cruce", "cruce2"):
        grupos = {"Eje N–S": [c for c in columnas if c[0] in "NS"], "Eje E–O": [c for c in columnas if c[0] in "EW"]}
    else:
        grupos = {"Todas las aproximaciones": columnas}
    fig, ejes = plt.subplots(1, len(grupos), figsize=(5.2 * len(grupos), 3.8), squeeze=False)
    for ax, (titulo, cols) in zip(ejes[0], grupos.items()):
        for b, filas_s in series.items():
            t = [float(f["t"]) / 60 for f in filas_s]
            y = [sum(float(f[c]) for c in cols) for f in filas_s]
            ax.plot(t, y, "-", color=color_de(b), lw=1.8, label=nombre_de(b))
        ax.axvline(30, color=GRIS, lw=1)
        ax.text(30.5, ax.get_ylim()[1] * 0.95, "cambia la demanda", fontsize=7.5, color=TINTA2, va="top")
        ax.set_title(titulo, loc="left")
        ax.set_xlabel("Minuto de la hora simulada")
        ax.set_ylabel("Vehículos detenidos")
        ax.set_xlim(0, 62)
        ax.set_ylim(bottom=0)
    manijas, etiquetas = ejes[0][0].get_legend_handles_labels()
    fig.legend(manijas, etiquetas, loc="lower center", ncol=len(etiquetas), bbox_to_anchor=(0.5, -0.02))
    fig.suptitle(f"Escenario {escenario}: vehículos detenidos por minuto, misma semilla en los tres controles",
                 x=0.02, ha="left", fontsize=10)
    fig.tight_layout(rect=(0, 0.05, 1, 0.93))
    guardar(fig, f"fig_{escenario}_serie.png")

# ---------------- Figura 4: distribucion por vehiculo ----------------
vehiculos = {b: leer_csv(f"vehiculos_{escenario}_{b}.csv") for b in brazos}
vehiculos = {b: v for b, v in vehiculos.items() if v}
if vehiculos:
    fig, ejes = plt.subplots(1, 2, figsize=(10, 3.8))
    for ax, (col, titulo) in zip(ejes, (("timeloss", "Retraso por vehículo (s)"), ("espera", "Espera detenida por vehículo (s)"))):
        for b, filas_v in vehiculos.items():
            vals = sorted(float(f[col]) for f in filas_v)
            n = len(vals)
            ax.plot(vals, [(i + 1) / n for i in range(n)], "-", color=color_de(b), lw=1.8, label=nombre_de(b))
            p90 = vals[int(0.9 * n) - 1]
            ax.plot([p90], [0.9], "o", color=color_de(b), ms=5)
        ax.axhline(0.9, color=GRIS_CLARO, lw=0.9)
        ax.text(ax.get_xlim()[1], 0.905, "percentil 90", fontsize=7.5, color=TINTA2, ha="right", va="bottom")
        ax.set_xlabel(titulo)
        ax.set_ylabel("Fracción acumulada de vehículos")
        ax.set_ylim(0, 1.02)
    ejes[0].legend(loc="lower right")
    fig.suptitle(f"Escenario {escenario}: distribución por vehículo (una semilla de evaluación)",
                 x=0.02, ha="left", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    guardar(fig, f"fig_{escenario}_ecdf.png")

# ---------------- Figura 5: Q-table ----------------
if train and any(numero(f.get("estados_q")) is not None for f in train):
    fig, ejes = plt.subplots(1, 2, figsize=(10, 3.4))
    est = [(int(f["episodio"]), numero(f["estados_q"])) for f in train if numero(f.get("estados_q")) is not None]
    dq = [(int(f["episodio"]), numero(f["dq_max"])) for f in train if numero(f.get("dq_max"))]
    ejes[0].plot([e for e, _ in est], [v for _, v in est], "-", color=TINTA2, lw=1.8)
    ejes[0].set_title("Estados distintos visitados (tamaño de la Q-table)", loc="left")
    ejes[0].set_ylabel("estados")
    ejes[0].set_ylim(bottom=0)
    ejes[1].plot([e for e, _ in dq], [v for _, v in dq], "-", color=TINTA2, lw=1.8)
    ejes[1].set_title("Mayor cambio de un valor Q en el episodio", loc="left")
    ejes[1].set_ylabel("|ΔQ| máximo")
    ejes[1].set_ylim(bottom=0)
    for ax in ejes:
        ax.set_xlabel("Episodio")
    fig.suptitle(f"Escenario {escenario}: convergencia de la Q-table", x=0.02, ha="left", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    guardar(fig, f"fig_{escenario}_qtable.png")

# ---------------- Figura 6: evaluacion intermedia de IPPO por semilla base ----------------
if politicas:
    variantes = [v for v in ("local", "vecinos", "spill", "cambio") if v in politicas]
    fig, ejes = plt.subplots(1, len(variantes), figsize=(5.2 * len(variantes), 3.9), squeeze=False, sharey=True)
    tope = 0
    for ax, v in zip(ejes[0], variantes):
        for base in sorted(politicas[v]["bases"]):
            filas_v = desde_ultimo_reinicio(leer_csv(f"resultados_{escenario}_ippo_{v}_s{base}.csv"))
            ev = [(int(f["episodio"]), numero(f["eval_timeloss"])) for f in filas_v
                  if numero(f.get("eval_timeloss")) is not None]
            mediana = base == politicas[v]["mediana"]
            ax.plot([e for e, _ in ev], [y for _, y in ev], "-o" if mediana else "-",
                    color=COLOR["ippo_" + v], lw=2.0 if mediana else 0.9, ms=3.5,
                    alpha=1.0 if mediana else 0.55, label=f"semilla base {base}" + (" (mediana)" if mediana else ""))
        for brazo in ("fijo", "actuado", "rl"):
            vals = valores_eval(brazo, "timeloss_prom")
            if vals:
                ax.axhline(statistics.mean(vals), color=COLOR[brazo], lw=1.3, label=NOMBRE[brazo])
                tope = max(tope, 2.5 * statistics.mean(vals))
        ax.set_title(NOMBRE["ippo_" + v], loc="left")
        ax.set_xlabel("Episodio de entrenamiento")
        ax.set_ylabel("Retraso con política congelada (s/veh)")
        ax.legend(fontsize=7, loc="upper right")
    if tope:
        ejes[0][0].set_ylim(0, tope)
    fig.suptitle(f"Escenario {escenario}: evaluación intermedia de IPPO (semilla 999) durante el entrenamiento; "
                 "líneas horizontales = media de los controles de referencia sobre las semillas de evaluación",
                 x=0.02, ha="left", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    guardar(fig, f"fig_{escenario}_curva_ippo.png")

# ---------------- Figura 7: fases por segundo (desfase emergente entre cruces) ----------------
fase_av = FASE_AVENIDA.get(escenario)
fases = {}
for b in brazos:
    for nombre in sorted(os.listdir(".")):
        if nombre.startswith(f"fases_{escenario}_{b}_s") and nombre.endswith(".csv"):
            fases[b] = leer_csv(nombre)
            break
if fases and fase_av is not None:
    t0, t1 = 600, 900                                   # minutos 10 a 15 del periodo punta O-E
    semaforos = [c for c in next(iter(fases.values()))[0] if c != "t"]
    alto = 0.55 * len(semaforos) * len(fases) + 0.6 * len(fases) + 0.8
    fig, ejes = plt.subplots(len(fases), 1, figsize=(10, alto), squeeze=False, sharex=True)
    for ax, (b, filas_f) in zip(ejes[:, 0], fases.items()):
        for k, tls in enumerate(semaforos):
            y = len(semaforos) - 1 - k
            for f in filas_f:
                t = int(f["t"])
                if t0 <= t < t1:
                    fase = int(f[tls])
                    if fase == fase_av:
                        ax.add_patch(plt.Rectangle((t / 60, y - 0.35), 1 / 60, 0.7, color=color_de(b), lw=0))
                    elif fase % 2 == 1:                 # fases impares = ambar en estos programas
                        ax.add_patch(plt.Rectangle((t / 60, y - 0.35), 1 / 60, 0.7, color=GRIS, lw=0))
        ax.set_yticks(range(len(semaforos)))
        ax.set_yticklabels([s.replace("semaforo_", "") for s in reversed(semaforos)])
        ax.set_ylim(-0.6, len(semaforos) - 0.4)
        ax.set_xlim(t0 / 60, t1 / 60)
        ax.set_title(nombre_de(b), loc="left", fontsize=9)
        ax.grid(False)
    ejes[-1, 0].set_xlabel("Minuto de la hora simulada")
    fig.suptitle(f"Escenario {escenario}: verde de la avenida (color) y ámbar (gris) en cada semáforo, "
                 "minutos 10 a 15, misma semilla de evaluación", x=0.02, ha="left", fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    guardar(fig, f"fig_{escenario}_fases.png")

# ---------------- Figura 8: spillback y saturacion (escenario de estres) ----------------
if evaluacion and any(numero(f.get("spillback_tasa")) for f in evaluacion):
    paneles = (("spillback_tasa", "Fracción de la hora con spillback", "fracción de segundos"),
               ("cola_max_enlace", "Cola máxima en un carril de enlace", "veh detenidos"),
               ("no_terminados", "Vehículos sin terminar a los 6000 s", "veh"))
    fig, ejes = plt.subplots(1, 3, figsize=(max(12, 2.2 * len(brazos) + 5), 4.0))
    for ax, (m, titulo, unidad) in zip(ejes, paneles):
        for i, b in enumerate(brazos):
            vals = valores_eval(b, m)
            if not vals:
                continue
            ax.plot([i] * len(vals), vals, "o", color=GRIS, ms=3.5, zorder=2)
            ax.errorbar(i, statistics.mean(vals), yerr=ic95(vals), fmt="o", color=color_de(b), ms=8,
                        capsize=4, lw=1.8, zorder=3)
        if m == "cola_max_enlace":
            ax.axhline(34, color=TINTA2, lw=0.9)
            ax.text(-0.45, 34.3, "umbral de spillback (34 de 38 plazas)", fontsize=7, color=TINTA2, va="bottom")
        ax.set_title(titulo, loc="left", fontsize=9)
        ax.set_ylabel(unidad)
        ax.set_xticks(range(len(brazos)))
        ax.set_xticklabels([nombre_de(b).replace(" (SUMO)", "").replace("IPPO ", "IPPO\n") for b in brazos],
                           fontsize=7.5)
        ax.set_xlim(-0.5, len(brazos) - 0.5)
        ax.set_ylim(bottom=0)
        ax.grid(axis="x", visible=False)
    fig.suptitle(f"Escenario {escenario}: spillback y saturación por control; puntos = una semilla, "
                 "marcador grande = media ± IC95 %", x=0.02, ha="left", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    guardar(fig, f"fig_{escenario}_spillback.png")
