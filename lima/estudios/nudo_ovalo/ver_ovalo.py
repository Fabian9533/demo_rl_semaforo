"""
ver_ovalo.py - Mirar en la ventana de SUMO (sumo-gui) el nudo en la red del Ovalo Vasco, con dos o mas controles a la
vez, uno al lado del otro y los mismos vehiculos (misma semilla). Solo para mirar: no escribe nada en salidas/ ni cambia
ningun resultado. Es lima/ver_en_sumo.py del estudio adaptado al ovalo (18.11.2026); sirve cuando ya existen las
politicas entrenadas (entrenar.sh).

Uso (desde cualquier carpeta):
  python ver_ovalo.py                                   # plan de hoy a la izquierda, modelo de orden libre a la derecha
  python ver_ovalo.py --demanda alta --controles hoy,completo,libre
  python ver_ovalo.py --semilla 21001 --retardo 50
Controles: hoy (el plan medido en el sitio), fijo (fijo ajustado), actuado (actuado ajustado), libre (modelo de orden
libre) y completo (modelo de orden fijo). De cada modelo se juega el entrenamiento citado: el de validacion mediana entre
los tres (como evaluar_ovalo.py).
--retardo: milisegundos entre segundos simulados (100 = una hora en unos 6 minutos); se cambia tambien en la ventana.
La vista empieza centrada en el ovalo (vista_ovalo.xml). Cada control corre en su propia copia de la carpeta de la
demanda (ver/<demanda>/<control>/), asi nada se pisa. Al cerrar cada simulacion se escribe en la consola el retraso total
por vehiculo de cada control.
--sin-ventana (solo para probar este programa): corre sumo sin ventana.
"""
import argparse
import ctypes
import json
import os
import shutil
import subprocess
import sys
from multiprocessing import Process, Queue

AQUI = os.path.dirname(os.path.abspath(__file__))
DEMO = os.path.join(AQUI, "demo_rl")
LIMA = os.path.join(DEMO, "lima")
sys.path.insert(0, DEMO)
sys.path.insert(0, LIMA)
NIVELES = {"publicada": "", "alta": "alta"}
PROGRAMA = {"hoy": "lima.add.xml", "fijo": "lima_fijo.add.xml", "actuado": "lima_actuadoaj.add.xml"}
NOMBRE = {"hoy": "plan de hoy", "fijo": "fijo ajustado", "actuado": "actuado ajustado",
          "libre": "modelo de orden libre", "completo": "modelo de orden fijo"}
DATOS = ["lima.sumocfg", "lima.net.xml", "lima.rou.xml", "lima.add.xml", "e2_lima_75.add.xml", "lima_libre.json",
         "lima_fijo.add.xml", "lima_actuadoaj.add.xml"]
VISTA = os.path.join(AQUI, "vista_ovalo.xml")
FIN_SIM = 6000


def citada(carpeta, etiqueta):
    """La base de validacion mediana entre los tres entrenamientos (veredicto.base_mediana sobre val_elegido)."""
    import veredicto as regla
    vals = {}
    for b in (42, 2042, 4042):
        with open(os.path.join(carpeta, f"politica_lima_vecinos_{etiqueta}_s{b}.json"), encoding="utf-8") as f:
            vals[b] = json.load(f)["val_elegido"]
    return regla.base_mediana(vals)


def ventanas(n):
    """Tamano y posicion de n ventanas lado a lado, segun la pantalla."""
    try:
        ancho, alto = ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)
    except Exception:
        ancho, alto = 1920, 1080
    w = ancho // n
    return [([f"{w}", f"{alto - 80}"], [f"{k * w}", "0"]) for k in range(n)]


def copia(carpeta, control, demanda, ver):
    """<ver>/<demanda>/<control>/: los datos de la demanda y la vista del ovalo (rl_ippo la lee como vista_lima.xml)."""
    destino = os.path.join(ver, demanda, control)
    os.makedirs(destino, exist_ok=True)
    for f in DATOS:
        if os.path.exists(os.path.join(carpeta, f)):
            shutil.copyfile(os.path.join(carpeta, f), os.path.join(destino, f))
    shutil.copyfile(VISTA, os.path.join(destino, "vista_lima.xml"))
    return destino


