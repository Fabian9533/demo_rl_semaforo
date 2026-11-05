"""
prueba_robustez.py - Arreglos de robustez de rl_ippo.py (revision del 05.11.2026 sobre la tarea 1.2 del plan 3).
Informe: plan3/doc/informe_ent1.md, seccion 7.

Corridas cortas en P1 (corredor): V2 con estado y registro, base 7, 6 episodios con validacion cada 2 en 424301-424302.
La referencia es el mismo comando seguido, sin cortes ni danos.
  R1. Estados danados con --reanudar auto: uno con una pieza del zip alterada (torch.load no lo nota; testzip si) y
      otro cuyo checkpoint ya no tiene su sha256. Se apartan a .roto con un AVISO, sin borrarlos; sigue desde el estado
      anterior y termina igual que la referencia. Un estado de otra configuracion no se aparta: sale con error.
  R2. Etiqueta nueva con la ruta del estado de origen (8 episodios, horizonte 6, piso 0.1): el estado propio mas
      avanzado truncado (0 bytes): sigue desde el propio anterior; todos los propios danados: copia otra vez del
      origen. Termina igual que la corrida seguida de 8 con esa etiqueta.
  R3. CSV tomado por otro programa (CreateFileW): un tramo intermedio avisa, sigue con el CSV en memoria y sale con 0;
      el ultimo tramo espera a que se libere, lo escribe y publica. Igual que la referencia.
  R4. B22: un episodio rehecho que no repite el intento anterior (fila alterada en el CSV): AVISO, sale con 0,
      checkpoints/<tag>_rehechos.json y meta["reanudaciones"] con el detalle.
  R5. Procedencia: el ultimo tramo corre con otra copia del codigo (un comentario de mas): AVISO de otro codigo y
      meta["tramos"] con las dos huellas, con los mismos numeros.
  R6. validar_args (en el proceso, despues de con_escenarios.registrar()) y --validar-args: argumentos buenos y malos,
      sin escribir nada ni cambiar HIPER.
  R7. Escrituras atomicas (en el proceso): el .pt con los bytes de un torch.save directo, primero el .json y despues
      el .pt, reintento con el destino tomado y, si el escritor falla, el archivo anterior queda entero.

Uso:  python plan3/pruebas/ent/prueba_robustez.py   (hasta 2 procesos a la vez, ~12 min)
Salida: plan3/pruebas/ent/salidas/prueba_robustez.txt; corridas en plan3/tmp_ent/rob_*.
"""
import io
import csv
import sys
import json
import time
import shutil
import struct
import zipfile
import threading
import contextlib
import ctypes
from ctypes import wintypes

import torch

import util_ent as u

ESC = "corredor"
TAG, POL = f"{ESC}_ippo_vecinos_p3rob_s7", f"{ESC}_vecinos_p3rob_s7"
TAG_N, POL_N = f"{ESC}_ippo_vecinos_p3robn_s7", f"{ESC}_vecinos_p3robn_s7"
AUTO = ["--reanudar", "auto"]


def comando(episodios=6, etiqueta="p3rob", extra=(), v2=("--v2",)):
    return (["train", "--escenario", ESC, "--seed", "7", "--episodios", str(episodios), "--eval-cada", "2",
             "--val-seeds", u.VAL_HUMO] + list(v2) + ["--criterio-val", "total", "--etiqueta", etiqueta,
                                                      "--guardar-estado", "--registro-extendido"] + list(extra))


COM = comando()
NUEVA = comando(8, "p3robn", ["--lr-horizonte", "6", "--lr-piso", "0.1"])


# ---------------- Ayudas ----------------
_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_k32.CreateFileW.restype = wintypes.HANDLE
_k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
                             wintypes.DWORD, wintypes.HANDLE]
_k32.CloseHandle.argtypes = [wintypes.HANDLE]


def tomar(ruta, compartir=0):
    """Abre ruta con CreateFileW como otro programa: compartir 0 = nadie mas puede abrirlo; 1 = solo leerlo (Excel).
    Devuelve la funcion que lo suelta."""
    h = _k32.CreateFileW(str(ruta), 0x80000000, compartir, None, 3, 0x80, None)     # GENERIC_READ, OPEN_EXISTING
    if h is None or h == ctypes.c_void_p(-1).value:
        raise OSError(ctypes.get_last_error(), f"no se pudo tomar {ruta}")
    return lambda: _k32.CloseHandle(h)


