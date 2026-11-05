"""
veredicto3.py - Etiquetas, hipotesis y numero unico del bloque plan3 con las reglas del prerregistro, sin cambiarlas
(PLAN3 5.0; DECISIONES B11, B21 y B22; PRERREGISTRO.md §2-§14).

Uso (desde plan3/):
  python veredicto3.py --probar
      Todas las pruebas: las del prototipo (con lo entregado de plan2/, solo lectura) y las de las reglas nuevas con
      datos sinteticos en tmp_ver/ (semillas de humo; no simula nada). Escribe pruebas/ver/prueba_veredicto3.txt y
      pruebas/ver/ejemplo_veredicto3.md (las salidas de un mundo sintetico). Sale con 1 si alguna prueba falla.
  python veredicto3.py --final
      Se niega (ERROR, no escribe nada) si: falta listo/cierre.ok; falta el sello cola/manifiesto_cierre.json o algo
      sellado cambio (CSV, metas y otros: manifiesto esperado, trabajos, caidas, promocion); un CSV de ciego/ no esta
      en la historia versionada de cola/manifiesto_ciego.json o cambio desde la primera manana en que aparecio; las
      semillas no son las del prerregistro; falta un trabajo, un meta o una base sin declararla caida
      (cola/caidas.json); o una celda no tiene modelo principal. Escribe en salidas/: veredicto3_celdas.csv,
      veredicto3_bases.csv, veredicto3_hipotesis.csv, veredicto3_comparaciones.csv, veredicto3_no_insertados.csv y
      veredicto3.md.
  python veredicto3.py --prueba-final LISTA.json
      Prueba final reservada (§13): exige listo/cierre.ok y listo/holdout.ok con el sha256 de LISTA.json; valida todo
      (CSV de una tanda de uso 'final', bloque completo de su tipo de llegadas, mismos vehiculos) y recien entonces crea
      el candado listo/holdout.candado (creacion exclusiva, con el sha256 de cada CSV leido y de la salida); no corre
      una segunda vez. Escribe salidas/veredicto3_prueba_final.csv.

Lee (rutas relativas a plan3/):
  cola/manifiesto_esperado.json   un CSV por (celda, escenario, tanda, brazo), con su tipo, su base y sus semillas
  cola/trabajos.jsonl             el comando de cada CSV: la politica que juega (y su meta) y el brazo que debe decir
  cola/caidas.json                bases caidas declaradas (§14, B22): celda, escenario, tipo, base y los dos intentos
  los CSV del manifiesto          evaluar3.py: una fila por semilla; metrica principal retraso_total_prom (§4)
  politica_*.json, insumos/entregado/politica_*.json   metas: val_elegido, ep_elegido, val_total_serie...
  promocion.json, promocion/*.json                     regla de promocion (§12, p3_promocion.py), con sha256
  insumos/puente/eval_<esc>_*.csv                      fijo e IPPO entregados en 1001-1030 (puente, descriptivo)
  listo/cierre.ok, cola/manifiesto_cierre.json y la historia git de cola/manifiesto_ciego.json: solo en --final
Escribe solo dentro de plan3/ (y nunca la carpeta plan3 misma): escribir() resuelve la ruta real y se niega si cae
fuera; carpeta_limpia() solo borra carpetas plan3/tmp_*. Importar veredicto, consolidar y sintesis_plan solo define
funciones; de ellos se usan solo funciones puras (vd.veredicto, vd.texto_veredicto, vd.convergencia, vd.flotante,
consolidar.comparar, sintesis_plan.indice_geo). Nunca se corren veredicto.py, consolidar.py ni sintesis_plan.py.

Las reglas del prerregistro que admitian mas de una lectura llevan la marca [AMB-n] donde se implementan; la lista,
con la lectura elegida y las que fijo la revision del 05.11, esta en doc/informe_ver.md.
"""
import io
import os
import re
import sys
import csv
import glob
import json
import zlib
import shlex
import stat
import shutil
import hashlib
import argparse
import tempfile
import statistics
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True          # importar los modulos de la raiz no deja __pycache__ fuera de plan3/
PLAN3 = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PLAN3)
for _ruta in (RAIZ, PLAN3):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

import numpy as np                      # noqa: E402
from scipy import stats                 # noqa: E402

import veredicto as vd                  # noqa: E402  solo funciones puras
import consolidar                       # noqa: E402  solo consolidar.comparar
import sintesis_plan                    # noqa: E402  solo sintesis_plan.indice_geo
import generar_trabajos3 as gt          # noqa: E402  celdas, bases y tandas del generador (importarlo no escribe)
import protecciones                     # noqa: E402  tabla de semillas del prerregistro y git (importarlo no escribe)

METRICA = "retraso_total_prom"          # principal (§4)
ALFA = vd.ALFA
MARGEN_NI = 2.0                         # % de la no inferioridad (§8)
MARGEN_EQ = 1.0                         # % de la equivalencia (H4)
BORDE_IC = 0.05                         # puntos: se marca un IC con un extremo a menos de esto del 0 (§7)
MALO_P6A = 1.3                          # P6 aleatoria: episodios con retraso > 1.3 x la mediana del fijo fino (§4)
TRABA_P6 = 1.10                         # P6 regular: semillas del fijo fino con retraso > 1.10 x su mediana (§4, A1)
BASES5, BASES3 = list(gt.BASES5), list(gt.BASES3)
VAL16 = list(gt.VAL16)                  # semillas de validacion (§3, A3)
T = ("T1", "T2")
POSITIVAS = ("MEJORA", "FUNCIONA")
REF_FINO, REF_VETO, REF_CICLO, REF_ENTREGADO = "ref_fino", "ref_actuadoaj", "ref_trivial", "ref_fijo"
ESC_REG = {**gt.CASOS, **gt.NIVELES, **gt.D, **gt.P6E}
CASOS6 = list(gt.CASOS)
ORDEN = CASOS6 + ["P6e", "D"] + list(gt.NIVELES)
# tanda fisica (la del manifiesto) -> tipo de llegadas. "promo" (regla de promocion, la usa p3_promocion) y las de uso
# "final" (prueba final, §13) no entran al veredicto.
LLEGADAS = {"t1r": "regulares", "t2r": "regulares", "h1t1": "regulares", "h1t2": "regulares", "puente": "regulares",
            "t1a": "aleatorias", "t2a": "aleatorias"}
# tanda logica -> tandas fisicas que se juntan (T1x, T2x: las 120 semillas de H1 y H2 = 30 + extension de 90)
FISICAS = {"regulares": {"T1": ("t1r",), "T2": ("t2r",), "T1x": ("t1r", "h1t1"), "T2x": ("t2r", "h1t2"),
                         "puente": ("puente",)},
           "aleatorias": {"T1": ("t1a",), "T2": ("t2a",)}}
# version evaluada de 3 bases que tambien se evalua publicada aparte (extension de H1/H2): mismo checkpoint
PUBLICADA = {("v2reg", 3): "v2reg3med"}
# modelo principal de cada celda: V2 regular, V2 aleatoria, V2 con el perfil y V2 con la mezcla (tambien en mixa_)
FAMILIAS_PRINCIPALES = ("v2reg", "v2poi", "v2per", "v2mix")
CANDIDATOS_PROMOCION = ({t for ts in gt.CANDIDATOS_REG.values() for t in ts}
                        | {t for ts in gt.CANDIDATOS_POI.values() for t in ts})
# Bases del DISENIO (§2, §6, A3, B23): 5 en el modelo principal y en H8a, 3 en lo demas. No sale del manifiesto: una
# base caida sigue contando en n (fuera del lado, §14) [AMB-7].
DISENIO5 = ({("v2reg", c) for c in CASOS6 + ["P6e", "c2715", "D"]} | {("v2poi", c) for c in CASOS6}
            | {("p3obs", "c2715"), ("p3obs", "D")})
TIPO_RED = "p3red"                      # [AMB-19] politica por red (B5); la Etapa 4 aun no esta en el generador
REDES = {"corredor": ["P1", "P2", "c905", "c1358", "c2715"],
         "red": ["P3", "P4", "r905", "r1358", "r1810", "r2715", "r3620"],
         "malla": ["P5", "P6", "m1810", "m2715", "m3620", "m6525"]}
MINIMO_RED = {"corredor": 4, "red": 6, "malla": 5}          # H10: al menos el 80 % de los niveles
# Perfil, mezcla y arranque lento (§8, A7; descriptivas): (celda, escenario, que); las celdas se buscan por escenario
ESTOCASTICAS = [("per1", "per_corredor", "perfil de 10 min"), ("per3", "per_red", "perfil de 10 min"),
                ("mix1", "mix_corredor", "mezcla de Lima"), ("mix3", "mix_red", "mezcla de Lima"),
                ("mixa1", "mixa_corredor", "mezcla con arranque lento"),
                ("mixa3", "mixa_red", "mezcla con arranque lento")]
# a3 (§8, "¿la política usa lo que ve?"): version perturbada t -> la misma version sin perturbar
A3_VERSION = {"v2reg3med": ("v2reg", 3), "p3obsmed": ("p3obs", 3), "v2poi3med": ("v2poi", 3),
              "p3obspoimed": ("p3obspoi", 3)}
A3_CELDAS = {"regulares": (["D", "c2715", "P1", "P2", "P3", "P6"], ("v2reg3med", "p3obsmed")),
             "aleatorias": (CASOS6, ("v2poi3med", "p3obspoimed"))}
A3_PERTURBACION = {"colas0": "con las colas en cero", "msg0": "con los mensajes cortados"}
SECUNDARIAS = ("timeloss_prom", "retraso_insercion_prom", "no_insertados", "cambios_fase")
POR_PERIODO = ("retraso_total_p1", "retraso_total_p2")
# Probabilidad de PENDIENTE por ruido (§6): se informa junto a la etiqueta provisional
RUIDO_PENDIENTE = {("regulares", "P1"): "0-1 %", ("regulares", "P2"): "0-1 %", ("regulares", "P3"): "0-1 %",
                   ("regulares", "P4"): "0-1 %", ("regulares", "P5"): "0-1 %", ("regulares", "P6"): "~10 %",
                   ("aleatorias", "P1"): "0.0 %", ("aleatorias", "P6"): "2.2 %"}
NOMBRE = {
    "v2reg": "IPPO con mensajes corregido", "v2poi": "IPPO con mensajes corregido (entrenado con llegadas aleatorias)",
    "v2per": "IPPO con mensajes corregido (entrenado con el perfil)",
    "v2mix": "IPPO con mensajes corregido (entrenado con la mezcla)",
    "v2loc": "IPPO sin mensajes corregido", "v2poiloc": "IPPO sin mensajes corregido (llegadas aleatorias)",
    "c0": "C0 (IPPO entregado con la selección nueva)", "c0med": "C0 (IPPO entregado con la selección nueva)",
    "c0poimed": "C0 con llegadas aleatorias", "entmed": "IPPO entregado",
    "v2viejamed": "IPPO con mensajes corregido, selección vieja",
    "v2reg3med": "IPPO con mensajes corregido (3 bases)",
    "v2regmed": "IPPO con mensajes corregido, entrenado con llegadas regulares",
    "v2reg3poi": "IPPO con mensajes corregido de 3 bases, entrenado con llegadas regulares",
    "v2poimed": "IPPO con mensajes corregido, entrenado con llegadas aleatorias",
    "v2poi3med": "IPPO con mensajes corregido (3 bases, llegadas aleatorias)",
    "p3obsmed": "observación nueva (3 bases)", "p3obspoimed": "observación nueva (3 bases, llegadas aleatorias)",
    "p3obs": "observación nueva", "p3obspoi": "observación nueva", "p3m7": "limpiezas de PPO juntas",
    "p3m7norm": "normalización del valor", "p3m7forz": "sin decisiones forzadas", "p3m7msg": "mensaje en cada paso",
    "p3ent": "más entropía", "p3reloj2": "reloj de 2 s", "p3reloj2poi": "reloj de 2 s",
    "p3completo": "modelo completo", "p3completopoi": "modelo completo", "p3sd": "solo descuento",
    "p3se": "solo exploración común", "p3e400": "400 episodios", "p3e400poi": "400 episodios",
    "p3piso200reg": "200 episodios con piso de la tasa", "p3piso200poi": "200 episodios con piso de la tasa",
    "p3e400c20reg": "400 episodios eligiendo entre 20", "p3e400c20poi": "400 episodios eligiendo entre 20",
    "p3red": "una política por red",
    "ref_fino": "fijo fino", "ref_fino5": "fijo de verdes de 5 en 5", "ref_franja": "fijo por franja",
    "ref_bloques": "fijo por bloques", "ref_actuadoaj": "actuado ajustado", "ref_actuado": "actuado por defecto",
    "ref_regla": "regla simple", "ref_mp": "Max-Pressure", "ref_mpc": "Max-Pressure con ciclo máximo",
    "ref_trivial": "ciclo mínimo", "ref_fijo": "fijo entregado"}


class ErrorVeredicto(Exception):
    """Un error de datos o de reglas: veredicto3 no sigue (§7: una semilla que falta o que sobra es un error)."""


# ---------------- Escritura (solo dentro de plan3/) ----------------

def dentro_de_plan3(ruta):
    """Ruta real si cae DENTRO de plan3/ (nunca la carpeta plan3 misma); si no, ErrorVeredicto. Todo lo que
    veredicto3 escribe pasa por aqui."""
    real = os.path.realpath(os.path.abspath(ruta))
    base = os.path.realpath(PLAN3)
    try:
        dentro = os.path.commonpath([os.path.normcase(real), os.path.normcase(base)]) == os.path.normcase(base)
    except ValueError:                                  # otra unidad de disco
        dentro = False
    if not dentro or os.path.normcase(real) == os.path.normcase(base):
        raise ErrorVeredicto(f"veredicto3 no escribe fuera de plan3/ ni la carpeta plan3 misma: {ruta}")
    return real


def escribir(ruta, texto):
    real = dentro_de_plan3(ruta)
    os.makedirs(os.path.dirname(real), exist_ok=True)
    tmp = f"{real}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(texto)
    os.replace(tmp, real)
    return real


def texto_csv(filas, campos):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=campos, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for f in filas:
        w.writerow({k: ("" if f.get(k) is None else f.get(k)) for k in campos})
    return buf.getvalue()


def carpeta_limpia(ruta):
    """Borra y vuelve a crear una carpeta temporal: solo plan3/tmp_* (o algo dentro de ella)."""
    real = dentro_de_plan3(ruta)
    rel = os.path.relpath(real, os.path.realpath(PLAN3)).replace(os.sep, "/")
    if not rel.split("/")[0].startswith("tmp_"):
        raise ErrorVeredicto(f"carpeta_limpia solo borra carpetas plan3/tmp_*: {ruta}")

    def solo_lectura(funcion, camino, _exc):  # en Windows git deja sus objetos de solo lectura
        os.chmod(camino, stat.S_IWRITE)
        funcion(camino)
    if os.path.exists(real):
        shutil.rmtree(real, onexc=solo_lectura)
    os.makedirs(real)
    return real


# ---------------- Lectura ----------------

def leer_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rango(texto):
    """'8001-8030,8040' -> [8001, ..., 8030, 8040]."""
    salida = []
    for parte in str(texto).split(","):
        parte = parte.strip()
        if not parte:
            continue
        if "-" in parte[1:]:
            a, b = parte.split("-", 1)
            salida += list(range(int(a), int(b) + 1))
        else:
            salida.append(int(parte))
    return salida


def politica_de(trabajo):
    """Ruta (relativa a plan3/) de la politica que juega un trabajo de evaluacion, o None (referencias)."""
    return opcion_de(trabajo, "--politica")


def partes_de(trabajo):
    if not trabajo:
        return []
    try:
        return shlex.split(trabajo.get("cmd", ""))
    except ValueError:
        return []


def opcion_de(trabajo, opcion):
    partes = partes_de(trabajo)
    if opcion in partes and partes.index(opcion) + 1 < len(partes):
        return partes[partes.index(opcion) + 1]
    return None


def brazo_de_trabajo(trabajo, meta):
    """El brazo que escribe evaluar3.py para un trabajo (o None si su nombre todavia no esta fijado: --programa,
    --franja, --actuado-aj, --regla). Con --politica, como evaluar.brazo_profundo: ippo_<variante>[_<etiqueta>]_s<base>,
    mas _L0p<perdida> que agrega brazo_profundo y _p<perdida> y _colas0 que agrega evaluar3 (a3)."""
    partes = partes_de(trabajo)
    if "--politica" in partes:
        if meta is None:
            return None
        modelo = "ippo_" + meta["variante"] + (f"_{meta['etiqueta']}" if meta.get("etiqueta") else "")
        base = meta.get("base", "")
        brazo = f"{modelo}_s{base}" if base != "" else modelo
        perdida = float(opcion_de(trabajo, "--perdida") or 0)
        if perdida:
            brazo += f"_L0p{int(round(perdida * 100))}_p{int(round(perdida * 100))}"
        if "--colas-cero" in partes:
            brazo += "_colas0"
        return brazo
    return opcion_de(trabajo, "--brazo")


def nombre(tipo):
    if tipo in NOMBRE:
        return NOMBRE[tipo]
    m = re.fullmatch(r"a3(colas0|msg0)_(.+)", tipo or "")
    if m:
        return f"{nombre(m.group(2))} {A3_PERTURBACION[m.group(1)]}"
    return tipo


def nombre_brazo(brazo):
    k = brazo[0]
    if k in ("ref", "pub"):
        return nombre(brazo[1])
    if k == "ins":
        return {"fijo": "fijo entregado", "ippo_entregado": "IPPO entregado"}.get(brazo[1], brazo[1])
    if k == "base":
        return f"{nombre(brazo[1])}, base {brazo[2]}"
    if k == "ver":
        return nombre(brazo[1]) + ("" if brazo[2] is None else f" (entre {brazo[2]} bases)")
    return f"{nombre(brazo[1])}, mejor base"


def clave_brazo(brazo):
    k = brazo[0]
    if k in ("ref", "pub", "ins"):
        return brazo[1]
    if k == "base":
        return f"{brazo[1]}_s{brazo[2]}"
    return f"{brazo[1]}_{'version' if k == 'ver' else 'mejor'}" + ("" if brazo[2] is None else f"{brazo[2]}")


# ---------------- Reglas: entrenamiento ----------------

def criterio(meta):
    return meta.get("criterio_val") or (meta.get("opciones") or {}).get("criterio_val") or "timeloss"


def validar_meta(meta, ruta):
    """§6: cada base de plan3 y de C0 se elige por retraso total medio en las 16 semillas de validacion. ERROR si no.
    Excepciones: lo entregado (insumos/entregado/, regla del 25.09), p3_elegir regla (V2 vieja, 200 con piso, 400 entre
    20: eligen con su propia serie, serie_eleccion/regla_eleccion) y la politica por red (8 semillas x 3 niveles)."""
    etiqueta = meta.get("etiqueta") or (meta.get("opciones") or {}).get("etiqueta") or ""
    if (ruta or "").replace("\\", "/").startswith("insumos/entregado/") or meta.get("serie_eleccion") \
            or meta.get("regla_eleccion") or etiqueta.startswith(TIPO_RED):
        return
    if criterio(meta) != "total" or list(meta.get("val_seeds") or []) != VAL16:
        raise ErrorVeredicto(f"{ruta}: la base no se eligio con criterio total y las 16 semillas de validacion (§6): "
                             f"criterio {criterio(meta)}, {len(meta.get('val_seeds') or [])} semillas")


def serie_criterio(meta):
    """(nombre, [(ep, valor)]) de la serie con que se eligio el checkpoint, con el ULTIMO valor de cada fila: la media
    de las semillas de validacion (§6). Nunca veredicto.info_base, que toma x[3] (con 16 semillas, una semilla).
    Todo lo entrenado en plan3 y C0 se elige por val_total_serie (criterio total). [AMB-1] Las metas que se eligieron
    con otra serie usan la suya: p3_elegir regla (V2 vieja, 200 con piso, 400 entre 20) -> serie_eleccion; lo entregado
    y el exploratorio (criterio timeLoss) -> val_serie."""
    if meta.get("serie_eleccion"):
        clave = "serie_eleccion"
    elif criterio(meta) == "total":
        clave = "val_total_serie"
    else:
        clave = "val_serie"
    return clave, sorted((int(x[0]), float(x[-1])) for x in meta.get(clave) or [])


def entrenamiento(meta):
    """Una base: validacion elegida, episodio, convergencia (regla del Cap. III, vd.convergencia, sobre la serie del
    criterio) y las columnas descriptivas de recomendaciones.tex l. 84-92."""
    clave, serie = serie_criterio(meta)
    if meta.get("serie_eleccion") and serie:
        episodios = float(serie[-1][0])     # [AMB-25] la regla eligio dentro de esos episodios (200 con piso: 200)
    else:
        episodios = float(meta.get("episodios") or (serie[-1][0] if serie else 0))
    conv, meseta, estab = vd.convergencia(serie, episodios) if serie else (False, None, None)
    val = vd.flotante(meta.get("val_elegido"))
    vals = [v for _, v in serie]
    med = float(np.median(vals)) if vals else None
    d_s = None if val is None or med is None else val - med
    # [AMB-2] distancia a la mediana de TODA la serie, en s y en % de esa mediana
    d_pct = None if d_s is None or not med else d_s / med * 100
    minimo = min(vals) if vals else None
    # [AMB-3] lectura literal: el valor minimo aparece en dos validaciones seguidas (con la precision del meta);
    # al lado, la alternativa: las dos mejores validaciones son seguidas
    repetido = any(vals[i] == minimo and vals[i + 1] == minimo for i in range(len(vals) - 1))
    orden = sorted(range(len(vals)), key=lambda i: (vals[i], i))
    seguidos = len(vals) >= 2 and abs(orden[0] - orden[1]) == 1
    return {"serie": clave, "n_validaciones": len(serie), "val": val, "ep": meta.get("ep_elegido"),
            "episodios": episodios, "convergio": conv, "meseta": meseta, "estabilidad": estab,
            "dist_mediana_s": d_s, "dist_mediana_pct": d_pct, "min_repetido": repetido,
            "dos_mejores_seguidos": seguidos, "criterio": criterio(meta), "val_seeds": meta.get("val_seeds")}


