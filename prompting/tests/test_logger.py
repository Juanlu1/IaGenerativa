from datetime import datetime

from chat.logger import LogConversacion
from chat.slots import get_slot
from chat.usage import Usage

INICIO = datetime(2026, 9, 3, 14, 2, 11)


def nuevo_log(tmp_path, slot=2):
    return LogConversacion(tmp_path, get_slot(slot), inicio=INICIO)


def test_el_nombre_del_archivo_lleva_fecha_hora_y_slot(tmp_path):
    log = nuevo_log(tmp_path)
    assert log.ruta.name == "2026-09-03-140211-slot2.md"


def test_abrir_crea_el_archivo_con_el_encabezado(tmp_path):
    log = nuevo_log(tmp_path)
    log.abrir()
    texto = log.ruta.read_text(encoding="utf-8")
    assert "anthropic/claude-haiku-4.5" in texto
    assert "2026-09-03 14:02:11" in texto


def test_abrir_crea_la_carpeta_si_no_existe(tmp_path):
    destino = tmp_path / "logs" / "pruebas"
    log = LogConversacion(destino, get_slot(1), inicio=INICIO)
    log.abrir()
    assert log.ruta.exists()


def test_un_turno_completo_queda_escrito(tmp_path):
    log = nuevo_log(tmp_path)
    log.abrir()
    log.usuario("hola")
    log.asistente("qué tal", Usage(prompt_tokens=18, completion_tokens=39,
                                   reasoning_tokens=23, cached_tokens=0,
                                   cost=8.19e-06))
    texto = log.ruta.read_text(encoding="utf-8")
    assert "## Turno 1 · usuario" in texto
    assert "hola" in texto
    assert "## Turno 1 · asistente" in texto
    assert "qué tal" in texto
    assert "$0.000008" in texto


def test_el_segundo_turno_no_pisa_al_primero(tmp_path):
    log = nuevo_log(tmp_path)
    log.abrir()
    log.usuario("primero")
    log.asistente("uno", Usage(cost=1e-06))
    log.usuario("segundo")
    log.asistente("dos", Usage(cost=2e-06))
    texto = log.ruta.read_text(encoding="utf-8")
    assert "primero" in texto and "segundo" in texto
    assert "## Turno 2 · usuario" in texto


def test_los_campos_ausentes_se_escriben_como_raya(tmp_path):
    log = nuevo_log(tmp_path)
    log.abrir()
    log.usuario("hola")
    log.asistente("respuesta", Usage(prompt_tokens=10))
    assert "—" in log.ruta.read_text(encoding="utf-8")


def test_un_error_queda_registrado_en_el_log(tmp_path):
    log = nuevo_log(tmp_path)
    log.abrir()
    log.usuario("hola")
    log.error("HTTP 429: rate limited")
    assert "429" in log.ruta.read_text(encoding="utf-8")