def danar_dentro(ruta):
    """Invierte un byte en medio de los datos de la pieza de tensores mas grande del zip; el directorio queda intacto.
    Devuelve el nombre de la pieza."""
    with zipfile.ZipFile(ruta) as z:
        info = max((i for i in z.infolist() if "/data/" in i.filename), key=lambda i: i.compress_size)
    with open(ruta, "r+b") as f:
        f.seek(info.header_offset)
        cabecera = f.read(30)
        n, m = struct.unpack("<HH", cabecera[26:30])
        pos = info.header_offset + 30 + n + m + info.compress_size // 2
        f.seek(pos)
        b = f.read(1)
        f.seek(pos)
        f.write(bytes([b[0] ^ 0xFF]))
    return info.filename


def log_de(c, nombre):
    return (c / nombre).read_text(encoding="utf-8", errors="replace")


def avisos(texto):
    return [linea for linea in texto.splitlines() if linea.startswith("AVISO")]


def huellas(c):
    return {str(p.relative_to(c)): u.sha256(p) for p in sorted(c.rglob("*"))
            if p.is_file() and not p.name.startswith("log")}


def estados(c, tag=TAG):
    return sorted(u.checkpoints(c, tag, ".estado.pt"))


def meta_de(c, pol=POL):
    with open(c / f"politica_{pol}.json", encoding="utf-8") as f:
        return json.load(f)


def frente_a_referencia(inf, ref, c, tag=TAG, pol=POL, ignorar_json=("reanudaciones",),
                        ignorar_estado=("tramos", "reanudaciones"), eps=(2, 4, 6), bytes_politica=True,
                        ignorar_checkpoints=()):
    inf.chequeo("CSV", *u.comparar_csv_bytes(ref / f"resultados_{tag}.csv", c / f"resultados_{tag}.csv"))
    inf.chequeo("checkpoints", *u.comparar_checkpoints(ref, tag, c, tag, ignorar_checkpoints))
    pa, pb = ref / f"politica_{pol}.pt", c / f"politica_{pol}.pt"
    inf.chequeo("politica publicada (tensores)", *u.comparar_pt(pa, pb))
    if bytes_politica:
        inf.chequeo("politica publicada (bytes)", u.sha256(pa) == u.sha256(pb))
    inf.chequeo("meta publicado", *u.comparar_json(pa.with_suffix(".json"), pb.with_suffix(".json"), ignorar_json))
    ea, eb = u.checkpoints(ref, tag, ".estado.pt"), u.checkpoints(c, tag, ".estado.pt")
    for ep in eps:
        if ep not in ea or ep not in eb:
            inf.chequeo(f"estado del ep {ep}", False, f"falta ({sorted(ea)} | {sorted(eb)})")
        else:
            inf.chequeo(f"estado del ep {ep}", *u.comparar_estados(ea[ep], eb[ep], ignorar_estado))
    restos = sorted(p.name for p in (c / "checkpoints").glob("*.tmp")) + sorted(p.name for p in c.glob("*.tmp"))
    inf.chequeo("no quedan temporales (.tmp)", not restos, f"{restos}")


