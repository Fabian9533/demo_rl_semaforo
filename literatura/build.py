# -*- coding: utf-8 -*-
"""Escribe TESIS/secciones/anexo_e_trabajos.tex (Anexo E, comparacion con otros trabajos).

Uso (desde demo_rl/literatura):  python build.py ../TESIS/secciones/anexo_e_trabajos.tex

Los datos de las filas (ent_datos.py y las tuplas de este archivo) se transcribieron de las fichas de
fichas_trabajos.json (27.09.2026: 64 fichas, 54 obras; solo las de verificacion 'confirmado' o
'corregido'). Cada ficha trae la cita textual de la fuente que respalda su numero (cita_textual) y la
nota del verificador que la releyo (nota_verificacion). texto.tex es el texto fijo del anexo; gen.py y
ent.py son los prototipos de las dos tablas. Las entradas BibTeX de las obras estan en
referencias_nuevas.bib, ya anexadas a TESIS/referencias.bib.
"""
import io, math, re, statistics, sys

SALIDA = sys.argv[1]
CM_CHAR, LINEA, EXTRA = 0.135, 0.334, 0.10


W10 = dict(zip("abcdefghijklmnopqrstuvwxyz",
  [5.00,5.56,4.44,5.56,4.44,3.06,5.00,5.56,2.78,3.06,5.28,2.78,8.33,5.56,5.00,5.56,5.28,3.92,3.94,3.89,5.56,5.28,7.22,5.28,5.28,4.44]))
W10.update(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ",
  [7.50,7.08,7.22,7.64,6.81,6.53,7.85,7.50,3.61,5.14,7.78,6.25,9.17,7.50,7.78,6.81,7.78,7.36,5.56,7.22,7.50,7.50,10.28,7.50,7.50,6.11]))
W10.update({c: 5.00 for c in "0123456789"})
W10.update({".": 2.78, ",": 2.78, ";": 2.78, ":": 2.78, "(": 3.89, ")": 3.89, "-": 3.33, "/": 5.00,
            "%": 8.33, "+": 7.78, "x": 5.28, "<": 7.78, "[": 2.78, "]": 2.78, "'": 2.78, "`": 2.78,
            "\u2212": 7.78, "\u2013": 5.00})
ACENTOS = str.maketrans("áéíóúñÁÉÍÓÚÑü", "aeiounAEIOUNu")
F8 = 0.848 * 0.03514      # cm por punto de cmr10 llevado a cmr8
ESP = 3.33 * F8

def plano(tex):
    t = re.sub(r"\\citep\{[^}]*\}", "[00]", tex)
    t = re.sub(r"\\ref\{[^}]*\}", "E.0", t)
    t = t.replace("$-$", "\u2212").replace("$+$", "+").replace("--", "\u2013")
    t = t.replace(r"$\leq -10$", "<\u221210").replace(r"$\times$", "x").replace(r"$\pm$", "+")
    t = t.replace("$", "")
    t = re.sub(r"\\textit\{([^}]*)\}", r"\1", t)
    t = t.replace(r"\,", "").replace(r"\%", "%").replace("~", " ")
    t = re.sub(r"_\{?([^}\s]*)\}?", r"\1", t)
    t = re.sub(r"\\[a-zA-Z]+\s?", "", t)
    return t.replace("{", "").replace("}", "").replace("``", "\"").replace("''", "\"")

def ancho_palabra(p):
    return sum(W10.get(c, 5.0) for c in p.translate(ACENTOS)) * F8

def lineas(tex, ancho, margen=0.97):
    n, actual = 1, 0.0
    for p in plano(tex).split():
        w = ancho_palabra(p)
        if actual == 0.0:
            actual = w
        elif actual + ESP + w <= ancho * margen:
            actual += ESP + w
        else:
            n, actual = n + 1, w
    return n

def palabras_largas(tex, ancho, donde):
    for k, p in enumerate(plano(tex).split()):
        partes = p.split("-") if "-" in p and k > 0 else [p]
        if k == 0 and "-" in p:
            partes = [s + "-" for s in p.split("-")[:-1]] + [p.split("-")[-1]]
        for s in partes:
            if ancho_palabra(s) > ancho:
                print(f"PALABRA LARGA ({donde}, {'primera' if k == 0 else 'interior'}):", s,
                      round(ancho_palabra(s), 2), ">", ancho)

