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
node --test
```

Los tests corren contra un `links.json` temporal (no tocan el archivo real
del repo).

## Qué hace cada archivo vivo

| Archivo | Qué hace |
|---|---|
| `server.js` | La app Express: endpoints de crear link y redirect, lee/escribe `links.json`. |
| `utils.js` | `generarCodigo()`, usado por `server.js` para generar el código corto. |
| `links.json` | Store de datos (array de links). No se trackea en git — ver `.gitignore`. |
| `public/index.html` | Página principal: formulario para acortar una URL. |
| `public/stats.html` | Página de estadísticas de un link (Milestone 4). |
| `public/estilos.css` | Estilos de ambas páginas. |
| `public/logo.png` | Logo mostrado en `index.html`. |
| `SPEC.md` | Contrato de comportamiento. Fuente de verdad para tests e implementación. |
| `test/` | Batería de tests derivada de `SPEC.md` (ver tabla abajo). |
| `mission.md` | Consigna original de la misión. Se queda en el repo por decisión del equipo. |
| `notas.txt` | Notas del desarrollador anterior; tiene una credencial, por eso está en `.gitignore` y nunca se commitea. |
| `CLAUDE.md` / `AGENTS.md`/ `.github/copilot-instructions.md` | Contrato vivo para el agente de código: reglas, estado del proyecto, decisiones. |

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

Persistencia (§7 del SPEC, Milestone 5) todavía no tiene tests: es un test de
integración que va junto con la migración a Postgres.