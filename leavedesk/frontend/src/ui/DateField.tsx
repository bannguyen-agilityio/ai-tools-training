import { useState } from "react";
import { formatDate, parseDate } from "../lib/dates";
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

const FORMAT_HINT = "Type a date like Mon 2 Nov 2026";

function show(iso: string): string {
  try {
    return iso ? formatDate(iso) : "";
  } catch {
    return iso;
  }
}

/**
 * Text input that shows and accepts "Mon 2 Nov 2026" (R31c), avoiding the
 * locale-dependent native date input. Emits ISO, or "" while the text is not a date.
 */
export function DateField({ label, value, onChange, error, hint, name }: DateFieldProps) {
  const [text, setText] = useState(show(value));
  const [typed, setTyped] = useState(false);
  const unparsable = typed && text.trim() !== "" && parseDate(text) === null;
  const shownError = error ?? (unparsable ? `Not a date. ${FORMAT_HINT}.` : undefined);

  return (
    <Field label={label} error={shownError} hint={hint ?? FORMAT_HINT}>
      {(control) => (
        <input
          className="input"
          name={name}
          inputMode="text"
          autoComplete="off"
          placeholder="Mon 2 Nov 2026"
          value={text}
          onChange={(e) => {
            setTyped(true);
            setText(e.target.value);
            onChange(parseDate(e.target.value) ?? "");
          }}
          onBlur={() => {
            const iso = parseDate(text);
            if (iso) setText(formatDate(iso));
          }}
          {...control}
        />
      )}
    </Field>
  );
}
