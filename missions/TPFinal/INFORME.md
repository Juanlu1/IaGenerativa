# Informe: TP Final: agente de admisión de guardia

## Parte 1: Curado e ingeniería de datos

### Método

`curar.py` enlaza cada registro de `historial/historial.csv` con su traza del
mismo ID y evalúa los campos de la ficha contra las normas originales y sus
parámetros. También revisa consultas y verificaciones de cobertura en la traza.
Una violación escrita clasifica la fila como `error`; si no la hay, una
desviación de las costumbres documentadas clasifica como `ruido`; las demás
filas quedan `correcta`. Los motivos por fila quedan en `curado/auditoria.csv`.

La clasificación cubre las 2.000 filas y sus 2.000 trazas. La primera pasada
usaba el corte de 76 años para la costumbre del voluntariado; la segunda, el
de 75 que muestra el historial (ver más abajo), y pasó 10 filas de `ruido` a
`correcta`:

| Tipo | Primera pasada (corte 76) | Actual (corte 75) |
|---|---:|---:|
| Correcta | 1.590 | 1.600 |
| Error | 240 | 240 |
| Ruido | 170 | 160 |

La clasificación es una primera pasada automatizada. Antes de usarla como
resultado final, el equipo debe revisar las filas de `curado/auditoria.csv`, en
particular las que tienen más de un motivo o una elección interpretativa.

### Costumbres identificadas

1. **Aviso al voluntariado para una persona de 75 años o más sin acompañante.**
   Aparece en 207 de 226 filas comparables (92%). Fuera de ese grupo, hay 132
   avisos en 1.774 filas (7%), y todos, como las 19 excepciones, son de OP-04,
   OP-11 y OP-17, que deciden el aviso sin seguir ninguna regla visible: entre
   los otros 17 operadores la costumbre se cumple 185 de 185 veces. No se
   deduce de la edad de box definida por P-ADM-2. La lista de evidencia y las
   excepciones está en `costumbres.md`.
   La primera pasada usaba 76 años (196 de 215 filas, 143 avisos fuera). La
   revisión de [`revision_parte1.md`](revision_parte1.md) mostró que los 11
   pacientes de 75 años sin acompañante tienen el aviso y que la práctica lo
   espera (`pev-006`); con el corte en 75, 10 filas pasaron de `ruido` a
   `correcta` (`H-0045`, `H-0576`, `H-0943`, `H-1269`, `H-1348`, `H-1592`,
   `H-1613`, `H-1677`, `H-1786` y `H-1884`; `H-1593` sigue como error por el
   plazo de su circuito).
2. **Prioridad de la prepaga cuando se presentan una obra social y una prepaga.**
   Se verificó la prepaga en 184 de 193 casos comparables (95%). Las normas no
   fijan una prioridad entre ambas; las 9 excepciones, también de OP-04, OP-11
   y OP-17, y la evidencia están en `costumbres.md`. Si la prepaga resulta
   inactiva, se registra sin cobertura sin verificar la obra social.

### Conversaciones de entrenamiento

- `curado/conversaciones_reales.jsonl`: 1.600 conversaciones construidas desde
  las trazas clasificadas como correctas, con el mensaje de sistema y el formato
  de herramientas de `admision/ejemplo.py`.
- `curado/conversaciones_sinteticas.jsonl`: 600 conversaciones generadas por
  `admision.generador` y resueltas por una política determinista que usa las
  normas y costumbres anteriores, con el buscador del grupo y las consultas de
  las trazas de la cátedra. La generación reparte las versiones `original`,
  `b` y `c` (200 cada una), con sus parámetros correspondientes. La semilla es
  `20261108`; la configuración está en `curado/sinteticas_config.json`. La
  política resuelve 50/50 casos de práctica en las tres versiones
  (`validar_politica.py`; la primera pasada, con 500 conversaciones, un
  buscador de palabras clave y el corte del voluntariado en 76 años, daba
  49/50).
- Las 800 trazas de referencia de la cátedra permanecen separadas en
  `entrenamiento/trazas.jsonl`.

La distribución real y las frecuencias sintéticas se registran en
`curado/resumen.json` y `curado/sinteticas_resumen.json`. Las conversaciones
sintéticas se mantienen separadas de las trazas reales para poder ponderarlas o
excluirlas al entrenar.

### Regeneración

Desde esta carpeta, con el entorno preparado mediante `uv sync`:

```bash
uv run python curar.py
uv run python generar_sinteticas.py
```

`curar.py` genera `historial_clasificado.csv`, `costumbres.md`,
`curado/auditoria.csv`, `curado/conversaciones_reales.jsonl` y
`curado/resumen.json`. `generar_sinteticas.py` genera las conversaciones
sintéticas y sus archivos de configuración y resumen.

## Parte 2: Buscador propio (RAG)

### Método

`parte2/rag_buscador.py` construye el índice con la carpeta de normas recibida
en cada corrida, mediante el cargador oficial de `admision.normas`. Usa un
ranking BM25 propio que combina la similitud de la sección completa y la de
su apartado más pertinente. Devuelve dos secciones completas para conservar
las excepciones, precedencias y valores de parámetros. No llama a servicios
externos durante la búsqueda ni contiene números de las normas fijados en el
código. Los experimentos y su justificación están en `parte2/RAG.md`.

### Evaluación aislada

Comando, desde esta carpeta:

```bash
uv run python -m admision.evaluar_rag --entrega parte2/entrega_rag.py --normas normas/original --consultas rag/consultas_dev.jsonl
```

Sobre las 60 consultas de desarrollo, el buscador obtuvo recall de evidencia
**1,000**, precisión **0,567**, **590 tokens por consulta** y **60/60** consultas
con toda la evidencia. La referencia BM25 de la cátedra informa 0,875, 0,492,
580 tokens y 51/60, respectivamente. Los tokens siguen la estimación del
evaluador oficial de cuatro caracteres por token.

`parte2/evaluar_variantes_rag.py` repite la evaluación con `original`, `b` y
`c`. Como el set de desarrollo contiene los números de `original`, el script
ajusta solo esas evidencias numéricas en memoria para cada versión. Dio 60/60
en las tres versiones. Es una prueba de que el buscador lee los parámetros de
la carpeta recibida, no un test independiente.

También se comparó el ranking con las 2.457 búsquedas de las 800 trazas de
referencia mediante `parte2/validar_trazas_rag.py`. La unión de secciones
recuperadas por caso cubrió 2.891 de los 3.652 IDs de `fundamentos` anotados
en esas fichas, igual que el ranking solo por sección; el ranking elegido usó
540 tokens promedio por búsqueda frente a 552 de esa alternativa. Los
`fundamentos` no son etiquetas oficiales por consulta, así que este contraste
sirve para detectar regresiones, no para puntuar al agente.

`entrega.py` usa este buscador en `construir_buscador`; los casos resueltos,
el contexto y el tiempo con el agente completo están en las Partes 3 y 4. El
60/60 corresponde al set de desarrollo del RAG; no estima el test secreto.

## Parte 3: Optimización de prompt, antes de entrenar

Todo se hizo con Gemma 4 E4B sin entrenar (`google/gemma-4-E4B-it`, revisión
`4ecc2ba63bcac23ba4a767fc87025b1450f84c9c`), servido con vLLM 0.33.0 (transformers 5.20.2) en una A100 de 40 GB de
Modal. Después, para entrenar y servir el adaptador con la misma pila, el repositorio pasó a vLLM 0.34.0
(transformers 5.22.2, el mismo torch 2.14.0; ver Parte 4, Configuración). Las evaluaciones de esta parte son las de
vLLM 0.33.0; la base y el prompt optimizado se repitieron con vLLM 0.34.0 al final de la sección (Repetición con
vLLM 0.34.0).

### Qué se optimiza

Solo el texto del mensaje de sistema. El resto del agente es el de `entrega.py` sin cambios: el `AgenteJSON` del kit
(`admision/ejemplo.py`), el mismo formato de mensajes (una llamada a una herramienta por turno, en JSON), el buscador
de la Parte 2 y la misma generación determinista (temperatura 0). Así el prompt se optimiza en el mismo formato con el
que después se evalúa y se entrena.

