> Especificación con la que se dibujaron los diagramas (27.09.2026). Cada nodo y flecha lleva su evidencia `archivo:línea`; las rutas `scratchpad/...` eran archivos de trabajo que no se versionaron. Para regenerar las figuras: `cd TESIS/diagramas && python construir.py`.

# Especificación unificada de los diagramas de la tesis: arquitectura, U1, U2, U3 y U4

Fecha: 27.09.2026, revisada el mismo día (§7). Rama `reestructura-tesis`. Fuentes: las cinco
fichas de análisis (arquitectura, u1, u2, u3, u4), contrastadas con el código y el texto actual, y
dos críticas (fidelidad y claridad) verificadas punto por punto contra el código. Todas las cifras
y nombres de esta especificación tienen su evidencia `archivo:línea` en las tablas. Lo que no se
pudo verificar quedó fuera del dibujo o figura en §5 como duda.

- Estilo común (único archivo de diagramas creado en el repositorio, junto a `construir.py`):
  `TESIS/diagramas/estilo_diagramas.tex`. La revisión lo tocó (§7.3).
- Prueba del estilo: `scratchpad/diagramas/prueba_estilo.tex`, `.pdf`, `prueba_estilo-1.png`
  (color) y `prueba_gris-1.png` (blanco y negro), recompilados tras la revisión.
- Medición de anchos: `scratchpad/revision/medir.sh` compila `medir.tex`, que mide cada línea de
  `lineas.tex` con el estilo real y la compara con el ancho de su columna. Todas las líneas de §3
  pasaron por ahí.
- Compilación: `TESIS/diagramas/construir.py` compila `<nombre>.tex` para `arquitectura`, `u1`,
  `u2`, `u3` y `u4`, y copia cada PDF a `TESIS/images/diag_<nombre>.pdf`.

Rutas relativas: `demo_rl/` es `C:/Users/GAMER/Documents/demo_rl_semaforo/demo_rl`, y las
secciones de la tesis están en `demo_rl/TESIS/secciones/`.

---

## 0. Decisiones de diseño (resumen)

1. **Cinco figuras TikZ standalone**, dibujadas a 15 cm exactos de ancho, se incluyen a escala 1
   con `\includegraphics[width=\textwidth]{diag_<nombre>.pdf}`. La letra es `\footnotesize` (8 pt)
   y los títulos de unidad van en `\small` (9 pt). Alto máximo: 13 cm para la arquitectura y 20 cm
   para cada unidad.
2. **Ubicación: las cinco van en el Cap. III.**
   - La arquitectura va en `sec:vision-general`.
   - Cada figura de unidad abre su sección, justo después del párrafo que la presenta: U1 en
     `sec:escenarios`, U2 en `sec:formulacion`, U4 en `sec:u4` y U3 en `sec:u3`.
   - Por el orden de las secciones (capitulo3.tex:76, 147, 295, 530), la numeración queda
     arquitectura, U1, U2, U4, U3. Por eso ningún texto cita un rango «Figuras U1 a U4»: cada
     figura se cita por separado.
   - El Cap. IV las vuelve a citar en `sec:construccion`, `sec:bucle`, `sec:aprendices` y
     `sec:ejecucion`.

   Criterio: la arquitectura es el mapa y cada unidad lo amplía, así que las cinco se leen juntas
   en el capítulo del método. El Cap. IV las usa como referencia.
3. **Nombres de las unidades**: se toman de la introducción (introduccion.tex:37).
   - U1 · Preprocesamiento
   - U2 · Aprendizaje por refuerzo
   - U3 · Simulación y medición
   - U4 · Coordinación distribuida

   SUMO + TraCI es el entorno de U3. **Condición previa a integrar las figuras**: la Tabla
   tab:pipeline usa otros nombres (U2 «Entrenamiento», U3 «Medición», capitulo3.tex:55,57) y está
   en la misma página que la arquitectura. Hay que renombrar esas dos filas, con la aprobación del
   autor (D1).
4. **Hay ocho interfaces con número, I1 a I8** (catálogo en §2). Desde la revisión, **I6 son las
   métricas por corrida e I7 la política publicada**, para que la arquitectura se lea I3, I4, I6,
   I7, I8 de arriba abajo. El resumen estadístico que va de `consolidar.py` a `veredicto.py` es
   interno a U3 y no lleva número.
5. **U4 no se dibuja como un módulo aparte que dialoga con U2.** U4 son las variantes con mensajes
   (IPPO vecinos, IPPO *spill*) y MAPPO, y siguen el mismo ciclo de entrenamiento que U2. DQN, que
   es de U2, usa la observación con mensajes de U4 (I5). Así lo describen introduccion.tex:52-54 y
   el pie de tab:pipeline (capitulo3.tex:62-65).
6. **En la arquitectura, una barra gris común («aprendices de U2 y U4»)** reúne las interfaces que
   U2 y U4 comparten con U3: I3, I4, I6 e I7. Según tab:pipeline, las salidas de U4 son «las mismas
   que U2».
7. **Cada figura lleva una leyenda compacta**: la macro `\leyenda`, en dos filas y con las mismas
   palabras en las cinco figuras. Solo incluye los elementos que esa figura usa. U2 añade una
   tercera fila con la clave de las marcas T, D y P.
8. **U4 amplía un episodio de U2.** Lo que pasa entre episodios (validación, *checkpoint*, episodio
   k + 1 y publicación) se dibuja solo en U2. U4 lo remite con un puerto «Sigue el ciclo de U2».
   En U4, los pasos que vienen de U2 van en naranja y lo que añade U4 en violeta.
9. **Una interfaz puede ir citada en el detalle de un nodo en lugar de tener puerto**, cuando un
   puerto obligaría a cruzar flechas o a alargar la figura: I1, I3 e I4 en el nodo SUMO (U2, U3,
   U4); I5 en Observar e I6 en Cierre del episodio y en Validación (U2); I2 en el mensaje (U4).

---

## 1. Principios comunes

### 1.1 Formato y compilación

Preámbulo idéntico en los cinco archivos `TESIS/diagramas/<nombre>.tex`:

```latex
\documentclass[10pt,border=0pt]{standalone}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish]{babel}
\usepackage{tikz}
\input{estilo_diagramas}
\begin{document}
\begin{tikzpicture}[diagrama]
\unidad{u2}                                  % u1, u2, u3, u4 (arquitectura: ext)
\useasboundingbox (0,0) rectangle (15,-<alto>);
...
\leyenda{(0.1,-<y1>)}{...}                   % fila 1
\leyenda{(0.1,-<y2>)}{...}                   % fila 2, 6 mm más abajo
\end{tikzpicture}
\end{document}
```

- Las coordenadas van en cm, con el origen arriba a la izquierda y la y negativa hacia abajo.
  `\useasboundingbox` fija 15 cm exactos, así que el PDF sale a escala 1.
- Letra Computer Modern: T1 con cm-super (ya instalado; `pdffonts` da Type 1). La
  librería TikZ `babel` neutraliza los caracteres activos del español (`<`, `>`, `"`), y el
  estilo restablece el punto decimal en modo matemático (`\decimalpoint`), porque la tesis escribe
  `f = 2.0`.
- El estilo `diagrama` desactiva el corte de palabras con guion dentro de los nodos
  (`\hyphenpenalty=10000`): la prueba anterior partía «cru-da» y «veci-nos».
- **Un diagrama no lleva `\ref` ni `\cite`**: se compila aparte. Se escribe «U2», «Anexo D» o
  «Cap. V».
- Se compila con `cd TESIS/diagramas && python construir.py <nombre>`. El script informa el
  tamaño; el ancho debe dar 15.0 cm y la escala 1.00. La tesis incluye
  `images/diag_<nombre>.pdf`: `\graphicspath{{images/}}` ya está en main.tex:23.

### 1.2 Tipografía y tamaños

| Elemento | Tamaño | Forma |
|---|---|---|
| Texto de nodos, etiquetas de flecha, notas y leyenda | `\footnotesize` = 8 pt | `diagrama` lo fija |
| Título de una unidad («U2 · Aprendizaje por refuerzo») | `\small\bfseries` = 9 pt | estilo `titulo`, con el color de la unidad |
| Título de un subgrupo (etapa) | `\footnotesize\bfseries` | estilo `subtitulo` |
| Semillas | `\footnotesize\itshape` | estilo `semillas` |

- Está prohibido `\scriptsize`, `\tiny` y escalar el dibujo (`scale`, `\resizebox`). Si algo no
  cabe, se acorta el texto o se quita un nodo prescindible (cada figura dice cuál).
- El texto de un nodo se escribe como `\nodo{Etiqueta}{detalle}`: la etiqueta va en negrita y el
  detalle debajo. **Los saltos de línea de las tablas de §3 son los que se midieron**: cada línea
  cabe en el ancho de la columna «Ancho» (cm), que es el `text width` del nodo. El detalle ocupa
  de una a tres líneas; solo `tripinfo`, Lecturas TraCI, `consolidar.py` y la regla (U3) y el
  mensaje (U4) llevan más, porque son el contenido central de su figura.
- El título de una figura de unidad es solo el nombre de la unidad («U2 · Aprendizaje por
  refuerzo»); el alcance («un aprendiz y una base», «un episodio») va en el pie.
- Archivos, programas y funciones van en `\texttt`, sin tildes y con `\_`. El texto lleva tildes.
  Una ruta en `\texttt` no se corta sola: se parte a mano con `\\` o se da al nodo el ancho
  necesario.
- Los decimales van con punto (0.02, 2.0) y los miles con espacio fino (`10\,000`). Los rangos se
  escriben con `--` (2001--2003), los porcentajes con `\,\%` (IC95\,\%) y las semillas `$b + k$`
  en modo matemático.
- Vocabulario: «valor de validación» (no «val»), «control» (no «brazo»), «la más probable» (no
  «argmax»), «metadatos» (no «meta»), «avenida, transversal» (no «E–O, N–S»), «programa estático
  por omisión» (no «programa "0"»), «Iniciar» (no «Lanzar»). De las funciones de `comun.py` y de
  `correr_episodio` se nombra el archivo o `correr_episodio`, que es lo que nombra el texto
  (capitulo4.tex:446-450).

### 1.3 Color por unidad

El color dice a qué unidad pertenece un elemento, sea cual sea la figura. Así, SUMO + TraCI y los
nodos de U3 son siempre verdes o grises, y un nodo de U2 que aparece en U4 va en naranja.

| Unidad | Borde y título (`<u>b`) | Fondo del grupo (`<u>f`) | Fondo del subgrupo (`<u>s`) |
|---|---|---|---|
| U1 | `2F5597` azul | `EDF2FA` | `DCE6F5` |
| U2 | `A65A0B` naranja | `FDF3E7` | `F9E3CA` |
| U3 | `3A6E21` verde | `EEF6EA` | `DDEDD5` |
| U4 | `5E4A9A` violeta | `F2EFF9` | `E3DDF2` |
| ext (fuera de las unidades: resultados, puertos hacia varias unidades) | `404040` | `F2F2F2` | `E6E6E6` |

- **Blanco y negro**: los rellenos quedan en grises muy claros y los bordes en gris oscuro
  (comprobado en `prueba_gris-1.png`). La unidad se reconoce siempre por su título «Uk · ...»,
  nunca solo por el color.
- `\unidad{uN}` fija la unidad de la figura: los estilos sin argumento usan ese color. Para un
  elemento de otra unidad se pasa el argumento: `proceso=u3`, `puerto=u1`, `grupo=u4`.
- En U4, todo paso que existe igual en IPPO local (U2) va en naranja (`=u2`): iniciar, decidir,
  cerrar, elegir, aplicar, avanzar, fin, crítico local, trayectorias, GAE y PPO. Van en violeta
  solo el reloj de 5 s, el mensaje con su canal, la observación extendida y el crítico central.
  El término *spill* se marca con una marca violeta «*spill*» sobre los nodos naranja Cerrar y
  Avanzar.

### 1.4 Forma según el tipo de nodo

| Tipo | Estilo TikZ | Forma | Uso |
|---|---|---|---|
| proceso | `proceso[=u]` | rectángulo redondeado, blanco, borde de la unidad | paso, programa o función; también los agentes |
| archivo o dato | `archivo[=u]` | rectángulo con la esquina superior derecha cortada | archivo en disco o tabla de datos en el código |
| decisión | `decision[=u]` | rombo | pregunta «¿...?», salidas «sí»/«no» (más su contenido) |
| inicio o fin | `iniciofin[=u]` | estadio con el relleno de la unidad y borde grueso | comienzo del flujo de una unidad, su resultado final, «Resultados (Cap. V y Anexo A)» (`iniciofin=ext`) |
| entorno | `entorno` | rectángulo gris con doble borde | **solo** SUMO: «SUMO + TraCI» (en U2 y U4, «SUMO + TraCI (U3)»); en U1, «SUMO sin TraCI» |
| puerto de interfaz | `puerto=<otra u>` más `hacia izquierda`, `hacia abajo` o `hacia arriba` | flecha-etiqueta | entrada o salida de una interfaz en las figuras de unidad (§1.7) |
| semillas | `semillas` | píldora gris en cursiva | rango de semillas de SUMO de una etapa: «<etapa>: <semillas>» |
| nota | `nota` | texto sin marco | aclaración corta de una a dos líneas |
| previsto | `<tipo>, previsto` | borde punteado gris y texto gris | lo previsto que no se usa (OSM, `netedit`) |
| marca | `marca[=u]` | recuadro pequeño en negrita | aplicabilidad: T, D o P (arquitectura y U2); IPPO, MAPPO o *spill* (U4). Se centra sobre la esquina superior derecha del nodo (`at (n.north east)`, ancla `center`), mitad afuera, para no tapar el título |
| grupo / subgrupo | `grupo=u`, `subgrupo=u` (fondo, *background layer*, `fit`) | fondo del color de la unidad | unidad (nivel 1) y etapa (nivel 2); **nunca un tercer nivel** |
| bus | `bus` | barra gris | solo en la arquitectura: aprendices de U2 y U4 |

### 1.5 Estilo de flecha según el tipo

| Tipo | Estilo | Trazo | Cuándo |
|---|---|---|---|
| flujo | `flujo` | continuo, 0.6 pt | secuencia y datos **dentro** de una unidad |
| interfaz | `interfaz` | discontinuo, 0.6 pt | el dato pertenece a una interfaz I1–I8 del catálogo: entre unidades, de un nodo a un puerto o de un puerto a un nodo, y entre SUMO (U3) y un nodo de U2/U4 |
| repetición | `repeticion` | continuo, 1.2 pt | vuelta de un bucle: siguiente segundo, episodio k + 1, una corrida por semilla, ampliar el eje de verde |
| no usado | `no usado` | punteado gris | camino previsto que no se usa (el borde de los nodos `previsto` es igual) |
| (modificador) | `doble` | con punta en ambos extremos | solo I5 entre agente i y agente j en la arquitectura |

- **Nombre de cada interfaz**: cada interfaz que aparece en una figura lleva su nombre completo
  una vez, con `\itfn{n}` (una línea) o `\itfnn{n}` (el mismo nombre en dos líneas, para huecos
  estrechos), sea en una flecha, un puerto o el detalle de un nodo. En las demás apariciones va
  `\itf{n}`. Si el nombre no cabe en ningún lugar de la figura, va en el pie.
- Una flecha continua nunca lleva número de interfaz.
- Las etiquetas de flecha llevan `etiqueta` (fondo blanco). Sobre el fondo de un grupo se usa
  `etiqueta en grupo`, y si no cortan ningún trazo, `etiqueta sin fondo`.
- Varias flechas pueden juntarse en un punto antes de entrar a un nodo, como en los diagramas de
  flujo: es preferible a cruzar líneas. No se cruzan dos flechas salvo que sea inevitable (cada
  figura dice cuáles). Si pasa, la que cruza por encima lleva un corte blanco
  (`preaction={draw=white, line width=2.4pt}`).

### 1.6 Etiquetas compartidas: el mismo texto en todas las figuras

| Elemento | Texto exacto | Dónde |
|---|---|---|
| Unidades | `U1 · Preprocesamiento`, `U2 · Aprendizaje por refuerzo`, `U3 · Simulación y medición`, `U4 · Coordinación distribuida` | títulos de los grupos (y título de cada figura de unidad, sin nada más) |
| Entorno | `SUMO + TraCI` (arquitectura y U3); `SUMO + TraCI (U3)` (U2 y U4); `SUMO sin TraCI` (U1, barrido) | nodo `entorno` |
| Interfaces | `\itfn{1}` … `\itfn{8}` o `\itfnn{n}` (§2) | flechas, puertos y detalles |
| Semillas | `tuneo: 2001--2003`; `entrenamiento: $b + k$`; `validación: 999 y 1999`; `evaluación: 1001--1030` | píldoras (las bases 42, 2042 y 4042 van en los pies) |
| Nodos del bucle comunes a U2 y U4 | `Iniciar el episodio $k$`, `¿Decide el\\ agente $i$?`, `Cerrar la decisión anterior`, `Observar`, `Elegir: mantener o cambiar`, `Aplicar la acción`, `Avanzar 1 s`, `¿Red vacía o\\ 6000 pasos?` | la etiqueta y el orden son iguales en las dos; el detalle puede cambiar |
| Resultados | `Resultados` con el detalle `Cap.~V y Anexo~A` | arquitectura (nodo); U3 (puerto I8) |
| Marcas | T = tabulares (Q-learning, SARSA, `ql_colas`); D = DQN; P = IPPO (local, vecinos, *spill*) y MAPPO | arquitectura y U2 |

