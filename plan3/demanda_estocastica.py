"""
demanda_estocastica.py - Demanda de los escenarios nuevos del plan 3 (escenarios_plan3.RECETAS): llegadas de
Poisson, entrada por el mejor carril, P6e, perfil de 10 min y mezcla de Lima. Diseno y pruebas de factibilidad en
analisis_mejora_2026-11-04/plan3/demanda/ (informe.md y guiones/); decisiones A2 y A7, tecnicas B6 y B19.

Uso (desde plan3/):
  python demanda_estocastica.py preparar3             escribe <esc>.rou.xml y <esc>.sumocfg de cada escenario nuevo
  python demanda_estocastica.py preparar3 --revisar   solo compara: sale con 1 si algun archivo no es el que escribiria
  python demanda_estocastica.py demanda A.rou.xml ... vehiculos esperados: total, por periodo y por bloque de 10 min

Que genera preparar3 y que hereda (todo en la carpeta de este archivo, plan3/):
  genera    <esc>.rou.xml   la demanda de <caso>.rou.xml con la receta del escenario (abajo)
            <esc>.sumocfg   el <caso>.sumocfg con route-files = <esc>.rou.xml
  hereda    la red y el programa fijo del caso: el .sumocfg nombra <red>.net.xml y <caso>.add.xml sin copiarlos, asi
            que el brazo "fijo" de un escenario nuevo es el fijo entregado de su caso. barrer_fijo --instalar escribiria
            un <esc>.add.xml que nadie carga (lo avisa); el plan 3 no usa --instalar.
  al vuelo  <esc>_actuado.add.xml y <esc>_trivial.add.xml: los escriben comun.archivo_actuado y archivo_trivial en el
            cwd al correr esos brazos, como en los escenarios entregados.
Receta (caso, llegadas, perfil, mezcla, arranque), en este orden:
  1. perfil: rou_perfil_poisson; si no, llegadas "poisson": rou_poisson; "regulares": la demanda del caso tal cual
  2. mezcla: con_mezcla (startupDelay = arranque) y escalar_exp(1 / equivalencia_media())
  3. entrada_best en todos los flows
Entrada por el mejor carril (A2): departLane="best" en cada flow y no <default.departlane> en el .sumocfg. Es parte
de la demanda: viaja con el .rou.xml, se ve al leerlo y no depende de que un programa lance sumo con el .sumocfg o
con su propia linea de comandos. Ademas, en SUMO 1.25 las dos formas no son iguales: el vehiculo que hereda "best" de
la opcion entra por MSEdge::getProbableLane (el carril con mas hueco) y el que lo trae en el flow por getFreeLane, el
"best" de la documentacion. Las dos ven las mismas llegadas y bajan la espera para entrar de P6 de ~46 s/veh a menos
de 1 s/veh, pero reparten distinto los carriles (plan3/pruebas/esc/salidas/archivos.txt, parte e).
"""
import os
import re
import sys
import argparse
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
if RAIZ not in sys.path:
    sys.path.append(RAIZ)                 # escenarios_plan3 y con_escenarios viven en la raiz
import escenarios_plan3                   # noqa: E402

# Perfil de 10 min (A7, B19): barrido_demanda.PERFIL (1.0, 1.5, 2.0, 2.0, 1.5, 1.0) dividido entre su media 1.5.
# Cada media hora suma la demanda del caso y la punta queda en el centro de la hora (de 20 a 40 min).
PERFIL = tuple(f / 1.5 for f in (1.0, 1.5, 2.0, 2.0, 1.5, 1.0))
BLOQUE = 600
EXP = re.compile(r"^\s*exp\(\s*([0-9.eE+-]+)\s*\)\s*$")
SUFIJO_BLOQUE = re.compile(r"_b(\d+)$")

