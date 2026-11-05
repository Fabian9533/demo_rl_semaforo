"""
prueba_lanzador.py - Prueba 6 de los escenarios nuevos: con_escenarios.py y escenarios_plan3.py (B2).
  a. Por el lanzador, desde plan3/, con poi_corredor y semillas de humo: evaluar.py (brazo fijo y ciclo minimo, 2
     semillas, --salida en tmp_esc/), rl_ippo.py train (2 episodios, base 7, --v2 --criterio-val total, validacion con
     424359 y 424360, --etiqueta p3humo), evaluar.py jugando la politica de humo que sale de ahi, y barrer_fijo.py
     (--limite 3, --tmp tmp_esc_barrido, sin --instalar). Sin el lanzador, evaluar.py rechaza el escenario. Un
     programa de plan3/ corre con su carpeta en sys.path (como evaluar3.py).
  b. plan2/generar_trabajos.py, corrido sobre una COPIA de plan2/ en tmp_esc (con escenarios_plan3.py y
     con_escenarios.py al lado), da el mismo cola/trabajos.jsonl que el de plan2/, tambien si el proceso importa antes
     escenarios_plan3. Si alguien registrara los escenarios en ese proceso, la cola de plan2 creceria (se mide en la
     copia: es lo que el lanzador evita).
  c. El lanzador se niega: si rl_corredor (u otro de TOMAN_DERIVADOS) ya estaba importado; si un nombre choca (con
     DERIVADOS, con un escenario fijo o al registrar dos veces); si el programa o el cwd estan en plan2/ o TESIS/.
Uso (desde plan3/): python pruebas/esc/prueba_lanzador.py      Salida: salidas/lanzador.txt y salidas/lanzador/
"""
import os
import sys
import csv
import json
import shutil
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_esc as u                       # noqa: E402

CARPETA = os.path.join(u.TMP, "lanzador")
LANZADOR = os.path.join(u.RAIZ, "con_escenarios.py")
ENTORNO = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
p = u.Salida("lanzador.txt")
fallas = []


def ok(cond, texto):
    p(("  ok    " if cond else "  FALLA ") + texto)
    if not cond:
        fallas.append(texto)


def correr(args, cwd=u.PLAN3):
    r = subprocess.run([sys.executable] + args, cwd=cwd, capture_output=True, text=True, env=ENTORNO)
    return r.returncode, r.stdout, r.stderr


def ultima(texto):
    lineas = [l for l in texto.strip().splitlines() if l.strip()]
    return lineas[-1] if lineas else ""


def leer_csv(ruta):
    with open(ruta, newline="") as f:
        return list(csv.DictReader(f))


