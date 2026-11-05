"""
generar_trabajos3.py - Escribe cola/trabajos.jsonl con los trabajos del bloque plan3 (PLAN3 0.18; DECISIONES B20).

Uso (desde plan3/):  python generar_trabajos3.py [--partes etapa1,...] [--seco] [--comprobar]
  --partes     partes a incluir (por defecto, todas las que ya tienen codigo; ver PARTES)
  --seco       no escribe: muestra cuantos trabajos y cuantas h-proceso por etapa
  --comprobar  sale con 1 si cola/trabajos.jsonl no es lo que este script generaria (lo usa chequeos_previos)

Cada trabajo declara: id, prioridad (menor = antes), cpus, requiere, cmd (cwd = plan3/), salidas (la cola lo da por
hecho solo si existen y son nuevas), duracion (s estimados, regimen conservador + 10 %), uso (bloque de semillas del
prerregistro §3), etapa y, en los tramos de un mismo entrenamiento, cadena.
Los entrenamientos de mas de 5 h se parten en tramos con --hasta-ep; todos llevan --reanudar auto, asi que un trabajo
caido se relanza con el mismo comando y sigue desde su ultimo estado (DECISIONES B15 y B22).
Regenerar el archivo deja los mismos ids: la cola no repite lo hecho.
"""
import os
import sys
import json
import argparse

PLAN3 = os.path.dirname(os.path.abspath(__file__))
TRABAJOS = os.path.join(PLAN3, "cola", "trabajos.jsonl")
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
POI_F = 1.07            # llegadas aleatorias frente a regulares [M +3 a +13 %]


def nombre_corrida(esc, variante, etiqueta, base):
    return f"{esc}_ippo_{variante}_{etiqueta}_s{base}"


def duracion_entreno(celda, episodios=EPISODIOS, desde=0, hasta=None, factor=1.0):
    tr, val = TR[celda]
    hasta = episodios if hasta is None else hasta
    n_val = hasta // EVAL_CADA - desde // EVAL_CADA
    return EMPAQUE * factor * ((hasta - desde) * tr + n_val * len(VAL16) * val)


class Lista:
    def __init__(self):
        self.trabajos = []
        self.ids = set()

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
        total = duracion_entreno(celda, episodios, desde=desde, factor=factor)
        n_tramos = max(1, -(-int(total) // TRAMO_MAX_S))
        paso = -(-(episodios - desde) // n_tramos)
        paso = -(-paso // EVAL_CADA) * EVAL_CADA          # los cortes caen en un checkpoint
        cortes = list(range(desde + paso, episodios, paso)) + [episodios]
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
    """Id del ultimo tramo de un entrenamiento (el que publica la politica), sin agregarlo."""
    total = duracion_entreno(celda, episodios, desde=desde, factor=factor)
    n = max(1, -(-int(total) // TRAMO_MAX_S))
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


def etapa3b(lista):
    op = "--v2 --lr-horizonte 200 --lr-piso 0.1"
    for tipo, celdas, et_v2, et, pref_v2 in (("reg", CASOS, "p3v2reg", "p3e400", "e1_v2reg"),
                                            ("poi", POI, "p3v2poi", "p3e400poi", "e2_v2poi")):
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


PARTES = {"etapa1": etapa1, "c0": c0, "v2vieja": v2vieja, "etapa2": etapa2, "etapa3b": etapa3b}


def generar(partes):
    lista = Lista()
    for p in partes:
        PARTES[p](lista)
    return lista.trabajos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--partes", default=",".join(PARTES))
    ap.add_argument("--seco", action="store_true")
    ap.add_argument("--comprobar", action="store_true")
    args = ap.parse_args()
    partes = [p for p in args.partes.split(",") if p]
    desconocidas = [p for p in partes if p not in PARTES]
    if desconocidas:
        sys.exit(f"partes desconocidas: {desconocidas}; hay {sorted(PARTES)}")
    trabajos = generar(partes)
    texto = "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in trabajos)
    if args.comprobar:
        actual = open(TRABAJOS, encoding="utf-8").read() if os.path.exists(TRABAJOS) else ""
        print("cola/trabajos.jsonl al dia" if actual == texto else "cola/trabajos.jsonl NO coincide")
        sys.exit(0 if actual == texto else 1)
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
        print(f"escrito {os.path.relpath(TRABAJOS, PLAN3)}")


if __name__ == "__main__":
    main()
