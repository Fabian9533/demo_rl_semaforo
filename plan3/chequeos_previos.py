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
  4. el codigo y el prerregistro no tienen cambios sin commit;
  5. cada comando de la lista pasa el parser de su script (validar_args de rl_ippo, barrer_fino, franja, actuado,
     reglas, p3_preparar y evaluar3): un desajuste entre el generador y un script se ve aqui y no a la noche;
  6. desde la parte B (dia 14): cada archivo de referencias_congeladas.json existe con su sha256.
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


def correr(codigo, carpeta, extra=(), programa="rl_ippo.py", cmd=None, archivos=None):
    """Corre el `programa` de `codigo` en `carpeta` (con los archivos del escenario). Por omision, el entrenamiento CMD
    de rl_ippo en P1."""
    os.makedirs(carpeta, exist_ok=True)
    for a in (ESCENARIO if archivos is None else archivos):
        shutil.copy(os.path.join(PLAN3, a), carpeta)
    entorno = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, os.path.join(codigo, programa)] + list(CMD if cmd is None else cmd)
                       + list(extra), cwd=carpeta, capture_output=True, text=True, env=entorno)
    if r.returncode != 0:
        raise RuntimeError(f"{programa} fallo en {carpeta}:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")


def filas(ruta, columnas=None, sin=("segundos",)):
    """Filas del CSV sin 'segundos' (y, si se da, solo esas columnas)."""
    with open(ruta, encoding="utf-8", newline="") as f:
        return [{k: v for k, v in r.items() if k not in sin and (columnas is None or k in columnas)}
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
    malos += identidad_tramos()
    malos += identidad_evaluar(tag)
    malos += identidad_evaluar_viejo(tag)
    malos += identidad_c0()
    malos += identidad_malla(tag)
    return malos


def iguales_corridas(a, b, etiqueta_a, etiqueta_b, que, esc="corredor", base=7, columnas_csv=None, subconjunto=False):
    """Compara dos corridas de entrenamiento: CSV (sin 'segundos' ni 'etiqueta'), tensores de los checkpoints y de la
    politica publicada, y la eleccion del checkpoint. Con subconjunto, los checkpoints de b pueden ser parte de los de a
    (una etiqueta nueva no repite los anteriores a su origen), pero el ultimo tiene que estar."""
    malos = []
    csv_a = f"resultados_{esc}_ippo_vecinos_{etiqueta_a}_s{base}.csv"
    csv_b = f"resultados_{esc}_ippo_vecinos_{etiqueta_b}_s{base}.csv"
    sin = ("segundos", "etiqueta")
    if filas(os.path.join(a, csv_a), columnas_csv, sin) != filas(os.path.join(b, csv_b), columnas_csv, sin):
        malos.append(f"{que}: el CSV difiere")
    pts = lambda d, et: {x.replace(f"_{et}_", "_"): x for x in os.listdir(os.path.join(d, "checkpoints"))
                         if x.endswith(".pt") and not x.endswith(".estado.pt") and f"_{et}_" in x}
    pa, pb = pts(a, etiqueta_a), pts(b, etiqueta_b)
    if (not set(pb) <= set(pa) or max(pa, default="") not in pb) if subconjunto else sorted(pa) != sorted(pb):
        malos.append(f"{que}: checkpoints distintos: {sorted(pa)} frente a {sorted(pb)}")
    for k in pa:
        if k in pb and not tensores_iguales(os.path.join(a, "checkpoints", pa[k]), os.path.join(b, "checkpoints", pb[k])):
            malos.append(f"{que}: tensores distintos en {pa[k]}")
    pol_a = os.path.join(a, f"politica_{esc}_vecinos_{etiqueta_a}_s{base}.pt")
    pol_b = os.path.join(b, f"politica_{esc}_vecinos_{etiqueta_b}_s{base}.pt")
    if not tensores_iguales(pol_a, pol_b):
        malos.append(f"{que}: la politica publicada difiere")
    ma, mb = (json.load(open(p[:-3] + ".json", encoding="utf-8")) for p in (pol_a, pol_b))
    if (ma["ep_elegido"], ma["val_elegido"]) != (mb["ep_elegido"], mb["val_elegido"]):
        malos.append(f"{que}: la eleccion del checkpoint difiere")
    return malos


def identidad_tramos():
    """El camino de los trabajos en tramos (revision de las Etapas 3-4, 05.11): V2 de hoy cortada en 5 + 5 con
    --reanudar auto, y la continuacion con una etiqueta nueva desde el estado del ep 5 (como la Etapa 3b, con las
    mismas opciones), dan lo mismo que la corrida seguida de identidad_v2 (TMP/v2_actual)."""
    base = ["--v2", "--criterio-val", "total", "--guardar-estado", "--registro-extendido"]
    seguida, tramos, nueva = (os.path.join(TMP, x) for x in ("v2_actual", "v2_tramos", "v2_nueva"))
    correr(RAIZ, tramos, base + ["--etiqueta", "p3id", "--reanudar", "auto", "--hasta-ep", "5"])
    correr(RAIZ, tramos, base + ["--etiqueta", "p3id", "--reanudar", "auto"])
    malos = iguales_corridas(seguida, tramos, "p3id", "p3id", "identidad en tramos (5 + 5)")
    os.makedirs(os.path.join(nueva, "checkpoints"), exist_ok=True)
    for x in os.listdir(os.path.join(tramos, "checkpoints")):
        if "_ep005" in x:
            shutil.copy(os.path.join(tramos, "checkpoints", x), os.path.join(nueva, "checkpoints"))
    correr(RAIZ, nueva, base + ["--etiqueta", "p3idn", "--reanudar",
                                "checkpoints/corredor_ippo_vecinos_p3id_s7_ep005.estado.pt"])
    malos += iguales_corridas(seguida, nueva, "p3id", "p3idn", "identidad con etiqueta nueva desde el ep 5",
                              subconjunto=True)
    return malos


def identidad_evaluar(tag):
    """evaluar.py del tag y de hoy juegan igual la politica V2 publicada por el tag (una semilla de humo)."""
    for a in ("evaluar.py",):
        rc, texto = protecciones.git("show", f"{TAG}:{a}")
        if rc != 0:
            return [f"no se pudo leer {a} del tag"]
        with open(os.path.join(tag, a), "w", encoding="utf-8", newline="") as f:
            f.write(texto)
    pol = os.path.join(TMP, "v2_tag", "politica_corredor_vecinos_p3id_s7.pt")
    salidas = {}
    for nombre, codigo in (("tag", tag), ("actual", RAIZ)):
        carpeta = os.path.join(TMP, f"evaluar_{nombre}")
        os.makedirs(carpeta, exist_ok=True)
        for x in (pol, pol[:-3] + ".json"):
            shutil.copy(x, carpeta)
        correr(codigo, carpeta, programa="evaluar.py",
               cmd=["--escenario", "corredor", "--politica", os.path.basename(pol), "--semillas", "424303",
                    "--salida", "eval_id.csv"])
        salidas[nombre] = filas(os.path.join(carpeta, "eval_id.csv"))
    return [] if salidas["tag"] == salidas["actual"] else ["identidad de evaluar.py: el CSV difiere del del tag"]


def identidad_evaluar_viejo(tag):
    """evaluar.py en su modo antiguo (--brazos "" --ippo P): el del tag y el de hoy juegan igual la politica V2 del tag
    en una semilla de humo. Es uno de los dos caminos que cambio el arreglo de las opciones del meta (revision del
    06.11, E2-L1). Usa el evaluar.py del tag que copio identidad_evaluar."""
    pol = os.path.join(TMP, "v2_tag", "politica_corredor_vecinos_p3id_s7.pt")
    salidas = {}
    for nombre, codigo in (("tag", tag), ("actual", RAIZ)):
        carpeta = os.path.join(TMP, f"evaluar_viejo_{nombre}")
        os.makedirs(carpeta, exist_ok=True)
        for x in (pol, pol[:-3] + ".json"):
            shutil.copy(x, carpeta)
        correr(codigo, carpeta, programa="evaluar.py",
               cmd=["--escenario", "corredor", "--brazos", "", "--ippo", os.path.basename(pol), "--semillas", "424303"])
        salidas[nombre] = filas(os.path.join(carpeta, "evaluacion_corredor.csv"))
    if not salidas["tag"]:
        return ["identidad de evaluar.py en modo antiguo: el del tag no escribio filas"]
    return [] if salidas["tag"] == salidas["actual"] else \
        ["identidad de evaluar.py en modo antiguo: el CSV difiere del del tag"]


def identidad_c0():
    """Los trabajos C0 (revalidar_c0.py validar) reproducen la validacion guardada de un checkpoint entregado: corredor,
    base 42, ep 10, semillas 999 y 1999. revalidar_c0 compara cada semilla con el meta y sale con error si no
    coincide; aqui se exige ademas que el control haya cubierto las dos (revision del 06.11, E2-L1)."""
    origen = os.path.join(PLAN3, "insumos", "c0_checkpoints", "corredor_ippo_vecinos_s42_ep010.pt")
    if not os.path.exists(origen):
        return ["identidad de C0: falta insumos/c0_checkpoints/corredor_ippo_vecinos_s42_ep010.pt (p3_insumos.py)"]
    salida = os.path.join("tmp_identidad", "c0_identidad.json")
    entorno = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, "revalidar_c0.py", "validar", "--escenario", "corredor",
                        "--origen", "insumos/c0_checkpoints", "--corrida", "corredor_ippo_vecinos_s42", "--eps", "10",
                        "--val-seeds", "999,1999", "--salida", salida], cwd=PLAN3, capture_output=True, text=True,
                       env=entorno)
    if r.returncode != 0:
        return [f"identidad de C0: revalidar_c0 fallo:\n{r.stdout[-600:]}\n{r.stderr[-600:]}"]
    with open(os.path.join(PLAN3, salida), encoding="utf-8") as f:
        res = json.load(f)
    control = res["checkpoints"][0].get("control_reproducido") if res.get("checkpoints") else None
    return [] if control == [999, 1999] else [f"identidad de C0: el control reprodujo {control}, no [999, 1999]"]


