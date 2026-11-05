"""
p3_promocion.py - Regla de promocion: que modelo se cita en cada celda (prerregistro §12; PLAN3 3.5; DECISIONES B25).

Uso (desde plan3/):
  python p3_promocion.py decidir --celda NOMBRE --v2 V2.csv --candidatos A.csv,B.csv --salida promocion/<celda>.json
  python p3_promocion.py juntar --entradas promocion/a.json,... --salida promocion.json

decidir: cada CSV es la evaluacion (evaluar3.py, uso "promocion") de la version evaluada entre las bases 42, 2042 y
  4042 de un candidato, en las 16 semillas de promocion 15009-15024, que nunca se usaron para elegir checkpoints.
  Gana el de menor retraso total medio, solo si le gana a V2 por al menos 1 %; si no, el modelo citado es V2.
  Exige las mismas 16 semillas en todos los CSV (ni una de mas ni de menos).
juntar: une las decisiones de todas las celdas en promocion.json con el sha256 de cada archivo; se registra antes de
  listo/cierre.ok.
Usa solo validacion: el examen sigue limpio.
"""
import os
import csv
import sys
import json
import hashlib
import argparse

SEMILLAS = list(range(15009, 15025))
MARGEN = -1.0           # % frente a V2: el candidato debe bajar el retraso total al menos 1 %


def leer(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    semillas = sorted(int(r["semilla"]) for r in filas)
    if semillas != SEMILLAS:
        sys.exit(f"{ruta}: semillas {semillas[:3]}... ({len(semillas)}); se esperaban 15009-15024")
    brazos = {r["brazo"] for r in filas}
    if len(brazos) != 1:
        sys.exit(f"{ruta}: mas de un brazo: {brazos}")
    media = sum(float(r["retraso_total_prom"]) for r in filas) / len(filas)
    return brazos.pop(), media


def sha(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def escribir(ruta, datos):
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    tmp = f"{ruta}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=1, ensure_ascii=False)
    os.replace(tmp, ruta)


def decidir(a):
    brazo_v2, media_v2 = leer(a.v2)
    cand = [(media_v2, brazo_v2, a.v2)]
    for ruta in [r for r in (a.candidatos or "").split(",") if r]:
        brazo, media = leer(ruta)
        cand.append((media, brazo, ruta))
    cand.sort(key=lambda x: x[0])
    mejor = cand[0]
    cambio = (mejor[0] - media_v2) / media_v2 * 100
    promovido = mejor[2] != a.v2 and cambio <= MARGEN
    citado = mejor if promovido else cand[[c[2] for c in cand].index(a.v2)]
    datos = {"celda": a.celda, "semillas": "15009-15024", "margen_pct": MARGEN,
             "v2": {"brazo": brazo_v2, "csv": a.v2, "retraso_total_medio": round(media_v2, 4)},
             "candidatos": [{"brazo": b, "csv": r, "retraso_total_medio": round(m, 4),
                             "cambio_vs_v2_pct": round((m - media_v2) / media_v2 * 100, 3)} for m, b, r in cand],
             "promovido": promovido, "modelo_citado": citado[1], "csv_citado": citado[2],
             "sha256": {r: sha(r) for _, _, r in cand}}
    escribir(a.salida, datos)
    print(f"{a.celda}: modelo citado {citado[1]} ({'promovido' if promovido else 'V2'})")


def juntar(a):
    datos = {}
    for ruta in a.entradas.split(","):
        with open(ruta, encoding="utf-8") as f:
            d = json.load(f)
        datos[d["celda"]] = {"archivo": ruta, "sha256": sha(ruta), "modelo_citado": d["modelo_citado"],
                             "promovido": d["promovido"]}
    escribir(a.salida, {"celdas": datos})
    print(f"promocion: {len(datos)} celdas; {sum(d['promovido'] for d in datos.values())} con variante promovida")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["decidir", "juntar"])
    ap.add_argument("--celda")
    ap.add_argument("--v2")
    ap.add_argument("--candidatos", default="")
    ap.add_argument("--entradas")
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    if a.modo == "decidir":
        assert a.celda and a.v2, "decidir necesita --celda y --v2"
        decidir(a)
    else:
        assert a.entradas, "juntar necesita --entradas"
        juntar(a)


if __name__ == "__main__":
    main()
