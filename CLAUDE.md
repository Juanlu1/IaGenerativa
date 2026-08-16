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
- **Milestone 2** (ordenar): HECHO. Archivos muertos y duplicados eliminados (`index_v2_FINAL.js`, `server_OLD.js`, `links_backup_marzo.json`, `public/estilos_viejos.css`, `test.js`), `public/logo (1).png` renombrado a `logo.png`, dependencias sin uso fuera de `package.json` (`lodash`, `moment`, `axios`), `links.json` sacado del tracking por ser store de datos, `README.md` con guía rápida y tabla de qué hace cada archivo vivo, `.gitignore` cubriendo `node_modules`, `notas.txt`, `links.json`, `.env` y `.DS_Store`. Script `npm test` cableado a `node --test`.
- **Milestone 3**: HECHO. Se aplicaron correcciones en `server.js` (validación de URL, deduplicación por URL exacta, reintento ante colisiones de código, persistencia robusta de `links.json`, incremento y persistencia de `clicks`, servir estáticos relativo a `__dirname`, usar PORT desde env).
- **Milestone 4** (completar lo que falta): HECHO. Endpoint `GET /api/links/:codigo/stats` implementado (200 con `{clicks, url, creado}`, 404 con `{error}` para código inexistente, no toca `clicks`), y `public/stats.html` conectada: consulta el endpoint y pinta los datos reales, con mensaje de error para código inexistente o fallo de red.
- **Milestone 5** (producción): HECHO (PR #1, `milestone-5-railway`). Se creó `storage.js`, una capa de persistencia intercambiable: usa PostgreSQL si hay `DATABASE_URL` y `links.json` si no. `server.js` bajó de 116 a 42 líneas porque la lógica de datos (dedup por URL, reintento ante colisión, clicks) se mudó ahí. Deployado en Railway: **https://corta-production-41e3.up.railway.app**.
- **Extra "trabajo en equipo"**: colaboradores HECHO — los 4 integrantes (`Juanlu1` admin, `MartinaCousido`, `juanchierasco`, `ana-castillo-zuain` con write) tienen commits propios en `main`. Tarea programada: HECHA la de `MartinaCousido`; **faltan las de los otros tres integrantes**, que deben configurarla en su propia máquina siguiendo el README.
- **Extra "memoria del agente"**: HECHO. La skill `/collect-memory` existe en `.claude/skills/` y se usa al cerrar sesión; la historia de git de `CLAUDE.md` muestra sus corridas.

**Auditoría del 2026-08-16** (sesión de verificación contra `mission.md`): los 5 milestones cumplen su criterio de éxito. Suite completa **22 passed, 0 failed**. Producción verificada punta a punta contra la URL real: acortar → 302 al destino → `clicks` pasa de 0 a 1; código inexistente 404; `javascript:` rechazado con 400. Sin secretos commiteados (`notas.txt`, que tiene una credencial, nunca entró a la historia).

Pendientes menores detectados en esa auditoría, no bloqueantes:

- `SPEC.md`: la sección "Estado verificado de produccion" quedó insertada entre §7 y §8 sin número, rompiendo la numeración que el resto del documento usa para referenciar tests.
- `server.js`: quedó un BOM UTF-8 al principio del archivo.
- No se verificó con un redeploy real que los links y clicks sobrevivan; el diseño lo garantiza (Postgres, cero estado en el filesystem) y el README dice que se probó a mano.

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
- Se decidió eliminar `axios` en lugar de dejarlo en `devDependencies`: su único consumidor era `test.js` (borrado en la limpieza del Milestone 2) y la batería nueva usa `supertest`. Motivo: el criterio del Milestone 2 pide que no queden dependencias que nadie usa.
- Se decidió cablear `npm test` a `node --test` en vez de documentar el comando suelto en el README. Motivo: quien clona el repo prueba `npm test` antes que cualquier otra cosa.
- Se decidió sumar `.env` y `.DS_Store` al `.gitignore` antes del Milestone 5. Motivo: los secretos de producción van a vivir en variables de entorno y no pueden filtrarse por un `.env` commiteado por descuido.
- Se decidió que el endpoint de estadísticas devuelva `clicks: link.clicks || 0`. Motivo: un link viejo del store heredado puede no tener el campo `clicks`; reportar `undefined` rompería el JSON y la página.
- Se decidió que `stats.html` arranque con el bloque de números oculto y lo muestre recién ante una consulta exitosa. Motivo: la maqueta original mostraba un `123` hardcodeado; dejar números visibles antes de consultar invita a leer datos que no corresponden a ningún link.
- El frontend de `stats.html` no tiene tests automatizados: la batería cubre el endpoint, no el DOM. Motivo: testear el DOM pediría jsdom y una capa de test nueva para una página de 40 líneas. La verificación fue manual, punta a punta. Si la página crece, revisar esta decisión.
- Se decidió que los tests de persistencia (SPEC §7) corran contra un backend en memoria que simula una base compartida entre instancias, en vez de contra PostgreSQL. Motivo: prueban el **contrato** que `storage.js` debe cumplir sin depender de Railway ni de una base levantada; la regla de infraestructura dice que los tests nunca corren contra Railway.
- Se decidió **descartar las routines cloud de `/schedule`** para la tarea programada del extra de equipo. Motivo: corren en infraestructura de Anthropic con su propio checkout, así que no cumplen ni "en su propia máquina" ni "actualiza su copia local", que la consigna pide textualmente.
- Se decidió programar la tarea con un **LaunchAgent de `launchd`** y no con `crontab`. Motivo: en macOS `crontab` falla con "Operation not permitted" salvo que se le dé Full Disk Access a la terminal desde Ajustes del Sistema; `launchd` es el mecanismo nativo y no lo necesita. El plist plantilla está en `scripts/`.
- Se decidió que el script haga el `fetch` + `merge --ff-only` de forma determinística y que el agente **solo redacte el reporte**. Motivo: actualizar la copia local es el requisito duro de la consigna y no puede depender de que el agente decida bien; el valor agregado del agente está en narrar los cambios, no en correr `git`.
- Se decidió guardar los reportes en `reportes/<usuario>/<fecha>.md`, con subcarpeta por integrante. Motivo: los cuatro corren la misma tarea; sin la subcarpeta, dos personas que reportan el mismo día se pisan el archivo.
- Se decidió que el push del reporte sea **opt-in** (`PUSH=1`) y que por defecto solo se commitee local. Motivo: una tarea automática que pushea sola todos los días a una rama compartida es una sorpresa desagradable para el resto del equipo.
- Se decidió **no reescribir la historia** para corregir el commit `9a0eecb` (Milestone 3), que quedó con autor `root <root@LAPTOP-61M7VSP0.>`. Motivo: ya está mergeado y pusheado, y reescribir historia compartida es más riesgoso que el beneficio cosmético; los 4 integrantes tienen commits propios igual, así que el criterio del extra se cumple. Mitigación: cada uno configura `git config --global user.name` y `user.email` en su máquina.

<!-- Fin sección Decisiones tomadas -->

## Convenciones del equipo

<!-- Sección mantenida por /collect-memory: formato de commits, naming, reglas y gustos del equipo. -->

- Convención de commits para cambios de memoria de sesión: usar prefijo `docs(memory):` en el mensaje. Ejemplo: `docs(memory): actualizar CLAUDE.md con avances y decisiones de la sesión`.
- **Los commits llevan únicamente el nombre de quien trabaja.** No se agrega el trailer `Co-Authored-By` de Claude ni de ninguna otra herramienta de IA, aunque el agente lo sugiera por defecto. Motivo: la autoría de la historia es del equipo.
- **Siempre `git pull` antes de `git push`.** Son cuatro personas sobre la misma rama `main`: pushear sin haber traído lo del remote primero es como se arma un conflicto evitable.
- **No pushear sin que el usuario lo pida explícitamente.** El agente commitea local y pregunta; el push a la rama compartida lo autoriza una persona.

<!-- Fin sección Convenciones del equipo -->