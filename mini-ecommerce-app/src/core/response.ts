import type { Response } from 'express';

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface ApiMeta {
  pagination?: PaginationMeta;
  [key: string]: unknown;
}

/** Standard success envelope: `{ success: true, data, meta? }`. */
export function sendSuccess<T>(res: Response, data: T, statusCode = 200, meta?: ApiMeta): Response {
  return res.status(statusCode).json({
    success: true,
    data,
    ...(meta ? { meta } : {}) satisfies Record<string, unknown>,
  });
}

export function sendCreated<T>(res: Response, data: T, meta?: ApiMeta): Response {
  return sendSuccess(res, data, 201, meta);
}

export function sendNoContent(res: Response): Response {
  return res.status(204).send();
}

export function buildPaginationMeta(page: number, limit: number, total: number): PaginationMeta {
  const totalPages = limit > 0 ? Math.ceil(total / limit) : 0;
  return {
    page,
    limit,
    total,
    totalPages,
    hasNext: page < totalPages,
    hasPrev: page > 1,
  };
}
