"""
prueba_no_regresion.py - Prueba de la tarea 0.12 (DECISIONES B13): despues de tocar evaluar.py, rl_corredor.py y
comun.py, los controles entregados repiten digito a digito sus CSV entregados.
  fijo, actuado, ciclo minimo (trivial) y la politica IPPO con mensajes publicada de la base 42, en P1-P6, con las
  semillas de no regresion 1001-1002, por evaluar.py (la linea de comandos de siempre), frente a las filas 1001 y
  1002 de las copias entregadas (insumos/puente/eval_<esc>_<brazo>.csv): todas las columnas, como texto.
  Y veredicto.py --probar pasa (solo escribe en carpetas temporales del sistema).
Corre en una copia (tmp_ref/no_regresion/): los brazos actuado y trivial regeneran su .add.xml en la carpeta actual.
Hasta 3 evaluaciones a la vez. Uso (cwd = plan3/): python pruebas/ref/prueba_no_regresion.py
Salida: pruebas/ref/salidas/prueba_no_regresion.txt
"""
import os
import sys
import csv
import subprocess
import concurrent.futures

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
inf = up.Informe("prueba_no_regresion")
CASOS = {"P1": "corredor", "P2": "corredor_alta", "P3": "red", "P4": "red_alta", "P5": "malla3",
         "P6": "malla3_alta"}
CARPETA = up.copia("no_regresion", list(CASOS.values()))
PUENTE = os.path.join(up.PLAN3, "insumos", "puente")
ENTREGADO = os.path.join(up.PLAN3, "insumos", "entregado")
SEMILLAS = ("1001", "1002")


def evaluar(esc, brazo):
    salida = os.path.join(CARPETA, f"nr_{esc}_{brazo}.csv")
    cmd = [sys.executable, os.path.join(up.RAIZ, "evaluar.py"), "--escenario", esc, "--semillas", "1001-1002",
           "--salida", salida, "--extras", os.path.join(CARPETA, f"extras_{esc}_{brazo}")]
    if brazo.startswith("ippo"):
        cmd += ["--politica", os.path.join(ENTREGADO, f"politica_{esc}_vecinos_s42.pt")]
    else:
        cmd += ["--brazo", brazo]
    r = subprocess.run(cmd, cwd=CARPETA, capture_output=True, text=True)
    return esc, brazo, r.returncode, salida, r.stdout[-1500:] + r.stderr[-1500:]


def comparar(esc, brazo, salida):
    with open(os.path.join(PUENTE, f"eval_{esc}_{brazo}.csv"), newline="", encoding="utf-8") as f:
        ref = {fila["semilla"]: fila for fila in csv.DictReader(f) if fila["semilla"] in SEMILLAS}
    with open(salida, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    distintas = []
    for fila in filas:
        r = ref[fila["semilla"]]
        distintas += [(fila["semilla"], k, fila[k], r.get(k)) for k in r if fila.get(k) != r[k]]
    return len(filas) == 2 and set(ref) == set(SEMILLAS) and not distintas, distintas, \
        len(filas[0]) if filas else 0


def main():
    inf(f"No regresion de lo entregado (copia en {CARPETA}): semillas 1001-1002, CSV de insumos/puente")
    trabajos = [(esc, brazo) for esc in CASOS.values() for brazo in ("fijo", "actuado", "trivial",
                                                                      "ippo_vecinos_s42")]
    # cada .add.xml (actuado, trivial) lo escribe una sola evaluacion a la vez (la carrera es prueba_atomica)
    with concurrent.futures.ThreadPoolExecutor(3) as ex:
        resultados = list(ex.map(lambda t: evaluar(*t), trabajos))
    total = 0
    for esc, brazo, cod, salida, texto in resultados:
        caso = next(k for k, v in CASOS.items() if v == esc)
        if cod != 0:
            inf.chequeo(False, f"{caso} {brazo}: evaluar.py termino con codigo {cod}\n{texto}")
            continue
        ok, distintas, columnas = comparar(esc, brazo, salida)
        total += ok
        inf.chequeo(ok, f"{caso} {brazo}: 1001 y 1002 iguales a lo entregado en las {columnas} columnas"
                        + (f"; distintas: {distintas[:6]}" if distintas else ""))
    inf(f"  {total} de {len(trabajos)} brazos iguales")
    r = subprocess.run([sys.executable, os.path.join(up.RAIZ, "veredicto.py"), "--probar"], cwd=up.PLAN3,
                       capture_output=True, text=True)
    inf.chequeo(r.returncode == 0 and "todas las pruebas pasan" in r.stdout,
                f"veredicto.py --probar (cwd plan3/): codigo {r.returncode}; {r.stdout.strip()[-120:]}")
    os.chdir(up.PLAN3)
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
