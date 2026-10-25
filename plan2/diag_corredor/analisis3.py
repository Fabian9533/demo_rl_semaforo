"""
analisis3.py - Responde la Enmienda 3 del diagnostico del corredor (PRERREGISTRO.md): por que 2715 veh/h.

Cuando termine la cola diag3_ (plan2/cola/; lanzada el 25.10.2026 a las 18:20 con el commit 50a9c6b), desde plan2/:
    python diag_corredor/analisis3.py
Escribe plan2/diag_corredor/pruebas3.txt y resultados3.csv. Si falta una evaluacion o un meta, lo lista y sale con
codigo 1 sin escribir nada.

Escenarios: O = dem_corredor_t2715 (original), D = dem_corredor_t2715_der (giros del periodo 2 a la derecha).
Pruebas (retraso total, cambio pareado por semilla, IC95 bootstrap pareado y p de Wilcoxon con evaluar.comparar,
a traves de analisis.comparar; IC entero bajo cero leido sobre el IC redondeado a 0.1, como en veredicto.py):
  H6a  en D, V2 de 2715 sin reentrenar (politica_dem_corredor_t2715_vecinos_v2_s42.pt) frente al fijo de 2715 (el
       mismo plan 25/10 s, desfases 0/0): IC entero bajo cero.
  H6b  en D, V2 entrenado en D (base mediana por val_elegido, veredicto.base_mediana) frente al fijo ajustado de D
       (barrido propio con la regla vigente): IC entero bajo cero.
  H7   en O, V2 con gamma 0.99 (base mediana) frente a V2 (base 42, la version evaluada de V2 en 2715): IC entero
       bajo cero.
Cada prueba en 1001-1030 y en 6001-6030 por separado. Sin prueba: el actuado y la version actual en D frente al fijo
de 2715 en D, el veredicto de la regla del plan de V2 entrenado en D, y las medias de cada control en O y en D.
"""
import os
import sys
import csv
import json

DIR = os.path.dirname(os.path.abspath(__file__))          # plan2/diag_corredor
P2 = os.path.dirname(DIR)
sys.path.insert(0, DIR)
import analisis as an                                     # noqa: E402  (comparar, leer_eval, vd, BASES, SEMILLAS)

EVAL3 = os.path.join(DIR, "eval3")
D, O = "dem_corredor_t2715_der", "dem_corredor_t2715"
JUEGOS = ["1001", "6001"]


def ruta_d(brazo, k):
    return os.path.join(EVAL3, f"eval_d_{brazo}_{k}.csv")


def ruta_o(brazo, k):
    """Evaluaciones en O: las de la primera ronda (diag_corredor/eval/ y demanda2/) y las de gamma 0.99 (eval3/)."""
    if brazo.startswith("ippo_v2g99"):
        return os.path.join(EVAL3, f"eval_o_{brazo}_{k}.csv")
    if brazo == "fijo":
        return an.ruta_ref("2715", "fijo10", k)
    if brazo == "actuado":
        return an.ruta_ref("2715", "actuado", k)
    if brazo == "ippo_actual":
        return an.ruta_ref("2715", "ippo_vecinos_s2042", k)
    if brazo == "ippo_v2":
        return an.ruta_diag("2715", "ippo_vecinos_v2_s42", k)
    raise KeyError(brazo)


def meta(esc, etiqueta, base):
    return an.leer_json(os.path.join(P2, f"politica_{esc}_vecinos_{etiqueta}_s{base}.json"))


def version(esc, etiqueta, faltan):
    """Base mediana por val_elegido (en retraso total: --criterio-val total) y su convergencia."""
    metas = {b: meta(esc, etiqueta, b) for b in an.BASES}
    for b, m in metas.items():
        if m is None:
            faltan.append(f"politica_{esc}_vecinos_{etiqueta}_s{b}.json")
        elif (m.get("opciones") or {}).get("criterio_val") != "total":
            faltan.append(f"politica_{esc}_vecinos_{etiqueta}_s{b}.json (criterio_val no es total)")
    if any(m is None for m in metas.values()):
        return None
    vals = {b: an.vd.flotante(m.get("val_elegido")) for b, m in metas.items()}
    base = an.vd.base_mediana(vals)
    m = metas[base]
    pares = sorted((int(x[0]), float(x[-1])) for x in m.get("val_total_serie") or [])
    conv, meseta, estab = an.vd.convergencia(pares, float(m.get("episodios") or 200)) if pares else (False, None, None)
    return {"base": base, "vals": vals, "ep": m.get("ep_elegido"), "convergio": conv, "meseta": meseta,
            "estabilidad": estab, "hiper": m.get("hiper")}


