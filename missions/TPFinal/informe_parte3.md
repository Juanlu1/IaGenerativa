# Parte 3: optimización de prompt, antes de entrenar

Apartado de la Parte 3 para unir a `INFORME.md`. Todo se hizo con Gemma 4 E4B sin entrenar
(`google/gemma-4-E4B-it`, revisión `4ecc2ba63bcac23ba4a767fc87025b1450f84c9c`), servido con vLLM 0.33.0 en una
A100 de 40 GB de Modal.

## Qué se optimiza

Solo el texto del mensaje de sistema. El resto del agente es el de `entrega.py` sin cambios: el `AgenteJSON` del kit
(`admision/ejemplo.py`), el mismo formato de mensajes (una llamada a una herramienta por turno, en JSON), el buscador
de la Parte 2 y la misma generación determinista (temperatura 0). Así el prompt se optimiza en el mismo formato con el
que después se evalúa y se entrena.

El punto de partida es `prompt_base.txt`, el mensaje de sistema de `admision/ejemplo.py` tal cual.

## Largo del prompt

Se mide en tokens con el tokenizer de Gemma 4 E4B (misma revisión), sobre el texto del mensaje de sistema solo, sin
la plantilla de chat (`AutoTokenizer.encode(texto, add_special_tokens=False)`). `optimizar_prompt.py` usa la misma
medida para la penalización por largo; si no puede cargar el tokenizer, usa caracteres / 4 y lo anota en su
`resumen.json`.

| Prompt | Tokens | Caracteres |
|---|---:|---:|
| `prompt_base.txt` | 615 | 2.232 |
| `prompt_corto.txt` | 467 | 1.634 |
| `prompt_optimizado.txt` | 693 | 2.429 |

## Prompt corto, a mano

`prompt_corto.txt` es `prompt_base.txt` acortado a mano sin sacar ninguna regla: las cinco herramientas con todos sus
argumentos y valores posibles, los ocho campos de la ficha más `fundamentos`, el protocolo (solo un objeto JSON por
turno, una herramienta por turno, el caso termina con `registrar_decision`), que el agente no toma decisiones clínicas
y qué normas tiene que buscar antes de decidir. Se sacaron las descripciones repetidas y la redacción larga de los
argumentos. Queda 24 % más corto (de 615 a 467 tokens). `config_corto.yaml` es `config.yaml` con ese prompt.

## Optimización con GEPA

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

## Casos usados

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

Pasan las 1.590 filas correctas, sin descartes (`uv run python casos_optimizacion.py`). Por circuito: 509 sepsis,
494 sin circuito, 340 ECG y 247 ACV; por cobertura: 756 sin cobertura, 311 prepaga, 306 ART y 217 obra social.

Límite: el control 3 no es independiente de la Parte 1. Una fila es `correcta` justamente porque cumple las normas y
las costumbres, así que el etiquetador y la clasificación comparten la misma lectura de las normas. El control
independiente es el 1, contra las fichas oficiales de la práctica.

De esas filas, `optimizar_prompt.py` elige con la semilla los casos de optimización y de validación, sin repetir caso
entre los dos conjuntos, y reparte la versión de las normas en rotación (original, b, c), así el prompt no se ajusta a
los números de una sola versión.

## Comandos

Prueba en la Mac, sin GPU (modelo falso: el agente sigue un guion fijo y la reflexión saca el último párrafo):

```bash
MODELO_FALSO=1 uv run python optimizar_prompt.py --presupuesto prueba --salida corridas/gepa/prueba_mac --sin-copiar-a-raiz
```

En Modal (detalle en `MODAL.md`, sección 8):

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

## Resultados

Casos resueltos sobre los 50 de práctica, con el modelo sin entrenar. Fuente: `corridas/tabla.md`.

| Prompt | Tokens | original | b | c | Corrida |
|---|---:|---:|---:|---:|---|
| Referencia de la cátedra (sin entrenar) | | 12 | 15 | 12 | `mission.md` |
| `prompt_base.txt` | 615 | 11 | 8 | 9 | `corridas/base/` |
| `prompt_corto.txt` | 467 | 6 | 5 | 3 | `corridas/prompt_corto/` |
| `prompt_optimizado.txt` | 693 | 8 | 10 | 10 | `corridas/prompt_optimizado/` |

La línea de base (`corridas/base/`, commit `d222a92`, 50 casos, búsquedas 1,3 por caso) queda por debajo de la
referencia de la cátedra en las tres versiones, sobre todo en b (8 contra 15). Los controles que más fallan son
`box_antes_del_registro` (60 a 62 % de aciertos), `registro` (68 a 74 %), `aviso_al_voluntariado` (72 %), `cobertura`
(72 a 76 %) y la verificación (72 a 78 %); `numero_documento` y `circuito` casi no fallan. La generación es greedy, pero
el lote en GPU puede mover algún caso entre corridas (ver Auditabilidad en `mission.md`).

Optimización con GEPA (`corridas/gepa/gepa1/resumen.json` y `log.jsonl`):

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

### Lectura de los resultados

- **El prompt corto empeora en las tres versiones** (6, 5 y 3 contra 11, 8 y 9). Casi toda la caída está en
  `box_antes_del_registro`, que baja de 60 a 62 % de aciertos a 36 a 42 %, y en `plazo_circuito_min` (de 90 a 92 %
  a 78 a 80 %). Al sacar la redacción larga de los argumentos se perdió contexto que la Gemma sin entrenar usaba para
  esos campos, aunque las reglas sigan escritas. Ahorra 148 tokens de prompt y unos 3.700 caracteres de contexto por
  caso, que no compensan.
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
