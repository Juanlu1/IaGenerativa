#!/usr/bin/env bash
#
# Tarea programada del extra "trabajo en equipo" (ver mission.md).
#
# Hace las dos cosas que pide la consigna:
#   1. actualiza la copia local del repositorio desde el remote, y
#   2. genera un reporte de los cambios del repositorio (que commits nuevos
#      entraron, de quien, que archivos tocaron).
#
# El paso 1 lo hace este script de forma deterministica; el reporte del paso 2
# lo redacta el agente (claude -p) con los datos ya recolectados.
#
# Cada integrante apunta su propio cron a este mismo script: el reporte se
# guarda en reportes/<su-usuario>/<fecha>.md, asi dos personas que corren la
# tarea el mismo dia no se pisan el archivo.
#
# Si no entraron commits nuevos no genera reporte ni commitea: el log alcanza
# como evidencia de que la tarea corrio.
#
# Uso:
#   ./scripts/reporte-cambios.sh              # actualiza, reporta y commitea local
#   PUSH=1 ./scripts/reporte-cambios.sh       # ademas pushea el reporte al remote
#   COMMIT=0 ./scripts/reporte-cambios.sh     # solo deja el archivo, sin commitear
#   FORCE_REPORTE=1 ./scripts/...             # genera el reporte aunque no haya
#                                             # commits nuevos (util para demos)

set -uo pipefail

# Por defecto opera sobre el repo que contiene a este script. Se puede apuntar a
# otro clon con REPO=/ruta/al/clon, que es como se testea sin tocar el repo real.
REPO="${REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$REPO" || exit 1

# cron arranca con un PATH minimo: git, node y claude no estan por defecto.
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
for dir in "$HOME"/.nvm/versions/node/*/bin; do
  [ -d "$dir" ] && export PATH="$dir:$PATH"
done

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

CLAUDE="$(command -v claude || true)"
if [ -z "$CLAUDE" ]; then
  log "ERROR: no encuentro el ejecutable 'claude' en el PATH. Aborto."
  exit 1
fi

AUTOR="$(git config user.name 2>/dev/null || echo "$USER")"
SLUG="$(echo "$AUTOR" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9' '-' | sed 's/-\{1,\}/-/g; s/^-//; s/-$//')"
FECHA="$(date +%F)"
DEST="reportes/${SLUG}/${FECHA}.md"

# --- Paso 1: actualizar la copia local ---------------------------------------

ANTES="$(git rev-parse HEAD)"
RAMA="$(git rev-parse --abbrev-ref HEAD)"
log "Repo: $REPO (rama $RAMA, HEAD $(git rev-parse --short HEAD))"

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  log "AVISO: hay cambios sin commitear. Actualizo igual, pero el pull puede fallar."
fi

log "Actualizando desde origin..."
git fetch origin --prune 2>&1 | sed 's/^/  /'

if ! git merge --ff-only "origin/${RAMA}" 2>&1 | sed 's/^/  /'; then
  log "ERROR: no se pudo hacer fast-forward a origin/${RAMA}."
  log "Causas tipicas: la rama local divergio del remote (resolvelo con"
  log "'git pull --rebase'), o hay archivos sin trackear que el merge pisaria"
  log "(movelos o borralos). Mira el detalle de git arriba y volve a correr."
  exit 1
fi

DESPUES="$(git rev-parse HEAD)"
RANGO="${ANTES}..${DESPUES}"

if [ "$ANTES" = "$DESPUES" ]; then
  log "Sin commits nuevos desde la ultima corrida."
  NUEVOS=0
else
  NUEVOS="$(git rev-list --count "$RANGO")"
  log "Entraron $NUEVOS commit(s) nuevos: $RANGO"
fi

# --- Paso 2: el agente redacta el reporte ------------------------------------

# Sin commits nuevos no hay nada que reportar: la evidencia de que la tarea
# corrio es este log (mas 'runs' en launchctl). Escribir igual un archivo
# "sin cambios" y commitearlo dejaria un commit de ruido por dia y por
# integrante: cuatro personas, ~120 commits vacios por mes tapando la historia
# real. De paso, los dias sin actividad no invocan al modelo.
if [ "$NUEVOS" -eq 0 ] && [ "${FORCE_REPORTE:-0}" != "1" ]; then
  log "Nada que reportar. (Usa FORCE_REPORTE=1 si igual querés el archivo.)"
  log "Listo."
  exit 0
fi

mkdir -p "$(dirname "$DEST")"

if [ "$NUEVOS" -eq 0 ]; then
  PROMPT="Sos el agente de la tarea programada del repositorio Corta (un acortador de URLs).
Acabo de actualizar la copia local desde origin y NO entraron commits nuevos desde la corrida anterior.
HEAD sigue en ${DESPUES}.

Escribi un reporte breve en el archivo ${DEST} (usa la herramienta Write). Formato Markdown:
un titulo con la fecha ${FECHA}, y una linea diciendo que no hubo cambios nuevos en el
repositorio, indicando en que commit quedo HEAD (hash corto y mensaje, obtenelo con git log -1).
No modifiques ningun otro archivo. No hagas commit ni push: de eso me encargo yo."
else
  PROMPT="Sos el agente de la tarea programada del repositorio Corta (un acortador de URLs).
Acabo de actualizar la copia local desde origin y entraron ${NUEVOS} commit(s) nuevos.
El rango de commits nuevos es ${RANGO}.

Investiga ese rango con git (por ejemplo: git log ${RANGO} --stat, git show --stat <hash>)
y escribi un reporte en el archivo ${DEST} (usa la herramienta Write). Formato Markdown:

1. Un titulo con la fecha ${FECHA} y el rango de commits en hashes cortos.
2. Una tabla con una fila por commit nuevo: hash corto, autor, fecha y mensaje.
3. Por cada commit, los archivos que toco con las lineas agregadas/eliminadas.
4. Un cierre de 2 o 3 frases explicando en lenguaje llano que cambio en conjunto
   en el repositorio y si algo merece atencion del equipo.

Escribi en espaniol rioplatense. No inventes datos: todo sale de git.
No modifiques ningun otro archivo. No hagas commit ni push: de eso me encargo yo."
fi

log "Pidiendole el reporte al agente..."
"$CLAUDE" -p "$PROMPT" \
  --permission-mode acceptEdits \
  --allowedTools "Bash(git:*)" "Read" "Write" "Glob" "Grep" \
  2>&1 | sed 's/^/  /'

if [ ! -f "$DEST" ]; then
  log "ERROR: el agente no genero $DEST."
  exit 1
fi
log "Reporte generado: $DEST"

# --- Paso 3: dejarlo registrado ----------------------------------------------

if [ "${COMMIT:-1}" = "1" ] && [ "$NUEVOS" -gt 0 ]; then
  git add "$DEST"
  if git diff --cached --quiet; then
    log "El reporte no cambio respecto del ultimo commit, no hay nada que commitear."
  else
    git commit -m "chore(reporte): cambios del repositorio al ${FECHA}" \
      --only "$DEST" 2>&1 | sed 's/^/  /'
    log "Reporte commiteado."
  fi

  # El push queda opt-in a proposito: una tarea automatica que pushea sola a una
  # rama compartida es una sorpresa desagradable para el resto del equipo.
  if [ "${PUSH:-0}" = "1" ]; then
    log "Pusheando a origin/${RAMA}..."
    git push origin "$RAMA" 2>&1 | sed 's/^/  /'
  fi
elif [ "$NUEVOS" -eq 0 ]; then
  log "Reporte forzado sin commits nuevos: lo dejo sin commitear."
fi

log "Listo."
