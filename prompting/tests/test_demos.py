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
        self.enviados = []

    def completar(self, slot, mensajes, opciones):
        self.llamadas.append((slot.numero, opciones))
        self.enviados.append(mensajes)
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


def test_demo_effort_usa_una_pregunta_que_obliga_a_pensar(tmp_path):
    # Con una pregunta trivial el modelo devuelve 0 tokens de razonamiento en
    # los tres niveles y el demo no muestra el efecto del effort.
    from chat.demos import PREGUNTA_EFFORT
    assert "paso a paso" in PREGUNTA_EFFORT


def test_demo_cache_manda_el_mismo_contexto_dos_veces(tmp_path):
    c = ClienteFalso([Usage(prompt_tokens=5000, cached_tokens=0, cost=5e-3),
                      Usage(prompt_tokens=5000, cached_tokens=4900, cost=1e-3)])
    filas = demo_cache(c, log_en(tmp_path), "contexto largo", "resumilo")
    assert len(c.llamadas) == 2
    assert filas[0]["cacheados"] == "0"
    assert filas[1]["cacheados"] == "4900"
    # Las dos pasadas mandan exactamente el mismo prefijo: si difiere, no hay hit.
    primera, segunda = c.enviados
    assert primera[0]["content"][0]["text"] == segunda[0]["content"][0]["text"]


def test_demo_cache_marca_cada_corrida_para_forzar_un_miss_inicial(tmp_path):
    # Sin marca, un cache caliente de antes hace que la primera pasada ya de
    # hit y el demo no muestre la transicion.
    c1 = ClienteFalso([Usage(cost=1e-3), Usage(cost=1e-4)])
    c2 = ClienteFalso([Usage(cost=1e-3), Usage(cost=1e-4)])
    demo_cache(c1, log_en(tmp_path), "contexto", "p")
    demo_cache(c2, log_en(tmp_path), "contexto", "p")
    assert c1.enviados[0][0]["content"][0]["text"] != c2.enviados[0][0]["content"][0]["text"]


def test_demo_precio_pregunta_a_los_slots_2_y_4(tmp_path):
    c = ClienteFalso([Usage(cost=5e-3), Usage(cost=3.25e-4)])
    filas = demo_precio(c, log_en(tmp_path), "hola")
    assert [n for n, _ in c.llamadas] == [2, 4]
    assert len(filas) == 2
    # Al slot 4 se le apaga el razonamiento: si razona, genera cientos de
    # tokens de salida y el costo total deja de comparar tarifas.
    assert dict(c.llamadas)[4] == {"razonar": False}


def test_los_demos_dejan_todo_escrito_en_el_log(tmp_path):
    log = log_en(tmp_path)
    c = ClienteFalso([Usage(cost=1e-6), Usage(cost=2e-6), Usage(cost=3e-6)])
    demo_effort(c, log, "pregunta")
    texto = log.ruta.read_text(encoding="utf-8")
    assert texto.count("· asistente") == 3
