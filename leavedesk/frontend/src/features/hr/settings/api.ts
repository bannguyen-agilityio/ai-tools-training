import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../../api/client";

export interface Deputy {
  employee_id: string | null;
  name: string | null;
  email: string | null;
}

export function useDeputy() {
  return useQuery({ queryKey: ["deputy"], queryFn: () => api<Deputy>("/hr/deputy") });
}

export function useAssignDeputy() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (employee_id: string | null) => api<Deputy>("/hr/deputy", { method: "PUT", body: { employee_id } }),
    onSuccess: (deputy) => {
      client.setQueryData(["deputy"], deputy);
      void client.invalidateQueries({ queryKey: ["employees"] });
    },
  });
}