def parte_a():
    p("a. Programas del repositorio por el lanzador (cwd = plan3/, escenario poi_corredor)")
    rel = os.path.relpath(CARPETA, u.PLAN3)
    for brazo in ("fijo", "trivial"):
        cod, out, err = correr(["../con_escenarios.py", "../evaluar.py", "--escenario", "poi_corredor",
                                "--brazo", brazo, "--semillas", "424303-424304",
                                "--salida", f"{rel}/eval_poi_corredor_{brazo}.csv", "--extras", f"{rel}/extras"])
        filas = leer_csv(os.path.join(CARPETA, f"eval_poi_corredor_{brazo}.csv")) if cod == 0 else []
        ok(cod == 0 and [f["semilla"] for f in filas] == ["424303", "424304"] and filas[0]["brazo"] == brazo,
           f"evaluar.py --brazo {brazo}: codigo {cod}; {ultima(out)}; retraso total "
           f"{[f['retraso_total_prom'] for f in filas]}")
    cod, out, err = correr(["../evaluar.py", "--escenario", "poi_corredor", "--brazo", "fijo", "--semillas", "424303",
                            "--salida", f"{rel}/sin_lanzador.csv"])
    ok(cod != 0 and "invalid choice" in err and not os.path.exists(os.path.join(CARPETA, "sin_lanzador.csv")),
       f"evaluar.py sin el lanzador: codigo {cod}; {ultima(err)[:120]}")

    tag = "poi_corredor_ippo_vecinos_p3humo_s7"
    cod, out, err = correr(["../con_escenarios.py", "../rl_ippo.py", "train", "--escenario", "poi_corredor",
                            "--variante", "vecinos", "--seed", "7", "--episodios", "2", "--eval-cada", "2",
                            "--val-seeds", "424359,424360", "--v2", "--criterio-val", "total", "--etiqueta", "p3humo",
                            "--csv", f"{rel}/resultados_{tag}.csv"])
    publicados = [f"politica_poi_corredor_vecinos_p3humo_s7{ext}" for ext in (".pt", ".json")]
    for nombre in publicados:                    # rl_ippo publica en el cwd: se mueve a tmp_esc
        if os.path.exists(os.path.join(u.PLAN3, nombre)):
            shutil.move(os.path.join(u.PLAN3, nombre), os.path.join(CARPETA, nombre))
    restos = [os.path.join(u.PLAN3, "checkpoints", f"{tag}_ep002{ext}") for ext in (".pt", ".json")] + \
        [os.path.join(u.PLAN3, f"tripinfo_{tag}_{m}{s}.xml") for m in ("train", "val") for s in ("", "_stats")]
    for ruta in restos:                          # checkpoint y tripinfo de humo (ignorados por git)
        if os.path.exists(ruta):
            shutil.move(ruta, os.path.join(CARPETA, os.path.basename(ruta)))
    meta = json.load(open(os.path.join(CARPETA, publicados[1]), encoding="utf-8")) if cod == 0 else {}
    filas = leer_csv(os.path.join(CARPETA, f"resultados_{tag}.csv")) if cod == 0 else []
    ok(cod == 0 and len(filas) == 2 and meta.get("escenario") == "poi_corredor" and meta.get("etiqueta") == "p3humo"
       and meta.get("base") == 7 and meta.get("val_seeds") == [424359, 424360] and filas[1].get("val_total") != "",
       f"rl_ippo.py train: codigo {cod}; {ultima(out)}; semillas de los episodios "
       f"{[f['semilla'] for f in filas]}; val_total del ep. 2 {filas[1].get('val_total') if filas else ''}")
    cod, out, err = correr(["../con_escenarios.py", "../evaluar.py", "--escenario", "poi_corredor", "--politica",
                            f"{rel}/{publicados[0]}", "--semillas", "424303-424304", "--salida",
                            f"{rel}/eval_poi_corredor_p3humo.csv", "--extras", f"{rel}/extras"])
    filas = leer_csv(os.path.join(CARPETA, "eval_poi_corredor_p3humo.csv")) if cod == 0 else []
    ok(cod == 0 and len(filas) == 2 and filas[0]["brazo"] == "ippo_vecinos_p3humo_s7",
       f"evaluar.py --politica (la de humo): codigo {cod}; brazo {filas[0]['brazo'] if filas else ''}; retraso total "
       f"{[f['retraso_total_prom'] for f in filas]}")

    cod, out, err = correr(["../con_escenarios.py", "../barrer_fijo.py", "poi_corredor", "--semillas", "424303-424304",
                            "--tmp", "tmp_esc_barrido", "--procesos", "3", "--limite", "3"])
    salida = os.path.join(u.PLAN3, "barrido_poi_corredor.csv")
    filas = []
    if os.path.exists(salida):
        shutil.move(salida, os.path.join(CARPETA, "barrido_poi_corredor.csv"))
        filas = leer_csv(os.path.join(CARPETA, "barrido_poi_corredor.csv"))
    shutil.rmtree(os.path.join(u.PLAN3, "tmp_esc_barrido"), ignore_errors=True)
    aviso = [l for l in out.splitlines() if l.startswith("AVISO")]
    ok(cod == 0 and len(filas) == 3 and not os.path.exists(os.path.join(u.PLAN3, "poi_corredor.add.xml")),
       f"barrer_fijo.py --limite 3: codigo {cod}; {len(filas)} configuraciones; sin --instalar no escribe "
       f"poi_corredor.add.xml; {aviso[0] if aviso else 'sin avisos'}")
    trivial = leer_csv(os.path.join(CARPETA, "eval_poi_corredor_trivial.csv"))
    media = round(sum(float(f["retraso_total_prom"]) for f in trivial) / len(trivial), 2)
    fila = [f for f in filas if f["verde"] == "10" and f["verde_transversal"] == "10" and f["offsets"] == "0/0"]
    ok(bool(fila) and abs(float(fila[0]["retraso_total_prom"]) - media) <= 0.01,
       f"el barrido (sumo puro) en 10/10 con desfases 0 da {fila[0]['retraso_total_prom'] if fila else '?'} s/veh y el "
       f"ciclo minimo por evaluar.py (TraCI) {media}: las dos rutas ven las mismas llegadas")

    eco = os.path.join(CARPETA, "eco_plan3.py")
    with open(eco, "w", encoding="utf-8") as f:
        f.write("import sys, json\nimport demanda_estocastica\nimport rl_corredor\n"
                "print('ECO ' + json.dumps({'argv': sys.argv[1:], 'poi': 'poi_red_alta' in rl_corredor.ESCENARIOS, "
                "'dem': 'dem_red_t905' in rl_corredor.ESCENARIOS, 'demanda': demanda_estocastica.__file__}))\n")
    shutil.copyfile(eco, os.path.join(u.PLAN3, "eco_plan3_tmp.py"))
    cod, out, err = correr(["../con_escenarios.py", "eco_plan3_tmp.py", "--a", "1"])
    os.remove(os.path.join(u.PLAN3, "eco_plan3_tmp.py"))
    eco_res = json.loads(ultima(out)[4:]) if cod == 0 else {}
    ok(cod == 0 and eco_res.get("argv") == ["--a", "1"] and eco_res.get("poi") and eco_res.get("dem"),
       f"un programa de plan3/ (como evaluar3.py) corre con sus argumentos, importa modulos de plan3/ y ve los "
       f"escenarios nuevos y los de plan2: {eco_res}")


