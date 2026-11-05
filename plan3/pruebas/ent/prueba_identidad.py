"""
prueba_identidad.py - Pruebas 1 y 2 de la tarea 1.1 del plan 3 (informe: plan3/doc/informe_ent1.md).

  1. Con todo apagado, rl_ippo.py nuevo = rl_ippo.py del tag entregado-2026-10-25: IPPO entregado (sin --v2) y V2
     (--v2 --criterio-val total) en P1 (corredor), base 7, 10 episodios, validacion cada 5 en 424301-424302. CSV byte
     a byte salvo la columna segundos, todos los checkpoints (tensores y .json), politica publicada (bytes) y meta.
  2. --guardar-estado y --registro-extendido no cambian ningun numero (columnas comunes del CSV, checkpoints, politica
     y meta), y evaluar.py juega igual la politica publicada con y sin las opciones (CSV de evaluar en 424303-424304).
  Ademas, ablacion: --solo-descuento mas --solo-exploracion es --v2 (CSV, checkpoints, politica y meta); cada una
  sola hace solo su mitad (el episodio 1 de --solo-descuento juega como IPPO y el de --solo-exploracion como V2, y la
  actualizacion cambia).

Uso (desde cualquier carpeta):  python plan3/pruebas/ent/prueba_identidad.py
Salida: plan3/pruebas/ent/salidas/prueba_identidad.txt; corridas en plan3/tmp_ent/ident_*.
"""
import re
import csv
import sys
import json

import util_ent as u

BASE = ["train", "--escenario", "corredor", "--seed", "7", "--episodios", "10", "--eval-cada", "5",
        "--val-seeds", u.VAL_HUMO]
V2 = ["--v2", "--criterio-val", "total", "--etiqueta", "p3prbv2"]
EXT = ["--guardar-estado", "--registro-extendido"]
TAG_IPPO, TAG_V2 = "corredor_ippo_vecinos_s7", "corredor_ippo_vecinos_p3prbv2_s7"
POL_IPPO, POL_V2 = "politica_corredor_vecinos_s7", "politica_corredor_vecinos_p3prbv2_s7"

CORRIDAS = {   # nombre: (codigo, argumentos, tag de los checkpoints, politica publicada)
    "tag_ippo": ("tag", BASE, TAG_IPPO, POL_IPPO),
    "tag_v2": ("tag", BASE + V2, TAG_V2, POL_V2),
    "nuevo_ippo": ("nuevo", BASE, TAG_IPPO, POL_IPPO),
    "nuevo_v2": ("nuevo", BASE + V2, TAG_V2, POL_V2),
    "nuevo_ippo_ext": ("nuevo", BASE + EXT, TAG_IPPO, POL_IPPO),
    "nuevo_v2_ext": ("nuevo", BASE + V2 + EXT, TAG_V2, POL_V2),
    "nuevo_solos": ("nuevo", BASE + ["--solo-descuento", "--solo-exploracion", "--criterio-val", "total",
                                     "--etiqueta", "p3prbv2"], TAG_V2, POL_V2),
    "nuevo_desc": ("nuevo", BASE + ["--solo-descuento", "--criterio-val", "total", "--etiqueta", "p3prbv2"],
                   TAG_V2, POL_V2),
    "nuevo_expl": ("nuevo", BASE + ["--solo-exploracion", "--criterio-val", "total", "--etiqueta", "p3prbv2"],
                   TAG_V2, POL_V2),
}


