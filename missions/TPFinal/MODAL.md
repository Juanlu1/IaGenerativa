# Correr el agente en Modal

Cómo evaluar el agente (`entrega.py`) y optimizar su prompt en una A100 de 40 GB de Modal, lanzando todo desde la
Mac. El entrenamiento se documenta en `modal_entrenamiento.md`.

Todos los comandos se corren desde `missions/TPFinal/` en la Mac. La GPU la pone Modal: en la Mac no se instala vLLM
y solo funciona el modo de prueba (`MODELO_FALSO=1`).

## Qué usa

| Recurso | Nombre | Para qué |
|---|---|---|
| App | `tp-admision` (`modal_app.py`) | Evaluación (`evaluar`) y optimización de prompt (`gepa`) |
| GPU | `A100-40GB` | La misma que usa la cátedra; no la de 80 GB |
| Secret | `tp-secrets` | `HF_TOKEN`, `WANDB_API_KEY` y `HF_REPO`, como variables de entorno |
| Volume | `tp-hf-cache` | Caché de Hugging Face: Gemma se baja una sola vez |
| Volume | `tp-corridas` | Corridas y checkpoints. Evaluaciones en `/corridas/<etiqueta>/`, prompt en `/corridas/gepa/<etiqueta>/` |

Los dos Volumes se crean solos la primera vez. En cada corrida se sube el código de esta carpeta (sin `.env`,
`.venv`, `corridas/` ni los datos de entrenamiento); las dependencias salen de `uv.lock` y quedan en la imagen, que
se arma la primera vez y después se reutiliza.

Cada evaluación carga el modelo **una sola vez** y corre los casos con las normas original, b y c en el mismo
contenedor (`evaluar.py`).

## 1. Preparar la Mac (una sola vez)

```bash
cd missions/TPFinal
uv sync
uv run modal token new
uv run modal secret list
```

`modal token new` abre el navegador para autenticar la cuenta. `modal secret list` tiene que mostrar `tp-secrets`.

## 2. Prueba sin GPU

Todas las corridas se lanzan igual: `modal run --detach` (la corrida sigue en Modal aunque se corte la Mac) adentro de
`nohup ... &` con un log local en `corridas/` (la terminal queda libre y la salida queda guardada). `tail -f` sigue el
log; `Ctrl+C` corta el `tail`, no la corrida.

Prueba la imagen, los Volumes y la bajada de resultados con el modelo falso, en un contenedor sin GPU:

```bash
nohup uv run modal run --detach modal_app.py::evaluar --etiqueta prueba_falso --cantidad 3 --falso > corridas/prueba_falso.log 2>&1 &
tail -f corridas/prueba_falso.log
```

La primera vez arma la imagen (instala vLLM y torch), así que tarda varios minutos. Sus números no significan nada:
el modelo falso registra siempre la misma ficha.

## 3. Prueba chica: 3 casos en la A100

```bash
nohup uv run modal run --detach modal_app.py::evaluar --etiqueta prueba_base --cantidad 3 > corridas/prueba_base.log 2>&1 &
tail -f corridas/prueba_base.log
```

La primera vez baja Gemma al Volume `tp-hf-cache`; las siguientes ya lo encuentran ahí.

## 4. Corrida completa: 50 casos

```bash
nohup uv run modal run --detach modal_app.py::evaluar --etiqueta base > corridas/base.log 2>&1 &
tail -f corridas/base.log
```

## 5. Otras variantes

Para evaluar el prompt optimizado o un adaptador entrenado, se crea un yaml en esta carpeta (con `prompt`,
`adaptador_lora` y `adaptador_revision`), se commitea y se pasa con `--config`, con otra etiqueta:

```bash
nohup uv run modal run --detach modal_app.py::evaluar --etiqueta prompt_optimizado --config config_optimizado.yaml > corridas/prompt_optimizado.log 2>&1 &
```

Sin `--config` se usa la variable `CONFIG` de la Mac, y si no está, `config.yaml`. El yaml tiene que estar en esta
carpeta porque se sube con el código. Si hay cambios sin commitear, la corrida se lanza igual pero queda marcada así
en `corrida.json`.

## 6. Ver los logs

Al lanzar, Modal muestra el link de la corrida en su web, con los logs en vivo. Desde la terminal:

```bash
uv run modal app list
uv run modal app logs <app-id>
```

