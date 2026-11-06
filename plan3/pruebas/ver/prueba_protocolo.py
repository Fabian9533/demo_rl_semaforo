"""
prueba_protocolo.py - El cierre y la prueba final de punta a punta, con los programas de verdad, en un repositorio de
prueba con su 'origin' (un repositorio desnudo al lado) (segunda y tercera revision del 05.11). Sin SUMO: lo que corre
de noche se fabrica con las piezas del mundo sintetico de veredicto3 (politicas_mundo, csv_mundo, puente_mundo y
promocion_mundo), escrito como lo escriben los programas de verdad (CSV con CRLF como evaluar3, metas con CRLF como
rl_ippo, las listas con LF como el generador, la promocion con los comandos de la cola y rutas relativas), sin las
anomalias del mundo. Las semillas de los CSV son las de la tabla del prerregistro (§3; en la prueba final,
11001-11030 y 12001-12100): son rotulos de filas sinteticas, no simulaciones.

Corren en su proceso, con el codigo del repositorio de prueba (copiado de este worktree tal como esta en disco):
generar_trabajos3.py, p3_noche.manifiesto_ciego (la manana), manifiesto.py cierre, veredicto3.py --final,
--preflight, --holdout, --prueba-final y --verificar-prueba-final, protecciones.py antes, chequeos_previos.py
--sin-identidad y protecciones.revisar_comando.

Amenaza (PLAN3 §5): (a) que se pueda recuperar: cada error honesto se ve en el preflight antes del push o se corrige
despues; (b) que una manipulacion se vea desde afuera: cada ataque se niega. Pasos:
  0. Parte A (tag, rama main) y lanzamiento, empujados; .gitattributes sin las 7 lineas '-text' (llegan despues).
  1. Noches y mananas, un sello temprano barrido a una manana, una enmienda §14 (_r2, declarada antes de correrla),
     las 7 lineas de .gitattributes en un worktree con datos (sin cambios fantasma) y una rama dev que va y vuelve.
  2. Cierre (PLAN3 5.1), con un merge de codigo entre manifiesto.py cierre y el commit del cierre.
  3. Ataques y errores del cierre, cada uno en una copia del repositorio con su propio origin.
  4. Enmienda de la prueba final, resello, holdout.ok (--holdout y --preflight), un merge despues de holdout.ok y el
     ensayo del lanzamiento de la noche final (chequeos_previos y protecciones antes).
  5. Noche final (la cola la registra en cola/estado.json) y su manana.
  6. Ataques y errores de la prueba final.
  7. La prueba final una vez, el candado, la verificacion y los ataques al candado.
  8. Un clon nuevo en Windows (core.autocrlf=true) corre --final.
Escribe solo en tmp_ver/proto/ (ignorada por git) y en pruebas/ver/salidas/prueba_protocolo.txt; los commits salen con
su nombre (<cierre>, <manana 3>...) para que la salida no cambie de una corrida a otra. Unos 20 minutos.

Uso (cwd = plan3/): python -B pruebas/ver/prueba_protocolo.py
"""
import os
import re
import sys
import csv
import json
import time
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
ENTORNO = dict({k: v for k, v in os.environ.items() if not k.startswith("GIT_")}, PYTHONIOENCODING="utf-8",
               PYTHONDONTWRITEBYTECODE="1")
NOCHE1, NOCHE2 = ("promo", "puente", "t1r", "t2r"), ("h1t1", "h1t2", "t1a", "t2a")
REHECHA = "ev_t1r_corredor__fino"               # la evaluacion que rehace la enmienda §14 (error de codigo)
VIEJO, NUEVO = "ciego/t1r/eval_corredor__fino.csv", "ciego/t1r/eval_corredor__fino_r2.csv"
LISTA = "listo/lista_final.json"
# (celda, escenario, tanda final, tanda de examen de donde sale el brazo, a y b = (tipo, base, clave))
COMPARACIONES = [("P1", "corredor", "f1r", "t1r", ("v2reg", 42, "v2reg_s42"), ("ref_fino", "", "fino")),
                 ("P1", "poi_corredor", "f1a", "t1a", ("v2poi", 42, "v2poi_s42"), ("ref_fino", "", "fino"))]
SIN_SELLO = ":(exclude)plan3/cola/manifiesto_cierre.json"
SIN_LISTO = ":(exclude)plan3/listo"
MARCA_ATRIBUTOS = "# Archivos sellados que se escriben con LF"
lineas, nombres, conocidos = [], {}, set()


# ---------------- registro de la salida ----------------

def limpio(texto):
    """Sin rutas de esta maquina ni hashes (cambian de una corrida a otra): cada commit con su nombre."""
    for ruta in (TMP, TMP.replace(os.sep, "/"), TMP.replace(os.sep, "\\\\"), os.path.normcase(TMP)):
        texto = texto.replace(ruta, "<tmp>")
    for h in sorted(conocidos, key=len, reverse=True):
        nombre = f"<{nombres[h]}>" if h in nombres else "<commit>"
        for n in (40, 10, 7):
            texto = texto.replace(h[:n], nombre)
    texto = re.sub(r"\b[0-9a-f]{64}\b", "<sha256>", texto)
    texto = re.sub(r"\b(?=[0-9]*[a-f])[0-9a-f]{7,40}\b", "<commit>", texto)
    return re.sub(r"\b20\d\d-\d\d-\d\d \d\d:\d\d\b", "<fecha>", texto)


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
                       encoding="utf-8", errors="replace", env=ENTORNO)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args[:4])}: {r.stderr.strip()[:300]}")
    return r.stdout.strip()


def conocer(repo):
    """Los commits de repo, para que la salida los nombre (o diga <commit>) en lugar del hash."""
    if os.path.isdir(os.path.join(repo, ".git")):
        conocidos.update(git(repo, "rev-list", "--all", check=False).split())


def correr(p3, *args, entorno=None):
    """(rc, texto) de python -B <args> en la carpeta plan3 p3 (con su codigo y sus datos)."""
    r = subprocess.run([sys.executable, "-B", *args], cwd=p3, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=entorno or ENTORNO, timeout=3600)
    conocer(os.path.dirname(p3))
    return r.returncode, (r.stdout + "\n" + r.stderr).strip()


