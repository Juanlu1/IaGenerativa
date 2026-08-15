# SPEC.md - Corta

Contrato de comportamiento de Corta. Define que es correcto y que es un bug.
Ante conflicto entre este documento y el codigo, manda este documento; el codigo
se corrige para ajustarse (ese es el trabajo del Milestone 3).

Alcance: lo que piden los milestones (acortar, redirect, estadisticas, y
produccion en Railway). Nada mas.

---

## 1. Proposito y alcance

Corta es un acortador de URLs interno. Crea un codigo corto para una URL larga,
redirige del codigo a la URL original, y expone estadisticas de uso.

Corta NO hace: auth de usuarios, expiracion de links, ni codigos personalizados.

## 2. Modelo de datos

Un link tiene cuatro campos:
- codigo: string de 3 caracteres de [a-z0-9], unico (ver seccion 3).
- url: la URL de destino, ya validada (ver seccion 3).
- clicks: entero, nace en 0, se incrementa y se persiste en cada redirect (ver seccion 6).
- creado: timestamp ISO 8601 de creacion.

Persistencia: en produccion los datos viven en una base de datos y sobreviven a
un redeploy (ver seccion 7). La app heredada usa un unico archivo links.json; eso
no sobrevive a un deploy en Railway y se reemplaza en el Milestone 5.

## 3. Endpoint: crear link - POST /api/links

- Entrada: body JSON { "url": "<destino>" }.
- Exito: status 200 con { "codigo": "<xxx>", "corta": "/<xxx>" }, donde corta es
  el path (el front compone la URL absoluta).
- Validacion de URL: se acepta solo si parsea como URL absoluta con esquema http o
  https (via new URL()). Se rechaza: vacio o falsy, texto arbitrario, numeros y
  esquemas como javascript:. Rechazo devuelve 400 con { "error": "<motivo>" }.
- Unicidad del codigo: el sistema garantiza que dos links nunca compartan codigo.
- Deduplicacion por URL: si la URL recibida es identica (string exacto) a la de un
  link ya existente, se devuelve el codigo de ese link y no se crea una entrada
  nueva. Si difiere en cualquier caracter (incluida la barra final), es otra URL y
  recibe su propio codigo.

## 4. Endpoint: redirect - GET /:codigo

- Codigo existente: redirige a la url con status 302. Se usa 302 y no 301 porque
  un 301 lo cachea el browser y dejaria de contar clicks.
- Cada redirect a un codigo existente incrementa clicks en 1 y lo persiste (ver
  seccion 6).
- Codigo inexistente: 404 con { "error": "No existe ese link" }. No cuenta como click.
- Comparacion del codigo: sensible a mayusculas/minusculas. Como los codigos
  generados son siempre minusculas, una mayuscula nunca es un codigo valido.

## 5. Endpoint: estadisticas - GET /api/links/:codigo/stats (Milestone 4)

- Codigo existente: 200 con { "clicks": <n>, "url": "<destino>", "creado": "<ISO>" }
  (clicks, URL original y fecha de creacion, como pide el Milestone 4).
- Codigo inexistente: 404 con { "error": "No existe ese link" }.
- No incrementa clicks (consultar no es visitar).
- La pagina public/stats.html consume este endpoint y muestra los datos reales.

## 6. "Las estadisticas dicen la verdad"

Invariante que los tests deben proteger:

- Un click es un redirect servido a un codigo existente (seccion 4).
- clicks se incrementa exactamente una vez por redirect servido, y se persiste en
  el mismo request.
- Requests a codigos inexistentes, a estaticos, o a paths que no matchean el
  redirect no afectan ningun contador.
- Se cuentan todos los GET que resuelven a destino (no se filtran previews ni bots).
- Invariante dura: para cualquier link, el clicks que reporta la seccion 5 es
  igual a la cantidad real de redirects servidos por la seccion 4 desde su creacion.

## 7. Persistencia en produccion (Milestone 5)

- Los links y sus clicks sobreviven a un redeploy. El archivo JSON no cumple esto
  en Railway (filesystem efimero) ni tolera multiples instancias; se migra a una
  base de datos persistente (Postgres provisto por Railway).
- Credenciales de la base: en variables de entorno. Nunca en el codigo, en
  notas.txt, ni en ningun archivo commiteado.

## Estado verificado de produccion

- Produccion usa PostgreSQL persistente provisto por Railway.
- Los links y sus clicks sobreviven a un redeploy; esto se verifico manualmente con un link real antes y despues del redeploy.
- La conexion se configura mediante la variable de entorno DATABASE_URL.
- La URL publica de produccion es https://corta-production-41e3.up.railway.app.
- No se guardan secretos en el codigo ni en ningun archivo commiteado.
## 8. Requisitos de ejecucion (para produccion)

No son comportamiento de usuario, pero son parte del contrato de que la app corre
en Railway. Se corrigen en los Milestones 2 y 5:

- El puerto se lee de process.env.PORT (la app heredada lo tiene hardcodeado en 3000).
- Los estaticos se sirven relativo a __dirname, no al cwd (la app heredada rompe
  si el proceso no arranca en la raiz del repo).
- Si la base o el archivo falta o esta corrupta, la app arranca en un estado
  valido en vez de tirar un 500 generico.

## 9. Casos borde (resumen para la bateria de tests)

| Caso | Seccion | Esperado |
|------|---------|----------|
| Crear con URL valida | 3 | 200 + {codigo, corta}, link persistido |
| Crear con URL invalida o falsy | 3 | 400, no se crea nada |
| Colision de codigo | 3 | Unicidad garantizada, ningun link inalcanzable |
| Misma URL exacta dos veces | 3 | Devuelve el mismo codigo, no duplica |
| URL distinta por un caracter | 3 | Codigo propio, entrada nueva |
| Redirect a codigo existente | 4 | 302 a la url, clicks +1 persistido |
| Redirect a codigo inexistente | 4 | 404, sin tocar contadores |
| Stats de codigo existente | 5 | 200 + {clicks, url, creado} |
| Stats de codigo inexistente | 5 | 404 |
| Verdad de stats | 6 | clicks == redirects reales servidos |
| Persistencia tras redeploy | 7 | Links y clicks intactos |

---

Este SPEC se escribe temprano y se actualiza cuando cambia el entendimiento. Cada
test de la bateria referencia la seccion que lo justifica.