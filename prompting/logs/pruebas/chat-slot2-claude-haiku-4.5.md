# Conversación — anthropic/claude-haiku-4.5
Inicio: 2026-09-03 08:28:12 · Slot 2 (Prompt caching explícito)

## Turno 1 · usuario

Segun el contexto que te pase: cuantos prompts como maximo permite el ejercicio 2?

## Turno 1 · asistente

Según el ejercicio 2 en `mission.md`, el máximo permitido es **2 prompts**.

Específicamente, la regla dice:

> Tiene que quedar **correcto en 1 prompt, o a lo sumo 2** (el segundo solo para pulir detalles).

Y si se pasan de 2:

> Si se pasan de 2, **la corrida quedó quemada**: conversación nueva, prompt reescrito desde cero, y de vuelta.

Entonces:
- **Ideal**: 1 prompt correctamente diseñado
- **Máximo permitido**: 2 prompts (el segundo solo para ajustes menores)
- **Si hay 3 o más**: la corrida no cuenta, hay que empezar de nuevo

| entrada | salida | razonamiento | cacheados | costo | descuento cache |
|---|---|---|---|---|---|
| 5223 | 189 | 0 | 5192 | $0.001495 | — |

generation id: gen-1788434893-wQC2qOhIe3A920ONeLQ4

## Turno 2 · usuario

Y que pasa si me paso de esa cantidad?

## Turno 2 · asistente

Si te pasas de 2 prompts, según el ejercicio 2:

> Si se pasan de 2, **la corrida quedó quemada**: conversación nueva, prompt reescrito desde cero, y de vuelta. Prohibido parchear a mano o seguir chateando: lo que se mejora entre intentos es **el prompt**, no el código.

**En concreto:**

1. **La corrida actual no cuenta** — se descarta completamente
2. **Tienes que empezar una conversación nueva** con el chat
3. **El prompt tiene que ser reescrito desde cero** (no vale reutilizar el anterior con pequeños cambios)
4. **No puedes parchear el código a mano** ni seguir chateando con el modelo para arreglarlo
5. **Solo se mejora el prompt**, no el código generado

Esto aplica para todos los intentos que se pasen de 2. El objetivo es que aprendas a escribir prompts muy precisos y completos desde la primera vez, no que depures código interactivamente con el modelo.

| entrada | salida | razonamiento | cacheados | costo | descuento cache |
|---|---|---|---|---|---|
| 5427 | 264 | 0 | 5192 | $0.002074 | — |

generation id: gen-1788434896-Fz1TXXpnXADOdzhKdMs1
