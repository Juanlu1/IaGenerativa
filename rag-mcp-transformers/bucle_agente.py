"""Lo común a los dos agentes (partes 2 y 3): modelo, bucle de tool calling, salida y log.

`agente.py` y `agente_mcp.py` solo difieren en de dónde sacan las tools de
LangChain que le pasan a `correr`. El contrato está en SPEC_AGENTE.md.
"""
import argparse
import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

RAIZ = Path(__file__).resolve().parent
MODELO = "deepseek/deepseek-v4-flash-0731"
OPENROUTER = "https://openrouter.ai/api/v1"
MAX_LLAMADAS = 6

SISTEMA = """Sos el asistente del Hospital Provincial Arroyo Claro. Respondés preguntas de pacientes y familiares.

Reglas:
1. No sabés nada del hospital por tu cuenta. Antes de responder, conseguí la información con las herramientas. Las normas y los procedimientos están en los documentos (buscar_documentos). El estado de hoy (camas, guardia, turnos, farmacia, espera) está en las herramientas consultar_*.
2. Si la pregunta tiene varias partes, usá una herramienta por cada parte. Muchas preguntas necesitan a la vez un dato de hoy y una norma de los documentos.
3. Respondé solo con lo que devolvieron las herramientas. No agregues datos, consejos ni suposiciones que no estén en esos resultados. Si un dato no aparece, decí que no tenés esa información.
4. Respondé todo lo que se preguntó, en español, de forma breve y directa, con los datos concretos (horarios, fechas, cantidades, nombres)."""


def cargar_env(ruta=RAIZ / ".env"):
    """Carga las variables de un .env sin pisar las que ya están en el entorno."""
    if not Path(ruta).exists():
        return
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        clave, igual, valor = linea.strip().partition("=")
        if igual and clave and not clave.startswith("#"):
            os.environ.setdefault(clave, valor.strip().strip("'\""))


def crear_modelo():
    cargar_env()
    key = os.environ.get("OPENROUTER_API_KEY") or exit("falta la variable OPENROUTER_API_KEY (ver .env.example)")
    return ChatOpenAI(model=MODELO, base_url=OPENROUTER, api_key=key, temperature=0)


def a_texto(contenido):
    """El contenido de un mensaje como texto: un string, o una lista de bloques de texto (MCP)."""
    if isinstance(contenido, str):
        return contenido
    return "\n".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in contenido)


async def _ejecutar(tools, llamada):
    tool = tools.get(llamada["name"])
    if tool is None:
        return f"error: la herramienta '{llamada['name']}' no existe (opciones: {', '.join(tools)})"
    try:
        return a_texto((await tool.ainvoke(llamada)).content)
    except Exception as e:  # argumentos inválidos o falla de la tool: el modelo ve el error y sigue
        return f"error al llamar a {llamada['name']}: {e}"


def _paso(mensaje, llamadas=()):
    meta = mensaje.response_metadata or {}
    return {"generation_id": meta.get("id"), "usage": meta.get("token_usage") or {},
            "texto": a_texto(mensaje.content), "llamadas": list(llamadas)}


async def responder(modelo, tools, pregunta, max_llamadas=MAX_LLAMADAS):
    """Corre el bucle de tool calling para una pregunta.

    `modelo` es un chat model de LangChain y `tools`, una lista de tools de LangChain.
    Devuelve respuesta, contextos y herramientas (el contrato de `mission.md`) más
    `pasos`, con el detalle de cada llamada al modelo para el log.
    """
    por_nombre = {t.name: t for t in tools}
    con_tools = modelo.bind_tools(tools)
    mensajes = [SystemMessage(SISTEMA), HumanMessage(pregunta)]
    contextos, herramientas, pasos = [], [], []
    for _ in range(max_llamadas):
        ai = await con_tools.ainvoke(mensajes)
        mensajes.append(ai)
        llamadas = []
        for llamada in ai.tool_calls:
            resultado = await _ejecutar(por_nombre, llamada)
            mensajes.append(ToolMessage(resultado, tool_call_id=llamada["id"]))
            contextos.append(resultado)
            herramientas.append(llamada["name"])
            llamadas.append({"nombre": llamada["name"], "args": llamada["args"], "resultado": resultado})
        pasos.append(_paso(ai, llamadas))
        if not ai.tool_calls:
            break
    else:
        # Se acabó el tope: una última llamada sin herramientas, para que responda con lo que tiene.
        ai = await modelo.ainvoke(mensajes)
        pasos.append(_paso(ai))
    return {"respuesta": a_texto(ai.content).strip(), "contextos": contextos,
            "herramientas": herramientas, "pasos": pasos}


# ---------------- salida y log ----------------

def leer_preguntas(ruta):
    return [json.loads(l) for l in Path(ruta).read_text(encoding="utf-8").splitlines() if l.strip()]


