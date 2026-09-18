# CLAUDE.md — Misión "El prompt mínimo"

Instrucciones para el agente que trabaja en **esta carpeta** (`prompting/`).
Las reglas comunes al repo están en el [`CLAUDE.md` de la raíz](../CLAUDE.md).
El contrato de lo que se construye está en [`SPEC.md`](SPEC.md); el enunciado
original de la cátedra, en [`mission.md`](mission.md).

## Reglas propias de esta misión

1. **`test_vida.py` no se toca.** Es de la cátedra y se entrega tal cual llegó.
   Si algo falla, se arregla `vida.py` — y `vida.py` solo se arregla
   **reescribiendo el prompt**, nunca a mano.
2. **`vida.py` es output del modelo, no nuestro.** Se pega tal cual sale del
   chat. Un solo archivo, solo biblioteca estándar. Cualquier edición manual
   invalida la corrida.
3. **Todo intento queda logueado.** El log `.md` se escribe solo, desde la
   interfaz. Los intentos quemados **también se commitean**: son la evidencia
   que respalda el informe del ejercicio 3. Borrar un log quemado es borrar la
   nota.
4. **La key nunca entra al repo.** Se lee de `OPENROUTER_API_KEY` (ver
   `.env.example`). Tampoco va en los logs: si la interfaz vuelca el request
   completo, hay que enmascararla antes de escribir el `.md`.
5. **El usage no se transcribe a mano.** Lo que va al log y al informe sale del
   objeto `usage` de la respuesta, tal cual lo devuelve OpenRouter.

## Hallazgos verificados contra la API (2026-09-02)

Todo esto se comprobo con llamadas reales, no sale de la documentacion. Condiciona
como se escribe la interfaz del ejercicio 1 y que numeros van al informe.

1. **La cuenta de OpenRouter es del curso, no del grupo.** `GET /api/v1/credits`
   devuelve el consumo de *todos* (25 creditos totales, 14.35 gastados por otros).
   Contra eso el informe no puede cerrar.
2. **Nuestra key tiene limite propio de USD 1** y su `usage` es solo nuestro:
   `GET /api/v1/key` -> `usage`, `limit`, `limit_remaining`. Ese es el numero
   auditable del ejercicio 3, y reemplaza al dashboard de actividad (al que no
   tenemos acceso: los profes dieron la key, no la cuenta). Se toma la lectura
   **antes y despues** de cada corrida y la diferencia es el gasto de esa corrida.
3. **Los 4 IDs del enunciado existen y estan vigentes.** El slot 4 sale 15.4x mas
   barato que el slot 2 en tokens de entrada ($0.065/M vs $1.00/M), que es
   exactamente la comparacion que pide el enunciado.
4. **`cache_discount` no siempre viene.** Sin evento de cache el campo esta
   ausente, no en cero. La interfaz tiene que tolerar campos faltantes o revienta
   con KeyError en la primera respuesta. Lo mismo vale para `reasoning_tokens`.
5. **DeepSeek si devuelve los tokens de pensamiento**: `reasoning_tokens` llego
   con valor (23 en la prueba). No sufrimos el problema que el enunciado advierte
   para la serie o de OpenAI.
6. **`GET /api/v1/generation?id=<id>` tarda en estar disponible**: a los 4 segundos
   da 404, a los 15 responde. Si la interfaz lo consulta, tiene que reintentar; no
   sirve pedirlo inmediatamente despues de la respuesta.
7. **Hay dos conteos de tokens distintos y no dan igual.** En la misma llamada:
   `tokens_prompt` = 12 (normalizado) contra `native_tokens_prompt` = 18 (el real
   del proveedor, que es el que se factura). Al informe van los **native**; mezclar
   los dos hace que las cuentas no cierren.
8. **Omitir `reasoning` no apaga el razonamiento.** DeepSeek razona por defecto:
   la misma pregunta sin el parametro devolvio 30 tokens de razonamiento, y con
   `reasoning: {"enabled": false}` devolvio 0 y costo la mitad. Para comparar
   precios entre modelos hay que apagarlo explicitamente, o se compara el largo
   de la respuesta en vez de la tarifa.
9. **La respuesta trae `cost_details`** ademas de `cost`, con el desglose de entrada
   y salida por separado. Sirve para la tabla del ejercicio 3.

## Decisiones tomadas

<!-- Sección mantenida por /collect-memory. Actualizar al cerrar cada sesión. -->

- Reorganización del repo en carpetas por misión (`corta/`, `prompting/`); el
  tooling de equipo quedó en la raíz.
- La contabilidad del ejercicio 3 sale del `usage` de nuestra key, no del dashboard
  de la cuenta: la cuenta es compartida con todo el curso (ver hallazgos 1 y 2).
  En el informe se verificó por `generation id` y se explicitó por qué no hay
  contraste contra el dashboard.
- Las respuestas de "Antes de todo" van como primera sección de `INFORME.md`, no en
  un archivo aparte: la rúbrica las evalúa como parte del informe (sin ellas el
  ejercicio 3 tiene tope de 15/20).
- Se borraron los logs vacíos (solo encabezado, sin turnos) que la interfaz crea al
  cambiar de modelo: no son intentos, y uno en `logs/conway/` hacía que los logs
  contaran 3 intentos contra 2 del informe.
- Intento ganador de Conway = `logs/conway/2026-09-17-160135-slot4.md` (su código es
  idéntico a `vida.py`); el intento 2 es `2026-09-17-142741-slot4.md`. Los nombres
  mezclan hora UTC y local; el orden real lo dan los `generation id`, y está
  explicado en el informe para que no parezca edición posterior.
- `.env.example` se había borrado por accidente en el commit de `vida.py`
  (`c367fdf`); se restauró con su contenido original.
- La conclusión del informe nombra decisiones concretas (`reasoning.effort: "low"`,
  pedir solo el código), porque "mantener todo" no puntúa en la rúbrica.

## Convenciones del equipo

<!-- Sección mantenida por /collect-memory. Actualizar al cerrar cada sesión. -->

- El agente **no hace commits ni push**: deja los cambios en el working tree y el
  equipo commitea.
- Al editar entregables ya escritos (como `INFORME.md`), cambiar solo lo necesario
  y conservar el texto del equipo; no reescribir el documento entero.

## Estado del proyecto

- **Paso 0** (repo organizado, key verificada, 4 modelos confirmados): HECHO.
- **Antes de todo** (router, mapa de modelos, parámetros): HECHO — en `INFORME.md`.
  DeepSeek y Kimi no figuran en el board de frontera (top 5).
- **Ejercicio 1** (interfaz + logs de prueba por modelo + demos): HECHO.
- **Ejercicio 2** (`vida.py` en 1 prompt): HECHO — 1 prompt, 9/9 tests, cache hit en
  el intento 2.
- **Ejercicio 3** (informe): HECHO salvo un `[COMPLETAR]`: la lectura de `usage` de
  `GET /api/v1/key` antes/después (anotarla o borrar el corchete si no se tomó).
- **Pendiente**: commitear los cambios de esta sesión (`.env.example`, borrado de
  logs vacíos, `INFORME.md`, `CLAUDE.md`). Los tests unitarios de la interfaz no se
  corrieron en esta máquina (no hay `.venv`); no los exige la entrega.
