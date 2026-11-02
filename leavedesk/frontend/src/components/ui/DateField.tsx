import { Field } from "./Field";

interface DateFieldProps {
  label: string;
  /** ISO date (YYYY-MM-DD) or "" - the same value that goes on the wire. */
  value: string;
  onChange: (iso: string) => void;
  error?: string;
  hint?: string;
  name?: string;
}

/**
 * Native calendar picker (R31c): the user picks a day instead of typing text.
 * Value in and out is ISO; "" while empty.
 */
export function DateField({ label, value, onChange, error, hint, name }: DateFieldProps) {
  return (
    <Field label={label} error={error} hint={hint ?? "Pick a date from the calendar."}>
      {(control) => (
        <input
          className="input"
          type="date"
          name={name}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          {...control}
        />
      )}
    </Field>
  );
}
