# Correr el agente y el entrenamiento en Modal

Cómo evaluar el agente (`entrega.py`), optimizar su prompt y entrenar el adaptador en una A100 de 40 GB de Modal,
lanzando todo desde la Mac. Las secciones siguen el orden en que se corren las cosas: preparar la Mac, la evaluación
del modelo sin entrenar, la Parte 3 (prompt), la Parte 4 (datos y entrenamiento) y la evaluación de los adaptadores.

Todos los comandos se corren desde `missions/TPFinal/` en la Mac. La GPU la pone Modal: en la Mac no se instala vLLM,
así que la evaluación solo funciona en modo de prueba (`MODELO_FALSO=1`) y el entrenamiento solo con `--prueba`.

## Qué usa

| Recurso | Nombre | Para qué |
|---|---|---|
| App | `tp-admision` (`modal_app.py`) | Evaluación (`evaluar`) y optimización de prompt (`gepa`) |
| App | `tp-admision-entrenar` (`modal_entrenar.py`) | Entrenamiento (`entrenar.py`) y bajada del modelo a la caché (`bajar_modelo`) |
| GPU | `A100-40GB` | La misma que usa la cátedra; no la de 80 GB |
| Secret | `tp-secrets` | `HF_TOKEN`, `WANDB_API_KEY` y `HF_REPO`, como variables de entorno |
| Volume | `tp-hf-cache` | Caché de Hugging Face: Gemma se baja una sola vez y la usan las dos apps |
| Volume | `tp-corridas` | Resultados. Evaluaciones en `/corridas/<etiqueta>/`, prompt en `/corridas/gepa/<etiqueta>/`, entrenamientos en `/<corrida>/` |

Los dos Volumes se crean solos la primera vez. Las dos apps arman su imagen desde el mismo `uv.lock` (vLLM 0.34.0,
torch 2.14.0, transformers 5.22.2): el adaptador se entrena con la misma pila que lo sirve. La imagen se arma la
primera vez y después se reutiliza.

- `modal_app.py` sube el código de esta carpeta (sin `.env`, `.venv`, `corridas/`, `curado/`, `entrenamiento/` ni
  `datos/`). Cada evaluación carga el modelo **una sola vez** y corre los casos con las normas original, b y c en el
  mismo contenedor (`evaluar.py`).
- `modal_entrenar.py` sube solo `entrenar.py`, `entrenar.yaml` y la carpeta `datos/`.

Todas las corridas se lanzan igual: `modal run --detach` adentro de `nohup caffeinate -is ... &` con un log local en
`corridas/` (la terminal queda libre y la salida queda guardada). `tail -f` sigue el log; `Ctrl+C` corta el `tail`, no
la corrida. `--detach` solo no alcanza: cuando la Mac se suspendió con la tapa cerrada, Modal canceló las corridas
(INFORME.md, Parte 4, pasada 6). `caffeinate -is` impide que se suspenda mientras dura el comando; la Mac tiene que
quedar enchufada y con la tapa abierta.

## 1. Preparar la Mac (una sola vez)

```bash
cd missions/TPFinal
uv sync
cp .env.example .env         # completar HF_TOKEN, WANDB_API_KEY y HF_REPO
uv run modal token new
uv run modal secret create tp-secrets HF_TOKEN=... WANDB_API_KEY=... HF_REPO=...
uv run modal secret list
```

`modal token new` abre el navegador para autenticar la cuenta. `modal secret list` tiene que mostrar `tp-secrets`
(si ya existe, no hace falta crearlo).

## 2. Probar en la Mac, sin GPU

Para probar cambios del código sin gastar Modal:

```bash
MODELO_FALSO=1 ./evaluar_todo.sh prueba_local 3
```

Corre los primeros 3 casos de práctica con las normas original, b y c, deja los mismos archivos que una corrida real
en `corridas/prueba_local/` y regenera `corridas/tabla.md`. Con el modelo falso la Gemma no corre: el agente sigue un
guion fijo y sus números no significan nada. Las pruebas no son resultados para el informe: se borran después de
revisarlas.

