"""
p3_congelar.py - Parte B del prerregistro (dia 14; PLAN3 0.17): escribe plan3/referencias_congeladas.json con el
archivo y el sha256 de cada referencia ajustada tal como la evalua la cola (generar_trabajos3.brazos_ref de cada celda
con referencias), despues de comprobar que cada una es la de su barrido y de la regla:
  - cada programa (<esc>_r10f, _m5f, _r10g, _franja, _bloques, _actuado_aj .add.xml) tiene el sha256 que anoto el JSON
    de su barrido (fijo_fino, fijo_mult5, fijo_grueso10, franja, bloques, actuado_aj .json);
  - ningun JSON trae la marca de prueba (registro.prueba vacio);
  - los JSON de las reglas (regla, reactiva, mp) son de su familia y de su escenario.
Despues, evaluar3 se niega a evaluar a ciegas una referencia que no este en el archivo con ese sha256, y
chequeos_previos compara cada tarde el disco con el archivo.

Uso (cwd = plan3/):  python p3_congelar.py [--comprobar]
  --comprobar   no escribe: dice que falta o que no cuadra (codigo 1 si algo).
Codigo 0 solo si todas las referencias de la lista existen y cuadran (y, sin --comprobar, el archivo quedo escrito).
"""
import os
import sys
import json
import shlex
import hashlib
import argparse
import datetime
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
for _ruta in (AQUI, RAIZ):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

DESTINO = os.path.join(AQUI, "referencias_congeladas.json")
# sufijo del programa -> JSON de su barrido en barridos/<esc>/
FUENTES = {"_r10f.add.xml": "fijo_fino.json", "_m5f.add.xml": "fijo_mult5.json", "_r10g.add.xml": "fijo_grueso10.json",
           "_franja.add.xml": "franja.json", "_bloques.add.xml": "bloques.json",
           "_actuado_aj.add.xml": "actuado_aj.json"}


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def archivo_del_brazo(esc, brazo):
    """El archivo que carga un brazo de brazos_ref (como lo resuelve evaluar3.archivo_de_referencia)."""
    partes = shlex.split(brazo)
    opcion = {partes[i]: partes[i + 1] for i in range(len(partes) - 1) if partes[i].startswith("--")}
    if "--regla-de" in opcion:
        return opcion["--regla-de"]
    if opcion.get("--brazo") in ("franja", "bloques", "actuado_aj"):
        return opcion.get("--programa") or f"{esc}_{opcion['--brazo']}.add.xml"
    if opcion.get("--brazo") == "fijo" and "--programa" in opcion:
        return opcion["--programa"]
    return None


def revisar(rel):
    """(datos de la entrada, problemas) de un archivo de referencia, relativo a plan3/."""
    ruta = os.path.join(AQUI, rel)
    if not os.path.exists(ruta):
        return None, [f"{rel}: falta"]
    problemas = []
    entrada = {"sha256": sha256(ruta)}
    if rel.endswith(".json"):                                   # barridos/<esc>/<familia>.json de reglas.py
        with open(ruta, encoding="utf-8") as f:
            datos = json.load(f)
        familia = os.path.splitext(os.path.basename(rel))[0]
        if datos.get("familia") != familia:
            problemas.append(f"{rel}: su familia es {datos.get('familia')}, no {familia}")
        if (datos.get("registro") or {}).get("prueba"):
            problemas.append(f"{rel}: trae la marca de prueba {datos['registro']['prueba']}")
        entrada.update(escenario=datos.get("escenario"), regla=datos.get("regla"), huella=datos.get("huella"))
        return entrada, problemas
    sufijo = next((s for s in FUENTES if rel.endswith(s)), None)
    if sufijo is None:
        return entrada, [f"{rel}: no se de que barrido sale"]
    esc = rel[:-len(sufijo)]
    fuente = os.path.join("barridos", esc, FUENTES[sufijo]).replace(os.sep, "/")
    if not os.path.exists(os.path.join(AQUI, fuente)):
        return entrada, [f"{rel}: falta {fuente}"]
    with open(os.path.join(AQUI, fuente), encoding="utf-8") as f:
        datos = json.load(f)
    if datos.get("sha256") != entrada["sha256"]:
        problemas.append(f"{rel}: su sha256 no es el que anoto {fuente}")
    if (datos.get("registro") or {}).get("prueba"):
        problemas.append(f"{fuente}: trae la marca de prueba {datos['registro']['prueba']}")
    entrada.update(escenario=esc, fuente=fuente, huella=datos.get("huella"), clave=datos.get("clave"))
    return entrada, problemas


def referencias():
    """{archivo relativo a plan3/: (escenario, clave, tipo)} de todas las referencias que evalua la cola."""
    import generar_trabajos3 as g
    if not g.REFS:
        g.referencias(g.Lista())
    salida = {}
    for esc in g.REFS:
        for clave, brazo, _, tipo in g.brazos_ref(esc):
            rel = archivo_del_brazo(esc, brazo)
            if rel:
                salida.setdefault(rel.replace(os.sep, "/"), (esc, clave, tipo))
    return salida


def main():
    ap = argparse.ArgumentParser(description="Parte B: referencias_congeladas.json (plan3, 0.17)", allow_abbrev=False)
    ap.add_argument("--comprobar", action="store_true", help="no escribe: dice que falta o que no cuadra")
    args = ap.parse_args()
    import barrer_fino
    barrer_fino.exigir_cwd()
    lista, problemas, entradas = referencias(), [], {}
    for rel, (esc, clave, tipo) in sorted(lista.items()):
        entrada, malos = revisar(rel)
        problemas += malos
        if entrada:
            entradas[rel] = dict(entrada, celda=esc, referencia=clave, tipo=tipo)
    for p in problemas:
        print("PROBLEMA:", p)
    print(f"referencias de la lista: {len(lista)}; con problemas: {len(problemas)}", flush=True)
    if problemas:
        sys.exit(1)
    if args.comprobar:
        return
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=AQUI, capture_output=True, text=True).stdout.strip()
    datos = {"version": 1, "commit": commit, "escrito": datetime.datetime.now().isoformat(timespec="seconds"),
             "referencias": entradas}
    tmp = f"{DESTINO}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=1, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, DESTINO)
    print(f"escrito {DESTINO}: {len(entradas)} referencias, sha256 {sha256(DESTINO)}")


if __name__ == "__main__":
    main()