El punto de partida es `prompt_base.txt`, el mensaje de sistema de `admision/ejemplo.py` tal cual.

### Largo del prompt

Se mide en tokens con el tokenizer de Gemma 4 E4B (misma revisión), sobre el texto del mensaje de sistema solo, sin
la plantilla de chat (`AutoTokenizer.encode(texto, add_special_tokens=False)`). `optimizar_prompt.py` usa la misma
medida para la penalización por largo; si no puede cargar el tokenizer, usa caracteres / 4 y lo anota en su
`resumen.json`.

| Prompt | Tokens | Caracteres |
|---|---:|---:|
| `prompt_base.txt` | 615 | 2.232 |
| `prompt_corto.txt` | 467 | 1.634 |
| `prompt_optimizado.txt` | 693 | 2.429 |

Los 615 y 693 tokens quedan en `corridas/gepa/gepa1/log.jsonl` (candidatos 0 y 9). Los 467 de `prompt_corto.txt` no
quedaron en ningún archivo de corrida; se recalcularon (y dan 615, 467 y 693) con:

```bash
uv run python -c "from transformers import AutoTokenizer as T; t=T.from_pretrained('google/gemma-4-E4B-it', revision='4ecc2ba63bcac23ba4a767fc87025b1450f84c9c'); [print(f, len(t.encode(open(f).read(), add_special_tokens=False))) for f in ('prompt_base.txt','prompt_corto.txt','prompt_optimizado.txt')]"
```

### Prompt corto, a mano

`prompt_corto.txt` es `prompt_base.txt` acortado a mano sin sacar ninguna regla: las cinco herramientas con todos sus
argumentos y valores posibles, los ocho campos de la ficha más `fundamentos`, el protocolo (solo un objeto JSON por
turno, una herramienta por turno, el caso termina con `registrar_decision`), que el agente no toma decisiones clínicas
y qué normas tiene que buscar antes de decidir. Se sacaron las descripciones repetidas y la redacción larga de los
argumentos. Queda 24 % más corto (de 615 a 467 tokens). `config_corto.yaml` es `config.yaml` con ese prompt.

### Optimización con GEPA

`optimizar_prompt.py` usa GEPA (paquete `gepa` 0.1.4, el motor que corre debajo de `dspy.GEPA` en DSPy 3.4.1) con
un adaptador propio (`AdaptadorAdmision`). No se usó un módulo de DSPy porque el agente juega los casos en lote con
vLLM y con su propio formato de mensajes; envolverlo en una firma de DSPy habría cambiado el formato con el que se
optimiza respecto del que se evalúa.

- **Candidato:** un solo componente, el texto del mensaje de sistema.
- **Evaluación:** por cada candidato, el adaptador arma el agente de `entrega.py` con ese mensaje y juega todos los
  casos del lote en una sola tanda de vLLM, en el entorno real del kit (`admision.entorno.Entorno`, con el buscador
  armado con las normas de la versión de cada caso).
- **Métrica por caso:** controles aprobados / 9 según el comparador del kit (`admision.comparar.comparar`), menos
  `--penalizacion` puntos por cada 1.000 tokens del prompt (por defecto 0,02: el prompt base pierde 0,0123).
- **Devolución en texto para la reflexión:** cuántos controles aprobó, cada control que falló con el valor esperado y
  el registrado (en la verificación, qué entidad había que consultar, cuáles no y cuáles consultó), si respondió sin
  JSON o no llegó a registrar, qué buscó en las normas, la nota de triage completa y las llamadas a herramientas.
- **Modelo de reflexión:** por defecto la misma Gemma local, con temperatura 0,7 y semilla por llamada (semilla + número
  de llamada), para que las propuestas varíen pero se puedan reproducir. Si hay `ANTHROPIC_API_KEY` usa Claude
  (`claude-opus-5-5`, SDK oficial de Anthropic) y si no, con `OPENAI_API_KEY`, un modelo de OpenAI por DSPy
  (`--modelo-reflexion`). Los modelos pagos se usan solo para desarrollar el prompt, nunca dentro del agente.
- **Plantilla de reflexión propia**, en español. La de GEPA pide incluir en la instrucción toda la información
  factual de los ejemplos, lo que llevaría a copiar los números de las normas al prompt. Como en el test esos números
  cambian, la plantilla lo prohíbe: el agente tiene que buscarlos con `buscar_normativa`. También exige conservar las
  herramientas, los campos y el protocolo, y pide un mensaje corto.
- **Selección:** frente de Pareto por caso de validación (`candidate_selection_strategy="pareto"`), minilotes de
  reflexión del tamaño del presupuesto. El prompt final es el candidato de mayor puntaje en validación (a igual
  puntaje, el más corto).
- **Semilla:** `--semilla` (por defecto 0) fija la elección de casos, el orden de GEPA y la reflexión local.

| Presupuesto | Casos de optimización | Casos de validación | Tope de casos jugados | Tope de tiempo | Minilote |
|---|---:|---:|---:|---:|---:|
| `prueba` | 6 | 6 | 40 | 10 minutos | 3 |
| `completo` (default) | 90 | 45 | 3.000 | 90 minutos | 6 |

El presupuesto completo está pensado para 1,5 horas en la A100; el tope de tiempo lo garantiza aunque cada
iteración tarde más de lo previsto. Cada valor se puede cambiar por argumento.

### Casos usados

**No se usan los 50 casos de práctica.** Con ellos se mide la tabla del informe; optimizar el prompt sobre esos mismos
casos daría números optimistas. Tampoco se usa ningún caso del test, que no tenemos.

Se investigó si se podían armar casos con respuesta desde el historial, y se puede. `casos_optimizacion.py` arma un
caso del kit (`admision.casos.Caso`) por cada fila clasificada `correcta` en `historial_clasificado.csv`:

- el triage y los documentos salen de la fila de `historial/historial.csv`;
- el nombre, el id del paciente y el motivo por el que no puede responder salen de la nota de triage de
  `historial/trazas.jsonl`;
- lo que contesta el paciente (cobertura, ART) y lo que informa cada entidad salen de lo que el operador preguntó y
  verificó en la traza. Si el operador no preguntó la cobertura porque había credencial, el paciente declara la
  credencial que cuenta.

La ficha esperada de cada caso se calcula para las normas original, b y c con `etiquetar`, que aplica NOR-ADM-01 a
03, NOR-COB-01 a 04 y NOR-TDE-01 a 04 con los parámetros de cada versión, más las dos costumbres de `costumbres.md`
(preferir la prepaga si hay dos credenciales y avisar al voluntariado desde los 75 años sin acompañante).

Controles:

1. **El etiquetador reproduce las 150 fichas esperadas de la práctica** (50 casos x 3 versiones, los 8 campos, la
   entidad a verificar y las prohibidas). Acá la práctica solo sirve para comprobar el etiquetador; no entra en la
   optimización.
2. **Reconstrucción exacta:** la nota de triage que arma el entorno del kit con el caso reconstruido tiene que ser
   idéntica, carácter por carácter, a la que vio el operador. Si no, la fila se descarta.
3. **Consistencia con el operador:** con las normas originales, la ficha calculada tiene que ser igual a la que
   registró el operador, y su verificación tiene que aprobar el control calculado. Si no, la fila se descarta.

En el commit desde el que se lanzó `gepa1` (`44c8299`, con la clasificación de la primera pasada) pasan las 1.590
filas correctas, sin descartes (`uv run python casos_optimizacion.py`; `"disponibles": 1590` en
`corridas/gepa/gepa1/resumen.json`). Por circuito: 509 sepsis, 494 sin circuito, 340 ECG y 247 ACV; por cobertura:
756 sin cobertura, 311 prepaga, 306 ART y 217 obra social (verificado volviendo a correr el script en ese commit).
Con la clasificación actual (corte del voluntariado en 75 años, Parte 1) el mismo comando da 1.600 casos: 511 sepsis,
499 sin circuito, 342 ECG y 248 ACV; 761 sin cobertura, 311 prepaga, 310 ART y 218 obra social. GEPA no se volvió a
correr con esos 10 casos de más.

