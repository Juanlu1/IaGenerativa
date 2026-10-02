# Corrida del benchmark — agente con tools de LangChain (parte 2)

- **Fecha:** 2026-10-01 22:24:38
- **Modelo:** `deepseek/deepseek-v4-flash-0731` por OpenRouter, temperatura 0
- **Preguntas:** `datos/preguntas_agente_dev.jsonl` (12)
- **Salida:** `experimentos/agente/04-k3.jsonl`
- **Herramientas:** funciones de `herramientas.py`, en el mismo proceso
- **Consumo de la key (`GET /api/v1/key`):** USD 0.092373 antes, USD 0.099879 después, diferencia USD 0.007506
- **Totales:** 24 llamadas al modelo, 39870 tokens de entrada, 2608 de salida (872 de razonamiento), costo USD 0.003769

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
| A01 | buscar_documentos | 2 | 3379 | 143 | 32 | 0.000220 |
| A02 | buscar_documentos | 2 | 3351 | 209 | 28 | 0.000304 |
| A03 | buscar_documentos | 2 | 3311 | 171 | 51 | 0.000255 |
| A04 | buscar_documentos | 2 | 3345 | 244 | 28 | 0.000348 |
| A05 | consultar_camas | 2 | 3140 | 113 | 37 | 0.000179 |
| A06 | consultar_guardia | 2 | 3176 | 198 | 103 | 0.000288 |
| A07 | consultar_turnos | 2 | 3161 | 107 | 31 | 0.000171 |
| A08 | consultar_farmacia | 2 | 3163 | 144 | 43 | 0.000218 |
| A09 | consultar_espera, buscar_documentos | 2 | 3482 | 321 | 208 | 0.000448 |
| A10 | consultar_camas, buscar_documentos | 2 | 3377 | 242 | 81 | 0.000346 |
| A11 | consultar_turnos, buscar_documentos | 2 | 3432 | 297 | 77 | 0.000417 |
| A12 | consultar_farmacia, buscar_documentos | 2 | 3553 | 419 | 153 | 0.000575 |
| **Total** | | 24 | 39870 | 2608 | 872 | 0.003769 |

## A01 — ¿Cuál es el horario de visita en neonatología para los abuelos?

### Llamada al modelo 1

- generation id: `gen-1790904279-pCOhXRwJ7VRCSEIAXrLa`
- usage: 1523 tokens de entrada, 87 de salida (32 de razonamiento), costo USD 0.000128

**Herramienta:** `buscar_documentos({"consulta": "horario de visita en neonatología para abuelos"})`

Resultado:

```text
Régimen de visitas — Neonatología
Madre y padre tienen ingreso libre las 24 horas. Los abuelos pueden visitar martes y jueves de 16:00 a 17:00, uno por vez y con la presencia de uno de los padres. Los hermanos del recién nacido no ingresan al sector durante la temporada de virus respiratorios, de mayo a septiembre.

---

Régimen de visitas — Unidad de terapia intensiva de adultos
La unidad tiene dos franjas de visita: de 12:00 a 12:30 y de 19:00 a 19:30. Ingresa un solo visitante por vez, que debe ser mayor de 14 años. Antes de entrar, el visitante se lava las manos y se coloca el camisolín que entrega enfermería. El parte médico a la familia se da en la franja del mediodía.

---

Régimen de visitas — Clínica médica y cirugía general
Las visitas son de 16:00 a 20:00. Se admiten hasta dos visitantes por paciente al mismo tiempo. Los menores de 12 años pueden ingresar acompañados por un adulto responsable.
```

### Llamada al modelo 2

- generation id: `gen-1790904282-X2HDz8XcTFYvBDF6egca`
- usage: 1856 tokens de entrada, 56 de salida (0 de razonamiento), costo USD 0.000092

### Respuesta

```text
El horario de visita en neonatología para los abuelos es **martes y jueves de 16:00 a 17:00**, con las siguientes condiciones: ingresa **uno por vez** y debe estar presente **uno de los padres**.
```

## A02 — ¿Qué preparación necesita una colonoscopía?

### Llamada al modelo 1

