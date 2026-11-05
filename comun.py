"""
comun.py - Funciones compartidas por rl_semaforo.py, rl_corredor.py y evaluar.py:
lectura de las metricas U3 del tripinfo, programa actuado de referencia, CSV de
resultados con sus columnas y series de cola por minuto.
"""
import os
import re
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
def ruta_estadisticas(tripinfo):
    """Archivo de --statistic-output que acompana a un tripinfo (mismo nombre con _stats)."""
    return (tripinfo[:-4] if tripinfo.endswith(".xml") else tripinfo) + "_stats.xml"


# plan3 (05.11.2026): evaluar3.py lo activa para tener tambien en el tripinfo una fila por cada vehiculo que al
# cerrar seguia esperando entrar (depart = -1, departDelay = lo que espero) y asignarlo a su periodo. Apagado por
# defecto: con False los comandos de sumo son los de siempre. leer_tripinfo y vehiculos_tripinfo ignoran esas filas,
# asi que las metricas no cambian con la opcion (los no insertados se siguen contando del archivo de estadisticas).
ESCRIBIR_NO_INSERTADOS = False


def args_estadisticas(tripinfo):
    """Argumentos de sumo para escribir el resumen de estadisticas junto al tripinfo. De ahi salen
    los vehiculos que al cerrar la simulacion aun esperaban entrar a la red (no estan en el tripinfo)."""
    extra = ["--tripinfo-output.write-undeparted", "true"] if ESCRIBIR_NO_INSERTADOS else []
    return ["--statistic-output", ruta_estadisticas(tripinfo)] + extra


# plan3 (05.11.2026): en el perfil de 10 min (plan3/demanda_estocastica.py) los flows de cada bloque se llaman
# <flow>_b<k>. con_escenarios.registrar() lo activa para que las metricas del corredor reconozcan esos vehiculos.
# Apagado por defecto: corredor_var (plan2), que ya usaba _b<k>, sigue dando lo mismo que en lo entregado.
QUITAR_BLOQUE = False
_SUFIJO_BLOQUE = re.compile(r"_b(\d+)$")


def _flujo(ident):
    """Flow de un vehiculo ("<flow>.<numero>"), sin el sufijo de bloque si QUITAR_BLOQUE esta activo."""
    flujo = ident.rsplit(".", 1)[0]
    return _SUFIJO_BLOQUE.sub("", flujo) if QUITAR_BLOQUE else flujo


def _viajes(archivo):
    """Filas del tripinfo de los vehiculos que entraron (sin las de los no insertados, depart < 0)."""
    return [v for v in ET.parse(archivo).getroot().findall("tripinfo") if float(v.get("depart", 0)) >= 0]


def borrar_tripinfo(tripinfo, intentos=5, espera=1.0):
    """Borra el tripinfo y su archivo de estadisticas, si existen. En Windows otro proceso (el
    antivirus) puede tener tomado un instante un archivo recien escrito (paso en un barrido de
    red): se reintenta y, si sigue tomado, se deja; no cambia ningun numero."""
    import time
    for ruta in (tripinfo, ruta_estadisticas(tripinfo)):
        for k in range(intentos):
            try:
                if os.path.exists(ruta):
                    os.remove(ruta)
                break
            except PermissionError:
                time.sleep(espera)


