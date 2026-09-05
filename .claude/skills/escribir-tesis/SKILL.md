---
name: escribir-tesis
description: Llevar a los .tex de la tesis (TESIS/, plantilla UTEC) cualquier hallazgo, resultado, cambio de metodo, metrica, escenario o decision de diseno, y corregir lo ya escrito cuando queda desactualizado. Usar cada vez que se produzca un resultado citable, se toque la formulacion RL o el plan de pruebas, se agregue una grafica o tabla, se cambie un baseline, se agregue una referencia, o se detecte que el documento dice algo que el codigo ya no hace.
---

# Escribir en la tesis

Regla del proyecto (pedido del asesor, reunion 28.08.2026): todo avance vive en la
plantilla de tesis, no en documentos sueltos. Jerarquia de registros:
- `resultados_<esc>.csv`: dato crudo, siempre.
- `TESIS/secciones/*.tex`: registro oficial, en el mismo turno en que se produce el
  hallazgo. Un resultado que no esta en el .tex no existe para la tesis.
- `LEEME.txt` y `CLAUDE.md`: notas de trabajo; nunca el unico lugar de un numero.

El usuario compila en Overleaf; en esta maquina no hay LaTeX.

## 0. Antes de editar (salvaguardas)

- Copia maestra. Confirmar con el usuario que `TESIS/` esta al dia con Overleaf
  antes del primer cambio. Al terminar, listar los archivos exactos que debe
  resubir. Una sola sesion edita `TESIS/` a la vez.
- Respaldo. Antes del primer cambio de la sesion copiar `main.tex`,
  `referencias.bib` y `secciones/` a `respaldo_tesis/<AAAA-MM-DD_HHMM>/` (fuera de
  `TESIS/`, para que no suba a Overleaf). En el reporte final, `diff -u` por
  archivo contra ese respaldo.
- Zonas protegidas. Su contenido solo se cambia con confirmacion previa, mostrando
  el texto propuesto: `resumen.tex`, `abstract.tex`, metas y objetivos de
  `introduccion.tex`, `capitulo1.tex`, captions de figuras del autor. Las
  correcciones puramente LaTeX (simbolo no soportado, mayuscula de imagen, entorno
  roto) si se hacen, y se reportan.
- No editar `tesisutec.cls` ni los paquetes de `main.tex`. En particular nunca
  cargar `subcaption`, `subfig` ni `cleveref`: los dos primeros chocan con el
  paquete `subfigure` que carga la clase (el contador ya existe y el entorno no se
  define) y `cleveref` redefine `\cref`, `\sref`, `\aref` y `\eref` de la clase.
- Lo provisional no entra al .tex. Solo se escribe lo evaluado con el protocolo de
  semillas de la seccion 6. Si hay que dejar constancia de un numero provisional,
  va como comentario `% PROVISIONAL: <comando que lo regenera>`, que el validador
  cuenta como aviso.

## 1. Mapa de la plantilla

`main.tex` incluye, en este orden: resumen, abstract, introduccion, capitulo1,
capitulo2, capitulo3, capitulo4, capitulo5, conclusiones, recomendaciones,
bibliografia (IEEEtran + natbib numerico), anexos. Los capitulos numerados se
cuentan por orden de aparicion y el nombre del archivo NO coincide con el numero:

| Archivo | Capitulo en el PDF | Contenido |
|---|---|---|
| introduccion.tex | sin numero | metas, objetivos U1-U4, alcance, metricas de evaluacion |
| capitulo1.tex | I | estado del arte (Uniandes 2023, Trinity 2022, UAQ 2024), revision critica, implicancias de diseno |
| capitulo2.tex | II | marco teorico: arquitectura U1-U4, definiciones |
| capitulo3.tex | ninguno | VACIO (0 lineas). No escribir aqui sin avisar |
| capitulo4.tex | III | marco metodologico: U1 (OSM, netedit, demanda) y U2 (formulacion RL, ciclo, Q-learning) |
| capitulo5.tex | IV | RESULTADOS. Conectado en main.tex el 04.09.2026; mientras solo tenga `\chapter{}` genera una pagina con el titulo y nada mas |
| conclusiones.tex | sin numero | solo el encabezado `\customchapter{CONCLUSIONES}`, sin contenido |
| recomendaciones.tex | sin numero | placeholder Lorem ipsum |
| anexos.tex | sin numero | placeholder de una linea |

