"""tablas_nudo_fijo.py - Tres tablas del nudo con el modelo completo (de orden fijo) como protagonista
(encuadre final del 19.11.2026). Son las de nudo_ovalo_estudio2/tablas_ovalo.py (mismo formato, mismas funciones:
tablas_lima.leer y estudio.comparar, que da el cambio %, el IC95 por bootstrap pareado y la p de Wilcoxon pareada),
con el cambio calculado para el modelo de orden fijo citado en lugar de la variante de orden libre:

  ovalo_resultado_fijo.tex   retraso total de cada control y de los dos modelos en las dos tandas, y cambio del modelo
                             de orden fijo frente a cada uno
  ovalo_completa_fijo.tex    lo mismo con IC95 y p, y las referencias secundarias
  ovalo_robustez_fijo.tex    la prueba de robustez del reparto (24001-24100), con el cambio del modelo de orden fijo
  ovalo_entrenamientos_fijo.tex  la de entrenamientos de tablas_ovalo.py, con el modelo de orden fijo primero y la
                             "variante de orden libre" con ese nombre

No simula ni escribe en nudo_ovalo_estudio2/ (se importa sin bytecode): lee salidas/eval_t*_*.csv de demo_rl/lima/,
demo_rl/lima/alta/ y demo_rl/lima/robustez/<variante>/, y los meta de las politicas (version citada = mediana).
Uso: python -B tablas_nudo_fijo.py DESTINO
"""
import os
import statistics
import sys

sys.dont_write_bytecode = True
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # con el repositorio y los estudios
EST = os.path.join(RAIZ, "nudo_ovalo_estudio2")
sys.path.insert(0, EST)
import tablas_ovalo as to  # noqa: E402

tl, tp, estudio = to.tl, to.tp, to.estudio
NIVELES = {"publicada": to.LIMA, "alta": os.path.join(to.LIMA, "alta")}
ROBUSTEZ = {"reducto": "Más carga en Reducto", "transversal": "Más carga en 28 de Julio y Balboa"}
NOMBRE = {"actual": "Plan actual", "fijo": "Fijo ajustado al segundo", "actuadoaj": "Actuado ajustado",
          "actuado": "Actuado por defecto", "minimo": "Ciclo mínimo",
          "actuadoajb": "Actuado ajustado, antes de la comprobación del borde", "libre": "Variante de orden libre"}
PRINCIPALES = ["actual", "fijo", "actuadoaj", "libre"]
DESTINO = None


def escribir(nombre, cabecera, cuerpo):
    ruta = os.path.join(DESTINO, nombre)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("% Generado por tesis_ovalo_2026-11-19/figuras/tablas_nudo_fijo.py (las funciones de tablas_ovalo.py y "
                "estudio.comparar), a partir de nudo_ovalo_estudio2/demo_rl/lima/. No editar a mano.\n"
                + "".join(f"% {linea}\n" for linea in cabecera) + cuerpo + "\n")
    print("Escrito", ruta)


def celda(c):
    p = "$p < 0.001$" if c["p"] < 0.001 else f"$p = {c['p']:.3f}$"
    return f"{tp.num(c['delta'])} [{tp.num(c['ic'][0])}, {tp.num(c['ic'][1])}], {p}"


def datos(carpeta):
    """Por tanda: retraso medio de cada brazo y comparacion del modelo de orden fijo citado con cada control."""
    cit = {e: to.citada(carpeta, e) for e in to.MODELOS}
    modelo, libre = f"completo_s{cit['completo']}", f"libre_s{cit['libre']}"
    comp, medias = {}, {}
    for t in estudio.TANDAS:
        vals = tl.leer(carpeta, t, modelo)
        comp[t], medias[t] = {}, {"modelo": statistics.mean(vals.values())}
        for ref in list(NOMBRE):
            r = tl.leer(carpeta, t, libre if ref == "libre" else ref)
            if r is not None:
                comp[t][ref] = estudio.comparar(vals, r)
                medias[t][ref] = comp[t][ref]["media_ref"]
    return {"cit": cit, "modelo": modelo, "libre": libre, "comp": comp, "medias": medias}


def tabla_resultado(todo):
    filas = []
    for n, d in todo.items():
        if filas:
            filas.append("\\midrule")
        primera = f"{n.capitalize()} ({to.VEH[n]:.0f}~veh/h)"
        for ref in PRINCIPALES:
            filas.append([primera, NOMBRE[ref], tl.par(d["medias"][1][ref], d["medias"][2][ref], tl.uno),
                          tl.par(d["comp"][1][ref]["delta"], d["comp"][2][ref]["delta"], tp.num)])
            primera = ""
        filas.append(["", "Modelo de orden fijo", tl.par(d["medias"][1]["modelo"], d["medias"][2]["modelo"], tl.uno),
                      "---"])
    escribir("ovalo_resultado_fijo.tex",
             ["Nudo en el ovalo: retraso total por vehiculo de cada control y de los dos modelos en las dos tandas (100",
              "semillas cada una) y cambio del modelo de orden fijo (el modelo completo) frente a cada uno.",
              "fuente: salidas/eval_t1_*.csv y eval_t2_*.csv de lima/ y lima/alta/; modelos: "
              + ", ".join(f"{n}: {d['modelo']} y {d['libre']}" for n, d in todo.items()) + "."],
             tp.tabular(f"{tp.IZQ}{{2.5cm}}{tp.IZQ}{{3.7cm}}{tp.IZQ}{{3.4cm}}{tp.IZQ}{{4.0cm}}",
                        ["Demanda", "Control", "Retraso total, tandas 1 y 2 (s por vehículo)",
                         "Cambio del modelo de orden fijo frente a este control, tandas 1 y 2 (\\%)"], filas))


