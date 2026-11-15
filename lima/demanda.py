"""
demanda.py - Escribe la demanda del caso Lima: lima.rou.xml (llegadas aleatorias) y lima.sumocfg.

Uso (desde demo_rl/lima):  python demanda.py [--factor 1.0] [--regulares]
Fuente de la demanda, en este orden:
1. conteo.csv, si existe: el conteo de campo. Columnas: entrada, salida, periodo, vehiculos, minutos.
   entrada: RN (Reducto desde el norte), RS (Reducto desde el sur), B (Balboa) o J (28 de Julio desde el puente);
   salida: L (hacia Larco), J (hacia el puente), RN (Reducto hacia el norte) o RS (Reducto hacia el sur);
   periodo: 1, 2, 3 o 4 (cuartos de hora de la hora punta); vehiculos: los contados en `minutos` minutos.
   La tasa de cada movimiento y periodo es vehiculos * 60 / minutos (veh/h).
2. Si no existe: el total publicado, 4271 veh/h en la hora punta de la tarde (Plan de Movilidad Urbana de
   Miraflores 2017-2020, pags. 30-31, fuente P.U.D. Miraflores), repartido entre los movimientos en proporcion a
   los carriles y al verde que el plan actual le da a cada uno (GRUPOS) y, dentro de cada grupo, con destinos
   supuestos (DESTINOS). No es un aforo: es un supuesto declarado.

Cada movimiento es un flujo por periodo de 15 min, con llegadas de Poisson (period="exp(tasa)"), como en el segundo
estudio; --regulares las escribe a intervalos iguales.

Vehiculos (--mezcla): "lima" (por defecto) usa la mezcla de vehiculos de Lima del segundo estudio (autos, motos,
combis, microbuses y buses; plan3/demanda_estocastica.py: JICA 2013 sin camiones y flota de la ATU 2021) o, si
existe mezcla.csv (columnas tipo y vehiculos, con tipo = auto, moto, combi, micro o bus), la mezcla contada en el
sitio. "ninguna" deja un solo tipo, el auto de los demas casos. Las tasas son vehiculos reales por hora: no se
convierten a vehiculos equivalentes.
"""
import argparse
import csv
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ENTRADA = {"RN": "RN_S1", "RS": "RS_S1", "B": "B_S1", "J": "J_S1"}
SALIDA = {"L": "S1_L", "J": "S1_J", "RN": "S1_RN", "RS": "S1_RS"}
PERIODOS = 4                   # cuartos de hora
CONDUCTA = ""                  # atributos extra de cada tipo de vehiculo (como cede el paso dentro del nudo)
PROCESO = ""                   # opciones extra de <processing> del .sumocfg
TOTAL_PUBLICADO = 4271         # veh/h, interseccion 28 de Julio / Reducto, punta de la tarde
# Sin conteo de campo, el total publicado se reparte en proporcion a lo que el plan actual le da a cada grupo de
# movimientos: carriles por segundos de verde medidos en el sitio (13.11.2026). Es el supuesto mas favorable para el
# plan actual: con el, todos los grupos quedan igual de cargados. grupo: (entrada, carriles, verde medido en s)
GRUPOS = {
    "RN_frente": ("RN", 3, 38), "RN_izquierda": ("RN", 1, 18),
    "RS_frente": ("RS", 3, 40), "RS_izquierda": ("RS", 2, 18),
    "J": ("J", 3, 38), "B": ("B", 3, 40),
}
# dentro de cada grupo, hacia donde van los vehiculos: lo que Fabian estimo en el sitio (13.11.2026: de Balboa, 1 de
# cada 10 sube hacia Reducto norte; de 28 de Julio, 2 o mas de cada 10 giran hacia Reducto sur) y, el resto, supuesto
DESTINOS = {
    "RN_frente": {"RS": 0.90, "L": 0.10}, "RN_izquierda": {"J": 1.00},
    "RS_frente": {"RN": 0.80, "J": 0.20}, "RS_izquierda": {"L": 1.00},
    "J": {"L": 0.65, "RN": 0.15, "RS": 0.20},
    "B": {"J": 0.55, "RS": 0.35, "RN": 0.10},          # sin el giro hacia Larco (armar_red.py)
}


def reparto_supuesto():
    """{(entrada, salida): veh/h} del total publicado, repartido por carriles y verde del plan actual."""
    unidades = sum(carriles * verde for _, carriles, verde in GRUPOS.values())
    res = {}
    for grupo, (entrada, carriles, verde) in GRUPOS.items():
        q = TOTAL_PUBLICADO * carriles * verde / unidades
        for salida, fraccion in DESTINOS[grupo].items():
            res[(entrada, salida)] = res.get((entrada, salida), 0.0) + q * fraccion
    return res


def tasas():
    """{(entrada, salida): [veh/h en cada cuarto de hora]} y el nombre de la fuente."""
    ruta = os.path.join(AQUI, "conteo.csv")
    if os.path.exists(ruta):
        res = {}
        with open(ruta, encoding="utf-8-sig", newline="") as f:
            for fila in csv.DictReader(f):
                clave = (fila["entrada"].strip().upper(), fila["salida"].strip().upper())
                assert clave[0] in ENTRADA and clave[1] in SALIDA and clave[0] != clave[1], clave
                p = int(fila["periodo"])
                assert 1 <= p <= PERIODOS, fila
                res.setdefault(clave, [0.0] * PERIODOS)[p - 1] += float(fila["vehiculos"]) * 60.0 / float(fila["minutos"])
        return res, "conteo de campo (conteo.csv)"
    res = {clave: [q] * PERIODOS for clave, q in reparto_supuesto().items()}
    return res, "total publicado (4271 veh/h) repartido por carriles y verde del plan actual; giros supuestos"


