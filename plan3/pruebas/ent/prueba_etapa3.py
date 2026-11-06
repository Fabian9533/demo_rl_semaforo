"""
prueba_etapa3.py - Pruebas de la Etapa 3 en rl_ippo.py (PLAN3 3.1-3.4; DECISIONES B14 y B24) y de la sensibilidad a3
(configurar_colas_cero). Informe: plan3/doc/informe_ent2.md. Cada medicion corre en un proceso aparte
(trabajo_e3.py), como mucho 2 a la vez; semillas de humo (424301-424320; entrenamiento con base 7).

  1. --obs-cercana 75: los detectores E2 no cambian la simulacion (la misma politica juega igual con y sin ellos,
     porque las entradas nuevas van al final y la politica ve solo las suyas: mismas metricas y mismos viajes); la
     espera del primero leida solo con alguien en la zona es igual a leerla en todos los carriles; cuesta <= x1.35 por
     episodio (mediana de 3 parejas sin/con alternadas en un proceso) y, en 2715 con la V2 del diagnostico (base 42),
     la marca giro_izq se activa en el 11-13 % de las decisiones con verde de C2_C1 en el periodo 2 (bloqueo.md: 12 %;
     W_C1 14 %, S2_C2 5 %; 0 % en el periodo 1), con 20 semillas. Lo mismo (sin la marca) en P6 con IPPO entregado
     (base 42), dimension 53 -> 73.
  2. --sin-forzadas: los intervalos entre decisiones del lote son 5, 13 o 18 s (reloj de 5 s) o 2, 13 o 15 s (reloj de
     2 s), salvo el cierre.
  3. --paso-decision 2: los verdes pueden durar 10, 12, 14... s (con 5: 10, 15, 20...).
  4. La recompensa por segundo es la misma con los dos relojes (mismo episodio con el decisor "mantener").
  5. configurar_colas_cero: con las mismas decisiones, las colas valen cero y todo lo demas es igual.
  6. Un entrenamiento corto con todas las opciones de la Etapa 3: msg_edad 0.0 (sin --msg-cada-paso, 1.9-2.0), ent_coef
     sigue el calendario, columnas vn_*; evaluar.py juega la politica de dimension 49 y da, semilla por semilla, lo
     mismo que su validacion; evaluar3.py --colas-cero la juega.

Uso:  python plan3/pruebas/ent/prueba_etapa3.py
Salida: plan3/pruebas/ent/salidas/prueba_etapa3.txt; corridas en plan3/tmp_ent/e3_*.
"""
import csv
import sys
import json
import shutil
import subprocess

import numpy as np

import util_ent as u

TRABAJO = u.AQUI / "trabajo_e3.py"
V2_2715 = "plan2/politica_dem_corredor_t2715_vecinos_v2_s42"          # del tag (la V2 del diagnostico)
P6_ENTREGADA = u.PLAN3 / "insumos" / "entregado" / "politica_malla3_alta_vecinos_s42"
MARCAS = [["semaforo_C1", "C2_C1"], ["semaforo_C1", "W_C1"], ["semaforo_C2", "S2_C2"]]
REFERENCIA_MARCA = {"C2_C1": 12, "W_C1": 14, "S2_C2": 5}     # % en plan2/diag_corredor/bloqueo.md (V2)


def politica_del_tag(ruta_tag, destino):
    for ext in (".pt", ".json"):
        datos = subprocess.run(["git", "show", f"{u.TAG}:{ruta_tag}{ext}"], cwd=u.RAIZ, capture_output=True,
                               check=True).stdout
        (destino / (ruta_tag.split("/")[-1] + ext)).write_bytes(datos)
    return ruta_tag.split("/")[-1] + ".pt"


def politica_copiada(origen, destino):
    for ext in (".pt", ".json"):
        shutil.copyfile(f"{origen}{ext}", destino / (origen.name + ext))
    return origen.name + ".pt"


def trabajos(lista, maximo=2):
    """lista = [(nombre, tarea, parametros, escenarios, politica)]: corre trabajo_e3.py; {nombre: (codigo, json)}."""
    preparados = []
    for nombre, tarea, p, escs, pol in lista:
        c = u.carpeta(f"e3_{nombre}", escs)
        if pol:
            p = {**p, "decisor": {"tipo": "politica", "ruta": pol(c)}}
        (c / "p.json").write_text(json.dumps(p), encoding="utf-8")
        preparados.append((nombre, c, (TRABAJO, [tarea, "p.json", "salida.json"], c, c / "log.txt")))
    codigos = u.en_tandas([t for _, _, t in preparados], maximo)
    salida = {}
    for (nombre, c, _), cod in zip(preparados, codigos):
        salida[nombre] = (cod, json.loads((c / "salida.json").read_text(encoding="utf-8")) if cod == 0 else None)
    return salida


