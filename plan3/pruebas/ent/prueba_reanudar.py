"""
prueba_reanudar.py - Pruebas 3 y 4 de la tarea 1.2 del plan 3 (informe: plan3/doc/informe_ent1.md).

  3. 20 episodios seguidos = 10 (corte con --hasta-ep 10) + 10 reanudados con --reanudar <estado del ep 10>, con
     validacion cada 5: CSV byte a byte salvo segundos, tensores y .json de todos los checkpoints, politica publicada
     (bytes) y su meta, y los estados de los episodios 5, 10, 15 y 20 (pesos, Adam con su contador, generadores,
     series y CSV). En P1 con IPPO entregado (--guardar-estado) y con V2 (--v2 --criterio-val total
     --guardar-estado --registro-extendido); en P6 (malla3_alta), con V2.
  4. (solo P1) Etiqueta nueva: desde el estado del ep 10 de la V2 de 20 episodios, otra etiqueta con 30 episodios y
     --lr-horizonte 20 --lr-piso 0.1. Deja copiados los checkpoints y estados <= 10 y sigue igual que una corrida
     seguida con esa etiqueta y esa tasa (salvo reanudado_de en los meta).
  Rechazos (solo P1): otra tasa, otra configuracion, otras semillas de validacion, otro registro, un checkpoint
  alterado y opciones incompatibles salen con error sin escribir nada.

Uso:  python plan3/pruebas/ent/prueba_reanudar.py corredor      (P1: IPPO y V2, prueba 4 y rechazos)
      python plan3/pruebas/ent/prueba_reanudar.py malla3_alta   (P6: V2; ~2 procesos durante 20-45 min)
Salida: plan3/pruebas/ent/salidas/prueba_reanudar_<escenario>.txt; corridas en plan3/tmp_ent/rean_<esc>_*.
"""
import sys
import json
import shutil

import util_ent as u

MODOS = {   # modo: (opciones, tag, politica)
    "ippo": (["--guardar-estado"], "ippo_vecinos_s7", "vecinos_s7"),
    "v2": (["--v2", "--criterio-val", "total", "--etiqueta", "p3prbv2", "--guardar-estado", "--registro-extendido"],
           "ippo_vecinos_p3prbv2_s7", "vecinos_p3prbv2_s7"),
}


def base(esc, episodios=20):
    return ["train", "--escenario", esc, "--seed", "7", "--episodios", str(episodios), "--eval-cada", "5",
            "--val-seeds", u.VAL_HUMO]


def comparar_corridas(inf, ca, cb, tag, pol, ignorar_json=(), ignorar_estado=(), estados=(5, 10, 15, 20)):
    inf.chequeo("CSV", *u.comparar_csv_bytes(ca / f"resultados_{tag}.csv", cb / f"resultados_{tag}.csv"))
    inf.chequeo("checkpoints", *u.comparar_checkpoints(ca, tag, cb, tag, ignorar_json))
    pa, pb = ca / f"politica_{pol}.pt", cb / f"politica_{pol}.pt"
    inf.chequeo("politica publicada (tensores)", *u.comparar_pt(pa, pb))
    if not ignorar_json:
        inf.chequeo("politica publicada (bytes)", u.sha256(pa) == u.sha256(pb))
    inf.chequeo("meta publicado", *u.comparar_json(pa.with_suffix(".json"), pb.with_suffix(".json"), ignorar_json))
    ea, eb = u.checkpoints(ca, tag, ".estado.pt"), u.checkpoints(cb, tag, ".estado.pt")
    for ep in estados:
        if ep not in ea or ep not in eb:
            inf.chequeo(f"estado del ep {ep}", False, f"falta ({sorted(ea)} | {sorted(eb)})")
            continue
        inf.chequeo(f"estado del ep {ep}", *u.comparar_estados(ea[ep], eb[ep], ignorar_estado))


