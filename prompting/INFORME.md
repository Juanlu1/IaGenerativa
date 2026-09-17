# Ejercicio 3 — La cuenta final

## Intentos del Ejercicio 2

Para generar `vida.py` se utilizó el modelo `deepseek/deepseek-v4-flash-0731` con razonamiento activado.

| Intento | Prompts | Tokens de entrada | Tokens de salida | Tokens de razonamiento | Tokens cacheados | Costo | Resultado |
|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | 1223 | 818 | 310 | 0 | USD 0.000172 | Generó el `vida.py` utilizado en la entrega y pasó los 9 tests |
| 2 | 1 | 1223 | 935 | 317 | 1223 | USD 0.000134 | Se repitió el mismo prompt para verificar el prompt caching obligatorio; se registró un cache hit de 1223 tokens |

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

## Conclusión

Mantendríamos el prompt completo porque permitió obtener una solución correcta en un solo mensaje y pasar los 9 tests sin correcciones posteriores.

Para reducir el costo, conservaríamos el mismo prefijo estático entre intentos para aprovechar el prompt caching, que en la segunda ejecución permitió reutilizar los 1223 tokens de entrada y reducir el costo de la generación.

También mantendríamos `deepseek/deepseek-v4-flash-0731`, ya que resolvió correctamente el problema con un costo total muy bajo.