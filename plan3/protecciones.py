"""
protecciones.py - Controles del bloque plan3 (DECISIONES B1; prerregistro §3 y §14).

Uso (desde <worktree>/plan3):
  python protecciones.py antes     antes de lanzar la cola: git, prerregistro, insumos, checkpoints, versiones, lista
  python protecciones.py despues   al terminar la noche: git, insumos, checkpoints, fallidos
  python protecciones.py comando "<cmd>" [--uso U]   revisa un comando suelto (para probar)
Sale con codigo 1 si encuentra un problema. Escribe solo cola/control_<fecha>_<momento>.json.

Tres capas:
  1. Comandos (revisar_comando), antes de lanzar cada trabajo. Desenvuelve el lanzador con_escenarios.py. Solo
     scripts de la tabla del prerregistro; nada que nombre plan2 o TESIS (con limites de palabra), rutas absolutas,
     '..' fuera del script de la raiz, operadores de consola ni --instalar. rl_ippo train con --etiqueta p3...,
     base de entrenamiento y semillas de validacion de la tabla; toda semilla dentro del bloque del uso declarado
     del trabajo y nunca en las prohibidas; las tandas decisivas escriben en ciego/; la prueba final exige
     listo/holdout.ok.
  2. Lista de trabajos (revisar_trabajos): ids unicos, dependencias que existen, sin ciclos, ninguna salida
     declarada por dos trabajos, ningun entrenamiento repetido fuera de su cadena de tramos.
  3. Git y archivos (estado_git y compañia): rama plan3; plan2/ y TESIS/ sin cambios, sin nuevos y sin ignorados;
     git diff main...HEAD -- plan2 TESIS vacio; todo lo nuevo bajo plan3/; insumos y checkpoints iguales a su
     manifiesto; prerregistro igual al de origin; versiones de Python, torch y SUMO.
"""
import os
import re
import sys
import json
import shlex
import hashlib
import subprocess
import time

PLAN3 = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(PLAN3)                      # raiz del worktree
COLA = os.path.join(PLAN3, "cola")
PRERREGISTRO = os.path.join(PLAN3, "PRERREGISTRO.md")
LANZADOR = "../con_escenarios.py"
SCRIPTS_RAIZ = {"../rl_ippo.py", "../evaluar.py", "../barrer_fijo.py"}
PROHIBIDO = re.compile(r"\bplan2\b|\bTESIS\b|[A-Za-z]:[\\/]|\\|[&|<>;`$]|(^|\s)cd(\s|$)|--instalar", re.IGNORECASE)
OPCION_SEMILLAS = re.compile(r"^--[a-z-]*(semilla|seed)[a-z-]*$")
USOS_CIEGOS = {"examen_regular", "examen_h1", "examen_aleatorio", "final"}
LARGO_MAX = 200                                    # caracteres desde C:\ (MAX_PATH de Windows = 260)
VERSIONES = {"python": "3.14.6", "torch": "2.14.0+cpu", "sumo": "1.25.0"}


def sha(ruta):
    if not os.path.exists(ruta):
        return ""
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*args, cwd=RAIZ):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout


# ---------------- Tabla del prerregistro ----------------

def tabla_prerregistro(texto=None):
    """El bloque JSON de §3 ("Tabla para la maquina"); la unica fuente de semillas, bases, scripts y etiqueta."""
    if texto is None:
        with open(PRERREGISTRO, encoding="utf-8") as f:
            texto = f.read()
    m = re.search(r"Tabla para la m[aá]quina.*?```json\s*(\{.*?\})\s*```", texto, re.S)
    if not m:
        raise ValueError("el prerregistro no tiene la tabla JSON de §3")
    return json.loads(m.group(1))


_TABLA = None


def tabla():
    global _TABLA
    if _TABLA is None:
        _TABLA = tabla_prerregistro()
    return _TABLA


def rango(texto):
    """'1001-1030,2001' -> [1001, ..., 1030, 2001]."""
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


def en_tramos(s, tramos):
    return any(a <= s <= b for a, b in tramos)


# ---------------- Capa 1: comandos ----------------

def opcion(args, nombre):
    if nombre in args:
        k = args.index(nombre)
        return args[k + 1] if k + 1 < len(args) else ""
    return None


def desenvolver(partes):
    """['python', '../con_escenarios.py', prog, *args] -> (prog, args); ['python', prog, *args] -> (prog, args)."""
    if len(partes) >= 3 and partes[1] == LANZADOR:
        return partes[2], partes[3:]
    return partes[1], partes[2:]