Límite: el control 3 no es independiente de la Parte 1. Una fila es `correcta` justamente porque cumple las normas y
las costumbres, así que el etiquetador y la clasificación comparten la misma lectura de las normas. El control
independiente es el 1, contra las fichas oficiales de la práctica.

De esas filas, `optimizar_prompt.py` elige con la semilla los casos de optimización y de validación, sin repetir caso
entre los dos conjuntos, y reparte la versión de las normas en rotación (original, b, c), así el prompt no se ajusta a
los números de una sola versión.

### Comandos

Prueba en la Mac, sin GPU (modelo falso: el agente sigue un guion fijo y la reflexión saca el último párrafo):

```bash
MODELO_FALSO=1 uv run python optimizar_prompt.py --presupuesto prueba --salida corridas/gepa/prueba_mac --sin-copiar-a-raiz
```

En Modal (detalle en `MODAL.md`, sección 7):

```bash
nohup uv run modal run --detach modal_app.py::gepa --etiqueta gepa_prueba --args="--presupuesto prueba" > corridas/gepa_prueba.log 2>&1 &
nohup uv run modal run --detach modal_app.py::gepa --etiqueta gepa1 > corridas/gepa1.log 2>&1 &
mkdir -p corridas/gepa
uv run modal volume get --force tp-corridas /corridas/gepa/gepa1 corridas/gepa
cp corridas/gepa/gepa1/prompt_optimizado.txt corridas/gepa/gepa1/config_optimizado.yaml .
```

En `gepa1` la salida de GEPA fue el prompt inicial, así que `prompt_optimizado.txt` se tomó del candidato 9 de
`log.jsonl` (ver Resultados) y `config_optimizado.yaml` es la de la corrida con otro comentario en la primera línea.

Evaluación de cada prompt sobre los 50 casos de práctica con las normas original, b y c:

```bash
nohup uv run modal run --detach modal_app.py::evaluar --etiqueta base > corridas/base.log 2>&1 &
nohup uv run modal run --detach modal_app.py::evaluar --etiqueta prompt_corto --config config_corto.yaml > corridas/prompt_corto.log 2>&1 &
nohup uv run modal run --detach modal_app.py::evaluar --etiqueta prompt_optimizado --config config_optimizado.yaml > corridas/prompt_optimizado.log 2>&1 &
uv run modal volume get --force tp-corridas /corridas/<etiqueta> corridas
uv run python tabla.py
```

Cada evaluación deja en `corridas/<etiqueta>/` el commit, la configuración y el prompt usados (`corrida.json`) y las
conversaciones completas, con cada mensaje que entró al modelo y cada uno que salió (`<version>/trazas.jsonl`).

**Para repetir `base` hoy hay que pasar `--config config_base.yaml`.** Cuando se corrió, `config.yaml` todavía era
el modelo sin entrenar con `prompt_base.txt`; desde `c23fbcc` es la entrega final (con el adaptador), y
`config_base.yaml` quedó con el contenido anterior (idéntico, sin contar comentarios, al de `22acf20`; en `d222a92`
solo cambiaba `max_lora_rank`, 64, que `entrega.py` usa únicamente si hay adaptador). `corrida.json` registra
`"adaptador_lora": null`, así que la corrida guardada es la del modelo sin entrenar. Lo mismo vale para `base_v034`
(Repetición con vLLM 0.34.0).

### Resultados

Casos resueltos sobre los 50 de práctica, con el modelo sin entrenar. Fuente: `corridas/tabla.md`.

| Prompt | Tokens | original | b | c | Corrida |
|---|---:|---:|---:|---:|---|
| Referencia de la cátedra (sin entrenar) | | 12 | 15 | 12 | `mission.md` |
| `prompt_base.txt` | 615 | 11 | 8 | 9 | `corridas/base/` |
| `prompt_corto.txt` | 467 | 6 | 5 | 3 | `corridas/prompt_corto/` |
| `prompt_optimizado.txt` | 693 | 8 | 10 | 10 | `corridas/prompt_optimizado/` |

De dónde sale cada fila. Todas usan `google/gemma-4-E4B-it` en la revisión `4ecc2ba63bcac23ba4a767fc87025b1450f84c9c`
sin adaptador (no hay punto de control propio en esta parte), vLLM 0.33.0 y los 50 casos de `practica/casos.jsonl`.
Ni la evaluación ni GEPA registran en W&B (solo `entrenar.py` lo hace), así que estas filas no tienen corrida de W&B:
la auditoría está en las trazas y en `corrida.json`.

| Fila | Comando (`modal_app.py::evaluar`, sección 5 de `MODAL.md`) | Prompt | Commit evaluado | Archivos |
|---|---|---|---|---|
| `prompt_base.txt` | `--etiqueta base` (hoy: `--config config_base.yaml`, ver arriba) | `prompt_base.txt` | `d222a92` | `corridas/base/corrida.json`, `<version>/resumen.json`, `resultados.jsonl`, `trazas.jsonl` |
| `prompt_corto.txt` | `--etiqueta prompt_corto --config config_corto.yaml` | `prompt_corto.txt` | `87ea664` | `corridas/prompt_corto/` (los mismos archivos) |
| `prompt_optimizado.txt` | `--etiqueta prompt_optimizado --config config_optimizado.yaml` | `prompt_optimizado.txt` | `87ea664` | `corridas/prompt_optimizado/` (los mismos archivos) |

La línea de base (`corridas/base/`, commit `d222a92`, 50 casos, búsquedas 1,3 por caso) queda por debajo de la
referencia de la cátedra en las tres versiones, sobre todo en b (8 contra 15). Los controles que más fallan son
`box_antes_del_registro` (60 a 62 % de aciertos), `registro` (68 a 74 %), `aviso_al_voluntariado` (72 %), `cobertura`
(72 a 76 %) y la verificación (72 a 78 %); `numero_documento` y `circuito` casi no fallan. La generación es greedy, pero
el lote en GPU puede mover algún caso entre corridas (ver Auditabilidad en `mission.md`).

Optimización con GEPA (`corridas/gepa/gepa1/resumen.json` y `log.jsonl`; comando:
`uv run modal run --detach modal_app.py::gepa --etiqueta gepa1`, commit `44c8299`, prompt inicial `prompt_base.txt`,
sin W&B):

| | Tokens | Puntaje | Controles aprobados medios (validación) | Resueltos (validación, de 45) |
|---|---:|---:|---:|---:|
| Prompt inicial (candidato 0) | 615 | 0,8348 | 0,8471 | 8 |
| Candidato 9 (`prompt_optimizado.txt`) | 693 | 0,8307 | 0,8446 | 15 |
| Otros 22 candidatos | 571 a 767 | 0,7156 a 0,7984 | 0,7286 a 0,8125 | 4 a 12 |

24 candidatos, tope de 3.000 casos jugados alcanzado en 3.347 s (56 minutos de optimización, más la carga del
modelo), reflexión con la misma Gemma, semilla 0, penalización 0,02. La corrida se lanzó desde el commit `44c8299`;
`resumen.json` lo marca "con cambios sin commitear" solo por los logs locales de lanzamiento, que ahora están en
`.gitignore`.

**GEPA no encontró un candidato con mejor puntaje que el inicial**, así que su salida
(`corridas/gepa/gepa1/prompt_optimizado.txt`) es `prompt_base.txt` tal cual. La métrica de GEPA es el promedio de
controles aprobados, y la del TP son los casos resueltos (los 9 controles a la vez). En validación el candidato 9
resolvió casi el doble de casos que el inicial (15 contra 8) con un promedio de controles casi igual. Por eso
`prompt_optimizado.txt` es el candidato 9 (`texto` de la línea `"candidato": 9` de `log.jsonl`), no la salida
directa de GEPA. Elegirlo mirando la validación entre 24 candidatos puede premiar el azar; la evaluación sobre los
50 casos de práctica, que no se usaron en la optimización, es la que dice si la mejora es real.