def identidad_malla(tag):
    """V2 en la malla de P6 (malla3_alta, 3 episodios, validacion al final en 2 semillas de humo): la red donde las
    cadenas de la Etapa 1 cruzan las fusiones. El tag y el codigo de hoy, a la vez (dos procesos)."""
    from concurrent.futures import ThreadPoolExecutor
    archivos = ["malla3_alta.sumocfg", "malla3.net.xml", "malla3_alta.rou.xml", "malla3_alta.add.xml"]
    cmd = ["train", "--escenario", "malla3_alta", "--seed", "7", "--episodios", "3", "--eval-cada", "3",
           "--val-seeds", "424301,424302", "--v2", "--criterio-val", "total", "--etiqueta", "p3id"]
    a, b = os.path.join(TMP, "malla_tag"), os.path.join(TMP, "malla_actual")
    with ThreadPoolExecutor(2) as ex:
        trabajos = [ex.submit(correr, tag, a, (), "rl_ippo.py", cmd, archivos),
                    ex.submit(correr, RAIZ, b, ["--guardar-estado", "--registro-extendido"], "rl_ippo.py", cmd,
                              archivos)]
        for t in trabajos:
            t.result()
    cab_a = encabezado(os.path.join(a, "resultados_malla3_alta_ippo_vecinos_p3id_s7.csv"))
    return iguales_corridas(a, b, "p3id", "p3id", "identidad V2 en la malla (P6)", esc="malla3_alta",
                            columnas_csv=set(cab_a))


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


