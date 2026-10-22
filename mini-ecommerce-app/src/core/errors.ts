/**
 * Application error taxonomy.
 *
 * Services throw these; the centralized error handler turns them into HTTP
 * responses. Nothing below the middleware layer is allowed to build an HTTP
 * response itself, which keeps business rules independent of the transport.
 */

export const ERROR_CODES = {
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  CONFLICT: 'CONFLICT',
  SKU_TAKEN: 'SKU_TAKEN',
  EMAIL_TAKEN: 'EMAIL_TAKEN',
  INSUFFICIENT_STOCK: 'INSUFFICIENT_STOCK',
  EMPTY_CART: 'EMPTY_CART',
  INVALID_STATE: 'INVALID_STATE',
  RATE_LIMITED: 'RATE_LIMITED',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
} as const;

export type ErrorCode = (typeof ERROR_CODES)[keyof typeof ERROR_CODES];

export interface FieldIssue {
  path: string;
  message: string;
}

export class AppError extends Error {
  readonly code: ErrorCode;
  readonly status: number;
  readonly details?: unknown;

  constructor(code: ErrorCode, status: number, message: string, details?: unknown) {
    super(message);
    this.name = new.target.name;
    this.code = code;
    this.status = status;
    this.details = details;
    Error.captureStackTrace?.(this, new.target);
  }
}

export class ValidationError extends AppError {
  constructor(message = 'Request validation failed', details?: unknown) {
    super(ERROR_CODES.VALIDATION_ERROR, 400, message, details);
  }
}

export class UnauthorizedError extends AppError {
  constructor(message = 'Authentication required', details?: unknown) {
    super(ERROR_CODES.UNAUTHORIZED, 401, message, details);
  }
}

export class ForbiddenError extends AppError {
  constructor(message = 'You do not have permission to perform this action', details?: unknown) {
    super(ERROR_CODES.FORBIDDEN, 403, message, details);
  }
}

export class NotFoundError extends AppError {
  constructor(message = 'Resource not found', details?: unknown) {
    super(ERROR_CODES.NOT_FOUND, 404, message, details);
  }
}

export class ConflictError extends AppError {
  constructor(message = 'Resource conflict', details?: unknown) {
    super(ERROR_CODES.CONFLICT, 409, message, details);
  }
}

export class InvalidStateError extends AppError {
  constructor(message = 'Operation is not allowed in the current state', details?: unknown) {
    super(ERROR_CODES.INVALID_STATE, 409, message, details);
  }
}

export class InsufficientStockError extends AppError {
  constructor(message = 'Not enough stock available', details?: unknown) {
    super(ERROR_CODES.INSUFFICIENT_STOCK, 409, message, details);
  }
}

export class EmptyCartError extends AppError {
  constructor(message = 'Cart is empty') {
    super(ERROR_CODES.EMPTY_CART, 400, message);
  }
}

export class RateLimitError extends AppError {
  constructor(message = 'Too many requests, please try again later', details?: unknown) {
    super(ERROR_CODES.RATE_LIMITED, 429, message, details);
  }
}

export class EmailTakenError extends AppError {
  constructor(message = 'An account with this email already exists') {
    super(ERROR_CODES.EMAIL_TAKEN, 409, message);
  }
}
