"""Entrega del grupo: el contrato que llama la cátedra (ver README.md, "El contrato de la entrega").

- construir_buscador(ruta_normas): el buscador de la Parte 2 (parte2/rag_buscador.py), armado con la carpeta recibida.
- construir_agente(): el AgenteJSON de admision/ejemplo.py con el mensaje de sistema de la configuración y un
  modelo_lote que corre todas las conversaciones activas en una sola llamada a vLLM.

La configuración sale de config.yaml, o del archivo que indique la variable de entorno CONFIG. HF_TOKEN se lee del
entorno; si hay un archivo .env al lado de este, se carga (sin pisar lo que ya está en el entorno).

Modo de prueba sin GPU: MODELO_FALSO=1 reemplaza el modelo por un guion fijo (leer_triage, buscar_normativa,
registrar_decision). Sirve para probar el circuito de punta a punta; sus fichas no significan nada.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from admision.ejemplo import AgenteJSON, _Partida

RAIZ = Path(__file__).resolve().parent
load_dotenv(RAIZ / ".env", override=False)


# --- configuración -----------------------------------------------------------------------------------------------

def ruta_config() -> Path:
    ruta = Path(os.environ.get("CONFIG") or "config.yaml")
    return ruta if ruta.is_absolute() else RAIZ / ruta


def cargar_config() -> dict:
    ruta = ruta_config()
    config = yaml.safe_load(ruta.read_text(encoding="utf-8"))
    config["_ruta"] = ruta
    return config


def ruta_prompt(config: dict) -> Path:
    ruta = Path(config["prompt"])
    return ruta if ruta.is_absolute() else config["_ruta"].parent / ruta


def leer_prompt(config: dict) -> str:
    return ruta_prompt(config).read_text(encoding="utf-8")


# --- buscador ----------------------------------------------------------------------------------------------------

def construir_buscador(ruta_normas):
    from parte2.rag_buscador import construir_buscador as construir

    return construir(ruta_normas)


# --- agente ------------------------------------------------------------------------------------------------------

class AgenteAdmision(AgenteJSON):
    """El AgenteJSON de la cátedra con dos cambios: el mensaje de sistema sale de la configuración, y si el modelo
    devuelve None para una conversación (porque ya no entra en el contexto), ese caso termina sin ficha en lugar de
    hacer caer el lote entero."""

    def __init__(self, modelo_lote, mensaje_de_sistema: str, max_turnos: int = 16, max_sin_json: int = 3):
        super().__init__(modelo_lote, max_turnos=max_turnos, max_sin_json=max_sin_json)
        self.mensaje_de_sistema = mensaje_de_sistema

    def jugar_lote(self, entornos: list) -> list[list[dict]]:
        partidas = [_Partida(e, self.max_turnos, self.max_sin_json) for e in entornos]
        for partida in partidas:
            partida.mensajes[0] = {"role": "system", "content": self.mensaje_de_sistema}
        while activas := [x for x in partidas if x.activa]:
            respuestas = self.modelo_lote([x.mensajes for x in activas])
            for partida, respuesta in zip(activas, respuestas, strict=True):
                if respuesta is None:
                    partida.activa = False
                else:
                    partida.recibir(respuesta)
        return [x.mensajes for x in partidas]


class ModeloVLLM:
    """modelo_lote con vLLM: una llamada a LLM.chat por vuelta, con todas las conversaciones activas."""

    def __init__(self, config: dict):
        from vllm import LLM, SamplingParams  # solo en Linux con GPU; en la Mac no está instalado

        argumentos = dict(config.get("vllm") or {})
        adaptador = (config.get("adaptador_lora") or "").strip()
        self.lora = None
        if adaptador:
            from huggingface_hub import snapshot_download
            from vllm.lora.request import LoRARequest

            revision = (config.get("adaptador_revision") or "").strip() or None
            ruta = snapshot_download(adaptador, revision=revision)
            self.lora = LoRARequest("adaptador", 1, ruta)
            argumentos.update(enable_lora=True, max_lora_rank=int(config.get("max_lora_rank", 32)), max_loras=1)

        self.llm = LLM(model=config["modelo"], revision=config.get("revision") or None,
                       tokenizer_revision=config.get("revision") or None, **argumentos)
        self.tokenizer = self.llm.get_tokenizer()
        generacion = dict(config.get("generacion") or {})
        self.max_tokens = int(generacion.get("max_tokens", 1024))
        self.max_model_len = int(argumentos.get("max_model_len") or self.llm.llm_engine.model_config.max_model_len)
        self.sampling = SamplingParams(temperature=float(generacion.get("temperature", 0.0)),
                                       max_tokens=self.max_tokens, seed=generacion.get("seed"))
        self.excedidas = 0

    def _largo(self, conversacion: list[dict]) -> int:
        texto = self.tokenizer.apply_chat_template(conversacion, tokenize=False, add_generation_prompt=True)
        return len(self.tokenizer.encode(texto, add_special_tokens=False))

    def __call__(self, conversaciones: list[list[dict]]) -> list[str | None]:
        # Una conversación que ya no entra en max_model_len haría fallar la llamada entera; esa se saca del lote y
        # su caso termina sin ficha (AgenteAdmision recibe None).
        entran = [self._largo(c) + self.max_tokens <= self.max_model_len for c in conversaciones]
        if not all(entran):
            self.excedidas += entran.count(False)
            print(f"[entrega] {entran.count(False)} conversaciones superan max_model_len={self.max_model_len}; "
                  "esos casos terminan sin ficha", file=sys.stderr)
        lote = [c for c, ok in zip(conversaciones, entran) if ok]
        salidas = iter(self.llm.chat(lote, self.sampling, lora_request=self.lora, use_tqdm=False,
                                     chat_template_kwargs={"enable_thinking": False}) if lote else [])
        return [next(salidas).outputs[0].text if ok else None for ok in entran]


class ModeloFalso:
    """Guion fijo para probar el circuito sin GPU: leer_triage, buscar_normativa y registrar_decision."""

    FICHA = {"registro": "provisorio", "numero_documento": None, "box_antes_del_registro": False,
             "circuito": "ninguno", "plazo_circuito_min": None, "cobertura": "sin_cobertura",
             "entidad_a_notificar": None, "aviso_al_voluntariado": False, "fundamentos": ["NOR-ADM-01"]}

    def _respuesta(self, conversacion: list[dict]) -> str:
        paso = sum(m["role"] == "assistant" for m in conversacion)
        if paso == 0:
            paciente = re.search(r"P-\d+", conversacion[1]["content"])
            llamada = {"herramienta": "leer_triage", "argumentos": {"paciente_id": paciente.group(0)}}
        elif paso == 1:
            llamada = {"herramienta": "buscar_normativa", "argumentos": {"consulta": "registro sin documento"}}
        else:
            llamada = {"herramienta": "registrar_decision", "argumentos": self.FICHA}
        return json.dumps(llamada, ensure_ascii=False)

    def __call__(self, conversaciones: list[list[dict]]) -> list[str]:
        return [self._respuesta(c) for c in conversaciones]


def construir_agente() -> AgenteAdmision:
    config = cargar_config()
    falso = os.environ.get("MODELO_FALSO", "").strip() not in ("", "0")
    print(f"[entrega] config={config['_ruta'].name} prompt={ruta_prompt(config).name} "
          f"modelo={'FALSO' if falso else config['modelo']}@{config.get('revision') or '-'} "
          f"adaptador={config.get('adaptador_lora') or '-'}@{config.get('adaptador_revision') or '-'}",
          file=sys.stderr)
    modelo = ModeloFalso() if falso else ModeloVLLM(config)
    return AgenteAdmision(modelo, leer_prompt(config), max_turnos=int(config.get("max_turnos", 16)),
                          max_sin_json=int(config.get("max_sin_json", 3)))
