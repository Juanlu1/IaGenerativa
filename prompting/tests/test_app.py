import pytest

from chat.app import crear_app


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-falsa")
    app = crear_app(tmp_path)
    app.config["TESTING"] = True
    return app.test_client()


def test_la_pagina_carga_y_lista_los_cuatro_modelos(cliente):
    html = cliente.get("/").get_data(as_text=True)
    for modelo in ("gpt-5.6-luna", "claude-haiku-4.5",
                   "gemini-3.7-flash", "deepseek-v4-flash"):
        assert modelo in html


def test_arrancar_el_server_no_crea_ningun_log(cliente, tmp_path):
    # El log es evidencia: no queremos archivos vacios ensuciando la carpeta.
    assert not list(tmp_path.glob("logs/**/*.md"))


def test_cambiar_de_slot_empieza_conversacion_nueva(cliente):
    r = cliente.post("/api/slot", json={"slot": 2, "carpeta": "pruebas"})
    datos = r.get_json()
    assert datos["slot"] == 2
    assert datos["mensajes"] == 0
    assert datos["log"].endswith(".md")


def test_cambiar_de_slot_crea_el_log_en_la_carpeta_elegida(cliente, tmp_path):
    cliente.post("/api/slot", json={"slot": 1, "carpeta": "conway"})
    assert list((tmp_path / "logs" / "conway").glob("*.md"))


def test_una_carpeta_inventada_cae_en_pruebas(cliente, tmp_path):
    cliente.post("/api/slot", json={"slot": 1, "carpeta": "../../etc"})
    assert list((tmp_path / "logs" / "pruebas").glob("*.md"))


def test_carga_el_prompt_desde_un_archivo_del_disco(cliente, tmp_path):
    archivo = tmp_path / "prompt-conway.txt"
    archivo.write_text("contrato largo del ejercicio 2", encoding="utf-8")
    r = cliente.post("/api/prompt-archivo", json={"ruta": str(archivo)})
    assert r.get_json()["texto"] == "contrato largo del ejercicio 2"


def test_pedir_un_archivo_inexistente_da_error_claro(cliente, tmp_path):
    r = cliente.post("/api/prompt-archivo", json={"ruta": str(tmp_path / "no-existe.txt")})
    assert r.status_code == 400
    assert "no-existe.txt" in r.get_json()["error"]