def tipos(mezcla):
    """Lineas del vType "auto" (o de su vTypeDistribution con la mezcla) y el nombre de la fuente de la mezcla."""
    if mezcla == "ninguna":
        return [f'    <vType id="auto" accel="2.6" decel="4.5" sigma="0.5" length="5" minGap="2.5" maxSpeed="13.89" {CONDUCTA}/>'], \
            "un solo tipo de vehiculo"
    sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "plan3"))
    sys.path.insert(0, os.path.dirname(AQUI))
    import demanda_estocastica as de            # mismas clases de vehiculo que la mezcla del segundo estudio
    ruta = os.path.join(AQUI, "mezcla.csv")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8-sig", newline="") as f:
            cuenta = {fila["tipo"].strip().lower(): float(fila["vehiculos"]) for fila in csv.DictReader(f)}
        assert set(cuenta) <= set(de.TIPOS), f"tipos desconocidos en mezcla.csv: {set(cuenta) - set(de.TIPOS)}"
        total = sum(cuenta.values())
        p, fuente = {c: n / total for c, n in cuenta.items() if n > 0}, "mezcla contada en el sitio (mezcla.csv)"
    else:
        p, fuente = de.composicion(), "mezcla de Lima del segundo estudio (JICA 2013 y flota ATU 2021)"
    lineas = ['    <vTypeDistribution id="auto">']
    lineas += [f'        <vType id="lima_{c}" {de.TIPOS[c]} {de.COMUNES} {CONDUCTA} probability="{q:.6f}"/>'
               for c, q in p.items()]
    return lineas + ["    </vTypeDistribution>"], fuente


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--factor", type=float, default=1.0, help="multiplica toda la demanda")
    ap.add_argument("--regulares", action="store_true", help="llegadas a intervalos iguales en vez de aleatorias")
    ap.add_argument("--mezcla", choices=["lima", "ninguna"], default="lima")
    ap.add_argument("--prefijo", default="lima")
    ap.add_argument("--carpeta", default=AQUI, help="donde escribir (otro nivel de demanda: alta/, con --factor)")
    ap.add_argument("--reparto", default=None, help="(prueba de robustez) otro reparto entre entradas con el mismo "
                    "total: multiplicadores por entrada, p. ej. RN=1.2,RS=1.2,J=0.8,B=0.8; despues se reescala todo")
    args = ap.parse_args()
    os.makedirs(args.carpeta, exist_ok=True)
    tabla, fuente = tasas()
    if args.reparto:
        mult = {k.strip().upper(): float(v) for k, v in (par.split("=") for par in args.reparto.split(","))}
        assert set(mult) <= set(ENTRADA), mult
        antes = sum(sum(q) for q in tabla.values())
        tabla = {(e, s): [x * mult.get(e, 1.0) for x in q] for (e, s), q in tabla.items()}
        escala = antes / sum(sum(q) for q in tabla.values())          # el total no cambia
        tabla = {clave: [x * escala for x in q] for clave, q in tabla.items()}
        fuente += f"; reparto entre entradas cambiado ({args.reparto}) con el mismo total"
    lineas_tipo, fuente_mezcla = tipos(args.mezcla)
    lineas = ["<routes>", f"    <!-- Demanda del caso Lima. Fuente: {fuente}; factor {args.factor}; vehiculos: "
              f"{fuente_mezcla}. Generado por demanda.py -->"] + lineas_tipo
    total = [0.0] * PERIODOS
    for p in range(PERIODOS):
        for (entrada, salida), q in sorted(tabla.items()):
            tasa = q[p] * args.factor
            if tasa <= 0:
                continue
            total[p] += tasa
            llegada = f'vehsPerHour="{tasa:.2f}"' if args.regulares else f'period="exp({tasa / 3600:.6f})"'
            lineas.append(f'    <flow id="p{p + 1}_{entrada}_{salida}" type="auto" from="{ENTRADA[entrada]}" '
                          f'to="{SALIDA[salida]}" begin="{900 * p}" end="{900 * (p + 1)}" {llegada} departLane="best"/>')
    lineas.append("</routes>")
    with open(os.path.join(args.carpeta, f"{args.prefijo}.rou.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas) + "\n")
    with open(os.path.join(args.carpeta, f"{args.prefijo}.sumocfg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"""<configuration>
    <input>
        <net-file value="lima.net.xml"/>
        <route-files value="{args.prefijo}.rou.xml"/>
        <additional-files value="lima.add.xml"/>
    </input>
    <time>
        <begin value="0"/>
        <step-length value="1"/>
    </time>
    <processing>
        <time-to-teleport value="-1"/>{PROCESO}
    </processing>
    <report>
        <no-step-log value="true"/>
        <no-warnings value="true"/>
    </report>
</configuration>
""")
    print(f"Fuente: {fuente}")
    print("Demanda por cuarto de hora (veh/h):", ", ".join(f"{t:.0f}" for t in total),
          f"| media {sum(total) / PERIODOS:.0f} veh/h")
    por_entrada = {}
    for (entrada, salida), q in tabla.items():
        por_entrada[entrada] = por_entrada.get(entrada, 0.0) + sum(q) / PERIODOS * args.factor
    print("Por entrada (veh/h):", ", ".join(f"{k} {v:.0f}" for k, v in sorted(por_entrada.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
