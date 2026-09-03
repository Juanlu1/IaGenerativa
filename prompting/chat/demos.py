"""Los tres demos que hacen visibles los criterios de exito del ejercicio 1."""
import time

from chat.openrouter import mensajes_con_contexto
from chat.slots import get_slot
from chat.usage import moneda, mostrar

EFFORTS = ("low", "medium", "high")


def _fila(etiqueta, usage, segundos):
    return {
        "etiqueta": etiqueta,
        "entrada": mostrar(usage.prompt_tokens),
        "salida": mostrar(usage.completion_tokens),
        "razonamiento": mostrar(usage.reasoning_tokens),
        "cacheados": mostrar(usage.cached_tokens),
        "costo": moneda(usage.cost),
        "segundos": f"{segundos:.1f}",
    }


def _turno(cliente, log, slot, mensajes, opciones, etiqueta):
    log.usuario(f"[{etiqueta}] {mensajes[-1]['content']}")
    t0 = time.monotonic()
    texto, usage = cliente.completar(slot, mensajes, opciones)
    segundos = time.monotonic() - t0
    log.asistente(texto, usage)
    return _fila(etiqueta, usage, segundos)


def demo_effort(cliente, log, pregunta):
    slot = get_slot(1)
    mensajes = [{"role": "user", "content": pregunta}]
    return [_turno(cliente, log, slot, mensajes, {"effort": e}, e) for e in EFFORTS]


def demo_cache(cliente, log, contexto, pregunta):
    slot = get_slot(2)
    mensajes = mensajes_con_contexto(contexto, [{"role": "user", "content": pregunta}])
    return [_turno(cliente, log, slot, mensajes, {"contexto": True}, etiqueta)
            for etiqueta in ("primera pasada", "segunda pasada")]


def demo_precio(cliente, log, pregunta):
    mensajes = [{"role": "user", "content": pregunta}]
    return [_turno(cliente, log, get_slot(n), mensajes, {}, f"slot {n}")
            for n in (2, 4)]