## 3. Prueba sin GPU en Modal

Prueba la imagen, los Volumes y la bajada de resultados con el modelo falso, en un contenedor sin GPU:

```bash
nohup caffeinate -is uv run modal run --detach modal_app.py::evaluar --etiqueta prueba_falso --cantidad 3 --falso > corridas/prueba_falso.log 2>&1 &
tail -f corridas/prueba_falso.log
```

La primera vez arma la imagen (instala vLLM y torch), así que tarda varios minutos.

## 4. Prueba chica: 3 casos en la A100

```bash
nohup caffeinate -is uv run modal run --detach modal_app.py::evaluar --etiqueta prueba_base --cantidad 3 --config config_base.yaml > corridas/prueba_base.log 2>&1 &
tail -f corridas/prueba_base.log
```

La primera vez baja Gemma al Volume `tp-hf-cache`; las siguientes ya lo encuentran ahí.

## 5. Corrida completa: 50 casos

```bash
nohup caffeinate -is uv run modal run --detach modal_app.py::evaluar --etiqueta base --config config_base.yaml > corridas/base.log 2>&1 &
tail -f corridas/base.log
```

`config_base.yaml` es el modelo sin entrenar con `prompt_base.txt`; `config.yaml` es la entrega final, con
`prompt_optimizado.txt` y el adaptador (sección 14). Para otra configuración se pasa un yaml de esta carpeta con
`--config` y otra etiqueta (secciones 7 y 14). Sin `--config` se usa la variable `CONFIG` de la Mac, y si no está,
`config.yaml`. El yaml tiene que estar en esta carpeta porque se sube con el código. Si hay cambios sin commitear, la
corrida se lanza igual pero queda marcada así en `corrida.json`.

## 6. Ver los logs y bajar los resultados

Al lanzar, Modal muestra el link de la corrida en su web, con los logs en vivo. Desde la terminal:

```bash
uv run modal app list
uv run modal app logs <app-id> -f
```

`<app-id>` es el de la fila de la app en `modal app list` (empieza con `ap-`). La salida de `evaluar.py` también queda
guardada en el Volume:

```bash
uv run modal volume get tp-corridas /corridas/base/modal.log -
```

Para cortar una corrida:

```bash
uv run modal app stop <app-id>
```

Al terminar, los resultados se bajan a `corridas/<etiqueta>/`, la misma carpeta que deja una corrida local, y se
regenera la tabla:

```bash
uv run modal volume ls tp-corridas /corridas
uv run modal volume get --force tp-corridas /corridas/base corridas
uv run python tabla.py
```

Queda `corridas/base/` con `corrida.json` (commit, configuración, prompt, modelo y tiempo de carga), `modal.log`,
copia del yaml y del prompt usados, y una carpeta por versión (`original/`, `b/`, `c/`) con `trazas.jsonl`,
`tiempos.json`, `resultados.jsonl` y `resumen.json`. `corridas/tabla.md` junta todas las etiquetas al lado de la
referencia de la cátedra.

## 7. Parte 3: optimización de prompt (GEPA)

`gepa` corre `optimizar_prompt.py` en la A100 con la misma imagen, el mismo secret y los mismos Volumes. Le pasa
`--salida /vol/corridas/gepa/<etiqueta> --sin-copiar-a-raiz` y lo que vaya en `--args`, con la configuración de
`--config` en la variable `CONFIG` (de ahí sale el prompt de partida). Qué hace y con qué casos: ver `INFORME.md`,
Parte 3.

Prueba en la Mac, sin GPU (el agente sigue un guion fijo y la reflexión saca el último párrafo del prompt; sirve para
probar el circuito):

```bash
MODELO_FALSO=1 uv run python optimizar_prompt.py --presupuesto prueba --salida corridas/gepa/prueba_mac --sin-copiar-a-raiz
```

Prueba chica en Modal (presupuesto `prueba`: 6 casos de optimización, 6 de validación, unos minutos):

