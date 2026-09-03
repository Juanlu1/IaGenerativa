'use strict';

const fs = require('fs');
const path = require('path');

class LocalPersistence {
  constructor(file = process.env.DB_FILE || path.join(__dirname, 'links.json')) {
    this.file = file;
  }
  read() {
    try {
      if (!fs.existsSync(this.file)) return [];
      const raw = fs.readFileSync(this.file, 'utf8');
      return raw ? JSON.parse(raw) : [];
    } catch (_) { return []; }
  }
  write(links) {
    const dir = path.dirname(this.file);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(this.file, JSON.stringify(links, null, 2));
  }
  async findByCode(codigo) { return this.read().find((link) => link.codigo === codigo) || null; }
  async findByUrl(url) { return this.read().find((link) => link.url === url) || null; }
  async insert(link) {
    const links = this.read();
    if (links.some((item) => item.codigo === link.codigo)) {
      const error = new Error('codigo duplicado'); error.constraint = 'links_codigo_key'; throw error;
    }
    if (links.some((item) => item.url === link.url)) {
      const error = new Error('url duplicada'); error.constraint = 'links_url_key'; throw error;
    }
    links.push({ ...link }); this.write(links); return { ...link };
  }
  async incrementClicks(codigo) {
    const links = this.read();
    const link = links.find((item) => item.codigo === codigo);
    if (!link) return null;
    link.clicks = (link.clicks || 0) + 1; this.write(links); return { ...link };
  }
}

class PostgresPersistence {
  constructor(connectionString = process.env.DATABASE_URL) {
    const { Pool } = require('pg');
    this.pool = new Pool({ connectionString, ssl: connectionString.includes('sslmode=require') ? { rejectUnauthorized: false } : undefined });
    this.ready = this.pool.query(`CREATE TABLE IF NOT EXISTS links (codigo TEXT PRIMARY KEY, url TEXT NOT NULL UNIQUE, clicks INTEGER NOT NULL DEFAULT 0, creado TIMESTAMPTZ NOT NULL)`);
  }
  async findByCode(codigo) { await this.ready; const result = await this.pool.query('SELECT codigo, url, clicks, creado FROM links WHERE codigo = $1', [codigo]); return result.rows[0] || null; }
  async findByUrl(url) { await this.ready; const result = await this.pool.query('SELECT codigo, url, clicks, creado FROM links WHERE url = $1', [url]); return result.rows[0] || null; }
  async insert(link) {
    await this.ready;
    const result = await this.pool.query('INSERT INTO links (codigo, url, clicks, creado) VALUES ($1, $2, $3, $4) RETURNING codigo, url, clicks, creado', [link.codigo, link.url, link.clicks, link.creado]);
    return result.rows[0];
  }
  async incrementClicks(codigo) {
    await this.ready;
    const result = await this.pool.query('UPDATE links SET clicks = clicks + 1 WHERE codigo = $1 RETURNING codigo, url, clicks, creado', [codigo]);
    return result.rows[0] || null;
  }
}

function isUniqueViolation(error) { return error && (error.code === '23505' || error.constraint === 'links_codigo_key' || error.constraint === 'links_pkey' || error.constraint === 'links_url_key'); }

function createStorage({ persistence } = {}) {
  const backend = persistence || (process.env.DATABASE_URL ? new PostgresPersistence() : new LocalPersistence());
  return {
    async createLink({ url, generarCodigo }) {
      const existing = await backend.findByUrl(url);
      if (existing) return existing;
      for (let intento = 0; intento <= 1000; intento += 1) {
        const link = { codigo: generarCodigo(), url, clicks: 0, creado: new Date().toISOString() };
        try { return await backend.insert(link); }
        catch (error) {
          if (!isUniqueViolation(error)) throw error;
          const duplicateUrl = await backend.findByUrl(url);
          if (duplicateUrl) return duplicateUrl;
          if (intento === 1000) throw new Error('No se pudo generar un codigo unico');
        }
      }
    },
    getByCode(codigo) { return backend.findByCode(codigo); },
    async getStats(codigo) { const link = await backend.findByCode(codigo); return link ? { clicks: link.clicks || 0, url: link.url, creado: link.creado } : null; },
    incrementClicks(codigo) { return backend.incrementClicks(codigo); }
  };
}

module.exports = { createStorage, LocalPersistence, PostgresPersistence };
