"""
tablas_corredor.py - Tablas y figuras del corredor de la Av. Benavides para la tesis, con sus niveles de demanda.

Uso (desde demo_rl/lima/corredor):
  python tablas_corredor.py [--niveles publicada,alta] [--destino carpeta]
Lee solo lo que ya esta escrito: salidas/ y alta/salidas/ (estudio_corredor.py), corredor.py (red, plan tipico y
demanda), los JSON de las politicas y los CSV de entrenamiento de cada carpeta. No corre ninguna simulacion.
El entrenamiento citado de cada modelo es el de validacion mediana entre sus tres (veredicto.base_mediana).
Escribe (en TESIS/secciones/tablas y TESIS/images, o todo en --destino para probar):
  corredor_cruces.tex          los seis cruces: distancia, carriles y volumen del escenario frente al publicado
  corredor_planes.tex          fijo ajustado y verde medio del modelo en cada cruce
  corredor_resultado.tex       retraso total de cada control y cambio del modelo frente a cada uno, tandas 1 y 2
  corredor_mensajes.tex        con mensajes frente a sin mensajes, y el modelo completo con el canal cortado
  corredor_completa.tex        todos los controles, con IC95 y p
  corredor_entrenamientos.tex  los nueve entrenamientos de cada nivel
  fig_corredor_mapa.pdf|png          esquema del corredor
  fig_corredor_retraso.pdf|png       retraso total por control (tanda 1), un panel por nivel
  fig_corredor_aprendizaje.pdf|png   validacion de los entrenamientos frente a las referencias, un panel por nivel
Con --niveles publicada,alta escribe ademas el resultado final de la tesis (15.11.2026), que junta los seis casos del
segundo estudio (plan3/salidas/) con los dos de Lima:
  resultado_final.tex                tabla de todos los casos con llegadas aleatorias, de menor a mayor demanda
  fig_resultado_final.pdf|png        cambio frente al fijo ajustado al segundo por caso y tanda, con llegadas
                                     aleatorias (arriba) y regulares (abajo)
Las tablas llevan solo el entorno tabular; el table, el caption y la etiqueta los pone el texto.
"""
import argparse
import csv
import json
import os
import statistics
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
LIMA = os.path.dirname(AQUI)
RAIZ = os.path.dirname(LIMA)
for carpeta in (RAIZ, LIMA, AQUI):
    sys.path.insert(0, carpeta)
import estudio
import corredor
import tablas_plan3 as tp          # formato de numeros y colores de las figuras del segundo estudio
import tablas_lima as tl           # estilo de las figuras del nudo
import veredicto as regla

ESC = corredor.ESC
NOMBRE = {"tipico": "Plan típico", "fijo": "Fijo ajustado al segundo", "actuadoaj": "Actuado ajustado",
          "actuado": "Actuado por defecto", "minimo": "Ciclo mínimo",
          "fijo55": "Fijo ajustado, primera búsqueda", "actuadoajsc": "Actuado ajustado, sin variantes coordinadas",
          "actuadoaj12": "Actuado ajustado, primera búsqueda"}
PRINCIPALES = ["tipico", "fijo", "actuadoaj"]
# clave: (brazo sin la base, nombre en la tesis, episodios del entrenamiento)
MODELOS = {"completo": ("vecinos_completo", "Modelo completo", 400),
           "corregido": ("vecinos_corregido", "IPPO con mensajes corregido", 200),
           "sinmsg": ("local_sinmsg", "IPPO sin mensajes corregido", 200)}
NIVELES = {"publicada": ("Publicada", AQUI, 1.0), "alta": ("Alta", os.path.join(AQUI, "alta"), 1.2)}
BASES = (42, 2042, 4042)
TOTAL = sum(corredor.flujos().values())              # veh/h que entran a la red con la demanda publicada
CALLE = {c: calle for c, calle, _, _, _ in corredor.CRUCES}
AZUL, AZUL_CLARO, GRIS = tl.AZUL, tl.AZUL_CLARO, tl.GRIS
NARANJA, AGUA = "#eb6834", "#1baf7a"
CEN, DER = tl.CEN, tl.DER
par, uno = tl.par, tl.uno


def miles(v, tex=True):
    """Entero con separador fino de miles desde 10 000 (10 447), como en el resto de la tesis."""
    s = f"{v:.0f}"
    if len(s) < 5:
        return s
    return s[:-3] + ("\\," if tex else chr(0x2009)) + s[-3:]


def escribir(nombre, cabecera, cuerpo):
    ruta = os.path.join(tl.DESTINO["tablas"], nombre)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("% Generado por lima/corredor/tablas_corredor.py a partir de lima/corredor/. No editar a mano.\n"
                + "".join(f"% {linea}\n" for linea in cabecera) + cuerpo + "\n")
    print("Escrito", ruta)


# ---------------- Datos ----------------
def leer(carpeta, tanda, brazo):
    return tl.leer(carpeta, tanda, brazo)


def leer_json(carpeta, nombre):
    with open(os.path.join(carpeta, "salidas", nombre), encoding="utf-8") as f:
        return json.load(f)


def meta_politica(carpeta, clave, base):
    with open(os.path.join(carpeta, f"politica_{ESC}_{MODELOS[clave][0]}_s{base}.json"), encoding="utf-8") as f:
        return json.load(f)


def brazo(clave, base):
    return f"{MODELOS[clave][0]}_s{base}"


def serie_validacion(carpeta, clave, base):
    ruta = os.path.join(carpeta, f"resultados_{ESC}_ippo_{MODELOS[clave][0]}_s{base}.csv")
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return [(int(r["episodio"]), float(r["val_total"])) for r in csv.DictReader(f) if r.get("val_total")]


def convergio(carpeta, clave, base):
    """(se estabilizo, plateau %, estabilidad %) con la regla de la tesis sobre la validacion."""
    return regla.convergencia(serie_validacion(carpeta, clave, base), MODELOS[clave][2])


def comparaciones(carpeta, modelo):
    """({tanda: {referencia: comparacion del modelo con ella}}, {tanda: {brazo: retraso total medio}})."""
    comp, medias = {}, {}
    for t in estudio.TANDAS:
        vals = leer(carpeta, t, modelo)
        if vals is None:
            raise SystemExit(f"falta {carpeta}/salidas/eval_t{t}_{modelo}.csv")
        comp[t], medias[t] = {}, {modelo: statistics.mean(vals.values())}
        for ref in NOMBRE:
            r = leer(carpeta, t, ref)
            if r is not None:
                comp[t][ref] = estudio.comparar(vals, r)
                medias[t][ref] = comp[t][ref]["media_ref"]
    return comp, medias


def cargar(n):
    """Todo lo de un nivel: entrenamiento citado de cada modelo, comparaciones del modelo completo y veredicto."""
    carpeta = NIVELES[n][1]
    d = {"carpeta": carpeta, "veh": TOTAL * NIVELES[n][2], "citado": {}}
    for clave in MODELOS:
        d["citado"][clave] = regla.base_mediana({b: meta_politica(carpeta, clave, b)["val_elegido"] for b in BASES})
    d["modelo"] = brazo("completo", d["citado"]["completo"])
    d["comp"], d["medias"] = comparaciones(carpeta, d["modelo"])
    d["etiquetas"] = {}
    for t, c in d["comp"].items():
        f, a = c["fijo"], c.get("actuadoaj")
        d["etiquetas"][t] = regla.veredicto(f["delta"], f["ic"], f["p"], a["ic"] if a else None, a["p"] if a else None)
    return d


