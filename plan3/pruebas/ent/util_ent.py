"""
util_ent.py - Utilidades de las pruebas de plan3/pruebas/ent (tareas 1.1 y 1.2 del plan 3: opciones nuevas de
rl_ippo.py, --guardar-estado, --hasta-ep y --reanudar). Informe: plan3/doc/informe_ent1.md.

Todo corre dentro de plan3/tmp_ent/ (ignorada por git): una carpeta por corrida, con copias de los escenarios de
plan3/ (cada .sumocfg y lo que nombra), OMP_NUM_THREADS=1 y MKL_NUM_THREADS=1 como la cola. El codigo del tag
entregado-2026-10-25 se extrae con git show a tmp_ent/codigo_tag/ (rl_ippo.py y los modulos que importa: la carpeta
del script va primera en sys.path, asi que importa esas copias y no las de la raiz). Las salidas pequenas van a
pruebas/ent/salidas/. Semillas: humo (base 7; validacion y evaluacion 424301-424360), salvo la identidad con el
diagnostico (base 42).
"""
import io
import os
import csv
import sys
import json
import time
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import torch

AQUI = Path(__file__).resolve().parent
PLAN3 = AQUI.parents[1]
RAIZ = PLAN3.parent
TMP = PLAN3 / "tmp_ent"
SALIDAS = AQUI / "salidas"
TAG = "entregado-2026-10-25"
CODIGO_TAG = TMP / "codigo_tag"
ARCHIVOS_TAG = ["rl_ippo.py", "comun.py", "rl_corredor.py", "escenarios_plan2.py"]
RL_NUEVO = RAIZ / "rl_ippo.py"
EVALUAR = RAIZ / "evaluar.py"
VAL_HUMO = "424301,424302"
EVAL_HUMO = "424303,424304"