Qué cambia el candidato 9 respecto del base: ordena el trabajo en un protocolo de cinco pasos (leer triage,
preguntar cobertura, verificar afiliación, buscar normativa, registrar), pide buscar en las normas antes de registrar,
con ejemplos de consultas, y prohíbe usar valores numéricos fijos de las normas. Conserva las cinco herramientas, los
argumentos y el formato JSON. Es 13 % más largo (693 tokens).

#### Lectura de los resultados

- **El prompt corto empeora en las tres versiones** (6, 5 y 3 contra 11, 8 y 9). Casi toda la caída está en
  `box_antes_del_registro`, que baja de 60 a 62 % de aciertos a 36 a 42 %, y en `plazo_circuito_min` (de 90 a 92 %
  a 78 a 80 %). Al sacar la redacción larga de los argumentos se perdió contexto que la Gemma sin entrenar usaba para
  esos campos, aunque las reglas sigan escritas. Ahorra 148 tokens de prompt y entre 3.600 y 4.300 caracteres de
  contexto por caso (3.623, 4.309 y 3.907 en original, b y c; `caracteres_de_contexto_por_caso` de cada
  `resumen.json`), que no compensan.
- **El prompt optimizado mejora en las normas b y c** (10 y 10 contra 8 y 9) y queda por debajo en las originales (8
  contra 11): 28 casos resueltos en total, igual que la base. Busca más en las normas (1,9 búsquedas por caso contra
  1,3), lo que sube `registro` (72 a 84 % contra 68 a 74 %), `circuito` (100 %) y `plazo_circuito_min`; con las
  normas cambiadas eso es lo que más importa. A cambio, el contexto por caso crece de unos 19.000 a unos 25.500
  caracteres.
- **Ninguno llega a la referencia de la cátedra sin entrenar** (12, 15 y 12). Los controles que siguen fallando en
  los tres prompts son `box_antes_del_registro`, `cobertura`, `aviso_al_voluntariado` y la verificación. Son reglas
  que dependen de combinar varios datos del caso, y el ajuste fino de la Parte 4 apunta a ellas.
- La mejora de 8 a 15 en validación no se sostuvo con la misma fuerza en la práctica: con 45 casos y 24 candidatos,
  parte de esa diferencia era azar.

### Repetición con vLLM 0.34.0

Las corridas `base` y `prompt_optimizado` se repitieron con la pila final (vLLM 0.34.0, transformers 5.22.2), con
las mismas configuraciones (`config.yaml` y `config_optimizado.yaml`), desde el commit `22acf20`. Etiquetas
`base_v034` y `prompt_optimizado_v034`; fuente: `corridas/tabla.md`.

| Prompt | vLLM | original | b | c | Total |
|---|---|---:|---:|---:|---:|
| `prompt_base.txt` | 0.33.0 (`corridas/base/`) | 11 | 8 | 9 | 28 |
| `prompt_base.txt` | 0.34.0 (`corridas/base_v034/`) | 12 | 5 | 8 | 25 |
| `prompt_optimizado.txt` | 0.33.0 (`corridas/prompt_optimizado/`) | 8 | 10 | 10 | 28 |
| `prompt_optimizado.txt` | 0.34.0 (`corridas/prompt_optimizado_v034/`) | 9 | 10 | 10 | 29 |

Caso por caso (`resultados.jsonl` de cada versión):

- **Base:** cambia la ficha registrada en 8, 8 y 9 de los 50 casos (original, b y c). En original gana un caso y no
  pierde ninguno; en b pierde 3 y no gana ninguno; en c gana 1 y pierde 2. Sumando los 50 casos de b, aprueba 2
  controles menos de `box_antes_del_registro`, 2 menos de verificación y 1 menos de `cobertura` y de
  `entidad_a_notificar`.
- **Prompt optimizado:** cambia la ficha en 6, 4 y 1 casos. Gana un caso en original y no cambia los resueltos en b
  ni en c.
- El contexto por caso, las búsquedas por caso y los segundos por caso quedan prácticamente iguales (por ejemplo, la
  base: 1,30 búsquedas y unos 18.800 caracteres por caso en las tres versiones).

Lectura: con generación greedy, el cambio de versión mueve algunas fichas, como ya pasaba con el lote en GPU entre
corridas. El prompt optimizado resultó más estable (casi las mismas fichas y un caso más) que el base, que pierde 3
casos en b. Con vLLM 0.34.0 el prompt optimizado queda por encima de la base en total (29 contra 25) y en b y c (10 y
10 contra 5 y 8), y sigue por debajo en original (9 contra 12). Con 50 casos por versión, diferencias de 1 a 3 casos
están dentro de lo que mueve el cambio de versión, así que estas comparaciones son indicios, no mediciones finas.

Comandos: `modal_app.py::evaluar --etiqueta base_v034 --config config_base.yaml` y
`--etiqueta prompt_optimizado_v034 --config config_optimizado.yaml` (en `22acf20` `config.yaml` todavía era la base,
ver Comandos). Sin adaptador, misma revisión del modelo, sin W&B; archivos en `corridas/base_v034/` y
`corridas/prompt_optimizado_v034/`.

### Lo que no funcionó en la Parte 3

Todo sale de `corridas/` y de `git log`:

1. **La prueba chica de GEPA en Modal no arrancó.** `casos_optimizacion.py` lee `historial/`, que la imagen de Modal
   no subía: `FileNotFoundError`. Se arregló en `44c8299` (subir `historial/`, 18 MB) y desde ese commit se lanzó
   `gepa1`. La salida de esa prueba no se bajó al repositorio (no hay `corridas/gepa/gepa_prueba/`).
2. **GEPA no mejoró su propia métrica.** Los 23 candidatos que propuso quedaron por debajo del inicial en puntaje
   (0,7156 a 0,8307 contra 0,8348), así que su salida fue `prompt_base.txt` sin cambios. La reflexión la hizo la
   misma Gemma sin entrenar; no se probó con un modelo de reflexión más grande. En casos resueltos de
   validación, en cambio, 7 de los 23 superaron al inicial (15, 12, 11, 11, 11, 10 y 10 contra 8), y de ahí sale el
   candidato 9.
3. **La mejora del candidato 9 en validación no se sostuvo en la práctica.** De 8 a 15 casos en validación pasó a
   28 casos contra 28 de la base en la práctica (vLLM 0.33.0), con una caída en las normas originales (8 contra 11).
4. **El prompt corto empeoró** en las tres versiones (6, 5 y 3 contra 11, 8 y 9): ver Lectura de los resultados.
5. **La base perdió 3 casos en b al pasar a vLLM 0.34.0** (de 8 a 5) sin cambiar ni el prompt ni el modelo: ver
   Repetición con vLLM 0.34.0.

## Parte 4: Entrenamiento

Todos los números salen de las corridas versionadas en `corridas/`, nunca a
mano. Los comandos de Modal están en
[`MODAL.md`](MODAL.md), secciones 8 a 14.

### Estrategia

Fine-tuning supervisado (SFT) con LoRA sobre `google/gemma-4-E4B-it`, en bf16,
en una A100 de 40 GB. El entrenamiento le enseña al modelo el oficio: el
protocolo JSON de las herramientas, el orden de los pasos, qué buscar, a quién
preguntar, qué verificar y las costumbres del hospital. Los números de las
normas no se aprenden: llegan en cada caso por `buscar_normativa`, así que el
conjunto de datos los hace variar (ver abajo).