# ---------------- Tablas ----------------
def tabla_cruces():
    totales = corredor.totales_por_cruce()
    filas = []
    for k, (c, calle, x, n, s) in enumerate(corredor.CRUCES):
        oeste = corredor.CARRILES_AV["W" if k == 0 else corredor.IDS[k - 1]]
        este = corredor.CARRILES_AV[c]
        avenida = str(este) if oeste == este else f"{oeste} al oeste, {este} al este"
        if n and s:
            transversal = f"{n}, en los dos sentidos"
            entra = f"{corredor.TRANSVERSAL[(c, 'N')]} por sentido"
        else:
            transversal = f"{n or s}, solo hacia el {'sur' if n else 'norte'}"
            entra = str(corredor.TRANSVERSAL[(c, "N" if n else "S")])
        filas.append([calle.replace("Av. ", "Av.~"), f"{x:.0f}", avenida, transversal, entra, f"{totales[c]:.0f}",
                      str(corredor.PUBLICADO[c]) if c in corredor.PUBLICADO else "---"])
    escribir("corredor_cruces.tex",
             ["Corredor de la Av. Benavides: los seis cruces con semaforo, de oeste a este. Distancia desde la Av. Larco,",
              "carriles por sentido de la avenida y de la transversal, demanda que entra por la transversal y vehiculos",
              "por hora que entran al cruce con la demanda del escenario, frente al volumen publicado.",
              "fuente: lima/corredor/corredor.py (CRUCES, CARRILES_AV, TRANSVERSAL, PUBLICADO y totales_por_cruce);",
              "geometria de OpenStreetMap; volumenes del Plan de Movilidad Urbana de Miraflores 2017-2020, pag. 31."],
             tp.tabular(f"{tp.IZQ}{{3.1cm}}{DER}{{1.4cm}}{tp.IZQ}{{2.1cm}}{tp.IZQ}{{2.4cm}}{tp.IZQ}{{1.9cm}}{DER}{{1.3cm}}"
                        f"{DER}{{1.4cm}}",
                        ["Cruce con", "Distancia desde Larco (m)", "Carriles de la avenida, por sentido",
                         "Carriles de la transversal", "Entra por la transversal (veh/h)", "Entran al cruce (veh/h)",
                         "Publicado (veh/h)"], filas))


def tabla_planes(datos):
    filas, notas = [], []
    for n, d in datos.items():
        fijo = leer_json(d["carpeta"], "fijo_ajustado.json")
        ruta = os.path.join(d["carpeta"], "salidas", "verdes_modelo.json")
        verdes = leer_json(d["carpeta"], "verdes_modelo.json")["cruces"] if os.path.exists(ruta) else None
        if filas:
            filas.append("\\midrule")
        primera = NIVELES[n][0]
        notas.append(f"{n}: ciclo {fijo['ciclo']}, transversales {fijo['transversal']}, desfases {fijo['desfases']}")
        for k, c in enumerate(corredor.IDS):
            t = fijo["transversal"][k]
            fila = [primera, CALLE[c].replace("Av. ", "Av.~"), str(fijo["ciclo"] - 2 * corredor.AMBAR - t), str(t),
                    str(fijo["desfases"][k])]
            fila += ([uno(verdes[c]["avenida"]), uno(verdes[c]["transversal"]), uno(verdes[c]["ciclo"])] if verdes
                     else ["---"] * 3)
            filas.append(fila)
            primera = ""
        # ultima fila del nivel: el ciclo comun del fijo y el ciclo medio del modelo en los seis cruces
        medio = (f"ciclo medio de {statistics.mean(v['ciclo'] for v in verdes.values()):.0f}~s" if verdes else "---")
        filas.append(["", "Los seis cruces", f"\\multicolumn{{3}}{{r}}{{ciclo común de {fijo['ciclo']}~s}}",
                      f"\\multicolumn{{3}}{{r}}{{{medio}}}"])
    tipico = corredor.PLAN_TIPICO
    escribir("corredor_planes.tex",
             ["Corredor de la Av. Benavides: el fijo ajustado al segundo (verde de la avenida, verde de la transversal y",
              "desfase de cada cruce, con un ciclo comun) y el verde medio que da el modelo completo en cada cruce, con su",
              f"ciclo medio. El plan tipico da {tipico['ciclo'] - 2 * corredor.AMBAR - tipico['transversal']} s a la avenida y",
              f"{tipico['transversal']} s a la transversal en todos los cruces, con ciclo de {tipico['ciclo']} s y sin desfases.",
              "fuente: salidas/fijo_ajustado.json y salidas/verdes_modelo.json de cada nivel (estudio_corredor.py); "
              + "; ".join(notas)],
             tp.tabular(f"{tp.IZQ}{{2.0cm}}{tp.IZQ}{{3.1cm}}" + f"{DER}{{1.3cm}}" * 6,
                        ["Demanda", "Cruce con", "Fijo: avenida (s)", "Fijo: transversal (s)", "Fijo: desfase (s)",
                         "Modelo: avenida (s)", "Modelo: transversal (s)", "Modelo: ciclo (s)"], filas))


def tabla_resultado(datos):
    filas = []
    for n, d in datos.items():
        comp, medias, modelo = d["comp"], d["medias"], d["modelo"]
        if filas:
            filas.append("\\midrule")
        primera = f"{NIVELES[n][0]} ({miles(d['veh'])}~veh/h)"
        for ref in PRINCIPALES:
            if ref in comp[1] and ref in comp[2]:
                filas.append([primera, NOMBRE[ref], par(medias[1][ref], medias[2][ref], uno),
                              par(comp[1][ref]["delta"], comp[2][ref]["delta"], tp.num)])
                primera = ""
        filas.append(["", "Modelo completo", par(medias[1][modelo], medias[2][modelo], uno), "---"])
    escribir("corredor_resultado.tex",
             ["Corredor de la Av. Benavides: retraso total por vehiculo de cada control en las dos tandas de evaluacion",
              "(100 semillas cada una) y cambio del modelo frente a cada control, por nivel de demanda.",
              "fuente: salidas/eval_t1_*.csv y eval_t2_*.csv de lima/corredor/ y lima/corredor/alta/ (retraso_total_prom); "
              "modelo: " + ", ".join(f"{n} = {d['modelo']}" for n, d in datos.items()) + "."],
             tp.tabular(f"{tp.IZQ}{{2.3cm}}{tp.IZQ}{{4.1cm}}{tp.IZQ}{{3.4cm}}{tp.IZQ}{{3.8cm}}",
                        ["Demanda", "Control", "Retraso total, tandas 1 y 2 (s por vehículo)",
                         "Cambio del modelo frente a este control, tandas 1 y 2 (\\%)"], filas))


def celda(c):
    p = "$p < 0.001$" if c["p"] < 0.001 else f"$p = {c['p']:.3f}$"
    return f"{tp.num(c['delta'])} [{tp.num(c['ic'][0])}, {tp.num(c['ic'][1])}], {p}"


