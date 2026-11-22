"""
evaluar_ovalo.py - Estudio del nudo en la red del Ovalo Vasco (enmienda del 18.11.2026 en lima/REGISTRO.md): evalua las
referencias y los dos modelos en las dos tandas, la prueba de robustez del reparto, y calcula los veredictos.

Uso (en Git Bash o PowerShell, desde cualquier carpeta; cada paso se puede cortar y volver a lanzar: lo ya evaluado no
se repite):
  python evaluar_ovalo.py referencias [--procesos 8]   tras referencias.sh: plan actual, fijo ajustado, actuado,
                                                       actuado ajustado (y el de antes del borde, si cambio) y ciclo
                                                       minimo, en las dos tandas y las dos demandas
  python evaluar_ovalo.py modelos [--procesos 8]       tras los 12 entrenamientos: primero el entrenamiento citado de
                                                       cada modelo en las dos tandas, despues los otros dos
  python evaluar_ovalo.py robustez [--procesos 8]      prueba de robustez del reparto (24001-24100), demanda publicada
  python evaluar_ovalo.py veredicto                    no simula: salidas_ovalo/veredicto_ovalo.md y .json (con
                                                       --nivel, veredicto_ovalo_<nivel>.md y .json)
--nivel publicada|alta (referencias, modelos y veredicto): solo esa demanda; sirve para evaluar la publicada en cuanto
terminan sus entrenamientos, mientras la alta sigue entrenando.
--comprobar, con cualquier paso: no simula; comprueba las huellas y la procedencia, y dice que correria y que falta.
Prueba del programa (solo semillas de humo): --prueba CARPETA corre todo sobre CARPETA (una copia de demo_rl/lima con
politicas de humo, la arma pruebas/lanzadores/probar.py) con las tandas 424341-424344 y 424345-424348 y la robustez en
424349-424352.

Antes de evaluar comprueba la procedencia y se detiene si no es la de la enmienda: los archivos de huellas.sha256 (el
codigo y los datos) no cambiaron, y cada politica se entreno con ese codigo (sha256_codigo de su meta).

Modelos (bases 42, 2042 y 4042; 400 episodios; validacion cada 20 en 21001-21008 por retraso total):
  libre      el modelo de orden libre (--orden-libre): el modelo CITADO del nudo
  completo   el modelo de orden fijo del estudio, en la misma red
Version citada de cada modelo y nivel: el de validacion mediana entre los tres (veredicto.base_mediana sobre
val_elegido). Estabilizacion: veredicto.convergencia sobre val_total (si no se estabilizo, provisional).
Comparaciones, tanda por tanda (estudio.comparar: cambio %, IC95 por bootstrap pareado y p de Wilcoxon pareado; regla
veredicto.veredicto; la etiqueta citable es la que se repite en las dos tandas, si no EMPATA):
  (1) libre frente al fijo ajustado, sin perder contra el actuado ajustado: el veredicto del nudo;
  (2) libre frente al modelo de orden fijo (la misma regla, con el de orden fijo en el lugar del fijo): lo que aporta
      elegir el orden en la misma red. Al lado, la media por semilla de los tres entrenamientos de cada modelo, cada
      entrenamiento y el rango entre sus medias;
  (3) el de orden fijo frente al fijo ajustado, sin perder contra el actuado ajustado: se informa al lado;
  (4) frente al plan actual: el cambio, sin etiqueta. El actuado por defecto y el ciclo minimo, como referencias
      secundarias.
Robustez (demanda publicada, reparto cambiado, sin reajustar ni reentrenar): plan actual, fijo ajustado, actuado
ajustado y el citado de cada modelo en 24001-24100; se informa el retraso de cada control y el cambio del modelo libre
(y al lado, el de orden fijo) frente a cada uno, sin etiqueta.
"""
import argparse
import csv
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DEMO = os.path.join(AQUI, "demo_rl")
ESTUDIO = os.path.join(DEMO, "lima", "estudio.py")
sys.path.insert(0, DEMO)
sys.path.insert(0, os.path.join(DEMO, "lima"))
import estudio                              # noqa: E402  (comparar(), METRICA y las tandas del estudio)
import veredicto as regla                   # noqa: E402

BASES = (42, 2042, 4042)
EPISODIOS = 400
MODELOS = {"libre": "Modelo de orden libre (citado)", "completo": "Modelo de orden fijo"}
NIVELES = {"publicada": "", "alta": "alta"}
PRINCIPALES = ("actual", "fijo", "actuadoaj")
SECUNDARIAS = ("actuado", "minimo", "actuadoajb")
NOMBRE = {"fijo": "Fijo ajustado al segundo", "actuadoaj": "Actuado ajustado", "actual": "Plan actual",
          "actuado": "Actuado por defecto", "minimo": "Ciclo minimo",
          "actuadoajb": "Actuado ajustado antes de la comprobacion del borde", "completo": "Modelo de orden fijo"}