def prueba_tramos(inf, esc, modos):
    """Prueba 3: seguida frente a corte en 10 + reanudacion. Devuelve las carpetas de las corridas seguidas."""
    trabajos, carpetas = [], {}
    for modo in modos:
        opciones = MODOS[modo][0]
        seguida = u.carpeta(f"rean_{esc}_{modo}_seguida", [esc])
        tramos = u.carpeta(f"rean_{esc}_{modo}_tramos", [esc])
        carpetas[modo] = (seguida, tramos)
        trabajos.append((u.RL_NUEVO, base(esc) + opciones, seguida, seguida / "log.txt"))
        trabajos.append((u.RL_NUEVO, base(esc) + opciones + ["--hasta-ep", "10"], tramos, tramos / "log_tramo1.txt"))
    codigos = u.en_tandas(trabajos, maximo=3)
    segundos = []
    for modo, (seguida, tramos) in carpetas.items():
        tag, pol = f"{esc}_{MODOS[modo][1]}", f"{esc}_{MODOS[modo][2]}"
        i = list(carpetas).index(modo)
        inf(f"-- {esc}, {modo}: {' '.join(MODOS[modo][0])}")
        inf.chequeo("corrida seguida de 20", codigos[2 * i] == 0, f"codigo {codigos[2 * i]}")
        inf.chequeo("tramo 1 (--hasta-ep 10) sale con 0", codigos[2 * i + 1] == 0, f"codigo {codigos[2 * i + 1]}")
        filas = (tramos / f"resultados_{tag}.csv").read_text().splitlines()
        inf.chequeo("tramo 1: CSV con los episodios 1-10", len(filas) == 11, f"{len(filas) - 1} filas")
        inf.chequeo("tramo 1: no publica la politica", not (tramos / f"politica_{pol}.pt").exists())
        inf.chequeo("tramo 1: estados en 5 y 10", sorted(u.checkpoints(tramos, tag, ".estado.pt")) == [5, 10],
                    f"{sorted(u.checkpoints(tramos, tag, '.estado.pt'))}")
        estado10 = f"checkpoints/{tag}_ep010.estado.pt"
        segundos.append((u.RL_NUEVO, base(esc) + MODOS[modo][0] + ["--reanudar", estado10], tramos,
                         tramos / "log_tramo2.txt"))
    codigos2 = u.en_tandas(segundos, maximo=3)
    for (modo, (seguida, tramos)), cod in zip(carpetas.items(), codigos2):
        tag, pol = f"{esc}_{MODOS[modo][1]}", f"{esc}_{MODOS[modo][2]}"
        inf(f"-- {esc}, {modo}: 20 seguidos frente a 10 + 10 reanudados")
        log = (tramos / "log_tramo2.txt").read_text(encoding="utf-8")
        inf.chequeo("tramo 2 (--reanudar ep 10) sale con 0 y dice desde donde sigue",
                    cod == 0 and "Reanuda desde" in log and "misma etiqueta" in log, f"codigo {cod}")
        comparar_corridas(inf, seguida, tramos, tag, pol)
    return {modo: c[0] for modo, c in carpetas.items()}