def tabla_mensajes(datos):
    """Dos comparaciones por nivel: entrenar con mensajes o sin ellos (IPPO corregido, entrenamientos citados) y
    cortar los mensajes al modelo completo ya entrenado."""
    filas, detalle = [], []
    for n, d in datos.items():
        carpeta = d["carpeta"]
        if filas:
            filas.append("\\midrule")
        primera = NIVELES[n][0]
        pares = [("Entrenar sin mensajes o con ellos (IPPO con mensajes corregido)", brazo("sinmsg", d["citado"]["sinmsg"]),
                  brazo("corregido", d["citado"]["corregido"])),
                 ("Cortar los mensajes al modelo completo ya entrenado", d["modelo"] + "_cortado", d["modelo"])]
        for rotulo, sin, con in pares:
            vs, vc = [leer(carpeta, t, sin) for t in estudio.TANDAS], [leer(carpeta, t, con) for t in estudio.TANDAS]
            if any(v is None for v in vs + vc):
                print(f"mensajes ({n}): falta la evaluacion de {sin} o de {con}")
                continue
            cs = [estudio.comparar(c, s) for c, s in zip(vc, vs)]
            filas.append([primera, rotulo, par(*[statistics.mean(v.values()) for v in vs], uno),
                          par(*[statistics.mean(v.values()) for v in vc], uno), par(cs[0]["delta"], cs[1]["delta"], tp.num)])
            detalle.append(f"{n}, {con} frente a {sin}: " + " y ".join(
                f"{c['delta']:+.2f} [{c['ic'][0]:+.2f}, {c['ic'][1]:+.2f}] p={c['p']:.2g}" for c in cs))
            primera = ""
    escribir("corredor_mensajes.tex",
             ["Corredor de la Av. Benavides: que aportan los mensajes entre cruces vecinos. Retraso total (s/veh) en las",
              "dos tandas sin mensajes y con ellos, y cambio con mensajes frente a sin ellos (%).",
              "fuente: salidas/eval_t*_*.csv de cada nivel (entrenamientos citados; el brazo *_cortado es el modelo",
              "completo evaluado con estudio_corredor.py evaluar --perdida 1); IC95 y p: " + " | ".join(detalle)],
             tp.tabular(f"{tp.IZQ}{{1.6cm}}{tp.IZQ}{{5.2cm}}{tp.IZQ}{{2.2cm}}{tp.IZQ}{{2.2cm}}{tp.IZQ}{{2.6cm}}",
                        ["Demanda", "Comparación", "Sin mensajes, tandas 1 y 2 (s/veh)",
                         "Con mensajes, tandas 1 y 2 (s/veh)", "Cambio con mensajes, tandas 1 y 2 (\\%)"], filas))


def tabla_completa(datos):
    filas = []
    for n, d in datos.items():
        comp, medias, modelo = d["comp"], d["medias"], d["modelo"]
        if filas:
            filas.append("\\midrule")
        primera = NIVELES[n][0]
        for ref in NOMBRE:
            if ref in comp[1] and ref in comp[2]:
                filas.append([primera, NOMBRE[ref], par(medias[1][ref], medias[2][ref], uno),
                              celda(comp[1][ref]), celda(comp[2][ref])])
                primera = ""
        filas.append(["", "Modelo completo", par(medias[1][modelo], medias[2][modelo], uno), "---", "---"])
    escribir("corredor_completa.tex",
             ["Corredor de la Av. Benavides: todos los controles, por nivel de demanda. Retraso total por vehiculo en las",
              "dos tandas y cambio del modelo frente a cada control, con IC95 (bootstrap pareado, 10 000 remuestreos) y p",
              "de Wilcoxon pareado. fuente: salidas/eval_t1_*.csv y eval_t2_*.csv de lima/corredor/ y lima/corredor/alta/."],
             tp.tabular(f"{tp.IZQ}{{1.5cm}}{tp.IZQ}{{2.6cm}}{tp.IZQ}{{2.0cm}}{tp.IZQ}{{4.0cm}}{tp.IZQ}{{4.0cm}}",
                        ["Demanda", "Control", "Retraso total, tandas 1 y 2 (s/veh)", "Cambio del modelo, tanda 1 (\\%)",
                         "Cambio del modelo, tanda 2 (\\%)"], filas))


def tabla_entrenamientos(datos):
    """Los nueve entrenamientos de cada nivel: validacion de la version evaluada, retraso en las dos tandas, cambio
    frente al fijo ajustado y si el entrenamiento se estabilizo (regla de la tesis)."""
    filas, notas = [], []
    for n, d in datos.items():
        carpeta = d["carpeta"]
        fijos = [leer(carpeta, t, "fijo") for t in estudio.TANDAS]
        if filas:
            filas.append("\\midrule")
        primera = NIVELES[n][0]
        for clave, (_, nombre, _) in MODELOS.items():
            segunda = nombre
            for base in BASES:
                meta = meta_politica(carpeta, clave, base)
                tandas = [leer(carpeta, t, brazo(clave, base)) for t in estudio.TANDAS]
                ok, plateau, estab = convergio(carpeta, clave, base)
                notas.append(f"{n} {clave} {base}: plateau {plateau:+.2f} %, estabilidad {estab:.2f} %")
                evaluado = all(v is not None for v in tandas)
                filas.append([primera, segunda, str(base) + (" (citado)" if base == d["citado"][clave] else ""),
                              str(meta["ep_elegido"]), uno(meta["val_elegido"]),
                              par(*[statistics.mean(v.values()) for v in tandas], uno) if evaluado else "---",
                              par(*[estudio.comparar(v, f)["delta"] for v, f in zip(tandas, fijos)], tp.num)
                              if evaluado else "---", "sí" if ok else "no"])
                primera, segunda = "", ""
    escribir("corredor_entrenamientos.tex",
             ["Corredor de la Av. Benavides: los tres entrenamientos de cada modelo en cada nivel de demanda. Episodio de",
              "la version evaluada (menor retraso total en la validacion, semillas 21001-21004), ese retraso, retraso",
              "total en las dos tandas de evaluacion, cambio frente al fijo ajustado al segundo y si el entrenamiento se",
              "estabilizo (regla de la tesis: en el ultimo tercio de las validaciones, tendencia y estabilidad dentro del",
              "5 %). El citado de cada modelo es el de validacion mediana.",
              "fuente: politica_benavides_<modelo>_s<base>.json (ep_elegido, val_elegido), salidas/eval_t*_*.csv y la",
              "columna val_total de resultados_benavides_ippo_<modelo>_s<base>.csv; " + "; ".join(notas)],
             tp.tabular(f"{tp.IZQ}{{1.55cm}}{tp.IZQ}{{2.2cm}}{tp.IZQ}{{1.4cm}}{tp.IZQ}{{1.3cm}}{tp.IZQ}{{1.5cm}}"
                        f"{tp.IZQ}{{1.9cm}}{tp.IZQ}{{2.05cm}}{tp.IZQ}{{1.3cm}}",
                        ["Demanda", "Modelo", "Base", "Episodio de la versión evaluada",
                         "Retraso en la validación (s/veh)", "Retraso en la evaluación, tandas 1 y 2 (s/veh)",
                         "Cambio frente al fijo ajustado (\\%)", "¿Se estabilizó?"], filas))


