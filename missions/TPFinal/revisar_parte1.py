"""Reproduce las cifras de revision_parte1.md (solo lee; no cambia la clasificación).

    uv run python revisar_parte1.py
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OPERADORES_RUIDO = ("OP-04", "OP-11", "OP-17")


def main() -> None:
    with (ROOT / "historial" / "historial.csv").open(encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))
    with (ROOT / "curado" / "auditoria.csv").open(encoding="utf-8") as f:
        auditoria = {r["id"]: r for r in csv.DictReader(f)}

    def costumbre(fila, corte=75):
        return int(fila["edad"]) >= corte and not fila["acompanante"].strip()

    def aviso(fila):
        return fila["aviso_al_voluntariado"] == "sí"

    print("1. Avisos por edad (sin acompañante | sin acompañante y sin OP-04/11/17 | con acompañante)")
    for edad in range(70, 81):
        sin = [x for x in filas if int(x["edad"]) == edad and not x["acompanante"].strip()]
        otros = [x for x in sin if x["operador"] not in OPERADORES_RUIDO]
        con = [x for x in filas if int(x["edad"]) == edad and x["acompanante"].strip()]
        print(f"   {edad}: {sum(map(aviso, sin))}/{len(sin)} | {sum(map(aviso, otros))}/{len(otros)} | "
              f"{sum(map(aviso, con))}/{len(con)}")
    a75 = [x for x in filas if int(x["edad"]) == 75 and not x["acompanante"].strip()]
    print("   75 años sin acompañante:", [(x["id"], auditoria[x["id"]]["tipo"]) for x in a75])
    for corte in (76, 75):
        dentro = [x for x in filas if costumbre(x, corte)]
        fuera = [x for x in filas if not costumbre(x, corte) and aviso(x)]
        print(f"   corte {corte}: costumbre {sum(map(aviso, dentro))}/{len(dentro)}, avisos fuera {len(fuera)}")

    print("2. Avisos fuera de la costumbre (corte 75), por operador")
    por_operador = defaultdict(lambda: [0, 0])
    for x in filas:
        if not costumbre(x):
            por_operador[x["operador"]][0] += aviso(x)
            por_operador[x["operador"]][1] += 1
    for operador, (avisos, total) in sorted(por_operador.items()):
        print(f"   {operador}: {avisos}/{total}")
    excepciones = Counter(x["operador"] for x in filas if costumbre(x) and not aviso(x))
    print("   avisos omitidos dentro de la costumbre, por operador:", dict(excepciones))
    ruido = Counter("OP-04/11/17" if x["operador"] in OPERADORES_RUIDO else "otros"
                    for x in filas if auditoria[x["id"]]["tipo"] == "ruido")
    print("   filas ruido:", dict(ruido))

    print("3. Auditoría: motivos de error y errores por operador")
    motivos = Counter(m for r in auditoria.values() for m in filter(None, r["reglas_violadas"].split(" | ")))
    for motivo, n in motivos.most_common():
        print(f"   {n}: {motivo}")
    por_op = Counter(x["operador"] for x in filas if auditoria[x["id"]]["tipo"] == "error")
    print(f"   errores por operador: min {min(por_op.values())}, max {max(por_op.values())}")
    print("   motivos por fila error:", Counter(len(r["reglas_violadas"].split(" | "))
                                             for r in auditoria.values() if r["tipo"] == "error"))
    libres = [x for x in filas if not (int(x["nivel"]) <= 2 or int(x["edad"]) >= 67)]
    print("   box sin obligación (P-ADM-1=2, P-ADM-2=67):", Counter(x["box_antes_del_registro"] for x in libres))
    dos = [x for x in filas if ";" in x["credenciales"]]
    print("   dos credenciales (prepaga verificada, respuesta, cobertura):",
          Counter((x["entidad_verificada"].startswith("Prepaga"), x["respuesta_verificacion"], x["cobertura"]) for x in dos))


if __name__ == "__main__":
    main()
