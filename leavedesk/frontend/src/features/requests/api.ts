import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";

export type LeaveType = "annual" | "sick" | "unpaid";
export type Part = "full" | "am" | "pm";

export interface RequestInput {
  leave_type: LeaveType;
  start_date: string;
  start_part: Part;
  end_date: string;
  end_part: Part;
  note?: string;
}

export interface LeaveRequest {
  id: string;
  employee_id: string;
  /** Null when the server redacts the Sick type (§8); `label` is then "Off". */
  leave_type: LeaveType | null;
  start_date: string;
  start_part: Part;
  end_date: string;
  end_part: Part;
  working_days: number;
  note: string | null;
  status: "pending" | "approved" | "rejected" | "cancelled";
  queue: string;
  assigned_to: string | null;
  submitted_at: string;
  notice_warning: boolean;
  version: number;
  label: string | null;
}

export interface Preview {
  valid: boolean;
  working_days: number | null;
  per_year: {
    year: number;
    days: number;
    available_before: number | null;
    available_after: number | null;
  }[];
  errors: { code: string; field: string | null; message: string }[];
}

export function usePreview(input: RequestInput | null) {
  return useQuery({
    queryKey: ["request-preview", input],
    queryFn: () =>
      api<Preview>("/requests/preview", { method: "POST", body: input }),
    enabled: input !== null,
    placeholderData: (previous) => previous,
  });
}

export function useCreateRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: RequestInput) =>
      api<LeaveRequest>("/requests", { method: "POST", body: input }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["my-requests"] });
      void qc.invalidateQueries({ queryKey: ["my-balances"] });
    },
  });
}

export function useMyRequests() {
  return useQuery({
    queryKey: ["my-requests"],
    queryFn: () =>
      api<{ items: LeaveRequest[]; next_cursor: string | null }>(
        "/me/requests",
      ),
    select: (r) => r.items,
  });
}

export function useRequest(id: string) {
  return useQuery({
    queryKey: ["request", id],
    queryFn: () => api<LeaveRequest>(`/requests/${id}`),
  });
}
