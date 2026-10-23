"""tablas_cap5.py - Tablas tab:plan2-resumen y tab:plan2-metas del Cap. V.

Uso (desde demo_rl/plan2):  python tablas_cap5.py [--modelo ippo_vecinos]
                            [--metrica M] [--fijo BRAZO] [--prefijo P] [--casos P1-P5] [--sin-trivial]
  principal (28.09.2026): python tablas_cap5.py --metrica timeloss_prom --fijo fijo_2509 --sin-trivial
  robustez:               python tablas_cap5.py --prefijo robustez_
Escribe TESIS/secciones/tablas/plan2_resumen.tex y plan2_metas.tex (el Cap. V las incluye con \\input).

tab:plan2-resumen: retraso del fijo por caso y, por modelo y caso, retraso de la base publicada,
Delta vs fijo y veredicto abreviado. Fuente: plan2/veredicto.csv (veredicto.py; metrica primaria
veredicto.METRICA, el retraso total desde el 27.09.2026) y la fila del fijo de
plan2/evaluacion_<esc>_resumen.csv.

tab:plan2-metas: Delta (%) frente al fijo de la base publicada de un modelo (por defecto IPPO vecinos) en
las cuatro metricas con meta de la introduccion. Fuente: plan2/evaluacion_<esc>_resumen.csv (delta_pct);
base publicada de plan2/veredicto.csv.

Formato de numeros igual que veredicto.py: retraso con 2 decimales, deltas con '{:+.1f}'.
No recalcula nada: solo lee y formatea. Cambios del 27.09.2026: lee el veredicto vigente (antes el
congelado de las 03:55), metrica primaria de veredicto.py, casos P1-P6, fila del control trivial y
marca * de las politicas iguales al trivial; escribe los archivos en vez de imprimirlos.

Cambios del 28.09.2026 (sin opciones, todo queda como antes): las opciones de veredicto.py.
  --metrica, --fijo BRAZO  la fila del fijo y los deltas salen del resumen frente a BRAZO
                           (evaluacion_<esc>_resumen_<BRAZO>.csv; fijo_2509 = el fijo del 25.09).
  --prefijo P              lee plan2/<P>veredicto.csv y escribe <P>plan2_resumen.tex y <P>plan2_metas.tex,
                           con labels tab:<P sin _>-plan2-... y el prefijo al inicio de los titulos.
  --casos, --sin-trivial   solo esos casos; sin la fila del control trivial.
  Con timeLoss, los titulos son los del 25.09 (retraso = timeLoss). Una celda sin comparacion con el
  fijo todavia (P6 mientras corre su barrido) se escribe "pendiente" y el archivo lleva un comentario
  % PENDIENTE-<caso>.

Cambios de la entrega 3 (23.10.2026), solo en los textos de los .tex (mismas cifras, CSV sin cambios):
  nombres del glosario de la tesis (IPPO con mensajes, IPPO sin mensajes, IPPO con penalizacion, Q-learning
  (colas), ciclo minimo, fijo ajustado, fijo ajustado desde 10 s en la robustez, version evaluada); notas en
  palabras ("igual a IPPO con mensajes" e "igual al ciclo minimo" en lugar de "= vecinos" y la marca *);
  encabezados de los casos con la red y la demanda, como la matriz de veredicto.py; y el PEN con su provisional
  en una linea aparte de la celda, porque la tabla se salia del margen (unos 31 pt; 43 pt en la robustez).
  Despues de la reduccion del Anexo F (23.10.2026), con --prefijo robustez_ la ultima frase del caption de
  tab:robustez-plan2-resumen remite a la tabla por modelo de IPPO con mensajes y a plan2/robustez_veredicto.csv
  (remision_detalle); la version principal no cambia.
  Verificacion de las tareas 4 y 5 (23.10.2026): el retraso de cada modelo se redondea una sola vez, desde la media
  de evaluacion_<esc>_resumen*.csv (media_cruda). Antes se tomaba de veredicto.csv, que lo guarda con 3 decimales,
  y al pasarlo a 2 salian 4 celdas de la robustez distintas de las tablas por modelo (DQN en P1 20.93 en vez de
  20.94; Q-learning en P2 498.52 en vez de 498.53; Q-learning (colas) en P2 559.95 en vez de 559.94; SARSA en P3
  24.50 en vez de 24.51). En la version principal no cambia ninguna celda.
"""
import os
import sys
import csv
import argparse

