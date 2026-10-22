import type { RequestHandler } from 'express';
import { rateLimit } from 'express-rate-limit';
import { env } from '../config/env';
import { RateLimitError } from '../core/errors';

/**
 * Per-IP limiter for login attempts. A new instance (and store) is created per call so the
 * limit is scoped to the app it was mounted on. Hits are routed through the central error
 * handler for the standard envelope; the library sets `Retry-After` / `RateLimit-*` headers.
 */
export function createLoginRateLimiter(): RequestHandler {
  return rateLimit({
    windowMs: env.LOGIN_RATE_LIMIT_WINDOW_MS,
    limit: env.LOGIN_RATE_LIMIT_MAX,
    standardHeaders: 'draft-7',
    legacyHeaders: false,
    handler: (_req, _res, next) => next(new RateLimitError('Too many login attempts, please try again later')),
  });
}