### 1.7 Puertos de interfaz (figuras de unidad)

- Un puerto es la entrada o la salida de una interfaz I1–I8 en la frontera de la unidad. Se dibuja
  **fuera del recuadro de la unidad, pegado a su borde**, y la flecha discontinua cruza el borde
  hasta el nodo que produce o consume el dato.
- Texto del puerto: el nombre (`\itfn{n}` o `\itfnn{n}`) y el sentido con la unidad del otro
  lado, siempre como **«desde Uk»** o **«hacia Uk»**; debajo, si hace falta, el contenido
  concreto para esa unidad.
- El color del puerto es el de la unidad del otro lado. Si del otro lado hay varias unidades, se
  usa `puerto=ext` (gris), el mismo gris de la barra «aprendices de U2 y U4» de la arquitectura.
- La punta apunta en el sentido del dato: a la derecha por defecto, `hacia izquierda`, y en los
  puertos de arriba o de abajo del recuadro `hacia abajo` o `hacia arriba`, con el texto
  horizontal. Así el puerto apunta igual que su flecha.
- Siempre que se pueda, el puerto va en el lado donde está la otra unidad en la arquitectura: U1
  arriba; U3 a la izquierda de U2 y U4 (y U2/U4 a la derecha de U3); U4 debajo de U2; los
  resultados abajo a la derecha. **Pesa más que las flechas sean cortas y no se crucen.**
- En U2 y U4, SUMO + TraCI (U3) va como nodo `entorno`, no como puerto. I1, I3 e I4 son las
  flechas discontinuas entre ese nodo y los nodos del bucle, y el detalle del nodo SUMO dice sus
  nombres completos.

### 1.8 Leyenda

- Va en cada figura, al pie, en dos filas generadas con `\leyenda{(0.1,y)}{claves}`, y encima una
  raya fina `black!30` de 15 cm.
- Las claves siguen este orden, y cada figura pone solo las que usa:

  ```
  fila 1: proceso, archivo, decision, iniciofin, entorno, semillas
  fila 2: puerto, flujo, interfaz, repeticion, previsto
  ```

  Probado: cada fila completa entra en 14.6 cm.
- Textos fijos:

  | Clave | Texto |
  |---|---|
  | proceso | proceso |
  | archivo | archivo o dato |
  | decision | decisión |
  | iniciofin | inicio o fin |
  | entorno | simulador SUMO |
  | semillas | semillas |
  | puerto | puerto de interfaz |
  | flujo | flujo |
  | interfaz | interfaz (I1–I8) |
  | repeticion | repetición |
  | previsto | previsto, no usado |

  «simulador SUMO» vale para el nodo con TraCI y para el de U1 sin TraCI.
- La clave `nousado`, la flecha punteada, no se usa: `previsto` cubre el mismo concepto.
- La leyenda ocupa 1.0 a 1.2 cm de alto, ya descontados en el presupuesto de cada figura.
- Marcas: en U2, una tercera fila de leyenda con el texto (14.45 cm medidos)
  `Marcas: T = tabulares (Q-learning, SARSA, \texttt{ql\_colas}) · D = DQN · P = IPPO y MAPPO · sin marca: todos`.
  En la arquitectura y en U4 las marcas se explican en el pie.

### 1.9 Regla de evidencia

- Cada nodo, número y flecha tiene evidencia en el código o en el texto actual: columna
  «Evidencia» de las tablas de §3.
- Quien dibuje no añade nada que no esté en esta especificación.
- Si al dibujar hay que acortar, se quita lo marcado como prescindible, nunca un dato del
  protocolo: semillas, 200 episodios, validación cada 10, 10–60 s, 5 s, 3 s.

---

## 2. Catálogo de interfaces (nombres exactos)

Las macros `\itf{n}` («**I3**»), `\itfn{n}` («**I3** observación y recompensa») e `\itfnn{n}`
(el mismo nombre en dos líneas) están en el estilo y garantizan que las cinco figuras usan el
mismo texto.

| Id | Nombre corto exacto | Contenido | Produce | Consume | Evidencia |
|---|---|---|---|---|---|
| I1 | escenario del caso | `<esc>.sumocfg` con red `.net.xml`, demanda `.rou.xml` y programa fijo `<esc>.add.xml`, más paso de 1 s y sin teletransporte. `preparar.py` lo copia a `plan2/`. El fijo tuneado lo instala `barrer_fijo.py --instalar`; el actuado `<esc>_actuado.add.xml` lo escribe `comun.py` al evaluar ese control | U1 | SUMO + TraCI (U3). Lo cargan, con la semilla de cada corrida, los entrenamientos de U2 y U4, `evaluar.py` para fijo, actuado y políticas, y `barrer_fijo.py` dentro de U1 | plan2/corredor.sumocfg:3-5,9,12; plan2/preparar.py:26-37; barrer_fijo.py:459-467; comun.py:113-142,294-304; rl_corredor.py:232-242; rl_ippo.py:449-456; introduccion.tex:37; capitulo3.tex:53 |
| I2 | aproximaciones, enlaces y vecinos | Por semáforo: aproximaciones O, E, N, S; enlaces entre cruces; vecinos por lado (vecino, enlace que llega y enlace que sale); flujos de extremo a extremo. Son tablas en el código: `rl_corredor.ESCENARIOS` (P1–P3), `rl_ippo.VECINOS`/`LADOS` y `escenarios_plan2.py` (P4, P5) | U1 | U2 (estado y recompensa por aproximación), U3 (lecturas TraCI: aproximaciones y enlaces; `tripinfo`: flujos de extremo a extremo), U4 (mensajes, ranuras de la observación, término *spill*) | rl_corredor.py:74-98,265-270,376; rl_ippo.py:103-127,458,665; escenarios_plan2.py:24-44,64-87; comun.py:71-83,180-200; capitulo3.tex:53,59 |
| I3 | observación y recompensa | Lecturas TraCI de cada paso de 1 s, casi todas por suscripción: detenidos, vehículos, espera y velocidad media por aproximación y detenidos por carril de los enlaces. El estado tabular, la recompensa de `ql_colas` y la fase se leen con llamadas directas al decidir. Con ellas cada agente arma su estado tabular o su observación continua y acumula la recompensa | U3 (SUMO + TraCI) | U2, U4 | rl_corredor.py:122-123,149-151,160-161,265-267,331-352; rl_ippo.py:219-241,346-380,412-427,605-619; comun.py:209-231; capitulo3.tex:196-199; introduccion.tex:37 |
| I4 | acción | Cada 5 s del verde propio, 0 mantener o 1 cambiar. Cambiar es ámbar de 3 s (`setPhase`/`setPhaseDuration`) y luego el otro verde. El verde dura de 10 a 60 s | U2, U4 | U3 (SUMO + TraCI) | rl_corredor.py:110-113,290-329,362-368; rl_ippo.py:548-603,630-636; capitulo3.tex:171-190 |
| I5 | mensajes entre vecinos | Cada 5 s de reloj global, de cada semáforo j a cada vecino i: fase (avenida, transversal o ámbar), tiempo en ella, vehículos que descargan hacia i (0 si su verde no va hacia i), cola detenida en esa aproximación y cola detenida en el enlace j → i. El canal tiene latencia y pérdida, ambas 0 en todo el plan. El receptor guarda el último mensaje y su edad | U4 (semáforo j) | U4 (observación de i en IPPO vecinos, IPPO *spill* y MAPPO); U2 (DQN usa la misma observación) | rl_ippo.py:284-338,534-546,360-379,445; rl_dqn.py:4-8,68; plan2/generar_trabajos.py:33-41 (sin `--latencia`); capitulo3.tex:316-336; introduccion.tex:54 |
| I6 | métricas por corrida | Mismas columnas para todo control: retraso (`timeloss_prom`, primaria), espera, cola media y máxima, paradas, *throughput*, CO₂, NOₓ, no terminados, *spillback*, métricas de corredor y retornos `ret_retraso`, `ret_colas`, `ret_spill`. Las del `tripinfo` las calcula `comun.leer_tripinfo`; las colas y los retornos, `correr_episodio`; el *spillback*, `comun.MedidorEnlaces` | U3 (medición) | U2 y U4 (`resultados_<tag>.csv`; valor de validación = retraso medio con 999 y 1999) y `evaluar.py` (una fila por semilla, interno a U3) | comun.py:35-84,180-240; rl_corredor.py:331-346,372-390,397-404,436-476; rl_ippo.py:605-620,640-682,753-770; evaluar.py:66-79,283-290; plan2/ESPEC.md:121-135 |
| I7 | política publicada | Por (modelo, caso, base), el *checkpoint* de menor validación (en empate, el más tardío). Tabulares: `q_table_<tag>.json` + `.meta.json`. Redes: `politica_<esc>_<var>_s<b>.pt` + `.json`. Los metadatos llevan `ep_elegido`, `val_elegido` y `val_serie` | U2, U4 | U3: `evaluar.py` (la política) y `veredicto.py` (los metadatos, para la base publicada y la convergencia) | rl_corredor.py:479-500; rl_ippo.py:902-913; rl_dqn.py:323-333; rl_mappo.py:267-281; plan2/generar_trabajos.py:87-94; evaluar.py:183-252; veredicto.py:9-13,123-128,215-233 |
| I8 | veredicto | `veredicto.csv`, `veredicto.md` y `TESIS/secciones/tablas/veredicto_matriz.tex`, `veredicto_<modelo>.tex`, `veredicto_bases.tex`. Cada celda (caso, modelo) queda en FUNCIONA, MEJORA, EMPATA, FALLA o PENDIENTE, o en «= vecinos» para IPPO *spill* en P3–P5 | U3 (`veredicto.py`) | Resultados: Cap. V y Anexo A (`\input` de las tablas) | veredicto.py:15-20,454-462,719-729; tablas/veredicto_matriz.tex:18; capitulo3.tex:837-838; capitulo5.tex:46,190-192; anexos.tex:32,46-47,57-58,81-82 |

**Flujos internos sin número** (flecha `flujo`, nunca `interfaz`):

- U3: la fila por semilla que va de la medición a `evaluar.py`,
  `parciales/eval_<esc>_<control>.csv` de `evaluar.py` a `consolidar.py`, y
  `evaluacion_<esc>_resumen.csv` de `consolidar.py` a `veredicto.py`.
- U1: todos los archivos intermedios.
- U2: *checkpoints* y registro.
- En U2, el término *spill* y el crítico central de MAPPO son aportes de U4 al ciclo común. Van
  como texto «(U4)» en el detalle de los nodos Cerrar y PPO, no como interfaz.

**Semillas** (Tabla tab:plan2-semillas, capitulo3.tex:700-719):

| Etapa | Semillas | Píldora | Dónde se dibuja |
|---|---|---|---|
| Tuneo | 2001–2003 | `tuneo: 2001--2003` | U1 (calibración de f, barrido); arquitectura (U1, con «(calibración de $f$ y barrido del fijo)») |
| Entrenamiento | b + k, k = 1…200, con b = 42, 2042 o 4042 | `entrenamiento: $b + k$` | U2; arquitectura (U2). Las bases van en los pies |
| Validación | 999 y 1999 | `validación: 999 y 1999` | U2; arquitectura (U2) |
| Evaluación | 1001–1030 | `evaluación: 1001--1030` | U3 (en la fila del subtítulo «Evaluación»); arquitectura (U3) |

**Matriz de puertos**: cada flecha I de la arquitectura tiene su puerto, su flecha o su cita en la
figura de cada unidad que la produce o la consume.

| Interfaz | Arquitectura (flecha) | U1 | U2 | U3 | U4 |
|---|---|---|---|---|---|
| I1 | colector bajo red, demanda y programas de referencia → SUMO + TraCI | puerto de salida hacia U3 (abajo), desde Fijo tuneado y Actuado | flecha Iniciar → SUMO («\itf{1}»); nombre en el nodo SUMO | puerto de entrada → SUMO (a la derecha); nombre en el nodo SUMO; citado en Controles evaluados | igual que U2 |
| I2 | Aproximaciones… → barra de aprendices; ramal al borde de U3 | puerto de salida hacia U2, U3 y U4 (abajo), desde la tabla | puerto de entrada (arriba) → Trabajo de entrenamiento | puerto de entrada → Lecturas TraCI (a la derecha); citado en `tripinfo` (flujos de extremo a extremo) | citado en el mensaje (vecinos y enlaces); nombre en el pie |
| I3 | SUMO + TraCI → barra | — | flechas SUMO → Observar y → Avanzar 1 s; nombre en el nodo SUMO | puerto de salida (a la derecha); nombre en el nodo SUMO | igual que U2 |
| I4 | barra → SUMO + TraCI | — | flecha Aplicar → SUMO; nombre en el nodo SUMO | puerto de entrada (a la derecha); nombre en el nodo SUMO | igual que U2 |
| I5 | agente j ⇄ agente i (dentro de U4); agente i → «Redes neuronales» de U2 con la etiqueta «\itf{5} (DQN)» | — | citado en Observar (D y variantes de U4) | — | nodo del mensaje → Observar |
| I6 | Medición → barra | — | citado en Cierre del episodio y en Validación | puerto de salida desde Métricas de la corrida (el flujo Métricas → `evaluar.py` es interno y va sin número) | — (dentro del ciclo de U2) |
| I7 | barra → `evaluar.py`; barra → `veredicto.py` («\itf{7} (metadatos)») | — | puerto de salida (arriba) desde Publicar | dos puertos de entrada: → Controles evaluados; (metadatos) → Base publicada | en el puerto «Sigue el ciclo de U2» |
| I8 | `veredicto.py` → Resultados | — | — | puerto de salida desde Tablas de veredicto | — |

---

## 3. Especificación de cada figura

La columna «Ancho» es el `text width` del nodo en cm. Las líneas de «Texto exacto» están medidas
con el estilo real (ver el encabezado); ninguna pasa de su ancho.

### 3.1 Arquitectura modular (`arquitectura.tex` → `images/diag_arquitectura.pdf`, `fig:arquitectura`)

**Propósito.** Mostrar al jurado y al asesor, en una sola figura, las cuatro unidades y sus
componentes con el programa que implementa cada uno, cómo se conectan con SUMO + TraCI y con la
cadena de evaluación, qué información intercambian (I1–I8) y dónde entra cada rango de semillas.
Deja claro que el cruce de Lima es un camino previsto que no se usa. Es el índice de las cuatro
figuras de unidad.

**Ubicación.**
- capitulo3.tex, `sec:vision-general`: la figura va después del párrafo del cruce de Lima (termina
  en la línea 42) y antes de la Tabla tab:pipeline (línea 44).
- Se borran el TODO de capitulo3.tex:71 y el de capitulo2.tex:14-18.

**Frase que la cita.** Reemplaza la de capitulo3.tex:31-32 («La Tabla~\ref{tab:pipeline} resume
qué hace cada unidad...»):
> La Figura~\ref{fig:arquitectura} muestra cómo se conectan las cuatro unidades con SUMO y con la
> cadena de evaluación y qué información intercambian (interfaces I1 a I8); la
> Tabla~\ref{tab:pipeline} resume qué hace cada unidad, qué recibe, qué entrega y con qué programas
> se implementa.

**Párrafo obligatorio** que define las interfaces, justo después de la figura (hoy ninguna sección
nombra I1–I8):
> Las interfaces entre unidades son ocho: I1, el escenario del caso (la configuración de SUMO con la
> red, la demanda y los programas de referencia); I2, las aproximaciones, los enlaces y los vecinos
> de cada semáforo; I3, la observación y la recompensa, que cada agente arma con las lecturas de
> TraCI; I4, la acción de cada agente; I5, los mensajes entre semáforos vecinos; I6, las métricas
> de cada corrida; I7, la política publicada de cada entrenamiento con su archivo de metadatos, e
> I8, el veredicto por caso y modelo.

Opcional: cerrar introduccion.tex:37 con «(Figura~\ref{fig:arquitectura})».

**Nivel de detalle.**
- Sí van: un nodo por componente, con su programa; las interfaces con número; las semillas por
  etapa; las marcas T, D y P; el camino previsto de OSM.
- Quedan fuera:
  - En U1, la geometría y la demanda de cada caso, `preparar.py` y los archivos intermedios.
  - En U2, el reloj de decisión, la máscara, el ámbar, la fórmula de la recompensa, los
    hiperparámetros y el protocolo de 200 episodios, validación cada 10 y *checkpoint* (van en el
    pie y en U2).
  - En U4, la composición de la observación y la frecuencia de los mensajes (van en U4).
  - En U3, la lista de métricas y la estadística.
  - La cola de trabajos (`generar_trabajos.py`, `cola.py`), que es mecánica de ejecución.
  - La fase exploratoria (`cruce`, `cruce2`, `rl_semaforo.py`).
  - `tablas_cap5.py` y `grafico_convergencia.py`.

