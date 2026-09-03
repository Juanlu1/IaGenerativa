"""Servidor de la interfaz. La conversacion vive aca, en memoria."""
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from chat.logger import LogConversacion
from chat.openrouter import (Cliente, ErrorOpenRouter, contexto_estatico,
                             leer_api_key, mensajes_con_contexto)
from chat.slots import SLOTS, get_slot
from chat.usage import moneda, mostrar

CARPETAS = ("pruebas", "conway")


class Conversacion:
    """El estado de la conversacion en curso.

    El log se abre en el primer uso, no al arrancar el server: si no, cada
    arranque dejaria un .md vacio en la carpeta que es nuestra evidencia.
    """

    def __init__(self, base: Path):
        self.base = base
        self.slot = get_slot(1)
        self.carpeta = "pruebas"
        self.mensajes: list[dict] = []
        self.log: LogConversacion | None = None
        self.total_costo = 0.0
        self.total_entrada = 0
        self.total_salida = 0

    def asegurar_log(self) -> None:
        if self.log is None:
            self.log = LogConversacion(self.base / "logs" / self.carpeta, self.slot)
            self.log.abrir()

    def reiniciar(self, slot_numero: int, carpeta: str) -> None:
        self.slot = get_slot(slot_numero)
        self.carpeta = carpeta if carpeta in CARPETAS else "pruebas"
        self.mensajes = []
        self.log = None
        self.total_costo = 0.0
        self.total_entrada = 0
        self.total_salida = 0
        self.asegurar_log()

    def sumar(self, usage) -> None:
        self.total_costo += usage.cost or 0.0
        self.total_entrada += usage.prompt_tokens or 0
        self.total_salida += usage.completion_tokens or 0


def crear_app(base) -> Flask:
    base = Path(base)
    app = Flask(__name__)
    estado = Conversacion(base)

    def cliente() -> Cliente:
        key = os.environ.get("OPENROUTER_API_KEY") or leer_api_key(base / ".env")
        return Cliente(key)

    @app.get("/")
    def index():
        return render_template("index.html", slots=SLOTS.values())

    @app.post("/api/slot")
    def cambiar_slot():
        datos = request.get_json(force=True)
        estado.reiniciar(int(datos["slot"]), datos.get("carpeta", "pruebas"))
        return jsonify(slot=estado.slot.numero, mensajes=0, log=estado.log.ruta.name)

    @app.post("/api/chat")
    def chat():
        datos = request.get_json(force=True)
        texto = datos.get("mensaje", "")
        opciones = datos.get("opciones", {})
        estado.asegurar_log()
        estado.mensajes.append({"role": "user", "content": texto})
        estado.log.usuario(texto)

        envio = estado.mensajes
        if estado.slot.control == "cache" and opciones.get("contexto"):
            envio = mensajes_con_contexto(contexto_estatico(base), estado.mensajes)

        try:
            respuesta, usage = cliente().completar(estado.slot, envio, opciones)
        except ErrorOpenRouter as e:
            estado.log.error(str(e))
            return jsonify(error=str(e)), 502

        estado.mensajes.append({"role": "assistant", "content": respuesta})
        estado.log.asistente(respuesta, usage)
        estado.sumar(usage)
        return jsonify(
            respuesta=respuesta,
            usage={
                "entrada": mostrar(usage.prompt_tokens),
                "salida": mostrar(usage.completion_tokens),
                "razonamiento": mostrar(usage.reasoning_tokens),
                "cacheados": mostrar(usage.cached_tokens),
                "costo": moneda(usage.cost),
                "descuento": moneda(usage.cache_discount),
            },
            totales={"entrada": estado.total_entrada, "salida": estado.total_salida,
                     "costo": moneda(estado.total_costo)},
        )

    @app.post("/api/prompt-archivo")
    def prompt_archivo():
        ruta = Path(request.get_json(force=True).get("ruta", ""))
        if not ruta.is_file():
            return jsonify(error=f"No encontre el archivo: {ruta}"), 400
        return jsonify(texto=ruta.read_text(encoding="utf-8"))

    @app.get("/api/presupuesto")
    def presupuesto():
        try:
            return jsonify(cliente().presupuesto())
        except ErrorOpenRouter as e:
            return jsonify(error=str(e)), 502

    return app


if __name__ == "__main__":
    crear_app(Path(__file__).resolve().parent.parent).run(port=5000, debug=True)
