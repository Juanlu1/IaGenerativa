# Interfaz de chat (ejercicio 1) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Una página web local que chatea con los 4 modelos del enunciado vía OpenRouter, muestra el usage de cada respuesta y guarda un `.md` por conversación.

**Architecture:** Flask sirve una página única. La conversación vive en memoria del servidor. El cliente HTTP, la normalización del usage, el armado del body por slot y el logger son módulos separados con funciones puras, testeables sin red.

**Tech Stack:** Python 3.14, Flask 3.1, pytest 9.1, `urllib` de la stdlib para llamar a OpenRouter (sin `requests`).

**Spec:** [`DESIGN.md`](DESIGN.md) (el diseño) y [`SPEC.md`](SPEC.md) (los requisitos que se corrigen).

## Global Constraints

- Todo corre dentro de `prompting/.venv`. Nunca instalar al Python del sistema (Homebrew lo bloquea).
- Dependencias permitidas: `flask` y `pytest`. Nada más.
- La key sale de `prompting/.env` (`OPENROUTER_API_KEY`). **Nunca** se imprime, ni se loguea, ni se manda al navegador.
- Los tests **no llaman a la red** y no gastan créditos. Se usan respuestas de mentira.
- Todo campo del usage puede venir ausente. Ausente se muestra `—`, nunca revienta.
- `test_vida.py` no se toca.
- Un commit por tarea, en castellano, explicando el porqué.

---

### Task 1: Entorno y esqueleto

**Files:**
- Create: `prompting/requirements.txt`
- Create: `prompting/chat/__init__.py`
- Create: `prompting/tests/__init__.py`
- Create: `prompting/pytest.ini`
- Modify: `.gitignore` (raíz del repo)

**Interfaces:**
- Consumes: nada
- Produces: `.venv` con flask y pytest; `pytest` corre desde `prompting/`

- [ ] **Step 1: Crear el venv e instalar**

```bash
cd prompting
python3 -m venv .venv
.venv/bin/pip install flask pytest
```

- [ ] **Step 2: Congelar las dependencias**

```bash
.venv/bin/pip freeze > requirements.txt
```

- [ ] **Step 3: Ignorar el venv**

Agregar a `.gitignore` de la raíz del repo:

```
.venv/
__pycache__/
.pytest_cache/
```

- [ ] **Step 4: Crear los paquetes y la config de pytest**

```bash
mkdir -p chat tests
touch chat/__init__.py tests/__init__.py
```

`prompting/pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 5: Verificar que pytest corre**

Run: `cd prompting && .venv/bin/pytest -q`
Expected: `no tests ran` (sin errores de colección)

- [ ] **Step 6: Commit**

```bash
git add prompting/requirements.txt prompting/pytest.ini prompting/chat prompting/tests .gitignore
git commit -m "chore(prompting): entorno de la interfaz con flask y pytest en venv"
```

---

### Task 2: Los 4 slots

**Files:**
- Create: `prompting/chat/slots.py`
- Test: `prompting/tests/test_slots.py`

**Interfaces:**
- Consumes: nada
- Produces:
  - `Slot` (dataclass): `numero: int`, `modelo: str`, `capacidad: str`, `control: str`
  - `SLOTS: dict[int, Slot]` con las claves 1, 2, 3, 4
  - `get_slot(numero: int) -> Slot` — lanza `ValueError` si no existe
  - Valores de `control`: `"effort"`, `"cache"`, `"schema"`, `"reasoning"`

- [ ] **Step 1: Escribir el test que falla**

`prompting/tests/test_slots.py`:

```python
import pytest
from chat.slots import SLOTS, Slot, get_slot


def test_hay_exactamente_cuatro_slots():
    assert sorted(SLOTS) == [1, 2, 3, 4]


def test_cada_slot_es_de_un_proveedor_distinto():
    proveedores = [s.modelo.split("/")[0] for s in SLOTS.values()]
    assert len(set(proveedores)) == 4


def test_los_modelos_son_los_del_enunciado():
    assert SLOTS[1].modelo == "openai/gpt-5.6-luna"
    assert SLOTS[2].modelo == "anthropic/claude-haiku-4.5"
    assert SLOTS[3].modelo == "google/gemini-3.7-flash"
    assert SLOTS[4].modelo == "deepseek/deepseek-v4-flash-0731"


def test_cada_slot_declara_el_control_que_ejercita():
    assert SLOTS[1].control == "effort"
    assert SLOTS[2].control == "cache"
    assert SLOTS[3].control == "schema"
    assert SLOTS[4].control == "reasoning"


def test_get_slot_devuelve_el_slot():
    assert get_slot(3) is SLOTS[3]


def test_get_slot_con_numero_invalido_lanza_error():
    with pytest.raises(ValueError):
        get_slot(9)
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `cd prompting && .venv/bin/pytest tests/test_slots.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'chat.slots'`

- [ ] **Step 3: Implementar**

`prompting/chat/slots.py`:

```python
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
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `cd prompting && .venv/bin/pytest tests/test_slots.py -q`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add prompting/chat/slots.py prompting/tests/test_slots.py
git commit -m "feat(prompting): los 4 slots con la capacidad que ejercita cada uno"
```

---

### Task 3: Normalizar el usage

**Files:**
- Create: `prompting/chat/usage.py`
- Test: `prompting/tests/test_usage.py`

**Interfaces:**
- Consumes: nada
- Produces:
  - `Usage` (dataclass): `prompt_tokens`, `completion_tokens`, `reasoning_tokens`, `cached_tokens`, `cache_write_tokens`, `cost`, `cache_discount`, `generation_id`, `model`, `raw` — todos `| None` salvo `raw: dict`
  - `normalizar(respuesta: dict) -> Usage`
  - `mostrar(valor) -> str` — `None` da `"—"`
  - `moneda(valor) -> str` — `None` da `"—"`, si no `"$0.000008"` (6 decimales)