**Tamaño objetivo:** 15 × 12.8 cm; como máximo 13.0 cm (presupuesto abajo, sin holgura: el
prescindible es la etiqueta «cada 5 s», que pasa al pie).

**Nodos**

| Id | Estilo | Ancho | Texto exacto | Evidencia |
|---|---|---|---|---|
| osm | `proceso, previsto` (una línea) | — | `\textbf{Cruce real de Lima (OSM)}: importación cruda del 01.12.2025, no usada en P1--P5 (Anexo~D)` | anexo_d_osm.tex:8-19; capitulo3.tex:38-42 |
| U1 | `grupo=u1`, `titulo=u1` | — | `U1 · Preprocesamiento` | introduccion.tex:37 |
| s_tuneo | `semillas` | — | `tuneo: 2001--2003 (calibración de $f$ y barrido del fijo)` | capitulo3.tex:708,721-728 |
| red | `proceso=u1` | 3.2 | `\nodo{Red vial}{\texttt{.nod.xml}, \texttt{.edg.xml}\\ \texttt{netconvert} $\to$ \texttt{.net.xml}}` | build_net.bat:5-8; capitulo4.tex:60-98 |
| dem | `proceso=u1` | 3.2 | `\nodo{Demanda}{\texttt{<flow>} $\to$ \texttt{.rou.xml}\\ escalada en P2 y P4}` | capitulo3.tex:84-97; corredor_alta.rou.xml:2-3; plan2/red_alta.rou.xml:2-3 |
| ref | `proceso=u1` | 3.2 | `\nodo{Programas\\ de referencia}{fijo: \texttt{barrer\_fijo.py}\\ actuado: \texttt{comun.py}}` | barrer_fijo.py:1-32; comun.py:113-142; capitulo4.tex:358-434 |
| tab | `archivo=u1` | 3.2 | `\nodo{Aproximaciones,\\ enlaces y vecinos}{de cada semáforo}` | capitulo3.tex:53; rl_corredor.py:74-98; rl_ippo.py:103-127; escenarios_plan2.py:24-44 |
| U3 | `grupo=u3`, `titulo=u3` | — | `U3 · Simulación y medición` | introduccion.tex:37 |
| sumo | `entorno` | 4.6 | `\nodo{SUMO + TraCI}{SUMO 1.25.0; paso de 1 s;\\ 1 h de demanda y vaciado\\ (máx. 6000 pasos)}` | capitulo4.tex:38,508-513; plan2/corredor.sumocfg:9; rl_corredor.py:284 |
| med | `proceso=u3` | 4.65 | `\nodo{Medición por corrida}{\texttt{tripinfo} y TraCI cada segundo\\ (\texttt{comun.py} y \texttt{correr\_episodio})}` | comun.py:35-84,180-240; rl_corredor.py:331-346,376-389; rl_ippo.py:605-620,665-681; capitulo4.tex:446-450; capitulo3.tex:529-619 |
| eva | `proceso=u3` | 4.65 | `\nodo{\texttt{evaluar.py}}{cada control, política congelada}` | evaluar.py:1-26,255-295 |
| s_eval | `semillas` | — | `evaluación: 1001--1030` | capitulo3.tex:713,730-735; plan2/generar_trabajos.py:21 |
| con | `proceso=u3` | 4.65 | `\nodo{\texttt{consolidar.py}}{media e IC95\,\%; $\Delta$ frente\\ al fijo y al actuado}` | consolidar.py:1-31 |
| ver | `proceso=u3` | 4.65 | `\nodo{\texttt{veredicto.py}}{base publicada, convergencia\\ y regla}` | veredicto.py:1-35 |
| bus | `bus` (0.4 × ~6.6 cm) con el texto girado 90° `aprendices de U2 y U4` | — | — | capitulo3.tex:59 («las mismas que U2») |
| U2 | `grupo=u2`, `titulo=u2` | — | `U2 · Aprendizaje por refuerzo` | introduccion.tex:37,52 |
| tabu | `proceso=u2` + `marca=u2` «T» | 3.05 | `\nodo{Tabulares}{\texttt{rl\_corredor.py}:\\ Q-learning, SARSA\\ y \texttt{ql\_colas}}` | rl_corredor.py:1-40; plan2/generar_trabajos.py:26-32 |
| redes | `proceso=u2` + `marca=u2` «D, P» | 3.05 | `\nodo{Redes neuronales}{IPPO local:\\ \texttt{rl\_ippo.py}\\ DQN: \texttt{rl\_dqn.py}}` | capitulo3.tex:55; introduccion.tex:52; rl_dqn.py:1-10; plan2/generar_trabajos.py:33-40 |
| s_ent | `semillas` | — | `entrenamiento: $b + k$` | capitulo3.tex:676-678,709-710 |
| s_val | `semillas` | — | `validación: 999 y 1999` | capitulo3.tex:680-683,711 |
| U4 | `grupo=u4`, `titulo=u4` | — | `U4 · Coordinación distribuida` | introduccion.tex:37,54 |
| l_i5 | `nota` (dos líneas, a la izquierda de aj) | — | `\itfnn{5}` | rl_ippo.py:324-338,534-546; capitulo3.tex:316-336 |
| aj, ai | `proceso=u4` | — | `agente $j$` y `agente $i$` | rl_ippo.py:534-546 |
| var | `proceso=u4` + `marca=u4` «P» | 6.4 | `\nodo{Variantes con mensajes}{\texttt{rl\_ippo.py}: vecinos (observación extendida)\\ y \textit{spill} (+ término de \textit{spillback})\\ \texttt{rl\_mappo.py}: MAPPO (+ crítico central)}` | capitulo3.tex:59,402-413; rl_ippo.py:10-15,166-187,417-427; rl_mappo.py:1-8; plan2/generar_trabajos.py:33-42 |
| res | `iniciofin=ext` | 5.9 | `\nodo{Resultados}{Cap.~V y Anexo~A: matriz caso $\times$ modelo;\\ tablas por modelo y por base}` | veredicto.py:15-20; capitulo5.tex:46,190-192; anexos.tex:32-82 |

**Aristas**

| Desde → hacia | Estilo | Etiqueta | Evidencia |
|---|---|---|---|
| osm → red | `no usado` | — | anexo_d_osm.tex:8-19 |
| red, dem y ref → colector (y ≈ −2.95) → sumo (baja por x ≈ 4.8) | `interfaz` | `\itfn{1}`, a la izquierda del tramo vertical | introduccion.tex:37; plan2/corredor.sumocfg:3-5; comun.py:113-142 |
| tab → baja por x ≈ 13.0 hasta y ≈ −3.3 → a la izquierda → barra (entra por arriba en x ≈ 7.8) | `interfaz` | `\itfn{2}`, sobre el tramo horizontal, entre x 8.2 y 13.0 | rl_corredor.py:74-98; rl_ippo.py:166-187 |
| la misma línea sigue a la izquierda → borde superior de U3 (x ≈ 5.2) | `interfaz` | — | comun.py:71-83,188-200; rl_corredor.py:270,376 (la medición usa los enlaces y los flujos de extremo a extremo) |
| sumo → barra | `interfaz` | `\itfnn{3}` | introduccion.tex:37; rl_ippo.py:605-619 |
| barra → sumo | `interfaz` | `\itfn{4}` | rl_corredor.py:319-329; rl_ippo.py:583-603 |
| sumo → med | `flujo` | — | rl_corredor.py:232-234,331-337 |
| med → barra | `interfaz` | `\itfnn{6}` | rl_corredor.py:450-469; rl_ippo.py:753-770 |
| med → eva | `flujo` | `una fila por semilla` | evaluar.py:277-289 |
| barra → eva | `interfaz` | `\itfnn{7}` | plan2/generar_trabajos.py:87-94; evaluar.py:183-252 |
| prolongación de la barra → ver | `interfaz` | `\itf{7} (metadatos)`, **encima** de su flecha | veredicto.py:9-13,215-233 |
| eva → sumo (por el margen izquierdo) | `repeticion` | — (el pie lo explica) | evaluar.py:173-180,277-283 |
| eva → con | `flujo` | `parciales por control` | evaluar.py:266-295; consolidar.py:49-60 |
| con → ver | `flujo` | `resumen` | consolidar.py:8-15; veredicto.py:10 |
| ver → res | `interfaz` | `\itfn{8}`, **debajo** de su flecha | veredicto.py:719-729 |
| aj ⇄ ai | `interfaz, doble` | `cada 5 s`, debajo de la flecha; el nombre lo da l_i5 | rl_ippo.py:534-546,367-379 |
| ai → redes (sube por x ≈ 14.55, entra por abajo de redes) | `interfaz` | `\itf{5} (DQN)`, a la izquierda del tramo, encima de ai | rl_dqn.py:4-8,68; capitulo3.tex:62-65 |

**Disposición** (coordenadas aproximadas, en cm):
- y 0 a −0.45: `osm`, arriba a la izquierda, en una línea.
- **U1**, x 0–15, y −0.6 a −2.8: el título arriba a la izquierda y `s_tuneo` arriba a la derecha.
  Cuatro nodos de 3.45 cm de ancho, con la parte superior en y −1.1 y x = 0.15 / 3.85 / 7.55 /
  11.25, **en este orden: red, dem, ref, tab**. El más alto (ref, cuatro líneas) mide 1.55 cm.
- Pasillo, y −2.8 a −3.55:
  - I1: tramos cortos desde el pie de red, dem y ref se juntan en un colector discontinuo en
    y ≈ −2.95 (x 1.9 a 9.3); de ahí I1 baja por x ≈ 4.8 hasta el borde superior de U3. La
    etiqueta va a la izquierda del tramo vertical (x 2.0–4.7).
  - I2: baja desde el pie de tab por x ≈ 13.0 hasta y ≈ −3.3 y va a la izquierda hasta x 5.2,
    donde baja al borde superior de U3. En x ≈ 7.8 sale un ramal hacia la barra. La etiqueta va
    sobre el tramo horizontal, entre x 8.2 y 13.0.
  - Así no se cruzan: el colector de I1 termina en y −2.95 y la horizontal de I2 va en y −3.3; I1
    baja en x 4.8 e I2 termina en x 5.2.
  - El título de U3 ocupa x 0.1–4.5, así que las flechas entran a la derecha del título.
- **U3**, x 0–5.6, y −3.55 a −11.5: una columna de 4.9 cm de ancho en x 0.45–5.35, con sumo
  (−4.05), med, eva (`s_eval` en su esquina inferior derecha), con y ver. La repetición eva → sumo
  va por el margen izquierdo, en x ≈ 0.2.
- Hueco de etiquetas, x 5.35–7.6, de arriba abajo: I3 (dos líneas), I4, I6 (dos líneas), I7 (dos
  líneas), «\itf{7} (metadatos)» encima de su flecha e I8 debajo de la suya. Las dos flechas de
  abajo van separadas 0.5 cm.
- **Barra**: x 7.6–8.0, y −3.55 a −10.3. Una línea la prolonga hasta la flecha de los metadatos.
- **U2**, x 8.1–15, y −3.55 a −7.1:
  - tabu en x 8.25–11.45 y redes en x 11.65–14.85, con la parte superior en y −4.2 (las marcas
    quedan bajo el título de U2).
  - Debajo, a la izquierda, `s_ent` (y ≈ −6.0) y `s_val` (y ≈ −6.5), una sobre otra, en
    x 8.3–11.6.
  - Se deja libre la franja x > 14.3 para la flecha I5 (DQN).
- **U4**, x 8.1–15, y −7.4 a −10.45:
  - Fila 1 (y ≈ −8.0 a −8.7): l_i5 en x 8.3–10.0; aj en x 10.2–11.4; la flecha doble hasta ai en
    x 13.35–14.75, con «cada 5 s» debajo. La etiqueta «\itf{5} (DQN)» va encima de ai, a la
    izquierda de la flecha que sube.
  - Fila 2 (y ≈ −8.85 a −10.35): var, a todo el ancho (x 8.25–14.85).
- **res**: x 8.4–15, y −10.7 a −11.4.
- **Leyenda**: raya en y −11.6; filas en y −11.95 y −12.55. Fila 1: `proceso, archivo, iniciofin,
  entorno, semillas`. Fila 2: `flujo, interfaz, repeticion, previsto`.
- Prescindible si falta alto: la etiqueta «cada 5 s» (pasa al pie).

**Pie de figura (borrador)**
```latex
\caption[Arquitectura modular del método]{Arquitectura modular del método. Cada recuadro de color
es una unidad, con sus componentes y los programas que los implementan. SUMO + TraCI (gris, doble
borde) es el entorno de U3: sobre él entrenan los aprendices de U2 y U4 y se evalúan todos los
controles. Las flechas discontinuas son las interfaces I1 a I8 entre unidades; la barra gris
reúne a los aprendices de U2 y U4, que intercambian con U3 las mismas interfaces, y DQN (U2) usa
la observación con los mensajes de U4 (I5). La flecha gruesa indica que \texttt{evaluar.py} corre
una simulación por semilla. Cada aprendiz se entrena 200 episodios en cada base (42, 2042 y
4042), con la semilla $b + k$ en el episodio $k$; se valida cada 10 episodios y publica el
\textit{checkpoint} de menor validación. Las píldoras en cursiva son las semillas de SUMO de cada
etapa (Tabla~\ref{tab:plan2-semillas}). Marcas: T, tabulares; D, DQN; P, IPPO y MAPPO. En
punteado gris, el cruce real de Lima, previsto y no usado en P1 a P5 (Anexo~D). En las figuras de
cada unidad, el color del borde indica la unidad a la que pertenece cada elemento y los puertos
llevan el color de la unidad del otro lado de la interfaz. U1 se amplía en la
Figura~\ref{fig:flujo-u1}; U2, en la Figura~\ref{fig:flujo-u2}; U3, en la
Figura~\ref{fig:flujo-u3}, y U4, en la Figura~\ref{fig:flujo-u4}.}
\label{fig:arquitectura}
```

---

### 3.2 Flujo de U1 (`u1.tex` → `images/diag_u1.pdf`, `fig:flujo-u1`)

**Propósito.** Mostrar cómo se construye un escenario del plan (P1–P5) y qué entrega U1 a las demás
unidades: el orden real de los pasos, los archivos y programas, y las dos decisiones reales (caso
de estrés, ganador en el borde de un eje de verde). Explica por qué P2 y P4 comparten la red de P1
y P3 y por qué el cruce de Lima no entra en ningún caso. Sus tres subgrupos son los tres nodos de
U1 de la arquitectura (Red vial, Demanda, Programas de referencia); el cuarto, la tabla de
aproximaciones, enlaces y vecinos, es un nodo suelto.

**Ubicación.** capitulo3.tex, `sec:escenarios`, después del primer párrafo (termina en la
línea 88).

**Frase que la cita**, al final de ese párrafo:
> La Figura~\ref{fig:flujo-u1} resume cómo se construye cada escenario: de los archivos de nodos,
> vías y flujos a la red, la demanda, los programas de referencia y la tabla de aproximaciones,
> enlaces y vecinos de cada semáforo, y qué entrega U1 a las demás unidades.

Segunda cita, en capitulo4.tex:53-58 (apertura de `sec:construccion`), al final de «Esta sección
recorre esos archivos...»: «(el flujo completo está en la Figura~\ref{fig:flujo-u1})».

**Nivel de detalle.**
- Sí van: etapas a nivel de archivo (`.nod.xml`/`.edg.xml`, `.net.xml`, `.rou.xml`, `.add.xml`,
  `.sumocfg`, `<esc>_actuado.add.xml`); el programa de cada paso; los parámetros que definen el
  método (2001–2003, f = 2.0 y 1.2, 34 de 38 plazas, la regla de la rotonda, 10–60 s, desfase 0
  del actuado, piso de 10 s y techo de 60 s del barrido, tres esquemas en malla3).
- Quedan fuera:
  - Los flujos de cada caso (tab:escenarios).
  - Las mallas barridas, los ganadores y los desfases (tab:plan2-fijo).
  - La tabla de calibración (tab:red-alta-factor).
  - Las cadenas de estado de las fases y la detección de la fase de avenida.
  - La cola de trabajos (`prep_<esc>`, `barrido_<esc>`, `eval_<esc>_actuado`), las opciones
    `--procesos` y `--tmp` y las banderas `listo/*.ok`: son mecánica de ejecución, como en la
    arquitectura. La dependencia real del entrenamiento (D4) se corrige en el texto.
  - `cruce`/`cruce2` (fase exploratoria).
  - La lectura de la demanda que hace `veredicto.py`.
  - `randomTrips` (solo sirve para inspeccionar la red OSM, anexo_d_osm.tex:104-115).
- Un solo diagrama cubre los cinco casos. Las diferencias entre casos van en las etiquetas.

**Tamaño objetivo:** 15 × 17.4 cm (máximo 20).

**Nodos**

