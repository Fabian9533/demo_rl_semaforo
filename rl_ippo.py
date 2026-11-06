"""
rl_ippo.py - Modulo U4: coordinacion distribuida entre semaforos con IPPO (PPO con pesos
compartidos: un solo actor y un solo critico para todos los semaforos del escenario, cada
agente decide con su propia observacion). Torch puro, sin Gym ni stable-baselines3.

Modos:
  python rl_ippo.py train --escenario red --variante vecinos --episodios 200 --seed 42
  python rl_ippo.py demo  --escenario red --politica politica_red_vecinos_s42.pt [--gui]

Variantes (--variante), en orden incremental:
  local    observacion local: colas y vehiculos en movimiento por aproximacion, fase activa,
           tiempo de verde, si ya puede cambiar e id del semaforo; ranuras de vecinos a cero.
  vecinos  local + estado extendido con lo que envian los cruces vecinos (mensajeria).
  spill    vecinos + penalizacion por spillback en los enlaces de salida hacia el vecino.
  cambio   vecinos + penalizacion por cambio de fase (opcional).

Lo que no cambia respecto de U2: fases, ambar de 3 s, verde minimo 10 s (5 s en giros) y
maximo 60 s, decision cada 5 s contados desde el inicio del verde propio (la primera a los
5 s), episodio = 1 h de demanda mas vaciado (tope 6000 pasos) y los pesos w1 = 1, w2 = 0.01.
Lo que cambia en la recompensa: el termino de cola detenida se sustituye por los
vehiculos-equivalentes retrasados n_a * (1 - v_media_a / v_max_a) de cada aproximacion (la
version por segundo del timeLoss, metrica primaria) y el agente recibe la suma por segundo
sobre su intervalo de decision dividida entre 5 (retraso-segundos), no el nivel en el
instante siguiente. La formula de U2 se sigue reportando a reloj fijo de 5 s para comparar.

Mensajeria: cada 5 s de reloj global cada semaforo publica a cada vecino el eje de su verde
(EO, NS o ambar), el tiempo en esa fase, el outflow que le va a enviar, la cola que tiene
esperando hacia el y la cola que ve en la salida del vecino. El receptor lo lee en su propia
decision; --latencia y --perdida simulan un canal imperfecto (solo evaluacion).

Cambios del plan de pruebas v2 (plan2/ESPEC.md):
  - Escenarios nuevos desde escenarios_plan2.py (VECINOS y LADOS): red_alta y malla3.
  - N lados por semaforo (oeste, este y, en malla3, norte y sur). Observacion de dimension
    12 + n_id + 8 * lados, con n_id = max(3, semaforos). Con dos lados el layout es el de
    siempre (31; id en 12..14; ranuras en 15 y 23) y las politicas de la fase exploratoria cargan igual.
    El mensaje dice el eje del verde; "verde hacia mi" es verde EO para un vecino al oeste o
    al este y verde NS para uno al norte o al sur.
  - Validacion con la politica congelada (argmax) en --val-seeds (999 y 1999) cada
    --eval-cada episodios y en el ultimo, sin tocar el RNG del entrenamiento. Checkpoint en
    cada validacion (checkpoints/<tag>_ep<NNN>.pt/.json) y politica publicada = checkpoint de
    menor val (empate: el mas tardio), con ep_elegido, val_elegido y val_serie en el meta.
  - ret_retraso, ret_colas y ret_spill medidos cada segundo en todos los modos.
  - El CSV de entrenamiento se reescribe desde cero; tripinfo unico por corrida.
  - Ganchos para decisores externos (rl_dqn.py, rl_mappo.py), sin cambiar los numeros de IPPO.

Correcciones del diagnostico del corredor (25.10.2026, plan2/diag_corredor/PRERREGISTRO.md). Apagadas
por defecto: sin ellas el entrenamiento da los mismos numeros que antes.
  --v2   (H3) los dos cambios de la variante V2 del Anexo G (plan2/exploratorio_coord/codigo/smdp_crn.diff):
         descuento por segundo en gae(), gamma^(dt/5) y (gamma*lam)^(dt/5) con dt el intervalo real de
         cada decision, y exploracion comun: un solo numero aleatorio u por segundo para todos los que
         deciden (a = 1 si p_cambiar > u; generador propio default_rng(semilla del episodio + 104729)).
         Solo en train; la evaluacion (argmax) no cambia.
  --recompensa-insercion   (H2, INS) cada segundo se suman al retraso del agente, con el peso de un
         vehiculo detenido (W1), los vehiculos que esperan para entrar a la red por las aristas de entrada
         de sus accesos (traci.simulation.getPendingVehicles; cada vehiculo se asigna por el flujo de
         origen del .rou.xml). Columna ins_espera del CSV: esa suma en vehiculo-segundos.
  --etiqueta X   se agrega a la variante en todos los nombres (resultados_<esc>_ippo_vecinos_X_s<b>.csv,
         politica_<esc>_vecinos_X_s<b>.pt, checkpoints); evaluar.py llama al brazo ippo_vecinos_X_s<b>.
  --criterio-val total   el checkpoint publicado (y val_elegido, con el que se elige la base mediana) se
         elige por el retraso total en la validacion (timeLoss + espera para entrar, retraso_total_prom)
         en vez del timeLoss. Por defecto timeloss, como siempre. La validacion registra las dos metricas
         en todos los casos: val_<s> y val (timeLoss, igual que antes) y, al final del CSV, val_total_<s> y
         val_total; en el meta, val_serie (timeLoss) y val_total_serie, y ep_elegido_timeloss y
         ep_elegido_total con lo que habria elegido cada criterio.
  --obs-insercion   (Enmienda 2 del prerregistro, INS observable) cuatro entradas mas al final de la
         observacion, una por acceso (o, e, n, s): n / (n + plazas del acceso), con n los vehiculos que esperan
         para entrar por esa arista (0.5 = una aproximacion llena esperando afuera). Va en el meta
         (opciones.obs_insercion, dim_obs) y evaluar.py la activa al cargar la politica. Apagada, la
         observacion y los numeros no cambian.

Plan 3 (05.11.2026; plan3/doc/PLAN3.md 1.1 y 1.2, DECISIONES B13, B15 y B22). Todo apagado por defecto: sin estas
opciones salen el mismo CSV (salvo la columna segundos, que es tiempo de reloj), los mismos checkpoints y la misma
politica publicada que antes. Contrato de --guardar-estado, --hasta-ep y --reanudar: plan3/doc/informe_ent1.md.
  --solo-descuento, --solo-exploracion   ablacion de V2: solo el descuento por segundo o solo la exploracion
         comun. Las dos juntas son --v2 (mismo entrenamiento y mismo meta).
  --lr-horizonte N --lr-piso F   lr = lr0 * max(F, 1 - (ep - 1) / N); por defecto N = --episodios y F = 0, la
         formula de siempre. Con N = 200 y F = 0.1, los episodios 1-181 son los de una corrida de 200 sin piso.
  --registro-extendido   columnas al final del CSV: val_<s> y val_total_<s> de las semillas de validacion que no
         tienen columna fija, var_explicada (del critico antes de actualizar), frac_forzadas (decisiones con una
         sola accion legal), msg_edad (edad media del mensaje al decidir, s) y ent_coef (coeficiente de entropia).
  --guardar-estado   en cada checkpoint, en el corte de --hasta-ep y en el ultimo episodio escribe aparte
         checkpoints/<tag>_epNNN.estado.pt: pesos, Adam con su contador, random, numpy global, torch, el default_rng
         de sembrar, las series de validacion, el CSV hasta NNN, la tasa de cada episodio y el sha256 de los
         checkpoints. El .pt de la politica no cambia (Politica.cargar sigue con weights_only=True).
  --hasta-ep K   corta despues del episodio K: guarda el estado y sale con codigo 0 sin publicar la politica.
  --reanudar ESTADO|auto   sigue exacto desde un estado. Misma etiqueta: conserva los checkpoints y las filas del
         CSV <= NNN y borra lo > NNN de un intento caido. Etiqueta nueva: copia los checkpoints y estados <= NNN,
         las filas del CSV <= NNN (con la etiqueta nueva) y las series de validacion, y anota reanudado_de en el
         meta; si un intento anterior ya avanzo desde ese mismo estado, sigue desde su estado mas avanzado. auto:
         el estado de mayor NNN de la propia etiqueta; sin estados empieza de cero; si la corrida ya llego a
         --hasta-ep o ya publico, sale con codigo 0 sin tocar nada.
  --validar-args   solo revisa los argumentos (validar_args, la que usa chequeos_previos) y sale con 0: no lee el
         escenario ni escribe nada.
  Robustez (revision del 05.11.2026; sin opcion y sin cambiar ningun numero ni los bytes de checkpoints y politica):
         checkpoints, estados, copias y la politica publicada se escriben en un temporal que se baja a disco (fsync) y
         se renombra; al publicar, primero el .json y al final el .pt. Un estado que no sirve (zip danado, no carga,
         checkpoints que no coinciden con su sha256) se renombra a .roto con un AVISO y auto sigue desde el anterior.
         Si otro programa tiene tomado el CSV (Excel), el tramo sigue con el CSV en memoria (el estado lo guarda) y lo
         escribe al final (el ultimo tramo, con esperas). Un episodio rehecho que no repite el intento anterior (B22)
         queda en checkpoints/<tag>_rehechos.json y en meta["reanudaciones"]. El estado anota la huella del codigo
         de cada tramo; el meta la lleva (meta["tramos"]) solo si cambio entre tramos.

Plan 3, Etapas 3 y 4 (PLAN3 3.1-3.4 y Etapa 4; DECISIONES B14, B16, B24 y B25). Apagadas por defecto; las
activas van al meta (opciones), a la configuracion que compara --reanudar y, si llevan estado, al estado.
Informe: plan3/doc/informe_ent2.md.
  --obs-cercana L   (M3) 16 + lados entradas al final de la observacion: por acceso, vehiculos a menos de L m de la
         linea detenidos y en movimiento (detectores E2 de L m por carril, suscritos), espera del primero y
         giro_izq (alguien detenido en el primer tramo interno del giro a la izquierda: espera el hueco dentro del
         cruce); por lado con vecino, los detenidos del enlace de SALIDA i->j (la ranura vieja cola_mi_salida mide
         el que entra: hallazgo 5 de CLAUDE.md). Dimension 31 -> 49 (53 -> 73 en malla3). Los E2 van en
         e2_<esc>_<L>.add.xml (archivo_e2; p3_preparar.py puede escribirlo antes) y se suman a los adicionales del
         .sumocfg.
  --norm-valor [--norm-beta B]   el critico aprende el retorno normalizado con medias moviles (ValueNorm de MAPPO,
         Yu et al. 2022; B = 0.99999 por defecto; la politica por red usa una mas rapida, fijada con un piloto).
  --sin-forzadas   (exige el descuento por segundo de V2) las decisiones con una sola accion legal se aplican pero
         no entran al lote ni cierran la decision pendiente: un cambio dura 13 s (ambar + verde minimo).
  --msg-cada-paso   los mensajes se publican cada segundo: al decidir, el del segundo actual (edad 0).
  --ent-final X   coeficiente de entropia lineal de HIPER["ent"] a X en el horizonte de la tasa, constante despues.
  --paso-decision K   (exige el descuento por segundo de V2) reloj de decision: cada K s antes del verde minimo
         (decisiones forzadas), cada K s desde el verde minimo y una al verde maximo; mensajes cada K s. La
         recompensa y el descuento de V2 siguen en unidades de 5 s (PASO_CONTROL). Con K = 5, el reloj de siempre.
  --escala-demanda a,b [--curriculo K]   (politica por red) cada episodio sortea f ~ U(a, tope) y corre sumo con
         --scale f; tope = b, o sube de a a b en K episodios. Generador propio: default_rng(base + 15485863).
  --val-escalas e1,e2,...   valida en varios niveles de demanda (--scale e): por nivel, la media de las semillas;
         val y val_total son la media geometrica de los niveles.
  configurar_colas_cero(True)   (a3, evaluar3.py --colas-cero) al jugar, las colas de la observacion valen cero.

Interfaz para decisores externos (correr_episodio):
  correr_episodio(modo, politica, gui, delay, seed, tripinfo=None, serie=None, latencia=0,
                  perdida=0.0, variante="vecinos", buffer=None, decidir=None,
                  transicion=None, con_estado=False) -> dict de metricas
  decidir(deciden, obs, mascara, modo, info) -> (acciones, extras)
      deciden: lista de tls que deciden en este segundo (orden de C["indice"]);
      obs: np.float32 (k, C["dim_obs"]); mascara: np.float32 (k, 2) [mantener, cambiar];
      modo: "train" o "demo"; info: {"t": segundo, "seed": semilla SUMO, "variante": ...,
      "estado": estado global (np.float32, len(C["indice"]) * C["dim_obs"]) si con_estado,
      si no None}. Devuelve k acciones enteras (0 mantener, 1 cambiar; deben ser legales
      segun la mascara) y k extras (cualquier objeto o None) que vuelven en la transicion.
      Si decidir es None decide `politica` (IPPO). No combinar decidir con buffer.
  transicion(tls, obs, accion, recompensa, obs_sig, mascara_sig, info) -> None
      Una llamada por decision cerrada de cada agente: recompensa = suma de r_paso (con los
      terminos de la variante) desde esa decision / 5 * ESCALA_R; obs_sig y mascara_sig son
      las de su siguiente decision (o las del cierre del episodio). info = {"extra": extra de
      decidir para esa decision, "ultima": True en la ultima transicion del agente,
      "vaciada": True si la red se vacio (terminal; si no, se trunco en 6000 s), "t": segundo
      de obs_sig, "estado_sig": estado global en ese instante si con_estado, si no None}.
  El estado global es la concatenacion de observar() de todos los semaforos en el orden de
  C["indice"]. Funciones reutilizables: preparar, observar, mascara, Politica, validar,
  limpiar_checkpoints, ruta_checkpoint, elegir_checkpoint, sembrar, hash_git.
"""
import io
import os
import re
import csv
import sys
import glob
import json
import time
import random
import shutil
import zipfile
import hashlib
import argparse
import subprocess

import numpy as np
import torch
import torch.nn as nn

try:
    import traci
    import traci.constants as tc
    import sumolib
except ImportError:
    if "SUMO_HOME" in os.environ:
        sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
        import traci
        import traci.constants as tc
        import sumolib
    else:
        sys.exit("No encuentro TraCI. Define la variable SUMO_HOME o ejecuta: pip install traci sumolib")

import comun
import rl_corredor as rc
import escenarios_plan2

# ---------------- Escenarios ----------------
# Vecinos de cada semaforo: por lado (oeste, este y en malla3 norte, sur) el vecino, el enlace
# que llega desde el vecino (j -> i, es aproximacion propia) y el enlace que sale hacia el (i -> j).
VECINOS = {
    "corredor": {
        "semaforo_C1": {"oeste": None, "este": ("semaforo_C2", "C2_C1", "C1_C2")},
        "semaforo_C2": {"oeste": ("semaforo_C1", "C1_C2", "C2_C1"), "este": None},
    },
    "red": {
        "semaforo_C1": {"oeste": None, "este": ("semaforo_C2", "C2_C1", "C1_C2")},
        "semaforo_C2": {"oeste": ("semaforo_C1", "C1_C2", "C2_C1"),
                        "este": ("semaforo_C3", "C3_C2", "C2_C3")},
        "semaforo_C3": {"oeste": ("semaforo_C2", "C2_C3", "C3_C2"), "este": None},
    },
    "cruce": {"semaforo_C": {"oeste": None, "este": None}},
}
VECINOS["corredor_alta"] = VECINOS["corredor"]
VECINOS.update(escenarios_plan2.VECINOS)
for _esc, (_base, _, _) in escenarios_plan2.DERIVADOS.items():     # barrido de demanda
    VECINOS[_esc] = VECINOS[_base]

# rl_corredor tambien importa escenarios_plan2; se suman aqui por si acaso
_FUENTES = {**escenarios_plan2.ESCENARIOS_RC, **rc.ESCENARIOS}
ESCENARIOS = {esc: {**e, "vecinos": VECINOS[esc]} for esc, e in _FUENTES.items() if esc in VECINOS}
ESCENARIOS["cruce"] = {"cfg": "cruce.sumocfg", "semaforos": {"semaforo_C": ["W_C", "E_C", "N_C", "S_C"]},
                       "enlaces": [], "flujos_corredor": None, "vecinos": VECINOS["cruce"]}
# Orden de las aproximaciones en SEMAFOROS: [avenida oeste, avenida este, norte, sur]
LADOS = {esc: tuple(escenarios_plan2.LADOS.get(esc, ("oeste", "este"))) for esc in ESCENARIOS}
for _esc, (_base, _, _) in escenarios_plan2.DERIVADOS.items():     # los lados de su red base
    LADOS[_esc] = LADOS[_base]          # (22.10.2026: los derivados de malla3 miran cuatro lados)
OPUESTO = {"oeste": "este", "este": "oeste", "norte": "sur", "sur": "norte"}
IDX_LADO = {"oeste": 0, "este": 1, "norte": 2, "sur": 3}     # indice de la aproximacion de ese lado
EJE = {"oeste": "EO", "este": "EO", "norte": "NS", "sur": "NS"}

# ---------------- Parametros ----------------
PASO_CONTROL, VERDE_MAX = rc.PASO_CONTROL, rc.VERDE_MAX
W1, W2 = rc.W1, rc.W2          # recompensa base, identica a U2
W3 = 2.0                       # spill: vehiculos-equivalentes por vehiculo detenido sobre la bisagra
W4 = 2.0                       # cambio: costo de cada cambio de fase
ESCALA_R = 0.02                # lo que ve PPO es r / 50 (valores de -5 a -10 con politicas buenas)
N_ID = 3                       # minimo de posiciones del id del semaforo (C1, C2, C3)
DIM_OBS = 15 + 2 * 8           # dos lados: bloque local + dos ranuras de vecinos (C["dim_obs"] manda)
OCULTAS = 64
# Fijados en la prueba de humo (cruce): con lr 3e-4, minilote 256 y 8 epocas la politica
# no salia de un programa fijo en 60 episodios (KL < 0.001 por actualizacion); con lr 1e-3,
# minilote 64 y 10 epocas iguala al actuado en 15 episodios. gamma 0.9 no cambio nada.
HIPER = {"gamma": 0.95, "lam": 0.95, "clip": 0.2, "epocas": 10, "minibatch": 64,
         "lr": 1e-3, "ent": 0.01, "valor": 0.5, "grad": 0.5}
