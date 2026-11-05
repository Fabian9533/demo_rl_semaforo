"""
prueba_protocolo.py - El cierre y la prueba final de punta a punta, con los programas de verdad, en un repositorio de
prueba con su 'origin' (un repositorio desnudo al lado) (segunda revision del 05.11: pruebas del protocolo). Sin SUMO:
lo que corre de noche se fabrica con las piezas del mundo sintetico de veredicto3 (politicas_mundo, csv_mundo,
puente_mundo y promocion_mundo), sin sus anomalias. Las semillas de los CSV son las de la tabla del prerregistro (§3;
en la prueba final, 11001-11030 y 12001-12100): son rotulos de filas sinteticas, no simulaciones.

Corren en su proceso, con el codigo del repositorio de prueba (copiado de este worktree tal como esta en disco):
generar_trabajos3.py (tambien con --partes y la parte de la enmienda), p3_noche.manifiesto_ciego (la manana),
manifiesto.py cierre, veredicto3.py --final, --sha-lista y --prueba-final, y protecciones.revisar_comando.
  0. Parte A (codigo e insumos sinteticos del puente; tag plan3-prerregistro-A) y lanzamiento (cola/caidas.json y
     generar_trabajos3.py), empujados.
  1. Noches y mananas: noche 1 (politicas, T1 y T2, promocion, puente), noche 2 (extension de H1 y aleatorias), un
     sello temprano (manifiesto.py cierre antes de tiempo) que se barre a la manana 3 (V1-M4) y una enmienda §14 que
     rehace una evaluacion con id y CSV nuevos (_r2) y conserva la salida vieja (noche 3).
  2. Cierre (PLAN3 5.1): manifiesto.py cierre se niega por la salida vieja hasta que cola/reemplazos.json la declara;
     cierre.ok; --final se niega sin el commit del cierre y sin el push; con los dos, corre.
  3. Ataques al cierre, cada uno en una copia del repositorio con su propio origin: el commit del cierre sin el sello
     (PLAN3 5.1 de antes, al pie de la letra), merge que esconde el sello, amend (sin push y con push forzado), otra
     rama, clon superficial, manana en una rama lateral, edicion sin sellar y objetos de reemplazo (git replace).
  4. Enmienda de la prueba final como codigo (tandas f1r y f1a en TANDAS, parte prueba_final en PARTES) y su lista;
     generar_trabajos3.py --partes <las del cierre>,prueba_final (lo de antes queda igual); resello; --final corre;
     holdout.ok (--sha-lista): protecciones no deja lanzar un trabajo 'final' hasta que esta commiteado y empujado.
  5. Noche final y su manana; antes, en una copia, holdout.ok commiteado despues de la noche final.
  6. Ataques a la prueba final, cada uno en su copia: edicion sin sellar, manana en una rama lateral y otra lista.
  7. --prueba-final corre una vez (exigir_semillas, bloques de verdad); otra vez con el candado en disco, se niega; se
     commitea el candado; sin el candado (borrado del disco o con git rm), con la misma lista o con otra y un segundo
     hash en holdout.ok (rev_ver2/critic/candado.py), se niega; un push forzado que borra el candado de la historia
     tambien, salvo en un clon que nunca vio la rama de antes (limite: lo cierra la proteccion de la rama en GitHub).
Escribe solo en tmp_ver/proto/ (ignorada por git) y en pruebas/ver/salidas/prueba_protocolo.txt; los commits salen con
su nombre (<cierre>, <manana 3>...) para que la salida no cambie de una corrida a otra. Unos 6 minutos.

Uso (cwd = plan3/): python -B pruebas/ver/prueba_protocolo.py
"""
import os
import re
import sys
import csv
import json
import shutil
import hashlib
import subprocess

sys.dont_write_bytecode = True
AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN3 = os.path.dirname(os.path.dirname(AQUI))
RAIZ = os.path.dirname(PLAN3)
sys.path.insert(0, PLAN3)
import veredicto3 as v3          # noqa: E402  piezas del mundo sintetico (escriben solo donde se les dice)

gt = v3.gt
TMP = os.path.join(PLAN3, "tmp_ver", "proto")
REPO = os.path.join(TMP, "repo")
P3 = os.path.join(REPO, "plan3")
ORIGEN = os.path.join(TMP, "origen.git")
SALIDA = os.path.join(AQUI, "salidas", "prueba_protocolo.txt")
ENTORNO = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
COPIAR = ["plan3", "veredicto.py", "consolidar.py", "sintesis_plan.py", ".gitattributes", ".gitignore"]
NOCHE1, NOCHE2 = ("promo", "puente", "t1r", "t2r"), ("h1t1", "h1t2", "t1a", "t2a")
REHECHA = "ev_t1r_corredor__fino"               # la evaluacion que rehace la enmienda §14 (error de codigo)
VIEJO, NUEVO = "ciego/t1r/eval_corredor__fino.csv", "ciego/t1r/eval_corredor__fino_r2.csv"
LISTA = "listo/lista_final.json"
# (celda, escenario, tanda final, tanda de examen de donde sale el brazo, a y b = (tipo, base, clave))
COMPARACIONES = [("P1", "corredor", "f1r", "t1r", ("v2reg", 42, "v2reg_s42"), ("ref_fino", "", "fino")),
                 ("P1", "poi_corredor", "f1a", "t1a", ("v2poi", 42, "v2poi_s42"), ("ref_fino", "", "fino"))]
