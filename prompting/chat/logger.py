"""El log .md de cada conversacion: la evidencia de auditoria del ejercicio 2.

Se appendea turno por turno, no al cerrar: si el proceso muere, lo que ya
paso quedo escrito.
"""
from datetime import datetime
from pathlib import Path

from chat.slots import Slot
from chat.usage import Usage, moneda, mostrar


class LogConversacion:
    def __init__(self, carpeta, slot: Slot, inicio: datetime | None = None):
        self.slot = slot
        self.inicio = inicio or datetime.now()
        self.carpeta = Path(carpeta)
        nombre = f"{self.inicio:%Y-%m-%d-%H%M%S}-slot{slot.numero}.md"
        self.ruta = self.carpeta / nombre
        self._turno = 0

    def abrir(self) -> None:
        self.carpeta.mkdir(parents=True, exist_ok=True)
        self.ruta.write_text(
            f"# Conversación — {self.slot.modelo}\n"
            f"Inicio: {self.inicio:%Y-%m-%d %H:%M:%S} · "
            f"Slot {self.slot.numero} ({self.slot.capacidad})\n",
            encoding="utf-8",
        )

    def _append(self, texto: str) -> None:
        with self.ruta.open("a", encoding="utf-8") as f:
            f.write(texto)

    def usuario(self, texto: str) -> None:
        self._turno += 1
        self._append(f"\n## Turno {self._turno} · usuario\n\n{texto}\n")

    def asistente(self, texto: str, usage: Usage) -> None:
        tabla = (
            "\n| entrada | salida | razonamiento | cacheados | costo | descuento cache |\n"
            "|---|---|---|---|---|---|\n"
            f"| {mostrar(usage.prompt_tokens)} | {mostrar(usage.completion_tokens)} "
            f"| {mostrar(usage.reasoning_tokens)} | {mostrar(usage.cached_tokens)} "
            f"| {moneda(usage.cost)} | {moneda(usage.cache_discount)} |\n"
        )
        gid = f"\ngeneration id: {mostrar(usage.generation_id)}\n"
        self._append(f"\n## Turno {self._turno} · asistente\n\n{texto}\n{tabla}{gid}")

    def error(self, mensaje: str) -> None:
        self._append(f"\n## Turno {self._turno} · ERROR\n\n{mensaje}\n")
