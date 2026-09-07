"""
barrer_fijo.py - Barrido del programa de tiempo fijo de un escenario para elegir el
baseline por la metrica primaria (timeLoss promedio por vehiculo), no por espera detenida.

Uso:
  python barrer_fijo.py cruce      [--semillas 1001-1003] [--tmp carpeta]
  python barrer_fijo.py cruce2
  python barrer_fijo.py corredor
  python barrer_fijo.py red

cruce y cruce2: se regenera la red con netconvert para cada verde (y cada verde de giro
protegido en cruce2), igual que hace build_net.bat.
corredor y red: se reescribe el programa fijo del .add.xml con cada verde y cada offset.
Las corridas son sumo puro (sin TraCI). Salida: barrido_<esc>.csv con el promedio de
cada configuracion sobre las semillas, ordenado por timeLoss.
"""
import os
import csv
import copy
import argparse
import statistics
import subprocess
import xml.etree.ElementTree as ET

import comun

SILENCIO = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}


def rango(texto):
    """'1001-1003' -> [1001, 1002, 1003]; '42' -> [42]"""
    if "-" in texto:
        a, b = texto.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(texto)]


def correr_sumo(cfg, extra, seed, tripinfo):
    cmd = ["sumo", "-c", cfg, "--seed", str(seed), "--tripinfo-output", tripinfo,
           "--tripinfo-output.write-unfinished", "true", "--device.emissions.probability", "1",
           "--no-step-log", "true", "--no-warnings", "true"] + extra
    subprocess.run(cmd, check=True, **SILENCIO)
    return comun.leer_tripinfo(tripinfo)


DESPLEGADO = {"cruce": {"verde": 25}, "cruce2": {"verde": 20, "izquierda": 6},
              "corredor": {"verde": 20, "verde_tr": 10, "off2": 15},     # asimetrico desde 06.09
              "red": {"verde": 25, "verde_tr": 15, "off2": 23},          # asimetrico desde 06.09
              "corredor_alta": {"verde": 25, "verde_tr": 15, "off2": 25}}
# Indice (en el .add.xml) de la fase verde que sirve a la avenida; el resto de fases verdes
# son transversales. Verificado en los .net.xml: corredor fase 2, red fase 0.
FASE_AVENIDA = {"corredor": 2, "red": 0, "corredor_alta": 2}


def configs_cruce(esc, tmp):
    """Un net por verde (y por verde de giro en cruce2). La malla incluye la configuracion desplegada."""
    for verde in sorted(set(range(15, 43, 3)) | {DESPLEGADO[esc]["verde"]}):
        for izq in ([None] if esc == "cruce" else [6, 8, 10, 12]):
            nombre = f"{esc}_v{verde}" + (f"_l{izq}" if izq else "")
            net = os.path.join(tmp, nombre + ".net.xml")
            if not os.path.exists(net):
                cmd = ["netconvert", "--node-files", f"{esc}.nod.xml", "--edge-files", f"{esc}.edg.xml",
                       "--output-file", net, "--no-turnarounds", "--tls.green.time", str(verde)]
                if esc == "cruce2":
                    cmd += ["--connection-files", "cruce2.con.xml", "--tls.left-green.time", str(izq)]
                subprocess.run(cmd, check=True, **SILENCIO)
            yield {"verde": verde, "izquierda": izq if izq else "", "offsets": ""}, ["--net-file", net]


def configs_cruce_asimetrico(esc, tmp):
    """Solo cruce: reparto asimetrico N-S x E-O escrito como programa 'fijo' en un .add.xml,
    porque netconvert solo admite un verde comun. 'verde' es el N-S y 'verde_transversal' el
    E-O (los dos ejes son principales, cada uno en una mitad de la hora). Incluye el 25/25."""
    verdes = (15, 20, 25, 30, 35, 40)
    for v_ns in verdes:
        for v_eo in verdes:
            ruta = os.path.join(tmp, f"{esc}_ns{v_ns}_eo{v_eo}.add.xml")
            if not os.path.exists(ruta):
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write('<additional>\n  <tlLogic id="semaforo_C" type="static" programID="fijo"'
                            ' offset="0">\n'
                            f'    <phase duration="{v_ns}" state="GGgrrrGGgrrr"/>\n'
                            '    <phase duration="3"  state="yyyrrryyyrrr"/>\n'
                            f'    <phase duration="{v_eo}" state="rrrGGgrrrGGg"/>\n'
                            '    <phase duration="3"  state="rrryyyrrryyy"/>\n'
                            '  </tlLogic>\n</additional>\n')
            yield ({"verde": v_ns, "izquierda": "", "verde_transversal": v_eo, "offsets": ""},
                   ["--additional-files", ruta])


