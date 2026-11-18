"""Parte 4: SFT con LoRA (TRL + PEFT) sobre google/gemma-4-E4B-it.

La configuración vive en `entrenar.yaml`. La pérdida se calcula solo sobre los
turnos del asistente (las llamadas JSON a herramientas): el mensaje de sistema,
los mensajes del usuario y los resultados de las herramientas quedan con
etiqueta -100.

Cada corrida:
  - registra en W&B la configuración, la semilla, el archivo de datos con su
    sha256 (también como artefacto) y la revisión de Hugging Face de cada
    punto de control;
  - sube cada punto de control a HF_REPO (repo privado de modelo): el
    adaptador en la raíz, para que vLLM lo cargue tal cual, y el estado del
    optimizador en `estado/`, para poder retomar. Cada subida es un commit con
    su etiqueta `<corrida>-paso-<N>`; al terminar, `<corrida>-final` y, si no se
    cortó con --max-pasos, `final`;
  - verifica que el adaptador sea cargable por el soporte LoRA de vLLM.

Uso (en GPU corre dentro de Modal, ver modal_entrenar.py y MODAL.md):
    python entrenar.py --config entrenar.yaml
    python entrenar.py --config entrenar.yaml --max-pasos 20
    python entrenar.py --config entrenar.yaml --retomar hf:<corrida>-paso-200
    python entrenar.py --prueba        # Mac, modelo diminuto, sin W&B ni HF reales

Variables de entorno: HF_TOKEN, HF_REPO, WANDB_API_KEY (ver .env.example).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent

# Soporte LoRA de vLLM 0.34.0 para Gemma 4 (vllm/model_executor/models/gemma4.py y
# gemma4_mm.py): capas lineales del modelo de lenguaje, empaquetadas como
# qkv_proj y gate_up_proj. Las torres de visión y audio solo admiten LoRA con
# enable_tower_connector_lora (experimental), así que quedan afuera.
MODULOS_VLLM = ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")
RANKS_VLLM = (1, 8, 16, 32, 64, 128, 256, 320, 512)  # vllm/config/lora.py: MaxLoRARanks
TARGET_REGEX = r"^(?!.*(?:vision|audio)).*\.(?:" + "|".join(MODULOS_VLLM) + r")$"

MODELO_PRUEBA = "trl-internal-testing/tiny-Gemma4ForConditionalGeneration"


# ------------------------------------------------------------------ utilidades

def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with Path(ruta).open("rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def leer_jsonl(ruta: Path) -> list[dict]:
    with Path(ruta).open(encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def marca_de_fin(tokenizer) -> str:
    """Texto que la plantilla de chat pone después del contenido del asistente (en Gemma 4, «<turn|>»)."""
    texto = tokenizer.apply_chat_template(
        [{"role": "user", "content": "U"}, {"role": "assistant", "content": "MARCA_ASISTENTE"}], tokenize=False)
    resto = texto[texto.rindex("MARCA_ASISTENTE") + len("MARCA_ASISTENTE"):]
    marca = resto.strip()
    if not marca:
        raise ValueError("la plantilla de chat no cierra el turno del asistente")
    return marca


def tokenizar(conversacion: list[dict], tokenizer, fin: str) -> dict[str, list[int]]:
    """input_ids y labels con -100 fuera de los turnos del asistente.

    Se renderiza la conversación con la plantilla de chat del modelo y se marcan
    los caracteres de cada respuesta del asistente más la marca de fin de turno
    (así el modelo aprende a cortar). Los offsets del tokenizador rápido pasan
    esa máscara de caracteres a tokens.
    """
    texto = tokenizer.apply_chat_template(conversacion, tokenize=False)
    tramos, cursor = [], 0
    for m in conversacion:
        contenido = m["content"].strip()
        inicio = texto.index(contenido, cursor)
        cursor = inicio + len(contenido)
        if m["role"] == "assistant":
            fin_marca = texto.index(fin, cursor) + len(fin)
            tramos.append((inicio, fin_marca))
            cursor = fin_marca
    enc = tokenizer(texto, add_special_tokens=False, return_offsets_mapping=True)
    labels = []
    t = 0
    for token, (a, b) in zip(enc["input_ids"], enc["offset_mapping"]):
        while t < len(tramos) and a >= tramos[t][1]:
            t += 1
        dentro = t < len(tramos) and a >= tramos[t][0] and b <= tramos[t][1] and b > a
        labels.append(token if dentro else -100)
    return {"input_ids": enc["input_ids"], "labels": labels}


# --------------------------------------------------------------- publicación

class PublicadorHF:
    """Sube cada punto de control a un repo privado de modelo de Hugging Face."""

    def __init__(self, repo: str, token: str | None):
        from huggingface_hub import HfApi
        self.repo, self.api = repo, HfApi(token=token)
        self.api.create_repo(repo, repo_type="model", private=True, exist_ok=True)

    def subir(self, carpeta: Path, etiqueta: str, mensaje: str) -> str:
        info = self.api.upload_folder(repo_id=self.repo, folder_path=str(carpeta), commit_message=mensaje)
        self.etiquetar(info.oid, etiqueta)
        return info.oid

    def etiquetar(self, revision: str, etiqueta: str, mover: bool = False) -> None:
        if mover:
            refs = self.api.list_repo_refs(self.repo)
            anterior = next((t.target_commit for t in refs.tags if t.name == etiqueta), None)
            if anterior:
                print(f"La etiqueta {etiqueta} apuntaba a {anterior}; pasa a {revision}.")
                self.api.delete_tag(self.repo, tag=etiqueta)
        self.api.create_tag(self.repo, tag=etiqueta, revision=revision)

    def bajar(self, revision: str, destino: Path) -> Path:
        from huggingface_hub import snapshot_download
        return Path(snapshot_download(self.repo, revision=revision, local_dir=str(destino), token=self.api.token))


class PublicadorLocal:
    """Para --prueba: imita al repo de HF en una carpeta, con una «revisión» por subida."""

    def __init__(self, carpeta: Path):
        self.carpeta = carpeta
        self.carpeta.mkdir(parents=True, exist_ok=True)
        self.etiquetas: dict[str, str] = {}

    def subir(self, carpeta: Path, etiqueta: str, mensaje: str) -> str:
        h = hashlib.sha1()
        for archivo in sorted(p for p in carpeta.rglob("*") if p.is_file()):
            h.update(archivo.name.encode())
            h.update(archivo.read_bytes())
        revision = h.hexdigest()
        shutil.copytree(carpeta, self.carpeta / revision, dirs_exist_ok=True)
        self.etiquetar(revision, etiqueta)
        return revision

    def etiquetar(self, revision: str, etiqueta: str, mover: bool = False) -> None:
        self.etiquetas[etiqueta] = revision
        (self.carpeta / "etiquetas.json").write_text(json.dumps(self.etiquetas, indent=2), encoding="utf-8")

    def bajar(self, revision: str, destino: Path) -> Path:
        revision = self.etiquetas.get(revision, revision)
        if not (self.carpeta / revision).exists():
            etiquetas = json.loads((self.carpeta / "etiquetas.json").read_text(encoding="utf-8"))
            revision = etiquetas.get(revision, revision)
        shutil.copytree(self.carpeta / revision, destino, dirs_exist_ok=True)
        return destino


ARCHIVOS_ADAPTADOR = ("adapter_model.safetensors", "adapter_config.json")


def armar_subida(checkpoint: Path, destino: Path, metadatos: dict) -> Path:
    """Adaptador en la raíz (lo carga vLLM) y estado para retomar en estado/."""
    if destino.exists():
        shutil.rmtree(destino)
    (destino / "estado").mkdir(parents=True)
    for archivo in checkpoint.iterdir():
        if archivo.is_dir():
            continue
        if archivo.name in ARCHIVOS_ADAPTADOR or archivo.name.startswith(("tokenizer", "chat_template", "special_tokens")):
            shutil.copy(archivo, destino / archivo.name)
        else:  # optimizer.pt, scheduler.pt, rng_state.pth, trainer_state.json, training_args.bin, wandb_id.txt
            shutil.copy(archivo, destino / "estado" / archivo.name)
    (destino / "corrida.json").write_text(json.dumps(metadatos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destino


def reconstruir_checkpoint(bajado: Path, destino: Path) -> Path:
    """Inversa de armar_subida: deja una carpeta checkpoint-N que entiende Trainer."""
    estado = json.loads((bajado / "estado" / "trainer_state.json").read_text(encoding="utf-8"))
    checkpoint = destino / f"checkpoint-{estado['global_step']}"
    checkpoint.mkdir(parents=True, exist_ok=True)
    for archivo in list(bajado.iterdir()) + list((bajado / "estado").iterdir()):
        if archivo.is_file():
            shutil.copy(archivo, checkpoint / archivo.name)
    return checkpoint


# ------------------------------------------------------------ compatibilidad vLLM

def verificar_adaptador_vllm(carpeta: Path) -> dict:
    """Controla lo que exige vLLM 0.34.0 para cargar un adaptador LoRA de Gemma 4."""
    from safetensors import safe_open
    config = json.loads((carpeta / "adapter_config.json").read_text(encoding="utf-8"))
    problemas = []
    if config["r"] not in RANKS_VLLM:
        problemas.append(f"rank {config['r']} no está en {RANKS_VLLM}")
    if config.get("modules_to_save"):
        problemas.append(f"modules_to_save no soportado: {config['modules_to_save']}")
    if config.get("use_dora"):
        problemas.append("DoRA no soportado")
    with safe_open(str(carpeta / "adapter_model.safetensors"), framework="pt") as f:
        claves = list(f.keys())
    modulos = set()
    for clave in claves:
        nombre = clave.split(".lora_")[0]
        modulos.add(nombre.rsplit(".", 1)[-1])
        if "vision" in nombre or "audio" in nombre:
            problemas.append(f"LoRA en la torre multimodal: {nombre}")
        if ".lora_" not in clave:
            problemas.append(f"tensor que no es LoRA: {clave}")
    fuera = modulos - set(MODULOS_VLLM)
    if fuera:
        problemas.append(f"módulos que vLLM no espera: {sorted(fuera)}")
    resultado = {"rank": config["r"], "alpha": config["lora_alpha"], "modulos": sorted(modulos),
                 "tensores": len(claves), "max_lora_rank_vllm": min(r for r in RANKS_VLLM if r >= config["r"]),
                 "problemas": problemas[:10]}
    if problemas:
        raise ValueError(f"El adaptador no es cargable por vLLM: {resultado}")
    return resultado


# ------------------------------------------------------------------- main

def cargar_config(args) -> dict:
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.datos:
        cfg["datos"]["train"] = str(args.datos)
    if args.val:
        cfg["datos"]["val"] = str(args.val)
    if args.prueba:
        cfg["modelo"]["id"] = MODELO_PRUEBA
        cfg["modelo"]["dtype"] = "float32"
        cfg["modelo"]["attn_implementation"] = "eager"
        cfg["entrenamiento"].update({
            "batch_por_dispositivo": 1, "acumulacion_gradiente": 2, "largo_maximo": 4096,
            "pasos_guardado": 2, "pasos_evaluacion": 2, "pasos_log": 1, "gradient_checkpointing": False})
        cfg["datos"]["max_train"], cfg["datos"]["max_val"] = 16, 4
    return cfg


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=ROOT / "entrenar.yaml")
    parser.add_argument("--datos", type=Path, help="reemplaza datos.train de la configuración")
    parser.add_argument("--val", type=Path, help="reemplaza datos.val de la configuración")
    parser.add_argument("--corrida", help="nombre de la corrida (por defecto, sft-<fecha>)")
    parser.add_argument("--salida", type=Path, default=ROOT / "corridas", help="carpeta raíz de las corridas")
    parser.add_argument("--max-pasos", type=int, help="corta en N pasos de optimización (pruebas chicas)")
    parser.add_argument("--retomar", help="carpeta checkpoint-N local, o hf:<etiqueta o revisión> de HF_REPO")
    parser.add_argument("--prueba", action="store_true", help="Mac: modelo diminuto, pocos pasos, sin W&B ni HF reales")
    args = parser.parse_args()
    if args.prueba and args.max_pasos is None:
        args.max_pasos = 4

    cfg = cargar_config(args)
    semilla = int(cfg["semilla"])
    corrida = args.corrida or ("prueba-" if args.prueba else "sft-") + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    salida = args.salida / corrida
    salida.mkdir(parents=True, exist_ok=True)

    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainerCallback, set_seed
    from trl import SFTConfig, SFTTrainer

    set_seed(semilla)

    # Datos -------------------------------------------------------------
    rutas = {k: (ROOT / cfg["datos"][k]) if not Path(cfg["datos"][k]).is_absolute() else Path(cfg["datos"][k])
             for k in ("train", "val")}
    datos_info = {k: {"ruta": str(cfg["datos"][k]), "sha256": sha256(r), "lineas": sum(1 for _ in r.open(encoding="utf-8"))}
                  for k, r in rutas.items()}
    tokenizer = AutoTokenizer.from_pretrained(cfg["modelo"]["id"])
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    fin = marca_de_fin(tokenizer)
    largo_maximo = int(cfg["entrenamiento"]["largo_maximo"])

    def preparar(nombre: str, limite: int | None) -> Dataset:
        filas = leer_jsonl(rutas[nombre])[:limite] if limite else leer_jsonl(rutas[nombre])
        ejemplos, largos, descartadas = [], [], []
        for fila in filas:
            ej = tokenizar(fila["messages"], tokenizer, fin)
            if len(ej["input_ids"]) > largo_maximo:  # truncar cortaría registrar_decision: se descarta
                descartadas.append(fila["id"])
                continue
            if not any(x != -100 for x in ej["labels"]):
                raise ValueError(f"{fila['id']}: ningún token del asistente quedó en la pérdida")
            ejemplos.append(ej)
            largos.append(len(ej["input_ids"]))
        datos_info[nombre].update({
            "conversaciones_usadas": len(ejemplos), "descartadas_por_largo": descartadas,
            "tokens": sum(largos), "tokens_en_perdida": sum(sum(x != -100 for x in e["labels"]) for e in ejemplos),
            "largo_maximo": max(largos), "largo_medio": round(sum(largos) / len(largos), 1)})
        return Dataset.from_list(ejemplos)

    train = preparar("train", cfg["datos"].get("max_train"))
    val = preparar("val", cfg["datos"].get("max_val"))
    print(json.dumps(datos_info, ensure_ascii=False, indent=2))

    # Modelo ------------------------------------------------------------
    dtype = getattr(torch, cfg["modelo"]["dtype"])
    modelo = AutoModelForCausalLM.from_pretrained(
        cfg["modelo"]["id"], dtype=dtype, attn_implementation=cfg["modelo"]["attn_implementation"])
    lora_cfg = cfg["lora"]
    if lora_cfg["r"] not in RANKS_VLLM:
        raise ValueError(f"lora.r = {lora_cfg['r']} no lo acepta vLLM; usar uno de {RANKS_VLLM}")
    peft_config = LoraConfig(r=lora_cfg["r"], lora_alpha=lora_cfg["alpha"], lora_dropout=lora_cfg["dropout"],
                             target_modules=TARGET_REGEX, bias="none", task_type="CAUSAL_LM")

    # Publicación y W&B -------------------------------------------------
    ent = cfg["entrenamiento"]
    if args.prueba:
        publicador = PublicadorLocal(args.salida / "hf_simulado")  # compartido entre corridas de prueba
        os.environ["WANDB_MODE"] = "offline"
        os.environ["WANDB_DIR"] = str(salida)
    else:
        repo = os.environ.get("HF_REPO") or cfg.get("hf_repo")
        if not repo:
            sys.exit("Falta HF_REPO (variable de entorno o hf_repo en la configuración).")
        publicador = PublicadorHF(repo, os.environ.get("HF_TOKEN"))

    checkpoint_inicial = None
    if args.retomar:
        if args.retomar.startswith("hf:"):
            bajado = publicador.bajar(args.retomar[3:], salida / "retomado")
            checkpoint_inicial = reconstruir_checkpoint(bajado, salida)
        else:
            checkpoint_inicial = Path(args.retomar)
        print(f"Retomando desde {checkpoint_inicial}")
    wandb_id_previo = None
    if checkpoint_inicial and (checkpoint_inicial / "wandb_id.txt").exists():
        wandb_id_previo = (checkpoint_inicial / "wandb_id.txt").read_text().strip()

    import wandb
    run = wandb.init(
        project=os.environ.get("WANDB_PROJECT") or cfg["wandb"]["proyecto"],
        entity=os.environ.get("WANDB_ENTITY") or cfg["wandb"].get("entidad"),
        name=corrida, id=wandb_id_previo, resume="allow" if wandb_id_previo else None,
        config={"configuracion": cfg, "semilla": semilla, "datos": datos_info, "corrida": corrida,
                "retomado_de": str(args.retomar) if args.retomar else None, "max_pasos": args.max_pasos,
                "target_modules": TARGET_REGEX, "comando": " ".join(sys.argv)})
    artefacto = wandb.Artifact(f"datos-{datos_info['train']['sha256'][:12]}", type="dataset",
                               metadata=datos_info)
    for r in rutas.values():
        artefacto.add_file(str(r))
    run.log_artifact(artefacto)
    run.summary["datos/train_sha256"] = datos_info["train"]["sha256"]
    run.summary["semilla"] = semilla

    (salida / "config_usada.yaml").write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (salida / "datos.json").write_text(json.dumps(datos_info, ensure_ascii=False, indent=2), encoding="utf-8")
    revisiones: list[dict] = []

    def metadatos(paso: int) -> dict:
        return {"corrida": corrida, "paso": paso, "semilla": semilla, "datos": {k: {"ruta": v["ruta"], "sha256": v["sha256"]}
                for k, v in datos_info.items()}, "config": cfg, "wandb": run.url if run else None,
                "modelo_base": cfg["modelo"]["id"]}

    class SubirCheckpoints(TrainerCallback):
        """Al guardar cada punto de control: lo verifica para vLLM, lo sube a HF y anota la revisión en W&B."""

        def on_save(self, targs, state, control, **kwargs):
            if not state.is_world_process_zero:
                return
            checkpoint = Path(targs.output_dir) / f"checkpoint-{state.global_step}"
            (checkpoint / "wandb_id.txt").write_text(run.id)
            vllm = verificar_adaptador_vllm(checkpoint)
            subida = armar_subida(checkpoint, salida / "subida", metadatos(state.global_step))
            etiqueta = f"{corrida}-paso-{state.global_step}"
            revision = publicador.subir(subida, etiqueta, f"{corrida}: punto de control del paso {state.global_step}")
            revisiones.append({"paso": state.global_step, "revision": revision, "etiqueta": etiqueta})
            (salida / "revisiones.json").write_text(json.dumps(revisiones, indent=2), encoding="utf-8")
            run.log({"hf/paso_subido": state.global_step}, step=state.global_step)
            run.summary["hf/ultima_revision"] = revision
            run.summary["hf/ultima_etiqueta"] = etiqueta
            print(f"Punto de control {state.global_step} -> {revision} ({etiqueta}); vLLM: {vllm}")

        def on_log(self, targs, state, control, logs=None, **kwargs):
            if torch.cuda.is_available():
                run.log({"gpu/vram_max_gb": torch.cuda.max_memory_allocated() / 2**30}, step=state.global_step)

    sft_args = SFTConfig(
        output_dir=str(salida / "checkpoints"),
        run_name=corrida,
        seed=semilla,
        data_seed=semilla,
        num_train_epochs=ent["epocas"],
        max_steps=args.max_pasos or -1,
        per_device_train_batch_size=ent["batch_por_dispositivo"],
        per_device_eval_batch_size=ent["batch_por_dispositivo"],
        gradient_accumulation_steps=ent["acumulacion_gradiente"],
        gradient_checkpointing=ent["gradient_checkpointing"],
        gradient_checkpointing_kwargs={"use_reentrant": False} if ent["gradient_checkpointing"] else None,
        learning_rate=float(ent["lr"]),
        lr_scheduler_type=ent["scheduler"],
        warmup_steps=float(ent["warmup"]),  # en transformers 5, un float < 1 es fracción de los pasos
        weight_decay=ent["weight_decay"],
        max_grad_norm=ent["max_grad_norm"],
        bf16=cfg["modelo"]["dtype"] == "bfloat16",
        logging_steps=ent["pasos_log"],
        eval_strategy="steps",
        eval_steps=min(ent["pasos_evaluacion"], args.max_pasos or 10**9),
        save_strategy="steps",
        save_steps=min(ent["pasos_guardado"], args.max_pasos or 10**9),
        save_total_limit=ent.get("checkpoints_locales", 3),
        report_to="wandb",
        max_length=largo_maximo,
        packing=False,
        train_sampling_strategy="group_by_length" if ent.get("agrupar_por_largo", True) else "random",
        dataset_kwargs={"skip_prepare_dataset": True},
        remove_unused_columns=False,
        dataloader_num_workers=0 if args.prueba else 2,
        use_cpu=args.prueba,
    )
    trainer = SFTTrainer(model=modelo, args=sft_args, train_dataset=train, eval_dataset=val,
                         processing_class=tokenizer, peft_config=peft_config, callbacks=[SubirCheckpoints()])
    entrenables = sum(p.numel() for p in trainer.model.parameters() if p.requires_grad)
    run.summary["parametros_entrenables"] = entrenables
    print(f"Parámetros entrenables (LoRA): {entrenables:,}")

    inicio = time.time()
    resultado = trainer.train(resume_from_checkpoint=str(checkpoint_inicial) if checkpoint_inicial else None)
    duracion = time.time() - inicio
    metricas_eval = trainer.evaluate()

    # Final -------------------------------------------------------------
    final = salida / "final"
    trainer.save_model(str(final))
    tokenizer.save_pretrained(str(final))
    (final / "wandb_id.txt").write_text(run.id)
    vllm = verificar_adaptador_vllm(final)
    paso = trainer.state.global_step
    subida = armar_subida(final, salida / "subida", metadatos(paso) | {"final": True})
    revision = publicador.subir(subida, f"{corrida}-final", f"{corrida}: adaptador final (paso {paso})")
    # Solo una corrida completa mueve la etiqueta móvil: una prueba con --max-pasos no pisa el adaptador final.
    etiqueta_movil = None if args.max_pasos and not args.prueba else cfg["hf"]["etiqueta_final"]
    if etiqueta_movil:
        publicador.etiquetar(revision, etiqueta_movil, mover=True)
    revisiones.append({"paso": paso, "revision": revision, "etiqueta": f"{corrida}-final",
                       "etiqueta_movil": etiqueta_movil})
    resumen = {"corrida": corrida, "pasos": paso, "segundos": round(duracion, 1),
               "train_loss": resultado.training_loss, "eval": metricas_eval, "revisiones": revisiones,
               "vllm": vllm, "wandb": run.url if run else None, "datos": datos_info, "semilla": semilla,
               "vram_max_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2) if torch.cuda.is_available() else None}
    (salida / "revisiones.json").write_text(json.dumps(revisiones, indent=2), encoding="utf-8")
    (salida / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    run.summary["hf/revision_final"] = revision
    run.summary["segundos_entrenamiento"] = round(duracion, 1)
    run.finish()
    print(json.dumps(resumen, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