EDAD_MAX = 30                  # edad de mensaje que satura la observacion (s)
RECOMPENSA = {"local": "retraso", "vecinos": "retraso", "spill": "spill", "cambio": "cambio"}
SEMILLA_EXPL = 104729          # --v2: rng de la exploracion comun = default_rng(semilla del episodio + esto)
CAMPOS_IPPO = ["variante", "base", "episodio", "semilla", "lr", "segundos", "vehiculos",
               "espera_prom", "timeloss_prom", "cola_prom", "cola_max",
               "recompensa", "recompensa_decision", "recompensa_total_decision",
               "decisiones", "decisiones_libres", "cambios_fase",
               "paradas_prom", "throughput", "co2_prom", "nox_prom", "no_terminados",
               "spillback_tasa", "spillback_seg", "spillback_eventos", "cola_max_enlace",
               "veh_max_enlace", "viaje_corredor_prom", "retraso_corredor_prom",
               "retraso_corredor_punta", "paradas_corredor", "paradas_corredor_le1",
               "spill_activaciones", "spill_suma",
               "perdida_politica", "perdida_valor", "entropia_libre", "kl_aprox", "clipfrac",
               "eval_timeloss", "eval_espera",
               "ret_retraso", "ret_colas", "ret_spill", "val_999", "val_1999", "val",
               "algoritmo", "recompensa_tipo",
               # 25.10.2026 (diagnostico del corredor): al final, para no mover las columnas de antes
               "etiqueta", "ins_espera", "ins_total", "expl_minoritaria", "dt_medio", "frac_dt8",
               "val_total_999", "val_total_1999", "val_total"]
# Plan 3, --registro-extendido: van despues de CAMPOS_IPPO y de val_<s>/val_total_<s> de las demas semillas de
# validacion. Una columna nueva entra solo con la opcion que la produce: asi el CSV de una corrida no cambia de
# columnas entre versiones del codigo y un tramo reanudado escribe las mismas que el primero.
CAMPOS_EXTENDIDOS = ["var_explicada", "frac_forzadas", "msg_edad", "ent_coef"]
VERSION_ESTADO = 1             # formato de checkpoints/<tag>_epNNN.estado.pt (--guardar-estado)
# Las claves que se agregan despues (codigo, tramos, reanudaciones; ent, norm_valor y generadores.escala de las Etapas
# 3 y 4) se leen con .get: un estado sin ellas sigue valiendo y la version no cambia
ESPERA_CSV, INTENTOS_CSV = 30, 60   # CSV tomado al final del ultimo tramo: reintenta cada 30 s durante 30 min
SEMILLA_ESCALA = 15485863      # --escala-demanda: generador del factor = default_rng(base + esto)
CERCA_MAX_ESPERA = 120.0       # --obs-cercana: espera del primero que satura la entrada (s)
BETA_NORM = 0.99999            # --norm-valor: beta por defecto de las medias moviles (ValueNorm de MAPPO)
COLAS_CERO = False             # a3 (configurar_colas_cero): fuera de C, porque preparar() vacia C
ESCALA_MIN, ESCALA_MAX = 0.1, 4.0   # --escala-demanda y --val-escalas: factores de demanda admitidos
# Opciones del meta que cambian como juega una politica (observacion, reloj y mensajes) y su valor de siempre:
# evaluar.py y revalidar_c0.py las aplican con configurar_desde_meta; demo avisa si la linea de comandos dice otra cosa
OPCIONES_QUE_ACTUAN = {"obs_insercion": False, "obs_cercana": 0.0, "paso_decision": PASO_CONTROL,
                       "msg_cada_paso": False}
DIAG_PPO = ("perdida_politica", "perdida_valor", "entropia_libre", "kl_aprox", "clipfrac")

# Se rellena con preparar(escenario)
C = {}


def preparar(escenario):
    """Fija el escenario y calcula la geometria (plazas por aproximacion y por carril) y el
    tamano de la observacion (C["lados"], C["n_id"], C["dim_obs"])."""
    e = ESCENARIOS[escenario]
    net_file, _ = comun.leer_cfg(e["cfg"])
    net = sumolib.net.readNet(net_file)
    aprox = [a for lista in e["semaforos"].values() for a in lista]
    lados = LADOS.get(escenario, ("oeste", "este"))
    n_id = max(N_ID, len(e["semaforos"]))
    C.clear()
    C.update({
        "escenario": escenario, "cfg": e["cfg"], "net": net_file,
        "semaforos": e["semaforos"], "enlaces": e["enlaces"],
        "flujos": e["flujos_corredor"], "vecinos": e["vecinos"],
        "indice": {tls: k for k, tls in enumerate(e["semaforos"])},
        "cap": {a: net.getEdge(a).getLaneNumber() * comun.plazas_carril(net, a) for a in aprox},
        "vmax": {a: net.getEdge(a).getSpeed() for a in aprox},
        "plazas": {l: comun.plazas_carril(net, l) for l in e["enlaces"]},
        "fase_av": {},          # se calcula con TraCI en el primer episodio
        "lados": lados, "n_id": n_id, "dim_obs": 12 + n_id + 8 * len(lados),
        "ins_flujo": origen_flujos(e["cfg"], e["semaforos"]),
        # --obs-insercion (configurar_obs_insercion): apagada por defecto
        "dim_base": 12 + n_id + 8 * len(lados), "obs_ins": False,
        "ins_salida": salidas_flujos(e["cfg"]), "pend_arista": {},
        # plan3, Etapas 3 y 4: apagadas (las ponen main y configurar_desde_meta)
        "obs_cerca": 0.0, "n_cerca": 0, "msg_paso": False, "sin_forzadas": False, "paso_decision": PASO_CONTROL,
        "vnorm": None, "_medidor": None,
    })
    return C


def dim_total():
    """Tamano de la observacion: base, + 4 con --obs-insercion, + 16 + lados con --obs-cercana (en ese orden)."""
    return C["dim_base"] + (4 if C["obs_ins"] else 0) + (C["n_cerca"] if C["obs_cerca"] else 0)


def configurar_obs_insercion(activa):
    """--obs-insercion: agrega (o quita) las cuatro entradas de vehiculos que esperan para entrar al final
    de la observacion. Se llama despues de preparar(); evaluar.py la llama con el valor del meta."""
    C["obs_ins"] = bool(activa)
    C["dim_obs"] = dim_total()


def configurar_obs_cercana(largo):
    """--obs-cercana L (M3, B14): agrega (o quita, con 0) las 16 + lados entradas cercanas al final de la
    observacion, con la geometria del escenario y el archivo de los E2 (lo escribe si falta). Va despues de
    preparar()."""
    C["obs_cerca"] = float(largo or 0)
    C["n_cerca"] = 16 + len(C["lados"]) if largo else 0
    C["dim_obs"] = dim_total()
    if largo:
        C.update(geometria_cercana(C["escenario"]))
        C["e2_archivo"] = archivo_e2(C["escenario"], largo)


_GEOMETRIA = {}         # escenario -> geometria de la zona cercana (la red se lee una vez por proceso)


def geometria_cercana(escenario):
    """Carriles de cada acceso, su largo y el primer carril interno del giro a la izquierda de cada carril (donde el
    que gira espera el hueco, como en plan2/diag_corredor/bloqueo.py)."""
    if escenario not in _GEOMETRIA:
        e = ESCENARIOS[escenario]
        net = sumolib.net.readNet(comun.leer_cfg(e["cfg"])[0], withInternal=True)
        aprox = [a for lista in e["semaforos"].values() for a in lista]
        carriles = {a: [l.getID() for l in net.getEdge(a).getLanes()] for a in aprox}
        via_izq = {}
        for a in aprox:
            for conns in net.getEdge(a).getOutgoing().values():
                for c in conns:
                    if c.getDirection() in ("l", "L") and c.getViaLaneID():
                        via_izq[c.getFromLane().getID()] = c.getViaLaneID()
        _GEOMETRIA[escenario] = {
            "carriles_aprox": carriles, "via_izq": via_izq,
            "largo_carril": {l: net.getLane(l).getLength() for ls in carriles.values() for l in ls}}
    return _GEOMETRIA[escenario]


def archivo_e2(escenario, largo, carpeta="."):
    """--obs-cercana: escribe (si falta o es otro) <carpeta>/e2_<esc>_<L>.add.xml, un detector E2 de L m que termina
    en la linea de parada en cada carril de acceso, y devuelve su ruta. Escritura atomica (temporal con el pid y
    reemplazo con reintentos): la llaman a la vez el trabajo "preparar" (plan3/p3_preparar.py), los entrenamientos y
    las evaluaciones."""
    geo = geometria_cercana(escenario)
    lineas = ["<additional>"]
    for ls in geo["carriles_aprox"].values():
        for l in ls:
            lg = geo["largo_carril"][l]
            lineas.append(f'    <laneAreaDetector id="e2_{l}" lane="{l}" pos="{max(0.0, lg - largo):.2f}" '
                          f'endPos="{lg:.2f}" period="100000" file="{os.devnull}" friendlyPos="true"/>')
    texto = "\n".join(lineas + ["</additional>"]) + "\n"
    ruta = os.path.join(carpeta, f"e2_{escenario}_{float(largo):g}.add.xml")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            if f.read() == texto:
                return ruta
    tmp = f"{ruta}.{os.getpid()}.tmp"          # con el pid: varios procesos pueden escribirlo a la vez
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(texto)
    reintentar(bajar_a_disco, tmp)
    reemplazar(tmp, ruta)
    return ruta


def configurar_desde_meta(meta):
    """La observacion, el reloj y los mensajes con que se entreno una politica, leidos de las opciones de su meta
    (evaluar.brazo_profundo y el modo demo). Con {} deja todo como siempre."""
    op = (meta or {}).get("opciones", {})
    configurar_obs_insercion(op.get("obs_insercion", False))
    configurar_obs_cercana(op.get("obs_cercana", 0.0))
    C["msg_paso"] = bool(op.get("msg_cada_paso", False))
    C["paso_decision"] = int(op.get("paso_decision", PASO_CONTROL))


def opciones_que_actuan(meta):
    """Las opciones del meta que cambian como juega la politica (OPCIONES_QUE_ACTUAN) y no tienen su valor de
    siempre, {nombre: valor}. Un programa que juega politicas sin configurar_desde_meta debe negarse si hay alguna."""
    op = (meta or {}).get("opciones", {})
    return {c: op[c] for c, defecto in OPCIONES_QUE_ACTUAN.items() if c in op and op[c] != defecto}


def configurar_colas_cero(activo):
    """a3 (evaluar3.py --colas-cero): al jugar, todas las entradas de colas (vehiculos detenidos) de la observacion
    valen cero: cola_o..cola_s, las que mandan los vecinos (<lado>_cola_alimentadora y <lado>_cola_mi_salida) y, con
    --obs-cercana, cerca_det_* y salida_ocup_*. Va fuera de C para que preparar() no la apague."""
    global COLAS_CERO
    COLAS_CERO = bool(activo)


def es_cola(nombre):
    return (nombre.startswith(("cola_", "cerca_det_", "salida_ocup_"))
            or nombre.endswith(("_cola_alimentadora", "_cola_mi_salida")))


def indices_colas():
    """Posiciones de las colas en la observacion de este escenario y estas opciones (para configurar_colas_cero)."""
    if C.get("_colas_dim") != C["dim_obs"]:
        C["_idx_colas"] = np.array([k for k, n in enumerate(nombres_features()) if es_cola(n)], dtype=np.int64)
        C["_colas_dim"] = C["dim_obs"]
    return C["_idx_colas"]


class NormValor:
    """--norm-valor: media y segundo momento moviles de los retornos (ValueNorm de MAPPO, Yu et al. 2022), un paso
    por actualizacion con beta y correccion de sesgo. El critico predice (V - media) / desv; los valores que entran
    a gae() se desnormalizan (a_valor) y el objetivo del critico se normaliza con las medias ya actualizadas."""

    def __init__(self, beta=BETA_NORM):
        self.beta, self.m1, self.m2, self.peso = float(beta), 0.0, 0.0, 0.0

    def actualizar(self, x):
        x = np.asarray(x, dtype=np.float64)
        assert x.size > 0, "NormValor.actualizar con un lote vacio (el episodio sin transiciones no actualiza)"
        self.m1 = self.beta * self.m1 + (1 - self.beta) * float(x.mean())
        self.m2 = self.beta * self.m2 + (1 - self.beta) * float((x ** 2).mean())
        self.peso = self.beta * self.peso + (1 - self.beta)

    def media_desv(self):
        if self.peso == 0:
            return 0.0, 1.0
        m = self.m1 / self.peso
        return m, max(1e-2, self.m2 / self.peso - m * m) ** 0.5

    def a_valor(self, v):
        m, d = self.media_desv()
        return v * d + m

    def normalizar(self, r):
        m, d = self.media_desv()
        return (r - m) / d

    def estado(self):
        return [self.beta, self.m1, self.m2, self.peso]

    def restaurar(self, e):
        self.beta, self.m1, self.m2, self.peso = (float(x) for x in e)


def salidas_flujos(cfg):
    """--obs-insercion: {id de flujo (o vehiculo): arista de salida (from, o la primera de su ruta)}, leido
    del .rou.xml del escenario, igual que en origen_flujos."""
    import xml.etree.ElementTree as ET
    rutas = ET.parse(cfg).getroot().find("input/route-files")
    res = {}
    if rutas is None:
        return res
    carpeta = os.path.dirname(cfg)
    for archivo in rutas.get("value").split(","):
        raiz = ET.parse(os.path.join(carpeta, archivo.strip())).getroot()
        for el in raiz:
            if el.tag not in ("flow", "trip", "vehicle"):
                continue
            arista = el.get("from")
            ruta = el.find("route")
            if arista is None and ruta is not None:
                arista = ruta.get("edges").split()[0]
            res[el.get("id")] = arista
    return res


def origen_flujos(cfg, semaforos):
    """--recompensa-insercion: {id de flujo (o vehiculo): semaforo cuyo acceso alimenta}, leido del
    .rou.xml del escenario. La arista de salida de cada flujo (from, o la primera de su ruta) es un
    acceso de un semaforo en los escenarios con semaforos en el borde (corredor, red, malla3); si no lo
    es, el flujo queda en None y sus pendientes solo cuentan en ins_total."""
    import xml.etree.ElementTree as ET
    de_arista = {a: tls for tls, lista in semaforos.items() for a in lista}
    rutas = ET.parse(cfg).getroot().find("input/route-files")
    res = {}
    if rutas is None:
        return res
    carpeta = os.path.dirname(cfg)
    for archivo in rutas.get("value").split(","):
        raiz = ET.parse(os.path.join(carpeta, archivo.strip())).getroot()
        for el in raiz:
            if el.tag not in ("flow", "trip", "vehicle"):
                continue
            arista = el.get("from")
            ruta = el.find("route")
            if arista is None and ruta is not None:
                arista = ruta.get("edges").split()[0]
            res[el.get("id")] = de_arista.get(arista)
    return res


def pendientes_por_agente():
    """Vehiculos que esperan para entrar a la red en este segundo: ({semaforo: n}, total). El id de un
    vehiculo de un flujo es <flujo>.<k>; se asigna al semaforo de la arista de salida del flujo.
    Con --obs-insercion deja ademas en C["pend_arista"] la cuenta por arista de salida (la lee observar)."""
    por_agente, total = {}, 0
    por_arista = {}
    for vid in traci.simulation.getPendingVehicles():
        total += 1
        tls = C["ins_flujo"].get(vid, C["ins_flujo"].get(vid.rsplit(".", 1)[0]))
        if tls is not None:
            por_agente[tls] = por_agente.get(tls, 0) + 1
        if C["obs_ins"]:
            a = C["ins_salida"].get(vid, C["ins_salida"].get(vid.rsplit(".", 1)[0]))
            por_arista[a] = por_arista.get(a, 0) + 1
    if C["obs_ins"]:
        C["pend_arista"] = por_arista
    return por_agente, total


def nombres_features():
    """Nombre de cada posicion de la observacion (va al meta de la politica)."""
    ids = [f"id_{t.replace('semaforo_', '')}" for t in C["semaforos"]]
    ids += [f"id_libre{k}" for k in range(len(ids), C["n_id"])]
    return (["cola_o", "cola_e", "cola_n", "cola_s", "movil_o", "movil_e", "movil_n", "movil_s",
             "fase_0", "fase_1", "t_verde", "puede_cambiar"] + ids
            + [f"{lado}_{f}" for lado in C["lados"]
               for f in ("presente", "verde_hacia_mi", "ambar", "t_fase", "outflow",
                         "cola_alimentadora", "cola_mi_salida", "edad")]
            + (["pend_o", "pend_e", "pend_n", "pend_s"] if C["obs_ins"] else [])
            + ([f"{f}_{x}" for x in "oens" for f in ("cerca_det", "cerca_mov", "espera_cab", "giro_izq")]
               + [f"salida_ocup_{lado}" for lado in C["lados"]] if C["obs_cerca"] else []))


