import { PrismaClient } from '@prisma/client';
import { env } from './env';

/**
 * A single PrismaClient instance per process. Creating one per request would
 * exhaust the connection pool; this module caches it on `globalThis` so that
 * tsx watch-mode reloads and Jest module resets do not spawn extra pools.
 */
const globalForPrisma = globalThis as unknown as { prisma?: PrismaClient };

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: env.NODE_ENV === 'development' ? ['warn', 'error'] : ['error'],
  });

if (env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

/**
 * SQLite is a single-writer database. Enabling WAL lets readers work while a
 * write transaction is open, and the busy timeout makes concurrent writers wait
 * for the lock instead of failing immediately with SQLITE_BUSY.
 */
export async function configureSqlite(): Promise<void> {
  // PRAGMA statements may return a row, so they must go through $queryRawUnsafe.
  await prisma.$queryRawUnsafe('PRAGMA journal_mode = WAL;');
  await prisma.$queryRawUnsafe('PRAGMA busy_timeout = 5000;');
  await prisma.$queryRawUnsafe('PRAGMA foreign_keys = ON;');
}
