# Corrida del benchmark — agente con tools de LangChain (parte 2)

- **Fecha:** 2026-10-01 22:19:44
- **Modelo:** `deepseek/deepseek-v4-flash-0731` por OpenRouter, temperatura 0
- **Preguntas:** `datos/preguntas_agente_dev.jsonl` (12)
- **Salida:** `experimentos/agente/02-k1.jsonl`
- **Herramientas:** funciones de `herramientas.py`, en el mismo proceso
- **Consumo de la key (`GET /api/v1/key`):** USD 0.054038 antes, USD 0.057150 después, diferencia USD 0.003112
- **Totales:** 24 llamadas al modelo, 38782 tokens de entrada, 2567 de salida (884 de razonamiento), costo USD 0.003705

## Herramientas que vio el modelo

- `buscar_documentos`: Busca en los documentos del hospital, que tienen las normas y los procedimientos que casi no cambian: horarios y reglas de visita de cada sector, quién puede acompañar o quedarse con un paciente, preparación para estudios y cirugías, requisitos y documentación para turnos, internación, alta y retiro de medicamentos, coberturas, niveles de triage de la guardia y sus tiempos máximos, vacunas, donación de sangre, accesos y derechos del paciente. Usala para cualquier pregunta sobre cómo funciona el hospital, qué hay que llevar o qué está permitido. No conoce el estado de hoy (camas libres, quién está de guardia, turnos disponibles, stock de farmacia, espera actual). 'consulta' es una pregunta completa en lenguaje natural, sobre un solo tema y nombrando el sector, estudio o trámite concreto; por ejemplo: '¿Cómo se pide una consulta por telemedicina?'. Devuelve los fragmentos más relevantes, separados por '---'. Si la pregunta del paciente tiene dos temas, hacé una búsqueda por cada tema.
- `consultar_camas`: Estado de las camas de un sector de internación en este momento: total, ocupadas y libres. 'sector' es el nombre del sector, por ejemplo 'pediatria', 'terapia intensiva' o 'maternidad'. Si el sector no existe, la respuesta trae la lista de sectores válidos para reintentar. No conoce las reglas de internación ni de acompañantes: eso está en los documentos.
- `consultar_guardia`: Profesionales que están de guardia hoy en una especialidad, con el horario de cada uno (por ejemplo 08:00-20:00 de día y 20:00-08:00 de noche). 'especialidad' es el nombre de la especialidad, por ejemplo 'cardiologia' o 'pediatria'. Si no existe, la respuesta trae la lista de especialidades válidas para reintentar.
- `consultar_turnos`: Próximos turnos disponibles (fecha y hora) para atenderse por consultorio en una especialidad, ordenados del más cercano al más lejano. 'especialidad' es el nombre de la especialidad, por ejemplo 'traumatologia' o 'dermatologia'. Si no existe, la respuesta trae la lista de especialidades válidas para reintentar. No conoce qué hay que llevar al turno ni cómo se pide: eso está en los documentos.
- `consultar_farmacia`: Stock de un medicamento en la farmacia del hospital hoy y, si no hay, la fecha de reposición. 'medicamento' es el nombre con su presentación, por ejemplo 'amoxicilina 500 mg' o 'salbutamol aerosol'. Si el nombre no coincide, la respuesta trae la lista de medicamentos válidos para reintentar con el nombre exacto. No conoce los requisitos para retirar un medicamento: eso está en los documentos.
- `consultar_espera`: Minutos de espera en la guardia en este momento, para cada nivel de triage (rojo, naranja, amarillo, verde, azul). No recibe parámetros. No conoce el tiempo máximo que fija la norma para cada nivel: eso está en los documentos.

## Resumen por pregunta

