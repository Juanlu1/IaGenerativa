# Resultados de las corridas

Generado por `uv run python tabla.py` a partir de `corridas/<etiqueta>/<version>/`. No editar a mano.

## Casos resueltos

| Etiqueta | original | b | c |
|---|---:|---:|---:|
| cátedra: sin entrenar | 12/50 | 15/50 | 12/50 |
| cátedra: SFT | 25/50 | 24/50 | 25/50 |
| base | 11/50 | 8/50 | 9/50 |
| base_v034 | 12/50 | 5/50 | 8/50 |
| prompt_corto | 6/50 | 5/50 | 3/50 |
| prompt_optimizado | 8/50 | 10/50 | 10/50 |
| prompt_optimizado_v034 | 9/50 | 10/50 | 10/50 |

## Detalle por corrida

- Segundos por caso: `jugar_lote` entero dividido por la cantidad de casos (los casos corren en lote).
- Contexto por caso: caracteres que se le pasaron al modelo en todo el caso, según `admision.correr`.
- Carga del modelo: `construir_agente`, una vez por etiqueta (corrida.json); el modelo se reutiliza en las tres versiones.

| Etiqueta | Versión | Resueltos | Parcial medio | Sin ficha | Búsquedas por caso | Segundos por caso | Contexto por caso (caracteres) | Carga del modelo (s) | Error |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| base | original | 11/50 | 0,800 | 0 | 1,30 | 0,294 | 18.713 | 230,8 |  |
| base | b | 8/50 | 0,793 | 0 | 1,34 | 0,237 | 19.418 | 230,8 |  |
| base | c | 9/50 | 0,793 | 0 | 1,30 | 0,223 | 18.810 | 230,8 |  |
| base_v034 | original | 12/50 | 0,805 | 0 | 1,30 | 0,303 | 18.766 | 232,4 |  |
| base_v034 | b | 5/50 | 0,780 | 0 | 1,30 | 0,235 | 18.756 | 232,4 |  |
| base_v034 | c | 8/50 | 0,796 | 0 | 1,30 | 0,234 | 18.790 | 232,4 |  |
| prompt_corto | original | 6/50 | 0,760 | 0 | 1,24 | 0,288 | 15.090 | 236,4 |  |
| prompt_corto | b | 5/50 | 0,749 | 0 | 1,24 | 0,231 | 15.109 | 236,4 |  |
| prompt_corto | c | 3/50 | 0,751 | 0 | 1,22 | 0,222 | 14.903 | 236,4 |  |
| prompt_optimizado | original | 8/50 | 0,807 | 0 | 1,86 | 0,343 | 25.395 | 248,1 |  |
| prompt_optimizado | b | 10/50 | 0,800 | 0 | 1,90 | 0,283 | 25.857 | 248,1 |  |
| prompt_optimizado | c | 10/50 | 0,805 | 0 | 1,88 | 0,275 | 25.716 | 248,1 |  |
| prompt_optimizado_v034 | original | 9/50 | 0,813 | 0 | 1,84 | 0,344 | 25.048 | 221,0 |  |
| prompt_optimizado_v034 | b | 10/50 | 0,798 | 0 | 1,88 | 0,285 | 25.291 | 221,0 |  |
| prompt_optimizado_v034 | c | 10/50 | 0,805 | 0 | 1,90 | 0,284 | 25.882 | 221,0 |  |