def prueba_nueva(inf, seguida_v2):
    """Prueba 4: etiqueta nueva desde el ep 10 de la V2 de 20, con 30 episodios, horizonte 20 y piso 0.1."""
    esc = "corredor"
    origen = f"{esc}_ippo_vecinos_p3prbv2_s7"
    tag, pol = f"{esc}_ippo_vecinos_p3prbnueva_s7", f"{esc}_vecinos_p3prbnueva_s7"
    opciones = ["--v2", "--criterio-val", "total", "--etiqueta", "p3prbnueva", "--guardar-estado",
                "--registro-extendido", "--lr-horizonte", "20", "--lr-piso", "0.1"]
    nueva = u.carpeta("rean_corredor_nueva", [esc])
    seguida = u.carpeta("rean_corredor_nueva_seguida", [esc])
    estado = seguida_v2 / "checkpoints" / f"{origen}_ep010.estado.pt"
    codigos = u.en_tandas([(u.RL_NUEVO, base(esc, 30) + opciones + ["--reanudar", estado], nueva, nueva / "log.txt"),
                           (u.RL_NUEVO, base(esc, 30) + opciones, seguida, seguida / "log.txt")], maximo=2)
    inf(f"-- etiqueta nueva p3prbnueva (30 episodios, --lr-horizonte 20 --lr-piso 0.1) desde {estado.name}")
    log = (nueva / "log.txt").read_text(encoding="utf-8")
    inf.chequeo("las dos corridas salen con 0", codigos == [0, 0], f"codigos {codigos}")
    inf.chequeo("dice que es etiqueta nueva", "etiqueta nueva" in log)
    copiados = all(u.sha256(nueva / "checkpoints" / f"{tag}_ep{ep:03d}.pt") ==
                   u.sha256(seguida_v2 / "checkpoints" / f"{origen}_ep{ep:03d}.pt") for ep in (5, 10))
    inf.chequeo("checkpoints <= 10 copiados byte a byte de la de origen", copiados)
    estados = all(u.sha256(nueva / "checkpoints" / f"{tag}_ep{ep:03d}.estado.pt") ==
                  u.sha256(seguida_v2 / "checkpoints" / f"{origen}_ep{ep:03d}.estado.pt") for ep in (5, 10))
    inf.chequeo("estados <= 10 copiados de la de origen", estados)
    with open(nueva / f"politica_{pol}.json", encoding="utf-8") as f:
        meta = json.load(f)
    esperado = [{"corrida": origen, "episodio": 10}]
    inf.chequeo("meta: reanudado_de", meta.get("reanudado_de") == esperado, f"{meta.get('reanudado_de')}")
    inf.chequeo("meta: opciones de la tasa", meta["opciones"].get("lr_horizonte") == 20 and
                meta["opciones"].get("lr_piso") == 0.1, f"{meta['opciones']}")
    inf("Frente a la corrida seguida de 30 con la misma etiqueta y la misma tasa:")
    comparar_corridas(inf, nueva, seguida, tag, pol, ignorar_json=("reanudado_de",),
                      ignorar_estado=("origen", "archivos"), estados=(15, 20, 25, 30))
    ok, txt = u.comparar_columnas(nueva / f"resultados_{tag}.csv", seguida_v2 / f"resultados_{origen}.csv",
                                  ignorar=("segundos", "etiqueta"), filas=10)
    inf.chequeo("filas 1-10 = las de la V2 de origen (salvo etiqueta y segundos)", ok, txt)


