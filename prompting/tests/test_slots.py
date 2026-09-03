import pytest
from chat.slots import SLOTS, Slot, get_slot


def test_hay_exactamente_cuatro_slots():
    assert sorted(SLOTS) == [1, 2, 3, 4]


def test_cada_slot_es_de_un_proveedor_distinto():
    proveedores = [s.modelo.split("/")[0] for s in SLOTS.values()]
    assert len(set(proveedores)) == 4


def test_los_modelos_son_los_del_enunciado():
    assert SLOTS[1].modelo == "openai/gpt-5.6-luna"
    assert SLOTS[2].modelo == "anthropic/claude-haiku-4.5"
    assert SLOTS[3].modelo == "google/gemini-3.7-flash"
    assert SLOTS[4].modelo == "deepseek/deepseek-v4-flash-0731"


def test_cada_slot_declara_el_control_que_ejercita():
    assert SLOTS[1].control == "effort"
    assert SLOTS[2].control == "cache"
    assert SLOTS[3].control == "schema"
    assert SLOTS[4].control == "reasoning"


def test_get_slot_devuelve_el_slot():
    assert get_slot(3) is SLOTS[3]


def test_get_slot_con_numero_invalido_lanza_error():
    with pytest.raises(ValueError):
        get_slot(9)
