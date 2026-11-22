"""
armar_ovalo.py - Red del estudio del nudo en el Ovalo Vasco (18.11.2026; nudo_ovalo_estudio2/LEEME.md).

CORRECCION DE CARRILES (18.11.2026, tarde; carpeta nudo_ovalo_estudio2). Fabian Alvarado reviso la red contra el lugar
y encontro mal los carriles de las dos entradas de Reducto y la falta de un giro de Balboa. Frente al constructor de
nudo_ovalo_estudio/ (sha256 90a8f59819c4392c), que queda como registro de la corrida detenida, cambia esto y nada mas:
  a. Los carriles de las entradas se escriben en UN solo sitio, DISPOSICION (mas abajo): carril por carril, de derecha
     a izquierda, con las salidas a las que va cada uno. De esa tabla salen solas (derivar_tablas) las que antes
     estaban escritas a mano en cinco lugares: AFUERA, CARRILES_INTERNOS, CONEXIONES, CARRILES_ENTRADA y los centros
     de armar_plano. comprobar_tablas detiene el armado si la tabla pide algo que la red no sabe armar o si algun
     carril no llega exactamente a sus salidas.
  b. Reducto desde el norte: 5 carriles (antes 4), los dos de la izquierda solo giran hacia el puente; su ramal de giro
     lleva 2 carriles antes y despues de cruzar (RN_NE y NE_MJ, antes 1).
  c. Reducto desde el sur: 4 carriles (antes 5), los dos de la izquierda solo giran hacia Larco y el de la derecha va
     de frente y tambien gira hacia el puente (antes solo giraba); su calzada principal lleva 2 carriles (RS_SE,
     antes 3).
  d. Balboa hacia Larco, el movimiento 13: un tramo nuevo de 1 carril, B_ML, de la linea de parada de Balboa a la
     union de la salida hacia Larco, por el oeste y sin cruzar los lados del ovalo (OpenStreetMap, via 366715629).
     Sale del carril izquierdo de Balboa, con su verde, y en la union es un ceda el paso (plan_ovalo.py, CEDEN y
     CEDA_EL_PASO). Para que la linea de parada de Balboa quede donde estaba, el extremo de su entrada se escribe a
     mano (EXTREMO_BALBOA).
No cambian los 10 nodos del semaforo (las cuatro esquinas, las dos uniones y las cuatro lineas de parada), la isla, el
ancho de carril, las velocidades, los largos de afuera ni las opciones de netconvert. Lo que si cambia sin pedirlo es el
lugar libre de los lados (las esquinas NE y SE dependen del ancho de lo que las cruza) y, en 0.26 y 0.10 m, donde
netconvert corta las dos entradas de Reducto antes de su nodo (pruebas/correccion_carriles/comparar_redes.txt). Con la
disposicion anterior (DISPOSICION_ANTERIOR) este constructor da la red anterior byte a byte
(pruebas/correccion_carriles/regresion.py).

El constructor de nudo_ovalo_estudio/ era a su vez
la copia de nudo_ovalo/medido/armar_ovalo.py (revision del 17.11.2026, sha256 c45236f8369fb91c) con tres cambios:
  1. Rutas: lee sus entradas de lima/ovalo/entrada/ (copias de la revision) y escribe en lima/ovalo/red/. La red por
     defecto se llama ovalo_estudio (geometria "medida": las medidas de Fabian en Google Maps).
  2. Esquinas: ningun tramo interno queda por debajo de VEL_GIRO_MIN (5.56 m/s, 20 km/h). Con las esquinas cortadas en
     el borde de la calzada que cruzan, netconvert deja cinco giros con radios de 1.5 a 4.3 m (de 2.9 a 4.9 m/s), un
     defecto de construccion: una esquina urbana tiene unos 5.6 m de radio, que con los 5.5 m/s2 de aceleracion lateral
     de netconvert dan 5.56 m/s. Esos giros llevan speed="5.56" en su conexion (.con.xml) y la red se vuelve a armar:
     no cambia ninguna forma ni ningun largo, solo la velocidad de esos tramos internos (red/<nombre>.giros.txt los
     muestra antes y despues).
  3. La matriz de cada esquina se completa con las cesiones del plan y tambien con las del orden libre
     (plan_ovalo.Plan.cesiones_necesarias), para que todos los controles y los dos modelos usen la misma red.
El resto es el texto de la revision:

Red del Ovalo Vasco: el mismo nudo del caso Lima (Av. Reducto, Av. 28 de Julio y Av. Vasco Nunez de
Balboa, Miraflores), ahora con su centro. Son cuatro calzadas de un sentido que rodean una isla y se cruzan en cuatro
esquinas (NO, NE, SO, SE); un solo semaforo, semaforo_S1, maneja las cuatro esquinas y las lineas de parada de afuera.

Uso (desde medido/):
  python -B armar_ovalo.py                         # red/ovalo_medido.net.xml: esquinas a las distancias medidas
  python -B armar_ovalo.py --ancho 3.0 --nombre ovalo_medido_a30   # supuesto: carriles de 3.0 m adentro
  python -B armar_ovalo.py --geometria coherente --escala 1.5 --nombre ovalo   # la red de nudo_ovalo (isla x1.5)

Lo unico nuevo frente a nudo_ovalo/armar_ovalo.py es la geometria "medida" (leer_osm) y las opciones --ancho y
--ramales: las esquinas salen de medidas/medidas_google.json (cruce de los ejes de las calzadas en las capturas de
Google Maps de Fabian, 17.11.2026), giradas a la cuadricula UTM (convergencia de meridianos, unos 0.43 grados) y
centradas en el centroide de las cuatro esquinas de OSM. Afuera todo queda igual.

Lee:
  entrada/red_estudio/lima.{nod,edg,con}.xml y lima.net.xml  la red del estudio (copias de lima/red/ y lima/)
  salidas/geometria_osm.json                                 los nodos de OpenStreetMap (geometria_osm.py)
Escribe en red/: <nombre>.{nod,edg,con}.xml (red plana), <nombre>.net.xml, <nombre>.netconvert.txt (orden y
avisos), e2_<nombre>_75.add.xml (detectores de 75 m antes de cada linea de parada, como lima/e2_lima_75.add.xml)
y <nombre>.resumen.txt (largos, carriles y comparacion con la red del estudio).

Decisiones (el porque esta en LEEME.md):
- Afuera todo es de la red del estudio: mismas 8 aristas (ids, carriles, velocidad y trazado). Cada entrada termina
  ahora en su linea de parada real (el semaforo de OSM) y su carril mide lo mismo que en el estudio: la recta
  artificial del comienzo se alarga lo que haga falta. Las salidas empiezan donde dejan el ovalo y tambien miden lo
  mismo (se alarga el final).
- Adentro: con las esquinas de OSM tal cual (--geometria osm) las esquinas se pisan: OSM deja 2.2 a 3.8 m de media
  calzada donde sus propios carriles piden 3.2 a 4.8 m. La red base usa la geometria "coherente": la isla de OSM,
  agrandada en ESCALA_BASE (provisional, hasta que Fabian la mida), rodeada por calzadas de 3.2 m por carril.
- Los dos ramales de giro a la izquierda de Reducto cruzan una calzada del ovalo pegados a una esquina (OSM
  4337293915/16 y 4337295647/48): esos cruces van dentro de la esquina (NE con el ramal de Reducto norte, SO con el
  de Reducto sur).
- Cada arista de adentro va de borde a borde de sus esquinas (--junctions.endpoint-shape): lo que queda entre dos
  esquinas es el lugar real para esperar.
- Carriles de adentro: los de OSM, salvo donde un movimiento del estudio pasaba con mas carriles (CARRILES_INTERNOS).
- Despues de netconvert, ajustar_matriz completa la matriz de cada esquina con las cesiones que pide el programa.
"""
import argparse
import json
import math
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
import sumolib  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
ESTUDIO = os.path.join(AQUI, "entrada", "red_estudio")
RED = os.path.join(AQUI, "red")
GEO = os.path.join(AQUI, "entrada", "geometria_osm.json")
VEL = 13.89                    # 50 km/h, como el estudio
VEL_GIRO_MIN = 5.56            # m/s (20 km/h): velocidad minima de un tramo interno (ver el cambio 2 de arriba)
ANCHO = 3.2                    # m por carril de ADENTRO (el de SUMO por defecto; --ancho lo cambia)
ANCHO_AFUERA = 3.2             # m por carril de las entradas del estudio (no cambia)
MEDIDAS = os.path.join(AQUI, "entrada", "medidas", "medidas_google.json")
LATLON_OVALO = (-12.12921, -77.02377)    # centro aproximado del ovalo (OSM), para la convergencia de UTM
RAMALES = "distancia"          # donde cruzan los ramales de giro en la geometria medida (ver leer_osm)
E2_LARGO = 75.0                # detectores de la observacion del modelo (--obs-cercana 75)
OFFSET_ESTUDIO = (45.81, 386.87)   # netOffset de lima/lima.net.xml: la red sale en sus mismas coordenadas
# Las opciones de lima/armar_red.py sin --no-internal-links, mas: las uniones se arman con los bordes que trae cada
# arista (--junctions.endpoint-shape; ver armar_plano) y las coordenadas quedan como en lima/lima.net.xml.
NETCONVERT = ["netconvert", "--no-turnarounds", "--junctions.corner-detail", "5", "--tls.default-type", "static",
              "--junctions.endpoint-shape", "true",
              "--offset.disable-normalization", "true", "--offset.x", str(OFFSET_ESTUDIO[0]),
              "--offset.y", str(OFFSET_ESTUDIO[1])]
TLS = "semaforo_S1"
TLS_E1 = "semaforo_E1"
# Isla del ovalo: la de OSM (area peatonal 653650079, unos 9.3 x 9.6 m) agrandada en este factor. PROVISIONAL hasta
# que Fabian la mida: con la isla de OSM (1.0) las esquinas se pisan en el lado oeste y en el este; 1.5 es el factor
# redondo mas chico con las cuatro esquinas separadas y lugar para un auto en el lado oeste (salidas/espacio_lados.txt).
ESCALA_BASE = 1.5
VISIBILIDAD = 25.0             # m: distancia desde la que se ve a los demas en las conexiones de adentro

