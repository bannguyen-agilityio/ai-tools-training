const db = require('./db');

function searchProducts(q) {
  return db.query("SELECT * FROM products WHERE name LIKE '%" + q + "%'");
}

module.exports = { searchProducts };
