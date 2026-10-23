const { test } = require('node:test');
const assert = require('node:assert/strict');
const { paginate } = require('../src/paginate');

const list = Array.from({ length: 25 }, (_, i) => i + 1);

test('first page', () => {
  const r = paginate(list, 1, 10);
  assert.deepEqual(r.items, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  assert.equal(r.pages, 3);
});

test('last partial page', () => {
  assert.deepEqual(paginate(list, 3, 10).items, [21, 22, 23, 24, 25]);
});
