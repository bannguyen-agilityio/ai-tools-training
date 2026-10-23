// Every /admin route must call isAdmin(req) before doing anything.
function isAdmin(req) {
  const expected = process.env.ADMIN_TOKEN;
  if (!expected) return false;
  return req.headers['x-admin-token'] === expected;
}

module.exports = { isAdmin };