def entorno():
    env = dict(os.environ)
    env.update({"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    return env


def archivos_cfg(cfg):
    """El .sumocfg y los archivos que nombra (red, rutas, adicionales)."""
    raiz = ET.parse(cfg).getroot()
    salida = [Path(cfg).name]
    for etiqueta in ("net-file", "route-files", "additional-files"):
        for nodo in raiz.iter(etiqueta):
            salida += [v.strip() for v in nodo.get("value", "").split(",") if v.strip()]
    return salida


def carpeta(nombre, escenarios, limpiar=True):
    """tmp_ent/<nombre> con copias de los escenarios de plan3/ (vacia si limpiar)."""
    destino = TMP / nombre
    if limpiar and destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True, exist_ok=True)
    for esc in escenarios:
        for rel in archivos_cfg(PLAN3 / f"{esc}.sumocfg"):
            shutil.copyfile(PLAN3 / rel, destino / rel)
    return destino


def codigo_tag():
    """Extrae del tag rl_ippo.py y los modulos que importa a tmp_ent/codigo_tag/; devuelve la ruta de rl_ippo.py."""
    CODIGO_TAG.mkdir(parents=True, exist_ok=True)
    for f in ARCHIVOS_TAG:
        texto = subprocess.run(["git", "show", f"{TAG}:{f}"], cwd=RAIZ, capture_output=True, check=True).stdout
        (CODIGO_TAG / f).write_bytes(texto)
    return CODIGO_TAG / "rl_ippo.py"


def lanzar(script, argumentos, cwd, log):
    """python script argumentos (cwd y entorno de la cola), stdout y stderr al log; devuelve el Popen."""
    f = open(log, "w", encoding="utf-8")
    p = subprocess.Popen([sys.executable, str(script)] + [str(a) for a in argumentos], cwd=cwd, env=entorno(),
                         stdout=f, stderr=subprocess.STDOUT)
    p.log = f
    return p


def esperar(procesos):
    codigos = []
    for p in procesos:
        codigos.append(p.wait())
        p.log.close()
    return codigos


def correr(script, argumentos, cwd, log):
    return esperar([lanzar(script, argumentos, cwd, log)])[0]


def en_tandas(trabajos, maximo=3):
    """trabajos = [(script, argumentos, cwd, log)]: corre de a `maximo` a la vez (tope: la variable ENT_PROCESOS,
    para no pasar de 3 procesos si otra prueba corre al lado); devuelve los codigos en orden."""
    maximo = max(1, min(maximo, int(os.environ.get("ENT_PROCESOS", maximo))))
    codigos, activos = [None] * len(trabajos), {}
    pendientes = list(enumerate(trabajos))
    while pendientes or activos:
        while pendientes and len(activos) < maximo:
            i, t = pendientes.pop(0)
            activos[i] = lanzar(*t)
        for i, p in list(activos.items()):
            if p.poll() is not None:
                p.log.close()
                codigos[i] = p.returncode
                del activos[i]
        time.sleep(0.5)
    return codigos


# ---------------- Comparaciones ----------------
def filas_csv(ruta):
    with open(ruta, newline="") as f:
        return list(csv.reader(f))


def texto_sin(ruta, columna="segundos"):
    """Texto del CSV con la columna vaciada (es tiempo de reloj). Antes comprueba que leer y reescribir con el modulo
    csv da el archivo exacto: asi comparar este texto es comparar los bytes del archivo fuera de esa columna."""
    with open(ruta, newline="") as f:
        original = f.read()
    filas = list(csv.reader(io.StringIO(original, newline="")))
    buf = io.StringIO()
    csv.writer(buf).writerows(filas)
    assert buf.getvalue() == original, f"{ruta}: leer y reescribir no da el mismo texto"
    if columna in filas[0]:
        i = filas[0].index(columna)
        filas = [filas[0]] + [f[:i] + [""] + f[i + 1:] for f in filas[1:]]
    buf = io.StringIO()
    csv.writer(buf).writerows(filas)
    return buf.getvalue()


def comparar_csv_bytes(a, b, columna="segundos"):
    """(iguales, texto): los dos CSV son iguales byte a byte salvo la columna (misma cabecera y filas)."""
    ta, tb = texto_sin(a, columna), texto_sin(b, columna)
    if ta == tb:
        return True, f"iguales byte a byte salvo '{columna}' ({len(ta.splitlines()) - 1} filas)"
    la, lb = ta.splitlines(), tb.splitlines()
    k = next((i for i, (x, y) in enumerate(zip(la, lb)) if x != y), min(len(la), len(lb)))
    return False, f"DISTINTOS: {len(la) - 1} y {len(lb) - 1} filas; primera linea distinta: {k}"


def comparar_columnas(a, b, ignorar=("segundos",), filas=None):
    """(iguales, texto) en las columnas comunes (salvo ignorar), fila por fila; filas = cuantas comparar (todas)."""
    with open(a, newline="") as f:
        ra = list(csv.DictReader(f))
    with open(b, newline="") as f:
        rb = list(csv.DictReader(f))
    comunes = [c for c in ra[0] if c in rb[0] and c not in ignorar]
    n = filas or max(len(ra), len(rb))
    if len(ra) < n or len(rb) < n:
        return False, f"DISTINTOS: faltan filas ({len(ra)} y {len(rb)}, se esperaban {n})"
    difs = [(k + 1, c, ra[k][c], rb[k][c]) for k in range(n) for c in comunes if ra[k][c] != rb[k][c]]
    texto = (f"{n} filas, {len(comunes)} columnas comunes (sin {sorted(ignorar)}), {len(difs)} diferencias"
             + "".join(f"\n    fila {d[0]} {d[1]}: {d[2]} | {d[3]}" for d in difs[:10]))
    return not difs, texto


def tensores(ruta):
    return torch.load(ruta, weights_only=True)


def tensores_estado(ruta):
    """Un .estado.pt entero (dict), como lo lee rl_ippo."""
    return torch.load(ruta, weights_only=True)


def comparar_pt(a, b):
    """(iguales, texto): torch.equal en todos los tensores del state_dict y las mismas claves."""
    x, y = tensores(a), tensores(b)
    iguales = sum(1 for k in x if k in y and torch.equal(x[k], y[k]))
    ok = iguales == len(x) and set(x) == set(y)
    return ok, f"{iguales}/{len(x)} tensores iguales (torch.equal), claves iguales {set(x) == set(y)}"


def comparar_json(a, b, ignorar=()):
    """(iguales, texto): mismo contenido salvo las claves de ignorar."""
    with open(a, encoding="utf-8") as f:
        x = json.load(f)
    with open(b, encoding="utf-8") as f:
        y = json.load(f)
    difs = [k for k in sorted(set(x) | set(y)) if k not in ignorar and x.get(k) != y.get(k)]
    extra = f" (sin {list(ignorar)})" if ignorar else ""
    return not difs, (f"meta igual{extra}" if not difs else f"meta DISTINTO{extra} en {difs[:8]}")


def checkpoints(carpeta_corrida, tag, ext=".pt"):
    """{episodio: ruta} de los checkpoints (o estados, con ext='.estado.pt') de un tag en una carpeta de corrida."""
    res = {}
    for r in (Path(carpeta_corrida) / "checkpoints").glob(f"{tag}_ep*{ext}"):
        nombre = r.name[len(tag) + 3:-len(ext)]
        if nombre.isdigit():
            res[int(nombre)] = r
    return res


def comparar_checkpoints(ca, ta, cb, tb, ignorar_json=()):
    """Todos los checkpoints de dos corridas: mismos episodios, tensores iguales y .json iguales (salvo claves)."""
    pa, pb = checkpoints(ca, ta), checkpoints(cb, tb)
    lineas, ok = [], sorted(pa) == sorted(pb)
    lineas.append(f"episodios con checkpoint: {sorted(pa)} | {sorted(pb)}")
    for ep in sorted(set(pa) & set(pb)):
        t_ok, t_txt = comparar_pt(pa[ep], pb[ep])
        j_ok, j_txt = comparar_json(pa[ep].with_suffix(".json"), pb[ep].with_suffix(".json"), ignorar_json)
        ok = ok and t_ok and j_ok
        lineas.append(f"  ep {ep:3d}: {t_txt}; {j_txt}")
    return ok, "\n".join(lineas)


def comparar_estados(a, b, ignorar=()):
    """(iguales, texto) de dos archivos .estado.pt: pesos, Adam (pasos, momentos y grupos), generadores, series,
    tasa, CSV (salvo segundos) y lo demas, salvo las claves de ignorar."""
    x, y = torch.load(a, weights_only=True), torch.load(b, weights_only=True)
    partes = []
    pol = all(torch.equal(x["politica"][k], y["politica"][k]) for k in x["politica"]) and \
        set(x["politica"]) == set(y["politica"])
    partes.append(("pesos", pol))
    ox, oy = x["opt"], y["opt"]
    adam = ox["param_groups"] == oy["param_groups"] and set(ox["state"]) == set(oy["state"]) and all(
        set(ox["state"][i]) == set(oy["state"][i]) and
        all(torch.equal(ox["state"][i][c], oy["state"][i][c]) for c in ox["state"][i]) for i in ox["state"])
    pasos = sorted({float(s["step"]) for s in ox["state"].values()})
    partes.append((f"Adam (paso {pasos}, exp_avg, exp_avg_sq, grupos)", adam))
    gx, gy = x["generadores"], y["generadores"]
    partes.append(("random", gx["random"] == gy["random"]))
    partes.append(("numpy global", gx["numpy"] == gy["numpy"]))
    partes.append(("torch", torch.equal(gx["torch"], gy["torch"])))
    partes.append(("default_rng de sembrar", gx["rng"] == gy["rng"]))

    def sin_seg(texto):
        filas = list(csv.reader(io.StringIO(texto, newline="")))
        i = filas[0].index("segundos")
        return [filas[0]] + [f[:i] + f[i + 1:] for f in filas[1:]]
    partes.append(("CSV hasta el episodio (salvo segundos)", sin_seg(x["csv"]) == sin_seg(y["csv"])))
    resto = [c for c in sorted(set(x) | set(y))
             if c not in ("politica", "opt", "generadores", "csv", "git", "torch", "python") and c not in ignorar]
    distintas = [c for c in resto if x.get(c) != y.get(c)]
    partes.append((f"{', '.join(resto)}" + (f" (distintas: {distintas})" if distintas else ""), not distintas))
    ok = all(v for _, v in partes)
    return ok, "; ".join(f"{n}: {'igual' if v else 'DISTINTO'}" for n, v in partes)


def sha256(ruta):
    import hashlib
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class Informe:
    """Acumula lineas y el resultado de cada comprobacion; escribe salidas/<nombre>.txt."""

    def __init__(self, nombre, titulo):
        self.ruta = SALIDAS / f"{nombre}.txt"
        self.lineas = [titulo, time.strftime("%d.%m.%Y %H:%M") + f"; python {sys.version.split()[0]}, "
                       f"torch {torch.__version__}", ""]
        self.fallas = 0

    def __call__(self, texto=""):
        print(texto, flush=True)
        self.lineas.append(texto)

    def chequeo(self, nombre, ok, detalle=""):
        self.fallas += 0 if ok else 1
        self(f"[{'OK' if ok else 'FALLA'}] {nombre}" + (f": {detalle}" if detalle else ""))
        return ok

    def cerrar(self):
        self("")
        self(f"Resultado: {'todo OK' if not self.fallas else f'{self.fallas} FALLAS'}")
        SALIDAS.mkdir(parents=True, exist_ok=True)
        self.ruta.write_text("\n".join(self.lineas) + "\n", encoding="utf-8")
        return self.fallas
