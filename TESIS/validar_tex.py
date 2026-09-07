r"""validar_tex.py - Revisa los .tex de la tesis sin necesidad de compilar LaTeX.

Uso:  python validar_tex.py [carpeta]   (por defecto, la carpeta donde esta este script)

Comprueba, en main.tex y en todos los archivos que incluye:
  ERRORES (codigo de salida 1)
  - llaves { } balanceadas y entornos \begin{x} ... \end{x} bien anidados
  - cada \ref / \autoref apunta a un \label existente; no hay labels repetidos
  - cada clave de \cite / \citep / \citet existe en referencias.bib
  - cada \includegraphics existe en images/ con el nombre EXACTO (Overleaf es Linux:
    distingue mayusculas; en Windows el error no se nota)
  - cada \input / \include existe; los archivos son UTF-8
  - caracteres que pdflatex no acepta en texto (>=, ~, ->, letras griegas...): van
    en modo matematico o como comando
  - espacio fino antes de \% dentro de math ($25\,\%$): babel-spanish rompe con
    "Incompatible glue units"; el signo va fuera del math ($25$\,\%)
  - caracteres ASCII con significado propio usados como texto: _ # ^ fuera de modo
    matematico y & fuera de una tabla (el guion bajo de corredor_alta en los captions
    rompio la compilacion en Overleaf el 06.09.2026: abre modo matematico y arrastra
    el resto del caption, y ademas revienta al releer la lista de tablas del .lot)
  - entorno subfigure (la clase carga el paquete antiguo subfigure, que solo define
    el comando \subfigure) y paquetes incompatibles con la clase en main.tex
  - table/figure sin \caption, o con \label antes de \caption (referencia mal numerada)
  AVISOS
  - secciones/ fuera de main.tex o vacias; \paragraph{} (entra al indice);
    % sin escapar tras un numero (corta la linea); comentarios TODO/PROVISIONAL;
    table/figure sin \label
"""
import os
import re
import sys
import glob

RAIZ = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(RAIZ, "main.tex")
BIB = os.path.join(RAIZ, "referencias.bib")
IMAGENES = os.path.join(RAIZ, "images")
EXT_IMG = ["", ".png", ".PNG", ".jpg", ".JPG", ".jpeg", ".JPEG", ".pdf", ".PDF", ".eps"]

# Fuera de ASCII, pdflatex con inputenc utf8 acepta el bloque Latin-1 (tildes, n con
# virgulilla, signos de apertura, grados, mas/menos) y esta puntuacion tipografica.
# Cualquier otro simbolo (>=, <=, ~, flechas, griegas, menos unicode) rompe el PDF.
PERMITIDOS = set(chr(c) for c in range(0xA0, 0x100)) | set("–—‘’“”…‚„‹›•‰€")

errores = []
avisos = []

# Una sola pasada de izquierda a derecha: asi un % dentro de verbatim o de \verb no es
# comentario, y un \begin{verbatim} dentro de un comentario no abre nada.
LITERALES = (
    r"\\begin\{(verbatim|lstlisting|comment)\}[\s\S]*?\\end\{\1\}"   # entornos literales
    r"|\\verb\*?(?![A-Za-z])(.)(?:(?!\2)[^\n])*\2"                    # \verb|...| y \verb*|...| (no \verbatiminput)
    r"|\\(?:url|href|path)\{[^}\n]*\}"                                # \url{...} admite % dentro
    r"|\\[\\%{}]"                                                     # \\  \%  \{  \}  (se conservan)
)
PATRON_LIMPIEZA = re.compile(LITERALES + r"|%[^\n]*")                 # ... y comentarios
PATRON_SIN_COMENTARIOS = re.compile(LITERALES)                        # conserva comentarios


def _reemplazo(m):
    s = m.group(0)
    if len(s) == 2 and s[0] == "\\":
        return s                              # \\ \% \{ \} se dejan tal cual
    if s.startswith(("\\url", "\\href", "\\path")):
        return s.split("{", 1)[0] + "{}"      # llaves balanceadas y sin % dentro
    return "\n" * s.count("\n")               # conserva el numero de lineas


def quitar_comentarios(texto):
    """Quita comentarios, verbatim, \\verb y el interior de \\url, conservando saltos de linea."""
    return PATRON_LIMPIEZA.sub(_reemplazo, texto)


def quitar_literales(texto):
    """Quita verbatim, \\verb y \\url pero deja los comentarios (para revisar % y TODO)."""
    return PATRON_SIN_COMENTARIOS.sub(_reemplazo, texto)


