import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

export interface Me {
  id: string;
  name: string;
  email: string;
  role: "employee" | "manager" | "hr";
  is_hr_deputy: boolean;
}

/** The signed-in user. Never redirects itself: callers decide (the shell also renders signed out). */
export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => api<Me>("/me", { noRedirect: true }),
    retry: false,
    staleTime: 60_000,
  });
}
