"""
p3_insumos.py - Copia a plan3/ lo entregado que usa el bloque, sin escribir en el origen, con su manifiesto sha256.

Uso (desde <worktree>/plan3):  python p3_insumos.py [--diag RUTA] [--revisar]

Copia:
  .                          escenarios base (cada .sumocfg de ESCENARIOS y los archivos que nombra), desde ../plan2
  insumos/entregado/         politicas IPPO con mensajes entregadas (politica_<esc>_vecinos_s<b>.pt), 18 celdas
  insumos/puente/            CSV de evaluacion entregados en 1001-1030 (fijo, actuado, trivial, IPPO con mensajes)
  insumos/c0_checkpoints/    checkpoints de IPPO entregado (C0), 18 celdas x 3 bases x 20 (ignorado por git)
  insumos/v2diag_checkpoints/ checkpoints de la V2 del diagnostico del corredor (demo_rl_diag; ignorado por git)
Escribe insumos/manifiesto.json = {grupo: {ruta relativa al grupo: [bytes, sha256]}}. Con --revisar solo compara.
Si un destino ya existe con otro contenido, se detiene: un insumo nunca se pisa en silencio.
"""
import os
import sys
import json
import shutil
import hashlib
import argparse
import xml.etree.ElementTree as ET

PLAN3 = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PLAN3)
PLAN2 = os.path.join(RAIZ, "plan2")
# Los checkpoints no estan en git: se leen del respaldo verificado del 05.11.2026 (sha256 igual al origen).
RESPALDO = os.path.join(os.path.dirname(RAIZ), "respaldo_checkpoints_2026-11-05")
CKPT_DEF = os.path.join(RESPALDO, "demo_rl", "checkpoints")
DIAG_DEF = os.path.join(RESPALDO, "demo_rl_diag", "checkpoints")

CASOS = ["corredor", "corredor_alta", "red", "red_alta", "malla3", "malla3_alta"]
NIVELES = ["dem_corredor_t905", "dem_corredor_t1358", "dem_corredor_t2715",
           "dem_red_t905", "dem_red_t1358", "dem_red_t1810", "dem_red_t2715", "dem_red_t3620",
           "dem_malla3_t1810", "dem_malla3_t2715", "dem_malla3_t3620", "dem_malla3_t6525"]
EXTRA = ["dem_corredor_t2715_der"]          # D: 2715 veh/h con los giros a la derecha (banco barato)
ESCENARIOS = CASOS + NIVELES + EXTRA
CELDAS_C0 = CASOS + NIVELES                 # 18 celdas con IPPO entregado
BASES = [42, 2042, 4042]
BRAZOS_PUENTE = ["fijo", "actuado", "trivial"] + [f"ippo_vecinos_s{b}" for b in BASES]
DIAG_V2 = ["corredor", "corredor_alta", "dem_corredor_t905", "dem_corredor_t1358", "dem_corredor_t2715",
           "dem_corredor_t2715_der"]
MANIFIESTO = os.path.join(PLAN3, "insumos", "manifiesto.json")


def sha(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def archivos_de_cfg(cfg):
    """El .sumocfg y los archivos que nombra (net, rutas, adicionales), relativos a su carpeta."""
    raiz = ET.parse(cfg).getroot()
    salida = [os.path.basename(cfg)]
    for etiqueta in ("net-file", "route-files", "additional-files"):
        for nodo in raiz.iter(etiqueta):
            salida += [v.strip() for v in nodo.get("value", "").split(",") if v.strip()]
    return salida


def plan_de_copias(ckpt, diag):
    """Lista de (grupo, ruta relativa al grupo, origen)."""
    copias = []
    vistos = set()
    for esc in ESCENARIOS:
        for rel in archivos_de_cfg(os.path.join(PLAN2, f"{esc}.sumocfg")):
            if rel not in vistos:
                vistos.add(rel)
                copias.append((".", rel, os.path.join(PLAN2, rel)))
    for esc in CELDAS_C0:
        for b in BASES:
            for ext in (".pt", ".json"):             # la politica y su meta (Politica.cargar lee los dos)
                rel = f"politica_{esc}_vecinos_s{b}{ext}"
                copias.append(("insumos/entregado", rel, os.path.join(PLAN2, rel)))
            for ep in range(10, 201, 10):
                for ext in (".pt", ".json"):
                    rel = f"{esc}_ippo_vecinos_s{b}_ep{ep:03d}{ext}"
                    copias.append(("insumos/c0_checkpoints", rel, os.path.join(ckpt, rel)))
    for esc in CASOS:
        for brazo in BRAZOS_PUENTE:
            rel = f"eval_{esc}_{brazo}.csv"
            copias.append(("insumos/puente", rel, os.path.join(PLAN2, "parciales", rel)))
    for esc in DIAG_V2:
        for b in BASES:
            for ep in range(10, 201, 10):
                for ext in (".pt", ".json"):
                    rel = f"{esc}_ippo_vecinos_v2_s{b}_ep{ep:03d}{ext}"
                    copias.append(("insumos/v2diag_checkpoints", rel, os.path.join(diag, rel)))
    return copias


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoints", default=CKPT_DEF, help="checkpoints entregados (respaldo de plan2/checkpoints)")
    ap.add_argument("--diag", default=DIAG_DEF, help="checkpoints del diagnostico del corredor (respaldo)")
    ap.add_argument("--revisar", action="store_true", help="solo compara las copias con el manifiesto")
    args = ap.parse_args()
    if args.revisar:
        esperado = json.load(open(MANIFIESTO, encoding="utf-8"))
        malos = [f"{g}/{r}" for g, archivos in esperado.items() for r, (_, h) in archivos.items()
                 if not os.path.exists(os.path.join(PLAN3, g, r)) or sha(os.path.join(PLAN3, g, r)) != h]
        print(f"{sum(len(a) for a in esperado.values())} insumos; {len(malos)} distintos o ausentes")
        for m in malos[:20]:
            print("  ", m)
        sys.exit(1 if malos else 0)
    copias = plan_de_copias(args.checkpoints, args.diag)
    faltan = [o for _, _, o in copias if not os.path.exists(o)]
    if faltan:
        sys.exit(f"faltan {len(faltan)} origenes, p. ej. {faltan[:3]}")
    manifiesto = {}
    for grupo, rel, origen in copias:
        destino = os.path.join(PLAN3, grupo, rel)
        h = sha(origen)
        if os.path.exists(destino):
            if sha(destino) != h:
                sys.exit(f"{grupo}/{rel} ya existe con otro contenido; no se pisa")
        else:
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            shutil.copyfile(origen, destino)
            if sha(destino) != h:
                sys.exit(f"copia distinta del origen: {grupo}/{rel}")
        manifiesto.setdefault(grupo, {})[rel] = [os.path.getsize(destino), h]
    os.makedirs(os.path.dirname(MANIFIESTO), exist_ok=True)
    with open(MANIFIESTO, "w", encoding="utf-8") as f:
        json.dump(manifiesto, f, indent=0, sort_keys=True)
    for grupo, archivos in sorted(manifiesto.items()):
        print(f"{grupo}: {len(archivos)} archivos")


if __name__ == "__main__":
    main()
