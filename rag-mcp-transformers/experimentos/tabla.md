# Experimentos de la parte 1

Generada por `experimentar.py` con `evaluar/evaluar.py` sobre `datos/preguntas_recuperacion_dev.jsonl`. 100 configuraciones, ordenadas por context relevance.

| Encoder | Chunking | Metadatos | k | Umbral | Margen | Context relevance | Recall | Precision | MRR | Fragmentos prom. | Evaluación |
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
