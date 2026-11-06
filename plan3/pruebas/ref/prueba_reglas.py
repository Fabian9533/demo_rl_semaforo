"""
prueba_reglas.py - Pruebas de la tarea 0.10 (reglas.py y evaluar.py --regla):
  1. con U = inf (regla_uinfg60) el mismo tripinfo que el ciclo minimo (brazo trivial), registro por registro
     (sha256), en P1 y P5;
  2. cada accion respeta la mascara (registro de todas las decisiones de un episodio de cada familia en P1 y P6);
  3. la presion es 0 con la red vacia (todas las fases de todos los semaforos, antes del primer paso) y no es 0 con
     trafico;
  4. evaluar.py --regla por la linea de comandos escribe su CSV con el brazo esperado;
  5. la regla reactiva: sus nombres (reactiva_d15 a reactiva_d70), la mascara y la logica (con la mascara libre
     alarga si y solo si hay un vehiculo a <= D m en un carril con verde), el mismo tripinfo que la logica del
     prototipo (reloj_reactivo.py, copiada aqui) por el mismo rl_ippo.correr_episodio en P1 y P6, el barrido
     --familia reactiva (reglas_reactiva.csv, reglas_reactiva_final.csv y reactiva.json con la ganadora y la marca de
     prueba) y evaluar.py --regla reactiva_d25;
  6. protecciones de evaluar.py: adicional solo con franja, bloques y actuado_aj; nada de plan3 (ni trivial) en cruce
     ni cruce2; --semillas obligatorio con los brazos de plan3 (sin el se usaria 1001-1030);
  7. la reactiva frente a un oraculo independiente (traci.vehicle.getNextTLS: con la mascara libre alarga si y solo
     si algun vehiculo cuyo proximo semaforo es este esta a <= D m de su linea con su propio enlace en G o g) y su
     reloj: cada verde dura 10-60 s en pasos de 5 s, la decision siguiente llega 5 s despues de alargar y 8 s despues
     de cambiar (3 de ambar), nunca en ambar (P1 con D 25 y P6 con D 50);
  8. la huella de la cache de las reglas cambia si cambia rl_ippo.py, rl_corredor.py, reglas.py, escenarios_plan3.py
     o con_escenarios.py (con copias cambiadas, sin tocar los de verdad).
Semillas de humo. Corre en una copia de los escenarios (tmp_ref/reglas/): el brazo trivial regenera su .add.xml en la
carpeta actual. Uso (cwd = plan3/): python pruebas/ref/prueba_reglas.py
Salida: pruebas/ref/salidas/prueba_reglas.txt
"""
import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
inf = up.Informe("prueba_reglas")
CARPETA = up.copia("reglas", ["corredor", "malla3", "malla3_alta"])
import traci  # noqa: E402
import rl_ippo  # noqa: E402
import evaluar  # noqa: E402
import reglas  # noqa: E402


def igual_ciclo_minimo(esc, semilla):
    _, _, _, trivial = evaluar.brazo_referencia(esc, "trivial")
    a = trivial(semilla, f"ti_trivial_{esc}.xml", None)
    brazo, _, _, regla = evaluar.brazo_regla(esc, "regla_uinfg60")
    b = regla(semilla, f"ti_regla_{esc}.xml", None)
    ha, hb = up.huella_tripinfo(f"ti_trivial_{esc}.xml"), up.huella_tripinfo(f"ti_regla_{esc}.xml")
    inf.chequeo(ha == hb and a["retraso_total_prom"] == b["retraso_total_prom"],
                f"1 {esc} s{semilla}: {brazo} tripinfo {hb} = ciclo minimo {ha}; retraso total "
                f"{b['retraso_total_prom']} = {a['retraso_total_prom']}, timeLoss {b['timeloss_prom']} = "
                f"{a['timeloss_prom']}")


def mascara(esc, regla, semilla):
    rl_ippo.preparar(esc)
    registro = []
    res = reglas.correr(esc, regla, semilla, f"ti_masc_{esc}_{regla}.xml", registro=registro)
    malas = [r for r in registro if (r[2][r[3]] == 0)]
    libres = sum(1 for r in registro if r[2] == (1.0, 1.0))
    forzadas = sum(1 for r in registro if r[2] == (0.0, 1.0))
    cambios = sum(r[3] for r in registro)
    inf.chequeo(not malas and registro, f"2 {esc} {regla}: {len(registro)} decisiones ({libres} libres, {forzadas} "
                                        f"forzadas por el verde maximo, {cambios} cambios), fuera de la mascara: "
                                        f"{len(malas)}; retraso total {res['retraso_total_prom']}")


