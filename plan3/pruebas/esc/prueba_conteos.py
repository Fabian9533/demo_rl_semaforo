"""
prueba_conteos.py - Prueba 2 de los escenarios nuevos: en 20 semillas de humo (424301-424320) la media de vehiculos
generados queda dentro de +-3 errores estandar de lo esperado (demanda_estocastica.demanda_esperada) en todos los
poi_, per_ y mix_ (y cada periodo de 30 min); en per_ tambien cada bloque de 10 min; en mix_ la composicion por tipo
queda dentro de +-2 errores estandar de la mezcla (mas una prueba chi cuadrado con los conteos sumados). P6e
(llegadas regulares) debe generar exactamente lo esperado.
Corridas: sumo puro con el fijo instalado hasta 3601 s (todas las llegadas ya cargadas; no hace falta vaciar la
red), tripinfo con los no terminados y los no insertados. Como mucho 3 sumo a la vez.
Uso (desde plan3/): python pruebas/esc/prueba_conteos.py      Salida: salidas/conteos.txt y conteos.csv
"""
import os
import sys
import csv
import statistics as st
import concurrent.futures as cf

from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_esc as u                       # noqa: E402
import demanda_estocastica as de           # noqa: E402
import escenarios_plan3 as e3              # noqa: E402

SEMILLAS = list(range(424301, 424321))
FIN = 3601
p = u.Salida("conteos.txt")
fallas = []


def ok(cond, texto):
    p(("  ok    " if cond else "  FALLA ") + texto)
    if not cond:
        fallas.append(texto)


def una(esc, semilla):
    """Conteos de una corrida: generados, por periodo (prefijo p1_/p2_ del flow), por bloque del perfil, por flow y
    por tipo."""
    tmp = os.path.join(u.TMP, "conteos")
    trip, stats_, _ = u.correr_sumo(f"{esc}.sumocfg", semilla, os.path.join(tmp, f"tripinfo_{esc}_{semilla}.xml"),
                                    fin=FIN)
    viajes = u.leer_viajes(trip)
    est = u.estadisticas(stats_)
    fila = {"escenario": esc, "semilla": semilla, "generados": len(viajes), "cargados": est["loaded"]}
    por_flow, por_tipo, fuera = {}, {}, 0
    for vid, v in viajes.items():
        flujo = de.flujo_de(vid)
        por_flow[flujo] = por_flow.get(flujo, 0) + 1
        periodo = {"p1": 1, "p2": 2}[flujo.split("_")[0]]
        fila[f"periodo{periodo}"] = fila.get(f"periodo{periodo}", 0) + 1
        k = de.bloque_de(vid)
        if k is not None:
            fila[f"b{k}"] = fila.get(f"b{k}", 0) + 1
            if v["deseada"] is not None and not 600 * k <= v["deseada"] < 600 * (k + 1) + 1:
                fuera += 1
        por_tipo[v["vtype"]] = por_tipo.get(v["vtype"], 0) + 1
    fila["fuera_de_bloque"] = fuera
    for clase in de.composicion():
        if f"lima_{clase}" in por_tipo:
            fila[clase] = por_tipo[f"lima_{clase}"]
    os.remove(trip)
    os.remove(stats_)
    return fila, por_flow


def prueba_media(nombre, valores, esperado, z_max, conteo=True):
    """|media - esperado| <= z_max errores estandar. En conteos informa ademas sd / raiz(esperado) (1 en un Poisson)."""
    media, sd = st.mean(valores), st.stdev(valores)
    ee = sd / len(valores) ** 0.5
    z = (media - esperado) / ee if ee > 0 else (0.0 if media == esperado else float("inf"))
    ok(abs(z) <= z_max, f"{nombre:26s} esperado {esperado:9.2f}, media {media:9.2f} (sd {sd:6.2f}, ee {ee:5.2f}), "
                        f"z {z:+5.2f}" + (f"; sd / raiz(esperado) {sd / esperado ** 0.5:4.2f}" if conteo else ""))
    return z


