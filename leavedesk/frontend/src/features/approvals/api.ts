import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import type { LeaveRequest } from "../requests/api";

export type ApprovalScope = "assigned" | "cover";

export function useApprovals(scope: ApprovalScope = "assigned") {
  return useQuery({
    queryKey: ["approvals", scope],
    queryFn: () => api<{ items: LeaveRequest[] }>(`/approvals?scope=${scope}`),
    select: (r) => r.items,
  });
}

export interface Decision {
  action: "approve" | "reject";
  version: number;
  /** Present for a rejection only (1–500 characters, R19). */
  reason?: string;
  /** Cover (R20): the direct manager being stood in for. */
  on_behalf_of?: string;
}

export function useDecide(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ action, ...body }: Decision) =>
      api<LeaveRequest>(`/approvals/${id}/${action}`, {
        method: "POST",
        body,
      }),
    // The list is not invalidated here: the item must stay on screen to show the outcome or
    // the "already decided" message. It is refetched the next time the screen mounts.
    onSettled: () => {
      void qc.invalidateQueries({ queryKey: ["request", id] });
    },
  });
}