def main():
    inf = u.Informe("prueba_identidad", "Pruebas 1 y 2 (tarea 1.1): identidad con el tag y opciones que no cambian "
                    "numeros; ablacion de V2. P1, base 7, 10 episodios, validacion cada 5 en " + u.VAL_HUMO)
    script_tag = u.codigo_tag()
    trabajos, carpetas = [], {}
    for nombre, (codigo, argumentos, _, _) in CORRIDAS.items():
        c = u.carpeta(f"ident_{nombre}", ["corredor"])
        carpetas[nombre] = c
        trabajos.append((script_tag if codigo == "tag" else u.RL_NUEVO, argumentos, c, c / "log.txt"))
    codigos = u.en_tandas(trabajos, maximo=3)
    for (nombre, (codigo, argumentos, _, _)), cod in zip(CORRIDAS.items(), codigos):
        inf.chequeo(f"corrida {nombre} ({codigo}: {' '.join(argumentos[1:])})", cod == 0, f"codigo {cod}")

    def csv_de(n):
        return carpetas[n] / f"resultados_{CORRIDAS[n][2]}.csv"

    def pol(n):
        return carpetas[n] / f"{CORRIDAS[n][3]}.pt"

    def misma_corrida(a, b, bytes_csv=True):
        inf(f"-- {a} frente a {b}")
        if bytes_csv:
            inf.chequeo("CSV", *u.comparar_csv_bytes(csv_de(a), csv_de(b)))
        else:
            inf.chequeo("CSV en las columnas comunes", *u.comparar_columnas(csv_de(a), csv_de(b)))
            with open(csv_de(a), newline="") as f:
                ca = next(csv.reader(f))
            with open(csv_de(b), newline="") as f:
                cb = next(csv.reader(f))
            inf.chequeo("cabecera = la del tag + columnas al final", ca[:len(cb)] == cb,
                        f"{len(cb)} columnas del tag, {len(ca) - len(cb)} al final: {ca[len(cb):]}")
        inf.chequeo("checkpoints", *u.comparar_checkpoints(carpetas[a], CORRIDAS[a][2], carpetas[b], CORRIDAS[b][2]))
        inf.chequeo("politica publicada (tensores)", *u.comparar_pt(pol(a), pol(b)))
        inf.chequeo("politica publicada (bytes)", u.sha256(pol(a)) == u.sha256(pol(b)))
        inf.chequeo("meta publicado", *u.comparar_json(pol(a).with_suffix(".json"), pol(b).with_suffix(".json")))

    def log_sin_tiempos(n):
        return [re.sub(r"\d+\.\d+s( |$)", r"Xs\1", linea)
                for linea in (carpetas[n] / "log.txt").read_text(encoding="utf-8").splitlines()]

    inf("")
    inf("Prueba 1: todo apagado = tag")
    misma_corrida("nuevo_ippo", "tag_ippo")
    misma_corrida("nuevo_v2", "tag_v2")
    for a, b in (("nuevo_ippo", "tag_ippo"), ("nuevo_v2", "tag_v2")):
        inf.chequeo(f"log de consola de {a} = el de {b} (salvo los segundos)", log_sin_tiempos(a) == log_sin_tiempos(b),
                    f"{len(log_sin_tiempos(a))} lineas")
    inf("")
    inf("Prueba 2: --guardar-estado y --registro-extendido no cambian ningun numero")
    misma_corrida("nuevo_ippo_ext", "tag_ippo", bytes_csv=False)
    misma_corrida("nuevo_v2_ext", "tag_v2", bytes_csv=False)
    for n in ("nuevo_ippo_ext", "nuevo_v2_ext"):
        estados = u.checkpoints(carpetas[n], CORRIDAS[n][2], ".estado.pt")
        inf.chequeo(f"{n}: un estado por checkpoint", sorted(estados) == [5, 10], f"estados en {sorted(estados)}")
    inf("evaluar.py con la politica publicada sin y con las opciones (semillas " + u.EVAL_HUMO + ")")
    for sin, con in (("nuevo_ippo", "nuevo_ippo_ext"), ("nuevo_v2", "nuevo_v2_ext")):
        trabajos = [(u.EVALUAR, ["--escenario", "corredor", "--politica", pol(n).name, "--semillas", u.EVAL_HUMO,
                                 "--salida", "eval_humo.csv"], carpetas[n], carpetas[n] / "log_evaluar.txt")
                    for n in (sin, con)]
        cods = u.en_tandas(trabajos, maximo=2)
        inf.chequeo(f"evaluar {sin} y {con}", cods == [0, 0], f"codigos {cods}")
        a, b = carpetas[sin] / "eval_humo.csv", carpetas[con] / "eval_humo.csv"
        iguales = a.read_bytes() == b.read_bytes()
        inf.chequeo(f"CSV de evaluar de {sin} = el de {con} (byte a byte)", iguales,
                    f"{len(a.read_text().splitlines()) - 1} semillas")
    inf("")
    inf("Ablacion: --solo-descuento --solo-exploracion = --v2; cada una sola hace su mitad")
    misma_corrida("nuevo_solos", "tag_v2")

    def fila(n, k=0):
        with open(csv_de(n), newline="") as f:
            return list(csv.DictReader(f))[k]
    juego = ["timeloss_prom", "espera_prom", "cambios_fase", "decisiones", "decisiones_libres", "expl_minoritaria",
             "dt_medio"]
    actualizacion = ["perdida_politica", "perdida_valor", "kl_aprox", "clipfrac"]
    for n, igual_a, distinto_de in (("nuevo_desc", "tag_ippo", "tag_v2"), ("nuevo_expl", "tag_v2", "tag_ippo")):
        f, g = fila(n), fila(igual_a)
        inf.chequeo(f"{n}: el episodio 1 juega como {igual_a}", all(f[c] == g[c] for c in juego),
                    ", ".join(f"{c} {f[c]}|{g[c]}" for c in juego[:3]))
        inf.chequeo(f"{n}: la actualizacion del episodio 1 no es la de {igual_a}",
                    any(f[c] != g[c] for c in actualizacion),
                    ", ".join(f"{c} {f[c]}|{g[c]}" for c in actualizacion[:2]))
        ok, txt = u.comparar_columnas(csv_de(n), csv_de(distinto_de))
        inf.chequeo(f"{n}: el entrenamiento no es el de {distinto_de}", not ok, txt.splitlines()[0])
        with open(pol(n).with_suffix(".json"), encoding="utf-8") as fj:
            meta = json.load(fj)
        inf(f"   meta de {n}: opciones {meta['opciones']}; descuento '{meta['descuento']}'; "
            f"exploracion '{meta['exploracion']}'")
    return inf.cerrar()


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
