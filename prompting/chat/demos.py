"""Los tres demos que hacen visibles los criterios de exito del ejercicio 1."""
import time
from datetime import datetime

from chat.openrouter import mensajes_con_contexto
from chat.slots import get_slot
from chat.usage import moneda, mostrar

EFFORTS = ("low", "medium", "high")

# La pregunta del demo de effort tiene que obligar a pensar. Con una pregunta
# facil el modelo responde con 0 tokens de razonamiento en los tres niveles y
# el demo no muestra nada.
PREGUNTA_EFFORT = (
    "Un glider del juego de la vida se desplaza una celda en diagonal cada 4 "
    "generaciones. Arranca con su celda mas baja en la fila 0 de un tablero de "
    "20x20 y avanza hacia arriba y a la derecha. En que generacion toca por "
    "primera vez un borde? Mostra el calculo paso a paso."
)
PREGUNTA_GENERAL = "Explica en una linea que es un automata celular."


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


def demo_effort(cliente, log, pregunta=None):
    pregunta = pregunta or PREGUNTA_EFFORT
    slot = get_slot(1)
    mensajes = [{"role": "user", "content": pregunta}]
    return [_turno(cliente, log, slot, mensajes, {"effort": e}, e) for e in EFFORTS]


def demo_cache(cliente, log, contexto, pregunta=None):
    """Manda el mismo contexto dos veces y muestra el hit de la segunda.

    El contexto lleva adelante una marca unica por corrida: sin eso, si el
    cache quedo caliente de una conversacion anterior, la primera pasada ya
    da hit y el demo no muestra la transicion, que es lo que hay que ver.
    """
    pregunta = pregunta or PREGUNTA_GENERAL
    slot = get_slot(2)
    marca = f"<!-- corrida {datetime.now():%Y-%m-%d %H:%M:%S.%f} -->\n"
    mensajes = mensajes_con_contexto(marca + contexto,
                                     [{"role": "user", "content": pregunta}])
    return [_turno(cliente, log, slot, mensajes, {"contexto": True}, etiqueta)
            for etiqueta in ("primera pasada", "segunda pasada")]


def demo_precio(cliente, log, pregunta=None):
    """La misma pregunta al slot caro y al barato.

    Al slot 4 se le apaga el razonamiento a proposito: si razona genera cientos
    de tokens de salida contra las decenas del slot 2, y el costo total deja de
    reflejar la diferencia de tarifa, que es lo que el ejercicio pide comparar.
    """
    pregunta = pregunta or PREGUNTA_GENERAL
    mensajes = [{"role": "user", "content": pregunta}]
    opciones = {2: {}, 4: {"razonar": False}}
    return [_turno(cliente, log, get_slot(n), mensajes, opciones[n], f"slot {n}")
            for n in (2, 4)]