def revisar_comando(t, existe=os.path.exists):
    """Problemas de un trabajo {"id", "cmd", "uso", ...}; lista vacia si esta bien."""
    cmd, malos = t.get("cmd", ""), []
    tab = tabla()
    if PROHIBIDO.search(cmd):
        malos.append("nombra plan2/TESIS, una ruta absoluta, '\\', cd, --instalar u operadores de consola")
    try:
        partes = shlex.split(cmd)
    except ValueError as e:
        return malos + [f"comando ilegible: {e}"]
    if len(partes) < 2 or partes[0] != "python":
        return malos + ["debe ser 'python <script> ...'"]
    prog, args = desenvolver(partes)
    permitidos = set(tab["scripts"]) - {LANZADOR}
    if prog not in permitidos:
        malos.append(f"script no permitido: {prog}")
    if prog.startswith("..") and prog not in SCRIPTS_RAIZ:
        malos.append(f"solo se sube de carpeta para los scripts de la raiz: {prog}")
    if any(".." in a for a in args):
        malos.append("un argumento sube de carpeta ('..')")
    uso = t.get("uso", "")
    semillas_tab = tab["semillas"]
    if uso and uso not in semillas_tab and uso not in ("entrenamiento", "sin_semillas"):
        malos.append(f"uso desconocido: {uso}")
    # Semillas: toda opcion que nombre semillas o seed.
    prohibidas = tab.get("prohibidas", [])
    es_entreno = prog == "../rl_ippo.py" and args[:1] == ["train"]
    for k, a in enumerate(args):
        if not OPCION_SEMILLAS.match(a) or k + 1 >= len(args):
            continue
        try:
            valores = rango(args[k + 1])
        except ValueError:
            malos.append(f"{a} ilegible: {args[k + 1]}")
            continue
        if any(en_tramos(s, prohibidas) for s in valores):
            malos.append(f"{a} usa semillas prohibidas: {args[k + 1]}")
        if es_entreno and a == "--seed":
            bases = tab["bases"]["principal"] + tab["bases"]["variantes"]
            if uso == "humo":
                bases = bases + tab["bases"]["humo"]
            if any(s not in bases for s in valores):
                malos.append(f"base de entrenamiento fuera de la tabla: {args[k + 1]}")
            continue
        if es_entreno and a == "--val-seeds":
            nombre = "validacion" + (" o humo" if uso == "humo" else "")
            bloque = semillas_tab["validacion"] + (semillas_tab["humo"] if uso == "humo" else [])
        elif uso in semillas_tab:
            nombre, bloque = uso, semillas_tab[uso]
        else:
            malos.append(f"{a} en un trabajo sin uso de semillas declarado")
            continue
        fuera = [s for s in valores if not en_tramos(s, bloque)]
        if fuera:
            malos.append(f"{a} fuera del bloque '{nombre}': {fuera[:5]}")
    if es_entreno:
        et = opcion(args, "--etiqueta")
        if not et or not re.fullmatch(tab["etiqueta"], et):
            malos.append("rl_ippo train sin --etiqueta p3...: pisaria los nombres de lo entregado")
        if opcion(args, "--seed") is None:
            malos.append("rl_ippo train sin --seed")
        if opcion(args, "--val-seeds") is None:
            malos.append("rl_ippo train sin --val-seeds")
        if opcion(args, "--csv") is not None:
            malos.append("--csv no se usa: el nombre lo da la etiqueta")
    if prog == "../evaluar.py" and uso in USOS_CIEGOS:
        malos.append("las tandas decisivas se evaluan con evaluar3.py (a ciegas)")
    salida = opcion(args, "--salida")
    if uso in USOS_CIEGOS and (salida is None or not salida.startswith("ciego/")):
        malos.append(f"uso '{uso}' debe escribir en ciego/: --salida {salida}")
    if uso == "final" and not existe(os.path.join(PLAN3, "listo", "holdout.ok")):
        malos.append("la prueba final exige listo/holdout.ok")
    for k, a in enumerate(args):
        if a.startswith("--") and k + 1 < len(args) and ("/" in args[k + 1] or "." in args[k + 1]):
            for v in args[k + 1].split(","):          # una opcion puede llevar varias rutas separadas por comas
                if os.path.isabs(v) or ":" in v:
                    malos.append(f"ruta absoluta en {a}: {v}")
                elif len(os.path.join(PLAN3, v)) > LARGO_MAX:
                    malos.append(f"ruta demasiado larga para Windows en {a}: {v}")
    return malos


# ---------------- Capa 2: lista de trabajos ----------------

