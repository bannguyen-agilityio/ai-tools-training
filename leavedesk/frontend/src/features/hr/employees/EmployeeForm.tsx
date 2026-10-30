import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "../../../ui/Button";
import { DateField } from "../../../ui/DateField";
import { ErrorSummary } from "../../../ui/ErrorSummary";
import { Select } from "../../../ui/Select";
import { TextField } from "../../../ui/TextField";
import { useFormFocusFirstError } from "../../../ui/useFormFocusFirstError";
import type { Team } from "../teams/api";
import type { Employee, EmployeeCreateInput, Role } from "./api";

const COMPANY_DOMAIN = "@asnet.com.vn";

const schema = z.object({
  name: z.string().trim().min(1, "Enter the employee's name.").max(100, "Use 100 characters or fewer."),
  email: z
    .string()
    .trim()
    .toLowerCase()
    .min(1, "Enter the work email.")
    .refine((v) => v.endsWith(COMPANY_DOMAIN), `Use a company email ending in ${COMPANY_DOMAIN}.`),
  role: z.enum(["employee", "manager", "hr"]),
  team_id: z.string(),
  manager_id: z.string(),
  start_date: z.string().min(1, "Enter the start date, for example Mon 2 Nov 2026."),
});
type Values = z.infer<typeof schema>;

const ROLES: { value: Role; label: string }[] = [
  { value: "employee", label: "Employee" },
  { value: "manager", label: "Manager" },
  { value: "hr", label: "HR" },
];

interface Props {
  /** Present when editing: email and start date are then read-only (A-8). */
  employee?: Employee;
  employees: Employee[];
  teams: Team[];
  serverError?: string;
  busy?: boolean;
  onSubmit: (values: EmployeeCreateInput) => void;
  onCancel: () => void;
}

export function EmployeeForm({ employee, employees, teams, serverError, busy, onSubmit, onCancel }: Props) {
  const { register, control, handleSubmit, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: employee?.name ?? "",
      email: employee?.email ?? "",
      role: employee?.role ?? "employee",
      team_id: employee?.team_id ?? "",
      manager_id: employee?.manager_id ?? "",
      start_date: employee?.start_date ?? "",
    },
    shouldFocusError: false, // useFormFocusFirstError focuses in DOM order (R31d)
  });
  const { errors, submitCount } = formState;
  const formRef = useFormFocusFirstError(submitCount, Object.keys(errors).length);
  const summary = (["name", "email", "start_date"] as const).flatMap((k) =>
    errors[k]?.message ? [{ fieldName: k, message: errors[k].message }] : [],
  );
  // Keep the current manager listed even when inactive, so saving never silently clears them.
  const managers = employees.filter(
    (e) => e.id !== employee?.id && (e.is_active || e.id === employee?.manager_id),
  );

  return (
    <form
      ref={formRef}
      noValidate
      aria-label={employee ? "Edit employee" : "Add employee"}
      onSubmit={handleSubmit((v) =>
        onSubmit({ ...v, team_id: v.team_id || null, manager_id: v.manager_id || null }),
      )}
    >
      <h2>{employee ? "Edit employee" : "Add employee"}</h2>
      <ErrorSummary items={summary} />
      {serverError && <p role="alert">{serverError}</p>}
      <TextField label="Name" error={errors.name?.message} {...register("name")} />
      <TextField
        label="Work email"
        type="email"
        hint={employee ? "The email cannot be changed." : `Must end in ${COMPANY_DOMAIN}. An invite is sent here.`}
        readOnly={!!employee}
        error={errors.email?.message}
        {...register("email")}
      />
      <Select label="Role" options={ROLES} {...register("role")} />
      <Select
        label="Team"
        options={[{ value: "", label: "No team" }, ...teams.map((t) => ({ value: t.id, label: t.name }))]}
        {...register("team_id")}
      />
      <Select
        label="Direct manager"
        hint="Leave empty for managers and HR."
        options={[{ value: "", label: "No manager" }, ...managers.map((m) => ({ value: m.id, label: m.name }))]}
        {...register("manager_id")}
      />
      {employee ? (
        <TextField label="Start date" readOnly hint="The start date cannot be changed." value={employee.start_date} />
      ) : (
        <Controller
          control={control}
          name="start_date"
          render={({ field }) => (
            <DateField
              name="start_date"
              label="Start date"
              value={field.value}
              onChange={field.onChange}
              error={errors.start_date?.message}
            />
          )}
        />
      )}
      <Button type="submit" disabled={busy}>
        Save employee
      </Button>{" "}
      <Button variant="secondary" onClick={onCancel}>
        Cancel
      </Button>
    </form>
  );
}