```bash
nohup caffeinate -is uv run modal run --detach modal_app.py::gepa --etiqueta gepa_prueba --args="--presupuesto prueba" > corridas/gepa_prueba.log 2>&1 &
tail -f corridas/gepa_prueba.log
```

Corrida real (presupuesto `completo`: 90 casos de optimización, 45 de validación, tope de 90 minutos):

```bash
nohup caffeinate -is uv run modal run --detach modal_app.py::gepa --etiqueta gepa1 > corridas/gepa1.log 2>&1 &
tail -f corridas/gepa1.log
```

Otros argumentos de `optimizar_prompt.py` van en `--args`, por ejemplo
`--args="--penalizacion 0.05 --semilla 1"`. Para partir del prompt corto: `--config config_corto.yaml`. El modelo de
reflexión es la misma Gemma, porque el secret `tp-secrets` no tiene claves de modelos pagos.

Al terminar, se baja la salida y se copian el prompt y la configuración optimizados a esta carpeta:

```bash
mkdir -p corridas/gepa
uv run modal volume get --force tp-corridas /corridas/gepa/gepa1 corridas/gepa
cp corridas/gepa/gepa1/prompt_optimizado.txt corridas/gepa/gepa1/config_optimizado.yaml .
```

`corridas/gepa/gepa1/` queda con `log.jsonl` (cada candidato con su texto, su largo en tokens y su puntaje en
validación), `resumen.json` (casos, semilla, presupuesto, modelo de reflexión, prompt inicial y mejor),
`modal.log` y `gepa_run/` (estado interno de GEPA). En `gepa1` la salida de GEPA fue el prompt inicial, así que
`prompt_optimizado.txt` se tomó del candidato 9 de `log.jsonl` (ver `INFORME.md`, Parte 3).

### Evaluar el prompt corto y el optimizado

Con los 50 casos de práctica y las normas original, b y c, igual que la base (sección 5):

```bash
nohup caffeinate -is uv run modal run --detach modal_app.py::evaluar --etiqueta prompt_corto --config config_corto.yaml > corridas/prompt_corto.log 2>&1 &
nohup caffeinate -is uv run modal run --detach modal_app.py::evaluar --etiqueta prompt_optimizado --config config_optimizado.yaml > corridas/prompt_optimizado.log 2>&1 &
```

`config_optimizado.yaml` y `prompt_optimizado.txt` tienen que estar commiteados antes de lanzar, para que
`corrida.json` registre un commit limpio. Después se bajan como en la sección 6 y `uv run python tabla.py` los pone al
lado de la base.

`evaluar_todo.sh` hace lo mismo en la máquina local con `CONFIG`; en la Mac solo sirve con el modelo falso:

```bash
CONFIG=config_corto.yaml MODELO_FALSO=1 ./evaluar_todo.sh prueba_corto 3
CONFIG=config_optimizado.yaml MODELO_FALSO=1 ./evaluar_todo.sh prueba_optimizado 3
```

## 8. Parte 4: armar los datos (en la Mac, sin GPU)

```bash
# Variante "prompt + entrenamiento": el prompt optimizado de la Parte 3, en datos/.
uv run python armar_dataset.py --prompt prompt_optimizado.txt

# Variante "solo entrenamiento": mensaje de sistema de admision/ejemplo.py, en datos/sin_prompt/.
uv run python armar_dataset.py --salida datos/sin_prompt
```

Tarda unos segundos. Cada carpeta queda con `train.jsonl`, `val.jsonl` y `resumen.json` (conversaciones por origen,
tokens y sha256 de cada archivo). `entrenar.yaml` lee `datos/train.jsonl` y `datos/val.jsonl` por defecto.
`modal_entrenar.py` sube la carpeta `datos/` entera con cada corrida, así que `--datos` y `--val` tienen que apuntar
adentro de `datos/`.

Si `train.jsonl` pasa los 50 MB, `armar_dataset.py` lo avisa: no se commitea y se publica en un repo privado de
dataset de Hugging Face, con una etiqueta `train-<sha256 corto>` que se cita en el informe:

