#!/usr/bin/env node
// Claude Code hook: format JS/TS files that Claude edits, using the repo's Prettier + .prettierrc.
//
//   format.mjs pre   (PreToolUse)  records whether the target file is already Prettier-clean
//   format.mjs post  (PostToolUse) formats it, but only if it was clean (or new) before the edit
//
// The pre/post pair keeps unrelated changes safe: a file that was already unformatted is left
// alone, so Prettier never rewrites lines Claude did not touch. Formatting runs as a plain child
// process, not a Claude tool call, so it cannot re-trigger the hook; and Prettier is idempotent
// and skipped when the file is already clean.
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { extname, join, relative, resolve, sep } from 'node:path';

const SUPPORTED = new Set(['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.mts', '.cts']);
const SKIPPED_DIRS = ['node_modules', 'dist', 'coverage', 'data', join('prisma', 'migrations')];

const mode = process.argv[2];
const input = JSON.parse(
  await new Promise((done) => {
    let raw = '';
    process.stdin.on('data', (chunk) => (raw += chunk)).on('end', () => done(raw || '{}'));
  }),
);

const projectDir = resolve(process.env.CLAUDE_PROJECT_DIR ?? input.cwd ?? process.cwd());
const filePath = input.tool_input?.file_path && resolve(projectDir, input.tool_input.file_path);
if (!['pre', 'post'].includes(mode) || !filePath) process.exit(0);

const rel = relative(projectDir, filePath);
const supported =
  !rel.startsWith('..') &&
  SUPPORTED.has(extname(filePath)) &&
  !SKIPPED_DIRS.some((dir) => rel === dir || rel.startsWith(dir + sep) || rel.includes(sep + dir + sep));
if (!supported) process.exit(0);

const prettier = join(projectDir, 'node_modules', '.bin', 'prettier');
if (!existsSync(prettier)) {
  console.error('format hook: prettier not installed (run npm ci); skipping');
  process.exit(0);
}
const runPrettier = (flag) =>
  spawnSync(prettier, [flag, '--ignore-unknown', '--log-level', 'warn', filePath], {
    cwd: projectDir,
    encoding: 'utf8',
  });

const markerDir = join(tmpdir(), `claude-format-hook-${input.session_id ?? 'default'}`);
const marker = join(markerDir, createHash('sha1').update(filePath).digest('hex'));

if (mode === 'pre') {
  // Record "safe to format": the file does not exist yet, or it is already Prettier-clean.
  if (!existsSync(filePath) || runPrettier('--check').status === 0) {
    mkdirSync(markerDir, { recursive: true });
    writeFileSync(marker, filePath);
  }
  process.exit(0);
}

const safeToFormat = existsSync(marker);
rmSync(marker, { force: true });
if (!safeToFormat) process.exit(0); // pre-existing unformatted file: leave the user's code alone

if (runPrettier('--check').status === 0) process.exit(0); // already formatted: nothing to write
const result = runPrettier('--write');
if (result.status !== 0) console.error(`format hook: prettier failed on ${rel}\n${result.stderr}`);
process.exit(0);
