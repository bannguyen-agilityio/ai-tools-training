import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";

/** Masked Sick leave has exactly these keys: no type, no status (spec 6.1). */
export interface OffEntry {
  employee_id: string;
  employee_name: string;
  date: string;
  slot: "am" | "pm";
  label: "Off";
}

export interface LeaveEntry {
  employee_id: string;
  employee_name: string;
  date: string;
  slot: "am" | "pm";
  leave_type: "annual" | "sick" | "unpaid";
  status: "pending" | "approved";
}

export type CalendarEntry = OffEntry | LeaveEntry;

export interface CalendarData {
  month: string;
  team_id: string | null;
  entries: CalendarEntry[];
}

export function useCalendar(month: string, teamId: string, ready: boolean) {
  return useQuery({
    enabled: ready, // wait for /me so the team filter is only ever sent for HR
    queryKey: ["calendar", month, teamId],
    queryFn: () => api<CalendarData>(`/calendar?month=${month}${teamId ? `&team_id=${teamId}` : ""}`),
  });
}
