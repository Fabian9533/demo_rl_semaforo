"""
prueba_nr_p6.py - Por que en la no regresion (prueba_no_regresion.py) IPPO con mensajes en P6 difiere del CSV
entregado solo en cambios_fase (+4 en 1001 y en 1002) con las otras 33 columnas iguales.
  1. El codigo entregado (223f908: evaluar.py, rl_corredor.py, rl_ippo.py, comun.py y escenarios_plan2.py sacados
     con git show a tmp_ref/codigo_entregado/) corrido hoy da lo mismo que el codigo de esta rama, columna por columna:
     entonces la diferencia no es una regresion de 0.7-0.11.
  2. Hipotesis: el CSV entregado se corrio con otra plantilla <esc>.add.xml. IPPO pone cada semaforo en su primera
     fase verde al empezar, asi que la plantilla no cambia el trafico; pero el conteo de cambios de fase compara con la
     fase inicial de la plantilla (la suscripcion se lee antes del setPhase): cada semaforo que la plantilla arranca
     fuera de esa fase suma un cambio. Con el 15/10 en ajedrez (4 semaforos desfasados medio ciclo) se espera
     exactamente +4 y el resto igual.
Semillas de no regresion 1001-1002, solo controles entregados. Uso (cwd = plan3/), despues de
prueba_no_regresion.py: python pruebas/ref/prueba_nr_p6.py    Salida: pruebas/ref/salidas/prueba_nr_p6.txt
"""
import os
import sys
import csv
import shutil
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
inf = up.Informe("prueba_nr_p6")
NR = os.path.join(up.TMP, "no_regresion")
CODIGO = os.path.join(up.TMP, "codigo_entregado")
POLITICA = os.path.join(up.PLAN3, "insumos", "entregado", "politica_malla3_alta_vecinos_s42.pt")
PUENTE = os.path.join(up.PLAN3, "insumos", "puente", "eval_malla3_alta_ippo_vecinos_s42.csv")


def leer(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return {fila["semilla"]: fila for fila in csv.DictReader(f) if fila["semilla"] in ("1001", "1002")}


def distintas(a, b):
    return [(s, k, a[s][k], b[s].get(k)) for s in sorted(a) for k in a[s] if a[s][k] != b[s].get(k)]


def evaluar(script, carpeta, salida):
    r = subprocess.run([sys.executable, script, "--escenario", "malla3_alta", "--politica", POLITICA, "--semillas",
                        "1001-1002", "--salida", salida, "--extras", os.path.join(carpeta, "extras_nr_p6")],
                       cwd=carpeta, capture_output=True, text=True)
    if r.returncode != 0:
        inf(r.stdout[-1500:] + r.stderr[-1500:])
    return r.returncode


def main():
    mia = os.path.join(NR, "nr_malla3_alta_ippo_vecinos_s42.csv")
    if not os.path.exists(mia):
        raise SystemExit("Corra antes pruebas/ref/prueba_no_regresion.py")
    os.makedirs(CODIGO, exist_ok=True)
    for f in ("evaluar.py", "rl_corredor.py", "rl_ippo.py", "comun.py", "escenarios_plan2.py"):
        texto = subprocess.run(["git", "show", f"223f908:{f}"], cwd=up.RAIZ, capture_output=True, text=True,
                               encoding="utf-8").stdout
        with open(os.path.join(CODIGO, f), "w", encoding="utf-8", newline="\n") as g:
            g.write(texto)
    inf("IPPO con mensajes (base 42) en P6, semillas 1001-1002")
    ent = os.path.join(NR, "nr_p6_codigo_entregado.csv")
    cod = evaluar(os.path.join(CODIGO, "evaluar.py"), NR, ent)
    d = distintas(leer(ent), leer(mia)) if cod == 0 else ["sin correr"]
    inf.chequeo(cod == 0 and not d, f"1 codigo entregado (223f908) corrido hoy = codigo de esta rama en las 34 "
                                    f"columnas: {not d} {d[:4]}")
    d_puente = distintas(leer(PUENTE), leer(mia))
    inf(f"  frente al CSV entregado (insumos/puente): {d_puente}")
    # 2. la plantilla de P6 cambiada por el 15/10 en ajedrez, en una copia del escenario
    alt = os.path.join(up.TMP, "nr_p6_ajedrez")
    os.makedirs(alt, exist_ok=True)
    for f in up.archivos_de_cfg(os.path.join(NR, "malla3_alta.sumocfg")):
        shutil.copyfile(os.path.join(NR, f), os.path.join(alt, f))
    os.chdir(alt)
    import barrer_fino as bfn
    c = bfn.Celda("malla3_alta", prefijos=())
    pl = c.plan(15, 10, c.desfases_esquema(c.p.ciclo(15, 10), "ajedrez"), "ajedrez")
    c.escribir_plan("malla3_alta.add.xml", pl)
    os.chdir(up.PLAN3)
    salida = os.path.join(alt, "nr_p6_ajedrez.csv")
    cod = evaluar(os.path.join(up.RAIZ, "evaluar.py"), alt, salida)
    d2 = distintas(leer(salida), leer(PUENTE)) if cod == 0 else ["sin correr"]
    inf.chequeo(cod == 0 and not d2, f"2 con la plantilla 15/10 en ajedrez ({pl['offsets']}) sale igual al CSV "
                                     f"entregado en las 34 columnas: {not d2} {d2[:4]}")
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
