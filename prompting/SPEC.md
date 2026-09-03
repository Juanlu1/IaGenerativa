# SPEC.md — Misión "El prompt mínimo"

Contrato de lo que construimos en esta misión. Ante conflicto entre este
documento y el código, manda este documento. Alcance: lo que piden los tres
ejercicios de [`mission.md`](mission.md), nada más.

---

## 1. La interfaz de chat (ejercicio 1)

Un chat que sirve 4 modelos vía OpenRouter. No tiene que ser linda: tiene que
cumplir los cuatro requisitos de abajo, que es lo que se corrige.

### 1.1 Modelos

IDs verificados por la cátedra al 2026-09-02. Si alguno desaparece del catálogo,
se reemplaza por el equivalente vigente **del mismo proveedor** y se anota el
cambio en el `INFORME.md`.

| Slot | Modelo | Capacidad que la interfaz tiene que ejercitar |
|---|---|---|
| 1 | `openai/gpt-5.6-luna` | `reasoning: {"effort": ...}` elegible por el usuario |
| 2 | `anthropic/claude-haiku-4.5` | caching explícito con `cache_control` sobre un bloque estático grande |
| 3 | `google/gemini-3.7-flash` | salida estructurada con JSON Schema |
| 4 | `deepseek/deepseek-v4-flash-0731` | el escalón barato; es el que usa el ejercicio 2 |

### 1.2 Requisitos

1. **Usage visible después de cada respuesta.** OpenRouter lo devuelve solo, sin
   pedirlo con ningún parámetro. Se muestran, como mínimo:
   `usage.prompt_tokens`, `usage.completion_tokens`,
   `usage.prompt_tokens_details.cached_tokens`,
   `usage.completion_tokens_details.reasoning_tokens`, `usage.cost` y
   `cache_discount`.
2. **Se puede cambiar de modelo**, y **cambiar de modelo inicia una conversación
   nueva** (se descarta el historial y se abre un log nuevo).
3. **Cada conversación se guarda en un archivo `.md`**: rol, mensaje, y el usage
   de cada respuesta. El guardado es automático, no manual — el log es la
   evidencia de auditoría del ejercicio 2, y una corrida sin log no cuenta.
4. Los 4 modelos son usables desde la interfaz, cada uno de un proveedor
   distinto.

### 1.3 Parámetros por proveedor

- **Razonamiento**: parámetro unificado `reasoning`. El slot 1 usa
  `{"effort": "low" | "medium" | "high" | ...}`. Claude y Gemini aceptan además
  `{"max_tokens": N}` como presupuesto de pensamiento.
- **Caching**: automático en OpenAI, Gemini y DeepSeek. En Anthropic hay que
  marcar los bloques estáticos con `"cache_control": {"type": "ephemeral"}`.
  El hit se ve en `cached_tokens` y en `cache_discount`.

### 1.4 Criterio de éxito

- Se chatea con los 4 modelos y se ve el usage de cada respuesta.
- Queda un log `.md` por conversación.
- En el slot 1 se ve el efecto de cambiar el effort.
- En el slot 2 se ve un cache hit: el costo de entrada baja en la segunda pasada
  del mismo contexto.

### 1.5 Fuera de alcance

Autenticación, UI linda, historial persistente entre sesiones, streaming,
soporte de modelos más allá de los 4 slots.

---

## 2. `vida.py` (ejercicio 2)

El contrato que el prompt tiene que transmitir completo. **No es negociable**:
es la interfaz que invocan los tests de la cátedra.

- Uso: `python3 vida.py <archivo_estado_inicial> <generaciones>`.
- El archivo de estado es una grilla rectangular: una línea por fila, `#` célula
  viva, `.` célula muerta.
- El mundo es **finito**, del tamaño de la grilla: fuera de los bordes todo está
  muerto. **Sin wrap-around.**
- Imprime por stdout la grilla resultante tras N generaciones, en el mismo
  formato.
- Con `generaciones = 0` imprime el estado inicial tal cual.
- Un solo script, **solo biblioteca estándar**.

### 2.1 Reglas de la corrida

1. El script se pide **a través de nuestro chat**, al modelo del slot 4, con el
   razonamiento activado.
2. Correcto en **1 prompt, o 2 a lo sumo** (el segundo solo para pulir).
3. Si se pasa de 2, la corrida quedó **quemada**: conversación nueva y prompt
   reescrito desde cero. Prohibido parchear el código a mano o seguir chateando.
   Lo que se mejora entre intentos es **el prompt**, no el código.
4. "Correcto" = los **9 tests** de `test_vida.py` pasan con el script tal cual
   salió del chat.
5. **Caching obligatorio.** En DeepSeek el cache es automático por prefijo
   repetido: la parte estática del prompt (contrato, instrucciones, ejemplos) va
   al principio e **idéntica** en todos los intentos, y lo que cambia va al
   final. Desde el 2º intento, `cached_tokens > 0`.

### 2.2 Criterio de éxito

El log de la conversación ganadora muestra 1 o 2 prompts, `test_vida.py` da los
9 en verde, y los intentos posteriores al primero muestran cache hits.

---

## 3. El informe (ejercicio 3)

Documenta **todos** los intentos del ejercicio 2, los quemados incluidos:

- Tokens de entrada y salida por intento, y totales.
- Tokens de pensamiento y qué se facturó por ellos. Si el modelo razona sin
  devolver esos tokens, se documenta como hallazgo.
- Tokens cacheados y cuánto se ahorró.
- Gasto total en USD, **contrastado contra el dashboard de actividad** de
  OpenRouter.
- Conclusión de tres líneas con una **decisión concreta** para bajar el costo sin
  perder el "1 prompt" (no vale "mejorar el prompt").

Incluye además las respuestas de la sección "Antes de todo" del enunciado: qué es
un router, el mapa de modelos por proveedor (precio in/out, contexto, benchmarks)
y la comparación de parámetros soportados.