# ---------------- aristas ----------------
# =====================================================================================================================
# DISPOSICION DE CARRILES. Es el UNICO sitio donde se escriben los carriles de las entradas: todo lo demas se deduce.
# =====================================================================================================================
# Cada entrada junto a su linea de parada, carril por carril, de DERECHA a IZQUIERDA del conductor (el primero es el
# carril 0 de SUMO), con las salidas a las que va cada carril:
#       L  = hacia Larco (28 de Julio, al oeste)        J  = hacia el puente (28 de Julio, al este)
#       RN = Reducto hacia el norte                     RS = Reducto hacia el sur
# Confirmada en el sitio por Fabian Alvarado el 18.11.2026 (lima/REGISTRO.md, 17:40, y su confirmacion de la entrada
# del sur). Para cambiar un carril se cambia ESTA tabla y se vuelve a armar: derivar_tablas saca de ella AFUERA,
# CARRILES_INTERNOS, CONEXIONES, CARRILES_ENTRADA, CAMINOS y CENTROS, y comprobar_tablas detiene el armado si algo no
# cuadra. La regla de la demanda (lima/demanda.py, GRUPOS) cuenta estos mismos carriles: comprobar_red.py compara.
DISPOSICION = {
    # Reducto desde el norte (RN_S1), 5 carriles: la avenida trae 3 y junto al paso peatonal se abre con 2 mas
    "RN": [("RS", "L"),         # 0: de frente (hacia Reducto sur) y derecha (hacia Larco)
           ("RS",),             # 1: de frente
           ("RS",),             # 2: de frente
           ("J",),              # 3: SOLO izquierda, hacia el puente
           ("J",)],             # 4: SOLO izquierda, hacia el puente
    # Reducto desde el sur (RS_S1), 4 carriles: la calzada trae 2 y se abre a 4 poco antes del semaforo
    "RS": [("RN", "J"),         # 0: de frente (hacia Reducto norte) y derecha (hacia el puente)
           ("RN",),             # 1: de frente
           ("L",),              # 2: SOLO izquierda, hacia Larco
           ("L",)],             # 3: SOLO izquierda, hacia Larco
    # Balboa (B_S1), 3 carriles
    "B": [("J", "RS"),          # 0: de frente (hacia el puente) y derecha (hacia Reducto sur)
          ("J",),               # 1: de frente (hacia el puente)
          ("J", "RN", "L")],    # 2: de frente (hacia el puente), hacia Reducto norte y, NUEVO, izquierda hacia Larco
    # 28 de Julio desde el puente (J_S1), 3 carriles (sin cambios)
    "J": [("L", "RN"),          # 0: de frente (hacia Larco) y derecha (hacia Reducto norte)
          ("L",),               # 1: de frente (hacia Larco)
          ("RS",)],             # 2: SOLO izquierda, hacia Reducto sur
}
# Simplificaciones declaradas (18.11.2026):
#  - Reducto desde el sur: segun Fabian, los DOS carriles de la derecha pueden ir de frente y girar hacia el puente. El
#    giro a la derecha desde el carril 1 cruzaria la trayectoria del carril 0 que sigue de frente: el giro se modela
#    solo desde el carril 0.
#  - Balboa: segun Fabian, desde el carril del medio tambien se gira. No se modela, por el mismo motivo.
#  - Los carriles de giro de Reducto son carriles completos de la entrada (1 km), aunque en el sitio el ensanche es
#    corto (simplificacion ya declarada en el estudio; ahora vale para las dos entradas).
#  - La vuelta en U desde Reducto norte no se modela.
#
# La disposicion de la red anterior (13.11.2026; nudo_ovalo_estudio/, corrida detenida el 18.11.2026 a las 17:39). Solo
# la usa la prueba de regresion: con ella este constructor da la red anterior byte a byte.
DISPOSICION_ANTERIOR = {
    "RN": [("RS", "L"), ("RS",), ("RS",), ("J",)],                 # 4 carriles, un solo carril de giro
    "RS": [("J",), ("RN",), ("RN",), ("L",), ("L",)],              # 5 carriles, el de la derecha solo giraba
    "B": [("J", "RS"), ("J",), ("J", "RN")],                       # sin el giro hacia Larco
    "J": [("L", "RN"), ("L",), ("RS",)],
}

# ---- lo que NO depende de la disposicion ----
ARISTA_ENTRADA = {"RN": "RN_S1", "RS": "RS_S1", "B": "B_S1", "J": "J_S1"}
ARISTA_SALIDA = {"L": "S1_L", "J": "S1_J", "RN": "S1_RN", "RS": "S1_RS"}
# Afuera: las 8 aristas del estudio. id -> (nodo de inicio, nodo final)
NODOS_AFUERA = {
    "RN_S1": ("RNe", "P_RN"), "RS_S1": ("RSe", "P_RS"), "B_S1": ("Be", "P_B"), "J_S1": ("Je", "P_J"),
    "S1_L": ("ML", "Ls"), "S1_RN": ("NE", "RNs"), "S1_RS": ("SO", "RSs"), "S1_J": ("MJ", "Js"),
}
# Carriles de las salidas y de las calzadas del ovalo (los cuatro lados y los dos tramos hacia las uniones)
CARRILES_SALIDAS = {"S1_L": 2, "S1_RN": 2, "S1_RS": 3, "S1_J": 3}
CARRILES_OVALO = {"NE_NO": 3, "NO_SO": 3, "SO_SE": 3, "SE_NE": 2, "NO_ML": 2, "SE_MJ": 3}
# Linea de parada de cada entrada: nodo -> (entrada, semaforo de OSM que fija su lugar)
PARADAS = {"P_RN": ("RN_S1", "PRN"), "P_RS": ("RS_S1", "PRS"), "P_B": ("B_S1", "PB"), "P_J": ("J_S1", "PJ")}
# Las dos entradas de Reducto se abren en dos tras su linea de parada: la calzada principal (de frente y derecha) sigue
# hasta su esquina, y el ramal de giro a la izquierda cruza el ovalo junto a otra esquina y llega a la union de su
# salida. frente, derecha: (salida, arista por la que sigue); giro: (salida, arista de la salida).
REDUCTO = {
    "RN": {"principal": "RN_NO", "ramal": "RN_NE", "ramal2": "NE_MJ",
           "frente": ("RS", "NO_SO"), "derecha": ("L", "NO_ML"), "giro": ("J", "S1_J")},
    "RS": {"principal": "RS_SE", "ramal": "RS_SO", "ramal2": "SO_ML",
           "frente": ("RN", "SE_NE"), "derecha": ("J", "SE_MJ"), "giro": ("L", "S1_L")},
}
# Conexiones carril a carril que no dependen de los carriles de Reducto: (desde, hacia, carril de origen, carril de
# destino). Son los caminos de 28 de Julio y de Balboa por el ovalo y el paso de cada lado a su salida.
CON_NE = [("J_NE", "S1_RN", 0, 0), ("J_NE", "NE_NO", 0, 0), ("J_NE", "NE_NO", 1, 1), ("J_NE", "NE_NO", 2, 2),
          ("SE_NE", "S1_RN", 0, 0), ("SE_NE", "S1_RN", 1, 1)]
CON_NO = [("NE_NO", "NO_ML", 0, 0), ("NE_NO", "NO_ML", 1, 1), ("NE_NO", "NO_SO", 2, 2)]
CON_SO = [("NO_SO", "S1_RS", 0, 0), ("NO_SO", "S1_RS", 1, 1), ("NO_SO", "S1_RS", 2, 2),
          ("B_SO", "S1_RS", 0, 0), ("B_SO", "SO_SE", 0, 0), ("B_SO", "SO_SE", 1, 1), ("B_SO", "SO_SE", 2, 2)]
CON_SE = [("SO_SE", "SE_MJ", 0, 0), ("SO_SE", "SE_MJ", 1, 1), ("SO_SE", "SE_MJ", 2, 2), ("SO_SE", "SE_NE", 2, 1)]
CON_MJ = [("SE_MJ", "S1_J", 0, 0), ("SE_MJ", "S1_J", 1, 1), ("SE_MJ", "S1_J", 2, 2)]
CON_ML = [("NO_ML", "S1_L", 0, 0), ("NO_ML", "S1_L", 1, 1)]

# Camino de cada movimiento: aristas en orden. Son los 12 del estudio mas Balboa hacia Larco (18.11.2026). CAMINOS
# (derivar_tablas) se queda con los que aparecen en la disposicion. Con el semaforo E1, S1_J pasa a ser "MJ_E1 S1_J".
CAMINOS_TODOS = {
    ("RN", "RS"): ["RN_S1", "RN_NO", "NO_SO", "S1_RS"],
    ("RN", "L"): ["RN_S1", "RN_NO", "NO_ML", "S1_L"],
    ("RN", "J"): ["RN_S1", "RN_NE", "NE_MJ", "S1_J"],
    ("RS", "RN"): ["RS_S1", "RS_SE", "SE_NE", "S1_RN"],
    ("RS", "J"): ["RS_S1", "RS_SE", "SE_MJ", "S1_J"],
    ("RS", "L"): ["RS_S1", "RS_SO", "SO_ML", "S1_L"],
    ("B", "J"): ["B_S1", "B_SO", "SO_SE", "SE_MJ", "S1_J"],
    ("B", "RS"): ["B_S1", "B_SO", "S1_RS"],
    ("B", "RN"): ["B_S1", "B_SO", "SO_SE", "SE_NE", "S1_RN"],
    ("B", "L"): ["B_S1", "B_ML", "S1_L"],
    ("J", "L"): ["J_S1", "J_NE", "NE_NO", "NO_ML", "S1_L"],
    ("J", "RN"): ["J_S1", "J_NE", "S1_RN"],
    ("J", "RS"): ["J_S1", "J_NE", "NE_NO", "NO_SO", "S1_RS"],
}
# Trazado del giro de Balboa hacia Larco (B_ML): nodos de la via 366715629 de OpenStreetMap (tertiary_link de 1 carril,
# 44.6 m del cruce peatonal de Balboa a la union ML), en las coordenadas de entrada/geometria_osm.json. Son, en orden,
# los nodos 3707018505, 3707018507, 3707018508, 3707018509, 3707018510 y 3707018512
# (pruebas/correccion_carriles/ramal_balboa_osm.py los vuelve a proyectar desde el archivo de OSM y los compara). No
# van los dos primeros nodos de la via (el cruce peatonal zB, que esta en el eje de Balboa, y 12820893202): el tramo
# nace en el lugar del carril izquierdo de Balboa, 1 m despues de su linea de parada, y va recto al primer nodo de la
# lista. Pasa al oeste de la isla chica (OSM 653650080) y no cruza ningun lado del ovalo; llega a la union ML por
# donde llega el ramal de giro de Reducto sur, como en OpenStreetMap.
RAMAL_BALBOA_LARCO = [(641.895, 613.907), (642.977, 617.798), (643.170, 621.141), (642.684, 625.022),
                      (641.327, 628.884), (638.180, 634.803)]
ESQUINAS = ["NO", "NE", "SO", "SE"]
NODOS_SEMAFORO = ["P_RN", "P_RS", "P_B", "P_J"] + ESQUINAS + ["MJ", "ML"]

# Semaforo E1 del puente (variante --puente): la salida hacia el puente se corta en E1 (OSM 263623489). En OSM el
# carril izquierdo de esa calzada es solo de giro (turn:lanes=left|through|through): aqui solo gira a la auxiliar,
# una salida sin demanda; los otros dos siguen hacia el puente.
PUENTE_ARISTAS = {"MJ_E1": ("MJ", "E1", 3), "S1_J": ("E1", "Js", 3), "E1_AUX": ("E1", "AUXs", 1)}
LARGO_AUX = 60.0               # m de la salida auxiliar (sin demanda)
GIRO_AUX = 25.0                # grados a la izquierda de la salida hacia el puente (solo para el dibujo)


