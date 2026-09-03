from datetime import datetime

from chat.demos import demo_cache, demo_effort, demo_precio
from chat.logger import LogConversacion
from chat.slots import get_slot
from chat.usage import Usage


class ClienteFalso:
    """Devuelve una respuesta fija y anota con que opciones lo llamaron."""

    def __init__(self, usages):
        self.usages = list(usages)
        self.llamadas = []

    def completar(self, slot, mensajes, opciones):
        self.llamadas.append((slot.numero, opciones))
        return "respuesta", self.usages.pop(0)


def log_en(tmp_path):
    log = LogConversacion(tmp_path, get_slot(1), inicio=datetime(2026, 9, 3, 12, 0, 0))
    log.abrir()
    return log


def test_demo_effort_corre_los_tres_niveles(tmp_path):
    c = ClienteFalso([Usage(cost=1e-6, reasoning_tokens=10),
                      Usage(cost=2e-6, reasoning_tokens=50),
                      Usage(cost=3e-6, reasoning_tokens=200)])
    filas = demo_effort(c, log_en(tmp_path), "cuanto es 2+2")
    assert [o["effort"] for _, o in c.llamadas] == ["low", "medium", "high"]
    assert [f["etiqueta"] for f in filas] == ["low", "medium", "high"]
    assert filas[2]["razonamiento"] == "200"


def test_demo_cache_manda_el_mismo_contexto_dos_veces(tmp_path):
    c = ClienteFalso([Usage(prompt_tokens=5000, cached_tokens=0, cost=5e-3),
                      Usage(prompt_tokens=5000, cached_tokens=4900, cost=1e-3)])
    filas = demo_cache(c, log_en(tmp_path), "contexto largo", "resumilo")
    assert len(c.llamadas) == 2
    assert filas[0]["cacheados"] == "0"
    assert filas[1]["cacheados"] == "4900"


def test_demo_precio_pregunta_a_los_slots_2_y_4(tmp_path):
    c = ClienteFalso([Usage(cost=5e-3), Usage(cost=3.25e-4)])
    filas = demo_precio(c, log_en(tmp_path), "hola")
    assert [n for n, _ in c.llamadas] == [2, 4]
    assert len(filas) == 2


def test_los_demos_dejan_todo_escrito_en_el_log(tmp_path):
    log = log_en(tmp_path)
    c = ClienteFalso([Usage(cost=1e-6), Usage(cost=2e-6), Usage(cost=3e-6)])
    demo_effort(c, log, "pregunta")
    texto = log.ruta.read_text(encoding="utf-8")
    assert texto.count("· asistente") == 3