def parte_b():
    p("b. plan2/generar_trabajos.py sobre una copia de plan2/ (tmp_esc/copia_gen), nunca dentro de plan2/")
    copia = os.path.join(u.TMP, "copia_gen")
    shutil.rmtree(copia, ignore_errors=True)
    shutil.copytree(os.path.join(u.RAIZ, "plan2"), os.path.join(copia, "plan2"))
    for nombre in ("escenarios_plan2.py", "escenarios_plan3.py", "con_escenarios.py"):
        shutil.copyfile(os.path.join(u.RAIZ, nombre), os.path.join(copia, nombre))
    original = u.sha256(os.path.join(u.RAIZ, "plan2", "cola", "trabajos.jsonl"))
    jsonl = os.path.join(copia, "plan2", "cola", "trabajos.jsonl")
    gen = os.path.join(copia, "plan2", "generar_trabajos.py")
    cod, out, err = correr([gen], cwd=os.path.join(copia, "plan2"))
    ok(cod == 0 and u.sha256(jsonl) == original,
       f"con escenarios_plan3.py al lado: {ultima(out)}; sha256 {u.sha256(jsonl)[:12]}... = el de plan2/ "
       f"({original[:12]}...)")
    os.remove(jsonl)
    previo = f"import sys, runpy; sys.path.insert(0, r'{copia}'); import escenarios_plan3; " \
             f"runpy.run_path(r'{gen}', run_name='__main__')"
    cod, out, err = correr(["-c", previo], cwd=os.path.join(copia, "plan2"))
    ok(cod == 0 and u.sha256(jsonl) == original,
       f"importando antes escenarios_plan3 en el mismo proceso: {ultima(out)}; mismo sha256")
    ids_original = [json.loads(l)["id"] for l in open(jsonl, encoding="utf-8")]
    cod, out, err = correr([LANZADOR, gen], cwd=u.PLAN3)
    ok(cod != 0 and u.sha256(jsonl) == original,
       f"el lanzador se niega a correr generar_trabajos.py de una carpeta plan2 (codigo {cod}: {ultima(err)[:90]}); "
       f"la copia no cambia")
    forzado = f"import sys, runpy; sys.path.insert(0, r'{copia}'); import con_escenarios; " \
              f"con_escenarios.registrar(); runpy.run_path(r'{gen}', run_name='__main__')"
    cod, out, err = correr(["-c", forzado], cwd=os.path.join(copia, "plan2"))
    ids_forzado = [json.loads(l)["id"] for l in open(jsonl, encoding="utf-8")]
    nuevos = [i for i in ids_forzado if i not in set(ids_original)]
    p(f"  (lo que evita el lanzador, medido en la copia) con los escenarios registrados en ese proceso la cola de "
      f"plan2 pasaria de {len(ids_original)} a {len(ids_forzado)} trabajos ({len(nuevos)} nuevos, "
      f"{len(nuevos) / 13:.0f} por escenario), p. ej. {', '.join(nuevos[:3])}")
    shutil.rmtree(copia, ignore_errors=True)


