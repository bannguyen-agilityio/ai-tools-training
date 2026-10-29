import { forwardRef, type SelectHTMLAttributes } from "react";
import { Field } from "./Field";

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "id"> {
  label: string;
  error?: string;
  hint?: string;
  options: { value: string; label: string }[];
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { label, error, hint, options, ...select },
  ref,
) {
  return (
    <Field label={label} error={error} hint={hint}>
      {(control) => (
        <select ref={ref} className="input" {...control} {...select}>
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      )}
    </Field>
  );
});
