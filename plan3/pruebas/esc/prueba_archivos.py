"""
prueba_archivos.py - Prueba 1 de los escenarios nuevos (y lo que se comprueba sin simular mucho):
  a. cada periodo de 30 min suma lo mismo que el caso regular (vehiculos esperados; en mix_ y mixa_, los mismos
     vehiculos equivalentes) y cada flow del caso conserva su total (en per_, juntando sus bloques con flujo_de);
  b. estructura: departLane="best" en todos los flows nuevos y en ninguno de los casos; poi_ con las mismas rutas,
     begin y end que el caso y tasa q/3600; malla3_alta_e = malla3_alta salvo departLane; mixa_ = mix_ salvo
     startupDelay; per_ ordenado por inicio; la mezcla suma 1;
  c. SUMO carga los 13 escenarios (300 s con avisos visibles; los casos al lado, para ver los mismos avisos);
  d. preparar3 --revisar sale con 0 y preparar3 en una copia escribe los mismos archivos (determinista);
  e. departLane="best" en los flows frente a --default.departlane best (P6 regular, semillas 424301-424303): las dos
     ven los mismos vehiculos y bajan la espera para entrar bajo 1 s/veh, pero en SUMO 1.25 eligen distinto el
     carril de entrada (se mide cuanto);
  f. sha256 de los .rou.xml de plan2/ al empezar (prueba_cierre.py los compara al final);
  g. los valores de SUMO 1.25 por clase (passenger, motorcycle, bus), leidos con TraCI, son los de la mezcla.
Uso (desde plan3/): python pruebas/esc/prueba_archivos.py      Salida: salidas/archivos.txt y sha_plan2_rou.txt
"""
import os
import re
import sys
import json
import shutil
import subprocess
import concurrent.futures as cf
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_esc as u                       # noqa: E402
import demanda_estocastica as de           # noqa: E402
import escenarios_plan3 as e3              # noqa: E402

p = u.Salida("archivos.txt")
fallas = []


def ok(cond, texto):
    p(("  ok    " if cond else "  FALLA ") + texto)
    if not cond:
        fallas.append(texto)


def ruta(nombre):
    return os.path.join(u.PLAN3, nombre)


def flows(nombre):
    return [dict(el.attrib) for el in ET.parse(ruta(nombre)).getroot().iter("flow")]


def parte_a():
    p("a. Demanda esperada por periodo y por flow frente al caso regular")
    for esc, (caso, llegadas, perfil, mezcla, arranque) in e3.RECETAS.items():
        f = de.equivalencia_media() if mezcla else 1.0
        c, n = de.por_periodo(ruta(f"{caso}.rou.xml")), de.por_periodo(ruta(f"{esc}.rou.xml"))
        dif = max(abs(n[k] * f - c[k]) for k in c)
        por_flow_caso = de.por_flow(ruta(f"{caso}.rou.xml"))
        juntos = {}
        for fid, v in de.por_flow(ruta(f"{esc}.rou.xml")).items():
            juntos[de.flujo_de(fid)] = juntos.get(de.flujo_de(fid), 0.0) + v * f
        dif_flow = max(abs(juntos.get(k, 0) - v) for k, v in por_flow_caso.items())
        equiv = f" (x {f:.4f} = {n[1] * f:.2f} y {n[2] * f:.2f} equivalentes)" if mezcla else ""
        ok(set(juntos) == set(por_flow_caso) and dif < 1e-6 and dif_flow < 1e-6 and set(n) == {1, 2},
           f"{esc:16s} periodo 1 {n[1]:8.2f}, periodo 2 {n[2]:8.2f} veh{equiv}; caso {caso} {c[1]:.0f} y "
           f"{c[2]:.0f}; dif. max. por periodo {dif:.1e}, por flow {dif_flow:.1e}")


