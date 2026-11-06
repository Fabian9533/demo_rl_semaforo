"""
prueba_comandos_ref.py - Sin sumo: los comandos que el generador arma para las referencias y sus evaluaciones pasan el
parser de su script, y lo que no corresponde se rechaza la tarde anterior (revision de 6e8cfab: G1-F4, G1-F5, G2-5,
G3-7, [21] y el chequeo estatico de los trozos del critico).
  1. chequeos_previos.comandos con todos los trabajos de referencias, sus evaluaciones (tambien perfil y mezcla) y
     "preparar": cada comando pasa el validar_args de su script (barrer_fino, franja, actuado, reglas, p3_preparar,
     evaluar3);
  2. un comando malo por script (una etapa con --trozo que no lo admite, una familia que no existe, --paso con
     --instalar, una pieza desconocida, dos brazos en evaluar3, una opcion abreviada) se rechaza con su motivo;
  3. trozos: cada r_<etapa>_<esc>_t<k>de<n> termina en --trozo k/n y declara su trozo, y la union r_<etapa>_<esc>
     requiere exactamente esos n;
  4. presupuestos: las reglas por familia y llegadas (regla 51/84, reactiva 36/84, MP 33/84 de la columna con llegadas
     regulares; 300, 150 y 120 de 420 con aleatorias), franja y reglas sin EMPAQUE, pasos del actuado por sus
     corridas; las salidas declaradas traen los *_semillas.csv;
  5. las evaluaciones decisivas (a ciegas) de las referencias ajustadas requieren referencias_congeladas.json; las
     otras no;
  6. cola.huerfano_vivo (huerfanos de una cola caida, por pid; revision de 0cea683 [25]) con listas de procesos
     armadas a mano: dos trabajos cuyos comandos son prefijo uno del otro (franja.py corredor y corredor_alta) se
     reconocen cada uno solo por su pid, y un pid que el sistema reuso para otro programa no cuenta.
Uso (cwd = plan3/): python pruebas/ref/prueba_comandos_ref.py     Salida: pruebas/ref/salidas/prueba_comandos_ref.txt
"""
import os
import re
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import util_pruebas as up  # noqa: E402

up.preparar()
inf = up.Informe("prueba_comandos_ref")
CARPETA = os.path.join(up.TMP, "comandos_ref")
os.makedirs(CARPETA, exist_ok=True)
import generar_trabajos3 as g  # noqa: E402
import chequeos_previos as ch  # noqa: E402

PARTES = ["preparar", "referencias", "evaluaciones_referencias", "evaluaciones_perfil_mezcla"]


