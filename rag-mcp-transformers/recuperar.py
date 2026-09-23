"""Parte 1: corre el recuperador sobre un archivo de preguntas.

    python3 recuperar.py --preguntas datos/preguntas_recuperacion_dev.jsonl --salida resultados.jsonl

La configuración es la de config_rag.json (ver SPEC.md).
"""
import argparse
import json
from pathlib import Path

from recuperador import Recuperador


def procesar(preguntas, salida, recuperador):
    filas = []
    for linea in Path(preguntas).read_text(encoding="utf-8").splitlines():
        if linea.strip():
            p = json.loads(linea)
            filas.append({"id": p["id"], "fragmentos": recuperador.buscar(p["pregunta"])})
    Path(salida).write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in filas), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preguntas", required=True)
    ap.add_argument("--salida", required=True)
    args = ap.parse_args()
    procesar(args.preguntas, args.salida, Recuperador.desde_config())