**Nota:** los datos de los tests son respuestas **reales** capturadas en la verificación del Paso 0. El caso sin `cache_discount` no es hipotético: es lo que devuelve DeepSeek cuando no hubo cache.

- [ ] **Step 1: Escribir el test que falla**

`prompting/tests/test_usage.py`:

```python
from chat.usage import Usage, normalizar, mostrar, moneda

RESPUESTA_REAL = {
    "id": "gen-1788403287-cuRGvN3vb9kzlchTAVoe",
    "model": "deepseek/deepseek-v4-flash-20260731",
    "usage": {
        "prompt_tokens": 18,
        "completion_tokens": 39,
        "total_tokens": 57,
        "cost": 8.19e-06,
        "prompt_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
        "completion_tokens_details": {"reasoning_tokens": 23},
    },
}


def test_normaliza_una_respuesta_real():
    u = normalizar(RESPUESTA_REAL)
    assert u.prompt_tokens == 18
    assert u.completion_tokens == 39
    assert u.reasoning_tokens == 23
    assert u.cached_tokens == 0
    assert u.cost == 8.19e-06
    assert u.generation_id == "gen-1788403287-cuRGvN3vb9kzlchTAVoe"
    assert u.model == "deepseek/deepseek-v4-flash-20260731"


def test_cache_discount_ausente_queda_en_none_no_en_cero():
    # Verificado contra la API: cuando no hubo cache, el campo no viene.
    u = normalizar(RESPUESTA_REAL)
    assert u.cache_discount is None


def test_respuesta_sin_ningun_detalle_no_revienta():
    u = normalizar({"id": "gen-x", "usage": {"prompt_tokens": 5}})
    assert u.prompt_tokens == 5
    assert u.completion_tokens is None
    assert u.reasoning_tokens is None
    assert u.cached_tokens is None


def test_respuesta_sin_usage_no_revienta():
    u = normalizar({"id": "gen-x"})
    assert u.prompt_tokens is None
    assert u.cost is None


def test_guarda_la_respuesta_cruda_para_el_informe():
    u = normalizar(RESPUESTA_REAL)
    assert u.raw is RESPUESTA_REAL


def test_mostrar_convierte_none_en_raya():
    assert mostrar(None) == "—"
    assert mostrar(0) == "0"
    assert mostrar(23) == "23"


def test_moneda_formatea_con_seis_decimales():
    assert moneda(None) == "—"
    assert moneda(8.19e-06) == "$0.000008"
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `cd prompting && .venv/bin/pytest tests/test_usage.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'chat.usage'`

- [ ] **Step 3: Implementar**

`prompting/chat/usage.py`:

```python
"""Normaliza el usage de OpenRouter.

Cualquier campo puede venir ausente segun el proveedor y segun si hubo cache.
Ausente se representa con None, y se muestra como raya. Nunca KeyError.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Usage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    reasoning_tokens: int | None = None
    cached_tokens: int | None = None
    cache_write_tokens: int | None = None
    cost: float | None = None
    cache_discount: float | None = None
    generation_id: str | None = None
    model: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def normalizar(respuesta: dict) -> Usage:
    u = respuesta.get("usage") or {}
    entrada = u.get("prompt_tokens_details") or {}
    salida = u.get("completion_tokens_details") or {}
    return Usage(
        prompt_tokens=u.get("prompt_tokens"),
        completion_tokens=u.get("completion_tokens"),
        reasoning_tokens=salida.get("reasoning_tokens"),
        cached_tokens=entrada.get("cached_tokens"),
        cache_write_tokens=entrada.get("cache_write_tokens"),
        cost=u.get("cost"),
        cache_discount=u.get("cache_discount"),
        generation_id=respuesta.get("id"),
        model=respuesta.get("model"),
        raw=respuesta,
    )


def mostrar(valor) -> str:
    return "—" if valor is None else str(valor)


def moneda(valor) -> str:
    return "—" if valor is None else f"${valor:.6f}"
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `cd prompting && .venv/bin/pytest tests/test_usage.py -q`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add prompting/chat/usage.py prompting/tests/test_usage.py
git commit -m "feat(prompting): normalizacion del usage tolerante a campos ausentes"
```

---

### Task 4: El log en Markdown

**Files:**
- Create: `prompting/chat/logger.py`
- Test: `prompting/tests/test_logger.py`

**Interfaces:**
- Consumes: `chat.slots.Slot`, `chat.usage.Usage`, `chat.usage.mostrar`, `chat.usage.moneda`
- Produces:
  - `LogConversacion(carpeta: Path, slot: Slot, inicio: datetime | None = None)`
  - `.ruta -> Path` — `<carpeta>/<YYYY-MM-DD-HHMMSS>-slot<N>.md`
  - `.abrir() -> None` — crea la carpeta si no existe y escribe el encabezado
  - `.usuario(texto: str) -> None` — incrementa el número de turno
  - `.asistente(texto: str, usage: Usage) -> None`
  - `.error(mensaje: str) -> None`

Cada método **appendea al archivo en el momento**. Si el proceso muere, lo ya escrito queda.

- [ ] **Step 1: Escribir el test que falla**

`prompting/tests/test_logger.py`:

```python
from datetime import datetime

from chat.logger import LogConversacion
from chat.slots import get_slot
from chat.usage import Usage

INICIO = datetime(2026, 9, 3, 14, 2, 11)


def nuevo_log(tmp_path, slot=2):
    return LogConversacion(tmp_path, get_slot(slot), inicio=INICIO)


def test_el_nombre_del_archivo_lleva_fecha_hora_y_slot(tmp_path):
    log = nuevo_log(tmp_path)
    assert log.ruta.name == "2026-09-03-140211-slot2.md"


def test_abrir_crea_el_archivo_con_el_encabezado(tmp_path):
    log = nuevo_log(tmp_path)
    log.abrir()
    texto = log.ruta.read_text(encoding="utf-8")
    assert "anthropic/claude-haiku-4.5" in texto
    assert "2026-09-03 14:02:11" in texto


def test_abrir_crea_la_carpeta_si_no_existe(tmp_path):
    destino = tmp_path / "logs" / "pruebas"
    log = LogConversacion(destino, get_slot(1), inicio=INICIO)
    log.abrir()
    assert log.ruta.exists()


def test_un_turno_completo_queda_escrito(tmp_path):
    log = nuevo_log(tmp_path)
    log.abrir()
    log.usuario("hola")
    log.asistente("qué tal", Usage(prompt_tokens=18, completion_tokens=39,
                                   reasoning_tokens=23, cached_tokens=0,
                                   cost=8.19e-06))
    texto = log.ruta.read_text(encoding="utf-8")
    assert "## Turno 1 · usuario" in texto
    assert "hola" in texto
    assert "## Turno 1 · asistente" in texto
    assert "qué tal" in texto
    assert "$0.000008" in texto


def test_el_segundo_turno_no_pisa_al_primero(tmp_path):
    log = nuevo_log(tmp_path)
    log.abrir()
    log.usuario("primero")
    log.asistente("uno", Usage(cost=1e-06))
    log.usuario("segundo")
    log.asistente("dos", Usage(cost=2e-06))
    texto = log.ruta.read_text(encoding="utf-8")
    assert "primero" in texto and "segundo" in texto
    assert "## Turno 2 · usuario" in texto


def test_los_campos_ausentes_se_escriben_como_raya(tmp_path):
    log = nuevo_log(tmp_path)
    log.abrir()
    log.usuario("hola")
    log.asistente("respuesta", Usage(prompt_tokens=10))
    assert "—" in log.ruta.read_text(encoding="utf-8")


def test_un_error_queda_registrado_en_el_log(tmp_path):
    log = nuevo_log(tmp_path)
    log.abrir()
    log.usuario("hola")
    log.error("HTTP 429: rate limited")
    assert "429" in log.ruta.read_text(encoding="utf-8")
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `cd prompting && .venv/bin/pytest tests/test_logger.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'chat.logger'`

- [ ] **Step 3: Implementar**

`prompting/chat/logger.py`:

```python
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
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `cd prompting && .venv/bin/pytest tests/test_logger.py -q`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add prompting/chat/logger.py prompting/tests/test_logger.py
git commit -m "feat(prompting): log .md por conversacion, appendeado turno a turno"
```

---

### Task 5: Armar el body por slot (puro, sin red)

**Files:**
- Create: `prompting/chat/openrouter.py`
- Test: `prompting/tests/test_openrouter.py`

**Interfaces:**
- Consumes: `chat.slots.Slot`, `chat.usage.normalizar`
- Produces:
  - `construir_body(slot: Slot, mensajes: list[dict], opciones: dict) -> dict`
  - `mensajes_con_contexto(contexto: str, mensajes: list[dict]) -> list[dict]`
  - `contexto_estatico(base: Path) -> str` — concatena `mission.md` y `SPEC.md`
  - `ErrorOpenRouter(Exception)`
  - `Cliente(api_key: str)` con `.completar(...)` y `.presupuesto()` (Task 6)

Esta tarea es solo lo puro. La parte que llama a la red va en la Task 6.

- [ ] **Step 1: Escribir el test que falla**

`prompting/tests/test_openrouter.py`:

```python
from chat.openrouter import construir_body, contexto_estatico, mensajes_con_contexto
from chat.slots import get_slot

MENSAJES = [{"role": "user", "content": "hola"}]


def test_el_body_siempre_lleva_modelo_y_mensajes():
    body = construir_body(get_slot(4), MENSAJES, {})
    assert body["model"] == "deepseek/deepseek-v4-flash-0731"
    assert body["messages"] == MENSAJES


def test_slot_1_manda_el_effort_elegido():
    body = construir_body(get_slot(1), MENSAJES, {"effort": "high"})
    assert body["reasoning"] == {"effort": "high"}


def test_slot_1_sin_effort_no_manda_reasoning():
    assert "reasoning" not in construir_body(get_slot(1), MENSAJES, {})


def test_slot_3_manda_el_schema_como_response_format():
    schema = {"type": "object", "properties": {"n": {"type": "integer"}}}
    body = construir_body(get_slot(3), MENSAJES, {"schema": schema})
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["schema"] == schema


def test_slot_4_con_razonamiento_prendido_manda_reasoning():
    body = construir_body(get_slot(4), MENSAJES, {"razonar": True})
    assert body["reasoning"] == {"effort": "medium"}


def test_slot_4_con_razonamiento_apagado_no_manda_reasoning():
    assert "reasoning" not in construir_body(get_slot(4), MENSAJES, {"razonar": False})


def test_el_contexto_estatico_va_primero_y_marcado_para_cachear():
    mensajes = mensajes_con_contexto("texto largo", MENSAJES)
    bloque = mensajes[0]["content"][0]
    assert mensajes[0]["role"] == "system"
    assert bloque["text"] == "texto largo"
    assert bloque["cache_control"] == {"type": "ephemeral"}
    assert mensajes[1:] == MENSAJES


def test_el_contexto_estatico_sale_de_los_archivos_del_repo(tmp_path):
    (tmp_path / "mission.md").write_text("enunciado", encoding="utf-8")
    (tmp_path / "SPEC.md").write_text("contrato", encoding="utf-8")
    texto = contexto_estatico(tmp_path)
    assert "enunciado" in texto and "contrato" in texto
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `cd prompting && .venv/bin/pytest tests/test_openrouter.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'chat.openrouter'`

- [ ] **Step 3: Implementar la parte pura**

`prompting/chat/openrouter.py`:

```python
"""Cliente de OpenRouter.

