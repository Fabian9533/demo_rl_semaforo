# Cronograma del plan 3

05.11.2026. Versión final. Supone las recomendaciones de `DECISIONES.md` y el trabajo "escalonado a ciegas":

- cada bloque entra a la cola la noche del día en que su código queda listo;
- nadie abre resultados decisivos hasta el cierre;
- "día" es una jornada de trabajo de Fabian con Claude; "noche" es una ventana de 10 h con 12 procesos (~120 h-p).

Las cargas salen de `costos_plan3.py`, en esta carpeta (salida en `costos_plan3_salida.txt`). El modelo simula la cola
como `plan3/cola.py`: cuando se libera un proceso lanza el trabajo listo de mayor prioridad (referencias primero,
después lo más largo) que alcance a terminar antes del corte. Respeta las dependencias, incluidas las cadenas.

**Régimen de base: conservador + 10 %.** Es la velocidad medida la noche del plan v2 (18 entrenamientos pesados a la
vez) más un 10 % por empaquetado [S]. El central (carga moderada) va al lado. Se cambió porque el central de P6 salió
de una tanda con 7.2 trabajos a la vez, y las noches del plan corren 12 en 8 núcleos [M
`critica_codigo/salidas/concurrencia_exploratorio.txt`].

## Respuesta corta

| | Conservador + 10 % (base) | Central |
|---|---|---|
| Cómputo | ~1901 h-p, ~159 h de reloj | ~1506 h-p, ~126 h |
| Noches con trabajo | 17 (días 4 a 20) | 15 (días 4 a 18) |
| Código | ~18-19 días; termina el día 19 | igual |
| Cierre (`cierre.ok`) | día 21 | día 20 |
| Fin del análisis | día 22 | día 21 |
| Fin de la escritura y revisión | día 27 | día 26 |
| **Total** | **~27 días** | **~26 días** |

**Por qué el borrador decía 18-19 días.**
- Contaba ~11 días de código, pero sus propias tareas sumaban 12.9-14.4, sin el generador de trabajos ni los pasos que
  eligen la versión evaluada [M, suma de las tareas de PLAN3].
- Usaba el régimen central y llenaba cada noche al 100 %.
- No tenía las piezas de A4 ni las correcciones de las críticas.

**Lo que manda es el código.** Cada día de atraso en el código corre el final un día. El cómputo extra casi no lo mueve:
las noches que el código igual tiene que esperar se llenan con entrenamientos largos.

## Código: suma de las tareas

| Bloque | Tareas de `PLAN3.md` | Días | Listo el día |
|---|---|---|---|
| Infraestructura | 0.1 respaldo, 0.2 worktrees y tag, 0.3 insumos, 0.4 cola y protecciones, 0.5 registro | 1.95 | 2 |
| Entrenamiento | 1.1 opciones de `rl_ippo`, 1.2 reanudación y sus pruebas, 0.18 generador (parte 1), 0.13 parte A | 2.0 | 4 |
| Escenarios y C0 | 0.6 escenarios nuevos, 1.4 C0 | 1.1 | 5 |
| Etapa 3 | 3.1 observación, 3.2-3.3 limpiezas y entropía, 3.4 reloj de 2 s, 3.5 completo y promoción, 0.18 (parte 2) | 2.65 | 8 |
| Referencias | 0.7 barrido fino, 0.8 franja, 0.9 actuado, 0.10 regla y MP, 0.11 preparar, 0.12 no regresión, 0.18 (parte 3) | 3.55 | 12 |
| Evaluación | 0.14 `evaluar3`, 0.15 manifiesto, 0.19 pasos de elección, 0.18 (parte 4), 0.16 chequeos, 0.17 parte B | 1.85 | 14 |
| Perfil y mezcla | 2.4, 2.5 | 1.5 | 16 |
| Política por red | Etapa 4 | 1.0 | 17 |
| `veredicto3` | 5.0 | 2.0 | 19 |
| **Total** | | **~17.6 (18-19 con imprevistos)** | |

[I] Las estimaciones salen de los informes de cada área, con los prototipos ya probados.

## Día por día (régimen conservador; entre paréntesis, central)

