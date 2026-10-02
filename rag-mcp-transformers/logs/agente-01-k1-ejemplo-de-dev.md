# Corrida del benchmark — agente con tools de LangChain (parte 2)

- **Fecha:** 2026-10-01 22:16:09
- **Modelo:** `deepseek/deepseek-v4-flash-0731` por OpenRouter, temperatura 0
- **Preguntas:** `datos/preguntas_agente_dev.jsonl` (12)
- **Salida:** `respuestas.jsonl`
- **Herramientas:** funciones de `herramientas.py`, en el mismo proceso
- **Consumo de la key (`GET /api/v1/key`):** USD 0.032736 antes, USD 0.035876 después, diferencia USD 0.003140
- **Totales:** 25 llamadas al modelo, 40373 tokens de entrada, 2523 de salida (967 de razonamiento), costo USD 0.003665

## Herramientas que vio el modelo

- `buscar_documentos`: Busca en los documentos del hospital, que tienen las normas y los procedimientos que casi no cambian: horarios y reglas de visita de cada sector, quién puede acompañar o quedarse con un paciente, preparación para estudios y cirugías, requisitos y documentación para turnos, internación, alta y retiro de medicamentos, coberturas, niveles de triage de la guardia y sus tiempos máximos, vacunas, donación de sangre, accesos y derechos del paciente. Usala para cualquier pregunta sobre cómo funciona el hospital, qué hay que llevar o qué está permitido. No conoce el estado de hoy (camas libres, quién está de guardia, turnos disponibles, stock de farmacia, espera actual). 'consulta' es una pregunta completa en lenguaje natural, sobre un solo tema y nombrando el sector, estudio o trámite concreto; por ejemplo: '¿Qué hay que presentar para retirar medicamentos en la farmacia?'. Devuelve el fragmento más relevante. Si la pregunta del paciente tiene dos temas, hacé una búsqueda por cada tema.
- `consultar_camas`: Estado de las camas de un sector de internación en este momento: total, ocupadas y libres. 'sector' es el nombre del sector, por ejemplo 'pediatria', 'terapia intensiva' o 'maternidad'. Si el sector no existe, la respuesta trae la lista de sectores válidos para reintentar. No conoce las reglas de internación ni de acompañantes: eso está en los documentos.
- `consultar_guardia`: Profesionales que están de guardia hoy en una especialidad, con el horario de cada uno (por ejemplo 08:00-20:00 de día y 20:00-08:00 de noche). 'especialidad' es el nombre de la especialidad, por ejemplo 'cardiologia' o 'pediatria'. Si no existe, la respuesta trae la lista de especialidades válidas para reintentar.
- `consultar_turnos`: Próximos turnos disponibles (fecha y hora) para atenderse por consultorio en una especialidad, ordenados del más cercano al más lejano. 'especialidad' es el nombre de la especialidad, por ejemplo 'traumatologia' o 'dermatologia'. Si no existe, la respuesta trae la lista de especialidades válidas para reintentar. No conoce qué hay que llevar al turno ni cómo se pide: eso está en los documentos.
- `consultar_farmacia`: Stock de un medicamento en la farmacia del hospital hoy y, si no hay, la fecha de reposición. 'medicamento' es el nombre con su presentación, por ejemplo 'amoxicilina 500 mg' o 'salbutamol aerosol'. Si el nombre no coincide, la respuesta trae la lista de medicamentos válidos para reintentar con el nombre exacto. No conoce los requisitos para retirar un medicamento: eso está en los documentos.
- `consultar_espera`: Minutos de espera en la guardia en este momento, para cada nivel de triage (rojo, naranja, amarillo, verde, azul). No recibe parámetros. No conoce el tiempo máximo que fija la norma para cada nivel: eso está en los documentos.

## Resumen por pregunta

