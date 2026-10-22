import { randomUUID } from 'node:crypto';
import express, { type Express } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import pinoHttp from 'pino-http';
import { env } from './config/env';
import { logger } from './core/logger';
import { errorHandler, notFoundHandler } from './core/error-handler';
import { requestContext } from './middleware/request-context';
import { healthRouter } from './modules/health/health.routes';
import { setupDocs } from './docs/swagger';

export function createApp(): Express {
  const app = express();

  app.disable('x-powered-by');
  app.set('trust proxy', 1);

  // Drop `upgrade-insecure-requests` so Swagger UI assets and "Try it out" calls
  // are not rewritten to https when the API is served over plain http.
  app.use(
    helmet({
      contentSecurityPolicy: {
        directives: { 'upgrade-insecure-requests': null },
      },
    }),
  );
  app.use(
    cors({
      origin: env.CORS_ORIGIN === '*' ? true : env.CORS_ORIGIN.split(',').map((origin) => origin.trim()),
      credentials: true,
    }),
  );
  app.use(express.json({ limit: '1mb' }));
  app.use(express.urlencoded({ extended: true, limit: '1mb' }));

  app.use(requestContext);
  app.use(
    pinoHttp({
      logger,
      genReqId: (req) => (req as { requestId?: string }).requestId ?? randomUUID(),
      autoLogging: { ignore: (req) => req.url === '/api/v1/health' },
    }),
  );

  setupDocs(app);
  app.use('/api/v1', healthRouter);

  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}