M = lambda x: "$-$" + x
P = lambda x: "$+$" + x

# ---------------------------------------------------------------- tabla de trabajos comparados
AN = [1.9, 1.7, 1.25, 1.7, 2.8, 1.25, 1.8]
assert abs(sum(AN) - 12.4) < 1e-9

BLOQUES = [
 ("tab:trabajos-comparados",
  "Trabajos comparados: bancos de prueba y control por presión",
  "Trabajos comparados, primer frente: bancos de prueba, comparaciones amplias y control por "
  "presión. Mejora: cambio porcentual frente a la referencia (negativo: menos retraso, espera o "
  "tiempo de viaje). Viaje: tiempo de viaje. Las convenciones de las columnas se explican en el texto.",
 [
  ("Lioris et al. (2014) \\citep{Lioris2014_MaxPressure}", "13, real", ".Q",
   "Max-Pressure \\citep{Varaiya2013_MaxPressure}, sin RL",
   [("fijo tuneado (LP)", "viaje", M("23.6"))]),
  ("Genders y Razavi (2019) \\citep{Genders2019_Framework}", "2, sintética", "SUMO", "DQN, DDPG",
   [("fijo tuneado", "viaje", M("8.9")), ("fijo tuneado", "viaje", M("1.3") + " DQN"),
    ("Webster adaptativo", "viaje", P("1.4")), ("Max-Pressure", "viaje", P("22.0"))]),
  ("LIT (2019) \\citep{Zheng2019_LIT}", "1 (12 cruces) y redes de 4 a 16, reales", "SUMO", "LIT (DQN)",
   [("fijo sin tunear", "viaje", M("55.5")), ("Webster", "viaje", M("34.0")),
    ("fijo sin tunear", "viaje", M("65.8") + " redes"), ("Webster", "viaje", M("37.6") + " redes")]),
  ("RESCO (2021) \\citep{Ault2021_RESCO}", "1 a 21, reales; mallas de 16, sintéticas", "SUMO",
   "IDQN, IPPO, MPLight, FMA2C",
   [("plan real", "retraso", "sin cifra"), ("Max-Pressure", "retraso", M("11")),
    ("Greedy", "retraso", M("20")), ("otro RL (IDQN)", "retraso", M("2.1") + " IPPO")]),
  ("Cabrejas-Egea et al. (2021) \\citep{CabrejasEgea2021_Comercial}", "1 (dos geometrías), sintética",
   "Vissim", "DDQN, DDDQN, A2C",
   [("fijo no declarado", "retraso", M("85.2")), ("MOVA (actuado)", "retraso", M("21.7")),
    ("MOVA (actuado)", "retraso", M("48.0")), ("MOVA (actuado)", "retraso", M("56.9")),
    ("SURTRAC", "retraso", M("26.6"))]),
  ("Efficient Pressure (2021) \\citep{Wu2021_EfficientMP}", "12 y 16, reales", "CityFlow",
   "Efficient-CoLight (DQN)",
   [("fijo no declarado", "viaje", M("38.2")), ("Max-Pressure", "viaje", M("3.7"))]),
  ("Advanced-XLight (2022) \\citep{Zhang2022_AdvancedMP}", "12 a 192, reales", "CityFlow",
   "Advanced-CoLight (DQN)",
   [("fijo no declarado", "viaje", M("38.6")), ("Max-Pressure", "viaje", M("8.6"))]),
  ("LibSignal (2024) \\citep{Mei2024_LibSignal}", "1 a 16 en SUMO (196 en CityFlow), reales y sintéticas",
   "SUMO y CityFlow", "IDQN, IPPO, CoLight, MPLight y otros",
   [("fijo sin tunear", "viaje", M("55.1")), ("Max-Pressure", "viaje", M("5.7")),
    ("Max-Pressure", "viaje", P("18.5") + " IPPO")]),
  ("T-REX (2025) \\citep{Nguyen2025_TREX}", "3 a 21, reales; malla de 16, sintética", "SUMO",
   "IDQN, IPPO, MPLight, FMA2C",
   [("plan real", "viaje", M("17.7")), ("plan real", "viaje", P("5.1") + " IPPO"),
    ("fijo sin tunear", "viaje", M("28.7") + " IDQN"), ("Max-Pressure", "viaje", M("20.2"))]),
 ]),
 ("tab:trabajos-comparados-2",
  "Trabajos comparados: cruce aislado y corredor",
  "Trabajos comparados, segundo frente: cruce aislado y corredor. Mismas convenciones que la "
  "Tabla~\\ref{tab:trabajos-comparados}.",
 [
  ("MARLIN-ATSC (2012) \\citep{ElTantawy2012_Tesis}", "1, 5 y 59, reales", "Paramics",
   "Q-learning, independiente y coordinado",
   [("Webster, 1 cruce", "retraso", M("35.5")), ("actuado, 1 cruce", "retraso", M("25.1")),
    ("Webster, 5 cruces", "retraso", M("21.4")), ("actuado, 5 cruces", "retraso", M("18.7")),
    ("plan real, 59 cruces", "retraso", M("37.6"))]),
  ("Genders y Razavi (2016) \\citep{Genders2016_DQTSC}", "1, sintética", "SUMO", "DQN (CNN)",
   [("otro RL", "retraso", M("82.4"))]),
  ("Gao et al. (2017) \\citep{Gao2017_DQN}", "1, sintética", "SUMO", "DQN",
   [("fijo no declarado", "retraso", M("86") + " máx."), ("LQF", "retraso", M("47") + " máx.")]),
  ("Mousavi et al. (2017) \\citep{Mousavi2017_PGDQN}", "1, sintética", "SUMO",
   "gradiente de política y DQN (CNN)",
   [("fijo sin tunear", "retraso", "sin cifra"), ("otro RL", "retraso", M("72.8"))]),
  ("IntelliLight (2018) \\citep{Wei2018_IntelliLight}", "1 (sintética y 24 reales, una a una)", "SUMO",
   "DQN",
   [("fijo tuneado", "viaje", M("40.3")), ("SOTL", "viaje", M("22.1"))]),
  ("FRAP (2019) \\citep{Zheng2019_FRAP}", "1 (18 cruces con demanda real)", "SUMO", "FRAP (DQN)",
   [("fijo tuneado", "viaje", M("64.1")), ("Webster", "viaje", M("58.1"))]),
  ("Liang et al. (2019) \\citep{Liang2019_3DQN}", "1, sintética", "SUMO", "3DQN",
   [("fijo sin tunear", "espera", M("25.7"))]),
  ("PressLight (2019) \\citep{Wei2019_PressLight}", "3 a 16, reales; 6 a 20, sintéticas", "CityFlow",
   "DQN con presión",
   [("fijo sin tunear", "viaje", M("52.1")), ("onda verde", "viaje", M("50.6")),
    ("Max-Pressure", "viaje", M("42.3"))]),
  ("Wang et al. (2019) \\citep{Wang2019_EventData3DQN}", "1, sintética", "SUMO", "3DQN",
   [("Webster", "retraso", M("21.2")), ("actuado", "retraso", M("10.1"))]),
  ("Ault et al. (2020) \\citep{Ault2020_Interpretable}", "1, real", "SUMO", "DQN regulable, PPO",
   [("actuado", "retraso", M("19.4") + " máx."), ("actuado, demanda alta", "retraso", "peor, PPO")]),
 ]),
 ("tab:trabajos-comparados-3",
  "Trabajos comparados: redes con varios agentes",
  "Trabajos comparados, tercer frente: redes con varios agentes. Retraso en el cruce: retraso medido "
  "solo en la intersección, no en todo el viaje. Mismas convenciones que la "
  "Tabla~\\ref{tab:trabajos-comparados}.",
 [
  ("S2R2L (2019) \\citep{Guo2019_S2R2L}", "16, sintética", "SUMO", "DQN descentralizado",
   [("Max-Pressure", "retraso", M("34.6")),
    ("Max-Pressure con verde máximo ajustado", "retraso", M("19.9"))]),
  ("CoLight (2019) \\citep{Wei2019_CoLight}", "12 a 196, reales; 36, sintética", "CityFlow",
   "DQN con atención",
   [("fijo sin tunear", "viaje", M("25.2")), ("Max-Pressure", "viaje", M("12.7"))]),
  ("MA2C (2020) \\citep{Chu2020_MA2C}", "30, real; 25, sintética", "SUMO", "MA2C",
   [("Greedy", "retraso", M("20.8")), ("otro RL (IA2C)", "retraso", M("30.9")),
    ("Greedy", "retraso en el cruce", M("64.1"))]),
  ("MPLight (2020) \\citep{Chen2020_MPLight}", "2510, real; 16, sintética", "CityFlow", "DQN con presión",
   [("fijo sin tunear", "viaje", M("47.5")), ("Max-Pressure", "viaje", M("14.4"))]),
  ("FMA2C (2020) \\citep{Ma2020_FMA2C}", "30, real; 16, sintética", "SUMO", "MA2C jerárquico",
   [("Greedy", "retraso", M("6.3") + " Mónaco"), ("Greedy", "retraso", P("10.8") + " malla"),
    ("otro RL (MA2C)", "retraso", M("55.7")), ("Greedy", "retraso en el cruce", M("90.5") + " malla")]),
  ("AttendLight (2020) \\citep{Oroojlooy2020_AttendLight}", "1 (112 cruces), reales y sintéticas",
   "CityFlow", "atención y gradiente de política",
   [("fijo sin tunear", "viaje", M("46")), ("Max-Pressure", "viaje", M("39"))]),
  ("EPyMARL en RESCO (2022) \\citep{Ault2022_EPyMARL}", "3 a 21, reales", "SUMO",
   "nueve MARL (IPPO, MAPPO, QMIX y otros)",
   [("plan real, corredor de 3 cruces", "retraso", "ninguno lo supera")]),
  ("X-Light (2024) \\citep{Jiang2024_XLight}", "8 a 25, reales y sintéticas", "SUMO",
   "PPO con \\textit{transformer}",
   [("fijo sin tunear", "viaje", M("28.8")), ("fijo sin tunear", "viaje", M("27.0") + " IPPO")]),
  ("CoSLight (2024) \\citep{Ruan2024_CoSLight}", "8 a 29, reales y sintéticas", "SUMO",
   "selección de colaboradores",
   [("fijo sin tunear", "viaje", M("27.3")), ("Max-Pressure", "viaje", M("13.8")),
    ("Max-Pressure", "viaje", M("5.7")),
    ("fijo sin tunear, red de Nanshan", "viaje", P("2.0") + " IPPO, " + P("2.1") + " MAPPO")]),
 ]),
 ("tab:trabajos-comparados-4",
  "Trabajos comparados: América Latina y sistemas en operación",
  "Trabajos comparados, cuarto frente: América Latina y sistemas en operación. Campo: medición en "
  "calles. En velocidad, un valor positivo es mejora. Mismas convenciones que la "
  "Tabla~\\ref{tab:trabajos-comparados}.",
 [
  ("SCOOT (1999) \\citep{DETR1999_SCOOT}", "varias ciudades, reales", "campo", "SCOOT, sin RL",
   [("fijo actualizado", "retraso", M("12")), ("fijo típico", "retraso", M("20")),
    ("actuado aislado", "retraso", M("23"))]),
  ("FHWA (2008) \\citep{Koonce2008_TSTM}", "síntesis de EE.~UU.", "--", "tiempos actualizados, sin RL",
   [("operación actual (proyección)", "retraso", M("15") + " a " + M("40"))]),
  ("SURTRAC (2013) \\citep{Smith2013_Surtrac}", "9, real", "campo", "planificación en línea, sin RL",
   [("actuado coordinado", "viaje", M("25.8")), ("actuado coordinado", "espera", M("40.6"))]),
  ("Higuera (2016) \\citep{Higuera2016_Uniandes}", "6, real (Bogotá)", "SUMO", "Q-learning coordinado",
   [("plan real", "espera", M("62.5"))]),
  ("ASCT, FHWA (2017) \\citep{FHWA2017_EDC1ASCT}", "síntesis de EE.~UU.", "--",
   "control adaptativo, sin RL",
   [("temporización existente", "viaje", "$\\leq -10$")]),
  ("City Brain (2018) \\citep{Alibaba2018_CityBrain}", "un distrito, real", "campo", "IA sin detallar",
   [("situación previa", "velocidad", P("15"))]),
  ("Ola verde de Lima (2019) \\citep{Sovero2019_OlaVerde}", "siete avenidas, real (Lima)", "campo",
   "onda verde por franja horaria, sin RL",
   [("situación previa (cifra municipal)", "viaje", M("10"))]),
  ("Borges et al. (2021) \\citep{Borges2021_Brasilia}", "2, real", "Vissim", "\\textit{deep Q-learning}",
   [("plan real", "retraso", M("28.4"))]),
  ("Montoya (2021) \\citep{Montoya2021_PUCP}", "10, real (Lima)", "SUMO", "algoritmo genético, sin RL",
   [("plan real", "espera", M("84.7")), ("onda verde manual", "espera", M("78.6"))]),
  ("Vivacity (2021) \\citep{Velasco2021_Vivacity}", "5, real", "campo", "RL sin detallar",
   [("incumbente", "viaje", M("30")), ("actuado (simulación)", "espera", M("45"))]),
  ("Trinity (2022) \\citep{Chakrabarti2022}", "1 y 2, sintéticas", "SUMO", "DQN, A2C, PPO",
   [("fijo sin tunear", "espera", "sin cifra")]),
  ("Uniandes (2023) \\citep{Chavez2023}", "4, sintética", "SUMO", "Q-learning, SARSA, DQN, PPO",
   [("fijo sin tunear", "espera", M("63.5")), ("fijo sin tunear", "espera", M("35.8") + " Q-learning")]),
  ("Tarquino (2023) \\citep{Tarquino2023_Lima}", "7 (5 con semáforo), real (Lima)", "Aimsun",
   "actuado con detectores, sin RL",
   [("plan real", "retraso", M("35.4")), ("plan real", "viaje", M("21.2"))]),
  ("Green Light (2023) \\citep{Google2023_GreenLight}", "más de 100 ciudades, reales", "campo",
   "IA que recomienda planes",
   [("plan real", "paradas", M("30") + " máx.")]),
 ]),
]

