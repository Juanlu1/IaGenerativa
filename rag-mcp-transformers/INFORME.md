# Informe — Misión RAG, MCP y Transformers (Hospital Arroyo Claro)

## Parte 1: RAG vectorial

### Configuración entregada

| Perilla | Valor |
|---|---|
| Encoder | `BAAI/bge-m3` |
| Chunking | un fragmento por sección `##` del Markdown (un documento sin secciones es un solo fragmento) |
| Metadatos | se antepone `"<título del documento> — <título de la sección>"` a cada fragmento |
| Top-k | 1 |
| Umbral / margen | no se usan |

Queda fija en `config_rag.json`. Se corre con:

```bash
python3 recuperar.py --preguntas datos/preguntas_recuperacion_dev.jsonl --salida resultados.jsonl
python3 evaluar/evaluar.py recuperacion --preguntas datos/preguntas_recuperacion_dev.jsonl --resultados resultados.jsonl
```

| | Context relevance | Recall | Precision | MRR |
|---|---|---|---|---|
| **Entregada** (bge-m3, sección + metadatos, k=1) | **1,000** | 1,000 | 1,000 | 1,000 |
| Mejor línea de base BERT (sección + metadatos, k=3, margen 0,02) | 0,375 | 0,450 | 0,350 | 0,358 |
| Recuperador léxico ingenuo (dato del enunciado) | 0,35 | — | — | — |

### Cómo se midió

`experimentar.py` corre una grilla de **100 configuraciones**: 5 encoders × 4 chunkings × 5 criterios de selección. Cada configuración se mide con `evaluar/evaluar.py` sin modificar, y su `.eval.json` está en `experimentos/`. La tabla completa, con una fila por configuración, está al final de esta sección.

- **Encoders:**
  - `bert-base`: `google-bert/bert-base-multilingual-cased`, promedio de la última capa pesado por la máscara de atención. Es la línea de base obligatoria.
  - `minilm`: `paraphrase-multilingual-MiniLM-L12-v2`.
  - `e5-small` y `e5-base`: `multilingual-e5-{small,base}`, con los prefijos `query: ` y `passage: `.
  - `bge-m3`.
- **Chunking:**
  - Por sección, sin metadatos.
  - Por sección, con metadatos.
  - Ventanas de 40 palabras con solapamiento de 10.
  - Ventanas de 80 palabras con solapamiento de 20.
- **Selección:**
  - k = 1, 3 y 5, sin filtros.
  - k = 3 con margen relativo de 0,02 y de 0,05. El margen descarta los fragmentos que quedan a más de esa distancia de coseno del mejor.

### Qué muestran los números

**1. Hay que usar un encoder entrenado para similitud.** BERT sin ajustar no pasa de 0,375 en ninguna de sus 20 configuraciones, casi lo mismo que el recuperador léxico del enunciado. Con k=1, sección y metadatos, falla 14 de las 20 preguntas. El promedio de los vectores de BERT representa el texto en general, pero no está entrenado para acercar una pregunta a su respuesta. Los cuatro modelos entrenados para embeddings de oraciones superan 0,90 con la misma configuración:

| Encoder | Mejor context relevance | Configuración |
|---|---|---|
| bert-base | 0,375 | sección + metadatos, k=3, margen 0,02 |
| e5-small | 0,900 | sección + metadatos, k=1 |
| minilm | 0,950 | sección + metadatos, k=1 |
| e5-base | 0,950 | sección + metadatos, k=1 |
| **bge-m3** | **1,000** | sección + metadatos, k=1 |

**2. Por qué ganó bge-m3.** Con la configuración ganadora, MiniLM y e5-base fallan solo la pregunta R01, y e5-small falla la R01 y la R02. La R01 es "Mi papá está en terapia intensiva, ¿a qué hora lo puedo ir a ver al mediodía?". MiniLM y e5-base devuelven la sección de Pediatría ("Madre, padre o tutor pueden permanecer…"): la palabra "papá" los lleva a la sección que habla de los padres. bge-m3 es el único que prioriza "terapia intensiva" y devuelve la sección correcta ("…de 12:00 a 12:30…"). Además, con k=1 bge-m3 queda primero en las cuatro estrategias de chunking:

| Context relevance con k=1 | sección | sección + metadatos | ventana 40/10 | ventana 80/20 |
|---|---|---|---|---|
| bert-base | 0,25 | 0,30 | 0,15 | 0,20 |
| minilm | 0,70 | 0,95 | 0,60 | 0,70 |
| e5-small | 0,80 | 0,90 | 0,60 | 0,80 |
| e5-base | 0,85 | 0,95 | 0,60 | 0,85 |
| **bge-m3** | **0,90** | **1,00** | **0,70** | **0,90** |

La diferencia con e5-base y MiniLM es **una sola pregunta de 20**. No alcanza para decir que bge-m3 es mucho mejor, pero sí que es al menos igual de bueno y que es el único que resuelve este distractor.

**3. Los metadatos ayudan a todos los encoders.** Anteponer el título del documento y de la sección sube *context_relevance* con k=1 en todos los casos: +0,05 con BERT, +0,25 con MiniLM, +0,10 con los dos e5 y con bge-m3. Muchas secciones no dicen de qué sector hablan. Por ejemplo, "Madre y padre tienen ingreso libre las 24 horas" no menciona Neonatología, que es el título de su sección, ni que se trata de visitas, que es el título del documento. El título le agrega ese contexto al embedding.