# Valida cada comando de la lista con el parser de su propio script (validar_args), en otro proceso para que el
# registro de los escenarios nuevos llegue antes de importar los modulos que lo copian (revision del 05.11; G1-F4).
SCRIPTS_VALIDADOS = {"rl_ippo.py": "rl_ippo", "barrer_fino.py": "barrer_fino", "franja.py": "franja",
                     "actuado.py": "actuado", "reglas.py": "reglas", "p3_preparar.py": "p3_preparar",
                     "evaluar3.py": "evaluar3"}
VALIDAR_COMANDOS = r'''
import io, os, sys, json, shlex, importlib, contextlib
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, os.getcwd())
import con_escenarios
con_escenarios.registrar()
SCRIPTS = json.loads(sys.argv[3])
modulos, malos, n = {}, [], {}
for linea in open(sys.argv[2], encoding="utf-8"):
    if not linea.strip():
        continue
    t = json.loads(linea)
    partes = shlex.split(t["cmd"])
    k = next((i for i, p in enumerate(partes) if os.path.basename(p.replace("\\", "/")) in SCRIPTS), None)
    if k is None:
        continue
    script = os.path.basename(partes[k].replace("\\", "/"))
    if script not in modulos:
        modulos[script] = importlib.import_module(SCRIPTS[script])
    n[script] = n.get(script, 0) + 1
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            modulos[script].validar_args(partes[k + 1:])
    except SystemExit:
        malos.append(t["id"] + ": " + script + ": " + (err.getvalue().strip().splitlines() or ["?"])[-1])
print(json.dumps({"n": n, "malos": malos}))
'''