- **Pérdida solo sobre el asistente.** Las respuestas del modelo (una llamada
  JSON por turno, más la marca de fin de turno `<turn|>`) son lo único que
  suma a la pérdida. El sistema, los resultados de las herramientas y el
  primer mensaje quedan en -100. La plantilla de Gemma 4 no trae las marcas
  `{% generation %}` que usa TRL para esto, así que `entrenar.py` arma las
  etiquetas con los offsets del tokenizador. En la prueba se controló que los
  tramos marcados, decodificados, son exactamente los turnos del asistente
  más su `<turn|>`: con la plantilla de chat real de `google/gemma-4-E4B-it`
  (solo su `chat_template.jinja`, sin bajar el modelo), la máscara fue exacta
  en las 150 conversaciones de val. En las 16 conversaciones de la prueba
  (variante `datos/sin_prompt/`), 4.766 de 47.179 tokens entran en la
  pérdida (10,1%, con el tokenizador del modelo diminuto). La prueba deja sus
  archivos en `corridas/prueba-*/`, que no se versiona; el número se
  reproduce con `uv run python entrenar.py --prueba --corrida prueba-mac
  --datos datos/sin_prompt/train.jsonl --val datos/sin_prompt/val.jsonl`
  (`tokens` y `tokens_en_perdida` de train en la salida). Sin `--datos`
  (variante `datos/`) da 4.766 de 48.427.
- **Compatible con vLLM.** `entrega.py` carga el adaptador con el soporte LoRA
  de vLLM 0.34.0. Según su código (`vllm/model_executor/models/gemma4.py`,
  `gemma4_mm.py` y `vllm/config/lora.py`), para Gemma 4 acepta LoRA en
  `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj` y
  `down_proj` del modelo de lenguaje, y ranks 1, 8, 16, 32, 64, 128, 256, 320
  o 512 (`max_lora_rank`). Las torres de visión y audio solo admiten LoRA con
  `enable_tower_connector_lora`, experimental, así que el adaptador no las
  toca: `entrenar.py` usa una expresión regular que deja afuera `vision` y
  `audio`, y antes de subir cada punto de control verifica rank, módulos,
  ausencia de `modules_to_save` y de DoRA. Los nombres de los tensores quedan
  como `base_model.model.model.language_model.layers.N...`, que vLLM mapea a
  `language_model.model.layers.N...`. `entrega.py` usa `enable_lora=True` y
  `max_lora_rank=32` (`config.yaml`), el rank del adaptador.
- **Dos variantes de datos**, para la tabla: "prompt + entrenamiento" con
  `prompt_optimizado.txt`, en `datos/` (la que lee `entrenar.yaml` por
  defecto), y "solo entrenamiento" con el mensaje de sistema de
  `admision/ejemplo.py`, en `datos/sin_prompt/`. Solo cambia el mensaje de
  sistema; las conversaciones son las mismas. Se eligió
  `prompt_optimizado.txt` para la variante principal porque en la Parte 3,
  con vLLM 0.33.0, empata en total con el prompt base (28 casos) pero gana en
  las normas b y c (10 y 10 contra 8 y 9), que se parecen más al test, donde
  cambian los números. Repetido con vLLM 0.34.0 la ventaja se mantiene (29
  contra 25 en total; 10 y 10 contra 5 y 8 en b y c).

### Conjunto de datos

`armar_dataset.py` (semilla 20261117) junta tres orígenes en el formato del
manual del kit ([`KIT.md`](KIT.md)) y separa 5% de cada origen para
validación. Las dos variantes tienen las mismas conversaciones
(`datos/resumen.json` y `datos/sin_prompt/resumen.json`):

| Origen | Conversaciones | Train | Val |
|---|---:|---:|---:|
| Historial, filas `correcta` de `historial_clasificado.csv` (normas originales) | 1.600 | 1.520 | 80 |
| Trazas de la cátedra, `entrenamiento/trazas.jsonl` (valores variables) | 800 | 760 | 40 |
| Sintéticas, `curado/conversaciones_sinteticas.jsonl` (200 por versión: original, b y c) | 600 | 570 | 30 |
| **Total** | **3.000** | **2.850** | **150** |

Tokens estimados como caracteres / 4, igual que `admision.evaluar_rag`:

| | `datos/` (`prompt_optimizado.txt`) | `datos/sin_prompt/` (`admision/ejemplo.py`) |
|---|---:|---:|
| Tokens totales | 8.140.628 | 7.992.888 |
| Train / val | 7.740.202 / 400.426 | 7.599.855 / 393.033 |
| Por conversación: media / mediana | 2.713,5 / 2.748 | 2.664,3 / 2.699 |
| Por conversación: percentil 95 / máximo (`E-177`) | 3.481 / 3.779 | 3.432 / 3.729 |
| Mensaje de sistema por conversación | 607 | 558 |
| `train.jsonl` / `val.jsonl` | 32,2 MB / 1,7 MB | 31,7 MB / 1,6 MB |
| sha256 de `train.jsonl` | `63139319143e...` | `16830998562d...` |

- Los tokens reales del tokenizador de Gemma quedan en
  `corridas/<corrida>/datos.json` y en W&B. El tokenizador del modelo
  diminuto de la prueba de la Mac no es idéntico al de Gemma 4 E4B (otro
  sha256 de `tokenizer.json`), así que la relación real sale de la prueba en
  GPU (`corridas/prueba-gpu-02/datos.json`, variante `datos/`): con el
  tokenizador de Gemma 4 E4B, train son 8.640.302 tokens (estimados:
  7.740.202, un 11,6% menos) y val 447.945 (estimados: 400.426). De los de
  train, 838.716 (9,7%) entran en la pérdida. La conversación más larga tiene
  4.176 tokens reales, por debajo del máximo de 6.144: no se descarta
  ninguna.
- Los dos `train.jsonl` pesan menos de 50 MB y van en git. Si una variante
  pasa ese límite, se publica con `armar_dataset.py --subir-hf` en un repo de
  dataset de HF (ver [`MODAL.md`](MODAL.md), sección 8).
- sha256 completos:
  `63139319143e32c98dd1ba4015a1ac78bacb9499eda1bf9efb38e95803650f65`
  (`datos/train.jsonl`) y
  `16830998562d978367220e329a3595673287a0889dcf886c14ad89cd88bcd072`
  (`datos/sin_prompt/train.jsonl`). Rearmar la variante sin prompt en su
  carpeta nueva dio el mismo hash que antes de moverla. La versión
  anterior, armada con la clasificación de la primera pasada (corte del
  voluntariado en 76 años, 1.590 filas correctas), tenía 2.990 conversaciones
  y el hash `a1e640db...` y no se usó para entrenar.

#### Las búsquedas muestran los números de cada traza

Cada traza de la cátedra usa sus propios valores de las normas (por ejemplo,
P-ADM-2 toma 8 valores entre 55 y 80 años en las 800 trazas). Si las
búsquedas se rehicieran con `normas/original`, el modelo vería un número en la
búsqueda y una ficha decidida con otro, y aprendería a ignorar la búsqueda.
Copiar el resultado original de la traza tampoco alcanza: viene del BM25 de la
cátedra, no del buscador que va a usar el agente.

La solución aprovecha que los textos de las normas son idénticos en las tres
versiones (`diff` de `normas/original`, `b` y `c` solo difiere en
`parametros.yaml`) y que cada resultado de búsqueda termina con su línea
`Valores: ...`. Para cada traza, `armar_dataset.py`:

1. lee los valores que muestran sus propios resultados de búsqueda;
2. arma una carpeta temporal con los textos de `normas/original` y un
   `parametros.yaml` con esos valores. Los parámetros que no cambian entre
   versiones (P-COB-1 y los de otras áreas) se toman de `normas/original`;
3. rehace cada búsqueda con `parte2/rag_buscador.py` sobre esa carpeta, con la
   misma consulta de la traza.

Si el buscador citara un parámetro que varía entre versiones y que la traza
nunca mostró, esa búsqueda conserva el resultado original. Resultados en este
conjunto: 7.316 búsquedas rehechas, **0** con resultado original y 5.478 que
devolvieron las mismas secciones que la traza; en esas 5.478 el texto nuevo
coincide carácter por carácter con el original, lo que confirma que los
valores reconstruidos son los de cada traza. Con `--busquedas originales` se
puede armar la variante que copia los resultados de la traza, para comparar.

#### Sintéticas

`generar_sinteticas.py` genera 600 casos con `admision.generador` (semilla
20261108) y los juega con una política determinista, en el simulador oficial,
con el buscador del grupo armado con la versión de normas de cada caso (200
por versión). Las consultas siguen las 14 plantillas y el orden de pasos de
las trazas de la cátedra, que son las que va a escribir el agente.

