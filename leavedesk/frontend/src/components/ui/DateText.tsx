import { formatDate, formatDateShort } from "../../lib/dates";
import { formatDays, formatQuantity } from "../../lib/days";

/** "Mon 2 Nov 2026" in the company calendar, as a semantic <time>. */
export function DateText({ iso, short = false }: { iso: string; short?: boolean }) {
  return <time dateTime={iso}>{short ? formatDateShort(iso) : formatDate(iso)}</time>;
}

/** Day quantities with "½", never "0.5". `unit` adds "day" / "days". */
export function DaysText({ value, unit = true }: { value: number; unit?: boolean }) {
  return <span className="num">{unit ? formatDays(value) : formatQuantity(value)}</span>;
}