PLAN2 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(PLAN2))
import veredicto as vd          # noqa: E402

# Nombres del glosario de la tesis (entrega 3, ajuste A8, 23.10.2026); los largos van en dos lineas para que la
# primera columna no ensanche la tabla. Antes: Trivial, ql_colas, IPPO local, IPPO vecinos e IPPO spill.
MODELOS = [("actuado", "Actuado"), ("trivial", "Ciclo mínimo"), ("ql", "Q-learning"), ("sarsa", "SARSA"),
           ("ql_colas", r"\makecell[l]{Q-learning\\(colas)}"), ("dqn", "DQN"),
           ("ippo_local", r"\makecell[l]{IPPO sin\\mensajes}"), ("ippo_vecinos", r"\makecell[l]{IPPO con\\mensajes}"),
           ("ippo_spill", r"\makecell[l]{IPPO con\\penalización}"), ("mappo", "MAPPO")]
ABREV = {"FUNCIONA": "FUN", "MEJORA": "MEJ", "EMPATA": "EMP", "FALLA": "FAL"}
IGUAL_VECINOS = r"\makecell{igual a IPPO\\con mensajes}"     # rotulo "= vecinos" de veredicto.csv, en palabras
TABLAS = os.path.join(os.path.dirname(PLAN2), "TESIS", "secciones", "tablas")


def menos(texto):
    return texto.replace("-", "$-$")


def delta(x):
    s = f"{float(x):+.1f}"
    if s in ("+0.0", "-0.0"):
        s = "0.0"
    return menos(s)


def veredicto_corto(v):
    """(veredicto abreviado, igual al ciclo minimo) de un texto de veredicto.csv. Entrega 3: la igualdad con el
    ciclo minimo ya no va como marca * sino en palabras, en una linea aparte de la celda."""
    v = v.strip()
    igual_ciclo = "(= trivial)" in v
    v = v.replace(" (= trivial)", "")
    if v in ABREV:
        return ABREV[v], igual_ciclo
    if v.startswith("= vecinos"):
        return "= vecinos", False
    if v.startswith("PENDIENTE (no convergi"):
        prov = v.split("provisional:")[1].strip(" )")
        return f"PEN ({ABREV[prov]})", igual_ciclo
    if v.startswith("PENDIENTE (falta"):
        return "pendiente", False
    if v.startswith("PENDIENTE"):
        return "sin datos", False
    raise ValueError(v)


def media_cruda(res_esc, modelo, r):
    """Retraso medio sin redondear de la version evaluada de un modelo (o del actuado y del ciclo minimo), de
    evaluacion_<esc>_resumen*.csv (res_esc, de vd.leer_resumen); si falta, el retraso de veredicto.csv. Asi la tabla
    redondea una sola vez, como las tablas por modelo de veredicto.py (verificacion de las tareas 4 y 5, 23.10.2026)."""
    brazo = modelo if modelo in ("actuado", "trivial") else f"{modelo}_s{r.get('base_publicada', '')}"
    fila = res_esc.get((brazo, vd.METRICA))
    if fila and fila.get("media") not in ("", None):
        return float(fila["media"])
    return float(r["retraso"])


def celda_modelo(r, v, igual_ciclo, retraso):
    """Retraso, cambio frente al fijo y veredicto abreviado de un modelo en un caso. El PEN con su provisional va
    en su propia linea (entrega 3: con todo en la segunda linea, la tabla se salia del margen) y la igualdad con el
    ciclo minimo, en palabras debajo. retraso: la media sin redondear (media_cruda)."""
    lineas = [f"{retraso:.2f}"]
    if v.startswith("PEN"):
        lineas += [delta(r["delta_fijo"]), v]
    else:
        lineas.append(delta(r["delta_fijo"]) + " " + v)
    if igual_ciclo:
        lineas += ["igual al", "ciclo mínimo"]
    return r"\makecell{" + r"\\".join(lineas) + "}"