# ---------------- R1: estados danados con auto ----------------
def r1(inf, ref):
    inf("R1. Estados danados con --reanudar auto (misma etiqueta)")
    c = u.carpeta("rob_r1", [ESC])
    t1 = COM + AUTO + ["--hasta-ep", "4"]
    cod = u.correr(u.RL_NUEVO, t1, c, c / "log_1.txt")
    inf.chequeo("tramo 1 (--hasta-ep 4)", cod == 0 and estados(c) == [2, 4], f"codigo {cod}, estados {estados(c)}")
    e4 = c / "checkpoints" / f"{TAG}_ep004.estado.pt"
    pieza = danar_dentro(e4)
    try:
        torch.load(e4, weights_only=True)
        carga = "torch.load lo carga sin error"
    except Exception as e:
        carga = f"torch.load falla ({type(e).__name__})"
    with zipfile.ZipFile(e4) as z:
        malo = z.testzip()
    inf.chequeo("estado del ep 4 con un byte cambiado en una pieza de tensores: testzip lo detecta", malo == pieza,
                f"pieza {pieza}; {carga}; testzip -> {malo}")
    cod = u.correr(u.RL_NUEVO, t1, c, c / "log_2.txt")
    log = log_de(c, "log_2.txt")
    roto = c / "checkpoints" / f"{TAG}_ep004.estado.pt.roto"
    inf.chequeo("relanzado: AVISO, el danado queda como .roto y sigue desde el estado del 2",
                cod == 0 and any("no pasa su CRC" in a and ".roto" in a for a in avisos(log)) and roto.exists()
                and "_ep002.estado.pt (episodio 2" in log and "CORTE: 4 de 6" in log,
                f"codigo {cod}; {avisos(log)}")
    inf.chequeo("los episodios rehechos (3-4) repiten el intento anterior",
                "Reanudacion: los episodios 3-4 repiten" in log)
    with open(c / "checkpoints" / f"{TAG}_ep004.pt", "ab") as f:           # el checkpoint que anota el estado del 4
        f.write(b"\0")
    cod = u.correr(u.RL_NUEVO, COM + AUTO, c, c / "log_3.txt")
    log = log_de(c, "log_3.txt")
    inf.chequeo("checkpoint del 4 alterado: el estado del 4 queda como .roto2 y sigue desde el del 2; publica",
                cod == 0 and any("no es el que escribio" in a and ".roto2" in a for a in avisos(log))
                and (c / "checkpoints" / f"{TAG}_ep004.estado.pt.roto2").exists()
                and "_ep002.estado.pt (episodio 2" in log and "Politica guardada" in log,
                f"codigo {cod}; {avisos(log)}")
    inf.chequeo("los .roto siguen ahi (no se borran)", roto.exists())
    antes = huellas(c)
    otra = comando(v2=("--solo-descuento",)) + AUTO
    cod = u.correr(u.RL_NUEVO, otra, c, c / "log_4.txt")
    log = log_de(c, "log_4.txt")
    inf.chequeo("auto con otra configuracion (--solo-descuento): sale con error sin apartar ni tocar nada",
                cod != 0 and "otra configuracion" in log and huellas(c) == antes,
                f"codigo {cod}; {[l for l in log.splitlines() if 'reanudar' in l][:1]}")
    inf("Frente a la referencia:")
    frente_a_referencia(inf, ref, c)
    meta = meta_de(c)
    inf.chequeo("meta: reanudaciones = la del ultimo relanzamiento (3-4 repetidos)",
                meta.get("reanudaciones") == [{"partida": 2, "episodios": [3, 4], "filas": 2, "distintos": []}],
                f"{meta.get('reanudaciones')}")
    inf.chequeo("sin rehechos.json (todo repitio)", not (c / "checkpoints" / f"{TAG}_rehechos.json").exists())


