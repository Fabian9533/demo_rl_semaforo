"""
plan_ovalo.py - Reglas de las luces del semaforo unico del Ovalo Vasco (semaforo_S1), con la logica de lima/programa.py.

Es una copia recortada de nudo_ovalo/programas/programa_ovalo.py (revision del 17.11.2026, sha256 91d90c44c2e6d618),
sin lo que aqui no se usa (la variante con el semaforo E1 del puente y la escritura de las carpetas de nudo_ovalo). Lo
nuevo, del 18.11.2026, es lo que necesita el modelo de orden libre (rl_ippo.py --orden-libre):
  - letras_verde(k, despeje): el verde de un estado con los movimientos de CUALQUIER estado anterior todavia adentro
    (antes solo el anterior del plan);
  - rojo(k): el todo rojo despues de cualquier estado (en el plan va solo despues de los giros);
  - fases_libres(): todas las fases que puede mostrar el semaforo con el orden libre y en que caso va cada una;
  - cesiones_necesarias() mira las fases del plan y las del orden libre (la matriz de la red sirve para los dos).
Con el orden del plan las letras son exactamente las de la revision (lo comprueba armar_ovalo.py).

Correccion de carriles (18.11.2026, tarde; nudo_ovalo_estudio2). La red tiene un movimiento mas, Balboa hacia Larco,
por un tramo propio (B_ML) que llega a la union ML. Aqui solo se agrega como trata el semaforo ese giro en la union:
cede el paso a 28 de Julio hacia Larco (CEDEN) y es un ceda el paso en todas las fases (CEDA_EL_PASO: nunca tiene
prioridad y nadie le cede). Las reglas de los demas movimientos no cambian: con la disposicion de carriles anterior,
sin ese giro, este archivo da las mismas letras y la misma matriz (pruebas/correccion_carriles/regresion.py).

Uso suelto (desde lima/ovalo):  python plan_ovalo.py red/ovalo_estudio.net.xml    # imprime el plan y el orden libre

Reglas (las de lima/programa.py, mas las de adentro del ovalo):
- Mismo PLAN, mismo orden y mismas duraciones; 3 s de ambar tras cada verde y 34 s con todo en rojo antes de 28 de
  Julio y Balboa (en el plan, tras los giros).
- Cada movimiento cruza una linea de parada de afuera (su carril de entrada) y varias de adentro (las esquinas y las
  uniones de su camino). Un movimiento con verde tiene verde en todas.
- Dentro del ovalo, el que se cruza con el otro flujo en verde cede el paso (g): 28 de Julio hacia Reducto sur en SO
  (cruza a Balboa) y Balboa hacia Reducto norte en NE (cruza a 28 de Julio). Son los dos unicos cruces entre
  movimientos de un mismo estado.
- Nadie queda atrapado por un rojo interno: una linea interna no muestra rojo. Quien ya esta dentro sale primero:
    * en el ambar, las lineas internas del estado que termina siguen como en su verde;
    * en el estado siguiente (si no hay un todo rojo entre los dos), las lineas internas del estado que termino siguen
      con prioridad (G) y las del estado nuevo que se cruzan con ellas ceden (g);
    * en el todo rojo, las internas del estado que termino quedan apagadas con prioridad (O) y el resto apagadas (o);
    * una linea interna que no usa nadie con verde ni nadie que este saliendo queda apagada (o): cede el paso.
  "O" y "o" en el todo rojo, y no "G" o "g": asi el todo rojo no cuenta como verde para el agente
  (rl_corredor.fases_verdes) ni para el actuado de SUMO, que siguen viendo 3 estados verdes.
- La matriz de cada esquina (quien cede a quien) la completa armar_ovalo.ajustar_matriz con cesiones_necesarias: en
  cada fase, el enlace con g u o cede al que tiene G u O.
- interno=cede (el de este estudio): la segunda esquina no tiene semaforo propio; los dos giros pasan cuando hay hueco.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))        # lima/ovalo
LIMA = os.path.dirname(AQUI)                             # lima
for _carpeta in (LIMA, AQUI):
    if _carpeta not in sys.path:
        sys.path.insert(0, _carpeta)
import armar_ovalo as ao    # noqa: E402  (CAMINOS y CARRILES_ENTRADA)
import programa as pe       # noqa: E402  (lima/programa.py: PLAN, TRANSICION, ROJO_TOTAL, NO_VERDES)
from red_tls import RedTLS  # noqa: E402

TLS = "semaforo_S1"
ENTRADA = {"RN_S1": "RN", "RS_S1": "RS", "B_S1": "B", "J_S1": "J"}
SALIDA = {"S1_L": "L", "S1_J": "J", "S1_RN": "RN", "S1_RS": "RS"}
PARADAS_AFUERA = {"P_RN", "P_RS", "P_B", "P_J"}
# Los dos giros que cruzan al otro flujo de su mismo estado, y la esquina donde lo cruzan (su segunda esquina).
# 18.11.2026, correccion de carriles (nudo_ovalo_estudio2): se agrega Balboa hacia Larco, el movimiento 13, que tiene
# verde junto con Balboa y en la union ML se junta con 28 de Julio hacia Larco, que viene de frente: le cede el paso
# ahi (g), con la misma regla que los otros dos. Lo necesita la red: sin el, armar_ovalo.ajustar_matriz se detiene
# porque los dos enlaces chocan con prioridad en la union.
CEDEN = {("J", "RS"): "SO", ("B", "RN"): "NE", ("B", "L"): "ML"}
# Balboa hacia Larco llega a su union por un tramo propio (B_ML), fuera de los lados del ovalo: alli es un CEDA EL
# PASO. Su enlace en la union nunca tiene prioridad (g cuando Balboa tiene verde y mientras quedan vehiculos de ese
# verde; apagado, o, el resto) y nadie le cede a el: no cuenta como "el que sale" en letras_verde ni sale con prioridad
# en un todo rojo. Por que: con la regla general ("lo que entra cede a lo que sale" y "lo que sale conserva su letra"),
# en Reducto de frente, que en el plan sigue a 28 de Julio y Balboa, el enlace de B_ML y el de NO_ML_0 (28 de Julio y
# Reducto norte hacia Larco) quedaban los dos sin prioridad y cediendose uno al otro: cuando coincidian un vehiculo en
# cada uno se bloqueaban toda la fase (medido con el plan actual y la semilla de humo 424301: 1 episodio de 39 s con
# la demanda publicada y 2 de 38 s con la alta; pruebas/correccion_carriles/variante_cede_mutuo/). Los otros dos giros
# de CEDEN no tienen ese problema: su enlace de la segunda esquina lo usa tambien el estado que sigue en el plan. Solo
# cambia las letras del enlace de B_ML en la union; las de todos los demas quedan como si ese giro no existiera.
CEDA_EL_PASO = {("B", "L")}
INTERNOS = ("cede", "semaforo")
TRAS_EL_ROJO = "-"          # orden libre: "estado anterior" de un verde que sigue a un todo rojo (nadie quedo adentro)


# ---------------- movimientos y enlaces ----------------
def movimientos_de(mov_plan):
    """Movimientos (origen, destino) de un estado de PLAN: [(entrada, salidas o "*", salidas excluidas)]."""
    res = set()
    inv = {v: k for k, v in SALIDA.items()}
    for entrada, salidas, excluidas in mov_plan:
        o = ENTRADA[entrada]
        for (oo, d) in ao.CAMINOS:
            if oo == o and (salidas == "*" or inv[d] in salidas) and inv[d] not in excluidas:
                res.add((oo, d))
    return res


def enlaces_de(red, mov):
    """Indices de semaforo_S1 que usa un movimiento: siguiendo sus carriles por las conexiones de la red."""
    c = ao.CAMINOS[mov]
    carriles = [f"{c[0]}_{k}" for k in ao.CARRILES_ENTRADA[mov]]
    usados = set()
    for siguiente in c[1:]:
        nuevos = []
        for carril in carriles:
            for con in red.net.getLane(carril).getOutgoing():
                if con.getToLane().getEdge().getID() != siguiente:
                    continue
                if con.getTLSID() == TLS:
                    usados.add(con.getTLLinkIndex())
                nuevos.append(con.getToLane().getID())
        if not nuevos:
            raise SystemExit(f"{mov}: no hay conexion de {carriles} hacia {siguiente}")
        carriles = sorted(set(nuevos))
    return usados


class Plan:
    """Los estados del plan sobre una red: quien usa cada enlace y las letras de cada fase."""

    def __init__(self, ruta_red, interno="cede", plan=None):
        assert interno in INTERNOS
        self.red = RedTLS(ruta_red, TLS)
        self.interno = interno
        self.plan = plan or pe.PLAN
        self.estados = [movimientos_de(m) for _, _, m in self.plan]
        self.usos = {i: set() for i in range(self.red.n)}
        self.por_mov = {}
        for mov in ao.CAMINOS:
            self.por_mov[mov] = enlaces_de(self.red, mov)
            for i in self.por_mov[mov]:
                self.usos[i].add(mov)
        self.avisos = []
        self.cede_al_que_sale = set()       # (i, j): el enlace i, del estado que entra, cede al j, que sale

    def afuera(self, i):
        return self.red.nodo(i) in PARADAS_AFUERA

    def segunda_esquina(self, i, activos):
        """El enlace es el cruce de un giro de CEDEN con el otro flujo, y ese giro tiene verde."""
        return any(CEDEN.get(m) == self.red.nodo(i) for m in self.usos[i] & activos)

    def ceda_el_paso(self, i):
        """El enlace es la llegada a su union de un movimiento de CEDA_EL_PASO, y no lo usa nadie mas."""
        return (not self.afuera(i) and bool(self.usos[i]) and self.usos[i] <= CEDA_EL_PASO
                and all(CEDEN.get(m) == self.red.nodo(i) for m in self.usos[i]))

    def anterior(self, k):
        """Movimientos del estado anterior DEL PLAN que pueden seguir dentro del ovalo al empezar el estado k: los del
        estado que termina justo antes, si entre los dos no hay un todo rojo (tras un todo rojo de 34 s ya salieron)."""
        prev = (k - 1) % len(self.plan)
        return set() if pe.ROJO_TOTAL.get(prev) else self.estados[prev]

    def letras_verde(self, k, despeje=None, nombre=None):
        """Letras de un estado verde. Afuera: G o r. Adentro: G para los movimientos con verde; g para el giro que
        cruza al otro flujo de su estado (en la segunda esquina; r con interno=semaforo); para los del estado anterior
        que siguen adentro (despeje: quien ya esta dentro sale primero), la letra de su propio verde (G, o g en la
        segunda esquina de su giro), y entonces g para los del estado nuevo que se cruzan con ellos; o (apagada) para
        el resto. despeje: movimientos que pueden seguir adentro al empezar el verde; None = los del anterior del plan
        (anterior(k)), como en la revision.
        La letra propia del despeje en la segunda esquina (18.11.2026) solo aparece con el orden libre, en los giros
        justo despues de 28 de Julio y Balboa: en el orden del plan los dos enlaces de la segunda esquina tienen verde
        en el estado que sigue y las letras son exactamente las de la revision. Cada par "el que entra cede al que
        sale" queda en self.cede_al_que_sale, para la matriz (cesiones_necesarias)."""
        activos = self.estados[k]
        despeje = self.anterior(k) if despeje is None else despeje
        res = []
        for i in range(self.red.n):
            activo = self.usos[i] & activos
            if self.afuera(i):
                res.append("G" if activo else "r")
            elif not activo:
                if self.usos[i] & despeje:
                    res.append("g" if self.segunda_esquina(i, despeje) and self.interno == "cede" else "G")
                else:
                    res.append("o")
            elif self.segunda_esquina(i, activos):
                res.append("g" if self.interno == "cede" else "r")
            else:
                res.append("G")
        saliendo = [j for j in range(self.red.n) if not self.afuera(j) and not (self.usos[j] & activos)
                    and self.usos[j] & despeje and not self.ceda_el_paso(j)]       # un ceda el paso no "sale primero"
        for i in range(self.red.n):
            if res[i] in "Gg" and not self.afuera(i) and self.usos[i] & activos:
                cruza = [j for j in saliendo if self.red.choca(i, j)]
                if cruza:
                    res[i] = "g"
                    self.cede_al_que_sale.update((i, j) for j in cruza)
        self.revisar(res, nombre or f"estado {k + 1}")
        return "".join(res)

    def ambar(self, verde):
        """Ambar tras un verde: las luces de afuera que estaban en verde pasan a y; adentro sigue todo igual."""
        return "".join("y" if (self.afuera(i) and c == "G") else c for i, c in enumerate(verde))

    def rojo(self, k):
        """Todo rojo tras el estado k: afuera r; adentro, los del estado que termina salen con prioridad (O, apagada con
        prioridad: no cuenta como verde para el agente ni para el actuado) y el resto apagadas (o)."""
        res = "".join("r" if self.afuera(i) else
                      ("O" if self.usos[i] & self.estados[k] and not self.ceda_el_paso(i) else "o")
                      for i in range(self.red.n))
        self.revisar(res, f"todo en rojo tras el estado {k + 1}")
        return res

    def revisar(self, res, fase):
        """Aviso si dos enlaces con prioridad (G u O) chocan en la misma fase."""
        for i in range(self.red.n):
            for j in range(i + 1, self.red.n):
                if res[i] in "GO" and res[j] in "GO" and self.red.choca(i, j):
                    self.avisos.append(f"{fase}: {self.texto_enlace(i)} y {self.texto_enlace(j)} chocan con prioridad")

    def texto_enlace(self, i):
        e = self.red.enlaces[i]
        return f"{i} ({e['nodo']} {e['desde']}->{e['hacia']})"

    def fases(self, verdes):
        """[(duracion, estado, nombre)] como programa.fases: verde, ambar y, tras el estado con ROJO_TOTAL, todo rojo."""
        assert len(verdes) == len(self.plan)
        res = []
        for k, (nombre, _, _) in enumerate(self.plan):
            verde = self.letras_verde(k)
            res.append((verdes[k], verde, nombre))
            res.append((pe.TRANSICION, self.ambar(verde), "transicion"))
            if pe.ROJO_TOTAL.get(k):
                res.append((pe.ROJO_TOTAL[k], self.rojo(k), "todo en rojo"))
        return res

    # ---------------- orden libre ----------------
    def rojo_antes(self):
        """Segundos con todo en rojo antes del verde de cada estado (en el plan, ROJO_TOTAL va tras el estado k, es
        decir, antes del k + 1). El orden libre lo pone siempre antes de ese estado, venga de donde venga."""
        n = len(self.plan)
        res = [0] * n
        for k, segundos in pe.ROJO_TOTAL.items():
            res[(k + 1) % n] = segundos
        return res

    def previos(self, k):
        """Estados de los que se puede llegar al verde de k con el orden libre: cualquier otro, o TRAS_EL_ROJO si antes
        de k va el todo rojo (entonces nadie queda adentro)."""
        n = len(self.plan)
        return [TRAS_EL_ROJO] if self.rojo_antes()[k] else [j for j in range(n) if j != k]

    def previo_del_plan(self, k):
        n = len(self.plan)
        return TRAS_EL_ROJO if self.rojo_antes()[k] else (k - 1) % n

    def fases_libres(self):
        """Programa del orden libre: todas las fases que puede mostrar el semaforo cuando el modelo elige el estado que
        sigue, con las reglas de arriba. Devuelve (fases, verde, ambar, rojo):
          fases  [(nombre, letras)] en orden. Las n primeras son los verdes del plan, en su orden (en el orden del plan
                 las luces son las de hoy; rl_ippo.py lo comprueba al instalarlo);
          verde  [(k, previo, indice)]: verde del estado k cuando el estado anterior fue previo (TRAS_EL_ROJO si entre
                 los dos fue el todo rojo);
          ambar  [(k, previo, indice)]: ambar al terminar ese verde; es el mismo vaya hacia donde vaya (pasan a ambar
                 todas las luces de afuera que estaban en verde; ninguna luz de afuera sigue en verde en otro estado);
          rojo   [(k, indice)]: todo rojo al terminar el estado k (antes del estado que lleva todo rojo previo)."""
        n = len(self.plan)
        claves = [(k, self.previo_del_plan(k)) for k in range(n)]
        claves += [(k, p) for k in range(n) for p in self.previos(k) if p != self.previo_del_plan(k)]
        fases, verde, ambar = [], [], []
        letras = {}
        for k, p in claves:
            despeje = set() if p == TRAS_EL_ROJO else self.estados[p]
            nombre = f"{self.plan[k][0]} (antes: {self.nombre_previo(p)})"
            letras[(k, p)] = self.letras_verde(k, despeje, nombre)
            verde.append((k, p, len(fases)))
            fases.append((nombre, letras[(k, p)]))
        for k, p in claves:
            ambar.append((k, p, len(fases)))
            fases.append((f"ambar tras {self.plan[k][0]} (antes: {self.nombre_previo(p)})", self.ambar(letras[(k, p)])))
        rojo = []
        con_rojo = [j for j in range(n) if self.rojo_antes()[j]]
        for k in range(n):
            if any(j != k for j in con_rojo):
                rojo.append((k, len(fases)))
                fases.append((f"todo en rojo tras {self.plan[k][0]}", self.rojo(k)))
        return fases, verde, ambar, rojo

    def nombre_previo(self, p):
        return "todo en rojo" if p == TRAS_EL_ROJO else self.plan[p][0]

    def cesiones_necesarias(self):
        """Pares (i, j) de enlaces que chocan tales que en alguna fase i no tiene prioridad (g u o) y j si (G u O), mas
        los pares en que el que entra (g) cede al que sale (g en la segunda esquina de su giro): la matriz de su
        esquina debe decir que i cede a j. Se miran las fases del plan y las del orden libre (son las mismas letras
        para todos los controles; las duraciones no importan)."""
        estados = [e for _, e, _ in self.fases([v for _, v, _ in self.plan])]
        estados += [letras for _, letras in self.fases_libres()[0]]
        pares = set(self.cede_al_que_sale)
        for estado in estados:
            for i, ci in enumerate(estado):
                if ci not in "go":
                    continue
                for j, cj in enumerate(estado):
                    if cj in "GO" and self.red.choca(i, j):
                        pares.add((i, j))
        return pares


