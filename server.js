const express = require('express');
const fs = require('fs');
const path = require('path');
const { generarCodigo } = require('./utils');

const app = express();
app.use(express.json());
// servir estaticos relativo a __dirname para ser robusto fuera del cwd
app.use(express.static(path.join(__dirname, 'public')));

const DB_FILE = process.env.DB_FILE || path.join(__dirname, 'links.json');

function leerLinks() {
  try {
    if (!fs.existsSync(DB_FILE)) return [];
    const raw = fs.readFileSync(DB_FILE, 'utf8');
    if (!raw) return [];
    return JSON.parse(raw);
  } catch (err) {
    // si el archivo esta corrupto o hay un error, devolver array vacio para seguir
    return [];
  }
}

function guardarLinks(links) {
  try {
    const dir = path.dirname(DB_FILE);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(DB_FILE, JSON.stringify(links, null, 2));
  } catch (err) {
    throw err;
  }
}

// crear un link corto
app.post('/api/links', (req, res) => {
  const { url } = req.body;

  // validar presencia y tipo
  if (!url || typeof url !== 'string') {
    return res.status(400).json({ error: 'Falta la url o tipo invalido' });
  }

  // validar parseo y esquema http/https
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return res.status(400).json({ error: 'Esquema no soportado' });
    }
  } catch (e) {
    return res.status(400).json({ error: 'URL invalida' });
  }

  const links = leerLinks();

  // deduplicacion por URL exacta
  const existente = links.find((l) => l.url === url);
  if (existente) {
    return res.json({ codigo: existente.codigo, corta: '/' + existente.codigo });
  }

  // generar codigo unico: reintentar mientras exista colision
  let codigo;
  let intento = 0;
  do {
    if (intento++ > 1000) {
      return res.status(500).json({ error: 'No se pudo generar un codigo unico' });
    }
    codigo = generarCodigo();
  } while (links.some((l) => l.codigo === codigo));

  const nuevo = {
    codigo: codigo,
    url: url,
    clicks: 0,
    creado: new Date().toISOString()
  };
  links.push(nuevo);
  guardarLinks(links);
  res.json({ codigo: codigo, corta: '/' + codigo });
});

// redirigir al destino
app.get('/:codigo', (req, res) => {
  const links = leerLinks();
  const link = links.find(function (l) { return l.codigo === req.params.codigo; });
  if (!link) {
    return res.status(404).json({ error: 'No existe ese link' });
  }
  link.clicks = (link.clicks || 0) + 1;
  guardarLinks(links);
  return res.redirect(302, link.url);
});

if (require.main === module) {
  const PORT = process.env.PORT || 3000;
  app.listen(PORT, function () {
    console.log('Corta escuchando en http://localhost:' + PORT);
  });
}

module.exports = app;
