"""Juicio de la confirmacion de P6 (malla3_alta) en 6001-6030 (exploratorio, fuera del veredicto del 25.09).
Estadistica como veredicto.py / tanda 2: evaluar.comparar (delta % de medias, IC95 bootstrap pareado por semilla,
10 000 remuestreos, rng 0; Wilcoxon pareado) y veredicto.veredicto (regla vs fijo y actuado). La convergencia NO
se re-juzga: se toma de tanda2/salidas/seleccion_P6_V{2,5}.json.
CONFIRMA = base publicada de V2 (4042) y de V5 (42) con IC95 entero < 0 frente al fijo 15/10 Y frente a IPPO
vecinos publicado s42, en 6001-6030 (timeLoss).
Sensibilidad: 60 semillas (5001-5030 de tanda2/mejora_coord + 6001-6030 de aqui).
Salida: conf_p6/salidas/juicio_conf_p6.txt y .json."""
import os, sys, csv, glob, json, statistics as st
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
AQ = os.path.dirname(os.path.abspath(__file__))
C2 = os.path.dirname(AQ)
T2 = os.path.join(C2, "tanda2")
MC = os.path.join(os.path.dirname(C2), "mejora_coord")
sys.path.insert(0, os.path.join(C2, "code"))
import evaluar as E
import veredicto as V

SAL = os.path.join(AQ, "salidas")
S6 = list(range(6001, 6031)); S5 = list(range(5001, 5031)); S60 = S5 + S6
out = []


def p(*x):
    out.append(" ".join(str(y) for y in x)); print(*x, flush=True)


def leer(pats):
    d = {}
    for pat in pats:
        for r in sorted(glob.glob(pat)):
            for f in csv.DictReader(open(r)):
                s = int(f["semilla"]); assert not 1001 <= s <= 1030
                d[s] = f
    return d


def ser(d, sem, col="timeloss_prom"):
    falta = sorted(set(sem) - set(d)); assert not falta, f"faltan {falta}"
    return [float(d[s][col]) for s in sem]


def ic(c, suf=""):
    return tuple(float(x) for x in c["delta_ic95" + suf].strip("[]").split(","))


def fmt(c, suf=""):
    return f"{c['delta_pct' + suf]:+.1f} % {c['delta_ic95' + suf]} p={c['p_wilcoxon' + suf]}"


BR = ["V2_s42", "V2_s2042", "V2_s4042", "V5_s42", "V5_s2042", "V5_s4042", "ippo_vecinos_s42", "fijo", "actuado", "trivial"]
PUB = {"V2": "V2_s4042", "V5": "V5_s42"}
D6 = {b: leer([os.path.join(SAL, f"malla3_alta_{b}_p*.csv")]) for b in BR}
# 5001-5030 (tanda 2 y mejora_coord)
sim = os.path.join(MC, "salidas", "sim")
D5 = {f"{br}_s{b}": leer([os.path.join(T2, "p6", "salidas", f"eval_malla3_alta_{br}_s{b}_p*.csv")])
      for br in ("V2", "V5") for b in (42, 2042, 4042)}
D5.update({"ippo_vecinos_s42": leer([os.path.join(sim, "malla3_alta_ippo_vecinos_s42.csv")]),
           "fijo": leer([os.path.join(sim, "malla3_alta_fijo2509.csv")]),
           "actuado": leer([os.path.join(sim, "malla3_alta_actuado.csv")]),
           "trivial": leer([os.path.join(sim, "malla3_alta_trivial.csv")])})
R = {}
sel = {br: json.load(open(os.path.join(T2, "salidas", f"seleccion_P6_{br}.json"), encoding="utf-8")) for br in ("V2", "V5")}
conv = {f"{br}_s{b}": sel[br]["bases"][str(b)]["convergio"] for br in ("V2", "V5") for b in (42, 2042, 4042)}
assert sel["V2"]["base_publicada"] == 4042 and sel["V5"]["base_publicada"] == 42

p("== Confirmacion P6 malla3_alta en semillas nuevas 6001-6030 (exploratorio; convergencia tomada de la tanda 2)")
p("  control de determinismo, semilla 5001 (conf_p6 frente a tanda2 / mejora_coord), timeLoss y retraso total:")
det = {}
for b in BR:
    a, z = D6[b].get(5001), D5[b].get(5001)
    ok = a is not None and z is not None and a["timeloss_prom"] == z["timeloss_prom"] and a["retraso_total_prom"] == z["retraso_total_prom"]
    det[b] = {"conf": a and a["timeloss_prom"], "antes": z and z["timeloss_prom"], "igual": ok}
    p(f"    {b:18s} {det[b]['conf']} = {det[b]['antes']}  {'OK' if ok else 'DISTINTO'}")
R["determinismo_5001"] = det


