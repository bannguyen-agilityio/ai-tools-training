const { subtotal } = require('./cart');

const COUPONS = {
  SAVE10: { type: 'percent', value: 10, expires: '2026-12-31' },
  FIVEOFF: { type: 'fixed', valueCents: 500, expires: '2026-12-31' },
};

// Returns the order total in cents after applying a coupon code.
function applyCoupon(items, code, now = new Date()) {
  const coupon = COUPONS[code];
  if (!coupon) return subtotal(items);
  if (new Date(coupon.expires) < now) return subtotal(items);

  const sub = subtotal(items);
  let discount;
  if (coupon.type === 'percent') {
    // Round once on the whole order so the result stays integer cents.
    discount = Math.round((sub * coupon.value) / 100);
  } else {
    // Fixed amount comes off the order once, never below zero.
    discount = Math.min(coupon.valueCents, sub);
  }
  return sub - discount;
}

module.exports = { applyCoupon, COUPONS };
