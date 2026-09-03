// test/redirect.test.js
// Tests de GET /:codigo (redirect) - SPEC.md seccion 4.
// Corren contra un DB_FILE aislado (no tocan links.json real).
'use strict';

const { test, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const os = require('os');

const DB_FILE = path.join(os.tmpdir(), 'corta-test-redirect.json');
process.env.DB_FILE = DB_FILE;

// server.js lee process.env.DB_FILE al cargarse, asi que el require va
// despues de setear la variable.
const request = require('supertest');
const app = require('../server');

const LINK_EXISTENTE = {
  codigo: 'a3k',
  url: 'https://example.com/destino',
  clicks: 5,
  creado: '2026-01-01T00:00:00.000Z'
};

function leerDB() {
  return JSON.parse(fs.readFileSync(DB_FILE, 'utf8'));
}

function escribirDB(links) {
  fs.writeFileSync(DB_FILE, JSON.stringify(links, null, 2));
}

beforeEach(() => {
  escribirDB([{ ...LINK_EXISTENTE }]);
});

test('SPEC 4: codigo existente redirige con 302 a la url', async () => {
  const res = await request(app).get('/a3k');

  assert.equal(res.status, 302);
  assert.equal(res.headers.location, LINK_EXISTENTE.url);
});

test('SPEC 4 y 6: el redirect a un codigo existente incrementa clicks en 1 y lo persiste', async () => {
  await request(app).get('/a3k');

  const links = leerDB();
  const link = links.find((l) => l.codigo === 'a3k');
  assert.equal(link.clicks, LINK_EXISTENTE.clicks + 1);
});

test('SPEC 4: codigo inexistente devuelve 404 con { error: "No existe ese link" }', async () => {
  const res = await request(app).get('/zzz');

  assert.equal(res.status, 404);
  assert.deepEqual(res.body, { error: 'No existe ese link' });
});

test('SPEC 4 y 6: un GET a codigo inexistente no cuenta como click de ningun link', async () => {
  await request(app).get('/a3k'); // click real: deberia dejar clicks en 6 y persistirlo
  await request(app).get('/zzz'); // codigo inexistente: no deberia sumar

  const links = leerDB();
  const link = links.find((l) => l.codigo === 'a3k');
  assert.equal(link.clicks, LINK_EXISTENTE.clicks + 1);
});

// NOTA: este test ya pasa con el codigo actual sin arreglar (Array.find con
// === ya es case-sensitive). No sigue el ciclo rojo->verde de esta feature;
// se agrega igual como regresion explicita porque lo pide SPEC 4 y asi queda
// protegido para el futuro. Verificado: nace en verde, no en rojo.
test('SPEC 4: la comparacion de codigo es sensible a mayusculas/minusculas (nace en verde, no en rojo)', async () => {
  const res = await request(app).get('/A3K');

  assert.equal(res.status, 404);
});
