import { useId, type ReactNode } from "react";
import { FormError } from "./FormError";

export interface ControlProps {
  id: string;
  "aria-invalid": boolean | undefined;
  "aria-describedby": string | undefined;
}

interface FieldProps {
  label: string;
  error?: string;
  hint?: string;
  children: (control: ControlProps) => ReactNode;
}

/** Visible label, hint and linked error around one control (R31b). */
export function Field({ label, error, hint, children }: FieldProps) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;
  return (
    <div className="field">
      <label htmlFor={id} className="field__label">
        {label}
      </label>
      {hint && (
        <p id={hintId} className="field__hint">
          {hint}
        </p>
      )}
      {children({ id, "aria-invalid": error ? true : undefined, "aria-describedby": describedBy })}
      {error && <FormError id={errorId}>{error}</FormError>}
    </div>
  );
}