def consumo_key():
    """Consumo acumulado de la key en USD (`GET /api/v1/key`), o None si no se pudo leer."""
    try:
        pedido = urllib.request.Request(f"{OPENROUTER}/key",
                                        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"})
        with urllib.request.urlopen(pedido, timeout=20) as r:
            return json.loads(r.read())["data"]["usage"]
    except Exception:
        return None


def _tokens(usage):
    detalle = usage.get("completion_tokens_details") or {}
    return (usage.get("prompt_tokens") or 0, usage.get("completion_tokens") or 0,
            detalle.get("reasoning_tokens") or 0, usage.get("cost") or 0.0)


def _totales(pasos):
    filas = [_tokens(p["usage"]) for p in pasos]
    return [len(filas)] + [sum(f[i] for f in filas) for i in range(4)]


def _bloque(texto):
    cerca = "````" if "```" in texto else "```"
    return f"{cerca}text\n{texto}\n{cerca}"


def escribir_log(ruta, titulo, cabecera, tools, resultados):
    """Log `.md` de la corrida: cada pregunta, sus llamadas a herramientas, la respuesta y el usage."""
    total = _totales([p for r in resultados for p in r["pasos"]])
    md = [f"# {titulo}", ""]
    md += [f"- **{k}:** {v}" for k, v in cabecera.items()]
    md += [f"- **Totales:** {total[0]} llamadas al modelo, {total[1]} tokens de entrada, {total[2]} de salida "
           f"({total[3]} de razonamiento), costo USD {total[4]:.6f}", "",
           "## Herramientas que vio el modelo", ""]
    md += [f"- `{t.name}`: {t.description}" for t in tools]
    md += ["", "## Resumen por pregunta", "",
           "| Pregunta | Herramientas | Llamadas al modelo | Tokens entrada | Tokens salida | Razonamiento | Costo USD |",
           "|---|---|---|---|---|---|---|"]
    for r in resultados:
        t = _totales(r["pasos"])
        md.append(f"| {r['id']} | {', '.join(r['herramientas']) or '—'} | {t[0]} | {t[1]} | {t[2]} | {t[3]} | {t[4]:.6f} |")
    md.append(f"| **Total** | | {total[0]} | {total[1]} | {total[2]} | {total[3]} | {total[4]:.6f} |")
    for r in resultados:
        md += ["", f"## {r['id']} — {r['pregunta']}"]
        for n, paso in enumerate(r["pasos"], 1):
            entrada, salida, razonamiento, costo = _tokens(paso["usage"])
            md += ["", f"### Llamada al modelo {n}", "",
                   f"- generation id: `{paso['generation_id']}`",
                   f"- usage: {entrada} tokens de entrada, {salida} de salida ({razonamiento} de razonamiento), "
                   f"costo USD {costo:.6f}"]
            if paso["texto"] and paso["llamadas"]:
                md.append(f"- texto del modelo: {paso['texto']}")
            for llamada in paso["llamadas"]:
                args = json.dumps(llamada["args"], ensure_ascii=False)
                md += ["", f"**Herramienta:** `{llamada['nombre']}({args})`", "", "Resultado:", "",
                       _bloque(llamada["resultado"])]
        md += ["", "### Respuesta", "", _bloque(r["respuesta"])]
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta).write_text("\n".join(md) + "\n", encoding="utf-8")


async def correr(preguntas, salida, modelo, tools, log, titulo, cabecera=None, medir_key=None):
    """Responde cada pregunta, escribe `salida` (contrato de `mission.md`) y el log de la corrida."""
    inicio, antes = datetime.now(), medir_key() if medir_key else None
    resultados = []
    for p in leer_preguntas(preguntas):
        r = await responder(modelo, tools, p["pregunta"])
        resultados.append({"id": p["id"], "pregunta": p["pregunta"], **r})
        print(f"{p['id']}  {', '.join(r['herramientas']) or '(sin herramientas)'}", flush=True)
    Path(salida).write_text("".join(
        json.dumps({k: r[k] for k in ["id", "respuesta", "contextos", "herramientas"]}, ensure_ascii=False) + "\n"
        for r in resultados), encoding="utf-8")
    cabecera = {"Fecha": inicio.strftime("%Y-%m-%d %H:%M:%S"), "Modelo": f"`{MODELO}` por OpenRouter, temperatura 0",
                "Preguntas": f"`{preguntas}` ({len(resultados)})", "Salida": f"`{salida}`", **(cabecera or {})}
    if medir_key:
        despues = medir_key()
        if antes is not None and despues is not None:
            cabecera["Consumo de la key (`GET /api/v1/key`)"] = (
                f"USD {antes:.6f} antes, USD {despues:.6f} después, diferencia USD {despues - antes:.6f}")
    escribir_log(log, titulo, cabecera, tools, resultados)
    print(f"log: {log}")
    return resultados


def argumentos(nombre):
    """Los argumentos del contrato de `mission.md`, más `--log` opcional."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--preguntas", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--log", default=None, help="ruta del log .md (por defecto, logs/<fecha>-<hora>-<agente>.md)")
    args = ap.parse_args()
    args.log = args.log or str(RAIZ / "logs" / f"{datetime.now():%Y-%m-%d-%H%M%S}-{nombre}.md")
    return args
