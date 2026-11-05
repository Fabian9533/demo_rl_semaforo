"""
prueba_promocion.py - Prueba de p3_promocion.py con CSV sinteticos (no simula nada).

Uso (desde plan3/):  python pruebas/infra/prueba_promocion.py   -> pruebas/infra/prueba_promocion.txt
Casos: un candidato que baja 0.5 % no se promueve; uno que baja 1.5 % si; con semillas de mas o de menos falla.
"""
import os
import csv
import sys
import json
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN3 = os.path.dirname(os.path.dirname(AQUI))
TMP = os.path.join(PLAN3, "tmp_prueba_promocion")


def csv_sintetico(nombre, brazo, media, semillas=range(15009, 15025)):
    ruta = os.path.join(TMP, nombre)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["brazo", "semilla", "retraso_total_prom"])
        w.writeheader()
        for k, s in enumerate(semillas):
            w.writerow({"brazo": brazo, "semilla": s, "retraso_total_prom": media + (0.3 if k % 2 else -0.3)})
    return ruta


def correr(*args):
    return subprocess.run([sys.executable, os.path.join(PLAN3, "p3_promocion.py"), *args], capture_output=True,
                          text=True, cwd=TMP)


def main():
    os.makedirs(TMP, exist_ok=True)
    v2 = csv_sintetico("v2.csv", "ippo_vecinos_p3v2regmed_s2042", 20.0)
    a = csv_sintetico("a.csv", "ippo_vecinos_p3obsmed_s42", 19.9)
    b = csv_sintetico("b.csv", "ippo_vecinos_p3completomed_s4042", 19.7)
    lineas, malos = [], 0

    def revisar(desc, cond):
        nonlocal malos
        malos += not cond
        lineas.append(f"{'ok ' if cond else 'MAL'} {desc}")
    r = correr("decidir", "--celda", "x", "--v2", v2, "--candidatos", a, "--salida", "x1.json")
    d = json.load(open(os.path.join(TMP, "x1.json"), encoding="utf-8"))
    revisar("-0.5 % no se promueve: se cita V2", r.returncode == 0 and not d["promovido"]
            and d["modelo_citado"] == "ippo_vecinos_p3v2regmed_s2042")
    r = correr("decidir", "--celda", "x", "--v2", v2, "--candidatos", f"{a},{b}", "--salida", "x2.json")
    d = json.load(open(os.path.join(TMP, "x2.json"), encoding="utf-8"))
    revisar("-1.5 % se promueve", r.returncode == 0 and d["promovido"]
            and d["modelo_citado"] == "ippo_vecinos_p3completomed_s4042")
    malo = csv_sintetico("malo.csv", "otro", 15.0, semillas=range(15009, 15026))
    r = correr("decidir", "--celda", "x", "--v2", v2, "--candidatos", malo, "--salida", "x3.json")
    revisar("una semilla de mas: falla", r.returncode != 0)
    malo = csv_sintetico("malo2.csv", "otro", 15.0, semillas=range(15009, 15024))
    r = correr("decidir", "--celda", "x", "--v2", v2, "--candidatos", malo, "--salida", "x4.json")
    revisar("una semilla de menos: falla", r.returncode != 0)
    r = correr("juntar", "--entradas", "x1.json,x2.json", "--salida", "promocion.json")
    revisar("juntar", r.returncode == 0)
    texto = "\n".join(lineas)
    print(texto)
    open(os.path.join(AQUI, "prueba_promocion.txt"), "w", encoding="utf-8").write(texto + "\n")
    sys.exit(1 if malos else 0)


if __name__ == "__main__":
    main()