SIN_SELLO = ":(exclude)plan3/cola/manifiesto_cierre.json"
lineas, nombres, conocidos = [], {}, set()


# ---------------- registro de la salida ----------------

def limpio(texto):
    """Sin rutas de esta maquina ni hashes (cambian de una corrida a otra): cada commit con su nombre."""
    for ruta in (TMP, TMP.replace(os.sep, "/"), TMP.replace(os.sep, "\\\\")):
        texto = texto.replace(ruta, "<tmp>")
    for h in sorted(conocidos, key=len, reverse=True):
        nombre = f"<{nombres[h]}>" if h in nombres else "<commit>"
        for n in (40, 10, 7):
            texto = texto.replace(h[:n], nombre)
    texto = re.sub(r"\b[0-9a-f]{64}\b", "<sha256>", texto)
    return re.sub(r"\b(?=[0-9]*[a-f])[0-9a-f]{7,40}\b", "<commit>", texto)


def ok(cond, texto):
    lineas.append(("PASA  " if cond else "FALLA ") + limpio(texto))
    print(lineas[-1][:160], flush=True)
    return cond


def nota(texto):
    lineas.append("      " + limpio(texto))


def titulo(texto):
    lineas.append(f"--- {texto}")
    print(lineas[-1], flush=True)


# ---------------- git y programas ----------------

def git(cwd, *args, check=True):
    r = subprocess.run(["git", "-c", "core.longpaths=true", *args], cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:4])}: {r.stderr.strip()[:300]}")
    return r.stdout.strip()


def conocer(repo):
    """Los commits de repo, para que la salida los nombre (o diga <commit>) en lugar del hash."""
    conocidos.update(git(repo, "rev-list", "--all").split())


def correr(p3, *args):
    """(rc, texto) de python -B <args> en la carpeta plan3 p3 (con su codigo y sus datos)."""
    r = subprocess.run([sys.executable, "-B", *args], cwd=p3, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=ENTORNO)
    conocer(os.path.dirname(p3))
    return r.returncode, (r.stdout + "\n" + r.stderr).strip()


def motivo(texto):
    """La linea con la causa: la de sys.exit (veredicto3:, manifiesto:...) y la primera 'MAL', o la ultima."""
    filas = [x.strip() for x in texto.splitlines() if x.strip()]
    salida = next((x for x in reversed(filas) if x.startswith(("veredicto3:", "manifiesto:", "generar_trabajos3:"))),
                  filas[-1] if filas else "")
    mal = next((x for x in filas if x.startswith("MAL ")), None)
    return salida + (f" [{mal}]" if mal else "")


def corre(texto, res, esperado):
    rc, salida = res
    linea = next((x.strip() for x in salida.splitlines() if esperado in x), motivo(salida))
    return ok(rc == 0 and esperado in salida, f"{texto}: corre ({linea[:220]})")


def se_niega(texto, res, esperado):
    rc, salida = res
    return ok(rc != 0 and esperado in salida, f"{texto}: se niega ({motivo(salida)[:400]})")


def commit(repo, nombre, *rels, forzar=(), empujar=True):
    """add -A de rels (y add -f de forzar: lo ignorado, como ciego/), commit y push de plan3."""
    if rels:
        git(repo, "add", "-A", "--", *rels)
    if forzar:
        git(repo, "add", "-f", "--", *forzar)
    git(repo, "commit", "-q", "-m", nombre)
    h = git(repo, "rev-parse", "HEAD")
    nombres[h] = nombre
    conocidos.add(h)
    if empujar:
        git(repo, "push", "-q", "origin", "plan3")
    return h


def manana(repo, nombre, con_sello=False, excluir=()):
    """La manana: p3_noche.manifiesto_ciego() y un commit de plan3/ (nunca ciego/; el sello, solo si con_sello: el
    error que PLAN3 5.1 prohibe; sin lo de excluir) con push."""
    rc, salida = correr(os.path.join(repo, "plan3"), "-c", "import p3_noche; print(p3_noche.manifiesto_ciego())")
    if rc != 0:
        raise RuntimeError(f"p3_noche.manifiesto_ciego: {salida[-300:]}")
    return commit(repo, nombre, "plan3", *([] if con_sello else [SIN_SELLO]),
                  *[f":(exclude){x}" for x in excluir])


def copia(nombre):
    """Una copia del repositorio de prueba tal como esta (con lo ignorado: ciego/, el candado...) y con su propio
    origin (copia del desnudo): cada ataque en la suya."""
    base = v3.carpeta_limpia(os.path.join(TMP, "c", nombre)) or os.path.join(TMP, "c", nombre)
    r = os.path.join(base, "r")
    shutil.copytree(REPO, r)
    git(base, "clone", "-q", "--bare", ORIGEN, "o.git")
    git(r, "remote", "set-url", "origin", os.path.join(base, "o.git"))
    return r


def leer(ruta):
    with open(ruta, encoding="utf-8-sig") as f:
        return json.load(f)


def escribir_json(ruta, datos):
    v3.escribir(ruta, json.dumps(datos, indent=1, ensure_ascii=False) + "\n")


def listas(p3):
    with open(os.path.join(p3, "cola", "trabajos.jsonl"), encoding="utf-8") as f:
        trabajos = [json.loads(x) for x in f if x.strip()]
    return trabajos, leer(os.path.join(p3, "cola", "manifiesto_esperado.json"))


