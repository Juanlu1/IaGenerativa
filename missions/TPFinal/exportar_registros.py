"""Baja a `corridas/` lo que de cada entrenamiento solo estaba en W&B y en Hugging Face.

Para cada run del proyecto de W&B de `entrenar.yaml` (también los que fallaron o se cortaron) escribe en
`corridas/<nombre del run>/`:

  wandb_history.jsonl   todas las filas de `run.scan_history()`: pérdidas de train y val, tasa de aprendizaje,
                        `_runtime` (segundos desde el arranque), VRAM y paso subido a HF, una fila por registro;
  wandb_system.jsonl    las métricas de sistema de la pestaña System (`run.history(stream="system")`): uso,
                        memoria, potencia y temperatura de la GPU, CPU y RAM, una fila por muestra;
  wandb_config.json     `run.config` completo (configuración de entrenamiento, comando, datos y sha256);
  wandb_run.json        id, nombre, estado, link, fechas y `run.summary`.

Y en `corridas/hf_etiquetas.json`, cada etiqueta del repo del adaptador (`adaptador_lora` de `config.yaml`, o
`HF_REPO`) con su commit, para citar puntos de control que ningún `revisiones.json` registró.

    uv run python exportar_registros.py              # W&B y HF
    uv run python exportar_registros.py --solo-wandb
    uv run python exportar_registros.py --solo-hf

Necesita estar logueado en W&B (`wandb login --host ...`) y en Hugging Face (`hf auth login`), o WANDB_API_KEY y
HF_TOKEN en el entorno. El servidor de W&B sale de WANDB_BASE_URL; si no está, del de este proyecto.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent
CORRIDAS = RAIZ / "corridas"
SERVIDOR_WANDB = "https://api.forge.coreweave.com"


def _json(datos) -> str:
    return json.dumps(datos, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n"


def exportar_wandb() -> None:
    import wandb

    cfg = yaml.safe_load((RAIZ / "entrenar.yaml").read_text(encoding="utf-8"))["wandb"]
    api = wandb.Api(overrides={"base_url": os.environ.get("WANDB_BASE_URL") or SERVIDOR_WANDB})
    entidad = os.environ.get("WANDB_ENTITY") or cfg.get("entidad") or api.default_entity
    proyecto = os.environ.get("WANDB_PROJECT") or cfg["proyecto"]
    for run in api.runs(f"{entidad}/{proyecto}", order="+created_at"):
        destino = CORRIDAS / run.name
        destino.mkdir(parents=True, exist_ok=True)
        filas = sorted(run.scan_history(), key=lambda fila: fila.get("_step", 0))
        with (destino / "wandb_history.jsonl").open("w", encoding="utf-8") as salida:
            for fila in filas:
                salida.write(json.dumps(fila, ensure_ascii=False, sort_keys=True, default=str) + "\n")
        sistema = sorted(run.history(samples=100_000, stream="system", pandas=False),
                         key=lambda fila: fila.get("_timestamp", 0))
        with (destino / "wandb_system.jsonl").open("w", encoding="utf-8") as salida:
            for fila in sistema:
                salida.write(json.dumps(fila, ensure_ascii=False, sort_keys=True, default=str) + "\n")
        (destino / "wandb_config.json").write_text(_json(dict(run.config)), encoding="utf-8")
        (destino / "wandb_run.json").write_text(_json({
            "id": run.id, "nombre": run.name, "estado": run.state, "url": run.url,
            "creado": run.created_at, "actualizado": getattr(run, "updated_at", None),
            "summary": dict(run.summary)}), encoding="utf-8")
        print(f"{run.id} {run.name} ({run.state}): {len(filas)} filas, {len(sistema)} de sistema"
              f" -> {destino.relative_to(RAIZ)}")


def exportar_hf() -> None:
    from huggingface_hub import HfApi

    config = yaml.safe_load((RAIZ / "config.yaml").read_text(encoding="utf-8"))
    repo = os.environ.get("HF_REPO") or config["adaptador_lora"]
    refs = HfApi().list_repo_refs(repo)
    etiquetas = {etiqueta.name: etiqueta.target_commit for etiqueta in refs.tags}
    salida = CORRIDAS / "hf_etiquetas.json"
    salida.write_text(_json({"repo": repo, "ramas": {r.name: r.target_commit for r in refs.branches},
                             "etiquetas": dict(sorted(etiquetas.items()))}), encoding="utf-8")
    print(f"{repo}: {len(etiquetas)} etiquetas -> {salida.relative_to(RAIZ)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument("--solo-wandb", action="store_true")
    grupo.add_argument("--solo-hf", action="store_true")
    args = parser.parse_args()
    if not args.solo_hf:
        exportar_wandb()
    if not args.solo_wandb:
        exportar_hf()


if __name__ == "__main__":
    main()
