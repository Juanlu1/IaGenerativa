"""Prueba el RAG con normas original/b/c usando el set de desarrollo.

Las consultas de desarrollo incluyen evidencias numéricas de `original`. Para
probar b/c, este script sustituye solo esos valores por los de cada carpeta;
no escribe ni altera los archivos oficiales.
"""

import argparse
import copy
import json
from pathlib import Path

from admision.evaluar_rag import cargar_dataset, evaluar_buscador
from admision.normas import cargar_parametros
from rag_buscador import construir_buscador


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normas", type=Path, required=True,
                    help="Carpeta que contiene original/, b/ y c/")
    ap.add_argument("--consultas", type=Path, required=True)
    args = ap.parse_args()
    original = cargar_dataset(args.consultas)
    parametros_originales = cargar_parametros(args.normas / "original")

    for version in ("original", "b", "c"):
        parametros = cargar_parametros(args.normas / version)
        dataset = copy.deepcopy(original)
        for item in dataset:
            for evidencia in item["evidencia"]:
                for codigo, valor_original in parametros_originales.items():
                    evidencia["texto"] = evidencia["texto"].replace(
                        f"{codigo} = {valor_original}", f"{codigo} = {parametros[codigo]}")
        buscador = construir_buscador(args.normas / version)
        resultado = {"version": version, **evaluar_buscador(buscador, dataset)}
        print(json.dumps(resultado, ensure_ascii=False))


if __name__ == "__main__":
    main()