def centro_carriles(n, carriles):
    """Desplazamiento a la derecha del eje (m) del centro de un grupo de carriles de una arista de n carriles con
    spreadType="center" (el carril 0 es el de la derecha). Se usa en las entradas del estudio (ANCHO_AFUERA)."""
    return sum(((n - 1) / 2 - k) * ANCHO_AFUERA for k in carriles) / len(carriles)


def leer_reducto(o, carriles, numero):
    """(n carriles de la calzada principal, g carriles de giro a la izquierda, carriles que giran a la derecha,
    carriles que siguen de frente) de una entrada de Reducto. Se detiene si la disposicion no se puede armar con esta
    red: el giro a la izquierda sale por un ramal propio, y un giro a la derecha no puede cruzar a un carril que sigue
    de frente."""
    p = REDUCTO[o]
    (d_frente, a_frente), (d_derecha, a_derecha), (d_giro, a_giro) = p["frente"], p["derecha"], p["giro"]
    usos = [set(c) for c in carriles]
    for k, u in enumerate(usos):
        if not u or not u <= {d_frente, d_derecha, d_giro}:
            raise SystemExit(f"DISPOSICION[{o}]: el carril {k} va a {sorted(u)}; desde {o} solo se va a "
                             f"{d_frente} (de frente), {d_derecha} (derecha) o {d_giro} (izquierda)")
        if d_giro in u and u != {d_giro}:
            raise SystemExit(f"DISPOSICION[{o}]: el carril {k} comparte el giro a la izquierda con otro movimiento; esta "
                             "red no lo arma (el giro sale por un ramal propio): hay que redisenar, no cambiar la tabla")
    g = sum(1 for u in usos if u == {d_giro})
    n = len(usos) - g
    if g < 1 or n < 1 or any(u == {d_giro} for u in usos[:n]):
        raise SystemExit(f"DISPOSICION[{o}]: los carriles de giro a la izquierda deben ser los de mas a la izquierda, y "
                         "al menos uno")
    derecha = [k for k in range(n) if d_derecha in usos[k]]
    frente = [k for k in range(n) if d_frente in usos[k]]
    if not derecha or derecha != list(range(len(derecha))):
        raise SystemExit(f"DISPOSICION[{o}]: los carriles que giran a la derecha deben ser los de mas a la derecha, y al "
                         "menos uno")
    if not frente or frente != list(range(frente[0], frente[0] + len(frente))):
        raise SystemExit(f"DISPOSICION[{o}]: los carriles de frente deben ser seguidos, y al menos uno")
    cruza = [k for k in derecha if any(j < k for j in frente)]
    if cruza:
        raise SystemExit(f"DISPOSICION[{o}]: el giro a la derecha desde el carril {cruza[0]} cruzaria a un carril de su "
                         "derecha que sigue de frente; esta red no lo arma (simplificacion declarada)")
    if len(frente) > numero[a_frente] or len(derecha) > numero[a_derecha] or g > numero[a_giro]:
        raise SystemExit(f"DISPOSICION[{o}]: mas carriles que los que tiene la calzada a la que entran")
    return n, g, derecha, frente


def derivar_tablas(disposicion):
    """Todas las tablas de carriles de la red, a partir de la disposicion de las entradas. Reglas:
      - cada carril de una entrada sigue al tramo de sus salidas: en Reducto, la calzada principal o el ramal de giro;
        en 28 de Julio y Balboa, la calzada, que llega con todos sus carriles a su primera esquina;
      - cada tramo que nace en una linea de parada tiene tantos carriles como carriles de la entrada lo alimentan, en
        el mismo orden, y nace en el lugar de esos carriles (CENTROS: m a la derecha del eje de la entrada);
      - el ramal de giro de Reducto conserva sus carriles al cruzar el ovalo y entra a los carriles de la IZQUIERDA de
        su salida;
      - en su esquina, la calzada principal de Reducto gira a la derecha desde sus carriles de la derecha y sigue de
        frente, en orden, a los carriles del lado del ovalo;
      - Balboa hacia Larco sale del carril izquierdo de Balboa por un tramo propio de 1 carril (B_ML) y entra al
        carril izquierdo de la salida hacia Larco.
    El orden de CONEXIONES es el del constructor anterior (asi, con DISPOSICION_ANTERIOR, el .con.xml sale igual)."""
    for o in ARISTA_ENTRADA:
        if o not in disposicion or not disposicion[o]:
            raise SystemExit(f"DISPOSICION: falta la entrada {o}")
    pedidos = [(o, d) for o in ARISTA_ENTRADA for destinos in disposicion[o] for d in destinos]
    sin_camino = sorted({m for m in pedidos if m not in CAMINOS_TODOS})
    if sin_camino:
        raise SystemExit(f"DISPOSICION: movimientos que esta red no tiene (CAMINOS_TODOS): {sin_camino}")
    caminos = {m: list(c) for m, c in CAMINOS_TODOS.items() if m in pedidos}
    entrada = {m: [k for k, destinos in enumerate(disposicion[m[0]]) if m[1] in destinos] for m in caminos}
    numero = {**CARRILES_SALIDAS, **CARRILES_OVALO}
    for o, arista in ARISTA_ENTRADA.items():
        numero[arista] = len(disposicion[o])
    parada, ramal, esquina, union, centros = {}, {}, {}, {}, {}
    for o, p in REDUCTO.items():
        n, g, derecha, frente = leer_reducto(o, disposicion[o], numero)
        arista = ARISTA_ENTRADA[o]
        numero.update({p["principal"]: n, p["ramal"]: g, p["ramal2"]: g})
        parada[o] = [(arista, p["principal"], k, k) for k in range(n)] + \
                    [(arista, p["ramal"], n + j, j) for j in range(g)]
        ramal[o] = [(p["ramal"], p["ramal2"], j, j) for j in range(g)]
        libres = numero[p["giro"][1]]
        union[o] = [(p["ramal2"], p["giro"][1], j, libres - g + j) for j in range(g)]
        esquina[o] = [(p["principal"], p["derecha"][1], k, j) for j, k in enumerate(derecha)] + \
                     [(p["principal"], p["frente"][1], k, i) for i, k in enumerate(frente)]
        centros[p["principal"]] = centro_carriles(n + g, list(range(n)))
        centros[p["ramal"]] = centro_carriles(n + g, list(range(n, n + g)))
    for o, calzada in (("B", "B_SO"), ("J", "J_NE")):
        arista = ARISTA_ENTRADA[o]
        numero[calzada] = numero[arista]
        parada[o] = [(arista, calzada, k, k) for k in range(numero[arista])]
        centros[calzada] = centro_carriles(numero[arista], list(range(numero[arista])))
    union["B"] = []
    a_larco = entrada.get(("B", "L"), [])
    if a_larco:
        if a_larco != [numero["B_S1"] - 1]:
            raise SystemExit("DISPOSICION[B]: el giro hacia Larco sale solo del carril de la izquierda; esta red arma su "
                             "tramo (B_ML) con 1 carril")
        numero["B_ML"] = 1
        parada["B"] = parada["B"] + [("B_S1", "B_ML", a_larco[0], 0)]
        centros["B_ML"] = centro_carriles(numero["B_S1"], a_larco)
        union["B"] = [("B_ML", "S1_L", 0, numero["S1_L"] - 1)]
    conexiones = (
        parada["RN"] + parada["RS"] + parada["B"] + parada["J"]         # lineas de parada de afuera
        + CON_NE + ramal["RN"]            # esquina NE (con los dos cruces del ramal de Reducto norte)
        + CON_NO + esquina["RN"]          # esquina NO
        + CON_SO + ramal["RS"]            # esquina SO (con los dos cruces del ramal de Reducto sur)
        + CON_SE + esquina["RS"]          # esquina SE
        + CON_MJ + union["RN"]            # union de la salida hacia el puente
        + CON_ML + union["RS"] + union["B"]                             # union de la salida hacia Larco
    )
    afuera = {e: (a, b, numero[e]) for e, (a, b) in NODOS_AFUERA.items()}
    g_n, g_s = numero["RN_NE"], numero["RS_SO"]
    # Adentro: id -> (desde, hasta, carriles, carriles en OSM, que es y por que esos carriles)
    internos = {
        "J_NE": ("P_J", "NE", numero["J_NE"], "3", "28 de Julio desde su linea de parada hasta NE"),
        "RN_NO": ("P_RN", "NO", numero["RN_NO"], "3", "Reducto desde el norte, calzada principal, hasta NO"),
        "RN_NE": ("P_RN", "NE", g_n, "2", f"ramal del giro izquierdo de Reducto norte hasta NE: {g_n} carril(es), los "
                  "que giran hacia el puente en DISPOSICION"),
        "RS_SE": ("P_RS", "SE", numero["RS_SE"], "2", "Reducto desde el sur, calzada principal, hasta SE: los carriles "
                  "de frente y derecha de DISPOSICION"),
        "RS_SO": ("P_RS", "SO", g_s, "2", f"ramal del giro izquierdo de Reducto sur hasta SO: {g_s} carril(es), los que "
                  "giran hacia Larco en DISPOSICION"),
        "B_SO": ("P_B", "SO", numero["B_SO"], "3", "Balboa desde su linea de parada hasta SO"),
        "NE_NO": ("NE", "NO", numero["NE_NO"], "3", "lado norte del ovalo: 28 de Julio hacia Larco"),
        "NO_SO": ("NO", "SO", numero["NO_SO"], "2 y 3", "lado oeste: Reducto hacia el sur. OSM: 2 carriles de NO al ramal "
                  "y 3 del ramal a SO; aqui 3 en todo el lado para que Reducto de frente pase con sus 3 carriles"),
        "SO_SE": ("SO", "SE", numero["SO_SE"], "3", "lado sur: Balboa hacia el puente"),
        "SE_NE": ("SE", "NE", numero["SE_NE"], "2", "lado este: Reducto hacia el norte"),
        "NO_ML": ("NO", "ML", numero["NO_ML"], "2", "salida hacia Larco desde NO hasta la union con el ramal de Reducto "
                  "sur"),
        "SE_MJ": ("SE", "MJ", numero["SE_MJ"], "3", "salida hacia el puente desde SE hasta la union con el ramal de "
                  "Reducto norte"),
        "NE_MJ": ("NE", "MJ", g_n, "2", f"ramal de Reducto norte despues de cruzar el ovalo ({g_n} carril(es), como "
                  "RN_NE)"),
        "SO_ML": ("SO", "ML", g_s, "1 y 2", "ramal de Reducto sur despues de cruzar el ovalo. OSM: 1 carril entre los dos "
                  f"cruces y 2 despues; aqui {g_s}, como RS_SO, en todo el tramo"),
    }
    if "B_ML" in numero:
        internos["B_ML"] = ("P_B", "ML", 1, "1", "giro de Balboa hacia Larco: tramo propio de la linea de parada de "
                            "Balboa a la union ML, por el oeste, sin cruzar los lados del ovalo (OSM, via 366715629)")
    puente = ([("SE_MJ", "MJ_E1", 0, 0), ("SE_MJ", "MJ_E1", 1, 1), ("SE_MJ", "MJ_E1", 2, 2)]
              + [("NE_MJ", "MJ_E1", j, 3 - g_n + j) for j in range(g_n)]
              + [("MJ_E1", "S1_J", 0, 0), ("MJ_E1", "S1_J", 1, 1), ("MJ_E1", "E1_AUX", 2, 0)])
    return {"AFUERA": afuera, "CARRILES_INTERNOS": internos, "CONEXIONES": conexiones, "CAMINOS": caminos,
            "CARRILES_ENTRADA": entrada, "CENTROS": centros, "PUENTE_CONEXIONES": puente}


