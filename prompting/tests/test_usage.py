from chat.usage import Usage, normalizar, mostrar, moneda

RESPUESTA_REAL = {
    "id": "gen-1788403287-cuRGvN3vb9kzlchTAVoe",
    "model": "deepseek/deepseek-v4-flash-20260731",
    "usage": {
        "prompt_tokens": 18,
        "completion_tokens": 39,
        "total_tokens": 57,
        "cost": 8.19e-06,
        "prompt_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
        "completion_tokens_details": {"reasoning_tokens": 23},
    },
}


def test_normaliza_una_respuesta_real():
    u = normalizar(RESPUESTA_REAL)
    assert u.prompt_tokens == 18
    assert u.completion_tokens == 39
    assert u.reasoning_tokens == 23
    assert u.cached_tokens == 0
    assert u.cost == 8.19e-06
    assert u.generation_id == "gen-1788403287-cuRGvN3vb9kzlchTAVoe"
    assert u.model == "deepseek/deepseek-v4-flash-20260731"


def test_cache_discount_ausente_queda_en_none_no_en_cero():
    # Verificado contra la API: cuando no hubo cache, el campo no viene.
    u = normalizar(RESPUESTA_REAL)
    assert u.cache_discount is None


def test_respuesta_sin_ningun_detalle_no_revienta():
    u = normalizar({"id": "gen-x", "usage": {"prompt_tokens": 5}})
    assert u.prompt_tokens == 5
    assert u.completion_tokens is None
    assert u.reasoning_tokens is None
    assert u.cached_tokens is None


def test_respuesta_sin_usage_no_revienta():
    u = normalizar({"id": "gen-x"})
    assert u.prompt_tokens is None
    assert u.cost is None


def test_guarda_la_respuesta_cruda_para_el_informe():
    u = normalizar(RESPUESTA_REAL)
    assert u.raw is RESPUESTA_REAL


def test_mostrar_convierte_none_en_raya():
    assert mostrar(None) == "—"
    assert mostrar(0) == "0"
    assert mostrar(23) == "23"


def test_moneda_formatea_con_seis_decimales():
    assert moneda(None) == "—"
    assert moneda(8.19e-06) == "$0.000008"