def base_mediana_n(vals):
    """{base: val_elegido} -> base de la version evaluada (§6, B21): la 3.a de 5, la 2.a de 3; con un numero par (una
    base caida), la peor de las dos centrales; empate de val, la base menor primero (como vd.base_mediana y
    p3_elegir.mediana)."""
    if not vals:
        return None
    orden = sorted(vals.items(), key=lambda bv: (bv[1], bv[0]))
    return orden[len(orden) // 2][0]


def mejor_base(vals):
    """La de menor val_elegido (empate: la base menor). Secundaria prerregistrada (§6, A3): no decide."""
    return min(vals.items(), key=lambda bv: (bv[1], bv[0]))[0] if vals else None


# ---------------- Reglas: comparacion y etiqueta ----------------

def comparar(a, b, esperadas=None):
    """a, b: {semilla: valor}. Cambio % de a frente a b, IC95 y p con consolidar.comparar (pareado por semilla; IC
    bootstrap pareado, 10 000 remuestreos con default_rng(0), redondeado a 2 decimales; Wilcoxon pareado de dos colas;
    con > 50 semillas, la aproximacion normal de scipy). ERROR si falta una semilla esperada o si sobra una (§7).
    [AMB-10] El p de dos colas es el de consolidar (3 cifras significativas, como lo entregado) y con el mismo se
    ajusta Holm; los p de una cola (no inferioridad, H6) van sin redondear."""
    esperadas = set(b) if esperadas is None else set(esperadas)
    for quien, d in (("brazo", a), ("referencia", b)):
        faltan, sobran = sorted(esperadas - set(d)), sorted(set(d) - esperadas)
        if faltan or sobran:
            raise ErrorVeredicto(f"semillas del {quien}: faltan {faltan[:5]} y sobran {sobran[:5]} (§7)")
    c = consolidar.comparar(a, b, False)
    if "delta_ic95" not in c or "p_wilcoxon" not in c:
        return None
    lo, hi = (float(x) for x in c["delta_ic95"].strip("[]").split(","))
    return {"n": c["n_par"], "cambio": c["delta_pct"], "ic": (lo, hi), "p": float(c["p_wilcoxon"]),
            "borde": min(abs(lo), abs(hi)) < BORDE_IC}


def etiqueta(ref, act=None, convergio=True, motivo=None):
    """La regla de veredicto.py sin cambios (§7): ref = comparar(modelo, fijo fino); act = comparar(modelo, actuado
    ajustado) para el veto de FUNCIONA. PENDIENTE con motivo si falta algo; con la provisional si no convergio."""
    if motivo:
        return vd.texto_veredicto(None, motivo)
    prov = vd.veredicto(ref["cambio"], ref["ic"], ref["p"], act["ic"] if act else None, act["p"] if act else None)
    return vd.texto_veredicto(prov, None, convergio)


def palabra(texto):
    """FUNCIONA, MEJORA, EMPATA, FALLA, PENDIENTE o CONTRADICTORIO."""
    return (texto or "PENDIENTE").split(" ")[0].rstrip("*")


def provisional(texto):
    m = re.search(r"provisional: (.+)\)$", texto or "")
    return m.group(1) if m else None


def acuerdo(e1, e2):
    """Etiqueta citable (§7, A5): solo se afirma lo que se repite en T1 y T2. [AMB-4] La tabla se lee simetrica (T1 y
    T2 son replicas; solo la fila FUNCIONA/MEJORA dice 'o al reves'). [AMB-5] Si las dos son PENDIENTE por
    convergencia, la provisional citable es el acuerdo de las provisionales."""
    p1, p2 = palabra(e1), palabra(e2)
    if "PENDIENTE" in (p1, p2):
        q1, q2 = provisional(e1), provisional(e2)
        if q1 and q2:
            return f"PENDIENTE (no convergió; provisional: {acuerdo(q1, q2)})"
        # una PENDIENTE por algo que falta manda; si no la hay, la que tiene provisional (PENDIENTE en cualquiera)
        sin_prov = next((e for e in (e1, e2) if palabra(e) == "PENDIENTE" and not provisional(e)), None)
        return sin_prov or next(e for e in (e1, e2) if palabra(e) == "PENDIENTE")
    if p1 == p2:
        return p1
    par = {p1, p2}
    if par == {"MEJORA", "FUNCIONA"}:
        return "MEJORA"
    if par & set(POSITIVAS) and "EMPATA" in par:
        return "EMPATA (mejora no confirmada)"
    if par == {"FALLA", "EMPATA"}:
        return "EMPATA (falla no confirmada)"
    if par & set(POSITIVAS) and "FALLA" in par:
        return "CONTRADICTORIO (no se concluye)"
    return "CONTRADICTORIO (no se concluye)"


def sentido(cambios, n, lado="bajo", umbral=0.0):
    """Sentido entre entrenamientos (§7, criterio por signo de A5): cuantas bases tienen el cambio estimado del lado de
    la afirmacion. cambios: {base: cambio % o None}; n: bases del diseno (5 o 3). Exige 4 de 5 o 3 de 3.
    lado 'bajo': cambio < umbral (mejora: 0; no inferioridad: +2 %); 'sobre': cambio > umbral.
    [AMB-7] Una base sin dato (caida: 'cuenta como fallida y fuera del sentido', §14) cuenta como fuera del lado y el
    minimo no baja."""
    k = sum(1 for b, c in cambios.items() if c is not None and (c < umbral if lado == "bajo" else c > umbral))
    requerido = 4 if n == 5 else n
    return {"k": k, "n": n, "requerido": requerido, "cumple": k >= requerido, "cambios": dict(cambios)}


def holm(pvals):
    """{clave: p} -> {clave: p ajustado} (Holm: paso descendente, monotono, tope 1), dentro de una familia y una tanda
    (§9). Una prueba que no se pudo correr (p None) entra con p = 1: la familia conserva su tamano y esa prueba cuenta
    como no pasada; su p ajustado sale None."""
    orden = sorted(pvals.items(), key=lambda kv: 1.0 if kv[1] is None else kv[1])
    m, ajustado, maximo = len(orden), {}, 0.0
    for i, (k, p) in enumerate(orden):
        maximo = max(maximo, min(1.0, (m - i) * (1.0 if p is None else p)))
        ajustado[k] = None if p is None else maximo
    return ajustado


def p_no_inferioridad(a, b, margen=MARGEN_NI):
    """p de una cola de 'a es peor que b en mas de margen %': Wilcoxon de rangos con signo sobre a - (1 + m) b,
    alternativa 'menor' (§8). 1 si todas las diferencias son 0."""
    comunes = sorted(set(a) & set(b))
    d = np.array([a[s] - (1 + margen / 100) * b[s] for s in comunes])
    if not np.any(d != 0):
        return 1.0
    return float(stats.wilcoxon(d, alternative="less").pvalue)


def lectura_ni(comp, p_ajustado, margen=MARGEN_NI):
    """Las tres lecturas de la no inferioridad (§8): 'no es peor' (limite superior del IC95 <= +2 % y p de una cola
    ajustado < 0.05), 'es peor' (IC95 entero sobre +2 %) o 'no concluyente' (el resto)."""
    if comp is None or p_ajustado is None:
        return "no se pudo correr"
    lo, hi = comp["ic"]
    if hi <= margen and p_ajustado < ALFA:
        return "no es peor"
    if lo > margen:
        return "es peor"
    return "no concluyente"


def lectura_ni_conjunta(lecturas, sentidos=None):
    """No inferioridad en las dos tandas (§8; AMB-9 fijada por la revision del 05.11): (pasa, lectura).
    Pasa solo si T1 y T2 dan 'no es peor' y, si lleva sentido, se cumple en las dos. Si las dos dan 'no es peor' y falla
    el sentido: 'la version evaluada no es peor; el metodo no se repite en k de n entrenamientos'. Si no pasa: 'es peor'
    (las dos), 'perdida no confirmada' (es peor + no concluyente), 'contradictorio' (no es peor + es peor) o 'no
    concluyente' (el resto); siempre con la lectura de cada tanda. lecturas: {tanda: lectura}; sentidos: {tanda:
    sentido()} o None."""
    detalle = "; ".join(f"{t}: {x}" for t, x in lecturas.items())
    vals = list(lecturas.values())
    if "no se pudo correr" in vals:
        return False, f"no se pudo correr ({detalle})"
    if all(x == "no es peor" for x in vals):
        malos = {t: s for t, s in (sentidos or {}).items() if not s["cumple"]}
        if not malos:
            return True, "no es peor"
        k = "; ".join(f"{s['k']} de {s['n']} en {t}" for t, s in malos.items())
        return False, f"la versión evaluada no es peor; el método no se repite en {k} entrenamientos"
    par = set(vals)
    if par == {"es peor"}:
        texto = "es peor"
    elif par == {"es peor", "no concluyente"}:
        texto = "pérdida no confirmada"
    elif "es peor" in par and "no es peor" in par:
        texto = "contradictorio"
    else:
        texto = "no concluyente"
    return False, f"{texto} ({detalle})"


def equivalente(comp, margen=MARGEN_EQ):
    """Equivalencia +-1 % (§8, H4): el IC95 del cambio queda dentro de [-1, +1] %."""
    return comp is not None and comp["ic"][0] >= -margen and comp["ic"][1] <= margen


def interseccion_union(casos):
    """H1 global (§8, A5): pasa si CADA caso da 'no es peor' al 5 % (sin Holm) en las dos tandas.
    casos: [[{comp, p_ni} de T1, {comp, p_ni} de T2], ...]."""
    return bool(casos) and all(t and t.get("comp") and t["comp"]["ic"][1] <= MARGEN_NI and t["p_ni"] < ALFA
                               for caso in casos for t in caso)


def bootstrap_cambios(a, b, semilla_rng, n_boot=consolidar.N_BOOT):
    """Cambios % remuestreados por semilla (pareados: los mismos indices para los dos brazos)."""
    comunes = sorted(set(a) & set(b))
    x = np.array([a[s] for s in comunes])
    y = np.array([b[s] for s in comunes])
    rng = np.random.default_rng(semilla_rng)
    idx = rng.integers(0, len(comunes), size=(n_boot, len(comunes)))
    return (x[idx].mean(axis=1) - y[idx].mean(axis=1)) / y[idx].mean(axis=1) * 100


def diferencia_no_pareada(a1, b1, a2, b2, esperadas1=None, esperadas2=None):
    """H6 (§8): D = cambio(a1 frente a b1) - cambio(a2 frente a b2), con semillas distintas en cada lado (1: llegadas
    aleatorias, 2: regulares). Bootstrap independiente en cada lado, pareado por semilla dentro de cada uno, 10 000
    remuestreos. [AMB-11] Generadores default_rng(1) y default_rng(2), los del prototipo (el prerregistro no los fija).
    Devuelve D (de los cambios de consolidar), IC95 a 2 decimales y p de una cola (fraccion de remuestreos con
    D >= 0)."""
    c1, c2 = comparar(a1, b1, esperadas1), comparar(a2, b2, esperadas2)
    dd = bootstrap_cambios(a1, b1, 1) - bootstrap_cambios(a2, b2, 2)
    return {"D": round(c1["cambio"] - c2["cambio"], 2), "cambio_1": c1["cambio"], "cambio_2": c2["cambio"],
            "ic": (round(float(np.percentile(dd, 2.5)), 2), round(float(np.percentile(dd, 97.5)), 2)),
            "p": float(np.mean(dd >= 0))}


def generados(fila):
    """Vehiculos generados en una semilla: la columna de evaluar3 o, en lo entregado, vehiculos + no insertados."""
    if fila.get("generados") not in (None, ""):
        return int(float(fila["generados"]))
    return int(float(fila.get("vehiculos") or 0)) + int(float(fila.get("no_insertados") or 0))


def generados_iguales(filas_por_brazo):
    """Numeros aleatorios comunes (§7): semillas en que los brazos NO generan los mismos vehiculos,
    [(semilla, {brazo: generados})]. Vacio = bien."""
    malas = []
    comunes = set.intersection(*[set(d) for d in filas_por_brazo.values()])
    for s in sorted(comunes):
        gen = {br: generados(d[s]) for br, d in filas_por_brazo.items()}
        if len(set(gen.values())) > 1:
            malas.append((s, gen))
    return malas


def igual_ciclo_minimo(filas_a, filas_ciclo):
    """La marca de lo entregado (vd.igual_a): la media de retraso total y la de espera coinciden con las del ciclo
    minimo hasta 0.0005 s/veh. [AMB-24] Con las medias redondeadas a 4 decimales, como las del resumen de consolidar."""
    for m in (METRICA, "espera_prom"):
        a = statistics.mean(float(r[m]) for r in filas_a.values())
        t = statistics.mean(float(r[m]) for r in filas_ciclo.values())
        if abs(round(a, 4) - round(t, 4)) > vd.IGUAL:
            return False
    return True


def demanda_esperada(rutas):
    """veh esperados de unos .rou.xml: vehsPerHour, number, period fijo y period="exp(l)" (vd.demanda hace
    float(period) y falla con llegadas aleatorias)."""
    total = 0.0
    for ruta in rutas:
        for flow in ET.parse(ruta).getroot().iter("flow"):
            ini, fin = float(flow.get("begin", 0)), float(flow.get("end", 3600))
            dur, per = fin - ini, flow.get("period") or ""
            if flow.get("vehsPerHour") or flow.get("perHour"):
                total += float(flow.get("vehsPerHour") or flow.get("perHour")) * dur / 3600
            elif flow.get("number"):
                total += float(flow.get("number"))
            elif per.startswith("exp("):
                total += float(per[4:-1]) * dur
            elif per:
                total += dur / float(per)
            elif flow.get("probability"):
                total += float(flow.get("probability")) * dur
    return total


def numero_unico(series):
    """Numero unico (§7): sintesis_plan.indice_geo sobre [(x, y)] (arreglos pareados por semilla, un par por caso),
    con default_rng(0) como sintesis_plan.numero_unico. (cambio %, lo, hi), a 2 decimales."""
    d, lo, hi = sintesis_plan.indice_geo(series, np.random.default_rng(0))
    return round(float(d), 2), round(float(lo), 2), round(float(hi), 2)


def familia_principal(celda):
    return next((f for f in FAMILIAS_PRINCIPALES if f in celda["tipos"]), None)


# ---------------- Datos: manifiesto, CSV y metas ----------------

class Datos:
    """Lo que veredicto3 lee de una carpeta plan3 (la real o una sintetica de las pruebas). Los brazos son tuplas:
    ("ref", tipo) referencia; ("pub", tipo) version ya publicada (C0, IPPO entregado, V2 vieja, transferencias, a3);
    ("base", familia, b) una base; ("ver", familia, n) version evaluada entre n bases (None: las del diseno);
    ("mejor", familia, n) la mejor base por validacion; ("ins", nombre) CSV entregado del puente.
    estricto (--final): falta de trabajos, metas o bases sin declarar = ERROR. sello: el de cola/manifiesto_cierre.json;
    con el, todo meta y todo archivo de control que se lee debe estar sellado con el mismo sha256."""

    def __init__(self, raiz, estricto=False, sello=None):
        self.raiz, self.estricto, self.sello = raiz, estricto, sello
        self.avisos, self.celdas, self.todas = [], {}, {}
        self._csv, self._meta, self._comp, self._pub, self._insumos = {}, {}, {}, {}, None
        if not os.path.exists(os.path.join(raiz, "cola", "manifiesto_esperado.json")):
            raise ErrorVeredicto("falta cola/manifiesto_esperado.json (python generar_trabajos3.py)")
        self.manifiesto = json.loads(self.leer_otro("cola/manifiesto_esperado.json"))
        self.trabajos = {}
        if os.path.exists(os.path.join(raiz, "cola", "trabajos.jsonl")):
            for linea in self.leer_otro("cola/trabajos.jsonl").splitlines():
                if linea.strip():
                    t = json.loads(linea)
                    self.trabajos[t["id"]] = t
        elif estricto:
            raise ErrorVeredicto("falta cola/trabajos.jsonl: sin el comando de cada CSV no se sabe qué política juega")
        else:
            self.avisos.append("falta cola/trabajos.jsonl: no se conocen las políticas ni sus metas")
        self.caidas = self.leer_caidas()
        vistos, fuera = set(), {}
        for e in self.manifiesto:
            if e["csv"] in vistos:
                raise ErrorVeredicto(f"{e['csv']} aparece dos veces en el manifiesto")
            vistos.add(e["csv"])
            base = int(e["base"]) if str(e.get("base", "")).strip() not in ("", "None") else None
            trabajo = self.trabajos.get(e.get("trabajo"))
            if trabajo is None and estricto:
                raise ErrorVeredicto(f"{e['csv']}: su trabajo {e.get('trabajo')} no está en cola/trabajos.jsonl")
            ent = dict(e, base=base, politica=politica_de(trabajo))
            self.todas[(e["celda"], e["escenario"], e["tipo"], base, e["tanda"])] = ent   # tambien la prueba final
            lleg = LLEGADAS.get(e["tanda"])
            if lleg is None:
                fuera[e["tanda"]] = fuera.get(e["tanda"], 0) + 1
                continue
            if (e["celda"], e["escenario"], e["tipo"], base) in self.caidas:
                continue                        # base caida declarada: sus CSV no existen (§14)
            ck = (e["celda"], e["escenario"])
            c = self.celdas.setdefault(ck, {"llegadas": lleg, "tipos": {}})
            if c["llegadas"] != lleg:
                raise ErrorVeredicto(f"la celda {ck} mezcla llegadas regulares y aleatorias")
            casilla = c["tipos"].setdefault(e["tipo"], {}).setdefault(base, {})
            if e["tanda"] in casilla:
                raise ErrorVeredicto(f"dos CSV del mismo brazo y tanda: {casilla[e['tanda']]['csv']} y {e['csv']}")
            casilla[e["tanda"]] = ent
        for tanda, n in sorted(fuera.items()):  # una linea por tanda, no una por CSV
            uso = gt.TANDAS.get(tanda, ("",))[0]
            por_que = {"promocion": "regla de promoción: se leen en promocion.json",
                       "final": "prueba final reservada (§13): --prueba-final"}.get(uso,
                                                                                    "tanda sin uso en el veredicto")
            self.avisos.append(f"{n} CSV de la tanda {tanda} no entran al veredicto ({por_que})")

    # --- sello del cierre ---

    def sha_insumo(self, rel):
        """sha256 de un insumo segun insumos/manifiesto.json (p3_insumos.py: {grupo: {ruta: [bytes, sha256]}})."""
        if self._insumos is None:
            p = os.path.join(self.raiz, "insumos", "manifiesto.json")
            self._insumos = leer_json(p) if os.path.exists(p) else {}
        for grupo, archivos in self._insumos.items():
            pre = grupo.replace("\\", "/").rstrip("/") + "/"
            if rel.startswith(pre) and rel[len(pre):] in archivos:
                return archivos[rel[len(pre):]][1]
        return None

    def verificar(self, rel, grupo):
        """Con sello (--final): rel debe estar sellado en su grupo ('csv', 'metas' u 'otros'; los insumos, en
        insumos/manifiesto.json) con el mismo sha256 que tiene ahora. Si no, ERROR."""
        if self.sello is None:
            return
        rel = rel.replace("\\", "/")
        h = self.sello.get(grupo, {}).get(rel)
        if h is None and rel.startswith("insumos/"):
            h = self.sha_insumo(rel)
        if h is None:
            raise ErrorVeredicto(f"{rel} no está sellado en cola/manifiesto_cierre.json ({grupo})")
        if sha256(os.path.join(self.raiz, rel)) != h:
            raise ErrorVeredicto(f"{rel} cambió después del cierre (sha256 distinto del sello)")

    def leer_otro(self, rel):
        self.verificar(rel, "otros")
        with open(os.path.join(self.raiz, rel), encoding="utf-8") as f:
            return f.read()

    def leer_caidas(self):
        """cola/caidas.json (§14, B22): lista de {celda, escenario, tipo, base, intentos: [{id, error, fecha}, ...]},
        con los dos intentos fallidos. Una base declarada cuenta como caida: fuera de la mediana y fuera del lado."""
        if not os.path.exists(os.path.join(self.raiz, "cola", "caidas.json")):
            return {}
        datos = json.loads(self.leer_otro("cola/caidas.json"))
        lista = datos.get("caidas", []) if isinstance(datos, dict) else datos
        caidas = {}
        for c in lista:
            faltan = [k for k in ("celda", "escenario", "tipo", "base", "intentos") if k not in c]
            intentos = c.get("intentos") or []
            incompletos = any(not all(i.get(k) for k in ("id", "error", "fecha")) for i in intentos)
            if faltan or len(intentos) < 2 or incompletos:
                raise ErrorVeredicto(f"cola/caidas.json: cada base caída lleva celda, escenario, tipo, base y los dos "
                                     f"intentos fallidos con id, error y fecha (§14): {c}")
            caidas[(c["celda"], c["escenario"], c["tipo"], int(c["base"]))] = c
        return caidas

    # --- celdas, bases y metas ---

    def orden(self):
        def clave(ck):
            c = self.celdas[ck]
            return (c["llegadas"] != "regulares", ORDEN.index(ck[0]) if ck[0] in ORDEN else len(ORDEN), ck)
        return sorted(self.celdas, key=clave)

    def bases_disenio(self, ck, fam):
        """Bases del DISENIO de una familia (§2, §6, B23; [AMB-7] fijada el 05.11): 5 para V2 regular en P1-P6, P6e,
        c2715 y D, para V2 aleatoria en los 6 casos y para la observacion nueva en c2715 y D; 3 en lo demas. No sale
        del manifiesto, asi que una base caida sigue contando en n."""
        presente = fam in self.celdas[ck]["tipos"] or any(k[:3] == (ck[0], ck[1], fam) for k in self.caidas)
        if not presente:
            return []
        return BASES5 if (fam, ck[0]) in DISENIO5 else BASES3

    def es_caida(self, ck, fam, b):
        return (ck[0], ck[1], fam, b) in self.caidas

    def meta(self, rel):
        if not rel:
            return None
        rel_json = rel[:-3] + ".json" if rel.endswith(".pt") else rel
        ruta = os.path.join(self.raiz, rel_json)
        if ruta not in self._meta:
            if os.path.exists(ruta):
                self.verificar(rel_json, "metas")
                self._meta[ruta] = leer_json(ruta)
            else:
                self._meta[ruta] = None
        return self._meta[ruta]

    def meta_base(self, ck, fam, b):
        """(meta, ruta de la politica, estado) de la base b de una familia; estado 'caida' (declarada en
        cola/caidas.json), 'publicada' o 'sin_meta'. ERROR si la base tiene CSV y no tiene meta (una base caida no se
        evalua, §14), si en --final no tiene CSV y no esta declarada caida, o si no se eligio con criterio total y 16
        semillas (validar_meta)."""
        por = self.celdas[ck]["tipos"].get(fam, {})
        pol = next((e["politica"] for e in por.get(b, {}).values() if e.get("politica")), None)
        tiene_csv = bool(por.get(b))
        if pol is None:                         # sin CSV de esa base: la ruta de otra base de la familia
            otra = next((e["politica"] for bb, ents in por.items() if bb is not None for e in ents.values()
                         if e.get("politica")), None)
            pol = re.sub(r"_s\d+\.pt$", f"_s{b}.pt", otra) if otra else None
        if self.es_caida(ck, fam, b):
            return None, pol, "caida"
        m = self.meta(pol)
        if m is None and tiene_csv:
            raise ErrorVeredicto(f"{ck[1]}: la base {b} de {nombre(fam)} tiene CSV y no tiene meta ({pol}); una base "
                                 f"caída no se evalúa y se declara en cola/caidas.json (§14)")
        if not tiene_csv and self.estricto:
            raise ErrorVeredicto(f"{ck[1]}: la base {b} de {nombre(fam)} no tiene CSV y no está declarada caída en "
                                 f"cola/caidas.json (§14)")
        if m is None:
            return None, pol, "sin_meta"
        validar_meta(m, pol[:-3] + ".json" if pol.endswith(".pt") else pol)
        return m, pol, "publicada"

    def base_version(self, ck, fam, n=None, cual="ver"):
        """(base, motivo): la version evaluada (mediana por val_elegido) o la mejor base, entre las bases del diseno
        (n None), entre 42, 2042 y 4042 (n=3) o entre las 5 (n=5). Las caidas declaradas quedan fuera (§6, §14: con un
        numero par, la peor de las dos centrales)."""
        disenio = self.bases_disenio(ck, fam)
        if not disenio:
            return None, f"no hay evaluaciones de {nombre(fam)}"
        if n == 5 and disenio != BASES5:
            return None, f"{nombre(fam)} tiene 3 bases"
        bases = disenio if n is None else (BASES3 if n == 3 else BASES5)
        vals = {}
        for b in bases:
            m, pol, estado = self.meta_base(ck, fam, b)
            if estado == "caida":
                continue
            if estado == "sin_meta":
                return None, f"falta el meta de la base {b} de {nombre(fam)}"
            v = vd.flotante(m.get("val_elegido"))
            if v is None:
                raise ErrorVeredicto(f"{pol}: la base no tiene val_elegido")
            vals[b] = v
        if not vals:
            return None, f"cayeron todas las bases de {nombre(fam)}"
        return (base_mediana_n(vals) if cual == "ver" else mejor_base(vals)), None

    def pub_info(self, ck, tipo):
        """(base elegida, meta de esa base) de una version publicada por p3_elegir mediana. Comprueba que la base es la
        mediana por val_elegido de sus candidatas, leidas (y validadas) de sus propios metas (ERROR si no)."""
        if (ck, tipo) in self._pub:
            return self._pub[(ck, tipo)]
        ents = [e for por in self.celdas[ck]["tipos"].get(tipo, {}).values() for e in por.values()]
        pol = next((e["politica"] for e in ents if e.get("politica")), None)
        meta = self.meta(pol)
        if meta is None:
            if pol and ents:
                raise ErrorVeredicto(f"{tipo} en {ck[1]}: tiene CSV y no tiene meta ({pol})")
            res = (None, None)
        elif meta.get("candidatas"):
            vals, metas = {}, {}
            for c in meta["candidatas"]:
                m = self.meta(c["politica"])
                if m is None:
                    raise ErrorVeredicto(f"{pol}: falta el meta de su candidata {c['politica']}")
                validar_meta(m, c["politica"][:-3] + ".json" if c["politica"].endswith(".pt") else c["politica"])
                if vd.flotante(m.get("val_elegido")) is not None:
                    metas[int(c["base"])] = m
                    vals[int(c["base"])] = vd.flotante(m.get("val_elegido"))
            b = base_mediana_n(vals)
            if b is None or b != meta.get("base_elegida"):
                raise ErrorVeredicto(f"{pol}: base_elegida {meta.get('base_elegida')}, pero la mediana por "
                                     f"val_elegido de sus candidatas es {b} (B21)")
            res = (b, metas[b])
        else:
            res = (meta.get("base"), meta)
        self._pub[(ck, tipo)] = res
        return res

    # --- CSV ---

    def entrada(self, ck, brazo, tf):
        """(entrada del manifiesto, motivo) del CSV de un brazo en una tanda fisica."""
        tipos = self.celdas[ck]["tipos"]
        k = brazo[0]
        if k in ("ref", "pub"):
            e = tipos.get(brazo[1], {}).get(None, {}).get(tf)
            return (e, None) if e else (None, f"falta {nombre(brazo[1])} en {tf}")
        if k == "base":
            if self.es_caida(ck, brazo[1], brazo[2]):
                return None, f"la base {brazo[2]} de {nombre(brazo[1])} cayó (cola/caidas.json)"
            e = tipos.get(brazo[1], {}).get(brazo[2], {}).get(tf)
            return (e, None) if e else (None, f"falta evaluar la base {brazo[2]} de {nombre(brazo[1])} en {tf}")
        if k in ("ver", "mejor"):
            fam, n = brazo[1], brazo[2]
            b, motivo = self.base_version(ck, fam, n, k)
            if motivo:
                return None, motivo
            e = tipos.get(fam, {}).get(b, {}).get(tf)
            pub = PUBLICADA.get((fam, n)) if k == "ver" else None
            e_pub = tipos.get(pub, {}).get(None, {}).get(tf) if pub else None
            if e_pub:                           # [AMB-21] la misma version publicada aparte (extension de H1/H2)
                b_pub, _ = self.pub_info(ck, pub)
                if b_pub != b:
                    raise ErrorVeredicto(f"{e_pub['csv']}: la version publicada es la base {b_pub} y la mediana "
                                         f"por val_elegido es {b}")
            if e:
                return e, None
            if e_pub:
                return e_pub, None
            return None, f"falta evaluar la base {b} de {nombre(fam)} en {tf}"
        raise ErrorVeredicto(f"brazo desconocido: {brazo}")

    def filas_csv(self, e):
        """({semilla: fila}, brazo) de un CSV del manifiesto, o None si no existe. ERROR si le falta la columna brazo,
        si tiene mas de un brazo o no es el brazo que escribe su trabajo (con su base), si repite una semilla, o si le
        falta o le sobra una semilla esperada (§7)."""
        ruta = os.path.join(self.raiz, e["csv"])
        if ruta in self._csv:
            return self._csv[ruta]
        if not os.path.exists(ruta):
            return None
        with open(ruta, newline="", encoding="utf-8") as f:
            filas = list(csv.DictReader(f))
        brazos = {r.get("brazo") for r in filas}
        if None in brazos or "" in brazos:
            raise ErrorVeredicto(f"{e['csv']}: falta la columna brazo o tiene filas sin brazo")
        if len(brazos) != 1:
            raise ErrorVeredicto(f"{e['csv']}: {len(brazos)} brazos en un CSV")
        brazo = next(iter(brazos))
        trabajo = self.trabajos.get(e.get("trabajo")) if e.get("trabajo") else None
        if trabajo is not None:
            meta = self.meta(politica_de(trabajo)) if politica_de(trabajo) else None
            if politica_de(trabajo) and meta is None:
                raise ErrorVeredicto(f"{e['csv']}: tiene CSV y no tiene el meta de su política {politica_de(trabajo)}")
            esperado = brazo_de_trabajo(trabajo, meta)
            if esperado is not None and brazo != esperado:
                raise ErrorVeredicto(f"{e['csv']}: el brazo es {brazo} y su trabajo escribe {esperado}")
            if meta is not None and e.get("base") is not None and meta.get("base") != e["base"]:
                raise ErrorVeredicto(f"{e['csv']}: el manifiesto dice base {e['base']} y el meta {meta.get('base')}")
        por = {}
        for r in filas:
            s = int(r["semilla"])
            if s in por:
                raise ErrorVeredicto(f"{e['csv']}: la semilla {s} aparece dos veces")
            por[s] = r
        esperadas = set(rango(e["semillas"]))
        faltan, sobran = sorted(esperadas - set(por)), sorted(set(por) - esperadas)
        if faltan or sobran:
            raise ErrorVeredicto(f"{e['csv']}: faltan las semillas {faltan[:5]} y sobran {sobran[:5]} (§7)")
        self._csv[ruta] = (por, brazo)
        return self._csv[ruta]

    def base_entregada(self, esc):
        """[AMB-26] IPPO entregado en el puente = su version evaluada (regla del 25.09: mediana por val_elegido de sus 3
        bases), leida de los CSV entregados de insumos/puente."""
        vals = {}
        for b in BASES3:
            m = self.meta(f"insumos/entregado/politica_{esc}_vecinos_s{b}.json")
            if m and vd.flotante(m.get("val_elegido")) is not None:
                vals[b] = vd.flotante(m["val_elegido"])
        return base_mediana_n(vals) if len(vals) == len(BASES3) else None

    def serie(self, ck, brazo, tl, metrica=METRICA):
        """({semilla: valor}, {semilla: fila}, semillas esperadas, motivo) de un brazo en una tanda logica (T1x junta
        t1r con la extension h1t1). motivo != None si falta algo: lo que lo usa queda PENDIENTE (o 'no se pudo
        correr'). ERROR si dos tandas fisicas repiten una semilla o si la metrica principal falta en una semilla."""
        c = self.celdas.get(ck)
        if c is None:
            return None, None, None, f"no hay evaluaciones de {ck[0]} ({ck[1]})"
        if brazo[0] == "ins":
            return self.serie_insumo(ck, brazo[1], tl, metrica)
        fisicas = FISICAS[c["llegadas"]].get(tl)
        if not fisicas:
            return None, None, None, f"no hay tanda {tl} con llegadas {c['llegadas']}"
        filas, esperadas = {}, set()
        for tf in fisicas:
            e, motivo = self.entrada(ck, brazo, tf)
            if motivo:
                return None, None, None, motivo
            leido = self.filas_csv(e)
            if leido is None:
                return None, None, None, f"falta el CSV {e['csv']}"
            por, nombre_csv = leido
            if brazo[0] == "ver" and e["tipo"] != brazo[1]:       # version publicada aparte: misma base
                b, _ = self.base_version(ck, brazo[1], brazo[2], "ver")
                if not nombre_csv.endswith(f"_s{b}"):
                    raise ErrorVeredicto(f"{e['csv']}: el brazo {nombre_csv} no es la base {b}")
            repetidas = set(por) & set(filas)
            if repetidas:
                raise ErrorVeredicto(f"{e['csv']}: semillas repetidas entre tandas {sorted(repetidas)[:5]}")
            filas.update(por)
            esperadas |= set(rango(e["semillas"]))
        return self._valores(filas, metrica, ck, brazo) + (esperadas, None)

    def serie_insumo(self, ck, cual, tl, metrica):
        """Puente (§8, descriptivo): fijo entregado o IPPO entregado de insumos/puente, en las semillas del puente."""
        if tl != "puente":
            return None, None, None, "lo entregado solo se usa en el puente"
        semillas = next((e["semillas"] for por in self.celdas[ck]["tipos"].values() for pb in por.values()
                         for t, e in pb.items() if t == "puente"), None)
        if semillas is None:
            return None, None, None, "la celda no tiene puente"
        nombre_csv = cual
        if cual == "ippo_entregado":
            b = self.base_entregada(ck[1])
            if b is None:
                return None, None, None, "faltan los metas de IPPO entregado"
            nombre_csv = f"ippo_vecinos_s{b}"
        rel = f"insumos/puente/eval_{ck[1]}_{nombre_csv}.csv"
        if not os.path.exists(os.path.join(self.raiz, rel)):
            return None, None, None, f"falta {rel}"
        self.verificar(rel, "insumos")
        leido = self.filas_csv({"csv": rel, "semillas": semillas})
        return self._valores(leido[0], metrica, ck, ("ins", cual)) + (set(rango(semillas)), None)

    @staticmethod
    def _valores(filas, metrica, ck, brazo):
        valores = {}
        for s, r in filas.items():
            v = vd.flotante(r.get(metrica))
            if v is None:
                if metrica == METRICA:
                    raise ErrorVeredicto(f"{metrica} vacio en la semilla {s} ({ck[1]}, {clave_brazo(brazo)})")
                continue
            valores[s] = v
        return valores, filas

    def comp(self, ck, a, b, tl, metrica=METRICA):
        """Comparacion de a frente a b en una tanda logica (cache): {comp, motivo, a, b, fa, fb}. motivo si falta algo
        o si los dos brazos no generan los mismos vehiculos en alguna semilla ([AMB-14]: la comparacion no vale)."""
        clave = (ck, a, b, tl, metrica)
        if clave in self._comp:
            return self._comp[clave]
        sa, fa, ea, ma = self.serie(ck, a, tl, metrica)
        sb, fb, eb, mb = (None, None, None, None) if ma else self.serie(ck, b, tl, metrica)
        res = {"comp": None, "motivo": ma or mb, "a": sa, "b": sb, "fa": fa, "fb": fb, "esperadas": ea}
        if not res["motivo"]:
            if ea != eb:
                raise ErrorVeredicto(f"{ck[1]} {tl}: {clave_brazo(a)} y {clave_brazo(b)} esperan otras semillas")
            malas = generados_iguales({"a": fa, "b": fb})
            if malas:
                res["motivo"] = (f"{clave_brazo(a)} y {clave_brazo(b)} no generan los mismos vehículos en "
                                 f"{len(malas)} semilla{'s' if len(malas) > 1 else ''} (la primera, {malas[0][0]})")
            elif metrica == METRICA:
                res["comp"] = comparar(sa, sb, ea)
            else:                               # secundarias: solo las semillas con valor en los dos brazos
                comunes = set(sa) & set(sb)
                res["comp"] = comparar({s: sa[s] for s in comunes}, {s: sb[s] for s in comunes}, comunes)
            if not res["motivo"] and res["comp"] is None:
                res["motivo"] = "sin cambio: la media de la referencia es 0"
        self._comp[clave] = res
        return res

    def convergencia(self, ck, brazo):
        """entrenamiento() de la version que juega un brazo; None si no es entrenado; {'sin_meta': True} si falta.
        [AMB-28] Una version jugada en otra celda (transferencias, IPPO entregado con llegadas aleatorias) lleva la
        convergencia de su propio entrenamiento: 'la version evaluada no convergio' es una propiedad de la version."""
        k = brazo[0]
        if k in ("ref", "ins"):
            return None
        if k == "pub":
            _, m = self.pub_info(ck, brazo[1])
            return entrenamiento(m) if m else {"convergio": False, "sin_meta": True}
        if k == "base":
            b = brazo[2]
        else:
            b, motivo = self.base_version(ck, brazo[1], brazo[2], k)
            if motivo:
                return {"convergio": False, "sin_meta": True}
        m, _, estado = self.meta_base(ck, brazo[1], b)
        return entrenamiento(m) if m else {"convergio": False, "sin_meta": True}

    # --- promocion y modelo citado ---

    def promocion(self, ck):
        """(decision, motivo) de la regla de promocion de la celda (§12). [AMB-20] La clave de promocion.json es el
        escenario de la celda (corredor, poi_corredor, ...; el generador llama a p3_promocion con --celda <escenario>).
        ERROR si el archivo de la celda no tiene el sha256 registrado en promocion.json."""
        if not os.path.exists(os.path.join(self.raiz, "promocion.json")):
            return None, "falta promocion.json (regla de promoción, §12)"
        d = json.loads(self.leer_otro("promocion.json")).get("celdas", {}).get(ck[1])
        if d is None:
            return None, f"falta la decisión de promoción de {ck[1]}"
        arch = d["archivo"]
        rel = os.path.relpath(arch, self.raiz).replace(os.sep, "/") if os.path.isabs(arch) else arch
        if not os.path.exists(os.path.join(self.raiz, rel)) or sha256(os.path.join(self.raiz, rel)) != d.get("sha256"):
            raise ErrorVeredicto(f"promocion: {rel} no coincide con el sha256 de promocion.json")
        dec = json.loads(self.leer_otro(rel))
        if dec.get("modelo_citado") != d.get("modelo_citado") or bool(dec.get("promovido")) != bool(d.get("promovido")):
            raise ErrorVeredicto(f"promocion: {rel} dice otra cosa que promocion.json")
        return dec, None

    def citado(self, ck, fam):
        """(brazo, nombre, promovido, motivo) del modelo citado (§12, A4). Sin variantes candidatas en la celda, V2 (con
        su version de las bases del diseno). Promovida, la variante con su version entre 42, 2042 y 4042, que debe ser
        la base que nombra p3_promocion (modelo_citado = ippo_<variante>_<etiqueta>med_s<base>)."""
        v2 = ("ver", fam, None)
        tipos = self.celdas[ck]["tipos"]
        if not set(tipos) & CANDIDATOS_PROMOCION:
            return v2, nombre(fam), False, None
        dec, motivo = self.promocion(ck)
        if motivo:
            return None, None, None, motivo
        if not dec.get("promovido"):
            return v2, nombre(fam), False, None
        tipo, base = tipo_de_brazo(dec.get("modelo_citado"), tipos)
        if tipo is None:
            return None, None, None, f"{dec.get('modelo_citado')} no es una variante de la celda"
        b, motivo = self.base_version(ck, tipo, 3, "ver")
        if motivo or b != base:
            return None, None, None, (f"{dec['modelo_citado']} no es la versión evaluada de {nombre(tipo)} "
                                      f"(base {b})")
        return ("ver", tipo, 3), nombre(tipo), True, None


def tipo_de_brazo(brazo, tipos):
    """(variante candidata, base) de un brazo de p3_promocion (ippo_<variante>_<etiqueta>med_s<base>): la candidata de
    la celda cuyo nombre es el comienzo mas largo de la etiqueta. (None, None) si no es ninguna."""
    m = re.fullmatch(r"ippo_[a-z]+_(p3[a-z0-9]+)_s(\d+)", str(brazo or ""))
    if not m:
        return None, None
    tipo = max((t for t in tipos if t in CANDIDATOS_PROMOCION and m.group(1).startswith(t)), key=len, default=None)
    return tipo, int(m.group(2))


# ---------------- Analisis: etiquetas por celda ----------------

def etiqueta_brazo(d, ck, brazo, tl, ref=REF_FINO, veto=None, con_convergencia=True):
    """Etiqueta de una tanda (§7): regla de veredicto.py frente a la referencia, con el veto del actuado ajustado en
    lo entrenado. [AMB-12] Lo que no se entrena (referencias) se juzga solo frente al fijo fino, como las filas de
    referencia de lo entregado. [AMB-13] Sin el actuado ajustado no hay veto que aplicar: PENDIENTE (falta), como
    lo entregado sin el actuado. PENDIENTE (no convergio; provisional) si la version no convergio."""
    if veto is None:
        veto = brazo[0] not in ("ref", "ins")
    r = {"texto": None, "comp": None, "comp_act": None, "conv": None, "brazo": brazo}
    c = d.comp(ck, brazo, ("ref", ref), tl)
    if c["motivo"]:
        r["texto"] = vd.texto_veredicto(None, c["motivo"])
        return r
    r["comp"] = c["comp"]
    if veto:
        ca = d.comp(ck, brazo, ("ref", REF_VETO), tl)
        if ca["motivo"]:
            r["texto"] = vd.texto_veredicto(None, ca["motivo"])
            return r
        r["comp_act"] = ca["comp"]
    conv = d.convergencia(ck, brazo) if con_convergencia else None
    r["conv"] = conv
    if conv and conv.get("sin_meta"):
        r["texto"] = vd.texto_veredicto(None, "sin el meta de la versión evaluada")
        return r
    r["texto"] = etiqueta(r["comp"], r["comp_act"], True if conv is None else conv["convergio"])
    return r


def sentido_brazo(d, ck, brazo, tl, lado="bajo", ref=REF_FINO, umbral=0.0):
    """Sentido entre entrenamientos de un brazo frente a una referencia: cada base de su version, frente a ella."""
    fam = brazo[1]
    bases = d.bases_disenio(ck, fam) if brazo[2] is None else (BASES3 if brazo[2] == 3 else BASES5)
    cambios = {}
    for b in bases:
        c = d.comp(ck, ("base", fam, b), ("ref", ref), tl)
        cambios[b] = c["comp"]["cambio"] if c.get("comp") else None
    return sentido(cambios, len(bases), lado, umbral)


def txt(x, dec=2):
    return "" if x is None else f"{x:.{dec}f}"


def txt_ic(ic, dec=2):
    return "" if not ic else f"[{ic[0]:.{dec}f}, {ic[1]:.{dec}f}]"


def txt_p(p):
    return "" if p is None else f"{p:.3g}"


def palabra_lado(texto):
    """[AMB-6] Lado de 'se repite en k de n': sobre cero si la etiqueta de esa tanda es FALLA; si no, bajo cero."""
    return "sobre" if palabra(texto) == "FALLA" else "bajo"


def referencias_al_lado(d, ck, brazo):
    """Etiqueta del brazo frente a cada referencia de la celda (sin veto ni convergencia): para las lecturas (§5)."""
    salida = {}
    for ref in sorted(t for t in d.celdas[ck]["tipos"] if t.startswith("ref_") and t != REF_FINO):
        e = {t: etiqueta_brazo(d, ck, brazo, t, ref=ref, veto=False, con_convergencia=False) for t in T}
        salida[ref] = {"T1": e["T1"], "T2": e["T2"], "citable": acuerdo(e["T1"]["texto"], e["T2"]["texto"])}
    return salida


def filas_no_insertados(d, ck):
    """§4 (cierre de la simulacion): por tanda y por CADA brazo de la celda, cuantas semillas cerraron con vehiculos
    que todavia esperaban entrar y cuantos vehiculos."""
    c, filas = d.celdas[ck], []
    for tipo, por in sorted(c["tipos"].items()):
        for base, ents in sorted(por.items(), key=lambda x: (x[0] is not None, x[0] or 0)):
            for tf, e in sorted(ents.items()):
                leido = d.filas_csv(e)
                if leido is None:
                    continue
                vals = [int(float(r.get("no_insertados") or 0)) for r in leido[0].values()]
                filas.append({"celda": ck[0], "escenario": ck[1], "llegadas": c["llegadas"], "tanda": tf,
                              "tipo": tipo, "nombre": nombre(tipo) + ("" if base is None else f", base {base}"),
                              "base": "" if base is None else base, "brazo": leido[1], "semillas": len(vals),
                              "semillas_con_no_insertados": sum(1 for v in vals if v > 0),
                              "vehiculos_no_insertados": sum(vals)})
    return filas


def fila_celda(d, ck):
    """Una fila de veredicto3_celdas.csv: modelo citado con su etiqueta en T1, T2 y la citable, cambio e IC por tanda,
    'se repite en k de n', etiqueta con la mejor base, la de V2 al lado y las lecturas obligadas (§11). Una celda sin
    modelo principal no desaparece: fila PENDIENTE con motivo y aviso; en --final, ERROR."""
    c = d.celdas[ck]
    fam = familia_principal(c)
    if fam is None:
        motivo = f"sin modelo principal ({', '.join(FAMILIAS_PRINCIPALES)}); tipos: {', '.join(sorted(c['tipos']))}"
        if d.estricto:
            raise ErrorVeredicto(f"la celda {ck[0]} ({ck[1]}) no tiene modelo principal: {motivo}")
        d.avisos.append(f"{ck[0]} ({ck[1]}): {motivo}")
        texto = vd.texto_veredicto(None, motivo)
        return {"celda": ck[0], "escenario": ck[1], "llegadas": c["llegadas"], "modelo_citado": "PENDIENTE",
                "promovido": "no", "etiqueta_T1": texto, "etiqueta_T2": texto, "etiqueta_citable": texto,
                "etiqueta_v2_citable": texto, "etiqueta_mejor_citable": texto, "motivo": motivo, "lecturas": "",
                "prob_pendiente_ruido": "", "_brazo_citado": None, "_brazo_v2": None, "_al_lado": {},
                "_promocion": None}
    v2 = ("ver", fam, None)
    cit, nom_cit, promovido, motivo_cit = d.citado(ck, fam)
    e_v2 = {t: etiqueta_brazo(d, ck, v2, t) for t in T}
    if cit is None:
        e_cit = {t: {"texto": vd.texto_veredicto(None, motivo_cit), "comp": None} for t in T}
    else:
        e_cit = e_v2 if cit == v2 else {t: etiqueta_brazo(d, ck, cit, t) for t in T}
    # la mejor base va al lado de la etiqueta citada: la de la familia del modelo citado (§6, §11, A3).
    # [AMB-22] Su etiqueta usa la convergencia de esa base.
    mejor = ("mejor", cit[1], cit[2]) if cit else ("mejor", fam, None)
    e_mj = {t: etiqueta_brazo(d, ck, mejor, t) for t in T}
    b_ver, _ = d.base_version(ck, fam, None, "ver")
    b_mj, _ = d.base_version(ck, mejor[1], mejor[2], "mejor")
    conv = d.convergencia(ck, cit or v2)
    fila = {"celda": ck[0], "escenario": ck[1], "llegadas": c["llegadas"], "modelo_citado": nom_cit or "PENDIENTE",
            "clave_citado": clave_brazo(cit) if cit else "", "promovido": "sí" if promovido else "no",
            "_brazo_citado": cit, "_brazo_v2": v2, "_e_cit": e_cit, "_e_v2": e_v2,
            "_promocion": d.promocion(ck)[0] if set(c["tipos"]) & CANDIDATOS_PROMOCION else None}
    lecturas = []
    for t in T:
        r = e_cit[t]
        comp = r.get("comp")
        fila[f"etiqueta_{t}"] = r["texto"]
        fila[f"cambio_{t}"] = txt(comp["cambio"]) if comp else ""
        fila[f"ic_{t}"] = txt_ic(comp["ic"]) if comp else ""
        fila[f"p_{t}"] = txt_p(comp["p"]) if comp else ""
        fila[f"borde_ic_{t}"] = ("sí" if comp["borde"] else "no") if comp else ""
        if cit is not None:
            s = sentido_brazo(d, ck, cit, t, palabra_lado(r["texto"]))
            sin_datos = all(x is None for x in s["cambios"].values())      # falta la referencia: no se cuenta
            fila[f"repite_{t}"] = "" if sin_datos else f"{s['k']} de {s['n']}"
            fila[f"_sentido_{t}"] = s
        fila[f"etiqueta_v2_{t}"] = e_v2[t]["texto"]
        fila[f"etiqueta_mejor_{t}"] = e_mj[t]["texto"]
    fila["etiqueta_citable"] = acuerdo(e_cit["T1"]["texto"], e_cit["T2"]["texto"])
    fila["etiqueta_v2_citable"] = acuerdo(e_v2["T1"]["texto"], e_v2["T2"]["texto"])
    fila["etiqueta_mejor_citable"] = acuerdo(e_mj["T1"]["texto"], e_mj["T2"]["texto"])
    if promovido:                               # la de V2 tambien lleva su mejor base al lado
        e_v2mj = {t: etiqueta_brazo(d, ck, ("mejor", fam, None), t) for t in T}
        fila["etiqueta_v2_mejor_citable"] = acuerdo(e_v2mj["T1"]["texto"], e_v2mj["T2"]["texto"])
    fila["version_evaluada"] = "" if b_ver is None else b_ver
    fila["mejor_base"] = "" if b_mj is None else b_mj
    fila["base_citado"] = d.base_version(ck, cit[1], cit[2], "ver")[0] if cit else ""
    fila["convergio"] = ("sí" if conv["convergio"] else "no") if conv and not conv.get("sin_meta") else ""
    fila["prob_pendiente_ruido"] = RUIDO_PENDIENTE.get((c["llegadas"], ck[0]), "no medido")
    # ciclo minimo y referencias al lado (lecturas obligadas de §5 y §11)
    iguales = []
    if cit is not None:
        for t in T:
            sa = d.serie(ck, cit, t)
            sc = d.serie(ck, ("ref", REF_CICLO), t)
            iguales.append(bool(not sa[3] and not sc[3] and igual_ciclo_minimo(sa[1], sc[1])))
        fila["igual_ciclo_minimo"] = "sí" if all(iguales) else "no"
        al_lado = referencias_al_lado(d, ck, cit)
    else:
        fila["igual_ciclo_minimo"] = ""
        al_lado = {}
    fila["_al_lado"] = al_lado
    cit_p = palabra(fila["etiqueta_citable"])
    if iguales and all(iguales):
        lecturas.append("Reproduce el ciclo mínimo (no se dice \"coordinación aprendida\").")
    for ref in ("ref_franja", "ref_bloques"):
        if ref in al_lado and cit_p in POSITIVAS and palabra(al_lado[ref]["citable"]) in ("EMPATA", "FALLA",
                                                                                          "CONTRADICTORIO"):
            lecturas.append(f"Mejora frente al fijo, pero no frente al {nombre(ref)}: la ventaja la logra también "
                            f"un plan por horario.")
    if "ref_regla" in al_lado and palabra(al_lado["ref_regla"]["citable"]) in ("EMPATA", "FALLA", "CONTRADICTORIO"):
        lecturas.append("No le gana a la regla simple: no se dice que el modelo aprendió algo que la regla no hace ni "
                        "\"coordinación aprendida\" (§5).")
    if cit is not None and cit_p in POSITIVAS:
        no_rep = [t for t in T if not fila[f"_sentido_{t}"]["cumple"]]
        if no_rep:
            s = fila[f"_sentido_{no_rep[0]}"]
            lecturas.append(f"La versión evaluada mejora; el método no se repite en {s['k']} de {s['n']} "
                            f"entrenamientos ({no_rep[0]}).")
    if "ref_fino5" in al_lado:                  # [AMB-16] §11 (gana el fino y empata el de 5 en 5) y §5 (iguala/supera)
        p5 = palabra(al_lado["ref_fino5"]["citable"])
        if cit_p == "FALLA" and p5 == "EMPATA":
            lecturas.append("Gana el fijo fino y empata el de verdes de 5 en 5: la diferencia está en verdes que "
                            "IPPO, decidiendo cada 5 s, no puede dar.")
        elif p5 in ("EMPATA", "FALLA"):
            lecturas.append("El fijo de verdes de 5 en 5 iguala o supera al modelo: parte de la ventaja del fijo fino "
                            "viene de verdes que IPPO, al decidir cada 5 s, no puede dar.")
    if ck == ("P6", gt.CASOS["P6"]):
        lecturas.append("P6 con la entrada por defecto: el cambio relativo está diluido por la espera de inserción; "
                        "ver P6e.")
    if promovido:
        lecturas.append(f"El modelo citado no es IPPO con mensajes corregido: es {nom_cit}; la etiqueta de IPPO con "
                        f"mensajes corregido es {fila['etiqueta_v2_citable']}.")
    if "c0med" in c["tipos"] and "entmed" in c["tipos"]:     # [AMB-23] con las tandas de 30 semillas (T1, T2)
        uno = [d.comp(ck, ("ver", fam, 3), ("pub", "c0med"), t) for t in T]
        dos = [d.comp(ck, ("pub", "c0med"), ("pub", "entmed"), t) for t in T]
        if all(x["comp"] and x["comp"]["ic"][1] < 0 and x["comp"]["p"] < ALFA for x in uno + dos):
            lecturas.append("V2 mejora a C0 y C0 mejora a IPPO entregado: parte de la ganancia viene de cómo se elige "
                            "la versión.")
    if palabra(fila["etiqueta_citable"]) == "PENDIENTE" and provisional(fila["etiqueta_citable"]):
        lecturas.append(f"PENDIENTE por no convergencia; probabilidad de que una política estable salga así por ruido: "
                        f"{fila['prob_pendiente_ruido']} (§6).")
    dejan = [x for x in filas_no_insertados(d, ck) if x["vehiculos_no_insertados"] > 0]
    if dejan:                                   # §4, cierre de la simulacion
        lista = "; ".join(f"{x['nombre']} en {x['tanda']}: {x['semillas_con_no_insertados']} de {x['semillas']} "
                          f"semillas, {x['vehiculos_no_insertados']} vehículos" for x in dejan[:4])
        lecturas.append(f"Deja vehículos sin entrar al cierre ({lista}{'; ...' if len(dejan) > 4 else ''}): su "
                        f"retraso total está subestimado y la diferencia con un brazo que no los deja es conservadora.")
    fila["lecturas"] = " | ".join(lecturas)
    fila["motivo"] = motivo_cit or ""
    return fila


# ---------------- Analisis: bases ----------------

def tabla_bases(d):
    """Todas las bases de todos los brazos (§11): las de cada familia por base y las candidatas de cada version
    publicada (C0, V2 vieja, IPPO entregado...). Una fila por politica."""
    filas, vistas = [], set()

    def agregar(ck, fam, b, pol, meta, ver, mejor, estado="publicada"):
        clave = pol or (ck, fam, b)             # una base sin ruta conocida no se confunde con otra
        if clave in vistas:
            return
        vistas.add(clave)
        fila = {"celda": ck[0], "escenario": ck[1], "llegadas": d.celdas[ck]["llegadas"], "familia": fam,
                "nombre": nombre(fam), "base": b, "politica": pol or "",
                "version_evaluada": "sí" if b == ver else "no", "mejor_base": "sí" if b == mejor else "no"}
        if meta is None:
            caida = d.caidas.get((ck[0], ck[1], fam, b))
            fila["estado"] = ("caída declarada en cola/caidas.json (" + ", ".join(
                f"{i['id']}: {i['error']} ({i['fecha']})" for i in caida["intentos"]) + ")" if caida
                else "sin meta: falta entrenarla o declararla caída (§14)")
            filas.append(fila)
            return
        e = entrenamiento(meta)
        fila.update({"estado": "publicada", "escenario_entrenamiento": meta.get("escenario", ""),
                     "criterio": e["criterio"], "serie": e["serie"], "val_elegido": txt(e["val"], 3),
                     "ep_elegido": e["ep"], "episodios": int(e["episodios"]), "n_validaciones": e["n_validaciones"],
                     "convergio": "sí" if e["convergio"] else "no", "meseta": txt(e["meseta"]),
                     "estabilidad": txt(e["estabilidad"]), "dist_mediana_s": txt(e["dist_mediana_s"], 3),
                     "dist_mediana_pct": txt(e["dist_mediana_pct"]),
                     "min_repetido": "sí" if e["min_repetido"] else "no",
                     "dos_mejores_seguidos": "sí" if e["dos_mejores_seguidos"] else "no",
                     "semillas_validacion": len(e["val_seeds"] or [])})
        filas.append(fila)

    for ck in d.orden():
        tipos = d.celdas[ck]["tipos"]
        principal = familia_principal(d.celdas[ck])
        for fam in sorted(tipos, key=lambda x: (x != principal, x)):
            if any(b is not None for b in tipos[fam]):
                ver, _ = d.base_version(ck, fam, None, "ver")
                mejor, _ = d.base_version(ck, fam, None, "mejor")
                for b in d.bases_disenio(ck, fam):
                    meta, pol, estado = d.meta_base(ck, fam, b)
                    agregar(ck, fam, b, pol, meta, ver, mejor, estado)
            elif not fam.startswith("ref_"):
                ents = [e for por in tipos[fam].values() for e in por.values()]
                pol = next((e["politica"] for e in ents if e.get("politica")), None)
                meta = d.meta(pol)
                if meta and meta.get("candidatas"):
                    b_el, _ = d.pub_info(ck, fam)
                    vals = {int(x["base"]): vd.flotante((d.meta(x["politica"]) or {}).get("val_elegido"))
                            for x in meta["candidatas"]}
                    mejor = mejor_base({b: v for b, v in vals.items() if v is not None})
                    for x in meta["candidatas"]:
                        agregar(ck, fam, int(x["base"]), x["politica"], d.meta(x["politica"]), b_el, mejor)
    return filas


# ---------------- Analisis: hipotesis (§8) ----------------

def h(id_, prueba, ck, a, b, n_fam=None, familia=None, tandas=T, sentido_=None, que=""):
    return {"id": id_, "prueba": prueba, "celda": ck, "a": a, "b": b, "familia": familia or id_, "n_familia": n_fam,
            "tandas": tandas, "sentido": sentido_, "que": que}


def pruebas_definidas():
    """Las pruebas de §8 con sus familias exactas (superioridad, no inferioridad) y los contrastes descriptivos."""
    R = lambda c: (c, ESC_REG[c])                                   # noqa: E731
    A = lambda c: (c, gt.POI[c])                                    # noqa: E731
    V = lambda fam, n=3: ("ver", fam, n)                            # noqa: E731
    L = []
    for c in CASOS6:
        L.append(h("H1", "ni", R(c), V("v2reg"), ("pub", "c0med"), 6, tandas=("T1x", "T2x"),
                   que="V2 no es peor que C0 (120 semillas por tanda)"))
    for c in CASOS6:
        L.append(h("H1", "ni", R(c), V("v2reg"), ("pub", "entmed"), 6, familia="H1 frente a IPPO entregado",
                   tandas=("T1x", "T2x"), que="V2 no es peor que IPPO entregado (secundaria)"))
    for c in ("P4", "m6525"):
        L.append(h("H2", "sup", R(c), V("v2reg"), ("pub", "c0med"), 2, tandas=("T1x", "T2x"),
                   sentido_=("pares", "v2reg", "c0", BASES3), que="V2 < C0 (120 semillas por tanda)"))
    for c in ("P1", "P2", "P6"):
        L.append(h("H7r", "sup", R(c), V("v2reg"), V("v2loc"), 3, sentido_=("pares", "v2reg", "v2loc", BASES3),
                   que="con mensajes < sin mensajes, llegadas regulares"))
    for c in CASOS6:
        L.append(h("H7", "sup", A(c), V("v2poi"), V("v2poiloc"), 6, sentido_=("pares", "v2poi", "v2poiloc", BASES3),
                   que="con mensajes < sin mensajes, llegadas aleatorias"))
    for c, n in (("c2715", 5), ("P2", 3), ("D", 5)):
        L.append(h("H8a", "sup", R(c), V("p3obs", n), V("v2reg", n), 3,
                   sentido_=("pares", "p3obs", "v2reg", BASES5 if n == 5 else BASES3),
                   que="V2 + observación < V2, llegadas regulares"))
    for c in CASOS6:
        L.append(h("H8b", "sup", A(c), V("p3obspoi"), V("v2poi"), 6, sentido_=("pares", "p3obspoi", "v2poi", BASES3),
                   que="V2 + observación < V2, llegadas aleatorias"))
    for c in ("P1", "P3", "P6"):                # [AMB-8] no inferioridad de metodo: con sentido bajo +2 %
        L.append(h("H8c", "ni", R(c), V("p3obs"), V("v2reg"), 3, sentido_=("pares", "p3obs", "v2reg", BASES3),
                   que="V2 + observación no es peor que V2"))
    for c in ("P2", "P6"):
        L.append(h("H12", "ni", R(c), V("p3m7"), V("v2reg"), 2, sentido_=("pares", "p3m7", "v2reg", BASES3),
                   que="V2 + las tres limpiezas no es peor que V2"))
    for c in ("D", "P1", "P2", "P6"):
        L.append(h("H14", "sup", R(c), V("p3reloj2"), V("v2reg"), 4, familia="H14 regulares",
                   sentido_=("pares", "p3reloj2", "v2reg", BASES3), que="reloj de 2 s < reloj de 5 s"))
    for c in ("P1", "P2", "P6"):
        L.append(h("H14", "sup", A(c), V("p3reloj2poi"), V("v2poi"), 3, familia="H14 aleatorias",
                   sentido_=("pares", "p3reloj2poi", "v2poi", BASES3), que="reloj de 2 s < reloj de 5 s"))
    for c in ("P1", "P2", "P4", "P6"):
        L.append(h("H15", "sup", R(c), V("p3completo"), V("v2reg"), 4, familia="H15 regulares",
                   sentido_=("pares", "p3completo", "v2reg", BASES3), que="modelo completo < V2"))
    for c in CASOS6:
        L.append(h("H15", "sup", A(c), V("p3completopoi"), V("v2poi"), 6, familia="H15 aleatorias",
                   sentido_=("pares", "p3completopoi", "v2poi", BASES3), que="modelo completo < V2"))
    for c in CASOS6:
        L.append(h("H9", "sup", R(c), V("p3e400"), V("v2reg"), 6, familia="H9 regulares",
                   sentido_=("pares", "p3e400", "v2reg", BASES3), que="400 episodios con piso < 200 sin piso"))
    for c in CASOS6:
        L.append(h("H9", "sup", A(c), V("p3e400poi"), V("v2poi"), 6, familia="H9 aleatorias",
                   sentido_=("pares", "p3e400poi", "v2poi", BASES3), que="400 episodios con piso < 200 sin piso"))
    for red, celdas in REDES.items():
        for c in celdas:
            L.append(h("H10", "ni", R(c), V(TIPO_RED), V("v2reg"), len(celdas), familia=f"H10 {red}",
                       sentido_=("pares", TIPO_RED, "v2reg", BASES3), que="una política por red no es peor que V2"))
    # Descriptivas (sin Holm): ablacion, cuadro 2x2 y C0 frente a IPPO entregado, puente, C0 aleatorio,
    # transferencias, limpiezas por separado, entropia, reloj sin forzadas y el estudio de 400 episodios.
    for c in ("P4", "P6"):
        for et in ("p3sd", "p3se"):
            L.append(h("Ablación", "desc", R(c), V(et), V("v2reg"), que=f"{nombre(et)} frente a V2"))
            L.append(h("Ablación", "desc", R(c), V(et), ("pub", "c0med"), que=f"{nombre(et)} frente a C0"))
    for c in CASOS6 + list(gt.NIVELES):
        L.append(h("2x2", "desc", R(c), V("v2reg"), ("pub", "c0med"), que="entrenamiento, con la selección nueva"))
        L.append(h("2x2", "desc", R(c), ("pub", "c0med"), ("pub", "entmed"),
                   que="selección, con el entrenamiento viejo (C0 frente a IPPO entregado)"))
        L.append(h("2x2", "desc", R(c), V("v2reg"), ("pub", "v2viejamed"), que="selección, con V2"))
        L.append(h("2x2", "desc", R(c), ("pub", "v2viejamed"), ("pub", "entmed"),
                   que="entrenamiento, con la selección vieja"))
    for c in CASOS6:
        for brazo in (("pub", "v2reg3med"), ("pub", "v2viejamed"), ("pub", "c0med")):
            for ins in ("fijo", "ippo_entregado"):
                L.append(h("Puente", "desc", R(c), brazo, ("ins", ins), tandas=("puente",),
                           que=f"{nombre_brazo(brazo)} frente a {nombre_brazo(('ins', ins))} (1001-1030)"))
    for c in CASOS6:                            # [AMB-27] fijada el 05.11: frente a C0, la V2 de 42, 2042 y 4042 (§6)
        L.append(h("C0 aleatorio", "desc", A(c), ("pub", "c0poimed"), ("pub", "v2reg3poi"),
                   que="elegir con desorden (C0 aleatorio frente a la V2 regular de 3 bases)"))
        L.append(h("C0 aleatorio", "desc", A(c), V("v2poi"), ("pub", "c0poimed"),
                   que="entrenar con desorden (V2 aleatoria frente a C0 aleatorio)"))
        L.append(h("Transferencia", "desc", A(c), ("pub", "v2regmed"), V("v2poi", None),
                   que="V2 regular jugada con llegadas aleatorias frente a la V2 aleatoria"))
        L.append(h("Transferencia", "desc", R("P6e" if c == "P6" else c), ("pub", "v2poimed"), V("v2reg", None),
                   que="V2 aleatoria jugada con llegadas regulares frente a la V2 regular"))
    for et in ("p3m7norm", "p3m7forz", "p3m7msg"):
        L.append(h("Limpiezas por separado", "desc", R("D"), V(et), V("v2reg"), que=f"{nombre(et)} frente a V2"))
    for c in ("P1", "D"):
        L.append(h("Entropía", "desc", R(c), V("p3ent"), V("v2reg"), que="más entropía frente a V2"))
    L.append(h("H14 sin forzadas", "desc", R("D"), V("p3reloj2"), V("p3m7forz"),
               que="reloj de 2 s frente a solo sin decisiones forzadas"))
    for tipo, ck_de, v2 in (("reg", R, "v2reg"), ("poi", A, "v2poi")):
        for c in CASOS6:
            L.append(h("3b", "desc", ck_de(c), V(f"p3piso200{tipo}"), V(v2), que="200 con piso frente a 200 sin piso"))
            L.append(h("3b", "desc", ck_de(c), V(f"p3e400c20{tipo}"), V(v2), que="400 eligiendo entre 20 frente a V2"))
            L.append(h("3b", "desc", ck_de(c), V("p3e400" + ("poi" if tipo == "poi" else "")),
                       V(f"p3e400c20{tipo}"), que="400 eligiendo entre 40 frente a eligiendo entre 20"))
    # a3, "¿la politica usa lo que ve?" (§8): cada version perturbada frente a la misma version sin perturbar
    for lleg, (celdas, versiones) in A3_CELDAS.items():
        for c in celdas:
            for t in versiones:
                for pert in A3_PERTURBACION:
                    L.append(h("a3", "desc", R(c) if lleg == "regulares" else A(c), ("pub", f"a3{pert}_{t}"),
                               ("ver",) + A3_VERSION[t],
                               que=f"{nombre(f'a3{pert}_{t}')} frente a la misma versión sin perturbar"))
    return L


def evaluar_pruebas(d, specs):
    """Comparacion de cada prueba en cada tanda, Holm por familia y tanda (§9) y lectura. [AMB-8] (fijada el 05.11) El
    sentido entre entrenamientos se exige en toda superioridad y en las no inferioridades H8c, H12 y H10 (cada base
    bajo +2 % en T1 y T2). H1 va SIN sentido: su potencia (>= 93 % con 120 semillas por tanda) se calculo sin el, y C0
    por base solo se evalua en P4 y en la malla con 6525 veh/h (para H2)."""
    res = []
    for s in specs:
        r = {"spec": s, "tandas": {}}
        for t in s["tandas"]:
            c = d.comp(s["celda"], s["a"], s["b"], t)
            x = {"motivo": c["motivo"], "comp": c["comp"], "n": len(c["a"]) if c.get("a") else None}
            if not x["motivo"] and s["prueba"] == "ni":
                x["p_ni"] = p_no_inferioridad(c["a"], c["b"])
            if s["sentido"]:
                _, fa, fb, bases = s["sentido"]
                umbral = MARGEN_NI if s["prueba"] == "ni" else 0.0
                cambios = {}
                for b in bases:
                    cb = d.comp(s["celda"], ("base", fa, b), ("base", fb, b), t)
                    cambios[b] = cb["comp"]["cambio"] if cb.get("comp") else None
                x["sentido"] = sentido(cambios, len(bases), "bajo", umbral)
            r["tandas"][t] = x
        res.append(r)
    familias = {}
    for i, r in enumerate(res):
        if r["spec"]["prueba"] in ("sup", "ni"):
            familias.setdefault(r["spec"]["familia"], []).append(i)
    for fam, idx in familias.items():
        n_decl = res[idx[0]]["spec"]["n_familia"]
        if len(idx) != n_decl:
            raise ErrorVeredicto(f"familia {fam}: {len(idx)} pruebas y el prerregistro fija {n_decl}")
        for k in range(len(res[idx[0]]["spec"]["tandas"])):
            pv = {}
            for i in idx:
                x = res[i]["tandas"][res[i]["spec"]["tandas"][k]]
                pv[i] = None if x["motivo"] else (x["p_ni"] if res[i]["spec"]["prueba"] == "ni" else x["comp"]["p"])
            for i, p in holm(pv).items():
                res[i]["tandas"][res[i]["spec"]["tandas"][k]]["p_aj"] = p
    for r in res:
        s, lecturas = r["spec"], []
        for t in s["tandas"]:
            x = r["tandas"][t]
            if x["motivo"]:
                x["lectura"] = "no se pudo correr"
            elif s["prueba"] == "sup":
                x["lectura"] = ("pasa" if x["comp"]["ic"][1] < 0 and x["p_aj"] is not None and x["p_aj"] < ALFA
                                else "no pasa")
            elif s["prueba"] == "ni":
                x["lectura"] = lectura_ni(x["comp"], x["p_aj"])
            else:
                lo, hi = x["comp"]["ic"]
                x["lectura"] = ("menor" if hi < 0 and x["comp"]["p"] < ALFA else
                                "mayor" if lo > 0 and x["comp"]["p"] < ALFA else "sin diferencia")
            lecturas.append(x["lectura"])
        sen_ok = all(r["tandas"][t].get("sentido", {}).get("cumple", True) for t in s["tandas"])
        if s["prueba"] == "sup":
            r["pasa"] = all(x == "pasa" for x in lecturas) and sen_ok
            r["lectura"] = "pasa" if r["pasa"] else ("no se pudo correr" if "no se pudo correr" in lecturas
                                                       else "no pasa")
            if all(x == "pasa" for x in lecturas) and not sen_ok:      # lectura obligada de §11
                malos = "; ".join(f"{r['tandas'][t]['sentido']['k']} de {r['tandas'][t]['sentido']['n']} en {t}"
                                  for t in s["tandas"] if not r["tandas"][t]["sentido"]["cumple"])
                r["lectura"] = f"no pasa: la versión evaluada mejora; el método no se repite en {malos} entrenamientos"
        elif s["prueba"] == "ni":               # [AMB-9] fijada el 05.11: lectura_ni_conjunta
            r["pasa"], r["lectura"] = lectura_ni_conjunta(
                {t: r["tandas"][t]["lectura"] for t in s["tandas"]},
                {t: r["tandas"][t]["sentido"] for t in s["tandas"]} if s["sentido"] else None)
        else:
            r["pasa"] = None
            r["lectura"] = lecturas[0] if len(set(lecturas)) == 1 else "no se repite: " + " / ".join(lecturas)
        if not sen_ok and s["prueba"] == "sup" and all(x != "no se pudo correr" for x in lecturas):
            malos = [f"{t}: {r['tandas'][t]['sentido']['k']} de {r['tandas'][t]['sentido']['n']}" for t in s["tandas"]
                     if not r["tandas"][t]["sentido"]["cumple"]]
            r["nota"] = "el método no se repite entre entrenamientos (" + "; ".join(malos) + ")"
    return res


def h_etiqueta(d, ck):
    """H3, H3e y H5: etiqueta citable de V2 (version del diseno, 5 bases) frente al fijo fino, convergida, y sentido 4
    de 5 de sus bases frente al fijo fino en T1 y T2."""
    if ck not in d.celdas or familia_principal(d.celdas[ck]) is None:
        return None
    fam = familia_principal(d.celdas[ck])
    v2 = ("ver", fam, None)
    e = {t: etiqueta_brazo(d, ck, v2, t) for t in T}
    cit = acuerdo(e["T1"]["texto"], e["T2"]["texto"])
    sen = {t: sentido_brazo(d, ck, v2, t, "bajo") for t in T}
    return {"e": e, "citable": cit, "sentido": sen,
            "pasa": palabra(cit) in POSITIVAS and all(sen[t]["cumple"] for t in T)}


def h6(d):
    """H6: D = cambio aleatorio - cambio regular de V2 (5 bases) frente a su fijo fino (P6: el lado regular es P6e);
    bootstrap independiente, T1 con T1 y T2 con T2; Holm de 6 por par; sentido: D por base, 4 de 5."""
    filas = []
    for c in CASOS6:
        cka, ckr = (c, gt.POI[c]), (("P6e", gt.P6E["P6e"]) if c == "P6" else (c, gt.CASOS[c]))
        x = {"caso": c, "tandas": {}}
        for t in T:
            sa = d.serie(cka, ("ver", "v2poi", None), t)
            fa = d.serie(cka, ("ref", REF_FINO), t)
            sr = d.serie(ckr, ("ver", "v2reg", None), t)
            fr = d.serie(ckr, ("ref", REF_FINO), t)
            motivo = next((s[3] for s in (sa, fa, sr, fr) if s[3]), None)
            if motivo:
                x["tandas"][t] = {"motivo": motivo}
                continue
            dif = diferencia_no_pareada(sa[0], fa[0], sr[0], fr[0], sa[2], sr[2])
            cambios = {}
            for b in BASES5:
                ca = d.comp(cka, ("base", "v2poi", b), ("ref", REF_FINO), t)
                cr = d.comp(ckr, ("base", "v2reg", b), ("ref", REF_FINO), t)
                cambios[b] = (ca["comp"]["cambio"] - cr["comp"]["cambio"]) if ca["comp"] and cr["comp"] else None
            x["tandas"][t] = {"motivo": None, "dif": dif, "sentido": sentido(cambios, len(BASES5), "bajo")}
        filas.append(x)
    for t in T:
        aj = holm({i: (x["tandas"][t]["dif"]["p"] if not x["tandas"][t]["motivo"] else None)
                   for i, x in enumerate(filas)})
        for i, x in enumerate(filas):
            x["tandas"][t]["p_aj"] = aj[i]
    for x in filas:
        ok = []
        for t in T:
            y = x["tandas"][t]
            if y["motivo"]:
                y["lectura"] = "no se pudo correr"
            else:
                y["lectura"] = "pasa" if y["dif"]["ic"][1] < 0 and y["p_aj"] < ALFA else "no pasa"
            ok.append(y["lectura"] == "pasa" and y["sentido"]["cumple"])
        x["pasa"] = all(ok)
    return filas


def fila_h(id_, familia, n_fam, prueba, caso, llegadas, a, b, tandas, pasa, lectura, nota="", que=""):
    fila = {"id": id_, "familia": familia, "n_familia": n_fam or "", "prueba": prueba, "que": que, "caso": caso,
            "llegadas": llegadas, "a": a, "b": b, "pasa": "" if pasa is None else ("sí" if pasa else "no"),
            "lectura": lectura, "nota": nota}
    for k, (t, x) in enumerate(tandas):
        n = str(k + 1)
        if not x:
            continue
        fila.update({f"tanda_{n}": t, f"semillas_{n}": x.get("n", ""), f"cambio_{n}": x.get("cambio", ""),
                     f"ic_{n}": x.get("ic", ""), f"p_{n}": x.get("p", ""), f"p_ajustado_{n}": x.get("p_aj", ""),
                     f"lectura_{n}": x.get("lectura", ""), f"sentido_{n}": x.get("sentido", "")})
    return fila


def txt_sentido(s):
    return "" if not s else f"{s['k']} de {s['n']}" + ("" if s["cumple"] else f" (hacen falta {s['requerido']})")


def hipotesis(d, filas_celdas):
    """Todas las hipotesis de §8, pasen o no (§11): filas de veredicto3_hipotesis.csv y un resumen para el .md."""
    salida, resumen = [], []
    def llegadas_de(ck):
        if ck in d.celdas:
            return d.celdas[ck]["llegadas"]
        return "aleatorias" if ck[1].startswith("poi_") else "regulares"
    res = evaluar_pruebas(d, pruebas_definidas())
    for r in res:
        s = r["spec"]
        tandas = []
        for t in s["tandas"]:
            x = r["tandas"][t]
            comp = x.get("comp")
            tandas.append((t, {"n": x.get("n") or "", "cambio": txt(comp["cambio"]) if comp else "",
                               "ic": txt_ic(comp["ic"]) if comp else "",
                               "p": txt_p(x.get("p_ni") if s["prueba"] == "ni" else (comp["p"] if comp else None)),
                               "p_aj": txt_p(x.get("p_aj")), "lectura": x.get("lectura", ""),
                               "sentido": txt_sentido(x.get("sentido"))}))
        nota = r.get("nota") or "; ".join(sorted({r["tandas"][t]["motivo"] for t in s["tandas"]
                                                  if r["tandas"][t]["motivo"]}))
        prueba = {"sup": "superioridad", "ni": "no inferioridad (+2 %)", "desc": "descriptiva"}[s["prueba"]]
        salida.append(fila_h(s["id"], s["familia"], s["n_familia"], prueba, s["celda"][0], llegadas_de(s["celda"]),
                             nombre_brazo(s["a"]), nombre_brazo(s["b"]), tandas, r["pasa"], r["lectura"], nota,
                             s["que"]))
    # H1 global por interseccion-union (sin Holm)
    casos_h1 = [r for r in res if r["spec"]["familia"] == "H1"]
    iu = interseccion_union([[r["tandas"][t] if not r["tandas"][t]["motivo"] else None for t in r["spec"]["tandas"]]
                             for r in casos_h1])
    peores = [f"{r['spec']['celda'][0]} ({r['lectura']})" for r in casos_h1 if r["lectura"] != "no es peor"]
    # [AMB-9] en H1, toda tanda que da "es peor" se nombra con su caso y su cifra
    es_peor = [f"{r['spec']['celda'][0]} es peor en {t} ({r['tandas'][t]['comp']['cambio']:+.2f} % "
               f"{txt_ic(r['tandas'][t]['comp']['ic'])})" for r in casos_h1 for t in r["spec"]["tandas"]
               if r["tandas"][t].get("lectura") == "es peor"]
    nota_h1 = "" if iu else ("no da 'no es peor' al 5 % en las dos tandas: " + ", ".join(peores)
                             + (". " + "; ".join(es_peor) if es_peor else ""))
    salida.append(fila_h("H1", "H1 global", "", "intersección-unión", "global", "regulares", "V2", "C0", [],
                         iu, "pasa" if iu else "no pasa", nota_h1, "V2 no es peor que C0 en ningún caso (P1-P6)"))
    resumen.append(("H1", "V2 no es peor que C0 en ningún caso (P1-P6, 120 semillas)", iu,
                    "pasa" if iu else "no pasa: " + ", ".join(peores) + (". " + "; ".join(es_peor) if es_peor else "")))
    for id_, fam, regla in (("H2", "H2", None), ("H7r", "H7r", None), ("H7", "H7", None), ("H8a", "H8a", None),
                            ("H8b", "H8b", 1), ("H8c", "H8c", None), ("H12", "H12", None),
                            ("H14", "H14 regulares", None), ("H14", "H14 aleatorias", None),
                            ("H15", "H15 regulares", None), ("H15", "H15 aleatorias", None),
                            ("H9", "H9 regulares", None), ("H9", "H9 aleatorias", None)):
        rs = [r for r in res if r["spec"]["familia"] == fam]
        k = sum(1 for r in rs if r["pasa"])
        casos = ", ".join(r["spec"]["celda"][0] for r in rs if r["pasa"]) or "ninguno"
        if regla is None:                       # [AMB-18] caso por caso; en la plantilla de §17, "pasa" = 1 caso o mas
            pasa, lect = k >= 1, f"pasa en {k} de {len(rs)} casos: {casos}"
        else:
            pasa = k >= regla
            lect = f"{'pasa' if pasa else 'no pasa'}: {k} de {len(rs)} casos ({casos}); hace falta {regla}"
        salida.append(fila_h(id_, fam, len(rs), "resumen", "global", "", "", "", [], pasa, lect, "",
                             rs[0]["spec"]["que"] if rs else ""))
        resumen.append((fam, rs[0]["spec"]["que"] if rs else fam, pasa, lect))
    for red in REDES:
        rs = [r for r in res if r["spec"]["familia"] == f"H10 {red}"]
        k = sum(1 for r in rs if r["pasa"])
        pasa = k >= MINIMO_RED[red]
        lect = (f"{'pasa' if pasa else 'no pasa'}: 'no es peor' en {k} de {len(rs)} niveles; hacen falta "
                f"{MINIMO_RED[red]} ('no concluyente' no cuenta)")
        salida.append(fila_h("H10", f"H10 {red}", len(rs), "resumen", "global", "regulares", "", "", [], pasa, lect,
                             "", f"una política por red ({red}) no es peor que la V2 de cada nivel"))
        resumen.append((f"H10 {red}", f"una política por red ({red}) no es peor que la V2 de cada nivel", pasa, lect))
    # H3 y H3e (P6 y P6e regulares) y H5 (aleatorias, al menos 3 de 6)
    for id_, ck, desc in (("H3", ("P6", gt.CASOS["P6"]), False), ("H3e", ("P6e", gt.P6E["P6e"]), True)):
        x = h_etiqueta(d, ck)
        if x is None:
            salida.append(fila_h(id_, id_, "", "etiqueta citable", ck[0], "regulares", "V2", "fijo fino", [], False,
                                 "no se pudo correr", "faltan las evaluaciones de V2"))
            resumen.append((id_, f"etiqueta citable de V2 en {ck[0]}", None if desc else False, "no se pudo correr"))
            continue
        tandas = [(t, {"lectura": x["e"][t]["texto"], "sentido": txt_sentido(x["sentido"][t]),
                       "cambio": txt(x["e"][t]["comp"]["cambio"]) if x["e"][t]["comp"] else "",
                       "ic": txt_ic(x["e"][t]["comp"]["ic"]) if x["e"][t]["comp"] else ""}) for t in T]
        lect = f"citable {x['citable']}; sentido {txt_sentido(x['sentido']['T1'])} y {txt_sentido(x['sentido']['T2'])}"
        salida.append(fila_h(id_, id_, "", "etiqueta citable" + (" (descriptiva)" if desc else ""), ck[0],
                             "regulares", "V2", "fijo fino", tandas, None if desc else x["pasa"], lect, "",
                             "MEJORA o FUNCIONA frente al fijo fino, convergida y con sentido 4 de 5"))
        resumen.append((id_, f"V2 MEJORA o FUNCIONA frente al fijo fino en {ck[0]}",
                        x["pasa"] if not desc else None, lect + ("" if not desc else " (descriptiva)")))
    k5, casos5 = 0, []
    for c in CASOS6:
        ck = (c, gt.POI[c])
        x = h_etiqueta(d, ck)
        if x is None:
            salida.append(fila_h("H5", "H5", "", "etiqueta citable", c, "aleatorias", "V2", "fijo fino", [], False,
                                 "no se pudo correr", "faltan las evaluaciones de V2"))
            continue
        k5 += x["pasa"]
        if x["pasa"]:
            casos5.append(c)
        tandas = [(t, {"lectura": x["e"][t]["texto"], "sentido": txt_sentido(x["sentido"][t]),
                       "cambio": txt(x["e"][t]["comp"]["cambio"]) if x["e"][t]["comp"] else "",
                       "ic": txt_ic(x["e"][t]["comp"]["ic"]) if x["e"][t]["comp"] else ""}) for t in T]
        salida.append(fila_h("H5", "H5", "", "etiqueta citable", c, "aleatorias", "V2", "fijo fino", tandas, x["pasa"],
                             f"citable {x['citable']}", ""))
    lect5 = f"{'pasa' if k5 >= 3 else 'no pasa'}: {k5} de 6 casos ({', '.join(casos5) or 'ninguno'}); hacen falta 3"
    salida.append(fila_h("H5", "H5", "", "resumen", "global", "aleatorias", "V2", "fijo fino", [], k5 >= 3, lect5, "",
                         "V2 aleatoria MEJORA o FUNCIONA frente al fijo fino en al menos 3 de 6 casos"))
    resumen.append(("H5", "V2 aleatoria MEJORA o FUNCIONA frente al fijo fino re-ajustado en al menos 3 de 6",
                    k5 >= 3, lect5))
    # H6
    k6 = []
    for x in h6(d):
        tandas = []
        for t in T:
            y = x["tandas"][t]
            if y["motivo"]:
                tandas.append((t, {"lectura": "no se pudo correr"}))
                continue
            tandas.append((t, {"cambio": txt(y["dif"]["D"]), "ic": txt_ic(y["dif"]["ic"]), "p": txt_p(y["dif"]["p"]),
                               "p_aj": txt_p(y["p_aj"]), "lectura": y["lectura"],
                               "sentido": txt_sentido(y["sentido"])}))
        nota = "; ".join(sorted({x["tandas"][t]["motivo"] for t in T if x["tandas"][t]["motivo"]}))
        salida.append(fila_h("H6", "H6", 6, "diferencia no pareada (D = aleatorias - regulares)", x["caso"],
                             "las dos", "V2 aleatoria frente a su fijo fino", "V2 regular frente a su fijo fino",
                             tandas, x["pasa"], "pasa" if x["pasa"] else "no pasa", nota,
                             "la ventaja frente al fijo es mayor con llegadas aleatorias"))
        if x["pasa"]:
            k6.append(x["caso"])
    resumen.append(("H6", "la ventaja frente al fijo es mayor con llegadas aleatorias (por caso)", len(k6) >= 1,
                    f"pasa en {len(k6)} de 6 casos: {', '.join(k6) or 'ninguno'}"))
    # H4 (descriptiva): cada base de V2 a +-1 % del ciclo minimo, en T1 y T2
    for c in ("P3", "P5", "m1810", "m2715", "m3620"):
        ck = (c, ESC_REG[c])
        if ck not in d.celdas:
            continue
        bases = d.bases_disenio(ck, "v2reg")
        k, det = 0, []
        for b in bases:
            cs = [d.comp(ck, ("base", "v2reg", b), ("ref", REF_CICLO), t) for t in T]
            ok = all(x["comp"] and equivalente(x["comp"]) for x in cs)
            k += ok
            det.append(f"s{b}: " + " / ".join(txt_ic(x["comp"]["ic"]) if x["comp"] else "falta" for x in cs))
        salida.append(fila_h("H4", "H4", "", "equivalencia ±1 % (descriptiva)", c, "regulares",
                             "V2, cada base", "ciclo mínimo", [], None,
                             f"{k} de {len(bases)} bases a ±1 % del ciclo mínimo en T1 y T2", "; ".join(det)))
    # H0 (descriptiva): controles que reaccionan frente al fijo fino re-ajustado con llegadas aleatorias
    controles = [("ref", "ref_actuado"), ("ref", "ref_actuadoaj"), ("ref", "ref_regla"), ("ref", "ref_mp"),
                 ("ref", "ref_mpc"), ("pub", "entmed"), ("pub", "v2regmed")]
    por_caso = {}
    for brazo in controles:
        k = 0
        for c in CASOS6:
            ck = (c, gt.POI[c])
            if ck not in d.celdas:
                continue
            e = {t: etiqueta_brazo(d, ck, brazo, t) for t in T}
            cit = acuerdo(e["T1"]["texto"], e["T2"]["texto"])
            if palabra(cit) in POSITIVAS:
                k += 1
                por_caso.setdefault(c, []).append(nombre_brazo(brazo))
            salida.append(fila_h("H0", "H0", "", "etiqueta citable (descriptiva)", c, "aleatorias",
                                 nombre_brazo(brazo), "fijo fino", [(t, {"lectura": e[t]["texto"]}) for t in T],
                                 None, f"citable {cit}"))
        salida.append(fila_h("H0", "H0", "", "resumen (descriptiva)", "global", "aleatorias", nombre_brazo(brazo),
                             "fijo fino", [], None, f"MEJORA o FUNCIONA en {k} de 6 casos"))
    lect0 = f"en {len(por_caso)} de 6 casos algún control que reacciona da MEJORA o FUNCIONA"
    salida.append(fila_h("H0", "H0", "", "resumen (descriptiva)", "global", "aleatorias", "algún control", "fijo fino",
                         [], None, lect0, "; ".join(f"{c}: {', '.join(v)}" for c, v in sorted(por_caso.items()))))
    resumen.append(("H0", "¿el desorden abre margen? (descriptiva)", None, lect0))
    # H8a en las bases nuevas 14042 y 16042 (se informa aparte)
    for c in ("c2715", "D"):
        ck = (c, ESC_REG[c])
        if ck not in d.celdas:
            continue
        partes = []
        for t in T:
            cs = {b: d.comp(ck, ("base", "p3obs", b), ("base", "v2reg", b), t) for b in (14042, 16042)}
            partes.append(f"{t}: " + ", ".join(f"s{b} {txt(x['comp']['cambio'])} %" if x["comp"] else f"s{b} falta"
                                               for b, x in cs.items()))
        salida.append(fila_h("H8a", "H8a bases nuevas", "", "descriptiva", c, "regulares", "V2 + observación",
                             "V2", [], None, "; ".join(partes), "solo las bases 14042 y 16042 (B23)"))
    # Perfil de 10 min, mezcla de Lima y arranque lento (§8, A7; descriptivas): etiqueta citable de la V2 de la celda
    # frente a su fijo fino re-ajustado; al lado, el fijo por bloques (perfil) y la V2 aleatoria sin perfil o sin mezcla
    for celda_def, esc, que in ESTOCASTICAS:
        ck = next((k for k in d.celdas if k[1] == esc), (celda_def, esc))
        fam = familia_principal(d.celdas[ck]) if ck in d.celdas else None
        if fam is None:
            salida.append(fila_h("Perfil y mezcla", "descriptiva", "", "etiqueta citable (descriptiva)", ck[0],
                                 "aleatorias", "V2 de la celda", "fijo fino", [], None, "no se pudo correr",
                                 f"no hay evaluaciones de {esc} con su modelo principal", que))
            continue
        brazos = [("ver", fam, None)] + [("pub", t) for t in sorted(d.celdas[ck]["tipos"])
                                         if not t.startswith("ref_") and None in d.celdas[ck]["tipos"][t]]
        for brazo in brazos:
            e = {t: etiqueta_brazo(d, ck, brazo, t) for t in T}
            al_lado = ""
            if "ref_bloques" in d.celdas[ck]["tipos"]:
                eb = {t: etiqueta_brazo(d, ck, brazo, t, ref="ref_bloques", veto=False, con_convergencia=False)
                      for t in T}
                al_lado = f"frente al fijo por bloques: {acuerdo(eb['T1']['texto'], eb['T2']['texto'])}"
            salida.append(fila_h("Perfil y mezcla", "descriptiva", "", "etiqueta citable (descriptiva)", ck[0],
                                 d.celdas[ck]["llegadas"], nombre_brazo(brazo), "fijo fino",
                                 [(t, {"lectura": e[t]["texto"],
                                       "cambio": txt(e[t]["comp"]["cambio"]) if e[t]["comp"] else "",
                                       "ic": txt_ic(e[t]["comp"]["ic"]) if e[t]["comp"] else ""}) for t in T],
                                 None, f"citable {acuerdo(e['T1']['texto'], e['T2']['texto'])}", al_lado, que))
    return salida, resumen


# ---------------- Analisis: numero unico, comparaciones y medianas ----------------

def tabla_numero(d, filas_celdas):
    """Numero unico (§7): media geometrica sobre P1-P6 (con P6, no P6e) del cociente modelo citado / fijo fino, por
    tanda y tipo de llegadas; al lado, frente al fijo entregado y, si el citado no es V2 en todas, la de V2.
    [AMB-17] (fijada el 05.11) Requiere los seis casos; usa los datos aunque la etiqueta sea PENDIENTE por convergencia,
    y entonces dice "provisional en [casos]"."""
    por_ck = {(f["celda"], f["escenario"]): f for f in filas_celdas}
    filas = []
    for lleg, esc_de in (("regulares", gt.CASOS), ("aleatorias", gt.POI)):
        cks = [(c, esc_de[c]) for c in CASOS6]
        hay_promovido = any(por_ck.get(ck, {}).get("promovido") == "sí" for ck in cks)
        provisionales = {campo: [ck[0] for ck in cks if provisional(por_ck.get(ck, {}).get(columna))]
                         for campo, columna in (("_brazo_citado", "etiqueta_citable"),
                                                ("_brazo_v2", "etiqueta_v2_citable"))}
        variantes = [("modelo citado", "_brazo_citado", REF_FINO), ("modelo citado", "_brazo_citado", REF_ENTREGADO)]
        if hay_promovido:
            variantes.append(("IPPO con mensajes corregido", "_brazo_v2", REF_FINO))
        for quien, campo, ref in variantes:
            for t in T:
                series, faltan = [], []
                for ck in cks:
                    brazo = por_ck.get(ck, {}).get(campo)
                    if brazo is None:
                        faltan.append(f"{ck[0]} (sin modelo citado)")
                        continue
                    c = d.comp(ck, brazo, ("ref", ref), t)
                    if c["motivo"]:
                        faltan.append(f"{ck[0]} ({c['motivo']})")
                        continue
                    s = sorted(c["a"])
                    series.append((np.array([c["a"][k] for k in s]), np.array([c["b"][k] for k in s])))
                fila = {"llegadas": lleg, "tanda": t, "modelo": quien, "referencia": nombre(ref)}
                if faltan:
                    fila.update({"cambio": "", "ic": "", "nota": "PENDIENTE: " + "; ".join(faltan)})
                else:
                    dd, lo, hi = numero_unico(series)
                    prov = provisionales[campo]
                    fila.update({"cambio": txt(dd), "ic": txt_ic((lo, hi)),
                                 "nota": f"provisional en {', '.join(prov)}" if prov else ""})
                filas.append(fila)
    return filas


def fila_comparacion(ck, lleg, t, brazo, ref, metrica, c, etiqueta_txt=""):
    comp = c.get("comp")
    fila = {"celda": ck[0], "escenario": ck[1], "llegadas": lleg, "tanda": t, "brazo": nombre_brazo(brazo),
            "clave": clave_brazo(brazo), "referencia": nombre(ref) if not isinstance(ref, tuple) else nombre_brazo(ref),
            "metrica": metrica, "etiqueta": etiqueta_txt, "nota": c.get("motivo") or ""}
    if comp:
        fila.update({"n": comp["n"], "media_brazo": txt(statistics.mean(c["a"][s] for s in c["a"]), 3),
                     "media_ref": txt(statistics.mean(c["b"][s] for s in c["b"]), 3), "cambio": txt(comp["cambio"]),
                     "ic": txt_ic(comp["ic"]), "p": txt_p(comp["p"]), "borde_ic": "sí" if comp["borde"] else "no"})
    return fila


def comparaciones(d, filas_celdas):
    """veredicto3_comparaciones.csv: cada brazo de cada celda frente al fijo fino (con su etiqueta), el modelo citado y
    V2 frente a cada referencia, las secundarias del modelo citado (§4: timeLoss, espera para entrar, no insertados,
    cambios de fase y, en los corredores, el retraso por media hora) y las medianas de P6 (§4, [AMB-15])."""
    por_ck = {(f["celda"], f["escenario"]): f for f in filas_celdas}
    filas = []
    for ck in d.orden():
        cel = d.celdas[ck]
        lleg = cel["llegadas"]
        tipos = cel["tipos"]
        brazos = [("ref", x) for x in sorted(tipos) if x.startswith("ref_") and x != REF_FINO]
        brazos += [("pub", x) for x in sorted(tipos) if not x.startswith("ref_") and None in tipos[x]]
        for fam in sorted(x for x in tipos if any(b is not None for b in tipos[x])):
            brazos.append(("ver", fam, None))
            brazos += [("base", fam, b) for b in sorted(b for b in tipos[fam] if b is not None)]
        for brazo in brazos:
            for t in T:
                e = etiqueta_brazo(d, ck, brazo, t)
                c = d.comp(ck, brazo, ("ref", REF_FINO), t)
                filas.append(fila_comparacion(ck, lleg, t, brazo, REF_FINO, METRICA, c, e["texto"]))
        fc = por_ck.get(ck)
        if not fc:
            continue
        for papel in ("_brazo_citado", "_brazo_v2"):
            brazo = fc.get(papel)
            if brazo is None or (papel == "_brazo_v2" and brazo == fc.get("_brazo_citado")):
                continue
            al_lado = fc["_al_lado"] if papel == "_brazo_citado" else referencias_al_lado(d, ck, brazo)
            for ref, x in al_lado.items():
                for t in T:
                    filas.append(fila_comparacion(ck, lleg, t, brazo, ref, METRICA, d.comp(ck, brazo, ("ref", ref), t),
                                                  x[t]["texto"]))
        cit = fc.get("_brazo_citado")
        if cit is None:
            continue
        metricas = list(SECUNDARIAS) + (list(POR_PERIODO) if "corredor" in ck[1] else [])
        for m in metricas:
            for t in T:
                filas.append(fila_comparacion(ck, lleg, t, cit, REF_FINO, m, d.comp(ck, cit, ("ref", REF_FINO), t, m)))
        if "corredor" in ck[1]:                 # no insertados por periodo, aparte (§4)
            for t in T:
                for brazo in (cit, ("ref", REF_FINO)):
                    s = d.serie(ck, brazo, t)
                    if s[3]:
                        continue
                    n1 = statistics.mean(float(r.get("no_insertados_p1") or 0) for r in s[1].values())
                    n2 = statistics.mean(float(r.get("no_insertados_p2") or 0) for r in s[1].values())
                    filas.append({"celda": ck[0], "escenario": ck[1], "llegadas": lleg, "tanda": t,
                                  "brazo": nombre_brazo(brazo), "clave": clave_brazo(brazo), "referencia": "",
                                  "metrica": "no insertados por periodo (media por semilla)",
                                  "media_brazo": f"{n1:.2f} / {n2:.2f}", "nota": "periodo 1 / periodo 2"})
    filas += medianas(d, por_ck)
    return filas


def medianas(d, por_ck):
    """P6 con llegadas aleatorias: mediana del retraso total y proporcion de episodios con retraso > 1.3 veces la
    mediana del fijo fino. P6 regular: mediana del fijo fino y semillas trabadas (> 1.10 veces su mediana)."""
    filas = []
    ck = ("P6", gt.POI["P6"])
    if ck in d.celdas:
        tipos = d.celdas[ck]["tipos"]
        brazos = [("ref", x) for x in sorted(tipos) if x.startswith("ref_")]
        brazos += [("pub", x) for x in sorted(tipos) if not x.startswith("ref_") and None in tipos[x]]
        brazos += [("ver", fam, None) for fam in sorted(x for x in tipos if any(b is not None for b in tipos[x]))]
        for t in T:
            f = d.serie(ck, ("ref", REF_FINO), t)
            if f[3]:
                continue
            med_f = statistics.median(f[0].values())
            for brazo in brazos:
                s = d.serie(ck, brazo, t)
                if s[3]:
                    continue
                malos = sum(1 for v in s[0].values() if v > MALO_P6A * med_f)
                filas.append({"celda": ck[0], "escenario": ck[1], "llegadas": "aleatorias", "tanda": t,
                              "brazo": nombre_brazo(brazo), "clave": clave_brazo(brazo), "referencia": "fijo fino",
                              "metrica": "mediana del retraso total", "n": len(s[0]),
                              "media_brazo": txt(statistics.median(s[0].values()), 3), "media_ref": txt(med_f, 3),
                              "nota": f"episodios con retraso > {MALO_P6A} x la mediana del fijo fino: {malos} de "
                                      f"{len(s[0])} ({100 * malos / len(s[0]):.1f} %)"})
    ck = ("P6", gt.CASOS["P6"])
    if ck in d.celdas:
        for t in T:
            f = d.serie(ck, ("ref", REF_FINO), t)
            if f[3]:
                continue
            med = statistics.median(f[0].values())
            trabadas = sum(1 for v in f[0].values() if v > TRABA_P6 * med)
            filas.append({"celda": ck[0], "escenario": ck[1], "llegadas": "regulares", "tanda": t,
                          "brazo": "fijo fino", "clave": REF_FINO, "referencia": "", "n": len(f[0]),
                          "metrica": "mediana del retraso total", "media_brazo": txt(med, 3),
                          "nota": f"semillas trabadas (> {TRABA_P6} x su mediana): {trabadas} de {len(f[0])}"})
    return filas


def revisar_generados(d):
    """§7: en cada celda y tanda, TODOS los brazos generan los mismos vehiculos en cada semilla (no solo los pares que
    entran a una etiqueta). Devuelve avisos; las comparaciones afectadas ya quedan con su motivo (Datos.comp).
    ERROR si dos CSV de una misma celda y tanda dicen el mismo brazo (un CSV copiado bajo otro nombre)."""
    avisos = []
    for ck in d.orden():
        por_tanda, brazos = {}, {}
        for tipo, por in d.celdas[ck]["tipos"].items():
            for ents in por.values():
                for tf, e in ents.items():
                    leido = d.filas_csv(e)
                    if leido:
                        por_tanda.setdefault(tf, {})[e["csv"]] = leido[0]
                        otro = brazos.setdefault((tf, leido[1]), e["csv"])
                        if otro != e["csv"]:
                            raise ErrorVeredicto(f"{e['csv']} y {otro} dicen el mismo brazo ({leido[1]}) en la "
                                                 f"misma celda y tanda")
        for tf, csvs in sorted(por_tanda.items()):
            malas = generados_iguales(csvs) if len(csvs) > 1 else []
            if malas:
                s, gen = malas[0]
                distintos = sorted(c for c, g in gen.items() if g != statistics.mode(gen.values()))
                avisos.append(f"{ck[0]} ({ck[1]}, {tf}): los brazos no generan los mismos vehículos en {len(malas)} "
                              f"semilla{'s' if len(malas) > 1 else ''} (la primera, {s}; distinto: "
                              f"{', '.join(distintos[:3])})")
    return avisos


def versiones_diag(filas_celdas):
    """§6: el corredor se reentrena; la V2 de la Seccion 5.5.1 queda como esta y, si la version evaluada cambia, se
    muestran las dos. Lee plan2/diag_corredor/resultados.csv (solo lectura)."""
    ruta = os.path.join(PLAN2, "diag_corredor", "resultados.csv")
    if not os.path.exists(ruta):
        return []
    with open(ruta, newline="", encoding="utf-8") as f:
        diag = {r["escenario"]: r["base_evaluada"] for r in csv.DictReader(f)
                if r["control"] == "v2" and r["semillas"] == "1001-1030"}
    lineas = []
    for f in filas_celdas:
        antes = diag.get(f["escenario"]) if f["llegadas"] == "regulares" else None
        if antes is not None and str(f["version_evaluada"]) != antes:
            lineas.append(f"{f['celda']}: la versión evaluada de la V2 del diagnóstico (Sección 5.5.1) es la base "
                          f"{antes}; la de ahora es la base {f['version_evaluada']} (se muestran las dos)")
    return lineas


def analizar(d):
    avisos_generados = revisar_generados(d)     # antes que nada: tambien comprueba que los brazos son distintos
    filas_celdas = [fila_celda(d, ck) for ck in d.orden()]
    hip, resumen = hipotesis(d, filas_celdas)
    return {"celdas": filas_celdas, "bases": tabla_bases(d), "hipotesis": hip, "resumen": resumen,
            "numero": tabla_numero(d, filas_celdas), "comparaciones": comparaciones(d, filas_celdas),
            "no_insertados": [x for ck in d.orden() for x in filas_no_insertados(d, ck)],
            "avisos": list(d.avisos) + avisos_generados, "diag": versiones_diag(filas_celdas)}


# ---------------- Salidas ----------------

CAMPOS_CELDAS = ["celda", "escenario", "llegadas", "modelo_citado", "clave_citado", "promovido", "base_citado",
                 "etiqueta_T1", "etiqueta_T2", "etiqueta_citable", "cambio_T1", "ic_T1", "p_T1", "borde_ic_T1",
                 "cambio_T2", "ic_T2", "p_T2", "borde_ic_T2", "repite_T1", "repite_T2", "convergio",
                 "prob_pendiente_ruido", "mejor_base", "etiqueta_mejor_T1", "etiqueta_mejor_T2",
                 "etiqueta_mejor_citable", "version_evaluada", "etiqueta_v2_T1", "etiqueta_v2_T2",
                 "etiqueta_v2_citable", "etiqueta_v2_mejor_citable", "igual_ciclo_minimo", "lecturas", "motivo"]
CAMPOS_BASES = ["celda", "escenario", "llegadas", "familia", "nombre", "base", "estado", "version_evaluada",
                "mejor_base", "val_elegido", "ep_elegido", "episodios", "convergio", "meseta", "estabilidad",
                "dist_mediana_s", "dist_mediana_pct", "min_repetido", "dos_mejores_seguidos", "n_validaciones",
                "semillas_validacion", "criterio", "serie", "escenario_entrenamiento", "politica"]
CAMPOS_HIP = (["id", "familia", "n_familia", "prueba", "que", "caso", "llegadas", "a", "b"]
              + [f"{c}_{k}" for k in ("1", "2") for c in ("tanda", "semillas", "cambio", "ic", "p", "p_ajustado",
                                                        "lectura", "sentido")]
              + ["pasa", "lectura", "nota"])
CAMPOS_NOINS = ["celda", "escenario", "llegadas", "tanda", "tipo", "base", "nombre", "brazo", "semillas",
                "semillas_con_no_insertados", "vehiculos_no_insertados"]
CAMPOS_COMP = ["celda", "escenario", "llegadas", "tanda", "brazo", "clave", "referencia", "metrica", "n",
               "media_brazo", "media_ref", "cambio", "ic", "p", "borde_ic", "etiqueta", "nota"]


def corto(texto):
    """Etiqueta corta para la tabla simple (sin el motivo largo de PENDIENTE)."""
    p = palabra(texto)
    if p == "PENDIENTE":
        q = provisional(texto)
        return f"PENDIENTE ({q})" if q else "PENDIENTE"
    return texto


def cambio_md(fila, t):
    if not fila.get(f"cambio_{t}"):
        return "—"
    ic = fila[f"ic_{t}"].strip("[]").split(",")
    marca = " †" if fila.get(f"borde_ic_{t}") == "sí" else ""
    return f"{float(fila[f'cambio_{t}']):+.1f} % [{float(ic[0]):.1f}, {float(ic[1]):.1f}]{marca}"


def valor_numero(f):
    if not f or not f["cambio"]:
        return "PENDIENTE" + (f" ({f['nota'][len('PENDIENTE: '):]})" if f and f["nota"] else "")
    lo, hi = (float(x) for x in f["ic"].strip("[]").split(","))
    return f"{float(f['cambio']):+.1f} % [{lo:.1f}, {hi:.1f}]"


def texto_md(res, titulo_extra=""):
    """veredicto3.md: respuesta corta, la tabla simple del anexo, hipotesis, lecturas obligadas y avisos."""
    L = [f"# Veredicto del bloque nuevo (plan 3){titulo_extra}", "",
         "Generado por `veredicto3.py` con las reglas de `PRERREGISTRO.md` (§7-§12). No editar a mano.", ""]
    L += ["## Respuesta corta", ""]
    num = {(f["llegadas"], f["modelo"], f["referencia"], f["tanda"]): f for f in res["numero"]}
    for lleg in ("regulares", "aleatorias"):            # la frase de §17: siempre las dos tandas, por separado
        fino = [valor_numero(num.get((lleg, "modelo citado", "fijo fino", t))) for t in T]
        ent = [valor_numero(num.get((lleg, "modelo citado", "fijo entregado", t))) for t in T]
        linea = (f"- Número único, llegadas {lleg} (P1-P6, con P6): frente al plan fijo ajustado al segundo, {fino[0]} "
                 f"en la tanda 1 y {fino[1]} en la tanda 2 (frente al plan fijo entregado: {ent[0]} y {ent[1]}).")
        if (lleg, "IPPO con mensajes corregido", "fijo fino", "T1") in num:
            v2 = [valor_numero(num.get((lleg, "IPPO con mensajes corregido", "fijo fino", t))) for t in T]
            linea += f" IPPO con mensajes corregido: {v2[0]} y {v2[1]}."
        notas = sorted({f["nota"] for f in res["numero"] if f["llegadas"] == lleg and f["cambio"] and f["nota"]})
        if notas:                               # [AMB-17] "provisional en [casos]", una sola vez por linea
            linea += " Cifra " + "; ".join(notas) + "."
        L.append(linea)
    pos = [f"{f['celda']} ({f['llegadas']})" for f in res["celdas"] if palabra(f["etiqueta_citable"]) in POSITIVAS]
    L.append(f"- Casos con etiqueta citable MEJORA o FUNCIONA: {len(pos)} de {len(res['celdas'])}"
             + (f" ({', '.join(pos)})" if pos else ""))
    pasan = [r[0] for r in res["resumen"] if r[2] is True]
    L.append(f"- Hipótesis que pasan (con su regla global o, si se juzgan caso por caso, en al menos un caso): "
             f"{', '.join(pasan) if pasan else 'ninguna'}.")
    L += ["", "## Cómo leer", "",
          "- Etiqueta: la regla de lo entregado frente al fijo fino (FUNCIONA: mejora de 5 % o más, significativa y "
          "sin perder contra el actuado ajustado; MEJORA: mejora significativa; FALLA: empeora; EMPATA: el resto).",
          "- Citable: la que se repite en las dos tandas de semillas. \"Se repite\": cuántos entrenamientos van del "
          "lado de la etiqueta.",
          "- Cambio: retraso total por vehículo frente al fijo fino, con su IC95; † = un extremo del IC a menos de "
          "0.05 puntos del 0.", ""]
    L += ["## Tabla del anexo: etiqueta por caso", "",
          "| Caso | Llegadas | Modelo citado | Tanda 1 | Tanda 2 | Citable | Cambio T1 [IC95] | Cambio T2 [IC95] "
          "| Se repite (T1; T2) | Con la mejor base |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for f in res["celdas"]:
        L.append(f"| {f['celda']} | {f['llegadas']} | {f['modelo_citado']} | {corto(f['etiqueta_T1'])} | "
                 f"{corto(f['etiqueta_T2'])} | {corto(f['etiqueta_citable'])} | {cambio_md(f, 'T1')} | "
                 f"{cambio_md(f, 'T2')} | {f.get('repite_T1') or '—'}; {f.get('repite_T2') or '—'} | "
                 f"{corto(f['etiqueta_mejor_citable'])} |")
    L += ["", "## Hipótesis", "", "| Id | Qué se prueba | Resultado |", "|---|---|---|"]
    for id_, que, pasa, lect in res["resumen"]:
        L.append(f"| {id_} | {que} | {lect} |")
    lect = [(f["celda"], f["llegadas"], f["lecturas"]) for f in res["celdas"] if f["lecturas"]]
    L += ["", "## Lecturas obligadas (§5 y §11)", ""]
    L += [f"- {c} ({ll}): {x}" for c, ll, x in lect] or ["- Ninguna."]
    al_lado = sorted({ref for f in res["celdas"] for ref in f["_al_lado"]})
    if al_lado:
        L += ["", "## Referencias al lado (etiqueta citable del modelo citado frente a cada una)", "",
              "| Caso | Llegadas | " + " | ".join(nombre(r) for r in al_lado) + " |",
              "|---|---|" + "---|" * len(al_lado)]
        for f in res["celdas"]:
            L.append(f"| {f['celda']} | {f['llegadas']} | "
                     + " | ".join(corto(f["_al_lado"][r]["citable"]) if r in f["_al_lado"] else "—" for r in al_lado)
                     + " |")
    pend = [f for f in res["celdas"] if palabra(f["etiqueta_citable"]) == "PENDIENTE"]
    if pend:
        L += ["", "## PENDIENTE", ""]
        for f in pend:
            ruido = (f"; probabilidad de que una política estable no converja por ruido (§6): "
                     f"{f['prob_pendiente_ruido']}" if provisional(f["etiqueta_citable"]) else "")
            L.append(f"- {f['celda']} ({f['llegadas']}): {f['etiqueta_citable']}{ruido}.")
    promo = [f for f in res["celdas"] if f.get("_promocion")]
    if promo:
        L += ["", "## Regla de promoción (§12): validación en 15009-15024 frente a V2", ""]
        for f in promo:
            dec = f["_promocion"]
            cands = [c for c in dec.get("candidatos", []) if c.get("brazo") != (dec.get("v2") or {}).get("brazo")]
            texto = ", ".join(f"{nombre(tipo_de_brazo(c['brazo'], CANDIDATOS_PROMOCION)[0] or c['brazo'])} "
                              f"{c.get('cambio_vs_v2_pct', 0):+.2f} %" for c in cands) or "sin candidatos"
            L.append(f"- {f['celda']} ({f['llegadas']}): {texto}; se cita {f['modelo_citado']}"
                     f"{' (promovido: le gana a V2 por al menos 1 %)' if f['promovido'] == 'sí' else ''}.")
    dejan = [x for x in res.get("no_insertados", []) if x["vehiculos_no_insertados"] > 0]
    L += ["", "## Vehículos sin entrar al cierre (§4)", ""]
    L += [f"- {x['celda']} ({x['llegadas']}, {x['tanda']}): {x['nombre']}: {x['semillas_con_no_insertados']} de "
          f"{x['semillas']} semillas, {x['vehiculos_no_insertados']} vehículos" for x in dejan] or \
        ["- Ningún brazo dejó vehículos sin entrar."]
    if dejan:
        L.append("- Lectura obligada: el retraso total de esos brazos está subestimado y la diferencia con un brazo "
                 "que no los deja es conservadora. Detalle por brazo en veredicto3_no_insertados.csv.")
    caidas = [b for b in res["bases"] if not b.get("estado", "").startswith("publicada")]
    L += ["", "## Entrenamientos caídos o sin publicar", ""]
    L += [f"- {b['escenario']}: {b['nombre']}, base {b['base']}: {b['estado']}" for b in caidas] or ["- Ninguno."]
    L.append("- Relanzamientos, desvíos y enmiendas: en cola/estado.json y en las enmiendas del prerregistro "
             "(§11, §14); veredicto3 no los calcula.")
    if res.get("diag"):
        L += ["", "## V2 del diagnóstico del corredor (§6)", ""] + [f"- {x}." for x in res["diag"]]
    if res["avisos"]:
        L += ["", "## Avisos", ""] + [f"- {a}" for a in res["avisos"]]
    L += ["", "La predicción de §15 del prerregistro va al lado de estos resultados para medir la sorpresa. El detalle "
          "está en veredicto3_celdas.csv, veredicto3_bases.csv, veredicto3_hipotesis.csv, "
          "veredicto3_comparaciones.csv y veredicto3_no_insertados.csv.", ""]
    return "\n".join(L)


def escribir_salidas(res, carpeta, titulo_extra=""):
    rutas = {
        "veredicto3_celdas.csv": texto_csv(res["celdas"], CAMPOS_CELDAS),
        "veredicto3_bases.csv": texto_csv(res["bases"], CAMPOS_BASES),
        "veredicto3_hipotesis.csv": texto_csv(res["hipotesis"] + [
            {"id": "Número único", "familia": "número único", "prueba": "media geométrica (indice_geo)",
             "caso": "P1-P6", "llegadas": f["llegadas"], "a": f["modelo"], "b": f["referencia"], "tanda_1": f["tanda"],
             "cambio_1": f["cambio"], "ic_1": f["ic"], "lectura": f["cambio"] and f"{f['cambio']} %",
             "nota": f["nota"]} for f in res["numero"]], CAMPOS_HIP),
        "veredicto3_comparaciones.csv": texto_csv(res["comparaciones"], CAMPOS_COMP),
        "veredicto3_no_insertados.csv": texto_csv(res["no_insertados"], CAMPOS_NOINS),
        "veredicto3.md": texto_md(res, titulo_extra)}
    for nombre_arch, texto in rutas.items():
        escribir(os.path.join(carpeta, nombre_arch), texto)
    return [os.path.join(carpeta, n) for n in rutas]


# ---------------- Modos ----------------

def es_final(tanda):
    """Tanda de la prueba final reservada: la enmienda que la active la declara con uso 'final' en gt.TANDAS (§13)."""
    return gt.TANDAS.get(tanda, ("",))[0] == "final"


def clave_base(e):
    return (e["celda"], e["escenario"], e["tipo"],
            int(e["base"]) if str(e.get("base", "")).strip() not in ("", "None") else None)


def caidas_declaradas(raiz):
    p = os.path.join(raiz, "cola", "caidas.json")
    if not os.path.exists(p):
        return set()
    datos = leer_json(p)
    lista = datos.get("caidas", []) if isinstance(datos, dict) else datos
    return {(c.get("celda"), c.get("escenario"), c.get("tipo"), int(c["base"])) for c in lista if "base" in c}


def otros_que_se_sellan(raiz):
    """Los archivos de control que deciden el veredicto: el manifiesto esperado, los trabajos, las caidas y la
    promocion. Deben estar en el sello ("otros")."""
    rels = ["cola/manifiesto_esperado.json", "cola/trabajos.jsonl"]
    rels += [r for r in ("cola/caidas.json", "promocion.json") if os.path.exists(os.path.join(raiz, r))]
    rels += sorted(os.path.relpath(p, raiz).replace(os.sep, "/")
                   for p in glob.glob(os.path.join(raiz, "promocion", "*.json")))
    return rels


def comprobar_cierre(raiz):
    """--final se niega sin listo/cierre.ok o si algo de lo sellado en cola/manifiesto_cierre.json cambio. El sello
    (manifiesto.py cierre) es {"csv": {ruta: sha256}, "metas": {...}, "otros": {...}}: todos los CSV del manifiesto
    salvo los de la prueba final (uso 'final') y los de bases caidas declaradas, los metas politica_*.json de lo
    evaluado y los archivos de control (otros_que_se_sellan). Devuelve el sello."""
    if not os.path.exists(os.path.join(raiz, "listo", "cierre.ok")):
        raise ErrorVeredicto("falta listo/cierre.ok: los resultados decisivos siguen a ciegas (§14); no se corre")
    ruta = os.path.join(raiz, "cola", "manifiesto_cierre.json")
    if not os.path.exists(ruta):
        raise ErrorVeredicto("falta cola/manifiesto_cierre.json (python manifiesto.py cierre); no se corre")
    sello = leer_json(ruta)
    if not isinstance(sello, dict) or not {"csv", "metas", "otros"} <= set(sello):
        raise ErrorVeredicto("cola/manifiesto_cierre.json no tiene las claves csv, metas y otros; no se corre")
    caidas = caidas_declaradas(raiz)
    esperado = leer_json(os.path.join(raiz, "cola", "manifiesto_esperado.json"))
    csvs = {e["csv"] for e in esperado if not es_final(e["tanda"]) and clave_base(e) not in caidas}
    problemas = []
    if set(sello["csv"]) != csvs:
        faltan, sobran = sorted(csvs - set(sello["csv"])), sorted(set(sello["csv"]) - csvs)
        problemas.append(f"el sello y el manifiesto no listan los mismos CSV (sin sellar: {faltan[:3]}; de más: "
                         f"{sobran[:3]})")
    for grupo, rels in (("csv", sorted(csvs & set(sello["csv"]))), ("metas", sorted(sello["metas"])),
                        ("otros", sorted(sello["otros"]))):
        for rel in rels:
            p = os.path.join(raiz, rel)
            if not os.path.exists(p):
                problemas.append(f"falta {rel}")
            elif sha256(p) != sello[grupo][rel]:
                problemas.append(f"{rel} cambió después del cierre (sha256 distinto)")
    problemas += [f"{rel} no está sellado (otros)" for rel in otros_que_se_sellan(raiz) if rel not in sello["otros"]]
    if problemas:
        raise ErrorVeredicto("lo sellado al cierre no coincide; no se corre: " + "; ".join(problemas[:5])
                             + (f" (y {len(problemas) - 5} más)" if len(problemas) > 5 else ""))
    return sello


def historia_ciego(raiz):
    """Las versiones commiteadas de cola/manifiesto_ciego.json (p3_noche, cada manana: {csv: {sha256, bytes, filas,
    semillas}}), de la mas vieja a la mas nueva: [(commit, manifiesto)]. Solo lee git (log y show)."""
    rc, top = protecciones.git("--no-optional-locks", "rev-parse", "--show-toplevel", cwd=raiz)
    if rc != 0:
        raise ErrorVeredicto("no se pudo leer la historia de git de cola/manifiesto_ciego.json")
    top = top.strip()
    rel = os.path.relpath(os.path.join(raiz, "cola", "manifiesto_ciego.json"), top).replace(os.sep, "/")
    rc, log = protecciones.git("--no-optional-locks", "log", "--reverse", "--format=%H", "--", rel, cwd=top)
    if rc != 0:
        raise ErrorVeredicto("no se pudo leer la historia de git de cola/manifiesto_ciego.json")
    versiones = []
    for h in log.split():
        rc, texto = protecciones.git("--no-optional-locks", "show", f"{h}:{rel}", cwd=top)
        if rc == 0:                             # un commit que borro el archivo no trae manifiesto
            versiones.append((h, json.loads(texto)))
    return versiones


def comprobar_ciego(raiz, sello):
    """Segunda barrera del a ciegas (§14, A5 #8): cada CSV sellado de ciego/ aparece en algun manifiesto de manana
    versionado, su sha256 no cambio de una manana a otra y el del cierre es el de la primera manana en que aparecio."""
    versiones = historia_ciego(raiz)
    if not versiones:
        raise ErrorVeredicto("no hay ninguna versión commiteada de cola/manifiesto_ciego.json (§14); no se corre")
    primero, problemas = {}, []
    for h, man in versiones:
        for rel, info in man.items():
            if rel in primero and info.get("sha256") != primero[rel][1]:
                problemas.append(f"{rel}: su sha256 cambió en el manifiesto de la mañana {h[:10]}")
            primero.setdefault(rel, (h, info.get("sha256")))
    for rel, h_sello in sorted(sello["csv"].items()):
        if not rel.startswith("ciego/"):
            continue
        if rel not in primero:
            problemas.append(f"{rel} no aparece en ningún manifiesto de la mañana")
        elif primero[rel][1] != h_sello:
            problemas.append(f"{rel}: el sha256 del cierre no es el de la primera mañana ({primero[rel][0][:10]})")
    if problemas:
        raise ErrorVeredicto("los CSV de ciego/ no son los de cada mañana (§14); no se corre: "
                             + "; ".join(problemas[:5])
                             + (f" (y {len(problemas) - 5} más)" if len(problemas) > 5 else ""))


def comprobar_semillas(manifiesto, texto_prerregistro=None):
    """Cada CSV del manifiesto tiene las semillas de su tanda (generar_trabajos3.TANDAS) y caen en el bloque de su uso
    en la tabla JSON del prerregistro (§3)."""
    tabla = protecciones.tabla_prerregistro(texto_prerregistro)["semillas"]
    problemas = []
    for e in manifiesto:
        if e["tanda"] not in gt.TANDAS:
            problemas.append(f"{e['csv']}: tanda desconocida {e['tanda']}")
            continue
        uso, semillas = gt.TANDAS[e["tanda"]]
        valores = rango(e["semillas"])
        if valores != rango(semillas):
            problemas.append(f"{e['csv']}: semillas {e['semillas']} y la tanda {e['tanda']} es {semillas}")
        elif not all(protecciones.en_tramos(s, tabla[uso]) for s in valores):
            problemas.append(f"{e['csv']}: semillas fuera del bloque '{uso}' del prerregistro")
    if problemas:
        raise ErrorVeredicto("semillas del manifiesto distintas de las del prerregistro: " + "; ".join(problemas[:5]))


def correr_final(raiz=PLAN3, exigir_semillas=True, carpeta=None):
    """--final: sello del cierre, historia de los manifiestos de la manana, datos en modo estricto (con el sello),
    semillas del prerregistro; recien entonces el analisis y las salidas."""
    sello = comprobar_cierre(raiz)
    comprobar_ciego(raiz, sello)
    d = Datos(raiz, estricto=True, sello=sello)
    if exigir_semillas:
        comprobar_semillas(d.manifiesto)
    res = analizar(d)
    rutas = escribir_salidas(res, carpeta or os.path.join(raiz, "salidas"))
    return res, rutas


def correr_prueba_final(lista, raiz=PLAN3, exigir_semillas=True):
    """Prueba final reservada (§13): una sola vez, con la lista exacta de la enmienda. listo/holdout.ok debe contener
    el sha256 de la lista. Antes de cerrar el candado se valida TODO: cada CSV en una tanda de uso 'final' con el bloque
    completo de su tipo de llegadas (11001-11030 regulares, 12001-12100 aleatorias; tabla JSON de §3), la metrica en
    cada semilla, las mismas semillas y los mismos vehiculos en los dos brazos (§7), y la comparacion misma. El
    candado listo/holdout.candado se crea en exclusiva (si ya existe, no corre) con el sha256 de la lista, de
    holdout.ok, de cada CSV leido y de la salida. Lista: {"comparaciones": [{"celda", "escenario", "tanda",
    "a": {"tipo", "base"?}, "b": {"tipo", "base"?}}]}. Lo que se cite de aqui dice 'elegido despues de ver T1 y T2;
    una tanda'."""
    if not os.path.exists(os.path.join(raiz, "listo", "cierre.ok")):
        raise ErrorVeredicto("la prueba final va después del cierre: falta listo/cierre.ok")
    ok = os.path.join(raiz, "listo", "holdout.ok")
    if not os.path.exists(ok):
        raise ErrorVeredicto("falta listo/holdout.ok (lo crea Fabian con la enmienda, §13)")
    h_lista = sha256(lista)
    with open(ok, encoding="utf-8") as f:
        if h_lista not in f.read():
            raise ErrorVeredicto("listo/holdout.ok no tiene el sha256 de la lista: no es la lista de la enmienda")
    candado = os.path.join(raiz, "listo", "holdout.candado")
    if os.path.exists(candado):
        raise ErrorVeredicto("la prueba final ya corrió (listo/holdout.candado): no corre una segunda vez")
    d = Datos(raiz)
    bloques = protecciones.tabla_prerregistro()["semillas"]["final"]      # [regulares, aleatorias] (§3)
    bloque = {"regulares": list(range(bloques[0][0], bloques[0][1] + 1)),
              "aleatorias": list(range(bloques[1][0], bloques[1][1] + 1))}
    filas, leidos = [], {}
    for item in leer_json(lista)["comparaciones"]:
        ck = (item["celda"], item["escenario"])
        lleg = (d.celdas[ck]["llegadas"] if ck in d.celdas
                else "aleatorias" if ck[1].startswith(("poi_", "per_", "mix")) else "regulares")
        lados = []
        for x in (item["a"], item["b"]):
            e = d.todas.get((ck[0], ck[1], x["tipo"], x.get("base"), item["tanda"]))
            if e is None:
                raise ErrorVeredicto(f"prueba final: no hay CSV de {x} en {ck} ({item['tanda']})")
            if exigir_semillas and not es_final(e["tanda"]):
                raise ErrorVeredicto(f"prueba final: la tanda {e['tanda']} no es de uso 'final' (generar_trabajos3)")
            if exigir_semillas and rango(e["semillas"]) != bloque[lleg]:
                raise ErrorVeredicto(f"prueba final: {e['csv']} no usa el bloque completo de llegadas {lleg} (§3, §13)")
            leido = d.filas_csv(e)
            if leido is None:
                raise ErrorVeredicto(f"prueba final: falta {e['csv']}")
            valores, filas_csv = Datos._valores(leido[0], METRICA, ck, ("pub", x["tipo"]))
            leidos[e["csv"]] = sha256(os.path.join(raiz, e["csv"]))
            lados.append((e, valores, filas_csv))
        (ea, va, fa), (eb, vb, fb) = lados
        if set(rango(ea["semillas"])) != set(rango(eb["semillas"])):
            raise ErrorVeredicto(f"prueba final: semillas distintas en {ck}")
        malas = generados_iguales({"a": fa, "b": fb})
        if malas:
            raise ErrorVeredicto(f"prueba final: {ea['csv']} y {eb['csv']} no generan los mismos vehículos en "
                                 f"{len(malas)} semilla{'s' if len(malas) > 1 else ''} (§7)")
        comp = comparar(va, vb, set(rango(ea["semillas"])))
        if comp is None:
            raise ErrorVeredicto(f"prueba final: sin cambio en {ck} (la media de la referencia es 0)")
        filas.append({"celda": ck[0], "escenario": ck[1], "tanda": item["tanda"], "brazo": json.dumps(item["a"]),
                      "referencia": json.dumps(item["b"]), "metrica": METRICA, "n": comp["n"],
                      "cambio": txt(comp["cambio"]), "ic": txt_ic(comp["ic"]), "p": txt_p(comp["p"]),
                      "nota": "elegido después de ver T1 y T2; una tanda (§13)"})
    texto = texto_csv(filas, ["celda", "escenario", "tanda", "brazo", "referencia", "metrica", "n", "cambio", "ic",
                              "p", "nota"])
    salida = "salidas/veredicto3_prueba_final.csv"
    registro = {"lista": os.path.basename(lista), "sha256_lista": h_lista, "sha256_holdout_ok": sha256(ok),
                "csv": leidos, "salida": {salida: hashlib.sha256(texto.encode("utf-8")).hexdigest()}}
    real = dentro_de_plan3(candado)
    os.makedirs(os.path.dirname(real), exist_ok=True)
    try:
        with open(real, "x", encoding="utf-8") as f:                  # creacion exclusiva: una sola corrida
            f.write(json.dumps(registro, indent=1) + "\n")
    except FileExistsError:
        raise ErrorVeredicto("la prueba final ya corrió (listo/holdout.candado): no corre una segunda vez")
    escribir(os.path.join(raiz, salida), texto)
    return filas


# ---------------- Pruebas (--probar) ----------------

TMP_VER = os.path.join(PLAN3, "tmp_ver")
SALIDA_PRUEBAS = os.path.join(PLAN3, "pruebas", "ver")
PLAN2 = os.path.join(RAIZ, "plan2")
VAL8 = [999, 1999, 2999, 3999, 4999, 7999, 8999, 9999]
# semillas de humo (prerregistro §3) para las tandas sinteticas: nunca las decisivas
SEMILLAS_PRUEBA = {"t1r": "424301-424310", "t2r": "424311-424320", "h1t1": "424321-424330", "h1t2": "424331-424340",
                   "t1a": "424341-424350", "t2a": "424351-424360", "puente": "424301-424310",
                   "promo": "424301-424316"}
VAL_BASE = {42: 30.0, 2042: 29.0, 4042: 31.0, 14042: 28.0, 16042: 32.0}      # mediana de 5 y de 3: 42


def unif(*claves):
    """Numero en [-0.5, 0.5) fijo para unas claves (crc32): ruido sintetico reproducible."""
    return (zlib.crc32("|".join(map(str, claves)).encode()) % 100000) / 100000 - 0.5


def fabricar(semillas, efecto, nivel=30.0, ruido=0.3, alterno=0.0, clave="x", esc="e"):
    """{semilla: retraso sintetico} = nivel x dificultad(esc, semilla) x (1 + (efecto + ruido + alterno) / 100);
    la dificultad es comun a todos los brazos de un escenario (numeros aleatorios comunes)."""
    salida = {}
    for k, s in enumerate(semillas):
        dif = 1 + 0.1 * unif("dif", esc, s)
        alt = alterno if k % 2 == 0 else -alterno
        salida[s] = nivel * dif * (1 + (efecto + 2 * ruido * unif(clave, s) + alt) / 100)
    return salida


# --- Mundo sintetico: el manifiesto real del generador con semillas de humo, CSV y metas fabricados ---

V2_REG = {"P1": (-8, -8), "P2": (-8, -3), "P3": (-3, "alt"), "P4": (4, "alt"), "P5": (-3, 4), "D": (-8, -8),
          "c905": ("alt", "alt"), "c1358": (4, 4)}
DELTA = {"v2loc": 2, "c0": 1, "c0med": 1, "entmed": 1.5, "v2viejamed": 0.5, "v2poimed": 3, "p3obs": -2, "p3m7": 0.5,
         "p3reloj2": -2, "p3completo": -1.5, "p3e400": -1, "p3sd": 1, "p3se": 0.5, "p3ent": 0, "p3m7norm": 0.2,
         "p3m7forz": 0.2, "p3m7msg": 0.2, "p3piso200reg": 0, "p3e400c20reg": -0.5, "v2reg3med": 0,
         "v2poiloc": 2, "p3obspoi": 1, "p3reloj2poi": -2, "p3completopoi": "alt", "p3e400poi": -1,
         "p3piso200poi": 0, "p3e400c20poi": -0.5}
REF_EFECTO = {"ref_fino": 0, "ref_actuadoaj": 3, "ref_actuado": 5, "ref_fijo": 2, "ref_trivial": 10, "ref_fino5": 1,
              "ref_franja": -1, "ref_bloques": -1.5, "ref_regla": 20, "ref_mp": 15, "ref_mpc": 12}
EXTRAS_REF = ("ref_fino", "ref_actuadoaj", "ref_fino5", "ref_franja", "ref_regla", "ref_mp", "ref_mpc")
NO_CONVERGE = {("dem_corredor_t2715", "p3v2reg", 42), ("poi_red", "p3v2poi", 42)}
# bases caidas declaradas en el mundo: las dos nuevas de V2 aleatoria en P4 (n sigue siendo 5: 3 de 5 no alcanza)
CAIDAS_MUNDO = {("P4", "poi_red_alta", "v2poi", 14042), ("P4", "poi_red_alta", "v2poi", 16042)}
NO_INSERTADOS_MUNDO = {("P2", "poi_corredor_alta", "ref_fino", "t1a"): {1: 40, 4: 40, 7: 40}}


def efecto_mundo(celda, esc, lleg, tl, tipo, base):
    """(efecto %, alterno, clave del ruido) de un brazo del mundo sintetico (ver la tabla de las pruebas)."""
    if tipo.startswith("ref_"):
        ef = REF_EFECTO.get(tipo, 0)
        if celda == "D" and tipo == REF_VETO:
            ef = -12                            # el actuado ajustado le gana a V2: veto de FUNCIONA
        if celda == "m3620" and tipo == REF_CICLO:
            ef = -3                             # V2 da lo mismo que el ciclo minimo
        return ef, 0.0, (esc, tipo)
    if lleg == "aleatorias":
        v2 = -6.0
        if tipo in ("v2regmed", "c0poimed", "entmed", "v2reg3poi"):
            return {"v2regmed": -2, "c0poimed": -3, "entmed": -1, "v2reg3poi": -2.5}[tipo], 0.0, (esc, tipo)
    else:
        par = V2_REG.get(celda, (-3, -3))
        v2 = par[0] if tl == "T1" else par[1]
    alt = 0.0
    if v2 == "alt":
        v2, alt = 0.0, 1.0
    if tipo.startswith("promo_"):               # promocion: en P1 regular la observacion nueva le gana a V2 por 3 %
        et = tipo[len("promo_"):]
        ef = v2 if et in ("p3v2reg", "p3v2poi") else (v2 - 3 if (celda, esc, et) == ("P1", "corredor", "p3obs")
                                                       else v2 + 0.3)
        return ef, 0.0, (esc, "promo", et)
    m = re.fullmatch(r"a3(colas0|msg0)_(.+)", tipo)
    if m:                                       # a3: la politica perturbada pierde frente a la misma sin perturbar
        fam = A3_VERSION[m.group(2)][0]
        base_ef = v2 + (DELTA.get(fam, 0) if fam not in ("v2reg", "v2poi") else 0)
        return base_ef + (5 if m.group(1) == "colas0" else 2), 0.0, (esc, tipo)
    b = 42 if base is None else base
    if lleg == "regulares" and ((celda == "P6" and b == 4042) or (celda == "P6e" and b in (4042, 16042))):
        v2 = 2.0                                # bases en contra del sentido (H3: 1 de 5; H3e: 2 de 5)
    if tipo in ("v2reg", "v2poi", "v2reg3med", "v2per", "v2mix"):
        if celda == "m3620" and lleg == "regulares":
            return REF_EFECTO["ref_trivial"] - 13, 0.0, (esc, REF_CICLO)         # = ciclo minimo (efecto -3)
        return v2, alt, (esc, "v2", b)
    delta = DELTA.get(tipo, 0)
    if tipo in ("c0", "c0med") and celda in ("P4", "m6525"):
        delta = 3                               # H2: V2 < C0
    if tipo in ("c0", "c0med") and celda == "P5" and tl == "T2":
        return -2.0, 0.0, (esc, "c0", b)         # H1 en P5: V2 (+4 %) es peor que C0 (-2 %) en T2
    if tipo == "v2loc" and celda == "P6" and b == 4042:
        return 0.0, 0.0, (esc, tipo, b)          # H7r en P6: el sentido falla (2 de 3)
    if tipo == "p3m7" and celda == "P2":
        delta = 5                               # H12 en P2: es peor
    if delta == "alt":
        return v2, 1.0, (esc, tipo, b)
    return v2 + delta, 0.0, (esc, tipo.replace("med", ""), b)


def serie_sintetica(val, episodios, converge=True, n_semillas=16):
    filas = []
    for ep in range(10, episodios + 1, 10):
        media = val + (2.0 * np.exp(-ep / 25.0) if converge else 0.06 * (episodios - ep))
        media = round(float(media), 3)
        filas.append([ep] + [round(media + 0.1 * (i - (n_semillas - 1) / 2), 3) for i in range(n_semillas)] + [media])
    return filas


def meta_sintetico(ruta, esc, var, et, b, episodios=200):
    """Meta de una base del mundo sintetico (como rl_ippo, revalidar_c0 o p3_elegir regla)."""
    val = VAL_BASE[b]
    conv = (esc, et, b) not in NO_CONVERGE
    if ruta.startswith("insumos/entregado/"):
        serie = serie_sintetica(val, 200, True, 2)
        return {"escenario": esc, "variante": "vecinos", "base": b, "episodios": 200, "val_seeds": [999, 1999],
                "val_serie": serie, "val_elegido": serie[-1][-1], "ep_elegido": serie[-1][0]}
    serie = serie_sintetica(val, episodios, conv)
    m = {"escenario": esc, "variante": var, "base": b, "etiqueta": et, "episodios": episodios, "algoritmo": "ippo",
         "val_seeds": list(gt.VAL16), "val_total_serie": serie, "val_serie": serie,
         "val_elegido": min(f[-1] for f in serie), "ep_elegido": min(serie, key=lambda f: f[-1])[0],
         "opciones": {"criterio_val": "total", "etiqueta": et}}
    if et.startswith(("p3c0",)):
        m["criterio_val"] = "total"
    if et in ("p3v2vieja",) or et.startswith(("p3piso200", "p3e400c20")):
        m["serie_eleccion"], m["regla_eleccion"] = serie, et
    return m


def csv_sintetico(ruta, e, lleg, brazo, roto=None, no_ins=None):
    filas = []
    tl = "T1" if e["tanda"] in ("t1r", "h1t1", "t1a", "puente", "promo") else "T2"
    base = e["base"] if e["base"] != "" else None
    ef, alt, clave = efecto_mundo(e["celda"], e["escenario"], lleg, tl, e["tipo"], base)
    for k, s in enumerate(rango(e["semillas"])):
        dif = 1 + 0.1 * unif("dif", e["escenario"], s)
        a = alt if s % 2 == 0 else -alt
        r = 30.0 * dif * (1 + (ef + 0.6 * unif(*clave, s) + a) / 100)
        gen = 1000 + zlib.crc32(f"g|{e['escenario']}|{s}".encode()) % 50 + (1 if roto == k else 0)
        n_ins = (no_ins or {}).get(k, 0)
        filas.append({"brazo": brazo, "modelo": brazo, "base": e["base"], "semilla": s,
                      "retraso_total_prom": round(r, 4), "timeloss_prom": round(0.9 * r, 4),
                      "espera_prom": round(0.3 * r, 4), "retraso_insercion_prom": round(0.1 * r, 4),
                      "no_insertados": n_ins, "cambios_fase": 400 + zlib.crc32(f"c|{clave}|{s}".encode()) % 20,
                      "generados": gen, "vehiculos": gen - n_ins, "retraso_total_p1": round(0.95 * r, 4),
                      "retraso_total_p2": round(1.05 * r, 4), "no_insertados_p1": 0, "no_insertados_p2": n_ins})
    escribir(ruta, texto_csv(filas, list(filas[0])))


def manifiesto_ciego_de(raiz, manifiesto, filtro):
    """El formato de p3_noche.manifiesto_ciego: {csv de ciego/: {sha256, bytes, filas, semillas}}."""
    salida = {}
    for e in manifiesto:
        if e["csv"].startswith("ciego/") and filtro(e):
            p = os.path.join(raiz, e["csv"])
            with open(p, encoding="utf-8", newline="") as f:
                semillas = sorted(int(r["semilla"]) for r in csv.DictReader(f))
            salida[e["csv"]] = {"sha256": sha256(p), "bytes": os.path.getsize(p), "filas": len(semillas),
                                "semillas": [semillas[0], semillas[-1], len(semillas)]}
    return salida


def sellar_mundo(raiz, manifiesto):
    """cola/manifiesto_cierre.json con las claves de manifiesto.py cierre: csv, metas y otros."""
    csvs = {e["csv"]: sha256(os.path.join(raiz, e["csv"])) for e in manifiesto if not es_final(e["tanda"])}
    metas = {os.path.relpath(p, raiz).replace(os.sep, "/"): sha256(p)
             for p in glob.glob(os.path.join(raiz, "politica_*.json"))}
    otros = {r: sha256(os.path.join(raiz, r)) for r in otros_que_se_sellan(raiz)}
    escribir(os.path.join(raiz, "cola", "manifiesto_cierre.json"),
             json.dumps({"csv": csvs, "metas": metas, "otros": otros}, indent=0, sort_keys=True) + "\n")


def mundo_sintetico(raiz):
    """Carpeta plan3 sintetica (dentro de tmp_ver/) con el manifiesto y los trabajos reales del generador (las partes
    base, sin los alias de etapa3b), mas lo que el generador todavia no produce (referencias nuevas, V2 regular de 3
    bases con llegadas aleatorias, a3, perfil, mezcla y arranque lento); semillas de humo; CSV de cada brazo con efectos
    conocidos; metas; bases caidas declaradas; promocion decidida con p3_promocion; insumos del puente; el sello del
    cierre y dos mananas de cola/manifiesto_ciego.json commiteadas en un repositorio git anidado (temporal)."""
    carpeta_limpia(raiz)
    partes = [p for p in gt.PARTES if not p.startswith("etapa3b_")]           # sin los alias etapa3b_reg/_poi
    trabajos, manifiesto = gt.generar_con_manifiesto(partes)
    nuevos = []

    def agregar(celda, esc, tanda, tipo, base, brazo_cmd):
        clave = f"{tipo}_s{base}" if base != "" else tipo
        carpeta = "ciego" if tanda in ("t1r", "t2r", "t1a", "t2a", "h1t1", "h1t2") else "parciales"
        ruta, tid = f"{carpeta}/{tanda}/eval_{esc}__{clave}.csv", f"ev_{tanda}_{esc}__{clave}"
        nuevos.append({"csv": ruta, "celda": celda, "escenario": esc, "tanda": tanda, "clave": clave, "tipo": tipo,
                       "base": base, "semillas": "", "trabajo": tid})
        trabajos.append({"id": tid, "etapa": "ev", "prioridad": 4, "uso": "sin_semillas", "requiere": [],
                         "cmd": f"python evaluar3.py --escenario {esc} --salida {ruta} {brazo_cmd}",
                         "salidas": [ruta], "duracion": 1})
    celdas = {}
    for e in manifiesto:
        celdas.setdefault((e["celda"], e["escenario"]), set()).add(e["tanda"])
    for (c, esc), tandas in sorted(celdas.items()):
        for t in sorted(tandas & {"t1r", "t2r", "t1a", "t2a"}):
            for ref in EXTRAS_REF:
                if (c, ref) not in (("r905", REF_FINO), ("r1358", REF_VETO)):  # una referencia que falta: PENDIENTE
                    agregar(c, esc, t, ref, "", f"--programa {ref}.add.xml --nombre {ref}")
    for c in CASOS6:                            # V2 regular de 42/2042/4042 con llegadas aleatorias (P6: la de P6e)
        e_reg = gt.P6E["P6e"] if c == "P6" else gt.CASOS[c]
        for t in ("t1a", "t2a"):
            agregar(c, gt.POI[c], t, "v2reg3poi", "", f"--politica politica_{e_reg}_vecinos_p3v2reg3med.pt")
    rutas_p6e = ",".join(f"politica_malla3_alta_e_vecinos_p3v2reg_s{b}.pt" for b in BASES3)
    trabajos.append({"id": "el_p3v2reg3med_malla3_alta_e", "etapa": "ev", "prioridad": 2, "uso": "sin_semillas",
                     "requiere": [], "salidas": ["politica_malla3_alta_e_vecinos_p3v2reg3med.pt"], "duracion": 10,
                     "cmd": f"python p3_elegir.py mediana --politicas {rutas_p6e} --etiqueta p3v2reg3med "
                            f"--salida politica_malla3_alta_e_vecinos_p3v2reg3med.pt"})
    for c, esc, tandas, versiones in (("P1", "corredor", ("t1r", "t2r"), ("v2reg3med", "p3obsmed")),
                                      ("P1", "poi_corredor", ("t1a", "t2a"), ("v2poi3med", "p3obspoimed"))):
        for t in tandas:                        # a3 solo en P1: las otras celdas de a3 quedan "no se pudo correr"
            for ver in versiones:
                pol = f"politica_{esc}_vecinos_{'p3' if ver.startswith('v2') else ''}{ver}.pt"
                agregar(c, esc, t, f"a3colas0_{ver}", "", f"--politica {pol} --colas-cero")
                agregar(c, esc, t, f"a3msg0_{ver}", "", f"--politica {pol} --perdida 1")
    for celda, esc, fam, et in (("per1", "per_corredor", "v2per", "p3v2per"),
                                ("mix1", "mix_corredor", "v2mix", "p3v2mix"),
                                ("mixa1", "mixa_corredor", "v2mix", "p3v2mix")):
        esc_pol = "mix_corredor" if et == "p3v2mix" else esc        # el arranque lento juega la V2 de la mezcla
        for t in ("t1a", "t2a"):
            for b in BASES3:
                agregar(celda, esc, t, fam, b, f"--politica politica_{esc_pol}_vecinos_{et}_s{b}.pt")
            refs = ("ref_fino", "ref_actuadoaj", "ref_regla", "ref_trivial", "ref_actuado", "ref_fijo")
            for ref in refs + (("ref_bloques",) if fam == "v2per" else ()):
                agregar(celda, esc, t, ref, "", f"--programa {ref}.add.xml --nombre {ref}")
            if fam == "v2per":
                agregar(celda, esc, t, "v2poimed", "", "--politica politica_poi_corredor_vecinos_p3v2poimed.pt")
    manifiesto = [e for e in manifiesto + nuevos if clave_base(e) not in CAIDAS_MUNDO]
    for e in manifiesto:
        e["semillas"] = SEMILLAS_PRUEBA[e["tanda"]]
    escribir(os.path.join(raiz, "cola", "manifiesto_esperado.json"), json.dumps(manifiesto, indent=0) + "\n")
    escribir(os.path.join(raiz, "cola", "trabajos.jsonl"), "".join(json.dumps(t) + "\n" for t in trabajos))
    escribir(os.path.join(raiz, "cola", "caidas.json"), json.dumps([
        {"celda": c, "escenario": esc, "tipo": tipo, "base": b,
         "intentos": [{"id": f"e2_v2poi_{esc}_s{b}", "error": "pérdida NaN", "fecha": "2026-11-15 03:10"},
                      {"id": f"e2_v2poi_{esc}_s{b}", "error": "pérdida NaN", "fecha": "2026-11-16 02:55"}]}
        for c, esc, tipo, b in sorted(CAIDAS_MUNDO)], indent=1) + "\n")
    # metas de cada base (menos las caidas) y de cada version publicada (con las candidatas que existen)
    rutas, medianas_pub = set(), []
    for t in trabajos:
        partes_t = partes_de(t)
        for op in ("--politica", "--politicas"):
            if op in partes_t:
                rutas |= set(partes_t[partes_t.index(op) + 1].split(","))
        if "mediana" in partes_t:
            medianas_pub.append((partes_t[partes_t.index("--politicas") + 1].split(","),
                                 partes_t[partes_t.index("--salida") + 1], partes_t[partes_t.index("--etiqueta") + 1]))
    caidas_pol = {f"politica_{esc}_vecinos_p3{tipo}_s{b}.pt" for _, esc, tipo, b in CAIDAS_MUNDO}
    for r in sorted(rutas - {m[1] for m in medianas_pub} - caidas_pol):
        m = (re.fullmatch(r"insumos/entregado/politica_(.+)_(vecinos)_s(\d+)\.pt", r)
             or re.fullmatch(r"politica_(.+)_(vecinos|local)_(p3[a-z0-9]+)_s(\d+)\.pt", r))
        if not m:
            raise ErrorVeredicto(f"mundo sintetico: ruta inesperada {r}")
        if r.startswith("insumos/"):
            meta = meta_sintetico(r, m.group(1), "vecinos", "", int(m.group(3)))
        else:
            et = m.group(3)
            eps = 400 if et.startswith(("p3e400", "p3completo")) else 200
            meta = meta_sintetico(r, m.group(1), m.group(2), et, int(m.group(4)), eps)
        escribir(os.path.join(raiz, r[:-3] + ".json"), json.dumps(meta) + "\n")
    for cand, salida, et in medianas_pub:
        metas = {r: leer_json(os.path.join(raiz, r[:-3] + ".json")) for r in cand
                 if os.path.exists(os.path.join(raiz, r[:-3] + ".json"))}
        b = base_mediana_n({m["base"]: m["val_elegido"] for m in metas.values()})
        elegida = next(m for m in metas.values() if m["base"] == b)
        meta = dict(elegida, etiqueta=et, version_evaluada=True, base_elegida=b,
                    candidatas=[{"base": m["base"], "val_elegido": m["val_elegido"], "politica": r}
                                for r, m in metas.items()])
        escribir(os.path.join(raiz, salida[:-3] + ".json"), json.dumps(meta) + "\n")
    # CSV de cada entrada del manifiesto (el brazo, el que escribiria evaluar3 para su trabajo)
    trab = {t["id"]: t for t in trabajos}
    for e in manifiesto:
        lleg = LLEGADAS.get(e["tanda"]) or ("aleatorias" if e["escenario"].startswith("poi_") else "regulares")
        t = trab.get(e["trabajo"])
        pol = politica_de(t)
        brazo = brazo_de_trabajo(t, leer_json(os.path.join(raiz, pol[:-3] + ".json")) if pol else None) or e["tipo"]
        roto = 3 if (e["celda"], e["tipo"], e["tanda"]) == ("m2715", "ref_franja", "t1r") else None
        no_ins = NO_INSERTADOS_MUNDO.get((e["celda"], e["escenario"], e["tipo"], e["tanda"]))
        csv_sintetico(os.path.join(raiz, e["csv"]), e, lleg, brazo, roto=roto, no_ins=no_ins)
    # puente: CSV entregados del fijo y de IPPO entregado (version evaluada: base 42) e insumos/manifiesto.json
    for c, esc in gt.CASOS.items():
        e = {"celda": c, "escenario": esc, "tanda": "puente", "semillas": SEMILLAS_PRUEBA["puente"], "base": 42}
        for nombre_csv, tipo in (("fijo", "ref_fijo"), ("ippo_vecinos_s42", "entmed")):
            csv_sintetico(os.path.join(raiz, "insumos", "puente", f"eval_{esc}_{nombre_csv}.csv"),
                          dict(e, tipo=tipo), "regulares", nombre_csv)
    escribir(os.path.join(raiz, "insumos", "manifiesto.json"), json.dumps({
        g: {os.path.basename(p): [os.path.getsize(p), sha256(p)] for p in glob.glob(os.path.join(raiz, g, "*"))}
        for g in ("insumos/entregado", "insumos/puente")}, indent=0) + "\n")
    # promocion con p3_promocion (decidir y juntar), con las semillas de humo del mundo; D queda sin decision
    import contextlib
    import p3_promocion
    viejas = p3_promocion.SEMILLAS
    p3_promocion.SEMILLAS = rango(SEMILLAS_PRUEBA["promo"])
    try:
        por_esc, salidas = {}, []
        for e in manifiesto:
            if e["tanda"] == "promo":
                por_esc.setdefault(e["escenario"], []).append(e)
        with contextlib.redirect_stdout(io.StringIO()):
            for esc, ents in sorted(por_esc.items()):
                if esc == gt.D["D"]:
                    continue
                v2 = next(x for x in ents if x["tipo"] in ("promo_p3v2reg", "promo_p3v2poi"))
                salida = os.path.join(raiz, "promocion", f"{esc}.json")
                p3_promocion.decidir(argparse.Namespace(
                    celda=esc, v2=os.path.join(raiz, v2["csv"]), salida=salida,
                    candidatos=",".join(os.path.join(raiz, x["csv"]) for x in ents if x is not v2)))
                salidas.append(salida)
            p3_promocion.juntar(argparse.Namespace(entradas=",".join(salidas),
                                                   salida=os.path.join(raiz, "promocion.json")))
    finally:
        p3_promocion.SEMILLAS = viejas
    escribir(os.path.join(raiz, "listo", "cierre.ok"), "cierre sintetico\n")
    sellar_mundo(raiz, manifiesto)
    # dos mananas de cola/manifiesto_ciego.json, commiteadas en un repositorio git anidado y temporal
    for args in (("init", "-q"),):
        rc, out = protecciones.git(*args, cwd=raiz)
        if rc != 0:
            raise ErrorVeredicto(f"mundo sintetico: git {args}: {out}")
    for n, filtro in ((1, lambda e: e["tanda"] in ("t1r", "t2r")), (2, lambda e: True)):
        escribir(os.path.join(raiz, "cola", "manifiesto_ciego.json"),
                 json.dumps(manifiesto_ciego_de(raiz, manifiesto, filtro), indent=1, sort_keys=True))
        for args in (("add", "cola/manifiesto_ciego.json"), ("commit", "-q", "-m", f"manana {n}")):
            rc, out = protecciones.git(*args, cwd=raiz)
            if rc != 0:
                raise ErrorVeredicto(f"mundo sintetico: git {args}: {out}")
    return manifiesto


def probar():
    lineas = []

    def ok(cond, texto):
        lineas.append(("PASA  " if cond else "FALLA ") + texto)
        return cond

    def nota(texto):
        lineas.append("      " + texto)

    def grupo(titulo, funcion):
        lineas.append(f"--- {titulo}")
        try:
            funcion()
        except Exception as ex:                 # una prueba que revienta cuenta como FALLA y se sigue
            import traceback
            ok(False, f"{titulo}: excepción {type(ex).__name__}: {ex}")
            lineas.extend("      " + x for x in traceback.format_exc().splitlines()[-6:])

    def leer_eval(ruta, metrica=METRICA):
        with open(ruta, newline="", encoding="utf-8") as f:
            return {int(r["semilla"]): float(r[metrica]) for r in csv.DictReader(f) if r.get(metrica)}

    def leer_filas(ruta):
        with open(ruta, newline="", encoding="utf-8") as f:
            return {int(r["semilla"]): r for r in csv.DictReader(f)}

    def meta_plan2(nombre_arch, carpeta=PLAN2):
        return leer_json(os.path.join(carpeta, nombre_arch))

    # ===== 1. Las del prototipo (lo entregado de plan2/, solo lectura) =====
    def prototipo():
        viejo = tempfile.tempdir
        tempfile.tempdir = carpeta_limpia(os.path.join(TMP_VER, "tempfile"))     # vd.probar usa un temporal
        try:
            vd.probar()
        finally:
            tempfile.tempdir = viejo
        ok(True, "P01 veredicto.probar(): la regla, la convergencia, la base mediana y el formato no cambiaron")
        expl = os.path.join(PLAN2, "exploratorio_coord", "politicas")
        m = meta_plan2("politica_malla3_alta_smdp_crn_s4042.json", expl)
        e = entrenamiento(m)
        ok(m["val_seeds"] == VAL8 and round(e["meseta"], 2) == 3.19 and round(e["estabilidad"], 2) == 0.00
           and e["convergio"], f"P02 V2 de P6 (s4042, 8 semillas, serie del diagnostico): meseta {e['meseta']:.2f} %, "
                               f"estabilidad {e['estabilidad']:.2f} %, convergio")
        x3 = sorted((int(x[0]), float(x[3])) for x in m["val_serie"])
        c3 = vd.convergencia(x3, 200)
        ok(round(c3[1], 2) == 9.43 and not c3[0], "P03 con x[3] (lo que hace info_base) sale 9.43 % y 'no convergio'")
        e5 = entrenamiento(meta_plan2("politica_malla3_alta_norm_smdp_crn_triv_s42.json", expl))
        ok(round(e5["meseta"], 2) == -4.61 and e5["convergio"], f"P04 V5 de P6 (s42): meseta {e5['meseta']:.2f} %")
        iguales = 0
        for b in BASES3:
            for esc in gt.CASOS.values():
                nuevo = entrenamiento(meta_plan2(f"politica_{esc}_vecinos_s{b}.json"))
                viejo_ = vd.info_base(PLAN2, esc, "ippo_vecinos", b)
                iguales += (nuevo["convergio"] == viejo_["convergio"]
                            and abs(nuevo["meseta"] - viejo_["plateau"]) < 1e-12
                            and abs(nuevo["estabilidad"] - viejo_["estabilidad"]) < 1e-12)
        ok(iguales == 18, f"P05 metas entregados de IPPO con mensajes: identico a info_base en {iguales}/18")
        with open(os.path.join(PLAN2, "diag_corredor", "resultados.csv"), newline="", encoding="utf-8") as f:
            filas = [r for r in csv.DictReader(f) if r["control"] == "v2" and r["semillas"] == "1001-1030"]
        nivel_esc = {"905": "dem_corredor_t905", "1358": "dem_corredor_t1358", "P1": "corredor",
                     "2715": "dem_corredor_t2715", "P2": "corredor_alta"}
        filas = list({r["nivel"]: r for r in filas}.values())
        coinciden = 0
        for r in filas:
            meta = meta_plan2(f"politica_{nivel_esc[r['nivel']]}_vecinos_v2_s{r['base_evaluada']}.json")
            e = entrenamiento(meta)
            coinciden += (criterio(meta) == "total" and ("si" if e["convergio"] else "no") == r["convergio"])
        ok(coinciden == len(filas) == 5,
           f"P06 V2 del corredor (criterio total): convergencia igual a analisis.py en {coinciden}/{len(filas)} "
           f"niveles")
        a = leer_eval(os.path.join(PLAN2, "parciales", "eval_corredor_ippo_vecinos_s4042.csv"))
        b = leer_eval(os.path.join(PLAN2, "parciales", "eval_corredor_fijo.csv"))
        c = comparar(a, b, range(1001, 1031))
        with open(os.path.join(PLAN2, "evaluacion_corredor_resumen.csv"), newline="", encoding="utf-8") as f:
            r = next(x for x in csv.DictReader(f) if x["brazo"] == "ippo_vecinos_s4042" and x["metrica"] == METRICA)
        ok(c["cambio"] == float(r["delta_pct"]) and r["delta_ic95"] == f"[{c['ic'][0]:.2f}, {c['ic'][1]:.2f}]"
           and f"{c['p']:.3g}" == r["p_wilcoxon"], f"P07 comparar reproduce el resumen de consolidar: "
                                                   f"{c['cambio']} % {c['ic']} p={c['p']:.3g}")
        with open(os.path.join(PLAN2, "robustez_veredicto.csv"), newline="", encoding="utf-8") as f:
            rob = {(x["caso"], x["modelo"]): x for x in csv.DictReader(f)}
        iguales = 0
        for caso, esc in vd.CASOS:
            infos = {bb: entrenamiento(meta_plan2(f"politica_{esc}_vecinos_s{bb}.json")) for bb in BASES3}
            pub = base_mediana_n({bb: i["val"] for bb, i in infos.items()})
            mod = leer_eval(os.path.join(PLAN2, "parciales", f"eval_{esc}_ippo_vecinos_s{pub}.csv"))
            fijo = leer_eval(os.path.join(PLAN2, "parciales", f"eval_{esc}_fijo.csv"))
            act = leer_eval(os.path.join(PLAN2, "parciales", f"eval_{esc}_actuado.csv"))
            et = etiqueta(comparar(mod, fijo, range(1001, 1031)), comparar(mod, act, range(1001, 1031)),
                          infos[pub]["convergio"])
            esperado = rob[(caso, "ippo_vecinos")]["veredicto"].replace(" (= trivial)", "")
            iguales += et == esperado
            nota(f"{caso}: base {pub} -> {et} (entregado: {esperado})")
        ok(iguales == 6, f"P08 etiqueta de IPPO con mensajes P1-P6 igual a la robustez entregada en {iguales}/6")
        with open(os.path.join(PLAN2, "demanda2", "resumen_demanda2.csv"), newline="", encoding="utf-8") as f:
            niveles = [x for x in csv.DictReader(f) if x["escenario"].startswith("dem_")]
        iguales = 0
        for x in niveles:
            esc = x["escenario"]
            infos = {bb: entrenamiento(meta_plan2(f"politica_{esc}_vecinos_s{bb}.json")) for bb in BASES3}
            pub = base_mediana_n({bb: i["val"] for bb, i in infos.items()})
            dem = os.path.join(PLAN2, "demanda2")
            mod = leer_eval(os.path.join(dem, f"eval_{esc}_ippo_vecinos_s{pub}.csv"), "timeloss_prom")
            fijo = leer_eval(os.path.join(dem, f"eval_{esc}_fijo.csv"), "timeloss_prom")
            act = leer_eval(os.path.join(dem, f"eval_{esc}_actuado.csv"), "timeloss_prom")
            et = etiqueta(comparar(mod, fijo, range(1001, 1031)), comparar(mod, act, range(1001, 1031)),
                          infos[pub]["convergio"])
            iguales += et == x["veredicto"] and str(pub) == x["base_evaluada"]
        ok(iguales == len(niveles) == 12, f"P08b etiquetas de los 12 niveles de la entrega 3 (timeLoss) desde los CSV "
                                          f"por semilla: iguales en {iguales}/{len(niveles)}")
        hh = holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.005})
        ok([round(hh[k], 4) for k in "abcd"] == [0.03, 0.06, 0.06, 0.02], f"P09 Holm {hh}")
        tabla = [("FUNCIONA", "FUNCIONA", "FUNCIONA"), ("FUNCIONA", "MEJORA", "MEJORA"),
                 ("MEJORA", "EMPATA", "EMPATA (mejora no confirmada)"), ("FALLA", "FALLA", "FALLA"),
                 ("FALLA", "EMPATA", "EMPATA (falla no confirmada)"),
                 ("MEJORA", "FALLA", "CONTRADICTORIO (no se concluye)"),
                 ("EMPATA", "EMPATA", "EMPATA"),
                 ("PENDIENTE (no convergió; provisional: MEJORA)", "PENDIENTE (no convergió; provisional: MEJORA)",
                  "PENDIENTE (no convergió; provisional: MEJORA)"), ("MEJORA (= trivial)", "MEJORA", "MEJORA")]
        ok(all(acuerdo(x, y) == z for x, y, z in tabla), "P10 acuerdo: tabla de verdad (textos de §7)")
        s = sentido({42: -2, 2042: -1, 4042: 0.5}, 3)
        ok(s["k"] == 2 and not s["cumple"], "P11 con 3 bases, 2 de 3 del lado ya no alcanza (A5: 3 de 3)")
        s = sentido({42: -2, 2042: -1, 4042: -0.5}, 3)
        ok(s["k"] == 3 and s["cumple"], "P12 con 3 bases, 3 de 3 cumple")
        s = sentido({42: -2, 2042: -1, 4042: -1, 14042: -3, 16042: 1.5}, 5)
        ok(s["k"] == 4 and s["cumple"], "P13 con 5 bases, 4 de 5 cumple")
        ok(lectura_ni({"ic": (-1.0, 1.99)}, 0.01) == "no es peor" and lectura_ni({"ic": (-1.0, 2.01)}, 0.01)
           == "no concluyente", "P14 no inferioridad: margen +2 %")
        ruta = escribir(os.path.join(TMP_VER, "demanda.rou.xml"),
                        '<routes><flow id="a" begin="0" end="1800" vehsPerHour="600"/>'
                        '<flow id="b" begin="0" end="3600" period="exp(0.25)"/>'
                        '<flow id="c" begin="1800" end="3600" period="36"/></routes>')
        ok(abs(demanda_esperada([ruta]) - (300 + 900 + 50)) < 1e-9, "P15 demanda esperada con period=exp(l)")
        filas = {br: leer_filas(os.path.join(PLAN2, "parciales", f"eval_corredor_{br}.csv"))
                 for br in ("fijo", "actuado", "trivial", "ippo_vecinos_s4042")}
        ok(not generados_iguales(filas), "P16 numeros aleatorios comunes (P1): mismos vehiculos en las 30 semillas")
        a1 = leer_eval(os.path.join(PLAN2, "diag_corredor", "eval", "eval_corredor_ippo_vecinos_v2_s42_1001.csv"))
        a2 = leer_eval(os.path.join(PLAN2, "diag_corredor", "eval", "eval_corredor_ippo_vecinos_v2_s42_6001.csv"))
        b2 = leer_eval(os.path.join(PLAN2, "diag_corredor", "eval", "eval_corredor_fijo_6001.csv"))
        dd = diferencia_no_pareada(a1, b, a2, b2, set(a1), set(a2))
        ok(dd["ic"][0] < dd["D"] < dd["ic"][1], f"P17 diferencia no pareada (V2 P1, 1001 menos 6001): {dd}")
        pni = p_no_inferioridad(a1, b)
        ok(pni < 0.05, f"P18 p de no inferioridad de V2 P1 frente al fijo (margen +2 %): {pni:.3g}")

    # ===== 2. Reglas nuevas con datos fabricados (sin archivos) =====
    S1, S2 = rango(SEMILLAS_PRUEBA["t1r"]), rango(SEMILLAS_PRUEBA["t2r"])

    def reglas():
        import random
        rnd = random.Random(7)
        bien = 0
        for _ in range(200):
            vals = {b: rnd.choice([19.0, 20.0, 20.5, 21.0]) for b in BASES3}
            bien += base_mediana_n(vals) == vd.base_mediana(vals)
        ok(bien == 200, "N01a base_mediana_n con 3 bases = veredicto.base_mediana (200 casos al azar, con empates)")
        ok(base_mediana_n({42: 30, 2042: 29, 4042: 31, 14042: 28, 16042: 32}) == 42,
           "N01b con 5 bases, la 3.a por val_elegido")
        ok(base_mediana_n({42: 30, 2042: 29, 4042: 31, 14042: 28}) == 42,
           "N01c con 4 bases (una caida), la peor de las dos centrales")
        ok(base_mediana_n({42: 20, 2042: 20, 4042: 25}) == 2042 and mejor_base({42: 20, 2042: 20, 4042: 25}) == 42,
           "N01d empate de val: la base menor va primero")
        m = meta_sintetico("politica_x_vecinos_p3v2reg_s42.pt", "x", "vecinos", "p3v2reg", 42)
        clave, serie = serie_criterio(m)
        ok(clave == "val_total_serie" and serie[0][1] == m["val_total_serie"][0][-1] and
           serie[0][1] != m["val_total_serie"][0][3], "N02 serie_criterio: val_total_serie con x[-1] (la media de 16), "
                                                       "no x[3]")
        f1 = fabricar(S1, 0, clave="fino", esc="e")
        try:
            comparar({**fabricar(S1, -3, clave="m", esc="e"), 424399: 1.0}, f1, S1)
            ok(False, "N03a una semilla de mas: deberia ser error")
        except ErrorVeredicto as ex:
            ok(True, f"N03a una semilla de mas es ERROR ({ex})")
        try:
            comparar({s: v for s, v in fabricar(S1, -3, clave="m", esc="e").items() if s != S1[0]}, f1, S1)
            ok(False, "N03b una semilla de menos: deberia ser error")
        except ErrorVeredicto as ex:
            ok(True, f"N03b una semilla de menos es ERROR ({ex})")
        # tabla de etiqueta citable de §7, con datos por semilla fabricados para cada fila
        efectos = {"FUNCIONA": (-8, 0), "MEJORA": (-3, 0), "EMPATA": (0, 1.0), "FALLA": (4, 0)}

        def et_tanda(objetivo, semillas, convergio=True, act_ef=3, act_alt=0.0):
            ef, alt = efectos[objetivo]
            fino = fabricar(semillas, 0, clave="fino")
            mod = fabricar(semillas, ef, alterno=alt, clave="mod")
            act = fabricar(semillas, act_ef, alterno=act_alt, clave="act")
            return etiqueta(comparar(mod, fino, semillas), comparar(mod, act, semillas), convergio)
        filas_tabla = [("FUNCIONA", "FUNCIONA", "FUNCIONA"), ("MEJORA", "MEJORA", "MEJORA"),
                       ("EMPATA", "EMPATA", "EMPATA"), ("FALLA", "FALLA", "FALLA"),
                       ("FUNCIONA", "MEJORA", "MEJORA"), ("MEJORA", "FUNCIONA", "MEJORA"),
                       ("MEJORA", "EMPATA", "EMPATA (mejora no confirmada)"),
                       ("FUNCIONA", "EMPATA", "EMPATA (mejora no confirmada)"),
                       ("EMPATA", "MEJORA", "EMPATA (mejora no confirmada)"),
                       ("FALLA", "EMPATA", "EMPATA (falla no confirmada)"),
                       ("EMPATA", "FALLA", "EMPATA (falla no confirmada)"),
                       ("MEJORA", "FALLA", "CONTRADICTORIO (no se concluye)"),
                       ("FUNCIONA", "FALLA", "CONTRADICTORIO (no se concluye)"),
                       ("FALLA", "MEJORA", "CONTRADICTORIO (no se concluye)")]
        for o1, o2, esperado in filas_tabla:
            e1, e2 = et_tanda(o1, S1), et_tanda(o2, S2)
            ok(e1 == o1 and e2 == o2 and acuerdo(e1, e2) == esperado,
               f"N04 T1 {o1} y T2 {o2} (datos por semilla): {e1} / {e2} -> {acuerdo(e1, e2)}")
        e1, e2 = et_tanda("MEJORA", S1, False), et_tanda("MEJORA", S2, False)
        ok(acuerdo(e1, e2) == "PENDIENTE (no convergió; provisional: MEJORA)",
           f"N04 version no convergida: {acuerdo(e1, e2)}")
        e1 = etiqueta(None, motivo="falta fijo fino en t1r")
        ok(acuerdo(e1, et_tanda("MEJORA", S2)) == "PENDIENTE (falta fijo fino en t1r)",
           "N04 una referencia que falta: PENDIENTE con su motivo")
        # veto del actuado ajustado
        e_veto = et_tanda("FUNCIONA", S1, act_ef=-12)
        e_empata = et_tanda("FUNCIONA", S1, act_ef=-8, act_alt=1.0)
        e_gana = et_tanda("FUNCIONA", S1, act_ef=3)
        ok(e_veto == "MEJORA" and e_empata == "FUNCIONA" and e_gana == "FUNCIONA",
           f"N05 veto: -8 % frente al fino y pierde contra el actuado ajustado (IC entero sobre 0, p < 0.05) -> "
           f"{e_veto}; empata con el actuado ajustado -> {e_empata}; le gana -> {e_gana}")
        # sentido 4 de 5
        uno = sentido({42: -3, 2042: -2.5, 4042: 1.0, 14042: -3.2, 16042: -2.8}, 5)
        dos = sentido({42: -3, 2042: 0.4, 4042: 1.0, 14042: -3.2, 16042: -2.8}, 5)
        ok(uno["cumple"] and not dos["cumple"], "N06 sentido: 4 de 5 con una base en contra pasa; con dos, no")
        cae = sentido({42: -3, 2042: -2.5, 4042: -1.0, 14042: -3.2, 16042: None}, 5)
        ok(cae["k"] == 4 and cae["cumple"] and not sentido({42: -3, 2042: None, 4042: -1}, 3)["cumple"],
           "N06b una base caida cuenta como fuera del lado (4 de 5 aun alcanza; con 3, no)")
        # Holm con una familia de 6
        p6 = {"P1": 0.001, "P2": 0.01, "P3": 0.04, "P4": 0.03, "P5": 0.2, "P6": None}
        aj = holm(p6)
        esperado = {"P1": 0.006, "P2": 0.05, "P4": 0.12, "P3": 0.12, "P5": 0.4, "P6": None}
        ok(all((aj[k] is None and esperado[k] is None) or abs(aj[k] - esperado[k]) < 1e-12 for k in p6),
           f"N07 Holm con una familia de 6 (P6 no se pudo correr y cuenta con p = 1): {aj}")
        # las tres lecturas de la no inferioridad, con datos
        lect = {}
        for nombre_l, ef, alt in (("no es peor", -1.0, 0), ("es peor", 5.0, 0), ("no concluyente", 2.0, 1.5)):
            a_, b_ = fabricar(S1, ef, alterno=alt, clave="ni"), fabricar(S1, 0, clave="fino")
            c_ = comparar(a_, b_, S1)
            lect[nombre_l] = lectura_ni(c_, p_no_inferioridad(a_, b_))
        ok(all(k == v for k, v in lect.items()), f"N08 tres lecturas de la no inferioridad: {lect}")
        # H1 por interseccion-union
        def caso_h1(ef1, ef2):
            out = []
            for ef, ss in ((ef1, S1), (ef2, S2)):
                a_, b_ = fabricar(ss, ef, clave="v2"), fabricar(ss, 0, clave="c0")
                out.append({"comp": comparar(a_, b_, ss), "p_ni": p_no_inferioridad(a_, b_)})
            return out
        bien = [caso_h1(-1, -0.5) for _ in range(6)]
        mal = bien[:5] + [caso_h1(-1, 2.0)]
        ok(interseccion_union(bien) and not interseccion_union(mal),
           "N09 H1 global (interseccion-union): 6 casos 'no es peor' en T1 y T2 pasa; uno que no lo es en T2, no")
        # H6
        a1, b1 = fabricar(S1, -6, clave="a1", esc="poi"), fabricar(S1, 0, clave="b1", esc="poi")
        a2, b2 = fabricar(S2, -3, clave="a2", esc="reg"), fabricar(S2, 0, clave="b2", esc="reg")
        dd = diferencia_no_pareada(a1, b1, a2, b2, S1, S2)
        ok(abs(dd["D"] - (-3)) < 0.6 and dd["ic"][1] < 0 and dd["p"] < 0.01,
           f"N10 H6, diferencia no pareada: D {dd['D']} [{dd['ic'][0]}, {dd['ic'][1]}], p de una cola {dd['p']}")
        # numeros aleatorios comunes y ciclo minimo
        fa = {s: {"generados": 1000, METRICA: 1.0, "espera_prom": 1.0} for s in S1}
        fb = {s: dict(fa[s], generados=1000 + (s == S1[3])) for s in S1}
        ok(generados_iguales({"a": fa, "b": fb}) == [(S1[3], {"a": 1000, "b": 1001})] and
           not generados_iguales({"a": fa, "b": fa}), "N11a generados_iguales encuentra la semilla con otro vehiculo")
        fc = {s: dict(fa[s], **{METRICA: 1.0004}) for s in S1}
        fd = {s: dict(fa[s], **{METRICA: 1.0011}) for s in S1}
        ok(igual_ciclo_minimo(fa, fc) and not igual_ciclo_minimo(fa, fd), "N11b igual al ciclo minimo hasta 0.0005 s")
        # numero unico
        series = [(np.array(list(fabricar(S1, ef, clave=f"m{k}").values())),
                   np.array(list(fabricar(S1, 0, clave=f"f{k}").values()))) for k, ef in enumerate((-3, -1, 2))]
        nu = numero_unico(series)
        directo = (np.exp(np.mean([np.log(x.mean() / y.mean()) for x, y in series])) - 1) * 100
        ok(abs(nu[0] - round(directo, 2)) < 1e-9 and nu[1] < nu[0] < nu[2],
           f"N12 numero unico = media geometrica de los cocientes ({nu}; directo {directo:.2f})")
        try:
            escribir(os.path.join(RAIZ, "veredicto3_prueba_fuera.txt"), "x")
            ok(False, "N13 escribir fuera de plan3/ deberia negarse")
        except ErrorVeredicto:
            ok(not os.path.exists(os.path.join(RAIZ, "veredicto3_prueba_fuera.txt")),
               "N13 se niega a escribir fuera de plan3/ (la raiz del repositorio)")
        fuera = os.path.join(os.path.dirname(RAIZ), "veredicto3_prueba_fuera.txt")       # sin tocar el temporal
        try:
            escribir(fuera, "x")
            ok(False, "N13b escribir fuera del repositorio deberia negarse")
        except ErrorVeredicto:
            ok(not os.path.exists(fuera), "N13b se niega a escribir fuera del repositorio (sin sondear el temporal)")
        try:
            dentro_de_plan3(PLAN3)
            ok(False, "N13c la carpeta plan3 misma deberia negarse")
        except ErrorVeredicto:
            ok(True, "N13c dentro_de_plan3 rechaza la carpeta plan3 misma")
        try:
            carpeta_limpia(os.path.join(PLAN3, "pruebas"))
            ok(False, "N13d carpeta_limpia fuera de tmp_* deberia negarse")
        except ErrorVeredicto:
            ok(os.path.isdir(os.path.join(PLAN3, "pruebas")), "N13d carpeta_limpia solo borra plan3/tmp_* (pruebas/ "
                                                               "sigue intacta)")
        mal = [{"csv": "ciego/t1r/x.csv", "tanda": "t1r", "semillas": SEMILLAS_PRUEBA["t1r"]}]
        bien_ = [{"csv": "ciego/t1r/x.csv", "tanda": "t1r", "semillas": "8001-8030"},
                 {"csv": "ciego/h1t2/x.csv", "tanda": "h1t2", "semillas": "13031-13120"},
                 {"csv": "ciego/t2a/x.csv", "tanda": "t2a", "semillas": "10001-10100"}]
        try:
            comprobar_semillas(mal)
            ok(False, "N14 un manifiesto con semillas que no son las del prerregistro deberia negarse")
        except ErrorVeredicto:
            comprobar_semillas(bien_)
            ok(True, "N14 --final exige las semillas del prerregistro (8001-8030 pasa; las de humo, no)")
        # AMB-9 (fijada el 05.11): lectura conjunta de una no inferioridad
        si = {"k": 3, "n": 3, "requerido": 3, "cumple": True}
        no = {"k": 2, "n": 3, "requerido": 3, "cumple": False}
        casos = [({"T1": "no es peor", "T2": "no es peor"}, None, (True, "no es peor")),
                 ({"T1": "no es peor", "T2": "no es peor"}, {"T1": si, "T2": si}, (True, "no es peor")),
                 ({"T1": "no es peor", "T2": "no es peor"}, {"T1": si, "T2": no},
                  (False, "la versión evaluada no es peor; el método no se repite en 2 de 3 en T2 entrenamientos")),
                 ({"T1": "es peor", "T2": "es peor"}, None, (False, "es peor (T1: es peor; T2: es peor)")),
                 ({"T1": "es peor", "T2": "no concluyente"}, None,
                  (False, "pérdida no confirmada (T1: es peor; T2: no concluyente)")),
                 ({"T1": "no es peor", "T2": "es peor"}, None,
                  (False, "contradictorio (T1: no es peor; T2: es peor)")),
                 ({"T1": "no es peor", "T2": "no concluyente"}, None,
                  (False, "no concluyente (T1: no es peor; T2: no concluyente)")),
                 ({"T1": "no concluyente", "T2": "no concluyente"}, None,
                  (False, "no concluyente (T1: no concluyente; T2: no concluyente)"))]
        malos = [(x, s, lectura_ni_conjunta(x, s)) for x, s, esperado in casos if lectura_ni_conjunta(x, s) != esperado]
        ok(not malos, f"N15 lectura conjunta de la no inferioridad (AMB-9): {len(casos) - len(malos)} de {len(casos)} "
                      f"casos" + (f"; mal: {malos}" if malos else ""))
        ok(acuerdo("PENDIENTE (no convergió; provisional: MEJORA)", "MEJORA")
           == "PENDIENTE (no convergió; provisional: MEJORA)"
           and acuerdo("FALLA", "PENDIENTE (no convergió; provisional: EMPATA)")
           == "PENDIENTE (no convergió; provisional: EMPATA)",
           "N16 acuerdo con una sola tanda PENDIENTE por convergencia: PENDIENTE (sin StopIteration)")
        m_ok = meta_sintetico("politica_x_vecinos_p3v2reg_s42.pt", "x", "vecinos", "p3v2reg", 42)
        rechazos = 0
        for malo in (dict(m_ok, opciones={"criterio_val": "timeloss"}), dict(m_ok, val_seeds=VAL8)):
            try:
                validar_meta(malo, "politica_x_vecinos_p3v2reg_s42.json")
            except ErrorVeredicto:
                rechazos += 1
        validar_meta(m_ok, "politica_x_vecinos_p3v2reg_s42.json")
        validar_meta(dict(m_ok, opciones={}, val_seeds=[999, 1999]), "insumos/entregado/politica_x_vecinos_s42.json")
        validar_meta(dict(m_ok, opciones={}, serie_eleccion=[[10, 1.0]], regla_eleccion="vieja"),
                     "politica_x_vecinos_p3v2vieja_s42.json")
        ok(rechazos == 2, "N17 una base de plan3 elegida con timeLoss o con 8 semillas es ERROR (§6); lo entregado y "
                          "p3_elegir regla no")

    # ===== 3. Mundo sintetico de punta a punta =====
    raiz = os.path.join(TMP_VER, "mundo")

    def negarse(etiqueta_prueba, funcion, contiene=""):
        """La funcion debe dar ErrorVeredicto (con 'contiene' en el mensaje)."""
        try:
            funcion()
            ok(False, f"{etiqueta_prueba}: debería negarse")
        except ErrorVeredicto as ex:
            texto = re.sub(r"\b[0-9a-f]{10}\b", "<commit>", str(ex))     # el registro no depende de la hora
            ok(contiene in str(ex), f"{etiqueta_prueba} ({texto})" if len(texto) < 160 else
               f"{etiqueta_prueba} ({texto[:157]}...)")

    def con_cambio(rel, nuevo_texto, funcion):
        """Corre funcion con rel cambiado y lo deja como estaba, byte a byte."""
        ruta = dentro_de_plan3(os.path.join(raiz, rel))
        viejo = open(ruta, "rb").read() if os.path.exists(ruta) else None
        try:
            if nuevo_texto is None:
                os.remove(ruta)
            else:
                escribir(ruta, nuevo_texto)
            funcion()
        finally:
            if viejo is None:
                if os.path.exists(ruta):
                    os.remove(ruta)
            else:
                with open(ruta, "wb") as f:
                    f.write(viejo)

    def mundo():
        manifiesto = mundo_sintetico(raiz)
        # --- negativas de --final (antes de analizar) ---
        con_cambio("listo/cierre.ok", None, lambda: negarse(
            "M01 --final sin listo/cierre.ok se niega", lambda: correr_final(raiz, exigir_semillas=False), "cierre.ok"))
        rel = "ciego/t1r/eval_corredor__v2reg_s42.csv"
        original = open(os.path.join(raiz, rel), encoding="utf-8").read()
        con_cambio(rel, original.replace(",", ";", 1), lambda: negarse(
            "M02 un CSV cambiado después del cierre: se niega", lambda: correr_final(raiz, exigir_semillas=False),
            "cambió después del cierre"))
        con_cambio("cola/manifiesto_cierre.json", None, lambda: negarse(
            "M03 sin cola/manifiesto_cierre.json: se niega", lambda: correr_final(raiz, exigir_semillas=False)))
        negarse("M04 --final con semillas que no son las del prerregistro: se niega",
                lambda: correr_final(raiz, exigir_semillas=True), "semillas")
        sello = leer_json(os.path.join(raiz, "cola", "manifiesto_cierre.json"))
        rel_meta = next(r for r in sello["metas"] if "p3v2reg_s14042" in r and "corredor_vecinos" in r)
        texto_meta = open(os.path.join(raiz, rel_meta), encoding="utf-8").read()
        con_cambio(rel_meta, texto_meta.replace('"val_elegido": 28.0', '"val_elegido": 35.0'), lambda: negarse(
            "M04b un meta cambiado después del cierre (otra versión evaluada): se niega",
            lambda: correr_final(raiz, exigir_semillas=False), "cambió después del cierre"))
        texto_promo = open(os.path.join(raiz, "promocion.json"), encoding="utf-8").read()
        con_cambio("promocion.json", texto_promo + " ", lambda: negarse(
            "M04c promocion.json cambiado después del cierre: se niega",
            lambda: correr_final(raiz, exigir_semillas=False), "cambió después del cierre"))
        sello_sin = dict(sello, otros={k: v for k, v in sello["otros"].items() if k != "cola/caidas.json"})
        con_cambio("cola/manifiesto_cierre.json", json.dumps(sello_sin), lambda: negarse(
            "M04d cola/caidas.json sin sellar: se niega", lambda: correr_final(raiz, exigir_semillas=False),
            "no está sellado"))
        sello_meta = dict(sello, metas={k: v for k, v in sello["metas"].items() if k != rel_meta})
        negarse("M04e un meta que se lee y no está sellado: ERROR",
                lambda: analizar(Datos(raiz, estricto=True, sello=sello_meta)), "no está sellado")
        # segunda barrera: la historia de los manifiestos de la manana
        sello_extra = dict(sello, csv=dict(sello["csv"], **{"ciego/t1r/eval_corredor__otro.csv": "0" * 64}))
        negarse("M04f un CSV de ciego/ que no aparece en ninguna mañana: se niega",
                lambda: comprobar_ciego(raiz, sello_extra), "no aparece en ningún manifiesto")
        rel_c = "ciego/t1a/eval_poi_corredor__v2poi_s42.csv"
        texto_c = open(os.path.join(raiz, rel_c), encoding="utf-8").read()

        def resellado():                        # el CSV cambia despues de su manana y se vuelve a sellar
            sellar_mundo(raiz, manifiesto)
            negarse("M04g un CSV de ciego/ cambiado después de su mañana, aunque se vuelva a sellar: se niega",
                    lambda: correr_final(raiz, exigir_semillas=False), "primera mañana")
        con_cambio(rel_c, texto_c.replace(texto_c.splitlines()[1].split(",")[5],
                                          str(float(texto_c.splitlines()[1].split(",")[5]) + 1), 1), resellado)
        sellar_mundo(raiz, manifiesto)
        # --- bases caidas, metas y brazos ---
        rel_m = "politica_red_vecinos_p3v2reg_s2042.json"
        con_cambio(rel_m, None, lambda: negarse(
            "M04h una base con CSV y sin meta: ERROR",
            lambda: Datos(raiz).base_version(("P3", "red"), "v2reg"), "tiene CSV y no tiene meta"))
        caidas = open(os.path.join(raiz, "cola", "caidas.json"), encoding="utf-8").read()
        sin_una = json.dumps([c for c in json.loads(caidas) if c["base"] != 16042])
        con_cambio("cola/caidas.json", sin_una, lambda: negarse(
            "M04i en --final, una base sin CSV y sin declarar caída: ERROR",
            lambda: Datos(raiz, estricto=True).base_version(("P4", "poi_red_alta"), "v2poi"), "no está declarada"))
        un_intento = json.dumps([dict(c, intentos=c["intentos"][:1]) for c in json.loads(caidas)])
        con_cambio("cola/caidas.json", un_intento, lambda: negarse(
            "M04j cola/caidas.json sin los dos intentos fallidos: ERROR", lambda: Datos(raiz), "dos intentos"))
        rel_b = "ciego/t1r/eval_red__v2reg_s42.csv"
        texto_b = open(os.path.join(raiz, rel_b), encoding="utf-8").read()
        con_cambio(rel_b, texto_b.replace("ippo_vecinos_p3v2reg_s42", "ippo_vecinos_p3v2reg_s2042"), lambda: negarse(
            "M04k un CSV con otro brazo que el de su trabajo: ERROR",
            lambda: Datos(raiz).serie(("P3", "red"), ("base", "v2reg", 42), "T1"), "su trabajo escribe"))
        man_txt = open(os.path.join(raiz, "cola", "manifiesto_esperado.json"), encoding="utf-8").read()
        man = json.loads(man_txt)
        con_cambio("cola/manifiesto_esperado.json", json.dumps(man + [dict(man[0], tipo="v2loc", clave="otro")]),
                   lambda: negarse("M04l un CSV que aparece dos veces en el manifiesto: ERROR", lambda: Datos(raiz),
                                   "aparece dos veces"))
        rel_d = "ciego/t1r/eval_dem_malla3_t1810__ref_fino5.csv"
        texto_d = open(os.path.join(raiz, rel_d), encoding="utf-8").read()
        con_cambio(rel_d, texto_d.replace("ref_fino5", "ref_fino"), lambda: negarse(
            "M04m dos CSV de una celda y tanda con el mismo brazo: ERROR", lambda: revisar_generados(Datos(raiz)),
            "el mismo brazo"))
        con_cambio("cola/trabajos.jsonl", None, lambda: negarse(
            "M04n en --final, sin cola/trabajos.jsonl: ERROR", lambda: Datos(raiz, estricto=True), "trabajos.jsonl"))
        # --- la corrida final ---
        res, rutas = correr_final(raiz, exigir_semillas=False)
        ok(all(os.path.exists(r) for r in rutas) and len(rutas) == 6,
           "M05 --final escribe las 6 salidas en salidas/ (dentro de la carpeta plan3)")
        cel = {(f["celda"], f["llegadas"]): f for f in res["celdas"]}
        esperado = {("P1", "regulares"): "FUNCIONA", ("P2", "regulares"): "MEJORA",
                    ("P3", "regulares"): "EMPATA (mejora no confirmada)",
                    ("P4", "regulares"): "EMPATA (falla no confirmada)",
                    ("P5", "regulares"): "CONTRADICTORIO (no se concluye)", ("P6", "regulares"): "MEJORA",
                    ("P6e", "regulares"): "MEJORA", ("c905", "regulares"): "EMPATA", ("c1358", "regulares"): "FALLA",
                    ("c2715", "regulares"): "PENDIENTE (no convergió; provisional: MEJORA)",
                    ("r905", "regulares"): "PENDIENTE (falta fijo fino en t1r)",
                    ("r1358", "regulares"): "PENDIENTE (falta actuado ajustado en t1r)",
                    ("m3620", "regulares"): "MEJORA", ("P1", "aleatorias"): "FUNCIONA",
                    ("P3", "aleatorias"): "PENDIENTE (no convergió; provisional: FUNCIONA)",
                    ("P4", "aleatorias"): "FUNCIONA", ("P6", "aleatorias"): "FUNCIONA",
                    ("per1", "aleatorias"): "FUNCIONA", ("mix1", "aleatorias"): "FUNCIONA",
                    ("mixa1", "aleatorias"): "FUNCIONA"}
        for k, v in esperado.items():
            ok(cel[k]["etiqueta_v2_citable"] == v,
               f"M06 {k[0]} {k[1]}: etiqueta citable de V2 {cel[k]['etiqueta_v2_citable']} (esperada {v})")
        f = cel[("D", "regulares")]
        ok(f["etiqueta_v2_citable"] == "MEJORA" and palabra(f["etiqueta_citable"]) == "PENDIENTE"
           and "promoción" in f["etiqueta_citable"],
           f"M07 D: veto del actuado ajustado (V2 MEJORA) y sin decisión de promoción el citado queda "
           f"{f['etiqueta_citable']}")
        f = cel[("P1", "regulares")]
        ok(f["modelo_citado"] == "observación nueva" and f["promovido"] == "sí" and f["etiqueta_citable"] == "FUNCIONA"
           and "El modelo citado no es IPPO" in f["lecturas"],
           f"M08 P1: la promoción (p3_promocion, -3 % en la validación) cita la observación nueva "
           f"({f['etiqueta_citable']}) con la etiqueta de V2 al lado")
        f = cel[("P6", "regulares")]
        ok(f["repite_T1"] == "4 de 5" and "diluido" in f["lecturas"], f"M09 P6: se repite en {f['repite_T1']} y lleva "
                                                                       f"la lectura de la espera de inserción")
        f = cel[("m3620", "regulares")]
        ok(f["igual_ciclo_minimo"] == "sí" and "Reproduce el ciclo mínimo" in f["lecturas"],
           "M10 m3620: V2 igual al ciclo mínimo -> 'Reproduce el ciclo mínimo'")
        f = cel[("P3", "aleatorias")]
        ok(f["prob_pendiente_ruido"] == "no medido" and cel[("P6", "regulares")]["prob_pendiente_ruido"] == "~10 %",
           "M11 probabilidad de PENDIENTE por ruido de §6 junto a la celda")
        f = cel[("P4", "aleatorias")]
        ok(f["repite_T1"] == "3 de 5" and f["version_evaluada"] == 42,
           "M11b P4 aleatoria con dos bases caídas declaradas: n del diseño (5), se repite en 3 de 5 y la versión "
           "evaluada sale de las que quedan")
        f = cel[("P2", "aleatorias")]
        ok("Deja vehículos sin entrar al cierre" in f["lecturas"] and "fijo fino en t1a: 3 de 10 semillas, 120 "
                                                                       "vehículos" in f["lecturas"],
           "M11c P2 aleatoria: el fijo fino deja vehículos sin entrar y la celda lleva la lectura obligada de §4")
        noins = [x for x in res["no_insertados"] if x["celda"] == "P2" and x["llegadas"] == "aleatorias"]
        ok(len(noins) > 20 and sum(x["vehiculos_no_insertados"] for x in noins) == 120,
           f"M11d veredicto3_no_insertados.csv: una fila por tanda y brazo ({len(noins)} en P2 aleatoria)")
        hip = {}
        for r in res["hipotesis"]:
            hip.setdefault((r["id"], r["familia"], r["caso"]), r)
        g = hip[("H1", "H1 global", "global")]
        ok(g["pasa"] == "no" and "P5 es peor en T2x (+" in g["nota"],
           f"M12 H1 global por intersección-unión: no pasa, y nombra la tanda que es peor con su cifra ({g['nota']})")
        x = hip[("H1", "H1", "P5")]
        ok(x["lectura_1"] == "no es peor" and x["lectura_2"] == "es peor" and x["lectura"].startswith("contradictorio"),
           f"M13 H1 en P5: T1 {x['lectura_1']}, T2 {x['lectura_2']} -> {x['lectura']}")
        ok(all(hip[("H1", "H1", c)]["lectura"] == "no es peor" for c in ("P1", "P2", "P3", "P4", "P6")) and
           hip[("H1", "H1", "P1")]["semillas_1"] == 20 and hip[("H1", "H1", "P1")]["sentido_1"] == "",
           "M14 H1 en los otros casos: no es peor, con T1 = t1r + h1t1 y sin sentido entre entrenamientos (AMB-8)")
        ok(all(hip[("H2", "H2", c)]["pasa"] == "sí" for c in ("P4", "m6525")), "M15 H2 pasa en P4 y m6525 (3 de 3)")
        ok(hip[("H3", "H3", "P6")]["pasa"] == "sí" and hip[("H3e", "H3e", "P6e")]["lectura"].endswith(
            "(hacen falta 4)"), "M16 H3 pasa con una base en contra (4 de 5); H3e, con dos en contra, no alcanza el "
                                "sentido")
        ok(hip[("H5", "H5", "global")]["pasa"] == "sí" and "4 de 6" in hip[("H5", "H5", "global")]["lectura"],
           f"M17 H5 (P4 no cuenta: 3 de 5 bases, dos caídas): {hip[('H5', 'H5', 'global')]['lectura']}")
        h6r = {c: hip[("H6", "H6", c)]["pasa"] for c in CASOS6}
        ok(h6r == {"P1": "no", "P2": "no", "P3": "sí", "P4": "no", "P5": "sí", "P6": "sí"}, f"M18 H6 por caso: {h6r}")
        x = hip[("H7r", "H7r", "P6")]
        ok(hip[("H7r", "H7r", "P1")]["pasa"] == "sí" and x["pasa"] == "no" and "2 de 3" in x["nota"]
           and "la versión evaluada mejora; el método no se repite" in x["lectura"],
           "M19 H7r: pasa en P1; en P6 la versión evaluada mejora pero el sentido es 2 de 3 (lectura de §11)")
        ok(hip[("H8b", "H8b", "global")]["pasa"] == "no" and hip[("H8a", "H8a", "global")]["lectura"].startswith(
            "pasa en 3 de 3 casos: "), "M20 H8a pasa en 3 de 3; H8b (al menos 1 de 6) no pasa")
        ok(hip[("H12", "H12", "P2")]["lectura"].startswith("es peor (T1: es peor; T2: es peor)")
           and hip[("H12", "H12", "P6")]["lectura"] == "no es peor", "M21 H12: P2 es peor, P6 no es peor")
        ok(hip[("H10", "H10 corredor", "global")]["pasa"] == "no" and
           hip[("H10", "H10 red", "P3")]["lectura"].startswith("no se pudo correr"),
           "M22 H10 sin datos de la política por red: 'no se pudo correr', la familia conserva su tamaño y no pasa")
        ok(hip[("H15", "H15 regulares", "global")]["lectura"].startswith("pasa en 4 de 4") and
           hip[("H15", "H15 aleatorias", "global")]["lectura"] == "pasa en 0 de 6 casos: ninguno" and
           hip[("H15", "H15 regulares", "global")]["pasa"] == "sí" and
           hip[("H15", "H15 aleatorias", "global")]["pasa"] == "no",
           "M23 H15: 'pasa en k de n casos' (AMB-18; pasa = al menos un caso)")
        num = [f for f in res["numero"] if f["modelo"] == "modelo citado" and f["referencia"] == "fijo fino"
               and f["llegadas"] == "regulares" and f["tanda"] == "T1"][0]
        d = Datos(raiz)
        series = []
        for c in CASOS6:
            ck = (c, gt.CASOS[c])
            brazo = cel[(c, "regulares")]["_brazo_citado"]
            sa, sf = d.serie(ck, brazo, "T1")[0], d.serie(ck, ("ref", REF_FINO), "T1")[0]
            series.append((np.array([sa[s] for s in sorted(sa)]), np.array([sf[s] for s in sorted(sf)])))
        directo = (np.exp(np.mean([np.log(x.mean() / y.mean()) for x, y in series])) - 1) * 100
        ok(num["cambio"] == f"{round(directo, 2):.2f}" and any(f["modelo"] == "IPPO con mensajes corregido"
                                                              for f in res["numero"]),
           f"M24 número único regular T1 frente al fijo fino {num['cambio']} % = directo {directo:.2f} %; con un "
           f"promovido se agrega el de V2")
        num_a = [f for f in res["numero"] if f["modelo"] == "modelo citado" and f["llegadas"] == "aleatorias"]
        ok(all(f["nota"] == "provisional en P3" for f in num_a),
           "M24b número único con llegadas aleatorias: dice 'provisional en P3' (AMB-17)")
        comp = [f for f in res["comparaciones"] if f["celda"] == "m2715" and f["clave"] == "ref_franja"
                and f["tanda"] == "T1" and f["referencia"] == "fijo fino"]
        ok(comp and "no generan los mismos vehículos" in comp[0]["nota"],
           "M25 números aleatorios comunes rotos (m2715, franja): la comparación queda con su motivo")
        b = [x for x in res["bases"] if x["escenario"] == "dem_corredor_t2715" and x["familia"] == "v2reg"
             and x["base"] == 42]
        ok(b and b[0]["convergio"] == "no" and b[0]["version_evaluada"] == "sí" and b[0]["min_repetido"] == "no",
           "M26 tabla de bases: la versión evaluada de c2715 no convergió")
        cae = [x for x in res["bases"] if x["escenario"] == "poi_red_alta" and x["familia"] == "v2poi"
               and x["base"] in (14042, 16042)]
        ok(any(x["familia"] == "entmed" for x in res["bases"]) and any(x["familia"] == "c0med" for x in res["bases"])
           and len(cae) == 2 and all(x["estado"].startswith("caída declarada") for x in cae),
           "M27 tabla de bases: las candidatas de C0 e IPPO entregado, y las dos caídas declaradas con sus intentos")
        md = open(os.path.join(raiz, "salidas", "veredicto3.md"), encoding="utf-8").read()
        ok("Tabla del anexo" in md and "Lecturas obligadas" in md and "| P5 | regulares |" in md
           and "Vehículos sin entrar al cierre" in md, "M28 veredicto3.md tiene la tabla simple, las lecturas "
                                                         "obligadas y los vehículos sin entrar")
        av_promo = [a for a in res["avisos"] if "tanda promo" in a]
        av_gen = [a for a in res["avisos"] if "no generan los mismos vehículos" in a]
        ok(len(av_promo) == 1 and len(av_gen) == 1 and av_gen[0].startswith("m2715") and len(res["avisos"]) == 2,
           f"M28b avisos: una sola línea para la tanda promo ({av_promo[0] if av_promo else '-'}) y la de m2715")
        ok("se cita observación nueva (promovido" in md and "en la tanda 1 y" in md and
           "frente al plan fijo entregado" in md,
           "M28c el .md trae la promoción de cada celda y el número único con las dos tandas y el fijo entregado (§17)")
        filas_h = {(r["id"], r["caso"], r["llegadas"], r["a"]): r for r in res["hipotesis"]}
        a3 = [r for r in res["hipotesis"] if r["id"] == "a3"]
        a3_p1 = [r for r in a3 if r["caso"] == "P1" and r["lectura"] == "mayor"]
        a3_no = [r for r in a3 if r["lectura"].startswith("no se pudo correr")]
        ok(len(a3) == 2 * 2 * (6 + 6) and len(a3_p1) == 8 and len(a3_no) == len(a3) - 8,
           f"M28d a3: {len(a3)} filas; en P1 las 8 perturbadas pierden frente a la misma versión; el resto 'no se pudo "
           f"correr'")
        pm = [r for r in res["hipotesis"] if r["id"] == "Perfil y mezcla"]
        ok(any(r["caso"] == "per1" and r["lectura"] == "citable FUNCIONA" and "fijo por bloques" in r["nota"]
               for r in pm) and sum(1 for r in pm if r["lectura"] == "no se pudo correr") == 3,
           "M28e perfil, mezcla y arranque lento: per1, mix1 y mixa1 con su etiqueta (per1 con el fijo por bloques al "
           "lado); per3, mix3 y mixa3 'no se pudo correr'")
        c0a = [r for r in res["hipotesis"] if r["id"] == "C0 aleatorio" and r["b"].startswith("IPPO con mensajes "
                                                                                              "corregido de 3 bases")]
        ok(len(c0a) == 6 and all(r["lectura"] == "menor" for r in c0a),
           "M28f C0 aleatorio frente a la V2 regular de 42/2042/4042 jugada con llegadas aleatorias (v2reg3poi)")
        ok(filas_h.get(("H1", "global", "regulares", "V2")) is not None, "M28g la fila global de H1 está")
        # una celda sin modelo principal no desaparece (y en --final es ERROR)
        d = Datos(raiz)
        d.celdas[("zz", "poi_zz")] = {"llegadas": "aleatorias", "tipos": {"ref_fino": {}}}
        fila = fila_celda(d, ("zz", "poi_zz"))
        ok(palabra(fila["etiqueta_citable"]) == "PENDIENTE" and any("zz" in a for a in d.avisos),
           "M28h una celda sin modelo principal: fila PENDIENTE con motivo y aviso")
        d.estricto = True
        negarse("M28i en --final, una celda sin modelo principal: ERROR", lambda: fila_celda(d, ("zz", "poi_zz")),
                "no tiene modelo principal")
        escribir(os.path.join(SALIDA_PRUEBAS, "ejemplo_veredicto3.md"),
                 texto_md(res, " — EJEMPLO CON DATOS SINTÉTICOS (veredicto3.py --probar), no son resultados"))
        # version publicada inconsistente con la mediana -> ERROR
        rel = "politica_corredor_alta_vecinos_p3v2reg3med.json"
        meta = leer_json(os.path.join(raiz, rel))
        con_cambio(rel, json.dumps(dict(meta, base_elegida=2042)), lambda: negarse(
            "M29 una versión publicada que no es la mediana: ERROR",
            lambda: Datos(raiz).serie(("P2", "corredor_alta"), ("ver", "v2reg", 3), "T1x"), "mediana"))
        rel = "ciego/t2r/eval_red__v2reg_s42.csv"
        texto = open(os.path.join(raiz, rel), encoding="utf-8").read()
        ultima = texto.strip().splitlines()[-1]
        con_cambio(rel, texto + ultima.replace("424320", "424399") + "\n", lambda: negarse(
            "M30 un CSV con una semilla de más: ERROR",
            lambda: Datos(raiz).serie(("P3", "red"), ("ver", "v2reg", None), "T2"), "sobran [424399]"))
        rel = "promocion/corredor_alta.json"
        texto = open(os.path.join(raiz, rel), encoding="utf-8").read()
        con_cambio(rel, texto.replace("false", "true"), lambda: negarse(
            "M31 una decisión de promoción con otro sha256 que el registrado: ERROR",
            lambda: Datos(raiz).citado(("P2", "corredor_alta"), "v2reg"), "sha256"))
        # --- prueba final: tanda de uso 'final' (simulada con humo), todo validado antes del candado exclusivo ---
        gt.TANDAS["f1r"] = ("final", SEMILLAS_PRUEBA["t1r"])
        try:
            extra = []
            for e in manifiesto:
                if e["celda"] == "P1" and e["escenario"] == "corredor" and e["tanda"] == "t1r" and (
                        (e["tipo"], e["base"]) in (("v2reg", 42), ("ref_fino", ""))):
                    f_ = dict(e, tanda="f1r", csv=e["csv"].replace("/t1r/", "/f1r/"))
                    escribir(os.path.join(raiz, f_["csv"]), open(os.path.join(raiz, e["csv"]),
                                                                 encoding="utf-8").read())
                    extra.append(f_)
            escribir(os.path.join(raiz, "cola", "manifiesto_esperado.json"), json.dumps(manifiesto + extra, indent=0))
            sellar_mundo(raiz, manifiesto + extra)
            d = Datos(raiz)
            ok(any("tanda f1r" in a and "prueba final" in a for a in d.avisos),
               "M32 los CSV de una tanda de uso 'final' no entran al veredicto (una línea de aviso)")
            comprobar_cierre(raiz)
            ok(True, "M32b comprobar_cierre no exige el sello de la prueba final (uso 'final')")
            lista = escribir(os.path.join(raiz, "listo", "lista_final.json"), json.dumps(
                {"comparaciones": [{"celda": "P1", "escenario": "corredor", "tanda": "f1r",
                                    "a": {"tipo": "v2reg", "base": 42}, "b": {"tipo": "ref_fino"}}]}))
            negarse("M33 prueba final sin listo/holdout.ok: se niega",
                    lambda: correr_prueba_final(lista, raiz, exigir_semillas=False), "holdout.ok")
            escribir(os.path.join(raiz, "listo", "holdout.ok"), "0" * 64 + "\n")
            negarse("M33b holdout.ok sin el sha256 de la lista: se niega",
                    lambda: correr_prueba_final(lista, raiz, exigir_semillas=False), "sha256")
            escribir(os.path.join(raiz, "listo", "holdout.ok"), sha256(lista) + "\n")
            candado = os.path.join(raiz, "listo", "holdout.candado")
            negarse("M33c con exigir_semillas, una tanda 'final' sin el bloque completo de su tipo de llegadas: se "
                    "niega", lambda: correr_prueba_final(lista, raiz, exigir_semillas=True), "bloque completo")
            rel_f = next(x["csv"] for x in extra if x["tipo"] == "ref_fino")
            texto_f = open(os.path.join(raiz, rel_f), encoding="utf-8").read()
            lineas_f = texto_f.splitlines()
            campos_f = lineas_f[0].split(",")
            vacia = lineas_f[1].split(",")
            vacia[campos_f.index(METRICA)] = ""
            con_cambio(rel_f, "\n".join([lineas_f[0], ",".join(vacia)] + lineas_f[2:]) + "\n", lambda: negarse(
                "M33d una métrica vacía: ERROR antes de cerrar el candado",
                lambda: correr_prueba_final(lista, raiz, exigir_semillas=False), "vacio"))
            otro = lineas_f[1].split(",")
            otro[campos_f.index("generados")] = str(int(otro[campos_f.index("generados")]) + 1)
            con_cambio(rel_f, "\n".join([lineas_f[0], ",".join(otro)] + lineas_f[2:]) + "\n", lambda: negarse(
                "M33e otros vehículos en una semilla: ERROR antes de cerrar el candado",
                lambda: correr_prueba_final(lista, raiz, exigir_semillas=False), "mismos vehículos"))
            ok(not os.path.exists(candado), "M33f ninguna de esas negativas cerró el candado")
            filas = correr_prueba_final(lista, raiz, exigir_semillas=False)
            reg = leer_json(candado)
            ok(len(filas) == 1 and "una tanda" in filas[0]["nota"] and len(reg["csv"]) == 2 and
               list(reg["salida"].values())[0] == sha256(os.path.join(raiz, "salidas", "veredicto3_prueba_final.csv")),
               "M34 la prueba final corre una vez; el candado guarda el sha256 de la lista, de cada CSV y de la salida")
            negarse("M34b no corre una segunda vez", lambda: correr_prueba_final(lista, raiz, exigir_semillas=False),
                    "ya corrió")
        finally:
            del gt.TANDAS["f1r"]
        # tercera manana con un sha256 distinto para un CSV ya registrado: --final se niega
        man_c = leer_json(os.path.join(raiz, "cola", "manifiesto_ciego.json"))
        clave_c = sorted(man_c)[0]
        man_c[clave_c] = dict(man_c[clave_c], sha256="f" * 64)
        escribir(os.path.join(raiz, "cola", "manifiesto_ciego.json"), json.dumps(man_c, indent=1, sort_keys=True))
        for args in (("add", "cola/manifiesto_ciego.json"), ("commit", "-q", "-m", "manana 3")):
            protecciones.git(*args, cwd=raiz)
        sello_v = leer_json(os.path.join(raiz, "cola", "manifiesto_cierre.json"))
        negarse("M35 un CSV cuyo sha256 cambia de una mañana a otra: se niega",
                lambda: comprobar_ciego(raiz, sello_v), "cambió en el manifiesto de la mañana")

    grupo("1. Pruebas del prototipo (lo entregado de plan2/, solo lectura)", prototipo)
    grupo("2. Reglas nuevas con datos por semilla fabricados", reglas)
    grupo("3. Mundo sintético de punta a punta (tmp_ver/mundo; semillas de humo)", mundo)
    rc, protegidos = protecciones.git("--no-optional-locks", "status", "--porcelain", "--ignored",
                                      "--untracked-files=all", "--", "plan2", "TESIS")
    ok(rc == 0 and not protegidos.strip(),
       f"G01 git status --porcelain --ignored -- plan2 TESIS vacío después de las pruebas (git rc {rc})")
    fallas = sum(1 for x in lineas if x.startswith("FALLA"))
    pasan = sum(1 for x in lineas if x.startswith("PASA"))
    lineas.append(f"=== {pasan} pasan, {fallas} fallan")
    escribir(os.path.join(SALIDA_PRUEBAS, "prueba_veredicto3.txt"), "\n".join(lineas) + "\n")
    print("\n".join(lineas))
    return fallas == 0


