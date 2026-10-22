import { execSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { TEST_DATABASE_URL } from '../helpers/constants';

const projectRoot = path.resolve(__dirname, '..', '..');
const prismaDir = path.join(projectRoot, 'prisma');

/**
 * Recreates the integration database from the checked-in migrations on every
 * test run. Using `migrate deploy` (instead of `db push`) means the suite also
 * proves the migrations themselves are valid.
 */
export default function globalSetup(): void {
  for (const suffix of ['', '-journal', '-wal', '-shm']) {
    fs.rmSync(path.join(prismaDir, `test.db${suffix}`), { force: true });
  }

  execSync('npx prisma migrate deploy', {
    cwd: projectRoot,
    env: { ...process.env, DATABASE_URL: TEST_DATABASE_URL, NODE_ENV: 'test' },
    stdio: 'inherit',
  });
}
