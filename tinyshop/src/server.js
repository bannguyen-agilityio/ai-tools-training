const http = require('node:http');
const db = require('./db');
const { isAdmin } = require('./auth');
const { saveOrder } = require('./orders');

function send(res, status, body) {
  res.writeHead(status, { 'content-type': 'application/json' });
  res.end(JSON.stringify(body));
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    let raw = '';
    req.on('data', (c) => (raw += c));
    req.on('end', () => { try { resolve(JSON.parse(raw || '{}')); } catch (e) { reject(e); } });
  });
}

async function handler(req, res) {
  const url = new URL(req.url, 'http://localhost');

  if (url.pathname === '/health') return send(res, 200, { ok: true });

  if (url.pathname === '/products') return send(res, 200, db.products);

  if (url.pathname === '/products/search') {
    const q = url.searchParams.get('q') || '';
    return send(res, 200, db.query('SELECT * FROM products WHERE name LIKE ?', [q]));
  }

  if (url.pathname === '/orders' && req.method === 'POST') {
    try {
      const order = await saveOrder(await readJson(req));
      return send(res, 201, order);
    } catch (e) {
      return send(res, 400, { error: e.message });
    }
  }

  if (url.pathname === '/admin/orders') {
    if (!isAdmin(req)) return send(res, 403, { error: 'forbidden' });
    return send(res, 200, db.orders);
  }

  send(res, 404, { error: 'not found' });
}

if (require.main === module) {
  const port = process.env.PORT || 3000;
  http.createServer(handler).listen(port, () => console.log(`tinyshop on :${port}`));
}

module.exports = { handler };