def cabecera():
    """Encabezados de los casos con la red y la demanda, como en la matriz de veredicto.py (entrega 3; antes el
    nombre del escenario, p. ej. corredor_alta)."""
    return " & ".join(vd.encabezado_caso(c, e) for c, e in vd.CASOS)


def sin_fijo(res):
    """Casos sin la fila del fijo de referencia (su columna queda pendiente)."""
    return [(c, e) for c, e in vd.CASOS if not res[e].get((vd.FIJO, vd.METRICA))]


def comentario_pendiente(res):
    return "".join(f"% PENDIENTE-{c}: falta evaluar el fijo de referencia ({vd.FIJO}) de {e}; al "
                   f"terminar, regenerar con plan2/tablas_cap5.py\n" for c, e in sin_fijo(res))


def titulo(corto, largo):
    """Titulos con el prefijo al inicio (p. ej. Robustez: ...), como en veredicto.py."""
    t = vd.titulo_prefijo()
    if not t:
        return corto, largo
    return f"{t}: {corto[0].lower()}{corto[1:]}", f"{t}. {largo}"


def remision_detalle():
    """Ultima frase del caption de tab:plan2-resumen: donde estan los intervalos, los valores p y Delta_a.

    Version principal (Anexo A): en las tablas por modelo. Robustez (--prefijo robustez_): el Anexo F conserva
    solo las tablas por modelo del ciclo minimo, que no tiene Delta_a, y de IPPO con mensajes (reduccion del
    23.10.2026); el detalle de todos los modelos esta en plan2/robustez_veredicto.csv del repositorio.
    """
    if vd.PREFIJO == "robustez_":
        return (r"Los intervalos, los valores $p$ y $\Delta_a$ de IPPO con mensajes están en la "
                r"Tabla~\ref{" + vd.etiqueta("veredicto-ippo-vecinos") + r"}, y los de todos los modelos, en el "
                r"repositorio del proyecto (\texttt{plan2/\allowbreak robustez\_veredicto.csv}).")
    return r"Los intervalos, los valores $p$ y $\Delta_a$ están en las tablas por modelo."


