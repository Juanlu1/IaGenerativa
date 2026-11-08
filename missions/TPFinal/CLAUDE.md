# CLAUDE.md — TP Final: agente de admisión de guardia

Reglas comunes: [`../../CLAUDE.md`](../../CLAUDE.md). Enunciado y manual oficial:
[`mission.md`](mission.md) y [`README.md`](README.md).

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
