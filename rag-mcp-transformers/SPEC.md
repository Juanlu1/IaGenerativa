# SPEC — Parte 1: RAG vectorial

Contrato de comportamiento del recuperador de la misión (`mission.md`, parte 1).
Ante conflicto entre el código y este archivo, manda este archivo; ante conflicto
entre este archivo y `mission.md`, manda `mission.md`.

## Para qué existe

Dada una pregunta de un paciente, devolver los fragmentos de `datos/corpus/` que
la responden, en orden de relevancia. Lo usan tres consumidores:

1. `recuperar.py`: el comando que corre la cátedra sobre las preguntas de test.
2. La tool `buscar_documentos` del agente de la parte 2 (`agente.py`).
3. La misma tool en el servidor MCP de la parte 3 (`servidor_mcp.py`).

## Interfaz pública (estable: las partes 2 y 3 dependen de ella)

```python
from recuperador import Recuperador

r = Recuperador.desde_config()        # lee config_rag.json; carga el modelo una vez
r.buscar("¿Horario de visita en terapia intensiva?")         # -> list[str]
r.buscar("¿Horario de visita en terapia intensiva?", k=3)    # pisa el top-k de la config
```

- `buscar` devuelve una lista de strings (el texto de cada fragmento), ordenada de
  más a menos relevante. Puede devolver menos de `k` si el umbral o el margen
  descartan resultados, pero **nunca devuelve una lista vacía**: si todo queda
  debajo del umbral, devuelve el mejor fragmento.
- `desde_config(ruta=None)` resuelve las rutas (`config_rag.json`, `datos/corpus/`)
  respecto de la carpeta de `recuperador.py`, no del directorio de trabajo: se
  puede importar desde cualquier lado.
- El modelo se carga una sola vez por instancia. El agente crea un `Recuperador`
  al arrancar y lo reutiliza en cada llamada a la tool.
- Cambiar la configuración ganadora (encoder, chunking, umbrales) no cambia esta
  interfaz.

## CLI (contrato de `mission.md`)

```bash
python3 recuperar.py --preguntas datos/preguntas_recuperacion_dev.jsonl --salida resultados.jsonl
```

Escribe una línea por pregunta, `{"id": "R01", "fragmentos": [...]}`, en el orden
de entrada, con UTF-8 sin escapar. Usa `config_rag.json` y no acepta parámetros
de tuning: la configuración entregada es la que está fija en ese archivo.

## Fragmentos (chunking)

El evaluador considera útil un fragmento solo si **contiene textual** la frase de
evidencia (normalizada en minúsculas y espacios). Por eso:

- **`seccion`**: un fragmento por sección `##` del Markdown. Un documento sin
  secciones es un solo fragmento. Nunca corta una oración.
- **`ventana`**: ventanas de N palabras con solapamiento S, como comparación.
  Puede cortar una evidencia al medio; eso es parte de lo que se mide.
- **`metadatos`** (opcional, para cualquier estrategia): antepone
  `"<título del documento> — <título de la sección>"` al texto que se embebe. El
  texto que se **devuelve** es el del fragmento (con los metadatos adelante si
  están activados), sin alterar el cuerpo, para que la evidencia siga siendo
  una subcadena.

## Encoders

| Nombre en la config | Modelo | Pooling / prefijos |
|---|---|---|
| `bert-base` (línea de base obligatoria) | `google-bert/bert-base-multilingual-cased` | promedio de los vectores de la última capa, pesado por la máscara de atención |
| `minilm` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | el de sentence-transformers |
| `e5-small` / `e5-base` | `intfloat/multilingual-e5-{small,base}` | `query: ` y `passage: ` |
| `bge-m3` (si alcanza el tiempo) | `BAAI/bge-m3` | el de sentence-transformers |

Todos los embeddings se normalizan a norma 1 y la similitud es el coseno. Todo
corre en CPU.

## Selección

Sobre los fragmentos ordenados por coseno:

1. Quedarse con los primeros `k`.
2. Descartar los que tengan coseno menor que `umbral` (absoluto).
3. Descartar los que estén a más de `margen` del mejor (`coseno < mejor - margen`).
4. Si no quedó ninguno, devolver el mejor.

`umbral` y `margen` son opcionales (`null` = no se aplica).

## `config_rag.json`

```json
{"encoder": "e5-base", "chunking": "seccion", "metadatos": true,
 "tam_ventana": null, "solapamiento": null,
 "k": 3, "umbral": null, "margen": 0.02}
```

(Valores de ejemplo; los definitivos salen de los experimentos.)

## Experimentos

`experimentar.py` corre una grilla de configuraciones. Para cada una escribe
`experimentos/<nombre>.jsonl` y corre el evaluador oficial
(`evaluar/evaluar.py recuperacion`, sin modificar), que genera
`experimentos/<nombre>.jsonl.eval.json`. Al final escribe `experimentos/tabla.md`
con una fila por configuración: encoder, chunking, metadatos, k, umbral, margen,
context_relevance, recall, precision, MRR y fragmentos promedio. Esa tabla va al
`INFORME.md`.

Criterio para elegir la configuración ganadora: el mayor `context_relevance` en
`dev`. Ante diferencias menores a 0,02, la más simple (menos perillas activas),
porque la cátedra evalúa sobre preguntas que no vemos.

## Criterios de aceptación

1. `pytest` en verde (tests con un encoder falso: no descargan modelos).
2. El comando CLI de arriba corre de punta a punta y el evaluador oficial lo acepta.
3. La configuración entregada le gana con claridad a la línea de base `bert-base`.
4. `Recuperador.desde_config().buscar(...)` funciona importado desde otra carpeta.
5. No se modifican `evaluar/`, `api/`, `datos/` ni `atencion/test_atencion.py`.