`<app-id>` es el de la fila de `tp-admision` en `modal app list` (empieza con `ap-`). La salida de `evaluar.py`
también queda guardada en el Volume:

```bash
uv run modal volume get tp-corridas /corridas/base/modal.log -
```

Para cortar una corrida:

```bash
uv run modal app stop <app-id>
```

## 7. Bajar los resultados

Al terminar, se bajan a `corridas/<etiqueta>/`, la misma carpeta que deja una corrida local, y se regenera la tabla:

```bash
uv run modal volume ls tp-corridas /corridas
uv run modal volume get --force tp-corridas /corridas/base corridas
uv run python tabla.py
```

Queda `corridas/base/` con `corrida.json` (commit, configuración, prompt, modelo y tiempo de carga), `modal.log`,
copia del yaml y del prompt usados, y una carpeta por versión (`original/`, `b/`, `c/`) con `trazas.jsonl`,
`tiempos.json`, `resultados.jsonl` y `resumen.json`. `corridas/tabla.md` junta todas las etiquetas al lado de la
referencia de la cátedra.

Las pruebas (`prueba_falso`, `prueba_base`) no son resultados para el informe: no se bajan, o se borran después de
revisarlas.

## 8. Parte 3: optimización de prompt (GEPA)

`gepa` corre `optimizar_prompt.py` en la A100 con la misma imagen, el mismo secret y los mismos Volumes. Le pasa
`--salida /vol/corridas/gepa/<etiqueta> --sin-copiar-a-raiz` y lo que vaya en `--args`, con la configuración de
`--config` en la variable `CONFIG` (de ahí sale el prompt de partida). Qué hace y con qué casos: ver
`informe_parte3.md`.

Prueba chica (presupuesto `prueba`: 6 casos de optimización, 6 de validación, unos minutos):

```bash
nohup uv run modal run --detach modal_app.py::gepa --etiqueta gepa_prueba --args="--presupuesto prueba" > corridas/gepa_prueba.log 2>&1 &
tail -f corridas/gepa_prueba.log
```

Corrida real (presupuesto `completo`: 90 casos de optimización, 45 de validación, tope de 90 minutos):

```bash
nohup uv run modal run --detach modal_app.py::gepa --etiqueta gepa1 > corridas/gepa1.log 2>&1 &
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
`modal.log` y `gepa_run/` (estado interno de GEPA).

### Evaluar el prompt corto y el optimizado

Con los 50 casos de práctica y las normas original, b y c, igual que la base (sección 5):

```bash
nohup uv run modal run --detach modal_app.py::evaluar --etiqueta prompt_corto --config config_corto.yaml > corridas/prompt_corto.log 2>&1 &
nohup uv run modal run --detach modal_app.py::evaluar --etiqueta prompt_optimizado --config config_optimizado.yaml > corridas/prompt_optimizado.log 2>&1 &
```

`config_optimizado.yaml` y `prompt_optimizado.txt` tienen que estar commiteados antes de lanzar, para que
`corrida.json` registre un commit limpio. Después se bajan como en la sección 7 y `uv run python tabla.py` los pone al
lado de la base.

`evaluar_todo.sh` hace lo mismo en la máquina local con `CONFIG`; en la Mac solo sirve con el modelo falso:

```bash
CONFIG=config_corto.yaml MODELO_FALSO=1 ./evaluar_todo.sh prueba_corto 3
CONFIG=config_optimizado.yaml MODELO_FALSO=1 ./evaluar_todo.sh prueba_optimizado 3
```

### Probar en la Mac sin GPU

```bash
MODELO_FALSO=1 uv run python optimizar_prompt.py --presupuesto prueba --salida corridas/gepa/prueba_mac --sin-copiar-a-raiz
```

Con el modelo falso la Gemma no corre: el agente sigue un guion fijo y la reflexión saca el último párrafo del
prompt. Sirve para probar el circuito; sus números no significan nada.

## 9. Guardar los resultados

Las corridas son la evidencia de los números del informe: se commitean y se pushean.

```bash
git add corridas/base corridas/tabla.md
git commit -m "eval(tpfinal): corrida base de Gemma 4 E4B sin entrenar en A100 40 GB"
git push
```

## Correr en la Mac (sin GPU)

Para probar cambios del código sin gastar Modal:

```bash
MODELO_FALSO=1 ./evaluar_todo.sh prueba_local 3
```

Deja los mismos archivos en `corridas/prueba_local/` y regenera `corridas/tabla.md`.