| Pregunta | Herramientas | Llamadas al modelo | Tokens entrada | Tokens salida | Razonamiento | Costo USD |
|---|---|---|---|---|---|---|
| A01 | buscar_documentos | 2 | 3205 | 125 | 25 | 0.000195 |
| A02 | buscar_documentos | 2 | 3222 | 206 | 28 | 0.000298 |
| A03 | buscar_documentos | 2 | 3169 | 173 | 58 | 0.000256 |
| A04 | buscar_documentos | 2 | 3245 | 238 | 26 | 0.000340 |
| A05 | consultar_camas | 2 | 3140 | 108 | 34 | 0.000172 |
| A06 | consultar_guardia | 2 | 3176 | 198 | 103 | 0.000288 |
| A07 | consultar_turnos | 2 | 3161 | 107 | 31 | 0.000171 |
| A08 | consultar_farmacia | 2 | 3163 | 115 | 22 | 0.000181 |
| A09 | consultar_espera, buscar_documentos | 2 | 3337 | 305 | 154 | 0.000426 |
| A10 | consultar_camas, buscar_documentos | 2 | 3271 | 300 | 131 | 0.000419 |
| A11 | consultar_turnos, buscar_documentos | 2 | 3284 | 258 | 83 | 0.000366 |
| A12 | consultar_farmacia, buscar_documentos | 2 | 3409 | 434 | 189 | 0.000592 |
| **Total** | | 24 | 38782 | 2567 | 884 | 0.003705 |

## A01 — ¿Cuál es el horario de visita en neonatología para los abuelos?

### Llamada al modelo 1

- generation id: `gen-1790903985-nbfsaG0s3sHTjPVXDOge`
- usage: 1523 tokens de entrada, 80 de salida (25 de razonamiento), costo USD 0.000119

**Herramienta:** `buscar_documentos({"consulta": "horario de visita en neonatología para abuelos"})`

Resultado:

```text
Régimen de visitas — Neonatología
Madre y padre tienen ingreso libre las 24 horas. Los abuelos pueden visitar martes y jueves de 16:00 a 17:00, uno por vez y con la presencia de uno de los padres. Los hermanos del recién nacido no ingresan al sector durante la temporada de virus respiratorios, de mayo a septiembre.
```

### Llamada al modelo 2

- generation id: `gen-1790903988-1955WxfAu6jgTPJZpZyb`
- usage: 1682 tokens de entrada, 45 de salida (0 de razonamiento), costo USD 0.000076

### Respuesta

```text
En neonatología, los abuelos pueden visitar los **martes y jueves de 16:00 a 17:00**, uno por vez y con la presencia de uno de los padres.
```

## A02 — ¿Qué preparación necesita una colonoscopía?

### Llamada al modelo 1

- generation id: `gen-1790903990-0exPZtM72VsVk9XvDDBh`
- usage: 1515 tokens de entrada, 84 de salida (28 de razonamiento), costo USD 0.000124

**Herramienta:** `buscar_documentos({"consulta": "¿Cómo es la preparación para una colonoscopía?"})`

Resultado:

```text
Preparación para estudios de diagnóstico por imágenes y endoscopía — Colonoscopía
Los tres días previos se sigue una dieta sin residuos: sin frutas, verduras, legumbres ni cereales integrales. La tarde anterior se toma la solución evacuante de polietilenglicol, cuatro litros repartidos en cuatro horas. Desde la medianoche solo se permiten líquidos claros, y el ayuno total es de 6 horas antes del turno. El paciente tiene que venir acompañado, porque el estudio se hace con sedación.
```

### Llamada al modelo 2

- generation id: `gen-1790903994-kJPC18QNI99Nx2yUDr35`
- usage: 1707 tokens de entrada, 122 de salida (0 de razonamiento), costo USD 0.000175

### Respuesta

```text
La preparación para una colonoscopía es la siguiente:

- **3 días previos**: dieta sin residuos (sin frutas, verduras, legumbres ni cereales integrales).
- **Tarde anterior**: tomar la solución evacuante de polietilenglicol, 4 litros repartidos en 4 horas.
- **Desde la medianoche**: solo líquidos claros.
- **Ayuno total**: 6 horas antes del turno.
- **Acompañante**: debe venir acompañado, porque el estudio se hace con sedación.
```

## A03 — ¿Qué documentos tengo que llevar a la primera consulta con un especialista?

### Llamada al modelo 1

