"""
prueba_revision_e34.py - Arreglos y comprobaciones de la revision del 05.11.2026 sobre las Etapas 3 y 4 (informe:
plan3/doc/informe_ent2.md, seccion 5). Semillas de humo: base 7 para entrenar; 424301-424304 para validar y evaluar.

  A. (1, 4) Una politica de la Etapa 3 (P1, 2 episodios: --obs-cercana 75 --norm-valor --sin-forzadas --msg-cada-paso
     --paso-decision 2) se juega con sus opciones en evaluar.py en el modo antiguo (--ippo), en revalidar_c0.py
     validar y en demo: los tres dan, semilla por semilla, su propia validacion; demo avisa que la linea de comandos
     pedia otras opciones.
  B. (7) Un episodio sin transiciones no actualiza la politica (columnas vacias y AVISO) y la corrida sigue;
     NormValor.actualizar se niega con un lote vacio.
  C. (2, 3) Reglas nuevas de validar_args.
  D. (c) evaluar3.py --regla regla_u2g60 en el corredor y --regla mp_c90 en malla3_alta (424301-424302): el arbol de
     a9ba36b (antes de las Etapas 3 y 4) y el de hoy dan el mismo CSV, byte a byte.
  E. (d) Variantes entregadas frente al tag (P1, base 7, 4 episodios, validacion cada 2 en 424301-424302):
     --obs-insercion, --recompensa-insercion, --variante spill y cambio (CSV salvo segundos, checkpoints, politica y
     meta); un episodio de rl_mappo; evaluar.py --latencia 5 con la politica de --obs-insercion.
  F. (e) Observacion cercana recalculada aparte con verif_e3.py (el guion del revisor R2) en red_alta, K = 5 y K = 2.
  G. (f) Una politica de forma p3obspoi (2 episodios en poi_corredor, por ../con_escenarios.py) jugada con
     evaluar3.py: sola, con --colas-cero y con --perdida 1. Las tres salen con 0; sola da su validacion semilla por
     semilla.
  H. (g) Ocho procesos crean a la vez, por primera vez, e2_corredor_75.add.xml: todos salen con 0, el archivo queda
     entero (igual al de un proceso solo) y no quedan temporales.

Uso:  python plan3/pruebas/ent/prueba_revision_e34.py   (hasta 2 procesos de SUMO a la vez; ~20 min)
Salida: plan3/pruebas/ent/salidas/prueba_revision_e34.txt; corridas en plan3/tmp_ent/rev_*.
"""
import io
import re
import csv
import sys
import json
import shutil
import tarfile
import contextlib
import subprocess

import util_ent as u

SEM = "424301,424302"
SEMILLAS = [424301, 424302]
CON_ESC = u.RAIZ / "con_escenarios.py"
EVALUAR3 = u.PLAN3 / "evaluar3.py"
VERIF = u.AQUI / "verif_e3.py"
ARBOL = u.TMP / "arbol_a9ba36b"


