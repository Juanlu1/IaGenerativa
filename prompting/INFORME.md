# Antes de todo (obligatorio)

Relevado en `openrouter.ai/discover`, las fichas de cada modelo y `GET https://openrouter.ai/api/v1/models`.

## 1. Qué es un router

Un router de modelos recibe el prompt y elige qué modelo lo responde (el Auto Router lo decide según lo que la comunidad de OpenRouter usó para tareas parecidas en los últimos 7 días): resuelve tener que elegir a mano entre cientos de modelos con precios y calidades distintas, y cae a otro proveedor cuando uno falla.

## 2. El mapa de modelos

Benchmark: Artificial Analysis *Intelligence Index* (0–100), board "Today's Frontier" de `/discover`.

| Proveedor | Modelo | Entrada USD/M | Salida USD/M | Contexto | Benchmark |
|---|---|---:|---:|---:|---|
| OpenAI | `openai/gpt-6-astra` | 10.00 | 50.00 | 1.05M | 53 — #2 |
| Anthropic | `anthropic/claude-fable-5.1` | 10.00 | 50.00 | 1M | 53 — #1 (y #1 en coding, 82) |
| Grok (xAI) | `x-ai/grok-4.6` | 2.00 | 6.00 | 500K | 44 — #4 |
| Gemini | `google/gemini-3.8-flash` | 0.75 | 3.75 | 1.05M | 41 — #5 |
| Qwen | `qwen/qwen3.8-max-0902` | 2.00 | 6.00 | 1M | 53 — #3 |
| DeepSeek | `deepseek/deepseek-v4-pro-0813` | 0.578 | 1.734 | 1.05M |  fuera del top 5 |
| Kimi | `moonshotai/kimi-k3` | 1.95 | 10.92 | 1.05M | fuera del top 5 |

## 3. Parámetros comunes

| Parámetro | GPT-6 Astra | Claude Fable 5.1 | DeepSeek V4 Pro |
|---|:-:|:-:|:-:|
| `reasoning` / `reasoning_effort` | ✅ | ✅ | ✅ |
| `structured_outputs` / `response_format` | ✅ | ✅ | ✅ |
| `tools` | ✅ | ✅ | ✅ |
| `temperature`, `top_p` | ❌ | ❌ | ✅ |
| `top_k`, `min_p`, penalties, `logit_bias`, `logprobs` | ❌ | ❌ | ✅ |
| `verbosity` | ❌ | ✅ | ❌ |

Los modelos de frontera cerrados no exponen perillas de sampling; los abiertos (DeepSeek, Kimi, Qwen) exponen todas. Entre los modelos del ejercicio 1, `claude-haiku-4.5` acepta `reasoning` pero no `reasoning_effort`, y `gpt-5.6-luna` no acepta `temperature`.

# Ejercicio 3 — La cuenta final

## Intentos del Ejercicio 2

Para generar `vida.py` se utilizó el modelo `deepseek/deepseek-v4-flash-0731` con razonamiento activado.

| Intento | Prompts | Tokens de entrada | Tokens de salida | Tokens de razonamiento | Tokens cacheados | Costo | Resultado |
|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | 1223 | 818 | 310 | 0 | USD 0.000172 | Generó el `vida.py` utilizado en la entrega y pasó los 9 tests |
| 2 | 1 | 1223 | 935 | 317 | 1223 | USD 0.000134 | Se repitió el mismo prompt para verificar el prompt caching obligatorio; se registró un cache hit de 1223 tokens |

Logs: el intento 1 es `logs/conway/2026-09-17-160135-slot4.md` y el intento 2 es `logs/conway/2026-09-17-142741-slot4.md`. Los nombres no siguen el orden real porque el del intento 1 quedó en hora UTC (16:01 UTC = 13:01 en Argentina) y el del intento 2 en hora local. El orden lo confirman los `generation id` guardados en cada log: `gen-1789661228-…` (13:07) y `gen-1789666340-…` (14:32).

## Totales

- Tokens de entrada: 2446
- Tokens de salida: 1753
- Tokens de razonamiento: 627
- Tokens cacheados: 1223
- Gasto total exacto: USD 0.00030532

## Uso de caché

En el primer intento no se registraron tokens cacheados.

En el segundo intento, OpenRouter informó:

- Tokens cacheados: 1223
- Costo real: USD 0.00013378
- Ahorro por caché (`cache_discount`): USD 0.00002446
- Costo teórico sin descuento de caché: USD 0.00015824

El segundo intento reutilizó los 1223 tokens de entrada desde caché, reduciendo el costo de la generación.

## Verificación de costos en OpenRouter

Se consultó el detalle de ambas generaciones directamente en OpenRouter mediante los `generation id` guardados en los logs.

- Intento 1: USD 0.00017154
- Intento 2: USD 0.00013378
- Gasto total exacto: USD 0.00030532

Los logs de la interfaz mostraron los costos redondeados como USD 0.000172 y USD 0.000134. La diferencia respecto de los valores anteriores se debe únicamente al redondeo de la visualización.

En el primer intento, `cache_discount` fue `null`, ya que no hubo uso de caché. En el segundo intento, OpenRouter informó un ahorro de USD 0.00002446 por reutilización de caché.

## Tokens de razonamiento

El modelo se utilizó con razonamiento activado en ambos intentos.

- Intento 1: 310 tokens de razonamiento
- Intento 2: 317 tokens de razonamiento
- Total: 627 tokens de razonamiento

OpenRouter informó estos tokens dentro del usage de cada generación. En los detalles consultados no apareció un costo separado exclusivamente para los tokens de razonamiento, sino un `total_cost` por generación. Por ese motivo, para la contabilidad final se tomó como fuente de verdad el costo total informado por OpenRouter.

Los tokens de razonamiento van incluidos en los tokens de salida y se facturan a la tarifa de salida (USD 0.12/M): 627 × 0.12/M = USD 0.0000752, un 25 % del gasto total.

## Conclusión

Bajaríamos el razonamiento a `reasoning: {"effort": "low"}`: es el 25 % del gasto y el problema no necesita más.

Agregaríamos al prompt "respondé solo con el bloque de código, sin explicación", para recortar la salida, que cuesta el doble que la entrada.

Mantendríamos `deepseek/deepseek-v4-flash-0731` y el mismo prefijo estático, que resolvió en 1 prompt y es lo que produce el cache hit.