def escribir_add(plantilla, ruta, verde_av, verde_tr, offsets, fase_av):
    """Copia el .add.xml del escenario con el verde de la avenida, el de las transversales y el
    offset de cada semaforo (fase_av = indice de la fase verde de la avenida en el programa)."""
    arbol = copy.deepcopy(plantilla)
    for i, tl in enumerate(arbol.getroot().findall("tlLogic")):
        tl.set("offset", str(offsets[i]))
        for k, fase in enumerate(tl.findall("phase")):
            estado = fase.get("state")
            if ("G" in estado or "g" in estado) and "y" not in estado:
                fase.set("duration", str(verde_av if k == fase_av else verde_tr))
    arbol.write(ruta)


def configs_corredor(esc, tmp):
    """Verde x offset del segundo cruce (y del tercero en red). En corredor_alta el reparto de
    verde es asimetrico (avenida x transversal) porque la avenida lleva casi toda la demanda."""
    plantilla = ET.parse(f"{esc}.add.xml")
    fase_av = FASE_AVENIDA[esc]
    # Reparto asimetrico avenida x transversal en los tres corredores: la avenida lleva mucha
    # mas demanda que las transversales, asi que un verde comun no es el mejor fijo posible.
    # La malla incluye siempre la configuracion desplegada.
    malla = {"corredor": ((20, 25, 30, 35), (10, 15, 20, 25)),
             "red": ((15, 20, 25, 30), (10, 15, 20)),
             "corredor_alta": ((25, 30, 35, 40), (10, 15, 20, 25))}
    avenidas, transversales = malla[esc]
    d = DESPLEGADO[esc]
    pares = sorted({(av, tr) for av in avenidas for tr in transversales}
                   | {(d["verde"], d.get("verde_tr", d["verde"]))})
    if esc == "corredor_alta":
        offsets2 = [0, 10, 20, 25, 30]
    else:
        offsets2 = sorted(set(range(0, 45, 5)) | {d["off2"]})
    for verde_av, verde_tr in pares:
        ciclo = verde_av + verde_tr + 6
        for off2 in offsets2:
            if off2 >= ciclo:
                continue
            terceros = [None] if esc != "red" else sorted({0, off2, (2 * off2) % ciclo})
            for off3 in terceros:
                offsets = [0, off2] + ([off3] if off3 is not None else [])
                nombre = f"{esc}_v{verde_av}_t{verde_tr}_o{'_'.join(map(str, offsets))}.add.xml"
                ruta = os.path.join(tmp, nombre)
                if not os.path.exists(ruta):
                    escribir_add(plantilla, ruta, verde_av, verde_tr, offsets, fase_av)
                yield {"verde": verde_av, "izquierda": "", "verde_transversal": verde_tr,
                       "offsets": "/".join(map(str, offsets))}, ["--additional-files", ruta]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("escenario", choices=["cruce", "cruce2", "corredor", "red", "corredor_alta"])
    ap.add_argument("--semillas", default="1001-1003")
    ap.add_argument("--tmp", default="tmp_barrido")
    ap.add_argument("--asimetrico", action="store_true",
                    help="cruce: reparto N-S x E-O por .add.xml (salida barrido_cruce_asimetrico.csv)")
    args = ap.parse_args()
    esc = args.escenario
    semillas = rango(args.semillas)
    os.makedirs(args.tmp, exist_ok=True)
    cfg = f"{esc}.sumocfg"
    if esc not in ("cruce", "cruce2"):
        configs = configs_corredor(esc, args.tmp)
    elif args.asimetrico:
        configs = configs_cruce_asimetrico(esc, args.tmp)
    else:
        configs = configs_cruce(esc, args.tmp)

    filas = []
    for params, extra in configs:
        res = [correr_sumo(cfg, extra, s, os.path.join(args.tmp, f"tripinfo_{esc}.xml")) for s in semillas]
        fila = dict(params)
        for m in ("timeloss_prom", "espera_prom", "paradas_prom", "throughput", "co2_prom"):
            vals = [float(r[m]) for r in res]
            fila[m] = round(statistics.mean(vals), 2)
        retrasos = [float(r["timeloss_prom"]) for r in res]
        fila["timeloss_sd"] = round(statistics.stdev(retrasos), 2) if len(res) > 1 else 0
        fila["semillas"] = args.semillas
        filas.append(fila)
        print(f"verde={fila['verde']:>2} izq={fila['izquierda']!s:>2} "
              f"offsets={fila['offsets']:<10} timeLoss={fila['timeloss_prom']:6.2f} "
              f"espera={fila['espera_prom']:6.2f}", flush=True)

    filas.sort(key=lambda f: f["timeloss_prom"])
    salida = f"barrido_{esc}{'_asimetrico' if args.asimetrico else ''}.csv"
    with open(salida, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print(f"\nMejores 5 por timeLoss ({salida}):")
    for fila in filas[:5]:
        print(f"  verde={fila['verde']} izq={fila['izquierda']} offsets={fila['offsets']} "
              f"timeLoss={fila['timeloss_prom']} (sd {fila['timeloss_sd']}) espera={fila['espera_prom']}")


if __name__ == "__main__":
    main()
