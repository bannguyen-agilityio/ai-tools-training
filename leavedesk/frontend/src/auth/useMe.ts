import { useQuery } from "@tanstack/react-query";
import { api, setCsrfToken } from "../api/client";

export interface Me {
  id: string;
  name: string;
  email: string;
  role: "employee" | "manager" | "hr";
  is_hr_deputy: boolean;
  csrf_token?: string;
}

/** The signed-in user. Never redirects itself: callers decide (the shell also renders signed out). */
export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const me = await api<Me>("/me", { noRedirect: true });
      // sessionStorage is per tab: a new tab has the cookie but no token, so POSTs fail the CSRF check (R29).
      if (me.csrf_token) setCsrfToken(me.csrf_token);
      return me;
    },
    retry: false,
    staleTime: 60_000,
  });
}