# ---------------- R2: etiqueta nueva con estados propios danados ----------------
def r2(inf, ref, refn):
    inf("R2. Etiqueta nueva desde el estado del ep 2 de la referencia (8 episodios, horizonte 6, piso 0.1)")
    c = u.carpeta("rob_r2", [ESC])
    origen = ref / "checkpoints" / f"{TAG}_ep002.estado.pt"
    a = NUEVA + ["--reanudar", origen, "--hasta-ep", "6"]
    b = NUEVA + ["--reanudar", origen]
    cod = u.correr(u.RL_NUEVO, a, c, c / "log_a1.txt")
    inf.chequeo("tramo A (--hasta-ep 6): copia el 2 y escribe estados propios 4 y 6",
                cod == 0 and estados(c, TAG_N) == [2, 4, 6], f"codigo {cod}, estados {estados(c, TAG_N)}")
    e4, e6 = (c / "checkpoints" / f"{TAG_N}_ep{ep:03d}.estado.pt" for ep in (4, 6))
    e6.write_bytes(b"")
    cod = u.correr(u.RL_NUEVO, a, c, c / "log_a2.txt")
    log = log_de(c, "log_a2.txt")
    inf.chequeo("estado propio del 6 truncado (0 bytes): AVISO, .roto y sigue desde el propio del 4 (no copia)",
                cod == 0 and any("_ep006.estado.pt no sirve" in x for x in avisos(log))
                and "continua desde" in log and "_ep004.estado.pt" in log and "copia lo de" not in log
                and "CORTE: 6 de 8" in log, f"codigo {cod}; {avisos(log)}")
    inf.chequeo("los episodios rehechos (5-6) repiten", "Reanudacion: los episodios 5-6 repiten" in log)
    e6.write_bytes(b"")
    danar_dentro(e4)
    cod = u.correr(u.RL_NUEVO, a, c, c / "log_a3.txt")
    log = log_de(c, "log_a3.txt")
    inf.chequeo("propios del 4 y del 6 danados: los aparta y copia otra vez del origen",
                cod == 0 and len(avisos(log)) >= 2 and "copia lo de" in log and "CORTE: 6 de 8" in log
                and (c / "checkpoints" / f"{TAG_N}_ep006.estado.pt.roto2").exists()
                and (c / "checkpoints" / f"{TAG_N}_ep004.estado.pt.roto").exists(),
                f"codigo {cod}; {avisos(log)}")
    inf.chequeo("los episodios rehechos (3-6) repiten", "Reanudacion: los episodios 3-6 repiten" in log)
    cod = u.correr(u.RL_NUEVO, b, c, c / "log_b.txt")
    log = log_de(c, "log_b.txt")
    inf.chequeo("tramo B (misma ruta de origen): sigue desde su estado del 6 y publica",
                cod == 0 and "_ep006.estado.pt" in log and "Politica guardada" in log, f"codigo {cod}")
    inf("Frente a la corrida seguida de 8 con la etiqueta nueva:")
    frente_a_referencia(inf, refn, c, TAG_N, POL_N, ignorar_json=("reanudado_de", "reanudaciones"),
                        ignorar_estado=("origen", "archivos", "tramos", "reanudaciones"), eps=(4, 6, 8),
                        bytes_politica=False, ignorar_checkpoints=("reanudado_de",))


# ---------------- R3: CSV tomado ----------------
def r3(inf, ref):
    inf("R3. CSV tomado por otro programa")
    c = u.carpeta("rob_r3", [ESC])
    ruta_csv = c / f"resultados_{TAG}.csv"
    ruta_csv.write_text("tomado\n", newline="")
    soltar = tomar(ruta_csv, 0)
    try:
        cod = u.correr(u.RL_NUEVO, COM + AUTO + ["--hasta-ep", "2"], c, c / "log_1.txt")
    finally:
        soltar()
    log = log_de(c, "log_1.txt")
    est = torch.load(c / "checkpoints" / f"{TAG}_ep002.estado.pt", weights_only=True) if estados(c) else {}
    inf.chequeo("tramo intermedio con el CSV tomado (sin compartir): avisa, sigue en memoria y sale con 0",
                cod == 0 and any("no se puede escribir" in a for a in avisos(log))
                and any("sigue tomado" in a for a in avisos(log)) and "CORTE: 2 de 6" in log,
                f"codigo {cod}; {avisos(log)}")
    inf.chequeo("el CSV en disco no cambio y el estado del 2 guarda las 2 filas",
                ruta_csv.read_text() == "tomado\n" and est.get("csv", "").count("\r\n") == 3,
                f"{est.get('csv', '').count(chr(10)) - 1} filas en el estado")
    cod = u.correr(u.RL_NUEVO, COM + AUTO + ["--hasta-ep", "4"], c, c / "log_2.txt")
    filas = ruta_csv.read_text().count("\n") - 1
    inf.chequeo("tramo siguiente ya sin tomar: reescribe el CSV desde el estado (filas 1-4)",
                cod == 0 and filas == 4, f"codigo {cod}, {filas} filas")
    soltar = tomar(ruta_csv, 1)
    p = u.lanzar(u.RL_NUEVO, COM + AUTO, c, c / "log_3.txt")
    t0 = time.time()
    try:
        while p.poll() is None and "se reintenta cada" not in log_de(c, "log_3.txt") and time.time() - t0 < 900:
            time.sleep(0.5)
        espera = time.time() - t0
        time.sleep(3)
    finally:
        soltar()
    cod = p.wait()
    p.log.close()
    log = log_de(c, "log_3.txt")
    inf.chequeo("ultimo tramo con el CSV tomado (solo lectura, como Excel): espera, lo escribe al soltarlo y publica",
                cod == 0 and "escrito al final del tramo (intento" in log and "Politica guardada" in log,
                f"codigo {cod}; aviso de espera a los {espera:.0f} s; {avisos(log)}")
    inf("Frente a la referencia:")
    frente_a_referencia(inf, ref, c)
    inf.chequeo("meta sin reanudaciones (ningun episodio rehecho)", "reanudaciones" not in meta_de(c))