# ---------------- Mezcla de Lima (A7; valores de la parte B del prerregistro) ----------------
# Composicion: linea cortina del rio Rimac (JICA y Nippon Koei 2013, Tabla 2.16: 15 puentes, 24 h, 8-9.05.2012),
# sumada por filas porque la fila Total publicada omite el puente Huachipa, y sin camiones (vienen sobre todo de vias
# de carga). Vehiculos por dia:
JICA_2013 = {"auto": 541088, "moto": 29919, "publico": 114537}
# El transporte publico se reparte como la flota regular de la ATU en 2021 (Lima Como Vamos, reporte 2021, p. 16,
# suma de su tabla por antiguedad). Es flota y no transito [I].
ATU_2021 = {"combi": 6420, "micro": 7533, "bus": 8357}
# Vehiculos equivalentes del INVERMET (UNFV, estudio de impacto vial del predio Oquendo, Tabla N.o 2): auto 1.00,
# camioneta rural (combi) 1.25, microbus 2.00, omnibus 3.00. La moto no tiene factor: 1.0 [S].
EQUIVALENTE = {"auto": 1.0, "moto": 1.0, "combi": 1.25, "micro": 2.0, "bus": 3.0}
# vType de cada clase. Todas conservan del vType "auto" entregado lo que no es de la clase: sigma 0.5, minGap 2.5 y
# maxSpeed 13.89 (tope de 50 km/h). auto: el vType entregado (clase passenger). moto y bus: los valores de su clase en
# SUMO 1.25 [M, leidos con TraCI]. combi y micro no tienen clase en SUMO: clase bus con largo, aceleracion y
# deceleracion supuestos [S]. Lo demas es de la clase: desvio de velocidad 0.1 (passenger, motorcycle) y 0.0 (bus).
TIPOS = {"auto": 'accel="2.6" decel="4.5" length="5"',
         "moto": 'vClass="motorcycle" accel="6" decel="10" length="2.2"',
         "combi": 'vClass="bus" accel="2" decel="4.5" length="6"',
         "micro": 'vClass="bus" accel="1.5" decel="4" length="8"',
         "bus": 'vClass="bus" accel="1.2" decel="4" length="12"'}
COMUNES = 'sigma="0.5" minGap="2.5" maxSpeed="13.89"'
VTYPE_AUTO = re.compile(r'<vType id="auto"[^>]*/>')


def composicion():
    """{clase: proporcion}: JICA 2013 sin camiones, con el transporte publico repartido como la flota ATU 2021."""
    total, flota = sum(JICA_2013.values()), sum(ATU_2021.values())
    p = {"auto": JICA_2013["auto"] / total, "moto": JICA_2013["moto"] / total}
    p.update({clase: JICA_2013["publico"] / total * n / flota for clase, n in ATU_2021.items()})
    return p


def equivalencia_media():
    """Vehiculos equivalentes por vehiculo de la mezcla. Con veh/h x 1/esto, la demanda equivalente es la del caso."""
    return sum(p * EQUIVALENTE[clase] for clase, p in composicion().items())


def tasa(q):
    """veh/h -> veh/s con 12 cifras significativas (SUMO la lee como double)."""
    return float("%.12g" % (q / 3600.0))


def contar_flows(texto):
    return len(re.findall(r"<flow\b", texto))


def rou_poisson(texto):
    """Cada vehsPerHour="q" pasa a period="exp(q/3600)": llegadas de Poisson con la misma tasa media por flow. begin y
    end no cambian: el total esperado por periodo y la inversion de la punta a los 1800 s son los del caso."""
    nuevo, n = re.subn(r'vehsPerHour="([0-9.]+)"', lambda m: 'period="exp(%r)"' % tasa(float(m.group(1))), texto)
    if n == 0 or n != contar_flows(texto):
        raise SystemExit(f"rou_poisson: {n} vehsPerHour y {contar_flows(texto)} flows")
    return nuevo


def escalar_exp(texto, f):
    """Multiplica por f la tasa de cada period="exp(r)" (12 cifras). No toca vehsPerHour."""
    nuevo, n = re.subn(r'period="exp\(([0-9.eE+-]+)\)"',
                       lambda m: 'period="exp(%r)"' % float("%.12g" % (float(m.group(1)) * f)), texto)
    if n == 0:
        raise SystemExit('escalar_exp: no hay period="exp(...)"')
    return nuevo


