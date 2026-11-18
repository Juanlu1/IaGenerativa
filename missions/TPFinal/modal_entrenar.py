"""Entrenamiento de la Parte 4 en Modal: entrenar.py en una A100 de 40 GB.

    modal run --detach modal_entrenar.py --corrida sft-v1
    modal run --detach modal_entrenar.py --corrida prueba-gpu --max-pasos 20
    modal run --detach modal_entrenar.py --corrida sft-v1b --retomar hf:sft-v1-paso-200
    modal run modal_entrenar.py::bajar_modelo        # opcional: llena la caché sin GPU

Volúmenes:
  tp-hf-cache   caché de Hugging Face (HF_HOME): Gemma se baja una sola vez.
  tp-corridas   una carpeta por corrida, igual que corridas/<corrida> en local.

El secret de Modal `tp-secrets` trae HF_TOKEN, WANDB_API_KEY y HF_REPO. Los
comandos para ver los logs y bajar los resultados están en modal_entrenamiento.md.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

import modal

AQUI = Path(__file__).resolve().parent
REMOTO = "/root/tp"
HF_CACHE = "/cache/hf"
CORRIDAS = "/corridas"
COMMIT_CADA_SEG = 600  # guarda el volumen cada 10 minutos mientras entrena

app = modal.App("tp-admision-entrenar")
volumen_hf = modal.Volume.from_name("tp-hf-cache", create_if_missing=True)
volumen_corridas = modal.Volume.from_name("tp-corridas", create_if_missing=True)
secretos = [modal.Secret.from_name("tp-secrets")]

imagen = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_requirements(str(AQUI / "deps_entrenamiento.txt"))
    .env({"HF_HOME": HF_CACHE, "TOKENIZERS_PARALLELISM": "false", "PYTHONUNBUFFERED": "1"})
    # Solo lo que usa el entrenamiento: el código, la configuración y los datos.
    .add_local_file(str(AQUI / "entrenar.py"), f"{REMOTO}/entrenar.py")
    .add_local_file(str(AQUI / "entrenar.yaml"), f"{REMOTO}/entrenar.yaml")
    .add_local_dir(str(AQUI / "datos"), f"{REMOTO}/datos", ignore=["prueba*", "**/prueba*"])
)


@app.function(image=imagen, gpu="A100-40GB", secrets=secretos, timeout=24 * 3600,
              volumes={HF_CACHE: volumen_hf, CORRIDAS: volumen_corridas})
def entrenar(argumentos: list[str], corrida: str, conservar_checkpoints: bool = False) -> None:
    comando = ["python", "entrenar.py", *argumentos, "--corrida", corrida, "--salida", CORRIDAS]
    print("$", " ".join(comando), flush=True)
    proceso = subprocess.Popen(comando, cwd=REMOTO)
    ultimo = time.time()
    while proceso.poll() is None:
        time.sleep(15)
        if time.time() - ultimo > COMMIT_CADA_SEG:
            volumen_corridas.commit()
            volumen_hf.commit()
            ultimo = time.time()
    salida = Path(CORRIDAS) / corrida
    if proceso.returncode == 0 and not conservar_checkpoints:
        # Los puntos de control ya están en HF_REPO (con el estado para retomar):
        # se borran del volumen para que bajar la corrida sea liviano.
        for carpeta in ("checkpoints", "subida", "retomado"):
            shutil.rmtree(salida / carpeta, ignore_errors=True)
    volumen_corridas.commit()
    volumen_hf.commit()
    if proceso.returncode != 0:
        raise RuntimeError(f"entrenar.py terminó con código {proceso.returncode}; ver los logs de la app")
    print(f"Listo. Bajar con: modal volume get tp-corridas /{corrida} corridas/", flush=True)


@app.function(image=imagen, secrets=secretos, timeout=3600, volumes={HF_CACHE: volumen_hf})
def bajar_modelo(modelo: str = "google/gemma-4-E4B-it") -> None:
    """Baja el modelo base a la caché compartida, sin GPU."""
    import os
    from huggingface_hub import snapshot_download
    ruta = snapshot_download(modelo, token=os.environ.get("HF_TOKEN"))
    volumen_hf.commit()
    print(f"{modelo} en {ruta}")


@app.local_entrypoint()
def main(corrida: str, config: str = "entrenar.yaml", datos: str = "", val: str = "",
         max_pasos: int = 0, retomar: str = "", conservar_checkpoints: bool = False) -> None:
    """Lanza entrenar.py en Modal. Las rutas de datos son relativas a missions/TPFinal y tienen que estar en datos/."""
    argumentos = ["--config", config]
    for opcion, valor in (("--datos", datos), ("--val", val)):
        if valor:
            if not Path(valor).as_posix().startswith("datos/"):
                raise SystemExit(f"{opcion} tiene que estar dentro de datos/ (es lo que se sube a Modal)")
            argumentos += [opcion, valor]
    if max_pasos:
        argumentos += ["--max-pasos", str(max_pasos)]
    if retomar:
        # hf:<etiqueta o revisión> de HF_REPO, o una carpeta checkpoint-N dentro del volumen tp-corridas.
        argumentos += ["--retomar", retomar if retomar.startswith("hf:") else f"{CORRIDAS}/{retomar.lstrip('/')}"]
    entrenar.remote(argumentos, corrida, conservar_checkpoints)
