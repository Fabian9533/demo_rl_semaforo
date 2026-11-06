"""
anclaje.py - La historia de git del bloque plan3, anclada a la rama empujada (tercera revision del 05.11).

La usan veredicto3.py (--final, --prueba-final y los preflight), manifiesto.py (cierre) y protecciones.py (antes y
despues de cada noche: asi refs/veredicto3/visto existe desde la primera noche). Importarlo no escribe ni llama a git.

Reglas:
  - git corre con un entorno limpio: sin GIT_DIR, GIT_WORK_TREE, GIT_CONFIG_*, GIT_*_PATHSPECS ni ninguna otra GIT_*
    que cambie de repositorio o de configuracion; sin objetos de reemplazo (GIT_NO_REPLACE_OBJECTS=1); sin preguntar
    credenciales (GIT_TERMINAL_PROMPT=0, GCM_INTERACTIVE=never); con un tiempo maximo. Sin red: un mensaje claro.
  - El ancla es refs/heads/plan3 del origin, traida con un fetch explicito a refs/veredicto3/traida (ni FETCH_HEAD ni
    una rama local). El origin tiene que ser el que dice PLAN3.md §5; el remoto no puede tener otra referencia que git
    confunda con la rama (un tag 'plan3', refs/plan3...); el tag del prerregistro local tiene que ser el del remoto.
  - Un repositorio superficial (shallow) se niega.
  - Push forzado: cada valor que este repositorio vio de la rama empujada (el reflog de refs/remotes/origin/plan3, que
    mueven los push y los fetch, y refs/veredicto3/visto, lo ultimo traido y aceptado) que ya tenia datos decisivos
    (una manana con algun CSV de ciego/) tiene que ser ancestro del ancla. Lo de antes de la primera manana con datos
    no cuenta: la rama se pudo rehacer antes. Un amend o un rebase local que nunca se empujo no esta en esos valores:
    se corrige sin consecuencias.
  - La historia de un archivo se lee desde el ancla (no desde HEAD), con rev-list --full-history; un merge cuyo
    contenido de los archivos que se miran es el de alguno de sus padres no cuenta como version nueva: un merge de
    codigo (plan3-dev -> plan3, plan3 -> otra rama y de vuelta) es transparente.
"""
import os
import re
import json
import subprocess

PLAN3 = os.path.dirname(os.path.abspath(__file__))
REMOTO, RAMA = "origin", "plan3"
REF_RAMA = f"refs/heads/{RAMA}"
REF_SEGUIMIENTO = f"refs/remotes/{REMOTO}/{RAMA}"
TRAIDA = "refs/veredicto3/traida"           # lo que trajo el ultimo fetch explicito (aceptado o no)
VISTO = "refs/veredicto3/visto"             # lo ultimo traido que se acepto; git push no sube refs/veredicto3/*
TAG = "plan3-prerregistro-A"
# referencias del remoto que git podria tomar por la rama 'plan3' (precedencia de nombres de git)
AMBIGUAS = ("refs/plan3", "refs/tags/plan3", "refs/remotes/plan3", "refs/remotes/plan3/HEAD")
MANANA = "cola/manifiesto_ciego.json"
ESPERA_RED = 90                             # s para fetch y ls-remote
ESPERA = 300                                # s para el resto
# variables de git que se dejan (autenticacion, rastreo); toda otra GIT_* se quita
DEJAR = {"GIT_SSH", "GIT_SSH_COMMAND", "GIT_SSH_VARIANT", "GIT_ASKPASS", "GIT_EXEC_PATH", "GIT_TRACE",
         "GIT_TRACE_PACKET", "GIT_CURL_VERBOSE", "GIT_HTTP_PROXY_AUTHMETHOD"}
LINEA_URL = re.compile(r"El `origin` de la rama `plan3` es `([^`]+)`")


class ErrorAncla(Exception):
    """Algo de la historia no es el de la rama empujada; el mensaje dice que."""


class SinRed(ErrorAncla):
    """No se pudo hablar con el origin (sin red, sin credenciales o sin respuesta)."""


