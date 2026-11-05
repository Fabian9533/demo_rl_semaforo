"""
generar_trabajos3.py - Escribe cola/trabajos.jsonl con los trabajos del bloque plan3 (PLAN3 0.18; DECISIONES B20).

Uso (desde plan3/):  python generar_trabajos3.py [--partes etapa1,...] [--seco] [--comprobar]
  --partes     partes a incluir (por defecto, todas las que ya tienen codigo; ver PARTES)
  --seco       no escribe: muestra cuantos trabajos y cuantas h-proceso por etapa
  --comprobar  sale con 1 si cola/trabajos.jsonl o cola/manifiesto_esperado.json no son lo que este script
               generaria (lo usa chequeos_previos)
Escribe tambien cola/manifiesto_esperado.json: una entrada por CSV de evaluacion esperado (celda, escenario, tanda,
clave del brazo, tipo, base, semillas y trabajo que lo produce). Lo usan manifiesto.py y veredicto3.py.

Cada trabajo declara: id, prioridad (menor = antes), cpus, requiere, cmd (cwd = plan3/), salidas (la cola lo da por
hecho solo si existen y son nuevas), duracion (s estimados, regimen conservador + 10 %), uso (bloque de semillas del
prerregistro §3), etapa y, en los tramos de un mismo entrenamiento, cadena.
Los entrenamientos de mas de 5 h se parten en tramos con --hasta-ep; todos llevan --reanudar auto, asi que un trabajo
caido se relanza con el mismo comando y sigue desde su ultimo estado (DECISIONES B15 y B22).
Regenerar el archivo deja los mismos ids: la cola no repite lo hecho.
"""
import os
import re
import sys
import json
import argparse

PLAN3 = os.path.dirname(os.path.abspath(__file__))
TRABAJOS = os.path.join(PLAN3, "cola", "trabajos.jsonl")
MANIFIESTO = os.path.join(PLAN3, "cola", "manifiesto_esperado.json")
PARTES_TXT = os.path.join(PLAN3, "cola", "partes.txt")       # partes con que se escribio la lista (para --comprobar)
LANZADOR = "python ../con_escenarios.py"

# ---------------- Celdas ----------------
CASOS = {"P1": "corredor", "P2": "corredor_alta", "P3": "red", "P4": "red_alta", "P5": "malla3",
         "P6": "malla3_alta"}
NIVELES = {"c905": "dem_corredor_t905", "c1358": "dem_corredor_t1358", "c2715": "dem_corredor_t2715",
           "r905": "dem_red_t905", "r1358": "dem_red_t1358", "r1810": "dem_red_t1810", "r2715": "dem_red_t2715",
           "r3620": "dem_red_t3620", "m1810": "dem_malla3_t1810", "m2715": "dem_malla3_t2715",
           "m3620": "dem_malla3_t3620", "m6525": "dem_malla3_t6525"}
D = {"D": "dem_corredor_t2715_der"}
P6E = {"P6e": "malla3_alta_e"}
POI = {c: f"poi_{e}" for c, e in CASOS.items()}
# Perfil de 10 min y mezcla de Lima (A7), en P1 y P3, con llegadas aleatorias; mixa_ = mezcla con arranque lento,
# solo para evaluar (escenarios_plan3.ESTOCASTICOS).
PERFIL = {"per1": "per_corredor", "per3": "per_red"}
MEZCLA = {"mix1": "mix_corredor", "mix3": "mix_red"}
MEZCLA_A = {"mixa1": "mixa_corredor", "mixa3": "mixa_red"}
ORIGEN_A = {"mixa1": "mix_corredor", "mixa3": "mix_red"}     # mixa_ juega lo de mix_

BASES5 = [42, 2042, 4042, 14042, 16042]
BASES3 = [42, 2042, 4042]
VAL16 = [999, 1999, 2999, 3999, 4999, 7999, 8999, 9999] + list(range(15001, 15009))
VAL = ",".join(str(s) for s in VAL16)
EPISODIOS = 200
EVAL_CADA = 10
TRAMO_MAX_S = 5 * 3600
EMPAQUE = 1.10

# s por episodio de entrenamiento y por episodio de validacion (una semilla), regimen conservador
# [M analisis_mejora_2026-11-04/plan3/final/costos_plan3.py, TR, medido la noche del plan v2]
TR = {"P1": (6.0, 4.8), "P2": (14.0, 11.9), "P3": (9.3, 7.6), "P4": (10.2, 8.4), "P5": (25.2, 19.6),
      "P6": (50.6, 42.6), "P6e": (50.6, 42.6),
      "c905": (5.0, 3.8), "c1358": (5.4, 4.2), "c2715": (8.1, 6.6),
      "r905": (7.4, 5.6), "r1358": (8.1, 6.3), "r1810": (8.9, 7.1), "r2715": (10.8, 9.1), "r3620": (14.1, 12.1),
      "m1810": (20.0, 14.8), "m2715": (21.5, 15.7), "m3620": (23.0, 17.4), "m6525": (29.4, 24.1),
      "D": (5.7, 4.8)}
TR.update({"per1": TR["P1"], "per3": TR["P3"], "mix1": TR["P1"], "mix3": TR["P3"]})
POI_F = 1.07            # llegadas aleatorias frente a regulares [M +3 a +13 %]


def nombre_corrida(esc, variante, etiqueta, base):
    return f"{esc}_ippo_{variante}_{etiqueta}_s{base}"


def duracion_entreno(celda, episodios=EPISODIOS, desde=0, hasta=None, factor=1.0):
    """s estimados; factor es un numero (entrenamiento y validacion) o un par (entrenamiento, validacion)."""
    ftr, fval = factor if isinstance(factor, tuple) else (factor, factor)
    tr, val = TR[celda]
    hasta = episodios if hasta is None else hasta
    n_val = hasta // EVAL_CADA - desde // EVAL_CADA
    return EMPAQUE * ((hasta - desde) * tr * ftr + n_val * len(VAL16) * val * fval)