def presion_vacia(esc, semilla):
    rl_ippo.preparar(esc)
    cfg = rl_ippo.C["cfg"]
    traci.start(["sumo", "-c", cfg, "--seed", str(semilla), "--no-step-log", "true", "--no-warnings", "true",
                 "--tripinfo-output", f"ti_pres_{esc}.xml"])
    geo = reglas.Geometria()
    geo.preparar()
    vacias = {(tls, f, m): reglas.presion(geo, tls, f, m) for tls in geo.verdes for f in geo.verdes[tls]
              for m in ("veh", "det")}
    n0 = traci.vehicle.getIDCount()
    for _ in range(900):
        traci.simulationStep()
    llenas = {(tls, f, m): reglas.presion(geo, tls, f, m) for tls in geo.verdes for f in geo.verdes[tls]
              for m in ("veh", "det")}
    n1 = traci.vehicle.getIDCount()
    traci.close()
    inf.chequeo(n0 == 0 and all(v == 0 for v in vacias.values()),
                f"3 {esc}: red vacia ({n0} vehiculos): presion 0 en las {len(vacias)} (semaforo, fase, medida)")
    inf.chequeo(any(v != 0 for v in llenas.values()),
                f"3 {esc}: a los 900 s ({n1} vehiculos) la presion no es 0 en "
                f"{sum(1 for v in llenas.values() if v != 0)} de {len(llenas)}")


def linea_de_comandos():
    salida = os.path.join(CARPETA, "eval_corredor_regla.csv")
    r = subprocess.run([sys.executable, os.path.join(up.RAIZ, "evaluar.py"), "--escenario", "corredor", "--regla",
                        "regla_u2g30", "--semillas", f"{up.HUMO[0]}-{up.HUMO[1]}", "--salida", salida,
                        "--extras", os.path.join(CARPETA, "extras")], capture_output=True, text=True)
    import csv
    filas = list(csv.DictReader(open(salida, encoding="utf-8"))) if os.path.exists(salida) else []
    resumen = [(f["brazo"], f["semilla"], f["retraso_total_prom"]) for f in filas]
    inf.chequeo(r.returncode == 0 and [f["brazo"] for f in filas] == ["regla_u2g30"] * 2,
                f"4 evaluar.py --regla regla_u2g30: codigo {r.returncode}, filas {resumen}")
    r = subprocess.run([sys.executable, os.path.join(up.RAIZ, "evaluar.py"), "--escenario", "corredor", "--regla",
                        "regla_x", "--semillas", str(up.HUMO[0])], capture_output=True, text=True)
    inf.chequeo(r.returncode != 0, f"4 una regla desconocida se rechaza (codigo {r.returncode})")


def decidir_prototipo(d):
    """La logica de analisis_mejora_2026-11-04/plan3/critica_resultados/reloj_reactivo.py (hacer_decidir), copiada."""
    cache = {}

    def carriles_verdes(tls):
        estado = traci.trafficlight.getRedYellowGreenState(tls)
        if tls not in cache:
            cache[tls] = traci.trafficlight.getControlledLinks(tls)
        links = cache[tls]
        return {links[k][0][0] for k, c in enumerate(estado) if c in "Gg" and links[k]}

    def hay_cerca(carril):
        largo = traci.lane.getLength(carril)
        for v in traci.lane.getLastStepVehicleIDs(carril):
            if largo - traci.vehicle.getLanePosition(v) <= d:
                return True
        return False

    def decidir(deciden, obs, masc, modo, info):
        acciones = []
        for k, tls in enumerate(deciden):
            m = masc[k]
            if m[1] == 0:
                acciones.append(0)
                continue
            if m[0] == 0:
                acciones.append(1)
                continue
            acciones.append(0 if any(hay_cerca(c) for c in carriles_verdes(tls)) else 1)
        return acciones, [None] * len(deciden)
    return decidir