def col(w):
    return ">{\\raggedright\\arraybackslash}p{%scm}" % w

def tabla_comparados(label, corto, largo_cap, filas):
    alto, out = 0.0, []
    out.append("\\begin{table}[H]")
    out.append("\\setstretch{1}")
    out.append("\\centering")
    out.append("\\scriptsize")
    out.append("\\setlength{\\tabcolsep}{3pt}")
    out.append("\\begin{tabular}{" + "".join(col(w) for w in AN) + "}")
    out.append("\\toprule")
    out.append("Trabajo & Red & Sim. & Algoritmo & Referencia & Métrica & Mejora (\\%) \\\\")
    out.append("\\midrule")
    for k, (t, r, s, a, comps) in enumerate(filas):
        for i, (ref, met, mej) in enumerate(comps[:-1]):
            for txt, w in ((ref, AN[4]), (met, AN[5]), (mej, AN[6])):
                if lineas(txt, w) > 1:
                    print("AVISO desalineacion:", t[:25], txt)
        for txt, w, nom in ((t, AN[0], "trabajo"), (r, AN[1], "red"), (s, AN[2], "sim"), (a, AN[3], "alg")):
            palabras_largas(txt, w, nom)
        for x in comps:
            for txt, w, nom in ((x[0], AN[4], "ref"), (x[1], AN[5], "met"), (x[2], AN[6], "mej")):
                palabras_largas(txt, w, nom)
        ref = "\\newline ".join(x[0] for x in comps)
        met = "\\newline ".join(x[1] for x in comps)
        mej = "\\newline ".join(x[2] for x in comps)
        h = max(lineas(t, AN[0]), lineas(r, AN[1]), lineas(s, AN[2]), lineas(a, AN[3]),
                sum(lineas(x[0], AN[4]) for x in comps), sum(lineas(x[1], AN[5]) for x in comps),
                sum(lineas(x[2], AN[6]) for x in comps))
        alto += h * LINEA + EXTRA
        out.append(f"{t} & {r} & {s} & {a}\n  & {ref}\n  & {met}\n  & {mej} \\\\")
        if k < len(filas) - 1:
            out.append("\\addlinespace[2pt]")
    out.append("\\bottomrule")
    out.append("\\end{tabular}")
    out.append(f"\\caption[{corto}]{{{largo_cap}}}")
    out.append(f"\\label{{{label}}}")
    out.append("\\end{table}")
    print(f"{label}: {len(filas)} obras, cuerpo ~{alto + 0.07 * (len(filas) - 1):.1f} cm")
    return "\n".join(out)

