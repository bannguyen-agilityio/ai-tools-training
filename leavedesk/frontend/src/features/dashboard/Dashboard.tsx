import { useApprovals } from "../approvals/api";
import { useMe } from "../../auth/useMe";
import { ButtonLink } from "../../components/ui/Button";
import { Card, PageHeader } from "../../components/ui/Card";
import { DataList } from "../../components/ui/DataList";
import { DaysText } from "../../components/ui/DateText";
import { Alert, EmptyState, Skeleton } from "../../components/ui/Feedback";
import { LeaveTypeTag } from "../../components/ui/LeaveTypeTag";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { formatDate, todayIso } from "../../lib/dates";
import { useActiveRequests, type LeaveRequest } from "../requests/api";
import { useMyBalances } from "./api";
import { AnnualCard, BalanceError, BalanceSkeleton, SickCard, UnpaidCard } from "./BalanceCard";
import { oldestSubmitted, upcoming, upcomingDates } from "./summary";

function ApprovalsCard() {
  const { data, isPending, isError, refetch } = useApprovals("assigned");
  const pending = data?.filter((r) => r.status === "pending") ?? [];
  const oldest = oldestSubmitted(pending);
  return (
    <Card className="work">
      <h2>Awaiting your decision</h2>
      {isPending && (
        <div role="status" aria-busy="true">
          <span className="visually-hidden">Loading approvals</span>
          <Skeleton className="skeleton--figure" />
          <Skeleton className="skeleton--line" />
        </div>
      )}
      {isError && (
        <Alert tone="danger" onRetry={() => void refetch()}>
          Could not load approvals.
        </Alert>
      )}
      {data && pending.length === 0 && <p className="muted">Nothing waiting</p>}
      {data && pending.length > 0 && (
        <>
          <p className="figure">
            <span className="figure__value num">{pending.length}</span>
          </p>
          <p className="caption">Oldest submitted {oldest}</p>
          <ButtonLink to="/approvals" variant="secondary">
            Review approvals →
          </ButtonLink>
        </>
      )}
    </Card>
  );
}

function UpcomingCard({ rows, loading, error, retry }: { rows: LeaveRequest[]; loading: boolean; error: boolean; retry: () => void }) {
  return (
    <Card className="work work--wide">
      <div className="section__head">
        <h2>Upcoming leave</h2>
        {rows.length > 0 && <ButtonLink to="/requests" variant="ghost" size="sm">View all</ButtonLink>}
      </div>
      {loading && (
        <div role="status" aria-busy="true">
          <span className="visually-hidden">Loading upcoming leave</span>
          <Skeleton className="skeleton--row" />
          <Skeleton className="skeleton--row" />
        </div>
      )}
      {error && (
        <Alert tone="danger" onRetry={retry}>
          Could not load upcoming leave.
        </Alert>
      )}
      {!loading && !error && rows.length === 0 && (
        <EmptyState title="No upcoming leave" action={<ButtonLink to="/requests/new" variant="secondary">Request leave</ButtonLink>} />
      )}
      {rows.length > 0 && (
        <DataList
          caption="Your upcoming leave"
          rows={rows}
          rowKey={(r) => r.id}
          columns={[
            { key: "dates", header: "Dates", primary: true, cell: (r) => upcomingDates(r) },
            { key: "type", header: "Type", cell: (r) => <LeaveTypeTag type={r.leave_type} label={r.label} /> },
            { key: "days", header: "Days", numeric: true, cell: (r) => <DaysText value={r.working_days} /> },
            { key: "status", header: "Status", numeric: true, cell: (r) => <StatusBadge status={r.status} /> },
          ]}
        />
      )}
    </Card>
  );
}

export function Dashboard() {
  const me = useMe().data;
  const balances = useMyBalances();
  const active = useActiveRequests();
  const today = todayIso();
  const isApprover = me ? me.role === "manager" || me.role === "hr" || me.is_hr_deputy : false;
  const rows = active.data ? upcoming(active.data.pending, active.data.approved, today) : [];
  const year = balances.data?.year ?? Number(today.slice(0, 4));
  const unpaidTaken = active.data
    ? active.data.approved
        .filter((r) => r.leave_type === "unpaid" && r.start_date.startsWith(String(year)))
        .reduce((sum, r) => sum + r.working_days, 0)
    : null;
  const annual = balances.data?.balances.find((b) => b.leave_type === "annual");
  const sick = balances.data?.balances.find((b) => b.leave_type === "sick");

  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle={`${formatDate(today)} · Leave year ${year}`}
        action={<ButtonLink to="/requests/new" variant="primary">Request leave</ButtonLink>}
      />
      <div className="dash-grid">
        {balances.isPending && (
          <>
            <BalanceSkeleton hero />
            <BalanceSkeleton />
            <BalanceSkeleton />
          </>
        )}
        {balances.isError && <BalanceError onRetry={() => void balances.refetch()} />}
        {balances.data && (
          <>
            {annual && <AnnualCard b={annual} />}
            {sick && <SickCard b={sick} />}
            <UnpaidCard taken={unpaidTaken} />
          </>
        )}
      </div>
      <div className={isApprover ? "dash-row" : "dash-row dash-row--single"}>
        {isApprover && <ApprovalsCard />}
        <UpcomingCard
          rows={rows}
          loading={active.isPending}
          error={active.isError}
          retry={() => void active.refetch()}
        />
      </div>
    </>
  );
}
