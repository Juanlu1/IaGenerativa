const express = require('express');
const path = require('path');
const { generarCodigo } = require('./utils');
const { createStorage } = require('./storage');

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
const storage = createStorage();

app.post('/api/links', async (req, res) => {
  const { url } = req.body;
  if (!url || typeof url !== 'string') return res.status(400).json({ error: 'Falta la url o tipo invalido' });
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return res.status(400).json({ error: 'Esquema no soportado' });
  } catch (_) { return res.status(400).json({ error: 'URL invalida' }); }
  try {
    const link = await storage.createLink({ url, generarCodigo });
    return res.json({ codigo: link.codigo, corta: '/' + link.codigo });
  } catch (error) { return res.status(500).json({ error: error.message }); }
});

app.get('/api/links/:codigo/stats', async (req, res) => {
  const stats = await storage.getStats(req.params.codigo);
  if (!stats) return res.status(404).json({ error: 'No existe ese link' });
  return res.json(stats);
});

app.get('/:codigo', async (req, res) => {
  const link = await storage.getByCode(req.params.codigo);
  if (!link) return res.status(404).json({ error: 'No existe ese link' });
  const updated = await storage.incrementClicks(req.params.codigo);
  return res.redirect(302, updated.url);
});

if (require.main === module) {
  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => console.log('Corta escuchando en http://localhost:' + PORT));
}

module.exports = app;