| Id | Estilo | Ancho | Texto exacto | Evidencia |
|---|---|---|---|---|
| osm | `proceso, previsto` | 3.0 | `\nodo{Cruce real de Lima\\ (OSM)}{importación cruda,\\ 01.12.2025}` | anexo_d_osm.tex:14-19 |
| netedit | `proceso, previsto` | 2.7 | `\nodo{Limpieza\\ en \texttt{netedit}}{prevista,\\ no ejecutada}` | anexo_d_osm.tex:17-19,84-102 |
| caso | `iniciofin` | 4.4 | `\nodo{Caso del plan (P1--P5)}{geometría, carriles,\\ semáforos y demanda}` | capitulo3.tex:76-128; plan2/ESPEC.md:30-44 |
| nodvia | `archivo` | 3.6 | `\nodo{Nodos y vías}{\texttt{.nod.xml}, \texttt{.edg.xml},\\ escritos a mano}` | capitulo3.tex:79-81; capitulo4.tex:59-80 |
| netconv | `proceso` | 3.6 | `\nodo{\texttt{netconvert}}{\texttt{build\_net.bat}}` | build_net.bat:5-8 |
| net | `archivo` | 3.6 | `\nodo{Red (\texttt{.net.xml})}{programa estático\\ por omisión; ámbar de 3 s}` | capitulo4.tex:91-98; build_net.bat:7 |
| n_red | `nota` | — | `P2 y P4 usan la red\\ de P1 y P3` | corredor_alta.sumocfg:3; red_alta.sumocfg:3; capitulo3.tex:83-85 |
| flujos | `proceso` | 4.6 | `\nodo{Flujos por movimiento\\ y periodo}{\texttt{<flow ... vehsPerHour>};\\ punta invertida a los 1800 s}` | corredor.rou.xml:4-26 (periodos 0–1800 y 1800–3600); capitulo3.tex:89-98 |
| rou | `archivo` | 4.6 | `\nodo{Demanda nominal (\texttt{.rou.xml})}{llegadas equiespaciadas}` | capitulo3.tex:93-95; capitulo4.tex:173-183 |
| estres | `decision` | — | `¿Caso de\\ estrés?` | capitulo3.tex:80-86 |
| calibrar | `proceso` | 4.6 | `\nodo{Calibrar el factor $f$\\ con el actuado}{P2: cola $\geq$ 34 de 38 plazas;\\ P4: sin saturar la rotonda}` | capitulo4.tex:240-303; comun.py:21-22,170-177 |
| s_tun1 | `semillas` | — | `tuneo: 2001--2003` | capitulo4.tex:242-244 |
| rou_alta | `archivo` | 4.6 | `\nodo{Demanda escalada (\texttt{.rou.xml})}{P2: $f = 2.0$; P4: $f = 1.2$}` | corredor_alta.rou.xml:2-3; plan2/red_alta.rou.xml:2-3 |
| tabla | `archivo` | 4.6 | `\nodo{Aproximaciones, enlaces\\ y vecinos}{por semáforo; flujos de extremo\\ a extremo; en \texttt{rl\_corredor.py},\\ \texttt{rl\_ippo.py}, \texttt{escenarios\_plan2.py}}` | rl_corredor.py:74-98; rl_ippo.py:103-127; escenarios_plan2.py:24-44,64-87 |
| cfg | `archivo` | 4.6 | `\nodo{Configuración (\texttt{.sumocfg})}{red, demanda y fijo de partida;\\ paso de 1 s; sin teletransporte;\\ \texttt{preparar.py} la copia a \texttt{plan2/}}` | corredor.sumocfg:3-5,9,12 (igual en los cinco); demo_rl/corredor.add.xml:2-6; plan2/preparar.py:1-44 |
| barrido | `proceso` | 4.4 | `\nodo{Barrido (\texttt{barrer\_fijo.py})}{reescribe el fijo de partida:\\ verde de avenida $\times$ transversal\\ $\times$ desfase (P5: tres esquemas)}` | barrer_fijo.py:1-33; plan2/preparar.py:6-8; capitulo4.tex:358-372 |
| sumo0 | `entorno` | 4.0 | `\nodo{SUMO sin TraCI}{una corrida por configuración\\ y semilla}` | barrer_fijo.py:17,82-100; capitulo4.tex:361-364 |
| s_tun2 | `semillas` | — | `tuneo: 2001--2003` | plan2/generar_trabajos.py:74 |
| borde | `decision` | — | `¿Ganador en el borde\\ de un eje de verde?` | barrer_fijo.py:27-30,326-348,435-445; capitulo3.tex:723-725 |
| n_piso | `nota` | 3.3 | `el verde mínimo de 10 s\\ cuenta como piso válido` | barrer_fijo.py:28-30,326-329; capitulo4.tex:373-376 |
| fijo | `archivo` | 4.4 | `\nodo{Fijo tuneado\\ (\texttt{plan2/<esc>.add.xml})}{\texttt{-{}-instalar}; registro en\\ \texttt{barrido\_<esc>.csv}}` | barrer_fijo.py:31-32,447-467; capitulo4.tex:376-379 |
| act_f | `proceso` | 3.9 | `\nodo{Programa actuado}{\texttt{comun.py}, al evaluar\\ el actuado (\texttt{evaluar.py})}` | plan2/generar_trabajos.py:78-81; evaluar.py:80,173-180; rl_corredor.py:235-237; comun.py:113-142; capitulo4.tex:423-434 |
| act | `archivo` | 3.9 | `\nodo{Actuado\\ (\texttt{<esc>\_actuado.add.xml})}{fases del programa\\ por omisión; verde 10--60 s;\\ desfase 0}` | comun.py:118-138; capitulo4.tex:91-96,426-432 |
| P_I1 | `puerto=u3, hacia abajo` | 6.8 | `\itfn{1} hacia U3\\ \texttt{plan2/<esc>.sumocfg} con el fijo tuneado; actuado` | §2 (I1) |
| P_I2 | `puerto=ext, hacia abajo` | 5.0 | `\itfn{2}\\ hacia U2, U3 y U4` | §2 (I2) |

**Aristas**

| Desde → hacia | Estilo | Etiqueta | Evidencia |
|---|---|---|---|
| osm → netedit | `no usado` | — | anexo_d_osm.tex:84-99 |
| netedit → net | `no usado` | `no usado (Anexo D)` | anexo_d_osm.tex:8-12,101-102 |
| caso → nodvia | `flujo` | `red` | capitulo4.tex:59-66 |
| caso → flujos | `flujo` | `demanda` | capitulo3.tex:89-98 |
| caso → tabla | `flujo` | `semáforos\\ y vecinos` | capitulo3.tex:53; rl_ippo.py:103-127 |
| nodvia → netconv → net | `flujo` | — | build_net.bat:5-8 |
| flujos → rou → estres | `flujo` | — | corredor.rou.xml:4-26 |
| estres → calibrar | `flujo` | `sí: P2, P4` | capitulo4.tex:240-248 |
| net → calibrar | `flujo` | — (el título dice «con el actuado») | corredor_alta.rou.xml:2-3; red_alta.sumocfg:3 |
| calibrar → rou_alta | `flujo` | `$f$` | plan2/red_alta.rou.xml:2-12 |
| estres → cfg | `flujo` | `no: P1, P3, P5` (se une a rou_alta → cfg en un punto) | corredor.sumocfg:4; red.sumocfg:4; malla3.sumocfg:4 |
| rou_alta → cfg | `flujo` | — | corredor_alta.sumocfg:4; red_alta.sumocfg:4 |
| net → cfg | `flujo` | — (tronco por el margen izquierdo, compartido con net → act_f) | corredor.sumocfg:3 |
| cfg → barrido | `flujo` | — | plan2/preparar.py:26-37; plan2/generar_trabajos.py:72-75 |
| barrido → sumo0 | `repeticion` | — (el detalle de sumo0 lo dice) | barrer_fijo.py:82-93,395-408 |
| sumo0 → barrido | `flujo` | `retraso medio` | barrer_fijo.py:87,95-100 |
| barrido → borde | `flujo` | `menor retraso` | barrer_fijo.py:435-436 |
| borde → barrido | `repeticion` | `sí: se amplía el eje` | barrer_fijo.py:332-348,437-445 |
| borde → fijo | `flujo` | `no, o techo de 60 s` | barrer_fijo.py:30,340-344,437-444,459-467 |
| net → act_f | `flujo` | — (el detalle de act dice «fases del programa por omisión») | comun.py:118-127 |
| act_f → act | `flujo` | — | comun.py:120-142 |
| fijo → P_I1 | `interfaz` | — | plan2/generar_trabajos.py:78-81 |
| act → P_I1 | `interfaz` | — | evaluar.py:173-180 |
| tabla → P_I2 (por el margen derecho, x ≈ 14.85) | `interfaz` | — | rl_corredor.py:74-98; rl_ippo.py:166-185 |

**Agrupaciones.**
- Recuadro `grupo=u1`, «U1 · Preprocesamiento».
- Subgrupo «Red vial»: nodvia, netconv, net y n_red.
- Subgrupo «Demanda»: flujos, rou, estres, calibrar, s_tun1 y rou_alta.
- Subgrupo «Programas de referencia»: barrido, sumo0, s_tun2, borde, n_piso, fijo, act_f y act.
- Sueltos dentro del recuadro: caso, tabla y cfg.
- osm y netedit quedan fuera del recuadro, como en la arquitectura; P_I1 y P_I2, abajo, fuera.

**Disposición** (15 × ~17.4 cm):
- **Franja superior**, fuera del recuadro, y 0 a −0.85: osm ⋯> netedit, arriba a la izquierda
  (x 0–3.2 y 3.7–6.6). La flecha punteada netedit ⋯> net baja por x ≈ 4.45, entre Red vial y
  Demanda, y entra a net por el este, en su mitad superior.
- **Recuadro U1**, x 0–15, y −1.0 a −15.0. caso arriba al centro (x 5.2–9.8, y −1.25 a −2.0).
- **Banda superior**, y −2.35 a −9.8:
  - «Red vial», x 0.3–4.3: nodvia, netconv, net y n_red debajo de net, a la izquierda.
  - «Demanda», x 4.6–9.6: flujos, rou, estres, calibrar, s_tun1 (debajo de calibrar, a la
    derecha de la flecha calibrar → rou_alta, que baja por la izquierda) y rou_alta.
  - Columna derecha, x 9.9–14.6, sin subgrupo: tabla arriba (desde y −2.6) y cfg abajo
    (y ≈ −8.0 a −9.3).
  - Rutas:
    - net → calibrar sale de net por el sur (x ≈ 3.8), baja hasta la altura de calibrar y entra
      por su oeste.
    - net → cfg y net → act_f comparten un tronco: salen de net por el oeste, bajan por el margen
      izquierdo (x ≈ 0.2) y en y ≈ −10.0 se separan: una rama va a la derecha, por debajo de
      Demanda, y sube a cfg por su borde inferior (x ≈ 10.5); la otra sigue bajando hasta act_f.
    - estres «no» sale por el este y baja por x ≈ 9.75 hasta el oeste de cfg; rou_alta → cfg se
      une a esa línea.
    - caso → tabla sale de caso por el este.
- **Banda inferior**, subgrupo «Programas de referencia», x 0.3–14.6, y −10.2 a −14.8:
  - Columna izquierda, x 0.5–4.6: act_f y act.
  - Columna central, x 5.0–9.6: barrido, borde y fijo.
  - Derecha, x 10.0–14.5: sumo0 con s_tun2 debajo, y n_piso junto a borde.
  - cfg → barrido sale de cfg por abajo (x ≈ 12.0), baja a y ≈ −10.0 y entra a barrido por
    arriba; no toca la rama net → cfg, que entra a cfg en x 10.5.
  - borde «sí» vuelve a barrido por el oeste (x ≈ 4.85); borde «no, o techo de 60 s» baja a fijo.
- **Fuera, abajo**, y −15.2 a −16.1: P_I1 en x 0.5–7.8, alimentado por act (vertical) y fijo
  (vertical); P_I2 en x 9.0–14.9, alimentado por tabla por el margen derecho (x ≈ 14.85).
- **Leyenda**: y −16.5 y −17.1. Fila 1: `proceso, archivo, decision, iniciofin, entorno,
  semillas`. Fila 2: `puerto, flujo, interfaz, repeticion, previsto`.
- Prescindibles si falta sitio, en este orden: n_piso, n_red (pasa al pie) y la tercera línea de
  cfg.

**Pie de figura (borrador)**
```latex
\caption[Flujo de U1: preprocesamiento]{Flujo de U1 para un caso del plan. Red vial: nodos y vías
escritos a mano, convertidos con \texttt{netconvert}. Demanda: flujos por movimiento y periodo; en
los casos de estrés (primer rombo) se escalan por el factor $f$, calibrado con el actuado. La
configuración de SUMO reúne la red, la demanda y el fijo de partida, y \texttt{preparar.py} la
copia a \texttt{plan2/}. Programas de referencia: el barrido corre SUMO sin TraCI por
configuración y semilla y, si el ganador queda en el borde de un eje de verde (segundo rombo),
amplía ese eje hasta que el ganador quede dentro o se llegue a 60~s; el actuado lo escribe
\texttt{comun.py} al evaluar ese control. U1 entrega a U3 el escenario del caso (I1) y a U2, U3 y
U4 las aproximaciones, enlaces y vecinos de cada semáforo (I2). En punteado gris, el cruce real
de Lima, previsto y no usado (Anexo~D).}
\label{fig:flujo-u1}
```

---

### 3.3 Flujo de U2 (`u2.tex` → `images/diag_u2.pdf`, `fig:flujo-u2`)

**Propósito.** Mostrar cómo entrena U2 a un aprendiz con una base b sobre SUMO a través de TraCI,
y cómo elige la política que entrega a U3. Muestra en un solo dibujo qué es común a todos los
aprendices y qué cambia entre tabulares (T), DQN (D) e IPPO/MAPPO (P). Las variantes de U4 siguen
este mismo ciclo. Reemplaza a U2.png.

**Ubicación.** capitulo3.tex, `sec:formulacion`, después del párrafo de apertura (termina en la
línea 157) y antes de «Agentes, decisiones y restricciones de verde».

**Frase que la cita**, al final de ese párrafo:
> La Figura~\ref{fig:flujo-u2} muestra cómo se encadenan estos elementos en el entrenamiento de un
> aprendiz con una base: el bucle de un segundo, la decisión de cada agente con lo que cambia entre
> algoritmos, la validación con \textit{checkpoint} y la publicación de la política
> (Sección~\ref{sec:protocolo}).

Segunda cita, en capitulo4.tex:445-451 (apertura de `sec:bucle`), al final del párrafo:
«La Figura~\ref{fig:flujo-u2} resume el ciclo completo.» Se borra el TODO de capitulo4.tex:575.

**Nivel de detalle.**
- Sí van:
  - Un trabajo de la cola: un aprendiz y una base.
  - El arranque de SUMO con la semilla del episodio.
  - El bucle de 1 s con la decisión de un agente i.
  - Los pasos que siguen a cada episodio y la publicación.
  - Las diferencias entre algoritmos, marcadas con T, D o P en el detalle de cada nodo. La marca
    recuadrada `P` va solo en el nodo exclusivo de P.
  - Solo los números que definen el flujo: 5 s, 10–60 s, ámbar de 3 s, 6000 pasos, 999 y 1999,
    N = 200, cada 10 y 0.02.
- Quedan fuera:
  - El contenido de los mensajes, el canal y las ranuras (van en U4).
  - Fórmulas de métricas y retornos (van en U3).
  - La recompensa heredada a reloj fijo de 5 s.
  - Las series por minuto.
  - Los hiperparámetros: factor de ε, tramos lineales, tasa inicial, minilotes, épocas, memoria y
    red objetivo de DQN (tab:plan2-hiper). Los de PPO van en U4.
  - La cola, la prueba de humo y la evaluación con 1001–1030.

**Tamaño objetivo:** 15 × 19.4 cm (máximo 20).

**Nodos**