| Pregunta | Herramientas | Llamadas al modelo | Tokens entrada | Tokens salida | Razonamiento | Costo USD |
|---|---|---|---|---|---|---|
| A01 | buscar_documentos | 2 | 3199 | 134 | 32 | 0.000206 |
| A02 | buscar_documentos | 2 | 3214 | 206 | 28 | 0.000298 |
| A03 | buscar_documentos | 2 | 3163 | 185 | 75 | 0.000271 |
| A04 | buscar_documentos | 2 | 3239 | 200 | 28 | 0.000291 |
| A05 | consultar_camas | 2 | 3134 | 113 | 37 | 0.000178 |
| A06 | consultar_guardia | 2 | 3170 | 114 | 29 | 0.000180 |
| A07 | consultar_turnos | 2 | 3155 | 107 | 31 | 0.000171 |
| A08 | consultar_farmacia | 2 | 3157 | 173 | 75 | 0.000256 |
| A09 | consultar_espera | 2 | 3142 | 203 | 159 | 0.000294 |
| A10 | consultar_camas, buscar_documentos, buscar_documentos | 3 | 5126 | 467 | 257 | 0.000653 |
| A11 | consultar_turnos, buscar_documentos | 2 | 3278 | 239 | 66 | 0.000341 |
| A12 | consultar_farmacia, buscar_documentos | 2 | 3396 | 382 | 150 | 0.000526 |
| **Total** | | 25 | 40373 | 2523 | 967 | 0.003665 |

## A01 — ¿Cuál es el horario de visita en neonatología para los abuelos?

### Llamada al modelo 1

- generation id: `gen-1790903770-FCCib7OKFk66WeKk9HEd`
- usage: 1520 tokens de entrada, 87 de salida (32 de razonamiento), costo USD 0.000128

**Herramienta:** `buscar_documentos({"consulta": "horario de visita en neonatología para abuelos"})`

Resultado:

```text
Régimen de visitas — Neonatología
Madre y padre tienen ingreso libre las 24 horas. Los abuelos pueden visitar martes y jueves de 16:00 a 17:00, uno por vez y con la presencia de uno de los padres. Los hermanos del recién nacido no ingresan al sector durante la temporada de virus respiratorios, de mayo a septiembre.
```

### Llamada al modelo 2

- generation id: `gen-1790903772-J75sk2vAecX0QzDbPBFI`
- usage: 1679 tokens de entrada, 47 de salida (0 de razonamiento), costo USD 0.000078

### Respuesta

```text
El horario de visita de los abuelos en neonatología es **martes y jueves de 16:00 a 17:00**, uno por vez y con la presencia de uno de los padres.
```

## A02 — ¿Qué preparación necesita una colonoscopía?

### Llamada al modelo 1

- generation id: `gen-1790903774-118MuPWPvqWWRUAyuJKr`
- usage: 1512 tokens de entrada, 82 de salida (28 de razonamiento), costo USD 0.000121

**Herramienta:** `buscar_documentos({"consulta": "¿Qué preparación necesita una colonoscopía?"})`

Resultado:

```text
Preparación para estudios de diagnóstico por imágenes y endoscopía — Colonoscopía
Los tres días previos se sigue una dieta sin residuos: sin frutas, verduras, legumbres ni cereales integrales. La tarde anterior se toma la solución evacuante de polietilenglicol, cuatro litros repartidos en cuatro horas. Desde la medianoche solo se permiten líquidos claros, y el ayuno total es de 6 horas antes del turno. El paciente tiene que venir acompañado, porque el estudio se hace con sedación.
```

### Llamada al modelo 2

- generation id: `gen-1790903778-as3fCFk1n7Izm96oIENw`
- usage: 1702 tokens de entrada, 124 de salida (0 de razonamiento), costo USD 0.000177

### Respuesta

```text
Para una colonoscopía, la preparación es la siguiente:

- **3 días previos:** dieta sin residuos (sin frutas, verduras, legumbres ni cereales integrales).
- **Tarde anterior:** tomar la solución evacuante de polietilenglicol, 4 litros repartidos en 4 horas.
- **Desde la medianoche:** solo líquidos claros.
- **Ayuno total:** 6 horas antes del turno.
- **Acompañante:** tiene que venir acompañado, porque el estudio se hace con sedación.
```

