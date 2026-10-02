# Corrida del benchmark — agente con tools de LangChain (parte 2)

- **Fecha:** 2026-10-01 22:32:14
- **Modelo:** `deepseek/deepseek-v4-flash-0731` por OpenRouter, temperatura 0
- **Preguntas:** `datos/preguntas_agente_dev.jsonl` (12)
- **Salida:** `experimentos/agente/05-k1-palabras-del-paciente.jsonl`
- **Herramientas:** funciones de `herramientas.py`, en el mismo proceso
- **Consumo de la key (`GET /api/v1/key`):** USD 0.108832 antes, USD 0.111968 después, diferencia USD 0.003135
- **Totales:** 24 llamadas al modelo, 39183 tokens de entrada, 2532 de salida (917 de razonamiento), costo USD 0.003664

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
| A01 | buscar_documentos | 2 | 3261 | 135 | 32 | 0.000208 |
| A02 | buscar_documentos | 2 | 3270 | 205 | 28 | 0.000298 |
| A03 | buscar_documentos | 2 | 3220 | 166 | 50 | 0.000247 |
| A04 | buscar_documentos | 2 | 3287 | 250 | 26 | 0.000355 |
| A05 | consultar_camas | 2 | 3190 | 113 | 37 | 0.000179 |
| A06 | consultar_guardia | 2 | 3226 | 181 | 84 | 0.000267 |
| A07 | consultar_turnos | 2 | 3211 | 107 | 31 | 0.000172 |
| A08 | consultar_farmacia | 2 | 3213 | 186 | 89 | 0.000273 |
| A09 | consultar_espera | 2 | 3198 | 270 | 224 | 0.000380 |
| A10 | consultar_camas, buscar_documentos | 2 | 3324 | 272 | 81 | 0.000384 |
| A11 | consultar_turnos, buscar_documentos | 2 | 3332 | 263 | 92 | 0.000373 |
| A12 | consultar_farmacia, buscar_documentos | 2 | 3451 | 384 | 143 | 0.000529 |
| **Total** | | 24 | 39183 | 2532 | 917 | 0.003664 |

## A01 — ¿Cuál es el horario de visita en neonatología para los abuelos?

### Llamada al modelo 1

- generation id: `gen-1790904735-zgpjkqQbJYOXi1NZf09W`
- usage: 1548 tokens de entrada, 91 de salida (32 de razonamiento), costo USD 0.000133

**Herramienta:** `buscar_documentos({"consulta": "¿Cuál es el horario de visita en neonatología para los abuelos?"})`

Resultado:

```text
Régimen de visitas — Neonatología
Madre y padre tienen ingreso libre las 24 horas. Los abuelos pueden visitar martes y jueves de 16:00 a 17:00, uno por vez y con la presencia de uno de los padres. Los hermanos del recién nacido no ingresan al sector durante la temporada de virus respiratorios, de mayo a septiembre.
```

### Llamada al modelo 2

- generation id: `gen-1790904739-Ik4wixQAUk836wgqI7bN`
- usage: 1713 tokens de entrada, 44 de salida (0 de razonamiento), costo USD 0.000075

### Respuesta

```text
En neonatología, los abuelos pueden visitar **martes y jueves de 16:00 a 17:00**, uno por vez y con la presencia de uno de los padres.
```

## A02 — ¿Qué preparación necesita una colonoscopía?

### Llamada al modelo 1

- generation id: `gen-1790904741-TS7rp0mtHCXzBOnzirHM`
- usage: 1540 tokens de entrada, 82 de salida (28 de razonamiento), costo USD 0.000122

**Herramienta:** `buscar_documentos({"consulta": "¿Qué preparación necesita una colonoscopía?"})`

Resultado:

```text
Preparación para estudios de diagnóstico por imágenes y endoscopía — Colonoscopía
Los tres días previos se sigue una dieta sin residuos: sin frutas, verduras, legumbres ni cereales integrales. La tarde anterior se toma la solución evacuante de polietilenglicol, cuatro litros repartidos en cuatro horas. Desde la medianoche solo se permiten líquidos claros, y el ayuno total es de 6 horas antes del turno. El paciente tiene que venir acompañado, porque el estudio se hace con sedación.
```

### Llamada al modelo 2

- generation id: `gen-1790904745-zKpfD1uUtly0FNaY9iUQ`
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

- generation id: `gen-1790904750-3qqMkfunZVZS1F3bBrQD`
- usage: 1546 tokens de entrada, 104 de salida (50 de razonamiento), costo USD 0.000150

**Herramienta:** `buscar_documentos({"consulta": "¿Qué documentos tengo que llevar a la primera consulta con un especialista?"})`

Resultado:

```text
Turnos en consultorios externos — Qué llevar a la primera consulta
DNI, credencial de la cobertura de salud, la derivación y los estudios previos relacionados con el motivo de consulta, en papel o en el teléfono.
```

### Llamada al modelo 2