def cortes_tramos(celda, episodios=EPISODIOS, desde=0, factor=1.0):
    """Episodios donde termina cada tramo de <= 5 h (multiplos de EVAL_CADA, para cortar en un checkpoint)."""
    total = duracion_entreno(celda, episodios, desde=desde, factor=factor)
    n_tramos = max(1, -(-int(total) // TRAMO_MAX_S))
    paso = -(-(episodios - desde) // n_tramos)
    paso = -(-paso // EVAL_CADA) * EVAL_CADA
    return list(range(desde + paso, episodios, paso)) + [episodios]


class Lista:
    def __init__(self):
        self.trabajos = []
        self.ids = set()
        self.manifiesto = []            # una entrada por CSV de evaluacion esperado (lo lee veredicto3)

    def agregar(self, t):
        assert t["id"] not in self.ids, f"id repetido: {t['id']}"
        self.ids.add(t["id"])
        t.setdefault("cpus", 1)
        t.setdefault("requiere", [])
        self.trabajos.append(t)

    def entrenamiento(self, tid, etapa, prioridad, celda, esc, etiqueta, base, opciones, variante="vecinos",
                      lanzador=False, factor=1.0, requiere=(), episodios=EPISODIOS, reanudar=None):
        """Agrega un entrenamiento (en tramos si pasa de 5 h). Devuelve el id de su ultimo tramo."""
        corrida = nombre_corrida(esc, variante, etiqueta, base)
        pre = LANZADOR if lanzador else "python"
        base_cmd = (f"{pre} ../rl_ippo.py train --escenario {esc} --variante {variante} --seed {base} "
                    f"--episodios {episodios} --eval-cada {EVAL_CADA} --val-seeds {VAL} --criterio-val total "
                    f"--guardar-estado --registro-extendido --etiqueta {etiqueta} {opciones}").strip()
        desde, ruta_origen = 0, None
        if reanudar:                         # etiqueta nueva desde un estado de otra corrida (p. ej. 3b)
            ruta_origen, desde = reanudar
        cortes = cortes_tramos(celda, episodios, desde, factor)
        previo, inicio = list(requiere), desde
        for k, fin in enumerate(cortes):
            ultimo = fin == episodios
            # el primer tramo de una etiqueta nueva parte del estado de origen; los demas, de su propio ultimo estado
            cmd = base_cmd + (f" --reanudar {ruta_origen}" if ruta_origen and k == 0 else " --reanudar auto")
            if not ultimo:
                cmd += f" --hasta-ep {fin}"
            salidas = ([f"politica_{esc}_{variante}_{etiqueta}_s{base}.pt",
                        f"resultados_{corrida}.csv"] if ultimo
                       else [f"checkpoints/{corrida}_ep{fin:03d}.estado.pt"])
            sufijo = "" if len(cortes) == 1 else f"_t{k + 1}"
            self.agregar({"id": tid + sufijo, "etapa": etapa, "prioridad": prioridad, "cmd": cmd,
                          "requiere": previo, "salidas": salidas, "uso": "entrenamiento", "cadena": corrida,
                          "duracion": round(duracion_entreno(celda, episodios, inicio, fin, factor))})
            previo, inicio = [f"trabajo:{tid + sufijo}"], fin
        return tid + ("" if len(cortes) == 1 else f"_t{len(cortes)}")


# ---------------- Etapa 1: V2 con llegadas regulares, ablacion y sin mensajes (PLAN3 1.3 y 1.5) ----------------

def etapa1(lista):
    v2 = "--v2"
    celdas = []
    for c, e in CASOS.items():
        celdas += [(c, e, b) for b in BASES5]
    for c, e in NIVELES.items():
        celdas += [(c, e, b) for b in (BASES5 if c == "c2715" else BASES3)]       # B23: 2715 con 5 bases
    for c, e in D.items():
        celdas += [(c, e, b) for b in BASES5]
    # lo mas largo primero, para que la cola no termine con un solo proceso
    for c, e, b in sorted(celdas, key=lambda x: -duracion_entreno(x[0])):
        lista.entrenamiento(f"e1_v2reg_{e}_s{b}", "1", 2, c, e, "p3v2reg", b, v2)
    for c in ("P4", "P6"):                                                    # 1.5 ablacion de V2
        for et, op in (("p3sd", "--solo-descuento"), ("p3se", "--solo-exploracion")):
            for b in BASES3:
                lista.entrenamiento(f"e1_{et}_{CASOS[c]}_s{b}", "1", 3, c, CASOS[c], et, b, op)
    for c in ("P1", "P2", "P6"):                                              # 1.5 V2 sin mensajes
        for b in BASES3:
            lista.entrenamiento(f"e1_v2loc_{CASOS[c]}_s{b}", "1", 3, c, CASOS[c], "p3v2reg", b, v2,
                                variante="local")


# ---------------- Etapa 1: control C0 (PLAN3 1.4) ----------------
C0_MAX_S = 3600          # trabajos de <= 1 h: la validacion de P6 con 16 semillas son ~11 min por checkpoint


def c0(lista, celdas=None, etiqueta="p3c0", origen="insumos/c0_checkpoints", fuente=None, etapa="1", requiere=None,
       uso_poi=False):
    """Re-valida con las 16 semillas los 20 checkpoints de cada base y publica el elegido por retraso total.
    celdas: {celda: escenario de evaluacion}; fuente(celda, base) -> nombre de la corrida de origen."""
    celdas = celdas or {**CASOS, **NIVELES}
    fuente = fuente or (lambda c, b: f"{celdas[c]}_ippo_vecinos_s{b}")
    for c, esc in celdas.items():
        por_ckpt = EMPAQUE * len(VAL16) * TR[c][1] * (POI_F if uso_poi else 1.0)
        n = max(1, int(C0_MAX_S // por_ckpt))
        eps = list(range(EVAL_CADA, EPISODIOS + 1, EVAL_CADA))
        grupos = [eps[i:i + n] for i in range(0, len(eps), n)]
        for b in BASES3:
            corrida = fuente(c, b)
            pre = LANZADOR if uso_poi else "python"
            partes = []
            for k, g in enumerate(grupos):
                tid = f"c0_{etiqueta}_{esc}_s{b}_g{k + 1}"
                salida = f"parciales/c0/{etiqueta}_{esc}_s{b}_g{k + 1}.json"
                lista.agregar({"id": tid, "etapa": etapa, "prioridad": 2, "uso": "validacion",
                               "requiere": list(requiere(c, b)) if requiere else [],
                               "cmd": f"{pre} revalidar_c0.py validar --escenario {esc} --origen {origen} "
                                      f"--corrida {corrida} --eps {','.join(map(str, g))} --val-seeds {VAL} "
                                      f"--salida {salida}",
                               "salidas": [salida], "duracion": round(por_ckpt * len(g))})
                partes.append((tid, salida))
            lista.agregar({"id": f"c0_{etiqueta}_{esc}_s{b}_publicar", "etapa": etapa, "prioridad": 2,
                           "uso": "sin_semillas", "requiere": [f"trabajo:{t}" for t, _ in partes],
                           "cmd": f"{pre} revalidar_c0.py publicar --escenario {esc} --origen {origen} "
                                  f"--corrida {corrida} --entradas {','.join(s for _, s in partes)} "
                                  f"--etiqueta {etiqueta}",
                           "salidas": [f"politica_{esc}_vecinos_{etiqueta}_s{b}.pt"], "duracion": 30})


def id_entreno(prefijo, esc, base, celda, episodios=EPISODIOS, desde=0, factor=1.0):
    """Id del ultimo tramo de un entrenamiento (el que publica la politica), sin agregarlo. Usa los mismos cortes que
    Lista.entrenamiento (revision del 05.11: con dos calculos podian no coincidir)."""
    n = len(cortes_tramos(celda, episodios, desde, factor))
    return f"{prefijo}_{esc}_s{base}" + ("" if n == 1 else f"_t{n}")


# ---------------- Etapa 2: llegadas aleatorias y P6e (PLAN3 1.3, 2.1 y 2.2) ----------------

def etapa2(lista):
    v2 = "--v2"
    for c, e in P6E.items():                                                  # P6e: V2 regular, 5 bases
        for b in BASES5:
            lista.entrenamiento(f"e2_v2reg_{e}_s{b}", "2", 2, c, e, "p3v2reg", b, v2, lanzador=True)
    trabajos = [(c, e, b, "vecinos") for c, e in POI.items() for b in BASES5]   # con mensajes, 5 bases
    trabajos += [(c, e, b, "local") for c, e in POI.items() for b in BASES3]    # sin mensajes, 3 bases
    for c, e, b, var in sorted(trabajos, key=lambda x: -duracion_entreno(x[0])):
        pref = "e2_v2poi" if var == "vecinos" else "e2_v2poiloc"
        lista.entrenamiento(f"{pref}_{e}_s{b}", "2", 2, c, e, "p3v2poi", b, v2, variante=var, lanzador=True,
                            factor=POI_F)
    # 2.2 C0 con llegadas aleatorias: los checkpoints de la V2 regular re-validados con llegadas aleatorias
    # (en P6, los de P6e, para no mezclar el cambio de entrada).
    origen_reg = {c: (P6E["P6e"] if c == "P6" else CASOS[c]) for c in CASOS}
    celda_reg = {c: ("P6e" if c == "P6" else c) for c in CASOS}

    def requiere(c, b):
        pref = "e2_v2reg" if c == "P6" else "e1_v2reg"
        return [f"trabajo:{id_entreno(pref, origen_reg[c], b, celda_reg[c])}"]
    c0(lista, celdas=POI, etiqueta="p3c0poi", origen="checkpoints", etapa="2", requiere=requiere, uso_poi=True,
       fuente=lambda c, b: f"{origen_reg[c]}_ippo_vecinos_p3v2reg_s{b}")


# ---------------- Etapa 3b: 400 episodios, reanudando desde el 180 (PLAN3 3b; A4) ----------------
DESDE_3B = 180


def etapa2pm(lista):
    """2.4 y 2.5: V2 entrenada con el perfil y con la mezcla (3 bases), con llegadas aleatorias."""
    for celdas, et, f in ((PERFIL, "p3v2per", POI_F), (MEZCLA, "p3v2mix", POI_F * 1.10)):
        for c, e in celdas.items():
            for b in BASES3:
                lista.entrenamiento(f"e2_{et}_{e}_s{b}", "2", 3, c, e, et, b, "--v2", lanzador=True, factor=f)


def etapa3b(lista, tipos=("reg", "poi")):
    op = "--v2 --lr-horizonte 200 --lr-piso 0.1"
    for tipo, celdas, et_v2, et, pref_v2 in (("reg", CASOS, "p3v2reg", "p3e400", "e1_v2reg"),
                                            ("poi", POI, "p3v2poi", "p3e400poi", "e2_v2poi")):
        if tipo not in tipos:
            continue
        for c, e in celdas.items():
            f = POI_F if tipo == "poi" else 1.0
            for b in BASES3:
                origen = nombre_corrida(e, "vecinos", et_v2, b)
                ult = lista.entrenamiento(
                    f"e3b_{et}_{e}_s{b}", "3b", 3, c, e, et, b, op, lanzador=(tipo == "poi"), factor=f,
                    episodios=400, reanudar=(f"checkpoints/{origen}_ep{DESDE_3B:03d}.estado.pt", DESDE_3B),
                    requiere=[f"trabajo:{id_entreno(pref_v2, e, b, c, factor=f)}"])
                corrida = nombre_corrida(e, "vecinos", et, b)
                for regla, et_r in (("piso200", f"p3piso200{tipo}"), ("cada20", f"p3e400c20{tipo}")):
                    lista.agregar({"id": f"e3b_elegir_{et_r}_{e}_s{b}", "etapa": "3b", "prioridad": 3,
                                   "uso": "sin_semillas", "requiere": [f"trabajo:{ult}"],
                                   "cmd": f"python p3_elegir.py regla --escenario {e} --corrida {corrida} "
                                          f"--regla {regla} --etiqueta {et_r}",
                                   "salidas": [f"politica_{e}_vecinos_{et_r}_s{b}.pt"], "duracion": 10})


# ---------------- Etapa 1: V2 vieja (regla del 25.09 sobre los checkpoints de V2; PLAN3 1.6) ----------------

def v2vieja(lista):
    for c, e in {**CASOS, **NIVELES}.items():
        for b in BASES3:
            lista.agregar({"id": f"e1_elegir_p3v2vieja_{e}_s{b}", "etapa": "1", "prioridad": 2,
                           "uso": "sin_semillas",
                           "requiere": [f"trabajo:{id_entreno('e1_v2reg', e, b, c)}"],
                           "cmd": f"python p3_elegir.py regla --escenario {e} "
                                  f"--corrida {nombre_corrida(e, 'vecinos', 'p3v2reg', b)} --regla vieja "
                                  f"--etiqueta p3v2vieja",
                           "salidas": [f"politica_{e}_vecinos_p3v2vieja_s{b}.pt"], "duracion": 10})


# ---------------- Etapa 3: observacion nueva, limpiezas, entropia, reloj de 2 s y modelo completo (PLAN3 3.6) ----------
# Factores de duracion [S, analisis_mejora_2026-11-04/plan3/final/costos_plan3.py]: observacion x1.35; reloj de 2 s
# x1.4 al entrenar y x1.15 al validar.
OBS, RELOJ_TR, RELOJ_VAL = 1.35, 1.40, 1.15
OP_OBS = "--obs-cercana 75"
OP_M7 = "--norm-valor --sin-forzadas --msg-cada-paso"
OP_ENT = "--hiper ent=0.03 --ent-final 0.003"
OP_RELOJ = "--paso-decision 2 --sin-forzadas"
OP_COMPLETO = ("--obs-cercana 75 --norm-valor --sin-forzadas --msg-cada-paso --lr-horizonte 200 --lr-piso 0.1 "
               "--paso-decision 2")


def etapa3(lista):
    """Cada brazo = (etiqueta, opciones ademas de --v2, celdas, bases, factor, episodios). D entra primero."""
    reg = {**CASOS, **NIVELES, **D}
    brazos = [
        ("p3obs", OP_OBS, {"D": D["D"], "c2715": NIVELES["c2715"]}, BASES5, OBS, EPISODIOS),
        ("p3obs", OP_OBS, {c: CASOS[c] for c in ("P1", "P2", "P3", "P6")}, BASES3, OBS, EPISODIOS),
        ("p3obspoi", OP_OBS, POI, BASES3, (OBS * POI_F, OBS * POI_F), EPISODIOS),
        ("p3m7norm", "--norm-valor", D, BASES3, 1.0, EPISODIOS),
        ("p3m7forz", "--sin-forzadas", D, BASES3, 1.0, EPISODIOS),
        ("p3m7msg", "--msg-cada-paso", D, BASES3, 1.0, EPISODIOS),
        ("p3m7", OP_M7, {"D": D["D"], "P2": CASOS["P2"], "P6": CASOS["P6"]}, BASES3, 1.0, EPISODIOS),
        ("p3ent", OP_ENT, {"D": D["D"], "P1": CASOS["P1"]}, BASES3, 1.0, EPISODIOS),
        ("p3reloj2", OP_RELOJ, {c: reg[c] for c in ("D", "P1", "P2", "P6")}, BASES3, (RELOJ_TR, RELOJ_VAL),
         EPISODIOS),
        ("p3reloj2poi", OP_RELOJ, {c: POI[c] for c in ("P1", "P2", "P6")}, BASES3,
         (RELOJ_TR * POI_F, RELOJ_VAL * POI_F), EPISODIOS),
        ("p3completo", OP_COMPLETO, {c: CASOS[c] for c in ("P1", "P2", "P4", "P6")}, BASES3,
         (OBS * RELOJ_TR, OBS * RELOJ_VAL), 400),
        ("p3completopoi", OP_COMPLETO, POI, BASES3, (OBS * RELOJ_TR * POI_F, OBS * RELOJ_VAL * POI_F), 400),
    ]
    trabajos = []
    for et, op, celdas, bases, f, eps in brazos:
        for c, e in celdas.items():
            for b in bases:
                trabajos.append((et, op, c, e, b, f, eps))
    # D primero (prioridad 2); el resto, lo mas largo primero (prioridad 3)
    trabajos.sort(key=lambda x: (x[2] != "D", -duracion_entreno(x[2], x[6], factor=x[5])))
    for et, op, c, e, b, f, eps in trabajos:
        lista.entrenamiento(f"e3_{et}_{e}_s{b}", "3", 2 if c == "D" else 3, c, e, et, b, f"--v2 {op}",
                            lanzador=e.startswith("poi_"), factor=f, episodios=eps)


# ---------------- Evaluaciones (PLAN3 1.6, 2.3, 3.6 y 3b; prerregistro §3, §7 y §12) ----------------
# tanda -> (uso del prerregistro, semillas). Las decisivas escriben en ciego/; las demas en parciales/.
TANDAS = {"t1r": ("examen_regular", "8001-8030"), "t2r": ("examen_regular", "13001-13030"),
          "h1t1": ("examen_h1", "8031-8120"), "h1t2": ("examen_h1", "13031-13120"),
          "t1a": ("examen_aleatorio", "7001-7100"), "t2a": ("examen_aleatorio", "10001-10100"),
          "puente": ("puente", "1001-1030"), "promo": ("promocion", "15009-15024")}
CIEGAS = {"examen_regular", "examen_h1", "examen_aleatorio", "final"}
REGULARES, ALEATORIAS = ("t1r", "t2r"), ("t1a", "t2a")
# s por semilla al jugar una politica o una referencia (regimen conservador) [M costos_plan3.py, EV]
EV = {"P1": 5.4, "P2": 13.2, "P3": 9.0, "P4": 10.0, "P5": 23.6, "P6": 42.2, "P6e": 42.2,
      "c905": 3.6, "c1358": 4.2, "c2715": 6.6, "r905": 5.6, "r1358": 6.2, "r1810": 6.6, "r2715": 8.8,
      "r3620": 12.0, "m1810": 13.6, "m2715": 15.6, "m3620": 17.6, "m6525": 24.8, "D": 5.4}
FACTOR_EV = {"p3obs": OBS, "p3obspoi": OBS, "p3reloj2": RELOJ_VAL, "p3reloj2poi": RELOJ_VAL,
             "p3completo": OBS * RELOJ_VAL, "p3completopoi": OBS * RELOJ_VAL}


def n_semillas(texto):
    return sum(int(b) - int(a) + 1 for a, b in (p.split("-") for p in texto.split(",")))


CAIDAS_JSON = os.path.join(PLAN3, "cola", "caidas.json")
# Corridas que salen de otra: si la de origen cayo, tampoco existen (V2 vieja y 3b re-eligen o siguen la de V2).
DERIVA = {"p3v2vieja": "p3v2reg", "p3e400": "p3v2reg", "p3e400poi": "p3v2poi",
          "p3piso200reg": "p3e400", "p3e400c20reg": "p3e400", "p3piso200poi": "p3e400poi", "p3e400c20poi": "p3e400poi"}
# Tipos que no son un entrenamiento y no pueden caer por si mismos: las re-elecciones de p3_elegir regla (V2 vieja,
# piso200, cada20) y la re-validacion de C0. Se declara la corrida de la que salen. p3e400 y p3e400poi si son
# entrenamientos (siguen a V2 desde el episodio 180) y se pueden declarar.
NO_ENTRENAMIENTO = {k for k in DERIVA if k not in ("p3e400", "p3e400poi")} | {"c0"}


def corrida_de_tipo(esc, tipo, base):
    """Nombre de la corrida de una base declarada por su tipo del manifiesto (v2reg, v2poi, v2loc, p3obs...)."""
    variante = "local" if tipo in ("v2loc", "v2poiloc") else "vecinos"
    etiqueta = {"v2reg": "p3v2reg", "v2loc": "p3v2reg", "v2poi": "p3v2poi", "v2poiloc": "p3v2poi",
                "v2per": "p3v2per", "v2mix": "p3v2mix", "c0": "p3c0"}.get(tipo, tipo)
    return nombre_corrida(esc, variante, etiqueta, base)


def corrida_de_politica(ruta):
    """(escenario, variante, etiqueta, base) de la corrida de entrenamiento de una politica por base
    (politica_<esc>_<variante>_<etiqueta>_s<base>.pt), o None (lo entregado, las versiones publicadas)."""
    m = re.fullmatch(r"politica_(.+)_(vecinos|local)_(p3[a-z0-9]+)_s(\d+)\.pt", os.path.basename(ruta or ""))
    return (m.group(1), m.group(2), m.group(3), int(m.group(4))) if m else None


def validar_caida(c):
    """La corrida de una declaracion de cola/caidas.json (prerregistro §14; B22), o ValueError con el motivo. Las
    mismas reglas para el generador (leer_caidas) y para veredicto3 (caidas_de_texto). Cada declaracion lleva celda,
    escenario, tipo, base y los dos intentos fallidos con id, error y fecha (la fecha en cada intento o una vez en la
    declaracion); el escenario es el de la politica (mix_, no mixa_: el arranque lento juega la de la mezcla); el tipo
    es un entrenamiento (no una re-eleccion ni C0); la corrida, si esta, es la de ese escenario, tipo y base."""
    faltan = [k for k in ("celda", "escenario", "tipo", "base", "intentos") if k not in c]
    intentos = c.get("intentos") or []
    incompletos = any(not (isinstance(i, dict) and i.get("id") and i.get("error")
                           and (i.get("fecha") or c.get("fecha"))) for i in intentos)
    if faltan or len(intentos) < 2 or incompletos:
        raise ValueError(f"cada base caída lleva celda, escenario, tipo, base y los dos intentos fallidos con id, "
                         f"error y fecha (§14): {c}")
    if c["escenario"] in MEZCLA_A.values():
        raise ValueError(f"{c['escenario']} juega la política de la mezcla: declárela con el escenario de la "
                         f"política (mix_corredor / mix_red): {c}")
    if c["tipo"] in NO_ENTRENAMIENTO:
        origen = DERIVA.get(c["tipo"], "la de los checkpoints entregados")
        raise ValueError(f"{c['tipo']} no es un entrenamiento (sale de {origen}): declare la corrida de la que sale: "
                         f"{c}")
    esperada = corrida_de_tipo(c["escenario"], c["tipo"], int(c["base"]))
    if c.get("corrida") and c["corrida"] != esperada:
        raise ValueError(f"la corrida {c['corrida']} no es la de {c['escenario']}, {c['tipo']}, base {c['base']} "
                         f"({esperada})")
    return esperada


def leer_caidas(ruta=None):
    """Corridas declaradas caidas (falla del metodo en dos intentos; prerregistro §7 y §14): sus evaluaciones no se
    generan y las versiones evaluadas salen de las bases que quedan. cola/caidas.json = lista de
    {"corrida", "celda", "escenario", "tipo", "base", "intentos", "fecha"} (validar_caida; la corrida es opcional).
    ruta: otro caidas.json (por defecto el de plan3/cola)."""
    ruta = ruta or CAIDAS_JSON
    if not os.path.exists(ruta):
        return set()
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    lista = datos.get("caidas", []) if isinstance(datos, dict) else datos
    return {validar_caida(c) for c in lista}


CAIDAS = leer_caidas()


def caida(esc, variante, et, base, caidas=None):
    """¿Esta corrida, o aquella de la que sale, esta declarada caida? caidas: otro conjunto (por defecto CAIDAS)."""
    caidas = CAIDAS if caidas is None else caidas
    while et:
        if nombre_corrida(esc, variante, et, base) in caidas:
            return True
        et = DERIVA.get(et)
    return False


def evaluacion(lista, celda, esc, tanda, clave, brazo, requiere=(), etapa="ev", factor=1.0, tipo="",
               base="", corrida=None):
    """Un brazo en un escenario y una tanda. clave da el nombre del CSV (el brazo real lo pone evaluar3).
    corrida: (escenario, variante, etiqueta, base) del entrenamiento del que sale la politica, si es una base; si esta
    caido (o cayo aquel del que sale) no se evalua."""
    if corrida is not None and caida(*corrida):
        return None
    uso, semillas = TANDAS[tanda]
    carpeta = "ciego" if uso in CIEGAS else "parciales"
    salida = f"{carpeta}/{tanda}/eval_{esc}__{clave}.csv"
    pre = LANZADOR if esc.startswith(("poi_", "per_", "mix", "malla3_alta_e")) else "python"
    f = factor * (POI_F if esc.startswith("poi_") else 1.0)
    tid = f"ev_{tanda}_{esc}__{clave}"
    lista.agregar({"id": tid, "etapa": etapa, "prioridad": 4, "uso": uso, "requiere": list(requiere),
                   "cmd": f"{pre} evaluar3.py --escenario {esc} --semillas {semillas} --salida {salida} {brazo}",
                   "salidas": [salida], "duracion": round(EMPAQUE * f * n_semillas(semillas) * EV[celda])})
    lista.manifiesto.append({"csv": salida, "celda": celda, "escenario": esc, "tanda": tanda, "clave": clave,
                             "tipo": tipo or clave, "base": base, "semillas": semillas, "trabajo": tid})
    return tid


def mediana(lista, esc, variante, et, bases, requiere, et_med, origen="", fuente=None):
    """Paso de eleccion: la version evaluada (base mediana por val_elegido) publicada como <...>_<et_med>.pt.
    requiere va alineada con bases (o vacia); las bases caidas no entran (prerregistro §6). fuente(b) da la corrida de
    origen (escenario, variante, etiqueta) cuando no es la misma (C0 aleatorio sale de la V2 regular)."""
    var_et = f"{variante}_{et}" if et else variante          # lo entregado no lleva etiqueta: politica_<esc>_vecinos_s42
    origen_de = fuente or (lambda b: (esc, variante, et))
    vivas = [k for k, b in enumerate(bases) if not et or not caida(*origen_de(b), b)]
    requiere = [requiere[k] for k in vivas] if requiere else []
    bases = [bases[k] for k in vivas]
    rutas = ",".join(f"{origen}politica_{esc}_{var_et}_s{b}.pt" for b in bases)
    salida = f"politica_{esc}_{variante}_{et_med}.pt"
    tid = f"el_{et_med}_{esc}"
    if tid not in lista.ids:
        lista.agregar({"id": tid, "etapa": "ev", "prioridad": 2, "uso": "sin_semillas", "requiere": list(requiere),
                       "cmd": f"python p3_elegir.py mediana --politicas {rutas} --etiqueta {et_med} --salida {salida}",
                       "salidas": [salida], "duracion": 10})
    return salida, tid


def req_entreno(pref, esc, b, celda, episodios=EPISODIOS, factor=1.0, desde=0):
    return f"trabajo:{id_entreno(pref, esc, b, celda, episodios, desde=desde, factor=factor)}"


def evaluaciones(lista):
    # --- Llegadas regulares: P1-P6, niveles, D y P6e ---
    celdas_reg = {**CASOS, **NIVELES, **D, **P6E}
    for c, e in celdas_reg.items():
        pref = "e2_v2reg" if c == "P6e" else "e1_v2reg"
        bases = BASES5 if c in CASOS or c in ("c2715", "D", "P6e") else BASES3
        reqs = {b: req_entreno(pref, e, b, c) for b in bases}
        for t in REGULARES:
            for b in bases:                                                       # V2, todas las bases
                evaluacion(lista, c, e, t, f"v2reg_s{b}", f"--politica politica_{e}_vecinos_p3v2reg_s{b}.pt",
                           [reqs[b]], tipo="v2reg", base=b, corrida=(e, "vecinos", "p3v2reg", b))
            for clave, brazo in (("fijo", "--brazo fijo"), ("actuado", "--brazo actuado"),
                                 ("trivial", "--brazo trivial")):                 # referencias que ya existen
                evaluacion(lista, c, e, t, clave, brazo, ["trabajo:preparar"], tipo=f"ref_{clave}")
        if c in ("P6e", "D"):
            continue
        # version evaluada de C0, de la V2 vieja, del IPPO entregado y de V2 entre 42/2042/4042
        c0m, c0t = mediana(lista, e, "vecinos", "p3c0", BASES3,
                           [f"trabajo:c0_p3c0_{e}_s{b}_publicar" for b in BASES3], "p3c0med")
        vvm, vvt = mediana(lista, e, "vecinos", "p3v2vieja", BASES3,
                           [f"trabajo:e1_elegir_p3v2vieja_{e}_s{b}" for b in BASES3], "p3v2viejamed")
        enm, ent = mediana(lista, e, "vecinos", "", BASES3, [], "p3entmed", origen="insumos/entregado/")
        v3m, v3t = mediana(lista, e, "vecinos", "p3v2reg", BASES3, [reqs[b] for b in BASES3], "p3v2reg3med")
        for t in REGULARES:
            evaluacion(lista, c, e, t, "c0med", f"--politica {c0m}", [f"trabajo:{c0t}"], tipo="c0med")
            evaluacion(lista, c, e, t, "v2viejamed", f"--politica {vvm}", [f"trabajo:{vvt}"], tipo="v2viejamed")
            evaluacion(lista, c, e, t, "entmed", f"--politica {enm}", [f"trabajo:{ent}"], tipo="entmed")
        if c in CASOS or c == "m6525":
            # H1 y H2: 120 semillas por tanda para V2 (de 42/2042/4042), C0 e IPPO entregado
            for t in ("h1t1", "h1t2"):
                evaluacion(lista, c, e, t, "v2reg3med", f"--politica {v3m}", [f"trabajo:{v3t}"], tipo="v2reg3med")
                evaluacion(lista, c, e, t, "c0med", f"--politica {c0m}", [f"trabajo:{c0t}"], tipo="c0med")
                evaluacion(lista, c, e, t, "entmed", f"--politica {enm}", [f"trabajo:{ent}"], tipo="entmed")
        if c in ("P4", "m6525"):
            # H2: sentido por base, V2 de la base b frente a C0 de la base b, en las 120 semillas
            for b in BASES3:
                for t in ("t1r", "t2r", "h1t1", "h1t2"):
                    evaluacion(lista, c, e, t, f"c0_s{b}", f"--politica politica_{e}_vecinos_p3c0_s{b}.pt",
                               [f"trabajo:c0_p3c0_{e}_s{b}_publicar"], tipo="c0", base=b)
                for t in ("h1t1", "h1t2"):
                    evaluacion(lista, c, e, t, f"v2reg_s{b}", f"--politica politica_{e}_vecinos_p3v2reg_s{b}.pt",
                               [reqs[b]], tipo="v2reg", base=b, corrida=(e, "vecinos", "p3v2reg", b))
        if c in CASOS:
            # puente con lo entregado (descriptivo): los CSV del fijo y del IPPO entregados se reutilizan
            for clave, ruta, req in (("v2reg3med", v3m, v3t), ("v2viejamed", vvm, vvt), ("c0med", c0m, c0t)):
                evaluacion(lista, c, e, "puente", clave, f"--politica {ruta}", [f"trabajo:{req}"], tipo=clave)
    # ablacion (P4, P6) y V2 sin mensajes (P1, P2, P6), todas sus bases
    for c in ("P4", "P6"):
        e = CASOS[c]
        for et in ("p3sd", "p3se"):
            for b in BASES3:
                for t in REGULARES:
                    evaluacion(lista, c, e, t, f"{et}_s{b}", f"--politica politica_{e}_vecinos_{et}_s{b}.pt",
                               [req_entreno(f"e1_{et}", e, b, c)], tipo=et, base=b,
                               corrida=(e, "vecinos", et, b))
    for c in ("P1", "P2", "P6"):
        e = CASOS[c]
        for b in BASES3:
            for t in REGULARES:
                evaluacion(lista, c, e, t, f"v2loc_s{b}", f"--politica politica_{e}_local_p3v2reg_s{b}.pt",
                           [req_entreno("e1_v2loc", e, b, c)], tipo="v2loc", base=b,
                           corrida=(e, "local", "p3v2reg", b))
    # --- Llegadas aleatorias: poi_P1-P6 ---
    for c, e in POI.items():
        reqs = {b: req_entreno("e2_v2poi", e, b, c, factor=POI_F) for b in BASES5}
        for t in ALEATORIAS:
            for b in BASES5:
                evaluacion(lista, c, e, t, f"v2poi_s{b}", f"--politica politica_{e}_vecinos_p3v2poi_s{b}.pt",
                           [reqs[b]], tipo="v2poi", base=b, corrida=(e, "vecinos", "p3v2poi", b))
            for b in BASES3:
                evaluacion(lista, c, e, t, f"v2poiloc_s{b}", f"--politica politica_{e}_local_p3v2poi_s{b}.pt",
                           [req_entreno("e2_v2poiloc", e, b, c, factor=POI_F)], tipo="v2poiloc", base=b,
                           corrida=(e, "local", "p3v2poi", b))
            for clave, brazo in (("fijo", "--brazo fijo"), ("actuado", "--brazo actuado"),
                                 ("trivial", "--brazo trivial")):
                evaluacion(lista, c, e, t, clave, brazo, ["trabajo:preparar"], tipo=f"ref_{clave}")
        # V2 regular jugada con llegadas aleatorias (en P6, la de P6e), C0 aleatorio e IPPO entregado
        e_reg, c_reg = (P6E["P6e"], "P6e") if c == "P6" else (CASOS[c], c)
        pref = "e2_v2reg" if c == "P6" else "e1_v2reg"
        v5m, v5t = mediana(lista, e_reg, "vecinos", "p3v2reg", BASES5,
                           [req_entreno(pref, e_reg, b, c_reg) for b in BASES5], "p3v2regmed")
        cpm, cpt = mediana(lista, e, "vecinos", "p3c0poi", BASES3,
                           [f"trabajo:c0_p3c0poi_{e}_s{b}_publicar" for b in BASES3], "p3c0poimed",
                           fuente=lambda b, e_reg=e_reg: (e_reg, "vecinos", "p3v2reg"))
        enm, ent = mediana(lista, CASOS[c], "vecinos", "", BASES3, [], "p3entmed", origen="insumos/entregado/")
        pm, pt = mediana(lista, e, "vecinos", "p3v2poi", BASES5, list(reqs.values()), "p3v2poimed")
        # la V2 regular de 42/2042/4042 (en P6, la de P6e) frente al C0 aleatorio, que solo tiene esas bases (§6)
        v3m, v3t = mediana(lista, e_reg, "vecinos", "p3v2reg", BASES3,
                           [req_entreno(pref, e_reg, b, c_reg) for b in BASES3], "p3v2reg3med")
        for t in ALEATORIAS:
            evaluacion(lista, c, e, t, "v2reg3poi", f"--politica {v3m}", [f"trabajo:{v3t}"], tipo="v2reg3poi")
            evaluacion(lista, c, e, t, "v2regmed", f"--politica {v5m}", [f"trabajo:{v5t}"], tipo="v2regmed")
            evaluacion(lista, c, e, t, "c0poimed", f"--politica {cpm}", [f"trabajo:{cpt}"], tipo="c0poimed")
            evaluacion(lista, c, e, t, "entmed", f"--politica {enm}", [f"trabajo:{ent}"], tipo="entmed")
        for t in REGULARES:                      # transferencia de vuelta: V2 aleatoria con llegadas regulares
            evaluacion(lista, c_reg, e_reg, t, "v2poimed", f"--politica {pm}", [f"trabajo:{pt}"], tipo="v2poimed")


def evaluaciones_variantes(lista):
    """Etapa 3 y 3b: todas las bases de cada variante, en las tandas de su tipo de llegadas."""
    reg = {**CASOS, **NIVELES, **D}
    variantes = [("p3obs", ["D", "c2715"], BASES5, 200), ("p3obs", ["P1", "P2", "P3", "P6"], BASES3, 200),
                 ("p3m7norm", ["D"], BASES3, 200), ("p3m7forz", ["D"], BASES3, 200), ("p3m7msg", ["D"], BASES3, 200),
                 ("p3m7", ["D", "P2", "P6"], BASES3, 200), ("p3ent", ["D", "P1"], BASES3, 200),
                 ("p3reloj2", ["D", "P1", "P2", "P6"], BASES3, 200), ("p3completo", ["P1", "P2", "P4", "P6"], BASES3, 400),
                 ("p3obspoi", list(POI), BASES3, 200), ("p3reloj2poi", ["P1", "P2", "P6"], BASES3, 200),
                 ("p3completopoi", list(POI), BASES3, 400)]
    for et, celdas, bases, eps in variantes:
        poi = et.endswith("poi")
        f_tr = {"p3obspoi": (OBS * POI_F, OBS * POI_F), "p3reloj2poi": (RELOJ_TR * POI_F, RELOJ_VAL * POI_F),
                "p3completopoi": (OBS * RELOJ_TR * POI_F, OBS * RELOJ_VAL * POI_F), "p3obs": OBS,
                "p3reloj2": (RELOJ_TR, RELOJ_VAL), "p3completo": (OBS * RELOJ_TR, OBS * RELOJ_VAL)}.get(et, 1.0)
        for c in celdas:
            e = POI[c] if poi else reg[c]
            for b in bases:
                req = req_entreno(f"e3_{et}", e, b, c, eps, factor=f_tr)
                for t in (ALEATORIAS if poi else REGULARES):
                    evaluacion(lista, c, e, t, f"{et}_s{b}", f"--politica politica_{e}_vecinos_{et}_s{b}.pt",
                               [req], factor=FACTOR_EV.get(et, 1.0), tipo=et, base=b,
                               corrida=(e, "vecinos", et, b))
    for tipo, celdas, pref in (("reg", CASOS, "p3e400"), ("poi", POI, "p3e400poi")):
        tandas = ALEATORIAS if tipo == "poi" else REGULARES
        for c, e in celdas.items():
            for b in BASES3:
                f = POI_F if tipo == "poi" else 1.0
                req = req_entreno(f"e3b_{pref}", e, b, c, 400, factor=f, desde=DESDE_3B)
                for t in tandas:
                    evaluacion(lista, c, e, t, f"{pref}_s{b}", f"--politica politica_{e}_vecinos_{pref}_s{b}.pt",
                               [req], tipo=pref, base=b, corrida=(e, "vecinos", pref, b))
                    for et_r in (f"p3piso200{tipo}", f"p3e400c20{tipo}"):
                        evaluacion(lista, c, e, t, f"{et_r}_s{b}", f"--politica politica_{e}_vecinos_{et_r}_s{b}.pt",
                                   [f"trabajo:e3b_elegir_{et_r}_{e}_s{b}"], tipo=et_r, base=b,
                                   corrida=(e, "vecinos", pref, b))


# ---------------- Promocion: que modelo se cita en cada celda (prerregistro §12; PLAN3 3.5) ----------------
# Candidatos de cada celda: V2 y las variantes prerregistradas entrenadas ahi con el mismo tipo de llegadas
# (observacion nueva, limpiezas juntas, 400 episodios, reloj de 2 s y modelo completo). Cada uno aporta su version
# evaluada entre 42, 2042 y 4042, jugada en 15009-15024. La decision se guarda por escenario (promocion/<esc>.json).
CANDIDATOS_REG = {"P1": ["p3obs", "p3reloj2", "p3completo", "p3e400"],
                  "P2": ["p3obs", "p3m7", "p3reloj2", "p3completo", "p3e400"],
                  "P3": ["p3obs", "p3e400"], "P4": ["p3completo", "p3e400"], "P5": ["p3e400"],
                  "P6": ["p3obs", "p3m7", "p3reloj2", "p3completo", "p3e400"],
                  "D": ["p3obs", "p3m7", "p3reloj2"], "c2715": ["p3obs"]}
CANDIDATOS_POI = {"P1": ["p3obspoi", "p3reloj2poi", "p3completopoi", "p3e400poi"],
                  "P2": ["p3obspoi", "p3reloj2poi", "p3completopoi", "p3e400poi"],
                  "P3": ["p3obspoi", "p3completopoi", "p3e400poi"], "P4": ["p3obspoi", "p3completopoi", "p3e400poi"],
                  "P5": ["p3obspoi", "p3completopoi", "p3e400poi"],
                  "P6": ["p3obspoi", "p3reloj2poi", "p3completopoi", "p3e400poi"]}


def promocion(lista):
    reg = {**CASOS, **NIVELES, **D}
    decisiones = []
    for tipo, candidatos in (("reg", CANDIDATOS_REG), ("poi", CANDIDATOS_POI)):
        for c, ets in candidatos.items():
            e = POI[c] if tipo == "poi" else reg[c]
            et_v2 = "p3v2poi" if tipo == "poi" else "p3v2reg"
            pref_v2 = "e2_v2poi" if tipo == "poi" else "e1_v2reg"
            f_v2 = POI_F if tipo == "poi" else 1.0
            csvs = {}
            for et in [et_v2] + ets:
                if et == et_v2:
                    reqs = [req_entreno(pref_v2, e, b, c, factor=f_v2) for b in BASES3]
                    et_med = f"{et_v2}3med"
                elif et.startswith("p3e400"):
                    reqs = [req_entreno(f"e3b_{et}", e, b, c, 400, factor=f_v2, desde=DESDE_3B) for b in BASES3]
                    et_med = f"{et}med"
                else:
                    eps = 400 if et.startswith("p3completo") else EPISODIOS
                    f_tr = {"p3obs": OBS, "p3obspoi": (OBS * POI_F, OBS * POI_F),
                            "p3reloj2": (RELOJ_TR, RELOJ_VAL), "p3reloj2poi": (RELOJ_TR * POI_F, RELOJ_VAL * POI_F),
                            "p3completo": (OBS * RELOJ_TR, OBS * RELOJ_VAL),
                            "p3completopoi": (OBS * RELOJ_TR * POI_F, OBS * RELOJ_VAL * POI_F)}.get(et, 1.0)
                    reqs = [req_entreno(f"e3_{et}", e, b, c, eps, factor=f_tr) for b in BASES3]
                    et_med = f"{et}med"
                ruta, tid = mediana(lista, e, "vecinos", et, BASES3, reqs, et_med)
                ev = evaluacion(lista, c, e, "promo", et_med, f"--politica {ruta}", [f"trabajo:{tid}"],
                                factor=FACTOR_EV.get(et, 1.0), tipo=f"promo_{et}")
                csvs[et] = (f"parciales/promo/eval_{e}__{et_med}.csv", ev)
            salida = f"promocion/{e}.json"
            lista.agregar({"id": f"promo_decidir_{e}", "etapa": "ev", "prioridad": 4, "uso": "sin_semillas",
                           "requiere": [f"trabajo:{ev}" for _, ev in csvs.values()],
                           "cmd": f"python p3_promocion.py decidir --celda {e} --v2 {csvs[et_v2][0]} "
                                  f"--candidatos {','.join(r for et, (r, _) in csvs.items() if et != et_v2)} "
                                  f"--salida {salida}",
                           "salidas": [salida], "duracion": 10})
            decisiones.append((f"promo_decidir_{e}", salida))
    lista.agregar({"id": "promo_juntar", "etapa": "ev", "prioridad": 4, "uso": "sin_semillas",
                   "requiere": [f"trabajo:{t}" for t, _ in decisiones],
                   "cmd": f"python p3_promocion.py juntar --entradas {','.join(s for _, s in decisiones)} "
                          f"--salida promocion.json",
                   "salidas": ["promocion.json"], "duracion": 10})


def preparar(lista):
    """Genera los programas del actuado y del ciclo minimo de cada escenario (p3_preparar.py; PLAN3 0.11). Las
    evaluaciones de esos brazos dependen de el (comun los reescribe de forma atomica, pero asi no compiten)."""
    escenarios = (list({**CASOS, **NIVELES, **D}.values()) + list(P6E.values()) + list(POI.values())
                  + list(PERFIL.values()) + list(MEZCLA.values()) + list(MEZCLA_A.values()))
    lista.agregar({"id": "preparar", "etapa": "0", "prioridad": 0, "uso": "sin_semillas",
                   "cmd": f"{LANZADOR} p3_preparar.py {' '.join(escenarios)} --piezas actuado,trivial",
                   "salidas": [f"{e}_{p}.add.xml" for e in escenarios for p in ("actuado", "trivial")],
                   "duracion": 600})


# ---------------- Referencias (PLAN3 0.7-0.10; informe_ref §2) ----------------
# h-proceso por etapa (regimen conservador + 10 %) [M plan3/pruebas/ref/salidas/costos_ref.txt]:
# (gruesa, fina, desfases, desempate, fragil, mult5, franja, actuado (7 trabajos), reglas (regla + mp))
REF_H = {"corredor": (.29, .14, .02, .04, .03, .12, .03, .06, .11),
         "corredor_alta": (.91, 1.03, .07, .18, .15, .54, .12, .16, .27),
         "red": (1.94, .19, .33, .10, .08, 1.18, .07, .11, .17),
         "red_alta": (2.34, .22, .40, .12, .10, 1.43, .08, .12, .20),
         "malla3": (.66, 3.20, 0, .21, .18, .43, .15, .32, .46),
         "malla3_alta": (1.12, 1.69, 0, .36, .31, .72, .25, .55, 1.00),
         "malla3_alta_e": (1.12, 1.69, 0, .36, .31, .72, .25, .55, 1.00),
         "dem_corredor_t2715_der": (.64, .62, .04, .11, .09, .32, .07, .16, .27),
         "dem_corredor_t905": (.15, .15, .02, .02, .02, 0, 0, .07, 0),
         "dem_corredor_t1358": (.23, .09, .01, .03, .03, 0, 0, .07, 0),
         "dem_corredor_t2715": (.61, .50, .06, .14, .12, 0, 0, .17, 0),
         "dem_red_t905": (1.34, .87, .60, .06, .05, 0, 0, .12, 0),
         "dem_red_t1358": (1.33, .27, .27, .08, .07, 0, 0, .12, 0),
         "dem_red_t1810": (1.50, .80, .60, .09, .07, 0, 0, .12, 0),
         "dem_red_t2715": (2.34, 1.25, .93, .13, .12, 0, 0, .12, 0),
         "dem_red_t3620": (3.63, 1.21, .73, .21, .18, 0, 0, .13, 0),
         "dem_malla3_t1810": (.28, 1.32, 0, .11, .09, 0, 0, .34, 0),
         "dem_malla3_t2715": (.33, 1.59, 0, .13, .11, 0, 0, .34, 0),
         "dem_malla3_t3620": (.39, 1.85, 0, .15, .13, 0, 0, .34, 0),
         "dem_malla3_t6525": (.75, 2.25, 0, .29, .25, 0, 0, .59, 0),
         "poi_corredor": (1.04, .50, .06, .12, .02, .29, .17, .27, .60),
         "poi_corredor_alta": (3.24, 3.68, .25, .54, .02, 1.28, .74, .67, 1.46),
         "poi_red": (6.92, .66, 1.19, .29, .02, 3.86, .40, .48, .90),
         "poi_red_alta": (8.36, .80, 1.44, .36, .02, 4.67, .48, .53, 1.06),
         "poi_malla3": (2.36, 11.40, 0, .66, .02, .75, .88, 1.36, 2.46),
         "poi_malla3_alta": (4.01, 6.02, 0, 1.11, .02, 1.28, 1.50, 2.32, 5.33)}
# perfil y mezcla: como la celda aleatoria de su caso (la mezcla, x1.10); el perfil agrega la verificacion de bloques
REF_H.update({"per_corredor": REF_H["poi_corredor"], "per_red": REF_H["poi_red"],
              "mix_corredor": tuple(round(x * 1.10, 2) for x in REF_H["poi_corredor"]),
              "mix_red": tuple(round(x * 1.10, 2) for x in REF_H["poi_red"])})
TROZO_MAX_H = 2.0
CON_TROZOS = ("gruesa", "fina", "desfases", "mult5")


def ref_salidas(esc, trabajo):
    """Salidas que deja cada trabajo de referencias (informe_ref §2.5)."""
    b = f"barridos/{esc}"
    if trabajo in ("fina", "desfases", "desempate"):
        return [f"{b}/{trabajo}.csv", f"{b}/{trabajo}_semillas.csv"]
    return {"gruesa": [f"{b}/gruesa.csv", f"{b}/gruesa_semillas.csv", f"{b}/fijo_grueso10.json", f"{esc}_r10g.add.xml"],
            "fragil": [f"{b}/fragil.csv", f"{b}/fijo_fino.json", f"{esc}_r10f.add.xml"],
            "mult5": [f"{b}/mult5.csv", f"{b}/mult5_desempate.csv", f"{b}/fijo_mult5.json", f"{esc}_m5f.add.xml"],
            "franja": [f"{b}/franja.csv", f"{b}/franja_final.csv", f"{b}/franja.json", f"{esc}_franja.add.xml"],
            "bloques": [f"{b}/bloques.csv", f"{b}/bloques.json", f"{esc}_bloques.add.xml"],
            "actuado_final": [f"{b}/actuado_final.csv", f"{b}/actuado_aj.json", f"{esc}_actuado_aj.add.xml"],
            "regla": [f"{b}/reglas_regla.csv", f"{b}/reglas_regla_final.csv", f"{b}/regla.json"],
            "mp": [f"{b}/reglas_mp.csv", f"{b}/reglas_mp_final.csv", f"{b}/mp.json"],
            "reactiva": [f"{b}/reglas_reactiva.csv", f"{b}/reglas_reactiva_final.csv", f"{b}/reactiva.json"]}[trabajo]


def ref_celda(lista, esc, completa=True, perfil=False, franja=True, mp=True, mult5=True):
    """Trabajos de referencias de un escenario. Devuelve {nombre: id del trabajo que deja su salida}."""
    pre = LANZADOR if esc.startswith(("poi_", "per_", "mix", "malla3_alta_e")) else "python"
    h = dict(zip(("gruesa", "fina", "desfases", "desempate", "fragil", "mult5", "franja", "actuado", "reglas"),
                 REF_H[esc]))
    bloque = " --bloque 600" if perfil else ""
    ids = {}

    def etapa(nombre, requiere):
        horas = max(h[nombre], 0.02)
        n = int(-(-horas // TROZO_MAX_H)) if nombre in CON_TROZOS and horas > TROZO_MAX_H else 1
        base = f"{pre} barrer_fino.py {esc} --etapa {nombre}{bloque}"
        previos = list(requiere)
        if n > 1:
            trozos = []
            for k in range(n):
                tid = f"r_{nombre}_{esc}_t{k}de{n}"
                lista.agregar({"id": tid, "etapa": "0", "prioridad": 1, "uso": "ajuste", "requiere": list(requiere),
                               "cmd": f"{base} --trozo {k}/{n}", "duracion": round(3600 * horas / n),
                               "salidas": [f"barridos/{esc}/trozos/{nombre}_t{k}de{n}.csv"]})
                trozos.append(f"trabajo:{tid}")
            previos = trozos
        tid = f"r_{nombre}_{esc}"
        lista.agregar({"id": tid, "etapa": "0", "prioridad": 1, "uso": "ajuste", "requiere": previos, "cmd": base,
                       "duracion": round(3600 * (horas if n == 1 else max(0.05, 0.25 * horas / n))),
                       "salidas": ref_salidas(esc, nombre)})
        ids[nombre] = tid
        return f"trabajo:{tid}"
    g = etapa("gruesa", [])
    d = etapa("desfases", [etapa("fina", [g])])
    f = etapa("fragil", [etapa("desempate", [d])])
    if completa and mult5:
        etapa("mult5", [g])
    if completa and (franja or perfil):
        nombre = "bloques" if perfil else "franja"
        tid = f"r_{nombre}_{esc}"
        lista.agregar({"id": tid, "etapa": "0", "prioridad": 1, "uso": "ajuste",
                       "requiere": [d, f] if perfil else [d],
                       "cmd": f"{pre} franja.py {esc}{' --bloques' if perfil else ''}",
                       "duracion": round(3600 * max(h["franja"], 0.05) * EMPAQUE), "salidas": ref_salidas(esc, nombre)})
        ids[nombre] = tid
    previo = []
    for paso in ("1", "2", "3", "4", "5", "6", "final"):
        tid = f"r_actuado{paso}_{esc}"
        req = previo + ([f] if paso == "6" else [])
        b = f"barridos/{esc}"
        lista.agregar({"id": tid, "etapa": "0", "prioridad": 1, "uso": "ajuste", "requiere": req,
                       "cmd": f"{pre} actuado.py {esc} --paso {paso}",
                       "duracion": round(3600 * max(h["actuado"], 0.07) * (
                           (0.81 if esc.startswith(("poi_", "per_", "mix")) else 0.25) if paso == "final" else
                           (0.19 if esc.startswith(("poi_", "per_", "mix")) else 0.75) / 6)),
                       "salidas": (ref_salidas(esc, "actuado_final") if paso == "final"
                                   else [f"{b}/actuado_paso{paso}.csv", f"{b}/actuado_paso{paso}.json"])})
        previo = [f"trabajo:{tid}"]
    ids["actuado"] = f"r_actuadofinal_{esc}"
    if completa:
        familias = ("regla", "reactiva", "mp") if mp else ("regla", "reactiva")
        for fam in familias:
            tid = f"r_{fam}_{esc}"
            parte = {"regla": 0.5, "reactiva": 0.3, "mp": 0.3}[fam]
            lista.agregar({"id": tid, "etapa": "0", "prioridad": 1, "uso": "ajuste", "requiere": [],
                           "cmd": f"{pre} reglas.py {esc} --familia {fam}",
                           "duracion": round(3600 * max(h["reglas"] * parte, 0.05) * EMPAQUE),
                           "salidas": ref_salidas(esc, fam)})
            ids[fam] = tid
    return ids


REFS = {}           # escenario -> {nombre: id}; lo llenan referencias() y lo usan las evaluaciones


def referencias(lista):
    for e in list(CASOS.values()) + list(D.values()) + list(P6E.values()) + list(POI.values()):
        REFS[e] = ref_celda(lista, e)
    for e in NIVELES.values():
        REFS[e] = ref_celda(lista, e, completa=False)
    for e in PERFIL.values():
        REFS[e] = ref_celda(lista, e, perfil=True, mult5=False)
    for e in MEZCLA.values():
        REFS[e] = ref_celda(lista, e, franja=False, mp=False, mult5=False)


def brazos_ref(esc, de=None):
    """[(clave, brazo de evaluar3, trabajo que lo deja, tipo)] de las referencias ajustadas de un escenario. de: el
    escenario cuyos ajustes se usan (mixa_ juega los de mix_)."""
    de = de or esc
    r = REFS.get(de, {})
    salida = []
    if "fragil" in r:
        salida.append(("fino", f"--brazo fijo --programa {de}_r10f.add.xml --nombre fino", r["fragil"], "ref_fino"))
    if "mult5" in r:
        salida.append(("fino5", f"--brazo fijo --programa {de}_m5f.add.xml --nombre mult5", r["mult5"], "ref_fino5"))
    if de in NIVELES.values() and "gruesa" in r:
        salida.append(("fijo10", f"--brazo fijo --programa {de}_r10g.add.xml --nombre grueso10", r["gruesa"],
                       "ref_fijo10"))
    if "franja" in r:
        salida.append(("franja", "--brazo franja", r["franja"], "ref_franja"))
    if "bloques" in r:
        salida.append(("bloques", "--brazo bloques", r["bloques"], "ref_bloques"))
    if "actuado" in r:
        prog = "" if de == esc else f" --programa {de}_actuado_aj.add.xml"
        salida.append(("actuadoaj", f"--brazo actuado_aj{prog}", r["actuado"], "ref_actuadoaj"))
    if "regla" in r:
        salida.append(("regla", f"--regla-de barridos/{de}/regla.json", r["regla"], "ref_regla"))
    if "reactiva" in r:
        salida.append(("reactiva", f"--regla-de barridos/{de}/reactiva.json", r["reactiva"], "ref_reactiva"))
    if "mp" in r:
        salida.append(("mp", f"--regla-de barridos/{de}/mp.json", r["mp"], "ref_mp"))
    return salida


EV.update({"per1": EV["P1"], "per3": EV["P3"], "mix1": EV["P1"] * 1.10, "mix3": EV["P3"] * 1.10,
           "mixa1": EV["P1"] * 1.10, "mixa3": EV["P3"] * 1.10})
TR.update({"mixa1": TR["P1"], "mixa3": TR["P3"]})


def evaluaciones_referencias(lista):
    """Las referencias ajustadas en las tandas de su tipo de llegadas (PLAN3 1.6 y 2.3)."""
    if not REFS:
        referencias(Lista())                      # solo para conocer los ids, si la parte no esta en la lista
    for celdas, tandas in (({**CASOS, **D, **P6E, **NIVELES}, REGULARES), (POI, ALEATORIAS)):
        for c, e in celdas.items():
            for clave, brazo, req, tipo in brazos_ref(e):
                for t in tandas:
                    evaluacion(lista, c, e, t, clave, brazo, [f"trabajo:{req}"], tipo=tipo)


def evaluaciones_perfil_mezcla(lista):
    """2.4 y 2.5: el modelo entrenado con el perfil o con la mezcla, sus referencias re-ajustadas y las de siempre."""
    if not REFS:
        referencias(Lista())
    for celdas, et, tipo, origen in ((PERFIL, "p3v2per", "v2per", None), (MEZCLA, "p3v2mix", "v2mix", None),
                                     (MEZCLA_A, "p3v2mix", "v2mix", ORIGEN_A)):
        for c, e in celdas.items():
            e_pol = origen[c] if origen else e              # mixa_ juega las politicas y ajustes de mix_
            for b in BASES3:
                req = req_entreno(f"e2_{et}", e_pol, b, c, factor=POI_F * (1.10 if et == "p3v2mix" else 1.0))
                for t in ALEATORIAS:
                    evaluacion(lista, c, e, t, f"{et}_s{b}", f"--politica politica_{e_pol}_vecinos_{et}_s{b}.pt",
                               [req], tipo=tipo, base=b, corrida=(e_pol, "vecinos", et, b))
            for clave, brazo, req, tipo_r in brazos_ref(e, de=e_pol):
                for t in ALEATORIAS:
                    evaluacion(lista, c, e, t, clave, brazo, [f"trabajo:{req}"], tipo=tipo_r)
            for clave, brazo in (("fijo", "--brazo fijo"), ("actuado", "--brazo actuado"),
                                 ("trivial", "--brazo trivial")):
                for t in ALEATORIAS:
                    evaluacion(lista, c, e, t, clave, brazo, ["trabajo:preparar"], tipo=f"ref_{clave}")
            if celdas is PERFIL:                     # la V2 aleatoria sin perfil, jugada con el perfil
                caso = "P1" if c == "per1" else "P3"
                pm = f"politica_{POI[caso]}_vecinos_p3v2poimed.pt"
                for t in ALEATORIAS:
                    evaluacion(lista, c, e, t, "v2poimed", f"--politica {pm}", [f"trabajo:el_p3v2poimed_{POI[caso]}"],
                               tipo="v2poimed")


def evaluaciones_a3(lista):
    """a3 (descriptiva): la version evaluada de V2 y de la observacion nueva con colas en cero y con los mensajes
    cortados, frente a la misma politica sin perturbar (prerregistro §8, Etapa 3)."""
    reg = {"D": D["D"], "c2715": NIVELES["c2715"], **{c: CASOS[c] for c in ("P1", "P2", "P3", "P6")}}
    for celdas, tandas, pares in ((reg, REGULARES, (("p3v2reg", "v2reg3med", "p3v2reg3med", "e1_v2reg", 200, 1.0),
                                                      ("p3obs", "p3obsmed", "p3obsmed", "e3_p3obs", 200, OBS))),
                                  (POI, ALEATORIAS, (("p3v2poi", "v2poi3med", "p3v2poi3med", "e2_v2poi", 200, POI_F),
                                                     ("p3obspoi", "p3obspoimed", "p3obspoimed", "e3_p3obspoi", 200,
                                                      (OBS * POI_F, OBS * POI_F))))):
        for c, e in celdas.items():
            for et, tipo, et_med, pref, eps, f in pares:
                reqs = [req_entreno(pref, e, b, c, eps, factor=f) for b in BASES3]
                ruta, tid = mediana(lista, e, "vecinos", et, BASES3, reqs, et_med)
                for t in tandas:
                    for pert, op in (("colas0", "--colas-cero"), ("msg0", "--perdida 1")):
                        evaluacion(lista, c, e, t, f"a3{pert}_{tipo}", f"--politica {ruta} {op}", [f"trabajo:{tid}"],
                                   factor=FACTOR_EV.get(et, 1.0), tipo=f"a3{pert}_{tipo}")


PARTES = {"etapa1": etapa1, "c0": c0, "v2vieja": v2vieja, "etapa2": etapa2, "etapa2pm": etapa2pm,
          "etapa3b": etapa3b, "etapa3b_reg": lambda l: etapa3b(l, ("reg",)),
          "etapa3b_poi": lambda l: etapa3b(l, ("poi",)), "etapa3": etapa3,
          "preparar": preparar, "referencias": referencias, "evaluaciones": evaluaciones,
          "evaluaciones_variantes": evaluaciones_variantes, "promocion": promocion,
          "evaluaciones_referencias": evaluaciones_referencias,
          "evaluaciones_perfil_mezcla": evaluaciones_perfil_mezcla, "evaluaciones_a3": evaluaciones_a3}
# Partes que forman el plan completo (los alias etapa3b_reg y etapa3b_poi son subconjuntos de etapa3b)
PARTES_PLAN = [p for p in PARTES if p not in ("etapa3b_reg", "etapa3b_poi")]


def generar(partes):
    lista = Lista()
    for p in partes:
        PARTES[p](lista)
    return lista.trabajos


def generar_con_manifiesto(partes):
    lista = Lista()
    for p in partes:
        PARTES[p](lista)
    return lista.trabajos, lista.manifiesto


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--partes", default=None, help="por defecto, todas; con --comprobar, las de cola/partes.txt")
    ap.add_argument("--seco", action="store_true")
    ap.add_argument("--comprobar", action="store_true")
    args = ap.parse_args()
    texto_partes = args.partes
    if texto_partes is None:
        if args.comprobar and os.path.exists(PARTES_TXT):
            with open(PARTES_TXT, encoding="utf-8") as f:
                texto_partes = f.read().strip()
        else:
            texto_partes = ",".join(PARTES_PLAN)
    partes = [p for p in texto_partes.split(",") if p]
    desconocidas = [p for p in partes if p not in PARTES]
    if desconocidas:
        sys.exit(f"partes desconocidas: {desconocidas}; hay {sorted(PARTES)}")
    trabajos, manifiesto = generar_con_manifiesto(partes)
    texto = "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in trabajos)
    texto_m = json.dumps(manifiesto, ensure_ascii=False, indent=0) + "\n"
    if args.comprobar:
        bien = True
        for ruta, esperado in ((TRABAJOS, texto), (MANIFIESTO, texto_m)):
            actual = open(ruta, encoding="utf-8").read() if os.path.exists(ruta) else ""
            print(f"{os.path.relpath(ruta, PLAN3)} {'al dia' if actual == esperado else 'NO coincide'}")
            bien &= actual == esperado
        sys.exit(0 if bien else 1)
    por_etapa = {}
    for t in trabajos:
        n, h = por_etapa.get(t["etapa"], (0, 0.0))
        por_etapa[t["etapa"]] = (n + 1, h + t["duracion"] * t["cpus"] / 3600)
    for etapa, (n, h) in sorted(por_etapa.items()):
        print(f"etapa {etapa}: {n} trabajos, ~{h:.0f} h-proceso")
    print(f"total: {len(trabajos)} trabajos, ~{sum(h for _, h in por_etapa.values()):.0f} h-proceso")
    if not args.seco:
        os.makedirs(os.path.dirname(TRABAJOS), exist_ok=True)
        with open(TRABAJOS, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto)
        with open(MANIFIESTO, "w", encoding="utf-8", newline="\n") as f:
            f.write(texto_m)
        with open(PARTES_TXT, "w", encoding="utf-8", newline="\n") as f:
            f.write(",".join(partes) + "\n")
        print(f"escritos {os.path.relpath(TRABAJOS, PLAN3)} y {os.path.relpath(MANIFIESTO, PLAN3)} "
              f"({len(manifiesto)} CSV esperados)")


if __name__ == "__main__":
    main()