# ---------------------------------------------------------------- tabla de entradas y salidas
exec(open("ent_datos.py", encoding="utf-8").read())      # define ENT (lista de 5-uplas)
EA = [2.0, 3.8, 2.4, 2.4, 1.8]
assert abs(sum(EA) - 12.4) < 1e-9

def tabla_entradas(label, corto, largo_cap, filas, ultima_con_regla=False):
    alto, out = 0.0, []
    out.append("\\begin{table}[H]")
    out.append("\\setstretch{1}")
    out.append("\\centering")
    out.append("\\scriptsize")
    out.append("\\setlength{\\tabcolsep}{3pt}")
    out.append("\\begin{tabular}{" + "".join(col(w) for w in EA) + "}")
    out.append("\\toprule")
    out.append("Trabajo & Estado (entradas) & Acción & Recompensa & Métricas de salida \\\\")
    out.append("\\midrule")
    for k, fila in enumerate(filas):
        h = max(lineas(x, w) for x, w in zip(fila, EA))
        for x, w in zip(fila, EA):
            palabras_largas(x, w, "entradas " + fila[0][:15])
        alto += h * LINEA + EXTRA
        if ultima_con_regla and k == len(filas) - 1:
            out.append("\\midrule")
        out.append(f"{fila[0]}\n  & {fila[1]}\n  & {fila[2]}\n  & {fila[3]}\n  & {fila[4]} \\\\")
        if k < len(filas) - 1 and not (ultima_con_regla and k == len(filas) - 2):
            out.append("\\addlinespace[2pt]")
    out.append("\\bottomrule")
    out.append("\\end{tabular}")
    out.append(f"\\caption[{corto}]{{{largo_cap}}}")
    out.append(f"\\label{{{label}}}")
    out.append("\\end{table}")
    print(f"{label}: {len(filas)} filas, cuerpo ~{alto:.1f} cm")
    return "\n".join(out)

