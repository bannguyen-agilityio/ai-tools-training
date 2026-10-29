import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../../api/client";

export interface Holiday {
  id: string;
  holiday_date: string;
  name: string;
  source: "seed" | "manual";
}

export interface HolidayChange {
  holiday: Holiday;
  affected_requests: number;
}

export interface HolidayInput {
  holiday_date: string;
  name: string;
}

export const holidaysKey = (year: number) => ["holidays", year] as const;

export function useHolidays(year: number) {
  return useQuery({ queryKey: holidaysKey(year), queryFn: () => api<Holiday[]>(`/holidays?year=${year}`) });
}

/** Pending/Approved requests a holiday on `date` touches, before it is saved (C-8). */
export function useImpact(date: string) {
  return useQuery({
    queryKey: ["holiday-impact", date],
    queryFn: () => api<{ affected_requests: number }>(`/hr/holidays/impact?date=${date}`),
    enabled: date !== "",
    select: (r) => r.affected_requests,
  });
}

export function useHolidayMutations() {
  const client = useQueryClient();
  const done = () => Promise.all([
    client.invalidateQueries({ queryKey: ["holidays"] }),
    client.invalidateQueries({ queryKey: ["holiday-impact"] }),
  ]);
  return {
    create: useMutation({
      mutationFn: (body: HolidayInput) => api<HolidayChange>("/hr/holidays", { method: "POST", body }),
      onSuccess: done,
    }),
    update: useMutation({
      mutationFn: ({ id, body }: { id: string; body: Partial<HolidayInput> }) =>
        api<HolidayChange>(`/hr/holidays/${id}`, { method: "PATCH", body }),
      onSuccess: done,
    }),
    remove: useMutation({
      mutationFn: (id: string) => api<HolidayChange>(`/hr/holidays/${id}`, { method: "DELETE" }),
      onSuccess: done,
    }),
  };
}
