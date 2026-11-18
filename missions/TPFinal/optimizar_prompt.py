"""Parte 3: optimiza el mensaje de sistema del agente con GEPA, con Gemma sin entrenar.

    uv run python optimizar_prompt.py --presupuesto prueba        # unos minutos
    uv run python optimizar_prompt.py                             # default: ~1,5 horas en una A100
    MODELO_FALSO=1 uv run python optimizar_prompt.py --presupuesto prueba --salida /tmp/gepa   # en la Mac

Qué hace:
- **Qué optimiza.** Solo el texto del mensaje de sistema. El resto es el agente de entrega.py tal cual: el mismo
  AgenteAdmision, el mismo formato de mensajes, el mismo buscador y el mismo modelo (vLLM con la configuración de
  CONFIG, por defecto config.yaml). El prompt de partida es el de esa configuración.
- **Casos.** Los de casos_optimizacion.py: filas correctas del historial con la ficha esperada calculada para las
  normas original, b y c. No usa los 50 casos de práctica, que quedan para la evaluación (evaluar.py). Se eligen con
  la semilla, sin repetir caso entre optimización y validación, y repartidos entre las tres versiones de las normas.
- **Métrica.** Por caso: controles aprobados / 9, jugando el caso en el entorno real de admision, menos
  `--penalizacion` por cada 1.000 tokens del prompt (tokenizer de Gemma). GEPA recibe además, en texto, qué controles
  fallaron, qué se esperaba, qué registró el agente y qué herramientas usó.
- **Reflexión.** Por defecto, la misma Gemma local. Con `--reflexion auto` (default), si hay ANTHROPIC_API_KEY usa
  Claude (claude-opus-5-5, SDK oficial) y si no, si hay OPENAI_API_KEY, un modelo de OpenAI por DSPy. Los modelos pagos
  se usan solo para desarrollar el prompt, nunca dentro del agente. La plantilla de reflexión prohíbe copiar valores
  numéricos de las normas al prompt, porque cambian en el test.
- **Salidas** en `--salida` (por defecto corridas/gepa): log.jsonl (cada candidato con su texto, su largo y su
  puntaje), resumen.json, prompt_optimizado.txt, config_optimizado.yaml y gepa_run/ (estado de GEPA). Salvo con
  --sin-copiar-a-raiz, copia prompt_optimizado.txt y config_optimizado.yaml a esta carpeta.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

import entrega
from admision.comparar import CONTROLES, comparar
from admision.entorno import Entorno, VistaDelAgente
from casos_optimizacion import VERSIONES, casos_del_historial
from evaluar import commit_actual

RAIZ = Path(__file__).resolve().parent
COMPONENTE = "mensaje_de_sistema"

PRESUPUESTOS = {
    # casos de optimización, casos de validación, llamadas a la métrica, minutos, casos por minilote
    "prueba": {"optimizacion": 6, "validacion": 6, "max_llamadas": 40, "max_minutos": 10, "minilote": 3},
    "completo": {"optimizacion": 90, "validacion": 45, "max_llamadas": 3000, "max_minutos": 90, "minilote": 6},
}

PLANTILLA_REFLEXION = """Le di a un agente de admisión de guardia de hospital este mensaje de sistema:
```
<curr_param>
```

Estos son casos que jugó con ese mensaje, con lo que hizo y una devolución sobre lo que salió mal:
```
<side_info>
```

Escribí un mensaje de sistema nuevo y mejor para el agente.

Reglas:
- Mantené las cinco herramientas con sus nombres y argumentos exactos, los ocho campos de registrar_decision con sus
  valores posibles y el protocolo: en cada turno, solo un objeto JSON {"herramienta": ..., "argumentos": {...}}.
- No copies valores numéricos de las normas (edades, niveles, minutos, dígitos): cambian de una versión de las normas a
  otra y en el test. El agente tiene que buscarlos con buscar_normativa en cada caso. Sí podés decir qué buscar y cuándo.
- Podés describir el procedimiento general (qué leer, qué preguntar, qué verificar, qué buscar y en qué orden) y las
  costumbres del hospital que la devolución deje ver.
- Cada token del mensaje se paga en cada llamada: escribilo corto y sin repetir.