def entrada_best(texto):
    """departLane="best" en cada flow: cada vehiculo entra por el carril que mas le sirve para su ruta (A2)."""
    if "departLane" in texto:
        raise SystemExit("entrada_best: la demanda ya trae departLane")
    nuevo, n = re.subn(r"<flow\b([^>]*?)\s*/>", r'<flow\1 departLane="best"/>', texto)
    if n != contar_flows(texto):
        raise SystemExit(f"entrada_best: {n} de {contar_flows(texto)} flows")
    return nuevo


def rou_perfil_poisson(texto, perfil=PERFIL, bloque=BLOQUE):
    """Cada flow (vehsPerHour="q") se parte en bloques de `bloque` s con period="exp(q*f_k/3600)", f_k el factor del
    bloque k, e id <flow>_b<k> (flujo_de quita el sufijo). Un Poisson partido en bloques, cada uno con su tasa, es un
    Poisson con tasa por tramos. Con PERFIL cada media hora suma lo del caso. Los flows salen ordenados por inicio
    (SUMO lee las rutas por tramos de tiempo)."""
    lineas, flujos = ["<routes>"], []
    for hijo in ET.fromstring(texto):
        if hijo.tag != "flow":
            lineas.append("    " + ET.tostring(hijo, encoding="unicode").strip())
            continue
        ini, fin, q = float(hijo.get("begin")), float(hijo.get("end")), float(hijo.get("vehsPerHour"))
        cubierto = 0.0
        for k, factor in enumerate(perfil):
            a, b = max(ini, bloque * k), min(fin, bloque * (k + 1))
            if a >= b:
                continue
            cubierto += b - a
            f = {c: v for c, v in hijo.attrib.items() if c != "vehsPerHour"}
            f.update(id=f"{hijo.get('id')}_b{k}", begin=f"{a:g}", end=f"{b:g}", period="exp(%r)" % tasa(q * factor))
            flujos.append((a, len(flujos), "    <flow " + " ".join(f'{c}="{v}"' for c, v in f.items()) + "/>"))
        if abs(cubierto - (fin - ini)) > 1e-9:
            raise SystemExit(f"rou_perfil_poisson: el perfil no cubre el flow {hijo.get('id')} ({ini:g}-{fin:g} s)")
    lineas += [x[2] for x in sorted(flujos)]
    return "\n".join(lineas) + "\n</routes>\n"


def con_mezcla(texto, arranque=0.0):
    """El vType "auto" pasa a una vTypeDistribution "auto" con la mezcla de Lima: los flows (type="auto") no cambian
    y SUMO sortea el tipo de cada vehiculo. arranque > 0: startupDelay (s) de todos los tipos."""
    extra = f' startupDelay="{arranque:g}"' if arranque else ""
    lineas = ['<vTypeDistribution id="auto">']
    lineas += [f'        <vType id="lima_{clase}" {TIPOS[clase]} {COMUNES}{extra} probability="{p:.6f}"/>'
               for clase, p in composicion().items()]
    bloque = "\n".join(lineas + ["    </vTypeDistribution>"])
    nuevo, n = VTYPE_AUTO.subn(lambda m: bloque, texto)
    if n != 1:
        raise SystemExit(f'con_mezcla: se esperaba un vType "auto" y hay {n}')
    return nuevo


def flujo_de(ident):
    """Flow de origen de un vehiculo (<flow>.<k>) o de un flow del perfil (<flow>_b<k>), sin el sufijo del bloque:
    "p1_W_E_b2.17" -> "p1_W_E". Con esto el lector por periodo y las metricas del corredor agrupan los bloques."""
    return SUFIJO_BLOQUE.sub("", ident.rsplit(".", 1)[0])


def bloque_de(ident):
    """Bloque k del perfil de un vehiculo o flow (<flow>_b<k>[.<n>]); None si no viene de un perfil."""
    m = SUFIJO_BLOQUE.search(ident.rsplit(".", 1)[0])
    return int(m.group(1)) if m else None