`recomendaciones.tex` y `anexos.tex` traen el `\chapter*` escrito a mano (tres
lineas: `\chapter*`, `\addcontentsline`, `\markboth`); al reemplazar el placeholder
conservar esas lineas o sustituirlas por `\customchapter{...}`.

Que va donde:

| Contenido nuevo | Archivo y seccion |
|---|---|
| Meta, objetivo, metrica de evaluacion, alcance | introduccion.tex, la `\introsection` correspondiente (zona protegida) |
| Definicion de un concepto en una frase (retraso, espera detenida, throughput, episodio, spillback) | capitulo2.tex, "Definiciones y conceptos fundamentales". Separar retraso (timeLoss: tiempo de viaje menos tiempo a flujo libre) de espera detenida (waitingTime: segundos con velocidad menor o igual a 0.1 m/s); hoy estan juntos |
| Trabajo relacionado o referencia nueva; cambio en la lista de algoritmos o en el diseno de U4 | capitulo1.tex (estado del arte, revision critica, implicancias) y el mismo cambio en introduccion.tex, resumen.tex, abstract.tex y capitulo2.tex, que hoy repiten la lista |
| Escenario: red, demanda, programa fijo tuneado (verde, offset), programa actuado (`tlLogic type="actuated"` con minDur/maxDur iguales al verde min/max del agente), ambar | capitulo4.tex, seccion U1: subseccion "Escenarios sinteticos de prueba" con tabla de escenarios (carriles, fases, demanda por periodo, verde tuneado, offset, ambar) |
| Formulacion RL implementada, hiperparametros, restricciones, definicion operativa de episodio (una hora de demanda mas vaciado de la red, tope 6000 s; N episodios con semilla 42+ep; la Q-table persiste entre episodios), schedule de epsilon y por que N episodios | capitulo4.tex, "Desarrollo del modulo U2" |
| Algoritmo nuevo (SARSA, DQN, PPO): hiperparametros y arquitectura | capitulo4.tex U2, una subseccion por algoritmo; resultados en la seccion final de capitulo5 con la misma tabla de metricas y las mismas semillas |
| Como se mide cada metrica (tripinfo, TraCI, device de emisiones, definicion de throughput) | capitulo4.tex, nueva seccion "Modulo U3: medicion" |
| Plan de pruebas: casos, factores, brazos, semillas, metrica primaria, pruebas estadisticas, decisiones de diseno con su justificacion | capitulo4.tex, nueva seccion "Plan de pruebas" al final del capitulo |
| U4: mensajeria, estado extendido, spillback, IPPO | capitulo4.tex, nueva seccion "Modulo U4"; resultados en capitulo5. El mismo diseno esta descrito en capitulo1.tex (implicancias), capitulo2.tex e introduccion.tex: mantener los cuatro iguales |
| Resultados: tablas por caso, por episodio, evaluacion por semillas, figuras, hallazgos positivos y negativos | capitulo5.tex, una `\section` por prueba y una final de comparacion entre escenarios y entre algoritmos |
| Herramientas y entorno real (SUMO 1.25, Python 3.14, librerias usadas, sin GPU, tiempo por episodio) | introduccion.tex "Areas de investigacion y herramientas", capitulo4.tex tabla `tab:hw`, anexos |
| Conclusion o recomendacion que ya se puede sostener | conclusiones.tex / recomendaciones.tex |
| Scripts completos, tablas largas, listados de parametros | anexos.tex |
| Cambio de metas o de resultado principal | ademas: resumen.tex y abstract.tex (zona protegida) |

## 2. Disparadores (cuando hay que escribir)

- Corrida que se va a citar: tabla o figura en capitulo5 con semillas, episodios y
  configuracion, mas 2-5 frases de interpretacion. Solo con el protocolo de
  semillas de la seccion 6; una corrida de una semilla es provisional.
- Cambio de formulacion o hiperparametro: capitulo4 U2, `CLAUDE.md` (seccion
  Formulacion RL), `LEEME.txt` y las cabeceras de `rl_semaforo.py` y
  `rl_corredor.py`, a la vez.
- Metrica nueva: definicion en capitulo2, medicion en capitulo4 U3, columna en capitulo5.
- Escenario nuevo, baseline nuevo o re-tuneado: tabla de escenarios en capitulo4 U1
  y seccion en capitulo5.
- Referencia o trabajo relacionado nuevo: entrada en el .bib y parrafo en capitulo1.
- Cambio de codigo que afecta reproducibilidad (flag, columnas del CSV, semillas):
  capitulo4 (U2 o plan de pruebas) y anexos.
