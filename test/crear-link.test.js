// test/crear-link.test.js
// Tests de POST /api/links (crear link) - SPEC.md seccion 3.
// Corren contra un DB_FILE aislado (no tocan links.json real).
'use strict';

const { test, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const os = require('os');

const DB_FILE = path.join(os.tmpdir(), 'corta-test-crear-link.json');
process.env.DB_FILE = DB_FILE;

// server.js lee process.env.DB_FILE al cargarse, asi que el require va
// despues de setear la variable.
const request = require('supertest');
const app = require('../server');

function leerDB() {
  return JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
}

function escribirDB(links) {
  fs.writeFileSync(DB_FILE, JSON.stringify(links, null, 2));
}

beforeEach(() => {
  escribirDB([]);
});

test('SPEC 3: crear con URL valida (http/https) devuelve 200 con {codigo, corta} y persiste el link (nace en verde)', async () => {
  const res = await request(app)
    .post('/api/links')
    .send({ url: 'https://example.com/pagina' });

  assert.equal(res.status, 200);
  assert.match(res.body.codigo, /^[a-z0-9]{3}$/);
  assert.equal(res.body.corta, '/' + res.body.codigo);

  const links = leerDB();
  assert.equal(links.length, 1);
  assert.equal(links[0].codigo, res.body.codigo);
  assert.equal(links[0].url, 'https://example.com/pagina');
  assert.equal(links[0].clicks, 0);
  assert.ok(links[0].creado);
});

test('SPEC 3: URL vacia se rechaza con 400 y no crea nada (nace en verde)', async () => {
  const res = await request(app)
    .post('/api/links')
    .send({ url: '' });

  assert.equal(res.status, 400);
  assert.equal(leerDB().length, 0);
});

test('SPEC 3: un string que no es URL se rechaza con 400 y no crea nada (nace en rojo)', async () => {
  const res = await request(app)
    .post('/api/links')
    .send({ url: 'esto no es una url' });

  assert.equal(res.status, 400);
  assert.equal(leerDB().length, 0);
});

test('SPEC 3: un numero como url se rechaza con 400 y no crea nada (nace en rojo)', async () => {
  const res = await request(app)
    .post('/api/links')
    .send({ url: 12345 });

  assert.equal(res.status, 400);
  assert.equal(leerDB().length, 0);
});

test('SPEC 3: un esquema no http/https (javascript:) se rechaza con 400 y no crea nada (nace en rojo)', async () => {
  const res = await request(app)
    .post('/api/links')
    .send({ url: 'javascript:alert(1)' });

  assert.equal(res.status, 400);
  assert.equal(leerDB().length, 0);
});

test('SPEC 3: postear la misma url exacta dos veces devuelve el mismo codigo y no duplica (nace en rojo)', async () => {
  const url = 'https://example.com/misma';

  const res1 = await request(app).post('/api/links').send({ url });
  const res2 = await request(app).post('/api/links').send({ url });

  assert.equal(res1.status, 200);
  assert.equal(res2.status, 200);
  assert.equal(res2.body.codigo, res1.body.codigo);
  assert.equal(leerDB().length, 1);
});

test('SPEC 3: URL que difiere en un caracter (barra final) recibe codigo propio, no se deduplica (nace en verde: hoy nunca deduplica, asi que por accidente cumple)', async () => {
  const res1 = await request(app).post('/api/links').send({ url: 'https://example.com/pagina' });
  const res2 = await request(app).post('/api/links').send({ url: 'https://example.com/pagina/' });

  assert.equal(res1.status, 200);
  assert.equal(res2.status, 200);
  assert.notEqual(res2.body.codigo, res1.body.codigo);
  assert.equal(leerDB().length, 2);
});

// Unicidad: ante una colision del generador, el sistema DEBE regenerar y asignar
// un codigo distinto. Forzamos UNA colision y despues dejamos que el generador
// escape a otro valor (no lo congelamos en una constante, para no crear un espacio
// de codigos de tamano 1 que haria imposible resolver la colision).
// Asume que generarCodigo hace 3 llamadas a Math.random sobre charset [a-z0-9]:
// con 0 -> 'aaa', con ~1/36 -> 'bbb'. Confirmado por el resultado del inventario.
test('SPEC 3: unicidad - ante colision del generador, regenera y no comparte codigo (nace en rojo)', async () => {
  const seq = [0, 0, 0, 0, 0, 0]; // link1 -> 'aaa'; 1er intento de link2 -> 'aaa' (colision)
  let i = 0;
  const orig = Math.random;
  Math.random = () => (i < seq.length ? seq[i++] : 1 / 36); // los reintentos escapan a 'bbb'

  try {
    const res1 = await request(app).post('/api/links').send({ url: 'https://example.com/uno' });
    const res2 = await request(app).post('/api/links').send({ url: 'https://example.com/dos' });

    // Sanity check: si esto falla, la asuncion sobre el generador ya no vale.
    assert.equal(res1.body.codigo, 'aaa');
    // Lo que realmente probamos: link2 NO reusa el codigo ocupado.
    assert.notEqual(res2.body.codigo, res1.body.codigo);

    const codigos = leerDB().map((l) => l.codigo);
    assert.equal(new Set(codigos).size, codigos.length); // todos unicos
  } finally {
    Math.random = orig;
  }
});