def parte_c():
    p("c. El lanzador se niega cuando debe")
    raiz = u.RAIZ.replace("\\", "/")
    casos = {
        "rl_corredor ya importado": "import rl_corredor; import con_escenarios; con_escenarios.registrar()",
        "evaluar ya importado": "import evaluar; import con_escenarios; con_escenarios.registrar()",
        "nombre que ya esta en DERIVADOS": "import escenarios_plan2 as ep; "
                                           "ep.DERIVADOS['poi_corredor'] = ('corredor', 'x.sumocfg', 'corredor'); "
                                           "import con_escenarios; con_escenarios.registrar()",
        "nombre de un escenario fijo": "import escenarios_plan3 as e3; "
                                       "e3.ESTOCASTICOS['corredor_alta'] = ('corredor', 'x.sumocfg', 'corredor'); "
                                       "import con_escenarios; con_escenarios.registrar()",
        "nombre de un nivel de demanda": "import escenarios_plan3 as e3; "
                                         "e3.ESTOCASTICOS['dem_red_t905'] = ('red', 'x.sumocfg', 'red'); "
                                         "import con_escenarios; con_escenarios.registrar()",
        "registrar dos veces": "import con_escenarios; con_escenarios.registrar(); con_escenarios.registrar()",
    }
    for nombre, codigo in casos.items():
        cod, out, err = correr(["-c", f"import sys; sys.path.insert(0, r'{raiz}'); " + codigo])
        ok(cod != 0 and "con_escenarios:" in err, f"{nombre}: codigo {cod}; {ultima(err)[:110]}")
    cod, out, err = correr(["-c", f"import sys; sys.path.insert(0, r'{raiz}'); import con_escenarios; "
                                  f"print(len(con_escenarios.registrar()))"])
    ok(cod == 0 and out.strip() == "13", f"sin nada importado antes registra los {out.strip()} escenarios")
    marca = os.path.join(CARPETA, "marca_no_debe_existir.txt")
    programa = os.path.join(CARPETA, "escribe_marca.py")
    with open(programa, "w", encoding="utf-8") as f:
        f.write(f"open(r'{marca}', 'w').write('corrio')\n")
    for nombre, args, cwd in (("programa en plan2/", [LANZADOR, "../plan2/no_existe_esc.py"], u.PLAN3),
                              ("programa en TESIS/", [LANZADOR, "../TESIS/no_existe_esc.py"], u.PLAN3),
                              ("cwd en plan2/", [LANZADOR, programa], os.path.join(u.RAIZ, "plan2"))):
        cod, out, err = correr(args, cwd=cwd)
        ok(cod != 0 and "plan2/ ni de TESIS/" in err and not os.path.exists(marca),
           f"{nombre}: codigo {cod}; {ultima(err)[:100]}")
    cod, out, err = correr([LANZADOR, programa], cwd=u.PLAN3)
    ok(cod == 0 and os.path.exists(marca), "el mismo programa con cwd = plan3/ si corre (control)")


def main():
    os.chdir(u.PLAN3)
    shutil.rmtree(CARPETA, ignore_errors=True)
    os.makedirs(CARPETA)
    parte_a()
    parte_b()
    parte_c()
    destino = os.path.join(u.SALIDAS, "lanzador")
    os.makedirs(destino, exist_ok=True)
    for nombre in os.listdir(CARPETA):
        if nombre.endswith(".csv"):
            shutil.copyfile(os.path.join(CARPETA, nombre), os.path.join(destino, nombre))
    u.limpiar_generados()
    p(f"\nResultado: {'TODO OK' if not fallas else f'{len(fallas)} FALLAS'}")
    p.guardar()
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