| Día | Código y pruebas | Fabian | Noche: qué corre | Carga h-p |
|---|---|---|---|---|
| 0 | — | **Decide A1-A8.** Pausa Windows Update y la suspensión | — | — |
| 1 | 0.1 respaldo; 0.2 worktrees y tag `entregado-2026-10-25`; 0.3 insumos; 0.4 cola y protecciones | Revisa el respaldo | — | — |
| 2 | 0.4 (fin, con la prueba de `taskkill`); 0.5 registro de escenarios | — | — | — |
| 3 | 1.1 opciones de `rl_ippo`; 1.2 reanudación | — | — | — |
| 4 | 1.2 pruebas (P1 y P6: 20 = 10 + 10); 0.18 generador (entrenamientos); 0.16 chequeos; 0.13 parte A | **Commit, push, tag y correo de la parte A** | V2 regular (P1-P6, niveles, D, 2715), ablación, V2 sin mensajes | 117 (116) |
| 5 | 0.6 escenarios nuevos y números comunes con `best`; 1.4 C0 | — | + llegadas aleatorias (V2 con y sin mensajes), P6e, C0, 400 episodios | 118 (118) |
| 6 | 3.1 observación cercana | — | Etapas 1, 2 y 3b | 118 (118) |
| 7 | 3.2 limpiezas; 3.3 entropía; 3.4 reloj de 2 s | — | Etapas 1, 2 y 3b | 118 (113) |
| 8 | 3.5 completo y promoción; 0.18 generador (Etapa 3) | — | **Etapa 3** (D primero): observación, limpiezas, entropía, reloj, completo | 118 (119) |
| 9 | 0.7 barrido fino | — | Etapa 3 | 120 (120) |
| 10 | 0.7 (fin); 0.8 franja | — | Etapa 3 | 119 (119) |
| 11 | 0.9 actuado ajustado; 0.10 regla y MP | — | Etapa 3 | 117 (35) |
| 12 | 0.11 preparar; 0.12 no regresión; 0.18 generador (referencias) | — | **Referencias** (regulares, niveles, D, P6e y aleatorias), con prioridad | 120 (120) |
| 13 | 0.14 `evaluar3`; 0.15 manifiesto | Comprueba que las referencias terminaron | Referencias (resto) y Etapa 3 | 115 (41) |
| 14 | 0.19 pasos de elección; 0.18 generador (evaluaciones); 0.16; 0.17 parte B | **Commit, push, tag y correo de la parte B** | **Evaluaciones decisivas** | 120 (120) |
| 15 | 2.4 perfil | — | Evaluaciones | 120 (120) |
| 16 | 2.5 mezcla | — | Perfil, mezcla y evaluaciones | 120 (120) |
| 17 | Política por red; piloto de humo del β | **Commit de la enmienda del β** | Política por red y lo pendiente | 120 (120) |
| 18 | 5.0 `veredicto3` | — | Lo pendiente | 120 (8) |
| 19 | 5.0 (fin y pruebas); esqueleto del anexo con datos sintéticos | — | Lo pendiente | 120 (—) |
| 20 | Análisis en seco (central: cierre) | (Central: crea `cierre.ok`) | Últimas evaluaciones de la política por red | 3 (—) |
| 21 | 5.1 cierre; 5.2 `veredicto3 --final` | **Crea `cierre.ok`** | — | — |
| 22 | Análisis; lista de lo que se cita; enmienda de la prueba final si hace falta | Decide qué se cita; `holdout.ok` si hace falta | Prueba final, solo si se usa (~22 h-p, ~2 h) | — |
| 23-26 | 5.4 escritura: anexo nuevo y sección corta del Cap. V | Revisa el borrador | — | — |
| 27 | Revisión final; zonas protegidas, una por una | Confirma; fusiona `plan3` con commit de fusión | — | — |

**Cada mañana** (5-10 min): Fabian mira solo el resumen (terminados, fallidos y bloqueados), hace commit y push del
manifiesto con los sha256 de lo decisivo y, si algo falló, se diagnostica con el error, nunca con resultados.

## Carga por noche (h-proceso)

| Noche del día | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Conservador + 10 % | 117 | 118 | 118 | 118 | 118 | 120 | 119 | 117 | 120 | 115 | 120 | 120 | 120 | 120 | 120 | 120 | 3 |
| Central | 116 | 118 | 118 | 113 | 119 | 120 | 119 | 35 | 120 | 41 | 120 | 120 | 120 | 120 | 8 | — | — |

**Qué ocupa cada noche (conservador):**