def leer(archivo):
    """Lee un .tex en UTF-8 (sin BOM). Si no es UTF-8 lo reporta como error y devuelve ''."""
    try:
        with open(archivo, encoding="utf-8-sig") as f:
            return f.read()
    except UnicodeDecodeError as e:
        errores.append(f"{os.path.relpath(archivo, RAIZ)}: no es UTF-8 (byte {e.object[e.start]:#x} "
                       f"en posicion {e.start}); guardarlo como UTF-8")
        return ""


def linea_de(texto, pos):
    return texto.count("\n", 0, pos) + 1


def archivos_incluidos(archivo, vistos=None):
    """Sigue \\input y \\include recursivamente desde main.tex.
    Devuelve {ruta: texto crudo} en orden de inclusion (None si no existe)."""
    if vistos is None:
        vistos = {}
    archivo = os.path.normpath(archivo)
    if os.path.normcase(archivo) in {os.path.normcase(v) for v in vistos}:
        return vistos                     # mismo archivo escrito de otra forma (./x.tex, x)
    if not os.path.exists(archivo):
        errores.append(f"{os.path.relpath(archivo, RAIZ)}: archivo incluido no existe")
        vistos[archivo] = None
        return vistos
    crudo = leer(archivo)
    vistos[archivo] = crudo
    for m in re.finditer(r"\\(?:input|include)\{([^}]+)\}", quitar_comentarios(crudo)):
        ruta = m.group(1).strip()
        if not ruta.endswith(".tex"):
            ruta += ".tex"
        archivos_incluidos(os.path.join(RAIZ, ruta), vistos)
    return vistos


def revisar_llaves_y_entornos(nombre, texto):
    limpio = re.sub(r"\\[\\{}]", "", texto)     # ignorar \{ y \}; consumir \\ para que \\} no se lea como \}
    prof = 0
    abiertas = []
    for i, linea in enumerate(limpio.splitlines(), 1):
        for c in linea:
            if c == "{":
                prof += 1
                abiertas.append(i)
            elif c == "}":
                prof -= 1
                if abiertas:
                    abiertas.pop()
                if prof < 0:
                    errores.append(f"{nombre}:{i}: llave de cierre sin apertura")
                    prof = 0
    if prof > 0:
        errores.append(f"{nombre}:{abiertas[-1]}: llave abierta sin cerrar (quedan {prof})")

    pila = []
    for m in re.finditer(r"\\(begin|end)\{([^}]+)\}", texto):
        tipo, env = m.group(1), m.group(2)
        linea = linea_de(texto, m.start())
        if tipo == "begin":
            pila.append((env, linea))
            if env == "subfigure":
                errores.append(f"{nombre}:{linea}: entorno subfigure no disponible en esta plantilla "
                               f"(usar \\subfigure[caption]{{...}} o dos figuras separadas)")
        elif not pila:
            errores.append(f"{nombre}:{linea}: \\end{{{env}}} sin \\begin")
        elif pila[-1][0] != env:
            errores.append(f"{nombre}:{linea}: \\end{{{env}}} pero el entorno abierto es "
                           f"{pila[-1][0]} (linea {pila[-1][1]})")
            pila.pop()
        else:
            pila.pop()
    for env, linea in pila:
        errores.append(f"{nombre}:{linea}: \\begin{{{env}}} sin cerrar")


def revisar_flotantes(nombre, texto):
    """Cada table/figure debe tener \\caption (error) y \\label (aviso), y el label despues del caption."""
    for m in re.finditer(r"\\begin\{(table|figure)\}([\s\S]*?)\\end\{\1\}", texto):
        cuerpo = m.group(2)
        linea = linea_de(texto, m.start())
        cap = cuerpo.find("\\caption")
        lab = cuerpo.find("\\label")
        if cap < 0:
            errores.append(f"{nombre}:{linea}: {m.group(1)} sin \\caption")
        if lab < 0:
            avisos.append(f"{nombre}:{linea}: {m.group(1)} sin \\label (no se puede referenciar)")
        elif cap >= 0 and lab < cap:
            errores.append(f"{nombre}:{linea}: \\label antes de \\caption en {m.group(1)} "
                           f"(la referencia tomara el numero de la seccion, no del flotante)")


