"""Tests del recuperador (parte 1). Usan un encoder falso: no descargan modelos."""
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import recuperar  # noqa: E402
from recuperador import (  # noqa: E402
    Recuperador,
    fragmentar,
    fragmentar_secciones,
    fragmentar_ventana,
    leer_corpus,
    seleccionar,
)

DOC = """# Ingreso a internación

## Documentación

Se presenta el DNI y la orden.

## Horario de ingreso

Ingresan a las 7:00 si la cirugía es por la mañana.
"""

DOC_SIN_SECCIONES = """# Telemedicina

Las consultas son por video.

Se piden por la web.
"""


class EncoderFalso:
    """Bolsa de palabras sobre un vocabulario fijo por hash: determinista y sin red."""

    DIM = 512

    def _vec(self, texto):
        v = np.zeros(self.DIM)
        for p in re.findall(r"\w+", texto.lower()):
            v[hash(p) % self.DIM] += 1
        n = np.linalg.norm(v)
        return v / n if n else v

    def codificar_consultas(self, textos):
        return np.array([self._vec(t) for t in textos])

    def codificar_pasajes(self, textos):
        return np.array([self._vec(t) for t in textos])


def norm(t):  # la misma normalización que usa evaluar/evaluar.py
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", t).lower())


# ---------------- chunking ----------------

def test_secciones_un_fragmento_por_seccion():
    frags = fragmentar_secciones(DOC, metadatos=False)
    assert frags == ["Se presenta el DNI y la orden.", "Ingresan a las 7:00 si la cirugía es por la mañana."]


def test_secciones_con_metadatos_antepone_titulos():
    frags = fragmentar_secciones(DOC, metadatos=True)
    assert frags[1] == "Ingreso a internación — Horario de ingreso\nIngresan a las 7:00 si la cirugía es por la mañana."


def test_documento_sin_secciones_es_un_solo_fragmento():
    assert fragmentar_secciones(DOC_SIN_SECCIONES, metadatos=False) == [
        "Las consultas son por video.\n\nSe piden por la web."
    ]
    assert fragmentar_secciones(DOC_SIN_SECCIONES, metadatos=True)[0].startswith("Telemedicina\n")


def test_ventana_respeta_tamano_y_solapamiento():
    texto = "# T\n\n" + " ".join(f"p{i}" for i in range(10))
    frags = fragmentar_ventana(texto, tam=4, solapamiento=1, metadatos=False)
    assert frags == ["p0 p1 p2 p3", "p3 p4 p5 p6", "p6 p7 p8 p9"]


def test_ventana_no_incluye_titulos_markdown():
    frags = fragmentar_ventana(DOC, tam=100, solapamiento=0, metadatos=False)
    assert len(frags) == 1 and "#" not in frags[0] and "Documentación" not in frags[0]


def test_ventana_rechaza_solapamiento_mayor_o_igual_al_tamano():
    with pytest.raises(ValueError):
        fragmentar_ventana(DOC, tam=4, solapamiento=4, metadatos=False)


def test_fragmentar_despacha_por_estrategia():
    assert fragmentar(DOC, {"chunking": "seccion", "metadatos": False}) == fragmentar_secciones(DOC, False)
    with pytest.raises(ValueError):
        fragmentar(DOC, {"chunking": "otra", "metadatos": False})


@pytest.mark.parametrize("metadatos", [False, True])
def test_toda_evidencia_dev_queda_entera_en_algun_fragmento_por_seccion(metadatos):
    frags = [norm(f) for _, t in leer_corpus(RAIZ / "datos" / "corpus")
             for f in fragmentar_secciones(t, metadatos)]
    for linea in (RAIZ / "datos" / "preguntas_recuperacion_dev.jsonl").read_text(encoding="utf-8").splitlines():
        for ev in json.loads(linea)["evidencia"]:
            assert any(norm(ev) in f for f in frags), ev


# ---------------- selección ----------------

def test_seleccionar_top_k_en_orden():
    assert seleccionar(np.array([0.1, 0.9, 0.5, 0.7]), k=2, umbral=None, margen=None) == [1, 3]


def test_seleccionar_aplica_umbral_absoluto():
    assert seleccionar(np.array([0.9, 0.5, 0.7]), k=3, umbral=0.6, margen=None) == [0, 2]


def test_seleccionar_aplica_margen_relativo_al_mejor():
    assert seleccionar(np.array([0.90, 0.89, 0.70]), k=3, umbral=None, margen=0.05) == [0, 1]


def test_seleccionar_nunca_devuelve_vacio():
    assert seleccionar(np.array([0.2, 0.3]), k=3, umbral=0.9, margen=None) == [1]


# ---------------- Recuperador ----------------

@pytest.fixture
def rec():
    cfg = {"encoder": "falso", "chunking": "seccion", "metadatos": False, "k": 2, "umbral": None, "margen": None}
    return Recuperador(cfg, encoder=EncoderFalso(), corpus=[("a.md", DOC), ("b.md", DOC_SIN_SECCIONES)])


def test_buscar_devuelve_lista_de_textos_con_el_mas_relevante_primero(rec):
    res = rec.buscar("¿a qué hora ingresan por la mañana?")
    assert isinstance(res, list) and all(isinstance(f, str) for f in res)
    assert res[0] == "Ingresan a las 7:00 si la cirugía es por la mañana."
    assert len(res) == 2


def test_buscar_permite_pisar_k(rec):
    assert len(rec.buscar("consultas por video", k=1)) == 1


def test_desde_config_resuelve_rutas_desde_cualquier_directorio(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = Recuperador.desde_config(encoder=EncoderFalso())
    assert len(r.fragmentos) > 20
    assert any("12:00 a 12:30" in f for f in r.buscar("horario de visita en terapia intensiva al mediodía", k=5))


# ---------------- CLI ----------------

def test_cli_escribe_una_linea_por_pregunta_en_orden(tmp_path, rec):
    preg = tmp_path / "p.jsonl"
    preg.write_text('{"id": "X2", "pregunta": "¿video?"}\n{"id": "X1", "pregunta": "¿DNI?"}\n', encoding="utf-8")
    salida = tmp_path / "r.jsonl"
    recuperar.procesar(preg, salida, rec)
    filas = [json.loads(l) for l in salida.read_text(encoding="utf-8").splitlines()]
    assert [f["id"] for f in filas] == ["X2", "X1"]
    assert all(isinstance(f["fragmentos"], list) and f["fragmentos"] for f in filas)
    texto = salida.read_text(encoding="utf-8")
    assert "mañana" in texto and "\\u00" not in texto  # UTF-8 sin escapar


def test_salida_la_acepta_el_evaluador_oficial(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = Recuperador.desde_config(encoder=EncoderFalso())
    preguntas = RAIZ / "datos" / "preguntas_recuperacion_dev.jsonl"
    salida = tmp_path / "resultados.jsonl"
    recuperar.procesar(preguntas, salida, r)
    out = subprocess.run([sys.executable, str(RAIZ / "evaluar" / "evaluar.py"), "recuperacion",
                          "--preguntas", str(preguntas), "--resultados", str(salida)],
                         capture_output=True, text=True, check=True)
    assert "context_relevance" in json.loads(out.stdout)
