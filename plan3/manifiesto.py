"""
manifiesto.py - Revisa las evaluaciones contra cola/manifiesto_esperado.json, sin mirar metricas (PLAN3 0.15).

Uso (desde plan3/):
  python manifiesto.py revisar            cuantos CSV esperados estan, faltan o estan mal (solo cuentas)
  python manifiesto.py cierre             exige todos bien y escribe cola/manifiesto_cierre.json (sha256 de cada CSV)
  python manifiesto.py prueba             prueba en seco con CSV sinteticos en tmp_prueba_manifiesto/
Un CSV esta bien si tiene exactamente las semillas esperadas (ni de mas ni de menos), una fila por semilla y un solo
brazo, y si en cada (escenario, tanda) todos los brazos generan los mismos vehiculos en cada semilla (numeros
aleatorios comunes). Solo lee las columnas semilla, brazo y generados: ninguna metrica de desempeno.
"""
import os
import csv
import sys
import json
import hashlib
from collections import defaultdict

PLAN3 = os.path.dirname(os.path.abspath(__file__))
ESPERADO = os.path.join(PLAN3, "cola", "manifiesto_esperado.json")
CIERRE = os.path.join(PLAN3, "cola", "manifiesto_cierre.json")


def rango(texto):
    salida = []
    for parte in texto.split(","):
        a, b = parte.split("-") if "-" in parte else (parte, parte)
        salida += list(range(int(a), int(b) + 1))
    return salida


def sha(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def leer_csv(ruta):
    """(brazos, {semilla: generados}, filas) sin leer metricas."""
    brazos, generados, filas = set(), {}, 0
    with open(ruta, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            filas += 1
            brazos.add(r["brazo"])
            generados[int(r["semilla"])] = r.get("generados", "")
    return brazos, generados, filas


def revisar(esperado, raiz=PLAN3):
    estado = {"bien": [], "faltan": [], "mal": []}
    grupos = defaultdict(dict)                         # (escenario, tanda) -> {csv: {semilla: generados}}
    for e in esperado:
        ruta = os.path.join(raiz, e["csv"])
        if not os.path.exists(ruta):
            estado["faltan"].append(e["csv"])
            continue
        brazos, generados, filas = leer_csv(ruta)
        semillas = rango(e["semillas"])
        problemas = []
        if sorted(generados) != semillas:
            problemas.append(f"semillas {len(generados)} distintas de las {len(semillas)} esperadas")
        if filas != len(semillas):
            problemas.append(f"{filas} filas para {len(semillas)} semillas")
        if len(brazos) != 1:
            problemas.append(f"{len(brazos)} brazos")
        if problemas:
            estado["mal"].append(f"{e['csv']}: {'; '.join(problemas)}")
        else:
            estado["bien"].append(e["csv"])
            grupos[(e["escenario"], e["tanda"])][e["csv"]] = generados
    for (esc, tanda), csvs in sorted(grupos.items()):
        rutas = sorted(csvs)
        ref = csvs[rutas[0]]
        for r in rutas[1:]:
            dif = [s for s in ref if csvs[r].get(s) != ref[s]]
            if dif:
                estado["mal"].append(f"{r}: genera otros vehiculos que {rutas[0]} en {len(dif)} semillas")
    return estado


def prueba():
    """CSV sinteticos: uno bien, uno con una semilla de mas, uno que falta y uno con otros vehiculos."""
    tmp = os.path.join(PLAN3, "tmp_prueba_manifiesto")
    os.makedirs(os.path.join(tmp, "ciego", "t1r"), exist_ok=True)
    esperado = [{"csv": f"ciego/t1r/eval_x__{k}.csv", "escenario": "x", "tanda": "t1r", "semillas": "8001-8003"}
                for k in ("a", "b", "c", "d", "e")]

    def escribir(k, semillas, generados=100):
        with open(os.path.join(tmp, "ciego", "t1r", f"eval_x__{k}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["brazo", "semilla", "generados", "retraso_total_prom"])
            w.writeheader()
            for s in semillas:
                w.writerow({"brazo": k, "semilla": s, "generados": generados, "retraso_total_prom": 1.0})
    escribir("a", [8001, 8002, 8003])
    escribir("b", [8001, 8002, 8003, 8004])
    escribir("d", [8001, 8002, 8003], generados=99)
    escribir("e", [8001, 8002, 8003])
    r = revisar(esperado, raiz=tmp)
    bien = (r["faltan"] == ["ciego/t1r/eval_x__c.csv"] and len(r["mal"]) == 2
            and any("eval_x__b" in m and "semillas" in m for m in r["mal"])
            and any("eval_x__d" in m and "otros vehiculos" in m for m in r["mal"]))
    print("prueba del manifiesto:", "bien" if bien else f"MAL {r}")
    return bien


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "revisar"
    if modo == "prueba":
        sys.exit(0 if prueba() else 1)
    with open(ESPERADO, encoding="utf-8") as f:
        esperado = json.load(f)
    r = revisar(esperado)
    print(f"{len(esperado)} CSV esperados: {len(r['bien'])} bien, {len(r['faltan'])} faltan, {len(r['mal'])} mal")
    for m in r["mal"][:30]:
        print("  MAL", m)
    if modo == "cierre":
        if r["faltan"] or r["mal"]:
            sys.exit("manifiesto: no se puede cerrar con CSV que faltan o estan mal")
        datos = {e["csv"]: sha(os.path.join(PLAN3, e["csv"])) for e in esperado}
        with open(CIERRE, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=0, sort_keys=True)
        print(f"escrito {os.path.relpath(CIERRE, PLAN3)}")


if __name__ == "__main__":
    main()