# ---------------- Demanda esperada ----------------
def demanda_flow(flow):
    """Vehiculos esperados de un <flow> entre begin y end: vehsPerHour (o perHour) q -> q*dur/3600;
    period="exp(r)" -> r*dur (Poisson); period=T -> dur/T; probability=p -> p*dur; number=N -> N."""
    dur = float(flow.get("end", 3600)) - float(flow.get("begin", 0))
    q = flow.get("vehsPerHour") or flow.get("perHour")
    if q:
        return float(q) * dur / 3600
    if flow.get("number"):
        return float(flow.get("number"))
    if flow.get("probability"):
        return float(flow.get("probability")) * dur
    periodo = flow.get("period")
    if periodo:
        m = EXP.match(periodo)
        return float(m.group(1)) * dur if m else dur / float(periodo)
    raise SystemExit(f"demanda_flow: el flow {flow.get('id')} no tiene tasa")


def leer_flows(rutas):
    """Los <flow> de un .rou.xml o de una lista de ellos."""
    return [el for r in ([rutas] if isinstance(rutas, str) else rutas) for el in ET.parse(r).getroot().iter("flow")]


def por_flow(rutas):
    """{id del flow: vehiculos esperados}."""
    return {el.get("id"): demanda_flow(el) for el in leer_flows(rutas)}


def demanda_esperada(rutas):
    """Vehiculos esperados en toda la demanda (los veh/h del caso). Mismo contrato que veredicto.demanda (lista de
    .rou.xml), pero entiende exp(), probability y number; cada <trip> o <vehicle> suelto cuenta 1."""
    rutas = [rutas] if isinstance(rutas, str) else rutas
    sueltos = sum(1 for r in rutas for el in ET.parse(r).getroot() if el.tag in ("trip", "vehicle"))
    return sum(por_flow(rutas).values()) + sueltos


