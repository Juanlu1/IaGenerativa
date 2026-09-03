"""Cliente de OpenRouter.

Lo puro (armado del body, contexto estatico) esta separado de la llamada HTTP
para poder testearlo sin red y sin gastar creditos.
"""
import json
import urllib.error
import urllib.request
from pathlib import Path

from chat.slots import Slot
from chat.usage import normalizar

BASE = "https://openrouter.ai/api/v1"


class ErrorOpenRouter(Exception):
    pass


def construir_body(slot: Slot, mensajes: list[dict], opciones: dict) -> dict:
    body = {"model": slot.modelo, "messages": mensajes}
    if slot.control == "effort" and opciones.get("effort"):
        body["reasoning"] = {"effort": opciones["effort"]}
    elif slot.control == "reasoning" and "razonar" in opciones:
        # Omitir el parametro NO apaga el razonamiento: DeepSeek razona por
        # defecto. Para apagarlo hay que mandarlo explicitamente.
        body["reasoning"] = ({"effort": "medium"} if opciones["razonar"]
                             else {"enabled": False})
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


def leer_api_key(ruta_env) -> str:
    for linea in Path(ruta_env).read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        for sep in ("=", ":"):
            if sep in linea:
                clave, valor = linea.split(sep, 1)
                if clave.strip() == "OPENROUTER_API_KEY":
                    return valor.strip().strip('"').strip("'")
                break
    raise ErrorOpenRouter(f"No encontre OPENROUTER_API_KEY en {ruta_env}")


class Cliente:
    def __init__(self, api_key: str):
        self._headers = {"Authorization": f"Bearer {api_key}",
                         "Content-Type": "application/json"}

    def _pedir(self, url: str, body: dict | None = None, timeout: int = 180):
        datos = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=datos, headers=self._headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            detalle = e.read().decode(errors="replace")[:500]
            raise ErrorOpenRouter(f"HTTP {e.code}: {detalle}") from None
        except Exception as e:
            raise ErrorOpenRouter(f"Fallo la conexion: {e}") from None

    def completar(self, slot: Slot, mensajes: list[dict], opciones: dict):
        body = construir_body(slot, mensajes, opciones)
        r = self._pedir(f"{BASE}/chat/completions", body)
        try:
            texto = r["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise ErrorOpenRouter(f"Respuesta inesperada: {json.dumps(r)[:300]}") from None
        return texto, normalizar(r)

    def presupuesto(self) -> dict:
        d = self._pedir(f"{BASE}/key")["data"]
        return {"usage": d.get("usage"), "limit": d.get("limit"),
                "limit_remaining": d.get("limit_remaining")}