def parte_b():
    p("b. Estructura de los archivos")
    for caso in sorted({r[0] for r in e3.RECETAS.values()}):
        ok(all("departLane" not in fl for fl in flows(f"{caso}.rou.xml")), f"{caso}.rou.xml sin departLane")
    for esc, (caso, llegadas, perfil, mezcla, arranque) in e3.RECETAS.items():
        nuevos, base = flows(f"{esc}.rou.xml"), flows(f"{caso}.rou.xml")
        ok(all(fl.get("departLane") == "best" for fl in nuevos), f"{esc}: departLane=best en los {len(nuevos)} flows")
        if llegadas == "poisson" and not perfil and not mezcla:
            igual = len(nuevos) == len(base) and all(
                all(a[k] == b[k] for k in ("id", "type", "from", "to", "begin", "end")) and
                abs(float(de.EXP.match(a["period"]).group(1)) * 3600 - float(b["vehsPerHour"])) < 1e-6
                for a, b in zip(nuevos, base))
            ok(igual, f"{esc}: mismos ids, rutas, begin y end que {caso}; tasa exp = vehsPerHour/3600")
        if perfil:
            inicios = [float(fl["begin"]) for fl in nuevos]
            ok(inicios == sorted(inicios) and len(nuevos) == 3 * len(base),
               f"{esc}: {len(nuevos)} flows (3 bloques por flow del caso), ordenados por inicio")
    a = flows("malla3_alta_e.rou.xml")
    b = flows("malla3_alta.rou.xml")
    ok([{k: v for k, v in fl.items() if k != "departLane"} for fl in a] == b,
       "malla3_alta_e: los flows de malla3_alta (mismos atributos) mas departLane=best")
    for caso in ("corredor", "red"):
        sin_comentario = [re.sub(r"<!--.*?-->", "", open(ruta(f"{pre}_{caso}.rou.xml"), encoding="utf-8").read(),
                                 count=1, flags=re.S) for pre in ("mix", "mixa")]
        ok(sin_comentario[0] == sin_comentario[1].replace(' startupDelay="0.5"', ""),
           f"mixa_{caso} = mix_{caso} salvo startupDelay=0.5 en los 5 tipos "
           f"({sin_comentario[1].count('startupDelay')} veces)")
        raiz = ET.parse(ruta(f"mix_{caso}.rou.xml")).getroot()
        probs = [float(t.get("probability")) for t in raiz.iter("vType")]
        ok(len(probs) == 5 and abs(sum(probs) - 1) < 1e-5 and raiz.find("vTypeDistribution").get("id") == "auto",
           f"mix_{caso}: vTypeDistribution 'auto' con 5 tipos que suman {sum(probs):.6f}")
    comp = de.composicion()
    eq = de.equivalencia_media()
    p("  composicion de la mezcla (%): " + ", ".join(f"{k} {v * 100:.3f}" for k, v in comp.items())
      + f"; vehiculos equivalentes por vehiculo {eq:.4f} -> demanda x {1 / eq:.4f}"
      + f" (con la moto en 0.5: x {1 / (eq - 0.5 * comp['moto']):.4f})")


def parte_c():
    p("c. SUMO carga los escenarios (semilla 424301, 300 s, avisos visibles)")
    casos = sorted({r[0] for r in e3.RECETAS.values()})

    def cargar(nombre):
        r = subprocess.run(["sumo", "-c", f"{nombre}.sumocfg", "--seed", "424301", "--end", "300",
                            "--no-warnings", "false", "--no-step-log", "true"],
                           cwd=u.PLAN3, capture_output=True, text=True)
        avisos = [l for l in r.stderr.splitlines() if l.startswith("Warning")]
        tipos = sorted({re.sub(r"'[^']*'|[-0-9.]+", "#", l)[:60] for l in avisos})
        return nombre, r.returncode, len(avisos), sum(1 for l in r.stderr.splitlines() if l.startswith("Error")), tipos

    with cf.ThreadPoolExecutor(u.MAX_SUMO) as pool:
        res = list(pool.map(cargar, casos + list(e3.ESTOCASTICOS)))
    for nombre, codigo, n_avisos, n_err, tipos in res:
        texto = f"{nombre:16s} codigo {codigo}, errores {n_err}, avisos {n_avisos}" + \
            (f": {'; '.join(tipos)}" if tipos else "")
        if nombre in casos:
            p("  (caso) " + texto)
        else:
            ok(codigo == 0 and n_err == 0, texto)


def parte_d():
    p("d. preparar3 es determinista y lo de disco esta al dia")
    r = subprocess.run([sys.executable, "demanda_estocastica.py", "preparar3", "--revisar"], cwd=u.PLAN3,
                       capture_output=True, text=True)
    ok(r.returncode == 0, f"preparar3 --revisar: codigo {r.returncode}; {r.stdout.strip()}")
    copia = os.path.join(u.TMP, "preparar_copia")
    shutil.rmtree(copia, ignore_errors=True)
    os.makedirs(copia)
    for caso in {rc[0] for rc in e3.RECETAS.values()}:
        for ext in (".rou.xml", ".sumocfg"):
            shutil.copyfile(ruta(caso + ext), os.path.join(copia, caso + ext))
    r = subprocess.run([sys.executable, "demanda_estocastica.py", "preparar3", "--carpeta", copia], cwd=u.PLAN3,
                       capture_output=True, text=True)
    iguales = [n for n in os.listdir(copia) if n.split(".")[0] in e3.RECETAS and
               open(os.path.join(copia, n), encoding="utf-8").read() == open(ruta(n), encoding="utf-8").read()]
    ok(r.returncode == 0 and len(iguales) == 2 * len(e3.RECETAS),
       f"preparar3 en una copia (tmp_esc/preparar_copia): {len(iguales)} de {2 * len(e3.RECETAS)} archivos "
       f"iguales a plan3/")


