# Corrida del benchmark — agente con tools de LangChain (parte 2)

- **Fecha:** 2026-10-01 22:22:11
- **Modelo:** `deepseek/deepseek-v4-flash-0731` por OpenRouter, temperatura 0
- **Preguntas:** `datos/preguntas_agente_dev.jsonl` (12)
- **Salida:** `experimentos/agente/03-k2.jsonl`
- **Herramientas:** funciones de `herramientas.py`, en el mismo proceso
- **Consumo de la key (`GET /api/v1/key`):** USD 0.065049 antes, USD 0.078756 después, diferencia USD 0.013707
- **Totales:** 24 llamadas al modelo, 39103 tokens de entrada, 2576 de salida (918 de razonamiento), costo USD 0.003720

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
| A01 | buscar_documentos | 2 | 3315 | 149 | 37 | 0.000227 |
| A02 | buscar_documentos | 2 | 3294 | 205 | 28 | 0.000298 |
| A03 | buscar_documentos | 2 | 3249 | 162 | 43 | 0.000242 |
| A04 | buscar_documentos | 2 | 3300 | 248 | 28 | 0.000353 |
| A05 | consultar_camas | 2 | 3140 | 113 | 37 | 0.000179 |
| A06 | consultar_guardia | 2 | 3176 | 131 | 48 | 0.000202 |
| A07 | consultar_turnos | 2 | 3161 | 107 | 31 | 0.000171 |
| A08 | consultar_farmacia | 2 | 3163 | 163 | 58 | 0.000243 |
| A09 | consultar_espera | 2 | 3148 | 306 | 275 | 0.000426 |
| A10 | consultar_camas, buscar_documentos | 2 | 3328 | 301 | 137 | 0.000421 |
| A11 | consultar_turnos, buscar_documentos | 2 | 3340 | 291 | 66 | 0.000409 |
| A12 | consultar_farmacia, buscar_documentos | 2 | 3489 | 400 | 130 | 0.000550 |
| **Total** | | 24 | 39103 | 2576 | 918 | 0.003720 |

## A01 — ¿Cuál es el horario de visita en neonatología para los abuelos?

### Llamada al modelo 1

- generation id: `gen-1790904131-TyuDXrBENHcltG9pUl5s`
- usage: 1523 tokens de entrada, 93 de salida (37 de razonamiento), costo USD 0.000135

**Herramienta:** `buscar_documentos({"consulta": "horario de visita en neonatología para abuelos"})`

Resultado:

```text
Régimen de visitas — Neonatología
Madre y padre tienen ingreso libre las 24 horas. Los abuelos pueden visitar martes y jueves de 16:00 a 17:00, uno por vez y con la presencia de uno de los padres. Los hermanos del recién nacido no ingresan al sector durante la temporada de virus respiratorios, de mayo a septiembre.

---

Régimen de visitas — Unidad de terapia intensiva de adultos
La unidad tiene dos franjas de visita: de 12:00 a 12:30 y de 19:00 a 19:30. Ingresa un solo visitante por vez, que debe ser mayor de 14 años. Antes de entrar, el visitante se lava las manos y se coloca el camisolín que entrega enfermería. El parte médico a la familia se da en la franja del mediodía.
```

### Llamada al modelo 2

- generation id: `gen-1790904134-ovwnsVf5KuFN5wNDy4Sk`
- usage: 1792 tokens de entrada, 56 de salida (0 de razonamiento), costo USD 0.000091

### Respuesta

```text
El horario de visita en neonatología para los abuelos es **martes y jueves de 16:00 a 17:00**, con las siguientes condiciones: ingresa **uno por vez** y debe estar presente **uno de los padres**.
```

## A02 — ¿Qué preparación necesita una colonoscopía?

### Llamada al modelo 1

- generation id: `gen-1790904138-cvm0VkTHnQBJ5coNhFhX`
- usage: 1515 tokens de entrada, 84 de salida (28 de razonamiento), costo USD 0.000124