**4. El corte por sección le gana a las ventanas.** El evaluador exige que la frase de evidencia esté **textual** dentro del fragmento. Una ventana de palabras puede partir esa frase al medio, y entonces el fragmento no cuenta aunque sea el correcto. Con ventanas de 40 palabras, los mejores encoders no pasan de 0,60–0,70. El corte por sección nunca parte una oración.

Las ventanas se probaron sin metadatos, así que la comparación justa es contra "sección" sin metadatos. Contra las ventanas de 40, la sección gana en los cinco encoders. Contra las de 80 empata en los cuatro encoders entrenados para similitud, porque las secciones del corpus son cortas y una ventana de 80 palabras suele abarcar una sección entera. La ventaja decisiva del corte por sección es que tiene un título natural para anteponer: con metadatos, la sección le gana a cualquier ventana en todos los encoders.

**5. k=1 es lo óptimo para esta métrica y este conjunto.** Cada pregunta `dev` tiene una sola frase de evidencia, en una sola sección. Si el primer resultado es el correcto, k=1 da *precision* 1. En cambio, con secciones y k=3, la *precision* queda en 1/3 como máximo y *context_relevance* no pasa de 0,50. Con ventanas llega a 0,575, porque dos ventanas que se solapan pueden contener la misma evidencia. El margen relativo recupera casi todo lo que se pierde (bge-m3 con k=3 y margen 0,02: 0,975), porque solo agrega un segundo fragmento cuando está prácticamente empatado con el primero. El umbral absoluto no se usó, porque la escala del coseno cambia mucho de un encoder a otro y el margen relativo cumple la misma función sin depender de esa escala.

### Por qué se eligió esta configuración y qué riesgos tiene

La regla fijada de antemano en `SPEC.md` es elegir el mayor *context_relevance* en `dev`, y ante diferencias menores a 0,02, la configuración más simple. La entregada es a la vez la mejor y la más simple de la grilla, porque no usa ni umbral ni margen.

Riesgos, porque la cátedra evalúa con preguntas que no vemos:

- **Si el conjunto de test tiene preguntas con evidencia en dos secciones, k=1 pierde recall.** La alternativa era k=3 con margen 0,02: en `dev` da 0,975, y cuando hay un empate devuelve un segundo fragmento. Nos quedamos con k=1 porque el enunciado dice que las preguntas de test son "de la misma forma" que las `dev`, y en `dev` todas tienen una sola frase de evidencia.
- **20 preguntas es una muestra chica.** La ventaja sobre e5-base es una sola pregunta. Por eso la conclusión más fuerte no es "bge-m3 gana", sino las tendencias que se repiten en todos los encoders: usar un encoder entrenado para similitud, cortar por sección, agregar metadatos y devolver pocos fragmentos.
- **Costo:** bge-m3 es el modelo más pesado de los cinco (unos 2,2 GB de descarga). Una vez descargado, `recuperar.py` sobre las 20 preguntas tarda unos 14 segundos en CPU, incluida la carga del modelo. Para el agente de las partes 2 y 3 alcanza: el modelo se carga una sola vez al arrancar.

### Uso desde las partes 2 y 3

```python
from recuperador import Recuperador
r = Recuperador.desde_config()   # una vez, al arrancar
r.buscar(consulta)               # -> list[str]; r.buscar(consulta, k=3) para más contexto
```

### Tabla completa de experimentos

Generada por `experimentar.py` (copia de `experimentos/tabla.md`), ordenada por *context relevance*. Cada fila tiene su archivo en `experimentos/`.

