import { randomUUID } from 'node:crypto';
import type { RequestHandler } from 'express';

/**
 * Attaches a correlation id to every request. Clients may supply their own
 * `x-request-id`; otherwise one is generated. The id is echoed in the response
 * headers and included in every error body.
 */
export const requestContext: RequestHandler = (req, res, next) => {
  const incoming = req.header('x-request-id');
  req.requestId = incoming && incoming.length <= 128 ? incoming : randomUUID();
  res.setHeader('x-request-id', req.requestId);
  next();
};