def carril_a_carril(tablas):
    """{(entrada, carril): {salida: [camino, ...]}}: a que salidas llega cada carril de cada entrada siguiendo
    CONEXIONES, y por donde (cada camino es la lista de sus carriles, "arista_carril")."""
    hacia = {}
    for a, b, i, j in tablas["CONEXIONES"]:
        hacia.setdefault((a, i), []).append((b, j))
    salida_de = {arista: d for d, arista in ARISTA_SALIDA.items()}
    res = {}
    for o, arista in ARISTA_ENTRADA.items():
        for k in range(tablas["AFUERA"][arista][2]):
            llegadas, pila = {}, [[(arista, k)]]
            while pila:
                camino = pila.pop()
                a, i = camino[-1]
                if a in salida_de:
                    llegadas.setdefault(salida_de[a], []).append([f"{x}_{y}" for x, y in camino])
                    continue
                if len(camino) > 12:
                    raise SystemExit(f"CONEXIONES: camino sin fin desde {arista}_{k}")
                pila += [camino + [sig] for sig in hacia.get((a, i), [])]
            res[(o, k)] = {d: sorted(c) for d, c in llegadas.items()}
    return res


def comprobar_tablas(tablas, disposicion):
    """Detiene el armado si las tablas derivadas no son coherentes entre si o con la disposicion:
      - indices de carril dentro de su arista, ninguna conexion repetida, y cada carril de destino recibe a lo sumo un
        carril de cada arista;
      - todo carril que no es de una salida tiene a donde seguir, y todo carril de una salida recibe a alguien;
      - cada carril de cada entrada llega EXACTAMENTE a las salidas de la disposicion, por el camino de su movimiento
        (CAMINOS) y por ningun otro: no hay vuelta en U ni movimientos de mas;
      - toda conexion la usa al menos un movimiento (una que no usara nadie quedaria en rojo para siempre)."""
    numero = {**{e: v[2] for e, v in tablas["AFUERA"].items()}, **{e: v[2] for e, v in tablas["CARRILES_INTERNOS"].items()}}
    con = tablas["CONEXIONES"]
    problemas = []
    for a, b, i, j in con:
        if not 0 <= i < numero[a]:
            problemas.append(f"{a}_{i} no existe ({a} tiene {numero[a]} carriles)")
        if not 0 <= j < numero[b]:
            problemas.append(f"{b}_{j} no existe ({b} tiene {numero[b]} carriles)")
    if len(set(con)) != len(con):
        problemas.append("conexiones repetidas")
    con_salida = {(a, i) for a, _, i, _ in con}
    con_llegada = {(b, j) for _, b, _, j in con}
    for arista, n in numero.items():
        for i in range(n):
            if arista in CARRILES_SALIDAS:
                if (arista, i) not in con_llegada:
                    problemas.append(f"a {arista}_{i} no llega nadie")
            elif (arista, i) not in con_salida:
                problemas.append(f"{arista}_{i} no tiene a donde seguir")
    for (a, b, j) in sorted({(a, b, j) for a, b, _, j in con}):
        origenes = [i for aa, bb, i, jj in con if (aa, bb, jj) == (a, b, j)]
        if len(origenes) > 1:
            problemas.append(f"{b}_{j} recibe {len(origenes)} carriles de {a}")
    usadas = set()
    for (o, k), llegadas in carril_a_carril(tablas).items():
        pedidas = set(disposicion[o][k])
        if set(llegadas) != pedidas:
            problemas.append(f"{ARISTA_ENTRADA[o]}_{k} llega a {sorted(llegadas)} y la disposicion dice {sorted(pedidas)}")
        for d, caminos in llegadas.items():
            for camino in caminos:
                aristas = [c.rsplit("_", 1)[0] for c in camino]
                if (o, d) in tablas["CAMINOS"] and aristas != tablas["CAMINOS"][(o, d)]:
                    problemas.append(f"{o}>{d}: {' '.join(camino)} no es el camino de CAMINOS")
                usadas.update(zip(camino, camino[1:]))
    for a, b, i, j in con:
        if (f"{a}_{i}", f"{b}_{j}") not in usadas:
            problemas.append(f"la conexion {a}_{i} -> {b}_{j} no la usa ningun movimiento")
    if set(tablas["CARRILES_ENTRADA"]) != set(tablas["CAMINOS"]):
        problemas.append("CARRILES_ENTRADA y CAMINOS no tienen los mismos movimientos")
    if any(o == d for o, d in tablas["CAMINOS"]):
        problemas.append("hay una vuelta en U")
    if problemas:
        raise SystemExit("armar_ovalo.comprobar_tablas: " + "; ".join(problemas))


def texto_disposicion(tablas, disposicion):
    """Lineas con la tabla carril a carril: cada carril de cada entrada, sus salidas y su camino por el ovalo."""
    nombres = {"L": "Larco", "J": "el puente", "RN": "Reducto norte", "RS": "Reducto sur"}
    lineas = []
    por_carril = carril_a_carril(tablas)
    for o, arista in ARISTA_ENTRADA.items():
        lineas.append(f"   {arista} ({len(disposicion[o])} carriles; el 0 es el de la derecha)")
        for k, destinos in enumerate(disposicion[o]):
            for d in destinos:
                for camino in por_carril[(o, k)].get(d, [["(sin camino)"]]):
                    lineas.append(f"      {arista}_{k} -> {nombres[d]:14s} {' -> '.join(camino)}")
    return lineas


def configurar(disposicion):
    """Deja en las tablas del modulo (AFUERA, CARRILES_INTERNOS, CONEXIONES, CAMINOS, CARRILES_ENTRADA, CENTROS y
    PUENTE_CONEXIONES) las que salen de la disposicion dada, ya comprobadas. Al importar el modulo se llama con
    DISPOSICION; la prueba de regresion la llama con DISPOSICION_ANTERIOR."""
    global AFUERA, CARRILES_INTERNOS, CONEXIONES, CAMINOS, CARRILES_ENTRADA, CENTROS, PUENTE_CONEXIONES, DISPOSICION_EN_USO
    tablas = derivar_tablas(disposicion)
    comprobar_tablas(tablas, disposicion)
    AFUERA, CARRILES_INTERNOS, CONEXIONES = tablas["AFUERA"], tablas["CARRILES_INTERNOS"], tablas["CONEXIONES"]
    CAMINOS, CARRILES_ENTRADA, CENTROS = tablas["CAMINOS"], tablas["CARRILES_ENTRADA"], tablas["CENTROS"]
    PUENTE_CONEXIONES, DISPOSICION_EN_USO = tablas["PUENTE_CONEXIONES"], disposicion
    return tablas


# Tablas derivadas (no se escriben a mano):
#   AFUERA             id -> (nodo de inicio, nodo final, carriles) de las 8 aristas del estudio
#   CARRILES_INTERNOS  id -> (desde, hasta, carriles, carriles en OSM, que es) de las aristas de adentro
#   CONEXIONES         [(desde, hacia, carril de origen, carril de destino)]: cada una es un enlace de semaforo_S1
#   CAMINOS            (entrada, salida) -> aristas del camino de cada movimiento
#   CARRILES_ENTRADA   (entrada, salida) -> carriles de la entrada de los que sale cada movimiento
#   CENTROS            tramo que nace en una linea de parada -> m a la derecha del eje de la entrada donde nace
configurar(DISPOSICION)


# ---------------- geometria ----------------
def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def largo(forma):
    return sum(dist(a, b) for a, b in zip(forma, forma[1:]))


def unitario(a, b):
    d = dist(a, b)
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def hacia(a, b, d):
    """Punto a d m de a en direccion a b."""
    u = unitario(a, b)
    return (a[0] + d * u[0], a[1] + d * u[1])


def lateral(p, direccion, d):
    """Punto a d m a la DERECHA de p, mirando en la direccion dada (negativo: a la izquierda)."""
    return (p[0] + d * direccion[1], p[1] - d * direccion[0])


def proyectar(forma, p):
    """(indice del tramo, punto proyectado) de p sobre la polilinea."""
    mejor = None
    for i, (a, b) in enumerate(zip(forma, forma[1:])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
        q = (a[0] + t * dx, a[1] + t * dy)
        if mejor is None or dist(p, q) < mejor[0]:
            mejor = (dist(p, q), i, q)
    return mejor[1], mejor[2]


def hasta(forma, p):
    """La polilinea desde su inicio hasta la proyeccion de p. Si el ultimo tramo queda de menos de 2 m, se quita el
    vertice anterior (un quiebre de pocos centimetros al final hace que netconvert vea una curva cerrada)."""
    i, q = proyectar(forma, p)
    res = forma[:i + 1] + [q]
    if len(res) >= 3 and dist(res[-2], res[-1]) < 2.0:
        res = res[:-2] + [q]
    return res


def desde(forma, p):
    """La polilinea desde la proyeccion de p hasta su final."""
    i, q = proyectar(forma, p)
    return [q] + forma[i + 1:]


def alargar_inicio(forma, metros):
    """Alarga la polilinea hacia atras, en linea recta con su primer tramo."""
    u = unitario(forma[1], forma[0])
    return [(forma[0][0] + metros * u[0], forma[0][1] + metros * u[1])] + forma[1:]


def alargar_final(forma, metros):
    u = unitario(forma[-2], forma[-1])
    return forma[:-1] + [(forma[-1][0] + metros * u[0], forma[-1][1] + metros * u[1])]


def texto(forma):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in forma)


def puntos(texto_forma):
    return [tuple(float(v) for v in p.split(",")) for p in texto_forma.split()]


# ---------------- lectura de entradas ----------------
def leer_estudio():
    edg = ET.parse(os.path.join(ESTUDIO, "lima.edg.xml")).getroot()
    formas = {e.get("id"): puntos(e.get("shape")) for e in edg.findall("edge")}
    net = sumolib.net.readNet(os.path.join(ESTUDIO, "lima.net.xml"), withInternal=False)
    largos = {eid: net.getEdge(eid).getLanes()[0].getLength() for eid in AFUERA}
    return formas, largos


# Lados del ovalo (circulan en sentido antihorario, con la isla a la izquierda): lado -> (esquina inicial, esquina
# final, arista). El eje de cada lado va a media calzada (carriles x ANCHO / 2) del borde de la isla.
LADOS = {"norte": ("NE", "NO", "NE_NO"), "oeste": ("NO", "SO", "NO_SO"), "sur": ("SO", "SE", "SO_SE"),
         "este": ("SE", "NE", "SE_NE")}