def por_bloque(rutas, bloque=BLOQUE):
    """{k: vehiculos esperados entre k*bloque y (k+1)*bloque s}. Un flow que cruza un borde se reparte en proporcion al
    tiempo (tasa constante dentro del flow)."""
    res = {}
    for el in leer_flows(rutas):
        ini, fin = float(el.get("begin", 0)), float(el.get("end", 3600))
        n, k = demanda_flow(el), int(ini // bloque)
        while bloque * k < fin:
            a, b = max(ini, bloque * k), min(fin, bloque * (k + 1))
            res[k] = res.get(k, 0.0) + n * (b - a) / (fin - ini)
            k += 1
    return dict(sorted(res.items()))


def por_periodo(rutas, corte=1800):
    """{1: vehiculos esperados antes de corte, 2: desde corte}: los dos periodos de 30 min (la punta se invierte)."""
    return {k + 1: v for k, v in por_bloque(rutas, corte).items()}


# ---------------- preparar3 ----------------
def leer(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return fh.read()


def rou_escenario(esc, carpeta=AQUI):
    """Texto del <esc>.rou.xml de un escenario de escenarios_plan3.RECETAS, hecho desde <caso>.rou.xml de carpeta."""
    caso, llegadas, perfil, mezcla, arranque = escenarios_plan3.RECETAS[esc]
    texto = leer(os.path.join(carpeta, f"{caso}.rou.xml"))
    if any(SUFIJO_BLOQUE.search(el.get("id")) for el in ET.fromstring(texto).iter("flow")):
        raise SystemExit(f"{caso}.rou.xml: hay flows que ya terminan en _b<k>; flujo_de no los distinguiria")
    if perfil:
        texto = rou_perfil_poisson(texto)
        pasos = ["perfil de 10 min con llegadas de Poisson (cada flow en bloques de 600 s con period exp(q*f/3600), "
                 "f = 2/3, 1, 4/3, 4/3, 1, 2/3; ids <flow>_b<k>)"]
    elif llegadas == "poisson":
        texto = rou_poisson(texto)
        pasos = ["llegadas de Poisson (vehsPerHour q pasa a period exp(q/3600); mismo begin y end)"]
    else:
        pasos = ["llegadas regulares (vehsPerHour del caso)"]
    if mezcla:
        if llegadas != "poisson":
            raise SystemExit(f"{esc}: la mezcla escala tasas exp(); con llegadas regulares habria que escalar vehsPerHour")
        f = 1 / equivalencia_media()
        texto = escalar_exp(con_mezcla(texto, arranque), f)
        pasos.append(f"mezcla de Lima (vTypeDistribution auto: JICA 2013 sin camiones y flota ATU 2021) con los mismos "
                     f"vehiculos equivalentes del INVERMET (tasas x {f:.6f} = 1/{equivalencia_media():.6f})")
        if arranque:
            pasos.append(f"arranque lento: startupDelay {arranque:g} s en todos los tipos (solo para evaluar)")
    texto = entrada_best(texto)
    pasos.append("entrada por el mejor carril (departLane best en cada flow)")
    comentario = (f"{esc} (plan 3; lo escribe demanda_estocastica.py preparar3, no editar a mano): {caso}.rou.xml con "
                  + "; ".join(pasos) + ".")
    return texto.replace("<routes>", f"<routes>\n    <!-- {comentario} -->", 1)


def sumocfg_escenario(esc, carpeta=AQUI):
    """Texto del <esc>.sumocfg: el <caso>.sumocfg con route-files = <esc>.rou.xml (red y .add.xml del caso)."""
    caso = escenarios_plan3.RECETAS[esc][0]
    arbol = ET.parse(os.path.join(carpeta, f"{caso}.sumocfg"))
    raiz = arbol.getroot()
    raiz.find(".//route-files").set("value", f"{esc}.rou.xml")
    raiz.insert(0, ET.Comment(f" {esc} (plan 3; lo escribe demanda_estocastica.py preparar3): {caso}.sumocfg con "
                              f"la demanda de {esc}.rou.xml; la red y el programa fijo son los del caso. "))
    ET.indent(arbol, space="    ")
    return ET.tostring(raiz, encoding="unicode") + "\n"


def escribir(ruta, texto):
    """Escritura atomica: temporal con el pid y os.replace."""
    temporal = f"{ruta}.{os.getpid()}.tmp"
    with open(temporal, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(texto)
    os.replace(temporal, ruta)


def preparar3(carpeta=AQUI, revisar=False):
    """Escribe (o con revisar solo compara) <esc>.rou.xml y <esc>.sumocfg de cada escenario de RECETAS en carpeta.
    Devuelve los archivos que no estaban como se escribirian."""
    distintos = []
    for esc in escenarios_plan3.RECETAS:
        for nombre, texto in ((f"{esc}.rou.xml", rou_escenario(esc, carpeta)),
                              (f"{esc}.sumocfg", sumocfg_escenario(esc, carpeta))):
            ruta = os.path.join(carpeta, nombre)
            if os.path.exists(ruta) and leer(ruta) == texto:
                continue
            distintos.append(nombre)
            if not revisar:
                escribir(ruta, texto)
    return distintos


def main():
    ap = argparse.ArgumentParser(description="Demanda de los escenarios nuevos del plan 3")
    ap.add_argument("modo", choices=["preparar3", "demanda"])
    ap.add_argument("rutas", nargs="*", help="demanda: archivos .rou.xml")
    ap.add_argument("--revisar", action="store_true", help="preparar3: solo compara con lo que hay en disco")
    ap.add_argument("--carpeta", default=AQUI, help="preparar3: carpeta de los casos y de la salida (plan3/)")
    args = ap.parse_args()
    if args.modo == "demanda":
        for r in args.rutas:
            print(f"{r}: total {demanda_esperada([r]):.3f}; por periodo "
                  f"{ {k: round(v, 3) for k, v in por_periodo(r).items()} }; por bloque de 600 s "
                  f"{ {k: round(v, 3) for k, v in por_bloque(r).items()} }")
        return
    import con_escenarios
    if con_escenarios.prohibida(args.carpeta):
        raise SystemExit("preparar3: no se escribe en plan2/ ni en TESIS/")
    distintos = preparar3(args.carpeta, args.revisar)
    n = 2 * len(escenarios_plan3.RECETAS)
    if args.revisar:
        print(f"{n - len(distintos)} de {n} archivos como los escribiria preparar3" +
              (f"; distintos o ausentes: {', '.join(distintos)}" if distintos else ""))
        sys.exit(1 if distintos else 0)
    print(f"{len(distintos)} de {n} archivos escritos en {args.carpeta}" +
          (f": {', '.join(distintos)}" if distintos else " (todos estaban al dia)"))


if __name__ == "__main__":
    main()
