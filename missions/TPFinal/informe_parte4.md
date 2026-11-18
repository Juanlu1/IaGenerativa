# Parte 4: entrenamiento

Apartado del informe para la Parte 4. Los números que todavía no se midieron
dicen **PENDIENTE**: se completan con los comandos indicados, nunca a mano.
Los comandos de Modal están en [`modal_entrenamiento.md`](modal_entrenamiento.md).

## Estrategia

Fine-tuning supervisado (SFT) con LoRA sobre `google/gemma-4-E4B-it`, en bf16,
en una A100 de 40 GB. El entrenamiento le enseña al modelo el oficio: el
protocolo JSON de las herramientas, el orden de los pasos, qué buscar, a quién
preguntar, qué verificar y las costumbres del hospital. Los números de las
normas no se aprenden: llegan en cada caso por `buscar_normativa`, así que el
conjunto de datos los hace variar (ver abajo).

- **Pérdida solo sobre el asistente.** Las respuestas del modelo (una llamada
  JSON por turno, más la marca de fin de turno `<turn|>`) son lo único que
  suma a la pérdida. El sistema, los resultados de las herramientas y el
  primer mensaje quedan en -100. La plantilla de Gemma 4 no trae las marcas
  `{% generation %}` que usa TRL para esto, así que `entrenar.py` arma las
  etiquetas con los offsets del tokenizador. En la prueba se controló que los
  tramos marcados, decodificados, son exactamente los turnos del asistente
  más su `<turn|>`: con la plantilla de chat real de `google/gemma-4-E4B-it`
  (solo su `chat_template.jinja`, sin bajar el modelo), la máscara fue exacta
  en las 150 conversaciones de val. En las 16 conversaciones de la prueba,
  4.512 de 46.421 tokens entran en la pérdida (9,7%, con el tokenizador del
  modelo diminuto).
- **Compatible con vLLM.** `entrega.py` carga el adaptador con el soporte LoRA
  de vLLM 0.34.0. Según su código (`vllm/model_executor/models/gemma4.py`,
  `gemma4_mm.py` y `vllm/config/lora.py`), para Gemma 4 acepta LoRA en
  `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj` y
  `down_proj` del modelo de lenguaje, y ranks 1, 8, 16, 32, 64, 128, 256, 320
  o 512 (`max_lora_rank`). Las torres de visión y audio solo admiten LoRA con
  `enable_tower_connector_lora`, experimental, así que el adaptador no las
  toca: `entrenar.py` usa una expresión regular que deja afuera `vision` y
  `audio`, y antes de subir cada punto de control verifica rank, módulos,
  ausencia de `modules_to_save` y de DoRA. Los nombres de los tensores quedan
  como `base_model.model.model.language_model.layers.N...`, que vLLM mapea a
  `language_model.model.layers.N...`. `entrega.py` tiene que usar
  `enable_lora=True` y `max_lora_rank=32`.
- **Dos variantes de datos**, para la tabla: "solo entrenamiento" con el
  mensaje de sistema de `admision/ejemplo.py` y "las dos cosas juntas" con
  `prompt_optimizado.txt`. Solo cambia el mensaje de sistema; las
  conversaciones son las mismas.

## Conjunto de datos

`armar_dataset.py` (semilla 20261117) junta tres orígenes en el formato del
README del kit y separa 5% de cada origen para validación. Cifras de
`datos/resumen.json` (variante con el prompt de `admision/ejemplo.py`):

| Origen | Conversaciones | Train | Val |
|---|---:|---:|---:|
| Historial, filas `correcta` de `historial_clasificado.csv` (normas originales) | 1.600 | 1.520 | 80 |
| Trazas de la cátedra, `entrenamiento/trazas.jsonl` (valores variables) | 800 | 760 | 40 |
| Sintéticas, `curado/conversaciones_sinteticas.jsonl` (200 por versión: original, b y c) | 600 | 570 | 30 |
| **Total** | **3.000** | **2.850** | **150** |

- Tokens totales: 7.992.888 (train 7.599.855, val 393.033), estimados como
  caracteres / 4, igual que `admision.evaluar_rag`. Por conversación: media
  2.664, mediana 2.699, percentil 95 3.432 y máximo 3.729 (`E-177`). El
  mensaje de sistema de `admision/ejemplo.py` son 558 de esos tokens por
  conversación. Los tokens reales del tokenizador de Gemma quedan en
  `corridas/<corrida>/datos.json` y en W&B. En la prueba de la Mac, las
  primeras 16 conversaciones de train dieron 46.421 tokens con el
  tokenizador del modelo diminuto, contra 42.194 estimados. Ese tokenizador
  no es idéntico al de Gemma 4 E4B (otro sha256 de `tokenizer.json`), así que
  la relación real sale de la prueba en GPU: PENDIENTE.
