const { test } = require('node:test');
const assert = require('node:assert/strict');
const { saveOrder } = require('../src/orders');

test('saveOrder computes total', async () => {
  const o = await saveOrder({ items: [{ priceCents: 800, qty: 2 }] });
  assert.equal(o.totalCents, 1600);
});

test('saveOrder rejects empty orders', async () => {
  await assert.rejects(saveOrder({ items: [] }), /at least one item/);
});