## A03 — ¿Qué documentos tengo que llevar a la primera consulta con un especialista?

### Llamada al modelo 1

- generation id: `gen-1790903785-egZ8Pe8XS36LZ74GnLax`
- usage: 1518 tokens de entrada, 123 de salida (75 de razonamiento), costo USD 0.000174

**Herramienta:** `buscar_documentos({"consulta": "¿Qué documentos hay que llevar a la primera consulta con un especialista?"})`

Resultado:

```text
Turnos en consultorios externos — Qué llevar a la primera consulta
DNI, credencial de la cobertura de salud, la derivación y los estudios previos relacionados con el motivo de consulta, en papel o en el teléfono.
```

### Llamada al modelo 2

- generation id: `gen-1790903791-h52GMhSnuHhZojfYAGNX`
- usage: 1645 tokens de entrada, 62 de salida (0 de razonamiento), costo USD 0.000097

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

- generation id: `gen-1790903794-geD6hjdp94NdI5QhCeYi`
- usage: 1510 tokens de entrada, 90 de salida (28 de razonamiento), costo USD 0.000132

**Herramienta:** `buscar_documentos({"consulta": "¿Quiénes pueden donar sangre? Requisitos para donar sangre"})`

Resultado:

```text
Donación de sangre
El servicio de hemoterapia recibe donantes de lunes a sábado de 7:30 a 12:00, en el primer piso.

Pueden donar personas de 18 a 65 años que pesen más de 50 kilos y se sientan bien. No hay que venir en ayunas: se recomienda un desayuno liviano, sin lácteos ni grasas. Entre una donación y la siguiente tienen que pasar al menos 2 meses en los hombres y 3 meses en las mujeres.

No pueden donar por 12 meses quienes se hicieron un tatuaje o un piercing en ese período.
```

### Llamada al modelo 2

- generation id: `gen-1790903797-IJHCpfcMr4WGjyobD8fc`
- usage: 1729 tokens de entrada, 110 de salida (0 de razonamiento), costo USD 0.000159

### Respuesta

```text
Pueden donar sangre las personas de **18 a 65 años** que pesen **más de 50 kilos** y se sientan bien. No hace falta ir en ayunas: se recomienda un desayuno liviano, sin lácteos ni grasas. Entre donación y donación deben pasar al menos **2 meses en hombres** y **3 meses en mujeres**. No pueden donar por **12 meses** quienes se hicieron un tatuaje o piercing en ese período.
```

## A05 — ¿Hay camas libres en terapia intensiva ahora?

### Llamada al modelo 1

- generation id: `gen-1790903800-tbPIiRk5ka9sP6M5qnX9`
- usage: 1513 tokens de entrada, 86 de salida (37 de razonamiento), costo USD 0.000126

**Herramienta:** `consultar_camas({"sector": "terapia intensiva"})`

Resultado:

```text
{"sector": "terapia_intensiva", "fecha": "2026-10-05", "datos": {"total": 12, "ocupadas": 12, "libres": 0}}
```

### Llamada al modelo 2

- generation id: `gen-1790903804-gWrstqQT4BsbTA7P485t`
- usage: 1621 tokens de entrada, 27 de salida (0 de razonamiento), costo USD 0.000052

### Respuesta

```text
No, en este momento no hay camas libres en terapia intensiva: las 12 camas están ocupadas.
```

## A06 — ¿Quién está de guardia en cardiología esta noche?

### Llamada al modelo 1

- generation id: `gen-1790903807-agH3ECkz3vkcYCHBmYyi`
- usage: 1514 tokens de entrada, 78 de salida (29 de razonamiento), costo USD 0.000116

**Herramienta:** `consultar_guardia({"especialidad": "cardiologia"})`

Resultado:

```text
{"especialidad": "cardiologia", "fecha": "2026-10-05", "datos": [{"profesional": "Dr. Julián Ferreyra", "horario": "08:00-20:00"}, {"profesional": "Dra. Paula Benítez", "horario": "20:00-08:00"}]}
```

