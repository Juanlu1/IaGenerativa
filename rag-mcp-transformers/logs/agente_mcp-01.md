# Corrida del benchmark — agente con tools por MCP (parte 3)

- **Fecha:** 2026-10-01 22:34:12
- **Modelo:** `deepseek/deepseek-v4-flash-0731` por OpenRouter, temperatura 0
- **Preguntas:** `datos/preguntas_agente_dev.jsonl` (12)
- **Salida:** `respuestas_mcp.jsonl`
- **Herramientas:** descubiertas con `tools/list` en `servidor_mcp.py` (stdio) y cargadas con `langchain-mcp-adapters`
- **Consumo de la key (`GET /api/v1/key`):** USD 0.112497 antes, USD 0.115284 después, diferencia USD 0.002788
- **Totales:** 24 llamadas al modelo, 39375 tokens de entrada, 2531 de salida (856 de razonamiento), costo USD 0.003665

## Herramientas que vio el modelo

- `buscar_documentos`: Busca en los documentos del hospital, que tienen las normas y los procedimientos que casi no cambian: horarios y reglas de visita de cada sector, quién puede acompañar o quedarse con un paciente, preparación para estudios y cirugías, requisitos y documentación para turnos, internación, alta y retiro de medicamentos, coberturas, niveles de triage de la guardia y sus tiempos máximos, vacunas, donación de sangre, accesos y derechos del paciente. Usala para cualquier pregunta sobre cómo funciona el hospital, qué hay que llevar o qué está permitido. No conoce el estado de hoy (camas libres, quién está de guardia, turnos disponibles, stock de farmacia, espera actual). 'consulta' es una pregunta completa sobre un solo tema, escrita con las mismas palabras que usó el paciente (el buscador funciona mejor con preguntas de pacientes que con términos técnicos) y nombrando el sector, estudio o trámite concreto; por ejemplo: '¿Cómo se pide una consulta por telemedicina?'. Devuelve los fragmentos más relevantes, separados por '---'. Si la pregunta del paciente tiene dos temas, hacé una búsqueda por cada tema.
- `consultar_camas`: Estado de las camas de un sector de internación en este momento: total, ocupadas y libres. 'sector' es el nombre del sector, por ejemplo 'pediatria', 'terapia intensiva' o 'maternidad'. Si el sector no existe, la respuesta trae la lista de sectores válidos para reintentar. No conoce las reglas de internación ni de acompañantes: eso está en los documentos.
- `consultar_guardia`: Profesionales que están de guardia hoy en una especialidad, con el horario de cada uno (por ejemplo 08:00-20:00 de día y 20:00-08:00 de noche). 'especialidad' es el nombre de la especialidad, por ejemplo 'cardiologia' o 'pediatria'. Si no existe, la respuesta trae la lista de especialidades válidas para reintentar.
- `consultar_turnos`: Próximos turnos disponibles (fecha y hora) para atenderse por consultorio en una especialidad, ordenados del más cercano al más lejano. 'especialidad' es el nombre de la especialidad, por ejemplo 'traumatologia' o 'dermatologia'. Si no existe, la respuesta trae la lista de especialidades válidas para reintentar. No conoce qué hay que llevar al turno ni cómo se pide: eso está en los documentos.
- `consultar_farmacia`: Stock de un medicamento en la farmacia del hospital hoy y, si no hay, la fecha de reposición. 'medicamento' es el nombre con su presentación, por ejemplo 'amoxicilina 500 mg' o 'salbutamol aerosol'. Si el nombre no coincide, la respuesta trae la lista de medicamentos válidos para reintentar con el nombre exacto. No conoce los requisitos para retirar un medicamento: eso está en los documentos.
- `consultar_espera`: Minutos de espera en la guardia en este momento, para cada nivel de triage (rojo, naranja, amarillo, verde, azul). No recibe parámetros. No conoce el tiempo máximo que fija la norma para cada nivel: eso está en los documentos.

## Resumen por pregunta

