# TP final: el agente de admisión de guardia (grupo)

Agente que completa la ficha de admisión de la guardia del Hospital General de
Prueba con Gemma 4 E4B, un buscador propio sobre las normas y un adaptador LoRA
entrenado por el grupo. El enunciado está en [`mission.md`](mission.md) y el
manual del kit de la cátedra, en [`KIT.md`](KIT.md) (los enlaces de
`mission.md` a `README.md#...` se refieren a ese manual). El desarrollo, parte
por parte, está en [`INFORME.md`](INFORME.md) y en
[`informe_parte4.md`](informe_parte4.md).

Todo se sigue con el punto de control publicado en Hugging Face: **no hace
falta entrenar** para verificar nada. Lo que usa GPU corre en Modal, en una
A100 de 40 GB, lanzado desde la terminal local.

Kit descargado de `austral-ing-ai/talksmith-ing` en la revisión de
[`KIT_VERSION.md`](KIT_VERSION.md). `admision/` es la copia oficial sin cambios.

## 1. Entorno

Desde `missions/TPFinal`:

```bash
uv sync                      # el kit, el agente y sus dependencias (pyproject.toml + uv.lock)
cp .env.example .env         # completar HF_TOKEN, WANDB_API_KEY y HF_REPO
```

Para lo que corre en Modal hace falta una cuenta con `modal token new` hecho y
el secret `tp-secrets` con las mismas tres variables:

```bash
modal secret create tp-secrets HF_TOKEN=... WANDB_API_KEY=... HF_REPO=...
```

El entrenamiento usa además las dependencias fijadas en
[`deps_entrenamiento.txt`](deps_entrenamiento.txt) (se instalan solas en la
imagen de Modal; en local, con `uv run --with-requirements deps_entrenamiento.txt`).

## 2. Un caso

`admision.correr practica` juega y puntúa. Para un solo caso, se copia su línea
a un archivo aparte (el caso `pev-001` activa el circuito de dolor torácico):

```bash
mkdir -p corridas/un-caso
sed -n 1p practica/casos.jsonl > corridas/un-caso/casos.jsonl
uv run python -m admision.correr practica --entrega entrega.py \
    --casos corridas/un-caso/casos.jsonl --esperadas practica/esperadas-b.jsonl \
    --normas normas/b --salida corridas/un-caso/b
```

Necesita GPU: desde la Mac se corre en Modal con los comandos de
[`MODAL.md`](MODAL.md). Qué se ve en `corridas/un-caso/b/`:

- `trazas.jsonl`: la conversación completa con el modelo (cada mensaje que
  entró y cada uno que salió), cada llamada a herramienta con su resultado,
  incluidas las secciones de las normas que trajo `buscar_normativa`, y la
  ficha registrada;
- `resultados.jsonl`: los 9 controles del caso (los 8 campos y la
  verificación de la afiliación) y si quedó resuelto;
- `resumen.json` y `tiempos.json`: casos resueltos, búsquedas, contexto y
  segundos.

## 3. El buscador

```bash
uv run python -m admision.evaluar_rag --entrega entrega.py \
    --normas normas/original --consultas rag/consultas_dev.jsonl
```

`entrega.py` usa el buscador de [`parte2/rag_buscador.py`](parte2/rag_buscador.py).
Sin GPU, la misma evaluación corre con el adaptador de la Parte 2:
`--entrega parte2/entrega_rag.py`. Resultados y experimentos en
[`parte2/RAG.md`](parte2/RAG.md).

## 4. La evaluación completa

Los 50 casos de práctica con las tres versiones de las normas. Para cada
versión `v` en `original`, `b` y `c`:

```bash
uv run python -m admision.correr practica --entrega entrega.py \
    --casos practica/casos.jsonl --esperadas practica/esperadas-$v.jsonl \
    --normas normas/$v --salida corridas/$v
```

`evaluar_todo.sh` y `tabla.py` automatizan las tres corridas y arman la tabla
del informe con sus `resumen.json`; cómo lanzarlos en Modal y bajar los
resultados a `corridas/` está en [`MODAL.md`](MODAL.md).

## 5. De dónde sale cada archivo