**Herramienta:** `buscar_documentos({"consulta": "¿Cómo es la preparación para una colonoscopía?"})`

Resultado:

```text
Preparación para estudios de diagnóstico por imágenes y endoscopía — Colonoscopía
Los tres días previos se sigue una dieta sin residuos: sin frutas, verduras, legumbres ni cereales integrales. La tarde anterior se toma la solución evacuante de polietilenglicol, cuatro litros repartidos en cuatro horas. Desde la medianoche solo se permiten líquidos claros, y el ayuno total es de 6 horas antes del turno. El paciente tiene que venir acompañado, porque el estudio se hace con sedación.

---

Preparación para estudios de diagnóstico por imágenes y endoscopía — Ecografía abdominal
Se requiere ayuno de 6 horas y no tomar bebidas con gas el día anterior. Para la ecografía de vías urinarias, en cambio, se toma un litro de agua una hora antes y no se orina hasta el estudio.
```

### Llamada al modelo 2

- generation id: `gen-1790904142-pgzCfCTr7ZX8qBE8LEej`
- usage: 1779 tokens de entrada, 121 de salida (0 de razonamiento), costo USD 0.000174

### Respuesta

```text
La preparación para una colonoscopía es la siguiente:

- **3 días previos:** dieta sin residuos (sin frutas, verduras, legumbres ni cereales integrales).
- **Tarde anterior:** tomar la solución evacuante de polietilenglicol, 4 litros repartidos en 4 horas.
- **Desde la medianoche:** solo líquidos claros.
- **Ayuno total:** 6 horas antes del turno.
- **Acompañante:** debe venir acompañado porque el estudio se hace con sedación.
```

## A03 — ¿Qué documentos tengo que llevar a la primera consulta con un especialista?

### Llamada al modelo 1

- generation id: `gen-1790904148-P6rYjRkoH3kwIqfpNhd7`
- usage: 1521 tokens de entrada, 99 de salida (43 de razonamiento), costo USD 0.000143

**Herramienta:** `buscar_documentos({"consulta": "¿Qué documentos hay que llevar a la primera consulta con un especialista?"})`

Resultado:

```text
Turnos en consultorios externos — Qué llevar a la primera consulta
DNI, credencial de la cobertura de salud, la derivación y los estudios previos relacionados con el motivo de consulta, en papel o en el teléfono.

---

Derechos del paciente e historia clínica — Copia de la historia clínica
El paciente, o su representante legal con poder, puede pedir una copia de su historia clínica en la mesa de entradas del archivo, en el subsuelo. La copia se entrega dentro de las 48 horas hábiles y es gratuita.
```

### Llamada al modelo 2

- generation id: `gen-1790904151-6oFDQuu7X1UClWDCSQ8g`
- usage: 1728 tokens de entrada, 63 de salida (0 de razonamiento), costo USD 0.000099

### Respuesta

```text
Para la primera consulta con un especialista tenés que llevar:

- **DNI**
- **Credencial de la cobertura de salud**
- **La derivación**
- **Estudios previos** relacionados con el motivo de consulta (en papel o en el teléfono)
```

## A04 — ¿Quiénes pueden donar sangre?

### Llamada al modelo 1

- generation id: `gen-1790904155-PzumILEQ0F5JHcYir7wD`
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
```

### Llamada al modelo 2

- generation id: `gen-1790904158-pjMQYkf0riQ1QKm2xZ4X`
- usage: 1787 tokens de entrada, 158 de salida (0 de razonamiento), costo USD 0.000222

### Respuesta

```text
Según los documentos del hospital, pueden donar sangre:

- **Personas de 18 a 65 años** que pesen **más de 50 kilos** y se sientan bien.
- No hace falta ir en ayunas: se recomienda un desayuno liviano, sin lácteos ni grasas.
- Entre donación y donación deben pasar al menos **2 meses en hombres** y **3 meses en mujeres**.
- **No pueden donar por 12 meses** quienes se hayan hecho un tatuaje o piercing en ese período.