def motivo(texto):
    """La linea con la causa: la de sys.exit (veredicto3:, manifiesto:...) y la primera 'MAL', o la ultima."""
    filas = [x.strip() for x in texto.splitlines() if x.strip()]
    salida = next((x for x in reversed(filas) if x.startswith(("veredicto3:", "manifiesto:", "generar_trabajos3:"))),
                  filas[-1] if filas else "")
    mal = next((x for x in filas if x.startswith(("MAL ", "PROBLEMA:"))), None)
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
    """La manana: p3_noche.manifiesto_ciego() y un commit de plan3/ (nunca ciego/ ni listo/; el sello, solo si
    con_sello: el error que PLAN3 5.1 prohibe; sin lo de excluir) con push."""
    rc, salida = correr(os.path.join(repo, "plan3"), "-c", "import p3_noche; print(p3_noche.manifiesto_ciego())")
    if rc != 0:
        raise RuntimeError(f"p3_noche.manifiesto_ciego: {salida[-300:]}")
    return commit(repo, nombre, "plan3", SIN_LISTO, *([] if con_sello else [SIN_SELLO]),
                  *[f":(exclude){x}" for x in excluir])


def poner_url(r, url):
    """PLAN3.md §5 de la copia r dice que su origin es url (cada copia tiene su origin desnudo)."""
    ruta = os.path.join(r, "plan3", "doc", "PLAN3.md")
    with open(ruta, encoding="utf-8", newline="") as f:
        texto = f.read()
    texto = re.sub(r"(El `origin` de la rama `plan3` es `)[^`]+(`)", lambda m: m.group(1) + url + m.group(2), texto)
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        f.write(texto)


def clonar_desnudo(base, origen):
    """git clone --bare origen base/o.git, con reintentos: en Windows un antivirus puede tener un archivo nuevo un
    rato ('Permission denied' al escribir config)."""
    for intento in range(4):
        try:
            git(base, "clone", "-q", "--bare", origen, "o.git")
            return
        except RuntimeError:
            if intento == 3:
                raise
            shutil.rmtree(os.path.join(base, "o.git"), ignore_errors=True)
            time.sleep(2 * (intento + 1))


def copia(nombre):
    """Una copia del repositorio de prueba tal como esta (con lo ignorado: ciego/, el candado...) y con su propio
    origin (copia del desnudo, que su PLAN3.md nombra): cada ataque o error en la suya."""
    base = v3.carpeta_limpia(os.path.join(TMP, "c", nombre)) or os.path.join(TMP, "c", nombre)
    r = os.path.join(base, "r")
    shutil.copytree(REPO, r)
    clonar_desnudo(base, ORIGEN)
    git(r, "remote", "set-url", "origin", os.path.join(base, "o.git"))
    poner_url(r, os.path.join(base, "o.git"))
    git(r, "update-index", "--assume-unchanged", "plan3/doc/PLAN3.md")
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
    entorno = dict(ENTORNO, GIT_INDEX_FILE=indice)

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
    """Lo que querria cambiar quien resella despues de ver los datos: la promocion de corredor al reves, con
    promocion/corredor.json y promocion.json de acuerdo entre si (como los escribe p3_promocion)."""
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


def preflight(p3, que):
    return correr(p3, "veredicto3.py", "--preflight", que)


