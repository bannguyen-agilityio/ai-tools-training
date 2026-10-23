# tinyshop

A deliberately small shop API for practising code review with Claude Code.

    npm test        # run tests (Node's built-in runner, no install needed)
    npm start       # http://localhost:3000

Routes on the base branch: `GET /health`, `GET /products`, `GET /products/search?q=`,
`POST /orders`, `GET /admin/orders` (needs header `x-admin-token`).

Money is always integer cents. Never use floats for money.
