"""
revalidar_c0.py - Control C0: re-valida SIN reentrenar checkpoints ya guardados con otras semillas de validacion,
elige por retraso total y publica la politica elegida con una etiqueta propia (PLAN3 1.4 y 2.2; DECISIONES B12).

Uso (desde plan3/):
  python revalidar_c0.py validar --escenario ESC --origen CARPETA --corrida TAG --eps 10,20,... --val-seeds S
         --salida parciales/c0/<x>.json
      Valida en ESC los checkpoints CARPETA/TAG_epNNN.pt de --eps y escribe por checkpoint el retraso total y el
      timeLoss medios y por semilla. Retoma: no repite los checkpoints que ya estan en --salida. Si ESC es el
      escenario de entrenamiento, comprueba que las semillas ya guardadas en el meta (999 y 1999) dan exactamente
      lo guardado; si no, sale con error (la validacion no seria la de lo entregado).
  python revalidar_c0.py publicar --escenario ESC --origen CARPETA --corrida TAG --entradas A.json,B.json
         --etiqueta p3c0
      Junta las validaciones, elige el checkpoint con rl_ippo.elegir_checkpoint sobre el retraso total (empate: el
      mas tardio) y publica politica_<ESC>_<variante>_<etiqueta>_s<base>.pt/.json: los mismos tensores del
      checkpoint elegido, con la etiqueta en el meta (asi evaluar.py lo llama ippo_<variante>_<etiqueta>_s<base>).
C0 = los checkpoints de IPPO entregado (insumos/c0_checkpoints) re-elegidos con las 16 semillas; C0 con llegadas
aleatorias = los de la V2 regular re-validados en poi_<caso> (en P6, los de P6e).
"""
import os
import sys
import json
import time
import argparse

PLAN3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(PLAN3))


def escribir_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    tmp = f"{ruta}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=1)
    os.replace(tmp, ruta)


def validar(a, rl_ippo):
    semillas = [int(s) for s in a.val_seeds.split(",")]
    eps = [int(x) for x in a.eps.split(",")]
    res = {"escenario": a.escenario, "corrida": a.corrida, "origen": a.origen, "val_seeds": semillas,
           "checkpoints": []}
    # El avance va a <salida>.parcial; la salida declarada se escribe solo completa, al final. Si el proceso o la cola
    # se cortan, la salida no existe y la cola no da el trabajo por hecho (06.11: un corte dejo diez salidas a medias
    # que la cola tomo por completas). Una salida incompleta de antes se pasa a .parcial y se retoma desde ahi.
    parcial = a.salida + ".parcial"
    if os.path.exists(a.salida) and not os.path.exists(parcial):
        with open(a.salida, encoding="utf-8") as f:
            previa = json.load(f)
        if sorted(c["ep"] for c in previa["checkpoints"]) != sorted(eps):
            os.replace(a.salida, parcial)
    fuente = parcial if os.path.exists(parcial) else (a.salida if os.path.exists(a.salida) else None)
    if fuente:
        with open(fuente, encoding="utf-8") as f:
            res = json.load(f)
        assert res["val_seeds"] == semillas and res["corrida"] == a.corrida, "otra validacion en el mismo archivo"
    hechos = {c["ep"] for c in res["checkpoints"]}
    rl_ippo.preparar(a.escenario)
    # Tripinfo propio de este trabajo y este proceso: los grupos de una misma corrida corren a la vez (revision del
    # 05.11: con un nombre comun, varios SUMO escribian el mismo archivo y el XML se corrompia).
    carpeta_tmp = os.path.join(PLAN3, f"tmp_c0_{os.getpid()}")
    os.makedirs(carpeta_tmp, exist_ok=True)
    tripinfo = os.path.join(carpeta_tmp, f"tripinfo_{os.path.splitext(os.path.basename(a.salida))[0]}_val.xml")
    try:
        _validar_checkpoints(a, rl_ippo, res, hechos, eps, semillas, tripinfo, parcial)
    finally:
        import shutil
        shutil.rmtree(carpeta_tmp, ignore_errors=True)
    faltan = sorted(set(eps) - {c["ep"] for c in res["checkpoints"]})
    if faltan:
        sys.exit(f"faltan checkpoints: {faltan}")
    escribir_json(a.salida, res)
    if os.path.exists(parcial):
        os.remove(parcial)


