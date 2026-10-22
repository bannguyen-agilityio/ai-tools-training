/**
 * Test environment configuration.
 *
 * This module must be imported *before* anything from `src/`, because
 * `src/config/env.ts` validates `process.env` at import time. `dotenv` does not
 * overwrite variables that are already set, so the values below win over `.env`.
 */
import { TEST_DATABASE_URL, TEST_JWT_SECRET } from '../helpers/constants';

process.env.NODE_ENV = 'test';
process.env.DATABASE_URL = TEST_DATABASE_URL;
process.env.JWT_SECRET = TEST_JWT_SECRET;
process.env.JWT_EXPIRES_IN = '1h';
process.env.BCRYPT_ROUNDS = '4';
process.env.LOG_LEVEL = 'silent';
process.env.LOGIN_RATE_LIMIT_MAX = '5';
process.env.LOGIN_RATE_LIMIT_WINDOW_MS = '60000';