SEMILLAS_MARCA = list(range(424301, 424321))      # 20 semillas de humo: la marca varia mucho de una a otra


def prueba_e2(inf):
    inf("1. --obs-cercana 75: los E2 no cambian la simulacion, costo por episodio y marca de giro en 2715")
    v2 = lambda c: politica_del_tag(V2_2715, c)            # noqa: E731
    p6 = lambda c: politica_copiada(P6_ENTREGADA, c)        # noqa: E731
    t2715 = {"escenario": "dem_corredor_t2715"}
    p6base = {"escenario": "malla3_alta", "semilla": 424301}
    lista = [("t2715_424301_sin", "episodio", {**t2715, "semilla": 424301}, ["dem_corredor_t2715"], v2),
             ("p6_424301_con", "episodio", {**p6base, "obs_cercana": 75, "verificar_espera": True},
              ["malla3_alta"], p6),
             ("p6_424301_sin", "episodio", p6base, ["malla3_alta"], p6)]
    lista += [(f"t2715_{s}_con", "episodio", {**t2715, "semilla": s, "obs_cercana": 75, "marcas": MARCAS,
                                              "verificar_espera": True, "marca_por_segundo": True},
               ["dem_corredor_t2715"], v2)
              for s in SEMILLAS_MARCA]
    r = trabajos(lista, maximo=2)
    inf.chequeo("las corridas terminan", all(c == 0 for c, _ in r.values()),
                f"{sum(c == 0 for c, _ in r.values())} de {len(r)}")
    for nombre in ("t2715_424301", "p6_424301"):
        con, sin = r[f"{nombre}_con"][1], r[f"{nombre}_sin"][1]
        iguales = con["res"] == sin["res"] and con["viajes"] == sin["viajes"]
        distintas = [k for k in con["res"] if con["res"][k] != sin["res"].get(k)]
        inf.chequeo(f"{nombre}: misma simulacion con y sin E2 (todas las metricas y los {len(con['viajes'])} viajes)",
                    iguales, f"dimension {sin['dim_obs']} -> {con['dim_obs']}; distintas: {distintas[:5]}")
    lecturas = sum(r[n][1]["registro"].get("espera_lecturas", 0) for n in r if n.endswith("_con"))
    distintas = sum(r[n][1]["registro"].get("espera_distintas", 0) for n in r if n.endswith("_con"))
    inf.chequeo("la espera del primero leida solo con alguien en la zona = leida en todos los carriles",
                lecturas > 0 and distintas == 0, f"{distintas} distintas de {lecturas} lecturas (2715 y P6)")
    # costo: el mismo episodio sin y con, alternados en un proceso (dos procesos que compiten por la maquina, uno
    # con y otro sin, dan razones de hasta x1.47 por puro ruido)
    costos = trabajos([("costo_t2715", "costo", {**t2715, "semilla": 424301, "obs_cercana": 75, "repeticiones": 3},
                        ["dem_corredor_t2715"], v2),
                       ("costo_p6", "costo", {**p6base, "obs_cercana": 75, "repeticiones": 3}, ["malla3_alta"], p6)],
                      maximo=2)
    for nombre, (cod, d) in costos.items():
        if cod != 0:
            inf.chequeo(f"{nombre}: termina", False, f"codigo {cod}")
            continue
        inf.chequeo(f"{nombre}: costo por episodio <= x1.35 (mediana de 3 parejas alternadas)", d["mediana"] <= 1.35,
                    f"sin {[round(x, 1) for x in d['sin']]} s, con {[round(x, 1) for x in d['con']]} s, razones "
                    f"{[round(x, 2) for x in d['razones']]}")
    # bloqueo.md mide "% del verde": segundos de verde del acceso con la cabeza detenida girando a la izquierda, en el
    # periodo 2 (V2 s42, semillas 1001-1005). El prototipo comparo con eso la fraccion de DECISIONES con la marca (2
    # semillas). Aqui las dos, con 20 semillas de humo; decide la de segundos de verde, que es la de bloqueo.md.
    inf("   Marca giro_izq en 2715 (V2 del diagnostico, base 42), periodo 2: % de los segundos de verde del acceso | "
        "% de sus decisiones")
    seg, dec, p1_seg, p1_dec = {}, {}, [0, 0], []
    for s in SEMILLAS_MARCA:
        reg = r[f"t2715_{s}_con"][1]["registro"]
        partes = []
        for tls, acceso in MARCAS:
            c = reg.get(f"seg|{tls}|{acceso}", [0, 0, 0, 0])
            filas = reg.get(f"{tls}|{acceso}", [])
            d2 = [g for t, g in filas if t > 1800]
            p1_dec += [g for t, g in filas if t <= 1800]
            p1_seg[0] += c[0]
            p1_seg[1] += c[1]
            seg.setdefault(acceso, []).append((c[2], c[3]))
            dec.setdefault(acceso, []).append(d2)
            partes.append(f"{acceso} {100 * c[3] / max(1, c[2]):5.1f} | {100 * np.mean(d2):5.1f} %")
        inf(f"   {s}: " + " | ".join(partes))
    por_seg = {a: 100 * sum(m for _, m in v) / sum(n for n, _ in v) for a, v in seg.items()}
    por_dec = {a: 100 * float(np.mean([g for d2 in v for g in d2])) for a, v in dec.items()}
    rango = {a: (min(100 * m / n for n, m in v), max(100 * m / n for n, m in v)) for a, v in seg.items()}
    inf("   20 semillas juntas: " + " | ".join(
        f"{a} {por_seg[a]:.1f} % del verde (por semilla {rango[a][0]:.1f}-{rango[a][1]:.1f}; "
        f"de las decisiones {por_dec[a]:.1f} %; bloqueo.md {REFERENCIA_MARCA[a]} %)" for a in por_seg))
    inf.chequeo("2715: la marca se activa en el 11-13 % del verde de C2_C1 (segundos de verde, periodo 2, 20 semillas)",
                11.0 <= por_seg["C2_C1"] <= 13.0,
                f"{por_seg['C2_C1']:.1f} % (de las decisiones: {por_dec['C2_C1']:.1f} %)")
    inf.chequeo("2715: la marca no se activa en el periodo 1", p1_seg[1] == 0 and sum(p1_dec) == 0,
                f"{p1_seg[1]} de {p1_seg[0]} segundos de verde; {int(sum(p1_dec))} de {len(p1_dec)} decisiones")


