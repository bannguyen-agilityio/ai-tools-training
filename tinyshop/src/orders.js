const db = require('./db');
const { subtotal } = require('./cart');

async function saveOrder(order) {
  if (!Array.isArray(order.items) || order.items.length === 0) {
    throw new Error('Order must contain at least one item');
  }
  const saved = { id: db.orders.length + 1, ...order, totalCents: subtotal(order.items) };
  db.orders.push(saved);
  return saved;
}

module.exports = { saveOrder };
