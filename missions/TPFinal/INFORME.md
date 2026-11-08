# Informe — TP Final: agente de admisión de guardia

## Parte 1 — Curado e ingeniería de datos

### Método

`curar.py` enlaza cada registro de `historial/historial.csv` con su traza del
mismo ID y evalúa los campos de la ficha contra las normas originales y sus
parámetros. También revisa consultas y verificaciones de cobertura en la traza.
Una violación escrita clasifica la fila como `error`; si no la hay, una
desviación de las costumbres documentadas clasifica como `ruido`; las demás
filas quedan `correcta`. Los motivos por fila quedan en `curado/auditoria.csv`.

La primera ejecución cubrió las 2.000 filas y sus 2.000 trazas:

| Tipo | Filas |
|---|---:|
| Correcta | 1.590 |
| Error | 240 |
| Ruido | 170 |

La clasificación es una primera pasada automatizada. Antes de usarla como
resultado final, el equipo debe revisar las filas de `curado/auditoria.csv`, en
particular las que tienen más de un motivo o una elección interpretativa.

### Costumbres identificadas

1. **Aviso al voluntariado para una persona de 76 años o más sin acompañante.**
   Aparece en 196 de 215 filas comparables (91%). Fuera de ese grupo, hay 143
   avisos en 1.785 filas (8%). La señal se ve en distintos operadores y no se
   deduce de la edad de box definida por P-ADM-2. La lista de evidencia y las
   excepciones está en `costumbres.md`.
2. **Prioridad de la prepaga cuando se presentan una obra social y una prepaga.**
   Se verificó la prepaga en 184 de 193 casos comparables (95%). Las normas no
   fijan una prioridad entre ambas; las 9 excepciones y la evidencia están en
   `costumbres.md`.

### Conversaciones de entrenamiento

- `curado/conversaciones_reales.jsonl`: 1.590 conversaciones construidas desde
  las trazas clasificadas como correctas, con el mensaje de sistema y el formato
  de herramientas de `admision/ejemplo.py`.
- `curado/conversaciones_sinteticas.jsonl`: 500 conversaciones generadas por
  `admision.generador` y resueltas por una política determinista que usa las
  normas y costumbres anteriores. La generación reparte las versiones
  `original`, `b` y `c`, con sus parámetros correspondientes. La semilla es
  `20261108`; la configuración está en `curado/sinteticas_config.json`.
- Las 800 trazas de referencia de la cátedra permanecen separadas en
  `entrenamiento/trazas.jsonl`.

La distribución real y las frecuencias sintéticas se registran en
`curado/resumen.json` y `curado/sinteticas_resumen.json`. Las conversaciones
sintéticas se mantienen separadas de las trazas reales para poder ponderarlas o
excluirlas al entrenar.

### Regeneración

Desde esta carpeta, con el entorno preparado mediante `uv sync`:

```powershell
uv run python curar.py
uv run python generar_sinteticas.py
```

`curar.py` genera `historial_clasificado.csv`, `costumbres.md`,
`curado/auditoria.csv`, `curado/conversaciones_reales.jsonl` y
`curado/resumen.json`. `generar_sinteticas.py` genera las conversaciones
sintéticas y sus archivos de configuración y resumen.

## Parte 2 — Buscador propio (RAG)

### Método

`parte2/rag_buscador.py` construye el índice con la carpeta de normas recibida
en cada corrida, mediante el cargador oficial de `admision.normas`. Usa un
ranking BM25 propio que combina la similitud de la sección completa y la de
su apartado más pertinente. Devuelve dos secciones completas para conservar
las excepciones, precedencias y valores de parámetros. No llama a servicios
externos durante la búsqueda ni contiene números de las normas fijados en el
código. Los experimentos y su justificación están en `parte2/RAG.md`.

### Evaluación aislada

Comando, desde esta carpeta:

```powershell
uv run python -m admision.evaluar_rag --entrega parte2/entrega_rag.py --normas normas/original --consultas rag/consultas_dev.jsonl
```

Sobre las 60 consultas de desarrollo, el buscador obtuvo recall de evidencia
**1,000**, precisión **0,567**, **590 tokens por consulta** y **60/60** consultas
con toda la evidencia. La referencia BM25 de la cátedra informa 0,875, 0,492,
580 tokens y 51/60, respectivamente. Los tokens siguen la estimación del
evaluador oficial de cuatro caracteres por token.

`parte2/evaluar_variantes_rag.py` repite la evaluación con `original`, `b` y
`c`. Como el set de desarrollo contiene los números de `original`, el script
ajusta solo esas evidencias numéricas en memoria para cada versión. Dio 60/60
en las tres versiones. Es una prueba de que el buscador lee los parámetros de
la carpeta recibida, no un test independiente.

También se comparó el ranking con las 2.457 búsquedas de las 800 trazas de
referencia mediante `parte2/validar_trazas_rag.py`. La unión de secciones
recuperadas por caso cubrió 2.891 de los 3.652 IDs de `fundamentos` anotados
en esas fichas, igual que el ranking solo por sección; el ranking elegido usó
540 tokens promedio por búsqueda frente a 552 de esa alternativa. Los
`fundamentos` no son etiquetas oficiales por consulta, así que este contraste
sirve para detectar regresiones, no para puntuar al agente.

**Pendiente:** conectar `construir_buscador` con el `entrega.py` del grupo y
medir casos resueltos, contexto, costo y tiempo con un agente ejecutable.
El 60/60 corresponde al set de desarrollo del RAG; no estima el test secreto.
