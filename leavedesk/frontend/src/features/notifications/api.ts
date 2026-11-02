import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";

export interface AppNotification {
  id: string;
  kind: string;
  title: string;
  body: string;
  link: string;
  read_at: string | null;
  created_at: string;
}
export interface NotificationList {
  unread_count: number;
  items: AppNotification[];
}

/** Own notifications only (R35). `enabled` keeps signed-out pages from calling the API. */
export function useNotifications(enabled: boolean) {
  return useQuery({
    queryKey: ["notifications"],
    queryFn: () => api<NotificationList>("/notifications", { noRedirect: true }),
    enabled,
    refetchInterval: 60_000,
    retry: false,
  });
}

export function useMarkRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api(`/notifications/${id}/read`, { method: "POST" }),
    onSettled: () => void qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api("/notifications/read-all", { method: "POST" }),
    onSettled: () => void qc.invalidateQueries({ queryKey: ["notifications"] }),
  });
}
