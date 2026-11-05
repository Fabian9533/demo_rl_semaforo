"""
prueba_etapa4.py - Pruebas de las opciones de la politica por red en rl_ippo.py (PLAN3 Etapa 4; DECISIONES B16).
Informe: plan3/doc/informe_ent2.md. Semillas de humo (424301-424302; entrenamiento con base 7).

  1. --scale 0.5 reproduce dem_corredor_t905: el corredor con --scale 0.5 y dem_corredor_t905 sin escala, con el mismo
     decisor (ciclo minimo) y la misma semilla, dan las mismas metricas y los mismos viajes (id, salida, llegada y
     timeLoss). Ademas --scale 1 = sin escala, y --scale 1.5 multiplica los vehiculos.
  2. Un entrenamiento corto con --escala-demanda 0.5,2.0 --curriculo 3 --val-escalas 0.5,1,1.5 --norm-valor
     --norm-beta 0.99: la columna escala sigue el sorteo (default_rng(base + 15485863), tope que sube en 3 episodios);
     cada nivel de la validacion es la media de sus semillas y val_total es su media geometrica (en el CSV, en cada
     checkpoint y en la serie que elige la politica); el meta trae las opciones.

Uso:  python plan3/pruebas/ent/prueba_etapa4.py
Salida: plan3/pruebas/ent/salidas/prueba_etapa4.txt; corridas en plan3/tmp_ent/e4_*.
"""
import csv
import sys
import json

import numpy as np

import util_ent as u

TRABAJO = u.AQUI / "trabajo_e3.py"
ESCALAS_VAL = [0.5, 1.0, 1.5]
SEMILLAS = [424301, 424302]


def geometrica(valores):
    return round(float(np.exp(np.mean(np.log(np.asarray(valores, dtype=np.float64))))), 3)


def prueba_scale(inf):
    inf("1. --scale 0.5 frente a dem_corredor_t905 (ciclo minimo, semilla 424301)")
    c = u.carpeta("e4_scale", ["corredor", "dem_corredor_t905"])
    (c / "p.json").write_text(json.dumps({"escenario": "corredor", "semilla": 424301}), encoding="utf-8")
    cod = u.correr(TRABAJO, ["escala", "p.json", "salida.json"], c, c / "log.txt")
    inf.chequeo("la corrida termina", cod == 0, f"codigo {cod}")
    d = json.loads((c / "salida.json").read_text(encoding="utf-8"))
    a, b = d["corredor_x0.5"], d["t905"]
    distintas = [k for k in a["res"] if a["res"][k] != b["res"].get(k)]
    inf.chequeo("--scale 0.5 = dem_corredor_t905: mismas metricas y mismos viajes",
                not distintas and a["viajes"] == b["viajes"],
                f"{len(a['viajes'])} viajes; vehiculos {a['res']['vehiculos']} | {b['res']['vehiculos']}; timeLoss "
                f"{a['res']['timeloss_prom']} | {b['res']['timeloss_prom']}; distintas: {distintas[:5]}")
    x1, base = d["corredor_x1"], d["corredor"]
    inf.chequeo("--scale 1 = sin escala", x1["res"] == base["res"] and x1["viajes"] == base["viajes"],
                f"vehiculos {x1['res']['vehiculos']} | {base['res']['vehiculos']}")
    n0, n15 = base["res"]["vehiculos"], d["corredor_x1.5"]["res"]["vehiculos"]
    inf.chequeo("--scale 1.5 multiplica los vehiculos por ~1.5", abs(n15 / n0 - 1.5) < 0.02,
                f"{n0} -> {n15} (x{n15 / n0:.3f})")
    return n0


