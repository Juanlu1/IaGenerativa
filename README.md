# Corta

Acortador de URLs interno. Recibe una URL larga, genera un código corto de 3
caracteres, y redirige del código al destino contando clicks.

El comportamiento completo y los casos borde están definidos en
[`SPEC.md`](SPEC.md) — ante cualquier duda, ese archivo manda.

## Cómo correrlo

```bash
npm install
npm start
```

La app escucha en `http://localhost:3000`. Abrí esa URL para acortar un link;
`/stats.html` deja consultar las estadísticas de un código.

## Cómo correr los tests

```bash
npm test
```

Los tests corren contra un `links.json` temporal (no tocan el archivo real
del repo).


## Produccion (Milestone 5)

La aplicacion esta desplegada en Railway y usa PostgreSQL persistente para produccion.

- URL publica: https://corta-production-41e3.up.railway.app
- DATABASE_URL se configura mediante una variable de entorno de Railway.
- No se guardan secretos en el codigo ni en el repositorio.
- Se verifico manualmente que los links y sus clicks sobreviven a un redeploy.

## Tarea programada de cada integrante

Cada integrante deja corriendo en **su propia máquina** una tarea que, todos los
días, actualiza su copia local desde el remote y genera un reporte de los cambios
del repositorio. El reporte lo redacta el agente, no un `git log` pelado: sale en
`reportes/<usuario>/<fecha>.md` con los commits nuevos, quién los hizo, qué
archivos tocaron y un resumen en lenguaje llano.

### Antes de configurarla

Dos requisitos que no dan error obvio si faltan:

- **Tener `claude` instalado y logueado** en esa máquina. Si no, la tarea muere
  con `ERROR: no encuentro el ejecutable 'claude' en el PATH`.
- **Tener `git config user.name` y `user.email` bien puestos.** El nombre de la
  subcarpeta del reporte sale de ahí: si están vacíos, tus reportes terminan en
  `reportes/root/` y tus commits quedan sin autor real (ya nos pasó una vez, en
  el commit `9a0eecb`).

### El script

El script es el mismo para todos — `scripts/reporte-cambios.sh` — y se puede
correr a mano para probarlo:

```bash
./scripts/reporte-cambios.sh               # actualiza, reporta y commitea local
COMMIT=0 ./scripts/reporte-cambios.sh      # solo genera el archivo, sin commitear
PUSH=1 ./scripts/reporte-cambios.sh        # además pushea el reporte al remote
FORCE_REPORTE=1 ./scripts/reporte-cambios.sh  # reporte aunque no haya commits nuevos
```

Si no entraron commits nuevos, la tarea **no genera reporte ni commitea**: la
evidencia de que corrió es el log. Un archivo "sin cambios" commiteado por día y
por integrante serían ~120 commits vacíos por mes tapando la historia real.

### Programarla (macOS)

Usamos un **LaunchAgent** en vez de `cron`, porque `crontab` necesita que le des
Full Disk Access a la terminal desde Ajustes del Sistema y `launchd` no:

```bash
cp scripts/com.corta.reporte-cambios.plist ~/Library/LaunchAgents/
# editá las rutas del plist para que apunten a tu clon del repo
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.corta.reporte-cambios.plist
launchctl kickstart -p gui/$(id -u)/com.corta.reporte-cambios   # dispararlo ahora
```

Disparala a mano con `kickstart` apenas la configures, en vez de esperar a las 9
del día siguiente: el LaunchAgent corre con un PATH distinto al de tu terminal, y
así te enterás en el momento si no encuentra `claude`. Que el script ande cuando
lo corrés vos no prueba que launchd lo dispare bien.

Los logs de cada corrida quedan en `~/Library/Logs/corta-reporte.log`. En Linux
alcanza con una línea de `crontab -e`:
`0 9 * * * /ruta/al/repo/scripts/reporte-cambios.sh >> ~/corta-reporte.log 2>&1`

## Qué hace cada archivo vivo

