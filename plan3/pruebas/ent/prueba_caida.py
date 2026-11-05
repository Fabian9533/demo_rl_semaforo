"""
prueba_caida.py - --reanudar auto con caidas de verdad (tarea 1.2 del plan 3, pedido del 05.11; DECISIONES B22).
Informe: plan3/doc/informe_ent1.md.

Un mismo comando, con --reanudar auto, en dos tramos (--hasta-ep 10 y hasta el final, 20 episodios), V2 en P1,
base 7, validacion cada 5 en 424301-424302. En cada tramo se mata el proceso a mitad de un episodio con
taskkill /F /T y se relanza el mismo comando: debe seguir desde el ultimo estado, repetir los episodios que el
intento caido alcanzo a escribir y terminar igual que la corrida seguida de prueba_reanudar.py (CSV salvo segundos,
checkpoints, politica publicada y estados). Relanzar un tramo ya hecho (o la corrida ya publicada) sale con 0 sin
tocar ningun archivo.

Uso:  python plan3/pruebas/ent/prueba_caida.py   (despues de prueba_reanudar.py corredor, que deja la seguida)
Salida: plan3/pruebas/ent/salidas/prueba_caida.txt; corrida en plan3/tmp_ent/caida_corredor.
"""
import sys
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


def filas(c):
    ruta = c / f"resultados_{TAG}.csv"
    if not ruta.exists():
        return 0
    with open(ruta, newline="") as f:
        return max(0, f.read().count("\r\n") - 1)


def huellas(c):
    """sha256 de cada archivo de la carpeta (menos los logs): para ver que un relanzamiento no toca nada."""
    return {str(p.relative_to(c)): u.sha256(p) for p in sorted(c.rglob("*"))
            if p.is_file() and not p.name.startswith("log")}


def matar_en(inf, c, argumentos, log, filas_objetivo):
    """Lanza, espera a que el CSV tenga filas_objetivo filas y mata el arbol de procesos (python y sumo)."""
    p = u.lanzar(u.RL_NUEVO, argumentos, c, log)
    while p.poll() is None and filas(c) < filas_objetivo:
        time.sleep(0.2)
    if p.poll() is None:
        r = subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True, text=True)
        inf(f"   taskkill /F /T /PID {p.pid} con {filas(c)} filas escritas: {r.stdout.strip()[:120]}")
    cod = p.wait()
    p.log.close()
    time.sleep(1)
    return cod


def main():
    inf = u.Informe("prueba_caida", "--reanudar auto con caidas (taskkill /F /T) a mitad de cada tramo: V2 en P1, "
                    "base 7, 20 episodios en dos tramos (--hasta-ep 10 y final), validacion cada 5 en " + u.VAL_HUMO)
    seguida = u.TMP / f"rean_{ESC}_v2_seguida"
    if not (seguida / f"politica_{POL}.pt").exists():
        inf("La corrida seguida no existe: la corro (mismo comando sin --reanudar auto).")
        s = u.carpeta(f"rean_{ESC}_v2_seguida", [ESC])
        u.correr(u.RL_NUEVO, COMANDO[:-2], s, s / "log.txt")
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
    inf.chequeo("meta publicado", *u.comparar_json(pa.with_suffix(".json"), pb.with_suffix(".json")))
    ea, eb = u.checkpoints(seguida, TAG, ".estado.pt"), u.checkpoints(c, TAG, ".estado.pt")
    for ep in (5, 10, 15, 20):
        inf.chequeo(f"estado del ep {ep}", *u.comparar_estados(ea[ep], eb[ep]))
    restos = sorted(p.name for p in (c / "checkpoints").glob("*.tmp"))
    inf.chequeo("no quedan estados a medio escribir (.tmp)", not restos, f"{restos}")
    return inf.cerrar()


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
