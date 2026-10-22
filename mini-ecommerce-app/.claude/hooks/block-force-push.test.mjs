// Run: node --test .claude/hooks/block-force-push.test.mjs   (only parses command strings; never runs git)
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const script = fileURLToPath(new URL('./block-force-push.mjs', import.meta.url));
const run = (command) => {
  const res = spawnSync('node', [script], {
    input: JSON.stringify({ tool_name: 'Bash', tool_input: { command } }),
    encoding: 'utf8',
  });
  assert.equal(res.status, 0);
  return res.stdout ? JSON.parse(res.stdout).hookSpecificOutput : null;
};

test('blocks forced pushes', () => {
  for (const cmd of [
    'git push --force origin main',
    'git push -f',
    'git push origin +main',
    'git -C app push -fu origin feat',
    'npm test && git push --force',
    'git push --force-with-lease origin feat',
    'git push --force-with-lease=feat:abc123 origin feat',
    'git push --force-if-includes origin feat',
    'git push --forc origin feat',
    'git push --mirror',
    'sudo git push -f',
    'env GIT_SSH=ssh git push --force-with-lease',
    '/usr/bin/git push -f',
    'bash -c "git push -f"',
    "sh -c 'cd app && git push --force'",
    'eval "git push -f"',
    'echo $(git push -f)',
    '(git push -f)',
    'git push -f &',
    'git -C "my dir" push -f',
    'git push origin "+main"',
  ]) {
    const out = run(cmd);
    assert.equal(out?.permissionDecision, 'deny', cmd);
    assert.equal(out.hookEventName, 'PreToolUse');
    assert.match(out.permissionDecisionReason, /force/i);
  }
});

test('allows normal commands', () => {
  for (const cmd of [
    'ls -la',
    'git status',
    'git push',
    'git push -u origin feat/x',
    'git commit -m "x"',
    'git -C "my dir" push origin feat',
  ]) {
    assert.equal(run(cmd), null, cmd);
  }
});

test('allows similar but harmless commands', () => {
  for (const cmd of [
    'git push --follow-tags',
    'git fetch --force',
    'echo "git push --force"',
    'git commit -m "no git push -f here"',
  ]) {
    assert.equal(run(cmd), null, cmd);
  }
});
