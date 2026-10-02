"""Tests del servidor MCP y de su agente cliente (parte 3). Sin red y sin cargar el encoder."""
import ast
import asyncio
import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp.shared.memory import create_connected_server_and_client_session

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "api"))

import herramientas  # noqa: E402
import servidor_mcp  # noqa: E402
from bucle_agente import responder  # noqa: E402
from servidor import Handler  # noqa: E402  (api/servidor.py, sin modificar)

NOMBRES = ["buscar_documentos", "consultar_camas", "consultar_guardia",
           "consultar_turnos", "consultar_farmacia", "consultar_espera"]


@pytest.fixture
def api(monkeypatch):
    servidor = ThreadingHTTPServer(("localhost", 0), Handler)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    monkeypatch.setenv("HOSPITAL_API_URL", f"http://localhost:{servidor.server_port}")
    yield
    servidor.shutdown()
    servidor.server_close()


def con_sesion(corrutina):
    """Corre `corrutina(sesion)` contra el servidor, conectado en memoria."""
    async def _correr():
        async with create_connected_server_and_client_session(servidor_mcp.mcp._mcp_server) as sesion:
            return await corrutina(sesion)
    return asyncio.run(_correr())


def test_tools_list_publica_las_seis_con_su_docstring():
    tools = con_sesion(lambda s: s.list_tools()).tools
    assert [t.name for t in tools] == NOMBRES
    por_nombre = {f.__name__: f for f in herramientas.HERRAMIENTAS}
    for t in tools:
        assert t.description == por_nombre[t.name].__doc__


def test_los_parametros_son_los_del_enunciado():
    tools = {t.name: t for t in con_sesion(lambda s: s.list_tools()).tools}
    assert list(tools["buscar_documentos"].inputSchema["properties"]) == ["consulta"]
    assert list(tools["consultar_camas"].inputSchema["properties"]) == ["sector"]
    assert list(tools["consultar_farmacia"].inputSchema["properties"]) == ["medicamento"]
    assert tools["consultar_espera"].inputSchema["properties"] == {}


def test_tools_call_devuelve_el_json_de_la_api_como_texto(api):
    r = con_sesion(lambda s: s.call_tool("consultar_camas", {"sector": "pediatria"}))
    assert not r.isError
    assert json.loads(r.content[0].text)["datos"]["libres"] == 7


def test_tools_call_de_buscar_documentos_usa_el_recuperador(monkeypatch):
    class Falso:
        def buscar(self, consulta, k=None):
            return [f"fragmento para: {consulta}"]
    monkeypatch.setattr(herramientas, "_recuperador", Falso())
    r = con_sesion(lambda s: s.call_tool("buscar_documentos", {"consulta": "¿visitas?"}))
    assert r.content[0].text == "fragmento para: ¿visitas?"


def test_el_bucle_del_agente_funciona_con_las_tools_cargadas_por_mcp(api):
    """De punta a punta sin LLM: tools/list -> tools de LangChain -> tools/call -> contexto en texto."""
    class Modelo:
        guion = [AIMessage(content="", tool_calls=[{"name": "consultar_espera", "args": {}, "id": "c1",
                                                    "type": "tool_call"}]),
                 AIMessage(content="135 minutos.")]

        def bind_tools(self, tools):
            return self

        async def ainvoke(self, mensajes):
            return self.guion.pop(0)

    async def flujo(sesion):
        tools = await load_mcp_tools(sesion)
        return [t.name for t in tools], await responder(Modelo(), tools, "¿cuánto se espera?")

    nombres, r = con_sesion(flujo)
    assert nombres == NOMBRES
    assert r["herramientas"] == ["consultar_espera"] and r["respuesta"] == "135 minutos."
    assert json.loads(r["contextos"][0])["minutos_por_nivel"]["verde"] == 135


def test_el_agente_mcp_no_tiene_codigo_propio_de_herramientas():
    """SPEC_AGENTE.md: todo lo obtiene del servidor."""
    arbol = ast.parse((RAIZ / "agente_mcp.py").read_text(encoding="utf-8"))
    importados = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            importados |= {a.name.split(".")[0] for a in nodo.names}
        elif isinstance(nodo, ast.ImportFrom):
            importados.add(nodo.module.split(".")[0])
    assert not importados & {"herramientas", "recuperador", "urllib", "requests", "httpx"}


def test_el_servidor_no_usa_langchain():
    fuente = (RAIZ / "servidor_mcp.py").read_text(encoding="utf-8")
    assert "from mcp.server.fastmcp import FastMCP" in fuente and "import langchain" not in fuente
    assert "from langchain" not in fuente