| Noche del día | Carga por etapa (h-p) |
|---|---|
| 4 | Etapa 1: 117 |
| 5 | Etapa 2: 102; 3b: 15 |
| 6 | Etapa 1: 55; 3b: 53; Etapa 2: 10 |
| 7 | Etapa 1: 77; 3b: 24; Etapa 2: 16 |
| 8-11 | Etapa 3: 107-118 por noche |
| 12 | Referencias: 120 |
| 13 | Referencias: 41; Etapa 3: 65; resto: 9 |
| 14-16 | Evaluaciones de las Etapas 1, 2, 3 y 3b; perfil y mezcla |
| 17-18 | Política por red: 47 y 14; evaluaciones |
| 19 | 3b: 61; Etapas 2 y 3: 44; resto: 15 |
| 20 | Política por red: 3 |

## Cómputo por etapa (h-proceso)

| Etapa | Conservador + 10 % | Central |
|---|---|---|
| 0 Referencias | 161 | 161 |
| 1 V2 regular, C0, ablación, sin mensajes, niveles | 451 | 354 |
| 2 Llegadas aleatorias, perfil, mezcla | 374 | 310 |
| 3b 400 episodios (regulares y aleatorias) | 172 | 136 |
| 3 Observación, limpiezas, reloj de 2 s, completo, promoción | 669 | 495 |
| 4 Política por red | 73 | 49 |
| **Total sin la prueba final** | **1901** | **1506** |
| Prueba final (si se usa) | 22 | 19 |

## Variantes y cuánto mueven el calendario

| Variante | h-p (conservador) | Última noche | Código termina | Total |
|---|---|---|---|---|
| Recomendada | 1901 | 20 (solo 3 h-p) | día 19 | ~26-27 |
| Sin las piezas de A4 | 1342 | 17 | día 18 | ~25 |
| Sin A4 y sin Etapa 4 | 1268 | 16 | día 17 | ~24 |
| Sin reloj de 2 s | 1735 | 18 | día 18-19 | ~25-26 |
| Sin modelo completo ni promoción | 1563 | 18 | día 19 | ~26 |
| Modelo completo con 200 episodios | 1753 | 18 | día 19 | ~26 |
| 3 bases en el modelo principal | 1800 | 19 | día 19 | ~26 |
| Validación con 8 semillas | 1552 | 18 | día 19 | ~26 |
| 60 semillas por tanda con llegadas aleatorias | 1785 | 19 | día 19 | ~26 |
| Etapa 4 solo corredores | 1883 | 19 | día 20 | ~27 |
| Etapa 4 con las dos | 1956 | 20 | día 21 | ~28 |
| Cola también de día cuando la PC está libre | 1901 | antes | día 19 | ~26 |
| Referencias primero (orden del borrador) | 1901 | 22 | día 19 | ~29 |

Notas:
- "Total" = cierre al día siguiente de lo último (código o noche), más 2 días de análisis, 4 de escritura y 1 de
  revisión.
- Las variantes que no tocan el código casi no mueven el total: el código termina el día 19 y el cómputo el 18-20.
  En la recomendada, la noche del día 20 solo tiene 3 h-p; si corren antes, el total es ~26.
- El orden importa: poner las referencias primero, como el borrador, deja noches vacías y termina 2 noches después [I
  `orden_codigo_salida.txt`].

## Supuestos del cronograma

- **Días de código** [I]: los de la tabla de arriba, con los prototipos ya probados.
- **Rendimiento:** 11.95 h-p por hora de reloj con 12 procesos [M, noche dem2].
- **Empaquetado:** +10 % en el conservador [S].
- **Duraciones supuestas** [S]:
  - observación nueva ×1.35 por episodio (medido +27-34 %);
  - mezcla ×1.10;
  - reloj de 2 s ×1.4 al entrenar y ×1.15 al jugar (la regla reactiva midió ×1.1-1.2 al jugar);
  - política por red: 23 s por episodio en la malla en el central (×1.66 en el conservador), 10 en la red y 5.8 en el
    corredor.
- **Tramos:** todo entrenamiento de más de 5 h se parte con `--reanudar`; el modelo completo con llegadas aleatorias en
  P6 son 6 tramos por base en el conservador.
- **La cola corre solo de noche, con `--hasta`.** Si Fabian libera la PC de día, el cómputo termina antes; el código no.
- **Análisis:** 2 días. **Escritura:** 4 días más 1 de revisión.
- **Disco:** sobra [M/I infra]: 258 GB libres; los checkpoints y archivos de estado del bloque ocupan del orden de
  0.2-1 GB; lo versionado crece ~40-65 MB; los tripinfo se borran cada mañana.