def revisar_caracteres(nombre, texto):
    for m in re.finditer(r"[^\x00-\x7f]", texto):
        c = m.group(0)
        if c not in PERMITIDOS:
            errores.append(f"{nombre}:{linea_de(texto, m.start())}: caracter '{c}' (U+{ord(c):04X}) no lo "
                           f"acepta pdflatex en texto; usar $\\geq$, $\\approx$, $\\varepsilon$, "
                           f"\\textrightarrow, etc.")


MATH_ENTORNOS = ("equation", "align", "gather", "multline", "eqnarray", "displaymath", "math",
                 "array", "cases", "split", "aligned", "alignat", "flalign", "gathered",
                 "pmatrix", "bmatrix", "vmatrix", "Vmatrix", "smallmatrix", "matrix")
TABLA_ENTORNOS = ("tabular", "tabularx", "tabulary", "longtable", "array", "matrix", "pmatrix",
                  "bmatrix", "vmatrix", "Vmatrix", "smallmatrix", "align", "alignat", "flalign",
                  "eqnarray", "cases", "split", "aligned", "gathered")
# argumentos que LaTeX no tipografia: son claves o nombres de archivo y el guion bajo es legal
ARG_NO_TEXTO = ("label", "ref", "eqref", "pageref", "autoref", "nameref", "vref", "Cref", "cref",
                "cite", "citep", "citet", "citealp", "citealt", "input", "include", "includegraphics",
                "bibliography", "bibliographystyle", "url", "href", "path", "verbatiminput",
                "lstinputlisting", "graphicspath", "bibitem", "usepackage", "documentclass")


def _borrar(texto, patron, flags=0):
    """Sustituye por espacios lo que empareje, conservando posiciones y saltos de linea."""
    return re.sub(patron, lambda m: re.sub(r"[^\n]", " ", m.group(0)), texto, flags=flags)


def sin_matematicas(texto, quitar_tablas=False):
    """Texto con las zonas donde _ ^ & son legales sustituidas por espacios."""
    t = _borrar(texto, r"\\[\\$_#&%^~{}]")                       # \_ \& \$ \\ ... ya escapados
    envs = MATH_ENTORNOS + (TABLA_ENTORNOS if quitar_tablas else ())
    for env in sorted(set(envs)):
        t = _borrar(t, r"\\begin\{" + env + r"\*?\}[\s\S]*?\\end\{" + env + r"\*?\}")
    t = _borrar(t, r"\$\$[\s\S]*?\$\$")
    t = _borrar(t, r"\$[^$]*?\$")                                # $...$ puede abarcar varias lineas
    t = _borrar(t, r"\\\[[\s\S]*?\\\]")
    t = _borrar(t, r"\\\([\s\S]*?\\\)")
    for cmd in ARG_NO_TEXTO:
        t = _borrar(t, r"\\" + cmd + r"\*?(?![A-Za-z])(\[[^\]]*\])?\{[^{}]*\}")
    return t


def revisar_especiales(nombre, texto):
    """Caracteres ASCII con significado propio en LaTeX usados como texto.

    Es el fallo que rompio la compilacion en Overleaf el 06.09.2026: los captions de
    las tablas de corredor_alta llevaban el guion bajo crudo, que abre modo matematico
    y arrastra el resto del caption (y de paso rompe la lista de tablas, que se relee
    desde el .lot antes que el propio capitulo).
    """
    t = sin_matematicas(texto)
    for simbolo, arreglo in (("_", "\\_"), ("#", "\\#"), ("^", "\\^{}")):
        for m in re.finditer(r"(?<!\\)" + re.escape(simbolo), t):
            errores.append(f"{nombre}:{linea_de(t, m.start())}: '{simbolo}' sin escapar en texto "
                           f"(escribir {arreglo}); LaTeX lo lee como subindice/superindice y falla "
                           f"con 'Missing $ inserted'")
    # & fuera de tabular: 'Misplaced alignment tab character &'
    t = sin_matematicas(texto, quitar_tablas=True)
    for m in re.finditer(r"(?<!\\)&", t):
        errores.append(f"{nombre}:{linea_de(t, m.start())}: '&' fuera de una tabla "
                       f"(escribir \\&); LaTeX falla con 'Misplaced alignment tab character'")


