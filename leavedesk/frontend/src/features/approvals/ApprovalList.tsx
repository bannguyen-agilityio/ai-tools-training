import { Link } from "react-router-dom";
import { formatDate } from "../../lib/dates";
import { daysText, rangeText, typeLabel } from "../requests/format";
import { useAssignedApprovals } from "./api";
import { DecisionPanel } from "./DecisionPanel";

export function ApprovalList() {
  const { data, isPending, isError } = useAssignedApprovals();
  return (
    <section aria-labelledby="approvals-title">
      <h1 id="approvals-title">Approvals</h1>
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
                <Link to={`/requests/${r.id}`}>{rangeText(r)}</Link>
              </h2>
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
              <DecisionPanel request={r} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
