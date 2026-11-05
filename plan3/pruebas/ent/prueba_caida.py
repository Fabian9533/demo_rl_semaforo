"""
prueba_caida.py - --reanudar auto con caidas de verdad (tarea 1.2 del plan 3, pedido del 05.11; DECISIONES B22).
Informe: plan3/doc/informe_ent1.md.

Un mismo comando, con --reanudar auto, en dos tramos (--hasta-ep 10 y hasta el final, 20 episodios), V2 en P1,
base 7, validacion cada 5 en 424301-424302. En cada tramo se mata el proceso a mitad de un episodio con
taskkill /F /T y se relanza el mismo comando: debe seguir desde el ultimo estado, repetir los episodios que el
intento caido alcanzo a escribir y terminar igual que la corrida seguida (el mismo comando sin --hasta-ep ni
caidas, en otra carpeta y con el mismo commit: el meta lo guarda): CSV salvo segundos, checkpoints, politica
publicada y estados. Relanzar un tramo ya hecho (o la corrida ya publicada) sale con 0 sin tocar ningun archivo.

Despues, lo mismo con una etiqueta nueva (como "400 desde el 180"): desde el estado del ep 10 de esa corrida, otra
etiqueta con 30 episodios, --lr-horizonte 20 --lr-piso 0.1 y la ruta del estado de origen en los dos tramos
(--hasta-ep 20 y final). El primer tramo se mata a mitad; relanzado con el mismo comando debe seguir desde sus
propios estados (no volver a copiar) y terminar igual que una corrida seguida de 30 con esa etiqueta.

Uso:  python plan3/pruebas/ent/prueba_caida.py   (un proceso a la vez, ~12 min)
Salida: plan3/pruebas/ent/salidas/prueba_caida.txt; corridas en plan3/tmp_ent/caida_*.
"""
import re
import sys
import json
import time
import subprocess

import util_ent as u

ESC = "corredor"
TAG, POL = f"{ESC}_ippo_vecinos_p3prbv2_s7", f"{ESC}_vecinos_p3prbv2_s7"
COMANDO = ["train", "--escenario", ESC, "--seed", "7", "--episodios", "20", "--eval-cada", "5",
           "--val-seeds", u.VAL_HUMO, "--v2", "--criterio-val", "total", "--etiqueta", "p3prbv2",
           "--guardar-estado", "--registro-extendido", "--reanudar", "auto"]
TRAMO1 = COMANDO + ["--hasta-ep", "10"]
TRAMO2 = COMANDO
TAG_N, POL_N = f"{ESC}_ippo_vecinos_p3prbcaidan_s7", f"{ESC}_vecinos_p3prbcaidan_s7"
NUEVA = ["train", "--escenario", ESC, "--seed", "7", "--episodios", "30", "--eval-cada", "5",
         "--val-seeds", u.VAL_HUMO, "--v2", "--criterio-val", "total", "--etiqueta", "p3prbcaidan",
         "--guardar-estado", "--registro-extendido", "--lr-horizonte", "20", "--lr-piso", "0.1"]


def filas(c, tag=TAG):
    ruta = c / f"resultados_{tag}.csv"
    if not ruta.exists():
        return 0
    with open(ruta, newline="") as f:
        return max(0, f.read().count("\r\n") - 1)


def huellas(c):
    """sha256 de cada archivo de la carpeta (menos los logs): para ver que un relanzamiento no toca nada."""
    return {str(p.relative_to(c)): u.sha256(p) for p in sorted(c.rglob("*"))
            if p.is_file() and not p.name.startswith("log")}


def matar_en(inf, c, argumentos, log, filas_objetivo, tag=TAG):
    """Lanza, espera a que el CSV tenga filas_objetivo filas y mata el arbol de procesos (python y sumo)."""
    p = u.lanzar(u.RL_NUEVO, argumentos, c, log)
    while p.poll() is None and filas(c, tag) < filas_objetivo:
        time.sleep(0.2)
    if p.poll() is None:
        r = subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True, text=True)
        muertos = len(re.findall(r"PID \d+ \(", r.stdout))     # una linea por proceso: "... PID n (... PID m)"
        inf(f"   taskkill /F /T /PID {p.pid} con {filas(c, tag)} filas escritas: codigo {r.returncode}, "
            f"{muertos} procesos terminados (python y su sumo)")
    cod = p.wait()
    p.log.close()
    time.sleep(1)
    return cod


