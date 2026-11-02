/** Rounds to the nearest 0.5 so float artefacts (0.30000000000000004) never reach the screen. */
function halves(n: number): number {
  return Math.round(n * 2) / 2;
}

/** 8 -> "8", 8.5 -> "8½", 0.5 -> "½". */
export function formatQuantity(n: number): string {
  const v = halves(n);
  const whole = Math.trunc(v);
  const half = v - whole !== 0;
  if (!half) return String(whole);
  return whole === 0 ? "½" : `${whole}½`;
}

/** 1 -> "1 day", 0.5 -> "½ day", 8.5 -> "8½ days". */
export function formatDays(n: number): string {
  const v = halves(n);
  return `${formatQuantity(v)} ${v <= 1 ? "day" : "days"}`;
}
