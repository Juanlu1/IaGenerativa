"""Muestra las consultas del set de desarrollo cuya evidencia no recupera el RAG."""

import argparse
import json
import re
from pathlib import Path

from rag_buscador import BuscadorNormas


def normalizar(texto):
    return re.sub(r"\s+", " ", texto).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normas", type=Path, required=True)
    ap.add_argument("--consultas", type=Path, required=True)
    ap.add_argument("--granularidad", choices=("apartado", "seccion", "hibrido2", "hibrido3"), default="seccion")
    a = ap.parse_args()
    buscador = BuscadorNormas(a.normas, a.granularidad)
    for linea in a.consultas.read_text(encoding="utf-8").splitlines():
        item = json.loads(linea)
        encontrados = buscador.recuperar(item["consulta"], buscador.k_entorno)
        faltantes = [e for e in item["evidencia"]
                     if not any(normalizar(e["texto"]) in normalizar(f.texto) for f in encontrados)]
        if faltantes:
            print(f"{item['id']} ({item['tipo']}): {item['consulta']}")
            print("  falta:", ", ".join(e["seccion"] for e in faltantes))
            print("  trajo:", ", ".join(f.seccion + " " + f.texto.splitlines()[1][:45] for f in encontrados))


if __name__ == "__main__":
    main()
