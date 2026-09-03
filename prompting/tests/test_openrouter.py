from chat.openrouter import construir_body, contexto_estatico, mensajes_con_contexto
from chat.slots import get_slot

MENSAJES = [{"role": "user", "content": "hola"}]


def test_el_body_siempre_lleva_modelo_y_mensajes():
    body = construir_body(get_slot(4), MENSAJES, {})
    assert body["model"] == "deepseek/deepseek-v4-flash-0731"
    assert body["messages"] == MENSAJES


def test_slot_1_manda_el_effort_elegido():
    body = construir_body(get_slot(1), MENSAJES, {"effort": "high"})
    assert body["reasoning"] == {"effort": "high"}


def test_slot_1_sin_effort_no_manda_reasoning():
    assert "reasoning" not in construir_body(get_slot(1), MENSAJES, {})


def test_slot_3_manda_el_schema_como_response_format():
    schema = {"type": "object", "properties": {"n": {"type": "integer"}}}
    body = construir_body(get_slot(3), MENSAJES, {"schema": schema})
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["schema"] == schema


def test_slot_4_con_razonamiento_prendido_manda_reasoning():
    body = construir_body(get_slot(4), MENSAJES, {"razonar": True})
    assert body["reasoning"] == {"effort": "medium"}


def test_slot_4_con_razonamiento_apagado_no_manda_reasoning():
    assert "reasoning" not in construir_body(get_slot(4), MENSAJES, {"razonar": False})


def test_el_contexto_estatico_va_primero_y_marcado_para_cachear():
    mensajes = mensajes_con_contexto("texto largo", MENSAJES)
    bloque = mensajes[0]["content"][0]
    assert mensajes[0]["role"] == "system"
    assert bloque["text"] == "texto largo"
    assert bloque["cache_control"] == {"type": "ephemeral"}
    assert mensajes[1:] == MENSAJES


def test_el_contexto_estatico_sale_de_los_archivos_del_repo(tmp_path):
    (tmp_path / "mission.md").write_text("enunciado", encoding="utf-8")
    (tmp_path / "SPEC.md").write_text("contrato", encoding="utf-8")
    texto = contexto_estatico(tmp_path)
    assert "enunciado" in texto and "contrato" in texto


import pytest
from chat.openrouter import ErrorOpenRouter, leer_api_key


def test_lee_la_key_con_igual(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OPENROUTER_API_KEY=sk-or-v1-abc\n", encoding="utf-8")
    assert leer_api_key(env) == "sk-or-v1-abc"


def test_lee_la_key_aunque_este_escrita_con_dos_puntos(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OPENROUTER_API_KEY: sk-or-v1-abc\n", encoding="utf-8")
    assert leer_api_key(env) == "sk-or-v1-abc"


def test_ignora_comentarios_y_lineas_vacias(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# comentario\n\nOPENROUTER_API_KEY=sk-or-v1-abc\n", encoding="utf-8")
    assert leer_api_key(env) == "sk-or-v1-abc"


def test_sin_key_lanza_error_claro(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OTRA=cosa\n", encoding="utf-8")
    with pytest.raises(ErrorOpenRouter, match="OPENROUTER_API_KEY"):
        leer_api_key(env)