- generation id: `gen-1790903998-6byKaNIEmhOtR0yWrn5N`
- usage: 1521 tokens de entrada, 111 de salida (58 de razonamiento), costo USD 0.000159

**Herramienta:** `buscar_documentos({"consulta": "¿Qué documentos hay que llevar a la primera consulta con un especialista?"})`

Resultado:

```text
Turnos en consultorios externos — Qué llevar a la primera consulta
DNI, credencial de la cobertura de salud, la derivación y los estudios previos relacionados con el motivo de consulta, en papel o en el teléfono.
```

### Llamada al modelo 2

- generation id: `gen-1790904003-kgYH42MRWwMz1ZQjZBlo`
- usage: 1648 tokens de entrada, 62 de salida (0 de razonamiento), costo USD 0.000097

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

- generation id: `gen-1790904006-lrhRMc8Juy4mPZieoDqJ`
- usage: 1513 tokens de entrada, 87 de salida (26 de razonamiento), costo USD 0.000128

**Herramienta:** `buscar_documentos({"consulta": "¿Quiénes pueden donar sangre? Requisitos para donar sangre"})`

Resultado:

```text
Donación de sangre
El servicio de hemoterapia recibe donantes de lunes a sábado de 7:30 a 12:00, en el primer piso.

Pueden donar personas de 18 a 65 años que pesen más de 50 kilos y se sientan bien. No hay que venir en ayunas: se recomienda un desayuno liviano, sin lácteos ni grasas. Entre una donación y la siguiente tienen que pasar al menos 2 meses en los hombres y 3 meses en las mujeres.

No pueden donar por 12 meses quienes se hicieron un tatuaje o un piercing en ese período.
```

### Llamada al modelo 2

- generation id: `gen-1790904010-5fgOXFsbso0nohplwsoU`
- usage: 1732 tokens de entrada, 151 de salida (0 de razonamiento), costo USD 0.000212

### Respuesta

```text
Pueden donar sangre las personas de **18 a 65 años** que pesen **más de 50 kilos** y se sientan bien.

Algunas condiciones:
- No hay que venir en ayunas: se recomienda un desayuno liviano, sin lácteos ni grasas.
- Entre donaciones deben pasar al menos **2 meses** en hombres y **3 meses** en mujeres.
- No pueden donar por **12 meses** quienes se hicieron un tatuaje o piercing en ese período.

El servicio de hemoterapia recibe donantes de **lunes a sábado de 7:30 a 12:00**, en el primer piso.
```

## A05 — ¿Hay camas libres en terapia intensiva ahora?

### Llamada al modelo 1

- generation id: `gen-1790904013-BKunIaa9lbC42WocnbSi`
- usage: 1516 tokens de entrada, 81 de salida (34 de razonamiento), costo USD 0.000120

**Herramienta:** `consultar_camas({"sector": "terapia intensiva"})`

Resultado:

```text
{"sector": "terapia_intensiva", "fecha": "2026-10-05", "datos": {"total": 12, "ocupadas": 12, "libres": 0}}
```

### Llamada al modelo 2

- generation id: `gen-1790904019-swEZCcUVGtK3yHhUYUgG`
- usage: 1624 tokens de entrada, 27 de salida (0 de razonamiento), costo USD 0.000052

### Respuesta

```text
No, en este momento no hay camas libres en terapia intensiva: las 12 camas están ocupadas.
```

## A06 — ¿Quién está de guardia en cardiología esta noche?

### Llamada al modelo 1

- generation id: `gen-1790904022-6GA4ik2ld4qWRsWGzZnP`
- usage: 1517 tokens de entrada, 95 de salida (48 de razonamiento), costo USD 0.000138

**Herramienta:** `consultar_guardia({"especialidad": "cardiologia"})`

Resultado:

```text
{"especialidad": "cardiologia", "fecha": "2026-10-05", "datos": [{"profesional": "Dr. Julián Ferreyra", "horario": "08:00-20:00"}, {"profesional": "Dra. Paula Benítez", "horario": "20:00-08:00"}]}
```

### Llamada al modelo 2

- generation id: `gen-1790904025-EdmPaIet6kjSHGUzSiLE`
- usage: 1659 tokens de entrada, 103 de salida (55 de razonamiento), costo USD 0.000150

