"""
construir.py - Compila los diagramas TikZ de la tesis y los deja en TESIS/images.

Uso (desde TESIS/diagramas):  python construir.py [nombre ...]   (sin nombres: todos)
Cada diagrama es un documento standalone <nombre>.tex que hace \\input{estilo_diagramas}. Se
compila con pdflatex y el PDF se copia a ../images/diag_<nombre>.pdf, que es el archivo que
incluye la tesis. Ademas escribe una vista previa PNG en previa/<nombre>.png y reporta el tamano
natural del dibujo: la tesis lo incluye a lo ancho del texto (15 cm), asi que un dibujo mucho mas
ancho que eso achica la letra.
Los diagramas se compilan aparte porque la plantilla no carga TikZ y los paquetes de main.tex no
se tocan.
"""
import os
import shutil
import subprocess
import sys

from pypdf import PdfReader

AQUI = os.path.dirname(os.path.abspath(__file__))
IMAGENES = os.path.join(AQUI, "..", "images")
PREVIA = os.path.join(AQUI, "previa")
DIAGRAMAS = ["arquitectura", "u1", "u2", "u3", "u4"]
ANCHO_TEXTO_CM = 15.0


def compilar(nombre):
    fuente = os.path.join(AQUI, nombre + ".tex")
    if not os.path.exists(fuente):
        print(f"{nombre}: falta {nombre}.tex")
        return False
    r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", nombre + ".tex"],
                       cwd=AQUI, capture_output=True, text=True, encoding="latin-1")
    pdf = os.path.join(AQUI, nombre + ".pdf")
    if r.returncode != 0 or not os.path.exists(pdf):
        errores = [l for l in r.stdout.splitlines() if l.startswith("!") or "Error" in l]
        print(f"{nombre}: ERROR de compilacion\n  " + "\n  ".join(errores[:8]))
        return False
    caja = PdfReader(pdf).pages[0].mediabox
    ancho = float(caja.width) / 72 * 2.54
    alto = float(caja.height) / 72 * 2.54
    escala = min(1.0, ANCHO_TEXTO_CM / ancho)
    shutil.copyfile(pdf, os.path.join(IMAGENES, f"diag_{nombre}.pdf"))
    os.makedirs(PREVIA, exist_ok=True)
    subprocess.run(["pdftoppm", "-png", "-r", "150", "-singlefile", pdf,
                    os.path.join(PREVIA, nombre)], check=True)
    print(f"{nombre}: {ancho:.1f} x {alto:.1f} cm; a 15 cm de ancho queda a escala {escala:.2f}"
          f" ({alto * escala:.1f} cm de alto)")
    return True


def main():
    nombres = sys.argv[1:] or DIAGRAMAS
    ok = all([compilar(n) for n in nombres])
    for ext in (".aux", ".log"):
        for n in nombres:
            ruta = os.path.join(AQUI, n + ext)
            if os.path.exists(ruta):
                os.remove(ruta)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