def condicion(c):
    """(cumple, linea) para 'IC entero bajo cero' sobre el retraso total."""
    lo, hi = c["ic_total"]
    cumple = hi < 0
    marca = "  [extremo del IC en 0.0 por el redondeo]" if hi == 0 else ""
    return cumple, (f"{c['media_ref_total']:8.2f} -> {c['media_total']:8.2f} s/veh  {an.txt_pct(c['cambio_total']):>9s} "
                    f"{an.txt_ic(c['ic_total']):>16s}  p={an.txt_p(c['p_total']):7s} "
                    f"{'cumple' if cumple else 'no cumple'}{marca}")


def escribir_tabla(datos, comp):
    """TESIS/secciones/tablas/diag_2715.tex (solo el tabular): los mismos controles en 2715 con y sin los giros a la
    izquierda del periodo 2, retraso total medio (1001-1030) y cambio frente al fijo de 2715 en su escenario."""
    filas_tex = [("Fijo de 2715 (25/10~s)", "fijo", "fijo2715"), ("Actuado", "actuado", "actuado"),
                 ("Versión evaluada", "ippo_actual", "ippo_actual"), ("V2", "ippo_v2", "ippo_v2")]
    lineas = ["% Generado por plan2/diag_corredor/analisis3.py. No editar a mano.",
              "% Enmienda 3: los mismos controles y politicas en dem_corredor_t2715 (con los giros a la izquierda del periodo 2)",
              "% y en dem_corredor_t2715_der (sin ellos), semillas 1001-1030; cambio pareado frente al fijo de 2715 (25/10 s) en",
              "% cada escenario, con IC95 bootstrap pareado. Necesita booktabs y makecell; el table lleva \\footnotesize.",
              r"\begin{tabular}{lrrrr}", r"\toprule",
              r" & \multicolumn{2}{c}{Con los giros a la izquierda} & \multicolumn{2}{c}{Sin ellos} \\",
              r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}",
              r"Control & \makecell[r]{Retraso total\\(s/veh)} & \makecell[r]{Frente al\\fijo (\%)} & "
              r"\makecell[r]{Retraso total\\(s/veh)} & \makecell[r]{Frente al\\fijo (\%)} \\", r"\midrule"]
    for nombre, b_o, b_d in filas_tex:
        celdas = [nombre]
        for esc, b, ref in (("O", b_o, "fijo"), ("D", b_d, "fijo2715")):
            m = an.media_col(datos[(esc, b, "1001")], "total")
            if b == ref:
                celdas += [f"{m:.2f}", "--"]
            else:
                c = comp(esc, b, esc, ref, "1001")
                celdas += [f"{m:.2f}", rf"\makecell[r]{{{an.tex_signo(c['cambio_total'])}\\{{}}{an.tex_ic(c['ic_total'])}}}"]
        lineas.append(" & ".join(celdas) + r" \\")
    # solo en el escenario sin giros: su fijo ajustado (barrido propio) y V2 entrenado ahi (base mediana)
    base_d = [b for (e, b, k) in datos if e == "D" and b.startswith("ippo_v2d_s") and k == "1001"][0]
    lineas.append(r"\addlinespace")
    for nombre, b in (("Fijo ajustado sin los giros", "fijo"), ("V2 entrenado sin los giros", base_d)):
        m = an.media_col(datos[("D", b, "1001")], "total")
        c = comp("D", b, "D", "fijo2715", "1001")
        lineas.append(" & ".join([nombre, "--", "--", f"{m:.2f}",
                                  rf"\makecell[r]{{{an.tex_signo(c['cambio_total'])}\\{{}}{an.tex_ic(c['ic_total'])}}}"])
                      + r" \\")
    lineas += [r"\bottomrule", r"\end{tabular}"]
    ruta = os.path.join(an.RAIZ, "TESIS", "secciones", "tablas", "diag_2715.tex")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n")
    print("Escrito", ruta)