- PNG regenerado: reemplazar el archivo en `TESIS/images/` con el mismo nombre y
  revisar que el caption siga siendo cierto.
- Numero nuevo en `CLAUDE.md` o `LEEME.txt`: no puede quedarse solo ahi; o va a
  capitulo5 con su protocolo, o se marca como provisional.
- Cambio de alcance (por ejemplo, si el cruce real de Lima no entra en Tesis 2):
  introduccion.tex (alcance), capitulo1.tex, resumen y abstract, con confirmacion.
- Hallazgo que contradice el documento: corregir el texto existente (seccion 4),
  nunca agregar un parrafo que conviva con el anterior.

## 3. Convenciones LaTeX de esta plantilla

- Texto en espanol con tildes (inputenc utf8 + babel spanish). Identificadores de
  codigo y labels sin tildes.
- Solo son seguros en UTF-8 los caracteres del bloque Latin-1 (tildes, enie, signos
  de apertura, grados, mas/menos) y la puntuacion tipografica (guiones largos,
  comillas, puntos suspensivos). Cualquier otro simbolo va en modo matematico o
  como comando: `$\geq$`, `$\leq$`, `$\approx$`, `$\varepsilon$`, `$\times$`,
  `\textrightarrow`. pdflatex descarta los simbolos crudos sin detener la
  compilacion en Overleaf: las metas de la introduccion perdieron el "mayor o
  igual" asi. El validador lo marca como error.
- babel lleva `es-nodecimaldot`: sin esa opcion babel-spanish convierte el punto de
  `$0.95$` en coma en modo matematico; con ella el punto se conserva. En modo
  texto babel nunca toca los numeros. Escribir siempre con punto decimal (9.30) y
  no quitar la opcion de la clase. Porcentajes con `\%`; un `%` sin escapar
  convierte el resto de la linea en comentario sin ningun error.
- Numeracion: automatica y en arabigo con el numero de capitulo (Tabla 3.2,
  Figura 3.1, seccion 3.1); solo la cabecera del capitulo sale en romano
  (CAPITULO III). Nunca escribir un numero de tabla o figura a mano: siempre
  `Tabla~\ref{tab:x}`, `Figura~\ref{fig:x}`, `Seccion~\ref{sec:x}`. No usar
  `\fref`, `\tref`, `\cref`, `\sref`, `\aref`, `\eref` de la clase (salen en
  ingles). La palabra "Tabla" (no "Cuadro") y los prefijos de los indices los
  pone la clase; no tocarlos desde los .tex.
- Tablas: `\begin{table}[H]`, `\centering`, booktabs (`\toprule`, `\midrule`,
  `\bottomrule`), `\caption{}` despues del tabular y `\label{tab:nombre}` despues
  del caption (un label antes del caption toma el numero de la seccion). Unidades
  en la cabecera (s/veh, veh). Tablas anchas: `\small` o tabularx. Tablas de mas
  de una pagina: `longtable` no esta cargado; hay que pedir al usuario agregar
  `\usepackage{longtable}` a main.tex y usar ese entorno sin `table`.
- Figuras: `\begin{figure}[H]`, `\centering`, `\includegraphics[width=...]{nombre}`
  (graphicspath es `images/`, no repetirlo en las secciones; el nombre debe
  coincidir EXACTO en mayusculas con el archivo porque Overleaf es Linux), caption
  que diga que representa cada elemento (puntos, banda, linea) y sus unidades,
  `\label{fig:nombre}` despues del caption. Los PNG que genera `graficar.py` se
  copian a `TESIS/images/` con nombre descriptivo, 150 dpi minimo.
- Dos imagenes lado a lado: la clase carga el paquete antiguo `subfigure`, que
  define el comando `\subfigure` y NO el entorno (el entorno es de subcaption, que
  no se puede cargar aqui). Receta:
  ```
  \begin{figure}[H]
    \centering
    \subfigure[Texto a.]{\includegraphics[width=0.48\textwidth]{A.png}}
    \hfill
    \subfigure[Texto b.]{\includegraphics[width=0.48\textwidth]{B.png}}
    \caption{Caption general.}
    \label{fig:nombre}
  \end{figure}
  ```
  Las subfiguras salen como (a) y (b) en tamano scriptsize.
