import { useInfiniteQuery } from "@tanstack/react-query";
import { api } from "../../../api/client";

export interface HrLeave {
  id: string;
  employee_id: string;
  employee_name: string;
  team_id: string | null;
  leave_type: "annual" | "sick" | "unpaid";
  start_date: string;
  start_part: "full" | "am" | "pm";
  end_date: string;
  end_part: "full" | "am" | "pm";
  working_days: number;
  note: string | null;
  status: "pending" | "approved" | "rejected" | "cancelled";
  version: number;
}

export interface LeaveFilters {
  status: string;
  from: string;
  to: string;
  employee_id: string;
  team_id: string;
  type: string;
}

export const NO_FILTERS: LeaveFilters = { status: "approved", from: "", to: "", employee_id: "", team_id: "", type: "" };

export function useAllLeave(filters: LeaveFilters) {
  // A reversed range would only come back as a 422; the form already flags it.
  const reversed = filters.from !== "" && filters.to !== "" && filters.to < filters.from;
  return useInfiniteQuery({
    enabled: !reversed,
    queryKey: ["hr-leave", filters],
    initialPageParam: "",
    queryFn: ({ pageParam }) => {
      const q = new URLSearchParams({ limit: "50" });
      for (const [key, value] of Object.entries(filters)) if (value) q.set(key, value);
      if (pageParam) q.set("cursor", pageParam);
      return api<{ items: HrLeave[]; next_cursor: string | null }>(`/hr/leave?${q}`);
    },
    getNextPageParam: (last) => last.next_cursor ?? undefined,
  });
}