def leer_tripinfo(archivo, flujos_corredor=None):
    """Metricas por vehiculo promediadas sobre el episodio.
    espera_prom   : s detenido por vehiculo (waitingTime, velocidad <= 0.1 m/s)
    timeloss_prom : s de retraso por vehiculo respecto a la velocidad deseada (timeLoss); SUMO lo
                    cuenta desde que el vehiculo entra a la red
    retraso_insercion_prom : s que el vehiculo espero para entrar a la red (departDelay): con la
                    arista de entrada llena, SUMO lo retiene fuera y ese tiempo no entra en timeLoss
    no_insertados : vehiculos que al cerrar la simulacion seguian esperando entrar (no aparecen en
                    el tripinfo); se leen del archivo de estadisticas (args_estadisticas)
    retraso_total_prom : metrica primaria. (suma de timeLoss + departDelay de
                    los vehiculos del tripinfo + espera acumulada de los no insertados) / (vehiculos
                    del tripinfo + no insertados). La espera de los no insertados es la que llevaban
                    al cerrar, una cota inferior. Sin archivo de estadisticas se toma no_insertados = 0.
    paradas_prom  : detenciones por vehiculo (waitingCount)
    throughput    : vehiculos que terminaron su viaje antes de los 3600 s
    co2_prom      : g de CO2 por vehiculo; nox_prom: mg de NOx por vehiculo
                    (requieren --device.emissions.probability 1; clase HBEFA3/PC_G_EU4 por defecto)
    Si se pasa flujos_corredor (ids de los <flow> que recorren toda la avenida), agrega
    viaje_corredor_prom y retraso_corredor_prom: duracion y timeLoss medios de esos
    vehiculos, es decir, el tiempo de viaje extremo a extremo del corredor."""
    viajes = _viajes(archivo)
    n = max(1, len(viajes))
    espera = sum(float(v.get("waitingTime")) for v in viajes) / n
    perdida = sum(float(v.get("timeLoss")) for v in viajes) / n
    insercion = sum(float(v.get("departDelay", 0)) for v in viajes)
    no_insertados, espera_fuera = 0, 0.0
    stats = ruta_estadisticas(archivo)
    if os.path.exists(stats):
        raiz = ET.parse(stats).getroot()
        veh, trip = raiz.find("vehicles"), raiz.find("vehicleTripStatistics")
        if veh is not None:
            no_insertados = int(veh.get("waiting", 0))
        if trip is not None and no_insertados:
            espera_fuera = no_insertados * float(trip.get("departDelayWaiting", 0))
    total = (sum(float(v.get("timeLoss")) for v in viajes) + insercion + espera_fuera) / \
        max(1, len(viajes) + no_insertados)
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
        "retraso_total_prom": round(total, 2),
        "retraso_insercion_prom": round(insercion / n, 2),
        "no_insertados": no_insertados,
        "paradas_prom": round(paradas, 3),
        "throughput": llegados,
        "co2_prom": round(co2 / m / 1000, 1) if con_emisiones else "",
        "nox_prom": round(nox / m, 1) if con_emisiones else "",
    }
    res["no_terminados"] = sum(1 for v in viajes if float(v.get("arrival", -1)) < 0)
    if flujos_corredor:
        # el id de un vehiculo de un flow es "<flow>.<numero>"
        largos = [v for v in viajes if _flujo(v.get("id")) in flujos_corredor]
        punta = [v for v in largos if _flujo(v.get("id")) in FLUJOS_PUNTA]
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
    for v in _viajes(archivo):
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
def escribir_atomico(ruta, texto, intentos=10, espera=2.0):
    """plan3 (0.11): escribe ruta en un temporal con el pid y lo reemplaza con reintentos (como
    barrer_fijo.reemplazar). Varias evaluaciones del mismo escenario regeneran el mismo .add.xml: asi ninguna
    lee un archivo a medio escribir y dos procesos no se pisan el temporal. En Windows os.replace falla si en
    ese instante un sumo tiene abierto el destino. El contenido es el mismo de antes, byte a byte. Si no llega
    a reemplazar (se agotan los reintentos u otro error), borra su temporal; el destino queda como estaba."""
    import time
    tmp = f"{ruta}.{os.getpid()}.tmp"
    try:
        with open(tmp, "w") as f:
            f.write(texto)
        for k in range(intentos):
            try:
                os.replace(tmp, ruta)
                return
            except PermissionError:
                if k == intentos - 1:
                    raise
                time.sleep(espera)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def leer_cfg(cfg):
    """Devuelve (net-file, lista de additional-files) del .sumocfg. plan3: sin espacios alrededor de cada ruta
    ('a.add.xml, b.add.xml' es valido en SUMO); con los .sumocfg de siempre la lista es la misma."""
    raiz = ET.parse(cfg).getroot()
    net = raiz.find("input/net-file").get("value")
    add = raiz.find("input/additional-files")
    adicionales = [a.strip() for a in add.get("value").split(",") if a.strip()] if add is not None else []
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
    escribir_atomico(salida, "\n".join(lineas) + "\n")
    return ",".join(adicionales + [salida])