Escribí solo el mensaje nuevo, dentro de un bloque ```."""


# --- datos -------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Ejemplo:
    caso: object       # admision.casos.Caso
    version: str       # original | b | c
    esperada: dict     # {"caso", "ficha", "verificacion"}


def elegir_ejemplos(n_opt: int, n_val: int, semilla: int) -> tuple[list[Ejemplo], list[Ejemplo], dict]:
    """Casos del historial sin repetir, mezclados con la semilla; la versión de las normas rota entre original, b
    y c."""
    casos, descartes = casos_del_historial()
    if n_opt + n_val > len(casos):
        raise SystemExit(f"se piden {n_opt + n_val} casos y hay {len(casos)}")
    rng = random.Random(semilla)
    elegidos = rng.sample(casos, n_opt + n_val)
    ejemplos = [Ejemplo(c, VERSIONES[i % len(VERSIONES)], esp[VERSIONES[i % len(VERSIONES)]])
                for i, (c, esp) in enumerate(elegidos)]
    info = {"disponibles": len(casos), "descartados": dict(descartes)}
    return ejemplos[:n_opt], ejemplos[n_opt:], info


# --- largo del prompt --------------------------------------------------------------------------------------------

class Medidor:
    """Tokens con el tokenizer del modelo de la configuración; si no se puede cargar, caracteres / 4."""

    def __init__(self, config: dict):
        try:
            from transformers import AutoTokenizer

            self._tok = AutoTokenizer.from_pretrained(config["modelo"], revision=config.get("revision") or None)
            self.metodo = f"tokenizer de {config['modelo']}@{config.get('revision') or 'main'}"
        except Exception as e:  # sin red o sin acceso al repositorio
            self._tok = None
            self.metodo = f"caracteres / 4 (no se pudo cargar el tokenizer: {type(e).__name__})"

    def __call__(self, texto: str) -> int:
        if self._tok is None:
            return round(len(texto) / 4)
        return len(self._tok.encode(texto, add_special_tokens=False))


# --- modelos de reflexión ----------------------------------------------------------------------------------------

def _bloque(texto: str) -> str:
    m = re.search(r"```[^\n]*\n(.*?)\n?```", texto, re.DOTALL)
    return m.group(1) if m else texto


class ReflexionLocal:
    """La misma Gemma que juega los casos (el LLM de vLLM de ModeloVLLM)."""

    def __init__(self, modelo, semilla: int, max_tokens: int = 2048):
        from vllm import SamplingParams

        self.modelo, self.semilla, self.max_tokens, self.llamadas = modelo, semilla, max_tokens, 0
        self._sampling = SamplingParams
        self.nombre = "local (la misma Gemma de la configuración)"

    def __call__(self, prompt) -> str:
        self.llamadas += 1
        mensajes = prompt if isinstance(prompt, list) else [{"role": "user", "content": prompt}]
        # Algo de temperatura para que las propuestas varíen; la semilla por llamada la hace reproducible.
        sampling = self._sampling(temperature=0.7, max_tokens=self.max_tokens, seed=self.semilla + self.llamadas)
        salida = self.modelo.llm.chat([mensajes], sampling, use_tqdm=False,
                                      chat_template_kwargs={"enable_thinking": False})
        return salida[0].outputs[0].text


class ReflexionAnthropic:
    """Claude por el SDK oficial de Anthropic (solo desarrollo)."""

    def __init__(self, modelo: str):
        import anthropic

        self.cliente, self.modelo = anthropic.Anthropic(), modelo
        self.nombre = f"anthropic:{modelo}"

    def __call__(self, prompt) -> str:
        mensajes = prompt if isinstance(prompt, list) else [{"role": "user", "content": prompt}]
        respuesta = self.cliente.beta.messages.create(
            model=self.modelo, max_tokens=16000, messages=mensajes, output_config={"effort": "high"},
            betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        if respuesta.stop_reason == "refusal":
            raise RuntimeError(f"el modelo de reflexión se negó: {respuesta.stop_details}")
        return "".join(b.text for b in respuesta.content if b.type == "text")


class ReflexionDSPy:
    """Un modelo de OpenAI por dspy.LM (litellm), solo desarrollo."""

    def __init__(self, modelo: str):
        import dspy

        self.lm, self.nombre = dspy.LM(modelo, max_tokens=16000), f"dspy:{modelo}"

    def __call__(self, prompt) -> str:
        mensajes = prompt if isinstance(prompt, list) else [{"role": "user", "content": prompt}]
        return self.lm(messages=mensajes)[0]


class ReflexionFalsa:
    """Para MODELO_FALSO: propone el mismo mensaje sin su último párrafo (o igual, si tiene uno solo)."""

    nombre = "falsa (saca el último párrafo)"

    def __call__(self, prompt) -> str:
        texto = prompt if isinstance(prompt, str) else prompt[-1]["content"]
        actual = _bloque(texto)
        parrafos = actual.split("\n\n")
        return "```\n" + "\n\n".join(parrafos[:-1] if len(parrafos) > 1 else parrafos) + "\n```"


def modelo_de_reflexion(tipo: str, nombre: str | None, modelo_agente, semilla: int, falso: bool):
    if falso:
        return ReflexionFalsa()
    if tipo == "auto":
        tipo = ("anthropic" if os.environ.get("ANTHROPIC_API_KEY")
                else "openai" if os.environ.get("OPENAI_API_KEY") else "local")
    if tipo == "anthropic":
        return ReflexionAnthropic(nombre or "claude-opus-5-5")
    if tipo == "openai":
        if not nombre:
            raise SystemExit("con --reflexion openai hay que indicar --modelo-reflexion, por ejemplo openai/<modelo>")
        return ReflexionDSPy(nombre)
    return ReflexionLocal(modelo_agente, semilla)


# --- adaptador de GEPA -------------------------------------------------------------------------------------------

def _resumen_llamadas(log: list[dict], limite: int = 160) -> list[str]:
    lineas = []
    for paso in log:
        args = json.dumps(paso["argumentos"], ensure_ascii=False)
        obs = str(paso["observacion"]).replace("\n", " ")
        if paso["herramienta"] != "leer_triage":  # el triage va entero: ahí está lo que decide la ficha
            obs = obs[:limite]
        lineas.append(f"{paso['herramienta']}({args[:400]}) -> {obs}")
    return lineas


def devolucion(resultado: dict, ejemplo: Ejemplo, log: list[dict], conversacion: list[dict]) -> str:
    """Qué controles fallaron y por qué, en texto, para el modelo de reflexión."""
    if resultado["obtenida"] is None:
        sin_json = sum(m["role"] == "user" and m["content"].startswith("No entendí") for m in conversacion)
        motivo = (f"respondió {sin_json} veces sin un JSON válido" if sin_json
                  else "no llegó a llamar a registrar_decision" if log else "no hizo ninguna llamada válida")
        return (f"Caso sin ficha: {motivo}. Aprobó 0 de 9 controles. Normas vigentes: versión {ejemplo.version}.")
    fallidos = [k for k in CONTROLES if not resultado["controles"][k]]
    if not fallidos:
        return "Caso resuelto: aprobó los 9 controles."
    partes = [f"Aprobó {9 - len(fallidos)} de 9 controles. Normas vigentes: versión {ejemplo.version}."]
    for campo in fallidos:
        if campo == "verificacion":
            v = ejemplo.esperada["verificacion"]
            hechas = [x["argumentos"] for x in log if x["herramienta"] == "verificar_afiliacion"]
            partes.append(f"- verificación: había que verificar {v['requerida'] or 'nada'}"
                          + (f" y no consultar a {', '.join(v['prohibidas'])}" if v["prohibidas"] else "")
                          + f"; verificó {hechas or 'nada'}.")
        else:
            partes.append(f"- {campo}: esperado {json.dumps(resultado['esperada'][campo], ensure_ascii=False)}, "
                          f"registró {json.dumps(resultado['obtenida'].get(campo), ensure_ascii=False)}.")
    buscadas = [x["argumentos"].get("consulta") for x in log if x["herramienta"] == "buscar_normativa"]
    partes.append(f"Búsquedas en las normas: {buscadas or 'ninguna'}.")
    return "\n".join(partes)


class AdaptadorAdmision:
    """GEPAAdapter: juega en lote los casos con el mensaje de sistema candidato y puntúa con el comparador del kit."""

    propose_new_texts = None  # usa la propuesta de GEPA, con PLANTILLA_REFLEXION

    def __init__(self, modelo, config: dict, medidor: Medidor, penalizacion: float, buscadores: dict):
        self.modelo, self.config, self.medidor = modelo, config, medidor
        self.penalizacion, self.buscadores = penalizacion, buscadores
        self.evaluaciones = 0

    def castigo(self, texto: str) -> float:
        return self.penalizacion * self.medidor(texto) / 1000

    def evaluate(self, batch: list[Ejemplo], candidate: dict[str, str], capture_traces: bool = False):
        from gepa.core.adapter import EvaluationBatch

        sistema = candidate[COMPONENTE]
        agente = entrega.AgenteAdmision(self.modelo, sistema, max_turnos=int(self.config.get("max_turnos", 16)),
                                        max_sin_json=int(self.config.get("max_sin_json", 3)))
        entornos = [Entorno(e.caso, self.buscadores[e.version]) for e in batch]
        vistas = [VistaDelAgente(e.caso.paciente_id, en.paso) for e, en in zip(batch, entornos)]
        try:
            conversaciones = agente.jugar_lote(vistas)
        except Exception as e:  # un lote que falla puntúa 0 en vez de cortar la optimización
            print(f"[optimizar] jugar_lote falló: {type(e).__name__}: {e}", file=sys.stderr, flush=True)
            conversaciones = [[] for _ in batch]
        castigo = self.castigo(sistema)
        salidas, puntajes, trayectorias = [], [], []
        for ejemplo, entorno, conversacion in zip(batch, entornos, conversaciones):
            r = comparar(ejemplo.esperada, entorno.decision, entorno.log)
            puntajes.append(r["parcial"] - castigo)
            salidas.append({"caso": ejemplo.caso.id, "version": ejemplo.version, "resuelto": r["resuelto"],
                            "parcial": r["parcial"], "decision": entorno.decision})
            if capture_traces:
                trayectorias.append({"ejemplo": ejemplo, "resultado": r, "log": entorno.log,
                                     "conversacion": conversacion})
        self.evaluaciones += len(batch)
        return EvaluationBatch(outputs=salidas, scores=puntajes,
                               trajectories=trayectorias if capture_traces else None)

    def make_reflective_dataset(self, candidate, eval_batch, components_to_update):
        registros = []
        for t in eval_batch.trajectories or []:
            e = t["ejemplo"]
            registros.append({
                "Entrada": f"Ingresó a la guardia el paciente {e.caso.paciente_id} (normas: versión {e.version}).",
                "Lo que hizo el agente": _resumen_llamadas(t["log"]),
                "Devolución": devolucion(t["resultado"], e, t["log"], t["conversacion"]),
            })
        return {COMPONENTE: registros}


# --- programa ----------------------------------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--presupuesto", choices=sorted(PRESUPUESTOS), default="completo")
    ap.add_argument("--casos-optimizacion", type=int, help="pisa el del presupuesto")
    ap.add_argument("--casos-validacion", type=int, help="pisa el del presupuesto")
    ap.add_argument("--max-llamadas", type=int, help="tope de casos jugados por GEPA; pisa el del presupuesto")
    ap.add_argument("--max-minutos", type=float, help="tope de tiempo; pisa el del presupuesto")
    ap.add_argument("--minilote", type=int, help="casos por minilote de reflexión; pisa el del presupuesto")
    ap.add_argument("--penalizacion", type=float, default=0.02,
                    help="puntos de métrica (escala 0-1) que se restan por cada 1.000 tokens del prompt")
    ap.add_argument("--reflexion", choices=["auto", "local", "anthropic", "openai"], default="auto")
    ap.add_argument("--modelo-reflexion", help="claude-opus-5-5 por defecto con anthropic; obligatorio con openai")
    ap.add_argument("--semilla", type=int, default=0)
    ap.add_argument("--salida", type=Path, default=RAIZ / "corridas" / "gepa")
    ap.add_argument("--sin-copiar-a-raiz", action="store_true",
                    help="no copia prompt_optimizado.txt y config_optimizado.yaml a esta carpeta")
    a = ap.parse_args()

    import gepa
    from gepa.utils.stop_condition import MaxMetricCallsStopper, TimeoutStopCondition

    p = dict(PRESUPUESTOS[a.presupuesto])
    for clave, valor in (("optimizacion", a.casos_optimizacion), ("validacion", a.casos_validacion),
                         ("max_llamadas", a.max_llamadas), ("max_minutos", a.max_minutos),
                         ("minilote", a.minilote)):
        if valor is not None:
            p[clave] = valor
    random.seed(a.semilla)
    salida = a.salida.resolve()
    if (salida / "gepa_run").exists():
        shutil.rmtree(salida / "gepa_run")  # cada corrida empieza de cero: misma semilla, mismo resultado
    salida.mkdir(parents=True, exist_ok=True)
    inicio = time.perf_counter()

    config = entrega.cargar_config()
    falso = os.environ.get("MODELO_FALSO", "").strip() not in ("", "0")
    prompt_inicial = entrega.leer_prompt(config)
    optimizacion, validacion, info_casos = elegir_ejemplos(p["optimizacion"], p["validacion"], a.semilla)
    print(f"[optimizar] {len(optimizacion)} casos de optimización y {len(validacion)} de validación del historial "
          f"({info_casos['disponibles']} disponibles); presupuesto {a.presupuesto}: {p}", flush=True)

    medidor = Medidor(config)
    modelo = entrega.ModeloFalso() if falso else entrega.ModeloVLLM(config)
    reflexion = modelo_de_reflexion(a.reflexion, a.modelo_reflexion, modelo, a.semilla, falso)
    buscadores = {v: entrega.construir_buscador(RAIZ / "normas" / v) for v in VERSIONES}
    adaptador = AdaptadorAdmision(modelo, config, medidor, a.penalizacion, buscadores)
    print(f"[optimizar] modelo={'FALSO' if falso else config['modelo']} reflexión={reflexion.nombre} "
          f"largo={medidor.metodo} prompt inicial={entrega.ruta_prompt(config).name} "
          f"({medidor(prompt_inicial)} tokens)", flush=True)

    resultado = gepa.optimize(
        seed_candidate={COMPONENTE: prompt_inicial}, trainset=optimizacion, valset=validacion, adapter=adaptador,
        reflection_lm=reflexion, reflection_prompt_template=PLANTILLA_REFLEXION,
        reflection_minibatch_size=p["minilote"], candidate_selection_strategy="pareto",
        stop_callbacks=[MaxMetricCallsStopper(p["max_llamadas"]), TimeoutStopCondition(p["max_minutos"] * 60)],
        run_dir=str(salida / "gepa_run"), seed=a.semilla, skip_perfect_score=False, display_progress_bar=False,
        raise_on_exception=True)

    # log.jsonl: cada candidato con su largo y su puntaje en validación (con y sin la penalización por largo).
    candidatos = []
    for i, cand in enumerate(resultado.candidates):
        texto = cand[COMPONENTE]
        castigo = adaptador.castigo(texto)
        subpuntajes = resultado.val_subscores[i]
        valores = list(subpuntajes.values()) if isinstance(subpuntajes, dict) else list(subpuntajes)
        candidatos.append({
            "candidato": i, "padres": resultado.parents[i], "tokens": medidor(texto), "caracteres": len(texto),
            "puntaje": round(resultado.val_aggregate_scores[i], 4),
            "controles_aprobados_medio": round(resultado.val_aggregate_scores[i] + castigo, 4),
            "resueltos_validacion": sum(round(v + castigo, 6) >= 1.0 for v in valores),
            "casos_validacion": len(valores), "texto": texto})
    with (salida / "log.jsonl").open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(c, ensure_ascii=False) + "\n" for c in candidatos)

    mejor = max(candidatos, key=lambda c: (c["puntaje"], -c["tokens"], -c["candidato"]))
    (salida / "prompt_optimizado.txt").write_text(mejor["texto"], encoding="utf-8")
    config_salida = {k: v for k, v in config.items() if not k.startswith("_")}
    config_salida["prompt"] = "prompt_optimizado.txt"
    encabezado = (f"# Generado por optimizar_prompt.py ({datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC), a partir de "
                  f"{config['_ruta'].name}. Solo cambia el prompt.\n")
    (salida / "config_optimizado.yaml").write_text(
        encabezado + yaml.safe_dump(config_salida, sort_keys=False, allow_unicode=True), encoding="utf-8")

    resumen = {
        "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit": os.environ.get("COMMIT_EVALUADO") or commit_actual(),
        "config": config["_ruta"].name, "prompt_inicial": entrega.ruta_prompt(config).name,
        "modelo": "FALSO" if falso else config["modelo"], "revision": config.get("revision"),
        "reflexion": reflexion.nombre, "largo": medidor.metodo, "semilla": a.semilla,
        "presupuesto": a.presupuesto, **p, "penalizacion_por_1000_tokens": a.penalizacion,
        "casos": {"origen": "casos_optimizacion.py (filas correctas del historial)", **info_casos,
                  "optimizacion": [[e.caso.id, e.version] for e in optimizacion],
                  "validacion": [[e.caso.id, e.version] for e in validacion]},
        "candidatos": len(candidatos), "casos_jugados": adaptador.evaluaciones,
        "segundos": round(time.perf_counter() - inicio, 1),
        "inicial": {k: candidatos[0][k] for k in ("tokens", "puntaje", "controles_aprobados_medio",
                                                  "resueltos_validacion", "casos_validacion")},
        "mejor": {k: mejor[k] for k in ("candidato", "tokens", "puntaje", "controles_aprobados_medio",
                                        "resueltos_validacion", "casos_validacion")},
    }
    (salida / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not a.sin_copiar_a_raiz and salida != RAIZ:
        shutil.copy(salida / "prompt_optimizado.txt", RAIZ / "prompt_optimizado.txt")
        shutil.copy(salida / "config_optimizado.yaml", RAIZ / "config_optimizado.yaml")
    print(f"[optimizar] {len(candidatos)} candidatos, {adaptador.evaluaciones} casos jugados en "
          f"{resumen['segundos']} s. Inicial: {resumen['inicial']}. Mejor: {resumen['mejor']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