def reactiva(esc, d, semilla):
    rl_ippo.preparar(esc)
    registro = []
    res = reglas.correr(esc, f"reactiva_d{d}", semilla, f"ti_reac_{esc}.xml", registro=registro)
    malas = [r for r in registro if r[2][r[3]] == 0]
    libres = [r for r in registro if r[2] == (1.0, 1.0)]
    incoherentes = [r for r in libres if (r[3] == 0) != bool(r[4])]
    alarga = sum(1 for r in libres if r[3] == 0)
    inf.chequeo(registro and not malas and libres and not incoherentes,
                f"5 {esc} reactiva_d{d}: {len(registro)} decisiones ({len(libres)} libres: alarga {alarga}, cambia "
                f"{len(libres) - alarga}), fuera de la mascara {len(malas)}, con la mascara libre alarga si y solo si "
                f"hay un vehiculo a <= {d} m en un carril con verde: {not incoherentes}; retraso total "
                f"{res['retraso_total_prom']}, cambios de fase {res['cambios_fase']}")
    proto = rl_ippo.correr_episodio("demo", None, False, 0, semilla, tripinfo=f"ti_proto_{esc}.xml",
                                    variante="local", decidir=decidir_prototipo(d))
    ha, hb = up.huella_tripinfo(f"ti_reac_{esc}.xml"), up.huella_tripinfo(f"ti_proto_{esc}.xml")
    inf.chequeo(ha == hb and res["retraso_total_prom"] == proto["retraso_total_prom"]
                and res["cambios_fase"] == proto["cambios_fase"],
                f"5 {esc} reactiva_d{d} = logica del prototipo por el mismo bucle: tripinfo {ha} = {hb}; retraso total "
                f"{res['retraso_total_prom']} = {proto['retraso_total_prom']}")


def reactiva_nombres_y_barrido():
    ok = all(reglas.validar(r) == {"tipo": "reactiva", "d": int(r.split("_d")[1])} for r in reglas.REACTIVAS)
    rechazadas = []
    for malo in ("reactiva_d", "reactiva_dx", "reactiva25", "reactiva_d25_c60", "reactiva_d26", "reactiva_d025",
                 "reactiva_d25\n"):
        try:
            reglas.validar(malo)
        except SystemExit:
            rechazadas.append(malo)
    inf.chequeo(ok and reglas.REACTIVAS == [f"reactiva_d{d}" for d in (15, 25, 35, 50, 70)]
                and len(rechazadas) == 7 and set(reglas.FAMILIAS) == {"regla", "reactiva", "mp"},
                f"5 nombres: {reglas.REACTIVAS} validos; rechazados {rechazadas}; familias {list(reglas.FAMILIAS)}")
    r = subprocess.run([sys.executable, os.path.join(up.PLAN3, "reglas.py"), "corredor", "--familia", "reactiva",
                        "--semillas", str(up.HUMO[0]), "--semillas-final", f"{up.HUMO[0]}-{up.HUMO[1]}"],
                       cwd=CARPETA, capture_output=True, text=True)
    import csv
    import json
    b = os.path.join(CARPETA, "barridos", "corredor")
    salidas = [os.path.join(b, f) for f in ("reglas_reactiva.csv", "reglas_reactiva_final.csv",
                                            "reglas_reactiva_semillas.csv", "reactiva.json")]
    hay = all(os.path.exists(s) for s in salidas)
    filas = list(csv.DictReader(open(salidas[0], encoding="utf-8"))) if hay else []
    finales = list(csv.DictReader(open(salidas[1], encoding="utf-8"))) if hay else []
    datos = json.load(open(salidas[3], encoding="utf-8")) if hay else {}
    inf.chequeo(r.returncode == 0 and hay and sorted(f["regla"] for f in filas) == sorted(reglas.REACTIVAS)
                and len(finales) == 3 and datos.get("regla") == finales[0]["regla"]
                and datos.get("familia") == "reactiva" and datos["registro"]["prueba"],
                f"5 reglas.py corredor --familia reactiva (humo): codigo {r.returncode}; 5 reglas, 3 finalistas, "
                f"reactiva.json gana {datos.get('regla')} {datos.get('retraso_total_prom')} ({datos.get('semillas')}), "
                f"marca de prueba {datos.get('registro', {}).get('prueba')}")
    if r.returncode != 0:
        inf(r.stdout[-1500:] + r.stderr[-1500:])
    salida = os.path.join(CARPETA, "eval_corredor_reactiva.csv")
    r = subprocess.run([sys.executable, os.path.join(up.RAIZ, "evaluar.py"), "--escenario", "corredor", "--regla",
                        "reactiva_d25", "--semillas", str(up.HUMO[0]), "--salida", salida, "--extras",
                        os.path.join(CARPETA, "extras_reac")], capture_output=True, text=True)
    filas = list(csv.DictReader(open(salida, encoding="utf-8"))) if os.path.exists(salida) else []
    inf.chequeo(r.returncode == 0 and [f["brazo"] for f in filas] == ["reactiva_d25"],
                f"5 evaluar.py --regla reactiva_d25: codigo {r.returncode}, filas "
                f"{[(f['brazo'], f['semilla'], f['retraso_total_prom']) for f in filas]}")