def archivo_trivial(cfg, escenario, tls_ids, verde_min, verde_min_giro):
    """Genera <escenario>_trivial.add.xml: control de cordura del plan v2. Es el
    programa fijo del escenario (el "fijo" de los .add.xml del .sumocfg; si no hay, el "0" de la
    red) con cada verde en el minimo del agente y todos los desfases en 0, es decir, la politica
    que cambia de fase en cuanto la mascara lo permite. programID "trivial". Devuelve el valor
    para --additional-files: los del .sumocfg mas el archivo nuevo."""
    net_file, adicionales = leer_cfg(cfg)
    fases = {}
    for ruta in adicionales:
        if not os.path.exists(ruta):
            continue
        for tl in ET.parse(ruta).getroot().findall("tlLogic"):
            if tl.get("id") in tls_ids and tl.get("programID") == "fijo":
                fases[tl.get("id")] = [(int(float(p.get("duration"))), p.get("state"))
                                       for p in tl.findall("phase")]
    if len(fases) < len(tls_ids):
        net = sumolib.net.readNet(net_file, withPrograms=True)
        for tls_id in tls_ids:
            if tls_id not in fases:
                programas = net.getTLS(tls_id).getPrograms()
                programa = programas.get("0", next(iter(programas.values())))
                fases[tls_id] = [(int(p.duration), p.state) for p in programa.getPhases()]
    salida = f"{escenario}_trivial.add.xml"
    lineas = ["<additional>",
              "    <!-- Control trivial: fases del programa fijo, cada verde en el minimo del agente "
              f"({verde_min} s, {verde_min_giro} s en giros) y desfases en 0. -->"]
    for tls_id in tls_ids:
        lineas.append(f'    <tlLogic id="{tls_id}" type="static" programID="trivial" offset="0">')
        for duracion, estado in fases[tls_id]:
            if ("G" in estado or "g" in estado) and "y" not in estado:
                duracion = verde_min if sum(1 for c in estado if c in "Gg") > 2 else verde_min_giro
            lineas.append(f'        <phase duration="{duracion}" state="{estado}"/>')
        lineas.append("    </tlLogic>")
    lineas.append("</additional>")
    escribir_atomico(salida, "\n".join(lineas) + "\n")
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


# ---------------- Semillas a ciegas del plan 3 (05.11.2026) ----------------
# Las semillas del examen y de la prueba final (plan3/PRERREGISTRO.md, tabla de §3: examen_regular, examen_h1,
# examen_aleatorio y final) solo se simulan desde la cola de plan3, en un trabajo de uso ciego: cola.py pone P3_USO.
# Cualquier otra corrida con ellas (una prueba, una revision) se niega antes de abrir SUMO. Lo entregado nunca uso
# estas semillas, y las de entrenamiento son base + episodio, asi que no cambia ningun numero.
BLOQUES_CIEGOS = ((7001, 7100), (8001, 8120), (10001, 10100), (11001, 11030), (12001, 12100), (13001, 13120))
USOS_CIEGOS = ("examen_regular", "examen_h1", "examen_aleatorio", "final")


def revisar_semilla_ciega(cmd):
    """Sale con error si cmd (lista de argumentos de sumo) lleva --seed de un bloque ciego fuera de un trabajo ciego."""
    cmd = list(cmd)
    if "--seed" not in cmd:
        return
    try:
        semilla = int(cmd[cmd.index("--seed") + 1])
    except (IndexError, ValueError):
        return
    uso = os.environ.get("P3_USO")
    if any(a <= semilla <= b for a, b in BLOQUES_CIEGOS) and uso not in USOS_CIEGOS:
        raise SystemExit(f"semilla {semilla}: es del examen o de la prueba final del plan 3 y solo se simula desde la "
                         f"cola, en un trabajo de uso ciego (P3_USO={uso!r}). Para probar, use las de humo "
                         f"424301-424360 o la base 7.")


# ---------------- Arranque robusto de SUMO (plan v2) ----------------
def iniciar_sumo(cmd, intentos=5, espera=3.0):
    """traci.start con reintentos. En Windows otro proceso (el antivirus) puede tener tomado un
    instante el archivo de salida recien escrito y SUMO sale con 'Could not build output file';
    una noche de cien entrenamientos lo encuentra seguro. Se descarta la conexion
    fallida y se repite el mismo comando: no cambia ningun numero de la simulacion."""
    import time
    import traci
    from traci import connection as conexiones
    revisar_semilla_ciega(cmd)
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
