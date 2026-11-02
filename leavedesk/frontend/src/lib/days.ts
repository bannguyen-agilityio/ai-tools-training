/** Rounds to the nearest 0.5 so float artefacts (0.30000000000000004) never reach the screen. */
function halves(n: number): number {
  return Math.round(n * 2) / 2;
}

/** 8 -> "8", 8.5 -> "8½", 0.5 -> "½". */
export function formatQuantity(n: number): string {
  const v = halves(n);
  const sign = v < 0 ? "-" : "";
  const abs = Math.abs(v);
  const whole = Math.trunc(abs);
  if (abs - whole === 0) return String(v === 0 ? 0 : v);
  return whole === 0 ? `${sign}½` : `${sign}${whole}½`;
}

/** 1 -> "1 day", 0.5 -> "½ day", 8.5 -> "8½ days". */
export function formatDays(n: number): string {
  const v = halves(n);
  return `${formatQuantity(v)} ${v === 1 || v === 0.5 ? "day" : "days"}`;
}
