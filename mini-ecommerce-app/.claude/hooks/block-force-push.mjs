#!/usr/bin/env node
// Claude Code PreToolUse hook (matcher: Bash): deny every kind of forced `git push`.
// Blocked: --force, --force-with-lease, --force-if-includes (and any abbreviation, `=value` form), -f
// (also in clusters like -fu), +refspec, --mirror. Also found behind wrappers (sudo, env, command, time,
// xargs...), `bash -c '...'`, `eval`, $(...), `...`, (...), {...}, full paths to git and `git -C "a dir"`.
// Nothing is ever executed here: the command string is only parsed. Limits: it cannot see through
// variables, aliases, or scripts that run git internally.
import { pathToFileURL } from 'node:url';

const GIT_OPTS_WITH_VALUE = new Set(['-C', '-c', '--git-dir', '--work-tree', '--namespace', '--exec-path']);
const SHELLS = new Set(['bash', 'sh', 'zsh', 'dash', 'ksh']);
const WRAPPERS = new Set([
  'sudo',
  'doas',
  'command',
  'env',
  'exec',
  'time',
  'nohup',
  'nice',
  'builtin',
  'xargs',
  'then',
  'do',
  'else',
  '!',
]);
const FORCE_ARG = [/^--forc/, /^--mi/, /^-[a-zA-Z]*f[a-zA-Z]*$/, /^\+\S/]; // --force*, --mirror, -f, +refspec

const basename = (word) => word.split('/').pop();

/** Split a command line into simple commands (arrays of words), honouring quotes and escapes. */
function parse(command) {
  const commands = [];
  let words = [];
  let word = null;
  let quote = null;
  const endWord = () => {
    if (word !== null) words.push(word);
    word = null;
  };
  const endCommand = () => {
    endWord();
    if (words.length) commands.push(words);
    words = [];
  };
  for (let i = 0; i < command.length; i++) {
    const ch = command[i];
    if (quote) {
      if (ch === quote) quote = null;
      else if (ch === '\\' && quote === '"' && i + 1 < command.length) word += command[++i];
      else word += ch;
    } else if (ch === "'" || ch === '"') {
      quote = ch;
      word ??= '';
    } else if (ch === '\\' && i + 1 < command.length) {
      word = (word ?? '') + command[++i];
    } else if (/\s/.test(ch) && ch !== '\n') {
      endWord();
    } else if (';&|\n(){}`'.includes(ch)) {
      endCommand();
    } else {
      word = (word ?? '') + ch;
    }
  }
  endCommand();
  return commands;
}

/** True if one simple command is a forcing `git push`. */
function isForcePush(words) {
  // Substitutions hidden inside quotes: "...$(git push -f)..."
  if (words.some((w) => /\$\(|`/.test(w) && isForbidden(w.replace(/\$\(|`/g, ';')))) return true;
  let i = 0;
  while (i < words.length && /^[A-Za-z_][A-Za-z0-9_]*=/.test(words[i])) i++; // leading VAR=value
  const first = basename(words[i] ?? '');
  if (SHELLS.has(first)) {
    const c = words.findIndex((w, idx) => idx > i && /^-[a-zA-Z]*c[a-zA-Z]*$/.test(w));
    return c !== -1 && isForbidden(words.slice(c + 1).join(' '));
  }
  if (first === 'eval') return isForbidden(words.slice(i + 1).join(' '));
  if (WRAPPERS.has(first)) {
    const g = words.findIndex((w, idx) => idx > i && basename(w) === 'git');
    if (g === -1) return false;
    i = g;
  }
  if (basename(words[i] ?? '') !== 'git') return false;
  i++;
  while (i < words.length && words[i].startsWith('-')) i += GIT_OPTS_WITH_VALUE.has(words[i]) ? 2 : 1;
  if (words[i] !== 'push') return false;
  return words.slice(i + 1).some((arg) => FORCE_ARG.some((re) => re.test(arg)));
}

export const isForbidden = (command) => parse(command).some(isForcePush);

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const raw = await new Promise((done) => {
    let data = '';
    process.stdin.on('data', (chunk) => (data += chunk)).on('end', () => done(data || '{}'));
  });
  const command = JSON.parse(raw).tool_input?.command;
  if (typeof command === 'string' && isForbidden(command)) {
    console.log(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: 'PreToolUse',
          permissionDecision: 'deny',
          permissionDecisionReason:
            'Blocked: force-pushing (including --force-with-lease) rewrites remote history. Ask the user to run it themselves.',
        },
      }),
    );
  }
}