|---|---|---|---|---|---|---|---|---|---|---|---|
| bge-m3 | sección | sí | 1 | — | — | **1.000** | 1.000 | 1.000 | 1.000 | 1.00 | `bge-m3__seccion-meta__k1.jsonl.eval.json` |
| bge-m3 | sección | sí | 3 | — | 0.02 | **0.975** | 1.000 | 0.967 | 1.000 | 1.10 | `bge-m3__seccion-meta__k3-m0.02.jsonl.eval.json` |
| minilm | sección | sí | 1 | — | — | **0.950** | 0.950 | 0.950 | 0.950 | 1.00 | `minilm__seccion-meta__k1.jsonl.eval.json` |
| e5-base | sección | sí | 1 | — | — | **0.950** | 0.950 | 0.950 | 0.950 | 1.00 | `e5-base__seccion-meta__k1.jsonl.eval.json` |
| minilm | sección | sí | 3 | — | 0.02 | **0.933** | 1.000 | 0.900 | 0.975 | 1.20 | `minilm__seccion-meta__k3-m0.02.jsonl.eval.json` |
| bge-m3 | sección | sí | 3 | — | 0.05 | **0.908** | 1.000 | 0.867 | 1.000 | 1.30 | `bge-m3__seccion-meta__k3-m0.05.jsonl.eval.json` |
| bge-m3 | ventana 80/20 | no | 1 | — | — | **0.900** | 0.900 | 0.900 | 0.900 | 1.00 | `bge-m3__ventana80-20__k1.jsonl.eval.json` |
| e5-small | sección | sí | 1 | — | — | **0.900** | 0.900 | 0.900 | 0.900 | 1.00 | `e5-small__seccion-meta__k1.jsonl.eval.json` |
| bge-m3 | sección | no | 1 | — | — | **0.900** | 0.900 | 0.900 | 0.900 | 1.00 | `bge-m3__seccion__k1.jsonl.eval.json` |
| minilm | sección | sí | 3 | — | 0.05 | **0.892** | 1.000 | 0.842 | 0.975 | 1.35 | `minilm__seccion-meta__k3-m0.05.jsonl.eval.json` |
| bge-m3 | sección | no | 3 | — | 0.02 | **0.883** | 0.900 | 0.875 | 0.900 | 1.10 | `bge-m3__seccion__k3-m0.02.jsonl.eval.json` |
| e5-small | sección | sí | 3 | — | 0.02 | **0.867** | 1.000 | 0.817 | 0.942 | 1.50 | `e5-small__seccion-meta__k3-m0.02.jsonl.eval.json` |
| e5-base | sección | sí | 3 | — | 0.02 | **0.867** | 1.000 | 0.817 | 0.975 | 1.50 | `e5-base__seccion-meta__k3-m0.02.jsonl.eval.json` |
| e5-base | ventana 80/20 | no | 1 | — | — | **0.850** | 0.850 | 0.850 | 0.850 | 1.00 | `e5-base__ventana80-20__k1.jsonl.eval.json` |
| e5-base | sección | no | 1 | — | — | **0.850** | 0.850 | 0.850 | 0.850 | 1.00 | `e5-base__seccion__k1.jsonl.eval.json` |
| bge-m3 | ventana 80/20 | no | 3 | — | 0.02 | **0.842** | 0.900 | 0.817 | 0.900 | 1.25 | `bge-m3__ventana80-20__k3-m0.02.jsonl.eval.json` |
| e5-base | ventana 80/20 | no | 3 | — | 0.02 | **0.833** | 1.000 | 0.767 | 0.925 | 1.75 | `e5-base__ventana80-20__k3-m0.02.jsonl.eval.json` |
| bge-m3 | sección | no | 3 | — | 0.05 | **0.825** | 0.900 | 0.792 | 0.900 | 1.35 | `bge-m3__seccion__k3-m0.05.jsonl.eval.json` |
| bge-m3 | ventana 80/20 | no | 3 | — | 0.05 | **0.825** | 0.950 | 0.775 | 0.925 | 1.55 | `bge-m3__ventana80-20__k3-m0.05.jsonl.eval.json` |
| e5-small | ventana 80/20 | no | 1 | — | — | **0.800** | 0.800 | 0.800 | 0.800 | 1.00 | `e5-small__ventana80-20__k1.jsonl.eval.json` |
| e5-small | sección | no | 1 | — | — | **0.800** | 0.800 | 0.800 | 0.800 | 1.00 | `e5-small__seccion__k1.jsonl.eval.json` |
| e5-base | sección | no | 3 | — | 0.02 | **0.775** | 0.900 | 0.733 | 0.875 | 1.60 | `e5-base__seccion__k3-m0.02.jsonl.eval.json` |
| e5-small | sección | no | 3 | — | 0.02 | **0.758** | 0.900 | 0.700 | 0.842 | 1.60 | `e5-small__seccion__k3-m0.02.jsonl.eval.json` |
| bge-m3 | ventana 40/10 | no | 3 | — | 0.02 | **0.733** | 0.750 | 0.725 | 0.725 | 1.15 | `bge-m3__ventana40-10__k3-m0.02.jsonl.eval.json` |
| minilm | ventana 80/20 | no | 3 | — | 0.05 | **0.725** | 0.800 | 0.692 | 0.750 | 1.55 | `minilm__ventana80-20__k3-m0.05.jsonl.eval.json` |
| e5-small | ventana 80/20 | no | 3 | — | 0.02 | **0.725** | 0.900 | 0.658 | 0.850 | 1.95 | `e5-small__ventana80-20__k3-m0.02.jsonl.eval.json` |
| minilm | ventana 80/20 | no | 3 | — | 0.02 | **0.717** | 0.750 | 0.700 | 0.725 | 1.20 | `minilm__ventana80-20__k3-m0.02.jsonl.eval.json` |
| minilm | sección | no | 3 | — | 0.02 | **0.708** | 0.750 | 0.692 | 0.725 | 1.15 | `minilm__seccion__k3-m0.02.jsonl.eval.json` |
| minilm | ventana 80/20 | no | 1 | — | — | **0.700** | 0.700 | 0.700 | 0.700 | 1.00 | `minilm__ventana80-20__k1.jsonl.eval.json` |
| bge-m3 | ventana 40/10 | no | 1 | — | — | **0.700** | 0.700 | 0.700 | 0.700 | 1.00 | `bge-m3__ventana40-10__k1.jsonl.eval.json` |
| minilm | sección | no | 1 | — | — | **0.700** | 0.700 | 0.700 | 0.700 | 1.00 | `minilm__seccion__k1.jsonl.eval.json` |
| e5-base | sección | sí | 3 | — | 0.05 | **0.692** | 1.000 | 0.583 | 0.975 | 2.20 | `e5-base__seccion-meta__k3-m0.05.jsonl.eval.json` |
| e5-small | sección | sí | 3 | — | 0.05 | **0.692** | 1.000 | 0.583 | 0.942 | 2.20 | `e5-small__seccion-meta__k3-m0.05.jsonl.eval.json` |
| e5-base | ventana 40/10 | no | 3 | — | 0.02 | **0.682** | 0.900 | 0.592 | 0.742 | 1.95 | `e5-base__ventana40-10__k3-m0.02.jsonl.eval.json` |
| e5-base | ventana 80/20 | no | 3 | — | 0.05 | **0.660** | 1.000 | 0.533 | 0.925 | 2.65 | `e5-base__ventana80-20__k3-m0.05.jsonl.eval.json` |
| minilm | sección | no | 3 | — | 0.05 | **0.658** | 0.750 | 0.617 | 0.725 | 1.40 | `minilm__seccion__k3-m0.05.jsonl.eval.json` |
| bge-m3 | ventana 40/10 | no | 3 | — | 0.05 | **0.657** | 0.800 | 0.600 | 0.750 | 1.90 | `bge-m3__ventana40-10__k3-m0.05.jsonl.eval.json` |
| minilm | ventana 40/10 | no | 3 | — | 0.02 | **0.600** | 0.600 | 0.600 | 0.600 | 1.15 | `minilm__ventana40-10__k3-m0.02.jsonl.eval.json` |
| e5-base | ventana 40/10 | no | 1 | — | — | **0.600** | 0.600 | 0.600 | 0.600 | 1.00 | `e5-base__ventana40-10__k1.jsonl.eval.json` |
| e5-small | ventana 40/10 | no | 1 | — | — | **0.600** | 0.600 | 0.600 | 0.600 | 1.00 | `e5-small__ventana40-10__k1.jsonl.eval.json` |
| minilm | ventana 40/10 | no | 1 | — | — | **0.600** | 0.600 | 0.600 | 0.600 | 1.00 | `minilm__ventana40-10__k1.jsonl.eval.json` |
| e5-small | ventana 40/10 | no | 3 | — | 0.02 | **0.582** | 0.750 | 0.500 | 0.675 | 2.05 | `e5-small__ventana40-10__k3-m0.02.jsonl.eval.json` |
| bge-m3 | ventana 80/20 | no | 3 | — | — | **0.575** | 1.000 | 0.417 | 0.950 | 3.00 | `bge-m3__ventana80-20__k3.jsonl.eval.json` |
| e5-base | ventana 80/20 | no | 3 | — | — | **0.575** | 1.000 | 0.417 | 0.925 | 3.00 | `e5-base__ventana80-20__k3.jsonl.eval.json` |
| e5-small | ventana 80/20 | no | 3 | — | 0.05 | **0.560** | 0.900 | 0.433 | 0.850 | 2.80 | `e5-small__ventana80-20__k3-m0.05.jsonl.eval.json` |
| e5-base | sección | no | 3 | — | 0.05 | **0.558** | 0.900 | 0.442 | 0.875 | 2.55 | `e5-base__seccion__k3-m0.05.jsonl.eval.json` |
| minilm | ventana 40/10 | no | 3 | — | 0.05 | **0.533** | 0.600 | 0.500 | 0.600 | 1.75 | `minilm__ventana40-10__k3-m0.05.jsonl.eval.json` |
| e5-small | sección | no | 3 | — | 0.05 | **0.525** | 0.900 | 0.400 | 0.842 | 2.70 | `e5-small__seccion__k3-m0.05.jsonl.eval.json` |
| e5-small | ventana 80/20 | no | 3 | — | — | **0.510** | 0.900 | 0.367 | 0.850 | 3.00 | `e5-small__ventana80-20__k3.jsonl.eval.json` |
| minilm | sección | sí | 3 | — | — | **0.500** | 1.000 | 0.333 | 0.975 | 3.00 | `minilm__seccion-meta__k3.jsonl.eval.json` |
| e5-small | sección | sí | 3 | — | — | **0.500** | 1.000 | 0.333 | 0.942 | 3.00 | `e5-small__seccion-meta__k3.jsonl.eval.json` |
| e5-base | sección | sí | 3 | — | — | **0.500** | 1.000 | 0.333 | 0.975 | 3.00 | `e5-base__seccion-meta__k3.jsonl.eval.json` |
| bge-m3 | sección | sí | 3 | — | — | **0.500** | 1.000 | 0.333 | 1.000 | 3.00 | `bge-m3__seccion-meta__k3.jsonl.eval.json` |
| e5-base | ventana 40/10 | no | 3 | — | 0.05 | **0.490** | 0.900 | 0.350 | 0.742 | 2.90 | `e5-base__ventana40-10__k3-m0.05.jsonl.eval.json` |
| e5-base | ventana 40/10 | no | 3 | — | — | **0.465** | 0.900 | 0.317 | 0.742 | 3.00 | `e5-base__ventana40-10__k3.jsonl.eval.json` |
| e5-small | ventana 40/10 | no | 3 | — | 0.05 | **0.463** | 0.750 | 0.358 | 0.675 | 2.75 | `e5-small__ventana40-10__k3-m0.05.jsonl.eval.json` |
| minilm | ventana 80/20 | no | 3 | — | — | **0.460** | 0.800 | 0.333 | 0.750 | 3.00 | `minilm__ventana80-20__k3.jsonl.eval.json` |
| bge-m3 | ventana 40/10 | no | 3 | — | — | **0.455** | 0.850 | 0.317 | 0.775 | 3.00 | `bge-m3__ventana40-10__k3.jsonl.eval.json` |
| bge-m3 | sección | no | 3 | — | — | **0.450** | 0.900 | 0.300 | 0.900 | 3.00 | `bge-m3__seccion__k3.jsonl.eval.json` |
| minilm | sección | no | 3 | — | — | **0.450** | 0.900 | 0.300 | 0.792 | 3.00 | `minilm__seccion__k3.jsonl.eval.json` |
| e5-base | sección | no | 3 | — | — | **0.450** | 0.900 | 0.300 | 0.875 | 3.00 | `e5-base__seccion__k3.jsonl.eval.json` |
| e5-small | sección | no | 3 | — | — | **0.450** | 0.900 | 0.300 | 0.842 | 3.00 | `e5-small__seccion__k3.jsonl.eval.json` |
| e5-small | ventana 40/10 | no | 3 | — | — | **0.405** | 0.750 | 0.283 | 0.675 | 3.00 | `e5-small__ventana40-10__k3.jsonl.eval.json` |
| e5-base | ventana 80/20 | no | 5 | — | — | **0.393** | 1.000 | 0.250 | 0.925 | 5.00 | `e5-base__ventana80-20__k5.jsonl.eval.json` |
| e5-small | ventana 80/20 | no | 5 | — | — | **0.393** | 1.000 | 0.250 | 0.873 | 5.00 | `e5-small__ventana80-20__k5.jsonl.eval.json` |
| bge-m3 | ventana 80/20 | no | 5 | — | — | **0.393** | 1.000 | 0.250 | 0.950 | 5.00 | `bge-m3__ventana80-20__k5.jsonl.eval.json` |
| bert-base | sección | sí | 3 | — | 0.02 | **0.375** | 0.450 | 0.350 | 0.358 | 2.25 | `bert-base__seccion-meta__k3-m0.02.jsonl.eval.json` |
| minilm | ventana 80/20 | no | 5 | — | — | **0.359** | 0.900 | 0.230 | 0.775 | 5.00 | `minilm__ventana80-20__k5.jsonl.eval.json` |
| minilm | ventana 40/10 | no | 3 | — | — | **0.355** | 0.650 | 0.250 | 0.625 | 3.00 | `minilm__ventana40-10__k3.jsonl.eval.json` |
| e5-base | ventana 40/10 | no | 5 | — | — | **0.352** | 0.950 | 0.220 | 0.752 | 5.00 | `e5-base__ventana40-10__k5.jsonl.eval.json` |
| bge-m3 | ventana 40/10 | no | 5 | — | — | **0.341** | 0.950 | 0.210 | 0.797 | 5.00 | `bge-m3__ventana40-10__k5.jsonl.eval.json` |
| e5-small | ventana 40/10 | no | 5 | — | — | **0.336** | 0.900 | 0.210 | 0.710 | 5.00 | `e5-small__ventana40-10__k5.jsonl.eval.json` |
| bge-m3 | sección | no | 5 | — | — | **0.333** | 1.000 | 0.200 | 0.925 | 5.00 | `bge-m3__seccion__k5.jsonl.eval.json` |
| bge-m3 | sección | sí | 5 | — | — | **0.333** | 1.000 | 0.200 | 1.000 | 5.00 | `bge-m3__seccion-meta__k5.jsonl.eval.json` |
| e5-small | sección | sí | 5 | — | — | **0.333** | 1.000 | 0.200 | 0.942 | 5.00 | `e5-small__seccion-meta__k5.jsonl.eval.json` |
| minilm | sección | sí | 5 | — | — | **0.333** | 1.000 | 0.200 | 0.975 | 5.00 | `minilm__seccion-meta__k5.jsonl.eval.json` |
| e5-base | sección | sí | 5 | — | — | **0.333** | 1.000 | 0.200 | 0.975 | 5.00 | `e5-base__seccion-meta__k5.jsonl.eval.json` |
| minilm | sección | no | 5 | — | — | **0.317** | 0.950 | 0.190 | 0.802 | 5.00 | `minilm__seccion__k5.jsonl.eval.json` |
| e5-base | sección | no | 5 | — | — | **0.317** | 0.950 | 0.190 | 0.887 | 5.00 | `e5-base__seccion__k5.jsonl.eval.json` |
| e5-small | sección | no | 5 | — | — | **0.300** | 0.900 | 0.180 | 0.842 | 5.00 | `e5-small__seccion__k5.jsonl.eval.json` |
| bert-base | sección | sí | 1 | — | — | **0.300** | 0.300 | 0.300 | 0.300 | 1.00 | `bert-base__seccion-meta__k1.jsonl.eval.json` |
| bert-base | sección | no | 1 | — | — | **0.250** | 0.250 | 0.250 | 0.250 | 1.00 | `bert-base__seccion__k1.jsonl.eval.json` |
| bert-base | sección | sí | 3 | — | 0.05 | **0.250** | 0.450 | 0.183 | 0.358 | 2.90 | `bert-base__seccion-meta__k3-m0.05.jsonl.eval.json` |
| bert-base | sección | no | 3 | — | 0.02 | **0.242** | 0.350 | 0.200 | 0.292 | 2.35 | `bert-base__seccion__k3-m0.02.jsonl.eval.json` |
| minilm | ventana 40/10 | no | 5 | — | — | **0.240** | 0.650 | 0.150 | 0.625 | 5.00 | `minilm__ventana40-10__k5.jsonl.eval.json` |
| bert-base | sección | sí | 3 | — | — | **0.225** | 0.450 | 0.150 | 0.358 | 3.00 | `bert-base__seccion-meta__k3.jsonl.eval.json` |
| bert-base | ventana 80/20 | no | 1 | — | — | **0.200** | 0.200 | 0.200 | 0.200 | 1.00 | `bert-base__ventana80-20__k1.jsonl.eval.json` |
| bert-base | sección | no | 3 | — | 0.05 | **0.200** | 0.350 | 0.150 | 0.292 | 2.90 | `bert-base__seccion__k3-m0.05.jsonl.eval.json` |
| bert-base | ventana 80/20 | no | 5 | — | — | **0.191** | 0.500 | 0.120 | 0.302 | 5.00 | `bert-base__ventana80-20__k5.jsonl.eval.json` |
| bert-base | ventana 80/20 | no | 3 | — | — | **0.190** | 0.350 | 0.133 | 0.267 | 3.00 | `bert-base__ventana80-20__k3.jsonl.eval.json` |
| bert-base | sección | sí | 5 | — | — | **0.183** | 0.550 | 0.110 | 0.383 | 5.00 | `bert-base__seccion-meta__k5.jsonl.eval.json` |
| bert-base | ventana 80/20 | no | 3 | — | 0.02 | **0.183** | 0.300 | 0.142 | 0.242 | 2.40 | `bert-base__ventana80-20__k3-m0.02.jsonl.eval.json` |
| bert-base | sección | no | 3 | — | — | **0.175** | 0.350 | 0.117 | 0.292 | 3.00 | `bert-base__seccion__k3.jsonl.eval.json` |
| bert-base | ventana 80/20 | no | 3 | — | 0.05 | **0.165** | 0.300 | 0.117 | 0.242 | 2.85 | `bert-base__ventana80-20__k3-m0.05.jsonl.eval.json` |
| bert-base | ventana 40/10 | no | 3 | — | 0.05 | **0.158** | 0.300 | 0.108 | 0.225 | 2.95 | `bert-base__ventana40-10__k3-m0.05.jsonl.eval.json` |
| bert-base | ventana 40/10 | no | 3 | — | 0.02 | **0.158** | 0.250 | 0.125 | 0.200 | 2.35 | `bert-base__ventana40-10__k3-m0.02.jsonl.eval.json` |
| bert-base | ventana 40/10 | no | 1 | — | — | **0.150** | 0.150 | 0.150 | 0.150 | 1.00 | `bert-base__ventana40-10__k1.jsonl.eval.json` |
| bert-base | sección | no | 5 | — | — | **0.150** | 0.450 | 0.090 | 0.314 | 5.00 | `bert-base__seccion__k5.jsonl.eval.json` |
| bert-base | ventana 40/10 | no | 3 | — | — | **0.150** | 0.300 | 0.100 | 0.225 | 3.00 | `bert-base__ventana40-10__k3.jsonl.eval.json` |
| bert-base | ventana 40/10 | no | 5 | — | — | **0.133** | 0.400 | 0.080 | 0.250 | 5.00 | `bert-base__ventana40-10__k5.jsonl.eval.json` |

