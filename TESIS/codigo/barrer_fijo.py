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
              "corredor": {"verde": 25, "off2": 25}, "red": {"verde": 20, "off2": 23}}


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


def escribir_add(plantilla, ruta, verde, offsets):
    """Copia el .add.xml del escenario cambiando el verde de las fases verdes y el offset de cada semaforo."""
    arbol = copy.deepcopy(plantilla)
    for i, tl in enumerate(arbol.getroot().findall("tlLogic")):
        tl.set("offset", str(offsets[i]))
        for fase in tl.findall("phase"):
            estado = fase.get("state")
            if ("G" in estado or "g" in estado) and "y" not in estado:
                fase.set("duration", str(verde))
    arbol.write(ruta)


def configs_corredor(esc, tmp):
    """Verde x offset del segundo cruce (y del tercero en red)."""
    plantilla = ET.parse(f"{esc}.add.xml")
    verdes = [15, 20, 25, 30, 35] if esc == "corredor" else [15, 20, 25, 30]
    for verde in verdes:
        ciclo = 2 * (verde + 3)
        for off2 in sorted(set(range(0, 45, 5)) | {DESPLEGADO[esc]["off2"]}):
            if off2 >= ciclo:
                continue
            terceros = [None] if esc == "corredor" else sorted({0, off2, (2 * off2) % ciclo})
            for off3 in terceros:
                offsets = [0, off2] + ([off3] if off3 is not None else [])
                ruta = os.path.join(tmp, f"{esc}_v{verde}_o{'_'.join(map(str, offsets))}.add.xml")
                if not os.path.exists(ruta):
                    escribir_add(plantilla, ruta, verde, offsets)
                yield {"verde": verde, "izquierda": "", "offsets": "/".join(map(str, offsets))}, \
                    ["--additional-files", ruta]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("escenario", choices=["cruce", "cruce2", "corredor", "red"])
    ap.add_argument("--semillas", default="1001-1003")
    ap.add_argument("--tmp", default="tmp_barrido")
    args = ap.parse_args()
    esc = args.escenario
    semillas = rango(args.semillas)
    os.makedirs(args.tmp, exist_ok=True)
    cfg = f"{esc}.sumocfg"
    configs = configs_cruce(esc, args.tmp) if esc in ("cruce", "cruce2") else configs_corredor(esc, args.tmp)

    filas = []
    for params, extra in configs:
        res = [correr_sumo(cfg, extra, s, os.path.join(args.tmp, f"tripinfo_{esc}.xml")) for s in semillas]
        fila = dict(params)
        for m in ("timeloss_prom", "espera_prom", "paradas_prom", "throughput", "co2_prom"):
            vals = [float(r[m]) for r in res]
            fila[m] = round(statistics.mean(vals), 2)
        fila["timeloss_sd"] = round(statistics.stdev([float(r["timeloss_prom"]) for r in res]), 2) if len(res) > 1 else 0
        fila["semillas"] = args.semillas
        filas.append(fila)
        print(f"verde={fila['verde']:>2} izq={fila['izquierda']!s:>2} "
              f"offsets={fila['offsets']:<10} timeLoss={fila['timeloss_prom']:6.2f} "
              f"espera={fila['espera_prom']:6.2f}", flush=True)

    filas.sort(key=lambda f: f["timeloss_prom"])
    salida = f"barrido_{esc}.csv"
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
