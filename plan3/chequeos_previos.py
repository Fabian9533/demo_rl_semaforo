"""
chequeos_previos.py - Chequeos de cada tarde antes de una noche del bloque plan3 (PLAN3 0.16).

Uso (desde <worktree de ejecucion>/plan3):  python chequeos_previos.py [--sin-identidad]
Pasos (si alguno falla, no escribe lanzamiento.sha256 y la cola no arranca):
  1. identidad: rl_ippo con todo apagado (P1, base de humo 7, 10 episodios, validacion cada 5 en 2 semillas de humo)
     da el mismo CSV (salvo la columna 'segundos') y los mismos tensores que el codigo del tag entregado-2026-10-25;
     y V2 con --guardar-estado --registro-extendido (el camino de los trabajos) da lo mismo que V2 del tag;
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


def correr(codigo, carpeta, extra=()):
    """Entrena con el rl_ippo.py de `codigo` en `carpeta` (con los archivos del escenario)."""
    os.makedirs(carpeta, exist_ok=True)
    for a in ESCENARIO:
        shutil.copy(os.path.join(PLAN3, a), carpeta)
    entorno = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, os.path.join(codigo, "rl_ippo.py")] + CMD + list(extra), cwd=carpeta,
                       capture_output=True, text=True, env=entorno)
    if r.returncode != 0:
        raise RuntimeError(f"rl_ippo fallo en {carpeta}:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")


def filas(ruta, columnas=None):
    """Filas del CSV sin 'segundos' (y, si se da, solo esas columnas)."""
    with open(ruta, encoding="utf-8", newline="") as f:
        return [{k: v for k, v in r.items() if k != "segundos" and (columnas is None or k in columnas)}
                for r in csv.DictReader(f)]


def encabezado(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return next(csv.reader(f))


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
    malos += identidad_v2(tag)
    return malos


def identidad_v2(tag):
    """El camino que usan los trabajos (revision del 05.11): V2 del tag frente a V2 de hoy con --guardar-estado y
    --registro-extendido. El CSV de hoy solo agrega columnas al final; en las del tag, las filas son iguales; los
    checkpoints, la politica y su eleccion tienen los mismos tensores; hay un estado por checkpoint."""
    base = ["--v2", "--criterio-val", "total", "--etiqueta", "p3id"]
    a, b = os.path.join(TMP, "v2_tag"), os.path.join(TMP, "v2_actual")
    correr(tag, a, base)
    correr(RAIZ, b, base + ["--guardar-estado", "--registro-extendido"])
    malos = []
    csv_id = "resultados_corredor_ippo_vecinos_p3id_s7.csv"
    cab_a, cab_b = encabezado(os.path.join(a, csv_id)), encabezado(os.path.join(b, csv_id))
    if cab_b[:len(cab_a)] != cab_a:
        malos.append("identidad V2: el CSV de hoy no empieza con las columnas del tag")
    if filas(os.path.join(a, csv_id)) != filas(os.path.join(b, csv_id), set(cab_a)):
        malos.append("identidad V2: las filas difieren en las columnas del tag")
    ckpt = lambda d, fin: sorted(x for x in os.listdir(os.path.join(d, "checkpoints")) if x.endswith(fin))
    pts_a = [x for x in ckpt(a, ".pt") if not x.endswith(".estado.pt")]
    pts_b = [x for x in ckpt(b, ".pt") if not x.endswith(".estado.pt")]
    if pts_a != pts_b:
        malos.append(f"identidad V2: checkpoints distintos: {pts_a} frente a {pts_b}")
    for x in pts_a:
        if x in pts_b and not tensores_iguales(os.path.join(a, "checkpoints", x), os.path.join(b, "checkpoints", x)):
            malos.append(f"identidad V2: tensores distintos en {x}")
    if len(ckpt(b, ".estado.pt")) < len(pts_b):
        malos.append("identidad V2: falta un estado por checkpoint")
    pol = "politica_corredor_vecinos_p3id_s7.pt"
    if not tensores_iguales(os.path.join(a, pol), os.path.join(b, pol)):
        malos.append("identidad V2: la politica publicada difiere")
    import json
    ma, mb = (json.load(open(os.path.join(d, pol[:-3] + ".json"), encoding="utf-8")) for d in (a, b))
    if (ma["ep_elegido"], ma["val_elegido"]) != (mb["ep_elegido"], mb["val_elegido"]):
        malos.append("identidad V2: la eleccion del checkpoint difiere")
    return malos


# Valida cada comando de rl_ippo de la lista con su propio parser (rl_ippo.validar_args), en otro proceso para que el
# registro de los escenarios nuevos llegue antes de importar rl_ippo (revision del 05.11).
VALIDAR_RL_IPPO = r'''
import io, sys, json, shlex, contextlib
sys.path.insert(0, sys.argv[1])
import con_escenarios
con_escenarios.registrar()
import rl_ippo
malos, n = [], 0
for linea in open(sys.argv[2], encoding="utf-8"):
    if not linea.strip():
        continue
    t = json.loads(linea)
    partes = shlex.split(t["cmd"])
    argv = next((partes[i + 1:] for i, p in enumerate(partes) if p.replace("\\", "/").endswith("rl_ippo.py")), None)
    if argv is None:
        continue
    n += 1
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            rl_ippo.validar_args(argv)
    except SystemExit:
        malos.append(t["id"] + ": " + (err.getvalue().strip().splitlines() or ["?"])[-1])
print(json.dumps({"n": n, "malos": malos}))
'''


def comandos_rl_ippo():
    """Problemas de los comandos de rl_ippo de cola/trabajos.jsonl (opciones que rl_ippo no acepta)."""
    ruta = os.path.join(PLAN3, "cola", "trabajos.jsonl")
    if not os.path.exists(ruta):
        return []
    r = subprocess.run([sys.executable, "-c", VALIDAR_RL_IPPO, RAIZ, ruta], cwd=PLAN3, capture_output=True,
                       text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return [f"no se pudieron validar los comandos de rl_ippo:\n{r.stderr[-800:]}"]
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    print(f"comandos de rl_ippo validados: {datos['n']}, rechazados: {len(datos['malos'])}", flush=True)
    malos = [f"rl_ippo rechaza {m}" for m in datos["malos"][:10]]
    return malos + ([f"... y {len(datos['malos']) - 10} comandos rechazados mas"] if len(datos["malos"]) > 10 else [])


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
    problemas += comandos_rl_ippo()
    r = subprocess.run([sys.executable, "generar_trabajos3.py", "--comprobar"], cwd=PLAN3, capture_output=True,
                       text=True)
    if r.returncode != 0:
        problemas.append("la lista de trabajos o el manifiesto no son los del generador:\n" + r.stdout + r.stderr)
    problemas += semillas_filtradas()
    # los escenarios nuevos estan como los escribe preparar3 (una receta cambiada sin regenerar, o un archivo editado)
    r = subprocess.run([sys.executable, "demanda_estocastica.py", "preparar3", "--revisar"], cwd=PLAN3,
                       capture_output=True, text=True)
    if r.returncode != 0:
        problemas.append("los escenarios nuevos no estan como los escribe preparar3:\n" + r.stdout + r.stderr)
    _, cambios = protecciones.git("status", "--porcelain", "--untracked-files=no", "--", *protecciones.SIN_CAMBIOS)
    if cambios.strip():
        problemas.append("hay codigo, prerregistro o escenarios sin commit:\n" + cambios)
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
