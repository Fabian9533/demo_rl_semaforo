"""
calibrar_demanda.py - Elige el factor de demanda de un caso de estres del plan de pruebas (P6).

Uso (desde demo_rl/plan2, con los archivos del escenario base en el cwd):
  python ../calibrar_demanda.py malla3 --nuevo malla3_alta [--factores 1.5,2.0,2.5,3.0]
         [--semillas 2001-2003] [--procesos 3] [--escribir]

Criterio (el mismo con que se eligieron corredor_alta y red_alta, CLAUDE.md U4 y cabecera de
red_alta.rou.xml): con el control actuado y las semillas de tuneo 2001-2003, el menor factor f de
la lista en que la cola detenida de algun carril de un enlace entre semaforos llega al 90 % de sus
plazas (hay spillback segun comun.MedidorEnlaces) en al menos 2 de 3 semillas, sin mas del 10 % de
vehiculos sin terminar a los 6000 pasos. Se reporta ademas la espera para entrar a la red y el
retraso total (comun.leer_tripinfo), parte de la metrica primaria.

Para cada f escribe en el cwd calib_<nuevo>_fNNN.rou.xml (cada vehsPerHour x f) y su .sumocfg,
corre el actuado de rl_corredor con cada semilla y al final los borra. Con --escribir deja en
demo_rl/ (la carpeta de este script) <nuevo>.rou.xml con el f elegido y la tabla por factor en la
cabecera, <nuevo>.sumocfg y <nuevo>.add.xml (copia del fijo del caso base; el barrido lo reemplaza
en plan2/). El escenario nuevo se registra aparte en escenarios_plan2.py.
"""
import os
import re
import sys
import shutil
import argparse
import concurrent.futures
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)


def escalar_rou(origen, destino, f, comentario=None):
    """Copia un .rou.xml multiplicando cada vehsPerHour por f (redondeado a entero)."""
    with open(origen, encoding="utf-8") as fh:
        texto = fh.read()
    texto = re.sub(r'vehsPerHour="([0-9.]+)"',
                   lambda m: 'vehsPerHour="%d"' % round(float(m.group(1)) * f), texto)
    if comentario:
        texto = texto.replace("<routes>", "<routes>\n    <!-- " + comentario + " -->", 1)
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(texto)


def escribir_cfg(cfg_base, destino, rou, add=None):
    """Copia un .sumocfg cambiando el archivo de rutas (y el additional, si se da)."""
    arbol = ET.parse(cfg_base)
    arbol.getroot().find(".//route-files").set("value", rou)
    if add is not None:
        arbol.getroot().find(".//additional-files").set("value", add)
    arbol.write(destino, encoding="unicode")


def correr(base, cfg, semilla):
    """Una corrida del actuado en un proceso aparte (rl_corredor usa variables globales y TraCI)."""
    import comun
    import rl_corredor
    esc = cfg[:-len(".sumocfg")]
    rl_corredor.ESCENARIOS[esc] = {**rl_corredor.ESCENARIOS[base], "cfg": cfg}
    rl_corredor.ESCENARIO, rl_corredor.CFG = esc, cfg
    rl_corredor.SEMAFOROS = rl_corredor.ESCENARIOS[base]["semaforos"]
    rl_corredor.ENLACES = rl_corredor.ESCENARIOS[base]["enlaces"]
    rl_corredor.FLUJOS_CORREDOR = rl_corredor.ESCENARIOS[base]["flujos_corredor"]
    tripinfo = f"{esc}_s{semilla}_tripinfo.xml"
    res = rl_corredor.correr_episodio("actuado", {}, 0.0, False, 0, semilla, tripinfo=tripinfo)
    comun.borrar_tripinfo(tripinfo)
    return res


def rango(texto):
    a, b = (texto.split("-") + [texto])[:2]
    return list(range(int(a), int(b) + 1))