### Respuesta

```text
Esta noche (turno 20:00-08:00) está de guardia en cardiología la **Dra. Paula Benítez**.
```

## A07 — ¿Cuándo es el próximo turno disponible con traumatología?

### Llamada al modelo 1

- generation id: `gen-1790904029-FI8IuqHyK7FZKyXrQd3A`
- usage: 1518 tokens de entrada, 76 de salida (31 de razonamiento), costo USD 0.000114

**Herramienta:** `consultar_turnos({"especialidad": "traumatologia"})`

Resultado:

```text
{"especialidad": "traumatologia", "fecha": "2026-10-05", "datos": ["2026-10-07 08:40", "2026-10-07 09:00", "2026-10-08 14:20"]}
```

### Llamada al modelo 2

- generation id: `gen-1790904032-faEHJMHxsBg9XOt7fqpq`
- usage: 1643 tokens de entrada, 31 de salida (0 de razonamiento), costo USD 0.000057

### Respuesta

```text
El próximo turno disponible con traumatología es el **miércoles 7 de octubre de 2026 a las 08:40**.
```

## A08 — ¿Tienen enalapril de 10 mg en la farmacia?

### Llamada al modelo 1

- generation id: `gen-1790904035-HUEqumT7HnTTbDiZqJy6`
- usage: 1520 tokens de entrada, 77 de salida (22 de razonamiento), costo USD 0.000115

**Herramienta:** `consultar_farmacia({"medicamento": "enalapril 10 mg"})`

Resultado:

```text
{"medicamento": "enalapril 10 mg", "fecha": "2026-10-05", "datos": {"stock": 0, "unidad": "comprimidos", "reposicion": "2026-10-09"}}
```

### Llamada al modelo 2

- generation id: `gen-1790904037-Vh85OJ6vITa3GKIEZayw`
- usage: 1643 tokens de entrada, 38 de salida (0 de razonamiento), costo USD 0.000066

### Respuesta

```text
No tenemos enalapril de 10 mg en stock hoy (0 comprimidos). La reposición está prevista para el 9 de octubre de 2026.
```

## A09 — ¿Cuánto se está esperando hoy en la guardia si me clasifican como verde?

### Llamada al modelo 1

- generation id: `gen-1790904040-2WutudTMoSj43LRfggcv`
- usage: 1525 tokens de entrada, 150 de salida (70 de razonamiento), costo USD 0.000208

**Herramienta:** `consultar_espera({})`

Resultado:

```text
{"fecha": "2026-10-05", "minutos_por_nivel": {"rojo": 0, "naranja": 7, "amarillo": 48, "verde": 135, "azul": 210}}
```

**Herramienta:** `buscar_documentos({"consulta": "¿Cuál es el tiempo máximo de espera para el nivel de triage verde en la guardia?"})`

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

- generation id: `gen-1790904042-jFsFPqpIwXTZQqHjypTw`
- usage: 1812 tokens de entrada, 155 de salida (84 de razonamiento), costo USD 0.000218

### Respuesta

```text
Hoy en la guardia, si te clasifican como **verde (urgencia menor)**, la espera actual es de **135 minutos**.

Según la norma del hospital, el tiempo máximo para ese nivel es de **2 horas (120 minutos)**, por lo que hoy la espera está por encima de lo establecido.
```

## A10 — Quiero internar a mi nene en pediatría, ¿hay lugar y me puedo quedar con él?

### Llamada al modelo 1

- generation id: `gen-1790904045-gRsQYBmdBidB6QiyP2f9`
- usage: 1529 tokens de entrada, 185 de salida (83 de razonamiento), costo USD 0.000253

**Herramienta:** `consultar_camas({"sector": "pediatria"})`

Resultado:

```text
{"sector": "pediatria", "fecha": "2026-10-05", "datos": {"total": 24, "ocupadas": 17, "libres": 7}}
```

**Herramienta:** `buscar_documentos({"consulta": "¿Puede un acompañante quedarse con un paciente internado en pediatría?"})`

