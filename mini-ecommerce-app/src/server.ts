import { createApp } from './app';
import { env } from './config/env';
import { configureSqlite, prisma } from './config/prisma';
import { logger } from './core/logger';

async function bootstrap(): Promise<void> {
  await configureSqlite();

  const app = createApp();
  const server = app.listen(env.PORT, env.HOST, () => {
    logger.info(
      { port: env.PORT, host: env.HOST, env: env.NODE_ENV },
      `Mini e-commerce API listening on http://${env.HOST}:${env.PORT}/api/v1`,
    );
  });

  const shutdown = (signal: string): void => {
    logger.info({ signal }, 'Shutting down');
    server.close(() => {
      void prisma.$disconnect().finally(() => process.exit(0));
    });
    // Do not hang forever if a connection refuses to close.
    setTimeout(() => process.exit(1), 10_000).unref();
  };

  process.on('SIGINT', () => void shutdown('SIGINT'));
  process.on('SIGTERM', () => void shutdown('SIGTERM'));
}

bootstrap().catch((error) => {
  logger.error({ err: error }, 'Failed to start the server');
  process.exit(1);
});
