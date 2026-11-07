"""Compara granularidades usando el evaluador oficial del set de desarrollo."""

import argparse
import json
from pathlib import Path

from admision.evaluar_rag import cargar_dataset, evaluar_buscador, evaluar_recuperador
from rag_buscador import BuscadorNormas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normas", type=Path, required=True)
    ap.add_argument("--consultas", type=Path, required=True)
    a = ap.parse_args()
    dataset = cargar_dataset(a.consultas)
    for granularidad in ("apartado", "seccion", "hibrido2", "hibrido3"):
        buscador = BuscadorNormas(a.normas, granularidad)
        resultado = {"granularidad": granularidad,
                     "entorno": evaluar_buscador(buscador, dataset),
                     "presupuesto_512": evaluar_recuperador(buscador.recuperar, dataset, 512)}
        print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
