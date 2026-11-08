"""Compara ranking por sección completa y por el apartado más relevante.

Es un experimento local sobre las consultas de desarrollo, no la implementación
que carga `entrega_rag.py`.
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from admision.evaluar_rag import _normalizar, cargar_dataset, evaluar_buscador
from rag_buscador import BuscadorNormas, _consulta_expandida, _normalizar as normalizar_consulta


def puntajes_bm25(buscador, consulta):
    terminos = Counter(_consulta_expandida(consulta))
    puntajes = []
    for frec, largo in zip(buscador._frecuencias, buscador._largos):
        normalizador = 1.2 * (0.25 + 0.75 * largo / max(buscador._largo_medio, 1))
        puntajes.append(sum(
            buscador._idf.get(t, 0) * (f * 2.2 / (f + normalizador)) * min(peso, 2)
            for t, peso in terminos.items() if (f := frec.get(t, 0))
        ))
    return puntajes


class BuscadorMixto:
    k_entorno = 2

    def __init__(self, ruta_normas, peso_seccion, peso_cita=0, peso_unidad=0):
        self.secciones = BuscadorNormas(ruta_normas, "seccion")
        self.apartados = BuscadorNormas(ruta_normas, "apartado")
        self.peso_seccion = peso_seccion
        self.peso_cita = peso_cita
        self.peso_unidad = peso_unidad

    def recuperar(self, consulta, k):
        return [fragmento for _, fragmento in self.rankear(consulta)[:k]]

    def rankear(self, consulta):
        ss = puntajes_bm25(self.secciones, consulta)
        pp = puntajes_bm25(self.apartados, consulta)
        mejor_apartado = {}
        for fragmento, puntaje in zip(self.apartados.fragmentos, pp):
            mejor_apartado[fragmento.seccion] = max(mejor_apartado.get(fragmento.seccion, 0), puntaje)
        max_s = max(ss, default=1) or 1
        max_p = max(pp, default=1) or 1
        ranking = []
        for i, (fragmento, s) in enumerate(zip(self.secciones.fragmentos, ss)):
            p = mejor_apartado.get(fragmento.seccion, 0)
            puntaje = self.peso_seccion * s / max_s + (1 - self.peso_seccion) * p / max_p
            ranking.append((puntaje, fragmento))
        ranking.sort(key=lambda x: (-x[0], x[1].seccion))
        q = normalizar_consulta(consulta)
        if self.peso_unidad and "nivel" in q:
            ranking = [(puntaje + (self.peso_unidad if "= nivel" in f.texto else 0), f)
                       for puntaje, f in ranking]
            ranking.sort(key=lambda x: (-x[0], x[1].seccion))
        if self.peso_cita and ranking:
            primera = ranking[0][1].seccion
            citas = {}
            max_apartado = max((puntaje for fragmento, puntaje in zip(self.apartados.fragmentos, pp)
                                if fragmento.seccion == primera), default=1) or 1
            for fragmento, puntaje in zip(self.apartados.fragmentos, pp):
                if fragmento.seccion != primera:
                    continue
                for destino in re.findall(r"NOR-[A-Z]{3}-\d{2}", fragmento.texto):
                    if destino != primera:
                        citas[destino] = max(citas.get(destino, 0), puntaje / max_apartado)
            ranking = [(puntaje + self.peso_cita * citas.get(f.seccion, 0), f)
                       for puntaje, f in ranking]
            ranking.sort(key=lambda x: (-x[0], x[1].seccion))
        return ranking


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--normas", type=Path, required=True)
    ap.add_argument("--consultas", type=Path, required=True)
    a = ap.parse_args()
    dataset = cargar_dataset(a.consultas)
    for peso in (0, 0.25, 0.5, 0.75, 1):
        configuraciones = ((0, 0), (0, 0.05), (0, 0.1), (0, 0.15)) if peso == 0.5 else ((0, 0),)
        for peso_cita, peso_unidad in configuraciones:
            buscador = BuscadorMixto(a.normas, peso, peso_cita, peso_unidad)
            print(json.dumps({"peso_seccion": peso, "peso_cita": peso_cita, "peso_unidad": peso_unidad,
                              **evaluar_buscador(buscador, dataset)}, ensure_ascii=False))
            if peso != 0.5 or peso_unidad == 0:
                continue
            for item in dataset:
                traidos = buscador.recuperar(item["consulta"], 2)
                falta = [e["seccion"] for e in item["evidencia"]
                         if not any(_normalizar(e["texto"]) in _normalizar(f.texto) for f in traidos)]
                if falta:
                    print(json.dumps({"consulta": item["id"], "falta": falta,
                                      "traidos": [f.seccion for f in traidos]}, ensure_ascii=False))
                    print(json.dumps({"ranking": [(f.seccion, round(s, 3)) for s, f in buscador.rankear(item["consulta"])[:6]]},
                                     ensure_ascii=False))


if __name__ == "__main__":
    main()