def linea(f, rs, marca):
    """Una fila de la tabla por factor."""
    con_spill = sum(1 for r in rs if r["spillback_eventos"] > 0)
    sin_terminar = max(r["no_terminados"] / max(1, r["vehiculos"]) for r in rs)
    colas = "/".join(str(r["cola_max_enlace"]) for r in rs)
    perdida = " / ".join("%.1f" % r["timeloss_prom"] for r in rs)
    total = " / ".join("%.1f" % r["retraso_total_prom"] for r in rs)
    entrar = max(r["retraso_insercion_prom"] for r in rs)
    return (f"{f:4.2f}  {con_spill}/{len(rs)}  {colas:>11}  {sin_terminar * 100:5.1f} %  {perdida:>20}  "
            f"{total:>20}  {entrar:6.1f} s{marca}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base", help="escenario base (sus archivos en el cwd), p. ej. malla3")
    ap.add_argument("--nuevo", required=True, help="nombre del caso de estres, p. ej. malla3_alta")
    ap.add_argument("--factores", default="1.5,2.0,2.5,3.0")
    ap.add_argument("--semillas", default="2001-2003")
    ap.add_argument("--procesos", type=int, default=3)
    ap.add_argument("--escribir", action="store_true", help="escribe el caso elegido en demo_rl/")
    args = ap.parse_args()
    factores = [float(x) for x in args.factores.split(",")]
    semillas = rango(args.semillas)
    cfg_base = f"{args.base}.sumocfg"
    rou_base = ET.parse(cfg_base).getroot().find(".//route-files").get("value")

    trabajos, temporales = [], []
    for f in factores:
        nombre = f"calib_{args.nuevo}_f{int(round(f * 100)):03d}"
        escalar_rou(rou_base, nombre + ".rou.xml", f)
        escribir_cfg(cfg_base, nombre + ".sumocfg", nombre + ".rou.xml")
        temporales += [nombre + ".rou.xml", nombre + ".sumocfg", nombre + "_actuado.add.xml"]
        trabajos += [(f, s, nombre + ".sumocfg") for s in semillas]
    resultados = {}
    with concurrent.futures.ProcessPoolExecutor(max(1, args.procesos)) as pool:
        futuros = {pool.submit(correr, args.base, cfg, s): (f, s) for f, s, cfg in trabajos}
        for fut in concurrent.futures.as_completed(futuros):
            resultados[futuros[fut]] = fut.result()
    for ruta in temporales:
        if os.path.exists(ruta):
            os.remove(ruta)

    elegido, filas = None, []
    for f in factores:
        rs = [resultados[(f, s)] for s in semillas]
        con_spill = sum(1 for r in rs if r["spillback_eventos"] > 0)
        sin_terminar = max(r["no_terminados"] / max(1, r["vehiculos"]) for r in rs)
        if elegido is None and con_spill >= 2 and sin_terminar <= 0.10:
            elegido = f
        filas.append(linea(f, rs, "  <- elegido" if f == elegido else ""))
    cabecera = ("   f  spill  cola max enl  sin term.   timeLoss por semilla      "
                "total por semilla   espera entrar")
    print("\n" + cabecera + "\n" + "\n".join(filas))
    if elegido is None:
        print("\nNingun factor cumple el criterio: ampliar --factores.")
        return
    print(f"\nFactor elegido: {elegido}")
    if not args.escribir:
        return
    comentario = (f"{args.nuevo} (plan de pruebas, P6): la demanda de {rou_base} con cada vehsPerHour x "
                  f"{elegido}.\n         Criterio (el de corredor_alta y red_alta): control actuado, "
                  f"semillas "
                  f"{args.semillas}, menor f de\n         {{{args.factores}}} con spillback (cola detenida "
                  f"de un carril de enlace >= 90 % de sus plazas) en\n         al menos 2 de 3 semillas y "
                  f"a lo sumo 10 % sin terminar a los 6000 pasos (calibrar_demanda.py).\n         Por "
                  f"factor (semillas en orden; s/veh; espera para entrar: la media mas alta):\n       "
                  + cabecera + "\n       " + "\n       ".join(filas) + "\n    ")
    escalar_rou(rou_base, os.path.join(AQUI, f"{args.nuevo}.rou.xml"), elegido, comentario)
    escribir_cfg(cfg_base, os.path.join(AQUI, f"{args.nuevo}.sumocfg"), f"{args.nuevo}.rou.xml",
                 f"{args.nuevo}.add.xml")
    shutil.copy2(os.path.join(AQUI, f"{args.base}.add.xml"), os.path.join(AQUI, f"{args.nuevo}.add.xml"))
    print(f"Escritos {args.nuevo}.rou.xml, .sumocfg y .add.xml en {AQUI}")


if __name__ == "__main__":
    main()
