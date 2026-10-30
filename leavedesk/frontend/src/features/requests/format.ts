import { formatDate } from "../../lib/dates";
import type { LeaveRequest, LeaveType, Part } from "./api";

export const TYPE_LABEL: Record<LeaveType, string> = {
  annual: "Annual",
  sick: "Sick",
  unpaid: "Unpaid",
};
const PART_LABEL: Record<Part, string> = {
  full: "full day",
  am: "morning",
  pm: "afternoon",
};

export function typeLabel(
  r: Pick<LeaveRequest, "leave_type" | "label">,
): string {
  return r.leave_type ? TYPE_LABEL[r.leave_type] : (r.label ?? "Off");
}

/** "Mon 2 Nov 2026" or "Mon 2 Nov 2026 (afternoon) to Wed 4 Nov 2026 (morning)". */
export function rangeText(
  r: Pick<LeaveRequest, "start_date" | "end_date" | "start_part" | "end_part">,
): string {
  if (r.start_date === r.end_date) {
    return r.start_part === "full"
      ? formatDate(r.start_date)
      : `${formatDate(r.start_date)} (${PART_LABEL[r.start_part]})`;
  }
  const side = (iso: string, part: Part) =>
    part === "full"
      ? formatDate(iso)
      : `${formatDate(iso)} (${PART_LABEL[part]})`;
  return `${side(r.start_date, r.start_part)} to ${side(r.end_date, r.end_part)}`;
}

export function daysText(n: number): string {
  return `${n} ${n === 1 ? "day" : "days"}`;
}

export function statusText(status: LeaveRequest["status"]): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}
