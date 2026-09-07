r"""compilar.py - Compila la tesis en local con MiKTeX y resume lo que salio mal.

Hace el mismo ciclo que Overleaf (pdflatex, bibtex, pdflatex, pdflatex) pero sin
limite de tiempo, y en vez del log crudo de miles de lineas imprime solo lo que
hay que mirar: errores, citas y referencias sin resolver, y las cajas que se salen
del margen. Tambien cronometra cada pasada, que es lo que decide si el documento
entra o no en el tiempo de compilacion de Overleaf.

Uso:
  python compilar.py              ciclo completo (pdflatex, bibtex, pdflatex x2)
  python compilar.py --rapido     una sola pasada, para revisar un cambio de texto
  python compilar.py --limpiar    borra los auxiliares y sale

La primera compilacion tras instalar MiKTeX descarga bastantes paquetes
(babel-spanish, algorithm2e, IEEEtran, subfigure, tocloft, vmargin...) y puede
tardar varios minutos; las siguientes son rapidas.
"""
import os
import re
import shutil
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.abspath(__file__))
TRABAJO = "main"
AUXILIARES = (".aux", ".log", ".out", ".toc", ".lot", ".lof", ".bbl", ".blg",
              ".synctex.gz", ".fdb_latexmk", ".fls")
UMBRAL_HBOX = 50.0        # pt: por debajo de esto el desborde no se ve en el papel


def hay(programa):
    return shutil.which(programa) is not None


def correr(orden, titulo):
    """Ejecuta un paso y devuelve (segundos, codigo). No corta en el primer error."""
    print(f"  {titulo} ...", end="", flush=True)
    t0 = time.time()
    p = subprocess.run(orden, cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    segundos = time.time() - t0
    print(f" {segundos:.1f} s")
    return segundos, p.returncode, p.stdout.decode("utf-8", "replace")


def limpiar():
    n = 0
    for ext in AUXILIARES:
        ruta = os.path.join(RAIZ, TRABAJO + ext)
        if os.path.exists(ruta):
            os.remove(ruta)
            n += 1
    print(f"{n} auxiliares borrados")


def leer(nombre):
    ruta = os.path.join(RAIZ, nombre)
    if not os.path.exists(ruta):
        return ""
    with open(ruta, encoding="utf-8", errors="replace") as f:
        return f.read()


def resumir():
    log = leer(TRABAJO + ".log")
    if not log:
        print("No se genero main.log")
        return 1

    # Errores de TeX: empiezan por '! ' y siguen hasta la linea 'l.<numero>'
    errores = []
    lineas = log.split("\n")
    for i, l in enumerate(lineas):
        if l.startswith("! "):
            sitio = next((x for x in lineas[i:i + 12] if x.startswith("l.")), "")
            errores.append((l.strip(), sitio.strip()[:110]))

    citas = sorted({m.group(1) for m in re.finditer(
        r"Citation `([^']+)' on page \d+ undefined", log)})
    refs = sorted({m.group(1) for m in re.finditer(
        r"Reference `([^']+)' on page \d+ undefined", log)})
    sin_bbl = f"No file {TRABAJO}.bbl" in log
    rerun = "Rerun to get" in log or "Label(s) may have changed" in log

    hbox = []
    for m in re.finditer(r"Overfull \\hbox \(([\d.]+)pt too wide\)[^\n]*", log):
        if float(m.group(1)) >= UMBRAL_HBOX:
            hbox.append((float(m.group(1)), m.group(0)[:100]))
    hbox.sort(reverse=True)

    faltan = sorted({m.group(1) for m in re.finditer(r"File `([^']+)' not found", log)})

    print()
    print("=" * 66)
    if errores:
        print(f"ERRORES ({len(errores)}):")
        for e, sitio in errores[:15]:
            print(f"  {e}")
            if sitio:
                print(f"     en {sitio}")
    else:
        print("ERRORES: ninguno")

    if faltan:
        print(f"\nARCHIVOS NO ENCONTRADOS ({len(faltan)}): {', '.join(faltan[:8])}")

    if sin_bbl:
        print("\nBIBLIOGRAFIA: no existe main.bbl; bibtex no llego a escribirlo")
    if citas:
        print(f"\nCITAS SIN RESOLVER ({len(citas)}): {', '.join(citas[:8])}"
              + (" ..." if len(citas) > 8 else ""))
    else:
        print("\nCITAS: todas resueltas")
    if refs:
        print(f"REFERENCIAS CRUZADAS SIN RESOLVER ({len(refs)}): {', '.join(refs[:8])}")

    if hbox:
        print(f"\nCAJAS QUE SE SALEN MAS DE {UMBRAL_HBOX:.0f} pt ({len(hbox)}):")
        for pt, texto in hbox[:10]:
            print(f"  {texto}")

    blg = leer(TRABAJO + ".blg")
    if blg:
        avisos = [l for l in blg.split("\n") if "Warning" in l or "I couldn't" in l
                  or l.startswith("Repeated") or "---line" in l]
        if avisos:
            print(f"\nBIBTEX ({len(avisos)} avisos):")
            for a in avisos[:8]:
                print("  " + a.strip()[:110])

    pdf = os.path.join(RAIZ, TRABAJO + ".pdf")
    if os.path.exists(pdf):
        paginas = ""
        try:
            import pypdf
            paginas = f", {len(pypdf.PdfReader(pdf).pages)} paginas"
        except Exception:
            pass
        print(f"\nPDF: {TRABAJO}.pdf, {os.path.getsize(pdf) / 1e6:.1f} MB{paginas}")
    else:
        print(f"\nPDF: no se genero {TRABAJO}.pdf")

    if rerun and not errores:
        print("\nNOTA: LaTeX pide otra pasada (cambiaron etiquetas o el indice).")
    print("=" * 66)
    return 1 if (errores or citas or refs or sin_bbl) else 0


def main():
    if "--limpiar" in sys.argv:
        limpiar()
        return 0
    if not hay("pdflatex"):
        print("No se encuentra pdflatex en el PATH.")
        print("Instala MiKTeX (basic-miktex-x64.exe) y reabre la terminal o VS Code.")
        return 2

    pdf = ["pdflatex", "-interaction=nonstopmode", "-file-line-error", TRABAJO + ".tex"]
    tiempos = []
    if "--rapido" in sys.argv:
        print("Compilando (una pasada):")
        tiempos.append(correr(pdf, "pdflatex")[0])
    else:
        print("Compilando (ciclo completo, como Overleaf):")
        tiempos.append(correr(pdf, "pdflatex 1/3")[0])
        if hay("bibtex"):
            tiempos.append(correr(["bibtex", TRABAJO], "bibtex")[0])
        else:
            print("  bibtex no esta instalado: las citas quedaran sin resolver")
        tiempos.append(correr(pdf, "pdflatex 2/3")[0])
        tiempos.append(correr(pdf, "pdflatex 3/3")[0])

    print(f"\nTiempo total: {sum(tiempos):.1f} s"
          f"  (Overleaf gratuito corta cerca del minuto)")
    return resumir()


if __name__ == "__main__":
    sys.exit(main())
