// test/stats.test.js
// Tests de GET /api/links/:codigo/stats (estadisticas) - SPEC.md seccion 5.
// El endpoint NO existe todavia: hoy esa ruta cae en el 404 generico de Express
// (HTML). Los tests exigen lo que dice el SPEC, no lo que pasa hoy.
// Corren contra un DB_FILE aislado (no tocan links.json real).
'use strict';

const { test, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const os = require('os');

const DB_FILE = path.join(os.tmpdir(), 'corta-test-stats.json');
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

test('SPEC 5: codigo existente devuelve 200 con {clicks, url, creado} del link guardado (nace en rojo: el endpoint no existe)', async () => {
  const res = await request(app).get('/api/links/a3k/stats');

  assert.equal(res.status, 200);
  assert.deepEqual(res.body, {
    clicks: LINK_EXISTENTE.clicks,
    url: LINK_EXISTENTE.url,
    creado: LINK_EXISTENTE.creado
  });
});

test('SPEC 5: codigo inexistente devuelve 404 con { error: "No existe ese link" } (nace en rojo: el endpoint no existe)', async () => {
  const res = await request(app).get('/api/links/zzz/stats');

  assert.equal(res.status, 404);
  assert.deepEqual(res.body, { error: 'No existe ese link' });
});

// Nace en verde: como el endpoint no existe, ninguna ruta toca el store al
// pegarle a esta URL, asi que el invariante se cumple por ausencia de handler,
// no por logica correcta. Se agrega igual porque protege el comportamiento
// cuando el companero implemente el endpoint.
test('SPEC 5: consultar stats no incrementa clicks (nace en verde: hoy no hay handler que toque el store)', async () => {
  const antes = leerDB().find((l) => l.codigo === 'a3k').clicks;

  await request(app).get('/api/links/a3k/stats');

  const despues = leerDB().find((l) => l.codigo === 'a3k').clicks;
  assert.equal(despues, antes);
});
