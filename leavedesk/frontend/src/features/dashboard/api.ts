import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";

export interface TypeBalance {
  leave_type: "annual" | "sick";
  entitlement: number;
  carried: number;
  expires_on: string | null;
  carried_expired: boolean;
  used: number;
  reserved: number;
  available: number;
}

export interface MyBalances {
  year: number;
  balances: TypeBalance[];
}

export function useMyBalances() {
  return useQuery({
    queryKey: ["my-balances"],
    queryFn: () => api<MyBalances>("/me/balances"),
  });
}
