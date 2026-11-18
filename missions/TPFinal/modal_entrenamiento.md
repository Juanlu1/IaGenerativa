# Entrenamiento en Modal

Comandos exactos para armar los datos, probar y lanzar el entrenamiento de la
Parte 4, ver los logs, bajar los resultados y retomar desde un punto de
control. Todo se corre desde `missions/TPFinal` en la Mac. Lo que usa GPU va a
Modal, en una A100 de 40 GB, con `modal run --detach`: sigue corriendo aunque
se cierre la terminal. La evaluación y la optimización de prompt están en
[`MODAL.md`](MODAL.md).

## Una sola vez

```bash
# El CLI de modal, con la versión fijada en deps_entrenamiento.txt.
alias modal="uv run --with modal==1.6.4 modal"

modal token new                     # si la Mac todavía no está autenticada
modal secret list | grep tp-secrets # el secret con HF_TOKEN, WANDB_API_KEY y HF_REPO
```

`modal_entrenar.py` crea solos los dos volúmenes la primera vez:

| Volumen | Qué guarda | Montado en |
|---|---|---|
| `tp-hf-cache` | la caché de Hugging Face: Gemma 4 E4B se baja una sola vez | `/cache/hf` |
| `tp-corridas` | una carpeta por corrida, con la misma estructura que `corridas/<corrida>` en la Mac | `/corridas` |

Opcional: bajar el modelo a la caché antes de la primera corrida, sin GPU:

```bash
modal run --detach modal_entrenar.py::bajar_modelo
```

## 1. Armar los datos (en la Mac, sin GPU)

```bash
# Variante "solo entrenamiento": mensaje de sistema de admision/ejemplo.py.
uv run python armar_dataset.py

# Variante "prompt + entrenamiento": el prompt optimizado de la Parte 3.
uv run python armar_dataset.py --prompt prompt_optimizado.txt --salida datos/con_prompt
```

Tarda unos segundos. Cada carpeta queda con `train.jsonl`, `val.jsonl` y
`resumen.json` (conversaciones por origen, tokens y sha256 de cada archivo).
`modal_entrenar.py` sube la carpeta `datos/` entera con cada corrida, así que
`--datos` y `--val` tienen que apuntar adentro de `datos/`.

Si `train.jsonl` pasa los 50 MB, `armar_dataset.py` lo avisa: no se commitea
y se publica en un repo privado de dataset de Hugging Face, con una etiqueta
`train-<sha256 corto>` que se cita en el informe:

```bash
set -a; source .env; set +a
uv run --with huggingface_hub==2.4.0 python armar_dataset.py \
    --prompt prompt_optimizado.txt --salida datos/con_prompt \
    --subir-hf <usuario>/tp-admision-datos
```

## 2. Prueba en la Mac (sin GPU ni servicios reales)

```bash
uv run --with-requirements deps_entrenamiento.txt python entrenar.py --prueba
```

Usa `trl-internal-testing/tiny-Gemma4ForConditionalGeneration` (la misma
arquitectura que Gemma 4 E4B, con pesos diminutos), 16 conversaciones, 4
pasos, W&B en modo offline y un Hugging Face simulado en
`corridas/hf_simulado/`. Controla la máscara de la pérdida, los puntos de
control, la compatibilidad del adaptador con vLLM y el retomado:

```bash
uv run --with-requirements deps_entrenamiento.txt python entrenar.py --prueba \
    --corrida prueba-mac-retomada --retomar hf:prueba-mac-paso-2
```

## 3. Prueba chica en GPU

Mide segundos por paso y VRAM con el modelo real antes de gastar horas:

```bash
modal run --detach modal_entrenar.py --corrida prueba-gpu-01 --max-pasos 20
```

Sube a `HF_REPO` las etiquetas `prueba-gpu-01-paso-20` y `prueba-gpu-01-final`
y registra la corrida en W&B, pero no mueve la etiqueta `final`. Al terminar,
`corridas/prueba-gpu-01/resumen.json` trae `segundos`, `pasos` y
`vram_max_gb`. La corrida completa tiene unos 530 pasos (2.840 conversaciones,
16 por paso, 3 épocas): si `530 x segundos / pasos` se va de 2 a 4 horas,
ajustar `epocas` en `entrenar.yaml` y commitear el cambio antes de lanzarla.

## 4. Entrenamiento completo

```bash
# Solo entrenamiento (prompt de admision/ejemplo.py).
modal run --detach modal_entrenar.py --corrida sft-ejemplo-v1

# Prompt optimizado + entrenamiento.
modal run --detach modal_entrenar.py --corrida sft-prompt-v1 \
    --datos datos/con_prompt/train.jsonl --val datos/con_prompt/val.jsonl
```

Opciones de `modal_entrenar.py`: `--corrida` (obligatoria; también es el
nombre en W&B y el prefijo de las etiquetas de HF), `--config` (por defecto
`entrenar.yaml`), `--datos`, `--val`, `--max-pasos`, `--retomar` y
`--conservar-checkpoints` (deja en el volumen los puntos de control, que si no
se borran al terminar bien porque ya están en HF).

Cada 100 pasos el punto de control sube a `HF_REPO` con la etiqueta
`<corrida>-paso-<N>`. Al terminar sube el adaptador final con
`<corrida>-final` y mueve `final` a esa revisión. Las revisiones quedan en
`corridas/<corrida>/revisiones.json`, en el resumen de W&B y en el log.

## 5. Ver los logs

```bash
modal app list                          # la app es tp-admision-entrenar; anotar su id (ap-...)
modal app logs <id de la app> -f        # en vivo
modal app logs <id de la app> --tail 1000
```

Las métricas (pérdida de train y val, lr, VRAM máxima) están en el proyecto
de W&B `tp-admision-guardia` (o el de `WANDB_PROJECT`). Para cortar una
corrida: `modal app stop <id de la app>`.

## 6. Bajar los resultados

```bash
modal volume get tp-corridas /sft-ejemplo-v1 corridas/
```

Deja todo en `corridas/sft-ejemplo-v1/`, igual que una corrida local:
`resumen.json`, `revisiones.json`, `datos.json` (sha256 y tokens reales de
cada archivo), `config_usada.yaml` y `final/` (el adaptador). Si la carpeta
ya existe, agregar `--force`. `.gitignore` deja afuera `final/`, `wandb/` y
los puntos de control: se commitean solo los JSON y el YAML.

## 7. Retomar desde un punto de control

Desde Hugging Face (lo normal: cada punto de control trae el estado del
optimizador, del scheduler y de los generadores aleatorios en `estado/`):

```bash
modal run --detach modal_entrenar.py --corrida sft-ejemplo-v1-r1 \
    --retomar hf:sft-ejemplo-v1-paso-300
```

Desde el volumen, si la corrida se cortó antes de subir el último punto de
control (los que quedaron están en `/corridas/<corrida>/checkpoints/`):

```bash
modal volume ls tp-corridas /sft-ejemplo-v1/checkpoints
modal run --detach modal_entrenar.py --corrida sft-ejemplo-v1-r1 \
    --retomar sft-ejemplo-v1/checkpoints/checkpoint-300
```

La corrida retomada sigue la misma corrida de W&B (su id viaja en el punto de
control) y sigue contando pasos desde donde quedó. En la prueba de la Mac,
retomar desde el paso 2 dio un adaptador idéntico bit a bit al de la corrida
sin cortes.
