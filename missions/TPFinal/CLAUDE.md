# CLAUDE.md — TP Final: agente de admisión de guardia

Reglas comunes: [`../../CLAUDE.md`](../../CLAUDE.md). Enunciado y manual oficial:
[`mission.md`](mission.md) y [`KIT.md`](KIT.md) (el manual del kit; `README.md` es el del grupo).

## Contrato del kit

- No modificar `admision/`; la cátedra ejecuta su propia copia.
- Conservar los datos originales de `historial/`, `normas/`, `practica/`, `rag/`
  y `entrenamiento/` sin ediciones manuales.
- Los artefactos derivados se generan desde scripts versionados y se documentan.
- `historial_clasificado.csv` mantiene las columnas requeridas `id,tipo` y una
  etiqueta por cada admisión.
- Las reglas escritas y las costumbres empíricas se justifican por separado.
- Las conversaciones usan el formato de `admision/ejemplo.py`; solo las trazas
  correctas entran en el conjunto real. Los datos sintéticos quedan separados.
- No incluir secretos ni credenciales en el repositorio.

## Parte 1

Desde esta carpeta, ejecutar `uv sync`, luego `uv run python curar.py` y
`uv run python generar_sinteticas.py`. El primer script genera la clasificación,
las costumbres y las conversaciones reales; el segundo, los ejemplos sintéticos.

La clasificación generada es una primera pasada basada en las normas y en las
costumbres documentadas. Antes de tomarla como entrega final, revisar las filas
de `curado/auditoria.csv` y resolver ambigüedades con el equipo.

## Estado del proyecto
<!-- Lo actualiza /collect-memory al cerrar cada sesión. -->

- Partes 1 a 5: HECHAS; `INFORME.md` no tiene ningún `PENDIENTE`. La entrega final es `config.yaml`
  (`prompt_optimizado.txt` y el adaptador `sft-prompt-v1-r1-final`, `Juanlu1/gemma-admision@a5af001`): 26, 25 y 28
  casos de práctica (original, b y c), contra 25, 24 y 25 de la cátedra. El commit entregado lleva el tag `entrega-final`.
- La entrega final se evaluó dos veces (`sft_prompt` y `sft_prompt_rep`): mismas fichas en los 150 casos;
  `comparar_corridas.py` compara dos etiquetas caso por caso.
- En `corridas/` están el historial, la configuración y las métricas de sistema (`wandb_system.jsonl`) de los 4 runs
  de W&B, las etiquetas de HF (`exportar_registros.py`) y el costo de Modal por app, hora y recurso
  (`modal_billing_2026-11.csv`: $16,13, todo con créditos del plan Starter; el comando está en la Parte 5).
- Falta, fuera del repo: la presentación en Loom y el mail de entrega (viernes 20/11/2026), con el tag como commit.

## Decisiones tomadas
<!-- Qué se decidió y por qué. -->

- Todo número de `INFORME.md` cita un archivo versionado (normalmente en `corridas/`) y el comando, el punto de
  control (repo de HF y revisión), el prompt y el run de W&B que lo producen. Si no hay archivo, queda `PENDIENTE`:
  lo que solo se vio en W&B o en un log de Modal se exporta antes de citarlo.
- El punto de control de cada entrenamiento se elige por menor pérdida de validación; los intermedios no se evalúan
  sobre la práctica por presupuesto y tiempo.
- La Parte 5 convierte segundos a dinero con la tarifa de la A100-40GB que sale del propio CSV de Modal ($2,10 la hora
  entera): costo por caso = `jugar_lote` × tarifa / casos. Los segundos por caso son de lote, no latencia de un caso solo.
- Cada app de Modal se ata a su corrida cruzando la hora del CSV, la fecha del run de W&B y los segundos de GPU contra
  la duración registrada. Se cita el costo sin salida de red ($16,13, el del panel de Modal).
- La caché KV sin adaptador se cita de `corridas/base/modal.log` (misma versión de vLLM que la entrega), no de GEPA.

## Convenciones del equipo
<!-- Formato de commits, naming y preferencias. -->

- Para repetir la evaluación sin entrenar se usa `--config config_base.yaml`: desde `c23fbcc` `config.yaml` es la
  entrega final, con adaptador.
- Commits chicos, uno por cambio, con el porqué en el mensaje. Al terminar: `git pull --rebase` y push a `main`.
- El CSV de Modal se baja con `COLUMNS=1000` (si no, la CLI corta las líneas) y con `--resolution h` en rangos de 7
  días como máximo. Los logins de Modal y W&B se hacen en una terminal aparte (el `!` del agente no es interactivo); los
  tokens quedan en `~/.modal.toml` y `~/.netrc`, fuera del repo.
- `corridas/prueba-*/` está en `.gitignore`: los archivos de `prueba-gpu-02` se agregan con `git add -f`.
