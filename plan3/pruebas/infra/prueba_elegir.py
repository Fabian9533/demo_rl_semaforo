"""
prueba_elegir.py - Prueba de p3_elegir.py con lo entregado (PLAN3 0.19).

Uso (desde plan3/):  python pruebas/infra/prueba_elegir.py
  1. regla vieja (timeLoss medio en 999 y 1999) sobre los checkpoints entregados de las 18 celdas x 3 bases: elige el
     mismo episodio que la politica publicada entonces, y la publicada nueva tiene los mismos tensores;
  2. mediana: la base que elige coincide con veredicto.base_mediana en las 18 celdas; con 4 bases, la peor central.
Salida: pruebas/infra/prueba_elegir.txt (trabaja en tmp_prueba_elegir/). Sale con 1 si algo no da lo esperado.
"""
import os
import sys
import json
import subprocess

import torch

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN3 = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.dirname(PLAN3))
import veredicto          # noqa: E402  (solo su funcion pura base_mediana)

TMP = os.path.join(PLAN3, "tmp_prueba_elegir")
CELDAS = ["corredor", "corredor_alta", "red", "red_alta", "malla3", "malla3_alta", "dem_corredor_t905",
          "dem_corredor_t1358", "dem_corredor_t2715", "dem_red_t905", "dem_red_t1358", "dem_red_t1810",
          "dem_red_t2715", "dem_red_t3620", "dem_malla3_t1810", "dem_malla3_t2715", "dem_malla3_t3620",
          "dem_malla3_t6525"]
BASES = [42, 2042, 4042]


def leer(r):
    with open(r, encoding="utf-8") as f:
        return json.load(f)


def main():
    os.makedirs(TMP, exist_ok=True)
    for a in os.listdir(TMP):                    # se vacia (la carpeta puede estar abierta por otro proceso)
        os.remove(os.path.join(TMP, a))
    elegir = os.path.join(PLAN3, "p3_elegir.py")
    lineas, malos = [], 0
    iguales = 0
    for e in CELDAS:
        for b in BASES:
            subprocess.run([sys.executable, elegir, "regla", "--escenario", e, "--corrida", f"{e}_ippo_vecinos_s{b}",
                            "--regla", "vieja", "--etiqueta", "p3prueba", "--origen",
                            os.path.join(PLAN3, "insumos", "c0_checkpoints")], cwd=TMP, check=True,
                           capture_output=True)
            nueva = leer(os.path.join(TMP, f"politica_{e}_vecinos_p3prueba_s{b}.json"))
            entregada = leer(os.path.join(PLAN3, "insumos", "entregado", f"politica_{e}_vecinos_s{b}.json"))
            a = torch.load(os.path.join(PLAN3, "insumos", "entregado", f"politica_{e}_vecinos_s{b}.pt"),
                           weights_only=True)
            c = torch.load(os.path.join(TMP, f"politica_{e}_vecinos_p3prueba_s{b}.pt"), weights_only=True)
            ok = (nueva["ep_elegido"] == entregada["ep_elegido"] and nueva["etiqueta"] == "p3prueba"
                  and a.keys() == c.keys() and all(torch.equal(a[k], c[k]) for k in a))
            iguales += ok
            if not ok:
                lineas.append(f"MAL regla vieja {e} s{b}: {nueva['ep_elegido']} frente a {entregada['ep_elegido']}")
    lineas.append(f"regla vieja: {iguales} de {len(CELDAS) * len(BASES)} iguales a lo publicado (episodio y tensores)")
    malos += len(CELDAS) * len(BASES) - iguales
    bien = 0
    for e in CELDAS:
        rutas = [os.path.join(PLAN3, "insumos", "entregado", f"politica_{e}_vecinos_s{b}.pt") for b in BASES]
        salida = os.path.join(TMP, f"politica_{e}_vecinos_p3med.pt")
        subprocess.run([sys.executable, elegir, "mediana", "--politicas", ",".join(rutas), "--etiqueta", "p3med",
                        "--salida", salida], cwd=TMP, check=True, capture_output=True)
        vals = {b: leer(r[:-3] + ".json")["val_elegido"] for b, r in zip(BASES, rutas)}
        bien += leer(salida[:-3] + ".json")["base_elegida"] == veredicto.base_mediana(vals)
    lineas.append(f"mediana: {bien} de {len(CELDAS)} iguales a veredicto.base_mediana")
    malos += len(CELDAS) - bien
    # 4 bases (una caida): la peor de las dos centrales
    rutas = [os.path.join(PLAN3, "insumos", "entregado", f"politica_{e}_vecinos_s42.pt") for e in CELDAS[:4]]
    vals = sorted((leer(r[:-3] + ".json")["val_elegido"], leer(r[:-3] + ".json")["base"], r) for r in rutas)
    salida = os.path.join(TMP, "politica_cuatro_p3med.pt")
    subprocess.run([sys.executable, elegir, "mediana", "--politicas", ",".join(rutas), "--etiqueta", "p3med",
                    "--salida", salida], cwd=TMP, check=True, capture_output=True)
    ok = leer(salida[:-3] + ".json")["candidatas"][2]["politica"] == vals[2][2]
    lineas.append(f"{'ok ' if ok else 'MAL'} con 4 candidatas elige la peor de las dos centrales")
    malos += not ok
    texto = "\n".join(lineas)
    print(texto)
    with open(os.path.join(AQUI, "prueba_elegir.txt"), "w", encoding="utf-8") as f:
        f.write(texto + "\n")
    sys.exit(1 if malos else 0)


if __name__ == "__main__":
    main()