def prueba_rechazos(inf, seguida_v2):
    """Opciones incompatibles o estados que no corresponden: error y ningun archivo nuevo."""
    esc = "corredor"
    origen = f"{esc}_ippo_vecinos_p3prbv2_s7"
    estado = seguida_v2 / "checkpoints" / f"{origen}_ep010.estado.pt"
    c = u.carpeta("rean_corredor_rechazos", [esc])
    v2 = ["--v2", "--criterio-val", "total", "--guardar-estado", "--registro-extendido"]
    casos = [
        ("otra tasa (--episodios 30 sin horizonte 20)", base(esc, 30) + v2 + ["--etiqueta", "p3prbmal"],
         "la tasa de esta corrida"),
        ("otra configuracion (sin --v2)", base(esc) + ["--guardar-estado", "--registro-extendido",
                                                       "--etiqueta", "p3prbmal"], "otra configuracion"),
        ("solo una mitad de V2 (--solo-descuento)", base(esc) + ["--solo-descuento", "--criterio-val", "total",
                                                                  "--guardar-estado", "--registro-extendido",
                                                                  "--etiqueta", "p3prbmal"], "otra configuracion"),
        ("otras semillas de validacion", ["train", "--escenario", esc, "--seed", "7", "--episodios", "20",
                                          "--eval-cada", "5", "--val-seeds", "424301,424303"] + v2
         + ["--etiqueta", "p3prbmal"], "otra configuracion"),
        ("otra base", ["train", "--escenario", esc, "--seed", "8", "--episodios", "20", "--eval-cada", "5",
                       "--val-seeds", u.VAL_HUMO] + v2 + ["--etiqueta", "p3prbmal"], "otra configuracion"),
        ("otro registro (sin --registro-extendido)", base(esc) + ["--v2", "--criterio-val", "total",
                                                                   "--guardar-estado", "--etiqueta", "p3prbmal"],
         "columnas que esta corrida no escribe"),
        ("--hasta-ep sin --guardar-estado", base(esc) + ["--v2", "--hasta-ep", "5", "--etiqueta", "p3prbmal"],
         "necesitan --guardar-estado"),
        ("--reanudar auto sin --guardar-estado", base(esc) + ["--v2", "--etiqueta", "p3prbmal"],
         "necesitan --guardar-estado"),
        ("--v2 con --solo-descuento", base(esc) + ["--v2", "--solo-descuento", "--etiqueta", "p3prbmal"],
         "ya trae"),
    ]
    for k, (nombre, argumentos, mensaje) in enumerate(casos):
        reanudar = ["--reanudar", "auto"] if "auto" in nombre else ([] if "--hasta-ep" in nombre or "--v2 con" in nombre
                                                                    else ["--reanudar", estado])
        log = c / f"log_rechazo{k}.txt"
        cod = u.correr(u.RL_NUEVO, argumentos + reanudar, c, log)
        texto = log.read_text(encoding="utf-8")
        escritos = sorted(p.name for p in c.rglob("*p3prbmal*"))
        inf.chequeo(f"rechaza {nombre}", cod != 0 and mensaje in texto and not escritos,
                    f"codigo {cod}; '{mensaje}' {'en' if mensaje in texto else 'NO en'} el log; "
                    f"archivos nuevos {escritos}")
    # checkpoint alterado: copia de la corrida seguida con un .json tocado
    alterada = u.carpeta("rean_corredor_alterada", [esc])
    shutil.copytree(seguida_v2 / "checkpoints", alterada / "checkpoints")
    shutil.copyfile(seguida_v2 / f"resultados_{origen}.csv", alterada / f"resultados_{origen}.csv")
    with open(alterada / "checkpoints" / f"{origen}_ep005.json", "a", encoding="utf-8") as f:
        f.write(" ")
    antes = {p.name: u.sha256(p) for p in (alterada / "checkpoints").iterdir()}
    log = alterada / "log_alterada.txt"
    cod = u.correr(u.RL_NUEVO, base(esc) + v2 + ["--etiqueta", "p3prbv2", "--reanudar",
                                                f"checkpoints/{origen}_ep010.estado.pt"], alterada, log)
    texto = log.read_text(encoding="utf-8")
    despues = {p.name: u.sha256(p) for p in (alterada / "checkpoints").iterdir()}
    inf.chequeo("rechaza un checkpoint alterado (misma etiqueta) sin borrar nada",
                cod != 0 and "no es el que escribio" in texto and antes == despues,
                f"codigo {cod}; {len(despues)} archivos sin cambios: {antes == despues}")


def main():
    esc = sys.argv[1] if len(sys.argv) > 1 else "corredor"
    p1 = esc == "corredor"
    inf = u.Informe(f"prueba_reanudar_{esc}", f"Pruebas 3{' y 4' if p1 else ''} (tarea 1.2): reanudacion exacta en "
                    f"{esc}, base 7, validacion cada 5 en {u.VAL_HUMO}")
    inf("")
    inf("Prueba 3: 20 seguidos = 10 + 10 reanudados")
    seguidas = prueba_tramos(inf, esc, ["ippo", "v2"] if p1 else ["v2"])
    if p1:
        inf("")
        inf("Prueba 4: etiqueta nueva")
        prueba_nueva(inf, seguidas["v2"])
        inf("")
        inf("Rechazos")
        prueba_rechazos(inf, seguidas["v2"])
    return inf.cerrar()


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
