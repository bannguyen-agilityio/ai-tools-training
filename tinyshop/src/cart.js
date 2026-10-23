// All amounts are integer cents.
function lineTotal(item) {
  return item.priceCents * item.qty;
}

function subtotal(items) {
  return items.reduce((sum, item) => sum + lineTotal(item), 0);
}

module.exports = { lineTotal, subtotal };
