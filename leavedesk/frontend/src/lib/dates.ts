export const COMPANY_TZ = "Asia/Ho_Chi_Minh";

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const ISO = /^(\d{4})-(\d{2})-(\d{2})$/;
const DISPLAY = /^(?:([A-Za-z]{3}) )?(\d{1,2}) ([A-Za-z]{3}) (\d{4})$/;

function valid(y: number, m: number, d: number): Date | null {
  const date = new Date(Date.UTC(y, m, d));
  return date.getUTCFullYear() === y && date.getUTCMonth() === m && date.getUTCDate() === d
    ? date
    : null;
}

/** ISO date (YYYY-MM-DD) to "Mon 2 Nov 2026". Calendar arithmetic only, no timezone shift. */
export function formatDate(iso: string): string {
  const m = ISO.exec(iso);
  const date = m && valid(+m[1], +m[2] - 1, +m[3]);
  if (!date) throw new RangeError(`Invalid ISO date: ${iso}`);
  return `${DAYS[date.getUTCDay()]} ${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()}`;
}

/** "Mon 2 Nov 2026" (weekday optional) to ISO, or null when it is not a real date. */
export function parseDate(text: string): string | null {
  const m = DISPLAY.exec(text.trim());
  if (!m) return null;
  const month = MONTHS.findIndex((x) => x.toLowerCase() === m[3].toLowerCase());
  const date = month >= 0 ? valid(+m[4], month, +m[2]) : null;
  if (!date) return null;
  const iso = date.toISOString().slice(0, 10);
  if (m[1] && formatDate(iso).slice(0, 3).toLowerCase() !== m[1].toLowerCase()) return null;
  return iso;
}

/** Today's ISO date in the company timezone. */
export function todayIso(now: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: COMPANY_TZ }).format(now);
}
