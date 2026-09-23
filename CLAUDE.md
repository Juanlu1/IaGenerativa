# CLAUDE.md — contrato de equipo

Instrucciones para el agente de código que trabaja en este repositorio.
Este archivo tiene las reglas **comunes a todas las misiones**. Lo específico de
cada una vive en el `CLAUDE.md` de su carpeta, y **manda ese** dentro de ella.

## Estructura del repo

Una carpeta por misión. Antes de tocar código, ubicá en cuál estás y leé su
`CLAUDE.md`:

| Carpeta | Misión | Contrato específico |
|---|---|---|
| `corta/` | Corta — acortador de URLs (clase 2, entregada) | [`corta/CLAUDE.md`](corta/CLAUDE.md) |
| `prompting/` | El prompt mínimo (clase 5, en curso) | [`prompting/CLAUDE.md`](prompting/CLAUDE.md) |
| `rag-mcp-transformers/` | RAG, MCP y Transformers — Hospital Arroyo Claro (entrega 9/10) | [`rag-mcp-transformers/CLAUDE.md`](rag-mcp-transformers/CLAUDE.md) |

En la raíz solo queda tooling de equipo: `scripts/` (tarea programada),
`reportes/`, `.claude/skills/` y los archivos de contrato. Nada de código de
misión en la raíz.

## Reglas comunes

1. **Secretos: nunca en el repo.** Ni en el código, ni en un `.txt`, ni en un
   `.mcp.json` commiteado. Van en variables de entorno o en un `.env`
   gitignoreado, con un `.env.example` sin valores como documentación.
2. **Historia de git limpia.** Un commit por cambio con sentido propio, mensaje
   que explique el *por qué*. Nada de commits "wip" ni volcados masivos.
3. **Cada misión trae su `SPEC.md`** cuando corresponde: el contrato de
   comportamiento arbitra qué es correcto y qué es un bug. Ante conflicto entre
   el código y el `SPEC.md` de esa misión, manda el `SPEC.md`.
4. **Los tests de la cátedra no se tocan.** Si una misión entrega un script de
   testing, se corre tal cual llegó; lo que se ajusta es nuestro código.
5. **Al cerrar sesión**, actualizar el `CLAUDE.md` de la misión con la skill
   `/collect-memory` (`.claude/skills/collect-memory/SKILL.md`).

## Infraestructura

- Railway es la capa de producción de `corta/`. El servicio buildea con *Root
  Directory* = `/corta` (desde la reorganización del repo en carpetas por
  misión). Se opera por el Railway MCP.
- Los tests corren siempre en local, nunca contra producción.
