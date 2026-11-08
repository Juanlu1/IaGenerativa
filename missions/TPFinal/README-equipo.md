# TP Final — trabajo del grupo

Este directorio contiene el kit oficial de la misión de admisión de guardia,
descargado desde `austral-ing-ai/talksmith-ing` en la revisión indicada por
[`KIT_VERSION.md`](KIT_VERSION.md). El manual de instalación y el contrato
oficial están en [`README.md`](README.md); el enunciado, en [`mission.md`](mission.md).

## Parte 1: estado inicial

El historial trae 2.000 filas y sus 2.000 trazas. El script `curar.py` compara
las fichas con las reglas de registro, ubicación, circuitos y cobertura, y usa
las trazas para revisar consultas y verificaciones. También separa las
costumbres no escritas de las infracciones normativas.

Desde esta carpeta:

```powershell
uv sync
uv run python curar.py
uv run python generar_sinteticas.py
```

El comando genera:

- `historial_clasificado.csv`: salida con el esquema exigido por la cátedra.
- `costumbres.md`: patrones empíricos con IDs de respaldo y excepciones.
- `curado/auditoria.csv`: motivo por fila para revisar errores y ruido.
- `curado/conversaciones_reales.jsonl`: trazas clasificadas `correcta` en formato de mensajes.
- `curado/conversaciones_sinteticas.jsonl`: 500 conversaciones generadas por el simulador oficial con semilla reproducible y las normas `original`, `b` y `c`.
- `curado/resumen.json`: conteos y distribución del conjunto generado.

Las 800 trazas de referencia siguen en `entrenamiento/trazas.jsonl` y no se
mezclan con ninguno de los dos conjuntos. El generador sintético usa el
simulador oficial y una política determinista derivada de normas y costumbres;
reparte los tres juegos de parámetros para reducir la memorización de números
de una sola versión. Revisen su semilla y distribución antes de usarlo para
fine-tuning.

## Reproducibilidad y revisión

El script toma los parámetros de `normas/original/parametros.yaml` y exige que
los IDs de historial y trazas coincidan en número y orden. Los resultados son
una primera clasificación automatizada; revisen especialmente cada fila marcada
en `curado/auditoria.csv` antes de considerarlos definitivos.
