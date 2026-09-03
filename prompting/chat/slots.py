"""Los 4 modelos del ejercicio 1 y la capacidad que ejercita cada uno."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Slot:
    numero: int
    modelo: str
    capacidad: str
    control: str


SLOTS: dict[int, Slot] = {
    1: Slot(1, "openai/gpt-5.6-luna", "Effort configurable", "effort"),
    2: Slot(2, "anthropic/claude-haiku-4.5", "Prompt caching explícito", "cache"),
    3: Slot(3, "google/gemini-3.7-flash", "Salidas estructuradas", "schema"),
    4: Slot(4, "deepseek/deepseek-v4-flash-0731", "El escalón barato", "reasoning"),
}


def get_slot(numero: int) -> Slot:
    if numero not in SLOTS:
        raise ValueError(f"slot inexistente: {numero} (validos: {sorted(SLOTS)})")
    return SLOTS[numero]
