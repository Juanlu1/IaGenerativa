# Resultados de las corridas

Generado por `uv run python tabla.py` a partir de `corridas/<etiqueta>/<version>/`. No editar a mano.

## Casos resueltos

| Etiqueta | original | b | c |
|---|---:|---:|---:|
| cátedra: sin entrenar | 12/50 | 15/50 | 12/50 |
| cátedra: SFT | 25/50 | 24/50 | 25/50 |
| base | 11/50 | 8/50 | 9/50 |

## Detalle por corrida

- Segundos por caso: `jugar_lote` entero dividido por la cantidad de casos (los casos corren en lote).
- Contexto por caso: caracteres que se le pasaron al modelo en todo el caso, según `admision.correr`.
- Carga del modelo: `construir_agente`, una vez por etiqueta (corrida.json); el modelo se reutiliza en las tres versiones.

| Etiqueta | Versión | Resueltos | Parcial medio | Sin ficha | Búsquedas por caso | Segundos por caso | Contexto por caso (caracteres) | Carga del modelo (s) | Error |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| base | original | 11/50 | 0,800 | 0 | 1,30 | 0,294 | 18.713 | 230,8 |  |
| base | b | 8/50 | 0,793 | 0 | 1,34 | 0,237 | 19.418 | 230,8 |  |
| base | c | 9/50 | 0,793 | 0 | 1,30 | 0,223 | 18.810 | 230,8 |  |
