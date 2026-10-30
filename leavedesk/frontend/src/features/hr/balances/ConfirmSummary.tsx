import { useEffect, useRef } from "react";
import { formatDate } from "../../../lib/dates";
import { Button } from "../../../ui/Button";
import type { Summary } from "./api";

const KIND = { opening: "Opening balance", carry_over: "Carried days", adjustment: "Correction" } as const;
const TYPE = { annual: "Annual", sick: "Sick" } as const;

interface Props {
  summary: Summary;
  busy?: boolean;
  serverError?: string;
  onSave: () => void;
  onBack: () => void;
}

/** The mandatory confirmation step before saving (R24, C-9). Saving adds a permanent entry. */
export function ConfirmSummary({ summary, busy, serverError, onSave, onBack }: Props) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => heading.current?.focus(), []);
  return (
    <section aria-labelledby="confirm-title">
      <h2 id="confirm-title" ref={heading} tabIndex={-1}>
        Check this entry before saving
      </h2>
      <dl>
        <dt>Employee</dt>
        <dd>{summary.employee_name}</dd>
        <dt>Leave type</dt>
        <dd>{TYPE[summary.leave_type_code]}</dd>
        <dt>Entry</dt>
        <dd>{KIND[summary.kind]}</dd>
        <dt>Days</dt>
        <dd>{summary.days}</dd>
        {summary.expires_on && (
          <>
            <dt>Expire on</dt>
            <dd>{formatDate(summary.expires_on)}</dd>
          </>
        )}
        <dt>Leave year</dt>
        <dd>{summary.leave_year}</dd>
        <dt>Available after saving</dt>
        <dd>{summary.resulting_available}</dd>
      </dl>
      <p>Saved entries cannot be edited or deleted. A mistake is fixed with a new correction.</p>
      {serverError && <p role="alert">{serverError}</p>}
      <Button variant="secondary" onClick={onBack}>
        Back to edit
      </Button>{" "}
      <Button onClick={onSave} disabled={busy}>
        Save entry
      </Button>
    </section>
  );
}
