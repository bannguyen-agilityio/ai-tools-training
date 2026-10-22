#!/usr/bin/env node
// Claude Code hook: notify when Claude finishes responding (Stop event).
//
// Always rings the terminal bell, then makes a best-effort desktop notification with whatever
// the platform offers (macOS osascript, WSL powershell.exe toast, Linux notify-send). Every
// step is optional and failures are ignored: a notification must never block or break Claude.
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { basename } from 'node:path';

const title = 'Claude Code';
const project = basename(process.env.CLAUDE_PROJECT_DIR ?? process.cwd());
const message = `Finished responding in ${project}`;

// Bell goes to the controlling terminal; stdout/stderr of a hook are not shown to the user.
try {
  writeFileSync('/dev/tty', '\x07');
} catch {
  // no controlling terminal (headless/CI): skip
}

const run = (cmd, args) => spawnSync(cmd, args, { stdio: 'ignore', timeout: 5000 });
const isWsl = () => {
  try {
    return /microsoft/i.test(readFileSync('/proc/version', 'utf8'));
  } catch {
    return false;
  }
};

if (process.platform === 'darwin') {
  run('osascript', ['-e', `display notification "${message}" with title "${title}"`]);
} else if (isWsl() && existsSync('/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe')) {
  const ps = `
$null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent('ToastText02')
$text = $xml.GetElementsByTagName('text')
$null = $text[0].AppendChild($xml.CreateTextNode('${title}'))
$null = $text[1].AppendChild($xml.CreateTextNode('${message.replaceAll("'", "''")}'))
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Code').Show($toast)`;
  run('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', ps]);
} else if (process.platform === 'linux') {
  run('notify-send', [title, message]);
}
process.exit(0);