- generation id: `gen-1790904753-pcnB6QFU6pPSMB2F8kue`
- usage: 1674 tokens de entrada, 62 de salida (0 de razonamiento), costo USD 0.000097

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

- generation id: `gen-1790904756-9P3XuyWqy2TjFfmWk0OA`
- usage: 1538 tokens de entrada, 79 de salida (26 de razonamiento), costo USD 0.000118

**Herramienta:** `buscar_documentos({"consulta": "¿Quiénes pueden donar sangre?"})`

Resultado:

```text
Donación de sangre
El servicio de hemoterapia recibe donantes de lunes a sábado de 7:30 a 12:00, en el primer piso.

Pueden donar personas de 18 a 65 años que pesen más de 50 kilos y se sientan bien. No hay que venir en ayunas: se recomienda un desayuno liviano, sin lácteos ni grasas. Entre una donación y la siguiente tienen que pasar al menos 2 meses en los hombres y 3 meses en las mujeres.

No pueden donar por 12 meses quienes se hicieron un tatuaje o un piercing en ese período.
```

### Llamada al modelo 2

- generation id: `gen-1790904759-RchYyHahzeJjDsQT1vJV`
- usage: 1749 tokens de entrada, 171 de salida (0 de razonamiento), costo USD 0.000238

### Respuesta

```text
Según los documentos del hospital:

**Pueden donar sangre** las personas de **18 a 65 años** que pesen **más de 50 kilos** y se sientan bien.

Requisitos y condiciones:
- No hay que ir en ayunas: se recomienda un desayuno liviano, sin lácteos ni grasas.
- Entre donación y donación deben pasar al menos **2 meses** (hombres) y **3 meses** (mujeres).
- **No pueden donar por 12 meses** quienes se hayan hecho un tatuaje o piercing en ese período.

El servicio de hemoterapia recibe donantes de **lunes a sábado de 7:30 a 12:00**, en el primer piso.
```

## A05 — ¿Hay camas libres en terapia intensiva ahora?

### Llamada al modelo 1

- generation id: `gen-1790904764-3AV0hmYiID2JnD55ZV7N`
- usage: 1541 tokens de entrada, 86 de salida (37 de razonamiento), costo USD 0.000127

**Herramienta:** `consultar_camas({"sector": "terapia intensiva"})`

Resultado:

```text
{"sector": "terapia_intensiva", "fecha": "2026-10-05", "datos": {"total": 12, "ocupadas": 12, "libres": 0}}
```

### Llamada al modelo 2

- generation id: `gen-1790904768-91BgU9XSAoFWbbalGsh4`
- usage: 1649 tokens de entrada, 27 de salida (0 de razonamiento), costo USD 0.000052

### Respuesta

```text
No, en este momento no hay camas libres en terapia intensiva: las 12 camas están ocupadas.
```

## A06 — ¿Quién está de guardia en cardiología esta noche?

### Llamada al modelo 1

- generation id: `gen-1790904771-K57wfoQvKSJyMod7RV3N`
- usage: 1542 tokens de entrada, 78 de salida (29 de razonamiento), costo USD 0.000116

**Herramienta:** `consultar_guardia({"especialidad": "cardiologia"})`

Resultado:

```text
{"especialidad": "cardiologia", "fecha": "2026-10-05", "datos": [{"profesional": "Dr. Julián Ferreyra", "horario": "08:00-20:00"}, {"profesional": "Dra. Paula Benítez", "horario": "20:00-08:00"}]}
```

### Llamada al modelo 2

- generation id: `gen-1790904774-WAMicTNcpnn8cVEc0Q2n`
- usage: 1684 tokens de entrada, 103 de salida (55 de razonamiento), costo USD 0.000150

### Respuesta

```text
Esta noche (turno 20:00-08:00) está de guardia en cardiología la **Dra. Paula Benítez**.
```

## A07 — ¿Cuándo es el próximo turno disponible con traumatología?

### Llamada al modelo 1

- generation id: `gen-1790904778-rhkrtE62Esy4yFy4AK94`
- usage: 1543 tokens de entrada, 76 de salida (31 de razonamiento), costo USD 0.000114

**Herramienta:** `consultar_turnos({"especialidad": "traumatologia"})`

Resultado:

```text
{"especialidad": "traumatologia", "fecha": "2026-10-05", "datos": ["2026-10-07 08:40", "2026-10-07 09:00", "2026-10-08 14:20"]}
```

### Llamada al modelo 2

- generation id: `gen-1790904781-rztHzcUUkPlFYBTjTC13`
- usage: 1668 tokens de entrada, 31 de salida (0 de razonamiento), costo USD 0.000058

### Respuesta

```text
El próximo turno disponible con traumatología es el **miércoles 7 de octubre de 2026 a las 08:40**.
```

## A08 — ¿Tienen enalapril de 10 mg en la farmacia?

### Llamada al modelo 1

- generation id: `gen-1790904784-hdQdVnaPiBr0vtebonUi`
- usage: 1545 tokens de entrada, 118 de salida (68 de razonamiento), costo USD 0.000168