def escribir(nombre, trabajos):
    ruta = os.path.join(CARPETA, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("".join(json.dumps(t) + "\n" for t in trabajos))
    return ruta


def main():
    lista = g.generar(PARTES)
    mios = [t for t in lista if re.search(r"(barrer_fino|franja|actuado|reglas|p3_preparar|evaluar3)\.py", t["cmd"])]
    malos = ch.comandos(escribir("trabajos.jsonl", mios))
    inf.chequeo(not malos, f"1 {len(mios)} comandos de {', '.join(PARTES)} pasan el parser de su script; "
                           f"rechazados: {malos[:3]}")
    errados = [("python barrer_fino.py corredor --etapa fragil --trozo 0/2", "--trozo solo"),
               ("python franja.py corredor --bloques --semilla 2001", "unrecognized arguments"),
               ("python actuado.py corredor --paso 6 --instalar", "excluyentes"),
               ("python reglas.py corredor --familia reactivas", "invalid choice"),
               ("python p3_preparar.py corredor --piezas actuado,e2", "piezas desconocidas"),
               ("python evaluar3.py --escenario corredor --semillas 2001-2003 --salida x.csv --brazo fijo --regla mp",
                "not allowed with"),
               ("python evaluar3.py --escenario corredor --semillas 2001-2003 --salida x.csv --brazo actuado "
                "--programa a.add.xml", "--programa solo va"),
               ("python ../con_escenarios.py reglas.py poi_corredor --fam reactiva", "unrecognized arguments")]
    malos = ch.comandos(escribir("errados.jsonl", [{"id": f"malo_{k}", "cmd": c} for k, (c, _) in enumerate(errados)]))
    motivos = {m.split(":")[0].replace("rechazado ", ""): m for m in malos}
    ok = len(malos) == len(errados) and all(esperado in motivos.get(f"malo_{k}", "")
                                            for k, (_, esperado) in enumerate(errados))
    inf.chequeo(ok, f"2 {len(errados)} comandos errados, {len(malos)} rechazados con su motivo: "
                    + "; ".join(m.split(": ", 2)[-1][:70] for m in malos))
    # 3. trozos
    refs = g.generar(["referencias"])
    por_id = {t["id"]: t for t in refs}
    mal, uniones = [], {}
    for t in refs:
        m = re.fullmatch(r"r_(\w+?)_(.+)_t(\d+)de(\d+)", t["id"])
        if not m:
            continue
        et, esc, k, n = m.group(1), m.group(2), int(m.group(3)), int(m.group(4))
        if not t["cmd"].endswith(f"--trozo {k}/{n}"):
            mal.append((t["id"], "cmd"))
        if t["salidas"] != [f"barridos/{esc}/trozos/{et}_t{k}de{n}.csv"]:
            mal.append((t["id"], "salidas"))
        uniones.setdefault(f"r_{et}_{esc}", []).append((t["id"], n))
    for u, trozos in uniones.items():
        ns = {n for _, n in trozos}
        req = {r[len("trabajo:"):] for r in por_id[u]["requiere"] if r.startswith("trabajo:")}
        if len(ns) != 1 or len(trozos) != ns.pop() or req != {i for i, _ in trozos}:
            mal.append((u, "union"))
    inf.chequeo(uniones and not mal, f"3 {sum(len(v) for v in uniones.values())} trozos en {len(uniones)} uniones: "
                                     f"id, --trozo k/n, salida y dependencias de la union: {mal or 'bien'}")
    # 4. presupuestos y salidas
    malos4 = []
    for esc, llegadas in (("corredor", "regulares"), ("poi_corredor", "aleatorias"), ("red", "regulares")):
        h = dict(zip(("gruesa", "fina", "desfases", "desempate", "fragil", "mult5", "franja", "actuado", "reglas"),
                     g.REF_H[esc]))
        for fam in ("regla", "reactiva", "mp"):
            esperado = round(3600 * max(h["reglas"] * g.PARTE_REGLAS[llegadas][fam], 0.05))
            if por_id[f"r_{fam}_{esc}"]["duracion"] != esperado:
                malos4.append((esc, fam, por_id[f"r_{fam}_{esc}"]["duracion"], esperado))
            if f"barridos/{esc}/reglas_{fam}_semillas.csv" not in por_id[f"r_{fam}_{esc}"]["salidas"]:
                malos4.append((esc, fam, "sin _semillas.csv"))
        if por_id[f"r_franja_{esc}"]["duracion"] != round(3600 * max(h["franja"], 0.05)):
            malos4.append((esc, "franja con EMPAQUE"))
        pasos = [por_id[f"r_actuado{k}_{esc}"]["duracion"] for k in "123456"]
        if not pasos[5] > pasos[0] > pasos[1] >= pasos[2]:
            malos4.append((esc, "pasos del actuado", pasos))
        for s in ("fragil_semillas.csv", "mult5_semillas.csv", "mult5_desempate_semillas.csv", "franja_semillas.csv"):
            dueno = {"fragil": "r_fragil", "mult5": "r_mult5", "franja": "r_franja"}[s.split("_")[0]]
            if f"barridos/{esc}/{s}" not in por_id[f"{dueno}_{esc}"]["salidas"]:
                malos4.append((esc, s))
    reparto = {k: {f: round(v, 3) for f, v in d.items()} for k, d in g.PARTE_REGLAS.items()}
    inf.chequeo(not malos4, f"4 presupuestos (reglas {reparto}; franja y reglas sin EMPAQUE; actuado por corridas "
                            f"{ {k: round(v, 3) for k, v in g.PESO_PASO.items()} }) y salidas con sus _semillas.csv: "
                            f"{malos4 or 'bien'}")
    # 5. referencias congeladas en las evaluaciones decisivas
    evs = [t for t in lista if t["id"].startswith("ev_")]
    de_ref = [t for t in evs if re.search(r"--programa |--brazo (franja|bloques|actuado_aj)|--regla-de ", t["cmd"])]
    sin = [t["id"] for t in de_ref if t["uso"] in g.CIEGAS and "referencias_congeladas.json" not in t["requiere"]]
    de_mas = [t["id"] for t in evs if t not in de_ref and "referencias_congeladas.json" in t["requiere"]]
    inf.chequeo(de_ref and not sin and not de_mas,
                f"5 {len(de_ref)} evaluaciones de referencias ajustadas: a ciegas sin referencias_congeladas.json en "
                f"requiere {len(sin)}; otras evaluaciones que lo piden {len(de_mas)}")
    # 6. huerfanos por pid
    import cola
    a, b = "python franja.py corredor", "python franja.py corredor_alta"
    vivos = [(500, 4, f"cmd.exe /c {b}"), (501, 500, f"C:/Python/python.exe {b[7:]}"),
             (600, 4, "C:/Windows/notepad.exe"), (700, 4, f"cmd.exe /c {a}"), (701, 700, f"python.exe {a[7:]}")]
    casos = {"corredor_alta vivo, por su pid": cola.huerfano_vivo(b, 500, vivos),
             "corredor con el pid del de corredor_alta": cola.huerfano_vivo(a, 500, vivos),
             "corredor vivo, por su pid": cola.huerfano_vivo(a, 700, vivos),
             "corredor con su pid reusado por notepad": cola.huerfano_vivo(a, 600, vivos),
             "corredor_alta muerto (pid sin proceso)": cola.huerfano_vivo(b, 800, vivos)}
    esperado = {"corredor_alta vivo, por su pid": True, "corredor con el pid del de corredor_alta": True,
                "corredor vivo, por su pid": True, "corredor con su pid reusado por notepad": False,
                "corredor_alta muerto (pid sin proceso)": False}
    # el segundo caso es True porque el comando de corredor esta dentro del de corredor_alta y el pid es el de ese
    # proceso: la cola no lo pregunta asi (cada trabajo con su propio pid), por eso lo que importa es el tercero
    inf.chequeo(casos == esperado, f"6 huerfanos por pid: {casos}")
    sys.exit(1 if inf.cerrar() else 0)


if __name__ == "__main__":
    main()
