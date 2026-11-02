import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { formatDate } from "../../lib/dates";
import { daysText, rangeText, typeLabel } from "../requests/format";
import { useApprovals, type ApprovalScope } from "./api";
import { DecisionPanel } from "./DecisionPanel";
import { Alert, Loading, Skeleton } from "../../components/ui/Feedback";
import { PageHeader } from "../../components/ui/Card";

export function ApprovalList() {
  const [scope, setScope] = useState<ApprovalScope>("assigned");
  const { data, isPending, isError } = useApprovals(scope);
  const cover = scope === "cover";
  return (
    <section aria-labelledby="approvals-title">
      <PageHeader title="Approvals" titleId="approvals-title" />
      <div role="group" aria-label="Approval lists">
        <Button variant={cover ? "secondary" : "primary"} aria-pressed={!cover} onClick={() => setScope("assigned")}>
          My team
        </Button>{" "}
        <Button variant={cover ? "primary" : "secondary"} aria-pressed={cover} onClick={() => setScope("cover")}>
          On behalf of
        </Button>
      </div>
      {isPending && <Loading label="Loading requests awaiting your decision…"><Skeleton className="skeleton--row" /></Loading>}
      {isError && (
        <Alert tone="danger">Could not load the approvals. Try again later.</Alert>
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
                {r.employee_name && (
                  <>
                    <dt>Requested by</dt>
                    <dd>{r.employee_name}</dd>
                  </>
                )}
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
