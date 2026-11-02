// Verifies WCAG 2.1 AA for the token pairs in both themes. Run: node scripts/check-contrast.mjs
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../src/styles/tokens.css", import.meta.url), "utf8");
const block = (re) => Object.fromEntries([...css.match(re)[1].matchAll(/--([\w-]+):\s*(#[0-9a-f]{6})/gi)].map((m) => [m[1], m[2]]));
const light = block(/^:root \{([\s\S]*?)\n\}/m);
const dark = { ...light, ...block(/:root\[data-theme="dark"\] \{([\s\S]*?)\n\}/) };

const lum = (hex) => {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
};
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };

const pairs = [
  ["text on bg", "color-text", "color-bg", 4.5],
  ["text on surface", "color-text", "color-surface", 4.5],
  ["muted on surface", "color-text-muted", "color-surface", 4.5],
  ["muted on bg", "color-text-muted", "color-bg", 4.5],
  ["muted on raised", "color-text-muted", "color-surface-raised", 4.5],
  ["primary btn", "color-primary-contrast", "color-primary", 4.5],
  ["danger btn", "color-danger-contrast", "color-danger", 4.5],
  ["danger text on surface", "color-danger", "color-surface", 4.5],
  ["focus ring on bg", "color-focus-ring", "color-bg", 3],
  ["focus ring on surface", "color-focus-ring", "color-surface", 3],
  ["control border on surface", "color-border-strong", "color-surface", 3],
  ["control border on bg", "color-border-strong", "color-bg", 3],
  ...["pending", "approved", "rejected", "cancelled", "info", "warning", "success", "annual", "unpaid", "off"].flatMap((s) => [
    [`${s} fg/bg`, `color-${s}-fg`, `color-${s}-bg`, 4.5],
    [`${s} border/surface`, `color-${s}-border`, "color-surface", 3],
  ]),
];

let failed = 0;
const rows = [];
for (const [name, fg, bg, min] of pairs) {
  const r = ["light", "dark"].map((t) => ratio((t === "light" ? light : dark)[fg], (t === "light" ? light : dark)[bg]));
  const ok = r.every((v) => v >= min);
  if (!ok) failed++;
  rows.push(`| ${name} | ${min}:1 | ${r[0].toFixed(1)} | ${r[1].toFixed(1)} | ${ok ? "pass" : "FAIL"} |`);
}
console.log("| Pair | Min | Light | Dark | |\n|---|---|---|---|---|\n" + rows.join("\n"));
process.exit(failed ? 1 : 0);