def prueba_entrenamiento(inf, vehiculos_base):
    inf("")
    inf("2. Entrenamiento corto con escala por episodio y validacion por niveles (P1, base 7, 4 episodios)")
    c = u.carpeta("e4_entreno", ["corredor"])
    tag, pol = "corredor_ippo_vecinos_p3prbe4_s7", "politica_corredor_vecinos_p3prbe4_s7"
    argumentos = ["train", "--escenario", "corredor", "--seed", "7", "--episodios", "4", "--eval-cada", "2",
                  "--val-seeds", ",".join(map(str, SEMILLAS)), "--v2", "--criterio-val", "total",
                  "--etiqueta", "p3prbe4", "--guardar-estado", "--registro-extendido",
                  "--escala-demanda", "0.5,2.0", "--curriculo", "3", "--val-escalas", "0.5,1,1.5",
                  "--norm-valor", "--norm-beta", "0.99"]
    inf(f"   rl_ippo.py {' '.join(argumentos)}")
    cod = u.correr(u.RL_NUEVO, argumentos, c, c / "log.txt")
    inf.chequeo("entrena y publica", cod == 0 and (c / f"{pol}.pt").exists(), f"codigo {cod}")
    with open(c / f"resultados_{tag}.csv", newline="") as f:
        filas = list(csv.DictReader(f))
    rng = np.random.default_rng(7 + 15485863)
    esperadas = [round(float(rng.uniform(0.5, 0.5 + 1.5 * min(1.0, ep / 3))), 4) for ep in range(1, 5)]
    escalas = [float(x["escala"]) for x in filas]
    inf.chequeo("la columna escala sigue el sorteo (con el tope del curriculo: 1.0, 1.5, 2.0, 2.0)",
                escalas == esperadas, f"{escalas} | esperadas {esperadas}")
    veh = [int(x["vehiculos"]) for x in filas]
    inf(f"   vehiculos por episodio {veh}; escala x {vehiculos_base} (sin escala): "
        f"{[round(e * vehiculos_base) for e in escalas]}")
    inf.chequeo("los vehiculos siguen la escala (+-2 %)",
                all(abs(v / (e * vehiculos_base) - 1) < 0.02 for v, e in zip(veh, escalas)))
    xs = ["_x0.5", "_x1", "_x1.5"]
    for x in filas:
        if not x["val_total"]:
            continue
        geo = geometrica([float(x[f"val_total{s}"]) for s in xs])
        inf.chequeo(f"CSV, episodio {x['episodio']}: val_total = media geometrica de los niveles",
                    float(x["val_total"]) == geo, f"{[x[f'val_total{s}'] for s in xs]} -> {x['val_total']} ({geo})")
    for ruta in sorted((c / "checkpoints").glob(f"{tag}_ep*.json")):
        m = json.loads(ruta.read_text(encoding="utf-8"))
        niveles = [round(float(np.mean([m[f"val_total_{s}{x}"] for s in SEMILLAS])), 3) for x in xs]
        ok = all(m[f"val_total{x}"] == n for x, n in zip(xs, niveles)) and \
            m["val_total_checkpoint"] == geometrica(niveles) and \
            m["val_checkpoint"] == geometrica([round(float(np.mean([m[f"val_{s}{x}"] for s in SEMILLAS])), 3)
                                               for x in xs])
        inf.chequeo(f"checkpoint del ep {m['ep_checkpoint']}: cada nivel es la media de sus semillas y val_total su "
                    "media geometrica", ok, f"niveles {niveles} -> {m['val_total_checkpoint']}")
    meta = json.loads((c / f"{pol}.json").read_text(encoding="utf-8"))
    serie_ok = all(len(f) == 5 and f[-1] == geometrica(f[1:4]) for f in meta["val_total_serie"])
    inf.chequeo("la serie que elige la politica: [ep, nivel 0.5, nivel 1, nivel 1.5, geometrica]", serie_ok,
                f"{meta['val_total_serie']}; elegido el ep {meta['ep_elegido']} (val {meta['val_elegido']})")
    op = meta["opciones"]
    inf.chequeo("meta: opciones de la politica por red", op.get("escala_demanda") == [0.5, 2.0] and
                op.get("curriculo") == 3 and op.get("val_escalas") == ESCALAS_VAL and op.get("norm_valor") is True
                and op.get("norm_beta") == 0.99, f"{op}")
    inf.chequeo("--norm-valor: columnas vn_media y vn_desv", all(x["vn_media"] and x["vn_desv"] for x in filas),
                f"vn_media {[x['vn_media'] for x in filas]}")
    # revision del 05.11 (R3-5 y R5-4): eval_* del nivel 1 y la escala del critico en los meta
    s0 = SEMILLAS[0]
    cks = {int(r.name[len(tag) + 3:len(tag) + 6]): json.loads(r.read_text(encoding="utf-8"))
           for r in sorted((c / "checkpoints").glob(f"{tag}_ep*.json"))}
    ok_eval = all(x["eval_timeloss"] == "" or float(x["eval_timeloss"]) == cks[int(x["episodio"])][f"val_{s0}_x1"]
                  for x in filas if x["val_total"]) and all(x["eval_timeloss"] for x in filas if x["val_total"])
    inf.chequeo("eval_timeloss de cada validacion = la primera semilla en el nivel 1",
                ok_eval, f"{[(x['episodio'], x['eval_timeloss']) for x in filas if x['val_total']]}")
    ultimo = cks[max(cks)]
    inf.chequeo("meta publicado: eval_nivel 1.0 y eval_999_final = la primera semilla en el nivel 1 del ultimo "
                "checkpoint", meta.get("eval_nivel") == 1.0 and meta["eval_999_final"] == ultimo[f"val_{s0}_x1"],
                f"eval_nivel {meta.get('eval_nivel')}, eval_999_final {meta['eval_999_final']} | "
                f"{ultimo[f'val_{s0}_x1']}")
    elegido = cks[meta["ep_elegido"]]
    inf.chequeo("--norm-valor: cada checkpoint guarda vn_media, vn_desv y vn_estado; el meta publicado, los del "
                "elegido", all(all(k in m for k in ("vn_media", "vn_desv", "vn_estado")) for m in cks.values())
                and all(meta.get(k) == elegido[k] for k in ("vn_media", "vn_desv", "vn_estado")),
                f"{[(e, m.get('vn_media'), m.get('vn_desv')) for e, m in cks.items()]}; publicado "
                f"{meta.get('vn_media')}, {meta.get('vn_desv')}")


def main():
    inf = u.Informe("prueba_etapa4", "Opciones de la politica por red en rl_ippo.py (PLAN3 Etapa 4)")
    n0 = prueba_scale(inf)
    prueba_entrenamiento(inf, n0)
    return inf.cerrar()


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