TEXTO = io.open("texto.tex", encoding="utf-8").read()
partes = {
 "COMPARADOS_1": tabla_comparados(*BLOQUES[0]),
 "COMPARADOS_2": tabla_comparados(*BLOQUES[1]),
 "COMPARADOS_3": tabla_comparados(*BLOQUES[2]),
 "COMPARADOS_4": tabla_comparados(*BLOQUES[3]),
}
n1, n2 = 12, 24
partes["ENTRADAS_1"] = tabla_entradas(
  "tab:trabajos-entradas", "Formulación de los trabajos con aprendizaje por refuerzo",
  "Formulación de los trabajos con aprendizaje por refuerzo: qué observa el agente (estado), qué "
  "decide (acción), con qué señal aprende (recompensa) y con qué métricas se evalúa. Mismo orden que "
  "las Tablas~\\ref{tab:trabajos-comparados} a~\\ref{tab:trabajos-comparados-4}, con el entorno "
  "SUMO-RL al inicio.", ENT[:n1])
partes["ENTRADAS_2"] = tabla_entradas(
  "tab:trabajos-entradas-2", "Formulación de los trabajos con aprendizaje por refuerzo (continuación)",
  "Continuación de la Tabla~\\ref{tab:trabajos-entradas}.", ENT[n1:n2])
partes["ENTRADAS_3"] = tabla_entradas(
  "tab:trabajos-entradas-3", "Formulación de los trabajos con aprendizaje por refuerzo (continuación)",
  "Continuación de la Tabla~\\ref{tab:trabajos-entradas}. La fila de la revisión da la frecuencia "
  "de cada elemento en los estudios que revisa, en porcentaje; la última fila describe esta tesis.",
  ENT[n2:], ultima_con_regla=True)
for k, v in partes.items():
    TEXTO = TEXTO.replace("@@" + k + "@@", v)
assert "@@" not in TEXTO
with io.open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
    f.write(TEXTO)
print("escrito", SALIDA, len(TEXTO.splitlines()), "lineas")
