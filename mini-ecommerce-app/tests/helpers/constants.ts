/**
 * Shared test constants. This module must stay free of imports from `src/`
 * so that it can be loaded before the environment is configured.
 */

/** SQLite file used by the integration suite. Relative paths resolve from `prisma/`. */
export const TEST_DATABASE_URL = 'file:./test.db?connection_limit=1';

export const TEST_JWT_SECRET = 'integration-test-secret-at-least-32-chars-long';
