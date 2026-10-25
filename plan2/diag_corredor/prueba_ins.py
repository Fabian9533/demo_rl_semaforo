"""
prueba_ins.py - Prueba unitaria de la correccion INS de rl_ippo.py (--recompensa-insercion), 25.10.2026.

Uso (desde demo_rl/plan2):
  python diag_corredor/prueba_ins.py --escenario corredor_alta --politica politica_corredor_alta_vecinos_s2042.pt

Juega la politica congelada (demo, argmax) con el conteo de vehiculos pendientes encendido y comprueba:
  1. la suma en el tiempo de los vehiculos que esperan para entrar (ins_total, vehiculo-segundos) coincide
     con la suma de departDelay del tripinfo mas la espera de los que no alcanzaron a entrar (archivo de
     estadisticas), salvo el redondeo (menos de 1 s por vehiculo); y vehiculo por vehiculo, los segundos
     que estuvo pendiente son departDelay sin la fraccion de redondeo: departDelay - 1 < n <= departDelay;
  2. todos los pendientes quedan asignados a un semaforo (ins_espera = ins_total);
  3. en demo el conteo no cambia la simulacion: con y sin ins dan las mismas metricas.
Sale con codigo 1 si algo no se cumple.

Por que hay redondeo: un flujo de 250 veh/h quiere soltar un vehiculo cada 14.4 s, pero SUMO solo inserta en
pasos enteros. El que quiere salir a los 14.4 s y entra a los 15 s lleva departDelay 0.6 sin haber quedado
pendiente al cerrar ningun paso. El tripinfo escribe departDelay con dos decimales (0.9996 sale 1.00), de ahi
el margen de 0.005 en la comprobacion por vehiculo.
"""
import os
import sys
import argparse
import collections
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import comun          # noqa: E402
import rl_ippo        # noqa: E402

TOLERANCIA = 1.0      # vehiculo-segundos por vehiculo, en la suma
MARGEN = 0.005        # dos decimales del tripinfo


def espera_tripinfo(tripinfo):
    """({id: departDelay} de los viajes, espera de los no insertados, no insertados)."""
    viajes = {v.get("id"): float(v.get("departDelay", 0))
              for v in ET.parse(tripinfo).getroot().findall("tripinfo")}
    fuera, n_fuera = 0.0, 0
    stats = comun.ruta_estadisticas(tripinfo)
    if os.path.exists(stats):
        raiz = ET.parse(stats).getroot()
        veh = raiz.find("vehicles")
        trip = raiz.find("vehicleTripStatistics")
        if veh is not None:
            n_fuera = int(veh.get("waiting", 0))          # como comun.leer_tripinfo
        if trip is not None and n_fuera:
            fuera = n_fuera * float(trip.get("departDelayWaiting", 0))
    return viajes, fuera, n_fuera


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escenario", default="corredor_alta")
    ap.add_argument("--politica", default="politica_corredor_alta_vecinos_s2042.pt")
    ap.add_argument("--semilla", type=int, default=1001)
    args = ap.parse_args()
    rl_ippo.preparar(args.escenario)
    rl_ippo.sembrar(0)
    politica, meta = rl_ippo.Politica.cargar(args.politica)
    sin_asignar = [f for f, t in rl_ippo.C["ins_flujo"].items() if t is None]
    print(f"{args.escenario}: {len(rl_ippo.C['ins_flujo'])} flujos, sin semaforo: {sin_asignar}")

    # Envoltorio solo para la prueba: cuenta, vehiculo por vehiculo, los segundos que estuvo pendiente
    por_vehiculo = collections.Counter()
    original = rl_ippo.traci.simulation.getPendingVehicles

    def contar():
        ids = original()
        por_vehiculo.update(ids)
        return ids
    rl_ippo.traci.simulation.getPendingVehicles = contar
    t_con, t_sin = f"prueba_ins_{args.escenario}_con.xml", f"prueba_ins_{args.escenario}_sin.xml"
    con = rl_ippo.correr_episodio("demo", politica, False, 0, args.semilla, tripinfo=t_con,
                                  variante=meta["variante"], ins=True)
    rl_ippo.traci.simulation.getPendingVehicles = original
    sin = rl_ippo.correr_episodio("demo", politica, False, 0, args.semilla, tripinfo=t_sin,
                                  variante=meta["variante"], ins=False)

    viajes, fuera, n_fuera = espera_tripinfo(t_con)
    suma = sum(viajes.values())
    n = len(viajes)
    esperado = suma + fuera
    dif = con["ins_total"] - esperado
    print(f"ins_total = {con['ins_total']} veh-s; departDelay del tripinfo = {suma:.2f} ({n} viajes) + "
          f"espera de {n_fuera} no insertados = {fuera:.2f} -> {esperado:.2f}; diferencia {dif:+.2f} "
          f"({dif / max(1, n):+.4f} por vehiculo)")
    print(f"ins_espera (asignados) = {con['ins_espera']}; retraso_insercion_prom = {con['retraso_insercion_prom']}")
    malos = [(v, d, por_vehiculo.get(v, 0)) for v, d in viajes.items()
             if not (d - 1 - MARGEN < por_vehiculo.get(v, 0) <= d + MARGEN)]
    fantasmas = [v for v in por_vehiculo if v not in viajes]       # pendientes que nunca entraron
    print(f"por vehiculo: {n - len(malos)} de {n} con departDelay - 1 < pendiente <= departDelay; "
          f"fuera de rango: {malos[:5]}; pendientes sin viaje en el tripinfo: {len(fantasmas)} "
          f"(no insertados al cerrar: {n_fuera})")
    iguales = [m for m in ("timeloss_prom", "retraso_total_prom", "retraso_insercion_prom", "cambios_fase",
                           "ret_retraso", "vehiculos") if con[m] != sin[m]]
    ok = [abs(dif) <= TOLERANCIA * max(1, n) and not malos and len(fantasmas) == n_fuera,
          con["ins_espera"] == con["ins_total"], not iguales]
    print(f"1 suma de pendientes = espera para entrar: {'OK' if ok[0] else 'FALLA'}")
    print(f"2 todos asignados: {'OK' if ok[1] else 'FALLA'}")
    print(f"3 la simulacion no cambia con el conteo: {'OK' if ok[2] else 'FALLA ' + str(iguales)}")
    for t in (t_con, t_sin):
        comun.borrar_tripinfo(t)
    sys.exit(0 if all(ok) else 1)


if __name__ == "__main__":
    main()