def main():
    os.chdir(u.PLAN3)
    os.makedirs(os.path.join(u.TMP, "conteos"), exist_ok=True)
    nombres = [e for e, r in e3.RECETAS.items() if r[1] == "poisson" and r[4] == 0]      # poi_, per_ y mix_
    trabajos = [(e, s) for e in nombres for s in SEMILLAS] + [("malla3_alta_e", s) for s in SEMILLAS[:2]]
    resultados = {}
    with cf.ThreadPoolExecutor(u.MAX_SUMO) as pool:
        fut = {pool.submit(una, e, s): (e, s) for e, s in trabajos}
        for f in cf.as_completed(fut):
            resultados[fut[f]] = f.result()
    filas = [resultados[k][0] for k in trabajos]
    campos = ["escenario", "semilla", "generados", "cargados", "periodo1", "periodo2"] + \
        [f"b{k}" for k in range(6)] + ["fuera_de_bloque"] + list(de.composicion())
    with open(os.path.join(u.SALIDAS, "conteos.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)

    p(f"Vehiculos generados en {len(SEMILLAS)} semillas de humo ({SEMILLAS[0]}-{SEMILLAS[-1]}), sumo puro "
      f"hasta {FIN} s")
    ok(all(fl["generados"] == fl["cargados"] for fl in filas),
       "en cada corrida el tripinfo tiene todos los vehiculos cargados (statistic-output)")
    for esc in nombres:
        rou = os.path.join(u.PLAN3, f"{esc}.rou.xml")
        mias = [fl for fl in filas if fl["escenario"] == esc]
        p(f"{esc}:")
        prueba_media("total", [fl["generados"] for fl in mias], de.demanda_esperada([rou]), 3)
        for k, v in de.por_periodo(rou).items():
            prueba_media(f"periodo {k}", [fl.get(f"periodo{k}", 0) for fl in mias], v, 3)
        if e3.RECETAS[esc][2]:
            for k, v in de.por_bloque(rou).items():
                prueba_media(f"bloque {k} ({600 * k}-{600 * (k + 1)} s)", [fl.get(f"b{k}", 0) for fl in mias], v, 3)
            ok(sum(fl["fuera_de_bloque"] for fl in mias) == 0,
               "todo vehiculo insertado pidio salir dentro de su bloque (salida pedida = depart - departDelay)")
        esperado_flow = de.por_flow(rou)
        n_fuera = 0
        for flujo in {de.flujo_de(fid) for fid in esperado_flow}:
            x = [resultados[(esc, s)][1].get(flujo, 0) for s in SEMILLAS]
            esp = sum(v for fid, v in esperado_flow.items() if de.flujo_de(fid) == flujo)
            ee = st.stdev(x) / len(x) ** 0.5
            n_fuera += abs(st.mean(x) - esp) > 3 * ee
        n_flows = len({de.flujo_de(f) for f in esperado_flow})
        p(f"  (informativo) flows con la media fuera de +-3 ee: {n_fuera} de {n_flows}")
        if e3.RECETAS[esc][3]:
            comp = de.composicion()
            escritas = {c: float(f"{q:.6f}") for c, q in comp.items()}
            total_p = sum(escritas.values())
            for clase in comp:
                cuotas = [fl.get(clase, 0) / fl["generados"] for fl in mias]
                prueba_media(f"cuota de {clase} (%)", [100 * c for c in cuotas], 100 * escritas[clase] / total_p, 2,
                             conteo=False)
            observados = [sum(fl.get(c, 0) for fl in mias) for c in comp]
            n = sum(observados)
            esperados = [n * escritas[c] / total_p for c in comp]
            chi2, pval = stats.chisquare(observados, esperados)
            p(f"  chi cuadrado de la composicion con los conteos sumados ({n} vehiculos, 4 g.l.): {chi2:.2f}, "
              f"p = {pval:.3f}")
    p("malla3_alta_e (llegadas regulares):")
    regular = [fl for fl in filas if fl["escenario"] == "malla3_alta_e"]
    ok(all(fl["generados"] == 8700 for fl in regular), f"genera exactamente 8700 vehiculos en las semillas "
                                                       f"{', '.join(str(fl['semilla']) for fl in regular)}")
    p(f"\nResultado: {'TODO OK' if not fallas else f'{len(fallas)} FALLAS'}")
    p.guardar()
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