ROBUSTEZ = {"avenida": "Más carga en la avenida", "transversal": "Más carga en las transversales"}


def tabla_robustez(d):
    """Prueba de robustez del reparto: los controles de la demanda publicada, sin reajustar ni reentrenar, con el
    mismo total repartido de otra forma entre la avenida y las transversales (100 semillas, 24001-24100)."""
    modelo = d["modelo"]
    filas, detalle = [], []

    def fila(nombre, lectura):
        vals = {b: lectura(b) for b in PRINCIPALES + [modelo]}
        if any(v is None for v in vals.values()):
            return None
        m = {b: statistics.mean(v.values()) for b, v in vals.items()}
        cambios = [estudio.comparar(vals[modelo], vals[ref]) for ref in PRINCIPALES]
        return [nombre] + [uno(m[b]) for b in PRINCIPALES + [modelo]] + [tp.num(c["delta"]) for c in cambios], cambios

    variantes = [("El supuesto (tanda 1)", d["carpeta"])] + [(nombre, os.path.join(AQUI, "robustez", carpeta))
                                                             for carpeta, nombre in ROBUSTEZ.items()]
    for nombre, carpeta in variantes:
        r = fila(nombre, lambda b, c=carpeta: leer(c, 1, b))
        if r is None:
            print("robustez: falta la evaluacion de", carpeta)
            return
        filas.append(r[0])
        detalle.append(f"{os.path.basename(carpeta)}: " + "; ".join(
            f"{ref} {c['delta']:+.2f} [{c['ic'][0]:+.2f}, {c['ic'][1]:+.2f}] p={c['p']:.2g}"
            for ref, c in zip(PRINCIPALES, r[1])))
    escribir("corredor_robustez.tex",
             ["Corredor de la Av. Benavides, prueba de robustez del reparto: retraso total (s/veh) de cada control con el",
              "mismo total (8706 veh/h) repartido de otra forma entre la avenida y las transversales, sin reajustar ni",
              "reentrenar, y cambio del modelo frente a cada control (%). 100 semillas (24001-24100); la primera fila es",
              "la tanda 1 del caso.",
              "fuente: lima/corredor/robustez/<variante>/salidas/eval_t1_*.csv; IC95 y p: " + " | ".join(detalle)],
             tp.tabular(f"{tp.IZQ}{{2.6cm}}" + f"{DER}{{1.45cm}}" * 7,
                        ["Reparto de la demanda", "Plan típico", "Fijo ajustado", "Actuado ajustado", "Modelo completo",
                         "Frente al plan típico (\\%)", "Frente al fijo (\\%)", "Frente al actuado (\\%)"], filas))


def etiqueta_citable(etiquetas, estable):
    """La etiqueta que se cita: la que se repite en las dos tandas (si no se repite, EMPATA), con la marca
    "(sin estabilizar)" si el entrenamiento citado no se estabilizo."""
    e = etiquetas[1] if etiquetas[1] == etiquetas[2] else "EMPATA"
    return e if estable else f"{e} (sin estabilizar)"


def tabla_resumen(datos, bases_nudo):
    """Los dos casos de Lima en una tabla: cambio del modelo completo frente al plan de hoy (el medido en el nudo y
    el tipico supuesto en el corredor), al fijo ajustado al segundo y al actuado ajustado, y veredicto."""
    filas = []

    def cambios(comp, referencias, quien):
        celdas = []
        for r in referencias:
            if r in comp[1] and r in comp[2]:
                celdas.append(par(comp[1][r]["delta"], comp[2][r]["delta"], tp.num))
            else:
                print(f"resumen ({quien}): falta la evaluacion de {r}")
                celdas.append("---")
        return celdas

    primera = "El nudo"
    for n, base in bases_nudo.items():
        carpeta = tl.NIVELES[n][1]
        comp, _ = tl.comparaciones(carpeta, f"completo_s{base}")
        estable = tl.convergio(carpeta, base)[0]
        filas.append([primera, f"{tl.NIVELES[n][0]} ({miles(4271 * tl.NIVELES[n][2])}~veh/h)"]
                     + cambios(comp, ("actual", "fijo", "actuadoaj"), f"nudo, {n}")
                     + [etiqueta_citable(tl.etiquetas(comp), estable)])
        primera = ""
    filas.append("\\midrule")
    primera = "El corredor"
    for n, d in datos.items():
        estable = convergio(d["carpeta"], "completo", d["citado"]["completo"])[0]
        filas.append([primera, f"{NIVELES[n][0]} ({miles(d['veh'])}~veh/h)"]
                     + cambios(d["comp"], ("tipico", "fijo", "actuadoaj"), f"corredor, {n}")
                     + [etiqueta_citable(d["etiquetas"], estable)])
        primera = ""
    escribir("lima_resumen.tex",
             ["Casos de Lima: cambio del retraso total con el modelo completo frente a cada referencia, en las tandas 1 y",
              "2 (%), y veredicto frente al fijo ajustado al segundo (regla de la tesis; la etiqueta se repite en las dos",
              "tandas; (sin estabilizar) = el entrenamiento citado no se estabilizo).",
              "fuente: lima/salidas/ y lima/alta/salidas/ (nudo, entrenamientos citados: "
              + ", ".join(f"{n} {b}" for n, b in bases_nudo.items()) + "); lima/corredor/salidas/ y lima/corredor/alta/"
              "salidas/ (corredor, entrenamientos citados: "
              + ", ".join(f"{n} {d['citado']['completo']}" for n, d in datos.items()) + ")."],
             tp.tabular(f"{tp.IZQ}{{1.7cm}}{tp.IZQ}{{2.5cm}}{tp.IZQ}{{2.3cm}}{tp.IZQ}{{2.3cm}}{tp.IZQ}{{2.3cm}}{tp.IZQ}{{2.5cm}}",
                        ["Caso", "Demanda", "Frente al plan de hoy (\\%)", "Frente al fijo ajustado (\\%)",
                         "Frente al actuado ajustado (\\%)", "Veredicto"], filas))


