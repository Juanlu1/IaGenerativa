"""Evalúa una etiqueta: carga el agente una sola vez y corre los casos de práctica con las normas original, b y c.

    uv run python evaluar.py <etiqueta> [cantidad_casos]

Lo usan evaluar_todo.sh (en la máquina local) y modal_app.py (en la A100 de Modal). Cada versión queda en
corridas/<etiqueta>/<version>/ con los mismos archivos que deja `admision.correr practica` (trazas.jsonl,
tiempos.json, resultados.jsonl y resumen.json), porque usa la misma función del kit (`admision.correr.correr`).

Diferencia con correr `admision.correr practica` tres veces: el modelo se carga una vez y se reutiliza en las tres
versiones, así que el `construir_agente` de cada tiempos.json da casi 0. El tiempo real de carga queda en
corridas/<etiqueta>/corrida.json, junto con el commit, la configuración, el prompt y el modelo usados. También puntúa
en el mismo proceso, después de jugar cada versión (las fichas esperadas se leen recién entonces).

La configuración es la de entrega.py (variable CONFIG); MODELO_FALSO=1 usa el guion fijo, sin GPU.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import entrega
from admision.casos import cargar_casos
from admision.correr import correr

RAIZ = Path(__file__).resolve().parent
VERSIONES = ("original", "b", "c")
ETIQUETA_VALIDA = re.compile(r"^[A-Za-z0-9._-]+$")


def commit_actual() -> str | None:
    """El commit de esta carpeta, con una marca si hay cambios sin commitear. None si no hay git (en Modal)."""
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True, text=True,
                             check=True).stdout.strip()
        sucio = subprocess.run(["git", "status", "--porcelain", "--", "."], cwd=RAIZ, capture_output=True,
                               text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    return sha + (" (con cambios sin commitear)" if sucio else "")


def _log(mensaje: str) -> None:
    print(f"[evaluar {datetime.now().strftime('%H:%M:%S')}] {mensaje}", flush=True)


def evaluar(etiqueta: str, cantidad: int | None = None, corridas: Path = RAIZ / "corridas",
            commit: str | None = None, al_cargar=None, al_terminar_version=None) -> int:
    """Corre las tres versiones y devuelve cuántas fallaron. `al_cargar` y `al_terminar_version` son ganchos sin
    argumentos (modal_app.py los usa para guardar los Volumes)."""
    if not ETIQUETA_VALIDA.match(etiqueta):
        raise ValueError("la etiqueta solo puede tener letras, números, punto, guion y guion bajo")
    if cantidad is not None and cantidad < 1:
        raise ValueError("cantidad_casos tiene que ser un entero positivo")

    config = entrega.cargar_config()
    destino = Path(corridas) / etiqueta
    destino.mkdir(parents=True, exist_ok=True)
    shutil.copy(config["_ruta"], destino)
    shutil.copy(entrega.ruta_prompt(config), destino)

    casos = cargar_casos(RAIZ / "practica" / "casos.jsonl")
    if cantidad is not None:
        casos = casos[:cantidad]
    falso = os.environ.get("MODELO_FALSO", "").strip() not in ("", "0")
    meta = {
        "etiqueta": etiqueta,
        "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit": commit or commit_actual(),
        "config": config["_ruta"].name,
        "prompt": entrega.ruta_prompt(config).name,
        "modelo": "FALSO" if falso else config["modelo"],
        "revision": config.get("revision"),
        "adaptador_lora": config.get("adaptador_lora") or None,
        "adaptador_revision": config.get("adaptador_revision") or None,
        "casos": len(casos),
        "construir_agente_segundos": None,
        "versiones": {},
    }

    def guardar_meta() -> None:
        (destino / "corrida.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    guardar_meta()
    _log(f"{etiqueta}: {len(casos)} casos, config={meta['config']}, prompt={meta['prompt']}, modelo={meta['modelo']}")
    inicio = time.perf_counter()
    agente = entrega.construir_agente()
    meta["construir_agente_segundos"] = round(time.perf_counter() - inicio, 3)
    guardar_meta()
    _log(f"agente cargado en {meta['construir_agente_segundos']} s")
    if al_cargar:
        al_cargar()

    # El kit llama a construir_agente en cada corrida; este módulo le devuelve siempre el agente ya cargado.
    con_agente_cargado = SimpleNamespace(construir_buscador=entrega.construir_buscador,
                                         construir_agente=lambda: agente)
    fallas = 0
    for version in VERSIONES:
        _log(f"{etiqueta} / {version}: jugando")
        salida = destino / version
        try:
            _, resumen = correr(con_agente_cargado, casos, RAIZ / "practica" / f"esperadas-{version}.jsonl",
                                RAIZ / "normas" / version, salida)
            meta["versiones"][version] = {"resueltos": resumen["resueltos"], "casos": resumen["casos"],
                                          "error": resumen.get("error")}
            fallas += bool(resumen.get("error"))
            _log(f"{etiqueta} / {version}: {resumen['resueltos']}/{resumen['casos']} resueltos"
                 + (f", error: {resumen['error']}" if resumen.get("error") else ""))
        except Exception as e:  # una versión que falla no corta las demás
            fallas += 1
            meta["versiones"][version] = {"error": f"{type(e).__name__}: {e}"}
            salida.mkdir(parents=True, exist_ok=True)
            (salida / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            _log(f"{etiqueta} / {version}: falló ({type(e).__name__}: {e})")
        guardar_meta()
        if al_terminar_version:
            al_terminar_version()
    return fallas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("etiqueta")
    ap.add_argument("cantidad_casos", nargs="?", type=int)
    a = ap.parse_args()
    try:
        return 1 if evaluar(a.etiqueta, a.cantidad_casos) else 0
    except ValueError as e:
        ap.error(str(e))


if __name__ == "__main__":
    sys.exit(main())