| Id | Estilo | Ancho | Texto exacto | Evidencia |
|---|---|---|---|---|
| P_I2 | `puerto=u1, hacia abajo` | 4.9 | `\itfn{2}\\ desde U1` | rl_corredor.py:74-98; rl_ippo.py:166-185 |
| P_I7 | `puerto=u3, hacia arriba` | 4.6 | `\itfn{7} hacia U3\\ \texttt{evaluar.py} y \texttt{veredicto.py}` | plan2/generar_trabajos.py:91-94; veredicto.py:11-13 |
| sumo | `entorno` | 2.5 | `\nodo{SUMO + TraCI\\ (U3)}{carga \itf{1} escenario\\ del caso;\\ paso de 1 s\\[2pt] entrega \itf{3}\\ observación\\ y recompensa\\[2pt] recibe \itf{4} acción}` | introduccion.tex:37; plan2/corredor.sumocfg:9 |
| ini | `iniciofin` | 4.5 | `\nodo{Trabajo de entrenamiento}{escenario, modelo y base $b$;\\ $N = 200$ episodios}` | plan2/generar_trabajos.py:20-43; capitulo3.tex:676-678 |
| s_ent | `semillas` | — | `entrenamiento: $b + k$` (dos líneas: `entrenamiento:\\ $b + k$`) | capitulo3.tex:678; rl_corredor.py:450 |
| lanzar | `proceso` | 3.0 | `\nodo{Iniciar el episodio $k$}{arranca SUMO (\itf{1})\\ con su semilla}` | rl_corredor.py:232-242,450; rl_ippo.py:449-456,880; comun.py:294-304 |
| decide | `decision` | — | `¿Decide el\\ agente $i$?` | rl_corredor.py:290-297; rl_ippo.py:548-555 |
| cerrar | `proceso` | 4.7 | `\nodo{Cerrar la decisión anterior}{$r_i$ = suma por segundo / 5\\ (\texttt{ql\_colas}: colas al decidir)\\ D, P: $\times\,0.02$; \textit{spill} (U4): $-$ término}` | rl_corredor.py:300-307; rl_ippo.py:137,496-526,557; capitulo3.tex:224-263 |
| obs | `proceso` | 4.7 | `\nodo{Observar}{T: niveles de cola y fase\\ D, P: vector continuo y máscara\\ D, U4: + \itfn{5}}` | rl_corredor.py:134-151,298; rl_ippo.py:346-389,558-559; rl_dqn.py:4-8,68; capitulo3.tex:194-214,360 |
| act | `proceso` | 4.7 | `\nodo{Actualizar o guardar}{T: actualiza $Q$ (SARSA: con la\\ acción siguiente, ya elegida)\\ D: guarda y entrena · P: anota $r_i$}` | rl_corredor.py:308-317 (SARSA elige antes, 310-312); rl_ippo.py:524,561-567; rl_dqn.py:169-204; rl_mappo.py:118-126 |
| elegir | `proceso` | 4.7 | `\nodo{Elegir: mantener o cambiar}{T, D: $\varepsilon$-greedy\\ P: muestrea; anota $o$, $a$, $\log\pi$, $V$}` | rl_corredor.py:201-206,319-321; rl_dqn.py:155-167; rl_ippo.py:568-594; rl_mappo.py:102-116 |
| aplicar | `proceso` | 4.7 | `\nodo{Aplicar la acción}{verde 10--60 s (D, P: máscara;\\ T: se corrige tras elegir)\\ 1: ámbar de 3 s y el otro verde}` | rl_corredor.py:323-329,362-368; rl_ippo.py:383-389,598-603,630-636; capitulo3.tex:176-190 |
| avanzar | `proceso` | 4.7 | `\nodo{Avanzar 1 s}{acumula la recompensa por agente}` | rl_corredor.py:331-346; rl_ippo.py:605-619 |
| fin | `decision` | — | `¿Red vacía o\\ 6000 pasos?` | rl_corredor.py:284; rl_ippo.py:534 |
| cierre | `proceso` | 4.8 | `\nodo{Cierre del episodio}{\itfn{6} del episodio;\\ D, P: cierran la última decisión}` | rl_corredor.py:372-390; rl_ippo.py:640-682 |
| ppo | `proceso` + `marca` «P» | 4.8 | `\nodo{GAE y actualización PPO}{MAPPO (U4): crítico central}` | rl_ippo.py:686-749,883-884; rl_mappo.py:135-177,248 |
| toca | `decision` | — | `¿$k$ múltiplo de 10\\ o $k = N$?` | rl_corredor.py:458; rl_ippo.py:888 |
| validar | `proceso` | 3.6 | `\nodo{Validación}{política congelada,\\ un episodio por semilla;\\ valor = retraso medio (\itf{6})}` | rl_corredor.py:397-404,458-466; rl_ippo.py:753-770,888-889; capitulo3.tex:680-686 |
| s_val | `semillas` | — | `validación: 999 y 1999` | capitulo3.tex:681-682 |
| ckpt | `archivo` | 4.8 | `\nodo{\textit{Checkpoint}}{\texttt{checkpoints/<tag>\_ep<NNN>}}` | rl_corredor.py:468; rl_ippo.py:891-893 |
| reg | `archivo` | 4.8 | `\nodo{Registro}{\texttt{resultados\_<tag>.csv}:\\ una fila por episodio}` | rl_corredor.py:436-440,474; rl_ippo.py:866-869,894 |
| otro | `decision` | — | `¿$k < N$?` | rl_corredor.py:448; rl_ippo.py:874 |
| ajuste | `proceso` | 4.8 | `\nodo{Ajuste para el episodio $k + 1$}{T, D: baja $\varepsilon$ · P: baja la tasa}` | rl_corredor.py:426-429,476; rl_dqn.py:216-219,299; rl_ippo.py:875-877; rl_mappo.py:240-242 |
| publicar | `iniciofin` | 4.6 | `\nodo{Publicar el \textit{checkpoint}\\ de menor validación}{empate: el más tardío;\\ con sus metadatos}` | rl_corredor.py:479-500; rl_ippo.py:902-913; capitulo3.tex:689-691 |

Notas de verificación:
- **Orden de la decisión** (cerrar → observar → actualizar o guardar → elegir → aplicar), válido
  para los cuatro casos:
  - `rl_ippo` cierra la decisión anterior antes de observar (557-558); `rl_corredor` observa y
    luego calcula r (298, 300-307), en el mismo instante (Q5). Se dibuja el orden de `rl_ippo`,
    igual que en U4.
  - Q-learning actualiza Q y después elige (308-317, 319-320). DQN guarda la transición y hace su
    actualización en el gancho `transicion`, antes de `decidir` (rl_ippo.py:561-567,581;
    rl_dqn.py:169-179). En los dos, actualizar va antes de elegir y el orden importa, porque la
    elección usa la Q ya actualizada.
  - SARSA es la excepción: elige la acción siguiente antes de actualizar (310-312). Lo dice el
    detalle de act.
  - IPPO anota r al cerrar (524) y guarda o, máscara, a, log π y V después de muestrear
    (588-594). MAPPO anota r y la transición anterior en `transicion` (rl_mappo.py:118-126) y
    calcula log π y V en `decidir` (102-116).
- **Ajuste**: T baja ε al final del episodio k (rl_corredor.py:476); D fija ε y P fija la tasa al
  empezar el episodio siguiente (rl_dqn.py:299; rl_ippo.py:875-877). Se dibuja en la rama «sí» de
  ¿k < N?, donde el efecto es el mismo para los tres: el ajuste de T tras el último episodio no
  se usa, y el de D y P en k = 1 da los valores iniciales (ε = 1, tasa 10⁻³).
- Los números de ε (× 0.9716 con piso 0.01; lineal de 1 a 0.05 en la primera mitad) y de la tasa
  (lineal desde 10⁻³) están verificados (rl_corredor.py:424-427; rl_dqn.py:216-219;
  rl_ippo.py:875), pero quedan fuera del dibujo: están en tab:plan2-hiper.

**Aristas**

| Desde → hacia | Estilo | Etiqueta | Evidencia |
|---|---|---|---|
| P_I2 → ini | `interfaz` | — | rl_ippo.py:166-185 |
| ini → lanzar | `flujo` | `$k = 1$` | rl_corredor.py:448 |
| lanzar → sumo | `interfaz` | `\itf{1}` | rl_corredor.py:232-242; rl_ippo.py:449-456 |
| lanzar → decide | `flujo` | — | rl_corredor.py:284-294 |
| decide → cerrar | `flujo` | `sí: cada 5 s\\ de su verde` | rl_corredor.py:290-297; rl_ippo.py:548-555; capitulo3.tex:171-173 |
| decide → avanzar | `flujo` | `no` | rl_corredor.py:294-297 (continue) |
| cerrar → obs → act → elegir → aplicar | `flujo` | — | rl_ippo.py:557-603; rl_corredor.py:298-329 |
| sumo → obs | `interfaz` | `\itf{3}` | rl_corredor.py:149-151; rl_ippo.py:346-357 |
| aplicar → sumo | `interfaz` | `\itf{4}` | rl_corredor.py:326-328; rl_ippo.py:600-601 |
| aplicar → avanzar | `flujo` | `tras todos los agentes` | rl_corredor.py:290,331; rl_ippo.py:583,605 |
| sumo → avanzar | `interfaz` | `\itf{3}` | rl_corredor.py:333; rl_ippo.py:607 |
| avanzar → fin | `flujo` | — | rl_corredor.py:284 |
| fin → decide (se une sobre decide) | `repeticion` | `no: siguiente segundo` | rl_corredor.py:284; rl_ippo.py:534 |
| fin → cierre | `flujo` | `sí` | rl_corredor.py:372; rl_ippo.py:640 |
| cierre → ppo | `flujo` | `P` | rl_ippo.py:883-884 |
| cierre → toca (se une a ppo → toca debajo de toca) | `flujo` | `T, D` | rl_corredor.py:450-458; rl_dqn.py:301-306 |
| ppo → toca | `flujo` | — | rl_ippo.py:884-888 |
| toca → validar | `flujo` | `sí` | rl_corredor.py:458-461 |
| toca → reg (se salta validar y ckpt) | `flujo` | `no` | rl_corredor.py:474 |
| validar → ckpt → reg → otro | `flujo` | — | rl_corredor.py:466-474 |
| otro → ajuste | `flujo` | `sí` | rl_corredor.py:448,476 |
| ajuste → lanzar (se une por arriba a la flecha ini → lanzar) | `repeticion` | `$k + 1$` | rl_corredor.py:448-450; rl_ippo.py:874-880 |
| otro → publicar | `flujo` | `no` | rl_corredor.py:479-488 |
| publicar → P_I7 | `interfaz` | — | plan2/generar_trabajos.py:91-94 |

**Agrupaciones.**
- Recuadro `grupo=u2`, título «U2 · Aprendizaje por refuerzo» (el alcance va en el pie).
- Subgrupo «Decisión del agente $i$» con cerrar, obs, act, elegir y aplicar.
- Subgrupo «Tras cada episodio» con cierre, ppo, toca, validar, s_val, ckpt, reg, otro y ajuste.
- Nada más: el bucle de 1 s lo muestra la flecha gruesa, no un tercer nivel.

**Disposición** (ciclo en sentido horario; 15 × ~19.4 cm):
- **Fuera del recuadro, arriba** (y 0 a −0.95): P_I2 sobre ini (x 3.4–8.3) y P_I7 sobre publicar
  (x 9.6–14.8).
- **sumo**, a la izquierda, x 0–2.8, desde la altura de lanzar hasta la de avanzar.
- **Recuadro U2**: x 3.2–15, y −1.1 a −17.55.
- **Columna izquierda**, x 3.5–8.65, de arriba abajo: ini, lanzar (x 3.5–6.7, con s_ent a su
  derecha, en dos líneas, x 6.8–9.1), decide, subgrupo de decisión (cerrar, obs, act, elegir,
  aplicar), avanzar y fin.
- **Hueco central**, x 8.65–9.25, con dos verticales:
  - decide «no» → avanzar (x ≈ 8.8, baja).
  - fin «no: siguiente segundo» → decide (x ≈ 9.05, sube y se une por arriba a la flecha
    lanzar → decide).
- **Columna derecha**, x 9.35–14.6, **de abajo arriba**: cierre (a la altura de fin), ppo, toca,
  validar (s_val debajo), ckpt, reg, otro y ajuste (a la altura de lanzar). publicar va arriba de
  todo.
- **Otras rutas**:
  - ajuste → lanzar sale de ajuste por el oeste, sube y va a la izquierda entre ini y lanzar,
    por encima de s_ent, hasta unirse a la flecha ini → lanzar. Queda por encima del final de las
    dos verticales del hueco central.
  - fin «sí» sale por el sur, baja, pasa por debajo de las verticales y entra a cierre por abajo.
  - cierre «T, D» sale por el este, sube por x ≈ 14.75 y se une a la flecha ppo → toca debajo de
    toca.
  - toca «no» sale por el este, sube por x ≈ 14.75 hasta reg (tramo distinto del anterior).
  - otro «no» sale por el este y sube por x ≈ 14.75 hasta publicar.
- Sin cruces de flechas.
- **Leyenda**: tres filas en y ≈ −17.9, −18.5 y −19.1. Fila 1: `proceso, archivo, decision,
  iniciofin, entorno, semillas`. Fila 2: `puerto, flujo, interfaz, repeticion`. Fila 3: la clave de
  las marcas (§1.8).
- Prescindibles si falta sitio, en este orden:
  1. La segunda línea de la etiqueta decide → cerrar (queda «sí» y la regla pasa al pie).
  2. Fundir toca con validar en un nodo «Validación (cada 10 episodios y en el último)».

**Pie de figura (borrador)**
```latex
\caption[Flujo de U2: entrenamiento de un aprendiz]{Flujo de U2 para un aprendiz y una base $b$
(un trabajo de la cola; se repite con las bases 42, 2042 y 4042). A la izquierda, el episodio:
SUMO arranca con la semilla $b + k$ (I1) y avanza de a 1~s; cada agente decide cada 5~s de su
verde, nunca en ámbar: cierra la decisión anterior con la recompensa acumulada, observa (I3),
aprende o anota, elige y aplica la acción (I4). La flecha gruesa de la izquierda repite el
segundo hasta vaciar la red o llegar a 6000 pasos, y la de arriba lanza el episodio $k + 1$. A la
derecha, lo que sigue a cada episodio: las métricas que entrega U3 (I6), la actualización PPO,
la validación con la política congelada, el \textit{checkpoint}, el registro y el ajuste de la
exploración o de la tasa de aprendizaje. Al terminar los $N = 200$ episodios se publica el
\textit{checkpoint} de menor validación con sus metadatos (I7). U2 recibe de U1 las
aproximaciones de cada semáforo (I2), y DQN y las variantes de U4 observan además los mensajes
(I5). T: tabulares; D: DQN; P: IPPO y MAPPO; lo que no lleva marca es común a todos. Las
variantes de U4 siguen este mismo ciclo (Figura~\ref{fig:flujo-u4}).}
\label{fig:flujo-u2}
```

---

### 3.4 Flujo de U3 (`u3.tex` → `images/diag_u3.pdf`, `fig:flujo-u3`)

**Propósito.** Responde dos preguntas:
1. Qué se mide en cada corrida de cualquier control (fijo, actuado o aprendiz; entrenamiento,
   validación o evaluación), de qué salida de SUMO sale y adónde va.
2. Cómo las corridas de evaluación (fijo, actuado y las tres bases de cada modelo, con las
   semillas 1001–1030) pasan por `evaluar.py`, `consolidar.py` y `veredicto.py` hasta las tablas
   del Cap. V y del Anexo A.

Además fija las interfaces de U3 con U1, U2/U4 y los resultados. Nunca hubo un diagrama propio de
U3.

**Ubicación.** capitulo3.tex, `sec:u3`, después del primer párrafo (termina en la línea 537).

**Frase que la cita**, al final de ese párrafo:
> La Figura~\ref{fig:flujo-u3} resume el flujo de U3: qué se mide en cada corrida y de dónde sale,
> adónde va, y cómo las corridas de evaluación llegan al veredicto (Secciones~\ref{sec:estadistica}
> y~\ref{sec:veredicto}).

Segunda cita, opcional: capitulo4.tex, `sec:ejecucion`, «Cierre de los resultados» (líneas
927-939).

**Nivel de detalle.**
- Sí van:
  - Arriba, la medición común a toda corrida: SUMO + TraCI y sus dos fuentes, las lecturas de
    cada segundo (con `comun.py` para los enlaces) y el `tripinfo` (leído por `comun.py`). Cada
    fuente lleva la familia de métricas que da.
  - En medio, la cadena de evaluación; abajo, `veredicto.py` en dos etapas: primero comprueba que
    los datos estén completos y solo después aplica la regla y mira la convergencia.
  - Los números del protocolo: 1001–1030, 10 000 remuestreos, 90 % de las plazas, 5 %, −5 % y
    p < 0.05. Las desigualdades completas de la regla van en el itemize de `sec:veredicto`.
- Quedan fuera:
  - El modo antiguo de `evaluar.py` (06.09), la fase exploratoria y la cola.
  - Latencia y pérdida (van en U4).
  - `tablas_cap5.py`, `grafico_convergencia.py` y `graficar.py`.
  - Las series `serie_`/`fases_` de la primera semilla, y el conteo de decisiones y cambios de
    fase.
  - La nota «IPPO *spill* = vecinos» del veredicto (está en el catálogo, I8).
  - La lectura de la demanda para las tablas que hace `veredicto.py`.

**Tamaño objetivo:** 15 × 19.6 cm (máximo 20; sin holgura, ver prescindibles).

**Nodos**

