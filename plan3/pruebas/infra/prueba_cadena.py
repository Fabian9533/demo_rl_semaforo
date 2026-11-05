"""
prueba_cadena.py - Prueba de punta a punta con la cola real (cola.py --sin-git) y comandos como los del generador.

Uso (desde plan3/):  python pruebas/infra/prueba_cadena.py   -> pruebas/infra/prueba_cadena.txt
Con semillas de humo (base 7; 424301-424304), en P1:
  humo_t1  rl_ippo en su primer tramo (--reanudar auto --hasta-ep 2) -> deja el estado del ep 2;
  humo_t2  el mismo comando sin --hasta-ep -> sigue desde ese estado y publica la politica;
  humo_ev  evaluar3 juega la politica publicada (2 semillas);
  humo_3b  etiqueta nueva desde el estado del ep 2 (como 3b), con tasa con piso.
Comprueba que la cola los da por hechos con sus salidas y que la corrida reanudada registra de donde partio. Al
final borra todo lo que creo (cola/, checkpoints de humo, politicas, CSV y parciales/humo).
Usa la cola de plan3/cola: no correr si hay una lista de trabajos real en esa carpeta.
"""
import os
import sys
import json
import glob
import shutil
import datetime
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN3 = os.path.dirname(os.path.dirname(AQUI))
BASE = ("python ../rl_ippo.py train --escenario corredor --variante vecinos --seed 7 --eval-cada 2 "
        "--val-seeds 424301,424302 --criterio-val total --guardar-estado --registro-extendido --v2")
TRABAJOS = [
    {"id": "humo_t1", "prioridad": 1, "uso": "humo", "cadena": "a",
     "cmd": BASE + " --episodios 4 --etiqueta p3humo --reanudar auto --hasta-ep 2",
     "salidas": ["checkpoints/corredor_ippo_vecinos_p3humo_s7_ep002.estado.pt"], "duracion": 120},
    {"id": "humo_t2", "prioridad": 1, "uso": "humo", "cadena": "a", "requiere": ["trabajo:humo_t1"],
     "cmd": BASE + " --episodios 4 --etiqueta p3humo --reanudar auto",
     "salidas": ["politica_corredor_vecinos_p3humo_s7.pt", "resultados_corredor_ippo_vecinos_p3humo_s7.csv"],
     "duracion": 120},
    {"id": "humo_ev", "prioridad": 1, "uso": "humo", "requiere": ["trabajo:humo_t2"],
     "cmd": "python evaluar3.py --escenario corredor --semillas 424303-424304 "
            "--salida parciales/humo/eval_corredor__p3humo.csv --politica politica_corredor_vecinos_p3humo_s7.pt",
     "salidas": ["parciales/humo/eval_corredor__p3humo.csv"], "duracion": 60},
    {"id": "humo_3b", "prioridad": 1, "uso": "humo", "cadena": "b", "requiere": ["trabajo:humo_t2"],
     "cmd": BASE + " --episodios 6 --lr-horizonte 4 --lr-piso 0.1 --etiqueta p3humob "
                   "--reanudar checkpoints/corredor_ippo_vecinos_p3humo_s7_ep002.estado.pt",
     "salidas": ["politica_corredor_vecinos_p3humob_s7.pt"], "duracion": 120},
]


def limpiar():
    for patron in ("politica_corredor_vecinos_p3humo*", "resultados_corredor_ippo_vecinos_p3humo*",
                   "checkpoints/corredor_ippo_vecinos_p3humo*", "tripinfo_corredor_ippo_vecinos_p3humo*"):
        for r in glob.glob(os.path.join(PLAN3, patron)):
            os.remove(r)
    for d in ("cola", os.path.join("parciales", "humo")):
        shutil.rmtree(os.path.join(PLAN3, d), ignore_errors=True)


def main():
    if os.path.exists(os.path.join(PLAN3, "cola", "trabajos.jsonl")):
        sys.exit("ya hay una lista de trabajos en cola/: esta prueba no se corre ahi")
    os.makedirs(os.path.join(PLAN3, "cola"))
    with open(os.path.join(PLAN3, "cola", "trabajos.jsonl"), "w", encoding="utf-8") as f:
        for t in TRABAJOS:
            f.write(json.dumps(t) + "\n")
    hasta = (datetime.datetime.now() + datetime.timedelta(minutes=60)).strftime("%H:%M")
    r = subprocess.run([sys.executable, "cola.py", "--sin-git", "--cpus", "3", "--hasta", hasta], cwd=PLAN3,
                       capture_output=True, text=True, timeout=3600)
    e = json.load(open(os.path.join(PLAN3, "cola", "estado.json"), encoding="utf-8"))
    meta = json.load(open(os.path.join(PLAN3, "politica_corredor_vecinos_p3humob_s7.json"), encoding="utf-8"))
    lineas = [r.stdout.strip()]
    malos = 0

    def revisar(desc, cond):
        nonlocal malos
        malos += not cond
        lineas.append(f"{'ok ' if cond else 'MAL'} {desc}")
    revisar("los 4 trabajos hechos, ninguno fallido",
            set(e["hechos"]) == {t["id"] for t in TRABAJOS} and not e["fallidos"])
    revisar(f"la corrida de etiqueta nueva registra su origen: {meta.get('reanudado_de')}",
            meta.get("reanudado_de") == [{"corrida": "corredor_ippo_vecinos_p3humo_s7", "episodio": 2}])
    texto = "\n".join(lineas)
    print(texto)
    limpiar()
    with open(os.path.join(AQUI, "prueba_cadena.txt"), "w", encoding="utf-8") as f:
        f.write(texto + "\n")
    sys.exit(1 if malos else 0)


if __name__ == "__main__":
    main()