| Pregunta | Herramientas | Llamadas al modelo | Tokens entrada | Tokens salida | Razonamiento | Costo USD |
|---|---|---|---|---|---|---|
| A01 | buscar_documentos | 2 | 3261 | 143 | 39 | 0.000218 |
| A02 | buscar_documentos | 2 | 3270 | 203 | 27 | 0.000295 |
| A03 | buscar_documentos | 2 | 3219 | 228 | 120 | 0.000327 |
| A04 | buscar_documentos | 2 | 3287 | 251 | 38 | 0.000357 |
| A05 | consultar_camas | 2 | 3190 | 113 | 37 | 0.000179 |
| A06 | consultar_guardia | 2 | 3226 | 132 | 49 | 0.000204 |
| A07 | consultar_turnos | 2 | 3211 | 107 | 31 | 0.000172 |
| A08 | consultar_farmacia | 2 | 3213 | 172 | 73 | 0.000255 |
| A09 | consultar_espera, buscar_documentos | 2 | 3388 | 282 | 134 | 0.000398 |
| A10 | consultar_camas, buscar_documentos | 2 | 3324 | 272 | 81 | 0.000384 |
| A11 | consultar_turnos, buscar_documentos | 2 | 3335 | 257 | 86 | 0.000365 |
| A12 | consultar_farmacia, buscar_documentos | 2 | 3451 | 371 | 141 | 0.000512 |
| **Total** | | 24 | 39375 | 2531 | 856 | 0.003665 |

## A01 — ¿Cuál es el horario de visita en neonatología para los abuelos?

### Llamada al modelo 1

- generation id: `gen-1790904853-bpl2ILfBz7Rt5rESNXDe`
- usage: 1548 tokens de entrada, 99 de salida (39 de razonamiento), costo USD 0.000143

**Herramienta:** `buscar_documentos({"consulta": "¿Cuál es el horario de visita en neonatología para los abuelos?"})`

Resultado:

```text
Régimen de visitas — Neonatología
Madre y padre tienen ingreso libre las 24 horas. Los abuelos pueden visitar martes y jueves de 16:00 a 17:00, uno por vez y con la presencia de uno de los padres. Los hermanos del recién nacido no ingresan al sector durante la temporada de virus respiratorios, de mayo a septiembre.
```

### Llamada al modelo 2

- generation id: `gen-1790904860-otodKEEaUFXqD1YiRJrc`
- usage: 1713 tokens de entrada, 44 de salida (0 de razonamiento), costo USD 0.000075

### Respuesta

```text
En neonatología, los abuelos pueden visitar **martes y jueves de 16:00 a 17:00**, uno por vez y con la presencia de uno de los padres.
```

## A02 — ¿Qué preparación necesita una colonoscopía?

### Llamada al modelo 1

- generation id: `gen-1790904863-8almeGD5E49kcy7WyX53`
- usage: 1540 tokens de entrada, 80 de salida (27 de razonamiento), costo USD 0.000119

**Herramienta:** `buscar_documentos({"consulta": "¿Qué preparación necesita una colonoscopía?"})`

Resultado:

```text
Preparación para estudios de diagnóstico por imágenes y endoscopía — Colonoscopía
Los tres días previos se sigue una dieta sin residuos: sin frutas, verduras, legumbres ni cereales integrales. La tarde anterior se toma la solución evacuante de polietilenglicol, cuatro litros repartidos en cuatro horas. Desde la medianoche solo se permiten líquidos claros, y el ayuno total es de 6 horas antes del turno. El paciente tiene que venir acompañado, porque el estudio se hace con sedación.
```

### Llamada al modelo 2

- generation id: `gen-1790904867-iDrle9Y8WQi3AH2hZWYK`
- usage: 1730 tokens de entrada, 123 de salida (0 de razonamiento), costo USD 0.000176

### Respuesta

```text
Para una colonoscopía, la preparación es la siguiente:

- **3 días previos:** dieta sin residuos (sin frutas, verduras, legumbres ni cereales integrales).
- **Tarde anterior:** tomar 4 litros de solución evacuante de polietilenglicol, repartidos en 4 horas.
- **Desde la medianoche:** solo líquidos claros.
- **Ayuno total:** 6 horas antes del turno.
- **Acompañante:** debe venir acompañado, porque el estudio se hace con sedación.
```

## A03 — ¿Qué documentos tengo que llevar a la primera consulta con un especialista?

### Llamada al modelo 1

- generation id: `gen-1790904872-KuGqwmM2fltn1ufP6Mpp`
- usage: 1546 tokens de entrada, 166 de salida (120 de razonamiento), costo USD 0.000229

**Herramienta:** `buscar_documentos({"consulta": "¿Qué documentos hay que llevar a la primera consulta con un especialista?"})`

Resultado:

