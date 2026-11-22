"""secuencia_ovalo_tesis.py - fig:lima-secuencia (Anexo D) con los nombres de la tesis: la figura de
nudo_ovalo_estudio2/figura_secuencia.py (accion "dibujar"), la misma ventana (minutos 30 a 36, semilla de validacion
21001) y las mismas trazas, con el rotulo "Variante de orden libre" en lugar de "Modelo de orden libre".

No simula ni escribe en nudo_ovalo_estudio2/ (se importa sin bytecode): copia las cuatro trazas ya corridas
(salidas_ovalo/corridas_secuencia/<nivel>/<modelo>/traza_21001.csv) a una carpeta temporal dentro de DESTINO, dibuja
ahi con figura_secuencia.dibujar y deja en DESTINO fig_ovalo_secuencia_<nivel>.pdf|png|txt.
Uso: python -B secuencia_ovalo_tesis.py DESTINO
"""
import os
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # con el repositorio y los estudios
EST = os.path.join(RAIZ, "nudo_ovalo_estudio2")
sys.path.insert(0, EST)
import figura_secuencia as fs  # noqa: E402

fs.MODELOS = [("completo", "Modelo de\norden fijo"), ("libre", "Variante de\norden libre")]
SEMILLA, DESDE, SEGUNDOS = 21001, 1800, 360


def main():
    destino = os.path.abspath(sys.argv[1])
    os.makedirs(destino, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destino) as tmp:
        for nivel, sub in fs.NIVELES.items():
            for etiqueta, _ in fs.MODELOS:
                origen = os.path.join(EST, "salidas_ovalo", "corridas_secuencia", nivel, etiqueta, f"traza_{SEMILLA}.csv")
                carpeta = os.path.join(tmp, "corridas_secuencia", nivel, etiqueta)
                os.makedirs(carpeta)
                shutil.copy2(origen, carpeta)
            fs.dibujar(os.path.join(fs.DEMO, "lima", sub), nivel, SEMILLA, DESDE, SEGUNDOS, tmp)
            for ext in ("pdf", "png", "txt"):
                shutil.copy2(os.path.join(tmp, f"fig_ovalo_secuencia_{nivel}.{ext}"), destino)


if __name__ == "__main__":
    main()
