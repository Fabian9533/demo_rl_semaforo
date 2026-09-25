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
LARGO_VEH, MIN_GAP = 5.0, 2.5    # plaza que ocupa un vehiculo detenido: 7.5 m
UMBRAL_SPILLBACK = 0.9           # spillback: la cola detenida ocupa >= 90 % de las plazas de un carril
# flows de paso en el sentido de la punta (el que favorece la onda verde)
FLUJOS_PUNTA = ["p1_W_E", "p2_E_W"]

# Columnas del CSV de resultados por episodio (una fila por corrida o por episodio)
CAMPOS = ["modo", "episodio", "semilla", "epsilon", "vehiculos",
          "espera_prom", "timeloss_prom", "cola_prom", "cola_max",
          "recompensa", "recompensa_decision", "decisiones", "cambios_fase",
          "paradas_prom", "throughput", "co2_prom", "nox_prom",
          "estados_q", "dq_max", "eval_timeloss", "eval_espera"]


# ---------------- Metricas del tripinfo ----------------
def leer_tripinfo(archivo, flujos_corredor=None):
    """Metricas por vehiculo promediadas sobre el episodio.
    espera_prom   : s detenido por vehiculo (waitingTime, velocidad <= 0.1 m/s)
    timeloss_prom : s de retraso por vehiculo respecto a la velocidad deseada (timeLoss)
    paradas_prom  : detenciones por vehiculo (waitingCount)
    throughput    : vehiculos que terminaron su viaje antes de los 3600 s
    co2_prom      : g de CO2 por vehiculo; nox_prom: mg de NOx por vehiculo
                    (requieren --device.emissions.probability 1; clase HBEFA3/PC_G_EU4 por defecto)
    Si se pasa flujos_corredor (ids de los <flow> que recorren toda la avenida), agrega
    viaje_corredor_prom y retraso_corredor_prom: duracion y timeLoss medios de esos
    vehiculos, es decir, el tiempo de viaje extremo a extremo del corredor."""
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
    res = {
        "vehiculos": len(viajes),
        "espera_prom": round(espera, 2),
        "timeloss_prom": round(perdida, 2),
        "paradas_prom": round(paradas, 3),
        "throughput": llegados,
        "co2_prom": round(co2 / m / 1000, 1) if con_emisiones else "",
        "nox_prom": round(nox / m, 1) if con_emisiones else "",
    }
    res["no_terminados"] = sum(1 for v in viajes if float(v.get("arrival", -1)) < 0)
    if flujos_corredor:
        # el id de un vehiculo de un flow es "<flow>.<numero>"
        largos = [v for v in viajes if v.get("id").rsplit(".", 1)[0] in flujos_corredor]
        punta = [v for v in largos if v.get("id").rsplit(".", 1)[0] in FLUJOS_PUNTA]
        k = max(1, len(largos))
        res["viaje_corredor_prom"] = round(sum(float(v.get("duration")) for v in largos) / k, 2)
        res["retraso_corredor_prom"] = round(sum(float(v.get("timeLoss")) for v in largos) / k, 2)
        retraso_punta = sum(float(v.get("timeLoss")) for v in punta) / max(1, len(punta))
        res["retraso_corredor_punta"] = round(retraso_punta, 2)
        res["paradas_corredor"] = round(sum(int(v.get("waitingCount", 0)) for v in largos) / k, 3)
        le1 = sum(1 for v in largos if int(v.get("waitingCount", 0)) <= 1)
        res["paradas_corredor_le1"] = round(le1 / k, 3)
        res["vehiculos_corredor"] = len(largos)
    return res


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
              f"         iguales a los del agente ({verde_min} s, {verde_min_giro} s en giros, "
              f"{verde_max} s). -->"]
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
    # extrasaction="ignore": las metricas que no estan en CAMPOS (por ejemplo las de corredor,
    # que solo van al CSV de evaluacion) no rompen el formato del CSV por episodio
    escritor = csv.DictWriter(archivo, fieldnames=campos, extrasaction="ignore")
    if nuevo:
        escritor.writeheader()
    return archivo, escritor


