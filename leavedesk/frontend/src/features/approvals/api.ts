import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import type { LeaveRequest } from "../requests/api";

export function useAssignedApprovals() {
  return useQuery({
    queryKey: ["approvals"],
    queryFn: () =>
      api<{ items: LeaveRequest[] }>("/approvals?scope=assigned"),
    select: (r) => r.items,
  });
}

export interface Decision {
  version: number;
  /** Present for a rejection only (1–500 characters, R19). */
  reason?: string;
}

export function useDecide(id: string, action: "approve" | "reject") {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Decision) =>
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
