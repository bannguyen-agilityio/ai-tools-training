import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import { Button } from "./ui/Button";
import { DateField } from "./ui/DateField";
import { ErrorSummary } from "./ui/ErrorSummary";
import { Select } from "./ui/Select";
import { TextField } from "./ui/TextField";
import { useFormFocusFirstError } from "./ui/useFormFocusFirstError";

const schema = z.object({
  name: z.string().min(1, "Enter your name, for example Linh Tran."),
  type: z.string(),
  start: z.string().min(1, "Enter the first day, for example Mon 2 Nov 2026."),
});
type Values = z.infer<typeof schema>;

/** Reference form showing how the shared pieces fit together; later slices copy this shape. */
export function SampleForm() {
  const { register, control, handleSubmit, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", type: "annual", start: "" },
  });
  const { errors, submitCount } = formState;
  const formRef = useFormFocusFirstError(submitCount, Object.keys(errors).length);
  const summary = (["name", "start"] as const).flatMap((k) =>
    errors[k]?.message ? [{ fieldId: k, message: errors[k].message }] : [],
  );

  return (
    <form ref={formRef} noValidate onSubmit={handleSubmit(() => {})}>
      <h1>Request leave</h1>
      <ErrorSummary items={summary} />
      <TextField label="Your name" error={errors.name?.message} {...register("name")} />
      <Select
        label="Leave type"
        options={[
          { value: "annual", label: "Annual" },
          { value: "unpaid", label: "Unpaid" },
        ]}
        {...register("type")}
      />
      <Controller
        control={control}
        name="start"
        render={({ field }) => (
          <DateField label="First day" value={field.value} onChange={field.onChange} error={errors.start?.message} />
        )}
      />
      <Button type="submit">Submit request</Button>
    </form>
  );
}
