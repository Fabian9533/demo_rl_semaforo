"""
prueba_aleatorias.py - Las referencias con llegadas aleatorias y con el perfil, a traves del lanzador (tareas
0.7-0.10; la regla de A1 con llegadas aleatorias).
Arma en tmp_ref/aleatorias/ (sin versionar) una copia del corredor, poi_corredor (cada flow con
period="exp(q/3600)") y per_corredor (bloques de 600 s con llegadas de Poisson), y copias de los prototipos
plan3/demanda/guiones/con_escenarios.py, escenarios_plan3.py, generar_demanda.py y perfil_poisson.py (el registro
real lo escribe otro agente). Corre por el lanzador, con semillas de humo en lugar de 2001-2010 y 2001-2030:
  barrer_fino poi_corredor: gruesa (subrejilla), fina, desfases, desempate y fragil -> llegadas detectadas como
      aleatorias; a la fina pasan los minimos a <= 2 errores estandar; 10 finalistas con las semillas del
      desempate; la regla de fragiles no corre nada nuevo;
  franja poi_corredor: los 9 pares son finalistas (10 >= 9) con las semillas finales;
  barrer_fino per_corredor --bloque 600 y franja per_corredor --bloques: 6 puntajes por bloque, secuencia de bloques
      verificada y jugada por TraCI con la misma media;
  actuado poi_corredor --paso todos: 10 finalistas;  reglas poi_corredor --familia mp: 4 finalistas.
Las gruesas son subrejillas con semillas de humo (opciones de prueba): las etapas siguientes corren con
--permitir-prueba (sin el se niegan; eso lo prueba prueba_fino.py F).
Uso (cwd = plan3/): python pruebas/ref/prueba_aleatorias.py    Salida: pruebas/ref/salidas/prueba_aleatorias.txt
"""
import os
import sys
import csv
import json
import shutil
import statistics
import subprocess
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
inf = up.Informe("prueba_aleatorias")
PROTO = "C:/Users/GAMER/Documents/demo_rl_semaforo/analisis_mejora_2026-11-04/plan3/demanda/guiones"
CARPETA = up.copia("aleatorias", ["corredor"])
PERFIL = [1.0, 1.5, 2.0, 2.0, 1.5, 1.0]


def preparar_escenarios():
    for f in ("con_escenarios.py", "escenarios_plan3.py", "generar_demanda.py", "perfil_poisson.py"):
        shutil.copyfile(os.path.join(PROTO, f), os.path.join(CARPETA, f))
    with open("escenarios_plan3.py", "a", encoding="utf-8") as f:     # el perfil del corredor, solo en la copia
        f.write('\nESTOCASTICOS["per_corredor"] = ("corredor", "per_corredor.sumocfg", "corredor")\n')
    sys.path.insert(0, CARPETA)
    import generar_demanda
    import perfil_poisson
    with open("corredor.rou.xml", encoding="utf-8") as f:
        texto = f.read()
    with open("poi_corredor.rou.xml", "w", encoding="utf-8") as f:
        f.write(generar_demanda.rou_poisson(texto))
    generar_demanda.escribir_cfg(CARPETA, "corredor", "poi_corredor.sumocfg", "poi_corredor.rou.xml")
    with open("per_corredor.rou.xml", "w", encoding="utf-8") as f:
        f.write(perfil_poisson.rou_perfil_poisson("corredor.rou.xml", PERFIL))
    generar_demanda.escribir_cfg(CARPETA, "corredor", "per_corredor.sumocfg", "per_corredor.rou.xml")


def lanzar(script, *args):
    """python con_escenarios.py <plan3> <script sin .py> args, con la raiz del repositorio en PYTHONPATH."""
    env = dict(os.environ, PYTHONPATH=up.RAIZ)
    r = subprocess.run([sys.executable, "con_escenarios.py", up.PLAN3, script[:-3], *args], cwd=CARPETA, env=env,
                       capture_output=True, text=True)
    lineas = [x for x in r.stdout.split("\n") if x.strip()]
    inf.chequeo(r.returncode == 0, f"{script} {' '.join(args)}: codigo {r.returncode}; {lineas[-1] if lineas else ''}")
    if r.returncode != 0:
        inf(r.stdout[-2000:] + r.stderr[-3000:])
    return r.stdout


