import { buildPaginationMeta } from '../../src/core/response';

describe('buildPaginationMeta', () => {
  it('computes the totals for a full page', () => {
    expect(buildPaginationMeta(1, 20, 45)).toEqual({
      page: 1,
      limit: 20,
      total: 45,
      totalPages: 3,
      hasNext: true,
      hasPrev: false,
    });
  });

  it('flags the last page as having no next page', () => {
    expect(buildPaginationMeta(3, 20, 45)).toMatchObject({ hasNext: false, hasPrev: true });
  });

  it('handles an empty result set', () => {
    expect(buildPaginationMeta(1, 20, 0)).toEqual({
      page: 1,
      limit: 20,
      total: 0,
      totalPages: 0,
      hasNext: false,
      hasPrev: false,
    });
  });
});