def prueba_reloj(inf):
    inf("")
    inf("2-4. --sin-forzadas, --paso-decision 2 y la recompensa por segundo (P1, semilla 424301)")
    base = {"escenario": "corredor", "semilla": 424301}
    r = trabajos([
        ("intervalos_5", "intervalos", {**base, "paso": 5}, ["corredor"], None),
        ("intervalos_2", "intervalos", {**base, "paso": 2}, ["corredor"], None),
        ("verdes_5", "episodio", {**base, "paso": 5, "registrar_verdes": True,
                                  "decisor": {"tipo": "azar", "p": 0.3, "semilla": 1}}, ["corredor"], None),
        ("verdes_2", "episodio", {**base, "paso": 2, "registrar_verdes": True,
                                  "decisor": {"tipo": "azar", "p": 0.3, "semilla": 1}}, ["corredor"], None),
        ("recompensa", "recompensa", base, ["corredor"], None),
    ], maximo=2)
    inf.chequeo("las corridas terminan", all(c == 0 for c, _ in r.values()), f"{ {k: c for k, (c, _) in r.items()} }")
    for k, esperados in (("5", {5, 13, 18}), ("2", {2, 13, 15})):
        iv = {int(x): n for x, n in r[f"intervalos_{k}"][1]["intervalos"].items()}
        inf.chequeo(f"--sin-forzadas con reloj de {k} s: intervalos del lote en {sorted(esperados)} (salvo el cierre)",
                    set(iv) <= esperados and len(iv) >= 2,
                    f"{iv}; cierres {r[f'intervalos_{k}'][1]['cierres']}; frac_forzadas no aplica (lote sin forzadas)")
    for k, paso in (("5", 5), ("2", 2)):
        verdes = r[f"verdes_{k}"][1]["registro"].get("verdes", [])
        validos = all(10 <= v <= 60 and (v - 10) % paso == 0 for v in verdes)
        valores = sorted(set(verdes))
        inf.chequeo(f"--paso-decision {k}: los verdes duran 10, {10 + paso}, {10 + 2 * paso}... s",
                    validos and (k == "5" or any(v % 5 for v in valores)),
                    f"{len(verdes)} verdes; duraciones {valores[:14]}{' ...' if len(valores) > 14 else ''}")
    rr = r["recompensa"][1]
    a, b = rr["5"], rr["2"]
    misma = a["viajes"] == b["viajes"] and a["timeloss"] == b["timeloss"] and a["cambios"] == b["cambios"]
    inf.chequeo("el decisor 'mantener' da la misma simulacion con los dos relojes", misma,
                f"timeLoss {a['timeloss']} | {b['timeloss']}; cambios {a['cambios']} | {b['cambios']}")
    rel = abs(a["recompensa_segundos"] - b["recompensa_segundos"]) / abs(a["recompensa_segundos"])
    rel_ret = abs(a["recompensa_segundos"] - a["ret_retraso"]) / abs(a["ret_retraso"])
    inf.chequeo("la recompensa por segundo es la misma con los dos relojes", rel < 1e-9 and rel_ret < 1e-6,
                f"suma de las transiciones x5/0.02: {a['recompensa_segundos']:.3f} (reloj 5 s, {a['transiciones']} "
                f"decisiones) | {b['recompensa_segundos']:.3f} (reloj 2 s, {b['transiciones']} decisiones); "
                f"ret_retraso {a['ret_retraso']}; por decision: {a['recompensa_segundos'] / a['transiciones']:.2f} | "
                f"{b['recompensa_segundos'] / b['transiciones']:.2f}")


