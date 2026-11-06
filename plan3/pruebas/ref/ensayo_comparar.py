"""
ensayo_comparar.py - Segunda mitad del ensayo de la cadena real de las referencias (informe_ref 2.8): despues de correr
por la cola, en un worktree aparte, los trabajos de referencias de una celda (generar_trabajos3.generar(["referencias"])
filtrado a esa celda, sin opciones de prueba, con las semillas de la regla), juega con evaluar3 cada brazo de
generar_trabajos3.brazos_ref(<esc>) mas el fijo desde 10 s y el actuado ajustado con --programa (como en mixa_), con
2001-2003, y compara cada semilla con la fila del ganador en barridos/<esc>/*_semillas.csv.

Como se arma el ensayo (cwd = plan3/ del worktree aparte):
  python -c "import json, generar_trabajos3 as g; L=[t for t in g.generar(['referencias']) if t['cmd'].split()[2]=='corredor'];
             open('cola/trabajos.jsonl','w',encoding='utf-8').write(''.join(json.dumps(t)+'\\n' for t in L))"
  python cola.py --cpus 2 --sin-git
y despues, desde plan3/ de esta rama:
  python pruebas/ref/ensayo_comparar.py --plan3 <worktree aparte>/plan3 [--escenario corredor]
Escribe pruebas/ref/salidas/ensayo_comparar.txt. Semillas de ajuste 2001-2003 (no se elige nada con ellas).
"""
import os
import sys
import csv
import glob
import json
import argparse
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

SEM = ["2001", "2002", "2003"]


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--plan3", required=True, help="plan3/ del worktree donde corrio la cadena por la cola")
    ap.add_argument("--escenario", default="corredor")
    args = ap.parse_args()
    up.preparar()
    inf = up.Informe("ensayo_comparar")
    plan3, esc = os.path.abspath(args.plan3), args.escenario
    b = os.path.join(plan3, "barridos", esc)

    def leer_json(nombre):
        with open(os.path.join(b, nombre), encoding="utf-8") as f:
            return json.load(f)

    def filas(clave, patron="*_semillas.csv", campo="clave"):
        salida = {}
        for ruta in sorted(glob.glob(os.path.join(b, patron))):
            with open(ruta, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    if r.get(campo) == clave and r["semilla"] in SEM and r["semilla"] not in salida:
                        salida[r["semilla"]] = (float(r["retraso_total_prom"]), os.path.basename(ruta))
        return salida
    marcas = {n: leer_json(n).get("registro", {}).get("prueba") for n in os.listdir(b) if n.endswith(".json")}
    inf.chequeo(not any(marcas.values()), f"{esc}: {len(marcas)} JSON del barrido, ninguno con la marca de prueba: "
                                          f"{ {k: v for k, v in marcas.items() if v} }")
    sys.path[:0] = [plan3, os.path.dirname(plan3)]
    import generar_trabajos3 as g
    g.referencias(g.Lista())
    brazos = [(clave, brazo) for clave, brazo, _, _ in g.brazos_ref(esc)]
    brazos += [("fijo10", f"--brazo fijo --programa {esc}_r10g.add.xml --nombre grueso10"),
               ("actuadoaj_programa", f"--brazo actuado_aj --programa {esc}_actuado_aj.add.xml")]
    ganadores = {"fino": filas(leer_json("fijo_fino.json")["clave"]),
                 "fino5": filas(leer_json("fijo_mult5.json")["clave"]),
                 "fijo10": filas(leer_json("fijo_grueso10.json")["clave"]),
                 "actuadoaj": filas(leer_json("actuado_aj.json")["clave"]),
                 "actuadoaj_programa": filas(leer_json("actuado_aj.json")["clave"])}
    for nombre in ("franja", "bloques"):
        if os.path.exists(os.path.join(b, f"{nombre}.json")):
            ganadores[nombre] = filas(leer_json(f"{nombre}.json")["clave"])
    for fam in ("regla", "reactiva", "mp"):
        if os.path.exists(os.path.join(b, f"{fam}.json")):
            ganadores[fam] = filas(leer_json(f"{fam}.json")["regla"], f"reglas_{fam}_semillas.csv", "regla")
    os.makedirs(os.path.join(plan3, "tmp_ensayo"), exist_ok=True)
    for clave, brazo in brazos:
        salida = os.path.join("tmp_ensayo", f"ev_{clave}.csv")
        r = subprocess.run([sys.executable, "evaluar3.py", "--escenario", esc, "--semillas", "2001-2003", "--salida",
                            salida, *brazo.split()], cwd=plan3, capture_output=True, text=True,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        if r.returncode != 0:
            inf.chequeo(False, f"{clave} ({brazo}): evaluar3 codigo {r.returncode}: {(r.stdout + r.stderr)[-300:]}")
            continue
        with open(os.path.join(plan3, salida), newline="", encoding="utf-8") as f:
            ev = list(csv.DictReader(f))
        valores = {x["semilla"]: float(x["retraso_total_prom"]) for x in ev}
        gan = ganadores.get(clave, {})
        iguales = bool(gan) and all(s in gan and abs(valores[s] - gan[s][0]) < 1e-6 for s in SEM)
        inf.chequeo(iguales and ev[0]["sha_ref"], f"{clave} ({brazo}): evaluar3 {[valores[s] for s in SEM]} = barrido "
                                                  f"{[gan[s][0] for s in SEM] if gan else '-'} "
                                                  f"({sorted({v[1] for v in gan.values()})}); sha_ref "
                                                  f"{ev[0]['sha_ref'][:12]}")
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
