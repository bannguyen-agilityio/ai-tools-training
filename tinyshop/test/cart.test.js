const { test } = require('node:test');
const assert = require('node:assert/strict');
const { lineTotal, subtotal } = require('../src/cart');

test('lineTotal multiplies price by quantity', () => {
  assert.equal(lineTotal({ priceCents: 1250, qty: 3 }), 3750);
});

test('subtotal sums all lines', () => {
  assert.equal(subtotal([{ priceCents: 800, qty: 2 }, { priceCents: 1500, qty: 1 }]), 3100);
});

test('subtotal of empty cart is 0', () => {
  assert.equal(subtotal([]), 0);
});
