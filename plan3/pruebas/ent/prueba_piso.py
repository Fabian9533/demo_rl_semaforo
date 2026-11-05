"""
prueba_piso.py - Tasa con piso (tarea 1.2 del plan 3, d; informe: plan3/doc/informe_ent1.md).

Una corrida de 400 episodios con --lr-horizonte 200 --lr-piso 0.1 debe repetir los episodios 1-181 de una de 200
sin piso (el diseno lo midio en 10 episodios: plan3/modelo/salidas/m4_identidad.txt). Aqui en los 181: V2 en P1,
base 7, validacion cada 10 en 424301-424302, las dos cortadas con --hasta-ep 181. Se comparan el CSV (todas las
columnas salvo segundos), los checkpoints 10-180 (tensores y validacion) y los estados; ademas la formula de la tasa
en todos los episodios.

Uso:  python plan3/pruebas/ent/prueba_piso.py [--sin-correr]   (~2 procesos durante ~20 min; con --sin-correr solo
      compara las corridas que ya estan en tmp_ent, hechas por este guion)
Salida: plan3/pruebas/ent/salidas/prueba_piso.txt; corridas en plan3/tmp_ent/piso_200 y piso_400.
"""
import sys

import torch

import util_ent as u

TAG = "corredor_ippo_vecinos_p3prbpiso_s7"
BASE = ["train", "--escenario", "corredor", "--seed", "7", "--eval-cada", "10", "--val-seeds", u.VAL_HUMO,
        "--v2", "--criterio-val", "total", "--guardar-estado", "--etiqueta", "p3prbpiso", "--hasta-ep", "181"]


def main():
    inf = u.Informe("prueba_piso", "Tasa con piso: 400 episodios con --lr-horizonte 200 --lr-piso 0.1 frente a 200 "
                    "sin piso, episodios 1-181 (V2 en P1, base 7)")
    sys.path.insert(0, str(u.RAIZ))
    import rl_ippo
    sin = [rl_ippo.tasa(ep, 200) for ep in range(1, 201)]
    con = [rl_ippo.tasa(ep, 200, 0.1) for ep in range(1, 401)]
    iguales = [ep for ep in range(1, 201) if sin[ep - 1] == con[ep - 1]]
    inf.chequeo("formula: la tasa es la misma (bit a bit) en los episodios 1-180",
                iguales == list(range(1, 181)), f"iguales en 1-{max(iguales)}; ep 181: {sin[180]!r} | {con[180]!r}; "
                f"ep 182: {sin[181]!r} | {con[181]!r}; ep 400 con piso: {con[399]!r}")
    inf.chequeo("formula: sin piso es la de siempre (lr0 * (1 - (ep - 1) / 200))",
                all(sin[ep - 1] == 1e-3 * (1 - (ep - 1) / 200) for ep in range(1, 201)))
    if "--sin-correr" in sys.argv:
        c200, c400 = u.TMP / "piso_200", u.TMP / "piso_400"
        cortes = [("CORTE: 181 de" in (c / "log.txt").read_text()) for c in (c200, c400)]
        inf(f"(--sin-correr: compara las corridas que ya estan en {c200.parent.name}/piso_200 y piso_400)")
        inf.chequeo("las dos corridas llegaron al 181 y cortaron", all(cortes), f"{cortes}")
    else:
        c200, c400 = u.carpeta("piso_200", ["corredor"]), u.carpeta("piso_400", ["corredor"])
        codigos = u.en_tandas([
            (u.RL_NUEVO, BASE + ["--episodios", "200"], c200, c200 / "log.txt"),
            (u.RL_NUEVO, BASE + ["--episodios", "400", "--lr-horizonte", "200", "--lr-piso", "0.1"], c400,
             c400 / "log.txt")], maximo=2)
        inf.chequeo("las dos corridas llegan al 181 y cortan", codigos == [0, 0], f"codigos {codigos}")
    a, b = c200 / f"resultados_{TAG}.csv", c400 / f"resultados_{TAG}.csv"
    inf.chequeo("CSV de los episodios 1-181 (todas las columnas salvo segundos)", *u.comparar_csv_bytes(a, b))
    inf.chequeo("checkpoints 10-180 (tensores; meta igual salvo episodios y opciones)",
                *u.comparar_checkpoints(c200, TAG, c400, TAG, ignorar_json=("episodios", "opciones")))
    ea, eb = u.checkpoints(c200, TAG, ".estado.pt"), u.checkpoints(c400, TAG, ".estado.pt")
    # los sha256 de los checkpoints (archivos) difieren porque sus .json dicen --episodios y las opciones de la tasa
    malos = [ep for ep in sorted(set(ea) & set(eb)) if ep < 181 and
             not u.comparar_estados(ea[ep], eb[ep], ignorar=("episodios", "archivos"))[0]]
    inf.chequeo("estados 10-180 iguales (salvo --episodios y los sha256 de los .json)", not malos and len(ea) == 19,
                f"{len(ea)} estados, distintos: {malos}")
    x, y = torch.load(ea[181], weights_only=True), torch.load(eb[181], weights_only=True)
    inf.chequeo("estado del 181: tasa usada en 1-180 igual y en el 181 distinta en el ultimo bit",
                x["lr"][:180] == y["lr"][:180] and x["lr"][180] != y["lr"][180],
                f"{x['lr'][180]!r} | {y['lr'][180]!r}")
    ox, oy = x["opt"], y["opt"]
    pesos = all(torch.equal(x["politica"][k], y["politica"][k]) for k in x["politica"])
    momentos = all(torch.equal(ox["state"][i][c], oy["state"][i][c]) for i in ox["state"] for c in ox["state"][i])
    grupos = [{k: v for k, v in g.items() if k != "lr"} for g in ox["param_groups"]] == \
        [{k: v for k, v in g.items() if k != "lr"} for g in oy["param_groups"]]
    inf(f"   estado del 181 (despues de actualizar con esa tasa): pesos iguales {pesos}; momentos y pasos de Adam "
        f"iguales {momentos}; grupos de Adam iguales salvo el lr guardado {grupos} (lr {ox['param_groups'][0]['lr']!r}"
        f" | {oy['param_groups'][0]['lr']!r})")
    inf("   (descriptivo: la diferencia de ~1e-20 en el lr del 181 se pierde al redondear a float32; desde el 182 la "
        "tasa cambia de verdad: 9.5e-05 frente a 1e-04)")
    return inf.cerrar()


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
