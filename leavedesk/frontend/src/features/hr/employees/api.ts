import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../../api/client";

export type Role = "employee" | "manager" | "hr";

export interface Employee {
  id: string;
  name: string;
  email: string;
  role: Role;
  is_hr_deputy: boolean;
  team_id: string | null;
  manager_id: string | null;
  start_date: string;
  is_active: boolean;
}

export interface EmployeeCreateInput {
  name: string;
  email: string;
  role: Role;
  team_id: string | null;
  manager_id: string | null;
  start_date: string;
}

export type EmployeeEditInput = Pick<EmployeeCreateInput, "name" | "role" | "team_id" | "manager_id">;

/** HR-only. The API caps a page at 200, which covers the ~250 staff over two pages. */
export function useEmployees() {
  return useQuery({
    queryKey: ["employees"],
    queryFn: async () => {
      const items: Employee[] = [];
      let cursor: string | null = null;
      do {
        const page: { items: Employee[]; next_cursor: string | null } = await api(
          `/hr/employees?limit=200${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ""}`,
        );
        items.push(...page.items);
        cursor = page.next_cursor;
      } while (cursor);
      return items;
    },
  });
}

export function useEmployeeMutations() {
  const client = useQueryClient();
  const done = () => client.invalidateQueries({ queryKey: ["employees"] });
  return {
    create: useMutation({
      mutationFn: (body: EmployeeCreateInput) => api<Employee>("/hr/employees", { method: "POST", body }),
      onSuccess: done,
    }),
    update: useMutation({
      mutationFn: ({ id, body }: { id: string; body: Partial<EmployeeEditInput> }) =>
        api<Employee>(`/hr/employees/${id}`, { method: "PATCH", body }),
      onSuccess: done,
    }),
    deactivate: useMutation({
      mutationFn: (id: string) => api<Employee>(`/hr/employees/${id}/deactivate`, { method: "POST" }),
      onSuccess: done,
    }),
    invite: useMutation({
      mutationFn: (id: string) => api<void>(`/hr/employees/${id}/invite`, { method: "POST" }),
    }),
  };
}
