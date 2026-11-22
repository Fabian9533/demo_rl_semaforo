"""
programa_ovalo.py - Escritor de programas del semaforo del Ovalo Vasco con la interfaz de programa.py (PLAN,
TRANSICION, ROJO_TOTAL, NO_VERDES, fases, minimos, tiempo_fijo, escribir). Lo usan lima/estudio.py y
lima/borde_actuado.py con LIMA_PROGRAMA=programa_ovalo para ajustar y escribir los controles en la red del ovalo.

Sale de pruebas/modelo/cambios.diff de la revision del ovalo (17.11.2026) con dos cambios del 18.11.2026: las reglas
de las luces vienen de ovalo/plan_ovalo.py (la copia recortada del constructor, con el orden libre) y escribir_libre()
escribe el programa del orden libre (lima_libre.json), que rl_ippo.py --orden-libre instala si esta junto al .sumocfg.

La red es la de la carpeta del caso: lima.net.xml de LIMA_CARPETA, con la misma regla que estudio.py (relativa a
lima/), sin depender del directorio actual (borde_actuado.py lee los minimos antes de entrar en la carpeta).
Los controles actuados miran solo las 15 entradas, como en el estudio: cada carril de adentro lleva un detector propio
que no cuenta a nadie. SUMO pide un E2 (laneAreaDetector) en delay_based y un E1 (inductionLoop) en actuated.

Uso suelto (desde lima/; escribe el plan actual y el programa libre de la carpeta):
  LIMA_CARPETA=alta python programa_ovalo.py
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "ovalo"))
import plan_ovalo as po  # noqa: E402
from programa import (PLAN, TRANSICION, ROJO_TOTAL, NO_VERDES, VERDE_MIN, VERDE_MAX, TLS,  # noqa: E402,F401
                      verde_minimo, tiempo_fijo)

CARPETA = os.path.normpath(os.path.join(AQUI, os.environ.get("LIMA_CARPETA", "")))   # la de estudio.py
RED = os.path.join(CARPETA, "lima.net.xml")
INTERNO = "cede"               # la segunda esquina no tiene semaforo propio (Fabian, 17.11.2026)
_PLANES = {}


def plan_de(plan=None):
    """El Plan del constructor sobre la red de la carpeta (uno por lista de estados)."""
    clave = repr(plan)
    if clave not in _PLANES:
        with open(RED, encoding="utf-8") as f:
            if 'id="NO_SO"' not in f.read():
                raise SystemExit(f"LIMA_PROGRAMA=programa_ovalo: {RED} no es la red del ovalo (falta la arista NO_SO); "
                                 "LIMA_CARPETA debe ser la carpeta del ovalo")
        _PLANES[clave] = po.Plan(RED, INTERNO, plan)
    return _PLANES[clave]


def fases(verdes_seg, plan=None, transicion=TRANSICION):
    """[(duracion, estado, nombre)] y los avisos de enlaces que chocan con prioridad, como programa.fases."""
    assert transicion == TRANSICION, "el ovalo usa la transicion de programa.py"
    p = plan_de(plan)
    n = len(p.avisos)
    lista = p.fases(list(verdes_seg))
    return lista, p.avisos[n:]


def minimos(plan=None):
    """Verde minimo de cada estado (programa.verde_minimo sobre las letras del ovalo)."""
    lista, _ = fases([v for _, v, _ in (plan or PLAN)], plan)
    return [verde_minimo(estado) for _, estado, nombre in lista if nombre not in NO_VERDES]


def detectores_nulos(p, clase):
    """Un detector que no cuenta a nadie (vTypes de un tipo que no existe) en cada carril de adentro."""
    if clase == "delay_based":
        return po.detectores_nulos(p)
    res = []
    for carril in po.carriles_internos(p):
        largo = p.red.net.getLane(carril).getLength()
        res.append(f'    <inductionLoop id="nulo_{carril}" lane="{carril}" pos="{largo / 2:.2f}" vTypes="ninguno" '
                   f'period="100000" file="nul" friendlyPos="true"/>')
    return res


def escribir(ruta, verdes_seg, plan=None, tipo="fijo", programa=None, comentario="", transicion=TRANSICION,
             parametros=None):
    """Escribe el .add.xml de un control, como programa.escribir. tipo: "fijo" (duraciones verdes_seg), "actuado"
    (actuated de SUMO; verdes_seg da el verde maximo de cada estado y el minimo es el del agente) o "retraso"
    (delay_based, con los mismos limites). parametros: {clave: valor} del control de SUMO."""
    assert transicion == TRANSICION, "el ovalo usa la transicion de programa.py"
    p = plan_de(plan)
    n = len(p.avisos)
    if tipo == "fijo":
        lineas = po.lineas_programa(p, "static", list(verdes_seg), {}, programa or "fijo", comentario)
        lista = p.fases(list(verdes_seg))
    else:
        clase = "delay_based" if tipo == "retraso" else "actuated"
        verdes = [(m, max(m, v)) for m, v in zip(minimos(plan), verdes_seg)]
        lineas = detectores_nulos(p, clase) + po.lineas_programa(p, clase, verdes, dict(parametros or {}),
                                                                 programa or "actuado", comentario)
        lista = p.fases([mx for _, mx in verdes])
    po.escribir_add(ruta, lineas)
    return lista, sorted(set(p.avisos[n:]))


def escribir_libre(ruta):
    """Escribe el programa del orden libre (lima_libre.json) para rl_ippo.py --orden-libre: todas las fases que puede
    mostrar el semaforo cuando el modelo elige el estado que sigue, y en que caso va cada una (plan_ovalo.fases_libres).
    Las claves "verde" y "ambar" son [estado, estado anterior ("-" si antes fue el todo rojo), indice de la fase] y
    "rojo", [estado que termino, indice]."""
    p = plan_de()
    n = len(p.avisos)
    fases_l, verde, ambar, rojo = p.fases_libres()
    if p.avisos[n:]:
        raise SystemExit("orden libre: enlaces que chocan con prioridad: " + "; ".join(sorted(set(p.avisos[n:]))))
    datos = {"comentario": "Programa del orden libre del Ovalo Vasco (lima/programa_ovalo.py, escribir_libre): las "
                           "fases que puede mostrar semaforo_S1 cuando el modelo elige el estado que sigue, con las "
                           "reglas del plan (ovalo/plan_ovalo.py). rl_ippo.py --orden-libre lo instala si esta junto "
                           "al .sumocfg.",
             "tls": TLS, "estados": [nombre for nombre, _, _ in PLAN],
             "fases": [[nombre, letras] for nombre, letras in fases_l],
             "verde": [list(x) for x in verde], "ambar": [list(x) for x in ambar], "rojo": [list(x) for x in rojo]}
    tmp = f"{ruta}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(datos, f, indent=1, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, ruta)
    return datos


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    verdes = [v for _, v, _ in PLAN]
    lista, avisos = escribir(os.path.join(CARPETA, "lima.add.xml"), verdes,
                             comentario="Plan actual del nudo, medido en el sitio el 13.11.2026, en el Ovalo Vasco "
                                        "(programa_ovalo.py)")
    print(f"Escrito {os.path.join(CARPETA, 'lima.add.xml')}: ciclo {sum(d for d, _, _ in lista)} s")
    for dur, estado, nombre in lista:
        print(f"  {dur:3d} s  {estado}  {nombre}")
    datos = escribir_libre(os.path.join(CARPETA, "lima_libre.json"))
    print(f"Escrito {os.path.join(CARPETA, 'lima_libre.json')}: {len(datos['fases'])} fases")
    for a in avisos:
        print("AVISO:", a)
    return 1 if avisos else 0


if __name__ == "__main__":
    sys.exit(main())