def etiqueta_entreno(args):
    """Nombre de la corrida de rl_ippo train (como rl_ippo: <esc>_ippo_<variante>[_<etiqueta>]_s<base>)."""
    esc = opcion(args, "--escenario") or "corredor"
    var = opcion(args, "--variante") or "vecinos"
    et = opcion(args, "--etiqueta") or ""
    return f"{esc}_ippo_{var}{'_' + et if et else ''}_s{opcion(args, '--seed') or 42}"


def revisar_trabajos(trabajos):
    """trabajos = lista en orden del archivo (una linea posterior con el mismo id reemplaza a la anterior)."""
    malos = []
    ultimo = {}
    for t in trabajos:
        ultimo[t["id"]] = t
    duenos_salida, duenos_corrida = {}, {}
    for tid, t in ultimo.items():
        for m in revisar_comando(t, existe=lambda _: True):
            malos.append(f"{tid}: {m}")
        if not t.get("salidas"):
            malos.append(f"{tid}: no declara salidas (la cola no podria saber si termino)")
        for s in t.get("salidas", []):
            if s in duenos_salida:
                malos.append(f"{tid}: la salida {s} ya la declara {duenos_salida[s]}")
            duenos_salida.setdefault(s, tid)
        for r in t.get("requiere", []):
            if r.startswith("trabajo:") and r[len("trabajo:"):] not in ultimo:
                malos.append(f"{tid}: depende de un trabajo que no existe: {r}")
            elif not r.startswith("trabajo:") and (".." in r or os.path.isabs(r)):
                malos.append(f"{tid}: requisito fuera de plan3: {r}")
        try:
            prog, args = desenvolver(shlex.split(t.get("cmd", "")))
        except ValueError:
            continue
        if prog == "../rl_ippo.py" and args[:1] == ["train"]:
            corrida = etiqueta_entreno(args)
            cadena = t.get("cadena", tid)
            if corrida in duenos_corrida and duenos_corrida[corrida][1] != cadena:
                malos.append(f"{tid}: la corrida {corrida} ya la entrena {duenos_corrida[corrida][0]}")
            duenos_corrida.setdefault(corrida, (tid, cadena))
    estado = {}

    def visitar(tid, camino):
        if estado.get(tid) == 1:
            malos.append("ciclo de dependencias: " + " -> ".join(camino + [tid]))
            return
        if estado.get(tid) == 2 or tid not in ultimo:
            return
        estado[tid] = 1
        for r in ultimo[tid].get("requiere", []):
            if r.startswith("trabajo:"):
                visitar(r[len("trabajo:"):], camino + [tid])
        estado[tid] = 2
    for tid in ultimo:
        visitar(tid, [])
    return malos


# ---------------- Capa 3: git, archivos y versiones ----------------

def estado_git():
    malos = []
    _, rama = git("rev-parse", "--abbrev-ref", "HEAD")
    if rama.strip() != "plan3":
        malos.append(f"el worktree no esta en la rama plan3: {rama.strip()}")
    _, protegidos = git("status", "--porcelain", "--ignored", "--untracked-files=all", "--", "plan2", "TESIS")
    for linea in protegidos.splitlines():
        malos.append(f"plan2/TESIS tocados: {linea}")
    rc, dif = git("diff", "--stat", "main...HEAD", "--", "plan2", "TESIS")
    if rc != 0:
        malos.append("no se pudo comparar con main")
    elif dif.strip():
        malos.append("la rama cambia plan2/ o TESIS/ frente a main:\n" + dif)
    _, todo = git("status", "--porcelain", "--untracked-files=all")
    for linea in todo.splitlines():
        ruta = linea[3:].strip().strip('"')
        if not ruta.startswith("plan3/"):
            malos.append(f"archivo nuevo o cambiado fuera de plan3/: {linea}")
    return malos


def revisar_insumos():
    ruta = os.path.join(PLAN3, "insumos", "manifiesto.json")
    if not os.path.exists(ruta):
        return ["falta insumos/manifiesto.json (corre p3_insumos.py)"]
    esperado = json.load(open(ruta, encoding="utf-8"))
    malos = []
    for grupo, archivos in esperado.items():
        for rel, (_, h) in archivos.items():
            p = os.path.join(PLAN3, grupo, rel)
            if not os.path.exists(p):
                malos.append(f"falta el insumo {grupo}/{rel}")
            elif sha(p) != h:
                malos.append(f"el insumo {grupo}/{rel} cambio (alguien instalo o escribio encima)")
    return malos