| Archivo | Lo genera | Con |
|---|---|---|
| `historial_clasificado.csv`, `costumbres.md`, `curado/auditoria.csv`, `curado/conversaciones_reales.jsonl`, `curado/resumen.json` | `uv run python curar.py` | `historial/`, `normas/original/parametros.yaml` |
| `curado/conversaciones_sinteticas.jsonl`, `curado/sinteticas_config.json`, `curado/sinteticas_resumen.json` | `uv run python generar_sinteticas.py` | semilla 20261108, 600 casos de `admision.generador`, normas original, b y c, buscador de `parte2/` |
| `datos/validacion_politica.json` | `uv run python validar_politica.py` | `practica/` |
| `datos/train.jsonl`, `datos/val.jsonl`, `datos/resumen.json` | `uv run python armar_dataset.py [--prompt <archivo>]` | semilla 20261117; historial correcto, `entrenamiento/trazas.jsonl` y sintéticas |
| `prompt_optimizado.txt` | `optimizar_prompt.py` (Parte 3, rama tp-agente) | ver `INFORME.md` y `MODAL.md` |
| Cada entrenamiento: adaptador en `HF_REPO` (etiquetas `<corrida>-paso-<N>`, `<corrida>-final` y `final`), corrida en W&B y `corridas/<corrida>/` | `modal run --detach modal_entrenar.py --corrida <corrida>` (corre `entrenar.py`) | `entrenar.yaml` (semilla 20261117) y el archivo de datos, cuyo sha256 queda en W&B y en `corrida.json` del repo de HF |
| `corridas/<version>/` (trazas, resultados y resumen de la evaluación) | `admision.correr` (sección 4) | `entrega.py`, la revisión del adaptador y el prompt que fija `entrega.py` |
| `revision_parte1.md` (cifras) | `uv run python revisar_parte1.py` | `historial/`, `curado/auditoria.csv` |

Los comandos de Modal (lanzar, ver logs, bajar resultados y retomar) están en
[`modal_entrenamiento.md`](modal_entrenamiento.md) para el entrenamiento y en
[`MODAL.md`](MODAL.md) para la evaluación y la optimización de prompt.

## 6. Cómo se conecta el agente

```mermaid
flowchart LR
    R["admision.correr<br/>(runner de la cátedra)"] -->|"casos: paciente_id y paso()"| A
    subgraph E["entrega.py"]
        A["Agente<br/>construir_agente / jugar_lote"]
        B["Buscador<br/>parte2/rag_buscador.py<br/>BM25 sección + apartado, k = 2"]
    end
    A -->|"mensajes: sistema + historia"| M["Gemma 4 E4B + adaptador LoRA<br/>(vLLM, A100 40 GB)"]
    M -->|"JSON: herramienta y argumentos"| A
    HF[("HF_REPO<br/>adaptador, revisión fija")] --> M
    P["prompt_optimizado.txt"] --> A
    A -->|"paso(herramienta, argumentos)"| T
    subgraph T["Entorno: las 5 herramientas"]
        T1["leer_triage"]
        T2["preguntar"]
        T3["verificar_afiliacion"]
        T4["buscar_normativa"]
        T5["registrar_decision"]
    end
    T4 -->|"recuperar(consulta, k)"| B
    B --> N[("normas de la versión<br/>secciones + parametros.yaml")]
    T -->|"observación"| A
    T5 -->|"ficha"| R
```

## Partes 1 y 2 en una línea

- **Parte 1:** `curar.py` clasifica el historial (1.590 correctas, 240 errores,
  170 ruido) y documenta dos costumbres: el aviso al voluntariado para mayores
  sin acompañante y la prepaga cuando se presentan dos credenciales. La
  revisión de [`revision_parte1.md`](revision_parte1.md) muestra que el corte de
  edad es 75 y no 76, y que los avisos sin explicar son ruido de tres
  operadores; la clasificación todavía no incorpora esa corrección.
- **Parte 2:** el buscador da recall 1,000, precisión 0,567, 590 tokens por
  consulta y 60 de 60 consultas completas en `rag/consultas_dev.jsonl`, contra
  0,875, 0,492, 580 y 51 de 60 de la referencia BM25 de la cátedra.
