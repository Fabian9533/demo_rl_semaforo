"""
manifiesto.py - Revisa las evaluaciones contra cola/manifiesto_esperado.json, sin mirar metricas (PLAN3 0.15 y 5.1).

Uso (desde plan3/):
  python manifiesto.py revisar            cuantos CSV esperados estan, faltan o estan mal (solo cuentas)
  python manifiesto.py cierre             exige todo bien y escribe cola/manifiesto_cierre.json
  python manifiesto.py prueba             prueba en seco con CSV sinteticos en tmp_prueba_manifiesto/
Un CSV esta bien si tiene exactamente las semillas esperadas (ni de mas ni de menos), una fila por semilla y un solo
brazo, y si en cada (escenario, tanda) todos los brazos generan los mismos vehiculos en cada semilla (numeros
aleatorios comunes). Solo lee las columnas semilla, brazo y generados: ninguna metrica de desempeno.
El cierre ademas (prerregistro §14):
  - coteja cada CSV de ciego/ con la historia versionada de cola/manifiesto_ciego.json (lo sube p3_noche.py cada
    manana): tiene que aparecer en algun manifiesto commiteado y su sha256 no pudo cambiar desde la primera manana;
  - sella, ademas de los CSV ("csv"), los metas de las politicas evaluadas ("metas": cada .pt y su .json) y los
    archivos que deciden que se lee ("otros": manifiesto esperado, lista de trabajos y sus partes, caidas, promocion,
    referencias congeladas). veredicto3.py --final coteja todo eso.
"""
import os
import csv
import sys
import json
import glob
import shlex
import hashlib
import subprocess
from collections import defaultdict

PLAN3 = os.path.dirname(os.path.abspath(__file__))
ESPERADO = os.path.join(PLAN3, "cola", "manifiesto_esperado.json")
CIERRE = os.path.join(PLAN3, "cola", "manifiesto_cierre.json")
CIEGO_MANANA = "plan3/cola/manifiesto_ciego.json"           # ruta en git, desde la raiz del worktree
OTROS = ["cola/manifiesto_esperado.json", "cola/trabajos.jsonl", "cola/partes.txt", "cola/caidas.json",
         "cola/reemplazos.json", "promocion.json", "referencias_congeladas.json", "insumos/manifiesto.json"]