def main():
    ap = argparse.ArgumentParser(description="Veredicto del bloque plan3 (prerregistro §7-§14).")
    modo = ap.add_mutually_exclusive_group(required=True)
    modo.add_argument("--probar", action="store_true", help="pruebas con datos sinteticos y con lo entregado")
    modo.add_argument("--final", action="store_true", help="el veredicto (exige listo/cierre.ok y el sello)")
    modo.add_argument("--prueba-final", metavar="LISTA", help="prueba final reservada (exige listo/holdout.ok)")
    a = ap.parse_args()
    try:
        if a.probar:
            sys.exit(0 if probar() else 1)
        if a.final:
            res, rutas = correr_final()
            for r in rutas:
                print("escrito", os.path.relpath(r, PLAN3))
            for f in res["numero"]:
                print(f"numero unico {f['llegadas']} {f['tanda']} {f['modelo']} frente al {f['referencia']}: "
                      f"{f['cambio'] or f['nota']} {f['ic']}")
            return
        filas = correr_prueba_final(os.path.abspath(a.prueba_final))
        print(f"prueba final: {len(filas)} comparaciones en salidas/veredicto3_prueba_final.csv")
    except ErrorVeredicto as ex:
        sys.exit(f"veredicto3: {ex}")


if __name__ == "__main__":
    main()