def commit_arbol(repo, padre, archivos, mensaje, base=None):
    """Un commit (sin checkout ni tocar el disco) con el arbol de base (por defecto, el de padre) y archivos {ruta del
    repositorio: bytes}; el padre, padre. Sin checkout: git no reescribe ningun archivo del disco."""
    indice = os.path.join(os.path.dirname(repo), "indice_tmp")
    entorno = dict(os.environ, GIT_INDEX_FILE=indice)

    def g(*args, entrada=None):
        r = subprocess.run(["git", *args], cwd=repo, capture_output=True, env=entorno, input=entrada)
        if r.returncode != 0:
            raise RuntimeError(f"git {args[0]}: {r.stderr.decode('utf-8', 'replace')[:300]}")
        return r.stdout.decode().strip()
    g("read-tree", base or padre)
    for ruta, contenido in archivos.items():
        blob = g("hash-object", "-w", "--stdin", entrada=contenido)
        g("update-index", "--add", "--cacheinfo", f"100644,{blob},{ruta}")
    arbol = g("write-tree")
    h = g("commit-tree", arbol, "-p", padre, "-m", mensaje)
    os.remove(indice)
    nombres[h] = mensaje
    conocidos.add(h)
    return h


def binario(ruta):
    with open(ruta, "rb") as f:
        return f.read()


def cambiar_promocion(p3):
    """Lo que querria cambiar quien resella despues de ver los datos: la promocion de corredor al reves."""
    ruta = os.path.join(p3, "promocion", "corredor.json")
    d = leer(ruta)
    d["promovido"] = not d["promovido"]
    citado = d["candidatos"][0] if d["promovido"] else d["v2"]
    d["modelo_citado"], d["csv_citado"] = citado["brazo"], citado["csv"]
    with open(ruta, "w", encoding="utf-8") as f:                    # como p3_promocion.escribir
        json.dump(d, f, indent=1, ensure_ascii=False)
    ruta_p = os.path.join(p3, "promocion.json")
    todo = leer(ruta_p)
    todo["celdas"]["corredor"].update(sha256=hashlib.sha256(binario(ruta)).hexdigest(),
                                      modelo_citado=d["modelo_citado"], promovido=d["promovido"])
    with open(ruta_p, "w", encoding="utf-8") as f:
        json.dump(todo, f, indent=1, ensure_ascii=False)
    return ["plan3/promocion/corredor.json", "plan3/promocion.json"]


def resellar(r):
    """La promocion al reves y manifiesto.py cierre en la copia r: {ruta del repositorio: bytes} de lo que cambia."""
    p3 = os.path.join(r, "plan3")
    rutas = cambiar_promocion(p3)
    rc, salida = correr(p3, "manifiesto.py", "cierre")
    if rc != 0:
        raise RuntimeError(f"resello en la copia: {motivo(salida)}")
    rutas.append("plan3/cola/manifiesto_cierre.json")
    return {x: binario(os.path.join(r, x)) for x in rutas}


def final(p3, *extra):
    return correr(p3, "veredicto3.py", "--final", *extra)


def prueba_final(p3, lista=LISTA):
    return correr(p3, "veredicto3.py", "--prueba-final", lista)


# ---------------- 0 y 1: parte A, lanzamiento, noches y mananas ----------------

def preparar():
    titulo("0. Parte A y lanzamiento (repositorio de prueba con su origin)")
    v3.carpeta_limpia(TMP)
    r = subprocess.run(["git", "ls-files", "-z", "--", *COPIAR], cwd=RAIZ, capture_output=True)
    for rel in filter(None, r.stdout.decode("utf-8").split("\0")):
        if os.path.exists(os.path.join(RAIZ, rel)):
            os.makedirs(os.path.dirname(os.path.join(REPO, rel)), exist_ok=True)
            shutil.copyfile(os.path.join(RAIZ, rel), os.path.join(REPO, rel))
    git(TMP, "init", "-q", "--bare", ORIGEN)
    git(REPO, "init", "-q")
    git(REPO, "checkout", "-q", "-b", "plan3")
    for clave, valor in (("user.name", "Prueba del protocolo"), ("user.email", "prueba@ejemplo.invalid"),
                         ("commit.gpgsign", "false"), ("tag.gpgsign", "false")):
        git(REPO, "config", clave, valor)
    git(REPO, "remote", "add", "origin", ORIGEN)
    escribir_json(os.path.join(P3, "cola", "caidas.json"), [
        {"corrida": corrida, "celda": c, "escenario": esc, "tipo": tipo, "base": b, "fecha": "2026-11-16",
         "intentos": [{"id": f"e2_v2poi_{esc}_s{b}", "error": "pérdida NaN", "fecha": "2026-11-15 03:10"},
                      {"id": f"e2_v2poi_{esc}_s{b}_r2", "error": "pérdida NaN", "fecha": "2026-11-16 02:55"}]}
        for c, esc, tipo, b, corrida in v3.CAIDAS_MUNDO])
    corre("generar_trabajos3.py escribe la lista y el manifiesto (con las dos bases caídas declaradas)",
          correr(P3, "generar_trabajos3.py"), "CSV esperados")
    trabajos, man = listas(P3)
    v3.politicas_mundo(P3, trabajos)
    v3.puente_mundo(P3, gt.TANDAS["puente"][1])
    commit(REPO, "parte A", ".", ":(exclude)plan3/politica_*", ":(exclude)plan3/cola", empujar=False)
    git(REPO, "tag", "plan3-prerregistro-A")
    git(REPO, "push", "-q", "origin", "plan3", "plan3-prerregistro-A")
    commit(REPO, "lanzamiento", "plan3/cola")
    nota(f"{len(trabajos)} trabajos, {len(man)} CSV esperados; semillas de la tabla del prerregistro (rótulos)")
    return trabajos, man


