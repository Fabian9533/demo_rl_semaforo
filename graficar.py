"""Grafica la curva de aprendizaje de un escenario (requiere matplotlib).

Uso: python graficar.py [cruce|cruce2|corredor]   (por defecto: cruce)
Lee resultados_<escenario>.csv y guarda curva_aprendizaje_<escenario>.png
"""
import csv
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

escenario = sys.argv[1] if len(sys.argv) > 1 else "cruce"
entrada = f"resultados_{escenario}.csv"
salida = f"curva_aprendizaje_{escenario}.png"

filas = list(csv.DictReader(open(entrada)))
train = [f for f in filas if f["modo"] == "train"]
base = [f for f in filas if f["modo"] == "baseline"]

# el CSV es un historial: si acumula varias corridas de entrenamiento
# (el numero de episodio se reinicia), graficar solo la ultima
inicio = 0
for i in range(1, len(train)):
    if int(train[i]["episodio"]) <= int(train[i - 1]["episodio"]):
        inicio = i
train = train[inicio:]
ep = [int(f["episodio"]) for f in train]
espera = [float(f["espera_prom"]) for f in train]
cola = [float(f["cola_prom"]) for f in train]

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].plot(ep, espera, marker="o", label="Q-learning")
if base:
    ax[0].axhline(float(base[-1]["espera_prom"]), color="red", linestyle="--", label="Tiempo fijo")
ax[0].set_xlabel("Episodio"); ax[0].set_ylabel("Espera promedio por vehiculo (s)"); ax[0].legend(); ax[0].grid(alpha=.3)
ax[1].plot(ep, cola, marker="o", label="Q-learning")
if base:
    ax[1].axhline(float(base[-1]["cola_prom"]), color="red", linestyle="--", label="Tiempo fijo")
ax[1].set_xlabel("Episodio"); ax[1].set_ylabel("Cola promedio (vehiculos detenidos)"); ax[1].legend(); ax[1].grid(alpha=.3)
fig.suptitle(f"Escenario: {escenario}")
plt.tight_layout(); plt.savefig(salida, dpi=150)
print(f"Guardado {salida}")