def leer_csv(rel):
    with open(os.path.join(CARPETA, rel), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def leer_json(rel):
    with open(os.path.join(CARPETA, rel), encoding="utf-8") as f:
        return json.load(f)


def main():
    inf(f"Referencias con llegadas aleatorias y perfil, por el lanzador (copia en {CARPETA})")
    preparar_escenarios()
    n = sum(1 for _ in ET.parse("poi_corredor.rou.xml").getroot().iter("flow"))
    inf(f"  poi_corredor: {n} flows con period=exp(); per_corredor: perfil {PERFIL} en bloques de 600 s")
    bar, des = ["--semillas", "424301-424305"], ["--semillas-desempate", "424301-424315",
                                                 "--semillas-fragil", "424301-424315"]
    out = lanzar("barrer_fino.py", "poi_corredor", "--etapa", "gruesa", "--procesos", "3", "--avenida", "18,20,25",
                 "--transversal", "10", *bar)
    inf.chequeo("llegadas aleatorias" in out, "poi_corredor: llegadas detectadas como aleatorias")
    for etapa in ("fina", "desfases", "desempate", "fragil"):
        out = lanzar("barrer_fino.py", "poi_corredor", "--etapa", etapa, "--procesos", "3", *bar, *des,
                     "--permitir-prueba")
    regiones = sorted({f["region"] for f in leer_csv("barridos/poi_corredor/fina.csv")})
    inf(f"  regiones de la fina (umbral de 2 errores estandar): {regiones}")
    d = leer_csv("barridos/poi_corredor/desempate.csv")
    fino = leer_json("barridos/poi_corredor/fijo_fino.json")
    inf.chequeo(len(d) == 10 and all(f["semillas"] == "424301-424315" for f in d) and fino["llegadas"] == "aleatorias",
                f"desempate: {len(d)} finalistas con {d[0]['semillas']}; fijo fino {fino['clave']} "
                f"{fino['retraso_total_prom']} ({fino['semillas']}), traza {fino['traza']}")
    lanzar("franja.py", "poi_corredor", "--procesos", "3", "--semillas", "424301-424305", "--semillas-final",
           "424301-424315", "--permitir-prueba")
    ff = leer_csv("barridos/poi_corredor/franja_final.csv")
    inf.chequeo(len(ff) == 9 and ff[0]["semillas"] == "424301-424315", f"franja: {len(ff)} finalistas (todos los "
                                                                         f"pares) con {ff[0]['semillas']}")
    # perfil: barrido con puntaje por bloque de 600 s y fijo por bloques
    lanzar("barrer_fino.py", "per_corredor", "--etapa", "gruesa", "--bloque", "600", "--procesos", "3", "--avenida",
           "20,25", "--transversal", "10", "--semillas", "424301-424303")
    for etapa in ("fina", "desfases"):
        lanzar("barrer_fino.py", "per_corredor", "--etapa", etapa, "--bloque", "600", "--procesos", "3",
               "--semillas", "424301-424303", "--permitir-prueba")
    g = leer_csv("barridos/per_corredor/gruesa.csv")
    inf.chequeo(all(f"total_p{k}" in g[0] for k in range(1, 7)) and "total_p7" not in g[0],
                "per_corredor: seis puntajes por bloque en el barrido (total_p1..total_p6)")
    lanzar("franja.py", "per_corredor", "--bloques", "--procesos", "3", "--semillas", "424301-424303",
           "--semillas-final", "424301-424310", "--permitir-prueba")
    bl = leer_json("barridos/per_corredor/bloques.json")
    inf(f"  bloques: {[(p['desde'], p['clave']) for p in bl['programas']]}, cambios {bl['instantes']} (reglas "
        f"{bl['cambios']['reglas']}, retraso maximo {bl['cambios']['retraso_maximo']} s); {bl['retraso_total_prom']} en "
        f"{bl['semillas']}; sin el fijo fino al lado (el perfil no corrio fragil): marca {bl['registro']['prueba']}")
    os.chdir(CARPETA)
    sys.path.insert(0, CARPETA)
    import escenarios_plan2 as ep
    import escenarios_plan3 as e3
    ep.DERIVADOS.update(e3.ESTOCASTICOS)            # como el lanzador, antes de importar evaluar
    import evaluar
    _, _, _, correr = evaluar.brazo_referencia("per_corredor", "bloques", "per_corredor_bloques.add.xml")
    vals = [float(correr(s, f"ti_bl_{s}.xml", None)["retraso_total_prom"]) for s in range(424301, 424311)]
    m = round(statistics.mean(vals), 2)
    inf.chequeo(m == bl["retraso_total_prom"], f"bloques jugado por TraCI (evaluar --brazo bloques): media {m} = "
                                               f"{bl['retraso_total_prom']}")
    lanzar("actuado.py", "poi_corredor", "--paso", "todos", "--procesos", "3", "--semillas", "424301-424302",
           "--semillas-final", "424301-424305", "--permitir-prueba")
    af = [f for f in leer_csv("barridos/poi_corredor/actuado_final.csv") if f["etapa"] == "final"]
    inf.chequeo(len(af) == 10 and af[0]["semillas"] == "424301-424305", f"actuado: {len(af)} finalistas con "
                                                                         f"{af[0]['semillas']}")
    lanzar("reglas.py", "poi_corredor", "--familia", "mp", "--semillas", "424301-424302", "--semillas-final",
           "424301-424303")
    rf = leer_csv("barridos/poi_corredor/reglas_mp_final.csv")
    inf.chequeo(len(rf) == 4, f"reglas mp: {len(rf)} finalistas (los 4, tope 10) con {rf[0]['semillas']}")
    os.chdir(up.PLAN3)
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