```bash
set -a; source .env; set +a
uv run python armar_dataset.py --prompt prompt_optimizado.txt --subir-hf <usuario>/tp-admision-datos
```

Hoy los dos `train.jsonl` pesan unos 32 MB y van en git.

## 9. Parte 4: prueba del entrenamiento en la Mac (sin GPU ni servicios reales)

```bash
uv run python entrenar.py --prueba --corrida prueba-mac
```

Usa `trl-internal-testing/tiny-Gemma4ForConditionalGeneration` (la misma arquitectura que Gemma 4 E4B, con pesos
diminutos), 16 conversaciones, 4 pasos, W&B en modo offline y un Hugging Face simulado en `corridas/hf_simulado/`.
Controla la máscara de la pérdida, los puntos de control, que el adaptador cumpla lo que pide vLLM 0.34.0 para cargar
un LoRA de Gemma 4 (rank, módulos, sin `modules_to_save` ni DoRA) y el retomado:

```bash
uv run python entrenar.py --prueba --corrida prueba-mac-retomada --retomar hf:prueba-mac-paso-2
```

Las carpetas `corridas/prueba-*/` y `corridas/hf_simulado/` están en `.gitignore`.

## 10. Parte 4: prueba chica de entrenamiento en la A100

Opcional, antes de la primera corrida: bajar el modelo a la caché sin GPU.

```bash
uv run modal run --detach modal_entrenar.py::bajar_modelo
```

Mide segundos por paso y VRAM con el modelo real antes de gastar horas:

```bash
nohup caffeinate -is uv run modal run --detach modal_entrenar.py --corrida prueba-gpu-01 --max-pasos 20 > corridas/prueba-gpu-01.log 2>&1 &
tail -f corridas/prueba-gpu-01.log
```

Sube a `HF_REPO` las etiquetas `prueba-gpu-01-paso-20` y `prueba-gpu-01-final` y registra la corrida en W&B, pero no
mueve la etiqueta `final`. Al terminar, `corridas/prueba-gpu-01/resumen.json` trae `segundos`, `pasos` y
`vram_max_gb`. Una época son unos 178 pasos (2.850 conversaciones, 16 por paso): si
`178 x epocas x segundos por paso` se va de 2 a 3 horas, ajustar `epocas` en `entrenar.yaml` y commitear el cambio
antes de lanzar la corrida completa. Con `prueba-gpu-02` (27,5 s por paso) quedó en 1,75 épocas, unos 312 pasos.

## 11. Parte 4: entrenamiento completo

```bash
# Prompt optimizado + entrenamiento (datos/, el default de entrenar.yaml).
nohup caffeinate -is uv run modal run --detach modal_entrenar.py --corrida sft-prompt-v1 > corridas/sft-prompt-v1.log 2>&1 &

# Solo entrenamiento (prompt de admision/ejemplo.py).
nohup caffeinate -is uv run modal run --detach modal_entrenar.py --corrida sft-ejemplo-v1 \
    --datos datos/sin_prompt/train.jsonl --val datos/sin_prompt/val.jsonl > corridas/sft-ejemplo-v1.log 2>&1 &
```

Opciones de `modal_entrenar.py`: `--corrida` (obligatoria; también es el nombre en W&B y el prefijo de las etiquetas
de HF), `--config` (por defecto `entrenar.yaml`), `--datos`, `--val`, `--max-pasos`, `--retomar` y
`--conservar-checkpoints` (deja en el volumen los puntos de control, que si no se borran al terminar bien porque ya
están en HF).

Cada 100 pasos el punto de control sube a `HF_REPO` con la etiqueta `<corrida>-paso-<N>`. Al terminar sube el
adaptador final con `<corrida>-final` y mueve `final` a esa revisión. Las revisiones quedan en
`corridas/<corrida>/revisiones.json`, en el resumen de W&B y en el log.

## 12. Parte 4: ver los logs y bajar los resultados del entrenamiento

Los logs, igual que en la sección 6 (la app es `tp-admision-entrenar`):

```bash
uv run modal app list
uv run modal app logs <app-id> -f
uv run modal app logs <app-id> --tail 1000
```