Resultado:

```text
Ingreso a internación programada — Acompañante
Se permite un acompañante por paciente internado durante la noche, salvo en terapia intensiva. El acompañante recibe una tarjeta que presenta en el control de acceso.
```

### Llamada al modelo 2

- generation id: `gen-1790904047-CyQjANZsSMnkURgXWk1K`
- usage: 1742 tokens de entrada, 115 de salida (48 de razonamiento), costo USD 0.000166

### Respuesta

```text
Sí, hay lugar en pediatría: hay 24 camas en total, 17 ocupadas y 7 libres.

En cuanto a quedarse con él: la norma permite un acompañante por paciente internado durante la noche, salvo en terapia intensiva. El acompañante recibe una tarjeta que debe presentar en el control de acceso.
```

## A11 — Necesito turno con cardiología, ¿cuál es el primero y qué tengo que llevar?

### Llamada al modelo 1

- generation id: `gen-1790904049-C6G92xXhQkdwbo2lCxQJ`
- usage: 1526 tokens de entrada, 174 de salida (83 de razonamiento), costo USD 0.000239

**Herramienta:** `consultar_turnos({"especialidad": "cardiologia"})`

Resultado:

```text
{"especialidad": "cardiologia", "fecha": "2026-10-05", "datos": ["2026-10-14 09:30", "2026-10-14 10:00", "2026-10-16 15:00"]}
```

**Herramienta:** `buscar_documentos({"consulta": "¿Qué hay que llevar a un turno de cardiología por consultorio?"})`

Resultado:

```text
Turnos en consultorios externos — Qué llevar a la primera consulta
DNI, credencial de la cobertura de salud, la derivación y los estudios previos relacionados con el motivo de consulta, en papel o en el teléfono.
```

### Llamada al modelo 2

- generation id: `gen-1790904055-pzR9KjufG3PsiujV39JR`
- usage: 1758 tokens de entrada, 84 de salida (0 de razonamiento), costo USD 0.000127

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

- generation id: `gen-1790904058-vaQEFhpEH3sVsCkkprwb`
- usage: 1525 tokens de entrada, 205 de salida (111 de razonamiento), costo USD 0.000279

**Herramienta:** `consultar_farmacia({"medicamento": "insulina NPH"})`

Resultado:

```text
{"medicamento": "insulina NPH", "fecha": "2026-10-05", "datos": {"stock": 0, "unidad": "frascos", "reposicion": "2026-10-12"}}
```

**Herramienta:** `buscar_documentos({"consulta": "¿Qué requisitos y documentación se necesitan para retirar un medicamento de la farmacia del hospital?"})`

Resultado:

```text
Farmacia del hospital
La farmacia de pacientes ambulatorios está en planta baja, junto a admisión, y atiende de lunes a viernes de 8:00 a 20:00. Entrega medicación a pacientes del hospital con receta de un profesional de la institución.

Para retirar medicación se presenta el DNI del paciente. Si retira otra persona, lleva su propio DNI y el del paciente.

Los medicamentos de alto costo, como los oncológicos y los biológicos, requieren un formulario de solicitud firmado por el especialista y aprobado por el comité de farmacia, que se reúne los miércoles.

La farmacia no hace entregas los fines de semana. Las recetas tienen una validez de 30 días desde la fecha de emisión.
```

### Llamada al modelo 2

- generation id: `gen-1790904066-eEbEXtIcwem0L0T5pul3`
- usage: 1884 tokens de entrada, 229 de salida (78 de razonamiento), costo USD 0.000313

### Respuesta

```text
**Stock de insulina NPH:** Hoy no hay stock (0 frascos). La reposición está prevista para el **12/10/2026**.

**Para retirarla (cuando haya stock):**
- Presentar el **DNI del paciente**.
- Si retira otra persona, debe llevar **su propio DNI y el del paciente**.
- La receta debe ser de un profesional de la institución y tiene una validez de **30 días** desde su emisión.
- La farmacia ambulatoria está en planta baja, junto a admisión, y atiende de lunes a viernes de 8:00 a 20:00 (no entrega los fines de semana).
```
