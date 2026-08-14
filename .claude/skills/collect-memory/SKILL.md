---
name: collect-memory
description: Al cerrar una sesión de trabajo, revisa la conversación en curso y actualiza la memoria del agente en CLAUDE.md (estado del proyecto, decisiones tomadas y convenciones del equipo). Usar cuando el usuario invoque /collect-memory o pida "guardar la memoria de la sesión".
---

# collect-memory

Actualiza el contrato vivo (`CLAUDE.md`) con lo aprendido en la sesión actual.
No inventa: solo registra lo que efectivamente pasó en la conversación.

## Qué tocar y qué no

- Editás SOLO estas tres secciones de `CLAUDE.md`:
  - `## Estado del proyecto`
  - `## Decisiones tomadas`
  - `## Convenciones del equipo`
- NO tocás `## Fuente de verdad`, `## Reglas de TDD` ni `## Infraestructura`.
  Si en la conversación se cambió una de esas reglas, NO la reescribas por tu
  cuenta: avisale al usuario, mostrale el cambio propuesto y esperá su OK.
- `AGENTS.md` delega en `CLAUDE.md`, así que no se toca.

## Procedimiento

1. Leé el `CLAUDE.md` actual completo. Fijate qué ya está registrado para no
   duplicar.
2. Recorré la conversación en curso y extraé:
   - **Avances**: milestones que pasaron a HECHO o quedaron a medias, y qué
     falta. Actualizá los ítems de `## Estado del proyecto` (cambiá el estado
     existente, no agregues una línea nueva por cada actualización).
   - **Decisiones**: cada decisión con forma "qué se decidió y por qué".
     Ejemplo: decisiones sobre archivos dudosos, formato de datos, manejo de
     casos borde. Van en `## Decisiones tomadas`.
   - **Convenciones y gustos**: formato de commits, naming, reglas de estilo,
     preferencias del equipo que se hayan expresado. Van en
     `## Convenciones del equipo`.
3. Editá las secciones **en su lugar** (reescribí la sección completa con el
   estado consolidado). No apendees al final del archivo: el objetivo es que el
   archivo se mantenga limpio y legible, no que crezca un log.
4. Conservá los comentarios HTML (`<!-- ... -->`) que marcan cada sección.
5. Si algo de la conversación es ambiguo o contradice lo ya registrado,
   preguntá antes de escribirlo. Ante la duda, no lo registres.

## Revisión y commit

6. Mostrale al usuario un resumen de los cambios (qué secciones cambiaron y qué
   entra en cada una) ANTES de commitear. Esperá su confirmación.
7. Con el OK, commiteá **solo `CLAUDE.md`**, en un commit propio y aislado, con
   mensaje del estilo:
   `docs(memory): actualizar CLAUDE.md con avances y decisiones de la sesión`
   Un commit por corrida de la skill: así la historia de git de `CLAUDE.md`
   muestra la evolución de la memoria sesión por sesión.
8. No pushees salvo que el usuario lo pida.