| Archivo | Qué hace |
|---|---|
| `server.js` | La app Express: endpoints de crear link, redirect y estadísticas. Delega el guardado en `storage.js`. |
| `storage.js` | Capa de persistencia: usa PostgreSQL si hay `DATABASE_URL` (producción) y `links.json` si no (local). Acá viven la deduplicación por URL, el reintento ante colisión de código y el conteo de clicks. |
| `utils.js` | `generarCodigo()`, usado por `server.js` para generar el código corto. |
| `links.json` | Store de datos (array de links). No se trackea en git — ver `.gitignore`. |
| `public/index.html` | Página principal: formulario para acortar una URL. |
| `public/stats.html` | Página de estadísticas: consulta `GET /api/links/:codigo/stats` y muestra los datos reales. |
| `public/estilos.css` | Estilos de ambas páginas. |
| `public/logo.png` | Logo mostrado en `index.html`. |
| `SPEC.md` | Contrato de comportamiento. Fuente de verdad para tests e implementación. |
| `test/` | Batería de tests derivada de `SPEC.md` (ver tabla abajo). |
| `scripts/reporte-cambios.sh` | Tarea programada del extra de equipo: actualiza la copia local y le pide al agente el reporte de cambios. |
| `scripts/com.corta.reporte-cambios.plist` | Plantilla de LaunchAgent (macOS) para disparar esa tarea todos los días. |
| `reportes/` | Reportes de cambios generados por la tarea programada, uno por integrante y fecha. |
| `mission.md` | Consigna original de la misión. Se queda en el repo por decisión del equipo. |
| `notas.txt` | Notas del desarrollador anterior; tiene una credencial, por eso está en `.gitignore` y nunca se commitea. |
| `CLAUDE.md` / `AGENTS.md`/ `.github/copilot-instructions.md` | Contrato vivo para el agente de código: reglas, estado del proyecto, decisiones. |
| `.claude/skills/collect-memory/SKILL.md` | Skill `/collect-memory`: actualiza el contrato del agente al cerrar cada sesión. |
| `package.json` / `package-lock.json` | Dependencias (`express` en runtime, `supertest` para tests) y scripts `start` / `test`. |
| `.gitignore` | Qué no viaja al remoto: `node_modules`, el store `links.json`, `notas.txt` (credencial), `.env`, `.DS_Store`. |

## Tests → feature → milestone

El milestone lo fija la feature (la sección de `SPEC.md`), no si el test ya pasa.
La última columna indica si el test nace en verde (ya cumple hoy) o en rojo
(comportamiento pendiente de implementar).

| Test | Sección de SPEC.md | Milestone | Estado inicial |
|---|---|---|---|
| `SPEC 3: crear con URL valida devuelve 200 con {codigo, corta} y persiste` | §3 Crear link | 3 | 🟢 verde |
| `SPEC 3: URL vacia se rechaza con 400 y no crea nada` | §3 Crear link | 3 | 🟢 verde |
| `SPEC 3: un string que no es URL se rechaza con 400` | §3 Crear link (validación) | 3 | 🔴 rojo |
| `SPEC 3: un numero como url se rechaza con 400` | §3 Crear link (validación) | 3 | 🔴 rojo |
| `SPEC 3: un esquema no http/https (javascript:) se rechaza con 400` | §3 Crear link (validación) | 3 | 🔴 rojo |
| `SPEC 3: misma url exacta dos veces devuelve el mismo codigo y no duplica` | §3 Crear link (dedup) | 3 | 🔴 rojo |
| `SPEC 3: URL que difiere en un caracter recibe codigo propio` | §3 Crear link (dedup) | 3 | 🟢 verde |
| `SPEC 3: unicidad - ante colision del generador, regenera y no comparte codigo` | §3 Crear link (unicidad) | 3 | 🔴 rojo |
| `SPEC 4: codigo existente redirige con 302 a la url` | §4 Redirect | 3 | 🔴 rojo |
| `SPEC 4 y 6: el redirect incrementa clicks en 1 y lo persiste` | §4 Redirect, §6 | 3 | 🔴 rojo |
| `SPEC 4: codigo inexistente devuelve 404 con { error: ... }` | §4 Redirect | 3 | 🔴 rojo |
| `SPEC 4 y 6: un GET a codigo inexistente no cuenta como click` | §4 Redirect, §6 | 3 | 🔴 rojo |
| `SPEC 4: la comparacion de codigo es sensible a mayusculas/minusculas` | §4 Redirect | 3 | 🟢 verde |
| `SPEC 5: codigo existente devuelve 200 con {clicks, url, creado}` | §5 Estadísticas | 4 | 🔴 rojo |
| `SPEC 5: codigo inexistente devuelve 404` | §5 Estadísticas | 4 | 🔴 rojo |
| `SPEC 5: consultar stats no incrementa clicks` | §5 Estadísticas, §6 | 4 | 🟢 verde |
| `SPEC 7: un link permanece disponible al crear una nueva instancia del almacenamiento` | §7 Persistencia | 5 | 🔴 rojo |
| `SPEC 7: los clicks permanecen al crear una nueva instancia del almacenamiento` | §7 Persistencia | 5 | 🔴 rojo |
| `SPEC 7: stats recupera los valores persistidos` | §7 Persistencia | 5 | 🔴 rojo |
| `SPEC 7: incrementar clicks no pierde incrementos concurrentes` | §7 Persistencia | 5 | 🔴 rojo |
| `SPEC 7 y SPEC 3: la deduplicacion por URL exacta se mantiene` | §7, §3 dedup | 5 | 🔴 rojo |
| `SPEC 7 y SPEC 3: codigo sigue siendo unico ante una colision` | §7, §3 unicidad | 5 | 🔴 rojo |

Los tests de persistencia (§7) corren contra un backend en memoria que simula una
base compartida entre instancias: prueban el contrato que `storage.js` tiene que
cumplir, sin depender de PostgreSQL ni de Railway.