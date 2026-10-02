"""Tests de las seis herramientas (partes 2 y 3). Sin red: API de la cátedra en un puerto libre."""
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "api"))

import herramientas  # noqa: E402
from servidor import Handler  # noqa: E402  (api/servidor.py, sin modificar)


@pytest.fixture
def api(monkeypatch):
    servidor = ThreadingHTTPServer(("localhost", 0), Handler)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    monkeypatch.setenv("HOSPITAL_API_URL", f"http://localhost:{servidor.server_port}")
    yield
    servidor.shutdown()
    servidor.server_close()


class RecuperadorFalso:
    def __init__(self, fragmentos):
        self.fragmentos, self.consultas = fragmentos, []

    def buscar(self, consulta, k=None):
        self.consultas.append(consulta)
        return self.fragmentos


def test_estan_las_seis_con_los_nombres_del_enunciado():
    assert [f.__name__ for f in herramientas.HERRAMIENTAS] == [
        "buscar_documentos", "consultar_camas", "consultar_guardia",
        "consultar_turnos", "consultar_farmacia", "consultar_espera"]


def test_todas_tienen_descripcion_para_el_modelo():
    for f in herramientas.HERRAMIENTAS:
        assert f.__doc__ and len(f.__doc__) > 80, f.__name__


def test_camas_devuelve_el_json_de_la_api_como_texto(api):
    datos = json.loads(herramientas.consultar_camas("pediatria"))
    assert datos["datos"] == {"total": 24, "ocupadas": 17, "libres": 7}


def test_acepta_nombres_con_espacios_y_tildes(api):
    assert json.loads(herramientas.consultar_camas("Terapia Intensiva"))["datos"]["libres"] == 0
    assert json.loads(herramientas.consultar_guardia("cardiología"))["datos"][1]["profesional"] == "Dra. Paula Benítez"
    assert json.loads(herramientas.consultar_farmacia("enalapril 10 mg"))["datos"]["reposicion"] == "2026-10-09"


def test_turnos_y_espera(api):
    assert json.loads(herramientas.consultar_turnos("traumatologia"))["datos"][0] == "2026-10-07 08:40"
    assert json.loads(herramientas.consultar_espera())["minutos_por_nivel"]["verde"] == 135


def test_un_nombre_inexistente_devuelve_el_error_con_las_opciones(api):
    datos = json.loads(herramientas.consultar_farmacia("enalapril"))
    assert "error" in datos and "enalapril 10 mg" in datos["opciones"]


def test_api_caida_devuelve_un_error_en_vez_de_lanzar(monkeypatch):
    monkeypatch.setenv("HOSPITAL_API_URL", "http://localhost:9")
    assert "no se pudo consultar la API" in json.loads(herramientas.consultar_espera())["error"]


def test_buscar_documentos_usa_el_recuperador_y_une_los_fragmentos(monkeypatch):
    falso = RecuperadorFalso(["fragmento uno", "fragmento dos"])
    monkeypatch.setattr(herramientas, "_recuperador", falso)
    assert herramientas.buscar_documentos("¿horario de visita?") == "fragmento uno\n\n---\n\nfragmento dos"
    assert falso.consultas == ["¿horario de visita?"]


def test_el_recuperador_se_crea_una_sola_vez(monkeypatch):
    falso = RecuperadorFalso(["x"])
    monkeypatch.setattr(herramientas, "_recuperador", falso)
    assert herramientas.recuperador() is herramientas.recuperador() is falso
