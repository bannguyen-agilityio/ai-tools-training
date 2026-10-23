// Toy in-memory "database". query() mimics a SQL driver: pass values in
// `params`, never by concatenating them into the SQL string.
const products = [
  { id: 1, name: 'Coffee beans', priceCents: 1250 },
  { id: 2, name: 'Green tea', priceCents: 800 },
  { id: 3, name: 'Ceramic mug', priceCents: 1500 },
  { id: 4, name: 'Pour-over kettle', priceCents: 4200 },
];
const orders = [];
const log = [];

function query(sql, params = []) {
  log.push(sql);
  const term = String(params[0] ?? '').toLowerCase();
  return products.filter((p) => p.name.toLowerCase().includes(term));
}

module.exports = { products, orders, query, log };