- No usar `\paragraph{}` como titulillo: con tocdepth=6 entra en el indice
  general. Usar `\noindent\textbf{Titulo.}` en linea o `\subsection*{}`.
- Citas: `\citep{Clave}`. Ver las claves existentes con `grep "^@" referencias.bib`
  antes de agregar una. Fuente nueva: usar el tipo BibTeX que corresponda
  (`@article`, `@inproceedings`, `@book`, `@mastersthesis`; `@misc` solo para
  paginas web, con `howpublished = {\url{...}}`, `year` y `note`), con claves
  del estilo `ApellidoAnio_Tema`. IEEEtran abrevia todos los nombres salvo el
  ultimo token: apellidos compuestos como `{Apellido1 Apellido2, Nombre}` e
  instituciones entre doble llave `{{SUMO Project}}`; si no, salen "J. D. C. Mass"
  y "S. Project".
- Ecuaciones: `\[ \]` o `equation` con `\label{eq:}`. La formula de la
  recompensa esta en capitulo4 U2 pero incompleta (sin pesos ni definicion TraCI
  de cada termino): completarla ahi, ponerle `\label{eq:recompensa}` y referirse
  a ella desde capitulo5.
- Codigo: `verbatim` para fragmentos cortos (asi esta el resto del documento);
  scripts completos van a anexos con fecha y version de SUMO. El pseudocodigo
  actual de capitulo4 U2 (traci.load por episodio, paso de 1 s, sin verde minimo)
  se sustituye por el bucle real de `correr_episodio` recortado a 25-30 lineas
  con las mismas variables del script.
- Capitulos sin numero: `\customchapter{TITULO}`. Secciones de la introduccion:
  `\introsection{Titulo}`.
- Redaccion: mismo tono del documento (impersonal: "se propone", "se observa"),
  frases cortas, sin lenguaje de IA, sin listas donde corresponde prosa. Cada
  numero con su unidad, su semilla o numero de replicas y su fuente (comentario
  `% fuente: <csv o script>` junto a la tabla). Los resultados negativos se
  reportan igual que los positivos y con su explicacion.
- Nunca inventar un numero: todo valor sale de `resultados_<esc>.csv`, de un
  tripinfo o de un script del proyecto, y el texto o el anexo dice como
  regenerarlo.

## 4. Modificar texto existente

Cuando un hallazgo contradice lo escrito:

1. Localizar todas las frases afectadas: `grep -n` en `secciones/` por la palabra
   clave (por ejemplo "cada segundo", "1~s", "ajustar hiperpar", "25–40").
2. Reescribir en el mismo lugar y con el mismo tono. No dejar la version vieja ni
   notas tipo "actualizado" o "antes decia".
3. Revisar en cascada lo que dependa del cambio: introduccion (metas, metricas,
   alcance), resumen y abstract, capitulo1 (revision critica e implicancias),
   capitulo2 (definiciones), capitulo4 (metodo), capitulo5 (resultados),
   conclusiones.
4. Reportar al usuario, en una linea por cambio: archivo, seccion, que decia y que
   dice ahora, mas el `diff -u` contra el respaldo. El lo revisa y compila en
   Overleaf.

Divergencias conocidas al 05.09.2026 entre capitulo4.tex y el codigo, a corregir
en cuanto se escriba la seccion de resultados:
- Estado: el texto usa colas crudas por carril (`lane.getLastStepVehicleNumber`)
  y "tiempo transcurrido en la fase"; el codigo usa vehiculos detenidos por
  aproximacion (`edge.getLastStepHaltingNumber`) discretizados en 4 bins
  (0, 1-3, 4-8, mas de 8) mas el indice de fase verde. Con 4 fases son 1024
  estados: es la causa del techo de cruce2 y el argumento para DQN/PPO.
- Accion: el texto enumera tres tipos genericos; el codigo tiene dos (mantener o
  pasar a la siguiente fase verde, con ambar automatico de la duracion del programa).
- Recompensa: faltan los pesos w1 = 1.0 y w2 = 0.01; el texto define w_i como
  "tiempo de espera acumulado en esa cola" y el codigo usa `edge.getWaitingTime`
  (espera de los vehiculos presentes en ese paso); el ciclo dice "incremento del
  tiempo de espera total" y el codigo usa el nivel, no la diferencia.
- Decision: el texto dice "cada segundo" y avanza 1 s; el codigo decide cada 5 s
  con verde minimo 10 s (5 s en giros) y maximo 60 s, que el texto no menciona.