Antes de usarla, la política se validó contra las fichas esperadas de la
práctica con el comparador oficial (`uv run python validar_politica.py`):

| Pasada | original | b | c |
|---|---:|---:|---:|
| Costumbre del voluntariado con corte en 76 años (`costumbres.md`) | 49/50 | 49/50 | 49/50 |
| Corte en 75 años | **50/50** | **50/50** | **50/50** |

El único fallo de la primera pasada fue `pev-006` (75 años, sin acompañante):
el historial muestra el corte en 75 (ver [`revision_parte1.md`](revision_parte1.md)).
Esa corrección se aplicó también a la clasificación del historial, lo que suma
10 conversaciones reales.

**Cuidado al leer la tabla final:** como las sintéticas usan las normas b y c
para que el modelo no memorice los números de `original`, la evaluación de
práctica con b y c deja de ser del todo independiente de los datos de
entrenamiento (no hay casos de práctica en el entrenamiento, pero sí los
valores de esas versiones). El test de la cátedra usa otros números; las
trazas de la cátedra, con valores que varían traza a traza, son lo que más
se le parece.

### Configuración

`entrenar.yaml`, comentado valor por valor. Lo principal:

| Parámetro | Valor | Por qué |
|---|---|---|
| Modelo | `google/gemma-4-E4B-it`, bf16, SDPA (eager en la torre de audio) | el del enunciado; ~16 GB en bf16 |
| LoRA | r = 32, alpha = 32, dropout 0,05 | rank aceptado por vLLM; ~1% de parámetros |
| Módulos | q/k/v/o_proj, gate/up/down_proj del modelo de lenguaje | lo que carga vLLM |
| Épocas | 1,75 | ~312 pasos; ~2,5 horas según la prueba chica (ver abajo) |
| lr | 1e-4, coseno, 3% de calentamiento | habitual en LoRA |
| Batch | 2 por paso x 8 de acumulación = 16 conversaciones | logits de 262.144 tokens de vocabulario |
| Largo máximo | 6.144 tokens (se descartan, no se truncan) | la más larga ronda 3.700 estimados |
| Gradient checkpointing | sí | memoria de activaciones |
| Semilla | 20261117 | datos, LoRA y dropout |
| Puntos de control | cada 100 pasos, a `HF_REPO` | con estado para retomar |

Las épocas salen de la prueba chica en la A100 (`corridas/prueba-gpu-02/`,
20 pasos con `datos/`, W&B `2r5rmemo`):

| Medida | Valor |
|---|---|
| Segundos por paso | PENDIENTE: se usó 27,5 (pasos 5 a 20) y 29,1 de promedio con el arranque, leídos en W&B `2r5rmemo`, pero ningún archivo del repo los respalda. `resumen.json` solo tiene 643,6 s para los 20 pasos, con la evaluación incluida |
| Pasos por época | 178 (2.850 conversaciones / 16) |
| VRAM máxima | 20,75 GB de 40, sin errores de memoria |
| Pérdida de train | media de la corrida: 0,2924. Pasos 10 y 20: PENDIENTE (W&B `2r5rmemo`, sin archivo en el repo) |
| Pérdida de val (paso 20) | 0,1273 (precisión por token 0,968) |
| Evaluación sobre val | 49 s |
| Puntos de control en HF | `Juanlu1/gemma-admision`: `prueba-gpu-02-paso-20` (`6d13f855fe77e8b22577adf67d4aae1a769e305d`) y `prueba-gpu-02-final` (`427aae909639f0b4c261ce71c1cc6daff61eb8f3`); compatibles con vLLM (rank 32, 7 módulos) |

Salvo lo marcado PENDIENTE, todo sale de `corridas/prueba-gpu-02/resumen.json`
y `datos.json`. Comando: `uv run modal run --detach modal_entrenar.py
--corrida prueba-gpu-02 --max-pasos 20` (datos `datos/train.jsonl`, prompt
`prompt_optimizado.txt`, semilla 20261117; la configuración exacta, todavía
con 3 épocas que `--max-pasos` corta, está en
`corridas/prueba-gpu-02/config_usada.yaml`. El commit de código no quedó
registrado en los archivos de la corrida).

Las épocas se eligieron con los segundos por paso medidos en esa prueba
(PENDIENTE de respaldar, ver arriba). Con esa medida, 3 épocas (534 pasos)
tardaban demasiado y 2 épocas (356 pasos) quedaban demasiado cerca del tope
de 3 horas para una medida de 20 pasos; se eligieron 1,75 épocas (unos 312
pasos). Las horas que se estimaron para cada opción dependen del número
PENDIENTE y se sacaron de acá. El tiempo real de las corridas completas sí
está respaldado: `segundos` de `corridas/<corrida>/resumen.json` (tabla de
abajo).

Dependencias: una sola pila para entrenar y para evaluar, con versión exacta
en `pyproject.toml` y `uv.lock`: vllm 0.34.0 (solo en Linux), torch 2.14.0,
transformers 5.22.2, trl 1.17.1, peft 0.21.2, accelerate 1.15.0, datasets
5.1.0, huggingface_hub 2.4.0, wandb 0.31.0, pyyaml 6.0.3 y modal 1.6.4. torch
y transformers son las que acepta vllm 0.34.0 (`torch==2.14.0`,
`transformers<5.23.0`, `huggingface_hub>=2.0.0`). La Parte 3 se midió con
vllm 0.33.0 y transformers 5.20.2; se pasó a 0.34.0 porque vllm 0.33.0 no
acepta transformers 5.22.2 (pide `<5.21.0`) y porque las reglas de LoRA de
Gemma 4 que controla `entrenar.py` se tomaron del código de la 0.34.0. Las
imágenes de Modal de la evaluación (`modal_app.py`) y del entrenamiento
(`modal_entrenar.py`) se arman desde el mismo `uv.lock`.

### Auditabilidad de cada corrida

- **W&B:** configuración completa, semilla, comando, ruta y sha256 de
  `train.jsonl` y `val.jsonl` (también como artefacto de tipo dataset),
  tokens reales, conversaciones descartadas, parámetros entrenables, VRAM
  máxima y la revisión de HF de cada punto de control.
- **Hugging Face (`HF_REPO`):** un commit por punto de control con el
  adaptador en la raíz (lo carga vLLM tal cual), `estado/` para retomar y
  `corrida.json` con corrida, paso, semilla, sha256 de los datos, configuración
  y link de W&B. Etiquetas `<corrida>-paso-<N>`, `<corrida>-final` y `final`
  (esta última solo en corridas completas).
- **Repositorio:** `corridas/<corrida>/resumen.json`, `revisiones.json`,
  `datos.json` y `config_usada.yaml`, bajados del volumen de Modal.

### Comandos

```bash
uv run python validar_politica.py                     # política sintética contra la práctica
uv run python generar_sinteticas.py                   # 600 conversaciones sintéticas
uv run python armar_dataset.py --prompt prompt_optimizado.txt   # datos/ (prompt + entrenamiento)
uv run python armar_dataset.py --salida datos/sin_prompt         # datos/sin_prompt/ (solo entrenamiento)
uv run python entrenar.py --prueba                    # Mac, modelo diminuto
uv run modal run --detach modal_entrenar.py --corrida prueba-gpu-01 --max-pasos 20
uv run modal run --detach modal_entrenar.py --corrida sft-prompt-v1    # cortada en el paso 106 (pasada 6)
caffeinate -is uv run modal run --detach modal_entrenar.py --corrida sft-prompt-v1-r1 \
    --retomar hf:sft-prompt-v1-paso-100
caffeinate -is uv run modal run --detach modal_entrenar.py --corrida sft-ejemplo-v2 \
    --datos datos/sin_prompt/train.jsonl --val datos/sin_prompt/val.jsonl
```

Las evaluaciones de los adaptadores son las de la sección 5 de
[`MODAL.md`](MODAL.md) con `--config config.yaml` (etiqueta `sft_prompt`) y
`--config config_sft_base.yaml` (etiqueta `sft`). Antes de cada una se corrió
la prueba de 3 casos (`--cantidad 3`) para confirmar que vLLM carga el
adaptador.

