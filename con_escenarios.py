"""
con_escenarios.py - Corre un programa con los escenarios del plan 3 (escenarios_plan3.ESTOCASTICOS) sumados a
escenarios_plan2.DERIVADOS solo dentro de este proceso (plan3/doc/DECISIONES.md, B2).

Uso (desde plan3/):  python ../con_escenarios.py <programa> [argumentos del programa]
  python ../con_escenarios.py ../rl_ippo.py train --escenario poi_corredor --v2 --etiqueta p3v2poi ...
  python ../con_escenarios.py ../evaluar.py --escenario poi_red --brazo fijo --semillas ... --salida ...
  python ../con_escenarios.py ../barrer_fijo.py poi_malla3 --semillas ... --tmp tmp_... --procesos 1
  python ../con_escenarios.py evaluar3.py ...
<programa> es una ruta relativa al cwd (o absoluta). rl_corredor, rl_ippo, evaluar y barrer_fijo (y rl_dqn y
rl_mappo, que importan rl_ippo) copian DERIVADOS al importarse: por eso el registro va antes de que se importe
cualquiera de ellos, y el lanzador se detiene si alguno ya estaba importado o si un nombre nuevo choca con uno
que ya existe. Despues corre el programa con runpy como __main__, con sys.argv = [programa, argumentos...] y
la carpeta del programa al frente de sys.path, como "python programa".

No edita ningun archivo: escenarios_plan2.py queda igual en disco y plan2/generar_trabajos.py, que corre en
otro proceso, no ve los escenarios nuevos. Se niega a correr un programa de plan2/ o de TESIS/, o con el cwd
dentro de ellas: nada del plan 3 escribe ahi, y la cola de plan2 no debe ver estos escenarios.
Otro programa puede registrar sin el lanzador (pruebas): import con_escenarios; con_escenarios.registrar(),
antes de importar los modulos de arriba. Un programa que lance procesos hijos de Python con multiprocessing no
pasa el registro a los hijos (ninguno de los del plan 3 lo hace).
"""
import os
import sys
import runpy

RAIZ = os.path.dirname(os.path.abspath(__file__))
# Modulos que copian escenarios_plan2.DERIVADOS a sus propias tablas al importarse
TOMAN_DERIVADOS = ("rl_corredor", "rl_ippo", "evaluar", "barrer_fijo", "rl_dqn", "rl_mappo")
# Escenarios con nombre escrito en el codigo, fuera de escenarios_plan2
NOMBRES_FIJOS = ("cruce", "cruce2", "corredor", "corredor_alta", "red")
PROHIBIDAS = ("plan2", "tesis")


def registrar():
    """Suma ESTOCASTICOS (escenarios_plan3) a DERIVADOS (escenarios_plan2) en este proceso y devuelve los
    nombres registrados."""
    tarde = [m for m in TOMAN_DERIVADOS if m in sys.modules]
    if tarde:
        raise SystemExit(f"con_escenarios: ya se importo {', '.join(tarde)}; el registro llegaria tarde")
    if RAIZ not in sys.path:
        sys.path.insert(0, RAIZ)
    import escenarios_plan2 as ep
    import escenarios_plan3 as e3
    for modulo in (ep, e3):
        if os.path.dirname(os.path.abspath(modulo.__file__)) != RAIZ:
            raise SystemExit(f"con_escenarios: {modulo.__name__} viene de {modulo.__file__}, no de {RAIZ}")
    usados = set(ep.DERIVADOS) | set(ep.ESCENARIOS_RC) | set(ep.VECINOS) | set(ep.LADOS) | set(NOMBRES_FIJOS)
    choque = sorted(set(e3.ESTOCASTICOS) & usados)
    if choque:
        raise SystemExit(f"con_escenarios: nombres ya usados: {', '.join(choque)}")
    ep.DERIVADOS.update(e3.ESTOCASTICOS)
    # perfil de 10 min: las metricas del corredor reconocen los flows <flow>_b<k> (comun no importa escenarios)
    import comun
    comun.QUITAR_BLOQUE = True
    return sorted(e3.ESTOCASTICOS)


def prohibida(ruta):
    """True si la ruta pasa por una carpeta plan2 o TESIS de este repositorio, de sus worktrees hermanos o de
    una copia dentro de ellos. Lo que esta por encima de la carpeta que los contiene no cuenta (puede llamarse
    Tesis)."""
    try:
        relativa = os.path.relpath(os.path.abspath(ruta), os.path.dirname(RAIZ))
    except ValueError:                    # otra unidad de disco
        return False
    if relativa.startswith(".."):
        return False
    return any(parte.lower() in PROHIBIDAS for parte in relativa.split(os.sep))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    programa, argumentos = sys.argv[1], sys.argv[2:]
    if prohibida(programa) or prohibida(os.getcwd()):
        raise SystemExit("con_escenarios: no se corre nada de plan2/ ni de TESIS/, "
                         "ni con el cwd dentro de ellas")
    ruta = os.path.abspath(programa)
    if not os.path.isfile(ruta):
        raise SystemExit(f"con_escenarios: no existe el programa {programa}")
    registrar()
    sys.argv = [programa] + argumentos
    sys.path.insert(0, os.path.dirname(ruta))
    runpy.run_path(ruta, run_name="__main__")


if __name__ == "__main__":
    main()
