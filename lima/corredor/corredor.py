"""
corredor.py - Segundo caso de Lima: el corredor de la Av. Alfredo Benavides (Miraflores), entre la Av. Jose Larco
y la Av. Republica de Panama. Seis cruces con semaforo en 1.2 km; un agente por cruce, con mensajes entre vecinos.

Uso (desde demo_rl/lima/corredor):
  python corredor.py red        # benavides.net.xml (y red/benavides.nod|edg|con.xml)
  python corredor.py plan       # benavides.add.xml: el plan tipico supuesto
  python corredor.py demanda [--factor 1.0]   # benavides.rou.xml y benavides.sumocfg
  python corredor.py nivel --factor 1.2 --carpeta alta   # otro nivel de demanda en su carpeta: red, plan y demanda
  python corredor.py nivel --reparto avenida=1.2,transversal=0.8 --carpeta robustez/avenida   # mismo total, otro reparto
Como modulo: escribir_programa(...) lo usa estudio_corredor.py.

De donde sale cada cosa:
- Geometria: OpenStreetMap (descarga del 13.11.2026). Posicion de cada cruce a lo largo de la avenida (metros desde
  Larco), carriles de la avenida (3 por sentido al oeste del puente de la Via Expresa y 2 al este) y carriles y
  sentido de cada transversal. La avenida se dibuja recta y las transversales, perpendiculares: importan las
  distancias y los carriles, no la forma. Los dos lados del puente de Paseo de la Republica (55 m entre si) son un
  solo cruce.
- Semaforos: NO se midieron. El "plan tipico" es un supuesto con el rango que se ve en la zona: transversales con
  unos 43 s de verde y 97 s de rojo, ciclo de 140 s, sin coordinacion entre cruces.
- Demanda: no hay conteo. El Plan de Movilidad Urbana de Miraflores 2017-2020 (pags. 30-31) publica el volumen
  total de tres de los cruces: Larco / Benavides 3390 veh/h, Paseo de la Republica / Benavides 3778 y Benavides /
  Republica de Panama 4358. Con 1000 veh/h entrando por cada extremo de la avenida y transversales de 1050 (Larco),
  719 por lado (Paseo de la Republica) y 1009 por sentido (Republica de Panama), el total de esos tres cruces queda
  a menos de un 2 % del publicado (totales_por_cruce). Las transversales de los otros tres cruces son supuestas por
  sus carriles.

Convenciones de los demas casos de la tesis: aristas "<origen>_<destino>", semaforo_C<k>, y en cada programa la fase
0 es el verde de la avenida y la 2 el de la transversal. Una transversal de un solo sentido tiene en la red el
acceso contrario como un tramo de un carril SIN demanda: el modelo describe cada cruce con cuatro accesos.
"""
import argparse
import os
import subprocess
import sys

if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
ESC = "benavides"
VEL = 13.89                    # 50 km/h
ENTRADA = 600.0                # m de cada entrada a la red (avenida y transversales): que la cola quepa dentro
AMBAR = 3
VERDE_MIN = 10

# (cruce, transversal, x en m desde Larco, carriles del acceso norte (va al sur), carriles del acceso sur (va al
# norte)). None = la calle no tiene ese sentido: en la red es un tramo de un carril sin demanda.
CRUCES = [
    ("C1", "Av. José Larco", 0.0, None, 3),
    ("C2", "Calle Alcanfores", 162.0, 2, None),
    ("C3", "Av. La Paz", 270.0, None, 2),
    ("C4", "Av. Paseo de la República", 566.0, 2, 2),
    ("C5", "Av. Casimiro Ulloa", 685.0, 2, 2),
    ("C6", "Av. República de Panamá", 1228.0, 2, 2),
]
IDS = [c[0] for c in CRUCES]
CARRILES_AV = {"W": 3, "C1": 3, "C2": 3, "C3": 3, "C4": 2, "C5": 2, "C6": 2}     # carriles del tramo que sale hacia el este
# Demanda (veh/h): avenida por sentido en cada extremo y transversal por acceso
AVENIDA = 1000                 # por sentido, lo que entra por cada extremo de la avenida
TRANSVERSAL = {("C1", "S"): 1050, ("C2", "N"): 500, ("C3", "S"): 700, ("C4", "N"): 719, ("C4", "S"): 719,
               ("C5", "N"): 500, ("C5", "S"): 500, ("C6", "N"): 1009, ("C6", "S"): 1009}
