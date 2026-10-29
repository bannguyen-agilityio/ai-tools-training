import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "../../../ui/Button";
import { DateField } from "../../../ui/DateField";
import { ErrorSummary } from "../../../ui/ErrorSummary";
import { TextField } from "../../../ui/TextField";
import { useFormFocusFirstError } from "../../../ui/useFormFocusFirstError";
import { useImpact, type HolidayInput } from "./api";

const schema = z.object({
  holiday_date: z.string().min(1, "Enter the date, for example Wed 2 Sep 2026."),
  name: z.string().trim().min(1, "Enter the holiday name, for example National Day.").max(100, "Use 100 characters or fewer."),
});

interface Props {
  initial?: HolidayInput;
  /** Server-side failure (for example a date that already has a holiday). */
  serverError?: string;
  busy?: boolean;
  onSubmit: (values: HolidayInput) => void;
  onCancel: () => void;
}

export function HolidayForm({ initial, serverError, busy, onSubmit, onCancel }: Props) {
  const { register, control, handleSubmit, watch, formState } = useForm<HolidayInput>({
    resolver: zodResolver(schema),
    defaultValues: initial ?? { holiday_date: "", name: "" },
    shouldFocusError: false, // useFormFocusFirstError focuses in DOM order (R31d)
  });
  const { errors, submitCount } = formState;
  const formRef = useFormFocusFirstError(submitCount, Object.keys(errors).length);
  const date = watch("holiday_date");
  const impact = useImpact(date);
  const summary = (["holiday_date", "name"] as const).flatMap((k) =>
    errors[k]?.message ? [{ fieldName: k, message: errors[k].message }] : [],
  );

  return (
    <form ref={formRef} noValidate onSubmit={handleSubmit(onSubmit)} aria-label={initial ? "Edit holiday" : "Add holiday"}>
      <h2>{initial ? "Edit holiday" : "Add holiday"}</h2>
      <ErrorSummary items={summary} />
      {serverError && <p role="alert">{serverError}</p>}
      <Controller
        control={control}
        name="holiday_date"
        render={({ field }) => (
          <DateField name="holiday_date" label="Date" value={field.value} onChange={field.onChange} error={errors.holiday_date?.message} />
        )}
      />
      <TextField label="Name" error={errors.name?.message} {...register("name")} />
      <p aria-live="polite">
        {date && impact.data !== undefined
          ? `${impact.data} ${impact.data === 1 ? "request" : "requests"} affected on this date.`
          : ""}
      </p>
      <Button type="submit" disabled={busy}>
        Save holiday
      </Button>{" "}
      <Button variant="secondary" onClick={onCancel}>
        Cancel
      </Button>
    </form>
  );
}
