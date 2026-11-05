"""
prueba_no_regresion.py - Prueba de la tarea 0.12 (DECISIONES B13): despues de tocar evaluar.py, rl_corredor.py y
comun.py, los controles entregados repiten digito a digito sus CSV entregados.
  fijo, actuado, ciclo minimo (trivial) y la politica IPPO con mensajes publicada de la base 42, en P1-P6, con las
  semillas de no regresion 1001-1002, por evaluar.py (la linea de comandos de siempre), frente a las filas 1001 y
  1002 de las copias entregadas (insumos/puente/eval_<esc>_<brazo>.csv): todas las columnas, como texto.
  Y veredicto.py --probar pasa (solo escribe en carpetas temporales del sistema).
La salida empieza con el codigo con que se corrio: commit y sha256 de comun.py, rl_ippo.py, evaluar.py y
rl_corredor.py (util_pruebas.cabecera_codigo). Diferencia conocida: IPPO con mensajes en P6 da cambios_fase 4 menos que
el CSV entregado en cada semilla, con las otras columnas iguales; prueba_nr_p6.py muestra que el codigo entregado
corrido hoy da lo mismo y que la diferencia viene de la plantilla con que se corrio ese CSV. Se informa aparte como
"conocida": cualquier otra diferencia, o esa con otro tamano, es una falla.
Corre en una copia (tmp_ref/no_regresion/): los brazos actuado y trivial regeneran su .add.xml en la carpeta actual.
Uso (cwd = plan3/): python pruebas/ref/prueba_no_regresion.py [--procesos 3]   (de 21:00 a 07:30, --procesos 2)
Salida: pruebas/ref/salidas/prueba_no_regresion.txt
"""
import os
import sys
import csv
import argparse
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
CONOCIDA = ("malla3_alta", "ippo_vecinos_s42", "cambios_fase", 4)     # (escenario, brazo, columna, entregado - hoy)


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


def conocida(esc, brazo, distintas):
    """True si las diferencias son solo la conocida de P6 IPPO (cambios_fase, entregado = hoy + 4, en cada semilla)."""
    e, b, columna, delta = CONOCIDA
    return (esc, brazo) == (e, b) and len(distintas) == len(SEMILLAS) and all(
        k == columna and int(entregado) - int(hoy) == delta for _, k, hoy, entregado in distintas)


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--procesos", type=int, default=3, help="evaluaciones a la vez (de 21:00 a 07:30, 2)")
    args = ap.parse_args()
    for linea in up.cabecera_codigo():
        inf(linea)
    inf(f"No regresion de lo entregado (copia en {CARPETA}): semillas 1001-1002, CSV de insumos/puente; "
        f"{args.procesos} evaluaciones a la vez")
    trabajos = [(esc, brazo) for esc in CASOS.values() for brazo in ("fijo", "actuado", "trivial",
                                                                      "ippo_vecinos_s42")]
    # cada .add.xml (actuado, trivial) lo escribe una sola evaluacion a la vez (la carrera es prueba_atomica)
    with concurrent.futures.ThreadPoolExecutor(args.procesos) as ex:
        resultados = list(ex.map(lambda t: evaluar(*t), trabajos))
    total = 0
    for esc, brazo, cod, salida, texto in resultados:
        caso = next(k for k, v in CASOS.items() if v == esc)
        if cod != 0:
            inf.chequeo(False, f"{caso} {brazo}: evaluar.py termino con codigo {cod}\n{texto}")
            continue
        ok, distintas, columnas = comparar(esc, brazo, salida)
        total += ok
        if not ok and conocida(esc, brazo, distintas):
            inf.chequeo(True, f"{caso} {brazo}: 1001 y 1002 iguales a lo entregado salvo la diferencia CONOCIDA "
                              f"(cambios_fase, entregado = hoy + 4; prueba_nr_p6.py): {distintas}")
            continue
        inf.chequeo(ok, f"{caso} {brazo}: 1001 y 1002 iguales a lo entregado en las {columnas} columnas"
                        + (f"; distintas: {distintas[:6]}" if distintas else ""))
    inf(f"  {total} de {len(trabajos)} brazos iguales en todas las columnas (y P6 IPPO con la diferencia conocida)")
    r = subprocess.run([sys.executable, os.path.join(up.RAIZ, "veredicto.py"), "--probar"], cwd=up.PLAN3,
                       capture_output=True, text=True)
    inf.chequeo(r.returncode == 0 and "todas las pruebas pasan" in r.stdout,
                f"veredicto.py --probar (cwd plan3/): codigo {r.returncode}; {r.stdout.strip()[-120:]}")
    os.chdir(up.PLAN3)
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
