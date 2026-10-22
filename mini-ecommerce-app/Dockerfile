# syntax=docker/dockerfile:1

# ---- base ----------------------------------------------------------------
FROM node:24-alpine AS base
WORKDIR /app
RUN apk add --no-cache libc6-compat openssl

# ---- dependencies --------------------------------------------------------
FROM base AS deps
COPY package.json package-lock.json ./
# `npm ci` installs exactly what the lockfile pins.
RUN npm ci

# ---- build ---------------------------------------------------------------
FROM deps AS build
COPY prisma ./prisma
COPY src ./src
COPY scripts ./scripts
COPY tsconfig.json tsconfig.build.json ./
RUN npx prisma generate && npm run build

# ---- runtime -------------------------------------------------------------
FROM base AS runtime
ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=3000 \
    DATABASE_URL="file:/app/data/production.db?connection_limit=1"

# The Prisma CLI ships as a devDependency but is required at runtime to apply
# migrations, so the full dependency tree is copied from the build stage.
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY --from=build /app/prisma ./prisma
COPY package.json ./

RUN mkdir -p /app/data && chown -R node:node /app
USER node

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
  CMD node -e "fetch('http://127.0.0.1:3000/api/v1/health/ready').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

# Apply pending migrations, then start the API.
CMD ["sh", "-c", "npx prisma migrate deploy && node dist/server.js"]