### Resultados

Casos resueltos de los 50 de práctica, con las normas completas. La evaluación
corre `admision.correr practica` con `entrega.py` (sección 4 del
[`README.md`](README.md)); cada celda debe citar el punto de control y el
prompt que la producen. Las dos filas sin entrenar son las corridas
`corridas/base_v034/` y `corridas/prompt_optimizado_v034/` (en
`corridas/tabla.md`), con vLLM 0.34.0, la misma pila con la que se evalúan los
adaptadores; las de vLLM 0.33.0 están en la Parte 3. `prompt_base.txt` es el
mensaje de sistema de `admision/ejemplo.py` tal cual.

| Variante | Punto de control | Prompt | original | b | c |
|---|---|---|---:|---:|---:|
| Referencia de la cátedra, sin entrenar | - | `admision/ejemplo.py` | 12 | 15 | 12 |
| Referencia de la cátedra, SFT con las 800 trazas | - | `admision/ejemplo.py` | 25 | 24 | 25 |
| Sin entrenar | modelo base | `admision/ejemplo.py` (`prompt_base.txt`) | 12 | 5 | 8 |
| Solo prompt | modelo base | `prompt_optimizado.txt` | 9 | 10 | 10 |
| Solo entrenamiento | `sft-ejemplo-v2-paso-300` (`67deca8`) | `admision/ejemplo.py` | 21 | 22 | 22 |
| Prompt + entrenamiento | `sft-prompt-v1-r1-final` (`a5af001`) | `prompt_optimizado.txt` | 26 | 25 | 28 |

De dónde sale cada fila. Modelo base `google/gemma-4-E4B-it`, revisión
`4ecc2ba63bcac23ba4a767fc87025b1450f84c9c`, vLLM 0.34.0, 50 casos de
`practica/casos.jsonl`. Los comandos son `uv run modal run --detach
modal_app.py::evaluar` con lo que dice la columna (sección 5 y 14 de
[`MODAL.md`](MODAL.md)); los números, de `corridas/<etiqueta>/<version>/resumen.json`
(y `corridas/tabla.md`, `uv run python tabla.py`). El punto de control y su
revisión salen de `corridas/<etiqueta>/corrida.json` (`adaptador_lora` y
`adaptador_revision`). La evaluación no registra en W&B; la columna W&B es la
del entrenamiento que produjo el punto de control.

| Fila | Argumentos de `evaluar` | Punto de control (repo de HF @ revisión) | Prompt | Commit evaluado | W&B del entrenamiento |
|---|---|---|---|---|---|
| Sin entrenar | `--etiqueta base_v034 --config config_base.yaml` | ninguno | `prompt_base.txt` | `22acf20` | no aplica |
| Solo prompt | `--etiqueta prompt_optimizado_v034 --config config_optimizado.yaml` | ninguno | `prompt_optimizado.txt` | `22acf20` | no aplica |
| Solo entrenamiento | `--etiqueta sft --config config_sft_base.yaml` | `Juanlu1/gemma-admision` @ `67deca83dd206515f99683fa46bb1b3db3eb8f1d` (`sft-ejemplo-v2-paso-300`) | `prompt_base.txt` | `a726121` | `g69gw15q` (`sft-ejemplo-v2`) |
| Prompt + entrenamiento | `--etiqueta sft_prompt --config config.yaml` | `Juanlu1/gemma-admision` @ `a5af001800f7da670f72d2a9461ec3a2d805f4f6` (`sft-prompt-v1-r1-final`) | `prompt_optimizado.txt` | `979e4d2` | `68qllkha` (`sft-prompt-v1` y `sft-prompt-v1-r1`) |

Los links completos de W&B están en `corridas/sft-ejemplo-v2/resumen.json` y
`corridas/sft-prompt-v1-r1/resumen.json` (proyecto
`juanlu1-austral/tp-admision-guardia`). Las dos filas de referencia son de
`mission.md` ("Cómo se corrige"). Las dos filas sin entrenar se corrieron en
`22acf20` con `--config config.yaml` y `--config config_optimizado.yaml`;
`config_base.yaml` es la `config.yaml` de ese commit (Parte 3, Comandos).

"Prompt + entrenamiento" es `corridas/sft_prompt/`, con `config.yaml` (la
entrega final). Supera a la referencia SFT de la cátedra en las tres
versiones (26, 25 y 28 contra 25, 24 y 25) y casi triplica la fila sin
entrenar con el mismo prompt (9, 10 y 10). La puntuación parcial media sube de
0,80 a 0,94 y el agente busca más: 2,9 búsquedas por caso contra 1,9.

"Solo entrenamiento" es `corridas/sft/`, con `config_sft_base.yaml`: 21, 22 y
22, casi el doble que sin entrenar (12, 5 y 8) pero por debajo de la
referencia SFT de la cátedra y de prompt + entrenamiento. El entrenamiento es
lo que más suma (de 12, 5 y 8 a 21, 22 y 22); el prompt optimizado agrega
entre 3 y 6 casos por versión sobre el adaptador (sin entrenar restaba 3 en
original y sumaba 5 y 2 en b y c). Las dos corridas de entrenamiento tienen
las mismas conversaciones, la misma semilla y los mismos pasos: solo cambia el
mensaje de sistema. Con 50 casos por versión, diferencias de 1 a 3 casos son
indicios, no mediciones finas (Parte 3).

#### Las corridas de entrenamiento

| Medida | `sft-prompt-v1` + `sft-prompt-v1-r1` | `sft-ejemplo-v2` |
|---|---|---|
| Datos | `datos/` (sha256 `63139319...`) | `datos/sin_prompt/` (sha256 `16830998...`) |
| Pasos | 314 (1,76 épocas): 1 a 100 en `sft-prompt-v1`, 101 a 314 en `sft-prompt-v1-r1` | 314 (1,76 épocas), sin cortes |
| Tiempo | 5.406 s (1,50 h) de la continuación (pasos 101 a 314). Pasos 1 a 100: PENDIENTE (se informaron 42 min, sin archivo que los respalde), así que el total también queda PENDIENTE | 7.778 s (2,16 h) |
| Pérdida de train | 0,00745 de media en los pasos 101 a 314. Último registro (paso 310): PENDIENTE | 0,0380 de media en los 314 pasos (incluye el arranque). Último registro (paso 310): PENDIENTE |
| Pérdida de val | 0,00402 (paso 314). Pasos 100, 200 y 300: PENDIENTE | 0,00530 (paso 314). Pasos 100, 200 y 300: PENDIENTE |
| Precisión por token en val | 0,9986 (paso 314) | 0,9981 (paso 314); paso 300: PENDIENTE |
| VRAM máxima | 20,81 GB | 20,72 GB |
| Comando | `modal_entrenar.py --corrida sft-prompt-v1`, retomada con `--corrida sft-prompt-v1-r1 --retomar hf:sft-prompt-v1-paso-100` (Comandos) | `modal_entrenar.py --corrida sft-ejemplo-v2 --datos datos/sin_prompt/train.jsonl --val datos/sin_prompt/val.jsonl` |
| Puntos de control (`Juanlu1/gemma-admision`) | `sft-prompt-v1-paso-100` (revisión PENDIENTE: la corrida cortada no dejó archivos), `-r1-paso-200` `69815ca`, `-r1-paso-300` `2735306`, `-r1-paso-314` `c559132`, `-r1-final` `a5af001` | `sft-ejemplo-v2-paso-100` `d003d71`, `-paso-200` `e841460`, `-paso-300` `67deca8`, `-paso-314` `53d6d35`, `-final` `858d416` |
| W&B | `68qllkha` (la continuación sigue el mismo run) | `g69gw15q` |

Los números con valor salen de `corridas/<corrida>/resumen.json` (`segundos`,
`train_loss`, `eval`, `vram_max_gb`, `wandb`) y las revisiones completas, de
`revisiones.json`. Los marcados PENDIENTE se leyeron en W&B o en el log de
Modal de la corrida, pero no quedaron en ningún archivo del repositorio:
falta exportar el historial de W&B (por ejemplo, `run.history()` de cada run)
a `corridas/<corrida>/`.

