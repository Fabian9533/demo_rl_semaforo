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
import re
import shlex
import hashlib
import subprocess
from collections import defaultdict

PLAN3 = os.path.dirname(os.path.abspath(__file__))
ESPERADO = os.path.join(PLAN3, "cola", "manifiesto_esperado.json")
CIERRE = os.path.join(PLAN3, "cola", "manifiesto_cierre.json")
OTROS = ["cola/manifiesto_esperado.json", "cola/trabajos.jsonl", "cola/partes.txt", "cola/caidas.json",
         "cola/reemplazos.json", "promocion.json", "referencias_congeladas.json", "insumos/manifiesto.json"]
# git sin objetos de reemplazo (git replace) y con rutas largas: la historia es la que esta en los commits
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


MANANA = "cola/manifiesto_ciego.json"
# los commits que cambian estos archivos forman una sola cadena (veredicto3.CADENA; los merges que no los cambian no
# cuentan)
CADENA = ("cola/manifiesto_cierre.json", "listo/cierre.ok", MANANA, "listo/holdout.ok", "cola/reemplazos.json",
          "cola/enmiendas.json")
RUTA_CIEGO = re.compile(r"ciego/([^/\\]+)/eval_([^/\\]+?)__([^/\\]+)\.csv")


def historial(raiz=PLAN3):
    """La historia de git de HEAD (anclaje.Historial, sin red); RuntimeError si no se puede leer."""
    import anclaje
    try:
        return anclaje.Historial(raiz)
    except anclaje.ErrorAncla as ex:
        raise RuntimeError(str(ex))


def historia_ciego(raiz=PLAN3, hist=None):
    """[(commit, {ruta: sha256})] de cada version commiteada de cola/manifiesto_ciego.json en la historia de HEAD, de
    la mas vieja a la nueva: rev-list --full-history (un merge no esconde una manana) y un merge que no trae una
    version nueva no cuenta (un merge de codigo no es una manana); cada version con cat-file. Una version que no se
    puede leer o se borra es un error (RuntimeError), no un borrado."""
    import anclaje
    hist = hist or historial(raiz)
    salida = []
    try:
        versiones = hist.versiones(MANANA)
    except anclaje.ErrorAncla as ex:
        raise RuntimeError(str(ex))
    for c, texto in versiones:
        try:
            datos = json.loads(texto.decode("utf-8-sig"))
        except (UnicodeDecodeError, ValueError) as ex:
            raise RuntimeError(f"{MANANA} en {c[:10]} no es un JSON valido: {ex}")
        salida.append((c, {k: v["sha256"] for k, v in datos.items()}))
    return salida


def leer_reemplazos(raiz=PLAN3):
    """cola/reemplazos.json (§14): las salidas viejas que se conservan y la corrida rehecha que las reemplaza (un error
    de codigo; el trabajo _r2 escribe un CSV nuevo): lista de {viejo, nuevo, motivo, fecha}, las dos rutas de ciego/.
    Versionado y sellado (OTROS); las reglas de tiempo, en validar_reemplazos. Devuelve {viejo: entrada}; ValueError si
    una entrada esta incompleta o el archivo no se puede leer."""
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
        if not (isinstance(r, dict) and r.get("viejo") and r.get("nuevo") and r.get("motivo") and r.get("fecha")):
            raise ValueError(f"cola/reemplazos.json: cada entrada lleva viejo, nuevo, motivo y fecha: {r}")
        salida[r["viejo"]] = r
    return salida


def base_rehecha(clave):
    """(clave sin el sufijo de rehecha, N) de una clave '<x>_r<N>'; (clave, 0) si no lo tiene."""
    m = re.fullmatch(r"(.+?)_r(\d+)", clave)
    return (m.group(1), int(m.group(2))) if m else (clave, 0)


