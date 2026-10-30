import { useEffect, useRef, useState, type FormEvent } from "react";
import { Button } from "../../ui/Button";
import { Field } from "../../ui/Field";

export const MAX_REASON = 500;

interface HrCancelDialogProps {
  consequence: string;
  pending: boolean;
  onSubmit: (reason: string) => void;
}

/** HR cancels Approved leave (R21). Opens collapsed; focus starts on "Keep" (R31e). */
export function HrCancelDialog({
  consequence,
  pending,
  onSubmit,
}: HrCancelDialogProps) {
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string>();
  const ref = useRef<HTMLTextAreaElement>(null);
  const keepRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) keepRef.current?.focus();
  }, [open]);

  function submit(e: FormEvent) {
    e.preventDefault();
    const trimmed = reason.trim();
    if (!trimmed || trimmed.length > MAX_REASON) {
      setError(
        trimmed
          ? `Use ${MAX_REASON} characters or fewer.`
          : "Enter a reason for cancelling this leave.",
      );
      ref.current?.focus();
      return;
    }
    setError(undefined);
    onSubmit(trimmed);
  }

  if (!open) {
    return (
      <Button variant="danger" onClick={() => setOpen(true)}>
        Cancel leave (HR)
      </Button>
    );
  }
  return (
    <form onSubmit={submit} noValidate aria-label="Cancel approved leave">
      <p>{consequence}</p>
      <Field
        label="Reason for cancelling"
        hint="Kept on the record. It is not sent in the emails."
        error={error}
      >
        {(control) => (
          <textarea
            ref={ref}
            className="input"
            rows={3}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            {...control}
          />
        )}
      </Field>
      <Button variant="secondary" ref={keepRef} onClick={() => setOpen(false)}>
        Keep
      </Button>{" "}
      <Button type="submit" variant="danger" disabled={pending}>
        Cancel leave
      </Button>
    </form>
  );
}
