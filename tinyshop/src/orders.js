const db = require('./db');
const { applyCoupon } = require('./discount');

async function saveOrder(order) {
  if (!Array.isArray(order.items) || order.items.length === 0) {
    throw new Error('Order must contain at least one item');
  }
  const saved = {
    id: db.orders.length + 1,
    ...order,
    totalCents: applyCoupon(order.items, order.coupon),
  };
  db.orders.push(saved);
  return saved;
}

module.exports = { saveOrder };