Lo puro (armado del body, contexto estatico) esta separado de la llamada HTTP
para poder testearlo sin red y sin gastar creditos.
"""
from pathlib import Path

from chat.slots import Slot


class ErrorOpenRouter(Exception):
    pass


def construir_body(slot: Slot, mensajes: list[dict], opciones: dict) -> dict:
    body = {"model": slot.modelo, "messages": mensajes}
    if slot.control == "effort" and opciones.get("effort"):
        body["reasoning"] = {"effort": opciones["effort"]}
    elif slot.control == "reasoning" and opciones.get("razonar"):
        body["reasoning"] = {"effort": "medium"}
    elif slot.control == "schema" and opciones.get("schema"):
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "respuesta", "strict": True,
                            "schema": opciones["schema"]},
        }
    return body


def mensajes_con_contexto(contexto: str, mensajes: list[dict]) -> list[dict]:
    """Antepone el bloque estatico marcado para que Anthropic lo cachee."""
    bloque = {
        "role": "system",
        "content": [{"type": "text", "text": contexto,
                     "cache_control": {"type": "ephemeral"}}],
    }
    return [bloque] + list(mensajes)


def contexto_estatico(base) -> str:
    base = Path(base)
    partes = [(base / n).read_text(encoding="utf-8") for n in ("mission.md", "SPEC.md")]
    return "\n\n".join(partes)
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `cd prompting && .venv/bin/pytest tests/test_openrouter.py -q`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add prompting/chat/openrouter.py prompting/tests/test_openrouter.py
git commit -m "feat(prompting): armado del body por slot, testeado sin tocar la red"
```

---

### Task 6: La llamada HTTP y el presupuesto

**Files:**
- Modify: `prompting/chat/openrouter.py`
- Test: `prompting/tests/test_openrouter.py` (agregar casos)

**Interfaces:**
- Consumes: lo de la Task 5
- Produces:
  - `Cliente(api_key: str)`
  - `.completar(slot, mensajes, opciones) -> tuple[str, Usage]` — lanza `ErrorOpenRouter` con el mensaje de la API
  - `.presupuesto() -> dict` con `usage`, `limit`, `limit_remaining`
  - `leer_api_key(ruta_env) -> str` — lee `OPENROUTER_API_KEY` de un `.env`, acepta `=` o `:` como separador

**Nota:** el `.env` real usa `:` en vez de `=` en algún caso; el parser acepta los dos para no fallar en silencio.

- [ ] **Step 1: Escribir el test que falla**

Agregar a `prompting/tests/test_openrouter.py`:

```python
import pytest
from chat.openrouter import ErrorOpenRouter, leer_api_key


def test_lee_la_key_con_igual(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OPENROUTER_API_KEY=sk-or-v1-abc\n", encoding="utf-8")
    assert leer_api_key(env) == "sk-or-v1-abc"


def test_lee_la_key_aunque_este_escrita_con_dos_puntos(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OPENROUTER_API_KEY: sk-or-v1-abc\n", encoding="utf-8")
    assert leer_api_key(env) == "sk-or-v1-abc"


def test_ignora_comentarios_y_lineas_vacias(tmp_path):
    env = tmp_path / ".env"
    env.write_text("# comentario\n\nOPENROUTER_API_KEY=sk-or-v1-abc\n", encoding="utf-8")
    assert leer_api_key(env) == "sk-or-v1-abc"


def test_sin_key_lanza_error_claro(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OTRA=cosa\n", encoding="utf-8")
    with pytest.raises(ErrorOpenRouter, match="OPENROUTER_API_KEY"):
        leer_api_key(env)
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `cd prompting && .venv/bin/pytest tests/test_openrouter.py -q`
Expected: FAIL — `ImportError: cannot import name 'leer_api_key'`

- [ ] **Step 3: Implementar**

Agregar a `prompting/chat/openrouter.py`:

```python
import json
import urllib.error
import urllib.request

from chat.usage import Usage, normalizar

BASE = "https://openrouter.ai/api/v1"


def leer_api_key(ruta_env) -> str:
    for linea in Path(ruta_env).read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        for sep in ("=", ":"):
            if sep in linea:
                clave, valor = linea.split(sep, 1)
                if clave.strip() == "OPENROUTER_API_KEY":
                    return valor.strip().strip('"').strip("'")
                break
    raise ErrorOpenRouter(f"No encontre OPENROUTER_API_KEY en {ruta_env}")


class Cliente:
    def __init__(self, api_key: str):
        self._headers = {"Authorization": f"Bearer {api_key}",
                         "Content-Type": "application/json"}

    def _pedir(self, url: str, body: dict | None = None, timeout: int = 180):
        datos = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=datos, headers=self._headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            detalle = e.read().decode(errors="replace")[:500]
            raise ErrorOpenRouter(f"HTTP {e.code}: {detalle}") from None
        except Exception as e:
            raise ErrorOpenRouter(f"Fallo la conexion: {e}") from None

    def completar(self, slot: Slot, mensajes: list[dict], opciones: dict):
        body = construir_body(slot, mensajes, opciones)
        r = self._pedir(f"{BASE}/chat/completions", body)
        try:
            texto = r["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise ErrorOpenRouter(f"Respuesta inesperada: {json.dumps(r)[:300]}") from None
        return texto, normalizar(r)

    def presupuesto(self) -> dict:
        d = self._pedir(f"{BASE}/key")["data"]
        return {"usage": d.get("usage"), "limit": d.get("limit"),
                "limit_remaining": d.get("limit_remaining")}
```

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `cd prompting && .venv/bin/pytest -q`
Expected: 0 failed (a esta altura hay 6 de slots, 7 de usage, 7 de logger y 12 de openrouter)

- [ ] **Step 5: Verificación manual contra la API real (una llamada, ~USD 0.00001)**

```bash
cd prompting && .venv/bin/python -c "
from pathlib import Path
from chat.openrouter import Cliente, leer_api_key
from chat.slots import get_slot
c = Cliente(leer_api_key(Path('.env')))
print('presupuesto:', c.presupuesto())
texto, u = c.completar(get_slot(4), [{'role':'user','content':'Decime solo: ok'}], {'razonar': True})
print('respuesta:', texto[:60])
print('usage:', u.prompt_tokens, u.completion_tokens, u.reasoning_tokens, u.cost)
"
```
Expected: imprime el presupuesto, una respuesta corta, y tokens con costo. **La key nunca se imprime.**

- [ ] **Step 6: Commit**

```bash
git add prompting/chat/openrouter.py prompting/tests/test_openrouter.py
git commit -m "feat(prompting): cliente HTTP de OpenRouter y lectura del presupuesto de la key"
```

---

### Task 7: El servidor con una conversación

**Files:**
- Create: `prompting/chat/app.py`
- Create: `prompting/chat/templates/index.html`

**Interfaces:**
- Consumes: todo lo anterior
- Produces:
  - `crear_app(base: Path) -> Flask`
  - Estado en memoria: `slot` actual, `mensajes`, `log`, `totales`
  - Rutas: `GET /`, `POST /api/chat`, `POST /api/slot`, `GET /api/presupuesto`, `POST /api/prompt-archivo`

- [ ] **Step 1: Escribir el test que falla**

`prompting/tests/test_app.py`:

```python
from pathlib import Path

import pytest

from chat.app import crear_app


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-falsa")
    app = crear_app(tmp_path)
    app.config["TESTING"] = True
    return app.test_client()


def test_la_pagina_carga_y_lista_los_cuatro_modelos(cliente):
    html = cliente.get("/").get_data(as_text=True)
    for modelo in ("gpt-5.6-luna", "claude-haiku-4.5",
                   "gemini-3.7-flash", "deepseek-v4-flash"):
        assert modelo in html


def test_cambiar_de_slot_empieza_conversacion_nueva(cliente):
    r = cliente.post("/api/slot", json={"slot": 2, "carpeta": "pruebas"})
    datos = r.get_json()
    assert datos["slot"] == 2
    assert datos["mensajes"] == 0
    assert datos["log"].endswith(".md")


def test_cambiar_de_slot_crea_el_log_en_la_carpeta_elegida(cliente, tmp_path):
    cliente.post("/api/slot", json={"slot": 1, "carpeta": "conway"})
    assert list((tmp_path / "logs" / "conway").glob("*.md"))


def test_carga_el_prompt_desde_un_archivo_del_disco(cliente, tmp_path):
    archivo = tmp_path / "prompt-conway.txt"
    archivo.write_text("contrato largo del ejercicio 2", encoding="utf-8")
    r = cliente.post("/api/prompt-archivo", json={"ruta": str(archivo)})
    assert r.get_json()["texto"] == "contrato largo del ejercicio 2"


def test_pedir_un_archivo_inexistente_da_error_claro(cliente, tmp_path):
    r = cliente.post("/api/prompt-archivo", json={"ruta": str(tmp_path / "no-existe.txt")})
    assert r.status_code == 400
    assert "no-existe.txt" in r.get_json()["error"]
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `cd prompting && .venv/bin/pytest tests/test_app.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'chat.app'`

- [ ] **Step 3: Implementar**

`prompting/chat/app.py`:

```python
"""Servidor de la interfaz. La conversacion vive aca, en memoria."""
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from chat.logger import LogConversacion
from chat.openrouter import (Cliente, ErrorOpenRouter, contexto_estatico,
                             leer_api_key, mensajes_con_contexto)
from chat.slots import SLOTS, get_slot
from chat.usage import moneda, mostrar


class Conversacion:
    def __init__(self, base: Path):
        self.base = base
        self.slot = get_slot(1)
        self.mensajes: list[dict] = []
        self.log: LogConversacion | None = None
        self.total_costo = 0.0
        self.total_entrada = 0
        self.total_salida = 0

    def reiniciar(self, slot_numero: int, carpeta: str) -> None:
        self.slot = get_slot(slot_numero)
        self.mensajes = []
        self.total_costo = 0.0
        self.total_entrada = 0
        self.total_salida = 0
        destino = self.base / "logs" / (carpeta if carpeta in ("pruebas", "conway") else "pruebas")
        self.log = LogConversacion(destino, self.slot)
        self.log.abrir()

    def sumar(self, usage) -> None:
        self.total_costo += usage.cost or 0.0
        self.total_entrada += usage.prompt_tokens or 0
        self.total_salida += usage.completion_tokens or 0


def crear_app(base) -> Flask:
    base = Path(base)
    app = Flask(__name__)
    estado = Conversacion(base)
    estado.reiniciar(1, "pruebas")

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
        return jsonify(slot=estado.slot.numero, mensajes=0,
                       log=estado.log.ruta.name)

    @app.post("/api/chat")
    def chat():
        datos = request.get_json(force=True)
        texto = datos.get("mensaje", "")
        opciones = datos.get("opciones", {})
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
```

- [ ] **Step 4: Crear la página**

`prompting/chat/templates/index.html`:

```html
<!doctype html>
<meta charset="utf-8">
<title>Chat multi-modelo — OpenRouter</title>
<style>
  body { font: 15px/1.5 system-ui, sans-serif; margin: 0; display: flex; height: 100vh; }
  main { flex: 1; display: flex; flex-direction: column; padding: 1rem; overflow: hidden; }
  aside { width: 300px; background: #f4f4f5; padding: 1rem; overflow-y: auto; }
  #conversacion { flex: 1; overflow-y: auto; border: 1px solid #ddd; padding: .75rem; }
  .turno { margin-bottom: 1rem; }
  .rol { font-weight: 600; font-size: .8rem; text-transform: uppercase; color: #666; }
  .texto { white-space: pre-wrap; }
  .usage { font-size: .8rem; color: #444; background: #fafafa; padding: .4rem; margin-top: .3rem; }
  .error { color: #b00; }
  textarea { width: 100%; height: 6rem; font: inherit; }
  table { border-collapse: collapse; width: 100%; font-size: .8rem; margin-top: .5rem; }
  th, td { border: 1px solid #ccc; padding: .25rem .4rem; text-align: right; }
  th:first-child, td:first-child { text-align: left; }
  #aviso { background: #fee; color: #900; padding: .5rem; display: none; }
</style>

<main>
  <div>
    <label>Modelo:
      <select id="slot">
        {% for s in slots %}
        <option value="{{ s.numero }}">Slot {{ s.numero }} — {{ s.modelo }} ({{ s.capacidad }})</option>
        {% endfor %}
      </select>
    </label>
    <label>Log en:
      <select id="carpeta">
        <option value="pruebas">logs/pruebas</option>
        <option value="conway">logs/conway</option>
      </select>
    </label>
    <span id="archivo-log"></span>
  </div>

  <div id="controles">
    <label class="ctl" data-slot="1">Effort:
      <select id="effort"><option>low</option><option selected>medium</option><option>high</option></select>
    </label>
    <label class="ctl" data-slot="2">
      <input type="checkbox" id="contexto" checked> Adjuntar contexto estático (cacheable)
    </label>
    <label class="ctl" data-slot="4">
      <input type="checkbox" id="razonar" checked> Razonamiento
    </label>
    <div class="ctl" data-slot="3">
      JSON Schema:
      <textarea id="schema">{"type":"object","properties":{"respuesta":{"type":"string"},"confianza":{"type":"number"}},"required":["respuesta"]}</textarea>
    </div>
  </div>

  <div id="conversacion"></div>

  <div>
    <textarea id="mensaje" placeholder="Escribí el mensaje..."></textarea>
    <input id="ruta" placeholder="…o pegá la ruta de un archivo con el prompt" size="45">
    <button id="cargar">Cargar archivo</button>
    <button id="enviar">Enviar</button>
  </div>
</main>

<aside>
  <div id="aviso">Presupuesto bajo: queda menos de USD 0.20.</div>
  <h3>Conversación</h3>
  <div id="totales">sin mensajes</div>
  <h3>Presupuesto de la key</h3>
  <div id="presupuesto">…</div>
  <h3>Demos</h3>
  <button class="demo" data-demo="effort">Effort (slot 1)</button>
  <button class="demo" data-demo="cache">Cache (slot 2)</button>
  <button class="demo" data-demo="precio">Precio (slots 2 y 4)</button>
  <div id="resultado-demo"></div>
</aside>

<script>
const $ = (id) => document.getElementById(id);
const conv = $("conversacion");

function pintarControles() {
  const n = $("slot").value;
  document.querySelectorAll(".ctl").forEach(e => {
    e.style.display = (e.dataset.slot === n) ? "block" : "none";
  });
}

function agregarTurno(rol, texto, usage) {
  const div = document.createElement("div");
  div.className = "turno";
  div.innerHTML = `<div class="rol">${rol}</div><div class="texto"></div>`;
  div.querySelector(".texto").textContent = texto;
  if (usage) {
    const u = document.createElement("div");
    u.className = "usage";
    u.textContent = `entrada ${usage.entrada} · salida ${usage.salida} · razonamiento ${usage.razonamiento}`
      + ` · cacheados ${usage.cacheados} · costo ${usage.costo} · descuento ${usage.descuento}`;
    div.appendChild(u);
  }
  conv.appendChild(div);
  conv.scrollTop = conv.scrollHeight;
}

async function cambiarSlot() {
  const r = await fetch("/api/slot", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({slot: Number($("slot").value), carpeta: $("carpeta").value})
  });
  const d = await r.json();
  conv.innerHTML = "";
  $("totales").textContent = "sin mensajes";
  $("archivo-log").textContent = "log: " + d.log;
  pintarControles();
}

function opciones() {
  const n = $("slot").value;
  if (n === "1") return {effort: $("effort").value};
  if (n === "2") return {contexto: $("contexto").checked};
  if (n === "4") return {razonar: $("razonar").checked};
  if (n === "3") { try { return {schema: JSON.parse($("schema").value)}; }
                   catch (e) { alert("El JSON Schema no es JSON válido"); return null; } }
  return {};
}

async function enviar() {
  const texto = $("mensaje").value.trim();
  const op = opciones();
  if (!texto || op === null) return;
  agregarTurno("usuario", texto, null);
  $("mensaje").value = "";
  const r = await fetch("/api/chat", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({mensaje: texto, opciones: op})
  });
  const d = await r.json();
  if (d.error) { agregarTurno("error", d.error, null); return; }
  agregarTurno("asistente", d.respuesta, d.usage);
  $("totales").textContent =
    `entrada ${d.totales.entrada} · salida ${d.totales.salida} · costo ${d.totales.costo}`;
  refrescarPresupuesto();
}

async function refrescarPresupuesto() {
  const d = await (await fetch("/api/presupuesto")).json();
  if (d.error) { $("presupuesto").textContent = d.error; return; }
  $("presupuesto").textContent =
    `gastado $${d.usage} de $${d.limit} · queda $${d.limit_remaining}`;
  $("aviso").style.display = (d.limit_remaining < 0.20) ? "block" : "none";
}

async function correrDemo(nombre) {
  $("resultado-demo").textContent = "corriendo…";
  const r = await fetch("/api/demo/" + nombre, {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({})
  });
  const d = await r.json();
  if (d.error) { $("resultado-demo").textContent = d.error; return; }
  const filas = d.filas.map(f =>
    `<tr><td>${f.etiqueta}</td><td>${f.entrada}</td><td>${f.salida}</td>`
    + `<td>${f.razonamiento}</td><td>${f.cacheados}</td><td>${f.costo}</td><td>${f.segundos}s</td></tr>`
  ).join("");
  $("resultado-demo").innerHTML =
    `<table><tr><th>caso</th><th>in</th><th>out</th><th>razon.</th>`
    + `<th>cache</th><th>costo</th><th>tiempo</th></tr>${filas}</table>`;
  refrescarPresupuesto();
}

$("slot").onchange = cambiarSlot;
$("carpeta").onchange = cambiarSlot;
$("enviar").onclick = enviar;
$("cargar").onclick = async () => {
  const r = await fetch("/api/prompt-archivo", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ruta: $("ruta").value})
  });
  const d = await r.json();
  if (d.error) { alert(d.error); return; }
  $("mensaje").value = d.texto;
};
document.querySelectorAll(".demo").forEach(b => b.onclick = () => correrDemo(b.dataset.demo));

pintarControles();
refrescarPresupuesto();
</script>
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `cd prompting && .venv/bin/pytest -q`
Expected: 0 failed

- [ ] **Step 6: Probar a mano**

```bash
cd prompting && .venv/bin/python -m chat.app
```
Abrir `http://localhost:5000`, mandar un mensaje al slot 4, ver la respuesta con su usage, y confirmar que apareció el `.md` en `logs/pruebas/`.

- [ ] **Step 7: Commit**

```bash
git add prompting/chat/app.py prompting/chat/templates/index.html prompting/tests/test_app.py
git commit -m "feat(prompting): interfaz de chat con usage por respuesta y log automatico"
```

---

### Task 8: Los 3 demos

**Files:**
- Create: `prompting/chat/demos.py`
- Modify: `prompting/chat/app.py` (agregar `POST /api/demo/<nombre>`)
- Modify: `prompting/chat/templates/index.html` (tres botones)
- Test: `prompting/tests/test_demos.py`

**Interfaces:**
- Consumes: `Cliente`, `get_slot`, `contexto_estatico`, `mensajes_con_contexto`, `LogConversacion`
- Produces:
  - `demo_effort(cliente, log, pregunta) -> list[dict]` — una fila por effort
  - `demo_cache(cliente, log, contexto, pregunta) -> list[dict]` — dos filas: primera y segunda pasada
  - `demo_precio(cliente, log, pregunta) -> list[dict]` — una fila por slot (2 y 4)
  - Cada fila: `{"etiqueta", "entrada", "salida", "razonamiento", "cacheados", "costo", "segundos"}`

**Nota:** los tests usan un cliente falso (una clase con `.completar()` que devuelve respuestas fijas). Ningún test llama a la red.

- [ ] **Step 1: Escribir el test que falla**

`prompting/tests/test_demos.py`:

```python
from datetime import datetime

from chat.demos import demo_cache, demo_effort, demo_precio
from chat.logger import LogConversacion
from chat.slots import get_slot
from chat.usage import Usage


class ClienteFalso:
    """Devuelve una respuesta fija y anota con que opciones lo llamaron."""

    def __init__(self, usages):
        self.usages = list(usages)
        self.llamadas = []

    def completar(self, slot, mensajes, opciones):
        self.llamadas.append((slot.numero, opciones))
        return "respuesta", self.usages.pop(0)


def log_en(tmp_path):
    log = LogConversacion(tmp_path, get_slot(1), inicio=datetime(2026, 9, 3, 12, 0, 0))
    log.abrir()
    return log


def test_demo_effort_corre_los_tres_niveles(tmp_path):
    c = ClienteFalso([Usage(cost=1e-6, reasoning_tokens=10),
                      Usage(cost=2e-6, reasoning_tokens=50),
                      Usage(cost=3e-6, reasoning_tokens=200)])
    filas = demo_effort(c, log_en(tmp_path), "cuanto es 2+2")
    assert [o["effort"] for _, o in c.llamadas] == ["low", "medium", "high"]
    assert [f["etiqueta"] for f in filas] == ["low", "medium", "high"]
    assert filas[2]["razonamiento"] == "200"


def test_demo_cache_manda_el_mismo_contexto_dos_veces(tmp_path):
    c = ClienteFalso([Usage(prompt_tokens=5000, cached_tokens=0, cost=5e-3),
                      Usage(prompt_tokens=5000, cached_tokens=4900, cost=1e-3)])
    filas = demo_cache(c, log_en(tmp_path), "contexto largo", "resumilo")
    assert len(c.llamadas) == 2
    assert filas[0]["cacheados"] == "0"
    assert filas[1]["cacheados"] == "4900"


def test_demo_precio_pregunta_a_los_slots_2_y_4(tmp_path):
    c = ClienteFalso([Usage(cost=5e-3), Usage(cost=3.25e-4)])
    filas = demo_precio(c, log_en(tmp_path), "hola")
    assert [n for n, _ in c.llamadas] == [2, 4]
    assert len(filas) == 2


def test_los_demos_dejan_todo_escrito_en_el_log(tmp_path):
    log = log_en(tmp_path)
    c = ClienteFalso([Usage(cost=1e-6), Usage(cost=2e-6), Usage(cost=3e-6)])
    demo_effort(c, log, "pregunta")
    texto = log.ruta.read_text(encoding="utf-8")
    assert texto.count("· asistente") == 3
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `cd prompting && .venv/bin/pytest tests/test_demos.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'chat.demos'`

- [ ] **Step 3: Implementar**

`prompting/chat/demos.py`:

```python
"""Los tres demos que hacen visibles los criterios de exito del ejercicio 1."""
import time

from chat.openrouter import mensajes_con_contexto
from chat.slots import get_slot
from chat.usage import moneda, mostrar

EFFORTS = ("low", "medium", "high")


def _fila(etiqueta, usage, segundos):
    return {
        "etiqueta": etiqueta,
        "entrada": mostrar(usage.prompt_tokens),
        "salida": mostrar(usage.completion_tokens),
        "razonamiento": mostrar(usage.reasoning_tokens),
        "cacheados": mostrar(usage.cached_tokens),
        "costo": moneda(usage.cost),
        "segundos": f"{segundos:.1f}",
    }


def _turno(cliente, log, slot, mensajes, opciones, etiqueta):
    log.usuario(f"[{etiqueta}] {mensajes[-1]['content']}")
    t0 = time.monotonic()
    texto, usage = cliente.completar(slot, mensajes, opciones)
    segundos = time.monotonic() - t0
    log.asistente(texto, usage)
    return _fila(etiqueta, usage, segundos)


def demo_effort(cliente, log, pregunta):
    slot = get_slot(1)
    mensajes = [{"role": "user", "content": pregunta}]
    return [_turno(cliente, log, slot, mensajes, {"effort": e}, e) for e in EFFORTS]


def demo_cache(cliente, log, contexto, pregunta):
    slot = get_slot(2)
    mensajes = mensajes_con_contexto(contexto, [{"role": "user", "content": pregunta}])
    return [_turno(cliente, log, slot, mensajes, {"contexto": True}, etiqueta)
            for etiqueta in ("primera pasada", "segunda pasada")]


def demo_precio(cliente, log, pregunta):
    mensajes = [{"role": "user", "content": pregunta}]
    return [_turno(cliente, log, get_slot(n), mensajes, {}, f"slot {n}")
            for n in (2, 4)]
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `cd prompting && .venv/bin/pytest tests/test_demos.py -q`
Expected: 4 passed

- [ ] **Step 5: Conectar los demos a la app**

Agregar a `prompting/chat/app.py`:

```python
from chat.demos import demo_cache, demo_effort, demo_precio

    @app.post("/api/demo/<nombre>")
    def demo(nombre):
        datos = request.get_json(force=True)
        pregunta = datos.get("pregunta", "Explicá en una línea qué es un autómata celular.")
        c = cliente()
        try:
            if nombre == "effort":
                filas = demo_effort(c, estado.log, pregunta)
            elif nombre == "cache":
                filas = demo_cache(c, estado.log, contexto_estatico(base), pregunta)
            elif nombre == "precio":
                filas = demo_precio(c, estado.log, pregunta)
            else:
                return jsonify(error=f"demo desconocido: {nombre}"), 404
        except ErrorOpenRouter as e:
            estado.log.error(str(e))
            return jsonify(error=str(e)), 502
        return jsonify(filas=filas)
```

Y tres botones en `index.html` que llaman a esas rutas y pintan las filas como tabla.

- [ ] **Step 6: Correr toda la suite**

Run: `cd prompting && .venv/bin/pytest -q`
Expected: 0 failed

- [ ] **Step 7: Commit**

```bash
git add prompting/chat/demos.py prompting/chat/app.py prompting/chat/templates/index.html prompting/tests/test_demos.py
git commit -m "feat(prompting): demos de effort, cache y precio como evidencia reproducible"
```

---

### Task 9: Los 4 logs de prueba (la entrega del ejercicio 1)

**Files:**
- Create: `prompting/logs/pruebas/*.md` (cuatro, uno por modelo)
- Modify: `prompting/README.md` (marcar el estado)

**Interfaces:**
- Consumes: la interfaz terminada
- Produces: la evidencia que pide la entrega

- [ ] **Step 1: Levantar el servidor**

```bash
cd prompting && .venv/bin/python -m chat.app
```

- [ ] **Step 2: Una conversación por modelo**

Con cada uno de los 4 slots, carpeta `pruebas`: mandar 2 o 3 mensajes y confirmar que el usage aparece debajo de cada respuesta.

- [ ] **Step 3: Correr el demo de effort (slot 1)**

Deja registrado el efecto de cambiar el effort, que es criterio de éxito.

- [ ] **Step 4: Correr el demo de cache (slot 2)**

Verificar que la segunda pasada muestra `cached_tokens > 0` y menor costo de entrada. **Si no hay cache hit, el contexto estático es muy corto**: agrandarlo repitiendo el bloque hasta pasar el mínimo cacheable de Anthropic, y volver a correr.

- [ ] **Step 5: Correr el demo de precio (slots 2 y 4)**

- [ ] **Step 6: Verificar los 4 archivos**

```bash
ls -la prompting/logs/pruebas/
```
Expected: al menos 4 `.md`, uno por slot, cada uno con tablas de usage.

- [ ] **Step 7: Anotar el gasto**

```bash
cd prompting && .venv/bin/python -c "
from pathlib import Path
from chat.openrouter import Cliente, leer_api_key
print(Cliente(leer_api_key(Path('.env'))).presupuesto())
"
```
Guardar el número: es el punto de partida de la contabilidad del ejercicio 3.

- [ ] **Step 8: Commit**

```bash
git add prompting/logs/pruebas prompting/README.md
git commit -m "docs(prompting): logs de prueba de los 4 modelos con su usage"
```