## Parte 2: agente con dos fuentes

### Qué se construyó

`agente.py` es un agente de tool calling hecho con LangChain sobre
`deepseek/deepseek-v4-flash-0731` (OpenRouter, temperatura 0). El contrato está en
[`SPEC_AGENTE.md`](SPEC_AGENTE.md). Las piezas:

- **`herramientas.py`**: las seis herramientas como funciones comunes de Python.
  Es el único lugar donde se consulta la API o el recuperador. La descripción que
  lee el modelo es el docstring de cada función.
- **`bucle_agente.py`**: el modelo (`ChatOpenAI`), el prompt de sistema, el bucle
  (el modelo pide herramientas, se ejecutan, ve los resultados y responde), la
  salida con el formato del enunciado y el log de la corrida.
- **`agente.py`**: envuelve cada función como tool de LangChain
  (`StructuredTool.from_function`) y corre el bucle.

Cada corrida escribe un log `.md` en `logs/` con cada pregunta, las herramientas
llamadas con sus argumentos y resultados, la respuesta y el usage de cada llamada
al modelo, tomado del objeto que devuelve OpenRouter.

### Corridas

Todas sobre las 12 preguntas de `datos/preguntas_agente_dev.jsonl`. Lo único que
cambia entre corridas es la herramienta `buscar_documentos`: cuántos fragmentos
devuelve (`k`) y cómo está escrita su descripción.

