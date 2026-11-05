"""
p3_preparar.py - Trabajo "preparar" del inicio de cada noche (plan3, tarea 0.11; DECISIONES B13): genera, antes de
las evaluaciones que dependen de el, los archivos de programa que los brazos regeneran o cargan al arrancar sumo.

Uso (cwd = plan3/; para escenarios de escenarios_plan3, a traves de ../con_escenarios.py):
  python p3_preparar.py <esc> [<esc> ...] [--piezas actuado,trivial]
Piezas (por defecto actuado y trivial; actuado_aj solo si se pide):
  actuado     <esc>_actuado.add.xml   comun.archivo_actuado (el actuado entregado)
  trivial     <esc>_trivial.add.xml   comun.archivo_trivial (el ciclo minimo)
  actuado_aj  <esc>_actuado_aj.add.xml desde barridos/<esc>/actuado_aj.json (actuado.reinstalar): si el instalado ya
              tiene el sha256 congelado no se toca; si no, el texto de hoy va a un temporal y reemplaza solo si su
              sha256 es el congelado (si no, error y el instalado queda como estaba)
Las dos primeras usan las funciones entregadas, que desde 0.11 escriben en un temporal con el pid y reemplazan con
reintentos: si un sumo de otra evaluacion tiene el archivo abierto, se espera; el contenido es el de siempre.
Punto de extension: PIEZAS es un diccionario {nombre: funcion(esc) -> ruta escrita}; los detectores E2 de la
observacion nueva (tarea 3.1) se agregan ahi con su propia pieza, sin tocar lo demas.
Imprime el sha256 de cada archivo; codigo 0 solo si todas las piezas pedidas quedaron escritas y se leen como XML.
Se corre con cwd = plan3/ (o una carpeta dentro de plan3/): desde otro lugar se niega.
"""
import os
import sys
import argparse
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
for _ruta in (AQUI, RAIZ):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import comun  # noqa: E402
import rl_corredor as rc  # noqa: E402
import barrer_fino as bfn  # noqa: E402


def escenario(esc):
    if esc not in rc.ESCENARIOS:
        raise SystemExit(f"{esc}: escenario sin registrar (los de escenarios_plan3 van con ../con_escenarios.py)")
    e = rc.ESCENARIOS[esc]
    if not os.path.exists(e["cfg"]):
        raise SystemExit(f"No existe {e['cfg']} en {os.getcwd()}")
    return e["cfg"], list(e["semaforos"])


def pieza_actuado(esc):
    cfg, tls = escenario(esc)
    comun.archivo_actuado(cfg, esc, tls, rc.VERDE_MIN, rc.VERDE_MIN_GIRO, rc.VERDE_MAX)
    return f"{esc}_actuado.add.xml"


def pieza_trivial(esc):
    cfg, tls = escenario(esc)
    comun.archivo_trivial(cfg, esc, tls, rc.VERDE_MIN, rc.VERDE_MIN_GIRO)
    return f"{esc}_trivial.add.xml"


def pieza_actuado_aj(esc):
    escenario(esc)
    import actuado
    return actuado.reinstalar(esc)


# Punto de extension: los E2 de la observacion nueva (3.1) se registran aqui como otra pieza.
PIEZAS = {"actuado": pieza_actuado, "trivial": pieza_trivial, "actuado_aj": pieza_actuado_aj}
POR_DEFECTO = ("actuado", "trivial")          # actuado_aj solo si se pide (--piezas actuado_aj)


def main():
    ap = argparse.ArgumentParser(description="Trabajo preparar de cada noche (plan3, 0.11)", allow_abbrev=False)
    ap.add_argument("escenarios", nargs="+")
    ap.add_argument("--piezas", default=",".join(POR_DEFECTO), help=f"de {', '.join(PIEZAS)} (por defecto "
                                                                   f"{', '.join(POR_DEFECTO)})")
    args = ap.parse_args()
    bfn.exigir_cwd()
    piezas = [p for p in args.piezas.split(",") if p]
    desconocidas = [p for p in piezas if p not in PIEZAS]
    if desconocidas:
        ap.error(f"piezas desconocidas: {desconocidas}")
    escritas = []
    for esc in args.escenarios:
        for pieza in piezas:
            ruta = PIEZAS[pieza](esc)
            ET.parse(ruta)                     # se lee completo
            escritas.append(ruta)
            print(f"{esc} {pieza}: {ruta} sha256 {bfn.sha256_archivo(ruta)}", flush=True)
    print(f"preparar: {len(escritas)} archivos")


if __name__ == "__main__":
    main()