def validar_reemplazos(actuales, versiones, primero, vigentes, es_ancestro):
    """P1-H4 (tercera revision del 05.11): cada entrada de cola/reemplazos.json es una corrida rehecha por un error de
    codigo, declarada antes de correrla. actuales: {viejo: entrada}; versiones: [(commit, lista)] de cada version
    commiteada del archivo; primero: {csv: (commit de su primera manana, sha256)}; vigentes: los CSV del manifiesto;
    es_ancestro(a, b). Reglas: viejo y nuevo son rutas canonicas de ciego/ de la misma tanda y el mismo escenario y la
    clave de nuevo es la de viejo con un sufijo _r<N> mayor (una sola direccion); nuevo esta en el manifiesto y viejo
    no; el commit que agrego la entrada es posterior a la primera manana de viejo y anterior a la primera de nuevo; una
    entrada no se borra ni cambia despues. Devuelve (problemas, [entrada con commit, manana_viejo y manana_nuevo])."""
    clave = lambda r: (r.get("viejo"), r.get("nuevo"))                  # noqa: E731
    lista_de = lambda v: v.get("reemplazos", []) if isinstance(v, dict) else (v or [])   # noqa: E731
    problemas, salida = [], []
    for (c1, v1), (c2, v2) in zip(versiones, versiones[1:]):
        despues = {clave(r): r for r in lista_de(v2)}
        quitadas = [k for k, r in ((clave(r), r) for r in lista_de(v1)) if despues.get(k) != r]
        if quitadas:
            problemas.append(f"una entrada de cola/reemplazos.json se borro o cambio en el commit {c2[:10]}: "
                             f"{quitadas[0][0]}")
    for viejo, r in sorted(actuales.items()):
        nuevo = r.get("nuevo")
        pv, pn = RUTA_CIEGO.fullmatch(viejo or ""), RUTA_CIEGO.fullmatch(nuevo or "")
        if pv is None or pn is None or nuevo == viejo:
            problemas.append(f"{viejo} -> {nuevo}: las dos rutas son de ciego/, canonicas y distintas")
            continue
        (tv, ev, kv), (tn, en, kn) = pv.groups(), pn.groups()
        (bv, nv), (bn, nn) = base_rehecha(kv), base_rehecha(kn)
        if (tv, ev, bv) != (tn, en, bn) or nn <= nv:
            problemas.append(f"{nuevo} no es una corrida rehecha de {viejo} (misma tanda y escenario, la clave "
                             f"{bv}_r<N> con un N mayor: una sola direccion)")
            continue
        if viejo in vigentes or nuevo not in vigentes:
            problemas.append(f"{viejo} sigue en el manifiesto o {nuevo} no esta: el manifiesto trae la rehecha en "
                             f"lugar de la vieja")
            continue
        e_c = next((c for c, v in versiones if any(clave(x) == (viejo, nuevo) for x in lista_de(v))), None)
        if e_c is None:
            problemas.append(f"{viejo} -> {nuevo} no esta commiteado")
            continue
        mv, mn = primero.get(viejo, (None,))[0], primero.get(nuevo, (None,))[0]
        if mv is None or mv == e_c or not es_ancestro(mv, e_c):
            problemas.append(f"{viejo}: tiene que estar en una manana anterior al commit que declara el reemplazo "
                             f"({e_c[:10]})")
        if mn is None or mn == e_c or not es_ancestro(e_c, mn):
            problemas.append(f"{nuevo}: su primera manana tiene que ser posterior al commit que declara el reemplazo "
                             f"({e_c[:10]}): la enmienda va antes de la corrida rehecha")
        salida.append(dict(r, commit=e_c, manana_viejo=mv or "", manana_nuevo=mn or ""))
    return problemas, salida


