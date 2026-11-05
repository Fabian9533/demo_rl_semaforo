"""
medir_costo_p6.py - Costo de --obs-cercana 75 en P6 (malla3_alta), medido otra vez y con mas parejas (revision del
05.11). La misma medicion que prueba_etapa3 (trabajo_e3.py costo: el mismo episodio sin y con, alternados en un
proceso), con IPPO entregado (base 42), semilla de humo 424301 y N parejas (por defecto 5). Sirve para ver cuanto
depende la razon de la carga de la maquina: se anota cuantos sumo corrian al empezar.

Uso:  python plan3/pruebas/ent/medir_costo_p6.py [N]
Salida: plan3/pruebas/ent/salidas/costo_p6.txt (se agrega una linea por medicion)
"""
import sys
import json
import time
import shutil
import subprocess

import util_ent as u

P6 = u.PLAN3 / "insumos" / "entregado" / "politica_malla3_alta_vecinos_s42"


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    c = u.carpeta("costo_p6", ["malla3_alta"])
    for ext in (".pt", ".json"):
        shutil.copyfile(f"{P6}{ext}", c / (P6.name + ext))
    p = {"escenario": "malla3_alta", "semilla": 424301, "obs_cercana": 75, "repeticiones": n,
         "decisor": {"tipo": "politica", "ruta": P6.name + ".pt"}}
    (c / "p.json").write_text(json.dumps(p), encoding="utf-8")
    tareas = subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower()
    sumos = tareas.count("sumo.exe")
    t0 = time.strftime("%d.%m.%Y %H:%M")
    cod = u.correr(u.AQUI / "trabajo_e3.py", ["costo", "p.json", "salida.json"], c, c / "log.txt")
    if cod != 0:
        sys.exit(f"trabajo_e3 costo salio con {cod}")
    d = json.loads((c / "salida.json").read_text(encoding="utf-8"))
    linea = (f"{t0}: {n} parejas, {sumos} sumo corriendo al empezar; sin {[round(x, 1) for x in d['sin']]} s, con "
             f"{[round(x, 1) for x in d['con']]} s; razones {[round(x, 2) for x in d['razones']]}; mediana "
             f"{d['mediana']:.2f}")
    print(linea)
    u.SALIDAS.mkdir(parents=True, exist_ok=True)
    with open(u.SALIDAS / "costo_p6.txt", "a", encoding="utf-8") as f:
        f.write(linea + "\n")


if __name__ == "__main__":
    main()