# Cada esquina es el cruce de dos lados: esquina -> (lado que llega, lado que sale)
CRUCE_LADOS = {"NO": ("norte", "oeste"), "SO": ("oeste", "sur"), "SE": ("sur", "este"), "NE": ("este", "norte")}
# Cruces de los ramales de giro con los lados: punto -> (ramal: los dos puntos de OSM que lo definen, lado)
CRUCE_RAMALES = {"XN": (("XN", "XE"), "norte"), "XE": (("XN", "XE"), "este"),
                 "XS": (("XS", "XO"), "sur"), "XO": (("XS", "XO"), "oeste")}


def interseccion(p, u, q, v):
    """Punto donde se cortan la recta p + t u y la recta q + s v."""
    den = u[0] * v[1] - u[1] * v[0]
    t = ((q[0] - p[0]) * v[1] - (q[1] - p[1]) * v[0]) / den
    return (p[0] + t * u[0], p[1] + t * u[1])


def leer_osm(geometria, escala):
    """Puntos (x, y) por nombre (geometria_osm.json) y el contorno de la isla.
    geometria "osm": las esquinas y los cruces de los ramales en los nodos de OSM, tal cual.
    geometria "coherente" (la de la red base): la isla que dibuja OSM (area peatonal 653650079), agrandada en el
    factor escala alrededor de su centro, rodeada por calzadas tan anchas como sus carriles (ANCHO por carril). El
    eje de cada lado conserva la direccion que le da OSM y queda a media calzada del borde de la isla; cada esquina
    es el cruce de dos ejes y cada ramal cruza los ejes por la recta que le da OSM (alejada del centro en el mismo
    factor que la isla). Lo de afuera (lineas de parada, uniones, E1) no se mueve."""
    with open(GEO, encoding="utf-8") as f:
        geo = json.load(f)
    P = {k: (v["x"], v["y"]) for k, v in geo["nodos"].items()}
    isla = [tuple(p) for p in geo["isla"]]
    if geometria == "osm":
        return P, isla
    if geometria == "medida":
        return leer_medida(P)
    c = (sum(p[0] for p in isla[:-1]) / (len(isla) - 1), sum(p[1] for p in isla[:-1]) / (len(isla) - 1))
    isla = [(c[0] + escala * (p[0] - c[0]), c[1] + escala * (p[1] - c[1])) for p in isla]
    ejes = {}
    for lado, (a, b, arista) in LADOS.items():
        d = unitario(P[a], P[b])
        n = (d[1], -d[0])                                   # a la derecha de la marcha: hacia afuera de la isla
        borde = max((v[0] - c[0]) * n[0] + (v[1] - c[1]) * n[1] for v in isla)
        h = borde + CARRILES_INTERNOS[arista][2] * ANCHO / 2
        ejes[lado] = ((c[0] + h * n[0], c[1] + h * n[1]), d)
    nuevo = dict(P)
    for esquina, (l1, l2) in CRUCE_LADOS.items():
        nuevo[esquina] = interseccion(*ejes[l1], *ejes[l2])
    for punto, ((r1, r2), lado) in CRUCE_RAMALES.items():
        u = unitario(P[r1], P[r2])
        n = (u[1], -u[0])
        dist_c = (P[r1][0] - c[0]) * n[0] + (P[r1][1] - c[1]) * n[1]      # con signo: lado del ramal
        desplazado = (P[r1][0] + (escala - 1) * dist_c * n[0], P[r1][1] + (escala - 1) * dist_c * n[1])
        nuevo[punto] = interseccion(desplazado, u, *ejes[lado])
    return nuevo, isla


# ---- geometria "medida" (nueva en medido/) ----
A_ELIP, F_ELIP = 6378137.0, 1 / 298.257223563     # WGS84, como geometria_osm.py


def utm(lat, lon, zona=18):
    """(este, norte) UTM (Snyder 1987; las mismas formulas de nudo_ovalo/geometria_osm.py)."""
    e2 = 2 * F_ELIP - F_ELIP ** 2
    ep2 = e2 / (1 - e2)
    k0 = 0.9996
    lon0 = math.radians((zona - 1) * 6 - 180 + 3)
    f, lam = math.radians(lat), math.radians(lon)
    n = A_ELIP / math.sqrt(1 - e2 * math.sin(f) ** 2)
    t = math.tan(f) ** 2
    c = ep2 * math.cos(f) ** 2
    a = (lam - lon0) * math.cos(f)
    m = A_ELIP * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * f
                  - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * math.sin(2 * f)
                  + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * math.sin(4 * f)
                  - (35 * e2 ** 3 / 3072) * math.sin(6 * f))
    x = k0 * n * (a + (1 - t + c) * a ** 3 / 6 + (5 - 18 * t + t ** 2 + 72 * c - 58 * ep2) * a ** 5 / 120)
    y = k0 * (m + n * math.tan(f) * (a ** 2 / 2 + (5 - t + 9 * c + 4 * c ** 2) * a ** 4 / 24
                                       + (61 - 58 * t + t ** 2 + 600 * c - 330 * ep2) * a ** 6 / 720))
    return x + 500000.0, y


def convergencia_utm(lat, lon):
    """Angulo (rad) del norte verdadero respecto del norte de la cuadricula UTM 18 (positivo: el norte verdadero
    apunta un poco al este de la cuadricula). Google Maps esta orientado al norte verdadero; la red, a la cuadricula."""
    e0, n0 = utm(lat, lon)
    e1, n1 = utm(lat + 0.001, lon)
    return math.atan2(e1 - e0, n1 - n0)


def leer_medida(P):
    """Geometria "medida": las cuatro esquinas a las distancias medidas en las capturas de Google Maps de Fabian
    (medidas/medidas_google.json, esquinas_promedio_m: cruce de los ejes de las calzadas, en m desde su centroide,
    x al este e y al norte verdadero). Se giran a la cuadricula UTM (convergencia de meridianos) y se centran en el
    centroide de las cuatro esquinas de OSM. No se escalan ni se ajustan: cada lado queda con su medida.
    Los ramales de giro a la izquierda no se ven en Google Maps (vista de mapa). Sus cruces con los lados del ovalo
    (XN y XE junto a la esquina NE, XS y XO junto a SO) quedan, segun RAMALES (SUPUESTO):
      "distancia"  (por defecto) a la misma distancia de su esquina que en OSM, sobre el eje medido;
      "proporcion" en la misma fraccion del lado que en OSM;
      "esquina"    pegados a la esquina (el ramal cruza los dos lados en la esquina misma): la cota con mas lugar
                   para esperar en los lados.
    La isla es el cuadrilatero que dejan los cuatro ejes con calzadas de ANCHO m por carril."""
    with open(MEDIDAS, encoding="utf-8") as f:
        med = json.load(f)
    g = {k: tuple(v) for k, v in med["esquinas_promedio_m"].items()}
    th = convergencia_utm(*LATLON_OVALO)
    c_osm = (sum(P[k][0] for k in ESQUINAS) / 4, sum(P[k][1] for k in ESQUINAS) / 4)
    cg = (sum(g[k][0] for k in ESQUINAS) / 4, sum(g[k][1] for k in ESQUINAS) / 4)
    nuevo = dict(P)
    for k in ESQUINAS:
        x, y = g[k][0] - cg[0], g[k][1] - cg[1]
        nuevo[k] = (c_osm[0] + x * math.cos(th) + y * math.sin(th), c_osm[1] - x * math.sin(th) + y * math.cos(th))
    for punto, esquina, otra in (("XN", "NE", "NO"), ("XE", "NE", "SE"), ("XS", "SO", "SE"), ("XO", "SO", "NO")):
        d = dist(P[esquina], P[punto])
        if RAMALES == "proporcion":
            d = d / dist(P[esquina], P[otra]) * dist(nuevo[esquina], nuevo[otra])
        elif RAMALES == "esquina":
            d = 0.0
        nuevo[punto] = hacia(nuevo[esquina], nuevo[otra], d)
    return nuevo, isla_entre_ejes(nuevo)


def isla_entre_ejes(P):
    """Poligono (cerrado) de la isla: el cuadrilatero que dejan los cuatro ejes corridos media calzada hacia adentro."""
    c = (sum(P[k][0] for k in ESQUINAS) / 4, sum(P[k][1] for k in ESQUINAS) / 4)
    rectas = {}
    for lado, (a, b, arista) in LADOS.items():
        d = unitario(P[a], P[b])
        n = (-d[1], d[0])
        if (c[0] - P[a][0]) * n[0] + (c[1] - P[a][1]) * n[1] < 0:
            n = (-n[0], -n[1])
        h = CARRILES_INTERNOS[arista][2] * ANCHO / 2
        rectas[lado] = ((P[a][0] + h * n[0], P[a][1] + h * n[1]), d)
    vert = [interseccion(*rectas[l1], *rectas[l2])
            for l1, l2 in (("norte", "oeste"), ("oeste", "sur"), ("sur", "este"), ("este", "norte"))]
    return vert + [vert[0]]


# ---------------- red plana ----------------
SEPARA_PARADA = 1.0     # m entre una linea de parada de afuera y el comienzo de la arista que sigue
# Linea de parada de Balboa (18.11.2026). Con el giro hacia Larco, de ese nodo salen dos tramos (B_SO y B_ML) y
# netconvert, que calcula por su cuenta el extremo de una arista que termina justo en su nodo, haria terminar la
# entrada 3.44 m antes (deja su radio de 4 m entre la entrada y el tramo nuevo; medido al armar). Para que la linea
# de parada quede donde estaba, el extremo de B_S1 se escribe a mano: EXTREMO_BALBOA m despues del nodo, que es donde
# netconvert lo dejaba cuando el nodo tenia una sola salida (HUECO_BALBOA m de tramo interno entre B_S1 y B_SO en la
# red anterior, red/ovalo_estudio.giros.txt). Con --junctions.endpoint-shape, un extremo escrito se respeta. Solo se
# aplica si existe B_ML; main() comprueba que el tramo interno siga midiendo HUECO_BALBOA.
HUECO_BALBOA = 0.65
EXTREMO_BALBOA = SEPARA_PARADA - HUECO_BALBOA
UNION = 3.0             # m antes y despues de una union (MJ, ML) donde terminan y empiezan sus aristas
LARGO_MINIMO = 2.0      # m de calzada que se deja como minimo entre una esquina y una union


def semi(arista):
    """Media calzada (m) de una arista de adentro."""
    return CARRILES_INTERNOS[arista][2] * ANCHO / 2


def seno(u, v):
    """Seno del angulo entre dos direcciones (con piso de 0.2 para cruces casi paralelos)."""
    return max(0.2, abs(u[0] * v[1] - u[1] * v[0]))


def direcciones_ramales(P):
    """Direccion con que cada ramal de giro atraviesa cada calzada del ovalo: el de Reducto norte cruza el lado norte
    entrando (desde su cruce peatonal hacia XN) y el lado este saliendo (de XE hacia la union MJ); el de Reducto sur
    cruza el lado sur entrando (desde su semaforo hacia XS) y el lado oeste saliendo (de XO hacia la union ML)."""
    return {"XN": unitario(P["zRNg"], P["XN"]), "XE": unitario(P["XE"], P["MJ"]),
            "XS": unitario(P["PRSg"], P["XS"]), "XO": unitario(P["XO"], P["ML"])}


