"""Compara dos evaluaciones caso por caso: qué fichas cambian, qué casos se ganan o se pierden y dónde se separan
las conversaciones.

Lee `corridas/<etiqueta>/<version>/resultados.jsonl` y `trazas.jsonl` de las dos etiquetas (las escribe
`admision.correr`, vía `evaluar.py`) para las normas original, b y c, y escribe el resultado en
`corridas/<etiqueta_b>/comparacion_<etiqueta_a>.json`. Por cada caso con alguna diferencia anota:

  - los campos de la ficha registrada que cambian y si el caso pasa de resuelto a no resuelto o al revés;
  - el primer mensaje del asistente que difiere (índice y número de turno del asistente). Si todos los mensajes que
    entraron al modelo hasta ese punto son idénticos, la diferencia salió del modelo con la misma entrada.

    uv run python comparar_corridas.py sft_prompt sft_prompt_rep
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
CORRIDAS = RAIZ / "corridas"
VERSIONES = ("original", "b", "c")


def _leer(ruta: Path) -> dict[str, dict]:
    filas = [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines() if linea.strip()]
    return {fila["caso"]: fila for fila in filas}


def _primera_diferencia(a: list[dict], b: list[dict]) -> dict | None:
    """Primer mensaje distinto entre dos conversaciones, con su rol y cuántos turnos del asistente lo preceden."""
    turnos = 0
    for indice, (ma, mb) in enumerate(zip(a, b)):
        if ma != mb:
            return {"indice": indice, "rol": ma.get("role"), "turno_asistente": turnos + (ma.get("role") == "assistant"),
                    "entrada_identica": a[:indice] == b[:indice]}
        turnos += ma.get("role") == "assistant"
    if len(a) != len(b):
        return {"indice": min(len(a), len(b)), "rol": "largo distinto", "turno_asistente": turnos,
                "entrada_identica": True}
    return None


def comparar_version(etiqueta_a: str, etiqueta_b: str, version: str) -> dict:
    res_a, res_b = (_leer(CORRIDAS / e / version / "resultados.jsonl") for e in (etiqueta_a, etiqueta_b))
    tr_a, tr_b = (_leer(CORRIDAS / e / version / "trazas.jsonl") for e in (etiqueta_a, etiqueta_b))
    casos = []
    for caso in sorted(res_a):
        ra, rb = res_a[caso], res_b[caso]
        diferencia = _primera_diferencia(tr_a[caso]["mensajes"], tr_b[caso]["mensajes"])
        campos = sorted(k for k in set(ra["obtenida"]) | set(rb["obtenida"])
                        if ra["obtenida"].get(k) != rb["obtenida"].get(k))
        controles = sorted(k for k in ra["controles"] if ra["controles"][k] != rb["controles"][k])
        if diferencia is None and not campos:
            continue
        casos.append({"caso": caso, "campos_que_cambian": campos, "controles_que_cambian": controles,
                      "resuelto": [ra["resuelto"], rb["resuelto"]], "primera_diferencia": diferencia})
    con_ficha = [c for c in casos if c["campos_que_cambian"]]
    return {
        "casos": len(res_a),
        "resueltos": [sum(r["resuelto"] for r in res_a.values()), sum(r["resuelto"] for r in res_b.values())],
        "conversaciones_distintas": sum(c["primera_diferencia"] is not None for c in casos),
        "fichas_distintas": len(con_ficha),
        "gana": [c["caso"] for c in casos if not c["resuelto"][0] and c["resuelto"][1]],
        "pierde": [c["caso"] for c in casos if c["resuelto"][0] and not c["resuelto"][1]],
        "divergen_con_entrada_identica": sum(bool(c["primera_diferencia"] and c["primera_diferencia"]["entrada_identica"])
                                             for c in casos),
        "detalle": casos,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("etiqueta_a")
    parser.add_argument("etiqueta_b")
    args = parser.parse_args()
    resultado = {"a": args.etiqueta_a, "b": args.etiqueta_b,
                 "versiones": {v: comparar_version(args.etiqueta_a, args.etiqueta_b, v) for v in VERSIONES}}
    salida = CORRIDAS / args.etiqueta_b / f"comparacion_{args.etiqueta_a}.json"
    salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for version, r in resultado["versiones"].items():
        print(f"{version}: resueltos {r['resueltos'][0]} -> {r['resueltos'][1]}, fichas distintas {r['fichas_distintas']}"
              f"/{r['casos']}, conversaciones distintas {r['conversaciones_distintas']}, gana {r['gana']},"
              f" pierde {r['pierde']}")
    print(f"-> {salida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
