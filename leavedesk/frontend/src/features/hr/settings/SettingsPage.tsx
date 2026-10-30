import { useState, type FormEvent } from "react";
import { ApiError } from "../../../api/problem";
import { Button } from "../../../ui/Button";
import { Field } from "../../../ui/Field";
import { useToast } from "../../../ui/Toast";
import { useEmployees } from "../employees/api";
import { useAssignDeputy, useDeputy } from "./api";

/** HR: Settings. One deputy HR admin, approval and cover only (R36). */
export function SettingsPage() {
  const deputy = useDeputy();
  const employees = useEmployees();
  const assign = useAssignDeputy();
  const toast = useToast();
  const [choice, setChoice] = useState<string>();
  const [error, setError] = useState<string>();

  if (deputy.isPending || employees.isPending) return <p>Loading settings…</p>;
  if (deputy.error || employees.error || !deputy.data || !employees.data) {
    return <p role="alert">Could not load the settings.</p>;
  }
  const current = deputy.data.employee_id ?? "";
  const value = choice ?? current;
  const candidates = employees.data.filter((e) => e.is_active && e.role !== "hr");

  function save(e: FormEvent) {
    e.preventDefault();
    setError(undefined);
    assign.mutate(value === "" ? null : value, {
      onSuccess: () => toast("success", value === "" ? "Deputy removed." : "Deputy saved."),
      onError: (err) => setError(err instanceof ApiError ? err.message : "Could not save the deputy."),
    });
  }

  return (
    <section aria-labelledby="settings-title">
      <h1 id="settings-title">Settings</h1>
      <form onSubmit={save} noValidate>
        <Field
          label="Deputy HR admin"
          hint="Approves HR's own leave and managers' requests when HR is away. Has no access to HR administration."
          error={error}
        >
          {(control) => (
            <select className="input" value={value} onChange={(e) => setChoice(e.target.value)} {...control}>
              <option value="">No deputy</option>
              {deputy.data.employee_id && !candidates.some((e) => e.id === current) && (
                <option value={current}>{deputy.data.name}</option>
              )}
              {candidates.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name}
                </option>
              ))}
            </select>
          )}
        </Field>
        <Button type="submit" disabled={assign.isPending || value === current}>
          Save deputy
        </Button>
      </form>
    </section>
  );
}