def avanzar(p, u, d):
    return (p[0] + d * u[0], p[1] + d * u[1])


def tramo(forma, s0, s1):
    """La parte de la polilinea entre las distancias s0 y s1 (m desde su inicio)."""
    res, acum = [], 0.0
    for a, b in zip(forma, forma[1:]):
        t = dist(a, b)
        if t > 0 and acum + t >= s0 and acum <= s1:
            u0, u1 = max(0.0, (s0 - acum) / t), min(1.0, (s1 - acum) / t)
            if not res:
                res.append((a[0] + u0 * (b[0] - a[0]), a[1] + u0 * (b[1] - a[1])))
            res.append((a[0] + u1 * (b[0] - a[0]), a[1] + u1 * (b[1] - a[1])))
        acum += t
    return res


def recortar(forma, ini, fin, nombre):
    """La polilinea sin sus primeros `ini` m ni sus ultimos `fin` m (los bordes de las esquinas)."""
    total = largo(forma)
    if ini + fin > total - 0.5:
        raise SystemExit(f"{nombre}: las esquinas se pisan ({ini:.1f} + {fin:.1f} m de esquina en {total:.1f} m de "
                         "eje): la isla es demasiado chica para sus carriles (ver salidas/espacio_lados.txt).")
    return tramo(forma, ini, total - fin)


def armar_plano(P, formas_estudio, alargues, puente):
    """Nodos y aristas (con su trazado) de la red del ovalo. alargues: {arista de afuera: m que se alarga su recta}.
    Cada arista de adentro va de borde a borde de sus esquinas (netconvert --junctions.endpoint-shape): una esquina
    ocupa, sobre cada calzada que llega o sale, media calzada de la otra calzada que la cruza (dividida por el seno
    del angulo de cruce). Asi lo que queda entre dos esquinas es el lugar real donde un vehiculo puede esperar."""
    nodos, aristas = {}, {}
    # 1. entradas: el trazado del estudio hasta el semaforo de OSM (linea de parada de afuera)
    dir_final = {}
    for nodo, (entrada, semaforo) in PARADAS.items():
        forma = hasta(formas_estudio[entrada], P[semaforo])
        dir_final[entrada] = unitario(forma[-2], forma[-1])
        if alargues.get(entrada):
            forma = alargar_inicio(forma, alargues[entrada])
        nodos[nodo] = forma[-1]
        nodos[AFUERA[entrada][0]] = forma[0]
        if entrada == "B_S1" and "B_ML" in CARRILES_INTERNOS:
            forma = forma[:-1] + [avanzar(forma[-1], dir_final[entrada], EXTREMO_BALBOA)]    # ver EXTREMO_BALBOA
        aristas[entrada] = (AFUERA[entrada][0], nodo, AFUERA[entrada][2], forma)
    # las uniones MJ y ML quedan en su lugar de OSM, salvo que la esquina agrandada las alcance: entonces se corren
    # hacia afuera lo justo para dejar LARGO_MINIMO m de calzada entre la esquina y la union
    P = dict(P)
    for esquina, union, arista, cruza in (("SE", "MJ", "SE_MJ", "RS_SE"), ("NO", "ML", "NO_ML", "NO_SO")):
        u = unitario(P[esquina], P[union])
        otra = unitario(P["SE"], P["NE"]) if esquina == "SE" else unitario(P["NO"], P["SO"])
        necesario = semi(cruza) / seno(u, otra) + UNION + LARGO_MINIMO
        if dist(P[esquina], P[union]) < necesario:
            P[union] = avanzar(P[esquina], u, necesario)
    for k in ESQUINAS + ["MJ", "ML"]:
        nodos[k] = P[k]
    # 2. ejes de adentro, de nodo a nodo. Cada tramo que nace en una linea de parada sale del lugar de sus carriles
    #    (CENTROS, de la disposicion): donde una entrada se abre en dos (Reducto norte y sur), cada parte sale del
    #    lugar de los suyos; el giro de Balboa hacia Larco, del lugar del carril izquierdo de Balboa
    rn, rs = dir_final["RN_S1"], dir_final["RS_S1"]

    def tras_parada(nodo, direccion, a_la_derecha=0.0):
        return avanzar(lateral(nodos[nodo], direccion, a_la_derecha), direccion, SEPARA_PARADA)
    ejes = {
        "J_NE": [tras_parada("P_J", dir_final["J_S1"], CENTROS["J_NE"]), P["zJ"], P["NE"]],
        "B_SO": [tras_parada("P_B", dir_final["B_S1"], CENTROS["B_SO"]), P["zB"], P["SO"]],
        "RN_NO": [tras_parada("P_RN", rn, CENTROS["RN_NO"]), P["NO"]],
        "RN_NE": [tras_parada("P_RN", rn, CENTROS["RN_NE"]), P["zRNg"], P["XN"]],
        "RS_SE": [tras_parada("P_RS", rs, CENTROS["RS_SE"]), P["mRS"], P["SE"]],
        "RS_SO": [tras_parada("P_RS", rs, CENTROS["RS_SO"]), P["XS"]],
        "NE_NO": [P["NE"], P["NO"]], "NO_SO": [P["NO"], P["SO"]],
        "SO_SE": [P["SO"], P["SE"]], "SE_NE": [P["SE"], P["NE"]],
        "NO_ML": [P["NO"], P["ML"]], "SE_MJ": [P["SE"], P["MJ"]],
        "NE_MJ": [P["XE"], P["MJ"]], "SO_ML": [P["XO"], P["ML"]],
    }
    if "B_ML" in CARRILES_INTERNOS:
        # Balboa hacia Larco: del carril izquierdo de Balboa, por el trazado de OpenStreetMap, hasta la union ML
        ejes["B_ML"] = ([tras_parada("P_B", dir_final["B_S1"], CENTROS["B_ML"])] + list(RAMAL_BALBOA_LARCO)
                        + [P["ML"]])
    ini = {k: unitario(v[0], v[1]) for k, v in ejes.items()}        # direccion al comienzo de cada eje
    fin = {k: unitario(v[-2], v[-1]) for k, v in ejes.items()}      # y al final
    norte, oeste, sur, este = ini["NE_NO"], ini["NO_SO"], ini["SO_SE"], ini["SE_NE"]
    r = direcciones_ramales(P)
    # 3. bordes de las esquinas: (m que se quitan al comienzo, m que se quitan al final) de cada eje
    recortes = {
        "J_NE": (0.0, semi("SE_NE") / seno(fin["J_NE"], este)),
        "B_SO": (0.0, semi("NO_SO") / seno(fin["B_SO"], oeste)),
        "RN_NO": (0.0, semi("NE_NO") / seno(fin["RN_NO"], norte)),
        "RN_NE": (0.0, semi("NE_NO") / seno(fin["RN_NE"], norte)),
        "RS_SE": (0.0, semi("SO_SE") / seno(fin["RS_SE"], sur)),
        "RS_SO": (0.0, semi("SO_SE") / seno(fin["RS_SO"], sur)),
        # los lados: en NE y SO la esquina incluye el cruce del ramal de giro
        "NE_NO": (max(dist(P["NE"], P["XN"]) + semi("RN_NE") / seno(norte, r["XN"]), semi("SE_NE") / seno(norte, este)),
                  semi("NO_SO") / seno(norte, oeste)),
        "NO_SO": (semi("NE_NO") / seno(oeste, norte),
                  max(dist(P["XO"], P["SO"]) + semi("SO_ML") / seno(oeste, r["XO"]), semi("SO_SE") / seno(oeste, sur))),
        "SO_SE": (max(dist(P["SO"], P["XS"]) + semi("RS_SO") / seno(sur, r["XS"]), semi("NO_SO") / seno(sur, oeste)),
                  semi("RS_SE") / seno(sur, este)),
        "SE_NE": (semi("SO_SE") / seno(este, sur),
                  max(dist(P["XE"], P["NE"]) + semi("NE_MJ") / seno(este, r["XE"]), semi("NE_NO") / seno(este, norte))),
        "NO_ML": (semi("NO_SO") / seno(ini["NO_ML"], oeste), UNION),
        "SE_MJ": (semi("RS_SE") / seno(ini["SE_MJ"], este), UNION),
        "NE_MJ": (semi("SE_NE") / seno(ini["NE_MJ"], este), UNION),
        "SO_ML": (semi("NO_SO") / seno(ini["SO_ML"], oeste), UNION),
    }
    if "B_ML" in ejes:
        recortes["B_ML"] = (0.0, UNION)       # no pasa por ninguna esquina: de la linea de parada a la union
    trazado = {eid: recortar(ejes[eid], a, b, eid) for eid, (a, b) in recortes.items()}
    for eid, (a, b, carriles, _, _) in CARRILES_INTERNOS.items():
        aristas[eid] = (a, b, carriles, trazado[eid])
    # 5. salidas del estudio: empiezan en el borde de su esquina (o pasada la union)
    inicio_salida = {"S1_RN": semi("NE_NO"), "S1_RS": semi("SO_SE"), "S1_L": UNION, "S1_J": UNION}
    for eid, (a, b, carriles) in AFUERA.items():
        if eid in aristas or (puente and eid == "S1_J"):
            continue
        forma = [nodos[a]] + desde(formas_estudio[eid], nodos[a])[1:]
        u = unitario(forma[0], forma[1])
        cruza = {"S1_RN": norte, "S1_RS": sur}.get(eid)
        recorte = inicio_salida[eid] / (seno(u, cruza) if cruza else 1.0)
        forma = tramo(forma, recorte, largo(forma))
        if alargues.get(eid):
            forma = alargar_final(forma, alargues[eid])
        nodos[b] = forma[-1]
        aristas[eid] = (a, b, carriles, forma)
    if puente:
        # la salida hacia el puente se corta en E1 (su linea de parada); despues de E1 sigue S1_J hasta el mismo final
        # que sin E1. El carril izquierdo solo lleva a la salida auxiliar, que no tiene demanda.
        forma = [nodos["MJ"]] + desde(formas_estudio["S1_J"], nodos["MJ"])[1:]
        forma = tramo(forma, UNION, largo(forma))
        if alargues.get("S1_J"):
            forma = alargar_final(forma, alargues["S1_J"])
        i, q = proyectar(forma, P["E1"])
        u = unitario(forma[i], forma[i + 1])
        nodos["E1"] = q
        nodos["Js"] = forma[-1]
        aristas["MJ_E1"] = ("MJ", "E1", 3, forma[:i + 1] + [q])
        aristas["S1_J"] = ("E1", "Js", 3, [avanzar(q, u, SEPARA_PARADA)] + forma[i + 1:])
        r = math.atan2(u[1], u[0]) + math.radians(GIRO_AUX)
        a0 = avanzar(lateral(q, u, -ANCHO), u, SEPARA_PARADA)          # donde esta el carril izquierdo (2 de 3)
        fin_aux = avanzar(a0, (math.cos(r), math.sin(r)), LARGO_AUX)
        nodos["AUXs"] = fin_aux
        aristas["E1_AUX"] = ("E1", "AUXs", 1, [a0, fin_aux])
    return nodos, aristas


