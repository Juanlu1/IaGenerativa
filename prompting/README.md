# Misión 5 — El prompt mínimo

Chat propio multi-modelo sobre **OpenRouter**, y con él resolver el juego de la
vida de Conway en la mínima cantidad de prompts posible, midiendo tokens y gasto.

El enunciado completo está en [`mission.md`](mission.md). El contrato de lo que
construimos, en [`SPEC.md`](SPEC.md); el diseño de la interfaz, en
[`DESIGN.md`](DESIGN.md).

## Qué hay acá

| Ruta | Qué es | Ejercicio |
|---|---|---|
| `chat/` | La interfaz de chat que sirve los 4 modelos vía OpenRouter | 1 |
| `logs/pruebas/` | Un log `.md` de prueba por modelo (evidencia de que los 4 son usables) | 1 |
| `logs/conway/` | Logs del chat que generó `vida.py`: la conversación ganadora y los intentos quemados | 2 |
| `vida.py` | El script resultante, tal cual salió del chat (prohibido parchearlo a mano) | 2 |
| `test_vida.py` | Tests de la cátedra, **tal cual se entregaron** — no se modifican | 2 |
| `INFORME.md` | La cuenta final: tokens, cache, USD, conclusión | 3 |

## Setup

```bash
cp .env.example .env      # y pegá la key de OpenRouter del grupo
```

La key **nunca** se commitea: `.env` está en el `.gitignore` de la raíz.

## Cómo correr los tests

```bash
python3 test_vida.py vida.py
```

Sin argumento busca `vida.py` al lado. Los 9 casos tienen que dar verde con el
script tal cual salió del chat.

## Estado

- [ ] **Antes de todo**: router, mapa de modelos y parámetros comunes → van al `INFORME.md`
- [ ] **Ej 1**: interfaz con los 4 modelos, usage por respuesta, log `.md` por conversación
- [ ] **Ej 1**: log de prueba de cada uno de los 4 modelos
- [ ] **Ej 2**: `vida.py` en 1 prompt (2 máximo), 9 tests en verde, cache hits desde el 2º intento
- [ ] **Ej 3**: informe con la cuenta final, cerrando contra el dashboard de OpenRouter
