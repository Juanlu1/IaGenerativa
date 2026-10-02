"""Parte 3: las seis herramientas del asistente como servidor MCP, por stdio.

    python3 servidor_mcp.py
    npx @modelcontextprotocol/inspector python3 servidor_mcp.py

No usa LangChain. Por stdio, la salida estándar es el canal del protocolo: acá
no se puede hacer `print`. El contrato está en SPEC_AGENTE.md.
"""
import threading

from mcp.server.fastmcp import FastMCP

import herramientas

mcp = FastMCP("hospital-arroyo-claro")

# Cada función de herramientas.py se registra con el decorador de FastMCP, que
# publica su nombre, sus parámetros y su docstring como descripción.
for funcion in herramientas.HERRAMIENTAS:
    mcp.tool()(funcion)


if __name__ == "__main__":
    # El encoder se carga de fondo: el servidor contesta `initialize` y `tools/list`
    # enseguida, y la primera `buscar_documentos` espera a que termine la carga.
    threading.Thread(target=herramientas.recuperador, daemon=True).start()
    mcp.run()
