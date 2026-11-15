"""
ver_en_sumo.py - Mirar en la ventana de SUMO un caso de Lima con dos o mas controles a la vez, uno al lado del otro,
con los mismos vehiculos (misma semilla). Solo para mirar: no escribe nada en salidas/ ni cambia ningun resultado.

Uso (desde demo_rl/lima):
  python ver_en_sumo.py nudo                              # plan de hoy a la izquierda, modelo a la derecha
  python ver_en_sumo.py corredor --demanda alta
  python ver_en_sumo.py corredor --controles hoy,fijo,actuado,modelo
  python ver_en_sumo.py nudo --semilla 22002 --retardo 50

Controles: hoy (en el nudo, el plan medido en el sitio; en el corredor, el plan tipico supuesto), fijo (fijo ajustado
al segundo), actuado (actuado ajustado), modelo (el modelo completo, el entrenamiento citado en la tesis).
--retardo: milisegundos entre segundos simulados (100 = una hora en unos 6 minutos); se cambia tambien en la ventana.
Al cerrar cada simulacion se escribe en la consola el retraso total por vehiculo de cada control.
"""
import argparse
import ctypes
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, RAIZ)
sys.path.insert(0, AQUI)
import comun

# caso -> (carpeta de la demanda publicada, escenario, prefijo de los archivos)
CASOS = {"nudo": ("", "lima", "lima"), "corredor": ("corredor", "benavides", "benavides")}
# entrenamiento citado en la tesis (lima_resumen.tex): base de la semilla por caso y demanda
CITADO = {("nudo", "publicada"): 42, ("nudo", "alta"): 42,
          ("corredor", "publicada"): 42, ("corredor", "alta"): 2042}
NOMBRE = {"hoy": "plan de hoy", "fijo": "fijo ajustado", "actuado": "actuado ajustado", "modelo": "modelo"}
FIN_SIM = 6000


def archivo_programa(prefijo, control):
    return {"hoy": f"{prefijo}.add.xml", "fijo": f"{prefijo}_fijo.add.xml",
            "actuado": f"{prefijo}_actuadoaj.add.xml"}[control]


def leer_y_borrar(trip):
    res = comun.leer_tripinfo(trip)["retraso_total_prom"]
    for archivo in (trip, comun.ruta_estadisticas(trip)):
        if os.path.exists(archivo):
            os.remove(archivo)
    return res


def ventanas(n):
    """Tamano y posicion de n ventanas lado a lado, segun la pantalla."""
    try:
        ancho, alto = ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1)
    except Exception:
        ancho, alto = 1920, 1080
    w = ancho // n
    return [([f"{w}", f"{alto - 80}"], [f"{k * w}", "0"]) for k in range(n)]


def opciones_gui(tam, pos, retardo):
    return ["--start", "--quit-on-end", "--delay", str(retardo),
            "--window-size", ",".join(tam), "--window-pos", ",".join(pos)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("caso", choices=sorted(CASOS))
    ap.add_argument("--demanda", choices=["publicada", "alta"], default="publicada")
    ap.add_argument("--controles", default="hoy,modelo")
    ap.add_argument("--semilla", type=int, default=22001, help="la primera de la tanda 1")
    ap.add_argument("--retardo", type=int, default=100)
    args = ap.parse_args()

    sub, esc, prefijo = CASOS[args.caso]
    carpeta = os.path.join(AQUI, sub, "alta" if args.demanda == "alta" else "")
    os.chdir(carpeta)
    tmp = os.path.join(carpeta, "tmp")
    os.makedirs(tmp, exist_ok=True)
    cfg = f"{prefijo}.sumocfg"
    controles = [c.strip() for c in args.controles.split(",") if c.strip()]
    lugares = ventanas(len(controles))

    print(f"{args.caso}, demanda {args.demanda}, semilla {args.semilla}. Ventanas de izquierda a derecha: "
          + ", ".join(NOMBRE[c] for c in controles))
    abiertas, trips = [], {}
    for (tam, pos), control in zip(lugares, controles):
        if control == "modelo":
            continue
        programa = archivo_programa(prefijo, control)
        trip = os.path.join(tmp, f"trip_ver_{control}_{args.semilla}.xml")
        cmd = ["sumo-gui", "-c", cfg, "--seed", str(args.semilla), "--tripinfo-output", trip,
               "--tripinfo-output.write-unfinished", "true", "--end", str(FIN_SIM),
               "--additional-files", programa] + comun.args_estadisticas(trip) + opciones_gui(tam, pos, args.retardo)
        abiertas.append((control, subprocess.Popen(cmd)))
        trips[control] = trip

    resultados = {}
    if "modelo" in controles:
        import torch
        import rl_ippo
        torch.set_num_threads(1)
        tam, pos = lugares[controles.index("modelo")]
        iniciar = comun.iniciar_sumo
        # la ventana del modelo la abre rl_ippo.correr_episodio: se le agrega su lugar en la pantalla
        comun.iniciar_sumo = lambda cmd, **kw: iniciar(cmd + ["--window-size", ",".join(tam),
                                                              "--window-pos", ",".join(pos)], **kw)
        ruta = f"politica_{esc}_vecinos_completo_s{CITADO[(args.caso, args.demanda)]}.pt"
        rl_ippo.preparar(esc)
        politica, meta = rl_ippo.Politica.cargar(ruta)
        rl_ippo.configurar_desde_meta(meta)
        trip = os.path.join(tmp, f"trip_ver_modelo_{args.semilla}.xml")
        res = rl_ippo.correr_episodio("demo", politica, True, args.retardo, args.semilla, tripinfo=trip,
                                      variante=meta.get("variante", "vecinos"))
        resultados["modelo"] = res["retraso_total_prom"]
        leer_y_borrar(trip)
    for control, proceso in abiertas:
        proceso.wait()
        resultados[control] = leer_y_borrar(trips[control])
    print("Retraso total por vehiculo en esta semilla (s/veh):")
    for control in controles:
        if control in resultados:
            print(f"  {NOMBRE[control]:17s} {resultados[control]:7.1f}")


if __name__ == "__main__":
    main()