```text
Turnos en consultorios externos — Qué llevar a la primera consulta
DNI, credencial de la cobertura de salud, la derivación y los estudios previos relacionados con el motivo de consulta, en papel o en el teléfono.
```

### Llamada al modelo 2

- generation id: `gen-1790904878-0CHqDl97fxzJNYw3UfTf`
- usage: 1673 tokens de entrada, 62 de salida (0 de razonamiento), costo USD 0.000097

### Respuesta

```text
Para la primera consulta con un especialista tenés que llevar:

- **DNI**
- **Credencial de la cobertura de salud**
- **La derivación**
- **Los estudios previos** relacionados con el motivo de consulta (en papel o en el teléfono)
```

## A04 — ¿Quiénes pueden donar sangre?

### Llamada al modelo 1

- generation id: `gen-1790904881-DtKWQsdASMipmihEiTxB`
- usage: 1538 tokens de entrada, 94 de salida (38 de razonamiento), costo USD 0.000137

**Herramienta:** `buscar_documentos({"consulta": "¿Quiénes pueden donar sangre?"})`

Resultado:

```text
Donación de sangre
El servicio de hemoterapia recibe donantes de lunes a sábado de 7:30 a 12:00, en el primer piso.

Pueden donar personas de 18 a 65 años que pesen más de 50 kilos y se sientan bien. No hay que venir en ayunas: se recomienda un desayuno liviano, sin lácteos ni grasas. Entre una donación y la siguiente tienen que pasar al menos 2 meses en los hombres y 3 meses en las mujeres.

No pueden donar por 12 meses quienes se hicieron un tatuaje o un piercing en ese período.
```

### Llamada al modelo 2

- generation id: `gen-1790904885-KOnVF5cLnc4SSMz6Ezqy`
- usage: 1749 tokens de entrada, 157 de salida (0 de razonamiento), costo USD 0.000220

### Respuesta

```text
Según los documentos del hospital, pueden donar sangre:

- **Personas de 18 a 65 años** que pesen **más de 50 kilos** y se sientan bien.
- No hay que venir en ayunas: se recomienda un desayuno liviano, sin lácteos ni grasas.
- Entre donación y donación deben pasar al menos **2 meses en hombres** y **3 meses en mujeres**.
- **No pueden donar por 12 meses** quienes se hicieron un tatuaje o piercing en ese período.

El servicio de hemoterapia recibe donantes de lunes a sábado de 7:30 a 12:00, en el primer piso.
```

## A05 — ¿Hay camas libres en terapia intensiva ahora?

### Llamada al modelo 1

- generation id: `gen-1790904888-qGAztqIReTWzMf8KvjEn`
- usage: 1541 tokens de entrada, 86 de salida (37 de razonamiento), costo USD 0.000127

**Herramienta:** `consultar_camas({"sector": "terapia intensiva"})`

Resultado:

```text
{"sector": "terapia_intensiva", "fecha": "2026-10-05", "datos": {"total": 12, "ocupadas": 12, "libres": 0}}
```

### Llamada al modelo 2

- generation id: `gen-1790904890-nULO19rVUNoymGYgu2Ka`
- usage: 1649 tokens de entrada, 27 de salida (0 de razonamiento), costo USD 0.000052

### Respuesta

```text
No, en este momento no hay camas libres en terapia intensiva: las 12 camas están ocupadas.
```

## A06 — ¿Quién está de guardia en cardiología esta noche?

### Llamada al modelo 1

- generation id: `gen-1790904892-mWrDvHnx61vY6rLsd3tG`
- usage: 1542 tokens de entrada, 96 de salida (49 de razonamiento), costo USD 0.000140

**Herramienta:** `consultar_guardia({"especialidad": "cardiologia"})`

Resultado:

```text
{"especialidad": "cardiologia", "fecha": "2026-10-05", "datos": [{"profesional": "Dr. Julián Ferreyra", "horario": "08:00-20:00"}, {"profesional": "Dra. Paula Benítez", "horario": "20:00-08:00"}]}
```

### Llamada al modelo 2

- generation id: `gen-1790904895-XImLTBjZOExCMEYhg6QZ`
- usage: 1684 tokens de entrada, 36 de salida (0 de razonamiento), costo USD 0.000064

### Respuesta

```text
Esta noche (guardia nocturna de 20:00 a 08:00) en cardiología está de guardia la **Dra. Paula Benítez**.
```

## A07 — ¿Cuándo es el próximo turno disponible con traumatología?