SALE_DE_LA_AVENIDA = 0.05      # parte del flujo de un extremo que gira a la derecha en cada cruce donde se puede
GIRA_DE_TRANSVERSAL = 0.15     # parte de cada transversal que gira a la derecha (y a la izquierda, si es de un sentido)
PLAN_TIPICO = {"ciclo": 140, "transversal": 43}      # verde de la transversal; la avenida recibe el resto


def tramo(a, b):
    return f"{a}_{b}"


def vecino(k, paso):
    """Extremo o cruce contiguo a IDS[k] hacia el este (paso = 1) o el oeste (paso = -1)."""
    j = k + paso
    return "W" if j < 0 else "E" if j >= len(IDS) else IDS[j]


# ---------------- Red ----------------
def armar():
    plano = os.path.join(AQUI, "red")
    os.makedirs(plano, exist_ok=True)
    x = {c: px for c, _, px, _, _ in CRUCES}
    nodos = [("W", -ENTRADA, 0.0, None), ("E", x["C6"] + ENTRADA, 0.0, None)]
    aristas, conexiones = [], []
    for k, (c, calle, px, n, s) in enumerate(CRUCES):
        nodos += [(c, px, 0.0, f"semaforo_{c}"), (f"N{k + 1}", px, ENTRADA, None), (f"S{k + 1}", px, -ENTRADA, None)]
    for k in range(-1, len(IDS)):                       # tramos de avenida, los dos sentidos
        a = "W" if k < 0 else IDS[k]
        b = vecino(k, 1) if k >= 0 else IDS[0]
        nl = CARRILES_AV[a]
        aristas += [(tramo(a, b), a, b, nl, "avenida"), (tramo(b, a), b, a, nl, "avenida")]
    for k, (c, calle, px, n, s) in enumerate(CRUCES):   # transversales: accesos y salidas
        N, S = f"N{k + 1}", f"S{k + 1}"
        aristas.append((tramo(N, c), N, c, n or 1, calle if n else f"{calle}: acceso sin demanda"))
        aristas.append((tramo(S, c), S, c, s or 1, calle if s else f"{calle}: acceso sin demanda"))
        if n:
            aristas.append((tramo(c, S), c, S, n, calle))          # lo que viene del norte sale por el sur
        if s:
            aristas.append((tramo(c, N), c, N, s, calle))
    carriles = {e[0]: e[3] for e in aristas}
    for k, (c, calle, px, n, s) in enumerate(CRUCES):
        N, S = f"N{k + 1}", f"S{k + 1}"
        o, e = vecino(k, -1), vecino(k, 1)
        del_oeste, del_este, al_este, al_oeste = tramo(o, c), tramo(e, c), tramo(c, e), tramo(c, o)
        sale_sur, sale_norte = tramo(c, S), tramo(c, N)
        # avenida de frente; si el tramo siguiente tiene menos carriles, el carril derecho solo gira a la derecha
        for desde, hacia in ((del_oeste, al_este), (del_este, al_oeste)):
            de, a = carriles[desde], carriles[hacia]
            if de > a:
                conexiones += [(desde, hacia, i, i - (de - a)) for i in range(de - a, de)]
            else:
                conexiones += [(desde, hacia, i, i) for i in range(de)]
                conexiones += [(desde, hacia, de - 1, i) for i in range(de, a)]
        # giros a la derecha desde la avenida, donde la transversal sale hacia ese lado
        if sale_sur in carriles:
            conexiones.append((del_oeste, sale_sur, 0, 0))
        if sale_norte in carriles:
            conexiones.append((del_este, sale_norte, 0, 0))
        # transversales: de frente, giro a la derecha y, si la calle es de un solo sentido, giro a la izquierda
        un_sentido = not (n and s)
        if n:
            conexiones += [(tramo(N, c), sale_sur, i, i) for i in range(n)]
            conexiones.append((tramo(N, c), al_oeste, 0, 0))
            if un_sentido:
                conexiones.append((tramo(N, c), al_este, n - 1, carriles[al_este] - 1))
        else:
            conexiones.append((tramo(N, c), al_oeste, 0, 0))                # acceso sin demanda
        if s:
            conexiones += [(tramo(S, c), sale_norte, i, i) for i in range(s)]
            conexiones.append((tramo(S, c), al_este, 0, 0))
            if un_sentido:
                conexiones.append((tramo(S, c), al_oeste, s - 1, carriles[al_oeste] - 1))
        else:
            conexiones.append((tramo(S, c), al_este, 0, 0))                 # acceso sin demanda
    cab = '<?xml version="1.0" encoding="UTF-8"?>\n<!-- Generado por corredor.py. No editar a mano. -->\n'
    with open(os.path.join(plano, f"{ESC}.nod.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(cab + "<nodes>\n")
        for nid, px, py, tl in nodos:
            f.write(f'    <node id="{nid}" x="{px:.1f}" y="{py:.1f}" type="{"traffic_light" if tl else "priority"}"'
                    + (f' tl="{tl}"' if tl else "") + "/>\n")
        f.write("</nodes>\n")
    with open(os.path.join(plano, f"{ESC}.edg.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(cab + "<edges>\n")
        for eid, a, b, nl, nombre in aristas:
            f.write(f'    <edge id="{eid}" from="{a}" to="{b}" numLanes="{nl}" speed="{VEL}"/>  <!-- {nombre} -->\n')
        f.write("</edges>\n")
    with open(os.path.join(plano, f"{ESC}.con.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(cab + "<connections>\n")
        for desde, hacia, i, j in conexiones:
            f.write(f'    <connection from="{desde}" to="{hacia}" fromLane="{i}" toLane="{j}"/>\n')
        f.write("</connections>\n")
    r = subprocess.run(["netconvert", "--node-files", os.path.join(plano, f"{ESC}.nod.xml"),
                        "--edge-files", os.path.join(plano, f"{ESC}.edg.xml"),
                        "--connection-files", os.path.join(plano, f"{ESC}.con.xml"),
                        "--output-file", os.path.join(AQUI, f"{ESC}.net.xml"),
                        "--no-turnarounds", "--tls.default-type", "static"], capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-800:])
    print(f"{len(aristas)} aristas, {len(conexiones)} conexiones, {len(CRUCES)} cruces")
    return r.returncode


# ---------------- Programas de semaforo ----------------
_RED = {}


def red():
    if not _RED:
        import sumolib
        net = sumolib.net.readNet(os.path.join(AQUI, f"{ESC}.net.xml"), withPrograms=True, withInternal=False)
        for c in IDS:
            con = {}
            for cx in net.getNode(c).getConnections():
                if cx.getTLSID() == f"semaforo_{c}":
                    con[cx.getTLLinkIndex()] = cx
            _RED[c] = (net.getNode(c), con)
    return _RED


def estados(c):
    """(verde de la avenida, verde de la transversal): cadenas de estado del cruce c. Un enlace va con "g" solo si
    entra al mismo carril que otro enlace en verde y le cede el paso."""
    k = IDS.index(c)
    nodo, con = red()[c]
    avenida = {tramo(vecino(k, -1), c), tramo(vecino(k, 1), c)}
    res = []
    for de_avenida in (True, False):
        verdes = {i for i, cx in con.items() if (cx.getFrom().getID() in avenida) == de_avenida}
        letras = []
        for i in range(len(con)):
            if i not in verdes:
                letras.append("r")
                continue
            cede = any(j != i and con[j].getToLane().getID() == con[i].getToLane().getID()
                       and nodo.forbids(con[j], con[i]) for j in verdes)
            letras.append("g" if cede else "G")
        res.append("".join(letras))
    return res


def escribir_programa(ruta, ciclo, transversal, desfases=None, tipo="fijo", programa=None, comentario="",
                      maximos=None, parametros=None, coordinado=None):
    """Escribe el .add.xml de un control para los seis cruces.
    tipo "fijo": ciclo comun (s), verde de la transversal de cada cruce (lista o un numero) y desfase de cada cruce;
    la avenida recibe el resto del ciclo. tipo "actuado": control actuado de SUMO en cada cruce, con verde minimo
    de 10 s y maximos = [(avenida, transversal), ...] por cruce; parametros: {clave: valor} del actuado de SUMO.
    tipo "retraso": lo mismo con la variante de SUMO que decide por el retraso de los vehiculos (delay_based).
    coordinado (solo con tipo "actuado"): "avenida" o "fin fijo", las dos variantes coordinadas del segundo estudio
    (plan3/actuado.py) sobre el plan fijo dado por ciclo, transversal y desfases. El ciclo de SUMO se cuenta desde
    el inicio del verde de la transversal del plan fijo. "avenida": el verde de la avenida no termina antes de su
    fin en el plan fijo. "fin fijo": ademas termina exactamente ahi, y el de la transversal no pasa del suyo."""
    n = len(IDS)
    transversal = list(transversal) if isinstance(transversal, (list, tuple)) else [transversal] * n
    desfases = list(desfases) if desfases else [0] * n
    assert coordinado in (None, "avenida", "fin fijo") and (not coordinado or tipo == "actuado"), (tipo, coordinado)
    lineas = ["<additional>"]
    if comentario:
        lineas.append(f"    <!-- {comentario} -->")
    for k, c in enumerate(IDS):
        av, tr = estados(c)
        amb_av = "".join("y" if x in "Gg" else x for x in av)
        amb_tr = "".join("y" if x in "Gg" else x for x in tr)
        if tipo == "fijo":
            g_av = ciclo - 2 * AMBAR - transversal[k]
            assert g_av >= VERDE_MIN and transversal[k] >= VERDE_MIN, (c, ciclo, transversal[k])
            lineas += [f'    <tlLogic id="semaforo_{c}" type="static" programID="{programa or "fijo"}" '
                       f'offset="{int(desfases[k]) % int(ciclo)}">',
                       f'        <phase duration="{g_av}" state="{av}"/>',
                       f'        <phase duration="{AMBAR}" state="{amb_av}"/>',
                       f'        <phase duration="{transversal[k]}" state="{tr}"/>',
                       f'        <phase duration="{AMBAR}" state="{amb_tr}"/>', "    </tlLogic>"]
        elif coordinado:
            m_av, m_tr = maximos[k]
            fin_fijo = coordinado == "fin fijo"
            g_tr = transversal[k]
            g_av = ciclo - 2 * AMBAR - g_tr
            ref = g_av + AMBAR                       # inicio del verde de la transversal en el plan fijo
            # el verde maximo de la avenida no baja de lo que necesita para llegar a su fin: el ciclo entero con
            # fin fijo (su latestEnd lo corta igual); si no, su verde fijo mas lo que la transversal puede cortar
            m_av = max(m_av, ciclo if fin_fijo else g_av + max(0, g_tr - VERDE_MIN))
            fin_av = (g_av - ref) % ciclo            # fin del verde de la avenida, contado desde ref
            fin_tr = g_tr                            # fin del verde de la transversal, contado desde ref
            lineas.append(f'    <tlLogic id="semaforo_{c}" type="actuated" programID="{programa or "actuado"}" '
                          f'offset="{(int(desfases[k]) + ref) % int(ciclo)}">')
            lineas += [f'        <param key="{clave}" value="{valor}"/>' for clave, valor in (parametros or {}).items()]
            lineas += ['        <param key="coordinated" value="true"/>',
                       f'        <param key="cycleTime" value="{ciclo}"/>',
                       f'        <phase duration="{min(max(g_av, VERDE_MIN), m_av)}" minDur="{VERDE_MIN}" maxDur="{m_av}" '
                       f'state="{av}" earliestEnd="{fin_av}"' + (f' latestEnd="{fin_av}"' if fin_fijo else "") + "/>",
                       f'        <phase duration="{AMBAR}" state="{amb_av}"/>',
                       f'        <phase duration="{min(max(g_tr, VERDE_MIN), m_tr)}" minDur="{VERDE_MIN}" maxDur="{m_tr}" '
                       f'state="{tr}"' + (f' latestEnd="{fin_tr}"' if fin_fijo else "") + "/>",
                       f'        <phase duration="{AMBAR}" state="{amb_tr}"/>', "    </tlLogic>"]
        else:
            m_av, m_tr = maximos[k]
            clase = "delay_based" if tipo == "retraso" else "actuated"      # "retraso": la variante que decide por el retraso
            lineas.append(f'    <tlLogic id="semaforo_{c}" type="{clase}" programID="{programa or "actuado"}" offset="0">')
            lineas += [f'        <param key="{clave}" value="{valor}"/>' for clave, valor in (parametros or {}).items()]
            lineas += [f'        <phase duration="{VERDE_MIN}" minDur="{VERDE_MIN}" maxDur="{m_av}" state="{av}"/>',
                       f'        <phase duration="{AMBAR}" state="{amb_av}"/>',
                       f'        <phase duration="{VERDE_MIN}" minDur="{VERDE_MIN}" maxDur="{m_tr}" state="{tr}"/>',
                       f'        <phase duration="{AMBAR}" state="{amb_tr}"/>', "    </tlLogic>"]
    lineas.append("</additional>")
    tmp = f"{ruta}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas) + "\n")
    os.replace(tmp, ruta)


# ---------------- Demanda ----------------
def flujos():
    """{(id del flujo, arista de origen, arista de destino): veh/h}. Los de la avenida de punta a punta se llaman
    W_E y E_W (flujos_corredor del escenario)."""
    res = {}
    al_sur = [c for c, _, _, n, _ in CRUCES if n]          # cruces donde se puede girar a la derecha yendo al este
    al_norte = [c for c, _, _, _, s in CRUCES if s]        # idem yendo al oeste
    res[("W_E", "W_C1", "C6_E")] = AVENIDA * (1 - SALE_DE_LA_AVENIDA * len(al_sur))
    res[("E_W", "E_C6", "C1_W")] = AVENIDA * (1 - SALE_DE_LA_AVENIDA * len(al_norte))
    for c in al_sur:
        k = IDS.index(c) + 1
        res[(f"W_S{k}", "W_C1", f"{c}_S{k}")] = AVENIDA * SALE_DE_LA_AVENIDA
    for c in al_norte:
        k = IDS.index(c) + 1
        res[(f"E_N{k}", "E_C6", f"{c}_N{k}")] = AVENIDA * SALE_DE_LA_AVENIDA
    for k, (c, calle, px, n, s) in enumerate(CRUCES, start=1):
        un_sentido = not (n and s)
        giros = GIRA_DE_TRANSVERSAL * (2 if un_sentido else 1)
        if n:
            q = TRANSVERSAL[(c, "N")]
            res[(f"N{k}_S{k}", f"N{k}_{c}", f"{c}_S{k}")] = q * (1 - giros)
            res[(f"N{k}_W", f"N{k}_{c}", "C1_W")] = q * GIRA_DE_TRANSVERSAL
            if un_sentido:
                res[(f"N{k}_E", f"N{k}_{c}", "C6_E")] = q * GIRA_DE_TRANSVERSAL
        if s:
            q = TRANSVERSAL[(c, "S")]
            res[(f"S{k}_N{k}", f"S{k}_{c}", f"{c}_N{k}")] = q * (1 - giros)
            res[(f"S{k}_E", f"S{k}_{c}", "C6_E")] = q * GIRA_DE_TRANSVERSAL
            if un_sentido:
                res[(f"S{k}_W", f"S{k}_{c}", "C1_W")] = q * GIRA_DE_TRANSVERSAL
    return res


PUBLICADO = {"C1": 3390, "C4": 3778, "C6": 4358}      # veh/h, Plan de Movilidad Urbana de Miraflores 2017-2020


def totales_por_cruce():
    """{cruce: veh/h que entran al cruce} con la demanda de flujos(), para comparar con el volumen publicado."""
    total = {c: 0.0 for c in IDS}
    for (fid, desde, hacia), q in flujos().items():
        a = 0 if desde == "W_C1" else len(IDS) - 1 if desde == "E_C6" else IDS.index(desde.split("_")[1])
        b = len(IDS) - 1 if hacia == "C6_E" else 0 if hacia == "C1_W" else IDS.index(hacia.split("_")[0])
        for k in range(min(a, b), max(a, b) + 1):
            total[IDS[k]] += q
    return total


def escribir_demanda(factor=1.0, carpeta=AQUI):
    sys.path.insert(0, os.path.join(RAIZ, "plan3"))
    sys.path.insert(0, RAIZ)
    import demanda_estocastica as de            # la mezcla de vehiculos de Lima del segundo estudio
    os.makedirs(carpeta, exist_ok=True)
    lineas = ["<routes>", f"    <!-- Corredor de la Av. Benavides: demanda supuesta (corredor.py), factor {factor}; llegadas "
              "aleatorias; mezcla de vehiculos de Lima del segundo estudio -->", '    <vTypeDistribution id="auto">']
    lineas += [f'        <vType id="lima_{c}" {de.TIPOS[c]} {de.COMUNES} probability="{q:.6f}"/>'
               for c, q in de.composicion().items()]
    lineas.append("    </vTypeDistribution>")
    total = 0.0
    for p in range(4):                              # cuatro cuartos de hora, como los demas casos
        for (fid, desde, hacia), q in sorted(flujos().items()):
            tasa = q * factor
            total += tasa / 4
            lineas.append(f'    <flow id="p{p + 1}_{fid}" type="auto" from="{desde}" to="{hacia}" begin="{900 * p}" '
                          f'end="{900 * (p + 1)}" period="exp({tasa / 3600:.6f})" departLane="best"/>')
    lineas.append("</routes>")
    with open(os.path.join(carpeta, f"{ESC}.rou.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas) + "\n")
    with open(os.path.join(carpeta, f"{ESC}.sumocfg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"""<configuration>
    <input>
        <net-file value="{ESC}.net.xml"/>
        <route-files value="{ESC}.rou.xml"/>
        <additional-files value="{ESC}.add.xml"/>
    </input>
    <time>
        <begin value="0"/>
        <step-length value="1"/>
    </time>
    <processing>
        <time-to-teleport value="-1"/>
    </processing>
    <report>
        <no-step-log value="true"/>
        <no-warnings value="true"/>
    </report>
</configuration>
""")
    print(f"Demanda total que entra a la red: {total:.0f} veh/h (factor {factor})")
    entra = {}
    for (fid, desde, hacia), q in flujos().items():
        entra[desde] = entra.get(desde, 0.0) + q * factor
    print("Por entrada (veh/h):", ", ".join(f"{k} {v:.0f}" for k, v in sorted(entra.items())))
    print("Total que entra a cada cruce (veh/h; entre parentesis, el publicado):",
          ", ".join(f"{c} {v * factor:.0f}" + (f" ({PUBLICADO[c]})" if c in PUBLICADO else "")
                    for c, v in totales_por_cruce().items()))


def repartir(reparto):
    """Prueba de robustez: cambia el reparto de la demanda entre la avenida y las transversales, {"avenida": 1.2,
    "transversal": 0.8}, y devuelve el factor que deja el total como estaba."""
    global AVENIDA, TRANSVERSAL
    total = sum(flujos().values())
    AVENIDA = AVENIDA * reparto.get("avenida", 1.0)
    TRANSVERSAL = {k: q * reparto.get("transversal", 1.0) for k, q in TRANSVERSAL.items()}
    return total / sum(flujos().values())


def escribir_plan(carpeta):
    escribir_programa(os.path.join(carpeta, f"{ESC}.add.xml"), PLAN_TIPICO["ciclo"], PLAN_TIPICO["transversal"],
                      programa="tipico", comentario="Plan tipico SUPUESTO del corredor (corredor.py): ciclo "
                      f"{PLAN_TIPICO['ciclo']} s, transversal {PLAN_TIPICO['transversal']} s, sin desfases")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("accion", choices=["red", "plan", "demanda", "nivel"])
    ap.add_argument("--factor", type=float, default=1.0)
    ap.add_argument("--carpeta", default=AQUI)
    ap.add_argument("--reparto", default=None, help="(nivel) otro reparto con el mismo total: avenida=1.2,transversal=0.8")
    args = ap.parse_args()
    if args.accion == "red":
        return armar()
    if args.accion == "plan":
        escribir_plan(args.carpeta)
        for c in IDS:
            print(c, *estados(c))
        return 0
    if args.accion == "nivel":          # otro nivel de demanda en su carpeta: la misma red y el mismo plan tipico
        import shutil
        carpeta = os.path.abspath(args.carpeta)
        os.makedirs(carpeta, exist_ok=True)
        shutil.copyfile(os.path.join(AQUI, f"{ESC}.net.xml"), os.path.join(carpeta, f"{ESC}.net.xml"))
        escribir_plan(carpeta)
        factor = args.factor
        if args.reparto:
            factor *= repartir({k: float(v) for k, v in (x.split("=") for x in args.reparto.split(","))})
        escribir_demanda(factor, carpeta)
        return 0
    escribir_demanda(args.factor, args.carpeta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
