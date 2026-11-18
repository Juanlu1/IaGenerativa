"""App de Modal del agente: la evaluación (evaluar.py) y la optimización de prompt (optimizar_prompt.py) en una A100
de 40 GB. Se lanza desde la Mac; los comandos exactos están en MODAL.md.

    uv run modal run --detach modal_app.py::evaluar --etiqueta base
    uv run modal run --detach modal_app.py::evaluar --etiqueta prueba_base --cantidad 3
    uv run modal run --detach modal_app.py::evaluar --etiqueta prompt_optimizado --config config_optimizado.yaml
    uv run modal run --detach modal_app.py::evaluar --etiqueta prueba_falso --cantidad 3 --falso   # sin GPU
    uv run modal run --detach modal_app.py::gepa --etiqueta gepa1 --args "..."

- GPU: A100 de 40 GB, la misma que usa la cátedra.
- Secret "tp-secrets": HF_TOKEN (y WANDB_API_KEY, HF_REPO) como variables de entorno.
- Volume "tp-hf-cache": la caché de Hugging Face, para bajar Gemma una sola vez.
- Volume "tp-corridas": corridas y checkpoints. Las evaluaciones van a /corridas/<etiqueta>/ y la optimización de
  prompt a /corridas/gepa/<etiqueta>/, así `modal volume get` las baja a las mismas rutas que una corrida local.
- El código de esta carpeta se sube en cada corrida (sin .env, .venv, corridas ni datos de entrenamiento); las
  dependencias se instalan desde uv.lock y quedan en la imagen.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import modal

RAIZ = Path(__file__).resolve().parent
REMOTO = "/root/tp"
CACHE_HF = "/cache/huggingface"
VOLUMEN = "/vol"
GPU = "A100-40GB"
HORAS = 3600

cache_hf = modal.Volume.from_name("tp-hf-cache", create_if_missing=True)
corridas = modal.Volume.from_name("tp-corridas", create_if_missing=True)
secretos = modal.Secret.from_name("tp-secrets")

imagen = (
    # Imagen con el toolkit de CUDA 13.0, la misma versión que traen los wheels de torch 2.14 del lock: vLLM y
    # flashinfer compilan algunos kernels al vuelo y necesitan nvcc.
    modal.Image.from_registry("nvidia/cuda:13.0.2-devel-ubuntu24.04", add_python="3.12")
    .uv_sync(uv_project_dir=str(RAIZ))
    .env({"HF_HOME": CACHE_HF, "PYTHONUNBUFFERED": "1", "PYTHONPATH": REMOTO})
    .workdir(REMOTO)
    .add_local_dir(RAIZ, REMOTO, ignore=[
        ".env", ".venv", "**/__pycache__", "*.egg-info", ".git", "corridas", "historial", "entrenamiento", "curado",
        "datos",
    ])
)

app = modal.App("tp-admision", image=imagen)
comunes = dict(secrets=[secretos], volumes={CACHE_HF: cache_hf, VOLUMEN: corridas}, timeout=24 * HORAS)

ETIQUETA_VALIDA = re.compile(r"^[A-Za-z0-9._-]+$")


# --- en el contenedor ----------------------------------------------------------------------------------------------

def _correr_y_guardar(comando: list[str], env: dict[str, str], log: Path) -> int:
    """Corre el comando, muestra la salida en los logs de Modal y la copia en `log`; al final guarda los Volumes."""
    log.parent.mkdir(parents=True, exist_ok=True)
    print("$ " + " ".join(comando), flush=True)
    try:
        with log.open("w", encoding="utf-8") as archivo:
            proceso = subprocess.Popen(comando, cwd=REMOTO, env={**os.environ, **env}, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, bufsize=1)
            for linea in proceso.stdout:
                sys.stdout.write(linea)
                archivo.write(linea)
                archivo.flush()
            return proceso.wait()
    finally:
        corridas.commit()
        cache_hf.commit()


def _evaluar(etiqueta: str, cantidad: int, config: str, commit: str, falso: bool) -> int:
    destino = Path(VOLUMEN) / "corridas"
    env = {"CONFIG": config, "COMMIT_EVALUADO": commit, "CORRIDAS": str(destino)}
    if falso:
        env["MODELO_FALSO"] = "1"
    comando = [sys.executable, "evaluar.py", etiqueta] + ([str(cantidad)] if cantidad else [])
    return _correr_y_guardar(comando, env, destino / etiqueta / "modal.log")


@app.function(gpu=GPU, **comunes)
def evaluar_gpu(etiqueta: str, cantidad: int, config: str, commit: str) -> int:
    return _evaluar(etiqueta, cantidad, config, commit, falso=False)


@app.function(**comunes)
def evaluar_cpu(etiqueta: str, cantidad: int, config: str, commit: str) -> int:
    """Solo para el modelo falso: prueba la imagen, los Volumes y la bajada de resultados sin pagar GPU."""
    return _evaluar(etiqueta, cantidad, config, commit, falso=True)


@app.function(gpu=GPU, **comunes)
def gepa_gpu(etiqueta: str, argumentos: list[str], config: str, commit: str) -> int:
    salida = Path(VOLUMEN) / "corridas" / "gepa" / etiqueta
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "commit.txt").write_text(commit + "\n", encoding="utf-8")
    comando = [sys.executable, "optimizar_prompt.py", "--salida", str(salida), *argumentos]
    return _correr_y_guardar(comando, {"CONFIG": config, "COMMIT_EVALUADO": commit}, salida / "modal.log")


# --- en la Mac -----------------------------------------------------------------------------------------------------

def _commit_local() -> str:
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True, text=True,
                         check=True).stdout.strip()
    sucio = subprocess.run(["git", "status", "--porcelain", "--", "."], cwd=RAIZ, capture_output=True, text=True,
                           check=True).stdout.strip()
    if sucio:
        print("Aviso: hay cambios sin commitear; la corrida queda marcada así en corrida.json.", file=sys.stderr)
    return sha + (" (con cambios sin commitear)" if sucio else "")


def _validar(etiqueta: str, config: str) -> str:
    if not ETIQUETA_VALIDA.match(etiqueta):
        raise SystemExit("la etiqueta solo puede tener letras, números, punto, guion y guion bajo")
    config = config or os.environ.get("CONFIG") or "config.yaml"
    if Path(config).is_absolute() or not (RAIZ / config).is_file():
        raise SystemExit(f"{config} tiene que ser un archivo de esta carpeta (se sube con el código)")
    return config


@app.local_entrypoint()
def evaluar(etiqueta: str, cantidad: int = 0, config: str = "", falso: bool = False):
    """Corre los casos de práctica con las normas original, b y c, cargando el modelo una sola vez."""
    config = _validar(etiqueta, config)
    if cantidad < 0:
        raise SystemExit("cantidad tiene que ser 0 (todos los casos) o un entero positivo")
    funcion = evaluar_cpu if falso else evaluar_gpu
    estado = funcion.remote(etiqueta, cantidad, config, _commit_local())
    print(f"evaluar.py terminó con estado {estado}. Para bajar los resultados:\n"
          f"  uv run modal volume get --force tp-corridas /corridas/{etiqueta} corridas\n"
          f"  uv run python tabla.py")
    if estado:
        raise SystemExit(estado)


@app.local_entrypoint()
def gepa(etiqueta: str, args: str = "", config: str = ""):
    """Corre optimizar_prompt.py --salida /vol/corridas/gepa/<etiqueta> <args> en la A100."""
    config = _validar(etiqueta, config)
    if not (RAIZ / "optimizar_prompt.py").is_file():
        raise SystemExit("falta optimizar_prompt.py en esta carpeta")
    estado = gepa_gpu.remote(etiqueta, args.split(), config, _commit_local())
    print(f"optimizar_prompt.py terminó con estado {estado}. Para bajar los resultados:\n"
          f"  uv run modal volume get --force tp-corridas /corridas/gepa/{etiqueta} corridas/gepa")
    if estado:
        raise SystemExit(estado)