- generation id: `gen-1790904286-siTwlLG9S86FHSCbUGyz`
- usage: 1515 tokens de entrada, 84 de salida (28 de razonamiento), costo USD 0.000124

**Herramienta:** `buscar_documentos({"consulta": "¿Cómo es la preparación para una colonoscopía?"})`

Resultado:

```text
Preparación para estudios de diagnóstico por imágenes y endoscopía — Colonoscopía
Los tres días previos se sigue una dieta sin residuos: sin frutas, verduras, legumbres ni cereales integrales. La tarde anterior se toma la solución evacuante de polietilenglicol, cuatro litros repartidos en cuatro horas. Desde la medianoche solo se permiten líquidos claros, y el ayuno total es de 6 horas antes del turno. El paciente tiene que venir acompañado, porque el estudio se hace con sedación.

---

Preparación para estudios de diagnóstico por imágenes y endoscopía — Ecografía abdominal
Se requiere ayuno de 6 horas y no tomar bebidas con gas el día anterior. Para la ecografía de vías urinarias, en cambio, se toma un litro de agua una hora antes y no se orina hasta el estudio.

---

Preparación para estudios de diagnóstico por imágenes y endoscopía — Ecografía ginecológica transabdominal
La vejiga tiene que estar llena: se toma un litro de agua una hora antes y no se orina hasta terminar el estudio.
```

### Llamada al modelo 2

- generation id: `gen-1790904290-QAoJGV4OZzvsnGl0FtuP`
- usage: 1836 tokens de entrada, 125 de salida (0 de razonamiento), costo USD 0.000180

### Respuesta

```text
La preparación para una colonoscopía es la siguiente:

- **Los 3 días previos:** dieta sin residuos (sin frutas, verduras, legumbres ni cereales integrales).
- **La tarde anterior:** tomar la solución evacuante de polietilenglicol, 4 litros repartidos en 4 horas.
- **Desde la medianoche:** solo líquidos claros.
- **Ayuno total:** 6 horas antes del turno.
- **Acompañante:** hay que venir acompañado, porque el estudio se hace con sedación.
```

## A03 — ¿Qué documentos tengo que llevar a la primera consulta con un especialista?

### Llamada al modelo 1

- generation id: `gen-1790904296-oC8nQhqT7bc0538haImh`
- usage: 1521 tokens de entrada, 103 de salida (51 de razonamiento), costo USD 0.000148

**Herramienta:** `buscar_documentos({"consulta": "¿Qué documentos hay que llevar a la primera consulta con un especialista?"})`

Resultado:

```text
Turnos en consultorios externos — Qué llevar a la primera consulta
DNI, credencial de la cobertura de salud, la derivación y los estudios previos relacionados con el motivo de consulta, en papel o en el teléfono.

---

Derechos del paciente e historia clínica — Copia de la historia clínica
El paciente, o su representante legal con poder, puede pedir una copia de su historia clínica en la mesa de entradas del archivo, en el subsuelo. La copia se entrega dentro de las 48 horas hábiles y es gratuita.

---

Ingreso a internación programada — Documentación
El día de la internación se presenta en admisión, en planta baja, el DNI, la credencial de la cobertura si la tiene, la orden de internación firmada por el médico y los estudios prequirúrgicos.
```

### Llamada al modelo 2

- generation id: `gen-1790904299-ytVANpv5CuLtJieSMrtN`
- usage: 1790 tokens de entrada, 68 de salida (0 de razonamiento), costo USD 0.000106

### Respuesta

```text
Para la primera consulta con un especialista en consultorios externos tenés que llevar:

- **DNI**
- **Credencial de la cobertura de salud**
- **La derivación**
- **Los estudios previos** relacionados con el motivo de consulta (en papel o en el teléfono)
```

## A04 — ¿Quiénes pueden donar sangre?

### Llamada al modelo 1

- generation id: `gen-1790904302-Q3iOPOTMmCJmA3ZjZAXt`
- usage: 1513 tokens de entrada, 90 de salida (28 de razonamiento), costo USD 0.000132

**Herramienta:** `buscar_documentos({"consulta": "¿Quiénes pueden donar sangre? Requisitos para donar sangre"})`

