"""
comun.py - Funciones compartidas por rl_semaforo.py, rl_corredor.py y evaluar.py:
lectura de las metricas U3 del tripinfo, programa actuado de referencia, CSV de
resultados con sus columnas y series de cola por minuto.
"""
import os
import csv
import sys
import xml.etree.ElementTree as ET

try:
    import sumolib
except ImportError:
    if "SUMO_HOME" in os.environ:
        sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
        import sumolib
    else:
        sys.exit("No encuentro sumolib. Define la variable SUMO_HOME o ejecuta: pip install traci sumolib")

FIN_HORA = 3600     # la demanda termina a los 3600 s; el throughput cuenta los que llegaron antes

# Columnas del CSV de resultados por episodio (una fila por corrida o por episodio)
CAMPOS = ["modo", "episodio", "semilla", "epsilon", "vehiculos",
          "espera_prom", "timeloss_prom", "cola_prom", "cola_max",
          "recompensa", "recompensa_decision", "decisiones", "cambios_fase",
          "paradas_prom", "throughput", "co2_prom", "nox_prom",
          "estados_q", "dq_max", "eval_timeloss", "eval_espera"]


# ---------------- Metricas del tripinfo ----------------
def leer_tripinfo(archivo):
    """Metricas por vehiculo promediadas sobre el episodio.
    espera_prom   : s detenido por vehiculo (waitingTime, velocidad <= 0.1 m/s)
    timeloss_prom : s de retraso por vehiculo respecto a la velocidad deseada (timeLoss)
    paradas_prom  : detenciones por vehiculo (waitingCount)
    throughput    : vehiculos que terminaron su viaje antes de los 3600 s
    co2_prom      : g de CO2 por vehiculo; nox_prom: mg de NOx por vehiculo
                    (requieren --device.emissions.probability 1; clase HBEFA3/PC_G_EU4 por defecto)"""
    viajes = ET.parse(archivo).getroot().findall("tripinfo")
    n = max(1, len(viajes))
    espera = sum(float(v.get("waitingTime")) for v in viajes) / n
    perdida = sum(float(v.get("timeLoss")) for v in viajes) / n
    paradas = sum(int(v.get("waitingCount", 0)) for v in viajes) / n
    llegados = sum(1 for v in viajes if 0 <= float(v.get("arrival", -1)) <= FIN_HORA)
    co2 = nox = 0.0
    con_emisiones = 0
    for v in viajes:
        e = v.find("emissions")
        if e is not None:
            co2 += float(e.get("CO2_abs", 0))
            nox += float(e.get("NOx_abs", 0))
            con_emisiones += 1
    m = max(1, con_emisiones)
    return {
        "vehiculos": len(viajes),
        "espera_prom": round(espera, 2),
        "timeloss_prom": round(perdida, 2),
        "paradas_prom": round(paradas, 3),
        "throughput": llegados,
        "co2_prom": round(co2 / m / 1000, 1) if con_emisiones else "",
        "nox_prom": round(nox / m, 1) if con_emisiones else "",
    }


def vehiculos_tripinfo(archivo):
    """Una fila por vehiculo (para distribuciones): id, salida, retraso, espera, paradas, CO2 en g."""
    filas = []
    for v in ET.parse(archivo).getroot().findall("tripinfo"):
        e = v.find("emissions")
        filas.append({
            "id": v.get("id"),
            "depart": float(v.get("depart")),
            "timeloss": float(v.get("timeLoss")),
            "espera": float(v.get("waitingTime")),
            "paradas": int(v.get("waitingCount", 0)),
            "co2": round(float(e.get("CO2_abs", 0)) / 1000, 2) if e is not None else "",
        })
    return filas


# ---------------- Programa actuado de referencia ----------------
def leer_cfg(cfg):
    """Devuelve (net-file, lista de additional-files) del .sumocfg."""
    raiz = ET.parse(cfg).getroot()
    net = raiz.find("input/net-file").get("value")
    add = raiz.find("input/additional-files")
    adicionales = add.get("value").split(",") if add is not None else []
    return net, adicionales


def archivo_actuado(cfg, escenario, tls_ids, verde_min, verde_min_giro, verde_max):
    """Genera <escenario>_actuado.add.xml: un programa actuado nativo de SUMO por semaforo,
    con las mismas fases del programa estatico de la red y los mismos limites que el
    agente RL (verde minimo y maximo). SUMO crea solos los detectores. Devuelve el valor
    para --additional-files: los del .sumocfg mas el archivo nuevo."""
    net_file, adicionales = leer_cfg(cfg)
    net = sumolib.net.readNet(net_file, withPrograms=True)
    salida = f"{escenario}_actuado.add.xml"
    lineas = ["<additional>",
              "    <!-- Programa actuado de referencia: fases del programa fijo, verde minimo y maximo",
              f"         iguales a los del agente ({verde_min} s, {verde_min_giro} s en giros, {verde_max} s). -->"]
    for tls_id in tls_ids:
        programas = net.getTLS(tls_id).getPrograms()
        programa = programas.get("0", next(iter(programas.values())))
        lineas.append(f'    <tlLogic id="{tls_id}" type="actuated" programID="actuado" offset="0">')
        for fase in programa.getPhases():
            estado = fase.state
            es_verde = ("G" in estado or "g" in estado) and "y" not in estado
            if es_verde:
                minimo = verde_min if sum(1 for c in estado if c in "Gg") > 2 else verde_min_giro
                lineas.append(f'        <phase duration="{int(fase.duration)}" '
                              f'minDur="{minimo}" maxDur="{verde_max}" state="{estado}"/>')
            else:
                lineas.append(f'        <phase duration="{int(fase.duration)}" state="{estado}"/>')
        lineas.append("    </tlLogic>")
    lineas.append("</additional>")
    with open(salida, "w") as f:
        f.write("\n".join(lineas) + "\n")
    return ",".join(adicionales + [salida])


# ---------------- CSV de resultados ----------------
def abrir_csv(ruta, campos=CAMPOS):
    """Abre el CSV en modo append. Si ya existe con otras columnas (formato anterior),
    lo renombra a *_v1.csv para conservar el historial y empieza uno nuevo."""
    nuevo = not os.path.exists(ruta)
    if not nuevo:
        with open(ruta, newline="") as f:
            cabecera = next(csv.reader(f), [])
        if cabecera != campos:
            k = 1
            while os.path.exists(ruta.replace(".csv", f"_v{k}.csv")):
                k += 1
            viejo = ruta.replace(".csv", f"_v{k}.csv")
            os.rename(ruta, viejo)
            print(f"El CSV anterior tenia otras columnas; se conservo como {viejo}")
            nuevo = True
    archivo = open(ruta, "a", newline="")
    escritor = csv.DictWriter(archivo, fieldnames=campos)
    if nuevo:
        escritor.writeheader()
    return archivo, escritor


def guardar_serie(ruta, encabezado, filas):
    """Serie de vehiculos detenidos por aproximacion cada 60 s (para graficar la hora)."""
    with open(ruta, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(encabezado)
        w.writerows(filas)
