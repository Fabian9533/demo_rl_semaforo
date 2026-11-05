"""
p3_elegir.py - Pasos de eleccion del bloque plan3 (PLAN3 0.19 y 3b; DECISIONES B5 y B21; prerregistro §6).

Uso (desde plan3/):
  python p3_elegir.py regla --escenario ESC --corrida TAG --regla vieja|piso200|cada20 --etiqueta ET [--origen DIR]
      Re-elige un checkpoint dentro de una corrida ya entrenada y lo publica como
      politica_<ESC>_<variante>_<ET>_s<base>.pt/.json (mismos tensores; la etiqueta ET va en el meta):
        vieja    la regla del 25.09: menor timeLoss medio en 999 y 1999, entre todos los checkpoints (V2 vieja);
        piso200  menor retraso total medio (16 semillas) entre los checkpoints <= 200 ("200 con piso");
        cada20   menor retraso total medio entre los episodios 20, 40, ..., 400 ("400 eligiendo entre 20").
  python p3_elegir.py mediana --politicas A.pt,B.pt,C.pt --etiqueta ET --salida politica_<esc>_<var>_<ET>.pt
      Version evaluada: la base mediana por val_elegido (la 3.a de 5, la 2.a de 3; empate, la base menor; con un
      numero par, la peor de las dos centrales). Publica una copia con la etiqueta ET y la lista de candidatas.
En todos los casos el empate entre checkpoints es el de rl_ippo.elegir_checkpoint (el mas tardio).
"""
import os
import sys
import json
import shutil
import argparse

import numpy as np

PLAN3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(PLAN3))


def elegir_checkpoint(val_serie):
    """La de rl_ippo (copiada para no importar SUMO): fila de menor ultimo valor; empate, la mas tardia."""
    return min(reversed(val_serie), key=lambda f: f[-1])


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def publicar(origen_pt, meta, destino_pt):
    """Copia el .pt (mismos bytes, mismos tensores) y escribe su meta junto a el."""
    tmp = f"{destino_pt}.{os.getpid()}.tmp"
    shutil.copyfile(origen_pt, tmp)
    os.replace(tmp, destino_pt)
    destino_json = destino_pt[:-3] + ".json"
    tmp = f"{destino_json}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
    os.replace(tmp, destino_json)


def regla(a):
    carpeta = a.origen
    prefijo = a.corrida + "_ep"
    eps = sorted(int(n[len(prefijo):len(prefijo) + 3]) for n in os.listdir(carpeta)
                 if n.startswith(prefijo) and n.endswith(".json") and not n.endswith(".estado.json"))
    if a.regla == "piso200":
        eps = [e for e in eps if e <= 200]
    elif a.regla == "cada20":
        eps = [e for e in eps if e % 20 == 0]
    if not eps:
        sys.exit(f"no hay checkpoints de {a.corrida} para la regla {a.regla}")
    serie, metas = [], {}
    for ep in eps:
        m = leer(os.path.join(carpeta, f"{a.corrida}_ep{ep:03d}.json"))
        metas[ep] = m
        if a.regla == "vieja":
            v = [m["val_999"], m["val_1999"]]
            serie.append([ep] + v + [round(float(np.mean(v)), 3)])
        else:
            semillas = m["val_seeds"]
            serie.append([ep] + [m[f"val_total_{s}"] for s in semillas] + [m["val_total_checkpoint"]])
    elegido = elegir_checkpoint(serie)
    ep = elegido[0]
    meta = dict(metas[ep])
    meta.update({"etiqueta": a.etiqueta, "ep_elegido": ep, "val_elegido": elegido[-1], "regla_eleccion": a.regla,
                 "corrida_origen": a.corrida, "serie_eleccion": serie,
                 "criterio_validacion": ("timeLoss medio en 999 y 1999 (regla del 25.09)" if a.regla == "vieja"
                                         else "retraso total medio en las semillas de validacion")})
    destino = f"politica_{a.escenario}_{meta['variante']}_{a.etiqueta}_s{meta['base']}.pt"
    publicar(os.path.join(carpeta, f"{a.corrida}_ep{ep:03d}.pt"), meta, destino)
    print(f"{a.corrida}: regla {a.regla}, elegido ep{ep:03d} entre {len(eps)}; publicado {destino}")


def mediana(a):
    rutas = a.politicas.split(",")
    cand = []
    for r in rutas:
        m = leer(r[:-3] + ".json")
        if m.get("val_elegido") is None:
            sys.exit(f"{r} no tiene val_elegido")
        cand.append((m["val_elegido"], m["base"], r, m))
    cand.sort(key=lambda x: (x[0], x[1]))            # empate: la base menor primero
    n = len(cand)
    k = n // 2                                     # impar: la central; par: la peor de las dos centrales
    val, base, ruta, meta = cand[k]
    meta = dict(meta)
    meta.update({"etiqueta": a.etiqueta, "version_evaluada": True, "base_elegida": base,
                 "candidatas": [{"base": b, "val_elegido": v, "politica": r} for v, b, r, _ in cand]})
    publicar(ruta, meta, a.salida)
    print(f"version evaluada: base {base} (val_elegido {val}) entre {[(b, v) for v, b, _, _ in cand]}; "
          f"publicada {a.salida}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["regla", "mediana"])
    ap.add_argument("--escenario")
    ap.add_argument("--corrida")
    ap.add_argument("--regla", choices=["vieja", "piso200", "cada20"])
    ap.add_argument("--origen", default="checkpoints", help="carpeta de los checkpoints de la corrida")
    ap.add_argument("--politicas")
    ap.add_argument("--etiqueta", required=True)
    ap.add_argument("--salida")
    a = ap.parse_args()
    if a.modo == "regla":
        assert a.escenario and a.corrida and a.regla, "regla necesita --escenario, --corrida y --regla"
        regla(a)
    else:
        assert a.politicas and a.salida, "mediana necesita --politicas y --salida"
        mediana(a)


if __name__ == "__main__":
    main()