def lineas_de(log, *inicios):
    return [linea for linea in log.read_text().splitlines() if linea.startswith(inicios)]


def etiqueta_nueva(inf, seguida):
    """Etiqueta nueva con la ruta del estado de origen en todos los tramos; caida a mitad del primero."""
    origen = seguida / "checkpoints" / f"{TAG}_ep010.estado.pt"
    ref = u.carpeta("caida_nueva_seguida", [ESC])
    cod = u.correr(u.RL_NUEVO, NUEVA, ref, ref / "log.txt")
    inf.chequeo("corrida seguida de 30 con la etiqueta nueva (desde cero)", cod == 0, f"codigo {cod}")
    n = u.carpeta("caida_nueva", [ESC])
    tramo_a = NUEVA + ["--reanudar", origen, "--hasta-ep", "20"]
    tramo_b = NUEVA + ["--reanudar", origen]
    inf(f"Tramo A: rl_ippo.py {' '.join(str(a) for a in NUEVA)} --reanudar <origen ep 10> --hasta-ep 20 "
        "(el B, sin --hasta-ep)")
    cod = matar_en(inf, n, tramo_a, n / "log_a1.txt", 17, TAG_N)
    estados = sorted(u.checkpoints(n, TAG_N, ".estado.pt"))
    inf.chequeo("A muerto durante el ep 18: no sale con 0; estados 5 y 10 copiados y 15 propio",
                cod != 0 and estados == [5, 10, 15], f"codigo {cod}, estados {estados}")
    cod = u.correr(u.RL_NUEVO, tramo_a, n, n / "log_a2.txt")
    log = (n / "log_a2.txt").read_text()
    inf.chequeo("A relanzado: sigue desde su estado del 15 (no copia otra vez) y corta en el 20",
                cod == 0 and "continua desde" in log and "_ep015.estado.pt" in log and "copia lo de" not in log
                and "CORTE: 20 de 30" in log, f"codigo {cod}; {lineas_de(n / 'log_a2.txt', 'corredor_ippo')}")
    repite = lineas_de(n / "log_a2.txt", "Reanudacion:", "AVISO")
    inf.chequeo("los episodios rehechos repiten los del intento muerto",
                bool(repite) and all(x.startswith("Reanudacion:") for x in repite), " | ".join(repite))
    cod = u.correr(u.RL_NUEVO, tramo_b, n, n / "log_b.txt")
    log = (n / "log_b.txt").read_text()
    inf.chequeo("B (misma ruta de origen): sigue desde su estado del 20 y publica",
                cod == 0 and "_ep020.estado.pt" in log and "Politica guardada" in log and filas(n, TAG_N) == 30,
                f"codigo {cod}, {filas(n, TAG_N)} filas")
    antes = huellas(n)
    for nombre, argumentos in (("A", tramo_a), ("B", tramo_b)):
        cod = u.correr(u.RL_NUEVO, argumentos, n, n / f"log_rel_{nombre}.txt")
        nada = lineas_de(n / f"log_rel_{nombre}.txt", "Nada que hacer")
        inf.chequeo(f"relanzar {nombre} con todo terminado: sale con 0 sin tocar nada",
                    cod == 0 and bool(nada) and huellas(n) == antes, f"codigo {cod}: {nada}")
    inf("Frente a la corrida seguida de 30 con la etiqueta nueva:")
    inf.chequeo("CSV", *u.comparar_csv_bytes(ref / f"resultados_{TAG_N}.csv", n / f"resultados_{TAG_N}.csv"))
    inf.chequeo("checkpoints", *u.comparar_checkpoints(ref, TAG_N, n, TAG_N, ("reanudado_de",)))
    pa, pb = ref / f"politica_{POL_N}.pt", n / f"politica_{POL_N}.pt"
    inf.chequeo("politica publicada (tensores)", *u.comparar_pt(pa, pb))
    inf.chequeo("meta publicado", *u.comparar_json(pa.with_suffix(".json"), pb.with_suffix(".json"),
                                                   ("reanudado_de", "reanudaciones")))
    reanudaciones(inf, pb.with_suffix(".json"), [15])
    ea, eb = u.checkpoints(ref, TAG_N, ".estado.pt"), u.checkpoints(n, TAG_N, ".estado.pt")
    for ep in (15, 20, 25, 30):
        inf.chequeo(f"estado del ep {ep}", *u.comparar_estados(ea[ep], eb[ep], ("origen", "archivos", "tramos",
                                                                                 "reanudaciones")))