| Id | Estilo | Ancho | Texto exacto | Evidencia |
|---|---|---|---|---|
| P_I1 | `puerto=u1, hacia izquierda` | 3.3 | `\itf{1} desde U1` | plan2/corredor.sumocfg:3-5; comun.py:113-142 |
| P_I4 | `puerto=ext, hacia izquierda` | 3.3 | `\itf{4} desde U2 y U4` | rl_corredor.py:325-329; rl_ippo.py:598-603 |
| P_I3 | `puerto=ext` | 3.3 | `\itf{3} hacia U2 y U4` | rl_corredor.py:149-151; rl_ippo.py:346-380 |
| P_I2 | `puerto=u1, hacia izquierda` | 3.3 | `\itfnn{2}\\ desde U1` | rl_corredor.py:265-270; rl_ippo.py:458 |
| P_I6 | `puerto=ext` | 3.3 | `\itfn{6}\\ hacia U2 y U4` | rl_corredor.py:436-476; rl_ippo.py:753-770 |
| P_I7a | `puerto=ext, hacia izquierda` | 3.3 | `\itfn{7}\\ desde U2 y U4 (3 bases)` | plan2/generar_trabajos.py:87-94; evaluar.py:183-252 |
| P_I7b | `puerto=ext, hacia izquierda` | 3.3 | `\itf{7} (metadatos)\\ valor elegido y serie` | veredicto.py:11-13,215-233 |
| P_I8 | `puerto=ext` | 3.3 | `\itfn{8}\\ hacia Cap.~V y Anexo~A` | capitulo5.tex:46,190-192; anexos.tex:32-82 |
| sumo | `entorno` | 9.6 | `\nodo{SUMO + TraCI}{SUMO 1.25.0; paso de 1 s; semilla de la corrida;\\ hasta vaciar la red (máx. 6000 pasos)\\ carga \itfn{1}; recibe \itfn{4};\\ entrega \itfn{3}}` | capitulo4.tex:38,485-489; plan2/corredor.sumocfg:9; rl_corredor.py:232-242,284 |
| trip | `archivo` | 4.4 | `\nodo{\texttt{tripinfo} (leído por \texttt{comun.py})}{retraso (\texttt{timeLoss}), espera,\\ paradas, \textit{throughput}, CO\textsubscript{2}, NO\textsubscript{x},\\ no terminados; corredor: flujos\\ de extremo a extremo (\itf{2})}` | rl_corredor.py:232-234,376; rl_ippo.py:450,665; comun.py:35-84; capitulo3.tex:539-552,595-603 |
| lect | `proceso` | 4.6 | `\nodo{Lecturas TraCI por segundo}{aproximaciones: colas,\\ \texttt{ret\_retraso}, \texttt{ret\_colas};\\ carriles de enlace (\texttt{comun.py}):\\ \textit{spillback} ($\geq$ 90\,\% de las plazas),\\ cola máx., \texttt{ret\_spill}}` | rl_corredor.py:265-270,331-346,378-389; rl_ippo.py:605-620,667-681; comun.py:21-22,170-240; capitulo3.tex:555-619 |
| metr | `proceso` | 4.4 | `\nodo{Métricas de la corrida}{mismas columnas en todo control}` | rl_corredor.py:376-390; rl_ippo.py:665-682; capitulo3.tex:742-744 |
| ctrl | `archivo` | 4.6 | `\nodo{Controles evaluados}{fijo tuneado y actuado (\itf{1});\\ políticas congeladas (\itf{7})}` | evaluar.py:173-252; capitulo3.tex:730-735 |
| eva | `proceso` | 4.4 | `\nodo{\texttt{evaluar.py}}{un control por llamada}` | evaluar.py:4-9,255-295 |
| s_eval | `semillas` | — | `evaluación: 1001--1030` | capitulo3.tex:713; plan2/generar_trabajos.py:21 |
| parc | `archivo` | 4.4 | `\nodo{Parciales}{\texttt{eval\_<esc>\_<control>.csv}:\\ una fila por semilla}` | evaluar.py:266-294 (en el código el marcador se llama `brazo`) |
| cons | `proceso` | 4.6 | `\nodo{\texttt{consolidar.py}}{media e IC95\,\% ($t$) por control;\\ $\Delta$ pareado por semilla frente al\\ fijo y al actuado: IC95\,\%\\ \textit{bootstrap} (10\,000) y Wilcoxon}` | consolidar.py:1-31,43,78-134; capitulo3.tex:742-780 |
| resu | `archivo` | 4.6 | `\nodo{Resumen}{\texttt{evaluacion\_<esc>\_resumen.csv}}` | consolidar.py:9-15,162-170 |
| dec1 | `decision` | — | `¿Datos\\ completos?` | veredicto.py:390-404,408-410 |
| base | `proceso` | 4.6 | `\nodo{Base publicada}{mediana de las tres bases por su\\ valor de validación elegido}` | veredicto.py:23-24,123-128,386-387; capitulo3.tex:692-696 |
| regla | `proceso` | 4.4 | `\nodo{Regla de veredicto}{base publicada frente al fijo y\\ al actuado: IC95\,\% \textit{bootstrap}\\ de $\Delta$, $p < 0.05$, umbral de $-5$\,\%\\ (actuado: solo frente al fijo)}` | veredicto.py:50,61-62,75-89,328-337,347-353,364-373; consolidar.py:97-104; capitulo3.tex:814-838,858-859 |
| conv | `proceso` | 4.6 | `\nodo{Convergencia}{último tercio de la validación:\\ meseta y estabilidad $\leq$ 5\,\%}` | veredicto.py:29-32,101-120; capitulo3.tex:799-811 |
| dec2 | `decision` | — | `¿Base\\ convergida?` | veredicto.py:131-137,411 |
| fver | `archivo` | 4.6 | `\nodo{Tablas de veredicto}{\texttt{veredicto.csv}, \texttt{veredicto.md},\\ \texttt{tablas/veredicto\_*.tex}}` | veredicto.py:15-20,719-729 |

**Aristas**

| Desde → hacia | Estilo | Etiqueta | Evidencia |
|---|---|---|---|
| P_I1 → sumo | `interfaz` | — | rl_corredor.py:232 |
| P_I4 → sumo | `interfaz` | — | rl_corredor.py:325-329 |
| sumo → P_I3 | `interfaz` | — | rl_ippo.py:223-232,607 |
| sumo → trip | `flujo` | `por viaje; no terminados al cierre` (a la izquierda del tramo) | rl_corredor.py:233; comun.py:46,70; capitulo3.tex:539-545 |
| sumo → lect | `flujo` | `cada segundo` | rl_corredor.py:331-337; rl_ippo.py:605-611 |
| P_I2 → lect (entra por el este) | `interfaz` | — | rl_corredor.py:265-270; rl_ippo.py:458 |
| trip → metr | `flujo` | `al cerrar la corrida` | rl_corredor.py:372-376 |
| lect → metr | `flujo` | — | rl_corredor.py:377-389 |
| metr → P_I6 | `interfaz` | — | rl_corredor.py:450-474 |
| metr → eva | `flujo` | `una fila por semilla` | evaluar.py:283-290 |
| P_I7a → ctrl | `interfaz` | — | evaluar.py:260-263 |
| ctrl → eva | `flujo` | — | plan2/generar_trabajos.py:76-94 |
| eva → sumo | `repeticion` | `una corrida por semilla` | evaluar.py:257,277-283 |
| eva → parc → cons → resu | `flujo` | — | evaluar.py:266-294; consolidar.py:49-63,162-170 |
| resu → dec1 | `flujo` | `$\Delta$, IC95\,\% y $p$ de cada control` | veredicto.py:188-191,328-337 |
| P_I7b → base | `interfaz` | — | veredicto.py:215-233,376-387 |
| base → dec1 | `flujo` | `base publicada` | veredicto.py:387-404 |
| base → conv | `flujo` | `su serie de validación` | veredicto.py:220-231,397-399 |
| dec1 → regla | `flujo` | `sí` | veredicto.py:405-408 |
| dec1 → fver | `flujo` | `no: PENDIENTE (motivo)` | veredicto.py:131-134,390-404,408-410 |
| regla → dec2; conv → dec2 (se une a regla → dec2) | `flujo` | — | veredicto.py:347-353,408-411 |
| dec2 → fver | `flujo` | `sí` (el veredicto: FUNCIONA, MEJORA, EMPATA o FALLA) | veredicto.py:80-89,137; capitulo3.tex:818-828 |
| dec2 → fver | `flujo` | `no: PENDIENTE con veredicto provisional` | veredicto.py:135-136; capitulo3.tex:829-833 |
| fver → P_I8 | `interfaz` | — | capitulo5.tex:46 |

**Agrupaciones.**
- Recuadro `grupo=u3`, «U3 · Simulación y medición».
- Subgrupo A: «Medición en cada corrida (entrenamiento, validación o evaluación)», con sumo,
  trip, lect y metr.
- Subgrupo B: «Evaluación», con `s_eval` en la misma fila que el subtítulo, a la derecha, y ctrl,
  eva, parc, cons y resu.
- Subgrupo C: «`veredicto.py`», con dec1, base, regla, conv, dec2 y fver.

**Disposición** (15 × ~19.6 cm). Es la columna U3 de la arquitectura ampliada: SUMO arriba y la
cadena hacia abajo, con U2/U4 a la derecha.
- **Recuadro U3**: x 0–10.8, desde y 0. Todos los puertos van fuera, a la derecha (x 11.0–15).
- Dos columnas dentro de los subgrupos: L, x 0.4–5.2, y R, x 5.6–10.4.
- **Subgrupo A**:
  - sumo a todo el ancho (x 0.4–10.4), con 1.85 cm de alto para que P_I1, P_I4 y P_I3 entren por
    su este.
  - Debajo, trip (L) y lect (R). P_I2 entra a lect por el este.
  - metr (L) debajo de trip. lect → metr baja desde lect y entra a metr por el este (mitad
    superior); metr → P_I6 sale por el este de metr (mitad inferior), pasa bajo lect y llega al
    puerto.
- **Subgrupo B**, en tres filas: eva (L) y ctrl (R, con P_I7a por el este); parc (L) y cons (R);
  resu (R). ctrl → eva va a la izquierda; eva → parc baja; parc → cons va a la derecha; cons →
  resu baja. La repetición eva → sumo va por el margen izquierdo, x ≈ 0.2.
- **Subgrupo C**, en tres filas:
  - dec1 (L, centrado en x ≈ 3.3) y base (R, con P_I7b por el este). resu → dec1 sale de resu por
    el oeste, va a x ≈ 3.3 y baja; la etiqueta va en el hueco L de la fila de resu. base → dec1 va
    a la izquierda.
  - regla (L) y conv (R). base → conv baja.
  - dec2 (L, centrado en x ≈ 3.3) y fver (R, con P_I8 por el este). conv se une a la flecha
    regla → dec2 sobre dec2; dec2 «sí» va a la derecha hasta fver.
  - dec2 «no» sale por abajo, baja 0.4 cm y va a la derecha hasta el pie de fver, con su etiqueta
    sobre ese tramo. dec1 «no» sale por el oeste, baja por x ≈ 0.2 y se une a ese tramo; su
    etiqueta va en tres líneas cortas («no:», «PENDIENTE», «(motivo)») entre el margen y dec1.
- Sin cruces de flechas.
- **Leyenda**: fila 1 `proceso, archivo, decision, entorno, semillas`; fila 2 `puerto, flujo,
  interfaz, repeticion`.
- Prescindibles si pasa de 20 cm, en este orden:
  1. La última línea de lect («cola máx., `ret_spill`») pasa al pie.
  2. La línea «(actuado: solo frente al fijo)» de regla pasa al pie.

**Pie de figura (borrador)**
```latex
\caption[Flujo de U3: medición y evaluación]{Flujo de U3. Arriba, la medición común a toda
corrida de cualquier control, sea de entrenamiento, de validación o de evaluación: SUMO con TraCI
y sus dos fuentes, las lecturas de cada segundo y el archivo \texttt{tripinfo}, que SUMO escribe
al terminar cada viaje y, al cerrar la simulación, con los vehículos no terminados. Sus métricas
van a los aprendices (I6) o, en la evaluación, a una fila por semilla. En medio, la evaluación de
cada control con la política congelada en las semillas 1001 a 1030 (\texttt{evaluar.py}) y la
estadística pareada por semilla (\texttt{consolidar.py}). Abajo, \texttt{veredicto.py}: elige la
base publicada con los metadatos de las políticas (I7) y comprueba que los datos estén completos;
solo entonces aplica la regla y mira la convergencia. Si faltan datos, o si la base publicada no
convergió, la celda queda PENDIENTE (en el segundo caso, con su veredicto provisional). El
actuado se juzga solo frente al fijo. El veredicto llega al Capítulo~V y al Anexo~A (I8). U3
entrega a U2 y U4 la observación y la recompensa (I3) y recibe sus acciones (I4).}
\label{fig:flujo-u3}
```

---

### 3.5 Flujo de U4 (`u4.tex` → `images/diag_u4.pdf`, `fig:flujo-u4`)

**Propósito.** Mostrar qué añade U4 al episodio de U2, en cada segundo y al final:
- qué se envían los semáforos vecinos, con qué reloj y cómo lo guarda el receptor;
- cómo entra en la observación, cómo decide el actor compartido y qué término añade *spill* a la
  recompensa;
- cómo se llena la trayectoria de cada agente durante el episodio, con el valor que estima el
  crítico (local en IPPO, central en MAPPO) en cada decisión, y cómo se actualiza la política con
  GAE y PPO al final.

De un vistazo, el color responde a «¿qué añade U4?»: naranja es lo de U2 y violeta lo de U4.
Amplía el recuadro U4 de la arquitectura y los nodos de U2 que llevan la marca P.

**Ubicación.** capitulo3.tex, `sec:u4`, después del segundo párrafo (termina en la línea 314) y
antes de «Vecinos y canal de mensajes» (línea 316).

**Frase que la cita**, al final de ese párrafo:
> La Figura~\ref{fig:flujo-u4} resume el flujo de U4 dentro de un episodio: cada 5~s los semáforos
> envían mensajes a sus vecinos; cuando le toca decidir, cada agente arma su observación con el
> último mensaje recibido, decide con el actor compartido y anota en su trayectoria el valor que
> estima el crítico, local en IPPO o centralizado en MAPPO; al terminar el episodio, la política
> se actualiza con PPO.

Segunda cita, opcional: capitulo4.tex:671 (IPPO) y 712 (MAPPO), «(Figura~\ref{fig:flujo-u4})».

**Nivel de detalle.**
- Sí van:
  - Los dos relojes: el global de 5 s para los mensajes y el propio de cada agente, cada 5 s de su
    verde.
  - Los cinco campos del mensaje, el canal y lo que guarda el receptor.
  - La observación (12 + id + 8 por lado; d = 31 o 53), la máscara y el actor.
  - La recompensa por segundo con el término *spill*, y el cierre de cada decisión.
  - La trayectoria de cada agente y los dos críticos, que actúan en cada decisión.
  - GAE y PPO al final del episodio.
  - Qué variantes usan cada paso (marcas y pie).
- Quedan fuera:
  - La tabla componente por componente (tab:obs-u4).
  - Los hiperparámetros, salvo los que identifican: 0.95, 0.2, 10 y 64.
  - Lo interno de DQN (memoria, red objetivo, ε).
  - Validación, *checkpoints* y publicación, que van en U2 y aquí se remiten con un puerto.
  - Métricas y `ret_*` (van en U3).
  - `cola_mi_salida` (capitulo4.tex:779-795).
  - La variante `cambio`, que no se entrenó (capitulo3.tex:413-415).
  - La robustez con latencia y pérdida (Anexo C).
  - La edad deducida de 0 a 4 s.
  - Un cuadro de variantes: repetiría tab:plan2-modelos (capitulo3.tex:430-456) y no cabe; lo
    cubren las marcas y el pie.

**Tamaño objetivo:** 15 × 19.4 cm (máximo 20).

**Nodos**