def protecciones_evaluar():
    casos = []
    for nombre, llamada in (
            ("brazo_referencia(corredor, fijo, adicional)",
             lambda: evaluar.brazo_referencia("corredor", "fijo", adicional="corredor_r10f.add.xml")),
            ("brazo_referencia(corredor, actuado, adicional)",
             lambda: evaluar.brazo_referencia("corredor", "actuado", adicional="x.add.xml")),
            ("brazo_referencia(corredor, trivial, adicional)",
             lambda: evaluar.brazo_referencia("corredor", "trivial", adicional="x.add.xml")),
            ("brazo_referencia(cruce, franja)", lambda: evaluar.brazo_referencia("cruce", "franja")),
            ("brazo_referencia(cruce2, actuado_aj)", lambda: evaluar.brazo_referencia("cruce2", "actuado_aj")),
            ("brazo_programa(cruce, ...)", lambda: evaluar.brazo_programa("cruce", "x.add.xml", "fino")),
            ("brazo_regla(cruce2, mp)", lambda: evaluar.brazo_regla("cruce2", "mp")),
            ("brazo_referencia(cruce, trivial)", lambda: evaluar.brazo_referencia("cruce", "trivial"))):
        try:
            llamada()
            casos.append((nombre, "aceptada"))
        except SystemExit:
            casos.append((nombre, "rechazada"))
    _, _, _, ok_franja = evaluar.brazo_referencia("corredor", "franja", adicional="corredor_franja.add.xml")
    inf.chequeo(all(r == "rechazada" for _, r in casos) and callable(ok_franja),
                f"6 API de evaluar.py: {casos}; brazo_referencia(corredor, franja, adicional) sigue valiendo")
    codigos = []
    for args in (["--brazo", "franja"], ["--brazo", "actuado_aj"], ["--brazo", "fijo", "--programa", "x.add.xml",
                                                                    "--nombre", "fino"], ["--regla", "mp"]):
        r = subprocess.run([sys.executable, os.path.join(up.RAIZ, "evaluar.py"), "--escenario", "corredor", *args],
                           cwd=CARPETA, capture_output=True, text=True)
        codigos.append((" ".join(args), r.returncode, "--semillas es obligatorio" in r.stderr))
    inf.chequeo(all(c == 2 and m for _, c, m in codigos),
                f"6 linea de comandos sin --semillas (se usaria 1001-1030): {codigos}")