def manifiesto_checkpoints():
    """{ruta relativa a checkpoints/: sha256} de todo lo que hay en plan3/checkpoints."""
    carpeta = os.path.join(PLAN3, "checkpoints")
    salida = {}
    for raiz, _, archivos in os.walk(carpeta):
        for a in archivos:
            p = os.path.join(raiz, a)
            salida[os.path.relpath(p, carpeta).replace(os.sep, "/")] = sha(p)
    return salida


def revisar_checkpoints():
    """Lo registrado la noche anterior sigue igual: un entrenamiento nuevo no piso uno viejo."""
    ruta = os.path.join(COLA, "manifiesto_checkpoints.json")
    if not os.path.exists(ruta):
        return []
    esperado = json.load(open(ruta, encoding="utf-8"))
    carpeta = os.path.join(PLAN3, "checkpoints")
    malos = []
    for rel, h in esperado.items():
        p = os.path.join(carpeta, rel)
        if not os.path.exists(p):
            malos.append(f"desaparecio el checkpoint {rel}")
        elif sha(p) != h:
            malos.append(f"cambio el checkpoint {rel}")
    return malos


def revisar_prerregistro():
    """El prerregistro existe, tiene su tabla y es igual al de origin/plan3 (subido antes de usarse)."""
    if not os.path.exists(PRERREGISTRO):
        return ["falta PRERREGISTRO.md"]
    malos = []
    try:
        tabla_prerregistro()
    except (ValueError, json.JSONDecodeError) as e:
        malos.append(f"tabla del prerregistro ilegible: {e}")
    git("fetch", "-q", "origin", "plan3")
    rc, remoto = git("show", "origin/plan3:plan3/PRERREGISTRO.md")
    if rc != 0:
        malos.append("el prerregistro no esta en origin/plan3 (falta el push de la parte A)")
    else:
        with open(PRERREGISTRO, encoding="utf-8") as f:
            local = f.read()
        if local.replace("\r\n", "\n") != remoto.replace("\r\n", "\n"):
            malos.append("el prerregistro local difiere del de origin/plan3")
    return malos


def versiones():
    import torch
    sumo = subprocess.run(["sumo", "--version"], capture_output=True, text=True).stdout.split("\n")[0].split()[-1]
    return {"python": sys.version.split()[0], "torch": torch.__version__, "sumo": sumo}


def revisar_versiones():
    v = versiones()
    return [f"version de {k}: {v[k]} (se esperaba {VERSIONES[k]})" for k in VERSIONES if v[k] != VERSIONES[k]]


def leer_trabajos():
    ruta = os.path.join(COLA, "trabajos.jsonl")
    if not os.path.exists(ruta):
        return []
    return [json.loads(l) for l in open(ruta, encoding="utf-8") if l.strip()]


def main():
    momento = sys.argv[1] if len(sys.argv) > 1 else "antes"
    if momento == "comando":
        uso = sys.argv[sys.argv.index("--uso") + 1] if "--uso" in sys.argv else ""
        malos = revisar_comando({"id": "prueba", "cmd": sys.argv[2], "uso": uso})
        print("\n".join(malos) if malos else "ACEPTADO")
        sys.exit(1 if malos else 0)
    informe = {"momento": momento, "hora": time.strftime("%Y-%m-%d %H:%M:%S"),
               "commit": git("rev-parse", "HEAD")[1].strip()}
    problemas = estado_git() + revisar_insumos() + revisar_checkpoints() + revisar_versiones()
    if momento == "antes":
        problemas += revisar_prerregistro()
        problemas += revisar_trabajos(leer_trabajos())
        libre = __import__("shutil").disk_usage(PLAN3).free / 2 ** 30
        informe["disco_libre_gb"] = round(libre, 1)
        if libre < 20:
            problemas.append(f"quedan {libre:.1f} GB libres; hacen falta 20")
    else:
        ruta_e = os.path.join(COLA, "estado.json")
        if os.path.exists(ruta_e):
            e = json.load(open(ruta_e, encoding="utf-8"))
            informe["fallidos"] = e.get("fallidos", {})
            informe["hechos"] = len(e.get("hechos", []))
    informe["versiones"] = versiones()
    informe["problemas"] = problemas
    os.makedirs(COLA, exist_ok=True)
    salida = os.path.join(COLA, f"control_{time.strftime('%Y%m%d_%H%M%S')}_{momento}.json")
    with open(salida, "w", encoding="utf-8") as f:
        json.dump(informe, f, indent=1, ensure_ascii=False)
    for p in problemas:
        print("PROBLEMA:", p)
    print(f"{momento}: {len(problemas)} problemas ({os.path.relpath(salida, PLAN3)})")
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
