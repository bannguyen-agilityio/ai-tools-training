import { formatDate, formatDateShort, todayIso } from "../../lib/dates";
import type { LeaveRequest } from "../requests/api";
import type { TypeBalance } from "./api";

const EXPIRY_WARNING_DAYS = 60;

function dayNumber(iso: string): number {
  return Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10)) / 86_400_000;
}

export function daysUntil(iso: string, today: string): number {
  return dayNumber(iso) - dayNumber(today);
}

/** Entitlement plus carried days that have not expired. */
export function annualTotal(b: TypeBalance): number {
  return b.entitlement + (b.carried_expired ? 0 : b.carried);
}

export function expiresSoon(b: TypeBalance, today: string): boolean {
  return (
    b.carried > 0 &&
    !b.carried_expired &&
    b.expires_on !== null &&
    daysUntil(b.expires_on, today) <= EXPIRY_WARNING_DAYS
  );
}

const PART = { am: "morning", pm: "afternoon" } as const;

/** "Mon 9 Nov", "Wed 23 Dec, morning", "Mon 28 – Wed 30 Dec"; the year is added when it is not this year. */
export function upcomingDates(r: Pick<LeaveRequest, "start_date" | "end_date" | "start_part">): string {
  const year = Number(todayIso().slice(0, 4));
  const parts = (iso: string) => formatDate(iso).split(" "); // [Mon, 2, Nov, 2026]
  if (r.start_date === r.end_date) {
    const d = formatDateShort(r.start_date, year);
    return r.start_part === "full" ? d : `${d}, ${PART[r.start_part]}`;
  }
  const [sw, sd, sm, sy] = parts(r.start_date);
  const end = formatDateShort(r.end_date, year);
  const sameMonth = r.start_date.slice(0, 7) === r.end_date.slice(0, 7);
  const start = sameMonth
    ? `${sw} ${sd}`
    : sy === r.end_date.slice(0, 4)
      ? `${sw} ${sd} ${sm}`
      : formatDateShort(r.start_date, year);
  return `${start} – ${end}`;
}

/** First page of both statuses, merged: end on or after today, soonest first, at most `max`. */
export function upcoming(pending: LeaveRequest[], approved: LeaveRequest[], today: string, max = 5): LeaveRequest[] {
  return [...pending, ...approved]
    .filter((r) => r.end_date >= today)
    .sort((a, b) => a.start_date.localeCompare(b.start_date) || a.submitted_at.localeCompare(b.submitted_at))
    .slice(0, max);
}

/** "Thu 29 Oct" for the oldest submission among items, in the company time zone. */
export function oldestSubmitted(items: Pick<LeaveRequest, "submitted_at">[]): string | null {
  if (items.length === 0) return null;
  const oldest = items.map((i) => i.submitted_at).sort()[0];
  return formatDateShort(todayIso(new Date(oldest)));
}

export { formatDate };
