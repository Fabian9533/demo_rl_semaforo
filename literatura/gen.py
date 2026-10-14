# -*- coding: utf-8 -*-
"""Genera las tablas del Anexo E desde datos transcritos de wf1/lit_todas.json.

Solo fichas 'confirmado' o 'corregido'. Cada linea de comparacion: (referencia, metrica, mejora).
Estima alturas para partir las tablas y calcula las medianas por categoria.
"""
import io, math, re, statistics

CM_CHAR = 0.135          # cm por caracter en \scriptsize (cmr8), estimado
LINEA = 0.334            # cm por linea (9.5 pt)
EXTRA_FILA = 0.10        # struts de p{}

def largo(tex):
    t = re.sub(r"\\citep\{[^}]*\}", "[00]", tex)
    t = re.sub(r"\$-\$", "-", t)
    t = t.replace("$", "")
    t = re.sub(r"\\times", "x", t)
    t = re.sub(r"\\leq", "<", t)
    t = re.sub(r"\\textit\{([^}]*)\}", r"\1", t)
    t = re.sub(r"\\emph\{([^}]*)\}", r"\1", t)
    t = re.sub(r"\\,", "", t)
    t = re.sub(r"\\%", "%", t)
    t = re.sub(r"\\_", "_", t)
    t = re.sub(r"_\{?([^}\s]*)\}?", r"\1", t)
    t = re.sub(r"\\[a-zA-Z]+\s?", "", t)
    t = t.replace("{", "").replace("}", "").replace("~", " ")
    return len(t)

def lineas(tex, ancho):
    cap = ancho / CM_CHAR
    return max(1, math.ceil(largo(tex) / cap))

# --------------------------------------------------------------------------------------------
# Tabla comparada: (bloque, trabajo, red, sim, algoritmo, [(ref, metrica, mejora), ...])
A_T, A_R, A_S, A_A, A_REF, A_M, A_MJ = 2.1, 1.9, 1.1, 2.0, 2.5, 1.3, 1.5
assert abs(A_T + A_R + A_S + A_A + A_REF + A_M + A_MJ - 12.4) < 1e-9

M = lambda x: "$-$" + x          # negativo
P = lambda x: "$+$" + x          # positivo