def escribir(nombre, texto):
    ruta = os.path.join(TABLAS, vd.PREFIJO + nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("% Generado por plan2/tablas_cap5.py. No editar a mano.\n" + texto + "\n")
    print("Escrito", ruta)


def lista_casos(casos):
    """"P5", "P5 ni en P6", "P4, P5 ni en P6"."""
    if len(casos) < 2:
        return "".join(casos)
    return ", ".join(casos[:-1]) + " ni en " + casos[-1]


def tabla_resumen(ver, res):
    lin = [r"Modelo & " + cabecera() + r" \\", r"\midrule"]
    fijo = []
    for _, esc in vd.CASOS:
        r = res[esc].get((vd.FIJO, vd.METRICA))
        fijo.append("--" if not r else
                    r"\makecell{" + f"{float(r['media']):.2f}" + r"\\$\pm$ " + f"{float(r['ic95']):.2f}"
                    + "}")
    # entrega 3: nombre del glosario; en la robustez la referencia es el fijo ajustado desde 10 s
    etiqueta_fijo = (r"Fijo ajustado\\(s/veh)" if vd.FIJO == "fijo_2509"
                     else r"Fijo ajustado\\desde 10~s\\(s/veh)")
    lin += [r"\makecell[l]{" + etiqueta_fijo + r"} & " + " & ".join(fijo) + r" \\", r"\midrule"]
    usados, hay_igual_ciclo = set(), False
    for m, nombre in MODELOS:
        celdas = []
        for caso, esc in vd.CASOS:
            r = ver.get((caso, m))
            v, igual_ciclo = veredicto_corto(r["veredicto"]) if r else ("sin datos", False)
            usados.add(v)
            hay_igual_ciclo = hay_igual_ciclo or igual_ciclo
            if not r or not r["retraso"] or v in ("= vecinos", "pendiente") or not r["delta_fijo"]:
                celdas.append(IGUAL_VECINOS if v == "= vecinos" else v)
                continue
            celdas.append(celda_modelo(r, v, igual_ciclo, media_cruda(res[esc], m, r)))
        lin.append(nombre + " & " + " & ".join(celdas) + r" \\")
    sin_ql_colas = [c for c, _ in vd.CASOS
                    if (ver.get((c, "ql_colas")) or {}).get("veredicto", "") == "PENDIENTE (sin datos)"]
    if vd.METRICA == "timeloss_prom":
        inicio = (r"Resumen del plan de pruebas por "
                  r"caso y modelo, sobre las semillas de evaluación 1001 a 1030. Primera fila: retraso del "
                  r"fijo ajustado (s/veh), media $\pm$ semiamplitud del IC95\,\%. Demás filas: retraso medio "
                  r"del modelo (s/veh), es decir, de su versión evaluada, ")
    else:
        que = "retraso total" if vd.METRICA == "retraso_total_prom" else "retraso (timeLoss)"
        inicio = (r"Resumen del plan de pruebas por "
                  r"caso y modelo, sobre las semillas de evaluación 1001 a 1030, con el " + que + r" "
                  r"(Ecuación~\ref{eq:retraso-total}). Primera fila: el del " + vd.nombre_fijo() + r" (s/veh), "
                  r"media $\pm$ "
                  r"semiamplitud del IC95\,\%. Demás filas: el del modelo (s/veh), es decir, de su versión "
                  r"evaluada, ")
    que_igual = "retraso total" if vd.METRICA == "retraso_total_prom" else "retraso"
    largo = (inicio +
             r"y debajo $\Delta_f$ (\%) con el veredicto abreviado: FUN, funciona; MEJ, "
             r"mejora; EMP, empata; FAL, falla; PEN, pendiente porque el entrenamiento de la versión "
             r"evaluada no converge, con el veredicto provisional entre paréntesis. "
             + ("" if vd.SIN_TRIVIAL or not hay_igual_ciclo else
                r"Igual al ciclo mínimo: la política da el mismo " + que_igual + r" y la misma espera que el "
                r"ciclo mínimo. ")
             + r"Igual a IPPO con mensajes: la penalización de \textit{spillback} no se activa y la política "
             r"es la de IPPO con mensajes. "
             + ("" if "pendiente" not in usados else
                r"Pendiente: el caso aún no tiene la comparación con el " + vd.nombre_fijo() + ". ")
             + ("" if not sin_ql_colas else
                r"Sin datos: Q-learning (colas) no se corrió en " + lista_casos(sin_ql_colas) + ". ")
             + remision_detalle())
    corto, largo = titulo("Retraso y cambio frente al fijo por caso y modelo", largo)
    # Verificacion de las tareas 4 y 5 (23.10.2026): en la robustez la tabla flota ([!tbp]). En [H], detras de la
    # matriz de veredicto.py, que flota, la matriz se iba al comienzo de la pagina siguiente y esta tabla, de casi una
    # pagina, se apilaba debajo en la misma pagina: el Anexo F se salia 261 pt por abajo (Overfull \vbox). La version
    # principal (Anexo A) sigue en [H].
    lugar = "!tbp" if vd.PREFIJO == "robustez_" else "H"
    return comentario_pendiente(res) + "\n".join([
        r"\begin{table}[" + lugar + "]", r"\setstretch{1}", r"\centering", r"\scriptsize",
        r"\setlength{\tabcolsep}{2.5pt}",
        r"\begin{tabular}{l" + "c" * len(vd.CASOS) + "}", r"\toprule"] + lin + [
        r"\bottomrule", r"\end{tabular}",
        r"\caption[" + corto + "]{" + largo + "}",
        r"\label{" + vd.etiqueta("plan2-resumen") + "}", r"\end{table}"])


def tabla_metas(ver, res, modelo):
    # entrega 3: en dos lineas, para que la tabla quepa con los encabezados de red y demanda
    retraso = (r"\makecell[l]{Retraso\\por vehículo}" if vd.METRICA == "timeloss_prom"
               else r"\makecell[l]{Retraso total\\por vehículo}")
    metas = [(vd.METRICA, retraso, r"$-25$ a $-40$"),
             ("cola_prom", r"Cola promedio", r"$\leq -20$"),
             ("co2_prom", r"Emisiones de CO$_2$", r"$\leq -5$"),
             ("throughput", r"\textit{Throughput}", r"$\geq +10$")]
    bases = [(ver.get((caso, modelo)) or {}).get("base_publicada", "") for caso, _ in vd.CASOS]
    lin = [r"Métrica & \makecell{Meta\\$\Delta$ (\%)} & " + cabecera() + r" \\", r"\midrule"]
    for met, nombre, meta in metas:
        celdas = []
        for (caso, esc), b in zip(vd.CASOS, bases):
            r = res[esc].get((f"{modelo}_s{b}", met))
            celdas.append(delta(r["delta_pct"]) if r and r.get("delta_pct") not in ("", None) else "--")
        lin.append(nombre + " & " + meta + " & " + " & ".join(celdas) + r" \\")
    comentario = "% bases publicadas de " + modelo + ": " + ", ".join(
        f"{c} {b}" for (c, _), b in zip(vd.CASOS, bases))
    corto, largo = titulo("Metas cuantitativas frente al " + vd.nombre_fijo(), (
        r"Metas cuantitativas de la tesis y "
        r"versión evaluada de " + vd.NOMBRE_LARGO[modelo] + r". Cambio porcentual de la media "
        r"frente al "
        + vd.nombre_fijo() + r" ($\Delta$, \%) en cada caso, sobre las semillas de evaluación 1001 a 1030 y "
        r"pareado por semilla. Meta: la de la introducción, expresada como cambio frente al fijo; "
        r"un valor negativo es una reducción."))
    return comentario_pendiente(res) + "\n".join([
        comentario, r"\begin{table}[H]", r"\setstretch{1}", r"\centering", r"\footnotesize",
        r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{lc" + "r" * len(vd.CASOS) + "}", r"\toprule"]
        + lin + [r"\bottomrule", r"\end{tabular}",
                 r"\caption[" + corto + "]{" + largo + "}",
                 r"\label{" + vd.etiqueta("plan2-metas") + "}", r"\end{table}"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="ippo_vecinos", help="modelo de la tabla de metas")
    ap.add_argument("--metrica", choices=["retraso_total_prom", "timeloss_prom"], default=vd.METRICA)
    ap.add_argument("--fijo", default="fijo", help="brazo de referencia (fijo_2509: el del 25.09)")
    ap.add_argument("--prefijo", default="", help="prefijo de veredicto.csv, de las salidas y de los labels")
    ap.add_argument("--casos", default=None, help='solo esos casos, p. ej. "P1-P5"')
    ap.add_argument("--sin-trivial", action="store_true", help="sin la fila del control trivial")
    args = ap.parse_args()
    vd.configurar(args.metrica, args.fijo, args.sin_trivial, args.casos, args.prefijo)
    if args.sin_trivial:
        MODELOS[:] = [mn for mn in MODELOS if mn[0] != "trivial"]
    with open(os.path.join(PLAN2, vd.PREFIJO + "veredicto.csv"), encoding="utf-8") as f:
        ver = {(r["caso"], r["modelo"]): r for r in csv.DictReader(f)}
    res = {esc: vd.leer_resumen(PLAN2, esc) for _, esc in vd.CASOS}
    escribir("plan2_resumen.tex", tabla_resumen(ver, res))
    escribir("plan2_metas.tex", tabla_metas(ver, res, args.modelo))


if __name__ == "__main__":
    main()
