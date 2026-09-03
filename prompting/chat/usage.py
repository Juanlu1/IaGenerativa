"""Normaliza el usage de OpenRouter.

Cualquier campo puede venir ausente segun el proveedor y segun si hubo cache.
Ausente se representa con None, y se muestra como raya. Nunca KeyError.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Usage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    reasoning_tokens: int | None = None
    cached_tokens: int | None = None
    cache_write_tokens: int | None = None
    cost: float | None = None
    cache_discount: float | None = None
    generation_id: str | None = None
    model: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def normalizar(respuesta: dict) -> Usage:
    u = respuesta.get("usage") or {}
    entrada = u.get("prompt_tokens_details") or {}
    salida = u.get("completion_tokens_details") or {}
    return Usage(
        prompt_tokens=u.get("prompt_tokens"),
        completion_tokens=u.get("completion_tokens"),
        reasoning_tokens=salida.get("reasoning_tokens"),
        cached_tokens=entrada.get("cached_tokens"),
        cache_write_tokens=entrada.get("cache_write_tokens"),
        cost=u.get("cost"),
        cache_discount=u.get("cache_discount"),
        generation_id=respuesta.get("id"),
        model=respuesta.get("model"),
        raw=respuesta,
    )


def mostrar(valor) -> str:
    return "—" if valor is None else str(valor)


def moneda(valor) -> str:
    return "—" if valor is None else f"${valor:.6f}"