def huerfanos(en_mananas, vigentes, reemplazos, trabajos=()):
    """CSV de ciego/ de una tanda que no es de la prueba final que estan en un manifiesto de la manana y no entre los
    vigentes (los del manifiesto esperado, o los sellados) ni declarados en cola/reemplazos.json con su nuevo vigente
    (validar_reemplazos decide si la declaracion vale). Un CSV ciego fuera del cierre seria una evaluacion que no se
    sabe por que se descarto."""
    malos = []
    for rel in sorted(en_mananas):
        partes = rel.split("/")
        if not (rel.startswith("ciego/") and rel.endswith(".csv")) or rel in vigentes:
            continue
        if len(partes) > 2 and es_final(partes[1]):
            continue
        r = reemplazos.get(rel)
        if r and r.get("nuevo") and r["nuevo"] in vigentes:
            continue
        malos.append(rel)
    return malos


def ruta_canonica(e):
    """La ruta del CSV de una entrada del manifiesto como la escribe generar_trabajos3.evaluacion."""
    import generar_trabajos3 as gt
    uso = gt.TANDAS.get(e.get("tanda"), ("",))[0]
    return f"{'ciego' if uso in gt.CIEGAS else 'parciales'}/{e.get('tanda')}/eval_{e.get('escenario')}__" \
           f"{e.get('clave', '')}.csv"


def rutas_canonicas(esperado, trabajos):
    """P1-H2: problemas de rutas: cada CSV del manifiesto esta en su ruta canonica (sin './', sin '\\', sin cambios de
    mayusculas), es la --salida de su trabajo y no se repite."""
    import generar_trabajos3 as gt
    problemas, vistas = [], set()
    for e in esperado:
        if e.get("tanda") not in gt.TANDAS:
            problemas.append(f"{e.get('csv')}: tanda desconocida {e.get('tanda')}")
            continue
        canon = ruta_canonica(e)
        if e.get("csv") != canon:
            problemas.append(f"{e.get('csv')} no es la ruta canonica de su entrada ({canon})")
        t = trabajos.get(e.get("trabajo"))
        if t is None:
            problemas.append(f"{e.get('csv')}: su trabajo {e.get('trabajo')} no esta en cola/trabajos.jsonl")
        else:
            partes = shlex.split(t.get("cmd", ""))
            salida = partes[partes.index("--salida") + 1] if "--salida" in partes[:-1] else None
            if salida != e.get("csv"):
                problemas.append(f"{e.get('csv')}: su trabajo {t['id']} escribe {salida}")
        if canon in vistas:
            problemas.append(f"{canon} esta dos veces en el manifiesto")
        vistas.add(canon)
    return problemas


def listas_del_generador(raiz=PLAN3):
    """P1-H2: [archivos] de cola/trabajos.jsonl y cola/manifiesto_esperado.json que no son los que escribe
    generar_trabajos3 (su codigo de hoy) con cola/partes.txt y cola/caidas.json de raiz (como 'generar_trabajos3.py
    --comprobar'). ValueError si no se puede generar."""
    import generar_trabajos3 as gt
    ruta_p = os.path.join(raiz, "cola", "partes.txt")
    if not os.path.exists(ruta_p):
        raise ValueError("falta cola/partes.txt (lo escribe generar_trabajos3.py)")
    with open(ruta_p, encoding="utf-8-sig") as f:
        partes = [x.strip() for x in f.read().strip().split(",") if x.strip()]
    desconocidas = [x for x in partes if x not in gt.PARTES]
    if desconocidas:
        raise ValueError(f"cola/partes.txt nombra partes que el generador no tiene: {desconocidas}")
    viejas = gt.CAIDAS
    try:
        gt.CAIDAS = gt.leer_caidas(os.path.join(raiz, "cola", "caidas.json"))
        trabajos, man = gt.generar_con_manifiesto(partes)
    finally:
        gt.CAIDAS = viejas
    esperados = {"cola/trabajos.jsonl": "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in trabajos),
                 "cola/manifiesto_esperado.json": json.dumps(man, ensure_ascii=False, indent=0) + "\n"}
    malos = []
    for rel, texto in esperados.items():
        ruta = os.path.join(raiz, rel)
        hoy = open(ruta, "rb").read() if os.path.exists(ruta) else b""
        if hoy.replace(b"\r\n", b"\n") != texto.encode("utf-8"):
            malos.append(rel)
    return malos