**Punto de control elegido.** El criterio es usar, en cada corrida, el de
menor pérdida de validación. En `sft-prompt-v1-r1` se eligió el final (paso
314, 0,00402). En `sft-ejemplo-v2` se eligió el del paso 300, y
`config_sft_base.yaml` fija su commit `67deca83dd20...`
(`sft-ejemplo-v2-paso-300`). Las pérdidas de validación de los pasos 100, 200
y 300 que respaldan esas elecciones están PENDIENTES de exportar (ver arriba);
con lo que hay en el repositorio solo se puede comprobar la del paso 314.
`config.yaml` fija el commit `a5af001800f7...` de la etiqueta
`sft-prompt-v1-r1-final` y no la etiqueta móvil `final`, que pisa cada
corrida completa. La configuración sin entrenar queda en `config_base.yaml`.

#### Corridas que no tienen carpeta en `corridas/`

Las cuatro filas que pide la consigna (sin entrenar, solo prompt, solo
entrenamiento y las dos cosas) tienen su corrida. Estas otras no dejaron
archivos en el repositorio, y por qué:

| Corrida | Qué pasó | Por qué no hay archivos |
|---|---|---|
| `prueba-gpu-01` | falló al armar el modelo (atención SDPA en la torre de audio, pasada 5) | no llegó a entrenar; `entrenar.py` escribe `resumen.json` y `revisiones.json` recién al terminar (líneas 460 y 461). Lo que haya escrito antes en el volumen de Modal (por ejemplo `datos.json`, línea 366) no se bajó al repositorio. Si dejó run en W&B, su id: PENDIENTE |
| `sft-prompt-v1` (pasos 1 a 100) | Modal la canceló en el paso 106 al suspenderse la Mac (pasada 6) | no terminó, así que no escribió `resumen.json`. Quedó el punto de control `sft-prompt-v1-paso-100` en HF y el run `68qllkha` de W&B, que la continuación `sft-prompt-v1-r1` siguió usando |
| `sft-ejemplo-v1` | cancelada en el paso 73 por la misma suspensión | no terminó ni llegó a subir un punto de control; se relanzó de cero como `sft-ejemplo-v2`. Su run de W&B: PENDIENTE (el id no quedó en ningún archivo del repo) |
| `gepa_prueba` | la prueba chica de GEPA falló con `FileNotFoundError` (Parte 3, Lo que no funcionó) | su salida no se bajó del volumen de Modal |

Tampoco se evaluaron sobre la práctica los puntos de control intermedios
(pasos 100 a 314 que no se eligieron) ni se repitió ninguna evaluación de
los adaptadores para medir la variación del lote en GPU. El motivo no quedó
registrado: PENDIENTE que lo complete el equipo.

### Pasadas del desarrollo

1. **Buscador propio de las sintéticas.** La primera versión de
   `generar_sinteticas.py` tenía un buscador de palabras clave fijas y
   consultas inventadas: las conversaciones no mostraban lo que el agente iba
   a ver. Se reemplazó por el buscador del grupo y las consultas de las trazas.
2. **Corte del voluntariado.** La validación contra la práctica dio 49/50 por
   un corte de edad mal tomado del historial (76 en vez de 75). Corregido, 50/50.
3. **API de transformers 5.** La primera prueba de `entrenar.py` falló porque
   `warmup_ratio` y `group_by_length` ya no existen en `TrainingArguments`;
   ahora son `warmup_steps` con una fracción y
   `train_sampling_strategy="group_by_length"`.
4. **Etiqueta final.** Al planear la prueba chica en GPU se vio que movería la
   etiqueta `final` de HF; ahora solo la mueven las corridas completas.
5. **Atención de la torre de audio.** La primera prueba chica en la A100
   (`prueba-gpu-01`) no llegó a entrenar: con `attn_implementation: sdpa`,
   transformers 5.22.2 no puede armar `Gemma4AudioModel`, que no admite SDPA.
   La prueba de la Mac no lo había visto porque fuerza `eager` y el modelo
   diminuto no tiene torre de audio. Ahora `entrenar.yaml` pide SDPA para el
   modelo de lenguaje y la visión y eager para el audio; se comprobó armando
   Gemma 4 E4B con su configuración real en el dispositivo `meta`.
6. **Corte por suspensión de la Mac.** `modal run --detach` no alcanzó: al
   cerrarse la tapa de la Mac, Modal canceló las dos corridas
   (`Function call was cancelled`). `sft-prompt-v1` iba por el paso 106 y ya
   había subido `sft-prompt-v1-paso-100`: se retomó desde ahí como
   `sft-prompt-v1-r1`, que siguió en el paso 101 con el mismo run de W&B.
   `sft-ejemplo-v1` iba por el paso 73, sin ningún punto de control, así que
   se relanzó de cero como `sft-ejemplo-v2`. Desde entonces cada lanzamiento
   corre bajo `caffeinate -is`, que impide que la Mac se suspenda.

## Parte 5: Recursos y producción

PENDIENTE: lo escribe otra integrante del grupo.

Lo que pide `mission.md` (Parte 5 y "El informe"): tiempo de entrenamiento,
VRAM usada, costo y tiempo por caso en la A100 de 40 GB, casos que se
procesan a la vez al entrenar y al evaluar, cuántos casos simultáneos tolera
en producción, la proyección de consumo, cómo escalaría y los trabajos
futuros. Como en el resto del informe, cada número tiene que citar el
comando, el punto de control y el prompt que lo producen.

De dónde sacar los datos (todo está en el repositorio salvo W&B):

| Dato | Archivo |
|---|---|
| Tiempo de juego por versión y por caso (`jugar_lote`, `jugar_lote_por_caso`) | `corridas/*/*/tiempos.json` (21 archivos: 7 etiquetas x original, b y c) |
| Casos resueltos, búsquedas por caso, caracteres de contexto por caso, llamadas por caso | `corridas/*/*/resumen.json` (y el detalle caso por caso en `resultados.jsonl`) |
| Carga del modelo (`construir_agente_segundos`), commit, config, prompt, adaptador y revisión de cada evaluación | `corridas/<etiqueta>/corrida.json` |
| Tabla con todo lo anterior junto | `corridas/tabla.md` (`uv run python tabla.py`) |
| Concurrencia de vLLM (tamaño de la caché KV en tokens y "Maximum concurrency" para 16.384 tokens por pedido) | `corridas/<etiqueta>/modal.log` y `corridas/gepa/gepa1/modal.log` |
| Parámetros de servicio (`max_model_len`, `gpu_memory_utilization`, `max_lora_rank`) | `config.yaml` (entrega final) y las demás `config_*.yaml` |
| Tiempo de entrenamiento (`segundos`), VRAM máxima (`vram_max_gb`), pérdidas finales | `corridas/sft-prompt-v1-r1/resumen.json`, `corridas/sft-ejemplo-v2/resumen.json`, `corridas/prueba-gpu-02/resumen.json` |
| Tokens reales de train y val, tokens en la pérdida | `corridas/<corrida>/datos.json` |
| Batch, acumulación, largo máximo y épocas usadas | `corridas/<corrida>/config_usada.yaml` y `entrenar.yaml` |
| Tiempo de la optimización de prompt (`segundos`, casos jugados) | `corridas/gepa/gepa1/resumen.json` |
| Métricas de sistema por paso (GPU, memoria, segundos por paso) | W&B, proyecto `juanlu1-austral/tp-admision-guardia`: runs `68qllkha` (`sft-prompt-v1` + `-r1`), `g69gw15q` (`sft-ejemplo-v2`) y `2r5rmemo` (`prueba-gpu-02`); links en el campo `wandb` de cada `resumen.json` |

Ojo: los tiempos de los pasos 1 a 100 de `sft-prompt-v1` y los segundos por
paso de `prueba-gpu-02` no están en ningún archivo (Parte 4, PENDIENTE); si
se usan, hay que exportarlos de W&B a `corridas/` antes de citarlos.