**Herramienta:** `consultar_farmacia({"medicamento": "enalapril 10 mg"})`

Resultado:

```text
{"medicamento": "enalapril 10 mg", "fecha": "2026-10-05", "datos": {"stock": 0, "unidad": "comprimidos", "reposicion": "2026-10-09"}}
```

### Llamada al modelo 2

- generation id: `gen-1790904790-IAmwkteXlDLBAMEdRLuV`
- usage: 1668 tokens de entrada, 68 de salida (21 de razonamiento), costo USD 0.000105

### Respuesta

```text
No, en este momento no hay stock de enalapril 10 mg en la farmacia. La reposición está prevista para el 9 de octubre de 2026.
```

## A09 — ¿Cuánto se está esperando hoy en la guardia si me clasifican como verde?

### Llamada al modelo 1

- generation id: `gen-1790904793-17VvM7AJ8qQSQwIsDehX`
- usage: 1550 tokens de entrada, 139 de salida (118 de razonamiento), costo USD 0.000195

**Herramienta:** `consultar_espera({})`

Resultado:

```text
{"fecha": "2026-10-05", "minutos_por_nivel": {"rojo": 0, "naranja": 7, "amarillo": 48, "verde": 135, "azul": 210}}
```

### Llamada al modelo 2

- generation id: `gen-1790904795-aH4hJ60Wmr9gx3xE9n1X`
- usage: 1648 tokens de entrada, 131 de salida (106 de razonamiento), costo USD 0.000185

### Respuesta

```text
Hoy (5 de octubre de 2026), si te clasifican como nivel verde en la guardia, la espera es de 135 minutos.
```

## A10 — Quiero internar a mi nene en pediatría, ¿hay lugar y me puedo quedar con él?

### Llamada al modelo 1

- generation id: `gen-1790904797-wALSpKuby9wMyszkIQhq`
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

- generation id: `gen-1790904800-mhqo9Fhua1Ky5EQPYZaf`
- usage: 1770 tokens de entrada, 93 de salida (0 de razonamiento), costo USD 0.000138

### Respuesta

```text
Sí, hay lugar en pediatría: hay 24 camas en total, 17 ocupadas y 7 libres.

Y sí, podés quedarte con tu nene: en pediatría, la madre, el padre o el tutor pueden permanecer las 24 horas junto al paciente. El resto de los familiares puede visitar de 17:00 a 19:00, con un máximo de dos personas.
```

## A11 — Necesito turno con cardiología, ¿cuál es el primero y qué tengo que llevar?

### Llamada al modelo 1

- generation id: `gen-1790904802-L490bnZlxybfVYUUdNu6`
- usage: 1551 tokens de entrada, 159 de salida (66 de razonamiento), costo USD 0.000220

**Herramienta:** `consultar_turnos({"especialidad": "cardiologia"})`

Resultado:

```text
{"especialidad": "cardiologia", "fecha": "2026-10-05", "datos": ["2026-10-14 09:30", "2026-10-14 10:00", "2026-10-16 15:00"]}
```

**Herramienta:** `buscar_documentos({"consulta": "¿Qué tengo que llevar a un turno con cardiología?"})`

Resultado:

```text
Turnos en consultorios externos — Qué llevar a la primera consulta
DNI, credencial de la cobertura de salud, la derivación y los estudios previos relacionados con el motivo de consulta, en papel o en el teléfono.
```

### Llamada al modelo 2

- generation id: `gen-1790904808-Wc0mBHyjZRGxaJfJX3H8`
- usage: 1781 tokens de entrada, 104 de salida (26 de razonamiento), costo USD 0.000152

### Respuesta

```text
El primer turno disponible en cardiología es el **14 de octubre de 2026 a las 09:30**.

Para la primera consulta tenés que llevar:
- **DNI**
- **Credencial de la cobertura de salud**
- **La derivación**
- **Estudios previos** relacionados con el motivo de consulta (en papel o en el teléfono).
```

## A12 — Me recetaron insulina NPH, ¿la tienen y qué necesito para retirarla?

### Llamada al modelo 1

- generation id: `gen-1790904812-YirxzF6dt349JNlKv2ko`
- usage: 1550 tokens de entrada, 164 de salida (66 de razonamiento), costo USD 0.000227

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

- generation id: `gen-1790904818-dwKT7COXBMRzMpupdaDE`
- usage: 1901 tokens de entrada, 220 de salida (77 de razonamiento), costo USD 0.000302

### Respuesta

```text
**Stock de insulina NPH:** No hay stock en este momento (0 frascos). La reposición está prevista para el **12/10/2026**.

**Para retirarla necesitás:**
- Receta de un profesional de la institución (validez de 30 días desde su emisión).
- DNI del paciente. Si retira otra persona, debe llevar su propio DNI y el del paciente.

La farmacia de pacientes ambulatorios está en planta baja, junto a admisión, y atiende de lunes a viernes de 8:00 a 20:00. No hace entregas los fines de semana.
```