- Ciclo: el texto usa `traci.load` por episodio; el codigo hace `traci.start` y
  `traci.close`.
- "Ajustar hiperparametros al final de cada episodio segun las metricas": lo
  unico que cambia entre episodios es epsilon, con decaimiento geometrico fijo
  (0.9 hasta 0.05; 0.96 y 0.95 por flag); alpha = 0.1 y gamma = 0.9 no cambian.
- Desempate: Q inicializada en cero y desempate aleatorio con RNG sembrado en
  todos los modos; no esta escrito.
- Episodio: no define su duracion (una hora de demanda mas vaciado, tope 6000 s)
  ni cuantos hay ni por que.
- U1: el texto fija "un minimo de cuatro segundos de ambar" y los cuatro escenarios
  usan 3 s (decidir con el autor: regenerar con `--tls.yellow.time 4` y re-tunear,
  o corregir el texto); describe la demanda con `randomTrips.py` y los escenarios
  usan `<flow vehsPerHour>` por periodo escritos a mano, con llegadas equiespaciadas.
- Herramientas: el documento declara pandas, PyTorch, Docker y "entorno Gym";
  el codigo usa csv, TraCI directo, sin Gym ni GPU.
- Algoritmos: capitulo1 promete "PPO, A2C y DQN", el resto del documento
  "Q-learning, SARSA, DQN y PPO", y capitulo4 menciona DDPG. Unificar.

## 5. Validar sin compilar

```
cd TESIS
python validar_tex.py
```

Errores: llaves y entornos, `\ref` sin `\label`, citas sin entrada en el .bib,
imagenes ausentes o con mayusculas distintas, caracteres no soportados, entorno
subfigure o paquetes incompatibles, flotantes sin caption o con label antes del
caption, archivos que no son UTF-8. Avisos: secciones fuera de `main.tex` o
vacias, `\paragraph`, `%` sin escapar tras un numero, comentarios TODO o
PROVISIONAL, flotantes sin label. Debe terminar en 0 errores y con los avisos
leidos antes de reportar. Ademas, leer una vez el parrafo editado con lo que tiene
antes y despues (`sed -n`) para comprobar que fluye.

## 6. Decisiones de diseno vigentes (05.09.2026, pendientes de confirmar con el asesor)

- Metrica primaria: retraso = timeLoss medio por vehiculo (tripinfo `timeLoss`),
  que es la definicion de retraso de la tesis y de las metas. Secundarias: espera
  detenida (`waitingTime`), cola promedio y maxima, paradas por vehiculo
  (`waitingCount`), throughput (llegados antes de 3600 s), CO2 y NOx (device de
  emisiones). Nunca llamar "delay" a la espera detenida.
- Brazos de comparacion: tiempo fijo tuneado, actuado nativo de SUMO con las
  mismas restricciones del agente, y RL con politica congelada.
- Semillas: entrenamiento con semilla base 42 (el episodio k usa 42 + k);
  evaluacion con semillas 1001-1010, fuera del rango de entrenamiento y las mismas
  para los tres brazos. Reportar media, IC95 % y prueba pareada (Wilcoxon) o
  Mann-Whitney exacta.
- El baseline fijo se tunea por la metrica primaria. Los baselines de cruce,
  cruce2, corredor y red se tunearon por espera detenida antes de esta regla
  (LEEME.txt): re-barrer antes de citarlos.
- Llegadas: `vehsPerHour` (equiespaciadas; la semilla solo cambia el comportamiento
  de los conductores). Se declara como limitacion; llegadas Poisson
  (`period="exp(...)"`) quedan como nivel del plan de pruebas porque obligan a
  rehacer baselines y entrenamientos.
- Throughput no es medible en los escenarios actuales (demanda subsaturada); se
  dice en el plan de pruebas en vez de reportar una columna que siempre da lo mismo.

## 7. Procedimiento resumido

1. Salvaguardas de la seccion 0 (copia al dia, respaldo).
2. Producir el resultado con el skill `experimento-sumo` y registrarlo en el CSV.
3. Generar la figura o tabla; copiar el PNG a `TESIS/images/`.
4. Escribir en el .tex que corresponde (tabla de la seccion 1), con caption, label,
   fuente y una interpretacion de 2-5 frases.
5. Actualizar en cascada lo que quede desactualizado (seccion 4).
6. `python validar_tex.py` con 0 errores; reportar archivos, secciones, diff y la
   lista de archivos a resubir a Overleaf.