| Corrida | Qué cambia | Context relevance | Faithfulness | Answer relevance | Ruteo | Costo agente (USD) | Costo juez (USD) |
|---|---|---|---|---|---|---|---|
| 01 | k=1. La descripción traía un ejemplo de consulta igual a la pregunta A12 | 5,000 | 5,000 | 5,000 | 1,00 | 0,003665 | 0,01764 |
| 02 | k=1, con un ejemplo que no está en `dev` | 4,917 | 5,000 | 5,000 | 1,00 | 0,003705 | 0,01784 |
| 03 | k=2 | 4,667 | 5,000 | 5,000 | 1,00 | 0,003720 | 0,01757 |
| 04 | k=3 | sin evaluar | sin evaluar | sin evaluar | 1,00 (a mano) | 0,003769 | — |
| **05 (entregada)** | k=1 y la descripción pide buscar con las palabras del paciente | **pendiente** | **pendiente** | **pendiente** | 1,00 (a mano) | 0,003664 | — |

Archivos de cada corrida: `experimentos/agente/<corrida>.jsonl`, su `.eval.json`
cuando existe, y `logs/agente-<corrida>.md`. `respuestas.jsonl` es una copia de la
corrida 05.

**Las corridas 04 y 05 no tienen evaluación del juez.** El 1/10/2026 la cuenta de
OpenRouter del curso se quedó sin crédito (USD 45,00 cargados, USD 44,996
consumidos) y el modelo juez empezó a devolver `HTTP 402: Payment Required`. El
límite de nuestra key no se alcanzó (quedan USD 0,88 de USD 1). La evaluación de
la corrida 04 se cortó en la quinta pregunta; las cuatro que llegó a puntuar
dieron *context relevance* 4, 4, 4 y 3. El ruteo de 04 y 05 se calculó a mano con
la fórmula del evaluador, porque el script no lo informa sin llamar al juez.