El servicio de hemoterapia recibe donantes de lunes a sábado de 7:30 a 12:00, en el primer piso.
```

## A05 — ¿Hay camas libres en terapia intensiva ahora?

### Llamada al modelo 1

- generation id: `gen-1790904161-OriXJO752L5ZouWA19Ew`
- usage: 1516 tokens de entrada, 86 de salida (37 de razonamiento), costo USD 0.000126

**Herramienta:** `consultar_camas({"sector": "terapia intensiva"})`

Resultado:

```text
{"sector": "terapia_intensiva", "fecha": "2026-10-05", "datos": {"total": 12, "ocupadas": 12, "libres": 0}}
```

### Llamada al modelo 2

- generation id: `gen-1790904165-hEf5doJIZqo21oH0ynm1`
- usage: 1624 tokens de entrada, 27 de salida (0 de razonamiento), costo USD 0.000052

### Respuesta

```text
No, en este momento no hay camas libres en terapia intensiva: las 12 camas están ocupadas.
```

## A06 — ¿Quién está de guardia en cardiología esta noche?

### Llamada al modelo 1

- generation id: `gen-1790904168-gl5Wt9uLcFKngGslmUMh`
- usage: 1517 tokens de entrada, 95 de salida (48 de razonamiento), costo USD 0.000138

**Herramienta:** `consultar_guardia({"especialidad": "cardiologia"})`

Resultado:

```text
{"especialidad": "cardiologia", "fecha": "2026-10-05", "datos": [{"profesional": "Dr. Julián Ferreyra", "horario": "08:00-20:00"}, {"profesional": "Dra. Paula Benítez", "horario": "20:00-08:00"}]}
```

### Llamada al modelo 2

- generation id: `gen-1790904173-ojBaYAbfm5mcRxElP2vu`
- usage: 1659 tokens de entrada, 36 de salida (0 de razonamiento), costo USD 0.000064

### Respuesta

```text
Esta noche (guardia nocturna de 20:00 a 08:00) está de guardia en cardiología la **Dra. Paula Benítez**.
```

## A07 — ¿Cuándo es el próximo turno disponible con traumatología?

### Llamada al modelo 1

- generation id: `gen-1790904177-w5iKDhiwZJYFjAfg9VjD`
- usage: 1518 tokens de entrada, 76 de salida (31 de razonamiento), costo USD 0.000114

**Herramienta:** `consultar_turnos({"especialidad": "traumatologia"})`

Resultado:

```text
{"especialidad": "traumatologia", "fecha": "2026-10-05", "datos": ["2026-10-07 08:40", "2026-10-07 09:00", "2026-10-08 14:20"]}
```

### Llamada al modelo 2

- generation id: `gen-1790904180-MdGzBMKjcmVI9XTgzn1F`
- usage: 1643 tokens de entrada, 31 de salida (0 de razonamiento), costo USD 0.000057

### Respuesta

```text
El próximo turno disponible con traumatología es el **miércoles 7 de octubre de 2026 a las 08:40**.
```

## A08 — ¿Tienen enalapril de 10 mg en la farmacia?

### Llamada al modelo 1

- generation id: `gen-1790904181-Iz1QQTEZKhk6AUyho9aS`
- usage: 1520 tokens de entrada, 96 de salida (37 de razonamiento), costo USD 0.000139

**Herramienta:** `consultar_farmacia({"medicamento": "enalapril 10 mg"})`

Resultado:

```text
{"medicamento": "enalapril 10 mg", "fecha": "2026-10-05", "datos": {"stock": 0, "unidad": "comprimidos", "reposicion": "2026-10-09"}}
```

### Llamada al modelo 2

- generation id: `gen-1790904186-8Zxrtr8oBjrf0LC9d7cp`
- usage: 1643 tokens de entrada, 67 de salida (21 de razonamiento), costo USD 0.000104

### Respuesta

```text
No, en este momento no hay stock de enalapril 10 mg en la farmacia. La reposición está prevista para el 09/10/2026.
```

## A09 — ¿Cuánto se está esperando hoy en la guardia si me clasifican como verde?

### Llamada al modelo 1

- generation id: `gen-1790904189-IxDQ1bePJJRdkBARBH0O`
- usage: 1525 tokens de entrada, 279 de salida (275 de razonamiento), costo USD 0.000374

**Herramienta:** `consultar_espera({})`

Resultado:

```text
{"fecha": "2026-10-05", "minutos_por_nivel": {"rojo": 0, "naranja": 7, "amarillo": 48, "verde": 135, "azul": 210}}
```

### Llamada al modelo 2

- generation id: `gen-1790904196-5MXLYoO0HXnJr6q1h321`
- usage: 1623 tokens de entrada, 27 de salida (0 de razonamiento), costo USD 0.000052

### Respuesta

```text
Hoy, si la clasifican como nivel verde en la guardia, la espera es de 135 minutos.
```

## A10 — Quiero internar a mi nene en pediatría, ¿hay lugar y me puedo quedar con él?

### Llamada al modelo 1

- generation id: `gen-1790904197-T8Sgmj4V7TaQP1BnLKYN`
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
```