def reanudaciones(inf, ruta_meta, partidas):
    """B22 en el meta publicado: un registro por relanzamiento (partida = estado desde el que siguio), todos sin
    diferencias; y ningun checkpoints/<tag>_rehechos.json (solo se escribe si algo no repite)."""
    with open(ruta_meta, encoding="utf-8") as f:
        regs = json.load(f).get("reanudaciones", [])
    inf.chequeo("meta['reanudaciones']: un registro por relanzamiento, todos repetidos",
                [r["partida"] for r in regs] == partidas and all(r["filas"] >= 1 and not r["distintos"] for r in regs),
                f"{regs}")
    rehechos = sorted(p.name for p in (ruta_meta.parent / "checkpoints").glob("*_rehechos.json"))
    inf.chequeo("sin checkpoints/*_rehechos.json", not rehechos, f"{rehechos}")


def main():
    inf = u.Informe("prueba_caida", "--reanudar auto con caidas (taskkill /F /T) a mitad de cada tramo: V2 en P1, "
                    "base 7, 20 episodios en dos tramos (--hasta-ep 10 y final), validacion cada 5 en " + u.VAL_HUMO)
    seguida = u.carpeta("caida_seguida", [ESC])
    cod = u.correr(u.RL_NUEVO, COMANDO, seguida, seguida / "log.txt")
    inf.chequeo("corrida seguida (el mismo comando, sin --hasta-ep ni caidas)", cod == 0, f"codigo {cod}")
    c = u.carpeta(f"caida_{ESC}", [ESC])
    inf(f"Comando de cada tramo: rl_ippo.py {' '.join(TRAMO1)}  (el segundo, sin --hasta-ep)")
    inf("")
    inf("Tramo 1, primer intento (sin estados: empieza de cero), muerto durante el episodio 8")
    cod = matar_en(inf, c, TRAMO1, c / "log_t1_a.txt", 7)
    estados = sorted(u.checkpoints(c, TAG, ".estado.pt"))
    inf.chequeo("el intento muerto no sale con 0 y deja el estado del 5, no el del 10",
                cod != 0 and estados == [5], f"codigo {cod}, estados {estados}, {filas(c)} filas")
    inf.chequeo("empezo de cero", "no tiene estados; empieza de cero" in (c / "log_t1_a.txt").read_text())
    inf("Tramo 1, relanzado con el mismo comando")
    cod = u.correr(u.RL_NUEVO, TRAMO1, c, c / "log_t1_b.txt")
    log = (c / "log_t1_b.txt").read_text()
    inf.chequeo("sale con 0, sigue desde el estado del 5 y llega al 10", cod == 0 and "_ep005.estado.pt" in log
                and "CORTE: 10 de 20" in log and filas(c) == 10, f"codigo {cod}, {filas(c)} filas")
    repite = [l for l in log.splitlines() if l.startswith(("Reanudacion:", "AVISO"))]
    inf.chequeo("los episodios rehechos repiten los del intento muerto",
                bool(repite) and all(l.startswith("Reanudacion:") for l in repite), " | ".join(repite))
    inf.chequeo("no publica la politica", not (c / f"politica_{POL}.pt").exists())
    antes = huellas(c)
    cod = u.correr(u.RL_NUEVO, TRAMO1, c, c / "log_t1_c.txt")
    inf.chequeo("relanzar el tramo 1 ya hecho: sale con 0 sin tocar nada",
                cod == 0 and "Nada que hacer" in (c / "log_t1_c.txt").read_text() and huellas(c) == antes,
                f"codigo {cod}")
    inf("")
    inf("Tramo 2, primer intento, muerto durante el episodio 18")
    cod = matar_en(inf, c, TRAMO2, c / "log_t2_a.txt", 17)
    estados = sorted(u.checkpoints(c, TAG, ".estado.pt"))
    inf.chequeo("el intento muerto no sale con 0 y deja los estados hasta el 15", cod != 0 and estados == [5, 10, 15],
                f"codigo {cod}, estados {estados}, {filas(c)} filas")
    inf("Tramo 2, relanzado con el mismo comando")
    cod = u.correr(u.RL_NUEVO, TRAMO2, c, c / "log_t2_b.txt")
    log = (c / "log_t2_b.txt").read_text()
    inf.chequeo("sale con 0, sigue desde el estado del 15 y publica", cod == 0 and "_ep015.estado.pt" in log and
                "Politica guardada" in log and filas(c) == 20, f"codigo {cod}, {filas(c)} filas")
    repite = [l for l in log.splitlines() if l.startswith(("Reanudacion:", "AVISO"))]
    inf.chequeo("los episodios rehechos repiten los del intento muerto",
                bool(repite) and all(l.startswith("Reanudacion:") for l in repite), " | ".join(repite))
    antes = huellas(c)
    for nombre, argumentos in (("tramo 2", TRAMO2), ("tramo 1", TRAMO1)):
        cod = u.correr(u.RL_NUEVO, argumentos, c, c / f"log_rel_{nombre[-1]}.txt")
        texto = (c / f"log_rel_{nombre[-1]}.txt").read_text()
        inf.chequeo(f"relanzar el {nombre} con todo terminado: sale con 0 sin tocar nada",
                    cod == 0 and "Nada que hacer" in texto and huellas(c) == antes,
                    f"codigo {cod}: {[l for l in texto.splitlines() if 'Nada' in l]}")
    inf("")
    inf("Frente a la corrida seguida (mismo comando sin cortes ni caidas)")
    inf.chequeo("CSV", *u.comparar_csv_bytes(seguida / f"resultados_{TAG}.csv", c / f"resultados_{TAG}.csv"))
    inf.chequeo("checkpoints", *u.comparar_checkpoints(seguida, TAG, c, TAG))
    pa, pb = seguida / f"politica_{POL}.pt", c / f"politica_{POL}.pt"
    inf.chequeo("politica publicada (bytes)", u.sha256(pa) == u.sha256(pb))
    inf.chequeo("meta publicado (salvo reanudaciones)", *u.comparar_json(pa.with_suffix(".json"),
                                                                         pb.with_suffix(".json"), ("reanudaciones",)))
    reanudaciones(inf, pb.with_suffix(".json"), [5, 15])
    ea, eb = u.checkpoints(seguida, TAG, ".estado.pt"), u.checkpoints(c, TAG, ".estado.pt")
    for ep in (5, 10, 15, 20):
        inf.chequeo(f"estado del ep {ep}", *u.comparar_estados(ea[ep], eb[ep], ("tramos", "reanudaciones")))
    restos = sorted(p.name for p in (c / "checkpoints").glob("*.tmp")) + sorted(p.name for p in c.glob("*.tmp"))
    inf.chequeo("no quedan temporales a medio escribir (.tmp)", not restos, f"{restos}")
    inf("")
    inf("Etiqueta nueva p3prbcaidan desde el estado del ep 10 de la corrida seguida (30 episodios, horizonte 20, "
        "piso 0.1)")
    etiqueta_nueva(inf, seguida)
    return inf.cerrar()


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
