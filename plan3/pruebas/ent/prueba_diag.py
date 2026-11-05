"""
prueba_diag.py - Prueba 5 de las tareas 1.1-1.2 del plan 3 (DECISIONES B12; informe: plan3/doc/informe_ent1.md).

V2 en el corredor (P1), base 42, con el codigo nuevo y las opciones de produccion (--v2 --criterio-val total
--guardar-estado --registro-extendido), --episodios 200 cortado con --hasta-ep 10 (la tasa de la corrida de 200 del
diagnostico) y validacion cada 5 en 424301-424302 (el diagnostico valido cada 10 en 999 y 1999). En el ep 10 los
tensores deben ser iguales (torch.equal sobre el state_dict) a los de insumos/v2diag_checkpoints/
corredor_ippo_vecinos_v2_s42_ep010.pt, que copia p3_insumos.py del respaldo; el sha256 del archivo no sirve porque
torch.save guarda el nombre. Tambien se comparan las filas 1-10 con el CSV del diagnostico del tag (salvo segundos,
etiqueta y las columnas de validacion, que usan otras semillas).

Uso:  python plan3/pruebas/ent/prueba_diag.py   (corre antes p3_insumos.py si faltan los checkpoints)
Salida: plan3/pruebas/ent/salidas/prueba_diag.txt; corrida en plan3/tmp_ent/diag_v2_s42.
"""
import sys
import subprocess

import util_ent as u

DIAG = u.PLAN3 / "insumos" / "v2diag_checkpoints" / "corredor_ippo_vecinos_v2_s42_ep010.pt"
TAG = "corredor_ippo_vecinos_p3prbdiag_s42"
VALIDACION = ["eval_timeloss", "eval_espera", "val_999", "val_1999", "val", "val_total_999", "val_total_1999",
              "val_total"]


def main():
    inf = u.Informe("prueba_diag", "Prueba 5: V2 del corredor, base 42, ep 10, frente a la V2 del diagnostico (B12)")
    if not DIAG.exists():
        r = subprocess.run([sys.executable, "p3_insumos.py"], cwd=u.PLAN3, capture_output=True, text=True)
        inf(f"p3_insumos.py (codigo {r.returncode}): {r.stdout.strip()[-300:]} {r.stderr.strip()[-300:]}")
    inf.chequeo("existe el checkpoint del diagnostico", DIAG.exists(), str(DIAG.relative_to(u.RAIZ)))
    c = u.carpeta("diag_v2_s42", ["corredor"])
    argumentos = ["train", "--escenario", "corredor", "--seed", "42", "--episodios", "200", "--hasta-ep", "10",
                  "--eval-cada", "5", "--val-seeds", u.VAL_HUMO, "--v2", "--criterio-val", "total",
                  "--guardar-estado", "--registro-extendido", "--etiqueta", "p3prbdiag"]
    inf(f"rl_ippo.py {' '.join(argumentos)}")
    cod = u.correr(u.RL_NUEVO, argumentos, c, c / "log.txt")
    inf.chequeo("corrida", cod == 0, f"codigo {cod}")
    nuevo = c / "checkpoints" / f"{TAG}_ep010.pt"
    inf.chequeo("ep 10: tensores iguales a los del diagnostico", *u.comparar_pt(nuevo, DIAG))
    inf(f"   sha256 de los archivos (distinto por el nombre que guarda torch.save): {u.sha256(nuevo)[:16]} | "
        f"{u.sha256(DIAG)[:16]}")
    csv_diag = c / "diag_resultados_corredor_ippo_vecinos_v2_s42.csv"
    csv_diag.write_bytes(subprocess.run(["git", "show", f"{u.TAG}:plan2/resultados_corredor_ippo_vecinos_v2_s42.csv"],
                                        cwd=u.RAIZ, capture_output=True, check=True).stdout)
    ok, txt = u.comparar_columnas(c / f"resultados_{TAG}.csv", csv_diag,
                                  ignorar=["segundos", "etiqueta"] + VALIDACION, filas=10)
    inf.chequeo("filas 1-10 = las del diagnostico (salvo segundos, etiqueta y validacion)", ok, txt)
    inf("La validacion del ep 5 y las semillas de humo (en vez de 999 y 1999) no cambiaron el entrenamiento"
        if ok else "OJO: algo distinto en el entrenamiento (ver arriba)")
    return inf.cerrar()


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
