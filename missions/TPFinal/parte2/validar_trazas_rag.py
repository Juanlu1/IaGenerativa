"""Contrasta el RAG con búsquedas reales de las 800 trazas de referencia.

La comparación es auxiliar: las secciones recuperadas por el buscador de la
cátedra y los `fundamentos` de cada ficha no son etiquetas oficiales por
consulta. Sirve para detectar si una mejora sobre las 60 consultas de
desarrollo empeora las búsquedas que hace un agente.
"""

import argparse
import json
import re
from pathlib import Path

from rag_buscador import BuscadorNormas


_ID = re.compile(r"^## (NOR-[A-Z]{3}-\d{2})", re.MULTILINE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normas", type=Path, required=True)
    ap.add_argument("--trazas", type=Path, required=True)
    ap.add_argument("--ejemplos", type=int, default=0)
    a = ap.parse_args()
    buscadores = {modo: BuscadorNormas(a.normas, modo) for modo in ("seccion", "mixto")}
    consultas = 0
    completos = {modo: 0 for modo in buscadores}
    coberturas = {modo: 0 for modo in buscadores}
    total_fundamentos = 0
    ejemplos = []
    caracteres = {modo: 0 for modo in buscadores}
    for linea in a.trazas.read_text(encoding="utf-8").splitlines():
        caso = json.loads(linea)
        por_caso = {modo: set() for modo in buscadores}
        consultas_caso = []
        for paso in caso["pasos"]:
            if paso["herramienta"] != "buscar_normativa":
                continue
            consulta = paso["argumentos"]["consulta"]
            referencia = _ID.findall(paso["resultado"])
            consultas += 1
            detalle = {"consulta": consulta}
            for modo, buscador in buscadores.items():
                fragmentos = buscador.recuperar(consulta, 2)
                encontrados = [f.seccion for f in fragmentos]
                caracteres[modo] += sum(len(f.texto) for f in fragmentos)
                por_caso[modo].update(encontrados)
                detalle[modo] = encontrados
                if set(referencia).issubset(encontrados):
                    completos[modo] += 1
            consultas_caso.append(detalle)
        decisiones = [p for p in caso["pasos"] if p["herramienta"] == "registrar_decision"]
        fundamentos = set(decisiones[-1]["argumentos"].get("fundamentos", [])) if decisiones else set()
        total_fundamentos += len(fundamentos)
        for modo in buscadores:
            coberturas[modo] += len(fundamentos & por_caso[modo])
        perdido = (fundamentos & por_caso["seccion"]) - por_caso["mixto"]
        if perdido and len(ejemplos) < a.ejemplos:
            ejemplos.append({"caso": caso["id"], "perdido": sorted(perdido),
                             "fundamentos": sorted(fundamentos), "consultas": consultas_caso})
    print(json.dumps({"consultas": consultas,
                      "referencia_top2_cubierta": completos,
                      "fundamentos_por_caso_cubiertos": coberturas,
                      "fundamentos_totales": total_fundamentos,
                      "tokens_por_consulta": {modo: round(caracteres[modo] / consultas / 4)
                                              for modo in buscadores},
                      "ejemplos": ejemplos}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
