"""Valida la política que arma las fichas sintéticas contra las fichas esperadas de la práctica.

Juega los 50 casos de `practica/casos.jsonl` con la política de `generar_sinteticas.py`,
el entorno oficial y el buscador del grupo, con las normas original, b y c, y los
puntúa con el comparador oficial (`admision.comparar`): 9 controles por caso.

    uv run python validar_politica.py

Escribe el detalle en `datos/validacion_politica.json`. Las esperadas solo se leen
para puntuar; la política no las ve.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from admision.casos import cargar_casos, cargar_esperadas
from admision.comparar import comparar, resumir
from generar_sinteticas import ROOT, VERSIONES_NORMAS, cargar_parametros, jugar_caso
from parte2.rag_buscador import construir_buscador


def validar(version: str) -> tuple[dict, list[dict]]:
    casos = cargar_casos(ROOT / "practica" / "casos.jsonl")
    esperadas = cargar_esperadas(ROOT / "practica" / f"esperadas-{version}.jsonl")
    buscador = construir_buscador(ROOT / "normas" / version)
    params = cargar_parametros(version)
    resultados = []
    for caso in casos:
        _, entorno = jugar_caso(caso, buscador, params)
        resultados.append(comparar(esperadas[caso.id], entorno.decision, entorno.log))
    return resumir(resultados), resultados


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--salida", type=Path, default=ROOT / "datos" / "validacion_politica.json")
    args = parser.parse_args()

    informe = {}
    for version in VERSIONES_NORMAS:
        resumen, resultados = validar(version)
        fallos = [{"caso": r["caso"], "controles_fallidos": [k for k, ok in r["controles"].items() if not ok],
                   "esperada": r["esperada"], "obtenida": r["obtenida"]}
                  for r in resultados if not r["resuelto"]]
        informe[version] = {"resumen": resumen, "fallos": fallos,
                            "controles_fallidos": dict(Counter(c for f in fallos for c in f["controles_fallidos"]))}
        print(f"normas/{version}: {resumen['resueltos']}/{resumen['casos']} casos resueltos; "
              f"controles fallidos: {informe[version]['controles_fallidos'] or 'ninguno'}")
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Detalle en {args.salida.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