def noches(trabajos, man):
    titulo("1. Noches y mañanas (cada mañana: p3_noche.manifiesto_ciego, commit sin ciego/ y push)")
    v3.csv_mundo(P3, man, trabajos, lambda e: e["tanda"] in NOCHE1, anomalias=False)
    v3.promocion_mundo(P3, man, v3.rango(gt.TANDAS["promo"][1]))
    m1 = manana(REPO, "manana 1")
    v3.csv_mundo(P3, man, trabajos, lambda e: e["tanda"] in NOCHE2, anomalias=False)
    manana(REPO, "manana 2")
    corre("un sello temprano (manifiesto.py cierre antes de tiempo; después se barre a la mañana 3)",
          correr(P3, "manifiesto.py", "cierre"), "manifiesto_cierre.json: ")
    # enmienda §14 (error de codigo en una evaluacion): id y CSV nuevos; la salida vieja se conserva
    ruta_g = os.path.join(P3, "generar_trabajos3.py")
    with open(ruta_g, encoding="utf-8") as f:
        texto = f.read()
    a = '    uso, semillas = TANDAS[tanda]\n    carpeta = "ciego" if uso in CIEGAS else "parciales"\n'
    b = "def evaluacion(lista, celda, esc, tanda, clave, brazo,"
    assert texto.count(a) == 1 and texto.count(b) == 1
    texto = texto.replace(a, '    uso, semillas = TANDAS[tanda]\n'
                             '    if f"ev_{tanda}_{esc}__{clave}" in REHECHAS:     # enmienda del 2026-11-20 (§14)\n'
                             '        clave = f"{clave}_r2"\n'
                             '    carpeta = "ciego" if uso in CIEGAS else "parciales"\n')
    texto = texto.replace(b, "# Enmienda del 2026-11-20 (prerregistro §14): un error de codigo en esta evaluacion; se "
                             "corre con id y CSV\n# nuevos (_r2) y la salida vieja se conserva (cola/reemplazos.json)\n"
                             f'REHECHAS = {{"{REHECHA}"}}\n\n\n' + b)
    with open(ruta_g, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    corre("la enmienda §14 como código: generar_trabajos3.py da el trabajo y el CSV nuevos (_r2)",
          correr(P3, "generar_trabajos3.py"), "CSV esperados")
    trabajos, man = listas(P3)
    ids, csvs = {t["id"] for t in trabajos}, {e["csv"] for e in man}
    ok(REHECHA + "_r2" in ids and REHECHA not in ids and NUEVO in csvs and VIEJO not in csvs,
       f"después de la enmienda §14: {REHECHA}_r2 y {NUEVO} en las listas; {VIEJO} queda en disco y en las "
       f"mañanas 1 y 2")
    commit(REPO, "enmienda r2", "plan3/generar_trabajos3.py", "plan3/cola/trabajos.jsonl",
           "plan3/cola/manifiesto_esperado.json", "plan3/cola/partes.txt")
    v3.csv_mundo(P3, man, trabajos, lambda e: e["csv"] == NUEVO, anomalias=False)
    m3 = manana(REPO, "manana 3", con_sello=True)
    ok(git(REPO, "show", "--name-only", "--format=", "HEAD").count("plan3/cola/manifiesto_cierre.json") == 1,
       "la mañana 3 se lleva por error el sello temprano (lo que PLAN3 5.1 prohíbe; V1-M4)")
    return trabajos, man, m1, m3


# ---------------- 2: cierre ----------------

def cierre():
    titulo("2. Cierre (PLAN3 5.1)")
    se_niega("manifiesto.py cierre con la salida vieja conservada y sin declarar",
             correr(P3, "manifiesto.py", "cierre"), VIEJO)
    escribir_json(os.path.join(P3, "cola", "reemplazos.json"), [
        {"viejo": VIEJO, "nuevo": NUEVO, "motivo": "error de código en la evaluación (§14, enmienda del 2026-11-20)",
         "fecha": "2026-11-21"}])
    m4 = manana(REPO, "manana 4")
    corre("con cola/reemplazos.json commiteado (mañana 4), manifiesto.py cierre escribe el sello",
          correr(P3, "manifiesto.py", "cierre"), "manifiesto_cierre.json: ")
    v3.escribir(os.path.join(P3, "listo", "cierre.ok"), "cierre: Fabian, 2026-11-28 09:00\n")
    # PLAN3 5.1 de antes, al pie de la letra: cierre.ok y los CSV en un commit, sin el sello
    r = copia("sin_sello")
    commit(r, "cierre sin el sello", "plan3/listo/cierre.ok", forzar=["plan3/ciego"])
    se_niega("el commit del cierre sin el sello (PLAN3 5.1 de antes; el de su árbol es el temprano de la mañana 3)",
             final(os.path.join(r, "plan3")), "es un sello viejo")
    se_niega("--final con cierre.ok sin commitear", final(P3), "listo/cierre.ok no está commiteado")
    c = commit(REPO, "cierre", "plan3/cola", "plan3/listo", forzar=["plan3/ciego"], empujar=False)
    se_niega("--final con el commit del cierre sin push", final(P3), "no está en origin/plan3")
    git(REPO, "push", "-q", "origin", "plan3")
    res = final(P3)
    if corre("--final con el commit del cierre (sello, cierre.ok, cola/ y ciego/) empujado", res, "escrito"):
        for x in res[1].splitlines():
            if x.startswith("numero unico"):
                nota(x)
    return c, m4


# ---------------- 3: ataques al cierre ----------------

def ataques_cierre(c, m1, m4):
    titulo("3. Ataques al cierre (cada uno en su copia, con su origin)")
    # merge que esconde el sello (V1-H1, k1): un cierre en una rama desde la manana 4, mezclado con -X theirs
    r = copia("merge")
    nuevos = resellar(r)
    git(r, "checkout", "-q", "--", *nuevos)
    nuevos["plan3/listo/cierre.ok"] = binario(os.path.join(r, "plan3", "listo", "cierre.ok"))
    lado = commit_arbol(r, m4, nuevos, "cierre (lado)")
    git(r, "branch", "lado", lado)
    git(r, "merge", "-q", "--no-edit", "-X", "theirs", "lado")
    nombres[git(r, "rev-parse", "HEAD")] = "merge del lado"
    git(r, "push", "-q", "origin", "plan3")
    se_niega("merge (empujado) que trae otro sello desde una rama lateral", final(os.path.join(r, "plan3")),
             "no forman una sola cadena")
    # amend del cierre: sin push y con push forzado (V1-H1)
    r = copia("amend")
    git(r, "add", "--", *resellar(r))
    git(r, "commit", "-q", "--amend", "--no-edit")
    nombres[git(r, "rev-parse", "HEAD")] = "cierre rehecho"
    se_niega("amend del commit del cierre, sin push", final(os.path.join(r, "plan3")), "no está en origin/plan3")
    git(r, "push", "-q", "-f", "origin", "plan3")
    se_niega("amend del commit del cierre con push forzado", final(os.path.join(r, "plan3")),
             "se reescribió (push forzado)")
    # otra rama: su propio cierre, empujado como otra rama
    r = copia("otra")
    nuevos = resellar(r)
    git(r, "checkout", "-q", "--", *nuevos)
    otra = commit_arbol(r, m4, nuevos, "cierre (otra rama)", base=c)
    git(r, "branch", "otra", otra)
    git(r, "checkout", "-q", "otra")
    git(r, "push", "-q", "origin", "otra")
    se_niega("otra rama con su propio cierre (empujada como otra rama)", final(os.path.join(r, "plan3")),
             "no está en origin/plan3")
    # clon superficial
    base = v3.carpeta_limpia(os.path.join(TMP, "c", "superficial")) or os.path.join(TMP, "c", "superficial")
    git(base, "clone", "-q", "--depth", "1", "-b", "plan3", "file:///" + ORIGEN.replace(os.sep, "/"), "r")
    se_niega("clon superficial (shallow) de la rama empujada", final(os.path.join(base, "r", "plan3")), "superficial")
    # manana en una rama lateral (V1-H1, k4): un CSV cambiado despues de su manana, una manana nueva desde la 1,
    # mezclada, y el sello arreglado a mano
    r = copia("manana_lado")
    p3 = os.path.join(r, "plan3")
    rel = "ciego/t1a/eval_poi_corredor__v2poi_s42.csv"
    with open(os.path.join(p3, rel), encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    for x in filas:
        x["retraso_total_prom"] = str(round(float(x["retraso_total_prom"]) * 0.85, 4))
    v3.escribir(os.path.join(p3, rel), v3.texto_csv(filas, list(filas[0])))
    rc, salida = correr(p3, "-c", "import p3_noche; print(p3_noche.manifiesto_ciego())")
    lado = commit_arbol(r, m1, {"plan3/cola/manifiesto_ciego.json": binario(os.path.join(p3, "cola",
                                                                                   "manifiesto_ciego.json"))},
                        "manana 2 (lado)")
    git(r, "checkout", "-q", "--", "plan3/cola/manifiesto_ciego.json")
    git(r, "branch", "lado", lado)
    git(r, "merge", "-q", "--no-edit", "-X", "theirs", "lado")
    nombres[git(r, "rev-parse", "HEAD")] = "merge del lado"
    sello = leer(os.path.join(p3, "cola", "manifiesto_cierre.json"))
    sello["csv"][rel] = hashlib.sha256(binario(os.path.join(p3, rel))).hexdigest()
    v3.escribir(os.path.join(p3, "cola", "manifiesto_cierre.json"), json.dumps(sello, indent=0, sort_keys=True))
    commit(r, "sello arreglado", "plan3/cola/manifiesto_cierre.json")
    se_niega("una mañana en una rama lateral (un CSV cambiado después de su mañana, mezclada y empujada)",
             final(p3), "no forman una sola cadena")
    # edicion sin sellar del manifiesto esperado
    r = copia("edicion")
    p3 = os.path.join(r, "plan3")
    man = leer(os.path.join(p3, "cola", "manifiesto_esperado.json"))
    for e in man:
        if e["tanda"] == "t1r" and e["escenario"] == "corredor" and e["tipo"] == "v2reg" and e["base"] == 42:
            e["semillas"] = "8001-8029"
    v3.escribir(os.path.join(p3, "cola", "manifiesto_esperado.json"), json.dumps(man, indent=0) + "\n")
    se_niega("cola/manifiesto_esperado.json editado después del cierre, sin sellar", final(p3),
             "manifiesto_esperado.json cambió después del cierre")
    # objetos de reemplazo (git replace): el commit del cierre 'muestra' otro sello
    r = copia("replace")
    git(r, "add", "--", *resellar(r))
    git(r, "commit", "-q", "--amend", "--no-edit")
    falso = git(r, "rev-parse", "HEAD")
    nombres[falso] = "cierre falso"
    git(r, "replace", c, falso)
    git(r, "reset", "-q", "--soft", c)
    visto = git(r, "show", f"{c}:plan3/cola/manifiesto_cierre.json") == git(r, "show", f"{falso}:plan3/cola/"
                                                                               f"manifiesto_cierre.json")
    se_niega(f"git replace del commit del cierre por uno con otro sello (git sin GIT_NO_REPLACE_OBJECTS lo ve: "
             f"{visto})", final(os.path.join(r, "plan3")), "no es el del cierre")
    # observacion: un clon nuevo con autocrlf (Windows) cambia los fines de linea de lo que se escribio con LF
    base = v3.carpeta_limpia(os.path.join(TMP, "c", "clon")) or os.path.join(TMP, "c", "clon")
    git(base, "-c", "core.autocrlf=true", "clone", "-q", "-b", "plan3", ORIGEN, "r")
    rc, salida = final(os.path.join(base, "r", "plan3"))
    nota(f"OBSERVACIÓN: --final en un clon nuevo con core.autocrlf=true: rc {rc} ({motivo(salida)[:300]})")


# ---------------- 4 a 7: la prueba final ----------------

def enmienda_final(trabajos, man):
    titulo("4. Enmienda de la prueba final (PLAN3 5.3): código, lista, resello y holdout.ok")
    por_id = {t["id"]: t for t in trabajos}
    brazos = []
    for celda, esc, tanda, examen, *lados in COMPARACIONES:
        for tipo, base, clave in lados:
            e = next(x for x in man if (x["escenario"], x["tanda"], x["tipo"], x["base"]) == (esc, examen, tipo, base))
            brazo = por_id[e["trabajo"]]["cmd"].split(f"--salida {e['csv']} ", 1)[1]
            brazos.append((celda, esc, tanda, clave, brazo, tipo, base))
    ruta_g = os.path.join(P3, "generar_trabajos3.py")
    with open(ruta_g, encoding="utf-8") as f:
        texto = f.read()
    a = '"promo": ("promocion", "15009-15024")}'
    b = "PARTES = {"
    c_ = 'PARTES_PLAN = [p for p in PARTES if p not in ("etapa3b_reg", "etapa3b_poi")]'
    assert texto.count(a) == 1 and texto.count(b) == 1 and texto.count(c_) == 1
    texto = texto.replace(a, '"promo": ("promocion", "15009-15024"),\n'
                             '          "f1r": ("final", "11001-11030"), "f1a": ("final", "12001-12100")}  '
                             '# enmienda del 2026-11-29 (§13)')
    parte = ("# Enmienda del 2026-11-29 (prerregistro §13): la prueba final, con la lista exacta de "
             "listo/lista_final.json\nBRAZOS_FINAL = [\n"
             + "".join(f"    {x!r},\n" for x in brazos)
             + "]\n\n\ndef prueba_final(lista):\n    for celda, esc, tanda, clave, brazo, tipo, base in BRAZOS_FINAL:\n"
               "        evaluacion(lista, celda, esc, tanda, clave, brazo, tipo=tipo, base=base)\n\n\n")
    texto = texto.replace(b, parte + 'PARTES = {"prueba_final": prueba_final, ')
    texto = texto.replace(c_, 'PARTES_PLAN = [p for p in PARTES if p not in ("etapa3b_reg", "etapa3b_poi", '
                              '"prueba_final")]')
    with open(ruta_g, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    with open(os.path.join(P3, "cola", "partes.txt"), encoding="utf-8") as f:
        partes = f.read().strip()
    corre("generar_trabajos3.py --partes <las del cierre>,prueba_final",
          correr(P3, "generar_trabajos3.py", "--partes", f"{partes},prueba_final"), "CSV esperados")
    trabajos_f, man_f = listas(P3)
    finales = [e for e in man_f if e["tanda"] in ("f1r", "f1a")]
    ok([t for t in trabajos_f if t.get("uso") != "final"] == trabajos
       and [e for e in man_f if e["tanda"] not in ("f1r", "f1a")] == man
       and len(finales) == 4 and all(t["uso"] == "final" for t in trabajos_f[len(trabajos):]),
       f"lo que no es de la prueba final queda igual en la lista y en el manifiesto; se agregan {len(finales)} CSV "
       f"(uso 'final', 11001-11030 y 12001-12100)")
    escribir_json(os.path.join(P3, LISTA), {"comparaciones": [
        {"celda": celda, "escenario": esc, "tanda": tanda, "a": {"tipo": a_[0], **({"base": a_[1]} if a_[1] else {})},
         "b": {"tipo": b_[0], **({"base": b_[1]} if b_[1] else {})}}
        for celda, esc, tanda, _, a_, b_ in COMPARACIONES]})
    commit(REPO, "enmienda de la prueba final", "plan3/generar_trabajos3.py", "plan3/cola/trabajos.jsonl",
           "plan3/cola/manifiesto_esperado.json", "plan3/cola/partes.txt", f"plan3/{LISTA}")
    corre("resello (manifiesto.py cierre): los CSV de la prueba final todavía no existen y no se sellan",
          correr(P3, "manifiesto.py", "cierre"), "resello de la prueba final")
    commit(REPO, "resello", "plan3/cola/manifiesto_cierre.json")
    corre("--final con el resello (solo le agrega la prueba final al sello del cierre)", final(P3), "escrito")
    rc, sha = correr(P3, "veredicto3.py", "--sha-lista", LISTA)
    v3.escribir(os.path.join(P3, "listo", "holdout.ok"), sha.strip() + "\n")
    t_final = json.dumps(trabajos_f[-1])
    codigo = ("import json, protecciones; print(json.dumps([m for m in protecciones.revisar_comando(json.loads("
              f"{t_final!r})) if 'holdout' in m], ensure_ascii=False))")
    estados = [json.loads(correr(P3, "-c", codigo)[1].splitlines()[-1])]
    copia("holdout_tarde")                    # para el paso 5: holdout.ok commiteado despues de la noche final
    commit(REPO, "holdout.ok", "plan3/listo/holdout.ok", empujar=False)
    estados.append(json.loads(correr(P3, "-c", codigo)[1].splitlines()[-1]))
    git(REPO, "push", "-q", "origin", "plan3")
    estados.append(json.loads(correr(P3, "-c", codigo)[1].splitlines()[-1]))
    ok(len(estados[0]) == 1 and "commiteado" in estados[0][0] and len(estados[1]) == 1
       and "no esta empujado" in estados[1][0] and estados[2] == [],
       f"protecciones.revisar_comando de un trabajo 'final': holdout.ok sin commitear, sin push y empujado {estados}")
    return trabajos_f, man_f


def noche_final(trabajos_f, man_f):
    titulo("5. Noche final y su mañana")
    # PLAN3 5.3 fuera de orden: holdout.ok commiteado despues de la noche final (en su copia)
    r = os.path.join(TMP, "c", "holdout_tarde", "r")
    p3 = os.path.join(r, "plan3")
    v3.csv_mundo(p3, man_f, trabajos_f, lambda e: e["tanda"] in ("f1r", "f1a"), anomalias=False)
    manana(r, "manana de la noche final (antes de holdout.ok)", excluir=["plan3/listo/holdout.ok"])
    commit(r, "holdout.ok tarde", "plan3/listo/holdout.ok")
    se_niega("holdout.ok commiteado después de la noche final (su mañana lista los CSV)", prueba_final(p3),
             "que no es posterior a")
    v3.csv_mundo(P3, man_f, trabajos_f, lambda e: e["tanda"] in ("f1r", "f1a"), anomalias=False)
    manana(REPO, "manana 5")
    filas = {}
    for e in man_f:
        if e["tanda"] in ("f1r", "f1a"):
            with open(os.path.join(P3, e["csv"]), encoding="utf-8", newline="") as f:
                semillas = [int(x["semilla"]) for x in csv.DictReader(f)]
            filas[e["csv"]] = (semillas[0], semillas[-1], len(semillas))
    ok(sorted(set(filas.values())) == [(11001, 11030, 30), (12001, 12100, 100)],
       f"los CSV de la noche final tienen los bloques de §13 {sorted(set(filas.values()))}")


def ataques_final(c_resello):
    titulo("6. Ataques a la prueba final (cada uno en su copia)")
    r = copia("f_edicion")
    p3 = os.path.join(r, "plan3")
    man = leer(os.path.join(p3, "cola", "manifiesto_esperado.json"))
    a, b = [e for e in man if e["tanda"] == "f1r"][:2]
    a["csv"], b["csv"] = b["csv"], a["csv"]
    v3.escribir(os.path.join(p3, "cola", "manifiesto_esperado.json"), json.dumps(man, indent=0) + "\n")
    se_niega("los dos brazos de f1r intercambiados en cola/manifiesto_esperado.json, sin sellar", prueba_final(p3),
             "manifiesto_esperado.json cambió después del cierre")
    r = copia("f_lado")
    p3 = os.path.join(r, "plan3")
    lado = commit_arbol(r, c_resello, {"plan3/cola/manifiesto_ciego.json": binario(os.path.join(
        p3, "cola", "manifiesto_ciego.json"))}, "manana final (lado, antes de holdout.ok)")
    git(r, "branch", "lado", lado)
    git(r, "merge", "-q", "--no-edit", "-X", "ours", "lado")
    nombres[git(r, "rev-parse", "HEAD")] = "merge del lado"
    git(r, "push", "-q", "origin", "plan3")
    se_niega("una mañana con los CSV finales en una rama lateral desde el resello (V1-H4), mezclada y empujada",
             prueba_final(p3), "no forman una sola cadena")
    r = copia("f_lista")
    p3 = os.path.join(r, "plan3")
    lista = leer(os.path.join(p3, LISTA))
    for x in lista["comparaciones"]:
        x["a"], x["b"] = x["b"], x["a"]
    escribir_json(os.path.join(p3, "listo", "lista_2.json"), lista)
    se_niega("otra lista (la de la enmienda al revés)", prueba_final(p3, "listo/lista_2.json"),
             "no tiene el sha256 de la lista")


def prueba_final_y_candado():
    titulo("7. La prueba final (una vez) y el candado")
    res = prueba_final(P3)
    corre("--prueba-final con la lista de la enmienda (exigir_semillas: los bloques de §13)", res,
          "prueba final: 2 comparaciones")
    with open(os.path.join(P3, v3.SALIDA_FINAL), encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    ok([(x["escenario"], x["tanda"], x["n"]) for x in filas] == [("corredor", "f1r", "30"),
                                                                  ("poi_corredor", "f1a", "100")]
       and all(x["nota"].startswith("elegido después de ver T1 y T2") for x in filas),
       "salidas/veredicto3_prueba_final.csv: una fila por comparación, con n = 30 y 100 y la nota de §13")
    for x in filas:
        nota(f"{x['escenario']} {x['tanda']}: {x['brazo']} frente a {x['referencia']}: {x['cambio']} % {x['ic']}")
    se_niega("otra vez, con el candado en disco", prueba_final(P3), "ya corrió")
    commit(REPO, "candado", "plan3/listo/holdout.candado", "plan3/salidas/veredicto3_prueba_final.csv",
           forzar=["plan3/ciego/f1r", "plan3/ciego/f1a"])
    r = copia("sin_candado")
    p3 = os.path.join(r, "plan3")
    os.remove(os.path.join(p3, "listo", "holdout.candado"))
    os.remove(os.path.join(p3, v3.SALIDA_FINAL))
    se_niega("el candado borrado del disco (commiteado antes), la misma lista", prueba_final(p3), "está en disco o "
             "en la historia")
    r = copia("critico")
    p3 = os.path.join(r, "plan3")
    os.remove(os.path.join(p3, "listo", "holdout.candado"))
    lista = leer(os.path.join(p3, LISTA))
    for x in lista["comparaciones"]:
        x["a"], x["b"] = x["b"], x["a"]
    escribir_json(os.path.join(p3, "listo", "lista_2.json"), lista)
    with open(os.path.join(p3, "listo", "holdout.ok"), "a", encoding="utf-8") as f:
        f.write(v3.sha_lista(os.path.join(p3, "listo", "lista_2.json")) + "\n")
    se_niega("rev_ver2/critic/candado.py: sin el candado, otra lista y su sha256 agregado a holdout.ok",
             prueba_final(p3, "listo/lista_2.json"), "listo/holdout.ok de hoy no es el que se commiteó")
    r = copia("git_rm")
    p3 = os.path.join(r, "plan3")
    git(r, "rm", "-q", "plan3/listo/holdout.candado")
    commit(r, "borra el candado")
    se_niega("el candado borrado con git rm (commit y push)", prueba_final(p3), "está en disco o en la historia")
    # un push forzado desde otro clon saca el candado de la rama empujada; en el repositorio del operador (que empujo
    # el candado) se borra del disco
    r = copia("forzado")
    p3 = os.path.join(r, "plan3")
    base = os.path.dirname(r)
    git(base, "clone", "-q", "--no-checkout", os.path.join(base, "o.git"), "otro")
    git(os.path.join(base, "otro"), "push", "-q", "-f", "origin", "origin/plan3~1:refs/heads/plan3")
    os.remove(os.path.join(p3, "listo", "holdout.candado"))
    se_niega("un push forzado desde otro clon saca el candado de la rama empujada (en el repositorio que la vio)",
             prueba_final(p3), "se reescribió (push forzado)")
    # el que hace el push forzado desde su propio repositorio (reset y push -f): el reflog guarda el candado
    r = copia("forzado_propio")
    p3 = os.path.join(r, "plan3")
    git(r, "reset", "-q", "--soft", "HEAD~1")
    git(r, "push", "-q", "-f", "origin", "plan3")
    git(r, "reset", "-q")
    for rel in ("listo/holdout.candado", v3.SALIDA_FINAL):
        os.remove(os.path.join(p3, rel))
    se_niega("reset y push forzado desde el propio repositorio, el candado borrado del disco", prueba_final(p3),
             "está en disco o en la historia")
    # el limite: ademas borra el reflog (reflog expire y gc); nada en este repositorio recuerda la rama de antes
    git(r, "update-ref", "-d", v3.VISTO)
    git(r, "reflog", "expire", "--expire=now", "--expire-unreachable=now", "--all")
    git(r, "gc", "-q", "--prune=now")
    rc, salida = prueba_final(p3)
    nota(f"LÍMITE: lo mismo, después de borrar el reflog y refs/veredicto3/visto (o desde un clon nuevo, que nunca "
         f"vio la rama de antes): rc {rc} ({motivo(salida)[:160]}). Lo cierra la protección de la rama plan3 en "
         f"GitHub (sin push forzado ni borrado) y el hash del commit del candado enviado al asesor")


def main():
    inicio = __import__("time").time()
    try:
        trabajos, man = preparar()
        trabajos, man, m1, m3 = noches(trabajos, man)
        c, m4 = cierre()
        git(REPO, "gc", "-q")
        ataques_cierre(c, m1, m4)
        trabajos_f, man_f = enmienda_final(trabajos, man)
        c_resello = next(h for h, n in nombres.items() if n == "resello")
        noche_final(trabajos_f, man_f)
        ataques_final(c_resello)
        prueba_final_y_candado()
    except Exception as ex:                       # la prueba misma fallo: se dice donde
        ok(False, f"la prueba se cortó: {type(ex).__name__}: {str(ex)[:400]}")
    pasan = sum(1 for x in lineas if x.startswith("PASA"))
    fallan = sum(1 for x in lineas if x.startswith("FALLA"))
    lineas.append(f"=== {pasan} pasan, {fallan} fallan")
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas) + "\n")
    print(lineas[-1], f"({__import__('time').time() - inicio:.0f} s)")
    sys.exit(1 if fallan else 0)


if __name__ == "__main__":
    main()
