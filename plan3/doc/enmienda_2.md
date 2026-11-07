# Enmienda 2 del plan 3: solo tráfico aleatorio, más un análisis regular simple

**Fecha:** 07.11.2026. **Decide:** Fabian Alvarado. **Se avisa por correo al asesor**, con el commit y el tag
`plan3-enmienda-2`.

**Datos a la vista al fijarla:**
- entrenamientos y validaciones;
- las referencias afinadas con semillas de ajuste;
- ninguna evaluación del examen: `plan3/ciego/` está vacío.

## 1. Qué cambia

El plan se queda con el tráfico aleatorio, que es el realista. Con llegadas regulares queda solo un análisis simple,
para comparar:
- la V2 regular de cada base (42, 2042, 4042, 14042 y 16042), el fijo afinado y el actuado afinado (su veto);
- en P1-P6 y P6e, con T1 y T2 regulares: 98 evaluaciones. Los entrenamientos ya están hechos.

Con eso se responde H6 (la ventaja frente al fijo, ¿es mayor con llegadas aleatorias?). Además se informa, por caso, la
etiqueta de la V2 regular frente al fijo afinado; en P6 y P6e son H3 y H3e.

Lo aleatorio necesita de lo regular solo esto, y se queda:
- los entrenamientos de la V2 regular, ya hechos: C0 con llegadas aleatorias y la V2 regular jugada con llegadas
  aleatorias (H0);
- P6e, con un tramo corriendo, para lo mismo en P6;
- las elecciones de la versión evaluada, que tardan segundos.

## 2. Qué sale

Salen 796 trabajos, todos pendientes al fijarla: ~234 h-proceso estimadas, unas 14 h de la PC. También sale la Etapa 4,
que todavía no estaba en la lista.

| Parte | Trabajos | Qué deja de responderse |
|---|---|---|
| Etapa 1: solo descuento, solo exploración y V2 local, con llegadas regulares | 30 | Cuál de las dos mejoras del modelo ayuda; H7r |
| Etapa 3 con llegadas regulares (2715, D y P2), con sus promociones y elecciones | 31 + 8 + 9 | H8a; H14 en D |
| Evaluaciones de H1 (120 semillas por tanda) | 66 | H1 y H2 |
| Resto del examen regular | 634 | H1, H2, H4 y H7r; la V2 aleatoria jugada con llegadas regulares; las demás referencias con llegadas regulares |
| Puente con lo entregado | 18 | La comparación directa con los resultados entregados |
| Etapa 4: una política por red | no estaba en la lista | H10 |

- La lista exacta, un id por línea, está en `plan3/doc/enmienda_2_quitados.txt`, y `generar_trabajos3.py` la aplica.
- Ningún trabajo hecho, corriendo o con llegadas aleatorias sale.
- Todo lo que queda tiene sus requisitos.
- Esperados del examen: 767 CSV, antes 1493.
- Sin la Etapa 4, el β de su media móvil y sus tres niveles de validación ya no se fijan. El piloto de humo del β
  (base 7) se detuvo, y sus archivos se archivaron sin abrir.

**Siguen todas las preguntas con llegadas aleatorias:** H0, H5 (la principal), H6, H7, H8b, H9, H14, H15, el C0
aleatorio y las referencias.

## 3. Por qué

- Con llegadas regulares, el fijo afinado es muy difícil de vencer y la política aprende un reloj (diagnóstico del
  04.11). La pregunta de la tesis está en el tráfico aleatorio.
- Lo que sale cuesta unas 14 h de la PC más la Etapa 4, y solo respondía preguntas con llegadas regulares.
- H10 casi no podía pasar con la potencia disponible.

## 4. Desviación

La §14 del prerregistro solo permite enmiendas por errores de código, por trabajos que no se pueden correr o para fijar
lo ya anunciado. Esta va más allá, como la enmienda 1, así que se declara como desviación (`plan3/doc/desviaciones.md`
§5). Se fijó antes de correr ninguna evaluación del examen.
