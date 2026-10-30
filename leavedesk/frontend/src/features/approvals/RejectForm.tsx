import { useEffect, useRef, useState, type FormEvent } from "react";
import { Button } from "../../ui/Button";
import { Field } from "../../ui/Field";

export const MAX_REASON = 500;

interface RejectFormProps {
  pending: boolean;
  serverError?: string;
  onSubmit: (reason: string) => void;
  onCancel: () => void;
}

/** Reason is required (1–500 characters after trimming); the error is inline and takes focus. */
export function RejectForm({
  pending,
  serverError,
  onSubmit,
  onCancel,
}: RejectFormProps) {
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string>();
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => ref.current?.focus(), []);

  function submit(e: FormEvent) {
    e.preventDefault();
    const trimmed = reason.trim();
    if (!trimmed) {
      setError("Enter a reason for rejecting this request.");
      ref.current?.focus();
    } else if (trimmed.length > MAX_REASON) {
      setError(`Use ${MAX_REASON} characters or fewer.`);
      ref.current?.focus();
    } else {
      setError(undefined);
      onSubmit(trimmed);
    }
  }

  return (
    <form onSubmit={submit} noValidate aria-label="Reject request">
      <Field
        label="Reason for rejecting"
        hint="The employee will see this reason."
        error={error ?? serverError}
      >
        {(control) => (
          <textarea
            ref={ref}
            className="input"
            rows={4}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            {...control}
          />
        )}
      </Field>
      <Button type="submit" variant="danger" disabled={pending}>
        Reject request
      </Button>{" "}
      <Button variant="secondary" onClick={onCancel}>
        Keep pending
      </Button>
    </form>
  );
}
