"""
comprobar_referencias.py - Lo que revisa "bash referencias.sh --comprobar", sin simular (18.11.2026): que el escritor de
programas del ovalo (LIMA_PROGRAMA=programa_ovalo) funciona en las dos carpetas de trabajo y da el plan actual que ya
esta escrito, y que la regla de la comprobacion del borde reproduce las variantes registradas.

Uso (desde cualquier carpeta):  python comprobar_referencias.py
Escribe los programas de prueba en un temporal (pruebas/lanzadores/tmp_referencias/), nunca en demo_rl/lima.

Correccion de carriles (18.11.2026, tarde; nudo_ovalo_estudio2): los detectores que no cuentan a nadie de los controles
actuados (uno por carril de adentro) ya no se comparan con un numero escrito a mano (34, los de la red anterior): se
comparan, carril por carril, con los carriles de las aristas de adentro leidos de la red de la carpeta (36 en la red
corregida: entran RN_NE_1, NE_MJ_1 y B_ML_0 y sale RS_SE_2).
"""
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

AQUI = os.path.dirname(os.path.abspath(__file__))
LIMA = os.path.join(AQUI, "demo_rl", "lima")
TMP = os.path.join(AQUI, "pruebas", "lanzadores", "tmp_referencias")
AFUERA = ("RN_S1", "RS_S1", "B_S1", "J_S1", "S1_L", "S1_RN", "S1_RS", "S1_J")     # las cuatro entradas y las cuatro salidas


def carriles_de_adentro(ruta_red):
    """Carriles de las aristas de adentro del ovalo (todas menos las entradas y las salidas), leidos del .net.xml sin
    pasar por el escritor: cada uno debe llevar su detector que no cuenta a nadie en los controles actuados."""
    return sorted(carril.get("id") for arista in ET.parse(ruta_red).getroot().findall("edge")
                  if arista.get("function") is None and arista.get("id") not in AFUERA
                  for carril in arista.findall("lane"))


def revisar_carpeta(sub):
    """Corre en un proceso aparte (programa_ovalo lee LIMA_CARPETA al importarse)."""
    os.environ["LIMA_CARPETA"] = sub
    os.environ["LIMA_PROGRAMA"] = "programa_ovalo"
    sys.path.insert(0, LIMA)
    import estudio
    programa = estudio.cargar_programa()
    assert programa.__name__ == "programa_ovalo", programa.__name__
    fallas = []
    if programa.minimos() != [10, 10, 10]:
        fallas.append(f"minimos {programa.minimos()}")
    lista, avisos = programa.fases([v for _, v, _ in programa.PLAN])
    with open(os.path.join(estudio.CARPETA, "lima.add.xml"), encoding="utf-8") as f:
        escrito = re.findall(r'duration="(\d+)" state="([^"]+)"', f.read())
    if [(str(d), e) for d, e, _ in lista] != escrito or avisos:
        fallas.append("el plan actual de programa_ovalo no es el de lima.add.xml")
    os.makedirs(TMP, exist_ok=True)
    nombre = sub or "publicada"
    adentro = carriles_de_adentro(os.path.join(estudio.CARPETA, "lima.net.xml"))
    for tipo, parametros in (("fijo", None), ("actuado", {"max-gap": 1.0}),
                             ("retraso", {"detectorRange": 200, "minTimeLoss": 3})):
        ruta = os.path.join(TMP, f"{nombre}_{tipo}.add.xml")
        _, avisos = programa.escribir(ruta, [37, 15, 37] if tipo == "fijo" else [60, 60, 60], tipo=tipo,
                                      parametros=parametros)
        raiz = ET.parse(ruta).getroot()
        nulos = raiz.findall("laneAreaDetector") + raiz.findall("inductionLoop")
        if avisos or (tipo != "fijo" and sorted(d.get("lane") for d in nulos) != adentro):
            fallas.append(f"{tipo}: avisos {avisos}, {len(nulos)} detectores nulos para {len(adentro)} carriles de adentro")
    print(f"{nombre}: " + ("escritor del ovalo correcto (plan actual igual a lima.add.xml; fijo, actuado y por "
                           f"retraso con un detector nulo en cada uno de los {len(adentro)} carriles de adentro de la red)"
                           if not fallas else "FALLAS: " + "; ".join(fallas)))
    return not fallas


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 1:
        return 0 if revisar_carpeta("" if sys.argv[1] == "publicada" else sys.argv[1]) else 1
    ok = True
    for nivel in ("publicada", "alta"):
        ok &= subprocess.run([sys.executable, "-B", os.path.abspath(__file__), nivel]).returncode == 0
    ok &= subprocess.run([sys.executable, "-B", os.path.join(LIMA, "borde_actuado.py"), "--probar-reglas"]).returncode == 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
