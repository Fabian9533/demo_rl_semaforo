"""
avance.py - Muestra en que va la demanda alta del corredor (o la carpeta que se le pase). Solo lee los logs.

Uso (desde demo_rl/lima/corredor):
  python avance.py            # demanda alta (carpeta alta/)
  python avance.py .          # demanda publicada
"""
import glob
import os
import re
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
EPISODIOS = {"completo": 400, "corregido": 200, "sinmsg": 200}


def ultimas(ruta, n=1, filtro=None):
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8", errors="replace") as f:
        lineas = [l.rstrip() for l in f if "Retrying" not in l and "Could not connect" not in l]
    if filtro:
        lineas = [l for l in lineas if filtro(l)]
    return lineas[-n:]


def main():
    carpeta = os.path.join(AQUI, sys.argv[1] if len(sys.argv) > 1 else "alta")
    logs = os.path.join(carpeta, "logs")
    print(time.strftime("Hora: %d.%m %H:%M"), "-", os.path.relpath(carpeta, AQUI))

    print("\n1. Referencias (fijo y actuado ajustados):")
    hitos = ultimas(os.path.join(logs, "referencias.log"), 4,
                    lambda l: l.startswith(("Fijo ajustado", "Actuado ajustado", "paso")) or "validacion" in l)
    for l in hitos:
        print("   ", l[:150])
    listo = os.path.exists(os.path.join(carpeta, "salidas", "val_referencias.json"))
    print("    ->", "LISTAS" if listo else "en curso; ultima medicion: "
          + (ultimas(os.path.join(logs, "referencias.log"))[0].strip()[:110] if hitos else "---"))

    print("\n2. Entrenamientos (episodio actual / total, y cuanto falta):")
    for modelo, total in EPISODIOS.items():
        for base in (42, 2042, 4042):
            l = ultimas(os.path.join(logs, f"{modelo}_s{base}.log"), 1, lambda x: x.startswith("Ep "))
            if not l:
                print(f"    {modelo}_s{base}: sin empezar")
                continue
            ep = int(l[0].split()[1])
            seg = re.search(r"([\d.]+)s  minor", l[0])
            falta = (total - ep) * float(seg.group(1)) / 60 if seg else 0
            estado = "TERMINADO" if ep >= total else f"faltan ~{falta:.0f} min"
            print(f"    {modelo:9s} base {base:<5d} {ep:3d}/{total}  {estado}")

    print("\n3. Evaluacion (dos tandas de 100 semillas):")
    hechos = sorted(os.path.basename(r)[5:-4] for r in glob.glob(os.path.join(carpeta, "salidas", "eval_t*_*.csv")))
    print("    ", ", ".join(hechos) if hechos else "sin empezar (arranca sola cuando esten 1 y 2)")
    for l in ultimas(os.path.join(logs, "evaluar.log"), 3):
        print("   ", l[:150])


if __name__ == "__main__":
    main()
