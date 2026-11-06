"""
analizar_largo.py - Estabilidad numerica de una corrida larga del modelo completo (revision del 05.11, punto h).

La corrida: rl_ippo.py del commit 5b2a32d (copiado a tmp_ent/codigo_largo), dem_corredor_t2715_der (D), base 7,
400 episodios, --eval-cada 10 --val-seeds 999,1999, con las opciones del modelo completo del generador (OP_COMPLETO:
--obs-cercana 75 --norm-valor --sin-forzadas --msg-cada-paso --lr-horizonte 200 --lr-piso 0.1 --paso-decision 2) y
--v2 --criterio-val total --guardar-estado --registro-extendido. Este guion solo lee sus archivos:
  - NaN o inf en cualquier celda numerica del CSV, en los pesos de cada checkpoint y en el estado final;
  - por bloques de 50 episodios: segundos por episodio, var_explicada, vn_media y vn_desv, entropia, KL, perdida
    del critico (en unidades normalizadas), timeLoss de entrenamiento y la validacion (retraso total).

Uso:  python plan3/pruebas/ent/analizar_largo.py [carpeta]   (por defecto plan3/tmp_ent/largo_e3c_t2715d)
Salida: plan3/pruebas/ent/salidas/largo_completo_d.txt
"""
import sys
import csv
import json
import math
from pathlib import Path

import numpy as np
import torch

import util_ent as u

TAG = "dem_corredor_t2715_der_ippo_vecinos_p3largo_s7"
POL = "politica_dem_corredor_t2715_der_vecinos_p3largo_s7"


def numero(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def finitos(obj):
    """(tensores revisados, no finitos) de un state_dict o de un estado entero (recorre dicts y listas)."""
    n = malos = 0
    if isinstance(obj, torch.Tensor):
        if obj.is_floating_point():
            return 1, int(not bool(torch.isfinite(obj).all()))
        return 0, 0
    if isinstance(obj, dict):
        obj = list(obj.values())
    if isinstance(obj, (list, tuple)):
        for x in obj:
            a, b = finitos(x)
            n, malos = n + a, malos + b
    return n, malos


def main():
    c = Path(sys.argv[1]) if len(sys.argv) > 1 else u.TMP / "largo_e3c_t2715d"
    inf = u.Informe("largo_completo_d", "Corrida larga del modelo completo en D (dem_corredor_t2715_der), base 7, "
                    "400 episodios, validacion cada 10 en 999,1999 (revision del 05.11, punto h)")
    with open(c / f"resultados_{TAG}.csv", newline="") as f:
        filas = list(csv.DictReader(f))
    horas = " ".join((c / "inicio.txt").read_text().split()) if (c / "inicio.txt").exists() else "sin inicio.txt"
    inf(f"{len(filas)} episodios en el CSV; reloj de la corrida: {horas}")
    no_finitos = [(r["episodio"], k, v) for r in filas for k, v in r.items()
                  if v and numero(v) is not None and not math.isfinite(numero(v))]
    texto_nan = [(r["episodio"], k) for r in filas for k, v in r.items() if v and v.lower() in ("nan", "inf", "-inf")]
    inf.chequeo("ninguna celda del CSV es NaN o inf", not no_finitos and not texto_nan,
                f"{len(no_finitos)} no finitas: {no_finitos[:5]}")
    vacias = [r["episodio"] for r in filas if r["perdida_politica"] == ""]
    inf.chequeo("todos los episodios actualizaron (ningun lote vacio)", not vacias, f"{vacias[:5]}")
    pts = sorted((c / "checkpoints").glob(f"{TAG}_ep*.pt"))
    pts = [p for p in pts if not p.name.endswith(".estado.pt")]
    revisados = malos = 0
    for p in pts:
        a, b = finitos(torch.load(p, weights_only=True))
        revisados, malos = revisados + a, malos + b
    estados = sorted((c / "checkpoints").glob(f"{TAG}_ep*.estado.pt"))
    if estados:
        a, b = finitos(torch.load(estados[-1], weights_only=True))
        revisados, malos = revisados + a, malos + b
    inf.chequeo(f"pesos finitos en los {len(pts)} checkpoints y en el ultimo estado (pesos, Adam, generadores)",
                malos == 0 and revisados > 0, f"{revisados} tensores, {malos} con NaN o inf")
    inf("")
    inf("Por bloques de 50 episodios (medias; vn al final del bloque; validacion: retraso total medio en 999 y 1999)")
    inf("   episodios | s/ep (mediana) | var_explicada | vn_media  vn_desv | entropia  kl     | perdida_valor | "
        "timeLoss | validacion")
    for ini in range(0, len(filas), 50):
        b = filas[ini:ini + 50]
        med = lambda k: float(np.mean([numero(r[k]) for r in b if numero(r[k]) is not None]))
        val = [numero(r["val_total"]) for r in b if numero(r.get("val_total")) is not None]
        inf(f"   {b[0]['episodio']:>3}-{b[-1]['episodio']:<3}   | {np.median([float(r['segundos']) for r in b]):6.1f}"
            f"         | {med('var_explicada'):8.3f}      | {numero(b[-1]['vn_media']):8.3f} {numero(b[-1]['vn_desv']):7.3f} "
            f"| {med('entropia_libre'):6.3f}  {med('kl_aprox'):.4f} | {med('perdida_valor'):9.4f}     | "
            f"{med('timeloss_prom'):6.2f}   | {', '.join(f'{v:.1f}' for v in val)}")
    meta_ruta = c / f"{POL}.json"
    if meta_ruta.exists():
        meta = json.loads(meta_ruta.read_text(encoding="utf-8"))
        inf("")
        inf(f"Publicada: ep {meta['ep_elegido']} (val_total {meta['val_elegido']}); vn_media {meta.get('vn_media')}, "
            f"vn_desv {meta.get('vn_desv')} (el codigo de 5b2a32d no guardaba la escala del critico en el meta)")
    seg = [float(r["segundos"]) for r in filas]
    inf(f"Tiempo por episodio de entrenamiento (sin validacion): mediana {np.median(seg):.1f} s, "
        f"p90 {np.percentile(seg, 90):.1f} s, total {sum(seg) / 3600:.2f} h")
    return inf.cerrar()


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