def escribir_plano(nombre, nodos, aristas, puente, lentas=()):
    """lentas: conexiones (desde, hacia, carril de origen, carril de destino) que llevan speed=VEL_GIRO_MIN."""
    cabeza = '<?xml version="1.0" encoding="UTF-8"?>\n<!-- Generado por armar_ovalo.py. No editar a mano. -->\n'
    rutas = {k: os.path.join(RED, f"{nombre}.{k}.xml") for k in ("nod", "edg", "con")}
    with open(rutas["nod"], "w", encoding="utf-8", newline="\n") as f:
        f.write(cabeza + "<nodes>\n")
        for nid, (x, y) in nodos.items():
            if nid in NODOS_SEMAFORO:
                extra = f' type="traffic_light" tl="{TLS}"'
            elif nid == "E1":
                extra = f' type="traffic_light" tl="{TLS_E1}"'
            else:
                extra = ' type="priority"'
            f.write(f'    <node id="{nid}" x="{x:.2f}" y="{y:.2f}"{extra}/>\n')
        f.write("</nodes>\n")
    with open(rutas["edg"], "w", encoding="utf-8", newline="\n") as f:
        f.write(cabeza + "<edges>\n")
        for eid, (a, b, carriles, forma) in aristas.items():
            # carriles de adentro con otro ancho (supuesto --ancho); afuera, el de SUMO por defecto, como el estudio
            ancho = f' width="{ANCHO:g}"' if (eid in CARRILES_INTERNOS and abs(ANCHO - 3.2) > 1e-9) else ""
            f.write(f'    <edge id="{eid}" from="{a}" to="{b}" numLanes="{carriles}" speed="{VEL}" spreadType="center" '
                    f'shape="{texto(forma)}"{ancho}/>  <!-- {largo(forma):.1f} m de trazado -->\n')
        f.write("</edges>\n")
    conexiones = [c for c in CONEXIONES if not (puente and c[1] == "S1_J")]
    if puente:
        conexiones += PUENTE_CONEXIONES
    # contPos="0": ninguna conexion tiene punto de espera dentro de una esquina (union interna de SUMO); quien debe
    # ceder el paso espera en su linea, al final de la arista que llega a la esquina (en el sitio: en el lado del
    # ovalo, antes de la calzada que cruza). visibility: dentro del ovalo se ve de lado a lado; quien tiene g y no ve
    # a nadie que se acerque sigue sin frenar (con los 4.5 m de SUMO por defecto frenaria siempre antes de la linea).
    with open(rutas["con"], "w", encoding="utf-8", newline="\n") as f:
        f.write(cabeza + "<connections>\n")
        for a, b, i, j in conexiones:
            vis = "" if a in AFUERA or a == "MJ_E1" else f' visibility="{VISIBILIDAD:g}"'
            vel = f' speed="{VEL_GIRO_MIN:g}"' if (a, b, i, j) in lentas else ""
            f.write(f'    <connection from="{a}" to="{b}" fromLane="{i}" toLane="{j}" contPos="0"{vis}{vel}/>\n')
        f.write("</connections>\n")
    return rutas


def tramos_internos(ruta):
    """{(desde, hacia, carril de origen, carril de destino): (nodo, [(tramo interno, largo, velocidad)], direccion)}
    de cada conexion con tramo interno de la red, leido con sumolib."""
    net = sumolib.net.readNet(ruta, withInternal=True)
    res = {}
    for e in net.getEdges():
        if e.isSpecial():
            continue
        for lane in e.getLanes():
            for con in lane.getOutgoing():
                via, tramos = con.getViaLaneID(), []
                while via:
                    vl = net.getLane(via)
                    tramos.append((via, vl.getLength(), vl.getSpeed()))
                    siguientes = vl.getOutgoing()
                    via = siguientes[0].getViaLaneID() if siguientes and siguientes[0].getViaLaneID() else ""
                if tramos:
                    clave = (e.getID(), con.getToLane().getEdge().getID(), lane.getIndex(), con.getToLane().getIndex())
                    res[clave] = (e.getToNode().getID(), tramos, con.getDirection())
    return res


def informe_giros(nombre, antes, despues):
    """red/<nombre>.giros.txt: velocidad y largo de cada tramo interno antes y despues de subir los giros lentos.
    Comprueba que solo cambio la velocidad de los tramos lentos y que ninguno queda por debajo de VEL_GIRO_MIN."""
    assert set(antes) == set(despues), "las conexiones cambiaron al subir la velocidad de los giros"
    lineas = [f"Tramos internos de {nombre}.net.xml (sumolib): velocidad (m/s) y largo (m), antes y despues de llevar a "
              f"{VEL_GIRO_MIN} m/s los giros mas lentos (atributo speed de su conexion).", "",
              f"{'nodo':5s} {'conexion':28s} dir  {'tramo interno':14s} {'largo antes':>11s} {'largo despues':>13s} "
              f"{'vel antes':>9s} {'vel despues':>11s}"]
    cambiados, problemas = 0, []
    for clave in sorted(antes, key=lambda c: (antes[c][0], c)):
        nodo, tramos_a, direccion = antes[clave]
        _, tramos_d, _ = despues[clave]
        for (via, largo_a, vel_a), (via_d, largo_d, vel_d) in zip(tramos_a, tramos_d):
            if via != via_d or abs(largo_a - largo_d) > 1e-6:
                problemas.append(f"{via}: cambio la forma ({largo_a:.2f} -> {largo_d:.2f} m)")
            if vel_d < VEL_GIRO_MIN - 1e-6:
                problemas.append(f"{via}: queda en {vel_d:.2f} m/s")
            if abs(vel_a - vel_d) > 1e-6:
                cambiados += 1
                if vel_a >= VEL_GIRO_MIN:
                    problemas.append(f"{via}: cambio de velocidad sin ser lento ({vel_a:.2f} -> {vel_d:.2f})")
            marca = "  <- subido" if abs(vel_a - vel_d) > 1e-6 else ""
            texto = f"{clave[0]}_{clave[2]} -> {clave[1]}_{clave[3]}"
            lineas.append(f"{nodo:5s} {texto:28s} {direccion:3s}  {via:14s} {largo_a:11.2f} {largo_d:13.2f} "
                          f"{vel_a:9.2f} {vel_d:11.2f}{marca}")
    lineas += ["", f"Tramos internos: {sum(len(t) for _, t, _ in antes.values())}; con la velocidad subida: {cambiados}; "
               f"mas lentos que {VEL_GIRO_MIN} m/s despues: "
               f"{sum(1 for _, t, _ in despues.values() for _, _, v in t if v < VEL_GIRO_MIN - 1e-6)}"]
    if problemas:
        raise SystemExit("informe_giros: " + "; ".join(problemas))
    with open(os.path.join(RED, f"{nombre}.giros.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas) + "\n")
    return cambiados


def netconvert(nombre, rutas):
    salida = os.path.join(RED, f"{nombre}.net.xml")
    orden = NETCONVERT + ["--node-files", rutas["nod"], "--edge-files", rutas["edg"], "--connection-files",
                          rutas["con"], "--output-file", salida]
    r = subprocess.run(orden, capture_output=True, text=True)
    with open(os.path.join(RED, f"{nombre}.netconvert.txt"), "w", encoding="utf-8") as f:
        f.write(" ".join(orden) + "\n\n" + r.stdout + r.stderr)
    if r.returncode:
        raise SystemExit(f"netconvert fallo:\n{r.stdout}{r.stderr}")
    return salida, (r.stdout + r.stderr).strip()


def ajustar_matriz(salida):
    """Agrega a la matriz de cada esquina (<request response> de la red) las cesiones que pide el programa del ovalo:
    en cada fase, el enlace sin prioridad (g u o) cede el paso al que la tiene (G), si SUMO los marca en conflicto.
    netconvert arma la matriz en un solo sentido (la que necesita su programa por defecto) y no la completa aunque
    reciba el programa con --tllogic-files (salidas/prueba_matriz.txt). Solo se agregan bits de "response" entre
    enlaces que ya son conflicto ("foes"); nada mas de la red cambia. Las cesiones dependen de los estados, no de sus
    duraciones: valen para todos los controles. Aqui se miran las fases del plan y las del orden libre
    (plan_ovalo.Plan.cesiones_necesarias, 18.11.2026). Devuelve (cesiones agregadas, de ellas las que pide solo el
    orden libre)."""
    from plan_ovalo import Plan              # noqa: E402 (plan_ovalo importa este modulo)
    plan = Plan(salida, "cede")
    solo_plan = set()
    for _, estado, _ in plan.fases([v for _, v, _ in plan.plan]):
        for i, ci in enumerate(estado):
            for j, cj in enumerate(estado):
                if ci in "go" and cj in "GO" and plan.red.choca(i, j):
                    solo_plan.add((i, j))
    agregar, del_libre = {}, 0
    for i, j in plan.cesiones_necesarias():
        if not plan.red.cede(i, j):
            a, b = plan.red.enlaces[i], plan.red.enlaces[j]
            agregar.setdefault((a["nodo"], a["local"]), set()).add(b["local"])
            del_libre += (i, j) not in solo_plan
    with open(salida, encoding="utf-8") as f:
        lineas = f.read().split("\n")
    nodo = None
    for n, l in enumerate(lineas):
        if l.lstrip().startswith("<junction "):
            nodo = l.split('id="')[1].split('"')[0]
        if "<request index=" in l and nodo is not None:
            k = int(l.split('index="')[1].split('"')[0])
            if (nodo, k) in agregar:
                ini = l.index('response="') + len('response="')
                fin = l.index('"', ini)
                bits = list(l[ini:fin])
                for j in agregar[(nodo, k)]:
                    bits[len(bits) - 1 - j] = "1"
                lineas[n] = l[:ini] + "".join(bits) + l[fin:]
    with open(salida, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas))
    verificado = Plan(salida, "cede")
    faltan = [(i, j) for i, j in verificado.cesiones_necesarias() if not verificado.red.cede(i, j)]
    if faltan:
        raise SystemExit(f"no se pudieron agregar las cesiones {faltan}")
    if verificado.avisos:
        raise SystemExit("enlaces que chocan con prioridad: " + "; ".join(sorted(set(verificado.avisos))))
    return sum(len(v) for v in agregar.values()), del_libre


def largos_red(ruta):
    net = sumolib.net.readNet(ruta, withInternal=True)
    return net, {e.getID(): [l.getLength() for l in e.getLanes()] for e in net.getEdges() if not e.isSpecial()}


# ---------------- salidas auxiliares ----------------
def escribir_e2(nombre, net):
    """Un detector E2 de 75 m que termina en la linea de parada en cada carril de entrada (mismo formato que
    rl_ippo.archivo_e2 y lima/e2_lima_75.add.xml)."""
    lineas = ["<additional>"]
    for eid in ("B_S1", "J_S1", "RN_S1", "RS_S1"):
        for lane in net.getEdge(eid).getLanes():
            lg = lane.getLength()
            lineas.append(f'    <laneAreaDetector id="e2_{lane.getID()}" lane="{lane.getID()}" pos="{max(0.0, lg - E2_LARGO):.2f}" '
                          f'endPos="{lg:.2f}" period="100000" file="nul" friendlyPos="true"/>')
    ruta = os.path.join(RED, f"e2_{nombre}_{E2_LARGO:g}.add.xml")
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas + ["</additional>"]) + "\n")
    return ruta