def zonas_matematicas(texto):
    """Lista de booleanos por posicion: True si esa posicion queda dentro de math."""
    dentro = [False] * len(texto)
    i = 0
    inline = display = False
    while i < len(texto):
        c = texto[i]
        if c == "\\":
            if texto[i:i + 2] == "\\[":
                display = True
                i += 2
                continue
            if texto[i:i + 2] == "\\]":
                display = False
                i += 2
                continue
            if i + 1 < len(texto):
                dentro[i] = dentro[i + 1] = inline or display
            i += 2
            continue
        if c == "$":
            if texto[i:i + 2] == "$$":
                display = not display
                i += 2
                continue
            inline = not inline
            i += 1
            continue
        dentro[i] = inline or display
        i += 1
    for env in ("equation", "align", "gather", "multline", "eqnarray", "displaymath"):
        for m in re.finditer(r"\\begin\{" + env + r"\*?\}[\s\S]*?\\end\{" + env + r"\*?\}", texto):
            for k in range(m.start(), m.end()):
                dentro[k] = True
    return dentro


def revisar_porcentaje_en_math(nombre, texto):
    """Espacio fino antes de \\% dentro de modo matematico: rompe con babel-spanish.

    babel-spanish redefine \\% para anteponer el espacio fino de la norma tipografica
    ("25 %"), y antes de ponerlo mira \\lastskip. Dentro de $...$ el \\, es un \\mskip en
    unidades mu y compararlo con 0pt da "! Incompatible glue units", que ademas deja el
    espacio mal (TeX asume 1mu=1pt). Se escribe $25$\\,\\%, con el % fuera del math.
    """
    dentro = zonas_matematicas(texto)
    for m in re.finditer(r"\\[,;:! ]\s*\\%", texto):
        if dentro[m.start()]:
            errores.append(f"{nombre}:{linea_de(texto, m.start())}: espacio fino antes de \\% "
                           f"dentro de modo matematico (escribir $25$\\,\\% y no $25\\,\\%$); "
                           f"babel-spanish falla con 'Incompatible glue units'")


def revisar_avisos_texto(nombre, crudo):
    """Sobre el texto con comentarios: % sin escapar tras un numero, TODO/PROVISIONAL, \\paragraph."""
    t = quitar_literales(crudo)
    for i, linea in enumerate(t.splitlines(), 1):
        m = re.search(r"(?<!\\)%", linea)          # primer % real de la linea: ahi empieza el comentario
        if m and re.search(r"\d\s*$", linea[:m.start()]):
            avisos.append(f"{nombre}:{i}: porcentaje sin escapar tras un numero "
                          f"(escribir \\%; el resto de la linea se pierde como comentario)")
    for m in re.finditer(r"%\s*(TODO|PROVISIONAL|PENDIENTE|FIXME)\b", t):
        avisos.append(f"{nombre}:{linea_de(t, m.start())}: comentario {m.group(1)} pendiente")
    limpio = quitar_comentarios(crudo)
    for m in re.finditer(r"\\paragraph\{", limpio):
        avisos.append(f"{nombre}:{linea_de(limpio, m.start())}: \\paragraph{{}} entra al indice "
                      f"(tocdepth=6); usar \\noindent\\textbf{{Titulo.}} o \\subsection*{{}}")


def imagen_existe(ruta):
    """Devuelve (existe_exacto, existe_sin_distinguir_mayusculas)."""
    aprox = False
    for carpeta in (IMAGENES, RAIZ):
        if not os.path.isdir(carpeta):
            continue
        sub = os.path.join(carpeta, os.path.dirname(ruta))
        if not os.path.isdir(sub):
            continue
        nombres = os.listdir(sub)
        base = os.path.basename(ruta)
        for e in EXT_IMG:
            if base + e in nombres:
                return True, True
        for e in EXT_IMG:
            if (base + e).lower() in [n.lower() for n in nombres]:
                aprox = True
    return False, aprox