### Llamada al modelo 2

- generation id: `gen-1790904199-CrepWzNu5wKpBEl0o2FG`
- usage: 1799 tokens de entrada, 118 de salida (56 de razonamiento), costo USD 0.000170

### Respuesta

```text
Sí, hay lugar: en pediatría hay 24 camas, 17 ocupadas y 7 libres.

Y sí, puede quedarse: en pediatría, la madre, el padre o el tutor pueden permanecer las 24 horas junto al paciente.
```

## A11 — Necesito turno con cardiología, ¿cuál es el primero y qué tengo que llevar?

### Llamada al modelo 1

- generation id: `gen-1790904201-VVr7ZQGZLosAKTeDAuRV`
- usage: 1526 tokens de entrada, 161 de salida (66 de razonamiento), costo USD 0.000223

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
```

### Llamada al modelo 2

- generation id: `gen-1790904207-fZhsl1VscDTTba3C86TK`
- usage: 1814 tokens de entrada, 130 de salida (0 de razonamiento), costo USD 0.000186

### Respuesta

```text
El primer turno disponible en cardiología es el **14 de octubre de 2026 a las 09:30**.

Para la primera consulta tenés que llevar:
- **DNI**
- **Credencial de la cobertura de salud**
- **La derivación**
- **Estudios previos** relacionados con el motivo de consulta (en papel o en el teléfono)

Además, se recomienda llegar **15 minutos antes** para hacer la admisión. Pasados 20 minutos de la hora del turno, el profesional puede atender a otro paciente y el turno se reprograma.
```

## A12 — Me recetaron insulina NPH, ¿la tienen y qué necesito para retirarla?

### Llamada al modelo 1

- generation id: `gen-1790904212-jg6ORzsNeps46SznY35c`
- usage: 1525 tokens de entrada, 169 de salida (63 de razonamiento), costo USD 0.000233

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
```

### Llamada al modelo 2

- generation id: `gen-1790904218-CGVARjRyks4tTtQaDJNl`
- usage: 1964 tokens de entrada, 231 de salida (67 de razonamiento), costo USD 0.000317

### Respuesta

```text
**Insulina NPH:** Hoy no hay stock en la farmacia (0 frascos). La reposición está prevista para el **12/10/2026**.

**Para retirarla** (cuando haya stock), según las normas del hospital:
- Presentar el **DNI del paciente**.
- Si retira otra persona, debe llevar **su propio DNI y el del paciente**.
- La receta debe ser de un profesional de la institución y tiene una validez de **30 días** desde su emisión.
- La farmacia de pacientes ambulatorios está en planta baja, junto a admisión, y atiende de lunes a viernes de 8:00 a 20:00 (no entrega los fines de semana).
```