def resumen(nombre, net, largos, largos_estudio, aristas, avisos, escala, puente):
    """Texto con lo que hay que mirar de la red: largos frente al estudio, espacio de espera adentro y recorrido de
    cada movimiento."""
    lineas = [f"Red {nombre}.net.xml (armar_ovalo.py; escala de la isla {escala}; semaforo E1: {'si' if puente else 'no'})", ""]
    lineas.append("1. Aristas de afuera (las del estudio): carriles y largo de carril (m)")
    for eid in AFUERA:
        e = net.getEdge(eid)
        lg = largos[eid]
        ref = largos_estudio[eid]
        lineas.append(f"   {eid:6s} {e.getLaneNumber()} carriles, {e.getSpeed():.2f} m/s; largo {min(lg):8.2f} a {max(lg):8.2f}"
                      f" (estudio {ref:8.2f}; diferencia {max(abs(x - ref) for x in lg):5.2f})")
    lineas += ["", "2. Aristas de adentro: carriles, largo de carril (m) y vehiculos de 7.5 m que caben detenidos por carril"]
    for eid, (a, b, carriles, osm, que) in CARRILES_INTERNOS.items():
        lg = largos[eid]
        lineas.append(f"   {eid:6s} {a:>4s} -> {b:4s} {carriles} carriles (OSM {osm}); largo {min(lg):5.1f} a {max(lg):5.1f};"
                      f" caben {int(min(lg) // 7.5)} por carril; {que}")
    if puente:
        for eid in PUENTE_ARISTAS:
            lg = largos[eid]
            lineas.append(f"   {eid:6s} {len(lg)} carriles; largo {min(lg):5.1f} a {max(lg):5.1f}; caben {int(min(lg) // 7.5)} "
                          f"por carril")
    lineas += ["", "3. Recorrido de cada movimiento dentro del nudo: desde la linea de parada de afuera hasta el comienzo de "
               "su salida (m; carril del medio de los que usa)"]
    for (o, d), camino in CAMINOS.items():
        camino = list(camino)
        if puente and camino[-1] == "S1_J":
            camino = camino[:-1] + ["MJ_E1", "S1_J"]
        total, i = 0.0, 0
        carril = CARRILES_ENTRADA[(o, d)][len(CARRILES_ENTRADA[(o, d)]) // 2]
        lane = net.getLane(f"{camino[0]}_{carril}")
        for sig in camino[1:]:
            con = [c for c in lane.getOutgoing() if c.getToLane().getEdge().getID() == sig]
            if not con:          # cambio de carril en la arista (con E1: el carril izquierdo solo va a la auxiliar)
                con = [c for l in lane.getEdge().getLanes() for c in l.getOutgoing()
                       if c.getToLane().getEdge().getID() == sig]
            if not con:
                total = float("nan")
                break
            c = con[0]
            via = c.getViaLaneID()
            while via:
                vl = net.getLane(via)
                total += vl.getLength()
                siguientes = vl.getOutgoing()
                via = siguientes[0].getViaLaneID() if siguientes and siguientes[0].getViaLaneID() else ""
            lane = c.getToLane()
            if sig != camino[-1]:
                total += lane.getLength()
        lineas.append(f"   {o}>{d:3s} {' '.join(camino[1:-1]) or '-':30s} {total:6.1f} m")
    lineas += ["", "4. Avisos de netconvert:"] + [f"   {l}" for l in avisos.splitlines() if l.strip()]
    texto_resumen = "\n".join(lineas) + "\n"
    with open(os.path.join(RED, f"{nombre}.resumen.txt"), "w", encoding="utf-8") as f:
        f.write(texto_resumen)
    return texto_resumen


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--puente", action="store_true", help="con el semaforo E1 del puente (variante de sensibilidad)")
    ap.add_argument("--geometria", choices=["medida", "coherente", "osm"], default="medida",
                    help="medida: esquinas a las distancias medidas en Google Maps (por defecto en medido/); "
                         "coherente: la isla de OSM agrandada (--escala); osm: los nodos de OSM tal cual")
    ap.add_argument("--escala", type=float, default=ESCALA_BASE,
                    help="factor de la isla de OSM (geometria coherente): medida de Fabian / medida de OSM")
    ap.add_argument("--ancho", type=float, default=3.2, help="m por carril de las calzadas de ADENTRO (supuesto)")
    ap.add_argument("--ramales", choices=["distancia", "proporcion", "esquina"], default="distancia",
                    help="geometria medida: donde cruzan los ramales de giro (ver leer_medida)")
    ap.add_argument("--nombre", default=None)
    args = ap.parse_args()
    global ANCHO, RAMALES
    ANCHO, RAMALES = args.ancho, args.ramales
    nombre = args.nombre or ("ovalo_estudio" if args.geometria == "medida" else
                             "ovalo_e1" if args.puente else "ovalo")
    os.makedirs(RED, exist_ok=True)
    formas_estudio, largos_estudio = leer_estudio()
    P, isla = leer_osm(args.geometria, args.escala)
    with open(GEO, encoding="utf-8") as f:
        osm = {k: (v["x"], v["y"]) for k, v in json.load(f)["nodos"].items()}
    movidos = {k: dist(P[k], osm[k]) for k in ESQUINAS + ["XN", "XE", "XS", "XO"]}
    # se arma, se mide el largo de cada carril de afuera y se alarga la recta artificial hasta que mida lo del
    # estudio (en la variante con E1, S1_J termina donde termina en la red sin E1: se toma su alargue)
    alargues = {}
    if args.puente:
        base = os.path.join(RED, "ovalo.alargues.json")
        if not os.path.exists(base):
            raise SystemExit("Primero hay que armar la red sin E1 (python -B armar_ovalo.py)")
        with open(base, encoding="utf-8") as f:
            alargues["S1_J"] = json.load(f)["alargues_m"]["S1_J"]
    for vuelta in range(4):
        nodos, aristas = armar_plano(P, formas_estudio, alargues, args.puente)
        rutas = escribir_plano(nombre, nodos, aristas, args.puente)
        salida, avisos = netconvert(nombre, rutas)
        net, largos = largos_red(salida)
        faltan = {eid: largos_estudio[eid] - sum(largos[eid]) / len(largos[eid]) for eid in AFUERA
                  if not (args.puente and eid == "S1_J")}
        if max(abs(v) for v in faltan.values()) < 0.02:
            break
        for eid, v in faltan.items():
            alargues[eid] = alargues.get(eid, 0.0) + v
    # esquinas: los giros que netconvert deja por debajo de VEL_GIRO_MIN por la forma de la esquina suben a ese valor
    # (speed de su conexion) y la red se vuelve a armar con lo mismo; solo cambia la velocidad de esos tramos
    antes = tramos_internos(salida)
    if "B_ML" in CARRILES_INTERNOS:           # la linea de parada de Balboa, donde estaba (ver EXTREMO_BALBOA)
        huecos = [antes[("B_S1", "B_SO", k, k)][1][0][1] for k in range(AFUERA["B_S1"][2])]
        if max(abs(h - HUECO_BALBOA) for h in huecos) > 0.02:
            raise SystemExit(f"la linea de parada de Balboa no quedo donde estaba: {huecos} m de tramo interno entre "
                             f"B_S1 y B_SO (deben ser {HUECO_BALBOA})")
    lentas = sorted(c for c, (_, tramos, _) in antes.items() if min(v for _, _, v in tramos) < VEL_GIRO_MIN)
    if lentas:
        rutas = escribir_plano(nombre, nodos, aristas, args.puente, lentas)
        salida, avisos = netconvert(nombre, rutas)
        net, largos = largos_red(salida)
    subidos = informe_giros(nombre, antes, tramos_internos(salida))
    agregadas, del_libre = ajustar_matriz(salida)
    avisos += (f"\n(armar_ovalo.py) {subidos} tramos internos llevados a {VEL_GIRO_MIN} m/s; cesiones agregadas a la "
               f"matriz de las esquinas: {agregadas} ({del_libre} las pide solo el orden libre)")
    with open(os.path.join(RED, f"{nombre}.netconvert.txt"), "a", encoding="utf-8") as f:
        f.write(f"\narmar_ovalo: {subidos} tramos internos llevados a {VEL_GIRO_MIN} m/s ({nombre}.giros.txt)\n"
                f"armar_ovalo.ajustar_matriz: {agregadas} cesiones agregadas a la matriz de las esquinas "
                f"({del_libre} las pide solo el orden libre)\n")
    e2 = escribir_e2(nombre, net)
    escala_txt = args.escala if args.geometria == "coherente" else f"(no se usa: geometria {args.geometria})"
    texto_resumen = resumen(nombre, net, largos, largos_estudio, aristas, avisos, escala_txt, args.puente)
    extra = [f"5. Geometria del interior: {args.geometria}"
             + (f", escala de la isla {args.escala}" if args.geometria == "coherente" else
                f", ramales '{RAMALES}', {ANCHO:g} m por carril adentro, convergencia UTM "
                f"{math.degrees(convergencia_utm(*LATLON_OVALO)):.3f} grados")
             + ". Distancia (m) de cada punto a su nodo de OSM: " + ", ".join(f"{k} {v:.1f}" for k, v in movidos.items()),
             "   Distancias entre esquinas (m): " + ", ".join(
                 f"{a}-{b} {dist(P[a], P[b]):.2f}" for a, b in (("NO", "NE"), ("NO", "SO"), ("NE", "SE"), ("SO", "SE"))),
             "   Ramales: " + ", ".join(f"{p} a {dist(P[p], P[e]):.2f} m de {e}" for p, e in
                                        (("XN", "NE"), ("XE", "NE"), ("XS", "SO"), ("XO", "SO"))),
             f"6. Carriles de cada entrada (DISPOSICION) y su camino carril a carril hasta la salida: {len(CAMINOS)} "
             f"movimientos, {len(CONEXIONES)} conexiones (enlaces de {TLS})"]
    extra += texto_disposicion(derivar_tablas(DISPOSICION_EN_USO), DISPOSICION_EN_USO)
    with open(os.path.join(RED, f"{nombre}.resumen.txt"), "a", encoding="utf-8") as f:
        f.write("\n".join(extra) + "\n")
    print(texto_resumen + "\n".join(extra))
    print(f"Escrito {salida} ({vuelta + 1} vueltas para igualar los largos) y {e2}")
    with open(os.path.join(RED, f"{nombre}.alargues.json"), "w", encoding="utf-8") as f:
        json.dump({"geometria": args.geometria, "escala": args.escala, "ancho_adentro": ANCHO, "ramales": RAMALES,
                   "puente": args.puente, "alargues_m": alargues,
                   "puntos": {k: [round(P[k][0], 3), round(P[k][1], 3)] for k in ESQUINAS + ["XN", "XE", "XS", "XO"]},
                   "isla": [[round(x, 3), round(y, 3)] for x, y in isla]}, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
