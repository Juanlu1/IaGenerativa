# CLAUDE.md — Corta
Instrucciones para el agente de código que trabaja en este repositorio.
Este archivo es el **contrato vivo** del proyecto: reglas, estado y decisiones.
Se mantiene con la skill `/collect-memory` al cerrar cada sesión de trabajo.

## Qué es Corta

Acortador de URLs interno, heredado, sin documentación original. Objetivo de la
misión: llevarlo del estado "carpeta copiada de la compu del dev anterior" a
producción, con historia completa en GitHub (del caos del primer commit al
deploy).

## Fuente de verdad

- `SPEC.md` (en la raíz) es el **contrato de comportamiento**. Arbitra qué es
  correcto y qué es un bug. Ante conflicto entre el código actual y `SPEC.md`,
  manda `SPEC.md`.
- Los tests se derivan de `SPEC.md`, **no** del comportamiento observado del
  código heredado. El código heredado tiene bugs conocidos; documentar lo que
  hace hoy sería canonizar esos bugs como si fueran features.
- El `SPEC.md` se escribe temprano (con lo que se va descubriendo) y se
  actualiza cuando cambia el entendimiento.

## Reglas de TDD (obligatorias y verificables)

1. Ningún cambio de comportamiento entra sin un test previo que lo cubra.
2. Orden de commits por cada feature o bug fix: **primero** el/los test en rojo
   (commit separado), **después** la implementación que los pone en verde
   (commit separado). La historia de git debe mostrar el test *antes* que la
   implementación que lo hace pasar.
3. Los tests se escriben **feature por feature**, no en un solo bloque, para
   preservar la secuencia rojo→verde en la historia de git.
4. Cada test referencia la sección de `SPEC.md` que lo justifica.
5. En cada milestone, la suite completa corre **verde** antes de dar el
   milestone por cerrado.
6. El usuario revisa los tests antes de aceptarlos, aunque los haya generado el agente.

## Infraestructura

- Railway es la capa de **producción** (deploy, provisión de base de datos,
  logs). Se opera por el Railway MCP.
- Los tests corren **localmente** contra una base de test, nunca contra Railway.
- **Secretos** (credenciales de DB, tokens): viven en variables de entorno.
  Nunca en el código, nunca en `.mcp.json` commiteado, nunca en un `.txt`.
  En `.mcp.json` se usa expansión de variables de entorno para no commitear el
  PAT ni otros tokens. Nunca se commitean ni se pushean.

## Estado del proyecto

<!-- Sección mantenida por /collect-memory. Actualizar al cerrar cada sesión. -->

- **Milestone 1** (trackear desde el principio): HECHO.
- **Milestone 2**: PENDIENTE.
- **Milestone 3**: HECHO. Se aplicaron correcciones en `server.js` (validación de URL, deduplicación por URL exacta, reintento ante colisiones de código, persistencia robusta de `links.json`, incremento y persistencia de `clicks`, servir estáticos relativo a `__dirname`, usar PORT desde env). Tests locales: 14 passed, 2 fallos (ver abajo).
- **Milestone 4**: PENDIENTE (endpoint de estadísticas `/api/links/:codigo/stats` no implementado; 2 tests fallaron por esto).
- **Milestone 5**: PENDIENTE (migración a Postgres / persistencia durable no realizada).

<!-- Fin sección Estado del proyecto -->

## Decisiones tomadas

<!-- Sección mantenida por /collect-memory. Formato por entrada: qué se decidió y por qué. -->

- Se decidió validar estrictamente la entrada `url` en POST /api/links: aceptar solo strings que parseen con `new URL()` y tengan esquema `http` o `https`. Motivo: evitar acortadores de esquemas peligrosos (ej. `javascript:`) y cumplir SPEC.md §3.
- Se decidió deduplicar por URL exacta: si la URL enviada ya existe exactamente en el store, devolver el mismo `codigo` y no crear duplicados. Motivo: cumplir la invarianta de deduplicación de SPEC §3.
- Se decidió implementar reintentos en la generación de `codigo` hasta encontrar uno no usado (límite 1000 intentos). Motivo: garantizar unicidad de códigos ante colisiones del generador (SPEC §3).
- Se decidió incrementar y persistir `clicks` en el mismo request de redirect y usar `res.redirect(302, url)` para asegurar Location header. Motivo: cumplir SPEC §4 y la invariante de estadísticas (SPEC §6).
- Se decidió servir archivos estáticos relativo a `__dirname` y manejar `links.json` ausente o corrupto devolviendo un store vacío, además de crear el directorio si hace falta al escribir. Motivo: robustez de arranque y compatibilidad con entornos donde el cwd no es la raíz del repo (SPEC §8).
- Se decidió no implementar en esta sesión el endpoint de estadísticas (`/api/links/:codigo/stats`) por petición del usuario; queda para Milestone 4.
- Se instaló Node/npm en el entorno temporal para ejecutar los tests locales y validar los cambios; se generó un commit con el trailer Co-authored-by solicitado por el usuario.

<!-- Fin sección Decisiones tomadas -->

## Convenciones del equipo

<!-- Sección mantenida por /collect-memory: formato de commits, naming, reglas y gustos del equipo. -->

- Convención de commits para cambios de memoria de sesión: usar prefijo `docs(memory):` en el mensaje. Ejemplo: `docs(memory): actualizar CLAUDE.md con avances y decisiones de la sesión`.

<!-- Fin sección Convenciones del equipo -->