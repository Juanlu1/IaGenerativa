#!/usr/bin/env bash
# Corre los casos de practica con las normas original, b y c en esta maquina y regenera corridas/tabla.md.
#
#   ./evaluar_todo.sh <etiqueta> [cantidad_casos]
#
# - Carga el modelo una sola vez y corre las tres versiones con el (ver evaluar.py).
# - Deja cada version en corridas/<etiqueta>/<version>/ y copia el yaml y el prompt usados a corridas/<etiqueta>/.
# - Usa la configuracion de CONFIG (por defecto config.yaml), igual que entrega.py.
# - Con cantidad_casos corre solo los primeros N casos de practica/casos.jsonl (para pruebas chicas).
# - En la Mac solo sirve con MODELO_FALSO=1 (sin GPU). Con el modelo de verdad se corre en Modal: ver MODAL.md.
set -uo pipefail

cd "$(dirname "$0")"

uv run python evaluar.py "$@"
estado=$?
if [[ $estado -eq 2 ]]; then
    exit 2  # argumentos invalidos
fi
uv run python tabla.py || estado=1
exit $((estado > 0))
