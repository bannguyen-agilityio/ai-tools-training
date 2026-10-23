const { lineTotal, subtotal } = require('./cart');

const COUPONS = {
  SAVE10: { type: 'percent', value: 15, expires: '2026-12-31' },
  FIVEOFF: { type: 'fixed', valueCents: 500, expires: '2026-12-31' },
};

// Returns the order total in cents after applying a coupon code.
function applyCoupon(items, code, now = new Date()) {
  const coupon = COUPONS[code];
  if (!coupon) return subtotal(items);
  if (new Date(coupon.expires) < now) return subtotal(items);

  let total = 0;
  for (const item of items) {
    let line = lineTotal(item);
    if (coupon.type === 'percent') {
      line = line * (1 - coupon.value / 100);
    } else {
      line = line - coupon.valueCents;
    }
    total += line;
  }
  return total;
}

module.exports = { applyCoupon, COUPONS };
