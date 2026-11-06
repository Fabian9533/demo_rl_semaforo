"""
prueba_congeladas.py - Las referencias congeladas de la parte B ([21] de la revision de 0cea683; G1-F2, G2-1 y G3-6 de
la de 6e8cfab), en una copia del corredor (tmp_ref/congeladas/) con un fijo fino y un regla.json armados a mano:
  1. evaluar3 escribe sha_ref (el sha256 del archivo de la referencia que carga) y, fuera de ciego/, no pide nada mas;
  2. a ciegas (--salida ciego/...) se niega antes de simular si falta referencias_congeladas.json, si no lista el
     archivo o si su sha256 no es el congelado; con el archivo congelado, corre;
  3. --regla-de se niega si el JSON trae la marca de prueba, si su familia no es la del nombre del archivo o si es de
     otro escenario (mixa_<x> juega lo de mix_<x>);
  4. p3_congelar: el archivo de cada brazo de la cola, y la revision de cada uno (el sha256 que anoto su barrido, la
     marca de prueba, la familia); chequeos_previos compara el disco con el JSON congelado.
Semilla de humo 424301 (dos corridas del corredor). Uso (cwd = plan3/): python pruebas/ref/prueba_congeladas.py
Salida: pruebas/ref/salidas/prueba_congeladas.txt
"""
import os
import sys
import csv
import json
import types
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
inf = up.Informe("prueba_congeladas")
CARPETA = up.copia("congeladas", ["corredor"])
import barrer_fino as bfn  # noqa: E402
import p3_congelar  # noqa: E402
import chequeos_previos as ch  # noqa: E402

S = str(up.HUMO[0])


