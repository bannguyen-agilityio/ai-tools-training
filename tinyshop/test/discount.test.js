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

test('SAVE10 takes exactly 10% off', () => {
  assert.equal(applyCoupon([{ priceCents: 1000, qty: 1 }], 'SAVE10', now), 900);
});

test('percent coupon always returns integer cents', () => {
  const items = [{ priceCents: 999, qty: 1 }, { priceCents: 333, qty: 3 }];
  const total = applyCoupon(items, 'SAVE10', now);
  assert.ok(Number.isInteger(total));
  assert.equal(total, 1798); // 1998 - round(199.8)
});

test('percent rounding is applied once per order, not per line', () => {
  const items = [{ priceCents: 5, qty: 1 }, { priceCents: 5, qty: 1 }];
  assert.equal(applyCoupon(items, 'SAVE10', now), 9); // 10 - round(1.0)
});

test('FIVEOFF is deducted once per order, not per line', () => {
  const items = [{ priceCents: 2000, qty: 1 }, { priceCents: 1000, qty: 1 }];
  assert.equal(applyCoupon(items, 'FIVEOFF', now), 2500);
});

test('FIVEOFF never makes the total negative', () => {
  assert.equal(applyCoupon([{ priceCents: 300, qty: 1 }], 'FIVEOFF', now), 0);
});

test('expired coupon returns subtotal', () => {
  const late = new Date('2027-01-01T00:00:00Z');
  assert.equal(applyCoupon([{ priceCents: 1000, qty: 1 }], 'SAVE10', late), 1000);
});
