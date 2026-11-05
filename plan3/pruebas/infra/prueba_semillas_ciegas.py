"""
prueba_semillas_ciegas.py - Las semillas del examen y de la prueba final solo se simulan desde la cola (05.11.2026).

Uso (desde plan3/):  python pruebas/infra/prueba_semillas_ciegas.py   -> pruebas/infra/prueba_semillas_ciegas.txt
No abre SUMO con ninguna semilla a ciegas: la guarda sale antes de traci.start.
  1. comun.BLOQUES_CIEGOS y comun.USOS_CIEGOS son los de la tabla del prerregistro y los de protecciones;
  2. revisar_semilla_ciega niega las semillas a ciegas sin P3_USO o con un uso que no es ciego, y deja pasar las de
     humo, validacion, promocion, ajuste, puente y todas las de entrenamiento (base + episodio, hasta 600 episodios);
  3. comun.iniciar_sumo llama a la guarda (un proceso aparte con --seed 8001 sale con el mensaje y sin abrir SUMO);
  4. cola.py pasa el uso de cada trabajo en P3_USO.
"""
import os
import re
import sys
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN3 = os.path.dirname(os.path.dirname(AQUI))
RAIZ = os.path.dirname(PLAN3)
sys.dont_write_bytecode = True
sys.path.insert(0, RAIZ)
sys.path.insert(0, PLAN3)
import comun            # noqa: E402
import protecciones     # noqa: E402

lineas, fallos = [], []


def ok(cond, texto):
    lineas.append(f"{'PASA' if cond else 'FALLA'}  {texto}")
    if not cond:
        fallos.append(texto)


def niega(semilla, uso):
    viejo = os.environ.pop("P3_USO", None)
    if uso is not None:
        os.environ["P3_USO"] = uso
    try:
        comun.revisar_semilla_ciega(["sumo", "-c", "x.sumocfg", "--seed", str(semilla)])
        return False
    except SystemExit:
        return True
    finally:
        os.environ.pop("P3_USO", None)
        if viejo is not None:
            os.environ["P3_USO"] = viejo


def conjunto(bloques):
    return {s for a, b in bloques for s in range(a, b + 1)}


# 1. los bloques y los usos son los del prerregistro
tabla = protecciones.tabla()["semillas"]
del_prerregistro = conjunto([tuple(b) for uso in comun.USOS_CIEGOS for b in tabla[uso]])
ok(conjunto(comun.BLOQUES_CIEGOS) == del_prerregistro,
   f"1a. BLOQUES_CIEGOS = examen_regular + examen_h1 + examen_aleatorio + final del prerregistro "
   f"({len(del_prerregistro)} semillas)")
ok(set(comun.USOS_CIEGOS) == set(protecciones.USOS_CIEGOS), "1b. USOS_CIEGOS = protecciones.USOS_CIEGOS")

# 2. la guarda
bordes = [7001, 7100, 8001, 8030, 8120, 10001, 10100, 11001, 11030, 12001, 12100, 13001, 13120]
ok(all(niega(s, None) for s in bordes), f"2a. sin P3_USO se niegan los bordes de cada bloque: {bordes}")
ok(all(niega(8001, u) for u in ("entrenamiento", "ajuste", "validacion", "humo", "sin_semillas", "")),
   "2b. con un uso que no es ciego (entrenamiento, ajuste, validacion, humo, sin_semillas, vacio) se niega 8001")
ok(not any(niega(s, u) for s, u in ((8001, "examen_regular"), (8120, "examen_h1"), (7001, "examen_aleatorio"),
                                    (11001, "final"))),
   "2c. en un trabajo ciego (examen_regular, examen_h1, examen_aleatorio, final) pasa")
libres = sorted({7, 424301, 424360, 999, 7999, 8999, 9999, 15001, 15024, 2001, 2030, 1001, 1030, 7000, 8000, 8121,
                 10000, 10101, 11000, 11031, 12000, 12101, 13000, 13121})
ok(not any(niega(s, None) for s in libres), f"2d. pasan las de humo, validacion, promocion, ajuste y puente y los "
                                            f"vecinos de cada bloque: {libres}")
entrenamiento = {b + ep for b in (7, 42, 2042, 4042, 14042, 16042) for ep in range(1, 601)}
ok(not (entrenamiento & conjunto(comun.BLOQUES_CIEGOS)),
   "2e. ninguna semilla de entrenamiento (base 7, 42, 2042, 4042, 14042, 16042 + episodio 1-600) cae en un bloque")
try:
    comun.revisar_semilla_ciega(["sumo", "-c", "x.sumocfg"])
    sin_seed = True
except SystemExit:
    sin_seed = False
ok(sin_seed, "2f. un comando sin --seed pasa")

# 3. iniciar_sumo llama a la guarda antes de abrir SUMO
entorno = {k: v for k, v in os.environ.items() if k != "P3_USO"}
r = subprocess.run([sys.executable, "-B", "-c",
                    "import sys; sys.path.insert(0, r'%s'); import comun; "
                    "comun.iniciar_sumo(['sumo', '-c', 'no_existe.sumocfg', '--seed', '8001'], intentos=1)" % RAIZ],
                   capture_output=True, text=True, env=entorno, cwd=AQUI)
ok(r.returncode != 0 and "semilla 8001" in (r.stderr + r.stdout) and "Could not" not in (r.stderr + r.stdout),
   f"3. iniciar_sumo con --seed 8001 y sin P3_USO sale con el mensaje de la guarda (codigo {r.returncode}) y no "
   f"llega a SUMO")

# 4. cola.py pasa el uso
fuente = open(os.path.join(PLAN3, "cola.py"), encoding="utf-8").read()
ok(re.search(r"env=dict\(entorno, P3_USO=t\.get\(\"uso\", \"\"\)\)", fuente) is not None,
   "4. cola.py lanza cada trabajo con P3_USO = su uso")

lineas.append(f"\n{len(lineas) - len(fallos)} de {len(lineas)} pasan")
salida = os.path.join(AQUI, "prueba_semillas_ciegas.txt")
with open(salida, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lineas) + "\n")
print("\n".join(lineas))
sys.exit(1 if fallos else 0)