def parte_e():
    p("e. departLane=best en los flows frente a --default.departlane best (P6 regular, fijo instalado, semillas "
      "424301-424303)")
    p("  En SUMO 1.25 no son lo mismo: un vehiculo sin departLane hereda el 'best' de la opcion, pero "
      "MSEdge::getDepartLane elige entre getFreeLane y getProbableLane mirando el departLane propio del vehiculo "
      "(DEFAULT), asi que con la opcion entra por getProbableLane (el carril con mas hueco, como best_prob) y con el "
      "atributo por getFreeLane (el 'best' de la documentacion).")
    os.makedirs(os.path.join(u.TMP, "archivos"), exist_ok=True)
    variantes = {"flows": ("malla3_alta_e.sumocfg", []),
                 "opcion": ("malla3_alta.sumocfg", ["--default.departlane", "best"]),
                 "defecto": ("malla3_alta.sumocfg", [])}
    trabajos = [(n, s) for n in variantes for s in (424301, 424302, 424303)]
    with cf.ThreadPoolExecutor(u.MAX_SUMO) as pool:
        fut = {(n, s): pool.submit(u.correr_sumo, variantes[n][0], s,
                                   os.path.join(u.TMP, "archivos", f"tripinfo_p6_{n}_{s}.xml"), variantes[n][1])
               for n, s in trabajos}
        rutas = {k: f.result()[0] for k, f in fut.items()}
    filas = {k: [dict(v.attrib) for v in ET.parse(r).getroot().iter("tripinfo")] for k, r in rutas.items()}
    for s in (424301, 424302, 424303):
        a, b = u.leer_viajes(rutas[("flows", s)]), u.leer_viajes(rutas[("opcion", s)])
        c = u.comparar_llegadas(a, b)
        iguales = filas[("flows", s)] == filas[("opcion", s)]
        ok(c["solo_uno"] == 0 and c["deseada_distinta"] == 0 and c["sf_distinto"] == 0,
           f"semilla {s}: las dos variantes ven los mismos vehiculos, salidas pedidas y speedFactor; tripinfo "
           f"{'identico' if iguales else 'distinto (cambia el carril de entrada y con el el trafico)'}")
    medias = {}
    for n in variantes:
        vs = [v for s in (424301, 424302, 424303) for v in filas[(n, s)]]
        medias[n] = {m: sum(float(v[m]) for v in vs) / len(vs) for m in ("departDelay", "timeLoss")}
        carril0 = sum(1 for v in vs if v["departLane"].endswith("_0")) / len(vs)
        p(f"  {n:8s} espera para entrar {medias[n]['departDelay']:6.2f} s/veh, timeLoss {medias[n]['timeLoss']:6.2f} "
          f"s/veh, retraso total {medias[n]['departDelay'] + medias[n]['timeLoss']:6.2f}; entra por el carril 0 el "
          f"{carril0 * 100:.1f} % (media de 3 semillas)")
    ok(medias["flows"]["departDelay"] < 1 and medias["opcion"]["departDelay"] < 1,
       "con las dos formas de 'best' la espera para entrar de P6 queda bajo 1 s/veh")


def parte_g():
    p("g. Valores por defecto de SUMO 1.25 por clase (leidos con TraCI) frente a los vType de la mezcla")
    import traci
    rou = os.path.join(u.TMP, "archivos", "clases.rou.xml")
    os.makedirs(os.path.dirname(rou), exist_ok=True)
    clases = ("passenger", "motorcycle", "bus")
    with open(rou, "w", encoding="utf-8") as f:
        f.write("<routes>\n" + "".join(f'    <vType id="{c}" vClass="{c}"/>\n' for c in clases) + "</routes>\n")
    traci.start(["sumo", "-n", "corredor.net.xml", "-r", rou, "--end", "1", "--no-step-log", "true"],
                label="clases")
    vt = traci.getConnection("clases").vehicletype
    medido = {c: {"length": vt.getLength(c), "accel": vt.getAccel(c), "decel": vt.getDecel(c),
                  "minGap": vt.getMinGap(c), "sigma": vt.getImperfection(c), "speedDev": vt.getSpeedDeviation(c),
                  "emergencyDecel": vt.getEmergencyDecel(c), "maxSpeed": round(vt.getMaxSpeed(c), 2),
                  "emision": vt.getEmissionClass(c)} for c in clases}
    traci.getConnection("clases").close()
    for clase, vclase in (("auto", "passenger"), ("moto", "motorcycle"), ("bus", "bus")):
        attrs = dict(re.findall(r'(\w+)="([^"]+)"', de.TIPOS[clase]))
        iguales = all(abs(float(attrs[k]) - medido[vclase][k]) < 1e-9 for k in ("length", "accel", "decel"))
        ok(iguales, f"{clase}: largo {attrs['length']}, accel {attrs['accel']}, decel {attrs['decel']} = los de la "
                    f"clase {vclase} de SUMO")
    for vclase in clases:
        resto = ", ".join(f"{k} {v}" for k, v in medido[vclase].items() if k not in ("length", "accel", "decel"))
        p(f"  {vclase:10s} lo que la mezcla toma de la clase: {resto}")


def main():
    os.chdir(u.PLAN3)
    shas = u.sha_plan2_rou()
    with open(os.path.join(u.SALIDAS, "sha_plan2_rou.txt"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(shas, f, indent=1, sort_keys=True)
    p(f"f. sha256 de {len(shas)} .rou.xml de plan2/ guardados en salidas/sha_plan2_rou.txt")
    parte_a()
    parte_b()
    parte_c()
    parte_d()
    parte_e()
    parte_g()
    p(f"\nResultado: {'TODO OK' if not fallas else f'{len(fallas)} FALLAS'}")
    p.guardar()
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
