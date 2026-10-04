# CLAUDE.md — Misión "RAG, MCP y Transformers" (Hospital Arroyo Claro)

Instrucciones para el agente que trabaja en **esta carpeta** (`rag-mcp-transformers/`).
Las reglas comunes al repo están en el [`CLAUDE.md` de la raíz](../CLAUDE.md).
El enunciado de la cátedra está en [`mission.md`](mission.md); el contrato de la
parte 1 (recuperador), en [`SPEC.md`](SPEC.md), y el de las partes 2 y 3 (agente y
servidor MCP), en [`SPEC_AGENTE.md`](SPEC_AGENTE.md). Entrega: viernes 9/10/2026.

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

5. **Las seis herramientas viven solo en `herramientas.py`.** `agente.py` y
   `servidor_mcp.py` las envuelven; `agente_mcp.py` no puede importarlas (hay un
   test que lo verifica). La descripción que lee el modelo es el docstring.
6. **Cada corrida del agente deja su log `.md` en `logs/`.** Sin log, la parte 2
   vale cero. Los logs de corridas descartadas también se commitean.

## Entorno

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest
pytest                      # 45 tests, sin red: encoder y modelo falsos
python3 api/servidor.py &   # la API tiene que estar corriendo para los agentes
```

La key de OpenRouter va en `.env` (ver `.env.example`). Los agentes la cargan
solos; `evaluar/evaluar.py` no, así que antes hay que hacer
`set -a; source .env; set +a`.

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

- El juez casi siempre pone 5: no alcanza para comparar configuraciones del
  agente. Hay que leer los logs. En A10 puso 5 a una respuesta que no coincidía con
  la referencia.
- El modelo reformula la consulta en términos técnicos y el recuperador trae otra
  sección. Pedirle en la descripción que busque con las palabras del paciente lo
  arregló con k=1; subir k también, pero baja *context relevance*.
- Con temperatura 0 el agente igual varía entre corridas (A09: a veces busca la
  norma del triage, a veces no).
- La cuenta de OpenRouter es del curso y se queda sin crédito: el juez pide saldo
  para 65.536 tokens de salida y devuelve 402 aunque a nuestra key le quede límite.
- `GET /api/v1/key` se actualiza con demora: sirve para el total de la sesión, no
  para el costo de una corrida sola.
- El MCP Inspector se puede manejar con `playwright-core` y el Chrome instalado
  (`DANGEROUSLY_OMIT_AUTH=true MCP_AUTO_OPEN_ENABLED=false`), sin sacar capturas a mano.

## Estado del proyecto

- **Parte 1** (RAG vectorial): HECHA. `config_rag.json` = bge-m3, sección con
  metadatos, k=1 → context_relevance 1,000 en dev (BERT de base: 0,375). Informe de la parte 1
  escrito en `INFORME.md` (sección "Parte 1").
- **Parte 2** (agente): HECHA. Entregada la corrida 05 (`respuestas.jsonl`): 5/5/5 y
  ruteo 1,00. Las cinco corridas tienen log y evaluación.
- **Parte 3** (MCP): HECHA. `respuestas_mcp.jsonl`: 5/5/5 y ruteo 1,00. Capturas del
  Inspector en `experimentos/inspector/`.
- **Costo de las partes 2 y 3:** USD 0,123 de la key (lectura del 4/10). Las
  evaluaciones pendientes se corrieron el 4/10, cuando la cátedra recargó la cuenta.
- **Partes 4 y 5**: a cargo de otros integrantes del grupo. Sin empezar.