def jugar_modelo(ruta_pt, donde, tam, pos, semilla, retardo, ventana, cola):
    """En su propio proceso: el modelo juega un episodio en su carpeta, con su ventana en su lugar de la pantalla."""
    import torch
    import comun
    import rl_ippo
    torch.set_num_threads(1)
    os.chdir(donde)
    iniciar = comun.iniciar_sumo
    if ventana:
        comun.iniciar_sumo = lambda cmd, **kw: iniciar(cmd + ["--window-size", ",".join(tam),
                                                              "--window-pos", ",".join(pos)], **kw)
    rl_ippo.preparar("lima")
    politica, meta = rl_ippo.Politica.cargar(ruta_pt)
    rl_ippo.configurar_desde_meta(meta)
    res = rl_ippo.correr_episodio("demo", politica, ventana, retardo, semilla, tripinfo="trip_ver.xml",
                                  variante=meta.get("variante", "vecinos"))
    cola.put(res["retraso_total_prom"])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--demanda", choices=list(NIVELES), default="publicada")
    ap.add_argument("--controles", default="hoy,libre")
    ap.add_argument("--semilla", type=int, default=21001)
    ap.add_argument("--retardo", type=int, default=100)
    ap.add_argument("--carpeta", default=None, help="(pruebas) otra carpeta con la forma de demo_rl/lima")
    ap.add_argument("--sin-ventana", action="store_true", help="(pruebas) sumo sin ventana")
    ap.add_argument("--ver", default=os.path.join(AQUI, "ver"), help="donde van las copias de cada control")
    args = ap.parse_args()
    # como figura_secuencia.py: nada de las semillas de ajuste ni de las tandas (solo validacion o humo)
    assert 21001 <= args.semilla <= 21008 or 424301 <= args.semilla <= 424360, "solo validacion o humo"
    import comun
    carpeta = os.path.join(os.path.abspath(args.carpeta) if args.carpeta else LIMA, NIVELES[args.demanda])
    controles = [c.strip() for c in args.controles.split(",") if c.strip()]
    lugares = ventanas(len(controles))
    ventana = not args.sin_ventana
    print(f"Ovalo, demanda {args.demanda}, semilla {args.semilla}. Ventanas de izquierda a derecha: "
          + ", ".join(NOMBRE[c] for c in controles))
    abiertas, modelos = [], []
    for (tam, pos), control in zip(lugares, controles):
        donde = copia(carpeta, control, args.demanda, args.ver)
        if control in ("libre", "completo"):
            ruta = os.path.join(carpeta, f"politica_lima_vecinos_{control}_s{citada(carpeta, control)}.pt")
            cola = Queue()
            p = Process(target=jugar_modelo, args=(ruta, donde, tam, pos, args.semilla, args.retardo, ventana, cola))
            p.start()
            modelos.append((control, p, cola))
            continue
        trip = os.path.join(donde, "trip_ver.xml")
        cmd = ["sumo-gui" if ventana else "sumo", "-c", os.path.join(donde, "lima.sumocfg"), "--seed",
               str(args.semilla), "--tripinfo-output", trip, "--tripinfo-output.write-unfinished", "true", "--end",
               str(FIN_SIM), "--additional-files", os.path.join(donde, PROGRAMA[control])] + comun.args_estadisticas(trip)
        if ventana:
            cmd += ["--start", "--quit-on-end", "--delay", str(args.retardo), "--window-size", ",".join(tam),
                    "--window-pos", ",".join(pos), "--gui-settings-file", VISTA]
        abiertas.append((control, subprocess.Popen(cmd), trip))
    resultados = {}
    for control, proceso, trip in abiertas:
        proceso.wait()
        resultados[control] = comun.leer_tripinfo(trip)["retraso_total_prom"]
    for control, p, cola in modelos:
        resultados[control] = cola.get()
        p.join()
    print("Retraso total por vehiculo en esta semilla (s/veh):")
    for control in controles:
        if control in resultados:
            print(f"  {NOMBRE[control]:22s} {resultados[control]:7.1f}")


if __name__ == "__main__":
    main()
