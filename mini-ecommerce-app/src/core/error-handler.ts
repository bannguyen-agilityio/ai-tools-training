import type { ErrorRequestHandler, RequestHandler } from 'express';
import { Prisma } from '@prisma/client';
import { ZodError } from 'zod';
import { AppError, ERROR_CODES, type ErrorCode, type FieldIssue } from './errors';
import { logger } from './logger';

interface ErrorBody {
  success: false;
  error: {
    code: ErrorCode;
    message: string;
    details?: unknown;
  };
  requestId?: string;
}

function toFieldIssues(error: ZodError): FieldIssue[] {
  return error.issues.map((issue) => ({
    path: issue.path.join('.') || '(root)',
    message: issue.message,
  }));
}

/**
 * Centralized error handler. Every error in the application ends here, is
 * translated into the standard error envelope, and is logged with the request
 * id so a client-reported requestId can be traced through the logs.
 */
export const errorHandler: ErrorRequestHandler = (err, req, res, _next) => {
  const requestId = req.requestId;

  if (err instanceof AppError) {
    logger.warn({ err, requestId, code: err.code, status: err.status }, 'Request failed');
    const body: ErrorBody = {
      success: false,
      error: { code: err.code, message: err.message, ...(err.details ? { details: err.details } : {}) },
      ...(requestId ? { requestId } : {}),
    };
    res.status(err.status).json(body);
    return;
  }

  if (err instanceof ZodError) {
    logger.warn({ err, requestId }, 'Request validation failed');
    const body: ErrorBody = {
      success: false,
      error: {
        code: ERROR_CODES.VALIDATION_ERROR,
        message: 'Request validation failed',
        details: toFieldIssues(err),
      },
      ...(requestId ? { requestId } : {}),
    };
    res.status(400).json(body);
    return;
  }

  if (err instanceof Prisma.PrismaClientKnownRequestError) {
    logger.error({ err, requestId, code: err.code }, 'Database error');
    const body: ErrorBody = {
      success: false,
      error: { code: ERROR_CODES.CONFLICT, message: 'The request conflicts with the current state of the data' },
      ...(requestId ? { requestId } : {}),
    };
    if (err.code === 'P2025') {
      res.status(404).json({ ...body, error: { code: ERROR_CODES.NOT_FOUND, message: 'Resource not found' } });
      return;
    }
    res.status(409).json(body);
    return;
  }

  if (err instanceof SyntaxError && 'body' in err) {
    const body: ErrorBody = {
      success: false,
      error: { code: ERROR_CODES.VALIDATION_ERROR, message: 'Request body is not valid JSON' },
      ...(requestId ? { requestId } : {}),
    };
    res.status(400).json(body);
    return;
  }

  logger.error({ err, requestId }, 'Unhandled error');
  const body: ErrorBody = {
    success: false,
    error: { code: ERROR_CODES.INTERNAL_ERROR, message: 'An unexpected error occurred' },
    ...(requestId ? { requestId } : {}),
  };
  res.status(500).json(body);
};

/** Terminal handler for routes that did not match anything. */
export const notFoundHandler: RequestHandler = (req, res) => {
  const body: ErrorBody = {
    success: false,
    error: { code: ERROR_CODES.NOT_FOUND, message: `Route ${req.method} ${req.originalUrl} not found` },
    ...(req.requestId ? { requestId: req.requestId } : {}),
  };
  res.status(404).json(body);
};
