# Revisión de la Parte 1: voluntariado y auditoría

Investigación hecha junto con la Parte 4, **sin modificar** `historial_clasificado.csv` ni
`costumbres.md`. Las cifras salen de `historial/historial.csv`, `curado/auditoria.csv` y
`practica/esperadas-*.jsonl`; los ids de cada hallazgo están en su seccion. Lo que propone
cambiar queda para que el equipo lo decida y lo aplique en `curar.py`.

## Resumen

1. **El corte de la costumbre del voluntariado es 75 años, no 76.** `curar.py` usa 76 y por
   eso marca como desvío a los 11 pacientes de 75 años sin acompañante, que tienen todos el
   aviso. Diez de esas filas quedaron `ruido` y probablemente son `correcta`.
2. **No hay otra costumbre detras de los 143 avisos sin explicar.** Con el corte en 75 quedan
   132, y los 132 son de tres operadores: OP-04, OP-11 y OP-17. Los otros 17 operadores siguen
   la costumbre sin una sola excepción. Esos tres operadores deciden el aviso casi al azar:
   es ruido de operador, no una costumbre.
3. **La auditoría de errores es consistente.** Cada fila `error` viola exactamente una norma,
   los errores se reparten parejo entre los 20 operadores y no aparece un patrón compartido
   que sugiera una costumbre mal leida como error.

## 1. El corte de edad del voluntariado es 75

Avisos al voluntariado por edad (filas de 70 a 80 años):

| Edad | Sin acompañante | Sin acompañante, sin OP-04/11/17 | Con acompañante |
|---:|---:|---:|---:|
| 70 | 1 de 21 | 0 de 18 | 0 de 8 |
| 71 | 1 de 19 | 0 de 15 | 1 de 19 |
| 72 | 0 de 10 | 0 de 8 | 1 de 10 |
| 73 | 1 de 18 | 0 de 16 | 1 de 17 |
| 74 | 1 de 15 | 0 de 13 | 1 de 10 |
| 75 | 11 de 11 | 8 de 8 | 0 de 7 |
| 76 | 14 de 14 | 13 de 13 | 2 de 11 |
| 77 | 10 de 11 | 8 de 8 | 1 de 13 |
| 78 | 13 de 18 | 13 de 13 | 0 de 13 |
| 79 | 13 de 13 | 12 de 12 | 1 de 10 |
| 80 | 18 de 19 | 15 de 15 | 0 de 6 |

El salto es entre 74 y 75. Fuera de los tres operadores del punto 2, de 74 para abajo no hay
ningún aviso y de 75 para arriba sin acompañante los hay todos: 185 de 185.

La práctica lo confirma: `pev-006` (75 años, sin acompañante) espera `aviso_al_voluntariado:
true` con las normas original, b y c. La política de las sinteticas fallaba solo en ese caso
con 76 y resuelve 50 de 50 en las tres versiones con 75 (`uv run python validar_politica.py`,
detalle en `datos/validacion_politica.json`). También muestra que el corte no depende de los
parámetros de las normas: es el mismo en las tres versiones.

Filas de 75 años sin acompañante, todas con aviso: `H-0045`, `H-0576`, `H-0943`, `H-1269`, `H-1348`, `H-1592`, `H-1593`, `H-1613`, `H-1677`, `H-1786`, `H-1884`.

- Quedaron `ruido` solo por este desvío (10): `H-0045`, `H-0576`, `H-0943`, `H-1269`, `H-1348`, `H-1592`, `H-1613`, `H-1677`, `H-1786`, `H-1884`. **Propuesta:** pasarlas a
  `correcta`, cambiando el corte a 75 en `curar.py` (funciones `verificar_fila` y
  `generar_costumbres`) y regenerando la clasificación y `costumbres.md`.
- Quedaron `error` (1): `H-1593`, por otra norma (circuito o plazo); siguen siendo error.

Con el corte en 75 la costumbre queda respaldada por 207 de 226 filas, y todas las
excepciones son de OP-04, OP-11 y OP-17.

## 2. Los avisos sin explicar son de tres operadores

Se buscaron otras explicaciones para los avisos fuera de la costumbre: nivel de triage, motivo,
sospecha de sepsis, llegada, tipo de documento, si el paciente puede responder, accidente de
trabajo, cobertura, circuito, registro, box, respuesta de la verificación, edad, acompañante y
mes. Ninguna separa los avisos: en los grupos de 20 filas o más, la tasa de aviso va de 4% a 14%.
El operador sí:

| Operador | Avisos fuera de la costumbre |
|---|---:|
| OP-01 | 0 de 86 |
| OP-02 | 0 de 86 |
| OP-03 | 0 de 86 |
| OP-04 | 33 de 82 |
| OP-05 | 0 de 93 |
| OP-06 | 0 de 95 |
| OP-07 | 0 de 85 |
| OP-08 | 0 de 72 |
| OP-09 | 0 de 100 |
| OP-10 | 0 de 100 |
| OP-11 | 54 de 99 |
| OP-12 | 0 de 103 |
| OP-13 | 0 de 98 |
| OP-14 | 0 de 81 |
| OP-15 | 0 de 80 |
| OP-16 | 0 de 69 |
| OP-17 | 45 de 104 |
| OP-18 | 0 de 78 |
| OP-19 | 0 de 89 |
| OP-20 | 0 de 88 |

Fuera de OP-04, OP-11 y OP-17, hay 0 avisos en 1489 filas fuera de la costumbre.
Dentro de esos tres operadores la tasa de aviso es parecida con o sin acompañante y a
cualquier edad (entre 29% y 64% según la década y el acompañante), y omiten el aviso en casi la mitad de los casos
de la costumbre: deciden el campo sin seguir ninguna regla visible. Los mismos tres operadores
son los únicos que eligieron la obra social cuando el paciente presentó también una prepaga
(las 9 excepciones de la costumbre de la prepaga: `H-0334`, `H-0404`, `H-0408`, `H-0480`,
`H-0792`, `H-0881`, `H-1190`, `H-1467` y `H-1520`). Son "los operadores que hacen las cosas a
su manera" del enunciado.

- **OP-04**: avisa en 33 de 82 filas fuera de la situación de la costumbre y omite el aviso en 5 de 11 filas dentro de ella.
  - Avisos fuera de la costumbre: `H-0005`, `H-0053`, `H-0108`, `H-0265`, `H-0322`, `H-0386`, `H-0443`, `H-0445`, `H-0450`, `H-0537`, `H-0607`, `H-0619`, `H-0630`, `H-0653`, `H-0741`, `H-0808`, `H-0883`, `H-0933`, `H-0936`, `H-0954`, `H-1052`, `H-1234`, `H-1276`, `H-1295`, `H-1313`, `H-1434`, `H-1443`, `H-1554`, `H-1582`, `H-1666`, `H-1722`, `H-1758`, `H-1860`.
  - Avisos omitidos: `H-0353`, `H-0617`, `H-0644`, `H-1088`, `H-1947`.
- **OP-11**: avisa en 54 de 99 filas fuera de la situación de la costumbre y omite el aviso en 6 de 12 filas dentro de ella.
  - Avisos fuera de la costumbre: `H-0067`, `H-0093`, `H-0140`, `H-0142`, `H-0150`, `H-0163`, `H-0188`, `H-0196`, `H-0241`, `H-0245`, `H-0255`, `H-0288`, `H-0306`, `H-0340`, `H-0444`, `H-0463`, `H-0489`, `H-0515`, `H-0562`, `H-0612`, `H-0652`, `H-0756`, `H-0778`, `H-0827`, `H-0856`, `H-0904`, `H-0958`, `H-0966`, `H-0970`, `H-0980`, `H-1020`, `H-1091`, `H-1102`, `H-1126`, `H-1143`, `H-1257`, `H-1391`, `H-1416`, `H-1496`, `H-1564`, `H-1568`, `H-1665`, `H-1669`, `H-1682`, `H-1702`, `H-1709`, `H-1778`, `H-1800`, `H-1821`, `H-1831`, `H-1843`, `H-1856`, `H-1905`, `H-1909`.
  - Avisos omitidos: `H-0127`, `H-0182`, `H-0449`, `H-0907`, `H-1116`, `H-1452`.
