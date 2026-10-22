import {
  AppError,
  ConflictError,
  ERROR_CODES,
  ForbiddenError,
  InsufficientStockError,
  InvalidStateError,
  NotFoundError,
  UnauthorizedError,
  ValidationError,
} from '../../src/core/errors';

describe('AppError taxonomy', () => {
  it('maps each error type to its HTTP status and stable error code', () => {
    const cases: Array<[AppError, number, string]> = [
      [new ValidationError(), 400, ERROR_CODES.VALIDATION_ERROR],
      [new UnauthorizedError(), 401, ERROR_CODES.UNAUTHORIZED],
      [new ForbiddenError(), 403, ERROR_CODES.FORBIDDEN],
      [new NotFoundError(), 404, ERROR_CODES.NOT_FOUND],
      [new ConflictError(), 409, ERROR_CODES.CONFLICT],
      [new InvalidStateError(), 409, ERROR_CODES.INVALID_STATE],
      [new InsufficientStockError(), 409, ERROR_CODES.INSUFFICIENT_STOCK],
    ];

    for (const [error, status, code] of cases) {
      expect(error).toBeInstanceOf(AppError);
      expect(error.status).toBe(status);
      expect(error.code).toBe(code);
      expect(error.message).toEqual(expect.any(String));
    }
  });

  it('keeps optional details on the error', () => {
    const error = new ValidationError('bad input', [{ path: 'email', message: 'invalid' }]);

    expect(error.details).toEqual([{ path: 'email', message: 'invalid' }]);
  });

  it('names the concrete error class', () => {
    expect(new NotFoundError().name).toBe('NotFoundError');
    expect(new NotFoundError() instanceof Error).toBe(true);
  });
});