def prueba_colas(inf):
    inf("")
    inf("5. configurar_colas_cero (a3): P1, ciclo minimo, --obs-cercana 75, semilla 424301")
    r = trabajos([("colas", "colas", {"escenario": "corredor", "semilla": 424301, "obs_cercana": 75},
                   ["corredor"], None)], maximo=1)["colas"]
    inf.chequeo("la corrida termina", r[0] == 0)
    d = r[1]
    nombres = d["features"]
    sin = np.array([f[2:] for f in d["sin"]["obs"]])
    con = np.array([f[2:] for f in d["con"]["obs"]])
    colas = [k for k, n in enumerate(nombres) if n.startswith(("cola_", "cerca_det_", "salida_ocup_"))
             or n.endswith(("_cola_alimentadora", "_cola_mi_salida"))]
    resto = [k for k in range(len(nombres)) if k not in colas]
    inf.chequeo("mismas decisiones (mismas metricas)", d["sin"]["res"] == d["con"]["res"] and sin.shape == con.shape,
                f"{sin.shape[0]} decisiones")
    inf.chequeo("con colas en cero: esas entradas valen 0 y las demas son iguales",
                float(np.abs(con[:, colas]).max()) == 0.0 and np.array_equal(sin[:, resto], con[:, resto]),
                f"{len(colas)} entradas en cero: {[nombres[k] for k in colas]}")
    inf.chequeo("sin colas en cero, esas entradas no son todas cero (la prueba mide algo)",
                float(np.abs(sin[:, colas]).max()) > 0, f"maximo {float(np.abs(sin[:, colas]).max()):.3f}")