- **OP-17**: avisa en 45 de 104 filas fuera de la situación de la costumbre y omite el aviso en 8 de 18 filas dentro de ella.
  - Avisos fuera de la costumbre: `H-0006`, `H-0009`, `H-0056`, `H-0110`, `H-0231`, `H-0357`, `H-0398`, `H-0399`, `H-0416`, `H-0497`, `H-0525`, `H-0542`, `H-0575`, `H-0597`, `H-0610`, `H-0622`, `H-0626`, `H-0627`, `H-0710`, `H-0717`, `H-0748`, `H-0749`, `H-0761`, `H-0770`, `H-0786`, `H-0875`, `H-0898`, `H-0925`, `H-1031`, `H-1040`, `H-1046`, `H-1173`, `H-1258`, `H-1283`, `H-1382`, `H-1427`, `H-1428`, `H-1466`, `H-1644`, `H-1708`, `H-1724`, `H-1752`, `H-1812`, `H-1973`, `H-1976`.
  - Avisos omitidos: `H-0077`, `H-1093`, `H-1549`, `H-1584`, `H-1641`, `H-1742`, `H-1794`, `H-1834`.

**Consecuencias.**

- La clasificación actual ya marca esas filas como `ruido` cuando no hay otro error: de las
  170 filas `ruido`, 163 son de estos tres operadores (las otras 7 son del punto 1). No
  hace falta cambiarlas.
- No conviene agregar una tercera costumbre: el patrón no se repite entre operadores.
- Las filas `correcta` de estos operadores (119) coinciden con la costumbre por azar en el campo
  del aviso. Siguen siendo correctas por definición, pero si se quiere un conjunto de
  entrenamiento más limpio se pueden excluir de las conversaciones reales (`armar_dataset.py`
  no lo hace hoy).

## 3. Revisión de `curado/auditoria.csv`

Motivos de las 240 filas `error` (cada una tiene un solo motivo):

| Motivo | Filas | Ejemplos |
|---|---:|---|
| NOR-TDE-01/02/03/04: circuito o plazo no coincide con triage y llegada | 97 | `H-0010`, `H-0031`, `H-0035`, `H-0059`, `H-0071`, `H-0085`, `H-0109`, `H-0126` |
| NOR-ADM-01/03: tipo de registro incompatible con documento y triage | 64 | `H-0014`, `H-0052`, `H-0098`, `H-0103`, `H-0115`, `H-0128`, `H-0156`, `H-0168` |
| NOR-ADM-01/02: faltó ubicar en el box antes del registro | 61 | `H-0040`, `H-0117`, `H-0212`, `H-0217`, `H-0254`, `H-0316`, `H-0320`, `H-0331` |
| NOR-COB-02/03/04: cobertura de la ficha no corresponde a credencial, consulta y verificación | 12 | `H-0555`, `H-0567`, `H-0581`, `H-0863`, `H-1311`, `H-1360`, `H-1401`, `H-1465` |
| NOR-COB-02/03/04: entidad de notificación incorrecta | 6 | `H-0378`, `H-0522`, `H-0929`, `H-1183`, `H-1290`, `H-1678` |

- Errores por operador: entre 7 y 18, sin un operador que concentre un tipo. Es lo
  esperable de equivocaciones sueltas y no de una costumbre.
- Los tipos son exactamente las reglas que "contradicen lo habitual": el descuento por
  ambulancia (NOR-TDE-04), el registro provisorio con pasaporte o cédula en niveles urgentes
  (NOR-ADM-03), el box para mayores de P-ADM-2 (NOR-ADM-02) y el dígito reservado
  (NOR-COB-04). En todos, el valor registrado es el que daría la regla "habitual".
- Se controlaron campos que `curar.py` no revisa: ninguna fila pone el box antes del registro
  cuando la norma no lo exige (582 filas, todas `no`), ninguna tiene plazo sin circuito y
  ninguna anota un número de documento que el paciente no presentó.
- Con dos credenciales y la prepaga inactiva, los operadores registran `sin_cobertura` sin
  verificar la obra social (45 filas). Es parte de la costumbre de la prepaga y la práctica lo
  confirma (`pev-048` y `pev-050`, resueltos por la política). Conviene decirlo explícitamente
  en `costumbres.md`.

No se encontraron filas `error` que parezcan mal clasificadas. Las dudas de la clasificación
están en el punto 1.

## Cómo reproducir

```bash
uv run python revisar_parte1.py   # todas las cifras de este documento
uv run python validar_politica.py # la política sintética contra las esperadas de práctica
```
