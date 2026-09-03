# Logs de prueba — ejercicio 1

Evidencia de que los 4 modelos son usables desde la interfaz y de que cada
conversación se guarda con su usage. Todos los generó la interfaz sola; lo único
que se hizo a mano fue renombrarlos (la interfaz los nombra por fecha y hora,
que no dice nada al leer el repo). El contenido no se tocó.

## Un chat por modelo

| Archivo | Slot | Modelo | Qué muestra |
|---|---|---|---|
| `chat-slot1-gpt-5.6-luna.md` | 1 | `openai/gpt-5.6-luna` | Dos turnos con effort distinto: `low` da 0 tokens de razonamiento, `high` da 266 |
| `chat-slot2-claude-haiku-4.5.md` | 2 | `anthropic/claude-haiku-4.5` | Contexto estático de ~5200 tokens con `cache_control`; los dos turnos muestran 5192 cacheados |
| `chat-slot3-gemini-3.7-flash.md` | 3 | `google/gemini-3.7-flash` | Salida estructurada: las dos respuestas son JSON que valida contra el schema pedido |
| `chat-slot4-deepseek-v4-flash.md` | 4 | `deepseek/deepseek-v4-flash-0731` | El escalón barato, con razonamiento prendido y apagado |

## Los tres demos

Cada uno corre una secuencia fija y deja las tres o dos llamadas en un solo log.

| Archivo | Qué demuestra | Resultado |
|---|---|---|
| `demo-effort-slot1.md` | El efecto de cambiar `reasoning_effort` | low 381 · medium 516 · high 516 tokens de razonamiento |
| `demo-cache-slot2.md` | El cache hit del slot 2 | 1ª pasada: 0 cacheados, $0.006783 · 2ª pasada: 5214 cacheados, $0.000766 (**8.9× más barato**) |
| `demo-precio-slots2y4.md` | La diferencia de precio entre el slot caro y el barato | slot 2 $0.000322 (60 tokens de salida) · slot 4 $0.000008 (44 tokens) |

## Dos cosas que conviene saber al leerlos

- **El demo de effort no es monótono**: `medium` y `high` dieron los mismos 516
  tokens de razonamiento. El efecto se ve entre `low` y el resto, no entre los
  tres niveles. Con esta pregunta el modelo llega a su techo de razonamiento en
  `medium`.
- **El demo de cache antepone una marca única al contexto en cada corrida.** Sin
  eso, si quedó cache caliente de una conversación anterior, la primera pasada
  ya da hit y no se ve la transición. La marca fuerza un miss real en la primera.