def fase_avenida(tls, aprox, verdes):
    """Indice (dentro de verdes) de la fase verde que sirve a la avenida (eje EO): la que pone
    en verde los links cuyo carril de entrada pertenece a las aproximaciones 0 o 1."""
    activo = traci.trafficlight.getProgram(tls)
    logicas = traci.trafficlight.getAllProgramLogics(tls)
    logica = next((l for l in logicas if l.programID == activo), logicas[0])
    links = traci.trafficlight.getControlledLinks(tls)
    de_avenida = [bool(l) and l[0][0].rsplit("_", 1)[0] in aprox[:2] for l in links]
    candidatas = []
    for k, f in enumerate(verdes):
        estado = logica.phases[f].state
        if any(c in "Gg" and av for c, av in zip(estado, de_avenida)):
            candidatas.append(k)
    assert len(candidatas) == 1, f"{tls}: fases de avenida {candidatas}"
    return candidatas[0]


# ---------------- Lecturas por suscripcion ----------------
HALT, VEH, ESP = tc.LAST_STEP_VEHICLE_HALTING_NUMBER, tc.LAST_STEP_VEHICLE_NUMBER, tc.VAR_WAITING_TIME
VEL = tc.LAST_STEP_MEAN_SPEED


def suscribir():
    for lista in C["semaforos"].values():
        for a in lista:
            traci.edge.subscribe(a, [HALT, VEH, ESP, VEL])
    for tls in C["semaforos"]:
        traci.trafficlight.subscribe(tls, [tc.TL_CURRENT_PHASE])


def lecturas():
    return traci.edge.getAllSubscriptionResults()


def leer(lect, edge, var):
    return lect.get(edge, {}).get(var, 0)


def fases_actuales():
    res = traci.trafficlight.getAllSubscriptionResults()
    return {tls: res.get(tls, {}).get(tc.TL_CURRENT_PHASE, -1) for tls in C["semaforos"]}


# ---------------- Politica ----------------
def capa(entrada, salida, ganancia):
    lin = nn.Linear(entrada, salida)
    nn.init.orthogonal_(lin.weight, ganancia)
    nn.init.zeros_(lin.bias)
    return lin


class Politica(nn.Module):
    """Actor y critico separados, MLP de dos capas ocultas con tanh."""

    def __init__(self, dim_obs=DIM_OBS, ocultas=OCULTAS):
        super().__init__()
        self.actor = nn.Sequential(capa(dim_obs, ocultas, 2 ** 0.5), nn.Tanh(),
                                   capa(ocultas, ocultas, 2 ** 0.5), nn.Tanh(),
                                   capa(ocultas, 2, 0.01))
        self.critico = nn.Sequential(capa(dim_obs, ocultas, 2 ** 0.5), nn.Tanh(),
                                     capa(ocultas, ocultas, 2 ** 0.5), nn.Tanh(),
                                     capa(ocultas, 1, 1.0))

    def forward(self, obs):
        return self.actor(obs), self.critico(obs).squeeze(-1)

    @staticmethod
    def enmascarar(logits, mascara):
        return logits.masked_fill(mascara == 0, -1e8)

    def guardar(self, ruta, meta):
        """Primero el .json y al final el .pt, cada uno en un temporal bajado a disco y renombrado: si el .pt esta,
        esta entero y su .json tambien. Los bytes son los de un torch.save directo (ruta_tmp)."""
        guardar_json(meta, ruta.replace(".pt", ".json"))
        guardar_pt(self.state_dict(), ruta)

    @staticmethod
    def cargar(ruta):
        with open(ruta.replace(".pt", ".json"), encoding="utf-8") as f:
            meta = json.load(f)
        politica = Politica(meta["dim_obs"], meta["ocultas"])
        politica.load_state_dict(torch.load(ruta, weights_only=True))
        politica.eval()
        return politica, meta


# ---------------- Mensajeria ----------------
class Canal:
    """Buzon entre semaforos vecinos. Cada mensaje se entrega t_emision + latencia segundos
    despues y se pierde con probabilidad perdida (RNG propio: no toca ninguna otra
    secuencia aleatoria). El receptor lee el mas reciente ya entregado; si no hay ninguno
    nuevo conserva el ultimo y la edad crece."""

    def __init__(self, latencia=0, perdida=0.0, semilla=0):
        self.latencia, self.perdida = int(latencia), float(perdida)
        self.rng = random.Random(semilla + 7919)
        self.buzon = {}
        self.ultimo = {}

    def publicar(self, emisor, receptor, t, msg):
        if self.perdida > 0 and self.rng.random() < self.perdida:
            return
        self.buzon.setdefault((emisor, receptor), []).append((t + self.latencia, t, msg))

    def leer(self, emisor, receptor, t):
        clave = (emisor, receptor)
        cola = self.buzon.get(clave, [])
        entregados = [x for x in cola if x[0] <= t]
        if entregados:
            self.ultimo[clave] = (entregados[-1][1], entregados[-1][2])
            self.buzon[clave] = [x for x in cola if x[0] > t]
        if clave in self.ultimo:
            t_em, msg = self.ultimo[clave]
            return msg, t - t_em
        return None, EDAD_MAX


def alimentadora(j, lado_de_i):
    """Aproximacion del vecino j que descarga sobre el enlace hacia i (i esta al lado_de_i de
    j): la del lado opuesto. Si i esta al este de j, la aproximacion oeste de j; si esta al
    norte, la aproximacion sur."""
    return C["semaforos"][j][IDX_LADO[OPUESTO[lado_de_i]]]


def mensaje(j, ag_j, lect, medidor, lado_de_i, enlace_i_a_j, t):
    """Lo que j le envia a su vecino i (i esta al lado_de_i de j). fase = eje del verde de j
    (EO si es su fase de avenida, NS si no) o ambar; outflow solo si ese verde va hacia i."""
    if ag_j["ambar_restante"] > 0:
        fase = "ambar"
    elif ag_j["verde"] == C["fase_av"][j]:
        fase = "EO"
    else:
        fase = "NS"
    alim = alimentadora(j, lado_de_i)
    total = leer(lect, alim, VEH)
    return {"fase": fase, "t_fase": 0 if fase == "ambar" else ag_j["t_verde"],
            "outflow": total if fase == EJE[lado_de_i] else 0,
            "cola_alimentadora": leer(lect, alim, HALT),
            "cola_salida": medidor.max_halting(enlace_i_a_j), "t": t}


# ---------------- Observacion, mascara y recompensa ----------------
def minimo_verde(ag):
    return ag["verde_min"][ag["verdes"][ag["verde"]]]


def observar(tls, ag, lect, canal, t, con_vecinos):
    """Bloque local (0..11), id del semaforo (12..12+n_id-1) y una ranura de 8 por lado."""
    obs = np.zeros(C["dim_obs"], dtype=np.float32)
    aprox = C["semaforos"][tls]
    for k, a in enumerate(aprox):
        h, v = leer(lect, a, HALT), leer(lect, a, VEH)
        obs[k] = min(1.0, h / C["cap"][a])
        obs[4 + k] = min(1.0, max(0, v - h) / C["cap"][a])
    obs[8 + ag["verde"]] = 1.0
    obs[10] = min(1.0, ag["t_verde"] / VERDE_MAX)
    obs[11] = 1.0 if ag["t_verde"] >= minimo_verde(ag) else 0.0
    obs[12 + C["indice"][tls]] = 1.0
    if C["obs_ins"]:
        # --obs-insercion: vehiculos que esperan para entrar por cada acceso, n / (n + plazas)
        for k, a in enumerate(aprox):
            n = C["pend_arista"].get(a, 0)
            obs[C["dim_base"] + k] = n / (n + C["cap"][a])
    if C["obs_cerca"]:
        obs[C["dim_obs"] - C["n_cerca"]:] = entradas_cercanas(tls)
    if con_vecinos:
        for r, lado in enumerate(C["lados"]):
            vec = C["vecinos"][tls].get(lado)
            if vec is None:
                continue
            j, enlace_j_a_i, enlace_i_a_j = vec
            base = 12 + C["n_id"] + 8 * r
            obs[base] = 1.0
            msg, edad = canal.leer(j, tls, t)
            if msg is None:
                obs[base + 7] = 1.0
                continue
            lado_de_i = OPUESTO[lado]                           # i visto desde j
            cap_alim = C["cap"][alimentadora(j, lado_de_i)]
            obs[base + 1] = 1.0 if msg["fase"] == EJE[lado] else 0.0     # verde de j hacia mi
            obs[base + 2] = 1.0 if msg["fase"] == "ambar" else 0.0
            obs[base + 3] = min(1.0, msg["t_fase"] / VERDE_MAX)
            obs[base + 4] = min(1.0, msg["outflow"] / cap_alim)
            obs[base + 5] = min(1.0, msg["cola_alimentadora"] / cap_alim)
            obs[base + 6] = min(1.0, msg["cola_salida"] / C["plazas"][enlace_i_a_j])
            obs[base + 7] = min(1.0, edad / EDAD_MAX)
    if COLAS_CERO:
        obs[indices_colas()] = 0.0
    return obs


def entradas_cercanas(tls):
    """--obs-cercana (M3), leidas al decidir. Por acceso: vehiculos a menos de L m de la linea, detenidos y en
    movimiento (del E2 suscrito; / (carriles * L / 7.5), tope 1), espera del primero de cada carril con alguien a
    menos de L m (la mayor; / 120 s, tope 1; con la zona vacia vale 0 y no se lee) y giro_izq = 1 si hay un detenido
    en el primer tramo interno del giro a la izquierda de algun carril. Por lado con vecino: detenidos del carril
    mas cargado del enlace de SALIDA i->j / plazas (MedidorEnlaces)."""
    res = np.zeros(C["n_cerca"], dtype=np.float32)
    e2 = traci.lanearea.getAllSubscriptionResults()
    vias = traci.lane.getAllSubscriptionResults()
    largo = C["obs_cerca"]
    for k, a in enumerate(C["semaforos"][tls]):
        det = mov = 0
        espera, giro = 0.0, 0.0
        for l in C["carriles_aprox"][a]:
            r = e2.get(f"e2_{l}", {})
            n, h = r.get(VEH, 0), r.get(HALT, 0)
            det += h
            mov += max(0, n - h)
            if n:                # zona vacia: el primero esta lejos y no espera (ahorra las 2 llamadas del carril)
                ids = traci.lane.getLastStepVehicleIDs(l)
                if ids:                              # el ultimo de la lista es el mas cercano a la linea
                    espera = max(espera, traci.vehicle.getWaitingTime(ids[-1]))
            via = C["via_izq"].get(l)
            if via is not None and vias.get(via, {}).get(HALT, 0) > 0:
                giro = 1.0
        plazas = len(C["carriles_aprox"][a]) * max(1.0, largo / (comun.LARGO_VEH + comun.MIN_GAP))
        res[4 * k: 4 * k + 4] = [min(1.0, det / plazas), min(1.0, mov / plazas),
                                 min(1.0, espera / CERCA_MAX_ESPERA), giro]
    medidor = C["_medidor"]
    for r, lado in enumerate(C["lados"]):
        vec = C["vecinos"][tls].get(lado)
        if vec is not None:
            res[16 + r] = min(1.0, medidor.max_halting(vec[2]) / C["plazas"][vec[2]])
    return res


def mascara(ag):
    """[puede mantener, puede cambiar]: verde minimo y maximo, igual que en U2."""
    if ag["t_verde"] < minimo_verde(ag):
        return [1.0, 0.0]
    if ag["t_verde"] >= VERDE_MAX:
        return [0.0, 1.0]
    return [1.0, 1.0]


def recompensa_base(tls, lect):
    """Formula de U2 (colas detenidas y esperas): se reporta a reloj fijo de 5 s en todos los brazos."""
    aprox = C["semaforos"][tls]
    return -(W1 * sum(leer(lect, a, HALT) for a in aprox) + W2 * sum(leer(lect, a, ESP) for a in aprox))


def retraso_base(tls, lect):
    """Vehiculos-equivalentes retrasados en las aproximaciones: n_a * (1 - v_media_a / v_max_a).
    Es la version por segundo del timeLoss de SUMO (metrica primaria): un vehiculo detenido
    cuenta 1 y uno que avanza a media velocidad cuenta 0.5. El conteo de detenidos de U2 no ve
    a los que avanzan a paso lento, y por eso cambiar de fase muy seguido (colas que reptan en
    vez de pararse) le parecia bueno al optimizador (prueba de humo en cruce)."""
    total = 0.0
    for a in C["semaforos"][tls]:
        n = leer(lect, a, VEH)
        if n:
            total += n * (1.0 - min(1.0, max(0.0, leer(lect, a, VEL)) / C["vmax"][a]))
    return total


def recompensa_paso(tls, lect):
    """Lo que acumula el agente de U4 cada segundo: retraso en vez de cola detenida, misma espera."""
    return -(W1 * retraso_base(tls, lect) + W2 * sum(leer(lect, a, ESP) for a in C["semaforos"][tls]))


