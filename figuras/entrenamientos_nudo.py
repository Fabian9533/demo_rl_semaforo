"""entrenamientos_nudo.py - Cambio de cada entrenamiento del nudo (los tres del modelo de orden fijo y los tres de la
variante de orden libre, con cada demanda) frente al fijo ajustado al segundo y frente al actuado ajustado, por tanda,
con estudio.comparar (cambio %, IC95 por bootstrap pareado y p de Wilcoxon pareada). Sirve para decir si un veredicto
sin estabilizar se sostiene con los entrenamientos que si se estabilizaron (la tabla de entrenamientos solo da el
cambio frente al fijo).

No simula ni escribe en nudo_ovalo_estudio2/ (se importa sin bytecode): lee salidas/eval_t*_*.csv de demo_rl/lima/ y
demo_rl/lima/alta/. Escribe DESTINO/entrenamientos_nudo.txt.
Uso: python -B entrenamientos_nudo.py DESTINO
"""
import os
import sys

sys.dont_write_bytecode = True
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # con el repositorio y los estudios
EST = os.path.join(RAIZ, "nudo_ovalo_estudio2")
sys.path.insert(0, EST)
import tablas_ovalo as to  # noqa: E402

tl, estudio = to.tl, to.estudio
NIVELES = {"publicada": to.LIMA, "alta": os.path.join(to.LIMA, "alta")}


def main():
    destino = os.path.abspath(sys.argv[1])
    os.makedirs(destino, exist_ok=True)
    lineas = []
    for nivel, carpeta in NIVELES.items():
        for etiqueta in ("completo", "libre"):
            for base in to.BASES:
                for t in estudio.TANDAS:
                    v = tl.leer(carpeta, t, f"{etiqueta}_s{base}")
                    cf = estudio.comparar(v, tl.leer(carpeta, t, "fijo"))
                    ca = estudio.comparar(v, tl.leer(carpeta, t, "actuadoaj"))
                    lineas.append(f"{nivel} {etiqueta} {base} tanda {t}: frente al fijo {cf['delta']:+.2f} "
                                  f"[{cf['ic'][0]:+.2f}, {cf['ic'][1]:+.2f}] p={cf['p']:.2g} | frente al actuado "
                                  f"ajustado {ca['delta']:+.2f} [{ca['ic'][0]:+.2f}, {ca['ic'][1]:+.2f}] p={ca['p']:.2g}")
    with open(os.path.join(destino, "entrenamientos_nudo.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas) + "\n")
    print("\n".join(lineas))


if __name__ == "__main__":
    main()
