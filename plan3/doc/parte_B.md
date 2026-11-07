# Prerregistro del plan 3, parte B

**Fecha:** 07.11.2026. **Decide:** Fabian Alvarado. **Se avisa por correo al asesor**, con el commit y el tag
`plan3-parte-B`.

**Datos a la vista al fijarla:**
- las referencias afinadas con semillas de ajuste (2001-2030);
- entrenamientos y validaciones;
- ninguna evaluación del examen: no existe ningún CSV de `plan3/ciego/`.

La parte A (tag `plan3-prerregistro-A`, 05.11.2026) dejó para esta parte solo dos cosas: las referencias ganadoras y
los valores de la mezcla de Lima. Ninguna regla cambia. Sigue vigente la enmienda 1 (`plan3/doc/enmienda_1.md`).

## 1. Referencias congeladas

`plan3/referencias_congeladas.json` lista las **154 referencias ganadoras** de los barridos, con el archivo y el sha256
de cada una:
- el fijo afinado al segundo, el de verdes de 5 en 5 y el fijo ajustado desde 10 s;
- el plan por franja y por bloques;
- el actuado ajustado;
- la regla simple, la regla reactiva y Max-Pressure.

Lo escribió `p3_congelar.py`, que antes comprobó cada archivo: 154 referencias, 0 con problemas.

Desde aquí:
- `evaluar3.py` no escribe en `ciego/` si la referencia que carga no coincide con su sha256 congelado;
- las evaluaciones decisivas de las referencias requieren este archivo;
- `chequeos_previos.py` compara cada tarde el disco con él.

## 2. Mezcla de Lima (A7, solo como sensibilidad)

| Clase | Cuota | Vehículos equivalentes |
|---|---|---|
| Auto y taxi | 78.928 % | 1.00 |
| Moto | 4.364 % | 1.0 (sin factor publicado) |
| Combi | 4.808 % | 1.25 |
| Micro | 5.641 % | 2.00 |
| Bus | 6.258 % | 3.00 |

- **Composición:** línea cortina del río Rímac.
  - Fuente: JICA y Nippon Koei (2013), *Encuesta de recolección de información básica del transporte urbano en el área
    metropolitana de Lima y Callao*, Tabla 2.16 (15 puentes, 24 h).
  - Sin camiones: 685 544 veh/día.
- **Reparto del transporte público:** flota regular de la ATU en 2021 (Lima Cómo Vamos, *Reporte urbano de
  indicadores de calidad de vida 2021*).
- **Equivalentes:** factores del INVERMET.
- **Demanda:** se multiplica por 1/1.1936 = 0.8378, para mantener los mismos vehículos equivalentes del caso.
- **Arranque lento:** solo se evalúa (`mixa_`): `startupDelay` de 0.5 s en los cinco tipos.
- **Detalle técnico:** clases de SUMO, largos y aceleraciones en `plan3/doc/informe_esc.md` §6.

## 3. Código de las referencias que corrió

Las referencias se afinaron con el código del commit `7714544`, no con el del tag de la parte A. Dos revisiones
corrigieron errores antes de correr ninguna referencia. La lista de archivos y las diferencias de comportamiento están
declaradas en `plan3/doc/desviaciones.md` §3.