ROBUSTEZ = {"reducto": os.path.join("robustez", "reducto"), "transversal": os.path.join("robustez", "transversal")}
SEMILLAS_ROBUSTEZ = list(range(24001, 24101))
PRUEBA = {"tandas": {1: list(range(424341, 424345)), 2: list(range(424345, 424349))},
          "robustez": list(range(424349, 424353))}
PROGRAMAS = ("demo_rl/rl_ippo.py", "demo_rl/lima/estudio.py", "demo_rl/lima/programa_ovalo.py",
             "demo_rl/lima/ovalo/plan_ovalo.py", "entrenar.sh", "referencias.sh", "evaluar_ovalo.py",
             "comprobar_fases.py")


def sha256(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def huellas():
    """{archivo: sha256} de huellas.sha256, despues de comprobar que los archivos son esos; si alguno cambio, se
    detiene."""
    esperadas = {}
    with open(os.path.join(AQUI, "huellas.sha256"), encoding="utf-8") as f:
        for linea in f:
            h, nombre = linea.split(maxsplit=1)
            esperadas[nombre.strip().lstrip("*")] = h
    distintos = [n for n, h in esperadas.items() if sha256(os.path.join(AQUI, n)) != h]
    if distintos:
        raise SystemExit(f"Estos archivos no son los de huellas.sha256 (enmienda del 18.11.2026): {distintos}")
    return esperadas


def leer_meta(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


# opciones de entrenar.sh que quedan en el meta de toda politica (rl_ippo.meta_base y opciones_etapas)
OPCIONES = {"v2": True, "criterio_val": "total", "lr_horizonte": 200, "lr_piso": 0.1, "obs_cercana": 75.0,
            "msg_cada_paso": True, "sin_forzadas": True, "paso_decision": 2, "norm_valor": True}


def procedencia(ruta_pt, esperadas, etiqueta, carpeta, prueba=False):
    """Se detiene si la politica no se entreno con el codigo de huellas.sha256 (sha256_codigo de su meta) o con
    opciones que no son las de entrenar.sh: modelo (etiqueta y --orden-libre), episodios, semillas de validacion,
    criterio, y en el libre el programa libre de su carpeta (lima_libre.json). En la prueba del programa (politicas de
    humo de 5 episodios con semillas de humo) no se miran los episodios ni las semillas de validacion."""
    meta = leer_meta(ruta_pt.replace(".pt", ".json"))
    del_meta = meta.get("sha256_codigo")
    if not del_meta:
        raise SystemExit(f"{ruta_pt}: su meta no trae sha256_codigo; no se entreno con este codigo")
    distintos = [n for n, h in del_meta.items() if esperadas.get(f"demo_rl/{n}") != h]
    if distintos:
        raise SystemExit(f"{ruta_pt}: se entreno con otro codigo ({distintos} no coinciden con huellas.sha256)")
    op = meta.get("opciones", {})
    distintas = [k for k, v in OPCIONES.items() if op.get(k) != v]
    if bool(op.get("orden_libre")) != (etiqueta == "libre"):
        distintas.append("orden_libre")
    if (meta.get("etiqueta"), meta.get("variante")) != (etiqueta, "vecinos") or not prueba and \
            (meta.get("episodios"), meta.get("val_seeds")) != (EPISODIOS, list(range(21001, 21009))):
        distintas.append("etiqueta, variante, episodios o semillas de validacion")
    if etiqueta == "libre":
        programa = meta.get("orden_libre", {}).get("semaforo_S1", {}).get("programa", {})
        if programa.get("sha256") != sha256(os.path.join(carpeta, "lima_libre.json")):
            distintas.append("programa libre (lima_libre.json de su carpeta)")
    if distintas:
        raise SystemExit(f"{ruta_pt}: no se entreno con las opciones de entrenar.sh: {distintas}")


def politica(carpeta, etiqueta, base):
    return os.path.join(carpeta, f"politica_lima_vecinos_{etiqueta}_s{base}.pt")


def citada(carpeta, etiqueta):
    """(base citada, {base: val_elegido}): la de validacion mediana de los tres entrenamientos (regla del estudio)."""
    vals = {b: leer_meta(politica(carpeta, etiqueta, b).replace(".pt", ".json"))["val_elegido"] for b in BASES}
    return regla.base_mediana(vals), vals


def estabilidad(carpeta, etiqueta, base):
    """(se estabilizo, tendencia %, estabilidad %) con la regla de la tesis sobre val_total."""
    ruta = os.path.join(carpeta, f"resultados_lima_ippo_vecinos_{etiqueta}_s{base}.csv")
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        serie = [(int(r["episodio"]), float(r["val_total"])) for r in csv.DictReader(f) if r.get("val_total")]
    return regla.convergencia(serie, EPISODIOS)


def leer(ruta):
    """{semilla: retraso total} de un eval_t*_*.csv, o None si no existe."""
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8", newline="") as f:
        return {int(r["semilla"]): float(r[estudio.METRICA]) for r in csv.DictReader(f)}


def sin_terminar(ruta):
    """(media por semilla, semillas con alguno) de los vehiculos que a los 6000 s seguian en la red o sin entrar
    (no_terminados + no_insertados del eval_t*_*.csv): su retraso cuenta hasta el corte, una cota inferior."""
    with open(ruta, encoding="utf-8", newline="") as f:
        n = [int(float(r.get("no_terminados") or 0)) + int(float(r.get("no_insertados") or 0))
             for r in csv.DictReader(f)]
    return statistics.mean(n), sum(1 for x in n if x)


def al_dia(programa, resultados):
    """Se detiene si un programa (o una politica) cambio despues de evaluarlo: estudio.py no repite lo ya evaluado,
    asi que el eval_t*_*.csv seria del programa anterior (por ejemplo, el actuado ajustado de antes del borde)."""
    for ruta in resultados:
        if os.path.exists(ruta) and os.path.getmtime(programa) > os.path.getmtime(ruta):
            raise SystemExit(f"{ruta} es anterior a {programa}: se evaluo otro programa; borrarlo y evaluar otra vez")


def referencias_terminadas(carpeta, nivel):
    """referencias.sh termino este nivel (su ultimo paso escribe val_referencias.json) y la comprobacion del borde
    quedo instalada: el ganador de actuado_ajustado.json y lima_actuadoaj.add.xml son los de borde_actuado.json, y
    lima_actuadoajb.add.xml existe solo si el borde cambio el ganador. referencias.sh salta todo el paso del borde si
    borde_actuado.json ya existe: si se corto entre borde_actuado.py y --instalar, el nuevo ganador no se instala."""
    salidas = os.path.join(carpeta, "salidas")
    for nombre in ("fijo_ajustado.json", "actuado_ajustado.json", "borde_actuado.json", "val_referencias.json"):
        if not os.path.exists(os.path.join(salidas, nombre)):
            falta(f"{nivel}: falta salidas/{nombre}: referencias.sh no termino este nivel")
            return False
    borde = leer_meta(os.path.join(salidas, "borde_actuado.json"))
    ganador = leer_meta(os.path.join(salidas, "actuado_ajustado.json"))["ganador"]
    esperado = borde["ganador"] if borde["cambia"] else borde["ganador_anterior"]
    clave = lambda v: {k: x for k, x in v.items() if not k.startswith("retraso_total") and k != "maximos"}  # noqa
    with open(os.path.join(carpeta, estudio.ARCHIVO["actuadoaj"]), encoding="utf-8") as f:
        instalado = estudio.texto_variante(esperado) in f.read()
    hay_b = os.path.exists(os.path.join(carpeta, estudio.ARCHIVO["actuadoajb"]))
    if clave(ganador) != clave(esperado) or not instalado or hay_b != bool(borde["cambia"]):
        raise SystemExit(f"{nivel}: el actuado ajustado no es el de borde_actuado.json (cambia={borde['cambia']}; "
                         f"actuado_ajustado.json {clave(ganador) == clave(esperado)}, lima_actuadoaj.add.xml "
                         f"{instalado}, lima_actuadoajb.add.xml {hay_b}): instalarlo a mano "
                         "(borde_actuado.py ovalo --instalar) antes de evaluar")
    return True


COMPROBAR = {"activo": False, "falta": []}     # --comprobar: no simula; anota lo que falta


def falta(texto):
    """Lo que falta para un paso: con --comprobar se anota y se sigue; si no, se detiene."""
    if not COMPROBAR["activo"]:
        raise SystemExit(texto)
    COMPROBAR["falta"].append(texto)


def correr_estudio(carpeta, tanda, procesos, brazos="ninguno", politicas=(), semillas=None):
    """Corre "estudio.py evaluar" en la carpeta del caso (LIMA_CARPETA, ruta absoluta). Lo que ya esta no se repite.
    Con --comprobar solo dice que correria."""
    cmd = [sys.executable, ESTUDIO, "evaluar", "--tanda", str(tanda), "--procesos", str(procesos), "--brazos", brazos]
    if politicas:
        cmd += ["--politicas", ",".join(politicas)]
    if semillas:
        cmd += ["--semillas", ",".join(str(s) for s in semillas)]
    if COMPROBAR["activo"]:
        print(f"correria (LIMA_CARPETA={carpeta}): estudio.py evaluar --tanda {tanda} --brazos {brazos}"
              + (f" --politicas {','.join(os.path.basename(p) for p in politicas)}" if politicas else "")
              + (f" --semillas {semillas[0]}-{semillas[-1]}" if semillas else ""))
        return
    subprocess.run(cmd, env={**os.environ, "LIMA_CARPETA": carpeta}, check=True)


def tandas(prueba):
    return PRUEBA["tandas"] if prueba else estudio.TANDAS


# ---------------- pasos que simulan ----------------
def evaluar_referencias(raiz, procesos, prueba, niveles):
    """Las referencias de cada nivel en las dos tandas: primero las tres del veredicto, despues las secundarias."""
    for nivel in niveles:
        carpeta = os.path.join(raiz, NIVELES[nivel])
        if not prueba and not referencias_terminadas(carpeta, nivel):
            continue
        for grupo in (PRINCIPALES, SECUNDARIAS):
            presentes = [b for b in grupo if os.path.exists(os.path.join(carpeta, estudio.ARCHIVO[b]))]
            faltan = [b for b in grupo if b not in presentes and b != "actuadoajb"]
            if faltan:
                falta(f"{nivel}: faltan los programas de {faltan} (los escribe referencias.sh)")
            for b in presentes:
                al_dia(os.path.join(carpeta, estudio.ARCHIVO[b]),
                       [os.path.join(carpeta, "salidas", f"eval_t{t}_{b}.csv") for t in tandas(prueba)])
            if presentes:
                for t, semillas in tandas(prueba).items():
                    correr_estudio(carpeta, t, procesos, ",".join(presentes), semillas=semillas if prueba else None)


def politicas_listas(carpeta, nivel, esperadas, prueba=False):
    """True si estan las seis politicas del nivel y se entrenaron con este codigo (si no, se detiene o se anota)."""
    faltan = [os.path.basename(politica(carpeta, e, b)) for e in MODELOS for b in BASES
              if not os.path.exists(politica(carpeta, e, b))]
    if faltan:
        falta(f"{nivel}: faltan las politicas {faltan} (las entrena entrenar.sh)")
        return False
    for e in MODELOS:
        for b in BASES:
            procedencia(politica(carpeta, e, b), esperadas, e, carpeta, prueba)
    return True


def evaluar_modelos(raiz, procesos, prueba, esperadas, solo_citados, niveles):
    """Los dos modelos de cada nivel: el citado de cada uno en las dos tandas y despues los otros dos."""
    for nivel in niveles:
        carpeta = os.path.join(raiz, NIVELES[nivel])
        if not politicas_listas(carpeta, nivel, esperadas, prueba):
            continue
        citados, otros = [], []
        for etiqueta in MODELOS:
            base, _ = citada(carpeta, etiqueta)
            citados.append(politica(carpeta, etiqueta, base))
            otros += [politica(carpeta, etiqueta, b) for b in BASES if b != base]
        for grupo in ([citados] if solo_citados else [citados, otros]):
            for t, semillas in tandas(prueba).items():
                correr_estudio(carpeta, t, procesos, politicas=grupo, semillas=semillas if prueba else None)


def evaluar_robustez(raiz, procesos, prueba, esperadas):
    """Robustez del reparto: las referencias y el modelo citado de la demanda publicada, sin reajustar ni reentrenar,
    en las dos variantes del reparto (lima/robustez/<variante>/), con 24001-24100."""
    semillas = PRUEBA["robustez"] if prueba else SEMILLAS_ROBUSTEZ
    citados = []
    if not prueba and not referencias_terminadas(raiz, "publicada"):
        return
    if politicas_listas(raiz, "publicada", esperadas, prueba):
        citados = [politica(raiz, e, citada(raiz, e)[0]) for e in MODELOS]
    for variante, sub in ROBUSTEZ.items():
        carpeta = os.path.join(raiz, sub)
        for archivo in (estudio.ARCHIVO["fijo"], estudio.ARCHIVO["actuadoaj"]):
            origen, destino = os.path.join(raiz, archivo), os.path.join(carpeta, archivo)
            if not os.path.exists(origen):
                falta(f"falta {origen} (lo escribe referencias.sh)")
                continue
            if os.path.exists(destino) and sha256(destino) != sha256(origen):
                raise SystemExit(f"{destino} no es el de la demanda publicada")
            if not COMPROBAR["activo"]:
                shutil.copyfile(origen, destino)
        correr_estudio(carpeta, 1, procesos, "actual,fijo,actuadoaj", citados, semillas)


# ---------------- veredicto (no simula) ----------------
def citable(etiquetas):
    return etiquetas[0] if len(set(etiquetas)) == 1 else "EMPATA (no se repite)"


def lectura_orden(etiqueta, separaciones):
    """Lectura de la etiqueta citable de (2) (enmienda del 18.11.2026): si la diferencia entre las medias de los tres
    entrenamientos de cada modelo no supera el rango mayor en las dos tandas, la etiqueta no se distingue de la
    variacion entre entrenamientos. Como en evaluar_control.atribucion (17.11.2026, 19:50), la diferencia tiene que ir
    ademas en el sentido de la etiqueta. separaciones: [(diferencia libre - orden fijo, rango mayor)] por tanda, o
    None si faltan entrenamientos. La etiqueta no cambia."""
    if etiqueta not in ("FUNCIONA", "MEJORA", "FALLA"):
        return "no aplica (la etiqueta no dice quien tiene menos retraso)"
    if len(separaciones) != 2 or None in separaciones:
        return "no se puede decir (faltan entrenamientos sin evaluar)"
    signo = 1 if etiqueta == "FALLA" else -1          # FALLA: el libre por encima; MEJORA y FUNCIONA: por debajo
    if all(signo * dif > rango for dif, rango in separaciones):
        return "se distingue de la variacion entre entrenamientos"
    return "no se distingue de la variacion entre entrenamientos (la etiqueta no cambia)"


def limites(carpeta):
    """Lo que la regla manda decir como limite: el fijo ajustado en el tope de 120 s, y el actuado ajustado otra vez
    en el borde despues de la comprobacion del borde (REGISTRO.md, 14.11.2026, 15:55: no se sigue)."""
    import borde_actuado
    salidas = os.path.join(carpeta, "salidas")
    notas = []
    fijo = leer_meta(os.path.join(salidas, "fijo_ajustado.json"))["ganador"]
    if any(v >= estudio.VERDE_MAX_FIJO for v in fijo):
        notas.append(f"el fijo ajustado {fijo} toca el tope de {estudio.VERDE_MAX_FIJO} s")
    if any(v > estudio.VERDE_MAX for v in fijo):
        notas.append(f"el fijo ajustado {fijo} da verdes de mas de {estudio.VERDE_MAX} s, que el actuado ajustado y "
                     f"los modelos no pueden dar (su verde maximo es {estudio.VERDE_MAX} s)")
    borde = leer_meta(os.path.join(salidas, "borde_actuado.json"))
    g = borde["ganador"]
    en_borde = [p for p, mas in borde_actuado.MAS_ALLA.get(g["tipo"], {}).items() if g.get(p) in mas.values()]
    if borde["cambia"] and en_borde:
        notas.append(f"el actuado ajustado ({estudio.texto_variante(g)}) queda otra vez en el borde ({en_borde}); "
                     "no se sigue: se dice como limite")
    return notas


def fila(nombre, c):
    return (f"| {nombre} | {c['media_ref']:.2f} | {c['media']:.2f} | {c['delta']:+.2f} | "
            f"[{c['ic'][0]:+.2f}, {c['ic'][1]:+.2f}] | {c['p']:.3g} |")


def tres(salidas, etiqueta, t):
    """Los tres entrenamientos de un modelo en una tanda: {base: media}, media por semilla de los tres y su rango."""
    vals = {b: leer(os.path.join(salidas, f"eval_t{t}_{etiqueta}_s{b}.csv")) for b in BASES}
    if any(v is None for v in vals.values()):
        return None
    semillas = sorted(set.intersection(*(set(v) for v in vals.values())))
    por_semilla = {s: statistics.mean(vals[b][s] for b in BASES) for s in semillas}
    medias = {b: statistics.mean(v.values()) for b, v in vals.items()}
    return {"medias": medias, "media_tres": statistics.mean(por_semilla.values()),
            "rango": max(medias.values()) - min(medias.values()), "por_semilla": por_semilla}


def veredicto(raiz, esperadas, prueba, niveles):
    lineas = ["# Nudo en la red del Ovalo Vasco: veredicto del modelo de orden libre", ""]
    if prueba:
        lineas += ["**PRUEBA del programa** con semillas de humo y politicas de humo: los numeros no significan nada.", ""]
    todo = {}
    for nivel in niveles:
        carpeta = os.path.join(raiz, NIVELES[nivel])
        salidas = os.path.join(carpeta, "salidas")
        if not prueba:
            referencias_terminadas(carpeta, nivel)
        politicas_listas(carpeta, nivel, esperadas, prueba)
        for b in PRINCIPALES + SECUNDARIAS:
            if os.path.exists(os.path.join(carpeta, estudio.ARCHIVO[b])):
                al_dia(os.path.join(carpeta, estudio.ARCHIVO[b]),
                       [os.path.join(salidas, f"eval_t{t}_{b}.csv") for t in tandas(prueba)])
        for e in MODELOS:
            for b in BASES:
                al_dia(politica(carpeta, e, b),
                       [os.path.join(salidas, f"eval_t{t}_{e}_s{b}.csv") for t in tandas(prueba)])
        modelos = {}
        for etiqueta in MODELOS:
            base, vals = citada(carpeta, etiqueta)
            ok, tendencia, estab = estabilidad(carpeta, etiqueta, base)
            modelos[etiqueta] = {"base": base, "val_elegido": vals, "estabilizado": ok, "tendencia": tendencia,
                                 "estabilidad": estab, "brazo": f"{etiqueta}_s{base}"}
        lineas += [f"## Demanda {nivel}", ""]
        for etiqueta, m in modelos.items():
            cifras = ("menos de 3 validaciones" if m["tendencia"] is None else
                      f"tendencia {m['tendencia']:+.2f} %, estabilidad {m['estabilidad']:.2f} %")
            lineas.append(f"- {MODELOS[etiqueta]}: version citada base {m['base']} (validacion mediana; val_elegido "
                          f"{m['val_elegido']}); entrenamiento "
                          + ("estabilizado" if m["estabilizado"] else "SIN ESTABILIZAR (provisional)") + f": {cifras}.")
        lineas.append("")
        datos, et, separaciones = {}, {"nudo": [], "orden": [], "fijo_m": []}, []
        for t in tandas(prueba):
            libre = leer(os.path.join(salidas, f"eval_t{t}_{modelos['libre']['brazo']}.csv"))
            completo = leer(os.path.join(salidas, f"eval_t{t}_{modelos['completo']['brazo']}.csv"))
            refs = {r: leer(os.path.join(salidas, f"eval_t{t}_{r}.csv")) for r in PRINCIPALES + SECUNDARIAS}
            faltan = [r for r in PRINCIPALES if refs[r] is None] + [n for n, v in (("libre", libre),
                                                                                   ("completo", completo)) if v is None]
            if faltan:
                raise SystemExit(f"{nivel}, tanda {t}: faltan resultados de {faltan}")
            if not prueba:
                assert sorted(libre) == estudio.TANDAS[t], f"tanda {t}: el modelo no tiene las 100 semillas"
            refs = {r: v for r, v in refs.items() if v is not None}
            assert all(sorted(v) == sorted(libre) for v in list(refs.values()) + [completo]), "semillas distintas"
            comp = {r: estudio.comparar(libre, v) for r, v in refs.items()}
            comp["completo"] = estudio.comparar(libre, completo)
            comp_m = {r: estudio.comparar(completo, refs[r]) for r in ("fijo", "actuadoaj", "actual")}
            f, a, c = comp["fijo"], comp["actuadoaj"], comp["completo"]
            et["nudo"].append(regla.veredicto(f["delta"], f["ic"], f["p"], a["ic"], a["p"]))
            et["orden"].append(regla.veredicto(c["delta"], c["ic"], c["p"], a["ic"], a["p"]))
            fm, am = comp_m["fijo"], comp_m["actuadoaj"]
            et["fijo_m"].append(regla.veredicto(fm["delta"], fm["ic"], fm["p"], am["ic"], am["p"]))
            entrenamientos = {e: tres(salidas, e, t) for e in MODELOS}
            datos[t] = {"libre": comp, "completo": comp_m, "entrenamientos": entrenamientos,
                        "veredictos": {k: v[-1] for k, v in et.items()}}
            lineas += [f"### Tanda {t} ({len(libre)} semillas)", "",
                       "| Frente a | Retraso total de la referencia (s/veh) | Del modelo de orden libre (s/veh) | "
                       "Cambio (%) | IC95 | p |", "|---|---|---|---|---|---|"]
            lineas += [fila(NOMBRE[r], comp[r]) for r in ("fijo", "actuadoaj", "completo", "actual")]
            lineas += [fila(NOMBRE[r], comp[r]) for r in SECUNDARIAS if r in comp]
            cortados = {n: sin_terminar(os.path.join(salidas, f"eval_t{t}_{n}.csv"))
                        for n in list(refs) + [modelos["libre"]["brazo"], modelos["completo"]["brazo"]]}
            datos[t]["sin_terminar"] = cortados
            lineas += ["", "Vehiculos sin terminar o sin entrar a los 6000 s (media por semilla; semillas con alguno; "
                       "su retraso cuenta hasta el corte): "
                       + "; ".join(f"{n} {m:.1f} ({k})" for n, (m, k) in cortados.items())]
            lineas += ["", f"(1) Veredicto del nudo (frente al fijo ajustado, sin perder contra el actuado ajustado): "
                       f"**{et['nudo'][-1]}**",
                       f"(2) Frente al modelo de orden fijo (la misma regla, con el de orden fijo en el lugar del fijo): "
                       f"**{et['orden'][-1]}**",
                       f"(3) El modelo de orden fijo frente al fijo ajustado, sin perder contra el actuado ajustado: "
                       f"**{et['fijo_m'][-1]}** ({comp_m['fijo']['delta']:+.2f} % frente al fijo, "
                       f"{comp_m['actuadoaj']['delta']:+.2f} % frente al actuado ajustado, "
                       f"{comp_m['actual']['delta']:+.2f} % frente al plan actual)"]
            for e, d in entrenamientos.items():
                if d is None:
                    lineas.append(f"Los tres entrenamientos de {MODELOS[e]}: sin evaluar")
                    continue
                lineas.append(f"Los tres entrenamientos de {MODELOS[e]}: " + ", ".join(
                    f"{b} {v:.2f}" for b, v in d["medias"].items()) + f" s/veh; media por semilla de los tres "
                    f"{d['media_tres']:.2f}; rango {d['rango']:.2f}")
            separaciones.append(None)
            if all(entrenamientos.values()):
                dif = entrenamientos["libre"]["media_tres"] - entrenamientos["completo"]["media_tres"]
                rango = max(entrenamientos["libre"]["rango"], entrenamientos["completo"]["rango"])
                datos[t]["diferencia_medias"], datos[t]["rango_mayor"] = dif, rango
                separaciones[-1] = (dif, rango)
                lineas.append(f"Media de los tres libres menos media de los tres de orden fijo: {dif:+.2f} s/veh ("
                              + ("los libres con menos retraso" if dif < 0 else "los libres con mas retraso"
                                 if dif > 0 else "iguales") + f"); rango mayor entre entrenamientos: {rango:.2f} s/veh")
            lineas.append("")
        prov_nudo = "" if modelos["libre"]["estabilizado"] else " (provisional: entrenamiento citado sin estabilizar)"
        prov_orden = "" if modelos["libre"]["estabilizado"] and modelos["completo"]["estabilizado"] else \
            " (provisional: algun entrenamiento citado sin estabilizar)"
        prov_fijo = "" if modelos["completo"]["estabilizado"] else " (provisional)"
        lectura = lectura_orden(citable(et["orden"]), separaciones)
        notas = [] if prueba else limites(carpeta)
        lineas += [f"Veredicto citable del nudo, demanda {nivel}: **{citable(et['nudo'])}**{prov_nudo}",
                   f"Orden libre frente a orden fijo, demanda {nivel}: **{citable(et['orden'])}**{prov_orden}; "
                   f"frente a la variacion entre entrenamientos: {lectura}",
                   f"Modelo de orden fijo frente al fijo ajustado, demanda {nivel}: **{citable(et['fijo_m'])}**"
                   f"{prov_fijo}", ""] + [f"Limite, demanda {nivel}: {n}" for n in notas] + ([""] if notas else [])
        todo[nivel] = {"modelos": modelos, "tandas": datos, "citable": {k: citable(v) for k, v in et.items()},
                       "lectura_orden": lectura, "limites": notas}
    # robustez (con la demanda publicada)
    rob = {}
    base_l = todo["publicada"]["modelos"]["libre"]["base"] if "publicada" in todo else None
    base_c = todo["publicada"]["modelos"]["completo"]["base"] if "publicada" in todo else None
    for variante, sub in ROBUSTEZ.items():
        if base_l is None:
            rob[variante] = None
            continue
        salidas = os.path.join(raiz, sub, "salidas")
        for b in ("fijo", "actuadoaj"):                 # las copias de los programas de la demanda publicada
            origen, copia = os.path.join(raiz, estudio.ARCHIVO[b]), os.path.join(raiz, sub, estudio.ARCHIVO[b])
            if os.path.exists(copia) and sha256(copia) != sha256(origen):
                raise SystemExit(f"{copia} no es el de la demanda publicada")
            al_dia(origen, [os.path.join(salidas, f"eval_t1_{b}.csv")])
        vals = {b: leer(os.path.join(salidas, f"eval_t1_{b}.csv")) for b in ("actual", "fijo", "actuadoaj")}
        libre = leer(os.path.join(salidas, f"eval_t1_libre_s{base_l}.csv"))
        completo = leer(os.path.join(salidas, f"eval_t1_completo_s{base_c}.csv"))
        if libre is None or completo is None or any(v is None for v in vals.values()):
            rob[variante] = None
            continue
        vals["completo"] = completo
        semillas = PRUEBA["robustez"] if prueba else SEMILLAS_ROBUSTEZ
        assert all(sorted(v) == semillas for v in list(vals.values()) + [libre]), f"{variante}: semillas distintas"
        rob[variante] = {r: estudio.comparar(libre, v) for r, v in vals.items()}
    lineas += ["## Prueba de robustez del reparto (demanda publicada, sin reajustar ni reentrenar; no interviene en el "
               "veredicto)", ""]
    for variante, comp in rob.items():
        if comp is None:
            lineas.append(f"- {variante}: sin evaluar")
            continue
        lineas.append(f"- {variante}: modelo de orden libre {comp['fijo']['media']:.2f} s/veh; " + "; ".join(
            f"{NOMBRE[r]} {c['media_ref']:.2f} ({c['delta']:+.2f} % [{c['ic'][0]:+.2f}, {c['ic'][1]:+.2f}], "
            f"p = {c['p']:.3g})" for r, c in comp.items()))
    todo["robustez"] = rob
    codigo = {p: esperadas.get(p) for p in PROGRAMAS}
    lineas += ["", "## Codigo", "", "Huellas sha256 de los programas; las del resto del codigo y de los datos, en "
               "huellas.sha256. Las politicas se entrenaron con este codigo (sha256_codigo de su meta).", ""]
    lineas += [f"- `{p}` {h}" for p, h in codigo.items()]
    todo["codigo"] = codigo
    destino = os.path.join(raiz, "salidas_prueba") if prueba else os.path.join(AQUI, "salidas_ovalo")
    os.makedirs(destino, exist_ok=True)
    # con --nivel, un archivo propio: el veredicto de una sola demanda no pisa el de las dos (ni la robustez)
    nombre = "veredicto_ovalo" + ("" if len(niveles) == len(NIVELES) else f"_{niveles[0]}")
    with open(os.path.join(destino, nombre + ".md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    with open(os.path.join(destino, nombre + ".json"), "w", encoding="utf-8") as f:
        json.dump(todo, f, indent=1, ensure_ascii=False, default=str)
    print("\n".join(lineas))
    print("Escrito", os.path.join(destino, nombre + ".md"), "y .json")


def comprobar_veredicto(raiz):
    """--comprobar del veredicto: que resultados por semilla estan y cuales faltan."""
    for nivel, sub in NIVELES.items():
        salidas = os.path.join(raiz, sub, "salidas")
        evaluados = sorted(f[len("eval_t"):-4] for f in os.listdir(salidas) if f.startswith("eval_t")) \
            if os.path.isdir(salidas) else []
        print(f"{nivel}: evaluados {evaluados or 'nada'}")
        for t in (1, 2):
            for b in PRINCIPALES:
                if f"{t}_{b}" not in evaluados:
                    falta(f"{nivel}: falta eval_t{t}_{b}.csv (evaluar_ovalo.py referencias)")
            for e in MODELOS:
                if not any(x.startswith(f"{t}_{e}_s") for x in evaluados):
                    falta(f"{nivel}: faltan las evaluaciones de {e} en la tanda {t} (evaluar_ovalo.py modelos)")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("paso", choices=["referencias", "modelos", "robustez", "veredicto"])
    ap.add_argument("--procesos", type=int, default=8)
    ap.add_argument("--solo-citados", action="store_true", help="modelos: no evalua los otros dos entrenamientos")
    ap.add_argument("--prueba", default=None, metavar="CARPETA", help="prueba del programa con semillas de humo")
    ap.add_argument("--comprobar", action="store_true", help="no simula: huellas, procedencia, que correria y que falta")
    ap.add_argument("--nivel", choices=["publicada", "alta", "ambas"], default="ambas",
                    help="referencias, modelos y veredicto: solo esa demanda (la publicada mientras la alta entrena)")
    args = ap.parse_args()
    esperadas = huellas()
    COMPROBAR["activo"] = args.comprobar
    raiz = os.path.abspath(args.prueba) if args.prueba else os.path.join(DEMO, "lima")
    niveles = list(NIVELES) if args.nivel == "ambas" else [args.nivel]
    if args.paso == "referencias":
        evaluar_referencias(raiz, args.procesos, bool(args.prueba), niveles)
    elif args.paso == "modelos":
        evaluar_modelos(raiz, args.procesos, bool(args.prueba), esperadas, args.solo_citados, niveles)
    elif args.paso == "robustez":
        evaluar_robustez(raiz, args.procesos, bool(args.prueba), esperadas)
    elif args.comprobar:
        comprobar_veredicto(raiz)
    else:
        veredicto(raiz, esperadas, bool(args.prueba), niveles)
    if args.comprobar:
        print(f"Huellas correctas. {args.paso}: " + ("listo; nada falta" if not COMPROBAR["falta"] else
                                                     "falta (lo hacen los pasos anteriores):\n  "
                                                     + "\n  ".join(COMPROBAR["falta"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