def entorno():
    e = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") or k in DEJAR}
    e.update(GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    return e


def git(*args, cwd, espera=ESPERA):
    """(rc, stdout en bytes, stderr) de git con el entorno limpio, rutas largas y sin locks opcionales; rc 124 si no
    responde a tiempo."""
    try:
        r = subprocess.run(["git", "-c", "core.longpaths=true", "--no-optional-locks", *args], cwd=cwd,
                           capture_output=True, env=entorno(), timeout=espera)
    except subprocess.TimeoutExpired:
        return 124, b"", f"git {args[0]} no respondio en {espera} s"
    return r.returncode, r.stdout, r.stderr.decode("utf-8", "replace")


def url_normal(u):
    """Una URL de GitHub (https o ssh, con o sin .git) como github.com/<duenio>/<repo>; una ruta local, absoluta y en
    la caja del sistema."""
    u = (u or "").strip()
    m = re.match(r"^(?:https?://(?:[^@/]+@)?|ssh://git@|git@)github\.com[:/](.+?)(?:\.git)?/?$", u, re.IGNORECASE)
    if m:
        return "github.com/" + m.group(1).lower()
    if u.startswith("file://"):
        u = u[len("file://"):]
        if re.match(r"^/[A-Za-z]:", u):
            u = u[1:]
    return os.path.normcase(os.path.abspath(u))


def url_del_plan(carpeta=PLAN3):
    """La URL del origin que fija PLAN3.md §5 ('El `origin` de la rama `plan3` es `...`'), o None."""
    ruta = os.path.join(carpeta, "doc", "PLAN3.md")
    if not os.path.exists(ruta):
        return None
    with open(ruta, encoding="utf-8-sig") as f:
        m = LINEA_URL.search(f.read())
    return m.group(1) if m else None


def decisivo(texto):
    """Una version del manifiesto de la manana con algun CSV de ciego/ (ya hay datos decisivos)."""
    if texto is None:
        return False
    try:
        datos = json.loads(texto.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError):
        return True                         # ilegible: se trata como decisiva (falla cerrado)
    return isinstance(datos, dict) and any(str(k).startswith("ciego/") for k in datos)


class Historial:
    """La historia de git de una carpeta plan3 leida desde un commit (por defecto HEAD), sin red: la usan
    manifiesto.py cierre (antes del commit del cierre) y Ancla. Lee con rev-list --full-history y cat-file; un merge
    que no trae una version nueva de lo que se mira no cuenta; una lectura que falla es un ERROR, no un borrado."""

    Error, Red = ErrorAncla, SinRed

    def __init__(self, raiz, desde="HEAD"):
        self.raiz = raiz
        self._ancestro, self._padres, self._igual = {}, {}, {}
        rc, top, err = git("rev-parse", "--show-toplevel", cwd=raiz)
        if rc != 0:
            raise self.Error(f"{raiz} no está en un repositorio git ({err.strip()[:120]}); no se corre")
        self.top = top.decode().strip()
        self.prefijo = git("rev-parse", "--show-prefix", cwd=raiz)[1].decode().strip()
        self.head = self.rev("HEAD")
        self.ancla = self.rev(desde) if desde else None
        self.nombre_ancla = desde

    # --- lecturas ---
    def rev(self, nombre):
        """El commit de nombre (una referencia), o None si no existe."""
        rc, out, _ = git("rev-parse", "--verify", "--quiet", f"{nombre}^{{commit}}", cwd=self.raiz)
        return out.decode().strip() if rc == 0 else None

    def reflog(self, ref):
        """Los valores del reflog de ref (del mas nuevo al mas viejo), o None si ref o su reflog no existen."""
        if self.rev(ref) is None:
            return None
        rc, out, _ = git("reflog", "show", "--format=%H", ref, "--", cwd=self.raiz)
        valores = out.decode().split() if rc == 0 else []
        return valores or None

    def padres(self, cs):
        faltan = [c for c in cs if c not in self._padres]
        for k in range(0, len(faltan), 200):
            rc, out, err = git("log", "--no-walk=unsorted", "--format=%H %P", *faltan[k:k + 200], "--",
                               cwd=self.top)
            if rc != 0:
                raise self.Error(f"no se pudo leer la historia de git: {err.strip()[:160]}")
            for linea in out.decode().splitlines():
                c, *ps = linea.split()
                self._padres[c] = ps
        return {c: self._padres[c] for c in cs}

    def igual_en(self, a, b, rutas):
        """El contenido de rutas es el mismo en los commits a y b."""
        clave = (a, b, rutas)
        if clave not in self._igual:
            rc, _, err = git("diff-tree", "-r", "--quiet", a, b, "--", *rutas, cwd=self.top)
            if rc not in (0, 1):
                raise self.Error(f"git diff-tree falló con {a[:10]} y {b[:10]}: {err.strip()[:160]}")
            self._igual[clave] = rc == 0
        return self._igual[clave]

    def commits(self, *rels, desde=None):
        """Los commits que cambian alguno de rels, del mas viejo al mas nuevo, en toda la historia del ancla (o de
        desde). Un merge cuyo contenido de rels es el de alguno de sus padres no cuenta (no trae una version nueva)."""
        rutas = tuple(self.prefijo + r for r in rels)
        rc, out, err = git("rev-list", "--full-history", "--topo-order", "--reverse", desde or self.ancla, "--",
                           *rutas, cwd=self.top)
        if rc != 0:
            raise self.Error(f"no se pudo leer la historia de git de {', '.join(rels)}: {err.strip()[:160]}")
        cs = out.decode().split()
        padres = self.padres(cs)
        return [c for c in cs if len(padres[c]) < 2 or not any(self.igual_en(p, c, rutas) for p in padres[c])]

    def cambios_por_archivo(self, patron, desde=None):
        """{ruta relativa a plan3/: [commits que la cambian, del mas nuevo al mas viejo]} de los archivos que calzan con
        patron (relativo a plan3/), en toda la historia del ancla; los merges no cuentan (git log no les lista
        archivos)."""
        rc, out, err = git("log", "--full-history", "--format=%x00%H", "--name-only", desde or self.ancla, "--",
                           self.prefijo + patron, cwd=self.top)
        if rc != 0:
            raise self.Error(f"no se pudo leer la historia de git de {patron}: {err.strip()[:160]}")
        salida = {}
        for bloque in out.decode("utf-8", "replace").split("\x00")[1:]:
            lineas = [x for x in bloque.splitlines() if x.strip()]
            if not lineas:
                continue
            for ruta in lineas[1:]:
                if ruta.startswith(self.prefijo):
                    salida.setdefault(ruta[len(self.prefijo):], []).append(lineas[0])
        return salida

    def en_algun_lado(self, rel):
        """Algun commit de cualquier rama, tag o reflog de este repositorio cambia rel."""
        rc, out, err = git("rev-list", "--all", "--reflog", "--full-history", "--", self.prefijo + rel, cwd=self.top)
        if rc != 0:
            raise self.Error(f"no se pudo leer la historia de git de {rel}: {err.strip()[:160]}")
        return bool(out.strip())

    def leer(self, c, rel, faltante_ok=False):
        """El contenido (bytes) de rel en el commit c, o None si no esta en ese commit. Otra falla: ERROR (o None con
        faltante_ok, si el commit mismo falta)."""
        ruta = self.prefijo + rel
        rc, out, err = git("cat-file", "-p", f"{c}:{ruta}", cwd=self.raiz)
        if rc == 0:
            return out
        rc2, ls, err2 = git("ls-tree", c, "--", ruta, cwd=self.top)
        if rc2 == 0 and not ls.strip():
            return None
        if faltante_ok and git("cat-file", "-e", f"{c}^{{commit}}", cwd=self.raiz)[0] != 0:
            return None
        raise self.Error(f"no se pudo leer {rel} en el commit {c[:10]}: {(err or err2).strip()[:160]}")

    def es_ancestro(self, a, b):
        """a es ancestro de b o el mismo commit (un commit que no existe aqui no es ancestro)."""
        if (a, b) not in self._ancestro:
            rc, _, err = git("merge-base", "--is-ancestor", a, b, cwd=self.raiz)
            if rc not in (0, 1) and git("cat-file", "-e", f"{a}^{{commit}}", cwd=self.raiz)[0] == 0:
                raise self.Error(f"git merge-base falló con {a[:10]} y {b[:10]}: {err.strip()[:160]}")
            self._ancestro[(a, b)] = rc == 0
        return self._ancestro[(a, b)]

    def anclado(self, c):
        return self.es_ancestro(c, self.ancla)

    def versiones(self, rel):
        """[(commit, bytes)] de cada version de rel en la historia del ancla; ERROR si un commit lo borra."""
        salida = []
        for c in self.commits(rel):
            contenido = self.leer(c, rel)
            if contenido is None:
                raise self.Error(f"{rel} se borró en el commit {c[:10]}; no se corre")
            salida.append((c, contenido))
        return salida

    def cadena(self, *rels):
        """Los commits que cambian rels forman una sola cadena de ascendencia (cada uno es ancestro del siguiente): una
        version en una rama lateral no entra. Si no, ERROR."""
        cs = self.commits(*rels)
        for a, b in zip(cs, cs[1:]):
            if not self.es_ancestro(a, b):
                raise self.Error(f"los commits de {', '.join(rels)} no forman una sola cadena ({a[:10]} y {b[:10]} "
                                 f"están en ramas distintas); no se corre")
        return cs

    def asunto(self, c):
        """La primera linea del mensaje del commit c."""
        rc, out, _ = git("log", "-1", "--format=%s", c, "--", cwd=self.top)
        return out.decode("utf-8", "replace").strip() if rc == 0 else ""

    def fecha(self, c):
        """Hora del commit c (committer, segundos desde 1970)."""
        rc, out, _ = git("log", "-1", "--format=%ct", c, "--", cwd=self.top)
        return int(out.decode().strip()) if rc == 0 and out.strip() else None

    def protegido_cambiado(self, rels):
        """Las rutas de rels (archivos o carpetas, relativas a plan3/) cuyo contenido en el disco (lo commiteado o no)
        no es el del ancla; y si HEAD y el ancla no estan en la misma linea, un motivo."""
        motivos = []
        if not (self.es_ancestro(self.ancla, self.head) or self.es_ancestro(self.head, self.ancla)):
            motivos.append(f"HEAD ({self.head[:10]}) no está en la línea de {self.nombre_ancla}")
        rc, out, err = git("diff", "--name-only", self.ancla, "--", *[self.prefijo + r for r in rels], cwd=self.top)
        if rc != 0:
            raise self.Error(f"git diff falló: {err.strip()[:160]}")
        motivos += [x for x in out.decode().splitlines() if x.strip()]
        return motivos


class Ancla(Historial):
    """La historia de una carpeta plan3 anclada a la rama empujada (ver el docstring del modulo).
    traer=False: sin fetch (el ancla es refs/remotes/origin/plan3; solo para pruebas). url: 'plan' (la de PLAN3.md),
    None (no se coteja; mundos de prueba) o una URL. en_head=True (preflight antes de un push): el ancla es HEAD, y lo
    que hay en el remoto tiene que ser ancestro de HEAD (el push sera rapido, sin forzar). nocturna=True
    (protecciones): sin la linea de la URL en PLAN3.md no se coteja. guardar=True: si todo cuadra, VISTO = lo traido
    del remoto. Sin el reflog de refs/remotes/origin/plan3 (un clon nuevo) no hay con que comparar: es el limite
    declarado en PLAN3 §5."""

    def __init__(self, raiz, traer=True, url="plan", en_head=False, nocturna=False, guardar=True, tag=TAG):
        super().__init__(raiz, desde=None)
        rc, sup, _ = git("rev-parse", "--is-shallow-repository", cwd=raiz)
        if rc != 0 or sup.decode().strip() != "false":
            raise self.Error("el repositorio es superficial (shallow): su historia no está completa; no se corre")
        self.comprobar_url(url, nocturna)
        vistos = [(VISTO, v) for v in [self.rev(VISTO)] if v]
        if traer:
            self.comprobar_remoto(tag)
            rc, _, err = git("fetch", "--quiet", "--no-tags", "--no-write-fetch-head", "--refmap=", REMOTO,
                             f"+{REF_RAMA}:{TRAIDA}", cwd=raiz, espera=ESPERA_RED)
            if rc != 0:
                raise self.Red(f"no se pudo traer {REMOTO}/{RAMA} (sin red, sin acceso o sin respuesta: "
                               f"{err.strip()[:160]}); no se corre")
        self.remoto = self.rev(TRAIDA if traer else REF_SEGUIMIENTO)
        if self.remoto is None:
            raise self.Error(f"no hay {REMOTO}/{RAMA} traída: la historia tiene que estar empujada; no se corre")
        self.en_head = en_head
        if en_head:
            if not self.es_ancestro(self.remoto, self.head):
                raise self.Error(f"{REMOTO}/{RAMA} ({self.remoto[:10]}) no es ancestro de HEAD: el push no sería "
                                 f"rápido (git pull primero, sin rebase); no se corre")
            self.ancla, self.nombre_ancla = self.head, "HEAD (antes del push)"
        else:
            self.ancla, self.nombre_ancla = self.remoto, f"{REMOTO}/{RAMA}"
        reflog = self.reflog(REF_SEGUIMIENTO)          # un clon nuevo no tiene: no vio nada antes (limite declarado)
        revisados = set()
        for nombre, v in vistos + [(f"el reflog de {REF_SEGUIMIENTO}", v) for v in (reflog or [])]:
            if v in revisados:
                continue
            revisados.add(v)
            if not self.es_ancestro(v, self.ancla) and decisivo(self.leer(v, MANANA, faltante_ok=True)):
                raise self.Error(f"{REMOTO}/{RAMA} se reescribió (push forzado): {v[:10]} ({nombre}) ya tenía datos "
                                 f"decisivos y no está en la rama empujada; no se corre")
        if traer and guardar and git("update-ref", VISTO, self.remoto, cwd=raiz)[0] != 0:
            raise self.Error(f"no se pudo guardar {VISTO}; no se corre")

    def comprobar_url(self, url, nocturna):
        if url is None:
            return
        esperada = url_del_plan() if url == "plan" else url
        if esperada is None:
            if nocturna:
                return
            raise self.Error("PLAN3.md §5 no dice el origin de la rama plan3 ('El `origin` de la rama `plan3` es "
                             "`...`'); no se corre")
        rc, real, err = git("remote", "get-url", REMOTO, cwd=self.raiz)
        if rc != 0:
            raise self.Error(f"no hay remoto {REMOTO} ({err.strip()[:120]}); no se corre")
        if url_normal(real.decode()) != url_normal(esperada):
            raise self.Error(f"el {REMOTO} de este repositorio ({real.decode().strip()}) no es el del plan "
                             f"({esperada}); no se corre")

    def comprobar_remoto(self, tag):
        """El remoto tiene refs/heads/plan3 y ninguna referencia que git confunda con ella; su tag del prerregistro es
        el local."""
        rc, out, err = git("ls-remote", REMOTO, cwd=self.raiz, espera=ESPERA_RED)
        if rc != 0:
            raise self.Red(f"no se pudo leer {REMOTO} (sin red, sin acceso o sin respuesta: {err.strip()[:160]}); "
                           f"no se corre")
        refs = {}
        for linea in out.decode().splitlines():
            if "\t" in linea:
                sha, nombre = linea.split("\t", 1)
                refs[nombre.strip()] = sha.strip()
        if REF_RAMA not in refs:
            raise self.Error(f"{REMOTO} no tiene la rama {RAMA}; no se corre")
        ambiguas = sorted(r for r in refs if r in AMBIGUAS)
        if ambiguas:
            raise self.Error(f"{REMOTO} tiene {', '.join(ambiguas)}, que git puede confundir con la rama {RAMA}: hay "
                             f"que borrarlo (y prohibirlo en GitHub); no se corre")
        if tag:
            local = self.rev(f"refs/tags/{tag}")
            remoto = refs.get(f"refs/tags/{tag}^{{}}") or refs.get(f"refs/tags/{tag}")
            if local and remoto and local != remoto:
                raise self.Error(f"el tag {tag} local ({local[:10]}) no es el de {REMOTO} ({remoto[:10]}); no se corre")
            if local and not remoto:
                raise self.Error(f"el tag {tag} no está en {REMOTO} (git push {REMOTO} {tag}); no se corre")