def main():
    # Con salida redirigida a archivo Windows usa cp1252 y un label con enie o flechas rompe el print
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    incluidos = archivos_incluidos(MAIN)
    archivos = list(incluidos)
    crudos = {a: t for a, t in incluidos.items() if t is not None}
    textos = {a: quitar_comentarios(t) for a, t in crudos.items()}

    for a, t in textos.items():
        nombre = os.path.relpath(a, RAIZ)
        revisar_llaves_y_entornos(nombre, t)
        revisar_flotantes(nombre, t)
        revisar_caracteres(nombre, t)
        revisar_especiales(nombre, t)
        revisar_porcentaje_en_math(nombre, t)
        revisar_avisos_texto(nombre, crudos[a])

    # paquetes incompatibles con la clase (subfigure viejo + comandos \cref/\sref propios)
    if MAIN in textos or os.path.normpath(MAIN) in textos:
        pre = textos.get(MAIN, textos.get(os.path.normpath(MAIN), ""))
        for m in re.finditer(r"\\usepackage(?:\[[^\]]*\])?\{([^}]*)\}", pre):
            for paq in m.group(1).split(","):
                if paq.strip() in ("subcaption", "subfig", "cleveref"):
                    errores.append(f"main.tex:{linea_de(pre, m.start())}: el paquete {paq.strip()} choca con "
                                   f"la clase tesisutec (subfigure viejo, \\cref propio); no cargarlo")

    labels = {}
    for a, t in textos.items():
        nombre = os.path.relpath(a, RAIZ)
        for m in re.finditer(r"\\label\{([^}]+)\}", t):
            if m.group(1) in labels:
                errores.append(f"{nombre}:{linea_de(t, m.start())}: label repetido '{m.group(1)}' "
                               f"(ya esta en {labels[m.group(1)]})")
            labels[m.group(1)] = f"{nombre}:{linea_de(t, m.start())}"
    for a, t in textos.items():
        nombre = os.path.relpath(a, RAIZ)
        for m in re.finditer(r"\\(?:ref|autoref|eqref|pageref|nameref|[Cc]ref|vref)\*?\{([^}]+)\}", t):
            for clave in m.group(1).split(","):
                clave = clave.strip()
                if clave not in labels:
                    errores.append(f"{nombre}:{linea_de(t, m.start())}: \\ref a label inexistente '{clave}'")

    claves_bib = set()
    if os.path.exists(BIB):
        with open(BIB, encoding="utf-8-sig") as f:
            for tipo, clave in re.findall(r"^\s*@(\w+)\s*[{(]\s*([^,\s]+)\s*,", f.read(), flags=re.M):
                if tipo.lower() not in ("comment", "string", "preamble"):
                    claves_bib.add(clave)
    else:
        errores.append("no existe referencias.bib")
    for a, t in textos.items():
        nombre = os.path.relpath(a, RAIZ)
        for m in re.finditer(r"\\[Cc]ite(?:p|t|alp|alt|author|year|yearpar|num|text)?\*?"
                             r"(?:\[[^\]]*\])*\{([^}]+)\}", t):
            for clave in m.group(1).split(","):
                clave = clave.strip()
                if clave and clave not in claves_bib:
                    errores.append(f"{nombre}:{linea_de(t, m.start())}: cita a clave inexistente "
                                   f"en referencias.bib '{clave}'")

    for a, t in textos.items():
        nombre = os.path.relpath(a, RAIZ)
        for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", t):
            ruta = m.group(1).strip().replace("./images/", "").replace("images/", "")
            exacto, aprox = imagen_existe(ruta)
            if exacto:
                continue
            if aprox:
                errores.append(f"{nombre}:{linea_de(t, m.start())}: imagen '{ruta}' existe con otras "
                               f"mayusculas/minusculas; en Overleaf (Linux) no se encontrara")
            else:
                errores.append(f"{nombre}:{linea_de(t, m.start())}: imagen no encontrada '{ruta}' "
                               f"(se busco en images/)")

    for a, t in textos.items():
        nombre = os.path.relpath(a, RAIZ)
        for m in re.finditer(r"\\(?:verbatiminput|lstinputlisting)(?:\[[^\]]*\])?\{([^}]+)\}", t):
            if not os.path.isfile(os.path.join(RAIZ, m.group(1).strip())):
                errores.append(f"{nombre}:{linea_de(t, m.start())}: archivo de codigo no encontrado "
                               f"'{m.group(1).strip()}'")

    incluidos_norm = {os.path.normcase(os.path.abspath(a)) for a in archivos}
    for f in sorted(glob.glob(os.path.join(RAIZ, "secciones", "*.tex"))):
        if os.path.normcase(os.path.abspath(f)) not in incluidos_norm:
            avisos.append(f"secciones/{os.path.basename(f)} no esta incluido en main.tex")
        elif os.path.getsize(f) == 0:
            avisos.append(f"secciones/{os.path.basename(f)} esta vacio")

    for e in errores:
        print("ERROR ", e)
    for w in avisos:
        print("AVISO ", w)
    print(f"{len(archivos)} archivos revisados, {len(labels)} labels, {len(claves_bib)} entradas bib, "
          f"{len(errores)} errores, {len(avisos)} avisos")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