def comandos(ruta=None):
    """Problemas de los comandos de cola/trabajos.jsonl (o de ruta): opciones que su script no acepta, segun el
    validar_args de rl_ippo, barrer_fino, franja, actuado, reglas, p3_preparar y evaluar3."""
    ruta = ruta or os.path.join(PLAN3, "cola", "trabajos.jsonl")
    if not os.path.exists(ruta):
        return []
    r = subprocess.run([sys.executable, "-c", VALIDAR_COMANDOS, RAIZ, ruta, json.dumps(SCRIPTS_VALIDADOS)],
                       cwd=PLAN3, capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return [f"no se pudieron validar los comandos:\n{r.stderr[-800:]}"]
    datos = json.loads(r.stdout.strip().splitlines()[-1])
    print(f"comandos validados con el parser de su script: {datos['n']}, rechazados: {len(datos['malos'])}",
          flush=True)
    malos = [f"rechazado {m}" for m in datos["malos"][:10]]
    return malos + ([f"... y {len(datos['malos']) - 10} comandos rechazados mas"] if len(datos["malos"]) > 10 else [])


def comandos_rl_ippo():
    """Nombre de antes (lo usan pruebas): ahora valida todos los scripts."""
    return comandos()


def referencias_congeladas():
    """Desde la parte B: cada archivo de referencias_congeladas.json existe en el disco con su sha256."""
    ruta = os.path.join(PLAN3, "referencias_congeladas.json")
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8") as f:
        congeladas = json.load(f)["referencias"]
    malos = []
    for rel, dato in sorted(congeladas.items()):
        archivo = os.path.join(PLAN3, rel)
        if not os.path.exists(archivo):
            malos.append(f"referencia congelada que falta: {rel}")
        elif protecciones.sha(archivo) != dato["sha256"]:
            malos.append(f"referencia congelada cambiada (sha256 distinto): {rel}")
    print(f"referencias congeladas: {len(congeladas)}, cambiadas o faltantes: {len(malos)}", flush=True)
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
    problemas += comandos()
    problemas += referencias_congeladas()
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
