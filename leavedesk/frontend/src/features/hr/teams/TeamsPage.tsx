import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { ApiError } from "../../../api/problem";
import { Button } from "../../../ui/Button";
import { ErrorSummary } from "../../../ui/ErrorSummary";
import { Select } from "../../../ui/Select";
import { TextField } from "../../../ui/TextField";
import { useToast } from "../../../ui/Toast";
import { useFormFocusFirstError } from "../../../ui/useFormFocusFirstError";
import { useEmployees } from "../employees/api";
import { useTeamMutations, useTeams, type Team } from "./api";

const schema = z.object({
  name: z.string().trim().min(1, "Enter the team name.").max(100, "Use 100 characters or fewer."),
  manager_id: z.string(),
});
type Values = z.infer<typeof schema>;

type Mode = { kind: "list" } | { kind: "add" } | { kind: "edit"; team: Team };

function TeamForm(props: {
  team?: Team;
  managers: { value: string; label: string }[];
  serverError?: string;
  busy: boolean;
  onSubmit: (v: { name: string; manager_id: string | null }) => void;
  onCancel: () => void;
}) {
  const { team, managers, serverError, busy, onSubmit, onCancel } = props;
  const { register, handleSubmit, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { name: team?.name ?? "", manager_id: team?.manager_id ?? "" },
    shouldFocusError: false,
  });
  const { errors, submitCount } = formState;
  const formRef = useFormFocusFirstError(submitCount, Object.keys(errors).length);
  const summary = errors.name?.message ? [{ fieldName: "name", message: errors.name.message }] : [];
  return (
    <form
      ref={formRef}
      noValidate
      aria-label={team ? "Edit team" : "Add team"}
      onSubmit={handleSubmit((v) => onSubmit({ name: v.name, manager_id: v.manager_id || null }))}
    >
      <h2>{team ? "Edit team" : "Add team"}</h2>
      <ErrorSummary items={summary} />
      {serverError && <p role="alert">{serverError}</p>}
      <TextField label="Team name" error={errors.name?.message} {...register("name")} />
      <Select label="Team manager" options={[{ value: "", label: "No manager" }, ...managers]} {...register("manager_id")} />
      <Button type="submit" disabled={busy}>
        Save team
      </Button>{" "}
      <Button variant="secondary" onClick={onCancel}>
        Cancel
      </Button>
    </form>
  );
}

export function TeamsPage() {
  const [mode, setMode] = useState<Mode>({ kind: "list" });
  const [serverError, setServerError] = useState<string>();
  const teams = useTeams();
  const employees = useEmployees();
  const { create, update } = useTeamMutations();
  const toast = useToast();

  const back = () => {
    setMode({ kind: "list" });
    setServerError(undefined);
  };
  const fail = (e: unknown) => setServerError(e instanceof ApiError ? e.message : "Could not save the team.");

  // Wait for the employee list: the manager select needs its options before it can be saved.
  if (mode.kind !== "list" && employees.data) {
    const editing = mode.kind === "edit" ? mode.team : undefined;
    const managers = employees.data.filter((e) => e.is_active || e.id === editing?.manager_id).map((e) => ({ value: e.id, label: e.name }));
    return (
      <TeamForm
        team={editing}
        managers={managers}
        serverError={serverError}
        busy={create.isPending || update.isPending}
        onCancel={back}
        onSubmit={(v) =>
          editing
            ? update.mutate({ id: editing.id, body: v }, { onSuccess: () => (toast("success", "Team updated."), back()), onError: fail })
            : create.mutate(v, { onSuccess: () => (toast("success", "Team added."), back()), onError: fail })
        }
      />
    );
  }

  const managerName = (id: string | null) => employees.data?.find((e) => e.id === id)?.name ?? "";
  return (
    <section aria-labelledby="teams-title">
      <h1 id="teams-title">Teams</h1>
      <p>
        <Button onClick={() => setMode({ kind: "add" })} disabled={!employees.data}>
          Add team
        </Button>
      </p>
      {teams.isError && <p role="alert">Could not load teams.</p>}
      {teams.data && teams.data.length === 0 && <p>No teams yet.</p>}
      {teams.data && teams.data.length > 0 && (
        <table>
          <caption className="visually-hidden">Teams</caption>
          <thead>
            <tr>
              <th scope="col">Team</th>
              <th scope="col">Manager</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {teams.data.map((t) => (
              <tr key={t.id}>
                <th scope="row">{t.name}</th>
                <td>{managerName(t.manager_id)}</td>
                <td>
                  <Button variant="secondary" aria-label={`Edit ${t.name}`} disabled={!employees.data} onClick={() => setMode({ kind: "edit", team: t })}>
                    Edit
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