# ---------------- escritura de programas ----------------
def lineas_programa(plan, tipo, verdes, params, programa, comentario):
    """Lineas del <tlLogic> de semaforo_S1 (como programa.escribir). tipo: static (verdes = duraciones) o un actuado
    de SUMO (verdes = [(minimo, maximo)])."""
    lineas = [f"    <!-- {comentario} -->"] if comentario else []
    if tipo == "static":
        fases = plan.fases(verdes)
        lineas.append(f'    <tlLogic id="{TLS}" type="static" programID="{programa}" offset="0">')
        for dur, estado, nombre in fases:
            lineas.append(f'        <phase duration="{dur}" state="{estado}"/>  <!-- {nombre} -->')
    else:
        fases = plan.fases([mx for _, mx in verdes])
        lineas.append(f'    <tlLogic id="{TLS}" type="{tipo}" programID="{programa}" offset="0">')
        for clave, valor in params.items():
            lineas.append(f'        <param key="{clave}" value="{valor}"/>')
        # el actuado del estudio solo mira las 15 entradas: los carriles de adentro llevan un detector propio que no
        # cuenta a ningun vehiculo (vTypes de un tipo que no existe)
        for carril in carriles_internos(plan):
            lineas.append(f'        <param key="{carril}" value="nulo_{carril}"/>')
        k = 0
        for dur, estado, nombre in fases:
            if nombre in pe.NO_VERDES:
                lineas.append(f'        <phase duration="{dur}" state="{estado}"/>  <!-- {nombre} -->')
            else:
                mn, mx = verdes[k]
                k += 1
                lineas.append(f'        <phase duration="{mn}" minDur="{mn}" maxDur="{mx}" state="{estado}"/>  '
                              f'<!-- {nombre} -->')
    lineas.append("    </tlLogic>")
    return lineas