def oraculo(esc, d, semilla):
    """La reactiva frente a un oraculo hecho con getNextTLS (otra forma de medir la distancia a la linea y el verde:
    la del propio vehiculo) y el reloj de sus decisiones."""
    rl_ippo.preparar(esc)
    registro, comparaciones = [], []
    regla = reglas.hacer_decidir(f"reactiva_d{d}", registro)

    def decidir(deciden, obs, masc, modo, info):
        acciones, extras = regla(deciden, obs, masc, modo, info)
        cerca = set()
        for v in traci.vehicle.getIDList():
            prox = traci.vehicle.getNextTLS(v)
            if prox and prox[0][2] <= d and prox[0][3] in "Gg":
                cerca.add(prox[0][0])
        for k, tls in enumerate(deciden):
            if masc[k][0] > 0 and masc[k][1] > 0:
                comparaciones.append((tls, info["t"], 0 if tls in cerca else 1, int(acciones[k])))
        return acciones, extras
    rl_ippo.correr_episodio("demo", None, False, 0, semilla, tripinfo=f"ti_oraculo_{esc}.xml", variante="local",
                            decidir=decidir)
    distintas = [x for x in comparaciones if x[2] != x[3]]
    reloj_malo, verdes = [], []
    for tls in {r[1] for r in registro}:
        mias = sorted((r[0], r[3], r[2]) for r in registro if r[1] == tls)
        largo = 5                                          # la primera decision de cada verde llega a los 5 s
        for (t0, a0, m0), (t1, a1, m1) in zip(mias, mias[1:]):
            esperado = 8 if a0 == 1 else 5
            if t1 - t0 != esperado:
                reloj_malo.append((tls, t0, a0, t1))
            if a0 == 1:
                verdes.append(largo)
                largo = 5
            else:
                largo += 5
    fuera = sorted({v for v in verdes if v not in range(10, 61, 5)})
    inf.chequeo(comparaciones and not distintas and not reloj_malo and not fuera,
                f"7 {esc} reactiva_d{d} frente al oraculo getNextTLS: {len(comparaciones)} decisiones libres, "
                f"distintas {len(distintas)} {distintas[:2]}; reloj: {len(registro)} decisiones, separaciones fuera de "
                f"5 s (tras alargar) u 8 s (tras cambiar): {len(reloj_malo)} {reloj_malo[:2]}; {len(verdes)} verdes, "
                f"todos de 10-60 s en pasos de 5: {not fuera} {fuera[:3]}")


def huella_reglas():
    """La huella de las reglas cambia con cada archivo de codigo que la forma (con copias cambiadas)."""
    import shutil
    import rl_corredor
    import barrer_fino as bfn
    base = reglas.codigo_de_reglas(rl_ippo, rl_corredor)
    cfg = "corredor.sumocfg"
    h0 = bfn.huella_escenario(cfg, codigo=base)
    cambian = {}
    carpeta = os.path.join(CARPETA, "huella_reglas")
    os.makedirs(carpeta, exist_ok=True)
    for i, ruta in enumerate(base):
        copia_ruta = os.path.join(carpeta, os.path.basename(ruta))
        shutil.copyfile(ruta, copia_ruta)
        with open(copia_ruta, "a", encoding="utf-8") as f:
            f.write("# cambio de prueba (prueba_reglas 8)" + os.linesep)
        cambiadas = base[:i] + [copia_ruta] + base[i + 1:]
        cambian[os.path.basename(ruta)] = bfn.huella_escenario(cfg, codigo=cambiadas) != h0
    nombres = {os.path.basename(r) for r in base}
    inf.chequeo(all(cambian.values()) and {"rl_ippo.py", "rl_corredor.py", "reglas.py", "escenarios_plan3.py",
                                           "con_escenarios.py"} <= nombres,
                f"8 huella de las reglas ({h0}): cambia con cada archivo {cambian}")


def main():
    inf(f"Pruebas de 0.10: regla simple, reactiva y Max-Pressure por el gancho decidir (copia en {CARPETA})")
    for esc in ("corredor", "malla3"):
        igual_ciclo_minimo(esc, up.HUMO[0])
    for regla in ("regla_u2g30", "regla_u6g60", "mp", "mp_det", "mp_c60", "mp_det_c90"):
        mascara("corredor", regla, up.HUMO[0])
    for regla in ("regla_u1g30", "mp_c90"):
        mascara("malla3_alta", regla, up.HUMO[0])
    presion_vacia("corredor", up.HUMO[0])
    presion_vacia("malla3_alta", up.HUMO[0])
    linea_de_comandos()
    reactiva_nombres_y_barrido()
    reactiva("corredor", 25, up.HUMO[0])
    reactiva("malla3_alta", 50, up.HUMO[0])
    protecciones_evaluar()
    oraculo("corredor", 25, up.HUMO[0])
    oraculo("malla3_alta", 50, up.HUMO[0])
    huella_reglas()
    os.chdir(up.PLAN3)
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
