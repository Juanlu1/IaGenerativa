# TP final — parte 2: buscador de normas

Este trabajo está aislado del curado del historial (parte 1) y del futuro
`entrega.py` común. El buscador se construye en cada corrida con la carpeta de
normas recibida; no tiene valores numéricos fijados en el código ni usa servicios
externos. Usa `admision.normas.cargar_normas` del kit oficial para cargar las
normas y sus parámetros, y un ranking BM25 propio para recuperarlas.

## Archivos

- `rag_buscador.py`: implementación de `construir_buscador(ruta_normas)` y
  `BuscadorNormas.recuperar(consulta, k)`. Por defecto devuelve dos secciones
  completas; `k_entorno = 2`.
- `entrega_rag.py`: adaptador temporal para `admision.evaluar_rag`. Incluye la
  función `construir_agente` requerida por el cargador, pero esta todavía no
  implementa el agente.
- `comparar_rag.py`: reproduce la comparación de granularidades en el set de
  desarrollo.
- `diagnosticar_rag.py`: enumera consultas cuya evidencia no se recuperó.
- `test_rag_buscador.py`: verifica que los valores salen de la carpeta recibida
  y que `recuperar` respeta `k`.

## Evaluación oficial

Desde `missions/TPFinal` del kit de la cátedra, con el paquete `admision`
instalado (por ejemplo, `uv sync`):

```bash
uv run python -m admision.evaluar_rag \
  --entrega <ruta-al-repo-del-grupo>/tpfinal/entrega_rag.py \
  --normas normas/original \
  --consultas rag/consultas_dev.jsonl
```

Resultado de esta versión en las 60 consultas de desarrollo con las normas
originales (7 de noviembre de 2026):

- Referencia BM25 de la cátedra: recall 0,875; precisión 0,492;
  580 tokens por consulta; 51/60 consultas con toda la evidencia.
- Este buscador: **recall 0,900**; **precisión 0,508**;
  587 tokens por consulta; **53/60** consultas con toda la evidencia.

La evaluación con presupuestos fijos dio recall 0,633 con 256 tokens, 0,758
con 512 y 0,967 con 1024. Son métricas del buscador aislado; **todavía falta
medir cuántos casos resuelve el agente con él**. Esa medición es la que más
importa para la nota.

## Experimentos y decisión

El primer prototipo recuperaba tres apartados (`§`) por consulta: 0,767 de
recall, 0,289 de precisión y 261 tokens por consulta. Las preguntas
coloquiales y las que pedían dos reglas perdían evidencia. Al recuperar dos
secciones completas con la misma tokenización, el recall subió a 0,892 y la
precisión a 0,500, con 586 tokens. Añadir una raíz corta a las palabras para
equiparar formas como «verificar» y «verifica» llevó el recall a 0,917. Se
ajustó luego la expansión de «ART» para evitar que coincidiera por accidente
con palabras como «parte»; el resultado final es el de arriba.

`comparar_rag.py` permite comparar las variantes actuales: tres apartados,
dos secciones y dos opciones híbridas que devuelven dos o tres apartados de
cada sección elegida. Las variantes más cortas ahorran contexto, pero
recuperan menos evidencia en este set. Se eligieron secciones completas para
esta primera integración. Las 60 consultas sirven para desarrollar el RAG;
no son una estimación de su rendimiento en el test secreto.

## Integración con el agente del grupo

Cuando se cree `tpfinal/entrega.py`, importar la función de este módulo:

```python
from rag_buscador import construir_buscador

# construir_agente() lo implementa quien integre el modelo y el prompt.
```

El cargador oficial añade la carpeta de `entrega.py` al `sys.path`, así que
este import funciona si ambos archivos están en `tpfinal/`. El kit `admision`
debe instalarse como dependencia del proyecto del grupo, con versiones
fijadas en `pyproject.toml` y `uv.lock`. No se copia ni se modifica
`admision/` en el repositorio del grupo.

Antes de la entrega final hay que probar el agente con `normas/original`,
`normas/b` y `normas/c`, y registrar casos resueltos, contexto y tiempo por
caso. La parte 1 puede avanzar en paralelo: este buscador no lee el historial.
