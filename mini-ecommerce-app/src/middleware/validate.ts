import type { RequestHandler } from 'express';
import type { ZodType } from 'zod';

/** Parses `req.body` with the schema and replaces it with the parsed value. ZodErrors reach the central handler. */
export const validateBody =
  (schema: ZodType): RequestHandler =>
  (req, _res, next) => {
    req.body = schema.parse(req.body ?? {});
    next();
  };