- `datos/train.jsonl` pesa 31,7 MB y `datos/val.jsonl` 1,6 MB: van en git.
  Si una variante pasa los 50 MB, se publica con `armar_dataset.py
  --subir-hf` en un repo de dataset de HF (ver `modal_entrenamiento.md`).
- sha256 de `datos/train.jsonl`:
  `16830998562d978367220e329a3595673287a0889dcf886c14ad89cd88bcd072`. Dos
  corridas seguidas de `armar_dataset.py` dieron el mismo hash. La versión
  anterior, armada con la clasificación de la primera pasada (corte del
  voluntariado en 76 años, 1.590 filas correctas), tenía 2.990 conversaciones
  y el hash `a1e640db...` y no se usó para entrenar.

### Las búsquedas muestran los números de cada traza

Cada traza de la cátedra usa sus propios valores de las normas (por ejemplo,
P-ADM-2 toma 8 valores entre 55 y 80 años en las 800 trazas). Si las
búsquedas se rehicieran con `normas/original`, el modelo vería un número en la
búsqueda y una ficha decidida con otro, y aprendería a ignorar la búsqueda.
Copiar el resultado original de la traza tampoco alcanza: viene del BM25 de la
cátedra, no del buscador que va a usar el agente.

La solución aprovecha que los textos de las normas son idénticos en las tres
versiones (`diff` de `normas/original`, `b` y `c` solo difiere en
`parametros.yaml`) y que cada resultado de búsqueda termina con su línea
`Valores: ...`. Para cada traza, `armar_dataset.py`:

1. lee los valores que muestran sus propios resultados de búsqueda;
2. arma una carpeta temporal con los textos de `normas/original` y un
   `parametros.yaml` con esos valores. Los parámetros que no cambian entre
   versiones (P-COB-1 y los de otras áreas) se toman de `normas/original`;
3. rehace cada búsqueda con `parte2/rag_buscador.py` sobre esa carpeta, con la
   misma consulta de la traza.

Si el buscador citara un parámetro que varía entre versiones y que la traza
nunca mostró, esa búsqueda conserva el resultado original. Resultados en este
conjunto: 7.316 búsquedas rehechas, **0** con resultado original y 5.478 que
devolvieron las mismas secciones que la traza; en esas 5.478 el texto nuevo
coincide carácter por carácter con el original, lo que confirma que los
valores reconstruidos son los de cada traza. Con `--busquedas originales` se
puede armar la variante que copia los resultados de la traza, para comparar.

### Sintéticas

`generar_sinteticas.py` genera 600 casos con `admision.generador` (semilla
20261108) y los juega con una política determinista, en el simulador oficial,
con el buscador del grupo armado con la versión de normas de cada caso (200
por versión). Las consultas siguen las 14 plantillas y el orden de pasos de
las trazas de la cátedra, que son las que va a escribir el agente.

Antes de usarla, la política se validó contra las fichas esperadas de la
práctica con el comparador oficial (`uv run python validar_politica.py`):

| Pasada | original | b | c |
|---|---:|---:|---:|
| Costumbre del voluntariado con corte en 76 años (`costumbres.md`) | 49/50 | 49/50 | 49/50 |
| Corte en 75 años | **50/50** | **50/50** | **50/50** |

El único fallo de la primera pasada fue `pev-006` (75 años, sin acompañante):
el historial muestra el corte en 75 (ver [`revision_parte1.md`](revision_parte1.md)).
Esa corrección se aplicó también a la clasificación del historial, lo que suma
10 conversaciones reales.

**Cuidado al leer la tabla final:** como las sintéticas usan las normas b y c
para que el modelo no memorice los números de `original`, la evaluación de
práctica con b y c deja de ser del todo independiente de los datos de
entrenamiento (no hay casos de práctica en el entrenamiento, pero sí los
valores de esas versiones). El test de la cátedra usa otros números; las
trazas de la cátedra, con valores que varían traza a traza, son lo que más
se le parece.

## Configuración

`entrenar.yaml`, comentado valor por valor. Lo principal:

| Parámetro | Valor | Por qué |
|---|---|---|
| Modelo | `google/gemma-4-E4B-it`, bf16, SDPA | el del enunciado; ~16 GB en bf16 |
| LoRA | r = 32, alpha = 32, dropout 0,05 | rank aceptado por vLLM; ~1% de parámetros |
| Módulos | q/k/v/o_proj, gate/up/down_proj del modelo de lenguaje | lo que carga vLLM |
| Épocas | 3 | ~530 pasos; a confirmar con la prueba chica |
| lr | 1e-4, coseno, 3% de calentamiento | habitual en LoRA |
| Batch | 2 por paso x 8 de acumulación = 16 conversaciones | logits de 262.144 tokens de vocabulario |
| Largo máximo | 6.144 tokens (se descartan, no se truncan) | la más larga ronda 3.700 estimados |
| Gradient checkpointing | sí | memoria de activaciones |
| Semilla | 20261117 | datos, LoRA y dropout |
| Puntos de control | cada 100 pasos, a `HF_REPO` | con estado para retomar |

