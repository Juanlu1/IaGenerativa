"""Parte 2: agente con tool calling sobre los documentos y la API del hospital.

    python3 agente.py --preguntas datos/preguntas_agente_dev.jsonl --salida respuestas.jsonl

La API tiene que estar corriendo (`python3 api/servidor.py`). El contrato está en
SPEC_AGENTE.md.
"""
import asyncio

from langchain_core.tools import StructuredTool

import herramientas
from bucle_agente import argumentos, consumo_key, correr, crear_modelo

# Cada función de herramientas.py es una tool de LangChain; la descripción es su docstring.
TOOLS = [StructuredTool.from_function(f) for f in herramientas.HERRAMIENTAS]


if __name__ == "__main__":
    args = argumentos("agente")
    modelo = crear_modelo()
    herramientas.recuperador()  # carga el encoder una vez, antes de la primera pregunta
    asyncio.run(correr(args.preguntas, args.salida, modelo, TOOLS, args.log,
                       titulo="Corrida del benchmark — agente con tools de LangChain (parte 2)",
                       cabecera={"Herramientas": "funciones de `herramientas.py`, en el mismo proceso"},
                       medir_key=consumo_key))