# ---------------- R4: B22 ----------------
def r4(inf, ref):
    inf("R4. B22: un episodio rehecho que no repite el intento anterior")
    c = u.carpeta("rob_r4", [ESC])
    t1 = COM + AUTO + ["--hasta-ep", "4"]
    cod = u.correr(u.RL_NUEVO, t1, c, c / "log_1.txt")
    ruta_csv = c / f"resultados_{TAG}.csv"
    with open(ruta_csv, newline="") as f:
        filas = list(csv.reader(f))
    i = filas[0].index("timeloss_prom")
    filas[3][i] += "1"                                      # la fila del episodio 3 del "intento anterior"
    with open(ruta_csv, "w", newline="") as f:
        csv.writer(f).writerows(filas)
    (c / "checkpoints" / f"{TAG}_ep004.estado.pt").unlink()  # caida despues de la fila 4 y antes de su estado
    cod2 = u.correr(u.RL_NUEVO, t1, c, c / "log_2.txt")
    log = log_de(c, "log_2.txt")
    ruta_r = c / "checkpoints" / f"{TAG}_rehechos.json"
    inf.chequeo("relanzado: AVISO del episodio 3 y sale con 0",
                cod == 0 and cod2 == 0 and "AVISO: el episodio 3 no repite el intento anterior (timeloss_prom)" in log
                and "1 de los 2 episodios rehechos (3-4)" in log, f"codigos {cod}, {cod2}; {avisos(log)}")
    rehechos = json.loads(ruta_r.read_text(encoding="utf-8")) if ruta_r.exists() else []
    esperado = {"partida": 2, "episodios": [3, 4], "filas": 2, "distintos": [[3, ["timeloss_prom"]]]}
    inf.chequeo("checkpoints/<tag>_rehechos.json con el detalle",
                len(rehechos) == 1 and {k: rehechos[0].get(k) for k in esperado} == esperado
                and rehechos[0].get("tag") == TAG and rehechos[0].get("codigo"),
                f"{[{k: v for k, v in r.items() if k != 'codigo'} for r in rehechos]}")
    cod = u.correr(u.RL_NUEVO, COM + AUTO, c, c / "log_3.txt")
    meta = meta_de(c)
    inf.chequeo("ultimo tramo: publica con meta['reanudaciones'] = esa comparacion",
                cod == 0 and meta.get("reanudaciones") == [esperado], f"codigo {cod}; {meta.get('reanudaciones')}")
    e6 = torch.load(c / "checkpoints" / f"{TAG}_ep006.estado.pt", weights_only=True)
    inf.chequeo("el estado final tambien la guarda", e6.get("reanudaciones") == [esperado])
    inf.chequeo("CSV final = el de la referencia (la fila rehecha reemplaza a la alterada)",
                *u.comparar_csv_bytes(ref / f"resultados_{TAG}.csv", ruta_csv))