# ---------------- Figuras ----------------
def figura_mapa():
    """Esquema del corredor: la avenida, sus seis cruces con semaforo a escala, el sentido de cada transversal y,
    bajo cada cruce, los vehiculos por hora que entran a el en el escenario (entre parentesis, el publicado)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    via, alto = "#c9c8c0", 210.0
    totales = corredor.totales_por_cruce()
    xs = [x for _, _, x, _, _ in corredor.CRUCES]
    with plt.rc_context(tl.estilo()):
        fig, ax = plt.subplots(figsize=(6.6, 3.4), facecolor=tp.FONDO)
        ax.set_facecolor(tp.FONDO)
        x0, x1 = xs[0] - 430, xs[-1] + 150
        ax.plot([x0, x1], [0, 0], color=via, lw=9, solid_capstyle="butt", zorder=1)
        ax.text(x0, 34, "Av. Alfredo Benavides", ha="left", va="bottom", fontsize=7.8, color=tp.TINTA)
        ax.annotate("", xy=(x0 + 70, alto * 0.95), xytext=(x0 + 70, alto * 0.55),
                    arrowprops=dict(arrowstyle="-|>", color=tp.TINTA2, lw=0.9, mutation_scale=9))
        ax.text(x0 + 70, alto * 0.99, "N", ha="center", va="bottom", fontsize=7.4, color=tp.TINTA2)
        flecha = dict(arrowstyle="-|>", color=tp.TINTA2, lw=0.9, mutation_scale=7)
        for c, calle, x, n, s in corredor.CRUCES:
            doble = bool(n and s)                  # doble sentido: banda ancha y una flecha por sentido
            ax.plot([x, x], [-alto, alto], color=via, lw=9 if doble else 5, solid_capstyle="butt", zorder=1)
            for lado in (1, -1):                   # los dos tramos de la transversal: al norte y al sur de la avenida
                a, b = sorted((lado * alto * 0.42, lado * alto * 0.80))
                if s:                              # sentido hacia el norte (carril del lado este)
                    px = x + (13 if doble else 0)
                    ax.annotate("", xy=(px, b), xytext=(px, a), arrowprops=flecha, zorder=3)
                if n:                              # sentido hacia el sur
                    px = x - (13 if doble else 0)
                    ax.annotate("", xy=(px, a), xytext=(px, b), arrowprops=flecha, zorder=3)
            ax.plot(x, 0, "o", ms=7.5, mfc=AZUL, mec=tp.FONDO, mew=1.2, zorder=4)
            ax.text(x - 12, alto + 22, calle, rotation=40, rotation_mode="anchor", ha="left", va="bottom",
                    fontsize=7.4, color=tp.TINTA)
            rotulo = f"{totales[c]:.0f}" + (f"\n({corredor.PUBLICADO[c]})" if c in corredor.PUBLICADO else "")
            ax.text(x, -alto - 22, rotulo, ha="center", va="top", fontsize=7.2, color=tp.TINTA, linespacing=1.3)
        for a, b in zip(xs, xs[1:]):               # distancia entre cruces contiguos
            ax.text((a + b) / 2, -30, f"{b - a:.0f} m", ha="center", va="top", fontsize=6.2, color=tp.TINTA2)
        # carriles de la avenida por sentido: cambian en el cruce con Paseo de la Republica
        cambio = next(k for k, c in enumerate(corredor.IDS) if corredor.CARRILES_AV[c] != corredor.CARRILES_AV["W"])
        for a, b, carriles in ((xs[cambio - 1], xs[cambio], corredor.CARRILES_AV["W"]),
                               (xs[-2], xs[-1], corredor.CARRILES_AV[corredor.IDS[-1]])):
            ax.text((a + b) / 2, 32, f"{carriles} carriles\npor sentido", ha="center", va="bottom", fontsize=6.6,
                    color=tp.TINTA2, linespacing=1.25)
        ax.text(x0, -alto - 22, "Entran, veh/h\n(publicado)", ha="left", va="top", fontsize=7.0,
                color=tp.TINTA2, linespacing=1.3)
        ax.set_xlim(x0 - 10, x1 + 330)
        ax.set_ylim(-alto - 130, alto + 345)
        ax.axis("off")
        fig.tight_layout(pad=0.3)
        tl.guardar(fig, "fig_corredor_mapa", plt)


def figura_retraso(datos):
    """Retraso total por vehiculo de cada control (tanda 1), un panel por nivel de demanda. Una sola serie: las
    referencias en gris y el modelo en azul; el nombre de cada barra va en el eje y el valor, sobre la barra."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    corto = {"tipico": "Plan\ntípico", "fijo": "Fijo ajustado\nal segundo", "actuadoaj": "Actuado\najustado"}
    with plt.rc_context(tl.estilo()):
        fig, ejes = plt.subplots(1, len(datos), figsize=(3.6 * len(datos), 3.4), facecolor=tp.FONDO, squeeze=False)
        for ax, (n, d) in zip(ejes[0], datos.items()):
            brazos = [b for b in PRINCIPALES if b in d["medias"][1]] + [d["modelo"]]
            valores = [d["medias"][1][b] for b in brazos]
            tl.limpiar(ax)
            barras = ax.bar(range(len(brazos)), valores, width=0.5, color=[GRIS] * (len(brazos) - 1) + [AZUL], zorder=3)
            for b, v in zip(barras, valores):
                ax.annotate(uno(v), (b.get_x() + b.get_width() / 2, v), xytext=(0, 3), textcoords="offset points",
                            ha="center", va="bottom", fontsize=8.2, color=tp.TINTA)
            ax.set_ylim(0, max(valores) * 1.16)
            ax.set_xticks(range(len(brazos)))
            ax.set_xticklabels([corto.get(b, "Modelo\ncompleto") for b in brazos], fontsize=7.8, color=tp.TINTA,
                               linespacing=1.25)
            ax.set_title(f"Demanda {NIVELES[n][0].lower()}: {miles(d['veh'], False)} veh/h", fontsize=8.4, color=tp.TINTA2, loc="left")
        ejes[0][0].set_ylabel("Retraso total (s por vehículo)", fontsize=8.2)
        fig.tight_layout(w_pad=2.0)
        tl.guardar(fig, "fig_corredor_retraso", plt)