### Llamada al modelo 1

- generation id: `gen-1790904897-FNvEH5dSAKr1Xr3BlA0S`
- usage: 1543 tokens de entrada, 76 de salida (31 de razonamiento), costo USD 0.000114

**Herramienta:** `consultar_turnos({"especialidad": "traumatologia"})`

Resultado:

```text
{"especialidad": "traumatologia", "fecha": "2026-10-05", "datos": ["2026-10-07 08:40", "2026-10-07 09:00", "2026-10-08 14:20"]}
```

### Llamada al modelo 2

- generation id: `gen-1790904900-fYHa0cwTrBUIpzSyRClM`
- usage: 1668 tokens de entrada, 31 de salida (0 de razonamiento), costo USD 0.000058

### Respuesta

```text
El próximo turno disponible con traumatología es el **miércoles 7 de octubre de 2026 a las 08:40**.
```

## A08 — ¿Tienen enalapril de 10 mg en la farmacia?

### Llamada al modelo 1

- generation id: `gen-1790904903-0yolBzPaNwA7IyBk3JC8`
- usage: 1545 tokens de entrada, 105 de salida (52 de razonamiento), costo USD 0.000151

**Herramienta:** `consultar_farmacia({"medicamento": "enalapril 10 mg"})`

Resultado:

```text
{"medicamento": "enalapril 10 mg", "fecha": "2026-10-05", "datos": {"stock": 0, "unidad": "comprimidos", "reposicion": "2026-10-09"}}
```

### Llamada al modelo 2

- generation id: `gen-1790904908-e89gWDGomrGfuGFXTa4Z`
- usage: 1668 tokens de entrada, 67 de salida (21 de razonamiento), costo USD 0.000104

### Respuesta

```text
No, en este momento no hay stock de enalapril 10 mg en la farmacia. La reposición está prevista para el 09/10/2026.
```

## A09 — ¿Cuánto se está esperando hoy en la guardia si me clasifican como verde?

### Llamada al modelo 1

- generation id: `gen-1790904911-LOQe5kIkygaOaj5Vj24z`
- usage: 1550 tokens de entrada, 142 de salida (59 de razonamiento), costo USD 0.000199

**Herramienta:** `consultar_espera({})`

Resultado:

```text
{"fecha": "2026-10-05", "minutos_por_nivel": {"rojo": 0, "naranja": 7, "amarillo": 48, "verde": 135, "azul": 210}}
```

**Herramienta:** `buscar_documentos({"consulta": "¿Cuánto es el tiempo máximo de espera en la guardia para un paciente clasificado como verde?"})`

Resultado:

```text
Guardia y clasificación por prioridad (triage) — Los cinco niveles
- Nivel 1, rojo (resucitación): atención inmediata.
- Nivel 2, naranja (emergencia): atención en 10 minutos como máximo.
- Nivel 3, amarillo (urgencia): atención dentro de los 60 minutos.
- Nivel 4, verde (urgencia menor): atención dentro de las 2 horas.
- Nivel 5, azul (no urgente): atención dentro de las 4 horas, o derivación a consultorio externo.
```

### Llamada al modelo 2

- generation id: `gen-1790904918-Hqxql44067vGPMfeoLmR`
- usage: 1838 tokens de entrada, 140 de salida (75 de razonamiento), costo USD 0.000199

### Respuesta

```text
Hoy, si te clasifican como **verde** (urgencia menor), la espera en la guardia es de **135 minutos**.

Según la norma del hospital, el nivel verde debe atenderse dentro de las **2 horas (120 minutos)** como máximo, por lo que la espera actual supera ese tiempo.
```

## A10 — Quiero internar a mi nene en pediatría, ¿hay lugar y me puedo quedar con él?

### Llamada al modelo 1

- generation id: `gen-1790904926-03WmKzHEaE9N0eljrBH3`
- usage: 1554 tokens de entrada, 179 de salida (81 de razonamiento), costo USD 0.000246

**Herramienta:** `consultar_camas({"sector": "pediatria"})`

Resultado:

```text
{"sector": "pediatria", "fecha": "2026-10-05", "datos": {"total": 24, "ocupadas": 17, "libres": 7}}
```

**Herramienta:** `buscar_documentos({"consulta": "¿Puedo quedarme con mi hijo internado en pediatría?"})`

Resultado:

