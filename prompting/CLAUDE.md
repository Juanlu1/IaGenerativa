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

## Decisiones tomadas

<!-- Sección mantenida por /collect-memory. Actualizar al cerrar cada sesión. -->

- Reorganización del repo en carpetas por misión (`corta/`, `prompting/`); el
  tooling de equipo quedó en la raíz.
- La cuenta de OpenRouter es **una sola por grupo**: el ejercicio 3 contrasta los
  números contra el dashboard de actividad, y con cuentas separadas no cierra.

## Estado del proyecto

- **Antes de todo** (router, mapa de modelos, parámetros): pendiente.
- **Ejercicio 1** (interfaz + logs de prueba por modelo): pendiente.
- **Ejercicio 2** (`vida.py` en 1 prompt): pendiente — depende del ej 1.
- **Ejercicio 3** (informe): pendiente — depende del ej 2.
