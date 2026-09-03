"""Cliente de OpenRouter.

Lo puro (armado del body, contexto estatico) esta separado de la llamada HTTP
para poder testearlo sin red y sin gastar creditos.
"""
from pathlib import Path

from chat.slots import Slot


class ErrorOpenRouter(Exception):
    pass


def construir_body(slot: Slot, mensajes: list[dict], opciones: dict) -> dict:
    body = {"model": slot.modelo, "messages": mensajes}
    if slot.control == "effort" and opciones.get("effort"):
        body["reasoning"] = {"effort": opciones["effort"]}
    elif slot.control == "reasoning" and opciones.get("razonar"):
        body["reasoning"] = {"effort": "medium"}
    elif slot.control == "schema" and opciones.get("schema"):
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "respuesta", "strict": True,
                            "schema": opciones["schema"]},
        }
    return body


def mensajes_con_contexto(contexto: str, mensajes: list[dict]) -> list[dict]:
    """Antepone el bloque estatico marcado para que Anthropic lo cachee."""
    bloque = {
        "role": "system",
        "content": [{"type": "text", "text": contexto,
                     "cache_control": {"type": "ephemeral"}}],
    }
    return [bloque] + list(mensajes)


def contexto_estatico(base) -> str:
    base = Path(base)
    partes = [(base / n).read_text(encoding="utf-8") for n in ("mission.md", "SPEC.md")]
    return "\n\n".join(partes)
