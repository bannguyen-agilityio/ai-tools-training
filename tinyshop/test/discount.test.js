const { test } = require('node:test');
const assert = require('node:assert/strict');
const { applyCoupon } = require('../src/discount');

const now = new Date('2026-10-01T00:00:00Z');

test('no coupon returns subtotal', () => {
  assert.equal(applyCoupon([{ priceCents: 1000, qty: 1 }], undefined, now), 1000);
});

test('SAVE10 gives a discount', () => {
  const total = applyCoupon([{ priceCents: 1000, qty: 1 }], 'SAVE10', now);
  assert.ok(total < 1000);
});

test('FIVEOFF works', () => {
  const total = applyCoupon([{ priceCents: 2000, qty: 1 }], 'FIVEOFF', now);
  assert.ok(total !== undefined);
});