def prueba_entrenamiento(inf):
    inf("")
    inf("6. Entrenamiento corto con todas las opciones de la Etapa 3 (P1, base 7, 4 episodios, validacion cada 2)")
    c = u.carpeta("e3_entreno", ["corredor"])
    tag, pol = "corredor_ippo_vecinos_p3prbe3_s7", "politica_corredor_vecinos_p3prbe3_s7"
    argumentos = ["train", "--escenario", "corredor", "--seed", "7", "--episodios", "4", "--eval-cada", "2",
                  "--val-seeds", u.VAL_HUMO, "--v2", "--criterio-val", "total", "--etiqueta", "p3prbe3",
                  "--guardar-estado", "--registro-extendido", "--obs-cercana", "75", "--norm-valor", "--sin-forzadas",
                  "--msg-cada-paso", "--hiper", "ent=0.03", "--ent-final", "0.003", "--paso-decision", "2"]
    inf(f"   rl_ippo.py {' '.join(argumentos)}")
    cod = u.correr(u.RL_NUEVO, argumentos, c, c / "log.txt")
    inf.chequeo("entrena y publica", cod == 0 and (c / f"{pol}.pt").exists(), f"codigo {cod}")
    with open(c / f"resultados_{tag}.csv", newline="") as f:
        filas = list(csv.DictReader(f))
    inf.chequeo("--msg-cada-paso: edad del mensaje al decidir 0.0 s", all(float(x["msg_edad"]) == 0.0 for x in filas),
                f"{[x['msg_edad'] for x in filas]}")
    previo = u.TMP / "ident_nuevo_v2_ext" / "resultados_corredor_ippo_vecinos_p3prbv2_s7.csv"
    if previo.exists():
        with open(previo, newline="") as f:
            edades = [float(x["msg_edad"]) for x in csv.DictReader(f)]
        inf(f"   sin --msg-cada-paso (prueba_identidad, V2): {min(edades):.3f}-{max(edades):.3f} s")
    esperado = [0.03 + (0.003 - 0.03) * min(1.0, (ep - 1) / 3) for ep in range(1, 5)]
    inf.chequeo("ent_coef sigue el calendario (0.03 -> 0.003 en el horizonte de 4 episodios)",
                [float(x["ent_coef"]) for x in filas] == esperado, f"{[x['ent_coef'] for x in filas]}")
    inf.chequeo("--norm-valor: columnas vn_media y vn_desv", all(x["vn_media"] and x["vn_desv"] for x in filas),
                f"vn_media {[x['vn_media'] for x in filas]}")
    inf.chequeo("--sin-forzadas con reloj de 2 s: frac_forzadas en el CSV", all(float(x["frac_forzadas"]) > 0
                                                                               for x in filas),
                f"{[x['frac_forzadas'] for x in filas]}")
    meta = json.loads((c / f"{pol}.json").read_text(encoding="utf-8"))
    inf(f"   meta: dim_obs {meta['dim_obs']}; opciones {meta['opciones']}")
    inf.chequeo("la politica publicada es de dimension 49 y su meta trae las opciones", meta["dim_obs"] == 49 and
                meta["opciones"].get("obs_cercana") == 75 and meta["opciones"].get("paso_decision") == 2 and
                meta["opciones"].get("msg_cada_paso") is True)
    elegido = json.loads((c / "checkpoints" / f"{tag}_ep{meta['ep_elegido']:03d}.json").read_text(encoding="utf-8"))
    cod = u.correr(u.EVALUAR, ["--escenario", "corredor", "--politica", f"{pol}.pt", "--semillas", u.VAL_HUMO,
                               "--salida", "eval_e3.csv"], c, c / "log_evaluar.txt")
    with open(c / "eval_e3.csv", newline="") as f:
        ev = {int(x["semilla"]): x for x in csv.DictReader(f)}
    pares = [(s, ev[s]["timeloss_prom"], elegido[f"val_{s}"], ev[s]["retraso_total_prom"], elegido[f"val_total_{s}"])
             for s in (424301, 424302)]
    inf.chequeo("evaluar.py juega la politica de dimension 49 igual que su validacion (semilla por semilla)",
                cod == 0 and all(float(a) == float(b) and float(x) == float(y) for _, a, b, x, y in pares),
                "; ".join(f"{s}: timeLoss {a} | {b}, total {x} | {y}" for s, a, b, x, y in pares))
    cod = u.correr(u.PLAN3 / "evaluar3.py", ["--escenario", "corredor", "--semillas", "424303",
                                            "--salida", "eval3_colas0.csv", "--politica", f"{pol}.pt",
                                            "--colas-cero"], c, c / "log_evaluar3.txt")
    with open(c / "eval3_colas0.csv", newline="") as f:
        fila = next(csv.DictReader(f))
    inf.chequeo("evaluar3.py --colas-cero la juega (brazo ..._colas0)", cod == 0 and fila["brazo"].endswith("_colas0"),
                f"brazo {fila['brazo']}, timeLoss {fila['timeloss_prom']}")


def main():
    inf = u.Informe("prueba_etapa3", "Etapa 3 de rl_ippo.py (PLAN3 3.1-3.4) y colas en cero (a3)")
    prueba_e2(inf)
    prueba_reloj(inf)
    prueba_colas(inf)
    prueba_entrenamiento(inf)
    return inf.cerrar()


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