Resultado:

```text
Donación de sangre
El servicio de hemoterapia recibe donantes de lunes a sábado de 7:30 a 12:00, en el primer piso.

Pueden donar personas de 18 a 65 años que pesen más de 50 kilos y se sientan bien. No hay que venir en ayunas: se recomienda un desayuno liviano, sin lácteos ni grasas. Entre una donación y la siguiente tienen que pasar al menos 2 meses en los hombres y 3 meses en las mujeres.

No pueden donar por 12 meses quienes se hicieron un tatuaje o un piercing en ese período.

---

Turnos en consultorios externos — Qué llevar a la primera consulta
DNI, credencial de la cobertura de salud, la derivación y los estudios previos relacionados con el motivo de consulta, en papel o en el teléfono.

---

Derechos del paciente e historia clínica — Segunda opinión
El paciente tiene derecho a pedir una segunda opinión médica, dentro o fuera del hospital, sin perder su lugar en la atención.
```

### Llamada al modelo 2

- generation id: `gen-1790904307-4wckZkye2skf68o7hGFD`
- usage: 1832 tokens de entrada, 154 de salida (0 de razonamiento), costo USD 0.000217

### Respuesta

```text
Pueden donar sangre las personas de **18 a 65 años** que pesen **más de 50 kilos** y se sientan bien. No hay que ir en ayunas: se recomienda un desayuno liviano, sin lácteos ni grasas.

Además:
- Entre donaciones deben pasar al menos **2 meses** (hombres) y **3 meses** (mujeres).
- No pueden donar por **12 meses** quienes se hayan hecho un tatuaje o piercing en ese período.

El servicio de hemoterapia recibe donantes de **lunes a sábado de 7:30 a 12:00**, en el primer piso.
```

## A05 — ¿Hay camas libres en terapia intensiva ahora?

### Llamada al modelo 1

- generation id: `gen-1790904309-9wzNg8FYKYfYCPO8zIdw`
- usage: 1516 tokens de entrada, 86 de salida (37 de razonamiento), costo USD 0.000126

**Herramienta:** `consultar_camas({"sector": "terapia intensiva"})`

Resultado:

```text
{"sector": "terapia_intensiva", "fecha": "2026-10-05", "datos": {"total": 12, "ocupadas": 12, "libres": 0}}
```

### Llamada al modelo 2

- generation id: `gen-1790904313-AFsr6E5QZonpWcrxoawV`
- usage: 1624 tokens de entrada, 27 de salida (0 de razonamiento), costo USD 0.000052

### Respuesta

```text
No, en este momento no hay camas libres en terapia intensiva: las 12 camas están ocupadas.
```

## A06 — ¿Quién está de guardia en cardiología esta noche?

### Llamada al modelo 1

- generation id: `gen-1790904315-q6sHOV7m4NUe5Q33v2Cc`
- usage: 1517 tokens de entrada, 95 de salida (48 de razonamiento), costo USD 0.000138

**Herramienta:** `consultar_guardia({"especialidad": "cardiologia"})`

Resultado:

```text
{"especialidad": "cardiologia", "fecha": "2026-10-05", "datos": [{"profesional": "Dr. Julián Ferreyra", "horario": "08:00-20:00"}, {"profesional": "Dra. Paula Benítez", "horario": "20:00-08:00"}]}
```

### Llamada al modelo 2

- generation id: `gen-1790904320-hjaj5N8tKYiP23Ba81dw`
- usage: 1659 tokens de entrada, 103 de salida (55 de razonamiento), costo USD 0.000150

### Respuesta

```text
Esta noche (turno 20:00-08:00) está de guardia en cardiología la **Dra. Paula Benítez**.
```

## A07 — ¿Cuándo es el próximo turno disponible con traumatología?

### Llamada al modelo 1

- generation id: `gen-1790904325-y7toSztu7JVCP8MkMyBM`
- usage: 1518 tokens de entrada, 76 de salida (31 de razonamiento), costo USD 0.000114

**Herramienta:** `consultar_turnos({"especialidad": "traumatologia"})`

Resultado:

```text
{"especialidad": "traumatologia", "fecha": "2026-10-05", "datos": ["2026-10-07 08:40", "2026-10-07 09:00", "2026-10-08 14:20"]}
```

### Llamada al modelo 2

- generation id: `gen-1790904328-o2oIQe4R3EmUOP3BOT0R`
- usage: 1643 tokens de entrada, 31 de salida (0 de razonamiento), costo USD 0.000057

### Respuesta

```text
El próximo turno disponible con traumatología es el **miércoles 7 de octubre de 2026 a las 08:40**.
```

## A08 — ¿Tienen enalapril de 10 mg en la farmacia?

### Llamada al modelo 1

- generation id: `gen-1790904330-7D0djazMyKIirAdvKWfb`
- usage: 1520 tokens de entrada, 77 de salida (22 de razonamiento), costo USD 0.000115

**Herramienta:** `consultar_farmacia({"medicamento": "enalapril 10 mg"})`

Resultado:

```text
{"medicamento": "enalapril 10 mg", "fecha": "2026-10-05", "datos": {"stock": 0, "unidad": "comprimidos", "reposicion": "2026-10-09"}}
```

### Llamada al modelo 2

- generation id: `gen-1790904333-sddjyJmOK3hMSS5rmyEO`
- usage: 1643 tokens de entrada, 67 de salida (21 de razonamiento), costo USD 0.000104

### Respuesta

```text
No, en este momento no hay stock de enalapril 10 mg en la farmacia. La reposición está prevista para el 09/10/2026.
```

## A09 — ¿Cuánto se está esperando hoy en la guardia si me clasifican como verde?

### Llamada al modelo 1

- generation id: `gen-1790904336-mJoYqgCsIlIAcOQBNK4H`
- usage: 1525 tokens de entrada, 194 de salida (135 de razonamiento), costo USD 0.000265

**Herramienta:** `consultar_espera({})`

Resultado:

```text
{"fecha": "2026-10-05", "minutos_por_nivel": {"rojo": 0, "naranja": 7, "amarillo": 48, "verde": 135, "azul": 210}}
```

**Herramienta:** `buscar_documentos({"consulta": "tiempo máximo de espera en guardia para triage verde"})`

Resultado:

```text
Guardia y clasificación por prioridad (triage) — Los cinco niveles
- Nivel 1, rojo (resucitación): atención inmediata.
- Nivel 2, naranja (emergencia): atención en 10 minutos como máximo.
- Nivel 3, amarillo (urgencia): atención dentro de los 60 minutos.
- Nivel 4, verde (urgencia menor): atención dentro de las 2 horas.
- Nivel 5, azul (no urgente): atención dentro de las 4 horas, o derivación a consultorio externo.

---

Guardia y clasificación por prioridad (triage)
En la guardia de adultos del Hospital Provincial Arroyo Claro la atención no sigue el orden de llegada. Una enfermera clasifica a cada paciente en uno de cinco niveles según la urgencia, y ese nivel define el tiempo máximo de espera.

---

Guardia y clasificación por prioridad (triage) — Reclasificación
Si los síntomas empeoran durante la espera, el paciente o su acompañante avisan en el mostrador de triage y la enfermera vuelve a evaluar. La guardia pediátrica tiene su propio triage y su propia sala de espera, con ingreso por la calle Los Tilos.
```

### Llamada al modelo 2

- generation id: `gen-1790904344-bNdIMLSJLYp9zKhDYnkI`
- usage: 1957 tokens de entrada, 127 de salida (73 de razonamiento), costo USD 0.000184

### Respuesta

```text
Hoy en la guardia, si te clasifican como **verde (urgencia menor)**, la espera actual es de **135 minutos**.

Según la norma del hospital, el tiempo máximo de espera para el nivel verde es de **2 horas**.
```

## A10 — Quiero internar a mi nene en pediatría, ¿hay lugar y me puedo quedar con él?

### Llamada al modelo 1

- generation id: `gen-1790904347-L1AfvyM6i2X2B32cadvK`
- usage: 1529 tokens de entrada, 183 de salida (81 de razonamiento), costo USD 0.000251

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

---

