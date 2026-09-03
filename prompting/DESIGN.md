# DESIGN.md — interfaz de chat (ejercicio 1)

Diseño de la interfaz que pide el ejercicio 1. El **qué** (los requisitos que se
corrigen) está en [`SPEC.md`](SPEC.md); acá está el **cómo**. Los hallazgos de la
API que condicionan varias decisiones están en [`CLAUDE.md`](CLAUDE.md).

## Forma

Página web única servida por Flask, en local. El enunciado dice que no tiene que
estar linda, pero una página hace dos cosas que una CLI hace mal: mostrar el
usage como bloque estructurado debajo de cada respuesta, y pegar el prompt largo
del ejercicio 2 sin pelear con la terminal.

**La conversación vive en el servidor, en memoria.** Es una sola usuaria en su
propia máquina, y el servidor ya necesita el historial para escribir el `.md`.
Mandarlo desde el navegador en cada request no compra nada. Contra: al reiniciar
se pierde la conversación en curso — pero el `.md` ya está en disco, y esa es la
evidencia que importa.

## Módulos

Cinco archivos, uno por responsabilidad. Los dos primeros son funciones puras
sobre diccionarios, testeables sin red ni gasto.

| Archivo | Responsabilidad | Depende de |
|---|---|---|
| `chat/slots.py` | Config de los 4 modelos: id, capacidad que ejercita, controles que muestra la UI | — |
| `chat/usage.py` | Normaliza el `usage` crudo de OpenRouter a una estructura fija | — |
| `chat/openrouter.py` | Cliente HTTP: arma el body por slot, llama, devuelve texto + usage + generation id | `usage` |
| `chat/logger.py` | Abre y appendea el `.md` de cada conversación | `usage` |
| `chat/app.py` | Flask: rutas, estado de la conversación, los 3 demos, la página | todos |

## Flujo de un mensaje

1. El navegador manda `{mensaje, parámetros del slot}` a `POST /api/chat`.
2. `app.py` lo agrega al historial de la conversación en curso.
3. `openrouter.py` arma el body según el slot y llama a la API.
4. `usage.py` normaliza la respuesta.
5. `logger.py` appendea el turno al `.md`.
6. La página pinta la respuesta, su bloque de usage, y refresca el panel de gasto.

## Rutas

| Ruta | Qué hace |
|---|---|
| `GET /` | La página |
| `POST /api/chat` | Un turno de conversación |
| `POST /api/slot` | Cambia de modelo: descarta el historial y abre un `.md` nuevo |
| `POST /api/demo/<nombre>` | Corre uno de los 3 demos (`effort`, `cache`, `precio`) |
| `GET /api/presupuesto` | `usage` y `limit_remaining` de la key |
| `POST /api/prompt-archivo` | Carga el texto de un archivo del disco en la caja de prompt |

## La estructura normalizada del usage

`usage.py` devuelve siempre las mismas claves, con `None` donde el campo no vino.
Esto no es defensivo por las dudas: ya verificamos contra la API que
`cache_discount` **viene ausente, no en cero**, cuando no hubo evento de cache.

```
prompt_tokens        completion_tokens     reasoning_tokens
cached_tokens        cache_write_tokens    cost
cache_discount       generation_id         model
```

Guarda además la respuesta cruda, para que el informe del ejercicio 3 pueda
sacar cualquier campo que no hayamos previsto sin volver a gastar llamadas.

## Controles por slot

Lo que hace que la interfaz *ejercite* cada capacidad, en vez de solo llamar a
cuatro modelos distintos:

| Slot | Modelo | Control en la UI | Qué manda al API |
|---|---|---|---|
| 1 | `openai/gpt-5.6-luna` | Desplegable de effort: low / medium / high | `reasoning: {effort}` |
| 2 | `anthropic/claude-haiku-4.5` | Checkbox "adjuntar contexto estático" | Bloque grande con `cache_control: {type: ephemeral}` |
| 3 | `google/gemini-3.7-flash` | Textarea con un JSON Schema (trae uno de ejemplo) | `response_format` con el schema |
| 4 | `deepseek/deepseek-v4-flash-0731` | Toggle de razonamiento on/off | `reasoning` |

Común a los cuatro: cargar el prompt desde un archivo del disco.

El **contexto estático** del slot 2 son nuestros propios `mission.md` + `SPEC.md`
concatenados (~16 KB, ya están en el repo): alcanza para superar el mínimo
cacheable de Anthropic y no hay que inventar relleno ni descargar nada.

## Los 3 demos

Cada botón corre una secuencia fija, muestra los resultados lado a lado y deja su
propio `.md`. Son los tres criterios de éxito del ejercicio 1 vueltos evidencia
reproducible:

1. **Effort** (slot 1): la misma pregunta con low, medium y high → tabla con
   `reasoning_tokens`, latencia y costo de cada uno.
2. **Cache** (slot 2): el mismo contexto estático dos veces seguidas → muestra
   `cached_tokens` y el costo de entrada de la primera contra la segunda.
3. **Precio** (slots 2 y 4): la misma pregunta a los dos → los dos costos y el
   múltiplo entre ellos.

## Panel de gasto

Total de la conversación en curso (tokens y USD) y el presupuesto de la key
(`usage` y `limit_remaining` de `GET /api/v1/key`), refrescado después de cada
respuesta. Es la contabilidad que va al ejercicio 3: la cuenta de OpenRouter es
del curso entero, así que el número auditable es el de nuestra key.

## Formato del log

Un `.md` por conversación, nombre `<fecha>-<hora>-<slot>.md`, en `logs/pruebas/`
o `logs/conway/` según un desplegable. Se abre al empezar la conversación y se le
appendea cada turno: si el proceso se cae, lo ya ocurrido quedó escrito. Eso es lo
que evita perder un intento quemado del ejercicio 2.

```markdown
# Conversación — anthropic/claude-haiku-4.5
Inicio: 2026-09-03 14:02:11 · Slot 2 (prompt caching explícito)

## Turno 1 · usuario
...el mensaje...

## Turno 1 · asistente
...la respuesta...

| entrada | salida | razonamiento | cacheados | costo | descuento cache |
|---|---|---|---|---|---|
| 4821 | 312 | — | 0 | $0.005133 | — |

generation id: gen-1788403287-cuRGvN3vb9kzlchTAVoe
```

## Errores

- **Error HTTP de la API**: se muestra en la página y se loguea como turno
  fallido. La conversación no se pierde.
- **Campo ausente en el usage**: se muestra `—`. Nunca `KeyError`.
- **Presupuesto bajo**: aviso visible cuando `limit_remaining` baja de USD 0.20
  (el 20% del presupuesto de la key).
- **`GET /api/v1/generation`**: da 404 hasta ~15s después de la respuesta. Si se
  consulta, se reintenta; nunca se pide inmediatamente después.

## Tests

`pytest` sobre `usage.py` y `logger.py`, con respuestas de mentira:

- normaliza correctamente una respuesta completa;
- no explota con una respuesta sin `cache_discount` ni `reasoning_tokens`
  (el caso real que verificamos);
- el `.md` sale con el formato esperado y el append no pisa turnos anteriores.

No se testea la red: los tests no deben gastar créditos.

## Fuera de alcance

Autenticación, historial navegable de conversaciones viejas, streaming de
respuestas, persistencia entre reinicios, y modelos fuera de los 4 slots. Nada de
eso se corrige.
