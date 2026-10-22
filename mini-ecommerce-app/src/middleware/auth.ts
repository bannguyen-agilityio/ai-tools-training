import type { RequestHandler } from 'express';
import type { Role } from '@prisma/client';
import { ForbiddenError, UnauthorizedError } from '../core/errors';
import { verifyAccessToken } from '../modules/auth/token';

/** Requires a valid `Authorization: Bearer <jwt>` header and sets `req.user`. */
export const authenticate: RequestHandler = (req, _res, next) => {
  const [scheme, token] = (req.header('authorization') ?? '').split(' ');
  if (scheme?.toLowerCase() !== 'bearer' || !token) {
    throw new UnauthorizedError('Missing or malformed Authorization header');
  }
  const claims = verifyAccessToken(token);
  req.user = { id: claims.sub, role: claims.role };
  next();
};

/** Must run after `authenticate`. */
export const requireRole =
  (...roles: Role[]): RequestHandler =>
  (req, _res, next) => {
    if (!req.user) throw new UnauthorizedError();
    if (!roles.includes(req.user.role)) throw new ForbiddenError();
    next();
  };