COMP = [
 ("Bancos de prueba, comparaciones amplias y control por presión", [
  ("RESCO (2021) \\citep{Ault2021_RESCO}", "1 a 21, reales; 16, sintéticas", "SUMO",
   "IDQN, IPPO, MPLight, FMA2C",
   [("plan real", "retraso", "sin cifra"), ("Max-Pressure", "retraso", M("11")),
    ("Greedy", "retraso", M("20")), ("otro RL (IDQN)", "retraso", M("2.1") + " IPPO")]),
  ("Genders y Razavi (2019) \\citep{Genders2019_Framework}", "2, sintética", "SUMO", "DQN, DDPG",
   [("fijo tuneado", "viaje", M("8.9")), ("fijo tuneado", "viaje", M("1.3") + " DQN"),
    ("Webster adaptativo", "viaje", P("1.4")), ("Max-Pressure", "viaje", P("22.0"))]),
  ("LIT (2019) \\citep{Zheng2019_LIT}", "1 (12 cruces) y redes de 4 a 16, reales", "SUMO", "LIT (DQN)",
   [("fijo sin tunear", "viaje", M("55.5")), ("Webster", "viaje", M("34.0")),
    ("fijo sin tunear", "viaje", M("65.8") + " redes"), ("Webster", "viaje", M("37.6") + " redes")]),
  ("Lioris et al. (2014) \\citep{Lioris2014_MaxPressure}", "13, real", ".Q",
   "Max-Pressure \\citep{Varaiya2013_MaxPressure}, sin RL",
   [("fijo tuneado (LP)", "viaje", M("23.6"))]),
  ("Cabrejas-Egea et al. (2021) \\citep{CabrejasEgea2021_Comercial}", "1 (dos geometrías), sintética",
   "Vissim", "DDQN, DDDQN, A2C",
   [("fijo no declarado", "retraso", M("85.2")), ("MOVA (actuado)", "retraso", M("21.7")),
    ("MOVA (actuado)", "retraso", M("48.0")), ("MOVA (actuado)", "retraso", M("56.9")),
    ("SURTRAC", "retraso", M("26.6"))]),
  ("Efficient Pressure (2021) \\citep{Wu2021_EfficientMP}", "12 y 16, reales", "CityFlow",
   "Efficient-CoLight (DQN)",
   [("fijo no declarado", "viaje", M("38.2")), ("Max-Pressure", "viaje", M("3.7"))]),
  ("LibSignal (2022) \\citep{Mei2024_LibSignal}", "1 a 16 en SUMO (196 en CityFlow), reales y sintéticas",
   "SUMO y CityFlow", "IDQN, IPPO, CoLight, MPLight y otros",
   [("fijo sin tunear", "viaje", M("55.1")), ("Max-Pressure", "viaje", M("5.7")),
    ("Max-Pressure", "viaje", P("18.5") + " IPPO")]),
  ("Advanced-XLight (2022) \\citep{Zhang2022_AdvancedMP}", "12 a 192, reales", "CityFlow",
   "Advanced-CoLight (DQN)",
   [("fijo no declarado", "viaje", M("38.6")), ("Max-Pressure", "viaje", M("8.6"))]),
  ("T-REX (2025) \\citep{Nguyen2025_TREX}", "3 a 21, reales; 16, sintética", "SUMO",
   "IDQN, IPPO, MPLight, FMA2C",
   [("plan real", "viaje", M("17.7")), ("plan real", "viaje", P("5.1") + " IPPO"),
    ("fijo sin tunear", "viaje", M("28.7")), ("Max-Pressure", "viaje", M("20.2"))]),
 ]),
 ("Cruce aislado y corredor", [
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
  ("PressLight (2019) \\citep{Wei2019_PressLight}", "3 a 16, reales; 6, sintética", "CityFlow",
   "DQN con presión",
   [("fijo sin tunear", "viaje", M("52.1")), ("onda verde", "viaje", M("50.6")),
    ("Max-Pressure", "viaje", M("42.3"))]),
  ("Wang et al. (2019) \\citep{Wang2019_EventData3DQN}", "1, sintética", "SUMO", "3DQN",
   [("Webster", "retraso", M("21.2")), ("actuado", "retraso", M("10.1"))]),
  ("Ault et al. (2020) \\citep{Ault2020_Interpretable}", "1, real", "SUMO", "DQN regulable, PPO",
   [("actuado", "retraso", M("19.4") + " máx."), ("actuado", "retraso", "peor, PPO")]),
 ]),
 ("Redes con varios agentes", [
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
   "CityFlow", "atención y REINFORCE",
   [("fijo sin tunear", "viaje", M("46")), ("Max-Pressure", "viaje", M("39"))]),
  ("EPyMARL en RESCO (2022) \\citep{Ault2022_EPyMARL}", "3 a 21, reales", "SUMO",
   "nueve MARL (IPPO, MAPPO, QMIX y otros)",
   [("plan real", "retraso", "ninguno lo supera")]),
  ("X-Light (2024) \\citep{Jiang2024_XLight}", "8 a 25, reales y sintéticas", "SUMO",
   "PPO con \\textit{transformer}",
   [("fijo sin tunear", "viaje", M("28.8")), ("fijo sin tunear", "viaje", M("27.0") + " IPPO"),
    ("fijo sin tunear", "retraso", M("40.4") + " IPPO")]),
  ("CoSLight (2024) \\citep{Ruan2024_CoSLight}", "8 a 29, reales y sintéticas", "SUMO",
   "selección de colaboradores",
   [("fijo sin tunear", "viaje", M("27.3")), ("fijo sin tunear", "viaje", P("2.0") + " IPPO"),
    ("fijo sin tunear", "viaje", P("2.1") + " MAPPO"), ("Max-Pressure", "viaje", M("13.8")),
    ("Max-Pressure", "viaje", M("5.7"))]),
 ]),
 ("América Latina y sistemas en operación", [
  ("DETR (1999) \\citep{DETR1999_SCOOT}", "varias ciudades, reales", "campo", "SCOOT, sin RL",
   [("fijo actualizado", "retraso", M("12")), ("fijo típico", "retraso", M("20")),
    ("actuado aislado", "retraso", M("23"))]),
  ("FHWA (2008) \\citep{Koonce2008_TSTM}", "síntesis de EE.~UU.", "--", "retemporización, sin RL",
   [("operación actual", "retraso", M("15") + " a " + M("40"))]),
  ("FHWA (EDC-1) \\citep{FHWA2017_EDC1ASCT}", "síntesis de EE.~UU.", "--",
   "control adaptativo, sin RL",
   [("fijo existente", "viaje", "$\\leq -10$")]),
  ("SURTRAC (2013) \\citep{Smith2013_Surtrac}", "9, real", "campo", "planificación en línea, sin RL",
   [("actuado coordinado", "viaje", M("25.8")), ("actuado coordinado", "espera", M("40.6"))]),
  ("Higuera (2016) \\citep{Higuera2016_Uniandes}", "6, real (Bogotá)", "SUMO",
   "Q-learning coordinado",
   [("plan real", "espera", M("62.5"))]),
  ("City Brain (2018) \\citep{Alibaba2018_CityBrain}", "un distrito, real", "campo", "IA sin detallar",
   [("situación previa", "velocidad", P("15"))]),
  ("Ola verde de Lima (2019) \\citep{Sovero2019_OlaVerde}", "siete avenidas, real (Lima)", "campo",
   "onda verde por franja horaria, sin RL",
   [("situación previa", "viaje", M("10"))]),
  ("Borges et al. (2021) \\citep{Borges2021_Brasilia}", "2, real (Brasil)", "Vissim", "\\textit{deep Q-learning}",
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

def alto_fila(t, r, s, a, comps):
    col = [lineas(t, A_T), lineas(r, A_R), lineas(s, A_S), lineas(a, A_A)]
    stack_ref = sum(lineas(x[0], A_REF) for x in comps)
    stack_m = sum(lineas(x[1], A_M) for x in comps)
    stack_mj = sum(lineas(x[2], A_MJ) for x in comps)
    # aviso de desalineacion: una linea que no es la ultima y parte en dos
    for k, (ref, met, mej) in enumerate(comps[:-1]):
        for txt, w, nom in ((ref, A_REF, "ref"), (met, A_M, "met"), (mej, A_MJ, "mej")):
            if lineas(txt, w) > 1:
                print("DESALINEA", t[:30], nom, txt)
    return max(col + [stack_ref, stack_m, stack_mj])

def fila_tex(t, r, s, a, comps):
    ref = "\\newline ".join(x[0] for x in comps)
    met = "\\newline ".join(x[1] for x in comps)
    mej = "\\newline ".join(x[2] for x in comps)
    return f"{t} & {r} & {s} & {a} & {ref} & {met} & {mej} \\\\"

tot = 0
for bloque, filas in COMP:
    print("==", bloque, len(filas))
    for f in filas:
        h = alto_fila(*f)
        tot += h
        print(f"  {h:2d}  {f[0][:40]}")
print("lineas totales comparados:", tot, " obras:", sum(len(f) for _, f in COMP))

# --------------------------------------------------------------------------------------------
# Medianas por categoria (solo RL; una cifra por obra y categoria). Ver el comentario % fuente.
CAT = {
 "A fijo sin tunear o no declarado": {
   "LibSignal": -55.1, "T-REX": -28.7, "LIT": statistics.median([-55.5, -65.8]),
   "Cabrejas-Egea": -85.2, "Efficient Pressure": -38.2, "Advanced-XLight": -38.6,
   "Gao (max.)": -86.0, "Liang": -25.7, "PressLight": -52.1, "CoLight": -25.2, "MPLight": -47.5,
   "AttendLight": -46.0, "X-Light": -28.8, "CoSLight": -27.3, "Uniandes": -63.49},
 "B fijo tuneado, Webster o plan real": {
   "Genders 2019": -8.9, "LIT": statistics.median([-34.0, -37.6]), "T-REX": -17.7,
   "MARLIN-ATSC": statistics.median([-35.5, -21.4, -37.6]), "IntelliLight": -40.3,
   "FRAP": statistics.median([-64.1, -58.1]), "PressLight": -50.6, "Wang": -21.2,
   "Higuera": -62.49, "Borges": -28.4},
 "C actuado": {
   "Cabrejas-Egea": statistics.median([-21.7, -48.0, -56.9]),
   "MARLIN-ATSC": statistics.median([-25.1, -18.7]), "Wang": -10.1, "Ault 2020 (max.)": -19.4},
 "D Max-Pressure u otra heuristica": {
   "RESCO": statistics.median([-11.0, -20.0]), "Genders 2019": 22.0, "Cabrejas-Egea (SURTRAC)": -26.6,
   "Efficient Pressure": -3.7, "LibSignal (SUMO)": -5.7, "Advanced-XLight": -8.6, "T-REX": -20.2,
   "Gao (LQF, max.)": -47.0, "IntelliLight (SOTL)": -22.1, "PressLight": -42.3,
   "S2R2L (MP ajustado)": -19.9, "CoLight": -12.7, "MA2C (Greedy)": -20.8, "MPLight": -14.4,
   "FMA2C (Greedy)": statistics.median([-6.3, 10.8]), "AttendLight": -39.0,
   "CoSLight": statistics.median([-13.8, -5.7])},
}
for c, d in CAT.items():
    v = sorted(d.values())
    print(c, "n=", len(v), "mediana=", round(statistics.median(v), 3), "rango", v[0], v[-1])
    print("   ", "; ".join(f"{k} {x:+.2f}" for k, x in d.items()))

# CoLight frente a MP: mediana de los 5 escenarios de la ficha
print("CoLight MP", statistics.median([-6.6, -12.7, -10.7, -29.6, -19.4]))
print("MPLight MP", statistics.median([-14.4, -34.8, -21.9, -13.1, -5.1]))

with io.open("comparados_filas.tex", "w", encoding="utf-8") as f:
    for bloque, filas in COMP:
        f.write(f"%% BLOQUE {bloque}\n")
        for fi in filas:
            f.write(fila_tex(*fi) + "\n")
