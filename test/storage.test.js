// Tests del contrato de persistencia - SPEC.md seccion 7.
//
// Estos tests no conocen PostgreSQL ni Railway. El backend en memoria simula
// una base persistente compartida entre instancias de LinkStorage. La
// implementacion de produccion debera reemplazar este backend por Postgres sin
// cambiar el contrato que se prueba aqui.
'use strict';

const { test, beforeEach } = require('node:test');
const assert = require('node:assert/strict');

class MemoryPersistence {
  constructor() {
    this.links = new Map();
  }

  async findByCode(codigo) {
    const link = this.links.get(codigo);
    return link ? { ...link } : null;
  }

  async findByUrl(url) {
    for (const link of this.links.values()) {
      if (link.url === url) return { ...link };
    }
    return null;
  }

  async insert(link) {
    if (this.links.has(link.codigo)) {
      const error = new Error('codigo duplicado');
      error.constraint = 'links_codigo_key';
      throw error;
    }
    if ([...this.links.values()].some((existing) => existing.url === link.url)) {
      const error = new Error('url duplicada');
      error.constraint = 'links_url_key';
      throw error;
    }
    this.links.set(link.codigo, { ...link });
    return { ...link };
  }

  async incrementClicks(codigo) {
    const link = this.links.get(codigo);
    if (!link) return null;
    link.clicks += 1;
    return { ...link };
  }
}

let createStorage;
let persistence;

beforeEach(() => {
  // El modulo todavia no existe en la fase roja. Mantener el require aqui
  // permite que cada test aparezca como fallo independiente y explicito.
  ({ createStorage } = require('../storage'));
  persistence = new MemoryPersistence();
});

function linkStorage() {
  return createStorage({ persistence });
}

test('SPEC 7: un link permanece disponible al crear una nueva instancia del almacenamiento', async () => {
  const first = linkStorage();
  const created = await first.createLink({
    url: 'https://example.com/persistente',
    generarCodigo: () => 'abc'
  });

  const second = linkStorage();
  const found = await second.getByCode(created.codigo);

  assert.deepEqual(found, created);
});

test('SPEC 7: los clicks permanecen al crear una nueva instancia del almacenamiento', async () => {
  const first = linkStorage();
  await first.createLink({
    url: 'https://example.com/clicks',
    generarCodigo: () => 'clk'
  });
  await first.incrementClicks('clk');
  await first.incrementClicks('clk');

  const second = linkStorage();
  const found = await second.getByCode('clk');

  assert.equal(found.clicks, 2);
});

test('SPEC 7: stats recupera los valores persistidos', async () => {
  const first = linkStorage();
  const created = await first.createLink({
    url: 'https://example.com/stats',
    generarCodigo: () => 'sts'
  });
  await first.incrementClicks(created.codigo);

  const second = linkStorage();
  const stats = await second.getStats(created.codigo);

  assert.deepEqual(stats, {
    clicks: 1,
    url: created.url,
    creado: created.creado
  });
});

test('SPEC 7: incrementar clicks no pierde incrementos concurrentes', async () => {
  const storage = linkStorage();
  await storage.createLink({
    url: 'https://example.com/concurrencia',
    generarCodigo: () => 'con'
  });

  await Promise.all(Array.from({ length: 50 }, () => storage.incrementClicks('con')));

  const found = await storage.getByCode('con');
  assert.equal(found.clicks, 50);
});

test('SPEC 7 y SPEC 3: la deduplicacion por URL exacta se mantiene', async () => {
  const storage = linkStorage();
  const generarCodigo = (() => {
    const codes = ['dup', 'dif'];
    return () => codes.shift();
  })();

  const first = await storage.createLink({
    url: 'https://example.com/misma',
    generarCodigo
  });
  const duplicate = await storage.createLink({
    url: 'https://example.com/misma',
    generarCodigo
  });
  const different = await storage.createLink({
    url: 'https://example.com/misma/',
    generarCodigo
  });

  assert.equal(duplicate.codigo, first.codigo);
  assert.equal(different.codigo, 'dif');
});

test('SPEC 7 y SPEC 3: codigo sigue siendo unico ante una colision', async () => {
  const storage = linkStorage();
  const codes = ['col', 'col', 'lib'];
  const generarCodigo = () => codes.shift();

  const first = await storage.createLink({
    url: 'https://example.com/uno',
    generarCodigo
  });
  const second = await storage.createLink({
    url: 'https://example.com/dos',
    generarCodigo
  });

  assert.equal(first.codigo, 'col');
  assert.equal(second.codigo, 'lib');
  assert.notEqual(first.codigo, second.codigo);
});
