"""
prueba_comandos.py - Los comandos de rl_ippo de la lista de trabajos pasan validar_args (revision de robustez del
05.11.2026, punto 6; informe: plan3/doc/informe_ent1.md, seccion 7).

Arma en este proceso la lista completa del generador (generar_trabajos3.generar_con_manifiesto con PARTES_PLAN, sin
escribir nada), toma cada comando que corre ../rl_ippo.py (directo o con ../con_escenarios.py) y lo pasa por
rl_ippo.validar_args, despues de con_escenarios.registrar(), como lo hara chequeos_previos. Cuenta, por etapa, los
aceptados y los rechazados con el motivo. Sin --esperar-rechazo, todo debe pasar; con --esperar-rechazo X, los
comandos de la parte X deben fallar (sirve para el commit de la robustez, antes de la Etapa 3).

Uso:  python plan3/pruebas/ent/prueba_comandos.py [--esperar-rechazo etapa3]
Salida: plan3/pruebas/ent/salidas/prueba_comandos.txt (no simula nada; segundos).
"""
import io
import sys
import shlex
import argparse
import contextlib
from collections import defaultdict

import util_ent as u


def argumentos(cmd):
    """argv de rl_ippo (sin python, sin el lanzador y sin ../rl_ippo.py) o None si el comando no corre rl_ippo."""
    partes = shlex.split(cmd, posix=True)
    for i, p in enumerate(partes):
        if p.replace("\\", "/").endswith("rl_ippo.py"):
            return partes[i + 1:]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--esperar-rechazo", default=None, help="parte del generador cuyos comandos deben fallar")
    a = ap.parse_args()
    inf = u.Informe("prueba_comandos", "Comandos de rl_ippo de la lista de trabajos frente a validar_args"
                    + (f" (se espera que falle {a.esperar_rechazo})" if a.esperar_rechazo else ""))
    sys.path.insert(0, str(u.RAIZ))
    sys.path.insert(0, str(u.PLAN3))
    import con_escenarios
    con_escenarios.registrar()
    import rl_ippo
    import generar_trabajos3 as g
    rechazar = set()
    if a.esperar_rechazo:
        rechazar = {t["id"] for t in g.generar_con_manifiesto([a.esperar_rechazo])[0]}
    trabajos, _ = g.generar_con_manifiesto(g.PARTES_PLAN)
    hiper = dict(rl_ippo.HIPER)
    cuenta = defaultdict(lambda: [0, 0, ""])          # etapa: [aceptados, rechazados, primer motivo]
    malos = []
    for t in trabajos:
        argv = argumentos(t["cmd"])
        if argv is None:
            continue
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                rl_ippo.validar_args(argv)
            ok, motivo = True, ""
        except SystemExit:
            ok, motivo = False, (err.getvalue().strip().splitlines() or ["?"])[-1]
        c = cuenta[t["etapa"]]
        c[0 if ok else 1] += 1
        if not ok and not c[2]:
            c[2] = f"{t['id']}: {motivo}"
        if ok == (t["id"] in rechazar):
            malos.append(f"{t['id']} ({'acepta' if ok else 'rechaza: ' + motivo})")
    for etapa, (si, no, motivo) in sorted(cuenta.items(), key=lambda x: str(x[0])):
        inf(f"   etapa {etapa}: {si} aceptados, {no} rechazados" + (f"; primero: {motivo[:150]}" if no else ""))
    total = sum(c[0] + c[1] for c in cuenta.values())
    inf.chequeo(f"{total} comandos de rl_ippo en {len(trabajos)} trabajos: "
                + ("todos pasan" if not rechazar else f"pasan todos menos los de {a.esperar_rechazo}, que fallan"),
                not malos and total > 0, f"{len(malos)} fuera de lo esperado: {malos[:5]}")
    inf.chequeo("validar_args no cambia HIPER ni C", rl_ippo.HIPER == hiper and rl_ippo.C == {})
    return inf.cerrar()


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