| Id | Estilo | Ancho | Texto exacto | Evidencia |
|---|---|---|---|---|
| sumo | `entorno` | 2.5 | `\nodo{SUMO + TraCI\\ (U3)}{carga \itf{1} escenario\\ del caso;\\ paso de 1 s\\[2pt] entrega \itf{3}\\ observación\\ y recompensa\\[2pt] recibe \itf{4} acción}` | rl_ippo.py:219-241,449-458 |
| lanzar | `proceso=u2` | 3.0 | `\nodo{Iniciar el episodio $k$}{arranca SUMO (\itf{1})\\ con su semilla}` | rl_ippo.py:446-476,880 |
| reloj | `decision` (u4) | — | `¿Múltiplo\\ de 5 s?` | rl_ippo.py:535,539 |
| n_reloj | `nota` | — | `reloj global` | rl_ippo.py:535; capitulo3.tex:321 |
| msg | `proceso` (u4) | 5.45 | `\nodo{\itfn{5} de $j$ a $i$}{fase de $j$ (avenida, transversal o ámbar)\\ y tiempo en ella; vehículos que descargan\\ hacia $i$; cola en esa aproximación y\\ en el enlace $j \to i$ (vecinos: \itf{2});\\ canal: latencia y pérdida 0 en el plan;\\ $i$ guarda el último mensaje y su edad}` | rl_ippo.py:286-314,324-338,540-546; plan2/generar_trabajos.py:33-41; capitulo3.tex:321-336 |
| decide | `decision=u2` | — | `¿Decide el\\ agente $i$?` | rl_ippo.py:548-555 |
| cerrar | `proceso=u2` + `marca=u4` «*spill*» | 4.7 | `\nodo{Cerrar la decisión anterior}{$r_i$ = suma por segundo / 5\\ (\textit{spill}: $-$ 2 $\cdot$ exceso / 5);\\ guarda $0.02\,r_i$ en la trayectoria}` | rl_ippo.py:135,137,496-526,557; capitulo3.tex:224-249 |
| obs | `proceso` (u4) | 4.7 | `\nodo{Observar}{$o_i$ = 12 locales + id + 8 por lado;\\ $d$ = 31 (53 en P5); local: ranuras 0}` | rl_ippo.py:174,185,346-380,558; capitulo3.tex:340-360 |
| elegir | `proceso=u2` | 4.7 | `\nodo{Elegir: mantener o cambiar}{actor compartido $\pi(a \mid o_i)$,\\ con máscara; muestrea al entrenar;\\ la más probable al evaluar}` | rl_ippo.py:252-259,383-389,568-578; capitulo3.tex:681; capitulo4.tex:673-686 |
| aplicar | `proceso=u2` | 4.7 | `\nodo{Aplicar la acción}{0: mantener; 1: ámbar de 3 s\\ y el otro verde}` | rl_ippo.py:598-603,630-636 |
| avanzar | `proceso=u2` + `marca=u4` «*spill*» | 4.7 | `\nodo{Avanzar 1 s}{acumula la recompensa de $i$\\ (\textit{spill}: y el exceso de cola en $i \to j$)}` | rl_ippo.py:412-427,605-619; capitulo3.tex:224-249 |
| fin | `decision=u2` | — | `¿Red vacía o\\ 6000 pasos?` | rl_ippo.py:534 |
| c_loc | `proceso=u2` + `marca=u2` «IPPO» | 2.35 | `\nodo{Crítico local\\ $V(o_i)$}{compartido}` | rl_ippo.py:1-4,252-265,570,594; capitulo4.tex:674-679 |
| c_cen | `proceso` (u4) + `marca` «MAPPO» | 2.7 | `\nodo{Crítico central\\ $V(o_1 \ldots o_n, i)$}{entrada $n \cdot d + n$;\\ solo al entrenar}` | rl_mappo.py:1-8,69-88,112-115,124; capitulo4.tex:714-731 |
| tray | `archivo=u2` | 5.45 | `\nodo{Trayectorias por agente}{$o_i$, máscara, $a_i$, $\log\pi$, $V$ al decidir;\\ $0.02\,r_i$ al cerrar la decisión}` | rl_ippo.py:478-481,524,588-594; rl_mappo.py:96-100,118-126 |
| gae | `proceso=u2` | 5.2 | `\nodo{GAE por agente}{sobre las trayectorias; $\gamma = \lambda = 0.95$;\\ si se cortó a los 6000 pasos,\\ $V$ del último estado}` | rl_ippo.py:144,646-652,686-710,883; rl_mappo.py:127-133,135-140 |
| ppo | `proceso=u2` | 4.7 | `\nodo{Actualización PPO}{recorte 0.2; 10 épocas; minilote 64;\\ actor y crítico (MAPPO: el central)}` | rl_ippo.py:144-145,713-749,884; rl_mappo.py:143-177,248 |
| P_U2 | `puerto=u2, hacia izquierda` | 2.3 | `\textbf{Sigue el ciclo}\\ \textbf{de U2}:\\ validación,\\ \textit{checkpoint},\\ episodio $k + 1$;\\ publicación de\\ la política (\itf{7})` | rl_ippo.py:874-913; rl_mappo.py:239-283 |

Nota de verificación: el valor V se calcula en cada decisión y se guarda en la trayectoria (IPPO:
`politica(obs)` → `b["valor"]`, rl_ippo.py:570,594; MAPPO: `critico(entradas)` en `decidir`,
rl_mappo.py:112-115, y `transicion`, 124). Al final solo se estima V para cerrar la trayectoria si
el episodio se cortó a los 6000 pasos (rl_ippo.py:647-652; rl_mappo.py:127-133).

**Aristas**

| Desde → hacia | Estilo | Etiqueta | Evidencia |
|---|---|---|---|
| lanzar → sumo | `interfaz` | `\itf{1}` | rl_ippo.py:449-456 |
| lanzar → reloj | `flujo` | — | rl_ippo.py:534-535 |
| reloj → msg | `flujo` | `sí (no en\\ IPPO local)` | rl_ippo.py:445,535-546 |
| reloj → decide | `flujo` | `no` | rl_ippo.py:535,548 |
| msg → decide (se une a reloj → decide sobre decide) | `flujo` | — | rl_ippo.py:546-548 |
| msg → obs | `interfaz` | `último mensaje y edad` | rl_ippo.py:367-379 |
| decide → cerrar | `flujo` | `sí: cada 5 s de su verde` | rl_ippo.py:548-557; capitulo3.tex:171-173 |
| decide → avanzar (por la derecha, x ≈ 14.65) | `flujo` | `no` | rl_ippo.py:549-555,605 |
| cerrar → obs → elegir → aplicar | `flujo` | — | rl_ippo.py:557-603 |
| sumo → obs | `interfaz` | `\itf{3}` | rl_ippo.py:349-353 |
| elegir → tray | `flujo` | `$o_i$, $a_i$, $\log\pi$` | rl_ippo.py:588-594 |
| c_loc → tray; c_cen → tray | `flujo` | `$V$ al decidir` (una etiqueta entre las dos flechas) | rl_ippo.py:570,594; rl_mappo.py:112-115,124 |
| aplicar → sumo | `interfaz` | `\itf{4}` | rl_ippo.py:598-603 |
| aplicar → avanzar | `flujo` | `tras todos los agentes` | rl_ippo.py:583,605 |
| sumo → avanzar | `interfaz` | `\itf{3}` | rl_ippo.py:605-619 |
| avanzar → fin | `flujo` | — | rl_ippo.py:534 |
| fin → reloj (por la derecha, x ≈ 14.9; se une a lanzar → reloj sobre reloj) | `repeticion` | `no: siguiente segundo` | rl_ippo.py:534 |
| fin → gae | `flujo` | `sí` | rl_ippo.py:640-652,883 |
| tray → gae | `flujo` | — | rl_ippo.py:686-710,883 |
| gae → ppo | `flujo` | — | rl_ippo.py:883-884 |
| ppo → P_U2 | `flujo` | — | rl_ippo.py:888-913 |

**Agrupaciones.**
- Recuadro `grupo=u4`, título «U4 · Coordinación distribuida» (el alcance va en el pie).
- Subgrupo `subgrupo=u2` «Al final del episodio (IPPO y MAPPO)»: gae y ppo.
- El resto no forma subgrupo: el bucle de cada segundo y el de cada decisión los muestran sus
  flechas.

**Disposición** (15 × ~19.4 cm; SUMO a la izquierda, como en U2):
- **sumo**, x 0–2.8, desde la altura de lanzar hasta la de avanzar. **P_U2**, fuera del recuadro,
  debajo de sumo (x 0–2.9), a la altura del subgrupo final; ppo → P_U2 sale de ppo por el oeste.
- **Recuadro U4**: x 3.2–15, desde y 0.
- **Espina**, x 3.5–8.4, de arriba abajo: lanzar, reloj (con n_reloj a su izquierda), decide,
  cerrar, obs, elegir, aplicar, avanzar y fin. Entre lanzar y reloj queda el punto donde entra
  fin «no»; entre reloj y decide, el punto donde entra msg.
- **Columna derecha**, x 8.85–14.5:
  - msg arriba, a la altura de reloj (reloj «sí» entra por su oeste). Su borde inferior queda por
    encima del codo de decide «no».
  - c_loc (x 8.85–11.4) y c_cen (x 11.6–14.5), lado a lado, entre cerrar y obs; tray debajo
    (x 8.85–14.5), a la altura de elegir. c_loc → tray y c_cen → tray bajan.
- **Subgrupo final**, debajo de fin, a todo el ancho: ppo a la izquierda (x 3.5–8.4) y gae a la
  derecha (x 8.85–14.5). fin «sí» sale por el sur, pasa sobre ppo y entra a gae por el oeste
  (mitad superior); gae → ppo sale de gae por el oeste (mitad inferior) y va a la izquierda.
- **Bucles por la derecha**, para que nada de la columna derecha los cruce al entrar a la espina:
  - decide «no» sale por el este, va a la derecha hasta x ≈ 14.65, baja y entra a avanzar por el
    este. Encierra a los críticos y a tray: elegir → tray no lo cruza.
  - fin «no» sale por el este, va a x ≈ 14.9, sube y entra por arriba de reloj. Encierra a msg y a
    todo el bucle de cada segundo.
- **Cruces inevitables, con corte blanco** (tres):
  - msg → obs cruza el tramo superior de decide «no».
  - tray → gae cruza el tramo inferior de decide «no» y el de fin «no».
- **Leyenda**: fila 1 `proceso, archivo, decision, entorno`; fila 2 `puerto, flujo, interfaz,
  repeticion`.
- Prescindibles si falta sitio, en este orden: n_reloj (pasa al pie), la tercera línea de gae y
  la flecha tray → gae (el detalle de gae ya dice «sobre las trayectorias»; así desaparecen dos
  cruces).

**Pie de figura (borrador)**
```latex
\caption[Flujo de U4: coordinación distribuida]{Flujo de U4 en un episodio de \texttt{rl\_ippo.py},
visto desde un semáforo $i$ y cada vecino $j$; DQN y MAPPO corren el mismo episodio. En naranja,
los pasos de U2 que U4 reutiliza; en violeta, lo que añade U4. Cada 5~s de reloj global, $j$ envía
a $i$ un mensaje (I5) que $i$ guarda con su edad; U1 da los vecinos y los enlaces de cada lado
(I2, aproximaciones, enlaces y vecinos). Cuando le toca decidir, cada 5~s de su propio verde, $i$
cierra la decisión anterior, observa con el último mensaje, elige con el actor compartido y anota
en su trayectoria la observación, la acción, su probabilidad y el valor que el crítico (local en
IPPO, central en MAPPO) estima para esa decisión. La variante \textit{spill} resta a la
recompensa la cola que pasa de la mitad de las plazas en los enlaces que salen de $i$. Al final
del episodio se calculan las ventajas con GAE y se actualizan el actor y el crítico con PPO; la
validación, el \textit{checkpoint} y la publicación siguen el ciclo de U2
(Figura~\ref{fig:flujo-u2}). Las marcas indican en qué modelos actúa cada paso. IPPO vecinos,
IPPO \textit{spill} y MAPPO usan los mensajes; DQN (U2) también, y decide con su red $Q$; IPPO
local no los usa. La flecha gruesa repite el segundo hasta vaciar la red o llegar a 6000 pasos.}
\label{fig:flujo-u4}
```

---

## 4. Cómo se relacionan los diagramas

1. **La arquitectura es el mapa.** Cada recuadro de color de la arquitectura es la figura de una
   unidad, y cada flecha I de la arquitectura aparece en la figura de la unidad que la produce y en
   la de la que la consume, como puerto, flecha o cita (matriz de §2). Nunca hay una flecha con
   número en una figura de unidad que no esté en la arquitectura.
2. **Cada figura de unidad amplía un recuadro de la arquitectura:**

   | Figura | Qué amplía de la arquitectura |
   |---|---|
   | U1 | Los cuatro nodos de U1: Red vial, Demanda y Programas de referencia son sus subgrupos, y la tabla de aproximaciones, enlaces y vecinos es un nodo; más el camino OSM |
   | U2 | Tabulares y redes neuronales (marcas T, D, P), las semillas de entrenamiento y validación y el protocolo del pie (200 episodios, validación, *checkpoint*, publicación) |
   | U3 | La columna SUMO → medición → `evaluar.py` → `consolidar.py` → `veredicto.py` → resultados |
   | U4 | agente j ⇄ agente i (I5), la observación extendida, *spill* y el crítico central, dentro de un episodio |

3. **La geometría se repite:** U1 arriba, U3 a la izquierda de los aprendices, U4 debajo de U2,
   resultados abajo a la derecha. En U2 y U4, SUMO va a la izquierda; en U3, U2/U4 van a la
   derecha.
4. **U2 y U4 comparten el bucle:**
   - En U2 están el ciclo completo y la marca P.
   - U4 amplía un episodio de P: mensajes, observación, críticos, trayectorias y actualización
     PPO, con los pasos de U2 en naranja.
   - U4 remite el ciclo entre episodios a U2 con el puerto «Sigue el ciclo de U2».
   - U2 remite los mensajes a U4 con la cita «D, U4: + \itfn{5}» en Observar.
   - Los nodos comunes llevan la misma etiqueta y el mismo orden en las dos figuras (§1.6).
5. **Referencias cruzadas**: solo en los pies de figura, no dentro de los dibujos. El pie de la
   arquitectura cita las cuatro figuras una por una; U2 cita a U4 y U4 cita a U2.
6. **Estilo único**: los cinco archivos hacen `\input{estilo_diagramas}`; ninguno define colores ni
   estilos propios. Si una figura necesita un ajuste local (por ejemplo `text width`), va en las
   opciones del nodo.

---

## 5. Discrepancias resueltas y dudas para el autor

Resueltas en los diagramas:

| # | Discrepancia | Decisión |
|---|---|---|
| D1 | El nombre de U2 y U3 cambia: la introducción dice «aprendizaje por refuerzo» y «simulación y medición en SUMO» (introduccion.tex:37); tab:pipeline dice «U2. Entrenamiento» y «U3. Medición», sin SUMO (capitulo3.tex:55-57) | Se usan los de la introducción, y SUMO + TraCI va dentro de U3. **Condición previa** a integrar la arquitectura, que queda en la misma página que la tabla: renombrar esas dos filas («U2. Aprendizaje por refuerzo», «U3. Simulación y medición»). Es un cambio de texto y lo aprueba el autor |
| D2 | tab:pipeline pone solo `escenarios_plan2.py` como registro de U1, pero ese archivo cubre P4 y P5; P1–P3 están en `rl_corredor.ESCENARIOS` y `rl_ippo.VECINOS` (rl_corredor.py:74-96; rl_ippo.py:105-118) | La figura de U1 nombra los tres archivos |
| D3 | El actuado figura como salida de U1 en tab:pipeline, pero `comun.archivo_actuado` lo escribe al lanzar el control actuado, desde el trabajo de U3 `eval_<esc>_actuado` (plan2/generar_trabajos.py:78-81; evaluar.py:173-180; rl_corredor.py:235-237) | Se deja en U1, como en tab:pipeline, con el detalle «`comun.py`, al evaluar el actuado (`evaluar.py`)» (capitulo4.tex:432-434 lo dice bien) |
| D4 | capitulo4.tex:906-907 dice que el entrenamiento depende «del barrido de su caso». En el código, `train_*` solo requiere la bandera y `prep_<esc>` (plan2/generar_trabajos.py:85-90); el barrido solo lo requiere `eval_<esc>_fijo` (78-81). cola.out lanza entrenamientos antes del primer barrido | La cola no se dibuja (mecánica de ejecución). **Hay que corregir esa frase de la tesis** |
| D5 | «Las mismas fases que el fijo» (capitulo3.tex:142 y 463; capitulo5.tex:20; conclusiones.tex:96; recomendaciones.tex:33,95) frente al código: el actuado toma las fases del programa estático por omisión del `.net.xml` (comun.py:118-137). Son los mismos estados, pero en malla3 van en otro orden | La figura dice «fases del programa por omisión», como capitulo4.tex:91-96,426-433 |
| D6 | La base publicada la elige `veredicto.py` (veredicto.py:123-129), no U2 | Va en U3 (nodo base, puerto I7 metadatos) |
| D7 | El objetivo U4 promete «colas/salidas previstas» e impacto a nivel de corredor (introduccion.tex:48). Los mensajes no llevan predicción (rl_ippo.py:324-338; introduccion.tex:54 ya lo dice) y las métricas de corredor no se analizaron | Se dibuja el contenido real del mensaje; no se dibuja predicción ni análisis de corredor |
| D8 | DQN está en U2 según tab:pipeline, pero usa la observación de U4 | DQN en U2, con la flecha I5 desde U4 (arquitectura), la cita en Observar (U2) y la mención en el pie de U4 |
| D9 | El boceto de la arquitectura usaba I8 = resumen e I9 = veredicto | I8 = veredicto; el resumen es interno a U3 y no lleva número |
| D10 | Tres fichas proponían etiquetas distintas para la misma figura (`fig:u1-flujo`, `fig:u2`, `fig:u4-flujo`) y otros archivos (`flujo_u3.pdf`, `u4_flujo.pdf`) | Se usan `fig:flujo-u1` … `fig:flujo-u4` y `images/diag_<nombre>.pdf`, como `construir.py` |
| D11 | tab:pipeline (capitulo3.tex:57) atribuye a U3 los programas `comun.py`, `evaluar.py`, `consolidar.py` y `veredicto.py`, y describe las entradas de U3 como «lecturas de TraCI de cada corrida». Pero las colas y los retornos `ret_*` se calculan en `correr_episodio` de `rl_corredor.py` y `rl_ippo.py` (rl_corredor.py:331-346,376-389; rl_ippo.py:605-620,665-681); `comun.py` solo aporta `leer_tripinfo` y `MedidorEnlaces` (comun.py:35,180) | La arquitectura dice «(`comun.py` y `correr_episodio`)» y U3 separa lo que hace cada uno. **Sugerencia**: añadir en la fila U3 de tab:pipeline «y la medición de \texttt{correr\_episodio}» |
| D12 | La numeración de la primera versión (I6 = política, I7 = métricas) hacía leer la arquitectura I3, I4, I7, I6 | Se intercambiaron: I6 = métricas por corrida, I7 = política publicada (estilo, catálogo, matriz y las cinco figuras). Aún no hay figuras dibujadas, así que no queda nada con la numeración vieja |

