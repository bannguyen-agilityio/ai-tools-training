import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../../api/client";

export interface Team {
  id: string;
  name: string;
  manager_id: string | null;
}

export interface TeamInput {
  name: string;
  manager_id: string | null;
}

export function useTeams() {
  return useQuery({
    queryKey: ["teams"],
    queryFn: () => api<{ items: Team[] }>("/hr/teams"),
    select: (r) => r.items,
  });
}

export function useTeamMutations() {
  const client = useQueryClient();
  const done = () => client.invalidateQueries({ queryKey: ["teams"] });
  return {
    create: useMutation({
      mutationFn: (body: TeamInput) => api<Team>("/hr/teams", { method: "POST", body }),
      onSuccess: done,
    }),
    update: useMutation({
      mutationFn: ({ id, body }: { id: string; body: Partial<TeamInput> }) =>
        api<Team>(`/hr/teams/${id}`, { method: "PATCH", body }),
      onSuccess: done,
    }),
  };
}
