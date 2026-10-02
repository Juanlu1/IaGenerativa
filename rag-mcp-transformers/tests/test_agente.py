"""Tests del bucle del agente (partes 2 y 3). Sin red: el modelo es un guion de mensajes."""
import asyncio
import json
import subprocess
import sys
from pathlib import Path

from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import bucle_agente  # noqa: E402
from bucle_agente import a_texto, cargar_env, correr, responder  # noqa: E402


class ModeloFalso:
    """Devuelve, en orden, los mensajes del guion. Anota qué vio en cada llamada."""

    def __init__(self, guion):
        self.guion, self.vistos, self.tools = list(guion), [], None

    def bind_tools(self, tools):
        self.tools = tools
        return self

    async def ainvoke(self, mensajes):
        self.vistos.append(list(mensajes))
        return self.guion.pop(0)


def pide(*llamadas, usage=None):
    return AIMessage(content="", tool_calls=[{"name": n, "args": a, "id": f"c{i}", "type": "tool_call"}
                                             for i, (n, a) in enumerate(llamadas)],
                     response_metadata={"id": "gen-1", "token_usage": usage or {}})


def dice(texto, usage=None):
    return AIMessage(content=texto, response_metadata={"id": "gen-2", "token_usage": usage or {}})


def consultar_camas(sector: str) -> str:
    """Camas de un sector."""
    return json.dumps({"sector": sector, "libres": 7}, ensure_ascii=False)


def buscar_documentos(consulta: str) -> str:
    """Busca en los documentos."""
    return "Madre, padre o tutor pueden permanecer las 24 horas."


TOOLS = [StructuredTool.from_function(f) for f in (consultar_camas, buscar_documentos)]


def correr_responder(guion, pregunta="¿hay lugar?", **kw):
    modelo = ModeloFalso(guion)
    return asyncio.run(responder(modelo, TOOLS, pregunta, **kw)), modelo


def test_sin_herramientas_la_respuesta_es_el_texto_del_modelo():
    r, modelo = correr_responder([dice("Hola.")])
    assert r["respuesta"] == "Hola." and r["contextos"] == [] and r["herramientas"] == []
    assert [m.type for m in modelo.vistos[0]] == ["system", "human"]


def test_ejecuta_las_herramientas_y_junta_contextos_en_orden():
    r, modelo = correr_responder([
        pide(("consultar_camas", {"sector": "pediatria"}), ("buscar_documentos", {"consulta": "¿acompañantes?"})),
        dice("Hay 7 camas y te podés quedar."),
    ])
    assert r["herramientas"] == ["consultar_camas", "buscar_documentos"]
    assert r["contextos"] == ['{"sector": "pediatria", "libres": 7}',
                              "Madre, padre o tutor pueden permanecer las 24 horas."]
    assert r["respuesta"] == "Hay 7 camas y te podés quedar."
    # la segunda llamada al modelo ve los dos resultados
    assert [m.type for m in modelo.vistos[1]] == ["system", "human", "ai", "tool", "tool"]


def test_el_modelo_recibe_las_tools_disponibles():
    _, modelo = correr_responder([dice("ok")])
    assert [t.name for t in modelo.tools] == ["consultar_camas", "buscar_documentos"]


def test_herramienta_inexistente_o_con_argumentos_invalidos_no_corta_la_corrida():
    r, _ = correr_responder([
        pide(("consultar_quirofanos", {})),
        pide(("consultar_camas", {})),  # falta 'sector'
        dice("No tengo esa información."),
    ])
    assert "no existe" in r["contextos"][0] and "consultar_camas" in r["contextos"][0]
    assert r["contextos"][1].startswith("error al llamar a consultar_camas")
    assert r["herramientas"] == ["consultar_quirofanos", "consultar_camas"]
    assert r["respuesta"] == "No tengo esa información."


def test_al_llegar_al_tope_hace_una_ultima_llamada_para_responder():
    guion = [pide(("consultar_camas", {"sector": "x"})) for _ in range(2)] + [dice("Respondo con lo que tengo.")]
    r, modelo = correr_responder(guion, max_llamadas=2)
    assert r["respuesta"] == "Respondo con lo que tengo."
    assert len(modelo.vistos) == 3 and len(r["pasos"]) == 3


def test_a_texto_acepta_string_y_bloques_de_contenido_de_mcp():
    assert a_texto("hola") == "hola"
    assert a_texto([{"type": "text", "text": "uno"}, {"type": "text", "text": "dos"}]) == "uno\ndos"