def bloque(D, sem, etiq):
    p(f"\n== semillas {etiq} (n={len(sem)})")
    v = {b: ser(D[b], sem) for b in BR}
    rt = {b: ser(D[b], sem, "retraso_total_prom") for b in BR}
    ins = {b: st.mean(ser(D[b], sem, "retraso_insercion_prom")) for b in BR}
    noins = {b: sum(int(float(x)) for x in ser(D[b], sem, "no_insertados")) for b in BR}
    noterm = {b: sum(int(float(x)) for x in ser(D[b], sem, "no_terminados")) for b in BR}
    res = {}
    p(f"  {'brazo':18s} {'media':>8s} {'sd':>6s} | vs fijo 15/10 (regla)                              | vs IPPO publicado s42              | vs actuado                          | retraso total vs fijo        | ret. ins. | gana fijo/ippo")
    for b in BR:
        f = {"media": round(st.mean(v[b]), 3), "sd": round(st.stdev(v[b]), 3), "max": max(v[b]),
             "retraso_total_media": round(st.mean(rt[b]), 3), "retraso_insercion_media": round(ins[b], 3),
             "no_insertados": noins[b], "no_terminados": noterm[b],
             "cambios_fase": round(st.mean(ser(D[b], sem, "cambios_fase")), 1)}
        if b != "fijo":
            cf = E.comparar(v[b], v["fijo"]); ca = E.comparar(v[b], v["actuado"], "_act")
            f["vs_fijo"] = cf
            f["etiqueta_regla"] = V.veredicto(cf["delta_pct"], ic(cf), float(cf["p_wilcoxon"]), ic(ca, "_act"), float(ca["p_wilcoxon_act"]))
            f["gana_fijo"] = sum(x < y for x, y in zip(v[b], v["fijo"]))
            f["retraso_total_vs_fijo"] = E.comparar(rt[b], rt["fijo"])
            f["gana_fijo_retraso_total"] = sum(x < y for x, y in zip(rt[b], rt["fijo"]))
        if b != "actuado":
            f["vs_actuado"] = E.comparar(v[b], v["actuado"])
        if b != "ippo_vecinos_s42":
            f["vs_ippo_pub"] = E.comparar(v[b], v["ippo_vecinos_s42"])
            f["gana_ippo"] = sum(x < y for x, y in zip(v[b], v["ippo_vecinos_s42"]))
            f["retraso_total_vs_ippo_pub"] = E.comparar(rt[b], rt["ippo_vecinos_s42"])
        if b in conv:
            f["convergio_tanda2"] = conv[b]
        f["publicada"] = b in PUB.values()
        res[b] = f
        marca = " <== PUBLICADA" if f["publicada"] else ""
        p(f"  {b:18s} {f['media']:8.3f} {f['sd']:6.2f} | "
          + (f"{fmt(f['vs_fijo']):34s} {f['etiqueta_regla']:8s}" if "vs_fijo" in f else f"{'(referencia)':43s}") + " | "
          + (f"{fmt(f['vs_ippo_pub']):34s}" if "vs_ippo_pub" in f else f"{'(referencia)':34s}") + " | "
          + (f"{fmt(f['vs_actuado']):35s}" if "vs_actuado" in f else f"{'(referencia)':35s}") + " | "
          + (f"{fmt(f['retraso_total_vs_fijo']):28s}" if "retraso_total_vs_fijo" in f else f"{f['retraso_total_media']:8.3f} (ref){'':15s}") + " | "
          + f"{ins[b]:7.2f}  | " + (f"{f.get('gana_fijo', '-')}/{f.get('gana_ippo', '-')}") + marca)
    p(f"  no_insertados: {noins}  no_terminados: {noterm}")
    res["V5pub_vs_V2pub"] = E.comparar(v[PUB["V5"]], v[PUB["V2"]])
    p(f"  V5 publicada vs V2 publicada: {fmt(res['V5pub_vs_V2pub'])}")
    p(f"  IPPO publicado vs fijo: {fmt(res['ippo_vecinos_s42']['vs_fijo'])}   max por semilla: "
      + ", ".join(f"{b} {res[b]['max']:.2f}" for b in BR))
    ok = {}
    for br, b in PUB.items():
        ok[br] = ic(res[b]["vs_fijo"])[1] < 0 and ic(res[b]["vs_ippo_pub"])[1] < 0
        p(f"  {br} publicada ({b}): IC95 vs fijo {res[b]['vs_fijo']['delta_ic95']}, vs IPPO publicado "
          f"{res[b]['vs_ippo_pub']['delta_ic95']} -> {'ambos < 0' if ok[br] else 'NO ambos < 0'}")
    res["_ok"] = ok
    return res


R["6001-6030"] = bloque(D6, S6, "6001-6030 (CONFIRMACION)")
okc = R["6001-6030"]["_ok"]
conf = okc["V2"] and okc["V5"]
R["CONFIRMA"] = conf
p(f"\n  CONFIRMA (V2 4042 y V5 42 con IC95 < 0 vs fijo 15/10 y vs IPPO publicado en 6001-6030): {'SI' if conf else 'NO'} {okc}")
D60 = {b: {**D5[b], **{s: D6[b][s] for s in S6}} for b in BR}
R["60_semillas"] = bloque(D60, S60, "5001-5030 + 6001-6030 (SENSIBILIDAD, n=60)")
R["5001-5030_recalculo"] = bloque(D5, S5, "5001-5030 (recalculo, referencia)")
for k in ("6001-6030", "60_semillas", "5001-5030_recalculo"):
    R[k].pop("_ok", None)
open(os.path.join(SAL, "juicio_conf_p6.txt"), "w", encoding="utf-8").write("\n".join(out) + "\n")
json.dump(R, open(os.path.join(SAL, "juicio_conf_p6.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
