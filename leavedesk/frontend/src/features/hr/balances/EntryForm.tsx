import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm, useWatch } from "react-hook-form";
import { z } from "zod";
import { Button } from "../../../ui/Button";
import { DateField } from "../../../ui/DateField";
import { ErrorSummary } from "../../../ui/ErrorSummary";
import { Select } from "../../../ui/Select";
import { TextField } from "../../../ui/TextField";
import { useFormFocusFirstError } from "../../../ui/useFormFocusFirstError";
import type { EntryInput } from "./api";

const schema = z
  .object({
    leave_type_code: z.enum(["annual", "sick"]),
    kind: z.enum(["opening", "carry_over", "adjustment"]),
    leave_year: z.string(),
    days: z.string().trim().min(1, "Enter the number of days."),
    expires_on: z.string(),
    reason: z.string().trim().max(500, "Use 500 characters or fewer."),
  })
  .superRefine((v, ctx) => {
    const days = Number(v.days);
    const bounded = v.kind === "adjustment" ? Math.abs(days) <= 40 : days >= 0 && days <= 40;
    if (v.days && (!Number.isFinite(days) || days * 2 !== Math.round(days * 2))) {
      ctx.addIssue({ code: "custom", path: ["days"], message: "Enter days in steps of 0.5, for example 7.5." });
    } else if (v.days && !bounded) {
      const range = v.kind === "adjustment" ? "-40 and 40" : "0 and 40";
      ctx.addIssue({ code: "custom", path: ["days"], message: `Days must be between ${range}.` });
    }
    if (v.kind === "carry_over" && Number.isFinite(days) && days > 6) {
      ctx.addIssue({ code: "custom", path: ["days"], message: "Carried days are at most 6." });
    }
    if (v.kind === "carry_over" && !v.expires_on) {
      ctx.addIssue({ code: "custom", path: ["expires_on"], message: "Enter the expiry date, for example Thu 31 Dec 2026." });
    }
    if (v.kind === "adjustment" && !v.reason) {
      ctx.addIssue({ code: "custom", path: ["reason"], message: "Enter the reason for the correction." });
    }
  });
type Values = z.infer<typeof schema>;

const THIS_YEAR = new Date().getFullYear();
const YEARS = [THIS_YEAR - 1, THIS_YEAR, THIS_YEAR + 1].map((y) => ({ value: String(y), label: String(y) }));
const TYPES = [
  { value: "annual", label: "Annual" },
  { value: "sick", label: "Sick" },
];
const KINDS = [
  { value: "opening", label: "Opening balance" },
  { value: "carry_over", label: "Carried days (with expiry)" },
  { value: "adjustment", label: "Correction (adjustment)" },
];

interface Props {
  employeeName: string;
  serverError?: string;
  busy?: boolean;
  onSubmit: (entry: EntryInput) => void;
  onCancel: () => void;
}

/** Fields in reading order, so Tab/Enter works for 250 entries by keyboard. */
export function EntryForm({ employeeName, serverError, busy, onSubmit, onCancel }: Props) {
  const { register, control, handleSubmit, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { leave_year: String(THIS_YEAR), leave_type_code: "annual", kind: "opening", days: "", expires_on: "", reason: "" },
    shouldFocusError: false,
  });
  const { errors, submitCount } = formState;
  const formRef = useFormFocusFirstError(submitCount, Object.keys(errors).length);
  const kind = useWatch({ control, name: "kind" });
  const summary = (["days", "expires_on", "reason"] as const).flatMap((k) =>
    errors[k]?.message ? [{ fieldName: k, message: errors[k].message }] : [],
  );

  return (
    <form
      ref={formRef}
      noValidate
      aria-label={`Balance entry for ${employeeName}`}
      onSubmit={handleSubmit((v) =>
        onSubmit({
          leave_type_code: v.leave_type_code,
          kind: v.kind,
          days: Number(v.days),
          leave_year: Number(v.leave_year),
          ...(v.kind === "carry_over" ? { expires_on: v.expires_on } : {}),
          ...(v.kind === "adjustment" ? { reason: v.reason } : {}),
        }),
      )}
    >
      <h2>Balance entry for {employeeName}</h2>
      <ErrorSummary items={summary} />
      {serverError && <p role="alert">{serverError}</p>}
      <Select label="Leave year" options={YEARS} {...register("leave_year")} />
      <Select label="Leave type" options={TYPES} {...register("leave_type_code")} />
      <Select label="Entry" options={KINDS} {...register("kind")} />
      <TextField
        label="Days"
        inputMode="decimal"
        hint={kind === "adjustment" ? "Use a minus sign to take days off, for example -2." : "0 to 40, in steps of 0.5."}
        error={errors.days?.message}
        {...register("days")}
      />
      {kind === "carry_over" && (
        <Controller
          control={control}
          name="expires_on"
          render={({ field }) => (
            <DateField
              name="expires_on"
              label="Carried days expire on"
              value={field.value}
              onChange={field.onChange}
              error={errors.expires_on?.message}
            />
          )}
        />
      )}
      {kind === "adjustment" && (
        <TextField label="Reason" hint="Required. Kept in the ledger." error={errors.reason?.message} {...register("reason")} />
      )}
      <Button type="submit" disabled={busy}>
        Review entry
      </Button>{" "}
      <Button variant="secondary" onClick={onCancel}>
        Cancel
      </Button>
    </form>
  );
}