def plazas_carril(net, edge_id):
    """Vehiculos detenidos que caben en UN carril del edge (5 m de auto + 2.5 m de separacion).
    En los enlaces de 285.6 m son 38; el umbral de spillback es el 90 %: 34."""
    return int(net.getEdge(edge_id).getLength() // (LARGO_VEH + MIN_GAP))


def umbral_carril(plazas):
    return int(UMBRAL_SPILLBACK * plazas)


class MedidorEnlaces:
    """Mide, por carril y con una sola lectura por paso (suscripcion TraCI), las colas en los
    enlaces compartidos entre cruces. Hay spillback en un paso cuando algun carril de algun
    enlace tiene al menos umbral_carril vehiculos detenidos: la cola llega casi hasta el
    cruce de aguas arriba y el siguiente vehiculo que se detenga lo bloquea. La misma
    clase la usan rl_corredor.py (fijo, actuado, Q-learning) y rl_ippo.py, asi que la
    medicion es identica en todos los controles. Crear despues de traci.start."""

    def __init__(self, net_file, enlaces):
        import traci
        import traci.constants as tc
        self.tc = tc
        net = sumolib.net.readNet(net_file)
        self.enlaces = list(enlaces)
        self.carriles = {e: [c.getID() for c in net.getEdge(e).getLanes()] for e in self.enlaces}
        self.plazas = {e: plazas_carril(net, e) for e in self.enlaces}
        self.umbral = {e: umbral_carril(self.plazas[e]) for e in self.enlaces}
        for e in self.enlaces:
            for c in self.carriles[e]:
                traci.lane.subscribe(c, [tc.LAST_STEP_VEHICLE_HALTING_NUMBER, tc.LAST_STEP_VEHICLE_NUMBER])
        self.halting = {e: [0] * len(self.carriles[e]) for e in self.enlaces}
        self.veh = {e: [0] * len(self.carriles[e]) for e in self.enlaces}
        self.cola_max = 0
        self.veh_max = 0
        self.seg_evento = 0        # segundos con spillback en toda la corrida
        self.seg_evento_hora = 0   # idem dentro de la hora de demanda (para la tasa)
        self.eventos = 0           # flancos de subida
        self.en_evento = False

    def paso(self, t):
        """Llamar despues de cada traci.simulationStep(); t = numero de paso."""
        import traci
        res = traci.lane.getAllSubscriptionResults()
        evento = False
        for e in self.enlaces:
            h = [res.get(c, {}).get(self.tc.LAST_STEP_VEHICLE_HALTING_NUMBER, 0) for c in self.carriles[e]]
            v = [res.get(c, {}).get(self.tc.LAST_STEP_VEHICLE_NUMBER, 0) for c in self.carriles[e]]
            self.halting[e], self.veh[e] = h, v
            self.cola_max = max(self.cola_max, max(h))
            self.veh_max = max(self.veh_max, max(v))
            if max(h) >= self.umbral[e]:
                evento = True
        if evento:
            self.seg_evento += 1
            if t <= FIN_HORA:
                self.seg_evento_hora += 1
            if not self.en_evento:
                self.eventos += 1
        self.en_evento = evento

    def max_halting(self, e):
        return max(self.halting[e]) if self.halting[e] else 0

    def resumen(self):
        return {
            "spillback_tasa": round(self.seg_evento_hora / FIN_HORA, 4),
            "spillback_seg": self.seg_evento,
            "spillback_eventos": self.eventos,
            "cola_max_enlace": self.cola_max,     # maximo por carril de detenidos en un enlace
            "veh_max_enlace": self.veh_max,       # maximo por carril de vehiculos (parados o no)
        }


def guardar_fases(ruta, tls_ids, filas):
    """Indice de fase de cada semaforo por segundo (para ver el desfase entre cruces)."""
    with open(ruta, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t"] + list(tls_ids))
        w.writerows(filas)


def guardar_serie(ruta, encabezado, filas):
    """Serie de vehiculos detenidos por aproximacion cada 60 s (para graficar la hora)."""
    with open(ruta, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(encabezado)
        w.writerows(filas)


def politicas_ippo(escenario):
    """Politicas IPPO entrenadas en un escenario, leidas de resultados_<esc>_ippo_<var>_s<base>.csv:
    {variante: {"bases": {base: eval_999_final}, "mediana": base}}. La politica que representa a
    cada variante en las tablas es la de la base cuya ultima evaluacion intermedia (semilla 999)
    es la mediana de las suyas; nunca se elige con las semillas de evaluacion final."""
    import re
    import glob
    res = {}
    for ruta in sorted(glob.glob(f"resultados_{escenario}_ippo_*_s*.csv")):
        m = re.match(rf"resultados_{escenario}_ippo_(\w+)_s(\d+)\.csv$", ruta)
        if not m:
            continue
        with open(ruta, newline="") as f:
            filas = list(csv.DictReader(f))
        evals = [float(x["eval_timeloss"]) for x in filas if x.get("eval_timeloss")]
        if evals:
            res.setdefault(m.group(1), {"bases": {}})["bases"][int(m.group(2))] = evals[-1]
    for d in res.values():
        orden = sorted(d["bases"], key=lambda b: d["bases"][b])
        d["mediana"] = orden[len(orden) // 2]
    return res


def brazo_ippo(variante, politicas, brazos_csv):
    """Nombre del brazo principal de una variante en evaluacion_<esc>.csv: ippo_<var>_s<mediana>
    si se evaluaron varias bases, ippo_<var> si solo una."""
    if variante not in politicas:
        return None
    con_base = f"ippo_{variante}_s{politicas[variante]['mediana']}"
    if con_base in brazos_csv:
        return con_base
    return f"ippo_{variante}" if f"ippo_{variante}" in brazos_csv else None


# ---------------- Arranque robusto de SUMO (plan v2) ----------------
def iniciar_sumo(cmd, intentos=5, espera=3.0):
    """traci.start con reintentos. En Windows otro proceso (el antivirus) puede tener tomado un
    instante el archivo de salida recien escrito y SUMO sale con 'Could not build output file';
    una noche de cien entrenamientos lo encuentra seguro (24.09.2026). Se descarta la conexion
    fallida y se repite el mismo comando: no cambia ningun numero de la simulacion."""
    import time
    import traci
    from traci import connection as conexiones
    for k in range(intentos):
        try:
            return traci.start(cmd)
        except Exception:
            if k == intentos - 1:
                raise
            for etiqueta in ("default", ""):
                con = conexiones._connections.pop(etiqueta, None)
                if con is not None and getattr(con, "_process", None) is not None:
                    try:
                        con._process.kill()
                    except Exception:
                        pass
            time.sleep(espera)