def tabla_completa(todo):
    filas = []
    for n, d in todo.items():
        if filas:
            filas.append("\\midrule")
        primera = n.capitalize()
        for ref in NOMBRE:
            if ref in d["comp"][1] and ref in d["comp"][2]:
                filas.append([primera, NOMBRE[ref], tl.par(d["medias"][1][ref], d["medias"][2][ref], tl.uno),
                              celda(d["comp"][1][ref]), celda(d["comp"][2][ref])])
                primera = ""
        filas.append(["", "Modelo de orden fijo", tl.par(d["medias"][1]["modelo"], d["medias"][2]["modelo"], tl.uno),
                      "---", "---"])
    escribir("ovalo_completa_fijo.tex",
             ["Nudo en el ovalo: todos los controles, por nivel de demanda. Retraso total por vehiculo en las dos tandas",
              "y cambio del modelo de orden fijo frente a cada uno, con IC95 (bootstrap pareado, 10 000 remuestreos) y",
              "p de Wilcoxon pareado. fuente: salidas/eval_t1_*.csv y eval_t2_*.csv de lima/ y lima/alta/."],
             tp.tabular(f"{tp.IZQ}{{1.5cm}}{tp.IZQ}{{2.6cm}}{tp.IZQ}{{2.0cm}}{tp.IZQ}{{4.0cm}}{tp.IZQ}{{4.0cm}}",
                        ["Demanda", "Control", "Retraso total, tandas 1 y 2 (s/veh)",
                         "Cambio del modelo de orden fijo, tanda 1 (\\%)", "Cambio, tanda 2 (\\%)"], filas))


def tabla_robustez(d):
    raiz = NIVELES["publicada"]
    modelo, libre = d["modelo"], d["libre"]
    brazos = ["actual", "fijo", "actuadoaj", libre, modelo]
    filas, detalle = [], []
    for variante, nombre in [("", "El supuesto (tanda 1)")] + list(ROBUSTEZ.items()):
        carpeta = raiz if not variante else os.path.join(raiz, "robustez", variante)
        vals = {b: tl.leer(carpeta, 1, b) for b in brazos}
        m = {b: statistics.mean(v.values()) for b, v in vals.items()}
        cambios = [estudio.comparar(vals[modelo], vals[ref]) for ref in brazos[:4]]
        filas.append([nombre] + [tl.uno(m[b]) for b in brazos] + [tp.num(c["delta"]) for c in cambios[:3]])
        detalle.append(f"{variante or 'tanda 1'}: " + "; ".join(
            f"{r} {c['delta']:+.2f} [{c['ic'][0]:+.2f}, {c['ic'][1]:+.2f}] p={c['p']:.2g}"
            for r, c in zip(brazos[:4], cambios)))
        print(detalle[-1])
    escribir("ovalo_robustez_fijo.tex",
             ["Nudo en el ovalo, prueba de robustez del reparto: retraso total (s/veh) de cada control y de los dos modelos",
              "con el mismo total (4271 veh/h) repartido de otra forma entre las entradas, sin reajustar ni reentrenar, y",
              "cambio del modelo de orden fijo frente a cada control (%). 100 semillas (24001-24100); la primera fila es la",
              "tanda 1. fuente: lima/robustez/<variante>/salidas/eval_t1_*.csv; IC95 y p: " + " | ".join(detalle)],
             tp.tabular(f"{tp.IZQ}{{2.3cm}}" + f"{tl.DER}{{1.33cm}}" * 8,
                        ["Reparto de la demanda", "Plan actual", "Fijo ajustado", "Actuado ajustado",
                         "Variante de orden libre", "Modelo de orden fijo", "Frente al plan actual (\\%)",
                         "Frente al fijo (\\%)", "Frente al actuado (\\%)"], filas))


def tabla_entrenamientos():
    """La tabla de entrenamientos de tablas_ovalo.py tal cual, con el modelo de orden fijo primero y el otro con su
    nombre en la tesis (variante de orden libre): se cambian MODELOS y escribir solo durante la llamada."""
    modelos, escribir_to = to.MODELOS, to.escribir
    to.MODELOS = {"completo": "Modelo de orden fijo", "libre": "Variante de orden libre"}
    # la primera columna, 0.25 cm mas ancha para que "Publicada" quepa; la de la base, 0.25 cm mas angosta
    to.escribir = lambda nombre, cabecera, cuerpo: escribir(
        nombre.replace(".tex", "_fijo.tex"), cabecera,
        cuerpo.replace("p{1.4cm}", "p{1.65cm}", 1).replace("p{1.5cm}", "p{1.25cm}", 1))
    try:
        to.tabla_entrenamientos({n: to.datos_nivel(c) for n, c in NIVELES.items()}, NIVELES)
    finally:
        to.MODELOS, to.escribir = modelos, escribir_to


def main():
    global DESTINO
    DESTINO = os.path.abspath(sys.argv[1])
    os.makedirs(DESTINO, exist_ok=True)
    todo = {n: datos(c) for n, c in NIVELES.items()}
    for n, d in todo.items():
        print(n, "citados", d["cit"])
        for t in (1, 2):
            print("  tanda", t, {r: (round(c["delta"], 2), [round(x, 2) for x in c["ic"]], float(f"{c['p']:.2g}"))
                                 for r, c in d["comp"][t].items()})
    tabla_resultado(todo)
    tabla_completa(todo)
    tabla_robustez(todo["publicada"])
    tabla_entrenamientos()


if __name__ == "__main__":
    main()
