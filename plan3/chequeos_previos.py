"""
chequeos_previos.py - Chequeos de cada tarde antes de una noche del bloque plan3 (PLAN3 0.16).

Uso (desde <worktree de ejecucion>/plan3):  python chequeos_previos.py [--sin-identidad]
Pasos (si alguno falla, no escribe lanzamiento.sha256 y la cola no arranca):
  1. identidad: rl_ippo con todo apagado (P1, base de humo 7, 10 episodios, validacion cada 5 en 2 semillas de humo)
     da el mismo CSV (salvo la columna 'segundos') y los mismos tensores que el codigo del tag entregado-2026-10-25;
  2. lista de trabajos: capas 1 y 2 de protecciones.py (comandos, nombres y salidas unicos, dependencias), y que
     cola/trabajos.jsonl y cola/manifiesto_esperado.json son los que escribe el generador con cola/partes.txt;
  3. semillas: ningun CSV fuera de ciego/ e insumos/ tiene semillas de las tandas decisivas o de la prueba final;
  4. el codigo y el prerregistro no tienen cambios sin commit.
Si todo pasa, escribe lanzamiento.sha256: "<commit> <sha256 de PRERREGISTRO.md> <sha256 de cola/trabajos.jsonl>".
"""
import os
import csv
import sys
import json
import time
import shutil
import argparse
import subprocess

import protecciones

PLAN3 = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PLAN3)
TMP = os.path.join(PLAN3, "tmp_identidad")
TAG = "entregado-2026-10-25"
CODIGO = ["rl_ippo.py", "rl_corredor.py", "comun.py", "escenarios_plan2.py"]
ESCENARIO = ["corredor.sumocfg", "corredor.net.xml", "corredor.rou.xml", "corredor.add.xml"]
CMD = ["train", "--escenario", "corredor", "--seed", "7", "--episodios", "10", "--eval-cada", "5",
       "--val-seeds", "424301,424302"]
CSV_ID = "resultados_corredor_ippo_vecinos_s7.csv"


def correr(codigo, carpeta):
    """Entrena con el rl_ippo.py de `codigo` en `carpeta` (con los archivos del escenario)."""
    os.makedirs(carpeta, exist_ok=True)
    for a in ESCENARIO:
        shutil.copy(os.path.join(PLAN3, a), carpeta)
    entorno = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, os.path.join(codigo, "rl_ippo.py")] + CMD, cwd=carpeta,
                       capture_output=True, text=True, env=entorno)
    if r.returncode != 0:
        raise RuntimeError(f"rl_ippo fallo en {carpeta}:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")