def escalar_csv(ruta, factor):
    """Un CSV de evaluar3 con el retraso por factor (CRLF, como evaluar3)."""
    with open(ruta, encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    for x in filas:
        x["retraso_total_prom"] = str(round(float(x["retraso_total_prom"]) * factor, 4))
    v3.escribir(ruta, v3.texto_csv(filas, list(filas[0])).replace("\n", "\r\n"))


def cola_lanza(repo, ids):
    """Lo que escribe cola.py al lanzar cada trabajo: su registro en cola/estado.json con el commit de HEAD, la hora y,
    al terminar bien, codigo 0."""
    ruta = os.path.join(repo, "plan3", "cola", "estado.json")
    e = leer(ruta) if os.path.exists(ruta) else {}
    head = git(repo, "rev-parse", "HEAD")
    ahora = time.time() + 1
    for tid in ids:
        e.setdefault("registro", {})[tid] = {"inicio_epoch": ahora, "primer_inicio_epoch": ahora, "commit": head,
                                             "codigo": 0, "intento": 0}
    e["hechos"] = sorted(set(e.get("hechos", [])) | set(ids))
    with open(ruta, "w", encoding="utf-8") as f:                    # como cola.guardar_estado
        json.dump(e, f, indent=1, ensure_ascii=False)


def revisar_comando(p3, trabajo):
    """protecciones.revisar_comando de un trabajo en la carpeta p3 (como al lanzarlo), solo sus problemas."""
    codigo = ("import json, protecciones; print(json.dumps(protecciones.revisar_comando(json.loads("
              f"{json.dumps(trabajo)!r})), ensure_ascii=False))")
    rc, salida = correr(p3, "-c", codigo)
    try:
        return json.loads(salida.splitlines()[-1])
    except (ValueError, IndexError):
        return [f"no se pudo revisar: {salida[-200:]}"]


def dev_commit(repo, nombre):
    """Un commit de codigo en la rama dev (una nota): lo que llega de plan3-dev."""
    git(repo, "checkout", "-q", "dev")
    ruta = os.path.join(repo, "plan3", "doc", "nota_dev.md")
    with open(ruta, "a", encoding="utf-8", newline="\n") as f:
        f.write(f"- {nombre}\n")
    h = commit(repo, nombre, "plan3/doc/nota_dev.md", empujar=False)
    git(repo, "checkout", "-q", "plan3")
    return h


def merge(repo, rama, nombre, empujar=True):
    git(repo, "merge", "-q", "--no-ff", "--no-edit", "-m", nombre, rama)
    h = git(repo, "rev-parse", "HEAD")
    nombres[h] = nombre
    conocidos.add(h)
    if empujar:
        git(repo, "push", "-q", "origin", "plan3")
    return h


# ---------------- 0 y 1: parte A, lanzamiento, noches y mananas ----------------

def archivos_a_copiar():
    """Lo versionado de la raiz (sin PDF) y de plan3/, y lo nuevo de plan3/ que todavia no esta en git."""
    r = subprocess.run(["git", "ls-files", "-z"], cwd=RAIZ, capture_output=True)
    rels = [x for x in r.stdout.decode("utf-8").split("\0") if x]
    salida = [x for x in rels if x.startswith("plan3/") or ("/" not in x and not x.lower().endswith(".pdf"))]
    r = subprocess.run(["git", "ls-files", "-z", "--others", "--exclude-standard", "--", "plan3"], cwd=RAIZ,
                       capture_output=True)
    return salida + [x for x in r.stdout.decode("utf-8").split("\0") if x and x.endswith((".py", ".md"))]


def preparar():
    titulo("0. Parte A y lanzamiento (repositorio de prueba con su origin)")
    v3.carpeta_limpia(TMP)
    for rel in archivos_a_copiar():
        if os.path.exists(os.path.join(RAIZ, rel)):
            os.makedirs(os.path.dirname(os.path.join(REPO, rel)), exist_ok=True)
            shutil.copyfile(os.path.join(RAIZ, rel), os.path.join(REPO, rel))
    with open(os.path.join(REPO, ".gitattributes"), encoding="utf-8") as f:
        atributos = f.read()
    with open(os.path.join(REPO, ".gitattributes"), "w", encoding="utf-8", newline="\n") as f:
        f.write(atributos.split(MARCA_ATRIBUTOS)[0])           # las 7 lineas '-text' llegan despues (paso 1)
    git(TMP, "init", "-q", "--bare", ORIGEN)
    git(REPO, "init", "-q")
    git(REPO, "checkout", "-q", "-b", "plan3")
    for clave, valor in (("user.name", "Prueba del protocolo"), ("user.email", "prueba@ejemplo.invalid"),
                         ("commit.gpgsign", "false"), ("tag.gpgsign", "false")):
        git(REPO, "config", clave, valor)
    git(REPO, "remote", "add", "origin", ORIGEN)
    poner_url(REPO, ORIGEN)
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
    git(REPO, "branch", "main")
    git(REPO, "push", "-q", "origin", "plan3", "main", "plan3-prerregistro-A")
    commit(REPO, "lanzamiento", "plan3/cola")
    nota(f"{len(trabajos)} trabajos, {len(man)} CSV esperados; semillas de la tabla del prerregistro (rótulos)")
    return trabajos, man


def noches(trabajos, man):
    titulo("1. Noches y mañanas (cada mañana: p3_noche.manifiesto_ciego, commit sin ciego/ ni listo/, push)")
    v3.csv_mundo(P3, man, trabajos, lambda e: e["tanda"] in NOCHE1, anomalias=False)
    v3.promocion_mundo(P3, trabajos, v3.rango(gt.TANDAS["promo"][1]))
    manana(REPO, "manana 1")
    # las 7 lineas '-text' de .gitattributes llegan con datos ya commiteados (P2-M2): ningun cambio fantasma
    with open(os.path.join(RAIZ, ".gitattributes"), encoding="utf-8") as f:
        bloque = MARCA_ATRIBUTOS + f.read().split(MARCA_ATRIBUTOS)[1]
    with open(os.path.join(REPO, ".gitattributes"), "a", encoding="utf-8", newline="\n") as f:
        f.write(bloque)
    commit(REPO, "gitattributes", ".gitattributes")
    sucio = git(REPO, "status", "--porcelain")
    ok(sucio == "", f"las 7 líneas '-text' de .gitattributes en un worktree con datos commiteados: git status queda "
                    f"limpio ({sucio[:120] or 'sin cambios'})")
    git(REPO, "branch", "dev")
    dev_commit(REPO, "dev 1")
    v3.csv_mundo(P3, man, trabajos, lambda e: e["tanda"] in NOCHE2, anomalias=False)
    manana(REPO, "manana 2")
    git(REPO, "checkout", "-q", "dev")
    merge(REPO, "plan3", "plan3 en dev", empujar=False)            # plan3 -> dev despues de una manana (P2-H3)
    git(REPO, "checkout", "-q", "plan3")
    dev_commit(REPO, "dev 2")
    corre("un sello temprano (manifiesto.py cierre antes de tiempo; después se barre a la mañana 3)",
          correr(P3, "manifiesto.py", "cierre"), "manifiesto_cierre.json: ")
    copia("antes_r2")                                    # para P1-H4: una _r2 hecha a mano, declarada tarde
    # enmienda §14 (error de codigo en una evaluacion): id y CSV nuevos, y el reemplazo declarado ANTES de correrla
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
    escribir_json(os.path.join(P3, "cola", "reemplazos.json"), [
        {"viejo": VIEJO, "nuevo": NUEVO, "motivo": "error de código en la evaluación (§14, enmienda del 2026-11-20)",
         "fecha": "2026-11-20"}])
    commit(REPO, "enmienda r2", "plan3/generar_trabajos3.py", "plan3/cola/trabajos.jsonl",
           "plan3/cola/manifiesto_esperado.json", "plan3/cola/partes.txt", "plan3/cola/reemplazos.json")
    v3.csv_mundo(P3, man, trabajos, lambda e: e["csv"] == NUEVO, anomalias=False)
    manana(REPO, "manana 3", con_sello=True)
    ok(git(REPO, "show", "--name-only", "--format=", "HEAD").count("plan3/cola/manifiesto_cierre.json") == 1,
       "la mañana 3 se lleva por error el sello temprano (lo que PLAN3 5.1 prohíbe; V1-M4)")
    merge(REPO, "dev", "dev en plan3 (ida y vuelta)")              # dev -> plan3 despues de otra manana (P2-H3)
    return trabajos, man


# ---------------- 2: cierre ----------------

def cierre():
    titulo("2. Cierre (PLAN3 5.1)")
    dev_commit(REPO, "dev 3")                            # un arreglo en dev que se fusiona despues del sello
    corre("manifiesto.py cierre (la salida vieja tiene su reemplazo declarado antes de la corrida rehecha)",
          correr(P3, "manifiesto.py", "cierre"), "manifiesto_cierre.json: ")
    merge(REPO, "dev", "dev en plan3 entre el sello y el cierre", empujar=False)       # P2-H1
    v3.escribir(os.path.join(P3, "listo", "cierre.ok"), "cierre: Fabian, 2026-11-28 09:00\n")
    copia("pre_cierre")                                  # el sello y cierre.ok en disco, sin commitear
    c = commit(REPO, "cierre", "plan3/cola", "plan3/listo", forzar=["plan3/ciego"], empujar=False)
    se_niega("--final con el commit del cierre sin push (lee todo desde origin/plan3)", final(P3),
             "listo/cierre.ok no está commiteado en origin/plan3")
    res = preflight(P3, "cierre")
    corre("--preflight cierre antes del push (con un merge de código entre manifiesto.py cierre y el commit del "
          "cierre, P2-H1)", res, "preflight cierre: todo bien")
    nota("el preflight imprime el correo: " + " | ".join(x.strip() for x in res[1].splitlines()
                                                        if x.strip().startswith(("commit del cierre", "sha256"))))
    git(REPO, "push", "-q", "origin", "plan3")
    res = final(P3)
    if corre("--final con el commit del cierre (sello, cierre.ok, cola/ y ciego/) empujado", res, "escrito"):
        for x in res[1].splitlines():
            if x.startswith("numero unico regulares T1"):
                nota(x)
    ok("Para el asesor" in res[1] and "commit del cierre" in res[1],
       "--final imprime el correo al asesor (commit del cierre, origin/plan3, sha256 del sello)")
    trabajos, man = listas(P3)
    t1 = next(t for t in trabajos if t["id"] == "ev_t1r_corredor__v2reg_s42")
    malos = revisar_comando(P3, t1)
    ok(any("despues de listo/cierre.ok" in m for m in malos) and any("ya esta en un manifiesto" in m for m in malos),
       f"después de cierre.ok, protecciones no lanza un trabajo ciego, y nunca relanza uno cuyo CSV ya está en una "
       f"mañana (también desde cola/reintentar.txt) {malos}")
    return c


# ---------------- 3: ataques y errores del cierre ----------------

def errores_del_cierre(c):
    titulo("3a. Errores honestos del cierre: el preflight los ve antes del push, o se corrigen después")
    # el sello fuera del commit del cierre (PLAN3 5.1 de antes, al pie de la letra): el preflight lo ve; y si se empuja
    # igual, el commit siguiente con el sello es el cierre
    r = copia_de("pre_cierre", "sin_sello")
    p3 = os.path.join(r, "plan3")
    commit(r, "cierre sin el sello", "plan3/listo/cierre.ok", forzar=["plan3/ciego"], empujar=False)
    se_niega("el commit del cierre sin el sello: el preflight lo ve antes del push", preflight(p3, "cierre"),
             "es un sello viejo")
    git(r, "push", "-q", "origin", "plan3")
    se_niega("empujado igual: --final se niega", final(p3), "no hay un commit de cierre que valga")
    commit(r, "el sello que faltaba", "plan3/cola")
    corre("se corrige con el commit del sello (el cierre es ese commit): --final corre", final(p3), "escrito")
    # cierre.ok barrido a un commit de la manana (git add -A plan3) y empujado: el commit del cierre lo corrige
    r = copia_de("pre_cierre", "cierre_en_manana")
    p3 = os.path.join(r, "plan3")
    git(r, "add", "-A", "--", "plan3/listo", "plan3/cola/manifiesto_ciego.json")
    git(r, "commit", "-q", "-m", "manana con cierre.ok por error")
    git(r, "push", "-q", "origin", "plan3")
    commit(r, "cierre", "plan3/cola", "plan3/listo", forzar=["plan3/ciego"])
    corre("cierre.ok barrido a un commit de la mañana y empujado: el commit siguiente con el sello es el cierre",
          final(p3), "escrito")
    # un archivo de mas en ciego/ y una manana de nuevo dentro del commit del cierre: el preflight lo ve
    r = copia_de("pre_cierre", "manana_sucia")
    p3 = os.path.join(r, "plan3")
    shutil.copyfile(os.path.join(p3, "ciego", "t1r", "eval_corredor__v2reg_s42.csv"),
                    os.path.join(p3, "ciego", "t1r", "eval_corredor__prueba_a_mano.csv"))
    correr(p3, "-c", "import p3_noche; p3_noche.manifiesto_ciego()")
    commit(r, "cierre con una manana sucia", "plan3/cola", "plan3/listo", forzar=["plan3/ciego"], empujar=False)
    se_niega("un CSV de más en ciego/ y el manifiesto de la mañana reescrito dentro del commit del cierre: el "
             "preflight lo ve antes del push", preflight(p3, "cierre"), "es un sello viejo")


def copia_de(origen, nombre):
    """Una copia de otra copia (con su propio origin desnudo)."""
    base = v3.carpeta_limpia(os.path.join(TMP, "c", nombre)) or os.path.join(TMP, "c", nombre)
    r = os.path.join(base, "r")
    shutil.copytree(os.path.join(TMP, "c", origen, "r"), r)
    clonar_desnudo(base, os.path.join(TMP, "c", origen, "o.git"))
    git(r, "remote", "set-url", "origin", os.path.join(base, "o.git"))
    poner_url(r, os.path.join(base, "o.git"))
    return r


def ataques_cierre(c, m1, m4):
    titulo("3b. Ataques al cierre (cada uno en su copia, con su origin)")
    # merge que esconde el sello (V1-H1, k1) y su variante P1-H1: HEAD en la rama lateral, el merge empujado
    r = copia("merge")
    nuevos = resellar(r)
    git(r, "checkout", "-q", "--", *nuevos)
    nuevos["plan3/listo/cierre.ok"] = binario(os.path.join(r, "plan3", "listo", "cierre.ok"))
    lado = commit_arbol(r, m4, nuevos, "cierre (lado)", base=c)
    git(r, "branch", "lado", lado)
    git(r, "merge", "-q", "--no-edit", "-s", "ours", "lado")
    nombres[git(r, "rev-parse", "HEAD")] = "merge del lado"
    git(r, "push", "-q", "origin", "plan3")
    se_niega("un cierre en una rama lateral, mezclado con -s ours y empujado; HEAD = plan3",
             final(os.path.join(r, "plan3")), "no forman una sola cadena")
    git(r, "checkout", "-q", "lado")
    se_niega("lo mismo con HEAD = la rama lateral (P1-H1: se lee desde origin/plan3, no desde HEAD)",
             final(os.path.join(r, "plan3")), "no forman una sola cadena")
    # un tag 'plan3' en el origin (P1-H1)
    r = copia("tag")
    git(r, "tag", "plan3", m4)
    git(r, "push", "-q", "origin", "refs/tags/plan3")
    se_niega("un tag 'plan3' empujado al origin (git lo podría tomar por la rama)", final(os.path.join(r, "plan3")),
             "que git puede confundir con la rama")
    # otro origin (P1-H1): la historia de otra copia
    r = copia("otro_origin")
    otro = os.path.join(TMP, "c", "otro_origin", "falso.git")
    git(os.path.dirname(otro), "clone", "-q", "--bare", ORIGEN, "falso.git")
    git(r, "remote", "set-url", "origin", otro)
    se_niega("el origin cambiado por otro repositorio (P1-H1)", final(os.path.join(r, "plan3")), "no es el del plan")
    # amend del cierre: sin push y con push forzado (V1-H1)
    r = copia("amend")
    git(r, "add", "--", *resellar(r))
    git(r, "commit", "-q", "--amend", "--no-edit")
    nombres[git(r, "rev-parse", "HEAD")] = "cierre rehecho"
    se_niega("amend del commit del cierre, sin push (se lee desde origin/plan3)", final(os.path.join(r, "plan3")),
             "no es el del cierre")
    git(r, "push", "-q", "-f", "origin", "plan3")
    se_niega("amend del commit del cierre con push forzado", final(os.path.join(r, "plan3")),
             "se reescribió (push forzado)")
    git(r, "update-ref", "-d", v3.VISTO)
    se_niega("lo mismo sin refs/veredicto3/visto (P1-M2: el reflog de origin/plan3 lo delata)",
             final(os.path.join(r, "plan3")), "se reescribió (push forzado)")
    # otra rama: su propio cierre, empujado como otra rama
    r = copia("otra")
    nuevos = resellar(r)
    git(r, "checkout", "-q", "--", *nuevos)
    otra = commit_arbol(r, m4, nuevos, "cierre (otra rama)", base=c)
    git(r, "branch", "otra", otra)
    git(r, "checkout", "-q", "otra")
    git(r, "push", "-q", "origin", "otra")
    se_niega("otra rama con su propio cierre (empujada como otra rama)", final(os.path.join(r, "plan3")),
             "no es el del cierre")
    # clon superficial
    base = v3.carpeta_limpia(os.path.join(TMP, "c", "superficial")) or os.path.join(TMP, "c", "superficial")
    git(base, "clone", "-q", "--depth", "1", "-b", "plan3", "file:///" + ORIGEN.replace(os.sep, "/"), "r")
    se_niega("clon superficial (shallow) de la rama empujada", final(os.path.join(base, "r", "plan3")), "superficial")
    # manana en una rama lateral (V1-H1, k4)
    r = copia("manana_lado")
    p3 = os.path.join(r, "plan3")
    rel = "ciego/t1a/eval_poi_corredor__v2poi_s42.csv"
    escalar_csv(os.path.join(p3, rel), 0.85)
    correr(p3, "-c", "import p3_noche; print(p3_noche.manifiesto_ciego())")
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
    # alias de ruta en el manifiesto (P1-H2): un CSV cambiado despues de su manana, sellado bajo './ciego/...'
    r = copia("alias")
    p3 = os.path.join(r, "plan3")
    rel = "ciego/t1r/eval_corredor__v2reg_s42.csv"
    escalar_csv(os.path.join(p3, rel), 0.85)
    man = leer(os.path.join(p3, "cola", "manifiesto_esperado.json"))
    for e in man:
        if e["csv"] == rel:
            e["csv"] = "./" + rel
    v3.escribir(os.path.join(p3, "cola", "manifiesto_esperado.json"), json.dumps(man, indent=0) + "\n")
    sello = leer(os.path.join(p3, "cola", "manifiesto_cierre.json"))
    sello["csv"]["./" + rel] = hashlib.sha256(binario(os.path.join(p3, rel))).hexdigest()
    sello["csv"].pop(rel, None)
    sello["otros"]["cola/manifiesto_esperado.json"] = hashlib.sha256(
        binario(os.path.join(p3, "cola", "manifiesto_esperado.json"))).hexdigest()
    v3.escribir(os.path.join(p3, "cola", "manifiesto_cierre.json"), json.dumps(sello, indent=0, sort_keys=True))
    commit(r, "sello con alias", "plan3/cola")
    se_niega("un CSV cambiado después de su mañana, en el manifiesto como './ciego/...' y sellado a mano (P1-H2)",
             final(p3), "no es la ruta canonica")
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
    # objetos de reemplazo (git replace)
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
    # codigo del analisis sin commitear (P1-M3)
    r = copia("codigo")
    p3 = os.path.join(r, "plan3")
    with open(os.path.join(p3, "veredicto3.py"), "a", encoding="utf-8", newline="\n") as f:
        f.write("\nMARGEN_NI = 5.0\n")
    se_niega("veredicto3.py editado sin commitear (P1-M3)", final(p3), "cambios sin commitear")
    # sin red (el origin no responde)
    r = copia("sin_red")
    os.rename(os.path.join(TMP, "c", "sin_red", "o.git"), os.path.join(TMP, "c", "sin_red", "o_fuera.git"))
    se_niega("sin red (el origin no responde): un mensaje claro, sin quedarse colgado", final(os.path.join(r, "plan3")),
             "sin red, sin acceso o sin respuesta")


def ataques_antes_del_cierre():
    titulo("3c. Ataques antes del cierre (P1-H3, P1-H4, P1-H6)")
    # P1-H3: un CSV decisivo cambiado y sus mananas reescritas con push forzado desde el repositorio de ejecucion,
    # antes del primer --final; despues, un cierre normal
    r = copia_de("pre_cierre", "reescrito")
    p3 = os.path.join(r, "plan3")
    m1 = next(h for h, n in nombres.items() if n == "manana 1")
    git(r, "reset", "-q", "--soft", m1)
    escalar_csv(os.path.join(p3, "ciego", "t1a", "eval_poi_corredor__v2poi_s42.csv"), 0.85)
    correr(p3, "-c", "import p3_noche; p3_noche.manifiesto_ciego()")
    commit(r, "manana 2 (reescrita)", "plan3", SIN_SELLO, SIN_LISTO, empujar=False)
    git(r, "push", "-q", "-f", "origin", "plan3")
    correr(p3, "manifiesto.py", "cierre")
    commit(r, "cierre (reescrito)", "plan3/cola", "plan3/listo", forzar=["plan3/ciego"])
    se_niega("un CSV cambiado, sus mañanas reescritas y push forzado antes del primer --final (P1-H3: el reflog de "
             "origin/plan3)", final(p3), "se reescribió (push forzado)")
    # P1-H6: la promocion dada vuelta antes del cierre (los dos archivos de acuerdo) y sellada
    r = copia_de("pre_cierre", "promocion")
    p3 = os.path.join(r, "plan3")
    cambiar_promocion(p3)
    commit(r, "promocion cambiada", "plan3/promocion.json", "plan3/promocion")
    correr(p3, "manifiesto.py", "cierre")
    commit(r, "cierre", "plan3/cola", "plan3/listo", forzar=["plan3/ciego"])
    se_niega("la promoción dada vuelta antes del cierre, commiteada y sellada (P1-H6: se vuelve a calcular)",
             final(p3), "no es la que da p3_promocion")
    # P1-H4: una _r2 hecha a mano junto a la original, y el reemplazo declarado despues (en las dos direcciones)
    r = os.path.join(TMP, "c", "antes_r2", "r")
    p3 = os.path.join(r, "plan3")
    original = "ciego/t1r/eval_corredor__v2reg_s42.csv"
    otra = "ciego/t1r/eval_corredor__v2reg_s42_r2.csv"
    shutil.copyfile(os.path.join(p3, original), os.path.join(p3, otra))
    escalar_csv(os.path.join(p3, otra), 0.9)
    manana(r, "manana con la _r2 a mano")
    ruta_g = os.path.join(p3, "generar_trabajos3.py")
    with open(ruta_g, encoding="utf-8") as f:
        texto = f.read()
    texto = texto.replace('    uso, semillas = TANDAS[tanda]\n', '    uso, semillas = TANDAS[tanda]\n'
                          '    if f"ev_{tanda}_{esc}__{clave}" == "ev_t1r_corredor__v2reg_s42":\n'
                          '        clave = f"{clave}_r2"\n', 1)
    with open(ruta_g, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)
    correr(p3, "generar_trabajos3.py")
    for viejo, nuevo, nombre in ((original, otra, "la nueva"), (otra, original, "la vieja")):
        escribir_json(os.path.join(p3, "cola", "reemplazos.json"), [
            {"viejo": viejo, "nuevo": nuevo, "motivo": "a mano", "fecha": "2026-11-21"}])
        h = commit(r, f"enmienda tarde ({nombre})", "plan3/generar_trabajos3.py", "plan3/cola/trabajos.jsonl",
                   "plan3/cola/manifiesto_esperado.json", "plan3/cola/reemplazos.json")
        se_niega(f"una _r2 hecha a mano y el reemplazo declarado después de su mañana; se queda {nombre} (P1-H4)",
                 correr(p3, "manifiesto.py", "cierre"), "reemplazos")
        git(r, "reset", "-q", "--hard", f"{h}~1")
        git(r, "push", "-q", "-f", "origin", "plan3")


# ---------------- 4 a 7: la prueba final ----------------

def enmienda_final(trabajos, man):
    titulo("4. Enmienda de la prueba final (PLAN3 5.3): código, lista, resello, holdout.ok y el ensayo de la noche")
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
    copia("antes_resello")                               # para holdout.ok commiteado antes del resello
    corre("resello (manifiesto.py cierre): los CSV de la prueba final todavía no existen y no se sellan",
          correr(P3, "manifiesto.py", "cierre"), "resello de la prueba final")
    commit(REPO, "resello", "plan3/cola/manifiesto_cierre.json")
    corre("--final con el resello (solo le agrega la prueba final al sello del cierre)", final(P3), "escrito")
    # holdout.ok: la lista con un error de tipeo no pasa --holdout; holdout.ok sin commitear, sin push y empujado
    r = copia("lista_mal")
    p3 = os.path.join(r, "plan3")
    lista = leer(os.path.join(p3, LISTA))
    lista["comparaciones"][0]["a"]["base"] = "42"
    escribir_json(os.path.join(p3, LISTA), lista)
    se_niega("una lista con la base escrita como texto ('42'): --holdout la rechaza antes de fijarla (P2-M1)",
             correr(p3, "veredicto3.py", "--holdout", LISTA), "la base va como número")
    t_final = trabajos_f[-1]
    estados = [revisar_comando(P3, t_final)]
    res = correr(P3, "veredicto3.py", "--holdout", LISTA)
    corre("python veredicto3.py --holdout listo/lista_final.json valida la lista y escribe holdout.ok (UTF-8, una "
          "línea)", res, "escrito listo/holdout.ok")
    copia("holdout_sin_commit")                          # para P1-H5, UTF-16, dos lineas
    estados.append(revisar_comando(P3, t_final))
    commit(REPO, "holdout.ok", "plan3/listo/holdout.ok", empujar=False)
    estados.append(revisar_comando(P3, t_final))
    res = preflight(P3, "holdout")
    corre("--preflight holdout antes del push", res, "preflight holdout: todo bien")
    git(REPO, "push", "-q", "origin", "plan3")
    estados.append(revisar_comando(P3, t_final))
    h = [[m for m in x if "holdout" in m] for x in estados]
    ok(any("exige listo/holdout.ok" in m for m in h[0]) and any("commiteado" in m for m in h[1])
       and any("no esta empujado" in m for m in h[2]) and h[3] == [],
       f"protecciones.revisar_comando de un trabajo 'final': sin holdout.ok, sin commitear, sin push y empujado {h}")
    # un merge de codigo despues de holdout.ok (P2-H2)
    dev_commit(REPO, "dev 4")
    merge(REPO, "dev", "dev en plan3 después de holdout.ok")
    # ensayo del lanzamiento de la noche final: protecciones.py antes y chequeos_previos.py (sin SUMO)
    rc, salida = correr(P3, "protecciones.py", "antes")
    problemas = [x for x in salida.splitlines() if x.startswith("PROBLEMA:")]
    ok(rc == 0, f"ensayo de la noche final: protecciones.py antes en el HEAD de holdout.ok: {len(problemas)} problemas "
                f"{[p[:100] for p in problemas[:2]]}")
    rc, salida = correr(P3, "chequeos_previos.py", "--sin-identidad")
    validados = next((x for x in salida.splitlines() if x.startswith("comandos validados")), "")
    ok(rc == 0 and "evaluar3.py" in validados and "rechazados: 0" in validados,
       f"ensayo de la noche final: chequeos_previos.py --sin-identidad (cada comando, los 'final' incluidos, pasa el "
       f"parser de su script): {validados or motivo(salida)[:200]}")
    return trabajos_f, man_f


def errores_holdout(trabajos_f, man_f):
    titulo("4b. Errores honestos de holdout.ok: el preflight los ve antes del push")
    r = copia_de("holdout_sin_commit", "utf16")
    p3 = os.path.join(r, "plan3")
    sha = open(os.path.join(p3, "listo", "holdout.ok"), encoding="utf-8").read().strip()
    with open(os.path.join(p3, "listo", "holdout.ok"), "wb") as f:              # lo que deja '>' en PowerShell 5.1
        f.write((sha + "\r\n").encode("utf-16"))
    commit(r, "holdout.ok en UTF-16", "plan3/listo/holdout.ok", empujar=False)
    se_niega("holdout.ok en UTF-16 (PowerShell 5.1): el preflight lo ve antes del push", preflight(p3, "holdout"),
             "UTF-16")
    corre("se reescribe con --holdout y se commitea: el preflight pasa (el contenido es el mismo)",
          correr(p3, "veredicto3.py", "--holdout", LISTA), "escrito listo/holdout.ok")
    commit(r, "holdout.ok en UTF-8", "plan3/listo/holdout.ok", empujar=False)
    corre("el preflight después de corregirlo", preflight(p3, "holdout"), "preflight holdout: todo bien")
    r = copia_de("holdout_sin_commit", "dos_lineas")
    p3 = os.path.join(r, "plan3")
    with open(os.path.join(p3, "listo", "holdout.ok"), "a", encoding="utf-8", newline="\n") as f:
        f.write("0" * 64 + "\n")
    commit(r, "holdout.ok con dos líneas", "plan3/listo/holdout.ok", empujar=False)
    se_niega("holdout.ok con dos líneas: el preflight lo ve antes del push", preflight(p3, "holdout"), "una sola línea")
    r = os.path.join(TMP, "c", "antes_resello", "r")
    p3 = os.path.join(r, "plan3")
    correr(p3, "veredicto3.py", "--holdout", LISTA)
    commit(r, "holdout.ok antes del resello", "plan3/listo/holdout.ok", empujar=False)
    se_niega("holdout.ok commiteado antes del resello: el preflight lo ve antes del push", preflight(p3, "holdout"),
             "cambió después del cierre")


def noche_final(trabajos_f, man_f):
    titulo("5. Noche final (la cola la registra en cola/estado.json) y su mañana")
    finales = [t["id"] for t in trabajos_f if t.get("uso") == "final"]
    v3.csv_mundo(P3, man_f, trabajos_f, lambda e: e["tanda"] in ("f1r", "f1a"), anomalias=False)
    cola_lanza(REPO, finales)
    manana(REPO, "manana 5")
    filas = {}
    for e in man_f:
        if e["tanda"] in ("f1r", "f1a"):
            with open(os.path.join(P3, e["csv"]), encoding="utf-8", newline="") as f:
                semillas = [int(x["semilla"]) for x in csv.DictReader(f)]
            filas[e["csv"]] = (semillas[0], semillas[-1], len(semillas))
    ok(sorted(set(filas.values())) == [(11001, 11030, 30), (12001, 12100, 100)],
       f"los CSV de la noche final tienen los bloques de §13 {sorted(set(filas.values()))}")


def ataques_final(c_resello, trabajos_f, man_f):
    titulo("6. Ataques a la prueba final (cada uno en su copia)")
    # P1-H5: los CSV finales hechos a mano antes de holdout.ok (no los lanzo la cola) y la lista elegida despues
    r = copia_de("holdout_sin_commit", "a_mano")
    p3 = os.path.join(r, "plan3")
    v3.csv_mundo(p3, man_f, trabajos_f, lambda e: e["tanda"] in ("f1r", "f1a"), anomalias=False)
    commit(r, "holdout.ok", "plan3/listo/holdout.ok")
    cola_lanza(r, [])                                    # la cola corrio otras cosas, no estos trabajos
    manana(r, "manana final (CSV a mano)")
    se_niega("los CSV de la prueba final hechos a mano antes de holdout.ok, sin la cola (P1-H5)", prueba_final(p3),
             "no lo lanzó la cola")
    # holdout.ok commiteado despues de la noche final
    r = copia_de("holdout_sin_commit", "holdout_tarde")
    p3 = os.path.join(r, "plan3")
    v3.csv_mundo(p3, man_f, trabajos_f, lambda e: e["tanda"] in ("f1r", "f1a"), anomalias=False)
    manana(r, "manana de la noche final (antes de holdout.ok)")
    commit(r, "holdout.ok tarde", "plan3/listo/holdout.ok")
    se_niega("holdout.ok commiteado después de la noche final (su mañana lista los CSV)", prueba_final(p3),
             "que no es posterior a")
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
    # P1-M1: la tabla de semillas del prerregistro editada (commit y push)
    r = copia("prerregistro")
    p3 = os.path.join(r, "plan3")
    with open(os.path.join(p3, "PRERREGISTRO.md"), encoding="utf-8", newline="") as f:
        texto = f.read()
    with open(os.path.join(p3, "PRERREGISTRO.md"), "w", encoding="utf-8", newline="") as f:
        f.write(texto.replace("[11001, 11030]", "[8001, 8030]", 1))
    commit(r, "prerregistro editado", "plan3/PRERREGISTRO.md")
    se_niega("la tabla de semillas de PRERREGISTRO.md editada, commiteada y empujada (P1-M1: vale la del tag)",
             prueba_final(p3), "no es la del tag")


def prueba_final_y_candado():
    titulo("7. La prueba final (una vez), el candado y su verificación")
    # P1-M5: un corte despues de la salida y antes del candado deja volver a correrla
    r = copia("corte")
    p3 = os.path.join(r, "plan3")
    codigo = ("import os, builtins, veredicto3 as v\nreal = builtins.open\n"
              "def falso(p, *a, **k):\n"
              "    if str(p).endswith('holdout.candado') and a and a[0] == 'x':\n"
              "        raise OSError('corte simulado')\n"
              "    return real(p, *a, **k)\n"
              "builtins.open = falso\n"
              "try:\n    v.correr_prueba_final(os.path.abspath('listo/lista_final.json'))\n"
              "except OSError as ex:\n    print('cortado:', ex)\n")
    rc, salida = correr(p3, "-c", codigo)
    ok("cortado: corte simulado" in salida and os.path.exists(os.path.join(p3, v3.SALIDA_FINAL))
       and not os.path.exists(os.path.join(p3, v3.CANDADO)),
       "un corte después de escribir la salida y antes del candado (P1-M5): queda la salida, sin candado")
    corre("después del corte, se vuelve a correr y da lo mismo", prueba_final(p3), "prueba final: 2 comparaciones")
    res = prueba_final(P3)
    corre("--prueba-final con la lista de la enmienda (exigir_semillas: los bloques de §13)", res,
          "prueba final: 2 comparaciones")
    with open(os.path.join(P3, v3.SALIDA_FINAL), encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    candado = leer(os.path.join(P3, v3.CANDADO))
    ok([(x["escenario"], x["tanda"], x["n"]) for x in filas] == [("corredor", "f1r", "30"),
                                                                  ("poi_corredor", "f1a", "100")]
       and all(x["nota"].startswith("elegido después de ver T1 y T2") for x in filas)
       and len(candado.get("filas", [])) == 2 and len(candado.get("trabajos", {})) == 4
       and candado.get("procedencia", {}).get("codigo", {}).get("veredicto3.py"),
       "la salida (n = 30 y 100, la nota de §13) y el candado con las filas, los trabajos de la cola y el código")
    for x in filas:
        nota(f"{x['escenario']} {x['tanda']}: {x['brazo']} frente a {x['referencia']}: {x['cambio']} % {x['ic']}")
    se_niega("otra vez, con el candado en disco", prueba_final(P3), "ya corrió")
    commit(REPO, "candado", "plan3/listo/holdout.candado", "plan3/salidas/veredicto3_prueba_final.csv",
           forzar=["plan3/ciego/f1r", "plan3/ciego/f1a"])
    res = correr(P3, "veredicto3.py", "--verificar-prueba-final")
    corre("--verificar-prueba-final (y el correo del candado)", res, "prueba final verificada")
    ok("commit del candado" in res[1], "imprime el correo al asesor con el commit del candado y sus sha256")
    corre("--final con el candado commiteado: verifica la prueba final", final(P3), "escrito")
    # P1-M4: la salida y el candado cambiados, commiteados y empujados
    r = copia("candado_cambiado")
    p3 = os.path.join(r, "plan3")
    ruta_s = os.path.join(p3, v3.SALIDA_FINAL)
    texto = open(ruta_s, encoding="utf-8").read()
    fila = [x for x in csv.DictReader(texto.splitlines())][1]
    texto = texto.replace(fila["cambio"], "-12.30", 1)
    v3.escribir(ruta_s, texto)
    reg = leer(os.path.join(p3, v3.CANDADO))
    reg["salida"] = {v3.SALIDA_FINAL: hashlib.sha256(texto.encode("utf-8")).hexdigest()}
    reg["filas"][1]["cambio"] = "-12.30"
    escribir_json(os.path.join(p3, v3.CANDADO), reg)
    commit(r, "candado cambiado", "plan3/listo/holdout.candado", "plan3/salidas/veredicto3_prueba_final.csv")
    se_niega("la salida de la prueba final y su candado cambiados, commiteados y empujados (P1-M4): --final la vuelve "
             "a calcular", final(p3), "volver a calcularla no da")
    r = copia("sin_candado")
    p3 = os.path.join(r, "plan3")
    os.remove(os.path.join(p3, v3.CANDADO))
    se_niega("el candado borrado del disco (commiteado antes), la misma lista", prueba_final(p3), "ya corrió")
    r = copia("critico")
    p3 = os.path.join(r, "plan3")
    os.remove(os.path.join(p3, v3.CANDADO))
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
    se_niega("el candado borrado con git rm (commit y push)", prueba_final(p3), "ya corrió")
    r = copia("forzado")
    p3 = os.path.join(r, "plan3")
    base = os.path.dirname(r)
    git(base, "clone", "-q", "--no-checkout", os.path.join(base, "o.git"), "otro")
    git(os.path.join(base, "otro"), "push", "-q", "-f", "origin", "origin/plan3~1:refs/heads/plan3")
    os.remove(os.path.join(p3, v3.CANDADO))
    se_niega("un push forzado desde otro clon saca el candado de la rama empujada (en el repositorio que la vio)",
             prueba_final(p3), "se reescribió (push forzado)")
    r = copia("forzado_propio")
    p3 = os.path.join(r, "plan3")
    git(r, "reset", "-q", "--soft", "HEAD~1")
    git(r, "push", "-q", "-f", "origin", "plan3")
    git(r, "reset", "-q")
    for rel in ("listo/holdout.candado", v3.SALIDA_FINAL):
        os.remove(os.path.join(p3, rel))
    se_niega("reset y push forzado desde el propio repositorio, el candado borrado del disco", prueba_final(p3),
             "se reescribió (push forzado)")
    git(r, "update-ref", "-d", v3.VISTO)
    git(r, "reflog", "expire", "--expire=now", "--expire-unreachable=now", "--all")
    git(r, "gc", "-q", "--prune=now")
    rc, salida = prueba_final(p3)
    nota(f"LÍMITE (sin protección de la rama en GitHub): lo mismo, después de borrar el reflog y "
         f"refs/veredicto3/visto (como un clon nuevo, que no vio la rama de antes): rc {rc} ({motivo(salida)[:160]}). "
         f"Lo ve el asesor: el commit del candado de su correo ya no está en la rama")


def clon_nuevo():
    titulo("8. Un clon nuevo en Windows (core.autocrlf=true)")
    base = v3.carpeta_limpia(os.path.join(TMP, "c", "clon")) or os.path.join(TMP, "c", "clon")
    git(base, "-c", "core.autocrlf=true", "clone", "-q", "-b", "plan3", ORIGEN, "r")
    corre("--final en un clon nuevo (con las 7 líneas '-text' y los datos escritos como los escriben los programas)",
          final(os.path.join(base, "r", "plan3")), "escrito")


def main():
    inicio = time.time()
    try:
        trabajos, man = preparar()
        trabajos, man = noches(trabajos, man)
        c = cierre()
        git(REPO, "gc", "-q")
        m1 = next(h for h, n in nombres.items() if n == "manana 1")
        m4 = next(h for h, n in nombres.items() if n == "dev en plan3 entre el sello y el cierre")
        errores_del_cierre(c)
        ataques_cierre(c, m1, m4)
        ataques_antes_del_cierre()
        trabajos_f, man_f = enmienda_final(trabajos, man)
        c_resello = next(h for h, n in nombres.items() if n == "resello")
        errores_holdout(trabajos_f, man_f)
        noche_final(trabajos_f, man_f)
        ataques_final(c_resello, trabajos_f, man_f)
        prueba_final_y_candado()
        clon_nuevo()
    except Exception as ex:                       # la prueba misma fallo: se dice donde
        import traceback
        ok(False, f"la prueba se cortó: {type(ex).__name__}: {str(ex)[:400]}")
        print(traceback.format_exc()[-1500:])
    pasan = sum(1 for x in lineas if x.startswith("PASA"))
    fallan = sum(1 for x in lineas if x.startswith("FALLA"))
    lineas.append(f"=== {pasan} pasan, {fallan} fallan")
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas) + "\n")
    print(lineas[-1], f"({time.time() - inicio:.0f} s)")
    sys.exit(1 if fallan else 0)


if __name__ == "__main__":
    main()