### Llamada al modelo 2

- generation id: `gen-1790903810-YkjzbRQiieGO9LofTqkj`
- usage: 1656 tokens de entrada, 36 de salida (0 de razonamiento), costo USD 0.000064

### Respuesta

```text
Esta noche (guardia nocturna de 20:00 a 08:00) en cardiología está de guardia la **Dra. Paula Benítez**.
```

## A07 — ¿Cuándo es el próximo turno disponible con traumatología?

### Llamada al modelo 1

- generation id: `gen-1790903812-wX4LjTEVCZzb713fGNKl`
- usage: 1515 tokens de entrada, 76 de salida (31 de razonamiento), costo USD 0.000114

**Herramienta:** `consultar_turnos({"especialidad": "traumatologia"})`

Resultado:

```text
{"especialidad": "traumatologia", "fecha": "2026-10-05", "datos": ["2026-10-07 08:40", "2026-10-07 09:00", "2026-10-08 14:20"]}
```

### Llamada al modelo 2

- generation id: `gen-1790903815-LD9KZ8Pp1DblrNiweFJo`
- usage: 1640 tokens de entrada, 31 de salida (0 de razonamiento), costo USD 0.000057

### Respuesta

```text
El próximo turno disponible con traumatología es el **miércoles 7 de octubre de 2026 a las 08:40**.
```

## A08 — ¿Tienen enalapril de 10 mg en la farmacia?

### Llamada al modelo 1

- generation id: `gen-1790903816-eHUCAueXKvvqTDg61s3E`
- usage: 1517 tokens de entrada, 105 de salida (54 de razonamiento), costo USD 0.000151

**Herramienta:** `consultar_farmacia({"medicamento": "enalapril 10 mg"})`

Resultado:

```text
{"medicamento": "enalapril 10 mg", "fecha": "2026-10-05", "datos": {"stock": 0, "unidad": "comprimidos", "reposicion": "2026-10-09"}}
```

### Llamada al modelo 2

- generation id: `gen-1790903821-LBdDyiy9OynLkbwVxwXB`
- usage: 1640 tokens de entrada, 68 de salida (21 de razonamiento), costo USD 0.000105

### Respuesta

```text
No, en este momento no hay stock de enalapril 10 mg en la farmacia. La reposición está prevista para el 9 de octubre de 2026.
```

## A09 — ¿Cuánto se está esperando hoy en la guardia si me clasifican como verde?

### Llamada al modelo 1

- generation id: `gen-1790903824-dcWFlqsw9iIJCmsIBwqw`
- usage: 1522 tokens de entrada, 85 de salida (57 de razonamiento), costo USD 0.000125

**Herramienta:** `consultar_espera({})`

Resultado:

```text
{"fecha": "2026-10-05", "minutos_por_nivel": {"rojo": 0, "naranja": 7, "amarillo": 48, "verde": 135, "azul": 210}}
```

### Llamada al modelo 2

- generation id: `gen-1790903826-CmFIsZ9twfm0fucyz7mr`
- usage: 1620 tokens de entrada, 118 de salida (102 de razonamiento), costo USD 0.000169

### Respuesta

```text
Hoy, si te clasifican como nivel verde en la guardia, la espera es de 135 minutos.
```

## A10 — Quiero internar a mi nene en pediatría, ¿hay lugar y me puedo quedar con él?

### Llamada al modelo 1

- generation id: `gen-1790903828-yZuQQUEyoOOoysM5g6Ra`
- usage: 1526 tokens de entrada, 183 de salida (81 de razonamiento), costo USD 0.000251

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

- generation id: `gen-1790903830-cHuas18cuc6zpXD92M8J`
- usage: 1739 tokens de entrada, 173 de salida (132 de razonamiento), costo USD 0.000240

**Herramienta:** `buscar_documentos({"consulta": "Acompañante de pacientes en pediatría durante la internación"})`

Resultado:

```text
Ingreso a internación programada — Acompañante
Se permite un acompañante por paciente internado durante la noche, salvo en terapia intensiva. El acompañante recibe una tarjeta que presenta en el control de acceso.
```

### Llamada al modelo 3

- generation id: `gen-1790903832-GOsNvpxo5FTlqbWgzpmM`
- usage: 1861 tokens de entrada, 111 de salida (44 de razonamiento), costo USD 0.000162

### Respuesta

```text
Sí, hay lugar en pediatría: hay 24 camas en total, 17 ocupadas y 7 libres.

En cuanto a quedarse con él: se permite un acompañante por paciente internado durante la noche (salvo en terapia intensiva). El acompañante recibe una tarjeta que debe presentar en el control de acceso.
```

## A11 — Necesito turno con cardiología, ¿cuál es el primero y qué tengo que llevar?

### Llamada al modelo 1

- generation id: `gen-1790903837-Fr99A8LEUNH8lxRQgnzT`
- usage: 1523 tokens de entrada, 161 de salida (66 de razonamiento), costo USD 0.000223

**Herramienta:** `consultar_turnos({"especialidad": "cardiologia"})`

Resultado:

```text
{"especialidad": "cardiologia", "fecha": "2026-10-05", "datos": ["2026-10-14 09:30", "2026-10-14 10:00", "2026-10-16 15:00"]}
```

**Herramienta:** `buscar_documentos({"consulta": "¿Qué hay que llevar para un turno de cardiología por consultorio?"})`

Resultado:

```text
Turnos en consultorios externos — Qué llevar a la primera consulta
DNI, credencial de la cobertura de salud, la derivación y los estudios previos relacionados con el motivo de consulta, en papel o en el teléfono.
```

### Llamada al modelo 2

- generation id: `gen-1790903842-uHe8k0iXgeDeTMy6txT9`
- usage: 1755 tokens de entrada, 78 de salida (0 de razonamiento), costo USD 0.000119

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

- generation id: `gen-1790903846-2978LC0fPtGy93l5lJqm`
- usage: 1522 tokens de entrada, 175 de salida (83 de razonamiento), costo USD 0.000240

**Herramienta:** `consultar_farmacia({"medicamento": "insulina NPH"})`

Resultado:

```text
{"medicamento": "insulina NPH", "fecha": "2026-10-05", "datos": {"stock": 0, "unidad": "frascos", "reposicion": "2026-10-12"}}
```

**Herramienta:** `buscar_documentos({"consulta": "¿Qué hay que presentar para retirar medicamentos en la farmacia?"})`

Resultado:

```text
Farmacia del hospital
La farmacia de pacientes ambulatorios está en planta baja, junto a admisión, y atiende de lunes a viernes de 8:00 a 20:00. Entrega medicación a pacientes del hospital con receta de un profesional de la institución.

Para retirar medicación se presenta el DNI del paciente. Si retira otra persona, lleva su propio DNI y el del paciente.

Los medicamentos de alto costo, como los oncológicos y los biológicos, requieren un formulario de solicitud firmado por el especialista y aprobado por el comité de farmacia, que se reúne los miércoles.

La farmacia no hace entregas los fines de semana. Las recetas tienen una validez de 30 días desde la fecha de emisión.
```

### Llamada al modelo 2

- generation id: `gen-1790903853-9SrvpQ4Ys481vUnQlWg3`
- usage: 1874 tokens de entrada, 207 de salida (67 de razonamiento), costo USD 0.000285

### Respuesta

```text
**Insulina NPH:** Hoy no hay stock en la farmacia (0 frascos). La reposición está prevista para el **12/10/2026**.

**Para retirarla** (cuando haya stock), necesitás:
- **Receta de un profesional del hospital** (validez de 30 días desde su emisión).
- **DNI del paciente**. Si retira otra persona, debe llevar su propio DNI y el del paciente.

La farmacia ambulatoria está en planta baja, junto a admisión, y atiende de lunes a viernes de 8:00 a 20:00.
```