def main():
    faltan = []
    v2d = version(D, "v2", faltan)
    g99 = version(O, "v2g99", faltan)
    datos = {}
    for k in JUEGOS:
        brazos_d = ["fijo2715", "fijo", "actuado", "ippo_actual", "ippo_v2"]
        if v2d:
            brazos_d.append(f"ippo_v2d_s{v2d['base']}")
        for b in brazos_d:
            datos[("D", b, k)] = an.leer_eval(ruta_d(b, k), k)
        brazos_o = ["fijo", "actuado", "ippo_actual", "ippo_v2"]
        if g99:
            brazos_o.append(f"ippo_v2g99_s{g99['base']}")
        for b in brazos_o:
            datos[("O", b, k)] = an.leer_eval(ruta_o(b, k), k)
    for clave, d in datos.items():
        if d is None:
            esc, b, k = clave
            faltan.append((ruta_d if esc == "D" else ruta_o)(b, k))
    if faltan:
        print(f"Faltan {len(faltan)} archivos (la cola no termino o algo fallo); no se escribe nada:")
        for f in sorted(set(faltan)):
            print("  ", f)
        return 1

    def comp(esc_a, a, esc_b, b, k):
        return an.comparar(datos[(esc_a, a, k)], datos[(esc_b, b, k)])

    pruebas = {
        "H6a": ("En D, V2 de 2715 sin reentrenar frente al fijo de 2715 (25/10 s, desfases 0/0)",
                ("D", "ippo_v2", "D", "fijo2715")),
        "H6b": (f"En D, V2 entrenado en D (base {v2d['base']}) frente al fijo ajustado de D",
                ("D", f"ippo_v2d_s{v2d['base']}", "D", "fijo")),
        "H7": (f"En O, V2 con gamma 0.99 (base {g99['base']}) frente a V2 (base 42)",
               ("O", f"ippo_v2g99_s{g99['base']}", "O", "ippo_v2")),
    }
    lineas = ["Diagnostico del corredor, Enmienda 3: por que 2715 veh/h (PRERREGISTRO.md)",
              "Generado por plan2/diag_corredor/analisis3.py. No editar a mano.", "",
              "O = dem_corredor_t2715 (original); D = dem_corredor_t2715_der (giros del periodo 2 a la derecha).",
              "Retraso total; cambio pareado por semilla, IC95 bootstrap pareado (10 000) y p de Wilcoxon (evaluar.comparar).",
              "IC entero bajo cero leido sobre el IC redondeado a 0.1, como en veredicto.py.", ""]
    resumen, filas = {}, []
    for h, (texto, (ea, a, eb, b)) in pruebas.items():
        lineas.append(f"{h}: {texto}; IC entero bajo cero.")
        res = []
        for k in JUEGOS:
            c = comp(ea, a, eb, b, k)
            cumple, linea = condicion(c)
            res.append(cumple)
            lineas.append(f"  {an.NOMBRE_SEMILLAS[k]}: {linea}")
            filas.append({"prueba": h, "semillas": an.NOMBRE_SEMILLAS[k], "control": f"{ea}:{a}", "referencia": f"{eb}:{b}",
                          "media": round(c["media_total"], 3), "media_ref": round(c["media_ref_total"], 3),
                          "cambio": c["cambio_total"], "ic_lo": c["ic_total"][0], "ic_hi": c["ic_total"][1],
                          "p": c["p_total"], "cumple": "si" if cumple else "no"})
        resumen[h] = ["PASA" if r else "NO PASA" for r in res]
        lineas.append(f"  => {resumen[h][0]} en 1001-1030; {resumen[h][1]} en 6001-6030")
        lineas.append("")

    lineas.append("SIN PRUEBA: cada control frente al fijo de 2715 (25/10 s) en su escenario, retraso total")
    for k in JUEGOS:
        lineas.append(f"  {an.NOMBRE_SEMILLAS[k]}:")
        for esc, ref, brazos in (("O", "fijo", ["actuado", "ippo_actual", "ippo_v2"] + ([f"ippo_v2g99_s{g99['base']}"])),
                                 ("D", "fijo2715", ["actuado", "ippo_actual", "ippo_v2", "fijo",
                                                    f"ippo_v2d_s{v2d['base']}"])):
            for b in brazos:
                c = comp(esc, b, esc, ref, k)
                lineas.append(f"    {esc} {b:18s} frente a {ref:8s} {c['media_ref_total']:8.2f} -> {c['media_total']:8.2f} "
                              f"{an.txt_pct(c['cambio_total']):>9s} {an.txt_ic(c['ic_total']):>16s}  p={an.txt_p(c['p_total'])}")
                filas.append({"prueba": "sin prueba", "semillas": an.NOMBRE_SEMILLAS[k], "control": f"{esc}:{b}",
                              "referencia": f"{esc}:{ref}", "media": round(c["media_total"], 3),
                              "media_ref": round(c["media_ref_total"], 3), "cambio": c["cambio_total"],
                              "ic_lo": c["ic_total"][0], "ic_hi": c["ic_total"][1], "p": c["p_total"], "cumple": ""})
    lineas.append("")

    # veredicto de la regla del plan para V2 entrenado en D frente al fijo ajustado de D (con el actuado de D)
    lineas.append("VEREDICTO de la regla del plan, retraso total, V2 entrenado en D frente al fijo ajustado de D:")
    for k in JUEGOS:
        cf = comp("D", f"ippo_v2d_s{v2d['base']}", "D", "fijo", k)
        ca = comp("D", f"ippo_v2d_s{v2d['base']}", "D", "actuado", k)
        prov = an.vd.veredicto(cf["cambio_total"], cf["ic_total"], cf["p_total"], ca["ic_total"], ca["p_total"])
        lineas.append(f"  {an.NOMBRE_SEMILLAS[k]}: {an.vd.texto_veredicto(prov, convergio=v2d['convergio'])} "
                      f"(frente al fijo {an.txt_pct(cf['cambio_total']).strip()}, frente al actuado "
                      f"{an.txt_pct(ca['cambio_total']).strip()})")
    lineas.append("")

    lineas.append("VERSIONES EVALUADAS (base mediana por val_elegido, en retraso total)")
    for nombre, v in (("V2 entrenado en D", v2d), ("V2 gamma 0.99 en O", g99)):
        vals = ", ".join(f"s{b} {x:.2f}" for b, x in v["vals"].items())
        conv = "se estabilizo" if v["convergio"] else "NO se estabilizo"
        extra = f" (meseta {v['meseta']:+.1f} %, estabilidad {v['estabilidad']:.1f} %)" if v["meseta"] is not None else ""
        lineas.append(f"  {nombre}: base {v['base']}, val {vals}; episodio {v['ep']}; {conv}{extra}; "
                      f"gamma {v['hiper'].get('gamma') if v['hiper'] else '?'}")
    lineas.append("")

    lineas.append("MEDIAS (s/veh, 1001-1030): retraso total | timeLoss | espera para entrar")
    for (esc, b, k), d in sorted(datos.items()):
        if k != "1001":
            continue
        m = {c: an.media_col(d, c) for c in ("total", "timeloss", "espera_entrar")}
        lineas.append(f"  {esc} {b:18s} {m['total']:8.2f} | {m['timeloss']:7.2f} | {m['espera_entrar']:7.2f}")
    lineas.append("")
    lineas.append("RESUMEN")
    for h, r in resumen.items():
        lineas.append(f"  {h:4s} {r[0]} en 1001-1030; {r[1]} en 6001-6030")
    if an.avisos:
        lineas += ["", "AVISOS"] + [f"  {a}" for a in an.avisos]
    texto = "\n".join(lineas) + "\n"
    with open(os.path.join(DIR, "pruebas3.txt"), "w", encoding="utf-8") as f:
        f.write(texto)
    escribir_tabla(datos, comp)
    with open(os.path.join(DIR, "resultados3.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
