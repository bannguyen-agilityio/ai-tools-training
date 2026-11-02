import { forwardRef, type InputHTMLAttributes } from "react";
import { Field } from "./Field";

interface TextFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "id"> {
  label: string;
  error?: string;
  hint?: string;
}

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  { label, error, hint, className, ...input },
  ref,
) {
  return (
    <Field label={label} error={error} hint={hint}>
      {(control) => <input ref={ref} className={`input ${className ?? ""}`} {...control} {...input} />}
    </Field>
  );
});