# ---------------- R5: procedencia ----------------
def r5(inf, ref):
    inf("R5. Procedencia: el ultimo tramo con otra copia del codigo (un comentario de mas)")
    c = u.carpeta("rob_r5", [ESC])
    mod = u.TMP / "codigo_mod"
    if mod.exists():
        shutil.rmtree(mod)
    mod.mkdir(parents=True)
    for f in u.ARCHIVOS_TAG:
        shutil.copyfile(u.RAIZ / f, mod / f)
    with open(mod / "rl_ippo.py", "a", encoding="utf-8") as f:
        f.write("\n# copia de prueba (prueba_robustez R5): mismo codigo con un comentario de mas\n")
    cod1 = u.correr(u.RL_NUEVO, COM + AUTO + ["--hasta-ep", "2"], c, c / "log_1.txt")
    cod2 = u.correr(mod / "rl_ippo.py", COM + AUTO, c, c / "log_2.txt")
    log = log_de(c, "log_2.txt")
    inf.chequeo("los dos tramos salen con 0 y el segundo avisa que el codigo es otro",
                cod1 == 0 and cod2 == 0 and any("otro codigo" in a for a in avisos(log)),
                f"codigos {cod1}, {cod2}; {avisos(log)}")
    meta = meta_de(c)
    tramos = meta.get("tramos") or []
    inf.chequeo("meta['tramos']: 1-2 y 3-6 con huellas distintas",
                [(t["desde"], t["hasta"]) for t in tramos] == [(1, 2), (3, 6)]
                and len({t["codigo"] for t in tramos}) == 2,
                f"{[(t['desde'], t['hasta'], t['codigo'][:12]) for t in tramos]}")
    with open(c / "checkpoints" / f"{TAG}_ep002.json", encoding="utf-8") as f:
        m2 = json.load(f)
    with open(c / "checkpoints" / f"{TAG}_ep004.json", encoding="utf-8") as f:
        m4 = json.load(f)
    inf.chequeo("checkpoints: el del 2 sin tramos (un solo codigo hasta ahi); el del 4 con 1-2 y 3-4",
                "tramos" not in m2 and [(t["desde"], t["hasta"]) for t in m4.get("tramos", [])] == [(1, 2), (3, 4)],
                f"{[(t['desde'], t['hasta']) for t in m4.get('tramos', [])]}")
    inf("Mismos numeros que la referencia:")
    inf.chequeo("CSV", *u.comparar_csv_bytes(ref / f"resultados_{TAG}.csv", c / f"resultados_{TAG}.csv"))
    inf.chequeo("checkpoints", *u.comparar_checkpoints(ref, TAG, c, TAG, ("tramos",)))
    pa, pb = ref / f"politica_{POL}.pt", c / f"politica_{POL}.pt"
    inf.chequeo("politica publicada (bytes)", u.sha256(pa) == u.sha256(pb))
    inf.chequeo("meta publicado", *u.comparar_json(pa.with_suffix(".json"), pb.with_suffix(".json"), ("tramos",)))


# ---------------- R6 y R7: en el proceso ----------------
def r6(inf, rl_ippo):
    inf("R6. validar_args y --validar-args")
    c = u.carpeta("rob_r6", [ESC])
    hiper = dict(rl_ippo.HIPER)
    casos = [
        (COM + AUTO + ["--hasta-ep", "4"], None),
        (["train", "--escenario", "poi_corredor", "--v2", "--etiqueta", "p3v2poi", "--hiper", "lr=5e-4,minibatch=128"],
         None),
        (COM + ["--hasta-ep", "9"], "--hasta-ep va de 1"),
        (["train", "--hasta-ep", "4"], "necesitan --guardar-estado"),
        (["train", "--v2", "--solo-descuento"], "ya trae"),
        (["train", "--etiqueta", "P3"], "solo minusculas"),
        (["train", "--hiper", "ent=x"], "no es un numero"),
        (["train", "--hiper", "otra=1"], "clave=valor"),
        (["train", "--val-seeds", "1,a"], "enteros"),
        (["train", "--escenario", "no_existe"], "invalid choice"),
        (["train", "--opcion-que-no-existe"], "unrecognized arguments"),
        (["demo"], "necesita --politica"),
    ]
    for argv, mensaje in casos:
        err = io.StringIO()
        try:
            with contextlib.redirect_stderr(err):
                args = rl_ippo.validar_args([str(a) for a in argv])
            ok, detalle = mensaje is None, f"acepta; cambios_hiper {args.cambios_hiper}"
        except SystemExit as e:
            ultima = (err.getvalue().strip().splitlines() or [""])[-1]
            ok, detalle = mensaje is not None and e.code == 2 and mensaje in ultima, f"sale {e.code}: {ultima[:110]}"
        inf.chequeo(f"{'acepta' if mensaje is None else 'rechaza'} {' '.join(str(a) for a in argv[1:])[:70]}", ok,
                    detalle)
    inf.chequeo("HIPER y C quedan iguales", rl_ippo.HIPER == hiper and rl_ippo.C == {})
    antes = huellas(c)
    cod = u.correr(u.RL_NUEVO, COM + AUTO + ["--validar-args"], c, c / "log_1.txt")
    cod2 = u.correr(u.RL_NUEVO, COM + ["--hasta-ep", "9", "--validar-args"], c, c / "log_2.txt")
    inf.chequeo("--validar-args: bueno sale con 0 y malo con 2, sin escribir nada",
                cod == 0 and "argumentos validos" in log_de(c, "log_1.txt") and cod2 == 2 and huellas(c) == antes,
                f"codigos {cod}, {cod2}; archivos {sorted(huellas(c))}")


