# CLAUDE.md — Misión "RAG, MCP y Transformers" (Hospital Arroyo Claro)

Instrucciones para el agente que trabaja en **esta carpeta** (`rag-mcp-transformers/`).
Las reglas comunes al repo están en el [`CLAUDE.md` de la raíz](../CLAUDE.md).
El enunciado de la cátedra está en [`mission.md`](mission.md); el contrato de la
parte 1 (recuperador), en [`SPEC.md`](SPEC.md). Entrega: viernes 9/10/2026.

## Reglas propias de esta misión

1. **No se tocan `evaluar/`, `api/`, `datos/` ni `atencion/test_atencion.py`.** La
   cátedra corre sus propias copias.
2. **La interfaz del recuperador es estable.** Las partes 2 y 3 usan
   `Recuperador.desde_config().buscar(consulta, k=None) -> list[str]`. Se puede
   cambiar todo lo de adentro (encoder, chunking, umbrales en `config_rag.json`),
   pero no esa firma.
3. **Cada configuración probada de la parte 1 tiene su `.eval.json` en
   `experimentos/`**, generado con el evaluador oficial. Sin ese archivo, la fila
   no cuenta.
4. **No tunear para las preguntas `dev`.** La cátedra evalúa con otro conjunto.
   Ante empates (< 0,02), gana la configuración más simple.

## Entorno

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest
pytest                      # tests del recuperador, con encoder falso (sin red)
```

Funciona con Python 3.14 (torch 2.14, transformers 5.17, sentence-transformers 6.1).
La primera corrida descarga el modelo del encoder desde Hugging Face.

## Hallazgos

- Cada pregunta `dev` de recuperación tiene **una sola** frase de evidencia, en una
  sola sección de un único documento. Devolver 1 fragmento correcto da 1,0;
  devolver 2 con uno correcto da 0,67. Por eso importa el `margen`.
- El evaluador pide la evidencia **textual** dentro del fragmento: un chunking
  que corte oraciones pierde recall aunque el fragmento sea el correcto.

- Grilla de 100 configuraciones (`experimentos/tabla.md`): BERT sin ajustar no pasa
  de 0,375; anteponer título de documento y sección mejora a todos los encoders;
  las ventanas de palabras rinden peor que el corte por sección.
- `bge-m3` pesa ~2,2 GB: la primera vez que alguien corre el recuperador se
  descarga (tarda unos minutos). Después arranca en ~15 s en CPU.

## Estado del proyecto

- **Parte 1** (RAG vectorial): HECHA. `config_rag.json` = bge-m3, sección con
  metadatos, k=1 → context_relevance 1,000 en dev (BERT de base: 0,375). Falta
  volcar la tabla y la justificación al `INFORME.md`.
- **Partes 2 a 5**: a cargo de otros integrantes del grupo.