def figura_aprendizaje(datos):
    """Retraso total en las semillas de validacion a lo largo de los entrenamientos de los tres modelos, con el fijo
    ajustado y el actuado ajustado en las mismas semillas. Un panel por nivel. Un color por modelo; de cada modelo,
    el entrenamiento citado va con linea gruesa y los otros dos con linea fina."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    color = {"completo": AZUL, "corregido": NARANJA, "sinmsg": AGUA}
    with plt.rc_context(tl.estilo()):
        fig, ejes = plt.subplots(len(datos), 1, figsize=(6.2, 2.8 * len(datos) + 0.6), facecolor=tp.FONDO, squeeze=False)
        for ax, (n, d) in zip(ejes[:, 0], datos.items()):
            carpeta = d["carpeta"]
            referencias = leer_json(carpeta, "val_referencias.json")["retraso_total"]
            tl.limpiar(ax)
            ultimo, todos = 0, []
            for clave in ("sinmsg", "corregido", "completo"):          # el modelo completo se dibuja encima
                for base in sorted(BASES, key=lambda b: b == d["citado"][clave]):
                    serie = serie_validacion(carpeta, clave, base)
                    xs, ys = [e for e, _ in serie], [v for _, v in serie]
                    ultimo = max(ultimo, xs[-1])
                    todos += ys[1:]                 # la primera validacion puede quedar fuera de la escala
                    citado = base == d["citado"][clave]
                    ax.plot(xs, ys, color=color[clave], lw=1.9 if citado else 0.8, alpha=1.0 if citado else 0.55,
                            zorder=4 if citado else 3, solid_joinstyle="round")
            for ref in ("fijo", "actuadoaj"):
                if ref in referencias:
                    todos.append(referencias[ref])
                    ax.axhline(referencias[ref], color=GRIS, lw=1.0, zorder=2)
            # las dos referencias quedan muy cerca: sus rotulos se separan a mano para que no se pisen
            arriba = max(("fijo", "actuadoaj"), key=lambda r: referencias.get(r, 0))
            for ref in ("fijo", "actuadoaj"):
                if ref in referencias:
                    ax.annotate(NOMBRE[ref].replace(" al segundo", "\nal segundo") + f": {referencias[ref]:.1f}",
                                (ultimo, referencias[ref]), xytext=(5, 2 if ref == arriba else -2),
                                textcoords="offset points", ha="left", va="bottom" if ref == arriba else "top",
                                fontsize=7.2, color=tp.TINTA2, linespacing=1.15, annotation_clip=False)
            ax.set_xlim(0, ultimo)
            # eje vertical acercado: las diferencias son de pocos segundos y con el eje desde cero no se verian
            margen = (max(todos) - min(todos)) * 0.12
            ax.set_ylim(min(todos) - margen, max(todos) + margen)
            ax.set_ylabel("Retraso total en la\nvalidación (s por vehículo)", fontsize=8.0, linespacing=1.35)
            ax.set_title(f"Demanda {NIVELES[n][0].lower()}: {miles(d['veh'], False)} veh/h", fontsize=8.4, color=tp.TINTA2, loc="left")
        ejes[-1, 0].set_xlabel("Episodio de entrenamiento", fontsize=8.2)
        leyenda = [Line2D([], [], color=color[c], lw=1.9, label=MODELOS[c][1]) for c in ("completo", "corregido", "sinmsg")]
        leyenda.append(Line2D([], [], color=GRIS, lw=1.0, label="Referencias, en las mismas semillas"))
        fig.legend(handles=leyenda, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.0), frameon=False, fontsize=7.6,
                   labelcolor=tp.TINTA, handlelength=1.6, columnspacing=1.6)
        fig.tight_layout(rect=(0, 0, 0.82, 1 - 0.52 / (2.8 * len(datos) + 0.6)), h_pad=1.4)
        tl.guardar(fig, "fig_corredor_aprendizaje", plt)


# ---------------- Resultado final: los seis casos del segundo estudio y los dos de Lima ----------------
# 15.11.2026, pedido del asesor (reunion del 13.11): los casos de Lima entran en la tabla final con los del segundo
# estudio, y las graficas ordenan los casos de menor a mayor demanda total.
ORDEN_SINTETICOS = ["P1", "P3", "P4", "P2", "P5", "P6"]          # 1810, 2150, 2580, 3620, 4350 y 8700 veh/h


def casos_finales(datos, bases_nudo):
    """Una entrada por caso con llegadas aleatorias: los seis del segundo estudio, de menor a mayor demanda, y despues
    los de Lima (nudo y corredor, cada uno con su demanda publicada y la alta). Por tanda (1 y 2): cambio frente al
    fijo ajustado al segundo con su IC95 y el veredicto de la tanda, y cambio frente al actuado ajustado."""
    celdas = {(r["celda"], r["llegadas"]): r for r in tp.leer_csv("veredicto3_celdas.csv")}
    comp3 = tp.leer_csv("veredicto3_comparaciones.csv")

    def tandas_plan3(r):
        res = {}
        for k, t in ((1, "T1"), (2, "T2")):
            ver, pendiente = tp.punto_etiqueta(r[f"etiqueta_{t}"])
            res[k] = {"fijo": float(r[f"cambio_{t}"]), "ic": tuple(float(v) for v in r[f"ic_{t}"].strip("[]").split(",")),
                      "veredicto": ver, "pendiente": pendiente}
        return res

    casos = []
    for c in ORDEN_SINTETICOS:
        red, demanda, veh = tp.CASOS[c]
        r = celdas[(c, "aleatorias")]
        fijo, _, modelo = tp.retrasos(celdas, comp3, c)
        tandas = tandas_plan3(r)
        for k, t in ((1, "T1"), (2, "T2")):
            fila = [x for x in comp3 if x["celda"] == c and x["llegadas"] == "aleatorias" and x["tanda"] == t
                    and x["clave"] == r["clave_citado"] and x["referencia"] == "actuado ajustado"
                    and x["metrica"] == "retraso_total_prom"]
            tandas[k]["actuado"] = float(fila[0]["cambio"])
        casos.append({"caso": c, "red": {"corredor": "corredor", "red con rotonda": "red", "malla": "malla"}[red],
                      "lugar": f"{red.capitalize()}, {demanda}", "veh": veh, "fijo": fijo, "modelo": modelo,
                      "tandas": tandas, "veredicto": tp.etiqueta(r["etiqueta_citable"]),
                      "regulares": tandas_plan3(celdas[(c, "regulares")]),
                      "veredicto_reg": tp.etiqueta(celdas[(c, "regulares")]["etiqueta_citable"])})

    def lima(nombre, red, demanda, veh, comp, medias, modelo, etiquetas, estable):
        tandas = {t: {"fijo": comp[t]["fijo"]["delta"], "ic": tuple(comp[t]["fijo"]["ic"]), "veredicto": etiquetas[t],
                      "pendiente": not estable, "actuado": comp[t]["actuadoaj"]["delta"]} for t in (1, 2)}
        return {"caso": "Lima", "red": red, "lugar": f"{nombre}, {demanda}", "veh": veh, "fijo": medias[1]["fijo"],
                "modelo": medias[1][modelo], "tandas": tandas, "veredicto": etiqueta_citable(etiquetas, estable),
                "regulares": None, "veredicto_reg": None}

    for n, base in bases_nudo.items():
        carpeta = tl.NIVELES[n][1]
        comp, medias = tl.comparaciones(carpeta, f"completo_s{base}")
        casos.append(lima("Nudo", "nudo", NIVELES[n][0].lower(), round(4271 * tl.NIVELES[n][2]), comp, medias,
                          f"completo_s{base}", tl.etiquetas(comp), tl.convergio(carpeta, base)[0]))
    for n, d in datos.items():
        casos.append(lima("Corredor Benavides", "benavides", NIVELES[n][0].lower(), round(d["veh"]), d["comp"],
                          d["medias"], d["modelo"], d["etiquetas"],
                          convergio(d["carpeta"], "completo", d["citado"]["completo"])[0]))
    return casos


def tabla_final(casos):
    filas, primera_lima = [], True
    for c in casos:
        if c["caso"] == "Lima":
            if primera_lima:
                filas.append("\\midrule")
            nombre, primera_lima = ("Lima" if primera_lima else ""), False
        else:
            nombre = c["caso"]
        t = c["tandas"]
        filas.append([nombre, c["lugar"], miles(c["veh"]), f"{c['fijo']:.1f}", f"{c['modelo']:.1f}",
                      f"{tp.num(t[1]['fijo'])} y {tp.num(t[2]['fijo'])}",
                      f"{tp.num(t[1]['actuado'])} y {tp.num(t[2]['actuado'])}", c["veredicto"]])
    escribir("resultado_final.tex",
             ["Resultado final: todos los casos con llegadas aleatorias, de menor a mayor demanda (los seis del segundo",
              "estudio y los dos de Lima con sus dos demandas). Retraso total por vehiculo con el fijo ajustado al",
              "segundo y con el modelo en la tanda 1; cambio del modelo frente al fijo ajustado al segundo y frente al",
              "actuado ajustado en las tandas 1 y 2 (100 semillas cada una); veredicto que se repite en las dos.",
              "fuente: plan3/salidas/veredicto3_celdas.csv y veredicto3_comparaciones.csv (tablas_plan3.retrasos; frente",
              "al actuado: referencia 'actuado ajustado' del modelo citado); Lima: lima/salidas/, lima/alta/salidas/,",
              "lima/corredor/salidas/ y lima/corredor/alta/salidas/ (eval_t1_*.csv y eval_t2_*.csv, estudio.comparar).",
              "Entorno: \\setstretch{1}, \\footnotesize y \\setlength{\\tabcolsep}{3pt}."],
             tp.tabular(f"l{tp.IZQ}{{2.2cm}}r{DER}{{1.35cm}}{DER}{{1.15cm}}{tp.IZQ}{{2.3cm}}{tp.IZQ}{{2.3cm}}"
                        f"{tp.IZQ}{{2.15cm}}",
                        ["Caso", "Red y demanda", "Veh/h", "Fijo ajustado al segundo (s/veh)", "Modelo (s/veh)",
                         "Frente al fijo, tandas 1 y 2 (\\%)", "Frente al actuado ajustado, tandas 1 y 2 (\\%)",
                         "Veredicto"], filas))


# Lugares de la figura final: nombre, color, forma y tamano. Los tres primeros son los de la Figura de los niveles de
# demanda (curvas_demanda.py, fig:efecto-demanda); los de Lima, dos colores mas de la misma paleta.
LUGARES = {"corredor": ("Corredor (P1 y P2)", "#2a78d6", "o", 7.6),
           "red": ("Red con rotonda (P3 y P4)", "#eb6834", "s", 6.9),
           "malla": ("Malla 3×3 (P5 y P6)", "#1baf7a", "^", 8.2),
           "nudo": ("Lima: el nudo", "#8a5cd6", "D", 6.6),
           "benavides": ("Lima: el corredor de Benavides", "#c2477a", "p", 8.2)}
# rotulo de cada caso del segundo estudio en cada panel: desplazamiento en puntos y alineacion
ROTULO = {"tandas": {"P1": (-9, 0, "right"), "P2": (9, 0, "left"), "P3": (0, 11, "center"), "P4": (0, -12, "center"),
                     "P5": (0, 11, "center"), "P6": (-9, 0, "right")},
          "regulares": {"P1": (-9, 0, "right"), "P2": (9, -3, "left"), "P3": (0, 11, "center"),
                        "P4": (9, 3, "left"), "P5": (0, 11, "center"), "P6": (9, -5, "left")}}


def fusion(tandas):
    """Un punto por caso: el promedio del cambio de las dos tandas, y una barra que va del extremo inferior al superior
    de sus dos IC95 (asi la barra no dice nada que no digan los dos intervalos ya publicados)."""
    y = (tandas[1]["fijo"] + tandas[2]["fijo"]) / 2
    return y, (min(tandas[k]["ic"][0] for k in (1, 2)), max(tandas[k]["ic"][1] for k in (1, 2)))


def palabra(citable):
    """('FUNCIONA', False), o ('FUNCIONA', True) si el veredicto lleva la marca (sin estabilizar)."""
    if citable.endswith(" (sin estabilizar)"):
        return citable[:-len(" (sin estabilizar)")], True
    return citable, False


def figura_final(casos):
    """Cambio del retraso total del modelo frente al fijo ajustado al segundo segun la demanda total (escala
    logaritmica), una linea por lugar y el veredicto en el relleno del marcador, como la Figura de los niveles de
    demanda. Un punto por caso: el promedio de las dos tandas. Arriba, llegadas aleatorias (los seis casos del segundo
    estudio y los de Lima); abajo, llegadas regulares (solo los del segundo estudio)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FixedLocator, NullLocator
    menos = "−"
    x0, x1 = 1450, 13500
    rojo, pequena, clara = tp.mezcla(tp.ROJO, 0.09), tp.mezcla(tp.VERDE, 0.06), tp.mezcla(tp.VERDE, 0.15)

    def banda(y):
        return rojo if y > 0 else (pequena if y > tp.UMBRAL else clara)

    def marcador(ax, x, y, lugar, ver, pendiente):
        _, color, forma, tam = LUGARES[lugar]
        ms = tam + (1.2 if ver == "MEJORA" else 0)
        # anillo del color de la banda: separa el marcador de las lineas que pasan cerca
        ax.plot(x, y, forma, ms=ms + 2.6, mfc=banda(y), mec=banda(y), mew=0, zorder=4.6)
        if ver == "EMPATA":
            ax.plot(x, y, forma, ms=tam, mfc=tp.FONDO, mec=color, mew=1.4, zorder=5)
        elif ver == "MEJORA":
            ax.plot(x, y, forma, ms=ms, fillstyle="bottom", mfc=color, markerfacecoloralt=tp.FONDO, mec=color,
                    mew=0.5, zorder=5)
        else:                                          # FUNCIONA o FALLA: la banda dice cual
            ax.plot(x, y, forma, ms=tam, mfc=color, mec=color, mew=1.0, zorder=5)
        if pendiente:                                  # entrenamiento sin estabilizar: anillo punteado alrededor
            ax.scatter([x], [y], s=(ms + 4.4) ** 2, marker=forma, facecolors="none", edgecolors=tp.TINTA,
                       linewidths=1.0, linestyle=(0, (1.2, 1.2)), zorder=5.5)

    def panel(ax, clave, y0, y1, titulo):
        ax.set_facecolor(tp.FONDO)
        ax.set_xscale("log")
        ax.axhspan(y0, tp.UMBRAL, color=clara, lw=0, zorder=0)
        ax.axhspan(tp.UMBRAL, 0, color=pequena, lw=0, zorder=0)
        ax.axhspan(0, y1, color=rojo, lw=0, zorder=0)
        ax.axhline(0, color=tp.APAGADO, lw=0.9, zorder=2)
        rot = dict(fontsize=6.9, color=tp.TINTA2, linespacing=1.25, zorder=2)
        if y0 < tp.META:                               # los rotulos de las bandas solo en el panel de arriba
            ax.text(x1 / 1.03, y1 - 0.5, "Más retraso que el fijo: FALLA si es significativo", ha="right", va="top",
                    **rot)
            ax.text(x1 / 1.03, tp.UMBRAL / 2, f"Mejora pequeña, entre {menos}5 y 0 %:\nMEJORA si es significativa",
                    ha="right", va="center", **rot)
            ax.axhline(tp.META, color=tp.TINTA2, lw=0.9, ls=(0, (1, 2.2)), zorder=2)
            ax.text(x0 * 1.03, tp.META + 0.5, f"meta de la tesis: {menos}25 %", ha="left", va="bottom", **rot)
            ax.text(x0 * 1.03, y0 + 0.6, f"Mejora clara, de {menos}5 % o más negativo: FUNCIONA si es significativa\n"
                    "y el modelo no tiene más retraso que el actuado ajustado", ha="left", va="bottom", **rot)
        for lugar, (_, color, _, _) in LUGARES.items():
            serie = sorted((c for c in casos if c["red"] == lugar and c[clave] is not None), key=lambda c: c["veh"])
            if not serie:
                continue
            puntos = [(c["veh"],) + fusion(c[clave]) + (c,) for c in serie]
            ax.plot([p[0] for p in puntos], [p[1] for p in puntos], color=color, lw=1.4, zorder=3,
                    solid_joinstyle="round", solid_capstyle="round")
            for x, y, (lo, hi), c in puntos:
                ax.plot([x, x], [lo, hi], color=color, lw=1.1, zorder=4, solid_capstyle="butt")
                ver, pendiente = palabra(c["veredicto"] if clave == "tandas" else c["veredicto_reg"])
                marcador(ax, x, y, lugar, ver, pendiente)
                if c["caso"] != "Lima":
                    dx, dy, lado = ROTULO[clave][c["caso"]]
                    ax.annotate(c["caso"], (x, y), xytext=(dx, dy), textcoords="offset points", ha=lado,
                                va="center", fontsize=7.6, color=tp.TINTA, fontweight="bold", zorder=6)
                elif clave == "tandas" and c is serie[0]:    # Lima: el nombre junto a su demanda publicada
                    ax.annotate({"nudo": "Nudo", "benavides": "Benavides"}[lugar], (x, y), xytext=(-9, 0),
                                textcoords="offset points", ha="right", va="center", fontsize=7.6, color=tp.TINTA,
                                fontweight="bold", zorder=6)
                elif clave == "tandas":                      # y "alta" junto a la demanda alta (el punto del nudo
                    ax.annotate("alta", (x, y), xytext=(9, 0),   # cae sobre la linea de la malla)
                                textcoords="offset points", ha="left", va="center", fontsize=7.2, color=tp.TINTA,
                                zorder=6)
        ax.set_xlim(x0, x1)
        ax.xaxis.set_major_locator(FixedLocator([2000, 3000, 4000, 6000, 8000, 10000]))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xticklabels([miles(v, False) for v in (2000, 3000, 4000, 6000, 8000, 10000)], fontsize=7.4)
        ax.set_ylim(y0, y1)
        marcas = [m for m in range(-30, 6, 5) if y0 <= m <= y1]
        ax.set_yticks(marcas)
        ax.set_yticklabels([f"{t:+d}".replace("-", menos) if t else "0" for t in marcas], fontsize=7.4)
        ax.tick_params(length=0)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.set_title(titulo, fontsize=8.0, color=tp.TINTA, loc="left")
        ax.set_ylabel("Cambio del retraso total frente al\nfijo ajustado al segundo (%)", fontsize=7.6, linespacing=1.3)

    with plt.rc_context(tl.estilo()):
        fig, (arriba, abajo) = plt.subplots(2, 1, figsize=(7.0, 7.1), facecolor=tp.FONDO,
                                            gridspec_kw={"height_ratios": [2.1, 1.0], "hspace": 0.3})
        panel(arriba, "tandas", -32.0, 6.0, "(a) Llegadas aleatorias: los seis casos del segundo estudio y los de Lima")
        panel(abajo, "regulares", -7.0, 5.0,
              "(b) Llegadas regulares: IPPO con mensajes corregido en los seis casos del segundo estudio")
        abajo.set_xlabel("Demanda total (veh/h, escala logarítmica)", fontsize=7.8)
        p = dict(ls="", ms=7.0)
        por_lugar = [Line2D([], [], marker=forma, mfc=color, mec=color, color=color, lw=1.4, ms=tam, label=nombre)
                     for nombre, color, forma, tam in LUGARES.values()]
        por_veredicto = [
            Line2D([], [], marker="o", mfc=tp.TINTA2, mec=tp.TINTA2, label="FUNCIONA o FALLA, según la banda", **p),
            Line2D([], [], marker="o", fillstyle="bottom", mfc=tp.TINTA2, markerfacecoloralt=tp.FONDO, mec=tp.TINTA2,
                   mew=0.5, label="MEJORA", **dict(p, ms=8.2)),
            Line2D([], [], marker="o", mfc=tp.FONDO, mec=tp.TINTA2, mew=1.4, label="EMPATA", **p),
            arriba.scatter([], [], s=9.6 ** 2, marker="o", facecolors="none", edgecolors=tp.TINTA, linewidths=1.0,
                           linestyle=(0, (1.2, 1.2)), label="Borde punteado: entrenamiento sin estabilizar"),
            Line2D([], [], marker="|", ms=10, mew=1.1, color=tp.TINTA2, ls="",
                   label="Barra: de un extremo a otro de los IC95 de las dos tandas")]
        comun = dict(fontsize=7.2, title_fontsize=7.4, handletextpad=0.5, alignment="left", labelcolor=tp.TINTA,
                     frameon=False)
        # las dos leyendas, una al lado de la otra, sobre el panel de arriba
        ley1 = fig.legend(handles=por_lugar, ncol=1, loc="upper left", bbox_to_anchor=(0.04, 1.0),
                          title="Lugar: color y forma\n(cada punto: promedio de las dos tandas)", handlelength=2.4,
                          labelspacing=0.3, **comun)
        ley2 = fig.legend(handles=por_veredicto, ncol=1, loc="upper left", bbox_to_anchor=(0.47, 1.0),
                          title="Veredicto que se repite en las dos tandas:\nrelleno del marcador", handlelength=1.6,
                          labelspacing=0.3, **comun)
        for ley in (ley1, ley2):
            ley.get_title().set_color(tp.TINTA2)
        fig.subplots_adjust(top=0.79)
        tl.guardar(fig, "fig_resultado_final", plt)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--niveles", default="publicada", help="niveles de demanda, separados por coma: publicada,alta")
    ap.add_argument("--destino", default=None, help="(pruebas) carpeta donde escribir todo, en vez de TESIS/")
    ap.add_argument("--solo-mapa", action="store_true", help="solo la tabla de cruces y el esquema del corredor")
    ap.add_argument("--nudo", default="publicada=42,alta=42",
                    help="entrenamiento citado del nudo en cada nivel, para la tabla resumen de los dos casos")
    args = ap.parse_args()
    if args.destino:
        os.makedirs(args.destino, exist_ok=True)
        tl.DESTINO.update(tablas=args.destino, imagenes=args.destino)
    tabla_cruces()
    figura_mapa()
    if args.solo_mapa:                 # lo que no necesita la evaluacion: los cruces, el esquema y los planes fijos
        tabla_planes({n: {"carpeta": NIVELES[n][1]} for n in args.niveles.split(",")})
        return 0
    datos = {n: cargar(n) for n in args.niveles.split(",")}
    bases_nudo = {n: int(b) for n, b in (x.split("=") for x in args.nudo.split(","))}
    tabla_resumen(datos, bases_nudo)
    if set(datos) == {"publicada", "alta"}:
        casos = casos_finales(datos, bases_nudo)
        tabla_final(casos)
        figura_final(casos)
    tabla_planes(datos)
    tabla_resultado(datos)
    tabla_mensajes(datos)
    tabla_completa(datos)
    tabla_entrenamientos(datos)
    if "publicada" in datos:
        tabla_robustez(datos["publicada"])
    figura_retraso(datos)
    figura_aprendizaje(datos)
    for n, d in datos.items():
        print(f"Demanda {n}: entrenamientos citados", d["citado"])
        ok, plateau, estab = convergio(d["carpeta"], "completo", d["citado"]["completo"])
        for t, e in d["etiquetas"].items():
            print(f"  veredicto de la tanda {t}: {e}" + ("" if ok else " (PENDIENTE: el entrenamiento citado no se "
                  f"estabilizo, plateau {plateau:+.2f} %, estabilidad {estab:.2f} %; provisional)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
