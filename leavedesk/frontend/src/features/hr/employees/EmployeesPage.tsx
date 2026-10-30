import { useState } from "react";
import { ApiError } from "../../../api/problem";
import { formatDate } from "../../../lib/dates";
import { Button } from "../../../ui/Button";
import { useToast } from "../../../ui/Toast";
import { useTeams } from "../teams/api";
import { useEmployeeMutations, useEmployees, type Employee } from "./api";
import { EmployeeForm } from "./EmployeeForm";

type Mode = { kind: "list" } | { kind: "add" } | { kind: "edit"; employee: Employee };

const ROLE_LABEL = { employee: "Employee", manager: "Manager", hr: "HR" } as const;

export function EmployeesPage() {
  const [mode, setMode] = useState<Mode>({ kind: "list" });
  const [serverError, setServerError] = useState<string>();
  const employees = useEmployees();
  const teams = useTeams();
  const { create, update, invite } = useEmployeeMutations();
  const toast = useToast();

  const back = () => {
    setMode({ kind: "list" });
    setServerError(undefined);
  };
  const fail = (e: unknown) => setServerError(e instanceof ApiError ? e.message : "Could not save the employee.");

  // Wait for both lists: a select without its options would submit "no team"/"no manager".
  if (mode.kind !== "list" && employees.data && teams.data) {
    const editing = mode.kind === "edit" ? mode.employee : undefined;
    return (
      <EmployeeForm
        employee={editing}
        employees={employees.data}
        teams={teams.data ?? []}
        serverError={serverError}
        busy={create.isPending || update.isPending}
        onCancel={back}
        onSubmit={(v) =>
          editing
            ? update.mutate(
                { id: editing.id, body: { name: v.name, role: v.role, team_id: v.team_id, manager_id: v.manager_id } },
                { onSuccess: () => (toast("success", "Employee updated."), back()), onError: fail },
              )
            : create.mutate(v, {
                onSuccess: () => (toast("success", "Employee added. An invite email was sent."), back()),
                onError: fail,
              })
        }
      />
    );
  }

  const nameOf = (id: string | null) => employees.data?.find((e) => e.id === id)?.name ?? "";
  const teamOf = (id: string | null) => teams.data?.find((t) => t.id === id)?.name ?? "";

  return (
    <section aria-labelledby="employees-title">
      <h1 id="employees-title">Employees</h1>
      <p>
        <Button onClick={() => setMode({ kind: "add" })} disabled={!employees.data || !teams.data}>
          Add employee
        </Button>
      </p>
      {employees.isError && <p role="alert">Could not load employees.</p>}
      {employees.data && employees.data.length === 0 && <p>No employees yet.</p>}
      {employees.data && employees.data.length > 0 && (
        <table>
          <caption className="visually-hidden">Employees</caption>
          <thead>
            <tr>
              <th scope="col">Name</th>
              <th scope="col">Email</th>
              <th scope="col">Role</th>
              <th scope="col">Team</th>
              <th scope="col">Manager</th>
              <th scope="col">Start date</th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {employees.data.map((e) => (
              <tr key={e.id}>
                <th scope="row">
                  {e.name}
                  {!e.is_active && " (inactive)"}
                </th>
                <td>{e.email}</td>
                <td>{ROLE_LABEL[e.role]}</td>
                <td>{teamOf(e.team_id)}</td>
                <td>{nameOf(e.manager_id)}</td>
                <td>{formatDate(e.start_date)}</td>
                <td>
                  <Button variant="secondary" aria-label={`Edit ${e.name}`} disabled={!teams.data} onClick={() => setMode({ kind: "edit", employee: e })}>
                    Edit
                  </Button>{" "}
                  {e.is_active && (
                    <Button
                      variant="secondary"
                      aria-label={`Re-send invite to ${e.name}`}
                      disabled={invite.isPending}
                      onClick={() =>
                        invite.mutate(e.id, {
                          onSuccess: () => toast("success", `Invite re-sent to ${e.name}.`),
                          onError: (err) => toast("error", err instanceof ApiError ? err.message : "Could not send the invite."),
                        })
                      }
                    >
                      Re-send invite
                    </Button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
