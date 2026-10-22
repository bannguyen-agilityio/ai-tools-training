/**
 * Express type augmentation. `req.requestId` is attached by the
 * request-context middleware and is used by the error handler to correlate
 * logs with the client. The name avoids clashing with `req.id`, which
 * pino-http already claims on `http.IncomingMessage`.
 */
import type { Role } from '@prisma/client';

declare global {
  namespace Express {
    interface Request {
      requestId: string;
      /** Set by the `authenticate` middleware. */
      user?: { id: string; role: Role };
    }
  }
}

export {};
