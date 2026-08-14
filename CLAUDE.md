# CLAUDE.md — Corta
Instrucciones para el agente de código que trabaja en este repositorio.
Este archivo es el **contrato vivo** del proyecto: reglas, estado y decisiones.
Se mantiene con la skill `/collect-memory` al cerrar cada sesión de trabajo.

## Qué es Corta

Acortador de URLs interno, heredado, sin documentación original. Objetivo de la
misión: llevarlo del estado "carpeta copiada de la compu del dev anterior" a
producción, con historia completa en GitHub (del caos del primer commit al
deploy).

## Fuente de verdad

- `SPEC.md` (en la raíz) es el **contrato de comportamiento**. Arbitra qué es
  correcto y qué es un bug. Ante conflicto entre el código actual y `SPEC.md`,
  manda `SPEC.md`.
- Los tests se derivan de `SPEC.md`, **no** del comportamiento observado del
  código heredado. El código heredado tiene bugs conocidos; documentar lo que
  hace hoy sería canonizar esos bugs como si fueran features.
- El `SPEC.md` se escribe temprano (con lo que se va descubriendo) y se
  actualiza cuando cambia el entendimiento.

## Reglas de TDD (obligatorias y verificables)

1. Ningún cambio de comportamiento entra sin un test previo que lo cubra.
2. Orden de commits por cada feature o bug fix: **primero** el/los test en rojo
   (commit separado), **después** la implementación que los pone en verde
   (commit separado). La historia de git debe mostrar el test *antes* que la
   implementación que lo hace pasar.
3. Los tests se escriben **feature por feature**, no en un solo bloque, para
   preservar la secuencia rojo→verde en la historia de git.
4. Cada test referencia la sección de `SPEC.md` que lo justifica.
5. En cada milestone, la suite completa corre **verde** antes de dar el
   milestone por cerrado.
6. El usuario revisa los tests antes de aceptarlos, aunque los haya generado el agente.

## Infraestructura

- Railway es la capa de **producción** (deploy, provisión de base de datos,
  logs). Se opera por el Railway MCP.
- Los tests corren **localmente** contra una base de test, nunca contra Railway.
- **Secretos** (credenciales de DB, tokens): viven en variables de entorno.
  Nunca en el código, nunca en `.mcp.json` commiteado, nunca en un `.txt`.
  En `.mcp.json` se usa expansión de variables de entorno para no commitear el
  PAT ni otros tokens. Nunca se commitean ni se pushean.

## Estado del proyecto

<!-- Sección mantenida por /collect-memory. Actualizar al cerrar cada sesión. -->

- **Milestone 1** (trackear desde el principio): HECHO.
- **Milestones 2–5** (ordenar, corregir bugs, completar stats, producción):
  PENDIENTES.

## Decisiones tomadas

<!-- Sección mantenida por /collect-memory. Formato por entrada: qué se decidió y por qué. -->

- (todavía ninguna registrada)

## Convenciones del equipo

<!-- Sección mantenida por /collect-memory: formato de commits, naming, reglas y gustos del equipo. -->

- (a definir)