def test_cargar_env_no_pisa_el_entorno_ni_lee_comentarios(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# comentario\nNUEVA_VAR_TEST=valor\nYA_ESTABA_TEST=del_archivo\n", encoding="utf-8")
    monkeypatch.delenv("NUEVA_VAR_TEST", raising=False)
    monkeypatch.setenv("YA_ESTABA_TEST", "del_entorno")
    cargar_env(env)
    import os
    assert os.environ["NUEVA_VAR_TEST"] == "valor" and os.environ["YA_ESTABA_TEST"] == "del_entorno"
    monkeypatch.delenv("NUEVA_VAR_TEST")


USAGE = {"prompt_tokens": 100, "completion_tokens": 20, "cost": 0.000123,
         "completion_tokens_details": {"reasoning_tokens": 5}}


def corrida(tmp_path, medir_key=None):
    preguntas = tmp_path / "p.jsonl"
    preguntas.write_text('{"id": "X2", "pregunta": "¿Hay lugar en pediatría?"}\n'
                         '{"id": "X1", "pregunta": "¿Qué tal?"}\n', encoding="utf-8")
    salida, log = tmp_path / "respuestas.jsonl", tmp_path / "logs" / "corrida.md"
    modelo = ModeloFalso([pide(("consultar_camas", {"sector": "pediatría"}), usage=USAGE),
                          dice("Sí, hay 7 camas.", usage=USAGE), dice("Bien.", usage=USAGE)])
    asyncio.run(correr(preguntas, salida, modelo, TOOLS, log, titulo="Corrida de prueba",
                       cabecera={"Herramientas": "de prueba"}, medir_key=medir_key))
    return preguntas, salida, log


def test_correr_escribe_el_contrato_en_orden_y_sin_escapar(tmp_path):
    _, salida, _ = corrida(tmp_path)
    filas = [json.loads(l) for l in salida.read_text(encoding="utf-8").splitlines()]
    assert [f["id"] for f in filas] == ["X2", "X1"]
    assert all(set(f) == {"id", "respuesta", "contextos", "herramientas"} for f in filas)
    assert filas[0]["herramientas"] == ["consultar_camas"] and filas[1]["contextos"] == []
    assert "pediatría" in salida.read_text(encoding="utf-8")


def test_el_log_tiene_pregunta_llamadas_resultados_respuesta_y_usage(tmp_path):
    lecturas = iter([0.5, 0.75])
    _, _, log = corrida(tmp_path, medir_key=lambda: next(lecturas))
    md = log.read_text(encoding="utf-8")
    assert "# Corrida de prueba" in md and "## X2 — ¿Hay lugar en pediatría?" in md
    assert '`consultar_camas({"sector": "pediatría"})`' in md
    assert '{"sector": "pediatría", "libres": 7}' in md
    assert "Sí, hay 7 camas." in md
    assert "generation id: `gen-1`" in md
    assert "100 tokens de entrada, 20 de salida (5 de razonamiento), costo USD 0.000123" in md
    assert "3 llamadas al modelo, 300 tokens de entrada, 60 de salida (15 de razonamiento), costo USD 0.000369" in md
    assert "- `consultar_camas`: Camas de un sector." in md
    assert "USD 0.500000 antes, USD 0.750000 después, diferencia USD 0.250000" in md


def test_la_salida_la_acepta_el_evaluador_oficial(tmp_path):
    """El evaluador valida el formato antes de llamar al juez: sin key, corta en ese punto."""
    preguntas, salida, _ = corrida(tmp_path)
    referencia = tmp_path / "ref.jsonl"
    referencia.write_text("".join(
        json.dumps({**json.loads(l), "herramientas_esperadas": ["consultar_camas"], "respuesta_referencia": "x"}) + "\n"
        for l in preguntas.read_text(encoding="utf-8").splitlines()), encoding="utf-8")
    out = subprocess.run([sys.executable, str(RAIZ / "evaluar" / "evaluar.py"), "agente",
                          "--preguntas", str(referencia), "--respuestas", str(salida)],
                         capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
    assert "falta la variable OPENROUTER_API_KEY" in out.stderr and "faltan respuestas" not in out.stderr


def test_el_modelo_y_el_prompt_son_los_del_contrato():
    assert bucle_agente.MODELO == "deepseek/deepseek-v4-flash-0731"
    assert "buscar_documentos" in bucle_agente.SISTEMA