Las métricas (pérdida de train y val, lr, VRAM máxima) están en el proyecto de W&B `tp-admision-guardia` (o el de
`WANDB_PROJECT`). Para cortar una corrida: `uv run modal app stop <app-id>`.

Los entrenamientos quedan en la raíz del volumen (no en `/corridas/`):

```bash
uv run modal volume get tp-corridas /sft-prompt-v1 corridas/
```

Deja todo en `corridas/sft-prompt-v1/`, igual que una corrida local: `resumen.json`, `revisiones.json`, `datos.json`
(sha256 y tokens reales de cada archivo), `config_usada.yaml` y `final/` (el adaptador). Si la carpeta ya existe,
agregar `--force`. `.gitignore` deja afuera `final/`, `wandb/` y los puntos de control: se commitean solo los JSON y
el YAML.

## 13. Parte 4: retomar desde un punto de control

Desde Hugging Face (lo normal: cada punto de control trae el estado del optimizador, del scheduler y de los
generadores aleatorios en `estado/`):

```bash
nohup caffeinate -is uv run modal run --detach modal_entrenar.py --corrida sft-prompt-v1-r1 \
    --retomar hf:sft-prompt-v1-paso-300 > corridas/sft-prompt-v1-r1.log 2>&1 &
```

Desde el volumen, si la corrida se cortó antes de subir el último punto de control (los que quedaron están en
`/<corrida>/checkpoints/`):

```bash
uv run modal volume ls tp-corridas /sft-prompt-v1/checkpoints
nohup caffeinate -is uv run modal run --detach modal_entrenar.py --corrida sft-prompt-v1-r1 \
    --retomar sft-prompt-v1/checkpoints/checkpoint-300 > corridas/sft-prompt-v1-r1.log 2>&1 &
```

Para la variante sin prompt, lo mismo con `--datos datos/sin_prompt/train.jsonl --val datos/sin_prompt/val.jsonl`.
La corrida retomada sigue la misma corrida de W&B (su id viaja en el punto de control) y sigue contando pasos desde
donde quedó. En la prueba de la Mac, retomar desde el paso 2 dio un adaptador idéntico bit a bit al de la corrida sin
cortes.

## 14. Evaluar los adaptadores entrenados

Cada adaptador tiene su yaml en esta carpeta: `config.yaml` (prompt optimizado + `sft-prompt-v1-r1`) y
`config_sft_base.yaml` (`prompt_base.txt` + `sft-ejemplo-v2`), con `adaptador_lora: <HF_REPO>` y
`adaptador_revision: <commit>`. El commit es el del punto de control con menor pérdida de validación, que queda en
`corridas/<corrida>/revisiones.json`; se fija el commit y no la etiqueta móvil `final`, que pisa cada corrida
completa. `max_lora_rank` queda en 32, el rank del adaptador. Se commitea, se prueba con 3 casos (que vLLM cargue el
adaptador) y se evalúa como en la sección 5:

```bash
nohup caffeinate -is uv run modal run --detach modal_app.py::evaluar --etiqueta prueba_sft_prompt --cantidad 3 --config config.yaml > corridas/prueba_sft_prompt.log 2>&1 &
nohup caffeinate -is uv run modal run --detach modal_app.py::evaluar --etiqueta sft_prompt --config config.yaml > corridas/sft_prompt.log 2>&1 &
nohup caffeinate -is uv run modal run --detach modal_app.py::evaluar --etiqueta sft --config config_sft_base.yaml > corridas/sft.log 2>&1 &
```

Las etiquetas usan `_` y no coinciden con `corridas/<corrida>/`, la carpeta del entrenamiento. Después se bajan como
en la sección 6 y `uv run python tabla.py` las suma a la tabla.

## 15. Guardar los resultados

Las corridas son la evidencia de los números del informe: se commitean y se pushean.

```bash
git add corridas/base corridas/tabla.md
git commit -m "eval(tpfinal): corrida base de Gemma 4 E4B sin entrenar en A100 40 GB"
git push
```
