# TP final — parte 2: buscador de normas

Este trabajo está aislado del curado del historial (parte 1) y del futuro
`entrega.py` común. El buscador se construye en cada corrida con la carpeta de
normas recibida; no tiene valores numéricos fijados en el código ni usa servicios
externos. Usa `admision.normas.cargar_normas` del kit oficial para cargar las
normas y sus parámetros, y un ranking BM25 propio para recuperarlas.

## Archivos

- `rag_buscador.py`: implementación de `construir_buscador(ruta_normas)` y
  `BuscadorNormas.recuperar(consulta, k)`. Por defecto ordena las normas con
  una combinación de BM25 por sección y por apartado, y devuelve dos secciones
  completas; `k_entorno = 2`.
- `entrega_rag.py`: adaptador temporal para `admision.evaluar_rag`. Incluye la
  función `construir_agente` requerida por el cargador, pero esta todavía no
  implementa el agente.
- `comparar_rag.py`: reproduce la comparación de granularidades en el set de
  desarrollo.
- `experimentar_ranking.py`: documenta la comparación entre ranking por
  sección, por apartado y mixto; incluye un experimento de expansión por citas
  que no se eligió.
- `diagnosticar_rag.py`: enumera consultas cuya evidencia no se recuperó.
- `evaluar_variantes_rag.py`: comprueba las tres versiones de normas. Ajusta
  solo las evidencias numéricas del set de desarrollo en memoria, sin modificar
  los archivos de la cátedra.
- `validar_trazas_rag.py`: contraste auxiliar con las consultas reales de las
  800 trazas de referencia.
- `test_rag_buscador.py`: verifica que los valores salen de la carpeta recibida
  y que `recuperar` respeta `k`.

## Evaluación oficial

Desde `missions/TPFinal`, con el paquete `admision` instalado (por ejemplo,
`uv sync`):

```bash
uv run python -m admision.evaluar_rag \
  --entrega parte2/entrega_rag.py \
  --normas normas/original \
  --consultas rag/consultas_dev.jsonl
```

Resultado de esta versión en las 60 consultas de desarrollo con las normas
originales (7 de noviembre de 2026):

- Referencia BM25 de la cátedra: recall 0,875; precisión 0,492;
  580 tokens por consulta; 51/60 consultas con toda la evidencia.
- Este buscador: **recall 1,000**; **precisión 0,567**;
  590 tokens por consulta; **60/60** consultas con toda la evidencia.

La evaluación con presupuestos fijos dio recall 0,692 con 256 tokens, 0,842
con 512 y 1,000 con 1024. Son métricas del buscador aislado; **todavía falta
medir cuántos casos resuelve el agente con él**. Esa medición es la que más
importa para la nota.

Para comprobar que los parámetros no quedan memorizados en el buscador:

```bash
uv run python parte2/evaluar_variantes_rag.py \
  --normas normas \
  --consultas rag/consultas_dev.jsonl
```

Con `original`, `b` y `c` resultó 60/60 en cada caso, con las evidencias
numéricas adaptadas a los parámetros de cada versión. Esta es una prueba
derivada del set de desarrollo, **no** una evaluación oficial adicional.

## Experimentos y decisión

El primer prototipo recuperaba tres apartados (`§`) por consulta: 0,767 de
recall, 0,289 de precisión y 261 tokens por consulta. Las preguntas
coloquiales y las que pedían dos reglas perdían evidencia. Al recuperar dos
secciones completas con la misma tokenización, el recall subió a 0,892 y la
precisión a 0,500, con 586 tokens. Añadir una raíz corta a las palabras para
equiparar formas como «verificar» y «verifica» llevó el recall a 0,917. Se
ajustó luego la expansión de «ART» para evitar que coincidiera por accidente
con palabras como «parte»; quedó en 0,900.

La siguiente pasada conservó «sin» como término significativo y amplió
paráfrasis generales, como «abuela» → edad mayor, «desmayado» → no puede
responder y ausencia de obra social/prepaga → sin cobertura. El recall subió a
0,983 con dos secciones. Después se combinaron dos señales: relevancia de la
sección completa y del mejor apartado dentro de ella. Una pequeña ventaja a
las normas cuyos parámetros miden niveles cuando la pregunta menciona un
«nivel» llevó las 60 consultas a evidencia completa. Esas reglas son de
recuperación; no contienen respuestas, valores de parámetros ni IDs de las
consultas de desarrollo. Un intento de promover secciones solo porque estaban
citadas por la primera recuperada empeoró los resultados y se descartó.

Antes de elegir el ranking final se contrastó con las **2.457 búsquedas** de
las 800 trazas de referencia, que no son el set de 60 consultas. El ranking
final y el ranking solo por sección cubrieron ambos 2.891 de los 3.652 IDs de
`fundamentos` anotados en las fichas, contando la unión de búsquedas por caso.
El ranking final usó en promedio 540 tokens por búsqueda, frente a 552 del
ranking solo por sección. Los `fundamentos` no son etiquetas oficiales por
consulta ni prueban aciertos del agente; la comparación solo detecta
regresiones evidentes en preguntas que un agente realmente hizo. Se reproduce
con `validar_trazas_rag.py --normas normas/original --trazas
entrenamiento/trazas.jsonl`.

`comparar_rag.py` permite comparar las variantes actuales: tres apartados,
dos secciones, dos opciones híbridas que devuelven dos o tres apartados por
sección y el ranking mixto elegido. Las variantes más cortas ahorran
contexto, pero recuperan menos evidencia en este set. Se conservan las
secciones completas para darle al agente también las excepciones y reglas de
precedencia. Las 60 consultas se usaron para desarrollar el RAG; alcanzar
60/60 ahí **no** estima su rendimiento en el test secreto.

## Integración con el agente del grupo

Cuando se cree `missions/TPFinal/entrega.py`, importar la función de este módulo:

```python
from parte2.rag_buscador import construir_buscador

# construir_agente() lo implementa quien integre el modelo y el prompt.
```

El cargador oficial añade la carpeta de `entrega.py` al `sys.path`, así que
este import funciona desde la raíz de la misión. El grupo conserva sus
dependencias fijadas en `pyproject.toml` y `uv.lock`; no se modifica
`admision/`.

Antes de la entrega final hay que probar el agente con `normas/original`,
`normas/b` y `normas/c`, y registrar casos resueltos, contexto y tiempo por
caso. La parte 1 puede avanzar en paralelo: este buscador no lee el historial.
