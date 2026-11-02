import { Link } from "react-router-dom";
import { ButtonLink } from "../../components/ui/Button";
import { PageHeader } from "../../components/ui/Card";
import { DataList } from "../../components/ui/DataList";
import { DaysText } from "../../components/ui/DateText";
import { Alert, EmptyState, Loading, Skeleton } from "../../components/ui/Feedback";
import { LeaveTypeTag } from "../../components/ui/LeaveTypeTag";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { useMyRequests } from "./api";
import { rangeText } from "./format";

export function MyRequests() {
  const { data, isPending, isError, refetch } = useMyRequests();
  return (
    <>
      <PageHeader
        title="My requests"
        action={<ButtonLink to="/requests/new" variant="primary">Request leave</ButtonLink>}
      />
      {isPending && (
        <Loading label="Loading your requests">
          <Skeleton className="skeleton--row" />
          <Skeleton className="skeleton--row" />
          <Skeleton className="skeleton--row" />
        </Loading>
      )}
      {isError && (
        <Alert tone="danger" onRetry={() => void refetch()}>
          Could not load your requests.
        </Alert>
      )}
      {data && data.length === 0 && (
        <EmptyState title="No requests yet">Leave you request is listed here.</EmptyState>
      )}
      {data && data.length > 0 && (
        <div className="card">
          <DataList
            caption="Your leave requests, newest first"
            rows={data}
            rowKey={(r) => r.id}
            columns={[
              { key: "dates", header: "Dates", primary: true, cell: (r) => <Link to={`/requests/${r.id}`}>{rangeText(r)}</Link> },
              { key: "type", header: "Type", cell: (r) => <LeaveTypeTag type={r.leave_type} label={r.label} /> },
              { key: "days", header: "Days", numeric: true, cell: (r) => <DaysText value={r.working_days} /> },
              { key: "status", header: "Status", numeric: true, cell: (r) => <StatusBadge status={r.status} /> },
            ]}
          />
        </div>
      )}
    </>
  );
}