def r7(inf, rl_ippo):
    inf("R7. Escrituras atomicas")
    c = u.carpeta("rob_r7", [])
    torch.manual_seed(0)
    pol = rl_ippo.Politica(31)
    sd = pol.state_dict()
    (c / "directo").mkdir()
    torch.save(sd, c / "directo" / "x_ep010.pt")
    rl_ippo.guardar_pt(sd, str(c / "x_ep010.pt"))
    inf.chequeo("guardar_pt da los bytes de un torch.save directo",
                u.sha256(c / "x_ep010.pt") == u.sha256(c / "directo" / "x_ep010.pt"))
    orden, original = [], rl_ippo.reemplazar

    def anotar(tmp, destino, intentos=20):
        orden.append(destino[-5:])
        original(tmp, destino, intentos)
    rl_ippo.reemplazar = anotar
    try:
        pol.guardar(str(c / "pol_s7.pt"), {"dim_obs": 31, "ocultas": rl_ippo.OCULTAS})
    finally:
        rl_ippo.reemplazar = original
    inf.chequeo("Politica.guardar: primero el .json y despues el .pt", orden == [".json", "s7.pt"], f"{orden}")
    _, meta = rl_ippo.Politica.cargar(str(c / "pol_s7.pt"))
    inf.chequeo("y se carga", meta["dim_obs"] == 31)
    destino = c / "m.json"
    destino.write_text("viejo", encoding="utf-8")
    soltar = tomar(destino, 0)
    hilo = threading.Timer(2.0, soltar)
    t0 = time.time()
    hilo.start()
    try:
        rl_ippo.guardar_json({"nuevo": 1}, str(destino))
        ok, detalle = json.loads(destino.read_text(encoding="utf-8")) == {"nuevo": 1}, f"{time.time() - t0:.1f} s"
    except Exception as e:
        ok, detalle = False, f"{type(e).__name__}: {e}"
    hilo.join()
    inf.chequeo("destino tomado 2 s: reintenta y escribe", ok, detalle)
    z = c / "z.json"
    z.write_text("entero", encoding="utf-8")

    def falla(tmp):
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("a medi")
        raise RuntimeError("corte simulado")
    try:
        rl_ippo.escribir_atomico(str(z), falla)
        cayo = False
    except RuntimeError:
        cayo = True
    inf.chequeo("si el escritor falla, el archivo anterior queda entero", cayo and z.read_text(encoding="utf-8")
                == "entero")
    inf.chequeo("ruta_tmp: .pt -> .tmp (mismo nombre dentro del zip); lo demas + .tmp",
                rl_ippo.ruta_tmp("a/b_ep010.pt") == "a/b_ep010.tmp"
                and rl_ippo.ruta_tmp("b_ep010.estado.pt") == "b_ep010.estado.tmp"
                and rl_ippo.ruta_tmp("b.json") == "b.json.tmp")


def main():
    inf = u.Informe("prueba_robustez", "Robustez de rl_ippo.py (revision del 05.11): estados danados, copias y "
                    "publicacion atomicas, CSV tomado, B22, procedencia y validar_args. P1, V2 con estado y registro, "
                    f"base 7, validacion cada 2 en {u.VAL_HUMO}")
    sys.path.insert(0, str(u.RAIZ))
    import con_escenarios
    con_escenarios.registrar()
    import rl_ippo
    inf("")
    r6(inf, rl_ippo)
    inf("")
    r7(inf, rl_ippo)
    inf("")
    ref = u.carpeta("rob_ref", [ESC])
    refn = u.carpeta("rob_refn", [ESC])
    cods = u.en_tandas([(u.RL_NUEVO, COM, ref, ref / "log.txt"), (u.RL_NUEVO, NUEVA, refn, refn / "log.txt")],
                       maximo=2)
    inf.chequeo("referencias: el comando seguido (6 episodios) y la etiqueta nueva seguida (8)", cods == [0, 0],
                f"codigos {cods}")
    for prueba in (r1, r3, r4, r5):
        inf("")
        prueba(inf, ref)
    inf("")
    r2(inf, ref, refn)
    return inf.cerrar()


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
