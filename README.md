# IaGenerativa

Repositorio del grupo para la materia **IA Generativa** (Austral, 2do cuatrimestre
2026). Una carpeta por misión; el tooling de equipo vive en la raíz.

## Misiones

| Carpeta | Misión | Clase | Estado |
|---|---|---|---|
| [`corta/`](corta/) | **Corta** — acortador de URLs, del caos a producción | 2 | Entregada (5 milestones, deployada en Railway) |
| [`prompting/`](prompting/) | **El prompt mínimo** — chat multi-modelo vía OpenRouter + Conway en 1 prompt | 5 | En curso |

Cada misión tiene su propio `README.md`, `SPEC.md`, `CLAUDE.md` y `mission.md`
(el enunciado original de la cátedra) dentro de su carpeta.

## Tooling de equipo (raíz)

| Ruta | Qué es |
|---|---|
| `CLAUDE.md` | Contrato de equipo: reglas comunes a todas las misiones. Cada misión suma las suyas en su propio `CLAUDE.md`. |
| `AGENTS.md` · `.github/copilot-instructions.md` | Redirigen a `CLAUDE.md`. Una sola fuente de verdad. |
| `.claude/skills/collect-memory/` | Skill `/collect-memory`: actualiza el contrato del agente al cerrar cada sesión. |
| `scripts/reporte-cambios.sh` · `scripts/com.corta.reporte-cambios.plist` | Tarea programada diaria de cada integrante (ver abajo). |
| `reportes/` | Reportes generados por esa tarea, uno por integrante y fecha. |

> **Nota sobre Railway.** El servicio de Corta buildea desde el repo; al mudar la
> app a `corta/` hay que dejar el *Root Directory* del servicio apuntando a
> `/corta`, o el próximo deploy falla por no encontrar `package.json`.

## Tarea programada de cada integrante

Cada integrante deja corriendo en **su propia máquina** una tarea que, todos los
días, actualiza su copia local desde el remote y genera un reporte de los cambios
del repositorio. El reporte lo redacta el agente, no un `git log` pelado: sale en
`reportes/<usuario>/<fecha>.md` con los commits nuevos, quién los hizo, qué
archivos tocaron y un resumen en lenguaje llano.

### Antes de configurarla

- **Tener `git config user.name` y `user.email` bien puestos.** El nombre de la
  subcarpeta del reporte sale de ahí: si están vacíos, tus reportes terminan en
  `reportes/root/` y tus commits quedan sin autor real (ya nos pasó una vez, en
  el commit `9a0eecb`).
- **Tener tu agente instalado y logueado** (ver abajo: no hace falta que sea
  Claude Code).

### Cada uno con su agente

La consigna pide que cada integrante use *su* agente, y en el equipo no todos
usamos el mismo. La variable `AGENTE` elige cuál redacta el reporte:

| `AGENTE=` | Qué usa | Estado |
|---|---|---|
| `auto` (default) | El primero que encuentre instalado; si no hay ninguno, cae a `git` | probado |
| `claude` | Claude Code headless (`claude -p`) | probado |
| `codex` | Codex CLI headless (`codex exec`) | ⚠️ **flags sin verificar** |
| `git` | Sin agente: el reporte lo arma `git` | probado |

Para cualquier otro agente, sin tocar el script:

```bash
AGENTE_CMD="mi-cli --flags" ./scripts/reporte-cambios.sh
```

El prompt le llega como único argumento posicional. En el plist se setea con un
bloque `EnvironmentVariables`.

⚠️ **El adaptador de Codex no está probado**: cuando se escribió esto, nadie del
equipo tenía Codex instalado. El primero que lo use, confirmá los flags contra
`codex exec --help` y corregí esa línea del script.

El modo `git` es la red de seguridad: produce el mismo reporte de commits,
autores y archivos, pero sin el resumen en prosa. Sirve si tu agente no anda o
no querés gastar llamadas al modelo. Además, si el agente falla en el momento,
el script cae solo a este modo antes que quedarse sin reportar.

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

