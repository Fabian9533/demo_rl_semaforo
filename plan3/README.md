# plan3: segundo estudio (mejorar los resultados)

Bloque nuevo, posterior a lo entregado el 25.10.2026 (tag `entregado-2026-10-25`, commit 81378fb). Corre todas las
etapas del plan sin puertas, a ciegas y con prerregistro. Las decisiones A1-A8 se tomaron el 05.11.2026 (todas las
recomendadas); las técnicas B1-B25 van por defecto.

- Plan, decisiones y calendario: `doc/PLAN3.md`, `doc/DECISIONES.md`, `doc/CRONOGRAMA.md`.
- Reglas que deciden: `PRERREGISTRO.md` (parte A antes de la primera noche).
- Informes del diseño (pruebas de factibilidad, prototipos y críticas), fuera del repositorio:
  `C:/Users/GAMER/Documents/demo_rl_semaforo/analisis_mejora_2026-11-04/plan3/`. En los documentos de `doc/`, una
  ruta `plan3/<área>/...` (demanda, referencias, modelo, veredicto, infra, critica_resultados, final) apunta ahí.

## Reglas para todo el código

1. **Nada escribe en `plan2/` ni en `TESIS/`.** `git diff main...HEAD -- plan2 TESIS` debe quedar vacío siempre.
2. **Lo entregado se modifica en el lugar con las opciones apagadas por defecto.** Con todo apagado, el resultado es
   idéntico al entregado (pruebas de identidad y de no regresión).
3. **Todo corre con `cwd = plan3/`**, como `plan2/` con su cola: los scripts de la raíz se llaman `../rl_ippo.py`,
   `../evaluar.py`, `../barrer_fijo.py`; los propios del bloque viven en `plan3/`.
4. **Escenarios nuevos** (llegadas aleatorias, P6e, perfil, mezcla) se registran en `escenarios_plan3.py` (raíz) y
   solo existen dentro del proceso que lanza `con_escenarios.py`:
   `python ../con_escenarios.py <programa> [argumentos]`, con `<programa>` relativo a `plan3/`
   (p. ej. `../rl_ippo.py` o `evaluar3.py`). Nunca se agregan a `escenarios_plan2.DERIVADOS` en disco.
5. **Nombres propios:** todo entrenamiento lleva `--etiqueta p3<...>`; ningún archivo nuevo puede llamarse como uno
   entregado.
6. **Semillas:** solo las de su uso, según la tabla JSON de `PRERREGISTRO.md` §3. Las pruebas de desarrollo usan humo
   (base 7, semillas 424301-424360) o no regresión (1001-1002, solo con controles entregados).
7. **A ciegas:** las tandas decisivas escriben en `plan3/ciego/` (fuera de git) y sus logs no muestran métricas.
8. **Commits:** a nombre de Fabian, sin línea de coautor.

## Carpetas

| Carpeta o archivo | Qué guarda | ¿En git? |
|---|---|---|
| `*.sumocfg`, `*.net.xml`, `*.rou.xml`, `*.add.xml` | Escenarios (copiados de `plan2/` por `p3_insumos.py` o generados) | sí |
| `insumos/` | Copias de lo entregado con su manifiesto (políticas, CSV del puente) | sí, salvo checkpoints |
| `checkpoints/` | Checkpoints y estados de los entrenamientos | no (respaldo cada mañana) |
| `resultados_*.csv`, `politica_*.pt` | Curvas y políticas publicadas | sí |
| `barridos/`, `referencias_congeladas.json` | Ajuste de las referencias | sí |
| `parciales/` | Evaluaciones no decisivas (humo, puente, promoción) | sí |
| `ciego/` | Evaluaciones decisivas (T1, T2, extensión de H1, prueba final) | no, hasta `listo/cierre.ok` |
| `cola/` | Lista de trabajos, estado, logs y manifiesto ciego | sí, salvo los archivos de control |
| `listo/` | Marcas (`cierre.ok`, `holdout.ok`) | sí |
| `tmp_*/` | Temporales de barridos y pruebas | no |