def _validar_checkpoints(a, rl_ippo, res, hechos, eps, semillas, tripinfo, destino):
    for ep in eps:
        if ep in hechos:
            continue
        ruta = os.path.join(a.origen, f"{a.corrida}_ep{ep:03d}.pt")
        politica, meta = rl_ippo.Politica.cargar(ruta)
        # la observacion, el reloj y los mensajes con que se entreno (como evaluar.brazo_profundo); con las opciones
        # de siempre, nada cambia. La dimension se compara despues de configurar.
        rl_ippo.configurar_desde_meta(meta)
        t0 = time.time()
        try:
            assert meta["dim_obs"] == rl_ippo.C["dim_obs"], (meta["dim_obs"], rl_ippo.C["dim_obs"])
            fila = rl_ippo.validar(politica, semillas, meta["variante"], tripinfo)
        finally:
            rl_ippo.configurar_desde_meta({})
        # Control de reproduccion: solo si se valida en el escenario de entrenamiento.
        control = {}
        if meta.get("escenario", a.escenario) == a.escenario:
            control = {s: (fila[f"val_{s}"], meta[f"val_{s}"]) for s in semillas if meta.get(f"val_{s}") is not None}
            distintos = {s: v for s, v in control.items() if abs(v[0] - v[1]) > 1e-9}
            if distintos:
                sys.exit(f"{ruta}: la validacion no reproduce lo guardado: {distintos}")
        res["checkpoints"].append({"ep": ep, "val": fila["val"], "val_total": fila["val_total"],
                                   **{f"val_{s}": fila[f"val_{s}"] for s in semillas},
                                   **{f"val_total_{s}": fila[f"val_total_{s}"] for s in semillas},
                                   "control_reproducido": sorted(control), "segundos": round(time.time() - t0, 1)})
        res["checkpoints"].sort(key=lambda c: c["ep"])
        escribir_json(destino, res)             # el avance, en .parcial (la salida va completa al final)
        print(f"{a.corrida} ep{ep:03d} en {a.escenario}: validado ({res['checkpoints'][-1]['segundos']} s; "
              f"control {sorted(control) or 'no aplica'})", flush=True)


def publicar(a, rl_ippo):
    import torch
    filas, semillas = [], None
    for ruta in a.entradas.split(","):
        with open(ruta, encoding="utf-8") as f:
            r = json.load(f)
        assert r["corrida"] == a.corrida and r["escenario"] == a.escenario, f"{ruta} es de otra corrida"
        assert semillas is None or r["val_seeds"] == semillas, "validaciones con semillas distintas"
        semillas = r["val_seeds"]
        filas += r["checkpoints"]
    eps = [c["ep"] for c in filas]
    assert len(eps) == len(set(eps)), "un checkpoint validado dos veces"
    filas.sort(key=lambda c: c["ep"])
    serie = [[c["ep"]] + [c[f"val_total_{s}"] for s in semillas] + [c["val_total"]] for c in filas]
    elegido = rl_ippo.elegir_checkpoint(serie)
    ep = elegido[0]
    origen = os.path.join(a.origen, f"{a.corrida}_ep{ep:03d}.pt")
    politica, meta = rl_ippo.Politica.cargar(origen)
    base = meta["base"]
    meta = dict(meta)
    meta.update({"etiqueta": a.etiqueta, "ep_elegido": ep, "val_elegido": elegido[-1],
                 "criterio_val": "total", "val_seeds": semillas, "origen_c0": origen.replace(os.sep, "/"),
                 "escenario_validacion": a.escenario, "val_total_serie": serie,
                 "nota": "control C0 del plan3: checkpoint ya entrenado, re-elegido sin entrenar"})
    destino = f"politica_{a.escenario}_{meta['variante']}_{a.etiqueta}_s{base}.pt"
    politica.guardar(destino, meta)
    a_t = torch.load(origen, weights_only=True)
    b_t = torch.load(destino, weights_only=True)
    assert a_t.keys() == b_t.keys() and all(torch.equal(a_t[k], b_t[k]) for k in a_t), "publicada distinta"
    print(f"{a.corrida} en {a.escenario}: elegido ep{ep:03d}; publicado {destino}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["validar", "publicar"])
    ap.add_argument("--escenario", required=True)
    ap.add_argument("--origen", required=True, help="carpeta de los checkpoints (relativa a plan3/)")
    ap.add_argument("--corrida", required=True, help="nombre de la corrida: <esc>_ippo_<variante>[_<et>]_s<base>")
    ap.add_argument("--eps", default=",".join(str(e) for e in range(10, 201, 10)))
    ap.add_argument("--val-seeds", default=None)
    ap.add_argument("--salida", default=None)
    ap.add_argument("--entradas", default=None)
    ap.add_argument("--etiqueta", default="p3c0")
    a = ap.parse_args()
    import rl_ippo
    if a.modo == "validar":
        assert a.val_seeds and a.salida, "validar necesita --val-seeds y --salida"
        validar(a, rl_ippo)
    else:
        assert a.entradas, "publicar necesita --entradas"
        publicar(a, rl_ippo)


if __name__ == "__main__":
    main()