def carriles_internos(plan):
    """Carriles que llegan a una linea de parada de adentro (no son de las 15 entradas)."""
    return sorted({e["desde"] for i, e in plan.red.enlaces.items() if not plan.afuera(i)})


def detectores_nulos(plan):
    res = []
    for carril in carriles_internos(plan):
        largo = plan.red.net.getLane(carril).getLength()
        res.append(f'    <laneAreaDetector id="nulo_{carril}" lane="{carril}" pos="0" endPos="{largo:.2f}" '
                   f'vTypes="ninguno" period="100000" file="nul" friendlyPos="true"/>')
    return res


def escribir_add(ruta, lineas):
    tmp = f"{ruta}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write("<additional>\n" + "\n".join(lineas) + "\n</additional>\n")
    os.replace(tmp, ruta)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    plan = Plan(sys.argv[1])
    print("Plan actual:")
    for dur, estado, nombre in plan.fases([v for _, v, _ in pe.PLAN]):
        print(f"{dur:4d} s  {estado}  {nombre}")
    fases, verde, ambar, rojo = plan.fases_libres()
    print("\nOrden libre:")
    for k, (nombre, letras) in enumerate(fases):
        print(f"{k:3d}  {letras}  {nombre}")
    for mov, enl in sorted(plan.por_mov.items()):
        print(f"  {mov[0]}>{mov[1]}: enlaces {sorted(enl)}")
    for a in sorted(set(plan.avisos)):
        print("AVISO:", a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