def revisar_historia(esperado, raiz=PLAN3, raiz_git=None, hist=None):
    """Problemas de los CSV de ciego/ frente a los manifiestos de cada manana (vacio si todo cuadra), en la historia de
    HEAD: los commits de las mananas, el sello, cierre.ok, holdout.ok, los reemplazos y las enmiendas forman una sola
    cadena; los CSV que se cotejan son los de las tandas ciegas del manifiesto (por el uso de su tanda, no por el
    prefijo de la ruta), cada uno en su ruta canonica; ningun CSV cambia su sha256 de una manana a otra;
    cola/reemplazos.json sigue validar_reemplazos; y ningun CSV de ciego/ de una manana queda fuera del manifiesto sin
    un reemplazo.
    Devuelve (problemas, el commit de la ultima manana). raiz_git: no se usa (la historia sale de raiz)."""
    import anclaje
    import generar_trabajos3 as gt
    hist = hist or historial(raiz)
    malos = []
    try:
        hist.cadena(*CADENA)
    except anclaje.ErrorAncla as ex:
        malos.append(str(ex))
    historia = historia_ciego(raiz, hist)
    primera = {}
    for commit, manifiesto in historia:
        for ruta, h in manifiesto.items():
            if ruta in primera and primera[ruta][1] != h:
                malos.append(f"{ruta}: su sha256 cambio entre la manana del {primera[ruta][0][:10]} y la del {commit[:10]}")
            primera.setdefault(ruta, (commit, h))
    for e in esperado:
        if gt.TANDAS.get(e["tanda"], ("",))[0] not in gt.CIEGAS or es_final(e["tanda"]):
            continue                                # la prueba final se coteja en veredicto3 --prueba-final
        if "clave" in e and e["csv"] != ruta_canonica(e):
            malos.append(f"{e['csv']}: no es la ruta canonica de su entrada ({ruta_canonica(e)})")
        elif e["csv"] not in primera:
            malos.append(f"{e['csv']}: nunca aparecio en un manifiesto de la manana commiteado")
        elif sha(os.path.join(raiz, e["csv"])) != primera[e["csv"]][1]:
            malos.append(f"{e['csv']}: hoy no es el que se registro la primera manana")
    actuales = leer_reemplazos(raiz)
    try:
        versiones = [(c, json.loads(x.decode("utf-8-sig"))) for c, x in hist.versiones("cola/reemplazos.json")]
    except (anclaje.ErrorAncla, UnicodeDecodeError, ValueError) as ex:
        raise RuntimeError(f"cola/reemplazos.json en la historia de git: {ex}")
    vigentes = {e["csv"] for e in esperado}
    problemas_r, validos = validar_reemplazos(actuales, versiones, primera, vigentes, hist.es_ancestro)
    malos += [f"cola/reemplazos.json: {m}" for m in problemas_r]
    for rel in huerfanos(set(primera), vigentes, {r["viejo"]: r for r in validos}):
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
        _, trabajos = leer_caidas_y_trabajos()
        rutas = rutas_canonicas(esperado, trabajos)
        for m in rutas[:30]:
            print("  MAL", m)
        if rutas:
            sys.exit(f"manifiesto: {len(rutas)} rutas del manifiesto no son las del generador")
        listas = listas_del_generador()
        if listas:
            sys.exit(f"manifiesto: {', '.join(listas)} no son los que escribe el generador con cola/partes.txt "
                     f"(python generar_trabajos3.py --comprobar)")
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
                  "CSV de ciego/ (git add -f plan3/ciego); python veredicto3.py --preflight cierre; push; despues "
                  "veredicto3.py --final. El sello nunca va en un commit de la manana")


if __name__ == "__main__":
    main()
