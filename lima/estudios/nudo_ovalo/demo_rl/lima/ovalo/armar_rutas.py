"""
armar_rutas.py - La demanda del estudio sobre la red del ovalo (copia de nudo_ovalo/rutas/armar_rutas.py de la revision
del 17.11.2026; aqui solo queda convertir(), que usa preparar_carpetas.py).

Que cambia y que no:
- Todo queda igual: los mismos <flow> (id, tipo, desde, hacia, inicio, fin, llegadas exp(tasa), departLane="best") y
  la misma mezcla de vehiculos (vTypeDistribution). En el estudio cada flujo tiene "from" y "to" y SUMO busca el camino
  al insertar cada vehiculo; aqui se conserva eso (rl_ippo lee el "from" de cada flujo) y se agrega solo "via": las
  aristas del camino de su movimiento dentro del ovalo (armar_ovalo.CAMINOS), para que el camino quede escrito.
Se comprueba que cada linea cambia solo en el "via" agregado.

18.11.2026 (correccion de carriles, nudo_ovalo_estudio2): "la demanda del estudio" es ahora la que escribe
lima/demanda.py con los carriles corregidos y el giro de Balboa hacia Larco (13 movimientos; su camino es B_ML). Lo
unico que cambia en este archivo es el comentario que se escribe en cada lima.rou.xml.
"""
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import armar_ovalo as ao  # noqa: E402

ENTRADA = {"RN_S1": "RN", "RS_S1": "RS", "B_S1": "B", "J_S1": "J"}
SALIDA = {"S1_L": "L", "S1_J": "J", "S1_RN": "RN", "S1_RS": "RS"}


def convertir(texto):
    lineas, n = [], 0
    for l in texto.split("\n"):
        m = re.search(r'<flow id="[^"]+" type="[^"]+" from="([^"]+)" to="([^"]+)"', l)
        if m:
            mov = (ENTRADA[m.group(1)], SALIDA[m.group(2)])
            via = " ".join(ao.CAMINOS[mov][1:-1])
            nueva = l.replace(f'to="{m.group(2)}"', f'to="{m.group(2)}" via="{via}"', 1)
            assert nueva.replace(f' via="{via}"', "") == l
            lineas.append(nueva)
            n += 1
        elif l.startswith("<routes>"):
            lineas.append(l)
            lineas.append("    <!-- Red del Ovalo Vasco (lima/ovalo/armar_rutas.py): la demanda de lima/demanda.py sin cambios "
                          "(copia en ovalo/entrada/rutas_estudio/), con el camino de cada movimiento dentro del ovalo en el "
                          "atributo via -->")
        else:
            lineas.append(l)
    return "\n".join(lineas), n