Dudas que no cambian el dibujo pero conviene que decida el autor:

- **Q1.** Ningún script del repositorio calcula el factor f. La calibración solo consta en el texto
  (capitulo4.tex:237-309) y en las cabeceras de corredor_alta.rou.xml:2-3 y
  plan2/red_alta.rou.xml:2-25. Las cifras de P2 de capitulo4.tex:262-266 no están en ningún
  archivo revisado. La figura dice «con el actuado», sin nombrar el programa.
- **Q2.** La ampliación automática del eje de verde en el barrido está implementada
  (barrer_fijo.py:326-348) y documentada (capitulo3.tex:723-725), pero no se disparó en el plan:
  ningún log `plan2/cola/logs/barrido_*.log` tiene «AVISO». La figura la muestra como parte del
  método. ¿Se aclara en el texto?
- **Q3.** CLAUDE.md:19 y :31 siguen diciendo que el cruce de Lima se «limpió en netedit», y el
  Anexo D dice que no. Las figuras siguen al Anexo D; habría que corregir CLAUDE.md.
- **Q4.** Los tabulares no cierran la última decisión al terminar el episodio (rl_corredor.py:372);
  las redes sí (rl_ippo.py:643-659). La figura de U2 lo muestra («D, P: cierran la última
  decisión»), pero el texto no lo dice.
- **Q5.** rl_corredor.py observa y luego calcula la recompensa (298, 300-307); rl_ippo.py cierra y
  luego observa (557-558). Pasa en el mismo instante y las figuras muestran el orden de
  `rl_ippo.py`.
- **Q6.** Resuelta en la revisión: la fase del mensaje se escribe «avenida, transversal o ámbar»,
  como la tesis (capitulo3.tex:323-324). En el código es EO/NS, y EO es siempre la fase de avenida
  (rl_ippo.py:329-332).
- **Q7.** Las tablas tab:plan2-resumen y tab:plan2-metas las genera plan2/tablas_cap5.py, que no
  aparece en el texto ni en el Anexo B. No se dibuja.

---

## 6. Lista de comprobación para quien dibuje cada figura

1. El preámbulo es el de §1.1, con `\input{estilo_diagramas}` y `\unidad{...}`. No hay `\ref`,
   `\cite`, `\scriptsize`, `\tiny`, `scale` ni `\resizebox`.
2. Los textos de nodos, aristas y puertos se copian **literalmente** de las tablas de §3, con sus
   saltos de línea, y cada nodo lleva el `text width` de la columna «Ancho». Las interfaces se
   escriben con `\itf`, `\itfn` o `\itfnn`.
3. Se compila con `cd TESIS/diagramas && python construir.py <nombre>`. El resultado debe dar
   15.0 cm de ancho, escala 1.00 y un alto ≤ 13 cm (arquitectura) o ≤ 20 cm (unidades).
4. Revisión de `previa/<nombre>.png` a 150 dpi:
   - Ningún texto tocado por una línea y ningún nodo encimado.
   - Las marcas quedan sobre el borde del nodo, sin tapar su título.
   - Las flechas entran en el nodo correcto.
   - Las etiquetas quedan junto a su flecha.
   - Solo hay los cruces que la figura declara, con corte blanco.
   - La leyenda no se sale de los 15 cm.
5. Revisión en blanco y negro (`pdftoppm -gray`): los títulos de unidad se leen, y la línea
   discontinua, la punteada y la gruesa se distinguen.
6. Cada flecha I del dibujo coincide con la matriz de §2, cada interfaz lleva su nombre una vez
   (o en el pie), y los nodos comunes de U2 y U4 tienen la misma etiqueta y el mismo orden.
7. En el log de pdflatex no hay *overfull* en nodos con `\texttt` (si lo hay, se parte la ruta a
   mano). Si se cambia un texto, se vuelve a medir con `scratchpad/revision/medir.sh`.
8. La especificación dice qué se integra en la tesis: la figura con `\includegraphics[width=\textwidth]{diag_<nombre>.pdf}`
   en `\begin{figure}[H]`, el pie y la etiqueta de §3, la frase que la cita, el párrafo de las
   interfaces (§3.1), el renombre de las filas de tab:pipeline (D1, con aprobación del autor) y
   los TODO que hay que borrar (capitulo3.tex:71, capitulo2.tex:14-18 y capitulo4.tex:575). Para
   Overleaf hay que subir `images/diag_*.pdf`.

---

## 7. Registro de la revisión

Revisión del 27.09.2026 con dos críticas: fidelidad (16 puntos y una nota de coherencia) y
claridad (32 puntos). Cada punto de fidelidad se verificó contra el código antes de aplicarlo;
los 16 se confirmaron. Los anchos se midieron con pdflatex y el estilo real
(`scratchpad/revision/medir.sh`); la copia previa de esta especificación quedó en
`scratchpad/revision/especificacion_antes_de_revision.md`.

### 7.1 Crítica de fidelidad

| # | Punto | Verificación | Qué se hizo |
|---|---|---|---|
| F1 | `med` atribuía colas y retornos a `comun.py` | Confirmado: colas y `ret_*` en `correr_episodio` (rl_corredor.py:331-346,376-389; rl_ippo.py:605-620,665-681); `comun.py` da `leer_tripinfo` y `MedidorEnlaces` (35, 180) | Aplicado: «(`comun.py` y `correr_episodio`)»; nueva D11 sobre tab:pipeline |
| F2 | U3: flujos de corredor por el puerto I2 hacia las lecturas TraCI | Confirmado: los usa `comun.leer_tripinfo` (rl_corredor.py:376; rl_ippo.py:665; comun.py:71-83) | Aplicado: I2 entra a Lecturas (aproximaciones y enlaces) y el `tripinfo` cita «flujos de extremo a extremo (\itf{2})»; catálogo y matriz corregidos |
| F3 | U4: los críticos no actúan «al final del episodio» | Confirmado: V en cada decisión (rl_ippo.py:570,594; rl_mappo.py:112-115,124); al final solo V del último estado si se cortó (rl_ippo.py:647-652; rl_mappo.py:127-133) | Aplicado: críticos fuera del subgrupo final, aristas c_* → tray «$V$ al decidir», pie reescrito, evidencia 112-113 |
| F4 | U4: faltaba cerrar la decisión y cómo se llena la trayectoria | Confirmado: `cerrar_pendiente` antes de `observar` (557) y `append` tras muestrear (588-594) | Aplicado: nodo «Cerrar la decisión anterior» entre decide y obs; arista elegir → tray |
| F5 | U3: el veredicto tiene dos etapas | Confirmado: PENDIENTE con motivo si faltan bases, evaluación o comparaciones (veredicto.py:390-410); la convergencia se mira al final (131-137, 411) | Aplicado: dec1 «¿Datos completos?» antes de la regla y dec2 «¿Base convergida?» después |
| F6 | U3: faltaba el actuado | Confirmado: veredicto solo frente al fijo, sin bases (veredicto.py:364-373) | Aplicado: línea «(actuado: solo frente al fijo)» en la regla y frase en el pie |
| F7 | U2 y U4: faltaba el arranque de SUMO y la validación corre en SUMO | Confirmado (rl_corredor.py:232-242,397-404; rl_ippo.py:449-456,753-763) | Aplicado: arista Iniciar → SUMO («\itf{1}») y «arranca SUMO (\itf{1}) con su semilla»; Validación dice «un episodio por semilla» y cita \itf{6} |
| F8 | U2: «P: guarda la transición» antes de elegir no vale para IPPO | Confirmado (rl_ippo.py:524,561-567,588-594) | Aplicado: act «P: anota $r_i$»; elegir «P: muestrea; anota $o$, $a$, $\log\pi$, $V$» |
| F9 | U2: el orden del ajuste no es el del código para D y P | Confirmado (rl_corredor.py:476; rl_dqn.py:299; rl_ippo.py:875-877; rl_mappo.py:240-242) | Aplicado con otra forma: el ajuste pasa a la rama «sí» de ¿k < N?, donde el efecto es exacto para T, D y P (nota de verificación en §3.3); el pie dice «de la exploración o de la tasa» |
| F10 | I8 no enumeraba «= vecinos» | Confirmado (veredicto.py:454-462; veredicto_matriz.tex:18) | Aplicado en el catálogo |
| F11 | I3 «por suscripción» no vale para todo | Confirmado (rl_corredor.py:150,160-161,352) | Aplicado: «casi todas por suscripción», con las lecturas directas nombradas |
| F12 | `sumo → trip` omitía los no terminados | Confirmado (rl_corredor.py:233; comun.py:70) | Aplicado: «por viaje; no terminados al cierre» y pie de U3 |
| F13 | La regla usa el IC95 *bootstrap* de Δ | Confirmado (veredicto.py:334-337; consolidar.py:97-104) | Aplicado en regla y cons |
| F14 | Solo se amplían los ejes de verde | Confirmado (barrer_fijo.py:27-30,326-348,443-444) | Aplicado: «¿Ganador en el borde de un eje de verde?», «sí: se amplía el eje» y «no, o techo de 60 s» |
| F15 | Faltaba el reloj propio del agente | Confirmado (rl_ippo.py:548-555) | Aplicado: «sí: cada 5 s de su verde» en U2 y U4 |
| F16 | Quién dispara el actuado | Confirmado (generar_trabajos.py:78-81; evaluar.py:173-180; rl_corredor.py:235-237) | Aplicado: act_f «`comun.py`, al evaluar el actuado (`evaluar.py`)»; D3 ampliada. La arista pasa a salir de net (con la crítica C16), sin nombre de trabajo |
| — | Coherencia: flechas continuas con «\itf{7}» | Confirmado | Aplicado: sin número, «una fila por semilla» |

### 7.2 Crítica de claridad

| # | Aplicado o descartado | Detalle |
|---|---|---|
| C1 | Aplicado | Títulos solo con el nombre de la unidad; alcance al pie; la clave de marcas de U2 pasa a una tercera fila de leyenda (14.45 cm) |
| C2 | Aplicado | Todas las líneas de §3 medidas y reescritas para caber; columna «Ancho» en cada tabla de nodos; regla de 1 a 3 líneas con cinco excepciones nombradas |
| C3 | Aplicado | Los nombres de I1, I3 e I4 van en el nodo SUMO; las flechas llevan solo `\itf` |
| C4 | Aplicado | El pie de la arquitectura cita las cuatro figuras una por una (§0.2) |
| C5 | Aplicado como condición previa | El renombre de las filas de tab:pipeline es un cambio de texto: queda en D1 y en §6.8, para que lo apruebe el autor |
| C6 | Descartado | El orden propuesto (elegir antes de actualizar) es falso para Q-learning y DQN: los dos actualizan antes de elegir y la elección usa la Q ya actualizada (rl_corredor.py:308-320; rl_ippo.py:561-567,581; rl_dqn.py:169-179). Se mantiene el orden y se precisa SARSA e IPPO en los detalles (F8) |
| C7 | Aplicado | Pasos de U2 en naranja dentro de U4; `actor` pasa a «Elegir: mantener o cambiar»; violeta solo para reloj, mensaje, observación extendida y crítico central, y marcas violetas «*spill*» |
| C8 | Aplicado | «(metadatos)» en lugar de «(meta)» |
| C9 | Aplicado | Párrafo de interfaces obligatorio; regla de nombre completo una vez por figura, o en el pie (§1.5); `\itfnn` para dos líneas; P_U2 dice «publicación de la política (\itf{7})», sin la validación |
| C10 | Aplicado | Orden red, dem, ref, tab; colector de I1 bajo los tres primeros; I2 desde tab sin cruces |
| C11 | Aplicado | «\itf{5} (DQN)» sale de agente i |
| C12 | Aplicado | Igual que la nota de coherencia |
| C13 | Aplicado (se quita) | Se quita el subgrupo Variantes; la matriz alternativa no cabía (unos 2.6 cm de alto) y repetía tab:plan2-modelos. Lo cubren las marcas y el pie |
| C14 | Aplicado, más allá de lo pedido | Canal y buzón se funden, y además con el mensaje, en un solo nodo violeta; su control vuelve a decide y una sola flecha I5 va a Observar; la etiqueta «no, o IPPO local» pasa a «sí (no en IPPO local)» / «no» |
| C15 | Aplicado | El término *spill* se acumula en Avanzar y se aplica en Cerrar, con «recompensa» en las dos figuras |
| C16 | Aplicado | Subgrupos Red vial, Demanda y Programas de referencia; sin nombres de trabajo ni n_cola; `preparar.py` en cfg; net → act_f por el margen izquierdo. El fijo de partida queda en el detalle de cfg y del barrido |
| C17 | Aplicado | caso → tabla «semáforos y vecinos»; P_I1 y P_I2 abajo |
| C18 | Aplicado | P_I2 entra a Lecturas por el este |
| C19 | Aplicado | U3 se estrecha a 10.8 cm y los puertos pasan a 4.0 cm; I1, I3 e I4 quedan en una línea |
| C20 | Aplicado | `\hyphenpenalty=10000` en el estilo `diagrama`; la prueba ya no corta palabras |
| C21 | Aplicado | Estilos `hacia abajo` y `hacia arriba`; «desde Uk» / «hacia Uk» siempre |
| C22 | Aplicado | La leyenda dice «simulador SUMO» |
| C23 | Aplicado | Pies reescritos con los rombos, las flechas gruesas, los puertos, la base publicada con I7, la rama PENDIENTE y el color |
| C24 | Aplicado | Demanda «escalada en P2 y P4»; med corto (con la corrección F1); sin «31 o 53» en la arquitectura; «cada 5 s» bajo la flecha doble; `s_ent` sin bases; marcas T, «D, P» y P. Además, la nota de protocolo pasa al pie porque no cabía |
| C25 | Aplicado | Vocabulario de §1.2 (valor de validación, control, la más probable, IC95\,\%, avenida y transversal, programa estático por omisión, veredicto provisional, Iniciar, «envía», eje de verde); nombres de función por `comun.py` o `correr_episodio` |
| C26 | Aplicado | Ajuste «T, D: baja ε · P: baja la tasa»; sin minilote en U2; los números de PPO solo en U4 |
| C27 | Aplicado | I6 = métricas, I7 = política, en estilo, catálogo, matriz y figuras (D12) |
| C28 | Descartado | Los puertos «U2 y U4» siguen en gris: es el gris de la barra «aprendices de U2 y U4» de la arquitectura, y el naranja diría «solo U2». El texto «hacia U2 y U4» / «hacia Cap. V» los distingue |
| C29 | Aplicado | Marcas centradas sobre la esquina superior derecha del nodo (§1.4) |
| C30 | Aplicado | `tripinfo` y su lectura en un solo nodo; «:» en lugar de «→» en Lecturas |
| C31 | Aplicado | La métrica (\itf{6}) se cita en Validación y se quita de P_U2 |
| C32 | Aplicado | Etiqueta de metadatos encima de su flecha e I8 debajo, a 0.5 cm |

### 7.3 Cambios fuera de esta especificación

- `TESIS/diagramas/estilo_diagramas.tex` (archivo nuevo de esta tarea, sin versionar): nombres de
  I6 e I7 intercambiados; macro `\itfnn` con el nombre en dos líneas; `\hyphenpenalty=10000` en
  `diagrama`; estilos `hacia abajo` y `hacia arriba`; texto de leyenda «simulador SUMO».
- `scratchpad/diagramas/prueba_estilo.tex`: prueba de los puertos verticales, `\itfnn` y la marca
  sobre el borde; recompilada (`prueba_estilo-1.png`, `prueba_gris-1.png`), sin cortes de palabra.

### 7.4 Cambios propios de la revisión (por los anchos medidos o por los cruces)

- U2: el puerto de U4 (I5) y el de U3 (I6) pasan a citas en Observar y en Cierre, y la tercera
  fila de leyenda lleva las marcas; así el alto baja a unos 19.4 cm y desaparece un cruce.
  «Iniciar el episodio $k$» se estrecha a 3.0 cm para que `s_ent` quepa a su lado, y la vuelta
  $k + 1$ entra por arriba, uniéndose a la flecha ini → lanzar.
- En todas: `eval_<esc>_<control>.csv` en lugar de `<brazo>`, por el vocabulario de C25.
- U3: los nodos Veredicto y PENDIENTE pasan a etiquetas de las salidas de dec2; P_I1 va a la
  derecha, con I3 e I4; `s_eval` va en la fila del subtítulo «Evaluación».
- U4: el puerto I2 pasa a cita en el mensaje (su nombre, al pie); P_U2 va debajo de SUMO; los dos
  bucles se trazan por la derecha para encerrar lo que ocurre en cada decisión y en cada segundo.
  Quedan tres cruces declarados, que desaparecen si se quita la flecha tray → gae (prescindible).
- Arquitectura: el recuadro U4 se rehízo (etiqueta I5 a la izquierda de los agentes, variantes a
  todo el ancho) y la nota de protocolo pasa al pie.