# git sin objetos de reemplazo (git replace) y con rutas largas: la historia es la que esta en los commits
ENTORNO_GIT = dict(os.environ, GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")


def git(*args, cwd):
    """(rc, stdout en bytes, stderr) de git con ENTORNO_GIT y core.longpaths."""
    r = subprocess.run(["git", "-c", "core.longpaths=true", *args], cwd=cwd, capture_output=True, env=ENTORNO_GIT)
    return r.returncode, r.stdout, r.stderr.decode("utf-8", "replace")


def es_final(tanda):
    """Tandas de la prueba final (uso 'final'): no se sellan al cierre; la enmienda que la active las agrega."""
    try:
        import generar_trabajos3 as gt
        return gt.TANDAS.get(tanda, ("",))[0] == "final"
    except Exception:
        return False


def rango(texto):
    salida = []
    for parte in texto.split(","):
        a, b = parte.split("-") if "-" in parte else (parte, parte)
        salida += list(range(int(a), int(b) + 1))
    return salida


def sha(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def leer_csv(ruta):
    """(brazos, {semilla: generados}, filas) sin leer metricas."""
    brazos, generados, filas = set(), {}, 0
    with open(ruta, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            filas += 1
            brazos.add(r["brazo"])
            generados[int(r["semilla"])] = r.get("generados", "")
    return brazos, generados, filas


def revisar(esperado, raiz=PLAN3):
    estado = {"bien": [], "faltan": [], "mal": []}
    grupos = defaultdict(dict)                         # (escenario, tanda) -> {csv: {semilla: generados}}
    caidas, trabajos = None, None                      # se leen solo si falta algun CSV
    for e in esperado:
        if es_final(e["tanda"]):
            continue
        ruta = os.path.join(raiz, e["csv"])
        if not os.path.exists(ruta):
            if caidas is None:
                caidas, trabajos = leer_caidas_y_trabajos(raiz)
            estado["faltan"].append(e["csv"] + (" (base caida declarada despues: regenerar el manifiesto)"
                                                if caida_declarada(e, caidas, trabajos) else ""))
            continue
        brazos, generados, filas = leer_csv(ruta)
        semillas = rango(e["semillas"])
        problemas = []
        if sorted(generados) != semillas:
            problemas.append(f"semillas {len(generados)} distintas de las {len(semillas)} esperadas")
        if filas != len(semillas):
            problemas.append(f"{filas} filas para {len(semillas)} semillas")
        if len(brazos) != 1:
            problemas.append(f"{len(brazos)} brazos")
        if problemas:
            estado["mal"].append(f"{e['csv']}: {'; '.join(problemas)}")
        else:
            estado["bien"].append(e["csv"])
            grupos[(e["escenario"], e["tanda"])][e["csv"]] = generados
    for (esc, tanda), csvs in sorted(grupos.items()):
        rutas = sorted(csvs)
        ref = csvs[rutas[0]]
        for r in rutas[1:]:
            dif = [s for s in ref if csvs[r].get(s) != ref[s]]
            if dif:
                estado["mal"].append(f"{r}: genera otros vehiculos que {rutas[0]} en {len(dif)} semillas")
    return estado


def leer_caidas_y_trabajos(raiz=PLAN3):
    """(corridas declaradas caidas en <raiz>/cola/caidas.json, {id: trabajo} de <raiz>/cola/trabajos.jsonl)."""
    import generar_trabajos3 as gt
    caidas = gt.leer_caidas(os.path.join(raiz, "cola", "caidas.json"))
    trabajos = {}
    ruta = os.path.join(raiz, "cola", "trabajos.jsonl")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            for linea in f:
                if linea.strip():
                    t = json.loads(linea)
                    trabajos[t["id"]] = t
    return caidas, trabajos


def caida_declarada(e, caidas, trabajos):
    """¿El CSV es de una base declarada caida? Con la corrida de la politica que juega su trabajo y las que salen de
    ella (generar_trabajos3.caida), como el generador; caidas y trabajos de leer_caidas_y_trabajos."""
    import generar_trabajos3 as gt
    trabajo = trabajos.get(e.get("trabajo")) or {}
    partes = shlex.split(trabajo.get("cmd", ""))
    politica = partes[partes.index("--politica") + 1] if "--politica" in partes[:-1] else None
    corrida = gt.corrida_de_politica(politica)
    return bool(caidas) and corrida is not None and gt.caida(*corrida, caidas=caidas)


def historia_ciego(raiz_git):
    """[(commit, {ruta: sha256})] de cada version commiteada de cola/manifiesto_ciego.json, de la mas vieja a la nueva:
    toda la historia (rev-list --full-history --topo-order: un merge no esconde una manana) y cada version con
    cat-file. Una version que no se puede leer es un error (RuntimeError), no un borrado."""
    rc, out, err = git("rev-list", "--full-history", "--topo-order", "--reverse", "HEAD", "--", CIEGO_MANANA,
                       cwd=raiz_git)
    if rc != 0:
        raise RuntimeError(f"git rev-list fallo: {err.strip()}")
    salida = []
    for c in out.decode().split():
        rc, texto, err = git("cat-file", "-p", f"{c}:{CIEGO_MANANA}", cwd=raiz_git)
        if rc != 0:
            raise RuntimeError(f"no se pudo leer {CIEGO_MANANA} en {c[:10]} (borrado o ilegible): {err.strip()}")
        try:
            datos = json.loads(texto.decode("utf-8-sig"))
        except (UnicodeDecodeError, ValueError) as ex:
            raise RuntimeError(f"{CIEGO_MANANA} en {c[:10]} no es un JSON valido: {ex}")
        salida.append((c, {k: v["sha256"] for k, v in datos.items()}))
    return salida


def leer_reemplazos(raiz=PLAN3):
    """cola/reemplazos.json (§14): las salidas viejas que se conservan y que otra reemplaza (una corrida rehecha por un
    error de codigo, un trabajo _r2): lista de {viejo, nuevo (CSV) o trabajo (id), motivo, fecha}. Versionado y sellado
    (OTROS). Devuelve {viejo: entrada}; ValueError si una entrada esta incompleta o el archivo no se puede leer."""
    ruta = os.path.join(raiz, "cola", "reemplazos.json")
    if not os.path.exists(ruta):
        return {}
    try:
        with open(ruta, encoding="utf-8-sig") as f:
            datos = json.load(f)
    except (OSError, UnicodeDecodeError, ValueError) as ex:
        raise ValueError(f"cola/reemplazos.json: no es un JSON valido ({ex})")
    salida = {}
    for r in (datos.get("reemplazos", []) if isinstance(datos, dict) else datos):
        if not (isinstance(r, dict) and r.get("viejo") and (r.get("nuevo") or r.get("trabajo")) and r.get("motivo")
                and r.get("fecha")):
            raise ValueError(f"cola/reemplazos.json: cada entrada lleva viejo, nuevo o trabajo, motivo y fecha: {r}")
        salida[r["viejo"]] = r
    return salida


def huerfanos(en_mananas, vigentes, reemplazos, trabajos):
    """CSV de ciego/ de una tanda que no es de la prueba final que estan en un manifiesto de la manana y no entre los
    vigentes (los del manifiesto esperado, o los sellados) ni declarados en cola/reemplazos.json con su nuevo vigente
    o su trabajo en la lista. Un CSV ciego fuera del cierre seria una evaluacion que no se sabe por que se descarto."""
    malos = []
    for rel in sorted(en_mananas):
        partes = rel.split("/")
        if not (rel.startswith("ciego/") and rel.endswith(".csv")) or rel in vigentes:
            continue
        if len(partes) > 2 and es_final(partes[1]):
            continue
        r = reemplazos.get(rel)
        if r and ((r.get("nuevo") and r["nuevo"] in vigentes) or (r.get("trabajo") and r["trabajo"] in trabajos)):
            continue
        malos.append(rel)
    return malos


def revisar_historia(esperado, raiz=PLAN3, raiz_git=None):
    """Problemas de los CSV de ciego/ frente a los manifiestos de cada manana (vacio si todo cuadra)."""
    historia = historia_ciego(raiz_git or os.path.dirname(raiz))
    primera = {}
    malos = []
    for commit, manifiesto in historia:
        for ruta, h in manifiesto.items():
            if ruta in primera and primera[ruta][1] != h:
                malos.append(f"{ruta}: su sha256 cambio entre la manana del {primera[ruta][0][:10]} y la del {commit[:10]}")
            primera.setdefault(ruta, (commit, h))
    for e in esperado:
        if not e["csv"].startswith("ciego/") or es_final(e["tanda"]):
            continue                                # la prueba final se coteja en veredicto3 --prueba-final
        if e["csv"] not in primera:
            malos.append(f"{e['csv']}: nunca aparecio en un manifiesto de la manana commiteado")
        elif sha(os.path.join(raiz, e["csv"])) != primera[e["csv"]][1]:
            malos.append(f"{e['csv']}: hoy no es el que se registro la primera manana")
    _, trabajos = leer_caidas_y_trabajos(raiz)
    for rel in huerfanos(set(primera), {e["csv"] for e in esperado}, leer_reemplazos(raiz), set(trabajos)):
        malos.append(f"{rel}: esta en el manifiesto de la manana {primera[rel][0][:10]} y no en el manifiesto "
                     f"esperado ni en cola/reemplazos.json")
    return malos, (historia[-1][0] if historia else None)


def politicas_evaluadas(esperado, raiz=PLAN3):
    """Rutas de las politicas que juega cada trabajo de evaluacion del manifiesto (--politica en su comando)."""
    trabajos = {}
    with open(os.path.join(raiz, "cola", "trabajos.jsonl"), encoding="utf-8") as f:
        for linea in f:
            if linea.strip():
                t = json.loads(linea)
                trabajos[t["id"]] = t
    rutas = set()
    for e in esperado:
        partes = shlex.split(trabajos[e["trabajo"]]["cmd"])
        if "--politica" in partes:
            rutas.add(partes[partes.index("--politica") + 1])
    return sorted(rutas)


def sello(esperado, raiz=PLAN3):
    """Lo que se sella al cierre: CSV, las politicas publicadas con sus metas (todas las politica_*.pt y .json de
    plan3/: veredicto3 lee tambien las de las bases que no se evaluan, como C0 por base) y los archivos que deciden
    que se lee. Las politicas que juega cada evaluacion tienen que estar entre ellas."""
    datos = {"csv": {e["csv"]: sha(os.path.join(raiz, e["csv"])) for e in esperado if not es_final(e["tanda"])},
             "metas": {}, "otros": {}}
    for ruta in sorted(glob.glob(os.path.join(raiz, "politica_*.pt")) + glob.glob(os.path.join(raiz, "politica_*.json"))):
        datos["metas"][os.path.relpath(ruta, raiz).replace(os.sep, "/")] = sha(ruta)
    faltan = [pt for pt in politicas_evaluadas(esperado, raiz) if pt not in datos["metas"]]
    if faltan:
        raise RuntimeError(f"politicas evaluadas que no estan en plan3/: {faltan[:5]}")
    otros = list(OTROS) + sorted(os.path.relpath(p, raiz).replace(os.sep, "/")
                                 for p in glob.glob(os.path.join(raiz, "promocion", "*.json")))
    for ruta in otros:
        if os.path.exists(os.path.join(raiz, ruta)):
            datos["otros"][ruta] = sha(os.path.join(raiz, ruta))
    return datos


def prueba():
    """CSV sinteticos: uno bien, uno con una semilla de mas, uno que falta y uno con otros vehiculos."""
    tmp = os.path.join(PLAN3, "tmp_prueba_manifiesto")
    os.makedirs(os.path.join(tmp, "ciego", "t1r"), exist_ok=True)
    esperado = [{"csv": f"ciego/t1r/eval_x__{k}.csv", "escenario": "x", "tanda": "t1r", "semillas": "8001-8003"}
                for k in ("a", "b", "c", "d", "e")]

    def escribir(k, semillas, generados=100):
        with open(os.path.join(tmp, "ciego", "t1r", f"eval_x__{k}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["brazo", "semilla", "generados", "retraso_total_prom"])
            w.writeheader()
            for s in semillas:
                w.writerow({"brazo": k, "semilla": s, "generados": generados, "retraso_total_prom": 1.0})
    escribir("a", [8001, 8002, 8003])
    escribir("b", [8001, 8002, 8003, 8004])
    escribir("d", [8001, 8002, 8003], generados=99)
    escribir("e", [8001, 8002, 8003])
    r = revisar(esperado, raiz=tmp)
    bien = (r["faltan"] == ["ciego/t1r/eval_x__c.csv"] and len(r["mal"]) == 2
            and any("eval_x__b" in m and "semillas" in m for m in r["mal"])
            and any("eval_x__d" in m and "otros vehiculos" in m for m in r["mal"]))
    print("prueba del manifiesto (semillas, faltantes, vehiculos):", "bien" if bien else f"MAL {r}")
    # Historia de los manifiestos de la manana, en un repositorio git de prueba: a aparece y no cambia (bien); e
    # cambia entre dos mananas (mal); d nunca aparece (mal).
    repo = os.path.join(tmp, "repo")
    import shutil
    shutil.rmtree(repo, ignore_errors=True)
    carpeta = os.path.join(repo, "plan3")
    os.makedirs(os.path.join(carpeta, "cola"))
    shutil.copytree(os.path.join(tmp, "ciego"), os.path.join(carpeta, "ciego"))

    def git(*a):
        subprocess.run(["git", *a], cwd=repo, check=True, capture_output=True)

    def manana(datos):
        with open(os.path.join(carpeta, "cola", "manifiesto_ciego.json"), "w", encoding="utf-8") as f:
            json.dump(datos, f)
        git("add", "-A")
        git("-c", "user.name=prueba", "-c", "user.email=prueba@local", "commit", "-q", "-m", "manana")
    git("init", "-q")
    ra, re_ = "ciego/t1r/eval_x__a.csv", "ciego/t1r/eval_x__e.csv"
    sha_a, sha_e = sha(os.path.join(carpeta, ra)), sha(os.path.join(carpeta, re_))
    manana({ra: {"sha256": sha_a}, re_: {"sha256": "0" * 64}})
    manana({ra: {"sha256": sha_a}, re_: {"sha256": sha_e}})
    esp = [e for e in esperado if e["csv"] in (ra, re_, "ciego/t1r/eval_x__d.csv")]
    malos, ultimo = revisar_historia(esp, raiz=carpeta, raiz_git=repo)
    bien_h = (len(malos) == 3 and ultimo is not None
              and any(re_ in m and "cambio entre" in m for m in malos)
              and any(re_ in m and "primera manana" in m for m in malos)
              and any("eval_x__d" in m and "nunca aparecio" in m for m in malos)
              and not any(ra in m for m in malos))
    print("prueba del manifiesto (historia de las mananas):", "bien" if bien_h else f"MAL {malos}")
    return bien and bien_h


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else "revisar"
    if modo == "prueba":
        sys.exit(0 if prueba() else 1)
    try:
        principal(modo)
    except (ValueError, RuntimeError) as ex:        # caidas.json, reemplazos.json o la historia: una linea con la causa
        sys.exit(f"manifiesto: {ex}")


def principal(modo):
    with open(ESPERADO, encoding="utf-8-sig") as f:
        esperado = json.load(f)
    r = revisar(esperado)
    print(f"{len(esperado)} CSV esperados: {len(r['bien'])} bien, {len(r['faltan'])} faltan, {len(r['mal'])} mal")
    for m in r["faltan"][:30]:
        print("  FALTA", m)
    for m in r["mal"][:30]:
        print("  MAL", m)
    if modo == "cierre":
        if r["faltan"] or r["mal"]:
            sys.exit("manifiesto: no se puede cerrar con CSV que faltan o estan mal")
        malos, ultimo = revisar_historia(esperado)
        for m in malos[:30]:
            print("  MAL", m)
        if malos:
            sys.exit(f"manifiesto: {len(malos)} CSV de ciego/ no cuadran con los manifiestos de cada manana")
        datos = sello(esperado)
        datos["manifiesto_ciego_commit"] = ultimo
        with open(CIERRE, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=0, sort_keys=True)
        print(f"escrito {os.path.relpath(CIERRE, PLAN3)}: {len(datos['csv'])} CSV, {len(datos['metas'])} metas, "
              f"{len(datos['otros'])} otros; ultimo manifiesto de la manana {str(ultimo)[:10]}")
        if os.path.exists(os.path.join(PLAN3, "listo", "cierre.ok")):
            print("siguiente (PLAN3 5.3, resello de la prueba final): commit de cola/manifiesto_cierre.json y push; "
                  "despues listo/holdout.ok (commit y push) y recien la noche final")
        else:
            print("siguiente (PLAN3 5.1): Fabian crea listo/cierre.ok; UN commit con el sello, cierre.ok, cola/ y los "
                  "CSV de ciego/ (git add -f plan3/ciego); push; despues veredicto3.py --final. El sello nunca va en "
                  "un commit de la manana")


if __name__ == "__main__":
    main()
