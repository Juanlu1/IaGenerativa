#!/usr/bin/env bash
# Corre los casos de practica con las normas original, b y c y guarda cada corrida en corridas/<etiqueta>/<version>/.
#
#   ./evaluar_todo.sh <etiqueta> [cantidad_casos]
#
# - Usa la configuracion de CONFIG (por defecto config.yaml), igual que entrega.py.
# - Copia el yaml y el prompt usados a corridas/<etiqueta>/, y anota el commit y la fecha en corridas/<etiqueta>/corrida.txt.
# - Con cantidad_casos corre solo los primeros N casos de practica/casos.jsonl (para pruebas chicas).
# - MODELO_FALSO=1 corre con el guion fijo de entrega.py, sin GPU.
# - Si una version falla sigue con las demas y al final sale con error.
set -uo pipefail

cd "$(dirname "$0")"

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "uso: $0 <etiqueta> [cantidad_casos]" >&2
    exit 2
fi
etiqueta=$1
cantidad=${2:-}
if [[ ! $etiqueta =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "la etiqueta solo puede tener letras, numeros, punto, guion y guion bajo" >&2
    exit 2
fi
if [[ -n $cantidad && ! $cantidad =~ ^[1-9][0-9]*$ ]]; then
    echo "cantidad_casos tiene que ser un entero positivo" >&2
    exit 2
fi

destino=corridas/$etiqueta
mkdir -p "$destino"

# El yaml y el prompt que usa entrega.py, resueltos con su misma logica.
read -r ruta_config ruta_prompt < <(uv run python -c \
    "import entrega; c = entrega.cargar_config(); print(c['_ruta'], entrega.ruta_prompt(c))") || exit 1
cp "$ruta_config" "$ruta_prompt" "$destino"/

casos=practica/casos.jsonl
temporal=
if [[ -n $cantidad ]]; then
    temporal=$(mktemp -d)
    trap 'rm -rf "$temporal"' EXIT
    head -n "$cantidad" practica/casos.jsonl > "$temporal/casos.jsonl"
    casos=$temporal/casos.jsonl
fi

{
    echo "etiqueta: $etiqueta"
    echo "fecha: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "commit: $(git rev-parse HEAD)$(git diff --quiet HEAD -- . || echo ' (con cambios sin commitear)')"
    echo "config: $(basename "$ruta_config")"
    echo "prompt: $(basename "$ruta_prompt")"
    echo "casos: $(wc -l < "$casos" | tr -d ' ') de practica/casos.jsonl"
    echo "modelo_falso: ${MODELO_FALSO:-0}"
} > "$destino/corrida.txt"

fallas=0
for version in original b c; do
    salida=$destino/$version
    mkdir -p "$salida"
    echo "=== $etiqueta / $version ($(date +%H:%M:%S))"
    if ! uv run python -m admision.correr practica --entrega entrega.py --casos "$casos" \
            --esperadas "practica/esperadas-$version.jsonl" --normas "normas/$version" \
            --salida "$salida" 2>&1 | tee "$salida/correr.log"; then
        echo "!!! fallo $etiqueta / $version (ver $salida/correr.log)" >&2
        fallas=$((fallas + 1))
    fi
done

uv run python tabla.py || fallas=$((fallas + 1))
exit $((fallas > 0))