La duración de 2 a 4 horas es una estimación (unos 23 millones de tokens
procesados a 2.000 o 3.000 tokens por segundo), no una medición. La prueba
chica en GPU mide segundos por paso y VRAM; con eso se ajustan las épocas.

Dependencias fijadas en `deps_entrenamiento.txt`: torch 2.14.0, transformers
5.22.2, trl 1.17.1, peft 0.21.2, accelerate 1.15.0, datasets 5.1.0,
huggingface_hub 2.4.0, wandb 0.31.0, pyyaml 6.0.3 y modal 1.6.4. torch y
transformers son las que acepta vllm 0.34.0 (`torch==2.14.0`,
`transformers<5.23.0`).

## Auditabilidad de cada corrida

- **W&B:** configuración completa, semilla, comando, ruta y sha256 de
  `train.jsonl` y `val.jsonl` (también como artefacto de tipo dataset),
  tokens reales, conversaciones descartadas, parámetros entrenables, VRAM
  máxima y la revisión de HF de cada punto de control.
- **Hugging Face (`HF_REPO`):** un commit por punto de control con el
  adaptador en la raíz (lo carga vLLM tal cual), `estado/` para retomar y
  `corrida.json` con corrida, paso, semilla, sha256 de los datos, configuración
  y link de W&B. Etiquetas `<corrida>-paso-<N>`, `<corrida>-final` y `final`
  (esta última solo en corridas completas).
- **Repositorio:** `corridas/<corrida>/resumen.json`, `revisiones.json`,
  `datos.json` y `config_usada.yaml`, bajados del volumen de Modal.

## Comandos

```bash
uv run python validar_politica.py                     # política sintética contra la práctica
uv run python generar_sinteticas.py                   # 600 conversaciones sintéticas
uv run python armar_dataset.py                        # datos/ (solo entrenamiento)
uv run python armar_dataset.py --prompt prompt_optimizado.txt --salida datos/con_prompt
uv run --with-requirements deps_entrenamiento.txt python entrenar.py --prueba
modal run --detach modal_entrenar.py --corrida prueba-gpu-01 --max-pasos 20
modal run --detach modal_entrenar.py --corrida sft-ejemplo-v1
modal run --detach modal_entrenar.py --corrida sft-prompt-v1 \
    --datos datos/con_prompt/train.jsonl --val datos/con_prompt/val.jsonl
```

## Resultados

Casos resueltos de los 50 de práctica, con las normas completas. La evaluación
corre `admision.correr practica` con `entrega.py` (sección 4 del
[`README.md`](README.md)); cada celda debe citar el punto de control y el
prompt que la producen.

| Variante | Punto de control | Prompt | original | b | c |
|---|---|---|---:|---:|---:|
| Referencia de la cátedra, sin entrenar | - | `admision/ejemplo.py` | 12 | 15 | 12 |
| Referencia de la cátedra, SFT con las 800 trazas | - | `admision/ejemplo.py` | 25 | 24 | 25 |
| Sin entrenar | modelo base | `admision/ejemplo.py` | PENDIENTE | PENDIENTE | PENDIENTE |
| Solo prompt | modelo base | `prompt_optimizado.txt` | PENDIENTE | PENDIENTE | PENDIENTE |
| Solo entrenamiento | PENDIENTE (`sft-ejemplo-v1-final`) | `admision/ejemplo.py` | PENDIENTE | PENDIENTE | PENDIENTE |
| Prompt + entrenamiento | PENDIENTE (`sft-prompt-v1-final`) | `prompt_optimizado.txt` | PENDIENTE | PENDIENTE | PENDIENTE |

Del entrenamiento: tiempo, pasos, pérdida final de train y val y VRAM máxima
de cada corrida, de `corridas/<corrida>/resumen.json`: **PENDIENTE**.

## Pasadas del desarrollo

1. **Buscador propio de las sintéticas.** La primera versión de
   `generar_sinteticas.py` tenía un buscador de palabras clave fijas y
   consultas inventadas: las conversaciones no mostraban lo que el agente iba
   a ver. Se reemplazó por el buscador del grupo y las consultas de las trazas.
2. **Corte del voluntariado.** La validación contra la práctica dio 49/50 por
   un corte de edad mal tomado del historial (76 en vez de 75). Corregido, 50/50.
3. **API de transformers 5.** La primera prueba de `entrenar.py` falló porque
   `warmup_ratio` y `group_by_length` ya no existen en `TrainingArguments`;
   ahora son `warmup_steps` con una fracción y
   `train_sampling_strategy="group_by_length"`.
4. **Etiqueta final.** Al planear la prueba chica en GPU se vio que movería la
   etiqueta `final` de HF; ahora solo la mueven las corridas completas.
