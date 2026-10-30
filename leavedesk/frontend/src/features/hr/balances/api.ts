import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../../api/client";

export type LeaveType = "annual" | "sick";
export type EntryKind = "opening" | "carry_over" | "adjustment";

export interface Balance {
  leave_type_code: LeaveType;
  entitlement_remaining: string;
  carried_remaining: string;
  used: string;
  reserved: string;
  available: string;
}

export interface BalanceRow {
  employee_id: string;
  employee_name: string;
  email: string;
  balances: Balance[];
}

export interface LedgerEntry {
  id: string;
  leave_type_code: LeaveType;
  leave_year: number;
  kind: string;
  days: string;
  expires_on: string | null;
  reason: string | null;
  source: string;
  created_at: string;
}

export interface EmployeeBalances {
  employee_id: string;
  employee_name: string;
  leave_year: number;
  balances: Balance[];
  ledger: LedgerEntry[];
}

export interface EntryInput {
  leave_type_code: LeaveType;
  kind: EntryKind;
  days: number;
  leave_year?: number;
  expires_on?: string;
  reason?: string;
}

export interface Summary {
  employee_name: string;
  leave_type_code: LeaveType;
  leave_year: number;
  kind: EntryKind;
  days: string;
  expires_on: string | null;
  resulting_available: string;
}

export function useBalanceList() {
  return useQuery({
    queryKey: ["hr-balances"],
    queryFn: () => api<{ leave_year: number; items: BalanceRow[] }>("/hr/balances"),
  });
}

export function useEmployeeBalances(employeeId: string | undefined) {
  return useQuery({
    queryKey: ["hr-balances", employeeId],
    enabled: !!employeeId,
    queryFn: () => api<EmployeeBalances>(`/hr/employees/${employeeId}/balances`),
  });
}

export function useEntryMutations(employeeId: string) {
  const client = useQueryClient();
  const base = `/hr/employees/${employeeId}/balance-entries`;
  return {
    preview: useMutation({
      mutationFn: (body: EntryInput) => api<Summary>(`${base}/preview`, { method: "POST", body }),
    }),
    save: useMutation({
      mutationFn: (body: EntryInput) => api<LedgerEntry>(base, { method: "POST", body }),
      onSuccess: () => client.invalidateQueries({ queryKey: ["hr-balances"] }),
    }),
  };
}
