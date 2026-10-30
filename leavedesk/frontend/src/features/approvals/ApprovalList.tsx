import { useState } from "react";
import { Link } from "react-router-dom";
import { formatDate } from "../../lib/dates";
import { daysText, rangeText, typeLabel } from "../requests/format";
import { useApprovals, type ApprovalScope } from "./api";
import { DecisionPanel } from "./DecisionPanel";

export function ApprovalList() {
  const [scope, setScope] = useState<ApprovalScope>("assigned");
  const { data, isPending, isError } = useApprovals(scope);
  const cover = scope === "cover";
  return (
    <section aria-labelledby="approvals-title">
      <h1 id="approvals-title">Approvals</h1>
      <div role="group" aria-label="Approval lists">
        <button
          type="button"
          aria-pressed={!cover}
          onClick={() => setScope("assigned")}
        >
          My team
        </button>{" "}
        <button
          type="button"
          aria-pressed={cover}
          onClick={() => setScope("cover")}
        >
          On behalf of
        </button>
      </div>
      {isPending && <p>Loading requests awaiting your decision…</p>}
      {isError && (
        <p role="alert">Could not load the approvals. Try again later.</p>
      )}
      {data && data.length === 0 && <p>Nothing is waiting for your decision.</p>}
      {data && data.length > 0 && (
        <ul className="approvals">
          {data.map((r) => (
            <li key={r.id}>
              <h2>
                {cover ? (
                  rangeText(r)
                ) : (
                  <Link to={`/requests/${r.id}`}>{rangeText(r)}</Link>
                )}
              </h2>
              {cover && (
                <p>
                  You are deciding for the direct manager of this request. The
                  decision is audited and they will be emailed.
                </p>
              )}
              <dl>
                <dt>Type</dt>
                <dd>{typeLabel(r)}</dd>
                <dt>Working days</dt>
                <dd>{daysText(r.working_days)}</dd>
                <dt>Submitted</dt>
                <dd>{formatDate(r.submitted_at.slice(0, 10))}</dd>
                {r.notice_warning && (
                  <>
                    <dt>Warning</dt>
                    <dd>Short notice for a long absence.</dd>
                  </>
                )}
                {r.note && (
                  <>
                    <dt>Note</dt>
                    <dd>{r.note}</dd>
                  </>
                )}
              </dl>
              <DecisionPanel
                request={r}
                onBehalfOf={cover ? (r.assigned_to ?? undefined) : undefined}
              />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
