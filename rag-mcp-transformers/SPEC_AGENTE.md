# SPEC — Partes 2 y 3: agente con herramientas y servidor MCP

Contrato de comportamiento del asistente (`mission.md`, partes 2 y 3). El del
recuperador de la parte 1 está en [`SPEC.md`](SPEC.md). Ante conflicto entre el
código y este archivo, manda este archivo; ante conflicto entre este archivo y
`mission.md`, manda `mission.md`.

## Para qué existe

Contestar preguntas de pacientes con dos fuentes: los documentos del hospital
(recuperador de la parte 1) y la API del día (`api/servidor.py`). Hay dos agentes
que hacen lo mismo y solo difieren en cómo obtienen las herramientas:

| | Parte 2 | Parte 3 |
|---|---|---|
| Comando | `agente.py` | `agente_mcp.py` |
| Herramientas | Importadas de `herramientas.py` y envueltas como tools de LangChain | Descubiertas en `servidor_mcp.py` con `tools/list` y llamadas con `tools/call` |
| Salida | `respuestas.jsonl` | `respuestas_mcp.jsonl` |

## Archivos

| Archivo | Responsabilidad | Usa LangChain |
|---|---|---|
| `herramientas.py` | Las seis herramientas, como funciones comunes de Python. **Único lugar** donde se consulta la API o el recuperador | No |
| `bucle_agente.py` | Lo común a los dos agentes: modelo, prompt de sistema, bucle de tool calling, salida y log | Sí |
| `agente.py` | Parte 2: envuelve las funciones de `herramientas.py` como tools de LangChain | Sí |
| `servidor_mcp.py` | Parte 3: publica las mismas funciones con FastMCP (SDK `mcp` 1.x), por stdio | No |
| `agente_mcp.py` | Parte 3: levanta el servidor, carga sus tools con `langchain-mcp-adapters` y corre el mismo bucle. No importa `herramientas.py` ni `recuperador.py` | Sí |

## Herramientas

Los nombres son fijos (los usa el evaluador para medir el ruteo):

| Herramienta | Fuente | Devuelve |
|---|---|---|
| `buscar_documentos(consulta)` | `Recuperador.desde_config().buscar(consulta)` | Los fragmentos, separados por `\n\n---\n\n` |
| `consultar_camas(sector)` | `GET /camas?sector=` | El JSON de la API, como texto |
| `consultar_guardia(especialidad)` | `GET /guardia?especialidad=` | Ídem |
| `consultar_turnos(especialidad)` | `GET /turnos?especialidad=` | Ídem |
| `consultar_farmacia(medicamento)` | `GET /farmacia?medicamento=` | Ídem |
| `consultar_espera()` | `GET /espera` | Ídem |

- Todas devuelven **texto** y **nunca lanzan una excepción**. Un 400 o 404 de la
  API devuelve el cuerpo del error, que trae la lista de opciones válidas, para que
  el modelo pueda corregirse. Si la API está caída, devuelven un JSON con `error`.
- La descripción que lee el modelo es el **docstring** de cada función, el mismo
  en las dos partes. Así, si los números de la parte 3 difieren de los de la 2, la
  causa no es una descripción distinta.
- El recuperador se crea **una sola vez** por proceso (cargar el modelo tarda unos
  15 segundos) y se usa con la configuración entregada en la parte 1, sin pisar `k`.
- La URL de la API es `http://localhost:8765`, o la de la variable
  `HOSPITAL_API_URL` si está definida (la usan los tests).

## Bucle del agente

1. Mensajes iniciales: el prompt de sistema y la pregunta.
2. Se llama al modelo con las seis herramientas disponibles.
3. Si el modelo pide herramientas, se ejecutan todas, se agrega cada resultado
   como mensaje y se vuelve al paso 2.
4. Si el modelo no pide herramientas, su texto es la respuesta.
5. Tope de 6 llamadas al modelo por pregunta. Si se alcanza, se hace una última
   llamada sin herramientas para que responda con lo que tiene.

Una herramienta que no existe o que recibe argumentos inválidos no corta la
corrida: el error vuelve al modelo como resultado de la herramienta.

**Modelo:** `deepseek/deepseek-v4-flash-0731` por OpenRouter, con `ChatOpenAI`
(`base_url="https://openrouter.ai/api/v1"`), temperatura 0. La key se lee de
`OPENROUTER_API_KEY`; si no está en el entorno, se carga de `.env`.

## CLI (contrato de `mission.md`)

```bash
python3 agente.py     --preguntas datos/preguntas_agente_dev.jsonl --salida respuestas.jsonl
python3 agente_mcp.py --preguntas datos/preguntas_agente_dev.jsonl --salida respuestas_mcp.jsonl
```

La API del hospital tiene que estar corriendo. Opcional: `--log <ruta>` para
elegir dónde se escribe el log (por defecto, `logs/<fecha>-<hora>-<agente>.md`).

Salida: una línea por pregunta, en el orden de entrada, UTF-8 sin escapar:

```json
{"id": "A01", "respuesta": "...", "contextos": ["...", "..."], "herramientas": ["buscar_documentos", "..."]}
```

- `contextos`: el texto de **cada** resultado de herramienta que recibió el modelo,
  en orden, incluidos los errores.
- `herramientas`: el nombre de cada herramienta llamada, en orden.

## Log de la corrida

Cada corrida escribe un `.md` con:

- Encabezado: fecha, agente, modelo, archivo de preguntas, las herramientas tal
  como las vio el modelo (nombre y descripción) y el consumo de la key antes y
  después (`GET /api/v1/key`).
- Por pregunta: cada llamada al modelo con su `generation id` y su usage (tokens
  de entrada, de salida, de razonamiento y costo), las herramientas pedidas con
  sus argumentos, el resultado de cada una y la respuesta final.
- Totales: llamadas al modelo, tokens y costo, por pregunta y de la corrida.

El usage sale del objeto que devuelve OpenRouter, sin transcribir a mano. La key
nunca se escribe en el log.

## Criterios de aceptación

1. `pytest` en verde, sin red: los tests usan un modelo falso, un encoder falso y
   la API de la cátedra levantada en un puerto libre.
2. Los dos comandos corren de punta a punta y el evaluador oficial acepta sus salidas.
3. En `dev`: ruteo cercano a 1 y las tres métricas del juez por encima de 4.
4. `agente_mcp.py` no importa `herramientas`, `recuperador` ni hace pedidos HTTP a la API.
5. El servidor MCP responde `tools/list` con las seis herramientas y se puede usar
   desde el MCP Inspector.
6. No se modifican `evaluar/`, `api/`, `datos/` ni `atencion/test_atencion.py`.
