"""
regenerar_demanda.py - UN comando para volver a escribir la demanda del nudo en el Ovalo Vasco (18.11.2026).

Uso (desde lima/ovalo):
  python -B regenerar_demanda.py               # regenera las cuatro demandas y las comprueba
  python -B regenerar_demanda.py --comprobar   # no escribe nada: comprueba lo que hay en las carpetas

Para que sirve: las fracciones de 28 de Julio y de Balboa (lima/demanda.py, DESTINOS_28_DE_JULIO y DESTINOS_BALBOA)
pueden cambiar antes de lanzar. Se editan esas dos lineas y se corre este comando; no hay que tocar nada mas. Despues
hay que rehacer las huellas (LEEME.md): cambian lima/demanda.py y los ocho lima.rou.xml.

Que hace:
  1. corre lima/demanda.py con sus cuatro comandos de siempre (publicada; alta, --factor 1.2; y las dos de la prueba
     de robustez, --reparto RN=1.2,RS=1.2,J=0.8,B=0.8 y --reparto RN=0.8,RS=0.8,J=1.2,B=1.2), en una carpeta temporal:
     demanda.py escribe tambien un lima.sumocfg SIN la valvula, y por eso nunca se apunta a una carpeta de trabajo;
  2. copia los cuatro lima.rou.xml a ovalo/entrada/rutas_estudio/;
  3. escribe el lima.rou.xml de las cuatro carpetas de trabajo, con el camino de cada movimiento por el ovalo
     (preparar_carpetas.py --solo rutas);
  4. comprueba (sale con 1 si algo falla):
     - los carriles de cada grupo de la regla (demanda.GRUPOS) son los de la red (armar_ovalo.DISPOSICION);
     - los movimientos con demanda son movimientos de la red, y cada movimiento de la red tiene demanda;
     - cada archivo tiene un flujo por movimiento y cuarto de hora, con la misma tasa en los cuatro;
     - totales: 4271 veh/h la publicada y las dos de robustez, y 1.2 x 4271 la alta, que ademas es la publicada por
       1.2 flujo por flujo; las de robustez, la publicada por su multiplicador y reescalada al mismo total;
     - el lima.rou.xml de cada carpeta de trabajo es el de entrada/rutas_estudio/ con su camino en via;
  5. escribe ovalo/entrada/rutas_estudio/flujos.txt: la tabla de flujos por movimiento (veh/h) de las cuatro demandas.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))           # lima/ovalo
LIMA = os.path.dirname(AQUI)
RUTAS = os.path.join(AQUI, "entrada", "rutas_estudio")
for _carpeta in (LIMA, AQUI):
    if _carpeta not in sys.path:
        sys.path.insert(0, _carpeta)
import armar_ovalo as ao        # noqa: E402
import demanda                  # noqa: E402  (lima/demanda.py)
import preparar_carpetas        # noqa: E402

FACTOR_ALTA = 1.2
REPARTOS = {"robustez/reducto": {"RN": 1.2, "RS": 1.2, "J": 0.8, "B": 0.8},
            "robustez/transversal": {"RN": 0.8, "RS": 0.8, "J": 1.2, "B": 1.2}}
# caso (carpeta dentro de entrada/rutas_estudio, con /) -> (argumentos de demanda.py, carpeta de trabajo dentro de lima/)
CASOS = {
    "publicada": ([], ""),
    "alta": (["--factor", str(FACTOR_ALTA)], "alta"),
    **{sub: (["--reparto", ",".join(f"{e}={m}" for e, m in mult.items())], os.path.join(*sub.split("/")))
       for sub, mult in REPARTOS.items()},
}


def carpeta_rutas(caso):
    return os.path.join(RUTAS, *caso.split("/"))
NOMBRES = {"RN": "Reducto norte", "RS": "Reducto sur", "J": "28 de Julio", "B": "Balboa", "L": "Larco"}
SALIDAS = {"L": "Larco", "J": "el puente", "RN": "Reducto norte", "RS": "Reducto sur"}
ORDEN = [("RN", "RS"), ("RN", "L"), ("RN", "J"), ("RS", "RN"), ("RS", "J"), ("RS", "L"),
         ("J", "L"), ("J", "RN"), ("J", "RS"), ("B", "J"), ("B", "RS"), ("B", "RN"), ("B", "L")]
FLUJO = re.compile(r'<flow id="p(\d)_([A-Z]+)_([A-Z]+)" type="auto" from="([^"]+)" to="([^"]+)"(?: via="[^"]*")? begin="(\d+)" '
                   r'end="(\d+)" period="exp\(([0-9.]+)\)" departLane="best"/>')


def leer(ruta):
    """{(entrada, salida): [veh/h en cada cuarto de hora]} y las lineas de flujo de un lima.rou.xml."""
    tabla, lineas = {}, []
    with open(ruta, encoding="utf-8") as f:
        for l in f:
            if "<flow " not in l:
                continue
            m = FLUJO.search(l)
            if not m:
                raise SystemExit(f"{ruta}: flujo que no se entiende: {l.strip()}")
            p, o, d, desde, hacia, ini, fin, tasa = m.groups()
            assert desde == demanda.ENTRADA[o] and hacia == demanda.SALIDA[d], l
            assert int(ini) == 900 * (int(p) - 1) and int(fin) == 900 * int(p), l
            tabla.setdefault((o, d), [0.0] * demanda.PERIODOS)[int(p) - 1] += float(tasa) * 3600.0
            lineas.append(l.strip())
    return tabla, lineas


def carriles_de_la_red():
    """Problemas entre la regla de la demanda (GRUPOS y DESTINOS) y los carriles de la red (DISPOSICION)."""
    problemas, por_entrada = [], {}
    for grupo, (e, carriles, _) in demanda.GRUPOS.items():
        usados = {k for k, destinos in enumerate(ao.DISPOSICION[e]) if set(destinos) & set(demanda.DESTINOS[grupo])}
        if len(usados) != carriles:
            problemas.append(f"demanda.GRUPOS[{grupo}] dice {carriles} carriles y la red usa {len(usados)} ({sorted(usados)})")
        if usados & por_entrada.get(e, set()):
            problemas.append(f"el grupo {grupo} comparte carriles con otro grupo de {e}")
        por_entrada.setdefault(e, set()).update(usados)
    for e, usados in por_entrada.items():
        if usados != set(range(len(ao.DISPOSICION[e]))):
            problemas.append(f"{e}: los grupos cubren los carriles {sorted(usados)} y la entrada tiene {len(ao.DISPOSICION[e])}")
    con_demanda = {(e, d) for (e, d), q in demanda.reparto_supuesto().items() if q > 0}
    if con_demanda - set(ao.CAMINOS):
        problemas.append(f"movimientos con demanda que la red no tiene: {sorted(con_demanda - set(ao.CAMINOS))}")
    if set(ao.CAMINOS) - con_demanda:
        problemas.append(f"movimientos de la red sin demanda: {sorted(set(ao.CAMINOS) - con_demanda)}")
    return problemas


def regenerar():
    tmp = tempfile.mkdtemp(prefix="demanda_ovalo_")
    try:
        for caso, (argumentos, _) in CASOS.items():
            carpeta = os.path.join(tmp, *caso.split("/"))
            r = subprocess.run([sys.executable, "-B", os.path.join(LIMA, "demanda.py")] + argumentos + ["--carpeta", carpeta],
                               cwd=LIMA, capture_output=True, text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            if r.returncode:
                raise SystemExit(f"demanda.py {' '.join(argumentos)}:\n{r.stdout}{r.stderr}")
            os.makedirs(carpeta_rutas(caso), exist_ok=True)
            shutil.copyfile(os.path.join(carpeta, "lima.rou.xml"), os.path.join(carpeta_rutas(caso), "lima.rou.xml"))
            print(f"demanda.py {' '.join(argumentos) or '(publicada)'} -> entrada/rutas_estudio/{caso}/lima.rou.xml")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    preparar_carpetas.main(["rutas"])


def comprobar():
    problemas = carriles_de_la_red()
    regla = demanda.reparto_supuesto()
    tablas = {}
    for caso, (_, sub) in CASOS.items():
        tabla, lineas = leer(os.path.join(carpeta_rutas(caso), "lima.rou.xml"))
        tabla_trabajo, lineas_trabajo = leer(os.path.join(LIMA, sub, "lima.rou.xml"))
        sin_via = [re.sub(r' via="[^"]*"', "", l) for l in lineas_trabajo]
        if sin_via != lineas or not all(' via="' in l for l in lineas_trabajo):
            problemas.append(f"{caso}: el lima.rou.xml de la carpeta de trabajo no es el de entrada/rutas_estudio con su camino")
        if set(tabla) != set(ao.CAMINOS) or len(lineas) != demanda.PERIODOS * len(ao.CAMINOS):
            problemas.append(f"{caso}: {len(lineas)} flujos de {len(tabla)} movimientos; la red tiene {len(ao.CAMINOS)} movimientos")
        if any(max(q) - min(q) > 1e-9 for q in tabla.values()):
            problemas.append(f"{caso}: la tasa no es la misma en los cuatro cuartos de hora")
        tablas[caso] = {m: sum(q) / demanda.PERIODOS for m, q in tabla.items()}
    total = {caso: sum(t.values()) for caso, t in tablas.items()}
    # una tasa se escribe con 6 decimales en veh/s: hasta 0.0018 veh/h de redondeo por flujo
    for caso, esperado in (("publicada", demanda.TOTAL_PUBLICADO), ("alta", FACTOR_ALTA * demanda.TOTAL_PUBLICADO),
                           *((sub, demanda.TOTAL_PUBLICADO) for sub in REPARTOS)):
        if abs(total[caso] - esperado) > 0.05:
            problemas.append(f"{caso}: total {total[caso]:.2f} veh/h; debia ser {esperado:.2f}")
    for m, q in regla.items():
        if q > 0 and abs(tablas["publicada"].get(m, 0.0) - q) > 0.002:
            problemas.append(f"publicada, {m}: {tablas['publicada'].get(m, 0.0):.3f} veh/h; la regla da {q:.3f}")
        if q > 0 and abs(tablas["alta"].get(m, 0.0) - FACTOR_ALTA * q) > 0.002:
            problemas.append(f"alta, {m}: {tablas['alta'].get(m, 0.0):.3f} veh/h; debia ser {FACTOR_ALTA * q:.3f}")
    for sub, mult in REPARTOS.items():
        escala = demanda.TOTAL_PUBLICADO / sum(q * mult[e] for (e, _), q in regla.items())
        for (e, d), q in regla.items():
            if q > 0 and abs(tablas[sub].get((e, d), 0.0) - q * mult[e] * escala) > 0.002:
                problemas.append(f"{sub}, {(e, d)}: {tablas[sub].get((e, d), 0.0):.3f} veh/h; debia ser {q * mult[e] * escala:.3f}")
    return problemas, tablas, total


def texto_tabla(tablas, total):
    unidades = sum(c * v for _, c, v in demanda.GRUPOS.values())
    casos = list(CASOS)
    out = ["Demanda del nudo en el Ovalo Vasco: flujos por movimiento (veh/h), leidos de ovalo/entrada/rutas_estudio/",
           "(regenerar_demanda.py). Regla: el total publicado de 4271 veh/h repartido en proporcion a carriles por",
           "segundos de verde medidos de cada grupo (lima/demanda.py, GRUPOS) y, dentro de cada grupo, por destino.", "",
           "Grupos (carriles x verde medido): " + "; ".join(
               f"{g} {c} x {v} = {c * v}" for g, (_, c, v) in demanda.GRUPOS.items()) + f"; suma {unidades}",
           "Destinos: " + "; ".join(f"{g}: " + ", ".join(f"{SALIDAS[d]} {f:.2f}" for d, f in demanda.DESTINOS[g].items())
                                    for g in demanda.GRUPOS), "",
           f"{'Entrada':14s} {'Hacia':14s} " + " ".join(f"{c:>22s}" for c in casos)]
    movimientos = [m for m in ORDEN if m in tablas["publicada"]] + sorted(set(tablas["publicada"]) - set(ORDEN))
    for (e, d) in movimientos:
        out.append(f"{NOMBRES[e]:14s} {SALIDAS[d]:14s} " + " ".join(f"{tablas[c].get((e, d), 0.0):22.1f}" for c in casos))
    for e in ("RN", "RS", "J", "B"):
        out.append(f"{'Entra por':14s} {NOMBRES[e]:14s} " + " ".join(
            f"{sum(q for (o, _), q in tablas[c].items() if o == e):22.1f}" for c in casos))
    for d in ("L", "J", "RN", "RS"):
        out.append(f"{'Sale hacia':14s} {SALIDAS[d]:14s} " + " ".join(
            f"{sum(q for (_, s), q in tablas[c].items() if s == d):22.1f}" for c in casos))
    out.append(f"{'Todo el nudo':29s} " + " ".join(f"{total[c]:22.2f}" for c in casos))
    return "\n".join(out) + "\n"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    solo_comprobar = "--comprobar" in sys.argv[1:]
    previos = carriles_de_la_red()
    if previos:
        raise SystemExit("regenerar_demanda.py: la regla de la demanda no cuadra con la red: " + "; ".join(previos))
    if not solo_comprobar:
        regenerar()
    problemas, tablas, total = comprobar()
    texto = texto_tabla(tablas, total)
    if not solo_comprobar:
        with open(os.path.join(RUTAS, "flujos.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
    print(texto)
    if problemas:
        print("FALLAS: " + "; ".join(problemas))
        return 1
    print("Comprobaciones de la demanda: todas bien." + ("" if solo_comprobar else
          " Falta rehacer las huellas (cambian lima/demanda.py y los ocho lima.rou.xml)."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