Régimen de visitas — Pediatría
Madre, padre o tutor pueden permanecer las 24 horas junto al paciente. Para el resto de los familiares, la visita es de 17:00 a 19:00, con un máximo de dos personas.

---

Régimen de visitas — Maternidad
La visita en la sala de puérperas es de 15:00 a 20:00. La persona acompañante de la madre puede quedarse también durante la noche.
```

### Llamada al modelo 2

- generation id: `gen-1790904349-jmXjBPSNknluZOCssSFZ`
- usage: 1848 tokens de entrada, 59 de salida (0 de razonamiento), costo USD 0.000095

### Respuesta

```text
Sí, hay lugar: en pediatría hay 24 camas, 17 ocupadas y 7 libres.

Y sí, podés quedarte con él: en pediatría, madre, padre o tutor pueden permanecer las 24 horas junto al paciente.
```

## A11 — Necesito turno con cardiología, ¿cuál es el primero y qué tengo que llevar?

### Llamada al modelo 1

- generation id: `gen-1790904351-0FISipetI4GznYVW3j5E`
- usage: 1526 tokens de entrada, 168 de salida (77 de razonamiento), costo USD 0.000232

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

---

Turnos en consultorios externos — Llegada
Se recomienda llegar 15 minutos antes para hacer la admisión. Pasados 20 minutos de la hora del turno, el profesional puede atender a otro paciente y el turno se reprograma.

---

Salud mental
La guardia de salud mental funciona las 24 horas dentro de la guardia general. Los consultorios externos de psicología y psiquiatría atienden con turno, de lunes a viernes de 8:00 a 18:00.

Para la primera consulta en psicología no se necesita derivación: se pide turno de admisión, y el equipo define después el tratamiento.
```

### Llamada al modelo 2

- generation id: `gen-1790904356-XZrPn9t1dumZznYiI5f3`
- usage: 1906 tokens de entrada, 129 de salida (0 de razonamiento), costo USD 0.000186

### Respuesta

```text
El primer turno disponible en cardiología es el **14 de octubre de 2026 a las 09:30**.

Para la consulta tenés que llevar:
- **DNI**
- **Credencial de la cobertura de salud**
- **La derivación**
- **Estudios previos** relacionados con el motivo de consulta (en papel o en el teléfono)

Además, se recomienda llegar **15 minutos antes** para hacer la admisión. Pasados 20 minutos de la hora del turno, el profesional puede atender a otro paciente y el turno se reprograma.
```

## A12 — Me recetaron insulina NPH, ¿la tienen y qué necesito para retirarla?

### Llamada al modelo 1

- generation id: `gen-1790904361-kX4sppvOAh2DdGjvq0u5`
- usage: 1525 tokens de entrada, 171 de salida (65 de razonamiento), costo USD 0.000235

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

---

Derechos del paciente e historia clínica — Copia de la historia clínica
El paciente, o su representante legal con poder, puede pedir una copia de su historia clínica en la mesa de entradas del archivo, en el subsuelo. La copia se entrega dentro de las 48 horas hábiles y es gratuita.

---

Ingreso a internación programada — Qué traer
Ropa cómoda, elementos de higiene personal y la medicación habitual en su envase original, con la lista de dosis. No se recomienda traer objetos de valor; el hospital no se responsabiliza por su pérdida.
```

### Llamada al modelo 2

- generation id: `gen-1790904367-GjEijFAvj3KN2e3Qm10l`
- usage: 2028 tokens de entrada, 248 de salida (88 de razonamiento), costo USD 0.000339

### Respuesta

```text
**Stock de insulina NPH:** Hoy no hay stock en la farmacia (0 frascos). La reposición está prevista para el **12/10/2026**.

**Para retirarla (cuando haya stock):**
- Presentar el **DNI del paciente**.
- Si retira otra persona, debe llevar su propio DNI y el del paciente.
- La receta debe ser de un profesional de la institución y tiene validez de **30 días** desde su emisión.
- La farmacia de pacientes ambulatorios está en planta baja, junto a admisión, y atiende de lunes a viernes de 8:00 a 20:00 (no entrega los fines de semana).
```
