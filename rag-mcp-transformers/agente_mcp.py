"""Parte 3: el mismo agente, con las herramientas servidas por MCP.

    python3 agente_mcp.py --preguntas datos/preguntas_agente_dev.jsonl --salida respuestas_mcp.jsonl

Levanta `servidor_mcp.py` por stdio, descubre sus herramientas con `tools/list`
y las llama con `tools/call`. No tiene código propio para consultar la API ni el
recuperador. El contrato está en SPEC_AGENTE.md.
"""
import asyncio
import os
import sys
from pathlib import Path

from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from bucle_agente import argumentos, consumo_key, correr, crear_modelo

SERVIDOR = Path(__file__).resolve().parent / "servidor_mcp.py"


def parametros_del_servidor():
    """Cómo lanzar el servidor: con este mismo Python y el entorno actual, menos la key."""
    entorno = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}
    return StdioServerParameters(command=sys.executable, args=[str(SERVIDOR)], env=entorno)


async def main(args):
    modelo = crear_modelo()
    async with stdio_client(parametros_del_servidor()) as (lectura, escritura):
        async with ClientSession(lectura, escritura) as sesion:
            await sesion.initialize()
            tools = await load_mcp_tools(sesion)  # tools/list; cada tool llama a tools/call
            await correr(args.preguntas, args.salida, modelo, tools, args.log,
                         titulo="Corrida del benchmark — agente con tools por MCP (parte 3)",
                         cabecera={"Herramientas": "descubiertas con `tools/list` en `servidor_mcp.py` (stdio) "
                                                   "y cargadas con `langchain-mcp-adapters`"},
                         medir_key=consumo_key)


if __name__ == "__main__":
    asyncio.run(main(argumentos("agente_mcp")))