def termino_spill(tls, medidor):
    """Vehiculos detenidos por encima de la mitad de las plazas en el carril mas cargado de
    cada enlace que sale de tls hacia un vecino (lectura directa, no del mensaje)."""
    total = 0.0
    for lado in C["lados"]:
        vec = C["vecinos"][tls].get(lado)
        if vec is None:
            continue
        enlace = vec[2]
        total += max(0, medidor.max_halting(enlace) - C["plazas"][enlace] // 2)
    return total


def exceso_enlaces(medidor):
    """Suma sobre todos los enlaces de max(0, max_halting - plazas // 2) (para ret_spill)."""
    return sum(max(0, medidor.max_halting(e) - C["plazas"][e] // 2) for e in C["enlaces"])


# ---------------- Episodio ----------------
def toca_decidir(ag, pasos):
    """Reloj de decision de un agente (fuera del ambar). Por defecto, cada PASO_CONTROL s de su verde (la primera a
    los 5 s) y todos en el segundo 0, como siempre. Con --paso-decision K: cada K s antes del verde minimo (son
    decisiones forzadas), cada K s desde el verde minimo y una al llegar al verde maximo."""
    if ag["ambar_restante"] > 0:
        return False
    t = ag["t_verde"]
    if t == 0:
        return pasos == 0
    k = C["paso_decision"]
    if k == PASO_CONTROL:
        return t % PASO_CONTROL == 0
    m = minimo_verde(ag)
    return t % k == 0 if t < m else ((t - m) % k == 0 or t == VERDE_MAX)


def correr_episodio(modo, politica, gui, delay, seed, tripinfo=None, serie=None,
                    latencia=0, perdida=0.0, variante="vecinos", buffer=None,
                    decidir=None, transicion=None, con_estado=False, v2=False, ins=False, escala=None):
    """Una hora simulada con los agentes IPPO. modo train (muestrea acciones y llena buffer)
    o demo (argmax). Devuelve las mismas metricas que rl_corredor.correr_episodio mas las
    de U4 y los retornos ret_*. El reloj de decision es el de rl_corredor.py. decidir,
    transicion y con_estado son la interfaz para decisores externos (docstring del modulo).
    v2: exploracion comun en train (--v2 o --solo-exploracion); ins: suma a la recompensa los
    vehiculos que esperan para entrar (--recompensa-insercion). Apagados, nada cambia.
    Con buffer (entrenamiento IPPO) devuelve ademas frac_forzadas y msg_edad (--registro-extendido);
    contarlas no cambia ningun numero. escala: --scale de sumo (--escala-demanda, --val-escalas).
    Las opciones de las Etapas 3 y 4 que cambian el episodio se leen de C (obs_cerca, msg_paso,
    sin_forzadas, paso_decision, vnorm)."""
    assert decidir is None or buffer is None, "buffer es solo para la politica IPPO"
    assert not (C["sin_forzadas"] and (decidir is not None or transicion is not None)), \
        "--sin-forzadas es solo para la politica IPPO"
    esc = C["escenario"]
    con_vecinos = variante != "local"
    binario = sumolib.checkBinary("sumo-gui" if gui else "sumo")
    if tripinfo is None:
        tripinfo = f"tripinfo_{esc}_ippo_{modo}.xml"
    cmd = [binario, "-c", C["cfg"], "--seed", str(seed),
           "--tripinfo-output", tripinfo, "--tripinfo-output.write-unfinished", "true",
           "--device.emissions.probability", "1"] + comun.args_estadisticas(tripinfo)
    if gui:
        cmd += ["--start", "--quit-on-end", "--delay", str(delay)]
        if os.path.exists(f"vista_{esc}.xml"):
            cmd += ["--gui-settings-file", f"vista_{esc}.xml"]
    if C["obs_cerca"]:
        # --additional-files reemplaza la lista del .sumocfg: van sus adicionales (el programa) y los E2 juntos
        carpeta_cfg = os.path.dirname(C["cfg"])
        cmd += ["--additional-files", ",".join([os.path.join(carpeta_cfg, a) for a in comun.leer_cfg(C["cfg"])[1]]
                                               + [C["e2_archivo"]])]
    if escala is not None:
        cmd += ["--scale", f"{escala:.4f}"]
    comun.iniciar_sumo(cmd)
    suscribir()
    medidor = comun.MedidorEnlaces(C["net"], C["enlaces"])
    C["_medidor"] = medidor                # entradas_cercanas lee de aqui la salida real de cada enlace
    if C["obs_cerca"]:
        for ls in C["carriles_aprox"].values():
            for l in ls:
                traci.lanearea.subscribe(f"e2_{l}", [VEH, HALT])
        for via in sorted(set(C["via_izq"].values())):
            traci.lane.subscribe(via, [HALT])
    canal = Canal(latencia, perdida, seed)
    crn = v2 and modo == "train" and decidir is None
    rng_expl = np.random.default_rng(seed + SEMILLA_EXPL) if crn else None
    minoritarias = 0               # decisiones libres de train con a != argmax
    ins_espera, ins_total = 0, 0   # vehiculo-segundos esperando para entrar (asignados, todos)
    C["pend_arista"] = {}          # --obs-insercion: nada del episodio anterior en la primera decision

    rc.SEMAFOROS = C["semaforos"]          # fases_verdes usa el programa activo del semaforo
    agentes = {}
    for tls, aprox in C["semaforos"].items():
        verdes, ambar, dur_ambar, verde_min = rc.fases_verdes(tls)
        assert len(verdes) == 2, f"{tls}: {len(verdes)} fases verdes; la observacion asume 2"
        if tls not in C["fase_av"]:
            C["fase_av"][tls] = fase_avenida(tls, aprox, verdes)
        agentes[tls] = {"verdes": verdes, "ambar": ambar, "dur_ambar": dur_ambar,
                        "verde_min": verde_min, "verde": 0, "t_verde": 0, "ambar_restante": 0,
                        "pendiente": None, "cambio": 0.0, "fase_previa": None,
                        "r_acum": 0.0, "s_acum": 0.0, "ultima": None}
        traci.trafficlight.setPhase(tls, verdes[0])
        traci.trafficlight.setPhaseDuration(tls, 100000)
    fases = fases_actuales()
    for tls in agentes:
        agentes[tls]["fase_previa"] = fases[tls]
    orden = list(C["semaforos"])
    if buffer is not None:
        for tls in orden:
            buffer[tls] = {"obs": [], "mascara": [], "accion": [], "logp": [], "valor": [],
                           "recompensa": [], "v_final": 0.0, "t": [], "t_final": 0}

    pasos = 0
    cola_acum = 0.0
    cola_max = 0
    r_reporte, n_reporte = 0.0, 0      # recompensa base a reloj fijo de 5 s (comparable con U2)
    r_agente, n_agente = 0.0, 0        # lo que ven los agentes (con terminos), sin escalar
    ret_retraso, ret_colas, exceso = 0.0, 0.0, 0.0     # retornos por segundo (ESPEC seccion 5)
    decisiones_libres = 0
    tomadas, edades = 0, []            # con buffer: decisiones y edad del mensaje al decidir (registro extendido)
    spill_activaciones, spill_suma = 0, 0.0
    cambios = 0
    filas_serie, filas_fases = [], []
    lect = {}
    aprox_todas = [a for lista in C["semaforos"].values() for a in lista]

    def recompensa_agente(tls, ag):
        # Suma por segundo de recompensa_paso sobre el intervalo de decision, dividida entre
        # 5 s: en un intervalo de mantener es el nivel medio y en uno de cambiar (8 s) pesa
        # 8/5 (retraso-segundos, el objetivo real). El nivel en el instante siguiente, como en
        # U2, subestimaba la cola al inicio de un verde y tambien sesgaba hacia cambiar.
        r = ag["r_acum"] / PASO_CONTROL
        if variante == "spill":
            s = ag["s_acum"] / PASO_CONTROL
            r -= W3 * s
            nonlocal spill_activaciones, spill_suma
            if s > 0:
                spill_activaciones += 1
                spill_suma += s
        if variante == "cambio":
            r -= W4 * ag["cambio"]
        ag["r_acum"], ag["s_acum"] = 0.0, 0.0
        return r

    def cerrar_pendiente(tls, ag):
        """Cierra la decision pendiente del agente; devuelve su recompensa sin escalar o None."""
        nonlocal r_agente, n_agente
        if ag["pendiente"] is None:
            return None
        r = recompensa_agente(tls, ag)
        r_agente += r
        n_agente += 1
        ag["cambio"] = 0.0
        if buffer is not None:
            buffer[tls]["recompensa"].append(r * ESCALA_R)
        ag["pendiente"] = None
        return r

    def estado_global(ya_vistas):
        """Concatenacion de observar() de todos los semaforos (orden de C["indice"])."""
        return np.concatenate([ya_vistas[t] if t in ya_vistas
                               else observar(t, agentes[t], lect, canal, pasos, con_vecinos)
                               for t in orden])

    while traci.simulation.getMinExpectedNumber() > 0 and pasos < 6000:
        if pasos > 0 and pasos % PASO_CONTROL == 0:
            for tls in orden:
                r_reporte += recompensa_base(tls, lect)
                n_reporte += 1
        # mensajes: cada PASO_CONTROL s de reloj global (cada K s con --paso-decision K; cada segundo con
        # --msg-cada-paso, antes de las decisiones de ese segundo: el receptor lee el de este segundo)
        if con_vecinos and pasos > 0 and (C["msg_paso"] or pasos % C["paso_decision"] == 0):
            for j, ag_j in agentes.items():
                for lado, vec in C["vecinos"][j].items():
                    if vec is None:
                        continue
                    i, _, enlace_i_a_j = vec
                    msg = mensaje(j, ag_j, lect, medidor, lado, enlace_i_a_j, pasos)
                    canal.publicar(j, i, pasos, msg)

        deciden = [tls for tls in orden if toca_decidir(agentes[tls], pasos)]
        if deciden:
            # --sin-forzadas: una decision con una sola accion legal se aplica pero no cierra la pendiente ni entra
            # al lote (su recompensa se suma a la de la decision libre anterior)
            forzada = ({tls: sum(mascara(agentes[tls])) == 1 for tls in deciden} if C["sin_forzadas"] else {})
            r_cerradas = {tls: None if forzada.get(tls) else cerrar_pendiente(tls, agentes[tls]) for tls in deciden}
            obs = np.stack([observar(tls, agentes[tls], lect, canal, pasos, con_vecinos) for tls in deciden])
            masc = np.array([mascara(agentes[tls]) for tls in deciden], dtype=np.float32)
            if buffer is not None:
                tomadas += len(deciden)
                if con_vecinos:            # edad del mensaje que observar() acaba de leer de cada vecino
                    for tls in deciden:
                        for vec in C["vecinos"][tls].values():
                            if vec is not None and (vec[0], tls) in canal.ultimo:
                                edades.append(pasos - canal.ultimo[(vec[0], tls)][0])
            estado = estado_global({t: obs[k] for k, t in enumerate(deciden)}) if con_estado else None
            if transicion is not None:
                for k, tls in enumerate(deciden):
                    ult = agentes[tls]["ultima"]
                    if ult is not None and r_cerradas[tls] is not None:
                        transicion(tls, ult[0], ult[1], r_cerradas[tls] * ESCALA_R, obs[k], masc[k],
                                   {"extra": ult[2], "ultima": False, "vaciada": False, "t": pasos,
                                    "estado_sig": estado})
            if decidir is None:
                with torch.no_grad():
                    logits, valores = politica(torch.from_numpy(obs))
                    logits = Politica.enmascarar(logits, torch.from_numpy(masc))
                    if crn:
                        # Exploracion comun (V2): un solo u por segundo, el mismo para todos los que
                        # deciden; a = 1 si p_cambiar > u. La marginal de cada agente es su politica
                        # y las acciones conjuntas quedan correlacionadas.
                        dist = torch.distributions.Categorical(logits=logits)
                        u = float(rng_expl.random())
                        acciones = (dist.probs[:, 1] > u).long()
                        logp = dist.log_prob(acciones)
                        assert all(masc[k, int(acciones[k])] > 0 for k in range(len(deciden)))
                    elif modo == "train":
                        dist = torch.distributions.Categorical(logits=logits)
                        acciones = dist.sample()
                        logp = dist.log_prob(acciones)
                    else:
                        acciones = logits.argmax(dim=1)
                        logp = torch.zeros(len(deciden))
                extras = [None] * len(deciden)
            else:
                acciones, extras = decidir(deciden, obs, masc, modo,
                                           {"t": pasos, "seed": seed, "variante": variante, "estado": estado})
            for k, tls in enumerate(deciden):
                ag = agentes[tls]
                a = int(acciones[k])
                if masc[k].sum() > 1:
                    decisiones_libres += 1
                    if modo == "train" and decidir is None and a != int(logits[k].argmax()):
                        minoritarias += 1
                if buffer is not None and not forzada.get(tls):
                    b = buffer[tls]
                    b["obs"].append(obs[k])
                    b["mascara"].append(masc[k])
                    b["accion"].append(a)
                    b["logp"].append(float(logp[k]))
                    v = float(valores[k])
                    b["valor"].append(C["vnorm"].a_valor(v) if C["vnorm"] is not None else v)
                    b["t"].append(pasos)
                if transicion is not None:
                    ag["ultima"] = (obs[k], a, extras[k])
                if not forzada.get(tls):
                    ag["pendiente"] = True
                if a == 1:                                  # la mascara garantiza que es legal
                    f_actual = ag["verdes"][ag["verde"]]
                    traci.trafficlight.setPhase(tls, ag["ambar"][f_actual])
                    traci.trafficlight.setPhaseDuration(tls, ag["dur_ambar"][f_actual])
                    ag["ambar_restante"] = ag["dur_ambar"][f_actual]
                    ag["cambio"] = 1.0

        traci.simulationStep()
        pasos += 1
        lect = lecturas()
        colas = [leer(lect, a, HALT) for a in aprox_todas]
        cola_acum += sum(colas)
        cola_max = max(cola_max, sum(colas))
        medidor.paso(pasos)
        if ins or C["obs_ins"]:
            pend, n_pend = pendientes_por_agente()
            ins_total += n_pend
        for tls, ag in agentes.items():
            r_paso = recompensa_paso(tls, lect)
            ret_retraso += r_paso
            ret_colas += recompensa_base(tls, lect)
            if ins:
                # INS: cada vehiculo que espera para entrar por un acceso de tls pesa como uno detenido
                ins_espera += pend.get(tls, 0)
                r_paso -= W1 * pend.get(tls, 0)
            if ag["pendiente"] is not None:
                ag["r_acum"] += r_paso
                if variante == "spill":
                    ag["s_acum"] += termino_spill(tls, medidor)
        exceso += exceso_enlaces(medidor)
        if serie is not None and pasos % rc.PASO_SERIE == 0:
            filas_serie.append([pasos] + colas)
        fases = fases_actuales()
        if serie is not None and pasos <= comun.FIN_HORA:
            filas_fases.append([pasos] + [fases[t] for t in orden])
        for tls, ag in agentes.items():
            if fases[tls] != ag["fase_previa"] and fases[tls] in ag["verdes"]:
                cambios += 1
            ag["fase_previa"] = fases[tls]
            if ag["ambar_restante"] > 0:
                ag["ambar_restante"] -= 1
                if ag["ambar_restante"] == 0:
                    ag["verde"] = (ag["verde"] + 1) % len(ag["verdes"])
                    traci.trafficlight.setPhase(tls, ag["verdes"][ag["verde"]])
                    traci.trafficlight.setPhaseDuration(tls, 100000)
                    ag["t_verde"] = 0
            else:
                ag["t_verde"] += 1

    vaciada = traci.simulation.getMinExpectedNumber() == 0
    estado_fin = estado_global({}) if (transicion is not None and con_estado) else None
    # transiciones pendientes: recompensa con el estado de cierre y valor final segun vaciado
    for tls in orden:
        ag = agentes[tls]
        r = cerrar_pendiente(tls, ag)
        if buffer is not None:
            buffer[tls]["t_final"] = pasos
            if vaciada:
                buffer[tls]["v_final"] = 0.0
            else:
                with torch.no_grad():
                    o = torch.from_numpy(observar(tls, ag, lect, canal, pasos, con_vecinos)).unsqueeze(0)
                    v = float(politica(o)[1][0])
                    buffer[tls]["v_final"] = C["vnorm"].a_valor(v) if C["vnorm"] is not None else v
        if transicion is not None and ag["ultima"] is not None and r is not None:
            ult = ag["ultima"]
            transicion(tls, ult[0], ult[1], r * ESCALA_R,
                       observar(tls, ag, lect, canal, pasos, con_vecinos),
                       np.array(mascara(ag), dtype=np.float32),
                       {"extra": ult[2], "ultima": True, "vaciada": vaciada, "t": pasos,
                        "estado_sig": estado_fin})
    traci.close()
    C["_medidor"] = None

    if serie is not None:
        comun.guardar_serie(serie, ["t"] + aprox_todas, filas_serie)
        comun.guardar_fases(serie.replace("serie_", "fases_", 1), orden, filas_fases)
    res = comun.leer_tripinfo(tripinfo, C["flujos"])
    res.update({
        "cola_prom": round(cola_acum / max(1, pasos), 2),
        "cola_max": cola_max,
        "recompensa": round(r_reporte, 1),
        "recompensa_decision": round(r_reporte / max(1, n_reporte), 3),
        "recompensa_total_decision": round(r_agente / max(1, n_agente), 3),
        "decisiones": n_agente,
        "decisiones_libres": decisiones_libres,
        "cambios_fase": cambios,
        "spill_activaciones": spill_activaciones,
        "spill_suma": round(spill_suma, 1),
        "ret_retraso": round(ret_retraso, 2),
        "ret_colas": round(ret_colas, 2),
        "ret_spill": round(ret_retraso - W3 * exceso, 2),
        "expl_minoritaria": round(minoritarias / max(1, decisiones_libres), 4),
    })
    if ins:
        res.update({"ins_espera": ins_espera, "ins_total": ins_total})
    if buffer is not None:
        # decisiones con una sola accion legal (verde minimo o maximo) y edad media del mensaje al decidir (s)
        res.update({"frac_forzadas": round((tomadas - decisiones_libres) / max(1, tomadas), 4),
                    "msg_edad": round(float(np.mean(edades)), 3) if edades else ""})
    res.update(medidor.resumen())
    return res


# ---------------- PPO ----------------
def intervalos(b):
    """dt de cada decision del buffer de un agente: t de la siguiente decision (o t_final) - t."""
    n = len(b["recompensa"])
    t_sig = b["t"][1:n] + [b["t_final"]]
    dt = np.array(t_sig, dtype=np.float64) - np.array(b["t"][:n], dtype=np.float64)
    assert len(dt) == n and (dt > 0).all(), dt
    return dt


def gae(buffer, gamma, lam, smdp=False):
    """Ventajas y retornos por agente; devuelve el lote concatenado. smdp=True (--v2): descuento
    por segundo, gamma^(dt/5) y (gamma*lam)^(dt/5) con dt el intervalo real de cada decision
    (5 s mantener, 8 s cambiar, t_final - t en la ultima, tambien para v_final)."""
    obs, masc, acc, logp, adv, ret = [], [], [], [], [], []
    for tls, b in buffer.items():
        n = len(b["recompensa"])
        if n == 0:
            continue
        valores = b["valor"] + [b["v_final"]]
        ventaja = np.zeros(n, dtype=np.float32)
        ultimo = 0.0
        if smdp:
            expo = intervalos(b) / PASO_CONTROL
            for t in reversed(range(n)):
                delta = b["recompensa"][t] + gamma ** expo[t] * valores[t + 1] - valores[t]
                ultimo = delta + (gamma * lam) ** expo[t] * ultimo
                ventaja[t] = ultimo
        else:
            for t in reversed(range(n)):
                delta = b["recompensa"][t] + gamma * valores[t + 1] - valores[t]
                ultimo = delta + gamma * lam * ultimo
                ventaja[t] = ultimo
        obs.extend(b["obs"][:n])
        masc.extend(b["mascara"][:n])
        acc.extend(b["accion"][:n])
        logp.extend(b["logp"][:n])
        adv.extend(ventaja)
        ret.extend(ventaja + np.array(b["valor"][:n], dtype=np.float32))
    adv = np.array(adv, dtype=np.float32)
    adv = (adv - adv.mean()) / (adv.std() + 1e-8)
    return (torch.from_numpy(np.stack(obs)), torch.from_numpy(np.stack(masc)),
            torch.tensor(acc), torch.tensor(logp, dtype=torch.float32),
            torch.from_numpy(adv), torch.tensor(ret, dtype=torch.float32))


def varianza_explicada(buffer, ret):
    """--registro-extendido: 1 - Var(retorno - V) / Var(retorno) en el lote, con V el valor que el critico dio al
    decidir (antes de actualizar, como stable-baselines3) y ret el retorno de gae(), en el mismo orden. 1: predice
    el retorno; 0: no mejor que su media."""
    v = np.concatenate([np.asarray(b["valor"][:len(b["recompensa"])], dtype=np.float64)
                        for b in buffer.values() if b["recompensa"]])
    r = ret.numpy().astype(np.float64)
    var = float(r.var())
    return round(1.0 - float((r - v).var()) / var, 4) if var > 0 else ""


def actualizar(politica, opt, lote, hiper, rng):
    obs, masc, acc, logp_viejo, adv, ret = lote
    n = len(obs)
    idx = np.arange(n)
    libres = masc.sum(dim=1) > 1
    diag = {"perdida_politica": [], "perdida_valor": [], "entropia_libre": [], "kl_aprox": [],
            "clipfrac": []}
    for _ in range(hiper["epocas"]):
        rng.shuffle(idx)
        for ini in range(0, n, hiper["minibatch"]):
            b = torch.from_numpy(idx[ini:ini + hiper["minibatch"]])
            logits, valor = politica(obs[b])
            dist = torch.distributions.Categorical(logits=Politica.enmascarar(logits, masc[b]))
            logp = dist.log_prob(acc[b])
            ratio = torch.exp(logp - logp_viejo[b])
            recortado = torch.clamp(ratio, 1 - hiper["clip"], 1 + hiper["clip"])
            perdida_pol = -torch.min(ratio * adv[b], recortado * adv[b]).mean()
            perdida_val = 0.5 * ((valor - ret[b]) ** 2).mean()
            ent_libre = dist.entropy()[libres[b]]
            entropia = ent_libre.mean() if len(ent_libre) else torch.tensor(0.0)
            perdida = perdida_pol + hiper["valor"] * perdida_val - hiper["ent"] * entropia
            opt.zero_grad()
            perdida.backward()
            # Recorte por red y no global: el error inicial del critico (retornos de -20 a -30
            # frente a un valor inicial 0) hace su gradiente ~100 veces mayor que el del actor y
            # un recorte conjunto reducia el paso del actor 50 veces (prueba de humo).
            nn.utils.clip_grad_norm_(politica.actor.parameters(), hiper["grad"])
            nn.utils.clip_grad_norm_(politica.critico.parameters(), hiper["grad"])
            opt.step()
            with torch.no_grad():
                diag["perdida_politica"].append(float(perdida_pol))
                diag["perdida_valor"].append(float(perdida_val))
                diag["entropia_libre"].append(float(entropia))
                # estimador k3 de KL(vieja || nueva): (ratio - 1) - log(ratio), siempre >= 0
                diag["kl_aprox"].append(float(((ratio - 1) - (logp - logp_viejo[b])).mean()))
                diag["clipfrac"].append(float(((ratio - 1).abs() > hiper["clip"]).float().mean()))
    return {k: round(float(np.mean(v)), 4) for k, v in diag.items()}


# ---------------- Validacion, checkpoints y publicacion ----------------
def validar(politica, semillas, variante, tripinfo, decidir=None, escalas=None):
    """Politica congelada (argmax, modo demo) en cada semilla de validacion. Guarda y restaura
    el RNG de random, numpy y torch: el entrenamiento da el mismo CSV con o sin validacion.
    Devuelve {"val_<s>": timeLoss medio, ..., "val": media, "val_total_<s>": retraso total medio
    (timeLoss + espera para entrar), ..., "val_total": media, "eval_timeloss": el de la primera
    semilla, "eval_espera": su espera}.
    Con escalas (--val-escalas), cada semilla en cada nivel de demanda (--scale e): por semilla y nivel
    val_<s>_x<e> y val_total_<s>_x<e>; por nivel, val_x<e> y val_total_x<e> (medias de las semillas,
    con 3 decimales); y val y val_total = la media geometrica de los niveles (no depende de la escala de
    cada nivel). eval_timeloss y eval_espera son entonces los de la primera semilla en el nivel 1 (la demanda
    del escenario), o None si ese nivel no esta (meta: eval_nivel)."""
    estados = (random.getstate(), np.random.get_state(), torch.get_rng_state())
    fila = {}
    if escalas:
        fila["eval_timeloss"] = fila["eval_espera"] = None
    for j, e in enumerate(escalas or [None]):
        x = "" if e is None else sufijo_escala(e)
        for k, s in enumerate(semillas):
            res = correr_episodio("demo", politica, False, 0, s, tripinfo=tripinfo, variante=variante,
                                  decidir=decidir, escala=e)
            fila[f"val_{s}{x}"] = res["timeloss_prom"]
            fila[f"val_total_{s}{x}"] = res["retraso_total_prom"]
            if k == 0 and (e is None or float(e) == 1.0):
                fila["eval_timeloss"], fila["eval_espera"] = res["timeloss_prom"], res["espera_prom"]
        fila[f"val{x}"] = round(float(np.mean([fila[f"val_{s}{x}"] for s in semillas])), 3)
        fila[f"val_total{x}"] = round(float(np.mean([fila[f"val_total_{s}{x}"] for s in semillas])), 3)
    if escalas:
        fila["val"] = media_geometrica([fila[f"val{sufijo_escala(e)}"] for e in escalas])
        fila["val_total"] = media_geometrica([fila[f"val_total{sufijo_escala(e)}"] for e in escalas])
    random.setstate(estados[0])
    np.random.set_state(estados[1])
    torch.set_rng_state(estados[2])
    return fila


def sufijo_escala(e):
    """Sufijo de las claves de un nivel de demanda de la validacion: _x0.5, _x1, _x1.5."""
    return f"_x{float(e):g}"


def media_geometrica(valores):
    """Media geometrica con 3 decimales (como val): la de los niveles de --val-escalas."""
    assert all(v > 0 for v in valores), valores
    return round(float(np.exp(np.mean(np.log(np.asarray(valores, dtype=np.float64))))), 3)


def ruta_checkpoint(tag, ep, ext=".pt"):
    return os.path.join("checkpoints", f"{tag}_ep{ep:03d}{ext}")


def archivos_etiqueta(tag, carpeta="checkpoints"):
    """{episodio: [rutas]} de los checkpoints (.pt), sus .json y sus estados (.estado.pt) del tag en la carpeta, y
    los temporales de uno a medio escribir (ruta_tmp). Los .roto (estados apartados por danados) no entran: no se
    borran."""
    patron = re.compile(re.escape(tag) + r"_ep(\d{3,})\.(pt|json|estado\.pt|tmp|json\.tmp|estado\.tmp|estado\.pt\.tmp)$")
    res = {}
    for ruta in glob.glob(os.path.join(carpeta, f"{tag}_ep*")):
        m = patron.match(os.path.basename(ruta))
        if m:
            res.setdefault(int(m.group(1)), []).append(ruta)
    return res


def limpiar_checkpoints(tag, desde=0):
    """Borra los checkpoints, sus .json y sus estados de una corrida anterior con el mismo tag cuyo episodio pase
    de desde (0: todos), y crea la carpeta. Al reanudar se llama con desde = el episodio de partida."""
    os.makedirs("checkpoints", exist_ok=True)
    for ep, rutas in archivos_etiqueta(tag).items():
        if ep > desde:
            for ruta in rutas:
                os.remove(ruta)


def elegir_checkpoint(val_serie):
    """val_serie = [[ep, val_s1, val_s2, val], ...]: la fila de menor val (empate: la mas tardia)."""
    return min(reversed(val_serie), key=lambda f: f[-1])


def sembrar(base):
    random.seed(base)
    np.random.seed(base)
    torch.manual_seed(base)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    return np.random.default_rng(base)


def hash_git():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                              text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def correcciones_v2(args):
    """(descuento por segundo, exploracion comun) de esta corrida: --v2 son las dos; --solo-descuento y
    --solo-exploracion, una cada una (ablacion del plan 3)."""
    v2 = getattr(args, "v2", False)
    return (v2 or getattr(args, "solo_descuento", False), v2 or getattr(args, "solo_exploracion", False))


def opciones_etapas(args):
    """Opciones de las Etapas 3 y 4 de esta corrida, solo las activas (asi los meta y los estados de antes no
    cambian): van a meta["opciones"] y a la configuracion que compara --reanudar. evaluar.py lee del meta las que
    cambian como juega la politica (configurar_desde_meta)."""
    op = {}
    if C["obs_cerca"]:
        op["obs_cercana"] = C["obs_cerca"]
    if C["msg_paso"]:
        op["msg_cada_paso"] = True
    if C["sin_forzadas"]:
        op["sin_forzadas"] = True
    if C["paso_decision"] != PASO_CONTROL:
        op["paso_decision"] = C["paso_decision"]
    if C["vnorm"] is not None:
        op.update({"norm_valor": True, "norm_beta": C["vnorm"].beta})
    if getattr(args, "ent_final", None) is not None:
        op["ent_final"] = args.ent_final
    if getattr(args, "escalas_demanda", None):
        op["escala_demanda"] = list(args.escalas_demanda)
        if args.curriculo:
            op["curriculo"] = args.curriculo
    if getattr(args, "escalas_val", None):
        op["val_escalas"] = list(args.escalas_val)
    return op


def coef_entropia(ep, ent_final, horizonte):
    """Coeficiente de entropia del episodio ep: HIPER["ent"] y, con --ent-final, lineal hasta ent_final en el
    horizonte de la tasa (en el ultimo episodio del horizonte vale ent_final) y constante despues."""
    if ent_final is None:
        return HIPER["ent"]
    frac = min(1.0, (ep - 1) / max(1, horizonte - 1))
    return HIPER["ent"] + (ent_final - HIPER["ent"]) * frac


def meta_base(args, val_seeds):
    """Meta comun de checkpoints y politica publicada."""
    descuento, exploracion = correcciones_v2(args)
    ins = getattr(args, "recompensa_insercion", False)
    criterio = getattr(args, "criterio_val", "timeloss")
    opciones = {"v2": descuento and exploracion, "recompensa_insercion": ins,
                "etiqueta": getattr(args, "etiqueta", "") or "", "criterio_val": criterio}
    if C["obs_ins"]:            # solo si esta activa: los meta de antes no cambian
        opciones["obs_insercion"] = True
    # plan3: igual, solo si estan activas (la tasa, si no es la de siempre)
    if descuento != exploracion:
        opciones["solo_descuento" if descuento else "solo_exploracion"] = True
    horizonte, piso = getattr(args, "lr_horizonte", None), getattr(args, "lr_piso", 0.0)
    if horizonte and horizonte != args.episodios:
        opciones["lr_horizonte"] = horizonte
    if piso:
        opciones["lr_piso"] = piso
    opciones.update(opciones_etapas(args))
    return {"escenario": C["escenario"], "variante": args.variante, "algoritmo": "ippo",
            "recompensa": RECOMPENSA[args.variante] + ("+insercion" if ins else ""),
            "etiqueta": opciones["etiqueta"], "opciones": opciones,
            "descuento": "por segundo: gamma^(dt/5)" if descuento else "por decision",
            "exploracion": (f"comun: un u por segundo, default_rng(semilla + {SEMILLA_EXPL})" if exploracion
                            else "independiente (dist.sample)"),
            "recompensa_insercion": ("W1 x vehiculos que esperan para entrar por las aristas de entrada de "
                                     "los accesos del agente, cada segundo" if ins else "no"),
            "criterio_validacion": ("retraso total (timeLoss + espera para entrar), media de val_total_<s>"
                                    if criterio == "total" else "timeLoss, media de val_<s>"),
            "base": args.seed, "episodios": args.episodios,
            "dim_obs": C["dim_obs"], "n_id": C["n_id"], "lados": list(C["lados"]),
            "ocultas": OCULTAS, "hiper": HIPER, "w1": W1, "w2": W2, "w3": W3, "w4": W4,
            "escala_r": ESCALA_R, "fase_av": C["fase_av"], "vecinos": C["vecinos"], "cap": C["cap"],
            "plazas": C["plazas"], "umbral_spillback": comun.UMBRAL_SPILLBACK,
            "latencia_entrenamiento": 0, "perdida_entrenamiento": 0.0,
            "val_seeds": val_seeds, "eval_seed": val_seeds[0] if val_seeds else None,
            "torch": torch.__version__, "python": sys.version.split()[0], "sumo": "1.25.0",
            "git": hash_git(), "features": nombres_features()}


# ---------------- Plan 3: tasa, registro extendido y reanudacion ----------------
def tasa(ep, horizonte, piso=0.0):
    """lr del episodio ep (--lr-horizonte, --lr-piso): lineal de HIPER["lr"] a 0 en `horizonte` episodios, sin bajar
    de piso * HIPER["lr"]. Con horizonte = --episodios y piso 0 da, bit a bit, la formula de siempre."""
    return HIPER["lr"] * max(piso, 1 - (ep - 1) / horizonte)


def campos_csv(val_seeds, extendido=False, escalas=None, extra=()):
    """Columnas del CSV de entrenamiento: CAMPOS_IPPO y, con --registro-extendido, al final val_<s> y val_total_<s>
    de las semillas de validacion que no tienen columna fija (con --val-escalas, val_x<e> y val_total_x<e> de cada
    nivel), CAMPOS_EXTENDIDOS y las columnas de las opciones activas que las tienen (extra: escala, vn_media,
    vn_desv)."""
    if not extendido:
        return list(CAMPOS_IPPO)
    if escalas:
        xs = [sufijo_escala(e) for e in escalas]
        por_semilla = [f"val{x}" for x in xs] + [f"val_total{x}" for x in xs]
    else:
        por_semilla = [f"val_{s}" for s in val_seeds] + [f"val_total_{s}" for s in val_seeds]
    return CAMPOS_IPPO + [c for c in por_semilla if c not in CAMPOS_IPPO] + CAMPOS_EXTENDIDOS + list(extra)


def linea_csv(campos, fila=None):
    """Texto de una fila del CSV de entrenamiento (de la cabecera si fila es None), el mismo que csv.DictWriter
    escribe en el archivo. El estado guarda estas lineas y una reanudacion las vuelve a escribir tal cual."""
    buf = io.StringIO()
    escritor = csv.DictWriter(buf, fieldnames=campos, extrasaction="ignore")
    if fila is None:
        escritor.writeheader()
    else:
        escritor.writerow(fila)
    return buf.getvalue()


def meta_checkpoint(meta, ep, val, val_seeds, escalas=None, tramos=()):
    """Meta del checkpoint del episodio ep: el de la corrida mas su validacion (val trae val_<s>, val,
    val_total_<s> y val_total; con --val-escalas, ademas las de cada nivel, de validar()) y, si los episodios <= ep
    los escribio mas de un codigo, sus tramos."""
    if escalas:
        xs = [sufijo_escala(e) for e in escalas]
        m = {**meta, "ep_checkpoint": ep, "val_checkpoint": val["val"],
             **{f"val{x}": val[f"val{x}"] for x in xs},
             **{f"val_{s}{x}": val[f"val_{s}{x}"] for x in xs for s in val_seeds},
             "val_total_checkpoint": val["val_total"],
             **{f"val_total{x}": val[f"val_total{x}"] for x in xs},
             **{f"val_total_{s}{x}": val[f"val_total_{s}{x}"] for x in xs for s in val_seeds}}
    else:
        m = {**meta, "ep_checkpoint": ep, "val_checkpoint": val["val"],
             **{f"val_{s}": val[f"val_{s}"] for s in val_seeds},
             "val_total_checkpoint": val["val_total"],
             **{f"val_total_{s}": val[f"val_total_{s}"] for s in val_seeds}}
    if C.get("vnorm") is not None:      # --norm-valor: la escala del critico de este checkpoint (media, desv y estado)
        media, desv = C["vnorm"].media_desv()
        m.update({"vn_media": round(media, 4), "vn_desv": round(desv, 4), "vn_estado": C["vnorm"].estado()})
    distintos = procedencia(tramos, ep)
    if distintos:
        m["tramos"] = distintos
    return m


def procedencia(tramos, hasta=None):
    """Los tramos ({desde, hasta, git, codigo}) que escribieron los episodios <= hasta (todos si es None), solo si
    hay mas de una huella de codigo entre ellos; si no, None y el meta queda como siempre."""
    vistos = [dict(t, hasta=t["hasta"] if hasta is None else min(t["hasta"], hasta)) for t in tramos
              if hasta is None or t["desde"] <= hasta]
    return vistos if len({t["codigo"] for t in vistos}) > 1 else None


def huella_codigo():
    """sha256 de rl_ippo.py, comun.py, rl_corredor.py y escenarios_plan2.py (con fin de linea \\n, para que dos copias
    del mismo commit den lo mismo): la procedencia de cada tramo de una corrida."""
    h = hashlib.sha256()
    for ruta in (os.path.abspath(__file__), comun.__file__, rc.__file__, escenarios_plan2.__file__):
        with open(ruta, "rb") as f:
            texto = f.read().replace(b"\r\n", b"\n")
        h.update(os.path.basename(ruta).encode() + b"\0" + hashlib.sha256(texto).digest())
    return h.hexdigest()


def sha256(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def tomado(error):
    """El error es de un archivo que otro proceso tiene abierto (antivirus, respaldo, Excel): PermissionError, o el
    RuntimeError con que torch.save dice lo mismo ('error code: 32')."""
    if isinstance(error, PermissionError):
        return True
    texto = str(error)
    return isinstance(error, RuntimeError) and ("error code: 32" in texto or "error code: 5" in texto
                                                or "Permission denied" in texto)


def reintentar(funcion, *args, intentos=20, espera=0.5):
    """funcion(*args), reintentando mientras Windows niegue el archivo porque otro proceso lo tiene abierto."""
    for k in range(intentos):
        try:
            return funcion(*args)
        except (PermissionError, RuntimeError) as e:
            if not tomado(e) or k == intentos - 1:
                raise
            time.sleep(espera)


def reemplazar(tmp, destino, intentos=20):
    """os.replace con reintentos: en Windows falla mientras otro proceso (respaldo, antivirus) tiene abierto el
    destino."""
    reintentar(os.replace, tmp, destino, intentos=intentos)


def ruta_tmp(destino):
    """Temporal de un archivo: un .pt cambia .pt por .tmp (torch.save guarda dentro del zip el nombre del archivo sin
    su ultima extension: asi el .pt sale con los mismos bytes que con un torch.save directo); lo demas, + .tmp."""
    raiz, ext = os.path.splitext(destino)
    return raiz + ".tmp" if ext == ".pt" else destino + ".tmp"


def bajar_a_disco(ruta):
    """fsync de un archivo ya escrito y cerrado, antes de renombrarlo a su nombre final: tras un corte de luz no queda
    un archivo a medias con ese nombre. 'ab' no cambia el contenido (FlushFileBuffers pide permiso de escritura)."""
    with open(ruta, "ab") as f:
        os.fsync(f.fileno())


def escribir_atomico(destino, escribir):
    """escribir(tmp) en el temporal, fsync y os.replace al destino, con reintentos si el archivo esta tomado: con su
    nombre final solo hay un archivo entero (el de antes o el nuevo)."""
    tmp = ruta_tmp(destino)
    reintentar(escribir, tmp)
    reintentar(bajar_a_disco, tmp)
    reemplazar(tmp, destino)


def guardar_pt(objeto, destino):
    escribir_atomico(destino, lambda tmp: torch.save(objeto, tmp))


def guardar_json(datos, destino):
    """Mismo texto que json.dump(datos, open(destino, "w", encoding="utf-8"), indent=1, ensure_ascii=False)."""
    def escribir(tmp):
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=1, ensure_ascii=False)
    escribir_atomico(destino, escribir)


def copiar(origen, destino):
    escribir_atomico(destino, lambda tmp: shutil.copyfile(origen, tmp))


def apartar(ruta):
    """Renombra un archivo danado a .roto (o .roto2, ...) en vez de borrarlo, y devuelve el nombre nuevo."""
    destino, n = ruta + ".roto", 1
    while os.path.exists(destino):
        n += 1
        destino = f"{ruta}.roto{n}"
    reemplazar(ruta, destino)
    return destino


def config_reanudacion(args, val_seeds):
    """Lo que debe ser igual entre un estado y la corrida que lo reanuda para que siga exacta la misma corrida. No
    entran las opciones que solo cambian nombres, cortes, validaciones o la eleccion final (--episodios,
    --eval-cada, --etiqueta, --criterio-val, --csv, --hasta-ep, --guardar-estado, --registro-extendido); la tasa se
    compara aparte, episodio por episodio. Una opcion nueva entra aqui solo si esta activa: asi un estado escrito
    antes de que existiera sigue valiendo con ella apagada."""
    descuento, exploracion = correcciones_v2(args)
    return {"escenario": C["escenario"], "variante": args.variante, "base": args.seed, "dim_obs": C["dim_obs"],
            "hiper": dict(HIPER), "descuento": descuento, "exploracion": exploracion,
            "recompensa_insercion": args.recompensa_insercion, "obs_insercion": C["obs_ins"],
            "val_seeds": list(val_seeds), **opciones_etapas(args)}


def estado_generadores(rng, rng_escala=None):
    """random, numpy global, torch, el default_rng de sembrar (baraja los minilotes) y, con --escala-demanda, el
    del factor de demanda, en tipos que torch.load lee con weights_only=True."""
    version, interno, gauss = random.getstate()
    nombre, claves, pos, tiene_gauss, gauss_np = np.random.get_state()
    gen = {"random": [version, list(interno), gauss],
           "numpy": [nombre, [int(x) for x in claves], int(pos), int(tiene_gauss), float(gauss_np)],
           "torch": torch.get_rng_state(), "rng": rng.bit_generator.state}
    if rng_escala is not None:
        gen["escala"] = rng_escala.bit_generator.state
    return gen


def restaurar_generadores(gen, rng, rng_escala=None):
    version, interno, gauss = gen["random"]
    random.setstate((version, tuple(interno), gauss))
    nombre, claves, pos, tiene_gauss, gauss_np = gen["numpy"]
    np.random.set_state((nombre, np.array(claves, dtype=np.uint32), pos, tiene_gauss, gauss_np))
    torch.set_rng_state(gen["torch"])
    rng.bit_generator.state = gen["rng"]
    if rng_escala is not None:
        rng_escala.bit_generator.state = gen["escala"]


def nueva_corrida(campos):
    """Lo que el bucle de entrenamiento lleva de un episodio al siguiente, ademas de pesos, Adam y generadores: lo
    que --guardar-estado guarda y --reanudar restaura."""
    return {"val_serie": [], "val_total_serie": [],   # [ep, val_<s1>, ..., media] en timeLoss y en retraso total
            "lineas": [linea_csv(campos)],            # el CSV como esta en el archivo: cabecera y una por episodio
            "lr": [],                                 # tasa usada en cada episodio
            "ent": [],                                # coeficiente de entropia de cada episodio
            "archivos": {},                           # {nombre: sha256} de los checkpoints (con --guardar-estado)
            "origen": [],                             # [{"corrida": tag, "episodio": k}] si sigue a otra etiqueta
            "tramos": [],                             # [{desde, hasta, git, codigo}]: quien escribio cada episodio
            "reanudaciones": [],                      # B22: [{partida, episodios, filas, distintos}] de cada relanzamiento
            "codigo": "",                             # huella del codigo de este proceso (huella_codigo)
            "previas": {},                            # filas > partida de un intento anterior (B22, para comparar)
            "b22": None}                              # la comparacion B22 de este proceso, si hay previas


def guardar_estado(ruta, ep, etiqueta, args, val_seeds, corrida, politica, opt, rng, ruta_csv, git,
                   rng_escala=None):
    """--guardar-estado: todo lo necesario para seguir exacto despues del episodio ep. Se escribe al final del
    episodio, despues del checkpoint y de la fila del CSV, en un temporal bajado a disco que se renombra: si el
    estado existe, esta entero y todo lo <= ep esta completo. Etapas 3 y 4 (claves nuevas, la version sigue en 1):
    el coeficiente de entropia de cada episodio, las medias de --norm-valor y el generador de --escala-demanda."""
    estado = {"version": VERSION_ESTADO, "episodio": ep, "tag": etiqueta, "etiqueta": args.etiqueta,
              "config": config_reanudacion(args, val_seeds), "episodios": args.episodios,
              "eval_cada": args.eval_cada, "ruta_csv": ruta_csv, "csv": "".join(corrida["lineas"]),
              "lr": list(corrida["lr"]), "ent": list(corrida["ent"]), "val_serie": corrida["val_serie"],
              "val_total_serie": corrida["val_total_serie"], "archivos": dict(corrida["archivos"]),
              "origen": corrida["origen"], "fase_av": dict(C["fase_av"]),
              "norm_valor": C["vnorm"].estado() if C["vnorm"] is not None else None,
              "politica": politica.state_dict(), "opt": opt.state_dict(),
              "generadores": estado_generadores(rng, rng_escala),
              "git": git, "torch": str(torch.__version__), "python": sys.version.split()[0],
              "codigo": corrida["codigo"], "tramos": [dict(t) for t in corrida["tramos"]],
              "reanudaciones": [dict(r) for r in corrida["reanudaciones"]]}
    guardar_pt(estado, ruta)


def estado_valido(ruta, tag=None):
    """(estado, None) si el estado sirve para reanudar; (None, motivo) si no: el zip esta danado (testzip comprueba el
    CRC de cada pieza; torch.load no lo hace), no carga, es de otra version, el episodio no es el de su nombre o
    algun checkpoint que anota (en su misma carpeta) falta o no tiene su sha256. Con tag, un estado de otra etiqueta
    (la copia de un origen en una etiqueta nueva) no se juzga por sus checkpoints: llevan el nombre del origen y
    pueden estar en la carpeta del origen; si se usa, reanudar los verifica antes de copiar."""
    try:
        with zipfile.ZipFile(ruta) as z:
            malo = z.testzip()
        if malo is not None:
            return None, f"la pieza {malo} del zip no pasa su CRC"
        estado = torch.load(ruta, weights_only=True)
    except Exception as e:          # zipfile.BadZipFile, EOFError, RuntimeError, OSError, del unpickler...
        return None, f"no se puede leer ({type(e).__name__}: {str(e)[:160]})"
    if not isinstance(estado, dict) or estado.get("version") != VERSION_ESTADO:
        version = estado.get("version") if isinstance(estado, dict) else None
        return None, f"es de la version {version} del estado (este codigo lee la {VERSION_ESTADO})"
    m = re.search(r"_ep(\d{3,})\.estado\.pt$", os.path.basename(ruta))
    if m and int(m.group(1)) != estado.get("episodio"):
        return None, f"guarda el episodio {estado.get('episodio')}"
    carpeta = os.path.dirname(ruta) or "."
    for archivo, h in (estado.get("archivos", {}) if tag is None or estado.get("tag") == tag else {}).items():
        r = os.path.join(carpeta, archivo)
        if not os.path.exists(r) or sha256(r) != h:
            return None, f"{archivo} falta o no es el que escribio la corrida del estado"
    return estado, None


def cargar_estado(ruta):
    """--reanudar con una ruta: el estado, o sale con el motivo si no sirve (no se aparta: lo eligio quien lanza)."""
    if not os.path.exists(ruta):
        raise SystemExit(f"--reanudar: no existe {ruta}")
    estado, motivo = estado_valido(ruta)
    if estado is None:
        raise SystemExit(f"--reanudar: {ruta} no sirve: {motivo}")
    return estado


def ultimo_estado(tag):
    """--reanudar auto: (ruta, estado) del estado valido de mayor episodio del tag en checkpoints/, o (None, None).
    Recorre de mayor a menor; uno que no sirve (estado_valido) se renombra a .roto con un AVISO, sin borrarlo, y se
    prueba el anterior (reanudar desde uno anterior da la misma corrida: borra lo posterior y lo rehace)."""
    estados = sorted(((ep, r) for ep, rutas in archivos_etiqueta(tag).items() for r in rutas
                      if r.endswith(".estado.pt")), reverse=True)
    for _, ruta in estados:
        estado, motivo = estado_valido(ruta, tag)
        if estado is not None:
            return ruta, estado
        roto = apartar(ruta)
        print(f"AVISO: {ruta} no sirve para reanudar ({motivo}); queda como {os.path.basename(roto)} y se prueba "
              "el estado anterior", flush=True)
    return None, None


def comprobar_estado(estado, args, val_seeds, horizonte):
    """El estado debe ser de esta misma corrida: la misma configuracion y la misma tasa en cada episodio hasta el
    de partida. Si no, sale con el motivo: seguir daria una corrida que no es ninguna de las dos."""
    viejo, nuevo = estado["config"], config_reanudacion(args, val_seeds)
    distintas = sorted(c for c in set(viejo) | set(nuevo) if viejo.get(c) != nuevo.get(c))
    if distintas:
        raise SystemExit(f"--reanudar: el estado es de otra configuracion ({', '.join(distintas)})")
    k = estado["episodio"]
    if k > args.episodios:
        raise SystemExit(f"--reanudar: el estado esta en el episodio {k} y --episodios es {args.episodios}")
    if len(estado["lr"]) != k:
        raise SystemExit(f"--reanudar: el estado no trae la tasa de los {k} episodios")
    esperada = [tasa(e, horizonte, args.lr_piso) for e in range(1, k + 1)]
    distinto = next((e for e in range(1, k + 1) if esperada[e - 1] != estado["lr"][e - 1]), None)
    if distinto is not None:
        raise SystemExit(f"--reanudar: en el episodio {distinto} la tasa de esta corrida es "
                         f"{esperada[distinto - 1]!r} y la del estado {estado['lr'][distinto - 1]!r} (revisa "
                         "--episodios, --lr-horizonte y --lr-piso)")
    if "ent" in estado:         # un estado de antes de las Etapas 3 y 4 no lo trae: era HIPER["ent"] (en la config)
        esperada = [coef_entropia(e, args.ent_final, horizonte) for e in range(1, k + 1)]
        if estado["ent"] != esperada:
            raise SystemExit("--reanudar: el calendario de entropia de esta corrida no es el del estado (revisa "
                             "--hiper ent, --ent-final y el horizonte de la tasa)")


def ya_terminada(estado, etiqueta, ruta_csv, ruta_politica, criterio):
    """La corrida ya llego al final y publico: el CSV en disco es el del estado del ultimo episodio y la politica
    publicada es el checkpoint que eligen sus series con este criterio (sin validacion, los pesos del estado)."""
    try:
        with open(ruta_csv, newline="") as f:
            if f.read() != estado["csv"]:
                return False
        with open(ruta_politica.replace(".pt", ".json"), encoding="utf-8") as f:
            meta = json.load(f)
        if meta.get("val_serie") != estado["val_serie"] or \
                meta.get("val_total_serie", []) != estado["val_total_serie"]:
            return False
        if estado["val_serie"]:
            serie = estado["val_total_serie"] if criterio == "total" else estado["val_serie"]
            return meta["ep_elegido"] == elegir_checkpoint(serie)[0] and \
                sha256(ruta_politica) == sha256(ruta_checkpoint(etiqueta, meta["ep_elegido"]))
        publicada = torch.load(ruta_politica, weights_only=True)
        return all(torch.equal(publicada[c], v) for c, v in estado["politica"].items())
    except Exception:          # falta o esta rota alguna pieza: no termino, se publica de nuevo
        return False


def lineas_csv_estado(texto, campos, etiqueta=None):
    """Las lineas del CSV que guarda un estado, para las columnas de esta corrida. Con las mismas columnas (y la
    misma etiqueta) salen tal cual. Si esta corrida agrega columnas, quedan vacias en esas filas (el estado no las
    tenia); si el estado tiene una columna que esta corrida no escribe, sale con error para no perderla. Con
    etiqueta, la columna etiqueta pasa a la de esta corrida (reanudacion con etiqueta nueva)."""
    lineas = [linea + "\r\n" for linea in texto.split("\r\n")[:-1]]
    cabecera = next(csv.reader(lineas[:1]))
    if cabecera == campos and etiqueta is None:
        return lineas
    perdidas = [c for c in cabecera if c not in campos]
    if perdidas:
        raise SystemExit(f"--reanudar: el CSV del estado tiene columnas que esta corrida no escribe "
                         f"({perdidas[:4]}): usa las mismas --val-seeds y el mismo --registro-extendido")
    nuevas = [c for c in campos if c not in cabecera]
    if nuevas:
        print(f"AVISO: las filas copiadas del estado quedan sin {nuevas[:4]}{'...' if len(nuevas) > 4 else ''}")
    salida = [linea_csv(campos)]
    for fila in csv.DictReader(io.StringIO(texto, newline="")):
        if etiqueta is not None:
            fila["etiqueta"] = etiqueta
        salida.append(linea_csv(campos, fila))
    return salida


def reanudar(estado, ruta_estado, etiqueta, args, campos, meta, ruta_csv, politica, opt, rng, rng_escala=None):
    """--reanudar: deja los archivos de la etiqueta como los habria dejado una corrida seguida al terminar el
    episodio de partida k, restaura pesos, Adam, generadores y series, y devuelve la corrida para seguir en k + 1.
      Misma etiqueta: verifica (sha256) los checkpoints <= k y borra los checkpoints y estados > k de un intento
      caido.
      Etiqueta nueva: borra lo que hubiera de la etiqueta nueva y copia los checkpoints y estados <= k de la de
      origen (verificados; el .pt byte a byte, el .json con el meta de esta corrida); las filas del CSV <= k pasan
      con la etiqueta nueva y meta["reanudado_de"] anota de donde viene.
      En los dos casos guarda las filas > k que haya en el CSV de esta corrida (un intento anterior) para
      compararlas con las que se rehacen (B22).
    Las copias van a un temporal bajado a disco que se renombra (copiar, guardar_json): un corte a mitad de la copia
    no deja un archivo a medias con su nombre final."""
    k = estado["episodio"]
    misma = estado["tag"] == etiqueta
    carpeta = os.path.dirname(ruta_estado) or "."
    en_su_lugar = misma and os.path.normcase(os.path.abspath(carpeta)) == \
        os.path.normcase(os.path.abspath("checkpoints"))
    corrida = nueva_corrida(campos)
    # un estado escrito antes de la huella del codigo: un tramo sin huella (cuenta como otro codigo)
    tramos = estado.get("tramos") or [{"desde": 1, "hasta": k, "git": estado.get("git", ""), "codigo": None}]
    corrida.update({"val_serie": estado["val_serie"], "val_total_serie": estado["val_total_serie"],
                    "lr": list(estado["lr"]), "ent": list(estado.get("ent", [HIPER["ent"]] * k)),
                    "origen": estado["origen"] + ([] if misma else [{"corrida": estado["tag"], "episodio": k}]),
                    "tramos": [dict(t) for t in tramos],
                    "reanudaciones": [dict(r) for r in estado.get("reanudaciones", [])]})
    C["fase_av"].update(estado["fase_av"])     # el meta lo comparte: sin episodios por correr quedaria vacio
    if corrida["origen"]:
        meta["reanudado_de"] = corrida["origen"]

    def nombre(tag, ep, ext=".pt"):
        return os.path.basename(ruta_checkpoint(tag, ep, ext))

    # primero todo lo que puede fallar, sin tocar ningun archivo
    faltan = [nombre(estado["tag"], f[0], ext) for f in estado["val_serie"] for ext in (".pt", ".json")
              if nombre(estado["tag"], f[0], ext) not in estado["archivos"]]
    if faltan:
        raise SystemExit(f"--reanudar: el estado no anota el sha256 de {faltan[:2]}")
    for archivo, h in estado["archivos"].items():
        ruta = os.path.join(carpeta, archivo)
        if not os.path.exists(ruta) or sha256(ruta) != h:
            raise SystemExit(f"--reanudar: {ruta} falta o no es el que escribio la corrida del estado")
    corrida["lineas"] = lineas_csv_estado(estado["csv"], campos, None if misma else args.etiqueta)
    if os.path.exists(ruta_csv):          # CSV de un intento anterior de esta misma llamada (B22)
        try:
            with open(ruta_csv, newline="") as f:
                for fila in csv.DictReader(f):
                    if None not in fila and None not in fila.values() and (fila.get("episodio") or "").isdigit() \
                            and int(fila["episodio"]) > k:
                        corrida["previas"][int(fila["episodio"])] = fila
        except (OSError, csv.Error, UnicodeDecodeError) as e:      # tomado o a medio escribir tras un corte
            corrida["previas"] = {}
            print(f"AVISO: no se pudo leer {ruta_csv} del intento anterior ({e}); no se comparan los episodios "
                  "rehechos (B22)")
    if corrida["previas"]:
        corrida["b22"] = {"partida": k, "episodios": [], "filas": 0, "distintos": []}
    # despues, los archivos de la etiqueta
    if en_su_lugar:
        limpiar_checkpoints(etiqueta, desde=k)
        corrida["archivos"] = dict(estado["archivos"])
    else:
        limpiar_checkpoints(etiqueta, desde=k if misma else 0)
        for f in estado["val_serie"]:
            ep = f[0]
            destino = ruta_checkpoint(etiqueta, ep)
            origen_json = os.path.join(carpeta, nombre(estado["tag"], ep, ".json"))
            if misma:
                copiar(origen_json, destino.replace(".pt", ".json"))
            else:
                # meta de esta corrida + la validacion de ese checkpoint (todo lo que va desde ep_checkpoint, en el
                # mismo orden, sin los tramos del origen) y los tramos de esta corrida hasta ep: lo que habria
                # escrito meta_checkpoint en una corrida seguida con esta etiqueta
                with open(origen_json, encoding="utf-8") as g:
                    viejo = json.load(g)
                claves = list(viejo)
                nuevo = {**meta, **{c: viejo[c] for c in claves[claves.index("ep_checkpoint"):] if c != "tramos"}}
                distintos = procedencia(corrida["tramos"], ep)
                if distintos:
                    nuevo["tramos"] = distintos
                guardar_json(nuevo, destino.replace(".pt", ".json"))
            copiar(os.path.join(carpeta, nombre(estado["tag"], ep)), destino)
            for ext in (".pt", ".json"):
                corrida["archivos"][nombre(etiqueta, ep, ext)] = sha256(ruta_checkpoint(etiqueta, ep, ext))
        for ep, rutas in sorted(archivos_etiqueta(estado["tag"], carpeta).items()):
            for ruta in rutas:
                if ep <= k and ruta.endswith(".estado.pt"):
                    copiar(ruta, ruta_checkpoint(etiqueta, ep, ".estado.pt"))
    politica.load_state_dict(estado["politica"])
    opt.load_state_dict(estado["opt"])
    restaurar_generadores(estado["generadores"], rng, rng_escala)
    if C["vnorm"] is not None:          # la configuracion ya comprobo que el estado tambien usa --norm-valor
        C["vnorm"].restaurar(estado["norm_valor"])
    return corrida


def comparar_intento(previas, lineas):
    """B22: los episodios rehechos al reanudar deben repetir los del intento anterior (salvo la columna segundos).
    lineas = cabecera y filas nuevas; devuelve {episodio: [columnas distintas]} de los que no lo repiten."""
    nuevas = {int(f["episodio"]): f for f in csv.DictReader(io.StringIO("".join(lineas), newline=""))}
    distintos = {}
    for k in sorted(set(previas) & set(nuevas)):
        cols = [c for c, v in nuevas[k].items() if c != "segundos" and c in previas[k] and previas[k][c] != v]
        if cols:
            distintos[k] = cols
    return distintos


def rehecho(corrida, ep, linea, etiqueta):
    """B22, en cuanto sale la fila rehecha del episodio ep: la compara con la del intento anterior y lo anota en la
    reanudacion de este proceso (corrida["b22"], que va al estado y al meta). Si no la repite, avisa en el log y lo
    deja en checkpoints/<tag>_rehechos.json (p3_noche lo muestra como PROBLEMA). No cambia el codigo de salida."""
    reg = corrida["b22"]
    if not reg["filas"]:
        corrida["reanudaciones"].append(reg)
    reg["episodios"] = [reg["episodios"][0] if reg["episodios"] else ep, ep]
    reg["filas"] += 1
    distintos = comparar_intento(corrida["previas"], [corrida["lineas"][0], linea])
    if not distintos:
        return
    reg["distintos"].append([ep, distintos[ep]])
    print(f"AVISO: el episodio {ep} no repite el intento anterior ({', '.join(distintos[ep][:6])})", flush=True)
    anotar_rehechos(corrida, etiqueta)


def anotar_rehechos(corrida, etiqueta):
    """checkpoints/<tag>_rehechos.json: lo que ya anotaron relanzamientos anteriores de esta etiqueta y, al final, la
    comparacion de este proceso tal como va (se reescribe en cada diferencia y al terminar el tramo)."""
    ruta = os.path.join("checkpoints", f"{etiqueta}_rehechos.json")
    if "rehechos_antes" not in corrida:
        try:
            with open(ruta, encoding="utf-8") as f:
                antes = json.load(f)
            corrida["rehechos_antes"] = antes if isinstance(antes, list) else []
        except (OSError, ValueError):
            corrida["rehechos_antes"] = []
        corrida["rehechos_fecha"] = time.strftime("%Y-%m-%d %H:%M:%S")
        corrida["rehechos_git"] = hash_git()
    guardar_json(corrida["rehechos_antes"] + [{"tag": etiqueta, "fecha": corrida["rehechos_fecha"],
                                               "git": corrida["rehechos_git"], "codigo": corrida["codigo"],
                                               **corrida["b22"]}], ruta)


def resumen_b22(corrida, etiqueta):
    reg = corrida["b22"]
    if not reg or not reg["filas"]:
        return
    a, b = reg["episodios"]
    if reg["distintos"]:
        anotar_rehechos(corrida, etiqueta)          # el registro completo (filas y episodios hasta el final)
        print(f"AVISO: {len(reg['distintos'])} de los {reg['filas']} episodios rehechos ({a}-{b}) no repiten el "
              f"intento anterior (B22); detalle en checkpoints/{etiqueta}_rehechos.json", flush=True)
    else:
        print(f"Reanudacion: los episodios {a}-{b} repiten el intento anterior ({reg['filas']} filas, sin la "
              "columna segundos)", flush=True)


# ---------------- Main ----------------
def construir_parser():
    """El parser de rl_ippo; --escenario acepta los escenarios de ESCENARIOS al momento de llamarla."""
    ap = argparse.ArgumentParser(prog="rl_ippo.py")
    ap.add_argument("modo", choices=["train", "demo"])
    ap.add_argument("--escenario", choices=sorted(ESCENARIOS), default="corredor")
    ap.add_argument("--variante", choices=["local", "vecinos", "spill", "cambio"], default="vecinos")
    ap.add_argument("--episodios", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42, help="semilla base (entrenamiento: base + episodio)")
    ap.add_argument("--eval-cada", type=int, default=10, help="validar cada N episodios (0 = nunca)")
    ap.add_argument("--val-seeds", default="999,1999", help="semillas de validacion separadas por coma")
    ap.add_argument("--latencia", type=int, default=0, help="segundos de retardo del canal (demo)")
    ap.add_argument("--perdida", type=float, default=0.0, help="probabilidad de perder un mensaje (demo)")
    ap.add_argument("--csv", default=None,
                    help="CSV de salida (por defecto resultados_<esc>_ippo_<variante>_s<seed>.csv)")
    ap.add_argument("--politica", default=None, help="archivo .pt para demo")
    ap.add_argument("--hiper", default="", help="cambios a HIPER, p. ej. lr=1e-3,minibatch=64")
    ap.add_argument("--serie", action="store_true")
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--delay", type=int, default=30)
    ap.add_argument("--v2", action="store_true",
                    help="correccion V2 (Anexo G): descuento por segundo y exploracion comun (solo train)")
    ap.add_argument("--recompensa-insercion", action="store_true",
                    help="correccion INS: la recompensa cuenta los vehiculos que esperan para entrar")
    ap.add_argument("--etiqueta", default="",
                    help="se agrega a la variante en los nombres de salida (p. ej. v2, ins, v2ins)")
    ap.add_argument("--criterio-val", choices=["timeloss", "total"], default="timeloss",
                    help="metrica de validacion con la que se elige el checkpoint publicado")
    ap.add_argument("--obs-insercion", action="store_true",
                    help="Enmienda 2: la observacion incluye los vehiculos que esperan para entrar por cada acceso")
    # plan3 (05.11.2026): todas apagadas por defecto
    ap.add_argument("--solo-descuento", action="store_true",
                    help="ablacion de V2: solo el descuento por segundo (con --solo-exploracion es --v2)")
    ap.add_argument("--solo-exploracion", action="store_true",
                    help="ablacion de V2: solo la exploracion comun (con --solo-descuento es --v2)")
    ap.add_argument("--lr-horizonte", type=int, default=None,
                    help="episodios en que el lr baja linealmente a 0 (por defecto --episodios)")
    ap.add_argument("--lr-piso", type=float, default=0.0, help="fraccion minima del lr inicial (por defecto 0)")
    ap.add_argument("--registro-extendido", action="store_true",
                    help="al final del CSV: val_<s> y val_total_<s> de todas las semillas, var_explicada, "
                         "frac_forzadas, msg_edad y ent_coef")
    ap.add_argument("--guardar-estado", action="store_true",
                    help="checkpoints/<tag>_epNNN.estado.pt en cada checkpoint, en el corte y al final")
    ap.add_argument("--reanudar", default=None, metavar="ESTADO|auto",
                    help="sigue exacto desde un estado; auto: el ultimo de esta etiqueta (sin estados, de cero)")
    ap.add_argument("--hasta-ep", type=int, default=None,
                    help="corta despues de este episodio: guarda el estado y sale con 0 sin publicar la politica")
    # plan3, Etapas 3 y 4 (todas apagadas por defecto)
    ap.add_argument("--obs-cercana", type=float, default=0.0,
                    help="M3: largo (m) de la zona cercana a la linea (E2 y giro a la izquierda); 0 = apagada")
    ap.add_argument("--norm-valor", action="store_true", help="M7: el critico aprende el retorno normalizado")
    ap.add_argument("--norm-beta", type=float, default=None,
                    help=f"beta de las medias moviles de --norm-valor (por defecto {BETA_NORM})")
    ap.add_argument("--sin-forzadas", action="store_true",
                    help="M7: las decisiones con una sola accion legal no entran al lote (exige descuento de V2)")
    ap.add_argument("--msg-cada-paso", action="store_true", help="M7: los mensajes se publican cada segundo")
    ap.add_argument("--ent-final", type=float, default=None,
                    help="entropia lineal de HIPER['ent'] a este valor en el horizonte de la tasa")
    ap.add_argument("--paso-decision", type=int, default=PASO_CONTROL,
                    help="reloj de decision (s) desde el verde minimo; 5 = el de siempre (otro exige descuento V2)")
    ap.add_argument("--escala-demanda", default=None, metavar="a,b",
                    help="politica por red: cada episodio corre con --scale f, f ~ U(a, tope)")
    ap.add_argument("--curriculo", type=int, default=0,
                    help="con --escala-demanda: episodios en que el tope sube de a a b (0 = tope b desde el 1)")
    ap.add_argument("--val-escalas", default=None, metavar="e1,e2,...",
                    help="valida en estos niveles de demanda (--scale); elige por la media geometrica")
    ap.add_argument("--validar-args", action="store_true",
                    help="solo revisa los argumentos y sale con 0 (no lee el escenario ni escribe nada)")
    return ap


def validar_args(argv):
    """Lee y revisa los argumentos de rl_ippo (argv sin el nombre del programa): parse_args y todos los ap.error, sin
    leer el escenario, sin tocar archivos y sin cambiar el estado del modulo (HIPER y C quedan iguales). Devuelve
    args, con los cambios de --hiper ya convertidos en args.cambios_hiper, o sale como argparse: SystemExit(2) con el
    motivo en stderr. chequeos_previos la llama en su proceso para cada comando de rl_ippo de la lista de trabajos,
    despues de con_escenarios.registrar() (asi --escenario acepta los escenarios del plan 3)."""
    ap = construir_parser()
    args = ap.parse_args(argv)
    if not re.fullmatch(r"[a-z0-9]*", args.etiqueta):
        ap.error("--etiqueta: solo minusculas y digitos")
    if args.modo == "demo" and not args.politica:
        ap.error("demo necesita --politica")
    if args.episodios < 1:
        ap.error("--episodios va desde 1")
    if args.eval_cada < 0:
        ap.error("--eval-cada va desde 0 (0 = nunca)")
    if not all(s.strip().lstrip("-").isdigit() for s in args.val_seeds.split(",") if s.strip()):
        ap.error("--val-seeds: enteros separados por coma")
    if args.v2 and (args.solo_descuento or args.solo_exploracion):
        ap.error("--v2 ya trae el descuento por segundo y la exploracion comun")
    if args.hasta_ep is not None and not 1 <= args.hasta_ep <= args.episodios:
        ap.error("--hasta-ep va de 1 a --episodios")
    if (args.hasta_ep is not None or args.reanudar == "auto") and not args.guardar_estado:
        ap.error("--hasta-ep y --reanudar auto necesitan --guardar-estado")
    if args.lr_horizonte is not None and args.lr_horizonte < 1:
        ap.error("--lr-horizonte va desde 1")
    if not 0.0 <= args.lr_piso < 1.0:
        ap.error("--lr-piso va de 0 a 1 (fraccion del lr inicial)")
    descuento_v2 = correcciones_v2(args)[0]
    if args.paso_decision < 1:
        ap.error("--paso-decision va desde 1")
    # las reglas del entrenamiento: en demo, la observacion, el reloj y los mensajes salen del meta de la politica
    if args.modo == "train" and args.sin_forzadas and not descuento_v2:
        ap.error("--sin-forzadas exige el descuento por segundo de V2 (--v2 o --solo-descuento)")
    if args.modo == "train" and args.paso_decision != PASO_CONTROL and not descuento_v2:
        ap.error("--paso-decision distinto de 5 exige el descuento por segundo de V2")
    if args.obs_cercana < 0:
        ap.error("--obs-cercana es un largo en metros (0 = apagada)")
    if args.norm_beta is not None and not (args.norm_valor and 0.0 < args.norm_beta < 1.0):
        ap.error("--norm-beta va con --norm-valor y entre 0 y 1")
    if args.ent_final is not None and args.ent_final < 0:
        ap.error("--ent-final es un coeficiente de entropia (>= 0)")

    def lista_escalas(texto, opcion):
        try:
            valores = [float(x) for x in texto.split(",") if x.strip()]
        except ValueError:
            ap.error(f"{opcion}: numeros separados por coma")
        if not valores or any(not ESCALA_MIN <= v <= ESCALA_MAX for v in valores):
            ap.error(f"{opcion}: factores de demanda entre {ESCALA_MIN:g} y {ESCALA_MAX:g}")
        return valores

    args.escalas_demanda = lista_escalas(args.escala_demanda, "--escala-demanda") if args.escala_demanda else None
    dem = args.escalas_demanda
    if dem and (len(dem) != 2 or dem[0] > dem[1]):
        ap.error("--escala-demanda: dos factores a,b con a <= b")
    if args.curriculo and (args.curriculo < 0 or not args.escalas_demanda):
        ap.error("--curriculo va con --escala-demanda y es un numero de episodios")
    args.escalas_val = lista_escalas(args.val_escalas, "--val-escalas") if args.val_escalas else None
    if args.escalas_val:
        sufijos = [sufijo_escala(e) for e in args.escalas_val]
        if len(set(sufijos)) != len(sufijos):
            ap.error(f"--val-escalas: niveles repetidos ({', '.join(s[2:] for s in sufijos)})")
        if args.eval_cada == 0 or not [s for s in args.val_seeds.split(",") if s.strip()]:
            ap.error("--val-escalas necesita validacion: --eval-cada > 0 y --val-seeds")
    if args.modo == "train":
        # Combinaciones que ningun trabajo del prerregistro usa (revision del 05.11): mejor un error que una corrida
        # que nadie va a leer. En demo mandan las opciones del meta (y un AVISO si la linea de comandos dice otra cosa).
        etapa3 = [o for o, activa in (("--obs-cercana", args.obs_cercana > 0), ("--norm-valor", args.norm_valor),
                                       ("--sin-forzadas", args.sin_forzadas), ("--msg-cada-paso", args.msg_cada_paso),
                                       ("--ent-final", args.ent_final is not None),
                                       ("--paso-decision", args.paso_decision != PASO_CONTROL)) if activa]
        if args.paso_decision != PASO_CONTROL and not args.sin_forzadas:
            ap.error("--paso-decision distinto de 5 va con --sin-forzadas (H14: antes del verde minimo las decisiones "
                     "son forzadas y no deben entrar al lote)")
        if args.obs_cercana and args.obs_insercion:
            ap.error("--obs-cercana no va con --obs-insercion (ningun trabajo del plan las junta)")
        if etapa3 and args.variante == "local":
            ap.error(f"{', '.join(etapa3)}: no van con --variante local (los trabajos de la Etapa 3 son de vecinos)")
        # B16: la politica por red usa --norm-valor (con su --norm-beta); el resto de la Etapa 3 no va con la escala
        otras = [o for o in etapa3 if o != "--norm-valor"]
        if otras and (args.escalas_demanda or args.escalas_val):
            ap.error(f"{', '.join(otras)}: no van con --escala-demanda ni --val-escalas (la politica por red, B16, "
                     "solo suma --norm-valor)")
    cambios = {}
    for cambio in [c for c in args.hiper.split(",") if c]:
        clave, igual, valor = cambio.partition("=")
        if clave not in HIPER or not igual:
            ap.error(f"--hiper: {cambio!r} (clave=valor con clave en {', '.join(HIPER)})")
        try:
            cambios[clave] = type(HIPER[clave])(float(valor)) if clave in ("epocas", "minibatch") else float(valor)
        except ValueError:
            ap.error(f"--hiper: {cambio!r} no es un numero")
    args.cambios_hiper = cambios
    return args


def abrir_csv(ruta_csv, texto):
    """Reescribe el CSV de entrenamiento con texto (cabecera y, al reanudar, las filas <= partida) y lo deja abierto
    para una fila por episodio. Si otro programa lo tiene tomado (Excel, antivirus) no se detiene: avisa y devuelve
    None; el tramo sigue con el CSV en memoria (el estado lo guarda) y escribir_csv lo intenta al final."""
    try:
        salida = open(ruta_csv, "w", newline="")          # se reescribe: la cola puede reintentar
    except PermissionError as e:
        print(f"AVISO: no se puede escribir {ruta_csv} ({e}); el tramo sigue con el CSV en memoria (el estado lo "
              "guarda) y lo escribe al terminar", flush=True)
        return None
    salida.write(texto)
    salida.flush()
    return salida


def escribir_csv(ruta_csv, texto, esperar):
    """El CSV entero (temporal, fsync y os.replace) cuando no se pudo abrir al empezar el tramo. En un tramo que no es
    el ultimo lo intenta una vez y, si sigue tomado, avisa: el estado lo guarda y el tramo siguiente lo reescribe. En
    el ultimo (esperar) reintenta cada ESPERA_CSV s, hasta INTENTOS_CSV veces, antes de publicar; si no puede, sale
    con el error (la cola reintenta los 'Permission denied' y el relanzamiento sigue desde el ultimo estado)."""
    def escribir(tmp):
        with open(tmp, "w", newline="") as f:
            f.write(texto)
    intentos = INTENTOS_CSV if esperar else 1
    for k in range(intentos):
        try:
            escribir_atomico(ruta_csv, escribir)
            print(f"{ruta_csv} escrito al final del tramo" + (f" (intento {k + 1})" if k else ""), flush=True)
            return
        except PermissionError as e:
            if not esperar:
                print(f"AVISO: {ruta_csv} sigue tomado ({e}); el estado guarda el CSV y el tramo siguiente lo "
                      "escribe", flush=True)
                return
            if k == intentos - 1:
                raise
            if k == 0:
                print(f"AVISO: {ruta_csv} sigue tomado ({e}); cierralo: se reintenta cada {ESPERA_CSV} s y la "
                      "politica se publica despues", flush=True)
            time.sleep(ESPERA_CSV)


def main():
    args = validar_args(sys.argv[1:])
    if args.validar_args:
        print(f"rl_ippo: argumentos validos ({args.modo} en {args.escenario})")
        return
    HIPER.update(args.cambios_hiper)

    preparar(args.escenario)
    configurar_obs_insercion(args.obs_insercion)
    configurar_obs_cercana(args.obs_cercana)
    C["msg_paso"], C["sin_forzadas"], C["paso_decision"] = args.msg_cada_paso, args.sin_forzadas, args.paso_decision
    C["vnorm"] = NormValor(args.norm_beta if args.norm_beta is not None else BETA_NORM) if args.norm_valor else None
    esc = args.escenario
    rng = sembrar(args.seed)

    if args.modo == "demo":
        politica, meta = Politica.cargar(args.politica)
        # la observacion, el reloj y los mensajes con que se entreno mandan; si la linea de comandos pedia otra cosa,
        # se avisa (no se juega con opciones distintas de las del entrenamiento)
        pedidas = {"obs_insercion": args.obs_insercion, "obs_cercana": float(args.obs_cercana or 0),
                   "paso_decision": args.paso_decision, "msg_cada_paso": args.msg_cada_paso}
        del_meta = {c: (meta.get("opciones", {}).get(c, d) if c != "obs_cercana"
                        else float(meta.get("opciones", {}).get(c, d) or 0)) for c, d in OPCIONES_QUE_ACTUAN.items()}
        distintas = [f"{c}={pedidas[c]!r} (meta: {del_meta[c]!r})" for c in OPCIONES_QUE_ACTUAN
                     if pedidas[c] != del_meta[c]]
        if distintas:
            print(f"AVISO: demo juega {args.politica} con las opciones de su meta; la linea de comandos pedia "
                  f"{'; '.join(distintas)}", flush=True)
        configurar_desde_meta(meta)
        C["sin_forzadas"], C["vnorm"] = False, None
        assert meta["dim_obs"] == C["dim_obs"], \
            f"la politica espera {meta['dim_obs']} entradas y {esc} da {C['dim_obs']}"
        variante = meta["variante"]
        serie = f"serie_{esc}_ippo_{variante}_s{args.seed}.csv" if args.serie else None
        res = correr_episodio("demo", politica, args.gui, args.delay, args.seed, serie=serie,
                              latencia=args.latencia, perdida=args.perdida, variante=variante)
        print(f"IPPO {variante} ({esc}):", res)
        return

    val_seeds = [int(s) for s in args.val_seeds.split(",") if s.strip()]
    politica = Politica(C["dim_obs"])
    opt = torch.optim.Adam(politica.parameters(), lr=HIPER["lr"], eps=1e-5)
    nombre_var = args.variante + (f"_{args.etiqueta}" if args.etiqueta else "")
    etiqueta = f"{esc}_ippo_{nombre_var}_s{args.seed}"
    ruta_csv = args.csv or f"resultados_{etiqueta}.csv"
    ruta = f"politica_{esc}_{nombre_var}_s{args.seed}.pt"
    descuento, exploracion = correcciones_v2(args)
    horizonte = args.lr_horizonte or args.episodios
    fin = args.hasta_ep or args.episodios           # ultimo episodio de esta llamada (un tramo si hay --hasta-ep)
    extra = ((["escala"] if args.escalas_demanda else [])
             + (["vn_media", "vn_desv"] if C["vnorm"] is not None else []))
    campos = campos_csv(val_seeds, args.registro_extendido, args.escalas_val, extra)
    meta = meta_base(args, val_seeds)
    codigo = huella_codigo()
    # --escala-demanda: generador propio del factor de cada episodio (no toca los demas)
    rng_escala = np.random.default_rng(args.seed + SEMILLA_ESCALA) if args.escalas_demanda else None
    # --reanudar: ruta explicita (misma etiqueta o nueva) o auto (el estado valido mas avanzado de esta etiqueta)
    ruta_estado, estado, como_auto = None, None, args.reanudar == "auto"
    if args.reanudar == "auto":
        ruta_estado, estado = ultimo_estado(etiqueta)
        if estado is None:
            print(f"--reanudar auto: {etiqueta} no tiene estados; empieza de cero")
    elif args.reanudar:
        ruta_estado, estado = args.reanudar, cargar_estado(args.reanudar)
    if estado is not None and estado["tag"] != etiqueta:
        # Etiqueta nueva ya empezada por un intento anterior de esta misma reanudacion (estados propios que salen
        # de este estado de origen): sigue desde el mas avanzado que sirva, como auto, en vez de copiar otra vez y
        # borrar. Si ninguno sirve (ultimo_estado aparta los danados), copia otra vez del origen.
        propio, mio = ultimo_estado(etiqueta)
        if mio is not None:
            salto = {"corrida": estado["tag"], "episodio": estado["episodio"]}
            if mio["tag"] == etiqueta and mio["episodio"] > estado["episodio"] and \
                    mio["origen"] == estado["origen"] + [salto]:
                print(f"{etiqueta} ya sigue a {os.path.basename(ruta_estado)}: continua desde {propio}")
                ruta_estado, estado, como_auto = propio, mio, True
    if estado is not None:
        comprobar_estado(estado, args, val_seeds, horizonte)
        k = estado["episodio"]
        if k > fin:                 # solo con --hasta-ep: un tramo posterior ya paso de aqui
            if not como_auto:
                raise SystemExit(f"--reanudar: el estado esta en el episodio {k}, despues de --hasta-ep {fin}")
            print(f"Nada que hacer: {ruta_estado} ya pasa del episodio {fin} (--hasta-ep)")
            return
        if k == fin and estado["tag"] == etiqueta and \
                (fin < args.episodios or ya_terminada(estado, etiqueta, ruta_csv, ruta, args.criterio_val)):
            print(f"Nada que hacer: {etiqueta} ya llego al episodio {k}"
                  + (f" (--hasta-ep {fin})" if fin < args.episodios else f" y publico {ruta}"))
            return
        corrida = reanudar(estado, ruta_estado, etiqueta, args, campos, meta, ruta_csv, politica, opt, rng,
                           rng_escala)
    else:
        limpiar_checkpoints(etiqueta)
        corrida = nueva_corrida(campos)
    corrida["codigo"] = codigo
    inicio = estado["episodio"] + 1 if estado is not None else 1
    val_serie, val_total_serie = corrida["val_serie"], corrida["val_total_serie"]
    tramo = {"desde": inicio, "hasta": inicio - 1, "git": meta["git"], "codigo": codigo}   # el de este proceso
    if inicio <= fin:
        corrida["tramos"].append(tramo)
    salida = abrir_csv(ruta_csv, "".join(corrida["lineas"]))   # cabecera (y, al reanudar, las filas <= partida)
    print(f"IPPO {nombre_var} en {esc}: {args.episodios} episodios, semilla base {args.seed}, "
          f"dim_obs {C['dim_obs']}, {sum(p.numel() for p in politica.parameters())} parametros"
          + (f", v2={descuento and exploracion} ins={args.recompensa_insercion}"
             if (descuento and exploracion) or args.recompensa_insercion else "")
          + (f", solo el {'descuento' if descuento else 'exploracion comun'} de V2"
             if descuento != exploracion else "")
          + (", obs_insercion" if C["obs_ins"] else ""))
    if opciones_etapas(args):
        print(f"Plan 3, Etapas 3 y 4: {opciones_etapas(args)}")
    if estado is not None:
        print(f"Reanuda desde {ruta_estado} (episodio {estado['episodio']}, "
              + ("misma etiqueta" if estado["tag"] == etiqueta else f"etiqueta nueva; copia lo de {estado['tag']}")
              + f"); sigue del {inicio} al {fin}", flush=True)
        # el HEAD cambia cada manana (se commitean estado y logs): se compara la huella del codigo, no el commit
        previo = estado.get("codigo")
        if previo is None and estado["git"] != meta["git"]:
            print(f"AVISO: el estado es del commit {estado['git']} (sin huella del codigo) y esta corrida corre en "
                  f"{meta['git']}")
        elif previo is not None and previo != codigo:
            print(f"AVISO: el estado se escribio con otro codigo (huella {previo[:12]}, commit {estado['git']}); "
                  f"esta corrida: huella {codigo[:12]}, commit {meta['git']}")
    for ep in range(inicio, fin + 1):
        tramo["hasta"] = ep
        lr = tasa(ep, horizonte, args.lr_piso)
        for g in opt.param_groups:
            g["lr"] = lr
        corrida["lr"].append(lr)
        # hiperparametros de este episodio: el coeficiente de entropia sigue --ent-final (si no, es el de HIPER)
        hiper_ep = (HIPER if args.ent_final is None
                    else {**HIPER, "ent": coef_entropia(ep, args.ent_final, horizonte)})
        corrida["ent"].append(hiper_ep["ent"])
        escala = None
        if args.escalas_demanda:            # --escala-demanda: factor del episodio (con curriculo, el tope sube)
            a_, b_ = args.escalas_demanda
            tope = b_ if not args.curriculo else a_ + (b_ - a_) * min(1.0, ep / args.curriculo)
            escala = round(float(rng_escala.uniform(a_, tope)), 4)
        buffer = {}
        t0 = time.time()
        res = correr_episodio("train", politica, args.gui, args.delay, args.seed + ep,
                              tripinfo=f"tripinfo_{etiqueta}_train.xml", variante=args.variante,
                              buffer=buffer, v2=exploracion, ins=args.recompensa_insercion, escala=escala)
        vacio = not any(b["recompensa"] for b in buffer.values())
        if args.registro_extendido:
            res["ent_coef"] = hiper_ep["ent"]
            if escala is not None:
                res["escala"] = escala
        if vacio:
            # ninguna transicion en el lote (p. ej. todas forzadas con --sin-forzadas): no hay que actualizar; las
            # columnas de la actualizacion quedan vacias y los generadores no se tocan
            print(f"AVISO: el episodio {ep} no dejo transiciones en el lote; no se actualiza la politica", flush=True)
            res.update({"dt_medio": "", "frac_dt8": ""})
            if args.registro_extendido:
                res["var_explicada"] = ""
            diag = dict.fromkeys(DIAG_PPO, "")
        else:
            lote = gae(buffer, HIPER["gamma"], HIPER["lam"], smdp=descuento)
            dts = np.concatenate([intervalos(b) for b in buffer.values() if b["recompensa"]])
            res.update({"dt_medio": round(float(dts.mean()), 3), "frac_dt8": round(float((dts == 8).mean()), 4)})
            if args.registro_extendido:
                res["var_explicada"] = varianza_explicada(buffer, lote[5])
            if C["vnorm"] is not None:
                # --norm-valor: las medias toman los retornos de este lote; el critico aprende el normalizado
                retornos = lote[5].numpy()
                C["vnorm"].actualizar(retornos)
                lote = lote[:5] + (torch.from_numpy(np.asarray(C["vnorm"].normalizar(retornos),
                                                               dtype=np.float32)),)
                if args.registro_extendido:
                    m, d = C["vnorm"].media_desv()
                    res.update({"vn_media": round(m, 4), "vn_desv": round(d, 4)})
            diag = actualizar(politica, opt, lote, hiper_ep, rng)
        fila = {"variante": args.variante, "base": args.seed, "episodio": ep, "semilla": args.seed + ep,
                "lr": f"{lr:.2e}", "segundos": round(time.time() - t0, 1), **res, **diag,
                "algoritmo": "ippo", "recompensa_tipo": meta["recompensa"], "etiqueta": args.etiqueta}
        checkpoint = bool(val_seeds and args.eval_cada and (ep % args.eval_cada == 0 or ep == args.episodios))
        if checkpoint:
            fila.update(validar(politica, val_seeds, args.variante, f"tripinfo_{etiqueta}_val.xml",
                                escalas=args.escalas_val))
            if args.escalas_val:        # una columna por nivel (media de sus semillas); la ultima, la geometrica
                xs = [sufijo_escala(e) for e in args.escalas_val]
                val_serie.append([ep] + [fila[f"val{x}"] for x in xs] + [fila["val"]])
                val_total_serie.append([ep] + [fila[f"val_total{x}"] for x in xs] + [fila["val_total"]])
            else:
                val_serie.append([ep] + [fila[f"val_{s}"] for s in val_seeds] + [fila["val"]])
                val_total_serie.append([ep] + [fila[f"val_total_{s}"] for s in val_seeds] + [fila["val_total"]])
            politica.guardar(ruta_checkpoint(etiqueta, ep),
                             meta_checkpoint(meta, ep, fila, val_seeds, args.escalas_val, corrida["tramos"]))
            if args.guardar_estado:         # despues del fsync de guardar: el sha256 es el de lo que esta en disco
                for ext in (".pt", ".json"):
                    corrida["archivos"][os.path.basename(ruta_checkpoint(etiqueta, ep, ext))] = \
                        sha256(ruta_checkpoint(etiqueta, ep, ext))
        linea = linea_csv(campos, fila)
        if salida is not None:
            salida.write(linea)
            salida.flush()
        corrida["lineas"].append(linea)
        if ep in corrida["previas"]:
            rehecho(corrida, ep, linea, etiqueta)
        print(f"Ep {ep:3d}  timeLoss={res['timeloss_prom']:6.2f}  espera={res['espera_prom']:5.2f}  "
              f"r/dec={res['recompensa_decision']:6.2f}  cambios={res['cambios_fase']:4d}  "
              + (f"kl={diag['kl_aprox']:.4f} ent={diag['entropia_libre']:.3f}" if not vacio else "sin lote")
              + f"  {fila['segundos']}s"
              + (f"  ins={res['ins_espera']}" if args.recompensa_insercion else "")
              + (f"  minor={res['expl_minoritaria']:.3f} dt={res['dt_medio']:.2f}"
                 if (descuento or exploracion) and not vacio else "")
              + (f"  val={fila['val']:.2f} total={fila['val_total']:.2f}" if "val" in fila else ""),
              flush=True)
        if args.guardar_estado and (checkpoint or ep == fin):
            guardar_estado(ruta_checkpoint(etiqueta, ep, ".estado.pt"), ep, etiqueta, args, val_seeds, corrida,
                           politica, opt, rng, ruta_csv, meta["git"], rng_escala)
    if salida is not None:
        salida.close()
    else:                           # el CSV estaba tomado al empezar: entero ahora (en el ultimo tramo, con esperas)
        escribir_csv(ruta_csv, "".join(corrida["lineas"]), esperar=fin == args.episodios)
    resumen_b22(corrida, etiqueta)
    if fin < args.episodios:
        print(f"CORTE: {fin} de {args.episodios} episodios; estado en "
              f"{ruta_checkpoint(etiqueta, fin, '.estado.pt')}. La politica se publica al llegar a --episodios.",
              flush=True)
        return

    distintos = procedencia(corrida["tramos"])
    if val_serie:
        # val_elegido queda en la metrica del criterio: con ella se elige la base mediana
        por_timeloss, por_total = elegir_checkpoint(val_serie), elegir_checkpoint(val_total_serie)
        elegida = por_total if args.criterio_val == "total" else por_timeloss
        eval_final = val_serie[-1][1]
        if args.escalas_val:
            # con niveles, val_serie trae medias por nivel: eval_999_final es la primera semilla en el nivel 1 del
            # ultimo checkpoint (como eval_timeloss), o None si no se valida en el nivel 1
            with open(ruta_checkpoint(etiqueta, val_serie[-1][0], ".json"), encoding="utf-8") as f:
                ultimo = json.load(f)
            nivel = 1.0 if any(float(e) == 1.0 for e in args.escalas_val) else None
            eval_final = ultimo.get(f"val_{val_seeds[0]}{sufijo_escala(1)}") if nivel else None
        meta.update({"ep_elegido": elegida[0], "val_elegido": elegida[-1], "val_serie": val_serie,
                     "eval_999_final": eval_final, "val_total_serie": val_total_serie,
                     "ep_elegido_timeloss": por_timeloss[0], "ep_elegido_total": por_total[0]})
        if args.escalas_val:
            meta["eval_nivel"] = nivel          # el nivel de demanda de eval_timeloss, eval_espera y eval_999_final
        if C["vnorm"] is not None:          # --norm-valor: la escala del critico del checkpoint publicado
            with open(ruta_checkpoint(etiqueta, elegida[0], ".json"), encoding="utf-8") as f:
                elegido = json.load(f)
            meta.update({c: elegido[c] for c in ("vn_media", "vn_desv", "vn_estado") if c in elegido})
        if distintos:
            meta["tramos"] = distintos
        if corrida["reanudaciones"]:
            meta["reanudaciones"] = corrida["reanudaciones"]
        # publicacion atomica: primero el .json y al final el .pt (la salida que mira la cola), cada uno en un
        # temporal bajado a disco y renombrado, con reintentos si estan tomados
        guardar_json(meta, ruta.replace(".pt", ".json"))
        copiar(ruta_checkpoint(etiqueta, elegida[0]), ruta)
    else:
        meta.update({"ep_elegido": args.episodios, "val_elegido": None, "val_serie": [],
                     "eval_999_final": None})
        if C["vnorm"] is not None:          # sin validacion se publican los pesos del final: su escala del critico
            media, desv = C["vnorm"].media_desv()
            meta.update({"vn_media": round(media, 4), "vn_desv": round(desv, 4), "vn_estado": C["vnorm"].estado()})
        if distintos:
            meta["tramos"] = distintos
        if corrida["reanudaciones"]:
            meta["reanudaciones"] = corrida["reanudaciones"]
        politica.guardar(ruta, meta)
    print(f"Politica guardada en {ruta} (episodio {meta['ep_elegido']}, val {meta['val_elegido']}, "
          f"criterio {args.criterio_val})")


if __name__ == "__main__":
    main()
