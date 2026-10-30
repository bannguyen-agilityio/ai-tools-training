import { TYPE_LABEL } from "../requests/format";
import type { CalendarEntry } from "./api";

export interface Day {
  date: string;
  items: { key: string; text: string; pending: boolean }[];
}

/** The leave text without the day part: "Annual", "Annual (Pending)" or "Off". */
function base(e: CalendarEntry): { text: string; pending: boolean } {
  if ("label" in e) return { text: e.label, pending: false };
  const pending = e.status === "pending";
  return { text: `${TYPE_LABEL[e.leave_type]}${pending ? " (Pending)" : ""}`, pending };
}

/**
 * Lines for one person and day: "Eli: Annual", "Eli: Annual (morning)", and when the two halves
 * differ (Annual in the morning, Off in the afternoon) one line per half, never a merged one.
 */
export function linesFor(name: string, entries: CalendarEntry[]): { text: string; pending: boolean }[] {
  const groups = new Map<string, { pending: boolean; slots: Set<string> }>();
  for (const e of entries) {
    const { text, pending } = base(e);
    const g = groups.get(text) ?? { pending, slots: new Set<string>() };
    g.slots.add(e.slot);
    groups.set(text, g);
  }
  return [...groups.entries()].map(([text, g]) => {
    const part = g.slots.size === 2 ? "" : g.slots.has("am") ? " (morning)" : " (afternoon)";
    return { text: `${name}: ${text}${part}`, pending: g.pending };
  });
}

export function groupByDay(entries: CalendarEntry[]): Day[] {
  const days = new Map<string, Map<string, CalendarEntry[]>>();
  for (const e of entries) {
    const people = days.get(e.date) ?? new Map<string, CalendarEntry[]>();
    const rows = people.get(e.employee_id) ?? [];
    rows.push(e);
    people.set(e.employee_id, rows);
    days.set(e.date, people);
  }
  return [...days.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, people]) => ({
      date,
      items: [...people.entries()].flatMap(([id, rows]) =>
        linesFor(rows[0].employee_name, rows).map((line, i) => ({ key: `${date}-${id}-${i}`, ...line })),
      ),
    }));
}