Cuando la cátedra recargue la cuenta, la evaluación pendiente es:

```bash
python3 evaluar/evaluar.py agente --preguntas datos/preguntas_agente_dev.jsonl --respuestas respuestas.jsonl
```

### Qué muestran los números

**1. El ruteo fue 1,00 en todas las corridas.** El agente llamó siempre a las
herramientas esperadas, incluidas las tres preguntas que necesitan dos fuentes
(A10, A11 y A12). Ninguna llamada a la API falló por un nombre mal escrito: el
modelo pasó `terapia intensiva`, `enalapril 10 mg` e `insulina NPH` bien al primer
intento.

**2. Más fragmentos bajan *context relevance* y no mejoran las otras dos.** Con
k=2, el juez bajó a 4 las preguntas A01, A03, A04 y A12 por "un fragmento
adicional irrelevante". *Faithfulness* y *answer relevance* quedaron en 5 con
cualquier k. Es el mismo resultado que la parte 1: en este corpus cada respuesta
está en una sola sección.

**3. El juez no distingue bien entre corridas.** Casi todo da 5, así que las
diferencias entre configuraciones salen de una o dos preguntas. Las conclusiones
de abajo se apoyan en leer los logs, no solo en el promedio.

### Preguntas donde el agente falló

**A10 — "Quiero internar a mi nene en pediatría, ¿hay lugar y me puedo quedar con
él?"** Es la falla más importante, y el juez no la penalizó. En las corridas 01 y
02 el modelo reformuló la segunda parte como *"¿Puede un acompañante quedarse con
un paciente internado en pediatría?"*. Con esa consulta el recuperador devuelve la
sección "Ingreso a internación programada — Acompañante" (coseno 0,667) antes que
"Régimen de visitas — Pediatría" (0,614). El agente respondió con la norma general
("un acompañante durante la noche") en vez de la de pediatría ("madre, padre o
tutor pueden permanecer las 24 horas"), que es la de la referencia. El juez puso
*answer relevance* 5 igual.

La causa no es el recuperador, sino la consulta. La parte 1 se midió con preguntas
escritas como las escribe un paciente; con *"¿Me puedo quedar con mi hijo internado
en pediatría?"* el mismo recuperador trae primero la sección correcta. Por eso la
corrida 05 agrega a la descripción de `buscar_documentos` que la consulta se
escriba con las palabras del paciente. En esa corrida el modelo buscó *"¿Puedo
quedarme con mi hijo internado en pediatría?"*, recibió la sección de pediatría y
respondió las 24 horas. Con k=2 y k=3 la respuesta también fue correcta, pero a
costa de *context relevance* en las otras preguntas.

**A09 — "¿Cuánto se está esperando hoy en la guardia si me clasifican como
verde?"** La referencia agrega que 135 minutos supera el máximo de 2 horas del
triage, aunque la única herramienta esperada es `consultar_espera`. El agente no
es estable en esta pregunta: en las corridas 02 y 04 además buscó la norma en los
documentos y respondió la comparación; en las 01, 03 y 05 respondió solo los 135
minutos. El juez puso 5 en los dos casos. Con temperatura 0 el modelo igual varía
entre corridas.

**Ejemplo filtrado en la corrida 01.** La primera descripción de
`buscar_documentos` tenía como ejemplo *"¿Qué hay que presentar para retirar
medicamentos en la farmacia?"*, y el modelo usó esa frase textual para responder
A12. Era ajustar a `dev` sin querer. Se cambió por un ejemplo de telemedicina, que
no aparece en ninguna pregunta `dev`. Los 5,000 de la corrida 01 no se toman como
resultado.

### Configuración entregada

La de la corrida 05: `buscar_documentos` devuelve un fragmento (la configuración
de la parte 1, sin cambios) y la descripción pide buscar con las palabras del
paciente. Se eligió porque es la única con k=1 que responde bien A10, y k=1 es lo
que mejor puntúa en *context relevance*. El riesgo es el mismo que en la parte 1:
si una pregunta de test necesita dos secciones del mismo tema, un solo fragmento
no alcanza y el agente tiene que hacer dos búsquedas.

## Parte 3: las mismas herramientas como servidor MCP

### Qué se construyó

- **`servidor_mcp.py`**: publica las seis funciones de `herramientas.py` con
  FastMCP (SDK `mcp` 1.30), por stdio. No usa LangChain. La descripción de cada
  herramienta es el mismo docstring que usa la parte 2.
- **`agente_mcp.py`**: levanta el servidor, descubre las herramientas con
  `tools/list` (`load_mcp_tools` de `langchain-mcp-adapters`) y corre el mismo
  bucle de `bucle_agente.py`. No importa `herramientas.py` ni `recuperador.py`: un
  test lo verifica (`tests/test_servidor_mcp.py`).

**MCP Inspector.** El servidor se conectó al Inspector (v1.0.2) y se llamó a cada
una de las seis herramientas. Las capturas están en `experimentos/inspector/`: la
lista de herramientas (`00-tools-list.png`) y una por herramienta con su resultado
(`01` a `06`). Se sacaron automatizando Chrome sobre el Inspector.

### Comparación con la parte 2

Misma configuración que la corrida 05. Archivos: `respuestas_mcp.jsonl` y
`logs/agente_mcp-01.md`.

| | Parte 2 (corrida 05) | Parte 3 (MCP) |
|---|---|---|
| Context relevance | pendiente | pendiente |
| Faithfulness | pendiente | pendiente |
| Answer relevance | pendiente | pendiente |
| Ruteo (a mano) | 1,00 | 1,00 |
| Llamadas al modelo | 24 | 24 |
| Tokens de entrada | 39.183 | 39.375 |
| Tokens de salida | 2.532 | 2.531 |
| Costo del agente (USD) | 0,003664 | 0,003665 |

Las tres métricas del juez están pendientes por la misma falta de crédito. El
comando es:

```bash
python3 evaluar/evaluar.py agente --preguntas datos/preguntas_agente_dev.jsonl --respuestas respuestas_mcp.jsonl
```

**Qué se puede afirmar desde los logs, sin el juez:**

- **El modelo ve exactamente las mismas herramientas.** La primera llamada de cada
  pregunta tiene los mismos tokens de entrada en los dos agentes (1.548 en A01).
  MCP no agrega ni quita nada a la definición de las herramientas.
- **En 11 de las 12 preguntas, las herramientas llamadas y los contextos recibidos
  son idénticos**, carácter por carácter.
- **La única diferencia es A09.** El agente MCP además buscó la norma del triage en
  los documentos; el de la parte 2 no. Es la misma inestabilidad que aparece entre
  corridas de la parte 2, no un efecto de MCP. Explica los 192 tokens de entrada
  de más.
- **El costo es el mismo**, porque MCP solo cambia cómo viajan las llamadas a las
  herramientas, no lo que se le manda al modelo.

Por eso se espera que las métricas del juez sean iguales o casi iguales a las de
la parte 2, con A09 como única fuente de diferencia.

## Costo de la misión en OpenRouter

No tenemos acceso al dashboard de actividad: la cuenta es del curso y nosotros
solo tenemos una key con límite de USD 1. Como en la misión de prompting, el
número auditable es el consumo de la key (`GET /api/v1/key`), leído antes y
después del trabajo.

| | USD |
|---|---|
| Consumo de la key antes de las partes 2 y 3 | 0,032443 |
| Consumo de la key después | 0,116161 |
| **Gasto de las partes 2 y 3** | **0,083718** |

| Desglose | USD | De dónde sale |
|---|---|---|
| Agente: 5 corridas de la parte 2 | 0,018523 | suma del usage de cada log |
| Agente: 1 corrida de la parte 3 | 0,003665 | usage del log |
| Juez: 3 evaluaciones completas | 0,053050 | `costo_juez_usd` de cada `.eval.json` |
| Resto | 0,008480 | evaluación de la corrida 04 cortada en la quinta pregunta, llamadas de prueba al modelo e intentos del juez |
| **Total** | **0,083718** | diferencia de la key |

La parte 1 no usa OpenRouter: el encoder corre en la computadora. El juez es el
63 % del gasto; una corrida completa del agente cuesta USD 0,0037 y evaluarla
cuesta USD 0,018.

El consumo antes y después que figura en cada log no sirve para auditar una
corrida sola: OpenRouter actualiza ese número con demora, y la diferencia de un
log a veces incluye el juez de la corrida anterior. El desglose de arriba usa el
usage de cada respuesta, y solo el total sale de la key.

Faltan sumar las dos evaluaciones pendientes, unos USD 0,036.