def evaluar3(*args):
    r = subprocess.run([sys.executable, os.path.join(up.PLAN3, "evaluar3.py"), "--escenario", "corredor",
                        "--semillas", S, *args], cwd=CARPETA, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def leer(ruta):
    with open(os.path.join(CARPETA, ruta), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def preparar_referencias():
    """corredor_r10f.add.xml con el fijo entregado (y su fijo_fino.json) y barridos/corredor/regla.json."""
    c = bfn.Celda("corredor", prefijos=())
    pl = c.plan(20, 10, [0, 15])
    c.escribir_plan("corredor_r10f.add.xml", pl)
    os.makedirs(os.path.join("barridos", "corredor"), exist_ok=True)
    with open(os.path.join("barridos", "corredor", "fijo_fino.json"), "w", encoding="utf-8") as f:
        json.dump({"escenario": "corredor", "sha256": up.sha256("corredor_r10f.add.xml"), "clave": pl["clave"],
                   "huella": c.huella, "cortes": c.cortes, "registro": {"prueba": []}}, f)
    regla = {"escenario": "corredor", "familia": "regla", "regla": "regla_u2g30", "registro": {"prueba": []}}
    with open(os.path.join("barridos", "corredor", "regla.json"), "w", encoding="utf-8") as f:
        json.dump(regla, f)
    return regla


def main():
    inf(f"Referencias congeladas (copia en {CARPETA})")
    import shutil
    for resto in ("ciego", "parciales", "barridos", "referencias_congeladas.json"):     # lo de una corrida anterior
        ruta = os.path.join(CARPETA, resto)
        if os.path.isdir(ruta):
            shutil.rmtree(ruta)
        elif os.path.exists(ruta):
            os.remove(ruta)
    regla = preparar_referencias()
    fino = ["--brazo", "fijo", "--programa", "corredor_r10f.add.xml", "--nombre", "fino"]
    cod, texto = evaluar3("--salida", "parciales/eval_fino.csv", *fino)
    filas = leer("parciales/eval_fino.csv") if cod == 0 else []
    inf.chequeo(cod == 0 and filas and filas[0]["sha_ref"] == up.sha256(os.path.join(CARPETA, "corredor_r10f.add.xml")),
                f"1 fuera de ciego/ corre sin el JSON congelado y anota sha_ref "
                f"{filas[0]['sha_ref'][:16] if filas else '-'}... (codigo {cod})")
    casos = []
    cod, texto = evaluar3("--salida", "ciego/t/eval_fino.csv", *fino)
    casos.append(("sin el JSON", cod, "necesita referencias_congeladas.json" in texto))
    with open(os.path.join(CARPETA, "referencias_congeladas.json"), "w", encoding="utf-8") as f:
        json.dump({"referencias": {"otro.add.xml": {"sha256": "0" * 64}}}, f)
    cod, texto = evaluar3("--salida", "ciego/t/eval_fino.csv", *fino)
    casos.append(("sin el archivo en el JSON", cod, "no esta en" in texto))
    with open(os.path.join(CARPETA, "referencias_congeladas.json"), "w", encoding="utf-8") as f:
        json.dump({"referencias": {"corredor_r10f.add.xml": {"sha256": "0" * 64}}}, f)
    cod, texto = evaluar3("--salida", "ciego/t/eval_fino.csv", *fino)
    casos.append(("sha256 distinto", cod, "no es la referencia congelada" in texto))
    sin_simular = not os.path.exists(os.path.join(CARPETA, "ciego", "t", "eval_fino.csv")) and not any(
        n.startswith("tmp_eval3_") for n in os.listdir(up.PLAN3))
    inf.chequeo(all(c != 0 and m for _, c, m in casos) and sin_simular,
                f"2 a ciegas se niega antes de simular: {casos}; ningun CSV ni carpeta temporal: {sin_simular}")
    with open(os.path.join(CARPETA, "referencias_congeladas.json"), "w", encoding="utf-8") as f:
        json.dump({"referencias": {"corredor_r10f.add.xml": {
            "sha256": up.sha256(os.path.join(CARPETA, "corredor_r10f.add.xml"))}}}, f)
    cod, texto = evaluar3("--salida", "ciego/t/eval_fino.csv", *fino)
    inf.chequeo(cod == 0 and leer("ciego/t/eval_fino.csv")[0]["sha_ref"] == filas[0]["sha_ref"],
                f"2 con la referencia congelada corre a ciegas (codigo {cod})")
    # 3. --regla-de
    resultados = []
    for nombre, cambio, archivo in (("marca de prueba", {"registro": {"prueba": ["--semillas 424301"]}}, "regla.json"),
                                    ("otra familia", {"familia": "mp"}, "regla.json"),
                                    ("otro escenario", {"escenario": "red"}, "regla.json"),
                                    ("nombre de otra familia", {}, "mp.json")):
        ruta = os.path.join("barridos", "corredor", archivo)
        with open(os.path.join(CARPETA, ruta), "w", encoding="utf-8") as f:
            json.dump(dict(regla, **cambio), f)
        cod, texto = evaluar3("--salida", "parciales/eval_regla.csv", "--regla-de", ruta.replace(os.sep, "/"))
        resultados.append((nombre, cod, texto.strip().splitlines()[-1][:90] if texto.strip() else ""))
    sys.path.insert(0, up.PLAN3)
    import evaluar3 as e3
    os.chdir(CARPETA)
    with open(os.path.join("barridos", "corredor", "regla.json"), "w", encoding="utf-8") as f:
        json.dump(dict(regla, escenario="mix_corredor"), f)
    mixa = e3.leer_regla_de(types.SimpleNamespace(regla_de="barridos/corredor/regla.json", escenario="mixa_corredor"))
    os.chdir(up.PLAN3)
    inf.chequeo(all(c != 0 for _, c, _ in resultados) and mixa == "regla_u2g30",
                f"3 --regla-de se niega: {resultados}; mixa_corredor acepta el de mix_corredor: {mixa}")
    # 4. p3_congelar y chequeos_previos
    archivos = {e: p3_congelar.archivo_del_brazo("corredor", b) for e, b in (
        ("fino", "--brazo fijo --programa corredor_r10f.add.xml --nombre fino"), ("franja", "--brazo franja"),
        ("actuado_aj mixa", "--brazo actuado_aj --programa mix_corredor_actuado_aj.add.xml"),
        ("regla", "--regla-de barridos/corredor/regla.json"), ("fijo", "--brazo fijo"))}
    os.chdir(CARPETA)
    with open(os.path.join("barridos", "corredor", "regla.json"), "w", encoding="utf-8") as f:
        json.dump(regla, f)
    bien_fino, prob_fino = p3_congelar.revisar("corredor_r10f.add.xml")
    bien_regla, prob_regla = p3_congelar.revisar("barridos/corredor/regla.json")
    with open("corredor_r10f.add.xml", "a", encoding="utf-8") as f:
        f.write("<!-- cambiado -->" + os.linesep)
    _, prob_cambiado = p3_congelar.revisar("corredor_r10f.add.xml")
    os.chdir(up.PLAN3)
    lista = p3_congelar.referencias()
    inf.chequeo(archivos == {"fino": "corredor_r10f.add.xml", "franja": "corredor_franja.add.xml",
                             "actuado_aj mixa": "mix_corredor_actuado_aj.add.xml",
                             "regla": "barridos/corredor/regla.json", "fijo": None}
                and not prob_fino and not prob_regla and prob_cambiado and len(lista) > 100,
                f"4 p3_congelar: archivos de los brazos {archivos}; el fino y la regla cuadran ({prob_fino}, "
                f"{prob_regla}); el fino cambiado no ({prob_cambiado}); {len(lista)} referencias en la cola")
    viejo = ch.PLAN3
    ch.PLAN3 = CARPETA
    try:
        malos = ch.referencias_congeladas()             # el JSON congelado de la prueba 2 y el fino ya cambiado
    finally:
        ch.PLAN3 = viejo
    inf.chequeo(len(malos) == 1 and "cambiada" in malos[0], f"4 chequeos_previos compara el disco con el JSON: {malos}")
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
