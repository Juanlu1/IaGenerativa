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

- Partes 1 a 4: HECHAS. La entrega final es `config.yaml` (`prompt_optimizado.txt` y el adaptador
  `sft-prompt-v1-r1-final`, `Juanlu1/gemma-admision@a5af001`): 26, 25 y 28 casos de práctica (original, b y c).
- Parte 5 (recursos y producción): PENDIENTE, la escribe otra integrante. `INFORME.md` le deja la lista de fuentes.
- Parte 4 sin PENDIENTE. La entrega final se evaluó dos veces (`sft_prompt` y `sft_prompt_rep`): mismas fichas en
  los 150 casos; `comparar_corridas.py` compara dos etiquetas caso por caso.
- El historial y la configuración de los 4 runs de W&B y las etiquetas de HF ya están en `corridas/`
  (`exportar_registros.py`).

## Decisiones tomadas
<!-- Qué se decidió y por qué. -->

- Todo número de `INFORME.md` cita un archivo versionado (normalmente en `corridas/`) y el comando, el punto de
  control (repo de HF y revisión), el prompt y el run de W&B que lo producen. Si no hay archivo, queda `PENDIENTE`:
  lo que solo se vio en W&B o en un log de Modal se exporta antes de citarlo.
- El punto de control de cada entrenamiento se elige por menor pérdida de validación; los intermedios no se evalúan
  sobre la práctica por presupuesto y tiempo.

## Convenciones del equipo
<!-- Formato de commits, naming y preferencias. -->

- Para repetir la evaluación sin entrenar se usa `--config config_base.yaml`: desde `c23fbcc` `config.yaml` es la
  entrega final, con adaptador.
- Commits chicos, uno por cambio, con el porqué en el mensaje. Al terminar: `git pull --rebase` y push a `main`.