def filas(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return [{k: v for k, v in r.items() if k != "segundos"} for r in csv.DictReader(f)]


def tensores_iguales(a, b):
    import torch
    sa = torch.load(a, map_location="cpu", weights_only=True)
    sb = torch.load(b, map_location="cpu", weights_only=True)

    def plano(x, pref=""):
        if isinstance(x, dict):
            out = {}
            for k, v in x.items():
                out.update(plano(v, f"{pref}{k}."))
            return out
        return {pref: x}
    pa, pb = plano(sa), plano(sb)
    if pa.keys() != pb.keys():
        return False
    for k in pa:
        if hasattr(pa[k], "shape"):
            if not torch.equal(pa[k], pb[k]):
                return False
        elif pa[k] != pb[k]:
            return False
    return True


def identidad():
    if os.path.exists(TMP):
        shutil.rmtree(TMP)
    tag = os.path.join(TMP, "codigo_tag")
    os.makedirs(tag)
    for a in CODIGO:
        rc, texto = protecciones.git("show", f"{TAG}:{a}")
        if rc != 0:
            return [f"no se pudo leer {a} del tag"]
        with open(os.path.join(tag, a), "w", encoding="utf-8", newline="") as f:
            f.write(texto)
    correr(tag, os.path.join(TMP, "corrida_tag"))
    correr(RAIZ, os.path.join(TMP, "corrida_actual"))
    malos = []
    a, b = os.path.join(TMP, "corrida_tag"), os.path.join(TMP, "corrida_actual")
    if filas(os.path.join(a, CSV_ID)) != filas(os.path.join(b, CSV_ID)):
        malos.append("identidad: el CSV de entrenamiento difiere del del tag")
    ckpt_a = sorted(os.listdir(os.path.join(a, "checkpoints")))
    ckpt_b = sorted(x for x in os.listdir(os.path.join(b, "checkpoints")) if not x.endswith(".estado.pt"))
    if ckpt_a != ckpt_b:
        malos.append(f"identidad: checkpoints distintos: {ckpt_a} frente a {ckpt_b}")
    for x in ckpt_a:
        if x.endswith(".pt") and x in ckpt_b and not tensores_iguales(os.path.join(a, "checkpoints", x),
                                                                       os.path.join(b, "checkpoints", x)):
            malos.append(f"identidad: tensores distintos en {x}")
    pol = "politica_corredor_vecinos_s7.pt"
    if not tensores_iguales(os.path.join(a, pol), os.path.join(b, pol)):
        malos.append("identidad: la politica publicada difiere")
    return malos


def semillas_filtradas():
    """CSV fuera de ciego/ e insumos/ con semillas de las tandas decisivas o de la prueba final."""
    tab = protecciones.tabla()["semillas"]
    tramos = tab["examen_regular"] + tab["examen_h1"] + tab["examen_aleatorio"] + tab["final"]
    malos = []
    for raiz, dirs, archivos in os.walk(PLAN3):
        rel = os.path.relpath(raiz, PLAN3).replace(os.sep, "/")
        if rel.split("/")[0] in ("ciego", "insumos", "checkpoints") or rel.startswith("tmp_"):
            dirs[:] = []
            continue
        for a in archivos:
            if not a.endswith(".csv"):
                continue
            with open(os.path.join(raiz, a), encoding="utf-8", errors="replace", newline="") as f:
                lector = csv.DictReader(f)
                col = next((c for c in ("semilla", "seed") if c in (lector.fieldnames or [])), None)
                if not col:
                    continue
                for r in lector:
                    try:
                        s = int(float(r[col]))
                    except (TypeError, ValueError):
                        continue
                    if protecciones.en_tramos(s, tramos):
                        malos.append(f"{rel}/{a} tiene la semilla decisiva {s} fuera de ciego/")
                        break
    return malos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-identidad", action="store_true", help="omite la prueba de identidad (solo pruebas)")
    args = ap.parse_args()
    ruta = os.path.join(PLAN3, "lanzamiento.sha256")
    if os.path.exists(ruta):
        os.remove(ruta)
    problemas = []
    t0 = time.time()
    if not args.sin_identidad:
        try:
            problemas += identidad()
        except RuntimeError as e:
            problemas.append(str(e))
        print(f"identidad: {'bien' if not problemas else 'MAL'} ({time.time() - t0:.0f} s)", flush=True)
    problemas += protecciones.revisar_trabajos(protecciones.leer_trabajos())
    r = subprocess.run([sys.executable, "generar_trabajos3.py", "--comprobar"], cwd=PLAN3, capture_output=True,
                       text=True)
    if r.returncode != 0:
        problemas.append("la lista de trabajos o el manifiesto no son los del generador:\n" + r.stdout + r.stderr)
    problemas += semillas_filtradas()
    _, cambios = protecciones.git("status", "--porcelain", "--untracked-files=no", "--", "*.py",
                                  "plan3/PRERREGISTRO.md")
    if cambios.strip():
        problemas.append("hay codigo o prerregistro sin commit:\n" + cambios)
    for p in problemas:
        print("PROBLEMA:", p)
    if problemas:
        sys.exit(f"chequeos previos: {len(problemas)} problemas; no se escribe lanzamiento.sha256")
    commit = protecciones.git("rev-parse", "HEAD")[1].strip()
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(f"{commit} {protecciones.sha(protecciones.PRERREGISTRO)} "
                f"{protecciones.sha(os.path.join(PLAN3, 'cola', 'trabajos.jsonl'))}\n")
    print(f"chequeos previos: bien; lanzamiento.sha256 = {commit[:10]}")


if __name__ == "__main__":
    main()