```text
Régimen de visitas — Pediatría
Madre, padre o tutor pueden permanecer las 24 horas junto al paciente. Para el resto de los familiares, la visita es de 17:00 a 19:00, con un máximo de dos personas.
```

### Llamada al modelo 2

- generation id: `gen-1790904928-MDt8IGjF6bPdf3Lqhi2o`
- usage: 1770 tokens de entrada, 93 de salida (0 de razonamiento), costo USD 0.000138

### Respuesta

```text
Sí, hay lugar en pediatría: hay 24 camas en total, 17 ocupadas y 7 libres.

Y sí, podés quedarte con tu nene: en pediatría, la madre, el padre o el tutor pueden permanecer las 24 horas junto al paciente. El resto de los familiares puede visitar de 17:00 a 19:00, con un máximo de dos personas.
```

## A11 — Necesito turno con cardiología, ¿cuál es el primero y qué tengo que llevar?

### Llamada al modelo 1

- generation id: `gen-1790904930-fa9mIfKjNroQKFwUoox7`
- usage: 1551 tokens de entrada, 160 de salida (63 de razonamiento), costo USD 0.000222

**Herramienta:** `consultar_turnos({"especialidad": "cardiologia"})`

Resultado:

```text
{"especialidad": "cardiologia", "fecha": "2026-10-05", "datos": ["2026-10-14 09:30", "2026-10-14 10:00", "2026-10-16 15:00"]}
```

**Herramienta:** `buscar_documentos({"consulta": "¿Qué tengo que llevar a un turno de cardiología por consultorio?"})`

Resultado:

```text
Turnos en consultorios externos — Qué llevar a la primera consulta
DNI, credencial de la cobertura de salud, la derivación y los estudios previos relacionados con el motivo de consulta, en papel o en el teléfono.
```

### Llamada al modelo 2

- generation id: `gen-1790904935-AdGpTysfTcWmLwsXQDRe`
- usage: 1784 tokens de entrada, 97 de salida (23 de razonamiento), costo USD 0.000143

### Respuesta

```text
El primer turno disponible en cardiología es el **14 de octubre de 2026 a las 09:30**.

Para la primera consulta tenés que llevar:
- DNI
- Credencial de la cobertura de salud
- La derivación
- Los estudios previos relacionados con el motivo de consulta (en papel o en el teléfono)
```

## A12 — Me recetaron insulina NPH, ¿la tienen y qué necesito para retirarla?

### Llamada al modelo 1

- generation id: `gen-1790904939-v9KqipJbngEJybu1M5t2`
- usage: 1550 tokens de entrada, 161 de salida (63 de razonamiento), costo USD 0.000223

**Herramienta:** `consultar_farmacia({"medicamento": "insulina NPH"})`

Resultado:

```text
{"medicamento": "insulina NPH", "fecha": "2026-10-05", "datos": {"stock": 0, "unidad": "frascos", "reposicion": "2026-10-12"}}
```

**Herramienta:** `buscar_documentos({"consulta": "¿Qué necesito para retirar un medicamento de la farmacia?"})`

Resultado:

```text
Farmacia del hospital
La farmacia de pacientes ambulatorios está en planta baja, junto a admisión, y atiende de lunes a viernes de 8:00 a 20:00. Entrega medicación a pacientes del hospital con receta de un profesional de la institución.

Para retirar medicación se presenta el DNI del paciente. Si retira otra persona, lleva su propio DNI y el del paciente.

Los medicamentos de alto costo, como los oncológicos y los biológicos, requieren un formulario de solicitud firmado por el especialista y aprobado por el comité de farmacia, que se reúne los miércoles.

La farmacia no hace entregas los fines de semana. Las recetas tienen una validez de 30 días desde la fecha de emisión.
```

### Llamada al modelo 2

- generation id: `gen-1790904945-GOvKK4roYG0BF1naunRY`
- usage: 1901 tokens de entrada, 210 de salida (78 de razonamiento), costo USD 0.000289

### Respuesta

```text
**Stock de insulina NPH:** Hoy no hay stock en la farmacia (0 frascos). La reposición está prevista para el **12/10/2026**.

**Para retirarla necesitás:**
- Receta de un profesional de la institución (validez de 30 días desde su emisión).
- DNI del paciente. Si retira otra persona, debe llevar su propio DNI y el del paciente.

La farmacia ambulatoria está en planta baja, junto a admisión, y atiende de lunes a viernes de 8:00 a 20:00.
```