def leer_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def filas(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validacion_publicada(c, tag, pol):
    """{semilla: timeLoss} de la validacion del checkpoint que se publico."""
    meta = leer_json(c / f"{pol}.json")
    ck = leer_json(c / "checkpoints" / f"{tag}_ep{meta['ep_elegido']:03d}.json")
    return {s: ck[f"val_{s}"] for s in SEMILLAS}, meta


# ---------------- A ----------------
def prueba_a(inf):
    inf("A. Politica de la Etapa 3 en evaluar.py (modo antiguo), revalidar_c0.py y demo")
    c = u.carpeta("rev_a", ["corredor"])
    tag, pol = "corredor_ippo_vecinos_p3rv3_s7", "politica_corredor_vecinos_p3rv3_s7"
    args = ["train", "--escenario", "corredor", "--seed", "7", "--episodios", "2", "--eval-cada", "1",
            "--val-seeds", SEM, "--v2", "--criterio-val", "total", "--etiqueta", "p3rv3", "--obs-cercana", "75",
            "--norm-valor", "--sin-forzadas", "--msg-cada-paso", "--paso-decision", "2"]
    cod = u.correr(u.RL_NUEVO, args, c, c / "log_train.txt")
    if not inf.chequeo("entrena la politica de la Etapa 3", cod == 0, f"codigo {cod}"):
        return
    val, meta = validacion_publicada(c, tag, pol)
    inf(f"   validacion del checkpoint publicado (ep {meta['ep_elegido']}): {val}")
    cod = u.correr(u.EVALUAR, ["--escenario", "corredor", "--brazos", "", "--ippo", f"{pol}.pt",
                               "--semillas", "424301-424302"], c, c / "log_evaluar.txt")
    ev = {int(f["semilla"]): float(f["timeloss_prom"]) for f in filas(c / "evaluacion_corredor.csv")
          if f["brazo"].startswith("ippo_")} if cod == 0 else {}
    inf.chequeo("evaluar.py --ippo (modo antiguo) la juega con su reloj, sus mensajes y su observacion: da su "
                "validacion", cod == 0 and ev == val, f"codigo {cod}; {ev} | {val}")
    cod = u.correr(u.PLAN3 / "revalidar_c0.py", ["validar", "--escenario", "corredor", "--origen", "checkpoints",
                                                  "--corrida", tag, "--eps", "1,2", "--val-seeds", SEM,
                                                  "--salida", "c0.json"], c, c / "log_c0.txt")
    r = leer_json(c / "c0.json") if cod == 0 else {"checkpoints": []}
    reproducidos = [ck["control_reproducido"] for ck in r["checkpoints"]]
    inf.chequeo("revalidar_c0.py validar reproduce la validacion guardada de los dos checkpoints",
                cod == 0 and reproducidos == [SEMILLAS, SEMILLAS], f"codigo {cod}; reproducidas {reproducidos}")
    cod = u.correr(u.RL_NUEVO, ["demo", "--escenario", "corredor", "--politica", f"{pol}.pt", "--seed", "424301"],
                   c, c / "log_demo.txt")
    log = (c / "log_demo.txt").read_text(encoding="utf-8", errors="replace")
    aviso = [linea for linea in log.splitlines() if linea.startswith("AVISO: demo juega")]
    m = re.search(r"'timeloss_prom': ([\d.]+)", log)
    tl = float(m.group(1)) if m else None
    inf.chequeo("demo avisa que la linea de comandos pedia otras opciones (obs_cercana, paso_decision, "
                "msg_cada_paso) y juega con las del meta: da su validacion",
                cod == 0 and len(aviso) == 1 and all(o in aviso[0] for o in ("obs_cercana", "paso_decision",
                                                                             "msg_cada_paso"))
                and tl == val[424301], f"codigo {cod}; timeLoss {tl} | {val[424301]}; {aviso[:1]}")


# ---------------- B ----------------
LOTE_VACIO = '''import sys
sys.path.insert(0, {raiz!r})
import rl_ippo as ri
real = ri.correr_episodio


def falso(modo, politica, gui, delay, seed, *a, **kw):
    res = real(modo, politica, gui, delay, seed, *a, **kw)
    if modo == "train" and seed == 9:          # episodio 2 de la base 7: el lote queda sin transiciones
        for b in kw["buffer"].values():
            for k in ("obs", "mascara", "accion", "logp", "valor", "recompensa", "t"):
                b[k].clear()
    return res


ri.correr_episodio = falso
sys.argv = ["rl_ippo.py", "train", "--escenario", "corredor", "--seed", "7", "--episodios", "3", "--eval-cada", "0",
            "--v2", "--norm-valor", "--registro-extendido", "--etiqueta", "p3rvvacio"]
ri.main()
'''


def prueba_b(inf, rl_ippo):
    inf("B. Episodio sin transiciones en el lote")
    c = u.carpeta("rev_b", ["corredor"])
    (c / "lote_vacio.py").write_text(LOTE_VACIO.format(raiz=str(u.RAIZ)), encoding="utf-8")
    cod = u.correr(c / "lote_vacio.py", [], c, c / "log.txt")
    log = (c / "log.txt").read_text(encoding="utf-8", errors="replace")
    f = filas(c / "resultados_corredor_ippo_vecinos_p3rvvacio_s7.csv") if cod == 0 else []
    col = ["perdida_politica", "perdida_valor", "kl_aprox", "dt_medio", "var_explicada"]
    ok = len(f) == 3 and all(f[1][x] == "" for x in col) and all(f[k][x] != "" for k in (0, 2) for x in col)
    inf.chequeo("la corrida sigue: el episodio 2 deja vacias las columnas de la actualizacion y el 1 y el 3 no",
                cod == 0 and ok and "AVISO: el episodio 2 no dejo transiciones" in log,
                f"codigo {cod}; episodio 2: {[f[1][x] for x in col] if len(f) == 3 else '-'}")
    meta = leer_json(c / "politica_corredor_vecinos_p3rvvacio_s7.json") if cod == 0 else {}
    inf.chequeo("sin validacion, la politica publicada lleva la escala del critico (vn_media, vn_desv, vn_estado)",
                all(k in meta for k in ("vn_media", "vn_desv", "vn_estado")),
                f"{ {k: meta.get(k) for k in ('vn_media', 'vn_desv')} }")
    try:
        rl_ippo.NormValor().actualizar([])
        negado = False
    except AssertionError:
        negado = True
    inf.chequeo("NormValor.actualizar se niega con un lote vacio", negado)


# ---------------- C ----------------
def prueba_c(inf, rl_ippo):
    inf("C. Reglas nuevas de validar_args")
    b = ["train", "--escenario", "corredor", "--v2"]
    casos = [
        (b + ["--paso-decision", "2"], "va con --sin-forzadas"),
        (b + ["--paso-decision", "2", "--sin-forzadas"], None),
        (["demo", "--politica", "x.pt", "--paso-decision", "2"], None),
        (b + ["--obs-cercana", "75", "--obs-insercion"], "no va con --obs-insercion"),
        (b + ["--obs-cercana", "75", "--variante", "local"], "--variante local"),
        (b + ["--norm-valor", "--variante", "local"], "--variante local"),
        (b + ["--msg-cada-paso", "--escala-demanda", "0.5,2"], "no van con --escala-demanda"),
        (b + ["--obs-cercana", "75", "--val-escalas", "0.5,1"], "no van con --escala-demanda"),
        (b + ["--norm-valor", "--escala-demanda", "0.5,2", "--val-escalas", "0.5,1,1.5"], None),
        (b + ["--val-escalas", "1,1.0"], "niveles repetidos"),
        (b + ["--val-escalas", "0.5,1", "--eval-cada", "0"], "necesita validacion"),
        (b + ["--val-escalas", "0.5,1", "--val-seeds", ""], "necesita validacion"),
        (b + ["--escala-demanda", "0.05,2"], "entre 0.1 y 4"),
        (b + ["--val-escalas", "0.5,4.5"], "entre 0.1 y 4"),
        (b + ["--escala-demanda", "0.1,4"], None),
    ]
    hiper = dict(rl_ippo.HIPER)
    for argv, mensaje in casos:
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                rl_ippo.validar_args(argv)
            ok, detalle = mensaje is None, "acepta"
        except SystemExit as e:
            ultima = (err.getvalue().strip().splitlines() or [""])[-1]
            ok, detalle = mensaje is not None and e.code == 2 and mensaje in ultima, f"sale {e.code}: {ultima[18:120]}"
        inf.chequeo(f"{'acepta' if mensaje is None else 'rechaza'} {' '.join(argv[:1] + argv[3:])}", ok, detalle)
    inf.chequeo("HIPER y C quedan iguales", rl_ippo.HIPER == hiper and rl_ippo.C == {})


# ---------------- D ----------------
def arbol_a9ba36b():
    """El codigo de a9ba36b (raiz y plan3/, solo .py) en tmp_ent/arbol_a9ba36b, sin tocar el repositorio."""
    if ARBOL.exists():
        shutil.rmtree(ARBOL)
    ARBOL.mkdir(parents=True)
    datos = subprocess.run(["git", "archive", "--format=tar", "a9ba36b", "--", ":(glob)*.py", ":(glob)plan3/*.py"],
                           cwd=u.RAIZ, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(datos)) as t:
        t.extractall(ARBOL, filter="data")
    return ARBOL


def prueba_d(inf):
    inf("D. Reglas y Max-Pressure: el arbol de a9ba36b frente al de hoy (evaluar3.py, 424301-424302)")
    arbol = arbol_a9ba36b()
    trabajos, pares = [], []
    for esc, regla in (("corredor", "regla_u2g60"), ("malla3_alta", "mp_c90")):
        par = []
        for nombre, raiz in (("a9ba36b", arbol), ("hoy", u.RAIZ)):
            c = u.carpeta(f"rev_d_{nombre}_{esc}", [esc])
            trabajos.append((raiz / "plan3" / "evaluar3.py", ["--escenario", esc, "--regla", regla, "--semillas",
                                                              "424301-424302", "--salida", "eval.csv"], c,
                             c / "log.txt"))
            par.append(c)
        pares.append((esc, regla, par))
    cods = u.en_tandas(trabajos, maximo=2)
    for k, (esc, regla, (a, b)) in enumerate(pares):
        ok = cods[2 * k] == 0 and cods[2 * k + 1] == 0 and (a / "eval.csv").read_bytes() == (b / "eval.csv").read_bytes()
        tl = [f["timeloss_prom"] for f in filas(b / "eval.csv")] if cods[2 * k + 1] == 0 else []
        inf.chequeo(f"{regla} en {esc}: mismo CSV byte a byte", ok, f"codigos {cods[2 * k:2 * k + 2]}; timeLoss {tl}")


# ---------------- E ----------------
VARIANTES = {   # nombre: (opciones, tag, politica)
    "obs_insercion": (["--obs-insercion", "--etiqueta", "p3rvobs"], "corredor_ippo_vecinos_p3rvobs_s7",
                      "politica_corredor_vecinos_p3rvobs_s7"),
    "recompensa_insercion": (["--recompensa-insercion", "--etiqueta", "p3rvins"], "corredor_ippo_vecinos_p3rvins_s7",
                             "politica_corredor_vecinos_p3rvins_s7"),
    "spill": (["--variante", "spill"], "corredor_ippo_spill_s7", "politica_corredor_spill_s7"),
    "cambio": (["--variante", "cambio"], "corredor_ippo_cambio_s7", "politica_corredor_cambio_s7"),
}


def prueba_e(inf):
    inf("E. Variantes entregadas frente al tag (P1, base 7, 4 episodios, validacion cada 2)")
    script_tag = u.codigo_tag()
    for extra in ("rl_mappo.py", "evaluar.py"):
        texto = subprocess.run(["git", "show", f"{u.TAG}:{extra}"], cwd=u.RAIZ, capture_output=True,
                               check=True).stdout
        (u.CODIGO_TAG / extra).write_bytes(texto)
    base = ["train", "--escenario", "corredor", "--seed", "7", "--episodios", "4", "--eval-cada", "2",
            "--val-seeds", SEM]
    trabajos, carpetas = [], {}
    for nombre, (op, _, _) in VARIANTES.items():
        for quien, script in (("tag", script_tag), ("hoy", u.RL_NUEVO)):
            c = u.carpeta(f"rev_e_{nombre}_{quien}", ["corredor"])
            carpetas[(nombre, quien)] = c
            trabajos.append((script, base + op, c, c / "log.txt"))
    mappo = ["train", "--escenario", "corredor", "--seed", "7", "--episodios", "1", "--eval-cada", "1",
             "--val-seeds", "424301"]
    for quien, script in (("tag", u.CODIGO_TAG / "rl_mappo.py"), ("hoy", u.RAIZ / "rl_mappo.py")):
        c = u.carpeta(f"rev_e_mappo_{quien}", ["corredor"])
        carpetas[("mappo", quien)] = c
        trabajos.append((script, mappo, c, c / "log.txt"))
    cods = dict(zip(carpetas, u.en_tandas(trabajos, maximo=2)))
    for nombre, (_, tag, pol) in VARIANTES.items():
        a, b = carpetas[(nombre, "tag")], carpetas[(nombre, "hoy")]
        inf(f"-- {nombre}")
        if not inf.chequeo("las dos corridas salen con 0", cods[(nombre, "tag")] == 0 and cods[(nombre, "hoy")] == 0,
                           f"codigos {cods[(nombre, 'tag')]}, {cods[(nombre, 'hoy')]}"):
            continue
        inf.chequeo("CSV", *u.comparar_csv_bytes(a / f"resultados_{tag}.csv", b / f"resultados_{tag}.csv"))
        inf.chequeo("checkpoints", *u.comparar_checkpoints(a, tag, b, tag))
        inf.chequeo("politica publicada (bytes)", u.sha256(a / f"{pol}.pt") == u.sha256(b / f"{pol}.pt"))
        inf.chequeo("meta publicado", *u.comparar_json(a / f"{pol}.json", b / f"{pol}.json"))
    a, b = carpetas[("mappo", "tag")], carpetas[("mappo", "hoy")]
    inf("-- rl_mappo, un episodio")
    if inf.chequeo("las dos corridas salen con 0", cods[("mappo", "tag")] == 0 and cods[("mappo", "hoy")] == 0,
                   f"codigos {cods[('mappo', 'tag')]}, {cods[('mappo', 'hoy')]}"):
        tag = "corredor_mappo_s7"
        inf.chequeo("CSV", *u.comparar_csv_bytes(a / f"resultados_{tag}.csv", b / f"resultados_{tag}.csv"))
        pts_a = sorted(p.name for p in (a / "checkpoints").glob("*.pt"))
        pts_b = sorted(p.name for p in (b / "checkpoints").glob("*.pt"))
        iguales = pts_a == pts_b and all(u.comparar_pt(a / "checkpoints" / x, b / "checkpoints" / x)[0] for x in pts_a)
        inf.chequeo("checkpoints de actor y critico (tensores)", iguales, f"{pts_a}")
        inf.chequeo("politica publicada (bytes)", u.sha256(a / "politica_corredor_mappo_s7.pt") ==
                    u.sha256(b / "politica_corredor_mappo_s7.pt"))
    inf("-- evaluar.py --latencia 5 con la politica de --obs-insercion (semillas 424303-424304)")
    pol = VARIANTES["obs_insercion"][2]
    trabajos, cs = [], []
    for quien, script in (("tag", u.CODIGO_TAG / "evaluar.py"), ("hoy", u.EVALUAR)):
        c = u.carpeta(f"rev_e_latencia_{quien}", ["corredor"])
        for ext in (".pt", ".json"):
            shutil.copyfile(carpetas[("obs_insercion", "hoy")] / f"{pol}{ext}", c / f"{pol}{ext}")
        trabajos.append((script, ["--escenario", "corredor", "--politica", f"{pol}.pt", "--semillas", "424303-424304",
                                  "--salida", "ev.csv", "--latencia", "5"], c, c / "log.txt"))
        cs.append(c)
    cods = u.en_tandas(trabajos, maximo=2)
    ok = cods == [0, 0] and (cs[0] / "ev.csv").read_bytes() == (cs[1] / "ev.csv").read_bytes()
    inf.chequeo("mismo CSV de evaluar.py byte a byte (tag y hoy)", ok, f"codigos {cods}")


# ---------------- F ----------------
def prueba_f(inf):
    inf("F. Observacion cercana recalculada aparte (verif_e3.py del revisor R2) en red_alta")
    cfgs = {5: {"escenario": "red_alta", "paso": 5, "sin_forzadas": False, "obs": 75.0},
            2: {"escenario": "red_alta", "paso": 2, "sin_forzadas": True, "msg": True, "obs": 75.0, "norm": True}}
    trabajos, cs = [], {}
    for k, cfg in cfgs.items():
        c = u.carpeta(f"rev_f_k{k}", ["red_alta"])
        (c / "cfg.json").write_text(json.dumps(cfg), encoding="utf-8")
        trabajos.append((VERIF, [str(u.RAIZ), "cfg.json", "out.json"], c, c / "log.txt"))
        cs[k] = c
    cods = u.en_tandas(trabajos, maximo=2)
    for (k, c), cod in zip(cs.items(), cods):
        out = leer_json(c / "out.json") if cod == 0 else {}
        cerca = out.get("cerca", {})
        inf.chequeo(f"K = {k}: sin problemas y la observacion cercana coincide con la recalculada",
                    cod == 0 and out.get("problemas") == [] and cerca.get("n", 0) > 0 and cerca.get("dif") == {},
                    f"codigo {cod}; dim {out.get('dim_obs')}; lecturas {cerca.get('n')}; distintas {cerca.get('dif')}; "
                    f"marca de giro en {cerca.get('giro1')}; decisiones a los t_verde "
                    f"{out.get('decisiones_t_verde', [])[:8]}")


# ---------------- G ----------------
def prueba_g(inf):
    inf("G. Politica de forma p3obspoi en poi_corredor, jugada con ../con_escenarios.py evaluar3.py")
    c = u.carpeta("rev_g", ["poi_corredor"])
    tag, pol = "poi_corredor_ippo_vecinos_p3rvpoi_s7", "politica_poi_corredor_vecinos_p3rvpoi_s7"
    cod = u.correr(CON_ESC, [str(u.RL_NUEVO), "train", "--escenario", "poi_corredor", "--seed", "7", "--episodios",
                             "2", "--eval-cada", "1", "--val-seeds", SEM, "--v2", "--criterio-val", "total",
                             "--etiqueta", "p3rvpoi", "--obs-cercana", "75"], c, c / "log_train.txt")
    if not inf.chequeo("entrena (2 episodios, --v2 --obs-cercana 75)", cod == 0, f"codigo {cod}"):
        return
    val, meta = validacion_publicada(c, tag, pol)
    casos = {"sola": [], "colas0": ["--colas-cero"], "perdida1": ["--perdida", "1"]}
    trabajos = [(CON_ESC, [str(EVALUAR3), "--escenario", "poi_corredor", "--politica", f"{pol}.pt", "--semillas",
                           "424301-424302", "--salida", f"ev_{n}.csv"] + op, c, c / f"log_{n}.txt")
                for n, op in casos.items()]
    cods = dict(zip(casos, u.en_tandas(trabajos, maximo=2)))
    tl = {n: {int(f["semilla"]): float(f["timeloss_prom"]) for f in filas(c / f"ev_{n}.csv")}
          for n in casos if cods[n] == 0}
    inf.chequeo("las tres salen con 0", list(cods.values()) == [0, 0, 0], f"{cods}")
    inf.chequeo("sola da su validacion, semilla por semilla", tl.get("sola") == val, f"{tl.get('sola')} | {val}")
    inf(f"   con --colas-cero {tl.get('colas0')}; con --perdida 1 {tl.get('perdida1')}")


# ---------------- H ----------------
CREAR_E2 = '''import os
import sys
import time
sys.path.insert(0, {raiz!r})
import rl_ippo as ri
ri.preparar("corredor")
ri.geometria_cercana("corredor")
open("listo_{{}}".format(sys.argv[1]), "w").close()
while not os.path.exists("ya"):
    time.sleep(0.005)
print(ri.archivo_e2("corredor", 75))
'''


def prueba_h(inf):
    inf("H. Ocho procesos crean a la vez e2_corredor_75.add.xml")
    ref = u.carpeta("rev_h_uno", ["corredor"])
    c = u.carpeta("rev_h", ["corredor"])
    for d in (ref, c):
        (d / "crear_e2.py").write_text(CREAR_E2.format(raiz=str(u.RAIZ)), encoding="utf-8")
    (ref / "ya").write_text("")                 # el de referencia no espera a nadie
    cod = u.correr(ref / "crear_e2.py", ["0"], ref, ref / "log.txt")
    procesos = [u.lanzar(c / "crear_e2.py", [str(k)], c, c / f"log_{k}.txt") for k in range(8)]
    import time
    t0 = time.time()
    while len(list(c.glob("listo_*"))) < 8 and time.time() - t0 < 300 and all(p.poll() is None for p in procesos):
        time.sleep(0.05)
    (c / "ya").write_text("")
    cods = u.esperar(procesos)
    archivo = c / "e2_corredor_75.add.xml"
    restos = sorted(p.name for p in c.glob("*.tmp"))
    inf.chequeo("los ocho salen con 0, el archivo queda igual al de un proceso solo y no quedan temporales",
                cod == 0 and cods == [0] * 8 and archivo.exists()
                and archivo.read_bytes() == (ref / "e2_corredor_75.add.xml").read_bytes() and not restos,
                f"codigos {cods}; {archivo.stat().st_size if archivo.exists() else 0} bytes; temporales {restos}")


def cuerpo(inf):
    sys.path.insert(0, str(u.RAIZ))
    import con_escenarios
    con_escenarios.registrar()
    import rl_ippo
    for prueba, args in ((prueba_c, (rl_ippo,)), (prueba_h, ()), (prueba_b, (rl_ippo,)), (prueba_a, ()),
                         (prueba_f, ()), (prueba_g, ()), (prueba_d, ()), (prueba_e, ())):
        inf("")
        prueba(inf, *args)


def main():
    inf = u.Informe("prueba_revision_e34", "Revision del 05.11 sobre las Etapas 3 y 4: politicas de la Etapa 3 en "
                    "evaluar, revalidar_c0 y demo; lote vacio; validar_args; reglas antes y despues; variantes "
                    "entregadas; observacion cercana recalculada; poi_corredor; creacion concurrente de los E2")
    return u.proteger(inf, cuerpo)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
