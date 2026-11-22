"""citado.py - Estudio 2 del corredor: la politica citada de un modelo en una carpeta, la base con la validacion
mediana (val_elegido de su meta), como en el estudio (lima/REGISTRO.md). Imprime la ruta del .pt.
Uso:  python citado.py <carpeta> <variante>_<etiqueta>      p. ej.  python citado.py demo_rl/lima/corredor vecinos_completo
"""
import json
import os
import sys

carpeta, nombre = sys.argv[1], sys.argv[2]
vals = []
for base in (42, 2042, 4042):
    with open(os.path.join(carpeta, f"politica_benavides_{nombre}_s{base}.json"), encoding="utf-8") as f:
        vals.append((json.load(f)["val_elegido"], base))
vals.sort()
print(os.path.join(os.path.abspath(carpeta), f"politica_benavides_{nombre}_s{vals[1][1]}.pt").replace("\\", "/"))
